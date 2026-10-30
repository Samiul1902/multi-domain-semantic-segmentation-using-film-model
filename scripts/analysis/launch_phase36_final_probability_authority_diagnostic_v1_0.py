#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 36 — FINAL-PROBABILITY AUTHORITY DIAGNOSTIC v1.0 LAUNCHER.

ADDITIVE, NEW diagnostic family
(``ra_medfilm_barr_phase36_final_probability_authority_diagnostic_v1_0``).

This launcher exists because the D51 adjudication line (v1.0 adjudication +
v1.1 reconciliation) identified a NUMERICAL-AUTHORITY question that the v1.14
science and the v1.2 clean-equivalence diagnostic could NOT answer: does the
current frozen clean end-to-end system reproduce the Phase27 FINAL persisted
float16 prediction authority, GT-free?

Governance lessons applied (D44–D51):
  * D50 — the frozen v1.14 ``_verify_transitive_source_integrity()`` carries
    FOREIGN launcher-authority semantics.  This launcher therefore NEVER calls
    it and NEVER sets / impersonates the foreign token
    ``PHASE36_V1_14_LAUNCH_AUTHORITY`` (fail closed if it is present);
  * D50-A — the exact BYTE-INTEGRITY proof of the frozen v1.14 tree is performed
    HERE, before launch authority and before the start marker, INCLUDING the
    exact (set + SHA) equality of the frozen source's DECLARED transitive
    authority maps against the pinned manifest;
  * D50-C — authority is diagnostic-native and written ONLY after every
    non-consuming gate has passed AND the ``--verify-only`` STOP is bypassed.

D-order (pre-dispatch, fail closed):
    (1) parse args
    (2) immutable anchors: diagnostic source SHA + frozen v1.14 exec/manifest SHAs
    (3) exact project interpreter identity (D37 semantics)
    (4) CUDA readiness (D38 semantics; device-only)
    (5) FOREIGN v1.14 LAUNCH-AUTHORITY ABSENCE gate (D50-B)
    (6) prior-failure provenance binding (the consumed v1.14 science failure)
    (7) consumed-evidence binding (v1.2 start/result + D51 adjudication/reconciliation)
    (8) PRE-CONSUMPTION BYTE-INTEGRITY GATE (14 deps / 4 ckpts; exact
        source<->manifest transitive set+SHA equality) — NO torch.load
    (9) --verify-only STOP (non-consuming)
    (10) set diagnostic-v1.0 launch-authority token ONLY now
    (11) dispatch the diagnostic module ONLY

There is NO auto-relaunch.  No test hook can weaken production ``main()``.
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

DIAGNOSTIC_SELF = ROOT / "scripts" / "analysis" / "phase36_final_probability_authority_diagnostic_v1_0.py"
FROZEN_V1_14 = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_14.py"
MANIFEST_V1_14 = ROOT / "reports" / "audits" / "phase36_v1_14_runtime_source_integrity_manifest.json"

CANONICAL_INTERPRETER = ROOT / ".venv" / "Scripts" / "python.exe"

# D50-C — diagnostic-native authority ONLY.
LAUNCH_AUTHORITY_TOKEN = "PHASE36_FINAL_PROB_AUTHORITY_V1_0_LAUNCH_AUTHORITY"
ONE_SHOT_ENV = "PHASE36_FINAL_PROB_AUTHORITY_EXECUTE"
# D50-B — the FOREIGN v1.14 launcher token: must NEVER be set by this diagnostic.
FOREIGN_V1_14_LAUNCH_TOKEN = "PHASE36_V1_14_LAUNCH_AUTHORITY"

# ---- FROZEN anchors (LITERAL, IMMUTABLE, NON-ENV-OVERRIDABLE) ------------- #
FROZEN_EXPECTED_DIAGNOSTIC_SHA = "89673c6fe6a86d1abe04a5987c0675bc5c5246e24c98979bc7649431b87b319f"
FROZEN_EXPECTED_V1_14_EXEC_SHA = "ac09ff8ded3610244920e66612145b246b33127140d344a9730d454bab27cff5"
FROZEN_EXPECTED_V1_14_MANIFEST_SHA = "b4c358dfcb5e7b59beb6ae1ba2cffc64677d10049e12568b4c8eea8e79bb911e"

