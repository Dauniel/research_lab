"""
test_stitch_nuclei.py — Test 2D slice-by-slice + stitch_threshold for nuclei.

Identical to spring_implementation/pipeline.py except nuclei segmentation uses:
    do_3D=False  +  stitch_threshold=0.5

Instead of do_3D=True, Cellpose segments each Z-slice independently then
stitches adjacent masks by IoU overlap. Works better for large spherical
nuclei where the 3D gradient flow over-splits internal texture into fragments.

Goal: reduce nuclei from ~76 fragments to ~3 proper objects and see if
the better nuclear mask improves PC toward reference 6.32.

Usage (from repo root):
    python nuclei_model_test/test_stitch_nuclei.py
"""

import numpy as np
import pandas as pd
import tifffile as tiff
import matplotlib.pyplot as plt
from skimage.measure import regionprops_table
from pathlib import Path

import torch
from cellpose import models, core, denoise

COND_PATH = Path("data/raw_condensates/C2-ROI_raw_stack_sample2_5.tif")
NUC_PATH  = Path("data/raw_nuclei/C1-ROI_raw_stack_sample2_5.tif")
OUTPUT    = Path("nuclei_model_test/outputs/stitch")


def load_stacks():
    cond = tiff.imread(COND_PATH)
    nuc  = tiff.imread(NUC_PATH)
    print(f"Condensate : {cond.shape}  dtype={cond.dtype}")
    print(f"Nuclei     : {nuc.shape}  dtype={nuc.dtype}")
    return cond, nuc


def denoise_stack(stack, dn_model, label):
    print(f"  Denoising {label}...")
    restored = dn_model.eval(
        [stack[z] for z in range(stack.shape[0])],
        diameter=None,
        channels=[0, 0],
    )
    return np.stack(restored)


def segment_condensates(stack, model):
    print("  Segmenting condensates — cyto3, do_3D=True...")
    masks, _, _ = model.eval(stack, do_3D=True, diameter=None, channels=[0, 0])
    print(f"    {masks.max()} condensates found")
    return masks.astype(np.int32)


def segment_nuclei_stitch(stack, model, stitch_threshold):
    print(f"  Segmenting nuclei — cyto3, 2D + stitch_threshold={stitch_threshold}...")
    masks, _, _ = model.eval(
        stack,
        do_3D=False,
        stitch_threshold=stitch_threshold,
        diameter=None,
        cellprob_threshold=-2.0,
        channels=[0, 0],
    )
    print(f"    {masks.max()} nuclei found")
    return masks.astype(np.int32)


def compute_pc(cond_stack, cond_masks, nuc_masks):
    B       = float(cond_stack.min())
    cond_3d = cond_masks > 0
    nuc_3d  = nuc_masks  > 0

    nuclear_cond = cond_3d & nuc_3d
    cond_vals    = np.clip(cond_stack[nuclear_cond].astype(np.float64) - B, 0, None)
    cond_density = cond_vals.sum() / nuclear_cond.sum()

    dilute_3d  = nuc_3d & ~cond_3d
    PATCH      = 10
    N_PATCHES  = 50
    Z, Y, X    = cond_stack.shape
    rng        = np.random.default_rng(42)
    candidates = np.argwhere(dilute_3d)
    in_bounds  = candidates[
        (candidates[:, 0] + PATCH <= Z) &
        (candidates[:, 1] + PATCH <= Y) &
        (candidates[:, 2] + PATCH <= X)
    ]
    rng.shuffle(in_bounds)

    patch_means = []
    for z0, y0, x0 in in_bounds:
        if len(patch_means) == N_PATCHES:
            break
        if dilute_3d[z0:z0+PATCH, y0:y0+PATCH, x0:x0+PATCH].all():
            patch = cond_stack[z0:z0+PATCH, y0:y0+PATCH, x0:x0+PATCH].astype(np.float64) - B
            patch_means.append(np.clip(patch, 0, None).mean())

    dilute_density = float(np.mean(patch_means)) if patch_means else np.clip(
        cond_stack[dilute_3d].astype(np.float64) - B, 0, None
    ).mean()

    return {
        "pc":            cond_density / dilute_density,
        "background":    B,
        "cond_density":  cond_density,
        "dilute_density": dilute_density,
        "n_patches_used": len(patch_means),
    }


