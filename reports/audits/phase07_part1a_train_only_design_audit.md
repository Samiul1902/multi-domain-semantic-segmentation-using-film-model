# Phase 07 Part 1A — TRAIN-Only Object-Size Taxonomy Design Audit

**Status:** `PASS`  
**Model:** Gemini 3.1 Pro High  
**Active manifest:** `phase4_v3`  
**Historical manifest:** `phase4_v2`  
**Generated:** 2026-09-20T04:02:00.516810+00:00

## TRAIN population

| Metric | Value |
|---|---|
| KUB TRAIN cases | 1978 |
| TRAIN patients | 318 |
| Multi-component cases (8-connectivity) | 210 |
| Multi-component cases (4-conn, Phase-06 reference) | 212 |
| TRAIN objects | 2375 |
| FULL_FIELD objects / cases | 1161 / 770 |
| ROI objects / cases | 1214 / 1208 |

> Connectivity note: Phase 07 uses 8-connectivity to match the historical kub_size_v1 taxonomy. Phase 06 used scipy.ndimage.label's default 4-connectivity, which splits diagonally touching regions and therefore reports a slightly higher multi-component case count (212 vs 210).

## Historical definition applied to CLEAN-v3 TRAIN

Label: `HISTORICAL_DEFINITION_APPLIED_TO_CLEAN_v3_TRAIN` (FULL_FIELD objects n=1161)

| Stratum | Objects | Prevalence |
|---|---:|---:|
| TINY | 291 | 25.0646% |
| SMALL | 289 | 24.8923% |
| MEDIUM | 290 | 24.9785% |
| LARGE | 291 | 25.0646% |

## Candidate taxonomies (EXPLORATORY — none frozen)

| Candidate | Metric | Unit | Acquisition | Cuts |
|---|---|---|---|---|
| `C1_HISTORICAL_kub_size_v1` | component_ratio | object (connected component, 8-connectivity) | FULL_FIELD only (ROI -> ROI_NOT_PRIMARY_BINNED) | 0.000149977 / 0.000339765 / 0.00082665 |
| `C2_NORMALIZED_EQ_DIAMETER` | normalized_equivalent_diameter | object (connected component, 8-connectivity) | both regimes (boundaries derived on FULL_FIELD TRAIN) | 0.0155413 / 0.0230702 / 0.0363009 |
| `C3_FULLFIELD_NATIVE_EQ_DIAMETER_PX` | equivalent_diameter | object (connected component, 8-connectivity) | FULL_FIELD only | 38.065 / 55.5548 / 85.994 |

### FULL_FIELD TRAIN counts

| Candidate | TINY | SMALL | MEDIUM | LARGE |
|---|---:|---:|---:|---:|
| `C1_HISTORICAL_kub_size_v1` | 291 | 289 | 290 | 291 |
| `C2_NORMALIZED_EQ_DIAMETER` | 291 | 290 | 290 | 290 |
| `C3_FULLFIELD_NATIVE_EQ_DIAMETER_PX` | 291 | 290 | 290 | 290 |

### ALL_TRAIN counts (cross-regime behaviour)

| Candidate | TINY | SMALL | MEDIUM | LARGE |
|---|---:|---:|---:|---:|
| `C1_HISTORICAL_kub_size_v1` | 291 | 289 | 290 | 291 |
| `C2_NORMALIZED_EQ_DIAMETER` | 291 | 294 | 292 | 1498 |
| `C3_FULLFIELD_NATIVE_EQ_DIAMETER_PX` | 291 | 290 | 290 | 290 |

**Cross-regime caveat:** Applying any FULL_FIELD-calibrated rule to ROI crops is not automatically valid: an ROI crop magnifies its object, so the object share of the crop is not comparable to the object share of a whole radiograph.

## Boundary sensitivity (TRAIN only)

| Candidate | Boundary | Cut | within +/-1 | within +/-2 |
|---|---|---:|---:|---:|
| `C1_HISTORICAL_kub_size_v1` | TINY_SMALL | 0.000149977 | 33 | 67 |
| `C1_HISTORICAL_kub_size_v1` | SMALL_MEDIUM | 0.000339765 | 28 | 59 |
| `C1_HISTORICAL_kub_size_v1` | MEDIUM_LARGE | 0.00082665 | 24 | 45 |
| `C2_NORMALIZED_EQ_DIAMETER` | TINY_SMALL | 0.0155413 | 61 | 118 |
| `C2_NORMALIZED_EQ_DIAMETER` | SMALL_MEDIUM | 0.0230702 | 65 | 140 |
| `C2_NORMALIZED_EQ_DIAMETER` | MEDIUM_LARGE | 0.0363009 | 43 | 86 |
| `C3_FULLFIELD_NATIVE_EQ_DIAMETER_PX` | TINY_SMALL | 38.065 | 53 | 87 |
| `C3_FULLFIELD_NATIVE_EQ_DIAMETER_PX` | SMALL_MEDIUM | 55.5548 | 21 | 50 |
| `C3_FULLFIELD_NATIVE_EQ_DIAMETER_PX` | MEDIUM_LARGE | 85.994 | 8 | 16 |

