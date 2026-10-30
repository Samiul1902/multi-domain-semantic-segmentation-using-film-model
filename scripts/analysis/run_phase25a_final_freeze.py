"""Phase 25A — FINAL FREEZE.

Collects every Phase-25A artifact, proves the frozen predecessors are byte-identical,
proves TEST stayed closed and no outcome leakage occurred, verifies the reviewer
notebook is 3x byte-identical, and emits the Phase-25A terminal state.

Writes:
    reports/audits/phase25a_final_freeze.json

Usage:
    ./.venv/Scripts/python.exe scripts/analysis/run_phase25a_final_freeze.py
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
FIG = ROOT / "reports" / "figures" / "phase25a_regional_refiner"
NB = (ROOT / "notebooks" / "phasewise" / "phase_25a_regional_refiner"
      / "phase25a_dedicated_regional_refiner.ipynb")
UTC = datetime.now(timezone.utc).isoformat()

TERMINAL = "PHASE25A_DEDICATED_REGIONAL_REFINER_COMPLETE__PHASE25B_ELIGIBLE_NOT_STARTED"

# frozen predecessors — MUST remain byte-identical
PREDECESSORS = {
    "phase21_global_medfilm_best_pt": (
        ROOT / "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt",
        "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7"),
    "phase22_diagnostic_protocol": (
        AUD / "phase22_diagnostic_protocol.json",
        "9d620d6c85276e1a9a086ec60172cdef3b94dc58fe8288222378d196dd4609b7"),
    "phase24_reviewer_notebook": (
        ROOT / "notebooks/phasewise/phase_24_architecture_spec"
              "/phase24_narrowed_benefit_aware_refinement_spec.ipynb",
        "612d71700c1c1a45b94b8fcb8a3ff427bf32f6f6453130febeec49c6ec78caef"),
    "phase24_router_split_manifest": (
        AUD / "phase24_router_split_manifest.csv",
        "b5da52d6220ef9b59b4ba70d0b403b38bf5234b897615b6ad55d718114db6555"),
}

REQUIRED_AUDITS = [
    "phase25a_entry_gate.json",
    "phase25a_phase24_v1_1_binding.json",
    "phase25a_data_split_binding.json",
    "phase25a_global_checkpoint_binding.json",
    "phase25a_augmentation_binding.json",
    "phase25a_roi_transform_audit.json",
    "phase25a_refiner_architecture_binding.json",
    "phase25a_crossfit_protocol.json",
    "phase25a_global_cache_provenance.json",
    "phase25a_resource_accounting.json",
    "phase25a_final_refit_epoch_rule.json",
    "phase25a_training_run_registry.json",
    "phase25a_training_health.json",
    "phase25a_checkpoint_integrity.json",
    "phase25a_no_outcome_leakage_audit.json",
    "phase25a_test_lock_audit.json",
    "phase25a_implementation_test_suite.json",
    "phase25a_notebook_visual_integrity.json",
    "phase25a_notebook_visual_determinism.json",
]

REQUIRED_TABLES = [
    "phase25a_population_accounting.csv",
    "phase25a_action_availability_by_domain.csv",
    "phase25a_crossfit_fold_manifest_summary.csv",
    "phase25a_resource_accounting.csv",
    "phase25a_refiner_selected_epochs.csv",
    "phase25a_training_epochs_fold0.csv",
    "phase25a_training_epochs_fold1.csv",
    "phase25a_training_epochs_fold2.csv",
    "phase25a_training_epochs_final.csv",
    "phase25a_run_summary.csv",
]

REQUIRED_FIGURES = [
    "p25a_fold0_loss_curve.png", "p25a_fold1_loss_curve.png", "p25a_fold2_loss_curve.png",
    "p25a_fold_training_comparison.png", "p25a_best_epoch_summary.png",
    "p25a_final_refit_training_curve.png", "p25a_action_availability_by_domain.png",
    "p25a_refiner_architecture_summary.png",
]


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def jload(p: Path) -> dict:
    p = Path(p)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def main() -> int:
    checks: list[dict] = []

    def chk(name: str, ok: bool, observed=None, expected=None) -> None:
        entry = {"check": name, "pass": bool(ok)}
        if observed is not None:
            entry["observed"] = observed
        if expected is not None:
            entry["expected"] = expected
        checks.append(entry)

    # ---- artifacts present ------------------------------------------------ #
    audit_shas, missing_audits = {}, []
    for n in REQUIRED_AUDITS:
        p = AUD / n
        if p.exists():
            audit_shas[n] = sha(p)
        else:
            missing_audits.append(n)
    chk("all_19_required_audits_present", not missing_audits, missing_audits, [])

    table_shas, missing_tables = {}, []
    for n in REQUIRED_TABLES:
        p = TAB / n
        if p.exists():
            table_shas[n] = sha(p)
        else:
            missing_tables.append(n)
    chk("all_10_required_tables_present", not missing_tables, missing_tables, [])

    fig_shas, missing_figs = {}, []
    for n in REQUIRED_FIGURES:
        p = FIG / n
        if p.exists() and p.stat().st_size > 2048:
            fig_shas[n] = sha(p)
        else:
            missing_figs.append(n)
    chk("all_8_required_figures_present", not missing_figs, missing_figs, [])

    # ---- predecessors byte-identical -------------------------------------- #
    pred_obs = {}
    pred_ok = True
    for name, (p, expected) in PREDECESSORS.items():
        actual = sha(p) if p.exists() else None
        same = actual == expected
        pred_ok = pred_ok and same
        pred_obs[name] = {"exists": p.exists(), "sha256": actual, "expected": expected,
                          "unchanged": same}
    chk("frozen_predecessors_unchanged", pred_ok, pred_obs)

    # ---- training completeness -------------------------------------------- #
    reg = jload(AUD / "phase25a_training_run_registry.json")
    chk("four_primary_runs_complete",
        reg.get("n_runs_complete") == 4 and reg.get("extra_primary_runs") == 0,
        reg.get("n_runs_complete"), 4)

    health = jload(AUD / "phase25a_training_health.json")
    chk("training_health_pass",
        health.get("verdict") == "PHASE25A_TRAINING_HEALTH_PASS", health.get("verdict"),
        "PHASE25A_TRAINING_HEALTH_PASS")

    integ = jload(AUD / "phase25a_checkpoint_integrity.json")
    chk("checkpoint_integrity_pass",
        integ.get("verdict") == "PHASE25A_CHECKPOINT_INTEGRITY_PASS", integ.get("verdict"),
        "PHASE25A_CHECKPOINT_INTEGRITY_PASS")

    rule = jload(AUD / "phase25a_final_refit_epoch_rule.json")
    chk("final_refit_epoch_rule_frozen",
        bool(rule.get("fold_best_epochs")) and rule.get("final_refit_epochs") is not None,
        rule.get("final_refit_epochs"))

    # ---- leakage / TEST ---------------------------------------------------- #
    leak = jload(AUD / "phase25a_no_outcome_leakage_audit.json")
    chk("no_outcome_leakage_pass",
        leak.get("verdict") == "PHASE25A_NO_OUTCOME_LEAKAGE_PASS", leak.get("verdict"),
        "PHASE25A_NO_OUTCOME_LEAKAGE_PASS")

    tl = jload(AUD / "phase25a_test_lock_audit.json")
    chk("test_lock_pass", tl.get("verdict") == "PHASE25A_TEST_LOCK_PASS",
        tl.get("verdict"), "PHASE25A_TEST_LOCK_PASS")
    chk("test_reads_zero", tl.get("test_reads") == 0, tl.get("test_reads"), 0)

    its = jload(AUD / "phase25a_implementation_test_suite.json")
    chk("implementation_test_suite_pass", its.get("n_failed") == 0 and its.get("n_checks", 0) > 0,
        {"n_checks": its.get("n_checks"), "n_failed": its.get("n_failed")})

    arch = jload(AUD / "phase25a_refiner_architecture_binding.json")
    chk("architecture_gate_pass",
        arch.get("verdict") == "PHASE25A_REFINER_ARCHITECTURE_FROZEN",
        arch.get("verdict"), "PHASE25A_REFINER_ARCHITECTURE_FROZEN")
    chk("parameter_count_exact_1276401",
        arch.get("parameter_count") == 1_276_401, arch.get("parameter_count"), 1_276_401)

    res = jload(AUD / "phase25a_resource_accounting.json")
    chk("resource_accounting_present",
        res.get("trainable_parameters") == 1_276_401, res.get("trainable_parameters"), 1_276_401)

    # ---- notebook ---------------------------------------------------------- #
    det = jload(AUD / "phase25a_notebook_visual_determinism.json")
    chk("notebook_3x_byte_identical", det.get("byte_identical") is True,
        det.get("n_distinct_sha256"), 1)
    vis = jload(AUD / "phase25a_notebook_visual_integrity.json")
    chk("notebook_visual_integrity_pass",
        vis.get("n_corrupt") == 0 and vis.get("n_missing") == 0,
        {"corrupt": vis.get("n_corrupt"), "missing": vis.get("n_missing")})

    nb_sha = sha(NB) if NB.exists() else None
    chk("reviewer_notebook_exists", NB.exists(), nb_sha)

    # ---- scope guards ------------------------------------------------------ #
    scope = jload(AUD / "phase25a_scope_guard.json")
    chk("router_not_trained", leak.get("benefit_router_training_runs") == 0,
        leak.get("benefit_router_training_runs"), 0)
    chk("no_paired_gain_labels", leak.get("paired_gain_labels_created") is False,
        leak.get("paired_gain_labels_created"))
    chk("holdout_outcomes_not_inspected",
        leak.get("router_holdout", {}).get("holdout_outcomes_inspected") is False)
    chk("val_not_evaluated", leak.get("existing_val", {}).get("outcome_evaluation") == 0)
    chk("phase25b_not_started", not scope.get("phase25b_started", False))
    chk("phase25c_not_started", not scope.get("phase25c_started", False))
    chk("phase25d_not_started", not scope.get("phase25d_started", False))

    n_fail = sum(1 for c in checks if not c["pass"])
    freeze = {
        "artifact": "phase25a_final_freeze",
        "phase": "25A",
        "module": "R_psi (dedicated crop-trained regional refiner)",
        "method": "RA-MedFiLM-BARR",
        "architecture_id": "ra_medfilm_barr_narrowed_v1_1",
        "architecture_revision_status": "ra_medfilm_barr_narrowed_v1_1",
        "classification": "IMPLEMENTATION_AND_TRAINING_PHASE",
        "science_changed": False,
        "n_checks": len(checks), "n_passed": len(checks) - n_fail, "n_failed": n_fail,
        "verdict": ("PHASE25A_FINAL_FREEZE_PASS" if n_fail == 0
                    else "PHASE25A_FINAL_FREEZE_FAIL"),
        "terminal": TERMINAL if n_fail == 0 else None,
        "checks": checks,
        "artifact_sha256": {
            "audits": audit_shas, "tables": table_shas, "figures": fig_shas,
            "reviewer_notebook": nb_sha,
        },
        "frozen_predecessors": pred_obs,
        "parameters": {
            "refiner_trainable": res.get("trainable_parameters"),
            "refiner_hard_ceiling": 2_000_000,
            "global_anchor": 3_523_001,
        },
        "resource": {
            "analytical_macs": res.get("analytical_macs"),
            "analytical_gmacs": res.get("analytical_gmacs"),
            "analytical_flops": res.get("analytical_flops"),
            "latency_note": "host-specific, not a deployment claim",
        },
        "test_reads": 0,
        "generated_utc": UTC,
    }
    (AUD / "phase25a_final_freeze.json").write_text(
        json.dumps(freeze, indent=1) + "\n", encoding="utf-8")

    for c in checks:
        print(f"  [{'PASS' if c['pass'] else 'FAIL'}] {c['check']}")
    print(f"\n{len(checks) - n_fail}/{len(checks)} final-freeze checks passed")
    print(f"reviewer notebook sha256: {nb_sha}")
    if n_fail == 0:
        print(TERMINAL)
    else:
        print("PHASE25A_FINAL_FREEZE_BLOCKED")
    return 0 if n_fail == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
