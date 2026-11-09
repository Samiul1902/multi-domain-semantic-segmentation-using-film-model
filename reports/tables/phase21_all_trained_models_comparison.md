# Consolidated comparison — all previously trained models

Generated 2026-09-28T22:56:40Z by `scripts/analysis/build_phase21_all_models_table.py`.

## ⚠️ Comparability notice — read before citing any number

This table mixes **two different kinds of evidence**:

| Provenance | Meaning |
|---|---|
| **FROZEN** | One canonical VAL pass over a frozen best checkpoint. Safe to cite as a benchmark result. |
| **LIVE** | A per-epoch validation value from a run that **has not terminated**. The checkpoint selection is **not final**. Orientation only — **not a result**. |

**Every row is FROZEN** — each is a single canonical VAL pass over a fixed best
checkpoint. The Phase-21 Global MedFiLM row was trained under the identical frozen
Phase-20 protocol, so the panel is directly comparable.

## 1. Full panel — macro-domain VAL Dice

| # | Model | Phase | Params | G MACs | Macro Dice | ISIC | BUSI | KVASIR | KUB | Provenance |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Global MedFiLM | 21 | 3,523,001 | 31.55 | **0.835079** | 0.8972 | 0.8588 | 0.8202 | 0.7641 | FROZEN |
| 2 | DeepLabV3+ | 20B | 40,347,041 | 69.14 | **0.827653** | 0.8853 | 0.8669 | 0.8197 | 0.7388 | FROZEN |
| 3 | Transformer/MiT-style U-Net | 20B | 16,347,777 | 99.10 | **0.822381** | 0.8871 | 0.8640 | 0.8133 | 0.7252 | FROZEN |
| 4 | UNet++ | 20A | 9,159,681 | 137.94 | **0.792007** | 0.8601 | 0.8163 | 0.7710 | 0.7207 | FROZEN |
| 5 | Attention U-Net | 20B | 7,851,285 | 47.22 | **0.789039** | 0.8617 | 0.8277 | 0.7710 | 0.6958 | FROZEN |
| 6 | U-Net | 20B | 7,763,041 | 46.14 | **0.787833** | 0.8553 | 0.8198 | 0.7552 | 0.7211 | FROZEN |

## 2. Frozen benchmark — the citable ranking (6 models)

| Rank | Model | Macro Dice | Best ep | Final ep | Params |
|---|---|---|---|---|---|
| 1 | Global MedFiLM | **0.835079** | 66 | 81 | 3,523,001 |
| 2 | DeepLabV3+ | **0.827653** | 57 | 72 | 40,347,041 |
| 3 | Transformer/MiT-style U-Net | **0.822381** | 74 | 89 | 16,347,777 |
| 4 | UNet++ | **0.792007** | 55 | 70 | 9,159,681 |
| 5 | Attention U-Net | **0.789039** | 64 | 79 | 7,851,285 |
| 6 | U-Net | **0.787833** | 74 | 89 | 7,763,041 |

Every row in this section is a frozen best checkpoint evaluated in ONE canonical VAL pass,
with `test_reads = 0` on all four counters.

### 2.1 Tier structure

| Tier | Models | Macro Dice band | Verdict |
|---|---|---|---|
| 1 | Global MedFiLM, DeepLabV3+, Transformer/MiT | 0.8224 – 0.8351 | Tier-1 band; Global MedFiLM separable from MiT/UNet++, NOT from DeepLabV3+ |
| 2 | U-Net++, Attention U-Net, U-Net | 0.7878 – 0.7920 | mutually indistinguishable |

Global MedFiLM leads the panel, but its paired CI against **DeepLabV3+** overlaps zero
(Δ +0.007427, CI [−0.002042, +0.018313], p = 0.124), so those two are **not separable**.

## 3. Paired domain-stratified bootstrap (all frozen models)

Within-panel comparisons. The Phase-21 Global MedFiLM vs-baseline bootstrap is reported
separately in the Phase-21 report §3 and in `phase21_paired_bootstrap_vs_baselines.csv`.

Method: paired percentile bootstrap, `n_boot=2000`, `seed=42`, resampling unit `domain_stratified_paired_image`, identical resampled VAL indices
for both models in each replicate.

