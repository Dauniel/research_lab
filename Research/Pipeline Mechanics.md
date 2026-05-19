# Pipeline Mechanics

How `spring_implementation/pipeline.py` turns a 3D fluorescence stack into a partition coefficient. This page explains each component, why it exists, and the version that fixed each problem.

## Inputs

- **Condensate channel** (Ch2): Z-stack TIF, e.g. `data/raw_condensates/C2-*.tif`
- **Nuclei channel** (Ch1): Z-stack TIF, e.g. `data/raw_nuclei/C1-*.tif`
- Or **multi-channel ROI** via `--roi`: shape `(Z, 2, Y, X)` from Box `Cut ROI/`
- Optional voxel sizes for µm-scale volumes (`--voxel-xy`, `--voxel-z`)

## Six Steps

### 1. Load
Reads TIFs; supports OME-TIFF axis re-ordering since 2026-05-07. Splits into nuclei + condensate stacks.

### 2. Denoise
`Cellpose 3 DenoiseModel(cyto3)` on every Z-slice, *both* channels. Sharpens boundaries without modifying raw intensity values — PC computations always use the original pixel values, denoising only guides where mask edges land.

### 3. Segment
- **Condensates**: Cellpose 3, `do_3D=True`. Default model `cyto3`, swappable via `--cond-model <path>`. The current production model is `cond_cyto3_v3_balanced_epoch_0035`. `--cond-cellprob` defaults to `-2.0` for V3 (it picks up dim condensates the default 0.0 would discard).
- **Nuclei**: Cellpose 3 `cyto3`, `do_3D=True`, `--nuc-cellprob -2.0`. The instance labels are post-processed by a **connected-component relabel + size filter** (see below) — Cellpose splits each true nucleus into ~15–25 fragments because of internal condensate texture in the aptamer signal, so we collapse the binary mask into 3D connected components and drop fragments <1000 voxels. Typical result: 5 clean nuclei from 76 raw Cellpose labels, with ~99.97% of binary coverage preserved.

### 4. Per-slice regionprops
`skimage.measure.regionprops_table` for area / centroid / mean intensity per (label, Z-slice).

### 5. 3D volume
Sum voxels per label across all slices; convert to µm³ if voxel sizes supplied.

### 6. Partition Coefficient — the Fabrini formula

From the Fabrini et al. manuscript, section 1.8.4. Three terms:

- **Background `B`** = `cond_stack.min()` (minimum voxel across the full FOV). Removes camera offset.
- **Condensed density**:
  ```
  cond_density = mean( clip(pixel − B, 0) )
                 over the top‑X% brightest voxels in (cond_mask ∩ nuc_mask)
  ```
  Top-X% trimming is the `--cond-topx` flag (default 75 for Cellpose). It removes the dim halo voxels Cellpose adds beyond the true condensate boundary. **Important caveat**: top-X% was calibrated for *Cellpose* masks, which are loose. The newer `blob_log` masks (see [[Spot Detection]]) are tighter and the same X may over-amplify — needs re-tuning per detector.
- **Dilute density**:
  ```
  dil_density  = mean( clip(pixel − B, 0) )
                 over the 50 lowest-intensity valid 10×10×10 patches
                 fully inside (nuc_mask ∧ ¬cond_mask)
  ```
  Lowest-50 sort mimics how an analyst manually picks "a quiet representative spot" in the dilute phase. Deterministic (no seed), stable, biologically grounded.

```
PC = cond_density / dil_density
```

### Optional: Calibration
If `--construct NAME` is set and `NAME` is in `outputs/calibration_table.json`:
- `kind: linear` → `pc_cal = slope · pc + intercept`
- `kind: isotonic` → `pc_cal = np.interp(pc, xs, ys)`
Calibrated PC and construct are written to `summary.csv` alongside the raw value.

## Outputs (per `--output` dir)

```
cond_restored.tif        denoised condensate stack
nuc_restored.tif         denoised nuclei stack
condensate_masks.tif     3D instance labels (condensates)
nuclei_masks.tif         3D instance labels (nuclei, post-relabel)
condensate_measurements.csv  per-(label, Z) regionprops
nuclei_measurements.csv      per-(label, Z) regionprops
condensate_volumes.csv   3D voxel count per label
nuclei_volumes.csv       3D voxel count per label
summary.csv              PC + dens + B + counts + (pc_calibrated, construct)
results.png              4-panel figure: raw, masks, distributions, density bars
```

## Improvements That Built the Current PC Accuracy

These are the actual moves that took JABr-region-2_5_1 PC from 2.04 → ~6.30 (matching ref 6.32). Anyone touching `pipeline.py` should know all four:

1. **Background subtraction** (2026-04-25). Reference uses `clip(pixel − B, 0)` everywhere; we weren't. Single largest single jump in PC.
2. **3D mode** (`do_3D=True`, 2026-04-22). Replaces slice-by-slice Cellpose; XY/XZ/YZ gradient flows are merged before drawing boundaries. Critical for objects spanning >1 Z-slice.
3. **Connected-component nuclei relabel** (2026-04-30). 76 Cellpose labels → 5 connected regions. Fixes which voxels count as "nuclear" without changing what's labelled as condensate.
4. **Lowest-50-patch dilute density** (2026-04-30). Previously single-patch + RNG-seed dependent — PC swung 4.3 to 6.0 across seeds. Determinism + biological match in one fix.
5. **Top-X% condensate trim** (2026-05-05). cyto3 mask = bright core + dim halo + dark interior. Mean over all mask voxels under-counts the bright cores. Top-75% recovers the manual reference density. Sweep confirmed `cond_topx=75` is the sweet spot for cyto3 masks; expect different optima for tighter masks.

## What Doesn't Help (tested, ruled out)

- **`--nuc-diameter` fixed to 60 px**: shattered nuclei into ~33 pieces. Always use `None` (auto-detect).
- **Cellpose `nuclei` model for nuclei**: trained on clean DAPI/Hoechst; gets confused by aptamer signal with internal texture. Stick with `cyto3` for both channels.
- **`--cond-cellprob` tuning beyond −2.0**: changes count but inversely tracks PC — fewer detections leaves the brightest, raising PC instead of lowering it. Wrong knob.
- **Adaptive top-X% per cell**: no single value fits all cells; per-cell tuning would need a mask-quality scorer that doesn't exist yet.

## See Also
- [[Model Variants]] — what `--cond-model` can point at
- [[Calibration]] — `--construct` flag + table format
- [[JABr Experiments]] — empirical accuracy
- [[Spot Detection]] — alternative condensate detector (`batch_blob_log.py`)