## Recommendation

- Status: **RECOMMENDED_FOR_SUPERVISOR_REVIEW**
- Candidate: `C1_HISTORICAL_kub_size_v1`
- Rationale: Highest historical continuity (identical metric, unit, connectivity, coordinate system and boundaries), it is already native-scale-normalized, and downstream object-recall analysis was built on these labels. C3 is offered as the most human-interpretable FULL_FIELD-only option. C2 is NOT recommended as-is: although its metric is scale-invariant, a FULL_FIELD-calibrated rule pushes almost all ROI objects into LARGE, so genuine cross-regime use would require separate ROI calibration (Option C). No VAL evidence was used.

## Governance

- VAL used for threshold selection: False
- VAL content reads (Part 1A): 0
- TEST content reads: 0
- TEST visualizations: 0
- TEST metrics: 0
- Threshold frozen: False
- Phase 08 started: False

## Phase-06 / Phase-05 immutability

- Phase-06 notebook: `notebooks/phasewise/phase_06_kub_characterization/phase06_kub_dataset_characterization_clean_v3.ipynb`
- Expected SHA: `c2164345d80843c6116093cc5c58bebfa3792b8becce0d887e6c379ab8069888`
- Actual SHA: `c2164345d80843c6116093cc5c58bebfa3792b8becce0d887e6c379ab8069888`
- Unchanged: **True**

| phase4_v3 manifest | SHA-256 |
|---|---|
| `train.csv` | `28702fc3a5ff8b950db372f03232d335e3a30b1fc2f21db7cd8c066055826ed6` |
| `val.csv` | `082c80b2bda63fd73f371f109c34643adf01edaead921643fb2e44993ba53315` |
| `test.csv` | `9361eba61c91c034a9aa4988a4df229bba591a5cbd553c98689ac7915da29727` |
| `quarantined.csv` | `a4ec1a8c46692f3c2d55d03c73569ce7b44aeeef734abd41e31bf5bf3e60059c` |

## Notebook execution state

- Path: `notebooks/phasewise/phase_07_tiny_object_definition/phase07_tiny_object_definition_train_only_design.ipynb`
- SHA-256: `f2ff7969d4c446c5c7fa737c7cbf36925123c97db1ca86593dbddea842a31eb9`
- SHA stable (3x): YES
- Cells: 47 total / 23 code
- Executed: 23 | Unexecuted: 0
- Errors: 0 | Embedded PNG: 11
- Figures on disk: 11

## Scientific gate

| Gate | Result |
|---|---|
| historical_definition_reconstructed | PASS |
| object_vs_case_explicit | PASS |
| train_only_object_geometry_exists | PASS |
| full_field_roi_handled_explicitly | PASS |
| candidates_compared | PASS |
| boundary_semantics_exact | PASS |
| boundary_sensitivity_reported | PASS |
| no_val_driven_selection | PASS |
| no_test_content_access | PASS |
| no_threshold_frozen | PASS |
| recommendation_provisional | PASS |
| phase06_notebook_unchanged | PASS |
| phase05_manifests_unchanged | PASS |
| notebook_run_all_clean | PASS |

**Overall: PASS**

## Table artifacts

| Table | SHA-256 |
|---|---|
| `phase07_kub_v3_train_object_geometry.csv` | `2094d2ed4fae02f05ad9b24e938a5707c73e3da794dcd536922da641f60318e8` |
| `phase07_kub_v3_train_case_size_summary.csv` | `d1b0c42f04ff4ac7ea26b7be919b04b44c20006f35cea75a486b0a2018d60d23` |
| `phase07_kub_v3_train_size_quantiles.csv` | `8c3b47a008cd530647f62a98c45986590b16aabd88530240fc0480f23a60aaf0` |
| `phase07_candidate_taxonomy_comparison.csv` | `7d42cf263ad865aabe8b15f34609943028c51dead14bfe306e80064efcd1f659` |
| `phase07_candidate_boundary_sensitivity.csv` | `3f80a4f3246a1b8ed5a17b5a6b36d1da37df9f17c7ab874f53e5e1b2bf687957` |
| `phase07_historical_definition_clean_v3_train.csv` | `77bf51beed28b55c5d68bf0671f4366172bad5993d7357b4ec99f9f41dee3274` |
| `phase07_train_gallery_selection.csv` | `79b45076aaa736c73a81c4c055906bf2c241e5a6f42ef638f9b96d7873ed7b5e` |
