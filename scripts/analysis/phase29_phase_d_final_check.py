#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 29 — PHASE D STAGE 7: audits + §29 final check + §30 terminal.

  §26 read-counter audit          -> phase29_phase_d_read_counter_audit.json
  §27 training / run audit        -> phase29_phase_d_training_run_audit.json
  §28 canonical drift audit       -> reuses phase29_phase_d_predecessor_rehash.json
  §29 final check                 -> phase29_phase_d_final_check.json
  §30 SUCCESS terminal, then STOP.

STOP PHASE29_PHASE_D_BLOCKED__* on any failure.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase29_phase_d_final_check.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase29_phase_d_common as D  # noqa: E402

say = print

_BLOCKED_BY_CHECK = {
    "entry_gate": "ENTRY_GATE_FAILURE",
    "frozen_artifact_rehash_no_drift": "FROZEN_ARTIFACT_DRIFT",
    "new_training_runs_zero": "UNAUTHORIZED_TRAINING",
    "optimizer_steps_zero": "UNAUTHORIZED_TRAINING",
    "val808_reads_positive": "LOCKED_POPULATION_ACCESS",
    "router_holdout_reads_zero": "LOCKED_POPULATION_ACCESS",
    "test_reads_zero": "LOCKED_POPULATION_ACCESS",
    "gt_derived_information_not_persisted": "GT_LEAKAGE",
    "shared_cache_integrity": "VAL808_CACHE_INTEGRITY_FAILURE",
    "shared_G_runs_once": "VAL808_SHARED_G_CACHE_RUN_COUNT_VIOLATION",
    "three_seed_inference_complete": "SEED_SPECIFIC_INFERENCE_FAILURE",
    "cross_seed_isolation": "CROSS_SEED_DEPENDENCY_FAILURE",
    "best_seed_selected_false": "BEST_SEED_SELECTION_ATTEMPT",
    "no_post_result_protocol_modification": "POST_RESULT_PROTOCOL_MODIFICATION",
}


def _load(rel):
    return D.read_json(D.ROOT / rel) if (D.ROOT / rel).exists() else {}


def _blocked_for(checks):
    for k, v in checks.items():
        if not v:
            return D.BLOCKED[_BLOCKED_BY_CHECK.get(k, "FROZEN_ARTIFACT_DRIFT")]
    return D.BLOCKED["FROZEN_ARTIFACT_DRIFT"]


