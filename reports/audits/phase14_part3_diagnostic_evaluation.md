# Phase 14 Part 3 — Canonical Diagnostic Evaluation (Reconciled)

## Authoritative Evaluator Reconciliation
- **Metric**: FROZEN HISTORICAL OBJECT RECALL (`src/metrics/object_metrics.py`, SHA-256 `9824397f0c2b5d88...`)
- **Success Criteria**: $\text{overlap} \ge 1\text{ pixel}$ with GT stone component
- **Reproduction**: Global Baseline Tiny = 57 / 73 = 0.780822 (EXACT MATCH with frozen $T_g$)
- **Secondary Metric (cov90)**: Strict pixel coverage $\ge 90\%$ (Global Tiny: 25/73; Oracle: 47/73; Predicted: 42/73)

## Gate Arithmetic (Authoritative Object Recall)
- **$T_g$**: 0.780822 (57/73), **$D_g$**: 0.652776
- **$T_o$**: 1.000000 (73/73), **$D_o$**: 0.815175
- **$T_p$**: 0.890411 (65/73), **$D_p$**: 0.383905
- **$G$ (Refiner Potential)**: $T_o - T_g = +0.219178$ ($16/73$)
- **$R$ (Proposal Retention Fraction)**: $(T_p - T_g) / G = 0.500000$ ($8/16$)

## Protocol Decision Gates
- **Step 1 (Refiner Potential):** PASS ($G = +0.219178 \ge 0.05$, $D_o = 0.815175 \ge 0.632776$)
  - *Finding*: When proposals are ideal, regional refinement significantly recovers missed stones (100% Tiny recall, +16.2% Dice gain).
- **Step 2 (Proposal Retention):** PASS ($R = 0.500000 \ge 0.50$)
  - *Finding*: Frozen Stage-4D localizer proposals retain exactly 50.0% of the oracle refiner's stone recovery benefit.
- **Step 3 (Practical Net Benefit):** FAIL ($T_p = 0.890411 \ge 0.780822$ [PASS], Hard-Tiny $=8 \ge 2$ [PASS], Global-Empty $=5 \ge 1$ [PASS], but $D_p = 0.383905 < 0.632776$ [FAIL])
  - *Finding*: End-to-end predicted regional refinement successfully recovers 8 hard-tiny stones, but suffers a severe full-field Dice drop (0.3839 vs baseline 0.6528) driven by false-positive proposal clutter (5.43 FP components/image vs 0.37 baseline).

## Final Diagnostic Classification
- **Classification:** `DIAGNOSTIC_PRACTICAL_SIGNAL_INSUFFICIENT`
- **Phase 15 Status:** `NOT_AUTHORIZED`
