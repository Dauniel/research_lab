# Analysis & Results

Diagnostic outputs, visualizations, and interpretation.

## Diagnostic Outputs

### Sample Analysis
- Location: `outputs/diagnostics/`
- Per-sample includes:
  - `raw_midZ.png` - Raw middle Z-slice image
  - `mask_overlay.png` - Predicted mask overlaid on raw
  - `intensity_hist.png` - Intensity distribution
  - `summary.txt` - Quantitative metrics

### Featured Samples
- [[Sample3 3 3 Trained]] - Trained model results
- [[Sample3 3 3 Cyto3]] - Cyto3 baseline
- [[Sample3 3 15 Trained Tuned]] - Trained + tuned variant

## Batch Comparisons
- [[Batch Comparison]] - Cross-experiment comparison results
- Comparison CSVs and scatter plots in `outputs/experiments/`

## ROI Sample Analysis
- Detailed measurements in `outputs/roi_sample/`
- Condensate and nuclei volumes
- Quantitative summary

## Evaluation Tools
- `evaluate_v2.py` - Latest evaluation framework
- `batch_compare.py` - Batch comparison pipeline
- `batch_sweep_topx.py` - Top-X sweep analysis
