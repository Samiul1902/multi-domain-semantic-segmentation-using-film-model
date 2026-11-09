# POST-PHASE13 H2-C — HEAD / REPRESENTATION REDESIGN PROTOCOL (FROZEN)

- **Status: SUPERVISOR_FROZEN_H2C_HEAD_REDESIGN_READY_FOR_B1_AUTHORIZATION**
- Model attribution: Gemini 3.1 Pro High
- Experiment id: `post_phase13_h2c_kub_localizer_spatialhead3x3relu_r512_h128_sigmaeq075_centernetfocal_deploymentbalance_seed42_clean_v3`
- Collision: NONE (checkpoints/ and experiments/ paths absent)

## 1. Purpose

**Scientific question.** Can a HEAD-ONLY SPATIAL REPRESENTATION REDESIGN improve heatmap discrimination and proposal precision while preserving object coverage, holding backbone, target, sigma, loss, optimizer, scheduler, augmentation, dataset, split, seed, checkpoint selection, proposal policy, regional segmentation checkpoints, fusion and segmentation threshold fixed?

**Changed axis.** `LOCALIZER PREDICTION-HEAD ARCHITECTURE / REPRESENTATION` — exactly ONE scientific axis.

## 2. Prior evidence binding

- H2B outcome adjudication `9371fc00ac0d65fc…` — H2B_OBJECTIVE_REDESIGN_INSUFFICIENT; H2C protocol design ELIGIBLE_FOR_SUPERVISOR_AUTHORIZATION; H2C execution NOT_AUTHORIZED; TEST reads 0
- H2A score-path audit `3d9fea04ba8ca8b6…` — SCORE_PATH_IMPLEMENTATION_VALID
- Interpretation constraint: This evidence SUPPORTS a head/representation hypothesis. It does NOT prove the head is the sole cause.

## 3. Baseline branch

H2C branches from **H2A (the scientifically stronger baseline)**. Loss: `CenterNetFocalLoss(alpha=2.0, beta=4.0)` — the H2B soft-target objective is **not** used.

Correct description: H2C branches from the H2A baseline and tests head representation as a new isolated axis after H2B objective redesign proved insufficient.

## 4. Old head (physically verified)

- module: `src/models/kub_localizer.py :: KUBLocalizer.head`
- structure: `nn.Conv2d(16, 1, kernel_size=1, stride=1, padding=0, bias=True)`
- spatial mixing inside head: NONE
- parameters: **17**
- weight shape: [1, 16, 1, 1]
- initialization: {'weight': 'ALL_ZERO (constant 0.0)', 'bias': 'log(0.1/0.9) = logit(0.1)'}
- output shape: [1, 1, 128, 128]
- internal sigmoid: **NONE**

## 5. New head — ONE variant only

**`SPATIAL_DISCRIMINATIVE_HEAD_3X3_RELU_1X1_V1`**

```
  Conv2d(16, 16, kernel_size=3, stride=1, padding=1, bias=True)
  ReLU(inplace=False)
  Conv2d(16, 1, kernel_size=1, stride=1, padding=0, bias=True)
```

- hidden width frozen at **16** (no search)
- forbidden components: BatchNorm, GroupNorm, LayerNorm, dropout, attention, residual block, extra decoder, multi-scale branch, deep supervision
- backbone: byte-for-byte / semantically UNCHANGED
- output shape: [1, 1, 128, 128] · internal sigmoid: NONE

## 6. Initialization (frozen prospectively)

- conv3x3 weight: kaiming_normal_(nonlinearity='relu')
- conv3x3 bias: 0
- conv1x1 weight: **ALL ZERO**
- conv1x1 bias: logit(0.1) = log(0.1/0.9) = -2.1972245773362196
- measured initial logit spread (max−min): **0.0** (spatially constant)

## 7. Rationale (prospective only)

Old head: only a pointwise linear projection of backbone features. H2C adds local 3x3 spatial mixing and one nonlinear transformation before the final heatmap logit. Will succeed asserted: **NO** · old head proven causal: **NO**

## 8. Parameter / shape contract

| quantity | value |
|---|---|
| old head parameters | 17 |
| new head parameters | 2337 |
| absolute delta | +2320 |
| whole-model old | 482449 |
| whole-model H2C | 484769 |
| percentage increase | 0.480880% |
| all new trainable params in head | YES |
| backbone parameter shapes | UNCHANGED |
| external inference sigmoid | exactly once, unchanged |

## 9. Frozen training contract

| field | value |
|---|---|
| TRAIN | 770 FULL_FIELD cases / 1161 components |
| VAL | 103 FULL_FIELD cases / 152 components |
| ROI | EXCLUDED |
| manifest | phase4_v3 |
| taxonomy | kub_size_clean_v3_v1 |
| input | 512 x 512 |
| heatmap | 128 x 128 |
| sigma | 0.75 |
| backbone | UNCHANGED existing KUB localizer backbone |
| target | UNCHANGED existing CenterNet-style Gaussian heatmap |
| loss | CenterNetFocalLoss(alpha=2.0, beta=4.0) |
| optimizer | AdamW |
| lr | 0.0001 |
| weight_decay | 0.0001 |
| scheduler | CosineAnnealingLR(T_max=100) |
| batch | 4 |
| amp | same accepted H2A semantics |
| seed | 42 |
| augmentation | UNCHANGED |
| workers | 0 |
| max_epochs | 100 |
| cuda | required during future execution |
| test | forbidden |

## 10. Proposal contract

