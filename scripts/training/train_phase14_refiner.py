"""Phase 14 Regional Refiner Diagnostic - Single Frozen Training Run.
Experiment: phase14_diag_regional_unet_oracletrain_a3_seed42_v1
"""
import os
import sys
import time
import json
from pathlib import Path
import random
import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.models.unet import UNet
from src.losses.segmentation import BCEDiceLoss
from src.data.regional_dataset import RegionalCropDataset
from src.utils.checkpointing import save_training_checkpoint, load_training_checkpoint
from src.utils.manifest_guard import verify_manifests
from src.utils.test_lock import verify_test_lock
from src.utils.reproducibility import set_seed, make_generator, seed_worker

def main():
    print("=== Phase 14 Regional Refiner Training ===")
    
    # 1. Interpreter & CUDA check
    expected_exe = Path(r"D:\Softfors\jup\.venv\Scripts\python.exe").resolve()
    actual_exe = Path(sys.executable).resolve()
    assert actual_exe == expected_exe, f"Wrong python interpreter: {actual_exe}"
    
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required but not available!")
    
    device = torch.device('cuda')
    gpu_name = torch.cuda.get_device_name(0)
    print(f"Python: {sys.version.split()[0]}")
    print(f"PyTorch: {torch.__version__}, CUDA runtime: {torch.version.cuda}")
    print(f"GPU: {gpu_name}")
    assert "3060" in gpu_name, f"Expected RTX 3060 Ti, got {gpu_name}"
    
    # 2. Governance verification
    verify_manifests()
    verify_test_lock(PROJECT_ROOT)
    print("Governance locks verified: TEST content not accessed, external blocked.")
    
    # 3. Seed & Reproducibility
    seed = 42
    set_seed(seed, deterministic=True)
    generator = make_generator(seed)
    
    # 4. Datasets
    print("Loading datasets...")
    train_ds = RegionalCropDataset(str(PROJECT_ROOT / 'manifests/train.csv'), 'TRAIN', seed=seed)
    val_ds = RegionalCropDataset(str(PROJECT_ROOT / 'manifests/val.csv'), 'VAL', seed=seed)
    
    assert len(train_ds) == 5028, f"Expected 5028 train examples, got {len(train_ds)}"
    assert len(val_ds) == 156, f"Expected 156 oracle val crops, got {len(val_ds)}"
    print(f"Train dataset: {len(train_ds)} crops (1162 base + 2324 perturbed + 1542 negatives)")
    print(f"Val dataset: {len(val_ds)} oracle crops")
    
    train_loader = DataLoader(
        train_ds, batch_size=8, shuffle=True, num_workers=0,
        pin_memory=True, worker_init_fn=seed_worker, generator=generator
    )
    val_loader = DataLoader(
        val_ds, batch_size=8, shuffle=False, num_workers=0,
        pin_memory=True, worker_init_fn=seed_worker, generator=make_generator(seed)
    )
    
    # 5. Model
    model = UNet(in_channels=1, out_channels=1, base_channels=32).to(device)
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Model parameters: {trainable_params}")
    assert trainable_params == 7762465, f"Expected 7762465 params, got {trainable_params}"
    
    # 6. Loss, Optimizer, Scheduler, Scaler
    loss_fn = BCEDiceLoss(bce_weight=0.5, dice_weight=0.5, epsilon=1e-6)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=100)
    scaler = torch.amp.GradScaler('cuda')
    
    # 7. Checkpoint Paths
    exp_id = "phase14_diag_regional_unet_oracletrain_a3_seed42_v1"
    chk_dir = PROJECT_ROOT / "checkpoints" / exp_id
    chk_dir.mkdir(parents=True, exist_ok=True)
    best_ckpt_path = chk_dir / "best.pt"
    latest_ckpt_path = chk_dir / "latest.pt"
    history_csv_path = chk_dir / "history.csv"
    config_json_path = chk_dir / "config.json"
    
    config_data = {
        "experiment_id": exp_id,
        "phase": 14,
        "dataset": "KUB",
        "population": "FULL_FIELD",
        "train_samples": 771,
        "train_components": 1162,
        "val_samples": 106,
        "val_components": 156,
        "train_crops": 5028,
        "val_crops": 156,
        "architecture": "UNet",
        "in_channels": 1,
        "out_channels": 1,
        "base_channels": 32,
        "trainable_params": trainable_params,
        "resolution": 256,
        "margin": 0.20,
        "optimizer": "AdamW",
        "lr": 1e-4,
        "weight_decay": 1e-4,
        "scheduler": "CosineAnnealingLR",
        "scheduler_t_max": 100,
        "loss": "0.5_BCE + 0.5_SoftDice",
        "batch_size": 8,
        "amp": True,
        "seed": 42,
        "max_epochs": 100,
        "patience": 15,
        "checkpoint_metric": "best_val_crop_dice"
    }
    with open(config_json_path, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=2)
        
    manifest_hashes = json.loads((PROJECT_ROOT / "manifests/manifest_metadata.json").read_text(encoding='utf-8'))['hashes']
    
    # Check for resumption
    start_epoch = 1
    history = []
    best_val_crop_dice = -1.0
    best_epoch = 0
    bad_epochs = 0
    global_step = 0
    
    if latest_ckpt_path.exists():
        print(f"Resuming from existing latest checkpoint: {latest_ckpt_path}")
        state = load_training_checkpoint(latest_ckpt_path, model, optimizer, scheduler, scaler, True, device)
        start_epoch = state['epoch'] + 1
        history = state.get('training_history', [])
        best_val_crop_dice = state.get('best_validation_score', -1.0)
        early = state.get('early_stopping_state', {})
        bad_epochs = int(early.get('bad_epochs', 0))
        best_epoch = int(early.get('best_epoch', start_epoch - 1))
        global_step = state.get('global_step', 0)
        gen_states = state.get('loader_generator_states')
        if gen_states and 'train' in gen_states and gen_states['train'] is not None:
            generator.set_state(gen_states['train'].detach().cpu().to(torch.uint8))
        print(f"Resumed at epoch {start_epoch}, best score: {best_val_crop_dice:.6f} (epoch {best_epoch}), bad_epochs: {bad_epochs}")
    
    # 8. Training Loop
    max_epochs = 100
    patience = 15
    stop_reason = "MAX_EPOCHS_REACHED"
    
    print(f"\n--- Starting Training (Epochs {start_epoch} to {max_epochs}, Patience {patience}) ---")
    
    for epoch in range(start_epoch, max_epochs + 1):
        epoch_start_time = time.perf_counter()
        torch.cuda.reset_peak_memory_stats()
        
        # --- Train Phase ---
        model.train()
        train_losses = []
        
        for batch_idx, batch in enumerate(train_loader):
            images = batch['image'].to(device, non_blocking=True)
            masks = batch['mask'].to(device, non_blocking=True)
            
            optimizer.zero_grad(set_to_none=True)
            with torch.amp.autocast('cuda'):
                logits = model(images)
                loss = loss_fn(logits, masks)
                
            if not torch.isfinite(loss):
                raise RuntimeError(f"Non-finite loss encountered at epoch {epoch}, batch {batch_idx}: {loss.item()}")
                
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            
            train_losses.append(loss.item())
            global_step += 1
            
        avg_train_loss = float(np.mean(train_losses))
        
        # --- Validation Phase (Oracle VAL crops) ---
        model.eval()
        val_dices = []
        
        with torch.inference_mode():
            for batch in val_loader:
                images = batch['image'].to(device, non_blocking=True)
                masks = batch['mask'].to(device, non_blocking=True)
                
                with torch.amp.autocast('cuda'):
                    logits = model(images)
                    preds = (torch.sigmoid(logits) >= 0.50).float()
                    
                # Compute per-crop Dice
                for p, t in zip(preds, masks):
                    intersection = (p * t).sum().item()
                    total = p.sum().item() + t.sum().item()
                    if total == 0:
                        crop_dice = 1.0
                    else:
                        crop_dice = (2.0 * intersection + 1e-7) / (total + 1e-7)
                    val_dices.append(crop_dice)
                    
        avg_val_crop_dice = float(np.mean(val_dices))
        
        # --- Scheduler Step (per epoch) ---
        current_lr = optimizer.param_groups[0]['lr']
        scheduler.step()
        
        # --- Tracking & Early Stopping ---
        improved = avg_val_crop_dice > best_val_crop_dice
        if improved:
            best_val_crop_dice = avg_val_crop_dice
            best_epoch = epoch
            bad_epochs = 0
        else:
            bad_epochs += 1
            
        elapsed_sec = time.perf_counter() - epoch_start_time
        peak_vram = torch.cuda.max_memory_allocated() / (1024**2)
        
        epoch_record = {
            "epoch": epoch,
            "train_loss": avg_train_loss,
            "val_crop_dice": avg_val_crop_dice,
            "learning_rate": current_lr,
            "elapsed_seconds": elapsed_sec,
            "peak_vram_mb": peak_vram,
            "best_val_crop_dice": best_val_crop_dice,
            "best_epoch": best_epoch,
            "bad_epochs": bad_epochs,
            "improved": improved
        }
        history.append(epoch_record)
        
        # Print progress
        print(f"Epoch {epoch:03d}/{max_epochs:03d} | Train Loss: {avg_train_loss:.4f} | Val Crop Dice: {avg_val_crop_dice:.4f} "
              f"| Best: {best_val_crop_dice:.4f} (ep {best_epoch}) | Bad: {bad_epochs}/{patience} | LR: {current_lr:.2e} | Time: {elapsed_sec:.1f}s")
        
        # Save checkpoints
        early_state = {
            "best_score": best_val_crop_dice,
            "best_epoch": best_epoch,
            "bad_epochs": bad_epochs,
            "patience": patience,
            "stopped": bad_epochs >= patience
        }
        
        common_args = (
            model, optimizer, scheduler, scaler, epoch, global_step,
            best_val_crop_dice, config_data, seed, history,
            "phase14_v1", manifest_hashes, exp_id, "unet", 256, 0.50
        )
        
        gen_state_dict = {'train': generator.get_state()}
        save_training_checkpoint(latest_ckpt_path, *common_args, early_stopping_state=early_state, loader_generator_states=gen_state_dict)
        if improved:
            save_training_checkpoint(best_ckpt_path, *common_args, early_stopping_state=early_state, loader_generator_states=gen_state_dict)
            print(f"  --> Saved new best checkpoint at epoch {epoch} (Val Crop Dice: {best_val_crop_dice:.4f})")
            
        # Update history.csv
        pd.DataFrame(history).to_csv(history_csv_path, index=False)
        
        # Early stop check
        if bad_epochs >= patience:
            print(f"\nEarly stopping triggered: no improvement for {patience} consecutive epochs.")
            stop_reason = f"EARLY_STOPPING_PATIENCE_{patience}"
            break
            
    print("\n=== Training Complete ===")
    print(f"Final Epoch: {history[-1]['epoch']}")
    print(f"Stop Reason: {stop_reason}")
    print(f"Best Epoch: {best_epoch}")
    print(f"Best Val Crop Dice: {best_val_crop_dice:.6f}")
    print(f"Best Checkpoint: {best_ckpt_path}")
    print(f"Latest Checkpoint: {latest_ckpt_path}")

if __name__ == '__main__':
    main()

