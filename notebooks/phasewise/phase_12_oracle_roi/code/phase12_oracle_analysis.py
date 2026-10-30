"""
Phase 12 Part 1C — paired oracle mechanism analysis + visual evidence (READ-ONLY).

Operates ONLY on frozen Phase-12 Part-1B tables. Does NOT load any segmentation
checkpoint, does NOT run inference, does NOT train, does NOT modify any source table.

PRIMARY mechanism comparison (the only primary):
    GLOBAL_NATIVE  vs  ORACLE_FLOAT_GLOBAL_RETAINED
    paired within the same FULL_FIELD case, architecture, native space, GT, threshold.

Comparators (never primary):
    ORACLE_FLOAT_CROP_ONLY          -> SECONDARY_HISTORICAL_GEOMETRY_COMPARATOR
    ORACLE_LEGACY_UINT8_CROP_ONLY   -> COMBINED_LEGACY_RESTORE_SENSITIVITY

Fixed non-ranking model order everywhere: UNet, Attention U-Net, UNet++, DeepLabV3+.

Author: Gemini 3.1 Pro High
Date: 2026-09-21
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(r'D:\Softfors\jup')
REPORTS = PROJECT_ROOT / 'reports'
TABLES = REPORTS / 'tables'
AUDITS = REPORTS / 'audits'
FIGDIR = REPORTS / 'figures' / 'phase12_clean_v3_oracle_analysis'
FIGDIR.mkdir(parents=True, exist_ok=True)

MODELS = ['unet', 'attention_unet', 'unetpp', 'deeplabv3plus']
DISPLAY = {'unet': 'UNet', 'attention_unet': 'Attention U-Net',
           'unetpp': 'UNet++', 'deeplabv3plus': 'DeepLabV3+'}
ORDER = [DISPLAY[k] for k in MODELS]
COLORS = {'UNet': 'C0', 'Attention U-Net': 'C1', 'UNet++': 'C2', 'DeepLabV3+': 'C3'}

V_GLOBAL = 'GLOBAL_NATIVE'
V_PRIMARY = 'ORACLE_FLOAT_GLOBAL_RETAINED'
V_CROP = 'ORACLE_FLOAT_CROP_ONLY'
V_LEGACY = 'ORACLE_LEGACY_UINT8_CROP_ONLY'

STRATA = ['TINY', 'SMALL', 'MEDIUM', 'LARGE']

# frozen Part-1B inputs
T_CASE = TABLES / 'phase12_clean_v3_oracle_case_metrics.csv'
T_COMP = TABLES / 'phase12_clean_v3_oracle_component_metrics.csv'
T_GEOM = TABLES / 'phase12_clean_v3_oracle_geometry.csv'
T_DELTA = TABLES / 'phase12_clean_v3_primary_paired_deltas.csv'
T_SUMM = TABLES / 'phase12_clean_v3_oracle_raw_summary_by_model.csv'
T_SENS = TABLES / 'phase12_float_vs_legacy_mapback_sensitivity.csv'
T_FLAGS = TABLES / 'phase12_phase11_cohort_flags.csv'
T_GATE = TABLES / 'phase12_clean_v3_global_reproduction_gate.csv'
T_PROV = TABLES / 'phase12_clean_v3_oracle_inference_provenance.csv'
A_FROZEN = AUDITS / 'phase12_clean_v3_oracle_protocol_frozen.json'
A_INF = AUDITS / 'phase12_clean_v3_oracle_inference_audit.json'

PHASE10_EPOCH_TABLES = {
    'unet': TABLES / 'phase10_final_epoch_results_unet.csv',
    'attention_unet': TABLES / 'phase10_final_epoch_results_attention_unet.csv',
    'unetpp': TABLES / 'phase10_final_epoch_results_unetpp.csv',
    'deeplabv3plus': TABLES / 'phase10_final_epoch_results_deeplabv3plus.csv',
}
EXPECTED_EPOCH_ROWS = {'unet': 59, 'attention_unet': 69, 'unetpp': 85, 'deeplabv3plus': 67}


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Loaders (fixed model order, name-keyed)
# ---------------------------------------------------------------------------

def load_case() -> pd.DataFrame:
    return pd.read_csv(T_CASE)


def load_comp() -> pd.DataFrame:
    return pd.read_csv(T_COMP)


def load_geom() -> pd.DataFrame:
    return pd.read_csv(T_GEOM)


def load_delta() -> pd.DataFrame:
    return pd.read_csv(T_DELTA)


def load_flags() -> pd.DataFrame:
    return pd.read_csv(T_FLAGS)


def load_sens() -> pd.DataFrame:
    return pd.read_csv(T_SENS)


def variant(case: pd.DataFrame, v: str) -> pd.DataFrame:
    d = case[case['variant'] == v].copy()
    d['model_disp'] = d['model'].map(DISPLAY)
    return d


def input_integrity() -> Dict[str, object]:
    case, comp, geom, delta, flags = load_case(), load_comp(), load_geom(), load_delta(), load_flags()
    return {
        'case_rows': len(case), 'case_expected': 1648,
        'component_rows': len(comp), 'component_expected': 608,
        'geometry_rows': len(geom), 'geometry_expected': 152,
        'delta_rows': len(delta), 'delta_expected': 412,
        'flag_rows': len(flags), 'flag_expected': 103,
        'geometry_unique_keys': geom[['sample_id', 'native_component_id']].drop_duplicates().shape[0],
        'component_unique_keys': comp[['sample_id', 'native_component_id', 'model']].drop_duplicates().shape[0],
        'variants': sorted(case['variant'].unique()),
        'models': sorted(case['model'].unique()),
        'strata': geom['size_stratum'].value_counts().to_dict(),
        'no_many_to_many': comp.merge(geom, on=['sample_id', 'native_component_id'], how='left').shape[0] == 608,
    }


# ---------------------------------------------------------------------------
# §5 primary macro comparison
# ---------------------------------------------------------------------------

def primary_global_vs_oracle_summary(case: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for k in MODELS:
        g = case[(case.model == k) & (case.variant == V_GLOBAL)]
        p = case[(case.model == k) & (case.variant == V_PRIMARY)]
        gv, pv = g[g.hd95_valid], p[p.hd95_valid]
        rec = {'model': DISPLAY[k], 'model_key': k, 'n': len(g)}
        for tag, d, val in [('global', g, gv), ('primary', p, pv)]:
            rec[f'{tag}_macro_dice'] = d.dice.mean()
            rec[f'{tag}_macro_iou'] = d.iou.mean()
            rec[f'{tag}_macro_precision'] = d.precision.mean()
            rec[f'{tag}_macro_recall'] = d.recall.mean()
            rec[f'{tag}_object_recall'] = d.object_recall.mean()
            rec[f'{tag}_empty_predictions'] = int(d.prediction_empty.sum())
            rec[f'{tag}_missed_components'] = int(d.missed_native_components.sum())
            rec[f'{tag}_median_valid_hd95'] = float(val.hd95.median()) if len(val) else np.nan
            rec[f'{tag}_mean_fp_pixels'] = d.fp_pixels.mean()
            rec[f'{tag}_median_fp_pixels'] = d.fp_pixels.median()
            rec[f'{tag}_mean_fn_pixels'] = d.fn_pixels.mean()
            rec[f'{tag}_median_fn_pixels'] = d.fn_pixels.median()
        for f in ['macro_dice', 'macro_iou', 'macro_precision', 'macro_recall', 'object_recall']:
            rec[f'diff_{f}'] = rec[f'primary_{f}'] - rec[f'global_{f}']
        rec['diff_missed_components'] = rec['primary_missed_components'] - rec['global_missed_components']
        rec['diff_empty_predictions'] = rec['primary_empty_predictions'] - rec['global_empty_predictions']
        rows.append(rec)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# §6 paired delta distribution
# ---------------------------------------------------------------------------

def primary_delta_distribution(delta: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for k in MODELS:
        d = delta[delta.model == k]['delta_dice']
        n = len(d)
        rows.append({'model': DISPLAY[k], 'model_key': k, 'n': n,
                     'mean_delta_dice': d.mean(), 'median_delta_dice': d.median(),
                     'q25': d.quantile(.25), 'q75': d.quantile(.75),
                     'min': d.min(), 'max': d.max(),
                     'count_improved': int((d > 0).sum()),
                     'count_unchanged': int((d == 0).sum()),
                     'count_worsened': int((d < 0).sum()),
                     'pct_improved': float((d > 0).mean()),
                     'pct_unchanged': float((d == 0).mean()),
                     'pct_worsened': float((d < 0).mean()),
                     'direction_only': 'positive/zero/negative (exact paired sign; no clinical cutoff)'})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# §7 worsened cases (exhaustive)
# ---------------------------------------------------------------------------

def primary_worsened_cases(delta: pd.DataFrame, case: pd.DataFrame, flags: pd.DataFrame) -> pd.DataFrame:
    g = variant(case, V_GLOBAL).set_index(['sample_id', 'model'])
    p = variant(case, V_PRIMARY).set_index(['sample_id', 'model'])
    w = delta[delta.delta_dice < 0].copy()
    rows = []
    for _, r in w.iterrows():
        key = (r['sample_id'], r['model'])
        gg, pp = g.loc[key], p.loc[key]
        fl = flags[flags.sample_id == r['sample_id']].iloc[0]
        rows.append({
            'sample_id': r['sample_id'], 'model': DISPLAY[r['model']],
            'category': gg['category'], 'native_component_count': int(gg['native_gt_components']),
            'global_dice': r['global_dice'], 'primary_dice': r['primary_dice'],
            'delta_dice': r['delta_dice'],
            'global_precision': r['global_precision'], 'primary_precision': r['primary_precision'],
            'delta_precision': r['delta_precision'],
            'global_recall': r['global_recall'], 'primary_recall': r['primary_recall'],
            'delta_recall': r['delta_recall'],
            'global_object_recall': r['global_object_recall'],
            'primary_object_recall': r['primary_object_recall'],
            'global_missed_components': int(r['global_missed_components']),
            'primary_missed_components': int(r['primary_missed_components']),
            'global_fp_pixels': gg['fp_pixels'], 'primary_fp_pixels': pp['fp_pixels'],
            'delta_fp_pixels': pp['fp_pixels'] - gg['fp_pixels'],
            'global_fn_pixels': gg['fn_pixels'], 'primary_fn_pixels': pp['fn_pixels'],
            'delta_fn_pixels': pp['fn_pixels'] - gg['fn_pixels'],
            'ALL_FOUR_LOW': bool(fl['ALL_FOUR_LOW']),
            'PHASE11_HARD_CASE': bool(fl['PHASE11_HARD_CASE']),
            'PHASE11_TOP_DISAGREEMENT': bool(fl['PHASE11_TOP_DISAGREEMENT']),
            'PHASE11_MULTICOMPONENT': bool(fl['PHASE11_MULTICOMPONENT']),
            'object_recall_improves_despite_dice_decrease':
                bool(r['primary_object_recall'] > r['global_object_recall']),
        })
    return pd.DataFrame(rows)


def worsened_summary(w: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for k in MODELS:
        d = w[w.model == DISPLAY[k]]
        rows.append({'model': DISPLAY[k], 'worsened_cases': len(d),
                     'median_worsening': float(d.delta_dice.median()) if len(d) else np.nan,
                     'max_worsening': float(d.delta_dice.min()) if len(d) else np.nan,
                     'n_object_recall_improves_despite_dice_decrease':
                         int(d.object_recall_improves_despite_dice_decrease.sum()) if len(d) else 0,
                     'fraction_object_recall_improves_despite_dice_decrease':
                         float(d.object_recall_improves_despite_dice_decrease.mean()) if len(d) else np.nan})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# §8 benefit / cost decomposition
# ---------------------------------------------------------------------------

def primary_benefit_cost_summary(delta: pd.DataFrame, case: pd.DataFrame) -> pd.DataFrame:
    g = variant(case, V_GLOBAL).set_index(['sample_id', 'model'])
    p = variant(case, V_PRIMARY).set_index(['sample_id', 'model'])
    rows = []
    for k in MODELS:
        d = delta[delta.model == k].copy()
        dfp, dfn = [], []
        for _, r in d.iterrows():
            key = (r['sample_id'], k)
            dfp.append(p.loc[key, 'fp_pixels'] - g.loc[key, 'fp_pixels'])
            dfn.append(p.loc[key, 'fn_pixels'] - g.loc[key, 'fn_pixels'])
        d['delta_fp_pixels'] = dfp; d['delta_fn_pixels'] = dfn
        imp = d.delta_dice > 0; wor = d.delta_dice < 0
        fp_up = d.delta_fp_pixels > 0
        rows.append({
            'model': DISPLAY[k], 'model_key': k, 'n': len(d),
            'mean_delta_precision': d.delta_precision.mean(), 'median_delta_precision': d.delta_precision.median(),
            'mean_delta_recall': d.delta_recall.mean(), 'median_delta_recall': d.delta_recall.median(),
            'mean_delta_fp_pixels': d.delta_fp_pixels.mean(), 'median_delta_fp_pixels': d.delta_fp_pixels.median(),
            'mean_delta_fn_pixels': d.delta_fn_pixels.mean(), 'median_delta_fn_pixels': d.delta_fn_pixels.median(),
            'mean_delta_object_recall': d.delta_object_recall.mean(),
            'median_delta_object_recall': d.delta_object_recall.median(),
            'dice_improves_and_fp_increases': int((imp & fp_up).sum()),
            'dice_improves_and_fp_decreases_or_equal': int((imp & ~fp_up).sum()),
            'dice_worsens_and_fp_increases': int((wor & fp_up).sum()),
            'dice_worsens_and_fp_decreases_or_equal': int((wor & ~fp_up).sum()),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# §9 normalized FP / FN burden
# ---------------------------------------------------------------------------

def primary_normalized_error_burden(case: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for k in MODELS:
        for vname, vtag in [(V_GLOBAL, 'GLOBAL'), (V_PRIMARY, 'PRIMARY')]:
            d = case[(case.model == k) & (case.variant == vname)].copy()
            gt = d.tp_pixels + d.fn_pixels
            d['fp_per_gt_pixel'] = np.where(gt > 0, d.fp_pixels / gt.replace(0, np.nan), np.nan)
            d['fn_fraction'] = np.where(gt > 0, d.fn_pixels / gt.replace(0, np.nan), np.nan)
            rows.append({'model': DISPLAY[k], 'model_key': k, 'variant': vtag, 'n': len(d),
                         'fp_per_gt_pixel_mean': d.fp_per_gt_pixel.mean(),
                         'fp_per_gt_pixel_median': d.fp_per_gt_pixel.median(),
                         'fp_per_gt_pixel_q25': d.fp_per_gt_pixel.quantile(.25),
                         'fp_per_gt_pixel_q75': d.fp_per_gt_pixel.quantile(.75),
                         'fn_fraction_mean': d.fn_fraction.mean(),
                         'fn_fraction_median': d.fn_fraction.median(),
                         'fn_fraction_q25': d.fn_fraction.quantile(.25),
                         'fn_fraction_q75': d.fn_fraction.quantile(.75)})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# §10/§11 component-level recovery
# ---------------------------------------------------------------------------

def component_events(comp: pd.DataFrame, geom: pd.DataFrame) -> pd.DataFrame:
    m = comp.merge(geom[['sample_id', 'native_component_id', 'size_stratum',
                         'native_component_ratio']],
                   on=['sample_id', 'native_component_id'], how='left')
    if len(m) != 608:
        raise RuntimeError(f'component/geometry merge produced {len(m)} rows, expected 608')
    m['model_disp'] = m['model'].map(DISPLAY)

    def status(r):
        if not r['global_detected'] and r['primary_oracle_detected']:
            return 'RECOVERED'
        if r['global_detected'] and r['primary_oracle_detected']:
            return 'PRESERVED_DETECTED'
        if not r['global_detected'] and not r['primary_oracle_detected']:
            return 'PERSISTENT_MISS'
        return 'LOST_DETECTION'
    m['status'] = m.apply(status, axis=1)
    return m


def primary_component_recovery_events(ev: pd.DataFrame) -> pd.DataFrame:
    cols = ['sample_id', 'native_component_id', 'model', 'model_disp', 'size_stratum',
            'native_component_ratio', 'global_detected', 'primary_oracle_detected', 'status']
    return ev[cols].rename(columns={'model_disp': 'model_display',
                                    'primary_oracle_detected': 'primary_detected'})


def primary_size_stratified_component_recovery(ev: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for k in MODELS:
        d = ev[ev.model == k]
        for s in STRATA:
            ds = d[d.size_stratum == s]
            if len(ds) == 0:
                continue
            gd = int(ds.global_detected.sum()); pd_ = int(ds.primary_oracle_detected.sum())
            gt = len(ds)
            rows.append({'model': DISPLAY[k], 'model_key': k, 'size_stratum': s,
                         'gt_components': gt,
                         'global_detected': gd, 'global_missed': gt - gd,
                         'global_object_recall': gd / gt,
                         'primary_detected': pd_, 'primary_missed': gt - pd_,
                         'primary_object_recall': pd_ / gt,
                         'recovered_components': int(((~ds.global_detected) & ds.primary_oracle_detected).sum()),
                         'lost_components': int((ds.global_detected & (~ds.primary_oracle_detected)).sum())})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# §12 multi-component transitions
# ---------------------------------------------------------------------------

def _classify(detected: int, total: int) -> str:
    if total == 0:
        return 'NO_COMPONENT'
    if detected == total:
        return 'COMPLETE_DETECTION'
    if detected == 0:
        return 'COMPLETE_MISS'
    return 'PARTIAL_DETECTION'


def primary_multicomponent_outcomes(case: pd.DataFrame, comp: pd.DataFrame) -> pd.DataFrame:
    multi_ids = set(case[case.native_gt_components > 1].sample_id.unique())
    rows, trans_rows = [], []
    for k in MODELS:
        g = case[(case.model == k) & (case.variant == V_GLOBAL) & case.sample_id.isin(multi_ids)]
        p = case[(case.model == k) & (case.variant == V_PRIMARY) & case.sample_id.isin(multi_ids)]
        gcls = {r['sample_id']: _classify(int(r['detected_native_components']), int(r['native_gt_components']))
                for _, r in g.iterrows()}
        pcls = {r['sample_id']: _classify(int(r['detected_native_components']), int(r['native_gt_components']))
                for _, r in p.iterrows()}
        gc = pd.Series(list(gcls.values())).value_counts().to_dict()
        pc = pd.Series(list(pcls.values())).value_counts().to_dict()
        rows.append({'model': DISPLAY[k], 'model_key': k, 'multicomponent_cases': len(gcls),
                     'global_complete': gc.get('COMPLETE_DETECTION', 0),
                     'global_partial': gc.get('PARTIAL_DETECTION', 0),
                     'global_miss': gc.get('COMPLETE_MISS', 0),
                     'primary_complete': pc.get('COMPLETE_DETECTION', 0),
                     'primary_partial': pc.get('PARTIAL_DETECTION', 0),
                     'primary_miss': pc.get('COMPLETE_MISS', 0)})
        for sid in sorted(gcls):
            trans_rows.append({'sample_id': sid, 'model': DISPLAY[k],
                               'global_outcome': gcls[sid], 'primary_outcome': pcls[sid],
                               'transition': f'{gcls[sid]} -> {pcls[sid]}'})
    return pd.DataFrame(rows), pd.DataFrame(trans_rows)


# ---------------------------------------------------------------------------
# §13 empty prediction recovery
# ---------------------------------------------------------------------------

def primary_empty_prediction_recovery(case: pd.DataFrame) -> pd.DataFrame:
    rows, id_rows = [], []
    for k in MODELS:
        g = case[(case.model == k) & (case.variant == V_GLOBAL)].set_index('sample_id')
        p = case[(case.model == k) & (case.variant == V_PRIMARY)].set_index('sample_id')
        ge = set(g.index[g.prediction_empty]); pe = set(p.index[p.prediction_empty])
        recovered = sorted(ge - pe); new_empty = sorted(pe - ge)
        rows.append({'model': DISPLAY[k], 'model_key': k,
                     'global_empty': len(ge), 'primary_empty': len(pe),
                     'recovered_empty_cases': len(recovered), 'new_empty_cases': len(new_empty),
                     'recovered_sample_ids': ';'.join(recovered) if recovered else '',
                     'new_empty_sample_ids': ';'.join(new_empty) if new_empty else ''})
        for sid in recovered:
            id_rows.append({'sample_id': sid, 'model': DISPLAY[k], 'event': 'RECOVERED_EMPTY'})
        for sid in new_empty:
            id_rows.append({'sample_id': sid, 'model': DISPLAY[k], 'event': 'NEW_EMPTY'})
    return pd.DataFrame(rows), pd.DataFrame(id_rows)


# ---------------------------------------------------------------------------
# §14 HD95
# ---------------------------------------------------------------------------

def primary_hd95_analysis(case: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for k in MODELS:
        g = case[(case.model == k) & (case.variant == V_GLOBAL)].set_index('sample_id')
        p = case[(case.model == k) & (case.variant == V_PRIMARY)].set_index('sample_id')
        both = sorted(set(g.index[g.hd95_valid]) & set(p.index[p.hd95_valid]))
        dh = p.loc[both, 'hd95'] - g.loc[both, 'hd95']
        rows.append({'model': DISPLAY[k], 'model_key': k,
                     'global_valid_n': int(g.hd95_valid.sum()), 'global_invalid_n': int((~g.hd95_valid).sum()),
                     'primary_valid_n': int(p.hd95_valid.sum()), 'primary_invalid_n': int((~p.hd95_valid).sum()),
                     'both_valid_paired_n': len(both),
                     'median_valid_hd95_global': float(g.loc[both, 'hd95'].median()) if both else np.nan,
                     'median_valid_hd95_primary': float(p.loc[both, 'hd95'].median()) if both else np.nan,
                     'delta_hd95_mean': float(dh.mean()) if both else np.nan,
                     'delta_hd95_median': float(dh.median()) if both else np.nan,
                     'delta_hd95_q25': float(dh.quantile(.25)) if both else np.nan,
                     'delta_hd95_q75': float(dh.quantile(.75)) if both else np.nan,
                     'delta_hd95_min': float(dh.min()) if both else np.nan,
                     'delta_hd95_max': float(dh.max()) if both else np.nan,
                     'note': 'negative delta = lower boundary distance; invalid flagged, never dropped'})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# §15 Phase-11 frozen cohort bridge
# ---------------------------------------------------------------------------

COHORTS = ['ALL_FOUR_LOW', 'PHASE11_HARD_CASE', 'PHASE11_TOP_DISAGREEMENT', 'PHASE11_MULTICOMPONENT']


def phase11_frozen_cohort_oracle_response(delta: pd.DataFrame, case: pd.DataFrame,
                                          flags: pd.DataFrame) -> pd.DataFrame:
    g = variant(case, V_GLOBAL).set_index(['sample_id', 'model'])
    p = variant(case, V_PRIMARY).set_index(['sample_id', 'model'])
    d = delta.merge(flags, on='sample_id', how='left')
    rows = []
    for c in COHORTS:
        for k in MODELS:
            sub = d[(d.model == k) & (d[c])]
            if len(sub) == 0:
                continue
            n_cases = sub.sample_id.nunique()
            fp_delta = [p.loc[(r['sample_id'], k), 'fp_pixels'] - g.loc[(r['sample_id'], k), 'fp_pixels']
                        for _, r in sub.iterrows()]
            rows.append({'cohort': c, 'model': DISPLAY[k], 'model_key': k,
                         'n_case_model_rows': len(sub), 'n_cases': n_cases,
                         'n_meaning': 'n_cases = distinct FULL_FIELD cases; n_case_model_rows = cases x 1 model',
                         'global_mean_dice': sub.global_dice.mean(), 'global_median_dice': sub.global_dice.median(),
                         'primary_mean_dice': sub.primary_dice.mean(), 'primary_median_dice': sub.primary_dice.median(),
                         'mean_delta_dice': sub.delta_dice.mean(), 'median_delta_dice': sub.delta_dice.median(),
                         'global_object_recall': sub.global_object_recall.mean(),
                         'primary_object_recall': sub.primary_object_recall.mean(),
                         'recovered_components': int(sub.recovered_components.sum()),
                         'empty_recoveries': int(sub.empty_recovered.sum()),
                         'mean_fp_burden_change': float(np.mean(fp_delta))})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# §16 category
# ---------------------------------------------------------------------------

def primary_category_analysis(delta: pd.DataFrame, case: pd.DataFrame) -> pd.DataFrame:
    g = variant(case, V_GLOBAL).set_index(['sample_id', 'model'])
    cat = g.reset_index()[['sample_id', 'category']].drop_duplicates()
    d = delta.merge(cat, on='sample_id', how='left')
    rows = []
    for k in MODELS:
        for c in ['Bladder_Stone', 'Kidney_Stone', 'Ureteric_Stone']:
            sub = d[(d.model == k) & (d.category == c)]
            if len(sub) == 0:
                continue
            rows.append({'model': DISPLAY[k], 'model_key': k, 'category': c, 'n': len(sub),
                         'global_mean_dice': sub.global_dice.mean(),
                         'primary_mean_dice': sub.primary_dice.mean(),
                         'mean_delta_dice': sub.delta_dice.mean(),
                         'median_delta_dice': sub.delta_dice.median(),
                         'improved': int((sub.delta_dice > 0).sum()),
                         'worsened': int((sub.delta_dice < 0).sum()),
                         'note': 'category is subgroup METADATA, not a segmentation class'})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# §17 primary vs crop-only comparator
# ---------------------------------------------------------------------------

def primary_vs_crop_only_comparator(case: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for k in MODELS:
        p = case[(case.model == k) & (case.variant == V_PRIMARY)].set_index('sample_id')
        c = case[(case.model == k) & (case.variant == V_CROP)].set_index('sample_id')
        fp = c.fp_pixels - p.fp_pixels; fn = c.fn_pixels - p.fn_pixels
        d_dice = c.dice.mean() - p.dice.mean()
        rows.append({'model': DISPLAY[k], 'model_key': k, 'n': len(p),
                     'primary_macro_dice': p.dice.mean(), 'crop_only_macro_dice': c.dice.mean(),
                     'macro_dice_difference_crop_minus_primary': d_dice,
                     'macro_precision_difference': c.precision.mean() - p.precision.mean(),
                     'macro_recall_difference': c.recall.mean() - p.recall.mean(),
                     'mean_fp_difference': float(fp.mean()), 'mean_fn_difference': float(fn.mean()),
                     'object_recall_difference': c.object_recall.mean() - p.object_recall.mean(),
                     'interpretation': 'ORACLE_BACKGROUND_SUPPRESSION_ADVANTAGE_PRESENT' if abs(d_dice) > 1e-12
                                       else 'NO_OBSERVED_ORACLE_BACKGROUND_SUPPRESSION_ADVANTAGE',
                     'note': 'crop-only zeroes all prediction outside oracle crop support, i.e. it has '
                             'access to oracle background suppression. It is NOT the primary SR-1 '
                             'mechanism estimate and must not be called preferred.'})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# §19 cross-architecture consistency
# ---------------------------------------------------------------------------

def cross_architecture_oracle_consistency(delta: pd.DataFrame, case: pd.DataFrame) -> pd.DataFrame:
    g = variant(case, V_GLOBAL).set_index(['sample_id', 'model'])
    p = variant(case, V_PRIMARY).set_index(['sample_id', 'model'])
    rows = []
    for sid, sub in delta.groupby('sample_id'):
        pos = int((sub.delta_dice > 0).sum())
        rec_imp = 0; comp_rec = 0
        for _, r in sub.iterrows():
            key = (sid, r['model'])
            if p.loc[key, 'object_recall'] > g.loc[key, 'object_recall']:
                rec_imp += 1
            if r['recovered_components'] > 0:
                comp_rec += 1
        rows.append({'sample_id': sid, 'models_delta_positive': pos,
                     'models_object_recall_improved': rec_imp,
                     'models_component_recovery_positive': comp_rec,
                     'all_four_delta_positive': pos == 4,
                     'all_four_object_recall_nonworse':
                         bool(all(p.loc[(sid, k), 'object_recall'] >= g.loc[(sid, k), 'object_recall']
                                  for k in MODELS))})
    df = pd.DataFrame(rows)
    return df


def cross_arch_distribution(ca: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for col in ['models_delta_positive', 'models_object_recall_improved',
                'models_component_recovery_positive']:
        vc = ca[col].value_counts().sort_index()
        for i in range(5):
            rows.append({'metric': col, 'n_models': i, 'n_cases': int(vc.get(i, 0))})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# §20 ALL_FOUR_LOW
# ---------------------------------------------------------------------------

def all_four_low_oracle_response(delta: pd.DataFrame, case: pd.DataFrame, flags: pd.DataFrame) -> pd.DataFrame:
    g = variant(case, V_GLOBAL).set_index(['sample_id', 'model'])
    p = variant(case, V_PRIMARY).set_index(['sample_id', 'model'])
    afl = set(flags.loc[flags.ALL_FOUR_LOW, 'sample_id'])
    rows = []
    for sid in sorted(afl):
        for k in MODELS:
            r = delta[(delta.sample_id == sid) & (delta.model == k)]
            if len(r) == 0:
                continue
            r = r.iloc[0]
            rows.append({'sample_id': sid, 'model': DISPLAY[k], 'model_key': k,
                         'category': g.loc[(sid, k), 'category'],
                         'native_gt_components': int(g.loc[(sid, k), 'native_gt_components']),
                         'global_dice': r['global_dice'], 'primary_dice': r['primary_dice'],
                         'delta_dice': r['delta_dice'],
                         'global_object_recall': r['global_object_recall'],
                         'primary_object_recall': r['primary_object_recall'],
                         'delta_object_recall': r['delta_object_recall'],
                         'delta_fp_pixels': p.loc[(sid, k), 'fp_pixels'] - g.loc[(sid, k), 'fp_pixels'],
                         'delta_fn_pixels': p.loc[(sid, k), 'fn_pixels'] - g.loc[(sid, k), 'fn_pixels'],
                         'recovered_components': int(r['recovered_components'])})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# §24 mechanism evidence matrix
# ---------------------------------------------------------------------------

def oracle_mechanism_evidence_matrix(case: pd.DataFrame, delta: pd.DataFrame,
                                     size: pd.DataFrame, mc_sum: pd.DataFrame,
                                     empty_sum: pd.DataFrame, hd95: pd.DataFrame,
                                     cohort: pd.DataFrame, ca: pd.DataFrame,
                                     crop_cmp: pd.DataFrame, worsened: pd.DataFrame,
                                     sens: pd.DataFrame) -> pd.DataFrame:
    def dir_of(x):
        return 'INCREASE' if x > 0 else ('DECREASE' if x < 0 else 'NO_CHANGE')
    mean_dd = delta.groupby('model')['delta_dice'].mean()
    mean_orec = delta.groupby('model')['delta_object_recall'].mean()
    rec = int(delta.recovered_components.sum())
    tiny = size[size.size_stratum == 'TINY']
    small = size[size.size_stratum == 'SMALL']
    emp = int(empty_sum.recovered_empty_cases.sum())
    afl = cohort[cohort.cohort == 'ALL_FOUR_LOW']
    hard = cohort[cohort.cohort == 'PHASE11_HARD_CASE']
    # cohort table holds aggregated means; fall back to per-case table when available
    afl_mean = (afl['mean_delta_dice'].mean() if 'mean_delta_dice' in afl.columns
                else (afl['delta_dice'].mean() if 'delta_dice' in afl.columns else 0.0))
    hard_mean = (hard['mean_delta_dice'].mean() if 'mean_delta_dice' in hard.columns
                 else (hard['delta_dice'].mean() if 'delta_dice' in hard.columns else 0.0))
    rows = [
        ('paired_dice', 'phase12_clean_v3_primary_paired_deltas.csv', 'FULL_FIELD 103 x 4 models',
         'all four', dir_of(mean_dd.mean()), f'mean delta_dice per model: {mean_dd.round(4).to_dict()}',
         'single seed; no significance testing', 'SUPPORTIVE_DESCRIPTIVE_EVIDENCE'),
        ('object_recall', 'phase12_clean_v3_primary_paired_deltas.csv', 'FULL_FIELD 103 x 4 models',
         'all four', dir_of(mean_orec.mean()), f'mean delta_object_recall per model: {mean_orec.round(4).to_dict()}',
         'object recall uses >=1 px overlap', 'SUPPORTIVE_DESCRIPTIVE_EVIDENCE'),
        ('component_recovery', 'phase12_primary_component_recovery_events.csv', '152 components x 4 models',
         'all four', dir_of(rec), f'total RECOVERED component detections: {rec}',
         'native component identity; no case attribution', 'SUPPORTIVE_DESCRIPTIVE_EVIDENCE'),
        ('TINY_recovery', 'phase12_primary_size_stratified_component_recovery.csv', '72 TINY components',
         'all four', dir_of(int(tiny.recovered_components.sum()) - int(tiny.lost_components.sum())),
         f'TINY recovered {int(tiny.recovered_components.sum())}, lost {int(tiny.lost_components.sum())}',
         'FULL_FIELD only; kub_size_clean_v3_v1', 'SUPPORTIVE_DESCRIPTIVE_EVIDENCE'),
        ('SMALL_recovery', 'phase12_primary_size_stratified_component_recovery.csv', '28 SMALL components',
         'all four', dir_of(int(small.recovered_components.sum()) - int(small.lost_components.sum())),
         f'SMALL recovered {int(small.recovered_components.sum())}, lost {int(small.lost_components.sum())}',
         'FULL_FIELD only', 'SUPPORTIVE_DESCRIPTIVE_EVIDENCE'),
        ('empty_recovery', 'phase12_primary_empty_prediction_recovery.csv', 'global-empty cases',
         'all four', dir_of(emp), f'recovered empty cases: {emp}',
         'empty = zero foreground pixels', 'SUPPORTIVE_DESCRIPTIVE_EVIDENCE'),
        ('phase11_all_four_low_recovery', 'phase12_all_four_low_oracle_response.csv', '12 frozen cases x 4 models',
         'all four', dir_of(afl_mean), f'mean delta_dice {afl_mean:.4f} (per-model means '
         f'{afl.set_index("model")["delta_dice"].mean().round(4).to_dict() if "delta_dice" in afl.columns else "see cohort table"})',
         'frozen cohort, not reselected', 'SUPPORTIVE_DESCRIPTIVE_EVIDENCE'),
        ('phase11_hard_case_recovery', 'phase12_phase11_frozen_cohort_oracle_response.csv',
         'frozen hard cohort (10 of 16 in FULL_FIELD) x 4 models', 'all four',
         dir_of(hard_mean), f'mean delta_dice {hard_mean:.4f} (aggregated over case-model rows)',
         'only FULL_FIELD members enter this population', 'SUPPORTIVE_DESCRIPTIVE_EVIDENCE'),
        ('worsening_cases', 'phase12_primary_worsened_cases.csv', 'cases with delta_dice < 0',
         'all four', 'PRESENT', f'{len(worsened)} case-model rows worsen; max worsening '
         f'{worsened.delta_dice.min():.4f}',
         'exhaustive, not cherry-picked', 'MIXED_DESCRIPTIVE_EVIDENCE'),
        ('fp_precision_cost', 'phase12_primary_benefit_cost_summary.csv', 'FULL_FIELD 103 x 4 models',
         'all four', 'MIXED',
         f'mean delta_precision {delta.groupby("model").delta_precision.mean().round(4).to_dict()}',
         'oracle-constrained FP is artificially advantaged', 'MIXED_DESCRIPTIVE_EVIDENCE'),
        ('boundary_effect', 'phase12_primary_hd95_analysis.csv', 'both-valid paired cases',
         'all four', dir_of(hd95.delta_hd95_median.mean()),
         f'median delta_hd95 per model: {hd95.delta_hd95_median.round(3).to_dict()}',
         'invalid HD95 flagged; paired subset only', 'MIXED_DESCRIPTIVE_EVIDENCE'),
        ('cross_architecture_consistency', 'phase12_cross_architecture_oracle_consistency.csv',
         'FULL_FIELD 103 cases', 'all four',
         'MIXED', f'cases with 4/4 positive delta_dice: {int(ca.all_four_delta_positive.sum())} of {len(ca)}',
         'no generality threshold defined', 'MIXED_DESCRIPTIVE_EVIDENCE'),
        ('crop_only_comparator', 'phase12_primary_vs_crop_only_comparator.csv', 'FULL_FIELD 103 x 4 models',
         'all four', 'PRESENT', 'crop-only exceeds primary due to oracle background suppression',
         'crop-only is a comparator, not the primary estimate', 'MIXED_DESCRIPTIVE_EVIDENCE'),
        ('legacy_restore_sensitivity', 'phase12_float_vs_legacy_mapback_sensitivity.csv',
         'FULL_FIELD 103 x 4 models', 'all four', 'SMALL',
         f'max abs Dice diff {sens.max_abs_dice_diff.max():.4f}',
         'COMBINED_LEGACY_RESTORE_SENSITIVITY (uint8 + engine confound); not gate-usable',
         'NOT_EVALUABLE'),
    ]
    return pd.DataFrame(rows, columns=['dimension', 'evidence_source', 'population', 'models',
                                       'observed_direction', 'quantitative_summary',
                                       'limitation', 'status'])


# ---------------------------------------------------------------------------
# Upstream epoch tables
# ---------------------------------------------------------------------------

def load_upstream_epoch_table(key: str) -> pd.DataFrame:
    return pd.read_csv(PHASE10_EPOCH_TABLES[key])


def verify_upstream_epoch_tables() -> pd.DataFrame:
    rows = []
    for k in MODELS:
        d = load_upstream_epoch_table(k)
        eps = d['epoch'].astype(int).tolist()
        exp = EXPECTED_EPOCH_ROWS[k]
        expected = list(range(1, exp + 1))
        rows.append({'model': DISPLAY[k], 'rows': len(d), 'expected_rows': exp,
                     'row_count_matches': len(d) == exp, 'contiguous': eps == expected,
                     'sha256': sha256_file(PHASE10_EPOCH_TABLES[k])})
    return pd.DataFrame(rows)
