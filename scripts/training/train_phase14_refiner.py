"""
Phase 14 — Regional Refiner Diagnostic — Clean-v3 Training
Frozen protocol: reports/audits/phase14_diagnostic_protocol_amendment.json
Experiment: phase14_kub_refiner_unet_a3_256_seed42_clean_v3
"""
import os
import sys
import json
import time
import random
import argparse
import hashlib
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
import numpy as np
import pandas as pd
from PIL import Image

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.models.unet import UNet
from src.losses.segmentation import BCEDiceLoss
from src.data.regional_dataset import (
    RegionalCropDataset,
    ORACLE_DERIVED_REFINER_MARGIN,
    PREDICTED_PROPOSAL_MARGIN,
)
from src.utils.device import get_device
from src.utils.config import validate_experiment_config

EXPERIMENT_ID = "phase14_kub_refiner_unet_a3_256_seed42_clean_v3"
CHECKPOINT_DIR = PROJECT_ROOT / "checkpoints" / EXPERIMENT_ID
EXPERIMENT_DIR = PROJECT_ROOT / "experiments" / EXPERIMENT_ID
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
EXPERIMENT_DIR.mkdir(parents=True, exist_ok=True)


def sha_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def compute_crop_dice(pred_logits, target_mask, epsilon=1e-6):
    """Compute Dice per crop. pred_logits: [B,1,H,W], target_mask: [B,1,H,W]."""
    probs = torch.sigmoid(pred_logits)
    pred_bin = (probs >= 0.5).float()
    dims = tuple(range(1, pred_logits.ndim))
    intersection = (pred_bin * target_mask).sum(dims)
    denominator = pred_bin.sum(dims) + target_mask.sum(dims)
    dice = (2.0 * intersection + epsilon) / (denominator + epsilon)
    return dice.mean().item()


def train_epoch(model, loader, criterion, optimizer, scaler, device):
    model.train()
    losses = []
    for batch in loader:
        imgs = batch['image'].to(device)
        masks = batch['mask'].to(device)
        optimizer.zero_grad()
        with torch.amp.autocast('cuda', enabled=scaler is not None):
            logits = model(imgs)
            loss = criterion(logits, masks)
        if scaler is not None:
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
        else:
            loss.backward()
            optimizer.step()
        losses.append(loss.item())
    return float(np.mean(losses))


@torch.no_grad()
def validate(model, loader, criterion, device):
    model.eval()
    losses = []
    dices = []
    for batch in loader:
        imgs = batch['image'].to(device)
        masks = batch['mask'].to(device)
        logits = model(imgs)
        loss = criterion(logits, masks)
        losses.append(loss.item())
        dices.append(compute_crop_dice(logits, masks))
    return float(np.mean(losses)), float(np.mean(dices))


# --- Execution-mechanism support: interruption-resilient resume ----------------
# The host terminates long-running child processes when the launching session's
# process tree is torn down. This is an OPERATIONAL constraint only; it does not
# change any scientific computation. To let a long run converge across such
# interruptions, the trainer records and restores the complete RNG state so that
# a resumed run is a BIT-EXACT continuation of the interrupted trajectory.
#
# RNG sources that must survive a restart:
#   - the dataset's own random.Random (used for perturbation jitter, augmentation)
#   - the global Python random module
#   - the global numpy RNG (used for background-negative sampling retries)
#   - the global torch CPU RNG (DataLoader shuffle permutation)
#   - the torch CUDA RNGs (dropout / any stochastic CUDA op)
def capture_rng_state(ds_train, ds_val):
    state = {
        'global_random': random.getstate(),
        'global_numpy': np.random.get_state(),
        'global_torch': torch.get_rng_state(),
        'dataset_train': ds_train.rng.getstate(),
        'dataset_val': ds_val.rng.getstate(),
    }
    if torch.cuda.is_available():
        state['cuda'] = torch.cuda.get_rng_state_all()
    return state


def _as_cpu_byte_tensor(t):
    """Coerce a stored RNG state into a CPU torch.ByteTensor.

    torch.set_rng_state / torch.cuda.set_rng_state_all require a ByteTensor, and
    the CPU default generator requires it to live on the CPU. Checkpoints are
    loaded with map_location=<cuda device>, which relocates saved tensors, so the
    device must be forced back to CPU here.
    """
    if isinstance(t, torch.Tensor):
        return t.detach().to(device='cpu', dtype=torch.uint8).contiguous()
    return torch.tensor(list(t), dtype=torch.uint8)


