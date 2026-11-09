# POST-PHASE-13 H2B — SoftTargetFocalBCE Synthetic Loss / Gradient Unit Audit

- **Status: PASS**
- Execution: `CPU_ONLY_SYNTHETIC`
- Loss module: `src/losses/soft_target_focal_bce.py` (`SoftTargetFocalBCE`, gamma=2.0)
- Loss module SHA: `40d359e36a5579ea7544a1f0079aa999e024b8b144956493c184388766c27b75`
- Formula: `L = mean( |sigmoid(z) - y|^gamma * BCEWithLogits(z, y) ), gamma = 2.0`
- Modulation detached: **NO**
- Gradient through BCE term: **True** · through modulation term: **True**
- Model constructions: **0** · CUDA requests: **0** · project images/masks used: **0**

## Checks

| check | result |
|---|---|
| all_losses_and_gradients_finite | **True** |
| no_nan_no_inf | **True** |
| y0_loss_increases_with_p | **True** |
| y1_loss_increases_as_p_to_0 | **True** |
| soft_target_minimised_near_p_equals_y | **True** |
| symmetry_L_y0_q_equals_L_y1_1mq | **True** |
| modulation_not_detached | **True** |
| all_rows_expected_direction_pass | **True** |
| target_out_of_range_rejected | **True** |
| target_nonfinite_rejected | **True** |

Symmetry max abs diff: `4.76837158203125e-07`

## Soft-target argmin (loss minimised at/near p = y)

| target | argmin probability | abs gap | ok |
|---|---|---|---|
| 0.25 | 0.25 | 0.0 | **True** |
| 0.5 | 0.5 | 0.0 | **True** |
| 0.75 | 0.75 | 0.0 | **True** |

Grid: targets [0.0, 0.25, 0.5, 0.75, 1.0] × probabilities [0.01, 0.1, 0.25, 0.5, 0.75, 0.9, 0.99] = **35 rows**.
Table: `reports/tables/post_phase13_h2b_soft_target_focal_gradient_sanity.csv` (SHA `cec71e9ef274111d…`)

Hyperparameter grid: **0** · alpha sweep: **0** · beta sweep: **0** · coefficient search: **0**.
