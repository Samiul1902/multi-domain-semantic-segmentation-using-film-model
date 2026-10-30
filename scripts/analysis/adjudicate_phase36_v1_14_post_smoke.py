#!/usr/bin/env python
"""
PHASE36 v1.14 -- POST-SMOKE ADJUDICATION (Work Order D, Steps 2-3).

Fail-closed, read-only independent adjudication of the ONE successful v1.14
synthetic smoke. Reads ONLY:
  * reports/audits/phase36_robustness_smoke_start_v1_14.json
  * reports/audits/phase36_robustness_smoke_v1_14.json
and verifies ~25 enumerated facts. If EVERY fact passes, writes ONCE:
  * reports/audits/phase36_v1_14_post_smoke_adjudication.json
Else STOP with a named terminal and write nothing.

NO smoke/science/model/checkpoint/TEST/ROUTER_HOLDOUT execution.
Raw-byte hashing only. Exclusive-create (write-once) output.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

EXEC = os.path.join(ROOT, "scripts", "analysis", "phase36_robustness_execution_v1_14.py")
START = os.path.join(ROOT, "reports", "audits", "phase36_robustness_smoke_start_v1_14.json")
RESULT = os.path.join(ROOT, "reports", "audits", "phase36_robustness_smoke_v1_14.json")
OUT = os.path.join(ROOT, "reports", "audits", "phase36_v1_14_post_smoke_adjudication.json")

FROZEN_EXEC_SHA = "ac09ff8ded3610244920e66612145b246b33127140d344a9730d454bab27cff5"
REVISION = "ra_medfilm_barr_phase36_robustness_v1_14"
TERMINAL_OK = (
    "PHASE36_V1_14_POST_SMOKE_ADJUDICATION_PASS__SCIENCE_RELEASE_ATTESTATION_ELIGIBLE_NOT_EXECUTED"
)


def raw_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> int:
    facts: list[dict] = []

    def fact(name: str, ok: bool, detail: object) -> bool:
        facts.append({"fact": name, "pass": bool(ok), "detail": detail})
        return bool(ok)

    all_ok = True

    # ---- FAIL-CLOSED BYTE VERIFICATION (Step 1 binding) ----
    exec_sha = raw_sha256(EXEC)
    start_sha = raw_sha256(START)
    result_sha = raw_sha256(RESULT)
    all_ok &= fact("execution_source_sha_matches_frozen", exec_sha == FROZEN_EXEC_SHA, exec_sha)

    d_start = json.load(open(START, "r", encoding="utf-8"))
    d_res = json.load(open(RESULT, "r", encoding="utf-8"))

    # ---- START MARKER FACTS ----
    all_ok &= fact("start_artifact_kind", d_start.get("artifact_kind") == "SMOKE_START_MARKER",
                   d_start.get("artifact_kind"))
    all_ok &= fact("start_attempted_true", d_start.get("attempted") is True, d_start.get("attempted"))
    all_ok &= fact("start_authorized_attempt_true", d_start.get("authorized_attempt") is True,
                   d_start.get("authorized_attempt"))
    all_ok &= fact("start_gate_authorized_before_marker_true",
                   d_start.get("gate_authorized_before_marker") is True,
                   d_start.get("gate_authorized_before_marker"))
    all_ok &= fact("start_automatic_retry_false", d_start.get("automatic_retry") is False,
                   d_start.get("automatic_retry"))
    all_ok &= fact("start_overwrite_permitted_false", d_start.get("overwrite_permitted") is False,
                   d_start.get("overwrite_permitted"))
    all_ok &= fact("start_source_sha256_matches_exec",
                   d_start.get("source_sha256") == FROZEN_EXEC_SHA, d_start.get("source_sha256"))
    all_ok &= fact("start_scientific_output_false", d_start.get("scientific_output") is False,
                   d_start.get("scientific_output"))
    all_ok &= fact("start_synthetic_only_true", d_start.get("synthetic_only") is True,
                   d_start.get("synthetic_only"))

    # ---- RESULT CORE FACTS ----
    all_ok &= fact("result_mode_smoke", d_res.get("mode") == "smoke", d_res.get("mode"))
    all_ok &= fact("result_classification",
                   d_res.get("classification") == "PRE_SCIENTIFIC_SYNTHETIC_FULL_PIPELINE_ROBUSTNESS_VALIDATION",
                   d_res.get("classification"))
    all_ok &= fact("result_synthetic_only_true", d_res.get("synthetic_only") is True,
                   d_res.get("synthetic_only"))
    all_ok &= fact("result_scientific_output_false", d_res.get("scientific_output") is False,
                   d_res.get("scientific_output"))
    all_ok &= fact("result_not_phase36_scientific_result_true",
                   d_res.get("not_phase36_scientific_robustness_result") is True,
                   d_res.get("not_phase36_scientific_robustness_result"))
    all_ok &= fact("result_four_real_components_loaded_true",
                   d_res.get("four_real_components_loaded") is True,
                   d_res.get("four_real_components_loaded"))
    all_ok &= fact("result_source_sha256_matches_exec",
                   d_res.get("source_sha256") == FROZEN_EXEC_SHA, d_res.get("source_sha256"))

    # ---- SUCCESS CONTRACT / SMOKE CHECKS ----
    all_ok &= fact("result_smoke_all_pass_true", d_res.get("smoke_all_pass") is True,
                   d_res.get("smoke_all_pass"))
    all_ok &= fact("result_n_smoke_checks_53", d_res.get("n_smoke_checks") == 53,
                   d_res.get("n_smoke_checks"))
    all_ok &= fact("result_failed_smoke_checks_empty", d_res.get("failed_smoke_checks") == [],
                   d_res.get("failed_smoke_checks"))

    sc = d_res.get("smoke_success_contract", {})
    ids = sc.get("ids", [])
    checks = d_res.get("smoke_checks", {})
    all_ok &= fact("contract_ids_count_53", len(ids) == 53, len(ids))
    all_ok &= fact("contract_ids_unique", len(set(ids)) == 53, len(set(ids)))
    all_ok &= fact("contract_n_checks_53", sc.get("n_checks") == 53, sc.get("n_checks"))
    all_ok &= fact("checks_keyset_equals_ids", set(checks.keys()) == set(ids),
                   {"checks": len(checks), "ids": len(ids)})
    all_ok &= fact("all_53_checks_true", all(checks.get(k) is True for k in ids),
                   [k for k in ids if checks.get(k) is not True])
    all_ok &= fact("contract_automatic_retry_false", sc.get("automatic_retry") is False,
                   sc.get("automatic_retry"))

    # ---- COMPONENT LOAD AUDIT ----
    cla = d_res.get("component_load_audit", {})
    comps = cla.get("components", {})
    expected_params = {"G": 3523001, "R_psi": 1276401, "B_phi": 36801, "S_omega": 1217}
    expected_ckpts = {
        "G": "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7",
        "R_psi": "6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109",
        "B_phi": "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b",
        "S_omega": "eee9b97b9921e53fc07eac9281dce64ba518c6e1659916b97b0b3bec21ec6d2e",
    }
    four_strict = True
    four_ckpt_sha = True
    four_params = True
    four_finite = True
    for c in ("G", "R_psi", "B_phi", "S_omega"):
        e = comps.get(c, {})
        four_strict &= (e.get("strict_load_ok") is True and e.get("missing_keys") == []
                        and e.get("unexpected_keys") == [])
        four_ckpt_sha &= (e.get("checkpoint_sha256") == expected_ckpts[c]
                          and e.get("checkpoint_sha256") == e.get("checkpoint_sha256_expected"))
        four_params &= (e.get("parameter_count") == expected_params[c]
                        and e.get("parameter_count") == e.get("parameter_count_expected"))
        four_finite &= (e.get("all_weights_finite") is True)
    all_ok &= fact("four_component_checkpoint_loads_strict", four_strict, four_strict)
    all_ok &= fact("four_checkpoint_sha_matches_frozen", four_ckpt_sha, four_ckpt_sha)
    all_ok &= fact("four_parameter_counts_exact", four_params, expected_params)
    all_ok &= fact("all_component_weights_finite", four_finite, four_finite)

    dc = cla.get("device_contract", {})
    all_ok &= fact("device_contract_cuda0", dc.get("resolved_device") == "cuda:0",
                   dc.get("resolved_device"))
    all_ok &= fact("device_no_cpu_fallback", dc.get("cpu_scientific_fallback_permitted") is False,
                   dc.get("cpu_scientific_fallback_permitted"))
    cdb = cla.get("component_device_binding", {})
    all_ok &= fact("all_four_on_canonical_device",
                   all(cdb.get(c, {}).get("on_canonical_device") is True
                       and cdb.get(c, {}).get("parameter_device") == "cuda:0"
                       for c in ("G", "R_psi", "B_phi", "S_omega")),
                   {c: cdb.get(c, {}).get("parameter_device") for c in ("G", "R_psi", "B_phi", "S_omega")})

    # ---- REAL EXECUTE COMPONENT PROBE (dims / forwards / finiteness) ----
    probe = d_res.get("real_execute_component_probe", {})
    all_ok &= fact("probe_router_vector_dim_202", probe.get("router_vector_dim") == 202,
                   probe.get("router_vector_dim"))
    all_ok &= fact("probe_post_safety_feature_dim_16", probe.get("post_safety_feature_dim") == 16,
                   probe.get("post_safety_feature_dim"))
    all_ok &= fact("probe_final_s_omega_input_dim_20", probe.get("final_s_omega_input_dim") == 20,
                   probe.get("final_s_omega_input_dim"))
    all_ok &= fact("probe_real_R_psi_forward_1", probe.get("actual_R_psi_forward_count") == 1,
                   probe.get("actual_R_psi_forward_count"))
    all_ok &= fact("probe_real_S_omega_forward_1", probe.get("actual_S_omega_forward_count") == 1,
                   probe.get("actual_S_omega_forward_count"))
    all_ok &= fact("probe_final_probability_finite", probe.get("final_probability_finite") is True,
                   probe.get("final_probability_finite"))
    all_ok &= fact("probe_final_probability_shape_512", probe.get("final_probability_shape") == [512, 512],
                   probe.get("final_probability_shape"))
    all_ok &= fact("probe_s_omega_prob_in_unit_interval",
                   probe.get("post_safety_accept_probability_in_unit_interval") is True,
                   probe.get("post_safety_accept_probability"))
    all_ok &= fact("probe_refined_output_shape_256", probe.get("refined_output_shape") == [256, 256],
                   probe.get("refined_output_shape"))

    # ---- PROPOSAL PIPELINE (real B_phi forward) ----
    pp = d_res.get("proposal_pipeline_check", {})
    all_ok &= fact("proposal_real_B_phi_forward_proven", pp.get("real_B_phi_forward_proven") is True,
                   pp.get("real_B_phi_forward_proven"))
    all_ok &= fact("proposal_router_vector_dim_202", pp.get("router_vector_dim") == 202,
                   pp.get("router_vector_dim"))
    all_ok &= fact("proposal_final_probability_finite", pp.get("final_probability_finite") is True,
                   pp.get("final_probability_finite"))

    # ---- STATE MACHINE ----
    sm = d_res.get("state_machine", {})
    all_ok &= fact("state_machine_all_pass", sm.get("all_pass") is True, sm.get("all_pass"))
    all_ok &= fact("state_machine_three_branches_covered",
                   set(sm.get("three_branches_covered", [])) ==
                   {"EXECUTE_THEN_ACCEPT", "EXECUTE_THEN_REJECT", "SKIP_GLOBAL"},
                   sm.get("three_branches_covered"))
    all_ok &= fact("state_machine_controls_not_scientific",
                   sm.get("policy_controls_not_scientific_outcomes") is True
                   and sm.get("policy_tests_not_scientific_outcomes") is True,
                   {"controls": sm.get("policy_controls_not_scientific_outcomes"),
                    "tests": sm.get("policy_tests_not_scientific_outcomes")})

    # ---- EMPTY PROPOSAL ----
    epc = d_res.get("empty_proposal_check", {})
    all_ok &= fact("empty_proposal_adapter_called", epc.get("empty_proposal_adapter_called") is True,
                   epc.get("empty_proposal_adapter_called"))
    all_ok &= fact("empty_proposal_R_psi_zero", epc.get("actual_R_psi_forward_count") == 0,
                   epc.get("actual_R_psi_forward_count"))
    all_ok &= fact("empty_proposal_S_omega_zero", epc.get("actual_S_omega_forward_count") == 0,
                   epc.get("actual_S_omega_forward_count"))
    all_ok &= fact("empty_proposal_no_replacement_geometry",
                   epc.get("no_replacement_geometry_generated") is True
                   and epc.get("no_geometry_returned") is True,
                   epc.get("handling"))

    # ---- HD95 / METRICS ----
    hd = d_res.get("hd95_hd", {})
    hde = d_res.get("hd95_hd_empty_case", {})
    all_ok &= fact("hd95_nonempty_valid_20px", hd.get("hd95") == 20.0 and hd.get("valid") is True,
                   {"hd95": hd.get("hd95"), "valid": hd.get("valid")})
    all_ok &= fact("hd95_empty_case_invalid_empty_prediction",
                   hde.get("valid") is False and hde.get("reason") == "empty_prediction",
                   {"valid": hde.get("valid"), "reason": hde.get("reason")})
    m = d_res.get("metrics", {})
    all_ok &= fact("metric_empty_empty_exact_one",
                   m.get("empty_empty", {}).get("dice") == 1.0
                   and m.get("empty_empty", {}).get("iou") == 1.0, m.get("empty_empty"))
    pcd = d_res.get("prediction_consistency_dice_smoke")
    all_ok &= fact("prediction_consistency_finite", isinstance(pcd, (int, float))
                   and pcd == pcd and abs(pcd - 0.9025) < 1e-9, pcd)

    # ---- PROTECTED POPULATION STATIC UNREACHABILITY ----
    all_ok &= fact("protected_test_holdout_runtime_io_statically_unreachable",
                   checks.get("protected_test_holdout_runtime_io_statically_unreachable") is True,
                   checks.get("protected_test_holdout_runtime_io_statically_unreachable"))

    # ---- DETERMINISM / BITWISE IDENTITY ----
    det = d_res.get("determinism", {})
    all_ok &= fact("determinism_same_inputs_identical", det.get("same_inputs_identical") is True,
                   det.get("same_inputs_identical"))
    all_ok &= fact("clean_bitwise_identity", d_res.get("clean_bitwise_identity") is True,
                   d_res.get("clean_bitwise_identity"))

    # ---- WRITE-ONCE SEMANTICS / NO-OVERWRITE ----
    all_ok &= fact("write_semantics_write_once", "write-once" in str(d_res.get("write_semantics", "")),
                   d_res.get("write_semantics"))
    all_ok &= fact("smoke_attempt_is_first_write_once", checks.get("smoke_attempt_is_first_write_once") is True,
                   checks.get("smoke_attempt_is_first_write_once"))
    all_ok &= fact("no_failure_artifact_present",
                   not os.path.exists(os.path.join(ROOT, "reports", "audits",
                                                   "phase36_robustness_smoke_fail_v1_14.json")), True)

    n_facts = len(facts)
    n_pass = sum(1 for f in facts if f["pass"])
    n_fail = n_facts - n_pass
    failed_facts = [f["fact"] for f in facts if not f["pass"]]

    if not all_ok or n_fail > 0:
        print(json.dumps({
            "terminal": "PHASE36_V1_14_POST_SMOKE_ADJUDICATION_FAILED",
            "n_facts": n_facts, "n_pass": n_pass, "n_fail": n_fail,
            "failed_facts": failed_facts,
        }, indent=1))
        print("STOP: adjudication failed; no artifact written.", file=sys.stderr)
        return 2

    payload = {
        "artifact": "phase36_v1_14_post_smoke_adjudication",
        "phase": 36,
        "revision": REVISION,
        "type": "POST_SMOKE_RELEASE_ADJUDICATION",
        "generated_utc": now_utc(),
        "adjudicator": "independent_read_only_post_smoke_adjudication",
        "consumed_inputs": {
            "smoke_start_marker": "reports/audits/phase36_robustness_smoke_start_v1_14.json",
            "smoke_start_marker_sha256": start_sha,
            "smoke_result": "reports/audits/phase36_robustness_smoke_v1_14.json",
            "smoke_result_sha256": result_sha,
            "execution_source": "scripts/analysis/phase36_robustness_execution_v1_14.py",
            "execution_source_sha256": exec_sha,
        },
        "byte_verification": {
            "execution_source_sha_matches_frozen": exec_sha == FROZEN_EXEC_SHA,
            "smoke_start_present": True,
            "smoke_result_present": True,
            "failure_artifact_absent": True,
        },
        "smoke_success_verified": {
            "smoke_all_pass": True,
            "n_smoke_checks": 53,
            "n_smoke_checks_true": 53,
            "failed_smoke_checks": [],
            "automatic_retry": False,
            "first_write_once": True,
        },
        "science_release_eligibility": {
            "attestation_written_by_this_step": False,
            "attestation_eligible": True,
            "release_gate_literal_required": "POST_SMOKE_RELEASE_ADJUDICATION",
            "required_attestation_fields": [
                "revision", "execution_source_sha256", "smoke_artifact_sha256",
                "smoke_all_pass", "scientific_output", "release_gate",
            ],
        },
        "facts": facts,
        "n_facts": n_facts,
        "n_facts_pass": n_pass,
        "n_facts_fail": n_fail,
        "failed_facts": failed_facts,
        "adjudication_result": "PASS",
        "all_facts_pass": True,
        "scientific_output_produced": False,
        "smoke_rerun": False,
        "science_executed": False,
        "test_or_router_holdout_accessed": False,
        "terminal": TERMINAL_OK,
    }

    # Exclusive-create (write-once).
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    fd = os.open(OUT, flags, 0o644)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(payload, fh, indent=1, ensure_ascii=False)
            fh.write("\n")
    except BaseException:
        os.close(fd)
        raise

    out_sha = raw_sha256(OUT)
    print(json.dumps({
        "artifact": OUT,
        "sha256": out_sha,
        "n_facts": n_facts, "n_pass": n_pass, "n_fail": n_fail,
        "adjudication_result": "PASS",
        "terminal": TERMINAL_OK,
    }, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
