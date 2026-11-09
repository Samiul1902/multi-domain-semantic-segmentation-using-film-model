# Repository Map

Where everything lives. Every link below is a real repository-relative path.

> Generated from `full_doc_report/PHASEWISE_NOTEBOOK_COVERAGE.csv` (57 audited
> phase directories). Regenerate with
> `.venv\Scripts\python.exe docs/generate_repository_map.py`.

---

## Map 1 — Project structure

```text
jup/
├── README.md                     entry point (this documentation set)
├── assets/figures/               methodology diagrams (svg/pdf/png)
├── docs/                         repository + methodology + reproducibility docs
├── src/                          library code
│   ├── models/film/              GlobalMedFiLM backbone (G)
│   ├── models/barr/              router, refiner, safety, FULL wrapper
│   ├── models/                   conventional baselines
│   ├── data/                     ROI transforms, datasets
│   ├── metrics/                  Dice / IoU / HD95 implementations
│   └── research/                 C1 / C2 / C3 + pipeline code
├── scripts/training/             training entry points
├── scripts/analysis/             evaluation + report builders
├── notebooks/phasewise/          57 phase directories (research history)
├── manifests/phase4_v3/          TRAIN5832 / VAL808 / TEST1683 splits
├── experiments/                  per-epoch history.csv for 82 runs
├── checkpoints/                  trained weights (git-ignored)
├── reports/                      audits and tables (largely git-ignored)
├── full_doc_report/              verified consolidation: notebooks, tables, figures
└── tests/                        automated tests
```

| Need | Location |
|---|---|
| Full model implementation | [`src/models/barr/ra_medfilm_barr.py`](../src/models/barr/ra_medfilm_barr.py) |
| Backbone implementation | [`src/models/film/global_medfilm.py`](../src/models/film/global_medfilm.py) |
| Verified master notebook | [`full_doc_report/ReMedFiLM_COMPLETE_MASTER_VERIFIED.ipynb`](../full_doc_report/ReMedFiLM_COMPLETE_MASTER_VERIFIED.ipynb) |
| Component registry | [`full_doc_report/REMEDFILM_FULL_COMPONENT_REGISTRY.json`](../full_doc_report/REMEDFILM_FULL_COMPONENT_REGISTRY.json) |
| Method → code trace | [`docs/METHODOLOGY_IMPLEMENTATION_MAP.md`](METHODOLOGY_IMPLEMENTATION_MAP.md) |

---

## Map 2 — Phase-wise notebook index

57 phase directories were audited. Status words are defined in
[`full_doc_report/NOTEBOOK_RECOVERY_AND_RECONSTRUCTION.md`](../full_doc_report/NOTEBOOK_RECOVERY_AND_RECONSTRUCTION.md).

#### Phases 00–10 — governance, data, baselines

