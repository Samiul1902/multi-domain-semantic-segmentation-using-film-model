# POST-PHASE-13 H2-A — SELECTION-ONLY PROTOCOL FROZEN

- status: **`SUPERVISOR_FROZEN_H2A_SELECTION_ONLY_READY_FOR_EXECUTION`**
- experiment id: `post_phase13_h2a_kub_localizer_r512_h128_sigmaeq075_centernetfocal_deploymentbalance_seed42_clean_v3`
- collision: **NONE (both checkpoints/ and experiments/ paths absent)**
- H2 axis: **`H2A_DEPLOYMENT_BALANCED_CHECKPOINT_SELECTION_ONLY`**
- score-path verdict: **`SCORE_PATH_IMPLEMENTATION_VALID`**
- trajectory classification: **`C__ONLY_BEST_AND_LATEST_AVAILABLE`**
- **execution mode: `MODE_B__DETERMINISTIC_TRAINING_REPLAY_WITH_NEW_SELECTION`**

## Scientific question

Can a deployment-aligned LOCALIZER CHECKPOINT-SELECTION rule improve proposal precision / precision-recall balance sufficiently WITHOUT changing architecture, training target, sigma, loss, optimizer, scheduler, augmentation, data, seed, proposal geometry, proposal threshold, margin, top-k, NMS, regional segmentation models or fusion semantics?

## Execution mode decision

The new rule requires PROPOSAL_PIXEL_ANY_HIT_PRECISION for EVERY epoch. That quantity needs proposals, which need each epoch's weights and an inference pass. Only 3 distinct epoch weights exist (31, 53, 68 of 68) and no per-epoch proposal outputs were persisted, so checkpoint replay alone cannot apply the new rule. MODE_B is therefore required. The replay MUST retain identical gradient-update semantics; the ONLY scientific change is which epoch is declared best and drives early stopping.

## Frozen training contract

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
| architecture | existing compact KUB localizer |
| in_channels | 1 |
| out_channels | 1 |
| base_channels | 16 |
| target | existing CenterNet-style heatmap target unchanged |
| loss | CenterNetFocalLoss(alpha=2.0, beta=4.0) |
| optimizer | AdamW |
| lr | 0.0001 |
| weight_decay | 0.0001 |
| scheduler | CosineAnnealingLR(T_max=100) |
| batch | 4 |
| amp | same accepted Phase13 semantics |
| seed | 42 |
| augmentation | UNCHANGED from clean-v3 Phase13 |
| max_epochs | 100 |
| workers | 0 |
| cuda | required |
| test | forbidden |

## Frozen proposal evaluation contract

- threshold **0.1** · margin **0.2** · top_k **5** · NMS IoU **0.3**
- grid: **NONE** · threshold search: **NONE** · per-epoch sensitivity: **NONE**
- coverage semantics: canonical historical executing BBOX coverage remains available; pixel semantics remain secondary sensitivity where appropriate

### New primary quantity `PROPOSAL_PIXEL_ANY_HIT_PRECISION`

- numerator: number of generated proposals whose CLIPPED native proposal support contains at least one native GT foreground pixel
- denominator: total generated proposals across the complete 103-case VAL population
- zero-denominator rule: precision = 0.0
- secondary diagnostic: `PROPOSAL_BBOX_ANY_HIT_PRECISION`

## New primary checkpoint utility

- label: **`DEPLOYMENT_BALANCE_HMEAN_P_TINY90_OVERALL90`**
- definition: `0.0 if any of P,T,O <= 0 else 3 / (1/P + 1/T + 1/O)`
- P = PROPOSAL_PIXEL_ANY_HIT_PRECISION · T = tiny_recall90 · O = overall_recall90
- is a statistical F1 score: **NO - must not be called an F1 score**
- purpose: balance proposal intervention precision, tiny-object coverage and overall component coverage without an arbitrary weighted sum

## H2A primary checkpoint tuple (frozen prospectively)

```
  1. DEPLOYMENT_BALANCE_HMEAN_P_TINY90_OVERALL90
  2. tiny_recall90
  3. overall_recall90
  4. PROPOSAL_PIXEL_ANY_HIT_PRECISION
  5. -mean_roi_area_fraction
  6. -val_loss
```

