# POST-PHASE13 H2B — OUTCOME ADJUDICATION

- **Status: PASS**
- **Outcome: `H2B_OBJECTIVE_REDESIGN_INSUFFICIENT`**
- Model attribution: Gemini 3.1 Pro High
- Execution mode: `PURE_READ_AUDIT_OF_FROZEN_EVIDENCE`

## 1. Frozen H2B scientific contract

- protocol: `reports/audits/post_phase13_h2b_protocol_frozen.json`
- SHA: `22d4e363a9375bc12828c944b1583921efa77d45b6df7d6387738d13d950949e`
- status: SUPERVISOR_FROZEN_H2B_OBJECTIVE_ONLY_READY_FOR_B1_AUTHORIZATION
- uniquely identified: **YES**

**Scientific question.** Can a SOFT-TARGET objective that directly treats the complete frozen Gaussian target as a continuous supervision signal improve heatmap discrimination and proposal precision while preserving object coverage, holding architecture, target, checkpoint selection, proposal policy and downstream fusion fixed?

**Authorized changed axis.** `LOSS / OBJECTIVE SEMANTICS` (changed fields: 1)

**Prospectively frozen evidence dimensions.** A LOCALIZER_PROPOSAL_QUALITY · B DOWNSTREAM_GLOBAL_PRESERVATION · C REGIONAL_UTILITY · D CROSS_ARCHITECTURE_GENERALITY

**Prospectively frozen outcome space.** `H2B_OBJECTIVE_REDESIGN_SUFFICIENT` · `H2B_OBJECTIVE_REDESIGN_PARTIAL` · `H2B_OBJECTIVE_REDESIGN_INSUFFICIENT` · `CHECK_REQUIRED`

## 2. Outcome-space definitional provenance

- outcome space explicitly frozen: **YES (4 exact labels enumerated in the frozen protocol)**
- explicit decision criteria in protocol: **NO — the protocol freezes the label LIST only; it contains no mapping from evidence to label**
- criteria applied: The project's immediately preceding adjudication (H2-A-C) froze explicit definitions for the IDENTICAL label family (<X>_SUFFICIENT / _PARTIAL / _INSUFFICIENT). Those pre-existing frozen definitions are applied here by inheritance; no new criterion was invented in this task.
- new criteria invented: **NO**
- CHECK_REQUIRED triggered: **NO — the outcome space is explicit; no label was invented.**

## 3. Integrity

- status: **PASS** · B2 integrity gate PASS (488 proposals · 412 case rows · 608 component rows · 4 summary rows · 1952 regional crops · 0 localizer forwards · 0 regeneration · 0 TEST)
- reporting reconciliation: **PASS** (`CHAT_TRANSCRIPTION_ONLY`, scientific_result_changed=NO, notebook_vs_model_summary=PASS)

## 4. Dimension A — Localizer proposal quality

Worse than H2A on **9/9** quality metrics. State: **DEGRADED_RELATIVE_TO_H2A_BASELINE** · supports H2B: **NO**

| metric | H2B | H2A |
|---|---|---|
| proposal_count | 488 | 457 |
| proposal_pixel_any_hit_precision | 0.2151639344262295 | 0.27571115973741794 |
| proposal_bbox_any_hit_precision | 0.21311475409836064 | 0.2735229759299781 |
| tiny_recall90 | 0.6111111111111112 | 0.6944444444444444 |
| overall_recall90 | 0.5921052631578947 | 0.6381578947368421 |
| overall_recall50 | 0.6973684210526315 | 0.8223684210526315 |
| any_overlap_recall | 0.7368421052631579 | 0.875 |
| mean_coverage | 0.6778087714762865 | 0.7878969538240504 |
| roc_auc_score_to_pixel_any_hit | 0.6149073728708193 | 0.7011101520164964 |
| pr_auc_score_to_pixel_any_hit | 0.22895342337838293 | 0.3729361181989911 |
| score_iqr | 0.0 | 0.0016540437936782837 |
| fraction_exactly_at_max | 0.7930327868852459 | 0.6455142231947484 |

## 5. Dimension B — Downstream global preservation

State: **GLOBAL_PRESERVATION_NOT_RESTORED__WORSE_THAN_GLOBAL** · supports H2B: **NO**

| model | H2B Dice | GLOBAL Dice | Δ H2B−GLOBAL | fp_delta_vs_global |
|---|---|---|---|---|
| unet | 0.279848 | 0.594180 | -0.314331 | 9625.621359 |
| attention_unet | 0.290569 | 0.629805 | -0.339236 | 9857.815534 |
| unetpp | 0.294688 | 0.640516 | -0.345827 | 10507.456311 |
| deeplabv3plus | 0.264614 | 0.560251 | -0.295637 | 11031.233010 |

