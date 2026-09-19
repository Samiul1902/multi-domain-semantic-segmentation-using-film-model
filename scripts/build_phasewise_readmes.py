import os

phase_data = [
    ("phase_00_governance", "Phase 00", "Governance & Scientific Protocol Control",
     "How is scientific reproducibility, test locking, and auditability strictly guaranteed?",
     "Research in medical image segmentation requires rock-solid data governance to eliminate cherry-picking, test set contamination, and undocumented parameter shifts.",
     "PROJECT_CONTEXT.md, ANTIGRAVITY_WORKFLOW.md, PROJECT_MASTER_PLAN.md", "None",
     "notebooks/00_project_initialization.ipynb", "notebooks/phasewise/00_PHASEWISE_PROJECT_INDEX.ipynb",
     "Governance contracts, test-lock verification, artifact hash protocols.", "COMPLETE",
     "Strict protocol boundaries prevent premature optimization and false scientific claims.",
     "Initialize project infrastructure under verified environment specifications."),

    ("phase_01_project_initialization", "Phase 01", "Project Initialization & Workspace Setup",
     "What is the exact directory layout, virtual environment, and dependency structure?",
     "Ensures clean development environment with isolated dependencies and standard tooling.",
     "Directory roots, requirements.txt, pyproject.toml", "None",
     "notebooks/00_project_initialization.ipynb", "notebooks/phasewise/phase_01_project_initialization/phase01_initialization.ipynb",
     "Project structure certification, virtualenv binding.", "COMPLETE",
     "Deterministic environment established with correct Python 3.11 virtualenv.",
     "Certify hardware and CUDA acceleration."),

    ("phase_02_environment_cuda", "Phase 02", "Environment & Hardware Certification",
     "Is the CUDA / PyTorch environment certified for deterministic execution?",
     "Confirms GPU hardware specifications, CUDA compiler compatibility, and deterministic RNG settings.",
     "NVIDIA GPU driver, PyTorch 2.6.0+cu124, CUDA 12.4 runtime", "None",
     "notebooks/01_environment_and_data_audit.ipynb", "notebooks/phasewise/phase_02_environment_cuda/phase02_environment_certification.ipynb",
     "Certified environment audit JSON and markdown reports.", "COMPLETE",
     "NVIDIA RTX 3060 Ti 8GB certified with cu124 runtime.",
     "Discover and catalog medical imaging raw datasets."),

    ("phase_03_dataset_discovery", "Phase 03", "Dataset Discovery & Forensic Inventory",
     "What medical imaging modalities and raw sources are cataloged?",
     "Discovers and audits image files, masks, resolutions, and file formats across four target domains: ISIC, BUSI, Kvasir, and KUB-Stone.",
     "Raw data folders: D:\\Softfors\\omni_seg\\data_raw", "None",
     "notebooks/02_dataset_discovery.ipynb", "notebooks/phasewise/phase_03_dataset_discovery/phase03_dataset_discovery.ipynb",
     "Dataset inventory tables, file counts, format verification.", "COMPLETE",
     "Total 8,441 images discovered across 4 clinical domains.",
     "Partition datasets into patient-stratified splits."),

    ("phase_04_manifest_splits", "Phase 04", "Manifest Generation & Patient Splits",
     "How are patient-leakage-free train/val/test splits created?",
     "Medical scans from the same patient must never cross split boundaries. This phase generates verified manifests.",
     "Patient ID mappings, image paths, mask paths", "None",
     "notebooks/03_leakage_and_split_audit.ipynb", "notebooks/phasewise/phase_04_manifest_splits/phase04_manifest_splits.ipynb",
     "manifests/train.csv, manifests/val.csv, manifests/test.csv (LOCKED).", "COMPLETE",
     "Global split created: TRAIN = 5,913, VAL = 845, TEST = 1,683 (LOCKED). Zero patient leakage.",
     "Perform forensic duplication and integrity audits on masks."),

    ("phase_05_leakage_audit", "Phase 05", "Forensic Data & Mask Semantic Audit",
     "Are there duplicate images, patient overlaps, or label anomalies?",
     "Performs pixel-level hashing, duplicate detection, and mask semantic verification to guarantee dataset integrity.",
     "Manifest files, image-mask pairs", "None",
     "notebooks/03_kub_forensic_audit.ipynb", "notebooks/phasewise/phase_05_leakage_audit/phase05_forensic_audit.ipynb",
     "Forensic integrity reports, hash audit logs.", "COMPLETE",
     "Zero duplicate pairs across splits; all masks verified binary.",
     "Characterize clinical and anatomical properties of KUB radiographs."),

    ("phase_06_kub_characterization", "Phase 06", "KUB Radiograph Characterization",
     "What are the clinical characteristics, FOV types, and stone burdens in KUB?",
     "Analyzes field of view (FULL_FIELD vs ROI_CROP), stone anatomical categories (Kidney, Ureteric, Bladder), and component counts.",
     "KUB image-mask pairs, patient metadata", "None",
     "notebooks/04_kub_characterization.ipynb", "notebooks/phasewise/phase_06_kub_characterization/phase06_kub_characterization.ipynb",
     "KUB characterization tables, FOV distribution plots.", "COMPLETE",
     "TRAIN has 771 FULL_FIELD, 1,208 ROI_CROP; VAL has 106 FULL_FIELD, 177 ROI_CROP.",
     "Define mathematical size taxonomy for kidney stones."),

    ("phase_07_tiny_object_definition", "Phase 07", "Stone Object Size Taxonomy",
     "How are Tiny, Small, Medium, and Large stones mathematically defined?",
     "Establishes dataset-relative component size quartiles based on original-space connected component area fractions.",
     "Original-space ground truth stone masks", "None",
     "notebooks/05_kub_object_size_taxonomy.ipynb", "notebooks/phasewise/phase_07_tiny_object_definition/phase07_size_taxonomy.ipynb",
     "kub_size_v1 taxonomy: Q25 (Tiny <= 0.000150), Q50 (Small <= 0.000340), Q75 (Medium <= 0.000827), Large (> 0.000827).", "COMPLETE",
     "Tiny stones occupy <0.015% of the abdominal radiograph area, posing severe scale challenges.",
     "Build modular baseline infrastructure for segmentation networks."),

    ("phase_08_baseline_infrastructure", "Phase 08", "Baseline Infrastructure & Pipeline Plumbing",
     "Are model factories, transforms, and loss layers verified with smoke tests?",
     "Constructs modular PyTorch architecture factories (UNet, AttentionUNet, UNet++, DeepLabV3+), aspect-preserving square padding, and loss functions.",
     "PyTorch datasets, loaders, transforms", "UNet smoke model",
     "notebooks/06_kub_baseline_infrastructure.ipynb", "notebooks/phasewise/phase_08_baseline_infrastructure/phase08_infrastructure.ipynb",
     "Plumbing smoke test checkpoints, unit tests.", "COMPLETE",
     "Complete modular training and inference pipeline verified.",
     "Train foundational U-Net baseline on full KUB dataset."),

    ("phase_09_baseline_training", "Phase 09", "Foundational Baseline Training",
     "How does foundational U-Net perform on KUB segmentation?",
     "Trains standard U-Net baseline on KUB training set using 0.5 BCE + 0.5 Dice loss with early stopping and power-resume support.",
     "KUB TRAIN (638 images), VAL (283 images)", "UNet (7.76M params)",
     "notebooks/07_kub_unet_baseline_training.ipynb", "notebooks/phasewise/phase_09_baseline_training/phase09_baseline_models_training_and_validation.ipynb",
     "Checkpoints best.pt (Val Macro Dice: 0.7455), training curves, evaluation tables.", "COMPLETE",
     "Foundational baseline establishes macro Dice 0.7455, but Tiny stone recall is limited to 75.34%.",
     "Benchmark multiple global architectures under strict fair comparison."),

    ("phase_10_baseline_comparison", "Phase 10", "Baseline Architecture Comparison",
     "Which global baseline architecture performs best on tiny stones and full fields?",
     "Performs controlled comparison of U-Net, Attention U-Net, UNet++, and DeepLabV3+ under identical seeds, splits, and loss formulations.",
     "KUB VAL (283 images: 106 FULL_FIELD + 177 ROI_CROP)", "U-Net, Attention U-Net, UNet++, DeepLabV3+",
     "notebooks/08_kub_baseline_comparison.ipynb", "notebooks/phasewise/phase_10_baseline_comparison/phase10_baseline_model_comparison_and_visual_analysis.ipynb",
     "Phase 10 model comparison table: UNet++ wins (Macro Dice 0.7625, Tiny Recall 78.08%, FP/img 1.53).", "COMPLETE",
     "UNet++ is the strongest global baseline, capturing stone edges best via dense skip connections.",
     "Conduct deep forensic failure analysis on baseline errors."),

    ("phase_11_failure_analysis", "Phase 11", "Failure Mode Taxonomy & Error Analysis",
     "Why do global full-field networks fail on small stones and complex anatomy?",
     "Analyzes false positive distributions, global-empty predictions (7 cases), and missed tiny stones across the 106 FULL_FIELD validation images.",
     "UNet++ predictions, Phase 10 validation tables", "UNet++",
     "notebooks/09_kub_failure_analysis.ipynb", "notebooks/phasewise/phase_11_failure_analysis/phase11_kub_failure_analysis_and_tiny_stone_errors.ipynb",
     "Failure classification tables: 16 Hard-Tiny missed stones, 7 Global-Empty images, bowel gas FPs.", "COMPLETE",
     "Downsampling to 512x512 destroys contrast for tiny stones, proving that monolithic global segmentation has fundamental scale limits.",
     "Evaluate oracle upper-bound potential of localized zoom."),

    ("phase_12_oracle_roi", "Phase 12", "Oracle ROI / Upper-Bound Study",
     "What performance headroom exists if target regions are perfectly localized?",
     "Extracts ground-truth-bounded regions of interest with 25% margin, passes them to high-resolution crops, and measures recovery headroom.",
     "Ground-truth stone bounding boxes, FULL_FIELD VAL images", "Oracle Zoom Pipeline",
     "notebooks/10_kub_oracle_roi_upper_bound.ipynb", "notebooks/phasewise/phase_12_oracle_roi/phase12_oracle_roi_upper_bound_analysis.ipynb",
     "Oracle Dice increases to 0.7757 (vs 0.6528 global); 15 of 16 globally missed Tiny stones are recovered (98.63% Tiny recall).", "COMPLETE",
     "Massive theoretical headroom exists if regions of interest can be proposed accurately without GT.",
     "Develop GT-free learned localizer to generate candidate proposals."),

    ("phase_13_predicted_roi_localization", "Phase 13", "Learned Localizer & Proposal Generation",
     "Can CenterNet heatmaps reliably propose stone regions without ground truth?",
     "Trains and evaluates candidate proposal models: simple connected components (Phase 13), exploratory localizers (Stage 4A/4B/4C), and final CenterNet Stage 4D with AvgPool4.",
     "CenterNet focal targets, Gaussian heatmaps", "CenterNet Localizer (Stage 4D)",
     "notebooks/11c_kub_final_localizer_redesign.ipynb", "notebooks/phasewise/phase_13_predicted_roi_localization/phase13_stage4d_localizer_final_visual_analysis.ipynb",
     "Stage 4D recovers 7/16 hard-Tiny stones, 84.93% Tiny proposal recall (62/73), 1.76 proposals/img.", "COMPLETE",
     "Stage 4D satisfies all entry gates, providing a viable coarse candidate proposal stage.",
     "Evaluate two-stage coarse-to-fine regional refiner cascade."),

    ("phase_14_regional_refiner", "Phase 14", "Regional Refiner Diagnostic Cascade",
     "Does crop-level refinement translate into full-field segmentation gains?",
     "Evaluates full two-stage pipeline: Stage 4D proposals -> cropped 256x256 Regional Refiner U-Net -> canvas restoration -> direct-replacement fusion.",
     "Stage 4D proposals, Regional U-Net checkpoint", "Regional Refiner U-Net (L0)",
     "notebooks/13_phase14_regional_refiner_diagnostic.ipynb", "notebooks/phasewise/phase_14_regional_refiner/phase14_regional_refiner_pipeline_and_diagnostic_analysis.ipynb",
     "Full-field Dice drops to 0.6133 (vs 0.6528 global); false positives inside proposals degrade performance.", "COMPLETE (DIAGNOSTIC)",
     "The regional refiner is uncalibrated on non-stone background crops, necessitating specialized asymmetric loss training.",
     "Conduct prospective loss function study (Phase 15)."),

    ("phase_15_loss_study", "Phase 15", "Regional Refiner Segmentation Loss Study",
     "Can specialized asymmetric losses (Focal, Tversky, Focal-Tversky) suppress crop false positives?",
     "Designs and freezes a 4-arm loss ablation (L0: BCE+Dice, L1: Focal+Dice, L2: Tversky, L3: Focal-Tversky) to optimize regional boundary refinement.",
     "723 training crops (483 base + 240 perturbed + pure negatives)", "Refiner L0, L1, L2, L3",
     "notebooks/14_phase15_loss_study.ipynb", "notebooks/phasewise/phase_15_loss_study/phase15_loss_function_comparison_and_validation.ipynb",
     "Frozen protocol, pre-training unit tests, L0 baseline evidence, 16-case cohort selection.", "CURRENT (PROTOCOL DESIGN)",
     "Theoretical autograd gradients verified; awaiting external supervisor training authorization.",
     "Train L1, L2, L3 refiners and advance to multi-domain harmonization (Phase 16).")
]

for p_dir, p_num, p_title, p_quest, p_why, p_inputs, p_models, p_canon, p_rev, p_out, p_stat, p_learn, p_next in phase_data:
    readme_path = os.path.join("notebooks/phasewise", p_dir, "README.md")
    content = f"""# {p_num}: {p_title}

## 1. Scientific Question
**{p_quest}**

## 2. Why This Phase Exists
{p_why}

## 3. Input Data & Artifacts
- **Inputs:** `{p_inputs}`
- **Models:** `{p_models}`

## 4. Notebook Reference
- **Canonical Provenance Source:** `{p_canon}`
- **Reviewer-Facing Notebook:** `{p_rev}`

## 5. Main Outputs & Milestones
- **Status:** `{p_stat}`
- **Outputs:** {p_out}

## 6. What Was Learned
{p_learn}

## 7. Why The Next Phase Was Needed
{p_next}
"""
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(content)

print(f"Generated {len(phase_data)} README.md files across all phases under notebooks/phasewise/!")

