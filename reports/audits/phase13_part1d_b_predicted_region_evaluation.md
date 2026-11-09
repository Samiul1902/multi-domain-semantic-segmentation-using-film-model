# PHASE-13 PART-1D-B — PREDICTED-REGION EVALUATION (COMPLETION AUDIT)

- status: **PASS**
- run id: `phase13_part1d_b_predicted_region_clean_v3`
- primary variant: **`PREDICTED_REGION_FLOAT_GLOBAL_RETAINED`**

## Population

| item | value |
|---|---|
| VAL FULL_FIELD cases | 103 |
| native components | 152 |
| frozen proposals | 494 (492 interior + 2 bottom-padded, margin 0.20) |
| regional crop evaluations | 1976 (494 x 4) |
| case-model rows | 412 |
| component-model rows | 608 |
| model summary rows | 4 |

## Global reproduction

| model | max abs Dice diff | mean Dice new | mean Dice Phase-12 | PASS |
|---|---|---|---|---|
| unet | 5.551e-17 | 0.594180 | 0.594180 | **YES** |
| attention_unet | 1.110e-16 | 0.629805 | 0.629805 | **YES** |
| unetpp | 1.110e-16 | 0.640516 | 0.640516 | **YES** |
| deeplabv3plus | 1.110e-16 | 0.560251 | 0.560251 | **YES** |

## Model summary (descriptive; no winner, no rank)

| model | D_G | D_O | D_P | DELTA_ORACLE | DELTA_PRED | RETENTION_DICE | ORACLE_GAP | IoU ret | Obj-recall ret | FN-reduction ret |
|---|---|---|---|---|---|---|---|---|---|---|
| UNet | 0.594180 | 0.724722 | 0.302314 | 0.130542 | -0.291866 | -2.235800 | -0.422408 | -2.503471 | 0.488372 | 0.041765 |
| Attention U-Net | 0.629805 | 0.699595 | 0.308619 | 0.069790 | -0.321186 | -4.602209 | -0.390976 | -5.373957 | 0.310345 | -0.096985 |
| UNet++ | 0.640516 | 0.726679 | 0.311355 | 0.086164 | -0.329161 | -3.820171 | -0.415324 | -4.796426 | 0.500000 | 0.090420 |
| DeepLabV3+ | 0.560251 | 0.750372 | 0.277292 | 0.190121 | -0.282959 | -1.488308 | -0.473080 | -1.554257 | 0.387755 | 0.183829 |

## Global-preservation / component events

| model | mean FP delta | mean FN delta | cases improved | unchanged | worsened | component recoveries | component losses | empty recoveries | new empties |
|---|---|---|---|---|---|---|---|---|---|
| UNet | 7325.0 | -76.7 | 10 | 0 | 93 | 16 | 0 | 8 | 0 |
| Attention U-Net | 7528.1 | 118.8 | 5 | 0 | 98 | 9 | 0 | 3 | 0 |
| UNet++ | 7924.5 | -184.1 | 8 | 0 | 95 | 14 | 0 | 5 | 0 |
| DeepLabV3+ | 8334.4 | -403.4 | 11 | 0 | 92 | 16 | 0 | 11 | 0 |

## Cross-architecture descriptive counts

| quantity | value |
|---|---|
| cases_improved_all_four | 3 |
| cases_nonworse_all_four | 3 |
| cases_worse_all_four | 86 |
| components_recovered_by_at_least_one | 27 |
| components_recovered_by_all_four | 4 |
| components_lost_by_at_least_one | 0 |
| components_lost_by_all_four | 0 |

## Integrity checks (§27)

