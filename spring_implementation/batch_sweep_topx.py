"""
batch_sweep_topx.py — For each Cut ROI TIF, run the pipeline once and compute
the condensate density several ways: full mean (current) plus mean of the
top-X% brightest voxels in the mask, for X in {10, 20, 25, 30, 40, 50, 75}.

This tests the hypothesis that Cellpose's do_3D=True mask is too inclusive
(includes large dim/dark regions inside object boundaries), and that taking a
high-percentile subset of mask pixels recovers the manually-drawn condensate
core that Imaris uses.

Outputs to <output>/:
    sweep.csv      one row per cell, columns: filename, ref_pc, pc_full,
                   pc_top75, ..., pc_top10
    summary.csv    per-X aggregate stats (r, RMSE, mean error)
    sweep_plot.png scatter of pipeline vs reference PC for each X

Usage:
    python spring_implementation/batch_sweep_topx.py \
        --construct-dir "C:/Users/Danie/Box/Condensate Volume Quantification/JABr" \
        --output spring_implementation/outputs/sweep_topx_JABr
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import tifffile as tiff
import torch
from cellpose import models, core, denoise as cp_denoise

sys.path.insert(0, str(Path(__file__).parent))
from pipeline import denoise_stack, segment_condensates, segment_nuclei
from batch_compare import max_overlap_nucleus


PERCENTILES = [10, 20, 25, 30, 40, 50, 75]   # X = top X% brightest


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--construct-dir", required=True, type=Path)
    p.add_argument("--output",        default=None,  type=Path)
    p.add_argument("--nuc-cellprob",  default=-2.0,  type=float)
    p.add_argument("--no-gpu",        action="store_true")
    return p.parse_args()


def compute_dilute_density(cond_stack: np.ndarray, dilute_3d: np.ndarray, B: float) -> float:
    """Same as pipeline.compute_partition_coefficient — lowest-50-patch dilute."""
    PATCH = 10
    N_PATCHES = 50
    Z, Y, X = cond_stack.shape
    candidates = np.argwhere(dilute_3d)
    in_bounds = candidates[
        (candidates[:, 0] + PATCH <= Z) &
        (candidates[:, 1] + PATCH <= Y) &
        (candidates[:, 2] + PATCH <= X)
    ]
    patch_means = []
    for z0, y0, x0 in in_bounds:
        if dilute_3d[z0:z0+PATCH, y0:y0+PATCH, x0:x0+PATCH].all():
            patch = cond_stack[z0:z0+PATCH, y0:y0+PATCH, x0:x0+PATCH].astype(np.float64) - B
            patch_means.append(np.clip(patch, 0, None).mean())
    if patch_means:
        patch_means.sort()
        return float(np.mean(patch_means[:N_PATCHES]))
    return float(np.clip(cond_stack[dilute_3d].astype(np.float64) - B, 0, None).mean())


def run_one(tif_path: Path, dn_model, seg_model, nuc_cellprob: float) -> dict:
    roi = tiff.imread(tif_path)
    if roi.ndim != 4 or roi.shape[1] != 2:
        raise ValueError(f"Expected (Z, 2, Y, X), got {roi.shape}")
    nuc_stack  = roi[:, 0, :, :].copy()
    cond_stack = roi[:, 1, :, :].copy()

    cond_restored = denoise_stack(cond_stack, dn_model, "condensates")
    nuc_restored  = denoise_stack(nuc_stack,  dn_model, "nuclei")
    cond_masks    = segment_condensates(cond_restored, seg_model, diameter=None)
    nuc_masks     = segment_nuclei(nuc_restored, seg_model, diameter=None, cellprob_threshold=nuc_cellprob)
    nuc_masks     = max_overlap_nucleus(nuc_masks, cond_masks)

    cond_3d = cond_masks > 0
    nuc_3d  = nuc_masks  > 0
    nuclear_cond = cond_3d & nuc_3d
    dilute_3d    = nuc_3d & ~cond_3d

    B = float(cond_stack.min())
    if not nuclear_cond.any() or not dilute_3d.any():
        return {"failed": True}

    cond_vals = np.clip(cond_stack[nuclear_cond].astype(np.float64) - B, 0, None)
    cond_vals_sorted = np.sort(cond_vals)
    n = len(cond_vals_sorted)

    densities = {"full": float(cond_vals.mean())}
    for X in PERCENTILES:
        cutoff = int(n * (1 - X / 100.0))
        densities[f"top{X}"] = float(cond_vals_sorted[cutoff:].mean())

    dilute_density = compute_dilute_density(cond_stack, dilute_3d, B)

    return {
        "failed": False,
        "B": B,
        "dilute_density": dilute_density,
        "cond_densities": densities,
        "n_cond_voxels": int(nuclear_cond.sum()),
        "n_dil_voxels":  int(dilute_3d.sum()),
    }


def main():
    args = parse_args()
    construct_dir = args.construct_dir
    output_dir = args.output or (Path(__file__).parent / "outputs" / f"sweep_topx_{construct_dir.name}")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Reference
    ref_csv = next(construct_dir.glob("*_Partition coefficient_nuclear.csv"))
    ref_df = pd.read_csv(ref_csv)
    ref_df.columns = ["filename", "ref_cond_density", "ref_dilute_density", "ref_pc"]
    ref_lookup = ref_df.set_index("filename")
    print(f"Reference: {ref_csv.name}  ({len(ref_df)} cells)")

    # Find TIFs
    roi_dir = construct_dir / "Cut ROI"
    tif_paths = sorted([p for p in roi_dir.rglob("*.tif") if "_cp_masks" not in p.name])
    print(f"Found {len(tif_paths)} TIFs in Cut ROI")

    # Init models
    use_gpu = core.use_gpu() and not args.no_gpu
    print(f"GPU: {'enabled' if use_gpu else 'disabled'}\n")
    dn_model  = cp_denoise.DenoiseModel(model_type="denoise_cyto3", gpu=use_gpu)
    seg_model = models.CellposeModel(gpu=use_gpu, model_type="cyto3")

    rows = []
    for tif_path in tif_paths:
        fname = tif_path.name
        if fname not in ref_lookup.index:
            continue
        print(f"Processing {fname}...")
        try:
            result = run_one(tif_path, dn_model, seg_model, args.nuc_cellprob)
            if result.get("failed"):
                print("  failed (no nucleus or no condensate overlap)")
                continue
            ref_row = ref_lookup.loc[fname]
            row = {
                "filename":        fname,
                "ref_pc":          ref_row["ref_pc"],
                "ref_cond":        ref_row["ref_cond_density"],
                "ref_dil":         ref_row["ref_dilute_density"],
                "pipe_dil":        result["dilute_density"],
                "n_cond_vox":      result["n_cond_voxels"],
            }
            row["pc_full"] = result["cond_densities"]["full"] / result["dilute_density"]
            row["cond_full"] = result["cond_densities"]["full"]
            for X in PERCENTILES:
                cd = result["cond_densities"][f"top{X}"]
                row[f"cond_top{X}"] = cd
                row[f"pc_top{X}"]   = cd / result["dilute_density"]
            rows.append(row)
            print(f"  full={row['pc_full']:.2f}  top25={row['pc_top25']:.2f}  ref={row['ref_pc']:.2f}")
        except Exception as e:
            print(f"  ERROR: {e}")

    if not rows:
        print("No results.")
        return

    df = pd.DataFrame(rows)
    df.to_csv(output_dir / "sweep.csv", index=False)
    print(f"\nSaved sweep.csv ({len(df)} cells)\n")

    # Per-X summary
    summary_rows = []
    variants = ["full"] + [f"top{X}" for X in PERCENTILES]
    for v in variants:
        col = f"pc_{v}"
        err_pct = (df[col] - df["ref_pc"]) / df["ref_pc"] * 100
        rmse = float(((df[col] - df["ref_pc"]) ** 2).mean() ** 0.5)
        corr = float(df["ref_pc"].corr(df[col]))
        me   = float(err_pct.mean())
        mae  = float(err_pct.abs().mean())
        summary_rows.append({
            "variant": v,
            "pearson_r": corr,
            "rmse": rmse,
            "mean_error_pct": me,
            "mean_abs_error_pct": mae,
        })
    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(output_dir / "summary.csv", index=False)

    print(f"{'variant':<10} {'r':>8} {'RMSE':>8} {'mean err':>10} {'|mean err|':>12}")
    for r in summary_rows:
        print(f"{r['variant']:<10} {r['pearson_r']:>8.3f} {r['rmse']:>8.3f}"
              f" {r['mean_error_pct']:>+9.1f}% {r['mean_abs_error_pct']:>+11.1f}%")

    # Plot scatter for each variant
    n = len(variants)
    cols = 4
    rows_n = (n + cols - 1) // cols
    fig, axes = plt.subplots(rows_n, cols, figsize=(4 * cols, 4 * rows_n))
    axes = axes.flatten()
    for i, v in enumerate(variants):
        ax = axes[i]
        ax.scatter(df["ref_pc"], df[f"pc_{v}"], alpha=0.7, s=30, edgecolors="none")
        lim = max(df["ref_pc"].max(), df[f"pc_{v}"].max()) * 1.1
        ax.plot([0, lim], [0, lim], "k--", linewidth=0.8)
        ax.set_xlim(0, lim); ax.set_ylim(0, lim)
        s = summary_rows[i]
        ax.set_title(f"{v}  r={s['pearson_r']:.3f}  RMSE={s['rmse']:.2f}", fontsize=10)
        ax.set_xlabel("ref PC", fontsize=9)
        ax.set_ylabel("pipeline PC", fontsize=9)
    for j in range(len(variants), len(axes)):
        axes[j].axis("off")
    plt.tight_layout()
    plt.savefig(output_dir / "sweep_plot.png", dpi=130)
    plt.close()
    print(f"\nOutputs: {output_dir}")


if __name__ == "__main__":
    main()
