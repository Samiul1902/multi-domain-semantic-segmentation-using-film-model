# POST-PHASE-13 REGIONAL REVISION — R0 FAILURE DECOMPOSITION

- status: **PASS**
- branch: **separate post-Phase-13 revision branch** (Phase-13 evidence **not** reopened or rewritten)
- analysis only — **no** training, inference, or proposal regeneration
- input evidence: 494 frozen proposals · 103 cases · 412 case-model rows · 608 component-model rows

## Binding verification (§2)

| binding | SHA-256 | match |
|---|---|---|
| final gate | `4436e6a5e13b99d422cfab1668c3f3f2d43993b4c43b19786308d106185a6c75` | **PASS** |
| Part-1D-B evaluation | `9a9838ac64af5109c13e0625066e6b891068c93ef5b726f89f03a65e4828ad28` | **PASS** |
| Part-1C proposals (494) | `8c3151a3f1f9a56f0692c6ff2d2171472a777a56e99fa2e474aff8a3478a564a` | **PASS** |
| Part-1C case proposals (103) | `d25c44ec1361365e261d36458e86e707ad3bcb58cf000763a732605db0f856ed` | **PASS** |
| Part-1C component coverage | `2a3623fecbc1fc5dd5a2c2a12fbd6d5e78fe2e123a9c45431ba53ca14e4e4b87` | **PASS** |
| Part-1D-B case-model (412) | `53e93982c0235e32568e01fbddbdd858d205077e3e0a50fd69bef992454f2658` | **PASS** |
| Part-1D-B component-model (608) | `f82e0632898467d32916eb0b71a9fff75818548665477052e2db9b365d313c9d` | **PASS** |

`final_gate_verdict == REVISE_LOCALIZER` confirmed.

## §5 Proposal score / rank diagnostics

| rank | n | pixel-hit count | hit rate | score mean | score median | saturated | saturated frac | mean area frac |
|---|---|---|---|---|---|---|---|---|
| 1 | 103 | 35 | 0.339806 | 0.125063 | 0.125065 | 102 | 0.990291 | 0.001496 |
| 2 | 103 | 41 | 0.398058 | 0.124655 | 0.125065 | 91 | 0.883495 | 0.001260 |
| 3 | 102 | 18 | 0.176471 | 0.123043 | 0.125065 | 67 | 0.656863 | 0.001067 |
| 4 | 96 | 14 | 0.145833 | 0.122230 | 0.125012 | 48 | 0.500000 | 0.000619 |
| 5 | 90 | 14 | 0.155556 | 0.120720 | 0.123366 | 29 | 0.322222 | 0.000549 |

**GT-hit proposals 122 · GT-miss proposals 372 · GT-miss fraction 0.753036.** No threshold is tuned or
called optimal here.

## §6 Score separability (diagnostics only)

| statistic | value |
|---|---|
| ROC-AUC score → pixel hit | **0.670611** |
| PR-AUC score → pixel hit | **0.305819** |
| base rate | 0.246964 |
| PR-AUC lift over base rate | 1.238317 |
| ROC-AUC rank → pixel hit | 0.634431 |
| hit score mean / median | 0.124987 / 0.125065 |
| miss score mean / median | 0.122639 / 0.125065 |
| score min / max / range / IQR | 0.100348 / 0.125065 / 0.024717 / 0.000533 |
| unique score values | 76 |
| saturated (== max) count / fraction | **337 / 0.682186** |
| saturated pixel-hit rate | **0.335312** |
| below-max pixel-hit rate | **0.057325** |

**Key finding.** The proposal score is **near-degenerate**: 68.22% of proposals sit exactly at the
maximum 0.125065 and the IQR is 0.000533. It is nevertheless **informative** — saturated proposals hit
GT at 0.3353 versus 0.0573 below the maximum (**5.85×**), with ROC-AUC 0.671. Reported strictly as
diagnostics, **not** deployment-performance claims; **no threshold was chosen from labels**.