| Phase | Directory | Purpose / notebook | Status | Experiment |
|---|---|---|---|---|
| 00 | `phase_00_governance` | [phase00_governance_reproducibility_and_protocol.ipynb](../notebooks/phasewise/phase_00_governance/phase00_governance_reproducibility_and_protocol.ipynb) | notebook present | results saved, run artifacts absent |
| 01 | `phase_01_project_initialization` | [phase01_project_initialization_and_repository_architecture.ipynb](../notebooks/phasewise/phase_01_project_initialization/phase01_project_initialization_and_repository_architecture.ipynb) | notebook present | executed, results saved |
| 02 | `phase_02_environment_cuda` | [phase02_environment_cuda_and_reproducibility_validation.ipynb](../notebooks/phasewise/phase_02_environment_cuda/phase02_environment_cuda_and_reproducibility_validation.ipynb) | notebook present | executed, results saved |
| 03 | `phase_03_dataset_discovery` | [phase03_multidomain_dataset_discovery_and_pairing_integrity.ipynb](../notebooks/phasewise/phase_03_dataset_discovery/phase03_multidomain_dataset_discovery_and_pairing_integrity.ipynb) | notebook present | results saved, run artifacts absent |
| 04 | `phase_04_manifest_splits` | [phase04_canonical_manifest_and_split_integrity.ipynb](../notebooks/phasewise/phase_04_manifest_splits/phase04_canonical_manifest_and_split_integrity.ipynb) | notebook present | results saved, run artifacts absent |
| 05 | `phase_05_leakage_audit` | [phase05_data_leakage_and_duplicate_audit.ipynb](../notebooks/phasewise/phase_05_leakage_audit/phase05_data_leakage_and_duplicate_audit.ipynb) (+3 more) | notebook present | results saved, run artifacts absent |
| 06 | `phase_06_kub_characterization` | [phase06_kub_dataset_characterization_clean_v3.ipynb](../notebooks/phasewise/phase_06_kub_characterization/phase06_kub_dataset_characterization_clean_v3.ipynb) | notebook present | results saved, run artifacts absent |
| 07 | `phase_07_tiny_object_definition` | [phase07_tiny_object_definition_train_only_design.ipynb](../notebooks/phasewise/phase_07_tiny_object_definition/phase07_tiny_object_definition_train_only_design.ipynb) (+1 more) | notebook present | results saved, run artifacts absent |
| 08 | `phase_08_baseline_infrastructure` | [phase08_clean_v3_training_infrastructure_validation.ipynb](../notebooks/phasewise/phase_08_baseline_infrastructure/phase08_clean_v3_training_infrastructure_validation.ipynb) (+1 more) | notebook present | executed, results saved |
| 09 | `phase_09_baseline_training` | [phase09_baseline_models_training_and_validation.ipynb](../notebooks/phasewise/phase_09_baseline_training/phase09_baseline_models_training_and_validation.ipynb) (+1 more) | notebook present | executed, results saved |
| 09 | `phase_09_clean_v3_baseline` | [phase09_clean_v3_baseline_reconstructed.ipynb](../full_doc_report/Reconstructed_Phasewise_Notebooks/phase_09_clean_v3_baseline/phase09_clean_v3_baseline_reconstructed.ipynb) | reconstructed | executed, results saved |
| 10 | `phase_10_baseline_comparison` | [phase10_attention_unet_clean_v3_training_review.ipynb](../notebooks/phasewise/phase_10_baseline_comparison/phase10_attention_unet_clean_v3_training_review.ipynb) (+4 more) | notebook present | executed, results saved |
| 10 | `phase_10_clean_v3_comparison` | [phase10_clean_v3_comparison_reconstructed.ipynb](../full_doc_report/Reconstructed_Phasewise_Notebooks/phase_10_clean_v3_comparison/phase10_clean_v3_comparison_reconstructed.ipynb) | reconstructed | executed, results saved |

#### Phases 11–19 — failure analysis, localisation, refiner precursors

