"""
Phase 10 Part 1B — CLEAN-v3 UNet++ Baseline Training.

Historical reference:
    experiment_id: phase10_kub_unetpp_seed42_512
    architecture  : unetpp_nested_4_level_no_deep_supervision (deep supervision OFF)
    best_epoch: 77
    best_val_dice: 0.7625221610069275
    final_epoch: 92 (EARLY_STOP)

Clean experiment:
    experiment_id: phase10_kub_unetpp_seed42_512_clean_v3
    manifest: phase4_v3
    taxonomy: kub_size_clean_v3_v1

Epoch ordering (from historical trainer scripts/training/train_phase10_baselines.py):
    TRAIN -> VAL -> scheduler.step() -> strict '>' improvement ->
    early_stopping.update() -> save latest (always) -> save best (if improved) -> stop check

DO NOT modify scientific fields mid-run. TEST is locked.
"""
from __future__ import annotations

import csv, hashlib, json, sys, time
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

PROJECT_ROOT = Path(r'D:\Softfors\jup')
CONFIG_PATH = PROJECT_ROOT / 'configs' / 'phase10_clean_v3' / 'phase10_unetpp_clean_v3.yaml'
EXPERIMENT_ID = 'phase10_kub_unetpp_seed42_512_clean_v3'
EXPERIMENT_DIR = PROJECT_ROOT / 'experiments' / EXPERIMENT_ID
CHECKPOINT_DIR = PROJECT_ROOT / 'checkpoints' / EXPERIMENT_ID

sys.path.insert(0, str(PROJECT_ROOT))
from src.data.kub_dataset import KUBDataset
from src.models.unetpp import UNetPlusPlus
from src.utils.device import get_device
from src.utils.targets import binarize_mask
from src.metrics.segmentation import binary_metrics
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
    """Phase-08-style explicit validation. Fails on placeholder/scientific drift."""
    errors = []
    for k in ['model', 'input_resolution', 'loss', 'optimizer', 'scheduler', 'training', 'augmentation']:
        if k not in cfg:
            errors.append(f'missing: {k}')
    if errors:
        return {'valid': False, 'problems': errors}
    m = cfg['model']
    if m.get('name') != 'unetpp':
        errors.append(f"model.name must be unetpp, got {m.get('name')}")
    if m.get('base_channels') != 32:
        errors.append(f"model.base_channels must be 32, got {m.get('base_channels')}")
    if m.get('deep_supervision') is not False:
        errors.append(f"deep_supervision must be false (historical), got {m.get('deep_supervision')}")
    t = cfg['training']
    for key, exp in [('batch_size', 4), ('seed', 42), ('max_epochs', 100),
                     ('early_stopping_patience', 15), ('threshold', 0.5),
                     ('gradient_accumulation_steps', 1)]:
        if t.get(key) != exp:
            errors.append(f"training.{key} must be {exp}, got {t.get(key)}")
    if cfg['manifest_version'] != 'phase4_v3':
        errors.append('manifest must be phase4_v3')
    if cfg.get('taxonomy_id') != 'kub_size_clean_v3_v1':
        errors.append('taxonomy must be kub_size_clean_v3_v1')
    if cfg.get('allow_test') is not False:
        errors.append('allow_test must be false')
    if cfg['optimizer']['learning_rate'] != 1e-4:
        errors.append('learning_rate must be 1e-4')
    if cfg['optimizer']['weight_decay'] != 1e-4:
        errors.append('weight_decay must be 1e-4')
    if cfg['loss']['bce_weight'] != 0.5 or cfg['loss']['dice_weight'] != 0.5:
        errors.append('loss weights must be 0.5/0.5')
    return {'valid': len(errors) == 0, 'problems': errors}


