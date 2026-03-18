from pathlib import Path

import numpy as np
import pandas as pd
import tifffile as tiff

from skimage.filters import gaussian, threshold_otsu
from skimage.morphology import (
    remove_small_objects,
    remove_small_holes,
    disk,
    opening,
)
from skimage.measure import label, regionprops_table
from skimage.exposure import rescale_intensity
from skimage.restoration import rolling_ball


# =========================================================
# BASE DIRECTORY (JUPYTER SAFE)
# =========================================================
BASE_DIR = Path.cwd()

# =========================================================
# PATHS
# =========================================================
CONDENSATE_RAW_PATH = BASE_DIR / "data" / "raw_mask_condensates" / "C2-raw_stack_sample2_5.ome.tif"
CONDENSATE_MASK_PATH = BASE_DIR / "data" / "raw_mask_condensates" / "C2-raw_stack_sample2_5.ome_cp_masks.tif"

NUCLEI_RAW_PATH = BASE_DIR / "data" / "raw_mask_nuclei" / "C1-raw_stack_sample2_5.tif"
NUCLEI_MASK_PATH = BASE_DIR / "data" / "raw_mask_nuclei" / "C1-raw_stack_sample2_5.ome_cp_masks.tif"

OUTPUT_DIR = BASE_DIR / "outputs" / "python_native_segmentation"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Versioned directories
COND_BASE = OUTPUT_DIR / "condensates"
V1_DIR = COND_BASE / "v1"
V2_DIR = COND_BASE / "v2"

V1_DIR.mkdir(parents=True, exist_ok=True)
V2_DIR.mkdir(parents=True, exist_ok=True)


# =========================================================
# PARAMETERS (TUNE THESE)
# =========================================================
# --- Condensates ---
COND_GAUSSIAN_SIGMA = 1.0
COND_ROLLING_BALL_RADIUS = 30
COND_MIN_OBJECT_SIZE = 8
COND_MIN_HOLE_SIZE = 8

# --- Nuclei ---
NUC_GAUSSIAN_SIGMA = 2.0
NUC_ROLLING_BALL_RADIUS = 50
NUC_MIN_OBJECT_SIZE = 200
NUC_MIN_HOLE_SIZE = 200


# =========================================================
# LOAD DATA
# =========================================================
print("Loading data...")

condensate_raw = tiff.imread(CONDENSATE_RAW_PATH)
condensate_mask = tiff.imread(CONDENSATE_MASK_PATH)

nuclei_raw = tiff.imread(NUCLEI_RAW_PATH)
nuclei_mask = tiff.imread(NUCLEI_MASK_PATH)

print("Condensate shape:", condensate_raw.shape)
print("Nuclei shape:", nuclei_raw.shape)


# =========================================================
# SEGMENTATION FUNCTIONS
# =========================================================
def segment_condensates(img):
    img = img.astype(np.float32)

    background = rolling_ball(img, radius=COND_ROLLING_BALL_RADIUS)
    corrected = img - background
    corrected[corrected < 0] = 0

    smoothed = gaussian(corrected, sigma=COND_GAUSSIAN_SIGMA)
    smoothed = rescale_intensity(smoothed, in_range="image", out_range=(0, 1))

    thresh = threshold_otsu(smoothed)
    binary = smoothed > thresh

    binary = remove_small_objects(binary, min_size=COND_MIN_OBJECT_SIZE)
    binary = remove_small_holes(binary, area_threshold=COND_MIN_HOLE_SIZE)
    binary = opening(binary, footprint=disk(1))
    binary = remove_small_objects(binary, min_size=COND_MIN_OBJECT_SIZE)

    labels = label(binary)

    return labels, binary


def segment_nuclei(img):
    img = img.astype(np.float32)

    background = rolling_ball(img, radius=NUC_ROLLING_BALL_RADIUS)
    corrected = img - background
    corrected[corrected < 0] = 0

    smoothed = gaussian(corrected, sigma=NUC_GAUSSIAN_SIGMA)
    smoothed = rescale_intensity(smoothed, in_range="image", out_range=(0, 1))

    thresh = threshold_otsu(smoothed)
    binary = smoothed > thresh

    binary = remove_small_objects(binary, min_size=NUC_MIN_OBJECT_SIZE)
    binary = remove_small_holes(binary, area_threshold=NUC_MIN_HOLE_SIZE)
    binary = opening(binary, footprint=disk(2))
    binary = remove_small_objects(binary, min_size=NUC_MIN_OBJECT_SIZE)

    labels = label(binary)

    return labels, binary


# =========================================================
# RUN CONDENSATE SEGMENTATION
# =========================================================
print("\nRunning condensate segmentation...")

cond_binary_stack = []
cond_label_stack = []
cond_measurements = []

for z in range(condensate_raw.shape[0]):
    img = condensate_raw[z]

    labels, binary = segment_condensates(img)

    cond_binary_stack.append(binary.astype(np.uint8))
    cond_label_stack.append(labels.astype(np.int32))

    props = regionprops_table(
        labels,
        intensity_image=img,
        properties=["label", "area", "centroid", "mean_intensity"],
    )

    df = pd.DataFrame(props)
    df["z"] = z
    cond_measurements.append(df)

    print(f"Condensate slice {z}: {labels.max()} objects")

cond_binary_stack = np.stack(cond_binary_stack)
cond_label_stack = np.stack(cond_label_stack)
condensate_df = pd.concat(cond_measurements, ignore_index=True)


# =========================================================
# RUN NUCLEI SEGMENTATION
# =========================================================
print("\nRunning nuclei segmentation...")

nuc_binary_stack = []
nuc_label_stack = []

for z in range(nuclei_raw.shape[0]):
    img = nuclei_raw[z]

    labels, binary = segment_nuclei(img)

    nuc_binary_stack.append(binary.astype(np.uint8))
    nuc_label_stack.append(labels.astype(np.int32))

    print(f"Nuclei slice {z}: {labels.max()} objects")

nuc_binary_stack = np.stack(nuc_binary_stack)
nuc_label_stack = np.stack(nuc_label_stack)


# =========================================================
# SAVE FUNCTION
# =========================================================
def save_version(version_dir):
    print(f"\nSaving to {version_dir}...")

    tiff.imwrite(version_dir / "binary_masks.tif", cond_binary_stack)
    tiff.imwrite(version_dir / "label_masks.tif", cond_label_stack)
    condensate_df.to_csv(version_dir / "measurements.csv", index=False)


# =========================================================
# CHOOSE VERSION TO SAVE
# =========================================================
VERSION = "v1"  # change to "v2" after tuning

if VERSION == "v1":
    save_version(V1_DIR)
elif VERSION == "v2":
    save_version(V2_DIR)


# =========================================================
# SAVE NUCLEI (no versioning needed)
# =========================================================
tiff.imwrite(OUTPUT_DIR / "nuclei_binary_masks.tif", nuc_binary_stack)
tiff.imwrite(OUTPUT_DIR / "nuclei_label_masks.tif", nuc_label_stack)

print("\nDone.")