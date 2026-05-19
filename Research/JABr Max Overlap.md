# JABr Max Overlap

Alternative nucleus selection using max-overlap heuristic.

## Location
`outputs/experiments/batch_JABr_maxoverlap/`

## Files
- Results: `comparison.csv`
- Visualization: `scatter.png`

## Strategy
Instead of basic selection, uses maximum-overlap nucleus heuristic:
- Identifies nucleus with largest overlap to reference
- Reduces false positives in crowded regions
- More robust to segmentation artifacts

## Performance
Good improvement, comparable to [[JABr Trained Tuned]].
Alternative approach with different tradeoffs.

## Implementation
Referenced in progress notes as key improvement.

## See Also
- [[JABr Experiments]] - Full series
- [[Calibration]] - Related optimization work
