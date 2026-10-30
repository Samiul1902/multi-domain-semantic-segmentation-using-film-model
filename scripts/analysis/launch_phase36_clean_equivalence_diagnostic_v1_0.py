#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 36 — CLEAN EQUIVALENCE DIAGNOSTIC v1.0 LAUNCHER.

PREPARED under Work Order H.  Mirrors the frozen v1.14 launcher's ORDER and
FAIL-CLOSED discipline, but pins the DIAGNOSTIC source and its own frozen v1.14
anchors.  It NEVER dispatches the v1.14 science path and NEVER touches v1.14
science markers.

D-order (pre-dispatch, fail closed):
    (1) parse args
    (2) immutable anchors: diagnostic source SHA + frozen v1.14 exec/manifest SHAs
    (3) exact project interpreter identity (D37 semantics)
    (4) CUDA readiness (D38 semantics; device-only)
    (5) --verify-only STOP (no dispatch)
    (6) set diagnostic launch-authority token ONLY now
    (7) dispatch the diagnostic module ONLY

There is NO auto-relaunch.  Interpreter/anchors can be overridden ONLY through
the negative-control test hooks (``--selftest-*``), which can never weaken
production ``main()`.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DIAGNOSTIC_SELF = ROOT / "scripts" / "analysis" / "phase36_clean_equivalence_diagnostic_v1_0.py"
FROZEN_V1_14 = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_14.py"
MANIFEST_V1_14 = ROOT / "reports" / "audits" / "phase36_v1_14_runtime_source_integrity_manifest.json"

CANONICAL_INTERPRETER = ROOT / ".venv" / "Scripts" / "python.exe"

LAUNCH_AUTHORITY_TOKEN = "PHASE36_CLEAN_EQ_DIAGNOSTIC_LAUNCH_AUTHORITY"
ONE_SHOT_ENV = "PHASE36_CLEAN_EQ_DIAGNOSTIC_EXECUTE"

# ---- FROZEN anchors (LITERAL, IMMUTABLE, NON-ENV-OVERRIDABLE) ------------- #
# The diagnostic source SHA is filled by build_phase36_clean_equivalence_diagnostic.py
# AFTER the source is frozen.  Until then it is a fail-closed placeholder.
FROZEN_EXPECTED_DIAGNOSTIC_SHA = "7cc51cceacfa314d7f84acb8a6dc482a2b46ea81de0ec695c0c8f0ca8b0b50f7"
FROZEN_EXPECTED_V1_14_EXEC_SHA = "ac09ff8ded3610244920e66612145b246b33127140d344a9730d454bab27cff5"
FROZEN_EXPECTED_V1_14_MANIFEST_SHA = "b4c358dfcb5e7b59beb6ae1ba2cffc64677d10049e12568b4c8eea8e79bb911e"

_PLACEHOLDER = "__FROZEN_DIAG_SHA__"

T_ANCHOR_FAILED = "PHASE36_CLEAN_EQ_DIAGNOSTIC_LAUNCH_FAIL_CLOSED__ANCHOR_VERIFICATION_FAILED__NO_ATTEMPT_CONSUMED"
T_WRONG_INTERPRETER = "PHASE36_CLEAN_EQ_DIAGNOSTIC_LAUNCH_FAIL_CLOSED__WRONG_INTERPRETER__NO_ATTEMPT_CONSUMED"
T_CUDA_UNAVAILABLE = "PHASE36_CLEAN_EQ_DIAGNOSTIC_LAUNCH_FAIL_CLOSED__CUDA_READINESS_FAILED__NO_ATTEMPT_CONSUMED"
T_VERIFY_ONLY_OK = "PHASE36_CLEAN_EQ_DIAGNOSTIC_LAUNCH_READINESS_VERIFIED__DISPATCH_SUPPRESSED_BY_VERIFY_ONLY"


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _norm(path) -> str:
    return os.path.normcase(os.path.realpath(str(path)))


def _frozen_diag_sha() -> str:
    return FROZEN_EXPECTED_DIAGNOSTIC_SHA


def _frozen_v14_sha() -> str:
    return FROZEN_EXPECTED_V1_14_EXEC_SHA


def _frozen_v14_manifest_sha() -> str:
    return FROZEN_EXPECTED_V1_14_MANIFEST_SHA


def verify_authority(diag_path: Path | None = None,
                     v14_path: Path | None = None,
                     manifest_path: Path | None = None) -> dict:
    """Verify diagnostic SHA + frozen v1.14 exec/manifest SHAs.  No model IO."""
    diag_p = Path(diag_path) if diag_path is not None else DIAGNOSTIC_SELF
    v14_p = Path(v14_path) if v14_path is not None else FROZEN_V1_14
    man_p = Path(manifest_path) if manifest_path is not None else MANIFEST_V1_14

    result = {"authorized": False, "items": {}, "fail_closed": True}
    exp_diag = _frozen_diag_sha()
    exp_v14 = _frozen_v14_sha()
    exp_man = _frozen_v14_manifest_sha()

    if not diag_p.exists():
        result["items"]["diagnostic_source"] = {"present": False, "match": False}
        return result
    obs_diag = sha(diag_p)
    result["items"]["diagnostic_source"] = {
        "present": True, "expected": exp_diag, "observed": obs_diag,
        "match": bool(exp_diag not in ("", _PLACEHOLDER) and obs_diag == exp_diag)}

    if not v14_p.exists():
        result["items"]["frozen_v1_14_source"] = {"present": False, "match": False}
        return result
    obs_v14 = sha(v14_p)
    result["items"]["frozen_v1_14_source"] = {
        "present": True, "expected": exp_v14, "observed": obs_v14,
        "match": bool(obs_v14 == exp_v14)}

    if not man_p.exists():
        result["items"]["runtime_manifest"] = {"present": False, "match": False}
        return result
    obs_man = sha(man_p)
    result["items"]["runtime_manifest"] = {
        "present": True, "expected": exp_man, "observed": obs_man,
        "match": bool(obs_man == exp_man)}

    declared = None
    try:
        man = json.loads(man_p.read_text(encoding="utf-8"))
        declared = man.get("execution_source_sha256")
        launcher_key = "launcher_sha256" in man
    except Exception as exc:  # noqa: BLE001
        result["items"]["manifest_parse"] = {"ok": False, "error": type(exc).__name__}
        return result
    result["items"]["manifest_parse"] = {"ok": True}
    result["items"]["manifest_declares_exec_sha"] = {
        "declared": declared, "observed_v14": obs_v14,
        "match": bool(declared and declared == obs_v14)}
    result["items"]["manifest_launcher_sha256_absent"] = {"absent": not launcher_key}

    result["authorized"] = bool(
        result["items"]["diagnostic_source"]["match"]
        and result["items"]["frozen_v1_14_source"]["match"]
        and result["items"]["runtime_manifest"]["match"]
        and result["items"]["manifest_declares_exec_sha"]["match"]
        and not launcher_key)
    result["fail_closed"] = not result["authorized"]
    return result


def check_interpreter_identity(expected_interpreter: Path | None = None,
                               observed_executable: str | None = None) -> dict:
    exp = Path(expected_interpreter) if expected_interpreter is not None else CANONICAL_INTERPRETER
    obs_raw = observed_executable if observed_executable is not None else sys.executable
    exp_norm, obs_norm = _norm(exp), _norm(obs_raw)
    return {
        "ok": bool(exp_norm == obs_norm),
        "expected_interpreter": str(exp),
        "observed_executable": str(obs_raw),
        "expected_interpreter_normalized": exp_norm,
        "observed_executable_normalized": obs_norm,
        "sys_prefix": str(getattr(sys, "prefix", "")),
        "note": "DIAGNOSTIC_EXACT_INTERPRETER_IDENTITY__NO_AUTO_RELAUNCH",
    }


def check_cuda_readiness() -> dict:
    """DEVICE-ONLY CUDA readiness probe (no model/checkpoint/data IO)."""
    out = {"ok": False, "torch_imported": False, "torch_version": None,
           "torch_cuda_version": None, "cuda_available": False,
           "device_count": 0, "resolved_device": None}
    try:
        import torch
        out["torch_imported"] = True
        out["torch_version"] = torch.__version__
        out["torch_cuda_version"] = getattr(torch.version, "cuda", None)
        out["cuda_available"] = bool(torch.cuda.is_available())
        out["device_count"] = int(torch.cuda.device_count()) if out["cuda_available"] else 0
    except Exception as exc:  # noqa: BLE001
        out["error"] = type(exc).__name__
        return out
    try:
        from src.utils.device import get_device
        dev = get_device(require_cuda=True)
        out["resolved_device"] = str(dev)
        out["ok"] = bool(out["cuda_available"] and out["device_count"] > 0
                         and str(getattr(dev, "type", "")) == "cuda")
    except Exception as exc:  # noqa: BLE001
        out["resolver_error"] = f"{type(exc).__name__}: {exc}"
    return out


def _emit(terminal: str, **extra) -> int:
    payload = {"launcher": "launch_phase36_clean_equivalence_diagnostic_v1_0",
               "terminal": terminal}
    payload.update(extra)
    print(json.dumps(payload, indent=1))
    return 2


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify-only", action="store_true",
                    help="verify anchors + interpreter + CUDA readiness and exit "
                         "WITHOUT dispatching.")
    a = ap.parse_args()

    auth = verify_authority()
    if not auth["authorized"]:
        return _emit(T_ANCHOR_FAILED, authorized=False, authority=auth)

    interp = check_interpreter_identity()
    if not interp["ok"]:
        return _emit(T_WRONG_INTERPRETER, authorized=False, interpreter=interp,
                     authority=auth,
                     hint=r"Invoke the canonical interpreter explicitly, e.g. "
                          r"D:\Softfors\jup\.venv\Scripts\python.exe "
                          r"scripts\analysis\launch_phase36_clean_equivalence_diagnostic_v1_0.py "
                          r"--verify-only")

    cuda = check_cuda_readiness()
    if not cuda["ok"]:
        return _emit(T_CUDA_UNAVAILABLE, authorized=False, interpreter=interp,
                     cuda_readiness=cuda, authority=auth)

    if a.verify_only:
        print(json.dumps({
            "launcher": "launch_phase36_clean_equivalence_diagnostic_v1_0",
            "authorized": True,
            "anchor_pass": True,
            "interpreter_pass": True,
            "cuda_readiness_pass": True,
            "terminal": T_VERIFY_ONLY_OK,
            "interpreter": interp,
            "cuda_readiness": cuda,
            "one_shot_gate_set": os.environ.get(ONE_SHOT_ENV) == "1",
        }, indent=1))
        return 0

    # ---- set diagnostic launch-authority token ONLY now ------------------- #
    os.environ[LAUNCH_AUTHORITY_TOKEN] = "1"

    import importlib.util
    spec = importlib.util.spec_from_file_location("phase36_clean_eq_diagnostic", DIAGNOSTIC_SELF)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return int(mod.main())


if __name__ == "__main__":
    raise SystemExit(main())
