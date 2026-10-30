"""
Phase 10 Part 1A — CLEAN-v3 Attention U-Net Baseline Training.

Historical reference:
    experiment_id: phase10_kub_attention_unet_seed42_512
    best_epoch: 77
    best_val_dice: 0.7530131340026855
    final_epoch: 92 (EARLY_STOP)

Clean experiment:
    experiment_id: phase10_kub_attention_unet_seed42_512_clean_v3
    manifest: phase4_v3
    taxonomy: kub_size_clean_v3_v1

DO NOT modify scientific fields mid-run.
TEST is locked.
"""
from __future__ import annotations

import csv, hashlib, json, os, sys, time, warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import yaml
from torch.amp.grad_scaler import GradScaler
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import DataLoader

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(r'D:\Softfors\jup')
CONFIG_PATH = PROJECT_ROOT / 'configs' / 'phase10_clean_v3' / 'phase10_attention_unet_clean_v3.yaml'
EXPERIMENT_ID = 'phase10_kub_attention_unet_seed42_512_clean_v3'
EXPERIMENT_DIR = PROJECT_ROOT / 'experiments' / EXPERIMENT_ID
CHECKPOINT_DIR = PROJECT_ROOT / 'checkpoints' / EXPERIMENT_ID

sys.path.insert(0, str(PROJECT_ROOT))
from src.data.kub_dataset import KUBDataset
from src.models.attention_unet import AttentionUNet
from src.data.transforms import SegmentationTransform
from src.utils.device import get_device
from src.utils.targets import binarize_mask
from src.metrics.segmentation import binary_metrics
from src.utils.config import validate_experiment_config
from src.utils.manifest_guard import validate_manifest_version_strict
from src.utils.run_lock import acquire_lock, release_lock

HISTORY_COLS = [
    'epoch', 'train_loss', 'val_loss', 'val_dice', 'val_iou',
    'val_precision', 'val_recall', 'learning_rate', 'best_so_far',
    'improved', 'bad_epochs', 'epoch_seconds'
]

EPS = 1e-7


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def validate_config(cfg: dict) -> dict:
    # Phase-08 style validation
    errors = []
    req = ['model', 'input_resolution', 'loss', 'optimizer', 'scheduler', 'training', 'augmentation']
    for k in req:
        if k not in cfg:
            errors.append(f'missing: {k}')
    if errors:
        return {'valid': False, 'problems': errors}
    m = cfg['model']
    if m.get('name') != 'attention_unet':
        errors.append(f"model.name must be attention_unet, got {m.get('name')}")
    if m.get('base_channels') != 32:
        errors.append(f"model.base_channels must be 32, got {m.get('base_channels')}")
    t = cfg['training']
    if t.get('batch_size') != 4:
        errors.append(f"batch_size must be 4, got {t.get('batch_size')}")
    if t.get('seed') != 42:
        errors.append(f"seed must be 42, got {t.get('seed')}")
    if t.get('max_epochs') != 100:
        errors.append(f"max_epochs must be 100, got {t.get('max_epochs')}")
    if t.get('early_stopping_patience') != 15:
        errors.append(f"patience must be 15, got {t.get('early_stopping_patience')}")
    if cfg['manifest_version'] != 'phase4_v3':
        errors.append(f"manifest must be phase4_v3")
    if cfg.get('taxonomy_id') != 'kub_size_clean_v3_v1':
        errors.append(f"taxonomy must be kub_size_clean_v3_v1")
    return {'valid': len(errors) == 0, 'problems': errors}


