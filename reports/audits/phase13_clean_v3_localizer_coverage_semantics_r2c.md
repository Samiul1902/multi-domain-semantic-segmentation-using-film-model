# PHASE-13 PART-1B — R2C COVERAGE-SEMANTICS ARBITRATION

- **amendment:** `R2C_HISTORICAL_EXECUTING_COVERAGE_ARBITRATION`
- **base:** R2 + R2A_LOSS_BINDING + provenance binding
- **supersedes for primary selection:** `R2B_PIXEL_MASK_COMPONENT_COVERAGE`
- **primary coverage semantics:** `HISTORICAL_EXECUTING_BBOX_COVERAGE`
- **pixel coverage role:** `SECONDARY_COVERAGE_SENSITIVITY_ONLY`
- **scientific materiality:** `MATERIAL_PROTOCOL_ARBITRATION_RESTORING_HISTORICAL_EXECUTING_SEMANTICS`

| declaration | value |
|---|---|
| selection tuple unchanged | **YES** |
| proposal config unchanged | YES |
| loss / architecture / target unchanged | YES |
| optimizer / scheduler unchanged | YES |
| history rewritten | **NO** |
| TEST reads | **0** |

## Why

Historical executing Phase-13 coverage was effectively **bbox-intersection**:
`gt_components(...)` never attached native component masks, so
`evaluate_roi_coverage(...)` always took its bbox fallback branch. R2/R2A give
precedence to **historical executing code** for the primary checkpoint-selection
protocol when documentation disagrees with execution — and that executing
behaviour produced the historical Phase-13 lineage.

R2B's pixel-mask coverage was scientifically meaningful but changed a **primary**
metric once proposals became nonzero. It is therefore demoted to a secondary
sensitivity metric and **must not** control `best checkpoint`, `bad_epochs`, or
`early stopping`.

R2B is **preserved as provenance** (not deleted, not rewritten).

## Explicit bbox implementation

The silent fallback is replaced by an explicit helper:

| helper | role |
|---|---|
| `evaluate_historical_bbox_coverage` | **PRIMARY** — ignores masks by design |
| `evaluate_pixel_mask_coverage` | SECONDARY sensitivity — fails loudly without a mask |

Authoritative source: `src/inference/predicted_roi.py::evaluate_roi_coverage`
else-branch, reproduced verbatim. No formula was inferred from prose.

## Epoch-31 canonical re-evaluation

| metric | BBOX (canonical) | PIXEL (recorded in history) |
|---|---|---|
| tiny_recall90 | **0.3888888888888889** | 0.4027777777777778 |
| overall_recall90 | **0.3881578947368421** | 0.4276315789473684 |
| mean_roi_area_fraction | 0.003918121982149612 | 0.003918121982149612 |
| val_loss | 2.178007864035093 | 2.178007864035093 |
| mean_proposals_per_image | 4.145631067961165 | 4.145631067961165 |

Pixel metrics **reproduced the immutable epoch-31 history exactly**. The bbox and
pixel primary terms differ materially, confirming the conflict was real.

## Canonical selection reconstruction

| item | value |
|---|---|
| prior canonical best through epoch 30 | **29** |
| epoch-31 canonical tuple | `[0.3888888888888889, 0.3881578947368421, -0.003918121982149612, -2.178007864035093]` |
| **epoch 31 still canonical best** | **YES** |
| canonical best through 31 | **31** |
| canonical bad_epochs after 31 | **0** |

Epoch 31's bbox first term (0.3889 > 0) strictly dominates epoch 29's
`(0, 0, 0, −val_loss)`, so **the epoch-31 weights remain the correct best
weights** — no weights were lost.

## Checkpoint archive and rebind

| item | value |
|---|---|
| archive dir | `checkpoints/<EXP>/provenance/` |
| label | `PROVISIONAL_R2B_PIXEL_SELECTION_CHECKPOINT` |
| downstream use | `NOT_FOR_DOWNSTREAM_USE` |
| byte-identical copies verified | **YES** |
| rebind status | **`PASS_MODEL_AND_TRAINING_STATE_UNCHANGED`** |
| state differences | **0** (model, optimizer, scheduler, scaler, RNG, generators, epoch, global_step) |

The rebound checkpoints record the canonical bbox tuple. **Only metadata
changed.** The disclosure that the original epoch-31 checkpoint was produced
under R2B pixel selection is recorded explicitly — this is not presented as if it
had been historically bbox-selected.

## Runner-SHA transition

| field | value |
|---|---|
| pre-repair runner SHA | `15a0c2f0cf02916f96f60b7cf3d148fac4d931df11d5e119eb9c76f22a0c889b` |
| post-repair runner SHA | `00ff82447f1f83935c042ea4fa19ad4f05956c48a80c474eaa98fc643bf79913` |

> **ERRATUM (2026-09-22).** This table previously reported the intermediate value
> `0d5a199d223296346f7d998551ec842f77298f0ec6e0328a1c6f007e8e751737`, which was
> captured before the final two runner edits and is **stale**. The authoritative
> value is `00ff82447f1f83935c042ea4fa19ad4f05956c48a80c474eaa98fc643bf79913`,
> established by the **R2C JSON**, the **checkpoint metadata**, and the
> **executing runner's physical SHA-256**. The R2C JSON was never wrong and was
> **not** modified. The stale value is retained above rather than hidden.
> See `phase13_clean_v3_localizer_coverage_semantics_r2c_erratum.{json,md}`.
> Classification: `R2C_MARKDOWN_RUNNER_SHA_REPORTING_ERRATUM_ONLY` —
> scientific result unchanged, model state unchanged, selection unchanged.
| authorized transitions | **1** (R2C epoch-31 rebind → first resumed epoch 32) |
| generic bypass | **NONE** |

## History governance

Rows 1–31 remain **untouched**. Row 31's legacy primary fields are pixel-based;
the authoritative reconstruction lives in
`reports/tables/phase13_part1b_canonical_selection_history.csv`.
Rows ≥ 32 will carry `coverage_semantics_primary = HISTORICAL_EXECUTING_BBOX_COVERAGE`
plus pixel sensitivity fields.
