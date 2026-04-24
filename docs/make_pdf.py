from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, HRFlowable
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import PageBreak
import os

W, H = landscape(letter)  # 11 x 8.5

BLUE = colors.HexColor("#1A6EB5")
LIGHT_BLUE = colors.HexColor("#E8F0FE")
ROW_ALT = colors.HexColor("#F0F4F8")
DARK = colors.HexColor("#1A1A2E")
MUTED = colors.HexColor("#667788")
GREEN = colors.HexColor("#158040")
YELLOW = colors.HexColor("#924000")
WHITE = colors.white
BLACK = colors.black

def style(size=11, bold=False, color=DARK, align=TA_LEFT, leading=None):
    return ParagraphStyle(
        "s",
        fontSize=size,
        fontName="Helvetica-Bold" if bold else "Helvetica",
        textColor=color,
        alignment=align,
        leading=leading or size * 1.35,
        spaceAfter=0,
    )

def slide_title(title, subtitle=None):
    elems = []
    elems.append(Paragraph(title, style(20, bold=True, color=BLUE)))
    if subtitle:
        elems.append(Spacer(1, 4))
        elems.append(Paragraph(subtitle, style(11, color=MUTED)))
    elems.append(Spacer(1, 6))
    elems.append(HRFlowable(width="100%", thickness=2, color=BLUE))
    elems.append(Spacer(1, 10))
    return elems

doc = SimpleDocTemplate(
    "spring_checkin_slides.pdf",
    pagesize=landscape(letter),
    leftMargin=0.6*inch, rightMargin=0.6*inch,
    topMargin=0.45*inch, bottomMargin=0.45*inch,
)

story = []

# ── Slide 1: Title ─────────────────────────────────────────────────────────
story.append(Spacer(1, 0.8*inch))
story.append(Paragraph("Spring 2026 Check-in", style(32, bold=True, color=BLUE, align=TA_CENTER)))
story.append(Spacer(1, 10))
story.append(Paragraph("Segmentation Model Survey — JABr Condensates", style(16, color=DARK, align=TA_CENTER)))
story.append(Spacer(1, 8))
story.append(Paragraph("Daniel Chang  ·  C&amp;S BIO 199/197  ·  PI: Elisa Franco  ·  2026-04-23",
                        style(12, color=MUTED, align=TA_CENTER)))
story.append(Spacer(1, 18))
story.append(HRFlowable(width="80%", thickness=2, color=BLUE, hAlign="CENTER"))
story.append(Spacer(1, 18))
bullets = [
    "Winter pipeline left a PC gap: automated 2.04 vs. manual reference 6.32",
    "Goal this week: survey alternative segmentation models to close the gap",
    "Dataset: JABr ROI Z-stack  (55 slices × 185 × 259, 2-channel fluorescence)",
]
for b in bullets:
    story.append(Paragraph(f"<bullet>&bull;</bullet>  {b}", style(12, color=DARK)))
    story.append(Spacer(1, 6))
story.append(PageBreak())

# ── Slide 2: Model Comparison Table ────────────────────────────────────────
story += slide_title("Model Comparison", "Same PC formula, same dataset — 4 new models benchmarked")

tdata = [
    ["Model", "Approach", "PC", "Runtime"],
    ["Old Cellpose (2D)", "cyto2, slice-by-slice (baseline)", "2.04", "—"],
    ["Cellpose 3  ★", "cyto3 + denoising + 3D mode", "3.33", "11 s"],
    ["StarDist 2D", "versatile_fluo, slice-by-slice", "1.91", "6 s"],
    ["U-FISH †", "ONNX spot detection", "3.81", "2 s"],
    ["Nellie", "Frangi filter + graph analysis", "3.57", "14 s"],
    ["Reference", "Manual / ImageJ benchmark", "6.32", "—"],
]

ts = TableStyle([
    ("BACKGROUND",  (0,0), (-1,0),  BLUE),
    ("TEXTCOLOR",   (0,0), (-1,0),  WHITE),
    ("FONTNAME",    (0,0), (-1,0),  "Helvetica-Bold"),
    ("FONTSIZE",    (0,0), (-1,-1), 11),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, ROW_ALT]),
    ("TEXTCOLOR",   (0,1), (-1,-1), DARK),
    # highlight Cellpose 3
    ("TEXTCOLOR",   (0,2), (0,2),  GREEN),
    ("FONTNAME",    (0,2), (-1,2), "Helvetica-Bold"),
    # highlight U-FISH
    ("TEXTCOLOR",   (0,4), (0,4),  YELLOW),
    # highlight Reference
    ("TEXTCOLOR",   (0,6), (-1,6), BLUE),
    ("FONTNAME",    (0,6), (-1,6), "Helvetica-Bold"),
    ("ALIGN",       (2,0), (3,-1), "CENTER"),
    ("VALIGN",      (0,0), (-1,-1),"MIDDLE"),
    ("ROWPADDING",  (0,0), (-1,-1), 7),
    ("GRID",        (0,0), (-1,-1), 0.5, colors.HexColor("#DDDDDD")),
])
col_w = [2.0*inch, 4.2*inch, 0.9*inch, 0.9*inch]
t = Table(tdata, colWidths=col_w, repeatRows=1)
t.setStyle(ts)
story.append(t)
story.append(Spacer(1, 8))
story.append(Paragraph("★ Recommended    † U-FISH uses Otsu threshold for nuclei (not a trained model) — PC likely inflated",
                        style(9, color=MUTED)))
