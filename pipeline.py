from pathlib import Path

import numpy as np
import pandas as pd
import tifffile as tiff
from cellpose import models
from skimage.measure import regionprops_table

import torch

BASE_DIR = Path.cwd()
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "outputs" / "cellpose_python"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

COND_PATH = DATA_DIR / "raw_mask_condensates" / "C2-raw_stack_sample2_5.tif"
NUC_PATH  = DATA_DIR / "raw_mask_nuclei" / "C1-raw_stack_sample2_5.tif"

print("Condensate file exists: ", COND_PATH.exists())
print("Nuclei file exists: ", NUC_PATH.exists())

cond_stack = tiff.imread(COND_PATH)
nuc_stack = tiff.imread(NUC_PATH)

print("Condensates shape:", cond_stack.shape)
print("Nuclei shape:", nuc_stack.shape)
print("Condensates dtype:", cond_stack.dtype)
print("Nuclei dtype:", nuc_stack.dtype)

cond_model = models.CellposeModel(gpu=True)
nuc_model  = models.CellposeModel(gpu=True)

from cellpose import core
print("GPU working:", core.use_gpu())

def run_cellpose_stack(stack, model, object_name="objects", diameter=None):
    mask_stack = []
    measurements = []

    for z in range(stack.shape[0]):
        img = stack[z]

        masks, flows, styles= model.eval(
            img,
            diameter=diameter,
            channels=[0, 0]
        )

        mask_stack.append(masks.astype(np.int32))

        props = regionprops_table(
            masks,
            intensity_image=img,
            properties=["label", "area", "centroid", "mean_intensity"]
        )

        df = pd.DataFrame(props)
        df["z"] = z
        measurements.append(df)

        print(f"{object_name} slice {z}: {masks.max()} objects")

    mask_stack = np.stack(mask_stack)
    measurements_df = pd.concat(measurements, ignore_index=True)

    return mask_stack, measurements_df

cond_masks, cond_df = run_cellpose_stack(
    cond_stack,
    cond_model,
    object_name="condensates",
    diameter=None
)

nuc_masks, nuc_df = run_cellpose_stack(
    nuc_stack,
    nuc_model,
    object_name="nuclei",
    diameter=None
)

print("Condensate mask stack shape:", cond_masks.shape)
print("Nuclei mask stack shape:", nuc_masks.shape)

display(cond_df.head())
display(nuc_df.head())

print("Condensate mask stack shape:", cond_masks.shape)
print("Nuclei mask stack shape:", nuc_masks.shape)

display(cond_df.head())
display(nuc_df.head())

tiff.imwrite(OUTPUT_DIR / "condensate_masks.tif", cond_masks.astype(np.int32))
tiff.imwrite(OUTPUT_DIR / "nuclei_masks.tif", nuc_masks.astype(np.int32))

cond_df.to_csv(OUTPUT_DIR / "condensate_measurements.csv", index=False)
nuc_df.to_csv(OUTPUT_DIR / "nuclei_measurements.csv", index=False)

print("Saved to:", OUTPUT_DIR)