"""Phasewise evaluation + visualization synchronization (post-audit).

Appends a phase-appropriate "Descriptive Evaluation and Visual Evidence" section
to each COMPLETED modeling/evaluation phasewise notebook, executes it, and records
old/new SHA-256.

Governance
----------
* No training, no model inference, no TEST access.
* Reads only already-saved artifacts (CSV / JSON / PNG).
* Notebook-only plotting from saved tables is allowed (no forward pass).
* Model identity is matched exactly: the central safe replay covers
  GLOBAL = Phase-10 UNet++, ORACLE_REGIONAL, PREDICTED_REGIONAL, H3_DOWNSTREAM.
  Metrics are attached ONLY to notebooks whose model is one of those arms.
* All added metrics carry DESCRIPTIVE_SUPPORTING_METRIC__NOT_PROSPECTIVE_GATE
  (or ...__NOT_H3_GATE / DESCRIPTIVE_POST_HOC_STATISTICAL_SUPPORT).

Usage:  python scripts/notebooks/sync_phasewise_evaluation_visualization.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(r"D:/Softfors/jup")
REC = ROOT / "reports" / "audits" / "phasewise_evaluation_visualization_sha_updates.json"
MARKER = "Descriptive Evaluation and Visual Evidence"

PREAMBLE = r'''
# ── Phasewise evaluation / visualization synchronization (post-audit) ─────────
import json as _json, hashlib as _hashlib
from pathlib import Path as _Path
import numpy as _np
import pandas as _pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as _plt
try:
    from IPython.display import display as _disp, Image as _Img
except Exception:
    _disp = print; _Img = None
_ROOT = _Path('D:/Softfors/jup')
_AUD = _ROOT / 'reports' / 'audits'
_TAB = _ROOT / 'reports' / 'tables'
_FIG = _ROOT / 'reports' / 'figures' / 'phasewise_sync'
_FIG.mkdir(parents=True, exist_ok=True)
def _sha(p): return _hashlib.sha256(_Path(p).read_bytes()).hexdigest()
def _load(p): return _json.loads(_Path(p).read_text(encoding='utf-8'))
def _show(p, w=840):
    if _Img is not None and _Path(p).exists():
        _disp(_Img(filename=str(p), width=w))
LBL      = 'DESCRIPTIVE_SUPPORTING_METRIC__NOT_PROSPECTIVE_GATE'
LBL_H3   = 'DESCRIPTIVE_SUPPORTING_METRIC__NOT_H3_GATE'
LBL_STAT = 'DESCRIPTIVE_POST_HOC_STATISTICAL_SUPPORT'
'''


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


# ─────────────────────────────────────────────────────────────────────────────
# Per-phase appendix specifications
# ─────────────────────────────────────────────────────────────────────────────
def spec_phase09():
    md = r"""
## Descriptive Evaluation and Visual Evidence — Phase 09 (UNet, clean-v3)

**Metric source / provenance.** All values below are read from already-saved
clean-v3 Phase-09 artifacts (`phase09_clean_v3_training_history.csv`,
`phase09_clean_v3_best_val_summary.csv`, `phase09_clean_v3_val_gallery_metrics.csv`).
No training and no inference was performed.

**Metric-domain label.** Aggregate epoch-level metrics are the authoritative
Phase-09 training-scope metrics. Any post-hoc added supporting value is labelled
`DESCRIPTIVE_SUPPORTING_METRIC__NOT_PROSPECTIVE_GATE`.

**Model-identity note (important).** The project-wide safe replay produced pixel
confusion, boundary and calibration metrics for four arms — `GLOBAL` (= **Phase-10
UNet++**), `ORACLE_REGIONAL`, `PREDICTED_REGIONAL`, `H3_DOWNSTREAM`. The Phase-09
model is a **UNet**, which is *not* one of those arms. Therefore per-pixel
confusion / boundary / calibration metrics are **not** attached here: doing so
would mix model identities. They are recorded as
`UNAVAILABLE_FROM_SAVED_ARTIFACTS` for the Phase-09 UNet.

**What this section does NOT prove.** These numbers describe a single-seed (42)
clean-v3 UNet run. They are not a superiority claim, not significance-tested, and
do not touch TEST.
"""
    code = r'''
prov = [
    ('phase09_clean_v3_training_history.csv', _TAB / 'phase09_clean_v3_training_history.csv'),
    ('phase09_clean_v3_best_val_summary.csv', _TAB / 'phase09_clean_v3_best_val_summary.csv'),
    ('phase09_clean_v3_val_gallery_metrics.csv', _TAB / 'phase09_clean_v3_val_gallery_metrics.csv'),
]
_disp(_pd.DataFrame([{'artifact': n, 'sha256': _sha(p)[:16], 'exists': p.exists()} for n, p in prov]))

hist = _pd.read_csv(_TAB / 'phase09_clean_v3_training_history.csv')
best = hist.loc[hist['val_macro_dice'].idxmax()]
_disp(_pd.DataFrame([{
    'epochs': int(hist['epoch'].max()), 'best_epoch': int(best['epoch']),
    'val_macro_dice': float(best['val_macro_dice']), 'val_macro_iou': float(best['val_macro_iou']),
    'val_macro_precision': float(best['val_macro_precision']), 'val_macro_recall': float(best['val_macro_recall']),
    'train_loss': float(best['train_loss']), 'val_loss': float(best['val_loss']),
    'metric_domain': 'TRAINING_OPTIMIZATION', 'label': LBL,
}]).round(6))

avail = _pd.DataFrame([
    {'metric_family': 'Dice / IoU / precision / recall', 'status': 'YES',
     'source': 'phase09_clean_v3_training_history.csv (epoch aggregate)'},
    {'metric_family': 'per-image Dice / IoU distribution', 'status': 'YES (16-case gallery)',
     'source': 'phase09_clean_v3_val_gallery_metrics.csv'},
    {'metric_family': 'specificity / balanced accuracy / MCC / kappa', 'status': 'UNAVAILABLE_FROM_SAVED_ARTIFACTS',
     'source': 'no per-pixel confusion persisted for the Phase-09 UNet'},
    {'metric_family': 'confusion matrix (raw / normalized)', 'status': 'UNAVAILABLE_FROM_SAVED_ARTIFACTS',
     'source': 'safe replay covers UNet++ (GLOBAL arm), not the Phase-09 UNet'},
    {'metric_family': 'boundary HD95 / ASSD / surface Dice', 'status': 'UNAVAILABLE_FROM_SAVED_ARTIFACTS',
     'source': 'no persisted masks; model identity mismatch'},
    {'metric_family': 'calibration Brier / ECE / reliability', 'status': 'UNAVAILABLE_FROM_SAVED_ARTIFACTS',
     'source': 'no persisted probability maps; model identity mismatch'},
    {'metric_family': 'proposal / localizer metrics', 'status': 'NA',
     'source': 'not a localization task in Phase 09'},
])
_disp(avail)

fig, (ax1, ax2) = _plt.subplots(1, 2, figsize=(13, 4.4))
ax1.plot(hist['epoch'], hist['train_loss'], label='train loss')
ax1.plot(hist['epoch'], hist['val_loss'], label='val loss')
ax1.axvline(int(best['epoch']), color='green', ls='--', lw=1, label=f"best ep {int(best['epoch'])}")
ax1.set_xlabel('epoch'); ax1.set_ylabel('loss'); ax1.set_title('Phase-09 UNet loss trajectory'); ax1.legend(fontsize=8)
ax2.plot(hist['epoch'], hist['val_macro_dice'], color='#c0392b')
ax2.axvline(int(best['epoch']), color='green', ls='--', lw=1)
ax2.scatter([best['epoch']], [best['val_macro_dice']], color='green', zorder=5)
ax2.set_xlabel('epoch'); ax2.set_ylabel('VAL macro Dice'); ax2.set_title('Phase-09 UNet VAL macro Dice')
_plt.tight_layout(); _p = _FIG / 'phase09_loss_and_dice.png'
_plt.savefig(str(_p), dpi=150, bbox_inches='tight'); _plt.show(); _show(_p)

gm = _pd.read_csv(_TAB / 'phase09_clean_v3_val_gallery_metrics.csv')
fig, ax = _plt.subplots(figsize=(7, 4.2))
ax.hist(gm['dice'].astype(float), bins=8, color='#2980b9', edgecolor='black', lw=0.4)
ax.set_xlabel('Dice'); ax.set_ylabel('gallery cases'); ax.set_title('Phase-09 UNet per-image Dice (16-case clean-v3 gallery)')
_plt.tight_layout(); _p = _FIG / 'phase09_gallery_dice_hist.png'
_plt.savefig(str(_p), dpi=150, bbox_inches='tight'); _plt.show(); _show(_p)

print('All values above are', LBL)
print('No training, no inference, no TEST access.')
'''
    return dict(md=md, code=code,
                sections=['Descriptive Evaluation and Visual Evidence — Phase 09 (UNet, clean-v3)'],
                tables=['Phase-09 best-epoch aggregate metrics', 'descriptive-metric availability matrix'],
                figures=['phase09_loss_and_dice.png', 'phase09_gallery_dice_hist.png'])


def spec_phase10():
    md = r"""
