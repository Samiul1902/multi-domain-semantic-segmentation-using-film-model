#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.14 — IMMUTABLE NON-CIRCULAR PRE-INVOCATION LAUNCHER with EXACT
INTERPRETER IDENTITY (D37) + CUDA READINESS PRE-DISPATCH (D38) + PROVEN
PRE-CONSUMPTION ORDER (D39).

ADDITIVE over the v1.12 launcher (history preserved byte-for-byte).  This is the
REAL external authority that (a) defeats a source+manifest co-edit and (b) makes
an ENVIRONMENT-SELECTION failure impossible to consume an attempt.

It is MODEL-FREE and PROTECTED-DATA-FREE.  It reads only the frozen
execution-source bytes and the frozen runtime-manifest bytes to verify their
SHA-256 against EXACT frozen constants, verifies that THIS PROCESS runs under
the canonical project interpreter, and performs a DEVICE-ONLY CUDA readiness
probe.  Only after ALL of those pass does it set the launch authority token and
dispatch the requested mode.

=========================================================================== #
v1.12 -> v1.14 — WHY THIS REVISION EXISTS                                 #
=========================================================================== #
The v1.12 FIRST SMOKE ATTEMPT was CONSUMED and FAILED pre-model with
``CudaUnavailableError``.  Adjudicated root cause:

    PRE_MODEL_EXECUTION_ENVIRONMENT_SELECTION_FAILURE
    (NOT_A_SCIENTIFIC_FAILURE)

The launcher had been invoked with BARE SYSTEM PYTHON
(``C:\\Users\\user\\AppData\\Local\\Programs\\Python\\Python311\\python.exe``),
which resolves ``torch == 2.10.0+cpu`` (``torch.version.cuda is None``,
``torch.cuda.is_available() is False``).  The healthy project interpreter is
``D:\\Softfors\\jup\\.venv\\Scripts\\python.exe`` (``torch == 2.6.0+cu124``,
CUDA available, RTX 3060 Ti).  The v1.12 launcher had NO interpreter gate and
NO readiness gate, so the environment defect propagated all the way into
``run_smoke`` and consumed the (unauthorized-to-consume) revision.

v1.14 CLOSES THAT HOLE AT THE LAUNCHER LAYER — the scientific execution source
is UNCHANGED in behaviour (new_scientific_choice = false):

  D37 EXACT PROJECT INTERPRETER PRE-DISPATCH GATE
      The launcher computes the canonical interpreter path from ROOT
      (``ROOT / ".venv" / "Scripts" / "python.exe"``), normalizes/resolves it
      (``os.path.realpath`` + ``normcase``) and compares it against
      ``os.path.realpath(sys.executable)``.  A mismatch FAILS CLOSED with
      terminal
      ``PHASE36_V1_14_LAUNCH_FAIL_CLOSED__WRONG_INTERPRETER__NO_ATTEMPT_CONSUMED``.
      The check runs BEFORE the token is set, BEFORE the execution module is
      imported/dispatched, BEFORE ``main()`` is entered, BEFORE any start marker
      can be created, BEFORE model construction, BEFORE checkpoint
      deserialization, BEFORE VAL access.  It NEVER consumes the v1.14 revision.
      The launcher NEVER re-executes itself under another interpreter: the HUMAN
      must invoke the correct interpreter explicitly.

  D38 CUDA READINESS PRE-DISPATCH GATE (DEVICE-ONLY)
      After interpreter identity passes, but still BEFORE dispatch and before
      any attempt marker, the launcher performs a device-only readiness probe:
      ``import torch``; ``torch.__version__``; ``torch.version.cuda``;
      ``torch.cuda.is_available()``; ``torch.cuda.device_count()``;
      ``torch.cuda.current_device()`` / ``get_device_name(0)`` (only when
      available); and ``src.utils.device.get_device(require_cuda=True)``.
      It REQUIREs: ``torch.version.cuda is not None``; ``is_available() is
      True``; ``device_count() >= 1``; ``get_device`` succeeds; resolved device
      type == "cuda".  A failure FAILS CLOSED with terminal
      ``PHASE36_V1_14_LAUNCH_FAIL_CLOSED__CUDA_READINESS_FAILED__NO_ATTEMPT_CONSUMED``.
      NO ``torch.load`` / checkpoint / model construction / forward / VAL read /
      GT read / TEST / ROUTER_HOLDOUT / training occurs in the probe.  NO silent
      CPU fallback.

  D39 PRE-CONSUMPTION ORDER PROOF
      The launcher order is exactly:
        1. parse mode
        2. verify immutable execution-source + manifest SHA anchor
        3. verify exact project interpreter
        4. verify CUDA readiness
        5. if --verify-only: STOP successfully WITHOUT dispatch
        6. only after all above pass: set PHASE36_V1_14_LAUNCH_AUTHORITY=1
        7. dispatch exact frozen v1.14 execution source
        8. execution source performs its existing mode-authorization gate
        9. only then may its exclusive start marker be created
      Therefore WRONG_INTERPRETER / CUDA_UNAVAILABLE / SOURCE_MANIFEST_HASH_
      FAILURE can NEVER consume the v1.14 attempt.  The order is PROVEN by the
      v1.14 negative controls (NC100..NC114).

