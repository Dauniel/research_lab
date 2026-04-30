"""
test_nuclei_model.py — Test using model_type="nuclei" for nucleus segmentation.

Identical to spring_implementation/pipeline.py except:
  - Condensates: CellposeModel(model_type="cyto3")       [unchanged]
  - Nuclei:      CellposeModel(model_type="nuclei")       [changed]

Goal: check whether the dedicated nuclei model reduces over-segmentation
(currently ~76 fragments for ~3 true nuclei) and whether PC shifts
relative to reference 6.32.

Usage:
    python nuclei_model_test/test_nuclei_model.py \
        --cond data/raw_condensates/C2-ROI_raw_stack_sample2_5.tif \
        --nuc  data/raw_nuclei/C1-ROI_raw_stack_sample2_5.tif
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import tifffile as tiff
import matplotlib.pyplot as plt
from skimage.measure import regionprops_table

import torch
from cellpose import models, core, denoise


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--cond",   required=True, type=Path)
    p.add_argument("--nuc",    required=True, type=Path)
    p.add_argument("--output", default=None,  type=Path)
    p.add_argument("--no-gpu", action="store_true")
    return p.parse_args()


def load_stacks(cond_path, nuc_path):
    cond_stack = tiff.imread(cond_path)
    nuc_stack  = tiff.imread(nuc_path)
    print(f"Condensate stack : {cond_stack.shape}  dtype={cond_stack.dtype}")
    print(f"Nuclei stack     : {nuc_stack.shape}  dtype={nuc_stack.dtype}")
    return cond_stack, nuc_stack


def denoise_stack(stack, dn_model, label):
    print(f"  Denoising {label}...")
    restored = dn_model.eval(
        [stack[z] for z in range(stack.shape[0])],
        diameter=None,
        channels=[0, 0],
    )
    return np.stack(restored)


def segment_condensates(stack, seg_model):
    print("  Segmenting condensates — cyto3, do_3D=True...")
    masks, _, _ = seg_model.eval(stack, do_3D=True, diameter=None, channels=[0, 0])
    print(f"    {masks.max()} condensates found")
    return masks.astype(np.int32)


def segment_nuclei(stack, nuc_model):
    print("  Segmenting nuclei — nuclei model, do_3D=True...")
    masks, _, _ = nuc_model.eval(stack, do_3D=True, diameter=None, channels=[0, 0])
    print(f"    {masks.max()} nuclei found")
    return masks.astype(np.int32)


def extract_slice_measurements(masks_3d, raw_stack):
    rows = []
    for z in range(raw_stack.shape[0]):
        props = regionprops_table(
            masks_3d[z],
            intensity_image=raw_stack[z],
            properties=["label", "area", "centroid", "mean_intensity"],
        )
        df = pd.DataFrame(props)
        if not df.empty:
            df["z"] = z
            rows.append(df)
    if rows:
        return pd.concat(rows, ignore_index=True)
    return pd.DataFrame(columns=["label", "area", "centroid-0", "centroid-1", "mean_intensity", "z"])


def compute_volumes(masks_3d):
    props = regionprops_table(masks_3d, properties=["label", "area"])
    return pd.DataFrame(props).rename(columns={"area": "volume_voxels"})


def compute_partition_coefficient(cond_stack, cond_masks_3d, nuc_masks_3d):
    B       = float(cond_stack.min())
    cond_3d = cond_masks_3d > 0
    nuc_3d  = nuc_masks_3d  > 0

    nuclear_cond = cond_3d & nuc_3d
    cond_vals    = np.clip(cond_stack[nuclear_cond].astype(np.float64) - B, 0, None)
    cond_density = cond_vals.sum() / nuclear_cond.sum()

    dilute_3d  = nuc_3d & ~cond_3d
    PATCH      = 10
    Z, Y, X    = cond_stack.shape
    rng        = np.random.default_rng(42)
    candidates = np.argwhere(dilute_3d)
    in_bounds  = candidates[
        (candidates[:, 0] + PATCH <= Z) &
        (candidates[:, 1] + PATCH <= Y) &
        (candidates[:, 2] + PATCH <= X)
    ]
    rng.shuffle(in_bounds)

    dilute_density = None
    for z0, y0, x0 in in_bounds[:2000]:
        if dilute_3d[z0:z0+PATCH, y0:y0+PATCH, x0:x0+PATCH].all():
            patch          = cond_stack[z0:z0+PATCH, y0:y0+PATCH, x0:x0+PATCH].astype(np.float64) - B
            dilute_density = np.clip(patch, 0, None).mean()
            break

    if dilute_density is None:
        dilute_density = np.clip(
            cond_stack[dilute_3d].astype(np.float64) - B, 0, None
        ).mean()

    return {
        "pc":            cond_density / dilute_density,
        "background":    B,
        "cond_density":  cond_density,
        "dilute_density": dilute_density,
    }


def plot_results(output_dir, cond_stack, cond_masks_3d, nuc_masks_3d, pc_result):
    mid_z = cond_stack.shape[0] // 2
    fig, axs = plt.subplots(1, 3, figsize=(15, 5))

    axs[0].imshow(cond_stack[mid_z], cmap="gray")
    axs[0].set_title(f"Raw condensates (z={mid_z})")
    axs[0].axis("off")

    axs[1].imshow(nuc_masks_3d[mid_z], cmap="tab20")
    axs[1].set_title(f"Nuclei masks — model_type='nuclei'\n{nuc_masks_3d.max()} objects (3D)")
    axs[1].axis("off")

    axs[2].imshow(cond_masks_3d[mid_z], cmap="tab20")
    axs[2].set_title(f"Condensate masks — cyto3\nPC = {pc_result['pc']:.3f}  (reference = 6.32)")
    axs[2].axis("off")

    plt.tight_layout()
    plt.savefig(output_dir / "results.png", dpi=150)
    plt.close()
    print(f"  Saved results.png")


def main():
    args   = parse_args()
    output = args.output or (Path(__file__).parent / "outputs")
    output.mkdir(parents=True, exist_ok=True)

    use_gpu = core.use_gpu() and not args.no_gpu
    print(f"GPU: {'enabled — ' + torch.cuda.get_device_name(0) if use_gpu else 'disabled'}")

    print("\n[1/5] Loading stacks...")
    cond_stack, nuc_stack = load_stacks(args.cond, args.nuc)

    print("\n[2/5] Denoising with Cellpose 3 DenoiseModel (cyto3)...")
    dn_model      = denoise.DenoiseModel(model_type="denoise_cyto3", gpu=use_gpu)
    cond_restored = denoise_stack(cond_stack, dn_model, "condensates")
    nuc_restored  = denoise_stack(nuc_stack,  dn_model, "nuclei")

    print("\n[3/5] Segmenting...")
    cond_model    = models.CellposeModel(gpu=use_gpu, model_type="cyto3")
    nuc_model     = models.CellposeModel(gpu=use_gpu, model_type="nuclei")
    cond_masks_3d = segment_condensates(cond_restored, cond_model)
    nuc_masks_3d  = segment_nuclei(nuc_restored, nuc_model)

    print("\n[4/5] Computing partition coefficient (Fabrini method)...")
    pc_result = compute_partition_coefficient(cond_stack, cond_masks_3d, nuc_masks_3d)
    print(f"    Partition Coefficient : {pc_result['pc']:.3f}  (reference = 6.32)")
    print(f"    Background (B)        : {pc_result['background']:.2f}")
    print(f"    Condensate density    : {pc_result['cond_density']:.2f}")
    print(f"    Dilute density        : {pc_result['dilute_density']:.2f}")

    print("\n[5/5] Saving outputs...")
    tiff.imwrite(output / "condensate_masks.tif", cond_masks_3d)
    tiff.imwrite(output / "nuclei_masks.tif",     nuc_masks_3d)

    cond_df    = extract_slice_measurements(cond_masks_3d, cond_stack)
    nuc_df     = extract_slice_measurements(nuc_masks_3d,  nuc_stack)
    cond_vol   = compute_volumes(cond_masks_3d)
    nuc_vol    = compute_volumes(nuc_masks_3d)

    cond_df.to_csv(output  / "condensate_measurements.csv", index=False)
    nuc_df.to_csv(output   / "nuclei_measurements.csv",     index=False)
    cond_vol.to_csv(output / "condensate_volumes.csv",      index=False)
    nuc_vol.to_csv(output  / "nuclei_volumes.csv",          index=False)

    summary = [
        ("partition_coefficient", pc_result["pc"]),
        ("background",            pc_result["background"]),
        ("condensate_density",    pc_result["cond_density"]),
        ("dilute_density",        pc_result["dilute_density"]),
        ("n_condensates",         int(cond_vol["label"].nunique())),
        ("n_nuclei",              int(nuc_vol["label"].nunique())),
        ("nuc_model",             "nuclei"),
        ("cond_model",            "cyto3"),
    ]
    pd.DataFrame(summary, columns=["metric", "value"]).to_csv(output / "summary.csv", index=False)

    plot_results(output, cond_stack, cond_masks_3d, nuc_masks_3d, pc_result)
    print(f"\nAll outputs saved to: {output}")


if __name__ == "__main__":
    main()