| field | value |
|---|---|
| threshold | 0.1 |
| margin | 0.2 |
| top_k | 5 |
| nms_iou | 0.3 |
| grid | NONE |
| threshold_search | NONE |
| max_proposal_ablation | NONE |
| h1_selective_filtering | NONE |
| score_calibration | NONE |
| policy_family | NONE |

## 11. Checkpoint selection (unchanged from H2A)

- P PROPOSAL_PIXEL_ANY_HIT_PRECISION · T tiny_recall90 · O overall_recall90
- H = 0 if any P/T/O <= 0 else 3 / (1/P + 1/T + 1/O)
- tuple: `['H', 'T', 'O', 'P', '-mean_roi_area_fraction', '-val_loss']`
- STRICT_LEXICOGRAPHIC_GREATER_THAN · patience 15 · changed vs H2A: **NO**

## 12. Scientific change register

| field | value |
|---|---|
| CHANGE_H2C_001 | {"axis": "LOCALIZER_PREDICTION_HEAD_ARCHITECTURE", "old": "Conv2d(16 -> 1, kernel_size=1)", "new": "Conv2d(16 -> 16, kernel_size=3, padding=1) + ReLU + Conv2d(16 -> 1, kernel_size=1)", "initialization_part_of_same_axis": true} |
| LOSS_CHANGED | NO vs H2A |
| TARGET_CHANGED | NO |
| SIGMA_CHANGED | NO |
| BACKBONE_CHANGED | NO |
| OPTIMIZER_CHANGED | NO |
| DATA_CHANGED | NO |
| AUGMENTATION_CHANGED | NO |
| CHECKPOINT_SELECTION_CHANGED | NO vs H2A |
| PROPOSAL_POLICY_CHANGED | NO |
| FUSION_CHANGED | NO |
| SEGMENTATION_CHECKPOINTS_CHANGED | NO |
| HEAD_ARCHITECTURE_CHANGED | YES |
| second_scientific_axis | NONE |

## 13. H2B relationship

- H2B CLOSED · combined with H2C: **NO**
- must not be described as: "H2B plus a new head"

## 14. Prospective outcome definitions (frozen BEFORE execution)

| label | definition |
|---|---|
| `note` | Frozen BEFORE H2C execution. H2B froze labels without an evidence-to-label mapping; H2C freezes both. |
| `H2C_HEAD_REDESIGN_SUFFICIENT` | The head redesign produces reproducible favourable localizer proposal quality relative to the frozen H2A baseline AND those changes translate into a downstream predicted-region path that descriptively resolves the major global-preservation failure while retaining meaningful regional utility across architectures. No numerical cutoff is introduced. |
| `H2C_HEAD_REDESIGN_PARTIAL` | The head redesign produces reproducible favourable localizer changes relative to H2A and at least some corresponding downstream improvement, but the complete predicted-region path still does not adequately resolve global preservation and/or loses substantial regional utility. |
| `H2C_HEAD_REDESIGN_INSUFFICIENT` | Either (a) the head redesign does not produce reproducible favourable localizer proposal-quality changes relative to H2A, OR (b) favourable localizer changes do not translate into meaningful downstream improvement and the major deployable failure remains. |
| `CHECK_REQUIRED` | A material protocol, provenance, integrity, leakage, or quantitative evidence defect prevents scientific adjudication. |
| `numerical_thresholds` | NONE |
| `weighted_score` | NONE |
| `winner` | NONE |

numerical thresholds **NONE** · weighted score **NONE** · winner **NONE**

## 15. Comparator discipline

- primary localizer comparator: H2A best checkpoint
- secondary historical: Phase13 best checkpoint
- downstream comparators: GLOBAL, Phase13 predicted-region, H2A predicted-region, ORACLE
- H2B role: **HISTORICAL_CONTEXT_ONLY** (never a tuning reference)

## 16. Future execution split

- H2C-B1: training + standalone localizer evaluation -> SUPERVISOR REVIEW
- H2C-B2: downstream four-architecture segmentation evaluation (only if separately authorized)
- both authorized now: **NO**

## 17. If H2C is insufficient

- FURTHER_REVISION: **REQUIRES_SUPERVISOR_DECISION** · H3: **NOT_AUTOMATICALLY_AUTHORIZED**
- no H2D, no target/sigma/backbone/fusion change, no H3, no Phase14

## 18. Zero execution

training 0 · optimizer constructions 0 · model constructions 0 · CUDA requests 0 · localizer forwards 0 · proposal generation 0 · segmentation forwards 0 · regional forwards 0 · checkpoint writes 0 · TEST reads 0 · external TEST reads 0

## 19. Continuity

| item | state |
|---|---|
| phase13 | COMPLETE_FROZEN |
| original_gate | REVISE_LOCALIZER_FROZEN |
| h1 | CLOSED |
| h2a | CLOSED__SELECTION_REDESIGN_PARTIAL |
| h2b | CLOSED__OBJECTIVE_REDESIGN_INSUFFICIENT |
| h2c_protocol | COMPLETE_PASS_FROZEN |
| h2c_b1 | ELIGIBLE_FOR_SUPERVISOR_AUTHORIZATION |
| h2c_b1_authorized | False |
| h2c_b2 | NOT_STARTED |
| h3 | NOT_STARTED |
| phase14 | NOT_STARTED |
| test | UNTOUCHED |

**next_action:** `WAIT_FOR_SUPERVISOR_H2C_B1_AUTHORIZATION`
