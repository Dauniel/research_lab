# Automated Python-Based Image Analysis Pipeline for Segmentation and Quantification of Biomolecular Condensates in Fluorescence Microscopy Z-Stacks

**Daniel Chang**
C&S BIO 199 / 197 — Spring 2026
PI: Elisa Franco

---

## 1. Abstract

This project develops a fully automated, reproducible Python-based image analysis pipeline for fluorescence microscopy data to accurately quantify biomolecular condensates in nuclear compartments. The pipeline incorporates Cellpose 3 denoising as a preprocessing step, full three-dimensional segmentation using `do_3D=True`, background subtraction following the Fabrini et al. method, and a mean voxel density estimator for the condensate phase. Applied to the JABr Sample2_5_1 region of interest, the pipeline produced a nuclear partition coefficient of 6.297 against a manual reference of 6.324, representing a −0.4% error. These results demonstrate that automated partition coefficient estimation can match manually-derived reference values through principled preprocessing and density estimation choices, without requiring custom model training.

---

## 2. Introduction

Biomolecular condensates are membrane-less cellular compartments that play important roles in processes such as gene expression and RNA regulation. Recent work from the Franco lab has shown that artificial RNA condensates can be engineered in living cells using programmable RNA nanostar motifs, which form distinct compartments in both the nucleus and cytoplasm through sequence-specific interactions [1].

Fluorescence microscopy enables visualization of these condensates; however, extracting quantitative and reproducible measurements from multi-channel Z-stack imaging data remains challenging. Manual and GUI-based approaches (e.g., Imaris) are difficult to scale and lack reproducibility, particularly when analyzing large datasets or comparing results across experimental conditions.

To address these limitations, this project develops an automated Python-based pipeline for condensate segmentation and partition coefficient quantification. The pipeline uses Cellpose 3 for denoising and 3D volumetric segmentation, followed by background-subtracted intensity estimation using the Fabrini et al. method. The goal is to produce partition coefficients that match the manually-derived reference values from the Franco lab dataset, enabling the pipeline to serve as a reproducible substitute for manual analysis.

---

## 3. Data Description

### 3.1 Biological Context and Dataset

The data used in this project originates from experiments involving engineered RNA nanostar constructs designed to form synthetic biomolecular condensates in living cells. RNA nanostars are programmable RNA structures composed of multiple stem-loop arms connected by flexible spacers, enabling interactions that drive phase separation. These condensates serve as a model system for studying RNA-driven phase separation [1, 2].

The naming convention for the RNA nanostar constructs reflects their structural design. In this dataset, JABr denotes a construct containing a 15-nt stem, a kissing-loop sequence (A), and the Broccoli fluorescent aptamer. These features influence interaction strength, condensate formation, and subcellular localization.

### 3.2 Dataset Organization and Reference Measurements

The dataset is part of a larger collection of fluorescence microscopy images and associated analysis outputs maintained by the Franco lab. Manual partition coefficient measurements for 30 JABr cells were previously computed in Imaris and are stored as reference CSVs containing per-cell condensate density, dilute density, and partition coefficient split by cellular compartment (nuclear and cytoplasmic). These reference values serve as the validation target for the automated pipeline.

### 3.3 Selected Sample

This project focuses on:

- **20240516_JABr_40uMDFHBI_20-40_Sample2_5_MMStack_Pos0.ome.tif**

This file is a multi-channel Z-stack fluorescence microscopy image of 55 slices containing two channels:

- Channel 1 (C1): nuclei signal
- Channel 2 (C2): condensate signal (Broccoli-labeled RNA)

To enable independent processing, the channels were separated and stored as:

- `C1-ROI_raw_stack_sample2_5.tif` (nuclei channel)
- `C2-ROI_raw_stack_sample2_5.tif` (condensate channel)

### 3.4 Region of Interest

A cropped region of interest (ROI) was selected to enable focused validation against the manually-derived reference partition coefficient. The ROI corresponds to Sample2_5_1, for which the nuclear reference partition coefficient is 6.324, with condensate density 658.30 and dilute density 104.09.

---

## 4. Methods

### 4.1 Overview

