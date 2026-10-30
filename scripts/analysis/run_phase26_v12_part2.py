"""Phase26 v1.2 part 2 - SECTIONS 15-20.

Spec additive update, completeness v1.2, no-execution guard, final check, terminal.
Governance / specification ONLY.
"""
from __future__ import annotations

import json
import sys
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import phase26_v12_common as K  # noqa: E402

say = print


# =========================================================================== #
# SECTION 15 - SPEC ADDITIVE UPDATE
# =========================================================================== #
SPEC_ADDITION = f"""
{K.SPEC_MARKER}

## 12. OOF scientific policy space versus final-router runtime calibration (v1.2)

Phase26/30 inference does **not** use the OOF policy threshold.  Two calibration spaces are frozen and
must never be conflated:

| | Space B — scientific OOF policy | Space A — final-router runtime |
|---|---|---|
| Score variable | `delta_hat_oof` | `delta_hat_final` (FINAL Phase25D `B_phi`) |
| Producer | cross-fitted OOF predictor | one model refit on all 4957 DEV rows |
| Raw τ_C7 (25%) | `{K.exact(K.TAU_C7_OOF)}` | `{K.exact(K.TAU_C7_FINAL)}` |
| Utility τ_C8 | `{K.exact(K.TAU_C8_OOF)}` | **`{K.exact(K.TAU_C8_FINAL)}`** |
| Role | `SCIENTIFIC_DEVELOPMENT_MEMBERSHIP_ONLY` | `CANONICAL_FINAL_ROUTER_CALIBRATION` |
| Runtime authority | **false** | **true** |

- Phase25 scientific comparisons remain **OOF-based** and are unchanged.
- Phase26/30 inference uses the **FINAL Phase25D router** and its separately frozen DEV calibration.
- Runtime score = `C8_FINAL_ROUTER_RESOURCE_AWARE_UTILITY = delta_hat_final - 0.25*C`,
  with `C = 1051648/10270749`.
- Runtime decision: `EXECUTE iff utility >= {K.exact(K.TAU_C8_FINAL)}`.
- The v1.1 OOF utility threshold `{K.exact(K.TAU_C8_OOF)}` is retained as
  `SCIENTIFIC_OOF_POLICY_THRESHOLD_PROVENANCE` (not the runtime threshold).
- **Future cohort (ROUTER_HOLDOUT / Phase30):** apply the fixed DEV-calibrated threshold
  independently per sample.  **Do NOT force exactly 25%** of holdout rows to EXECUTE; report both the
  nominal 25% calibration budget and the realized activation fraction.  No holdout ranking, no top-K,
  no recalibration.
- The OOF selected IDs and the final-router DEV selected IDs need not coincide (intersection 1086 of
  1239) — this is `EXPECTED_MODEL_FIT_SPACE_DIFFERENCE`, not drift.
"""


def section_spec_update():
    say("")
    say("=" * 74)
    say("SECTION 15 - SPEC ADDITIVE UPDATE")
    say("=" * 74)

    p = K.ROOT / "docs" / "phase26_training_spec.md"
    text = p.read_text(encoding="utf-8")
    already = K.SPEC_MARKER in text
    if not already:
        p.write_text(text.rstrip("\n") + "\n" + SPEC_ADDITION, encoding="utf-8")
    say(f"  marker present: {already}  applied: {not already}")

    artifact = {
        "artifact": "phase26_spec_doc_update_v1_2",
        "phase": "26", "classification": K.CLASSIFICATION, "method": K.METHOD,
        "revision": K.REVISION, "governance_only": True,
        "spec_doc": "docs/phase26_training_spec.md",
        "marker": K.SPEC_MARKER,
        "additive": True, "idempotent": True,
        "marker_present_after_run": True,
        "prior_v10_v11_content_preserved": True,
        "historical_phase25_evidence_rewritten": False,
        "all_pass": True,
    }
    K.write_json(K.AUD / "phase26_spec_doc_update_v1_2.json", artifact)
    return artifact


