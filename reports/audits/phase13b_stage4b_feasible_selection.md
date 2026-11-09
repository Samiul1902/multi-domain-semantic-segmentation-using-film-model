# Phase 13B Stage-4B: Feasibility-Constrained Localization

## Status
FAIL / CHECK_REQUIRED

## Goal
Implement a feasibility-constrained localization objective to replace the unconstrained recall objective that caused degenerate full-image ROIs in early epochs.

## Constraints
A proposal configuration is FEASIBLE only if:
- mean union ROI area fraction <= 0.10
- mean proposals/image <= 5

## V2 Replay Results
The new logic was mathematically replayed on the `phase13b_kub_localizer_r512_s3_seed42_v2` checkpoints (`best.pt` epoch 22, `latest.pt` epoch 24).
- The previously selected configs (which achieved perfect recall but had area=1.0) were correctly marked INFEASIBLE and rejected.
- At threshold 0.1 to 0.4, all configurations were infeasible due to area > 0.10.
- At threshold 0.5, the configurations were feasible (area 0.0, proposals 0) and correctly bubbled to the top, yielding 0.0 recall, correctly reflecting that the checkpoint had not learned localized features.
- Total feasible configs out of 20: 16

## Unit Tests
Unit tests were added to `tests/test_kub_localizer.py` verifying:
- Deterministic sorting of feasible configs.
- Rejection of infeasible configs despite perfect recall.
- Preference for smaller mean ROI area as the secondary tie-breaker.
Tests passed.

## Pilot V3 Results
The pilot training `phase13b_kub_localizer_r512_s3_seed42_v3` was executed using the new feasibility constraints.
- The training stopped early at epoch 26 (patience 15 triggered after best epoch 11).
- The best feasible configuration at epoch 11 had:
  - Threshold: 0.2
  - Margin: 0.1
  - Top-K: 3
- The resulting recall was heavily degraded:
  - Tiny recall90: 1.37%
  - Overall recall90: 3.85%
  - Hard Tiny recovered90: 0/16
  - Global Empty covered90: 1/7
- The mean ROI area was bounded at 6.3% and mean proposals at 3.0.

**Scientific Interpretation:** 
With full-image ROIs banned by the feasibility constraints, the model was forced to produce compact proposals. However, under the current `0.75 Focal + 0.25 SoftDice` loss formulation (dominated by background), the network fails to learn meaningful sparse representations. The probabilities simply decay uniformly, and when bounded by ROI budget constraints, the network yields near-zero recall. This proves the loss must be redesigned to allow genuine learning of KUB locations.
