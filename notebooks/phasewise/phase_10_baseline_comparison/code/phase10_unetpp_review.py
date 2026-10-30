"""
Phase 10 Part 1B — Read-only reviewer / analysis support for the completed
CLEAN-v3 UNet++ run.

READ-ONLY. This module does NOT train, does NOT call optimizer.step(), does NOT
write checkpoints, and does NOT touch TEST.

Canonical training was executed by:
    notebooks/phasewise/phase_10_clean_v3_comparison/code/train_phase10_unetpp_clean_v3.py
That runner is frozen execution provenance and must not be altered.

Gallery note: this module reuses the CANONICAL frozen 16-case KUB VAL selection
(SHA 10ad09cb...) shared with UNet and Attention U-Net so the three models are
paired on identical samples. It never reselects cases.

Author: Gemini 3.8 Flash Medium
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
EXPERIMENT_ID = 'phase10_kub_unetpp_seed42_512_clean_v3'
EXPERIMENT_DIR = PROJECT_ROOT / 'experiments' / EXPERIMENT_ID
CHECKPOINT_DIR = PROJECT_ROOT / 'checkpoints' / EXPERIMENT_ID
CONFIG_PATH = PROJECT_ROOT / 'configs' / 'phase10_clean_v3' / 'phase10_unetpp_clean_v3.yaml'
HISTORY_PATH = EXPERIMENT_DIR / 'history.csv'
BEST_PT = CHECKPOINT_DIR / 'best.pt'
LATEST_PT = CHECKPOINT_DIR / 'latest.pt'
TAXONOMY_ARTIFACT = PROJECT_ROOT / 'reports' / 'audits' / 'kub_size_clean_v3_v1_thresholds.json'
START_AUDIT = PROJECT_ROOT / 'reports' / 'audits' / 'phase10_unetpp_clean_v3_training_start_audit.json'
COMPLETION_AUDIT = PROJECT_ROOT / 'reports' / 'audits' / 'phase10_unetpp_clean_v3_training_completion_audit.json'
PROTOCOL_DIFF = PROJECT_ROOT / 'reports' / 'tables' / 'phase10_unetpp_v2_to_clean_v3_protocol_diff.csv'

TRAINING_RUNNER = (PROJECT_ROOT / 'notebooks' / 'phasewise' / 'phase_10_clean_v3_comparison'
                   / 'code' / 'train_phase10_unetpp_clean_v3.py')

# Frozen provenance (recorded at completion)
EXPECTED_CONFIG_SHA = 'e2788e504b09cd8544e45fb7aef4001b8363452963d7d793f693647b4df24f53'
EXPECTED_BEST_SHA = 'ec7eb13f32e43af27eab7fc617bd1a2a8fcce1d6651a1b4a3653f3e4d1283269'
EXPECTED_LATEST_SHA = '77a39b4f510f69956233af898f7f62d4ae755fac57375bab70f95102b142c8ef'
EXPECTED_HISTORY_SHA = 'a733d8366278d2ddb1a44db0d94ff7525fb9b10afefba787abfd036c1fb1de5a'
TAXONOMY_SHA = '89031c51a35c24f6f939fd6206fde6002a019d4bda24ce8cb21988f04db0f0d6'

# Canonical paired gallery (shared with UNet + Attention U-Net)
CANONICAL_GALLERY = PROJECT_ROOT / 'reports' / 'tables' / 'phase09_clean_v3_val_gallery_selection.csv'
CANONICAL_GALLERY_SHA = '10ad09cbcaabb56bc6bc6aefe016c83b2173933bf6d1f16e4baaf3f0845613db'

KUB_VAL_EXPECTED_ROWS = 280
KUB_ALLOWED_CATEGORIES = {'Kidney_Stone', 'Bladder_Stone', 'Ureteric_Stone'}

HISTORICAL_EXPERIMENT_ID = 'phase10_kub_unetpp_seed42_512'


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
    res = {
        'config_match': sha256_file(CONFIG_PATH) == EXPECTED_CONFIG_SHA,
        'config_sha': sha256_file(CONFIG_PATH),
        'best_pt_match': sha256_file(BEST_PT) == EXPECTED_BEST_SHA,
        'best_pt_sha': sha256_file(BEST_PT),
        'latest_pt_match': sha256_file(LATEST_PT) == EXPECTED_LATEST_SHA,
        'latest_pt_sha': sha256_file(LATEST_PT),
        'history_match': sha256_file(HISTORY_PATH) == EXPECTED_HISTORY_SHA,
        'history_sha': sha256_file(HISTORY_PATH),
        'taxonomy_match': sha256_file(TAXONOMY_ARTIFACT) == TAXONOMY_SHA,
        'taxonomy_sha': sha256_file(TAXONOMY_ARTIFACT),
    }
    res['runner_sha'] = sha256_file(TRAINING_RUNNER)
    res['protocol_diff_sha'] = sha256_file(PROTOCOL_DIFF)
    res['all_pass'] = all([
        res['config_match'], res['best_pt_match'], res['latest_pt_match'],
        res['history_match'], res['taxonomy_match'],
    ])
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
    """Load checkpoint metadata without instantiating the model.

    The clean runner stores the monitored score under `best_metric` and keeps
    resolution/threshold/model name inside `configuration`. Resolve both.
    """
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
        'cuda_available': ckpt.get('cuda_available'),
        'gpu_name': ckpt.get('gpu_name'),
    }


# ---------------------------------------------------------------------------
# History integrity
# ---------------------------------------------------------------------------

def check_history_integrity(df: pd.DataFrame) -> Dict[str, Any]:
    best_row = df.loc[df['val_dice'].idxmax()]
    final_row = df.iloc[-1]
    return {
        'row_count': len(df),
        'contiguous_epochs': list(df['epoch']) == list(range(1, len(df) + 1)),
        'no_duplicates': df['epoch'].duplicated().sum() == 0,
        'best_epoch': int(best_row['epoch']),
        'best_val_dice': float(best_row['val_dice']),
        'best_val_iou': float(best_row['val_iou']),
        'best_val_precision': float(best_row['val_precision']),
        'best_val_recall': float(best_row['val_recall']),
        'unique_strict_max': int((df['val_dice'] == df['val_dice'].max()).sum()) == 1,
        'final_epoch': int(final_row['epoch']),
        'final_bad_epochs': int(final_row['bad_epochs']),
        'stop_consistent': int(final_row['epoch']) == int(best_row['epoch']) + int(final_row['bad_epochs']),
        'improved_count': int(df['improved'].sum()),
        'no_nan': not bool(df.isna().any().any()),
        'finite_losses': bool(df['train_loss'].notna().all() and df['val_loss'].notna().all()),
    }


def check_best_checkpoint_consistency() -> Dict[str, Any]:
    meta = load_checkpoint_meta(BEST_PT)
    df = load_history()
    best_row = df.loc[df['val_dice'].idxmax()]
    checks = {
        'epoch_matches': meta['epoch'] == int(best_row['epoch']),
        'experiment_id_matches': meta['experiment_id'] == EXPERIMENT_ID,
        'manifest_matches': meta['manifest_version'] == 'phase4_v3',
        'taxonomy_matches': meta['taxonomy_id'] == 'kub_size_clean_v3_v1',
        'seed_matches': meta['seed'] == 42,
        'model_matches': meta['model_name'] == 'unetpp',
        'resolution_matches': meta['input_resolution'] == 512,
        'threshold_matches': meta['threshold'] == 0.5,
        'score_agrees_with_history': abs(float(meta['best_metric']) - float(best_row['val_dice'])) < 1e-9,
    }
    checks['all_pass'] = all(checks.values())
    checks['epoch'] = meta['epoch']
    checks['best_metric'] = meta['best_metric']
    checks['bad_epochs'] = meta['early_stopping_state'].get('bad_epochs')
    return checks


def check_latest_checkpoint_consistency() -> Dict[str, Any]:
    meta = load_checkpoint_meta(LATEST_PT)
    df = load_history()
    final_row = df.iloc[-1]
    checks = {
        'epoch_matches': meta['epoch'] == int(final_row['epoch']),
        'experiment_id_matches': meta['experiment_id'] == EXPERIMENT_ID,
        'manifest_matches': meta['manifest_version'] == 'phase4_v3',
        'taxonomy_matches': meta['taxonomy_id'] == 'kub_size_clean_v3_v1',
        'seed_matches': meta['seed'] == 42,
        'model_matches': meta['model_name'] == 'unetpp',
        'bad_epochs_matches': int(meta['early_stopping_state'].get('bad_epochs', -1)) == int(final_row['bad_epochs']),
    }
    checks['all_pass'] = all(checks.values())
    checks['epoch'] = meta['epoch']
    checks['bad_epochs'] = meta['early_stopping_state'].get('bad_epochs')
    return checks


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
    assert all_kub, f"Non-KUB datasets present: {df.loc[df['dataset'] != 'KUB', 'dataset'].unique().tolist()}"
    assert len(df) == KUB_VAL_EXPECTED_ROWS, f"Expected {KUB_VAL_EXPECTED_ROWS} KUB VAL rows, got {len(df)}"
    cats = set(df['category'].unique())
    assert cats.issubset(KUB_ALLOWED_CATEGORIES), f"Unexpected categories: {cats - KUB_ALLOWED_CATEGORIES}"
    na_count = int((df['category'] == 'NOT_AVAILABLE').sum())
    assert na_count == 0, f"Found {na_count} NOT_AVAILABLE rows"
    acqs = df['image_path'].apply(derive_acquisition_type)
    unknown = int((acqs == 'UNKNOWN').sum())
    assert unknown == 0, f"Found {unknown} UNKNOWN acquisition types"
    return {'all_kub': all_kub, 'row_count': len(df), 'categories': cats,
            'not_available_count': na_count, 'unknown_acquisition_count': unknown, 'all_pass': True}


def get_kub_val() -> pd.DataFrame:
    df = pd.read_csv(PROJECT_ROOT / 'manifests' / 'phase4_v3' / 'val.csv')
    kub = df[df['dataset'] == 'KUB'].copy()
    assert_kub_scope(kub)
    kub['acquisition_type'] = kub['image_path'].apply(derive_acquisition_type)
    return kub


def load_canonical_gallery(kub_val: pd.DataFrame) -> pd.DataFrame:
    """Load the CANONICAL frozen 16-case selection (shared across models).

    Verifies the file SHA and that every selected sample is a KUB VAL row.
    Never reselects. This guarantees UNet / Attention U-Net / UNet++ are paired
    on identical samples.
    """
    actual = sha256_file(CANONICAL_GALLERY)
    assert actual == CANONICAL_GALLERY_SHA, (
        f"Canonical gallery SHA mismatch!\n  expected {CANONICAL_GALLERY_SHA}\n  actual   {actual}")
    sel = pd.read_csv(CANONICAL_GALLERY)
    assert len(sel) == 16, f"Expected 16 canonical cases, got {len(sel)}"
    # Join to KUB VAL to get current paths/metadata (IDs are the authority)
    merged = sel.merge(
        kub_val[['sample_id', 'image_path', 'mask_path', 'category', 'acquisition_type', 'patient_id']],
        on='sample_id', how='left', suffixes=('', '_kub'))
    assert merged['image_path'].notna().all(), 'Some canonical gallery IDs missing from KUB VAL!'
    return merged


# ---------------------------------------------------------------------------
# Inference (read-only, best checkpoint only)
# ---------------------------------------------------------------------------

def load_best_model_for_inference(device: str = 'cuda'):
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    from src.utils.device import get_device
    from src.models.unetpp import UNetPlusPlus

    ckpt = torch.load(BEST_PT, map_location='cpu', weights_only=False)
    cfg = ckpt['configuration']['model']
    model = UNetPlusPlus(in_channels=cfg['input_channels'],
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
    new_w, new_h = int(w * scale), int(h * scale)
    img = img.resize((new_w, new_h), Image.BILINEAR)
    pad_left = (target_size - new_w) // 2
    pad_top = (target_size - new_h) // 2
    pad_right = target_size - new_w - pad_left
    pad_bottom = target_size - new_h - pad_top
    arr = np.array(img, dtype=np.float32) / 255.0
    arr = np.pad(arr, ((pad_top, pad_bottom), (pad_left, pad_right)),
                 mode='constant', constant_values=0)
    tensor = torch.from_numpy(arr).unsqueeze(0).unsqueeze(0).float().to(device)
    with torch.no_grad():
        with torch.amp.autocast('cuda', enabled=(device.type == 'cuda')):
            out = model(tensor)
        prob = torch.sigmoid(out).squeeze().cpu().numpy()
    prob = prob[pad_top:pad_top + new_h, pad_left:pad_left + new_w]
    return prob, (new_w, new_h), (pad_left, pad_top)


# ---------------------------------------------------------------------------
# Curves
# ---------------------------------------------------------------------------

def plot_training_curves(df: pd.DataFrame, output_path: Optional[Path] = None):
    best_epoch = int(df.loc[df['val_dice'].idxmax(), 'epoch'])
    final_epoch = int(df['epoch'].iloc[-1])
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    fig.suptitle(f'Phase 10 UNet++ Clean-v3 Training Curves\n{EXPERIMENT_ID}', fontsize=12)

    ax = axes[0, 0]
    ax.plot(df['epoch'], df['train_loss'], label='Train loss', linewidth=1.2)
    ax.plot(df['epoch'], df['val_loss'], label='VAL loss', linewidth=1.2)
    ax.axvline(best_epoch, color='green', linestyle='--', alpha=0.7, label=f'Best {best_epoch}')
    ax.axvline(final_epoch, color='red', linestyle='--', alpha=0.7, label=f'Stop {final_epoch}')
    ax.set_xlabel('Epoch'); ax.set_ylabel('Loss'); ax.set_title('A. Train & VAL Loss')
    ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

    ax = axes[0, 1]
    ax.plot(df['epoch'], df['val_dice'], label='VAL macro Dice', linewidth=1.2, color='C2')
    ax.plot(df['epoch'], df['val_dice'].cummax(), label='Best so far', linewidth=1.0,
            color='C3', linestyle='--')
    ax.axvline(best_epoch, color='green', linestyle='--', alpha=0.7)
    ax.axvline(final_epoch, color='red', linestyle='--', alpha=0.7)
    ax.set_xlabel('Epoch'); ax.set_ylabel('Dice'); ax.set_title('B. VAL Macro Dice')
    ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

    ax = axes[0, 2]
    ax.plot(df['epoch'], df['learning_rate'], linewidth=1.2, color='C4')
    ax.axvline(best_epoch, color='green', linestyle='--', alpha=0.7)
    ax.axvline(final_epoch, color='red', linestyle='--', alpha=0.7)
    ax.set_xlabel('Epoch'); ax.set_ylabel('LR')
    ax.set_title('C. Learning Rate (CosineAnnealing)')
    ax.set_yscale('log'); ax.grid(True, alpha=0.3)

    ax = axes[1, 0]
    ax.plot(df['epoch'], df['bad_epochs'], linewidth=1.2, color='C5')
    ax.axvline(best_epoch, color='green', linestyle='--', alpha=0.7)
    ax.axvline(final_epoch, color='red', linestyle='--', alpha=0.7)
    ax.axhline(15, color='red', linestyle=':', alpha=0.5, label='Patience = 15')
    ax.set_xlabel('Epoch'); ax.set_ylabel('Bad epochs'); ax.set_title('D. Early-Stop Counter')
    ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

    ax = axes[1, 1]
    imp = df[df['improved'] == 1]
    ax.scatter(imp['epoch'], imp['val_dice'], color='green', s=30, zorder=5, label='Improvement')
    ax.plot(df['epoch'], df['val_dice'], linewidth=0.8, color='gray', alpha=0.5)
    ax.axvline(best_epoch, color='green', linestyle='--', alpha=0.7)
    ax.axvline(final_epoch, color='red', linestyle='--', alpha=0.7)
    ax.set_xlabel('Epoch'); ax.set_ylabel('Dice'); ax.set_title('E. Improvement Events')
    ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

    ax = axes[1, 2]
    ax.axis('off')
    best = df.loc[df['val_dice'].idxmax()]
    summary = (
        f"Experiment: {EXPERIMENT_ID}\n"
        f"Architecture: unetpp (base 32, no deep supervision)\n"
        f"Best epoch: {best_epoch}\n"
        f"Best VAL macro Dice: {df['val_dice'].max():.6f}\n"
        f"Best VAL macro IoU: {float(best['val_iou']):.6f}\n"
        f"Best Precision: {float(best['val_precision']):.6f}\n"
        f"Best Recall: {float(best['val_recall']):.6f}\n"
        f"Final epoch: {final_epoch}\n"
        f"Stop: EARLY_STOP (patience 15)\n"
        f"Epochs: {len(df)} | Improvements: {int(df['improved'].sum())}\n"
        f"Epoch time: ~179s (UNet++ is the slowest of the three)"
    )
    ax.text(0.05, 0.5, summary, transform=ax.transAxes, fontsize=8,
            verticalalignment='center', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

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
    return {'experiment_id': EXPERIMENT_ID, 'architecture': 'unetpp',
            'manifest_version': 'phase4_v3', 'taxonomy_id': 'kub_size_clean_v3_v1',
            'history_integrity': hi, 'artifact_shas': art,
            'best_checkpoint_consistency': bck, 'latest_checkpoint_consistency': lck,
            'overall_pass': (hi['contiguous_epochs'] and hi['stop_consistent']
                             and hi['unique_strict_max'] and art['all_pass']
                             and bck['all_pass'] and lck['all_pass'])}


if __name__ == '__main__':
    print('Phase 10 UNet++ reviewer support - self-test')
    print('=' * 52)
    art = verify_artifact_shas()
    print(f"Artifact SHAs: {'PASS' if art['all_pass'] else 'FAIL'} (runner {art['runner_sha'][:16]}...)")
    hi = check_history_integrity(load_history())
    print(f"History: rows={hi['row_count']} best_epoch={hi['best_epoch']} "
          f"contiguous={hi['contiguous_epochs']} stop_ok={hi['stop_consistent']}")
    bck = check_best_checkpoint_consistency()
    print(f"Best ckpt: {'PASS' if bck['all_pass'] else 'FAIL'} epoch={bck['epoch']}")
    lck = check_latest_checkpoint_consistency()
    print(f"Latest ckpt: {'PASS' if lck['all_pass'] else 'FAIL'} epoch={lck['epoch']} bad={lck['bad_epochs']}")
    kv = get_kub_val()
    print(f"KUB VAL: {len(kv)} rows | cats={kv['category'].value_counts().to_dict()}")
    print(f"Acquisition: {kv['acquisition_type'].value_counts().to_dict()}")
    g = load_canonical_gallery(kv)
    print(f"Canonical gallery: {len(g)} cases (SHA verified {CANONICAL_GALLERY_SHA[:16]}...)")
    print('All gates:', 'PASS' if (art['all_pass'] and hi['contiguous_epochs']
          and hi['stop_consistent'] and bck['all_pass'] and lck['all_pass']) else 'FAIL')