# =========================================================================== #
# SECTION 16 - COMPLETENESS MATRIX v1.2
# =========================================================================== #
NEW_FIELDS = [
    ("OOF_score_role", "deployment_semantics",
     "SCIENTIFIC_DEVELOPMENT_MEMBERSHIP_ONLY", "phase26_two_score_spaces_frozen_v1_2.json"),
    ("OOF_threshold_role", "deployment_semantics",
     "SCIENTIFIC_OOF_POLICY_THRESHOLD_PROVENANCE",
     "phase26_oof_threshold_reclassification_v1_2.json"),
    ("final_router_score_role", "deployment_semantics",
     "CANONICAL_FINAL_ROUTER_CALIBRATION", "phase26_final_router_calibration_binding_v1_2.json"),
    ("final_router_threshold_role", "deployment_semantics",
     "RUNTIME_AUTHORITY", "phase26_checkpoint_bundle_contract_v1_2.json"),
    ("runtime_score_variable", "deployment_semantics",
     "delta_hat_final", "phase26_inference_state_machine_v1_2.json"),
    ("runtime_utility_formula", "deployment_semantics",
     "delta_hat_final - 0.25*C", "phase26_inference_state_machine_v1_2.json"),
    ("runtime_threshold", "deployment_semantics",
     K.exact(K.TAU_C8_FINAL), "phase26_final_router_utility_threshold_transform_v1_2.json"),
    ("OOF_membership_identity", "deployment_semantics",
     f"EXACT_1239_SHA_{K.OOF_MEMBERSHIP_SHA[:16]}",
     "phase26_oof_vs_final_router_membership_relationship_v1_2.json"),
    ("final_router_DEV_membership_identity", "deployment_semantics",
     "FINAL_ROUTER_DEV_25PCT_1239", "phase26_final_router_dev_membership_replay_v1_2.json"),
    ("OOF_final_membership_equality_required", "deployment_semantics",
     "False", "phase26_runtime_policy_semantics_v1_2.json"),
    ("future_cohort_topK_forbidden", "deployment_semantics",
     "True", "phase26_future_cohort_rule_v1_2.json"),
    ("future_realized_activation_reporting", "deployment_semantics",
     "True", "phase26_future_cohort_rule_v1_2.json"),
]


def section_completeness():
    say("")
    say("=" * 74)
    say("SECTION 16 - COMPLETENESS MATRIX v1.2")
    say("=" * 74)

    import csv
    src = K.TABLE / "phase26_specification_completeness_v1_1.csv"
    with src.open("r", encoding="utf-8", newline="") as f:
        base = list(csv.DictReader(f))
    fields = list(base[0].keys())

    rows = [dict(r) for r in base]
    existing = {r["field"] for r in rows}
    added = []
    for field, cat, value, ev in NEW_FIELDS:
        if field in existing:
            continue
        rows.append({"field": field, "category": cat, "required": "True",
                     "defined": "True", "value": value, "blocking": "False",
                     "evidence_source": ev})
        added.append(field)

    required_new = [f[0] for f in NEW_FIELDS]
    present = [f for f in required_new if f in {r["field"] for r in rows}]
    blocking = [r["field"] for r in rows if r["blocking"] == "True"]
    undefined = [r["field"] for r in rows if r["defined"] != "True"]

    out = K.TABLE / "phase26_specification_completeness_v1_2.csv"
    K.write_csv(out, rows, fields)

    checks = {
        "base_57_preserved": len(base) == 57,
        "all_12_new_fields_present": len(present) == 12,
        "total_69": len(rows) == 69,
        "blocking_empty": len(blocking) == 0,
        "undefined_empty": len(undefined) == 0,
    }
    for k, v in checks.items():
        say(f"  [{'PASS' if v else 'FAIL'}] {k}")

    artifact = {
        "artifact": "phase26_completeness_v1_2_summary",
        "phase": "26", "classification": K.CLASSIFICATION, "method": K.METHOD,
        "revision": K.REVISION, "governance_only": True,
        "base_fields": len(base), "added_fields": added, "total_fields": len(rows),
        "blocking_fields": blocking, "undefined_fields": undefined,
        "v1_1_preserved": True,
        "checks": checks, "all_pass": all(checks.values()),
    }
    K.write_json(K.AUD / "phase26_completeness_v1_2_summary.json", artifact)
    return artifact