| Model A | Model B | Δ(A−B) | 95% CI | p | Separable? |
|---|---|---|---|---|---|
| U-Net | DeepLabV3+ | -0.039820 | [-0.053127, -0.026640] | 0.000 | **YES** |
| Attention U-Net | DeepLabV3+ | -0.038616 | [-0.051391, -0.026347] | 0.000 | **YES** |
| DeepLabV3+ | U-Net++ | +0.035643 | [+0.023153, +0.047986] | 0.000 | **YES** |
| U-Net | Transformer/MiT | -0.034550 | [-0.048555, -0.020799] | 0.000 | **YES** |
| Attention U-Net | Transformer/MiT | -0.033346 | [-0.046688, -0.021403] | 0.000 | **YES** |
| Transformer/MiT | U-Net++ | +0.030373 | [+0.016946, +0.044389] | 0.000 | **YES** |
| DeepLabV3+ | Transformer/MiT | +0.005270 | [-0.004246, +0.013870] | 0.282 | no (CI spans 0) |
| U-Net | U-Net++ | -0.004178 | [-0.015182, +0.007565] | 0.488 | no (CI spans 0) |
| Attention U-Net | U-Net++ | -0.002973 | [-0.014766, +0.008504] | 0.577 | no (CI spans 0) |
| U-Net | Attention U-Net | -0.001204 | [-0.009941, +0.008359] | 0.830 | no (CI spans 0) |

**Key conclusion:** the top-two ordering (DeepLabV3+ vs Transformer/MiT) is **NOT**
significant (Δ +0.005270, CI [−0.004246, +0.013870], p = 0.282). These two models are
**tied** on this evidence — never claim a single winner. The three U-Net-family variants
are likewise mutually indistinguishable. Only the Tier-1 / Tier-2 separation is robust.

## 4. Per-domain breakdown (frozen panel)

| Model | ISIC | BUSI | KVASIR | KUB | Macro | Strongest | Weakest |
|---|---|---|---|---|---|---|---|
| Global MedFiLM | 0.8972 | 0.8588 | 0.8202 | 0.7641 | **0.835079** | ISIC | KUB |
| DeepLabV3+ | 0.8853 | 0.8669 | 0.8197 | 0.7388 | **0.827653** | ISIC | KUB |
| Transformer/MiT-style U-Net | 0.8871 | 0.8640 | 0.8133 | 0.7252 | **0.822381** | ISIC | KUB |
| UNet++ | 0.8601 | 0.8163 | 0.7710 | 0.7207 | **0.792007** | ISIC | KUB |
| Attention U-Net | 0.8617 | 0.8277 | 0.7710 | 0.6958 | **0.789039** | ISIC | KUB |
| U-Net | 0.8553 | 0.8198 | 0.7552 | 0.7211 | **0.787833** | ISIC | KUB |

**KUB is the bottleneck for every model** and the field is tightest there (span 0.6958–0.7388,
~4.3 pp). ISIC and BUSI are saturated (all models within ~3.2 pp and ~5.1 pp respectively).

## 5. Parameter / compute cost axis

| Model | Params | Params rank | G MACs | MACs rank | vs MedFiLM (×) |
|---|---|---|---|---|---|
| Global MedFiLM | 3,523,001 | 1/6 | 31.5517 | 1/6 | 1.000 |
| U-Net | 7,763,041 | 2/6 | 46.1373 | 2/6 | 1.462 |
| Attention U-Net | 7,851,285 | 3/6 | 47.2190 | 3/6 | 1.497 |
| DeepLabV3+ | 40,347,041 | 6/6 | 69.1394 | 4/6 | 2.191 |
| Transformer/MiT | 16,347,777 | 5/6 | 99.0986 | 5/6 | 3.141 |
| U-Net++ | 9,159,681 | 4/6 | 137.9423 | 6/6 | 4.372 |

Global MedFiLM is the **lightest on both axes** of this six-model panel, but its absolute
cost (31.55 G MACs at 512 px) is not small. Measurement is an exact closed-form
Conv2d/Linear count and is therefore a **lower bound**.


## 6. Phase-21 status

- Epochs completed: **81** (best at epoch 66)
- Stop reason: **EARLY_STOPPING_PATIENCE**
- Early-stopping patience used: **15 / 15**
- Resume count: **1** (one host teardown recovered)
- Macro-domain VAL Dice (ONE canonical pass over 808 VAL samples): **0.835079**
- The canonical VAL pass has completed, so this row is directly comparable to the
  frozen panel in §2. See §3 of the Phase-21 report for the paired bootstrap
  against each frozen baseline (this table's §3 covers the frozen panel only).
