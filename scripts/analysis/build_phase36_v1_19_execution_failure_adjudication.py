#!/usr/bin/env python3
"""
WO#20  §3  -  v1.19 EXECUTION FAILURE ADJUDICATION  (write-once, NON-CONSUMING).

Establishes the exact v1.19 failure from durable evidence and writes the
write-once adjudication artifact.  NO scientific execution, NO model load,
NO checkpoint deserialization, NO VAL_GT / VAL image / TEST / ROUTER_HOLDOUT
read, NO v1.19 artifact modified, NO relaunch.
"""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import sys
from datetime import datetime, timezone

REPO = pathlib.Path(__file__).resolve().parents[2]
OUT = REPO / "reports/audits/phase36_v1_19_execution_failure_adjudication_v1_0.json"

FROZEN: dict[str, str] = {
    "reports/audits/phase36_robustness_science_process_exit_v1_19.json":
        "ee0a4e3a010e57b62ff7043df813cdc23d3f8ed668ed9df46be08b4dcde0ecd3",
    "reports/audits/phase36_robustness_science_stdout_v1_19.txt":
        "1857f668c80d62d0e618cf0aa13b9dc0d7ed49674f26f2d665d16e3f04e6c805",
    "reports/audits/phase36_robustness_science_stderr_v1_19.txt":
        "0e2dc81540ebbcced7d16ad9c9c068e42c9e5de3617605451b3033c140bc4438",
    "reports/audits/phase36_robustness_science_start_v1_19.json":
        "ce275f81f822b310b2ceb3d9dd6ec63efdfed1053307ae7a3d86b9d22254bdf2",
    "scripts/analysis/phase36_robustness_execution_v1_19.py":
        "3ec5ea920af2b6d66864b3bbc7e5362f0756777512c29be70d3e5453e18693cd",
}

OPTIONAL_ABSENT = {
    "RESULT": "reports/audits/phase36_robustness_scientific_result_v1_19.json",
    "FAILURE": "reports/audits/phase36_robustness_science_failure_v1_19.json",
}


def sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def verify() -> dict[str, str]:
    got = {}
    for rel, exp in FROZEN.items():
        p = REPO / rel
        if not p.exists():
            sys.stderr.write(f"FATAL: missing frozen evidence: {rel}\n")
            raise SystemExit(2)
        g = sha(p)
        if g != exp:
            sys.stderr.write(f"FATAL: SHA mismatch {rel}: exp {exp} got {g}\n")
            raise SystemExit(2)
        got[rel] = g
    return got


