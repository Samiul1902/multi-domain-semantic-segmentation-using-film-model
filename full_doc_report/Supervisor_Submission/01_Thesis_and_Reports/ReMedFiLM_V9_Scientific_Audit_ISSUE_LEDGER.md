# ReMedFiLM V8 Source-First Re-Audit and Issue Ledger

**Target:** `full_doc_report/ReMedFiLM_Complete_Scientific_Report_V8.pdf` and its build system (`full_doc_report/v8_build/`)  
**Auditor:** Independent Scientific Auditor & Principal Research Software Engineer  
**Status:** Audit Completed; Resolutions Mapped for Version 9 (`full_doc_report/V9/`)

---

## 1. Executive Summary

A comprehensive source-code and evidence-ledger audit of the V8 report revealed critical scientific and implementation discrepancies:
1. **Model Executability Status:** V8 describes ReMedFiLM as an end-to-end forward-inference system. In actual repository source code (`src/models/barr/ra_medfilm_barr.py`), `forward_inference` **cannot execute standalone on an arbitrary new image**; it strictly requires pre-computed, cached out-of-fold inputs (`router_features_202`, `oof_refined_crop_prob`, `safety_post_features_16`). It is an offline validation harness, not a deployable online pipeline.
2. **Computational Accounting vs. Routing Frequencies:** The reported `32.4379` conditional GMACs is derived from an analytical formula assuming a 27.43% routing activation rate from historical `ROUTER_HOLDOUT_875`, whereas the headline `VAL808` population exhibits a 34.53% routing frequency (279 / 808 cases).
3. **HAM10000 Status:** V8 omitted the local skin dermoscopy dataset (`D:\Softfors\final\external_test_ds\HAM10000`). Source inspection shows 10,015 images and masks exist locally, but with 0% overlap with the ISIC 2018 benchmark splits and zero established historical ReMedFiLM evaluations.
4. **External 14/14 Stone-Free Cases:** On `Stones_where_are_you`, both GlobalMedFiLM and ReMedFiLM predict false-positive stone masks on all 14 stone-free negative control images (`empty_prediction_rate = 0.0`), resulting in `Dice = 0.0`. The reported `HD95` (166.9 px / 169.9 px) belongs exclusively to the `n=6` stone-positive subset.
5. **Phase 39 Historical TEST1683 Disclosure:** V8 correctly emphasizes that TEST1683 was not reopened during reconstruction, but risks giving the impression that the cohort has never been exposed. In truth, historical one-shot access occurred in Phase 39 and was permanently consumed.

---

## 2. Structured Issue Ledger

| Issue ID | Severity | V8 Page / Section | Claim in V8 | Actual Code / Source Evidence | Discrepancy / Uncertainty | Required V9 Resolution |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **ISS-01** | **CRITICAL** | Pages 4–7 (Methodology & Inference) | ReMedFiLM executes end-to-end online segmentation on arbitrary images | `src/models/barr/ra_medfilm_barr.py` lines 223–315 | `forward_inference` raises `ValueError` if `router_features_202`, `oof_refined_crop_prob`, or `safety_post_features_16` are `None` | Classify implementation accurately as **Mode B (Historical Offline Candidate Replay)**; document online candidate generator as an engineering gap |
| **ISS-02** | **HIGH** | Page 16, Table 4 (Efficiency) | ReMedFiLM FULL conditional compute is 32.4379 GMACs on VAL808 | `reports/tables/c2_barr/c2_barr_aggregate.json` | 32.4379 GMACs is calculated using $p = 240/875 = 27.43\%$ from `ROUTER_HOLDOUT_875`, not VAL808 ($p = 279/808 = 34.53\%$, which would yield 32.667 GMACs) | Explicitly decouple the analytical routing cost benchmark from VAL808 empirical frequencies; disclose both numbers with clear population tags |
| **ISS-03** | **HIGH** | Section 7 & Table 3 (External Eval) | Stones_where_are_you external evaluation reported as $n=20$ | `reports/tables/c1_external_stress_stones_subgroups.csv` | Recall and HD95 are mathematically undefined on 14 stone-free scans; metric is computed strictly on $n=6$ stone-positive cases | Separate $n=6$ stone-positive boundary metrics from $n=14$ negative control false-positive suppression statistics ($0/14$ empty mask rate) |
| **ISS-04** | **HIGH** | Not in V8 (Omitted Dataset) | External skin dataset HAM10000 omitted | `D:\Softfors\final\external_test_ds\HAM10000` (10,015 images & masks) | Audit confirms zero overlap with ISIC 2018 train/val/test splits, but no verified ReMedFiLM segmentation evaluation was ever executed | Add comprehensive HAM10000 audit; classify as `EXTERNAL_SKIN_DATASET_AVAILABLE__SEGMENTATION_EVALUATION_NOT_ESTABLISHED` |
| **ISS-05** | **MEDIUM** | Page 18 (Governance & TEST1683) | TEST1683 was not accessed during reporting | `reports/audits/phase39_v1_2_scientific_delta_proof.json` | Historical one-shot test protocol was consumed in Phase 39; reporting that it was not opened now might mislead reviewers into thinking it is untouched prospective data | Fully disclose that Phase 39 consumed the one-shot protocol historically; no reopening occurred in V8/V9; recommend a new independent prospective cohort |
| **ISS-06** | **MEDIUM** | Page 14, Table 2 (13-Arm Ablation) | Arm definitions vary across report sections | `reports/tables/phase28_table_01_arm_definitions.csv` | A2–A5 are heuristic routing signal controls, A6 is learned paired-gain, A7 is cost-aware utility, A8 is safety-gated, R1–R3 are router variants, F1 is refiner RGB-only stem | Standardize exact 13-arm naming and configuration contracts directly matching Phase 28 Table 01 |
| **ISS-07** | **MEDIUM** | Page 6, Figure 2 & Figure 5 | Redundant architecture diagrams; tiny illegible portrait layout | `full_doc_report/figures/ReMedFiLM_Methodology_V8.png` | Figure 2 has illegible text at manuscript width; Figure 5 repeats the same architecture | Consolidate into one definitive landscape methodology diagram with clear offline/online dataflow markings; export high-res vector formats |

---

## 3. V9 Action Plan
All issues above will be systematically resolved in the V9 deliverables, establishing strict scientific defensibility without retraining models or modifying frozen evidence.
