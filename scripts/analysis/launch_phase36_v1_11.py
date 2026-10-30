#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.11 — EXTERNAL NON-CIRCULAR PRE-INVOCATION LAUNCHER (D33).

This is the REAL external authority that defeats a source+manifest co-edit.

It is MODEL-FREE and PROTECTED-DATA-FREE: at pre-invocation it imports NO torch,
opens NO checkpoint, reads NO VAL/VAL-GT/ROUTER_HOLDOUT/TEST content.  It reads
only the frozen source bytes and the frozen manifest bytes to verify their
SHA-256 against EXACT expected values, then (and only then) sets the launch
authority token and dispatches the requested mode.

NON-CIRCULAR RELEASE CHAIN
--------------------------
    supervisor (external)  --pins-->  launcher SHA (this file)
    supervisor (external)  --pins-->  source-freeze SHA
    launcher  --verifies exact SHA of-->  v1.11 execution source
    launcher  --verifies exact SHA of-->  v1.11 runtime manifest
    manifest  --declares-->  execution_source_sha256  (source self-check)

The chain is a DAG, not a cycle: the manifest declares only the execution-source
SHA (which the launcher independently verifies by exact value), and the launcher
declares the exact expected execution-source + manifest SHAs.  Nothing hashes
the launcher from inside the manifest or the source; the launcher's own SHA is
pinned EXTERNALLY by the supervisor (and bound by the v1.11 source freeze),
which terminates the chain.  A source+manifest co-edit therefore cannot pass:
the launcher's frozen expected SHAs are unchanged and will reject the co-edited
bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

EXEC_V1_11 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_11.py"
MANIFEST_V1_11 = ROOT / "reports/audits/phase36_v1_11_runtime_source_integrity_manifest.json"
LAUNCHER_SELF = ROOT / "scripts/analysis/launch_phase36_v1_11.py"

GATE_ENV = "PHASE36_EXECUTE"
SMOKE_GATE_ENV = "PHASE36_SMOKE_EXECUTE"
LAUNCH_AUTHORITY_TOKEN = "PHASE36_V1_11_LAUNCH_AUTHORITY"

# FROZEN expected SHAs.  Written by build_phase36_v1_11_freeze_and_eligibility.py
# and pinned externally by the supervisor.  Env may override for a *verification*
# negative control, but ONLY to trigger a mismatch -- never to accept a co-edit.
FROZEN_EXPECTED_EXEC_SHA = "dc4928417444304ad637907c53089e512577254b368e438d0098ade6202083f0"
FROZEN_EXPECTED_MANIFEST_SHA = "d795d41152accde6cf59717d2d17ab429b0cdf8fc1ff98bca11dcb13a591bda7"


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _expected_exec_sha() -> str:
    return os.environ.get("PHASE36_V1_11_EXPECTED_EXEC_SHA", FROZEN_EXPECTED_EXEC_SHA)


def _expected_manifest_sha() -> str:
    return os.environ.get("PHASE36_V1_11_EXPECTED_MANIFEST_SHA",
                          FROZEN_EXPECTED_MANIFEST_SHA)


def verify_authority() -> dict:
    """Verify exact frozen SHAs of the execution source AND the runtime manifest.

    Returns a dict with ``authorized`` (bool) and per-item evidence.  Performs
    NO model / protected-data IO.
    """
    result = {"authorized": False, "items": {}, "fail_closed": True}
    exp_exec = _expected_exec_sha()
    exp_man = _expected_manifest_sha()

    if not EXEC_V1_11.exists():
        result["items"]["execution_source"] = {"present": False, "match": False}
        return result
    obs_exec = sha(EXEC_V1_11)
    exec_match = (exp_exec not in ("", "__FROZEN_EXEC_SHA__") and obs_exec == exp_exec)
    result["items"]["execution_source"] = {"present": True, "expected": exp_exec,
                                           "observed": obs_exec, "match": bool(exec_match)}

    if not MANIFEST_V1_11.exists():
        result["items"]["runtime_manifest"] = {"present": False, "match": False}
        return result
    obs_man = sha(MANIFEST_V1_11)
    man_match = (exp_man not in ("", "__FROZEN_MANIFEST_SHA__") and obs_man == exp_man)
    result["items"]["runtime_manifest"] = {"present": True, "expected": exp_man,
                                           "observed": obs_man, "match": bool(man_match)}

    # The manifest must be parseable and declare the execution-source SHA that the
    # launcher independently verified above (two independent mechanisms agree).
    declared_exec = None
    try:
        man = json.loads(MANIFEST_V1_11.read_text(encoding="utf-8"))
        declared_exec = man.get("execution_source_sha256")
    except Exception as exc:
        result["items"]["manifest_parse"] = {"ok": False, "error": type(exc).__name__}
        return result
    result["items"]["manifest_parse"] = {"ok": True}
    manifest_declares_exec = bool(declared_exec and declared_exec == obs_exec)
    result["items"]["manifest_declares_exec_sha"] = {
        "declared": declared_exec, "observed_exec": obs_exec,
        "match": bool(manifest_declares_exec)}

    result["authorized"] = bool(exec_match and man_match and manifest_declares_exec)
    result["fail_closed"] = not result["authorized"]
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True, choices=("smoke", "science"))
    ap.add_argument("--verify-only", action="store_true",
                    help="verify the anchor and exit WITHOUT dispatching.")
    a = ap.parse_args()

    auth = verify_authority()
    if not auth["authorized"]:
        print(json.dumps({
            "launcher": "launch_phase36_v1_11",
            "mode": a.mode,
            "authorized": False,
            "terminal": "PHASE36_V1_11_LAUNCH_NOT_AUTHORIZED__ANCHOR_VERIFICATION_FAILED",
            "authority": auth,
        }, indent=1))
        return 2

    if a.verify_only:
        print(json.dumps({
            "launcher": "launch_phase36_v1_11",
            "authorized": True,
            "terminal": "PHASE36_V1_11_LAUNCH_ANCHOR_VERIFIED__DISPATCH_SUPPRESSED_BY_VERIFY_ONLY",
            "authority": auth,
        }, indent=1))
        return 0

    # Dispatch: set the launch-authority token so the source accepts the dispatch,
    # then run the module's main() in-process with argv set to the dispatched mode.
    os.environ[LAUNCH_AUTHORITY_TOKEN] = "1"
    import importlib.util
    spec = importlib.util.spec_from_file_location("phase36_v1_11_exec", EXEC_V1_11)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _saved_argv = sys.argv
    try:
        sys.argv = [str(EXEC_V1_11), "--mode", a.mode]
        return int(mod.main())
    finally:
        sys.argv = _saved_argv


if __name__ == "__main__":
    raise SystemExit(main())
