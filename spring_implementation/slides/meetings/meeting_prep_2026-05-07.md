# PI Meeting Prep — 2026-05-07
Last meeting: 2026-04-22

---

## What's been done since last meeting

### Reference PC investigation (4/23)
- Reviewed the manual CSVs for Sample2_5_1 (the ROI we've been benchmarking against)
- Found that the reference PC = 6.32 is **background-subtracted** — the old pipeline wasn't doing this, explaining much of the gap
- B is defined as the minimum voxel intensity across the full FOV

### Background subtraction implemented (4/25)
- Updated pipeline to match the Fabrini et al. 1.8.4 formula:
  - `cond_density = mean(clip(pixel - B, 0))` over condensate ∩ nucleus voxels
  - `dil_density = mean(clip(pixel - B, 0))` over a 10×10×10 patch in the dilute region
- Applied to all five segmentation model scripts for fair comparison

### Spring pipeline built (4/28)
- New `pipeline.py` from scratch: denoise → segment (3D) → measure → volume → PC
- First run: **PC = 6.775** vs reference 6.32 — essentially matching for the first time
- Identified nuclei over-segmentation: Cellpose splits each nucleus into ~15–25 fragments due to internal condensate texture

### Nuclei parameter sweep (4/29)
- Tested `--nuc-cellprob` and `--nuc-diameter` settings; `nuclei` model type also tested
- Best: `cyto3`, `do_3D=True`, `diameter=None`, `cellprob=-2` → **PC = 6.048**
- The dedicated `nuclei` model performed worse on this data (too much internal texture)

### Dilute density stability + final tuning (4/30)
- Single random 10×10×10 patch was seed-dependent (PC swung 4.3–6.0)
- Fix: find all ~88k valid patches in the dilute region, take the **50 lowest-intensity** → deterministic
- Added **3D connected-component relabeling** for nuclei: 76 Cellpose labels → 5 clean nuclei
- **Final single-ROI result: PC = 6.297 (reference = 6.32, error = −0.4%)**

### Batch cross-reference across 30 JABr cells (5/5)
- Ran pipeline on all 30 cells in Box's Cut ROI folder; joined against nuclear reference CSV
- Key finding: Cellpose draws inflated boundaries — mask includes dim halo around bright cores
- Fix: **top-75% brightest voxels** in the condensate mask for `cond_density` (trims Cellpose "fluff")
- Nucleus selection: **central nucleus** (closest to XY center of stack) picks the target cell reliably

| Approach | r | RMSE | Mean bias |
|---|---|---|---|
| All nuclei pooled | 0.681 | 3.250 | −13.4% |
| Central nuc + top-75% | **0.735** | **2.815** | **+2.8%** |
| top-10% (reference-style tight masks) | 0.912 | 13.095 | +119.8% |

- 3 new scripts added: `batch_compare.py`, `batch_sweep_topx.py`, `diagnose_cell.py`

---

## Current status

**Best result: r = 0.735, RMSE = 2.815, mean bias +2.8% across 29/30 JABr cells**

Known failure modes (~6 cells with >30% error — all trace to segmentation, not calibration):
- `Sample1_1_1`: wrong cell selected (+146%)
- `Sample3_3_2`: missed nucleus (−51%)
- `Sample3_3_11`: bright cores undersampled (−38%)
- `Sample2_5_5`: unusually large FOV (32×417×370), target nucleus never detected (−38%)
- `Sample3_3_15`: NaN — central nucleus has zero condensate overlap

---

## Questions / things to discuss

1. **top-75% calibration** — is trimming the bottom 25% of mask voxels a defensible method to report in the paper, or should we pursue tighter segmentation instead?
2. **Generalizability** — should I run batch_compare on other constructs (JwtBr, 10ntABr, etc.) next?
3. **Outlier cells** — worth fixing Sample2_5_5 / Sample3_3_15 specifically, or acceptable to exclude?
4. **Presentation** — still need discussion slides and an "applicability of condensates" intro slide

---

## Numbers to know

| | Value |
|---|---|
| Single-ROI PC (Sample2_5_1) | 6.297 |
| Reference PC (Sample2_5_1) | 6.32 |
| Error | −0.4% |
| Batch r (29 cells) | 0.735 |
| Batch RMSE | 2.815 |
| Batch mean bias | +2.8% |
