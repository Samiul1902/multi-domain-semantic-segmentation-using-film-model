# PHASE-13 PART-1E-A — REGIONAL INTEGRATION GATE CRITERIA (PROSPECTIVELY FROZEN)

- status: **`PROSPECTIVE_GATE_CRITERIA_FROZEN_BEFORE_PART1D_B_RESULTS`**
- freeze time (UTC): `2026-09-22T04:18:00Z`
- gate id: **`REGIONAL_INTEGRATION_GATE_AFTER_PHASE13`**
- gate state: **`NOT_DECIDED`**
- gate mode: **`QUALITATIVE_PROSPECTIVE_EVIDENCE_ADJUDICATION`**
- Part1D-B results inspected: **NO**
- numerical gate thresholds introduced: **0**
- weighted score / rank introduced: **NO** / **NO**
- reference model: **NONE** | model ranking: **NONE**

> These criteria were frozen **before** any Part-1D-B predicted-region result existed. They may
> not be revised after seeing results.

## Authorization

| phase | state |
|---|---|
| Phase 13 Part 1B | COMPLETE / PASS / FROZEN |
| Phase 13 Part 1C | COMPLETE / PASS / FROZEN |
| Phase 13 Part 1D-A-R1 | COMPLETE / PASS / FROZEN |
| Phase 13 Part 1D-B | **ELIGIBLE / NOT YET AUTHORIZED** |

This task performed only the prospective gate-criteria freeze.

## Governance basis

| source | role |
|---|---|
| `docs/DESIGN.md` §11 | gate definition GO / REVISE_LOCALIZER / NO_GO + prospective-freeze requirement |
| `docs/DESIGN.md` §9 | Phase-12 oracle evidence; `ORACLE_MECHANISM_VALUE = SUPPORTED_DESCRIPTIVE_EVIDENCE` |
| `docs/RULES.md` §12 | prospective gate freeze; **no** post-hoc numerical GO/NO-GO thresholds |
| `docs/RULES.md` §9 | evidence discipline; no fabricated metrics; no significance claim unless tested |
| `reports/tables/regional_integration_gate_state_after_phase12.csv` | pre-existing dimension state A/B/C/D |
| `reports/audits/phase13_part1d_predicted_region_protocol_frozen_r1.json` | Part-1D R1 boundary; gate verdict **FORBIDDEN** in Part 1D |

## Governance invariants (the anchor)

Phase 12 recorded `ORACLE_MECHANISM_VALUE = SUPPORTED_DESCRIPTIVE_EVIDENCE`.

- a poor Part-1D-B predicted localization result **MUST NOT**, by itself, be relabelled `NO_GO`
- if the Phase-12 oracle evidence remains valid, a poor deployable result maps to
  **`REVISE_LOCALIZER`**
- `NO_GO` requires that the **oracle-mechanism evidence itself** is invalidated or no longer
  scientifically supportable

## The four frozen gate dimensions

### A — `ORACLE_MECHANISM_VALUE`

*Does the Phase-12 oracle experiment continue to provide credible descriptive evidence that
regional high-resolution processing has mechanistic value?*

- state before Part-1D-B: **`SUPPORTED_DESCRIPTIVE_EVIDENCE`**
- Part-1D-B may alter this: **NO** — only if it reveals a material integrity/reproduction defect
  in the Phase-12 evidence itself
- recorded basis: positive aggregate Dice across all four models · mean delta Dice +0.0698 …
  +0.1901 · large object-recall recovery · component recovery · TINY/SMALL recovery · empty
  recovery · difficult-cohort response

### B — `PRACTICAL_LOCALIZATION_RETENTION`

*Does the frozen GT-free predicted-region pipeline retain meaningful downstream segmentation
utility relative to the global baseline and the Phase-12 oracle upper-bound/mechanism result?*

Frozen evidence fields (per model):

`D_GLOBAL` · `D_ORACLE` · `D_PREDICTED` · `DELTA_ORACLE_DICE` · `DELTA_PRED_DICE` ·
`RETENTION_DICE` · `ORACLE_GAP_DICE` · IoU gain retention · object-recall gain retention ·
FN-reduction retention · component recovery events · component lost events · empty recovery
events · new-empty events · localization-coverage → segmentation-recovery linkage

- **no single field alone decides** the dimension
- retention label `PRACTICAL_GT_FREE_ORACLE_BENEFIT_RETENTION`,
  `(D_pred - D_global) / (D_oracle - D_global)`, never clipped, negative and >1 preserved,
  valid only if `delta_oracle > 0`
- "meaningful utility" means **segmentation utility**, not merely proposal coverage

### C — `GLOBAL_PRESERVATION_FP_COST`

*Does predicted regional replacement preserve acceptable global segmentation behavior, or does
it introduce broad adverse segmentation cost?*

Frozen evidence fields (per model):

mean Dice delta PREDICTED-GLOBAL · mean IoU delta · mean precision delta · mean recall delta ·
mean FP pixel delta · mean FN pixel delta · cases improved · cases unchanged · cases worsened ·
maximum case improvement · maximum case worsening · new empty predictions · empty recoveries ·
component recoveries · component losses

