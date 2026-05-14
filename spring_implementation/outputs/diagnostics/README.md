# Diagnostic Analysis of 5 Bad Cases

All 5 outlier cases from the batch processing have been analyzed with full diagnostics.

## Directory Structure

```
diagnostics/
├── BAD_CASES_SUMMARY.txt           ← Comprehensive analysis of root causes
├── diagnose_Sample1_1_1/           ← Case 1: Wrong cell (+146% error)
│   ├── raw_midZ.png                   [raw nuclei & condensate channels]
│   ├── mask_overlay.png               [segmentation masks overlaid]
│   └── intensity_hist.png             [intensity distributions]
├── diagnose_Sample3_3_2/           ← Case 2: Missed nucleus (-51% error)
├── diagnose_Sample3_3_11/          ← Case 3: Bright cores undersampled (-38% error)
├── diagnose_Sample2_5_5/           ← Case 4: Wide FOV, wrong nucleus (-38% error)
└── diagnose_Sample3_3_15/          ← Case 5: NaN - zero condensate overlap
```

## Quick Summary

| Case | Error | Root Cause | Fix |
|------|-------|------------|-----|
| Sample1_1_1 | +146% | Central nucleus wrong / mask too loose | Test max-overlap heuristic |
| Sample3_3_2 | -51% | Central nucleus missing some condensates | Switch to max-overlap |
| Sample3_3_11 | -38% | Top-75% not aggressive enough | Adaptive trimming (use top-25% when bimodal) |
| Sample2_5_5 | -38% | Wide FOV, central nucleus 102px away | Switch to max-overlap |
| Sample3_3_15 | NaN | Central nucleus too small, zero overlap | Add fallback (max-overlap or largest) |

## How to View

Open each diagnostic folder to see 4 files:
1. **summary.txt** — Text output with all metrics
2. **raw_midZ.png** — Mid-Z slices of nuclei (blue) and condensate (green) channels
3. **mask_overlay.png** — 3-panel view:
   - Left: Raw condensate image
   - Middle: Segmentation masks (green=condensate, cyan=central nucleus)
   - Right: Region used for PC calculation (red highlight)
4. **intensity_hist.png** — 2-panel histograms showing intensity distributions

## Key Findings

**Nucleus Selection Issue (4 of 5 cases)**
- Central nucleus heuristic assumes target cell is at image center
- Fails for:
  - Wide FOVs (Sample2_5_5: 417×370 pixels, nucleus 102px from center)
  - Cells where central nucleus doesn't contain all condensates (Sample3_3_2)
  - Abnormally small central nuclei (Sample3_3_15)
  - Possibly wrong nucleus selected (Sample1_1_1)

**Recommended Fix:** Switch to **max-overlap nucleus heuristic**
- Pick the nucleus with the MOST condensate-mask overlap
- Falls back to largest nucleus if max-overlap has zero voxels
- Should solve ~4 of the 5 bad cases

**Adaptive Trimming Issue (1 case)**
- Fixed top-75% trim doesn't work for all cells
- Sample3_3_11: needs top-25% instead (1314.9 vs 470.3 mean)
- Should detect intensity distribution bimodality and adjust per-cell

---

**Next step:** Implement fixes and re-run batch_compare on all 30 cells
