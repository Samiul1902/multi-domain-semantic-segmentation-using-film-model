#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 36 — CLEAN EQUIVALENCE DIAGNOSTIC v1.1 LAUNCHER.

ADDITIVE revision of the diagnostic v1.0 launcher (which is preserved
byte-for-byte).  Repairs D45 and D48 at the launcher layer and enforces the
frozen v1.14 pre-dispatch discipline.

D-order (pre-dispatch, fail closed):
    (1) parse args
    (2) immutable anchors: diagnostic source SHA + frozen v1.14 exec/manifest SHAs
    (3) exact project interpreter identity (D37 semantics)
    (4) CUDA readiness (D38 semantics; device-only)
    (5) prior-failure provenance binding (D45/D48 handoff contract)
    (6) D48 TRANSITIVE HASH-ONLY INTEGRITY (14 deps / 4 ckpts) — NO torch.load
    (7) --verify-only STOP (non-consuming)
    (8) set launch-authority token ONLY now (PHASE36_CLEAN_EQ_DIAGNOSTIC_V1_1_LAUNCH_AUTHORITY)
    (9) dispatch the diagnostic module ONLY

There is NO auto-relaunch.  Test hooks (``--selftest-*``) can never weaken
production ``main()``.
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

DIAGNOSTIC_SELF = ROOT / "scripts" / "analysis" / "phase36_clean_equivalence_diagnostic_v1_1.py"
FROZEN_V1_14 = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_14.py"
MANIFEST_V1_14 = ROOT / "reports" / "audits" / "phase36_v1_14_runtime_source_integrity_manifest.json"

CANONICAL_INTERPRETER = ROOT / ".venv" / "Scripts" / "python.exe"

LAUNCH_AUTHORITY_TOKEN = "PHASE36_CLEAN_EQ_DIAGNOSTIC_V1_1_LAUNCH_AUTHORITY"
ONE_SHOT_ENV = "PHASE36_CLEAN_EQ_DIAGNOSTIC_EXECUTE"

# ---- FROZEN anchors (LITERAL, IMMUTABLE, NON-ENV-OVERRIDABLE) ------------- #
FROZEN_EXPECTED_DIAGNOSTIC_SHA = "04fa6252ff2533464553fb1a6c1f55ae009ee7ff00c1dbf89c1f901b089c839e"
FROZEN_EXPECTED_V1_14_EXEC_SHA = "ac09ff8ded3610244920e66612145b246b33127140d344a9730d454bab27cff5"
FROZEN_EXPECTED_V1_14_MANIFEST_SHA = "b4c358dfcb5e7b59beb6ae1ba2cffc64677d10049e12568b4c8eea8e79bb911e"

# D48: expected transitive counts (must match the frozen manifest exactly).
EXPECTED_N_DEPENDENCIES = 14
EXPECTED_N_CHECKPOINTS = 4

_PLACEHOLDER = "__FROZEN_DIAG_SHA__"

# Prior-failure provenance pins (machine-bound release — D45/D48 handoff contract).
PRIOR_FAILURE_PROVENANCE = {
    "v1_14_science_start": ("reports/audits/phase36_robustness_science_start_v1_14.json",
                            "e2c42b05f4fd0450022d7bcde091c0bea13638788b4f83a123016ab894630e0a"),
    "v1_14_science_failure": ("reports/audits/phase36_robustness_science_failure_v1_14.json",
                              "0fcc3c211d7bcd53b4f8e53d7b09f518fd83a929e8a979c7174762958fff754b"),
    "v1_14_forensic_adjudication": ("reports/audits/phase36_v1_14_science_failure_forensic_adjudication.json",
                                    "f1d4712ae7b3f0b333a22c852f99d6b3812218ffb258f8f58ddba62c7193c17e"),
    "forensic_reconciliation_v2": ("reports/audits/phase36_v1_14_science_failure_forensic_reconciliation_v2.json",
                                   "cc9a3b502f59e3855c395b9d6afa2f5616f513d60af4756e4477a9370889cc3c"),
    "targeted_static_audit": ("reports/audits/phase36_clean_equivalence_targeted_static_audit_v1_0.json",
                              "8def086c44a7e80461c729f41ab61c0be347ef1589c94d6884a082adbde64ed4"),
}
REQUIRED_STATIC_AUDIT_VERDICT = "STATIC_ROOT_CAUSE_NOT_ESTABLISHED"

