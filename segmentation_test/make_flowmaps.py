"""
Generates two readable flowmap PDFs for the segmentation model survey.
  flowmap_1_cellpose.pdf  — Old Cellpose (baseline) vs. Cellpose 3 (recommended)
  flowmap_2_alternatives.pdf — StarDist, U-FISH, Nellie
Output goes to docs/pipeline/.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
from pathlib import Path

OUT_DIR = Path(__file__).parent.parent / "docs" / "pipeline"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Known values from the model survey ───────────────────────────────────────
META = {
    "old_cellpose": {"pc": 2.04, "runtime": "—",   "color": "#888888"},
    "cellpose3":    {"pc": 3.33, "runtime": "11 s", "color": "#1A6EB5"},
    "stardist":     {"pc": 1.91, "runtime": "6 s",  "color": "#E05C2A"},
    "ufish":        {"pc": 3.81, "runtime": "2 s",  "color": "#C4850A"},
    "nellie":       {"pc": 3.57, "runtime": "14 s", "color": "#6B46C1"},
}

PIPELINES = {
    "old_cellpose": {
        "label": "Old Cellpose (Baseline)",
        "note": "Winter 2026 pipeline — reference point",
        "steps": [
            ("Input", "Full Z-stack\nCh1 (nuclei)\nCh2 (condensates)"),
            ("2D Segmentation\nper slice", "Cellpose cyto2\nNo denoising\n55 independent slices"),
            ("Per-slice\nMeasurements", "scikit-image\nregionprops_table\n(area, centroid, intensity)"),
            ("Overlap Analysis", "Condensate ∩ nucleus\nClassify nuclear\nvs. cytoplasmic"),
            ("Partition\nCoefficient", "PC = condensate density\n÷ dilute density"),
        ],
    },
    "cellpose3": {
        "label": "Cellpose 3  ★ Recommended",
        "note": "Three concrete improvements over the baseline",
        "steps": [
            ("Input", "ROI Z-stack\nCh1 (nuclei)\nCh2 (condensates)"),
            ("Denoise", "DenoiseModel cyto3\nRuns on every slice\nSharpens boundaries\nbefore segmentation"),
            ("3D Segmentation", "Cellpose cyto3\ndo_3D=True\nXY + XZ + YZ planes\nmerged jointly"),
            ("Per-slice\nMeasurements", "scikit-image\nregionprops_table\n(area, centroid, intensity)"),
            ("Partition\nCoefficient", "PC = condensate density\n÷ dilute density"),
        ],
    },
    "stardist": {
        "label": "StarDist 2D",
        "note": "Designed for cell nuclei — not ideal for condensates",
        "steps": [
            ("Input", "ROI Z-stack\nCh1 (nuclei)\nCh2 (condensates)"),
            ("Normalize\nper slice", "Clip to 1st–99.8th\npercentile intensity\nbefore prediction"),
            ("2D Prediction\nper slice", "StarDist2D\nversatile_fluo model\nPolygon instance labels"),
            ("Instance Labels\n+ Measurements", "scikit-image\nregionprops\nper detected object"),
            ("Partition\nCoefficient", "PC = condensate density\n÷ dilute density"),
        ],
    },
    "ufish": {
        "label": "U-FISH",
        "note": "Spot detector — treats condensates as points, not volumes",
        "steps": [
            ("Input", "ROI Z-stack\nCh2: condensates\nCh1: nuclei"),
            ("ONNX Spot\nDetection", "Finds spot centers\nper slice\nTreats each condensate\nas a point source"),
            ("Spots → Mask", "Expand each spot\nto disk radius = 3 px\nOtsu threshold\nfor nuclei (!)"),
            ("Overlap\nAnalysis", "Spot disk ∩ nucleus\nClassify nuclear\nvs. cytoplasmic"),
            ("Partition\nCoefficient", "PC = condensate density\n÷ dilute density\n⚠ nuclei mask differs"),
        ],
    },
    "nellie": {
        "label": "Nellie",
        "note": "Designed for tubular organelles — not principled for condensates",
        "steps": [
            ("Input", "ROI Z-stack\nCh1 (nuclei)\nCh2 (condensates)"),
            ("Frangi Filter", "Detects tubular /\nelongated structures\n(mitochondria-optimized)"),
            ("Semantic Label\n+ Network Graph", "Builds organelle\ngraph from filtered\nresponse"),
            ("Hierarchy Feature\nExtraction", "Extracts shape and\nintensity features\nfrom graph nodes"),
            ("Partition\nCoefficient", "PC = condensate density\n÷ dilute density"),
        ],
    },
}


def draw_flowmap(ax, model_key, show_baseline_tag=False):
    info = PIPELINES[model_key]
    meta = META[model_key]
    color = meta["color"]
    steps = info["steps"]
    n = len(steps)

    BOX_W = 0.68
    BOX_H = 0.90
    STEP_H = 1.35
    total_h = (n - 1) * STEP_H + BOX_H
    pad = 0.3

    ax.set_xlim(0, 1)
    ax.set_ylim(-1.5, total_h + pad + 0.6)
    ax.axis("off")

    # Model title
    ax.text(0.5, total_h + pad + 0.45, info["label"],
            ha="center", va="center", fontsize=15, fontweight="bold", color=color)
    # Subtitle note
    ax.text(0.5, total_h + pad + 0.05, info["note"],
            ha="center", va="center", fontsize=10, color="#555555", style="italic")

    # Divider line under title
    ax.plot([0.05, 0.95], [total_h + pad - 0.12, total_h + pad - 0.12],
            color=color, lw=1.5, alpha=0.4)

    for i, (title, body) in enumerate(steps):
        y = total_h - i * STEP_H - BOX_H / 2
        is_start = (i == 0)
        is_end = (i == n - 1)
        is_key = not is_start and not is_end

        if is_start or is_end:
            fc = color
            title_color = "white"
            body_color = "white"
            alpha = 1.0
        else:
            fc = "white"
            title_color = color
            body_color = "#333333"
            alpha = 1.0

        box = mpatches.FancyBboxPatch(
            ((1 - BOX_W) / 2, y - BOX_H / 2),
            BOX_W, BOX_H,
            boxstyle="round,pad=0.05",
            facecolor=fc,
            edgecolor=color,
            linewidth=2.2,
            zorder=3,
        )
        ax.add_patch(box)

        # Step title (bold, larger)
        ax.text(0.5, y + 0.18, title,
                ha="center", va="center",
                fontsize=11, fontweight="bold", color=title_color,
                linespacing=1.3, zorder=4)

        # Step body (smaller, details)
        ax.text(0.5, y - 0.2, body,
                ha="center", va="center",
                fontsize=9, color=body_color,
                linespacing=1.4, zorder=4)

        # Arrow to next step
        if i < n - 1:
            y_next = total_h - (i + 1) * STEP_H - BOX_H / 2
            ax.annotate(
                "", xy=(0.5, y_next + BOX_H / 2 + 0.04),
                xytext=(0.5, y - BOX_H / 2 - 0.04),
                arrowprops=dict(
                    arrowstyle="-|>", color=color,
                    lw=2.0, mutation_scale=18),
                zorder=2)

    # PC + runtime badge at bottom
    badge_text = f"PC = {meta['pc']:.2f}     Runtime: {meta['runtime']}"
    ax.text(0.5, -1.1, badge_text,
            ha="center", va="center", fontsize=11, fontweight="bold", color=color,
            bbox=dict(boxstyle="round,pad=0.5", facecolor=color,
                      alpha=0.12, edgecolor=color, linewidth=1.8))


def make_pdf(models, filename, title, subtitle):
    n = len(models)
    fig, axes = plt.subplots(1, n, figsize=(n * 5.5, 13))
    if n == 1:
        axes = [axes]

    fig.patch.set_facecolor("white")
    fig.suptitle(title, fontsize=20, fontweight="bold", y=0.98, color="#111111")
    fig.text(0.5, 0.955, subtitle, ha="center", fontsize=12, color="#555555", style="italic")

    for ax, model in zip(axes, models):
        draw_flowmap(ax, model)

    plt.tight_layout(rect=[0, 0, 1, 0.945])
    out = OUT_DIR / filename
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: {out}")


# ── PDF 1: Old Cellpose vs. Cellpose 3 ────────────────────────────────────────
make_pdf(
    models=["old_cellpose", "cellpose3"],
    filename="flowmap_1_cellpose.pdf",
    title="Segmentation Flowmap — Cellpose Comparison",
    subtitle="Left: Winter 2026 baseline (cyto2, 2D)     Right: Recommended model (cyto3, denoising, 3D)",
)

# ── PDF 2: StarDist, U-FISH, Nellie ───────────────────────────────────────────
make_pdf(
    models=["stardist", "ufish", "nellie"],
    filename="flowmap_2_alternatives.pdf",
    title="Segmentation Flowmap — Alternative Models",
    subtitle="Surveyed but not recommended — see notes on each for why",
)
