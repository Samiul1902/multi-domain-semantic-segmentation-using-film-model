"""
Phase 10 Part 1C — Read-only reviewer / analysis support for the completed
CLEAN-v3 DeepLabV3+ run.

READ-ONLY. This module does NOT train, does NOT call optimizer.step(), does NOT
write checkpoints, and does NOT touch TEST.

Canonical training was executed by:
    notebooks/phasewise/phase_10_clean_v3_comparison/code/train_phase10_deeplabv3plus_clean_v3.py
That runner is frozen execution provenance and must not be altered.

Gallery note: reuses the CANONICAL frozen 16-case KUB VAL selection
(SHA 10ad09cb...) shared with UNet / Attention U-Net / UNet++.

Epoch-table note: builds a REVIEWER epoch table from the immutable physical
history.csv (one row per completed epoch) with derived reviewer-only columns.
history.csv itself is NEVER modified.

Author: Gemini 3.1 Pro High
Date: 2026-09-20
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd
import torch
import yaml
from PIL import Image
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(r'D:\Softfors\jup')
EXPERIMENT_ID = 'phase10_kub_deeplabv3plus_seed42_512_clean_v3'
EXPERIMENT_DIR = PROJECT_ROOT / 'experiments' / EXPERIMENT_ID
CHECKPOINT_DIR = PROJECT_ROOT / 'checkpoints' / EXPERIMENT_ID
CONFIG_PATH = PROJECT_ROOT / 'configs' / 'phase10_clean_v3' / 'phase10_deeplabv3plus_clean_v3.yaml'
HISTORY_PATH = EXPERIMENT_DIR / 'history.csv'
BEST_PT = CHECKPOINT_DIR / 'best.pt'
LATEST_PT = CHECKPOINT_DIR / 'latest.pt'
TAXONOMY_ARTIFACT = PROJECT_ROOT / 'reports' / 'audits' / 'kub_size_clean_v3_v1_thresholds.json'
START_AUDIT = PROJECT_ROOT / 'reports' / 'audits' / 'phase10_deeplabv3plus_clean_v3_training_start_audit.json'
COMPLETION_AUDIT = PROJECT_ROOT / 'reports' / 'audits' / 'phase10_deeplabv3plus_clean_v3_training_completion_audit.json'
PROTOCOL_DIFF = PROJECT_ROOT / 'reports' / 'tables' / 'phase10_deeplabv3plus_v2_to_clean_v3_protocol_diff.csv'
EPOCH_TABLE_CSV = PROJECT_ROOT / 'reports' / 'tables' / 'phase10_deeplabv3plus_clean_v3_epoch_results.csv'

TRAINING_RUNNER = (PROJECT_ROOT / 'notebooks' / 'phasewise' / 'phase_10_clean_v3_comparison'
                   / 'code' / 'train_phase10_deeplabv3plus_clean_v3.py')

EXPECTED_CONFIG_SHA = 'a5220e3135618513a71e0094197b2cffe0aef9334f7d53e39642c7a00ddd5b57'
TAXONOMY_SHA = '89031c51a35c24f6f939fd6206fde6002a019d4bda24ce8cb21988f04db0f0d6'

CANONICAL_GALLERY = PROJECT_ROOT / 'reports' / 'tables' / 'phase09_clean_v3_val_gallery_selection.csv'
CANONICAL_GALLERY_SHA = '10ad09cbcaabb56bc6bc6aefe016c83b2173933bf6d1f16e4baaf3f0845613db'

KUB_VAL_EXPECTED_ROWS = 280
KUB_ALLOWED_CATEGORIES = {'Kidney_Stone', 'Bladder_Stone', 'Ureteric_Stone'}

HISTORICAL_EXPERIMENT_ID = 'phase10_kub_deeplabv3plus_seed42_512'


# ---------------------------------------------------------------------------
# Hashing
# ---------------------------------------------------------------------------

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def verify_artifact_shas() -> Dict[str, Any]:
    """Verify physical artifacts against the completion audit (authoritative record)."""
    ca = load_completion_audit()
    res = {
        'config_match': sha256_file(CONFIG_PATH) == EXPECTED_CONFIG_SHA,
        'config_sha': sha256_file(CONFIG_PATH),
        'best_pt_match': sha256_file(BEST_PT) == ca.get('best_checkpoint_sha'),
        'best_pt_sha': sha256_file(BEST_PT),
        'latest_pt_match': sha256_file(LATEST_PT) == ca.get('latest_checkpoint_sha'),
        'latest_pt_sha': sha256_file(LATEST_PT),
        'history_match': sha256_file(HISTORY_PATH) == ca.get('history_sha'),
        'history_sha': sha256_file(HISTORY_PATH),
        'taxonomy_match': sha256_file(TAXONOMY_ARTIFACT) == TAXONOMY_SHA,
        'taxonomy_sha': sha256_file(TAXONOMY_ARTIFACT),
    }
    res['runner_sha'] = sha256_file(TRAINING_RUNNER)
    res['protocol_diff_sha'] = sha256_file(PROTOCOL_DIFF)
    res['all_pass'] = all([res['config_match'], res['best_pt_match'],
                           res['latest_pt_match'], res['history_match'],
                           res['taxonomy_match']])
    return res


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_config() -> Dict[str, Any]:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding='utf-8'))


def load_history() -> pd.DataFrame:
    return pd.read_csv(HISTORY_PATH)


def load_start_audit() -> Dict[str, Any]:
    return json.loads(START_AUDIT.read_text(encoding='utf-8'))


def load_completion_audit() -> Dict[str, Any]:
    return json.loads(COMPLETION_AUDIT.read_text(encoding='utf-8'))


def load_protocol_diff() -> pd.DataFrame:
    return pd.read_csv(PROTOCOL_DIFF)


def load_checkpoint_meta(path: Path) -> Dict[str, Any]:
    ckpt = torch.load(path, map_location='cpu', weights_only=False)
    cfg = ckpt.get('configuration', {}) or {}
    tcfg = cfg.get('training', {}) or {}
    mcfg = cfg.get('model', {}) or {}
    score = ckpt.get('best_metric')
    if score is None:
        score = ckpt.get('best_validation_score')
    return {
        'epoch': ckpt.get('epoch'),
        'experiment_id': ckpt.get('experiment_id'),
        'manifest_version': ckpt.get('manifest_version'),
        'taxonomy_id': ckpt.get('taxonomy_id'),
        'seed': ckpt.get('seed'),
        'input_resolution': ckpt.get('input_resolution') or cfg.get('input_resolution'),
        'threshold': ckpt.get('threshold') or tcfg.get('threshold'),
        'model_name': ckpt.get('model_name') or mcfg.get('name'),
        'best_metric': score,
        'configuration': cfg,
        'early_stopping_state': ckpt.get('early_stopping_state', {}),
        'pytorch_version': ckpt.get('pytorch_version'),
        'gpu_name': ckpt.get('gpu_name'),
    }


# ---------------------------------------------------------------------------
# History integrity
# ---------------------------------------------------------------------------

def check_history_integrity(df: pd.DataFrame) -> Dict[str, Any]:
    best = df.loc[df['val_dice'].idxmax()]
    final = df.iloc[-1]
    return {
        'row_count': len(df),
        'contiguous_epochs': list(df['epoch']) == list(range(1, len(df) + 1)),
        'no_duplicates': df['epoch'].duplicated().sum() == 0,
        'best_epoch': int(best['epoch']),
        'best_val_dice': float(best['val_dice']),
        'best_val_iou': float(best['val_iou']),
        'best_val_precision': float(best['val_precision']),
        'best_val_recall': float(best['val_recall']),
        'unique_strict_max': int((df['val_dice'] == df['val_dice'].max()).sum()) == 1,
        'final_epoch': int(final['epoch']),
        'final_bad_epochs': int(final['bad_epochs']),
        'stop_consistent': int(final['epoch']) == int(best['epoch']) + int(final['bad_epochs']),
        'improved_count': int(df['improved'].sum()),
        'no_nan': not bool(df.isna().any().any()),
        'finite_losses': bool(df['train_loss'].notna().all() and df['val_loss'].notna().all()),
    }


def check_best_checkpoint_consistency() -> Dict[str, Any]:
    meta = load_checkpoint_meta(BEST_PT)
    df = load_history()
    best = df.loc[df['val_dice'].idxmax()]
    checks = {
        'epoch_matches': meta['epoch'] == int(best['epoch']),
        'experiment_id_matches': meta['experiment_id'] == EXPERIMENT_ID,
        'manifest_matches': meta['manifest_version'] == 'phase4_v3',
        'taxonomy_matches': meta['taxonomy_id'] == 'kub_size_clean_v3_v1',
        'seed_matches': meta['seed'] == 42,
        'model_matches': meta['model_name'] == 'deeplabv3plus',
        'resolution_matches': meta['input_resolution'] == 512,
        'threshold_matches': meta['threshold'] == 0.5,
        'score_agrees_with_history': abs(float(meta['best_metric']) - float(best['val_dice'])) < 1e-9,
    }
    checks['all_pass'] = all(checks.values())
    checks['epoch'] = meta['epoch']
    checks['best_metric'] = meta['best_metric']
    checks['bad_epochs'] = meta['early_stopping_state'].get('bad_epochs')
    return checks


def check_latest_checkpoint_consistency() -> Dict[str, Any]:
    meta = load_checkpoint_meta(LATEST_PT)
    df = load_history()
    final = df.iloc[-1]
    checks = {
        'epoch_matches': meta['epoch'] == int(final['epoch']),
        'experiment_id_matches': meta['experiment_id'] == EXPERIMENT_ID,
        'manifest_matches': meta['manifest_version'] == 'phase4_v3',
        'taxonomy_matches': meta['taxonomy_id'] == 'kub_size_clean_v3_v1',
        'seed_matches': meta['seed'] == 42,
        'model_matches': meta['model_name'] == 'deeplabv3plus',
        'bad_epochs_matches': int(meta['early_stopping_state'].get('bad_epochs', -1)) == int(final['bad_epochs']),
    }
    checks['all_pass'] = all(checks.values())
    checks['epoch'] = meta['epoch']
    checks['bad_epochs'] = meta['early_stopping_state'].get('bad_epochs')
    return checks


# ---------------------------------------------------------------------------
# EPOCH TABLE (reviewer-only; history.csv is never modified)
# ---------------------------------------------------------------------------

def build_epoch_table(df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """Build a reviewer epoch table: exactly one row per completed epoch.

    Raw columns come from the immutable history.csv. Derived columns are
    reviewer-only and are computed here (never written back to history).
    Missing physical fields are represented as N/A rather than fabricated.
    """
    if df is None:
        df = load_history()
    d = df.copy().sort_values('epoch').reset_index(drop=True)

    dice_col = 'val_dice' if 'val_dice' in d.columns else 'val_macro_dice'
    iou_col = 'val_iou' if 'val_iou' in d.columns else 'val_macro_iou'

    out = pd.DataFrame({'epoch': d['epoch'].astype(int)})
    out['train_loss'] = d['train_loss']
    out['val_loss'] = d['val_loss']
    out['val_macro_dice'] = d[dice_col]
    out['val_macro_iou'] = d[iou_col]
    # Availability-aware; never fabricated
    out['val_precision'] = d['val_precision'] if 'val_precision' in d.columns else 'N/A'
    out['val_recall'] = d['val_recall'] if 'val_recall' in d.columns else 'N/A'
    out['learning_rate'] = d['learning_rate']
    out['best_metric_so_far'] = d.get('best_so_far', pd.Series([np.nan] * len(d)))
    out['improved'] = d['improved'].astype(int)
    out['bad_epochs'] = d['bad_epochs'].astype(int)
    out['elapsed_seconds'] = d.get('epoch_seconds', pd.Series([np.nan] * len(d)))
    out['checkpoint_event'] = np.where(out['improved'] == 1, 'BEST_SAVED', 'LATEST_ONLY')

    # ---- derived reviewer-only columns ----
    dice = pd.to_numeric(out['val_macro_dice'], errors='coerce')
    out['delta_val_dice_vs_previous_epoch'] = dice.diff().round(10)
    best_so_far = pd.to_numeric(out['best_metric_so_far'], errors='coerce')
    out['delta_best_metric'] = best_so_far.diff().round(10)
    out['is_new_best'] = (out['improved'] == 1)
    best_epoch = int(out.loc[dice.idxmax(), 'epoch']) if dice.notna().any() else None
    out['is_best_epoch'] = out['epoch'] == best_epoch
    # epochs_since_best: epochs elapsed since the running best was last improved
    since = []
    last_best_ep = None
    for _, r in out.iterrows():
        if r['is_new_best']:
            last_best_ep = int(r['epoch'])
        since.append(0 if last_best_ep is None else int(r['epoch']) - last_best_ep)
    out['epochs_since_best'] = since
    return out


def verify_epoch_table(tbl: pd.DataFrame, history: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    if history is None:
        history = load_history()
    eps = tbl['epoch'].astype(int).tolist()
    expected = list(range(1, len(history) + 1))
    missing = sorted(set(expected) - set(eps))
    dupes = sorted({e for e in eps if eps.count(e) > 1})
    streak, longest = 0, 0
    for imp in tbl['improved']:
        streak = 0 if imp == 1 else streak + 1
        longest = max(longest, streak)
    return {
        'epochs_expected': len(history),
        'rows': len(tbl),
        'row_count_matches_history': len(tbl) == len(history),
        'unique_epochs': len(set(eps)),
        'first_epoch': min(eps) if eps else None,
        'last_epoch': max(eps) if eps else None,
        'missing_epochs': missing,
        'duplicate_epochs': dupes,
        'contiguous_1_to_N': eps == expected,
        'best_epoch': int(tbl.loc[pd.to_numeric(tbl['val_macro_dice']).idxmax(), 'epoch']),
        'improvement_events': int(tbl['improved'].sum()),
        'longest_no_improvement_streak': longest,
        'final_bad_epochs': int(tbl['bad_epochs'].iloc[-1]),
        'integrity_pass': (len(tbl) == len(history)) and (missing == []) and (dupes == [])
                          and (eps == expected),
    }


def save_epoch_table(tbl: pd.DataFrame, path: Optional[Path] = None) -> Path:
    path = path or EPOCH_TABLE_CSV
    path.parent.mkdir(parents=True, exist_ok=True)
    tbl.to_csv(path, index=False)
    return path


# ---------------------------------------------------------------------------
# KUB VAL scope
# ---------------------------------------------------------------------------

def derive_acquisition_type(image_path: str) -> str:
    p = str(image_path).replace('\\', '/')
    if '/ROI/' in p or '/roi/' in p:
        return 'ROI'
    if '/Images/' in p or '/images/' in p:
        return 'FULL_FIELD'
    return 'UNKNOWN'


def assert_kub_scope(df: pd.DataFrame) -> Dict[str, Any]:
    assert 'dataset' in df.columns, "manifest missing 'dataset' column"
    all_kub = bool((df['dataset'] == 'KUB').all())
    assert all_kub, f"Non-KUB present: {df.loc[df['dataset'] != 'KUB', 'dataset'].unique().tolist()}"
    assert len(df) == KUB_VAL_EXPECTED_ROWS, f"Expected 280 KUB VAL rows, got {len(df)}"
    cats = set(df['category'].unique())
    assert cats.issubset(KUB_ALLOWED_CATEGORIES), f"Unexpected categories: {cats - KUB_ALLOWED_CATEGORIES}"
    na = int((df['category'] == 'NOT_AVAILABLE').sum())
    assert na == 0, f"Found {na} NOT_AVAILABLE rows"
    unk = int((df['image_path'].apply(derive_acquisition_type) == 'UNKNOWN').sum())
    assert unk == 0, f"Found {unk} UNKNOWN acquisition types"
    return {'all_kub': all_kub, 'row_count': len(df), 'categories': cats,
            'not_available_count': na, 'unknown_acquisition_count': unk, 'all_pass': True}


def get_kub_val() -> pd.DataFrame:
    df = pd.read_csv(PROJECT_ROOT / 'manifests' / 'phase4_v3' / 'val.csv')
    kub = df[df['dataset'] == 'KUB'].copy()
    assert_kub_scope(kub)
    kub['acquisition_type'] = kub['image_path'].apply(derive_acquisition_type)
    return kub


def load_canonical_gallery(kub_val: pd.DataFrame) -> pd.DataFrame:
    actual = sha256_file(CANONICAL_GALLERY)
    assert actual == CANONICAL_GALLERY_SHA, (
        f"Canonical gallery SHA mismatch!\n expected {CANONICAL_GALLERY_SHA}\n actual   {actual}")
    sel = pd.read_csv(CANONICAL_GALLERY)
    assert len(sel) == 16, f"Expected 16 canonical cases, got {len(sel)}"
    merged = sel.merge(kub_val[['sample_id', 'image_path', 'mask_path', 'category',
                                'acquisition_type', 'patient_id']],
                       on='sample_id', how='left', suffixes=('', '_kub'))
    assert merged['image_path'].notna().all(), 'Canonical gallery IDs missing from KUB VAL!'
    return merged


# ---------------------------------------------------------------------------
# Inference (read-only, best checkpoint only)
# ---------------------------------------------------------------------------

def load_best_model_for_inference(device: str = 'cuda'):
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    from src.utils.device import get_device
    from src.models.deeplabv3plus import DeepLabV3Plus

    ckpt = torch.load(BEST_PT, map_location='cpu', weights_only=False)
    cfg = ckpt['configuration']['model']
    model = DeepLabV3Plus(in_channels=cfg['input_channels'],
                          out_channels=cfg['output_channels'],
                          base_channels=cfg.get('base_channels', 32))
    model.load_state_dict(ckpt['model_state'])
    dev = get_device(require_cuda=(device != 'cpu'))
    model = model.to(dev)
    model.eval()
    return model, dev


def predict_on_val_sample(model, device, image_path: Path, target_size: int = 512):
    img = Image.open(image_path).convert('L')
    w, h = img.size
    scale = min(target_size / w, target_size / h)
    nw, nh = int(w * scale), int(h * scale)
    img = img.resize((nw, nh), Image.BILINEAR)
    pl = (target_size - nw) // 2; pt = (target_size - nh) // 2
    pr = target_size - nw - pl; pb = target_size - nh - pt
    arr = np.array(img, dtype=np.float32) / 255.0
    arr = np.pad(arr, ((pt, pb), (pl, pr)), mode='constant', constant_values=0)
    ten = torch.from_numpy(arr).unsqueeze(0).unsqueeze(0).float().to(device)
    with torch.no_grad():
        with torch.amp.autocast('cuda', enabled=(device.type == 'cuda')):
            out = model(ten)
        prob = torch.sigmoid(out).squeeze().cpu().numpy()
    prob = prob[pt:pt + nh, pl:pl + nw]
    return prob, (nw, nh), (pl, pt)


# ---------------------------------------------------------------------------
# Curves
# ---------------------------------------------------------------------------

def plot_training_curves(df: pd.DataFrame, output_path: Optional[Path] = None):
    best_ep = int(df.loc[df['val_dice'].idxmax(), 'epoch'])
    final_ep = int(df['epoch'].iloc[-1])
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    fig.suptitle(f'Phase 10 DeepLabV3+ Clean-v3 Training Curves\n{EXPERIMENT_ID}', fontsize=12)

    ax = axes[0, 0]
    ax.plot(df['epoch'], df['train_loss'], label='Train loss', linewidth=1.2)
    ax.plot(df['epoch'], df['val_loss'], label='VAL loss', linewidth=1.2)
    ax.axvline(best_ep, color='green', linestyle='--', alpha=.7, label=f'Best {best_ep}')
    ax.axvline(final_ep, color='red', linestyle='--', alpha=.7, label=f'Stop {final_ep}')
    ax.set_xlabel('Epoch'); ax.set_ylabel('Loss'); ax.set_title('A. Train & VAL Loss')
    ax.legend(fontsize=7); ax.grid(True, alpha=.3)

    ax = axes[0, 1]
    ax.plot(df['epoch'], df['val_dice'], label='VAL macro Dice', linewidth=1.2, color='C2')
    ax.plot(df['epoch'], df['val_dice'].cummax(), label='Best so far', linewidth=1.,
            color='C3', linestyle='--')
    ax.axvline(best_ep, color='green', linestyle='--', alpha=.7)
    ax.axvline(final_ep, color='red', linestyle='--', alpha=.7)
    ax.set_xlabel('Epoch'); ax.set_ylabel('Dice'); ax.set_title('B. VAL Macro Dice')
    ax.legend(fontsize=7); ax.grid(True, alpha=.3)

    ax = axes[0, 2]
    ax.plot(df['epoch'], df['learning_rate'], linewidth=1.2, color='C4')
    ax.axvline(best_ep, color='green', linestyle='--', alpha=.7)
    ax.axvline(final_ep, color='red', linestyle='--', alpha=.7)
    ax.set_xlabel('Epoch'); ax.set_ylabel('LR'); ax.set_title('C. LR (CosineAnnealing)')
    ax.set_yscale('log'); ax.grid(True, alpha=.3)

    ax = axes[1, 0]
    ax.plot(df['epoch'], df['bad_epochs'], linewidth=1.2, color='C5')
    ax.axvline(best_ep, color='green', linestyle='--', alpha=.7)
    ax.axvline(final_ep, color='red', linestyle='--', alpha=.7)
    ax.axhline(15, color='red', linestyle=':', alpha=.5, label='Patience = 15')
    ax.set_xlabel('Epoch'); ax.set_ylabel('Bad epochs'); ax.set_title('D. Early-Stop Counter')
    ax.legend(fontsize=7); ax.grid(True, alpha=.3)

    ax = axes[1, 1]
    imp = df[df['improved'] == 1]
    ax.scatter(imp['epoch'], imp['val_dice'], color='green', s=30, zorder=5, label='Improvement')
    ax.plot(df['epoch'], df['val_dice'], linewidth=.8, color='gray', alpha=.5)
    ax.axvline(best_ep, color='green', linestyle='--', alpha=.7)
    ax.axvline(final_ep, color='red', linestyle='--', alpha=.7)
    ax.set_xlabel('Epoch'); ax.set_ylabel('Dice'); ax.set_title('E. Improvement Events')
    ax.legend(fontsize=7); ax.grid(True, alpha=.3)

    ax = axes[1, 2]; ax.axis('off')
    b = df.loc[df['val_dice'].idxmax()]
    summary = (
        f"Experiment: {EXPERIMENT_ID}\n"
        f"Arch: deeplabv3plus_resnet50_os16 (no pretrained)\n"
        f"Params: 40,340,769\n"
        f"Best epoch: {best_ep}\nBest VAL Dice: {df['val_dice'].max():.6f}\n"
        f"Best IoU: {float(b['val_iou']):.6f}\n"
        f"Precision: {float(b['val_precision']):.6f}\nRecall: {float(b['val_recall']):.6f}\n"
        f"Final epoch: {final_ep}\nStop: EARLY_STOP (patience 15)\n"
        f"Epochs: {len(df)} | Improvements: {int(df['improved'].sum())}"
    )
    ax.text(0.05, 0.5, summary, transform=ax.transAxes, fontsize=8,
            verticalalignment='center', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=.3))

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    if output_path:
        fig.savefig(output_path, dpi=150, bbox_inches='tight')
    return fig


def full_integrity_summary() -> Dict[str, Any]:
    df = load_history()
    hi = check_history_integrity(df)
    art = verify_artifact_shas()
    bck = check_best_checkpoint_consistency()
    lck = check_latest_checkpoint_consistency()
    tbl = build_epoch_table(df)
    ev = verify_epoch_table(tbl, df)
    return {'experiment_id': EXPERIMENT_ID, 'architecture': 'deeplabv3plus',
            'manifest_version': 'phase4_v3', 'taxonomy_id': 'kub_size_clean_v3_v1',
            'history_integrity': hi, 'artifact_shas': art,
            'best_checkpoint_consistency': bck, 'latest_checkpoint_consistency': lck,
            'epoch_table_integrity': ev,
            'overall_pass': (hi['contiguous_epochs'] and hi['stop_consistent']
                             and hi['unique_strict_max'] and art['all_pass']
                             and bck['all_pass'] and lck['all_pass']
                             and ev['integrity_pass'])}


if __name__ == '__main__':
    print('Phase 10 DeepLabV3+ reviewer support - self-test')
    print('=' * 55)
    art = verify_artifact_shas()
    print(f"Artifact SHAs: {'PASS' if art['all_pass'] else 'FAIL'}")
    h = load_history(); hi = check_history_integrity(h)
    print(f"History: rows={hi['row_count']} best_ep={hi['best_epoch']} "
          f"contig={hi['contiguous_epochs']} stop_ok={hi['stop_consistent']}")
    b = check_best_checkpoint_consistency(); print(f"Best ckpt: {'PASS' if b['all_pass'] else 'FAIL'} ep={b['epoch']}")
    l = check_latest_checkpoint_consistency(); print(f"Latest ckpt: {'PASS' if l['all_pass'] else 'FAIL'} ep={l['epoch']}")
    kv = get_kub_val(); print(f"KUB VAL: {len(kv)} | cats={kv['category'].value_counts().to_dict()}")
    print(f"Acq: {kv['acquisition_type'].value_counts().to_dict()}")
    g = load_canonical_gallery(kv); print(f"Canonical gallery: {len(g)} (SHA verified)")
    t = build_epoch_table(h); ev = verify_epoch_table(t, h)
    print(f"Epoch table: rows={ev['rows']} history={ev['epochs_expected']} "
          f"match={ev['row_count_matches_history']} integrity={'PASS' if ev['integrity_pass'] else 'FAIL'}")
