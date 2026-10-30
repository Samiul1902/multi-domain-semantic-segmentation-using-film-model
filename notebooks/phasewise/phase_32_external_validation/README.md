# Phase 32 — External Dataset & Domain Shift Evaluation

- **Phase ID:** phase_32_external_domain_shift
- **Scientific Title:** External Dataset & Domain Shift Evaluation
- **Status:** `COMPLETE_CANONICAL` (governance-only; NO external execution performed)
- **Revision:** `ra_medfilm_barr_phase32_external_domain_shift_v1_0`
- **Classification:** `PRE_EXECUTION_EXTERNAL_PROVENANCE_AND_DOMAIN_SHIFT_SPECIFICATION`

## Scientific question

How does the frozen RA-MedFiLM-BARR system generalize under external dataset / domain shift?
This is **external/domain-shift evidence only** — not training, model/threshold/policy selection,
calibration, or a Phase39 TEST substitute.

## Discovery (metadata / filesystem only)

* No project-declared external root exists in `D:/Softfors/jup`.
* A **legacy external root** was found: `D:/Softfors/final/external_test_ds` (predecessor
  **MedFiLM-Seg** project) — 19 candidates discovered on disk + 3 legacy result documents.
* Additional non-project datasets upstream at `D:/Softfors/omni_seg/data_raw`.

## Historical exposure (load-bearing)

The legacy notebooks reference the external cohorts heavily (`external_test_ds` ×1523,
`CVC-ClinicDB` ×659, `HAM10000` ×306, `BrEaST` ×233, `MILK10k` ×192, `OrthoFrac` ×173,
`DentIRO` ×157, `BDCXR` ×150, `GastroEndoNet` ×61) and legacy result documents exist.
**No discovered cohort may be called an untouched external validation set.**

## Role classification

| role | count |
|---|---|
| PRIMARY_EXTERNAL_DOMAIN_SHIFT_COHORT | **0** |
| SECONDARY_EXTERNAL_DOMAIN_SHIFT_COHORT | **0** |
| HISTORICALLY_EXPOSED_EXTERNAL_BENCHMARK | 8 |
| SUPPLEMENTARY_STRESS_TEST_ONLY | 0 |
| INELIGIBLE (task mismatch / provenance / overlap) | 11 |

## Conclusion

**No prospective clean external cohort is eligible.** Every discovered candidate is historically
outcome-exposed, task/annotation-incompatible, not genuinely external, or provenance-ambiguous.
Phase32 external execution is **NOT authorized** on the currently available cohorts.

## Terminal

`PHASE32_EXTERNAL_DOMAIN_SHIFT_SPEC_COMPLETE__NO_PROSPECTIVE_CLEAN_EXTERNAL_COHORT_ELIGIBLE__HISTORICAL_AND_STRESS_TEST_EVIDENCE_CLASSIFIED__EXECUTION_NOT_AUTHORIZED`

## Phase30 qualifier (mandatory)

`ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_SCIENTIFIC_SOURCE_FREEZE_DEVIATION` —
Phase30 remains `COMPLETE_WITH_PROTOCOL_DEVIATION__NOT_COMPLETE_CANONICAL`, not upgraded.

<!-- PHASE32_GOVERNANCE_ONLY_FINAL_CLOSURE -->
## Phase 32 closure (governance-only external provenance & domain-shift eligibility)

**Status:** `COMPLETE_CANONICAL` · **Closure class:**
`GOVERNANCE_ONLY_EXTERNAL_PROVENANCE_AND_DOMAIN_SHIFT_ELIGIBILITY_CLOSURE__NO_NEW_EXTERNAL_EXECUTION`

**Reviewer notebook:** `phase32_external_domain_shift_review.ipynb` (read-only; no external image/GT
read, no model, no metric computation).

**Counts (frozen):** 19 discovered candidates · 9 historically outcome-exposed · 8
`HISTORICALLY_EXPOSED_EXTERNAL_BENCHMARK` · 2 `INELIGIBLE_OVERLAP_RISK` · 4
`INELIGIBLE_PROVENANCE_AMBIGUOUS` · 5 `INELIGIBLE_TASK_MISMATCH` · **0 primary · 0 secondary · 0
supplementary stress-test**. The 9-vs-8 difference is expected: `EXT-13` (duplicate CVC copy) is
exposed but assigned overlap-risk.

**Historical cohorts may be described only as** `HISTORICALLY_EXPOSED_EXTERNAL_BENCHMARK` /
`HISTORICAL_EXTERNAL_EVIDENCE` — never as new/untouched/prospective/independent validation.

**Downstream:** `ROUTER_HOLDOUT` = `OPENED_AND_FROZEN__NO_PHASE32_REREAD`; `TEST` =
`LOCKED_UNTIL_PHASE39`; **Phase33 = `ELIGIBLE_NOT_STARTED`** (Final System Failure & Boundary Error
Analysis).

**Terminal:** `PHASE32_EXTERNAL_DOMAIN_SHIFT_GOVERNANCE_COMPLETE_CANONICAL__NO_PROSPECTIVE_CLEAN_EXTERNAL_COHORT_ELIGIBLE_AND_NO_EXTERNAL_EXECUTION_PERFORMED__PHASE31_AND_PHASE32_REVIEWER_NOTEBOOKS_PACKAGED__PHASE30_QUALIFIER_PRESERVED__PHASE33_ELIGIBLE_NOT_STARTED`
