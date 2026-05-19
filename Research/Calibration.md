# Calibration & Analysis

Post-training calibration and parameter tuning.

## Calibration Analysis
- Script: `analyze_calibration.py`
- Summary: `outputs/calibration_summary.csv`
- Table: `outputs/calibration_table.json`

## Diameter Sweep
- Script: `diameter_sweep.py`
- Tests nucleus diameter parameter optimization
- Results in `outputs/diagnostics/diameter_sweep_AABr/`

## Top-X Analysis
- Testing different nucleus selection strategies (top 25%, top 50%, etc.)
- Results in `outputs/diagnostics/sweep_topx_JABr/`

## Key Findings
- Max-overlap nucleus heuristic improved results
- Mask quality identified as root cause for bad cases
- Calibration reduces variance across sample types

## Diagnostics
See [[Diagnostic Outputs]] for per-sample analysis.