| Phase | Directory | Purpose / notebook | Status | Experiment |
|---|---|---|---|---|
| 11 | `phase_11_failure_analysis` | [phase11_clean_v3_baseline_failure_analysis.ipynb](../notebooks/phasewise/phase_11_failure_analysis/phase11_clean_v3_baseline_failure_analysis.ipynb) (+3 more) | notebook present | executed, results saved |
| 12 | `phase_12_oracle_roi` | [phase12_clean_v3_oracle_regional_analysis.ipynb](../notebooks/phasewise/phase_12_oracle_roi/phase12_clean_v3_oracle_regional_analysis.ipynb) (+3 more) | notebook present | executed, results saved |
| 13 | `phase_13_predicted_roi_localization` | [phase13_clean_v3_best_checkpoint_proposal_analysis.ipynb](../notebooks/phasewise/phase_13_predicted_roi_localization/phase13_clean_v3_best_checkpoint_proposal_analysis.ipynb) (+14 more) | notebook present | executed, results saved |
| 14 | `phase_14_regional_refiner` | [phase14_regional_refiner_pipeline_and_diagnostic_analysis.ipynb](../notebooks/phasewise/phase_14_regional_refiner/phase14_regional_refiner_pipeline_and_diagnostic_analysis.ipynb) (+1 more) | notebook present | executed, results saved |
| POST14 | `post_phase14_h3_proposal_supply` | [01_proposal_root_cause_diagnostic.ipynb](../notebooks/phasewise/post_phase14_h3_proposal_supply/01_proposal_root_cause_diagnostic.ipynb) (+7 more) | notebook present | executed, results saved |
| 15 | `phase_15_loss_study` | [phase15_loss_function_comparison.ipynb](../notebooks/phasewise/phase_15_loss_study/phase15_loss_function_comparison.ipynb) | notebook present | results saved, run artifacts absent |
| 16 | `phase_16_fusion` | [PHASE_INDEX.md](../full_doc_report/Reconstructed_Phasewise_Notebooks/phase_16_fusion/PHASE_INDEX.md) | documentation only | not applicable |
| 17 | `phase_17_kub_regional_ablation` | [PHASE_INDEX.md](../full_doc_report/Reconstructed_Phasewise_Notebooks/phase_17_kub_regional_ablation/PHASE_INDEX.md) | documentation only | not applicable |
| 18 | `phase_18_kub_final_dev_benchmark` | [PHASE_INDEX.md](../full_doc_report/Reconstructed_Phasewise_Notebooks/phase_18_kub_final_dev_benchmark/PHASE_INDEX.md) | documentation only | not applicable |
| 19 | `phase_19_harmonization` | [phase19_multidomain_dataset_harmonization.ipynb](../notebooks/phasewise/phase_19_harmonization/phase19_multidomain_dataset_harmonization.ipynb) | notebook present | results saved, run artifacts absent |

#### Phases 20–24 — multi-domain baselines and the GlobalMedFiLM reference

| Phase | Directory | Purpose / notebook | Status | Experiment |
|---|---|---|---|---|
| 20 | `phase_20_multidomain_baselines` | [phase20_shared_global_unetpp_baseline.ipynb](../notebooks/phasewise/phase_20_multidomain_baselines/phase20_shared_global_unetpp_baseline.ipynb) | notebook present | executed, results saved |
| 20B | `phase_20b_five_model_baselines` | [phase20b_five_model_conventional_baselines.ipynb](../notebooks/phasewise/phase_20b_five_model_baselines/phase20b_five_model_conventional_baselines.ipynb) | notebook present | executed, results saved |
| 21 | `phase_21_global_medfilm` | [phase21_global_medfilm_reference.ipynb](../notebooks/phasewise/phase_21_global_medfilm/phase21_global_medfilm_reference.ipynb) | notebook present | executed, results saved |
| 22 | `phase_22_resource_gap` | [phase22_resource_gap_analysis.ipynb](../notebooks/phasewise/phase_22_resource_gap/phase22_resource_gap_analysis.ipynb) | notebook present | results saved, run artifacts absent |
| 23 | `phase_23_literature_novelty` | [phase23_literature_methodological_novelty_audit.ipynb](../notebooks/phasewise/phase_23_literature_novelty/phase23_literature_methodological_novelty_audit.ipynb) | notebook present | results saved, run artifacts absent |
| 24 | `phase_24_architecture_spec` | [phase24_narrowed_benefit_aware_refinement_spec.ipynb](../notebooks/phasewise/phase_24_architecture_spec/phase24_narrowed_benefit_aware_refinement_spec.ipynb) (+1 more) | notebook present | results saved, run artifacts absent |
| 24 | `phase_24_ra_medfilm_design` | [phase24_architecture_spec_reconstructed.ipynb](../full_doc_report/Reconstructed_Phasewise_Notebooks/phase_24_ra_medfilm_design/phase24_architecture_spec_reconstructed.ipynb) | reconstructed | results saved, run artifacts absent |

