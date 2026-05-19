# Diameter Sweep Analysis

Parameter sweep for nucleus diameter optimization.

## Overview
- Script: `diameter_sweep.py`
- Tests different nucleus diameter parameters
- Identifies optimal settings per organism

## Results
- Location: `outputs/diagnostics/diameter_sweep_AABr/`
- Main output: `sweep.csv`
- Tabulates performance across diameter range

## Parameters
Tests nucleus diameter across typical biological range
- Measures segmentation quality
- Compares to reference measurements
- Finds parameter that minimizes error

## Application
- Results feed into [[Calibration]] optimization
- Used to set default nucleus diameter per organism
- Cross-referenced in [[Model Variants]] tuning

## See Also
- [[Calibration]] - Overall tuning framework
- [[Analysis]] - Results interpretation
