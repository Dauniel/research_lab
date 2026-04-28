"""
pipeline.py — Spring 2026 Cellpose 3 condensate analysis pipeline.

Usage:
    python pipeline.py --cond <condensate_tif> --nuc <nuclei_tif> [options]

Options:
    --cond        Path to condensate channel Z-stack TIF (required)
    --nuc         Path to nuclei channel Z-stack TIF (required)
    --output      Output directory (default: spring_implementation/outputs)
    --voxel-xy    XY pixel size in µm, e.g. 0.065 (optional; volumes reported in voxels if omitted)
    --voxel-z     Z-slice spacing in µm, e.g. 0.3   (optional)
    --diameter      Cellpose condensate diameter in pixels, None = auto-detect (default: None)
    --nuc-diameter  Cellpose nuclei diameter in pixels, None = auto-detect (default: 60)
    --nuc-cellprob  Nuclei cell probability threshold (default: -2, lower = more merging)
    --no-gpu        Disable GPU even if available

Outputs (all written to --output):
    cond_restored.tif               denoised condensate stack
    nuc_restored.tif                denoised nuclei stack
    condensate_masks.tif            3D condensate instance labels
    nuclei_masks.tif                3D nuclei instance labels
    condensate_measurements.csv     per-slice regionprops (label, area, centroid, mean_intensity, z)
    nuclei_measurements.csv         per-slice regionprops
    condensate_volumes.csv          per-object 3D volume (voxels + µm³ if voxel sizes given)
    nuclei_volumes.csv              per-object 3D volume
    summary.csv                     partition coefficient + metadata
    results.png                     summary figure
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


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(
        description="Cellpose 3 condensate segmentation + partition coefficient pipeline."
    )
    p.add_argument("--cond",       required=True,  type=Path, help="Condensate channel TIF")
    p.add_argument("--nuc",        required=True,  type=Path, help="Nuclei channel TIF")
    p.add_argument("--output",     default=None,   type=Path, help="Output directory")
    p.add_argument("--voxel-xy",   default=None,   type=float, help="XY pixel size in µm")
    p.add_argument("--voxel-z",    default=None,   type=float, help="Z-slice spacing in µm")
    p.add_argument("--diameter",      default=None,  type=float, help="Cellpose condensate diameter (px)")
    p.add_argument("--nuc-diameter",  default=60.0,  type=float, help="Nuclei diameter (px)")
    p.add_argument("--nuc-cellprob",  default=-2.0,  type=float, help="Nuclei cellprob_threshold")
    p.add_argument("--no-gpu",        action="store_true",       help="Disable GPU")
    return p.parse_args()


# ── Step 1: Load ──────────────────────────────────────────────────────────────

def load_stacks(cond_path: Path, nuc_path: Path):
    """Load condensate and nuclei Z-stacks from TIF files."""
    cond_stack = tiff.imread(cond_path)
    nuc_stack  = tiff.imread(nuc_path)
    print(f"Condensate stack : {cond_stack.shape}  dtype={cond_stack.dtype}")
    print(f"Nuclei stack     : {nuc_stack.shape}  dtype={nuc_stack.dtype}")
    return cond_stack, nuc_stack


# ── Step 2: Denoise ───────────────────────────────────────────────────────────

def denoise_stack(stack: np.ndarray, dn_model, label: str) -> np.ndarray:
    """
    Restore a Z-stack with the Cellpose 3 DenoiseModel.

    DenoiseModel.eval expects a list of 2D arrays; returns a list of 2D arrays.
    Removes shot noise before segmentation, which tightens condensate boundaries.
    """
    print(f"  Denoising {label}...")
    restored = dn_model.eval(
        [stack[z] for z in range(stack.shape[0])],
        diameter=None,
        channels=[0, 0],
    )
    return np.stack(restored)


# ── Step 3: Segment ───────────────────────────────────────────────────────────

def segment_condensates(stack: np.ndarray, seg_model, diameter) -> np.ndarray:
    """Segment condensates with Cellpose 3 in native 3D mode."""
    print("  Segmenting condensates (do_3D=True)...")
    masks_3d, _, _ = seg_model.eval(
        stack,
        do_3D=True,
        diameter=diameter,
        channels=[0, 0],
    )
    print(f"    condensates: {masks_3d.max()} objects found")
    return masks_3d.astype(np.int32)


def segment_nuclei(stack: np.ndarray, seg_model, diameter, cellprob_threshold) -> np.ndarray:
    """
    Segment nuclei with Cellpose 3 in native 3D mode.

    Uses an explicit diameter and lower cellprob_threshold to prevent
    over-segmentation of large nuclei with internal texture variation.
    """
    print("  Segmenting nuclei (do_3D=True)...")
    masks_3d, _, _ = seg_model.eval(
        stack,
        do_3D=True,
        diameter=diameter,
        cellprob_threshold=cellprob_threshold,
        channels=[0, 0],
    )
    print(f"    nuclei: {masks_3d.max()} objects found")
    return masks_3d.astype(np.int32)


# ── Step 4: Per-slice measurements ───────────────────────────────────────────

def extract_slice_measurements(masks_3d: np.ndarray, raw_stack: np.ndarray) -> pd.DataFrame:
    """
    Compute per-slice regionprops from a 3D instance label volume.

    Uses the raw (undenoised) stack for intensity values so measurements
    reflect true signal, not denoising-modified values.

    Returns a DataFrame with columns: label, area, centroid-0, centroid-1,
    mean_intensity, z.
    """
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


# ── Step 5: 3D volume estimation ──────────────────────────────────────────────

def compute_volumes(masks_3d: np.ndarray, voxel_xy: float | None, voxel_z: float | None) -> pd.DataFrame:
    """
    Compute per-object 3D volume from a 3D instance label volume.

    Counts voxels per label (label 0 = background, excluded). If voxel_xy and
    voxel_z are provided, also reports physical volume in µm³.

    Returns a DataFrame with columns: label, volume_voxels[, volume_um3].
    """
    props = regionprops_table(masks_3d, properties=["label", "area"])
    df = pd.DataFrame(props).rename(columns={"area": "volume_voxels"})

    if voxel_xy is not None and voxel_z is not None:
        df["volume_um3"] = df["volume_voxels"] * (voxel_xy ** 2) * voxel_z
        print(f"    Voxel size: {voxel_xy} µm (XY) × {voxel_z} µm (Z)")

    return df


# ── Step 6: Partition coefficient ─────────────────────────────────────────────

def compute_partition_coefficient(
    cond_stack: np.ndarray,
    cond_masks_3d: np.ndarray,
    nuc_masks_3d: np.ndarray,
) -> dict:
    """
    Compute the nuclear partition coefficient using the Fabrini et al. method.

    B = minimum voxel intensity across the full FOV (camera background offset).
    Condensed density  = mean clip(pixel - B, 0) over voxels inside both nucleus
                         and condensate masks.
    Dilute density     = mean clip(pixel - B, 0) over the first fully-nuclear,
                         fully-dilute 10×10×10 voxel patch found (representative
                         sample of the nuclear dilute phase). Falls back to the
                         mean over all dilute voxels if no patch is found.
    PC = condensed density / dilute density.

    Returns a dict with keys: pc, background, cond_density, dilute_density.
    """
    B       = float(cond_stack.min())
    cond_3d = cond_masks_3d > 0
    nuc_3d  = nuc_masks_3d  > 0

    # Condensed phase
    nuclear_cond = cond_3d & nuc_3d
    cond_vals    = np.clip(cond_stack[nuclear_cond].astype(np.float64) - B, 0, None)
    cond_density = cond_vals.sum() / nuclear_cond.sum()

    # Dilute phase — 10×10×10 patch entirely within nuclear dilute region
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

    pc = cond_density / dilute_density
    return {"pc": pc, "background": B, "cond_density": cond_density, "dilute_density": dilute_density}


# ── Step 7: Save outputs ──────────────────────────────────────────────────────

def save_outputs(
    output_dir: Path,
    cond_restored, nuc_restored,
    cond_masks_3d, nuc_masks_3d,
    cond_df, nuc_df,
    cond_vol_df, nuc_vol_df,
    pc_result: dict,
    voxel_xy, voxel_z,
):
    """Save all masks, tables, and summary CSV to output_dir."""
    tiff.imwrite(output_dir / "cond_restored.tif",    cond_restored)
    tiff.imwrite(output_dir / "nuc_restored.tif",     nuc_restored)
    tiff.imwrite(output_dir / "condensate_masks.tif", cond_masks_3d)
    tiff.imwrite(output_dir / "nuclei_masks.tif",     nuc_masks_3d)

    cond_df.to_csv(output_dir / "condensate_measurements.csv", index=False)
    nuc_df.to_csv(output_dir  / "nuclei_measurements.csv",     index=False)
    cond_vol_df.to_csv(output_dir / "condensate_volumes.csv",  index=False)
    nuc_vol_df.to_csv(output_dir  / "nuclei_volumes.csv",      index=False)

    summary_rows = [
        ("partition_coefficient", pc_result["pc"]),
        ("background",            pc_result["background"]),
        ("condensate_density",    pc_result["cond_density"]),
        ("dilute_density",        pc_result["dilute_density"]),
        ("n_condensates",         int(cond_vol_df["label"].nunique())),
        ("n_nuclei",              int(nuc_vol_df["label"].nunique())),
        ("voxel_xy_um",           voxel_xy if voxel_xy else float("nan")),
        ("voxel_z_um",            voxel_z  if voxel_z  else float("nan")),
    ]
    pd.DataFrame(summary_rows, columns=["metric", "value"]).to_csv(
        output_dir / "summary.csv", index=False
    )


# ── Step 8: Visualisation ─────────────────────────────────────────────────────

def plot_summary(
    output_dir: Path,
    cond_stack, cond_restored, cond_masks_3d,
    cond_df, nuc_df,
    pc_result: dict,
):
    """Save a 2×3 summary figure to output_dir/results.png."""
    mid_z = cond_stack.shape[0] // 2
    fig, axs = plt.subplots(2, 3, figsize=(15, 8))

    axs[0, 0].imshow(cond_stack[mid_z], cmap="gray")
    axs[0, 0].set_title(f"Raw condensates (z={mid_z})")
    axs[0, 0].axis("off")

    axs[0, 1].imshow(cond_restored[mid_z], cmap="gray")
    axs[0, 1].set_title("After Cellpose 3 denoising")
    axs[0, 1].axis("off")

    axs[0, 2].imshow(cond_masks_3d[mid_z], cmap="tab20")
    axs[0, 2].set_title(f"Condensate masks (do_3D=True)\nPC = {pc_result['pc']:.3f}")
    axs[0, 2].axis("off")

    axs[1, 0].hist(cond_df["area"], bins=40, color="steelblue")
    axs[1, 0].set_title("Condensate area per slice (px²)")
    axs[1, 0].set_xlabel("Area")
    axs[1, 0].set_ylabel("Count")

    axs[1, 1].hist(cond_df["mean_intensity"], bins=40, color="steelblue")
    axs[1, 1].set_title("Condensate mean intensity")
    axs[1, 1].set_xlabel("Mean intensity")

    cond_counts = cond_df.groupby("z")["label"].count()
    nuc_counts  = nuc_df.groupby("z")["label"].count()
    axs[1, 2].plot(cond_counts.index, cond_counts.values, label="Condensates")
    axs[1, 2].plot(nuc_counts.index,  nuc_counts.values,  label="Nuclei")
    axs[1, 2].set_title("Objects per Z-slice")
    axs[1, 2].set_xlabel("Z-slice")
    axs[1, 2].set_ylabel("Count")
    axs[1, 2].legend()

    plt.tight_layout()
    plt.savefig(output_dir / "results.png", dpi=150)
    plt.close()


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    args = parse_args()

    output_dir = args.output or (Path(__file__).parent / "outputs")
    output_dir.mkdir(parents=True, exist_ok=True)

    use_gpu = core.use_gpu() and not args.no_gpu
    print(f"GPU: {'enabled — ' + torch.cuda.get_device_name(0) if use_gpu else 'disabled'}")

    # Load
    print("\n[1/6] Loading stacks...")
    cond_stack, nuc_stack = load_stacks(args.cond, args.nuc)

    # Denoise
    print("\n[2/6] Denoising with Cellpose 3 DenoiseModel...")
    dn_model     = denoise.DenoiseModel(model_type="denoise_cyto3", gpu=use_gpu)
    cond_restored = denoise_stack(cond_stack, dn_model, "condensates")
    nuc_restored  = denoise_stack(nuc_stack,  dn_model, "nuclei")

    # Segment
    print("\n[3/6] Segmenting with Cellpose 3 (cyto3, do_3D=True)...")
    seg_model     = models.CellposeModel(gpu=use_gpu, model_type="cyto3")
    cond_masks_3d = segment_condensates(cond_restored, seg_model, args.diameter)
    nuc_masks_3d  = segment_nuclei(nuc_restored, seg_model, args.nuc_diameter, args.nuc_cellprob)

    # Per-slice measurements
    print("\n[4/6] Extracting per-slice measurements...")
    cond_df = extract_slice_measurements(cond_masks_3d, cond_stack)
    nuc_df  = extract_slice_measurements(nuc_masks_3d,  nuc_stack)
    print(f"    Condensate rows: {len(cond_df)}  |  Nuclei rows: {len(nuc_df)}")

    # 3D volumes
    print("\n[5/6] Computing 3D volumes...")
    cond_vol_df = compute_volumes(cond_masks_3d, args.voxel_xy, args.voxel_z)
    nuc_vol_df  = compute_volumes(nuc_masks_3d,  args.voxel_xy, args.voxel_z)
    print(f"    Condensate objects: {len(cond_vol_df)}  |  Nuclei objects: {len(nuc_vol_df)}")

    # Partition coefficient
    print("\n[6/6] Computing partition coefficient...")
    pc_result = compute_partition_coefficient(cond_stack, cond_masks_3d, nuc_masks_3d)
    print(f"    Partition Coefficient : {pc_result['pc']:.3f}")
    print(f"    Background (B)        : {pc_result['background']:.2f}")
    print(f"    Condensate density    : {pc_result['cond_density']:.2f}")
    print(f"    Dilute density        : {pc_result['dilute_density']:.2f}")

    # Save
    save_outputs(
        output_dir,
        cond_restored, nuc_restored,
        cond_masks_3d, nuc_masks_3d,
        cond_df, nuc_df,
        cond_vol_df, nuc_vol_df,
        pc_result,
        args.voxel_xy, args.voxel_z,
    )
    plot_summary(output_dir, cond_stack, cond_restored, cond_masks_3d, cond_df, nuc_df, pc_result)

    print(f"\nAll outputs saved to: {output_dir}")


if __name__ == "__main__":
    main()
