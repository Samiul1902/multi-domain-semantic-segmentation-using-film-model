#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 36 — FINAL-PROBABILITY AUTHORITY DIAGNOSTIC v1.3 — D67 POST-START TERMINAL-EVIDENCE ANOMALY ADJUDICATION BUILDER.

Write-once, FAIL-CLOSED generator for the additive adjudication artifact:

    reports/audits/
      phase36_final_probability_authority_diagnostic_v1_3_terminal_evidence_anomaly_adjudication_v1_0.json

D67 = POST_START_TERMINAL_EVIDENCE_ANOMALY.

The v1.3 one-shot attempt was CONSUMED: the START marker exists, but there is NO
RESULT, NO FAILURE, and stdout/stderr are both zero-byte.  Per the v1.3 diagnostic
source, ANY ordinary Python exception (including SystemExit and KeyboardInterrupt)
inside the guarded computation region is expected to durably write a FAILURE
artifact.  The absence of FAILURE therefore suggests termination OUTSIDE the normal
failure path.  This is a STRUCTURAL INFERENCE ONLY: no bypass class is claimed to
have actually occurred, the root cause is UNRESOLVED, and no reproduction is
attempted.

MODE: STATIC / EXISTING-EVIDENCE FORENSICS ONLY.

NO v1.3 execution.  NO v1.4 creation.  NO model run.  NO checkpoint load.
NO VAL image read.  NO VAL GT read.  NO perturbation.  NO TEST.  NO ROUTER_HOLDOUT.
NO v1.15 science.  NO Phase37.  NO retroactive RESULT/FAILURE.  NO START alteration.

Run:  .venv\\Scripts\\python.exe scripts\\analysis\\build_phase36_final_probability_authority_diagnostic_v1_3_terminal_evidence_anomaly_adjudication_v1_0.py
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
RECONCILIATION_REVISION = "v1_0"

EMPTY_SHA = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

DIAG = ROOT / "scripts/analysis/phase36_final_probability_authority_diagnostic_v1_3.py"
LAUNCHER = ROOT / "scripts/analysis/launch_phase36_final_probability_authority_diagnostic_v1_3.py"
D66_RECON = AUD / "phase36_final_probability_authority_diagnostic_v1_3_governance_reconciliation_v1_0.json"

START = AUD / "phase36_final_probability_authority_diagnostic_start_v1_3.json"
RESULT = AUD / "phase36_final_probability_authority_diagnostic_result_v1_3.json"
FAILURE = AUD / "phase36_final_probability_authority_diagnostic_failure_v1_3.json"
STDOUT = AUD / "phase36_final_probability_authority_diagnostic_stdout_first_attempt_v1_3.txt"
STDERR = AUD / "phase36_final_probability_authority_diagnostic_stderr_first_attempt_v1_3.txt"

# ---- FROZEN PINS (LITERAL) -------------------------------------------------- #
PIN = {
    "diagnostic_v1_3": (DIAG, "b32a9db41a53b5007c6b9989bdbee22a0b7ea14587d222a3399980142dd9621e"),
    "launcher_v1_3": (LAUNCHER, "d5f9cd3dff302c849d195d909f6f2c9a59fbbbaaf359d859e69442d9fe05b504"),
    "d66_reconciliation_v1_0": (D66_RECON, "b0c01e40c4764514a01a9f082483a071634a0630d6c4c4640e1bb4ac2f829303"),
    "start_v1_3": (START, "b984d09bf3a266de8d75b39b6ad2ff3236cce09915a7f2a5c874813af8c3c1c5"),
}

OUT = AUD / "phase36_final_probability_authority_diagnostic_v1_3_terminal_evidence_anomaly_adjudication_v1_0.json"
SELF = ROOT / "scripts/analysis/build_phase36_final_probability_authority_diagnostic_v1_3_terminal_evidence_anomaly_adjudication_v1_0.py"


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
               "builder": "phase36_final_prob_authority_v1_3_d67_terminal_anomaly_adjudication"}
    payload.update(extra)
    print(json.dumps(payload, indent=1))
    return code


def _file_state(p: Path) -> dict:
    if not p.exists():
        return {"state": "ABSENT", "size": None, "sha256": None}
    size = p.stat().st_size
    h = sha(p)
    return {"state": ("PRESENT_EMPTY" if size == 0 else "PRESENT"), "size": size, "sha256": h}


def _find_lines(p: Path, needles) -> dict:
    out = {}
    if not p.exists():
        return out
    lines = p.read_text(encoding="utf-8").splitlines()
    for needle in needles:
        hits = [{"line": i, "text": lines[i - 1].strip()}
                for i in range(1, len(lines) + 1) if needle in lines[i - 1]]
        out[needle] = hits
    return out


