import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIG_DIR = ROOT / 'reports/figures/phase13b_learned_localizer'
FIG_DIR.mkdir(parents=True, exist_ok=True)

# Load data
v3_hist = pd.read_csv(ROOT / 'experiments/phase13b_kub_localizer_r512_s3_centernetfocal_seed42_v3/history.csv')
v3_search97 = pd.read_csv(ROOT / 'experiments/phase13b_kub_localizer_r512_s3_centernetfocal_seed42_v3/val_search_epoch097.csv')
v3_comp = pd.read_csv(ROOT / 'reports/tables/phase13b_centernet_v3_best_val_per_component.csv')
p13_size = pd.read_csv(ROOT / 'reports/tables/phase13_predicted_roi_size_summary.csv')
p13_sel = pd.read_csv(ROOT / 'reports/tables/phase13_predicted_roi_selected_config.csv').iloc[0]
stage4b_hist = pd.read_csv(ROOT / 'experiments/phase13b_kub_localizer_r512_s3_seed42_v3/history.csv')

epochs = v3_hist['epoch']

# Figure A: Train vs Validation Loss by Epoch
fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(epochs, v3_hist['train_loss'], label='Train Loss (CenterNet)', color='#1f77b4', lw=2)
ax.plot(epochs, v3_hist['val_loss'], label='Val Loss (CenterNet)', color='#ff7f0e', lw=2)
ax.set_xlabel('Epoch')
ax.set_ylabel('Loss')
ax.set_title('Phase 13B V3: Train vs Validation Loss (CenterNet Focal Loss)')
ax.grid(True, linestyle='--', alpha=0.6)
ax.legend()
plt.tight_layout()
fig.savefig(FIG_DIR / 'fig_a_loss_by_epoch.png', dpi=200)
plt.close(fig)

# Figure B: Tiny recall90 and overall recall90 vs Epoch
fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(epochs, v3_hist['val_tiny_recall90'], label='VAL Tiny Recall@90', color='#2ca02c', lw=2)
ax.plot(epochs, v3_hist['val_overall_recall90'], label='VAL Overall Recall@90', color='#9467bd', lw=2)
ax.axhline(0.50, color='r', linestyle=':', label='Stage-4C Target (0.50)')
ax.set_xlabel('Epoch')
ax.set_ylabel('Recall@90')
ax.set_title('Phase 13B V3: Validation Recall@90 over Epochs')
ax.grid(True, linestyle='--', alpha=0.6)
ax.legend()
plt.tight_layout()
fig.savefig(FIG_DIR / 'fig_b_recall_by_epoch.png', dpi=200)
plt.close(fig)

# Figure C: Hard-Tiny Recovery over Training
fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(epochs, v3_hist['val_hard_tiny_recovered90'], label='Hard Tiny Recovered (out of 16)', color='#d62728', lw=2)
ax.plot(epochs, v3_hist['val_global_empty_images_covered90'], label='Global Empty Covered (out of 7)', color='#8c564b', lw=2, linestyle='--')
ax.axhline(2, color='black', linestyle=':', label='Stage-4C Gate Threshold (>=2 hard tiny)')
ax.set_xlabel('Epoch')
ax.set_ylabel('Recovered Count')
ax.set_title('Phase 13B V3: Hard-Case Recovery vs Epoch')
ax.set_ylim(-0.2, 3.5)
ax.grid(True, linestyle='--', alpha=0.6)
ax.legend()
plt.tight_layout()
fig.savefig(FIG_DIR / 'fig_c_hard_cases_by_epoch.png', dpi=200)
plt.close(fig)

# Figure D: Mean and Median Max Heatmap Probability vs Epoch
fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(epochs, v3_hist['mean_max_heatmap'], label='Mean Max Heatmap Prob', color='#e377c2', lw=2)
ax.plot(epochs, v3_hist['median_max_heatmap'], label='Median Max Heatmap Prob', color='#7f7f7f', lw=2, linestyle='--')
ax.axhline(0.10, color='blue', linestyle=':', label='Initial Prior (p=0.10)')
ax.set_xlabel('Epoch')
ax.set_ylabel('Heatmap Probability')
ax.set_title('Phase 13B V3: Maximum Heatmap Probability Evolution')
ax.grid(True, linestyle='--', alpha=0.6)
ax.legend()
plt.tight_layout()
fig.savefig(FIG_DIR / 'fig_d_heatmap_probs_by_epoch.png', dpi=200)
plt.close(fig)

# Figure E: ROI-Area Burden vs Epoch
fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(epochs, v3_hist['mean_roi_area_fraction'], label='Mean Union ROI Area Fraction', color='#bcbd22', lw=2)
ax.axhline(0.10, color='r', linestyle=':', label='Feasibility Constraint (<=0.10)')
ax.set_xlabel('Epoch')
ax.set_ylabel('Area Fraction')
ax.set_title('Phase 13B V3: ROI Area Burden over Training')
ax.grid(True, linestyle='--', alpha=0.6)
ax.legend()
plt.tight_layout()
fig.savefig(FIG_DIR / 'fig_e_roi_area_by_epoch.png', dpi=200)
plt.close(fig)

