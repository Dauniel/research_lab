# Model Variants & Versions

Every condensate-segmentation model we've trained or tried, in order. The nuclei pass uses built-in Cellpose `cyto3` throughout — only the condensate model and its post-processing change between versions.

## Cellpose 3 Lineage

### Old Cellpose (Winter 2026 baseline)
- `cyto2`, 2D slice-by-slice, no denoising
- JABr region 2_5_1 PC = **2.04** (ref 6.32)
- Discontinued. Three things fixed it: cyto3 vs cyto2, do_3D=True, DenoiseModel preprocessing.

### V1 — `cyto3` built-in + `cond_cyto3_resume`
- First Spring 2026 fine-tune. Trained from `cyto3` for 125 epochs on the full 663-volume / 24-construct manifest.
- Checkpoints: `cond_cyto3_epoch_0025`, `cond_cyto3_resume`, `cond_cyto3_resume_epoch_{25, 50, 75, 100}`.
- **JABr LOO-honest result (with isotonic cal):** r=0.90, MAE 15.6%, 69% within ±20%
- Other constructs degraded badly — see [[Cross-Construct Performance]]. Tornado (only true held-out construct) dropped *below* the cyto3 baseline. Overfitting signature.

### V2 — `cond_cyto3_v2_clean`
- Cleaned manifest (542 vols, drops two outlier constructs + per-construct vpi outliers)
- Halted at epoch 20 — short-lived; results never published. Superseded by V3's balancing approach.

### V3 — `cond_cyto3_v3_balanced` (current production Cellpose model)
- **Motivation:** V1's training voxels were 17.4% GwtBr while the 4 main targets combined were only 7%. Balance the training distribution rather than just clean it.
- Flag: `--balance-constructs --balance-cap 700` (22 constructs × 700 slices each, 15,400 total)
- Trained from `cyto3`. Loss plateaued by epoch ~20-30; stopped at epoch 35.
- Checkpoints saved every 5 epochs: `cond_cyto3_v3_balanced_epoch_{05, 10, 15, 20, 25, 30, 35}`.
- **Production checkpoint:** `cond_cyto3_v3_balanced_epoch_0035`
- Inference flags: `--cond-cellprob -2.0 --cond-topx 75`
- **JABr LOO-honest (isotonic cal):** ~19.8% MAE. The widely-quoted 9.5% number was in-sample only.
- **JABr in-sample (isotonic cal):** 9.5% (do not cite this in writeups — overfit)
- **Sample 2_5 condensate count:** V3 stays 9-60 per cell vs Cellpose cyto3's 5-280. V3 over-segments much less than cyto3 even when raw PC is similar.

## What V1 vs V3 Actually Changed
- Same pretrained base (`cyto3`)
- Same dataset (cleaned manifest)
- Different sampling: V3 upsamples small-condensate constructs to match large-condensate ones, removing the gradient bias
- Result on JABr: roughly comparable accuracy
- Result expected on GABr / AABr (under-represented in V1): V3 should improve — **not yet measured**

## Alternative Architectures (April model survey, single-sample baselines)
All on JABr region 2_5_1, defaults, no calibration:

| Model | PC | n_cond | Notes |
|---|---|---|---|
| Old Cellpose (cyto2, 2D) | 2.04 | — | Winter baseline |
| **Cellpose 3 (cyto3, 3D)** | **3.33** | — | Adopted as pipeline backbone |
| StarDist 2D (versatile_fluo) | 1.91 | — | Trained on cell nuclei, wrong target |
| U-FISH (ONNX spot) | 3.81 | — | Spot detector + Otsu nuclei — caveat, different nuclear mask |
| Nellie (Frangi + graph) | 3.57 | — | Tubular-organelle library, off-target |
| Reference (Imaris/manual) | 6.32 | — | Ground truth |

Decisional outcome (2026-04-22): Cellpose 3 wins on principled grounds; the gap to ref 6.32 was later closed by the pipeline fixes documented in [[Pipeline Mechanics]] (background subtraction, top-X%, connected-component nuclei, etc.), not by switching models.

## Spot Detector (2026-05-19, current JABr best)
- **`blob_log`** — Laplacian-of-Gaussian via `skimage.feature.blob_log` (classical 3D blob detection, not a learned model)
- Uses Cellpose V3 nuclei masks unchanged; only condensate detection swaps
- **JABr LOO-honest (linear cal, threshold=0.03):** **14.7% MAE** — current best on JABr
- **GABr LOO-honest (preliminary):** MAE 114.8%, r=0.57 — **does not generalize** with the same threshold
- See [[Spot Detection]]

## Production Choices by Construct (post 2026-05-19 head-to-head)

| Construct | Production model | Best calibration | LOO-CV MAE |
|---|---|---|---|
| **JABr** | blob_log (thresh=0.03) | linear | **14.7%** |
| JABr_4arm | Cellpose V3 epoch 35 | linear | **29.8%** |
| Tornado | Cellpose V3 epoch 35 | linear | **23.7%** (low signal, r=0.19) |
| GABr | Cellpose V3 epoch 35 | isotonic | 57.3% |
| AABr | Cellpose V3 epoch 35 | isotonic | 58.0% |
| Everything else | Cellpose V3 (untested) | none yet | — |

Calibration tables for GABr/AABr/JABr_4arm/Tornado V3 outputs need to be added to `calibration_table.json` (currently only JABr is fit).

## See Also
- [[Training Pipeline]] — how the V3 model was trained
- [[Cross-Construct Performance]] — V1's 5-construct results + label inconsistency diagnosis
- [[Calibration]] — calibration tables + LOO-CV methodology
- [[Pipeline Mechanics]] — what runs at inference for any of these models
- [[JABr Experiments]] — empirical head-to-head
- [[Spot Detection]] — blob_log mechanics
