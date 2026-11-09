# Supervisor Submission — Verification Report

**Verdict (pre-archive checks):** `PASS`  
**Markdown documents scanned:** 25  
**Python files scanned:** 69

This report is generated **before** the ZIP is built, so that it can be included in the archive. An archive cannot contain its own hash or its own CRC result: the archive SHA-256, CRC outcome, member count and per-member SHA-256 verification are written **out-of-band** after construction to `full_doc_report/Supervisor_Submission_ZIP_INTEGRITY.json` and `full_doc_report/ReMedFiLM_Supervisor_Submission.zip.sha256`.

## 1. File references

- Reference targets classified: `DOCUMENTED_MISSING_REFERENCE` 4, `DOCUMENTED_WITHHELD_ARTIFACT` 25, `EXTERNAL_DATASET_NAMED_ARTIFACT` 29, `INLINE_CODE_NAMED_ARTIFACT` 7, `PACKAGE_INTERNAL` 93, `PACKAGE_INTERNAL_BASENAME` 129, `PACKAGE_INTERNAL_EQUIVALENT` 5, `REPOSITORY_EXTERNAL` 282, `REPOSITORY_EXTERNAL_BASENAME` 50, `REPOSITORY_EXTERNAL_DIRECTORY` 12, `STAGE2_GENERATED_ARTIFACT` 11
- **Broken references: 0**

Only unresolved Markdown/HTML link targets are classified BROKEN. Inline-code path-like tokens are artifact names, not hyperlinks: they are resolved where possible or assigned an explicit WITHHELD / EXTERNAL / GENERATED / NAMED status. Copied repository documents retain their original repository-relative links; source-aware resolution uses COPY_MAP.json to resolve them from their original locations. REPOSITORY_EXTERNAL, REPOSITORY_EXTERNAL_BASENAME and PACKAGE_INTERNAL_EQUIVALENT entries are documented resolutions, not package-link failures.

## 2. Code dependencies

- Parse failures: 0
- Import classification: {'THIRD_PARTY': 15, 'STDLIB': 24, 'UNCLASSIFIED': 2, 'LOCAL_PROJECT': 18}
- Local `src.*` / flat modules: 18; **unresolved: 0**
- Third-party availability in this environment: 15/15 present

Scripts were copied out of the repository package tree into flat code/ directories. `src.*` imports need the original repository on PYTHONPATH to re-execute; flattened equivalents are shipped for reading. Third-party availability is informational and environment-specific.

## 3. Scientific consistency

**31/31 checks passed; 0 failed.**

