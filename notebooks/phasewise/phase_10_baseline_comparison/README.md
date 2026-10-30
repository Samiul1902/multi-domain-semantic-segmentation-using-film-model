# Phase 10 — CLEAN-v3 KUB Baseline Comparison

## Current Phase-10 state: PHASE 10 COMPLETE

**UNet, Attention U-Net, UNet++, and DeepLabV3+ have ALL been rerun under `phase4_v3`, and
the final four-model cross-model comparison is COMPLETE** — delivered by
`phase10_clean_v3_final_baseline_comparison.ipynb`.

**PHASE 10 IS COMPLETE.** No winner is declared; no significance testing performed.

| Model | clean-v3 run | Status |
|---|---|---|
| UNet (Phase 09) | `phase9_kub_unet_baseline_seed42_512_clean_v3` | COMPLETE |
| Attention U-Net (Part 1A) | `phase10_kub_attention_unet_seed42_512_clean_v3` | COMPLETE |
| UNet++ (Part 1B) | `phase10_kub_unetpp_seed42_512_clean_v3` | COMPLETE |
| DeepLabV3+ (Part 1C) | `phase10_kub_deeplabv3plus_seed42_512_clean_v3` | COMPLETE |
| Final four-model comparison | `phase10_clean_v3_final_baseline_comparison.ipynb` | COMPLETE |

> **Winner: NOT DECLARED.** All four runs are **single-seed (42) descriptive VAL evidence**.
> No significance testing has been performed (Phase 29 / Phase 31 have not run).
> **TEST remains LOCKED until Phase 39.**

---

## Part 1A — Attention U-Net CLEAN-v3 scientific training (COMPLETE)

Executed by the canonical runner:

```
notebooks/phasewise/phase_10_clean_v3_comparison/code/train_phase10_attention_unet_clean_v3.py
```

This runner is frozen execution provenance. Do not modify it.

**Experiment:** `phase10_kub_attention_unet_seed42_512_clean_v3`

| Property | Value |
|----------|-------|
| Manifest | `phase4_v3` |
| Taxonomy | `kub_size_clean_v3_v1` |
| Architecture | `attention_unet` (base_channels=32, ~7.85M params) |
| Epochs completed | 69 |
| Best epoch | 54 |
| Best VAL macro Dice | 0.7525129853960107 |
| Best VAL macro IoU | 0.6349387691368995 |
| Best VAL Precision | 0.7729140812402236 |
| Best VAL Recall | 0.7922248481868364 |
| Final epoch | 69 |
| Stop reason | EARLY_STOP (bad_epochs=15) |

### Artifacts
- `configs/phase10_clean_v3/phase10_attention_unet_clean_v3.yaml`
- `checkpoints/phase10_kub_attention_unet_seed42_512_clean_v3/{best.pt,latest.pt}`
- `experiments/phase10_kub_attention_unet_seed42_512_clean_v3/{history.csv,training.log}`
- `reports/audits/phase10_attention_unet_clean_v3_training_{start,completion}_audit.{json,md}`
- `reports/tables/phase10_attention_unet_v2_to_clean_v3_protocol_diff.csv`
- `reports/figures/phase10_attention_unet_clean_v3_training_curves.png`

## Part 1A-R1 — Reviewer notebook / packaging (THIS DIRECTORY)

- **Reviewer notebook:** `phase10_attention_unet_clean_v3_training_review.ipynb`
- **Support code:** `code/phase10_attention_unet_review.py`
- **Code README:** `code/README.md`

Read-only review of the completed run. Does not train. TEST locked.

## Part 1B — UNet++ CLEAN-v3 scientific training + reviewer package (COMPLETE)

Executed by the canonical runner:

```
notebooks/phasewise/phase_10_clean_v3_comparison/code/train_phase10_unetpp_clean_v3.py
```

**Experiment:** `phase10_kub_unetpp_seed42_512_clean_v3`
**Architecture:** `unetpp_nested_4_level_no_deep_supervision` (deep supervision OFF, ~9.16M params)

