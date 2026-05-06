"""
diagnose_cell.py — Run the pipeline on a single Cut ROI TIF and dump diagnostics
to figure out why pipeline PC differs from the manual reference.

Outputs to <output>/diagnose_<filename>/:
    raw_midZ.png            mid-Z slice of cond/nuc channels
    mask_overlay.png        condensate mask + central nucleus overlay
    intensity_hist.png      histogram of intensities inside vs outside cond mask
    summary.txt             pipeline densities computed several ways

Usage:
    python spring_implementation/diagnose_cell.py \
        --tif "C:/Users/Danie/Box/Condensate Volume Quantification/JABr/Cut ROI/20240516_JABr_40uMDFHBI_20-40_Sample3_3_11.tif" \
        --ref-pc 16.95 --ref-cond 1361.65 --ref-dil 80.33
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import tifffile as tiff
from cellpose import models, core, denoise as cp_denoise

sys.path.insert(0, str(Path(__file__).parent))
from pipeline import denoise_stack, segment_condensates, segment_nuclei
from batch_compare import central_nucleus_only


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--tif",      required=True, type=Path)
    p.add_argument("--output",   default=None,  type=Path)
    p.add_argument("--ref-pc",   default=None,  type=float)
    p.add_argument("--ref-cond", default=None,  type=float)
    p.add_argument("--ref-dil",  default=None,  type=float)
    p.add_argument("--no-gpu",   action="store_true")
    return p.parse_args()


def main():
    args = parse_args()
    output_dir = args.output or (Path(__file__).parent / "outputs" / f"diagnose_{args.tif.stem}")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load
    roi = tiff.imread(args.tif)
    nuc_stack  = roi[:, 0, :, :].copy()
    cond_stack = roi[:, 1, :, :].copy()
    Z, Y, X = cond_stack.shape
    print(f"Stack shape: {cond_stack.shape}")

    # Run pipeline
    use_gpu = core.use_gpu() and not args.no_gpu
    dn_model  = cp_denoise.DenoiseModel(model_type="denoise_cyto3", gpu=use_gpu)
    seg_model = models.CellposeModel(gpu=use_gpu, model_type="cyto3")

    cond_restored = denoise_stack(cond_stack, dn_model, "condensates")
    nuc_restored  = denoise_stack(nuc_stack,  dn_model, "nuclei")
    cond_masks    = segment_condensates(cond_restored, seg_model, diameter=None)
    nuc_masks     = segment_nuclei(nuc_restored, seg_model, diameter=None, cellprob_threshold=-2.0)
    nuc_masks     = central_nucleus_only(nuc_masks)

    cond_3d = cond_masks > 0
    nuc_3d  = nuc_masks  > 0

    # Pipeline values (current method)
    B = float(cond_stack.min())
    nuclear_cond = cond_3d & nuc_3d
    dilute_3d    = nuc_3d & ~cond_3d

    cond_vals_in_mask = cond_stack[nuclear_cond].astype(np.float64)
    cond_density_pipe = np.clip(cond_vals_in_mask - B, 0, None).mean() if nuclear_cond.any() else float("nan")

    # Try alternative density computations
    summary = []
    summary.append(f"DIAGNOSTIC: {args.tif.name}")
    summary.append(f"FOV shape (Z, Y, X)            : {cond_stack.shape}")
    summary.append(f"Background B (min of FOV)      : {B:.1f}")
    summary.append(f"Cond intensity range (raw)     : [{cond_stack.min()}, {cond_stack.max()}]")
    summary.append(f"")
    summary.append(f"== Mask coverage ==")
    summary.append(f"Total cond mask voxels         : {int(cond_3d.sum()):>10}  ({cond_3d.mean()*100:.2f}% of FOV)")
    summary.append(f"Central nucleus voxels         : {int(nuc_3d.sum()):>10}  ({nuc_3d.mean()*100:.2f}% of FOV)")
    summary.append(f"Cond & nucleus (used for PC)   : {int(nuclear_cond.sum()):>10}")
    summary.append(f"Dilute region (nuc & ~cond)    : {int(dilute_3d.sum()):>10}")
    summary.append(f"")
    summary.append(f"== Condensate-density variants (background-subtracted) ==")

    if nuclear_cond.any():
        v = np.clip(cond_vals_in_mask - B, 0, None)
        summary.append(f"Mean of mask voxels (CURRENT)  : {v.mean():.1f}")
        summary.append(f"Median of mask voxels          : {np.median(v):.1f}")
        summary.append(f"Top 50% brightest in mask      : {np.sort(v)[len(v)//2:].mean():.1f}")
        summary.append(f"Top 25% brightest in mask      : {np.sort(v)[int(len(v)*0.75):].mean():.1f}")
        summary.append(f"Top 10% brightest in mask      : {np.sort(v)[int(len(v)*0.90):].mean():.1f}")
        summary.append(f"Peak in mask                   : {v.max():.1f}")
        summary.append(f"Sum / volume (= mean)          : {v.sum() / nuclear_cond.sum():.1f}")

    summary.append(f"")
    summary.append(f"== What's bright that's NOT in the mask? ==")
    nuc_only = nuc_3d & ~cond_3d
    if nuc_only.any():
        in_dil = np.clip(cond_stack[nuc_only].astype(np.float64) - B, 0, None)
        summary.append(f"Dilute region peak             : {in_dil.max():.1f}")
        summary.append(f"Dilute region 99th percentile  : {np.percentile(in_dil, 99):.1f}")
        summary.append(f"Dilute region 95th percentile  : {np.percentile(in_dil, 95):.1f}")

    if args.ref_pc is not None:
        summary.append(f"")
        summary.append(f"== Reference (Imaris/manual) ==")
        summary.append(f"Reference PC                   : {args.ref_pc}")
        if args.ref_cond is not None:
            summary.append(f"Reference cond density         : {args.ref_cond}")
        if args.ref_dil is not None:
            summary.append(f"Reference dilute density       : {args.ref_dil}")

    summary_text = "\n".join(summary)
    print("\n" + summary_text)
    (output_dir / "summary.txt").write_text(summary_text)

    # Visualisations
    midZ = Z // 2

    # 1. Raw mid-Z slices
    fig, ax = plt.subplots(1, 2, figsize=(11, 5))
    ax[0].imshow(nuc_stack[midZ],  cmap="Blues")
    ax[0].set_title(f"Nuclei channel  z={midZ}")
    ax[0].axis("off")
    ax[1].imshow(cond_stack[midZ], cmap="Greens")
    ax[1].set_title(f"Condensate channel  z={midZ}")
    ax[1].axis("off")
    plt.tight_layout()
    plt.savefig(output_dir / "raw_midZ.png", dpi=150)
    plt.close()

    # 2. Mask overlay on raw condensate
    fig, ax = plt.subplots(1, 3, figsize=(15, 5))
    ax[0].imshow(cond_stack[midZ], cmap="gray")
    ax[0].set_title("Raw condensate")
    ax[0].axis("off")

    # condensate mask edges
    ax[1].imshow(cond_stack[midZ], cmap="gray")
    cm = cond_3d[midZ]
    ax[1].contour(cm, levels=[0.5], colors="lime", linewidths=0.6)
    nm = nuc_3d[midZ]
    ax[1].contour(nm, levels=[0.5], colors="cyan",  linewidths=0.8)
    ax[1].set_title("Cond mask (green) + central nucleus (cyan)")
    ax[1].axis("off")

    # used-for-PC region (cond & nuc)
    ax[2].imshow(cond_stack[midZ], cmap="gray")
    used = (cond_3d & nuc_3d)[midZ]
    ax[2].imshow(np.where(used, 1, np.nan), cmap="autumn", alpha=0.45)
    ax[2].set_title("Voxels used for cond density (red)")
    ax[2].axis("off")
    plt.tight_layout()
    plt.savefig(output_dir / "mask_overlay.png", dpi=150)
    plt.close()

    # 3. Intensity histograms
    fig, ax = plt.subplots(1, 2, figsize=(12, 4))
    if nuclear_cond.any():
        ax[0].hist(np.clip(cond_vals_in_mask - B, 0, None), bins=80, color="green", alpha=0.7)
        ax[0].axvline(cond_density_pipe, color="red", linestyle="--",
                      label=f"pipeline mean = {cond_density_pipe:.1f}")
        if args.ref_cond is not None:
            ax[0].axvline(args.ref_cond, color="blue", linestyle="--",
                          label=f"reference     = {args.ref_cond:.1f}")
        ax[0].set_title("Intensity inside cond mask (B-subtracted)")
        ax[0].set_xlabel("Intensity")
        ax[0].legend(fontsize=9)

    if dilute_3d.any():
        dil_vals = np.clip(cond_stack[dilute_3d].astype(np.float64) - B, 0, None)
        ax[1].hist(dil_vals, bins=80, color="gray", alpha=0.7)
        ax[1].set_title("Intensity inside nuclear dilute region (B-subtracted)")
        ax[1].set_xlabel("Intensity")
    plt.tight_layout()
    plt.savefig(output_dir / "intensity_hist.png", dpi=150)
    plt.close()

    print(f"\nSaved to: {output_dir}")


if __name__ == "__main__":
    main()