The updated pipeline follows a six-step workflow:

**Load → Denoise → Segment (3D) → Measure → Compute Volumes → Partition Coefficient**

All steps are implemented in Python and executed through a single script (`spring_implementation/pipeline.py`) with command-line arguments controlling key parameters.

### 4.2 Image Loading

The condensate (C2) and nuclei (C1) channels were loaded as separate 3D TIFF stacks using `tifffile`. Both channels have shape (55, 185, 259) with `uint16` dtype, corresponding to 55 Z-slices at 185 × 259 pixels each.

### 4.3 Denoising with Cellpose 3

Prior to segmentation, both channels were denoised using the Cellpose 3 `DenoiseModel`. This step reduces high-frequency noise in the fluorescence images, improving downstream segmentation quality, particularly for faint condensate structures. Denoising was applied to the full 3D stack before segmentation.

### 4.4 Three-Dimensional Segmentation

Segmentation was performed using Cellpose 3 with `do_3D=True`, which processes the full volumetric stack rather than operating on individual Z-slices as in the winter implementation. This produces spatially coherent 3D instance labels, eliminating the fragmentation and label inconsistencies introduced by slice-by-slice segmentation.

**Condensate segmentation** used the `cyto3` pretrained model with `cellprob_threshold=0.0` and GPU acceleration enabled.

**Nuclei segmentation** used the `cyto3` model followed by connected-component relabeling to enforce a single label per nucleus. Raw Cellpose output produced 76 candidate labels; after connected-component cleanup, 5 distinct nuclei were retained in the ROI.

### 4.5 Partition Coefficient Computation

The nuclear partition coefficient was computed following the Fabrini et al. method [1], modified for 3D volumetric masks:

**Background subtraction:**
$$B = \min(\text{all voxel intensities in the condensate stack})$$

This removes the camera offset from all intensity measurements.

**Condensate density:**
The condensate phase was defined as voxels inside both the condensate mask and the nucleus mask. Mean intensity was computed over all such voxels after background subtraction. A top-100% estimator was used, meaning all voxels within the condensate-nucleus intersection contributed equally to the mean (equivalent to `--cond-topx 100`).

$$\rho_\text{cond} = \text{mean}\left(\text{clip}(I - B,\ 0)\right) \text{ over } \{\text{cond mask} \cap \text{nuc mask}\}$$

**Dilute density:**
The dilute phase was defined as voxels inside the nucleus mask but outside the condensate mask. To approximate the manual selection of a quiet representative region, the 50 lowest-intensity valid 10×10×10 patches fully within the dilute region were identified, and their mean intensity was used as the dilute density estimate.

$$\rho_\text{dilute} = \text{mean of 50 lowest-intensity 10×10×10 patches within } \{\text{nuc mask} \cap \lnot\text{cond mask}\}$$

**Partition coefficient:**
$$\text{PC} = \frac{\rho_\text{cond}}{\rho_\text{dilute}}$$

### 4.6 Output Organization

The pipeline saves the following outputs to a specified directory:

- `cond_restored.tif` / `nuc_restored.tif` — denoised stacks
- `condensate_masks.tif` / `nuclei_masks.tif` — 3D instance label stacks
- `condensate_measurements.csv` / `nuclei_measurements.csv` — per-slice regionprops
- `condensate_volumes.csv` / `nuclei_volumes.csv` — per-object 3D volumes
- `summary.csv` — partition coefficient and metadata
- `results.png` — six-panel pipeline visualization

---

## 5. Results

### 5.1 Segmentation

The pipeline segmented 186 condensate objects and 5 nuclei in the Sample2_5_1 ROI. Nuclei were detected as spatially coherent 3D regions after connected-component relabeling reduced 76 raw Cellpose labels to 5 distinct nuclei. Condensates were identified as punctate 3D structures distributed throughout the nuclear volume.

### 5.2 Partition Coefficient

The pipeline produced the following measurements for Sample2_5_1:

| Metric | Pipeline Output | Nuclear Reference | Error |
|--------|-----------------|-------------------|-------|
| Partition Coefficient | **6.297** | 6.324 | −0.4% |
| Condensate density | 440.93 | 658.30 | −33% |
| Dilute density | 70.03 | 104.09 | −33% |