## Descriptive Evaluation and Visual Evidence — Phase 10 (four-model comparison)

**Metric source / provenance.** Central post-audit artifacts
(`project_evaluation_segmentation_summary.csv`,
`project_evaluation_confusion_matrices.json`,
`project_evaluation_paired_comparisons.csv`) plus the saved clean-v3 paired
per-case table (`phase10_clean_v3_paired_val_case_metrics.csv`). No inference.

**Model-identity match (critical).** The central `GLOBAL` arm is
**`phase10_kub_unetpp_seed42_512_clean_v3` (UNet++, epoch 70)**. Pixel confusion,
boundary and calibration metrics from the audit therefore apply **only to UNet++**.
The other three models (UNet, Attention U-Net, DeepLabV3+) have no persisted
per-pixel maps, so those metric families are `UNAVAILABLE_FROM_SAVED_ARTIFACTS`
for them — no metric is borrowed across models.

**What this section does NOT prove.** Single-seed (42) descriptive VAL evidence.
No winner is declared; no significance testing was performed (Phases 29/31 have
not run). TEST remains locked.
"""
    code = r'''
prov = [
    ('project_evaluation_segmentation_summary.csv', _TAB / 'project_evaluation_segmentation_summary.csv'),
    ('project_evaluation_confusion_matrices.json', _TAB / 'project_evaluation_confusion_matrices.json'),
    ('project_evaluation_paired_comparisons.csv', _TAB / 'project_evaluation_paired_comparisons.csv'),
    ('phase10_clean_v3_paired_val_case_metrics.csv', _TAB / 'phase10_clean_v3_paired_val_case_metrics.csv'),
]
_disp(_pd.DataFrame([{'artifact': n, 'sha256': _sha(p)[:16]} for n, p in prov if p.exists()]))

summ = _pd.read_csv(_TAB / 'project_evaluation_segmentation_summary.csv')
g = summ[summ['arm'] == 'GLOBAL'].iloc[0]
cols = ['pooled_dice', 'pooled_iou', 'pooled_precision', 'pooled_recall', 'pooled_specificity',
        'pooled_balanced_accuracy', 'pooled_mcc', 'pooled_cohen_kappa', 'pooled_tp', 'pooled_tn',
        'pooled_fp', 'pooled_fn', 'image_mean_hd95', 'image_mean_assd', 'image_mean_surface_dice',
        'brier', 'ece', 'roc_auc', 'average_precision', 'dice_ci_low', 'dice_ci_high']
row = {'model': 'UNet++ (GLOBAL arm)', 'metric_domain': 'PIXEL_SEGMENTATION', 'label': LBL}
row.update({c: g[c] for c in cols})
_disp(_pd.DataFrame([row]).round(6))

paired = _pd.read_csv(_TAB / 'phase10_clean_v3_paired_val_case_metrics.csv')
rows = []
for m in ['unet', 'attention_unet', 'unetpp', 'deeplabv3plus']:
    rows.append({'model': m, 'n': int(paired[f'{m}_dice'].notna().sum()),
                 'mean_dice': float(paired[f'{m}_dice'].mean()),
                 'mean_iou': float(paired[f'{m}_iou'].mean()),
                 'mean_precision': float(paired[f'{m}_precision'].mean()),
                 'mean_recall': float(paired[f'{m}_recall'].mean()),
                 'metric_domain': 'PIXEL_SEGMENTATION', 'label': LBL})
_disp(_pd.DataFrame(rows).round(6))

avail = _pd.DataFrame([
    {'model': 'UNet++', 'confusion_matrix': 'YES', 'boundary': 'YES', 'calibration': 'YES',
     'reason': 'GLOBAL arm of the central safe replay'},
    {'model': 'UNet', 'confusion_matrix': 'UNAVAILABLE_FROM_SAVED_ARTIFACTS', 'boundary': 'UNAVAILABLE_FROM_SAVED_ARTIFACTS',
     'calibration': 'UNAVAILABLE_FROM_SAVED_ARTIFACTS', 'reason': 'no persisted per-pixel maps for this model'},
    {'model': 'Attention U-Net', 'confusion_matrix': 'UNAVAILABLE_FROM_SAVED_ARTIFACTS', 'boundary': 'UNAVAILABLE_FROM_SAVED_ARTIFACTS',
     'calibration': 'UNAVAILABLE_FROM_SAVED_ARTIFACTS', 'reason': 'no persisted per-pixel maps for this model'},
    {'model': 'DeepLabV3+', 'confusion_matrix': 'UNAVAILABLE_FROM_SAVED_ARTIFACTS', 'boundary': 'UNAVAILABLE_FROM_SAVED_ARTIFACTS',
     'calibration': 'UNAVAILABLE_FROM_SAVED_ARTIFACTS', 'reason': 'no persisted per-pixel maps for this model'},
])
_disp(avail)

conf = _load(_TAB / 'project_evaluation_confusion_matrices.json')
gc = conf['GLOBAL']
fig, axes = _plt.subplots(1, 2, figsize=(11, 4.3))
m_raw = _np.array(gc['matrix_raw'], dtype=float)
axes[0].imshow(_np.log10(m_raw + 1), cmap='Blues')
for i in range(2):
    for j in range(2):
        axes[0].text(j, i, f'{int(m_raw[i, j]):,}', ha='center', va='center', fontsize=10,
                     color='black' if m_raw[i, j] < m_raw.max() * 0.6 else 'white')
axes[0].set_xticks([0, 1]); axes[0].set_xticklabels(['Pred Background', 'Pred Foreground'])
axes[0].set_yticks([0, 1]); axes[0].set_yticklabels(['GT Background', 'GT Foreground'])
axes[0].set_title('UNet++ raw pixel confusion (counts)')
m_norm = _np.array(gc['matrix_row_normalized'], dtype=float)
axes[1].imshow(m_norm, cmap='Blues', vmin=0, vmax=1)
for i in range(2):
    for j in range(2):
        axes[1].text(j, i, f'{m_norm[i, j]:.4f}', ha='center', va='center', fontsize=10,
                     color='black' if m_norm[i, j] < 0.6 else 'white')
axes[1].set_xticks([0, 1]); axes[1].set_xticklabels(['Pred Background', 'Pred Foreground'])
axes[1].set_yticks([0, 1]); axes[1].set_yticklabels(['GT Background', 'GT Foreground'])
axes[1].set_title('UNet++ row-normalized confusion')
_plt.tight_layout(); _p = _FIG / 'phase10_unetpp_confusion.png'
_plt.savefig(str(_p), dpi=150, bbox_inches='tight'); _plt.show(); _show(_p)

fig, ax = _plt.subplots(figsize=(9, 4.6))
data = [paired[f'{m}_dice'].dropna().astype(float) for m in ['unet', 'attention_unet', 'unetpp', 'deeplabv3plus']]
try:
    ax.boxplot(data, tick_labels=['UNet', 'Attention U-Net', 'UNet++', 'DeepLabV3+'], showmeans=True)
except TypeError:
    ax.boxplot(data, labels=['UNet', 'Attention U-Net', 'UNet++', 'DeepLabV3+'], showmeans=True)
ax.set_ylabel('per-image Dice'); ax.set_title('Phase-10 clean-v3 per-image Dice by model (descriptive)')
_plt.tight_layout(); _p = _FIG / 'phase10_per_image_dice_by_model.png'
_plt.savefig(str(_p), dpi=150, bbox_inches='tight'); _plt.show(); _show(_p)

pc = _pd.read_csv(_TAB / 'project_evaluation_paired_comparisons.csv')
_disp(pc[['comparison', 'metric', 'n_pairs', 'mean_difference', 'ci_low', 'ci_high', 'label']])
print('All values above are', LBL, '| paired statistics are', LBL_STAT)
'''
    return dict(md=md, code=code,
                sections=['Descriptive Evaluation and Visual Evidence — Phase 10 (four-model comparison)'],
                tables=['UNet++ (GLOBAL arm) descriptive pixel/boundary/calibration metrics',
                        'clean-v3 four-model per-image Dice/IoU/precision/recall',
                        'per-model descriptive-metric availability'],
                figures=['phase10_unetpp_confusion.png', 'phase10_per_image_dice_by_model.png'])


def spec_phase11():
    md = r"""
