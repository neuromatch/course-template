import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# Create a simple experimental setup schematic
fig, ax = plt.subplots(figsize=(8, 4))
ax.set_xlim(0, 10)
ax.set_ylim(0, 5)
ax.axis('off')

# Title
ax.text(5, 4.5, 'Experimental Setup', ha='center', fontsize=16, fontweight='bold')

# Stimulus presentation
rect1 = patches.FancyBboxPatch((0.5, 2.5), 2, 1.5, boxstyle="round,pad=0.1", 
                                edgecolor='black', facecolor='lightblue', linewidth=2)
ax.add_patch(rect1)
ax.text(1.5, 3.25, 'Stimulus\nPresentation', ha='center', va='center', fontsize=10)

# Arrow
arrow1 = patches.FancyArrowPatch((2.5, 3.25), (3.5, 3.25), 
                                 arrowstyle='->', mutation_scale=20, linewidth=2)
ax.add_patch(arrow1)

# Neural recording
rect2 = patches.FancyBboxPatch((3.5, 2.5), 2, 1.5, boxstyle="round,pad=0.1",
                                edgecolor='black', facecolor='lightcoral', linewidth=2)
ax.add_patch(rect2)
ax.text(4.5, 3.25, 'Neural\nRecording', ha='center', va='center', fontsize=10)

# Arrow
arrow2 = patches.FancyArrowPatch((5.5, 3.25), (6.5, 3.25),
                                 arrowstyle='->', mutation_scale=20, linewidth=2)
ax.add_patch(arrow2)

# Analysis
rect3 = patches.FancyBboxPatch((6.5, 2.5), 2, 1.5, boxstyle="round,pad=0.1",
                                edgecolor='black', facecolor='lightgreen', linewidth=2)
ax.add_patch(rect3)
ax.text(7.5, 3.25, 'Spike Train\nAnalysis', ha='center', va='center', fontsize=10)

# Timeline annotation
ax.text(1.5, 1.8, '5 conditions\n100 trials each', ha='center', fontsize=8, style='italic')
ax.text(4.5, 1.8, '20 neurons\n1 sec trials', ha='center', fontsize=8, style='italic')
ax.text(7.5, 1.8, 'Firing rates\nPSTH', ha='center', fontsize=8, style='italic')

plt.tight_layout()
plt.savefig('experimental_setup.png', dpi=150, bbox_inches='tight', facecolor='white')
print("Generated experimental_setup.png")
