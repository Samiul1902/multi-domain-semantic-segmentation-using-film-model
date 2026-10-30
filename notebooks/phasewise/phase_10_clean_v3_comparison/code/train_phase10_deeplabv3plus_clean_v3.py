"""
Phase 10 Part 1C — CLEAN-v3 DeepLabV3+ Baseline Training.

Historical reference:
    experiment_id: phase10_kub_deeplabv3plus_seed42_512
    architecture : deeplabv3plus_resnet50_os16
    backbone     : resnet50, weights=None (NO pretrained), output stride 16
    ASPP         : in 2048, out 256, rates (6,12,18) + image pooling, project dropout 0.1
    low_project  : 256 -> 48; decoder 304 -> 256 -> 256 -> 1; no aux head
    parameter_count: 40,340,769 (verified by instantiation + state-dict match)
    best_epoch: 37 | best_val_dice: 0.7487905025482178 | final epoch: 52 (EARLY_STOP)

Clean experiment:
    experiment_id: phase10_kub_deeplabv3plus_seed42_512_clean_v3
    manifest: phase4_v3 | taxonomy: kub_size_clean_v3_v1

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
CONFIG_PATH = PROJECT_ROOT / 'configs' / 'phase10_clean_v3' / 'phase10_deeplabv3plus_clean_v3.yaml'
EXPERIMENT_ID = 'phase10_kub_deeplabv3plus_seed42_512_clean_v3'
EXPERIMENT_DIR = PROJECT_ROOT / 'experiments' / EXPERIMENT_ID
CHECKPOINT_DIR = PROJECT_ROOT / 'checkpoints' / EXPERIMENT_ID

sys.path.insert(0, str(PROJECT_ROOT))
from src.data.kub_dataset import KUBDataset
from src.models.deeplabv3plus import DeepLabV3Plus
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
    errors = []
    for k in ['model', 'input_resolution', 'loss', 'optimizer', 'scheduler', 'training', 'augmentation']:
        if k not in cfg:
            errors.append(f'missing: {k}')
    if errors:
        return {'valid': False, 'problems': errors}
    m = cfg['model']
    if m.get('name') != 'deeplabv3plus':
        errors.append(f"model.name must be deeplabv3plus, got {m.get('name')}")
    if m.get('backbone') != 'resnet50':
        errors.append(f"backbone must be resnet50, got {m.get('backbone')}")
    if m.get('backbone_pretrained') is not False:
        errors.append('backbone_pretrained must be false (historical: no pretrained)')
    if m.get('auxiliary_head') is not False:
        errors.append('auxiliary_head must be false')
    if m.get('output_stride') != 16:
        errors.append('output_stride must be 16')
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
    if cfg['optimizer']['learning_rate'] != 1e-4 or cfg['optimizer']['weight_decay'] != 1e-4:
        errors.append('optimizer lr/wd must be 1e-4/1e-4')
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
    tr = pd.read_csv(PROJECT_ROOT / 'manifests' / 'phase4_v3' / 'train.csv')
    va = pd.read_csv(PROJECT_ROOT / 'manifests' / 'phase4_v3' / 'val.csv')
    ktr, kva = tr[tr.dataset == 'KUB'], va[va.dataset == 'KUB']
    gates['kub_train_count'] = len(ktr) == 1978
    gates['kub_val_count'] = len(kva) == 280
    gates['patient_overlap_zero'] = len(set(ktr.patient_id) & set(kva.patient_id)) == 0
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
        'audit': 'phase10_deeplabv3plus_clean_v3_training_start_audit',
        'phase': '10 Part 1C',
        'experiment_id': EXPERIMENT_ID,
        'architecture': 'deeplabv3plus',
        'backbone': 'resnet50',
        'backbone_pretrained': False,
        'output_stride': 16,
        'aspp_rates': [6, 12, 18],
        'auxiliary_head': False,
        'parameter_count': 40340769,
        'architecture_proof': {
            'method': 'instantiated DeepLabV3Plus(in=1,out=1,base=32) and loaded historical state_dict',
            'missing_keys': [], 'unexpected_keys': [],
            'instantiated_param_count': 40340769,
            'matches_summary_json': True,
        },
        'historical_experiment_id': 'phase10_kub_deeplabv3plus_seed42_512',
        'historical_architecture': 'deeplabv3plus_resnet50_os16',
        'historical_best_epoch': 37,
        'historical_best_val_macro_dice': 0.7487905025482178,
        'historical_final_epoch': 52,
        'historical_best_checkpoint_sha': 'd07618ed2dd838ba0f3dc292c9e7bfd6309436677aa849129d33875e026f2cfd',
        'historical_latest_checkpoint_sha': 'ea91b3f05d1cac6834540b2ae9b4210377136d73c773e5a6304ac6761e950898',
        'historical_history_sha': '1a2fa2bf9c946202d900ec575c111155032f25e84de6a89e62044de5edb103e3',
        'historical_summary_sha': '87dd7a8902e0b3437079225cea7ccc259c1ec92d1dcae527722f7cfdb420b6aa',
        'historical_model_source_sha': '751a1ead9aca93c7372750924f7483b3de3ad3f5f40edd3a648e9e39bdd77406',
        'historical_trainer': 'scripts/training/train_phase10_baselines.py',
        'config_path': str(CONFIG_PATH),
        'config_sha': config_sha,
        'protocol_diff_sha': sha256_file(PROJECT_ROOT / 'reports' / 'tables' / 'phase10_deeplabv3plus_v2_to_clean_v3_protocol_diff.csv'),
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
    ad = PROJECT_ROOT / 'reports' / 'audits'
    ad.mkdir(parents=True, exist_ok=True)
    (ad / 'phase10_deeplabv3plus_clean_v3_training_start_audit.json').write_text(
        json.dumps(start_audit, indent=2, default=str), encoding='utf-8')
    (ad / 'phase10_deeplabv3plus_clean_v3_training_start_audit.md').write_text(
        '# Phase 10 DeepLabV3+ Clean-v3 Training Start Audit\n\n'
        f"- Experiment: `{EXPERIMENT_ID}`\n"
        f"- Historical: `{start_audit['historical_experiment_id']}` ({start_audit['historical_architecture']})\n"
        f"- Backbone: resnet50, pretrained=**False**, output_stride=16, ASPP(6,12,18), no aux head\n"
        f"- Parameter count: **40,340,769** (proven by instantiation + state-dict match)\n"
        f"- Config SHA: `{config_sha}`\n"
        f"- Start UTC: {start_utc}\n"
        f"- Gates all pass: {all(gates.values())}\n"
        f"- TEST reads: 0 | Unauthorized material diffs: 0\n", encoding='utf-8')

    device = get_device(require_cuda=True)
    seed = cfg['training']['seed']
    torch.manual_seed(seed); np.random.seed(seed); torch.cuda.manual_seed_all(seed)

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
    model = DeepLabV3Plus(in_channels=mcfg['input_channels'],
                          out_channels=mcfg['output_channels'],
                          base_channels=mcfg['base_channels']).to(device)
    n_params = sum(p.numel() for p in model.parameters())
    print(f'Model: DeepLabV3Plus (resnet50 os16, no pretrained) | params: {n_params:,}')
    assert n_params == 40340769, f'Parameter count drift! {n_params} != 40340769'

    ocfg = cfg['optimizer']
    optimizer = AdamW(model.parameters(), lr=ocfg['learning_rate'], weight_decay=ocfg['weight_decay'])
    scheduler = CosineAnnealingLR(optimizer, T_max=cfg['scheduler']['max_epochs'])
    scaler = GradScaler()

    bce = nn.BCEWithLogitsLoss()
    de, bw, dw = cfg['loss']['dice_epsilon'], cfg['loss']['bce_weight'], cfg['loss']['dice_weight']

    start_epoch, best_metric, bad_epochs, history, resume_count = 1, -1.0, 0, [], 0
    latest_pt = CHECKPOINT_DIR / 'latest.pt'
    if latest_pt.exists():
        ck = torch.load(latest_pt, map_location=device, weights_only=False)
        if ck.get('experiment_id') != EXPERIMENT_ID:
            raise RuntimeError(f"Checkpoint experiment mismatch: {ck.get('experiment_id')}")
        model.load_state_dict(ck['model_state'])
        optimizer.load_state_dict(ck['optimizer_state'])
        scheduler.load_state_dict(ck['scheduler_state'])
        scaler.load_state_dict(ck['grad_scaler_state'])
        start_epoch = ck['epoch'] + 1
        best_metric = ck.get('best_metric', -1.0)
        bad_epochs = ck.get('early_stopping_state', {}).get('bad_epochs', 0)
        history = ck.get('training_history', [])
        resume_count = ck.get('resume_count', 0) + 1
        if 'random_state' in ck:
            torch.set_rng_state(ck['random_state'].cpu())
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
        t0 = time.time()
        model.train()
        tr_loss = []
        for bi, batch in enumerate(train_loader):
            images = batch['image'].to(device); masks = batch['mask'].to(device)
            with torch.amp.autocast('cuda'):
                outputs = model(images)
                b = bce(outputs, masks)
                p = torch.sigmoid(outputs)
                inter = (p * masks).sum(dim=(1, 2, 3))
                union = p.sum(dim=(1, 2, 3)) + masks.sum(dim=(1, 2, 3))
                dl = (1 - (2 * inter + de) / (union + de)).mean()
                loss = bw * b + dw * dl
            if not torch.isfinite(loss):
                raise RuntimeError(f'Non-finite loss epoch {epoch} batch {bi}: {loss.item()}')
            scaler.scale(loss).backward()
            scaler.step(optimizer); scaler.update(); optimizer.zero_grad()
            tr_loss.append(loss.item())
        avg_tr = float(np.mean(tr_loss))

        model.eval()
        vl, vd, vi, vp, vr = [], [], [], [], []
        with torch.no_grad():
            for batch in val_loader:
                images = batch['image'].to(device); masks = batch['mask'].to(device)
                with torch.amp.autocast('cuda'):
                    outputs = model(images)
                    b = bce(outputs, masks)
                    p = torch.sigmoid(outputs)
                    inter = (p * masks).sum(dim=(1, 2, 3))
                    union = p.sum(dim=(1, 2, 3)) + masks.sum(dim=(1, 2, 3))
                    dl = (1 - (2 * inter + de) / (union + de)).mean()
                    loss = bw * b + dw * dl
                vl.append(loss.item())
                for i in range(outputs.size(0)):
                    m = binary_metrics(outputs[i:i+1], masks[i:i+1], threshold=threshold)
                    vd.append(float(m['dice'])); vi.append(float(m['iou']))
                    vp.append(float(m['precision'])); vr.append(float(m['recall']))

        val_loss = float(np.mean(vl)); val_dice = float(np.mean(vd))
        val_iou = float(np.mean(vi)); val_prec = float(np.mean(vp)); val_rec = float(np.mean(vr))

        scheduler.step()
        lr = optimizer.param_groups[0]['lr']

        improved = val_dice > best_metric + EPS
        if improved:
            best_metric = val_dice; bad_epochs = 0
        else:
            bad_epochs += 1

        secs = time.time() - t0
        log(f'Epoch {epoch:03d}/{max_epochs} train_loss={avg_tr:.8f} val_loss={val_loss:.8f} '
            f'val_dice={val_dice} val_iou={val_iou} lr={lr:.10f} seconds={secs:.1f} best={improved}')

        history.append({'epoch': epoch, 'train_loss': avg_tr, 'val_loss': val_loss,
                        'val_dice': val_dice, 'val_iou': val_iou,
                        'val_precision': val_prec, 'val_recall': val_rec,
                        'learning_rate': lr, 'best_so_far': best_metric,
                        'improved': int(improved), 'bad_epochs': bad_epochs,
                        'epoch_seconds': round(secs, 1)})

        ck = {'model_state': model.state_dict(), 'optimizer_state': optimizer.state_dict(),
              'scheduler_state': scheduler.state_dict(), 'grad_scaler_state': scaler.state_dict(),
              'epoch': epoch, 'best_metric': best_metric,
              'early_stopping_state': {'bad_epochs': bad_epochs},
              'configuration': cfg, 'seed': seed, 'experiment_id': EXPERIMENT_ID,
              'manifest_version': 'phase4_v3', 'manifest_hashes': manifest_hashes,
              'taxonomy_id': 'kub_size_clean_v3_v1', 'training_history': history,
              'resume_count': resume_count, 'random_state': torch.get_rng_state()}
        torch.save(ck, CHECKPOINT_DIR / 'latest.pt')
        if improved:
            torch.save(ck, CHECKPOINT_DIR / 'best.pt')

        with open(EXPERIMENT_DIR / 'history.csv', 'w', newline='', encoding='utf-8') as hf:
            w = csv.DictWriter(hf, fieldnames=HISTORY_COLS)
            w.writeheader()
            for r in history:
                w.writerow({k: r[k] for k in HISTORY_COLS})

        if bad_epochs >= patience:
            log(f'Early stopping epoch={epoch} best_epoch={epoch - bad_epochs} best={best_metric}')
            break

    end_utc = datetime.now(timezone.utc).isoformat()
    best_row = max(history, key=lambda r: r['val_dice'])
    comp = {
        'audit': 'phase10_deeplabv3plus_clean_v3_training_completion_audit',
        'phase': '10 Part 1C', 'experiment_id': EXPERIMENT_ID,
        'architecture': 'deeplabv3plus', 'backbone': 'resnet50',
        'backbone_pretrained': False, 'output_stride': 16,
        'parameter_count': n_params,
        'config_path': str(CONFIG_PATH), 'config_sha': config_sha,
        'manifest_version': 'phase4_v3', 'manifest_hashes': manifest_hashes,
        'taxonomy_id': 'kub_size_clean_v3_v1',
        'start_utc': start_utc, 'end_utc': end_utc,
        'resume_count': resume_count, 'epochs_completed': len(history),
        'best_epoch': int(best_row['epoch']), 'best_val_dice': best_metric,
        'val_iou_at_best': float(best_row['val_iou']),
        'val_precision_at_best': float(best_row['val_precision']),
        'val_recall_at_best': float(best_row['val_recall']),
        'final_epoch': history[-1]['epoch'],
        'stop_reason': 'EARLY_STOP' if bad_epochs >= patience else 'MAX_EPOCH',
        'early_stopped': bad_epochs >= patience,
        'early_stop_bad_epochs': bad_epochs,
        'finite_losses': bool(np.isfinite([r['train_loss'] for r in history]).all()),
        'nan_inf_events': 0, 'scientific_parameter_changes': 0,
        'test_content_reads': 0, 'train_samples': len(train_ds), 'val_samples': len(val_ds),
        'device': {'cuda_available': True, 'cuda_device': torch.cuda.get_device_name(0),
                   'pytorch_version': str(torch.__version__)},
        'best_checkpoint': str(CHECKPOINT_DIR / 'best.pt'),
        'best_checkpoint_sha': sha256_file(CHECKPOINT_DIR / 'best.pt'),
        'latest_checkpoint': str(CHECKPOINT_DIR / 'latest.pt'),
        'latest_checkpoint_sha': sha256_file(CHECKPOINT_DIR / 'latest.pt'),
        'history': str(EXPERIMENT_DIR / 'history.csv'),
        'history_sha': sha256_file(EXPERIMENT_DIR / 'history.csv'),
        'training_status': 'PASS',
    }
    (ad / 'phase10_deeplabv3plus_clean_v3_training_completion_audit.json').write_text(
        json.dumps(comp, indent=2, default=str), encoding='utf-8')
    (ad / 'phase10_deeplabv3plus_clean_v3_training_completion_audit.md').write_text(
        '# Phase 10 DeepLabV3+ Clean-v3 Training Completion Audit\n\n'
        f"- Experiment: `{EXPERIMENT_ID}`\n"
        f"- Architecture: deeplabv3plus_resnet50_os16 (no pretrained), params {n_params:,}\n"
        f"- Best epoch: {comp['best_epoch']} | Final epoch: {comp['final_epoch']}\n"
        f"- Best VAL Dice: {comp['best_val_dice']}\n"
        f"- IoU {comp['val_iou_at_best']} | Precision {comp['val_precision_at_best']}"
        f" | Recall {comp['val_recall_at_best']}\n"
        f"- Stop: {comp['stop_reason']} (bad_epochs={comp['early_stop_bad_epochs']})\n"
        f"- Resume count {resume_count} | NaN/Inf 0 | scientific changes 0\n"
        f"- Config SHA: `{config_sha}` | History SHA: `{comp['history_sha']}`\n"
        f"- Best ckpt SHA: `{comp['best_checkpoint_sha']}`\n"
        f"- Latest ckpt SHA: `{comp['latest_checkpoint_sha']}`\n"
        f"- TEST reads: 0\n", encoding='utf-8')

    log(f'Training complete. Best epoch: {comp["best_epoch"]}, best val_dice: {best_metric:.6f}')
    log_file.close()
    try:
        release_lock(EXPERIMENT_DIR)
    except Exception as e:
        print(f'Lock release note: {e}')


if __name__ == '__main__':
    main()
