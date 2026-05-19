# Cross-Construct Performance

The hard test for any model: does accuracy on JABr (the training-dominant construct) transfer to other RNA scaffolds?

## V1 (cyto3-resume, May 16, ~100 epochs) — Five-Construct Comparison

LOO-honest, per-construct isotonic calibration. From `outputs/calibration_summary.csv`.

| Construct | n | r_raw | r_best | MAE_best | within ±20% | Strategy |
|---|---|---|---|---|---|---|
| JABr | 29 | 0.87 | 0.90 | 15.6% | 69% | mix(0.85·trained + 0.15·cyto3) + isotonic |
| GABr | 29 | 0.58 | 0.55 | 59% | 35% | trained + isotonic |
| AABr | 25 | 0.15 | 0.45 | 57% | 44% | trained + isotonic |
| JABr_4arm | 37 | 0.81 | 0.79 | 30% | 49% | trained + isotonic |
| Tornado* | 18 | 0.17 | 0.13 | 22% | 50% | cyto3 + isotonic |

*Tornado is the only construct NEVER in training — true held-out.

**Pattern:** V1 memorized JABr (which dominated the training mix) and degraded sharply on every other construct, including ones it was nominally trained on. Tornado dropped *below* the cyto3 baseline (r=0.13 trained vs r=0.23 cyto3), the canonical overfitting signature.

## Diagnosed Root Cause: Label Inconsistency

Across the 24 training constructs, **median voxels-per-condensate-instance spans 42 (15ntEMango) to 1840 (GwtBr) — a >40× cross-construct range**. Within a single construct (JABr_4arm) the coefficient of variation is 1.15, meaning instance sizes vary 30× from cell to cell. The model effectively learned ~24 different definitions of "condensate" and can't reconcile them at inference.

Cellprob_threshold sweeps, diameter sweeps, and post-hoc calibration cannot fix this — it's a data problem.

## V3 Response: Construct-Balanced Training

V3 (`cond_cyto3_v3_balanced`) was launched specifically to address the imbalance: V1's training voxels were dominated by GwtBr (17.4%) while the 4 target constructs (JABr + GABr + AABr + JABr_4arm) combined were only 7%. V3 upsamples underrepresented constructs to equal slice count (`--balance-constructs --balance-cap 700`).

- Stopped at epoch 35 (loss plateaued by ~20).
- Tested on JABr only as of 2026-05-18: raw MAE 21.2%, in-sample isotonic 9.5%, **LOO-CV isotonic 19.8%**.
- Cross-construct V3 evaluation **not yet run** (the natural follow-up the V3 retrain was supposed to enable).

## blob_log Cross-Construct Test (2026-05-19, complete)

`batch_blob_log.py --blob-threshold 0.03 --cond-topx 75`, LOO-CV out-of-sample:

| Construct | n | Raw MAE | Linear cal | Isotonic cal | r | mean n_cond |
|---|---|---|---|---|---|---|
| **JABr** | 28 | 75% | **14.7%** | 14.8% | **0.926** | 9.8 |
| JABr_4arm | 37 | 89% | 38.7% | 40.9% | 0.803 | 8.6 |
| Tornado* | 18 | 118% | 23.6% | 23.6% | 0.213 | 100.7 |
| GABr | 29 | 115% | 77.8% | 69.2% | 0.570 | 15.3 |
| AABr | 25 | 188% | 78.9% | 58.3% | 0.121 | 21.4 |

*Tornado's low MAE is misleading: reference PCs are small and clustered, so a near-constant calibrated prediction lands near the mean despite r=0.21 (no real signal).

**Verdict: blob_log does not generalize.** JABr (r=0.93) and to a lesser extent JABr_4arm (r=0.80) — both Broccoli-family scaffolds — rank-correlate reasonably. GABr / AABr / Tornado have weak-to-zero signal. Tornado's `mean n_cond ≈ 100` (vs 8–21 elsewhere) suggests sigma range / threshold are wrong for that construct's condensate morphology.

## Cellpose V3 Cross-Construct Test (2026-05-19, complete)

`batch_compare.py --cond-model cond_cyto3_v3_balanced_epoch_0035 --cond-cellprob -2.0 --cond-topx 75`, LOO-CV out-of-sample:

| Construct | n | Raw MAE | Linear cal | Isotonic cal | r |
|---|---|---|---|---|---|
| JABr | 29 | 40.1% | 22.2% | **18.1%** | 0.865 |
| JABr_4arm | 37 | 70.3% | **29.8%** | 32.5% | 0.874 |
| GABr | 29 | 76.7% | 61.8% | **57.3%** | 0.654 |
| AABr | 25 | 178.0% | 76.4% | **58.0%** | 0.171 |
| Tornado | 18 | 184.1% | **23.7%** | 24.5% | 0.190 |

Outputs under `outputs/experiments/batch_<construct>_v3_epoch35/`.

## Head-to-Head: blob_log vs Cellpose V3

LOO-CV honest, best calibration per cell:

| Construct | blob_log best | V3 best | Winner |
|---|---|---|---|
| **JABr** | **14.7%** (linear, r=0.93) | 18.1% (iso, r=0.87) | **blob_log** |
| JABr_4arm | 38.7% (linear, r=0.80) | **29.8%** (linear, r=0.87) | **V3** |
| GABr | 69.2% (iso, r=0.57) | **57.3%** (iso, r=0.65) | **V3** |
| AABr | 58.3% (iso, r=0.12) | **58.0%** (iso, r=0.17) | V3 (barely) |
| Tornado | **23.6%** (linear, r=0.21) | 23.7% (linear, r=0.19) | tie |

V3 wins or ties on every construct except JABr. blob_log's specialty is JABr only.

## Recommended Production Strategy

**Hybrid pipeline routed by `--construct NAME`:**
- `JABr` → blob_log (thresh=0.03) + linear calibration (14.7% MAE)
- All other constructs → Cellpose V3 epoch 35 + per-construct calibration (linear for JABr_4arm/Tornado, isotonic for GABr/AABr)
- Tornado and AABr are not "solved" — they hit a floor around 24% / 58% MAE that's likely labeling-quality limited

This requires building per-construct calibration entries in `calibration_table.json` for GABr / AABr / JABr_4arm / Tornado from the V3 outputs (single LOO-CV fit per construct using `analyze_calibration.py` or equivalent).

## Implications

- **JABr-specific production:** blob_log + linear cal (14.7% MAE) stays best.
- **Multi-construct production:** Cellpose V3 + per-construct calibration is the only path. blob_log can't carry the load.
- **Strategic question for the report/paper:** is the goal a single-construct showcase (JABr at 14.7%) or a multi-construct generalist? The two have different best models.
- **Hybrid pipeline option:** `--construct NAME` routes to the right detector. JABr → blob_log; everything else → V3.

## Implications

- **JABr-specific production:** blob_log + linear cal (14.7% MAE) stays best.
- **Multi-construct production:** Cellpose V3 + per-construct calibration is the only path. blob_log can't carry the load.
- **Strategic question for the report/paper:** is the goal a single-construct showcase (JABr at 14.7%) or a multi-construct generalist? The two have different best models.
- **Hybrid pipeline option:** `--construct NAME` could route to the right detector. JABr → blob_log; everything else → V3.

## See Also
- [[Spot Detection]] — blob_log mechanics + JABr threshold sweep
- [[Model Variants]] — V1 / V2 / V3 lineage
- [[Training Pipeline]] — voxel-imbalance diagnosis + construct balancing flags
- [[Calibration]] — calibration table format
