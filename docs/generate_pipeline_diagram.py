#!/usr/bin/env python3
"""Generate pipeline flowchart diagram using matplotlib."""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

fig, ax = plt.subplots(figsize=(2.72, 4.9), dpi=150)
ax.set_xlim(-1.5, 1.5)
ax.set_ylim(-5, 5)
ax.axis('off')

# Colors
colors = {
    'input': '#EDE8DC',
    'channel': '#FDEBD0',
    'process': '#EAF3FB',
    'mask': '#D5F5E3',
    'analysis': '#D6EEF8',
    'output': '#D4EDDA',
}

borders = {
    'input': '#8B7355',
    'channel': '#CA6F1E',
    'process': '#2980B9',
    'mask': '#1A8048',
    'analysis': '#117A8B',
    'output': '#1D7A38',
}

def draw_box(ax, x, y, label, color_type, width=0.8, height=0.4):
    """Draw a rounded box with text."""
    box = FancyBboxPatch((x - width/2, y - height/2), width, height,
                         boxstyle="round,pad=0.05",
                         edgecolor=borders[color_type], facecolor=colors[color_type],
                         linewidth=1.5)
    ax.add_patch(box)
    ax.text(x, y, label, ha='center', va='center', fontsize=7.5, weight='normal',
            fontfamily='sans-serif', wrap=True)

def draw_arrow(ax, x1, y1, x2, y2):
    """Draw an arrow between two points."""
    arrow = FancyArrowPatch((x1, y1), (x2, y2),
                           arrowstyle='->', mutation_scale=15,
                           color='gray', linewidth=0.8, zorder=1)
    ax.add_patch(arrow)

# Y positions
y_input = 4.5
y_split = 3.7
y_denoise = 2.9
y_seg = 2.1
y_mask = 1.3
y_merge = 0.8
y_feat = 0.0
y_pc = -0.8
y_out = -1.6

# Input
draw_box(ax, 0, y_input, 'Raw Z-Stack\n(.ome.tif)', 'input', width=1.0, height=0.45)

# Channel split
draw_box(ax, -0.65, y_split, 'Ch1: Nuclei', 'channel', width=0.75, height=0.4)
draw_box(ax, 0.65, y_split, 'Ch2: Cond.', 'channel', width=0.75, height=0.4)
draw_arrow(ax, -0.2, y_input - 0.225, -0.65, y_split + 0.2)
draw_arrow(ax, 0.2, y_input - 0.225, 0.65, y_split + 0.2)

# Denoise
draw_box(ax, -0.65, y_denoise, 'Denoise\n(cyto3)', 'process', width=0.75, height=0.45)
draw_box(ax, 0.65, y_denoise, 'Denoise\n(cyto3)', 'process', width=0.75, height=0.45)
draw_arrow(ax, -0.65, y_split - 0.2, -0.65, y_denoise + 0.225)
draw_arrow(ax, 0.65, y_split - 0.2, 0.65, y_denoise + 0.225)

# 3D Segment
draw_box(ax, -0.65, y_seg, '3D Segment\n(do_3D=True)', 'process', width=0.75, height=0.5)
draw_box(ax, 0.65, y_seg, '3D Segment\n(do_3D=True)', 'process', width=0.75, height=0.5)
draw_arrow(ax, -0.65, y_denoise - 0.225, -0.65, y_seg + 0.25)
draw_arrow(ax, 0.65, y_denoise - 0.225, 0.65, y_seg + 0.25)

# Masks
draw_box(ax, -0.65, y_mask, 'Nuclei\nMasks', 'mask', width=0.7, height=0.45)
draw_box(ax, 0.65, y_mask, 'Cond.\nMasks', 'mask', width=0.7, height=0.45)
draw_arrow(ax, -0.65, y_seg - 0.25, -0.65, y_mask + 0.225)
draw_arrow(ax, 0.65, y_seg - 0.25, 0.65, y_mask + 0.225)

# Merge
draw_arrow(ax, -0.65, y_mask - 0.225, -0.2, y_merge + 0.1)
draw_arrow(ax, 0.65, y_mask - 0.225, 0.2, y_merge + 0.1)
draw_arrow(ax, -0.2, y_merge + 0.1, 0, y_merge + 0.15)
draw_arrow(ax, 0.2, y_merge + 0.1, 0, y_merge + 0.15)
draw_box(ax, 0, y_merge, 'Merge', 'mask', width=0.6, height=0.35)

# Feature extraction
draw_arrow(ax, 0, y_merge - 0.175, 0, y_feat + 0.25)
draw_box(ax, 0, y_feat, 'Feature Extraction\n(area, intensity, vol.)', 'analysis', width=1.1, height=0.5)

# Partition coefficient
draw_arrow(ax, 0, y_feat - 0.25, 0, y_pc + 0.25)
draw_box(ax, 0, y_pc, 'Partition Coeff.\n(PC = cond / dilute)', 'analysis', width=1.0, height=0.5)

# Output
draw_arrow(ax, 0, y_pc - 0.25, 0, y_out + 0.2)
draw_box(ax, 0, y_out, 'Output\n(masks, tables, PC)', 'output', width=0.95, height=0.45)


plt.tight_layout(pad=0)
plt.savefig('/Users/danielchang/code/research/docs/pipeline_diagram_vertical.pdf',
            format='pdf', dpi=150, bbox_inches='tight', pad_inches=0.05)
plt.savefig('/Users/danielchang/code/research/docs/pipeline_diagram_vertical.png',
            format='png', dpi=150, bbox_inches='tight', pad_inches=0.05)
plt.savefig('/Users/danielchang/code/research/docs/pipeline_diagram_vertical.jpg',
            format='jpg', dpi=150, bbox_inches='tight', pad_inches=0.05)
print("✓ Generated pipeline_diagram_vertical.pdf, .png, and .jpg")
plt.close()
