# Appendix: Quantified Historical C2 and C3 Evidence

**Governance Standard:** Historical Retrospective Inventory  
**Status:** `HISTORICAL_DESCRIPTIVE_RESULT` & `PROTOCOL_INCOMPARABLE`  
**Test Isolation Notice:** All metrics reported below were obtained exclusively on historical development partitions or pre-remediation splits (v1/v2). They demonstrate engineering feasibility and exploratory behaviors but are **not comparable to clean Manifest v3 prospective benchmarks**. Zero test-set evaluation has been executed.

---

## 1. Campaign 2 — BARR Regional Refinement, Routing & Safety (Module 1 / Phase 28 / Phase 30)

Budget-Aware Regional Refinement (BARR) combines an unrefined global segmentation pass ($A0$) with a localized high-capacity regional refiner ($R_\psi$) and a learned post-safety filter ($S_\omega$).

### 1.1 Ablation Family and Arm Invariants ($N_{\text{pop}} = 4,957$ Dev Cases)
Measured from frozen authority [`reports/tables/phase28_table_02_arm_primary_metrics.csv`](file:///d:/Softfors/jup/reports/tables/phase28_table_02_arm_primary_metrics.csv) and [`reports/audits/barr_m1_v1_0c_precision_audit.json`](file:///d:/Softfors/jup/reports/audits/barr_m1_v1_0c_precision_audit.json):

| Arm ID | Architectural Specification | Cases Routed ($n_{\text{routed}}$) | Budget Fraction ($B_{\text{frac}}$) | Pooled Mean True $\Delta\text{DSC}_{\text{routed}}$ | Cases Benefited ($\Delta > 0$) | Cases Harmed ($\Delta < 0$) | All-Population Harm Rate ($/4,957$) | Evidence Class |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **A0** | Global pass only (no refinement) | 0 | 0.00% | 0.000000 | 0 | 0 | 0.00% | `ENDPOINT_BY_CONSTRUCTION` |
| **A1** | Unconditional refinement (all crops) | 4,957 | 100.00% | +0.001658 | 2,775 | 2,115 (strict) / 2,107 (tol) | 42.67% (strict) / 42.51% (tol) | `ENDPOINT_BY_CONSTRUCTION` |
| **A6** | Utility-guided selection (no cost) | 1,239 | 24.99% | +0.007247 | 827 | 412 | 8.31% | `PRIOR_CANONICAL_EVIDENCE` |
| **A7** | Cost-aware utility: $U = \hat{\Delta} - \lambda C$ | 1,239 | 24.99% | +0.007247 | 827 | 412 | 8.31% | `PRIOR_CANONICAL_EVIDENCE` |
| **A8** | Full BARR: $A7$ + Post-Safety $S_\omega$ | 1,205 accepted (1,239 executed) | 24.31% accepted (24.99% executed) | +0.007516 | 815 | 390 | 7.87% | `PRIOR_CANONICAL_EVIDENCE` |

### 1.2 Key Behavioral Findings & Denominator Precision
1. **Execution vs. Acceptance ($A8$)**:
   - $n_{\text{selected}} = n_{\text{executed}} = 1,239$ cases routed to refiner.
   - $n_{\text{accepted}} = 1,205$ cases (97.26% of executed) where $S_\omega$ allowed refined mask substitution.
   - $n_{\text{rejected}} = 34$ cases (2.74% of executed) where $S_\omega$ reverted refinement to global mask ($\Delta \text{DSC} \equiv 0.0$).
2. **Harm Mitigation**:
   - Unconditional refinement ($A1$) harms **42.67%** of cases across the population (2,115 / 4,957).
   - Full BARR with safety filter ($A8$) limits population harm to **7.87%** (390 / 4,957), eliminating 1,725 harmed cases while reducing compute by $>75\%$.
3. **Phase 30 Non-Inferiority Verification on Router Holdout ($N=875$)**:
   - Estimand: Equal-domain macro Dice delta between BARR ($A8$) and Global baseline ($A0$).
   - Point Estimate: $\Delta_{\text{macro}} = +0.001739$
   - 95% Domain-Stratified Group Bootstrap CI ($B=2,000$): $[+0.001117, +0.002405]$
   - **Non-inferiority bound**: Lower bound $+0.001117 > -0.005$ margin; non-inferiority rigorously established.
   - **Per-Domain Deltas**:
     - KUB: $+0.005945$ (95% CI: $[+0.003635, +0.008456]$) — largest regional benefit.
     - ISIC: $+0.000986$ (95% CI: $[+0.000329, +0.001764]$)
     - BUSI: $+0.000005$ (95% CI: $[0.000000, +0.000015]$)
     - KVASIR: $+0.000020$ (95% CI: $[0.000000, +0.000060]$)

---

## 2. Campaign 3 — Fair Multi-Domain Segmentation Benchmarking (Phase 20 / Phase 20b / Phase 21)

All historical shared multi-domain models trained under Phase 20/20b/21 are summarized below.

### 2.1 Five-Model Comparative Baseline (Phase 20b Development Validation)
Measured from authoritative summary [`reports/tables/phase20b_five_model_comparison_final.csv`](file:///d:/Softfors/jup/reports/tables/phase20b_five_model_comparison_final.csv):

| Model Name | Backbone Class | Trainable Params | Best Epoch | Macro Domain Dice | 95% Bootstrap CI | Macro Domain IoU | ISIC Dice | BUSI Dice | KVASIR Dice | KUB Dice |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **DeepLabV3+** | `DeepLabV3Plus` | 40,347,041 | 57 | 0.8277 | [0.7707, 0.8761] | 0.7412 | 0.8853 | 0.8669 | 0.8197 | 0.7387 |
| **Transformer MiT U-Net** | `TransformerMiTUNet` | 16,347,777 | 74 | 0.8224 | [0.7599, 0.8755] | 0.7366 | 0.8871 | 0.8640 | 0.8133 | 0.7252 |
| **U-Net++** | `UNetPlusPlus` | 9,159,681 | 55 | 0.7920 | [0.7446, 0.8382] | 0.6910 | 0.8601 | 0.8163 | 0.7710 | 0.7207 |
| **Attention U-Net** | `AttentionUNet` | 7,851,285 | 64 | 0.7890 | [0.7288, 0.8447] | 0.6927 | 0.8617 | 0.8277 | 0.7710 | 0.6958 |
| **Standard U-Net** | `UNet` | 7,763,041 | 74 | 0.7878 | [0.7381, 0.8375] | 0.6881 | 0.8553 | 0.8198 | 0.7552 | 0.7211 |

### 2.2 Global MedFiLM Exploratory Benchmark (Phase 21)
Measured from authoritative summary [`reports/tables/phase21_six_model_comparison.csv`](file:///d:/Softfors/jup/reports/tables/phase21_six_model_comparison.csv):
- **Parameters**: 3,523,001 (Trainable: 3,523,001; Backbone: 3,432,233; Conditioning: 90,768).
- **Macro Domain Dice**: $0.8351$ (95% CI: $[0.7877, 0.8780]$).
- **Macro Domain IoU**: $0.7448$.
- **Per-Domain Dice**:
  - ISIC: $0.8972$
  - BUSI: $0.8588$
  - KVASIR: $0.8202$
  - KUB: $0.7641$
- **Comparison to DeepLabV3+**: Achieved $+0.0074$ higher macro Dice with **11.4x fewer parameters** (3.52M vs 40.35M).

### 2.3 Protocol Incomparability & Governance Boundaries
These historical C3 results **cannot be claimed as a clean prospective benchmark** because:
1. They were trained on Phase 2 v2 manifests prior to the Phase 05 leakage audit.
2. 118 quarantined patient-linked and perceptual duplicate cases were active in training.
3. Checkpoint selection was performed on the same validation population without prospective test holdout verification.
4. Definitive benchmarking requires execution under the clean Manifest v3 prospective protocol ($C1\text{-}T$ vs $C1\text{-}C$).