| Check | Result | Detail |
|---|---|---|
| `canonical_full_macro_dice_matches_val808_table` | PASS | registry 0.8372896860016156 vs table 0.8372896860016156 |
| `canonical_global_macro_dice_matches_val808_table` | PASS | registry 0.8350797177681444 vs table 0.8350797177681444 |
| `canonical_paired_delta_matches_val808_table` | PASS | registry 0.002209968233471182 vs table 0.002209968233471182 |
| `canonical_ci_excludes_zero` | PASS | CI [0.001147693051341143, 0.0032920500180402866] |
| `val808_domain_counts_sum_to_808` | PASS | {'ISIC': 357, 'BUSI': 84, 'KVASIR': 87, 'KUB': 280} |
| `legacy_0_837862_is_rejected` | PASS | 0.837862 adjudicated as a V5/V6/V7 hard-coded reporting inconsistency |
| `legacy_value_absent_from_val808_metrics_table` | PASS | 0.837862 must not appear as a headline metric |
| `full_total_parameters_4837420` | PASS | G 3,523,001 + R_psi 1,276,401 + B_phi 36,801 + S_omega 1,217 = 4,837,420 |
| `v8_verified_total_parameters_matches` | PASS | 4837420 |
| `backbone_parameters_3523001` | PASS | 3523001 |
| `train_manifest_5832` | PASS | 5832 |
| `val_manifest_808` | PASS | 808 |
| `resource_table_isic_split_counts` | PASS | ('2556', '357', '46') |
| `resource_table_kub_split_counts` | PASS | ('1978', '280', '4') |
| `resource_table_has_8_datasets_including_ham10000` | PASS | ['ISIC 2018 Task 1', 'BUSI-WHU V3', 'Kvasir-SEG', 'KUB-StoneX Figshare v1', 'CVC-ClinicDB', 'BrEaST-Lesions-USG', 'Stones_where_are_you (Roboflow COCO-seg v3)', 'HAM10000 (ISIC-2018 Task 3 t |
| `external884_total_analysed` | PASS | 884 |
| `external884_composition_612_252_20` | PASS | 612 CVC + 252 BrEaST + 20 Stones |
| `ham10000_zero_rows_analysed_and_excluded` | PASS | 10015 manifest rows, 0 analysed, HAM10000_EXCLUDED__MASK_PROVENANCE_UNVERIFIED |
| `ham10000_inventory_10015_each` | PASS | (10015, 10015, 10015) |
| `ham10000_full_stem_match` | PASS | 100.0 |
| `ham10000_zero_id_overlap` | PASS | 0 |
| `ham10000_zero_byte_identical_overlap` | PASS | 28 |
| `ham10000_no_saved_full_predictions` | PASS | 0 |
| `ham10000_not_a_completed_benchmark` | PASS | EXTERNAL_SKIN_DATASET_AVAILABLE__SEGMENTATION_EVALUATION_NOT_ESTABLISHED |
| `ham10000_boundaries_respected` | PASS | {'training_performed': False, 'inference_performed': False, 'mask_or_prediction_written': False, 'test_csv_opened': False, 'protected_test1683_pixels_opened': False, 'frozen_evidence_modifie |
| `ham10000_matrix_has_no_fabricated_metrics` | PASS | {'dice': 'NOT_ESTABLISHED', 'iou': 'NOT_ESTABLISHED', 'precision': 'NOT_ESTABLISHED', 'recall': 'NOT_ESTABLISHED', 'hd95_px': 'NOT_ESTABLISHED', 'paired_delta': 'NOT_ESTABLISHED'} |
| `phase28_13_arms_defined_with_metrics` | PASS | 13 definitions / 13 metric rows |
| `phase28_a8_vs_a7_ci_includes_zero` | PASS | mean 1.5717229e-05, CI [-1.4313785e-05, 5.1010811e-05] |
| `phase28_18_historical_training_runs` | PASS | 18 |
| `training_history_has_5_separate_component_histories` | PASS | {'GlobalMedFiLM (G)': 1863, 'R_psi (Regional Refiner)': 6476, 'B_phi (Benefit Router)': 4649, 'S_omega (Post-Safety Gate)': 3407, 'F1 (Ablation Variant)': 284} |
| `no_joint_full_curve_claimed` | PASS | no jointly trained FULL curve exists |

## 4. Publication safety

- Forbidden artifacts / credentials: **0**
- Excluded by policy: Patient_infos_BUSI-WHU.xlsx, quarantined.csv, test.csv; suffixes .bmp, .ckpt, .dcm, .key, .npy, .npz, .pem, .pkl, .pt, .pth
- Absolute local paths disclosed in new docs: 0 (informational)

Local HAM10000 inspection paths are disclosed to the supervisor on purpose; copied frozen manifests retain their original absolute paths as historical provenance.

## 5. ZIP integrity

`SELF_EXCLUDED_BY_CONSTRUCTION` — verified after archive construction; see the out-of-band `Supervisor_Submission_ZIP_INTEGRITY.json`.

## 6. Boundaries

No training, no new inference, no checkpoint modification, no TEST1683 pixel access, no `test.csv` opening, no fabricated mask or prediction, and no modification of frozen source artifacts. All copied artifacts are byte-identical to their repository originals (SHA-256 in `SUBMISSION_MANIFEST.csv`, which by construction does not list itself). The manifest itself is still CRC- and per-member SHA-256-checked by the out-of-band ZIP integrity record.