def restore_rng_state(state, ds_train, ds_val):
    random.setstate(state['global_random'])
    np.random.set_state(state['global_numpy'])
    torch.set_rng_state(_as_cpu_byte_tensor(state['global_torch']))
    ds_train.rng.setstate(state['dataset_train'])
    ds_val.rng.setstate(state['dataset_val'])
    if torch.cuda.is_available() and 'cuda' in state:
        cuda_states = [_as_cpu_byte_tensor(s) for s in state['cuda']]
        if len(cuda_states) == torch.cuda.device_count():
            torch.cuda.set_rng_state_all(cuda_states)


def main():
    ap = argparse.ArgumentParser(description='Phase-14 clean-v3 regional refiner (OPTION_A3).')
    ap.add_argument('--resume', action='store_true',
                    help='Resume from latest.pt if present (execution-mechanism recovery only; '
                         'restores full optimizer/scheduler/scaler and RNG state for bit-exact continuation).')
    args = ap.parse_args()

    seed = 42
    torch.manual_seed(seed)
    np.random.seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    device = get_device(require_cuda=True)
    print(f"Device: {device}")

    # Datasets
    # Role-resolved margins (reports/audits/phase14_roi_margin_role_resolution.json):
    # the refiner's oracle-derived TRAIN and crop-level VAL crops use
    # ORACLE_DERIVED_REFINER_MARGIN; the predicted-proposal margin is a separate,
    # downstream, frozen contract value and is never used for crop construction.
    ds_train = RegionalCropDataset(
        PROJECT_ROOT / 'manifests/phase4_v3/train.csv',
        split='TRAIN', target_size=256, margin=ORACLE_DERIVED_REFINER_MARGIN, seed=seed
    )
    ds_val = RegionalCropDataset(
        PROJECT_ROOT / 'manifests/phase4_v3/val.csv',
        split='VAL', target_size=256, margin=ORACLE_DERIVED_REFINER_MARGIN, seed=seed
    )
    print(f"Train items: {len(ds_train)} | Val items: {len(ds_val)}")
    print(f"Crop margin (oracle-derived refiner): {ORACLE_DERIVED_REFINER_MARGIN}")
    print(f"Predicted proposal margin (downstream, frozen): {PREDICTED_PROPOSAL_MARGIN}")
    assert abs(ds_train.margin - ORACLE_DERIVED_REFINER_MARGIN) < 1e-12, "TRAIN margin role mismatch"
    assert abs(ds_val.margin - ORACLE_DERIVED_REFINER_MARGIN) < 1e-12, "VAL margin role mismatch"

    loader_train = DataLoader(ds_train, batch_size=8, shuffle=True, num_workers=0, pin_memory=True)
    loader_val = DataLoader(ds_val, batch_size=8, shuffle=False, num_workers=0, pin_memory=True)

    # Model
    model = UNet(in_channels=1, out_channels=1, base_channels=32).to(device)
    print(f"Model params: {sum(p.numel() for p in model.parameters() if p.requires_grad):,}")

    # Loss, optimizer, scheduler
    criterion = BCEDiceLoss(bce_weight=0.5, dice_weight=0.5, epsilon=1e-6)
    optimizer = AdamW(model.parameters(), lr=1e-4, weight_decay=1e-4)
    scheduler = CosineAnnealingLR(optimizer, T_max=100)
    scaler = torch.amp.GradScaler('cuda') if torch.cuda.is_available() else None

    # Early stopping state
    best_val_dice = -1.0
    best_epoch = 0
    bad_epochs = 0
    patience = 15
    history = []
    start_epoch = 1
    resume_source = None
    run_start = time.time()

    # Durable run log: unbuffered, flushed per line, with cumulative elapsed.
    run_log_path = PROJECT_ROOT / 'logs' / f'{EXPERIMENT_ID}.run.log'
    run_log_path.parent.mkdir(parents=True, exist_ok=True)
    run_log = open(run_log_path, 'a', encoding='utf-8', buffering=1)

    def log(msg):
        line = f"[{time.strftime('%Y-%m-%dT%H:%M:%S')}] +{time.time() - run_start:9.1f}s {msg}"
        print(line)
        run_log.write(line + '\n')
        run_log.flush()
        sys.stdout.flush()

    # --- Resume (execution-mechanism recovery only) --------------------------
    # Restores model/optimizer/scheduler/scaler AND all RNG state, so the
    # continuation is bit-exact with respect to the interrupted trajectory.
    # No scientific parameter is affected by resuming.
    if args.resume:
        latest_path = CHECKPOINT_DIR / 'latest.pt'
        if latest_path.exists():
            ck = torch.load(latest_path, map_location=device, weights_only=False)
            model.load_state_dict(ck['model_state'])
            optimizer.load_state_dict(ck['optimizer_state'])
            scheduler.load_state_dict(ck['scheduler_state'])
            if scaler is not None and ck.get('grad_scaler_state'):
                scaler.load_state_dict(ck['grad_scaler_state'])
            best_val_dice = float(ck['best_val_crop_dice'])
            best_epoch = int(ck.get('best_epoch', ck['epoch']))
            bad_epochs = int(ck.get('bad_epochs', 0))
            start_epoch = int(ck['epoch']) + 1
            if 'rng_state' in ck:
                restore_rng_state(ck['rng_state'], ds_train, ds_val)
                rng_restored = True
            else:
                rng_restored = False
            hist_path = EXPERIMENT_DIR / 'history.csv'
            if hist_path.exists():
                history = pd.read_csv(hist_path).to_dict('records')
            resume_source = str(latest_path)
            log(f"RESUME loaded={resume_source} from_epoch={ck['epoch']} next_epoch={start_epoch} "
                f"best_val_crop_dice={best_val_dice:.6f} best_epoch={best_epoch} bad_epochs={bad_epochs} "
                f"rng_state_restored={rng_restored} history_rows={len(history)}")
            if not rng_restored:
                raise RuntimeError("REFUSING to resume without RNG state: continuation would not be "
                                   "bit-exact. Checkpoint predates RNG persistence.")
        else:
            log("RESUME requested but no latest.pt found; starting from epoch 1")

    log(f"RUN START experiment={EXPERIMENT_ID} seed={seed} device={device} "
        f"start_epoch={start_epoch} resumed={resume_source is not None}")
    log(f"ROLE MARGINS trainer_crop={ORACLE_DERIVED_REFINER_MARGIN} predicted_proposal={PREDICTED_PROPOSAL_MARGIN}")

    config = {
        'experiment_id': EXPERIMENT_ID,
        'model': {'name': 'UNet', 'in_channels': 1, 'out_channels': 1, 'base_channels': 32},
        'loss': {'name': 'BCEDiceLoss', 'bce_weight': 0.5, 'dice_weight': 0.5, 'epsilon': 1e-6},
        'optimizer': {'name': 'AdamW', 'lr': 1e-4, 'weight_decay': 1e-4},
        'scheduler': {'name': 'CosineAnnealingLR', 'T_max': 100},
        'training': {'batch_size': 8, 'seed': seed, 'max_epochs': 100, 'early_stopping_patience': 15,
                     'checkpoint_metric': 'val_crop_dice', 'amp': True},
        'dataset': {'train_manifest': 'manifests/phase4_v3/train.csv',
                    'val_manifest': 'manifests/phase4_v3/val.csv',
                    'target_size': 256, 'option': 'A3',
                    'margin': ORACLE_DERIVED_REFINER_MARGIN,
                    'margin_role': 'ORACLE_DERIVED_REFINER_TRAIN_VAL_CROP_CONSTRUCTION',
                    'predicted_proposal_margin': PREDICTED_PROPOSAL_MARGIN,
                    'margin_resolution_artifact': 'reports/audits/phase14_roi_margin_role_resolution.json'},
    }

    for epoch in range(start_epoch, 101):
        t0 = time.time()
        train_loss = train_epoch(model, loader_train, criterion, optimizer, scaler, device)
        val_loss, val_dice = validate(model, loader_val, criterion, device)
        scheduler.step()
        elapsed = time.time() - t0

        is_new_best = val_dice > best_val_dice
        if is_new_best:
            best_val_dice = val_dice
            best_epoch = epoch
            bad_epochs = 0
        else:
            bad_epochs += 1

        row = {
            'epoch': epoch,
            'train_loss': train_loss,
            'val_loss': val_loss,
            'val_crop_dice': val_dice,
            'learning_rate': optimizer.param_groups[0]['lr'],
            'is_new_best': is_new_best,
            'best_epoch_so_far': best_epoch,
            'bad_epochs': bad_epochs,
            'elapsed_seconds': elapsed,
            'cumulative_elapsed_seconds': time.time() - run_start,
        }
        history.append(row)
        log(f"EPOCH {epoch:03d} train_loss={train_loss:.4f} val_loss={val_loss:.4f} "
            f"val_dice={val_dice:.6f} best_epoch={best_epoch} bad={bad_epochs} "
            f"lr={optimizer.param_groups[0]['lr']:.6f} epoch_s={elapsed:.1f}")

        # Durable logging: persist history after EVERY epoch so that an
        # externally terminated process still leaves a complete, readable
        # per-epoch record on disk. The predecessor implementation wrote
        # history.csv only after the loop completed, so an external stop left
        # no training history at all.
        pd.DataFrame(history).to_csv(EXPERIMENT_DIR / 'history.csv', index=False)

        # Save checkpoint
        ckpt = {
            'model_state': model.state_dict(),
            'optimizer_state': optimizer.state_dict(),
            'scheduler_state': scheduler.state_dict(),
            'grad_scaler_state': scaler.state_dict() if scaler else None,
            'epoch': epoch,
            'best_val_crop_dice': best_val_dice,
            'best_epoch': best_epoch,
            'bad_epochs': bad_epochs,
            'rng_state': capture_rng_state(ds_train, ds_val),
            'configuration': config,
            'seed': seed,
            'experiment_id': EXPERIMENT_ID,
        }
        latest_path = CHECKPOINT_DIR / 'latest.pt'
        torch.save(ckpt, latest_path)
        if is_new_best:
            best_path = CHECKPOINT_DIR / 'best.pt'
            torch.save(ckpt, best_path)
            print(f"  -> Saved new best checkpoint (val_dice={val_dice:.6f})")

        # Early stopping
        if bad_epochs >= patience:
            log(f"EARLY STOPPING at epoch {epoch} (patience={patience})")
            break

    # Save history (also written incrementally above; this is the final flush)
    df = pd.DataFrame(history)
    df.to_csv(EXPERIMENT_DIR / 'history.csv', index=False)

    # Write closure summary
    closure = {
        'experiment_id': EXPERIMENT_ID,
        'best_epoch': best_epoch,
        'best_val_crop_dice': best_val_dice,
        'total_epochs': epoch,
        'stop_reason': 'EARLY_STOPPING_PATIENCE_15' if bad_epochs >= patience else 'MAX_EPOCHS',
        'best_checkpoint_sha256': sha_file(CHECKPOINT_DIR / 'best.pt'),
        'latest_checkpoint_sha256': sha_file(CHECKPOINT_DIR / 'latest.pt'),
        'history_sha256': sha_file(EXPERIMENT_DIR / 'history.csv'),
        'crop_margin': ORACLE_DERIVED_REFINER_MARGIN,
        'crop_margin_role': 'ORACLE_DERIVED_REFINER_TRAIN_VAL_CROP_CONSTRUCTION',
        'predicted_proposal_margin': PREDICTED_PROPOSAL_MARGIN,
        'margin_resolution_artifact': 'reports/audits/phase14_roi_margin_role_resolution.json',
        'total_elapsed_seconds': time.time() - run_start,
        'history_written_incrementally': True,
        'start_epoch': start_epoch,
        'resumed': resume_source is not None,
        'resume_source': resume_source,
        'rng_state_persisted_in_checkpoints': True,
    }
    json.dump(closure, open(EXPERIMENT_DIR / 'closure.json', 'w', encoding='utf-8'), indent=2)
    log(f"TRAINING COMPLETE best_epoch={best_epoch} best_val_crop_dice={best_val_dice:.6f} "
        f"total_epochs={epoch} stop_reason={closure['stop_reason']}")
    run_log.close()


if __name__ == '__main__':
    main()
