---
tags: [reference, index]
---

# Reference Data Index

Partition coefficient reference measurements from Box › Condensate Volume Quantification.
Each node contains cytoplasmic and/or nuclear tables (condensate density, dilute density, partition coefficient).

Source layout (per construct in Box):
- `Cut ROI/*.tif` — 2-channel (nuclei + condensate) Z-stacks; pipeline input
- `Imaris file/*.ims` — Imaris source with surface annotations
- `Statistics-cleaned/inside/*_inside.xls` — per-condensate-surface measurements (used for ground-truth condensate counts)
- `Cell Number/<construct>.xlsx` — analyst's per-ROI cell count
- `<construct>_Partition coefficient_nuclear.csv` — per-ROI reference PC (one row per ROI; multi-cell ROIs aggregated)

For head-to-head pipeline-vs-reference comparison, see [[../JABr Experiments|JABr Experiments]] (only construct with pipeline evaluation so far).

## Pipeline Evaluation Status

| Construct                         | Pipeline run             | Best honest MAE                       | Calibration fit |
| --------------------------------- | ------------------------ | ------------------------------------- | --------------- |
| JABr                              | ✅ Cellpose V3 + blob_log | **14.7%** (blob_log + linear, LOO-CV) | isotonic table  |
| GABr / AABr / JABr_4arm / Tornado | ⏳ not yet run on V3      | —                                     | needs rebuild   |
| Others                            | ⏳ not yet                | —                                     | —               |

## Constructs with Data

| Construct | Cytoplasmic (n) | Nuclear (n) |
|-----------|----------------|-------------|
| [[JABr Reference Data]] | 30 | 30 |
| [[GABr Reference Data]] | 31 | 30 |
| [[AABr Reference Data]] | 26 | 26 (25 nuclear) |
| [[JABr 4-Arm Reference Data]] | 37 | 37 |
| [[JABr 2-Arm Reference Data]] | 9 | 24 |
| [[JAMango Reference Data]] | 31 | 32 |
| [[JAPP Reference Data]] | 26 | 25 |
| [[JwtBr Reference Data]] | 26 | 25 |
| [[JEBr Reference Data]] | 10 | 20 |
| [[JFBr Reference Data]] | 12 | 16 |
| [[AwtBr Reference Data]] | 33 | 33 |
| [[GwtBr Reference Data]] | 32 | 31 |
| [[10ntABr Reference Data]] | 28 | 0 (empty) |
| [[10ntABr 4-Arm Reference Data]] | 33 | 18 |
| [[10ntABr 5-Arm Reference Data]] | 28 | 27 |
| [[10ntwtBr Reference Data]] | 31 | 1 |
| [[Tornado Reference Data]] | 0 (empty) | 18 |

## Constructs Pending Data

| Construct | Notes |
|-----------|-------|
| [[15ntBPP Reference Data]] | No CSVs in Box |
| [[15ntCMango Reference Data]] | No CSVs in Box |
| [[15ntEMango Reference Data]] | No CSVs in Box |
| [[15ntFMango Reference Data]] | No CSVs in Box |
| [[15ntwtPP Reference Data]] | No CSVs in Box |
| [[ABPP Reference Data]] | No CSVs in Box |
| [[JABr MS2-mCherry Reference Data]] | No CSVs in Box |
| [[JABr mCherry Reference Data]] | No CSVs in Box |
| [[JBPP Reference Data]] | No CSVs in Box |