=========================================================================== #
DEFECTS CARRIED FORWARD FROM V1.12 (still enforced)                       #
=========================================================================== #
  D34 the launcher verifies the exact execution-source + manifest SHAs and
      NEVER asks the manifest to declare its own SHA (no cycle).
  D35 the FROZEN expected SHAs are LITERAL constants; there is NO environment,
      CLI, config, or attribute mechanism capable of replacing them.  The old
      override env names (``PHASE36_V1_12_*EXPECTED*`` and any
      ``PHASE36_V1_14_*EXPECTED*`` variant) are read by NOTHING here and are
      therefore INERT.
  D36 the launch-anchor contract is validated across ALL THREE files (source,
      launcher, manifest) and proven MUTUALLY SATISFIABLE.

=========================================================================== #
NON-CIRCULAR RELEASE CHAIN (v1.14)                                        #
=========================================================================== #
    supervisor (external)  --pins-->  launcher SHA (this file)
    supervisor (external)  --pins-->  source-freeze SHA
    launcher  --verifies exact SHA of-->  v1.14 execution source (literal const)
    launcher  --verifies exact SHA of-->  v1.14 runtime manifest  (literal const)
    manifest  --declares-->  execution_source_sha256  (source self-check)
    execution source  --requires-->  launch-authority TOKEN (NOT a manifest hash)

The chain is a DAG, not a cycle.  A source+manifest co-edit cannot pass because
the launcher's literal frozen expected SHAs are unchanged.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# The canonical device resolver lives in ``src.utils.device`` and MUST be
# importable regardless of how this launcher is invoked (script path, absolute
# path, from another cwd).  Put the project ROOT on sys.path ONCE, here.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

EXEC_V1_14 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_14.py"
MANIFEST_V1_14 = ROOT / "reports/audits/phase36_v1_14_runtime_source_integrity_manifest.json"
LAUNCHER_SELF = ROOT / "scripts/analysis/launch_phase36_v1_14.py"

# ---- D37: the canonical project interpreter (derived from ROOT) ------------ #
CANONICAL_INTERPRETER = ROOT / ".venv" / "Scripts" / "python.exe"

GATE_ENV = "PHASE36_EXECUTE"
SMOKE_GATE_ENV = "PHASE36_SMOKE_EXECUTE"
LAUNCH_AUTHORITY_TOKEN = "PHASE36_V1_14_LAUNCH_AUTHORITY"