**Rank caveat.** With 102/103 rank-1 and 91/103 rank-2 proposals saturated, ordering *within* the
saturated group is effectively a tie-break; rank-2's higher hit rate (0.398) than rank-1 (0.340) is
consistent with arbitrary tie ordering rather than a meaningful confidence ordering.

### Floor trade-off — floors are label-blind marginal quantiles

| floor | derivation | accepted | accepted hits | off-target accepted | hits lost | off-target removed | off-target removed frac |
|---|---|---|---|---|---|---|---|
| 0.100000 | frozen proposal threshold (baseline) | 494 | 122 | 372 | 0 | 0 | 0.000000 |
| 0.119470 | marginal q10, **no GT labels** | 444 | 122 | 322 | **0** | **50** | 0.134409 |
| 0.124532 | marginal q25, **no GT labels** | 372 | 118 | 254 | 4 | 118 | 0.317204 |
| 0.125065 | marginal max, **no GT labels** | 337 | 113 | 224 | 9 | 148 | 0.397849 |

Every label-blind floor removes **far more off-target proposals than GT-hit proposals**. The q10 floor
is strictly dominant: 50 off-target removed at **zero** hit cost.

## §7 Case-level off-target burden (103 rows)

| quantity | mean | median | min | max |
|---|---|---|---|---|
| proposal count | 4.796 | 5 | 2 | 5 |
| GT-hit proposal count | 1.184 | 1 | 0 | 5 |
| GT-miss proposal count | 3.612 | 4 | 0 | 5 |
| fraction proposals off-target | 0.749515 | 0.800 | 0.000 | 1.000 |
| proposal union area fraction | 0.004846 | 0.003668 | 0.001200 | 0.021164 |
| off-target union area fraction | 0.002413 | 0.002026 | 0.000000 | 0.009877 |
| top proposal score | 0.125063 | 0.125065 | 0.124852 | 0.125065 |

Minimum accepted score under the old policy: **0.10**. Off-target union area is derived
**deterministically** from frozen clip geometry + frozen GT-hit flags. **No new inference.**

## §8 Proposal burden → segmentation linkage (Spearman rho)

| x quantity | y quantity | UNet | Attention U-Net | UNet++ | DeepLabV3+ |
|---|---|---|---|---|---|
| off_target_support_fraction | fp_pixel_delta | **0.6282** | **0.6372** | **0.6080** | **0.5918** |
| total_proposal_count | fp_pixel_delta | 0.2509 | 0.2520 | 0.2613 | 0.2559 |
| gt_miss_proposal_count | fp_pixel_delta | 0.2208 | 0.1904 | 0.0960 | 0.1535 |
| gt_miss_proposal_count | predicted−global Dice | −0.0098 | −0.0634 | −0.0921 | 0.0814 |
| off_target_support_fraction | predicted−global Dice | −0.0687 | −0.1728 | −0.1656 | −0.0506 |
| top_proposal_score | predicted−global Dice | 0.1166 | 0.1066 | 0.1232 | −0.1032 |

**Dominant association.** `off_target_support_fraction` is the strongest descriptor of the FP burden
(**rho 0.5918 – 0.6372**, positive and consistent across all four architectures). Total proposal count
is a weak positive descriptor. GT-miss *count* is only weakly associated with FP delta and essentially
unassociated with Dice delta. Top proposal score is unassociated with Dice delta.

Language: **ASSOCIATION / DESCRIPTIVE LINKAGE — not CAUSE.** No p-value claimed.

## §9 Improved vs worsened case context

Improved cases carry **more** GT-hit proposals (1.60 / 2.20 / 1.75 / 1.73 vs 1.14 / 1.13 / 1.14 / 1.12)
and a **larger** proposal union area (0.00718 / 0.00810 / 0.00709 / 0.00663 vs
0.00460 / 0.00468 / 0.00466 / 0.00463), while GT-miss counts are similar (3.40 / 2.80 / 3.25 / 3.27 vs
3.63 / 3.65 / 3.64 / 3.65). Improved cases have **lower** Part-1C `bbox_covered90` fraction
(0.450 / 0.200 / 0.250 / 0.318 vs 0.629 / 0.633 / 0.642 / 0.647) — improvement concentrates where the
GLOBAL path was already struggling.

