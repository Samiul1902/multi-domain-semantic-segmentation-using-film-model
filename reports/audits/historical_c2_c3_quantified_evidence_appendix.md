# Appendix: Quantified Historical C2 and C3 Evidence

**Governance Standard:** Historical Retrospective Inventory  
**Status:** `HISTORICAL_DESCRIPTIVE_RESULT` & `PROTOCOL_INCOMPARABLE`  
**Test Isolation Notice:** All metrics reported below were obtained exclusively on historical development partitions or pre-remediation splits (v1/v2). They demonstrate engineering feasibility and exploratory behaviors but are **not comparable to clean Manifest v3 prospective benchmarks**. Zero test-set evaluation has been executed.

---

## 1. Campaign 2 — BARR Regional Refinement, Routing & Safety (Module 1 / Phase 28 / Phase 30)

Budget-Aware Regional Refinement (BARR) combines an unrefined global segmentation pass ($A0$) with a localized high-capacity regional refiner ($R_\psi$) and a learned post-safety filter ($S_\omega$).

### 1.1 Ablation Family and Arm Invariants ($N_{\text{pop}} = 4,957$ Dev Cases)
Measured from frozen authority [`reports/tables/phase28_table_02_arm_primary_metrics.csv`](file:///d:/Softfors/jup/reports/tables/phase28_table_02_arm_primary_metrics.csv) and [`reports/audits/barr_m1_v1_0b_harm_denominator_audit.json`](file:///d:/Softfors/jup/reports/audits/barr_m1_v1_0b_harm_denominator_audit.json):

| Arm ID | Architectural Specification | Cases Routed ($n_{\text{routed}}$) | Cases Accepted ($n_{\text{accepted}}$) | Pooled Mean True $\Delta\text{DSC}_{\text{routed}}$ | Cases Benefited ($\Delta > 0$) | Cases Harmed ($\Delta < 0$) | Conditional Harm Rate | All-Population Harm Rate ($/4,957$) | Evidence Class |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **A0** | Global pass only (no refinement) | 0 | 0 | 0.000000 | 0 | 0 | 0.00% | 0.00% | `ENDPOINT_BY_CONSTRUCTION` |
| **A1** | Unconditional refinement (all crops) | 4,957 | 4,890 | +0.001658 | 2,775 | 2,115 (strict) / 2,107 (tol) | 42.67% (2,115 / 4,957) | 42.67% (strict) / 42.51% (tol) | `ENDPOINT_BY_CONSTRUCTION` |
| **A6** | Utility-guided selection (no cost) | 1,239 | 1,239 | +0.007247 | 827 | 412 | 33.25% (412 / 1,239) | 8.31% (412 / 4,957) | `PRIOR_CANONICAL_EVIDENCE` |
| **A7** | Cost-aware utility: $U = \hat{\Delta} - \lambda C$ | 1,239 | 1,239 | +0.007247 | 827 | 412 | 33.25% (412 / 1,239) | 8.31% (412 / 4,957) | `PRIOR_CANONICAL_EVIDENCE` |
| **A8** | Full BARR: $A7$ + Post-Safety $S_\omega$ | 1,239 | 1,205 | +0.007516 | 815 | 390 | 32.37% (390 / 1,205) | 7.87% (390 / 4,957) | `PRIOR_CANONICAL_EVIDENCE` |

### 1.2 Mathematical Harm Reconciliations & Denominator Precision
1. **Meaning of the 390 Harmed Cases ($A8$)**:
   - In Arm $A8$, exactly **390 cases** experienced a negative Dice change ($\Delta \text{DSC} < 0$).
   - All 390 harmed cases lie strictly within the **1,205 accepted cases** ($n_{\text{accepted}}$).
   - Unselected cases ($3,718$) and rejected cases ($34$) revert to the global mask ($A0$), yielding $\Delta \text{DSC} \equiv 0.0$.
2. **Conditional vs. All-Population Harm Rates**:
   - **Conditional on Acceptance**: $390 / 1,205 = \mathbf{32.37\%}$.
   - **All-Population (Intent-to-Treat)**: $390 / 4,957 = \mathbf{7.87\%}$.
   - Comparing $A1$'s all-population harm rate ($42.67\%$) directly to $32.37\%$ was an earlier denominator error. Like-for-like all-population comparison shows harm dropped from **42.67%** ($A1$) to **7.87%** ($A8$), eliminating 1,725 harmed cases while reducing compute by $>75\%$.
3. **Historical Router Holdout ($N=875$) Provenance & Non-Inferiority Status**:
   - Evaluated during Phase 30 under specification revision `v1.3`.
   - Adjudicated evidence class: `ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_SCIENTIFIC_SOURCE_FREEZE_DEVIATION` ([`phase30_supervisor_evidence_class_adjudication.json`](file:///d:/Softfors/jup/reports/audits/phase30_supervisor_evidence_class_adjudication.json)).
   - Prior to opening, holdout isolation was verified ([`phase30_router_holdout_first_open_precondition.json`](file:///d:/Softfors/jup/reports/audits/phase30_router_holdout_first_open_precondition.json)).
   - During execution, a post-scoring `TypeError` occurred, requiring a documented source re-bind. The supervisor ruled that numerical outputs remain frozen, but perfect pre-registration cannot be claimed.
   - **Primary Non-Inferiority Estimand**: Equal-domain macro Dice delta between $A8$ and $A0$:
     - Point estimate: $\Delta_{\text{macro}} = +0.001739$
     - 95% Domain-Stratified Group Bootstrap CI ($B=2,000$): $[+0.001117, +0.002405]$
     - **Verdict**: Lower bound $+0.001117 > -0.005$ non-inferiority margin. Confirms historical non-inferiority under this specific protocol, but does **not** constitute independent confirmatory proof or clinical safety.

---

## 2. Campaign 3 — Multi-Domain Segmentation Benchmarking (Phase 20 / Phase 20b / Phase 21)

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

### 2.3 Protocol Incomparability & Scientific Boundaries
These historical C3 results **cannot be claimed as a clean prospective benchmark** because:
1. They were trained on Phase 2 v2 manifests prior to the Phase 05 leakage audit.
2. 118 quarantined patient-linked and perceptual duplicate cases were active in training.
3. Checkpoint selection was performed on the same validation population without prospective test holdout verification.
4. Definitive benchmarking requires execution under the clean Manifest v3 prospective protocol ($C1\text{-}T$ vs $C1\text{-}C$).
