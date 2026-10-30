#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 36 — FINAL-PROBABILITY AUTHORITY DIAGNOSTIC v1.3 — D68 ADDITIVE FORENSIC-PRECISION RECONCILIATION BUILDER.

Write-once, FAIL-CLOSED generator for the additive reconciliation artifact:

    reports/audits/
      phase36_final_probability_authority_diagnostic_v1_3_terminal_evidence_anomaly_adjudication_reconciliation_v1_1.json

D68 = D67_TERMINAL_WRITE_REACH_OVERCLAIM.

The frozen D67 adjudication (v1.0) records, inside its ``execution_reach`` block::

    result_write_attempt  = NOT_REACHED
    failure_write_attempt = NOT_REACHED

Those states are NOT established by the durable evidence.  D67 itself leaves hard
termination / forced kill / native abort UNRESOLVED.  A hard termination could occur
(i) after entering the result-write region but before durable RESULT creation,
(ii) during the RESULT write before a FAILURE handler completes,
(iii) after entering the FAILURE-write path but before durable FAILURE creation, or
(iv) during the FAILURE write before any stdout diagnostic is emitted.  Therefore the
absence of RESULT / FAILURE / stdout does NOT prove those write regions were never
entered.  The correct states are UNKNOWN.

This reconciliation ALSO corrects the scope of D67's ``prohibitions_observed``: those
prohibitions describe the STATIC D67 ADJUDICATION OPERATION, NOT the consumed v1.3
attempt.  For the consumed attempt the model/checkpoint/VAL-image/GT observations are
UNKNOWN_FROM_DURABLE_TERMINAL_EVIDENCE.

D67's CORE classification is UNCHANGED (POST_START_TERMINAL_EVIDENCE_ANOMALY;
CONSUMED_TERMINAL_EVIDENCE_ANOMALY; retry forbidden; no scientific result).

MODE: STATIC / EXISTING-EVIDENCE ONLY.

NO v1.3 execution.  NO model execution.  NO checkpoint deserialization.  NO VAL image
read.  NO VAL GT read.  NO TEST.  NO ROUTER_HOLDOUT.  NO perturbations.  NO v1.4
creation.  NO v1.15 science.  NO Phase37.  NO ancestor modification.

Run:  .venv\\Scripts\\python.exe scripts\\analysis\\build_phase36_final_probability_authority_diagnostic_v1_3_terminal_evidence_anomaly_adjudication_reconciliation_v1_1.py
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUD = ROOT / "reports" / "audits"

REVISION = "ra_medfilm_barr_phase36_final_probability_authority_diagnostic_v1_3"
RECONCILIATION_REVISION = "v1_1"

# ---- FROZEN ANCESTOR PINS (LITERAL) ---------------------------------------- #
D67_ADJ = AUD / "phase36_final_probability_authority_diagnostic_v1_3_terminal_evidence_anomaly_adjudication_v1_0.json"
D67_BUILDER = ROOT / "scripts/analysis/build_phase36_final_probability_authority_diagnostic_v1_3_terminal_evidence_anomaly_adjudication_v1_0.py"
START_V1_3 = AUD / "phase36_final_probability_authority_diagnostic_start_v1_3.json"
DIAG = ROOT / "scripts/analysis/phase36_final_probability_authority_diagnostic_v1_3.py"
LAUNCHER = ROOT / "scripts/analysis/launch_phase36_final_probability_authority_diagnostic_v1_3.py"
D66_RECON = AUD / "phase36_final_probability_authority_diagnostic_v1_3_governance_reconciliation_v1_0.json"

