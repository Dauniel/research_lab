# M187 Presentation — Getting Started

## What's Ready

Your presentation directory is fully populated with:

### ✓ Research Data & Figures
- **results.png**: Full 6-step pipeline output visualization
- **summary.csv**: Key metrics (PC = 6.297 vs 6.32 reference)
- **mask_overlay.png**: Segmentation quality (masks on raw image)
- **raw_midZ.png**: Raw fluorescence at mid-Z slice
- **intensity_hist.png**: Intensity distribution validation
- **batch_comparison_scatter.png**: Validation across 30 JABr cells (r=0.735)
- **Measurement CSVs**: Per-object and volumetric data

### ✓ Content Sections (Ready to Use)
- **abstract.txt** — 200 words, highlights the 6.297 vs 6.32 achievement
- **introduction.txt** — JABr system, reference standard, motivation
- **methods.txt** — 6-step pipeline, three key improvements explained
- **results.txt** — Single-ROI PC matching + batch validation stats
- **conclusion.txt** — Achievements, advantages, future directions
- **acknowledgements.txt** — Credits, funding, references

### ✓ Code Reference
- **pipeline.py** — Main pipeline (for technical appendix if needed)

---

## Next Steps to Create Your Poster

### 1. Choose a Design Tool
- **PowerPoint** (easiest, good enough for academic posters)
- **Adobe Illustrator** (professional, more control)
- **Canva** (web-based, templates available)
- **LaTeX + TikZ** (scriptable, publication-ready)

### 2. Poster Layout Template
Follow the example format provided (4-column, color-coded sections):

```
┌─────────────────────────────────────────────────────────────┐
│  Title: Automated Segmentation of RNA-Aptamer Condensates   │
│  Authors: Daniel Chang & Elisa Franco | UCLA Bioengineering  │
└─────────────────────────────────────────────────────────────┘

┌──────────────┬──────────────┬──────────────┬──────────────┐
│              │              │              │              │
│  ABSTRACT    │  MATERIALS & │  RESULTS     │  CONCLUSION  │
│  (top-left)  │  METHODS     │  (center)    │  (right)     │
│              │  (left)      │              │              │
├──────────────┼──────────────┼──────────────┼──────────────┤
│              │              │              │              │
│ INTRO-       │  METHODOLOGY │  FIGURES:    │ FUTURE       │
│ DUCTION      │  (left)      │  - results   │ DIRECTIONS   │
│              │              │  - scatter   │              │
│              │              │  - overlay   │              │
└──────────────┴──────────────┴──────────────┴──────────────┘

ACKNOWLEDGEMENTS (bottom)
```

### 3. Fill In Poster
1. Copy title: "Automated Segmentation and Partition Coefficient Analysis of RNA-Aptamer Condensates"
2. Copy authors: "Daniel Chang & Elisa Franco | UCLA Department of Bioengineering"
3. Copy sections from `content/` directory
4. Arrange figures:
   - Raw image + segmentation overlay (mask_overlay.png)
   - PC comparison chart (main result: 6.297 vs 6.32)
   - Batch validation scatter (batch_comparison_scatter.png)
   - Pipeline workflow diagram (optional: add text box explaining 6 steps)
5. Highlight three key improvements (as mini-callout boxes)

### 4. Key Callout Boxes

**Improvement #1: Background Subtraction**
```
PC = (Σ[pixel - B] in condensate) / (Σ[pixel - B] in dilute)
B = minimum voxel intensity across FOV
Single largest accuracy jump (2.04 → 3.33 PC)
```

**Improvement #2: Connected Components**
```
Cellpose 76 labels → 3D connected components → 5 true nuclei
Removes internal fragments from condensate texture
Cleans dilute-phase pixel selection
```

**Improvement #3: Robust Dilute Density**
```
Find all ~88,000 valid 10×10×10 patches
Sort by intensity, take average of lowest 50
Eliminates seed-dependent swing (4.3 to 6.0 → stable 6.297)
```

### 5. Design Tips
- Use consistent colors (blue for pipeline steps, orange for results, green for validation)
- Large fonts (title 48pt, section headers 36pt, body text 20–24pt)
- White/light background for readability
- Emphasize the **−0.4% error** as the headline achievement
- Include at least 3 figures (raw image, segmentation, PC comparison)
- Balance text and visuals (roughly 40% text, 60% figures)

### 6. Print Considerations
Standard poster size: **36" × 48"** (portrait)
- High-DPI images (300 ppi recommended for print)
- All figures in `figures/` are screen-res; request high-res versions from pipeline if printing

---

## Quick Reference: Key Numbers

| What | Value |
|------|-------|
| Pipeline PC | 6.297 |
| Reference PC | 6.32 |
| Error | −0.4% |
| Batch r | 0.735 |
| Batch RMSE | 2.815 |
| Batch n | 29 cells |
| Condensates detected | 186 |
| Nuclei after CC | 5 |

---

## Questions?

Refer to:
- `README.md` for overview and materials list
- `POSTER_OUTLINE.md` for layout template
- `content/` for full text of each section
- `figures/` for all visualizations
- `pipeline.py` for technical implementation details

Good luck with your poster! 🎨
