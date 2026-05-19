# Training Pipeline

Cellpose 3 fine-tuning for nuclear-condensate segmentation. Three generations of training runs (V1, V2, V3); V3 construct-balanced epoch 35 is the current production checkpoint.

## Data Source

- Builder: `build_training_data.py` — slices Imaris-segmented 3D volumes from Box into 2D Cellpose patches.
- Raw manifest: `training/dataset/manifest.csv` — 664 (or 663 depending on version) labeled 3D volumes across 24 constructs.
- Clean manifest: `training/dataset/manifest_clean.csv` — 542 volumes after dropping two outlier constructs and per-construct voxel-per-instance outliers.
- Skipped: `training/dataset/skipped.csv`.
- Each volume sliced into 2D Z-planes (filter: ≥3 instances per slice).
- Sources: per-construct Imaris `.ims` files under `Box/Condensate Volume Quantification/<construct>/`.

## V1 — `cond_cyto3_resume` (April 22 → May 16)
- Pretrained: `cyto3`
- Schedule: first attempt stopped at epoch 25 (terminal closure overnight). Resumed from `cond_cyto3_epoch_0025` checkpoint, ran 125 more epochs (~10 h total).
- Loss curve (resume): epoch 0 (train=0.107, val=0.120) → epoch 100 (train=0.087, val=0.107) → epoch 120 plateau (train=0.088, val=0.107). Best val 0.1065 at epoch 110.
- Checkpoints preserved at epochs 25, 50, 75, 100, plus final `cond_cyto3_resume`.
- **Cross-construct results** drove the V3 retrain decision — see [[Cross-Construct Performance]].

## V2 — `cond_cyto3_v2_clean` (May 16, short-lived)
- Pretrained: `cyto3`
- Manifest: `manifest_clean.csv` (542 vols)
- Stopped at epoch 20. Checkpoints `epoch_0010`, `epoch_0020` preserved.
- Superseded by V3 before extensive evaluation — the cleaning step alone didn't fix the voxel-imbalance problem.

## V3 — `cond_cyto3_v3_balanced` (May 16 → 18, current production)

### Motivation
V1 analysis showed severe **training-voxel imbalance**:
- GwtBr alone contributed 17.4% of all training voxels (large condensates)
- The 4 target constructs (JABr + GABr + AABr + JABr_4arm) combined: only 7%
- Diagnosis: V1 over-fit to large-condensate morphology, generalized poorly to small-condensate constructs (GABr, AABr, Tornado all had Pearson r < 0.6 at best)

### Solution
`--balance-constructs` flag added to `train_cellpose.py`. Upsamples underrepresented constructs so each contributes equal slice count.
- Before balance: 15,183 slices, GwtBr-dominated
- After balance (`--balance-cap 700`): 22 constructs × 700 slices = 15,400 slices

### Schedule
- Three attempts on 2026-05-16; first OOM'd (35k slices without cap), second hit an arg-parse bug, third (`--balance-cap 700`) ran cleanly at ~3.5 min/epoch on RTX 4080.
- Checkpoints saved every 5 epochs.
- Loss plateaued by epoch ~20 (test_loss ~0.106 at epoch 20-30, vs 0.117 at epoch 5). Stopped at epoch 35 (more epochs unlikely to help).

### Production Checkpoint
`spring_implementation/training/models/models/cond_cyto3_v3_balanced_epoch_0035`

Inference flags: `--cond-cellprob -2.0 --cond-topx 75`.

### Resume Command (for future use)
```
python spring_implementation/training/train_cellpose.py \
    --dataset spring_implementation/training/dataset \
    --output spring_implementation/training/models \
    --manifest spring_implementation/training/dataset/manifest_clean.csv \
    --balance-constructs --balance-cap 700 \
    --name cond_cyto3_v3_balanced \
    --epochs 150 --save-every 5
```

## Hardware

- **DANIEL-PC** with NVIDIA GeForce RTX 4080
- V3 balanced: ~3.5 min/epoch (15.4k slices)
- V1 unbalanced: ~5 min/epoch (15.2k slices)
- Power management: run `keep_awake.ps1` alongside multi-hour training to keep Windows from sleeping mid-run (the previous Tornado run died this way).

## Monitoring Tools
- `training/watch_training.py` — tails the loss curve during training.
- `training/watch_system.py` — terminal-only GPU / VRAM / CPU / RAM monitor with ANSI bar charts (rewritten 2026-05-18 to remove matplotlib GUI). Flags: `--refresh`, `--bar-width`.

## What's Already Been Ruled Out

- **More epochs.** Loss plateaued by epoch 20-30. Residual error is precision/labeling, not capacity.
- **Switching to Cellpose `nuclei` model for the nuclei pass.** Trained on clean DAPI; over-fragments on aptamer signal with internal texture.
- **Diameter tuning at inference** (`--diameter`, `--nuc-diameter`). Auto-detect (`None`) wins on every construct tested.
- **Cellprob sweep beyond `-2.0`.** Marginal effect on density (mean shifted ~9% across the range). Wrong knob.
- **Per-construct ridge with multi-feature inputs** (pipeline_pc + cond_density + dilute_density). Underperforms single-feature isotonic. Extra features inject noise on small datasets.

## The Diagnosed Bottleneck

Audit across 24 training constructs (`audit_labels.py`):
- Median voxels-per-instance: **42 (15ntEMango) to 1840 (GwtBr) — 40× spread**
- Within JABr_4arm alone, CV = 1.15 (30× range cell-to-cell)
- The model learned ~24 different definitions of "what a condensate is"

Post-hoc methods (calibration, threshold tuning, ensembling) cannot fix this. To break past current accuracy ceilings on under-represented constructs, the next move is **label cleanup at the source**, not more training.

## See Also
- [[Model Variants]] — checkpoint catalogue
- [[Cross-Construct Performance]] — V1 5-construct results, label inconsistency diagnosis
- [[Calibration]] — post-training fix-ups
- [[JABr Experiments]] — current evaluation results
