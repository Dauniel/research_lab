# Diagnostic Outputs

Per-sample analysis and visualization.

## Output Format

Each diagnostic sample includes:
1. **raw_midZ.png** - Raw image at middle Z-plane
2. **mask_overlay.png** - Predicted segmentation mask overlaid
3. **intensity_hist.png** - Histogram of pixel intensities
4. **summary.txt** - Quantitative metrics (volume, area, etc.)

## Sample Coverage

### Trained Model Diagnostics
- Sample3_3_3_trained - Multiple CPM variants
  - cpm1, cpm2, cpm3 - Different parameter sets
- Sample3_3_15_trained_tuned - Tuned variant

### Baseline Comparison
- Sample3_3_3_cyto3 - Standard cyto3 model output

## Interpretation Guide

### Metrics in summary.txt
- **Volume metrics** - Total segmented volume
- **Area measurements** - 2D slice area
- **Diameter estimates** - Nuclear/condensate size
- **Intensity stats** - Mean, std of raw signal

### Visual Assessment
- **raw_midZ** - Check for imaging artifacts or sample quality
- **mask_overlay** - Evaluate segmentation accuracy
- **intensity_hist** - Identify background/foreground separation

## Accessing Diagnostics
- Location: `outputs/diagnostics/`
- Organized by sample name and variant

## See Also
- [[Analysis]] - Analysis framework overview
- [[Calibration]] - Why diagnostics matter for tuning