#### Phases 25–29 — BARR component development, integration, preservation, ablation, seeds

| Phase | Directory | Purpose / notebook | Status | Experiment |
|---|---|---|---|---|
| 25 | `phase_25_ra_medfilm_dev` | [phase25_component_development_reconstructed.ipynb](../full_doc_report/Reconstructed_Phasewise_Notebooks/phase_25_ra_medfilm_dev/phase25_component_development_reconstructed.ipynb) | reconstructed | executed, results saved |
| 25A | `phase_25a_regional_refiner` | [phase25a_dedicated_regional_refiner.ipynb](../notebooks/phasewise/phase_25a_regional_refiner/phase25a_dedicated_regional_refiner.ipynb) | notebook present | executed, results saved |
| 25B | `phase_25b_gt_free_features` | [phase25b_gt_free_pre_refinement_features.ipynb](../notebooks/phasewise/phase_25b_gt_free_features/phase25b_gt_free_pre_refinement_features.ipynb) | notebook present | executed, results saved |
| 25C | `phase_25c_paired_gain_labels` | [phase25c_oof_paired_refinement_gain.ipynb](../notebooks/phasewise/phase_25c_paired_gain_labels/phase25c_oof_paired_refinement_gain.ipynb) | notebook present | executed, results saved |
| 25D | `phase_25d_benefit_router` | [phase25d_benefit_router.ipynb](../notebooks/phasewise/phase_25d_benefit_router/phase25d_benefit_router.ipynb) | notebook present | executed, results saved |
| 25E | `phase_25e_resource_gate` | [phase25e_resource_gate.ipynb](../notebooks/phasewise/phase_25e_resource_gate/phase25e_resource_gate.ipynb) (+1 more) | notebook present | executed, results saved |
| 25F | `phase_25f_post_safety` | [phase25f_post_safety_execution.ipynb](../notebooks/phasewise/phase_25f_post_safety/phase25f_post_safety_execution.ipynb) | notebook present | executed, results saved |
| 25G | `phase_25g_controlled_validation` | [phase25g_integrated_controlled_evaluation.ipynb](../notebooks/phasewise/phase_25g_controlled_validation/phase25g_integrated_controlled_evaluation.ipynb) | notebook present | executed, results saved |
| 26 | `phase_26_full_four_domain_training` | [phase26_full_system_integration_reconstructed.ipynb](../full_doc_report/Reconstructed_Phasewise_Notebooks/phase_26_full_four_domain_training/phase26_full_system_integration_reconstructed.ipynb) | reconstructed | results saved, run artifacts absent |
| 26 | `phase_26_full_system_integration` | [phase26_canonical_integration_and_bundle_freeze.ipynb](../notebooks/phasewise/phase_26_full_system_integration/phase26_canonical_integration_and_bundle_freeze.ipynb) | notebook present | results saved, run artifacts absent |
| 27 | `phase_27_preservation` | [phase27_multidomain_preservation_audit.ipynb](../notebooks/phasewise/phase_27_preservation/phase27_multidomain_preservation_audit.ipynb) | notebook present | results saved, run artifacts absent |
| 28 | `phase_28_model_ablation` | [phase28_comprehensive_ablation.ipynb](../notebooks/phasewise/phase_28_model_ablation/phase28_comprehensive_ablation.ipynb) | notebook present | executed, results saved |
| 29 | `phase_29_3seed_reproducibility` | [phase29_phase_d_canonical_three_seed_validation.ipynb](../notebooks/phasewise/phase_29_3seed_reproducibility/phase29_phase_d_canonical_three_seed_validation.ipynb) | notebook present | executed, results saved |

#### Phases 30–36 — final development validation through robustness

