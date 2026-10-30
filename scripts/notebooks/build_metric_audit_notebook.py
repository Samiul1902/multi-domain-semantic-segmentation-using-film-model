"""Build + execute notebooks/evaluation/project_evaluation_metrics_audit.ipynb.

16 required sections. Reads only saved artifacts; performs no training and no inference.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(r"D:/Softfors/jup")
NB_PATH = ROOT / "notebooks" / "evaluation" / "project_evaluation_metrics_audit.ipynb"
NB_PATH.parent.mkdir(parents=True, exist_ok=True)

md = lambda s: nbformat.v4.new_markdown_cell(s.strip("\n"))
code = lambda s: nbformat.v4.new_code_cell(s.strip("\n"))
cells = []

cells.append(md(r"""
# Project-Wide Evaluation-Metrics Audit, Standardization and Descriptive Backfill

Scope: the completed KUB research chain (Phases 09–14 and the post-Phase14 H3
training / supply / downstream steps) up to the state
`H3_DOWNSTREAM_EVALUATION_COMPLETE__FORMAL_ADJUDICATION_PENDING`.

This notebook is an **audit + standardization** record. It performs **no training,
no inference and no TEST access**, and it does not change any frozen gate.

**Terminal state:** `PROJECT_EVALUATION_METRICS_AUDIT_COMPLETE__H3_ADJUDICATION_PENDING`
"""))

# 1
cells.append(md("## 1. Scope"))
cells.append(code(r"""
import json, hashlib, sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path('D:/Softfors/jup')
sys.path.insert(0, str(ROOT))
AUDITS = ROOT / 'reports' / 'audits'
TABLES = ROOT / 'reports' / 'tables'
FIGDIR = ROOT / 'reports' / 'figures'
FIGDIR.mkdir(parents=True, exist_ok=True)