# --------------------------------------------------------------------------- #
# FROZEN expected SHAs — LITERAL, IMMUTABLE, NON-ENV-OVERRIDABLE (D35).
# Written by build_phase36_v1_14_freeze_and_eligibility.py and pinned EXTERNALLY
# by the supervisor.  These are the SOLE authorization authority: no env var,
# CLI flag, config file, or attribute assignment can substitute for them.
# --------------------------------------------------------------------------- #
FROZEN_EXPECTED_EXEC_SHA = "ac09ff8ded3610244920e66612145b246b33127140d344a9730d454bab27cff5"
FROZEN_EXPECTED_MANIFEST_SHA = "b4c358dfcb5e7b59beb6ae1ba2cffc64677d10049e12568b4c8eea8e79bb911e"

# Placeholder sentinels that can never be a real SHA (frozen-source fail-closed).
_EXEC_PLACEHOLDER = "__FROZEN_EXEC_SHA__"
_MANIFEST_PLACEHOLDER = "__FROZEN_MANIFEST_SHA__"

# --------------------------------------------------------------------------- #
# D37 terminal verbs
# --------------------------------------------------------------------------- #
T_WRONG_INTERPRETER = "PHASE36_V1_14_LAUNCH_FAIL_CLOSED__WRONG_INTERPRETER__NO_ATTEMPT_CONSUMED"
T_CUDA_UNAVAILABLE = "PHASE36_V1_14_LAUNCH_FAIL_CLOSED__CUDA_READINESS_FAILED__NO_ATTEMPT_CONSUMED"
T_ANCHOR_FAILED = "PHASE36_V1_14_LAUNCH_FAIL_CLOSED__ANCHOR_VERIFICATION_FAILED__NO_ATTEMPT_CONSUMED"
T_VERIFY_ONLY_OK = "PHASE36_V1_14_LAUNCH_READINESS_VERIFIED__DISPATCH_SUPPRESSED_BY_VERIFY_ONLY"
T_SCIENCE_NOT_RELEASED = ("PHASE36_V1_14_SCIENCE_NOT_RELEASED"
                          "__SUCCESSFUL_SMOKE_REQUIRED__NO_ATTEMPT_CONSUMED")

# --------------------------------------------------------------------------- #
# D40 — science release attestation contract (MUST match the execution source).
# --------------------------------------------------------------------------- #
SCIENCE_RELEASE_ATTESTATION = "reports/audits/phase36_v1_14_science_release_attestation.json"
SMOKE_V1_14_ARTIFACT = "reports/audits/phase36_robustness_smoke_v1_14.json"
_SCIENCE_RELEASE_REVISION = "ra_medfilm_barr_phase36_robustness_v1_14"


