# KUB Object-Size Taxonomy: Reconciled Methodology

The FOV rule uses explicit path components: `Images` is FULL_FIELD, `ROI` is ROI_CROP,
and anything else is UNRESOLVED. Dimensions are supporting evidence only.

Sample counts and component counts are separate:
- TRAIN samples: FULL_FIELD 771; ROI_CROP 1208; UNRESOLVED 0; total 1979.
- TRAIN components: FULL_FIELD 1162; ROI_CROP 1214; UNRESOLVED 0; total 2376.

`kub_size_v1` is unchanged. It uses 8-connected FULL_FIELD TRAIN components only:
- Q25 = 0.000149976677760
- Q50 = 0.000339764724543
- Q75 = 0.000826649606964

VAL receives these frozen TRAIN thresholds. TEST masks and external data are not accessed.
The strata are dataset-relative and have no physical/mm clinical interpretation.
