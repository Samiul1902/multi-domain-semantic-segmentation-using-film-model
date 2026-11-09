# PHASE-13 PART-1B — R2B METRIC-SEMANTICS IMPLEMENTATION CORRECTION

- **base protocol:** R2
- **loss amendment:** R2A_LOSS_BINDING
- **amendment:** `R2B_METRIC_SEMANTICS_IMPLEMENTATION_CORRECTION`
- **scope:** `VAL_EVALUATION_IMPLEMENTATION_ONLY`

| declaration | value |
|---|---|
| scientific definitions changed | **NO** |
| implementation corrected to frozen definitions | **YES** |
| primary selection tuple changed | NO |
| proposal configuration changed | NO |
| loss changed | NO |
| architecture changed | NO |
| target changed | NO |
| optimizer changed | NO |
| threshold changed | NO |
| history rows 1–28 rewritten | **NO** |
| TEST reads | **0** |

---

## Defects corrected

| id | impact | correction |
|---|---|---|
| `MISSING_NATIVE_COMPONENT_MASK_IN_PRODUCTION_EVALUATOR` | **PRIMARY** | Attach the full native boolean mask; stop the silent bbox fallback |
| `HARD_TINY_SAMPLE_LEVEL_INSTEAD_OF_COMPONENT_LEVEL` | SECONDARY | Component identity `(sample_id, native_component_id)`; integer count / 15 |
| `GLOBAL_EMPTY_GT_EMPTY_BRANCH_ERROR` | SECONDARY | Integer count / 5 over the frozen image IDs, evaluated even though those images contain GT components |
| `MULTICOMPONENT_CASE_COMPLETE_INSTEAD_OF_COMPONENT_MEAN` | SECONDARY | Component-level mean of `covered90` over multi-component image rows |

**Root cause of the primary defect:** `evaluate_roi_coverage` uses
`component.get("mask")` and, when the mask is absent, silently falls back to
**bbox-intersection** coverage (`src/inference/predicted_roi.py`, else-branch).
The pre-R2B evaluator never attached a mask, so the frozen pixel-coverage
definition was never actually applied.

---

## Frozen definitions preserved (unchanged)

```
coverage_fraction = native GT component pixels inside union of proposal supports
                    / total native GT component pixels
covered90  = coverage_fraction >= 0.90
tiny_recall90       = mean(covered90) over the 72 TINY components
overall_recall90    = mean(covered90) over all 152 components
mean_roi_area_fraction = mean over 103 VAL images of union area / native area
hard_tiny_recovered90          = INTEGER COUNT 0..15
global_empty_images_covered90  = INTEGER COUNT 0..5
multi_component_recall90       = mean(covered90) over component rows of multi-component images
```

Explicitly **rejected**: bbox area as coverage, bbox intersection as coverage,
case-level detection as component recall, sample-level hard-Tiny membership,
global-empty restricted to a GT-empty branch.

Reference: frozen historical executing semantics,
`scripts/training/train_phase13b_localizer.py` lines 83 and 86.

---

## Controlled runner-SHA transition

| field | value |
|---|---|
| pre-repair runner SHA | `f9d8c0d4166b283f279a43102083ad2d898724385729ab30ab6a3723fc4744f0` |
| post-repair runner SHA | `15a0c2f0cf02916f96f60b7cf3d148fac4d931df11d5e119eb9c76f22a0c889b` |
| authorized transitions | **1** (checkpoint epoch 28 → first resumed epoch 29) |
| generic bypass | **NONE** |

The runner verifies that `post_repair_runner_sha` equals its own executing SHA,
so a runner edited after R2B was frozen cannot inherit the transition.

---

## Component contract

103 cases / **152 components** / 152 unique identities /
strata **72-28-36-16** / hard-Tiny **15** / global-empty **5**.
Join: **152/152 matched, 0 missing, 0 duplicates, 0 ambiguous** on
`sample_id + native_component_id`.

---

## Disclosure

The frozen historical helper `gt_components(mask_path, component_metadata)`
accepts `mask_path` but never attaches a mask, so **pre-R2B coverage — historical
and clean-v3 alike — used the bbox fallback path.** R2B corrects the clean-v3
implementation to the frozen PIXEL definition. Historical artifacts are frozen
and were **not** modified.

This amendment does **not** claim the pre-repair evaluator was correct. It claims
only that its defect could not alter the primary selection tuple while proposals
were zero.
