# Phase 14 — Regional Refiner Diagnostic: Final Closure Audit

**Phase:** 14  
**Title:** Regional Refiner Diagnostic  
**Status:** **COMPLETE**  
**Final Classification:** `DIAGNOSTIC_PRACTICAL_SIGNAL_INSUFFICIENT`  
**Phase 15 Status:** `NOT_AUTHORIZED`  
**Current Next Action:** `WAIT_FOR_SUPERVISOR_ROADMAP_DECISION`  

---

## 1. Executive Summary & Scientific Findings

Phase 14 investigated the coarse-to-fine regional refinement hypothesis for kidney stone segmentation on KUB radiographs:
1. **Refiner Potential (Step 1): PASS**  
   Under ideal Oracle bounding box proposals, the regional refiner demonstrates clear capability to recover stones missed by the global baseline:
   - **Tiny Object Detection Recall:** Increases from $57/73$ ($78.1\%$) to $73/73$ ($100.0\%$).
   - **FULL_FIELD Macro Dice:** Increases from $0.6528$ to $0.8152$ ($+16.2\%$ absolute gain).
   - **Gate Gain $G$:** $+0.219178$ ($\ge +0.05$).
2. **Proposal Retention (Step 2): PASS**  
   When driven by frozen Stage-4D localizer proposals ($heatmap\_resolution=128$, AvgPool4 active, 494 proposals, 4.66/image), the pipeline retains exactly $50.0\%$ of the oracle recovery benefit:
   - **Retention Ratio $R$:** $(T_p - T_g) / G = \frac{8/73}{16/73} = \frac{8}{16} = 0.500000$ ($\ge 0.50$).
   - **Hard-Tiny Stones Recovered:** $8$ out of $16$ ($50.0\%$).
3. **Practical Net Benefit (Step 3): FAIL**  
   While Predicted Regional recovers half the missed tiny stones, false positive proposal clutter outside genuine stone targets (mean $5.43$ FP components/image vs $0.37$ baseline) leads to a severe full-field Dice penalty:
   - **Predicted FULL_FIELD Dice $D_p$:** $0.383905$ (fails the required tolerance threshold $\ge 0.632776$).
   - Consequently, Step 3 **FAILS**.

**Diagnostic Classification:** `DIAGNOSTIC_PRACTICAL_SIGNAL_INSUFFICIENT`  
**Phase 15 Authorization:** `NOT_AUTHORIZED` (Confirmatory deployment branch closed).

---

## 2. Frozen Population & Proposal Burden

- **Dataset:** KUB FULL_FIELD VAL split (106 images, 156 stone components)
- **Component Strata:**
  - **TINY:** 73 components
  - **SMALL:** 29 components
  - **MEDIUM:** 36 components
  - **LARGE:** 18 components
- **Proposal Statistics:**
  - **Total Proposals:** Exactly 494 across 106 images
  - **Mean Proposals per Image:** 4.660377
  - **Localizer Resolution:** Heatmap 128 (4x average-pooling active)
  - **Mean ROI Area Fraction:** 0.005899

---

## 3. Authoritative Metric Definition & Provenance

- **Metric:** **FROZEN HISTORICAL OBJECT RECALL**
- **Implementation:** `src/metrics/object_metrics.py`
- **Function:** `object_metrics(prediction, target, minimum_overlap_pixels=1)`
- **Evaluator SHA-256:** `9824397f0c2b5d8807fadd2ba79ec565902ae47b8a36f719a4ae5a4e99a81238`
- **Definition:** A ground-truth stone component is scored as detected if any predicted foreground pixel overlaps it by $\ge 1\text{ pixel}$ (`overlap_pixels >= 1`).
- **Reproduction of Historical Reference:**
  $$\text{Global Baseline Tiny Recall} = \frac{57}{73} = 0.7808219... \equiv T_g = 0.780822 \quad (\mathbf{EXACT\ MATCH})$$
- **Legacy Terminology Caveat:** Historical artifacts and table column headers (e.g. `*_recall90_*`) used legacy project labels. The secondary strict coverage metric `cov90` ($\ge 90\%$ mask coverage: Global Tiny 25/73, Oracle Tiny 47/73, Predicted Tiny 42/73) is preserved for descriptive purposes only and does **not** feed decision gates.

---

## 4. Reconciled Strata Results

| Stratum | Total | Global Baseline ($T_g$) | Oracle Regional ($T_o$) | Predicted Regional ($T_p$) |
|---|:---:|:---:|:---:|:---:|
| **TINY** | **73** | **57 / 73 (0.780822)** | **73 / 73 (1.000000)** | **65 / 73 (0.890411)** |
| **SMALL** | **29** | 25 / 29 (0.862069) | 29 / 29 (1.000000) | 28 / 29 (0.965517) |
| **MEDIUM** | **36** | 32 / 36 (0.888889) | 36 / 36 (1.000000) | 35 / 36 (0.972222) |
| **LARGE** | **18** | 17 / 18 (0.944444) | 18 / 18 (1.000000) | 17 / 18 (0.944444) |
| **OVERALL** | **156** | **131 / 156 (0.839744)** | **156 / 156 (1.000000)** | **145 / 156 (0.929487)** |

---

## 5. Hard-Case Reconciliation

