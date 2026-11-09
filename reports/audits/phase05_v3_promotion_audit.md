# Phase 05 — v3 Promotion Audit

**Status:** `PASS`  
**Generated:** 2026-09-19T19:21:51.427777+00:00  
**Model:** Gemini 3.1 Pro High  
**Phase:** 05 — Final Leakage Remediation Closure (Part 1E)

## Promotion Authorization

- **Supervisor authorized:** YES
- **Basis:** population accounting, TEST immutability, sample disjointness, KUB patient disjointness, BUSI recovered patient-group disjointness, exact duplicate remediation, TRAIN<->VAL d0 high-risk remediation, TRAIN<->VAL d2 conservative remediation, historical TEST-linked d<=2 development-side quarantine, cross-artifact consistency, BUSI provenance reconciliation

## Governance State

| Item | Value |
|---|---|
| Active development manifest | `phase4_v3` |
| Historical manifest | `phase4_v2` |
| Canonical v3 directory | `manifests/phase4_v3/` |
| v2 status | `HISTORICAL_SUPERSEDED_FOR_FUTURE_DEVELOPMENT` |
| v3 status | `CANONICAL_ACTIVE_DEVELOPMENT` |

## Candidate -> Canonical Hashes

| Artifact | Promoted SHA-256 | Cand==Prom | Prom==Expected |
|---|---|---|---|
| `manifests/phase4_v3/all_paired.csv` | `eb3062fa0e84f9952f994df79ed4d767417a912e18dce86560f6e2edcdd02ded` | YES | YES |
| `manifests/phase4_v3/train.csv` | `28702fc3a5ff8b950db372f03232d335e3a30b1fc2f21db7cd8c066055826ed6` | YES | YES |
| `manifests/phase4_v3/val.csv` | `082c80b2bda63fd73f371f109c34643adf01edaead921643fb2e44993ba53315` | YES | YES |
| `manifests/phase4_v3/test.csv` | `9361eba61c91c034a9aa4988a4df229bba591a5cbd553c98689ac7915da29727` | YES | YES |
| `manifests/phase4_v3/quarantined.csv` | `a4ec1a8c46692f3c2d55d03c73569ce7b44aeeef734abd41e31bf5bf3e60059c` | YES | YES |
| `manifests/phase4_v3/duplicate_groups.csv` | `830d3c0ce08f735081e5a44fe3a740031da1c70cfc19ebcb4ef89c31acd704fb` | YES | YES |
| `manifests/phase4_v3/grouping_provenance.csv` | `3eff84851d33e1c8b5894ce05049433287067a5e6088a90f5c67394230317f66` | YES | YES |

**Candidate -> canonical byte identical:** YES  
**All promoted hashes match brief:** YES

## v2 Immutability

| File | SHA-256 | Unchanged |
|---|---|---|
| `manifests/all_paired.csv` | `66350d465209e4bf0948a16f0da213abb9f8f87c0b222ead7632d2350463f7cc` | YES |
| `manifests/train.csv` | `d67b549a6cc80b579dfaf4976b9b51630f6d703d8c6bfb33188355cfa6056bc3` | YES |
| `manifests/val.csv` | `46079b594ed9535c2de953bb976684b8b0bab30c27c6e6e4f2b9f9314b4cc5f4` | YES |
| `manifests/test.csv` | `9361eba61c91c034a9aa4988a4df229bba591a5cbd553c98689ac7915da29727` | YES |

**v2 hashes unchanged:** YES

## TEST Governance

- **TEST SHA:** `9361eba61c91c034a9aa4988a4df229bba591a5cbd553c98689ac7915da29727`
- **TEST byte-identical v2/v3:** YES
- **TEST membership changed:** NO
- **TEST image reads:** 0
- **TEST mask reads:** 0
- **TEST decodes:** 0
- **TEST visualizations:** 0
- **TEST metrics:** NONE

## Population

