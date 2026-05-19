---
tags: [validation, pipeline, JABr, Sample2_5_1]
construct: JABr
sample: Sample2_5_1
---

# Sample2_5_1 Pipeline Validation

Pipeline run: `--cond-topx 100`, cyto3 baseline model, do_3D=True.
Region: **Nuclear**

## Results vs Reference

| Metric | Nuclear Reference | Pipeline Output | Error |
|--------|------------------|-----------------|-------|
| PC | 6.324 | 6.297 | −0.4% |
| Condensate density | 658.30 | 440.93 | −33% |
| Dilute density | 104.09 | 70.03 | −33% |

> [!note] Both densities are ~33% low but cancel in the ratio, giving a PC within 0.4% of reference.

## Output Files
- `figures/results/summary.csv`
- `figures/results/results.png`
