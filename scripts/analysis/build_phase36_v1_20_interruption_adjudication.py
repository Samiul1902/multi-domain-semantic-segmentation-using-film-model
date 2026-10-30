#!/usr/bin/env python
"""WO#21 §1/§2 — BUILD the v1.20 INTERRUPTED-EXECUTION ADJUDICATION (write-once).

MODE: STATIC / ADDITIVE GOVERNANCE ONLY.  NON-CONSUMING.

Creates EXACTLY ONE new artifact:

    reports/audits/phase36_v1_20_interruption_adjudication_v1_0.json

It does NOT modify ANY v1.20 artifact (START / PROCESS_EXIT / stdout / stderr /
journal record / execution source / supervisor source are READ-ONLY here).

FROZEN v1.20 EVIDENCE (durable, on disk)
----------------------------------------
  START marker          reports/audits/phase36_robustness_science_start_v1_20.json
  PROCESS_EXIT          reports/audits/phase36_robustness_science_process_exit_v1_20.json
  stderr                reports/audits/phase36_robustness_science_stderr_v1_20.txt
  START/BEGIN journal   reports/audits/phase36_robustness_science_v1_20_journal/000_START__BEGIN.json
  v1.20 execution source scripts/analysis/phase36_robustness_execution_v1_20.py
  v1.20 supervisor source scripts/analysis/supervise_phase36_v1_20.py

FACTS (durable, established)
----------------------------
  * v1.20 real execution STARTED; the START marker exists; the journal reached
    START:BEGIN; RESULT and FAILURE are ABSENT; all 23 scientific outputs are
    ABSENT.
  * The supervisor's PROCESS_EXIT records child_exit_code = null and
    termination_observed = false.
  * The supervisor stderr carries ``SUPERVISOR_EXCEPTION::KeyboardInterrupt::``.
  * The supervisor INCORRECTLY returned rc = 0 when termination was NOT observed
    (defect D95).

The ORIGIN of the KeyboardInterrupt is NOT established by this adjudication and
is deliberately NOT claimed.  This is NOT a scientific-model failure.

CLASSIFICATION: CONSUMED_INTERRUPTED_POST_START_PRE_SCIENTIFIC_RESULT.
v1.20 MUST NEVER BE RERUN.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
AUD = ROOT / "reports" / "audits"

# ---- frozen v1.20 evidence paths ----------------------------------------- #
P_START = AUD / "phase36_robustness_science_start_v1_20.json"
P_PROCESS_EXIT = AUD / "phase36_robustness_science_process_exit_v1_20.json"
P_STDERR = AUD / "phase36_robustness_science_stderr_v1_20.txt"
P_STDOUT = AUD / "phase36_robustness_science_stdout_v1_20.txt"
P_JOURNAL_START_BEGIN = (
    AUD / "phase36_robustness_science_v1_20_journal" / "000_START__BEGIN.json")
P_RESULT = AUD / "phase36_robustness_scientific_result_v1_20.json"
P_FAILURE = AUD / "phase36_robustness_science_failure_v1_20.json"

P_EXEC = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_20.py"
P_SUPERVISOR = ROOT / "scripts" / "analysis" / "supervise_phase36_v1_20.py"
P_LAUNCHER = ROOT / "scripts" / "analysis" / "launch_phase36_v1_20.py"

OUT = AUD / "phase36_v1_20_interruption_adjudication_v1_0.json"

# ---- expected frozen SHAs (FAIL CLOSED if any drifts) -------------------- #
EXP_START_SHA = "f60eac4fb6296a69455848e66aa09cecd999ac527243e8d05e3a2c5e70b25aa8"
EXP_PROCESS_EXIT_SHA = "26e80a164a05a1dce9f2c7377508149da189702007f0be1f6fa9b4ef7cd0e7b3"
EXP_STDERR_SHA = "8e29136d5cd0e97f3ff0c3bfb71cc7ddebfb0084f101272648bcee4159a83fb1"
EXP_STDOUT_SHA = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
EXP_JOURNAL_SHA = "ee7e4e661b2b8768b19fb1352683a14b49e725179e80a58bd62ce57718afec99"
EXP_EXEC_SHA = "b9d128240596c5c6b7c040480823f4cc653d26a4bc665fc69b396d00e4fe0ad8"
EXP_SUPERVISOR_SHA = "ce06475ea7030bd97b96f7fb1f61fdd5cb7f99254e821270f0a4dcbf32e9db46"
EXP_LAUNCHER_SHA = "8df467446a4fe7a1fdaf44a2e15889ea783ea2a8b4e81b773030c51d56697722"

# v1.21 (the fresh revision that carries the D95 supervisor repair).
EXP_V1_21_SUPERVISOR_REPAIR_CLASS = "D95_SUPERVISOR_RC_ZERO_ON_UNOBSERVED_TERMINATION"


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha_file(p: Path) -> str:
    return sha_bytes(Path(p).read_bytes())


def write_once(path: Path, data: bytes) -> str:
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    fd = os.open(str(path), flags, 0o644)
    try:
        w = 0
        while w < len(data):
            w += os.write(fd, data[w:])
        os.fsync(fd)
    finally:
        os.close(fd)
    if path.stat().st_size != len(data):
        raise OSError(f"POST_WRITE_SIZE_MISMATCH: {path}")
    return sha_bytes(data)


def main() -> int:
    if OUT.exists():
        print(f"REFUSE_OVERWRITE {OUT.name}", file=sys.stderr)
        return 1

    # ---- read-only evidence presence + SHA verification (FAIL CLOSED) ---- #
    missing = [str(p) for p in (P_START, P_PROCESS_EXIT, P_STDERR, P_STDOUT,
                                P_JOURNAL_START_BEGIN, P_EXEC, P_SUPERVISOR,
                                P_LAUNCHER) if not p.exists()]
    if missing:
        print(f"FAIL_CLOSED: missing evidence {missing}", file=sys.stderr)
        return 3

    obs = {
        "start": sha_file(P_START),
        "process_exit": sha_file(P_PROCESS_EXIT),
        "stderr": sha_file(P_STDERR),
        "stdout": sha_file(P_STDOUT),
        "journal_start_begin": sha_file(P_JOURNAL_START_BEGIN),
        "exec": sha_file(P_EXEC),
        "supervisor": sha_file(P_SUPERVISOR),
        "launcher": sha_file(P_LAUNCHER),
    }
    exp = {
        "start": EXP_START_SHA,
        "process_exit": EXP_PROCESS_EXIT_SHA,
        "stderr": EXP_STDERR_SHA,
        "stdout": EXP_STDOUT_SHA,
        "journal_start_begin": EXP_JOURNAL_SHA,
        "exec": EXP_EXEC_SHA,
        "supervisor": EXP_SUPERVISOR_SHA,
        "launcher": EXP_LAUNCHER_SHA,
    }
    drift = {k: {"observed": obs[k], "expected": exp[k]}
             for k in exp if obs[k] != exp[k]}
    if drift:
        print(f"FAIL_CLOSED: frozen evidence SHA drift {json.dumps(drift, indent=1)}",
              file=sys.stderr)
        return 3

    # ---- parse the durable evidence (read-only) -------------------------- #
    pe = json.loads(P_PROCESS_EXIT.read_text(encoding="utf-8"))
    start = json.loads(P_START.read_text(encoding="utf-8"))
    jrn = json.loads(P_JOURNAL_START_BEGIN.read_text(encoding="utf-8"))
    stderr_text = P_STDERR.read_text(encoding="utf-8")

    adj = {
        "artifact": "phase36_v1_20_interruption_adjudication_v1_0",
        "phase": 36,
        "revision": "ra_medfilm_barr_phase36_robustness_v1_20",
        "method": "RA-MedFiLM-BARR",
        "type": "INTERRUPTED_EXECUTION_ADJUDICATION",
        "mode": "STATIC_ADDITIVE_GOVERNANCE_ONLY_NON_CONSUMING",
        "generated_utc": "2026-10-11T00:00:00Z",
        "classification": "CONSUMED_INTERRUPTED_POST_START_PRE_SCIENTIFIC_RESULT",
        "real_dispatch_occurred": True,
        "attempt_consumed": True,
        "relaunch_permitted": False,
        "retry_permitted": False,
        "rerun_permitted": False,
        "v1_20_must_never_be_rerun": True,
        "is_scientific_model_failure": False,
        "scientific_result_written": False,
        "failure_marker_written": False,
        "post_start_pre_scientific_result": True,
        "interrupt_origin_established": False,
        "interrupt_origin_note": (
            "The ORIGIN of the KeyboardInterrupt is NOT established by durable "
            "evidence and is deliberately NOT claimed. Only the OBSERVED "
            "supervisor-visible outcome is adjudicated."),

        "bound_evidence": {
            "start_marker": {
                "path": "reports/audits/phase36_robustness_science_start_v1_20.json",
                "sha256": obs["start"],
                "size_bytes": P_START.stat().st_size,
                "mtime_utc": "2026-10-11T01:38:30Z",
                "present": True,
                "science_gate_state": start.get("science_gate_state"),
                "scientific_output": start.get("scientific_output"),
                "source_sha256": start.get("source_sha256"),
            },
            "process_exit": {
                "path": "reports/audits/phase36_robustness_science_process_exit_v1_20.json",
                "sha256": obs["process_exit"],
                "size_bytes": P_PROCESS_EXIT.stat().st_size,
                "mtime_utc": "2026-10-11T01:44:15Z",
                "present": True,
                "attempt_id": pe.get("attempt_id"),
                "supervisor_pid": pe.get("supervisor_pid"),
                "child_pid": pe.get("child_pid"),
                "child_exit_code": pe.get("child_exit_code"),
                "termination_observed": pe.get("termination_observed"),
                "START_present": pe.get("START_present"),
                "RESULT_present": pe.get("RESULT_present"),
                "FAILURE_present": pe.get("FAILURE_present"),
            },
            "stderr": {
                "path": "reports/audits/phase36_robustness_science_stderr_v1_20.txt",
                "sha256": obs["stderr"],
                "size_bytes": P_STDERR.stat().st_size,
                "mtime_utc": "2026-10-11T01:44:15Z",
                "present": True,
                "content": stderr_text,
                "supervisor_exception_observed": True,
                "supervisor_exception_type": "KeyboardInterrupt",
            },
            "stdout": {
                "path": "reports/audits/phase36_robustness_science_stdout_v1_20.txt",
                "sha256": obs["stdout"],
                "size_bytes": P_STDOUT.stat().st_size,
                "present": True,
                "empty": True,
            },
            "journal_start_begin_record": {
                "path": ("reports/audits/phase36_robustness_science_v1_20_journal/"
                         "000_START__BEGIN.json"),
                "sha256": obs["journal_start_begin"],
                "size_bytes": P_JOURNAL_START_BEGIN.stat().st_size,
                "mtime_utc": "2026-10-11T01:38:30Z",
                "present": True,
                "stage": jrn.get("stage"),
                "event": jrn.get("event"),
                "attempt_id": jrn.get("attempt_id"),
                "scientific_output": jrn.get("scientific_output"),
            },
            "v1_20_execution_source": {
                "path": "scripts/analysis/phase36_robustness_execution_v1_20.py",
                "sha256": obs["exec"],
                "size_bytes": P_EXEC.stat().st_size,
            },
            "v1_20_supervisor_source": {
                "path": "scripts/analysis/supervise_phase36_v1_20.py",
                "sha256": obs["supervisor"],
                "size_bytes": P_SUPERVISOR.stat().st_size,
            },
            "v1_20_launcher_source": {
                "path": "scripts/analysis/launch_phase36_v1_20.py",
                "sha256": obs["launcher"],
                "size_bytes": P_LAUNCHER.stat().st_size,
            },
        },

        "observed_state": {
            "START_present": True,
            "RESULT_present": False,
            "FAILURE_present": False,
            "journal_records": 1,
            "last_journal_stage": "START:BEGIN",
            "first_failed_stage": "POST_START__NO_SCIENTIFIC_RESULT",
            "child_exit_code": None,
            "termination_observed": False,
            "supervisor_exception_type": "KeyboardInterrupt",
            "supervisor_exception_message": "",
            "supervisor_returned_rc": 0,
            "supervisor_rc_zero_when_termination_unobserved": True,
            "scientific_outputs_written": False,
            "all_23_targets_absent": True,
        },

        "defect": {
            "id": "D95",
            "code": "V1_20_SUPERVISOR_RETURNS_ZERO_ON_UNOBSERVED_CHILD_TERMINATION",
            "description": (
                "supervise_phase36_v1_20.supervise_once() falls through to "
                "`return {\"rc\": 0, ...}` whenever termination_observed is False "
                "(including a KeyboardInterrupt raised from proc.communicate()). "
                "An UNOBSERVED child state is therefore masked as SUCCESS. The "
                "supervisor also does not deterministically terminate/wait for the "
                "launcher child/process tree and does not distinguish normal child "
                "completion vs supervisor interruption vs supervisor internal "
                "exception in PROCESS_EXIT."),
            "scientific_semantics_effect": "NONE",
            "governance_effect": "YES",
            "repaired_in": "v1.21",
            "repair_class": EXP_V1_21_SUPERVISOR_REPAIR_CLASS,
        },

        "effects": {
            "scientific_effect": "NONE",
            "runtime_effect": "NONE",
            "governance_history_accuracy": "YES",
        },

        "next_revision": {
            "revision": "v1.21",
            "scientific_delta_count_v1_20_to_v1_21": 0,
            "supervisor_repair_only": True,
        },

        "protected_populations": {
            "TEST": "PHASE39_ONLY_LOCKED",
            "ROUTER_HOLDOUT": "LOCKED",
        },
        "TEST_accessed": False,
        "ROUTER_HOLDOUT_accessed": False,
        "write_semantics": "O_CREAT|O_EXCL|O_WRONLY{+O_BINARY} + full-write + fsync + st_size check",
        "terminal": "PHASE36_V1_20_INTERRUPTION_ADJUDICATION_WRITTEN",
    }

    sha_out = write_once(OUT, (json.dumps(adj, indent=1) + "\n").encode("utf-8"))
    print(json.dumps({
        "written": str(OUT.relative_to(ROOT)).replace("\\", "/"),
        "sha256": sha_out,
        "size_bytes": OUT.stat().st_size,
        "classification": adj["classification"],
        "bound_evidence_sha256": obs,
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
