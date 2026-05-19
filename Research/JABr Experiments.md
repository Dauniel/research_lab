# JABr Experiments

JABr is the primary target construct and the only one with enough cells (n=29 nuclear) to do meaningful evaluation. All MAE numbers below are **LOO-CV out-of-sample** unless noted.

## Headline Result (2026-05-19)

**Best honest MAE: 14.7% — blob_log (thresh=0.03) + linear calibration.**

| Method | Calibration | LOO-CV MAE | Pearson r |
|---|---|---|---|
| Cellpose V3 epoch 35 | linear | 21.7% | ~0.85 |
| Cellpose V3 epoch 35 | isotonic | 19.8% | ~0.85 |
| blob_log (thresh=0.02) | linear | 14.9% | **0.938** |
| **blob_log (thresh=0.03)** | **linear** | **14.7%** | 0.926 |
| blob_log (thresh=0.04) | linear | 15.3% | 0.924 |
| blob_log (thresh=0.05) | linear | 15.6% | 0.922 |
| Ensemble (0.81·blob + 0.19·CP) | isotonic | 14.3% | — |

Caveats:
- "In-sample" calibration numbers (e.g. 9.5% for Cellpose, 6.8% for blob_log) overfit because isotonic regression has n_segments = n_cells. Reported numbers above are LOO-CV.
- The ensemble (~14.3%) is within noise of single-model blob_log; not worth the complexity for now.
- All blob_log runs use identical nuclei segmentation (Cellpose `cyto3` + connected-component relabel).

## Region 2_5_1 — Detailed Look

GT: PC=6.324 (from `JABr_Partition coefficient_nuclear.csv`), **16 or 25 condensates depending on source** (see GT discrepancy note below), 2 transfected cells in the field. PC is computed as a single aggregate over the ROI — multi-cell ROIs are merged into one PC measurement.

**GT condensate count discrepancy:** Earlier Imaris count `Statistics-cleaned/inside/*_inside.xls` Detailed sheet had 16 rows for 2_5_1. The 2026-05-18 progress log table reports 25 (likely from `Statistics/inside`, the un-cleaned version). The "cleaned" stats may exclude small or edge-of-nucleus surfaces. Worth confirming which source the published Imaris analysis used before quoting per-condensate counts in any writeup.

| Run | n_cond | PC raw | PC cal | err vs GT PC |
|---|---|---|---|---|
| Cellpose V3 epoch 35 + isotonic | 38 | 10.49 | 8.24 | +30% |
| **blob_log thresh=0.03** | **18** | 8.38 | 5.93* | −6% |
| cyto3 baseline + topx=100 | 186 | 6.30 | — | −0.4% (lucky cancellation; 186 over-segments) |

*2_5_1 blob_log calibrated value used the JABr isotonic table — the calibration was tuned on this same data, so the −6% number is in-sample for this ROI.

## Cellprob Sweep (Cellpose V3, region 2_5_1)
| cellprob | n_cond | PC raw |
|---|---|---|
| −2.0 (production) | 38 | 10.49 |
| −1.0 | 36 | 10.95 |
| 0.0 | 34 | 11.39 |
| 1.0 | 29 | 11.84 |

Raising cellprob trades count vs PC in the wrong direction — fewer faint detections survive, but the surviving ones are brighter, so PC goes up while count goes down. cellprob is the wrong knob for Cellpose over-segmentation. Outputs: `outputs/cellprob_sweep_2_5_1/`

## Sample 2_5 Family — GT vs Pipeline (Cellpose V3, May 18 sweep)

Per-cell `cyto3` baseline vs V3 epoch 35 (raw, no calibration). From `progress_log.txt` 2026-05-18.