# Figure F: Proposals/Image vs Epoch
fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(epochs, v3_hist['mean_proposals_per_image'], label='Mean Proposals per Image', color='#17becf', lw=2)
ax.axhline(5.0, color='r', linestyle=':', label='Feasibility Constraint (<=5.0)')
ax.set_xlabel('Epoch')
ax.set_ylabel('Proposals / Image')
ax.set_title('Phase 13B V3: Proposals Generated per Image')
ax.grid(True, linestyle='--', alpha=0.6)
ax.legend()
plt.tight_layout()
fig.savefig(FIG_DIR / 'fig_f_proposals_by_epoch.png', dpi=200)
plt.close(fig)

# Figure G: Simple Predicted ROI vs Learned Localizer Comparison
fig, ax = plt.subplots(figsize=(9, 5))
labels = ['Tiny Recall@90', 'Overall Recall@90', 'Mean Area (x100)', 'Proposals/Img']
simple_vals = [p13_sel['tiny_recall90'], p13_sel['overall_recall90'], p13_sel['mean_total_roi_area_fraction']*100, p13_sel['mean_proposals_per_image']]
best_v3 = v3_search97.loc[v3_search97['overall_recall90'].idxmax()]
learned_vals = [best_v3['tiny_recall90'], best_v3['overall_recall90'], best_v3['mean_roi_area_fraction']*100, best_v3['mean_proposals_per_image']]

x = np.arange(len(labels))
width = 0.35
ax.bar(x - width/2, simple_vals, width, label='Phase 13 Simple ROI (Thresh=0.5)', color='#4c72b0')
ax.bar(x + width/2, learned_vals, width, label='Phase 13B Learned V3 (Epoch 97)', color='#dd8452')
ax.set_ylabel('Metric Value')
ax.set_title('Phase 13 Simple Predicted ROI vs Phase 13B Learned Localizer V3')
ax.set_xticks(x)
ax.set_xticklabels(labels)
ax.grid(True, linestyle='--', alpha=0.6, axis='y')
ax.legend()
plt.tight_layout()
fig.savefig(FIG_DIR / 'fig_g_simple_vs_learned.png', dpi=200)
plt.close(fig)

# Figure H: Stage 4B (Focal+Dice) vs Stage 4C (CenterNet V3) Comparison
fig, ax = plt.subplots(figsize=(8, 5))
models = ['Stage 4B (Focal+Dice)', 'Stage 4C V3 (CenterNet)']
tiny_recalls = [0.0137, best_v3['tiny_recall90']]
overall_recalls = [0.0385, best_v3['overall_recall90']]
x = np.arange(len(models))
width = 0.35
ax.bar(x - width/2, tiny_recalls, width, label='Tiny Recall@90', color='#55a868')
ax.bar(x + width/2, overall_recalls, width, label='Overall Recall@90', color='#c44e52')
ax.axhline(0.50, color='r', linestyle=':', label='Promising Gate (0.50)')
ax.set_ylabel('Recall@90')
ax.set_title('Loss Comparison: Stage 4B (Focal+SoftDice) vs Stage 4C (CenterNet)')
ax.set_xticks(x)
ax.set_xticklabels(models)
ax.grid(True, linestyle='--', alpha=0.6, axis='y')
ax.legend()
plt.tight_layout()
fig.savefig(FIG_DIR / 'fig_h_stage4b_vs_centernet.png', dpi=200)
plt.close(fig)

# Figure I: Size-Stratum Recall Comparison
fig, ax = plt.subplots(figsize=(8, 5))
strata = ['TINY', 'SMALL', 'MEDIUM', 'LARGE']
p13_strata_rec = [p13_size.loc[p13_size['Size']==s, 'recall90'].values[0] for s in strata]
v3_strata_rec = [v3_comp.loc[v3_comp['kub_size_v1']==s, 'covered90'].mean() for s in strata]
x = np.arange(len(strata))
width = 0.35
ax.bar(x - width/2, p13_strata_rec, width, label='Phase 13 Simple ROI', color='#4c72b0')
ax.bar(x + width/2, v3_strata_rec, width, label='Phase 13B Learned V3', color='#dd8452')
ax.set_ylabel('Recall@90')
ax.set_title('Recall@90 by Component Size Stratum')
ax.set_xticks(x)
ax.set_xticklabels(strata)
ax.grid(True, linestyle='--', alpha=0.6, axis='y')
ax.legend()
plt.tight_layout()
fig.savefig(FIG_DIR / 'fig_i_size_strata.png', dpi=200)
plt.close(fig)

# Figure J: Multi-Component Localization Result
fig, ax = plt.subplots(figsize=(7, 5))
cats = ['Phase 13 Simple', 'Phase 13B Learned V3']
multi_vals = [0.70, 0.23] # Authoritative multi_component_recall90
bars = ax.bar(cats, multi_vals, color=['#4c72b0', '#dd8452'], width=0.5)
ax.set_ylabel('Multi-Component Recall@90')
ax.set_title('Multi-Component Image Localization Performance')
ax.set_ylim(0, 1.0)
for bar in bars:
    y = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2, y + 0.02, f'{y:.2f}', ha='center', va='bottom', fontweight='bold')
ax.grid(True, linestyle='--', alpha=0.6, axis='y')
plt.tight_layout()
fig.savefig(FIG_DIR / 'fig_j_multicomponent.png', dpi=200)
plt.close(fig)

print('All 10 figures created and saved successfully.')

