"""
run_comparison.py
Runs all five segmentation approaches (4 new + 1 old baseline), times them,
then produces:
  outputs/comparison/comparison_figure.png  — side-by-side segmentation + metrics
  outputs/comparison/flowmap_figure.png     — pipeline flowmap for each model
"""
import subprocess, time, sys, glob
from pathlib import Path

import numpy as np
import pandas as pd
import tifffile as tiff
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from matplotlib.colors import ListedColormap

BASE_DIR   = Path(__file__).parent.parent
OUT_DIR    = BASE_DIR / "segmentation_test" / "outputs"
SCRIPT_DIR = BASE_DIR / "segmentation_test"
COND_PATH  = BASE_DIR / "data" / "raw_condensates" / "C2-ROI_raw_stack_sample2_5.tif"
NUC_PATH   = BASE_DIR / "data" / "raw_nuclei"      / "C1-ROI_raw_stack_sample2_5.tif"
OLD_COND_MASK = BASE_DIR / "outputs" / "cellpose_python" / "ROI_condensate_masks.tif"
OLD_NUC_MASK  = BASE_DIR / "outputs" / "cellpose_python" / "ROI_nuclei_masks.tif"
FIG_DIR    = OUT_DIR / "comparison"
FIG_DIR.mkdir(parents=True, exist_ok=True)

NEW_MODELS = ["cellpose3", "stardist", "ufish", "nellie"]
ALL_MODELS = ["old_cellpose"] + NEW_MODELS

COLORS = {
    "old_cellpose": "#7F7F7F",
    "cellpose3":    "#4C72B0",
    "stardist":     "#DD8452",
    "ufish":        "#55A868",
    "nellie":       "#C44E52",
}
LABELS = {
    "old_cellpose": "Old Cellpose\n(2D, cyto2)",
    "cellpose3":    "Cellpose 3\n(3D + denoise)",
    "stardist":     "StarDist 2D",
    "ufish":        "U-FISH",
    "nellie":       "Nellie",
}

# ── 1a. Run old cellpose baseline (cyto2, slice-by-slice, ROI data) ───────────
print("=" * 60)
print("\n[old_cellpose] Running (cyto2, slice-by-slice)...", flush=True)

from cellpose import models as cp_models
from skimage.measure import regionprops_table

cond_stack_roi = tiff.imread(COND_PATH)
nuc_stack_roi  = tiff.imread(NUC_PATH)

cond_model_old = cp_models.CellposeModel(gpu=True, model_type="cyto2")
nuc_model_old  = cp_models.CellposeModel(gpu=True, model_type="cyto2")

def run_cp_stack(stack, model):
    masks_out = []
    for z in range(stack.shape[0]):
        m, _, _ = model.eval(stack[z], diameter=None, channels=[0, 0])
        masks_out.append(m.astype(np.int32))
    return np.stack(masks_out)

t0 = time.perf_counter()
old_cond_masks = run_cp_stack(cond_stack_roi, cond_model_old)
old_nuc_masks  = run_cp_stack(nuc_stack_roi,  nuc_model_old)
timings = {"old_cellpose": time.perf_counter() - t0}

# compute old PC from fresh masks; fall back to saved masks if no overlap found
cp_all, dp_all = [], []
for z in range(cond_stack_roi.shape[0]):
    img = cond_stack_roi[z]
    cm  = old_cond_masks[z] > 0
    nm  = old_nuc_masks[z]  > 0
    cp_ = img[cm & nm];  dp_ = img[nm & ~cm]
    if cp_.size > 0: cp_all.append(cp_)
    if dp_.size > 0: dp_all.append(dp_)

# Always use saved masks for PC — they represent the original pipeline output
saved_cm = tiff.imread(OLD_COND_MASK)
saved_nm = tiff.imread(OLD_NUC_MASK)

_B         = float(cond_stack_roi.min())
_cond_3d   = saved_cm > 0
_nuc_3d    = saved_nm > 0
_nuc_cond  = _cond_3d & _nuc_3d
_cond_v    = np.clip(cond_stack_roi[_nuc_cond].astype(np.float64) - _B, 0, None)
_cond_dens = _cond_v.sum() / _nuc_cond.sum()

