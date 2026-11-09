# POST-PHASE-13 R1-H1 — SELECTIVE-ACCEPTANCE HYPOTHESIS ADJUDICATION

- status: **PASS**
- hypothesis: **`H1_FIRST_SELECTIVE_ACCEPTANCE`**
- **H1 OUTCOME: `H1_PARTIAL_MITIGATION_INSUFFICIENT_AS_STANDALONE_REVISION`**
- integrity precondition: **PASS**
- new numerical thresholds **0** · new configs **0** · new subgroup **0** · winner **NONE** · selected threshold **NONE**
- created (UTC): `2026-09-22T07:15:00Z`

## The H1 question

> Is selective proposal acceptance / abstention, with all other scientific axes frozen, **sufficient** to
> make the current GT-free regional path a credible standalone revision?

H1 does **not** ask whether selectivity helps at all. It asks whether selectivity **alone** adequately
resolves the Phase-13 deployable failure while retaining meaningful regional utility.

## Integrity precondition

| check | result |
|---|---|
| R1 evaluation status PASS | **PASS** |
| R1 integrity failures `[]` | **PASS** |
| C0 reproduction PASS | **PASS** |
| C1 membership == C3 | **PASS** |
| C1 output == C3 | **PASS** |
| 28-row model-policy summary | **PASS** |
| 7-row policy intervention summary | **PASS** |
| 7-row cross-architecture summary | **PASS** |
| R0 clarification scope intact | **PASS** |

## Dimension A — `GLOBAL_PRESERVATION` → **NOT_RESTORED**

**Does selective abstention restore acceptable global preservation? NO.**

Every one of the **28 / 28** config/model combinations has policy macro Dice **below GLOBAL**.

| model | GLOBAL | C5 policy | C5 delta | C5 mean FP delta | C5 cases worse |
|---|---|---|---|---|---|
| UNet | 0.594180 | 0.463044 | **−0.131136** | +1770 | 93 |
| Attention U-Net | 0.629805 | 0.485950 | **−0.143855** | +1974 | 93 |
| UNet++ | 0.640516 | 0.482567 | **−0.157948** | +2177 | 92 |
| DeepLabV3+ | 0.560251 | 0.426495 | **−0.133755** | +2274 | 94 |

Selectivity sharply reduces the FP burden (mean FP delta +7778 → ≈+2049, a **74% reduction**) and roughly
halves the Dice deficit — but the burden remains **positive** for every policy and the deficit is never
closed. Case worsening is essentially unchanged at **93.0–94.5 of 103** under every policy.

## Dimension B — `REGIONAL_UTILITY_RETENTION` → **PARTIAL, INSUFFICIENT**

Component **losses are 0** for every policy and architecture, and empty recoveries are largely retained
(C0 8/3/5/11 → C5 8/3/5/10). **But** component recoveries collapse under aggressive selectivity:

| policy | recoveries (UNet / Attn / UNet++ / DeepLab) | total |
|---|---|---|
| R1-C0 | 16 / 9 / 14 / 16 | **55** |
| R1-C1 (= C3) | 2 / 1 / 3 / 4 | **10** |
| R1-C5 | 2 / 1 / 3 / 4 | **10** |

`RETENTION_DICE` is **negative in all 28 / 28** config/model combinations. No policy converts the oracle
mechanism into positive deployable benefit.

## Dimension C — `INTERVENTION_SELECTIVITY` → **IMPROVED** (the one clearly positive dimension)

| quantity | R1-C0 | R1-C5 |
|---|---|---|
| accepted proposals | **494** | **102** |
| GT-miss accepted proposals | **372** | **68** |
| accepted GT-miss fraction | 0.753036 | **0.666667** |
| mean accepted per image | 4.796 | 0.990 |
| mean intervention union area | 0.004846 | 0.001486 |
| mean policy precision | 0.2342 | **0.4259** |
| mean policy recall | 0.6664 | 0.6502 |

Selectivity **does** improve intervention precision, and recall is essentially unchanged. However two
thirds of the surviving interventions (68/102 = **0.666667**) are still off-target. GT fields are
post-freeze descriptive evaluation only; **membership was label-blind**.

## Dimension D — `CROSS_ARCHITECTURE_CONSISTENCY` → **GENERAL, NOT ARCHITECTURE-SPECIFIC**