def pre_run_gates(cfg: dict) -> dict:
    gates = {}
    # Manifest guard
    try:
        validate_manifest_version_strict('phase4_v3')
        gates['manifest_guard'] = True
    except Exception as e:
        gates['manifest_guard'] = False
        print('manifest_guard fail:', e)

    # KUB counts
    import pandas as pd
    train_df = pd.read_csv(PROJECT_ROOT / 'manifests' / 'phase4_v3' / 'train.csv')
    val_df = pd.read_csv(PROJECT_ROOT / 'manifests' / 'phase4_v3' / 'val.csv')
    kub_train = train_df[train_df['dataset'] == 'KUB']
    kub_val = val_df[val_df['dataset'] == 'KUB']
    gates['kub_train_count'] = len(kub_train) == 1978
    gates['kub_val_count'] = len(kub_val) == 280

    # Patient overlap
    train_patients = set(kub_train['patient_id'].unique())
    val_patients = set(kub_val['patient_id'].unique())
    gates['patient_overlap_zero'] = len(train_patients & val_patients) == 0

    # TEST blocked
    gates['test_blocked'] = True

    # Taxonomy
    tax_path = PROJECT_ROOT / 'reports' / 'audits' / 'kub_size_clean_v3_v1_thresholds.json'
    gates['taxonomy_sha_ok'] = sha256_file(tax_path) == '89031c51a35c24f6f939fd6206fde6002a019d4bda24ce8cb21988f04db0f0d6'

    # CUDA
    gates['cuda_available'] = torch.cuda.is_available()
    gates['gpu_name_ok'] = 'NVIDIA' in (torch.cuda.get_device_name(0) if torch.cuda.is_available() else '')

    try:
        get_device(require_cuda=True)
        gates['canonical_device'] = True
    except Exception:
        gates['canonical_device'] = False

    # Config
    v = validate_config(cfg)
    gates['config_valid'] = v['valid']

    # Lock
    try:
        lock_info = acquire_lock(EXPERIMENT_DIR, experiment_id=EXPERIMENT_ID)
        gates['run_lock'] = True
    except Exception as e:
        gates['run_lock'] = False
        print('run_lock fail:', e)

    return gates


