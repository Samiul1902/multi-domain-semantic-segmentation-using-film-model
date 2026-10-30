"""
Phase 09 Part 1A — CLEAN-v3 KUB UNet baseline training.

Authorized single-model clean-v3 rerun of the historical Phase-09 UNet baseline.

Scientific protocol is FROZEN (see configs/phase09_clean_v3/phase09_unet_baseline_clean_v3.yaml).
Authorized differences vs historical v2: manifest_version, taxonomy_id, experiment_id,
fail-loud CUDA device contract, centralized mask>0 target helper, extra provenance
metadata, single-writer protection. None of these alter training mathematics.

TEST content is never read. VAL only for checkpoint selection.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import yaml

PROJECT_ROOT = Path(r'D:\Softfors\jup')
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.manifest_guard import validate_manifest_version
from src.utils.test_lock import verify_test_lock
from src.utils.device import get_device, device_report
from src.utils.run_lock import acquire_lock, inspect_lock, release_lock, ExperimentLockError
from src.utils.reproducibility import set_seed
from src.utils import config as cfgmod
from src.data.kub_dataset import KUBDataset
from src.data.transforms import SegmentationTransform
from src.data.loaders import create_loader
from src.models.factory import create_model
from src.losses.segmentation import BCEDiceLoss
from src.training.trainer import Trainer
from src.utils.checkpointing import save_training_checkpoint, load_training_checkpoint
from src.utils.experiment import register_experiment

CONFIG_PATH = PROJECT_ROOT / 'configs' / 'phase09_clean_v3' / 'phase09_unet_baseline_clean_v3.yaml'
EXP_ID = 'phase9_kub_unet_baseline_seed42_512_clean_v3'
MANIFEST_VERSION = 'phase4_v3'
TAXONOMY_ID = 'kub_size_clean_v3_v1'
TAXONOMY_ARTIFACT = PROJECT_ROOT / 'reports' / 'audits' / 'kub_size_clean_v3_v1_thresholds.json'

EXP_DIR = PROJECT_ROOT / 'experiments' / EXP_ID
CHK_DIR = PROJECT_ROOT / 'checkpoints' / EXP_ID
TABLES = PROJECT_ROOT / 'reports' / 'tables'
AUDITS = PROJECT_ROOT / 'reports' / 'audits'
FIGDIR = PROJECT_ROOT / 'reports' / 'figures' / 'phase09_clean_v3'

HISTORICAL_EXP_ID = 'phase9_kub_unet_baseline_seed42_512'
HISTORICAL_BEST_SHA = 'a32d7fff1e019a179ef011795b6be8ee98ab548831f790a557726f32b38db8ec'
HISTORICAL_LATEST_SHA = '2b535401e7db95469b39a62bd6b6df51e0e298c32d00047465bc39ababd0ad61'

EXPECTED_TRAIN, EXPECTED_VAL = 1978, 280

#: Fields that must never change during the run (no autonomous retuning).
FROZEN_SCIENTIFIC_FIELDS = (
    'learning_rate', 'weight_decay', 'batch_size', 'scheduler', 'max_epochs',
    'early_stopping_patience', 'threshold', 'seed', 'amp', 'base_channels',
    'input_resolution', 'loss', 'augmentation',
)


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def git_commit():
    import subprocess
    try:
        return subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=str(PROJECT_ROOT),
                              capture_output=True, text=True).stdout.strip() or None
    except Exception:
        return None


def validate_config(cfg: dict) -> dict:
    """Validate the frozen protocol before any training."""
    problems = []
    if cfg['experiment_id'] != EXP_ID:
        problems.append(f"experiment_id {cfg['experiment_id']!r} != {EXP_ID!r}")
    if cfg['manifest_version'] != MANIFEST_VERSION:
        problems.append('manifest_version mismatch')
    if cfg['taxonomy_id'] != TAXONOMY_ID:
        problems.append('taxonomy_id mismatch')
    if cfg['allow_test'] is not False:
        problems.append('allow_test must be False')

    m, p, o, s, t, a = (cfg['model'], cfg['preprocessing'], cfg['optimizer'],
                        cfg['scheduler'], cfg['training'], cfg['augmentation'])
    checks = [
        (m['name'] == 'unet', 'model.name'), (m['input_channels'] == 1, 'input_channels'),
        (m['output_channels'] == 1, 'output_channels'), (m['base_channels'] == 32, 'base_channels'),
        (cfg['input_resolution'] == 512, 'input_resolution'),
        (p['strategy'] == 'aspect_ratio_resize_symmetric_pad', 'preprocessing.strategy'),
        (p['image_interpolation'] == 'bilinear', 'image_interpolation'),
        (p['mask_interpolation'] == 'nearest', 'mask_interpolation'),
        (a['horizontal_flip_probability'] == 0.5, 'hflip'),
        (a['rotation_degrees'] == 5.0, 'rotation'),
        (a['brightness'] == 0.1, 'brightness'), (a['contrast'] == 0.1, 'contrast'),
        (a['vertical_flip'] is False, 'vertical_flip'),
        (cfg['loss']['name'] == 'bce_dice', 'loss.name'),
        (cfg['loss']['bce_weight'] == 0.5, 'bce_weight'),
        (cfg['loss']['dice_weight'] == 0.5, 'dice_weight'),
        (cfg['loss']['dice_epsilon'] == 1e-6, 'dice_epsilon'),
        (o['name'] == 'AdamW', 'optimizer.name'),
        (o['learning_rate'] == 1e-4, 'learning_rate'),
        (o['weight_decay'] == 1e-4, 'weight_decay'),
        (s['name'] == 'CosineAnnealingLR', 'scheduler.name'),
        (s['max_epochs'] == 100, 'scheduler.max_epochs'),
        (t['max_epochs'] == 100, 'max_epochs'),
        (t['early_stopping_patience'] == 15, 'early_stopping_patience'),
        (t['threshold'] == 0.5, 'threshold'),
        (t['seed'] == 42, 'seed'), (t['amp'] is True, 'amp'),
        (t['batch_size'] == 4, 'batch_size'),
        (t['gradient_accumulation_steps'] == 1, 'gradient_accumulation_steps'),
        (t['effective_batch_size'] == 4, 'effective_batch_size'),
        (t['num_workers'] == 0, 'num_workers'), (t['pin_memory'] is True, 'pin_memory'),
    ]
    problems += [name for ok, name in checks if not ok]
    return {'valid': not problems, 'problems': problems}


def pre_run_gates(cfg: dict) -> dict:
    """All hard gates required before the first scientific batch."""
    gates = {}
    res = validate_manifest_version(MANIFEST_VERSION)
    gates['manifest_guard'] = bool(res['ok'])

    train = pd.read_csv(PROJECT_ROOT / 'manifests' / MANIFEST_VERSION / 'train.csv')
    val = pd.read_csv(PROJECT_ROOT / 'manifests' / MANIFEST_VERSION / 'val.csv')
    ktr = train[train['dataset'] == 'KUB']
    kva = val[val['dataset'] == 'KUB']
    gates['kub_train_1978'] = len(ktr) == EXPECTED_TRAIN
    gates['kub_val_280'] = len(kva) == EXPECTED_VAL
    gates['patient_overlap_zero'] = len(set(ktr['patient_id']) & set(kva['patient_id'])) == 0

    # TEST construction must be blocked
    try:
        KUBDataset(PROJECT_ROOT / 'manifests' / MANIFEST_VERSION / 'train.csv', 'TEST')
        gates['test_construction_blocked'] = False
    except Exception:
        gates['test_construction_blocked'] = True

    gates['taxonomy_artifact_sha'] = (
        sha256_file(TAXONOMY_ARTIFACT)
        == '89031c51a35c24f6f939fd6206fde6002a019d4bda24ce8cb21988f04db0f0d6')
    dr = device_report()
    gates['cuda_available'] = dr['cuda_available']
    gates['device_require_cuda'] = get_device(require_cuda=True).type == 'cuda'
    gates['config_validation'] = validate_config(cfg)['valid']

    # test lock (historical protocol statement) — metadata only
    try:
        verify_test_lock(PROJECT_ROOT)
        gates['test_lock_verified'] = True
    except Exception:
        gates['test_lock_verified'] = False
    return gates


def atomic_write_csv(df: pd.DataFrame, path: Path):
    tmp = path.with_suffix(path.suffix + '.tmp')
    df.to_csv(tmp, index=False)
    os.replace(tmp, path)


def main():
    start_utc = utcnow()
    for d in (EXP_DIR, CHK_DIR, TABLES, AUDITS, FIGDIR):
        d.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Config load + validate + hash
    # ------------------------------------------------------------------
    cfg = yaml.safe_load(CONFIG_PATH.read_text(encoding='utf-8'))
    config_sha = sha256_file(CONFIG_PATH)
    v = validate_config(cfg)
    print('=' * 70)
    print('PHASE 09 PART 1A — CLEAN-v3 UNet BASELINE TRAINING')
    print('=' * 70)
    print('config      :', CONFIG_PATH)
    print('config SHA  :', config_sha)
    print('config valid:', v['valid'], v['problems'] if v['problems'] else '')
    for k in ('experiment_id', 'manifest_version', 'taxonomy_id'):
        print(f'{k:12s}:', cfg[k])
    print('model       :', cfg['model'])
    print('resolution  :', cfg['input_resolution'])
    print('loss        :', cfg['loss'])
    print('optimizer   :', cfg['optimizer'])
    print('scheduler   :', cfg['scheduler'])
    print('training    :', cfg['training'])
    print('augmentation:', cfg['augmentation'])
    if not v['valid']:
        print('CHECK_REQUIRED: config validation failed')
        sys.exit(2)

    # ------------------------------------------------------------------
    # Pre-run gates
    # ------------------------------------------------------------------
    gates = pre_run_gates(cfg)
    print()
    print('PRE-RUN GATES')
    for k, val in gates.items():
        print(f'  {k:26s}: {val}')
    if not all(gates.values()):
        print('CHECK_REQUIRED: pre-run gate failure')
        sys.exit(2)

    # ------------------------------------------------------------------
    # Single-writer lock
    # ------------------------------------------------------------------
    lock_status = inspect_lock(EXP_DIR)
    recovered = False
    if lock_status['present']:
        print('existing lock:', lock_status)
    payload = acquire_lock(EXP_DIR, EXP_ID,
                           recover_stale=True if lock_status['present'] else False)
    recovered = bool(payload.get('recovered_stale_lock'))
    print('run lock acquired; pid =', payload['pid'], '| recovered stale =', recovered)

    device = get_device(require_cuda=True)
    set_seed(cfg['training']['seed'], deterministic=True)

    manifest_meta = json.loads(
        (PROJECT_ROOT / 'manifests' / MANIFEST_VERSION / 'manifest_metadata.json')
        .read_text(encoding='utf-8')) if (PROJECT_ROOT / 'manifests' / MANIFEST_VERSION
                                          / 'manifest_metadata.json').exists() else {'hashes': {}}
    manifest_hashes = manifest_meta.get('hashes') or {
        k: sha256_file(PROJECT_ROOT / 'manifests' / MANIFEST_VERSION / f'{k}.csv')
        for k in ('train', 'val', 'test')}

    # ------------------------------------------------------------------
    # Start audit
    # ------------------------------------------------------------------
    start_audit = {
        'audit': 'phase09_clean_v3_training_start_audit',
        'phase': '09 — CLEAN-v3 KUB UNet Baseline (Part 1A)',
        'experiment_id': EXP_ID,
        'config_path': str(CONFIG_PATH.relative_to(PROJECT_ROOT)).replace('\\', '/'),
        'config_sha': config_sha,
        'manifest_version': MANIFEST_VERSION,
        'manifest_hashes': manifest_hashes,
        'taxonomy_id': TAXONOMY_ID,
        'taxonomy_artifact_sha': sha256_file(TAXONOMY_ARTIFACT),
        'git_commit': git_commit(),
        'environment': device_report(),
        'seed': cfg['training']['seed'],
        'start_utc': start_utc,
        'pre_run_gates': gates,
        'run_lock': {'pid': payload['pid'], 'recovered_stale_lock': recovered},
        'historical_checkpoints_reference_only': {
            'best.pt': HISTORICAL_BEST_SHA, 'latest.pt': HISTORICAL_LATEST_SHA},
        'authorized_differences_vs_v2': [
            'manifest_version phase4_v2 -> phase4_v3',
            'taxonomy_id None -> kub_size_clean_v3_v1',
            'experiment_id new clean-v3 logical run',
            'fail-loud CUDA device contract',
            'centralized mask > 0 target helper',
            'additional provenance/checkpoint/resume metadata',
            'single-writer protection',
        ],
        'test_content_reads': 0,
        'scientific_parameter_changes': 0,
    }
    (AUDITS / 'phase09_clean_v3_training_start_audit.json').write_text(
        json.dumps(start_audit, indent=2, default=str), encoding='utf-8')
    _start_md(start_audit, AUDITS / 'phase09_clean_v3_training_start_audit.md')
    print('start audit written')

    # ------------------------------------------------------------------
    # Data / model / training objects
    # ------------------------------------------------------------------
    resolution = cfg['input_resolution']
    train_transform = SegmentationTransform(resolution, train=True)
    val_transform = SegmentationTransform(resolution, train=False)
    train_ds = KUBDataset(PROJECT_ROOT / 'manifests' / MANIFEST_VERSION / 'train.csv',
                          'TRAIN', train_transform, None)
    val_ds = KUBDataset(PROJECT_ROOT / 'manifests' / MANIFEST_VERSION / 'val.csv',
                        'VAL', val_transform, None)

    model = create_model('unet', in_channels=cfg['model']['input_channels'],
                         out_channels=cfg['model']['output_channels'],
                         base_channels=cfg['model']['base_channels']).to(device)
    optimizer = torch.optim.AdamW(model.parameters(),
                                  lr=float(cfg['optimizer']['learning_rate']),
                                  weight_decay=float(cfg['optimizer']['weight_decay']))
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=cfg['scheduler']['max_epochs'])
    criterion = BCEDiceLoss(bce_weight=cfg['loss']['bce_weight'],
                            dice_weight=cfg['loss']['dice_weight'],
                            epsilon=float(cfg['loss']['dice_epsilon']))
    trainer = Trainer(model, optimizer, scheduler, criterion, device,
                      amp=cfg['training']['amp'],
                      gradient_accumulation_steps=cfg['training']['gradient_accumulation_steps'],
                      threshold=cfg['training']['threshold'],
                      patience=cfg['training']['early_stopping_patience'])

    history, best_val_dice, best_epoch = [], -1.0, -1
    start_epoch, resume_count = 1, 0
    train_generator_state = None
    latest_path, best_path = CHK_DIR / 'latest.pt', CHK_DIR / 'best.pt'
    history_path = EXP_DIR / 'history.csv'

    if latest_path.exists():
        state = load_training_checkpoint(latest_path, model, optimizer, scheduler,
                                         trainer.scaler, True, device)
        if state['manifest_version'] != MANIFEST_VERSION:
            print('CHECK_REQUIRED: resume manifest_version mismatch'); sys.exit(2)
        history = state['training_history']
        best_val_dice = float(state['best_validation_score'])
        start_epoch = int(state['epoch']) + 1
        trainer.global_step = int(state['global_step'])
        if best_path.exists():
            best_epoch = int(torch.load(best_path, map_location='cpu',
                                        weights_only=False)['epoch'])
        es = state.get('early_stopping_state') or {}
        trainer.early_stopping.best = float(es.get('best', best_val_dice))
        trainer.early_stopping.bad_epochs = int(es.get('bad_epochs', 0))
        train_generator_state = (state.get('loader_generator_states') or {}).get('train')
        resume_count = 1
        print(f'RESUMING from epoch {start_epoch} (resume count {resume_count})')

    train_loader = create_loader(train_ds, batch_size=cfg['training']['batch_size'],
                                 shuffle=True, seed=cfg['training']['seed'],
                                 num_workers=cfg['training']['num_workers'],
                                 pin_memory=cfg['training']['pin_memory'],
                                 generator_state=train_generator_state)
    val_loader = create_loader(val_ds, batch_size=cfg['training']['batch_size'],
                               shuffle=False, seed=cfg['training']['seed'],
                               num_workers=cfg['training']['num_workers'],
                               pin_memory=cfg['training']['pin_memory'])

    log_file = open(EXP_DIR / 'training.log', 'a' if start_epoch > 1 else 'w', encoding='utf-8')
    log_file.write(f"{'Resume' if start_epoch > 1 else 'Start'} UTC={start_utc} "
                   f"epoch={start_epoch} pid={payload['pid']}\n")
    log_file.flush()

    nan_events, early_stopped, stop_reason = 0, False, 'MAX_EPOCH'
    training_start = time.time()

    # ------------------------------------------------------------------
    # Training loop (exact historical ordering)
    # ------------------------------------------------------------------
    for epoch in range(start_epoch, cfg['training']['max_epochs'] + 1):
        ep_start = time.time()
        tr_info = trainer.train_one_epoch(train_loader)
        val_info, _ = trainer.validate(val_loader)
        scheduler.step()
        ep_time = time.time() - ep_start

        values = [tr_info['loss'], val_info['loss'], val_info['dice'],
                  val_info['iou'], val_info['precision'], val_info['recall']]
        if not all(math.isfinite(float(x)) for x in values):
            nan_events += 1
            log_file.write(f'NON-FINITE at epoch {epoch}: {values}\n'); log_file.flush()
            print('CHECK_REQUIRED: non-finite value encountered at epoch', epoch)
            _completion(AUDITS, TABLES, FIGDIR, cfg, config_sha, manifest_hashes,
                        history, best_epoch, best_val_dice, 'CHECK_REQUIRED',
                        'NON_FINITE', early_stopped, resume_count, start_utc,
                        training_start, CHK_DIR, EXP_DIR, nan_events, payload, recovered,
                        len(train_ds), len(val_ds))
            log_file.close()
            release_lock(EXP_DIR, force=True)
            sys.exit(3)

        improved = val_info['dice'] > best_val_dice
        if improved:
            best_val_dice = val_info['dice']
            best_epoch = epoch
        should_stop = trainer.early_stopping.update(val_info['dice'])

        current_lr = optimizer.param_groups[0]['lr']
        epoch_rec = {
            'epoch': epoch,
            'train_loss': tr_info['loss'],
            'val_loss': val_info['loss'],
            'val_macro_dice': val_info['dice'],
            'val_macro_iou': val_info['iou'],
            'val_macro_precision': val_info['precision'],
            'val_macro_recall': val_info['recall'],
            'learning_rate': current_lr,
            'best_metric_so_far': best_val_dice,
            'improved': bool(improved),
            'bad_epochs': int(trainer.early_stopping.bad_epochs),
            'epoch_seconds': ep_time,
            'checkpoint_event': ('best+latest' if improved else 'latest'),
        }
        history.append(epoch_rec)
        atomic_write_csv(pd.DataFrame(history), history_path)

        msg = (f"Epoch {epoch:03d}/{cfg['training']['max_epochs']} | "
               f"train={tr_info['loss']:.4f} | val_loss={val_info['loss']:.4f} | "
               f"val_macro_dice={val_info['dice']:.4f} | lr={current_lr:.6f} | "
               f"{ep_time:.1f}s | best={best_val_dice:.4f} | bad={trainer.early_stopping.bad_epochs}")
        print(msg, flush=True)
        log_file.write(msg + '\n'); log_file.flush()

        early_state = {'best': trainer.early_stopping.best,
                       'bad_epochs': trainer.early_stopping.bad_epochs,
                       'patience': trainer.early_stopping.patience,
                       'stopped': should_stop}
        loader_states = {'train': train_loader.generator.get_state(),
                         'val': val_loader.generator.get_state()}
        common = dict(model=model, optimizer=optimizer, scheduler=scheduler,
                      scaler=trainer.scaler, epoch=epoch,
                      global_step=trainer.global_step, best_validation_score=best_val_dice,
                      configuration=cfg, seed=cfg['training']['seed'],
                      training_history=history, manifest_version=MANIFEST_VERSION,
                      manifest_hashes=manifest_hashes, experiment_id=EXP_ID,
                      model_name='unet', input_resolution=resolution,
                      threshold=cfg['training']['threshold'],
                      early_stopping_state=early_state,
                      loader_generator_states=loader_states, taxonomy_id=TAXONOMY_ID)
        save_training_checkpoint(latest_path, **common)
        if improved:
            save_training_checkpoint(best_path, **common)

        if should_stop:
            early_stopped, stop_reason = True, 'EARLY_STOP'
            print(f'Early stopping at epoch {epoch}')
            log_file.write(f'Early stopping at epoch {epoch}\n')
            break

    log_file.close()
    training_end = utcnow()
    print(f'Training finished: best epoch {best_epoch}, best val macro dice {best_val_dice:.6f}')

    # ------------------------------------------------------------------
    # Curves
    # ------------------------------------------------------------------
    _curves(history, FIGDIR)
    atomic_write_csv(pd.DataFrame(history), TABLES / 'phase09_clean_v3_training_history.csv')

    # ------------------------------------------------------------------
    # Completion audit
    # ------------------------------------------------------------------
    audit = _completion(AUDITS, TABLES, FIGDIR, cfg, config_sha, manifest_hashes,
                        history, best_epoch, best_val_dice, 'PASS', stop_reason,
                        early_stopped, resume_count, start_utc, training_start,
                        CHK_DIR, EXP_DIR, nan_events, payload, recovered,
                        len(train_ds), len(val_ds), training_end=training_end)
    release_lock(EXP_DIR, force=True)
    print('completion audit written')
    print('=' * 70)
    print('STATUS:', audit['training_status'])
    print('=' * 70)
    return audit


def _curves(history, figdir):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    if not history:
        return
    df = pd.DataFrame(history)
    fig, axes = plt.subplots(2, 2, figsize=(11, 7.5))
    axes[0, 0].plot(df['epoch'], df['train_loss'], label='train loss', color='#1f77b4')
    axes[0, 0].plot(df['epoch'], df['val_loss'], label='val loss', color='#ff7f0e')
    axes[0, 0].set_title('Loss'); axes[0, 0].legend(frameon=False, fontsize=8)
    axes[0, 1].plot(df['epoch'], df['val_macro_dice'], color='#2ca02c', label='val macro dice')
    axes[0, 1].plot(df['epoch'], df['best_metric_so_far'], '--', color='#888',
                    label='best so far')
    axes[0, 1].set_title('VAL macro Dice'); axes[0, 1].legend(frameon=False, fontsize=8)
    axes[1, 0].plot(df['epoch'], df['learning_rate'], color='#d62728')
    axes[1, 0].set_title('Learning rate (cosine)')
    axes[1, 1].plot(df['epoch'], df['bad_epochs'], color='#9467bd')
    axes[1, 1].set_title('Early-stop counter (patience 15)')
    for ax in axes.ravel():
        ax.set_xlabel('epoch')
    fig.suptitle('Phase 09 CLEAN-v3 UNet baseline — training curves', fontweight='bold')
    fig.tight_layout()
    fig.savefig(figdir / 'phase09_clean_v3_training_curves.png', dpi=130, bbox_inches='tight')
    plt.close(fig)


def _completion(audits, tables, figdir, cfg, config_sha, manifest_hashes, history,
                best_epoch, best_val_dice, status, stop_reason, early_stopped,
                resume_count, start_utc, training_start, chk_dir, exp_dir, nan_events,
                payload, recovered, n_train, n_val, training_end=None):
    best_path, latest_path = chk_dir / 'best.pt', chk_dir / 'latest.pt'
    best_meta = torch.load(best_path, map_location='cpu', weights_only=False) if best_path.exists() else {}
    latest_meta = torch.load(latest_path, map_location='cpu', weights_only=False) if latest_path.exists() else {}
    df = pd.DataFrame(history)
    best_row = df[df['epoch'] == best_epoch].iloc[0].to_dict() if best_epoch in set(df.get('epoch', [])) else {}

    audit = {
        'audit': 'phase09_clean_v3_training_completion_audit',
        'phase': '09 — CLEAN-v3 KUB UNet Baseline (Part 1A)',
        'experiment_id': EXP_ID,
        'config_path': str(CONFIG_PATH.relative_to(PROJECT_ROOT)).replace('\\', '/'),
        'config_sha': config_sha,
        'manifest_version': MANIFEST_VERSION,
        'manifest_hashes': manifest_hashes,
        'taxonomy_id': TAXONOMY_ID,
        'start_utc': start_utc,
        'end_utc': training_end or utcnow(),
        'wall_seconds': time.time() - training_start,
        'resume_count': resume_count,
        'epochs_completed': len(history),
        'best_epoch': best_epoch,
        'best_val_macro_dice': float(best_val_dice) if best_epoch > 0 else None,
        'val_macro_iou_at_best': best_row.get('val_macro_iou'),
        'val_macro_precision_at_best': best_row.get('val_macro_precision'),
        'val_macro_recall_at_best': best_row.get('val_macro_recall'),
        'val_loss_at_best': best_row.get('val_loss'),
        'final_epoch': int(df['epoch'].iloc[-1]) if len(df) else None,
        'stop_reason': stop_reason,
        'early_stopped': early_stopped,
        'early_stop_bad_epochs': int(df['bad_epochs'].iloc[-1]) if len(df) else None,
        'train_samples': n_train,
        'val_samples': n_val,
        'device': device_report(),
        'best_checkpoint': str(best_path.relative_to(PROJECT_ROOT)).replace('\\', '/'),
        'best_checkpoint_sha': sha256_file(best_path) if best_path.exists() else None,
        'latest_checkpoint': str(latest_path.relative_to(PROJECT_ROOT)).replace('\\', '/'),
        'latest_checkpoint_sha': sha256_file(latest_path) if latest_path.exists() else None,
        'best_checkpoint_epoch': best_meta.get('epoch'),
        'latest_checkpoint_epoch': latest_meta.get('epoch'),
        'best_checkpoint_taxonomy_id': best_meta.get('taxonomy_id'),
        'latest_checkpoint_taxonomy_id': latest_meta.get('taxonomy_id'),
        'best_checkpoint_manifest_version': best_meta.get('manifest_version'),
        'latest_checkpoint_manifest_version': latest_meta.get('manifest_version'),
        'best_checkpoint_experiment_id': best_meta.get('experiment_id'),
        'history': str((exp_dir / 'history.csv').relative_to(PROJECT_ROOT)).replace('\\', '/'),
        'history_sha': sha256_file(exp_dir / 'history.csv') if (exp_dir / 'history.csv').exists() else None,
        'finite_losses': bool(nan_events == 0),
        'nan_inf_events': nan_events,
        'scientific_parameter_changes': 0,
        'run_lock': {'pid': payload['pid'], 'recovered_stale_lock': recovered,
                     'released': True},
        'test_content_reads': 0,
        'test_image_reads': 0,
        'test_mask_reads': 0,
        'test_metrics': 0,
        'test_visualizations': 0,
        'test_checkpoint_selection': False,
        'training_status': status,
    }
    (audits / 'phase09_clean_v3_training_completion_audit.json').write_text(
        json.dumps(audit, indent=2, default=str), encoding='utf-8')
    _completion_md(audit, audits / 'phase09_clean_v3_training_completion_audit.md')
    return audit


def _start_md(a, path):
    md = ['# Phase 09 CLEAN-v3 — Training Start Audit', '',
          f"**Experiment ID:** `{a['experiment_id']}`  ",
          f"**Start (UTC):** {a['start_utc']}  ",
          f"**Status:** `{a['training_status'] if 'training_status' in a else 'STARTED'}`", '',
          '| Field | Value |', '|---|---|',
          f"| Config | `{a['config_path']}` |",
          f"| Config SHA | `{a['config_sha']}` |",
          f"| Manifest version | `{a['manifest_version']}` |",
          f"| Taxonomy ID | `{a['taxonomy_id']}` |",
          f"| Taxonomy artifact SHA | `{a['taxonomy_artifact_sha']}` |",
          f"| Git commit | `{a['git_commit']}` |",
          f"| Seed | {a['seed']} |",
          f"| Run lock PID | {a['run_lock']['pid']} |",
          f"| Stale lock recovered | {a['run_lock']['recovered_stale_lock']} |", '',
          '## Environment', '', '| Field | Value |', '|---|---|']
    for k, v in a['environment'].items():
        md.append(f'| {k} | {v} |')
    md += ['', '## Pre-run gates', '', '| Gate | Result |', '|---|---|']
    for k, v in a['pre_run_gates'].items():
        md.append(f"| {k} | {'PASS' if v else 'FAIL'} |")
    md += ['', '## Authorized differences vs historical v2', '']
    for d in a['authorized_differences_vs_v2']:
        md.append(f'- {d}')
    md += ['', f"- TEST content reads: {a['test_content_reads']}",
           f"- Scientific parameter changes: {a['scientific_parameter_changes']}", '']
    path.write_text('\n'.join(md), encoding='utf-8')


def _completion_md(a, path):
    md = ['# Phase 09 CLEAN-v3 — Training Completion Audit', '',
          f"**Status:** `{a['training_status']}`  ",
          f"**Experiment ID:** `{a['experiment_id']}`", '',
          '## Run summary', '', '| Field | Value |', '|---|---|',
          f"| Config SHA | `{a['config_sha']}` |",
          f"| Manifest version | `{a['manifest_version']}` |",
          f"| Taxonomy ID | `{a['taxonomy_id']}` |",
          f"| Start (UTC) | {a['start_utc']} |",
          f"| End (UTC) | {a['end_utc']} |",
          f"| Wall seconds | {a['wall_seconds']:.1f} |",
          f"| Resume count | {a['resume_count']} |",
          f"| Epochs completed | {a['epochs_completed']} |",
          f"| Best epoch | {a['best_epoch']} |",
          f"| Best VAL macro Dice | {a['best_val_macro_dice']} |",
          f"| VAL macro IoU @ best | {a['val_macro_iou_at_best']} |",
          f"| VAL macro Precision @ best | {a['val_macro_precision_at_best']} |",
          f"| VAL macro Recall @ best | {a['val_macro_recall_at_best']} |",
          f"| Final/latest epoch | {a['final_epoch']} |",
          f"| Stop reason | **{a['stop_reason']}** |",
          f"| Early-stop bad_epochs | {a['early_stop_bad_epochs']} |", '',
          '## Checkpoints', '', '| Field | Value |', '|---|---|',
          f"| best.pt | `{a['best_checkpoint']}` |",
          f"| best.pt SHA | `{a['best_checkpoint_sha']}` |",
          f"| best.pt epoch | {a['best_checkpoint_epoch']} |",
          f"| latest.pt | `{a['latest_checkpoint']}` |",
          f"| latest.pt SHA | `{a['latest_checkpoint_sha']}` |",
          f"| latest.pt epoch | {a['latest_checkpoint_epoch']} |",
          f"| best taxonomy_id | `{a['best_checkpoint_taxonomy_id']}` |",
          f"| latest taxonomy_id | `{a['latest_checkpoint_taxonomy_id']}` |",
          f"| best manifest_version | `{a['best_checkpoint_manifest_version']}` |",
          f"| latest manifest_version | `{a['latest_checkpoint_manifest_version']}` |", '',
          '## History', '', f"- Path: `{a['history']}`", f"- SHA: `{a['history_sha']}`", '',
          '## Governance', '',
          f"- Finite losses: {a['finite_losses']}",
          f"- NaN/Inf events: {a['nan_inf_events']}",
          f"- Scientific parameter changes: {a['scientific_parameter_changes']}",
          f"- TEST content reads: {a['test_content_reads']}",
          f"- TEST metrics: {a['test_metrics']}",
          f"- TEST visualizations: {a['test_visualizations']}",
          f"- TEST checkpoint selection: {a['test_checkpoint_selection']}", '']
    path.write_text('\n'.join(md), encoding='utf-8')


if __name__ == '__main__':
    main()
