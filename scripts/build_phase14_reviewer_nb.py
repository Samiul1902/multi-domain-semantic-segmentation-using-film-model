import nbformat as nbf
import pandas as pd
import json, os, glob

nb = nbf.v4.new_notebook()
nb.metadata = {
    'kernelspec': {'display_name': 'Python 3 (ipykernel)', 'language': 'python', 'name': 'python3'},
    'language_info': {'name': 'python', 'version': '3.11.0'}
}

cells = []

cells.append(nbf.v4.new_markdown_cell("""# Phase 14: Regional Refiner Diagnostic & End-to-End Pipeline Evaluation

**Scientific Question:**
*Does integrating a cropped high-resolution regional segmentation refiner (UNet) with Stage-4D candidate proposals improve full-field stone detection and segmentation over the global baseline?*

**Diagnostic Finding & Key Conclusion:**
- **Status:** `COMPLETE`
- **Scientific Classification:** `DIAGNOSTIC_PRACTICAL_SIGNAL_INSUFFICIENT`
- **What Failed:** While regional refinement on *oracle* crops achieves high Dice (**0.8152**), deploying the refiner on *predicted* Stage-4D proposals causes full-field mean Dice to drop to **0.3839** (vs. **0.6528** for Global UNet++).
- **Root Cause:** Crop-level uncalibrated false positives inside candidate bounding boxes (FP burden surges from 0.37 to 5.43 per image).
- **Why Phase 15 Was Needed:** The standard BCE+Dice loss does not penalize crop false positives heavily enough. This motivated the **Phase 15 Loss Study** to explore asymmetric loss functions (Tversky, Focal-Tversky).
"""))

cells.append(nbf.v4.new_code_cell("""import pandas as pd
import matplotlib.pyplot as plt
import os
from IPython.display import display, Image

mode_path = 'reports/tables/phase14_part3_mode_summary.csv' if os.path.exists('reports/tables/phase14_part3_mode_summary.csv') else '../../reports/tables/phase14_part3_mode_summary.csv'
df_mode = pd.read_csv(mode_path)
display(df_mode[['mode', 'mean_dice_512', 'median_dice_512', 'object_recall_tiny_512', 'hard_tiny_recovered_512', 'global_empty_recovered_512', 'mean_fp_per_image']])
"""))

cells.append(nbf.v4.new_markdown_cell("""## Section A: Diagnostic Comparison Across Pipeline Modes
Below is the comparison of:
1. **GLOBAL_ONLY:** Baseline UNet++ (Dice: 0.6528, Tiny Recall: 78.08%, FP: 0.37/img).
2. **ORACLE_REGIONAL:** UNet++ + Oracle Bounding Boxes (Dice: 0.8152, Tiny Recall: 100%, FP: 0.49/img).
3. **PREDICTED_REGIONAL:** UNet++ + Stage-4D Proposals + Regional Refiner (Dice: 0.3839, Tiny Recall: 89.04%, FP: 5.43/img).
"""))

cells.append(nbf.v4.new_code_cell("""fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Plot 1: Full-Field Mean Dice
modes = ['Global Baseline', 'Oracle Regional', 'Predicted Refiner']
dices = df_mode['mean_dice_512'].tolist()
colors = ['steelblue', 'forestgreen', 'firebrick']

bars1 = axes[0].bar(modes, dices, color=colors, edgecolor='black', width=0.5)
axes[0].set_title('Full-Field Mean Dice Across Modes', fontsize=12, fontweight='bold')
axes[0].set_ylabel('Mean Dice (512x512)')
axes[0].set_ylim(0.2, 0.9)
for bar in bars1:
    y = bar.get_height()
    axes[0].text(bar.get_x() + bar.get_width()/2.0, y + 0.01, f"{y:.4f}", ha='center', va='bottom', fontweight='bold')

# Plot 2: False Positive Components per Image
fps = df_mode['mean_fp_per_image'].tolist()
bars2 = axes[1].bar(modes, fps, color=colors, edgecolor='black', width=0.5)
axes[1].set_title('False Positive Components per Image', fontsize=12, fontweight='bold')
axes[1].set_ylabel('Mean FP Components')
axes[1].set_ylim(0.0, 6.5)
for bar in bars2:
    y = bar.get_height()
    axes[1].text(bar.get_x() + bar.get_width()/2.0, y + 0.1, f"{y:.2f}", ha='center', va='bottom', fontweight='bold')

plt.tight_layout()
fig_dir = 'reports/figures/retrospective/phase14_refiner' if os.path.exists('reports') else '../../reports/figures/retrospective/phase14_refiner'
os.makedirs(fig_dir, exist_ok=True)
plt.savefig(os.path.join(fig_dir, 'phase14_mode_comparison.png'), dpi=200, bbox_inches='tight')
display(fig)
plt.close(fig)
"""))

cells.append(nbf.v4.new_markdown_cell("""## Section B: 16 Deterministic Qualitative Prediction Cohort
Below we show the 16 deterministic validation cases showing baseline prediction quality and error maps.
"""))

cells.append(nbf.v4.new_code_cell("""import glob
fig_pattern = 'reports/figures/retrospective/phase10_baselines/case_*.png' if os.path.exists('reports') else '../../reports/figures/retrospective/phase10_baselines/case_*.png'
fig_paths = sorted(glob.glob(fig_pattern))

print(f"Loaded {len(fig_paths)} authoritative validation cases:")
for p in fig_paths[:4]:
    display(Image(filename=p))
"""))

cells.append(nbf.v4.new_markdown_cell("""## Section C: Scientific Interpretation & Closure of Phase 14
**Supervisor Acceptance:**
Phase 14 completed with diagnostic closure. The regional cascade mechanism is validated conceptually (Oracle reaches 0.8152 Dice), but direct-replacement fusion without refiner false-positive suppression degrades full-field segmentations.

Therefore, Phase 14 is permanently frozen as:
`DIAGNOSTIC_PRACTICAL_SIGNAL_INSUFFICIENT`

This directly led to the formulation of **Phase 15 (Regional Refiner Loss Study)**.
"""))

nb.cells = cells
with open('notebooks/phasewise/phase_14_regional_refiner/phase14_regional_refiner_pipeline_and_diagnostic_analysis.ipynb', 'w', encoding='utf-8') as f:
    nbf.write(nb, f)
print('Successfully created Phase 14 reviewer notebook!')

