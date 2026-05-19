#!/usr/bin/env python3
"""Generate comparison chart: reference vs pipeline metrics."""

import matplotlib.pyplot as plt
import numpy as np

fig, ax = plt.subplots(figsize=(8, 5), dpi=150)

# Data
metrics = ['Partition Coefficient\n(PC)', 'Condensate Density\n(μm⁻³)', 'Dilute Density\n(μm⁻³)']
reference = [6.324, 658.30, 104.09]
pipeline = [6.297, 440.93, 70.03]

# Calculate errors
errors = [(p - r) / r * 100 for p, r in zip(pipeline, reference)]

x = np.arange(len(metrics))
width = 0.35

# Create bars
bars1 = ax.bar(x - width/2, reference, width, label='Reference', color='#7DB8DE', edgecolor='black', linewidth=1.2)
bars2 = ax.bar(x + width/2, pipeline, width, label='Pipeline', color='#70AD47', edgecolor='black', linewidth=1.2)

# Add value labels on bars
for bar in bars1:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{height:.1f}', ha='center', va='bottom', fontsize=10, weight='bold')

for bar, error in zip(bars2, errors):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{height:.1f}', ha='center', va='bottom', fontsize=10, weight='bold')
    ax.text(bar.get_x() + bar.get_width()/2., height/2,
            f'{error:+.1f}%', ha='center', va='center', fontsize=9, color='white', weight='bold')

# Formatting
ax.set_ylabel('Value', fontsize=12, weight='bold')
ax.set_title('Pipeline Validation: Reference vs Pipeline Output', fontsize=14, weight='bold', pad=20)
ax.set_xticks(x)
ax.set_xticklabels(metrics, fontsize=11)
ax.legend(fontsize=11, loc='upper right', frameon=True, shadow=True)
ax.grid(axis='y', alpha=0.3, linestyle='--')
ax.set_axisbelow(True)

plt.tight_layout()
plt.savefig('/Users/danielchang/code/research/docs/validation_comparison.png', dpi=150, bbox_inches='tight')
plt.savefig('/Users/danielchang/code/research/docs/validation_comparison.jpg', dpi=150, bbox_inches='tight')
print("✓ Generated validation_comparison.png and .jpg")
plt.close()
