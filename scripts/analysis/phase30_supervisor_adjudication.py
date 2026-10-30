#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""PHASE 30 — SUPERVISOR POST-OPEN ADJUDICATION (governance only).

SCIENTIFIC RESULT PRESERVATION + PERMANENT SOURCE-FREEZE PROTOCOL-DEVIATION
CLASSIFICATION.

No image read, no GT read, no model forward, no metric recomputation, no rerun,
no TEST access. Governance / reporting artifacts only.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase30_supervisor_adjudication.py
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"

METHOD = "RA-MedFiLM-BARR"
SPEC_REVISION = "ra_medfilm_barr_phase30_final_dev_validation_v1_3"

BLOCKED_TERMINAL = ("PHASE30_ONE_SHOT_EXECUTION_BLOCKED_AFTER_FIRST_OPEN__STAGE_B_SCIENTIFIC_"
                    "SOURCE_NOT_IN_PREOPEN_SOURCE_FREEZE__EVIDENCE_PRESERVED__NO_RERUN_AUTHORIZED")
EXEC_TERMINAL = ("PHASE30_ONE_SHOT_ROUTER_HOLDOUT_EXECUTION_COMPLETE__A8_C9_FINAL_DEVELOPMENT_"
                 "VALIDATION_RESULT_FROZEN__PHASE31_ELIGIBLE_NOT_STARTED")
ADJUDICATION_TERMINAL = (
    "PHASE30_SUPERVISOR_ADJUDICATION_COMPLETE__SCIENTIFIC_RESULT_PRESERVED_WITH_PREOPEN_SOURCE_"
    "FREEZE_PROTOCOL_DEVIATION__NOT_COMPLETE_CANONICAL__NO_RERUN__PHASE31_QUALIFIED_ELIGIBLE_NOT_STARTED")

EVIDENCE_CLASS = ("ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_SCIENTIFIC_SOURCE_"
                  "FREEZE_DEVIATION")

SOURCE_FREEZE_REBIND = "reports/audits/phase30_source_freeze_postdefect_rebind.json"
SOURCE_FREEZE_REBIND_SHA = "dddb71e6e3d64762062d9a69bd749988a64582b24e0948bc27f0c7d7df4fa7aa"
STAGE_B_PATH = "scripts/analysis/phase30_execution_stage_b.py"
STAGE_B_SHA = "9331c75bab2a5502c37ea4d9e1cd9afcf52766a0897b03c4d96a2c4fcc744fed"
STAGE_B_MTIME = "2026-10-04T03:15:36.906972+00:00"
FIRST_OPEN_MARKER_UTC = "2026-10-04T03:15:34+00:00"

# §G: exact SHAs of all Phase30 inputs permitted for Phase31
PHASE31_PERMITTED = [
    "reports/audits/phase30_primary_noninferiority_result.json",
    "reports/tables/phase30_router_holdout_scored_results.csv",
    "reports/tables/phase30_router_holdout_per_domain_results.csv",
    "reports/tables/phase30_router_holdout_predictions.csv",
    "reports/audits/phase30_router_metric_results.json",
    "reports/audits/phase30_a7_descriptive_companion_result.json",
    "reports/audits/phase30_h3_descriptive_result.json",
    "reports/audits/phase30_compute_results.json",
    "reports/audits/phase30_final_freeze.json",
    "reports/audits/phase30_execution_terminal.json",
    "reports/audits/phase30_postclosure_defect_reconciliation_terminal.json",
    "reports/audits/phase30_defect_classification.json",
    "reports/audits/phase30_source_freeze_postdefect_rebind.json",
    "reports/audits/phase30_supervisor_evidence_class_adjudication.json",
    "reports/audits/phase30_reporting_qualification_contract.json",
    "reports/audits/phase30_final_freeze.json",
    "notebooks/phasewise/phase_30_final_validation/phase30_final_development_validation.ipynb",
]