story.append(PageBreak())

# ── Slide 3: Why Cellpose 3 ─────────────────────────────────────────────────
story += slide_title("Why Cellpose 3?", "Three concrete changes over the Winter baseline  (PC: 2.04 → 3.33)")

items = [
    ("1  Denoising",
     "DenoiseModel cyto3 runs on every slice before segmentation — suppresses shot noise and sharpens condensate boundaries. "
     "PC intensities are always computed from the original raw pixels; denoising only guides boundary placement."),
    ("2  3D mode",
     "do_3D=True processes XY, XZ, and YZ planes simultaneously and merges gradient flows before drawing boundaries. "
     "The old pipeline ran 55 independent 2D slices with no cross-slice awareness — a condensate spanning 3 slices "
     "was segmented 3 separate times, often with inconsistent boundaries, directly hurting the intensity ratio."),
    ("3  cyto3 vs cyto2",
     "cyto3 is trained on a larger, more diverse dataset and is generally better at small, dim, or irregularly shaped objects. "
     "The 3D mode is likely the single largest contributor to the PC improvement."),
]
for title, body in items:
    story.append(Paragraph(title, style(13, bold=True, color=BLUE)))
    story.append(Spacer(1, 3))
    story.append(Paragraph(body, style(11, color=DARK)))
    story.append(Spacer(1, 12))

# callout box via a 1-cell table
callout_text = (
    "All models still fall short of reference PC = 6.32. The gap is due to condensate segmentation sensitivity — "
    "small boundary errors have an outsized effect on intensity ratios."
)
callout = Table([[Paragraph(callout_text, style(11, color=DARK))]],
                colWidths=[9.5*inch])
callout.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,-1), LIGHT_BLUE),
    ("BOX",        (0,0), (-1,-1), 1.5, BLUE),
    ("ROWPADDING", (0,0), (-1,-1), 8),
]))
story.append(callout)
story.append(PageBreak())

# ── Slide 4: Comparison Figure ──────────────────────────────────────────────
story += slide_title("Segmentation Output — Side-by-Side", "Mid-Z slice, all models")

fig_path = "segmentation_test/outputs/comparison/comparison_figure.png"
if os.path.exists(fig_path):
    img = Image(fig_path, width=9.5*inch, height=5.5*inch)
    img.hAlign = "CENTER"
    story.append(img)
else:
    story.append(Paragraph(f"[figure not found: {fig_path}]", style(12, color=MUTED, align=TA_CENTER)))
story.append(PageBreak())

# ── Slide 5: Caveats ────────────────────────────────────────────────────────
story += slide_title("Caveats — Apples-to-Apples Problem", "PC values are not fully comparable across models")

tdata2 = [
    ["Model", "Condensate mask", "Nuclei mask"],
    ["Old Cellpose", "Cellpose cyto2 (2D)", "Cellpose cyto2 (2D)"],
    ["Cellpose 3", "Cellpose cyto3 (3D)", "Cellpose cyto3 (3D)"],
    ["StarDist 2D", "StarDist2D", "StarDist2D"],
    ["U-FISH  ⚠", "U-FISH spot + disk", "Otsu threshold  ← different!"],
    ["Nellie", "Frangi + graph", "Frangi + graph"],
]
ts2 = TableStyle([
    ("BACKGROUND",  (0,0), (-1,0), BLUE),
    ("TEXTCOLOR",   (0,0), (-1,0), WHITE),
    ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
    ("FONTSIZE",    (0,0), (-1,-1), 11),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, ROW_ALT]),
    ("TEXTCOLOR",   (0,1), (-1,-1), DARK),
    ("TEXTCOLOR",   (0,4), (-1,4), YELLOW),
    ("FONTNAME",    (0,4), (-1,4), "Helvetica-Bold"),
    ("ALIGN",       (0,0), (-1,-1), "LEFT"),
    ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
    ("ROWPADDING",  (0,0), (-1,-1), 7),
    ("GRID",        (0,0), (-1,-1), 0.5, colors.HexColor("#DDDDDD")),
])
col_w2 = [2.2*inch, 3.6*inch, 3.6*inch]
t2 = Table(tdata2, colWidths=col_w2)
t2.setStyle(ts2)
story.append(t2)
story.append(Spacer(1, 14))

