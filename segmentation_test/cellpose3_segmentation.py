from pathlib import Path

import numpy as np
import pandas as pd
import tifffile as tiff
import matplotlib.pyplot as plt
from skimage.measure import regionprops_table

import torch
from cellpose import models, core, denoise

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "segmentation_test" / "outputs" / "cellpose3"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

COND_PATH = DATA_DIR / "raw_condensates" / "C2-ROI_raw_stack_sample2_5.tif"
NUC_PATH  = DATA_DIR / "raw_nuclei"     / "C1-ROI_raw_stack_sample2_5.tif"

USE_GPU = core.use_gpu()
print(f"GPU available: {USE_GPU}")
if USE_GPU:
    print(f"  {torch.cuda.get_device_name(0)}")

# ── Step 1: Restore images with Cellpose 3 denoising ─────────────────────────
# denoise_cyto3 removes shot noise from confocal/widefield stacks before
# segmentation, which tightens condensate boundaries and improves the PC.
print("\nRestoring images with Cellpose 3 denoising...")
dn_model = denoise.DenoiseModel(model_type="denoise_cyto3", gpu=USE_GPU)

cond_stack = tiff.imread(COND_PATH)
nuc_stack  = tiff.imread(NUC_PATH)
print(f"Condensate stack: {cond_stack.shape}  Nuclei stack: {nuc_stack.shape}")

# DenoiseModel.eval expects a list of 2D arrays
cond_restored = dn_model.eval(
    [cond_stack[z] for z in range(cond_stack.shape[0])],
    diameter=None,
    channels=[0, 0],
)
nuc_restored = dn_model.eval(
    [nuc_stack[z] for z in range(nuc_stack.shape[0])],
    diameter=None,
    channels=[0, 0],
)

cond_restored = np.stack(cond_restored)
nuc_restored  = np.stack(nuc_restored)

# Save restored stacks so you can inspect them in Fiji
tiff.imwrite(OUTPUT_DIR / "cond_restored.tif", cond_restored)
tiff.imwrite(OUTPUT_DIR / "nuc_restored.tif",  nuc_restored)
print("Restored stacks saved.")

# ── Step 2: Segment with Cellpose 3 in native 3D mode ────────────────────────
# do_3D=True processes XY, XZ, YZ planes and merges gradient flows — no
# slice-by-slice stitching artefacts. Requires more VRAM (RTX 4080 is fine).
print("\nSegmenting with Cellpose 3 (do_3D=True)...")
seg_model = models.CellposeModel(gpu=USE_GPU, model_type="cyto3")

cond_masks_3d, _, _ = seg_model.eval(
    cond_restored,
    do_3D=True,
    diameter=None,
    channels=[0, 0],
)

nuc_masks_3d, _, _ = seg_model.eval(
    nuc_restored,
    do_3D=True,
    diameter=None,
    channels=[0, 0],
)

print(f"  Condensate objects: {cond_masks_3d.max()}")
print(f"  Nuclei objects    : {nuc_masks_3d.max()}")

# ── Step 3: Extract per-slice measurements ───────────────────────────────────
cond_measurements = []
nuc_measurements  = []

for z in range(cond_stack.shape[0]):
    for masks, stack, measurements, name in [
        (cond_masks_3d, cond_stack, cond_measurements, "condensates"),
        (nuc_masks_3d,  nuc_stack,  nuc_measurements,  "nuclei"),
    ]:
        props = regionprops_table(
            masks[z],
            intensity_image=stack[z],
            properties=["label", "area", "centroid", "mean_intensity"],
        )
        df = pd.DataFrame(props)
        if not df.empty:
            df["z"] = z
        else:
            df = pd.DataFrame(columns=["label", "area", "centroid-0", "centroid-1", "mean_intensity", "z"])
        measurements.append(df)

cond_df = pd.concat(cond_measurements, ignore_index=True)
nuc_df  = pd.concat(nuc_measurements,  ignore_index=True)

# ── Step 4: Partition coefficient (background-subtracted) ────────────────────
# Reference method (Fabrini et al.):
#   B = minimum voxel intensity across the full FOV
#   condensed density = Σ clip(pixel - B, 0) over nuclear condensate voxels / n voxels
#   dilute density    = mean clip(pixel - B, 0) over a 10×10×10 patch from nuclear dilute phase
B = float(cond_stack.min())

