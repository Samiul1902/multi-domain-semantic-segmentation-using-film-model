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
| [`phase_15_loss_study/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_15_loss_study/README.md) | Regional Refiner Segmentation Loss Study | Asymmetric loss functions (L0, L1, L2, L3) to suppress FP | DEFERRED_CONDITIONAL__NOT_EXECUTED (protocol frozen; post-H3 insufficiency) |
| [`phase_16_fusion/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_16_fusion/README.md) | Regional-Global Mask Fusion | Intelligent fusion between global baseline & regional refiner | DEFERRED_CONDITIONAL__NOT_EXECUTED |
| [`phase_17_kub_regional_ablation/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_17_kub_regional_ablation/README.md) | KUB Regional Pipeline Comprehensive Ablation | End-to-end ablation of proposals, resolution, and loss | DEFERRED_CONDITIONAL__NOT_EXECUTED |
| [`phase_18_kub_final_dev_benchmark/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_18_kub_final_dev_benchmark/README.md) | KUB Final Development Validation Benchmark | Benchmark finalized KUB regional pipeline on VAL | DEFERRED_CONDITIONAL__NOT_EXECUTED |
| [`phase_19_harmonization/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_19_harmonization/README.md) | Multi-Domain Dataset Harmonization | Standardize ISIC, BUSI, Kvasir, KUB under one leakage-safe task/data contract | **COMPLETE** |
| [`phase_20_multidomain_baselines/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_20_multidomain_baselines/README.md) | Shared Four-Domain Global Baseline | Single frozen UNet++ shared across ISIC/BUSI/Kvasir/KUB (no FiLM, no regional module) | **COMPLETE** |
| [`phase_20b_five_model_baselines/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_20b_five_model_baselines/README.md) | Five-Model Conventional Baseline Benchmark (20B) | U-Net · Attention U-Net · UNet++ · DeepLabV3+ · Transformer/MiT-style U-Net under one frozen protocol | **COMPLETE** (reviewer package + full visual evidence) |
| [`phase_21_global_medfilm/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_21_global_medfilm/README.md) | Global MedFiLM Reference Architecture | Unified feature-interleaved multi-domain backbone | **ELIGIBLE / NOT STARTED** (authorization required) |
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

---

## Evaluation / visualization synchronization

A project-wide evaluation-metrics audit (terminal state
`PROJECT_EVALUATION_METRICS_AUDIT_COMPLETE__H3_ADJUDICATION_PENDING`) produced reusable
descriptive metrics, confusion matrices, per-image / per-component tables, confidence
intervals, boundary metrics, calibration metrics, proposal metrics and figures. These
have now been synchronized into the completed phasewise notebooks.

**No new inference was run.** Every added value is read from already-saved artifacts;
notebook-only plotting from saved tables is used where a central figure mixed arms that
are not all relevant to a phase.

### What was synchronized

| Phase | Confusion matrix | Advanced metrics | Proposal / FROC | Visual evidence |
| :--- | :--- | :--- | :--- | :--- |
| Phase 09 (UNet) | UNAVAILABLE_FROM_SAVED_ARTIFACTS | Dice/IoU/precision/recall + training curves | NA | gallery |
| Phase 10 (4-model) | YES (UNet++ = GLOBAL arm only) | Dice/IoU/precision/recall/specificity/MCC/HD95/ASSD/surface Dice/Brier/ECE + CIs | NA | per-model Dice boxplot |
| Phase 11 (failure) | NO (component focus) | size-stratified recall, HD95, FP/FN | NA | failure dashboards |
| Phase 12 (oracle) | YES (GLOBAL + ORACLE) | full pixel/boundary/calibration + paired Dice | NA (GT-derived) | confusion + paired benefit |
| Phase 13 (localizer) | NA (no TN unit) | proposal precision, component recall, box IoU | PR + FROC (Phase-13B) | proposal gallery |
| Phase 14 (refiner) | YES (3 modes) | pixel/boundary/calibration + paired Dice | proposal burden | diagnostic figures |
| H3-01 / H3-02 | NA | proposal / component diagnostics | UNAVAILABLE (degenerate) | component outcome chart |
| H3-04 (training) | NA | training / optimization curves only | NA | loss + recall curves |
| H3-05 (supply) | NA | supply coverage by size | UNAVAILABLE (degenerate sentinel) | coverage-by-size |
| H3-06 (downstream) | YES | pixel/boundary/calibration + paired Dice | NA | confusion + paired diff |

### Metric-availability conventions

- `YES` — present and model-identity-matched.
- `NA` — not applicable by task design (e.g. no TN unit for proposal detection).
- `UNAVAILABLE_FROM_SAVED_ARTIFACTS` — the value was never persisted and may not be
  produced without new inference, which is forbidden here.
