#!/usr/bin/env python3
"""Generate partition coefficient comparison visualization."""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

fig, ax = plt.subplots(figsize=(8, 5), dpi=150)
ax.set_xlim(0, 7)
ax.set_ylim(0, 4)
ax.axis('off')

# Title
ax.text(3.5, 3.5, 'Partition Coefficient', fontsize=28, weight='bold', ha='center')

# Large PC value
ax.text(3.5, 2.7, '6.297', fontsize=72, weight='bold', color='#1D7A38', ha='center')

# Horizontal bars
bar_y_pipeline = 1.3
bar_y_reference = 0.5
bar_width = 3.5
bar_height = 0.35

# Pipeline bar (green)
rect_pipeline = mpatches.Rectangle((1, bar_y_pipeline), bar_width, bar_height,
                                   facecolor='#70AD47', edgecolor='black', linewidth=1.5)
ax.add_patch(rect_pipeline)
ax.text(0.8, bar_y_pipeline + bar_height/2, 'Pipeline', fontsize=12, weight='bold',
        ha='right', va='center')
ax.text(1 + bar_width + 0.2, bar_y_pipeline + bar_height/2, '6.297', fontsize=12,
        weight='bold', ha='left', va='center')

# Reference bar (red)
rect_reference = mpatches.Rectangle((1, bar_y_reference), bar_width, bar_height,
                                    facecolor='#C85A54', edgecolor='black', linewidth=1.5)
ax.add_patch(rect_reference)
ax.text(0.8, bar_y_reference + bar_height/2, 'Reference', fontsize=12, weight='bold',
        ha='right', va='center')
ax.text(1 + bar_width + 0.2, bar_y_reference + bar_height/2, '6.32', fontsize=12,
        weight='bold', ha='left', va='center')

# Baseline
ax.plot([1, 4.5], [bar_y_reference - 0.05, bar_y_reference - 0.05], 'k-', linewidth=2)

plt.tight_layout()
plt.savefig('/Users/danielchang/code/research/docs/pc_comparison.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.savefig('/Users/danielchang/code/research/docs/pc_comparison.jpg', dpi=150, bbox_inches='tight', facecolor='white')
print("✓ Generated pc_comparison.png and .jpg")
plt.close()
