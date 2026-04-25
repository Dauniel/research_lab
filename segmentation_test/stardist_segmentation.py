from pathlib import Path

import numpy as np
import pandas as pd
import tifffile as tiff
import matplotlib.pyplot as plt
from csbdeep.utils import normalize
from skimage.measure import regionprops_table
from stardist.models import StarDist2D

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "segmentation_test" / "outputs" / "stardist"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

COND_PATH = DATA_DIR / "raw_condensates" / "C2-ROI_raw_stack_sample2_5.tif"
NUC_PATH  = DATA_DIR / "raw_nuclei"     / "C1-ROI_raw_stack_sample2_5.tif"

# '2D_versatile_fluo' is the general-purpose fluorescence pre-trained model.
# For condensates (tiny objects), lower prob_thresh detects more dim spots;
# raise it to reduce false positives. nms_thresh controls overlap suppression.
PROB_THRESH = 0.3
NMS_THRESH  = 0.3


def segment_stack_stardist(stack, model, name="objects"):
    mask_stack   = []
    measurements = []

    for z in range(stack.shape[0]):
        img = stack[z].astype(np.float32)

        # Normalise per-slice using 1st–99.8th percentile (StarDist recommendation)
        img_norm = normalize(img, 1, 99.8, axis=(0, 1))

        labels, _ = model.predict_instances(
            img_norm,
            prob_thresh=PROB_THRESH,
            nms_thresh=NMS_THRESH,
        )
        mask_stack.append(labels.astype(np.int32))

        props = regionprops_table(
            labels,
            intensity_image=stack[z],
            properties=["label", "area", "centroid", "mean_intensity"],
        )
        df = pd.DataFrame(props)
        if not df.empty:
            df["z"] = z
        else:
            df = pd.DataFrame(columns=["label", "area", "centroid-0", "centroid-1", "mean_intensity", "z"])
        measurements.append(df)

        print(f"  {name} z={z:02d}: {labels.max()} objects")

    return np.stack(mask_stack), pd.concat(measurements, ignore_index=True)


# Load pre-trained fluorescence model (downloads on first run, ~50 MB)
print("Loading StarDist 2D_versatile_fluo model...")
model = StarDist2D.from_pretrained("2D_versatile_fluo")

cond_stack = tiff.imread(COND_PATH)
nuc_stack  = tiff.imread(NUC_PATH)
print(f"Condensate stack: {cond_stack.shape}  Nuclei stack: {nuc_stack.shape}")

print("\nSegmenting condensates...")
cond_masks, cond_df = segment_stack_stardist(cond_stack, model, "condensates")

print("\nSegmenting nuclei...")
nuc_masks, nuc_df = segment_stack_stardist(nuc_stack, model, "nuclei")

# Partition coefficient (background-subtracted, Fabrini et al. method)
B = float(cond_stack.min())

cond_3d  = cond_masks > 0
nuc_3d   = nuc_masks  > 0

nuclear_cond_mask = cond_3d & nuc_3d
cond_vals         = cond_stack[nuclear_cond_mask].astype(np.float64) - B
cond_vals         = np.clip(cond_vals, 0, None)
cond_density      = cond_vals.sum() / nuclear_cond_mask.sum()

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

print(f"\nStarDist Partition Coefficient (background-subtracted): {pc:.3f}")
print(f"  Background (min FOV intensity) : {B:.2f}")
print(f"  Condensate density             : {cond_density:.2f}")
print(f"  Dilute density                 : {dilute_density:.2f}")
print(f"  Total condensates              : {len(cond_df)}")

# Save outputs
tiff.imwrite(OUTPUT_DIR / "stardist_condensate_masks.tif", cond_masks)
tiff.imwrite(OUTPUT_DIR / "stardist_nuclei_masks.tif",     nuc_masks)
cond_df.to_csv(OUTPUT_DIR / "stardist_condensate_measurements.csv", index=False)
nuc_df.to_csv(OUTPUT_DIR  / "stardist_nuclei_measurements.csv",     index=False)

summary = pd.DataFrame({
    "metric": ["partition_coefficient", "background", "condensate_density", "dilute_density", "n_condensates"],
    "value":  [pc, B, cond_density, dilute_density, len(cond_df)],
})
summary.to_csv(OUTPUT_DIR / "stardist_summary.csv", index=False)

# Visualisation
mid_z = cond_stack.shape[0] // 2
fig, axs = plt.subplots(2, 3, figsize=(15, 8))

axs[0, 0].imshow(cond_stack[mid_z], cmap="gray")
axs[0, 0].set_title(f"Raw condensates (z={mid_z})")

axs[0, 1].imshow(cond_masks[mid_z], cmap="tab20")
axs[0, 1].set_title("StarDist condensate labels")

axs[0, 2].imshow(nuc_masks[mid_z], cmap="tab20")
axs[0, 2].set_title("StarDist nuclei labels")

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
plt.savefig(OUTPUT_DIR / "stardist_results.png", dpi=150)
plt.close()
print(f"\nSaved to: {OUTPUT_DIR}")

# Note: StarDist3D with a custom-trained model would replace the slice-by-slice
# approach above. Use your .labeling annotations with train_stardist3d() to get
# a model that processes the full ZYX volume natively.