T_ANCHOR_FAILED = "PHASE36_CLEAN_EQ_DIAGNOSTIC_V1_1_LAUNCH_FAIL_CLOSED__ANCHOR_VERIFICATION_FAILED__NO_ATTEMPT_CONSUMED"
T_WRONG_INTERPRETER = "PHASE36_CLEAN_EQ_DIAGNOSTIC_V1_1_LAUNCH_FAIL_CLOSED__WRONG_INTERPRETER__NO_ATTEMPT_CONSUMED"
T_CUDA_UNAVAILABLE = "PHASE36_CLEAN_EQ_DIAGNOSTIC_V1_1_LAUNCH_FAIL_CLOSED__CUDA_READINESS_FAILED__NO_ATTEMPT_CONSUMED"
T_PROVENANCE_FAILED = "PHASE36_CLEAN_EQ_DIAGNOSTIC_V1_1_LAUNCH_FAIL_CLOSED__PRIOR_FAILURE_PROVENANCE_NOT_BOUND__NO_ATTEMPT_CONSUMED"
T_TRANSITIVE_FAILED = "PHASE36_CLEAN_EQ_DIAGNOSTIC_V1_1_FAIL_CLOSED__TRANSITIVE_INTEGRITY_FAILED__NO_ATTEMPT_CONSUMED"
T_VERIFY_ONLY_OK = "PHASE36_CLEAN_EQ_DIAGNOSTIC_V1_1_LAUNCH_READINESS_VERIFIED__DISPATCH_SUPPRESSED_BY_VERIFY_ONLY"


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _norm(path) -> str:
    return os.path.normcase(os.path.realpath(str(path)))


def _frozen_diag_sha() -> str:
    return FROZEN_EXPECTED_DIAGNOSTIC_SHA


def verify_authority(diag_path: Path | None = None,
                     v14_path: Path | None = None,
                     manifest_path: Path | None = None) -> dict:
    """Verify diagnostic SHA + frozen v1.14 exec/manifest SHAs.  No model IO."""
    diag_p = Path(diag_path) if diag_path is not None else DIAGNOSTIC_SELF
    v14_p = Path(v14_path) if v14_path is not None else FROZEN_V1_14
    man_p = Path(manifest_path) if manifest_path is not None else MANIFEST_V1_14

    result = {"authorized": False, "items": {}, "fail_closed": True}
    exp_diag = _frozen_diag_sha()
    exp_v14 = FROZEN_EXPECTED_V1_14_EXEC_SHA
    exp_man = FROZEN_EXPECTED_V1_14_MANIFEST_SHA

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
           "device_count": 0, "resolved_device": None,
           "torch_load": False, "checkpoint_read": False, "model_forward": False,
           "val_image_read": False, "gt_read": False, "training": False}
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


def check_prior_failure_provenance() -> dict:
    """D45/D48 — bind the exact consumed failure that justified this diagnostic."""
    out = {"ok": True, "items": {}, "static_audit_verdict": None}
    for name, (rel, exp) in PRIOR_FAILURE_PROVENANCE.items():
        p = ROOT / rel
        ok = p.exists() and sha(p) == exp
        out["items"][name] = {"path": rel, "present": p.exists(), "expected": exp,
                              "observed": (sha(p) if p.exists() else None), "match": bool(ok)}
        if not ok:
            out["ok"] = False
    audit_p = ROOT / PRIOR_FAILURE_PROVENANCE["targeted_static_audit"][0]
    if audit_p.exists():
        try:
            out["static_audit_verdict"] = json.loads(
                audit_p.read_text(encoding="utf-8")).get("root_cause_static_verdict")
        except Exception as exc:  # noqa: BLE001
            out["static_audit_verdict"] = f"UNPARSEABLE::{type(exc).__name__}"
    if out["static_audit_verdict"] != REQUIRED_STATIC_AUDIT_VERDICT:
        out["ok"] = False
    return out