PIN = {
    "d67_adjudication_v1_0": (D67_ADJ, "3d3f943c19d5b419fb00bcf19748c0dd41ff8002ef26a4a3c51ad32ef6afecd5"),
    "d67_builder": (D67_BUILDER, "05e7b90baab29f60888843f194895401708bac1e706cb922515ac05c2d6df89b"),
    "start_v1_3": (START_V1_3, "b984d09bf3a266de8d75b39b6ad2ff3236cce09915a7f2a5c874813af8c3c1c5"),
    "diagnostic_v1_3": (DIAG, "b32a9db41a53b5007c6b9989bdbee22a0b7ea14587d222a3399980142dd9621e"),
    "launcher_v1_3": (LAUNCHER, "d5f9cd3dff302c849d195d909f6f2c9a59fbbbaaf359d859e69442d9fe05b504"),
    "d66_reconciliation_v1_0": (D66_RECON, "b0c01e40c4764514a01a9f082483a071634a0630d6c4c4640e1bb4ac2f829303"),
}

OUT = AUD / "phase36_final_probability_authority_diagnostic_v1_3_terminal_evidence_anomaly_adjudication_reconciliation_v1_1.json"
SELF = ROOT / "scripts/analysis/build_phase36_final_probability_authority_diagnostic_v1_3_terminal_evidence_anomaly_adjudication_reconciliation_v1_1.py"


def sha(p: Path) -> str:
    try:
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()
    except FileNotFoundError:
        return "ABSENT"


def now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def write_once(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, indent=1, ensure_ascii=False, default=str).encode("utf-8")
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    fd = os.open(str(path), flags, 0o644)
    try:
        total = 0
        while total < len(data):
            n = os.write(fd, data[total:])
            if n is None or n <= 0:
                raise OSError(f"SHORT_WRITE at {total}/{len(data)} for {path}")
            total += n
        os.fsync(fd)
    finally:
        os.close(fd)
    if path.stat().st_size != len(data):
        raise OSError(f"POST_WRITE_SIZE_MISMATCH for {path}")


def fatal(code: int, reason: str, **extra) -> int:
    payload = {"REFUSED": reason,
               "builder": "phase36_final_prob_authority_v1_3_d68_forensic_precision_reconciliation_v1_1"}
    payload.update(extra)
    print(json.dumps(payload, indent=1))
    return code