| Phase | Directory | Purpose / notebook | Status | Experiment |
|---|---|---|---|---|
| 30 | `phase_30_final_dev_val` | [phase30_holdout_validation_reconstructed.ipynb](../full_doc_report/Reconstructed_Phasewise_Notebooks/phase_30_final_dev_val/phase30_holdout_validation_reconstructed.ipynb) | reconstructed | results saved, run artifacts absent |
| 30 | `phase_30_final_validation` | [phase30_final_development_validation.ipynb](../notebooks/phasewise/phase_30_final_validation/phase30_final_development_validation.ipynb) | notebook present | results saved, run artifacts absent |
| 31 | `phase_31_statistical_significance` | [phase31_statistical_significance_review.ipynb](../notebooks/phasewise/phase_31_statistical_significance/phase31_statistical_significance_review.ipynb) | notebook present | results saved, run artifacts absent |
| 32 | `phase_32_external_validation` | [phase32_external_domain_shift_review.ipynb](../notebooks/phasewise/phase_32_external_validation/phase32_external_domain_shift_review.ipynb) | notebook present | results saved, run artifacts absent |
| 33 | `phase_33_final_failure_analysis` | [phase33_failure_boundary_spec_review.ipynb](../notebooks/phasewise/phase_33_final_failure_analysis/phase33_failure_boundary_spec_review.ipynb) (+2 more) | notebook present | results saved, run artifacts absent |
| 34 | `phase_34_efficiency_profiling` | [phase34_efficiency_profiling_execution_v1_3_review.ipynb](../notebooks/phasewise/phase_34_efficiency_profiling/phase34_efficiency_profiling_execution_v1_3_review.ipynb) (+7 more) | notebook present | results saved, run artifacts absent |
| 35 | `phase_35_interpretability` | [phase35_empty_mask_actual_logits_repair_v1_0f_review.ipynb](../notebooks/phasewise/phase_35_interpretability/phase35_empty_mask_actual_logits_repair_v1_0f_review.ipynb) (+13 more) | notebook present | results saved, run artifacts absent |
| 36 | `phase_36_robustness` | [phase36_synthetic_full_pipeline_smoke_v1_1_review.ipynb](../notebooks/phasewise/phase_36_robustness/phase36_synthetic_full_pipeline_smoke_v1_1_review.ipynb) | notebook present | results saved, run artifacts absent |
| 36 | `phase_36_robustness_perturbation` | [phase36_robustness_perturbation_reconstructed.ipynb](../full_doc_report/Reconstructed_Phasewise_Notebooks/phase_36_robustness_perturbation/phase36_robustness_perturbation_reconstructed.ipynb) | reconstructed | results saved, run artifacts absent |

#### Phases 37–40 — evidence consolidation, protocol freeze, TEST, manuscript

| Phase | Directory | Purpose / notebook | Status | Experiment |
|---|---|---|---|---|
| 37 | `phase_37_evidence_consolidation` | [phase37_evidence_consolidation_review.ipynb](../notebooks/phasewise/phase_37_evidence_consolidation/phase37_evidence_consolidation_review.ipynb) | notebook present | results saved, run artifacts absent |
| 38 | `phase_38_protocol_freeze` | [phase38_manuscript_protocol_checkpoint_freeze_review.ipynb](../notebooks/phasewise/phase_38_protocol_freeze/phase38_manuscript_protocol_checkpoint_freeze_review.ipynb) | notebook present | results saved, run artifacts absent |
| 39 | `phase_39_untouched_test_evaluation` | [PHASE_INDEX.md](../full_doc_report/Reconstructed_Phasewise_Notebooks/phase_39_untouched_test_evaluation/PHASE_INDEX.md) | gated (TEST consumed) | gated, one-shot consumed |
| 40 | `phase_40_manuscript_assembly` | [phase40_manuscript_assembly_review.ipynb](../notebooks/phasewise/phase_40_manuscript_assembly/phase40_manuscript_assembly_review.ipynb) | notebook present | results saved, run artifacts absent |
| 40 | `phase_40_publication_reproducibility_audit` | [phase40_reproducibility_audit_reconstructed.ipynb](../full_doc_report/Reconstructed_Phasewise_Notebooks/phase_40_publication_reproducibility_audit/phase40_reproducibility_audit_reconstructed.ipynb) | reconstructed | results saved, run artifacts absent |