| Split | Count |
|---|---|
| TRAIN | 5832 |
| VAL | 808 |
| TEST | 1683 |
| QUARANTINED | 118 |
| ACTIVE TOTAL | 8323 |
| TOTAL (incl. quarantine) | 8441 |

## Quarantine Breakdown (118)

| Reason | Count |
|---|---|
| `QUARANTINED_TEST_LINKED_PATIENT_OVERLAP` | 62 |
| `QUARANTINED_TEST_LINKED_PHASH_HIGH_RISK` | 34 |
| `QUARANTINED_SAME_ACQUISITION` | 13 |
| `QUARANTINED_BUSI_PATIENT_OVERLAP` | 5 |
| `CONSERVATIVE_HIGH_RISK_GROUPING` | 3 |
| `QUARANTINED_EXACT_DUPLICATE` | 1 |

## Leakage Gates

| Gate | Result |
|---|---|
| population_accounting_8441_conserved | PASS |
| test_immutability | PASS |
| sample_id_disjointness | PASS |
| kub_patient_disjointness | PASS |
| busi_recovered_patient_group_disjointness | PASS |
| exact_duplicate_remediation | PASS |
| train_val_d0_high_risk_remediation | PASS |
| train_val_d2_conservative_remediation | PASS |
| historical_test_linked_d_le_2_quarantine | PASS |
| cross_artifact_consistency | PASS |
| busi_provenance_reconciliation | PASS |

## BUSI Provenance

- **Mapping SHA:** `df4b01487ea6e1cb5c004e11535e4c3252c19dc3b84cbb21816c737dbaf2753b`
- **Source metadata SHA:** `14f6bb5332036218e4c59d119d12ea67281b0a4d1373668d35530763f9121d44`

## Manifest Registry

- `manifests/manifest_registry.json`
- `manifests/manifest_registry.md`

## Manifest Guard

- v2 validation: **PASS**
- v3 validation: **PASS**
- unit tests: **PASS** (14 passed in 0.12s)
- test file: `tests/test_manifest_guard.py`

## Clean Rerun Scope

| Phase | Name | Historical v2 | Clean v3 |
|---|---|---|---|
| 06 | Descriptive Dataset Analysis | `COMPLETE` | `RERUN_REQUIRED` |
| 07 | Taxonomy and Labeling | `COMPLETE` | `RERUN_REQUIRED` |
| 08 | Infrastructure Verification | `COMPLETE` | `PARTIAL_RERUN_REQUIRED` |
| 09 | Baseline Model Training | `COMPLETE_v2_CONTAMINATED` | `RERUN_REQUIRED` |
| 10 | Baseline Comparison | `COMPLETE_v2_CONTAMINATED` | `RERUN_REQUIRED` |
| 11 | Failure Analysis | `COMPLETE_v2_CONTAMINATED` | `RERUN_REQUIRED` |
| 12 | Oracle Evaluation | `COMPLETE_v2_CONTAMINATED` | `RERUN_REQUIRED` |
| 13 | Localizer Training | `COMPLETE_v2_CONTAMINATED` | `RERUN_REQUIRED` |
| 14 | Regional Refiner Training | `COMPLETE_v2_CONTAMINATED` | `RERUN_REQUIRED` |
| 15 | Regional Refiner Protocol | `COMPLETE_v2_CONTAMINATED` | `REVALIDATION_REQUIRED` |

**Executed in this task:** NO

## Closure Notebook

- path: `notebooks/phasewise/phase_05_leakage_audit/phase05_manifest_v3_promotion_and_leakage_closure.ipynb`
- SHA-256: `cb6fa37d395022eb0aed7115f29c29e679ba3b63744aeda9925de24668d0592a`
- SHA stable (3x): YES
- code cells: 20 | executed: 20 | unexecuted: 0
- errors: 0 | embedded PNG: 6

## Phase-05 Completion

- scientific gate: **PASS**
- Phase-05 complete: **YES**
- Phase-06 started: NO
- next action: `WAIT_FOR_SUPERVISOR_PHASE06_AUTHORIZATION`
