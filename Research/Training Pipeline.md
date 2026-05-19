# Training Pipeline

Cell segmentation model training and development.

## Data
- Training data built in `build_training_data.py`
- Manifest: `training/dataset/manifest.csv` (664 samples)
- Clean manifest: `training/dataset/manifest_clean.csv` (543 samples)
- Skipped samples: `training/dataset/skipped.csv`

## Models

### Cyto3 Models
- `cond_cyto3_epoch_0025` - 25-epoch checkpoint
- `cond_cyto3_resume` - Resume training baseline
- `cond_cyto3_v2_clean` - Cleaned training variant
  - `epoch_0010` - 10-epoch checkpoint
  - `epoch_0020` - 20-epoch checkpoint

### Resume Training
- `cond_cyto3_resume_epoch_0025` - 25 epochs
- `cond_cyto3_resume_epoch_0050` - 50 epochs
- `cond_cyto3_resume_epoch_0075` - 75 epochs
- `cond_cyto3_resume_epoch_0100` - 100 epochs

## Monitoring
- `watch_training.py` - Training progress tracking
- `watch_system.py` - System resource monitoring
- `train_cellpose.py` - Main training script

## See Also
- [[Calibration]] - Tuning parameters after training
