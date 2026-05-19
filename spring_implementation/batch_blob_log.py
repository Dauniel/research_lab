"""
batch_blob_log.py — Like batch_compare.py but uses skimage blob_log (LoG spot
detection) for condensates instead of Cellpose. Reuses Cellpose only for nuclei.
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import tifffile as tiff
import torch
from skimage.feature import blob_log
from cellpose import models, core, denoise as cp_denoise

sys.path.insert(0, str(Path(__file__).parent))
from pipeline import denoise_stack, segment_nuclei, compute_partition_coefficient
from batch_compare import max_overlap_nucleus


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--construct-dir", required=True, type=Path)
    p.add_argument("--output",        default=None,  type=Path)
    p.add_argument("--nuc-cellprob",  default=-2.0,  type=float)
    p.add_argument("--cond-topx",     default=75.0,  type=float)
    p.add_argument("--blob-threshold",default=0.03,  type=float)
    p.add_argument("--min-sigma",     default=1.5,   type=float)
    p.add_argument("--max-sigma",     default=6.0,   type=float)
    p.add_argument("--num-sigma",     default=8,     type=int)
    p.add_argument("--no-gpu",        action="store_true")
    return p.parse_args()


def detect_condensates_blob(cond_stack: np.ndarray, nuc_3d: np.ndarray,
                            threshold: float, min_sigma: float, max_sigma: float,
                            num_sigma: int) -> np.ndarray:
    """Return an int32 instance mask. One ball per LoG blob; radius = sigma*sqrt(3)."""
    B = float(cond_stack.min())
    norm = np.clip(cond_stack.astype(np.float32) - B, 0, None)
    mx = norm.max()
    if mx <= 0:
        return np.zeros_like(cond_stack, dtype=np.int32)
    norm /= mx

    blobs = blob_log(norm, min_sigma=min_sigma, max_sigma=max_sigma,
                     num_sigma=num_sigma, threshold=threshold, overlap=0.5)
    if len(blobs) == 0:
        return np.zeros_like(cond_stack, dtype=np.int32)

    zs = blobs[:, 0].astype(int); ys = blobs[:, 1].astype(int); xs = blobs[:, 2].astype(int)
    inside = nuc_3d[zs, ys, xs]
    blobs_in = blobs[inside]

    Z, Y, X = cond_stack.shape
    mask = np.zeros_like(cond_stack, dtype=np.int32)
    for i, (z, y, x, s) in enumerate(blobs_in, start=1):
        r = max(1.5, s * np.sqrt(3))
        zi, yi, xi = int(round(z)), int(round(y)), int(round(x))
        rr = int(np.ceil(r))
        z0, z1 = max(0, zi - rr), min(Z, zi + rr + 1)
        y0, y1 = max(0, yi - rr), min(Y, yi + rr + 1)
        x0, x1 = max(0, xi - rr), min(X, xi + rr + 1)
        zz, yy, xx = np.ogrid[z0:z1, y0:y1, x0:x1]
        sphere = (zz - zi) ** 2 + (yy - yi) ** 2 + (xx - xi) ** 2 <= r * r
        sub = mask[z0:z1, y0:y1, x0:x1]
        sub[sphere & (sub == 0)] = i
    return mask


def run_one(tif_path, dn_model, nuc_seg_model, nuc_cellprob, cond_topx,
            blob_threshold, min_sigma, max_sigma, num_sigma):
    roi = tiff.imread(tif_path)
    if roi.ndim != 4 or roi.shape[1] != 2:
        raise ValueError(f"Expected (Z, 2, Y, X), got {roi.shape}")
    nuc_stack  = roi[:, 0].copy()
    cond_stack = roi[:, 1].copy()

    nuc_restored = denoise_stack(nuc_stack, dn_model, "nuclei")
    nuc_masks = segment_nuclei(nuc_restored, nuc_seg_model, diameter=None,
                               cellprob_threshold=nuc_cellprob)

    cond_masks = detect_condensates_blob(cond_stack, nuc_masks > 0,
                                         blob_threshold, min_sigma, max_sigma, num_sigma)
    print(f"    blob_log condensates inside nuclei: {cond_masks.max()}")
    nuc_masks = max_overlap_nucleus(nuc_masks, cond_masks)

    r = compute_partition_coefficient(cond_stack, cond_masks, nuc_masks, cond_topx=cond_topx)
    r["n_condensates"] = int(cond_masks.max())
    return r


def main():
    args = parse_args()
    construct_dir = args.construct_dir
    output_dir = args.output or (Path(__file__).parent / "outputs" / f"blob_{construct_dir.name}")
    output_dir.mkdir(parents=True, exist_ok=True)

    ref_csv = next(construct_dir.glob("*_Partition coefficient_nuclear.csv"))
    ref_df = pd.read_csv(ref_csv)
    ref_df.columns = ["filename", "ref_cond_density", "ref_dilute_density", "ref_pc"]
    ref_lookup = ref_df.set_index("filename")
    print(f"Reference: {ref_csv.name}  ({len(ref_df)} cells)")

    roi_dir = construct_dir / "Cut ROI"
    tif_paths = sorted([p for p in roi_dir.rglob("*.tif") if "_cp_masks" not in p.name])
    print(f"Found {len(tif_paths)} TIFs in Cut ROI")

    use_gpu = core.use_gpu() and not args.no_gpu
    print(f"GPU: {'enabled — ' + torch.cuda.get_device_name(0) if use_gpu else 'disabled'}\n")
    dn_model      = cp_denoise.DenoiseModel(model_type="denoise_cyto3", gpu=use_gpu)
    nuc_seg_model = models.CellposeModel(gpu=use_gpu, model_type="cyto3")

    print(f"blob_log: threshold={args.blob_threshold}, sigma=[{args.min_sigma},{args.max_sigma}], num_sigma={args.num_sigma}\n")

    rows = []
    for tif_path in tif_paths:
        fname = tif_path.name
        if fname not in ref_lookup.index:
            print(f"  skip {fname} (no reference entry)")
            continue
        print(f"Processing {fname}...")
        try:
            r = run_one(tif_path, dn_model, nuc_seg_model, args.nuc_cellprob,
                        args.cond_topx, args.blob_threshold,
                        args.min_sigma, args.max_sigma, args.num_sigma)
            ref_row = ref_lookup.loc[fname]
            err = (r["pc"] - ref_row["ref_pc"]) / ref_row["ref_pc"] * 100
            rows.append({
                "filename": fname,
                "ref_pc": ref_row["ref_pc"],
                "pipeline_pc": r["pc"],
                "n_condensates": r["n_condensates"],
                "pipeline_cond_density": r["cond_density"],
                "pipeline_dilute_density": r["dilute_density"],
                "pipeline_background": r["background"],
                "error_pct": err,
            })
            print(f"  pipeline={r['pc']:.3f}  ref={ref_row['ref_pc']:.3f}  err={err:+.1f}%  n={r['n_condensates']}")
        except Exception as e:
            print(f"  ERROR: {e}")

    if not rows:
        print("No results.")
        return

    df = pd.DataFrame(rows)
    df.to_csv(output_dir / "comparison.csv", index=False)

    mae  = float(df["error_pct"].abs().mean())
    rmse = float(((df["pipeline_pc"] - df["ref_pc"]) ** 2).mean() ** 0.5)
    corr = float(df["ref_pc"].corr(df["pipeline_pc"]))
    me   = float(df["error_pct"].mean())
    print(f"\n{'=' * 50}")
    print(f"Cells processed : {len(df)}")
    print(f"Mean error (ME) : {me:+.1f}%")
    print(f"MAE             : {mae:.1f}%")
    print(f"RMSE            : {rmse:.3f}")
    print(f"Pearson r       : {corr:.3f}")
    print(f"Outputs         : {output_dir}")

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(df["ref_pc"], df["pipeline_pc"], alpha=0.7, s=45, edgecolors="none")
    lim_max = max(df["ref_pc"].max(), df["pipeline_pc"].max()) * 1.1
    ax.plot([0, lim_max], [0, lim_max], "k--", linewidth=1)
    ax.set_xlim(0, lim_max); ax.set_ylim(0, lim_max)
    ax.set_xlabel("Reference PC"); ax.set_ylabel("blob_log PC")
    ax.set_title(f"{construct_dir.name} — blob_log — {len(df)} cells")
    ax.text(0.05, 0.95, f"r={corr:.3f}\nMAE={mae:.1f}%\nME={me:+.1f}%",
            transform=ax.transAxes, va="top",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8))
    plt.tight_layout()
    plt.savefig(output_dir / "scatter.png", dpi=150)
    plt.close()


if __name__ == "__main__":
    main()