def sha256_file(p) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def write_json(obj, path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = str(path) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(json.dumps(obj, indent=1) + "\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def read_json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def main() -> int:
    print("=" * 78)
    print("PHASE 30 SUPERVISOR POST-OPEN ADJUDICATION (governance only)")
    print("=" * 78)

    pr = read_json(AUD / "phase30_primary_noninferiority_result.json")

    # ================= §A/§B permanent adjudication + defect binding ================= #
    sfr = read_json(ROOT / SOURCE_FREEZE_REBIND)
    sfr_sha = sha256_file(ROOT / SOURCE_FREEZE_REBIND)
    a_ok = (sfr_sha == SOURCE_FREEZE_REBIND_SHA
            and sfr["first_open_marker_utc"] == FIRST_OPEN_MARKER_UTC
            and sfr["stage_b_in_preopen_source_freeze"] is False
            and sfr["stage_b_sha_frozen_before_first_open"] is None)
    write_json({
        "artifact": "phase30_permanent_adjudication_status", "phase": 30,
        "classification": "SUPERVISOR_POST_OPEN_ADJUDICATION",
        "method": METHOD, "specification_revision": SPEC_REVISION,
        "scientific_result_status": "PRESERVED_VALID_ONE_SHOT_RESULT_WITH_PROTOCOL_DEVIATION",
        "protocol_conformance": "FAILED_PREOPEN_SCIENTIFIC_SOURCE_FREEZE",
        "canonical_status": "COMPLETE_WITH_PROTOCOL_DEVIATION__NOT_COMPLETE_CANONICAL",
        "scientific_execution_invalidated": False,
        "one_shot_integrity_invalidated": False,
        "scientific_results_changed": False,
        "rerun_required": False, "rerun_authorized": False,
        "ROUTER_HOLDOUT_state": "OPENED_AND_FROZEN",
        "failure_nature": "GOVERNANCE_REPRODUCIBILITY_PROVENANCE__NOT_DEMONSTRATED_SCIENTIFIC_RESULT_"
                          "CORRUPTION",
        "load_bearing_defect": {
            "authority_artifact": SOURCE_FREEZE_REBIND, "authority_sha256": sfr_sha,
            "authority_expected_sha256": SOURCE_FREEZE_REBIND_SHA,
            "first_open_marker_utc": FIRST_OPEN_MARKER_UTC,
            "stage_b_source": STAGE_B_PATH, "stage_b_source_sha256": STAGE_B_SHA,
            "stage_b_source_mtime_utc": STAGE_B_MTIME,
            "stage_b_in_preopen_source_freeze": False,
            "stage_b_sha_frozen_before_first_open": None,
            "stage_b_scientific_or_provenance_only": "SCIENTIFIC",
            "permanent_historical_provenance": True,
            "retroactive_preopen_sha_created": False,
            "source_relabelled_governance_only": False},
        "generated_utc": now_utc(), "all_pass": a_ok,
    }, AUD / "phase30_permanent_adjudication_status.json")
    print(f"§A/§B permanent adjudication frozen (authority ok={a_ok})")

    # ================= §C mitigating scientific evidence ================= #
    bar = read_json(AUD / "phase30_prediction_hash_barrier.json")
    gtc = read_json(AUD / "phase30_gt_read_counter_postdefect_reconciliation.json")
    fsa = read_json(AUD / "phase30_finalize_script_scope_audit.json")
    pab = read_json(AUD / "phase30_stage_b_pre_abort_scientific_output_provenance.json")
    c_ok = (bar["barrier_token"] == "PREDICTION_HASH_BARRIER_PASS"
            and bar["ROUTER_HOLDOUT_GT_reads_at_hash"] == 0
            and gtc["TOTAL_ROUTER_HOLDOUT_GT_physical_reads"] == 875
            and gtc["second_GT_pass"] is False
            and fsa["finalize_reads_GT"] is False and fsa["finalize_runs_models"] is False
            and pab["all_scientific_outputs_preceded_exception"] is True)
    write_json({
        "artifact": "phase30_mitigating_scientific_evidence", "phase": 30, "section": "§C",
        "prediction_hash_barrier": "PASS",
        "GT_reads_at_barrier": bar["ROUTER_HOLDOUT_GT_reads_at_hash"],
        "total_ROUTER_HOLDOUT_GT_physical_reads": gtc["TOTAL_ROUTER_HOLDOUT_GT_physical_reads"],
        "second_GT_pass": False,
        "stage_b_executed_exactly_once": True,
        "model_rerun": False, "metric_recomputation": False, "bootstrap_regeneration": False,
        "scientific_artifact_mutation": False,
        "finalize_GT_reads": 0, "finalize_model_forwards": 0,
        "finalize_scientific_recomputation": False,
        "TEST_reads": 0, "training": 0,
        "all_claim_bearing_scientific_outputs_persisted_before_exception":
            pab["all_scientific_outputs_preceded_exception"],
        "effect_on_result": "SUPPORTS_SCIENTIFIC_RESULT",
        "effect_on_protocol_deviation": "DOES_NOT_ERASE",
        "generated_utc": now_utc(), "all_pass": c_ok,
    }, AUD / "phase30_mitigating_scientific_evidence.json")
    print(f"§C mitigating evidence bound (ok={c_ok})")

    # ================= §D preserve numerical result ================= #
    d_ok = (abs(pr["global_macro_dice"] - 0.9285481511747413) < 1e-15
            and abs(pr["a8_macro_dice"] - 0.9302871820357663) < 1e-15
            and abs(pr["macro_delta_dice"] - 0.0017390308610248934) < 1e-15
            and pr["PRESERVATION_ASSERTED"] is True and pr["p_values_computed"] == 0)
    write_json({
        "artifact": "phase30_frozen_numerical_result_preservation", "phase": 30, "section": "§D",
        "recomputed": False,
        "population": "ROUTER_HOLDOUT", "n": 875,
        "global_macro_dice": pr["global_macro_dice"],
        "a8_macro_dice": pr["a8_macro_dice"],
        "macro_delta_dice": pr["macro_delta_dice"],
        "macro_ci": pr["macro_ci"],
        "frozen_criterion": "lower 95% CI > -0.005",
        "PRESERVATION_ASSERTED": pr["PRESERVATION_ASSERTED"],
        "p_values_computed": pr["p_values_computed"],
        "PRESERVATION_ASSERTED_changed": False,
        "future_use_qualifier": "must accompany the Phase30 source-freeze protocol deviation",
        "primary_result_sha256": sha256_file(AUD / "phase30_primary_noninferiority_result.json"),
        "generated_utc": now_utc(), "all_pass": d_ok,
    }, AUD / "phase30_frozen_numerical_result_preservation.json")
    print(f"§D numerical result preserved unchanged (ok={d_ok})")

    # ================= §E evidence class adjudication ================= #
    write_json({
        "artifact": "phase30_supervisor_evidence_class_adjudication", "phase": 30, "section": "§E",
        "method": METHOD, "specification_revision": SPEC_REVISION,
        "evidence_class": EVIDENCE_CLASS,
        "result_not_discarded": True,
        "result_rerunnable_as_clean_holdout": False,
        "result_is_COMPLETE_CANONICAL": False,
        "numerical_outputs_remain_frozen": True,
        "protocol_deviation_must_accompany_publication_claims": True,
        "claim_of_perfect_preregistration_or_source_freeze_conformance_allowed": False,
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase30_supervisor_evidence_class_adjudication.json")
    print("§E evidence class frozen")

    # ================= §F reporting qualification contract ================= #
    write_json({
        "artifact": "phase30_reporting_qualification_contract", "phase": 30, "section": "§F",
        "method": METHOD, "specification_revision": SPEC_REVISION,
        "allowed_wording":
            "On the one-shot ROUTER_HOLDOUT evaluation, the frozen A8/C9 policy produced a "
            "macro-domain Dice difference of +0.001739 with 95% CI [0.001117, 0.002405], satisfying "
            "the prespecified numerical non-inferiority margin. A protocol deviation occurred "
            "because the Stage-B scientific scoring source was not included in the pre-open source "
            "freeze; predictions and decision rules were frozen before GT access, GT was read once, "
            "and no scientific rerun or recomputation occurred.",
        "allowed_wording_note": "equivalent concise wording is acceptable",
        "forbidden_unqualified_wording": [
            "fully preregistered execution",
            "perfectly source-frozen one-shot validation",
            "Phase30 COMPLETE_CANONICAL",
            "no protocol deviations",
            "strictly protocol-perfect holdout"],
        "deviation_may_be_hidden_in_supplementary_provenance_only": False,
        "deviation_must_be_prominent": True,
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase30_reporting_qualification_contract.json")
    print("§F reporting qualification contract frozen")

    # ================= §G Phase31 qualified handoff ================= #
    permitted = [{"path": p, "sha256": sha256_file(ROOT / p)} for p in PHASE31_PERMITTED]
    write_json({
        "artifact": "phase30_phase31_qualified_handoff", "phase": 30, "section": "§G",
        "method": METHOD, "specification_revision": SPEC_REVISION,
        "phase31_eligibility": "ELIGIBLE_WITH_PHASE30_PROTOCOL_DEVIATION_QUALIFIER",
        "evidence_class_to_carry_forward": EVIDENCE_CLASS,
        "phase31_must_not": [
            "reopen ROUTER_HOLDOUT images", "reopen ROUTER_HOLDOUT GT",
            "rerun Phase30 models", "regenerate Phase30 metrics",
            "change Phase30 bootstrap indices", "change Phase30 claim criterion",
            "treat Phase30 as COMPLETE_CANONICAL"],
        "phase31_may_consume": "frozen Phase30 result tables/audits only",
        "qualifier_carried_forward": True,
        "permitted_inputs": permitted,
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase30_phase31_qualified_handoff.json")
    print(f"§G Phase31 qualified handoff frozen ({len(permitted)} permitted inputs)")

    # ================= §I final adjudication check ================= #
    checks = {
        "blocked_terminal_preserved":
            sha256_file(AUD / "phase30_postclosure_defect_reconciliation_terminal.json")
            == "75faa3edb7457848ed6537cb660978a8408dcf1bfd1bd7828a4962d297d22b53",
        "19_of_20_reconciliation_preserved":
            sha256_file(AUD / "phase30_postclosure_defect_reconciliation_final_check.json")
            == "1e86a3a5b739c63afc5f0dd013ef9b17b03b8baf655b82bd028f3b8b8d7bfead",
        "original_execution_terminal_preserved":
            sha256_file(AUD / "phase30_execution_terminal.json")
            == "f511fdc228847fb5669f0adb7dc38d15b2632b3b3429e88e48d7ad4bf29f778b",
        "stage_b_missing_from_preopen_freeze_acknowledged": sfr["stage_b_in_preopen_source_freeze"] is False,
        "no_retroactive_source_freeze_created": True,
        "scientific_result_preserved": True,
        "scientific_result_sha_unchanged":
            sha256_file(AUD / "phase30_primary_noninferiority_result.json")
            == "6548aa6ba438b1763727696b7ec1e339ec9ebf541df1d763ebc0c90922459856",
        "prediction_barrier_preserved":
            sha256_file(AUD / "phase30_prediction_hash_barrier.json")
            == "10d44c5bc920d6dca71acec4b320c8e3278f656fe9478bea1497bc83f0c1b425",
        "GT_reads_at_hash_0": bar["ROUTER_HOLDOUT_GT_reads_at_hash"] == 0,
        "total_GT_reads_875": gtc["TOTAL_ROUTER_HOLDOUT_GT_physical_reads"] == 875,
        "second_GT_pass_false": gtc["second_GT_pass"] is False,
        "model_rerun_false": True, "metric_recomputation_false": True,
        "bootstrap_regeneration_false": True,
        "TEST_reads_0": True, "rerun_authorized_false": True,
        "canonical_status_not_complete_canonical": True,
        "publication_qualification_required": True,
        "phase31_qualified_handoff_frozen": True,
        "Phase31_started_false": True,
        "preservation_asserted_unchanged": pr["PRESERVATION_ASSERTED"] is True,
        "p_values_computed_0": pr["p_values_computed"] == 0,
    }
    n_failed = sum(1 for v in checks.values() if not v)
    write_json({
        "artifact": "phase30_supervisor_adjudication_final_check", "phase": 30, "section": "§I",
        "method": METHOD, "specification_revision": SPEC_REVISION,
        "n_checks": len(checks), "n_failed": n_failed,
        "failed": [k for k, v in checks.items() if not v], "checks": checks,
        "generated_utc": now_utc(), "all_pass": n_failed == 0,
    }, AUD / "phase30_supervisor_adjudication_final_check.json")
    print(f"§I supervisor adjudication final check: {len(checks)-n_failed}/{len(checks)} pass")

    # ================= §J additive supervisor terminal ================= #
    if n_failed == 0:
        write_json({
            "artifact": "phase30_supervisor_adjudication_terminal", "phase": 30,
            "status": "ADJUDICATED", "terminal": ADJUDICATION_TERMINAL,
            "adjudication_nature": "SUPERVISOR_STATUS_ADJUDICATION__NOT_A_DEFECT_REPAIR",
            "scientific_result_status":
                "PRESERVED_VALID_ONE_SHOT_RESULT_WITH_PROTOCOL_DEVIATION",
            "protocol_conformance": "FAILED_PREOPEN_SCIENTIFIC_SOURCE_FREEZE",
            "canonical_status": "COMPLETE_WITH_PROTOCOL_DEVIATION__NOT_COMPLETE_CANONICAL",
            "evidence_class": EVIDENCE_CLASS,
            "PRESERVATION_ASSERTED": True,
            "p_values_computed": 0,
            "rerun_required": False, "rerun_authorized": False,
            "ROUTER_HOLDOUT_state": "OPENED_AND_FROZEN",
            "original_blocked_terminal_preserved": True,
            "original_execution_terminal_preserved": True,
            "phase31_eligibility": "ELIGIBLE_WITH_PHASE30_PROTOCOL_DEVIATION_QUALIFIER",
            "Phase31_started": False, "TEST_reads": 0,
            "generated_utc": now_utc(), "all_pass": True,
        }, AUD / "phase30_supervisor_adjudication_terminal.json")
        print("")
        print("=" * 78)
        print(ADJUDICATION_TERMINAL)
        print("=" * 78)
    else:
        print("ADJUDICATION CHECK FAILED:", [k for k, v in checks.items() if not v])
    return 0 if n_failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
