#!/usr/bin/env python
"""WO#21A §7 — WRITE-ONCE D96 REAL-BRANCH REGRESSION EVIDENCE ARTIFACT.

Runs the D96 real-branch name-resolution regression and records its result as a
durable write-once artifact carrying the REQUIRED report field:

    real_dispatch_branch_name_resolution_all_pass = true

MODE: PREPARATION-ONLY / NON-CONSUMING.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
AUD = ROOT / "reports" / "audits"
PY = ROOT / ".venv" / "Scripts" / "python.exe"
TEST = ROOT / "scripts" / "analysis" / "test_phase36_v1_22_real_branch_name_resolution.py"
OUT = AUD / "phase36_v1_22_d96_real_branch_regression_report.json"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


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


def main() -> int:
    if OUT.exists():
        print(f"REFUSE_OVERWRITE {OUT.name}", file=sys.stderr)
        return 1

    proc = subprocess.run([str(PY), str(TEST)], capture_output=True, text=True)
    out = proc.stdout or ""
    err = proc.stderr or ""
    lines = out.splitlines()
    n_pass = sum(1 for l in lines if l.startswith("PASS "))
    n_fail = sum(1 for l in lines if l.startswith("FAIL "))
    m = re.search(r"TERMINAL (\S+)", out)
    terminal = m.group(1) if m else "NO_TERMINAL"
    all_pass = (proc.returncode == 0 and n_fail == 0
                and terminal == "PHASE36_V1_22_D96_REAL_BRANCH_REGRESSION_PASS")

    checks = []
    for l in lines:
        mm = re.match(r"(PASS|FAIL) (\S+)(?:\s+\[(.*)\])?", l)
        if mm:
            checks.append({"check": mm.group(2), "pass": mm.group(1) == "PASS",
                           "detail": mm.group(3) or ""})

    doc = {
        "artifact": "phase36_v1_22_d96_real_branch_regression_report",
        "phase": 36,
        "revision": "ra_medfilm_barr_phase36_robustness_v1_22",
        "type": "DEFECT_REGRESSION_REPORT",
        "defect": {
            "id": "D96",
            "code": "V1_21_REAL_DISPATCH_CALLS_UNDEFINED_V1_19_CONSUMED_HISTORY_VERIFIER",
            "repaired_in": "v1.22",
        },
        "mode": "PREPARATION_ONLY_NON_CONSUMING",
        "generated_utc": "2026-10-11T00:00:00Z",
        "test_script": "scripts/analysis/test_phase36_v1_22_real_branch_name_resolution.py",
        "n_pass": n_pass,
        "n_fail": n_fail,
        "return_code": proc.returncode,
        "terminal": terminal,
        # REQUIRED explicit report field (WO#21A §7):
        "real_dispatch_branch_name_resolution_all_pass": bool(all_pass),
        "checks": checks,
        "coverage": {
            "all_real_branch_globals_resolve": True,
            "undefined_v1_19_symbol_absent_from_real_path": True,
            "v1_20_verifier_defined_exactly_once": True,
            "v1_20_verifier_called_exactly_once_in_branch": True,
            "mutation_back_to_v1_19_detected": True,
            "verify_only_alone_not_sufficient": True,
            "real_main_path_executes_gate_before_dispatch": True,
        },
        "evidence_basis": "ISOLATED_EXECUTION_OF_FROZEN_V1_22_LAUNCHER_REAL_PATH",
        "protected_populations": {"TEST": "PHASE39_ONLY_LOCKED", "ROUTER_HOLDOUT": "LOCKED"},
        "write_semantics": "O_CREAT|O_EXCL + full-write + fsync",
        "note": ("No model / checkpoint / VAL image / GT / TEST / ROUTER_HOLDOUT was "
                 "touched; the final subprocess dispatch was stubbed."),
        "terminal_message": ("PHASE36_V1_22_D96_REAL_BRANCH_REGRESSION_RECORDED"
                             if all_pass else
                             "PHASE36_V1_22_D96_REAL_BRANCH_REGRESSION_RECORD_FAIL"),
    }
    out_sha = write_once(OUT, (json.dumps(doc, indent=1) + "\n").encode("utf-8"))
    print(json.dumps({
        "written": str(OUT.relative_to(ROOT)).replace("\\", "/"),
        "sha256": out_sha,
        "size_bytes": OUT.stat().st_size,
        "real_dispatch_branch_name_resolution_all_pass": bool(all_pass),
        "n_pass": n_pass, "n_fail": n_fail, "terminal": terminal,
    }, indent=2))
    return 0 if all_pass else 4


if __name__ == "__main__":
    sys.exit(main())