def plot_results(output_dir, cond_stack, cond_masks, nuc_masks, pc):
    mid_z = cond_stack.shape[0] // 2
    fig, axs = plt.subplots(1, 3, figsize=(15, 5))

    axs[0].imshow(cond_stack[mid_z], cmap="gray")
    axs[0].set_title(f"Raw condensates (z={mid_z})")
    axs[0].axis("off")

    axs[1].imshow(nuc_masks[mid_z], cmap="tab20")
    axs[1].set_title(f"Nuclei — 2D + stitch\n{nuc_masks.max()} objects (3D)")
    axs[1].axis("off")

    axs[2].imshow(cond_masks[mid_z], cmap="tab20")
    axs[2].set_title(f"Condensate masks — cyto3 do_3D\nPC = {pc['pc']:.3f}  (reference = 6.32)")
    axs[2].axis("off")

    plt.tight_layout()
    plt.savefig(output_dir / "results.png", dpi=150)
    plt.close()


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)

    use_gpu = core.use_gpu()
    print(f"GPU: {'enabled — ' + torch.cuda.get_device_name(0) if use_gpu else 'disabled'}")

    print("\n[1/5] Loading stacks...")
    cond_stack, nuc_stack = load_stacks()

    print("\n[2/5] Denoising...")
    dn_model      = denoise.DenoiseModel(model_type="denoise_cyto3", gpu=use_gpu)
    cond_restored = denoise_stack(cond_stack, dn_model, "condensates")
    nuc_restored  = denoise_stack(nuc_stack,  dn_model, "nuclei")

    print("\n[3/5] Segmenting...")
    seg_model     = models.CellposeModel(gpu=use_gpu, model_type="cyto3")
    cond_masks    = segment_condensates(cond_restored, seg_model)
    nuc_masks     = segment_nuclei_stitch(nuc_restored, seg_model, stitch_threshold=0.5)

    print("\n[4/5] Computing partition coefficient (50-patch average)...")
    pc = compute_pc(cond_stack, cond_masks, nuc_masks)
    print(f"    Partition Coefficient : {pc['pc']:.3f}  (reference = 6.32)")
    print(f"    Background (B)        : {pc['background']:.2f}")
    print(f"    Condensate density    : {pc['cond_density']:.2f}")
    print(f"    Dilute density        : {pc['dilute_density']:.2f}")
    print(f"    Patches used          : {pc['n_patches_used']}/50")

    print("\n[5/5] Saving outputs...")
    tiff.imwrite(OUTPUT / "condensate_masks.tif", cond_masks)
    tiff.imwrite(OUTPUT / "nuclei_masks.tif",     nuc_masks)

    summary = [
        ("partition_coefficient", pc["pc"]),
        ("background",            pc["background"]),
        ("condensate_density",    pc["cond_density"]),
        ("dilute_density",        pc["dilute_density"]),
        ("n_patches_used",        pc["n_patches_used"]),
        ("n_condensates",         int(cond_masks.max())),
        ("n_nuclei",              int(nuc_masks.max())),
        ("nuc_segmentation",      "cyto3_2D_stitch0.5"),
        ("cond_segmentation",     "cyto3_3D"),
    ]
    pd.DataFrame(summary, columns=["metric", "value"]).to_csv(
        OUTPUT / "summary.csv", index=False
    )

    plot_results(OUTPUT, cond_stack, cond_masks, nuc_masks, pc)
    print(f"\nOutputs saved to: {OUTPUT}")


if __name__ == "__main__":
    main()
