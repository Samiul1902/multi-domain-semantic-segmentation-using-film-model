# V5 to V6 Scientific Corrections and Evidence Reconciliation Audit

**Document Version:** 6.0  
**Date:** November 8, 2026  
**Auditor:** Principal Medical Imaging Software Architect & Independent Scientific Auditor  
**Repository:** `D:\Softfors\jup`  
**Output Target:** `D:\Softfors\jup\full_doc_report`

---

## 1. Executive Summary & Core Mission

This audit document tracks all structural, architectural, visual, and statistical corrections implemented during the transition from **Report V5** to **Report V6 (ReMedFiLM Definitive)**.

The primary defect of V5 was an unresolved tension between introductory text (which correctly named FULL RA-MedFiLM-BARR) and the downstream figures/tables (which frequently emphasized GlobalMedFiLM, lacked explicit ReMedFiLM representation, or provided an incomplete external evaluation matrix).

In Report V6:
1. **ReMedFiLM** is established as the canonical proposed system name across all text, tables, and figures.
2. **GlobalMedFiLM** is consistently designated as the internal task-conditioned backbone and primary comparator ($G$).
3. **The External Evaluation Matrix** has been expanded across all historical `EXTERNAL884` cohorts (CVC-ClinicDB, BrEaST-Lesions-USG, Stones_where_are_you), complete with routing counts, safety outcomes, and negative-case disclosures.
4. **All 16 Visual Segmentation Cases** and **External Example Galleries** feature explicit ReMedFiLM overlays and verified Dice metrics.
5. **Statistical Overstatements** (such as unsupported $p < 10^{-4}$ assertions) have been purged and reconciled with frozen percentile bootstrap intervals.

---

## 2. Item-by-Item Correction Ledger (Audit Tasks 1–7)

### 2.1 Model Identity & Canonical Branding (Task 1)
* **V5 Defect:** Mixed nomenclature (`FULL RA-MedFiLM-BARR`, `ReMedFiLM`, `BARR A8/C9`) caused confusion as to whether ReMedFiLM was a newly trained network or the modular assembly.
* **V6 Rectification:** Established frozen naming map:
  - Proposed System: **ReMedFiLM (FULL RA-MedFiLM-BARR)** (4,837,420 parameters; $G + B_\phi + R_\psi + S_\omega$).
  - Internal Backbone: **GlobalMedFiLM ($G$)** (3,523,001 parameters).
  - Wrapper: 0 trainable parameters; staged freeze modular composition.
* **Evidence Source:** `src/models/barr/ra_medfilm_barr.py`, `full_doc_report/ReMedFiLM_Model_Identity_and_Methodology.md`.

---

### 2.2 Rebuilt Methodology Architecture Figures (Task 2)
* **V5 Defect:** Figure 1 was dense, labeled `FULL RA-MedFiLM-BARR`, and lacked explicit ReMedFiLM branding on its enclosing boundary and final output.
* **V6 Rectification:** 
  - Generated `figures/FIG01_ReMedFiLM_Methodology_V6.svg`, `.pdf`, and 300-DPI `.png` ($6667 \times 3834$ px).
  - Enclosing boundary explicitly titled: **ReMedFiLM — FULL PROPOSED SYSTEM (4.84M Parameters)**.
  - Final segmentation box labeled: **ReMedFiLM Final Segmentation**.
  - All three execution paths explicitly labeled:
    1. `Outcome 1: SKIP (Global Prediction)`
    2. `Outcome 2: REFINE + ACCEPT (ReMedFiLM Final)`
    3. `Outcome 3: REFINE + REJECT (Global Fallback)`
  - Generated single-column variant: `figures/FIG01_ReMedFiLM_Methodology_SingleColumn_V6.*`.

---

