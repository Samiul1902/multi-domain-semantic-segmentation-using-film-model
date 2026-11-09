# KUB Object-Size Thresholds (Taxonomy Version: `kub_size_v1`)

## Methodology
- **FOV Stratification**: KUB dataset contains two distinct acquisition types: `FULL_FIELD` (full radiography plates) and `ROI_CROP` (cropped ROI images).
- **Threshold Source**: Predeclared quartile cutouts (Q25, Q50, Q75) computed exclusively on **TRAIN FULL_FIELD connected components** (n=1162).
- **Primary Measure**: `component_ratio` = `component_pixels / image_area`.

## Frozen Threshold Cutoffs
- **Q25**: `0.00014998` (~0.015% of image area)
- **Q50**: `0.00033976` (~0.034% of image area)
- **Q75**: `0.00082665` (~0.083% of image area)

## Strata Definitions
- **TINY**: `component_ratio <= 0.00014998`
- **SMALL**: `0.00014998 < component_ratio <= 0.00033976`
- **MEDIUM**: `0.00033976 < component_ratio <= 0.00082665`
- **LARGE**: `component_ratio > 0.00082665`

*Note: These strata are dataset-relative for research evaluation and do not represent millimeter-based clinical stone sizes. VAL receives frozen TRAIN thresholds. TEST mask morphology remains locked.*
