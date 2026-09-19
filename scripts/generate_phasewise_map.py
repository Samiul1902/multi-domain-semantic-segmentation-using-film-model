import json, csv
from pathlib import Path

# Mapping of all 41 phases
phases = [
    {
        "phase_id": "00",
        "folder": "phase_00_governance",
        "title": "Governance & Scientific Protocols",
        "stage": "Stage A: KUB Regional Development",
        "status": "COMPLETE",
        "reviewer_notebook": "phase00_governance_and_protocol_audit.ipynb",
        "canonical_source": "reports/audits/research_protocol.md",
        "visual_artifacts": "reports/audits/test_lock.json"
    },
    {
        "phase_id": "01",
        "folder": "phase_01_project_initialization",
        "title": "Project Initialization & Architecture",
        "stage": "Stage A: KUB Regional Development",
        "status": "COMPLETE",
        "reviewer_notebook": "phase01_project_structure_and_contract.ipynb",
        "canonical_source": "PROJECT_MASTER_PLAN.md",
        "visual_artifacts": "reports/audits/repository_script_inventory.md"
    },
    {
        "phase_id": "02",
        "folder": "phase_02_environment_cuda",
        "title": "Environment & CUDA Verification",
        "stage": "Stage A: KUB Regional Development",
        "status": "COMPLETE",
        "reviewer_notebook": "phase02_environment_and_hardware_certification.ipynb",
        "canonical_source": "reports/audits/environment.json",
        "visual_artifacts": "reports/audits/environment.md"
    },
    {
        "phase_id": "03",
        "folder": "phase_03_dataset_discovery",
        "title": "Dataset Discovery & Multi-Domain Cataloging",
        "stage": "Stage A: KUB Regional Development",
        "status": "COMPLETE",
        "reviewer_notebook": "phase03_multidomain_dataset_inventory.ipynb",
        "canonical_source": "reports/audits/dataset_inventory.json",
        "visual_artifacts": "reports/figures/sample_visualizations/"
    },
    {
        "phase_id": "04",
        "folder": "phase_04_manifest_splits",
        "title": "Patient-Aware Manifest & Data Splits",
        "stage": "Stage A: KUB Regional Development",
        "status": "COMPLETE",
        "reviewer_notebook": "phase04_patient_split_and_leakage_barrier.ipynb",
        "canonical_source": "manifests/manifest_metadata.json",
        "visual_artifacts": "reports/tables/manifest_distributions.csv"
    },
    {
        "phase_id": "05",
        "folder": "phase_05_leakage_audit",
        "title": "Forensic Data & Image Leakage Audit",
        "stage": "Stage A: KUB Regional Development",
        "status": "COMPLETE",
        "reviewer_notebook": "phase05_forensic_duplicate_and_leakage_audit.ipynb",
        "canonical_source": "reports/audits/leakage_audit.json",
        "visual_artifacts": "reports/audits/near_duplicate_candidates.csv"
    },
    {
        "phase_id": "06",
        "folder": "phase_06_kub_characterization",
        "title": "KUB Clinical & Anatomical Characterization",
        "stage": "Stage A: KUB Regional Development",
        "status": "COMPLETE",
        "reviewer_notebook": "phase06_kub_clinical_and_stone_burden_characterization.ipynb",
        "canonical_source": "reports/audits/kub_characterization.json",
        "visual_artifacts": "reports/figures/kub_characterization/"
    },
    {
        "phase_id": "07",
        "folder": "phase_07_tiny_object_definition",
        "title": "Tiny Object Definition & Size Stratification",
        "stage": "Stage A: KUB Regional Development",
        "status": "COMPLETE",
        "reviewer_notebook": "phase07_tiny_object_size_quartiles.ipynb",
        "canonical_source": "reports/audits/kub_object_size_thresholds.json",
        "visual_artifacts": "reports/figures/kub_object_size/"
    },
    {
        "phase_id": "08",
        "folder": "phase_08_baseline_infrastructure",
        "title": "Baseline Infrastructure & Model Factories",
        "stage": "Stage A: KUB Regional Development",
        "status": "COMPLETE",
        "reviewer_notebook": "phase08_baseline_model_infrastructure.ipynb",
        "canonical_source": "reports/audits/kub_baseline_infrastructure.json",
        "visual_artifacts": "reports/figures/kub_baseline_infrastructure/"
    },
    {
        "phase_id": "09",
        "folder": "phase_09_baseline_training",
        "title": "Global Baseline Model Training (U-Net)",
        "stage": "Stage A: KUB Regional Development",
        "status": "COMPLETE",
        "reviewer_notebook": "phase09_baseline_models_training_and_validation.ipynb",
        "canonical_source": "reports/audits/phase9_kub_unet_baseline.json",
        "visual_artifacts": "reports/figures/phase9_unet_baseline/"
    },
    {
        "phase_id": "10",
        "folder": "phase_10_baseline_comparison",
        "title": "Baseline Comparison (U-Net vs UNet++ vs SegNet)",
        "stage": "Stage A: KUB Regional Development",
        "status": "COMPLETE",
        "reviewer_notebook": "phase10_baseline_model_comparison_and_visual_analysis.ipynb",
        "canonical_source": "reports/audits/phase10_kub_baseline_comparison.json",
        "visual_artifacts": "reports/figures/retrospective/phase10_baselines/"
    },
    {
        "phase_id": "11",
        "folder": "phase_11_failure_analysis",
        "title": "Baseline Failure Analysis & Small-Stone Error Modes",
        "stage": "Stage A: KUB Regional Development",
        "status": "COMPLETE",
        "reviewer_notebook": "phase11_kub_failure_analysis_and_tiny_stone_errors.ipynb",
        "canonical_source": "reports/audits/phase11_kub_failure_analysis.json",
        "visual_artifacts": "reports/figures/retrospective/phase11_failures/"
    },
    {
        "phase_id": "12",
        "folder": "phase_12_oracle_roi",
        "title": "Oracle ROI Upper Bound Analysis",
        "stage": "Stage A: KUB Regional Development",
        "status": "COMPLETE",
        "reviewer_notebook": "phase12_oracle_roi_upper_bound_analysis.ipynb",
        "canonical_source": "reports/audits/phase12_oracle_roi_upper_bound.json",
        "visual_artifacts": "reports/figures/phase12_oracle_roi/"
    },
    {
        "phase_id": "13",
        "folder": "phase_13_predicted_roi_localization",
        "title": "GT-Free Regional Proposal Localization (Stage 4D)",
        "stage": "Stage A: KUB Regional Development",
        "status": "COMPLETE",
        "reviewer_notebook": "phase13_stage4d_localizer_final_visual_analysis.ipynb",
        "canonical_source": "reports/audits/phase13b_stage4d_final_evaluation.json",
        "visual_artifacts": "reports/figures/phase13b_stage4d_final_localizer/"
    },
    {
        "phase_id": "14",
        "folder": "phase_14_regional_refiner",
        "title": "Regional Refiner Diagnostic Evaluation",
        "stage": "Stage A: KUB Regional Development",
        "status": "COMPLETE_DIAGNOSTIC",
        "reviewer_notebook": "phase14_regional_refiner_pipeline_and_diagnostic_analysis.ipynb",
        "canonical_source": "reports/audits/phase14_final_closure_audit.json",
        "visual_artifacts": "reports/figures/phase14_part3c/"
    },
    {
        "phase_id": "15",
        "folder": "phase_15_loss_study",
        "title": "Regional Refiner Segmentation Loss Study",
        "stage": "Stage A: KUB Regional Development",
        "status": "CURRENT_PROTOCOL_DESIGN",
        "reviewer_notebook": "phase15_loss_function_comparison.ipynb",
        "canonical_source": "reports/audits/phase15_loss_study_protocol.json",
        "visual_artifacts": "reports/figures/phase15_protocol/"
    },
    {
        "phase_id": "16",
        "folder": "phase_16_fusion",
        "title": "Regional-Global Mask Fusion & False Positive Suppression",
        "stage": "Stage A: KUB Regional Development",
        "status": "NOT_STARTED",
        "reviewer_notebook": "README.md",
        "canonical_source": "PENDING_PHASE15",
        "visual_artifacts": "NONE"
    },
    {
        "phase_id": "17",
        "folder": "phase_17_kub_regional_ablation",
        "title": "KUB Regional Pipeline Comprehensive Ablation",
        "stage": "Stage A: KUB Regional Development",
        "status": "NOT_STARTED",
        "reviewer_notebook": "README.md",
        "canonical_source": "PENDING_PHASE16",
        "visual_artifacts": "NONE"
    },
    {
        "phase_id": "18",
        "folder": "phase_18_kub_final_dev_benchmark",
        "title": "KUB Final Development Validation Benchmark",
        "stage": "Stage A: KUB Regional Development",
        "status": "NOT_STARTED",
        "reviewer_notebook": "README.md",
        "canonical_source": "PENDING_PHASE17",
        "visual_artifacts": "NONE"
    },
    {
        "phase_id": "19",
        "folder": "phase_19_harmonization",
        "title": "Multi-Domain Dataset Harmonization (ISIC, BUSI, Kvasir, KUB)",
        "stage": "Stage B: Multi-Domain Scaling",
        "status": "NOT_STARTED",
        "reviewer_notebook": "README.md",
        "canonical_source": "PENDING_PHASE18",
        "visual_artifacts": "NONE"
    },
    {
        "phase_id": "20",
        "folder": "phase_20_multidomain_baselines",
        "title": "Multi-Domain Global Baseline Evaluation",
        "stage": "Stage B: Multi-Domain Scaling",
        "status": "NOT_STARTED",
        "reviewer_notebook": "README.md",
        "canonical_source": "PENDING_PHASE19",
        "visual_artifacts": "NONE"
    },
    {
        "phase_id": "21",
        "folder": "phase_21_global_medfilm",
        "title": "Global MedFiLM Reference Architecture",
        "stage": "Stage B: Multi-Domain Scaling",
        "status": "NOT_STARTED",
        "reviewer_notebook": "README.md",
        "canonical_source": "PENDING_PHASE20",
        "visual_artifacts": "NONE"
    },
    {
        "phase_id": "22",
        "folder": "phase_22_gap_analysis",
        "title": "Multi-Domain Scale & Transfer Gap Analysis",
        "stage": "Stage B: Multi-Domain Scaling",
        "status": "NOT_STARTED",
        "reviewer_notebook": "README.md",
        "canonical_source": "PENDING_PHASE21",
        "visual_artifacts": "NONE"
    },
    {
        "phase_id": "23",
        "folder": "phase_23_literature_novelty",
        "title": "Literature & Methodological Novelty Positioning",
        "stage": "Stage B: Multi-Domain Scaling",
        "status": "NOT_STARTED",
        "reviewer_notebook": "README.md",
        "canonical_source": "PENDING_PHASE22",
        "visual_artifacts": "NONE"
    },
    {
        "phase_id": "24",
        "folder": "phase_24_ra_medfilm_design",
        "title": "RA-MedFiLM Architectural Specification",
        "stage": "Stage B: Multi-Domain Scaling",
        "status": "NOT_STARTED",
        "reviewer_notebook": "README.md",
        "canonical_source": "PENDING_PHASE23",
        "visual_artifacts": "NONE"
    },
    {
        "phase_id": "25",
        "folder": "phase_25_ra_medfilm_dev",
        "title": "RA-MedFiLM Controlled Module Development",
        "stage": "Stage B: Multi-Domain Scaling",
        "status": "NOT_STARTED",
        "reviewer_notebook": "README.md",
        "canonical_source": "PENDING_PHASE24",
        "visual_artifacts": "NONE"
    },
    {
        "phase_id": "26",
        "folder": "phase_26_full_four_domain_training",
        "title": "Full Four-Domain Joint Architecture Training",
        "stage": "Stage B: Multi-Domain Scaling",
        "status": "NOT_STARTED",
        "reviewer_notebook": "README.md",
        "canonical_source": "PENDING_PHASE25",
        "visual_artifacts": "NONE"
    },
    {
        "phase_id": "27",
        "folder": "phase_27_preservation",
        "title": "Multi-Domain Performance Preservation Audit",
        "stage": "Stage C: Evidence & Rigor",
        "status": "NOT_STARTED",
        "reviewer_notebook": "README.md",
        "canonical_source": "PENDING_PHASE26",
        "visual_artifacts": "NONE"
    },
    {
        "phase_id": "28",
        "folder": "phase_28_model_ablation",
        "title": "Comprehensive System Ablation Matrix",
        "stage": "Stage C: Evidence & Rigor",
        "status": "NOT_STARTED",
        "reviewer_notebook": "README.md",
        "canonical_source": "PENDING_PHASE27",
        "visual_artifacts": "NONE"
    },
    {
        "phase_id": "29",
        "folder": "phase_29_3seed_reproducibility",
        "title": "Three-Seed Deterministic Reproducibility Study",
        "stage": "Stage C: Evidence & Rigor",
        "status": "NOT_STARTED",
        "reviewer_notebook": "README.md",
        "canonical_source": "PENDING_PHASE28",
        "visual_artifacts": "NONE"
    },
    {
        "phase_id": "30",
        "folder": "phase_30_final_dev_val",
        "title": "Final Development Validation Benchmark",
        "stage": "Stage C: Evidence & Rigor",
        "status": "NOT_STARTED",
        "reviewer_notebook": "README.md",
        "canonical_source": "PENDING_PHASE29",
        "visual_artifacts": "NONE"
    },
    {
        "phase_id": "31",
        "folder": "phase_31_statistical_significance",
        "title": "Statistical Significance & Hypothesis Testing",
        "stage": "Stage C: Evidence & Rigor",
        "status": "NOT_STARTED",
        "reviewer_notebook": "README.md",
        "canonical_source": "PENDING_PHASE30",
        "visual_artifacts": "NONE"
    },
    {
        "phase_id": "32",
        "folder": "phase_32_external_validation",
        "title": "External Dataset & Domain Shift Evaluation",
        "stage": "Stage C: Evidence & Rigor",
        "status": "NOT_STARTED",
        "reviewer_notebook": "README.md",
        "canonical_source": "PENDING_PHASE31",
        "visual_artifacts": "NONE"
    },
    {
        "phase_id": "33",
        "folder": "phase_33_final_failure_analysis",
        "title": "Final System Failure & Boundary Error Analysis",
        "stage": "Stage C: Evidence & Rigor",
        "status": "NOT_STARTED",
        "reviewer_notebook": "README.md",
        "canonical_source": "PENDING_PHASE32",
        "visual_artifacts": "NONE"
    },
    {
        "phase_id": "34",
        "folder": "phase_34_efficiency_profiling",
        "title": "Computational Efficiency & Runtime Profiling",
        "stage": "Stage C: Evidence & Rigor",
        "status": "NOT_STARTED",
        "reviewer_notebook": "README.md",
        "canonical_source": "PENDING_PHASE33",
        "visual_artifacts": "NONE"
    },
    {
        "phase_id": "35",
        "folder": "phase_35_interpretability",
        "title": "Feature Attribution & Visual Interpretability",
        "stage": "Stage C: Evidence & Rigor",
        "status": "NOT_STARTED",
        "reviewer_notebook": "README.md",
        "canonical_source": "PENDING_PHASE34",
        "visual_artifacts": "NONE"
    },
    {
        "phase_id": "36",
        "folder": "phase_36_robustness_perturbation",
        "title": "Robustness & Image Perturbation Analysis",
        "stage": "Stage C: Evidence & Rigor",
        "status": "NOT_STARTED",
        "reviewer_notebook": "README.md",
        "canonical_source": "PENDING_PHASE35",
        "visual_artifacts": "NONE"
    },
    {
        "phase_id": "37",
        "folder": "phase_37_evidence_consolidation",
        "title": "Comprehensive Visual & Tabular Evidence Consolidation",
        "stage": "Stage C: Evidence & Rigor",
        "status": "NOT_STARTED",
        "reviewer_notebook": "README.md",
        "canonical_source": "PENDING_PHASE36",
        "visual_artifacts": "NONE"
    },
    {
        "phase_id": "38",
        "folder": "phase_38_protocol_freeze",
        "title": "Manuscript Protocol & Checkpoint Freeze",
        "stage": "Stage D: Freeze & Publication",
        "status": "NOT_STARTED",
        "reviewer_notebook": "README.md",
        "canonical_source": "PENDING_PHASE37",
        "visual_artifacts": "NONE"
    },
    {
        "phase_id": "39",
        "folder": "phase_39_untouched_test_evaluation",
        "title": "Final Untouched Test Cohort Evaluation",
        "stage": "Stage D: Freeze & Publication",
        "status": "NOT_STARTED",
        "reviewer_notebook": "README.md",
        "canonical_source": "PENDING_PHASE38",
        "visual_artifacts": "NONE"
    },
    {
        "phase_id": "40",
        "folder": "phase_40_publication_reproducibility_audit",
        "title": "Publication Package & Reproducibility Audit",
        "stage": "Stage D: Freeze & Publication",
        "status": "NOT_STARTED",
        "reviewer_notebook": "README.md",
        "canonical_source": "PENDING_PHASE39",
        "visual_artifacts": "NONE"
    }
]

