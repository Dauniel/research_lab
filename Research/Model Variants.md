# Model Variants & Versions

Overview of different trained and tuned model configurations.

## Training Progression

### Initial Training (Cyto3)
- `cond_cyto3_epoch_0025` - First checkpoint
- `cond_cyto3_resume` - Baseline for continued training

### Clean Training (V2)
- `cond_cyto3_v2_clean_epoch_0010` - Early checkpoint
- `cond_cyto3_v2_clean_epoch_0020` - Later checkpoint
- Cleaner dataset, improved training setup

### Extended Training (Resume)
- Starting from: `cond_cyto3_resume`
- `epoch_0025` - 25 epoch checkpoint
- `epoch_0050` - 50 epoch checkpoint
- `epoch_0075` - 75 epoch checkpoint
- `epoch_0100` - 100 epoch checkpoint (longest run)

## Model Application

### Configuration by Experiment
- **JABr** → Uses trained+tuned variant
- **AABr** → Trained+tuned variant
- **GABr** → Trained+tuned variant
- **Tornado** → Trained+tuned variant

## See Also
- [[Training Pipeline]] - How models are trained
- [[Calibration]] - Parameter tuning per model
