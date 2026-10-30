"""
Phase 09 Part 1B-R1 — Read-only reviewer / analysis support (REPAIRED).

This module contains READ-ONLY reviewer functions for the completed clean-v3 UNet
baseline training run. It does NOT train. It does NOT modify checkpoints or history.

REPAIR NOTE (Part 1B-R1):
- Pre-repair notebook (SHA 7721a285...) accidentally used the full 808-row multi-domain
  VAL manifest for gallery selection, mixing ISIC/BUSI/Kvasir cases into the KUB review.
- This version filters VAL to KUB-only (280 rows) and derives acquisition_type from paths.
- The mixed-domain gallery outputs from the pre-repair notebook are INVALID_SUPERSEDED.

Canonical training was executed by:
    notebooks/phasewise/phase_09_clean_v3_baseline/code/train_phase09_clean_v3.py
That runner is frozen execution provenance and must not be altered.

Author: Gemini 3.8 Flash Medium
Date: 2026-09-20
"""

from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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
EXPERIMENT_ID = 'phase9_kub_unet_baseline_seed42_512_clean_v3'
EXPERIMENT_DIR = PROJECT_ROOT / 'experiments' / EXPERIMENT_ID
CHECKPOINT_DIR = PROJECT_ROOT / 'checkpoints' / EXPERIMENT_ID
CONFIG_PATH = PROJECT_ROOT / 'configs' / 'phase09_clean_v3' / 'phase09_unet_baseline_clean_v3.yaml'
HISTORY_PATH = EXPERIMENT_DIR / 'history.csv'
BEST_PT = CHECKPOINT_DIR / 'best.pt'
LATEST_PT = CHECKPOINT_DIR / 'latest.pt'
TAXONOMY_ARTIFACT = PROJECT_ROOT / 'reports' / 'audits' / 'kub_size_clean_v3_v1_thresholds.json'
START_AUDIT = PROJECT_ROOT / 'reports' / 'audits' / 'phase09_clean_v3_training_start_audit.json'
COMPLETION_AUDIT = PROJECT_ROOT / 'reports' / 'audits' / 'phase09_clean_v3_training_completion_audit.json'

HISTORICAL_BEST_PT = PROJECT_ROOT / 'checkpoints' / 'phase9_kub_unet_baseline_seed42_512' / 'best.pt'
HISTORICAL_LATEST_PT = PROJECT_ROOT / 'checkpoints' / 'phase9_kub_unet_baseline_seed42_512' / 'latest.pt'

EXPECTED_CONFIG_SHA = '8a45458c7c5e34062214a741550a84ff9ab56e4ad9ceef81cbcf263052b5172a'
EXPECTED_BEST_SHA = '7b955ba86464a2fec2d569ecb6124de1fa9a4e66d0b5d58b267be9a280b4c2c0'
EXPECTED_LATEST_SHA = '6de118bf21cacd560769bfc5781d2928e0ef0c96e41035c34d6bb17f375e4509'
EXPECTED_HISTORY_SHA = '7678a5822542cd356f85e9c153da460a87e58d85e7cd1221d8fb66e323f60217'

TAXONOMY_SHA = '89031c51a35c24f6f939fd6206fde6002a019d4bda24ce8cb21988f04db0f0d6'

KUB_VAL_EXPECTED_ROWS = 280
KUB_ALLOWED_CATEGORIES = {'Kidney_Stone', 'Bladder_Stone', 'Ureteric_Stone'}

# Pre-repair notebook SHA for audit trail
PRE_REPAIR_NOTEBOOK_SHA = '7721a28575fc8ffa6e2eed226232a26c4bb2c41e1c40c4a33459a004b122c318'

# ---------------------------------------------------------------------------
# Artifact hashing
# ---------------------------------------------------------------------------

def sha256_file(path: Path) -> str:
    """Compute SHA-256 of a file."""
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def verify_artifact_shas() -> Dict[str, Any]:
    """Verify all physical artifact SHAs against recorded provenance."""
    results = {
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
        'all_pass': None,
    }
    results['all_pass'] = all([
        results['config_match'], results['best_pt_match'],
        results['latest_pt_match'], results['history_match'], results['taxonomy_match']
    ])
    return results


