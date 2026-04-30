"""
make_slide_08.py — Generate slide_08_pc_method.png.

Reads pipeline outputs (masks + summary) and the raw condensate stack,
then renders a two-panel figure:
  Left : z=20 slice with color-coded region overlay
  Right: Partition Coefficient formula (steps 1–3) + final PC value

Run from repo root:
    python spring_implementation/make_slide_08.py
"""

import numpy as np
import tifffile as tiff
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd
from pathlib import Path

OUTPUTS   = Path("spring_implementation/outputs")
SLIDES    = Path("spring_implementation/slides")
COND_PATH = Path("data/raw_condensates/C2-ROI_raw_stack_sample2_5.tif")
Z_SLICE   = 20

COND_COLOR = (0.15, 0.85, 0.15)   # green
NUC_COLOR  = (0.20, 0.30, 0.80)   # blue
BG_COLOR   = (0.78, 0.42, 0.38)   # warm brown-red


def make_overlay(raw, cond_mask, nuc_mask):
    """Return an RGB array with region-colored overlay."""
    lo, hi = np.percentile(raw, 1), np.percentile(raw, 99.5)
    norm   = np.clip((raw.astype(float) - lo) / (hi - lo + 1e-9), 0, 1)
    rgb    = np.stack([norm, norm, norm], axis=-1)

    background   = ~nuc_mask
    dilute       = nuc_mask & ~cond_mask
    nuclear_cond = nuc_mask & cond_mask

    # Extranuclear: warm red tint
    a = 0.60
    rgb[background, 0] = np.clip(rgb[background, 0] * (1 - a) + a * BG_COLOR[0], 0, 1)
    rgb[background, 1] = rgb[background, 1] * (1 - a) + a * BG_COLOR[1]
    rgb[background, 2] = rgb[background, 2] * (1 - a) + a * BG_COLOR[2]

    # Nuclear dilute: blue tint
    a = 0.55
    rgb[dilute, 0] = rgb[dilute, 0] * (1 - a) + a * NUC_COLOR[0]
    rgb[dilute, 1] = rgb[dilute, 1] * (1 - a) + a * NUC_COLOR[1]
    rgb[dilute, 2] = rgb[dilute, 2] * (1 - a) + a * NUC_COLOR[2]

    # Condensates: bright green tint
    a = 0.70
    rgb[nuclear_cond, 0] = rgb[nuclear_cond, 0] * (1 - a) + a * COND_COLOR[0]
    rgb[nuclear_cond, 1] = rgb[nuclear_cond, 1] * (1 - a) + a * COND_COLOR[1]
    rgb[nuclear_cond, 2] = rgb[nuclear_cond, 2] * (1 - a) + a * COND_COLOR[2]

    return np.clip(rgb, 0, 1)


def draw_formula(ax, pc_val):
    """Render the PC formula as styled text on ax."""
    ax.axis("off")

    def t(y, text, size=11, weight="normal", color="black", style="normal"):
        ax.text(0.5, y, text, transform=ax.transAxes,
                ha="center", va="top", fontsize=size,
                fontweight=weight, color=color, fontstyle=style)

    t(0.97, "Partition Coefficient Formula", size=15, weight="bold")

    # Step 1
    t(0.82, "Step 1 — Background subtraction", size=12, weight="bold")
    t(0.72, "B  =  min(intensity across full FOV)", size=11)
    t(0.63, "removes camera/autofluorescence offset",
      size=9, color="#999999", style="italic")

    # Step 2
    t(0.52, "Step 2 — Condensate density",
      size=12, weight="bold", color="#2e8b57")
    t(0.42, "ρ_cond  =  mean[ clip(pixel − B, 0) ]", size=11)
    t(0.33, "over nuclear condensate voxels",
      size=9, color="#999999", style="italic")

    # Step 3
    t(0.22, "Step 3 — Dilute phase density",
      size=12, weight="bold", color="#4169e1")
    t(0.12, "ρ_dil  =  mean[ clip(pixel − B, 0) ]", size=11)
    t(0.03, "over 10×10×10 voxel patch in nuclear dilute phase",
      size=9, color="#999999", style="italic")

    # Final result
    ax.text(0.5, -0.06,
            f"PC  =  ρ_cond / ρ_dil  =  {pc_val:.3f}",
            transform=ax.transAxes, ha="center", va="top",
            fontsize=16, fontweight="bold", color="#4169e1")


def main():
    SLIDES.mkdir(exist_ok=True)

    cond_stack    = tiff.imread(COND_PATH)
    cond_masks_3d = tiff.imread(OUTPUTS / "condensate_masks.tif")
    nuc_masks_3d  = tiff.imread(OUTPUTS / "nuclei_masks.tif")
    summary       = pd.read_csv(OUTPUTS / "summary.csv").set_index("metric")["value"]
    pc_val        = float(summary["partition_coefficient"])

    raw       = cond_stack[Z_SLICE]
    cond_mask = cond_masks_3d[Z_SLICE] > 0
    nuc_mask  = nuc_masks_3d[Z_SLICE]  > 0
    rgb       = make_overlay(raw, cond_mask, nuc_mask)

    fig = plt.figure(figsize=(14, 6), facecolor="#d8d8d8")
    ax_img  = fig.add_axes([0.02, 0.13, 0.44, 0.82])
    ax_form = fig.add_axes([0.51, 0.10, 0.47, 0.88])
    ax_form.set_facecolor("#d8d8d8")

    ax_img.imshow(rgb)
    ax_img.set_title(f"Full slice  (z = {Z_SLICE})", fontsize=14,
                     fontweight="bold", pad=8)
    ax_img.axis("off")

    patches = [
        mpatches.Patch(facecolor=COND_COLOR, label="Condensate voxels"),
        mpatches.Patch(facecolor=NUC_COLOR,  label="Dilute phase (nuclear)"),
        mpatches.Patch(facecolor=BG_COLOR,   label="Background (B)"),
    ]
    ax_img.legend(handles=patches, loc="lower left", fontsize=9,
                  framealpha=0.75, edgecolor="none")

    draw_formula(ax_form, pc_val)

    out = SLIDES / "slide_08_pc_method.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved {out}  (PC = {pc_val:.3f})")


if __name__ == "__main__":
    main()