**Diagnostic only. No new gate subgroup. No classifier defined.** Implication: improvement and FP burden
both scale with intervention coverage, so reducing accepted proposals trades recovery against FP cost —
exactly the trade-off the bounded R1 ablation must measure.

## §10 Component-recovery context

| model | recovered | recovered bbox_any_overlap rate | lost | not recovered | not-recovered bbox_any_overlap rate |
|---|---|---|---|---|---|
| UNet | 16 | **1.000** | **0** | 136 | 0.830882 |
| Attention U-Net | 9 | **1.000** | **0** | 143 | 0.839161 |
| UNet++ | 14 | **1.000** | **0** | 138 | 0.833333 |
| DeepLabV3+ | 16 | **1.000** | **0** | 136 | 0.830882 |

Every recovered component had `bbox_any_overlap_rate` 1.000 — recovery **requires** at least one
proposal to overlap the component. **Component losses are 0 for all four architectures and must not be
erased by the FP failure.** TINY recoveries 9 / 4 / 5 / 8; SMALL 4 / 2 / 3 / 3; MEDIUM 2 / 3 / 5 / 4;
LARGE 1 / 0 / 1 / 1.

## §11 Hypothesis hierarchy

| rank | hypothesis | status | changed axis |
|---|---|---|---|
| **1** | **H1 SELECTIVE PROPOSAL ACCEPTANCE / ABSTENTION** | **SELECTED AS FIRST REVISION** | which already-produced proposals are accepted |
| 2 | H2 LOCALIZER RETRAINING / SELECTION REDESIGN | not selected — conditional on H1 | model weights / objective / selection |
| 3 | H3 FUSION / ROUTING REDESIGN | not selected — conditional on H1+H2 | fusion function |

H1 holds **constant**: localizer weights · segmentation checkpoints · proposal geometry generation ·
margin 0.20 · NMS 0.30 · regional crop/restore · regional replacement fusion · threshold 0.5.
Zero accepted proposals is an allowed outcome. **Simultaneous change of H1+H2+H3 is forbidden.**

## §18 R0 conclusion — `H1_FIRST_SELECTIVE_ACCEPTANCE`

H1 is the only axis that is simultaneously **(a)** directly implicated by the evidence, **(b)**
achievable with zero training, zero checkpoint change, zero geometry change and zero fusion change, and
**(c)** reversible.

The frozen evidence shows an **intervention-precision** failure, not a representation failure: 122
GT-hit proposals already exist and 27 components are recovered with **0 losses**, so the localizer does
produce usable targets. What is missing is a mechanism to **decline** the 372 off-target proposals — and
the off-target support fraction is the strongest descriptor of the FP burden (rho 0.5918 – 0.6372,
consistent across all four architectures). The score, though saturated, retains moderate discriminative
information (ROC-AUC 0.670611), and every label-blind marginal floor removes strictly more off-target
than GT-hit proposals.

H2 would change the model weights before establishing whether the existing weights are the limiting
factor; H3 would confound the analysis by changing the fusion rule while the accept/reject policy is
still untested.

> This is a **revision-development ordering decision**. It is **not** GO, **not** NO_GO, and **not**
> regional-mechanism promotion.

## Zero-execution counters

training **0** · optimizer **0** · model constructions **0** · CUDA requests **0** · localizer forwards
**0** · segmentation forwards **0** · regional crop forwards **0** · proposal regeneration **0** ·
checkpoint writes **0** · TEST reads **0** · external-test reads **0**

**next_action: `WAIT_FOR_SUPERVISOR_REVISION_R1_AUTHORIZATION`**
