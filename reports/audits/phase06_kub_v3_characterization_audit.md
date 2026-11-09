# Phase 06 Part 1A-R1 — KUB v3 Characterization Audit

**Status:** `PASS`  
**Model:** Gemini 3.8 Flash Medium  
**Active manifest:** `phase4_v3`  
**Historical manifest:** `phase4_v2`  
**Generated:** 2026-09-20T03:12:34.179859+00:00

## Repair Scope (Part 1A-R1)

- Part: `1A-R1`
- Scope: distribution-interpretation + stratification + reviewer-visualization repair
- Population changed: False
- Split membership changed: False
- Pre-repair notebook SHA: `488af85c93ba6c986a13b57def06db94adfac7e0f26c965e2ace42f63edfe7d2`

## KUB Counts

| Split | Count |
|---|---|
| TRAIN | 1978 |
| VAL | 280 |
| TEST | 558 |
| QUARANTINED | 4 |

## Patient Counts

- KUB TRAIN unique patients: 318
- KUB VAL unique patients: 111
- TRAIN/VAL patient overlap: 0

## Mask Foreground Rule

- **mask > 0**
- Mask label vocabulary table: `reports/tables/phase06_kub_v3_mask_label_vocabulary.csv`
- Mask label vocabulary SHA: `07480745ecea3f37c5ece3259a0aeb2dd4491361a4ccbb2fcde5363f92012e51`
- Observed raw labels: [0, 1, 2, 3, 255]

| Label signature | Cases |
|---|---|
| `0|1` | 465 |
| `0|1|2` | 3 |
| `0|2` | 304 |
| `0|3` | 101 |
| `0|255` | 1385 |

## Descriptive Differences (TRAIN vs VAL)

- Max category percentage-point difference: **19.3760 pp**
- Max acquisition percentage-point difference: **2.1425 pp**
- Multi-component TRAIN: **10.7179%**
- Multi-component VAL: **17.5000%**

### Category

| Level | TRAIN cases | TRAIN % | VAL cases | VAL % | abs diff (pp) |
|---|---:|---:|---:|---:|---:|
| Bladder_Stone | 634 | 32.0526 | 144 | 51.4286 | 19.3760 |
| Kidney_Stone | 1133 | 57.2801 | 112 | 40.0000 | 17.2801 |
| Ureteric_Stone | 211 | 10.6673 | 24 | 8.5714 | 2.0959 |

### Acquisition

| Level | TRAIN cases | TRAIN % | VAL cases | VAL % | abs diff (pp) |
|---|---:|---:|---:|---:|---:|
| FULL_FIELD | 770 | 38.9282 | 103 | 36.7857 | 2.1425 |
| ROI | 1208 | 61.0718 | 177 | 63.2143 | 2.1425 |

## Stratified Artifacts

- Stratified geometry table: `reports/tables/phase06_kub_v3_stratified_geometry_summary.csv`
- Stratified geometry SHA: `bffb72858cdb042f1c4f5b0b9b0987c49a84434df0ad99cc9427ea14b00957fa`
- Acquisition regime table: `reports/tables/phase06_kub_v3_acquisition_regime_geometry.csv`
- Acquisition regime SHA: `523a82bf4636e678ec143d6f8200a552b71de469a13b9654f2767f1dc795e295`

## Table Registry

- Final table count: **12**
- All tables hashed: **True**

| Table | SHA-256 |
|---|---|
| `phase06_kub_v3_population_summary.csv` | `afcca4cdc621bcb114c00844b22a9479be529889ef7e73c4a6e55129b4b44147` |
| `phase06_kub_v3_patient_summary.csv` | `93dc43eb8778d4a83602af07c041e4a419b798fe0c13f9e608cdb3029f3536ce` |
| `phase06_kub_v3_image_geometry_summary.csv` | `d579a76ae90fc1ed02a346c8e932bced44ef2daaa71992e41a8120d20b8e4f63` |
| `phase06_kub_v3_mask_geometry_summary.csv` | `cb09860332da254960c13f6ada453a4537caf86d4691bd9fc84a53a59cad35d2` |
| `phase06_kub_v3_category_summary.csv` | `512c18282dbbcf9802074c76ddcf8e7b468c0233a1dc36e9060c90839673a7f5` |
| `phase06_kub_v3_acquisition_summary.csv` | `19a95de00785fb7325d9fcebaccd183a36a3bd9a8f8ff2930c7788f0f0416c63` |
| `phase06_kub_v3_geometry_quantiles.csv` | `3f5b3fb6c9b87cd78675cf26b1e3a88819d9cf93dfa440d4e340045727f6b6ca` |
| `phase06_kub_v3_quarantined_metadata.csv` | `cc97693f8b305116d682084deeb69a97eb98ce508c8c5e10ad64a686af504cb5` |
| `phase06_kub_v3_sample_selection.csv` | `f187e17702f857be4ac70c118e7ff35e1217c30afed74f8a24283855c91d514b` |
| `phase06_kub_v3_mask_label_vocabulary.csv` | `07480745ecea3f37c5ece3259a0aeb2dd4491361a4ccbb2fcde5363f92012e51` |
| `phase06_kub_v3_acquisition_regime_geometry.csv` | `523a82bf4636e678ec143d6f8200a552b71de469a13b9654f2767f1dc795e295` |
| `phase06_kub_v3_stratified_geometry_summary.csv` | `bffb72858cdb042f1c4f5b0b9b0987c49a84434df0ad99cc9427ea14b00957fa` |

## Gallery

- Cases: 16
- Sample IDs changed: False
- Sample selection SHA: `7324b7cc91f4c39b76bfd80e78d14154d0e91ec165f727d4c43dfb82fac1d485`
- Pages: 4 (4 pages x 4 cases (3 panels each))
- Shows original: True
- Shows binary GT: True
- Shows GT overlay: True

## TEST Lock

- TEST content reads: 0
- TEST visualizations: 0
- TEST metrics: 0
- TEST referenced via manifest metadata only: YES

## Images Read

- From TRAIN: 1978
- From VAL: 280
- Total: 2258

## Notebook Execution State

- Path: `notebooks/phasewise/phase_06_kub_characterization/phase06_kub_dataset_characterization_clean_v3.ipynb`
- SHA-256: `c2164345d80843c6116093cc5c58bebfa3792b8becce0d887e6c379ab8069888`
- SHA stable (3x): YES
- Cells: 77 total / 36 code
- Executed: 36 | Unexecuted: 0
- Errors: 0 | Embedded PNG: 16
- Tiny threshold defined: NO
- Phase 07 started: NO
- Old 'no material anomaly' claim removed: True

## Phase-07 Governance Rule

> Phase 07 must NOT choose a tiny-object threshold by optimizing against VAL. The prospective tiny-object definition must be frozen using TRAIN-only empirical geometry and/or predeclared domain/geometric rationale before examining VAL prevalence/results under that threshold. VAL may then be used for evaluation/characterization after freeze.

## Scientific Gate

| Gate | Result |
|---|---|
| canonical_phase4_v3_verified | PASS |
| kub_train_1978 | PASS |
| kub_val_280 | PASS |
| patient_overlap_zero | PASS |
| all_pairs_valid | PASS |
| no_manifest_integrity_failure | PASS |
| statistics_from_clean_v3 | PASS |
| gallery_16_cases_3_panels | PASS |
| sample_selection_sha_unchanged | PASS |
| stratified_geometry_present | PASS |
| final_table_count_12 | PASS |
| all_tables_hashed | PASS |
| no_test_medical_access | PASS |
| no_tiny_threshold | PASS |
| notebook_run_all_clean | PASS |

**Overall: PASS**
