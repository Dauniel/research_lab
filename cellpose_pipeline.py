from pathlib import Path

import numpy as np
import pandas as pd
import tifffile as tiff
from cellpose import models
from skimage.measure import regionprops_table

import torch
from cellpose import core
import matplotlib.pyplot as plt

# setting up paths

BASE_DIR = Path.cwd()
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "outputs" / "cellpose_python"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

COND_PATH = DATA_DIR / "raw_mask_condensates" / "C2-raw_stack_sample2_5.tif"
NUC_PATH  = DATA_DIR / "raw_mask_nuclei" / "C1-raw_stack_sample2_5.tif"

# checking input files

print("Condensate file exists: ", COND_PATH.exists())
print("Nuclei file exists: ", NUC_PATH.exists())

# loading image stacks

cond_stack = tiff.imread(COND_PATH)
nuc_stack = tiff.imread(NUC_PATH)

# checking stack information

print("Condensates shape:", cond_stack.shape)
print("Nuclei shape:", nuc_stack.shape)
print("Condensates dtype:", cond_stack.dtype)
print("Nuclei dtype:", nuc_stack.dtype)

# loading cellpose models

cond_model = models.CellposeModel(gpu=True)
nuc_model  = models.CellposeModel(gpu=True)

# checking gpu status

print("GPU working:", core.use_gpu())
print("CUDA available:", torch.cuda.is_available())
print("GPU count:", torch.cuda.device_count())
print("Current device:", torch.cuda.current_device())
print("GPU name:", torch.cuda.get_device_name(torch.cuda.current_device()))

# segmentation function

def run_cellpose_stack(stack, model, object_name="objects", diameter=None):
    mask_stack = []
    measurements = []

    for z in range(stack.shape[0]):
        img = stack[z]

        # running cellpose on one slice

        masks, flows, styles = model.eval(
            img,
            diameter=diameter,
        )

        mask_stack.append(masks.astype(np.int32))

        # extracting object measurements

        props = regionprops_table(
            masks,
            intensity_image=img,
            properties=["label", "area", "centroid", "mean_intensity"]
        )

        df = pd.DataFrame(props)

        # adding slice index

        if not df.empty:
            df["z"] = z
        else:
            df = pd.DataFrame(columns=["label", "area", "centroid-0", "centroid-1", "mean_intensity", "z"])

        measurements.append(df)

        print(f"{object_name} slice {z}: {masks.max()} objects")

    # combining outputs across slices

    mask_stack = np.stack(mask_stack)
    measurements_df = pd.concat(measurements, ignore_index=True)

    return mask_stack, measurements_df

# running segmentation for condensates

cond_masks, cond_df = run_cellpose_stack(
    cond_stack,
    cond_model,
    object_name="condensates",
    diameter=None
)

# running segmentation for nuclei

nuc_masks, nuc_df = run_cellpose_stack(
    nuc_stack,
    nuc_model,
    object_name="nuclei",
    diameter=None
)

# checking segmentation outputs

print("Condensate mask stack shape:", cond_masks.shape)
print("Nuclei mask stack shape:", nuc_masks.shape)

print(cond_df.head())
print(nuc_df.head())

# partition coefficient calculation

cond_pixels_all = []
dilute_pixels_all = []

for z in range(cond_stack.shape[0]):
    cond_mask = cond_masks[z] > 0
    nuc_mask  = nuc_masks[z] > 0
    img = cond_stack[z]

    # getting condensate and dilute phase pixels inside nuclei

    cond_pixels = img[cond_mask & nuc_mask]
    dilute_pixels = img[nuc_mask & (~cond_mask)]

    if cond_pixels.size > 0:
        cond_pixels_all.append(cond_pixels)

    if dilute_pixels.size > 0:
        dilute_pixels_all.append(dilute_pixels)

# computing mean densities and partition coefficient

cond_density = np.mean(np.concatenate(cond_pixels_all))
dilute_density = np.mean(np.concatenate(dilute_pixels_all))
partition_coefficient = cond_density / dilute_density

# saving masks and measurement tables

tiff.imwrite(OUTPUT_DIR / "ROI_condensate_masks.tif", cond_masks.astype(np.int32))
tiff.imwrite(OUTPUT_DIR / "ROI_nuclei_masks.tif", nuc_masks.astype(np.int32))

cond_df.to_csv(OUTPUT_DIR / "ROI_condensate_measurements.csv", index=False)
nuc_df.to_csv(OUTPUT_DIR / "ROI_nuclei_measurements.csv", index=False)

print("Saved to:", OUTPUT_DIR)

# plotting summary figures

fig, axs = plt.subplots(2, 3, figsize=(15, 8))

axs[0,0].hist(cond_df["area"], bins=50)
axs[0,0].set_title("Condensate Area")
axs[0,0].set_xlabel("Area")
axs[0,0].set_ylabel("Count")

axs[0,1].hist(nuc_df["area"], bins=50)
axs[0,1].set_title("Nuclei Area")
axs[0,1].set_xlabel("Area")

axs[0,2].axis("off")

axs[1,0].hist(cond_df["mean_intensity"], bins=50)
axs[1,0].set_title("Condensate Intensity")
axs[1,0].set_xlabel("Mean Intensity")
axs[1,0].set_ylabel("Count")

axs[1,1].hist(nuc_df["mean_intensity"], bins=50)
axs[1,1].set_title("Nuclei Intensity")
axs[1,1].set_xlabel("Mean Intensity")

# counting objects per slice

cond_counts = cond_df.groupby("z")["label"].count()
nuc_counts = nuc_df.groupby("z")["label"].count()

axs[1,2].plot(cond_counts.index, cond_counts.values, label="Condensates")
axs[1,2].plot(nuc_counts.index, nuc_counts.values, label="Nuclei")
axs[1,2].set_title("Object Count per Slice")
axs[1,2].set_xlabel("Z-slice")
axs[1,2].set_ylabel("Count")
axs[1,2].legend()

plt.tight_layout()
plt.show()