def _science_release_evidence() -> dict:
    """D40: DEVICE-DATA-FREE science release check (mirrors the execution gate).

    Returns {"state": "RELEASED"|"NOT_RELEASED", ...}.  Reads ONLY the release
    attestation and hashes the smoke artifact's bytes.  NO model/checkpoint/VAL
    access; NO marker; NO torch.
    """
    ev: dict = {"attestation": SCIENCE_RELEASE_ATTESTATION}
    att_path = ROOT / SCIENCE_RELEASE_ATTESTATION
    if not att_path.exists():
        ev["reason"] = "NO_ATTESTATION"
        return {"state": "NOT_RELEASED", **ev}
    try:
        att = json.loads(att_path.read_text(encoding="utf-8"))
    except Exception as exc:
        ev["reason"] = "ATTESTATION_MALFORMED"
        ev["error"] = type(exc).__name__
        return {"state": "NOT_RELEASED", **ev}
    if att.get("revision") != _SCIENCE_RELEASE_REVISION:
        ev["reason"] = "REVISION_MISMATCH"
        return {"state": "NOT_RELEASED", **ev}
    source_sha = sha(EXEC_V1_14)
    if att.get("execution_source_sha256") != source_sha:
        ev["reason"] = "SOURCE_SHA_MISMATCH"
        ev["observed_source_sha256"] = source_sha
        return {"state": "NOT_RELEASED", **ev}
    smoke_path = ROOT / SMOKE_V1_14_ARTIFACT
    if not smoke_path.exists():
        ev["reason"] = "SMOKE_ARTIFACT_MISSING"
        return {"state": "NOT_RELEASED", **ev}
    smoke_sha = sha(smoke_path)
    if att.get("smoke_artifact_sha256") != smoke_sha:
        ev["reason"] = "SMOKE_ARTIFACT_SHA_MISMATCH"
        ev["observed_smoke_artifact_sha256"] = smoke_sha
        return {"state": "NOT_RELEASED", **ev}
    if att.get("smoke_all_pass") is not True:
        ev["reason"] = "SMOKE_NOT_SUCCESSFUL"
        return {"state": "NOT_RELEASED", **ev}
    if att.get("scientific_output") is not False:
        ev["reason"] = "SCIENTIFIC_OUTPUT_NOT_FALSE"
        return {"state": "NOT_RELEASED", **ev}
    if att.get("release_gate") != "POST_SMOKE_RELEASE_ADJUDICATION":
        ev["reason"] = "RELEASE_GATE_MISMATCH"
        return {"state": "NOT_RELEASED", **ev}
    ev["reason"] = "SUCCESSFUL_SMOKE_BOUND"
    return {"state": "RELEASED", **ev}


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _norm(path) -> str:
    """Normalize a filesystem path for identity comparison.

    Uses ``os.path.realpath`` (resolves symlinks / ``..`` / short names) then
    ``os.path.normcase`` (case-folds on Windows) so that
    ``D:\\Softfors\\jup\\.venv\\Scripts\\python.exe`` and its short-name /
    different-case spellings compare EQUAL, while a genuinely different
    interpreter (bare system Python) compares UNEQUAL.
    """
    return os.path.normcase(os.path.realpath(str(path)))


def _frozen_expected_exec_sha() -> str:
    """Return the IMMUTABLE frozen expected execution-source SHA.

    D35: this function reads NO environment variable, NO CLI argument, and NO
    config.  It returns the literal module constant unconditionally.
    """
    return FROZEN_EXPECTED_EXEC_SHA


def _frozen_expected_manifest_sha() -> str:
    """Return the IMMUTABLE frozen expected runtime-manifest SHA (D35)."""
    return FROZEN_EXPECTED_MANIFEST_SHA


# --------------------------------------------------------------------------- #
# D37 — EXACT PROJECT INTERPRETER PRE-DISPATCH GATE
# --------------------------------------------------------------------------- #
def canonical_interpreter_path() -> Path:
    """Return the canonical project interpreter path derived from ROOT."""
    return CANONICAL_INTERPRETER


def check_interpreter_identity(
    expected_interpreter: Path | None = None,
    observed_executable: str | None = None,
) -> dict:
    """D37: prove ``sys.executable`` IS the canonical project interpreter.

    Returns a dict with ``ok`` (bool) and evidence.  Performs NO model /
    protected-data IO.  ``expected_interpreter`` / ``observed_executable``
    default to the canonical production values; they exist ONLY so the
    negative-control harness can exercise rejection logic with a simulated
    interpreter.  They can NEVER weaken production (``main()`` passes neither).
    """
    exp = Path(expected_interpreter) if expected_interpreter is not None else canonical_interpreter_path()
    obs_raw = observed_executable if observed_executable is not None else sys.executable

    exp_norm = _norm(exp)
    obs_norm = _norm(obs_raw)
    in_venv = bool(getattr(sys, "prefix", "") and
                   _norm(Path(sys.prefix)) == _norm(exp.parent.parent))
    return {
        "ok": bool(exp_norm == obs_norm),
        "expected_interpreter": str(exp),
        "expected_interpreter_normalized": exp_norm,
        "observed_executable": str(obs_raw),
        "observed_executable_normalized": obs_norm,
        "observed_exists": bool(Path(obs_raw).exists()),
        "sys_prefix": str(getattr(sys, "prefix", "")),
        "sys_prefix_is_project_venv": in_venv,
        "note": "D37_EXACT_INTERPRETER_IDENTITY__NO_AUTO_RELAUNCH",
    }