## Descriptive Evaluation and Visual Evidence — Phase 11 (baseline failure analysis)

**Metric source / provenance.** Central post-audit component tables
(`project_evaluation_component_recall_by_size.csv`,
`project_evaluation_coverage_sensitivity.csv`,
`project_evaluation_per_component_metrics.csv`) filtered to the `GLOBAL` arm
(= Phase-10 UNet++), which is the baseline whose failures Phase 11 analyses.

**Why this domain.** Failure analysis is a detection/component question
(size-stratified recall, missed components, FP burden, boundary failure), not a
pixel-classification question. A TN-based confusion matrix is therefore **not**
forced here.

**What this section does NOT prove.** The size-stratified numbers are descriptive
VAL evidence for one frozen baseline. They do not establish causality and do not
touch TEST.
"""
    code = r'''
prov = [
    ('project_evaluation_component_recall_by_size.csv', _TAB / 'project_evaluation_component_recall_by_size.csv'),
    ('project_evaluation_coverage_sensitivity.csv', _TAB / 'project_evaluation_coverage_sensitivity.csv'),
    ('project_evaluation_per_component_metrics.csv', _TAB / 'project_evaluation_per_component_metrics.csv'),
]
_disp(_pd.DataFrame([{'artifact': n, 'sha256': _sha(p)[:16]} for n, p in prov if p.exists()]))

size = _pd.read_csv(_TAB / 'project_evaluation_component_recall_by_size.csv')
_disp(size[size['arm'] == 'GLOBAL'])
cov = _pd.read_csv(_TAB / 'project_evaluation_coverage_sensitivity.csv')
_disp(cov[cov['arm'] == 'GLOBAL'])

comp = _pd.read_csv(_TAB / 'project_evaluation_per_component_metrics.csv')
cg = comp[comp['arm'] == 'GLOBAL']
by = cg.groupby('size_stratum').agg(gt=('detection', 'size'), detected=('detection', 'sum')).reset_index()
by['missed'] = by['gt'] - by['detected']
by['recall'] = by['detected'] / by['gt']
by['metric_domain'] = 'OBJECT_COMPONENT_DETECTION'; by['label'] = LBL
_disp(by.round(6))

fig, ax = _plt.subplots(figsize=(8, 4.4))
order = ['TINY', 'SMALL', 'MEDIUM', 'LARGE']
vals = [float(by[by['size_stratum'] == s]['recall'].iloc[0]) for s in order]
ax.bar(order, vals, color='#8e44ad')
for i, v in enumerate(vals):
    ax.text(i, v + 0.01, f'{v:.3f}', ha='center', fontsize=9)
ax.set_ylim(0, 1.08); ax.set_ylabel('component detection recall (>=1 px)')
ax.set_title('Phase-11 baseline (UNet++ GLOBAL arm) component detection recall by size')
_plt.tight_layout(); _p = _FIG / 'phase11_recall_by_size.png'
_plt.savefig(str(_p), dpi=150, bbox_inches='tight'); _plt.show(); _show(_p)

pi = _pd.read_csv(_TAB / 'project_evaluation_per_image_metrics.csv')
gp = pi[pi['arm'] == 'GLOBAL']
hv = gp['hd95'].dropna().astype(float)
fig, (ax1, ax2) = _plt.subplots(1, 2, figsize=(12.5, 4.2))
ax1.hist(hv, bins=25, color='#e67e22', edgecolor='black', lw=0.4)
ax1.set_xlabel('HD95 (pixels)'); ax1.set_ylabel('images')
ax1.set_title('Phase-11 baseline boundary failure: HD95 (pixels)')
ax2.hist(gp['dice'].dropna().astype(float), bins=25, color='#16a085', edgecolor='black', lw=0.4)
ax2.set_xlabel('Dice'); ax2.set_ylabel('images'); ax2.set_title('Phase-11 baseline per-image Dice')
_plt.tight_layout(); _p = _FIG / 'phase11_boundary_and_dice.png'
_plt.savefig(str(_p), dpi=150, bbox_inches='tight'); _plt.show(); _show(_p)

print('All values above are', LBL)
'''
    return dict(md=md, code=code,
                sections=['Descriptive Evaluation and Visual Evidence — Phase 11 (baseline failure analysis)'],
                tables=['GLOBAL-arm component detection recall by size', 'GLOBAL-arm coverage sensitivity',
                        'GLOBAL-arm component TP/FN summary'],
                figures=['phase11_recall_by_size.png', 'phase11_boundary_and_dice.png'])


def spec_phase12():
    md = r"""
## Descriptive Evaluation and Visual Evidence — Phase 12 (oracle ROI upper bound)

**Metric source / provenance.** Central post-audit arms `GLOBAL` (= Phase-10
UNet++) and `ORACLE_REGIONAL` (GT-bbox proposals + frozen Phase-14 refiner), plus
the saved Phase-12 primary tables. No inference was performed in this notebook.