Reconstruction table: `reports/tables/phase14_part3d_frozen_hardcase_reconstruction.csv`

1. **16 Hard-Tiny Components:**
   - Global UNet++ Baseline: 0 / 16 (0.0%)
   - Oracle Regional: **16 / 16 (100.0%) recovered**
   - Predicted Regional: **8 / 16 (50.0%) recovered**
2. **7 Global-Empty Images (Target Stone Recovery):**
   - Evaluated strictly on underlying ground-truth stone target recovery ($\text{detected components} > 0$).
   - Global UNet++ Baseline: 0 / 7 (0.0%)
   - Oracle Regional: **7 / 7 (100.0%) recovered**
   - Predicted Regional: **5 / 7 (71.4%) recovered**

---

## 6. Gate Hierarchy Arithmetic

- $T_g = 0.780822$, $D_g = 0.652776$
- $T_o = 1.000000$, $D_o = 0.815175$
- $T_p = 0.890411$, $D_p = 0.383905$
- $G = T_o - T_g = 16 / 73 = +0.219178$
- $R = (T_p - T_g) / G = 8 / 16 = 0.500000$

- **Step 1:** $G \ge 0.05$ AND $D_o \ge 0.632776 \rightarrow$ **PASS**
- **Step 2:** $R \ge 0.50 \rightarrow$ **PASS**
- **Step 3:** $T_p \ge 0.780822$ (PASS), Hard-Tiny $\ge 2/16$ (PASS), Global-Empty $\ge 1/7$ (PASS), $D_p \ge 0.632776$ (FAIL) $\rightarrow$ **FAIL**

---

## 7. Checkpoint Provenance

| Role | Checkpoint Path | SHA-256 |
|---|---|---|
| Global UNet++ | `checkpoints/phase10_kub_unetpp_seed42_512/best.pt` | `4bffcf926227fb11029ead6bcd8e7dd8ed246e0f1678e3efb2ce4297439a3f2d` |
| Stage-4D Localizer | `checkpoints/phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_v1/best.pt` | `ece906df6c73f2e93c3f873661490bf3cb1a6b82be2d2d93b58c25bc967cbace` |
| Regional Refiner | `checkpoints/phase14_diag_regional_unet_oracletrain_a3_seed42_v1/best.pt` | `89ada72700385ed56b49b6caf34d9061349c24a566794176911b83fb0c8cd9f0` |

*Regional Training Details:* Best epoch 14 (val crop Dice 0.8437), stopped at epoch 29 via early stopping patience 15. Power-resume audit certified `VALID_SAME_EXPERIMENT`.

---

## 8. Canonical Artifact Cryptographic Registry

| Artifact | File Path | SHA-256 | Status |
|---|---|---|:---:|
| Executed Notebook | `notebooks/13_phase14_regional_refiner_diagnostic.ipynb` | `b5b329d1d100138db640e4a3e91069a4008a434d998945646bc7a4522c040948` | **FROZEN** |
| Diagnostic Audit JSON | `reports/audits/phase14_part3_diagnostic_evaluation.json` | `48ec4beafd7a090b084b53bc662f5cb59cc349bf5f2bde1c39caacdc39910b4b` | **FROZEN** |
| Diagnostic Audit MD | `reports/audits/phase14_part3_diagnostic_evaluation.md` | `8aaef263deda3c36fd083b95dd5b28c800d4380f41d7dcb3b93312354cf6e5f8` | **FROZEN** |
| Mode Summary Table | `reports/tables/phase14_part3_mode_summary.csv` | `aabf89da1e8e464ce8d509e1e5fb69e7ded124fb4565dec3103f53bcc8a6cef8` | **FROZEN** |
| Component Metrics Table | `reports/tables/phase14_part3_component_metrics.csv` | `20f75b163d699dcfcfb3118108b1e370c7d1ea75552e2fdc3196115ee0bd63f5` | **FROZEN** |
| Hard-Case Summary Table | `reports/tables/phase14_part3_hardcase_summary.csv` | `9853d141654f7b19a967145cef5a5542bedd2438f9d4158881967f62266827e3` | **FROZEN** |
| Hard-Case Reconstruction | `reports/tables/phase14_part3d_frozen_hardcase_reconstruction.csv` | `b3e6ec55def6bf5599760710d22f340a95eab42e82091908dfea1e7cf8beb368` | **FROZEN** |
| Image Metrics Table | `reports/tables/phase14_part3_image_metrics.csv` | `874f4447935b5d77be5f099ae9cbc122150924cc5de53301319f38f394870b6e` | **FROZEN** |
| Evaluator Code | `src/metrics/object_metrics.py` | `9824397f0c2b5d8807fadd2ba79ec565902ae47b8a36f719a4ae5a4e99a81238` | **FROZEN** |

---

## 9. Governance & Project State Lock

- **Training Performed in Closure:** NO
- **Inference Performed in Closure:** NO
- **Optimizer Steps:** 0
- **Test Set Reads:** 0
- **Test Metrics Evaluated:** NONE
- **External Data Used:** NO
- **Experiment A Modified:** NO
- **Phase 15 Status:** NOT_AUTHORIZED (Not Started)
- **Phase 16 Status:** NOT_STARTED
- **Next Action:** WAIT_FOR_SUPERVISOR_ROADMAP_DECISION