def main() -> int:
    # ---- (0) write-once precondition ------------------------------------ #
    if OUT.exists():
        return fatal(2, "RECONCILIATION_V1_1_ALREADY_EXISTS", path=str(OUT))

    # ---- (1) fail-closed frozen ancestor bind --------------------------- #
    bad = {}
    for k, (p, e) in PIN.items():
        o = sha(p)
        if o != e:
            bad[k] = {"observed": o, "expected": e}
    if bad:
        return fatal(3, "FROZEN_ANCESTOR_PIN_MISMATCH", bad=bad)

    # ---- (2) verify the D67 defect is actually present (fail closed) ----- #
    d67 = json.loads(D67_ADJ.read_text(encoding="utf-8"))
    d67_reach = d67.get("execution_reach", {})
    rwa = (d67_reach.get("result_write_attempt") or {}).get("value")
    fwa = (d67_reach.get("failure_write_attempt") or {}).get("value")
    if not (rwa == "NOT_REACHED" and fwa == "NOT_REACHED"):
        return fatal(4, "D68_PRECONDITION_NOT_MET__D67_WRITE_REACH_NOT_OVERCLAIMED__FAIL_CLOSED",
                     result_write_attempt=rwa, failure_write_attempt=fwa)

    # ---- (3) build corrected execution reach ---------------------------- #
    reach_stages = [
        "diagnostic_main_after_start",
        "frozen_v1_14_import",
        "gt_guard_installation",
        "model_load",
        "checkpoint_deserialization",
        "clean_g_generation",
        "phase27_global_reproduction_gate",
        "clean_row_loop_started",
        "final_probability_computation_started",
        "finite_gate",
        "final_authority_comparison",
        "result_write_attempt",
        "failure_write_attempt",
    ]
    corrected_reach = {}
    for s in reach_stages:
        if s == "diagnostic_main_after_start":
            corrected_reach[s] = {
                "value": "REACHED",
                "preserved_from": "D67",
                "basis": "START artifact durably written (fsync, O_CREAT|O_EXCL); only established fact.",
            }
        else:
            corrected_reach[s] = {
                "value": "UNKNOWN",
                "basis": ("durable evidence does not establish reach; a hard termination before a "
                          "terminal artifact cannot be excluded"),
            }

    corrected_reach["result_write_attempt"]["corrected_from"] = "NOT_REACHED (D67 overclaim)"
    corrected_reach["result_write_attempt"]["d68_rationale"] = (
        "A hard termination could occur AFTER entering the result-write region but BEFORE durable "
        "RESULT creation, or DURING the RESULT write before a FAILURE handler completes; absence of "
        "RESULT/FAILURE/stdout does NOT prove the region was never entered.")
    corrected_reach["failure_write_attempt"]["corrected_from"] = "NOT_REACHED (D67 overclaim)"
    corrected_reach["failure_write_attempt"]["d68_rationale"] = (
        "A hard termination could occur AFTER entering the FAILURE-write path but BEFORE durable "
        "FAILURE creation, or DURING the FAILURE write before any stdout diagnostic is emitted; "
        "absence of FAILURE/stdout does NOT prove the path was never entered.")

    # ---- (4) scope correction for the consumed attempt ------------------- #
    scope_correction = {
        "note": ("D67 `prohibitions_observed` applies to the STATIC D67 ADJUDICATION OPERATION and "
                 "must NOT be read as proof that the consumed v1.3 attempt avoided models / "
                 "checkpoints / VAL images / intermediate stages."),
        "d67_prohibitions_scope": "STATIC_D67_ADJUDICATION_OPERATION_ONLY",
        "consumed_v1_3_attempt": {
            "model_run_observed": "UNKNOWN_FROM_DURABLE_TERMINAL_EVIDENCE",
            "checkpoint_deserialization_observed": "UNKNOWN_FROM_DURABLE_TERMINAL_EVIDENCE",
            "val_image_read_observed": "UNKNOWN_FROM_DURABLE_TERMINAL_EVIDENCE",
            "post_start_gt_read_observed": "UNKNOWN_FROM_DURABLE_TERMINAL_EVIDENCE",
            "val_gt_read_claimable": False,
        },
        "gt_static_prohibition": "PASS",
        "val_gt_read_basis_unchanged": "D67 gt_runtime_terminal_evidence = UNAVAILABLE (VAL_GT_READ=0 NOT claimed)",
    }

    ts = now()
    payload = {
        "artifact_kind":
            "PHASE36_FINAL_PROBABILITY_AUTHORITY_DIAGNOSTIC_V1_3_TERMINAL_EVIDENCE_ANOMALY_ADJUDICATION_RECONCILIATION",
        "revision": REVISION,
        "reconciliation_revision": RECONCILIATION_REVISION,
        "supersedes": None,
        "amends":
            "phase36_final_probability_authority_diagnostic_v1_3_terminal_evidence_anomaly_adjudication_v1_0.json",
        "amends_sha256": PIN["d67_adjudication_v1_0"][1],
        "additive": True,
        "mode": "STATIC_EXISTING_EVIDENCE_ONLY",
        "D67": "PRESERVED",
        "D68": "RECONCILED",
        "d68_classification": "D67_TERMINAL_WRITE_REACH_OVERCLAIM",
        "d68_root_cause_established": True,
        "result_write_attempt_corrected": "UNKNOWN",
        "failure_write_attempt_corrected": "UNKNOWN",
        "d67_core_classification_unchanged": True,
        "retry_policy_unchanged": True,
        "scientific_result_status_unchanged": True,
        "d67_preserved_fields": {
            "D67": "POST_START_TERMINAL_EVIDENCE_ANOMALY",
            "attempt_state": "CONSUMED_TERMINAL_EVIDENCE_ANOMALY",
            "retry_permitted": False,
            "root_cause": "UNRESOLVED",
            "termination_mechanism": "UNRESOLVED",
            "external_process_termination": "PLAUSIBLE_HYPOTHESIS_NOT_ESTABLISHED",
            "child_exit_code_durably_captured": False,
            "child_exit_code": None,
            "host_or_tool_observed_return_status": 1,
            "scientific_result_produced": False,
            "repair_proof_result_produced": False,
            "START": "PRESENT",
            "RESULT": "ABSENT",
            "FAILURE": "ABSENT",
            "STDOUT": "PRESENT_EMPTY",
            "STDERR": "PRESENT_EMPTY",
        },
        "d68_correction": {
            "overclaimed_states": {
                "result_write_attempt": "NOT_REACHED",
                "failure_write_attempt": "NOT_REACHED",
            },
            "corrected_states": {
                "result_write_attempt": "UNKNOWN",
                "failure_write_attempt": "UNKNOWN",
            },
            "rationale": ("D67 leaves hard termination / forced kill / native abort UNRESOLVED.  Such a "
                          "termination can occur after entering (or during) a write region but before "
                          "any durable artifact/stdout appears; therefore absence of RESULT/FAILURE/"
                          "stdout does NOT prove the write regions were never entered."),
            "enumeration_of_unexcluded_scenarios": [
                "termination after entering the result-write region but before durable RESULT creation",
                "termination during the RESULT write before a FAILURE handler completes",
                "termination after entering the FAILURE-write path but before durable FAILURE creation",
                "termination during the FAILURE write before any stdout diagnostic is emitted",
            ],
            "only_durably_established_fact": "START completion (after authorization)",
        },
        "execution_reach_corrected": corrected_reach,
        "scope_correction": scope_correction,
        "scientific_semantics_effect": "NONE",
        "runtime_execution_effect": "NONE",
        "forensic_precision_effect": "YES",
        "root_cause": "UNRESOLVED",
        "termination_mechanism": "UNRESOLVED",
        "v1_3_retry_permitted": False,
        "v1_3_attempt_state": "CONSUMED_TERMINAL_EVIDENCE_ANOMALY",
        "scientific_result_produced": False,
        "repair_proof_result_produced": False,
        "ancestor_binding": {k: {"path": str(v[0].relative_to(ROOT)).replace("\\", "/"),
                                 "sha256": v[1]} for k, v in PIN.items()},
        "ancestors_modified": False,
        "d67_adjudication_not_overwritten": True,
        "d67_builder_not_overwritten": True,
        "prohibitions_observed": [
            "no_v1_3_execution", "no_model_execution", "no_checkpoint_deserialization",
            "no_val_image_read", "no_val_gt_read", "no_test", "no_router_holdout",
            "no_perturbations", "no_v1_4_creation", "no_v1_15_science", "no_phase37",
            "no_ancestor_modification",
        ],
        "governance_state_after": {
            "v1_0": "FROZEN_NEVER_CONSUMED_NOT_AUTHORIZED",
            "v1_1": "CONSUMED_FAILED",
            "v1_2_final_prob": "CONSUMED_RESULT",
            "v1_3_final_prob": "CONSUMED_TERMINAL_EVIDENCE_ANOMALY",
            "v1_3_retry_permitted": False,
            "v1_14_science": "CONSUMED_FAILED",
            "v1_15": "NOT_CREATED",
            "phase37": "NOT_STARTED",
            "test": "PHASE39_ONLY",
            "router_holdout": "NOT_ACCESSED",
        },
        "scientific_output": False,
        "generated_utc": ts,
    }
    write_once(OUT, payload)

    print(json.dumps({
        "status": "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_3_D68_FORENSIC_RECONCILIATION_BUILT",
        "reconciliation_sha256": sha(OUT),
        "reconciliation_builder_sha256": sha(SELF),
        "D67": "PRESERVED",
        "D68": "RECONCILED",
        "d68_classification": "D67_TERMINAL_WRITE_REACH_OVERCLAIM",
        "result_write_attempt_corrected": "UNKNOWN",
        "failure_write_attempt_corrected": "UNKNOWN",
        "root_cause": "UNRESOLVED",
        "termination_mechanism": "UNRESOLVED",
        "v1_3_attempt_state": "CONSUMED_TERMINAL_EVIDENCE_ANOMALY",
        "v1_3_retry_permitted": False,
        "scientific_result_produced": False,
        "repair_proof_result_produced": False,
        "scientific_semantics_effect": "NONE",
        "forensic_precision_effect": "YES",
    }, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