The partition coefficient of 6.297 is within 0.4% of the manual reference value of 6.324. Both the condensate density and dilute density are approximately 33% lower than the reference values, but because the underestimation is proportionally equal in both the numerator and denominator, the ratio — and thus the partition coefficient — is accurately recovered.

---

## 6. Discussion

The pipeline achieved a partition coefficient of 6.297, within 0.4% of the manual reference of 6.324. Two design choices were central to this accuracy.

Background subtraction (B = minimum voxel intensity across the stack) removes the camera offset from all intensity measurements. Without this correction, both condensate and dilute densities are overestimated, but not by the same factor — the dilute phase, which has lower absolute signal, is affected proportionally more, causing the PC to be underestimated.

Full 3D segmentation using `do_3D=True` produces spatially coherent instance labels across the entire Z-stack. This ensures each condensate object is represented as a single contiguous 3D region, so all contributing voxels are included in the intensity estimate.

The persistent ~33% offset in individual densities relative to the Imaris reference likely reflects differences in how the pipeline and Imaris define object boundaries. Despite this offset, the proportionality between condensate and dilute densities is preserved, yielding an accurate partition coefficient. Future work could investigate whether boundary definition differences can be corrected to also match individual density values.

---

## 7. Conclusion

This project developed and validated an updated Python-based pipeline for automated quantification of biomolecular condensate partition coefficients from fluorescence microscopy Z-stacks. The key contributions of the spring quarter work are:

1. Integration of Cellpose 3 DenoiseModel for preprocessing
2. Full 3D volumetric segmentation (`do_3D=True`) replacing slice-by-slice analysis
3. Background subtraction following the Fabrini et al. method
4. Top-100% voxel density estimation for the condensate phase
5. Connected-component relabeling for nucleus cleanup

Applied to JABr Sample2_5_1, the pipeline achieved a partition coefficient of 6.297 against a manual reference of 6.324 (−0.4% error). These results establish the pipeline as a reproducible and accurate alternative to manual Imaris-based analysis for this sample.

---

## 8. Reproducibility

The pipeline is implemented entirely in Python using open-source libraries: Cellpose 3 for denoising and segmentation, NumPy and pandas for data processing, scikit-image for feature extraction, and tifffile for image I/O. All steps are executed through a single script with documented command-line arguments.

The pipeline was developed and tested on:

- **MacBook Pro** (Apple M1 Pro, 10-core CPU, 16 GB RAM)
- **Desktop workstation** (AMD Ryzen 7 7700 CPU, NVIDIA RTX 4080 GPU, 32 GB RAM)

GPU acceleration (CUDA, RTX 4080) was used for all segmentation and denoising steps reported here.

The full pipeline code is available at: https://github.com/Dauniel/research_lab

---

## 9. References

[1] Li, S., Kim, Y., Wang, K., Payson, E. J., Tang, A. A., Villalba Nieto, M., Osmanovic, D., Yang, M., Dilao, D., Bermudez, A., Xiao, W., Li, M. M. H., Lin, N. Y. C., Plath, K., Black, D. L., & Franco, E. (2026). Programmable artificial RNA condensates in mammalian cells. *bioRxiv*. https://doi.org/10.64898/2026.01.28.702393

[2] Banani, S. F., Lee, H. O., Hyman, A. A., & Rosen, M. K. (2017). Biomolecular condensates: organizers of cellular biochemistry. *Nature Reviews Molecular Cell Biology*, 18(5), 285–298. https://doi.org/10.1038/nrm.2017.7

[3] Stringer, C., Wang, T., Michaelos, M., & Pachitariu, M. (2021). Cellpose: a generalist algorithm for cellular segmentation. *Nature Methods*, 18(1), 100–106. https://doi.org/10.1038/s41592-020-01018-x

[4] Pachitariu, M., & Stringer, C. (2022). Cellpose 2.0: how to train your own model. *Nature Methods*, 19(12), 1634–1641. https://doi.org/10.1038/s41592-022-01663-4