cond_3d   = cond_masks_3d > 0
nuc_3d    = nuc_masks_3d  > 0

# Condensed density
nuclear_cond_mask = cond_3d & nuc_3d
cond_vals         = cond_stack[nuclear_cond_mask].astype(np.float64) - B
cond_vals         = np.clip(cond_vals, 0, None)
cond_density      = cond_vals.sum() / nuclear_cond_mask.sum()

# Dilute density — 10×10×10 voxel patch entirely within nuclear dilute phase
dilute_3d_mask = nuc_3d & ~cond_3d
PATCH = 10
Z, Y, X = cond_stack.shape
rng = np.random.default_rng(42)

candidates = np.argwhere(dilute_3d_mask)
in_bounds  = candidates[
    (candidates[:, 0] + PATCH <= Z) &
    (candidates[:, 1] + PATCH <= Y) &
    (candidates[:, 2] + PATCH <= X)
]
rng.shuffle(in_bounds)

dilute_density = None
for z0, y0, x0 in in_bounds[:2000]:
    if dilute_3d_mask[z0:z0+PATCH, y0:y0+PATCH, x0:x0+PATCH].all():
        patch          = cond_stack[z0:z0+PATCH, y0:y0+PATCH, x0:x0+PATCH].astype(np.float64) - B
        dilute_density = np.clip(patch, 0, None).mean()
        break

if dilute_density is None:
    dilute_density = np.clip(
        cond_stack[dilute_3d_mask].astype(np.float64) - B, 0, None
    ).mean()

pc = cond_density / dilute_density

print(f"\nCellpose 3 Partition Coefficient (background-subtracted): {pc:.3f}")
print(f"  Background (min FOV intensity) : {B:.2f}")
print(f"  Condensate density             : {cond_density:.2f}")
print(f"  Dilute density                 : {dilute_density:.2f}")
print(f"  Total condensates              : {len(cond_df)}")

# ── Save outputs ─────────────────────────────────────────────────────────────
tiff.imwrite(OUTPUT_DIR / "cp3_condensate_masks.tif", cond_masks_3d.astype(np.int32))
tiff.imwrite(OUTPUT_DIR / "cp3_nuclei_masks.tif",     nuc_masks_3d.astype(np.int32))
cond_df.to_csv(OUTPUT_DIR / "cp3_condensate_measurements.csv", index=False)
nuc_df.to_csv(OUTPUT_DIR  / "cp3_nuclei_measurements.csv",     index=False)

summary = pd.DataFrame({
    "metric": ["partition_coefficient", "background", "condensate_density", "dilute_density", "n_condensates"],
    "value":  [pc, B, cond_density, dilute_density, len(cond_df)],
})
summary.to_csv(OUTPUT_DIR / "cp3_summary.csv", index=False)

# ── Visualisation ─────────────────────────────────────────────────────────────
mid_z = cond_stack.shape[0] // 2
fig, axs = plt.subplots(2, 3, figsize=(15, 8))

axs[0, 0].imshow(cond_stack[mid_z], cmap="gray")
axs[0, 0].set_title(f"Raw condensates (z={mid_z})")

axs[0, 1].imshow(cond_restored[mid_z], cmap="gray")
axs[0, 1].set_title("After Cellpose 3 denoising")

axs[0, 2].imshow(cond_masks_3d[mid_z], cmap="tab20")
axs[0, 2].set_title("Cellpose 3 masks (do_3D=True)")

axs[1, 0].hist(cond_df["area"], bins=40, color="steelblue")
axs[1, 0].set_title("Condensate area distribution")
axs[1, 0].set_xlabel("Area (px²)")

axs[1, 1].hist(cond_df["mean_intensity"], bins=40, color="steelblue")
axs[1, 1].set_title("Condensate intensity distribution")
axs[1, 1].set_xlabel("Mean intensity")

counts = cond_df.groupby("z")["label"].count()
axs[1, 2].plot(counts.index, counts.values)
axs[1, 2].set_title("Condensates per Z-slice")
axs[1, 2].set_xlabel("Z-slice")
axs[1, 2].set_ylabel("Count")

plt.tight_layout()
plt.savefig(OUTPUT_DIR / "cp3_results.png", dpi=150)
plt.close()
print(f"\nSaved to: {OUTPUT_DIR}")
