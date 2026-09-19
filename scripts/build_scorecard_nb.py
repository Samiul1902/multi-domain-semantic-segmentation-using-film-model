import nbformat as nbf
import json, os

nb = nbf.v4.new_notebook()
nb.metadata = {
    'kernelspec': {'display_name': 'Python 3 (ipykernel)', 'language': 'python', 'name': 'python3'},
    'language_info': {'name': 'python', 'version': '3.11.0'}
}

cells = []

cells.append(nbf.v4.new_markdown_cell("""# Project-Wide Trained Model Scorecard & Visual Provenance

This notebook presents an executive, aggregate visual summary of all trained models discovered across the KUB Kidney Stone Detection and Segmentation project.

**Models Included:**
1. **U-Net** (`phase9_kub_unet_baseline_seed42_512`): Foundational baseline with power-resume.
2. **Attention U-Net** (`phase10_kub_attention_unet_seed42_512`): Attention-gated baseline.
3. **UNet++** (`phase10_kub_unetpp_seed42_512`): Canonical baseline winner (Macro Dice: 0.7625, Global Object Recall: 92.17%).
4. **DeepLabV3+** (`phase10_kub_deeplabv3plus_seed42_512`): Atrous Spatial Pyramid Pooling baseline.
5. **CenterNet Localizer (Stage 4D)** (`phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_v1`): Frozen canonical localizer.
6. **Regional Refiner U-Net** (`phase14_diag_regional_unet_oracletrain_a3_seed42_v1`): Phase 14 regional crop segmentation refiner.

*Note:* In accordance with the Project-Wide Visualization Standard NV-1/NV-2, all detailed prediction cases are rendered in companion notebooks (`notebooks/retrospective/`).
"""))

cells.append(nbf.v4.new_code_cell("""import pandas as pd
import json, os
import matplotlib.pyplot as plt
from IPython.display import display, Image, Markdown

scorecard_path = '../reports/tables/trained_model_visual_scorecard.csv' if os.path.exists('../reports/tables/trained_model_visual_scorecard.csv') else 'reports/tables/trained_model_visual_scorecard.csv'
sc_df = pd.read_csv(scorecard_path)
print("=== TRAINED MODEL VISUAL SCORECARD ===")
display(sc_df)
"""))

cells.append(nbf.v4.new_markdown_cell("""## 1. Baseline Model Comparison & Strata Breakdown
Here we plot the validation macro dice and stratified object recall across the baseline architectures. UNet++ demonstrates superior tiny-stone recall (78.08%) and the lowest FP burden per image (1.53).
"""))

cells.append(nbf.v4.new_code_cell("""# Plot baseline architecture performance
baseline_models = ['U-Net', 'Attention U-Net', 'UNet++', 'DeepLabV3+']
b_df = sc_df[sc_df['model'].isin(baseline_models)].copy()

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Plot 1: Macro Dice & FP Burden
ax1 = axes[0]
bars1 = ax1.bar(b_df['model'], b_df['val_dice'].astype(float), color=['skyblue', 'lightgreen', 'coral', 'mediumpurple'], edgecolor='black')
ax1.set_title('Validation Macro Dice by Architecture', fontsize=12, fontweight='bold')
ax1.set_ylabel('Macro Dice')
ax1.set_ylim(0.70, 0.80)
for bar in bars1:
    yval = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2.0, yval + 0.002, f"{yval:.4f}", ha='center', va='bottom', fontweight='bold')

# Plot 2: Tiny Stone Recall
ax2 = axes[1]
bars2 = ax2.bar(b_df['model'], b_df['tiny_recall'].astype(float), color=['skyblue', 'lightgreen', 'coral', 'mediumpurple'], edgecolor='black')
ax2.set_title('Tiny Stone (<5mm) Object Recall', fontsize=12, fontweight='bold')
ax2.set_ylabel('Object Recall')
ax2.set_ylim(0.60, 0.85)
for bar in bars2:
    yval = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2.0, yval + 0.005, f"{yval:.4f}", ha='center', va='bottom', fontweight='bold')

plt.tight_layout()
os.makedirs('../reports/figures/scorecard', exist_ok=True)
os.makedirs('reports/figures/scorecard', exist_ok=True)
save_fig_path = 'reports/figures/scorecard/baseline_macro_dice_tiny_recall.png' if os.path.exists('reports') else '../reports/figures/scorecard/baseline_macro_dice_tiny_recall.png'
plt.savefig(save_fig_path, dpi=200, bbox_inches='tight')
display(fig)
plt.close(fig)
"""))

cells.append(nbf.v4.new_markdown_cell("""## 2. Multi-Stage Pipeline Evolution
The project advanced from monolithic full-field segmenters to a two-stage coarse-to-fine regional refinement pipeline:
- **Phase 10:** Global UNet++ establishes baseline full-field Dice of 0.6528 (Macro Dice 0.7625 across mixed split).
- **Phase 12:** Oracle ROI Upper Bound reveals potential Dice up to 0.7844 when high-resolution context is provided.
- **Phase 13B:** CenterNet Stage 4D learns to propose candidates, achieving 84.93% Tiny object recall with 1.76 proposals per image.
- **Phase 14:** Regional Refiner diagnostic reveals that crop-level uncalibrated false positives inside proposed ROIs reduce full-field Dice, motivating the Phase 15 loss function study.
"""))

cells.append(nbf.v4.new_code_cell("""# Plot pipeline performance progression
fig, ax = plt.subplots(figsize=(10, 5))
stages = ['Phase 10: Global UNet++', 'Phase 12: Oracle Upper Bound', 'Phase 14: Stage-4D Refiner']
dices = [0.6528, 0.7844, 0.6133]
colors = ['steelblue', 'forestgreen', 'darkorange']

bars = ax.bar(stages, dices, color=colors, edgecolor='black', width=0.5)
ax.set_ylabel('Full-Field Val Dice', fontsize=11, fontweight='bold')
ax.set_title('Progression of Full-Field Segmentation Performance Across Project Phases', fontsize=13, fontweight='bold')
ax.set_ylim(0.50, 0.85)
ax.axhline(0.6528, color='steelblue', linestyle='--', alpha=0.7, label='Global Baseline (0.6528)')

for bar in bars:
    yval = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2.0, yval + 0.005, f"{yval:.4f}", ha='center', va='bottom', fontweight='bold', fontsize=11)

ax.legend(loc='upper right')
plt.tight_layout()
fig_prog_path = 'reports/figures/scorecard/pipeline_dice_progression.png' if os.path.exists('reports') else '../reports/figures/scorecard/pipeline_dice_progression.png'
plt.savefig(fig_prog_path, dpi=200, bbox_inches='tight')
display(fig)
plt.close(fig)
"""))

cells.append(nbf.v4.new_markdown_cell("""## 3. Provenance & Artifact Hashes
All models are backed by cryptographically hashed checkpoints in `reports/audits/trained_model_visualization_registry.json`.
"""))

cells.append(nbf.v4.new_code_cell("""reg_path = '../reports/audits/trained_model_visualization_registry.csv' if os.path.exists('../reports/audits/trained_model_visualization_registry.csv') else 'reports/audits/trained_model_visualization_registry.csv'
reg_df = pd.read_csv(reg_path)
display(reg_df[['experiment_id', 'status', 'checkpoint_sha256', 'visualization_notebook']])
"""))

nb.cells = cells
with open('notebooks/01_trained_model_results_visual_scorecard.ipynb', 'w', encoding='utf-8') as f:
    nbf.write(nb, f)
print('Created notebooks/01_trained_model_results_visual_scorecard.ipynb!')

