# Calibration & Analysis

Every model we've tried produces PC values with a systematic offset vs the Imaris reference. Calibration is a per-construct map `pipeline_pc → ref_pc` fit on a held set of cells. The pipeline applies it at inference when `--construct NAME` is passed.

## Table Format

`outputs/calibration_table.json`. Per-construct entry, two flavors:

```json
"JABr": {
  "kind": "isotonic",
  "xs": [...sorted pipeline_pc values...],
  "ys": [...corresponding mapped values...]
}
```

```json
"GABr": {
  "kind": "linear",
  "slope": 0.624,
  "intercept": 0.0
}
```

At inference, `pipeline.apply_calibration()` dispatches on `entry["kind"]`:
- `linear` → `slope * pipeline_pc + intercept`
- `isotonic` → `np.interp(pipeline_pc, xs, ys)` (clamped at endpoints)
- Unknown construct or missing entry → return raw value, no calibration applied

Calibrated PC and construct are written to `summary.csv` as `pc_calibrated` and `construct` rows when calibration fires.

## CRITICAL: In-Sample vs Out-of-Sample

Earlier `progress_log.txt` entries (and earlier versions of this vault) quoted in-sample MAEs — calibration fit on the *same* 29 cells it was scored on. Isotonic regression with n=29 makes n_segments = 29 → near-zero training error. These numbers are not predictive.

**Always report LOO-CV or held-out MAE.** Honest LOO-CV numbers on JABr (2026-05-19):

| Model | Calibration | LOO-CV MAE |
|---|---|---|
| Cellpose V3 epoch 35 | linear | 21.7% |
| Cellpose V3 epoch 35 | isotonic | 19.8% |
| blob_log (thresh=0.03) | linear | **14.7%** |
| blob_log (thresh=0.03) | isotonic | 14.8% |
| Ensemble (0.81·blob + 0.19·CP) | isotonic | 14.3% |

Linear vs isotonic on these datasets is within ≤1%. **Default to linear** — simpler, harder to overfit, and the cross-construct calibration constant for V1 (`k ≈ 0.58-0.62`) stayed stable across constructs.

## Calibration Family Decisions Already Made

- **Linear (through origin):** the V1 calibration was `pc_imaris ≈ 0.576 · pipeline_pc`. Worked but had +RMSE 2.86 on JABr.
- **Full linear (slope + intercept):** `pc_imaris ≈ 0.379 · pipeline_pc + 3.72` for V1 on JABr. RMSE 1.91, ~37% better than through-origin.
- **Isotonic:** strictly best on V1 trained model (non-linear pipeline-to-ref relationship). On AABr, isotonic lifted r=0.15 → r=0.45 just from rank-rebinning.
- **Polynomial:** tried, worse than isotonic.
- **Multi-feature ridge:** tried (pipeline_pc + cond_density + dilute_density). Underperforms single-feature isotonic. Extra features inject noise.
- **Weighted ensemble before calibration:** mix(0.85·trained + 0.15·cyto3) → isotonic adds ~+0.03 Pearson r on JABr. Needs paired baselines (only have for JABr + Tornado).

## Per-Construct Calibration Strategy (V1, May 16)

| Construct | Best strategy | r_best | MAE | within ±20% |
|---|---|---|---|---|
| JABr | mix(0.85t,0.15c) + isotonic | 0.90 | 15.6% | 69% |
| GABr | trained + isotonic | 0.55 | 59% | 35% |
| AABr | trained + isotonic | 0.45 | 57% | 44% |
| JABr_4arm | trained + isotonic | 0.79 | 30% | 49% |
| Tornado | cyto3 + isotonic | 0.13 | 22% | 50% |

Tornado calibration deliberately uses cyto3 baseline, not trained model (V1 trained dropped below cyto3 on this held-out construct).

## Sweeps

- **`batch_sweep_topx.py`** — top-X% trim sweep. Validated `cond_topx=75` for Cellpose masks. Top-10% has highest Pearson (r=0.91) but +120% mean bias; top-75% has best calibration with +2.8% mean bias.
- **`diameter_sweep.py`** — Cellpose `diameter` sweep at inference. Conclusion: auto-detect (`None`) wins on every construct tested. Explicit diameters always lose.
- **`batch_blob_log.py` threshold sweep on JABr** — 0.02 / 0.03 / 0.04 / 0.05, all within 14.7-15.6% MAE after linear cal. Calibration dominates. Highest correlation: 0.02 (r=0.938).

## Spearman vs Pearson Check (V1, all 5 constructs)

| Construct | Pearson r | Spearman r |
|---|---|---|
| JABr | 0.87 | (similar) |
| GABr | 0.58 | 0.70 |
| AABr | 0.15 | 0.48 |
| JABr_4arm | 0.81 | 0.88 |
| Tornado | 0.17 | 0.17 |

GABr, AABr, JABr_4arm have meaningful rank-order signal that Pearson hides via outliers. Validates isotonic as the right calibration family (it monotone-maps ranks). Tornado has no signal on either metric — calibration there is essentially a constant offset.

## Known Limitations

- Calibration tables are built per construct from in-sample fits. For new constructs without a fit, **no calibration applies** (returns raw PC).
- Reference PC is itself a manual measurement; absolute floor is unknown (estimated 5-15% based on industry norms for biological image quantification).
- Mask quality on the worst cells (e.g. Sample1_1_1 wrong-cell, Sample3_3_11 bright-core undersampled) is the root limiter — calibration cannot fix segmentation failures.
- All current calibration assumes a single scalar adjustment. A *spatial* calibration (per-cell features → per-cell offset) hasn't been tested.

## See Also
- [[JABr Experiments]] — full LOO-CV result tables
- [[Cross-Construct Performance]] — V1 5-construct calibration strategies
- [[Spot Detection]] — blob_log threshold sweep
- [[Model Variants]] — model lineage
- [[Pipeline Mechanics]] — where calibration lives in the inference flow
