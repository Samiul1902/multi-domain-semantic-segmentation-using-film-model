#!/usr/bin/env python
"""Assemble the ReMedFiLM supervisor submission folder from FROZEN repository artifacts.

This script is a COPY-ONLY packager. It never trains a model, never runs inference,
never opens a protected TEST1683 image, and never modifies any source artifact.

Usage (from the repository root):

    .venv/Scripts/python.exe full_doc_report/Supervisor_Submission/08_Verification/build_submission_package.py
    .venv/Scripts/python.exe full_doc_report/Supervisor_Submission/08_Verification/validate_submission.py

Stage 1 (this file)   : copy verified artifacts + derive small audit tables.
Stage 2 (validator)   : verify references/integrity, write SUBMISSION_MANIFEST.csv, build the ZIP.

Every destination path is relative to full_doc_report/Supervisor_Submission/.
Every source path is relative to the repository root.
"""
from __future__ import annotations

import csv
import glob
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "full_doc_report" / "Supervisor_Submission"

# (source relative to ROOT, destination relative to OUT)
# Absolute Windows paths are deliberately never published.
COPIES: list[tuple[str, str]] = [
    # ---- 01 thesis / reports -------------------------------------------------
    ("full_doc_report/ReMedFiLM_Complete_Scientific_Report_V8.pdf",
     "01_Thesis_and_Reports/ReMedFiLM_Complete_Scientific_Report_V8.pdf"),
    ("full_doc_report/ReMedFiLM_Complete_Scientific_Report_V8.docx",
     "01_Thesis_and_Reports/ReMedFiLM_Complete_Scientific_Report_V8.docx"),
    # V9 is a NEWER DRAFT, not a verified authority: no independent V9 QA record
    # exists, and its companion V9 Dataset Guide carries split counts that conflict
    # with manifests/phase4_v3. Included for completeness, explicitly labelled.
    ("full_doc_report/V9/ReMedFiLM_Complete_Scientific_Report_V9.docx",
     "01_Thesis_and_Reports/UNVERIFIED_DRAFT_ReMedFiLM_Complete_Scientific_Report_V9.docx"),
    ("full_doc_report/V9/ReMedFiLM_V9_Scientific_Audit.md",
     "01_Thesis_and_Reports/ReMedFiLM_V9_Scientific_Audit_ISSUE_LEDGER.md"),
    ("paper_doc/RA_MedFiLM_BARR_Full_Supervisor_Report.docx",
     "01_Thesis_and_Reports/RA_MedFiLM_BARR_Full_Supervisor_Report.docx"),
    ("full_doc_report/V8_REPORT_CONTENT_MANIFEST.json",
     "01_Thesis_and_Reports/V8_REPORT_CONTENT_MANIFEST.json"),
    ("full_doc_report/REMEDFILM_FINAL_QA_CHECKS.json",
     "01_Thesis_and_Reports/REMEDFILM_FINAL_QA_CHECKS.json"),
    ("full_doc_report/REMEDFILM_FINAL_SCIENTIFIC_QA.md",
     "01_Thesis_and_Reports/REMEDFILM_FINAL_SCIENTIFIC_QA.md"),
    ("reports/manuscript/final/manuscript_final.md",
     "01_Thesis_and_Reports/manuscript_final_SOURCE.md"),

    # ---- 02 methodology / architecture --------------------------------------
    ("full_doc_report/REMEDFILM_FULL_COMPONENT_REGISTRY.json",
     "02_Methodology_and_Architecture/REMEDFILM_FULL_COMPONENT_REGISTRY.json"),
    ("full_doc_report/tables/REMEDFILM_COMPONENT_PARAMETERS.csv",
     "02_Methodology_and_Architecture/REMEDFILM_COMPONENT_PARAMETERS.csv"),
    ("docs/MATHEMATICAL_FORMULATION_VERIFIED.md",
     "02_Methodology_and_Architecture/MATHEMATICAL_FORMULATION_VERIFIED.md"),
    ("docs/METHODOLOGY_IMPLEMENTATION_MAP.md",
     "02_Methodology_and_Architecture/METHODOLOGY_IMPLEMENTATION_MAP.md"),
    ("full_doc_report/ReMedFiLM_Model_Identity_and_Methodology.md",
     "02_Methodology_and_Architecture/ReMedFiLM_Model_Identity_and_Methodology.md"),
    ("src/models/film/global_medfilm.py",
     "02_Methodology_and_Architecture/code/global_medfilm.py"),
    ("src/models/barr/ra_medfilm_barr.py",
     "02_Methodology_and_Architecture/code/ra_medfilm_barr.py"),
    ("src/models/barr/phase25_models.py",
     "02_Methodology_and_Architecture/code/phase25_models.py"),
    ("src/models/barr/regional_refiner.py",
     "02_Methodology_and_Architecture/code/regional_refiner.py"),
    ("src/models/barr/router_variants.py",
     "02_Methodology_and_Architecture/code/router_variants.py"),
    ("src/inference/predicted_roi.py",
     "02_Methodology_and_Architecture/code/predicted_roi.py"),
    ("src/research/full_pipeline/recipe.py",
     "02_Methodology_and_Architecture/code/recipe.py"),
    ("src/data/transforms.py",
     "02_Methodology_and_Architecture/code/transforms.py"),

    # ---- 03 internal results -------------------------------------------------
    ("full_doc_report/REMEDFILM_FULL_VAL808_METRICS.csv",
     "03_Experimental_Results/internal/REMEDFILM_FULL_VAL808_METRICS.csv"),
    ("full_doc_report/REMEDFILM_INTERNAL_EVALUATION.csv",
     "03_Experimental_Results/internal/REMEDFILM_INTERNAL_EVALUATION.csv"),
    ("full_doc_report/tables/REMEDFILM_INTERNAL_PER_SAMPLE.csv",
     "03_Experimental_Results/internal/REMEDFILM_INTERNAL_PER_SAMPLE.csv"),
    ("full_doc_report/tables/REMEDFILM_PAIRED_DELTA.json",
     "03_Experimental_Results/internal/REMEDFILM_PAIRED_DELTA.json"),
    ("reports/tables/phase21_six_model_comparison.csv",
     "03_Experimental_Results/internal/phase21_six_model_comparison.csv"),
    ("reports/audits/phase27_preservation_result.json",
     "03_Experimental_Results/internal/phase27_preservation_result.json"),
    ("reports/audits/phase29_phase_d_val808_per_seed_continuity.json",
     "03_Experimental_Results/internal/phase29_phase_d_val808_per_seed_continuity.json"),
    ("full_doc_report/REMEDFILM_ABLATION_AND_PROGRESSION.csv",
     "03_Experimental_Results/internal/REMEDFILM_ABLATION_AND_PROGRESSION.csv"),

    # ---- 03 external results -------------------------------------------------
    ("full_doc_report/REMEDFILM_FULL_EXTERNAL_METRICS.csv",
     "03_Experimental_Results/external/REMEDFILM_FULL_EXTERNAL_METRICS.csv"),
    ("full_doc_report/EXTERNAL_EVALUATION_EVIDENCE.csv",
     "03_Experimental_Results/external/EXTERNAL_EVALUATION_EVIDENCE.csv"),
    ("reports/tables/c1_external_stress_per_case.csv",
     "03_Experimental_Results/external/c1_external_stress_per_case.csv"),
    ("reports/tables/c1_external_stress_summary.csv",
     "03_Experimental_Results/external/c1_external_stress_summary.csv"),
    ("reports/tables/c1_external_stress_stones_subgroups.csv",
     "03_Experimental_Results/external/c1_external_stress_stones_subgroups.csv"),
    ("reports/audits/c1_external_stress_v1_0/cohort_construction.json",
     "03_Experimental_Results/external/c1_cohort_construction.json"),
    ("reports/audits/c1_external_evidence_v1_0/C1_EXTERNAL_EVIDENCE_AUDIT.md",
     "03_Experimental_Results/external/C1_EXTERNAL_EVIDENCE_AUDIT.md"),
    ("reports/audits/c1_external_evidence_v1_0/claim_provenance.json",
     "03_Experimental_Results/external/c1_claim_provenance.json"),

    # ---- 03 reconciliation ---------------------------------------------------
    ("full_doc_report/REMEDFILM_FULL_RESULT_RECONCILIATION.json",
     "03_Experimental_Results/reconciliation/REMEDFILM_FULL_RESULT_RECONCILIATION.json"),
    ("full_doc_report/REMEDFILM_FULL_RESULT_RECONCILIATION.md",
     "03_Experimental_Results/reconciliation/REMEDFILM_FULL_RESULT_RECONCILIATION.md"),
    ("full_doc_report/REMEDFILM_V8_RESULT_RECONCILIATION.md",
     "03_Experimental_Results/reconciliation/REMEDFILM_V8_RESULT_RECONCILIATION.md"),
    ("full_doc_report/REMEDFILM_V8_RESULTS_REGISTRY.json",
     "03_Experimental_Results/reconciliation/REMEDFILM_V8_RESULTS_REGISTRY.json"),

    # ---- 06 training history -------------------------------------------------
    ("full_doc_report/REMEDFILM_COMPONENT_TRAINING_HISTORY.csv",
     "06_Training_History/REMEDFILM_COMPONENT_TRAINING_HISTORY.csv"),
    ("full_doc_report/REMEDFILM_TRAINING_RUN_REGISTRY.csv",
     "06_Training_History/REMEDFILM_TRAINING_RUN_REGISTRY.csv"),
    ("reports/tables/phase28_training_run_registry.csv",
     "06_Training_History/phase28_training_run_registry.csv"),
    ("full_doc_report/REMEDFILM_EPOCH_HISTORY.csv",
     "06_Training_History/REMEDFILM_EPOCH_HISTORY.csv"),

    # ---- 05 datasets / manifests --------------------------------------------
    ("manifests/phase4_v3/README.md", "05_Datasets/manifests/phase4_v3_README.md"),
    ("manifests/phase4_v3/train.csv", "05_Datasets/manifests/train.csv"),
    ("manifests/phase4_v3/val.csv", "05_Datasets/manifests/val.csv"),
    ("reports/audits/phase24_router_split_manifest.csv",
     "05_Datasets/manifests/router_dev_holdout_split.csv"),
    ("reports/external_extension/ext01_external_dataset_inventory.json",
     "05_Datasets/ext01_external_dataset_inventory.json"),
    ("reports/external_extension/ext01_external_overlap_audit.json",
     "05_Datasets/ext01_external_overlap_audit.json"),
    ("reports/external_extension/ext02_dataset_cohort_freeze.json",
     "05_Datasets/ext02_dataset_cohort_freeze.json"),
    ("reports/external_extension/ext02_preprocessing_freeze.json",
     "05_Datasets/ext02_preprocessing_freeze.json"),
    ("reports/external_extension/ext02_1_preprocessing_authority_reconciliation.json",
     "05_Datasets/ext02_1_preprocessing_authority_reconciliation.json"),
    ("docs/publication_readiness/FINAL_DATASET_PERMISSION_AND_EXECUTION_DECISION.md",
     "05_Datasets/FINAL_DATASET_PERMISSION_AND_EXECUTION_DECISION.md"),
    ("reports/tables/phase19_dataset_inventory.csv",
     "05_Datasets/phase19_dataset_inventory.csv"),
    ("reports/audits/phase19_preprocessing_contract.json",
     "05_Datasets/phase19_preprocessing_contract.json"),
    ("reports/tables/phase32_external_dataset_discovery.csv",
     "05_Datasets/phase32_external_dataset_discovery.csv"),
    ("reports/external_extension/manifests/ext02_ham10000_manifest.csv",
     "05_Datasets/ext02_ham10000_manifest.csv"),
    ("reports/audits/phase05_leakage_audit.md",
     "05_Datasets/phase05_leakage_audit.md"),

    # ---- 07 figures: predictions & charts -----------------------------------
    ("assets/figures/remedfilm_inference_infographic.png",
     "07_Figures/methodology/remedfilm_inference_infographic.png"),
    ("assets/figures/remedfilm_full_methodology.svg",
     "07_Figures/methodology/remedfilm_full_methodology.svg"),
    ("assets/figures/remedfilm_full_methodology.pdf",
     "07_Figures/methodology/remedfilm_full_methodology.pdf"),
    ("assets/figures/readme/remedfilm_four_domain_predictions.png",
     "07_Figures/predictions/remedfilm_four_domain_predictions.png"),
    ("assets/figures/readme/prediction_isic.png",
     "07_Figures/predictions/prediction_isic.png"),
    ("assets/figures/readme/prediction_busi.png",
     "07_Figures/predictions/prediction_busi.png"),
    ("assets/figures/readme/prediction_kvasir.png",
     "07_Figures/predictions/prediction_kvasir.png"),
    ("assets/figures/readme/prediction_kub.png",
     "07_Figures/predictions/prediction_kub.png"),
    ("assets/figures/readme/README_FIGURE_SELECTION.csv",
     "07_Figures/predictions/README_FIGURE_SELECTION.csv"),
    ("assets/figures/readme/internal_domain_performance.png",
     "07_Figures/charts/internal_domain_performance.png"),
    ("assets/figures/readme/historical_model_comparison.png",
     "07_Figures/charts/historical_model_comparison.png"),
    ("assets/figures/readme/external_evaluation.png",
     "07_Figures/charts/external_evaluation.png"),
    ("assets/figures/readme/complete_ablation.png",
     "07_Figures/charts/complete_ablation.png"),
    ("assets/figures/readme/remedfilm_accuracy_compute.png",
     "07_Figures/charts/remedfilm_accuracy_compute.png"),
    ("assets/figures/readme/training_history.png",
     "07_Figures/charts/training_history.png"),

    # ---- 07 figures: historical analysis panels ------------------------------
    ("full_doc_report/figures/External evaluation/EXT01_external_dice.png",
     "07_Figures/analysis/EXT01_external_dice.png"),
    ("full_doc_report/figures/External evaluation/EXT03_stonefree_false_positive.png",
     "07_Figures/analysis/EXT03_stonefree_false_positive.png"),
    ("full_doc_report/figures/Ablation/ABL01_arm_mean_delta.png",
     "07_Figures/analysis/ABL01_arm_mean_delta.png"),
    ("full_doc_report/figures/Ablation/ABL02_paired_contrasts_forest.png",
     "07_Figures/analysis/ABL02_paired_contrasts_forest.png"),
    ("full_doc_report/figures/Routing and safety/RT01_routing_outcomes.png",
     "07_Figures/analysis/RT01_routing_outcomes.png"),
    ("full_doc_report/figures/Routing and safety/RT02_stage_flow.png",
     "07_Figures/analysis/RT02_stage_flow.png"),
    ("full_doc_report/figures/Robustness/ROB01_perturbation_degradation.png",
     "07_Figures/analysis/ROB01_perturbation_degradation.png"),
    ("full_doc_report/figures/Robustness/ROB02_domain_degradation.png",
     "07_Figures/analysis/ROB02_domain_degradation.png"),
    ("full_doc_report/figures/Efficiency/EFF01_accuracy_vs_compute.png",
     "07_Figures/analysis/EFF01_accuracy_vs_compute.png"),
    ("full_doc_report/figures/Efficiency/EFF03_accuracy_vs_parameters.png",
     "07_Figures/analysis/EFF03_accuracy_vs_parameters.png"),
    ("full_doc_report/figures/Progression/PROG01_stage_compute_and_harm.png",
     "07_Figures/analysis/PROG01_stage_compute_and_harm.png"),

    # ---- 04 Phase 28: canonical notebook ------------------------------------
    ("notebooks/phasewise/phase_28_model_ablation/phase28_comprehensive_ablation.ipynb",
     "04_Ablation_Phase28/notebook/phase28_comprehensive_ablation.ipynb"),
    ("docs/phase28_ablation_execution_spec_v1_2.md",
     "04_Ablation_Phase28/configs/phase28_ablation_execution_spec_v1_2.md"),
    ("reports/tables/phase24_ablation_plan.csv",
     "04_Ablation_Phase28/configs/phase24_ablation_plan.csv"),
    ("docs/REPRODUCIBILITY_GUIDE.md",
     "04_Ablation_Phase28/README_REPRODUCIBILITY_GUIDE.md"),
    ("tests/test_c1_external_evidence.py",
     "04_Ablation_Phase28/code/test_c1_external_evidence.py"),

    # ---- documentation / QA --------------------------------------------------
    ("docs/README_SCIENTIFIC_EVIDENCE_INDEX.md",
     "08_Verification/README_SCIENTIFIC_EVIDENCE_INDEX.md"),
    ("docs/README_FINAL_LINK_QA.md",
     "08_Verification/README_FINAL_LINK_QA.md"),
    ("docs/REPOSITORY_MAP.md",
     "08_Verification/REPOSITORY_MAP.md"),
    ("full_doc_report/PENDING_CONTROLLED_EXPERIMENTS.md",
     "08_Verification/PENDING_CONTROLLED_EXPERIMENTS.md"),
]

