#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.12 — IMMUTABLE NON-CIRCULAR PRE-INVOCATION LAUNCHER.

ADDITIVE over the v1.11 launcher (history preserved byte-for-byte).  This is the
REAL external authority that defeats a source+manifest co-edit.

It is MODEL-FREE and PROTECTED-DATA-FREE: at pre-invocation it imports NO torch,
opens NO checkpoint, and reads NO VAL/VAL-GT/ROUTER_HOLDOUT/TEST content.  It
reads only the frozen execution-source bytes and the frozen runtime-manifest
bytes to verify their SHA-256 against EXACT frozen constants, then (and only
then) sets the launch authority token and dispatches the requested mode.

=========================================================================== #
DEFECTS REPAIRED IN V1.12 (proven from the frozen v1.11 bytes)             #
=========================================================================== #
  D34 SOURCE/MANIFEST LAUNCH-ANCHOR CONTRADICTION
      v1.11 execution source required ``manifest["launcher_sha256"]`` while the
      frozen manifest deliberately OMITS that key and the v1.11 unit suite
      required it absent -> canonical v1.11 could NEVER pass.  The v1.12
      execution source (``phase36_robustness_execution_v1_12.py``) removes that
      requirement and FAILS CLOSED if ``launcher_sha256`` unexpectedly appears.
      This launcher's contract is unchanged in that respect: it verifies the
      exact execution-source + manifest SHAs and NEVER asks the manifest to
      declare its own SHA.  The chain stays a DAG (no cycle).
  D35 FROZEN LAUNCH HASHES MUST NOT BE ENV-OVERRIDABLE
      The v1.11 launcher resolved its expected hashes through
      ``os.environ.get("PHASE36_V1_11_EXPECTED_EXEC_SHA", FROZEN_EXPECTED_EXEC_SHA)``
      (and the manifest equivalent), defeating the external immutable anchor.
      A co-edited source+manifest could supply their new hashes through those
      variables.  THIS v1.12 launcher uses LITERAL frozen constants ONLY.  There
      is NO environment, CLI, config, or attribute mechanism capable of
      replacing ``FROZEN_EXPECTED_EXEC_SHA`` / ``FROZEN_EXPECTED_MANIFEST_SHA``
      for AUTHORIZATION.  The old override env names (``PHASE36_V1_11_*`` and
      any ``PHASE36_V1_12_*EXPECTED*`` variant) are read by NOTHING here and
      therefore cannot alter the production expected-hash authority.
      NOTE on negative-control testing (D35): a separate in-memory test harness
      (``phase36_robustness_negative_controls_v1_12.py``) MAY pass mutated temp
      bytes / a temp root to ``verify_authority(...)`` to exercise rejection
      logic.  That hook accepts ONLY paths to files on disk; it CANNOT change
      the frozen expected-hash CONSTANTS and it is NOT reachable from
      ``main()``'s production dispatch, so it does NOT weaken this launcher.
  D36 THREE-FILE VALIDATION CROSS-BINDING
      v1.11 validated the manifest and the source in isolation (proving
      "manifest has NO launcher_sha256" while failing to see "source REQUIRED
      launcher_sha256").  v1.12 validates the launch-anchor contract across ALL
      THREE files (execution source, launcher, manifest) and proves they are
      MUTUALLY SATISFIABLE.  The cross-contract test lives in the v1.12 unit /
      preflight suites and uses this launcher's ``verify_authority`` entry point.

=========================================================================== #
NON-CIRCULAR RELEASE CHAIN (v1.12)                                          #
=========================================================================== #
    supervisor (external)  --pins-->  launcher SHA (this file)
    supervisor (external)  --pins-->  source-freeze SHA
    launcher  --verifies exact SHA of-->  v1.12 execution source (literal const)
    launcher  --verifies exact SHA of-->  v1.12 runtime manifest  (literal const)
    manifest  --declares-->  execution_source_sha256  (source self-check)
    execution source  --requires-->  launch-authority TOKEN (NOT a manifest hash)

The chain is a DAG, not a cycle: the manifest declares only the execution-source
SHA (which the launcher independently verifies by exact frozen value), and the
launcher declares the exact expected execution-source + manifest SHAs as LITERAL
constants.  Nothing hashes the launcher from inside the manifest or the source;
the launcher's own SHA is pinned EXTERNALLY by the supervisor (and bound by the
v1.12 source freeze), which terminates the chain.  A source+manifest co-edit
therefore cannot pass: the launcher's literal frozen expected SHAs are unchanged
and will reject the co-edited bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

EXEC_V1_12 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_12.py"
MANIFEST_V1_12 = ROOT / "reports/audits/phase36_v1_12_runtime_source_integrity_manifest.json"
LAUNCHER_SELF = ROOT / "scripts/analysis/launch_phase36_v1_12.py"

GATE_ENV = "PHASE36_EXECUTE"
SMOKE_GATE_ENV = "PHASE36_SMOKE_EXECUTE"
LAUNCH_AUTHORITY_TOKEN = "PHASE36_V1_12_LAUNCH_AUTHORITY"

# --------------------------------------------------------------------------- #
# FROZEN expected SHAs — LITERAL, IMMUTABLE, NON-ENV-OVERRIDABLE (D35).
# Written by build_phase36_v1_12_freeze_and_eligibility.py and pinned EXTERNALLY
# by the supervisor.  These are the SOLE authorization authority: no env var,
# CLI flag, config file, or attribute assignment can substitute for them.
# --------------------------------------------------------------------------- #
FROZEN_EXPECTED_EXEC_SHA = "8ed75a9b8f4ea8c204875bf1810e17df3f9c342a434f25399154f355ee888ea4"
FROZEN_EXPECTED_MANIFEST_SHA = "f75b719e125ac85f901950034c7364bb77614831ce425660d41d2a9f432b1b35"

