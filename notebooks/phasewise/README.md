# Phase-Wise Reviewer Navigation Tree (RA-MedFiLM-Seg++)

This directory contains the authoritative **Reviewer-Facing / Publication Navigation Layer** for the RA-MedFiLM-Seg++ medical image segmentation research project, structured across the full 41-phase canonical research roadmap (Phase 00 through Phase 40).

## 1. Architectural Principles
- **Canonical Provenance Immutability:** Historical canonical notebooks (e.g., `notebooks/13_phase14_regional_refiner_diagnostic.ipynb`, SHA `b5b329d1...`) represent frozen scientific provenance and remain strictly immutable.
- **Reviewer-Facing Accessibility:** Reviewers can inspect and execute notebooks in this directory to verify the complete scientific progression:
  1. What data went into each stage.
  2. What intermediate representations were generated.
  3. What predictions emerged.
  4. How they compared against ground truth (standardized TP/FP/FN error maps).
  5. What the quantitative scores were.
  6. Where and why methods failed.
  7. Why subsequent phases were required.
- **Strict Governance:** All visual predictions use the permitted validation cohort (`VAL`) or training samples. The test set (`TEST`) is locked (`TEST reads = 0`, `TEST visualizations = 0`).
- **Standard Qualitative Coverage:** Every modeling phase provides $\ge 12$ deterministic sample visualizations per dataset and $\ge 16$ deterministic case predictions.

---

## 2. Canonical 41-Phase Roadmap Navigation