# --------------------------------------------------------------------------- #
# D38 — CUDA READINESS PRE-DISPATCH GATE (DEVICE-ONLY)
# --------------------------------------------------------------------------- #
def check_cuda_readiness() -> dict:
    """D38: DEVICE-ONLY CUDA readiness probe.  NO model/checkpoint/data IO.

    Returns a dict with ``ok`` (bool) and observed environment evidence.  The
    only device APIs touched are torch CUDA introspection and the canonical
    ``src.utils.device.get_device(require_cuda=True)`` resolver.
    """
    out = {
        "ok": False,
        "torch_imported": False,
        "torch_version": None,
        "torch_version_cuda": None,
        "cuda_is_available": None,
        "cuda_device_count": None,
        "current_device": None,
        "device_name_0": None,
        "get_device_require_cuda_success": False,
        "get_device_resolved": None,
        "get_device_resolved_type": None,
        "get_device_error": None,
        "conditions": {},
        "torch_load": False,
        "checkpoint_read": False,
        "model_construction": False,
        "model_forward": False,
        "val_image_read": False,
        "gt_read": False,
        "training": False,
        "note": "D38_DEVICE_ONLY_READINESS_PROBE",
    }
    try:
        import torch  # noqa: WPS433 (intentional: only for device introspection)
    except Exception as exc:  # pragma: no cover - environment dependent
        out["get_device_error"] = f"torch import failed: {type(exc).__name__}"
        return out

    out["torch_imported"] = True
    out["torch_version"] = getattr(torch, "__version__", None)
    out["torch_version_cuda"] = getattr(getattr(torch, "version", None), "cuda", None)
    try:
        out["cuda_is_available"] = bool(torch.cuda.is_available())
    except Exception as exc:
        out["cuda_is_available"] = False
        out["cuda_probe_error"] = f"{type(exc).__name__}"
    if out["cuda_is_available"]:
        try:
            out["cuda_device_count"] = int(torch.cuda.device_count())
        except Exception:
            out["cuda_device_count"] = 0
        if out["cuda_device_count"] and out["cuda_device_count"] >= 1:
            try:
                out["current_device"] = int(torch.cuda.current_device())
            except Exception:
                out["current_device"] = None
            try:
                out["device_name_0"] = str(torch.cuda.get_device_name(0))
            except Exception:
                out["device_name_0"] = None

    # Canonical device resolution (the SAME resolver the execution source uses).
    try:
        from src.utils.device import get_device  # noqa: WPS433
        dev = get_device(require_cuda=True)
        out["get_device_require_cuda_success"] = True
        out["get_device_resolved"] = str(dev)
        out["get_device_resolved_type"] = str(getattr(dev, "type", dev))
    except Exception as exc:
        out["get_device_require_cuda_success"] = False
        out["get_device_error"] = f"{type(exc).__name__}: {exc}"

    conds = {
        "torch_version_cuda_not_none": out["torch_version_cuda"] is not None,
        "cuda_is_available_true": out["cuda_is_available"] is True,
        "device_count_ge_1": bool(out["cuda_device_count"] and out["cuda_device_count"] >= 1),
        "get_device_require_cuda_ok": bool(out["get_device_require_cuda_success"]),
        "resolved_device_type_is_cuda": (out["get_device_resolved_type"] == "cuda"),
    }
    out["conditions"] = conds
    out["ok"] = all(conds.values())
    return out


# --------------------------------------------------------------------------- #
# D34/D35/D36 — anchor verification (carried, unchanged)
# --------------------------------------------------------------------------- #
def verify_authority(
    exec_path: Path | None = None,
    manifest_path: Path | None = None,
) -> dict:
    """Verify exact frozen SHAs of the execution source AND the runtime manifest.

    Performs NO model / protected-data IO.  ``exec_path`` / ``manifest_path``
    exist ONLY for the negative-control harness (mutated temp copies); they can
    NEVER change the frozen expected-hash CONSTANTS.  ``main()`` never passes them.
    """
    exec_p = Path(exec_path) if exec_path is not None else EXEC_V1_14
    man_p = Path(manifest_path) if manifest_path is not None else MANIFEST_V1_14

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


