# Phase 07 Part 1B — CLEAN-v3 Taxonomy Freeze Audit

**Status:** `PASS`  
**Model:** Gemini 3.1 Pro High  
**Generated:** 2026-09-20T04:24:10.064495+00:00

## Supervisor decision

- Part 1A PASS; taxonomy design authorized

## Clean taxonomy (FROZEN)

| Field | Value |
|---|---|
| Taxonomy ID | `kub_size_clean_v3_v1` |
| Status | **FROZEN** |
| Unit | object (connected component) |
| Connectivity | 8 |
| Foreground rule | `mask > 0` |
| Acquisition scope | FULL_FIELD |
| ROI handling | `ROI_NOT_PRIMARY_BINNED` |
| Metric | `component_ratio` |
| Q25 | `0.0001497998649691358` |
| Q50 | `0.0003401438395182292` |
| Q75 | `0.0008279682677469136` |

## Historical taxonomy (immutable)

- `kub_size_v1` — HISTORICAL_v2_IMMUTABLE
- Q25 `0.0001499766777599` · Q50 `0.00033976472454305` · Q75 `0.0008266496069636999`
- Modified: False

## Quantile method

| Field | Value |
|---|---|
| Implementation | `numpy.quantile` |
| Method | default 'linear' interpolation |
| Call | `np.quantile(values, [0.25, 0.50, 0.75])` |
| Precision | float64 |

## Historical reproduction

- Reproduced exactly: **True**
- Source table: `reports/tables/kub_train_components_sized.csv`
- Source table SHA matches provenance: True
- Recomputed: {'Q25': 0.0001499766777599, 'Q50': 0.00033976472454305, 'Q75': 0.0008266496069636999}
- Recorded: {'Q25': 0.0001499766777599, 'Q50': 0.00033976472454305, 'Q75': 0.0008266496069636999}

## Derivation

| Field | Value |
|---|---|
| Manifest version | `phase4_v3` |
| Split | TRAIN |
| FULL_FIELD cases | 770 |
| Objects | 1161 |
| Object table | `phase07_clean_v3_threshold_derivation_objects.csv` |
| Object table SHA | `5c270dd4cb09e5697fdd5d7eb2ae4465f82489bb71ccead019a558934f5d1a08` |
| Persistence cross-check agrees | False |
| Max relative diff (persistence vs canonical) | 2.390e-13 |
| Precision choice changes classification | 3 objects |

## Threshold artifact

- Path: `reports/audits/kub_size_clean_v3_v1_thresholds.json`
- SHA-256: `89031c51a35c24f6f939fd6206fde6002a019d4bda24ce8cb21988f04db0f0d6`

## Frozen distributions

| Stratum | TRAIN objects | TRAIN % | VAL objects | VAL % |
|---|---:|---:|---:|---:|
| TINY | 291 | 25.0646 | 72 | 47.3684 |
| SMALL | 290 | 24.9785 | 28 | 18.4211 |
| MEDIUM | 290 | 24.9785 | 36 | 23.6842 |
| LARGE | 290 | 24.9785 | 16 | 10.5263 |

## VAL population

- FULL_FIELD cases: 103
- Objects: 152

## Crosswalk (TRAIN, historical vs clean)

- Objects: 1161
- Changed stratum: 2
- Changed percent: 0.172265%

## Derivation sequence (provenance)

| Step | UTC | Detail |
|---|---|---|
| immutability | 2026-09-20T04:24:10.075144+00:00 | verified previous-phase artifacts unchanged |
| historical_reproduction | 2026-09-20T04:24:10.087147+00:00 | kub_size_v1 reproduced exactly from historical table |
| A_derive | 2026-09-20T04:24:51.407330+00:00 | TRAIN FULL_FIELD cases=770 objects=1161 |
| A_derive_quantiles | 2026-09-20T04:24:51.432324+00:00 | Q25=0.0001497998649691358 Q50=0.0003401438395182292 Q75=0.0008279682677469136 persistence_crosscheck_agrees=False precision_class_changes=3 |
| B_persist | 2026-09-20T04:24:51.440866+00:00 | reports\audits\kub_size_clean_v3_v1_thresholds.json (reused existing frozen artifact) |
| C_hash | 2026-09-20T04:24:51.440866+00:00 | 89031c51a35c24f6f939fd6206fde6002a019d4bda24ce8cb21988f04db0f0d6 |
| D_frozen | 2026-09-20T04:24:51.440866+00:00 | status=FROZEN |
| E_val_unlock | 2026-09-20T04:24:51.440866+00:00 | VAL medical content read begins AFTER freeze artifact hashed |
| E_val_read | 2026-09-20T04:24:58.145568+00:00 | VAL FULL_FIELD cases=103 objects=152 |
| F_apply | 2026-09-20T04:24:58.146568+00:00 | frozen thresholds applied to TRAIN and VAL unchanged |

## Governance

- VAL content reads before freeze: 0
- TEST content reads: 0
- Thresholds changed after VAL: False
- ROI-specific taxonomy created: False
- Historical kub_size_v1 modified: False
- Part-1A C2 wording corrected in freeze record: True

## Immutability

- Phase-06 notebook unchanged: True
- Phase-07 Part-1A notebook unchanged: True

## Scientific gate

| Gate | Result |
|---|---|
| historical_kub_size_v1_immutable | PASS |
| thresholds_from_train_full_field_only | PASS |
| historical_quantile_method_reproduced | PASS |
| threshold_artifact_persisted_and_hashed_before_val | PASS |
| clean_taxonomy_frozen | PASS |
| val_used_only_after_freeze | PASS |
| thresholds_unchanged_after_val | PASS |
| roi_not_primary_binned | PASS |
| object_level_8_connectivity_frozen | PASS |
| boundary_semantics_exact | PASS |
| no_test_content_access | PASS |
| phase06_notebook_unchanged | PASS |
| phase07_part1a_notebook_unchanged | PASS |

**Overall: PASS**

## Table artifacts

| Table | SHA-256 |
|---|---|
| `phase07_clean_v3_threshold_derivation_objects.csv` | `5c270dd4cb09e5697fdd5d7eb2ae4465f82489bb71ccead019a558934f5d1a08` |
| `phase07_historical_vs_clean_thresholds.csv` | `6ddadd8f4717db0c6bc462247345d18ecb58a5ada71ffa0a11a5c3b52ea227f4` |
| `phase07_train_historical_clean_label_crosswalk.csv` | `d1cc3951c791003d6dc28f4bc7e41f93c8741cf31977270b0d65a58c856839d0` |
| `phase07_kub_v3_val_object_size_frozen.csv` | `3300a266505eb4d21f91c685dea09edddb7f8b4cb51c3a217548440a3894162b` |
| `phase07_kub_v3_frozen_taxonomy_summary.csv` | `74705df82683da4ae204e51d326e0e2b614174ab5c1f49a9736e42be1790a956` |
