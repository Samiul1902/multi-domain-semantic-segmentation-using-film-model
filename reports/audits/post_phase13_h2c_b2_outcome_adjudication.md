# POST-PHASE13 H2C-B2 — Outcome Adjudication

- **Status: PASS**
- **Outcome: `H2C_HEAD_REDESIGN_INSUFFICIENT`**
- Frozen rule: `reports/audits/post_phase13_h2c_protocol_frozen.json :: prospective_outcome_definitions`
- New criterion invented: **NO**

## Dimension A — localizer proposal quality

**REPRODUCIBLY_FAVOURABLE_VS_H2A**

| metric | H2C | H2A | delta |
|---|---|---|---|
| tiny_recall90 | 0.750000 | 0.694444 | +0.055556 |
| overall_recall90 | 0.697368 | 0.638158 | +0.059211 |
| mean_coverage | 0.808416 | 0.787897 | +0.020519 |
| score_iqr | 0.004663 | 0.001654 | +0.003009 |
| fraction_at_max | 0.549784 | 0.645514 | -0.095731 |
| roc_auc | 0.756421 | 0.701110 | +0.055311 |
| pr_auc | 0.412665 | 0.372936 | +0.039729 |
| pixel_any_hit_precision (unfavourable) | 0.266234 | 0.275711 | -0.009477 |
| bbox_any_hit_precision (unfavourable) | 0.264069 | 0.273523 | -0.009454 |

## Dimension B — downstream global preservation

**GLOBAL_PRESERVATION_NOT_RESOLVED**

| model | H2C | GLOBAL | delta |
|---|---|---|---|
| unet | 0.300230 | 0.594180 | -0.293950 |
| attention_unet | 0.301089 | 0.629805 | -0.328716 |
| unetpp | 0.304042 | 0.640516 | -0.336474 |
| deeplabv3plus | 0.282357 | 0.560251 | -0.277894 |

## Dimension C — regional utility

**RECOVERY_SIGNAL_PRESENT__NET_UTILITY_NOT_ACHIEVED**
- oracle-benefit retention negative on all four: True
- component losses vs GLOBAL zero on all four: True
- components recovered vs GLOBAL by >=1: 33

## Dimension D — cross-architecture generality

**CONSISTENTLY_BELOW_GLOBAL_ACROSS_ALL_FOUR**

| quantity | value |
|---|---|
| cases_h2c_improved_vs_global_all4 | 3 |
| cases_h2c_nonworse_vs_global_all4 | 3 |
| cases_h2c_worse_vs_global_all4 | 82 |
| cases_h2c_improved_vs_phase13_all4 | 44 |
| cases_h2c_worse_vs_phase13_all4 | 36 |
| components_recovered_vs_global_by_at_least_one | 33 |
| components_recovered_vs_global_by_all4 | 5 |
| components_lost_vs_global_by_at_least_one | 0 |
| components_lost_vs_global_by_all4 | 0 |
| cases_h2c_improved_vs_h2a_all4 | 38 |
| cases_h2c_worse_vs_h2a_all4 | 45 |

## Outcome

### `H2C_HEAD_REDESIGN_INSUFFICIENT`

**Clause applied:** H2C_HEAD_REDESIGN_INSUFFICIENT clause (b): 'favourable localizer changes do not translate into meaningful downstream improvement and the major deployable failure remains'.

The localizer changes ARE reproducibly favourable vs H2A (8/10 metrics, including the targeted saturation/dispersion metrics), so clause (a) does not apply. However the frozen PARTIAL definition additionally requires 'at least some corresponding downstream improvement', measured against the protocol-designated PRIMARY downstream comparator (H2A predicted-region). H2C macro Dice is BELOW H2A on ALL FOUR architectures (-0.013550, -0.019084, -0.019004, -0.006560), so the favourable localizer changes did NOT translate into downstream improvement against the primary comparator. The major deployable failure also remains (H2C is far below GLOBAL on all four; oracle-benefit retention negative on all four). Clause (b) therefore applies.

## Countervailing evidence (disclosed)

This is a CLOSE CALL and is disclosed as such. H2C is roughly at Phase13 level downstream and improves the recovery signal (22 -> 33 components recovered by >=1 architecture, zero losses) and 38/103 cases improve in all four architectures vs H2A. A reader who measures 'downstream improvement' against Phase13 or at case level rather than against the primary comparator H2A could reasonably argue for PARTIAL. The label applied follows the protocol's designated primary downstream comparator.

- H2C−Phase13 Dice: {'unet': -0.0020839589505221, 'attention_unet': -0.0075299017983538, 'unetpp': -0.0073132703836263, 'deeplabv3plus': 0.0050647191103552}
- cases improved vs H2A (all 4): 38 | worse: 45
- components recovered vs GLOBAL by >=1: H2A 22 → H2C 33

## Phase-14 eligibility

- status: **ELIGIBLE_NOT_STARTED**
- basis: H2C protocol if_h2c_insufficient: FURTHER_REVISION = REQUIRES_SUPERVISOR_DECISION; H3 NOT_AUTOMATICALLY_AUTHORIZED. Phase 14 requires separate supervisor authorization.

descriptive single-seed evidence · no winner · no statistical claim