The negative Dice-vs-GLOBAL behaviour holds in all four architectures for every policy (28/28 below
GLOBAL). At R1-C5: cases worse in all four **84 / 103** · components recovered by ≥1 architecture **6** ·
recovered by all four **1** · lost by ≥1 architecture **0**. Every architecture improves under aggressive
selectivity *and* loses recovery at the same time. **No winner, no ranking.**

## §8 Trade-off adjudication — pattern exactly reproduced

> **MILD selectivity** preserves recovery but barely relieves the global Dice / FP failure;
> **AGGRESSIVE selectivity** substantially relieves FP but removes most component-recovery benefit and
> still remains below GLOBAL.

**Pattern supported: YES.**

| policy | accepted/img | mean macro Dice | mean Δ vs GLOBAL | mean FP delta | total recoveries |
|---|---|---|---|---|---|
| R1-C0 | 4.796 | 0.2999 | −0.306293 | +7778 | 55 |
| R1-C2 (mild) | 4.311 | 0.3054 | −0.300817 | +7598 | **55** |
| R1-C4 (mild) | 3.612 | 0.3219 | −0.284332 | +7118 | 52 |
| R1-C6 (mild) | 3.272 | 0.3314 | −0.274773 | +6829 | 41 |
| R1-C1 / C5 (aggressive) | 1.000 / 0.990 | 0.4608 / 0.4645 | −0.145387 / −0.141674 | **+2075 / +2049** | **10 / 10** |

Mild selectivity reproduces the C0 recovery profile exactly (C2: 16/9/14/16) while relieving only **2%** of
the FP burden. Aggressive selectivity relieves **74%** of the FP burden but destroys **82%** of the
recoveries. No eighth policy was searched, no threshold interpolated, no best policy declared.

## H1 outcome and reasoning

**`H1_PARTIAL_MITIGATION_INSUFFICIENT_AS_STANDALONE_REVISION`**

Dimension C is clearly positive. Dimensions A and B are materially improved but **not resolved**: all 28
config/model combinations remain below GLOBAL, the most aggressive policy still trails by 0.131–0.158, the
FP burden remains positive everywhere, and `RETENTION_DICE` is negative in all 28. The trade-off is strict
and no frozen policy jointly restores global preservation **and** retains enough regional utility.

> **H1 does NOT establish a representation failure.** H1 isolated the acceptance-only axis, and its
> insufficiency leaves localizer representation, heatmap confidence calibration, proposal ranking, training
> objective, checkpoint-selection semantics and precision/recall balance as open contributors for H2
> protocol design.

## H2 eligibility

- `H2_LOCALIZER_RETRAINING_OR_SELECTION_REDESIGN`: **ELIGIBLE_FOR_PROTOCOL_DESIGN**
- `AUTHORIZED_FOR_TRAINING`: **NO**
- No H2 issue is changed in this task.

## Bounded search closure

R1 candidate family **CLOSED**. `POST_HOC_R1_EXPANSION: FORBIDDEN` — no R1-C7, no new floor, no new
max-proposal count, no interpolated threshold, no outcome-driven candidate without a new
supervisor-approved scientific protocol.

## Counters

training **0** · optimizer **0** · model constructions **0** · CUDA requests **0** · global forwards **0** ·
regional forwards **0** · localizer forwards **0** · proposal generation **0** · oracle reruns **0** ·
TEST reads **0** · external-test reads **0**

## Continuity

| item | state |
|---|---|
| Phase 13 | **COMPLETE / FROZEN** |
| original regional gate | **REVISE_LOCALIZER / FROZEN** |
| R0 | **COMPLETE / PASS / FROZEN** |
| R1 policy | **COMPLETE / PASS / FROZEN** |
| R1 execution | **COMPLETE / PASS / FROZEN** |
| H1 adjudication | **COMPLETE / PASS** |
| H1 | **CLOSED — PARTIAL_MITIGATION_INSUFFICIENT** |
| H2 protocol design | **ELIGIBLE / NOT AUTHORIZED** |
| H2 training | **NOT AUTHORIZED** |
| Phase 14 | **NOT_STARTED** |
| TEST | **UNTOUCHED** |

**next_action: `WAIT_FOR_SUPERVISOR_H2_PROTOCOL_DESIGN_AUTHORIZATION`**