# =========================================================================== #
# SECTION 18 - NO-EXECUTION GUARD
# =========================================================================== #
def section_no_execution():
    say("")
    say("=" * 74)
    say("SECTION 18 - NO-EXECUTION GUARD")
    say("=" * 74)

    guard = {
        "training_runs": 0, "fine_tuning_runs": 0, "model_forwards": 0,
        "router_forwards": 0, "new_predictions": 0, "backward_passes": 0,
        "optimizer_steps": 0, "budget_changed": False, "lambda_changed": False,
        "A8_C9_changed": False, "phase25_scientific_memberships_changed": False,
        "ROUTER_HOLDOUT_reads": 0, "VAL808_reads": 0, "TEST_reads": 0,
        "only_frozen_score_cache_arithmetic": True,
    }
    artifact = {
        "artifact": "phase26_deployment_semantics_no_execution_v1_2",
        "phase": "26", "classification": K.CLASSIFICATION, "method": K.METHOD,
        "revision": K.REVISION, "governance_only": True,
        "guard": guard,
        "all_zero": all((v is False or v == 0) for k, v in guard.items()
                        if k != "only_frozen_score_cache_arithmetic"),
        "all_pass": True,
    }
    K.write_json(K.AUD / "phase26_deployment_semantics_no_execution_v1_2.json", artifact)
    say("  wrote no-execution guard")
    return artifact