# D50-A: expected transitive counts (must match the frozen manifest exactly).
EXPECTED_N_DEPENDENCIES = 14
EXPECTED_N_CHECKPOINTS = 4

_PLACEHOLDER = "__FROZEN_DIAG_SHA__"

# Prior-failure provenance pins (the consumed v1.14 science failure).
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

# Consumed-evidence binding: the v1.2 attempt + the D51 adjudication line.
CONSUMED_EVIDENCE_PROVENANCE = {
    "v1_2_start_marker": ("reports/audits/phase36_clean_equivalence_diagnostic_start_v1_2.json",
                          "be93d494b1aa2aad3c900f442c16efe55bcbf0bd508a72df8f8b83e72cd7d2d3"),
    "v1_2_result": ("reports/audits/phase36_clean_equivalence_diagnostic_result_v1_2.json",
                    "b64f7e6282f9abb864a5d5bc438a22e1096aaf56e0a4e94fe53ba7c9bab6fa4a"),
    "d51_adjudication_v1_0": ("reports/audits/phase36_clean_equivalence_d51_numerical_authority_adjudication_v1_0.json",
                              "27ac7ada4ee39190d8823b8b1ff7e6e2beb304e2e7fc5778542883ac7eacc53a"),
    "d51_reconciliation_v1_1": ("reports/audits/phase36_clean_equivalence_d51_reconciliation_v1_1.json",
                                "d8e3e83e6c31004e610faef9d93c221c026eb8974c033f47fbff91106836758b"),
}
REQUIRED_V1_2_START_ARTIFACT_KIND = "PHASE36_CLEAN_EQ_DIAGNOSTIC_START"
REQUIRED_V1_2_RESULT_ARTIFACT_KIND = "PHASE36_CLEAN_EQUIVALENCE_DIAGNOSTIC_RESULT"
REQUIRED_V1_2_DIAGNOSIS = "CLEAN_EQUIVALENCE_FAILS__REPRODUCED__SEE_FAILING_CHECKS_AND_MISMATCH_LISTS"
REQUIRED_V1_2_DICE_MISMATCHES = 390
REQUIRED_V1_2_MAX_ABS_DICE_DEVIATION = 0.3810357118803769
REQUIRED_D51_ADJUDICATION_VERDICT = "D51_ROOT_CAUSE_ESTABLISHED__BOTH_BOUNDARIES"
REQUIRED_D51_RECONCILIATION_VERDICT = (
    "D51_ROOT_CAUSE_PARTIALLY_ESTABLISHED__FINAL_SCORE_BOUNDARY_CONFIRMED__G_HANDOFF_CAUSALITY_UNPROVEN")
REQUIRED_D51_G_REPAIR_STATUS = "WITHDRAWN"

T_ANCHOR_FAILED = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_0_LAUNCH_FAIL_CLOSED__ANCHOR_VERIFICATION_FAILED__NO_ATTEMPT_CONSUMED"
T_WRONG_INTERPRETER = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_0_LAUNCH_FAIL_CLOSED__WRONG_INTERPRETER__NO_ATTEMPT_CONSUMED"
T_CUDA_UNAVAILABLE = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_0_LAUNCH_FAIL_CLOSED__CUDA_READINESS_FAILED__NO_ATTEMPT_CONSUMED"
T_FOREIGN_TOKEN_PRESENT = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_0_FAIL_CLOSED__FOREIGN_V1_14_LAUNCH_AUTHORITY_PRESENT__NO_ATTEMPT_CONSUMED"
T_PROVENANCE_FAILED = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_0_LAUNCH_FAIL_CLOSED__PRIOR_FAILURE_PROVENANCE_NOT_BOUND__NO_ATTEMPT_CONSUMED"
T_CONSUMED_BIND_FAILED = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_0_LAUNCH_FAIL_CLOSED__CONSUMED_EVIDENCE_NOT_BOUND__NO_ATTEMPT_CONSUMED"
T_TRANSITIVE_FAILED = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_0_FAIL_CLOSED__TRANSITIVE_INTEGRITY_FAILED__NO_ATTEMPT_CONSUMED"
T_AUTHORITY_EXACT_FAILED = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_0_FAIL_CLOSED__SOURCE_MANIFEST_TRANSITIVE_AUTHORITY_MISMATCH__NO_ATTEMPT_CONSUMED"
T_VERIFY_ONLY_OK = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_0_LAUNCH_READINESS_VERIFIED__DISPATCH_SUPPRESSED_BY_VERIFY_ONLY"


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
    launcher_key = True
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