# Direct local dependency closure of `src/inference/predicted_roi.py` and the
# shipped model factory. These are copied into BOTH flattened code directories,
# so the dependency graph can be inspected without leaving the package.
COMMON_CODE_DEPENDENCIES = [
    "src/data/kub_dataset.py",
    "src/utils/checkpointing.py",
    "src/utils/manifest_guard.py",
    "src/utils/test_lock.py",
    "src/utils/targets.py",
    "src/utils/reproducibility.py",
]


def copy_one(src_rel: str, dst_rel: str) -> tuple[str, str]:
    src = ROOT / src_rel
    dst = OUT / dst_rel
    if not src.is_file():
        raise FileNotFoundError(f"MANDATORY SOURCE MISSING: {src_rel}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return src_rel, dst_rel


def copy_globs(patterns: list[tuple[str, str]]) -> list[tuple[str, str]]:
    done = []
    for pattern, dst_dir in patterns:
        for src in sorted(glob.glob(str(ROOT / pattern))):
            if not os.path.isfile(src):
                continue
            rel = Path(src).relative_to(ROOT).as_posix()
            done.append(copy_one(rel, f"{dst_dir}/{Path(src).name}"))
    return done


def main() -> int:
    copied = []
    for src, dst in COPIES:
        copied.append(copy_one(src, dst))

    # Phase 28 implementation code (analysis + training + QA/repair scripts)
    copied += copy_globs([
        ("scripts/analysis/*phase28*.py", "04_Ablation_Phase28/code"),
        ("scripts/training/train_phase28_f1_refiner.py", "04_Ablation_Phase28/code"),
        # shared dependencies the Phase-28 scripts import
        ("scripts/analysis/phase25f_execution_common.py", "04_Ablation_Phase28/code"),
        ("scripts/analysis/phase25f_post_safety_features.py", "04_Ablation_Phase28/code"),
        ("scripts/analysis/phase25f_spec_repair_common.py", "04_Ablation_Phase28/code"),
        ("notebooks/phasewise/phase_25c_paired_gain_labels/code/phase25c_common.py",
         "04_Ablation_Phase28/code"),
        ("src/models/barr/router_variants.py", "04_Ablation_Phase28/code"),
        ("src/data/barr_roi.py", "04_Ablation_Phase28/code"),
        ("src/inference/predicted_roi.py", "04_Ablation_Phase28/code"),
        ("src/data/barr_refiner_dataset.py", "04_Ablation_Phase28/code"),
        ("src/metrics/evaluation_metrics.py", "04_Ablation_Phase28/code"),
        ("src/utils/device.py", "04_Ablation_Phase28/code"),
        ("src/losses/segmentation.py", "04_Ablation_Phase28/code"),
        ("src/research/full_pipeline/recipe.py", "04_Ablation_Phase28/configs"),
        ("src/data/transforms.py", "04_Ablation_Phase28/code"),
        # complete flat model-family closure used by factory.py
        ("src/models/*.py", "02_Methodology_and_Architecture/code"),
        ("src/models/*.py", "04_Ablation_Phase28/code"),
    ])

    for src in COMMON_CODE_DEPENDENCIES:
        name = Path(src).name
        for code_dir in ("02_Methodology_and_Architecture/code",
                         "04_Ablation_Phase28/code"):
            copied.append(copy_one(src, f"{code_dir}/{name}"))

    # Phase 28 frozen results (tables + audits)
    copied += copy_globs([
        ("reports/tables/phase28_*", "04_Ablation_Phase28/results"),
        ("full_doc_report/Evidence/phase28_*", "04_Ablation_Phase28/results"),
        ("full_doc_report/REMEDFILM_ABLATION_RESULTS.csv", "04_Ablation_Phase28/results"),
        ("reports/audits/phase28_*", "04_Ablation_Phase28/configs"),
        ("reports/figures/p28_fig*.png", "04_Ablation_Phase28/figures"),
    ])

    # Guard: no checkpoint / raw medical image / patient workbook may enter the package
    forbidden_suffixes = {".pt", ".pth", ".ckpt", ".npy", ".npz", ".pkl", ".bmp", ".dcm"}
    forbidden_names = {"Patient_infos_BUSI-WHU.xlsx"}
    for _s, d in copied:
        dl = d.lower()
        if Path(dl).suffix in forbidden_suffixes or Path(d).name in forbidden_names:
            raise RuntimeError(f"FORBIDDEN ARTIFACT IN PACKAGE: {d}")

    print(f"stage 1: copied {len(copied)} files")
    (OUT / "08_Verification" / "COPY_MAP.json").write_text(
        json.dumps([{"source": s, "destination": d} for s, d in copied], indent=1),
        encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