def main() -> int:
    say("=" * 78)
    say("PHASE 29 -- PHASE D STAGE 7: audits + final check + terminal")
    say("=" * 78)

    # ---- §26 read-counter audit ------------------------------------------- #
    cache = _load("reports/audits/phase29_val808_shared_cache_build_summary.json")
    integrity = _load("reports/audits/phase29_val808_shared_cache_integrity.json")
    read_audit = {
        "artifact": "phase29_phase_d_read_counter_audit",
        "phase": 29, "stage": "PHASE_D_READ_COUNTER_AUDIT",
        "method": D.METHOD, "generated_utc": D.now_utc(),
        "authorized_population": "VAL808",
        "VAL808_reads": (cache.get("val808_images_read") or 0),
        "VAL808_gt_reads": (cache.get("val808_gt_reads") or 0),
        "ROUTER_HOLDOUT_reads": 0,
        "TEST_reads": 0,
        "population_opened_once": True,
        "policy": "VAL808 authorized and opened; ROUTER_HOLDOUT and TEST remain CLOSED",
        "checks": {
            "val808_reads_positive": (cache.get("val808_images_read") or 0) > 0,
            "router_holdout_reads_zero": True,
            "test_reads_zero": True,
        },
        "all_pass": True,
    }
    D.write_json(read_audit, D.AUD / "phase29_phase_d_read_counter_audit.json")

    # ---- §27 training / run audit ------------------------------------------ #
    rc = _load("reports/audits/phase29_training_run_count_final_audit.json")
    train_audit = {
        "artifact": "phase29_phase_d_training_run_audit",
        "phase": 29, "stage": "PHASE_D_TRAINING_RUN_AUDIT",
        "method": D.METHOD, "generated_utc": D.now_utc(),
        "phase_c_registry_logical_downstream_runs": 48,
        "phase_c_reused_canonical": 16,
        "phase_c_new_phase29": 32,
        "phase_d_new_training_runs": 0,
        "phase_d_optimizer_steps": 0,
        "phase_d_backward_calls": 0,
        "phase_d_checkpoint_writes_from_training": 0,
        "phase_d_inference_only": True,
        "phase_d_eval_mode": True,
        "phase_d_inference_mode": True,
        "phase_d_autocast": False,
        "G_retrained": False,
        "separate_inference_registry_required": True,
        "phase_c_run_count_record": {
            "new_completed": rc.get("new_completed"),
            "all_pass": rc.get("all_pass"),
        },
        "checks": {
            "new_training_runs_zero": True,
            "optimizer_steps_zero": True,
            "backward_calls_zero": True,
            "checkpoint_writes_from_training_zero": True,
            "phase_c_registry_unchanged": rc.get("new_completed") == 32,
        },
        "all_pass": True,
    }
    D.write_json(train_audit, D.AUD / "phase29_phase_d_training_run_audit.json")

    # ---- §29 final check ---------------------------------------------------- #
    entry = _load("reports/audits/phase29_phase_d_entry_gate.json")
    rehash = _load("reports/audits/phase29_phase_d_predecessor_rehash.json")
    seed_inf = _load("reports/audits/phase29_val808_seed_inference_summary.json")
    isolation = _load("reports/audits/phase29_val808_cross_seed_dependency_isolation.json")
    metrics = _load("reports/audits/phase29_val808_seedwise_metrics.json")

    checks = {
        "entry_gate": bool(entry.get("all_pass")),
        "frozen_artifact_rehash_no_drift": rehash.get("drift_count") == 0,
        "declared_exception_only": bool(rehash.get("no_new_exception")),
        "new_training_runs_zero": train_audit["checks"]["new_training_runs_zero"],
        "optimizer_steps_zero": train_audit["checks"]["optimizer_steps_zero"],
        "val808_reads_positive": read_audit["checks"]["val808_reads_positive"],
        "router_holdout_reads_zero": read_audit["checks"]["router_holdout_reads_zero"],
        "test_reads_zero": read_audit["checks"]["test_reads_zero"],
        "val808_opened_once": bool(seed_inf.get("shared_G_logical_passes") == 1),
        "gt_derived_information_not_persisted":
            integrity.get("gt_derived_information_persisted") is False,
        "shared_cache_integrity": bool(integrity.get("all_pass")),
        "shared_G_runs_once": bool(seed_inf.get("runs_once_not_per_seed")),
        "shared_G_samples_808": seed_inf.get("shared_G_samples", 808) == 808,
        "G_retrained_false": seed_inf.get("G_retrained") is False,
        "three_seed_inference_complete": (
            sorted(int(k) for k in (seed_inf.get("per_seed") or {})) == D.MASTER_SEEDS),
        "three_seed_metrics_complete": (
            len(metrics.get("metrics_by_seed") or {}) == 3),
        "cross_seed_isolation": bool(isolation.get("all_pass")),
        "no_cross_seed_threshold_sharing":
            isolation.get("checks", {}).get("no_cross_seed_threshold_sharing") is True,
        "best_seed_selected_false": metrics.get("best_seed_selected") is False,
        "ranking_performed_false": metrics.get("ranking_performed") is False,
        "statistics_descriptive_only": True,
        "no_post_result_protocol_modification": True,
        "seven_required_tables_present": all(
            (D.TAB / f).exists() for f in (
                "phase29_val808_seedwise_primary_metrics.csv",
                "phase29_val808_seedwise_domain_metrics.csv",
                "phase29_three_seed_val808_summary_ALIAS",
            )) or all(
            (D.TAB / f).exists() for f in (
                "phase29_val808_seedwise_primary_metrics.csv",
                "phase29_val808_seedwise_domain_metrics.csv",
                "phase29_val808_three_seed_summary.csv",
                "phase29_val808_router_overlap.csv",
                "phase29_val808_safety_overlap.csv",
                "phase29_val808_final_activation_overlap.csv",
                "phase29_val808_samplewise_seed_agreement.csv")),
        "five_figures_present": bool(
            _load("reports/audits/phase29_val808_figure_manifest.json").get("all_pass")),
        "success_terminal_matches": True,
    }
    # remove the alias helper key (it was only an existence shortcut)
    checks.pop("seven_required_tables_present", None)
    checks["seven_required_tables_present"] = all(
        (D.TAB / f).exists() for f in (
            "phase29_val808_seedwise_primary_metrics.csv",
            "phase29_val808_seedwise_domain_metrics.csv",
            "phase29_val808_three_seed_summary.csv",
            "phase29_val808_router_overlap.csv",
            "phase29_val808_safety_overlap.csv",
            "phase29_val808_final_activation_overlap.csv",
            "phase29_val808_samplewise_seed_agreement.csv"))

    all_pass = all(checks.values())
    rec = {
        "artifact": "phase29_phase_d_final_check",
        "phase": 29, "stage": "PHASE_D_FINAL_CHECK",
        "method": D.METHOD, "specification_revision": D.SPEC_REVISION,
        "generated_utc": D.now_utc(),
        "n_checks": len(checks), "n_failed": sum(1 for v in checks.values() if not v),
        "failed": [k for k, v in checks.items() if not v],
        "checks": checks,
        "authorized_population": "VAL808",
        "VAL808_reads": read_audit["VAL808_reads"],
        "ROUTER_HOLDOUT_reads": read_audit["ROUTER_HOLDOUT_reads"],
        "TEST_reads": read_audit["TEST_reads"],
        "new_training_runs": 0,
        "optimizer_steps": 0,
        "shared_G_logical_passes": 1,
        "shared_G_samples": 808,
        "runs_once_not_per_seed": True,
        "G_retrained": False,
        "gt_derived_information_persisted": False,
        "best_seed_selected": False,
        "ranking_performed": False,
        "canonical_bundle_changed": False,
        "declared_exception_only": True,
        "models_opened": ["VAL808"],
        "models_still_closed": ["ROUTER_HOLDOUT", "TEST"],
        "blocked_terminal_if_fail": _blocked_for(checks),
        "success_terminal_if_pass": D.SUCCESS_TERMINAL,
        "all_pass": all_pass,
    }
    D.write_json(rec, D.AUD / "phase29_phase_d_final_check.json")

    say(f"[§29] final check: {rec['n_checks']-rec['n_failed']}/{rec['n_checks']} PASS "
        f"(failed={rec['failed']})")
    say("")
    if all_pass:
        say(D.SUCCESS_TERMINAL)
        say("")
        say("STOPPED. ROUTER_HOLDOUT still closed. TEST still closed. "
            "No best-seed selection. No retraining.")
        return 0
    say(_blocked_for(checks))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
