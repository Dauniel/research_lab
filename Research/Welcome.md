# Research Lab — Condensate Quantification

Spring 2026 project (C&S BIO 199 / 197, PI Elisa Franco). Automate the Imaris-style 3D segmentation and partition-coefficient measurement of nuclear condensates in fluorescence microscopy stacks, then package it for lab-wide use.

## Current Status (2026-05-19)

- **JABr (the primary construct, n=28, LOO-CV honest):** blob_log + linear cal → **14.7% MAE**, beating Cellpose V3 + isotonic cal (~19.8%).
- **Earlier "9.5% MAE" Cellpose number was in-sample (overfit)** — calibration was fit on the same 29 cells it was scored on. Always report LOO-CV.
- **Cross-construct test in progress.** First result (GABr) shows blob_log fails to generalize: MAE 114.8%, r=0.57. JABr's win may be construct-specific.
- **Diagnosed root cause for all model accuracy ceilings: label inconsistency** across the 24-construct training set (per-instance voxel medians range 42 → 1840, a >40× spread). Model architecture and calibration cannot fix this — it's a data problem.

## What This Project Has Built

- **`spring_implementation/pipeline.py`** — single-ROI Cellpose pipeline with Fabrini-formula PC (background-subtracted, top-X% condensate trim, lowest-50-patch dilute density)
- **V3 construct-balanced Cellpose model** (`cond_cyto3_v3_balanced_epoch_0035`) — production condensate model, training-voxel-balanced to fix V1 over-fitting to large-condensate constructs
- **Per-construct calibration table** (`outputs/calibration_table.json`) — isotonic or linear curves applied at inference via `--construct NAME`
- **`batch_blob_log.py`** (2026-05-19) — alternative spot-detection condensate pipeline; currently winning on JABr
- **Tkinter GUI** (`run_gui.py`) — lab-friendly wrapper around the CLI

## Main Topics
- [[JABr Experiments]] — current best result, threshold sweeps, LOO-CV
- [[Cross-Construct Performance]] — generalization beyond JABr (V1 history + V3 + blob_log)
- [[Pipeline Mechanics]] — the 6-step pipeline, every component and why it exists
- [[Pipeline Tools]] — full script catalogue + typical workflows
- [[Model Variants]] — Cellpose lineage (V1 / V2 / V3 + V3 balanced) + blob_log spot detector
- [[Training Pipeline]] — V3 construct-balanced training, hardware, what didn't help
- [[Calibration]] — isotonic vs linear, in-sample vs out-of-sample
- [[Spot Detection]] — `blob_log` algorithm, threshold sweep, sigma choice

## Reference Data
- [[reference_data/Reference Data Index|All constructs]]
- [[reference_data/JABr Reference Data|JABr]] (primary target, n=29 nuclear cells)

## Source of Truth
- **Daily progress log:** `spring_implementation/progress_log.txt` (1395 lines, 2026-04-22 → present)
- **Box reference data:** `C:\Users\Danie\Box\Condensate Volume Quantification\<construct>\` — Cut ROI, Imaris files, Statistics-cleaned, Cell Number, nuclear/cytoplasmic PC CSVs