- **target recovery MUST always be interpreted together with FP / precision cost**
- state before Part-1D-B: `MIXED_DESCRIPTIVE_EVIDENCE` (Phase-12 oracle evidence)

### D — `GENERALITY`

*Is the practical signal supported across the four frozen architectures rather than being an
architecture-specific accident?*

- architectures: **UNet · Attention U-Net · UNet++ · DeepLabV3+**
- reference model **NONE** · no winner · no rank
- evidence isolated to one architecture is **insufficient by itself** for a GO conclusion
- heterogeneity **MUST** be reported rather than averaged away

## Prospective outcome logic (frozen)

### `GO`

Oracle helps **AND** predicted localization retains meaningful practical utility.

Required pattern: A remains supported · **AND** B shows meaningful practical GT-free downstream
utility rather than merely proposal coverage · **AND** C does not show broad systematic
degradation undermining the practical benefit · **AND** D shows the signal is not merely an
isolated architecture-specific artifact.

→ Promote the regional mechanism toward RA-MedFiLM-Seg++.

> A GO conclusion does **NOT** require predicted performance to equal oracle. Retention >1, <1
> or negative values must be preserved honestly.

### `REVISE_LOCALIZER`

Oracle helps **BUT** predicted localization loses too much practical benefit / global
preservation cost is materially problematic — the regional hypothesis is **not** abandoned, but
the deployable localization/fusion path requires revision.

Required pattern: A remains supported · **AND** at least one of — B is weak, inconsistent or
fails to translate the oracle mechanism into sufficient deployable segmentation utility; C shows
material preservation / FP-cost problems; D indicates the effect is too architecture-specific.

→ Do not abandon the hypothesis; redesign localizer work first. **Do NOT automatically redesign
the localizer in Part 1E.**

> A poor GT-free localizer result **MUST NOT** be relabelled `NO_GO` while A remains supported.

### `NO_GO`

Even oracle evidence is insufficient / invalidated; do not force regional complexity.

Required pattern: **A is no longer scientifically supportable** — e.g. the Phase-12 oracle
mechanism evidence is invalidated by a material integrity/reproduction problem, or no longer
demonstrates meaningful regional mechanism value.

→ Do not force regional complexity; proceed with global multi-domain MedFiLM and document the
negative evidence.

> A poor GT-free localizer result alone **MUST NOT** produce `NO_GO` while A remains supported.

### `CHECK_REQUIRED` — integrity override

Before any GO / REVISE_LOCALIZER / NO_GO decision, if Part-1D-B contains a material unresolved
integrity failure — GLOBAL reproduction failure · checkpoint identity mismatch · wrong
crop/restore semantics · proposal provenance mismatch · wrong population · TEST leakage · metric
mismatch · incomplete 412 / 608 tables — then the gate status becomes **`CHECK_REQUIRED`** and
**NO gate verdict is issued**.

> Scientific integrity takes precedence over gate classification.

## Part-1E-B evidence contract

Part-1E-B may use **only** the prospective Part-1D-B outputs defined before inference:

412-row case-model table · 608-row component-model table · 4-row model summary ·
cross-architecture descriptive summary · Part-1C proposal/localization tables · Phase-12 frozen
oracle tables · Part-1D-B reproduction audit.

- **no** new tuned threshold · **no** post-hoc subgroup invented for gate justification
- predeclared cohorts allowed: **TINY · SMALL · MEDIUM · LARGE · hard-Tiny · global-empty ·
  multi-component**
- the 16-case deterministic gallery is **REVIEW ONLY** and **cannot determine the gate**

## No statistical superiority claim

The gate is a **mechanism-development decision**. It **MUST NOT** be converted into statistical
superiority, model ranking, winner declaration, or clinical superiority. No p-value threshold is
part of the gate. Later formal paired statistics remain governed by the project roadmap.

## Forbidden post-hoc behaviours

- defining any new numerical gate threshold after seeing Part-1D-B
- defining a weighted composite score
- constructing a model rank or declaring a winner
- inventing a post-hoc subgroup to justify the gate
- using the 16-case gallery to determine the gate
- converting the gate into a statistical or clinical superiority claim
- relabelling a poor deployable result as `NO_GO` while A remains supported
- issuing any gate verdict while a material integrity failure is unresolved

## Zero-execution counters

| counter | value |
|---|---|
| training | **0** |
| optimizer_creations | **0** |
| model_constructions | **0** |
| cuda_requests | **0** |
| segmentation_forwards | **0** |
| regional_crop_forwards | **0** |
| localizer_forwards | **0** |
| proposal_generation | **0** |
| test_reads | **0** |
| part1d_b_results_inspected | **NO** |

## Continuity

Phase13 Part1D-A-R1 **COMPLETE / PASS / FROZEN** · Part1E-A gate criteria
**COMPLETE / PASS / FROZEN** · Part1D-B **ELIGIBLE_FOR_SUPERVISOR_AUTHORIZATION**, authorized
**FALSE** · Part1E-B gate adjudication **NOT_STARTED** ·
`REGIONAL_INTEGRATION_GATE_AFTER_PHASE13` **NOT_DECIDED** · Phase14 **NOT_STARTED**.

**next_action: `WAIT_FOR_SUPERVISOR_PHASE13_PART1D_B_INFERENCE_AUTHORIZATION`**