| Property | Value |
|----------|-------|
| Epochs completed | 85 |
| Best epoch | 70 |
| Best VAL macro Dice | 0.7641595156062713 |
| Best VAL macro IoU | 0.6525442690586191 |
| Best VAL Precision | 0.7996825971468945 |
| Best VAL Recall | 0.7912384169561990 |
| Final epoch | 85 |
| Stop reason | EARLY_STOP (bad_epochs=15) |

- Reviewer notebook: `phase10_unetpp_clean_v3_training_review.ipynb`
- Support code: `code/phase10_unetpp_review.py`
- Gallery: the **same frozen 16-case KUB VAL selection** as UNet and Attention U-Net
  (canonical SHA `10ad09cb...`), so all three models are paired sample-for-sample.

## Part 1C — DeepLabV3+ CLEAN-v3 scientific training + reviewer package (COMPLETE)

Executed by the canonical runner:

```
notebooks/phasewise/phase_10_clean_v3_comparison/code/train_phase10_deeplabv3plus_clean_v3.py
```

**Experiment:** `phase10_kub_deeplabv3plus_seed42_512_clean_v3`
**Architecture:** `deeplabv3plus_resnet50_os16` — ResNet-50 backbone, **no pretrained
weights**, output stride 16, ASPP rates (6,12,18) + image pooling, no auxiliary head,
**40,340,769 parameters** (proven by instantiating the model and loading the historical
state-dict with zero missing/unexpected keys).

| Property | Value |
|----------|-------|
| Epochs completed | 67 |
| Best epoch | 52 |
| Best VAL macro Dice | 0.7509140344161673 |
| Best VAL macro IoU | 0.6460492792430865 |
| Best VAL Precision | 0.7943328495850855 |
| Best VAL Recall | 0.7822983241135557 |
| Final epoch | 67 |
| Stop reason | EARLY_STOP (bad_epochs=15) |

- Reviewer notebook: `phase10_deeplabv3plus_clean_v3_training_review.ipynb`
- Support code: `code/phase10_deeplabv3plus_review.py`
- **Complete epoch-by-epoch table** (67 rows, one per epoch, untruncated) rendered in the
  notebook and saved to
  `reports/tables/phase10_deeplabv3plus_clean_v3_epoch_results.csv` — per the new canonical
  per-epoch notebook rule.
- Gallery: the **same frozen 16-case KUB VAL selection** (canonical SHA `10ad09cb...`)
  shared with UNet, Attention U-Net, and UNet++.

> Note: config carries `base_channels: 32` for factory-signature compatibility, but
> `DeepLabV3Plus` deletes it (canonical decoder width is 256). This is expected, not a defect.

## FINAL STATE

| Item | Status |
|------|--------|
| UNet | **COMPLETE** |
| Attention U-Net | **COMPLETE** |
| UNet++ | **COMPLETE** |
| DeepLabV3+ | **COMPLETE** |
| Final four-model comparison | **COMPLETE** |
| Winner | **NOT DECLARED** |
| Statistical significance | **NOT TESTED** |
| TEST | **LOCKED (Phase 39)** |
| Phase 11 | **NOT STARTED** |
| Next | **WAIT_FOR_SUPERVISOR_PHASE11_AUTHORIZATION** |

**PHASE 10 CLEAN-v3 BASELINE COMPARISON: COMPLETE.**

**No winner is declared.** All four architectures have clean-v3 runs, but they are
single-seed (42) and descriptive; no significance testing has been performed (Phase 29 /
Phase 31 have not run), so no ranking or superiority claim is scientifically valid.

| Model | clean-v3 VAL Dice (single-seed, descriptive, NOT ranked) |
|---|---|
| UNet | 0.7406133413314819 |
| Attention U-Net | 0.7525129853960107 |
| UNet++ | 0.7641595156062713 |
| DeepLabV3+ | 0.7509140344161673 |

## Provenance notes

- Historical v2 Attention U-Net (`phase10_kub_attention_unet_seed42_512`) is immutable and
  used only for protocol reconstruction and historical separation.
- The old notebook `phase10_baseline_model_comparison_and_visual_analysis.ipynb` in this
  directory is historical v2 evidence and is NOT modified by Part 1A/1A-R1.
- TEST is locked: TEST reads = 0.
