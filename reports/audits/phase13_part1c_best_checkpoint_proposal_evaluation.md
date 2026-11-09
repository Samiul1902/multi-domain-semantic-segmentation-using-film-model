# PHASE-13 PART-1C — FROZEN BEST-CHECKPOINT STANDALONE GT-FREE PROPOSAL EVALUATION

- status: **PASS**
- best checkpoint epoch: **53**
- best.pt SHA: `7673c34a2f2c86eca2e45c1bc6abe77842d17cd09f122f2da0f2d414ca492273`
- lineage: R2 + R2A + NON_SCIENTIFIC_PROVENANCE_BINDING + R2B(provenance) + R2C
- manifest / taxonomy: `phase4_v3` / `kub_size_clean_v3_v1`

## Population and contract

| item | value |
|---|---|
| VAL images | 103 |
| VAL components | 152 |
| strata | TINY 72 / SMALL 28 / MEDIUM 36 / LARGE 16 |
| heatmap | 512 -> 128 |
| proposal config | 0.10 / 0.20 / 5 / 0.30 |
| proposal configurations | 1 |
| grid search | DISABLED |
| primary coverage | `HISTORICAL_EXECUTING_BBOX_COVERAGE` |
| secondary sensitivity | `PIXEL_MASK_COMPONENT_COVERAGE` |
| total proposals | **494** |

## Reproduction gate vs frozen Part-1B integrity audit

mismatches: **0** (tolerance 1e-12)

## Canonical BBOX metrics (PRIMARY)

| metric | value |
|---|---|
| tiny_recall90 | 0.6805555555555556 |
| overall_recall90 | 0.5986842105263158 |
| mean_roi_area_fraction | 0.004846047236646118 |
| hard_tiny_recovered90 | 4 |
| global_empty_images_covered90 | 1 |
| multi_component_recall90 | 0.5714285714285714 |
| mean_proposals_per_image | 4.796116504854369 |
| overall_recall50 | 0.7894736842105263 |
| any_overlap_recall | 0.8486842105263158 |
| mean_coverage | 0.7584022780771768 |

## Pixel sensitivity metrics (SECONDARY)

| metric | value |
|---|---|
| tiny_recall90 | 0.6944444444444444 |
| overall_recall90 | 0.6644736842105263 |
| hard_tiny_recovered90 | 5 |
| global_empty_images_covered90 | 1 |
| multi_component_recall90 | 0.6224489795918368 |
| overall_recall50 | 0.8026315789473685 |
| any_overlap_recall | 0.8486842105263158 |
| mean_coverage | 0.7768993431799454 |

## Proposal any-hit precision (DESCRIPTIVE ONLY)

- `proposal_bbox_any_hit_precision`: **0.24898785425101214**
- `proposal_pixel_any_hit_precision`: **0.24696356275303644**
- role: `DESCRIPTIVE_ONLY_NOT_SELECTION_NOT_GATE_NOT_TUNED`

## Bbox / pixel disagreement (sensitivity only)

- covered90 disagreements: **10**
- covered50 disagreements: **4**
- any-overlap disagreements: **0**
- mean bbox − pixel: -0.01849706510276846
- median bbox − pixel: 0.0
- largest positive: 0.0458992164024832 | largest negative: -0.1345996136216201
- by stratum (mean): {'TINY': -0.004707144266427323, 'SMALL': -0.024798879421307835, 'MEDIUM': -0.03584090539544789, 'LARGE': -0.03049989315033095}

## Special cohorts

| cohort | unit | denominator | bbox covered90 | pixel covered90 |
|---|---|---|---|---|
| hard_tiny | COMPONENT | 15 | 4 | 5 |
| global_empty | IMAGE | 5 | 1 | 1 |
| multi_component | COMPONENT | 98 | 56 | 61 |

Uncovered components (bbox_covered90 == FALSE): **61**

## Side-effect counts

| counter | value |
|---|---|
| new full-VAL inference passes | 1 |
| model constructions | 1 |
| training | 0 |
| optimizer | 0 |
| grid configs | 0 |
| regional segmentation | 0 |
| TEST reads | 0 |
| gate decision | `NOT_DECIDED` |