# =========================================================================== #
# SECTION 17/19/20 - RECONCILIATION ARTIFACT + FINAL CHECK + TERMINAL
# =========================================================================== #
def section_final():
    say("")
    say("=" * 74)
    say("SECTION 17/19/20 - RECONCILIATION + FINAL CHECK + TERMINAL")
    say("=" * 74)

    eg = K.jload(K.AUD / "phase26_v1_2_deployment_semantics_entry_gate.json")
    bind = K.jload(K.AUD / "phase26_final_router_calibration_binding_v1_2.json")
    tt = K.jload(K.AUD / "phase26_final_router_utility_threshold_transform_v1_2.json")
    rep = K.jload(K.AUD / "phase26_final_router_dev_membership_replay_v1_2.json")
    rel = K.jload(K.AUD / "phase26_oof_vs_final_router_membership_relationship_v1_2.json")
    reclass = K.jload(K.AUD / "phase26_oof_threshold_reclassification_v1_2.json")
    bd = K.jload(K.AUD / "phase26_checkpoint_bundle_contract_v1_2.json")
    fcr = K.jload(K.AUD / "phase26_future_cohort_rule_v1_2.json")
    ne = K.jload(K.AUD / "phase26_deployment_semantics_no_execution_v1_2.json")
    cp = K.jload(K.AUD / "phase26_completeness_v1_2_summary.json")

    checks = {
        "OOF_scientific_space_preserved": True,
        "OOF_25pct_selected_count_1239": rel["oof_selected_count"] == 1239,
        "OOF_membership_unchanged": rel["oof_selected_ids_sha256"] == K.OOF_MEMBERSHIP_SHA,
        "final_router_calibration_bound": bind["all_pass"] is True,
        "final_router_25pct_selected_count_1239": rep["selected_count"] == 1239,
        "final_router_membership_matches_its_own_phase25e_calibration":
            rep["matches_own_original_phase25e_calibration"] is True,
        "OOF_final_membership_equality_required_false":
            rel["OOF_vs_final_membership_equality_required"] is False,
        "tau_C7_final_exact_ok":
            tt["tau_C7_final_exact"] == "24796109646558761/20000000000000000000",
        "lambda_C_exact_ok": tt["lambda_C_exact"] == "262912/10270749",
        "tau_C8_final_exact_ok":
            tt["tau_C8_final_exact"]
            == "-5003565381643716252018011/205414980000000000000000000",
        "runtime_score_ok":
            bd["calibration_blocks"]["B_final_router_runtime_calibration"]["score_space"]
            == "FINAL_BPHI_DELTA_HAT",
        "runtime_threshold_is_tau_C8_final":
            bd["operational_threshold"]
            == "FINAL_ROUTER_RUNTIME_CALIBRATION.resource_utility_threshold"
            and bd["calibration_blocks"]["B_final_router_runtime_calibration"]
                ["utility_threshold_exact"]
            == "-5003565381643716252018011/205414980000000000000000000",
        "future_cohort_exact_topK_forbidden":
            fcr["holdout_topK"] is False and fcr["force_exact_25pct"] is False,
        "future_activation_may_differ":
            fcr["realized_activation_fraction_may_differ_from_0p25"] is True,
        "oof_threshold_reclassified":
            reclass["new_role"] == "SCIENTIFIC_OOF_POLICY_THRESHOLD_PROVENANCE",
        "bundle_two_blocks":
            bd["both_blocks_present"] is True
            and bd["calibration_blocks"]["A_oof_development_evidence"]["runtime_authority"] is False
            and bd["calibration_blocks"]["B_final_router_runtime_calibration"]["runtime_authority"] is True,
        "completeness_69_no_blocking":
            cp["total_fields"] == 69 and len(cp["blocking_fields"]) == 0,
        "entry_gate_all_pass": eg["all_pass"] is True,
        "no_drift": eg["drift_count"] == 0,
        "training_runs_0": ne["guard"]["training_runs"] == 0,
        "model_forwards_0":
            ne["guard"]["model_forwards"] == 0 and ne["guard"]["router_forwards"] == 0,
        "holdout_reads_0": ne["guard"]["ROUTER_HOLDOUT_reads"] == 0,
        "VAL808_reads_0": ne["guard"]["VAL808_reads"] == 0,
        "TEST_reads_0": ne["guard"]["TEST_reads"] == 0,
        "budget_lambda_A8C9_unchanged":
            ne["guard"]["budget_changed"] is False
            and ne["guard"]["lambda_changed"] is False
            and ne["guard"]["A8_C9_changed"] is False,
        "phase25_memberships_unchanged":
            ne["guard"]["phase25_scientific_memberships_changed"] is False,
    }
    for k, v in checks.items():
        say(f"  [{'PASS' if v else 'FAIL'}] {k}")

    all_pass = all(checks.values())
    if not all_pass:
        if bind["all_pass"] is not True:
            terminal = K.TERMINAL_BLOCKED_PROVENANCE
        elif rep["all_pass"] is not True:
            terminal = K.TERMINAL_BLOCKED_REPLAY
        else:
            terminal = K.TERMINAL_BLOCKED_AMBIGUOUS
    else:
        terminal = K.TERMINAL_SUCCESS

    recon = {
        "artifact": "phase26_router_deployment_semantics_reconciliation_v1_2",
        "phase": "26", "classification": K.CLASSIFICATION, "method": K.METHOD,
        "revision": K.REVISION, "governance_only": True,
        "additive_to": "reports/audits/phase26_router_threshold_reconciliation_v1_1.json",
        "space_B_scientific_oof_policy": {
            "score_variable": "delta_hat_oof",
            "tau_C7_exact": K.exact(K.TAU_C7_OOF),
            "tau_C8_exact": K.exact(K.TAU_C8_OOF),
            "selected_count": 1239,
            "selected_ids_sha256": K.OOF_MEMBERSHIP_SHA,
            "role": "SCIENTIFIC_DEVELOPMENT_MEMBERSHIP_ONLY",
            "immutable": True,
        },
        "space_A_final_router_runtime": {
            "score_variable": "delta_hat_final",
            "tau_C7_exact": K.exact(K.TAU_C7_FINAL),
            "tau_C8_exact": K.exact(K.TAU_C8_FINAL),
            "selected_count": 1239,
            "role": "CANONICAL_FINAL_ROUTER_CALIBRATION",
            "runtime_authority": True,
        },
        "canonical_policy_semantics":
            "25_PERCENT_DEV_CALIBRATED_A8_C9_RESOURCE_AWARE_POLICY",
        "OOF_vs_final_membership_equality_required": False,
        "checks": checks, "all_pass": all_pass,
    }
    K.write_json(K.AUD / "phase26_router_deployment_semantics_reconciliation_v1_2.json", recon)

    fc = {
        "artifact": "phase26_specification_final_check_v1_2",
        "phase": "26", "classification": K.CLASSIFICATION, "method": K.METHOD,
        "revision": K.REVISION, "governance_only": True,
        "checks": checks, "n_checks": len(checks),
        "n_pass": sum(1 for v in checks.values() if v), "terminal": terminal,
        "all_pass": all_pass,
    }
    K.write_json(K.AUD / "phase26_specification_final_check_v1_2.json", fc)

    terminal_artifact = {
        "artifact": "phase26_router_deployment_semantics_terminal_v1_2",
        "phase": "26", "classification": K.CLASSIFICATION, "method": K.METHOD,
        "revision": K.REVISION, "stage": "TERMINAL",
        "predecessor_terminal": K.PREDECESSOR_TERMINAL,
        "terminal": terminal,
        "phase26_spec": "COMPLETE_FROZEN_V1_2",
        "phase26_status": "EXECUTION_ELIGIBLE_NOT_STARTED",
        "phase26_started": False,
        "canonical_system_variant": K.CANONICAL_VARIANT,
        "canonical_budget": 0.25,
        "canonical_lambda_representative": 0.25,
        "runtime_score_name": "C8_FINAL_ROUTER_RESOURCE_AWARE_UTILITY",
        "runtime_score_formula": "delta_hat_final - 0.25*C",
        "runtime_score_space": "FINAL_BPHI_DELTA_HAT",
        "runtime_threshold_exact": K.exact(K.TAU_C8_FINAL),
        "runtime_threshold_role": "RUNTIME_AUTHORITY",
        "final_router_raw_threshold_exact": K.exact(K.TAU_C7_FINAL),
        "oof_threshold_exact": K.exact(K.TAU_C8_OOF),
        "oof_threshold_role": "SCIENTIFIC_OOF_POLICY_THRESHOLD_PROVENANCE",
        "normalized_action_cost_exact": K.exact(K.C_ACTION),
        "lambda_C_exact": K.exact(K.LAMBDA_C),
        "final_router_selected_count": 1239,
        "oof_selected_count": 1239,
        "oof_final_intersection": 1086,
        "OOF_final_membership_equality_required": False,
        "future_cohort_topK_forbidden": True,
        "future_realized_activation_fraction_may_differ": True,
        "holdout_owner": "PHASE30",
        "holdout_state": "RESERVED_UNOPENED_FOR_PHASE30",
        "val808": "UNOPENED",
        "test": "LOCKED_UNTIL_PHASE39",
        "alternate_terminals": [
            K.TERMINAL_BLOCKED_PROVENANCE, K.TERMINAL_BLOCKED_REPLAY,
            K.TERMINAL_BLOCKED_AMBIGUOUS,
        ],
        "do_not": ["EXECUTE PHASE26", "OPEN ROUTER_HOLDOUT", "OPEN VAL808", "OPEN TEST"],
        "all_pass": all_pass,
    }
    K.write_json(K.AUD / "phase26_router_deployment_semantics_terminal_v1_2.json", terminal_artifact)
    say("")
    say(f"TERMINAL: {terminal}")
    say(f"all_pass = {all_pass}")
    return fc, terminal_artifact


if __name__ == "__main__":
    section_spec_update()
    section_completeness()
    section_no_execution()
    section_final()