def check_transitive_integrity(manifest_path: Path | None = None,
                               root: Path | None = None) -> dict:
    """D48 — HASH-ONLY transitive integrity (NO torch.load, NO model, NO VAL/GT).

    Verifies: manifest SHA, execution_source_sha256, exactly 14 dependencies,
    exactly 4 checkpoints, every actual dependency SHA, every actual checkpoint
    SHA, and launcher_sha256 absence.
    """
    man_p = Path(manifest_path) if manifest_path is not None else MANIFEST_V1_14
    base = Path(root) if root is not None else ROOT
    out = {"ok": False, "manifest_sha": None, "manifest_sha_expected": FROZEN_EXPECTED_V1_14_MANIFEST_SHA,
           "execution_source_declared": None, "execution_source_expected": FROZEN_EXPECTED_V1_14_EXEC_SHA,
           "n_dependencies": None, "n_checkpoints": None,
           "n_dependencies_expected": EXPECTED_N_DEPENDENCIES,
           "n_checkpoints_expected": EXPECTED_N_CHECKPOINTS,
           "dependencies": {}, "checkpoints": {}, "launcher_sha256_absent": None,
           "torch_load": False, "checkpoint_deserialization": False,
           "model_construction": False, "val_or_gt_read": False}
    if not man_p.exists():
        out["reason"] = "MANIFEST_MISSING"
        return out
    out["manifest_sha"] = sha(man_p)
    if out["manifest_sha"] != FROZEN_EXPECTED_V1_14_MANIFEST_SHA:
        out["reason"] = "MANIFEST_SHA_MISMATCH"
        return out
    try:
        man = json.loads(man_p.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        out["reason"] = f"MANIFEST_MALFORMED::{type(exc).__name__}"
        return out

    out["launcher_sha256_absent"] = ("launcher_sha256" not in man)
    out["execution_source_declared"] = man.get("execution_source_sha256")
    deps = man.get("dependencies", {})
    ckpts = man.get("checkpoints", {})
    out["n_dependencies"] = len(deps)
    out["n_checkpoints"] = len(ckpts)

    all_ok = True
    all_ok = all_ok and out["launcher_sha256_absent"]
    all_ok = all_ok and (out["execution_source_declared"] == FROZEN_EXPECTED_V1_14_EXEC_SHA)
    all_ok = all_ok and (out["n_dependencies"] == EXPECTED_N_DEPENDENCIES)
    all_ok = all_ok and (out["n_checkpoints"] == EXPECTED_N_CHECKPOINTS)

    for rel, exp in deps.items():
        p = base / rel
        obs = sha(p) if p.exists() else None
        m = (obs == exp)
        out["dependencies"][rel] = {"expected": exp, "observed": obs, "present": p.exists(), "match": bool(m)}
        all_ok = all_ok and m
    for rel, exp in ckpts.items():
        p = base / rel
        obs = sha(p) if p.exists() else None
        m = (obs == exp)
        out["checkpoints"][rel] = {"expected": exp, "observed": obs, "present": p.exists(), "match": bool(m)}
        all_ok = all_ok and m

    out["ok"] = bool(all_ok)
    if not out["ok"]:
        out["reason"] = "TRANSITIVE_BYTE_MISMATCH"
    return out


def _emit(terminal: str, **extra) -> int:
    payload = {"launcher": "launch_phase36_clean_equivalence_diagnostic_v1_1",
               "terminal": terminal}
    payload.update(extra)
    print(json.dumps(payload, indent=1))
    return 2


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify-only", action="store_true",
                    help="verify anchors + interpreter + CUDA + provenance + transitive "
                         "integrity and exit WITHOUT dispatching.")
    a = ap.parse_args()

    # (2) immutable anchor
    auth = verify_authority()
    if not auth["authorized"]:
        return _emit(T_ANCHOR_FAILED, authorized=False, authority=auth)

    # (3) exact project interpreter
    interp = check_interpreter_identity()
    if not interp["ok"]:
        return _emit(T_WRONG_INTERPRETER, authorized=False, interpreter=interp,
                     authority=auth,
                     hint=r"Invoke the canonical interpreter explicitly, e.g. "
                          r"D:\Softfors\jup\.venv\Scripts\python.exe "
                          r"scripts\analysis\launch_phase36_clean_equivalence_diagnostic_v1_1.py --verify-only")

    # (4) CUDA readiness
    cuda = check_cuda_readiness()
    if not cuda["ok"]:
        return _emit(T_CUDA_UNAVAILABLE, authorized=False, interpreter=interp,
                     cuda_readiness=cuda, authority=auth)

    # (5) prior-failure provenance binding
    prov = check_prior_failure_provenance()
    if not prov["ok"]:
        return _emit(T_PROVENANCE_FAILED, authorized=False, provenance=prov,
                     interpreter=interp, cuda_readiness=cuda, authority=auth)

    # (6) D48 transitive hash-only integrity (BEFORE launch authority)
    ti = check_transitive_integrity()
    if not ti["ok"]:
        return _emit(T_TRANSITIVE_FAILED, authorized=False, transitive_integrity=ti,
                     provenance=prov, interpreter=interp, cuda_readiness=cuda,
                     authority=auth)

    # (7) verify-only STOP (non-consuming)
    if a.verify_only:
        print(json.dumps({
            "launcher": "launch_phase36_clean_equivalence_diagnostic_v1_1",
            "authorized": True,
            "anchor_pass": True,
            "interpreter_pass": True,
            "cuda_readiness_pass": True,
            "prior_failure_provenance_pass": True,
            "transitive_integrity_pass": True,
            "n_dependencies_verified": ti["n_dependencies"],
            "n_checkpoints_verified": ti["n_checkpoints"],
            "terminal": T_VERIFY_ONLY_OK,
            "interpreter": interp,
            "cuda_readiness": cuda,
            "one_shot_gate_set": os.environ.get(ONE_SHOT_ENV) == "1",
        }, indent=1))
        return 0

    # (8) set launch-authority token ONLY now
    os.environ[LAUNCH_AUTHORITY_TOKEN] = "1"

    # (9) dispatch the diagnostic module ONLY
    import importlib.util
    spec = importlib.util.spec_from_file_location("phase36_clean_eq_diagnostic_v1_1",
                                                  DIAGNOSTIC_SELF)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return int(mod.main())


if __name__ == "__main__":
    raise SystemExit(main())