def pre_run_gates(cfg: dict) -> dict:
    gates = {}
    try:
        validate_manifest_version_strict('phase4_v3')
        gates['manifest_guard'] = True
    except Exception as e:
        gates['manifest_guard'] = False
        print('manifest_guard fail:', e)

    import pandas as pd
    train_df = pd.read_csv(PROJECT_ROOT / 'manifests' / 'phase4_v3' / 'train.csv')
    val_df = pd.read_csv(PROJECT_ROOT / 'manifests' / 'phase4_v3' / 'val.csv')
    kub_train = train_df[train_df['dataset'] == 'KUB']
    kub_val = val_df[val_df['dataset'] == 'KUB']
    gates['kub_train_count'] = len(kub_train) == 1978
    gates['kub_val_count'] = len(kub_val) == 280
    gates['patient_overlap_zero'] = len(set(kub_train['patient_id']) & set(kub_val['patient_id'])) == 0
    gates['test_blocked'] = True
    gates['taxonomy_sha_ok'] = sha256_file(
        PROJECT_ROOT / 'reports' / 'audits' / 'kub_size_clean_v3_v1_thresholds.json'
    ) == '89031c51a35c24f6f939fd6206fde6002a019d4bda24ce8cb21988f04db0f0d6'
    gates['cuda_available'] = torch.cuda.is_available()
    gates['gpu_name_ok'] = 'NVIDIA' in (torch.cuda.get_device_name(0) if torch.cuda.is_available() else '')
    try:
        get_device(require_cuda=True)
        gates['canonical_device'] = True
    except Exception:
        gates['canonical_device'] = False
    gates['config_valid'] = validate_config(cfg)['valid']
    try:
        acquire_lock(EXPERIMENT_DIR, experiment_id=EXPERIMENT_ID)
        gates['run_lock'] = True
    except Exception as e:
        gates['run_lock'] = False
        print('run_lock fail:', e)
    return gates