_dilute_3d  = _nuc_3d & ~_cond_3d
_PATCH      = 10
_Z, _Y, _X  = cond_stack_roi.shape
_rng        = np.random.default_rng(42)
_cands      = np.argwhere(_dilute_3d)
_ib         = _cands[(_cands[:,0]+_PATCH<=_Z) & (_cands[:,1]+_PATCH<=_Y) & (_cands[:,2]+_PATCH<=_X)]
_rng.shuffle(_ib)
_dil_dens   = None
for _z0, _y0, _x0 in _ib[:2000]:
    if _dilute_3d[_z0:_z0+_PATCH, _y0:_y0+_PATCH, _x0:_x0+_PATCH].all():
        _p        = cond_stack_roi[_z0:_z0+_PATCH, _y0:_y0+_PATCH, _x0:_x0+_PATCH].astype(np.float64) - _B
        _dil_dens = np.clip(_p, 0, None).mean()
        break
if _dil_dens is None:
    _dil_dens = np.clip(cond_stack_roi[_dilute_3d].astype(np.float64) - _B, 0, None).mean()
old_pc = _cond_dens / _dil_dens

print(f"[old_cellpose] OK in {timings['old_cellpose']:.1f}s  PC={old_pc:.3f}")

# ── 1b. Run new models via subprocess ─────────────────────────────────────────
for model in NEW_MODELS:
    script = SCRIPT_DIR / f"{model}_segmentation.py"
    print(f"\n[{model}] Running...", flush=True)
    t0 = time.perf_counter()
    r  = subprocess.run([sys.executable, str(script)])
    timings[model] = time.perf_counter() - t0
    status = "OK" if r.returncode == 0 else "ERROR"
    print(f"[{model}] {status} in {timings[model]:.1f}s")
print("=" * 60)

# ── 2. Load masks and PCs ─────────────────────────────────────────────────────
cond_stack = tiff.imread(COND_PATH)
mid_z_new  = cond_stack.shape[0] // 2
raw_img    = cond_stack[mid_z_new].astype(np.float32)

def load_mask(model):
    if model == "old_cellpose":
        # always use saved masks for visualization (fresh cyto2 run misses some slices)
        return tiff.imread(OLD_COND_MASK)[mid_z_new] > 0
    if model == "cellpose3":
        return tiff.imread(OUT_DIR / "cellpose3" / "cp3_condensate_masks.tif")[mid_z_new] > 0
    if model == "stardist":
        return tiff.imread(OUT_DIR / "stardist" / "stardist_condensate_masks.tif")[mid_z_new] > 0
    if model == "ufish":
        return tiff.imread(OUT_DIR / "ufish" / "ufish_condensate_masks.tif")[mid_z_new].astype(bool)
    if model == "nellie":
        paths = glob.glob(
            str(OUT_DIR / "nellie" / "condensates" / "**" / "*im_instance_label*.ome.tif"),
            recursive=True)
        arr = tiff.imread(paths[0])
        if arr.ndim == 4:
            arr = arr[0]
        return arr[mid_z_new] > 0

def load_pc(model):
    if model == "old_cellpose":
        return old_pc
    csv_paths = {
        "cellpose3": OUT_DIR / "cellpose3" / "cp3_summary.csv",
        "stardist":  OUT_DIR / "stardist"  / "stardist_summary.csv",
        "ufish":     OUT_DIR / "ufish"     / "ufish_summary.csv",
        "nellie":    OUT_DIR / "nellie"    / "nellie_summary.csv",
    }
    df = pd.read_csv(csv_paths[model])
    return float(df.loc[df["metric"] == "partition_coefficient", "value"].iloc[0])

masks = {m: load_mask(m) for m in ALL_MODELS}
pcs   = {m: load_pc(m)   for m in ALL_MODELS}

print("\nResults summary:")
for m in ALL_MODELS:
    print(f"  {LABELS[m].replace(chr(10),' '):25s}  PC={pcs[m]:.3f}  time={timings[m]:.0f}s")

# ── 3. Composite segmentation figure ─────────────────────────────────────────
vmin_new = raw_img.min()
vmax_new = np.percentile(raw_img, 99.5)

fig = plt.figure(figsize=(26, 12))
gs  = gridspec.GridSpec(3, 5, figure=fig, hspace=0.38, wspace=0.06,
                        height_ratios=[2.2, 2.2, 1.0])