def load_json(p): return json.loads((ROOT / p).read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()

inv = load_json('reports/audits/project_evaluation_metrics_inventory.json')
policy = load_json('reports/audits/project_evaluation_metric_policy.json')
empty_pol = load_json('reports/audits/evaluation_empty_mask_policy.json')
registry = load_json('reports/audits/project_metric_registry.json')
backfill = load_json('reports/audits/project_evaluation_metrics_backfill.json')
proposal = load_json('reports/audits/project_evaluation_proposal_metrics_backfill.json')

summary_df = pd.read_csv(TABLES / 'project_evaluation_segmentation_summary.csv')
perimg_df = pd.read_csv(TABLES / 'project_evaluation_per_image_metrics.csv')
size_df = pd.read_csv(TABLES / 'project_evaluation_component_recall_by_size.csv')
cov_df = pd.read_csv(TABLES / 'project_evaluation_coverage_sensitivity.csv')
paired_df = pd.read_csv(TABLES / 'project_evaluation_paired_comparisons.csv')
conf = load_json('reports/tables/project_evaluation_confusion_matrices.json')
prop_summary = pd.read_csv(TABLES / 'project_evaluation_proposal_metrics_summary.csv')
curves = load_json('reports/tables/project_evaluation_proposal_curves.json')

print('Audited scope:', inv['scope'])
print('Inventory rows:', len(inv['rows']))
print('Registry metrics:', len(registry['metrics']))
print('Backfill status:', backfill['status'])
print('Proposal backfill status:', proposal['status'])
print('TEST reads:', backfill['governance']['test_reads'], '| external:', backfill['governance']['external_test_reads'])
"""))

# 2
cells.append(md("## 2. Metric-Domain Taxonomy"))
cells.append(code(r"""
display(pd.DataFrame(list(inv['metric_domains'].items()), columns=['code', 'metric_domain']))
print()
print('Policy label rule:', policy['label_rule'])
print('Policy distance-unit rule:', policy['distance_unit_rule'])
"""))

# 3
cells.append(md("## 3. Confusion-Matrix Policy"))
cells.append(code(r"""
rows = []
for task, d in policy['policies'].items():
    rows.append({'task_type': task, 'confusion_matrix': d['confusion_matrix'],
                 'form': d['form'], 'reason': d.get('reason', '')})
display(pd.DataFrame(rows))
print()
print('Empty-mask policy principle:', empty_pol['principle'])
display(pd.DataFrame([{'case': k, 'dice': v.get('dice'), 'recall': v.get('recall'),
                       'specificity': v.get('specificity'), 'hd95': v.get('hd95')}
                      for k, v in empty_pol['cases'].items()]))
"""))

# 4
cells.append(md("## 4. Current Phase / Step Inventory"))
cells.append(code(r"""
inv_df = pd.DataFrame(inv['rows'])
display(inv_df[['phase_or_step', 'task_type', 'metric_domains', 'requires_new_inference', 'status']])
"""))

# 5
cells.append(md("## 5. Existing-vs-Missing Metric Matrix"))
cells.append(code(r"""
inv_csv = pd.read_csv(TABLES / 'project_evaluation_metrics_inventory.csv')
display(inv_csv[['phase_or_step', 'existing_metrics', 'missing_recommended_metrics', 'status']])
"""))

# 6
cells.append(md("## 6. Derivability Matrix"))
cells.append(code(r"""
der = inv_csv[['phase_or_step', 'derivable_from_saved_artifacts', 'requires_new_inference',
               'scientifically_appropriate', 'usable_for_formal_adjudication']].copy()
display(der)
print()
print('Key finding: no per-pixel masks or probability maps were persisted by the historical')
print('evaluators, so pixel confusion / boundary / calibration metrics were NOT derivable')
print('from saved artifacts. They were obtained through ONE logged safe VAL replay.')
print('Replay verdict:', backfill['safe_replay_rule']['verdict'])
"""))

# 7
cells.append(md("## 7. Segmentation Metrics"))
cells.append(code(r"""
cols = ['arm', 'pooled_dice', 'pooled_iou', 'pooled_precision', 'pooled_recall', 'pooled_specificity',
        'pooled_npv', 'pooled_accuracy', 'pooled_balanced_accuracy', 'pooled_mcc', 'pooled_cohen_kappa',
        'pooled_tp', 'pooled_tn', 'pooled_fp', 'pooled_fn']
display(summary_df[[c for c in cols if c in summary_df.columns]])
print()
print('Image-level (mean / median / std / IQR / min / max / 95% bootstrap CI) for Dice:')
dcols = ['arm', 'image_mean_dice', 'image_median_dice', 'image_std_dice', 'image_iqr_dice',
         'image_min_dice', 'image_max_dice', 'dice_ci_low', 'dice_ci_high']
display(summary_df[[c for c in dcols if c in summary_df.columns]])
print()
print('CAUTION: under heavy class imbalance accuracy/specificity alone are not evidence of quality.')
print('Positive (foreground) pixel fraction per arm:')
display(summary_df[['arm', 'positive_fraction']])
"""))

cells.append(md("### Figure 1 — Raw pixel confusion matrices (counts)"))
cells.append(code(r"""
arms = list(conf.keys())
fig, axes = plt.subplots(1, len(arms), figsize=(4.2 * len(arms), 4.2))
if len(arms) == 1: axes = [axes]
for ax, a in zip(axes, arms):
    m = np.array(conf[a]['matrix_raw'], dtype=float)
    ax.imshow(np.log10(m + 1), cmap='Blues')
    for i in range(2):
        for j in range(2):
            ax.text(j, i, f'{int(m[i, j]):,}', ha='center', va='center', fontsize=11,
                    color='black' if m[i, j] < m.max() * 0.6 else 'white')
    ax.set_xticks([0, 1]); ax.set_xticklabels(['Pred BG', 'Pred FG'])
    ax.set_yticks([0, 1]); ax.set_yticklabels(['GT BG', 'GT FG'])
    ax.set_title(f'{a}\n(raw counts, log color)')
plt.tight_layout(); plt.savefig(str(FIGDIR / 'project_metrics_fig1_confusion_raw.png'), dpi=150, bbox_inches='tight'); plt.show()
print('Figure 1 saved.')
"""))

cells.append(md("### Figure 2 — Row-normalized pixel confusion matrices"))
cells.append(code(r"""
fig, axes = plt.subplots(1, len(arms), figsize=(4.2 * len(arms), 4.2))
if len(arms) == 1: axes = [axes]
for ax, a in zip(axes, arms):
    m = np.array(conf[a]['matrix_row_normalized'], dtype=float)
    im = ax.imshow(m, cmap='Blues', vmin=0, vmax=1)
    for i in range(2):
        for j in range(2):
            ax.text(j, i, f'{m[i, j]:.4f}', ha='center', va='center', fontsize=11,
                    color='black' if m[i, j] < 0.6 else 'white')
    ax.set_xticks([0, 1]); ax.set_xticklabels(['Pred BG', 'Pred FG'])
    ax.set_yticks([0, 1]); ax.set_yticklabels(['GT BG', 'GT FG'])
    ax.set_title(f'{a}\n(row-normalized)')
plt.tight_layout(); plt.savefig(str(FIGDIR / 'project_metrics_fig2_confusion_normalized.png'), dpi=150, bbox_inches='tight'); plt.show()
print('Figure 2 saved.')
"""))

# 8
cells.append(md("## 8. Detection / Localization Metrics"))
cells.append(code(r"""
display(size_df)
print()
display(cov_df)
print()
display(prop_summary)
print()
for arm, d in curves.items():
    if d.get('pr_curve_meaningful') is False:
        print(f'{arm}: PR/FROC NOT MEANINGFUL -> {d.get("pr_curve_not_meaningful_reason")}')
"""))

cells.append(md("### Figure 3 — Component detection recall by size stratum"))
cells.append(code(r"""
fig, ax = plt.subplots(figsize=(10, 5.5))
sizes = ['TINY', 'SMALL', 'MEDIUM', 'LARGE']
arms_c = sorted(size_df['arm'].unique())
x = np.arange(len(sizes)); w = 0.8 / max(1, len(arms_c))
for i, a in enumerate(arms_c):
    vals = [float(size_df[(size_df['arm'] == a) & (size_df['size_stratum'] == s)]['detection_recall'].iloc[0])
            if len(size_df[(size_df['arm'] == a) & (size_df['size_stratum'] == s)]) else 0.0 for s in sizes]
    ax.bar(x + i * w - 0.4 + w / 2, vals, w, label=a)
ax.set_xticks(x); ax.set_xticklabels(sizes)
ax.set_ylabel('component detection recall (>=1 px)'); ax.set_ylim(0, 1.05)
ax.set_title('Component detection recall by size stratum (frozen detection domain)')
ax.legend(fontsize=8)
plt.tight_layout(); plt.savefig(str(FIGDIR / 'project_metrics_fig3_component_recall_by_size.png'), dpi=150, bbox_inches='tight'); plt.show()
print('Figure 3 saved.')
"""))

cells.append(md("### Figure 4 — Precision-Recall curve (Phase-13B localizer proposals)"))
cells.append(code(r"""
p13 = curves.get('PHASE13B_LOCALIZER', {})
if p13.get('pr_curve'):
    pc = p13['pr_curve']
    order = np.argsort(pc['recall'])
    rec = np.array(pc['recall'])[order]; prec = np.array(pc['precision'])[order]
    fig, ax = plt.subplots(figsize=(7, 5.5))
    ax.plot(rec, prec, marker='.', ms=3, label=f"Phase-13B (AP={p13['average_precision_descriptive']:.4f})")
    ax.axvline(x=0.0, color='gray', lw=0.8)
    ax.set_xlabel('recall (proposal-level)'); ax.set_ylabel('precision (proposal-level)')
    ax.set_title('Descriptive PR curve — Phase-13B localizer proposals\n(DESCRIPTIVE ONLY; frozen threshold not re-selected)')
    ax.set_xlim(0, 1.02); ax.set_ylim(0, 1.02); ax.legend()
    plt.tight_layout(); plt.savefig(str(FIGDIR / 'project_metrics_fig4_pr_curve_phase13b.png'), dpi=150, bbox_inches='tight'); plt.show()
    print('Figure 4 saved.')
else:
    print('PR curve not available.')
"""))

cells.append(md("### Figure 5 — FROC curve (Phase-13B localizer proposals)"))
cells.append(code(r"""
froc = p13.get('froc_curve')
if froc:
    fig, ax = plt.subplots(figsize=(7, 5.5))
    ax.plot(froc['fp_per_image'], froc['sensitivity'], marker='.', ms=3)
    ax.set_xlabel('false positives per image'); ax.set_ylabel('sensitivity (proposal-level)')
    ax.set_title('Descriptive FROC — Phase-13B localizer proposals\n(DESCRIPTIVE ONLY; operating point not re-selected)')
    plt.tight_layout(); plt.savefig(str(FIGDIR / 'project_metrics_fig5_froc_phase13b.png'), dpi=150, bbox_inches='tight'); plt.show()
    print('Figure 5 saved.')
else:
    print('FROC not available.')
"""))

# 9
cells.append(md("## 9. Boundary Metrics"))
cells.append(code(r"""
bcols = ['arm', 'image_mean_hd95', 'image_median_hd95', 'hd95_ci_low', 'hd95_ci_high', 'n_valid_hd95',
         'image_mean_assd', 'assd_ci_low', 'assd_ci_high', 'n_valid_assd',
         'image_mean_surface_dice', 'surface_dice_ci_low', 'surface_dice_ci_high', 'n_valid_surface_dice']
display(summary_df[[c for c in bcols if c in summary_df.columns]])
print()
print('UNITS: pixels. pixel_spacing_available =', backfill['pixel_spacing_available'])
print('surface tolerance (px):', backfill['surface_tolerance_px'])
print('boundary crop margin (px):', backfill['boundary_crop_margin_px'])
"""))

cells.append(md("### Figure 6 — HD95 and surface Dice distributions"))
cells.append(code(r"""
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
for a in sorted(perimg_df['arm'].unique()):
    v = perimg_df[perimg_df['arm'] == a]['hd95'].astype(float).dropna()
    if len(v): ax1.hist(v, bins=25, alpha=0.5, label=a)
    w = perimg_df[perimg_df['arm'] == a]['surface_dice'].astype(float).dropna()
    if len(w): ax2.hist(w, bins=25, alpha=0.5, label=a)
ax1.set_xlabel('HD95 (pixels)'); ax1.set_ylabel('images'); ax1.set_title('HD95 distribution (pixels)'); ax1.legend(fontsize=8)
ax2.set_xlabel('surface Dice @2 px'); ax2.set_ylabel('images'); ax2.set_title('Surface Dice distribution'); ax2.legend(fontsize=8)
plt.tight_layout(); plt.savefig(str(FIGDIR / 'project_metrics_fig6_boundary_distributions.png'), dpi=150, bbox_inches='tight'); plt.show()
print('Figure 6 saved.')
"""))

# 10
cells.append(md("## 10. Calibration Metrics"))
cells.append(code(r"""
ccols = ['arm', 'brier', 'ece', 'mce', 'roc_auc', 'average_precision', 'positive_fraction']
display(summary_df[[c for c in ccols if c in summary_df.columns]])
print()
print('Calibration note:', backfill['calibration_quantization_note'])
print('Bins:', backfill['calibration_bins'])
"""))

cells.append(md("### Figure 7 — Reliability diagrams (pixel-level)"))
cells.append(code(r"""
fig, axes = plt.subplots(1, len(arms), figsize=(4.2 * len(arms), 4.2))
if len(arms) == 1: axes = [axes]
for ax, a in zip(axes, arms):
    rb = conf[a]['calibration']['reliability_bins']
    n = np.array(rb['bin_count'], dtype=float)
    c = np.array([np.nan if v is None else v for v in rb['bin_confidence']], dtype=float)
    acc = np.array([np.nan if v is None else v for v in rb['bin_accuracy']], dtype=float)
    m = (n > 0) & ~np.isnan(c)
    ax.plot([0, 1], [0, 1], 'k--', lw=1)
    if m.any():
        ax.scatter(c[m], acc[m], s=np.clip(n[m] / max(1, n[m].max()) * 120, 4, 120), alpha=0.75)
    ax.set_xlabel('mean predicted probability'); ax.set_ylabel('empirical foreground fraction')
    ax.set_title(f"{a}\nBrier={conf[a]['calibration']['brier']:.5f}  ECE={conf[a]['calibration']['ece']:.5f}")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
plt.tight_layout(); plt.savefig(str(FIGDIR / 'project_metrics_fig7_reliability.png'), dpi=150, bbox_inches='tight'); plt.show()
print('Figure 7 saved.')
"""))

# 11
cells.append(md("## 11. Uncertainty Metrics"))
cells.append(code(r"""
print('Bootstrap configuration:', json.dumps(backfill['bootstrap']))
print()
dcols = ['arm', 'image_mean_dice', 'dice_ci_low', 'dice_ci_high', 'image_mean_recall', 'recall_ci_low', 'recall_ci_high',
         'image_mean_precision', 'precision_ci_low', 'precision_ci_high', 'image_mean_specificity', 'specificity_ci_low', 'specificity_ci_high']
display(summary_df[[c for c in dcols if c in summary_df.columns]])
print()
display(paired_df)
print()
print('All paired statistics are labelled:', backfill['metric_labels']['paired_statistics'])
"""))

cells.append(md("### Figure 8 — Bootstrap 95% CI forest plot (Dice)"))
cells.append(code(r"""
fig, ax = plt.subplots(figsize=(8, 4.5))
y = np.arange(len(summary_df))
ax.errorbar(summary_df['image_mean_dice'], y,
            xerr=[summary_df['image_mean_dice'] - summary_df['dice_ci_low'],
                  summary_df['dice_ci_high'] - summary_df['image_mean_dice']],
            fmt='o', capsize=5, color='#e67e22')
ax.set_yticks(y); ax.set_yticklabels(summary_df['arm'])
ax.set_xlabel('mean per-image Dice (95% bootstrap CI)')
ax.set_title('Descriptive uncertainty — mean per-image Dice by arm')
plt.tight_layout(); plt.savefig(str(FIGDIR / 'project_metrics_fig8_dice_forest.png'), dpi=150, bbox_inches='tight'); plt.show()
print('Figure 8 saved.')
"""))

cells.append(md("### Figure 9 — Paired per-image Dice difference (H3 - GLOBAL)"))
cells.append(code(r"""
piv = perimg_df.pivot_table(index='sample_id', columns='arm', values='dice')
if 'H3_DOWNSTREAM' in piv and 'GLOBAL' in piv:
    d = (piv['H3_DOWNSTREAM'] - piv['GLOBAL']).astype(float)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
    ax1.hist(d, bins=30, color='#2980b9', edgecolor='black', linewidth=0.4)
    ax1.axvline(0, color='black', lw=1)
    ax1.axvline(float(d.mean()), color='red', linestyle='--', label=f'mean={d.mean():.4f}')
    ax1.set_xlabel('per-image Dice(H3) - Dice(GLOBAL)'); ax1.set_ylabel('images')
    ax1.set_title('Paired Dice difference'); ax1.legend()
    ax2.scatter(piv['GLOBAL'], piv['H3_DOWNSTREAM'], s=12, alpha=0.6)
    lim = [0, 1]; ax2.plot(lim, lim, 'k--', lw=1)
    ax2.set_xlabel('Dice GLOBAL'); ax2.set_ylabel('Dice H3 downstream'); ax2.set_title('Paired scatter')
    plt.tight_layout(); plt.savefig(str(FIGDIR / 'project_metrics_fig9_paired_dice_diff.png'), dpi=150, bbox_inches='tight'); plt.show()
    print('Figure 9 saved.')
else:
    print('Paired data unavailable.')
"""))

# 12
cells.append(md("## 12. H3 Descriptive Augmentation"))
cells.append(code(r"""
h3 = summary_df[summary_df['arm'] == 'H3_DOWNSTREAM'].iloc[0]
h3_ref = load_json('reports/audits/h3_downstream_evaluation.json')
print('FROZEN H3 FORMAL METRIC (unchanged):')
print('  TinyRecall_H3 =', h3_ref['formal_downstream']['TinyRecall_H3'], '=', h3_ref['formal_downstream']['TinyRecall_H3_fraction'])
print('  R_H3          =', h3_ref['formal_downstream']['R_H3'], '->', h3_ref['formal_downstream']['interpretation_band'])
print()
print('NEW DESCRIPTIVE H3 METRICS (label:', backfill['metric_labels']['h3_specific'], ')')
print('  pooled Dice           :', h3['pooled_dice'])
print('  pooled IoU            :', h3['pooled_iou'])
print('  pooled precision      :', h3['pooled_precision'])
print('  pooled recall         :', h3['pooled_recall'])
print('  pooled specificity    :', h3['pooled_specificity'])
print('  pooled MCC            :', h3['pooled_mcc'])
print('  pooled balanced acc   :', h3['pooled_balanced_accuracy'])
print('  HD95 (px) mean        :', h3.get('image_mean_hd95'))
print('  ASSD (px) mean        :', h3.get('image_mean_assd'))
print('  surface Dice @2px     :', h3.get('image_mean_surface_dice'))
print('  Brier / ECE / ROC-AUC :', h3['brier'], '/', h3['ece'], '/', h3['roc_auc'])
print('  component TP/FP/FN    :', h3['component_tp_total'], '/', h3['component_fp_total'], '/', h3['component_fn_total'])
print('  component precision   :', h3['component_precision_overall'])
print('  FP components / image :', h3['mean_fp_components_per_image'])
print('  Dice 95% CI           :', h3['dice_ci_low'], '-', h3['dice_ci_high'])
"""))

# 13
cells.append(md("## 13. Phase-14 Descriptive Augmentation"))
cells.append(code(r"""
p14 = summary_df[summary_df['arm'].isin(['GLOBAL', 'ORACLE_REGIONAL', 'PREDICTED_REGIONAL'])]
cols14 = ['arm', 'pooled_dice', 'pooled_iou', 'pooled_precision', 'pooled_recall', 'pooled_specificity',
          'pooled_mcc', 'image_mean_hd95', 'image_mean_surface_dice', 'brier', 'ece', 'roc_auc']
display(p14[[c for c in cols14 if c in p14.columns]])
print()
print('Phase-14 frozen references reproduced exactly by the replay:')
for arm, r in backfill['reproduction_gate'].items():
    print(f"  {arm}: dice {r['replayed_mean_dice']:.10f} vs frozen {r['frozen_reference']:.10f} -> {r['match']}")
"""))

# 14
cells.append(md("## 14. Reproducibility / Provenance"))
cells.append(code(r"""
prov = [
    ('project_evaluation_metrics_inventory.json', 'reports/audits/project_evaluation_metrics_inventory.json'),
    ('project_evaluation_metric_policy.json', 'reports/audits/project_evaluation_metric_policy.json'),
    ('evaluation_empty_mask_policy.json', 'reports/audits/evaluation_empty_mask_policy.json'),
    ('project_metric_registry.json', 'reports/audits/project_metric_registry.json'),
    ('project_evaluation_metrics_backfill.json', 'reports/audits/project_evaluation_metrics_backfill.json'),
    ('project_evaluation_proposal_metrics_backfill.json', 'reports/audits/project_evaluation_proposal_metrics_backfill.json'),
    ('project_evaluation_segmentation_summary.csv', 'reports/tables/project_evaluation_segmentation_summary.csv'),
    ('project_evaluation_per_image_metrics.csv', 'reports/tables/project_evaluation_per_image_metrics.csv'),
    ('project_evaluation_confusion_matrices.json', 'reports/tables/project_evaluation_confusion_matrices.json'),
    ('project_evaluation_paired_comparisons.csv', 'reports/tables/project_evaluation_paired_comparisons.csv'),
    ('src/metrics/evaluation_metrics.py', 'src/metrics/evaluation_metrics.py'),
]
display(pd.DataFrame([{'artifact': n, 'path': p, 'sha256': sha(p)} for n, p in prov]))
print()
print('Safe-replay rule checks:')
for k, v in backfill['safe_replay_rule'].items():
    print(f'  {k}: {v}')
"""))

# 15
cells.append(md("## 15. Future Metric Standard"))
cells.append(code(r"""
print('Registry:', registry['artifact'], '| version', registry['version'])
print('Module  :', registry['module'], '| sha', registry['module_sha256'][:16], '...')
print()
reg_df = pd.DataFrame(registry['metrics'])
display(reg_df[['name', 'domain', 'unit', 'aggregation', 'higher_is_better', 'prospective_gate', 'descriptive_only']])
print()
print('Rule:', registry['governance']['rule'])
"""))

# 16
cells.append(md("## 16. Current Governance State"))
cells.append(code(r"""
gov = {
    'terminal_state': 'PROJECT_EVALUATION_METRICS_AUDIT_COMPLETE__H3_ADJUDICATION_PENDING',
    'h3_state': 'H3_DOWNSTREAM_EVALUATION_COMPLETE__FORMAL_ADJUDICATION_PENDING',
    'frozen_gates_changed': False,
    'checkpoints_changed': False,
    'thresholds_changed': False,
    'notebook_07_status': 'NOT_CREATED__FORMAL_ADJUDICATION_PENDING_AUTHORIZATION',
    'phase_15_status': 'NOT_STARTED_AND_NOT_AUTHORIZED',
    'test_reads': 0,
    'external_test_reads': 0,
}
for k, v in gov.items():
    print(f'{k}: {v}')
"""))

cells.append(md("## Assertions"))
cells.append(code(r"""
# ── Governance ───────────────────────────────────────────────────────────────
assert backfill['governance']['test_reads'] == 0
assert backfill['governance']['external_test_reads'] == 0
assert backfill['governance']['training_executed'] is False
assert backfill['governance']['thresholds_changed'] is False
assert backfill['governance']['checkpoints_changed'] is False
assert backfill['governance']['frozen_gates_changed'] is False
assert backfill['governance']['phase15_status'] == 'NOT_STARTED_AND_NOT_AUTHORIZED'
assert proposal['governance']['inference_executed'] is False
assert proposal['governance']['threshold_selected_from_curves'] is False

# ── Safe-replay conditions ───────────────────────────────────────────────────
sr = backfill['safe_replay_rule']
for k in ['1_checkpoints_frozen_and_sha_verified', '2_evaluator_preprocessing_frozen',
          '3_no_test_access', '4_no_threshold_search', '5_strictly_descriptive_missing_metrics',
          '6_existing_primary_metrics_reproduced_first', '7_does_not_change_frozen_decisions',
          '8_explicitly_logged']:
    assert sr[k] is True, k

# ── Reproduction gate: every arm reproduced its frozen primary metric ────────
for arm, r in backfill['reproduction_gate'].items():
    assert r['match'] is True, f"{arm} dice mismatch"
    assert r['tiny_match'] is True, f"{arm} tiny detection mismatch"

# ── New metrics are labelled descriptive ─────────────────────────────────────
assert backfill['metric_labels']['all_new_metrics'] == 'DESCRIPTIVE_SUPPORTING_METRIC__NOT_PROSPECTIVE_GATE'
assert backfill['metric_labels']['h3_specific'] == 'DESCRIPTIVE_SUPPORTING_METRIC__NOT_H3_GATE'

# ── H3 formal metric unchanged ───────────────────────────────────────────────
h3_ref = load_json('reports/audits/h3_downstream_evaluation.json')
assert h3_ref['formal_downstream']['TinyRecall_H3_fraction'] == '59/72'
assert abs(h3_ref['formal_downstream']['R_H3'] - 2/15) < 1e-12

# ── Table cardinality ────────────────────────────────────────────────────────
assert len(summary_df) == 4
assert len(perimg_df) == 4 * 103
assert inv['rows']
assert len(registry['metrics']) >= 30

# ── Confusion matrices are real pixel counts ─────────────────────────────────
for a, d in conf.items():
    tot = d['raw_counts']['tn'] + d['raw_counts']['fp'] + d['raw_counts']['fn'] + d['raw_counts']['tp']
    assert tot == d['pooled_pixels'] > 0

print('\n✓ All project evaluation-metrics audit assertions passed.')
print('Terminal state: PROJECT_EVALUATION_METRICS_AUDIT_COMPLETE__H3_ADJUDICATION_PENDING')
"""))

nb = nbformat.v4.new_notebook(cells=cells)
nbformat.write(nb, str(NB_PATH))
print(f'Wrote {NB_PATH} ({len(nb.cells)} cells)')

print('Executing...')
client = NotebookClient(nb, kernel_name='jup-venv', timeout=900,
                        resources={'metadata': {'path': str(ROOT)}})
client.execute()
nbformat.write(nb, str(NB_PATH))

errors = 0
for i, c in enumerate(nb.cells):
    if c.cell_type == 'code':
        for o in c.get('outputs', []):
            if o.get('output_type') == 'error':
                errors += 1
                print(f'  ERROR cell {i}: {o.get("ename")}: {o.get("evalue")}')
counts = [c.get('execution_count') for c in nb.cells if c.cell_type == 'code']
mono = all(counts[i] == i + 1 for i in range(len(counts)))
print(f'Cells: {len(nb.cells)} | code cells: {len(counts)}')
print(f'Zero tracebacks: {"PASS" if errors == 0 else "FAIL"}')
print(f'Monotonic exec counts (1..{len(counts)}): {"PASS" if mono else "CHECK"}')
print('Audit notebook SHA:', hashlib.sha256(NB_PATH.read_bytes()).hexdigest())