# ---------------------------------------------------------------------------
# History / audit loading
# ---------------------------------------------------------------------------

def load_history() -> pd.DataFrame:
    """Load training history."""
    return pd.read_csv(HISTORY_PATH)


def load_start_audit() -> Dict[str, Any]:
    return json.loads(START_AUDIT.read_text(encoding='utf-8'))


def load_completion_audit() -> Dict[str, Any]:
    return json.loads(COMPLETION_AUDIT.read_text(encoding='utf-8'))


def load_config() -> Dict[str, Any]:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding='utf-8'))


# ---------------------------------------------------------------------------
# Checkpoint metadata (safe load)
# ---------------------------------------------------------------------------

def load_checkpoint_meta(path: Path) -> Dict[str, Any]:
    """Load checkpoint metadata without instantiating model."""
    ckpt = torch.load(path, map_location='cpu', weights_only=False)
    meta = {
        'epoch': ckpt.get('epoch'),
        'experiment_id': ckpt.get('experiment_id'),
        'manifest_version': ckpt.get('manifest_version'),
        'taxonomy_id': ckpt.get('taxonomy_id'),
        'seed': ckpt.get('seed'),
        'input_resolution': ckpt.get('input_resolution'),
        'threshold': ckpt.get('threshold'),
        'best_validation_score': ckpt.get('best_validation_score'),
        'configuration': ckpt.get('configuration', {}),
        'early_stopping_state': ckpt.get('early_stopping_state', {}),
        'model_name': ckpt.get('model_name'),
        'pytorch_version': ckpt.get('pytorch_version'),
        'cuda_available': ckpt.get('cuda_available'),
        'gpu_name': ckpt.get('gpu_name'),
    }
    return meta


# ---------------------------------------------------------------------------
# History integrity checks
# ---------------------------------------------------------------------------

def check_history_integrity(df: pd.DataFrame) -> Dict[str, Any]:
    """Recompute history consistency independently."""
    expected_epochs = list(range(1, len(df) + 1))
    epoch_list = list(df['epoch'])
    best_idx = df['val_macro_dice'].idxmax()
    best_row = df.loc[best_idx]
    final_row = df.iloc[-1]

    return {
        'row_count': len(df),
        'contiguous_epochs': epoch_list == expected_epochs,
        'best_epoch': int(best_row['epoch']),
        'best_val_macro_dice': float(best_row['val_macro_dice']),
        'final_epoch': int(final_row['epoch']),
        'final_bad_epochs': int(final_row['bad_epochs']),
        'stop_consistent': int(final_row['epoch']) == int(best_row['epoch']) + int(final_row['bad_epochs']),
        'improved_count': int(df['improved'].sum()),
        'no_nan': not bool(df.isna().any().any()),
        'finite_losses': bool(df['train_loss'].notna().all() and df['val_loss'].notna().all()),
    }


# ---------------------------------------------------------------------------
# Checkpoint consistency
# ---------------------------------------------------------------------------

def check_best_checkpoint_consistency() -> Dict[str, Any]:
    meta = load_checkpoint_meta(BEST_PT)
    df = load_history()
    best_row = df.loc[df['val_macro_dice'].idxmax()]
    epoch_matches = meta['epoch'] == int(best_row['epoch'])
    exp_matches = meta['experiment_id'] == EXPERIMENT_ID
    manifest_matches = meta['manifest_version'] == 'phase4_v3'
    taxonomy_matches = meta['taxonomy_id'] == 'kub_size_clean_v3_v1'
    seed_matches = meta['seed'] == 42
    return {
        'epoch_matches': epoch_matches,
        'epoch': meta['epoch'],
        'experiment_id_matches': exp_matches,
        'experiment_id': meta['experiment_id'],
        'manifest_matches': manifest_matches,
        'manifest_version': meta['manifest_version'],
        'taxonomy_matches': taxonomy_matches,
        'taxonomy_id': meta['taxonomy_id'],
        'seed_matches': seed_matches,
        'seed': meta['seed'],
        'input_resolution': meta['input_resolution'],
        'configuration_present': bool(meta['configuration']),
        'config_model': meta['configuration'].get('model', {}).get('name'),
        'all_pass': epoch_matches and exp_matches and manifest_matches and taxonomy_matches and seed_matches,
    }


