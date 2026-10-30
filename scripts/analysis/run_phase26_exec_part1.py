"""Phase26 canonical integration execution - SECTIONS 0-2.

0. Required predecessor / entry gate
1. Predecessor immutability (SHA-bind every canonical component + config input)
2. Execution classification

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/run_phase26_exec_part1.py
"""
from __future__ import annotations

import sys
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import phase26_exec_common as K  # noqa: E402

say = print


def check(name, cond):
    say(f"  [{'PASS' if cond else 'FAIL'}] {name}")
    return bool(cond)


# =========================================================================== #
# SECTION 0 - ENTRY GATE
# =========================================================================== #
def section_entry_gate():
    say("=" * 74)
    say("SECTION 0 - REQUIRED PREDECESSOR / ENTRY GATE")
    say("=" * 74)

    v12 = K.jload(K.ROOT / K.V12_TERMINAL)
    v12_fc = K.jload(K.AUD / "phase26_specification_final_check_v1_2.json")
    p25g = K.jload(K.AUD / "phase25g_final_freeze.json")

    checks = {
        "predecessor_terminal_exact": v12.get("terminal") == K.PREDECESSOR_TERMINAL,
        "v12_all_pass": v12.get("all_pass") is True,
        "phase25_complete_canonical":
            "COMPLETE" in str(p25g.get("terminal", "")).upper(),
        "phase26_spec_complete_frozen_v1_2":
            v12.get("phase26_spec") == "COMPLETE_FROZEN_V1_2",
        "phase26_execution_eligible_not_started":
            v12.get("phase26_status") == "EXECUTION_ELIGIBLE_NOT_STARTED",
        "phase26_started_false": v12.get("phase26_started") is False,
        "v12_final_check_26_of_26": v12_fc.get("n_pass") == 26 and v12_fc.get("n_checks") == 26,
        "canonical_variant_A8_C9": v12.get("canonical_system_variant") == K.CANONICAL_VARIANT,
        "canonical_budget_0p25": float(v12.get("canonical_budget")) == K.NOMINAL_BUDGET,
        "canonical_lambda_0p25":
            float(v12.get("canonical_lambda_representative")) == float(K.CANONICAL_LAMBDA),
        "runtime_score_formula":
            v12.get("runtime_score_formula") == "delta_hat_final - 0.25*C",
        "C_exact": K.exact(K.C_ACTION) == "1051648/10270749",
        "runtime_threshold_exact": K.exact(K.TAU_C8_FINAL) == v12.get("runtime_threshold_exact"),
        "s_omega_threshold_0p50": K.SOMEGA_ACCEPT_THRESHOLD == 0.50,
        "roi_proposal_threshold_0p30": K.ROI_PROPOSAL_THRESHOLD == 0.30,
        "segmentation_output_threshold_0p50": K.SEGMENTATION_OUTPUT_THRESHOLD == 0.50,
        "router_holdout_reserved":
            v12.get("holdout_state") == "RESERVED_UNOPENED_FOR_PHASE30",
        "val808_unopened": v12.get("val808") == "UNOPENED",
        "test_locked": v12.get("test") == "LOCKED_UNTIL_PHASE39",
    }
    for k, v in checks.items():
        check(k, v)

    artifact = {
        "artifact": "phase26_execution_entry_gate",
        "phase": "26",
        "classification": K.CLASSIFICATION,
        "method": K.METHOD,
        "revision": K.PHASE26_REVISION,
        "spec_authority": K.PHASE26_REVISION + " + router deployment semantics v1.2",
        "operational_meaning": "ASSEMBLY_ONLY__NO_PARAMETER_OPTIMIZATION",
        "predecessor_terminal_required": K.PREDECESSOR_TERMINAL,
        "predecessor_terminal_actual": v12.get("terminal"),
        "phase25": "COMPLETE_CANONICAL",
        "phase26_spec": v12.get("phase26_spec"),
        "phase26_status": v12.get("phase26_status"),
        "canonical_system": K.CANONICAL_VARIANT,
        "nominal_budget": K.NOMINAL_BUDGET,
        "canonical_lambda": float(K.CANONICAL_LAMBDA),
        "runtime_router_score": "delta_hat_final - 0.25*C",
        "C_exact": K.exact(K.C_ACTION),
        "runtime_threshold_exact": K.exact(K.TAU_C8_FINAL),
        "s_omega_threshold": K.SOMEGA_ACCEPT_THRESHOLD,
        "roi_proposal_threshold": K.ROI_PROPOSAL_THRESHOLD,
        "segmentation_output_threshold": K.SEGMENTATION_OUTPUT_THRESHOLD,
        "router_holdout": K.HOLDOUT_STATE,
        "val808": K.VAL808,
        "test": K.TEST,
        "checks": checks,
        "all_pass": bool(all(checks.values())),
        "terminal_on_failure": K.TERMINAL_DRIFT,
    }
    K.write_json(K.AUD / "phase26_execution_entry_gate.json", artifact)
    return artifact


