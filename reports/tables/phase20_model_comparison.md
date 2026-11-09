# Phase 20 — Model Comparison (class / subclass + completed-model standings)

**Status snapshot:** 2026-09-27 14:40 (GMT+6)
**Scope:** Phase 20A (UNet++, pre-existing) + Phase 20B (four conventional baselines, sequential).
**Protocol:** identical frozen Phase-20 protocol for all five — one shared parameter set,
`task_id` never passed to the model, seed 42, 512 px, AdamW lr 1e-4, cosine T_max=100,
BCE+Dice 0.5/0.5, macro-domain mean VAL Dice selection, patience 15, max 100 epochs.

> **Governance note.** All figures below are VAL-set only. TEST content reads remain **0** for
> every model. Nothing in the frozen protocol, the `phase20b_*_architecture_binding.json`, or the
> `phase20b_*_pre_execution_check.json` files was modified. Metrics are quoted from each
> experiment's own `closure.json`; no re-evaluation or inference replay was performed.

## 1. Architecture classes and subclasses

The four Phase-20B models are all registered in `MODEL_REGISTRY`
(`scripts/training/train_phase20b_shared_baseline.py`). Each maps to exactly one top-level
`torch.nn.Module` subclass, plus its own internal helper subclasses:

| model key | top-level class | source file | internal subclasses | architecture id |
|---|---|---|---|---|
| `unet` | `UNet` | `src/models/unet.py` | `DoubleConv(nn.Sequential)` | `unet_4_stage_plain_skip_base32` |
| `attention_unet` | `AttentionUNet` | `src/models/attention_unet.py` | `AttentionGate(nn.Module)` | `attention_unet_4_stage_additive_skip_gates_base32` |
| `deeplabv3plus` | `DeepLabV3Plus` | `src/models/deeplabv3plus.py` | `ASPP`, `ASPPConv(nn.Sequential)`, `ASPPPooling(nn.Sequential)` | `deeplabv3plus_resnet50_os16_random_init_no_pretrained_aspp_rates_6_12_18` |
| `transformer_mit_unet` | `TransformerMiTUNet` | `src/models/transformer_mit_unet.py` | `OverlapPatchEmbed`, `EfficientSelfAttention`, `MixFFN`, `TransformerBlock`, `MiTStage` | `transformer_mit_style_unet_local_random_init` |

Notes on the two non-trivial entries:

- **`deeplabv3plus`** — architecture id explicitly records `random_init_no_pretrained`. It must
  never be described as an ImageNet-pretrained ResNet-50 backbone. ASPP dilation rates are
  `6, 12, 18`, output stride 16.
- **`transformer_mit_unet`** — source file carries
  `LOCAL_RANDOM_INIT__NOT_OFFICIAL_PRETRAINED_MIT_B1`. It is a MiT-style design with widths
  `[64, 128, 320, 512]` at `base_channels=32`, **not** official pretrained MiT-B1. No
  `timm` / `transformers` / `segmentation_models_pytorch` / `einops` dependency is used.

`TransformerMiTUNet` currently has `class: null` in the in-memory registry because the class is
resolved lazily from the module at instantiation — this is a registry bookkeeping detail, not a
missing implementation (the trainer instantiates it successfully).

## 2. Completed models — head-to-head

Ranked by macro-domain mean VAL Dice at each model's own best epoch.

| rank | model | class | params | best epoch | **macro Dice** | final epoch | stop |
|---|---|---|---|---|---|---|---|
| 1 | U-Net++ (20A) | `UNetPP` | 9,159,681 | 55 | **0.792007** | 70 | EARLY_STOPPING_PATIENCE |

