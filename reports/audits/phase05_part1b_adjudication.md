# Phase 05 Part 1B — Leakage Adjudication & Downstream Impact Report

- **Audit Execution Gate:** `PASS`
- **Scientific Leakage Gate:** `CHECK_REQUIRED`
- **Confirmed Exact Duplicate:** 1 raw KUB acquisition shared across `patient-00273` (TRAIN) and `patient-00320` (VAL).
  - Mask Dice: `0.9108` | Mask IoU: `0.8361` (annotator boundary variance).
- **Downstream Validation Sensitivity (Excluding Affected VAL Case):**
  - Phase 09 UNet: Mean Dice `0.7455` -> `0.7449` ($\Delta = -0.0006$)
  - Phase 10 UNet++: Mean Dice `0.7625` -> `0.7619` ($\Delta = -0.0006$)
  - Phase 10 DeepLabV3+: Mean Dice `0.7488` -> `0.7482` ($\Delta = -0.0005$)
  - Phase 10 AttnUNet: Mean Dice `0.7530` -> `0.7524` ($\Delta = -0.0006$)
  - Phase 12 Oracle ROI: Global Dice `0.6528` -> `0.6502` ($\Delta = -0.0026$)
  - Phase 14 Regional Refiner: Predicted Dice `0.3861` -> `0.3814` ($\Delta = -0.0046$)
- **Near-Duplicate Adjudication (64 TRAIN <-> VAL Pairs):**
  - `CONFIRMED_EXACT_DUPLICATE`: 1 (KUB raw collision)
  - `LIKELY_SAME_ACQUISITION`: 13 (ISIC distance-0 pairs with visual identity)
  - `UNRESOLVED_NEAR_DUPLICATE`: 4 (ISIC & KUB distance-2 pairs)
  - `LIKELY_FALSE_POSITIVE`: 46 (distance $\ge 4$ driven by background/border similarity)
- **Governance Enforced:** TEST content reads = 0 | TEST visualizations = 0 | Training = NO | Inference = NO.