**Metric-domain label.** `PIXEL_SEGMENTATION` + `OBJECT_COMPONENT_DETECTION`.
Post-hoc added values are `DESCRIPTIVE_SUPPORTING_METRIC__NOT_PROSPECTIVE_GATE`;
the GLOBAL↔ORACLE paired difference is `DESCRIPTIVE_POST_HOC_STATISTICAL_SUPPORT`.

**Interpretation guard.** ORACLE_REGIONAL is a **diagnostic upper bound** obtained
from ground-truth bounding boxes. It is **not deployable performance** and must
never be reported as a method result.

**What this section does NOT prove.** It bounds what a perfect ROI supply could
buy; it does not show that any GT-free method attains it.
"""
    code = r'''
prov = [
    ('project_evaluation_segmentation_summary.csv', _TAB / 'project_evaluation_segmentation_summary.csv'),
    ('project_evaluation_confusion_matrices.json', _TAB / 'project_evaluation_confusion_matrices.json'),
    ('project_evaluation_paired_comparisons.csv', _TAB / 'project_evaluation_paired_comparisons.csv'),
    ('phase12_primary_global_vs_oracle_summary.csv', _TAB / 'phase12_primary_global_vs_oracle_summary.csv'),
]
_disp(_pd.DataFrame([{'artifact': n, 'sha256': _sha(p)[:16]} for n, p in prov if p.exists()]))

summ = _pd.read_csv(_TAB / 'project_evaluation_segmentation_summary.csv')
sub = summ[summ['arm'].isin(['GLOBAL', 'ORACLE_REGIONAL'])]
cols = ['arm', 'pooled_dice', 'pooled_iou', 'pooled_precision', 'pooled_recall', 'pooled_specificity',
        'pooled_balanced_accuracy', 'pooled_mcc', 'image_mean_hd95', 'image_mean_surface_dice',
        'brier', 'ece', 'roc_auc', 'dice_ci_low', 'dice_ci_high']
_disp(sub[cols].round(6))

size = _pd.read_csv(_TAB / 'project_evaluation_component_recall_by_size.csv')
_disp(size[size['arm'].isin(['GLOBAL', 'ORACLE_REGIONAL'])])

pc = _pd.read_csv(_TAB / 'project_evaluation_paired_comparisons.csv')
_disp(pc[pc['comparison'].str.contains('ORACLE')][['comparison', 'metric', 'n_pairs', 'mean_difference', 'ci_low', 'ci_high', 'wilcoxon_p', 'label']])

conf = _load(_TAB / 'project_evaluation_confusion_matrices.json')
fig, axes = _plt.subplots(2, 2, figsize=(11, 9))
for j, arm in enumerate(['GLOBAL', 'ORACLE_REGIONAL']):
    d = conf[arm]
    raw = _np.array(d['matrix_raw'], dtype=float); nrm = _np.array(d['matrix_row_normalized'], dtype=float)
    axes[0, j].imshow(_np.log10(raw + 1), cmap='Blues')
    for a in range(2):
        for b in range(2):
            axes[0, j].text(b, a, f'{int(raw[a, b]):,}', ha='center', va='center', fontsize=9,
                            color='black' if raw[a, b] < raw.max() * 0.6 else 'white')
    axes[0, j].set_xticks([0, 1]); axes[0, j].set_xticklabels(['Pred BG', 'Pred FG'])
    axes[0, j].set_yticks([0, 1]); axes[0, j].set_yticklabels(['GT BG', 'GT FG'])
    axes[0, j].set_title(f'{arm}\nraw counts (log color)')
    axes[1, j].imshow(nrm, cmap='Blues', vmin=0, vmax=1)
    for a in range(2):
        for b in range(2):
            axes[1, j].text(b, a, f'{nrm[a, b]:.4f}', ha='center', va='center', fontsize=9,
                            color='black' if nrm[a, b] < 0.6 else 'white')
    axes[1, j].set_xticks([0, 1]); axes[1, j].set_xticklabels(['Pred BG', 'Pred FG'])
    axes[1, j].set_yticks([0, 1]); axes[1, j].set_yticklabels(['GT BG', 'GT FG'])
    axes[1, j].set_title(f'{arm}\nrow-normalized')
_plt.tight_layout(); _p = _FIG / 'phase12_confusion_global_vs_oracle.png'
_plt.savefig(str(_p), dpi=150, bbox_inches='tight'); _plt.show(); _show(_p, 900)

pi = _pd.read_csv(_TAB / 'project_evaluation_per_image_metrics.csv')
piv = pi.pivot_table(index='sample_id', columns='arm', values='dice')
if 'GLOBAL' in piv and 'ORACLE_REGIONAL' in piv:
    d = (piv['ORACLE_REGIONAL'] - piv['GLOBAL']).astype(float)
    fig, ax = _plt.subplots(figsize=(8.5, 4.6))
    ax.hist(d, bins=30, color='#c0392b', edgecolor='black', lw=0.4)
    ax.axvline(0, color='black', lw=1)
    ax.axvline(float(d.mean()), color='blue', ls='--', label=f'mean={d.mean():.4f}')
    ax.set_xlabel('per-image Dice(ORACLE) - Dice(GLOBAL)'); ax.set_ylabel('images')
    ax.set_title('Phase-12 oracle benefit: paired per-image Dice difference (diagnostic upper bound)')
    ax.legend()
    _plt.tight_layout(); _p = _FIG / 'phase12_paired_oracle_benefit.png'
    _plt.savefig(str(_p), dpi=150, bbox_inches='tight'); _plt.show(); _show(_p)

print('ORACLE_REGIONAL is a DIAGNOSTIC UPPER BOUND, not deployable performance.')
print('All values above are', LBL, '| paired difference is', LBL_STAT)
'''
    return dict(md=md, code=code,
                sections=['Descriptive Evaluation and Visual Evidence — Phase 12 (oracle ROI upper bound)'],
                tables=['GLOBAL vs ORACLE_REGIONAL descriptive metrics', 'component recall by size (GLOBAL/ORACLE)',
                        'paired GLOBAL→ORACLE Dice difference'],
                figures=['phase12_confusion_global_vs_oracle.png', 'phase12_paired_oracle_benefit.png'])


def spec_phase13():
    md = r"""
## Descriptive Evaluation and Visual Evidence — Phase 13 (proposal / localizer)

**Metric source / provenance.** Central proposal-domain artifacts
(`project_evaluation_proposal_metrics_summary.csv`,
`project_evaluation_proposal_curves.json`) derived from the saved Phase-13B
per-proposal table, plus the saved size-stratified coverage table.

**Metric-domain label.** `LOCALIZATION_PROPOSAL_SUPPLY` +
`OBJECT_COMPONENT_DETECTION`. Added values are
`DESCRIPTIVE_SUPPORTING_METRIC__NOT_PROSPECTIVE_GATE`.

**No TN-based confusion matrix.** A proposal detector has no defensible
"true-negative" unit (background is unbounded), so a confusion matrix is
deliberately **not** produced here. Proposal quality is expressed as TP/FP
proposals, precision, FP/image, component recall and PR/FROC curves.

**Frozen operating point.** The PR/FROC curves are **descriptive**; the frozen
threshold is annotated only and is never re-selected from these curves.