out_json = Path("reports/audits/phasewise_notebook_map.json")
with open(out_json, "w", encoding="utf-8") as jf:
    json.dump(phases, jf, indent=2)

out_csv = Path("reports/audits/phasewise_notebook_map.csv")
with open(out_csv, "w", encoding="utf-8", newline="") as cf:
    writer = csv.DictWriter(cf, fieldnames=list(phases[0].keys()))
    writer.writeheader()
    writer.writerows(phases)

out_md = Path("reports/audits/phasewise_notebook_map.md")
md_lines = [
    "# Canonical 41-Phase Reviewer Notebook Map",
    "",
    f"- **Total Phases Cataloged:** {len(phases)} (Phase 00 to Phase 40)",
    "- **Generated At:** 2026-09-19",
    "- **Execution Environment:** `D:\\Softfors\\jup\\.venv\\Scripts\\python.exe` (Kernel: `jup-venv`)",
    "",
    "| Phase | Stage | Title | Status | Reviewer Notebook | Canonical Source |",
    "| :--- | :--- | :--- | :--- | :--- | :--- |"
]

for p in phases:
    nb_link = f"[`{p['reviewer_notebook']}`](file:///D:/Softfors/jup/notebooks/phasewise/{p['folder']}/{p['reviewer_notebook']})" if p['reviewer_notebook'] != 'README.md' else f"[`{p['reviewer_notebook']}`](file:///D:/Softfors/jup/notebooks/phasewise/{p['folder']}/README.md)"
    md_lines.append(f"| `{p['phase_id']}` | {p['stage']} | **{p['title']}** | `{p['status']}` | {nb_link} | `{p['canonical_source']}` |")

out_md.write_text("\n".join(md_lines), encoding="utf-8")
print(f"Phasewise notebook map generated successfully for {len(phases)} phases!")