- tuple length **6** · comparison **STRICT_LEXICOGRAPHIC_GREATER_THAN** · ties **BAD_EPOCH**
- early-stop patience **15** · checkpoint **strict improvement only** · latest.pt **every completed epoch**
- downstream segmentation metric participates: **NO**
- Phase-12 oracle result participates: **NO**
- R1 segmentation outcome participates: **NO**

## Secondary per-epoch diagnostics (structurally excluded from selection)

- proposal_bbox_any_hit_precision
- proposal_count_per_image
- hard_Tiny_recovery
- global_empty_recovery
- multi_component_recall
- overall_recall50
- any_overlap_recall
- mean_coverage
- proposal_score_mean
- proposal_score_median
- proposal_score_Q25
- proposal_score_Q75
- proposal_score_max
- fraction_proposals_exactly_at_epoch_max_score
- score_IQR
- hit_proposal_score_distribution
- miss_proposal_score_distribution
- ROC_AUC_score_to_pixel_any_hit
- PR_AUC_score_to_pixel_any_hit

AUC role: **DIAGNOSTIC_ONLY** · score-calibration threshold search: **NONE**

## Selection-only interpretation

| item | value |
|---|---|
| loss_changed | **NO** |
| target_changed | **NO** |
| architecture_changed | **NO** |
| sigma_changed | **NO** |
| data_changed | **NO** |
| augmentation_changed | **NO** |
| optimizer_changed | **NO** |
| proposal_config_changed | **NO** |
| checkpoint_selection_changed | **YES** |

## Scientific change register


### `CHANGE_H2A_001` — field: checkpoint selection

**old:**
```
tiny_recall90 , overall_recall90 , -mean_roi_area_fraction , -val_loss
```
**new:**
```
  1. DEPLOYMENT_BALANCE_HMEAN_P_TINY90_OVERALL90
  2. tiny_recall90
  3. overall_recall90
  4. PROPOSAL_PIXEL_ANY_HIT_PRECISION
  5. -mean_roi_area_fraction
  6. -val_loss
```

**motivation:** Phase13 + H1 show recall-first selection yields useful target recovery but unacceptable off-target intervention / downstream FP burden, while acceptance-only mitigation is insufficient. No causal claim is made.

## H2A outcome space (NOT adjudicated now)

- `H2A_SELECTION_REDESIGN_SUFFICIENT`
- `H2A_SELECTION_REDESIGN_PARTIAL`
- `H2A_SELECTION_REDESIGN_INSUFFICIENT`
- `CHECK_REQUIRED`

loss/target/representation redesign MAY become eligible later; NOT automatically authorized

## Training notebook requirement (if MODE_B authorized)

Must display one completed epoch per row, untruncated, with: epoch, train_loss, val_loss, P, T, O, deployment_balance_hmean, proposal_count, mean_roi_area, checkpoint_tuple, is_new_best, bad_epochs

## Claim limits

| item | value |
|---|---|
| new_numerical_success_threshold | NONE |
| hidden_grid | NONE |
| downstream_metric_in_selection | NO |
| phase12_oracle_in_selection | NO |
| r1_outcome_in_selection | NO |
| test_or_external_access | NONE |
| selection_redesign_will_succeed_asserted | NO |

## Counters

| counter | value |
|---|---|
| training | **0** |
| optimizer_construction | **0** |
| model_construction | **0** |
| cuda_requests | **0** |
| localizer_forwards | **0** |
| segmentation_forwards | **0** |
| regional_forwards | **0** |
| proposal_generation | **0** |
| checkpoint_writes | **0** |
| test_reads | **0** |
| external_test_reads | **0** |

## Continuity

| item | state |
|---|---|
| phase13 | **COMPLETE_FROZEN** |
| original_regional_gate | **REVISE_LOCALIZER_FROZEN** |
| h1 | **CLOSED__PARTIAL_MITIGATION_INSUFFICIENT** |
| h2a_protocol | **COMPLETE_PASS_FROZEN** |
| h2a_execution | **ELIGIBLE_FOR_SUPERVISOR_AUTHORIZATION__NOT_AUTHORIZED** |
| h2_loss_redesign | **NOT_STARTED** |
| h3_fusion_redesign | **NOT_STARTED** |
| phase14 | **NOT_STARTED** |
| test | **UNTOUCHED** |

**next_action: `WAIT_FOR_SUPERVISOR_H2A_EXECUTION_AUTHORIZATION`**
