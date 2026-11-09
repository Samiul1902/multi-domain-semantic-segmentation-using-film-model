# PHASE-13 — REGIONAL_INTEGRATION_GATE_AFTER_PHASE13 (ADJUDICATED)

- **FINAL GATE VERDICT: `REVISE_LOCALIZER`**
- gate mode: `QUALITATIVE_PROSPECTIVE_EVIDENCE_ADJUDICATION`
- evidence scope: **prospectively frozen evidence only**
- integrity precondition: **PASS**
- post-hoc numerical thresholds: **0** · new subgroups: **0** · weighted score: **NO**
- reference model: **NONE** · ranking: **NONE** · winner: **NONE**
- statistical / clinical superiority claim: **NO**

## Integrity precondition (§2)

| check | result |
|---|---|
| gate_criteria_sha_match | **PASS** |
| gate_status | **PASS** |
| gate_part1d_b_results_inspected_no | **PASS** |
| gate_numerical_thresholds_zero | **PASS** |
| gate_mode | **PASS** |
| part1d_b_status_pass | **PASS** |
| global_reproduction_all_four_pass | **PASS** |
| case_model_rows_412 | **PASS** |
| component_model_rows_608 | **PASS** |
| model_summary_rows_4 | **PASS** |
| test_reads_zero | **PASS** |
| integrity_failures_empty | **PASS** |
| r1_protocol_sha_match | **PASS** |
| part1d_b_integrity_checks_all_pass | **PASS** |

## Dimension adjudication

| dim | dimension | pre-state | adjudicated state | supports GO | supports REVISE | supports NO_GO |
|---|---|---|---|---|---|---|
| **A** | ORACLE_MECHANISM_VALUE | `SUPPORTED_DESCRIPTIVE_EVIDENCE` | **`SUPPORTED_DESCRIPTIVE_EVIDENCE`** | YES_AS_PRECONDITION | YES_AS_PRECONDITION | NO |
| **B** | PRACTICAL_LOCALIZATION_RETENTION | `NOT_EVALUABLE_UNTIL_PHASE13` | **`WEAK__FAILS_TO_TRANSLATE_ORACLE_MECHANISM_INTO_DEPLOYABLE_UTILITY`** | NO | YES | NO |
| **C** | GLOBAL_PRESERVATION_FP_COST | `MIXED_DESCRIPTIVE_EVIDENCE` | **`MATERIAL_GLOBAL_PRESERVATION_FP_COST`** | NO | YES | NO |
| **D** | GENERALITY | `SUPPORTED_WITH_HETEROGENEITY` | **`CROSS_ARCHITECTURE_CONSISTENT_NEGATIVE__NOT_ISOLATED`** | NO | YES_AS_PRECONDITION | NO |

### A — ORACLE_MECHANISM_VALUE

Phase-12 oracle Dice gains remain positive for all four architectures and were independently re-confirmed through the frozen oracle gains: UNet +0.130542, Attention U-Net +0.069790, UNet++ +0.086164, DeepLabV3+ +0.190121. Part-1D-B global reproduction reproduced the shared global path at machine precision (max abs per-case Dice difference 5.551e-17 to 1.110e-16), so the comparator provenance is intact. No material Phase-12 integrity or reproduction defect was discovered.

### B — PRACTICAL_LOCALIZATION_RETENTION

| model | GLOBAL Dice | ORACLE Dice | PREDICTED Dice | DELTA_ORACLE | DELTA_PRED | RETENTION_DICE | ORACLE_GAP |
|---|---|---|---|---|---|---|---|
| UNet | 0.594180 | 0.724722 | 0.302314 | +0.130542 | **-0.291866** | **-2.235800** | -0.422408 |
| Attention U-Net | 0.629805 | 0.699595 | 0.308619 | +0.069790 | **-0.321186** | **-4.602209** | -0.390976 |
| UNet++ | 0.640516 | 0.726679 | 0.311355 | +0.086164 | **-0.329161** | **-3.820171** | -0.415324 |
| DeepLabV3+ | 0.560251 | 0.750372 | 0.277292 | +0.190121 | **-0.282959** | **-1.488308** | -0.473080 |

