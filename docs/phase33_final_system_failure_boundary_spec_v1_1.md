# Phase 33 — Final System Failure & Boundary Error Analysis
## Specification v1.1 — Additive Governance Reconciliation of the Failure-Family Summary Partition

**Revision:** `ra_medfilm_barr_phase33_failure_boundary_v1_1`
**Classification:** `ADDITIVE_GOVERNANCE_RECONCILIATION__NO_SCIENTIFIC_ELIGIBILITY_CHANGE`
**Method:** RA-MedFiLM-BARR
**Generated:** 2026-10-04T08:27:49+00:00

---

## 1. What changed in v1.1

v1.1 is an **additive governance reconciliation** of the v1.0 **top-level failure-family summary
partition only**.

In v1.0 (`reports/audits/phase33_failure_taxonomy_contract.json`, SHA
`25691caa5a7509c7b3edbab595136718c31272ef6028f479097a823a1c7c508d`, preserved byte-for-byte):

* the **per-family records were correct** — six families carry `claim_status = INELIGIBLE`;
* `ineligible_families` was correct (6);
* but `eligible_families` incorrectly contained **all 13** families, producing a 6-family overlap
  with `ineligible_families`.

Defect classification:
`GOVERNANCE_SUMMARY_PARTITION_INCONSISTENCY__NO_SCIENTIFIC_CLASSIFICATION_CHANGE`.

**No scientific eligibility changed.** No boundary, component, qualitative, raw-read or rerun ruling
changed. `science_changed = false`; `execution_eligibility_changed = false`.

## 2. Canonical eligible descriptive families (7)

1. `LOW_OVERLAP`
2. `EMPTY_PREDICTION` — **Dice-0 proxy only** (no predicted-positive-area computation authorized)
3. `ROUTER_HARMFUL_ACTIVATION`
4. `ROUTER_MISSED_BENEFIT`
5. `EXECUTE_THEN_REJECT`
6. `DOMAIN_SPECIFIC_FAILURE`
7. `GROUP_OR_PATIENT_CLUSTERED_FAILURE`

## 3. Canonical ineligible families (6)

1. `FALSE_POSITIVE_BURDEN`
2. `FALSE_NEGATIVE_BURDEN`
3. `OBJECT_MISS`
4. `MULTI_COMPONENT_PARTIAL_DETECTION`
5. `MULTI_COMPONENT_COMPLETE_MISS`
6. `BOUNDARY_ERROR`

## 4. Partition invariants

| invariant | value |
|---|---|
| eligible_family_count | 7 |
| ineligible_family_count | 6 |
| total_family_count | 13 |
| eligible_ineligible_overlap_count | 0 |
| eligible_ineligible_disjoint | true |
| eligible_ineligible_union_count | 13 |
| every_family_classified_exactly_once | true |

## 5. Execution eligibility (unchanged)

table-only **true** · derived non-pixel **true** · prediction-pixel false · raw image false ·
raw GT false · qualitative gallery false · boundary metric false · component metric false ·
model rerun false · execution_started **false** · Phase34_started **false**.

Execution may begin only after the v1.1 reconciliation passes.
