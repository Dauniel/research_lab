# Project Context for Claude

## Who I Am
Daniel Chang, undergraduate researcher in C&S BIO 199 and 197 at UCLA under PI **Elisa Franco**. Deliverables for Spring 2026: **poster, report, and presentation**.

---

## Research Summary

### Biological Background
The Franco lab engineers **artificial RNA condensates** in mammalian cells using programmable RNA nanostar motifs (multi-arm RNA structures that drive phase separation). These synthetic condensates form in both the nucleus and cytoplasm and serve as a model system for studying RNA-driven phase separation.

The dataset used is the **JABr construct** — a 15-nt stem with a kissing-loop sequence (A) and Broccoli fluorescent aptamer — imaged via fluorescence microscopy.

### Core Problem Solved
The existing condensate analysis was done **manually** using GUI-based tools (e.g., ImageJ/FIJI). This was slow, hard to reproduce, and didn't scale to large datasets. This project automates it entirely in Python.

### What Was Built (Winter 2026 — Complete)
An automated Python pipeline that:
1. Loads multi-channel fluorescence microscopy Z-stacks (55 slices, 2 channels)
2. Segments **nuclei** (Ch1) and **condensates** (Ch2) using **Cellpose** models, slice-by-slice
3. Extracts per-object measurements: `area`, `centroid`, `mean_intensity` via `scikit-image.regionprops_table`
4. Classifies condensates as nuclear or cytoplasmic based on spatial overlap with nuclei masks
5. Computes the **nuclear partition coefficient** (PC):
   - `condensate density` = mean intensity of pixel values that fall within both the nuclei mask and the condensate mask
   - `dilute-phase density` = mean intensity of pixel values that fall within the nuclei mask but not the condensate mask
   - `PC = condensate density / dilute-phase density`
6. Saves segmentation masks (TIF stacks) and measurement tables (CSV)

### Winter 2026 Key Results
- Full-stack PC = **1.71**, ROI PC = **2.04**, reference PC = **6.32**
- Gap is due to condensate segmentation quality — small boundary differences have a large effect on intensity-based metrics
- Nuclei segmented well; condensates are harder (small, heterogeneous, sensitive to background)

---

## Spring 2026 Work

### PI's Requested Extension
> "Develop a well-documented, user-friendly pipeline for image analysis, with estimation of volume & partition coefficient."

### Segmentation Model Survey (2026-04-22 — Complete)
Tested four new models on the JABr ROI dataset (`C2-ROI_raw_stack_sample2_5.tif`, 55×185×259, 2-channel):

| Model | Approach | PC | Runtime |
|---|---|---|---|
| Old Cellpose (2D) | cyto2, slice-by-slice | 2.04 | — |
| **Cellpose 3** | cyto3 + denoising + 3D mode | **3.33** | 11 s |
| StarDist 2D | versatile_fluo, slice-by-slice | 1.91 | 6 s |
| U-FISH | ONNX spot detection | 3.81* | 2 s |
| Nellie | Frangi filter + graph analysis | 3.57 | 14 s |
| Reference | manual/ImageJ benchmark | **6.32** | — |

*U-FISH PC is likely inflated — it uses Otsu threshold for nuclei (not a trained model) and treats condensates as point sources, not filled objects.

**Recommended model: Cellpose 3** — cyto3 + DenoiseModel + do_3D=True are the three concrete improvements over the old pipeline. PC improved 2.04 → 3.33 via tighter boundaries and cross-slice 3D consistency. All models still fall short of reference PC = 6.32; gap is due to condensate segmentation sensitivity.

### Remaining Work (Spring 2026)
1. **3D Volume Estimation** — aggregate masks across Z-slices to compute true 3D volumes per object (voxel size × pixel area × Z-depth)
2. **Improved Partition Coefficient** — use Cellpose 3 as the base; consider fixing nuclear mask consistency across models for a fair comparison
3. **User-Friendly Packaging** — `cellpose_pipeline.py` has hardcoded paths; needs CLI args / config file, docstrings, README
4. **Spring 2026 poster / report / presentation**

---

## Key Files
| File | Description |
|------|-------------|
| `winter_implementation/cellpose_pipeline.py` | Old Winter 2026 pipeline script (reference only) |
| `winter_implementation/cellpose_pipeline_dev.ipynb` | Old development notebook |
| `winter_implementation/skimage_segmentation_dev.ipynb` | Old skimage exploration notebook |
| `winter_implementation/mask_split_explore.py` | Old mask exploration script |
| `winter_implementation/outputs/cellpose_python/` | Output masks and CSVs from the old pipeline |
| `segmentation_test/` | Model comparison scripts and outputs |
| `segmentation_test/run_comparison.py` | Runs all 5 models, generates comparison + flowmap figures |
| `segmentation_test/cellpose3_segmentation.py` | Cellpose 3 script (recommended model) |
| `segmentation_test/outputs/comparison/` | Side-by-side figure, flowmap, raw mid-Z image |
| `data/raw_condensates/C2-ROI_raw_stack_sample2_5.tif` | Condensate channel ROI Z-stack (~5 MB) |
| `data/raw_nuclei/C1-ROI_raw_stack_sample2_5.tif` | Nuclei channel ROI Z-stack (~5 MB) |
| `data/ROI/roi_sample2_5_1..tif` | Full ROI stack |
| `docs/progress_log.txt` | Detailed session-by-session log |
| `docs/reports/Daniel Chang ~ C&S BIO 199 ~ Winter 2026 ~ Report.pdf` | Completed Winter 2026 report |

> Full 340 MB Z-stacks are gitignored. ROI files (~5 MB each) are tracked.

## Tech Stack
- **Cellpose 3.1.1** — primary segmentation model (cyto3 + denoising + 3D)
- **StarDist**, **U-FISH**, **Nellie** — surveyed alternatives
- **tifffile** — loading/saving TIF stacks
- **scikit-image** (`regionprops_table`) — feature extraction
- **numpy**, **pandas** — data processing
- **matplotlib** — visualization
- GPU: NVIDIA RTX 4080 (desktop), Apple M1 Pro (laptop)

---

## Poster/Presentation Narrative
1. **Problem**: Manual GUI-based analysis was slow, not reproducible, doesn't scale
2. **What I built**: Automated Cellpose pipeline → feature extraction → partition coefficient
3. **Winter results**: Nuclei segment well; condensates harder; PC gap (2.04 vs 6.32) reveals segmentation sensitivity
4. **Spring extension**: Model survey (4 alternatives tested) → Cellpose 3 best principled improvement (PC 3.33); 3D volume estimation; user-friendly CLI packaging
5. **Impact**: Lab can now run this on new RNA nanostar constructs quickly and consistently