**What this section does NOT prove.** These are single-seed descriptive VAL curves
for the frozen localizer; they are not a re-tuning of the operating point.
"""
    code = r'''
prov = [
    ('project_evaluation_proposal_metrics_summary.csv', _TAB / 'project_evaluation_proposal_metrics_summary.csv'),
    ('project_evaluation_proposal_curves.json', _TAB / 'project_evaluation_proposal_curves.json'),
    ('phase13_part1c_size_stratified_coverage.csv', _TAB / 'phase13_part1c_size_stratified_coverage.csv'),
]
_disp(_pd.DataFrame([{'artifact': n, 'sha256': _sha(p)[:16]} for n, p in prov if p.exists()]))

psum = _pd.read_csv(_TAB / 'project_evaluation_proposal_metrics_summary.csv')
_disp(psum[psum['arm'].str.contains('PHASE13B')])

cov = _pd.read_csv(_TAB / 'phase13_part1c_size_stratified_coverage.csv')
_disp(cov[['stratum', 'n_components', 'pixel_any_overlap_count', 'pixel_any_overlap_rate',
           'pixel_covered90_count', 'pixel_covered90_rate']])

curves = _load(_TAB / 'project_evaluation_proposal_curves.json')
p13 = curves.get('PHASE13B_LOCALIZER', {})
if p13.get('pr_curve'):
    pc = p13['pr_curve']
    order = _np.argsort(pc['recall'])
    rec = _np.array(pc['recall'])[order]; prec = _np.array(pc['precision'])[order]
    fig, (ax1, ax2) = _plt.subplots(1, 2, figsize=(13, 5))
    ax1.plot(rec, prec, marker='.', ms=3, color='#2980b9',
             label=f"AP={p13['average_precision_descriptive']:.4f}")
    ax1.set_xlabel('recall (proposal-level)'); ax1.set_ylabel('precision (proposal-level)')
    ax1.set_xlim(0, 1.02); ax1.set_ylim(0, 1.02)
    ax1.set_title('Phase-13B proposal PR curve (descriptive)'); ax1.legend()
    fr = p13.get('froc_curve')
    if fr:
        ax2.plot(fr['fp_per_image'], fr['sensitivity'], marker='.', ms=3, color='#c0392b')
        ax2.set_xlabel('false positives per image'); ax2.set_ylabel('sensitivity')
        ax2.set_title('Phase-13B proposal FROC (descriptive)')
    _plt.tight_layout(); _p = _FIG / 'phase13_pr_froc.png'
    _plt.savefig(str(_p), dpi=150, bbox_inches='tight'); _plt.show(); _show(_p)
else:
    print('PR curve unavailable for PHASE13B_LOCALIZER.')

for arm, d in curves.items():
    if d.get('pr_curve_meaningful') is False:
        print(f'{arm}: PR/FROC NOT MEANINGFUL -> {d.get("pr_curve_not_meaningful_reason")}')
print('Frozen operating threshold (annotated, not re-selected):', p13.get('operating_point_threshold'))
print('All values above are', LBL)
'''
    return dict(md=md, code=code,
                sections=['Descriptive Evaluation and Visual Evidence — Phase 13 (proposal / localizer)'],
                tables=['Phase-13B proposal metrics summary', 'Phase-13B size-stratified coverage'],
                figures=['phase13_pr_froc.png'])


def spec_phase14_supplement():
    md = r"""
### Supplementary — confusion matrices and paired comparisons (Phase 14)

The Phase-14 descriptive appendix above reports pooled pixel / boundary /
calibration metrics and Dice confidence intervals for the GLOBAL / ORACLE_REGIONAL
/ PREDICTED_REGIONAL modes. This supplementary block adds the two families that
were still missing from the central audit: **raw + row-normalized pixel confusion
matrices** and the **paired per-image Dice comparison**.

All added values are `DESCRIPTIVE_SUPPORTING_METRIC__NOT_PROSPECTIVE_GATE` /
`DESCRIPTIVE_POST_HOC_STATISTICAL_SUPPORT`. No inference, no training.
"""
    code = r'''
prov = [
    ('project_evaluation_confusion_matrices.json', _TAB / 'project_evaluation_confusion_matrices.json'),
    ('project_evaluation_paired_comparisons.csv', _TAB / 'project_evaluation_paired_comparisons.csv'),
]
_disp(_pd.DataFrame([{'artifact': n, 'sha256': _sha(p)[:16]} for n, p in prov if p.exists()]))

conf = _load(_TAB / 'project_evaluation_confusion_matrices.json')
arms14 = ['GLOBAL', 'ORACLE_REGIONAL', 'PREDICTED_REGIONAL']
fig, axes = _plt.subplots(2, len(arms14), figsize=(4.3 * len(arms14), 8.6))
for j, arm in enumerate(arms14):
    raw = _np.array(conf[arm]['matrix_raw'], dtype=float)
    nrm = _np.array(conf[arm]['matrix_row_normalized'], dtype=float)
    axes[0, j].imshow(_np.log10(raw + 1), cmap='Blues')
    for a in range(2):
        for b in range(2):
            axes[0, j].text(b, a, f'{int(raw[a, b]):,}', ha='center', va='center', fontsize=8,
                            color='black' if raw[a, b] < raw.max() * 0.6 else 'white')
    axes[0, j].set_xticks([0, 1]); axes[0, j].set_xticklabels(['Pred BG', 'Pred FG'])
    axes[0, j].set_yticks([0, 1]); axes[0, j].set_yticklabels(['GT BG', 'GT FG'])
    axes[0, j].set_title(f'{arm}\nraw counts')
    axes[1, j].imshow(nrm, cmap='Blues', vmin=0, vmax=1)
    for a in range(2):
        for b in range(2):
            axes[1, j].text(b, a, f'{nrm[a, b]:.4f}', ha='center', va='center', fontsize=8,
                            color='black' if nrm[a, b] < 0.6 else 'white')
    axes[1, j].set_xticks([0, 1]); axes[1, j].set_xticklabels(['Pred BG', 'Pred FG'])
    axes[1, j].set_yticks([0, 1]); axes[1, j].set_yticklabels(['GT BG', 'GT FG'])
    axes[1, j].set_title(f'{arm}\nrow-normalized')
_plt.tight_layout(); _p = _FIG / 'phase14_confusion_matrices.png'
_plt.savefig(str(_p), dpi=150, bbox_inches='tight'); _plt.show(); _show(_p, 980)

pc = _pd.read_csv(_TAB / 'project_evaluation_paired_comparisons.csv')
_disp(pc[['comparison', 'metric', 'n_pairs', 'mean_difference', 'ci_low', 'ci_high', 'wilcoxon_p', 'label']])

pi = _pd.read_csv(_TAB / 'project_evaluation_per_image_metrics.csv')
piv = pi.pivot_table(index='sample_id', columns='arm', values='dice')
if {'PREDICTED_REGIONAL', 'GLOBAL'} <= set(piv.columns):
    d = (piv['PREDICTED_REGIONAL'] - piv['GLOBAL']).astype(float)
    fig, ax = _plt.subplots(figsize=(8.5, 4.5))
    ax.hist(d, bins=30, color='#8e44ad', edgecolor='black', lw=0.4)
    ax.axvline(0, color='black', lw=1); ax.axvline(float(d.mean()), color='blue', ls='--', label=f'mean={d.mean():.4f}')
    ax.set_xlabel('per-image Dice(PREDICTED_REGIONAL) - Dice(GLOBAL)'); ax.set_ylabel('images')
    ax.set_title('Phase-14 paired per-image Dice difference (PREDICTED_REGIONAL vs GLOBAL)')
    ax.legend()
    _plt.tight_layout(); _p = _FIG / 'phase14_paired_predicted_vs_global.png'
    _plt.savefig(str(_p), dpi=150, bbox_inches='tight'); _plt.show(); _show(_p)

print('All added values are', LBL, '| paired statistics are', LBL_STAT)
'''
    return dict(md=md, code=code,
                sections=['Supplementary — confusion matrices and paired comparisons (Phase 14)'],
                tables=['Phase-14 paired per-image Dice comparisons'],
                figures=['phase14_confusion_matrices.png', 'phase14_paired_predicted_vs_global.png'])


def spec_h3_01():
    md = r"""
