# Phase 32 — External Dataset & Domain Shift Evaluation
## Entry Gate + External-Cohort Provenance + Population Ownership + Pre-Execution Specification

**Revision:** `ra_medfilm_barr_phase32_external_domain_shift_v1_0`
**Classification:** `PRE_EXECUTION_EXTERNAL_PROVENANCE_AND_DOMAIN_SHIFT_SPECIFICATION`
**Method:** RA-MedFiLM-BARR
**Status:** SPECIFICATION COMPLETE — **external execution NOT authorized**
**Generated:** 2026-10-04T07:07:24+00:00

> **Phase30 qualifier carried forward (mandatory):**
> `ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_SCIENTIFIC_SOURCE_FREEZE_DEVIATION`
> Phase30 remains `COMPLETE_WITH_PROTOCOL_DEVIATION__NOT_COMPLETE_CANONICAL` — **not upgraded**.

---

## 1. Scientific question

**How does the frozen RA-MedFiLM-BARR system generalize under external dataset / domain shift?**

This is **not** training, model selection, threshold selection, policy selection, calibration,
external hyper-parameter tuning, or a replacement for Phase39 TEST. Phase32 is **external /
domain-shift evidence only**.

## 2. Discovery result (metadata / filesystem only)

No project-declared external root exists inside `D:/Softfors/jup`
(`data_external/`, `external_test_ds/`, `data/external/`, `data_raw/external/` are all absent).

A **legacy external root was found**: `D:/Softfors/final/external_test_ds` (predecessor
**MedFiLM-Seg** project), containing 19 discovered candidates plus three legacy result
documents (`MedFiLM_Seg_Important_Result_Parameters_V7_FINAL_CLEAN.docx`, `MedSegFilm_Report`,
`MedSeg-FiLM Presentation`). A duplicate external copy exists at
`D:/Softfors/final/medfilm_seg/data_external/CVC_ClinicDB`.

Additional non-project datasets exist upstream at `D:/Softfors/omni_seg/data_raw`
(NLM, msd, kits_2d_splitted, BraTS-PEDs-v1, brats_2d_npy, stone).

## 3. Historical exposure (load-bearing)

The legacy MedFiLM-Seg notebooks reference the external cohorts heavily
(`external_test_ds` ×1523, `CVC-ClinicDB` ×659, `HAM10000` ×306, `BrEaST` ×233, `MILK10k` ×192,
`OrthoFrac` ×173, `DentIRO` ×157, `BDCXR` ×150, `GastroEndoNet` ×61), and the legacy result
documents are present.

**Consequence:** the eight legacy cohorts with direct evaluation references are
`EXTERNAL_OUTCOME_EXPOSED_HISTORICALLY`. **No discovered cohort may be called an untouched external
validation set.**

## 4. Population ownership

No candidate has fully resolved population ownership. Patient/case identity, annotation semantics,
licensing and clustering structure are **not recoverable** from current project provenance for any
candidate. Clinical equivalence is **not** inferred from similar filenames.

## 5. Role classification

| role | count |
|---|---|
| PRIMARY_EXTERNAL_DOMAIN_SHIFT_COHORT | **0** |
| SECONDARY_EXTERNAL_DOMAIN_SHIFT_COHORT | **0** |
| HISTORICALLY_EXPOSED_EXTERNAL_BENCHMARK | 8 |
| SUPPLEMENTARY_STRESS_TEST_ONLY | 0 |
| INELIGIBLE (task mismatch / provenance / overlap) | 11 |

Selection depended only on provenance, task compatibility, externality and integrity — **never** on
known performance.

## 6. Frozen system under test

Canonical **A8/C9** RA-MedFiLM-BARR bundle. No retraining, fine-tuning, external adaptation,
threshold tuning, normalization refit, router/post-safety recalibration, policy change, or
dataset-specific parameter selection.

## 7. Contracts frozen

Preprocessing (frozen deployment semantics; no dataset-specific preprocessing), metric contract
(Dice/IoU/precision/recall/accuracy frozen; boundary metrics and HD95-mm **not promised**), estimand
contract (absolute external performance / internal-to-external shift / cross-domain balanced summary
only if prospectively weighted), claim hierarchy (no primary or secondary claim available),
statistics provenance (no Wilcoxon/Holm/Cohen-d imported from Phase31), GT/inference separation
(Phase30-style Stage A/B), and the external open-state registry (historical states preserved, **not**
falsely reset).

## 8. Conclusion

**No prospective clean external cohort is eligible.** Every discovered candidate is historically
outcome-exposed, task/annotation-incompatible, not genuinely external, or provenance-ambiguous.
Phase32 external execution is therefore **NOT authorized** on the currently available cohorts. This
is a valid scientific result.

The classification classes are preserved distinctly: **NEW PROSPECTIVE EXTERNAL EVIDENCE** (none
available), **HISTORICALLY EXPOSED EXTERNAL EVIDENCE** (8 cohorts), **SUPPLEMENTARY STRESS TEST**
(none), **INELIGIBLE EXTERNAL COHORT** (the remainder).
