#!/usr/bin/env python3
"""Generate combined metrics comparison visualization."""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

fig, ax = plt.subplots(figsize=(10, 12), dpi=150)
ax.set_xlim(0, 10)
ax.set_ylim(0, 12)
ax.axis('off')

# Colors
color_pipeline = '#70AD47'
color_reference = '#C85A54'

# Bar positioning (centered on canvas width 10)
# Longest bar is 2.5 wide, center at x=5: start at 5-1.25=3.75
bar_x_start = 3.75
label_x = 3.5

# Metric 1: Partition Coefficient
y_start = 10.5
ax.text(5, y_start, 'Partition Coefficient', fontsize=20, weight='bold', ha='center')
ax.text(5, y_start - 0.8, '6.297', fontsize=60, weight='bold', color='#1D7A38', ha='center')

# PC bars
bar_height = 0.3
rect_pc_pipeline = mpatches.Rectangle((bar_x_start, y_start - 2), 2.5, bar_height,
                                       facecolor=color_pipeline, edgecolor='black', linewidth=1.2)
ax.add_patch(rect_pc_pipeline)
ax.text(label_x, y_start - 1.85, 'Pipeline', fontsize=12, weight='bold', ha='right', va='center')
ax.text(bar_x_start + 2.7, y_start - 1.85, '6.297', fontsize=10, weight='bold', ha='left', va='center')

rect_pc_reference = mpatches.Rectangle((bar_x_start, y_start - 2.5), 2.5, bar_height,
                                        facecolor=color_reference, edgecolor='black', linewidth=1.2)
ax.add_patch(rect_pc_reference)
ax.text(label_x, y_start - 2.35, 'Reference', fontsize=12, weight='bold', ha='right', va='center')
ax.text(bar_x_start + 2.7, y_start - 2.35, '6.32', fontsize=10, weight='bold', ha='left', va='center')

ax.plot([bar_x_start, bar_x_start + 2.5], [y_start - 2.7, y_start - 2.7], 'k-', linewidth=1.5)

# Metric 2: Condensate Density
y_start = 6.5
ax.text(5, y_start, 'Condensate Density (μm⁻³)', fontsize=20, weight='bold', ha='center')
ax.text(5, y_start - 0.8, '440.93', fontsize=60, weight='bold', color='#70AD47', ha='center')

# Scale bars proportionally to their values (condensate: ref 658.30, pip 440.93)
max_cond = 658.30
bar_width_cond_ref = (658.30 / max_cond) * 2.5
bar_width_cond_pip = (440.93 / max_cond) * 2.5

rect_cond_pipeline = mpatches.Rectangle((bar_x_start, y_start - 2), bar_width_cond_pip, bar_height,
                                         facecolor=color_pipeline, edgecolor='black', linewidth=1.2)
ax.add_patch(rect_cond_pipeline)
ax.text(label_x, y_start - 1.85, 'Pipeline', fontsize=12, weight='bold', ha='right', va='center')
ax.text(bar_x_start + bar_width_cond_pip + 0.2, y_start - 1.85, '440.93', fontsize=10, weight='bold', ha='left', va='center')

rect_cond_reference = mpatches.Rectangle((bar_x_start, y_start - 2.5), bar_width_cond_ref, bar_height,
                                          facecolor=color_reference, edgecolor='black', linewidth=1.2)
ax.add_patch(rect_cond_reference)
ax.text(label_x, y_start - 2.35, 'Reference', fontsize=12, weight='bold', ha='right', va='center')
ax.text(bar_x_start + bar_width_cond_ref + 0.2, y_start - 2.35, '658.30', fontsize=10, weight='bold', ha='left', va='center')

ax.plot([bar_x_start, bar_x_start + bar_width_cond_ref + 0.3], [y_start - 2.7, y_start - 2.7], 'k-', linewidth=1.5)

# Metric 3: Dilute Density
y_start = 3
ax.text(5, y_start, 'Dilute Density (μm⁻³)', fontsize=20, weight='bold', ha='center')
ax.text(5, y_start - 0.8, '70.03', fontsize=60, weight='bold', color='#70AD47', ha='center')

# Scale bars proportionally (dilute: ref 104.09, pip 70.03)
max_dilute = 104.09
bar_width_dilute_ref = (104.09 / max_dilute) * 2.5
bar_width_dilute_pip = (70.03 / max_dilute) * 2.5

rect_dilute_pipeline = mpatches.Rectangle((bar_x_start, y_start - 2), bar_width_dilute_pip, bar_height,
                                          facecolor=color_pipeline, edgecolor='black', linewidth=1.2)
ax.add_patch(rect_dilute_pipeline)
ax.text(label_x, y_start - 1.85, 'Pipeline', fontsize=12, weight='bold', ha='right', va='center')
ax.text(bar_x_start + bar_width_dilute_pip + 0.2, y_start - 1.85, '70.03', fontsize=10, weight='bold', ha='left', va='center')

rect_dilute_reference = mpatches.Rectangle((bar_x_start, y_start - 2.5), bar_width_dilute_ref, bar_height,
                                           facecolor=color_reference, edgecolor='black', linewidth=1.2)
ax.add_patch(rect_dilute_reference)
ax.text(label_x, y_start - 2.35, 'Reference', fontsize=12, weight='bold', ha='right', va='center')
ax.text(bar_x_start + bar_width_dilute_ref + 0.2, y_start - 2.35, '104.09', fontsize=10, weight='bold', ha='left', va='center')

ax.plot([bar_x_start, bar_x_start + bar_width_dilute_ref + 0.3], [y_start - 2.7, y_start - 2.7], 'k-', linewidth=1.5)

plt.tight_layout()
plt.savefig('/Users/danielchang/code/research/docs/metrics_comparison.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.savefig('/Users/danielchang/code/research/docs/metrics_comparison.jpg', dpi=150, bbox_inches='tight', facecolor='white')
print("✓ Generated metrics_comparison.png and .jpg")
plt.close()