def check_foreign_v1_14_token_absent(environ: dict | None = None) -> dict:
    """D50-B — the FOREIGN v1.14 launcher token MUST be ABSENT.

    Returns ok=True iff ``PHASE36_V1_14_LAUNCH_AUTHORITY`` is NOT "1".
    """
    env = os.environ if environ is None else environ
    present = env.get(FOREIGN_V1_14_LAUNCH_TOKEN) == "1"
    raw = env.get(FOREIGN_V1_14_LAUNCH_TOKEN)
    return {
        "ok": not present,
        "foreign_token": FOREIGN_V1_14_LAUNCH_TOKEN,
        "foreign_token_present": bool(present),
        "foreign_token_raw": raw,
        "note": "DIAGNOSTIC_MUST_NOT_MASQUERADE_AS_V1_14_LAUNCHER",
    }


def check_prior_failure_provenance() -> dict:
    """Bind the exact consumed v1.14 science failure that justified this line."""
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


def check_consumed_evidence() -> dict:
    """Bind the consumed v1.2 attempt + the D51 adjudication/reconciliation line.

    This is the *raison d'être* binding: it proves the exact failure this new
    diagnostic is designed to interrogate (GT-free) is durably recorded and that
    the D51 correction (partial verdict; G repair WITHDRAWN) is in force.
    """
    out = {"ok": True, "items": {}, "predicates": {}}
    for name, (rel, exp) in CONSUMED_EVIDENCE_PROVENANCE.items():
        p = ROOT / rel
        ok = p.exists() and sha(p) == exp
        out["items"][name] = {"path": rel, "present": p.exists(), "expected": exp,
                              "observed": (sha(p) if p.exists() else None), "match": bool(ok)}
        if not ok:
            out["ok"] = False

    pred = {
        "v1_2_start_artifact_kind": None,
        "v1_2_result_artifact_kind": None,
        "v1_2_diagnosis": None,
        "v1_2_all_pass": None,
        "v1_2_dice_mismatches_n": None,
        "v1_2_max_abs_dice_deviation": None,
        "d51_adjudication_verdict": None,
        "d51_reconciliation_verdict": None,
        "d51_reconciliation_superseded_verdict": None,
        "d51_g_repair_status": None,
        "d51_original_adjudication_not_overwritten": None,
    }

    start_p = ROOT / CONSUMED_EVIDENCE_PROVENANCE["v1_2_start_marker"][0]
    result_p = ROOT / CONSUMED_EVIDENCE_PROVENANCE["v1_2_result"][0]
    adj_p = ROOT / CONSUMED_EVIDENCE_PROVENANCE["d51_adjudication_v1_0"][0]
    rec_p = ROOT / CONSUMED_EVIDENCE_PROVENANCE["d51_reconciliation_v1_1"][0]

    try:
        pred["v1_2_start_artifact_kind"] = json.loads(
            start_p.read_text(encoding="utf-8")).get("artifact_kind")
    except Exception as exc:  # noqa: BLE001
        pred["v1_2_start_parse_error"] = type(exc).__name__
        out["ok"] = False
    try:
        rj = json.loads(result_p.read_text(encoding="utf-8"))
        cef = rj.get("clean_equivalence_full", {}) or {}
        pred["v1_2_result_artifact_kind"] = rj.get("artifact_kind")
        pred["v1_2_diagnosis"] = rj.get("diagnosis")
        pred["v1_2_all_pass"] = rj.get("all_pass")
        dm = cef.get("dice_mismatches")
        pred["v1_2_dice_mismatches_n"] = (len(dm) if isinstance(dm, list) else dm)
        pred["v1_2_max_abs_dice_deviation"] = cef.get("max_abs_dice_deviation")
    except Exception as exc:  # noqa: BLE001
        pred["v1_2_result_parse_error"] = type(exc).__name__
        out["ok"] = False
    try:
        pred["d51_adjudication_verdict"] = json.loads(
            adj_p.read_text(encoding="utf-8")).get("verdict")
    except Exception as exc:  # noqa: BLE001
        pred["d51_adjudication_parse_error"] = type(exc).__name__
        out["ok"] = False
    try:
        rj2 = json.loads(rec_p.read_text(encoding="utf-8"))
        pred["d51_reconciliation_verdict"] = rj2.get("corrected_overall_verdict")
        pred["d51_reconciliation_superseded_verdict"] = rj2.get("superseded_verdict")
        pred["d51_g_repair_status"] = (rj2.get("g_quantization_repair", {}) or {}).get("status")
        pred["d51_original_adjudication_not_overwritten"] = rj2.get("original_adjudication_not_overwritten")
    except Exception as exc:  # noqa: BLE001
        pred["d51_reconciliation_parse_error"] = type(exc).__name__
        out["ok"] = False

    out["predicates"] = pred
    ok_predicates = bool(
        pred["v1_2_start_artifact_kind"] == REQUIRED_V1_2_START_ARTIFACT_KIND
        and pred["v1_2_result_artifact_kind"] == REQUIRED_V1_2_RESULT_ARTIFACT_KIND
        and pred["v1_2_diagnosis"] == REQUIRED_V1_2_DIAGNOSIS
        and pred["v1_2_all_pass"] is False
        and pred["v1_2_dice_mismatches_n"] == REQUIRED_V1_2_DICE_MISMATCHES
        and pred["v1_2_max_abs_dice_deviation"] == REQUIRED_V1_2_MAX_ABS_DICE_DEVIATION
        and pred["d51_adjudication_verdict"] == REQUIRED_D51_ADJUDICATION_VERDICT
        and pred["d51_reconciliation_verdict"] == REQUIRED_D51_RECONCILIATION_VERDICT
        and pred["d51_reconciliation_superseded_verdict"] == REQUIRED_D51_ADJUDICATION_VERDICT
        and pred["d51_g_repair_status"] == REQUIRED_D51_G_REPAIR_STATUS
        and pred["d51_original_adjudication_not_overwritten"] is True)
    out["ok"] = bool(out["ok"] and ok_predicates)
    return out