DELTA_PRED_DICE is strongly negative for all four architectures (-0.291866, -0.321186, -0.329161, -0.282959) and RETENTION_DICE is negative for all four (-2.235800, -4.602209, -3.820171, -1.488308), never clipped. IoU gain retention is negative for all four (-2.503471 to -5.373957). ORACLE_GAP_DICE is -0.390976 to -0.473080. Downstream segmentation utility is therefore NOT retained: the frozen GT-free path does not translate the oracle mechanism into deployable utility. Positive but weak object-recall retention (0.310345 to 0.500000), 9-16 component recoveries, 0 component losses and 3-11 empty recoveries are recorded as genuine favourable signal, but they do not constitute retained downstream segmentation utility.

### C — GLOBAL_PRESERVATION_FP_COST

| model | mean precision delta | mean recall delta | mean FP delta | mean FN delta | cases improved / unchanged / worsened | max improvement | max worsening |
|---|---|---|---|---|---|---|---|
| UNet | -0.458950 | +0.018182 | **+7324.97** | -76.69 | 10 / 0 / **93** | +0.386978 | **-0.789794** |
| Attention U-Net | -0.427001 | -0.013473 | **+7528.07** | +118.83 | 5 / 0 / **98** | +0.388847 | **-0.756766** |
| UNet++ | -0.491628 | +0.021993 | **+7924.50** | -184.14 | 8 / 0 / **95** | +0.381842 | **-0.799650** |
| DeepLabV3+ | -0.494926 | +0.039483 | **+8334.42** | -403.36 | 11 / 0 / **92** | +0.393970 | **-0.750510** |

Precision decreases strongly for all four architectures (mean precision delta -0.427001 to -0.494926) while recall is broadly preserved or mixed (-0.013473 to +0.039483) rather than collapsing. Mean FP pixel delta is +7324.97, +7528.07, +7924.50 and +8334.42. Cases worsened 93, 98, 95 and 92 of 103 (cases improved 10, 5, 8, 11; unchanged 0 for all four). Maximum case worsening -0.750510 to -0.799650 against maximum improvement +0.381842 to +0.393970. This is broad systematic degradation, not a localized effect. Recorded alongside it without hiding: component losses are 0 for all four, component recoveries are 9-16, empty recoveries 3-11, and new empty predictions 0.

### D — GENERALITY

| quantity | value |
|---|---|
| cases_improved_all_four | 3 |
| cases_nonworse_all_four | 3 |
| cases_worse_all_four | 86 |
| components_recovered_by_at_least_one | 27 |
| components_recovered_by_all_four | 4 |
| components_lost_by_at_least_one | 0 |
| components_lost_by_all_four | 0 |

The negative practical result is present in all four architectures (negative DELTA_PRED_DICE and negative RETENTION_DICE in every architecture; 92-98 of 103 cases worsened per architecture). Cross-architecture: cases worsened for all four = 86, cases improved for all four = 3, cases non-worse for all four = 3; native components recovered by >=1 architecture = 27, recovered by all four = 4, lost by >=1 architecture = 0, lost by all four = 0. The signal is therefore cross-architecture CONSISTENT and is not an isolated architecture-specific accident. No architecture is ranked, no winner is selected, and heterogeneity is reported rather than averaged away.

## Prospective logic applied (§9)

- **GO** — satisfied: **NO**; blocked by: B weak / fails to translate into deployable utility; C broad systematic degradation undermining the practical benefit
- **REVISE_LOCALIZER** — satisfied: **YES**; triggered by: B weak / fails to translate oracle mechanism into deployable utility; C materially problematic global-preservation / FP cost
- **NO_GO** — satisfied: **NO**; blocked by: A remains SUPPORTED_DESCRIPTIVE_EVIDENCE; frozen invariant: a poor GT-free localizer result alone cannot produce NO_GO while A remains supported

## Verdict reasoning

