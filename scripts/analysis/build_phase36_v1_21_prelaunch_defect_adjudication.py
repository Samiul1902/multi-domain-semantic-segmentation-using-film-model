#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""WO#21A §1 — WRITE-ONCE v1.21 PRELAUNCH-DEFECT ADJUDICATION (D96).

MODE: PREPARATION-ONLY / NON-CONSUMING.

v1.21 HAS NOT BEEN EXECUTED.  v1.20 remains the last consumed real attempt.

A direct independent audit of the frozen v1.21 launcher established:

    REAL DISPATCH currently calls:

        verify_v1_19_consumed_history()

    but that symbol is NOT defined anywhere in the v1.21 launcher.  The launcher
    actually DEFINES ``verify_v1_20_consumed_history()`` (the correct verifier for
    the consumed v1.20 state).  This escaped ``--verify-only`` because verify-only
    RETURNS before the real-dispatch branch.

    D96 = V1_21_REAL_DISPATCH_CALLS_UNDEFINED_V1_19_CONSUMED_HISTORY_VERIFIER

This builder is FAIL-CLOSED on ANY drift: it re-derives the defect from the
frozen v1.21 launcher (SHA-pinned), confirms all v1.21 attempt markers are ABSENT,
and refuses to overwrite an existing adjudication.

Classification: NOT_EXECUTED__PRELAUNCH_REAL_PATH_DEFECT
(v1.21 is NEVER classified as a consumed attempt).
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
AUD = ROOT / "reports" / "audits"

LAUNCHER_V121 = ROOT / "scripts" / "analysis" / "launch_phase36_v1_21.py"
EXEC_V121 = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_21.py"
OUT = AUD / "phase36_v1_21_prelaunch_defect_adjudication_v1_0.json"

FROZEN_LAUNCHER_V121_SHA = (
    "0711fd79ca117dedaf8eae1eb024d0754033e0417c506bd748577fec73402208")
FROZEN_EXEC_V121_SHA = (
    "312886c68f056375adc3f091766777da9e1caa47c1d422673de67751e8df7b97")

# v1.20 consumed state (last consumed real attempt).
V1_20_ADJUDICATION = AUD / "phase36_v1_20_interruption_adjudication_v1_0.json"
V1_20_ADJUDICATION_SHA = (
    "31c29955380c6ec75d18f747dec4f91332177ddabeccef40cb0cafa8b37f5b72")

# v1.21 attempt markers (must ALL be ABSENT).
V1_21_START = AUD / "phase36_robustness_science_start_v1_21.json"
V1_21_RESULT = AUD / "phase36_robustness_scientific_result_v1_21.json"
V1_21_FAILURE = AUD / "phase36_robustness_science_failure_v1_21.json"
V1_21_PROCESS_EXIT = AUD / "phase36_robustness_science_process_exit_v1_21.json"
V1_21_JOURNAL = AUD / "phase36_robustness_science_v1_21_journal"
V1_21_STDOUT = AUD / "phase36_robustness_science_stdout_v1_21.txt"
V1_21_STDERR = AUD / "phase36_robustness_science_stderr_v1_21.txt"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha_file(p: Path) -> str:
    return sha(Path(p).read_bytes())


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
    return sha(data)


def _audit_defect() -> dict:
    """Re-derive D96 from the frozen launcher AST. FAIL-CLOSED on any deviation."""
    src = LAUNCHER_V121.read_text(encoding="utf-8")
    tree = ast.parse(src)

    defined = set()
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defined.add(n.name)
        elif isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name):
                    defined.add(t.id)
        elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
            defined.add(n.target.id)

    calls_19 = [n.lineno for n in ast.walk(tree)
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                and n.func.id == "verify_v1_19_consumed_history"]
    calls_20 = [n.lineno for n in ast.walk(tree)
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                and n.func.id == "verify_v1_20_consumed_history"]

    main = next(n for n in tree.body
                if isinstance(n, ast.FunctionDef) and n.name == "main")
    verify_only_if_line = None
    for st in main.body:
        if isinstance(st, ast.If):
            seg = ast.get_source_segment(src, st) or ""
            if "--verify-only" in seg:
                verify_only_if_line = st.lineno
                break

    return {
        "called_symbol": "verify_v1_19_consumed_history",
        "called_symbol_defined": ("verify_v1_19_consumed_history" in defined),
        "called_symbol_call_sites": calls_19,
        "defined_symbol": "verify_v1_20_consumed_history",
        "defined_symbol_defined": ("verify_v1_20_consumed_history" in defined),
        "defined_symbol_call_sites": calls_20,
        "main_verify_only_early_return_line": verify_only_if_line,
        "defect_confirmed": (
            ("verify_v1_19_consumed_history" not in defined)
            and (len(calls_19) == 1)
            and ("verify_v1_20_consumed_history" in defined)
            and (len(calls_20) == 0)
            and verify_only_if_line is not None
            and calls_19[0] > verify_only_if_line
        ),
    }