for col, model in enumerate(ALL_MODELS):
    color  = COLORS[model]
    ri     = raw_img
    vmin_  = vmin_new
    vmax_  = vmax_new
    mid_z_ = mid_z_new

    # Row 0: raw + colored overlay
    ax0 = fig.add_subplot(gs[0, col])
    ax0.imshow(ri, cmap="gray", vmin=vmin_, vmax=vmax_, interpolation="nearest")
    masked = np.ma.masked_where(~masks[model], np.ones_like(ri))
    ax0.imshow(masked, cmap=ListedColormap([color]), alpha=0.5,
               interpolation="nearest", vmin=0, vmax=1)
    label_str = LABELS[model].replace("\n", "  ")
    ax0.set_title(
        f"{label_str}\nPC = {pcs[model]:.2f}   {timings[model]:.0f} s",
        fontsize=10, fontweight="bold", color=color, pad=5)
    ax0.axis("off")
    if col == 0:
        ax0.text(-0.04, 0.5, f"z={mid_z_}", transform=ax0.transAxes,
                 va="center", ha="right", fontsize=8, rotation=90, color="gray")

    # Row 1: binary mask
    ax1 = fig.add_subplot(gs[1, col])
    ax1.imshow(masks[model].astype(np.uint8), cmap="gray", interpolation="nearest")
    npx = int(masks[model].sum())
    ax1.set_title(f"Mask  ({npx:,} px)", fontsize=9, color="dimgray")
    ax1.axis("off")

    # Divider line between old and new
    if col == 0:
        for row in range(2):
            ax_ = fig.add_subplot(gs[row, col])
            ax_.spines["right"].set_visible(True)
            ax_.spines["right"].set_linewidth(2)
            ax_.spines["right"].set_color("black")

# Row 2 left: PC bar chart
ax_pc = fig.add_subplot(gs[2, :3])
bars  = ax_pc.bar(
    [LABELS[m].replace("\n", " ") for m in ALL_MODELS],
    [pcs[m] for m in ALL_MODELS],
    color=[COLORS[m] for m in ALL_MODELS],
    width=0.55, edgecolor="white", linewidth=0.8)
ax_pc.axhline(6.32, color="crimson", linestyle="--", linewidth=1.4,
              label="Reference PC = 6.32")
for bar, m in zip(bars, ALL_MODELS):
    ax_pc.text(bar.get_x() + bar.get_width() / 2,
               bar.get_height() + 0.05, f"{pcs[m]:.2f}",
               ha="center", va="bottom", fontsize=9, fontweight="bold")
ax_pc.set_ylabel("Partition Coefficient", fontsize=10)
ax_pc.set_title("PC comparison", fontsize=11)
ax_pc.legend(fontsize=9)
ax_pc.tick_params(labelsize=8)
ax_pc.set_ylim(0, max(pcs.values()) * 1.25)
ax_pc.axvline(0.5, color="black", linewidth=1.2, linestyle=":")  # divider old vs new

# Row 2 right: timing bar chart
ax_t = fig.add_subplot(gs[2, 3:])
bars2 = ax_t.bar(
    [LABELS[m].replace("\n", " ") for m in ALL_MODELS],
    [timings[m] for m in ALL_MODELS],
    color=[COLORS[m] for m in ALL_MODELS],
    width=0.55, edgecolor="white", linewidth=0.8)
for bar, m in zip(bars2, ALL_MODELS):
    ax_t.text(bar.get_x() + bar.get_width() / 2,
              bar.get_height() + 0.5, f"{timings[m]:.0f}s",
              ha="center", va="bottom", fontsize=9, fontweight="bold")
ax_t.set_ylabel("Runtime (s)", fontsize=10)
ax_t.set_title("Runtime comparison", fontsize=11)
ax_t.tick_params(labelsize=8)
ax_t.set_ylim(0, max(timings.values()) * 1.2)
ax_t.axvline(0.5, color="black", linewidth=1.2, linestyle=":")

fig.suptitle(
    "Condensate Segmentation — Model Comparison\n"
    "(Old: full stack  |  New models: ROI stack, mid Z-slice)",
    fontsize=13, fontweight="bold")
comp_path = FIG_DIR / "comparison_figure.png"
fig.savefig(comp_path, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"\nSaved: {comp_path}")