> Class/architecture strings for U-Net++ are taken from `src/models/unetpp.py` and the Phase-20A
> record. Its `closure.json` predates the 20B schema and does **not** carry
> `architecture` / `model_class` / `model_source_file` fields (they read `None`); only
> `model_params`, `best_epoch`, `best_macro_domain_dice`, `final_epoch`, `stop_reason`, and
> `per_domain_dice_at_best` are populated.
| 2 | Attention U-Net | `AttentionUNet` | 7,851,285 | 64 | **0.789039** | 79 | EARLY_STOPPING_PATIENCE |
| 3 | U-Net | `UNet` | 7,763,041 | 74 | **0.787833** | 89 | EARLY_STOPPING_PATIENCE |

**Spread across the top three is 0.004174 Dice (~0.42 pp)** — effectively a three-way tie at this
precision. U-Net++ leads, but it also needed the fewest epochs (70 vs 79 vs 89).

### Per-domain VAL Dice at each model's best epoch

| model | ISIC | BUSI | KVASIR | KUB | mean |
|---|---|---|---|---|---|
| U-Net++ (20A) | 0.86007 | 0.81630 | 0.77100 | **0.72066** | 0.79201 |
| Attention U-Net | **0.86169** | **0.82768** | **0.77100** | 0.69578 | 0.78904 |
| U-Net | 0.85527 | 0.81977 | 0.75520 | **0.72109** | 0.78783 |

### Reading the per-domain pattern

- **KUB is the discriminator.** U-Net++ (0.72066) and U-Net (0.72109) hold ~0.72; Attention U-Net
  drops to 0.69578. Since the three are otherwise within ~0.01 on ISIC/BUSI/KVASIR, the entire
  macro gap between rank 1 and rank 2 is explained by KUB alone (−0.0249 on that one domain,
  i.e. −0.0062 on the 4-domain mean).
- **KVASIR is a near-exact tie** for U-Net++ and Attention U-Net (0.770995 vs 0.770999).
- **Attention U-Net is the strongest on ISIC and BUSI** (both best-in-class), which is consistent
  with attention gates helping on larger, cleaner objects while under-serving KUB's tiny objects.
- This matches the known Phase-20 bottleneck: KUB tiny objects (TINY bin Dice 0.531 on the shared
  baseline). The attention mechanism did not relieve it.

## 3. Not yet complete

| model | class | params | state | notes |
|---|---|---|---|---|
| `deeplabv3plus` | `DeepLabV3Plus` | 40,347,041 | IN PROGRESS | epoch 001 @14:37:32, macro 0.589998, ~501 s/epoch |
| `transformer_mit_unet` | `TransformerMiTUNet` | 16,347,777 | NOT_STARTED | queued behind DeepLabV3+ |

DeepLabV3+ is ~4.4× larger than the U-Net family and costs more per epoch, so its runtime is the
main source of ETA uncertainty for the remaining sequence.

## 4. Projected remaining work

Using the measured ~455 s/epoch rate:

- `deeplabv3plus` — ~9.3–11.9 h remaining
- `transformer_mit_unet` — ~9.5–12.0 h
- **Total: ~18.8–23.8 h → completion Monday 2026-09-28, ~09:24–14:27 (GMT+6)**

## 5. Provenance

- `unet` closure: `experiments/phase20b_shared_unet_fourdomain_seed42_clean_v3/closure.json`
- `attention_unet` closure: `experiments/phase20b_shared_attention_unet_fourdomain_seed42_clean_v3/closure.json`
- `unetpp` closure: `experiments/phase20_shared_unetpp_fourdomain_seed42_clean_v3/closure.json`
- Machine-readable snapshot: `reports/tables/phase20b_model_comparison_in_progress.csv`

Both 20B closures record `independent_duplicate_runs: 0` and all `test_reads` fields at 0.
`unet` carried `resume_count: 1` (a single resume of the same logical run after a harness
teardown); `attention_unet` ran with `resume_count: 0`.

The five-model freeze document
(`reports/audits/phase20_five_model_baseline_benchmark_freeze.json`) is **not** produced yet —
it requires all five models to have closed, followed by the canonical disk-only replay,
metrics + bootstrap CI, and paired-bootstrap comparison. That remains the sequence's terminal step.
