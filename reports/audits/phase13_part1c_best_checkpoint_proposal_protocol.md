# PHASE-13 PART-1C — PRE-INFERENCE PROTOCOL FREEZE

- status: **SUPERVISOR_FROZEN_PART1C**
- best checkpoint epoch: **53**
- best checkpoint SHA: `7673c34a2f2c86eca2e45c1bc6abe77842d17cd09f122f2da0f2d414ca492273`
- component source SHA: `29326d5b9a3bf71add74d8743750511f146d8c4dfbd1dc5b04a5e1b647c37cc0`

| item | value |
|---|---|
| population | KUB FULL_FIELD VAL only |
| VAL images | 103 |
| native components | 152 |
| strata | TINY 72 / SMALL 28 / MEDIUM 36 / LARGE 16 |
| hard-Tiny | 15 components |
| global-empty | 5 images |
| heatmap | 512 -> 128 |
| proposal config | 0.10 / 0.20 / 5 / 0.30 |
| proposal configurations | 1 |
| grid search | DISABLED |
| primary coverage | HISTORICAL_EXECUTING_BBOX_COVERAGE |
| secondary sensitivity | PIXEL_MASK_COMPONENT_COVERAGE |
| TEST | LOCKED |
| gate threshold introduced | NONE |
| gate judgment authorized | NO |
| max new full-VAL inference passes | 1 |

**Descriptive-only precision definitions.** `proposal_bbox_any_hit_precision` = fraction of
emitted proposals intersecting at least one native GT bbox. `proposal_pixel_any_hit_precision` =
fraction of emitted proposals containing at least one native GT foreground pixel. These are
**DESCRIPTIVE ONLY** — not checkpoint-selection terms, not gate thresholds, not tuned metrics.