def _emit(terminal: str, **extra) -> int:
    payload = {"launcher": "launch_phase36_v1_14", "terminal": terminal}
    payload.update(extra)
    print(json.dumps(payload, indent=1))
    return 2


def main() -> int:
    # ---- D39 (1) parse mode ------------------------------------------------ #
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True, choices=("smoke", "science"))
    ap.add_argument("--verify-only", action="store_true",
                    help="verify anchor + interpreter + CUDA readiness and exit "
                         "WITHOUT dispatching.")
    a = ap.parse_args()

    # ---- D39 (2) immutable anchor ----------------------------------------- #
    auth = verify_authority()
    if not auth["authorized"]:
        return _emit(T_ANCHOR_FAILED, mode=a.mode, authorized=False, authority=auth)

    # ---- D39 (3) exact project interpreter -------------------------------- #
    interp = check_interpreter_identity()
    if not interp["ok"]:
        return _emit(T_WRONG_INTERPRETER, mode=a.mode, authorized=False,
                     interpreter=interp, authority=auth,
                     hint="Invoke the canonical interpreter explicitly, e.g. "
                          r"D:\Softfors\jup\.venv\Scripts\python.exe "
                          r"scripts\analysis\launch_phase36_v1_14.py --mode smoke")

    # ---- D39 (4) CUDA readiness ------------------------------------------- #
    cuda = check_cuda_readiness()
    if not cuda["ok"]:
        return _emit(T_CUDA_UNAVAILABLE, mode=a.mode, authorized=False,
                     interpreter=interp, cuda_readiness=cuda, authority=auth)

    # ---- D39 (5) verify-only STOP ----------------------------------------- #
    if a.verify_only:
        print(json.dumps({
            "launcher": "launch_phase36_v1_14",
            "mode": a.mode,
            "authorized": True,
            "anchor_pass": True,
            "interpreter_pass": True,
            "cuda_readiness_pass": True,
            "terminal": T_VERIFY_ONLY_OK,
            "interpreter": interp,
            "cuda_readiness": cuda,
        }, indent=1))
        return 0

    # ---- D40 (5.5) SCIENCE RELEASE GATE (pre-dispatch, fail closed) ------- #
    #   A successful v1.14 SMOKE is an EXECUTABLE PREREQUISITE for science.
    #   This runs AFTER interpreter identity + CUDA readiness but BEFORE the
    #   launch-authority token is set, BEFORE the execution source is imported,
    #   BEFORE any marker can be created, and BEFORE model/VAL access.  Verify-
    #   only science (handled above) therefore does NOT release science.
    if a.mode == "science":
        release = _science_release_evidence()
        if release["state"] != "RELEASED":
            return _emit(T_SCIENCE_NOT_RELEASED, mode=a.mode, authorized=False,
                         science_release_state=release["state"],
                         science_release_evidence=release,
                         interpreter=interp, cuda_readiness=cuda, authority=auth,
                         hint="Run a successful v1.14 smoke and the post-smoke "
                              "release adjudication first.")

    # ---- D39 (6) set the launch-authority token ONLY now ------------------ #
    os.environ[LAUNCH_AUTHORITY_TOKEN] = "1"

    # ---- D39 (7) dispatch the exact frozen v1.14 execution source --------- #
    import importlib.util
    spec = importlib.util.spec_from_file_location("phase36_v1_14_exec", EXEC_V1_14)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _saved_argv = sys.argv
    try:
        sys.argv = [str(EXEC_V1_14), "--mode", a.mode]
        return int(mod.main())
    finally:
        sys.argv = _saved_argv


if __name__ == "__main__":
    raise SystemExit(main())