def check_latest_checkpoint_consistency() -> Dict[str, Any]:
    meta = load_checkpoint_meta(LATEST_PT)
    df = load_history()
    final_row = df.iloc[-1]
    epoch_matches = meta['epoch'] == int(final_row['epoch'])
    exp_matches = meta['experiment_id'] == EXPERIMENT_ID
    manifest_matches = meta['manifest_version'] == 'phase4_v3'
    taxonomy_matches = meta['taxonomy_id'] == 'kub_size_clean_v3_v1'
    seed_matches = meta['seed'] == 42
    return {
        'epoch_matches': epoch_matches,
        'epoch': meta['epoch'],
        'experiment_id_matches': exp_matches,
        'experiment_id': meta['experiment_id'],
        'manifest_matches': manifest_matches,
        'manifest_version': meta['manifest_version'],
        'taxonomy_matches': taxonomy_matches,
        'taxonomy_id': meta['taxonomy_id'],
        'seed_matches': seed_matches,
        'seed': meta['seed'],
        'bad_epochs': meta['early_stopping_state'].get('bad_epochs') if meta['early_stopping_state'] else None,
        'all_pass': epoch_matches and exp_matches and manifest_matches and taxonomy_matches and seed_matches,
    }


# ---------------------------------------------------------------------------
# Training curves
# ---------------------------------------------------------------------------

