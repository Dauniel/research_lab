from pathlib import Path

import numpy as np
import pandas as pd
import tifffile as tiff
import matplotlib.pyplot as plt

from nellie.im_info.verifier import FileInfo, ImInfo
from nellie.run import run as nellie_run

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "segmentation_test" / "outputs" / "nellie"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

COND_PATH = DATA_DIR / "raw_condensates" / "C2-ROI_raw_stack_sample2_5.tif"
NUC_PATH  = DATA_DIR / "raw_nuclei"     / "C1-ROI_raw_stack_sample2_5.tif"

VOXEL_Z_UM = 0.6
VOXEL_Y_UM = 0.1597
VOXEL_X_UM = 0.1597


def run_nellie_pipeline(im_path, output_dir):
    file_info = FileInfo(filepath=str(im_path), output_dir=str(output_dir))
    file_info.find_metadata()
    file_info.load_metadata()
    file_info.change_dim_res("Z", VOXEL_Z_UM)
    file_info.change_dim_res("Y", VOXEL_Y_UM)
    file_info.change_dim_res("X", VOXEL_X_UM)
    im_info = nellie_run(file_info)
    return im_info


print("Running Nellie on condensate channel...")
cond_im_info = run_nellie_pipeline(COND_PATH, OUTPUT_DIR / "condensates")

print("Running Nellie on nuclei channel...")
nuc_im_info = run_nellie_pipeline(NUC_PATH, OUTPUT_DIR / "nuclei")

# Load instance label masks produced by Nellie
cond_labels = tiff.imread(cond_im_info.pipeline_paths["im_instance_label"])
nuc_labels  = tiff.imread(nuc_im_info.pipeline_paths["im_instance_label"])

cond_stack = tiff.imread(COND_PATH)

# Partition coefficient
cond_pixels_all   = []
dilute_pixels_all = []

for z in range(cond_stack.shape[0]):
    cond_mask  = cond_labels[z] > 0
    nuc_mask   = nuc_labels[z]  > 0
    img        = cond_stack[z]

    cond_pixels   = img[cond_mask & nuc_mask]
    dilute_pixels = img[nuc_mask & ~cond_mask]

    if cond_pixels.size   > 0: cond_pixels_all.append(cond_pixels)
    if dilute_pixels.size > 0: dilute_pixels_all.append(dilute_pixels)

cond_density   = np.mean(np.concatenate(cond_pixels_all))
dilute_density = np.mean(np.concatenate(dilute_pixels_all))
pc             = cond_density / dilute_density

print(f"\nNellie Partition Coefficient: {pc:.3f}")
print(f"  Condensate density : {cond_density:.2f}")
print(f"  Dilute density     : {dilute_density:.2f}")

# Organelle-level features
features_df = pd.read_csv(cond_im_info.pipeline_paths["features_organelles"])
print(f"\nDetected {len(features_df)} condensate objects")

summary = pd.DataFrame({
    "metric": ["partition_coefficient", "condensate_density", "dilute_density", "n_objects"],
    "value":  [pc, cond_density, dilute_density, len(features_df)],
})
summary.to_csv(OUTPUT_DIR / "nellie_summary.csv", index=False)

# Visualisation
mid_z = cond_stack.shape[0] // 2
fig, axs = plt.subplots(1, 3, figsize=(15, 4))

axs[0].imshow(cond_stack[mid_z], cmap="gray")
axs[0].set_title(f"Raw condensates (z={mid_z})")

axs[1].imshow(cond_labels[mid_z], cmap="tab20")
axs[1].set_title("Nellie instance labels")

axs[2].hist(features_df["intensity_mean"], bins=30, color="steelblue")
axs[2].set_title("Condensate intensity distribution")
axs[2].set_xlabel("Mean intensity")
axs[2].set_ylabel("Count")

plt.tight_layout()
plt.savefig(OUTPUT_DIR / "nellie_results.png", dpi=150)
plt.close()
print(f"\nSaved to: {OUTPUT_DIR}")