# Placeholder sentinels that can never be a real SHA (frozen-source fail-closed).
_EXEC_PLACEHOLDER = "__FROZEN_EXEC_SHA__"
_MANIFEST_PLACEHOLDER = "__FROZEN_MANIFEST_SHA__"


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _frozen_expected_exec_sha() -> str:
    """Return the IMMUTABLE frozen expected execution-source SHA.

    D35: this function reads NO environment variable, NO CLI argument, and NO
    config.  It returns the literal module constant unconditionally.  The
    indirection exists only to make the immutability contract explicit and
    auditable by the unit suite (which asserts the body references no
    ``os.environ`` / ``getenv``).
    """
    return FROZEN_EXPECTED_EXEC_SHA


def _frozen_expected_manifest_sha() -> str:
    """Return the IMMUTABLE frozen expected runtime-manifest SHA (D35)."""
    return FROZEN_EXPECTED_MANIFEST_SHA


def verify_authority(
    exec_path: Path | None = None,
    manifest_path: Path | None = None,
) -> dict:
    """Verify exact frozen SHAs of the execution source AND the runtime manifest.

    Returns a dict with ``authorized`` (bool) and per-item evidence.  Performs
    NO model / protected-data IO.

    D35 SAFETY: ``exec_path`` / ``manifest_path`` default to the canonical
    production paths.  They exist ONLY so a SEPARATE negative-control harness can
    point at mutated temp copies to exercise rejection logic.  They can NEVER
    change the frozen expected-hash CONSTANTS returned by
    ``_frozen_expected_exec_sha`` / ``_frozen_expected_manifest_sha``, so
    authorizing a mutated file remains impossible.  ``main()`` never passes them.
    """
    exec_p = Path(exec_path) if exec_path is not None else EXEC_V1_12
    man_p = Path(manifest_path) if manifest_path is not None else MANIFEST_V1_12

    result = {"authorized": False, "items": {}, "fail_closed": True}
    exp_exec = _frozen_expected_exec_sha()
    exp_man = _frozen_expected_manifest_sha()

    if not exec_p.exists():
        result["items"]["execution_source"] = {"present": False, "match": False}
        return result
    obs_exec = sha(exec_p)
    exec_match = (exp_exec not in ("", _EXEC_PLACEHOLDER) and obs_exec == exp_exec)
    result["items"]["execution_source"] = {"present": True, "expected": exp_exec,
                                           "observed": obs_exec, "match": bool(exec_match)}

    if not man_p.exists():
        result["items"]["runtime_manifest"] = {"present": False, "match": False}
        return result
    obs_man = sha(man_p)
    man_match = (exp_man not in ("", _MANIFEST_PLACEHOLDER) and obs_man == exp_man)
    result["items"]["runtime_manifest"] = {"present": True, "expected": exp_man,
                                           "observed": obs_man, "match": bool(man_match)}

    # The manifest must be parseable and declare the execution-source SHA that the
    # launcher independently verified above (two independent mechanisms agree).
    declared_exec = None
    try:
        man = json.loads(man_p.read_text(encoding="utf-8"))
        declared_exec = man.get("execution_source_sha256")
    except Exception as exc:
        result["items"]["manifest_parse"] = {"ok": False, "error": type(exc).__name__}
        return result
    result["items"]["manifest_parse"] = {"ok": True}
    manifest_declares_exec = bool(declared_exec and declared_exec == obs_exec)
    result["items"]["manifest_declares_exec_sha"] = {
        "declared": declared_exec, "observed_exec": obs_exec,
        "match": bool(manifest_declares_exec)}

    # D34 no-cycle invariant: the manifest MUST NOT declare a launcher SHA.
    launcher_key_present = "launcher_sha256" in man
    result["items"]["manifest_launcher_sha256_absent"] = {
        "absent": (not launcher_key_present),
        "present_fail_closed": bool(launcher_key_present)}

    result["authorized"] = bool(exec_match and man_match
                                and manifest_declares_exec
                                and not launcher_key_present)
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
            "launcher": "launch_phase36_v1_12",
            "mode": a.mode,
            "authorized": False,
            "terminal": "PHASE36_V1_12_LAUNCH_NOT_AUTHORIZED__ANCHOR_VERIFICATION_FAILED",
            "authority": auth,
        }, indent=1))
        return 2

    if a.verify_only:
        print(json.dumps({
            "launcher": "launch_phase36_v1_12",
            "authorized": True,
            "terminal": "PHASE36_V1_12_LAUNCH_ANCHOR_VERIFIED__DISPATCH_SUPPRESSED_BY_VERIFY_ONLY",
            "authority": auth,
        }, indent=1))
        return 0

    # Dispatch: set the launch-authority token so the source accepts the dispatch,
    # then run the module's main() in-process with argv set to the dispatched mode.
    os.environ[LAUNCH_AUTHORITY_TOKEN] = "1"
    import importlib.util
    spec = importlib.util.spec_from_file_location("phase36_v1_12_exec", EXEC_V1_12)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _saved_argv = sys.argv
    try:
        sys.argv = [str(EXEC_V1_12), "--mode", a.mode]
        return int(mod.main())
    finally:
        sys.argv = _saved_argv


if __name__ == "__main__":
    raise SystemExit(main())