def main() -> int:
    if OUT.exists():
        print(f"REFUSE_OVERWRITE {OUT.name}", file=sys.stderr)
        return 1

    # FAIL-CLOSED: frozen v1.21 launcher + exec SHAs unchanged.
    l_sha = sha_file(LAUNCHER_V121)
    if l_sha != FROZEN_LAUNCHER_V121_SHA:
        print(f"FAIL_CLOSED: v1.21 launcher SHA drift {l_sha}", file=sys.stderr)
        return 3
    e_sha = sha_file(EXEC_V121)
    if e_sha != FROZEN_EXEC_V121_SHA:
        print(f"FAIL_CLOSED: v1.21 exec SHA drift {e_sha}", file=sys.stderr)
        return 3

    # FAIL-CLOSED: v1.20 remains the last consumed real attempt.
    if not V1_20_ADJUDICATION.exists():
        print("FAIL_CLOSED: v1.20 interruption adjudication absent", file=sys.stderr)
        return 3
    v120_sha = sha_file(V1_20_ADJUDICATION)
    if v120_sha != V1_20_ADJUDICATION_SHA:
        print(f"FAIL_CLOSED: v1.20 adjudication SHA drift {v120_sha}", file=sys.stderr)
        return 3
    v120_doc = json.loads(V1_20_ADJUDICATION.read_text(encoding="utf-8"))

    # FAIL-CLOSED: every v1.21 attempt marker ABSENT (v1.21 NEVER executed).
    marker_state = {
        "START": V1_21_START.exists(),
        "RESULT": V1_21_RESULT.exists(),
        "FAILURE": V1_21_FAILURE.exists(),
        "PROCESS_EXIT": V1_21_PROCESS_EXIT.exists(),
        "JOURNAL_DIR": V1_21_JOURNAL.exists(),
        "STDOUT": V1_21_STDOUT.exists(),
        "STDERR": V1_21_STDERR.exists(),
    }
    if any(marker_state.values()):
        print(f"FAIL_CLOSED: v1.21 attempt marker present {marker_state}", file=sys.stderr)
        return 4

    defect = _audit_defect()
    if not defect["defect_confirmed"]:
        print(f"FAIL_CLOSED: D96 not reproducible from frozen launcher {defect}",
              file=sys.stderr)
        return 5

    doc = {
        "artifact": "phase36_v1_21_prelaunch_defect_adjudication",
        "phase": 36,
        "revision": "ra_medfilm_barr_phase36_robustness_v1_21",
        "type": "PRELAUNCH_REAL_PATH_DEFECT_ADJUDICATION",
        "mode": "PREPARATION_ONLY_NON_CONSUMING",
        "generated_utc": "2026-10-11T00:00:00Z",
        "classification": "NOT_EXECUTED__PRELAUNCH_REAL_PATH_DEFECT",
        "v1_21_executed": False,
        "real_dispatch_occurred": False,
        "attempt_consumed": False,
        "scientific_execution": False,
        "relaunch_permitted": False,
        "rerun_permitted": False,
        "is_scientific_model_failure": False,
        "is_consumed_attempt": False,
        "interrupt_origin_established": False,
        "v1_20_remains_last_consumed_real_attempt": True,
        "bound_v1_21_launcher_sha256": l_sha,
        "bound_v1_21_execution_sha256": e_sha,
        "v1_20_consumed_state": {
            "adjudication": "reports/audits/phase36_v1_20_interruption_adjudication_v1_0.json",
            "adjudication_sha256": v120_sha,
            "classification": v120_doc.get("classification"),
            "attempt_consumed": bool(v120_doc.get("attempt_consumed")),
        },
        "attempt_marker_state_v1_21": {
            "START_present": marker_state["START"],
            "RESULT_present": marker_state["RESULT"],
            "FAILURE_present": marker_state["FAILURE"],
            "PROCESS_EXIT_present": marker_state["PROCESS_EXIT"],
            "JOURNAL_DIR_present": marker_state["JOURNAL_DIR"],
            "STDOUT_present": marker_state["STDOUT"],
            "STDERR_present": marker_state["STDERR"],
        },
        "defect": {
            "id": "D96",
            "code": "V1_21_REAL_DISPATCH_CALLS_UNDEFINED_V1_19_CONSUMED_HISTORY_VERIFIER",
            "called_symbol": defect["called_symbol"],
            "called_symbol_defined": defect["called_symbol_defined"],
            "called_symbol_call_sites": defect["called_symbol_call_sites"],
            "defined_symbol": defect["defined_symbol"],
            "defined_symbol_defined": defect["defined_symbol_defined"],
            "defined_symbol_call_sites": defect["defined_symbol_call_sites"],
            "main_verify_only_early_return_line": defect["main_verify_only_early_return_line"],
            "escaped_verify_only": True,
            "escape_reason": ("--verify-only returns BEFORE the real-dispatch branch, "
                              "so the undefined call was never exercised in verify-only."),
            "real_dispatch_effect": ("NameError: name 'verify_v1_19_consumed_history' "
                                     "is not defined, at the consumed-history gate, "
                                     "BEFORE any dispatch / token set / model load."),
            "scientific_semantics_effect": "NONE",
            "operational_effect": "YES",
            "repaired_in": "v1.22",
            "repair_scope": "LAUNCHER_REAL_DISPATCH_CALL_ONLY",
        },
        "evidence_basis": "INDEPENDENT_AUDIT_OF_FROZEN_V1_21_LAUNCHER",
        "independent_audit_reproduced_by_builder": True,
        "protected_populations": {"TEST": "PHASE39_ONLY_LOCKED", "ROUTER_HOLDOUT": "LOCKED"},
        "write_semantics": "O_CREAT|O_EXCL + full-write + fsync",
        "terminal": "PHASE36_V1_21_PRELAUNCH_DEFECT_ADJUDICATED",
    }
    out_sha = write_once(OUT, (json.dumps(doc, indent=1) + "\n").encode("utf-8"))
    print(json.dumps({
        "written": str(OUT.relative_to(ROOT)).replace("\\", "/"),
        "sha256": out_sha,
        "size_bytes": OUT.stat().st_size,
        "classification": doc["classification"],
        "defect": doc["defect"]["id"],
        "defect_confirmed": True,
        "attempt_consumed": False,
        "real_dispatch_occurred": False,
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
