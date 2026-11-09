# Phase 10 CLEAN-v3 Final Four-Model Comparison Audit

## Models

| Model | Experiment | Best ep | Epochs | VAL Dice |
|---|---|---|---|---|
| UNet | `phase9_kub_unet_baseline_seed42_512_clean_v3` | 44 | 59 | 0.7406133413314819 |
| Attention U-Net | `phase10_kub_attention_unet_seed42_512_clean_v3` | 54 | 69 | 0.7525129853960107 |
| UNet++ | `phase10_kub_unetpp_seed42_512_clean_v3` | 70 | 85 | 0.7641595156062713 |
| DeepLabV3+ | `phase10_kub_deeplabv3plus_seed42_512_clean_v3` | 52 | 67 | 0.7509140344161673 |

## Immutability

- All four runs config/history/best/latest verified: **True**

## Complete epoch tables

| Model | Rows | Missing | Duplicates | Improvements | Integrity |
|---|---|---|---|---|---|
| UNet | 59 | [] | [] | 21 | PASS |
| Attention U-Net | 69 | [] | [] | 24 | PASS |
| UNet++ | 85 | [] | [] | 21 | PASS |
| DeepLabV3+ | 67 | [] | [] | 23 | PASS |

- Combined MODEL_EPOCH long table rows: **280** (59+69+85+67), distinct from 280 VAL cases

## Paired inference

- Paired KUB VAL rows: **280** · KUB-only: true · all four models per case: true
- Category: Bladder 144 / Kidney 112 / Ureteric 24 · Acquisition: ROI 177 / FULL_FIELD 103

## Aggregate reproduction

- UNet: abs_diff=1.215e-07 · strict 1e-6 PASS · material 1e-4 PASS
- Attention U-Net: abs_diff=1.888e-05 · strict 1e-6 FAIL · material 1e-4 PASS
- UNet++: abs_diff=6.497e-07 · strict 1e-6 PASS · material 1e-4 PASS
- DeepLabV3+: abs_diff=5.145e-06 · strict 1e-6 FAIL · material 1e-4 PASS

> Residuals at 1e-6..1e-5 for two models arise from AMP fp16 batch-shape differences (training-time validation batch=4 vs paired re-inference batch=1); these are floating-point rounding, not metric differences. An earlier 1e-3-level discrepancy caused by using int() instead of round() for the resized extent was found and corrected.

## Governance

- TEST reads/metrics/visualizations: **0** · training performed: **false** (0 steps, 0 epochs)
- Statistical testing: **False** · Winner declared: **False**
- Phase 11 started: **False**
- README stale heading repaired: **True**
- DeepLabV3+ canonical improvement events: **23** (Part-1C pasted note value 24 = SUPERSEDED_REPORTING_NOTE_ONLY)

## Status: PASS