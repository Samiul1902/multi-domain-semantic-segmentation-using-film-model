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

---

## 4. Resolution status of the V9 report document

The V9 DOCX that eventually shipped was **not** produced by `v9_build/v9_report.py`. That generator is a copy of the V8 builder: it imports `v9_common` (a V8 clone), reads `REMEDFILM_V9_FIGURE_EVIDENCE_MAP.json` and `REMEDFILM_V9_METHODOLOGY_ARROWS.json` which do not exist, and **44 of its 46 registry lookups** are absent from the verified 267-record V9 registry. Running it cannot reproduce a V9 document.

The V9 DOCX in `full_doc_report/V9/` was instead a relabelled V8 build — identical structure (194 paragraphs, 24 tables, 33 images) with V8→V9 string substitution — so it carried V8 residues and omitted the V9 corrections. It was therefore **repaired and completed** by `v9_build/v9_finalize_report.py`, which reads the verified registry and edits the existing artifact rather than regenerating it:

| Correction | Issue addressed | Status |
| :--- | :--- | :--- |
| R01 running header V8→V9 (run-level, tab preserved) | V8 residue | Applied |
| R02 `Status in V8` column → V9; TEST1683 row reconciled with `test1683_disclosure` | ISS-05 | Applied |
| R03 registry size 291 → **267** metric records | factual error | Applied |
| R04 appendix deliverables rebuilt from files that exist; **V8 filenames removed** | V8 residue | Applied |
| R05 §3.4 HAM10000 disposition + source-table row | ISS-04 | Applied |
| R06 §2.7 Mode-B implementation class | ISS-01 | Applied |
| R07 dual-population compute (32.4379 holdout / **32.6673 VAL808**) + new table row | ISS-02 | Applied |
| R08 operator-supplied conceptual diagram inserted as Figure 6 with 7-item divergence register | ISS-07 | Applied |
| R09 References section (17 repository-recorded entries) | missing section | Applied |
| R10/R11 remaining V8 self-references and the stale V8 regeneration recipe | V8 residue | Applied |
| R12 Word TOC field replaced with a static contents list carrying real page numbers | TOC never resolved | Applied |
| R13 footer tab restored (`…not opened Page N of M`) | pre-existing layout defect | Applied |
| R14 literal `**bold**` / `` `mono` `` markers rendered instead of leaking | pre-existing layout defect | Applied |

**Not resolved, and deliberately so:** ISS-03 (Stones `n = 6/20` denominators) was already correct in the document and is preserved; ISS-06 (13-arm naming) is carried as-is because the arm definitions are frozen in Phase 28 and were not re-derived here.

Verification: `v9_build/verify_v9_report.py` reports **48/48 checks passed**, including sequential figure (1–34) and table (1–14) numbering, zero residual `V8` tokens, registry-value agreement, and all 29 PDF pages rendered and inspected.
