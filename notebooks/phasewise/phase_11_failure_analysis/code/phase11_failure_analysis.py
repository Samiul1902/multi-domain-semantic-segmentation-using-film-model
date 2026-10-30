"""
Phase 11 Part 1B — CLEAN-v3 four-model failure analysis (READ-ONLY).

Implements the SUPERVISOR-FROZEN protocol recorded in
reports/audits/phase11_clean_v3_failure_protocol_frozen.json.

Read-only. Forbidden: training, optimizer.step, checkpoint writes, config changes,
threshold tuning, TEST reads, winner declaration, reference-model selection.

UNet++ is used ONLY as HISTORICAL_REPLICATION_ANALYSIS_ANCHOR for the historically
anchored single-model strata. All four models are analysed.

Prediction pass reproduces validation-time numerics:
  - canonical KUBDataset + DataLoader(batch_size=4, shuffle=False)
  - canonical resize math: max(1, round(extent * scale))   (NOT int())
  - AMP autocast on CUDA
  - threshold 0.5
Aggregate macro Dice must reproduce frozen Phase-10 values within 1e-4.

Author: Gemini 3.1 Pro High
Date: 2026-09-21
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import torch
import yaml
from PIL import Image

PROJECT_ROOT = Path(r'D:\Softfors\jup')
REPORTS = PROJECT_ROOT / 'reports'
TABLES = REPORTS / 'tables'
FIGURES = REPORTS / 'figures'
AUDITS = REPORTS / 'audits'

THRESHOLD = 0.5
TARGET = 512
BATCH = 4
CONNECTIVITY = 8          # 8-connectivity, both component spaces
MIN_OVERLAP = 1           # >=1 px overlap => GT component detected
MATERIAL_TOL = 1e-4       # aggregate Dice reproduction tolerance

MODELS = ['unet', 'attention_unet', 'unetpp', 'deeplabv3plus']
DISPLAY = {'unet': 'UNet', 'attention_unet': 'Attention U-Net',
           'unetpp': 'UNet++', 'deeplabv3plus': 'DeepLabV3+'}
ANCHOR = 'unetpp'   # HISTORICAL_REPLICATION_ANALYSIS_ANCHOR (NOT a winner/reference)

SPECS = {
    'unet': {'experiment_id': 'phase9_kub_unet_baseline_seed42_512_clean_v3',
             'config': PROJECT_ROOT / 'configs/phase09_clean_v3/phase09_unet_baseline_clean_v3.yaml',
             'best': PROJECT_ROOT / 'checkpoints/phase9_kub_unet_baseline_seed42_512_clean_v3/best.pt'},
    'attention_unet': {'experiment_id': 'phase10_kub_attention_unet_seed42_512_clean_v3',
                       'config': PROJECT_ROOT / 'configs/phase10_clean_v3/phase10_attention_unet_clean_v3.yaml',
                       'best': PROJECT_ROOT / 'checkpoints/phase10_kub_attention_unet_seed42_512_clean_v3/best.pt'},
    'unetpp': {'experiment_id': 'phase10_kub_unetpp_seed42_512_clean_v3',
               'config': PROJECT_ROOT / 'configs/phase10_clean_v3/phase10_unetpp_clean_v3.yaml',
               'best': PROJECT_ROOT / 'checkpoints/phase10_kub_unetpp_seed42_512_clean_v3/best.pt'},
    'deeplabv3plus': {'experiment_id': 'phase10_kub_deeplabv3plus_seed42_512_clean_v3',
                      'config': PROJECT_ROOT / 'configs/phase10_clean_v3/phase10_deeplabv3plus_clean_v3.yaml',
                      'best': PROJECT_ROOT / 'checkpoints/phase10_kub_deeplabv3plus_seed42_512_clean_v3/best.pt'},
}

AUTHORITATIVE = {
    'unet': 0.7406133413314819, 'attention_unet': 0.7525129853960107,
    'unetpp': 0.7641595156062713, 'deeplabv3plus': 0.7509140344161673,
}

# clean-v3 size taxonomy (FULL_FIELD only)
Q25, Q50, Q75 = 0.0001497998649691358, 0.0003401438395182292, 0.0008279682677469136
TAXONOMY_ID = 'kub_size_clean_v3_v1'

STRUCT8 = np.ones((3, 3), dtype=bool)


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Frozen quantile helper (historical method: np.quantile default 'linear', float64)
# ---------------------------------------------------------------------------

def q(values, prob: float) -> float:
    v = np.asarray(values, dtype=np.float64)
    return float(np.quantile(v, prob))


# ---------------------------------------------------------------------------
# Model / data
# ---------------------------------------------------------------------------

def load_model(key: str, device: str = 'cuda'):
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    from src.utils.device import get_device
    if key == 'unet':
        from src.models.unet import UNet as M
    elif key == 'attention_unet':
        from src.models.attention_unet import AttentionUNet as M
    elif key == 'unetpp':
        from src.models.unetpp import UNetPlusPlus as M
    else:
        from src.models.deeplabv3plus import DeepLabV3Plus as M
    ck = torch.load(SPECS[key]['best'], map_location='cpu', weights_only=False)
    model = M(in_channels=ck['configuration']['model']['input_channels'],
              out_channels=ck['configuration']['model']['output_channels'],
              base_channels=ck['configuration']['model']['base_channels'])
    model.load_state_dict(ck['model_state'])
    dev = get_device(require_cuda=(device != 'cpu'))
    return model.to(dev).eval(), dev


def kub_val_frame() -> pd.DataFrame:
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    from src.data.kub_dataset import KUBDataset, derive_acquisition_type
    ds = KUBDataset(manifest_path=PROJECT_ROOT / 'manifests' / 'phase4_v3' / 'val.csv',
                    split='VAL', target_size=TARGET)
    f = ds.frame.copy()
    f['acquisition_type'] = f['image_path'].apply(derive_acquisition_type)
    return f[['sample_id', 'patient_id', 'category', 'image_path', 'mask_path', 'acquisition_type']].reset_index(drop=True)


def make_loader():
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    from torch.utils.data import DataLoader
    from src.data.kub_dataset import KUBDataset
    ds = KUBDataset(manifest_path=PROJECT_ROOT / 'manifests' / 'phase4_v3' / 'val.csv',
                    split='VAL', target_size=TARGET)
    return DataLoader(ds, batch_size=BATCH, shuffle=False, num_workers=0, pin_memory=True), ds


def _native_components(gt_full: np.ndarray) -> int:
    from scipy.ndimage import label
    _, n = label(gt_full > 0, structure=STRUCT8)
    return int(n)


def _eval_components(gt_eval: np.ndarray, pred_eval: np.ndarray):
    """8-conn components in evaluation-512 space; overlap-based detection (>=1 px)."""
    from scipy.ndimage import label
    gt_lab, n_gt = label(gt_eval > 0, structure=STRUCT8)
    pr_lab, n_pr = label(pred_eval > 0, structure=STRUCT8)
    detected = 0
    for gid in range(1, n_gt + 1):
        overlap = np.unique(pr_lab[gt_lab == gid])
        overlap = overlap[overlap > 0]
        if any(int(np.sum((pr_lab == pid) & (gt_lab == gid))) >= MIN_OVERLAP for pid in overlap):
            detected += 1
    fp = 0
    for pid in range(1, n_pr + 1):
        if not np.any(gt_lab[pr_lab == pid] > 0):
            fp += 1
    return int(n_gt), int(n_pr), int(detected), int(n_gt - detected), int(fp)


def _case_metrics(gt: np.ndarray, prob: np.ndarray) -> Dict[str, Any]:
    """Case metrics on the padded 512 evaluation grid (matches validation numerics).

    NOTE: src.metrics.segmentation.binary_metrics expects LOGITS (it applies sigmoid
    internally). Passing already-binary 0/1 would make every pixel 'foreground'.
    We therefore compute the pixel metrics directly here, using the SAME formulas and
    the SAME epsilon (1e-7) as binary_metrics, to stay numerically consistent.
    """
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    from src.metrics.segmentation import hd95

    pred = (prob >= THRESHOLD).astype(np.uint8)
    gtb = gt.astype(np.uint8)
    h = hd95(pred.astype(bool), gtb.astype(bool))

    tp = float(np.sum((pred == 1) & (gtb == 1)))
    fp = float(np.sum((pred == 1) & (gtb == 0)))
    fn = float(np.sum((pred == 0) & (gtb == 1)))
    eps = 1e-7  # identical to src/metrics/segmentation.binary_metrics
    dice = (2 * tp + eps) / (2 * tp + fp + fn + eps)
    iou = (tp + eps) / (tp + fp + fn + eps)
    precision = (tp + eps) / (tp + fp + eps)
    recall = (tp + eps) / (tp + fn + eps)

    gt_px = float(np.sum(gtb == 1))
    pred_px = float(np.sum(pred == 1))
    return {
        'dice': float(dice), 'iou': float(iou),
        'precision': float(precision), 'recall': float(recall),
        'hd95': float(h['hd95']) if h['hd95_valid'] else np.nan,
        'hd95_valid': bool(h['hd95_valid']),
        'hd95_invalid_reason': h.get('invalid_reason', ''),
        'prediction_empty': bool(pred_px == 0),
        'tp_pixels': tp, 'fp_pixels': fp, 'fn_pixels': fn,
        'gt_pixels': gt_px, 'pred_pixels': pred_px,
        'pred_gt_area_ratio': float(pred_px / gt_px) if gt_px > 0 else np.nan,
        'fp_fraction': float(fp / (fp + gt_px)) if (fp + gt_px) > 0 else np.nan,
        'fn_fraction': float(fn / gt_px) if gt_px > 0 else np.nan,
    }


def run_prediction_pass(verbose: bool = True):
    """Read-only inference for all four models.

    Uses the canonical KUBDataset loader so the padded-512 GT is validation-identical.
    Returns (per_model_case_table, reproduction_gate_table).
    """
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    from src.utils.targets import binarize_mask

    loader, ds = make_loader()

    rows, repro = [], {}
    for key in MODELS:
        model, dev = load_model(key)
        if verbose:
            print(f'  inference {DISPLAY[key]} ...')
        dice_all = []
        for batch in loader:
            imgs = batch['image'].to(dev)
            with torch.no_grad():
                with torch.amp.autocast('cuda', enabled=(dev.type == 'cuda')):
                    out = model(imgs)
                probs = torch.sigmoid(out).float().cpu().numpy()[:, 0]
            masks = batch['mask'].cpu().numpy()[:, 0]
            for b in range(probs.shape[0]):
                gt = (masks[b] > 0).astype(np.uint8)   # canonical padded-512 GT, mask > 0
                prob = probs[b]
                m = _case_metrics(gt, prob)
                n_gt_e, n_pr_e, det, missed, fp_c = _eval_components(gt, (prob >= THRESHOLD).astype(np.uint8))
                # native (original) space component count / size taxonomy source
                gt_full = binarize_mask(np.array(Image.open(batch['mask_path'][b]).convert('L'))).astype(np.uint8)
                n_native = _native_components(gt_full)
                H, W = gt_full.shape
                rows.append({
                    'sample_id': batch['sample_id'][b],
                    'patient_id': batch['patient_id'][b],
                    'category': batch['category'][b],
                    'acquisition_type': batch['acquisition_type'][b],
                    'model': key, 'model_display': DISPLAY[key],
                    **m,
                    'gt_eval_components': n_gt_e, 'pred_eval_components': n_pr_e,
                    'detected_gt_eval_components': det, 'missed_gt_eval_components': missed,
                    'fp_eval_components': fp_c,
                    'object_recall': float(det / n_gt_e) if n_gt_e > 0 else np.nan,
                    'original_gt_component_count': n_native,
                    'is_multicomponent': bool(n_native > 1),
                    'native_height': int(H), 'native_width': int(W),
                })
                dice_all.append(m['dice'])
        repro[key] = {'recomputed': float(np.mean(dice_all)),
                      'authoritative': AUTHORITATIVE[key],
                      'abs_diff': abs(float(np.mean(dice_all)) - AUTHORITATIVE[key])}
        if verbose:
            print(f"    macro Dice {repro[key]['recomputed']:.10f} vs "
                  f"{repro[key]['authoritative']:.10f} (|d|={repro[key]['abs_diff']:.2e})")
        del model
        torch.cuda.empty_cache()

    df = pd.DataFrame(rows)
    gate = pd.DataFrame([{'model': DISPLAY[k], 'model_key': k, **v,
                          'pass_1e-4': bool(v['abs_diff'] < MATERIAL_TOL)} for k, v in repro.items()])
    return df, gate


# ---------------------------------------------------------------------------
# Frozen-protocol derivations
# ---------------------------------------------------------------------------

def low_dice_cutoffs(per_model: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for key in MODELS:
        d = per_model[per_model['model'] == key]['dice'].astype(float)
        cut = q(d.values, 0.10)
        n_le = int((d <= cut).sum())
        ties = int((d == cut).sum())
        rows.append({'model': DISPLAY[key], 'model_key': key, 'n': int(len(d)),
                     'quantile_method': "np.quantile(values, 0.10) default 'linear' float64",
                     'q10_cutoff': float(cut), 'count_le_cutoff': n_le,
                     'prevalence': float(n_le / len(d)), 'tie_count_at_cutoff': ties})
    return pd.DataFrame(rows)


def apply_low_dice(per_model: pd.DataFrame, cuts: pd.DataFrame) -> pd.DataFrame:
    cut_map = dict(zip(cuts['model_key'], cuts['q10_cutoff']))
    hi_map = dict(zip(cuts['model_key'], cuts['q10_cutoff']))
    per_model = per_model.copy()
    per_model['low_dice_cutoff'] = per_model['model'].map(cut_map)
    per_model['low_dice_flag'] = per_model['dice'] <= per_model['low_dice_cutoff']
    return per_model


def anchor_decile_cutoffs(per_model: pd.DataFrame) -> pd.DataFrame:
    a = per_model[per_model['model'] == ANCHOR]
    dice_q10 = q(a['dice'].astype(float).values, 0.10)
    valid = a[a['hd95_valid']]
    hd95_q90 = q(valid['hd95'].astype(float).values, 0.90)
    fp_q90 = q(a['fp_eval_components'].astype(float).values, 0.90)
    return pd.DataFrame([{
        'anchor_model': DISPLAY[ANCHOR], 'anchor_role': 'HISTORICAL_REPLICATION_ANALYSIS_ANCHOR',
        'n_cases': int(len(a)),
        'clean_v3_low_dice_q10': float(dice_q10),
        'low_dice_count': int((a['dice'].astype(float) <= dice_q10).sum()),
        'hd95_valid_n': int(len(valid)), 'hd95_invalid_n': int((~a['hd95_valid']).sum()),
        'clean_v3_hd95_q90_valid': float(hd95_q90),
        'high_hd95_count': int((valid['hd95'].astype(float) >= hd95_q90).sum()),
        'clean_v3_fp_q90': float(fp_q90),
        'high_fp_count': int((a['fp_eval_components'].astype(float) >= fp_q90).sum()),
        'historical_v2_dice_q10_provenance': 0.5461063385009766,
        'historical_v2_hd95_q90_provenance': 83.07246563841615,
        'historical_v2_fp_cutoff_provenance': 4,
        'note': 'clean-v3 cutoffs recomputed; v2 values are provenance columns only',
    }])


def paired_summary(per_model: pd.DataFrame) -> pd.DataFrame:
    piv = per_model.pivot_table(index='sample_id',
                                columns='model', values=['dice', 'low_dice_flag', 'prediction_empty',
                                                         'missed_gt_eval_components', 'fp_eval_components'],
                                aggfunc='first')
    meta = per_model[per_model['model'] == MODELS[0]][['sample_id', 'patient_id', 'category', 'acquisition_type']]
    out = meta.set_index('sample_id')
    dice = piv['dice']
    out['dice_min'] = dice.min(axis=1); out['dice_max'] = dice.max(axis=1)
    out['dice_mean'] = dice.mean(axis=1); out['dice_median'] = dice.median(axis=1)
    out['dice_range'] = out['dice_max'] - out['dice_min']
    out['dice_sd'] = dice.std(axis=1, ddof=1)
    low = piv['low_dice_flag']
    out['low_model_count'] = low.sum(axis=1).astype(int)
    out['ALL_FOUR_LOW'] = (out['low_model_count'] == 4)
    out['empty_prediction_model_count'] = piv['prediction_empty'].sum(axis=1).astype(int)
    out['missed_component_model_count'] = (piv['missed_gt_eval_components'] > 0).sum(axis=1).astype(int)
    return out.reset_index()


def disagreement_table(paired: pd.DataFrame, per_model: pd.DataFrame) -> pd.DataFrame:
    piv = per_model.pivot_table(index='sample_id', columns='model', values='dice', aggfunc='first')
    meta = per_model[per_model['model'] == MODELS[0]][['sample_id', 'patient_id', 'category', 'acquisition_type']].set_index('sample_id')
    t = meta.join(piv.rename(columns=DISPLAY))
    t['dice_min'] = piv.min(axis=1); t['dice_max'] = piv.max(axis=1)
    t['dice_range'] = t['dice_max'] - t['dice_min']
    t['dice_sd'] = piv.std(axis=1, ddof=1)
    t = t.reset_index().sort_values(['dice_range', 'sample_id'], ascending=[False, True])
    return t


def top_disagreement(disag: pd.DataFrame, k: int = 4) -> pd.DataFrame:
    t = disag.head(k).copy()
    t['status'] = 'DESCRIPTIVE_DISAGREEMENT_DIAGNOSTIC_ONLY'
    return t


# ---------------------------------------------------------------------------
# Historical-style deterministic hard-case cohort (UNet++ anchor)
# ---------------------------------------------------------------------------

def _stratum_pick(pool: pd.DataFrame, order: List[str], ascending: List[bool], k: int) -> pd.DataFrame:
    if pool.empty:
        return pool
    return pool.sort_values(order, ascending=ascending).head(k)


def build_hard_cohort(per_model: pd.DataFrame, cuts: pd.DataFrame, anchor_cuts: pd.DataFrame) -> pd.DataFrame:
    a = per_model[per_model['model'] == ANCHOR].copy()
    dice_cut = float(anchor_cuts.loc[0, 'clean_v3_low_dice_q10'])
    fp_cut = float(anchor_cuts.loc[0, 'clean_v3_fp_q90'])
    a['low_dice_flag'] = a['dice'] <= dice_cut
    a['high_fp_flag'] = a['fp_eval_components'] >= fp_cut

    selected, order_rows, underfilled = [], [], []
    used = set()

    # A. EMPTY_PREDICTION  (lowest Dice, then sample_id)
    pool = a[(a['prediction_empty']) & (~a['sample_id'].isin(used))]
    pick = _regime_balanced(pool, ['dice', 'sample_id'], [True, True], 4)
    _append(selected, order_rows, pick, 'A_EMPTY_PREDICTION', 'prediction_empty; severity=dice asc')
    used |= set(pick['sample_id'])
    if len(pick) < 4:
        underfilled.append(('A_EMPTY_PREDICTION', len(pick), 4))

    # B. MISSED_EVAL_COMPONENTS > 0
    pool = a[(a['missed_gt_eval_components'] > 0) & (~a['sample_id'].isin(used))]
    pick = _regime_balanced(pool, ['missed_gt_eval_components', 'dice', 'sample_id'], [False, True, True], 4)
    _append(selected, order_rows, pick, 'B_MISSED_COMPONENT', 'missed_eval_components desc; dice asc')
    used |= set(pick['sample_id'])
    if len(pick) < 4:
        underfilled.append(('B_MISSED_COMPONENT', len(pick), 4))

    # C. HIGH_FP_DECILE
    pool = a[(a['high_fp_flag']) & (~a['sample_id'].isin(used))]
    pick = _regime_balanced(pool, ['fp_eval_components', 'dice', 'sample_id'], [False, True, True], 4)
    _append(selected, order_rows, pick, 'C_HIGH_FP_DECILE', f'fp_eval_components >= {fp_cut:g} (clean Q90)')
    used |= set(pick['sample_id'])
    if len(pick) < 4:
        underfilled.append(('C_HIGH_FP_DECILE', len(pick), 4))

    # D. LOW_DICE_DECILE
    pool = a[(a['low_dice_flag']) & (~a['sample_id'].isin(used))]
    pick = _regime_balanced(pool, ['dice', 'sample_id'], [True, True], 4)
    _append(selected, order_rows, pick, 'D_LOW_DICE_DECILE', f'dice <= {dice_cut:g} (clean Q10)')
    used |= set(pick['sample_id'])
    if len(pick) < 4:
        underfilled.append(('D_LOW_DICE_DECILE', len(pick), 4))

    out = pd.DataFrame(order_rows)
    if not out.empty:
        out['anchor_model'] = DISPLAY[ANCHOR]
        out['anchor_role'] = 'HISTORICAL_REPLICATION_ANALYSIS_ANCHOR'
        out['selection_status'] = 'DETERMINISTIC_PREDICTION_DEPENDENT'
    return out, underfilled


def _regime_balanced(pool: pd.DataFrame, order: List[str], ascending: List[bool], k: int) -> pd.DataFrame:
    """Target 2 FULL_FIELD + 2 ROI; fill shortfalls from the other regime using same severity order."""
    if pool.empty:
        return pool
    ff = _stratum_pick(pool[pool['acquisition_type'] == 'FULL_FIELD'], order, ascending, 2)
    roi = _stratum_pick(pool[pool['acquisition_type'] == 'ROI'], order, ascending, 2)
    picked = pd.concat([ff, roi])
    if len(picked) < k:
        rest = pool[~pool['sample_id'].isin(picked['sample_id'])]
        picked = pd.concat([picked, _stratum_pick(rest, order, ascending, k - len(picked))])
    return picked.sort_values(order, ascending=ascending).head(k)


def _append(selected, order_rows, pick, stratum, reason):
    for i, (_, r) in enumerate(pick.iterrows()):
        order_rows.append({
            'selection_order': len(order_rows) + 1, 'stratum': stratum,
            'sample_id': r['sample_id'], 'patient_id': r['patient_id'],
            'category': r['category'], 'acquisition': r['acquisition_type'],
            'dice': float(r['dice']), 'object_recall': float(r['object_recall']),
            'prediction_empty': bool(r['prediction_empty']),
            'missed_gt_eval_components': int(r['missed_gt_eval_components']),
            'fp_eval_components': int(r['fp_eval_components']),
            'selection_reason': reason,
            'duplicate_exclusion': 'excluded_if_selected_in_earlier_stratum',
        })


# ---------------------------------------------------------------------------
# Subgroup summaries
# ---------------------------------------------------------------------------

def subgroup(per_model: pd.DataFrame, by: str) -> pd.DataFrame:
    g = per_model.groupby(['model_display', by])
    out = g.agg(n=('dice', 'size'), mean_dice=('dice', 'mean'), median_dice=('dice', 'median'),
                empty_pred=('prediction_empty', 'sum'),
                gt_comp=('gt_eval_components', 'sum'), detected=('detected_gt_eval_components', 'sum'),
                missed=('missed_gt_eval_components', 'sum'),
                fp_comp=('fp_eval_components', 'sum'),
                hd95_valid_n=('hd95_valid', 'sum'),
                mean_fp_frac=('fp_fraction', 'mean'), mean_fn_frac=('fn_fraction', 'mean'),
                ).reset_index()
    out['object_recall'] = out['detected'] / out['gt_comp'].replace(0, np.nan)
    out['empty_pred_pct'] = out['empty_pred'] / out['n']
    out['hd95_invalid_n'] = out['n'] - out['hd95_valid_n']
    return out


def size_stratum_table(per_model: pd.DataFrame) -> pd.DataFrame:
    """FULL_FIELD only: per-component size strata via kub_size_clean_v3_v1 on native GT."""
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    from src.utils.targets import binarize_mask
    from src.analysis.kub_object_size import get_kub_size_taxonomy
    from scipy.ndimage import label

    tax = get_kub_size_taxonomy(TAXONOMY_ID)
    ff = per_model[(per_model['acquisition_type'] == 'FULL_FIELD')]
    rows = []
    for key in MODELS:
        sub = ff[ff['model'] == key]
        comp_rows = []
        for _, r in sub.iterrows():
            gt_full = binarize_mask(np.array(Image.open(r['mask_path']).convert('L'))).astype(np.uint8) \
                if 'mask_path' in r else None
            if gt_full is None:
                continue
            lab, n = label(gt_full > 0, structure=STRUCT8)
            H, W = gt_full.shape
            for gid in range(1, n + 1):
                px = int(np.sum(lab == gid))
                ratio = px / (H * W)
                comp_rows.append({'sample_id': r['sample_id'], 'component_px': px,
                                  'ratio': ratio, 'model': key})
        if not comp_rows:
            continue
        c = pd.DataFrame(comp_rows)
        # classify via taxonomy thresholds
        thr = tax if isinstance(tax, dict) else {}
        q25 = thr.get('Q25', Q25); q50 = thr.get('Q50', Q50); q75 = thr.get('Q75', Q75)
        c['stratum'] = np.select(
            [c['ratio'] <= q25, c['ratio'] <= q50, c['ratio'] <= q75],
            ['TINY', 'SMALL', 'MEDIUM'], default='LARGE')
        # detection: reuse case-level detected/missed split is not per-component; approximate
        # by case-level object recall attribution: count components in cases with complete detection
        det_map = sub.set_index('sample_id')['detected_gt_eval_components'].to_dict()
        gt_map = sub.set_index('sample_id')['gt_eval_components'].to_dict()
        def _det(r):
            g = gt_map.get(r['sample_id'], 0); d = det_map.get(r['sample_id'], 0)
            return d > 0 and g > 0 and (d / g) >= 1.0
        c['case_complete'] = c.apply(_det, axis=1)
        agg = c.groupby('stratum').agg(GT_components=('ratio', 'size'),
                                       cases_complete=('case_complete', 'sum')).reset_index()
        agg['model'] = DISPLAY[key]
        agg['model_key'] = key
        rows.append(agg)
    if not rows:
        return pd.DataFrame(columns=['model', 'stratum', 'GT_components', 'cases_complete'])
    out = pd.concat(rows, ignore_index=True)
    return out[['model', 'model_key', 'stratum', 'GT_components', 'cases_complete']]


# ---------------------------------------------------------------------------
# Visualisation (read-only; re-runs inference only for a small case subset)
# ---------------------------------------------------------------------------

def _load_gt(path: Path) -> np.ndarray:
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    from src.utils.targets import binarize_mask
    return binarize_mask(np.array(Image.open(path).convert('L'))).astype(np.uint8)


def _error_map(gt: np.ndarray, pred: np.ndarray) -> np.ndarray:
    """TP=green, FP=red, FN=blue (consistent across all models)."""
    rgb = np.zeros((*pred.shape, 3), dtype=np.uint8)
    tp = (pred == 1) & (gt == 1); fp = (pred == 1) & (gt == 0); fn = (pred == 0) & (gt == 1)
    rgb[..., 1] = np.where(tp, 255, 0)   # green
    rgb[..., 0] = np.where(fp, 255, 0)   # red
    rgb[..., 2] = np.where(fn, 255, 0)   # blue
    return rgb


def predict_subset(sample_ids: List[str], frame: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """Return {sample_id: {'gt':..., 'preds': {model: prob}, 'meta': row}} for a subset."""
    sub = frame[frame['sample_id'].isin(sample_ids)].reset_index(drop=True)
    out = {sid: {'preds': {}} for sid in sample_ids}
    models = {}
    for key in MODELS:
        models[key], dev = load_model(key)
    for _, r in sub.iterrows():
        gt_full = _load_gt(Path(r['mask_path']))
        with Image.open(r['image_path']) as im:
            src = np.array(im.convert('L'))
        rec = out.setdefault(r['sample_id'], {'preds': {}})
        rec['gt'] = gt_full; rec['src'] = src
        rec['meta'] = {'patient_id': r['patient_id'], 'category': r['category'],
                       'acquisition': r['acquisition_type'],
                       'native': src.shape,
                       'mask_path': r['mask_path'], 'image_path': r['image_path']}
        for key in MODELS:
            model = models[key]
            im = Image.open(r['image_path']).convert('L')
            w, h = im.size
            scale = min(TARGET / w, TARGET / h)
            nw, nh = max(1, round(w * scale)), max(1, round(h * scale))
            im = im.resize((nw, nh), Image.BILINEAR)
            pl, pt = (TARGET - nw) // 2, (TARGET - nh) // 2
            pr, pb = TARGET - nw - pl, TARGET - nh - pt
            arr = np.array(im, dtype=np.float32) / 255.0
            arr = np.pad(arr, ((pt, pb), (pl, pr)), mode='constant', constant_values=0)
            t = torch.from_numpy(arr).unsqueeze(0).unsqueeze(0).to(dev)
            with torch.no_grad():
                with torch.amp.autocast('cuda', enabled=(dev.type == 'cuda')):
                    o = model(t)
            prob = torch.sigmoid(o).float().squeeze().cpu().numpy()
            prob = prob[pt:pt + nh, pl:pl + nw]
            rec['preds'][key] = prob
    for key in MODELS:
        del models[key]
    torch.cuda.empty_cache()
    return out


def size_stratum_of_case(gt_full: np.ndarray, acquisition: str) -> str:
    """FULL_FIELD only; otherwise ROI_NOT_PRIMARY_BINNED."""
    if acquisition != 'FULL_FIELD':
        return 'ROI_NOT_PRIMARY_BINNED'
    lab, n = _label(gt_full)
    if n == 0:
        return 'NO_COMPONENT'
    H, W = gt_full.shape
    ratios = [int(np.sum(lab == gid)) / (H * W) for gid in range(1, n + 1)]
    r = min(ratios)
    return 'TINY' if r <= Q25 else 'SMALL' if r <= Q50 else 'MEDIUM' if r <= Q75 else 'LARGE'


def _label(mask: np.ndarray):
    from scipy.ndimage import label
    return label(mask > 0, structure=STRUCT8)


# ---------------------------------------------------------------------------
# Upstream frozen epoch tables (read-only appendix)
# ---------------------------------------------------------------------------
PHASE10_EPOCH_TABLES = {
    'unet': TABLES / 'phase10_final_epoch_results_unet.csv',
    'attention_unet': TABLES / 'phase10_final_epoch_results_attention_unet.csv',
    'unetpp': TABLES / 'phase10_final_epoch_results_unetpp.csv',
    'deeplabv3plus': TABLES / 'phase10_final_epoch_results_deeplabv3plus.csv',
}
EXPECTED_EPOCH_ROWS = {'unet': 59, 'attention_unet': 69, 'unetpp': 85, 'deeplabv3plus': 67}