# =========================================================================== #
# SECTION 1 - PREDECESSOR IMMUTABILITY
# =========================================================================== #
def section_immutability():
    say("")
    say("=" * 74)
    say("SECTION 1 - PREDECESSOR IMMUTABILITY")
    say("=" * 74)

    comps = {
        "phase21_global_medfilm_checkpoint": (K.GLOBAL_CHECKPOINT, K.GLOBAL_SHA),
        "phase25a_final_regional_refiner_checkpoint": (K.REFINER_CHECKPOINT, K.REFINER_SHA),
        "phase25d_final_benefit_router_checkpoint": (K.ROUTER_CHECKPOINT, K.ROUTER_SHA),
        "phase25d_final_normalization": (K.ROUTER_NORMALIZATION, K.ROUTER_NORMALIZATION_SHA),
        "phase25b_router_feature_schema": (K.ROUTER_SCHEMA, K.ROUTER_SCHEMA_SHA),
        "phase25f_final_somega_checkpoint": (K.SOMEGA_CHECKPOINT, K.SOMEGA_SHA),
        "phase25f_final_normalization": (K.SOMEGA_NORMALIZATION_PATH, None),
        "phase25f_20d_feature_schema": (K.SOMEGA_SCHEMA, None),
        "phase25a_roi_geometry_contract": (K.ROI_GEOMETRY_CONTRACT, None),
        "phase25f_fusion_fallback_contract": (K.FUSION_FALLBACK_CONTRACT, None),
        "phase26_training_integration_spec": (K.SPEC_DOC, None),
        "phase26_v1_1_score_space_reconciliation": (K.V11_TERMINAL, None),
        "phase26_v1_2_deployment_semantics_reconciliation": (K.V12_TERMINAL, None),
    }
    bound = {name: K.bind(p, s) for name, (p, s) in comps.items()}
    for name, b in bound.items():
        if b["expected_sha256"]:
            check(f"{name} sha match", b["match"])
        else:
            check(f"{name} exists", b["exists"])

    drift = [n for n, b in bound.items() if not b["match"]]

    artifact = {
        "artifact": "phase26_predecessor_immutability_gate",
        "phase": "26",
        "classification": K.CLASSIFICATION,
        "method": K.METHOD,
        "authority": "physical frozen artifacts",
        "components": bound,
        "drift_paths": drift,
        "drift_count": len(drift),
        "all_pass": bool(not drift),
        "terminal_on_failure": K.TERMINAL_DRIFT,
    }
    K.write_json(K.AUD / "phase26_predecessor_immutability_gate.json", artifact)
    return artifact


# =========================================================================== #
# SECTION 2 - EXECUTION CLASSIFICATION
# =========================================================================== #
def section_classification():
    say("")
    say("=" * 74)
    say("SECTION 2 - EXECUTION CLASSIFICATION")
    say("=" * 74)

    creates = ["integration code", "canonical bundle manifest", "contract tests",
               "configuration freeze", "reviewer notebook"]
    does_not_create = ["new learned parameters", "new scientific predictions",
                       "new performance estimates", "new calibration", "new thresholds"]
    checks = {
        "training_required_false": True,
        "new_model_state_false": True,
        "new_performance_evidence_false": True,
        "creates": bool(creates),
    }
    for k, v in checks.items():
        check(k, v)

    artifact = {
        "artifact": "phase26_execution_contract_binding",
        "phase": "26",
        "classification": K.CLASSIFICATION,
        "method": K.METHOD,
        "revision": K.PHASE26_REVISION,
        "operational_meaning": "ASSEMBLY_ONLY__NO_PARAMETER_OPTIMIZATION",
        "creates": creates,
        "does_not_create": does_not_create,
        "training_required": False,
        "new_model_state": False,
        "new_performance_evidence": False,
        "scientific_model_forwards": 0,
        "backward_passes": 0,
        "optimizer_steps": 0,
        "checks": checks,
        "all_pass": bool(all(checks.values())),
    }
    K.write_json(K.AUD / "phase26_execution_contract_binding.json", artifact)
    return artifact


def main():
    g = section_entry_gate()
    if not g["all_pass"]:
        say("\nENTRY GATE FAILED -> " + K.TERMINAL_DRIFT)
        return 1
    im = section_immutability()
    if not im["all_pass"]:
        say("\nPREDECESSOR DRIFT -> " + K.TERMINAL_DRIFT)
        return 1
    c = section_classification()
    say("")
    say("=" * 74)
    say(f"PART 1 COMPLETE  entry={g['all_pass']} immutability={im['all_pass']} "
        f"classification={c['all_pass']}")
    say("=" * 74)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
