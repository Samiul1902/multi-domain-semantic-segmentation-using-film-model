# Phase 14 clean-v3 Full Validation Diagnostic Evaluation Audit

## 1. Executive Summary
- **Primary Population:** KUB FULL_FIELD clean-v3 VAL (103 images, 152 authoritative components)
- **Component Size Stratification:** 72 Tiny, 28 Small, 36 Medium, 16 Large
- **Hard Failure Cases:** 15 hard-Tiny components, 5 global-empty images
- **Checkpoints:**
  - Global UNet++: `ec7eb13f32e43af27eab7fc617bd1a2a8fcce1d6651a1b4a3653f3e4d1283269`
  - Regional Refiner: `2e09e3a9c39c731687db1a9fef0c80881ed6235e4cda070bb4b8b382caa45daa` (epoch 56)
  - Stage-4D Localizer: `7673c34a2f2c86eca2e45c1bc6abe77842d17cd09f122f2da0f2d414ca492273` (thresh=0.10, margin=0.20, Top-K=5, NMS=0.30)

## 2. Mode Performance Summary
| Mode | FULL_FIELD Mean Dice | Median Dice | Overall Recall@90 | Tiny Recall@90 | Small Recall@90 | Med Recall@90 | Large Recall@90 | Hard Tiny Rec | GE Rec | Mean FP/img | Mean ROI Area |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **GLOBAL_ONLY** | 0.635917 | 0.745656 | 0.822368 | 0.791667 | 0.821429 | 0.861111 | 0.875000 | 0/15 | 0/5 | 0.4854 | 0.0000 |
| **ORACLE_REGIONAL** | 0.802416 | 0.834329 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 15/15 | 5/5 | 0.6311 | 0.0034 |
| **PREDICTED_REGIONAL** | 0.418531 | 0.370672 | 0.875000 | 0.791667 | 0.892857 | 1.000000 | 0.937500 | 0/15 | 1/5 | 7.7767 | 0.0049 |

## 3. Diagnostic Contrasts & Gate Hierarchy
- **Frozen References:** $D_g = 0.635917$, $T_g = 0.791667$
- **Measured Values:**
  - $D_o = 0.802416$, $T_o = 1.000000$ (Oracle Regional)
  - $D_p = 0.418531$, $T_p = 0.791667$ (Predicted Regional)
- **Contrast G (Oracle Gain):** $G = T_o - T_g = 1.000000 - 0.791667 = +0.208333$
- **Contrast R (Retention):** $R = (T_p - T_g) / G = 0.000000$

### Gate Results
1. **Step 1 — Refiner Potential:** `PASS`
   - Condition: $G \ge 0.05$ AND $D_o \ge 0.632776$
   - Actual: $G = +0.208333$, $D_o = 0.802416$
2. **Step 2 — Proposal Retention:** `FAIL`
   - Condition: $R \ge 0.50$
   - Actual: $R = 0.000000$
3. **Step 3 — Practical Net Benefit:** `FAIL`
   - Condition: $T_p \ge 0.780822$, $D_p \ge 0.632776$, Hard-Tiny $\ge 2/15$, Global-Empty $\ge 1/5$
   - Actual: $T_p = 0.791667$, $D_p = 0.418531$, Hard-Tiny = 0/15, Global-Empty = 1/5

## 4. Final Classification
**`DIAGNOSTIC_PROPOSAL_BOTTLENECK`**

- **Phase-15 Consequence:** `NOT_AUTHORIZED`

## 5. Governance and Cryptographic Lock
- TEST content reads: 0
- TEST metrics: NONE
- External data: NO
- Experiment A modified: NO
- Training executed: NO (frozen evaluation pass)
