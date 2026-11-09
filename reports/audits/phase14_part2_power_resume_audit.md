# Phase 14 Part 2R — Power Interruption Recovery Audit

**Experiment ID:** `phase14_diag_regional_unet_oracletrain_a3_seed42_v1`  
**Power Interruption:** YES  
**Last Completed Epoch Before Interruption:** 25  
**First New Epoch:** 26  
**Resume Mode:** `SAME_EXPERIMENT` (Resuming from `latest.pt`)

## 1. Checkpoint & History Pre-Resume Consistency Check
- **`latest.pt` SHA-256 (pre-resume):** `5a39cde21ee8e61f78f94b72006d9e15b1d3c675c02ce87912670d03f695ee22`
- **`best.pt` SHA-256 (pre-resume):** `89ada72700385ed56b49b6caf34d9061349c24a566794176911b83fb0c8cd9f0`
- **History Last Completed Epoch:** 25
- **`latest.pt` Completed Epoch:** 25
- **`best.pt` Best Epoch:** 14
- **History Best Epoch:** 14
- **Best Validation Crop Dice:** `0.8437233057743712` (consistent across `best.pt`, `latest.pt`, and `history.csv`)
- **Early Stopping Bad Epochs at Epoch 25:** 11 / 15 (consistent across `latest.pt` and `history.csv`)
- **Optimizer State:** RESTORABLE (valid state dict present in `latest.pt`)
- **Scheduler State:** RESTORABLE (`last_epoch: 25`, LR for epoch 26 = `8.53553e-05`)
- **GradScaler State:** RESTORABLE
- **RNG State:** RESTORABLE (`python`, `numpy`, `torch_cpu`, `torch_cuda`)
- **Global Step:** 15725
- **Active Trainer Processes:** 0

## 2. Recovery Rules & Continuity
- **Experiment ID Changed:** NO
- **Configuration Changed:** NO
- **Early Stopping Reset:** NO (continues at `bad_epochs = 11`)
- **Scheduler Reset:** NO (continues at `last_epoch = 25`)
- **History Overwritten:** NO (epochs 1–25 preserved; new epochs appended starting at 26)
- **Status:** READY FOR RESUMPTION