def _load_frozen_v1_14_authority_maps(v14_path: Path) -> dict:
    """Parse the frozen v1.14 source's DECLARED transitive authority maps.

    Uses the module's own literal constants via a restricted AST parse (NO import,
    NO execution, NO torch, NO checkpoint).  Returns the two dicts or an error.
    """
    import ast as _ast
    try:
        src = Path(v14_path).read_text(encoding="utf-8")
        tree = _ast.parse(src)
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"PARSE::{type(exc).__name__}"}
    want = {"TRANSITIVE_RUNTIME_DEPENDENCIES", "TRANSITIVE_RUNTIME_CHECKPOINTS"}
    found: dict = {}
    for node in tree.body:
        if isinstance(node, _ast.Assign):
            for t in node.targets:
                if isinstance(t, _ast.Name) and t.id in want:
                    try:
                        found[t.id] = _ast.literal_eval(node.value)
                    except Exception as exc:  # noqa: BLE001
                        return {"ok": False, "error": f"LITERAL_EVAL::{t.id}::{type(exc).__name__}"}
    if set(found.keys()) != want:
        return {"ok": False, "error": f"MISSING_MAPS::{sorted(want - set(found.keys()))}"}
    return {"ok": True, "deps": found["TRANSITIVE_RUNTIME_DEPENDENCIES"],
            "ckpts": found["TRANSITIVE_RUNTIME_CHECKPOINTS"]}


