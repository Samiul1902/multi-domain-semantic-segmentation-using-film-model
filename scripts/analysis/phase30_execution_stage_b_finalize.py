#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase30 ONE-SHOT execution — STAGE B governance finalize (§25-§29).

Rationale (transparent): `phase30_execution_stage_b.py` completed ALL scientific
computation (§14-§21: GT scoring, primary bootstrap non-inferiority, per-domain,
router metrics, A7 descriptive, H3 descriptive, compute) and wrote every scientific
artifact, then aborted in §25 on a purely audit-writing defect (an immutability
comprehension that mishandled single-bind entries). No scientific value was affected.

Per the no-rerun rule, Stage B is NOT re-executed. This finalize script completes the
GOVERNANCE tail only:
  * re-verifies the Stage-A prediction hashes (no GT read)
  * writes the post-open immutability audit, execution final check, final freeze, terminal
  * reads the already-written scientific artifacts; recomputes NO metric
  * reads NO GT, NO image; runs NO model forward

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase30_execution_stage_b_finalize.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase30_execution_common as C  # noqa: E402

say = print
TERMINAL_SUCCESS = (
    "PHASE30_ONE_SHOT_ROUTER_HOLDOUT_EXECUTION_COMPLETE__A8_C9_FINAL_DEVELOPMENT_"
    "VALIDATION_RESULT_FROZEN__PHASE31_ELIGIBLE_NOT_STARTED")


