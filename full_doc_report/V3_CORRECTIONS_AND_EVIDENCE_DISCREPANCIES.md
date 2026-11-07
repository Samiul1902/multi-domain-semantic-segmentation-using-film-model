# V3 Corrections and Evidence Discrepancies Audit
## RA-MedFiLM-BARR: Pre-V4 Scientific Quality & Provenance Audit

This document records the exact discrepancies, overstatements, unsupported statistical markers, and methodological corrections identified during the audit of `full_doc_report/RA_MedFiLM_BARR_Visual_Research_Report_V3.pdf` and its companion artifacts, establishing the scientific foundation for the Master Report V4.

---

### 1. Statistical Claims & Hypothesis Testing
* **Discrepancy in V3**: Reported blanket macro p-values such as "$p < 10^{-4}$" and "$p < 0.001$" across all competing architectures and domain comparisons.
* **Correction in V4**: 
  - Historical paired bootstrap comparisons between **GlobalMedFiLM** and **DeepLabV3+** reveal confidence intervals spanning zero on specific domains (e.g., KVASIR and pooled macro). Broad superiority cannot be asserted as universally statistically significant without qualifying individual domain differences.
  - Paired Wilcoxon signed-rank and bootstrap confidence intervals are reported strictly alongside exact effect sizes and 95% CIs from original Phase 21 records (`reports/tables/phase21_six_model_comparison.csv`). Unsupported p-values have been removed.

---

### 2. Safety & Clinical Non-Negative Claims
* **Discrepancy in V3**: Asserted that BARR "guarantees strictly non-negative refinement," "eliminates catastrophic degradation across all samples," and is "certified complete and clinically safe."
* **Correction in V4**:
  - Removed all unverified expressions ("guarantees non-negative refinement", "clinically safe", "eliminates catastrophic failures", "ready for clinical deployment").
  - The empirical evidence demonstrates that **harmful refinements occur**: in ROUTER_DEVELOPMENT4957, Arm A8 resulted in 390 worsened cases (32.4% of routed); in the EXTERNAL884 retrospective stress evaluation, 34 cases were worsened after adoption.
  - On the external negative control cohort (`Stones_where_are_you`), a severe **14/14 false-positive failure pattern** occurred where stone-free images were predicted as containing stones (mean Dice 0.000). These material failure patterns are now prominently analyzed and documented.

---

### 3. Historical TEST Partition Access
* **Discrepancy in V3**: Stated that "the protected prospective testing partition (TEST1683) was strictly air-gapped and never accessed."
* **Correction in V4**:
  - V3 conflated the generation of the report with historical repository milestones. In Phase 39 (v1.2), TEST1683 was in fact accessed and evaluated, establishing a historical one-shot macro Dice of **0.8314** (ISIC n=735: 0.8869, BUSI n=174: 0.8504, KVASIR n=216: 0.8507, KUB n=558: 0.7377) across 1,683 test images, following two earlier disclosed process exit aborts.
  - V4 explicitly distinguishes historical Phase 39 TEST access from the present V4 reporting task (which strictly does not access, open, or re-evaluate TEST1683).

---

### 4. Computational Measurements & Complexity Metrics
* **Discrepancy in V3**: Conflated parameter counts, analytical GMACs, and inference timings under imprecise units (e.g. citing 28.4 GMACs for BARR without separating G-only baseline from conditional execution).
* **Correction in V4**:
  - Reconciled against `reports/tables/phase34_analytical_compute_summary_v1_3.csv` and `reports/tables/phase34_batch1_latency_results_v1_4.csv`:
    * Architecture parameters: GlobalMedFiLM backbone = 3,523,001; Refiner $R_\psi$ = 1,276,401; Router $B_\phi$ = 36,801; Safety $S_\omega$ = 1,217; Total Bundle = 4,837,420 parameters.
    * Analytical MACs: Global-only = $3.155 \times 10^{10}$ (31.55 GMACs); Final A8_C9 expected conditional execution = $3.244 \times 10^{10}$ (32.44 GMACs).
    * Hardware Latency (batch 1, RTX 3060 Ti): Global forward = 15.77 ms; Skip controlled path = 15.72 ms; Full execute path = 18.89 ms.

---

### 5. Medical Image Annotations & Subgroup Pathology
* **Discrepancy in V3**: Imputed clinical histological subtypes (e.g. naming specific nevus/melanoma histology, invasive carcinoma subtypes, and stone mineral composition) purely from visual inspections of RGB/radiograph panels.
* **Correction in V4**:
  - Removed all speculative clinical interpretations. Pathology labels are restricted to validated metadata:
    * BUSI-WHU: Matched to `Patient_infos_BUSI-WHU.xlsx` (Benign: 60, Malignant: 24).
    * KUB-StoneX: Restricted to verified anatomical stone sites (Bladder, Kidney, Ureteric) and annotated for full-field vs ROI patch status.
    * Kvasir-SEG: Restricted to image-mask area quantiles (Large vs Small/Sessile polyp), explicitly labeled as morphological area strata rather than histopathology.
    * ISIC 2018: Task-level lesion segmentation; sub-pathology labeled as `UNVERIFIED_SUBGROUP` where clinical ground truth metadata is not recorded.

---

### 6. Mask Integrity & Audit Provenance
* **Discrepancy in V3**: Cited SHA256 audit verification without including complete cross-referencing tables for all composite figures.
* **Correction in V4**:
  - Validated that `reports/audits/phase27_val808_predictions_sha256.json` exists and covers the 1,616 saved binary PNG masks (`*_global.png` and `*_final.png`) in `reports/figures/phase27_preservation/masks/`.
  - Machine-readable indices (`SEGMENTATION_VISUAL_EVIDENCE_INDEX.csv`, `EXTERNAL_EVALUATION_EVIDENCE.csv`, and `PROGRESSION_AND_PROPAGATION_EVIDENCE.csv`) now accompany the V4 release.

---

### 7. Layout, Page Count & Completeness
* **Discrepancy in V3**: Rendered as a condensed 10-page document lacking dedicated sections for external stress testing, incremental domain progression, stage-wise error propagation, router interpretability, perturbation robustness, and failure taxonomy.
* **Correction in V4**:
  - V4 is expanded into a comprehensive, publication-ready **20-page Master Scientific Report** adhering strictly to IEEE TMI / Medical Image Analysis standards, incorporating 14 multi-panel figures and 8 standardized tables.
