# Batch Comparison Results

Comparative analysis across experiments and organism types.

## Comparison Framework
- Tool: `batch_compare.py`
- Latest version: `evaluate_v2.py`
- Outputs: CSV comparison tables and scatter plots

## Experiments Compared

### JABr Variants
- Original vs Trained vs Trained+Tuned
- Shows progressive improvement
- Max-overlap heuristic comparison

### Cross-Organism
- JABr trained+tuned (baseline)
- AABr trained+tuned
- GABr trained+tuned
- Tornado trained+tuned

## Results Structure
Each batch comparison includes:
- `comparison.csv` - Quantitative metrics
- `scatter.png` - Visual scatter plot comparison
- Metrics: accuracy, precision, recall, F1, etc.

## Key Insights
- Trained models consistently outperform original
- Tuning provides additional marginal improvements
- Cross-organism consistency validates training approach
- Tornado shows different characteristics

## See Also
- [[JABr Experiments]] - Primary series
- [[Analysis]] - Diagnostic details
