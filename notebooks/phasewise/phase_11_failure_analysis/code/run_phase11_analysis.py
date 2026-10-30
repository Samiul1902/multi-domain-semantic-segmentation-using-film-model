"""Run the Phase 11 Part 1B four-model clean-v3 failure analysis and write all tables.

Read-only: uses the cached prediction pass (experiments/phase11_pred_cache_per_model.csv)
produced by phase11_failure_analysis.run_prediction_pass, which itself is read-only.
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(r'D:\Softfors\jup')))
sys.path.insert(0, str(Path(r'D:\Softfors\jup') / 'notebooks' / 'phasewise' / 'phase_11_failure_analysis' / 'code'))
import phase11_failure_analysis as fa
from scipy.ndimage import label

ROOT = Path(r'D:\Softfors\jup')
T = fa.TABLES
CACHE = ROOT / 'experiments' / 'phase11_pred_cache_per_model.csv'

per_model = pd.read_csv(CACHE)
print('per-model rows:', len(per_model), '(expected 1120)')
assert len(per_model) == 1120

# ---------------------------------------------------------------- 7. decile cutoffs
cuts = fa.low_dice_cutoffs(per_model)
cuts.to_csv(T / 'phase11_clean_v3_low_dice_decile_cutoffs.csv', index=False)
print('\n=== LOW-DICE CLEAN Q10 (per model, bottom decile) ===')
print(cuts[['model', 'n', 'q10_cutoff', 'count_le_cutoff', 'prevalence', 'tie_count_at_cutoff']].to_string(index=False))

per_model = fa.apply_low_dice(per_model, cuts)

# ---------------------------------------------------------------- 8. anchor cutoffs
anchor = fa.anchor_decile_cutoffs(per_model)
anchor.to_csv(T / 'phase11_clean_v3_unetpp_failure_decile_cutoffs.csv', index=False)
print('\n=== UNET++ ANCHOR CLEAN DECILES ===')
for c in ['clean_v3_low_dice_q10', 'low_dice_count', 'hd95_valid_n', 'hd95_invalid_n',
          'clean_v3_hd95_q90_valid', 'high_hd95_count', 'clean_v3_fp_q90', 'high_fp_count']:
    print(f'  {c}: {anchor.loc[0, c]}')

# ---------------------------------------------------------------- 10. per-model case table
per_model.to_csv(T / 'phase11_clean_v3_per_model_case_failure_metrics.csv', index=False)
print('\nwrote phase11_clean_v3_per_model_case_failure_metrics.csv')

# ---------------------------------------------------------------- 11. paired summary
paired = fa.paired_summary(per_model)
paired.to_csv(T / 'phase11_clean_v3_paired_case_failure_summary.csv', index=False)
print('\n=== SHARED FAILURE (ALL_FOUR_LOW) ===')
print('ALL_FOUR_LOW count:', int(paired['ALL_FOUR_LOW'].sum()), f"/ {len(paired)}")
print('low_model_count distribution:', paired['low_model_count'].value_counts().sort_index().to_dict())
print('empty_prediction_model_count dist:', paired['empty_prediction_model_count'].value_counts().sort_index().to_dict())
print('missed_component_model_count dist:', paired['missed_component_model_count'].value_counts().sort_index().to_dict())

# ---------------------------------------------------------------- 21/22. disagreement
disag = fa.disagreement_table(paired, per_model)
disag.to_csv(T / 'phase11_clean_v3_architecture_disagreement.csv', index=False)
top = fa.top_disagreement(disag, 4)
top.to_csv(T / 'phase11_clean_v3_top_disagreement_cases.csv', index=False)
print('\n=== DISAGREEMENT (dice_range, continuous; NO threshold) ===')
print('dice_range: mean %.4f median %.4f max %.4f' % (disag.dice_range.mean(), disag.dice_range.median(), disag.dice_range.max()))
print('top 4 sample_ids:', list(top['sample_id']))

# ---------------------------------------------------------------- 32. failure summary by model
rows = []
for key in fa.MODELS:
    d = per_model[per_model['model'] == key]
    val = d[d['hd95_valid']]
    multi = d[d['is_multicomponent']]
    def cls(r):
        if r['gt_eval_components'] == 0:
            return 'NO_GT_COMPONENT'
        if r['detected_gt_eval_components'] == r['gt_eval_components']:
            return 'COMPLETE_DETECTION'
        if r['detected_gt_eval_components'] == 0:
            return 'COMPLETE_MISS'
        return 'PARTIAL_DETECTION'
    mcls = multi.apply(cls, axis=1).value_counts()
    rows.append({
        'model': fa.DISPLAY[key], 'n': len(d),
        'mean_dice': d['dice'].mean(), 'median_dice': d['dice'].median(),
        'empty_predictions': int(d['prediction_empty'].sum()),
        'empty_pct': float(d['prediction_empty'].mean()),
        'gt_eval_components': int(d['gt_eval_components'].sum()),
        'detected_components': int(d['detected_gt_eval_components'].sum()),
        'missed_components': int(d['missed_gt_eval_components'].sum()),
        'object_recall': float(d['detected_gt_eval_components'].sum() / max(1, d['gt_eval_components'].sum())),
        'fp_eval_components': int(d['fp_eval_components'].sum()),
        'mean_fp_components': float(d['fp_eval_components'].mean()),
        'hd95_valid_n': int(len(val)), 'hd95_invalid_n': int((~d['hd95_valid']).sum()),
        'median_hd95_valid': float(val['hd95'].median()) if len(val) else np.nan,
        'multicomponent_cases': int(len(multi)),
        'multi_complete': int(mcls.get('COMPLETE_DETECTION', 0)),
        'multi_partial': int(mcls.get('PARTIAL_DETECTION', 0)),
        'multi_miss': int(mcls.get('COMPLETE_MISS', 0)),
        'mean_tp_pixels': float(d['tp_pixels'].mean()), 'mean_fp_pixels': float(d['fp_pixels'].mean()),
        'mean_fn_pixels': float(d['fn_pixels'].mean()),
        'mean_fp_fraction': float(d['fp_fraction'].mean()), 'mean_fn_fraction': float(d['fn_fraction'].mean()),
        'mean_pred_gt_area_ratio': float(d['pred_gt_area_ratio'].mean()),
        'status': 'DESCRIPTIVE_SINGLE_SEED_ONLY',
    })
summary = pd.DataFrame(rows)
summary.to_csv(T / 'phase11_clean_v3_failure_summary_by_model.csv', index=False)
print('\n=== FAILURE SUMMARY BY MODEL ===')
print(summary[['model', 'mean_dice', 'empty_predictions', 'object_recall', 'missed_components',
               'fp_eval_components', 'hd95_valid_n', 'hd95_invalid_n', 'multicomponent_cases']].to_string(index=False))

# ---------------------------------------------------------------- regime / category
regime = fa.subgroup(per_model, 'acquisition_type')
regime.to_csv(T / 'phase11_clean_v3_failure_by_acquisition.csv', index=False)
print('\n=== REGIME (mandatory separation) ===')
print(regime[['model_display', 'acquisition_type', 'n', 'mean_dice', 'empty_pred_pct',
              'object_recall', 'hd95_valid_n', 'hd95_invalid_n']].to_string(index=False))

cat = fa.subgroup(per_model, 'category')
cat.to_csv(T / 'phase11_clean_v3_failure_by_category.csv', index=False)
print('\n=== CATEGORY (metadata subgroup) ===')
print(cat[['model_display', 'category', 'n', 'mean_dice', 'empty_pred_pct']].to_string(index=False))

# ---------------------------------------------------------------- empty prediction
emp = per_model.groupby(['model_display', 'acquisition_type'])['prediction_empty'].agg(['sum', 'mean']).reset_index()
emp.to_csv(T / 'phase11_clean_v3_empty_prediction_analysis.csv', index=False)
print('\n=== EMPTY PREDICTIONS ===')
print(emp.to_string(index=False))

# ---------------------------------------------------------------- boundary (HD95)
bd = per_model.groupby('model_display').agg(
    n_total=('hd95', 'size'), n_valid=('hd95_valid', 'sum'),
    median_hd95=('hd95', 'median'), mean_hd95=('hd95', 'mean')).reset_index()
bd['n_invalid'] = bd['n_total'] - bd['n_valid']
bd['valid_rate'] = bd['n_valid'] / bd['n_total']
# NOTE: bd is sorted alphabetically by groupby -> map q90 by model name, never positionally
hd_q90_map = {fa.DISPLAY[k]: float(fa.q(
    per_model[(per_model.model == k) & per_model.hd95_valid]['hd95'].astype(float).values, 0.90))
    for k in fa.MODELS}
bd['q90_hd95_valid'] = bd['model_display'].map(hd_q90_map)
bd['note'] = 'invalid (empty pred / empty GT) explicitly accounted, never dropped'
bd.to_csv(T / 'phase11_clean_v3_boundary_hd95_summary.csv', index=False)
print('\n=== BOUNDARY / HD95 ===')
print(bd[['model_display', 'n_total', 'n_valid', 'n_invalid', 'valid_rate', 'median_hd95', 'q90_hd95_valid']].to_string(index=False))

# ---------------------------------------------------------------- FP burden
fpb = per_model.groupby('model_display')['fp_eval_components'].agg(
    mean='mean', median='median', max='max').reset_index()
# NOTE: fpb is sorted alphabetically by groupby -> map q90 by model name, never positionally
fp_q90_map = {fa.DISPLAY[k]: float(fa.q(
    per_model[per_model.model == k]['fp_eval_components'].astype(float).values, 0.90))
    for k in fa.MODELS}
fpb['q90'] = fpb['model_display'].map(fp_q90_map)
fpb['note'] = 'HIGH_FP_DECILE frozen only for UNet++ anchor; others descriptive'
fpb.to_csv(T / 'phase11_clean_v3_fp_burden_summary.csv', index=False)
print('\n=== FP BURDEN ===')
print(fpb.to_string(index=False))

# ---------------------------------------------------------------- TP/FP/FN extension
px = per_model.groupby(['model_display', 'acquisition_type']).agg(
    mean_tp=('tp_pixels', 'mean'), mean_fp=('fp_pixels', 'mean'), mean_fn=('fn_pixels', 'mean'),
    mean_fp_frac=('fp_fraction', 'mean'), mean_fn_frac=('fn_fraction', 'mean'),
    mean_area_ratio=('pred_gt_area_ratio', 'mean')).reset_index()
px['status'] = 'CLEAN_V3_DESCRIPTIVE_EXTENSION'
px.to_csv(T / 'phase11_clean_v3_pixel_error_extension.csv', index=False)
print('\n=== TP/FP/FN EXTENSION (descriptive) ===')
print(px.to_string(index=False))

# ---------------------------------------------------------------- multicomponent
mc_rows = []
for key in fa.MODELS:
    d = per_model[(per_model['model'] == key) & per_model['is_multicomponent']]
    def cls(r):
        if r['detected_gt_eval_components'] == r['gt_eval_components']:
            return 'COMPLETE_DETECTION'
        if r['detected_gt_eval_components'] == 0:
            return 'COMPLETE_MISS'
        return 'PARTIAL_DETECTION'
    counts = d.apply(cls, axis=1).value_counts()
    mc_rows.append({'model': fa.DISPLAY[key], 'multicomponent_cases': len(d),
                    'COMPLETE_DETECTION': int(counts.get('COMPLETE_DETECTION', 0)),
                    'PARTIAL_DETECTION': int(counts.get('PARTIAL_DETECTION', 0)),
                    'COMPLETE_MISS': int(counts.get('COMPLETE_MISS', 0)),
                    'connectivity': 8,
                    'membership_space': 'ORIGINAL_NATIVE (8-conn component count > 1)',
                    'detection_space': 'EVALUATION_512 (8-conn, >=1px overlap)'})
mc = pd.DataFrame(mc_rows)
mc.to_csv(T / 'phase11_clean_v3_multicomponent_analysis.csv', index=False)
print('\n=== MULTI-COMPONENT (8-conn) ===')
print(mc.to_string(index=False))

# ---------------------------------------------------------------- FULL_FIELD size strata (native)
from src.utils.targets import binarize_mask
from PIL import Image
size_rows = []
ff = per_model[per_model['acquisition_type'] == 'FULL_FIELD']
frame = fa.kub_val_frame()
meta = frame[['sample_id', 'mask_path']].drop_duplicates()
comp_info = []
for _, r in meta.iterrows():
    gt_full = binarize_mask(np.array(Image.open(r['mask_path']).convert('L'))).astype(np.uint8)
    lab, n = label(gt_full > 0, structure=fa.STRUCT8)
    H, W = gt_full.shape
    for gid in range(1, n + 1):
        px_ = int(np.sum(lab == gid))
        ratio = px_ / (H * W)
        stratum = 'TINY' if ratio <= fa.Q25 else 'SMALL' if ratio <= fa.Q50 else 'MEDIUM' if ratio <= fa.Q75 else 'LARGE'
        comp_info.append({'sample_id': r['sample_id'], 'stratum': stratum})
ci = pd.DataFrame(comp_info)
for key in fa.MODELS:
    d = ff[ff['model'] == key].copy()
    def cls(r):
        if r['detected_gt_eval_components'] == r['gt_eval_components']:
            return 'COMPLETE_DETECTION'
        if r['detected_gt_eval_components'] == 0:
            return 'COMPLETE_MISS'
        return 'PARTIAL_DETECTION'
    d['det_class'] = d.apply(cls, axis=1)
    merged = ci.merge(d[['sample_id', 'det_class']], on='sample_id', how='left')
    g = merged.groupby('stratum').agg(GT_components=('stratum', 'size')).reset_index()
    for c in ['COMPLETE_DETECTION', 'PARTIAL_DETECTION', 'COMPLETE_MISS']:
        g[c] = g['stratum'].map(merged[merged.det_class == c].groupby('stratum').size()).fillna(0).astype(int)
    g['model'] = fa.DISPLAY[key]
    g['space_note'] = 'strata from ORIGINAL_NATIVE FULL_FIELD; detection outcome is case-level EVALUATION_512 (approximate attribution)'
    size_rows.append(g)
size = pd.concat(size_rows, ignore_index=True)
size.to_csv(T / 'phase11_clean_v3_fullfield_size_stratum_object_analysis.csv', index=False)
print('\n=== FULL_FIELD SIZE STRATA (kub_size_clean_v3_v1, native) ===')
print(size[['model', 'stratum', 'GT_components', 'COMPLETE_DETECTION', 'PARTIAL_DETECTION', 'COMPLETE_MISS']].to_string(index=False))

print('\nALL TABLES WRITTEN')
