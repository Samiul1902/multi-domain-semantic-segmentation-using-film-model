# Phase 13B — Learned Localizer Notebook Validation Audit

**Notebook Path:** `notebooks/11b_kub_learned_localizer.ipynb`  
**Date:** 2026-09-17  
**Status:** PASS (Audit & Analysis Only)  
**SHA-256:** `3b978fa99ea8797dfadda3c3d7927615edfabe180efdf581ae4fe4689730d01b`

---

## 1. Execution Summary

The notebook was created from scratch and validated via programmatic Run All using the project virtual environment (`D:\Softfors\jup\.venv\Scripts\python.exe` via `jupyter nbconvert`).

- **Total Cells:** 30
- **Code Cells:** 14 (all executed, 0 errors)
- **Markdown Cells:** 16
- **Safety Audit:** PASS (0 training calls, 0 optimizer steps, 0 backward passes, 0 test reads)

---

## 2. Provenance & Run Status Register

| Run ID | Loss / Architecture | Status | Reason / Scientific Notes |
|---|---|---|---|
| `phase13b_kub_localizer_r512_s3_seed42` | Focal+Dice (unapproved balancing) | `INVALID_FOR_FINAL_SELECTION` | Provisional exploratory run; unapproved pos/neg balancing; unconstrained checkpoint selection. |
| `phase13b_kub_localizer_r512_s3_seed42_v2` | Focal+Dice (frozen) | `INVALID_FOR_FINAL_SELECTION` | Stage-4A degenerate full-image ROIs (mean union area = 1.0; 106/106 images covered >=90%). |
| `phase13b_kub_localizer_r512_s3_seed42_v3` | Focal+Dice (feasibility gate) | `TRAINED` | Stage-4B feasibility pilot (epochs=26); revealed standard Focal+Dice fails compact localization (Tiny recall = 0.0137). |
| `phase13b_kub_localizer_r512_s3_centernetfocal_seed42_v1` | CenterNet Focal | `DIAGNOSTIC_ONLY` | Launched before preflight clearance; component count discrepancy and extreme initial scale. |
| `phase13b_kub_localizer_r512_s3_centernetfocal_seed42_v2` | CenterNet Focal (p01 init) | `ABORTED` | Suffered evaluation accumulator duplication and restart contamination with partial latest.pt. |
| `phase13b_kub_localizer_r512_s3_centernetfocal_seed42_v3` | CenterNet Focal (p01 init) | `TRAINED` (CLEAN V3) | Authoritative clean run (100 epochs complete); Stage-4C-R4 scientific evidence. |

---

## 3. Clean V3 Authoritative Results (Best Epoch 97)

Loaded directly from `history.csv`, `val_search_epoch097.csv`, and validation evaluation tables:

- **Best Epoch:** 97
- **Train Loss:** 2.046753
- **Val Loss:** 2.399564
- **Tiny Recall@90:** 0.465753 (34 / 73)
- **Small Recall@90:** 0.275862 (8 / 29)
- **Medium Recall@90:** 0.055556 (2 / 36)
- **Large Recall@90:** 0.000000 (0 / 18)
- **Overall Recall@90:** 0.282051 (44 / 156)
- **Overall Recall@50:** 0.564103 (88 / 156)
- **Any Overlap Recall:** 0.769231 (120 / 156)
- **Hard Tiny Recovered@90:** 1 / 16
- **Global Empty Covered@90:** 1 / 7
- **Multi-Component Recall@90:** 0.230000 (23 / 100)
- **Mean Proposals / Image:** 3.179245
- **Zero Proposal Images:** 2 / 106
- **Mean Union ROI Area Fraction:** 0.000863 (<0.1%)
- **Median Union ROI Area Fraction:** 0.000601
- **P90 Union ROI Area Fraction:** 0.001591
- **Max Union ROI Area Fraction:** 0.004439
- **Mean Max Heatmap Probability:** 0.100299
- **Median Max Heatmap Probability:** 0.100342

---

## 4. Stage-4C Promising Gate Evaluation

| Criterion | Required Threshold | Clean V3 Result | Status |
|---|---|---|---|
| **A. Tiny Recall@90** | $\ge 0.50$ | 0.465753 | **FAIL** |
| **B. Overall Recall@90** | $\ge 0.50$ | 0.282051 | **FAIL** |
| **C. Hard Tiny Recovered@90** | $\ge 2 / 16$ | 1 / 16 | **FAIL** |
| **D. Mean Union ROI Area** | $\le 0.10$ | 0.000863 | **PASS** |
| **E. Mean Proposals / Image** | $\le 5.0$ | 3.179245 | **PASS** |

**Final Scientific Gate Status:** **NOT_PROMISING**

---

## 5. Governance & Safety Checklist

- **Training Triggered:** NO
- **TEST Content Reads:** 0 (strictly locked)
- **TEST Metrics Calculated:** NONE
- **External Data Accessed:** NO
- **Experiment A Modified:** NO
- **Phase 14 Executed:** NO
- **Prohibited Executable Code Found:** 0

