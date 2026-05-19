# M187 Research Poster Structure

## Poster Layout (Academic Poster Format)

### Top Section
- **Title**: Automated Segmentation and Partition Coefficient Analysis of RNA-Aptamer Condensates
- **Authors**: Daniel Chang, Elisa Franco (PI) | UCLA

### Left Column
1. **Abstract** (top)
   - Goal, approach, key result

2. **Introduction**
   - Background on biomolecular condensates
   - JABr aptamer system
   - Existing challenges in automated segmentation
   - Reference PC = 6.32 baseline

### Center Column
3. **Materials & Methods**
   - Pipeline overview (6 steps)
   - Cellpose 3 with 3D mode
   - Three key improvements that enabled PC matching

4. **Methodology** (detailed)
   - Denoising (DenoiseModel cyto3)
   - 3D segmentation (do_3D=True)
   - Connected-component nuclei refinement
   - Background subtraction formula
   - Lowest-intensity patch selection for dilute density

### Right Column
5. **Results**
   - Single-ROI validation: PC = 6.297 vs 6.32 (−0.4% error)
   - Figures:
     * Raw image + segmentation overlay
     * PC comparison chart
     * Step-by-step pipeline outputs

6. **Conclusion**
   - Summary of achievements
   - Biological implications
   - Next steps (generalization to other constructs)

### Bottom Right
7. **Acknowledgements**
   - PI, collaborators, funding

---

## Directory Structure
```
M187_Presentation/
├── content/
│   ├── abstract.txt
│   ├── introduction.txt
│   ├── methods.txt
│   ├── results.txt
│   ├── conclusion.txt
│   └── acknowledgements.txt
├── figures/
│   ├── results/
│   │   ├── sample2_5_1_raw_image.png
│   │   ├── sample2_5_1_segmentation_overlay.png
│   │   ├── pc_comparison_chart.png
│   │   └── pc_accuracy_summary.csv
│   └── pipeline/
│       ├── pipeline_workflow_diagram.png
│       ├── cellpose_3d_mode_explanation.png
│       └── background_subtraction_formula.png
├── layouts/
│   └── poster_template.pptx (or .ai)
└── POSTER_OUTLINE.md (this file)
```

---

## Key Results to Highlight
- **PC Achievement**: 6.297 (pipeline) vs 6.32 (reference) = −0.4% error
- **Three Critical Improvements**:
  1. Background subtraction (Fabrini et al. method)
  2. Connected-component nuclei relabeling (76 labels → 5 true regions)
  3. Lowest-intensity patch selection for dilute density (50 patches vs 1 unstable patch)