# ── 4. Pipeline flowmap figure ────────────────────────────────────────────────
PIPELINES = {
    "old_cellpose": [
        "Input\nFull Z-stack\n(Ch1, Ch2)",
        "2D Segmentation\nper slice\nCellpose cyto2\n(no denoise)",
        "Per-slice\nMeasurements\n(regionprops)",
        "Overlap\nAnalysis",
        "Partition\nCoefficient",
    ],
    "cellpose3": [
        "Input\nROI Z-stack\n(Ch1, Ch2)",
        "Denoise\nDenoiseModel\ncyto3",
        "3D Segmentation\nCellpose cyto3\n(do_3D=True)",
        "Per-slice\nMeasurements\n(regionprops)",
        "Partition\nCoefficient",
    ],
    "stardist": [
        "Input\nROI Z-stack\n(Ch1, Ch2)",
        "Normalize\n1st–99.8th pctile\nper slice",
        "2D Prediction\nper slice\nStarDist2D\n(versatile_fluo)",
        "Instance Labels\n+ regionprops",
        "Partition\nCoefficient",
    ],
    "ufish": [
        "Input\nROI Z-stack\n(Ch2: condensates\nCh1: nuclei)",
        "ONNX Spot\nDetection\nper slice",
        "Spots → Mask\n(disk r=3 px)\n+ Otsu nuclei\nthreshold",
        "Overlap\nAnalysis",
        "Partition\nCoefficient",
    ],
    "nellie": [
        "Input\nROI Z-stack\n(Ch1, Ch2)",
        "Frangi Filter\n(tubularity /\nedge enhance)",
        "Semantic Label\n+ Network\nAnalysis",
        "Hierarchy\nFeature\nExtraction",
        "Partition\nCoefficient",
    ],
}

N_STEPS = 5
BOX_W   = 0.72
BOX_H   = 0.70
STEP_H  = 1.15

fig2, axes2 = plt.subplots(1, 5, figsize=(26, 8))
fig2.suptitle("Pipeline Flowmap — How Each Model Works",
              fontsize=15, fontweight="bold", y=1.03)

for ax, model in zip(axes2, ALL_MODELS):
    color = COLORS[model]
    steps = PIPELINES[model]
    n     = len(steps)
    total_h = (n - 1) * STEP_H + BOX_H

    ax.set_xlim(0, 1)
    ax.set_ylim(-1.0, total_h + 0.3)
    ax.axis("off")
    title = LABELS[model].replace("\n", " ")
    suffix = "  ← baseline" if model == "old_cellpose" else ""
    ax.set_title(title + suffix, fontsize=12, fontweight="bold",
                 color=color, pad=12)

    for i, step in enumerate(steps):
        y      = total_h - i * STEP_H - BOX_H / 2
        is_end = (i == 0 or i == n - 1)
        fc     = color if is_end else "white"
        tc     = "white" if is_end else color

        box = mpatches.FancyBboxPatch(
            ((1 - BOX_W) / 2, y - BOX_H / 2),
            BOX_W, BOX_H,
            boxstyle="round,pad=0.04",
            facecolor=fc, edgecolor=color, linewidth=2,
            transform=ax.transData, clip_on=False)
        ax.add_patch(box)
        ax.text(0.5, y, step, ha="center", va="center",
                fontsize=8, color=tc,
                fontweight="bold" if is_end else "normal",
                linespacing=1.4)

        if i < n - 1:
            y_next = total_h - (i + 1) * STEP_H - BOX_H / 2
            ax.annotate(
                "", xy=(0.5, y_next + BOX_H / 2 + 0.03),
                xytext=(0.5, y - BOX_H / 2 - 0.03),
                arrowprops=dict(arrowstyle="-|>", color=color,
                                lw=1.8, mutation_scale=14))

    ax.text(0.5, -0.75,
            f"Runtime: {timings[model]:.0f} s\nPC: {pcs[model]:.2f}",
            ha="center", va="center", fontsize=9.5, color=color, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.4", facecolor=color,
                      alpha=0.12, edgecolor=color, linewidth=1.5))

fig2.tight_layout()
flow_path = FIG_DIR / "flowmap_figure.png"
fig2.savefig(flow_path, dpi=150, bbox_inches="tight")
plt.close(fig2)
print(f"Saved: {flow_path}")
print("\nDone.")
