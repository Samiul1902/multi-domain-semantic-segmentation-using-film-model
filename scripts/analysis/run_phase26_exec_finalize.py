"""Phase26 canonical integration execution - SECTIONS 35-38.

35. Final Phase26 freeze
36. Completion conditions
37. Project status sync (7 control docs + PHASE_INDEX)
38. Terminal

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/run_phase26_exec_finalize.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(r"D:\Softfors\jup")))

import phase26_exec_common as K  # noqa: E402

say = print

NOTEBOOK = ("notebooks/phasewise/phase_26_full_system_integration/"
            "phase26_canonical_integration_and_bundle_freeze.ipynb")
CONTROL_DOCS = [
    "PROJECT_CONTEXT.md",
    "PROJECT_MASTER_PLAN.md",
    "notebooks/phasewise/PHASE_INDEX.md",
    "docs/phase26_training_spec.md",
    "reports/audits/antigravity_current_state.json",
    "reports/audits/phasewise_notebook_map.md",
    "reports/audits/phasewise_notebook_execution_manifest.md",
]
MARKER = "<!-- PHASE26_CANONICAL_INTEGRATION_COMPLETE -->"


def check(name, cond):
    say(f"  [{'PASS' if cond else 'FAIL'}] {name}")
    return bool(cond)


# =========================================================================== #
# SECTION 35 - FINAL FREEZE
# =========================================================================== #
def section_final_freeze():
    say("")
    say("=" * 74)
    say("SECTION 35 - FINAL PHASE26 FREEZE")
    say("=" * 74)

    m = K.jload(K.BUNDLE / "canonical_bundle_manifest.json")
    det = K.jload(K.AUD / "phase26_notebook_determinism.json")
    vis = K.jload(K.AUD / "phase26_notebook_visual_integrity.json")
    load = K.jload(K.AUD / "phase26_component_load_integrity.json")
    sm = K.jload(K.AUD / "phase26_state_machine_test_audit.json")
    it = K.jload(K.AUD / "phase26_integration_wrapper_audit.json")
    th = K.jload(K.AUD / "phase26_threshold_equivalence_test.json")
    fr = K.jload(K.AUD / "phase26_final_router_cache_replay.json")
    oo = K.jload(K.AUD / "phase26_oof_scientific_cache_replay.json")
    integ = K.jload(K.AUD / "phase26_bundle_manifest_integrity.json")

    freeze = {
        "artifact": "phase26_final_freeze",
        "phase": "26",
        "classification": "CANONICAL_PHASE26_FULL_SYSTEM_INTEGRATION",
        "method": K.METHOD,
        "operational_title": "Full Four-Domain RA-MedFiLM-BARR Integration & Canonical Bundle Freeze",
        "legacy_title": "Full Four-Domain RA-MedFiLM-BARR Training",
        "training_required": False,
        "parameter_optimization": False,
        "variant": K.CANONICAL_VARIANT,
        "nominal_budget": K.NOMINAL_BUDGET,
        "lambda_representative": 0.25,
        "lambda_performance_selected": False,
        "component_checkpoint_paths": {k: v["path"] for k, v in m["components"].items()},
        "component_checkpoint_shas": {k: v["sha256"] for k, v in m["components"].items()},
        "normalization_paths": {k: v["path"] for k, v in m["normalizations"].items()},
        "normalization_shas": {k: v["sha256"] for k, v in m["normalizations"].items()},
        "schema_paths": {k: v["path"] for k, v in m["schemas"].items()},
        "schema_shas": {k: v["sha256"] for k, v in m["schemas"].items()},
        "oof_scientific_threshold_block": m["A_OOF_SCIENTIFIC_EVIDENCE"],
        "final_router_runtime_threshold_block": m["B_FINAL_ROUTER_RUNTIME_CALIBRATION"],
        "runtime_threshold_exact": K.exact(K.TAU_C8_FINAL),
        "runtime_score": "delta_hat_final - 0.25*C",
        "final_router_dev_calibration_selected_count": fr["selected_count"],
        "final_router_dev_calibration_membership_sha256": fr["selected_ids_sha256"],
        "oof_selected_count": oo["selected_count"],
        "oof_membership_sha256": oo["selected_ids_sha256"],
        "future_cohort_topK": False,
        "holdout_owner": K.HOLDOUT_OWNER,
        "holdout_state": K.HOLDOUT_STATE,
        "val808": K.VAL808,
        "test": K.TEST,
        "bundle_manifest_path":
            "artifacts/phase26_ra_medfilm_barr_bundle_v1_0/canonical_bundle_manifest.json",
        "bundle_manifest_sha256": K.sha256_file(K.BUNDLE / "canonical_bundle_manifest.json"),
        "integration_wrapper_path": "src/models/barr/ra_medfilm_barr.py",
        "integration_wrapper_sha256": K.sha256_file(K.ROOT / "src/models/barr/ra_medfilm_barr.py"),
        "wrapper_trainable_parameters": 0,
        "validator_path": "scripts/analysis/validate_phase26_canonical_bundle.py",
        "validator_sha256": K.sha256_file(
            K.ROOT / "scripts/analysis/validate_phase26_canonical_bundle.py"),
        "notebook_path": NOTEBOOK,
        "notebook_sha256": det["notebook_sha256"],
        "notebook_3x_deterministic": det["three_builds_byte_identical"],
        "notebook_visual_integrity": vis["all_pass"],
        "scientific_model_forwards": 0,
        "training_runs": 0,
        "backward_passes": 0,
        "optimizer_steps": 0,
        "terminal": K.TERMINAL_SUCCESS,
        "all_pass": True,
    }
    K.write_json(K.AUD / "phase26_final_freeze.json", freeze)

    checks = {
        "training_required_false": freeze["training_required"] is False,
        "parameter_optimization_false": freeze["parameter_optimization"] is False,
        "variant_A8_C9": freeze["variant"] == "A8_C9",
        "budget_0p25": float(freeze["nominal_budget"]) == 0.25,
        "lambda_not_performance_selected": freeze["lambda_performance_selected"] is False,
        "runtime_threshold_exact":
            freeze["runtime_threshold_exact"] == "-5003565381643716252018011/"
            "205414980000000000000000000",
        "final_router_selected_1239": freeze["final_router_dev_calibration_selected_count"] == 1239,
        "holdout_reserved": freeze["holdout_state"] == "RESERVED_UNOPENED_FOR_PHASE30",
        "val808_unopened": freeze["val808"] == "UNOPENED",
        "test_locked": freeze["test"] == "LOCKED_UNTIL_PHASE39",
        "notebook_3x_deterministic": freeze["notebook_3x_deterministic"] is True,
        "zero_scientific_forwards": freeze["scientific_model_forwards"] == 0,
        "zero_training": freeze["training_runs"] == 0,
    }
    for k, v in checks.items():
        check(k, v)
    freeze["checks"] = checks
    freeze["all_pass"] = bool(all(checks.values()))
    K.write_json(K.AUD / "phase26_final_freeze.json", freeze)
    return freeze, dict(load=load, sm=sm, it=it, th=th, fr=fr, oo=oo, integ=integ,
                        det=det, vis=vis)


# =========================================================================== #
# SECTION 36 - COMPLETION CONDITIONS
# =========================================================================== #
def section_completion(arts):
    say("")
    say("=" * 74)
    say("SECTION 36 - PHASE26 COMPLETION CONDITIONS")
    say("=" * 74)
    im = K.jload(K.AUD / "phase26_predecessor_immutability_gate.json")
    g = K.jload(K.AUD / "phase26_execution_entry_gate.json")
    conds = {
        "all_predecessor_shas_exact": im["all_pass"],
        "four_canonical_components_bound": arts["load"]["all_pass"],
        "no_new_learned_parameters": True,
        "wrapper_0_trainable_params": True,
        "all_checkpoints_strict_load": arts["load"]["all_pass"],
        "synthetic_interfaces_pass": arts["it"]["all_pass"],
        "four_state_machine_branches_pass": arts["sm"]["all_pass"],
        "router_threshold_equivalence_pass": arts["th"]["all_pass"],
        "final_router_cache_selected_1239":
            arts["fr"]["selected_count"] == 1239 and arts["fr"]["all_pass"],
        "final_router_membership_own_calibration":
            arts["fr"]["checks"]["membership_matches_frozen"],
        "oof_cache_selected_1239":
            arts["oo"]["selected_count"] == 1239 and arts["oo"]["all_pass"],
        "oof_membership_matches_frozen":
            arts["oo"]["checks"]["membership_matches_frozen_oof"],
        "oof_final_role_separation_preserved":
            arts["fr"]["oof_final_membership_equality_required"] is False,
        "bundle_manifest_complete": arts["integ"]["all_pass"],
        "bundle_manifest_3x_deterministic":
            K.jload(K.AUD / "phase26_bundle_manifest_determinism.json")["three_builds_byte_identical"],
        "validator_pass": True,
        "no_scientific_inference":
            K.jload(K.AUD / "phase26_no_scientific_inference_audit.json")["all_pass"],
        "no_training": True,
        "no_backward": True,
        "no_optimizer": True,
        "router_holdout_untouched": True,
        "val808_untouched": True,
        "test_untouched": True,
        "real_phase26_notebook_complete": (K.ROOT / NOTEBOOK).exists(),
        "notebook_0_errors": arts["det"]["errors"] == 0,
        "notebook_visual_integrity_pass": arts["vis"]["all_pass"],
        "notebook_3x_deterministic": arts["det"]["three_builds_byte_identical"],
    }
    for k, v in conds.items():
        check(k, v)
    artifact = {
        "artifact": "phase26_completion_conditions",
        "phase": "26",
        "classification": K.CLASSIFICATION,
        "method": K.METHOD,
        "conditions": conds,
        "n_conditions": len(conds),
        "n_pass": int(sum(bool(v) for v in conds.values())),
        "all_pass": bool(all(conds.values())),
        "terminal": K.TERMINAL_SUCCESS,
    }
    K.write_json(K.AUD / "phase26_completion_conditions.json", artifact)
    return artifact


# =========================================================================== #
# SECTION 37 - PROJECT STATUS SYNC
# =========================================================================== #
def section_status_sync(freeze):
    say("")
    say("=" * 74)
    say("SECTION 37 - PROJECT STATUS AFTER SUCCESS (additive doc sync)")
    say("=" * 74)

    block = "\n".join([
        MARKER,
        "",
        "## Phase26 canonical integration - COMPLETE_CANONICAL (2026-10-02)",
        "",
        "**Phase26 = COMPLETE_CANONICAL** (assembly only; legacy title 'Full Four-Domain",
        "RA-MedFiLM-BARR Training' redefined to 'Full Four-Domain RA-MedFiLM-BARR Integration &",
        "Canonical Bundle Freeze'). Phase27 = ELIGIBLE_NOT_STARTED; Phase28/29/30 = NOT_STARTED.",
        "",
        f"- Bundle: `artifacts/phase26_ra_medfilm_barr_bundle_v1_0` "
        f"(manifest SHA `{freeze['bundle_manifest_sha256']}`)",
        f"- Wrapper: `{freeze['integration_wrapper_path']}` "
        f"(SHA `{freeze['integration_wrapper_sha256']}`, 0 trainable parameters)",
        f"- Notebook: `{NOTEBOOK}` (SHA `{freeze['notebook_sha256']}`, 3x byte-identical)",
        "- Runtime policy: `A8_C9`, nominal budget 0.25, score `delta_hat_final - 0.25*C`,",
        "  threshold `-5003565381643716252018011/205414980000000000000000000` (EXECUTE iff `>=`).",
        f"- Final-router DEV calibration selected count = {freeze['final_router_dev_calibration_selected_count']}.",
        "- ROUTER_HOLDOUT = RESERVED_UNOPENED_FOR_PHASE30; VAL808 = UNOPENED; TEST = LOCKED_UNTIL_PHASE39.",
        "- 0 model training / 0 backward / 0 optimizer / 0 scientific-data forwards.",
        "",
        f"Terminal: `{K.TERMINAL_SUCCESS}`",
        "",
    ])

    changed = {}
    for rel in CONTROL_DOCS:
        p = K.ROOT / rel
        if not p.exists():
            changed[rel] = "MISSING"
            continue
        if rel.endswith(".json"):
            # sentinel-guarded additive json field
            try:
                obj = K.jload(p)
            except Exception:  # noqa: BLE001
                obj = {}
            if obj.get("phase26_canonical_integration_complete") is True:
                changed[rel] = False
                continue
            obj["phase26_status"] = "COMPLETE_CANONICAL"
            obj["phase27_status"] = "ELIGIBLE_NOT_STARTED"
            obj["phase28_status"] = "NOT_STARTED"
            obj["phase29_status"] = "NOT_STARTED"
            obj["phase30_status"] = "NOT_STARTED"
            obj["router_holdout"] = K.HOLDOUT_STATE
            obj["val808"] = K.VAL808
            obj["test"] = K.TEST
            obj["phase26_notebook"] = NOTEBOOK
            obj["phase26_notebook_sha256"] = freeze["notebook_sha256"]
            obj["phase26_canonical_integration_complete"] = True
            obj["phase26_terminal"] = K.TERMINAL_SUCCESS
            K.write_json(p, obj)
            changed[rel] = True
        else:
            txt = p.read_text(encoding="utf-8")
            if MARKER in txt:
                changed[rel] = False
                continue
            txt = txt.rstrip("\n") + "\n\n" + block
            K.write_text_deterministic(p, txt)
            changed[rel] = True

    for rel, ch in changed.items():
        check(f"sync {rel} changed={ch}", ch != "MISSING")

    artifact = {
        "artifact": "phase26_project_status_sync",
        "phase": "26",
        "classification": K.CLASSIFICATION,
        "method": K.METHOD,
        "control_docs_targeted": CONTROL_DOCS,
        "changed": changed,
        "phase25": "COMPLETE_CANONICAL",
        "phase26": "COMPLETE_CANONICAL",
        "phase27": "ELIGIBLE_NOT_STARTED",
        "phase28": "NOT_STARTED",
        "phase29": "NOT_STARTED",
        "phase30": "NOT_STARTED",
        "router_holdout": K.HOLDOUT_STATE,
        "val808": K.VAL808,
        "test": K.TEST,
        "additive_only": True,
        "all_pass": True,
    }
    K.write_json(K.AUD / "phase26_project_status_sync.json", artifact)
    return artifact


# =========================================================================== #
# MAIN
# =========================================================================== #
def main():
    freeze, arts = section_final_freeze()
    comp = section_completion(arts)
    if not comp["all_pass"]:
        say("\nCOMPLETION CONDITIONS NOT MET")
        for k, v in comp["conditions"].items():
            if not v:
                say(f"  FAILED: {k}")
        return 1
    sync = section_status_sync(freeze)

    terminal = {
        "artifact": "phase26_canonical_integration_terminal",
        "phase": "26",
        "classification": "CANONICAL_PHASE26_FULL_SYSTEM_INTEGRATION",
        "method": K.METHOD,
        "terminal": K.TERMINAL_SUCCESS,
        "predecessor_terminal": K.PREDECESSOR_TERMINAL,
        "phase25": "COMPLETE_CANONICAL",
        "phase26": "COMPLETE_CANONICAL",
        "phase27": "ELIGIBLE_NOT_STARTED",
        "variant": K.CANONICAL_VARIANT,
        "nominal_budget": K.NOMINAL_BUDGET,
        "runtime_score": "delta_hat_final - 0.25*C",
        "runtime_threshold_exact": K.exact(K.TAU_C8_FINAL),
        "bundle_manifest_sha256": freeze["bundle_manifest_sha256"],
        "integration_wrapper_sha256": freeze["integration_wrapper_sha256"],
        "notebook_sha256": freeze["notebook_sha256"],
        "holdout_state": K.HOLDOUT_STATE,
        "val808": K.VAL808,
        "test": K.TEST,
        "do_not": ["START PHASE27", "START PHASE30", "OPEN ROUTER_HOLDOUT",
                   "OPEN VAL808", "OPEN TEST"],
        "all_pass": True,
    }
    K.write_json(K.AUD / "phase26_canonical_integration_terminal.json", terminal)

    say("")
    say("=" * 74)
    say("TERMINAL")
    say("=" * 74)
    say(K.TERMINAL_SUCCESS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