def main() -> int:
    # ---- (0) write-once precondition ------------------------------------ #
    if OUT.exists():
        return fatal(2, "ADJUDICATION_V1_0_ALREADY_EXISTS", path=str(OUT))

    # ---- (1) fail-closed frozen pin verification ------------------------ #
    pin_bad = {}
    for k, (p, e) in PIN.items():
        o = sha(p)
        if o != e:
            pin_bad[k] = {"observed": o, "expected": e}
    if pin_bad:
        return fatal(3, "FROZEN_PIN_MISMATCH", bad=pin_bad)

    # ---- (2) STEP 1 — bind ACTUAL terminal evidence --------------------- #
    start_state = _file_state(START)
    result_state = _file_state(RESULT)
    failure_state = _file_state(FAILURE)
    stdout_state = _file_state(STDOUT)
    stderr_state = _file_state(STDERR)

    # exact anomaly precondition (fail closed otherwise)
    if not (start_state["state"] == "PRESENT"
            and result_state["state"] == "ABSENT"
            and failure_state["state"] == "ABSENT"):
        return fatal(4, "TERMINAL_EVIDENCE_NOT_ANOMALOUS__FAIL_CLOSED__NO_WRITE",
                     start=start_state, result=result_state, failure=failure_state)

    child_exit_code_durably_captured = False
    for cand in (ROOT / ".exitcode.txt", ROOT / "exitcode.txt"):
        if cand.exists():
            child_exit_code_durably_captured = True
    # scan for any stray exit-code artifact
    for cand in ROOT.glob("**/*exitcode*.txt"):
        child_exit_code_durably_captured = True

    # ---- (3) STEP 5 — source-level termination forensics ---------------- #
    diag_src = DIAG.read_text(encoding="utf-8")
    launch_src = LAUNCHER.read_text(encoding="utf-8")

    anchors = _find_lines(DIAG, [
        "_write_once_json(DIAGNOSTIC_START",
        "diag = run_diagnostic(runtime_state)",
        "except SystemExit as exc:",
        "except BaseException as exc:",
        "except Exception as exc:",
        "traceback.print_exc()",
        "_write_failure(termination_kind=\"SYSTEM_EXIT\"",
        "_write_failure(termination_kind=\"EXCEPTION\"",
        "_write_failure(termination_kind=\"RESULT_WRITE_FAILURE\"",
        "os._exit(",
        "atexit",
        "sys.exit(",
        "raise SystemExit(main())",
    ])
    launch_anchors = _find_lines(LAUNCHER, [
        "os.environ[LAUNCH_AUTHORITY_TOKEN]",
        "mod.main()",
        "raise SystemExit(main())",
        "os._exit(",
    ])

    start_write_line = anchors["_write_once_json(DIAGNOSTIC_START"][0]["line"] \
        if anchors.get("_write_once_json(DIAGNOSTIC_START") else None
    first_after_start = anchors["diag = run_diagnostic(runtime_state)"][0]["line"] \
        if anchors.get("diag = run_diagnostic(runtime_state)") else None

    has_except_systemexit = bool(anchors.get("except SystemExit as exc:"))
    has_except_baseexception = bool(anchors.get("except BaseException as exc:"))
    has_traceback_print = bool(anchors.get("traceback.print_exc()"))
    has_systemexit_failure = bool(anchors.get('_write_failure(termination_kind="SYSTEM_EXIT"'))
    has_exception_failure = bool(anchors.get('_write_failure(termination_kind="EXCEPTION"'))
    has_resultwrite_failure = bool(anchors.get('_write_failure(termination_kind="RESULT_WRITE_FAILURE"'))
    has_os_exit = bool(anchors.get("os._exit(")) or bool(launch_anchors.get("os._exit("))
    has_atexit = bool(anchors.get("atexit"))

    # KeyboardInterrupt is a BaseException subclass -> covered by `except BaseException`
    ordinary_exception_writes_failure = bool(
        has_except_systemexit and has_except_baseexception
        and has_systemexit_failure and has_exception_failure)

    # structural bypass classes (identified only; none claimed to have occurred)
    bypass_classes = [
        {"class": "external_process_termination",
         "description": "parent/session process-tree teardown kills the child before unwinding",
         "bypasses_failure_write": True,
         "claimed_to_have_occurred": False},
        {"class": "os_exit",
         "description": "os._exit() terminates without unwinding except/finally blocks",
         "present_in_source": has_os_exit,
         "bypasses_failure_write": True,
         "claimed_to_have_occurred": False},
        {"class": "fatal_interpreter_abort",
         "description": "native fatal abort (e.g. Py_FatalError) terminates without Python unwinding",
         "bypasses_failure_write": True,
         "claimed_to_have_occurred": False},
        {"class": "native_runtime_crash",
         "description": "segfault / CUDA driver fatal error aborts the process",
         "bypasses_failure_write": True,
         "claimed_to_have_occurred": False},
        {"class": "forced_process_kill",
         "description": "TerminateProcess / SIGKILL — no cleanup handlers run",
         "bypasses_failure_write": True,
         "claimed_to_have_occurred": False},
        {"class": "machine_or_session_termination",
         "description": "power loss / logoff / reboot terminates the host",
         "bypasses_failure_write": True,
         "claimed_to_have_occurred": False},
    ]

    # ---- (4) STEP 3 — execution reach ----------------------------------- #
    UNK = "UNKNOWN"
    execution_reach = {
        "diagnostic_main_after_start": {
            "value": "REACHED",
            "basis": ("START artifact written and durably completed (fsync); the START-write "
                      "statement executes inside diagnostic main() after authorization. "
                      "Advancement beyond the write statement is NOT proven."),
        },
        "frozen_v1_14_import": {"value": UNK, "basis": "no durable terminal artifact"},
        "gt_guard_installation": {"value": UNK, "basis": "no durable terminal artifact"},
        "model_load": {"value": UNK, "basis": "no durable terminal artifact"},
        "checkpoint_deserialization": {"value": UNK, "basis": "no durable terminal artifact"},
        "clean_g_generation": {"value": UNK, "basis": "no durable terminal artifact"},
        "phase27_global_reproduction_gate": {"value": UNK, "basis": "no durable terminal artifact"},
        "clean_row_loop_started": {"value": UNK, "basis": "no durable terminal artifact"},
        "final_probability_computation_started": {"value": UNK, "basis": "no durable terminal artifact"},
        "finite_gate": {"value": UNK, "basis": "no durable terminal artifact"},
        "final_authority_comparison": {"value": UNK, "basis": "no durable terminal artifact"},
        "result_write_attempt": {
            "value": "NOT_REACHED",
            "basis": ("reaching the result-write region must produce EITHER a RESULT artifact "
                      "(success) OR a FAILURE artifact (result-write failure); both are ABSENT, "
                      "so the region was not reached (source/order inference)."),
        },
        "failure_write_attempt": {
            "value": "NOT_REACHED",
            "basis": ("the failure path durably writes FAILURE (O_CREAT|O_EXCL + fsync); FAILURE is "
                      "ABSENT and no FAILURE_ARTIFACT_WRITE_FAILED stdout diagnostic is present. "
                      "Caveat: a doubly-failed failure-write cannot be excluded from terminal "
                      "evidence alone, but it would still have emitted a stdout diagnostic."),
        },
    }

    # ---- (5) assemble adjudication -------------------------------------- #
    ts = now()
    payload = {
        "artifact_kind":
            "PHASE36_FINAL_PROBABILITY_AUTHORITY_DIAGNOSTIC_V1_3_TERMINAL_EVIDENCE_ANOMALY_ADJUDICATION",
        "revision": REVISION,
        "adjudication_revision": RECONCILIATION_REVISION,
        "supersedes": None,
        "amends": None,
        "additive": True,
        "mode": "STATIC_EXISTING_EVIDENCE_FORENSICS_ONLY",
        "D67": "POST_START_TERMINAL_EVIDENCE_ANOMALY",
        "attempt_state": "CONSUMED_TERMINAL_EVIDENCE_ANOMALY",
        "retry_permitted": False,
        "v1_3_retry_forbidden": True,
        "root_cause": "UNRESOLVED",
        "external_process_termination": "PLAUSIBLE_HYPOTHESIS_NOT_ESTABLISHED",
        "termination_mechanism": "UNRESOLVED",
        "child_exit_code_durably_captured": child_exit_code_durably_captured,
        "child_exit_code": None,
        "host_or_tool_observed_return_status": 1,
        "scientific_result_produced": False,
        "repair_proof_result_produced": False,
        "terminal_evidence": {
            "start": start_state,
            "result": result_state,
            "failure": failure_state,
            "stdout": stdout_state,
            "stderr": stderr_state,
            "result_absent": result_state["state"] == "ABSENT",
            "failure_absent": failure_state["state"] == "ABSENT",
            "stdout_state": stdout_state["state"],
            "stderr_state": stderr_state["state"],
            "empty_sha256_expected": EMPTY_SHA,
        },
        "execution_reach": execution_reach,
        "source_termination_forensics": {
            "diagnostic_path": str(DIAG.relative_to(ROOT)).replace("\\", "/"),
            "diagnostic_sha256": PIN["diagnostic_v1_3"][1],
            "launcher_path": str(LAUNCHER.relative_to(ROOT)).replace("\\", "/"),
            "launcher_sha256": PIN["launcher_v1_3"][1],
            "A_start_write_line": start_write_line,
            "B_first_operation_after_start": {
                "line": first_after_start,
                "text": "diag = run_diagnostic(runtime_state)",
                "region": "GUARDED_COMPUTATION_REGION (try:)",
            },
            "C_exception_coverage_after_start": {
                "except_systemexit_present": has_except_systemexit,
                "except_baseexception_present": has_except_baseexception,
                "traceback_print_present": has_traceback_print,
                "systemexit_writes_failure": has_systemexit_failure,
                "baseexception_writes_failure": has_exception_failure,
                "result_write_failure_writes_failure": has_resultwrite_failure,
                "keyboardinterrupt_covered": has_except_baseexception,
                "keyboardinterrupt_note": "KeyboardInterrupt is a BaseException subclass -> caught by `except BaseException`",
                "os_exit_in_source": has_os_exit,
                "atexit_in_source": has_atexit,
            },
            "D_ordinary_python_exception_expected_to_write_failure": ordinary_exception_writes_failure,
            "E_bypass_classes_identified": bypass_classes,
            "absence_of_failure_suggests_outside_normal_failure_path": ordinary_exception_writes_failure,
            "note": ("STRUCTURAL INFERENCE ONLY.  The source would durably write FAILURE for any "
                     "ordinary Python exception, SystemExit, or KeyboardInterrupt.  FAILURE is "
                     "ABSENT, therefore termination occurred OUTSIDE the normal failure path.  No "
                     "specific bypass class is claimed to have actually happened."),
        },
        "os_evidence": {
            "windows_application_log_window_local": "2026-10-08 14:00:00 .. 2026-10-08 17:00:00",
            "application_critical_or_error_count": 0,
            "application_any_level_count": 40,
            "application_providers_observed": ["chromoting", "Microsoft-Windows-Security-SPP"],
            "system_critical_or_error_count": 0,
            "windows_error_reporting_present": False,
            "application_error_present": False,
            "python_crash_record_present": False,
            "cuda_driver_crash_log_present": False,
            "inconclusive_context": ("Information-level `chromoting` (Chrome Remote Desktop) events "
                                     "occur at 15:12 and 15:34 local, bracketing the execution time "
                                     "15:30:52 local (09:30:52Z).  This is recorded as inconclusive "
                                     "context ONLY and is NOT evidence of session teardown."),
            "termination_mechanism": "UNRESOLVED",
            "durable_os_evidence_found": False,
        },
        "gt_wording": {
            "gt_static_prohibition": "PASS",
            "gt_static_basis": ("v1.3 source contains the inherited raising guards and no intended "
                                "GT metric path"),
            "gt_runtime_terminal_evidence": "UNAVAILABLE",
            "post_start_GT_read_observed": "UNKNOWN_FROM_DURABLE_TERMINAL_EVIDENCE",
            "VAL_GT_READ_claimable": False,
            "note": ("VAL_GT_READ=0 is NOT claimed as observed runtime evidence; no durable post-START "
                     "artifact contains it."),
        },
        "preservation": {
            "diagnostic_v1_3": sha(DIAG),
            "launcher_v1_3": sha(LAUNCHER),
            "d66_reconciliation_v1_0": sha(D66_RECON),
            "start_v1_3": sha(START),
            "runtime_sources_unchanged": True,
            "result_not_created_retroactively": True,
            "failure_not_created_retroactively": True,
            "start_not_altered": True,
        },
        "prohibitions_observed": [
            "no_v1_3_execution", "no_v1_4_creation", "no_model_run",
            "no_checkpoint_load", "no_val_image_read", "no_val_gt_read",
            "no_perturbation", "no_test", "no_router_holdout",
            "no_v1_15_science", "no_phase37",
            "no_retroactive_result", "no_retroactive_failure", "no_start_alteration",
            "no_source_modification", "no_reproduction_triggered",
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
        "status": "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_3_D67_TERMINAL_ANOMALY_ADJUDICATION_BUILT",
        "adjudication_sha256": sha(OUT),
        "adjudication_builder_sha256": sha(SELF),
        "D67": "POST_START_TERMINAL_EVIDENCE_ANOMALY",
        "attempt_state": "CONSUMED_TERMINAL_EVIDENCE_ANOMALY",
        "retry_permitted": False,
        "root_cause": "UNRESOLVED",
        "external_process_termination": "PLAUSIBLE_HYPOTHESIS_NOT_ESTABLISHED",
        "termination_mechanism": "UNRESOLVED",
        "child_exit_code_durably_captured": child_exit_code_durably_captured,
        "host_or_tool_observed_return_status": 1,
        "ordinary_python_exception_expected_to_write_failure": ordinary_exception_writes_failure,
        "absence_of_failure_suggests_outside_normal_failure_path": ordinary_exception_writes_failure,
        "scientific_result_produced": False,
        "repair_proof_result_produced": False,
        "stdout_state": stdout_state["state"],
        "stderr_state": stderr_state["state"],
    }, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