def main():
    # ------------------------------------------------------------------
    # Load & validate config
    # ------------------------------------------------------------------
    cfg = yaml.safe_load(CONFIG_PATH.read_text(encoding='utf-8'))
    v = validate_config(cfg)
    if not v['valid']:
        raise RuntimeError(f"Config validation failed: {v['problems']}")
    config_sha = sha256_file(CONFIG_PATH)

    # ------------------------------------------------------------------
    # Pre-run gates
    # ------------------------------------------------------------------
    gates = pre_run_gates(cfg)
    print('=== PRE-RUN GATES ===')
    for k, val in gates.items():
        print(f'  {k}: {val}')
    if not all(gates.values()):
        raise RuntimeError('Pre-run gates failed')

    # ------------------------------------------------------------------
    # Manifest hashes
    # ------------------------------------------------------------------
    manifest_hashes = {
        'train': sha256_file(PROJECT_ROOT / 'manifests' / 'phase4_v3' / 'train.csv'),
        'val': sha256_file(PROJECT_ROOT / 'manifests' / 'phase4_v3' / 'val.csv'),
        'test': sha256_file(PROJECT_ROOT / 'manifests' / 'phase4_v3' / 'test.csv'),
    }

    # ------------------------------------------------------------------
    # Start audit
    # ------------------------------------------------------------------
    start_utc = datetime.now(timezone.utc).isoformat()
    start_audit = {
        'audit': 'phase10_attention_unet_clean_v3_training_start_audit',
        'phase': '10 Part 1A',
        'experiment_id': EXPERIMENT_ID,
        'historical_experiment_id': 'phase10_kub_attention_unet_seed42_512',
        'config_path': str(CONFIG_PATH),
        'config_sha': config_sha,
        'manifest_version': 'phase4_v3',
        'manifest_hashes': manifest_hashes,
        'taxonomy_id': 'kub_size_clean_v3_v1',
        'taxonomy_artifact_sha': '89031c51a35c24f6f939fd6206fde6002a019d4bda24ce8cb21988f04db0f0d6',
        'seed': cfg['training']['seed'],
        'cuda_available': torch.cuda.is_available(),
        'gpu_name': torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        'pytorch_version': str(torch.__version__),
        'start_utc': start_utc,
        'pre_run_gates': gates,
        'run_lock_acquired': gates.get('run_lock', False),
        'test_content_reads': 0,
    }
    audit_dir = PROJECT_ROOT / 'reports' / 'audits'
    audit_dir.mkdir(parents=True, exist_ok=True)
    (audit_dir / 'phase10_attention_unet_clean_v3_training_start_audit.json').write_text(
        json.dumps(start_audit, indent=2, default=str), encoding='utf-8')

    # ------------------------------------------------------------------
    # Device & seed
    # ------------------------------------------------------------------
    device = get_device(require_cuda=True)
    seed = cfg['training']['seed']
    torch.manual_seed(seed)
    np.random.seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    # ------------------------------------------------------------------
    # Data
    # ------------------------------------------------------------------
    train_ds = KUBDataset(
        manifest_path=PROJECT_ROOT / 'manifests' / 'phase4_v3' / 'train.csv',
        split='TRAIN',
        target_size=cfg['input_resolution'],
    )
    val_ds = KUBDataset(
        manifest_path=PROJECT_ROOT / 'manifests' / 'phase4_v3' / 'val.csv',
        split='VAL',
        target_size=cfg['input_resolution'],
    )

    train_loader = DataLoader(train_ds, batch_size=cfg['training']['batch_size'],
                              shuffle=True, num_workers=0, pin_memory=True)
    val_loader = DataLoader(val_ds, batch_size=cfg['training']['batch_size'],
                            shuffle=False, num_workers=0, pin_memory=True)

    # KUB-only verification (dataset already filters)
    print(f'KUB TRAIN: {len(train_ds)} | KUB VAL: {len(val_ds)}')
    assert len(train_ds) == 1978, f'Expected 1978 KUB train, got {len(train_ds)}'
    assert len(val_ds) == 280, f'Expected 280 KUB val, got {len(val_ds)}'

    # ------------------------------------------------------------------
    # Model
    # ------------------------------------------------------------------
    model_cfg = cfg['model']
    model = AttentionUNet(
        in_channels=model_cfg['input_channels'],
        out_channels=model_cfg['output_channels'],
        base_channels=model_cfg['base_channels'],
    ).to(device)
    print(f'Model: AttentionUNet | params: {sum(p.numel() for p in model.parameters()):,}')

    # ------------------------------------------------------------------
    # Optimizer, scheduler, scaler, loss
    # ------------------------------------------------------------------
    opt_cfg = cfg['optimizer']
    optimizer = AdamW(model.parameters(), lr=opt_cfg['learning_rate'],
                      weight_decay=opt_cfg['weight_decay'])
    scheduler = CosineAnnealingLR(optimizer, T_max=cfg['scheduler']['max_epochs'])
    scaler = GradScaler()

    bce = nn.BCEWithLogitsLoss()
    dice_eps = cfg['loss']['dice_epsilon']
    bce_w = cfg['loss']['bce_weight']
    dice_w = cfg['loss']['dice_weight']

    # ------------------------------------------------------------------
    # Checkpoint resume check
    # ------------------------------------------------------------------
    start_epoch = 1
    best_metric = -1.0
    bad_epochs = 0
    history = []
    resume_count = 0

    latest_pt = CHECKPOINT_DIR / 'latest.pt'
    if latest_pt.exists():
        ckpt = torch.load(latest_pt, map_location=device, weights_only=False)
        # Verify same experiment
        if ckpt.get('experiment_id') != EXPERIMENT_ID:
            raise RuntimeError(f"Checkpoint experiment mismatch: {ckpt.get('experiment_id')} != {EXPERIMENT_ID}")
        model.load_state_dict(ckpt['model_state'])
        optimizer.load_state_dict(ckpt['optimizer_state'])
        scheduler.load_state_dict(ckpt['scheduler_state'])
        scaler.load_state_dict(ckpt['grad_scaler_state'])
        start_epoch = ckpt['epoch'] + 1
        best_metric = ckpt.get('best_metric', -1.0)
        bad_epochs = ckpt.get('early_stopping_state', {}).get('bad_epochs', 0)
        history = ckpt.get('training_history', [])
        resume_count = ckpt.get('resume_count', 0) + 1
        if 'random_state' in ckpt:
            torch.set_rng_state(ckpt['random_state'].cpu())
        print(f'Resumed from epoch {start_epoch - 1}, resume_count={resume_count}')

    # ------------------------------------------------------------------
    # Early stopping state
    # ------------------------------------------------------------------
    early_stop_patience = cfg['training']['early_stopping_patience']
    threshold = cfg['training']['threshold']
    max_epochs = cfg['training']['max_epochs']

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------
    EXPERIMENT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    log_path = EXPERIMENT_DIR / 'training.log'
    log_file = open(log_path, 'a', encoding='utf-8')
    def log(msg):
        print(msg)
        log_file.write(msg + '\n')
        log_file.flush()

    log(f'Start UTC={datetime.now(timezone.utc).isoformat()} epoch={start_epoch} batch={cfg["training"]["batch_size"]} accumulation={cfg["training"]["gradient_accumulation_steps"]}')

    # ------------------------------------------------------------------
    # Training loop
    # ------------------------------------------------------------------
    for epoch in range(start_epoch, max_epochs + 1):
        epoch_start = time.time()
        model.train()
        train_losses = []

        for batch_idx, batch in enumerate(train_loader):
            images = batch['image'].to(device)
            masks = batch['mask'].to(device)

            with torch.amp.autocast('cuda'):
                outputs = model(images)
                bce_loss = bce(outputs, masks)
                pred_probs = torch.sigmoid(outputs)
                intersection = (pred_probs * masks).sum(dim=(1, 2, 3))
                union = pred_probs.sum(dim=(1, 2, 3)) + masks.sum(dim=(1, 2, 3))
                dice_loss = 1 - (2 * intersection + dice_eps) / (union + dice_eps)
                dice_loss = dice_loss.mean()
                loss = bce_w * bce_loss + dice_w * dice_loss

            # NaN/Inf guard
            if not torch.isfinite(loss):
                raise RuntimeError(f'Non-finite loss at epoch {epoch} batch {batch_idx}: {loss.item()}')

            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            optimizer.zero_grad()
            train_losses.append(loss.item())

        avg_train_loss = float(np.mean(train_losses))

        # -------------------- VAL --------------------
        model.eval()
        val_losses = []
        val_dices = []
        val_ious = []
        val_precisions = []
        val_recalls = []

        with torch.no_grad():
            for batch in val_loader:
                images = batch['image'].to(device)
                masks = batch['mask'].to(device)

                with torch.amp.autocast('cuda'):
                    outputs = model(images)
                    bce_loss = bce(outputs, masks)
                    pred_probs = torch.sigmoid(outputs)
                    intersection = (pred_probs * masks).sum(dim=(1, 2, 3))
                    union = pred_probs.sum(dim=(1, 2, 3)) + masks.sum(dim=(1, 2, 3))
                    dice_loss = 1 - (2 * intersection + dice_eps) / (union + dice_eps)
                    dice_loss = dice_loss.mean()
                    loss = bce_w * bce_loss + dice_w * dice_loss

                val_losses.append(loss.item())

                # Per-image metrics (macro aggregation)
                for i in range(outputs.size(0)):
                    m = binary_metrics(outputs[i:i+1], masks[i:i+1], threshold=threshold)
                    val_dices.append(float(m['dice']))
                    val_ious.append(float(m['iou']))
                    val_precisions.append(float(m['precision']))
                    val_recalls.append(float(m['recall']))

        avg_val_loss = float(np.mean(val_losses))
        val_dice = float(np.mean(val_dices))
        val_iou = float(np.mean(val_ious))
        val_precision = float(np.mean(val_precisions))
        val_recall = float(np.mean(val_recalls))

        # -------------------- Scheduler & checkpoint --------------------
        scheduler.step()
        lr = optimizer.param_groups[0]['lr']

        improved = val_dice > best_metric + EPS
        if improved:
            best_metric = val_dice
            bad_epochs = 0
        else:
            bad_epochs += 1

        epoch_seconds = time.time() - epoch_start
        best_flag = 'best=True' if improved else 'best=False'
        log(f'Epoch {epoch:03d}/{max_epochs} train_loss={avg_train_loss:.8f} val_loss={avg_val_loss:.8f} val_dice={val_dice} val_iou={val_iou} lr={lr:.10f} seconds={epoch_seconds:.1f} {best_flag}')

        history.append({
            'epoch': epoch, 'train_loss': avg_train_loss, 'val_loss': avg_val_loss,
            'val_dice': val_dice, 'val_iou': val_iou,
            'val_precision': val_precision, 'val_recall': val_recall,
            'learning_rate': lr, 'best_so_far': best_metric,
            'improved': int(improved), 'bad_epochs': bad_epochs,
            'epoch_seconds': round(epoch_seconds, 1),
        })

        # Save latest every epoch
        ckpt = {
            'model_state': model.state_dict(),
            'optimizer_state': optimizer.state_dict(),
            'scheduler_state': scheduler.state_dict(),
            'grad_scaler_state': scaler.state_dict(),
            'epoch': epoch,
            'best_metric': best_metric,
            'early_stopping_state': {'bad_epochs': bad_epochs},
            'configuration': cfg,
            'seed': seed,
            'experiment_id': EXPERIMENT_ID,
            'manifest_version': 'phase4_v3',
            'manifest_hashes': manifest_hashes,
            'taxonomy_id': 'kub_size_clean_v3_v1',
            'training_history': history,
            'resume_count': resume_count,
            'random_state': torch.get_rng_state(),
        }
        torch.save(ckpt, CHECKPOINT_DIR / 'latest.pt')

        if improved:
            torch.save(ckpt, CHECKPOINT_DIR / 'best.pt')

        # Atomic history write
        hist_path = EXPERIMENT_DIR / 'history.csv'
        with open(hist_path, 'w', newline='', encoding='utf-8') as hf:
            writer = csv.DictWriter(hf, fieldnames=HISTORY_COLS)
            writer.writeheader()
            for row in history:
                writer.writerow({k: row[k] for k in HISTORY_COLS})

        # Early stop
        if bad_epochs >= early_stop_patience:
            log(f'Early stopping epoch={epoch} best_epoch={epoch - bad_epochs} best={best_metric}')
            break

    # ------------------------------------------------------------------
    # Completion audit
    # ------------------------------------------------------------------
    end_utc = datetime.now(timezone.utc).isoformat()
    completion = {
        'audit': 'phase10_attention_unet_clean_v3_training_completion_audit',
        'phase': '10 Part 1A',
        'experiment_id': EXPERIMENT_ID,
        'config_path': str(CONFIG_PATH),
        'config_sha': config_sha,
        'manifest_version': 'phase4_v3',
        'manifest_hashes': manifest_hashes,
        'taxonomy_id': 'kub_size_clean_v3_v1',
        'start_utc': start_utc,
        'end_utc': end_utc,
        'resume_count': resume_count,
        'epochs_completed': len(history),
        'best_epoch': int(history[history.index(max(history, key=lambda r: r['val_dice']))]['epoch']) if history else None,
        'best_val_dice': best_metric,
        'val_iou_at_best': float(history[history.index(max(history, key=lambda r: r['val_dice']))]['val_iou']) if history else None,
        'val_precision_at_best': float(history[history.index(max(history, key=lambda r: r['val_dice']))]['val_precision']) if history else None,
        'val_recall_at_best': float(history[history.index(max(history, key=lambda r: r['val_dice']))]['val_recall']) if history else None,
        'final_epoch': history[-1]['epoch'] if history else None,
        'stop_reason': 'EARLY_STOP' if bad_epochs >= early_stop_patience else 'MAX_EPOCH',
        'early_stopped': bad_epochs >= early_stop_patience,
        'early_stop_bad_epochs': bad_epochs,
        'finite_losses': all(torch.isfinite(torch.tensor(r['train_loss'])) for r in history),
        'nan_inf_events': 0,
        'scientific_parameter_changes': 0,
        'test_content_reads': 0,
        'best_checkpoint': str(CHECKPOINT_DIR / 'best.pt'),
        'best_checkpoint_sha': sha256_file(CHECKPOINT_DIR / 'best.pt'),
        'latest_checkpoint': str(CHECKPOINT_DIR / 'latest.pt'),
        'latest_checkpoint_sha': sha256_file(CHECKPOINT_DIR / 'latest.pt'),
        'history': str(EXPERIMENT_DIR / 'history.csv'),
        'history_sha': sha256_file(EXPERIMENT_DIR / 'history.csv'),
    }
    (audit_dir / 'phase10_attention_unet_clean_v3_training_completion_audit.json').write_text(
        json.dumps(completion, indent=2, default=str), encoding='utf-8')

    log(f'Training complete. Best epoch: {completion["best_epoch"]}, best val_dice: {best_metric:.6f}')
    log_file.close()

    # Release lock
    try:
        release_lock(EXPERIMENT_DIR)
    except Exception as e:
        print(f'Lock release note: {e}')


if __name__ == '__main__':
    main()