## 6. Dimension C — Regional utility

State: **PARTIAL_RECOVERY_SIGNAL_RETAINED__NET_UTILITY_NOT_ACHIEVED** · supports H2B: **NO**

| model | recoveries vs GLOBAL | losses vs GLOBAL | oracle retention |
|---|---|---|---|
| unet | 10 | 0 | -2.407893 |
| attention_unet | 7 | 0 | -4.860838 |
| unetpp | 11 | 0 | -4.013603 |
| deeplabv3plus | 16 | 0 | -1.554992 |

Cross-architecture: recovered by ≥1 = 22, by all four = 3, lost by ≥1 = 0, lost by all four = 0.

## 7. Dimension D — Cross-architecture generality

State: **CONSISTENTLY_UNFAVOURABLE_ACROSS_ALL_FOUR_ARCHITECTURES** · supports H2B: **NO**

| quantity | value |
|---|---|
| cases_h2b_improved_vs_global_all4 | 2 |
| cases_h2b_nonworse_vs_global_all4 | 2 |
| cases_h2b_worse_vs_global_all4 | 87 |
| cases_h2b_improved_vs_phase13_all4 | 32 |
| cases_h2b_worse_vs_phase13_all4 | 50 |
| components_recovered_vs_global_by_at_least_one | 22 |
| components_recovered_vs_global_by_all4 | 3 |
| components_lost_vs_global_by_at_least_one | 0 |
| components_lost_vs_global_by_all4 | 0 |
| cases_h2b_improved_vs_h2a_all4 | 31 |
| cases_h2b_worse_vs_h2a_all4 | 51 |

## 8. Outcome

### `H2B_OBJECTIVE_REDESIGN_INSUFFICIENT`

H2B changed exactly the authorized axis (loss/objective semantics) and nothing else. The intended direction was improved heatmap discrimination and proposal precision while preserving object coverage. Physically, the H2B best checkpoint was WORSE than the H2A baseline on every localizer quality metric (9/9), and the downstream predicted-region path was worse than GLOBAL, Phase13 predicted and H2A predicted on all four architectures, with a materially larger FP burden. Because the frozen PARTIAL label requires reproducible FAVOURABLE localizer changes, PARTIAL cannot apply; SUFFICIENT plainly cannot apply. The frozen outcome space therefore resolves to INSUFFICIENT.

- H2B proves sole cause: **NO**
- winner: **NONE** · selected threshold: **NONE**
- new numerical thresholds: **0** · new configs: **0** · new subgroups: **0**

## 9. Preserved favourable evidence


- component recoveries vs GLOBAL: 10 / 7 / 11 / 16 (UNet / Attention / UNet++ / DeepLabV3+)
- component losses vs GLOBAL: 0 for all four
- components recovered vs GLOBAL by >=1 architecture: 22 (by all four: 3)
- components lost vs GLOBAL by >=1 architecture: 0

## 10. H2C eligibility

- H2C protocol design: **ELIGIBLE_FOR_SUPERVISOR_AUTHORIZATION**
- H2C execution: **NOT_AUTHORIZED**
- H2C designed in this task: **NO**
- basis: Frozen protocol branch if_h2b_insufficient: representation/head redesign MAY_BECOME_ELIGIBLE_NOT_AUTHORIZED; h3 fusion redesign FUTURE_AXIS_NOT_AUTHORIZED.

## 11. Zero execution

training 0 · optimizer 0 · model constructions 0 · CUDA 0 · localizer forwards 0 · segmentation forwards 0 · proposal generation 0 · oracle reruns 0 · TEST reads 0 · external TEST reads 0

## 12. Continuity

| item | state |
|---|---|
| phase13 | COMPLETE_FROZEN |
| original_gate | REVISE_LOCALIZER_FROZEN |
| h1 | CLOSED |
| h2a | CLOSED__SELECTION_REDESIGN_PARTIAL |
| h2b_b1 | COMPLETE_PASS_FROZEN |
| h2b_b2 | COMPLETE_PASS_FROZEN |
| h2b_reporting_reconciliation | COMPLETE_PASS |
| h2b_outcome_adjudication | COMPLETE_PASS |
| h2b | CLOSED__OBJECTIVE_REDESIGN_INSUFFICIENT |
| h2c | PROTOCOL_DESIGN_ELIGIBLE_NOT_AUTHORIZED |
| phase14 | NOT_STARTED |
| test | UNTOUCHED |

**next_action:** `WAIT_FOR_SUPERVISOR_H2C_PROTOCOL_DESIGN_AUTHORIZATION`
