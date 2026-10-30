"""
Phase 11 CLEAN-v3 failure analysis — companion VISUALIZATION dashboard (READ-ONLY).

Purpose: make the four-model KUB failure comparison easy to understand visually.

This module is READ-ONLY and DESCRIPTIVE. It:
  - reads ONLY existing frozen Phase-11 tables/audits
  - runs NO model inference, NO training, NO threshold changes
  - never modifies a scientific source table
  - never declares a winner / rank / superiority / significance

FIXED MODEL ORDER everywhere (descriptive, NOT a ranking):
    UNet -> Attention U-Net -> UNet++ -> DeepLabV3+

Author: Gemini 3.8 Flash Medium
Date: 2026-09-21
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(r'D:\Softfors\jup')
REPORTS = PROJECT_ROOT / 'reports'
TABLES = REPORTS / 'tables'
AUDITS = REPORTS / 'audits'
FIGDIR = REPORTS / 'figures' / 'phase11_clean_v3_failure_visual_dashboard'
FIGDIR.mkdir(parents=True, exist_ok=True)

# Fixed, non-ranking model order used by every plot and table in this dashboard.
MODELS: List[str] = ['UNet', 'Attention U-Net', 'UNet++', 'DeepLabV3+']
COLORS = {'UNet': 'C0', 'Attention U-Net': 'C1', 'UNet++': 'C2', 'DeepLabV3+': 'C3'}
BAR_COLOR = 'steelblue'

# Source tables (frozen Phase-11 evidence)
T_FAILURE_SUMMARY = TABLES / 'phase11_clean_v3_failure_summary_by_model.csv'
T_ACQUISITION = TABLES / 'phase11_clean_v3_failure_by_acquisition.csv'
T_LOW_DICE = TABLES / 'phase11_clean_v3_low_dice_decile_cutoffs.csv'
T_ANCHOR = TABLES / 'phase11_clean_v3_unetpp_failure_decile_cutoffs.csv'
T_DISAGREEMENT = TABLES / 'phase11_clean_v3_architecture_disagreement.csv'
T_TOP_DISAGREEMENT = TABLES / 'phase11_clean_v3_top_disagreement_cases.csv'
T_HARD_CASE = TABLES / 'phase11_clean_v3_hard_case_selection.csv'
T_PAIRED = TABLES / 'phase11_clean_v3_paired_case_failure_summary.csv'
T_FP = TABLES / 'phase11_clean_v3_fp_burden_summary.csv'
T_HD95 = TABLES / 'phase11_clean_v3_boundary_hd95_summary.csv'
T_BRIDGE = TABLES / 'phase11_clean_v3_phase12_bridge_evidence.csv'
T_PER_MODEL = TABLES / 'phase11_clean_v3_per_model_case_failure_metrics.csv'
T_MULTI = TABLES / 'phase11_clean_v3_multicomponent_analysis.csv'
A_AUDIT = AUDITS / 'phase11_clean_v3_failure_analysis_audit.json'

# Phase-10 authoritative overall VAL Dice (single-seed descriptive; NOT a ranking)
PHASE10_VAL_DICE = {
    'UNet': 0.7406133413314819,
    'Attention U-Net': 0.7525129853960107,
    'UNet++': 0.7641595156062713,
    'DeepLabV3+': 0.7509140344161673,
}

SUBTITLE = "DESCRIPTIVE SINGLE-SEED FAILURE ANALYSIS\nNO WINNER\nNO SIGNIFICANCE TESTING"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Loaders (all keyed by model name -> immune to groupby sort order)
# ---------------------------------------------------------------------------

def load_summary() -> pd.DataFrame:
    return pd.read_csv(T_FAILURE_SUMMARY).set_index('model').loc[MODELS].reset_index()


def load_regime() -> Dict[str, Dict[str, float]]:
    """Return {'FULL_FIELD': {model: dice}, 'ROI': {model: dice}} in FIXED model order."""
    d = pd.read_csv(T_ACQUISITION)
    out = {}
    for acq in ['FULL_FIELD', 'ROI']:
        s = d[d['acquisition_type'] == acq].set_index('model_display')['mean_dice']
        out[acq] = {m: float(s.loc[m]) for m in MODELS}
    return out


def load_regime_n() -> Dict[str, int]:
    d = pd.read_csv(T_ACQUISITION)
    s = d.groupby('acquisition_type')['n'].first()
    return {k: int(v) for k, v in s.items()}


def load_low_dice_q10() -> Dict[str, float]:
    d = pd.read_csv(T_LOW_DICE).set_index('model')
    return {m: float(d.loc[m, 'q10_cutoff']) for m in MODELS}


def load_low_dice_counts() -> Dict[str, int]:
    d = pd.read_csv(T_LOW_DICE).set_index('model')
    return {m: int(d.loc[m, 'count_le_cutoff']) for m in MODELS}


def load_anchor() -> Dict[str, float]:
    r = pd.read_csv(T_ANCHOR).iloc[0]
    return {'model': str(r['anchor_model']), 'role': str(r['anchor_role']),
            'hd95_q90': float(r['clean_v3_hd95_q90_valid']),
            'hd95_valid_n': int(r['hd95_valid_n']), 'hd95_invalid_n': int(r['hd95_invalid_n']),
            'fp_q90': float(r['clean_v3_fp_q90']), 'high_fp_count': int(r['high_fp_count'])}


def load_fp() -> pd.DataFrame:
    d = pd.read_csv(T_FP).set_index('model_display').loc[MODELS]
    return d.reset_index().rename(columns={'model_display': 'model'})


def load_hd95() -> pd.DataFrame:
    d = pd.read_csv(T_HD95).set_index('model_display').loc[MODELS]
    return d.reset_index().rename(columns={'model_display': 'model'})


def load_disagreement() -> pd.DataFrame:
    return pd.read_csv(T_DISAGREEMENT)


def load_top_disagreement(k: int = 4) -> pd.DataFrame:
    return pd.read_csv(T_TOP_DISAGREEMENT).head(k)


def load_hard_case() -> pd.DataFrame:
    return pd.read_csv(T_HARD_CASE)


def load_paired() -> pd.DataFrame:
    return pd.read_csv(T_PAIRED)


def load_bridge() -> pd.DataFrame:
    return pd.read_csv(T_BRIDGE)


def load_multi() -> pd.DataFrame:
    d = pd.read_csv(T_MULTI).set_index('model').loc[MODELS]
    return d.reset_index()


# ---------------------------------------------------------------------------
# Summary table (§18)
# ---------------------------------------------------------------------------

def dashboard_summary_table() -> pd.DataFrame:
    s = load_summary().set_index('model')
    reg = load_regime()
    rows = []
    for m in MODELS:
        rows.append({
            'Model': m,
            'Overall Phase-10 VAL Dice': PHASE10_VAL_DICE[m],
            'FULL_FIELD Dice': reg['FULL_FIELD'][m],
            'ROI Dice': reg['ROI'][m],
            'Object Recall': float(s.loc[m, 'object_recall']),
            'Empty Predictions': int(s.loc[m, 'empty_predictions']),
            'Multi-component Complete': int(s.loc[m, 'multi_complete']),
            'Multi-component Partial': int(s.loc[m, 'multi_partial']),
            'Multi-component Miss': int(s.loc[m, 'multi_miss']),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Plot helpers
# ---------------------------------------------------------------------------

def _annotate(ax, bars, fmt='{:.0f}'):
    for b in bars:
        h = b.get_height()
        ax.annotate(fmt.format(h), (b.get_x() + b.get_width() / 2, h),
                    ha='center', va='bottom', fontsize=9)


def _finish(fig, name: str) -> Path:
    p = FIGDIR / name
    fig.savefig(p, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return p


# ---------------------------------------------------------------------------
# PLOT 1 — empty predictions
# ---------------------------------------------------------------------------

def plot_empty_predictions() -> Path:
    s = load_summary().set_index('model')
    vals = [int(s.loc[m, 'empty_predictions']) for m in MODELS]
    fig, ax = plt.subplots(figsize=(8, 4.6))
    bars = ax.bar(MODELS, vals, color=[COLORS[m] for m in MODELS])
    _annotate(ax, bars)
    ax.set_ylabel('Empty predictions (count)')
    ax.set_title('Empty Predictions on KUB VAL\n280 KUB VAL cases — descriptive only', fontsize=11)
    ax.grid(True, alpha=.3, axis='y')
    plt.tight_layout()
    return _finish(fig, 'empty_predictions_by_model.png')


# ---------------------------------------------------------------------------
# PLOT 2 — object recall
# ---------------------------------------------------------------------------

def plot_object_recall() -> Path:
    s = load_summary().set_index('model')
    vals = [float(s.loc[m, 'object_recall']) for m in MODELS]
    fig, ax = plt.subplots(figsize=(8, 4.6))
    bars = ax.bar(MODELS, vals, color=[COLORS[m] for m in MODELS])
    _annotate(ax, bars, fmt='{:.4f}')
    ax.set_ylim(0, 1.0)
    ax.set_ylabel('Object Recall')
    ax.set_title('Object Recall by Model (EVALUATION_512 component space)\n'
                 '8-connectivity, >=1 px overlap — descriptive, NOT a ranking', fontsize=11)
    ax.grid(True, alpha=.3, axis='y')
    plt.tight_layout()
    return _finish(fig, 'object_recall_by_model.png')


# ---------------------------------------------------------------------------
# PLOT 3 — ROI vs FULL_FIELD dice
# ---------------------------------------------------------------------------

def plot_roi_vs_fullfield() -> Path:
    reg = load_regime()
    n = load_regime_n()
    x = np.arange(len(MODELS)); w = 0.38
    ff = [reg['FULL_FIELD'][m] for m in MODELS]
    roi = [reg['ROI'][m] for m in MODELS]
    fig, ax = plt.subplots(figsize=(10, 5))
    b1 = ax.bar(x - w / 2, ff, w, label=f"FULL_FIELD (n={n['FULL_FIELD']})", color='#4c72b0')
    b2 = ax.bar(x + w / 2, roi, w, label=f"ROI (n={n['ROI']})", color='#dd8452')
    _annotate(ax, b1, fmt='{:.4f}'); _annotate(ax, b2, fmt='{:.4f}')
    ax.set_xticks(x); ax.set_xticklabels(MODELS)
    ax.set_ylim(0, 1.0)
    ax.set_ylabel('Mean Dice')
    ax.set_title('KUB Acquisition-Regime Performance\n'
                 'FULL_FIELD n=103 · ROI n=177\n'
                 'The regime gap is observed across all four models.', fontsize=11)
    ax.legend()
    ax.grid(True, alpha=.3, axis='y')
    plt.tight_layout()
    return _finish(fig, 'roi_vs_fullfield_dice.png')


# ---------------------------------------------------------------------------
# PLOT 4 — ROI minus FULL_FIELD gap
# ---------------------------------------------------------------------------

def plot_regime_gap() -> Path:
    reg = load_regime()
    gaps = [reg['ROI'][m] - reg['FULL_FIELD'][m] for m in MODELS]
    fig, ax = plt.subplots(figsize=(8, 4.6))
    bars = ax.bar(MODELS, gaps, color=[COLORS[m] for m in MODELS])
    _annotate(ax, bars, fmt='{:.4f}')
    ax.set_ylabel('ROI mean Dice − FULL_FIELD mean Dice')
    ax.set_title('Observed ROI–FULL_FIELD Mean Dice Gap\n'
                 'DESCRIPTIVE ACQUISITION-REGIME GAP\n'
                 'NOT an oracle-ROI treatment effect', fontsize=11)
    ax.grid(True, alpha=.3, axis='y')
    plt.tight_layout()
    return _finish(fig, 'roi_fullfield_gap.png')


# ---------------------------------------------------------------------------
# PLOT 5 — multi-component outcomes
# ---------------------------------------------------------------------------

def plot_multicomponent() -> Path:
    m = load_multi().set_index('model')
    comp = [int(m.loc[x, 'COMPLETE_DETECTION']) for x in MODELS]
    part = [int(m.loc[x, 'PARTIAL_DETECTION']) for x in MODELS]
    miss = [int(m.loc[x, 'COMPLETE_MISS']) for x in MODELS]
    x = np.arange(len(MODELS)); w = 0.26
    fig, ax = plt.subplots(figsize=(10, 5))
    b1 = ax.bar(x - w, comp, w, label='COMPLETE_DETECTION', color='#55a868')
    b2 = ax.bar(x, part, w, label='PARTIAL_DETECTION', color='#c44e52')
    b3 = ax.bar(x + w, miss, w, label='COMPLETE_MISS', color='#8172b2')
    for bs in (b1, b2, b3):
        _annotate(ax, bs)
    ax.set_xticks(x); ax.set_xticklabels(MODELS)
    total = int(m['multicomponent_cases'].iloc[0])
    ax.set_ylabel('Multi-component cases (count)')
    ax.set_title(f'Multi-Component Case Detection Outcomes\n'
                 f'native GT membership, 8-connectivity · {total} multi-component cases\n'
                 f'descriptive only', fontsize=11)
    ax.legend()
    ax.grid(True, alpha=.3, axis='y')
    plt.tight_layout()
    return _finish(fig, 'multicomponent_outcomes.png')


# ---------------------------------------------------------------------------
# PLOT 6 — missed GT components
# ---------------------------------------------------------------------------

def plot_missed_components() -> Path:
    s = load_summary().set_index('model')
    missed = [int(s.loc[m, 'missed_components']) for m in MODELS]
    total = int(s['gt_eval_components'].iloc[0])
    fig, ax = plt.subplots(figsize=(8, 4.6))
    bars = ax.bar(MODELS, missed, color=[COLORS[m] for m in MODELS])
    _annotate(ax, bars)
    ax.set_ylabel('Missed GT components')
    ax.set_title(f'Missed GT Components by Model\n'
                 f'out of {total} GT evaluation components\n'
                 f'EVALUATION_512 space · 8-connectivity · >=1 px overlap', fontsize=11)
    ax.grid(True, alpha=.3, axis='y')
    plt.tight_layout()
    return _finish(fig, 'missed_components_by_model.png')


# ---------------------------------------------------------------------------
# PLOT 7 — model-specific low-dice Q10
# ---------------------------------------------------------------------------

def plot_low_dice_q10() -> Path:
    q10 = load_low_dice_q10()
    vals = [q10[m] for m in MODELS]
    fig, ax = plt.subplots(figsize=(8, 4.6))
    bars = ax.bar(MODELS, vals, color=[COLORS[m] for m in MODELS])
    _annotate(ax, bars, fmt='{:.4f}')
    ax.set_ylabel('Bottom-decile Dice cutoff (Q10)')
    ax.set_title('Model-Specific CLEAN-v3 Bottom-Decile Dice Cutoffs\n'
                 'each cutoff is defined from that model\'s OWN distribution —\n'
                 'NOT a model-performance ranking', fontsize=11)
    ax.grid(True, alpha=.3, axis='y')
    plt.tight_layout()
    return _finish(fig, 'low_dice_q10_by_model.png')


# ---------------------------------------------------------------------------
# PLOT 8 — shared failure distribution
# ---------------------------------------------------------------------------

def plot_shared_failure() -> Path:
    d = load_paired()
    counts = [int((d['low_model_count'] == i).sum()) for i in range(5)]
    allfour = int(d['ALL_FOUR_LOW'].sum())
    fig, ax = plt.subplots(figsize=(8, 4.6))
    bars = ax.bar([str(i) for i in range(5)], counts,
                  color=['#bbbbbb', '#9ecae1', '#6baed6', '#3182bd', '#08519c'])
    _annotate(ax, bars)
    ax.set_xlabel('low_model_count (how many models flag the case as bottom-decile Dice)')
    ax.set_ylabel('KUB VAL cases')
    ax.set_title('How Many Models Flag Each Case as Bottom-Decile Dice?\n'
                 f'low_model_count = 4 corresponds to ALL_FOUR_LOW = {allfour} / 280\n'
                 f'descriptive only', fontsize=11)
    ax.grid(True, alpha=.3, axis='y')
    plt.tight_layout()
    return _finish(fig, 'shared_failure_low_model_count.png')


# ---------------------------------------------------------------------------
# PLOT 9 — FP component burden
# ---------------------------------------------------------------------------

def plot_fp_burden() -> Path:
    f = load_fp().set_index('model')
    anchor = load_anchor()
    mean = [float(f.loc[m, 'mean']) for m in MODELS]
    q90 = [float(f.loc[m, 'q90']) for m in MODELS]
    x = np.arange(len(MODELS)); w = 0.38
    fig, ax = plt.subplots(figsize=(10, 5))
    b1 = ax.bar(x - w / 2, mean, w, label='mean fp_eval_components', color='#4c72b0')
    b2 = ax.bar(x + w / 2, q90, w, label='Q90 fp_eval_components', color='#c44e52')
    _annotate(ax, b1, fmt='{:.3f}'); _annotate(ax, b2, fmt='{:.2f}')
    ax.set_xticks(x); ax.set_xticklabels(MODELS)
    ax.set_ylabel('FP evaluation components')
    ax.set_title('False-Positive Component Burden (EVALUATION_512)\n'
                 f"UNet++ CLEAN-v3 Q90 = {anchor['fp_q90']:.1f} (HIGH_FP_DECILE anchor only —\n"
                 f"NOT a universal FP threshold; other models descriptive)", fontsize=11)
    ax.legend()
    ax.grid(True, alpha=.3, axis='y')
    plt.tight_layout()
    return _finish(fig, 'fp_component_burden.png')


# ---------------------------------------------------------------------------
# PLOT 10 — HD95 validity / boundary burden
# ---------------------------------------------------------------------------

def plot_hd95() -> Path:
    h = load_hd95().set_index('model')
    valid = [int(h.loc[m, 'n_valid']) for m in MODELS]
    invalid = [int(h.loc[m, 'n_invalid']) for m in MODELS]
    q90 = [float(h.loc[m, 'q90_hd95_valid']) for m in MODELS]
    median = [float(h.loc[m, 'median_hd95']) for m in MODELS]
    x = np.arange(len(MODELS)); w = 0.38
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    b1 = axes[0].bar(x - w / 2, valid, w, label='HD95 valid', color='#55a868')
    b2 = axes[0].bar(x + w / 2, invalid, w, label='HD95 invalid (flagged, not dropped)', color='#c44e52')
    _annotate(axes[0], b1); _annotate(axes[0], b2)
    axes[0].set_xticks(x); axes[0].set_xticklabels(MODELS, fontsize=9)
    axes[0].set_ylabel('cases'); axes[0].set_title('HD95 validity accounting')
    axes[0].legend(fontsize=8); axes[0].grid(True, alpha=.3, axis='y')

    b3 = axes[1].bar(x - w / 2, median, w, label='median valid HD95', color='#4c72b0')
    b4 = axes[1].bar(x + w / 2, q90, w, label='Q90 valid HD95', color='#dd8452')
    _annotate(axes[1], b3, fmt='{:.1f}'); _annotate(axes[1], b4, fmt='{:.1f}')
    axes[1].set_xticks(x); axes[1].set_xticklabels(MODELS, fontsize=9)
    axes[1].set_ylabel('HD95 (px)'); axes[1].set_title('Boundary burden (valid cases only)')
    axes[1].legend(fontsize=8); axes[1].grid(True, alpha=.3, axis='y')
    fig.suptitle('HD95 Validity and Boundary Burden — descriptive, invalid cases never dropped',
                 fontsize=11)
    plt.tight_layout(rect=[0, 0, 1, 0.94])
    return _finish(fig, 'hd95_validity.png')


# ---------------------------------------------------------------------------
# PLOT 11 — architecture disagreement
# ---------------------------------------------------------------------------

def plot_disagreement() -> Path:
    d = load_disagreement()
    top = load_top_disagreement(4)
    fig, axes = plt.subplots(1, 2, figsize=(15, 5))
    axes[0].hist(d['dice_range'], bins=40, color='indianred')
    axes[0].axvline(d['dice_range'].mean(), color='navy', linestyle='--',
                    label=f"mean {d['dice_range'].mean():.4f}")
    axes[0].axvline(d['dice_range'].median(), color='green', linestyle=':',
                    label=f"median {d['dice_range'].median():.4f}")
    axes[0].set_xlabel('dice_range = max Dice − min Dice')
    axes[0].set_ylabel('cases')
    axes[0].set_title(f"Disagreement distribution (no binary threshold)\n"
                      f"max {d['dice_range'].max():.4f}")
    axes[0].legend(fontsize=8); axes[0].grid(True, alpha=.3)

    labels = [s[:8] for s in top['sample_id']]
    b = axes[1].bar(labels, top['dice_range'], color='#8172b2')
    _annotate(axes[1], b, fmt='{:.3f}')
    axes[1].set_ylabel('dice_range')
    axes[1].set_title('Top 4 disagreement cases\nDESCRIPTIVE_DISAGREEMENT_DIAGNOSTIC_ONLY')
    axes[1].grid(True, alpha=.3, axis='y')
    fig.suptitle('Architecture Disagreement — continuous measure, no threshold', fontsize=11)
    plt.tight_layout(rect=[0, 0, 1, 0.93])
    return _finish(fig, 'architecture_disagreement_top4.png')


# ---------------------------------------------------------------------------
# PLOT 12 — hard-case cohort composition
# ---------------------------------------------------------------------------

def plot_hard_case_composition() -> Path:
    d = load_hard_case()
    order = ['A_EMPTY_PREDICTION', 'B_MISSED_COMPONENT', 'C_HIGH_FP_DECILE', 'D_LOW_DICE_DECILE']
    counts = [int((d['stratum'] == s).sum()) for s in order]
    acq = d['acquisition'].value_counts()
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8))
    b = axes[0].bar(order, counts, color=['#c44e52', '#dd8452', '#4c72b0', '#55a868'])
    _annotate(axes[0], b)
    axes[0].set_ylabel('selected cases')
    axes[0].set_title(f'Hard-case cohort by stratum (total {len(d)})')
    axes[0].tick_params(axis='x', labelsize=7); axes[0].grid(True, alpha=.3, axis='y')

    acq_labels = ['FULL_FIELD', 'ROI']
    acq_vals = [int(acq.get(k, 0)) for k in acq_labels]
    b2 = axes[1].bar(acq_labels, acq_vals, color=['#4c72b0', '#dd8452'])
    _annotate(axes[1], b2)
    axes[1].set_ylabel('selected cases')
    axes[1].set_title('Hard-case cohort by acquisition regime')
    axes[1].grid(True, alpha=.3, axis='y')
    fig.suptitle('Deterministic Historical-Style Hard-Case Cohort (UNet++ anchor)\n'
                 'prediction-dependent diagnostic cohort — NOT a prevalence estimate', fontsize=11)
    plt.tight_layout(rect=[0, 0, 1, 0.88])
    return _finish(fig, 'hard_case_composition.png')


# ---------------------------------------------------------------------------
# PLOT 13 — overall failure dashboard (composite)
# ---------------------------------------------------------------------------

def plot_overall_dashboard() -> Path:
    s = load_summary().set_index('model')
    reg = load_regime()
    d = load_paired()
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))

    vals = [int(s.loc[m, 'empty_predictions']) for m in MODELS]
    b = axes[0, 0].bar(MODELS, vals, color=[COLORS[m] for m in MODELS]); _annotate(axes[0, 0], b)
    axes[0, 0].set_title('Empty predictions'); axes[0, 0].grid(True, alpha=.3, axis='y')
    axes[0, 0].tick_params(axis='x', labelsize=8)

    vals = [float(s.loc[m, 'object_recall']) for m in MODELS]
    b = axes[0, 1].bar(MODELS, vals, color=[COLORS[m] for m in MODELS]); _annotate(axes[0, 1], b, fmt='{:.4f}')
    axes[0, 1].set_ylim(0, 1.0); axes[0, 1].set_title('Object recall (EVALUATION_512)')
    axes[0, 1].grid(True, alpha=.3, axis='y'); axes[0, 1].tick_params(axis='x', labelsize=8)

    x = np.arange(len(MODELS)); w = 0.38
    b1 = axes[1, 0].bar(x - w / 2, [reg['FULL_FIELD'][m] for m in MODELS], w, label='FULL_FIELD', color='#4c72b0')
    b2 = axes[1, 0].bar(x + w / 2, [reg['ROI'][m] for m in MODELS], w, label='ROI', color='#dd8452')
    _annotate(axes[1, 0], b1, fmt='{:.3f}'); _annotate(axes[1, 0], b2, fmt='{:.3f}')
    axes[1, 0].set_xticks(x); axes[1, 0].set_xticklabels(MODELS, fontsize=8)
    axes[1, 0].set_ylim(0, 1.0); axes[1, 0].set_title('ROI vs FULL_FIELD mean Dice')
    axes[1, 0].legend(fontsize=8); axes[1, 0].grid(True, alpha=.3, axis='y')

    counts = [int((d['low_model_count'] == i).sum()) for i in range(5)]
    b = axes[1, 1].bar([str(i) for i in range(5)], counts,
                       color=['#bbbbbb', '#9ecae1', '#6baed6', '#3182bd', '#08519c'])
    _annotate(axes[1, 1], b)
    axes[1, 1].set_xlabel('low_model_count'); axes[1, 1].set_title('Shared failure (ALL_FOUR_LOW = 12/280)')
    axes[1, 1].grid(True, alpha=.3, axis='y')

    fig.suptitle('Phase 11 CLEAN-v3 KUB Failure Analysis — Visual Comparison Dashboard\n'
                 + SUBTITLE.replace('\n', ' · '), fontsize=12)
    plt.tight_layout(rect=[0, 0, 1, 0.93])
    return _finish(fig, 'overall_failure_dashboard.png')


# ---------------------------------------------------------------------------
# Bridge summary table (§17) — qualitative dimensions stay tabular
# ---------------------------------------------------------------------------

def bridge_summary_table() -> pd.DataFrame:
    b = load_bridge()
    return b[['evidence', 'value', 'verdict']].copy()


# ---------------------------------------------------------------------------
# Registry (§26)
# ---------------------------------------------------------------------------

def build_registry(produced: Dict[str, Path]) -> pd.DataFrame:
    src_map = {
        'overall_failure_dashboard.png': T_FAILURE_SUMMARY.name,
        'empty_predictions_by_model.png': T_FAILURE_SUMMARY.name,
        'object_recall_by_model.png': T_FAILURE_SUMMARY.name,
        'roi_vs_fullfield_dice.png': T_ACQUISITION.name,
        'roi_fullfield_gap.png': T_ACQUISITION.name,
        'multicomponent_outcomes.png': T_MULTI.name,
        'missed_components_by_model.png': T_FAILURE_SUMMARY.name,
        'low_dice_q10_by_model.png': T_LOW_DICE.name,
        'shared_failure_low_model_count.png': T_PAIRED.name,
        'fp_component_burden.png': T_FP.name,
        'hd95_validity.png': T_HD95.name,
        'architecture_disagreement_top4.png': T_DISAGREEMENT.name,
        'hard_case_composition.png': T_HARD_CASE.name,
    }
    rows = []
    for name, path in produced.items():
        rows.append({'artifact': name, 'type': 'figure',
                     'source_table': src_map.get(name, 'multiple frozen Phase-11 tables'),
                     'SHA256': sha256_file(path),
                     'description': 'read-only descriptive Phase-11 failure visualisation'})
    rows.append({'artifact': 'phase11_failure_visual_dashboard.py', 'type': 'support_code',
                 'source_table': 'n/a',
                 'SHA256': sha256_file(Path(__file__)),
                 'description': 'read-only dashboard plotting helpers'})
    return pd.DataFrame(rows)


def save_registry(df: pd.DataFrame) -> Path:
    p = TABLES / 'phase11_clean_v3_failure_visual_dashboard_registry.csv'
    df.to_csv(p, index=False)
    return p