Dimension A remains SUPPORTED_DESCRIPTIVE_EVIDENCE: the Phase-12 oracle gains are positive for all four architectures and Part-1D-B independently reproduced the shared global path at machine precision, so no integrity or reproduction defect invalidates A. Therefore NO_GO is not available, and the frozen invariant explicitly forbids NO_GO from a poor GT-free localizer result alone while A remains supported. Dimension B fails: DELTA_PRED_DICE and RETENTION_DICE are negative for all four architectures, so the frozen GT-free path does not translate the oracle mechanism into deployable downstream segmentation utility. Dimension C fails: precision decreases strongly for all four architectures with mean FP pixel deltas of +7324.97 to +8334.42 and 92-98 of 103 cases worsening, which is broad systematic degradation undermining the practical benefit. Dimension D shows the effect is cross-architecture consistent and not an isolated architecture-specific accident; D is therefore not the operative trigger. GO requires A and B and C and D; B and C are not satisfied. REVISE_LOCALIZER requires A supported AND at least one of (B weak, C materially problematic, D too architecture-specific); A is supported and both B and C are satisfied. The adjudicated verdict is therefore REVISE_LOCALIZER, derived strictly from the prospectively frozen dimensions with no post-hoc threshold, no new subgroup and no weighted score.

## Verdict discipline (§12)

| statement | value |
|---|---|
| phase12_regional_mechanism_hypothesis_remains_supported | **YES** |
| current_frozen_gt_free_localization_proposal_integration_path_promoted | **NO** |
| result_authorizes_ra_medfilm_regional_integration | **NO** |
| phase14_may_begin_as_if_regional_mechanism_approved | **NO** |
| automatic_redesign_performed_in_part1e_b | **NO** |
| separately_supervised_revision_plan_required | **YES** |
| revise_localizer_equated_with_oracle_mechanism_scientific_failure | **NO** |
| proposal_threshold_or_fusion_rule_silently_changed | **NO** |

## Localization / FP context (§8)

Frozen Part-1C proposals: **494** total, **122** overlap >=1 GT pixel, **372** overlap no GT pixel (off-target fraction **0.753036**). Gallery fusion verification: outside `U_pred`, `P == G` exactly for all **64** checked case-model pairs.

This is **descriptive** evidence consistent with the current GT-free proposal / integration path driving substantial FP burden. It is **not** a claim that proposal precision is conclusively the sole causal mechanism, and the gate decision does **not** require a sole-cause diagnosis.

## Claim limits

| item | value |
|---|---|
| numerical_thresholds_introduced_after_results | 0 |
| new_subgroup | NO |
| weighted_score | NO |
| reference_model | None |
| ranking | NONE |
| winner | NONE |
| statistical_superiority_claim | NO |
| clinical_superiority_claim | NO |
| gallery_used_to_determine_gate | NO |
| predeclared_cohorts_only | ['TINY', 'SMALL', 'MEDIUM', 'LARGE', 'hard-Tiny', 'global-empty', 'multi-component'] |

## Phase-13 closure state

| item | state |
|---|---|
| phase13_part1b | **COMPLETE_PASS_FROZEN** |
| phase13_part1c | **COMPLETE_PASS_FROZEN** |
| phase13_part1d_a_r1 | **COMPLETE_PASS_FROZEN** |
| phase13_part1d_b | **COMPLETE_PASS_FROZEN** |
| phase13_part1e_a | **COMPLETE_PASS_FROZEN** |
| phase13_part1e_b | **COMPLETE_PASS** |
| phase13 | **COMPLETE** |
| regional_integration_gate_after_phase13 | **REVISE_LOCALIZER** |
| regional_mechanism_promoted | **NO** |
| phase14 | **NOT_STARTED** |
| test | **UNTOUCHED** |

## Zero-execution counters

training **0** · optimizer **0** · model constructions **0** · CUDA requests **0** · segmentation forwards **0** · regional crop forwards **0** · localizer forwards **0** · proposal generation **0** · oracle reruns **0** · TEST reads **0**

**next_action: `WAIT_FOR_SUPERVISOR_REGIONAL_LOCALIZER_REVISION_PLAN`**
