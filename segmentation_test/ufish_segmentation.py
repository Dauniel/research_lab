from pathlib import Path

import numpy as np
import pandas as pd
import tifffile as tiff
import matplotlib.pyplot as plt
from skimage.draw import disk
from skimage.filters import threshold_otsu
from skimage.morphology import binary_closing, disk as morphdisk

from ufish.api import UFish

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "segmentation_test" / "outputs" / "ufish"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

COND_PATH = DATA_DIR / "raw_condensates" / "C2-ROI_raw_stack_sample2_5.tif"
NUC_PATH  = DATA_DIR / "raw_nuclei"     / "C1-ROI_raw_stack_sample2_5.tif"

# Radius (pixels) used to build a binary mask around each detected spot centre.
# Adjust to match the typical condensate radius in your images.
SPOT_RADIUS = 3


def spots_to_mask(spots_df, shape):
    """Convert U-FISH spot coordinates into a 2D binary mask."""
    mask = np.zeros(shape, dtype=bool)
    for _, row in spots_df.iterrows():
        r, c = int(round(row["axis-0"])), int(round(row["axis-1"]))
        rr, cc = disk((r, c), SPOT_RADIUS, shape=shape)
        mask[rr, cc] = True
    return mask


# Load stacks
cond_stack = tiff.imread(COND_PATH)
nuc_stack  = tiff.imread(NUC_PATH)
print(f"Condensate stack: {cond_stack.shape}  Nuclei stack: {nuc_stack.shape}")

# Initialise U-FISH and download pre-trained weights (cached after first run)
print("Loading U-FISH weights...")
ufish = UFish()
ufish.load_weights()

# Run spot detection slice by slice and build mask stack
print("Running U-FISH spot detection...")
cond_mask_stack = np.zeros(cond_stack.shape, dtype=bool)
nuc_mask_stack  = np.zeros(nuc_stack.shape,  dtype=bool)
all_spots       = []

for z in range(cond_stack.shape[0]):
    cond_spots, _ = ufish.predict(cond_stack[z])
    cond_mask_stack[z] = spots_to_mask(cond_spots, cond_stack[z].shape)

    # Nuclei are large diffuse objects — Otsu threshold works better than spot detection
    nuc_img = nuc_stack[z].astype(np.float32)
    thresh = threshold_otsu(nuc_img)
    nuc_mask_stack[z] = binary_closing(nuc_img > thresh, morphdisk(5))

    cond_spots["z"] = z
    all_spots.append(cond_spots)

    print(f"  z={z:02d}  condensate spots={len(cond_spots)}")

spots_df = pd.concat(all_spots, ignore_index=True)

# Partition coefficient
cond_pixels_all   = []
dilute_pixels_all = []

for z in range(cond_stack.shape[0]):
    cond_mask  = cond_mask_stack[z]
    nuc_mask   = nuc_mask_stack[z]
    img        = cond_stack[z]

    cond_pixels   = img[cond_mask & nuc_mask]
    dilute_pixels = img[nuc_mask & ~cond_mask]

    if cond_pixels.size   > 0: cond_pixels_all.append(cond_pixels)
    if dilute_pixels.size > 0: dilute_pixels_all.append(dilute_pixels)

cond_density   = np.mean(np.concatenate(cond_pixels_all))
dilute_density = np.mean(np.concatenate(dilute_pixels_all))
pc             = cond_density / dilute_density

print(f"\nU-FISH Partition Coefficient: {pc:.3f}")
print(f"  Condensate density : {cond_density:.2f}")
print(f"  Dilute density     : {dilute_density:.2f}")
print(f"  Total spots        : {len(spots_df)}")

# Save outputs
tiff.imwrite(OUTPUT_DIR / "ufish_condensate_masks.tif", cond_mask_stack.astype(np.uint8))
tiff.imwrite(OUTPUT_DIR / "ufish_nuclei_masks.tif",     nuc_mask_stack.astype(np.uint8))
spots_df.to_csv(OUTPUT_DIR / "ufish_spots.csv", index=False)

summary = pd.DataFrame({
    "metric": ["partition_coefficient", "condensate_density", "dilute_density", "total_spots"],
    "value":  [pc, cond_density, dilute_density, len(spots_df)],
})
summary.to_csv(OUTPUT_DIR / "ufish_summary.csv", index=False)

# Visualisation
mid_z = cond_stack.shape[0] // 2
fig, axs = plt.subplots(1, 3, figsize=(15, 4))

axs[0].imshow(cond_stack[mid_z], cmap="gray")
axs[0].set_title(f"Raw condensates (z={mid_z})")

axs[1].imshow(cond_stack[mid_z], cmap="gray")
mid_spots = spots_df[spots_df["z"] == mid_z]
axs[1].scatter(mid_spots["axis-1"], mid_spots["axis-0"], s=20, c="red", alpha=0.7)
axs[1].set_title(f"U-FISH detections (z={mid_z})")

counts_per_z = spots_df.groupby("z").size()
axs[2].plot(counts_per_z.index, counts_per_z.values)
axs[2].set_title("Spots per Z-slice")
axs[2].set_xlabel("Z-slice")
axs[2].set_ylabel("Spot count")

plt.tight_layout()
plt.savefig(OUTPUT_DIR / "ufish_results.png", dpi=150)
plt.close()
print(f"\nSaved to: {OUTPUT_DIR}")