| check | pass | detail |
|---|---|---|
| global_reproduction_all_four | **PASS** | max abs dice diff per model {'UNet': 0.0, 'Attention U-Net': 0.0, 'UNet++': 0.0, 'DeepLabV3+': 0.0} |
| case_model_rows_412 | **PASS** | rows=412 |
| unique_sample_model_412 | **PASS** | unique=412 |
| component_model_rows_608 | **PASS** | rows=608 |
| unique_sample_component_model_608 | **PASS** | unique=608 |
| model_summary_rows_4 | **PASS** | rows=4 |
| case_ids_103 | **PASS** | n=103 |
| component_ids_152 | **PASS** | n=152 |
| proposal_counts_494 | **PASS** | total=494 |
| no_missing_predicted_rows | **PASS** | predicted metric columns complete |
| no_nan_inf_valid_metrics | **PASS** | all 12 metric columns finite |
| hd95_invalidity_labelled | **PASS** | hd95_valid flags present; invalid reasons carried in *_hd95_invalid_reason |
| retention_denominator_handled | **PASS** | RETENTION_DICE is either a value or N/A (never a fabricated zero) |
| immutable_r1_protocol | **PASS** | 9089b948ef7563252963bf68d0e0b57a9e891c5e913f54a315bce94c98207eb8 |
| immutable_gate_criteria | **PASS** | 342a8bcac2c87bf0b85f7bbd963179e74f029825c0434cf527fbd939d2d13c21 |
| immutable_part1d_helper | **PASS** | 8cd7e39814a049a025f706c57ccea0b535a230908a177690d6289318234c6284 |
| immutable_checkpoints_unet | **PASS** | 7b955ba86464a2fec2d569ecb6124de1fa9a4e66d0b5d58b267be9a280b4c2c0 |
| immutable_checkpoints_attention_unet | **PASS** | a49b19d66e43b57ed082ea6efc0ac10bccf444277abd3540dc68612bf30b88b3 |
| immutable_checkpoints_unetpp | **PASS** | ec7eb13f32e43af27eab7fc617bd1a2a8fcce1d6651a1b4a3653f3e4d1283269 |
| immutable_checkpoints_deeplabv3plus | **PASS** | f519027ba1a3a4d6212d83fecd4379f61f71bc05b0751924b9660da08d597dad |
| immutable_phase12_comparator_case_metrics | **PASS** | 080f158fb8b3e3552ac7854c6d9a116e11564bcefa9efdcdbb3511dba090b436 |
| immutable_phase12_comparator_component_metrics | **PASS** | d66933a3c2821d3ab9375eadb5c0540fea145edcf49b648064fe9aa4c460c753 |
| immutable_phase12_comparator_geometry | **PASS** | 29326d5b9a3bf71add74d8743750511f146d8c4dfbd1dc5b04a5e1b647c37cc0 |
| immutable_part1c_proposals_case_table | **PASS** | d25c44ec1361365e261d36458e86e707ad3bcb58cf000763a732605db0f856ed |
| immutable_part1c_proposals_proposals | **PASS** | 8c3151a3f1f9a56f0692c6ff2d2171472a777a56e99fa2e474aff8a3478a564a |
| immutable_part1c_proposals_component_coverage | **PASS** | 2a3623fecbc1fc5dd5a2c2a12fbd6d5e78fe2e123a9c45431ba53ca14e4e4b87 |
| immutable_part1c_proposals_size_stratified | **PASS** | 147d3947d53fce5102ad290d8caa5f19ccb3eebcc61f75634fcb261780c792f9 |
| immutable_part1c_proposals_gallery_selection | **PASS** | 1fcbc0ae93e1b63ef3b7c3f045af740e9c353cb7635fd5c98e61d31e177d49d3 |
| test_reads_zero | **PASS** | TEST never read |

## Defects found and corrected before artifact release

### PART1D_B_ORACLE_VARIANT_LOOKUP_DEFECT

- detected by: `ORACLE_SOURCE_GUARD (D_O - D_G must reproduce the frozen Phase-12 oracle Dice gain to 1e-4)`
- symptom: first execution produced D_O == D_G exactly and RETENTION_DICE = None for all four models
- cause: the case-model builder indexed the ORACLE columns from the GLOBAL_NATIVE variant index instead of a separate ORACLE_FLOAT_GLOBAL_RETAINED index
- effect: all oracle_* columns and every oracle-dependent retention quantity were wrong
- disclosure: NOT hidden; the defective run was discarded and the phase re-executed after the fix
- residual risk: NONE - a permanent guard now fails loud if D_O - D_G does not match the frozen gain
- artifact released with defect: **NO**

## Counters

training **0** · optimizer **0** · localizer forwards **0** · proposal generation **0** · grid configs **0** · oracle reruns **0** · TEST reads **0** · gate verdict **NOT_DECIDED**

## Continuity

- phase13_part1d_a_r1: **COMPLETE_PASS_FROZEN**
- phase13_part1e_a_gate_criteria: **COMPLETE_PASS_FROZEN**
- phase13_part1d_b: **COMPLETE_PASS**
- phase13_part1e_b_gate_adjudication: **ELIGIBLE_FOR_SUPERVISOR_AUTHORIZATION**
- phase13_part1e_b_authorized: **False**
- regional_integration_gate_after_phase13: **NOT_DECIDED**
- phase14: **NOT_STARTED**

**next_action: `WAIT_FOR_SUPERVISOR_PHASE13_PART1E_B_GATE_ADJUDICATION_AUTHORIZATION`**