def plot_training_curves(df: pd.DataFrame, output_path: Optional[Path] = None) -> plt.Figure:
    """Generate reviewer-quality training curves from history."""
    best_epoch = int(df.loc[df['val_macro_dice'].idxmax(), 'epoch'])
    final_epoch = int(df['epoch'].iloc[-1])

    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    fig.suptitle(f'Phase 09 Clean-v3 UNet Baseline Training Curves\n{EXPERIMENT_ID}', fontsize=12)

    # A. Train + Val loss
    ax = axes[0, 0]
    ax.plot(df['epoch'], df['train_loss'], label='Train loss', linewidth=1.2)
    ax.plot(df['epoch'], df['val_loss'], label='VAL loss', linewidth=1.2)
    ax.axvline(best_epoch, color='green', linestyle='--', alpha=0.7, label=f'Best epoch {best_epoch}')
    ax.axvline(final_epoch, color='red', linestyle='--', alpha=0.7, label=f'Stop epoch {final_epoch}')
    ax.set_xlabel('Epoch')
    ax.set_ylabel('Loss')
    ax.set_title('A. Train & VAL Loss')
    ax.legend(fontsize=7)
    ax.grid(True, alpha=0.3)

    # B. VAL macro Dice + best-so-far
    ax = axes[0, 1]
    ax.plot(df['epoch'], df['val_macro_dice'], label='VAL macro Dice', linewidth=1.2, color='C2')
    best_sofar = df['val_macro_dice'].cummax()
    ax.plot(df['epoch'], best_sofar, label='Best so far', linewidth=1.0, color='C3', linestyle='--')
    ax.axvline(best_epoch, color='green', linestyle='--', alpha=0.7)
    ax.axvline(final_epoch, color='red', linestyle='--', alpha=0.7)
    ax.set_xlabel('Epoch')
    ax.set_ylabel('Dice')
    ax.set_title('B. VAL Macro Dice')
    ax.legend(fontsize=7)
    ax.grid(True, alpha=0.3)

    # C. Learning rate
    ax = axes[0, 2]
    ax.plot(df['epoch'], df['learning_rate'], linewidth=1.2, color='C4')
    ax.axvline(best_epoch, color='green', linestyle='--', alpha=0.7)
    ax.axvline(final_epoch, color='red', linestyle='--', alpha=0.7)
    ax.set_xlabel('Epoch')
    ax.set_ylabel('LR')
    ax.set_title('C. Learning Rate (CosineAnnealing)')
    ax.set_yscale('log')
    ax.grid(True, alpha=0.3)

    # D. Early-stop counter
    ax = axes[1, 0]
    ax.plot(df['epoch'], df['bad_epochs'], linewidth=1.2, color='C5')
    ax.axvline(best_epoch, color='green', linestyle='--', alpha=0.7)
    ax.axvline(final_epoch, color='red', linestyle='--', alpha=0.7)
    ax.axhline(15, color='red', linestyle=':', alpha=0.5, label='Patience = 15')
    ax.set_xlabel('Epoch')
    ax.set_ylabel('Bad epochs')
    ax.set_title('D. Early-Stop Counter')
    ax.legend(fontsize=7)
    ax.grid(True, alpha=0.3)

    # E. Checkpoint improvement events
    ax = axes[1, 1]
    improved = df[df['improved'] == 1]
    ax.scatter(improved['epoch'], improved['val_macro_dice'], color='green', s=30, zorder=5, label='Improvement')
    ax.plot(df['epoch'], df['val_macro_dice'], linewidth=0.8, color='gray', alpha=0.5)
    ax.axvline(best_epoch, color='green', linestyle='--', alpha=0.7)
    ax.axvline(final_epoch, color='red', linestyle='--', alpha=0.7)
    ax.set_xlabel('Epoch')
    ax.set_ylabel('Dice')
    ax.set_title('E. Improvement Events')
    ax.legend(fontsize=7)
    ax.grid(True, alpha=0.3)

    # F. Summary text
    ax = axes[1, 2]
    ax.axis('off')
    summary = (
        f"Experiment: {EXPERIMENT_ID}\n"
        f"Best epoch: {best_epoch}\n"
        f"Best VAL macro Dice: {df['val_macro_dice'].max():.6f}\n"
        f"Final epoch: {final_epoch}\n"
        f"Stop reason: EARLY_STOP\n"
        f"Patience: 15\n"
        f"Total epochs: {len(df)}\n"
        f"Improvements: {int(df['improved'].sum())}\n"
        f"Config SHA: {EXPECTED_CONFIG_SHA[:16]}...\n"
        f"Best ckpt SHA: {EXPECTED_BEST_SHA[:16]}...\n"
        f"Latest ckpt SHA: {EXPECTED_LATEST_SHA[:16]}...\n"
        f"History SHA: {EXPECTED_HISTORY_SHA[:16]}..."
    )
    ax.text(0.1, 0.5, summary, transform=ax.transAxes, fontsize=9,
            verticalalignment='center', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    if output_path:
        fig.savefig(output_path, dpi=150, bbox_inches='tight')
    return fig


# ---------------------------------------------------------------------------
# KUB VAL scope assertions
# ---------------------------------------------------------------------------

def derive_acquisition_type(image_path: str) -> str:
    """Derive acquisition type from image path using Phase-06 convention."""
    p = str(image_path).replace('\\', '/')
    if '/ROI/' in p:
        return 'ROI'
    if '/Images/' in p:
        return 'FULL_FIELD'
    return 'UNKNOWN'


def assert_phase09_kub_scope(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Hard assertions that df is the correct KUB-only VAL scope for Phase 09.
    Returns a dict of check results; raises AssertionError on failure.
    """
    results = {
        'has_dataset_col': 'dataset' in df.columns,
        'all_kub': False,
        'row_count': len(df),
        'expected_row_count': KUB_VAL_EXPECTED_ROWS,
        'row_count_match': False,
        'categories': set(),
        'categories_allowed': False,
        'not_available_count': 0,
        'no_not_available': False,
        'unknown_acquisition_count': 0,
        'no_unknown_acquisition': False,
        'all_pass': False,
    }

    assert results['has_dataset_col'], "VAL manifest missing 'dataset' column"
    results['all_kub'] = bool((df['dataset'] == 'KUB').all())
    assert results['all_kub'], f"Non-KUB datasets found: {df.loc[df['dataset'] != 'KUB', 'dataset'].unique().tolist()}"

    results['row_count_match'] = len(df) == KUB_VAL_EXPECTED_ROWS
    assert results['row_count_match'], f"Expected {KUB_VAL_EXPECTED_ROWS} KUB VAL rows, got {len(df)}"

    results['categories'] = set(df['category'].unique())
    results['categories_allowed'] = results['categories'].issubset(KUB_ALLOWED_CATEGORIES)
    assert results['categories_allowed'], f"Unexpected categories: {results['categories'] - KUB_ALLOWED_CATEGORIES}"

    results['not_available_count'] = int((df['category'] == 'NOT_AVAILABLE').sum())
    results['no_not_available'] = results['not_available_count'] == 0
    assert results['no_not_available'], f"Found {results['not_available_count']} NOT_AVAILABLE rows in KUB VAL"

    if 'image_path' in df.columns:
        acqs = df['image_path'].apply(derive_acquisition_type)
        results['unknown_acquisition_count'] = int((acqs == 'UNKNOWN').sum())
        results['no_unknown_acquisition'] = results['unknown_acquisition_count'] == 0
        assert results['no_unknown_acquisition'], f"Found {results['unknown_acquisition_count']} UNKNOWN acquisition types"

    results['all_pass'] = True
    return results


# ---------------------------------------------------------------------------
# VAL deterministic gallery selection
# ---------------------------------------------------------------------------

def get_val_manifest() -> pd.DataFrame:
    """Load KUB-only VAL manifest (phase4_v3). Hard-gated to 280 rows."""
    df = pd.read_csv(PROJECT_ROOT / 'manifests' / 'phase4_v3' / 'val.csv')
    kub_df = df[df['dataset'] == 'KUB'].copy()
    assert_phase09_kub_scope(kub_df)
    # Derive acquisition_type for stratification
    kub_df['acquisition_type'] = kub_df['image_path'].apply(derive_acquisition_type)
    return kub_df


def deterministic_val_gallery_selection(
    val_df: pd.DataFrame,
    n_cases: int = 16,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Deterministic, prediction-independent VAL gallery selection.
    Stratify by (category, acquisition_type) where possible.
    """
    need = ['sample_id', 'patient_id', 'category', 'acquisition_type']
    for c in need:
        if c not in val_df.columns:
            raise ValueError(f"VAL manifest missing column: {c}")

    df = val_df.copy()
    df['_sort_key'] = df['sample_id'].astype(str)
    df = df.sort_values('_sort_key').reset_index(drop=True)

    # Stratify by category + acquisition_type
    groups = df.groupby(['category', 'acquisition_type'], group_keys=False)
    selected = []

    # First, try to pick at least one from each group
    for _, grp in groups:
        if len(selected) >= n_cases:
            break
        selected.append(grp.iloc[0])

    # Fill remaining slots deterministically from the full sorted list
    selected_ids = {r['sample_id'] for r in selected}
    remaining = df[~df['sample_id'].isin(selected_ids)].copy()
    remaining = remaining.sample(n=min(len(remaining), n_cases - len(selected)),
                                 random_state=seed).sort_values('_sort_key')

    selected_df = pd.concat([pd.DataFrame(selected), remaining], ignore_index=True)
    selected_df = selected_df.head(n_cases).sort_values('_sort_key').reset_index(drop=True)

    # Add deterministic index
    selected_df['gallery_index'] = range(1, len(selected_df) + 1)
    return selected_df[['gallery_index', 'sample_id', 'patient_id', 'category',
                        'acquisition_type', 'image_path', 'mask_path']]


# ---------------------------------------------------------------------------
# Best-checkpoint inference model (VAL only)
# ---------------------------------------------------------------------------

def load_best_model_for_inference(device: str = 'cpu'):
    """Load best checkpoint model for inference. No training."""
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    from src.utils.device import get_device
    from src.models.unet import UNet

    ckpt = torch.load(BEST_PT, map_location='cpu', weights_only=False)
    cfg = ckpt['configuration']['model']
    model = UNet(
        in_channels=cfg['input_channels'],
        out_channels=cfg['output_channels'],
        base_channels=cfg.get('base_channels', 32),
    )
    model.load_state_dict(ckpt['model_state'])
    dev = get_device(require_cuda=(device != 'cpu'))
    model = model.to(dev)
    model.eval()
    return model, dev


def predict_on_val_sample(model, device, image_path: Path, target_size: int = 512) -> np.ndarray:
    """Run deterministic inference on a single image. Returns probability map [H, W]."""
    import torchvision.transforms as T
    img = Image.open(image_path).convert('L')
    w, h = img.size
    scale = min(target_size / w, target_size / h)
    new_w, new_h = int(w * scale), int(h * scale)
    img = img.resize((new_w, new_h), Image.BILINEAR)

    # Center pad
    pad_left = (target_size - new_w) // 2
    pad_top = (target_size - new_h) // 2
    pad_right = target_size - new_w - pad_left
    pad_bottom = target_size - new_h - pad_top

    arr = np.array(img, dtype=np.float32) / 255.0
    arr = np.pad(arr, ((pad_top, pad_bottom), (pad_left, pad_right)), mode='constant', constant_values=0)
    tensor = torch.from_numpy(arr).unsqueeze(0).unsqueeze(0).float().to(device)

    with torch.no_grad():
        with torch.amp.autocast('cuda', enabled=(device.type == 'cuda')):
            out = model(tensor)
        prob = torch.sigmoid(out).squeeze().cpu().numpy()

    # Crop back to original aspect ratio
    prob = prob[pad_top:pad_top + new_h, pad_left:pad_left + new_w]
    return prob, (new_w, new_h), (pad_left, pad_top)


# ---------------------------------------------------------------------------
# Notebook integrity summary
# ---------------------------------------------------------------------------

def full_integrity_summary() -> Dict[str, Any]:
    """Return a comprehensive integrity summary for the reviewer notebook."""
    df = load_history()
    hist_int = check_history_integrity(df)
    art = verify_artifact_shas()
    best_ck = check_best_checkpoint_consistency()
    latest_ck = check_latest_checkpoint_consistency()

    return {
        'experiment_id': EXPERIMENT_ID,
        'manifest_version': 'phase4_v3',
        'taxonomy_id': 'kub_size_clean_v3_v1',
        'config_sha': art['config_sha'],
        'history_sha': art['history_sha'],
        'best_checkpoint_sha': art['best_pt_sha'],
        'latest_checkpoint_sha': art['latest_pt_sha'],
        'best_epoch': hist_int['best_epoch'],
        'final_epoch': hist_int['final_epoch'],
        'stop_reason': 'EARLY_STOP',
        'history_integrity': hist_int,
        'artifact_shas': art,
        'best_checkpoint_consistency': best_ck,
        'latest_checkpoint_consistency': latest_ck,
        'overall_pass': hist_int['contiguous_epochs'] and hist_int['stop_consistent']
                        and art['all_pass'] and best_ck['all_pass'] and latest_ck['all_pass'],
    }


if __name__ == '__main__':
    # Quick self-test
    print('Phase09 Training Review (REPAIRED) — self-test')
    print('===============================================')
    art = verify_artifact_shas()
    print('Artifact SHA verification:', 'PASS' if art['all_pass'] else 'FAIL')
    hist = load_history()
    hi = check_history_integrity(hist)
    print('History integrity:', 'PASS' if hi['contiguous_epochs'] and hi['stop_consistent'] else 'FAIL')
    best_ck = check_best_checkpoint_consistency()
    print('Best checkpoint consistency:', 'PASS' if best_ck['all_pass'] else 'FAIL')
    latest_ck = check_latest_checkpoint_consistency()
    print('Latest checkpoint consistency:', 'PASS' if latest_ck['all_pass'] else 'FAIL')
    val_df = get_val_manifest()
    print(f'KUB VAL rows: {len(val_df)} — PASS' if len(val_df) == KUB_VAL_EXPECTED_ROWS else f'KUB VAL rows: {len(val_df)} — FAIL')
    print('KUB categories:', val_df['category'].value_counts().to_dict())
    print('Acquisition types:', val_df['acquisition_type'].value_counts().to_dict())
    gal = deterministic_val_gallery_selection(val_df, n_cases=16, seed=42)
    print(f'Gallery selection: {len(gal)} cases')
    print(gal[['gallery_index', 'category', 'acquisition_type']].to_string(index=False))
    print()
    print('All gates:', 'PASS' if (art['all_pass'] and hi['contiguous_epochs']
          and hi['stop_consistent'] and best_ck['all_pass'] and latest_ck['all_pass']
          and len(val_df) == KUB_VAL_EXPECTED_ROWS) else 'FAIL')
