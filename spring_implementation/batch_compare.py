"""
batch_compare.py — Batch-run the pipeline on all Cut ROI TIFs for a construct
and compare pipeline PC against the manual reference nuclear CSV.

Usage:
    python spring_implementation/batch_compare.py \
        --construct-dir "C:/Users/Danie/Box/Condensate Volume Quantification/JABr" \
        --output spring_implementation/outputs/batch_JABr

Options:
    --construct-dir   Path to a construct folder containing Cut ROI/ and
                      *_Partition coefficient_nuclear.csv  (required)
    --output          Output directory (default: outputs/batch_<construct>)
    --nuc-cellprob    Nuclei cellprob_threshold (default: -2.0)
    --no-gpu          Disable GPU
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
from pipeline import denoise_stack, segment_condensates, segment_nuclei, compute_partition_coefficient


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--construct-dir", required=True, type=Path)
    p.add_argument("--output",        default=None,  type=Path)
    p.add_argument("--nuc-cellprob",  default=-2.0,  type=float)
    p.add_argument("--cond-topx",     default=75.0,  type=float, help="Top-X%% brightest cond voxels (100 = full mean)")
    p.add_argument("--all-nuclei",    action="store_true",       help="Skip nucleus selection, pool all nuclei")
    p.add_argument("--no-gpu",        action="store_true")
    return p.parse_args()


def central_nucleus_only(nuc_masks: np.ndarray) -> np.ndarray:
    """Keep only the nucleus whose XY centroid is closest to the image center."""
    if nuc_masks.max() == 0:
        return nuc_masks

    Z, Y, X = nuc_masks.shape
    cy_target, cx_target = Y / 2.0, X / 2.0

    labels = np.unique(nuc_masks)
    labels = labels[labels > 0]

    best_label = None
    best_dist  = float("inf")
    for lbl in labels:
        coords = np.argwhere(nuc_masks == lbl)
        cy = coords[:, 1].mean()
        cx = coords[:, 2].mean()
        dist = ((cy - cy_target) ** 2 + (cx - cx_target) ** 2) ** 0.5
        if dist < best_dist:
            best_dist  = dist
            best_label = int(lbl)

    out = np.zeros_like(nuc_masks)
    if best_label is not None:
        out[nuc_masks == best_label] = 1
        print(f"    central nucleus: label {best_label}  (XY dist {best_dist:.1f} from center)")
    return out


def max_overlap_nucleus(nuc_masks: np.ndarray, cond_masks: np.ndarray) -> np.ndarray:
    """Keep only the nucleus with the most condensate-mask overlap.

    The "target cell" is the one Imaris's manual analysis was done on — almost
    always the cell containing the visible condensates. Picking the nucleus with
    the largest cond ∩ nuc voxel count selects that cell directly, regardless of
    where it sits in the cropped FOV. More robust than a centroid heuristic on
    wide multi-cell fields where the target cell isn't centered.
    """
    if nuc_masks.max() == 0:
        return nuc_masks

    cond_3d = cond_masks > 0
    labels  = np.unique(nuc_masks)
    labels  = labels[labels > 0]

    best_label   = None
    best_overlap = -1
    for lbl in labels:
        overlap = int(((nuc_masks == lbl) & cond_3d).sum())
        if overlap > best_overlap:
            best_overlap = overlap
            best_label   = int(lbl)

    out = np.zeros_like(nuc_masks)
    if best_label is not None and best_overlap > 0:
        out[nuc_masks == best_label] = 1
        print(f"    target nucleus: label {best_label}  ({best_overlap} cond voxels overlap)")
    else:
        print(f"    no nucleus has condensate overlap — keeping all nuclei")
        out = (nuc_masks > 0).astype(nuc_masks.dtype)
    return out


def run_one(tif_path: Path, dn_model, seg_model, nuc_cellprob: float,
            cond_topx: float = 75.0, all_nuclei: bool = False) -> dict:
    roi = tiff.imread(tif_path)
    if roi.ndim != 4 or roi.shape[1] != 2:
        raise ValueError(f"Expected (Z, 2, Y, X), got {roi.shape}")
    nuc_stack  = roi[:, 0, :, :].copy()
    cond_stack = roi[:, 1, :, :].copy()

    cond_restored = denoise_stack(cond_stack, dn_model, "condensates")
    nuc_restored  = denoise_stack(nuc_stack,  dn_model, "nuclei")

    cond_masks = segment_condensates(cond_restored, seg_model, diameter=None)
    nuc_masks  = segment_nuclei(nuc_restored, seg_model, diameter=None, cellprob_threshold=nuc_cellprob)
    if not all_nuclei:
        nuc_masks = max_overlap_nucleus(nuc_masks, cond_masks)

    return compute_partition_coefficient(cond_stack, cond_masks, nuc_masks, cond_topx=cond_topx)


def main():
    args = parse_args()
    construct_dir = args.construct_dir
    output_dir = args.output or (Path(__file__).parent / "outputs" / f"batch_{construct_dir.name}")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load nuclear reference CSV
    ref_csv = next(construct_dir.glob("*_Partition coefficient_nuclear.csv"))
    ref_df = pd.read_csv(ref_csv)
    ref_df.columns = ["filename", "ref_cond_density", "ref_dilute_density", "ref_pc"]
    ref_lookup = ref_df.set_index("filename")
    print(f"Reference: {ref_csv.name}  ({len(ref_df)} cells)")

    # Find Cut ROI TIFs (skip Cellpose mask files)
    roi_dir = construct_dir / "Cut ROI"
    tif_paths = sorted([
        p for p in roi_dir.rglob("*.tif")
        if "_cp_masks" not in p.name
    ])
    print(f"Found {len(tif_paths)} TIFs in Cut ROI")

    # Initialise models once
    use_gpu = core.use_gpu() and not args.no_gpu
    print(f"GPU: {'enabled — ' + torch.cuda.get_device_name(0) if use_gpu else 'disabled'}\n")
    dn_model  = cp_denoise.DenoiseModel(model_type="denoise_cyto3", gpu=use_gpu)
    seg_model = models.CellposeModel(gpu=use_gpu, model_type="cyto3")

    rows = []
    for tif_path in tif_paths:
        fname = tif_path.name
        if fname not in ref_lookup.index:
            print(f"  skip {fname} (no reference entry)")
            continue

        print(f"Processing {fname}...")
        try:
            result  = run_one(tif_path, dn_model, seg_model, args.nuc_cellprob,
                              cond_topx=args.cond_topx, all_nuclei=args.all_nuclei)
            ref_row = ref_lookup.loc[fname]
            rows.append({
                "filename":                fname,
                "ref_pc":                  ref_row["ref_pc"],
                "pipeline_pc":             result["pc"],
                "ref_cond_density":        ref_row["ref_cond_density"],
                "ref_dilute_density":      ref_row["ref_dilute_density"],
                "pipeline_cond_density":   result["cond_density"],
                "pipeline_dilute_density": result["dilute_density"],
                "pipeline_background":     result["background"],
                "error_pct": (result["pc"] - ref_row["ref_pc"]) / ref_row["ref_pc"] * 100,
            })
            print(f"  pipeline={result['pc']:.3f}  ref={ref_row['ref_pc']:.3f}  "
                  f"err={rows[-1]['error_pct']:+.1f}%")
        except Exception as e:
            print(f"  ERROR: {e}")

    if not rows:
        print("No results — check that filenames match the reference CSV.")
        return

    df = pd.DataFrame(rows)
    df.to_csv(output_dir / "comparison.csv", index=False)

    # Summary stats
    rmse = float(((df["pipeline_pc"] - df["ref_pc"]) ** 2).mean() ** 0.5)
    corr = float(df["ref_pc"].corr(df["pipeline_pc"]))
    me   = float(df["error_pct"].mean())
    print(f"\n{'='*50}")
    print(f"Cells processed : {len(df)}")
    print(f"Mean error      : {me:+.1f}%")
    print(f"RMSE            : {rmse:.3f}")
    print(f"Pearson r       : {corr:.3f}")
    print(f"Outputs         : {output_dir}")

    # Scatter plot: pipeline PC vs reference PC
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(df["ref_pc"], df["pipeline_pc"], alpha=0.7, s=45, edgecolors="none")
    lim_max = max(df["ref_pc"].max(), df["pipeline_pc"].max()) * 1.1
    ax.plot([0, lim_max], [0, lim_max], "k--", linewidth=1, label="y = x (perfect agreement)")
    ax.set_xlim(0, lim_max)
    ax.set_ylim(0, lim_max)
    ax.set_xlabel("Reference PC (Imaris / manual)", fontsize=12)
    ax.set_ylabel("Pipeline PC (automated)", fontsize=12)
    ax.set_title(f"{construct_dir.name}  —  {len(df)} cells", fontsize=13)
    ax.text(0.05, 0.95,
            f"r = {corr:.3f}\nRMSE = {rmse:.3f}\nMean err = {me:+.1f}%",
            transform=ax.transAxes, fontsize=10, va="top",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8))
    ax.legend(fontsize=9)
    plt.tight_layout()
    plt.savefig(output_dir / "scatter.png", dpi=150)
    plt.close()
    print(f"Saved scatter.png")


if __name__ == "__main__":
    main()