### 2.3 Comprehensive Visual Figure Reconstruction (Task 3)
* **V5 Defect:** Figures 3, 4, 11, 15, 17, 18, 19 either omitted ReMedFiLM or plotted GlobalMedFiLM as the central result.
* **V6 Rectification:** Rebuilt all thematic figure families with explicit ReMedFiLM series:
  - **F01:** ReMedFiLM Full Methodology Architecture (SVG/PDF/PNG).
  - **F03:** Internal Model Comparison (7 models: U-Net, Att-UNet, UNet++, MiT-UNet, DeepLabV3+, GlobalMedFiLM, and ReMedFiLM). ReMedFiLM highlighted with distinctive green hatch and red border (+0.28 pp dev mean over backbone).
  - **F04:** Four-Domain Performance Profile & Paired Forest Plot showing ReMedFiLM gains across ISIC, BUSI, KVASIR, and KUB.
  - **F06–F09:** Visual Segmentation Galleries for all 4 domains showing matched images, ground truths, GlobalMedFiLM predictions, and ReMedFiLM final segmentations with TP/FP/FN error maps.
  - **F11:** Retrospective External Quantitative Evaluation across 884 cases.
  - **F12:** External Qualitative Composite Gallery (CVC-ClinicDB, BrEaST-USG, Stones).
  - **F15:** Complete 13-Arm Component Ablation showing harm reduction from 42.7% (A1) to 7.87% (A8).
  - **F17:** Multi-Seed Reproducibility Analysis (Seeds 42, 123, 3407) with shared backbone disclosure.
  - **F18:** Robustness & Environmental Stress Degradation under Gaussian noise and blur.
  - **F19:** Accuracy vs. GMACs Pareto Frontier and Latency Accounting (forward-only vs. full pipeline).

---

### 2.4 External Test Evaluation Matrices (Task 4)
* **V5 Defect:** V5 Table 4 only reported high-level Dice scores, omitting detailed precision, recall, HD95, sample counts, and routing-safety accounting.
* **V6 Rectification:** Built three comprehensive external CSV matrices:
  1. `ReMedFiLM_External_Evaluation_Matrix.csv`: Complete metrics (Dice, IoU, Precision, Recall, HD95, 95% CI) for CVC-ClinicDB ($N=612$), BrEaST-Lesions-USG ($N=252$), and Stones_where_are_you ($N=20$, stratified into 6 positive and 14 negative controls).
  2. `ReMedFiLM_External_Routing_Safety_Matrix.csv`: Exact breakdowns of routed proposals, refiner executions, safety acceptances, rejections, improved cases, worsened cases, harm rates, and latency.
  3. `ReMedFiLM_External_Negative_Cases.csv`: Exhaustive disclosure of normal control behavior, confirming the 14/14 false-positive detection rate on stone-free radiographs (Dice 0.000).

---

### 2.5 Correction of Statistical & Clinical Claims (Tasks 5 & 7)
* **V5 Defect:** V5 contained an unsupported claim of "macro $p < 10^{-4}$ superiority". Furthermore, it occasionally implied universal superiority and zero-harm refinement.
* **V6 Rectification:**
  - **P-Value Removal:** Removed all unsupported $p < 10^{-4}$ claims. The frozen benchmark protocol in `reports/audits/phase21_analysis.json` and `reports/audits/phase30_primary_noninferiority_result.json` established a **domain-stratified group percentile bootstrap** (2,000 resamples), demonstrating non-inferior preservation (lower CI $> -0.005$). The comparison against DeepLabV3+ overlaps zero (non-significant difference).
  - **Harm Reduction Nuance:** Clarified that ReMedFiLM *substantially reduces* refinement harm (from 42.7% down to 7.87% in development, and 16.87% in external CVC), but does *not* provide a mathematical zero-harm guarantee.
  - **Latency Transparency:** Disclosed that while GlobalMedFiLM requires 16.4 ms, ReMedFiLM full pipeline requires 26.5 ms on routed cases due to ROI cropping, router scoring, and spatial recomposition (+10.1 ms overhead).
  - **Causal Limitations:** Explicitly maintained that formal causal attribution studies (C1 learned vs. identity FiLM, C2 controlled component attribution, C3 24-cell matched matrix) remain prospective research goals.
  - **Quarantine Confirmation:** Confirmed that protected historical `TEST1683` was strictly quarantined and never accessed.

---

## 3. Summary of Deliverables & Files

All files are preserved in [`D:\Softfors\jup\full_doc_report`](file:///d:/Softfors/jup/full_doc_report):
- `ReMedFiLM_Model_Identity_and_Methodology.md`
- `V5_TO_V6_SCIENTIFIC_CORRECTIONS.md`
- `PAPER_WRITING_GUIDE_V6.md`
- `FINAL_V6_VERIFICATION.md`
- `ReMedFiLM_External_Evaluation_Matrix.csv`
- `ReMedFiLM_External_Routing_Safety_Matrix.csv`
- `ReMedFiLM_External_Negative_Cases.csv`
- `ReMedFiLM_Internal_Model_Comparison.csv`
- `ReMedFiLM_Class_Subclass_Performance.csv`
- `ReMedFiLM_Ablation_Statistics.csv`
- `REPORT_EVIDENCE_INDEX.json`
- `ReMedFiLM_Complete_Scientific_Report_V6.docx`
- `ReMedFiLM_Complete_Scientific_Report_V6.pdf`