- `NO` — deliberately not added (e.g. pixel confusion is not duplicated into the
  component-focused failure-analysis notebook).

### Which metrics are NA by task design

- Proposal/localizer notebooks (Phase 13, H3-01, H3-02, H3-05): **no TN-based confusion
  matrix** — background is unbounded, so a defensible negative unit does not exist.
- H3 supply PR/FROC curves: **NA_DEGENERATE_SENTINEL_SCORE** — the persisted
  `best_proposal_score` uses a `-1.0` sentinel and is perfectly separable by construction.

### Which evidence is unavailable

- Pixel confusion / boundary / calibration for any model that is **not** one of the four
  central safe-replay arms (GLOBAL = Phase-10 UNet++, ORACLE_REGIONAL,
  PREDICTED_REGIONAL, H3_DOWNSTREAM). In particular the Phase-09 UNet has no persisted
  per-pixel maps, so those families are `UNAVAILABLE_FROM_SAVED_ARTIFACTS` there.

### Coverage matrix

`reports/tables/phasewise_evaluation_visualization_coverage.csv`
SHA-256 `d81823d26a3cf87a89ea44c2934a74533d1812545588013fb4dde1615802cac3`

### Provenance

`reports/audits/phasewise_evaluation_visualization_sha_updates.json`
records old/new SHA-256 for every modified notebook, with
`inference_performed=false`, `training_performed=false`, `frozen_metrics_changed=false`.

### Governance

- No training. No inference. No TEST access (TEST reads = 0, external TEST reads = 0).
- Thresholds, checkpoints and frozen scientific gates are unchanged.
- H3 formal adjudication remains **PENDING** (`H3_DOWNSTREAM_EVALUATION_COMPLETE__FORMAL_ADJUDICATION_PENDING`);
  Notebook 07 was not created.
- Phase 15 remains `NOT_STARTED_AND_NOT_AUTHORIZED`.

---

## Future modeling-phase evaluation acceptance template

Every FUTURE modeling / evaluation phase notebook must, **as applicable**, include the
following before it can be accepted. This is a requirement template — it is not data,
and it must never be populated with fabricated values.

1. Complete training curves (loss, task metric, learning rate, epoch timing).
2. Aggregate metrics (pooled and macro).
3. Per-case (per-image) metric tables.
4. Confusion matrix for segmentation / classification tasks (raw + row-normalized).
5. Proposal TP / FP / FN for localization tasks (no TN-based matrix).
6. Component / object recall (size-stratified where relevant).
7. Dice / IoU.
8. Precision / recall / specificity / MCC.
9. Boundary metrics (HD95 / ASSD / surface Dice) with declared units.
10. Uncertainty (bootstrap CIs) and, where compared, paired tests + effect size.
11. Success examples and failure examples (never success-only).
12. Saved figures written to `reports/figures/`.
13. Executed notebook outputs (monotonic execution counts, zero tracebacks).
14. Recorded SHA-256 for the notebook and its source artifacts.
15. TEST leakage = 0 (TEST reads and TEST visualizations both zero).

## Phase-15 protocol vs execution

Phase 15 exists as a FROZEN PROTOCOL / DESIGN only. Phase-15 clean-v3 scientific EXECUTION and TRAINING remain NOT_STARTED_AND_NOT_AUTHORIZED. The two must not be conflated: a frozen protocol is not an executed phase.

Phase 15 is a **separate phase** from the post-Phase14 H3 gate-resolution branch and is not renumbered.

## Stage-B activation (post-H3 supervisor decision)

The post-Phase14 / H3 target-support branch is **CLOSED** with the frozen scientific label
**`H3_SUPPLY_REDESIGN_INSUFFICIENT`**. The regional branch is **DEFERRED / NOT PROMOTED** —
preserved as diagnostically supported by the Oracle but not deployably resolved. It is neither
erased nor successfully integrated.

- Authorization artifact: `reports/audits/stage_b_phase19_authorization.json`
- Supervisor state: `STAGE_B_AUTHORIZED__PHASE19_READY_TO_START`
- Option B / Option C: `DEFERRED__NOT_AUTHORIZED`
- Phases 15-18: `DEFERRED_CONDITIONAL__NOT_EXECUTED` (not deleted, not renumbered)
- **Stage B is ACTIVE**; the main multi-domain program begins at **Phase 19**
- Phase 20+: `NOT_STARTED_AND_NOT_AUTHORIZED`
- TEST and external TEST remain `CLOSED`

The correct summary of the regional evidence: *Oracle regional processing shows potential, but the
current GT-free predicted localization path does not preserve enough practical benefit.*

## Stage-B Phase-20 completion (shared four-domain global baseline)

