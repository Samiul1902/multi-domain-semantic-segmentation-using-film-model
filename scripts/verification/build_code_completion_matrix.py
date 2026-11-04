"""Build the 44-phase source/test matrix from the preserved roadmap, without data I/O."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
DOCUMENTS = ["PROJECT_MASTER_PLAN.md", *[f"docs/{n}.md" for n in
             ("TASKS", "PRD", "ARCHITECTURE", "DESIGN", "RULES", "MEMORY")]]
# Requirement summaries are traceability labels, not replacements for the specs.
DELIVERABLES = [
 ("Governance, protocol and split-access contracts", "docs/RULES.md", "tests/test_test_lock.py"),
 ("Repository layout and reproducibility entrypoints", "ANTIGRAVITY_WORKFLOW.md", ""),
 ("Interpreter/CUDA/environment capture", "src/research/operator.py;src/utils/device.py", "tests/test_performance_phase_d.py"),
 ("Discovery, image/mask pairing, domain catalog", "src/data/development_validation.py;notebooks/phasewise/phase_03_dataset_discovery/code/phase03_dataset_discovery_audit.py", "tests/test_development_validation.py"),
 ("Manifest identity, split/group integrity", "src/utils/manifest_guard.py;src/data/development_validation.py", "tests/test_manifest_guard.py;tests/test_development_validation.py"),
 ("Duplicate/leakage detection; preserve v2 and v3 identities", "src/data/development_validation.py;scripts/audit/audit_v3.py", "tests/test_development_validation.py"),
 ("KUB morphology and component characterization", "src/analysis/kub_characterization.py;src/inference/clean_v3_components.py", "tests/test_phase07_taxonomy.py"),
 ("TRAIN-defined object-size quartiles and size metrics", "src/analysis/kub_object_size.py;src/metrics/object_metrics.py", "tests/test_phase07_taxonomy.py;tests/test_object_metrics.py"),
 ("Model/loss factories, data loaders, resumable trainer", "src/data/loaders.py;src/models/factory.py;src/utils/checkpointing.py", "tests/test_phase08_infrastructure.py;tests/test_phase08b_trainer_protocol.py"),
 ("KUB U-Net trainer and deterministic checkpoints", "scripts/training/train_kub_baseline.py;src/models/unet.py", "tests/test_unet.py;tests/test_checkpointing.py"),
 ("Conventional baseline training/comparison", "scripts/training/train_phase10_baselines.py;src/models/factory.py", "tests/test_phase10_models.py"),
 ("Failure taxonomy, component/size metrics, visual reporting", "scripts/analysis/analyze_phase11_failures.py;src/metrics/evaluation_metrics.py", "tests/test_object_metrics.py;tests/test_evaluation_metrics.py"),
 ("Oracle crop/zoom upper-bound tooling, paired analysis", "src/analysis/oracle_roi.py", "tests/test_oracle_roi.py"),
 ("GT-free proposals/localization and provenance", "src/inference/predicted_roi.py;src/inference/learned_roi_clean_v3.py", "tests/test_predicted_roi.py;tests/test_phase13_manifest_provenance_binding.py"),
 ("Regional refiner diagnostic and conditional gate", "src/data/regional_dataset.py;scripts/evaluation/evaluate_phase14_clean_v3_diagnostic.py", "tests/test_phase14_part1.py"),
 ("Conditional regional loss study; reusable losses only", "src/losses/segmentation.py", "tests/test_segmentation_loss.py"),
 ("Conditional fusion/routing; reusable replacement fusion", "src/research/stage6/end_to_end.py", "tests/test_stage6_integration.py"),
 ("Conditional KUB ablations; no abandoned branch activation", "scripts/analysis/build_phase28_matrix.py", ""),
 ("Conditional KUB freeze/validation; do not advance gate", "docs/RULES.md", ""),
 ("Four-domain harmonization and task metadata policy", "src/analysis/multidomain_harmonization.py;src/data/multidomain_dataset.py", "tests/test_full_pipeline.py;tests/test_stage6_baselines.py"),
 ("Shared global baseline and five-model comparison", "scripts/training/train_phase20b_shared_baseline.py;src/research/stage6/baseline_real.py", "tests/test_stage6_baselines.py"),
 ("GlobalMedFiLM and task-conditioned FiLM training", "src/models/film/global_medfilm.py;src/research/full_pipeline/stages/global_stage.py", "tests/test_full_pipeline.py;tests/test_c1_training_integration.py"),
 ("Scale, transfer, regional benefit and resource diagnostics", "src/analysis/phase22_scale.py;src/analysis/phase22_regional.py;src/analysis/phase22_resource.py", ""),
 ("Literature and novelty evidence provenance", "scripts/analysis/build_phase23_prior_art_matrix.py", ""),
 ("Frozen architecture, 202 numeric +16 task features", "src/features/barr_pre_refinement_features.py;src/models/barr/phase25_models.py", "tests/test_phase25_architecture_drift.py"),
 ("25A refiner;25B features;25C OOF gains;25D router;25E resource gate;25F safety/fusion;25G integrated controls", "src/research/full_pipeline/stages;src/research/stage6/end_to_end.py", "tests/test_full_pipeline.py;tests/test_phase25_architecture_drift.py"),
 ("Canonical assembly; independent FULL G-CACHE-R-LABELS-B-S families", "src/research/full_pipeline/orchestrator.py;src/research/full_pipeline/inference.py", "tests/test_full_pipeline.py;tests/test_full_family_loading_contract.py"),
 ("Per-domain preservation and paired sample comparisons", "src/research/evaluation/stats.py;scripts/analysis/phase27_exec_common.py", "tests/test_evaluation_phase_c.py"),
 ("Architecture ablation matrix and exports", "scripts/analysis/build_phase28_matrix.py;src/research/c1_film/training_engine.py", "tests/test_c1_training_integration.py;tests/test_c3_controlled_experiments.py"),
 ("Independent three-seed weights, recovery and deterministic execution", "src/research/full_pipeline/seeds.py;src/research/lite_pipeline/orchestrator.py", "tests/test_full_pipeline.py;tests/test_lite_pipeline.py;tests/test_c1_launch_multiprocessing.py"),
 ("Development-only validation, fair eight-model/24-cell comparisons", "src/research/evaluation/runner.py;src/research/evaluation/registry.py", "tests/test_evaluation_phase_c.py;tests/test_stage6_integration.py"),
 ("Paired differences, cluster CIs, domain aggregation, inference-class separation", "src/research/evaluation/stats.py;src/research/evaluation_r1/statistics.py", "tests/test_evaluation_phase_c.py;tests/test_statistics_input_contract.py;tests/test_evaluation_r1_reference.py"),
 ("External adapters, domain-shift reporting and false positives", "scripts/analysis/phase32_specification.py;src/research/evaluation/metrics.py", "tests/test_c1_external_stress.py;tests/test_c1_external_evidence.py"),
 ("Failure/boundary taxonomy and domain summaries", "scripts/analysis/phase33_tier0_tier1_execution_v1_2.py;src/metrics/evaluation_metrics.py", "tests/test_evaluation_metrics.py"),
 ("Parameters/MACs/latency/memory and conditional invocation cost", "src/research/performance;src/research/evaluation/efficiency.py", "tests/test_performance_phase_d.py;tests/test_evaluation_phase_c.py"),
 ("FiLM attribution, Grad-CAM, proposals/router/safety visual evidence", "scripts/analysis/phase35_interpretability_execution_v1_0h.py;src/research/performance/film.py", "tests/test_late_phase_synthetic.py;tests/test_performance_phase_d.py"),
 ("Frozen noise/blur/contrast/brightness/resolution/proposal perturbations", "scripts/analysis/phase36_robustness_common_v1_0.py;scripts/analysis/phase36_robustness_execution_v1_23.py", "tests/test_late_phase_synthetic.py"),
 ("Evidence index, provenance-bound tables/figures", "src/research/evaluation/reports.py;src/research/paper_assets/validation.py", "tests/test_evaluation_phase_c.py;tests/test_paper_assets.py"),
 ("Protocol/config/checkpoint/environment/manifest/evidence hashes", "src/research/deployment/artifacts.py;src/research/full_pipeline/provenance.py", "tests/test_deployment_artifacts.py;tests/test_full_pipeline.py"),
 ("Authorized single-pass evaluation, accounting and failure-safe publication", "scripts/analysis/phase39_final_test_execution_v1_2.py;src/research/evaluation/single_pass.py", "tests/test_late_phase_synthetic.py;tests/test_single_pass_transaction.py"),
 ("Publication tables, evidence validation, reproducibility manifests", "src/research/paper_assets/validation.py;src/research/paper_assets/c1_run_export.py;src/research/evaluation/reports.py", "tests/test_paper_assets.py;tests/test_c1_stats_and_exports.py"),
 ("Byte-bound G/R/B/S packaging, preprocessing and versioned config", "src/research/deployment/artifacts.py;src/research/deployment/runtime.py", "tests/test_deployment_artifacts.py;tests/test_full_pipeline.py"),
 ("Exact packaged inference parity and measured deployment cost", "src/research/deployment/validation.py", "tests/test_deployment_artifacts.py;tests/test_full_pipeline.py"),
 ("Immutable release registry, drift/regression monitoring and rollback", "src/research/deployment/artifacts.py", "tests/test_deployment_artifacts.py"),
]


def build() -> dict:
    texts = {name: (ROOT / name).read_text(encoding="utf-8") for name in DOCUMENTS}
    titles, original, aliases = {}, {}, {}
    for match in re.finditer(r"^- \*\*Phase (\d{2}):\*\* (.+)$", texts[DOCUMENTS[0]], re.M):
        phase, entry = int(match[1]), match[2]
        title, _, status = entry.rpartition(" (")
        title = title or entry
        titles.setdefault(phase, title)
        original.setdefault(phase, status.rstrip(")"))
        aliases.setdefault(phase, []).append(entry)
    for match in re.finditer(r"^\| (4[123]) \| (.*?) \| (.*?) \|$", texts[DOCUMENTS[0]], re.M):
        phase = int(match[1]); titles[phase] = match[2]; original[phase] = match[3]
        aliases[phase] = [match[2]]
    if set(titles) != set(range(44)) or len(DELIVERABLES) != 44:
        raise ValueError("canonical 44-phase coverage is incomplete")
    evidence = {}
    for path in sorted((ROOT / "runs/code_completion_00_43").glob("*.xml")):
        tree = ET.parse(path)
        for case in tree.iter("testcase"):
            module = case.get("classname", "").replace(".", "/")
            # unittest class suffixes follow the test module.
            match = re.match(r"(tests/test_[^/]+)", module)
            if match:
                state = "failed" if case.find("failure") is not None or case.find("error") is not None else "skipped" if case.find("skipped") is not None else "passed"
                evidence.setdefault(match[1] + ".py", set()).add(state)
    rows = []
    for phase, (requirement, source, tests) in enumerate(DELIVERABLES):
        sources = source.split(";")
        missing = [p for p in sources if not (ROOT / p).exists()]
        test_paths = tests.split(";") if tests else []
        verified = bool(test_paths) and all("passed" in evidence.get(t, set()) and "failed" not in evidence.get(t, set()) for t in test_paths)
        status = "IMPLEMENTATION_MISSING" if missing else "CODE_COMPLETE_VERIFIED" if verified else "CODE_EXISTS_TESTING_INCOMPLETE"
        dependency = "Genuine experiments and applicable authorization remain separate"
        pending = "No new scientific execution in this task"
        gap = "No demonstrated mapped-component defect" if verified else "Complete phase-specific synthetic coverage; see test/source paths"
        if phase in (0, 1, 23):
            status = "NOT_APPLICABLE_BY_DESIGN"; gap = "Governance/literature acceptance is not software execution"
        if 15 <= phase <= 18:
            status = "NOT_APPLICABLE_BY_DESIGN"; dependency = "DEFERRED_CONDITIONAL__NOT_EXECUTED; H3 gate not satisfied"
            gap = "No conditional scientific branch activated; reusable losses/fusion retained"
        if phase == 39:
            status = "CODE_EXISTS_TESTING_INCOMPLETE"
            gap = "New single_pass.run_once is synthetic-verified; not bound into a new authorized Phase39 release"
            dependency = "EXTERNAL_AUTHORIZATION_REQUIRED; never rerun historical TEST subjects"
        if phase in (41, 42):
            status = "CODE_EXISTS_TESTING_INCOMPLETE"
            gap = "FULL package parity verified; historical Phase26/single-channel design vs RGB source reconciliation not authorized"
            dependency = "EXTERNAL_AUTHORIZATION_REQUIRED for exact historical subject/control population and release"
        rows.append(dict(phase=f"{phase:02}", exact_original_title=titles[phase],
            original_historical_status=original[phase], preserved_title_entries=aliases[phase],
            original_software_requirements=requirement, existing_implementation=sources,
            missing_implementation=missing, remaining_verification=gap, relevant_tests=test_paths,
            coding_status=status, scientific_execution_status=pending, dependency_constraints=dependency))
    return {"scope": "44 numbered phases; additive software evidence, no phase advancement",
            "authority_documents": {n: hashlib.sha256(texts[n].encode()).hexdigest() for n in DOCUMENTS},
            "rows": rows, "test_module_observations": {k: sorted(v) for k, v in evidence.items()}}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    payload = build()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"44 phases; {sum(r['coding_status'] == 'IMPLEMENTATION_MISSING' for r in payload['rows'])} missing source mappings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