fix_text = ("Fix: use the same Cellpose 3 nuclear mask for all models and only swap the condensate mask — "
            "isolates condensate segmentation as the single variable.")
fix_box = Table([[Paragraph(fix_text, style(11, bold=True, color=GREEN))]],
                colWidths=[9.5*inch])
fix_box.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#F0FFF4")),
    ("BOX",        (0,0), (-1,-1), 1.5, GREEN),
    ("ROWPADDING", (0,0), (-1,-1), 8),
]))
story.append(fix_box)
story.append(PageBreak())

# ── Slide 6: Next Steps ─────────────────────────────────────────────────────
story += slide_title("Next Steps", "Spring 2026")

steps = [
    ("1  Standardize nuclear mask", "Re-run all models using Cellpose 3 nuclei masks → fair PC comparison"),
    ("2  3D volume estimation", "Aggregate masks across Z-slices; compute true voxel volumes per condensate"),
    ("3  CLI packaging", "Replace hardcoded paths in cellpose_pipeline.py with argparse / config file; add docstrings"),
    ("4  Spring poster / report", "Narrative: problem → Winter pipeline → model survey → Cellpose 3 → 3D volume"),
]
for title, desc in steps:
    story.append(Paragraph(title, style(13, bold=True, color=BLUE)))
    story.append(Spacer(1, 3))
    story.append(Paragraph(desc, style(11, color=DARK)))
    story.append(Spacer(1, 14))

# ── Slide 7: Reference PC Investigation ─────────────────────────────────────
story += slide_title("Reference PC Investigation", "2026-04-23 — found a methodological mismatch")

story.append(Paragraph("Three types of PC", style(13, bold=True, color=BLUE)))
story.append(Spacer(1, 6))

pc_types = [
    ("Nuclear PC",
     "Condensate vs. dilute, both measured inside the nucleus. This is what the automated pipeline computes."),
    ("Cytoplasmic PC",
     "Condensate vs. dilute, both measured in the cytoplasm. Not currently computed by the pipeline."),
    ("Background-subtracted PC",
     "Same formula but a background constant B (measured outside all cells) is subtracted from both "
     "densities before taking the ratio. The reference CSVs use this method."),
]
for title, desc in pc_types:
    story.append(Paragraph(f"<b>{title}</b> — {desc}", style(11, color=DARK)))
    story.append(Spacer(1, 6))

story.append(Spacer(1, 8))
story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#DDDDDD")))
story.append(Spacer(1, 8))

story.append(Paragraph("Findings for Sample2_5_1", style(13, bold=True, color=BLUE)))
story.append(Spacer(1, 6))

findings = [
    ("Dilute density anomaly",
     "Nuclear dilute density for Sample2_5_1 = 104.09, vs. ~70 for all other Sample2_5 entries. "
     "If dilute density were ~70, reference PC ≈ 9.4, not 6.32. "
     "Possible cause: loose manual ImageJ mask left bright condensate-edge pixels counted as "
     "dilute-phase background, deflating the reference PC."),
    ("Background subtraction not in pipeline",
     "The person who computed the reference CSVs confirmed she applied background subtraction before "
     "computing PC. The automated pipeline does not. The formula becomes: "
     "PC = (condensate_density − B) / (dilute_density − B). "
     "Since dilute density is much closer to background than condensate density, subtracting B "
     "lowers the denominator more proportionally, inflating PC. "
     "Part of the gap (pipeline 3.33 vs. reference 6.32) is methodological, not just segmentation quality."),
]
for title, desc in findings:
    warn_box = Table([[Paragraph(f"<b>{title}</b>", style(11, color=YELLOW)),
                       Paragraph(desc, style(11, color=DARK))]],
                     colWidths=[1.8*inch, 7.7*inch])
    warn_box.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#FFFBEB")),
        ("BOX",        (0,0), (-1,-1), 1, colors.HexColor("#924000")),
        ("VALIGN",     (0,0), (-1,-1), "TOP"),
        ("ROWPADDING", (0,0), (-1,-1), 7),
    ]))
    story.append(warn_box)
    story.append(Spacer(1, 8))

action_text = ("Action: confirm background estimation method with lab member → "
               "add background subtraction to pipeline → recompute PC for fair comparison with reference.")
action_box = Table([[Paragraph(action_text, style(11, bold=True, color=BLUE))]],
                   colWidths=[9.5*inch])
action_box.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#E8F0FE")),
    ("BOX",        (0,0), (-1,-1), 1.5, BLUE),
    ("ROWPADDING", (0,0), (-1,-1), 8),
]))
story.append(action_box)

doc.build(story)
print("Saved: spring_checkin_slides.pdf")
