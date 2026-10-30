"""
Phase 10 FINAL PART — Four-model CLEAN-v3 baseline comparison support (READ-ONLY).

Compares four already-frozen clean-v3 KUB baseline runs:
    UNet, Attention U-Net, UNet++, DeepLabV3+

READ-ONLY. Forbidden: optimizer.step, trainer.fit, checkpoint writes, config changes,
threshold tuning, TEST reads.

All inference uses each model's frozen best.pt at threshold 0.5 on the SAME
phase4_v3 KUB VAL (280 cases). No winner is declared; no significance testing.

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
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(r'D:\Softfors\jup')
REPORTS = PROJECT_ROOT / 'reports'
TABLES = REPORTS / 'tables'
FIGURES = REPORTS / 'figures'

TAXONOMY_ARTIFACT = REPORTS / 'audits' / 'kub_size_clean_v3_v1_thresholds.json'
TAXONOMY_SHA = '89031c51a35c24f6f939fd6206fde6002a019d4bda24ce8cb21988f04db0f0d6'
CANONICAL_GALLERY = TABLES / 'phase09_clean_v3_val_gallery_selection.csv'
CANONICAL_GALLERY_SHA = '10ad09cbcaabb56bc6bc6aefe016c83b2173933bf6d1f16e4baaf3f0845613db'

THRESHOLD = 0.5
TARGET_SIZE = 512

# ---------------------------------------------------------------------------
# Frozen experiment registry (verified by SHA at runtime)
# ---------------------------------------------------------------------------

MODELS: Dict[str, Dict[str, Any]] = {
    'unet': {
        'display': 'UNet',
        'experiment_id': 'phase9_kub_unet_baseline_seed42_512_clean_v3',
        'config': PROJECT_ROOT / 'configs/phase09_clean_v3/phase09_unet_baseline_clean_v3.yaml',
        'history': PROJECT_ROOT / 'experiments/phase9_kub_unet_baseline_seed42_512_clean_v3/history.csv',
        'best': PROJECT_ROOT / 'checkpoints/phase9_kub_unet_baseline_seed42_512_clean_v3/best.pt',
        'latest': PROJECT_ROOT / 'checkpoints/phase9_kub_unet_baseline_seed42_512_clean_v3/latest.pt',
        'reviewer_notebook': PROJECT_ROOT / 'notebooks/phasewise/phase_09_baseline_training/phase09_clean_v3_unet_training_review.ipynb',
        'expected_history_sha': '7678a5822542cd356f85e9c153da460a87e58d85e7cd1221d8fb66e323f60217',
        'expected_best_sha': '7b955ba86464a2fec2d569ecb6124de1fa9a4e66d0b5d58b267be9a280b4c2c0',
        'expected_epochs': 59, 'expected_best_epoch': 44,
        'authoritative': {'dice': 0.7406133413314819, 'iou': 0.6253822445869446,
                          'precision': 0.7707186937332153, 'recall': 0.7839437127113342},
        'param_count': None,  # filled from physical model if instantiated
    },
    'attention_unet': {
        'display': 'Attention U-Net',
        'experiment_id': 'phase10_kub_attention_unet_seed42_512_clean_v3',
        'config': PROJECT_ROOT / 'configs/phase10_clean_v3/phase10_attention_unet_clean_v3.yaml',
        'history': PROJECT_ROOT / 'experiments/phase10_kub_attention_unet_seed42_512_clean_v3/history.csv',
        'best': PROJECT_ROOT / 'checkpoints/phase10_kub_attention_unet_seed42_512_clean_v3/best.pt',
        'latest': PROJECT_ROOT / 'checkpoints/phase10_kub_attention_unet_seed42_512_clean_v3/latest.pt',
        'reviewer_notebook': PROJECT_ROOT / 'notebooks/phasewise/phase_10_baseline_comparison/phase10_attention_unet_clean_v3_training_review.ipynb',
        'expected_history_sha': 'ee5073f0bea745280ae7d9a8f651cc4cae72a18d408750623d838f7cd8d24e58',
        'expected_best_sha': 'a49b19d66e43b57ed082ea6efc0ac10bccf444277abd3540dc68612bf30b88b3',
        'expected_epochs': 69, 'expected_best_epoch': 54,
        'authoritative': {'dice': 0.7525129853960107, 'iou': 0.6349387691368995,
                          'precision': 0.7729140812402236, 'recall': 0.7922248481868364},
        'param_count': None,
    },
    'unetpp': {
        'display': 'UNet++',
        'experiment_id': 'phase10_kub_unetpp_seed42_512_clean_v3',
        'config': PROJECT_ROOT / 'configs/phase10_clean_v3/phase10_unetpp_clean_v3.yaml',
        'history': PROJECT_ROOT / 'experiments/phase10_kub_unetpp_seed42_512_clean_v3/history.csv',
        'best': PROJECT_ROOT / 'checkpoints/phase10_kub_unetpp_seed42_512_clean_v3/best.pt',
        'latest': PROJECT_ROOT / 'checkpoints/phase10_kub_unetpp_seed42_512_clean_v3/latest.pt',
        'reviewer_notebook': PROJECT_ROOT / 'notebooks/phasewise/phase_10_baseline_comparison/phase10_unetpp_clean_v3_training_review.ipynb',
        'expected_history_sha': 'a733d8366278d2ddb1a44db0d94ff7525fb9b10afefba787abfd036c1fb1de5a',
        'expected_best_sha': 'ec7eb13f32e43af27eab7fc617bd1a2a8fcce1d6651a1b4a3653f3e4d1283269',
        'expected_epochs': 85, 'expected_best_epoch': 70,
        'authoritative': {'dice': 0.7641595156062713, 'iou': 0.6525442690586191,
                          'precision': 0.7996825971468945, 'recall': 0.7912384169561990},
        'param_count': None,
    },
    'deeplabv3plus': {
        'display': 'DeepLabV3+',
        'experiment_id': 'phase10_kub_deeplabv3plus_seed42_512_clean_v3',
        'config': PROJECT_ROOT / 'configs/phase10_clean_v3/phase10_deeplabv3plus_clean_v3.yaml',
        'history': PROJECT_ROOT / 'experiments/phase10_kub_deeplabv3plus_seed42_512_clean_v3/history.csv',
        'best': PROJECT_ROOT / 'checkpoints/phase10_kub_deeplabv3plus_seed42_512_clean_v3/best.pt',
        'latest': PROJECT_ROOT / 'checkpoints/phase10_kub_deeplabv3plus_seed42_512_clean_v3/latest.pt',
        'reviewer_notebook': PROJECT_ROOT / 'notebooks/phasewise/phase_10_baseline_comparison/phase10_deeplabv3plus_clean_v3_training_review.ipynb',
        'expected_history_sha': '9c3a4611f0f38b474aa18537b0509bf9a4cb539baf077e6ba12c7880a73cd01f',
        'expected_best_sha': 'f519027ba1a3a4d6212d83fecd4379f61f71bc05b0751924b9660da08d597dad',
        'expected_epochs': 67, 'expected_best_epoch': 52,
        'authoritative': {'dice': 0.7509140344161673, 'iou': 0.6460492792430865,
                          'precision': 0.7943328495850855, 'recall': 0.7822983241135557},
        'param_count': 40340769,
    },
}

MODEL_ORDER = ['unet', 'attention_unet', 'unetpp', 'deeplabv3plus']


# ---------------------------------------------------------------------------
# Hashing
# ---------------------------------------------------------------------------

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def verify_immutability() -> Dict[str, Dict[str, Any]]:
    """Verify config/history/best/latest/reviewer-notebook SHAs for all four models."""
    out = {}
    for key in MODEL_ORDER:
        m = MODELS[key]
        rec = {
            'experiment_id': m['experiment_id'],
            'config_sha': sha256_file(m['config']),
            'history_sha': sha256_file(m['history']),
            'best_sha': sha256_file(m['best']),
            'latest_sha': sha256_file(m['latest']),
            'reviewer_notebook_sha': sha256_file(m['reviewer_notebook']),
        }
        rec['history_sha_match'] = rec['history_sha'] == m['expected_history_sha']
        rec['best_sha_match'] = rec['best_sha'] == m['expected_best_sha']
        rec['all_match'] = rec['history_sha_match'] and rec['best_sha_match']
        out[key] = rec
    return out


# ---------------------------------------------------------------------------
# History normalization + epoch tables
# ---------------------------------------------------------------------------

def _dice_col(df: pd.DataFrame) -> str:
    return 'val_dice' if 'val_dice' in df.columns else 'val_macro_dice'


def _iou_col(df: pd.DataFrame) -> str:
    return 'val_iou' if 'val_iou' in df.columns else 'val_macro_iou'


def load_history(key: str) -> pd.DataFrame:
    return pd.read_csv(MODELS[key]['history'])


def build_epoch_table(key: str) -> pd.DataFrame:
    """One row per completed epoch with canonical + derived reviewer-only columns."""
    m = MODELS[key]
    h = load_history(key)
    d = h.copy().sort_values('epoch').reset_index(drop=True)
    dc, ic = _dice_col(d), _iou_col(d)
    out = pd.DataFrame({'model': m['display'], 'experiment_id': m['experiment_id'],
                        'epoch': d['epoch'].astype(int)})
    out['train_loss'] = d['train_loss']
    out['val_loss'] = d['val_loss']
    out['val_macro_dice'] = d[dc]
    out['val_macro_iou'] = d[ic]
    out['val_precision'] = d['val_precision'] if 'val_precision' in d.columns else 'N/A'
    out['val_recall'] = d['val_recall'] if 'val_recall' in d.columns else 'N/A'
    out['learning_rate'] = d['learning_rate']
    out['best_metric_so_far'] = d.get('best_so_far', pd.Series([np.nan] * len(d)))
    out['improved'] = d['improved'].astype(int)
    out['bad_epochs'] = d['bad_epochs'].astype(int)
    out['elapsed_seconds'] = d.get('epoch_seconds', pd.Series([np.nan] * len(d)))
    out['checkpoint_event'] = np.where(out['improved'] == 1, 'BEST_SAVED', 'LATEST_ONLY')

    dice = pd.to_numeric(out['val_macro_dice'], errors='coerce')
    best_so_far = pd.to_numeric(out['best_metric_so_far'], errors='coerce')
    out['delta_val_dice_vs_previous_epoch'] = dice.diff().round(10)
    out['delta_best_metric'] = best_so_far.diff().round(10)
    out['is_new_best'] = out['improved'] == 1
    best_ep = int(out.loc[dice.idxmax(), 'epoch']) if dice.notna().any() else None
    out['is_best_epoch'] = out['epoch'] == best_ep
    since, last = [], None
    for _, r in out.iterrows():
        if r['is_new_best']:
            last = int(r['epoch'])
        since.append(0 if last is None else int(r['epoch']) - last)
    out['epochs_since_best'] = since
    return out


def verify_epoch_table(key: str, tbl: pd.DataFrame) -> Dict[str, Any]:
    h = load_history(key)
    dc = _dice_col(h)
    eps = tbl['epoch'].astype(int).tolist()
    expected = list(range(1, len(h) + 1))
    missing = sorted(set(expected) - set(eps))
    dupes = sorted({e for e in eps if eps.count(e) > 1})
    streak = longest = 0
    for imp in tbl['improved']:
        streak = 0 if imp == 1 else streak + 1
        longest = max(longest, streak)
    best = h.loc[h[dc].idxmax()]
    return {
        'model': MODELS[key]['display'],
        'rows': len(tbl), 'history_rows': len(h),
        'row_count_matches_history': len(tbl) == len(h),
        'unique_epochs': len(set(eps)), 'first_epoch': min(eps), 'last_epoch': max(eps),
        'missing_epochs': missing, 'duplicate_epochs': dupes,
        'contiguous_1_to_N': eps == expected,
        'best_epoch': int(best['epoch']),
        'strict_unique_max': int((h[dc] == h[dc].max()).sum()) == 1,
        'final_bad_epochs': int(h['bad_epochs'].iloc[-1]),
        'early_stop_arithmetic_ok': int(h['epoch'].iloc[-1]) == int(best['epoch']) + int(h['bad_epochs'].iloc[-1]),
        'improvement_events': int(h['improved'].sum()),
        'longest_no_improvement_streak': longest,
        'final_lr': float(h['learning_rate'].iloc[-1]),
        'best_lr': float(best['learning_rate']),
        'finite_losses': bool(h['train_loss'].notna().all() and h['val_loss'].notna().all()),
        'integrity_pass': (len(tbl) == len(h)) and not missing and not dupes and eps == expected,
    }


def save_epoch_table(key: str, tbl: pd.DataFrame) -> Path:
    name = {'unet': 'unet', 'attention_unet': 'attention_unet', 'unetpp': 'unetpp',
            'deeplabv3plus': 'deeplabv3plus'}[key]
    p = TABLES / f'phase10_final_epoch_results_{name}.csv'
    p.parent.mkdir(parents=True, exist_ok=True)
    tbl.to_csv(p, index=False)
    return p


def build_long_table(tables: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """MODEL_EPOCH_LONG_TABLE — one row per model-epoch (280 expected)."""
    cols = ['model', 'experiment_id', 'epoch', 'train_loss', 'val_loss', 'val_macro_dice',
            'val_macro_iou', 'val_precision', 'val_recall', 'learning_rate',
            'best_metric_so_far', 'improved', 'bad_epochs', 'elapsed_seconds',
            'checkpoint_event', 'delta_val_dice_vs_previous_epoch', 'delta_best_metric',
            'is_new_best', 'is_best_epoch', 'epochs_since_best']
    return pd.concat([tables[k][cols] for k in MODEL_ORDER], ignore_index=True)


# ---------------------------------------------------------------------------
# KUB VAL
# ---------------------------------------------------------------------------

def derive_acquisition_type(p: str) -> str:
    s = str(p).replace('\\', '/')
    if '/ROI/' in s or '/roi/' in s:
        return 'ROI'
    if '/Images/' in s or '/images/' in s:
        return 'FULL_FIELD'
    return 'UNKNOWN'


def get_kub_val() -> pd.DataFrame:
    df = pd.read_csv(PROJECT_ROOT / 'manifests' / 'phase4_v3' / 'val.csv')
    k = df[df['dataset'] == 'KUB'].copy().reset_index(drop=True)
    assert len(k) == 280, f'expected 280 KUB VAL rows, got {len(k)}'
    assert set(k['category']) <= {'Kidney_Stone', 'Bladder_Stone', 'Ureteric_Stone'}
    k['acquisition_type'] = k['image_path'].apply(derive_acquisition_type)
    assert (k['acquisition_type'] != 'UNKNOWN').all()
    return k


def load_canonical_gallery() -> pd.DataFrame:
    actual = sha256_file(CANONICAL_GALLERY)
    assert actual == CANONICAL_GALLERY_SHA, f'gallery SHA mismatch {actual}'
    return pd.read_csv(CANONICAL_GALLERY)


# ---------------------------------------------------------------------------
# Inference
# ---------------------------------------------------------------------------

def _make_model(key: str, cfg_model: dict):
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    if key == 'unet':
        from src.models.unet import UNet
        return UNet(in_channels=cfg_model['input_channels'], out_channels=cfg_model['output_channels'],
                    base_channels=cfg_model['base_channels'])
    if key == 'attention_unet':
        from src.models.attention_unet import AttentionUNet
        return AttentionUNet(in_channels=cfg_model['input_channels'], out_channels=cfg_model['output_channels'],
                             base_channels=cfg_model['base_channels'])
    if key == 'unetpp':
        from src.models.unetpp import UNetPlusPlus
        return UNetPlusPlus(in_channels=cfg_model['input_channels'], out_channels=cfg_model['output_channels'],
                            base_channels=cfg_model['base_channels'])
    if key == 'deeplabv3plus':
        from src.models.deeplabv3plus import DeepLabV3Plus
        return DeepLabV3Plus(in_channels=cfg_model['input_channels'], out_channels=cfg_model['output_channels'],
                             base_channels=cfg_model['base_channels'])
    raise ValueError(key)


def load_model_for_inference(key: str, device: str = 'cuda'):
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    from src.utils.device import get_device
    m = MODELS[key]
    ck = torch.load(m['best'], map_location='cpu', weights_only=False)
    model = _make_model(key, ck['configuration']['model'])
    model.load_state_dict(ck['model_state'])
    dev = get_device(require_cuda=(device != 'cpu'))
    model = model.to(dev).eval()
    return model, dev


def preprocess(image_path: Path, target: int = TARGET_SIZE):
    """Match KUBDataset._load_and_resize EXACTLY (round, not int)."""
    img = Image.open(image_path).convert('L')
    w, h = img.size
    scale = min(target / w, target / h)
    nw, nh = max(1, round(w * scale)), max(1, round(h * scale))
    img = img.resize((nw, nh), Image.BILINEAR)
    pl, pt = (target - nw) // 2, (target - nh) // 2
    pr, pb = target - nw - pl, target - nh - pt
    arr = np.array(img, dtype=np.float32) / 255.0
    arr = np.pad(arr, ((pt, pb), (pl, pr)), mode='constant', constant_values=0)
    ten = torch.from_numpy(arr).unsqueeze(0).unsqueeze(0)
    return ten, (nw, nh), (pl, pt), (w, h)


def predict_case(model, device, image_path: Path):
    """Deterministic single-case inference. Returns prob map cropped to resized extent."""
    ten, (nw, nh), (pl, pt), native = preprocess(image_path)
    ten = ten.to(device)
    with torch.no_grad():
        with torch.amp.autocast('cuda', enabled=(device.type == 'cuda')):
            out = model(ten)
        prob = torch.sigmoid(out).squeeze().cpu().numpy()
    prob = prob[pt:pt + nh, pl:pl + nw]
    return prob, (nw, nh), native


def predict_case_padded(model, device, image_path: Path):
    """Deterministic inference returning the FULL padded 512x512 probability map.

    Training-time validation computed metrics on the padded 512x512 geometry, so the
    aggregate-metric reproduction gate must also use the padded geometry. Cropping to the
    resized extent changes the result (the padded border can contain predictions), which is
    why a cropped variant does NOT reproduce the authoritative values.
    """
    ten, (nw, nh), (pl, pt), native = preprocess(image_path)
    ten = ten.to(device)
    with torch.no_grad():
        with torch.amp.autocast('cuda', enabled=(device.type == 'cuda')):
            out = model(ten)
        prob = torch.sigmoid(out).squeeze().cpu().numpy().astype(np.float64)
    return prob, (nw, nh), (pl, pt), native


def padded_gt(mask_path: Path, target: int = TARGET_SIZE) -> np.ndarray:
    """Build the padded 512x512 binary GT exactly as the training pipeline does.

    Raw mask -> binarize (mask > 0) -> NEAREST resize to (nw, nh) -> zero-pad to target.
    """
    from src.utils.targets import binarize_mask
    gt_full = binarize_mask(np.array(Image.open(mask_path).convert('L'))).astype(np.uint8)
    m = Image.fromarray(gt_full)
    w, h = m.size
    scale = min(target / w, target / h)
    nw, nh = max(1, round(w * scale)), max(1, round(h * scale))
    m = m.resize((nw, nh), Image.NEAREST)
    pl, pt = (target - nw) // 2, (target - nh) // 2
    pr, pb = target - nw - pl, target - nh - pt
    arr = np.array(m, dtype=np.uint8)
    return np.pad(arr, ((pt, pb), (pl, pr)), mode='constant', constant_values=0)


def _case_metrics(gt: np.ndarray, prob: np.ndarray) -> Dict[str, float]:
    pred = (prob >= THRESHOLD).astype(np.uint8)
    g = gt.astype(bool)
    p = pred.astype(bool)
    tp = float((p & g).sum()); fp = float((p & ~g).sum()); fn = float((~p & g).sum())
    eps = 1e-7
    return {'dice': (2 * tp + eps) / (2 * tp + fp + fn + eps),
            'iou': (tp + eps) / (tp + fp + fn + eps),
            'precision': (tp + eps) / (tp + fp + eps),
            'recall': (tp + eps) / (tp + fn + eps)}


def build_paired_table(verbose: bool = True) -> pd.DataFrame:
    """Run all four models on the same 280 KUB VAL cases; one row per case."""
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    from src.utils.targets import binarize_mask

    val = get_kub_val()
    rows = []
    for key in MODEL_ORDER:
        model, device = load_model_for_inference(key)
        if verbose:
            print(f'  inference {MODELS[key]["display"]} ...')
        per = {}
        for _, r in val.iterrows():
            # Padded 512x512 geometry - matches training-time validation space
            prob, (nw, nh), (pl, pt), native = predict_case_padded(model, device, Path(r['image_path']))
            gt = padded_gt(Path(r['mask_path']))
            per[r['sample_id']] = _case_metrics(gt, prob)
        rows.append((key, per))
        del model
        torch.cuda.empty_cache()

    out = val[['sample_id', 'patient_id', 'category']].copy()
    out['acquisition_type'] = val['acquisition_type'].values
    # native resolution
    native = []
    for _, r in val.iterrows():
        with Image.open(r['image_path']) as im:
            native.append(im.size)
    out['native_width'] = [n[0] for n in native]
    out['native_height'] = [n[1] for n in native]
    for key, per in rows:
        out[f'{key}_dice'] = out['sample_id'].map(lambda s: per[s]['dice'])
        out[f'{key}_iou'] = out['sample_id'].map(lambda s: per[s]['iou'])
        out[f'{key}_precision'] = out['sample_id'].map(lambda s: per[s]['precision'])
        out[f'{key}_recall'] = out['sample_id'].map(lambda s: per[s]['recall'])
    return out


# ---------------------------------------------------------------------------
# Summaries (descriptive only — no rank/winner columns)
# ---------------------------------------------------------------------------

def overall_comparison(paired: pd.DataFrame, epochs: Dict[str, int]) -> pd.DataFrame:
    rows = []
    for key in MODEL_ORDER:
        m = MODELS[key]
        d = float(paired[f'{key}_dice'].mean())
        a = m['authoritative']
        rows.append({
            'model': m['display'], 'experiment_id': m['experiment_id'],
            'parameter_count': m['param_count'] if m['param_count'] else 'N/A',
            'epochs_completed': epochs.get(key, len(load_history(key))),
            'best_epoch': m['expected_best_epoch'],
            'stop_epoch': int(load_history(key)['epoch'].iloc[-1]),
            'val_macro_dice': d, 'val_macro_iou': float(paired[f'{key}_iou'].mean()),
            'val_precision': float(paired[f'{key}_precision'].mean()),
            'val_recall': float(paired[f'{key}_recall'].mean()),
            'authoritative_dice': a['dice'],
            'reproduction_abs_diff': abs(d - a['dice']),
        })
    return pd.DataFrame(rows)


def stratified(paired: pd.DataFrame, by: str) -> pd.DataFrame:
    rows = []
    for grp, sub in paired.groupby(by):
        row = {by: grp, 'n': len(sub)}
        for key in MODEL_ORDER:
            row[f'{key}_dice'] = float(sub[f'{key}_dice'].mean())
            row[f'{key}_iou'] = float(sub[f'{key}_iou'].mean())
            row[f'{key}_precision'] = float(sub[f'{key}_precision'].mean())
            row[f'{key}_recall'] = float(sub[f'{key}_recall'].mean())
        rows.append(row)
    return pd.DataFrame(rows)


def pairwise_deltas(paired: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for i in range(len(MODEL_ORDER)):
        for j in range(i + 1, len(MODEL_ORDER)):
            a, b = MODEL_ORDER[i], MODEL_ORDER[j]
            dd = paired[f'{a}_dice'] - paired[f'{b}_dice']
            di = paired[f'{a}_iou'] - paired[f'{b}_iou']
            rows.append({
                'model_a': MODELS[a]['display'], 'model_b': MODELS[b]['display'],
                'mean_paired_dice_diff': float(dd.mean()),
                'median_paired_dice_diff': float(dd.median()),
                'mean_paired_iou_diff': float(di.mean()),
                'median_paired_iou_diff': float(di.median()),
                'status': 'DESCRIPTIVE_SINGLE_SEED_ONLY',
            })
    return pd.DataFrame(rows)


def disagreement_summary(paired: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for i in range(len(MODEL_ORDER)):
        for j in range(i + 1, len(MODEL_ORDER)):
            a, b = MODEL_ORDER[i], MODEL_ORDER[j]
            da, db = paired[f'{a}_dice'], paired[f'{b}_dice']
            rows.append({
                'model_a': MODELS[a]['display'], 'model_b': MODELS[b]['display'],
                'both_dice_ge_0.5': int(((da >= 0.5) & (db >= 0.5)).sum()),
                'both_dice_lt_0.5': int(((da < 0.5) & (db < 0.5)).sum()),
                'abs_dice_diff_gt_0.10': int((abs(da - db) > 0.10).sum()),
                'a_better_by_gt_0.10': int(((da - db) > 0.10).sum()),
                'b_better_by_gt_0.10': int(((db - da) > 0.10).sum()),
                'status': 'DESCRIPTIVE_SINGLE_SEED_ONLY',
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Figures (descriptive only - no "winner" annotation)
# ---------------------------------------------------------------------------

COLORS = {'unet': 'C0', 'attention_unet': 'C1', 'unetpp': 'C2', 'deeplabv3plus': 'C3'}


def _short(k):
    return MODELS[k]['display']


def plot_training_dynamics(tables: Dict[str, pd.DataFrame], outdir: Path = FIGURES):
    """Six descriptive training-dynamics panels across all four models."""
    outdir.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    fig.suptitle('Phase 10 CLEAN-v3 — Four-Model Training Dynamics (descriptive, single seed)',
                 fontsize=12)

    def mark(ax, k, t):
        be = int(t.loc[t['is_best_epoch'], 'epoch'].iloc[0])
        se = int(t['epoch'].iloc[-1])
        ax.axvline(be, color=COLORS[k], linestyle=':', alpha=.5)
        ax.axvline(se, color=COLORS[k], linestyle='--', alpha=.35)

    # A VAL Dice vs epoch
    ax = axes[0, 0]
    for k in MODEL_ORDER:
        t = tables[k]
        ax.plot(t['epoch'], t['val_macro_dice'], color=COLORS[k], label=_short(k), linewidth=1.2)
        mark(ax, k, t)
    ax.set_xlabel('Epoch'); ax.set_ylabel('VAL macro Dice'); ax.set_title('A. VAL Dice vs epoch')
    ax.legend(fontsize=8); ax.grid(True, alpha=.3)

    # B best-so-far
    ax = axes[0, 1]
    for k in MODEL_ORDER:
        t = tables[k]
        ax.plot(t['epoch'], pd.to_numeric(t['best_metric_so_far']), color=COLORS[k],
                label=_short(k), linewidth=1.2)
    ax.set_xlabel('Epoch'); ax.set_ylabel('Best-so-far Dice'); ax.set_title('B. Best-so-far')
    ax.legend(fontsize=8); ax.grid(True, alpha=.3)

    # C train loss
    ax = axes[0, 2]
    for k in MODEL_ORDER:
        t = tables[k]
        ax.plot(t['epoch'], t['train_loss'], color=COLORS[k], label=_short(k), linewidth=1.2)
    ax.set_xlabel('Epoch'); ax.set_ylabel('Train loss'); ax.set_title('C. Train loss')
    ax.legend(fontsize=8); ax.grid(True, alpha=.3)

    # D val loss
    ax = axes[1, 0]
    for k in MODEL_ORDER:
        t = tables[k]
        ax.plot(t['epoch'], t['val_loss'], color=COLORS[k], label=_short(k), linewidth=1.2)
    ax.set_xlabel('Epoch'); ax.set_ylabel('VAL loss'); ax.set_title('D. VAL loss')
    ax.legend(fontsize=8); ax.grid(True, alpha=.3)

    # E LR
    ax = axes[1, 1]
    for k in MODEL_ORDER:
        t = tables[k]
        ax.plot(t['epoch'], t['learning_rate'], color=COLORS[k], label=_short(k), linewidth=1.2)
    ax.set_xlabel('Epoch'); ax.set_ylabel('LR'); ax.set_title('E. Learning rate')
    ax.set_yscale('log'); ax.legend(fontsize=8); ax.grid(True, alpha=.3)

    # F bad epochs / improvements
    ax = axes[1, 2]
    for k in MODEL_ORDER:
        t = tables[k]
        ax.plot(t['epoch'], t['bad_epochs'], color=COLORS[k], label=_short(k), linewidth=1.2)
        imp = t[t['is_new_best']]
        ax.scatter(imp['epoch'], [0] * len(imp), color=COLORS[k], s=12, marker='|')
    ax.axhline(15, color='red', linestyle=':', alpha=.5, label='patience 15')
    ax.set_xlabel('Epoch'); ax.set_ylabel('bad_epochs')
    ax.set_title('F. Early-stop counter (+ ticks = improvements)')
    ax.legend(fontsize=7); ax.grid(True, alpha=.3)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    p = outdir / 'phase10_clean_v3_training_dynamics.png'
    fig.savefig(p, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return p


def plot_stratified(cat: pd.DataFrame, acq: pd.DataFrame, outdir: Path = FIGURES):
    outdir.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle('Phase 10 CLEAN-v3 — Stratified descriptive VAL metrics (single seed)', fontsize=11)

    ks = MODEL_ORDER
    labels = [_short(k) for k in ks]
    x = np.arange(len(ks)); w = 0.26

    ax = axes[0]
    for i, (_, r) in enumerate(cat.iterrows()):
        vals = [r[f'{k}_dice'] for k in ks]
        ax.bar(x + (i - 1) * w, vals, w, label=f"{r['category']} (n={r['n']})")
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel('Macro Dice'); ax.set_title('Category-stratified Dice')
    ax.legend(fontsize=7); ax.grid(True, alpha=.3, axis='y')

    ax = axes[1]
    for i, (_, r) in enumerate(acq.iterrows()):
        vals = [r[f'{k}_dice'] for k in ks]
        ax.bar(x + (i - 0.5) * w, vals, w, label=f"{r['acquisition_type']} (n={r['n']})")
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel('Macro Dice')
    ax.set_title('Acquisition-stratified Dice (distinct regimes)')
    ax.legend(fontsize=7); ax.grid(True, alpha=.3, axis='y')

    plt.tight_layout(rect=[0, 0.03, 1, 0.93])
    p = outdir / 'phase10_clean_v3_stratified_metrics.png'
    fig.savefig(p, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return p


def plot_paired_distributions(paired: pd.DataFrame, outdir: Path = FIGURES):
    outdir.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle('Phase 10 CLEAN-v3 — Paired per-case Dice distributions (descriptive)', fontsize=11)

    ax = axes[0]
    data = [paired[f'{k}_dice'].values for k in MODEL_ORDER]
    names = [_short(k) for k in MODEL_ORDER]
    try:
        ax.boxplot(data, tick_labels=names, showmeans=True)
    except TypeError:
        ax.boxplot(data, labels=names, showmeans=True)
    ax.set_ylabel('Per-case Dice'); ax.set_title('Per-case Dice by model')
    ax.tick_params(axis='x', labelsize=8); ax.grid(True, alpha=.3, axis='y')

    ax = axes[1]
    base = 'unetpp'
    for k in MODEL_ORDER:
        if k == base:
            continue
        diff = paired[f'{k}_dice'] - paired[f'{base}_dice']
        ax.hist(diff, bins=40, alpha=.5, label=f'{_short(k)} − {_short(base)}')
    ax.axvline(0, color='black', linewidth=1)
    ax.set_xlabel('Paired per-case Dice difference')
    ax.set_ylabel('Cases')
    ax.set_title(f'Paired Dice differences vs {_short(base)} (descriptive only)')
    ax.legend(fontsize=7); ax.grid(True, alpha=.3)

    plt.tight_layout(rect=[0, 0.03, 1, 0.93])
    p = outdir / 'phase10_clean_v3_paired_dice_distributions.png'
    fig.savefig(p, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return p


# ---------------------------------------------------------------------------
# Frozen 16-case paired qualitative gallery
# ---------------------------------------------------------------------------

def build_paired_gallery(paired: pd.DataFrame, outdir: Path = FIGURES,
                         gallery_prefix: str = 'phase10_clean_v3_paired_gallery') -> List[Path]:
    """One readable page per frozen case: source + GT, then per-model prob/pred/overlay.

    Identical probability scaling (0-1) and identical overlay semantics across models.
    Labelled DETERMINISTIC_GALLERY_SUBSET_ONLY.
    """
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    from src.utils.targets import binarize_mask

    outdir.mkdir(parents=True, exist_ok=True)
    gal = load_canonical_gallery()
    val = get_kub_val()
    gal = gal.merge(val[['sample_id', 'image_path', 'mask_path', 'category', 'acquisition_type']],
                    on='sample_id', how='left', suffixes=('', '_v'))
    # deterministic order
    gal = gal.sort_values('gallery_index').reset_index(drop=True)

    models = {k: load_model_for_inference(k) for k in MODEL_ORDER}
    paths = []

    for _, row in gal.iterrows():
        sid = row['sample_id']
        ip, mp = Path(row['image_path']), Path(row['mask_path'])
        if not ip.exists() or not mp.exists():
            continue
        gt_full = binarize_mask(np.array(Image.open(mp).convert('L'))).astype(np.uint8)
        with Image.open(ip) as im:
            native = im.size
        src = np.array(Image.open(ip).convert('L'))

        ncol = 2 + 3 * len(MODEL_ORDER)   # src, GT, then 3 per model
        fig, axes = plt.subplots(1, ncol, figsize=(3 * ncol, 3.6))
        fig.suptitle(
            f"Case {int(row['gallery_index'])} · {sid[:12]} · {row['category']} · "
            f"{row['acquisition_type']} · native {native[0]}x{native[1]}\n"
            f"DETERMINISTIC_GALLERY_SUBSET_ONLY — not an overall model score",
            fontsize=11)

        axes[0].imshow(src, cmap='gray', vmin=0, vmax=255)
        axes[0].set_title('Source', fontsize=9); axes[0].axis('off')
        axes[1].imshow(gt_full, cmap='gray', vmin=0, vmax=1)
        axes[1].set_title('Binary GT', fontsize=9); axes[1].axis('off')

        for i, k in enumerate(MODEL_ORDER):
            model, dev = models[k]
            prob, (nw, nh), native_sz = predict_case(model, dev, ip)
            gt = np.array(Image.fromarray(gt_full).resize((nw, nh), Image.NEAREST))
            pred = (prob >= THRESHOLD).astype(np.uint8)
            m = _case_metrics(gt, prob)
            ov = np.zeros((*pred.shape, 3), dtype=np.uint8)
            ov[..., 0] = gt * 255; ov[..., 1] = pred * 255
            both = gt & pred
            ov[..., 0] = np.where(both, 0, ov[..., 0]); ov[..., 1] = np.where(both, 255, ov[..., 1])
            ov[..., 2] = np.where((gt == 0) & (pred == 1), 255, 0)
            base = 2 + i * 3
            axes[base].imshow(prob, cmap='viridis', vmin=0, vmax=1)
            axes[base].set_title(f"{_short(k)}\nprob", fontsize=9); axes[base].axis('off')
            axes[base + 1].imshow(pred, cmap='gray', vmin=0, vmax=1)
            axes[base + 1].set_title('pred t=0.5', fontsize=9); axes[base + 1].axis('off')
            axes[base + 2].imshow(ov)
            axes[base + 2].set_title(f"overlay\nDice={m['dice']:.3f} IoU={m['iou']:.3f}", fontsize=9)
            axes[base + 2].axis('off')

        plt.tight_layout(rect=[0, 0.02, 1, 0.87])
        p = outdir / f"{gallery_prefix}_case{int(row['gallery_index']):02d}.png"
        fig.savefig(p, dpi=110, bbox_inches='tight')
        plt.close(fig)
        paths.append(p)

    for k in MODEL_ORDER:
        del models[k]
    torch.cuda.empty_cache()
    return paths
