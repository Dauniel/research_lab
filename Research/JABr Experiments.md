# JABr Experiments

Primary experimental series with JABr sample type.

## Variants Tested

### Original Implementation
- [[JABr Original]] - Baseline nucleus selection

### Trained Model
- [[JABr Trained]] - Using trained cellpose model
- Results show significant improvement over original

### Trained + Tuned
- [[JABr Trained Tuned]] - Best performing variant
- Incorporates calibration and parameter optimization
- Reference configuration for other organisms

### Alternative Selection Strategies
- [[JABr Central]] - Select central nucleus only
- [[JABr Largest Nuc]] - Select largest nucleus
- [[JABr Overlap]] - Overlap-based selection
- [[JABr Max Overlap]] - Max-overlap nucleus heuristic

### Multi-Arm Configuration
- [[JABr 4-Arm]] - 4-armed configuration variant

## Results Summary
| Variant | Status | Notes |
|---------|--------|-------|
| Original | Baseline | High variance |
| Trained | Good | Consistent improvement |
| Trained Tuned | **Best** | Optimized parameters |
| Max Overlap | Good | Better nucleus selection |
| 4-Arm | Promising | Alternative approach |

## See Also
- [[Experiments]] - Other experiment series
- [[Calibration]] - Parameter tuning approach
