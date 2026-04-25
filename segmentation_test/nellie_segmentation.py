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

# Partition coefficient (background-subtracted, Fabrini et al. method)
B = float(cond_stack.min())

cond_3d  = cond_labels > 0
nuc_3d   = nuc_labels  > 0

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

print(f"\nNellie Partition Coefficient (background-subtracted): {pc:.3f}")
print(f"  Background (min FOV intensity) : {B:.2f}")
print(f"  Condensate density             : {cond_density:.2f}")
print(f"  Dilute density                 : {dilute_density:.2f}")

# Organelle-level features
features_df = pd.read_csv(cond_im_info.pipeline_paths["features_organelles"])
print(f"\nDetected {len(features_df)} condensate objects")

summary = pd.DataFrame({
    "metric": ["partition_coefficient", "background", "condensate_density", "dilute_density", "n_objects"],
    "value":  [pc, B, cond_density, dilute_density, len(features_df)],
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
