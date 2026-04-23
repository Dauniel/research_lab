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

# ── Step 4: Partition coefficient ────────────────────────────────────────────
cond_pixels_all   = []
dilute_pixels_all = []

for z in range(cond_stack.shape[0]):
    cond_mask  = cond_masks_3d[z] > 0
    nuc_mask   = nuc_masks_3d[z]  > 0
    img        = cond_stack[z]

    cond_pixels   = img[cond_mask & nuc_mask]
    dilute_pixels = img[nuc_mask & ~cond_mask]

    if cond_pixels.size   > 0: cond_pixels_all.append(cond_pixels)
    if dilute_pixels.size > 0: dilute_pixels_all.append(dilute_pixels)

cond_density   = np.mean(np.concatenate(cond_pixels_all))
dilute_density = np.mean(np.concatenate(dilute_pixels_all))
pc             = cond_density / dilute_density

print(f"\nCellpose 3 Partition Coefficient: {pc:.3f}")
print(f"  Condensate density : {cond_density:.2f}")
print(f"  Dilute density     : {dilute_density:.2f}")
print(f"  Total condensates  : {len(cond_df)}")

# ── Save outputs ─────────────────────────────────────────────────────────────
tiff.imwrite(OUTPUT_DIR / "cp3_condensate_masks.tif", cond_masks_3d.astype(np.int32))
tiff.imwrite(OUTPUT_DIR / "cp3_nuclei_masks.tif",     nuc_masks_3d.astype(np.int32))
cond_df.to_csv(OUTPUT_DIR / "cp3_condensate_measurements.csv", index=False)
nuc_df.to_csv(OUTPUT_DIR  / "cp3_nuclei_measurements.csv",     index=False)

summary = pd.DataFrame({
    "metric": ["partition_coefficient", "condensate_density", "dilute_density", "n_condensates"],
    "value":  [pc, cond_density, dilute_density, len(cond_df)],
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
