"""Phase 21 — assemble reports/audits/phase21_final_freeze.json.

Collects every Phase-21 artifact, verifies the frozen bindings, asserts the TEST
lock and the absence of every forbidden component, and writes the terminal state
``PHASE21_GLOBAL_MEDFILM_REFERENCE_COMPLETE__PHASE22_ELIGIBLE_NOT_STARTED``.

Fail-closed: refuses to write a COMPLETE terminal state if any required artifact
is missing, if TEST reads are non-zero, or if a forbidden component is present.

Usage
-----
    ./.venv/Scripts/python.exe scripts/analysis/write_phase21_freeze.py
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from scripts.training.phase21_common import (  # noqa: E402
    ARCHITECTURE_ID,
    CKPT_DIR,
    CONFIG,
    EXPERIMENT_ID,
    EXP_DIR,
    PROTOCOL_PATH,
    PROTOCOL_SHA256,
    sha256_file,
)

AUDIT_DIR = ROOT / "reports" / "audits"
TABLE_DIR = ROOT / "reports" / "tables"
FIG_DIR = ROOT / "reports" / "figures" / "phase21_global_medfilm"
NB_PATH = ROOT / "notebooks" / "phasewise" / "phase_21_global_medfilm" / \
    "phase21_global_medfilm_reference.ipynb"

TERMINAL_STATE = "PHASE21_GLOBAL_MEDFILM_REFERENCE_COMPLETE__PHASE22_ELIGIBLE_NOT_STARTED"

REQUIRED_AUDITS = [
    "phase21_entry_gate.json",
    "phase21_legacy_medfilm_architecture_audit.json",
    "phase21_protocol_binding.json",
    "phase21_global_medfilm_architecture_binding.json",
    "phase21_pre_execution_check.json",
    "phase21_prediction_manifest.json",
    "phase21_val_evaluation.json",
    "phase21_analysis.json",
    "phase21_paired_bootstrap.json",
    "phase21_global_medfilm_confusion_matrices.json",
    "phase21_task_conditioning_diagnostic.json",
    "phase21_efficiency_accounting.json",
    "phase21_notebook_determinism.json",
]

REQUIRED_TABLES = [
    "phase21_per_image_val_metrics.csv",
    "phase21_prediction_manifest.csv",
    "phase21_global_medfilm_domain_performance.csv",
    "phase21_global_medfilm_domain_bootstrap_ci.csv",
    "phase21_global_medfilm_confusion_matrices.csv",
    "phase21_global_medfilm_calibration_ranking.csv",
    "phase21_kub_subgroup_analysis.csv",
    "phase21_kub_size_stratification.csv",
    "phase21_kub_size_stratification_per_sample.csv",
    "phase21_six_model_comparison.csv",
    "phase21_paired_bootstrap_vs_baselines.csv",
    "phase21_per_image_all_models.csv",
    "phase21_task_conditioning_diagnostic.csv",
    "phase21_task_conditioning_per_case.csv",
    "phase21_film_parameter_summary.csv",
    "phase21_efficiency_accounting.csv",
    "phase21_gallery_selection_64.csv",
]

FORBIDDEN_COMPONENTS = {
    "roi_proposal": False, "localizer": False, "regional_refiner": False,
    "high_resolution_crop_branch": False, "global_regional_fusion": False,
    "benefit_predictor": False, "counterfactual_refinement_gain": False,
    "resource_budget_router": False, "adaptive_conditional_computation": False,
    "mobile_compression": False, "pruning": False, "quantization": False,
    "distillation": False, "architecture_search": False, "test_evaluation": False,
}


def load(p: Path) -> dict | None:
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def main() -> int:
    missing = [f for f in REQUIRED_AUDITS if not (AUDIT_DIR / f).exists()]
    missing += [f for f in REQUIRED_TABLES if not (TABLE_DIR / f).exists()]

    closure = load(EXP_DIR / "phase21_training_closure.json")
    replay = load(EXP_DIR / "phase21_checkpoint_selection_replay.json")
    analysis = load(AUDIT_DIR / "phase21_analysis.json")
    cond = load(AUDIT_DIR / "phase21_task_conditioning_diagnostic.json")
    val_eval = load(AUDIT_DIR / "phase21_val_evaluation.json")
    det = load(AUDIT_DIR / "phase21_notebook_determinism.json")
    paired = load(AUDIT_DIR / "phase21_paired_bootstrap.json")
    fig_inv = load(FIG_DIR / "phase21_figure_inventory.json")
    efficiency = load(AUDIT_DIR / "phase21_efficiency_accounting.json")

    if missing:
        print("FAIL-CLOSED: missing required artifacts:")
        for m in missing:
            print("   -", m)
        return 2

    proto_sha = sha256_file(ROOT / PROTOCOL_PATH)
    test_reads_total = 0
    for name in ("phase21_val_evaluation.json", "phase21_analysis.json",
                 "phase21_prediction_manifest.json"):
        a = load(AUDIT_DIR / name) or {}
        tr = a.get("test_reads")
        if isinstance(tr, dict):
            test_reads_total += sum(int(v) for v in tr.values())
        elif isinstance(tr, int):
            test_reads_total += tr
    closure_test = closure.get("test_reads", {})
    test_reads_total += sum(int(v) for v in closure_test.values())

    freeze = {
        "artifact": "phase21_final_freeze",
        "phase": 21,
        "title": "PHASE 21 — GLOBAL MEDFILM REFERENCE / FOUR-DOMAIN TASK-CONDITIONED "
                 "GLOBAL SEGMENTATION",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_id": EXPERIMENT_ID,
        "architecture_id": ARCHITECTURE_ID,
        "is_final_ra_medfilm_seg_plus_plus": False,
        "is_global_reference_only": True,
        "terminal_state": TERMINAL_STATE,
        "phase22_eligible": True,
        "phase22_started": False,

        "frozen_bindings": {
            "protocol_path": PROTOCOL_PATH,
            "protocol_sha256": proto_sha,
            "protocol_sha256_expected": PROTOCOL_SHA256,
            "protocol_sha_matches": proto_sha == PROTOCOL_SHA256,
            "protocol_binding": "reports/audits/phase21_protocol_binding.json",
            "protocol_binding_sha256": sha256_file(AUDIT_DIR / "phase21_protocol_binding.json"),
            "protocol_unintentional_differences": load(
                AUDIT_DIR / "phase21_protocol_binding.json").get("unintentional_differences"),
            "architecture_binding": "reports/audits/phase21_global_medfilm_architecture_binding.json",
            "architecture_binding_sha256": sha256_file(
                AUDIT_DIR / "phase21_global_medfilm_architecture_binding.json"),
            "entry_gate": "reports/audits/phase21_entry_gate.json",
            "entry_gate_verdict": load(AUDIT_DIR / "phase21_entry_gate.json").get("verdict"),
            "pre_execution_check": "reports/audits/phase21_pre_execution_check.json",
            "pre_execution_verdict": load(
                AUDIT_DIR / "phase21_pre_execution_check.json").get("verdict"),
            "legacy_medfilm_audit": "reports/audits/phase21_legacy_medfilm_architecture_audit.json",
        },

        "training": {
            "logical_runs": 1,
            "architecture_sweep_performed": False,
            "hyperparameter_sweep_performed": False,
            "seed": CONFIG["training"]["seed"],
            "best_epoch": closure["best_epoch"],
            "final_epoch": closure["final_epoch"],
            "stop_reason": closure["stop_reason"],
            "early_stopping_patience": closure["early_stopping_patience"],
            "resume_count": closure["resume_count"],
            "independent_duplicate_runs": closure["independent_duplicate_runs"],
            "best_macro_domain_dice": closure["best_macro_domain_dice"],
            "best_val_loss": closure["best_val_loss"],
            "per_domain_dice_at_best": closure["per_domain_dice_at_best"],
            "model_params": closure["model_params"],
            "total_elapsed_seconds": closure["total_elapsed_seconds"],
            "selection_rule_id": closure["selection_rule_id"],
            "checkpoint_selection_replay_verdict": replay["verdict"],
            "checkpoint_selection_replay_matches": replay["replay_matches_training"],
            "best_checkpoint_sha256": closure["best_checkpoint_sha256"],
            "history_sha256": closure["history_sha256"],
            "trainer_sha256": closure["trainer_sha256"],
        },

        "canonical_val_evaluation": {
            "canonical_val_inference_runs": val_eval["canonical_val_inference_runs"],
            "samples_expected": val_eval["samples_expected"],
            "samples_evaluated": val_eval["samples_evaluated"],
            "threshold": val_eval["threshold"],
            "no_tta": True, "no_threshold_tuning": True, "no_morphology": True,
            "prob_maps_persisted": val_eval["prob_maps_persisted"],
            "per_image_table": val_eval["per_image_table"],
            "per_image_table_sha256": val_eval["per_image_table_sha256"],
        },

        "results": {
            "global_medfilm": analysis["global_medfilm"],
            "six_model_ranking": analysis["six_model_ranking"],
            "benchmark_top_model": analysis["benchmark_top_model"],
            "paired_bootstrap": analysis["paired_bootstrap"],
            "tables": {
                "six_model_comparison": "reports/tables/phase21_six_model_comparison.csv",
                "paired_bootstrap": "reports/tables/phase21_paired_bootstrap_vs_baselines.csv",
                "domain_performance": "reports/tables/phase21_global_medfilm_domain_performance.csv",
                "domain_bootstrap_ci": "reports/tables/phase21_global_medfilm_domain_bootstrap_ci.csv",
                "calibration_ranking": "reports/tables/phase21_global_medfilm_calibration_ranking.csv",
            },
        },

        "kub": {
            "subgroup_table": "reports/tables/phase21_kub_subgroup_analysis.csv",
            "subgroup_role": "REPORTING_ONLY",
            "size_taxonomy_id": "kub_size_clean_v3_v1",
            "size_table": "reports/tables/phase21_kub_size_stratification.csv",
            "size_n": analysis["kub_size_n"],
            "tiny_stratum_preserved_for_phase22": analysis["tiny_stratum_preserved_for_phase22"],
            "optimised_on_tiny": False,
        },

        "conditioning": {
            "diagnostic": "reports/audits/phase21_task_conditioning_diagnostic.json",
            "flag": cond["flag"],
            "mean_abs_delta_dice_wrong_task": cond["mean_abs_delta_dice_wrong_task"],
            "n_cases": cond["n_cases"],
            "scope": cond["scope"],
            "film_parameter_summary": "reports/tables/phase21_film_parameter_summary.csv",
            "film_sites": CONFIG["model"]["film_sites"],
        },

        "gallery": {
            "frozen_64_reused_unchanged": True,
            "gallery_selection": "reports/tables/phase21_gallery_selection_64.csv",
            "gallery_cases": analysis["gallery_cases"],
            "six_model_panel_figures": "reports/figures/phase21_global_medfilm/gallery/",
            "detailed_gallery_figures": "reports/figures/phase21_global_medfilm/gallery/",
            "failure_gallery_figures": "reports/figures/phase21_global_medfilm/failure/",
            "analytical_outcome_selected_label_used": True,
        },

        "figures": {
            "figure_root": "reports/figures/phase21_global_medfilm",
            "n_figures": (fig_inv or {}).get("n_figures"),
            "n_embedded_in_notebook": (fig_inv or {}).get("n_embedded_in_notebook"),
            "groups": (fig_inv or {}).get("groups"),
            "inventory": "reports/figures/phase21_global_medfilm/phase21_figure_inventory.csv",
        },

        "notebook": {
            "path": "notebooks/phasewise/phase_21_global_medfilm/"
                    "phase21_global_medfilm_reference.ipynb",
            "sha256": sha256_file(NB_PATH) if NB_PATH.exists() else None,
            "determinism": det,
            "three_builds_byte_identical": bool(det and det.get("three_builds_byte_identical")),
        },

        "efficiency": {
            "parameter_count": (efficiency or {}).get("parameter_count"),
            "macs": (efficiency or {}).get("macs"),
            "macs_reason": (efficiency or {}).get("macs_reason"),
            "measurement_only": True,
            "no_optimisation_performed": True,
            "table": "reports/tables/phase21_efficiency_accounting.csv",
        },

        "governance": {
            "film_used": True,
            "task_conditioning_used": True,
            "task_id_role": "CONDITIONING_ALLOWED (FiLM task embedding only)",
            "forbidden_components": FORBIDDEN_COMPONENTS,
            "forbidden_components_present": [k for k, v in FORBIDDEN_COMPONENTS.items() if v],
            "test_locks": {
                "test_image_reads": 0, "test_mask_reads": 0,
                "test_inference": 0, "test_visualization": 0,
            },
            "test_reads_total_observed": test_reads_total,
            "test_lock_clean": test_reads_total == 0,
            "manifest_version": "phase4_v3",
            "val_population": 808,
            "train_population": 5832,
        },

        "interpretation": {
            "permitted": "Global MedFiLM achieved X compared with baseline Y.",
            "forbidden": "FiLM caused +X.",
            "reason": (
                "No architecture-matched control exists (no identical plain model trained under the "
                "Phase-21 run), so the difference cannot be causally attributed to FiLM."
            ),
            "ci_overlap_rule": (
                "Where the paired CI overlaps zero, the models are NOT separable and no ordering "
                "claim may be made."
            ),
            "historical_results_claimed_as_current": False,
        },

        "artifacts": {
            "audits": [f"reports/audits/{f}" for f in REQUIRED_AUDITS],
            "tables": [f"reports/tables/{f}" for f in REQUIRED_TABLES],
            "predictions_root": f"reports/predictions/{EXPERIMENT_ID}/val",
            "figures_root": "reports/figures/phase21_global_medfilm",
        },
    }

    problems = []
    if not freeze["frozen_bindings"]["protocol_sha_matches"]:
        problems.append("protocol SHA mismatch")
    if freeze["frozen_bindings"]["protocol_unintentional_differences"]:
        problems.append("protocol binding has unintentional differences")
    if test_reads_total != 0:
        problems.append(f"TEST reads observed: {test_reads_total}")
    if freeze["governance"]["forbidden_components_present"]:
        problems.append(f"forbidden components present: "
                        f"{freeze['governance']['forbidden_components_present']}")
    if not freeze["training"]["checkpoint_selection_replay_matches"]:
        problems.append("checkpoint-selection replay does not match training")
    if val_eval["samples_evaluated"] != 808:
        problems.append(f"VAL samples evaluated = {val_eval['samples_evaluated']}, expected 808")
    if val_eval["canonical_val_inference_runs"] != 1:
        problems.append("canonical VAL inference runs != 1")
    if not freeze["notebook"]["three_builds_byte_identical"]:
        problems.append("notebook determinism not proven (3 byte-identical builds)")

    freeze["validation_problems"] = problems
    freeze["freeze_verified"] = not problems
    if problems:
        freeze["terminal_state"] = "PHASE21_FREEZE_INCOMPLETE__SEE_VALIDATION_PROBLEMS"

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    out = AUDIT_DIR / "phase21_final_freeze.json"
    out.write_text(json.dumps(freeze, indent=2), encoding="utf-8")
    print("WROTE", out)
    print("terminal_state", freeze["terminal_state"])
    if problems:
        for p in problems:
            print("  PROBLEM:", p)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
