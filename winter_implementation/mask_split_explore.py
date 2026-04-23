import tifffile
import numpy as np

# LOAD IMAGES
condensates = tifffile.imread(r"C:\storage\code\research\tutorial\sample_image.tif")
mask = tifffile.imread(r"C:\storage\code\research\tutorial\sample_image_cp_masks.tif")

print("condensates shape:", condensates.shape)  # should be (55, 2, 173, 257)
print("mask shape:", mask.shape)                # should be (55, 173, 257)

# Extract condensates channel = 1 (channel axis is C)
# condensates: (Z, C, Y, X) -> take C=1
cond_ch1 = condensates[:, 1, :, :]   # shape: (55, 173, 257)

# If mask is categorical labels, convert to 0/1
mask_binary = (mask > 0).astype(cond_ch1.dtype)  # match dtype

# NUCLEAR CONDENSATES (inside nuclei)
nuclear_image = cond_ch1 * mask_binary
tifffile.imwrite(r"C:\storage\code\research\tutorial\nuclear_condensates.tif", nuclear_image)

# CYTOPLASMIC CONDENSATES (outside nuclei)
inverse_mask = 1 - mask_binary
cytoplasmic_image = cond_ch1 * inverse_mask
tifffile.imwrite(r"C:\storage\code\research\tutorial\cytoplasmic_condensates.tif", cytoplasmic_image)

print("DONE: wrote nuclear_condensates.tif and cytoplasmic_condensates.tif")
