# Notebooks Root Directory Cleanup & Provenance Audit

- **Total Cataloged Items in `notebooks/`:** 23
- **Generated At:** 2026-09-19
- **Preservation Principle:** No scientific notebooks or figures are deleted. Legacy notebooks are preserved as scientific provenance.

## 1. Classification Summary

- **KEEP_PROVENANCE:** 17
- **KEEP_REVIEWER:** 4
- **KEEP_CANONICAL:** 1
- **SAFE_ARCHIVE_CANDIDATE:** 1

## 2. Immediate Directory Items Audit Table

| Name | Type | Phase | Action | Canonical Status | Phasewise Exists | Reason |
| :--- | :---: | :---: | :--- | :--- | :---: | :--- |
| `00_project_initialization.ipynb` | FILE | 01 | **KEEP_PROVENANCE** | PROVENANCE_ORIGINAL | YES (phase_01) | Original foundational initialization notebook from Phase 01 development. |
| `00_project_visual_index.ipynb` | FILE | PROJECT_WIDE | **KEEP_REVIEWER** | REVIEWER_INDEX_LEGACY | YES (00_PHASEWISE_PROJECT_INDEX.ipynb) | Executed top-level project visual navigation index from NV-2. |
| `01_environment_and_data_audit.ipynb` | FILE | 02 | **KEEP_PROVENANCE** | PROVENANCE_ORIGINAL | PENDING (phase_02) | Original Phase 02 CUDA and environment certification notebook. |
| `01_trained_model_results_visual_scorecard.ipynb` | FILE | PROJECT_WIDE | **KEEP_REVIEWER** | REVIEWER_SCORECARD_LEGACY | NO | Executed trained model visual scorecard across all historical phases. |
| `02_dataset_discovery.ipynb` | FILE | 03 | **KEEP_PROVENANCE** | PROVENANCE_ORIGINAL | PENDING (phase_03) | Original Phase 03 dataset discovery and multi-domain inventory notebook. |
| `03_kub_forensic_audit.ipynb` | FILE | 05 | **KEEP_PROVENANCE** | PROVENANCE_ORIGINAL | PENDING (phase_05) | Original Phase 05 KUB forensic duplicate and leakage audit notebook. |
| `03_leakage_and_split_audit.ipynb` | FILE | 04 | **KEEP_PROVENANCE** | PROVENANCE_ORIGINAL | PENDING (phase_04) | Original Phase 04 split manifest and patient leakage audit notebook. |
| `04_kub_characterization.ipynb` | FILE | 06 | **KEEP_PROVENANCE** | PROVENANCE_ORIGINAL | PENDING (phase_06) | Original Phase 06 KUB clinical and FOV characterization notebook. |
| `05_kub_object_size_taxonomy.ipynb` | FILE | 07 | **KEEP_PROVENANCE** | PROVENANCE_ORIGINAL | PENDING (phase_07) | Original Phase 07 stone object size taxonomy and quartiles notebook. |
| `06_kub_baseline_infrastructure.ipynb` | FILE | 08 | **KEEP_PROVENANCE** | PROVENANCE_ORIGINAL | PENDING (phase_08) | Original Phase 08 baseline model factory and smoke-test harness notebook. |
| `07_kub_unet_baseline_training.ipynb` | FILE | 09 | **KEEP_PROVENANCE** | PROVENANCE_ORIGINAL | YES (phase_09) | Original Phase 09 U-Net baseline training and validation notebook. |
| `08_kub_baseline_comparison.ipynb` | FILE | 10 | **KEEP_PROVENANCE** | PROVENANCE_ORIGINAL | YES (phase_10) | Original Phase 10 baseline comparison (UNet vs UNet++ vs SegNet) notebook. |
| `09_kub_failure_analysis.ipynb` | FILE | 11 | **KEEP_PROVENANCE** | PROVENANCE_ORIGINAL | YES (phase_11) | Original Phase 11 KUB baseline failure analysis notebook. |
| `09b_kub_manual_prediction_demo.ipynb` | FILE | 11 | **KEEP_PROVENANCE** | PROVENANCE_DEMO | NO | Phase 11 manual prediction demonstration on baseline models. |
| `10_kub_oracle_roi_upper_bound.ipynb` | FILE | 12 | **KEEP_PROVENANCE** | PROVENANCE_ORIGINAL | YES (phase_12) | Original Phase 12 Oracle ROI upper bound analysis notebook. |
| `11_kub_predicted_roi_localizer.ipynb` | FILE | 13 | **KEEP_PROVENANCE** | PROVENANCE_ORIGINAL | YES (phase_13) | Original Phase 13 predicted ROI localizer exploration notebook. |
| `11b_kub_learned_localizer.ipynb` | FILE | 13 | **KEEP_PROVENANCE** | PROVENANCE_EXPLORATORY | YES (phase_13) | Phase 13 learned localizer (CenterNet pilot) intermediate notebook. |
| `11c_kub_final_localizer_redesign.ipynb` | FILE | 13 | **KEEP_PROVENANCE** | PROVENANCE_STAGE4D | YES (phase_13) | Phase 13 Stage 4D final localizer redesign and tuning notebook. |
| `12_phase14_15_gate_closure.ipynb` | FILE | 14/15 | **KEEP_PROVENANCE** | PROVENANCE_GATE | NO | Historical Phase 14/15 closure gate audit and transition notebook. |
| `13_phase14_regional_refiner_diagnostic.ipynb` | FILE | 14 | **KEEP_CANONICAL** | CANONICAL_FROZEN | YES (phase_14) | Authoritative frozen Phase 14 regional refiner diagnostic provenance notebook. |
| `phasewise` | DIR | PHASES_00_TO_40 | **KEEP_REVIEWER** | REVIEWER_PRIMARY_LAYER | N/A (IS_PHASEWISE) | Authoritative 41-phase reviewer navigation tree and executed companion notebooks. |
| `reports` | DIR | ARTIFACT_OUTPUTS | **SAFE_ARCHIVE_CANDIDATE** | REDUNDANT_OUTPUT_DIR | N/A | Contains duplicate generated figure outputs created during earlier notebook executions; retain as archive candidate. |
| `retrospective` | DIR | PHASES_09_10 | **KEEP_REVIEWER** | REVIEWER_COMPANION | YES (phase_09, phase_10) | Executed visual companion notebook for baseline models from NV-2. |