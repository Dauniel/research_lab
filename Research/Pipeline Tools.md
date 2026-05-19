# Pipeline Tools

Catalogue of every script in `spring_implementation/` and what it does. Use this as a "I want to do X — which script do I run?" lookup.

## Core Pipeline

| Script | Purpose |
|---|---|
| `pipeline.py` | Single-ROI end-to-end Cellpose pipeline. Reads TIF(s), denoises, segments, computes PC. Optional `--construct NAME` triggers calibration lookup. See [[Pipeline Mechanics]]. |
| `batch_compare.py` | Run `pipeline.py` over an entire `Cut ROI/` folder and compare each cell's PC to the reference CSV. Outputs `comparison.csv` + `scatter.png`. |
| `batch_blob_log.py` | Same as `batch_compare.py` but swaps Cellpose condensates for `skimage.feature.blob_log` (LoG spot detection). Nuclei still Cellpose. See [[Spot Detection]]. |
| `run_gui.py` | Tkinter GUI wrapping `pipeline.py` for lab members who don't use the CLI. Single-file + batch tabs; live log streaming. macOS-safe (no `*.ome.tif` filter). |

## Diagnostics & Sweeps

| Script | Purpose |
|---|---|
| `diagnose_cell.py` | Deep diagnostic for one TIF: raw mid-Z PNG, mask overlay, intensity histograms, density variants (mean, top-50%, top-25%, peak), mask coverage stats. First tool when something looks wrong. |
| `batch_sweep_topx.py` | Run the same segmentation but compute density at top-X% ∈ {10, 20, 25, 30, 40, 50, 75, full} across a full construct dataset. Used to validate `cond_topx=75`. |
| `diameter_sweep.py` | Per-construct Cellpose `diameter` sweep at inference. Conclusion (May 16): explicit diameters always lose to `None` (auto-detect). |
| `analyze_calibration.py` | LOO-CV across linear / isotonic / weighted-ensemble calibrations. Picks the best per construct. Outputs `calibration_table.json` and `calibration_summary.csv`. |
| `evaluate_v2.py` | One-command harness: runs `batch_compare` + `analyze_calibration` across all 5 focus constructs using a given model. Built for V2 evaluation, reusable for V3. |
| `audit_labels.py` | Surveys training-label statistics across constructs (median voxels-per-instance, CV, etc.). Diagnosed the label-inconsistency problem driving V3. |

## Training

| Script | Purpose |
|---|---|
| `training/train_cellpose.py` | Main training script. Flags include `--balance-constructs`, `--balance-cap`, `--manifest`, `--save-every`. Resume by passing a checkpoint to `--pretrained-model`. |
| `training/watch_training.py` | Tail the loss curve during training. |
| `training/watch_system.py` | Terminal-only GPU / VRAM / CPU / RAM monitor with ANSI bar charts. Refreshes in place (`\033[nA`), no matplotlib GUI. Flags: `--refresh`, `--bar-width`. |
| `build_training_data.py` | Slice Imaris-segmented 3D volumes into Cellpose-compatible 2D patches. Writes `manifest.csv`. |
| `keep_awake.ps1` | `SetThreadExecutionState` wrapper. Run alongside multi-hour training so Windows doesn't sleep. |

## Generated Artifacts

| Path | Contents |
|---|---|
| `outputs/<roi>/` | Single-ROI pipeline output (masks, summary, results.png) |
| `outputs/experiments/batch_*/` | Per-construct batch comparison runs |
| `outputs/blob_<construct>_thresh*/` | `batch_blob_log.py` runs |
| `outputs/diagnostics/<sample>_<config>/` | `diagnose_cell.py` outputs |
| `outputs/calibration_table.json` | Per-construct calibration curves used at inference |
| `outputs/calibration_summary.csv` | LOO-CV stats from `analyze_calibration.py` |
| `training/dataset/manifest_clean.csv` | Cleaned training manifest (542 vols, drops outlier constructs) |
| `training/models/models/cond_cyto3_v3_balanced_epoch_*` | V3 checkpoints (5/10/15/20/25/30/35) |

## Reference Files

| Path | Contents |
|---|---|
| `progress_log.txt` | Day-by-day project journal back to 2026-04-22. Primary source for any "why does X exist" question. |
| `reference/pipeline_tutorial.txt` | Tutorial-style guide for the four CLI scripts. |
| `slides/week5/` | Week-5 class presentation assets. |
| `slides/meetings/meeting_*` | Date-stamped PI-meeting materials. |

## Typical Workflows

**"I have a new ROI — what's its PC?"**
```
python pipeline.py --roi <path>.tif --output outputs/<name> \
    --cond-model training/models/models/cond_cyto3_v3_balanced_epoch_0035 \
    --cond-cellprob -2.0 --cond-topx 75 --construct JABr
```

**"How does the V3 model do across an entire JABr dataset?"**
```
python batch_compare.py \
    --construct-dir "C:/Users/Danie/Box/Condensate Volume Quantification/JABr" \
    --output outputs/experiments/batch_JABr_v3 \
    --cond-model training/models/models/cond_cyto3_v3_balanced_epoch_0035 \
    --cond-cellprob -2.0 --cond-topx 75
```

**"Try the spot detector instead of Cellpose."**
```
python batch_blob_log.py \
    --construct-dir "C:/Users/Danie/Box/Condensate Volume Quantification/JABr" \
    --output outputs/blob_JABr_thresh03 \
    --blob-threshold 0.03 --cond-topx 75
```

**"This cell looks wrong — what's going on?"**
```
python diagnose_cell.py --roi <path>.tif --output outputs/diagnostics/<sample>_<config> \
    --cond-model training/models/models/cond_cyto3_v3_balanced_epoch_0035
```

## See Also
- [[Pipeline Mechanics]] — what each step does internally
- [[Model Variants]] — which `--cond-model` to choose
- [[Calibration]] — how `--construct` translates to a calibration curve