def check_transitive_integrity(manifest_path: Path | None = None,
                               v14_path: Path | None = None,
                               root: Path | None = None) -> dict:
    """D50-A — PRE-CONSUMPTION HASH-ONLY BYTE-INTEGRITY GATE.

    Verifies: manifest SHA, execution_source_sha256, exactly 14 dependencies,
    exactly 4 checkpoints, every actual dependency SHA, every actual checkpoint
    SHA, launcher_sha256 absence — AND proves the frozen v1.14 source's DECLARED
    transitive authority maps agree EXACTLY (set + SHA) with the pinned manifest.
    NO torch.load, NO model construction, NO checkpoint deserialization, NO VAL/GT.
    """
    man_p = Path(manifest_path) if manifest_path is not None else MANIFEST_V1_14
    v14_p = Path(v14_path) if v14_path is not None else FROZEN_V1_14
    base = Path(root) if root is not None else ROOT
    out = {"ok": False, "manifest_sha": None, "manifest_sha_expected": FROZEN_EXPECTED_V1_14_MANIFEST_SHA,
           "execution_source_declared": None, "execution_source_expected": FROZEN_EXPECTED_V1_14_EXEC_SHA,
           "frozen_v1_14_source_sha": None, "frozen_v1_14_source_sha_expected": FROZEN_EXPECTED_V1_14_EXEC_SHA,
           "n_dependencies": None, "n_checkpoints": None,
           "n_dependencies_expected": EXPECTED_N_DEPENDENCIES,
           "n_checkpoints_expected": EXPECTED_N_CHECKPOINTS,
           "dependencies": {}, "checkpoints": {}, "launcher_sha256_absent": None,
           "source_manifest_transitive_authority_exact_match": False,
           "authority_set_equal": {"dependencies": None, "checkpoints": None},
           "authority_sha_equal": {"dependencies": None, "checkpoints": None},
           "torch_load": False, "checkpoint_deserialization": False,
           "model_construction": False, "val_or_gt_read": False}
    if not man_p.exists():
        out["reason"] = "MANIFEST_MISSING"
        return out
    out["manifest_sha"] = sha(man_p)
    if out["manifest_sha"] != FROZEN_EXPECTED_V1_14_MANIFEST_SHA:
        out["reason"] = "MANIFEST_SHA_MISMATCH"
        return out

    # D50-A: the frozen v1.14 SOURCE bytes must also match the pinned exec SHA.
    if not v14_p.exists():
        out["reason"] = "FROZEN_V1_14_SOURCE_MISSING"
        return out
    out["frozen_v1_14_source_sha"] = sha(v14_p)
    out["frozen_v1_14_source_sha_expected"] = FROZEN_EXPECTED_V1_14_EXEC_SHA
    if out["frozen_v1_14_source_sha"] != FROZEN_EXPECTED_V1_14_EXEC_SHA:
        out["reason"] = "FROZEN_V1_14_SOURCE_SHA_MISMATCH"
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

    # ---- D50-A item 9: source<->manifest EXACT transitive authority equality -- #
    maps = _load_frozen_v1_14_authority_maps(v14_p)
    if not maps.get("ok"):
        out["reason"] = f"SOURCE_AUTHORITY_MAPS_UNAVAILABLE::{maps.get('error')}"
        out["ok"] = False
        return out
    src_deps, src_ckpts = maps["deps"], maps["ckpts"]
    man_deps = dict(deps)
    man_ckpts = dict(ckpts)
    set_equal_deps = set(src_deps.keys()) == set(man_deps.keys())
    set_equal_ckpts = set(src_ckpts.keys()) == set(man_ckpts.keys())
    sha_equal_deps = set_equal_deps and all(src_deps[k] == man_deps.get(k) for k in src_deps)
    sha_equal_ckpts = set_equal_ckpts and all(src_ckpts[k] == man_ckpts.get(k) for k in src_ckpts)
    out["authority_set_equal"] = {"dependencies": bool(set_equal_deps), "checkpoints": bool(set_equal_ckpts)}
    out["authority_sha_equal"] = {"dependencies": bool(sha_equal_deps), "checkpoints": bool(sha_equal_ckpts)}
    exact = bool(set_equal_deps and set_equal_ckpts and sha_equal_deps and sha_equal_ckpts)
    out["source_manifest_transitive_authority_exact_match"] = exact
    out["source_authority_map_counts"] = {"dependencies": len(src_deps), "checkpoints": len(src_ckpts)}
    all_ok = all_ok and exact

    out["ok"] = bool(all_ok)
    if not out["ok"]:
        if out.get("reason") is None:
            out["reason"] = ("SOURCE_MANIFEST_TRANSITIVE_AUTHORITY_MISMATCH"
                             if not exact else "TRANSITIVE_BYTE_MISMATCH")
    return out