## Descriptive Evaluation and Visual Evidence — H3 proposal root cause

**Metric source / provenance.** Central proposal-domain artifact
(`project_evaluation_proposal_metrics_summary.csv`) plus the saved H3 supply
per-component table. No inference.

**Metric-domain label.** `LOCALIZATION_PROPOSAL_SUPPLY` +
`OBJECT_COMPONENT_DETECTION`. Added values are
`DESCRIPTIVE_SUPPORTING_METRIC__NOT_H3_GATE` (H3-specific) and
`DESCRIPTIVE_SUPPORTING_METRIC__NOT_PROSPECTIVE_GATE` (cross-arm).

**No confusion matrix.** Proposal/localizer root-cause diagnostics are expressed as
proposal TP/FP, component recall and zero-proposal counts — a TN-based confusion
matrix is not defined for this task.

**What this section does NOT prove.** It is a descriptive decomposition of where
proposals are lost; it does not adjudicate H3.
"""
    code = r'''
psum = _pd.read_csv(_TAB / 'project_evaluation_proposal_metrics_summary.csv')
_disp(psum)

h3c = _pd.read_csv(_TAB / 'h3_supply_eval_per_component.csv')
by = h3c.groupby('size_stratum').agg(n=('any_overlap', 'size'), detected=('any_overlap', 'sum')).reset_index()
by['any_overlap_recall'] = by['detected'] / by['n']
by['metric_domain'] = 'OBJECT_COMPONENT_DETECTION'; by['label'] = LBL_H3
_disp(by.round(6))

fig, ax = _plt.subplots(figsize=(8, 4.3))
order = ['TINY', 'SMALL', 'MEDIUM', 'LARGE']
vals = [float(by[by['size_stratum'] == s]['any_overlap_recall'].iloc[0]) for s in order]
ax.bar(order, vals, color='#d35400')
for i, v in enumerate(vals):
    ax.text(i, v + 0.01, f'{v:.3f}', ha='center', fontsize=9)
ax.set_ylim(0, 1.08); ax.set_ylabel('any-overlap proposal recall')
ax.set_title('H3 proposal-supply any-overlap recall by size (descriptive)')
_plt.tight_layout(); _p = _FIG / 'h3_01_proposal_recall_by_size.png'
_plt.savefig(str(_p), dpi=150, bbox_inches='tight'); _plt.show(); _show(_p)

print('All values above are', LBL_H3, '/', LBL)
'''
    return dict(md=md, code=code,
                sections=['Descriptive Evaluation and Visual Evidence — H3 proposal root cause'],
                tables=['proposal metrics summary (all arms)', 'H3 any-overlap proposal recall by size'],
                figures=['h3_01_proposal_recall_by_size.png'])


def spec_h3_02():
    md = r"""
## Descriptive Evaluation and Visual Evidence — H3 axis priority (A-only vs C-only)

**Metric source / provenance.** Central proposal-domain artifact
(`project_evaluation_proposal_metrics_summary.csv`) and the saved H3 supply
per-component table. No inference.

**Metric domain.** `CAUSAL_COUNTERFACTUAL_DIAGNOSTIC` +
`LOCALIZATION_PROPOSAL_SUPPLY`. Added values are
`DESCRIPTIVE_SUPPORTING_METRIC__NOT_H3_GATE`.

**Why no pixel confusion matrix.** The A-only / C-only comparison is a
proposal-supply axis diagnostic; the counterfactual unit is a *component*, not a
pixel, so a TN-based pixel confusion matrix does not apply.

**What this section does NOT prove.** It summarises the already-frozen axis-priority
evidence descriptively; it does not adjudicate H3.
"""
    code = r'''
psum = _pd.read_csv(_TAB / 'project_evaluation_proposal_metrics_summary.csv')
h3 = psum[psum['arm'].str.contains('H3')]
_disp(h3)

h3c = _pd.read_csv(_TAB / 'h3_supply_eval_per_component.csv')
tot = int(len(h3c)); det = int(h3c['any_overlap'].sum())
zero = tot - det
tiny = h3c[h3c['size_stratum'] == 'TINY']
_disp(_pd.DataFrame([{
    'gt_components': tot, 'any_overlap_detected': det, 'zero_proposal_components': zero,
    'zero_proposal_rate': zero / tot,
    'tiny_gt': int(len(tiny)), 'tiny_zero_proposal': int((~tiny['any_overlap']).sum()),
    'metric_domain': 'CAUSAL_COUNTERFACTUAL_DIAGNOSTIC', 'label': LBL_H3,
}]).round(6))

fig, ax = _plt.subplots(figsize=(7.5, 4.2))
ax.bar(['GT components', 'any-overlap\ndetected', 'zero-proposal\n(missed)'], [tot, det, zero],
       color=['#7f8c8d', '#27ae60', '#c0392b'])
for i, v in enumerate([tot, det, zero]):
    ax.text(i, v + 1, str(v), ha='center', fontsize=10)
ax.set_ylabel('components'); ax.set_title('H3 proposal supply: component outcome decomposition')
_plt.tight_layout(); _p = _FIG / 'h3_02_component_outcomes.png'
_plt.savefig(str(_p), dpi=150, bbox_inches='tight'); _plt.show(); _show(_p)

print('All values above are', LBL_H3)
'''
    return dict(md=md, code=code,
                sections=['Descriptive Evaluation and Visual Evidence — H3 axis priority (A-only vs C-only)'],
                tables=['H3 proposal metrics', 'H3 component outcome decomposition'],
                figures=['h3_02_component_outcomes.png'])


def spec_h3_04():
    md = r"""
## Descriptive Evaluation and Visual Evidence — H3 training (optimization metrics)

**Metric source / provenance.** The saved H3 training history
(`experiments/h3_kub_localizer_sigma_adaptive_sizeaware_seed42_clean_v3/history.csv`,
69 epochs). No training was performed in this notebook; the record is read-only.

**Metric-domain label.** `TRAINING_OPTIMIZATION` (loss / learning-rate / epoch
timing) plus the localizer's own validation-selection signals. Added values are
`DESCRIPTIVE_SUPPORTING_METRIC__NOT_H3_GATE`.

**Why no confusion matrix here.** This is a training-record notebook. Pixel /
proposal confusion matrices belong to the evaluation notebooks (H3-05, H3-06) and
are deliberately not duplicated here.