#### Post-phase and extension directories

| Phase | Directory | Purpose / notebook | Status | Experiment |
|---|---|---|---|---|
| POST14 | `post_phase14_h3_proposal_supply` | [01_proposal_root_cause_diagnostic.ipynb](../notebooks/phasewise/post_phase14_h3_proposal_supply/01_proposal_root_cause_diagnostic.ipynb) (+7 more) | notebook present | executed, results saved |

---

## Map 3 — Model and checkpoint locations

| Component | Code | Weights |
|---|---|---|
| **G** GlobalMedFiLM | [`src/models/film/global_medfilm.py`](../src/models/film/global_medfilm.py) | `checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt` |
| **R_psi** Regional Refiner | [`src/models/barr/regional_refiner.py`](../src/models/barr/regional_refiner.py) | `checkpoints/phase25a_barr_regional_refiner_v1_1_roi030/final/final.pt` |
| **B_phi** Benefit Router | [`src/models/barr/phase25_models.py`](../src/models/barr/phase25_models.py) | `checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt` |
| **S_omega** Post-Safety Gate | [`src/models/barr/phase25_models.py`](../src/models/barr/phase25_models.py) | `checkpoints/phase25f_barr_post_safety_v1_0_seed42/final/final.pt` |
| **FULL** assembly | [`src/models/barr/ra_medfilm_barr.py`](../src/models/barr/ra_medfilm_barr.py) | bundle of the four above |

**Weights are not distributed with this repository.** `checkpoints/` and
`*.pt` are excluded by `.gitignore`. The registry records each checkpoint's
SHA-256 so a holder of the weights can verify identity:
[`REMEDFILM_FULL_COMPONENT_REGISTRY.json`](../full_doc_report/REMEDFILM_FULL_COMPONENT_REGISTRY.json).

| Registry field | Location |
|---|---|
| Component inventory (frozen, contains a units defect — see note) | [`reports/tables/phase26_component_inventory.csv`](../reports/tables/phase26_component_inventory.csv) |
| Corrected parameter table | [`full_doc_report/tables/REMEDFILM_COMPONENT_PARAMETERS.csv`](../full_doc_report/tables/REMEDFILM_COMPONENT_PARAMETERS.csv) |
| Backbone training closure | `experiments/phase21_global_medfilm_fourdomain_seed42_clean_v3/closure.json` |

> The frozen `phase26_component_inventory.csv` stores **MACs** in G's
> `parameters` column (31,551,740,928 instead of 3,523,001). Do not sum that
> column. The corrected derived table is authoritative.

---

## Map 4 — Training and validation

| Need | Location |
|---|---|
| Training entry points | [`scripts/training/`](../scripts/training/) |
| Backbone training script | [`scripts/training/train_phase21_global_medfilm.py`](../scripts/training/train_phase21_global_medfilm.py) |
| Optimizer / scheduler config | inside each `closure.json` / `run.json` under `experiments/` |
| Per-epoch histories (82 runs) | `experiments/**/history.csv` |
| Long-form epoch table | [`full_doc_report/tables/REMEDFILM_EPOCH_HISTORY.csv`](../full_doc_report/tables/REMEDFILM_EPOCH_HISTORY.csv) |
| Run registry (best epoch, status) | [`full_doc_report/tables/TRAINING_RUN_REGISTRY.csv`](../full_doc_report/tables/TRAINING_RUN_REGISTRY.csv) |
| Component-only epoch history | [`full_doc_report/REMEDFILM_COMPONENT_TRAINING_HISTORY.csv`](../full_doc_report/REMEDFILM_COMPONENT_TRAINING_HISTORY.csv) |
| Internal evaluation | [`full_doc_report/REMEDFILM_FULL_VAL808_METRICS.csv`](../full_doc_report/REMEDFILM_FULL_VAL808_METRICS.csv) |
| Per-sample internal scores | [`full_doc_report/tables/REMEDFILM_INTERNAL_PER_SAMPLE.csv`](../full_doc_report/tables/REMEDFILM_INTERNAL_PER_SAMPLE.csv) |
| Data splits | [`manifests/phase4_v3/`](../manifests/phase4_v3/) |