| Phase Folder | Phase Name | Scientific Scope | Current Status |
| :--- | :--- | :--- | :--- |
| [`phase_00_governance/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_00_governance/README.md) | Governance & Scientific Protocols | Protocol verification, test locking, reproducibility audits | COMPLETE |
| [`phase_01_project_initialization/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_01_project_initialization/README.md) | Project Initialization & Architecture | Canonical project layout, paths, and coding standards | COMPLETE |
| [`phase_02_environment_cuda/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_02_environment_cuda/README.md) | Environment & CUDA Verification | Hardware certification, CUDA driver, PyTorch determinism | COMPLETE |
| [`phase_03_dataset_discovery/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_03_dataset_discovery/README.md) | Dataset Discovery & Multi-Domain Cataloging | Raw dataset cataloging across KUB, ISIC, BUSI, Kvasir | COMPLETE |
| [`phase_04_manifest_splits/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_04_manifest_splits/README.md) | Patient-Aware Manifest & Data Splits | Patient-leakage-free train/val/test splits | COMPLETE |
| [`phase_05_leakage_audit/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_05_leakage_audit/README.md) | Forensic Data & Image Leakage Audit | Zero pHash duplicate verification, patient separation | COMPLETE |
| [`phase_06_kub_characterization/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_06_kub_characterization/README.md) | KUB Clinical & Anatomical Characterization | FOV types, stone locations, radiopacity distributions | COMPLETE |
| [`phase_07_tiny_object_definition/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_07_tiny_object_definition/README.md) | Tiny Object Definition & Stratification | Tiny (<32px), small, medium, large stone quartiles | COMPLETE |
| [`phase_08_baseline_infrastructure/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_08_baseline_infrastructure/README.md) | Baseline Infrastructure & Model Factories | Model builders, loss functions, and smoke test harness | COMPLETE |
| [`phase_09_baseline_training/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_09_baseline_training/README.md) | Global Baseline Model Training (U-Net) | Foundational full-field U-Net performance on KUB | COMPLETE |
| [`phase_10_baseline_comparison/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_10_baseline_comparison/README.md) | Baseline Comparison (UNet vs UNet++ vs SegNet) | Benchmark standard architectures showing UNet++ lead | COMPLETE |
| [`phase_11_failure_analysis/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_11_failure_analysis/README.md) | Baseline Failure Analysis & Error Modes | False negative patterns and tiny-stone miss rates | COMPLETE |
| [`phase_12_oracle_roi/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_12_oracle_roi/README.md) | Oracle ROI Upper Bound Analysis | +16.2% Dice & 100% tiny recall with perfect GT boxes | COMPLETE |
| [`phase_13_predicted_roi_localization/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_13_predicted_roi_localization/README.md) | GT-Free Proposal Localization (Stage 4D) | CenterNet localizer proposing ROIs with zero GT at test | COMPLETE |
| [`phase_14_regional_refiner/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_14_regional_refiner/README.md) | Regional Refiner Diagnostic Evaluation | Localizer + refiner pipeline; FP clutter diagnostic | COMPLETE (DIAGNOSTIC) |
| [`phase_15_loss_study/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_15_loss_study/README.md) | Regional Refiner Segmentation Loss Study | Asymmetric loss functions (L0, L1, L2, L3) to suppress FP | CURRENT (PROTOCOL FROZEN) |
| [`phase_16_fusion/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_16_fusion/README.md) | Regional-Global Mask Fusion | Intelligent fusion between global baseline & regional refiner | NOT_STARTED |
| [`phase_17_kub_regional_ablation/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_17_kub_regional_ablation/README.md) | KUB Regional Pipeline Comprehensive Ablation | End-to-end ablation of proposals, resolution, and loss | NOT_STARTED |
| [`phase_18_kub_final_dev_benchmark/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_18_kub_final_dev_benchmark/README.md) | KUB Final Development Validation Benchmark | Benchmark finalized KUB regional pipeline on VAL | NOT_STARTED |
| [`phase_19_harmonization/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_19_harmonization/README.md) | Multi-Domain Harmonization | Standardize ISIC, BUSI, Kvasir, KUB task encodings | NOT_STARTED |
| [`phase_20_multidomain_baselines/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_20_multidomain_baselines/README.md) | Multi-Domain Global Baseline Evaluation | Evaluate global baselines across all 4 modalities | NOT_STARTED |
| [`phase_21_global_medfilm/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_21_global_medfilm/README.md) | Global MedFiLM Reference Architecture | Unified feature-interleaved multi-domain backbone | NOT_STARTED |
| [`phase_22_gap_analysis/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_22_gap_analysis/README.md) | Multi-Domain Gap Analysis | Diagnose scale and domain transfer weaknesses | NOT_STARTED |
| [`phase_23_literature_novelty/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_23_literature_novelty/README.md) | Literature & Methodological Novelty | Formalize theoretical contributions & survey positioning | NOT_STARTED |
| [`phase_24_ra_medfilm_design/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_24_ra_medfilm_design/README.md) | RA-MedFiLM Architectural Specification | Specify Regional Scale-Aware MedFiLM framework | NOT_STARTED |
| [`phase_25_ra_medfilm_dev/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_25_ra_medfilm_dev/README.md) | RA-MedFiLM Controlled Module Development | Implement regional attention, scale routing modules | NOT_STARTED |
| [`phase_26_full_four_domain_training/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_26_full_four_domain_training/README.md) | Full Four-Domain Joint Architecture Training | Joint multi-task training across all 4 domains on TRAIN | NOT_STARTED |
| [`phase_27_preservation/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_27_preservation/README.md) | Multi-Domain Preservation Audit | Audit that refinement does not degrade global domains | NOT_STARTED |
| [`phase_28_model_ablation/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_28_model_ablation/README.md) | Comprehensive System Ablation Matrix | Component ablations (attention, loss, fusion, scale) | NOT_STARTED |
| [`phase_29_3seed_reproducibility/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_29_3seed_reproducibility/README.md) | Three-Seed Deterministic Reproducibility | Stability & variance audit across 3 frozen random seeds | NOT_STARTED |
| [`phase_30_final_dev_val/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_30_final_dev_val/README.md) | Final Development Validation Benchmark | Final multi-domain validation before protocol freeze | NOT_STARTED |
| [`phase_31_statistical_significance/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_31_statistical_significance/README.md) | Statistical Significance & Hypothesis Testing | Paired Wilcoxon, bootstrap 95% CIs, Cohen effect sizes | NOT_STARTED |
| [`phase_32_external_validation/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_32_external_validation/README.md) | External Dataset & Domain Shift Evaluation | Out-of-distribution evaluation on external cohorts | NOT_STARTED |
| [`phase_33_final_failure_analysis/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_33_final_failure_analysis/README.md) | Final System Failure & Boundary Error Analysis | Exhaustive qualitative & quantitative failure modes | NOT_STARTED |
| [`phase_34_efficiency_profiling/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_34_efficiency_profiling/README.md) | Computational Efficiency & Runtime Profiling | FLOPs, parameter count, FPS latency, memory footprint | NOT_STARTED |
| [`phase_35_interpretability/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_35_interpretability/README.md) | Feature Attribution & Visual Saliency | Grad-CAM and regional attention saliency visualizations | NOT_STARTED |
| [`phase_36_robustness_perturbation/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_36_robustness_perturbation/README.md) | Robustness & Image Perturbation Analysis | Noise, contrast reduction, blur, resolution robustness | NOT_STARTED |
| [`phase_37_evidence_consolidation/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_37_evidence_consolidation/README.md) | Visual & Tabular Evidence Consolidation | Compile all manuscript figures, galleries, and tables | NOT_STARTED |
| [`phase_38_protocol_freeze/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_38_protocol_freeze/README.md) | Manuscript Protocol & Checkpoint Freeze | Irreversible hashing of models and code prior to test | NOT_STARTED |
| [`phase_39_untouched_test_evaluation/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_39_untouched_test_evaluation/README.md) | Final Untouched Test Cohort Evaluation | Strictly single-pass inference on locked test split | NOT_STARTED |
| [`phase_40_publication_reproducibility_audit/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_40_publication_reproducibility_audit/README.md) | Publication Package & Reproducibility Audit | Package artifacts and code for Q1/A* peer review | NOT_STARTED |