| Sample | Ref PC | GT cond | GT nuc | cyto3 PC (n_cond) | V3 raw PC (n_cond) |
|---|---|---|---|---|---|
| 2_5_1 | 6.324 | 25 | 2 | 6.61 (n=70) +4.5% | 9.00 (n=38) +42.3% |
| 2_5_2 | 6.873 | 10 | 1 | 7.74 (n=5) +12.7% | 7.88 (n=9) +14.7% |
| 2_5_3 | 4.558 | 18 | 1 | 6.63 (n=20) +45.3% | 5.70 (n=16) +25.0% |
| 2_5_4 | 6.020 | 15 | 2 | 4.38 (n=47) −27.2% | 6.46 (n=16) +7.3% |
| 2_5_5 | 6.728 | 43 | 5 | 6.55 (n=280) −2.6% | 9.02 (n=60) +34.1% |
| 2_5_6 | 12.151 | 21 | 2 | 8.33 (n=99) −31.4% | 12.59 (n=23) +3.6% |
| **MAE** |  |  |  | **20.6%** | **21.2%** |

V3 dramatically reduces count over-segmentation (5–60 per cell vs cyto3's 5–280) but raw PC is no better than cyto3. The win for V3 only appears with V3-specific calibration, and even then only in-sample.

## Ground Truth Sources (Box)

- **Cell count:** `JABr/Cell Number/JABr.xlsx`
- **Per-condensate surfaces:** `JABr/Statistics-cleaned/inside/*_inside.xls` (Imaris Detailed sheet; one row per surface)
- **Per-ROI PC table:** `JABr/JABr_Partition coefficient_nuclear.csv` (n=30 with 2_5_1 = 6.324)
- **Imaris source files:** `JABr/Imaris file/*.ims`

Note: "Cell number" is bookkeeping (cells in the field), not per-cell PC. The PC CSV has one row per ROI, regardless of cell count — multi-cell ROIs are aggregated into a single PC measurement.

## Skipped ROIs (in Cut ROI/ but not in PC CSV)
Sample1_2_4, Sample1_4_5/6/7/8, Sample2_1_1/2/3/4, Sample2_2_1, Sample3_3_12/13. These were excluded by the analyst (often "no transfected cell").

## Outputs of Interest
- `outputs/experiments/batch_JABr_trained_v3_epoch35/comparison.csv` — Cellpose V3 batch result
- `outputs/blob_JABr_thresh{002,03,004,005}/comparison.csv` — blob_log threshold sweep
- `outputs/cellprob_sweep_2_5_1/cp{−2,−1,0,1}/` — single-ROI cellprob sweep

## Bad Cases (May 14 diagnostic, V1 model)

Five cells consistently fail across model versions. Root causes traced via `diagnose_cell.py`:

| Sample | Ref | V1 PC | Error | Root cause |
|---|---|---|---|---|
| Sample1_1_1 | 4.78 | 11.77 | +146% | Mask too loose; dilute peak = 1214 (should be ~82) — halo bleed |
| Sample3_3_2 | 9.05 | 4.47 | −51% | Condensates undersampled; mask missing real ones |
| Sample3_3_11 | 16.95 | 10.57 | −38% | Bright cores undersampled; top-25% recovers ref but top-75% doesn't |
| Sample2_5_5 | 6.73 | 4.20 | −38% | Wide FOV (32×417×370); target cell's nucleus never segmented |
| Sample3_3_15 | 6.41 | NaN | n/a | Central nucleus has zero condensate overlap; fixed by max-overlap heuristic |

Max-overlap nucleus heuristic only fixed Sample3_3_15. For the other 4, nucleus selection was already correct — failures are mask-quality, not nucleus-selection.

## Open Questions
- Does blob_log's lead hold on other constructs? (In progress 2026-05-19. GABr first result: r=0.57, MAE 115% — does **not** generalize.)
- Would a *spatial* calibration (per-cell features → PC offset) beat the current scalar?
- The 14.7% floor — is it segmentation-limited or reference-noise-limited? Worth re-doing Imaris on a subset to estimate measurement noise.
- Which Imaris stats version (`Statistics/` vs `Statistics-cleaned/`) did the lab's published PC analysis use? Affects all GT condensate counts.

## See Also
- [[Spot Detection]] — blob_log mechanics + threshold sweep
- [[Calibration]] — calibration methodology
- [[Cross-Construct Performance]] — V1 5-construct results + label inconsistency diagnosis
- [[Pipeline Mechanics]] — what runs internally for each PC computation
- [[Model Variants]] — model lineage
- [[reference_data/JABr Reference Data]] — raw reference numbers
