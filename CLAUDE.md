# Project Context for Claude

## Who I Am
Daniel Chang, undergraduate researcher in C&S BIO  at 199 and 197 UCLA under PI **Elisa Franco**. I need to produce a final **poster, report, and presentation** for this research course (Spring 2026).

---

## Research Summary

### Biological Background
The Franco lab engineers **artificial RNA condensates** in mammalian cells using programmable RNA nanostar motifs (multi-arm RNA structures that drive phase separation). These synthetic condensates form in both the nucleus and cytoplasm and serve as a model system for studying RNA-driven phase separation.

The dataset used is the **JABr construct** — a 15-nt stem with a kissing-loop sequence (A) and Broccoli fluorescent aptamer — imaged via fluorescence microscopy.

### Core Problem Solved
The existing condensate analysis was done **manually** using GUI-based tools (e.g., ImageJ/FIJI). This was slow, hard to reproduce, and didn't scale to large datasets. This project automates it entirely in Python.

### What Was Built (Winter 2026 Report — Already Complete)
An automated Python pipeline that:
1. Loads multi-channel fluorescence microscopy Z-stacks (55 slices, 2 channels)
2. Segments **nuclei** (Ch1) and **condensates** (Ch2) using **Cellpose** models, slice-by-slice
3. Extracts per-object measurements: `area`, `centroid`, `mean_intensity` via `scikit-image.regionprops_table`
4. Classifies condensates as nuclear or cytoplasmic based on spatial overlap with nuclei masks
5. Computes the **nuclear partition coefficient** (PC):
   - `condensate density` = mean intensity of pixels inside (nucleus ∩ condensate)
   - `dilute-phase density` = mean intensity of pixels inside nucleus but outside condensates
   - `PC = condensate density / dilute-phase density`
6. Saves segmentation masks (TIF stacks) and measurement tables (CSV)

### Key Results
- Full-stack PC = **1.71**, ROI PC = **2.04**, reference PC = **6.32**
- Gap is due to condensate segmentation quality — small boundary differences have a large effect on intensity-based metrics
- Nuclei segmented well; condensates are harder (small, heterogeneous, sensitive to background)

---

## PI's Requested Extension (The New Work)

> "Develop a well-documented, user-friendly pipeline for image analysis, with estimation of volume & partition coefficient."

### What This Means Concretely
1. **3D Volume Estimation** — current pipeline only computes 2D per-slice area. Need to aggregate masks across Z-slices to compute true 3D volumes per object (voxel size × pixel area × Z-depth)
2. **Improved Partition Coefficient** — per-object PC or improved segmentation to close the gap with the reference value
3. **User-Friendly Packaging** — `pipeline.py` is currently a flat script with hardcoded paths. Needs:
   - CLI arguments or config file for input paths, voxel size, Cellpose diameter params
   - Clear docstrings on all functions
   - README with usage instructions

---

## Key Files
| File | Description |
|------|-------------|
| `pipeline.py` | Main pipeline script (flat, hardcoded paths — needs refactoring) |
| `pipeline_development.ipynb` | Development notebook |
| `python_implementation.ipynb` | Implementation notebook |
| `data/raw_mask_condensates/C2-raw_stack_sample2_5.tif` | Condensate channel Z-stack |
| `data/raw_mask_nuclei/C1-raw_stack_sample2_5.tif` | Nuclei channel Z-stack |
| `outputs/cellpose_python/` | Output masks (TIF) and measurements (CSV) |
| `Daniel Chang ~ C&S BIO 199 ~ Winter 2026 ~ Report.pdf` | Completed Winter 2026 report |

## Tech Stack
- **Cellpose** — segmentation models
- **tifffile** — loading/saving TIF stacks
- **scikit-image** (`regionprops_table`) — feature extraction
- **numpy**, **pandas** — data processing
- **matplotlib** — visualization
- GPU: NVIDIA RTX 4080 (desktop), Apple M1 Pro (laptop)

---

## Poster/Presentation Narrative
1. **Problem**: Manual GUI-based analysis was slow, not reproducible, doesn't scale
2. **What I built**: Automated Cellpose pipeline → feature extraction → partition coefficient
3. **Results**: Nuclei segment well; condensates harder; PC gap reveals segmentation sensitivity
4. **Extension**: 3D volume estimation + user-friendly CLI packaging
5. **Impact**: Lab can now run this on new RNA nanostar constructs quickly and consistently