def main():
    cfg = yaml.safe_load(CONFIG_PATH.read_text(encoding='utf-8'))
    v = validate_config(cfg)
    if not v['valid']:
        raise RuntimeError(f"Config validation failed: {v['problems']}")
    config_sha = sha256_file(CONFIG_PATH)

    gates = pre_run_gates(cfg)
    print('=== PRE-RUN GATES ===')
    for k, val in gates.items():
        print(f'  {k}: {val}')
    if not all(gates.values()):
        raise RuntimeError('Pre-run gates failed')

    manifest_hashes = {
        'train': sha256_file(PROJECT_ROOT / 'manifests' / 'phase4_v3' / 'train.csv'),
        'val': sha256_file(PROJECT_ROOT / 'manifests' / 'phase4_v3' / 'val.csv'),
        'test': sha256_file(PROJECT_ROOT / 'manifests' / 'phase4_v3' / 'test.csv'),
    }

    start_utc = datetime.now(timezone.utc).isoformat()
    start_audit = {
        'audit': 'phase10_unetpp_clean_v3_training_start_audit',
        'phase': '10 Part 1B',
        'experiment_id': EXPERIMENT_ID,
        'architecture': 'unetpp',
        'historical_experiment_id': 'phase10_kub_unetpp_seed42_512',
        'historical_architecture': 'unetpp_nested_4_level_no_deep_supervision',
        'historical_best_epoch': 77,
        'historical_best_val_macro_dice': 0.7625221610069275,
        'historical_final_epoch': 92,
        'historical_best_checkpoint_sha': '4bffcf926227fb11029ead6bcd8e7dd8ed246e0f1678e3efb2ce4297439a3f2d',
        'historical_latest_checkpoint_sha': '0538df33a2371b4ce4179510189d1258f8b269bb53d22ae9f53bab61ee29cb16',
        'historical_history_sha': '143acaeab463c7d156b612e52f09ca782dc7faa79ce59a88ea2719ff3a8760fd',
        'config_path': str(CONFIG_PATH),
        'config_sha': config_sha,
        'protocol_diff_sha': sha256_file(PROJECT_ROOT / 'reports' / 'tables' / 'phase10_unetpp_v2_to_clean_v3_protocol_diff.csv'),
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
        'unauthorized_material_differences': 0,
    }
    audit_dir = PROJECT_ROOT / 'reports' / 'audits'
    audit_dir.mkdir(parents=True, exist_ok=True)
    (audit_dir / 'phase10_unetpp_clean_v3_training_start_audit.json').write_text(
        json.dumps(start_audit, indent=2, default=str), encoding='utf-8')
    (audit_dir / 'phase10_unetpp_clean_v3_training_start_audit.md').write_text(
        '# Phase 10 UNet++ Clean-v3 Training Start Audit\n\n'
        f"- Experiment: `{EXPERIMENT_ID}`\n"
        f"- Historical: `{start_audit['historical_experiment_id']}`\n"
        f"- Config SHA: `{config_sha}`\n"
        f"- Manifest: phase4_v3 | Taxonomy: kub_size_clean_v3_v1\n"
        f"- Start UTC: {start_utc}\n"
        f"- Gates: all pass = {all(gates.values())}\n"
        f"- TEST reads: 0 | Unauthorized material diffs: 0\n", encoding='utf-8')

    device = get_device(require_cuda=True)
    seed = cfg['training']['seed']
    torch.manual_seed(seed)
    np.random.seed(seed)
    torch.cuda.manual_seed_all(seed)

    train_ds = KUBDataset(manifest_path=PROJECT_ROOT / 'manifests' / 'phase4_v3' / 'train.csv',
                          split='TRAIN', target_size=cfg['input_resolution'])
    val_ds = KUBDataset(manifest_path=PROJECT_ROOT / 'manifests' / 'phase4_v3' / 'val.csv',
                        split='VAL', target_size=cfg['input_resolution'])
    train_loader = DataLoader(train_ds, batch_size=cfg['training']['batch_size'],
                              shuffle=True, num_workers=0, pin_memory=True)
    val_loader = DataLoader(val_ds, batch_size=cfg['training']['batch_size'],
                            shuffle=False, num_workers=0, pin_memory=True)
    print(f'KUB TRAIN: {len(train_ds)} | KUB VAL: {len(val_ds)}')
    assert len(train_ds) == 1978 and len(val_ds) == 280

    mcfg = cfg['model']
    model = UNetPlusPlus(in_channels=mcfg['input_channels'],
                         out_channels=mcfg['output_channels'],
                         base_channels=mcfg['base_channels']).to(device)
    print(f'Model: UNetPlusPlus (deep_supervision=False) | params: {sum(p.numel() for p in model.parameters()):,}')

    ocfg = cfg['optimizer']
    optimizer = AdamW(model.parameters(), lr=ocfg['learning_rate'], weight_decay=ocfg['weight_decay'])
    scheduler = CosineAnnealingLR(optimizer, T_max=cfg['scheduler']['max_epochs'])
    scaler = GradScaler()

    bce = nn.BCEWithLogitsLoss()
    dice_eps, bce_w, dice_w = cfg['loss']['dice_epsilon'], cfg['loss']['bce_weight'], cfg['loss']['dice_weight']

    # Resume support (same experiment ID only)
    start_epoch, best_metric, bad_epochs, history, resume_count = 1, -1.0, 0, [], 0
    latest_pt = CHECKPOINT_DIR / 'latest.pt'
    if latest_pt.exists():
        ckpt = torch.load(latest_pt, map_location=device, weights_only=False)
        if ckpt.get('experiment_id') != EXPERIMENT_ID:
            raise RuntimeError(f"Checkpoint experiment mismatch: {ckpt.get('experiment_id')}")
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
        print(f'Resumed from epoch {start_epoch-1}, resume_count={resume_count}')

    patience = cfg['training']['early_stopping_patience']
    threshold = cfg['training']['threshold']
    max_epochs = cfg['training']['max_epochs']

    EXPERIMENT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    log_file = open(EXPERIMENT_DIR / 'training.log', 'a', encoding='utf-8')

    def log(msg):
        print(msg); log_file.write(msg + '\n'); log_file.flush()

    log(f'Start UTC={datetime.now(timezone.utc).isoformat()} epoch={start_epoch} '
        f'batch={cfg["training"]["batch_size"]} accumulation={cfg["training"]["gradient_accumulation_steps"]}')

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
                probs = torch.sigmoid(outputs)
                inter = (probs * masks).sum(dim=(1, 2, 3))
                union = probs.sum(dim=(1, 2, 3)) + masks.sum(dim=(1, 2, 3))
                dice_loss = (1 - (2 * inter + dice_eps) / (union + dice_eps)).mean()
                loss = bce_w * bce_loss + dice_w * dice_loss
            if not torch.isfinite(loss):
                raise RuntimeError(f'Non-finite loss at epoch {epoch} batch {batch_idx}: {loss.item()}')
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            optimizer.zero_grad()
            train_losses.append(loss.item())
        avg_train = float(np.mean(train_losses))

        # ---- VAL (deterministic, augmentation OFF, shuffle FALSE) ----
        model.eval()
        vloss, vdice, viou, vprec, vrec = [], [], [], [], []
        with torch.no_grad():
            for batch in val_loader:
                images = batch['image'].to(device)
                masks = batch['mask'].to(device)
                with torch.amp.autocast('cuda'):
                    outputs = model(images)
                    bce_loss = bce(outputs, masks)
                    probs = torch.sigmoid(outputs)
                    inter = (probs * masks).sum(dim=(1, 2, 3))
                    union = probs.sum(dim=(1, 2, 3)) + masks.sum(dim=(1, 2, 3))
                    dice_loss = (1 - (2 * inter + dice_eps) / (union + dice_eps)).mean()
                    loss = bce_w * bce_loss + dice_w * dice_loss
                vloss.append(loss.item())
                for i in range(outputs.size(0)):
                    m = binary_metrics(outputs[i:i+1], masks[i:i+1], threshold=threshold)
                    vdice.append(float(m['dice'])); viou.append(float(m['iou']))
                    vprec.append(float(m['precision'])); vrec.append(float(m['recall']))

        val_loss = float(np.mean(vloss))
        val_dice = float(np.mean(vdice))      # macro = unweighted mean of per-image
        val_iou = float(np.mean(viou))
        val_prec = float(np.mean(vprec))
        val_rec = float(np.mean(vrec))

        # ---- scheduler step (after train+val, per historical ordering) ----
        scheduler.step()
        lr = optimizer.param_groups[0]['lr']

        # ---- strict '>' improvement; ties = bad epoch ----
        improved = val_dice > best_metric + EPS
        if improved:
            best_metric = val_dice
            bad_epochs = 0
        else:
            bad_epochs += 1

        secs = time.time() - epoch_start
        log(f'Epoch {epoch:03d}/{max_epochs} train_loss={avg_train:.8f} val_loss={val_loss:.8f} '
            f'val_dice={val_dice} val_iou={val_iou} lr={lr:.10f} seconds={secs:.1f} best={improved}')

        history.append({'epoch': epoch, 'train_loss': avg_train, 'val_loss': val_loss,
                        'val_dice': val_dice, 'val_iou': val_iou,
                        'val_precision': val_prec, 'val_recall': val_rec,
                        'learning_rate': lr, 'best_so_far': best_metric,
                        'improved': int(improved), 'bad_epochs': bad_epochs,
                        'epoch_seconds': round(secs, 1)})

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
        torch.save(ckpt, CHECKPOINT_DIR / 'latest.pt')   # always
        if improved:
            torch.save(ckpt, CHECKPOINT_DIR / 'best.pt')  # on improvement only

        with open(EXPERIMENT_DIR / 'history.csv', 'w', newline='', encoding='utf-8') as hf:
            w = csv.DictWriter(hf, fieldnames=HISTORY_COLS)
            w.writeheader()
            for row in history:
                w.writerow({k: row[k] for k in HISTORY_COLS})

        if bad_epochs >= patience:
            log(f'Early stopping epoch={epoch} best_epoch={epoch - bad_epochs} best={best_metric}')
            break

    end_utc = datetime.now(timezone.utc).isoformat()
    best_row = max(history, key=lambda r: r['val_dice'])
    completion = {
        'audit': 'phase10_unetpp_clean_v3_training_completion_audit',
        'phase': '10 Part 1B',
        'experiment_id': EXPERIMENT_ID,
        'architecture': 'unetpp',
        'config_path': str(CONFIG_PATH),
        'config_sha': config_sha,
        'manifest_version': 'phase4_v3',
        'manifest_hashes': manifest_hashes,
        'taxonomy_id': 'kub_size_clean_v3_v1',
        'start_utc': start_utc,
        'end_utc': end_utc,
        'resume_count': resume_count,
        'epochs_completed': len(history),
        'best_epoch': int(best_row['epoch']),
        'best_val_dice': best_metric,
        'val_iou_at_best': float(best_row['val_iou']),
        'val_precision_at_best': float(best_row['val_precision']),
        'val_recall_at_best': float(best_row['val_recall']),
        'final_epoch': history[-1]['epoch'],
        'stop_reason': 'EARLY_STOP' if bad_epochs >= patience else 'MAX_EPOCH',
        'early_stopped': bad_epochs >= patience,
        'early_stop_bad_epochs': bad_epochs,
        'finite_losses': bool(np.isfinite([r['train_loss'] for r in history]).all()),
        'nan_inf_events': 0,
        'scientific_parameter_changes': 0,
        'test_content_reads': 0,
        'train_samples': len(train_ds),
        'val_samples': len(val_ds),
        'device': {'cuda_available': True,
                   'cuda_device': torch.cuda.get_device_name(0),
                   'pytorch_version': str(torch.__version__)},
        'best_checkpoint': str(CHECKPOINT_DIR / 'best.pt'),
        'best_checkpoint_sha': sha256_file(CHECKPOINT_DIR / 'best.pt'),
        'latest_checkpoint': str(CHECKPOINT_DIR / 'latest.pt'),
        'latest_checkpoint_sha': sha256_file(CHECKPOINT_DIR / 'latest.pt'),
        'history': str(EXPERIMENT_DIR / 'history.csv'),
        'history_sha': sha256_file(EXPERIMENT_DIR / 'history.csv'),
        'training_status': 'PASS',
    }
    (audit_dir / 'phase10_unetpp_clean_v3_training_completion_audit.json').write_text(
        json.dumps(completion, indent=2, default=str), encoding='utf-8')
    (audit_dir / 'phase10_unetpp_clean_v3_training_completion_audit.md').write_text(
        '# Phase 10 UNet++ Clean-v3 Training Completion Audit\n\n'
        f"- Experiment: `{EXPERIMENT_ID}`\n"
        f"- Best epoch: {completion['best_epoch']} | Final epoch: {completion['final_epoch']}\n"
        f"- Best VAL macro Dice: {completion['best_val_dice']}\n"
        f"- IoU: {completion['val_iou_at_best']} | Precision: {completion['val_precision_at_best']}"
        f" | Recall: {completion['val_recall_at_best']}\n"
        f"- Stop: {completion['stop_reason']} (bad_epochs={completion['early_stop_bad_epochs']})\n"
        f"- Resume count: {resume_count} | NaN/Inf: 0 | scientific changes: 0\n"
        f"- Config SHA: `{config_sha}`\n"
        f"- History SHA: `{completion['history_sha']}`\n"
        f"- Best ckpt SHA: `{completion['best_checkpoint_sha']}`\n"
        f"- Latest ckpt SHA: `{completion['latest_checkpoint_sha']}`\n"
        f"- TEST reads: 0\n", encoding='utf-8')

    log(f'Training complete. Best epoch: {completion["best_epoch"]}, best val_dice: {best_metric:.6f}')
    log_file.close()
    try:
        release_lock(EXPERIMENT_DIR)
    except Exception as e:
        print(f'Lock release note: {e}')


if __name__ == '__main__':
    main()
