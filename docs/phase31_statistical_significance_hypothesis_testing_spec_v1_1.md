# Phase 31 — Statistical Significance & Hypothesis Testing
## Specification v1.1 — Artifact Status Completeness & Execution-Eligibility Reconciliation

**Specification revision:** `ra_medfilm_barr_phase31_statistics_v1_1`
**Classification:** `ARTIFACT_STATUS_COMPLETENESS_AND_EXECUTION_ELIGIBILITY_RECONCILIATION`
**Method:** RA-MedFiLM-BARR
**Status:** SPECIFICATION v1.1 COMPLETE — **no statistical execution eligible**
**Generated:** 2026-10-04T05:49:23+00:00

`science_changed = false` · `new_statistics_computed = false` ·
`Phase30 numerical result changed = false` · `hypothesis classifications changed = false`.
Only artifact completeness / execution-eligibility semantics were repaired.

---

## 1. Repairs in v1.1

**Defect 1 — hypothesis matrix status column.** The v1.0 CSV header carried
`current_Phase31_status` but all 10 data rows were empty (a key-name lookup defect). v1.1 populates
exactly one status per row; counts reconcile to 10. The **scientific classification is unchanged**
from the v1.0 Markdown.

**Defect 2 — completeness semantics.** v1.0 reported "20/21 COMPLETE + 1 BLOCKING (confirmatory
execution eligibility)" while simultaneously reporting `specification_complete = true` and
`unresolved_provenance_items = []`. v1.1 separates **specification completeness** from **execution
eligibility**:

* `specification_complete = true`
* `unresolved_specification_items = 0`
* `confirmatory_execution_eligible = false` (reason `NO_CONFIRMATORY_PREOUTCOME_EXACT_METHOD_FROZEN`)
* `exploratory_execution_eligible = false`

A resolved negative eligibility result is **not** an unresolved specification blocker.

**Defect 3 — exploratory execution eligibility.** T01 (naive 875-row sample-level paired Wilcoxon)
violates the frozen group-dependence ruling (875 rows / 628 groups) and is dispositioned
`POST_HOC_EXPLORATORY_CONCEPT_ONLY__CURRENT_FORM_FORBIDDEN_BY_GROUP_DEPENDENCE`. T02 (new bootstrap
p-value estimand) is not authorized by the frozen bootstrap reuse scope and is dispositioned
`POST_HOC_EXPLORATORY_CONCEPT_ONLY__BOOTSTRAP_PVALUE_NOT_AUTHORIZED_BY_FROZEN_REUSE_SCOPE`.
No replacement procedure is invented.

## 2. Hypothesis status counts (v1.1)

| status | count |
|---|---|
| CONFIRMATORY_PREOUTCOME_EXACT_METHOD_FROZEN | 0 |
| PREOUTCOME_HYPOTHESIS_METHOD_INCOMPLETE | 1 |
| ALREADY_ADJUDICATED_BY_PREDECESSOR_PHASE | 5 |
| DESCRIPTIVE_ONLY_BY_PREDECESSOR_AUTHORITY | 2 |
| POST_HOC_EXPLORATORY_ONLY | 1 |
| FORBIDDEN_OR_OUT_OF_SCOPE | 1 |
| **total** | **10** |

## 3. Execution eligibility (frozen)

* `confirmatory_execution_eligible = false` — `NO_CONFIRMATORY_PREOUTCOME_EXACT_METHOD_FROZEN`
* `exploratory_execution_eligible = false` — `CURRENT_EXPLORATORY_CANDIDATES_NOT_EXECUTABLE_UNDER_`
  `FROZEN_CLUSTER_AND_BOOTSTRAP_REUSE_CONSTRAINTS`
* `statistical_execution_required_for_phase31_closure = false`

**All 4 registry tests: `execution_authorized = false`, `execution_eligible = false`.**
Confirmatory executable = 0; exploratory executable = 0; descriptive statistical executions = 0;
method-incomplete executable = 0.

This does **not** mean exploratory analyses are scientifically impossible forever. It means **no
exact exploratory procedure is currently frozen and authorized for execution**; any future
exploratory analysis would require a separate, explicitly post-hoc protocol and supervisor
authorization.

## 4. Scientific interpretation

The provenance audit found **no new confirmatory hypothesis test that can legitimately be executed
after Phase30**. Existing claim-bearing questions were already adjudicated, descriptive-only,
method-incomplete, post-hoc exploratory, or forbidden/out-of-scope. Phase31 therefore contributes
**STATISTICAL CLAIM-GOVERNANCE / PROVENANCE ADJUDICATION** rather than a newly manufactured p-value.

The correct statement is **"NO NEW CONFIRMATORY SIGNIFICANCE PROCEDURE IS ELIGIBLE."**
It is **not** correct to say "no significance exists" or "the method is not significant."

## 5. Phase30 boundary (unchanged)

macro ΔDice `+0.0017390308610248934` · 95% CI
`[0.00111729355352301, 0.0024049809029647283]` · `PRESERVATION_ASSERTED = true` ·
Phase30 p-values = 0. Qualifier remains mandatory:
`ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_SCIENTIFIC_SOURCE_FREEZE_DEVIATION`.
No Phase31 repair may upgrade Phase30 canonicality.