---

## Map 5 — Scientific results

| Result | Notebook | Table / figure |
|---|---|---|
| Six-model baseline comparison | §06 master | `full_doc_report/tables/REMEDFILM_MODEL_COMPARISON.csv` |
| FULL ReMedFiLM validation | §07 master | [`REMEDFILM_FULL_VAL808_METRICS.csv`](../full_doc_report/REMEDFILM_FULL_VAL808_METRICS.csv) |
| Per-domain metrics figure | §07 master | [`figures/Internal validation/`](../full_doc_report/figures/Internal%20validation/) |
| Subgroup (KUB) evaluation | §09 master | `full_doc_report/figures/Internal validation/SG*.png` |
| Segmentation galleries | §08 master | [`figures/Semantic segmentation/`](../full_doc_report/figures/Semantic%20segmentation/) |
| External evaluation (884 cases) | §10 master | [`REMEDFILM_FULL_EXTERNAL_METRICS.csv`](../full_doc_report/REMEDFILM_FULL_EXTERNAL_METRICS.csv) |
| 13-arm ablation | §12 master | [`REMEDFILM_ABLATION_AND_PROGRESSION.csv`](../full_doc_report/REMEDFILM_ABLATION_AND_PROGRESSION.csv) |
| Component progression | §11 master | [`figures/Progression/`](../full_doc_report/figures/Progression/) |
| Routing and safety | §13 master | [`figures/Routing and safety/`](../full_doc_report/figures/Routing%20and%20safety/) |
| Statistics / reproducibility | §14 master | [`figures/Statistics/`](../full_doc_report/figures/Statistics/) |
| Robustness | §15 master | [`figures/Robustness/`](../full_doc_report/figures/Robustness/) |
| Efficiency | §16 master | [`figures/Efficiency/`](../full_doc_report/figures/Efficiency/) |
| Historical TEST summary | §17 master | `reports/audits/phase39_final_test_v1_2_scientific_result.json` |

Result reconciliation (0.837290 vs 0.837862):
[`REMEDFILM_FULL_RESULT_RECONCILIATION.md`](../full_doc_report/REMEDFILM_FULL_RESULT_RECONCILIATION.md).

---

## Map 6 — Documentation and reproduction

| Need | Location |
|---|---|
| Environment setup | [`docs/REPRODUCIBILITY_GUIDE.md`](REPRODUCIBILITY_GUIDE.md) |
| Method → code trace | [`docs/METHODOLOGY_IMPLEMENTATION_MAP.md`](METHODOLOGY_IMPLEMENTATION_MAP.md) |
| Tests | [`tests/`](../tests/) |
| Safe analysis runner | [`full_doc_report/Scripts/execute_notebooks.py`](../full_doc_report/Scripts/execute_notebooks.py) |
| Figure regeneration | [`full_doc_report/Scripts/build_figures.py`](../full_doc_report/Scripts/build_figures.py) |
| Methodology figure source | [`assets/figures/generate_methodology.py`](../assets/figures/generate_methodology.py) |
| Verification suites | [`full_doc_report/Scripts/verify_verified.py`](../full_doc_report/Scripts/verify_verified.py) |
| Scientific QA record | [`REMEDFILM_FINAL_SCIENTIFIC_QA.md`](../full_doc_report/REMEDFILM_FINAL_SCIENTIFIC_QA.md) |
| Pending experiments | [`PENDING_CONTROLLED_EXPERIMENTS.md`](../full_doc_report/PENDING_CONTROLLED_EXPERIMENTS.md) |