**What this section does NOT prove.** It documents the optimization trajectory; it
does not adjudicate H3 and does not re-select the checkpoint.
"""
    code = r'''
from pathlib import Path as _P2
hist_p = _P2('D:/Softfors/jup/experiments/h3_kub_localizer_sigma_adaptive_sizeaware_seed42_clean_v3/history.csv')
hist = _pd.read_csv(hist_p)
print('history rows:', len(hist), '| sha256:', _sha(hist_p)[:16])
best = hist.loc[hist['val_localization_recall'].idxmax()]
_disp(_pd.DataFrame([{
    'epochs': int(hist['epoch'].max()), 'best_epoch': int(best['epoch']),
    'best_val_localization_recall': float(best['val_localization_recall']),
    'final_train_loss': float(hist['train_loss'].iloc[-1]), 'final_val_loss': float(hist['val_loss'].iloc[-1]),
    'median_epoch_seconds': float(hist['epoch_seconds'].median()),
    'final_zero_proposal_gt': int(best['zero_proposal_gt']),
    'final_zero_proposal_tiny': int(best['zero_proposal_tiny']),
    'metric_domain': 'TRAINING_OPTIMIZATION', 'label': LBL_H3,
}]).round(6))

fig, (ax1, ax2) = _plt.subplots(1, 2, figsize=(13, 4.4))
ax1.plot(hist['epoch'], hist['train_loss'], label='train loss')
ax1.plot(hist['epoch'], hist['val_loss'], label='val loss')
ax1.axvline(int(best['epoch']), color='green', ls='--', lw=1, label=f"best ep {int(best['epoch'])}")
ax1.set_xlabel('epoch'); ax1.set_ylabel('loss'); ax1.set_title('H3 training / validation loss'); ax1.legend(fontsize=8)
ax2.plot(hist['epoch'], hist['val_localization_recall'], color='#8e44ad')
ax2.axvline(int(best['epoch']), color='green', ls='--', lw=1)
ax2.set_xlabel('epoch'); ax2.set_ylabel('VAL localization recall'); ax2.set_title('H3 VAL localization recall')
_plt.tight_layout(); _p = _FIG / 'h3_04_training_curves.png'
_plt.savefig(str(_p), dpi=150, bbox_inches='tight'); _plt.show(); _show(_p)

print('All values above are', LBL_H3)
'''
    return dict(md=md, code=code,
                sections=['Descriptive Evaluation and Visual Evidence — H3 training (optimization metrics)'],
                tables=['H3 best-epoch optimization summary'],
                figures=['h3_04_training_curves.png'])


def spec_h3_05():
    md = r"""
## Descriptive Evaluation and Visual Evidence — H3 supply axis (proposal/localizer)

**Metric source / provenance.** Central proposal-domain artifacts
(`project_evaluation_proposal_metrics_summary.csv`,
`project_evaluation_proposal_curves.json`) plus the saved H3 supply per-component
table. No inference.

**Metric-domain label.** `LOCALIZATION_PROPOSAL_SUPPLY` +
`OBJECT_COMPONENT_DETECTION`. Added values are
`DESCRIPTIVE_SUPPORTING_METRIC__NOT_H3_GATE`.

**Curve availability (honest labelling).** The H3 proposal PR/FROC curves are
**NOT** meaningful: `best_proposal_score` uses a `-1.0` sentinel for components
without an overlapping proposal, which makes the score perfectly separable by
construction. The curves are therefore reported as
`NA_DEGENERATE_SENTINEL_SCORE`, **not** fabricated.

**What this section does NOT prove.** Supply-axis evidence only; it does not
adjudicate H3 and does not re-select the frozen operating point.
"""
    code = r'''
psum = _pd.read_csv(_TAB / 'project_evaluation_proposal_metrics_summary.csv')
_disp(psum[psum['arm'].str.contains('H3')])

curves = _load(_TAB / 'project_evaluation_proposal_curves.json')
d = curves.get('H3_PROPOSAL_SUPPLY', {})
print('H3 proposal PR curve meaningful :', d.get('pr_curve_meaningful'))
print('Reason                          :', d.get('pr_curve_not_meaningful_reason'))
print('Operating threshold (annotated) :', d.get('operating_point_threshold'))

h3c = _pd.read_csv(_TAB / 'h3_supply_eval_per_component.csv')
rows = []
for s in ['TINY', 'SMALL', 'MEDIUM', 'LARGE']:
    sub = h3c[h3c['size_stratum'] == s]
    rows.append({'size_stratum': s, 'n': int(len(sub)),
                 'any_overlap_rate': float(sub['any_overlap'].mean()),
                 'coverage50_rate': float(sub['coverage50_success'].mean()),
                 'coverage90_rate': float(sub['coverage90_success'].mean()),
                 'metric_domain': 'LOCALIZATION_PROPOSAL_SUPPLY', 'label': LBL_H3})
_disp(_pd.DataFrame(rows).round(6))

fig, ax = _plt.subplots(figsize=(9, 4.4))
order = ['TINY', 'SMALL', 'MEDIUM', 'LARGE']
x = _np.arange(len(order)); w = 0.26
for i, (col, nm) in enumerate([('any_overlap_rate', 'any overlap'),
                               ('coverage50_rate', 'coverage >=50%'),
                               ('coverage90_rate', 'coverage >=90%')]):
    vals = [float([r for r in rows if r['size_stratum'] == s][0][col]) for s in order]
    ax.bar(x + i * w - w, vals, w, label=nm)
ax.set_xticks(x); ax.set_xticklabels(order); ax.set_ylim(0, 1.08)
ax.set_ylabel('component rate'); ax.set_title('H3 supply-axis component coverage by size (descriptive)')
ax.legend(fontsize=8)
_plt.tight_layout(); _p = _FIG / 'h3_05_supply_coverage_by_size.png'
_plt.savefig(str(_p), dpi=150, bbox_inches='tight'); _plt.show(); _show(_p)

print('All values above are', LBL_H3)
'''
    return dict(md=md, code=code,
                sections=['Descriptive Evaluation and Visual Evidence — H3 supply axis (proposal/localizer)'],
                tables=['H3 proposal metrics', 'H3 supply coverage by size stratum'],
                figures=['h3_05_supply_coverage_by_size.png'])


def spec_h3_06_supplement():
    md = r"""
### Supplementary — confusion matrices and paired comparisons (H3 downstream)

The H3 downstream descriptive augmentation above (§30) reports pooled pixel
metrics, boundary metrics, calibration and component detection. This supplementary
block adds the two remaining families from the central audit: **raw +
row-normalized pixel confusion matrices** and the **paired per-image Dice
comparison**.

