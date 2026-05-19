# Spot Detection (`blob_log`)

Classical 3D blob detection as an alternative to Cellpose for condensates. Bright, round, sub-resolution puncta are exactly what `skimage.feature.blob_log` (multi-scale Laplacian of Gaussian) was designed for.

## Why this works better than Cellpose on JABr

Cellpose is a semantic-segmentation network trained on cells and nuclei (filled, irregular, µm-scale). Forcing it to segment ~hundreds-of-nm puncta produces fragmented masks with dim halo voxels — the model wants to outline objects, not detect points. `blob_log` directly searches for local intensity maxima at multiple scales, which is the native operation for puncta.

The Imaris ground truth itself uses surface/spot detection (not segmentation), so we're aligning the method to the GT methodology.

## Algorithm

For each ROI:
1. Compute camera background `B = cond_stack.min()`
2. Background-subtract, normalize to [0,1]
3. `blob_log(norm, min_sigma=1.5, max_sigma=6.0, num_sigma=8, threshold=T, overlap=0.5)` → list of `(z, y, x, σ)`
4. Keep blobs whose centroid lies inside the nuclei mask
5. Render each blob as a sphere of radius `r = σ·√3` to build an integer instance mask
6. Feed mask + original `cond_stack` to the existing `compute_partition_coefficient()` (with `cond_topx=75`)

Nuclei are still segmented by Cellpose V3 (`cyto3`, cellprob=−2.0) plus connected-component relabeling — only condensate detection changed.

## Threshold Choice

LOO-CV on JABr (n=29 cells, linear cal):

| Threshold | Raw MAE | Linear cal MAE | Mean n_cond | Pearson r |
|---|---|---|---|---|
| 0.02 | 54.7% | 14.9% | **16.5** (GT≈16) | **0.938** |
| **0.03** | 75.3% | **14.7%** | 9.8 | 0.926 |
| 0.04 | 82.1% | 15.3% | 7.4 | 0.924 |
| 0.05 | 88.8% | 15.6% | 5.4 | 0.922 |

Raw MAE is bad at every threshold (~55–90%) because blob_log systematically over-estimates PC — fewer detected blobs means the surviving ones are the brightest, so the top-X% intensity average inside their spheres is inflated. After linear calibration, all thresholds collapse to 14.7–15.6%.

- **`0.03`** chosen as production: lowest LOO-CV MAE
- `0.02` worth considering: highest correlation, best n_cond match to GT (would matter if downstream code cares about per-condensate stats, not just PC)

## Sigma Range

`min_sigma=1.5, max_sigma=6.0` covers a condensate radius range of roughly √3·1.5 ≈ 2.6 to √3·6 ≈ 10.4 voxels. Tuned by single-image inspection on 2_5_1; not swept yet.

## Script

`spring_implementation/batch_blob_log.py`

```
python batch_blob_log.py \
    --construct-dir "C:/Users/Danie/Box/Condensate Volume Quantification/JABr" \
    --output outputs/blob_JABr_thresh03 \
    --blob-threshold 0.03 \
    --cond-topx 75
```

Flags: `--blob-threshold`, `--min-sigma`, `--max-sigma`, `--num-sigma`, `--nuc-cellprob`, `--cond-topx`.

## What's Not Yet Tested

- Anisotropic sigma — z step is larger than xy in the source stacks; current code uses isotropic σ
- Sub-voxel intensity integration — currently uses rendered-sphere voxels; could integrate the analytic LoG response at the detected center
- Cross-construct: only run on JABr so far
- Sphere radius factor — `σ·√3` is the geometric "characteristic radius" but the visible condensate may be larger/smaller

## See Also
- [[JABr Experiments]] — head-to-head with Cellpose
- [[Model Variants]] — full model lineage
- [[Calibration]] — calibration methodology