Phase 20 is **COMPLETE**. It establishes **ONE** strong conventional shared segmentation
baseline over all four Stage-B domains under the frozen Phase-19 harmonized protocol —
**no FiLM, no task conditioning, no regional mechanism, no localizer, no ROI/proposal**.

- Experiment: `phase20_shared_unetpp_fourdomain_seed42_clean_v3`
- Architecture: single frozen **UNet++** (9,159,681 params), one shared parameter set, one head
- Best epoch **55** — **macro-domain VAL Dice 0.792007**
- Early stopped at epoch 70 (patience 15); resumes during training: 0
- Canonical VAL pass: **808** samples, exactly 1 inference run, threshold 0.5
- Persisted predictions: **808** NPZ (prob float16 / pred uint8 / gt uint8)
- Phase-21 entry criteria: **12/12 met**
- TEST reads: image 0, mask 0, inference 0, visualization 0

- Protocol: `reports/audits/phase20_shared_global_baseline_protocol.json`
- Notebook: `notebooks/phasewise/phase_20_multidomain_baselines/phase20_shared_global_unetpp_baseline.ipynb`
- Terminal state: **`PHASE20_SHARED_GLOBAL_BASELINE_COMPLETE__PHASE21_ELIGIBLE_NOT_STARTED`**
- **Phase 21 is ELIGIBLE but NOT STARTED** — it requires fresh supervisor authorization.

---

## Stage-B Phase-20B completion (five-model conventional baseline benchmark)

**Phase 20B is COMPLETE.** Under the **same** frozen Phase-19/20 protocol (identical data,
sampler, loss, optimizer, scheduler, augmentation, threshold 0.5 and selection rule), **four**
additional conventional architectures were trained strictly sequentially and compared with the
frozen Phase-20A UNet++ reference — a **five-model** benchmark.

- Models: `unet`, `attention_unet`, `unetpp` (20A reference), `deeplabv3plus`, `transformer_mit_unet`
- Five-model macro-domain VAL Dice: **DeepLabV3+ 0.827652** > Transformer/MiT 0.822383 >
  UNet++ 0.792010 > Attention U-Net 0.789037 > U-Net 0.787832 (each at its own best epoch)
- Two tiers separated (p ≈ 0.000); **top-two ordering NOT significant** —
  DeepLabV3+ vs Transformer/MiT Δ ≈ +0.005270, 95% CI crosses zero (p ≈ 0.282)
- Canonical VAL pass: **808** cases per model, exactly **1** inference run each, threshold 0.5
- Persisted predictions: **808 × 5 = 4040** NPZ (prob float16 / pred uint8 / gt uint8)
- **Reviewer package**: 153 figures (114 embedded), **51/51 evaluation matrices visualized (100 %)**
- Notebook determinism: **3 consecutive builds → identical SHA-256**
  (`77dc0aa84259ff7438253206c03f60fad5423b5ce41c3c3b00b029217ddd55b7`)
- TEST reads: image 0, mask 0, inference 0, visualization 0

- Freeze: `reports/audits/phase20_five_model_baseline_benchmark_freeze.json`
- Reviewer package audit: `reports/audits/phase20b_reviewer_package_audit.json`
- Figure inventory: `reports/audits/phase20b_figure_inventory.csv`
- Matrix visualization coverage: `reports/audits/phase20b_evaluation_matrix_visualization_coverage.csv`
- Notebook: `notebooks/phasewise/phase_20b_five_model_baselines/phase20b_five_model_conventional_baselines.ipynb`
- Scientific terminal state: **`PHASE20_FIVE_MODEL_BASELINE_BENCHMARK_COMPLETE__PHASE21_ELIGIBLE_NOT_STARTED`**
- Documentation terminal state: **`PHASE20B_REVIEWER_PACKAGE_COMPLETE__FULL_VISUAL_EVIDENCE__PHASE21_ELIGIBLE_NOT_STARTED`**
- **Phase 21 remains ELIGIBLE but NOT STARTED** — fresh supervisor authorization required.

## Phase 22 — Resource Gap Analysis (COMPLETE)

- Notebook: `notebooks/phasewise/phase_22_resource_gap/phase22_resource_gap_analysis.ipynb`
- Model: the FROZEN Phase-21 Global MedFiLM reference (unchanged).
- Scope: diagnostic gap analysis only — scale sensitivity, oracle regional benefit, resource frontier. NO training, NO architecture change, NO benefit predictor, NO TEST access.
- Failure atlas pooled mean Dice: 0.8387815425121063
- Oracle accept-if-beneficial ceiling gain over always-global: 0.021034244277644776 (UPPER BOUND, not deployable)
- Terminal state: `PHASE22_MULTIDOMAIN_SCALE_REGIONAL_RESOURCE_GAP_ANALYSIS_COMPLETE__PHASE23_ELIGIBLE_NOT_STARTED`