All added values are `DESCRIPTIVE_SUPPORTING_METRIC__NOT_H3_GATE` /
`DESCRIPTIVE_POST_HOC_STATISTICAL_SUPPORT`. The frozen H3 formal metric
(`TinyRecall_H3 = 59/72`, `R_H3 = 2/15`) is **unchanged**. No inference.
"""
    code = r'''
conf = _load(_TAB / 'project_evaluation_confusion_matrices.json')
hc = conf['H3_DOWNSTREAM']
fig, axes = _plt.subplots(1, 2, figsize=(11, 4.3))
raw = _np.array(hc['matrix_raw'], dtype=float); nrm = _np.array(hc['matrix_row_normalized'], dtype=float)
axes[0].imshow(_np.log10(raw + 1), cmap='Blues')
for a in range(2):
    for b in range(2):
        axes[0].text(b, a, f'{int(raw[a, b]):,}', ha='center', va='center', fontsize=10,
                     color='black' if raw[a, b] < raw.max() * 0.6 else 'white')
axes[0].set_xticks([0, 1]); axes[0].set_xticklabels(['Pred Background', 'Pred Foreground'])
axes[0].set_yticks([0, 1]); axes[0].set_yticklabels(['GT Background', 'GT Foreground'])
axes[0].set_title('H3 downstream raw pixel confusion (counts)')
axes[1].imshow(nrm, cmap='Blues', vmin=0, vmax=1)
for a in range(2):
    for b in range(2):
        axes[1].text(b, a, f'{nrm[a, b]:.4f}', ha='center', va='center', fontsize=10,
                     color='black' if nrm[a, b] < 0.6 else 'white')
axes[1].set_xticks([0, 1]); axes[1].set_xticklabels(['Pred Background', 'Pred Foreground'])
axes[1].set_yticks([0, 1]); axes[1].set_yticklabels(['GT Background', 'GT Foreground'])
axes[1].set_title('H3 downstream row-normalized confusion')
_plt.tight_layout(); _p = _FIG / 'h3_06_confusion.png'
_plt.savefig(str(_p), dpi=150, bbox_inches='tight'); _plt.show(); _show(_p)

pc = _pd.read_csv(_TAB / 'project_evaluation_paired_comparisons.csv')
_disp(pc[['comparison', 'metric', 'n_pairs', 'mean_difference', 'ci_low', 'ci_high', 'wilcoxon_p', 'label']])

pi = _pd.read_csv(_TAB / 'project_evaluation_per_image_metrics.csv')
piv = pi.pivot_table(index='sample_id', columns='arm', values='dice')
if {'H3_DOWNSTREAM', 'GLOBAL'} <= set(piv.columns):
    dd = (piv['H3_DOWNSTREAM'] - piv['GLOBAL']).astype(float)
    fig, ax = _plt.subplots(figsize=(8.5, 4.5))
    ax.hist(dd, bins=30, color='#2c3e50', edgecolor='black', lw=0.4)
    ax.axvline(0, color='black', lw=1); ax.axvline(float(dd.mean()), color='red', ls='--', label=f'mean={dd.mean():.4f}')
    ax.set_xlabel('per-image Dice(H3 downstream) - Dice(GLOBAL)'); ax.set_ylabel('images')
    ax.set_title('H3 downstream paired per-image Dice difference vs GLOBAL')
    ax.legend()
    _plt.tight_layout(); _p = _FIG / 'h3_06_paired_vs_global.png'
    _plt.savefig(str(_p), dpi=150, bbox_inches='tight'); _plt.show(); _show(_p)

print('Frozen H3 formal metric unchanged (TinyRecall_H3 = 59/72, R_H3 = 2/15).')
print('All added values are', LBL_H3, '| paired statistics are', LBL_STAT)
'''
    return dict(md=md, code=code,
                sections=['Supplementary — confusion matrices and paired comparisons (H3 downstream)'],
                tables=['H3 downstream paired per-image Dice comparisons'],
                figures=['h3_06_confusion.png', 'h3_06_paired_vs_global.png'])


SPECS = [
    dict(phase='Phase 09',
         notebook='notebooks/phasewise/phase_09_baseline_training/phase09_clean_v3_unet_training_review.ipynb',
         **spec_phase09()),
    dict(phase='Phase 10',
         notebook='notebooks/phasewise/phase_10_baseline_comparison/phase10_clean_v3_final_baseline_comparison.ipynb',
         **spec_phase10()),
    dict(phase='Phase 11',
         notebook='notebooks/phasewise/phase_11_failure_analysis/phase11_clean_v3_baseline_failure_analysis.ipynb',
         **spec_phase11()),
    dict(phase='Phase 12',
         notebook='notebooks/phasewise/phase_12_oracle_roi/phase12_clean_v3_oracle_regional_analysis.ipynb',
         **spec_phase12()),
    dict(phase='Phase 13',
         notebook='notebooks/phasewise/phase_13_predicted_roi_localization/phase13_clean_v3_best_checkpoint_proposal_analysis.ipynb',
         **spec_phase13()),
    dict(phase='Phase 14',
         notebook='notebooks/phasewise/phase_14_regional_refiner/phase_14_regional_refiner_pipeline.ipynb',
         **spec_phase14_supplement()),
    dict(phase='H3-01',
         notebook='notebooks/phasewise/post_phase14_h3_proposal_supply/01_proposal_root_cause_diagnostic.ipynb',
         **spec_h3_01()),
    dict(phase='H3-02',
         notebook='notebooks/phasewise/post_phase14_h3_proposal_supply/02_h3_axis_priority_diagnostic.ipynb',
         **spec_h3_02()),
    dict(phase='H3-04',
         notebook='notebooks/phasewise/post_phase14_h3_proposal_supply/04_h3_training.ipynb',
         **spec_h3_04()),
    dict(phase='H3-05',
         notebook='notebooks/phasewise/post_phase14_h3_proposal_supply/05_h3_supply_axis_evaluation.ipynb',
         **spec_h3_05()),
    dict(phase='H3-06',
         notebook='notebooks/phasewise/post_phase14_h3_proposal_supply/06_h3_downstream_evaluation.ipynb',
         **spec_h3_06_supplement()),
]


def main() -> None:
    rec = json.loads(REC.read_text(encoding="utf-8")) if REC.exists() else {
        "artifact": "phasewise_evaluation_visualization_sha_updates",
        "status": "PHASEWISE_EVALUATION_VISUALIZATION_SYNC_RECORDED",
        "note": "Additive evaluation/visualization synchronization across completed phasewise notebooks.",
        "governance": {"training_performed": False, "inference_performed": False,
                       "test_reads": 0, "external_test_reads": 0, "thresholds_changed": False,
                       "checkpoints_changed": False, "frozen_metrics_changed": False,
                       "h3_adjudication": "NOT_PERFORMED"},
        "transitions": [],
    }
    only = set(a for a in sys.argv[1:] if not a.startswith("-"))
    results = []
    for spec in SPECS:
        if only and spec["phase"] not in only:
            continue
        p = ROOT / spec["notebook"]
        old = sha(p)
        nb = nbformat.read(str(p), as_version=4)
        already = any(MARKER in c.source for c in nb.cells)
        if not already:
            nb.cells.append(nbformat.v4.new_markdown_cell(spec["md"].strip("\n")))
            nb.cells.append(nbformat.v4.new_code_cell((PREAMBLE + spec["code"]).strip("\n")))
        nbformat.write(nb, str(p))
        print(f"[sync] executing {spec['phase']}: {Path(spec['notebook']).name} ...")
        client = NotebookClient(nb, kernel_name="jup-venv", timeout=900,
                                resources={"metadata": {"path": str(ROOT)}})
        client.execute()
        nbformat.write(nb, str(p))
        errs = sum(1 for c in nb.cells if c.cell_type == "code"
                   for o in c.get("outputs", []) if o.get("output_type") == "error")
        counts = [c.get("execution_count") for c in nb.cells if c.cell_type == "code"]
        mono = all(counts[i] == i + 1 for i in range(len(counts)))
        new = sha(p)
        print(f"        cells={len(nb.cells)} code={len(counts)} errors={errs} monotonic={mono}")
        entry = {
            "phase": spec["phase"], "notebook": spec["notebook"],
            "old_sha": old, "new_sha": new,
            "sections_added": spec["sections"], "tables_added": spec["tables"],
            "figures_added": spec["figures"],
            "code_cells": len(counts), "tracebacks": errs, "monotonic_execution": bool(mono),
            "inference_performed": False, "training_performed": False, "frozen_metrics_changed": False,
        }
        rec["transitions"] = [t for t in rec["transitions"] if t["notebook"] != spec["notebook"]] + [entry]
        results.append(entry)

    REC.write_text(json.dumps(rec, indent=2), encoding="utf-8")
    print("\n=== PHASEWISE SYNC SUMMARY ===")
    for r in results:
        print(f"  {r['phase']:8s} errors={r['tracebacks']} mono={r['monotonic_execution']} "
              f"{r['old_sha'][:12]} -> {r['new_sha'][:12]}  {Path(r['notebook']).name}")
    print("Record:", REC.relative_to(ROOT))


if __name__ == "__main__":
    main()
