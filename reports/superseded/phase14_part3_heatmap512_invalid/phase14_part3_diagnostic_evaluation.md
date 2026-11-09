# Phase 14 Regional Refiner Diagnostic — Part 3 Full Validation Diagnostic Evaluation Audit

## 1. Executive Summary
- **Primary Population:** KUB FULL_FIELD VAL (106 images, 156 authoritative components)
- **Component Size Stratification:** 73 Tiny, 29 Small, 36 Medium, 18 Large
- **Hard Failure Cases:** 16 hard-Tiny components, 7 global-empty images
- **Checkpoints:**
  - Global UNet++: `4bffcf926227fb11029ead6bcd8e7dd8ed246e0f1678e3efb2ce4297439a3f2d`
  - Regional Refiner: `89ada72700385ed56b49b6caf34d9061349c24a566794176911b83fb0c8cd9f0` (epoch 14)
  - Stage-4D Localizer: `ece906df6c73f2e93c3f873661490bf3cb1a6b82be2d2d93b58c25bc967cbace` (thresh=0.10, margin=0.20, Top-K=5, NMS=0.30)

## 2. Mode Performance Summary
| Mode | FULL_FIELD Mean Dice | Median Dice | Overall Recall@90 | Tiny Recall@90 | Small Recall@90 | Med Recall@90 | Large Recall@90 | Hard Tiny Rec | GE Rec | Mean FP/img | Mean ROI Area |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **GLOBAL_ONLY** | 0.642499 | 0.760397 | 0.846154 | 0.794521 | 0.862069 | 0.888889 | 0.944444 | 1/16 | 0/7 | 0.3585 | 0.0000 |
| **ORACLE_REGIONAL** | 0.813166 | 0.841177 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 16/16 | 7/7 | 0.5283 | 0.0045 |
| **PREDICTED_REGIONAL** | 0.349511 | 0.316490 | 0.897436 | 0.808219 | 0.965517 | 1.000000 | 0.944444 | 2/16 | 3/7 | 6.0849 | 0.0068 |

## 3. Diagnostic Contrasts & Gate Hierarchy
- **Frozen References:** $D_g = 0.652776$, $T_g = 0.780822$
- **Measured Values:**
  - $D_o = 0.813166$, $T_o = 1.000000$ (Oracle Regional)
  - $D_p = 0.349511$, $T_p = 0.808219$ (Predicted Regional)
- **Contrast G (Oracle Gain):** $G = T_o - T_g = 1.000000 - 0.780822 = +0.219178$
- **Contrast R (Retention):** $R = (T_p - T_g) / G = 0.125000$

### Gate Results
1. **Step 1 — Refiner Potential:** `PASS`
   - Condition: $G \ge 0.05$ AND $D_o \ge 0.632776$
   - Actual: $G = +0.219178$, $D_o = 0.813166$
2. **Step 2 — Proposal Retention:** `FAIL`
   - Condition: $R \ge 0.50$
   - Actual: $R = 0.125000$
3. **Step 3 — Practical Net Benefit:** `FAIL`
   - Condition: $T_p \ge 0.780822$, $D_p \ge 0.632776$, Hard-Tiny $\ge 2/16$, Global-Empty $\ge 1/7$
   - Actual: $T_p = 0.808219$, $D_p = 0.349511$, Hard-Tiny = 2/16, Global-Empty = 3/7

## 4. Final Classification
**`DIAGNOSTIC_PROPOSAL_BOTTLENECK`**

- **Phase-15 Consequence:** `NOT_AUTHORIZED`

## 5. Governance and Cryptographic Lock
- TEST content reads: 0
- TEST metrics: NONE
- External data: NO
- Experiment A modified: NO
- Training executed: NO (frozen evaluation pass)