def _emit(terminal: str, **extra) -> int:
    payload = {"launcher": "launch_phase36_final_probability_authority_diagnostic_v1_0",
               "terminal": terminal}
    payload.update(extra)
    print(json.dumps(payload, indent=1))
    return 2


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify-only", action="store_true",
                    help="verify anchors + interpreter + CUDA + foreign-token absence + "
                         "provenance + consumed-evidence binding + transitive integrity "
                         "and exit WITHOUT dispatching.")
    a = ap.parse_args()

    # (2) immutable anchor
    auth = verify_authority()
    if not auth["authorized"]:
        return _emit(T_ANCHOR_FAILED, authorized=False, authority=auth)

    # (3) exact project interpreter
    interp = check_interpreter_identity()
    if not interp["ok"]:
        return _emit(T_WRONG_INTERPRETER, authorized=False, interpreter=interp, authority=auth,
                     hint=r"Invoke the canonical interpreter explicitly, e.g. "
                          r"D:\Softfors\jup\.venv\Scripts\python.exe "
                          r"scripts\analysis\launch_phase36_final_probability_authority_diagnostic_v1_0.py --verify-only")

    # (4) CUDA readiness
    cuda = check_cuda_readiness()
    if not cuda["ok"]:
        return _emit(T_CUDA_UNAVAILABLE, authorized=False, interpreter=interp,
                     cuda_readiness=cuda, authority=auth)

    # (5) D50-B foreign v1.14 launch-authority ABSENCE gate
    foreign = check_foreign_v1_14_token_absent()
    if not foreign["ok"]:
        return _emit(T_FOREIGN_TOKEN_PRESENT, authorized=False, foreign_gate=foreign,
                     interpreter=interp, cuda_readiness=cuda, authority=auth)

    # (6) prior-failure provenance binding
    prov = check_prior_failure_provenance()
    if not prov["ok"]:
        return _emit(T_PROVENANCE_FAILED, authorized=False, provenance=prov,
                     foreign_gate=foreign, interpreter=interp, cuda_readiness=cuda, authority=auth)

    # (7) consumed-evidence binding (v1.2 attempt + D51 adjudication line)
    consumed = check_consumed_evidence()
    if not consumed["ok"]:
        return _emit(T_CONSUMED_BIND_FAILED, authorized=False, consumed_evidence=consumed,
                     provenance=prov, foreign_gate=foreign, interpreter=interp,
                     cuda_readiness=cuda, authority=auth)

    # (8) D50-A pre-consumption byte-integrity gate (incl. exact authority equality)
    ti = check_transitive_integrity()
    if not ti["ok"]:
        term = (T_AUTHORITY_EXACT_FAILED
                if ti.get("reason") == "SOURCE_MANIFEST_TRANSITIVE_AUTHORITY_MISMATCH"
                else T_TRANSITIVE_FAILED)
        return _emit(term, authorized=False, transitive_integrity=ti, consumed_evidence=consumed,
                     provenance=prov, foreign_gate=foreign, interpreter=interp,
                     cuda_readiness=cuda, authority=auth)

    # (9) verify-only STOP (non-consuming)
    # D50-C stage order: the diagnostic-v1.0 launch-authority token is set ONLY
    # after every non-consuming gate has passed AND the verify-only STOP is
    # bypassed, i.e. immediately before dispatch. Setting it earlier would make
    # the token observable during a --verify-only run.
    if a.verify_only:
        print(json.dumps({
            "launcher": "launch_phase36_final_probability_authority_diagnostic_v1_0",
            "authorized": True,
            "anchor_pass": True,
            "interpreter_pass": True,
            "cuda_readiness_pass": True,
            "foreign_v1_14_token_absent_pass": True,
            "prior_failure_provenance_pass": True,
            "consumed_evidence_binding_pass": True,
            "transitive_integrity_pass": True,
            "source_manifest_transitive_authority_exact_match": ti["source_manifest_transitive_authority_exact_match"],
            "n_dependencies_verified": ti["n_dependencies"],
            "n_checkpoints_verified": ti["n_checkpoints"],
            "terminal": T_VERIFY_ONLY_OK,
            "interpreter": interp,
            "cuda_readiness": cuda,
            "foreign_gate": foreign,
            "consumed_evidence_predicates": consumed["predicates"],
            "one_shot_gate_set": os.environ.get(ONE_SHOT_ENV) == "1",
        }, indent=1))
        return 0

    # D50-C: the ONLY write of the diagnostic-native launch-authority token.
    # It appears exactly once in this file, strictly AFTER the verify-only STOP
    # guard, so a --verify-only run can never observe it set.
    os.environ[LAUNCH_AUTHORITY_TOKEN] = "1"

    # (11) dispatch the diagnostic module ONLY
    import importlib.util
    spec = importlib.util.spec_from_file_location("phase36_final_prob_authority_diag_v1_0",
                                                  DIAGNOSTIC_SELF)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return int(mod.main())


if __name__ == "__main__":
    raise SystemExit(main())
