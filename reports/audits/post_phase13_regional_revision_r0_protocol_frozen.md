# POST-PHASE-13 REGIONAL REVISION — R0 PROTOCOL FROZEN

- status: **`REVISION_PROTOCOL_FROZEN_BEFORE_R1_EXECUTION`**
- branch: separate post-Phase-13 revision branch · Phase-13 evidence **not** reopened
- Phase-13 gate verdict carried forward: **`REVISE_LOCALIZER`**
- oracle mechanism value: **`SUPPORTED_DESCRIPTIVE_EVIDENCE`**
- selected first axis: **`H1_SELECTIVE_PROPOSAL_ACCEPTANCE_ABSTENTION`**

## Revision question

Which single failure axis should be tested **first** — proposal acceptance/abstention (A), localizer
representation/training/selection (B), or regional fusion/gating (C)? The future experiment must change
**only one** primary scientific axis at a time, and the first revision must be the **lowest-complexity
intervention capable of testing a credible explanation of the Phase-13 failure**.

## Safety property relied upon

```
if no predicted proposal is accepted:   PREDICTED output == GLOBAL output   (exactly)
```

Source: the frozen Part-1D-B fusion semantics `P(x) = R(x) if U_pred(x) else G(x)`.
**Consequence: maximum proposal recall is not required — abstention is a legitimate outcome.**

## Selective-abstention principle assessment — **SUPPORTED**

Supporting evidence:

- score retains moderate discriminative information despite saturation (ROC-AUC 0.670611, PR-AUC
  0.305819 vs 0.246964 base rate)
- saturated proposals hit GT at 0.3353 vs 0.0573 below the maximum (5.85×)
- every label-blind marginal floor removes more off-target than GT-hit proposals (q10: 50 off-target, **0** hits)
- off-target support fraction is the strongest descriptor of FP burden (rho 0.5918 – 0.6372, all four architectures)
- the fusion rule already provides exact GLOBAL fallback when nothing is accepted

Counter-evidence recorded (not hidden):

- proposal scores are near-degenerate — 337/494 saturated at 0.125065, range 0.024717, IQR 0.000533
- rank ordering within the saturated group is effectively a tie-break
- improved cases carry **more** GT-hit proposals and **larger** intervention area, so reducing
  intervention may cost recovery

> The hypothesis `SELECTIVE_REGIONAL_INTERVENTION_WITH_ABSTENTION` is **frozen for testing**, **not
> promoted**.

## R1 candidate family — DESIGN ONLY, NOT EXECUTED

`reports/tables/post_phase13_regional_revision_r1_candidate_family.csv` — **7 configurations**
(maximum allowed 8), including the Phase-13 control.

| config | role | score acceptance floor | max accepted proposals | floor derivation |
|---|---|---|---|---|
| **R1-C0** | **CONTROL / BASELINE** | 0.100000 | 5 | frozen Part-1C threshold |
| R1-C1 | candidate | 0.119470 | 1 | marginal score q10 |
| R1-C2 | candidate | 0.119470 | 5 | marginal score q10 |
| R1-C3 | candidate | 0.124532 | 1 | marginal score q25 |
| R1-C4 | candidate | 0.124532 | 5 | marginal score q25 |
| R1-C5 | candidate | 0.125065 | 1 | marginal score max |
| R1-C6 | candidate | 0.125065 | 5 | marginal score max |

- allowed changed fields: **proposal score acceptance floor** · **maximum accepted proposals per image**
- frozen fields: localizer checkpoint · proposal coordinates · margin 0.20 · NMS 0.30 · regional
  crop/restore · segmentation checkpoints · fusion rule · threshold 0.5
- zero accepted proposals: **allowed** · localizer retraining: **NO** · score weighting: **NONE** ·
  new fusion: **NONE**

### Anti-overfitting rule

- family constructed by optimising Part-1D-B Dice outcomes: **NO**
- floors derived from the **marginal** proposal-score distribution **without GT labels**
- `max_accepted` candidates used: **1, 5** (allowed set 1, 2, 3, 5)
- baseline appears as the control: **YES**
- family frozen **before** any candidate-specific segmentation inference: **YES**
- GT labels may **describe** but must **not** change the already-frozen family: **YES**

## R1 evidence dimensions — FROZEN, NO VERDICT

> These letters are **R1-local** and must **not** be confused with the Part-1E-B gate dimensions A–D.

| dim | question | frozen fields |
|---|---|---|
| **R1_A GLOBAL PRESERVATION** | Does selective abstention remove the catastrophic FP / precision cost? | mean Dice/IoU/precision/recall deltas vs GLOBAL · mean FP/FN pixel deltas · cases improved/unchanged/worsened · max improvement/worsening · new empty predictions |
| **R1_B REGIONAL UTILITY RETENTION** | Does any selective policy retain genuine component / empty recovery benefit beyond GLOBAL? | component recoveries · component losses · empty recoveries · new empty predictions · PREDICTED−GLOBAL Dice · object recall |
| **R1_C INTERVENTION SELECTIVITY** | Does the policy reduce off-target proposal intervention? | accepted proposal count · accepted off-target count · accepted support area fraction · cases with zero accepted proposals |
| **R1_D CROSS-ARCHITECTURE CONSISTENCY** | Does the behaviour generalize across all four architectures? | per-architecture direction and magnitude · heterogeneity report · no winner · no rank |

No new numerical GO threshold · no weighted score · no automatic winner. **The future supervisor
adjudication decides whether H1 is viable.**

## Bounded revision budget

- R1 is **ONE** bounded policy-ablation round
- candidate-family expansion after results: **FORBIDDEN without supervisor approval**
- if H1 fails: **STOP — do NOT automatically move to retraining**
- H2 requires a supervisor decision
- open-ended VAL search: **FORBIDDEN**

## Publication / validation discipline

- nature: **adaptive development revision informed by Phase-13 VAL failure evidence**
- VAL remains **development data**; TEST remains **untouched until Phase 39**
- no revision VAL claim can substitute for final TEST evaluation
- no external-test tuning · no hidden candidate search

## Continuity

| item | state |
|---|---|
| Phase 13 | **COMPLETE / FROZEN** |
| original gate | **REVISE_LOCALIZER / FROZEN** |
| regional mechanism promoted | **NO** |
| Phase 14 | **NOT_STARTED** |
| Post-Phase-13 revision R0 | **COMPLETE / PASS** |
| Revision R1 | **ELIGIBLE after supervisor review — NOT AUTHORIZED** |
| TEST | **UNTOUCHED** |

## Zero-execution counters

training **0** · optimizer **0** · model constructions **0** · CUDA requests **0** · localizer forwards
**0** · segmentation forwards **0** · regional crop forwards **0** · proposal regeneration **0** ·
checkpoint writes **0** · TEST reads **0** · external-test reads **0**

**next_action: `WAIT_FOR_SUPERVISOR_REVISION_R1_AUTHORIZATION`**