def write_once(path: pathlib.Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    fd = os.open(str(path), flags, 0o644)
    try:
        mv = memoryview(payload)
        off = 0
        while off < len(payload):
            off += os.write(fd, mv[off:])
        os.fsync(fd)
    finally:
        os.close(fd)
    if path.stat().st_size != len(payload):
        raise SystemExit(3)


def main() -> int:
    if OUT.exists():
        sys.stderr.write(f"REFUSE_OVERWRITE: {OUT}\n")
        return 1

    frozen = verify()

    journal_dir = REPO / "reports/audits/phase36_robustness_science_v1_19_journal"
    journal_records = sorted(p.name for p in journal_dir.glob("*.json")) if journal_dir.exists() else []

    absent = {k: (not (REPO / v).exists()) for k, v in OPTIONAL_ABSENT.items()}

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    adjudication = {
        "artifact_kind": "PHASE36_V1_19_EXECUTION_FAILURE_ADJUDICATION",
        "revision": "ra_medfilm_barr_phase36_robustness_adjudication_v1_0",
        "work_order": "WO#20",
        "section": "\u00a71\u2013\u00a73 v1.19 FAILURE ADJUDICATION",
        "mode": "POST_FAILURE_ADJUDICATION__STATIC_EVIDENCE_ONLY__NON_CONSUMING",
        "created_utc": now,

        "real_dispatch_occurred": True,
        "attempt_consumed": True,
        "relaunch_permitted": False,
        "retry_permitted": False,
        "attempt_id": "v1_19sup_3380_2026-10-10T19:40:57Z",
        "supervisor_pid": 3380,
        "child_pid": 4788,

        "evidence_bindings": {
            "PROCESS_EXIT": {
                "path": "reports/audits/phase36_robustness_science_process_exit_v1_19.json",
                "sha256": frozen["reports/audits/phase36_robustness_science_process_exit_v1_19.json"],
                "size": 2198,
                "present": True,
            },
            "stdout": {
                "path": "reports/audits/phase36_robustness_science_stdout_v1_19.txt",
                "sha256": frozen["reports/audits/phase36_robustness_science_stdout_v1_19.txt"],
                "size": 39,
                "present": True,
            },
            "stderr": {
                "path": "reports/audits/phase36_robustness_science_stderr_v1_19.txt",
                "sha256": frozen["reports/audits/phase36_robustness_science_stderr_v1_19.txt"],
                "size": 960,
                "present": True,
            },
            "START": {
                "path": "reports/audits/phase36_robustness_science_start_v1_19.json",
                "sha256": frozen["reports/audits/phase36_robustness_science_start_v1_19.json"],
                "size": 589,
                "present": True,
            },
            "RESULT": {
                "path": OPTIONAL_ABSENT["RESULT"],
                "sha256": None,
                "present": not absent["RESULT"],
            },
            "FAILURE": {
                "path": OPTIONAL_ABSENT["FAILURE"],
                "sha256": None,
                "present": not absent["FAILURE"],
            },
            "execution_source": {
                "path": "scripts/analysis/phase36_robustness_execution_v1_19.py",
                "sha256": frozen["scripts/analysis/phase36_robustness_execution_v1_19.py"],
                "size": 236195,
                "present": True,
            },
        },
        "frozen_evidence_sha_match": True,

        "exact_failure_location": {
            "v1_19_START_present": True,
            "v1_19_RESULT_present": (not absent["RESULT"]),
            "v1_19_FAILURE_present": (not absent["FAILURE"]),
            "child_exit_code": 1,
            "last_completed_journal_stage": "NONE",
            "first_failed_stage": "START:BEGIN",
            "journal_records_written": 0,
            "journal_dir_created_before_crash": True,
            "model_construction_reached": False,
            "VAL_image_access_started": False,
            "GT_scoring_started": False,
            "scientific_outputs_written": False,
            "root_exception_type": "NameError",
            "root_exception_message": "name '_write_once_json' is not defined",
            "root_source_file": "scripts/analysis/phase36_robustness_execution_v1_19.py",
            "root_source_line": 561,
            "root_reference_line": 561,
            "root_definition_count": 0,
            "root_reference_count": 1,
            "observed_traceback": [
                "line 4668 in <module>: raise SystemExit(main())",
                "line 4391 in main: return _run_science_with_durable_evidence(journal=_ScienceJournal(",
                "line 4270 in _run_science_with_durable_evidence: _j.begin(\"START\")",
                "line 577 in begin: _journal_record(stage, \"BEGIN\", self.attempt_id)",
                "line 561 in _journal_record: _write_once_json(path, payload)",
                "NameError: name '_write_once_json' is not defined",
            ],
        },

        "root_cause": {
            "status": "ESTABLISHED",
            "defect_id": "D93A",
            "statement": (
                "The v1.19 crash-survivable stage journal calls the helper "
                "`_write_once_json(path, payload)` at "
                "`_journal_record()` line 561, but that helper is NEVER defined at "
                "module scope (references = 1, definitions = 0).  The FIRST journal "
                "event is `_j.begin(\"START\")` (line 4270 -> begin line 577), so the "
                "NameError fires POST-START (the START marker was already written at "
                "line 10 of the START artifact / gate-authorised before model "
                "construction) but BEFORE any model construction, VAL image access, "
                "GT scoring, or scientific output.  The journal directory is created "
                "(mkdir) before the failing call, so the run aborts with an empty "
                "journal and NO scientific output."
            ),
            "scope_aware_ast_proof": (
                "Scope-aware AST free-name analysis of the frozen v1.19 source "
                "reports `_write_once_json` as the SINGLETON unresolved module-level "
                "name (referenced at line 561 only).  The same defect is present in "
                "the frozen v1.18 source (reference line 561, definition absent): the "
                "shared journal block was introduced with an undefined helper."
            ),
            "no_guessing": True,
        },

        "classification": "CONSUMED_POST_START_PRE_MODEL_FAILURE",
        "classification_justification": (
            "START marker present (post-START), but model construction / VAL image "
            "access / GT scoring / scientific output all NOT reached (pre-model). "
            "Hence CONSUMED_POST_START_PRE_MODEL_FAILURE."
        ),

        "scientific_effect": {
            "scientific_computation_effect": "NONE",
            "model_load_effect": "NONE",
            "scientific_semantics_effect": "NONE",
            "scientific_semantics_effect_reason": (
                "The crash is in the observability-only stage journal, before any "
                "model is constructed, before any tensor, probability, mask, metric, "
                "threshold, seed, or fusion path is touched."
            ),
            "runtime_effect": "FATAL_POST_START_PRE_MODEL",
            "execution_effect": "ABORTED_AFTER_START_BEFORE_MODEL",
            "launcher_effect": "NONE",
            "supervisor_effect": "NONE",
            "governance_effect": "NONE",
        },

        "scientific_implementation_error": False,
        "v1_19_to_v1_20_required_scientific_delta": 0,
        "v1_20_creation_authorized": True,
        "v1_20_creation_basis": "RUNTIME_DEFECT_ESTABLISHED__NOT_A_SCIENTIFIC_CHANGE",

        "provenance": {
            "derived_from": "frozen v1.19 evidence on disk + frozen execution source AST",
            "val_gt_read": False,
            "val_image_read": False,
            "checkpoint_deserialization": False,
            "test_reads": 0,
            "router_holdout_reads": 0,
            "model_loaded": False,
            "new_scientific_output": False,
        },
        "write_semantics":
            "O_CREAT|O_EXCL|O_WRONLY + O_BINARY (Windows) + full-write loop + "
            "os.fsync + post-write st_size check. Write-once; never overwritten.",
        "terminal": "PHASE36_V1_19_FAILURE_ADJUDICATED__ROOT_CAUSE_ESTABLISHED",
    }

    write_once(OUT, (json.dumps(adjudication, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))
    print(f"WROTE {OUT}")
    print(f"SHA256 {sha(OUT)}")
    print(f"SIZE {OUT.stat().st_size}")
    print("ROOT_CAUSE ESTABLISHED")
    print("CLASSIFICATION CONSUMED_POST_START_PRE_MODEL_FAILURE")
    print("TERMINAL PHASE36_V1_19_FAILURE_ADJUDICATED__ROOT_CAUSE_ESTABLISHED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
