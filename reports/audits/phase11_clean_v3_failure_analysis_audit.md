# Phase 11 — CLEAN-v3 Four-Model Failure Analysis Audit

- Created: 2026-09-20T20:10:29.325786+00:00
- Status: **PASS**

## Scope

- Manifest `phase4_v3` · taxonomy `kub_size_clean_v3_v1` · KUB VAL **280**
- Models: UNet, Attention U-Net, UNet++, DeepLabV3+
- Reference model selected: **False**
- Historical replication anchor: **UNet++** (HISTORICAL_REPLICATION_ANALYSIS_ANCHOR) — not a winner/best model/Phase-12 decision

## Reproduction gate

- batch 4, AMP, threshold 0.5, resize `round()`
| Model | |Dice diff| | pass 1e-4 |
|---|---|---|
| UNet | 2.608e-08 | PASS |
| Attention U-Net | 4.514e-10 | PASS |
| UNet++ | 7.507e-10 | PASS |
| DeepLabV3+ | 3.175e-10 | PASS |

## Low-Dice (per-model bottom decile)

| Model | clean Q10 | count <= cutoff |
|---|---|---|
| UNet | 0.4693939398443986 | 28 |
| Attention U-Net | 0.5360238052845407 | 28 |
| UNet++ | 0.5618055568014564 | 28 |
| DeepLabV3+ | 0.3784289703007593 | 28 |

- ALL_FOUR_LOW: **12/280**
- low_model_count distribution: {0: 233, 1: 17, 2: 7, 3: 11, 4: 12}

## UNet++ anchored strata

- HD95 Q90 (valid only): **85.240955** · valid/invalid **[274, 6]**
- FP Q90: **5** · high-FP count **31**

## Regime (mandatory separation)

| Model | FULL_FIELD mean Dice | ROI mean Dice |
|---|---|---|
| UNet | 0.5965 | 0.8245 |
| Attention U-Net | 0.6317 | 0.8228 |
| UNet++ | 0.6455 | 0.8332 |
| DeepLabV3+ | 0.5591 | 0.8625 |

- Regime gap (mean): **0.2276**

## Objects / multi-component

- Object recall: {'UNet': 0.896341, 'Attention U-Net': 0.92378, 'UNet++': 0.914634, 'DeepLabV3+': 0.881098}
- Empty predictions: {'UNet': 8, 'Attention U-Net': 3, 'UNet++': 6, 'DeepLabV3+': 11}
- Multi-component cases: 49 · {'UNet': {'COMPLETE': 30, 'PARTIAL': 16, 'MISS': 3}, 'Attention U-Net': {'COMPLETE': 33, 'PARTIAL': 12, 'MISS': 4}, 'UNet++': {'COMPLETE': 33, 'PARTIAL': 11, 'MISS': 5}, 'DeepLabV3+': {'COMPLETE': 27, 'PARTIAL': 16, 'MISS': 6}}

## Hard cohort

- target 16 / actual **16** · underfilled: **NONE**
- regime mix: {'FULL_FIELD': 10, 'ROI': 6}
- selection SHA: `72f16916e9a9e86b047514842634ab7b73c245d131d5fbbd37db9fff171e3c46`

## Governance

- TP/FP/FN: CLEAN_V3_DESCRIPTIVE_EXTENSION
- Disagreement: dice_range = max(Dice) - min(Dice) · threshold **NONE**
- TEST reads/metrics/visualizations: 0 · training: false · optimizer steps: 0
- Statistical testing: **False**
- Phase 12: started **False** · model decision **SUPERVISOR_DECISION_REQUIRED**

## Status: PASS