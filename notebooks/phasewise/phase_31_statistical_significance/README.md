# Statistical Significance & Hypothesis Testing (phase_31_statistical_significance)

## 1. Scientific Overview
- **Phase ID:** phase_31_statistical_significance
- **Scientific Title:** Statistical Significance & Hypothesis Testing
- **Current Status:** COMPLETE_CANONICAL (governance-only; NO NEW STATISTICAL EXECUTION)
- **Core Question:** Phase 31 adjudicates which statistical procedures are legitimately eligible. The roadmap phrase (paired Wilcoxon / bootstrap CIs / Cohen effect sizes) is a TOOLBOX DESCRIPTION, not a preregistration. Conclusion: **NO NEW CONFIRMATORY SIGNIFICANCE PROCEDURE IS ELIGIBLE.**

## 2. Rationale & Academic Significance
Understanding the specific scientific role of this phase within the 41-phase canonical progression (Stage A: KUB Regional/Tiny Development, Stage B: Multi-Domain Scaling, Stage C: Evidence & Rigor, Stage D: Verification & Freeze).

## 3. Inputs & Governance Boundaries
- **Canonical Provenance Source:** docs/phase31_stats_spec.md
- **Dataset Cohorts:** TRAIN and VAL only (TEST strictly locked: TEST reads = 0).
- **Hardware Profile:** NVIDIA GeForce RTX 3060 Ti 8GB certified.

## 4. Primary Outputs & Deliverables
- **Documented Artifacts:** Checkpoints, metrics tables, error maps, and qualitative panels.
- **Reviewer Notebook:** Reviewer-facing reproducible Jupyter Notebook.

## 5. Visual Standards
- **Sample Visualizations:** $\ge 12$ deterministic cases where applicable.
- **Prediction Panels:** $\ge 16$ deterministic cases with TP/FP/FN error maps.

<!-- PHASE31_GOVERNANCE_ONLY_FINAL_CLOSURE -->
## Phase 31 closure (governance-only statistical claim-provenance adjudication)

**Status:** `COMPLETE_CANONICAL` · **Closure class:**
`GOVERNANCE_ONLY_STATISTICAL_PROVENANCE_CLOSURE__NO_NEW_STATISTICAL_EXECUTION` ·
**Scientific role:** `STATISTICAL_CLAIM_GOVERNANCE_AND_PROVENANCE_ADJUDICATION` ·
revision `ra_medfilm_barr_phase31_statistics_v1_1`.

**Conclusion:** **NO NEW CONFIRMATORY SIGNIFICANCE PROCEDURE IS ELIGIBLE.** Unsupported alternatives:
"no significance exists", "the method is not significant", "failed to reach significance".

**Hypotheses (10):** 0 confirmatory / 1 method-incomplete (H6) / 5 already-adjudicated (H1, H2, H4, H5,
P30-PRIMARY) / 2 descriptive-only (H3, P30-A7-COMPANION) / 1 post-hoc exploratory
(P30-A8VSRANDOM-P) / 1 forbidden-or-out-of-scope (C11-JFS).

**Registry (4, none executable):** T01 `...FORBIDDEN_BY_GROUP_DEPENDENCE`; T02
`...BOOTSTRAP_PVALUE_NOT_AUTHORIZED_BY_FROZEN_REUSE_SCOPE`; T03 descriptive-only; T04 method-incomplete.
All `execution_authorized = false`, `execution_eligible = false`.

**Phase30 qualifier (mandatory, not upgraded):**
`ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_SCIENTIFIC_SOURCE_FREEZE_DEVIATION`.
Phase30 numerical result unchanged (macro ΔDice +0.0017390308610248934, 95% CI
[0.00111729355352301, 0.0024049809029647283], `PRESERVATION_ASSERTED = true`, p-values 0).

**Downstream:** ROUTER_HOLDOUT `OPENED_AND_FROZEN__NO_PHASE31_RAW_REREAD` (not reusable as a new clean
holdout); TEST `LOCKED_UNTIL_PHASE39`; **Phase32 `ELIGIBLE_NOT_STARTED`** (External Dataset & Domain
Shift Evaluation).

**Terminal:** `PHASE31_STATISTICAL_CLAIM_GOVERNANCE_COMPLETE_CANONICAL__NO_NEW_CONFIRMATORY_OR_EXPLORATORY_STATISTICAL_EXECUTION_ELIGIBLE_OR_REQUIRED__PHASE30_PROTOCOL_DEVIATION_QUALIFIER_PRESERVED__PHASE32_ELIGIBLE_NOT_STARTED`

<!-- PHASE31_REVIEWER_NOTEBOOK -->
## Reviewer notebook

`phase31_statistical_significance_review.ipynb` — post-closure read-only evidence packaging
(`POST_CLOSURE_READ_ONLY_REVIEWER_NOTEBOOK__NO_NEW_SCIENTIFIC_EXECUTION`). No statistical estimator,
no inferential function, no model, no raw image/GT read.
