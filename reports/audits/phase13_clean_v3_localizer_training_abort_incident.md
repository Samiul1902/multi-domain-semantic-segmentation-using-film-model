# PHASE-13 PART-1B — TRAINING ABORT INCIDENT

- experiment_id: `phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_clean_v3`
- stopped_by: **SUPERVISOR_ORDER** (`SIGTERM`, exit 143)
- run_status: **ABORTED_NOT_COMPLETED**
- epochs_completed: **28**
- completion audit written: **False**

## Observed defect

`tiny_recall90` and `overall_recall90` were **0.000 for all 28 epochs**.
`mean_roi_area_fraction` was **0.0** throughout. No proposal was ever generated.

Meanwhile `val_loss` fell monotonically from **10.3618** to
**2.2076** (78.7% reduction),
so the optimiser was genuinely descending — into a degenerate minimum.

## Checkpoint evidence (epoch 27)

| quantity | value |
|---|---|
| `head.bias` | **-2.2245101928710938** |
| implied peak probability | **0.097571** |
| frozen proposal threshold | 0.1 |
| **threshold gap** | **+0.002429** |
| bias needed to cross threshold | -2.197225 |
| `head.weight` min / max | -0.15079878270626068 / -0.14705722033977509 |
| `best_validation_score` | `[0.0, 0.0, -0.0, -2.188045249535487]` |

The model predicts a **spatially uniform** logit of ~-2.2245 everywhere.
`sigmoid(-2.2245) = 0.097571`, which sits
**0.002429 below** the 0.10 threshold. Zero pixels qualify, so zero
proposals are produced, so recall is structurally pinned to 0.

## Mechanism

1. The target heatmap uses `sigma = 0.75` in 128-space. This makes each target
   effectively a **single-pixel spike** (1 pixel at 1.0 against
   16383 background pixels, ratio **1:16383**).
2. `CenterNetFocalLoss(alpha=2.0, beta=4.0)` sums `neg_loss` over the whole
   background and divides by `num_pos`. The background term dominates.
3. The cheapest descent is to **suppress the entire field**, landing just under the
   detection threshold.
4. Because terms 1-3 of the selection tuple are constant, the **entire** best-epoch
   decision collapsed onto `-val_loss`. Every loss improvement was accepted as a new
   best, so `bad_epochs` kept resetting and patience never accumulated.

## Protocol integrity

The manifest-provenance amendment is **intact** (`train_table_sha256` /
`val_table_sha256` absent; 8-field binding present; grid search not run; TEST not
read). **This is a scientific/optimisation defect, not a provenance defect.**

## Status

**NO REPAIR PERFORMED.** No new experiment ID created. Awaiting
**SUPERVISOR_PHASE13_PART1B_INCIDENT_REVIEW**.
