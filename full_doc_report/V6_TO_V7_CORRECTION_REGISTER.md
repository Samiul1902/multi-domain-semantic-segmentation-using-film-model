# V6 to V7 Scientific and Visual Correction Register

**Document Version:** 7.0 (Definitive Master Audit)  
**Date:** November 8, 2026  
**Auditor:** Principal Medical Imaging Software Architect & Independent Scientific Integrity Auditor  
**Repository:** `D:\Softfors\jup`  
**Output Target Directory:** `D:\Softfors\jup\full_doc_report`

---

## 1. Executive Summary of V6 Defects & V7 Systemic Solutions

Although Report V6 resolved foundational nomenclature conflicts, critical defects persisted in visual artifacts, computational profiling, document labeling, and cross-figure data contracts. Report V7 eliminates these defects across all figures, tables, text, DOCX, and PDF documents.

---

## 2. Systematic Item-by-Item Correction Ledger

### 2.1 Rebuilding the Page-17 Computational Efficiency Figure (Task 2 & Gate A)
* **V6 Failure:** 
  - Plotted GlobalMedFiLM but omitted the ReMedFiLM point on the accuracy axis.
  - Erroneously stated inside the graphic that "matched FULL accuracy is pending", contradicting the historical VAL808 results reported in Table 1 and Section 3.
  - Figure numbering was contradictory: labeled "Figure 10" inside the graphic canvas while titled "Figure 16" in the report text.
  - Mixed forward-only latencies with full-pipeline latencies without separating measurement classes.
* **V7 Rectification:**
  - Generated `FIG_Accuracy_Compute_ReMedFiLM_V7.svg`, `.pdf`, and 300-DPI `.png` via deterministic script `scripts/analysis/build_v7_figures.py`.
  - **Panel A (Accuracy vs. Analytical Workload):** ReMedFiLM FULL is prominently plotted with a distinctive green star marker (`#27AE60`) with red border at **32.44 Expected Conditional GMACs** ($31.55 + 0.274 \times 3.23$) and **83.79% VAL808 Macro Dice** (+0.28 pp gain over GlobalMedFiLM backbone). GlobalMedFiLM is plotted as a blue square at 31.55 GMACs / 83.51% Dice. Conventional baselines (U-Net, Attention U-Net, U-Net++, MiT-UNet, DeepLabV3+) are plotted in neutral grey with marker sizes proportional to parameter count.
  - **Panel B (Zoomed Proposed vs. Backbone Trade-Off):** Magnified callout explicitly shows the paired transition: $+0.28\text{ pp Dice}$, $+0.89\text{ GMACs}$, and $+1.31\text{M parameters}$.
  - **Panel C (Hardware Latency Accounting):** Separated into distinct, non-conflated measurement classes on NVIDIA GeForce RTX 3060 Ti (FP32, batch=1, 1000 iterations):
    1. GlobalMedFiLM Forward Pass: $15.77\text{ ms}$
    2. ReMedFiLM SKIP Controlled Path: $15.72\text{ ms}$
    3. ReMedFiLM EXECUTE Controlled Path: $18.89\text{ ms}$
    4. Phase 34 Weighted Mean Latency: $16.59\text{ ms}$ ($(635/875) \times 15.72 + (240/875) \times 18.89$)
    5. Phase D Full-Pipeline Fixture Benchmark: $87.99\text{ ms}$ p50 (includes synthetic tensor transfers, dynamic bounding box extraction, and host coordination).
  - **Figure Numbering Unified:** Synchronized across canvas header, report caption, text cross-references, and index as **Figure 16 / FIG 16**.

---

### 2.2 Automated Figure-to-Table Consistency & Data Contract (Task 3 & Gate B)
* **V6 Failure:** Charts were generated using disparate ad-hoc scripts with hardcoded string parameters, leading to subtle naming and numeric divergences.
* **V7 Rectification:** Created `full_doc_report/FIGURE_DATA_CONTRACT.json`, linking every figure to its source tables, exact model identities, mathematical units, seeds, and cryptographic SHA256 checksums. Verified zero missing series, zero mislabeled baselines, and zero ungrounded error bars.

---

### 2.3 Document Versioning & Typography Reconciliation (Task 7 & Gate E)
* **V6 Failure:** The V6 PDF retained old strings reading "Version 5.0" in several header running banners and section titles.
* **V7 Rectification:** 
  - Audited all 20 pages of the PDF and all sections of the DOCX.
  - Replaced all legacy references with **Version 7.0 Definitive Scientific Report**.
  - All figure captions, headers, running footers, and metadata JSON files now reflect V7.0.

---

### 2.4 External Test Evaluation Completeness (Task 5 & Gate C)
* **V6 Verification & V7 Preservation:**
  - Preserved the full historical `EXTERNAL884` evaluation: CVC-ClinicDB ($N=612$), BrEaST-Lesions-USG ($N=252$), and Stones_where_are_you ($N=20$: 6 positive, 14 negative controls).
  - Generated dedicated V7 CSV tables: `tables/ReMedFiLM_Complete_External_Evaluation_V7.csv` and `tables/ReMedFiLM_External_Routing_Safety_V7.csv`.
  - Maintained prominent disclosure of the **14/14 false-positive detection rate** on stone-free radiographs (Dice 0.000).

---

### 2.5 Statistical & Clinical Integrity (Task 7 & Gate D)
* **V7 Validation:**
  - All unsupported $p < 10^{-4}$ assertions purged.
  - Reconciled with frozen percentile bootstrap non-inferiority intervals ($B=2,000$, margin 0.005, lower CI $> -0.005$).
  - Overlap with zero in the DeepLabV3+ comparison clearly stated; superiority framed as an **8.3x parameter reduction** (4.84M vs. 40.35M).
  - Explicitly disclosed that multi-seed evaluations (42, 123, 3407) shared a frozen global backbone.
  - Causal studies C1 (FiLM attribution), C2 (component attribution), and C3 (24-cell matched matrix) remain explicitly marked as prospective milestones.
  - Protected `TEST1683` partition confirmed strictly unread and quarantined.
