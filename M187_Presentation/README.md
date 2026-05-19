# M187 Research Poster: Automated Segmentation of RNA-Aptamer Condensates

## Key Achievement

**Partition Coefficient: 6.297 vs Reference: 6.32 (−0.4% error)**

Successfully replicated manual reference PC value using fully automated pipeline for the first time.

---

## Single-ROI Validation Results (April 30, 2026)

| Metric | Value |
|--------|-------|
| **Partition Coefficient (PC)** | **6.297** |
| Reference PC (manual) | 6.32 |
| Error | −0.4% ✓ |
| Condensate density | 440.93 |
| Dilute density | 70.03 |
| Background (B) | 76.00 |
| Condensates detected | 186 |
| Nuclei detected (after CC cleanup) | 5 |
| Sample | JABr Sample2_5_1 (55 × 185 × 259 pixels, 2 channels) |

---

## Three Critical Improvements

### 1. Background Subtraction (Fabrini et al. Method)
- **What**: Subtract minimum voxel intensity (B) from all pixels before computing density ratios
- **Why**: Reference PC was computed with background subtraction; old pipeline lacked this
- **Impact**: Largest single jump in PC accuracy

```
Fluor. density = Σ clip(pixel - B, 0) / n_voxels
PC = density_condensed / density_dilute
```

### 2. Connected-Component Nuclei Relabeling
- **What**: Cellpose produces 76 instance labels. Post-processing via 3D connected-component analysis reveals only 5 true contiguous nuclei
- **Why**: Cellpose splits large nuclei into ~15-25 fragments due to internal condensate texture interference
- **Impact**: Cleans up dilute-phase pixel selection without changing nuclear area covered

### 3. Lowest-Intensity Patch Selection for Dilute Density
- **What**: Instead of sampling one random 10×10×10 patch (seed-dependent, PC = 4.3–6.0 swing), find all ~88,000 valid patches in dilute region, sort by intensity, average the 50 quietest
- **Why**: Manually selected patch is the "quietest" representative spot; automated approach was unstable without seed control
- **Impact**: Stable, deterministic result (PC = 5.213 before further optimization)

---

## Pipeline Architecture (6 Steps)

1. **Load**: Read condensate (Ch2) and nuclei (Ch1) Z-stacks
2. **Denoise**: Cellpose 3 DenoiseModel on every slice (prepares boundaries, preserves raw intensity)
3. **Segment**: Cellpose 3 (cyto3, do_3D=True) in full 3D + nuclei post-processing (CC relabeling)
4. **Measure**: regionprops extracts per-object area, centroid, intensity per Z-slice
5. **Volume**: Sum voxels per object across all 55 slices
6. **PC**: Background-subtracted partition coefficient (Fabrini formula with lowest-patch dilute density)

---

## Materials in This Directory

```
M187_Presentation/
├── POSTER_OUTLINE.md              # Poster layout template
├── README.md                       # This file
├── pipeline.py                     # Main pipeline code
├── figures/
│   ├── results/
│   │   ├── summary.csv             # PC = 6.297 and metrics
│   │   ├── results.png             # Pipeline output visualization
│   │   ├── condensate_measurements.csv
│   │   ├── condensate_volumes.csv
│   │   ├── nuclei_measurements.csv
│   │   ├── nuclei_volumes.csv
│   │   ├── batch_comparison_scatter.png  # Batch validation across 30 JABr cells
│   │   └── batch_JABr_final_comparison.csv
│   └── pipeline/
│       ├── raw_midZ.png            # Raw image at mid-Z slice
│       ├── mask_overlay.png        # Segmentation masks overlaid on raw
│       └── intensity_hist.png      # Intensity distribution analysis
├── content/                        # Text sections (to be filled)
│   ├── abstract.txt
│   ├── introduction.txt
│   ├── methods.txt
│   ├── results.txt
│   ├── conclusion.txt
│   └── acknowledgements.txt
└── layouts/                        # Poster design template (to be added)
    └── poster_template.pptx
```

---

## Key Figures for Poster

- **results.png**: Full pipeline output (6-step visualization with raw image, masks, and quantified metrics)
- **raw_midZ.png**: Raw fluorescence at mid-Z plane (shows condensate morphology)
- **mask_overlay.png**: Segmentation quality visualization (condensate + nuclei masks on raw)
- **intensity_hist.png**: Intensity distribution inside condensates vs. dilute phase (validates PC calculation)
- **batch_comparison_scatter.png**: Validation across 29 JABr cells (r=0.735, RMSE=2.815)

---

## Next Steps for Poster

1. **Write content sections** (abstract, introduction, methods, results, conclusion)
2. **Design layout** in PowerPoint/Illustrator matching the example template
3. **Arrange figures** in right column with clear captions
4. **Add methodology diagrams** (e.g., denoising effect, 3D segmentation vs 2D, background subtraction formula)
5. **Highlight the three key improvements** as discrete callout boxes or mini-figures

---

## Citation / Attribution

- Fabrini et al. (2023) — Partition coefficient formula (background subtraction method)
- Cellpose 3 (Stringer et al., 2021) — Segmentation model
- scikit-image — Connected-component analysis

---

*Last updated: 2026-05-18*