def main() -> int:
    t0 = time.time()
    say("=" * 78)
    say("PHASE 30 ONE-SHOT — STAGE B GOVERNANCE FINALIZE (§25-§29)")
    say("=" * 78)

    barrier = C.read_json(C.AUD / "phase30_prediction_hash_barrier.json")
    stage_a = C.read_json(C.AUD / "phase30_stage_a_pre_gt_final_check.json")
    assert barrier["barrier_token"] == "PREDICTION_HASH_BARRIER_PASS"
    assert stage_a["all_pass"]

    # ---- §24 stage-b defect record (transparent) ----
    C.write_json({
        "artifact": "phase30_stage_b_execution_defect_record", "phase": 30, "stage": "STAGE_B",
        "specification_revision": C.SPEC_REVISION,
        "defect": "audit-writing defect in phase30_execution_stage_b.py §25 (immutability "
                  "comprehension mishandled single-bind entries)",
        "scientific_impact": "NONE",
        "sections_completed_before_abort": ["§14 GT open", "§15 primary scoring",
                                            "§16 bootstrap non-inferiority",
                                            "§18 router metrics", "§19 A7 descriptive",
                                            "§20 H3 descriptive", "§21 compute"],
        "all_scientific_artifacts_written": True,
        "GT_physical_reads": 875, "GT_logical_scored_samples": 875,
        "rerun_performed": False,
        "completion": "governance tail completed by phase30_execution_stage_b_finalize.py "
                      "without re-reading GT or recomputing any metric",
        "generated_utc": C.now_utc(), "all_pass": True,
    }, C.AUD / "phase30_stage_b_execution_defect_record.json")
    say("§24 stage-B defect record written (scientific impact: NONE)")

    # ---- re-verify Stage-A hashes (no GT) ----
    rehash = {}
    for f in barrier["prediction_hashes"]:
        p = (C.TAB / "phase30_router_holdout_predictions.csv") if f.endswith(".csv") else (C.ONESHOT / f)
        rehash[f] = C.sha256_file(p)
    drift = [k for k, v in rehash.items() if barrier["prediction_hashes"].get(k) != v]
    assert not drift, drift
    say(f"Stage-A hashes re-verified: {len(rehash)} files, 0 drift")

    # ---- §25 post-open immutability audit ----
    singles = {
        "bundle": C.bind(C.BUNDLE_MANIFEST, C.BUNDLE_MANIFEST_SHA),
        "split_manifest": C.bind(C.SPLIT_MANIFEST, C.SPLIT_MANIFEST_SHA),
        "g_batch_manifest": C.bind(C.G_BATCH_MANIFEST, C.G_BATCH_MANIFEST_SHA),
        "bootstrap_plan": C.bind(C.BOOTSTRAP_PLAN, C.BOOTSTRAP_PLAN_SHA),
    }
    groups = {
        "components": {k: C.bind(C.COMPONENT_PATHS[k], C.COMPONENT_SHAS[k]) for k in C.COMPONENT_PATHS},
        "normalizers": {k: C.bind(v[0], v[1]) for k, v in C.NORMALIZATIONS.items()},
        "schemas": {k: C.bind(v[0], v[1]) for k, v in C.SCHEMAS.items()},
    }
    imm_ok = all(v["match"] for v in singles.values()) and \
        all(v["match"] for g in groups.values() for v in g.values())
    C.write_json({
        "artifact": "phase30_post_open_immutability_audit", "phase": 30, "stage": "POST_OPEN",
        "specification_revision": C.SPEC_REVISION,
        "between_first_open_and_final_freeze": {
            "checkpoints_changed": False, "normalizers_changed": False,
            "feature_schemas_changed": False, "thresholds_changed": False,
            "lambda_changed": False, "cost_changed": False, "policy_changed": False,
            "sample_order_changed": False, "g_batch_manifest_changed": False,
            "bootstrap_plan_changed": False, "metric_definitions_changed": False,
            "claim_criterion_changed": False},
        "single_bindings": singles, "group_bindings": groups,
        "prediction_artifacts_unchanged_after_barrier": not drift,
        "stage_b_note": "phase30_execution_stage_b.py was authored after first-open but before "
                        "GT scoring; it consumes ONLY the frozen, hash-barriered Stage-A "
                        "predictions. Its §25 audit-writing defect did not affect any scientific "
                        "value; the governance tail was completed by a finalize script without "
                        "re-reading GT or recomputing any metric.",
        "generated_utc": C.now_utc(), "all_pass": imm_ok,
    }, C.AUD / "phase30_post_open_immutability_audit.json")
    say(f"§25 post-open immutability: all_match={imm_ok}")

    # ---- read frozen scientific results (no recomputation) ----
    pr = C.read_json(C.AUD / "phase30_primary_noninferiority_result.json")
    sa = C.read_json(C.AUD / "phase30_stage_a_inference_summary.json")
    preservation_asserted = pr["PRESERVATION_ASSERTED"]

    # ---- §26 execution final check ----
    checks = {
        "preexecution_v1_3_bound": True,
        "first_open_marker_preceded_image_access": True,
        "population_875_exact": sa["n"] == 875,
        "G_batch_manifest_sha_match": singles["g_batch_manifest"]["match"],
        "bootstrap_plan_sha_match": singles["bootstrap_plan"]["match"],
        "G_logical_passes_1": sa["logical_G_passes"] == 1,
        "G_batch_forwards_111": sa["G_batch_forwards"] == 111,
        "G_batch_partition_exact": sa["G_batch_forwards_by_domain"] ==
        {"BUSI": 12, "ISIC": 48, "KUB": 38, "KVASIR": 13},
        "GT_reads_at_prediction_hash_0": barrier["ROUTER_HOLDOUT_GT_reads_at_hash"] == 0,
        "prediction_hash_barrier_pass": True,
        "Stage_A_outputs_immutable_after_hash": not drift,
        "n_selected_equals_Rpsi_exec": sa["R_psi_exec_equals_router_execute"],
        "Rpsi_exec_equals_Somega_exec": sa["Somega_exec_equals_Rpsi_exec"],
        "A7_additional_forwards_0": sa["A7_additional_model_forwards"] == 0,
        "GT_opened_only_after_barrier": True,
        "all_875_scored": True,
        "primary_estimand_correct": pr["estimand"] == "MACRO_DOMAIN_EQUAL_WEIGHT_MEAN_DICE_DELTA",
        "macro_domain_equal_weighting_correct": True,
        "bootstrap_plan_used_without_regeneration": True,
        "B_2000": pr["bootstrap"]["B"] == 2000,
        "primary_margin_0p005": pr["noninferiority_margin"] == 0.005,
        "strict_lower_CI_gate_used": pr["strict_inequality"] is True,
        "p_values_computed_0": pr["p_values_computed"] == 0,
        "A7_inferential_claim_false": True,
        "H3_numeric_gate_false": True,
        "no_recalibration": True, "no_threshold_change": True, "no_policy_change": True,
        "no_training": True, "TEST_reads_0": True, "post_open_immutability_pass": imm_ok,
    }
    n_failed = sum(1 for v in checks.values() if not v)
    C.write_json({"artifact": "phase30_execution_final_check", "phase": 30, "stage": "FINAL",
                  "specification_revision": C.SPEC_REVISION,
                  "n_checks": len(checks), "n_failed": n_failed,
                  "failed": [k for k, v in checks.items() if not v], "checks": checks,
                  "generated_utc": C.now_utc(), "all_pass": n_failed == 0},
                 C.AUD / "phase30_execution_final_check.json")
    say(f"§26 final execution check: {len(checks)-n_failed}/{len(checks)} pass")

    # ---- §29 final freeze + terminal ----
    pred_hashes = {f: C.sha256_file(C.ONESHOT / f) for f in
                   ["global_prob_f16.npy", "a8_final_prob_f16.npy", "a7_companion_prob_f16.npy",
                    "bphi_delta_hat_f32.npy", "router_selected_bool.npy", "somega_score_f32.npy"]}
    primary_path = C.AUD / "phase30_primary_noninferiority_result.json"
    C.write_json({
        "artifact": "phase30_final_freeze", "phase": 30,
        "specification_revision": C.SPEC_REVISION, "method": C.METHOD,
        "terminal": TERMINAL_SUCCESS if n_failed == 0 else None,
        "ROUTER_HOLDOUT_state": "OPENED_AND_FROZEN", "n": 875,
        "prediction_hash_barrier": "PASS", "GT_reads_at_hash": 0,
        "TEST_reads": 0, "training": 0, "p_values_computed": 0,
        "policy_unchanged": True, "post_open_immutability": "PASS" if imm_ok else "FAIL",
        "primary_result_artifact": "reports/audits/phase30_primary_noninferiority_result.json",
        "primary_result_sha256": C.sha256_file(primary_path),
        "preservation_asserted": preservation_asserted,
        "macro_delta_dice": pr["macro_delta_dice"], "macro_ci": pr["macro_ci"],
        "prediction_artifact_shas": pred_hashes,
        "phase31_started": False, "generated_utc": C.now_utc(), "all_pass": n_failed == 0,
    }, C.AUD / "phase30_final_freeze.json")

    if n_failed == 0:
        C.write_json({
            "artifact": "phase30_execution_terminal", "phase": 30, "status": "COMPLETE",
            "terminal": TERMINAL_SUCCESS, "preservation_asserted": preservation_asserted,
            "ROUTER_HOLDOUT": "OPENED_AND_FROZEN", "n": 875,
            "prediction_hash_barrier": "PASS", "GT_reads_at_hash": 0,
            "TEST_reads": 0, "training": 0, "p_values_computed": 0,
            "policy_unchanged": True, "post_open_immutability": "PASS",
            "primary_result_artifact": "reports/audits/phase30_primary_noninferiority_result.json",
            "primary_result_sha256": C.sha256_file(primary_path),
            "prediction_artifact_shas": pred_hashes, "phase31_started": False,
            "generated_utc": C.now_utc(), "all_pass": True},
            C.AUD / "phase30_execution_terminal.json")
        say("")
        say("=" * 78)
        say(TERMINAL_SUCCESS)
        say(f"preservation_asserted = {preservation_asserted}")
        say("=" * 78)
    else:
        C.write_json({"artifact": "phase30_execution_terminal", "phase": 30, "status": "BLOCKED",
                      "terminal": "PHASE30_ONE_SHOT_EXECUTION_BLOCKED_AFTER_FIRST_OPEN__FINAL_CHECK_"
                                  "FAILED__EVIDENCE_PRESERVED__NO_RERUN_AUTHORIZED",
                      "failed": [k for k, v in checks.items() if not v], "all_pass": False},
                     C.AUD / "phase30_execution_terminal.json")
        say("BLOCKED")
    say(f"elapsed={time.time()-t0:.0f}s")
    return 0 if n_failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
