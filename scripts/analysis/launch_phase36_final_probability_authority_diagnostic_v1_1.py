#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 36 — FINAL-PROBABILITY AUTHORITY DIAGNOSTIC v1.1 LAUNCHER.

ADDITIVE revision of the v1.0 launcher.  v1.0 remains byte-for-byte frozen.

Repairs:
  * **D52** FINAL_AUTHORITY_NOT_BOUND_PRECONSUMPTION — this launcher now verifies
    the exact Phase27 FINAL float16 prediction authority (exists / raw-byte SHA /
    ``.npy`` header shape + dtype / GT-free sample-order binding) BEFORE:
      - the v1.1 launch-authority token,
      - the diagnostic import/dispatch,
      - the diagnostic start marker,
      - checkpoint load / model construction / VAL image read.
  * D50 (from v1.0): the frozen v1.14 ``_verify_transitive_source_integrity()`` is
    NEVER called; the FOREIGN token ``PHASE36_V1_14_LAUNCH_AUTHORITY`` is NEVER set
    and its presence FAILS CLOSED.
  * v1.0 source preservation is verified (all 5 v1.0 SHAs pinned).

Required order (fail closed):
    (1) parse args
    (2) immutable anchors: v1.1 diagnostic SHA + frozen v1.14 exec/manifest SHAs
    (3) exact project interpreter identity
    (4) CUDA readiness
    (5) FOREIGN v1.14 LAUNCH-AUTHORITY ABSENCE gate
    (6) prior-failure provenance binding
    (7) consumed v1.2 / D51 provenance binding
    (8) v1.0 source preservation (5 pins)
    (9) exact 14-dependency / 4-checkpoint integrity + exact source<->manifest equality
    (10) **D52** Phase27 FINAL f16 authority SHA / header / sample-order gate
    (11) --verify-only STOP (non-consuming)
    (12) set the v1.1 launch-authority token ONLY now
    (13) dispatch the diagnostic module ONLY

There is NO auto-relaunch.  No test hook can weaken production ``main()``.
"""
from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DIAGNOSTIC_SELF = ROOT / "scripts" / "analysis" / "phase36_final_probability_authority_diagnostic_v1_1.py"
FROZEN_V1_14 = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_14.py"
MANIFEST_V1_14 = ROOT / "reports" / "audits" / "phase36_v1_14_runtime_source_integrity_manifest.json"

CANONICAL_INTERPRETER = ROOT / ".venv" / "Scripts" / "python.exe"

# D50-C — diagnostic-native authority ONLY (v1.1 token).
LAUNCH_AUTHORITY_TOKEN = "PHASE36_FINAL_PROB_AUTHORITY_V1_1_LAUNCH_AUTHORITY"
ONE_SHOT_ENV = "PHASE36_FINAL_PROB_AUTHORITY_EXECUTE"
FOREIGN_V1_14_LAUNCH_TOKEN = "PHASE36_V1_14_LAUNCH_AUTHORITY"

# ---- FROZEN anchors (LITERAL, IMMUTABLE, NON-ENV-OVERRIDABLE) ------------- #
FROZEN_EXPECTED_DIAGNOSTIC_SHA = "b9f6a449445d8ac5edd1dafe30e2f0b5005d487be314011bd2ff9162db770672"
FROZEN_EXPECTED_V1_14_EXEC_SHA = "ac09ff8ded3610244920e66612145b246b33127140d344a9730d454bab27cff5"
FROZEN_EXPECTED_V1_14_MANIFEST_SHA = "b4c358dfcb5e7b59beb6ae1ba2cffc64677d10049e12568b4c8eea8e79bb911e"

EXPECTED_N_DEPENDENCIES = 14
EXPECTED_N_CHECKPOINTS = 4

# ---- v1.0 source pins (must remain byte-for-byte) ------------------------- #
V1_0_PINS = {
    "scripts/analysis/phase36_final_probability_authority_diagnostic_v1_0.py":
        "89673c6fe6a86d1abe04a5987c0675bc5c5246e24c98979bc7649431b87b319f",
    "scripts/analysis/launch_phase36_final_probability_authority_diagnostic_v1_0.py":
        "f77b9fd4226cc2eb7a71d84b07e06d28719d7f56fc7ef10f842005f7656ccdc6",
    "scripts/analysis/phase36_final_probability_authority_diagnostic_unit_v1_0.py":
        "7cccd24cfaba2ecb243871aa44389c4f8c88b5ce782972e8d41be13e34ba5acf",
    "scripts/analysis/phase36_final_probability_authority_diagnostic_preflight_v1_0.py":
        "a7d13d122f8aaeb522ec213968917085aa79804caaafa7aecd835fead74591c3",
    "scripts/analysis/phase36_final_probability_authority_diagnostic_negative_controls_v1_0.py":
        "126d95548179fd5886e2687f84ca1927c60c0c30b75f6e929f211ecd4759df86",
}

# ---- D52 — Phase27 FINAL float16 prediction authority --------------------- #
PHASE27_FINAL_PROB_AUTHORITY_PATH = "data_cache/phase27_barr_preservation_v1_0/phase27_val808_final_prob_f16.npy"
PHASE27_FINAL_PROB_AUTHORITY_SHA = "506ab6c4e715a9106889e186c146b73903493c80a63258007954cf5deb3ea9cf"
PHASE27_FINAL_PROB_AUTHORITY_SHAPE = (808, 512, 512)
PHASE27_FINAL_PROB_AUTHORITY_DTYPE = "float16"
SEGMENTATION_OUTPUT_THRESHOLD = 0.50

# ---- D52 — sample-order authority (GT-free) ------------------------------- #
VAL_MANIFEST = "manifests/phase4_v3/val.csv"
VAL_MANIFEST_SHA = "082c80b2bda63fd73f371f109c34643adf01edaead921643fb2e44993ba53315"
PHASE27_SCORES_CSV = "reports/tables/phase27_val808_per_sample_scores.csv"
PHASE27_SCORES_CSV_SHA = "702133930ce14ac9513c992833396e3e250d08417b17d1032cbd260a405cfb12"
CANONICAL_DOMAIN_ORDER = ("BUSI", "ISIC", "KUB", "KVASIR")
EXPECTED_SAMPLE_N = 808

# Prior-failure provenance pins (unchanged).
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

# Consumed-evidence binding (v1.2 attempt + D51 line).
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

T_ANCHOR_FAILED = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_1_LAUNCH_FAIL_CLOSED__ANCHOR_VERIFICATION_FAILED__NO_ATTEMPT_CONSUMED"
T_WRONG_INTERPRETER = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_1_LAUNCH_FAIL_CLOSED__WRONG_INTERPRETER__NO_ATTEMPT_CONSUMED"
T_CUDA_UNAVAILABLE = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_1_LAUNCH_FAIL_CLOSED__CUDA_READINESS_FAILED__NO_ATTEMPT_CONSUMED"
T_FOREIGN_TOKEN_PRESENT = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_1_FAIL_CLOSED__FOREIGN_V1_14_LAUNCH_AUTHORITY_PRESENT__NO_ATTEMPT_CONSUMED"
T_PROVENANCE_FAILED = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_1_LAUNCH_FAIL_CLOSED__PRIOR_FAILURE_PROVENANCE_NOT_BOUND__NO_ATTEMPT_CONSUMED"
T_CONSUMED_BIND_FAILED = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_1_LAUNCH_FAIL_CLOSED__CONSUMED_EVIDENCE_NOT_BOUND__NO_ATTEMPT_CONSUMED"
T_V1_0_PRESERVATION_FAILED = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_1_LAUNCH_FAIL_CLOSED__V1_0_SOURCE_NOT_PRESERVED__NO_ATTEMPT_CONSUMED"
T_TRANSITIVE_FAILED = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_1_FAIL_CLOSED__TRANSITIVE_INTEGRITY_FAILED__NO_ATTEMPT_CONSUMED"
T_AUTHORITY_EXACT_FAILED = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_1_FAIL_CLOSED__SOURCE_MANIFEST_TRANSITIVE_AUTHORITY_MISMATCH__NO_ATTEMPT_CONSUMED"
T_FINAL_AUTHORITY_FAILED = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_1_FAIL_CLOSED__FINAL_AUTHORITY_PRECONSUMPTION_GATE_FAILED__NO_ATTEMPT_CONSUMED"
T_VERIFY_ONLY_OK = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_1_LAUNCH_READINESS_VERIFIED__DISPATCH_SUPPRESSED_BY_VERIFY_ONLY"


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _norm(path) -> str:
    return os.path.normcase(os.path.realpath(str(path)))


def _frozen_diag_sha() -> str:
    return FROZEN_EXPECTED_DIAGNOSTIC_SHA


def _read_npy_header(path: Path) -> dict:
    """Header-only ``.npy`` inspection (NO array data, NO memory blow-up)."""
    with open(path, "rb") as f:
        magic = f.read(6)
        if magic != b"\x93NUMPY":
            raise ValueError("NPY_BAD_MAGIC")
        major, minor = f.read(2)
        if (major, minor) == (1, 0):
            hlen = int.from_bytes(f.read(2), "little")
        elif (major, minor) == (2, 0):
            hlen = int.from_bytes(f.read(4), "little")
        else:
            raise ValueError(f"NPY_BAD_VERSION::{major}.{minor}")
        header = f.read(hlen).decode("latin1")
    return ast.literal_eval(header.strip())


def verify_authority(diag_path: Path | None = None,
                     v14_path: Path | None = None,
                     manifest_path: Path | None = None) -> dict:
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
        "match": bool(obs_diag == exp_diag)}

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
        "note": "DIAGNOSTIC_EXACT_INTERPRETER_IDENTITY__NO_AUTO_RELAUNCH",
    }


def check_cuda_readiness() -> dict:
    out = {"ok": False, "torch_imported": False, "torch_version": None,
           "torch_cuda_version": None, "cuda_available": False, "device_count": 0,
           "resolved_device": None, "torch_load": False, "checkpoint_read": False,
           "model_forward": False, "val_image_read": False, "gt_read": False, "training": False}
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
    env = os.environ if environ is None else environ
    present = env.get(FOREIGN_V1_14_LAUNCH_TOKEN) == "1"
    return {"ok": not present, "foreign_token": FOREIGN_V1_14_LAUNCH_TOKEN,
            "foreign_token_present": bool(present), "foreign_token_raw": env.get(FOREIGN_V1_14_LAUNCH_TOKEN),
            "note": "DIAGNOSTIC_MUST_NOT_MASQUERADE_AS_V1_14_LAUNCHER"}


def check_prior_failure_provenance() -> dict:
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
    out = {"ok": True, "items": {}, "predicates": {}}
    for name, (rel, exp) in CONSUMED_EVIDENCE_PROVENANCE.items():
        p = ROOT / rel
        ok = p.exists() and sha(p) == exp
        out["items"][name] = {"path": rel, "present": p.exists(), "expected": exp,
                              "observed": (sha(p) if p.exists() else None), "match": bool(ok)}
        if not ok:
            out["ok"] = False

    pred = {"v1_2_start_artifact_kind": None, "v1_2_result_artifact_kind": None,
            "v1_2_diagnosis": None, "v1_2_all_pass": None, "v1_2_dice_mismatches_n": None,
            "v1_2_max_abs_dice_deviation": None, "d51_adjudication_verdict": None,
            "d51_reconciliation_verdict": None, "d51_reconciliation_superseded_verdict": None,
            "d51_g_repair_status": None, "d51_original_adjudication_not_overwritten": None}
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


def check_v1_0_preserved(root: Path | None = None) -> dict:
    base = Path(root) if root is not None else ROOT
    out = {"ok": True, "items": {}}
    for rel, exp in V1_0_PINS.items():
        p = base / rel
        obs = sha(p) if p.exists() else None
        m = (obs == exp)
        out["items"][rel] = {"present": p.exists(), "expected": exp, "observed": obs, "match": bool(m)}
        if not m:
            out["ok"] = False
    return out


def _load_frozen_v1_14_authority_maps(v14_path: Path) -> dict:
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
    if not v14_p.exists():
        out["reason"] = "FROZEN_V1_14_SOURCE_MISSING"
        return out
    out["frozen_v1_14_source_sha"] = sha(v14_p)
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


# --------------------------------------------------------------------------- #
# D52 — PRE-CONSUMPTION PHASE27 FINAL AUTHORITY GATE (GT-free)
# --------------------------------------------------------------------------- #
def check_final_authority_preconsumption(authority_path: Path | None = None,
                                         manifest_path: Path | None = None,
                                         scores_path: Path | None = None,
                                         root: Path | None = None) -> dict:
    """Verify the exact Phase27 FINAL float16 prediction authority BEFORE consumption.

    Checks (all GT-free — no VAL image bytes, no GT bytes):
      1. authority file exists
      2. raw-byte SHA exact
      3. ``.npy`` header shape exact  (header-only inspection)
      4. ``.npy`` header dtype exact  (header-only inspection)
      5. sample-order authority:
         a. frozen VAL manifest SHA + 808 rows
         b. Phase27 per-sample scores CSV SHA + 808 unique sample_ids
         c. CSV sample_id order == canonical (dataset asc, sample_id asc) order
         d. STRONG GT-free row binding: (authority[i] >= 0.5).sum() == csv.final_fg_pixels[i]
            for every row (binds npy row i <-> CSV row i using prediction-derived counts only)
    """
    base = Path(root) if root is not None else ROOT
    auth_p = Path(authority_path) if authority_path is not None else base / PHASE27_FINAL_PROB_AUTHORITY_PATH
    man_p = Path(manifest_path) if manifest_path is not None else base / VAL_MANIFEST
    sc_p = Path(scores_path) if scores_path is not None else base / PHASE27_SCORES_CSV

    out = {
        "final_authority_preconsumption_pass": False,
        "final_authority_sha256": None,
        "final_authority_sha256_expected": PHASE27_FINAL_PROB_AUTHORITY_SHA,
        "final_authority_shape": None,
        "final_authority_shape_expected": list(PHASE27_FINAL_PROB_AUTHORITY_SHAPE),
        "final_authority_dtype": None,
        "final_authority_dtype_expected": PHASE27_FINAL_PROB_AUTHORITY_DTYPE,
        "final_authority_sample_order_pass": False,
        "reason": None,
        # no-IO flags
        "torch_load": False, "checkpoint_deserialization": False,
        "model_construction": False, "val_image_read": False, "gt_read": False,
    }

    # 1. exists
    if not auth_p.exists():
        out["reason"] = "FINAL_AUTHORITY_ABSENT"
        return out

    # 2. raw-byte SHA
    out["final_authority_sha256"] = sha(auth_p)
    if out["final_authority_sha256"] != PHASE27_FINAL_PROB_AUTHORITY_SHA:
        out["reason"] = "FINAL_AUTHORITY_SHA_MISMATCH"
        return out

    # 3/4. header-only shape + dtype
    try:
        hdr = _read_npy_header(auth_p)
    except Exception as exc:  # noqa: BLE001
        out["reason"] = f"FINAL_AUTHORITY_HEADER_UNREADABLE::{type(exc).__name__}"
        return out
    try:
        shape = tuple(int(x) for x in hdr.get("shape", ()))
        descr = str(hdr.get("descr", ""))
        dtype = str(np.dtype(descr))
    except Exception as exc:  # noqa: BLE001
        out["reason"] = f"FINAL_AUTHORITY_HEADER_MALFORMED::{type(exc).__name__}"
        return out
    out["final_authority_shape"] = list(shape)
    out["final_authority_dtype"] = dtype
    if shape != tuple(PHASE27_FINAL_PROB_AUTHORITY_SHAPE):
        out["reason"] = "FINAL_AUTHORITY_SHAPE_MISMATCH"
        return out
    if dtype != PHASE27_FINAL_PROB_AUTHORITY_DTYPE:
        out["reason"] = "FINAL_AUTHORITY_DTYPE_MISMATCH"
        return out

    # 5. sample-order authority (GT-free)
    if not man_p.exists():
        out["reason"] = "VAL_MANIFEST_ABSENT"
        return out
    if sha(man_p) != VAL_MANIFEST_SHA:
        out["reason"] = "VAL_MANIFEST_SHA_MISMATCH"
        return out
    if not sc_p.exists():
        out["reason"] = "PHASE27_SCORES_CSV_ABSENT"
        return out
    if sha(sc_p) != PHASE27_SCORES_CSV_SHA:
        out["reason"] = "PHASE27_SCORES_CSV_SHA_MISMATCH"
        return out

    try:
        with man_p.open(encoding="utf-8", newline="") as fh:
            man_rows = list(csv.DictReader(fh))
    except Exception as exc:  # noqa: BLE001
        out["reason"] = f"VAL_MANIFEST_UNREADABLE::{type(exc).__name__}"
        return out
    if len(man_rows) != EXPECTED_SAMPLE_N:
        out["reason"] = "VAL_MANIFEST_SIZE_MISMATCH"
        return out
    canonical_ids = [r["sample_id"] for r in sorted(
        man_rows, key=lambda r: (str(r.get("dataset", "")), str(r["sample_id"])))]

    try:
        with sc_p.open(encoding="utf-8", newline="") as fh:
            sc_rows = list(csv.DictReader(fh))
    except Exception as exc:  # noqa: BLE001
        out["reason"] = f"PHASE27_SCORES_CSV_UNREADABLE::{type(exc).__name__}"
        return out
    if len(sc_rows) != EXPECTED_SAMPLE_N:
        out["reason"] = "PHASE27_SCORES_CSV_SIZE_MISMATCH"
        return out
    csv_ids = [r["sample_id"] for r in sc_rows]
    if len(set(csv_ids)) != EXPECTED_SAMPLE_N:
        out["reason"] = "PHASE27_SCORES_CSV_SAMPLE_ID_NOT_UNIQUE"
        return out

    # 5c. CSV order == canonical order
    if csv_ids != canonical_ids:
        out["reason"] = "FINAL_AUTHORITY_SAMPLE_ORDER_MISMATCH"
        out["sample_order_detail"] = "CSV_SAMPLE_ID_ORDER != CANONICAL_(dataset,sample_id)_ORDER"
        return out

    # 5d. STRONG GT-free row binding via prediction-derived foreground counts
    try:
        arr = np.load(auth_p, mmap_mode="r")
        if tuple(arr.shape) != tuple(PHASE27_FINAL_PROB_AUTHORITY_SHAPE):
            out["reason"] = "FINAL_AUTHORITY_SHAPE_MISMATCH"
            return out
        fg = np.asarray(arr >= np.float16(SEGMENTATION_OUTPUT_THRESHOLD)).sum(axis=(1, 2))
        csv_fg = np.asarray([int(r["final_fg_pixels"]) for r in sc_rows], dtype=np.int64)
    except Exception as exc:  # noqa: BLE001
        out["reason"] = f"FINAL_AUTHORITY_ROW_BINDING_UNREADABLE::{type(exc).__name__}"
        return out
    row_mismatch = int(np.count_nonzero(np.asarray(fg, dtype=np.int64) != csv_fg))
    out["final_authority_row_binding_mismatch_count"] = row_mismatch
    if row_mismatch != 0:
        out["reason"] = "FINAL_AUTHORITY_SAMPLE_ORDER_MISMATCH"
        out["sample_order_detail"] = "FG_PIXEL_ROW_BINDING_MISMATCH"
        return out

    out["final_authority_sample_order_pass"] = True
    out["final_authority_preconsumption_pass"] = True
    return out


def _emit(terminal: str, **extra) -> int:
    payload = {"launcher": "launch_phase36_final_probability_authority_diagnostic_v1_1",
               "terminal": terminal}
    payload.update(extra)
    print(json.dumps(payload, indent=1))
    return 2


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify-only", action="store_true",
                    help="verify all gates incl. the D52 final-authority gate and exit "
                         "WITHOUT dispatching.")
    a = ap.parse_args()

    auth = verify_authority()
    if not auth["authorized"]:
        return _emit(T_ANCHOR_FAILED, authorized=False, authority=auth)

    interp = check_interpreter_identity()
    if not interp["ok"]:
        return _emit(T_WRONG_INTERPRETER, authorized=False, interpreter=interp, authority=auth,
                     hint=r"Invoke the canonical interpreter explicitly, e.g. "
                          r"D:\Softfors\jup\.venv\Scripts\python.exe "
                          r"scripts\analysis\launch_phase36_final_probability_authority_diagnostic_v1_1.py --verify-only")

    cuda = check_cuda_readiness()
    if not cuda["ok"]:
        return _emit(T_CUDA_UNAVAILABLE, authorized=False, interpreter=interp,
                     cuda_readiness=cuda, authority=auth)

    foreign = check_foreign_v1_14_token_absent()
    if not foreign["ok"]:
        return _emit(T_FOREIGN_TOKEN_PRESENT, authorized=False, foreign_gate=foreign,
                     interpreter=interp, cuda_readiness=cuda, authority=auth)

    prov = check_prior_failure_provenance()
    if not prov["ok"]:
        return _emit(T_PROVENANCE_FAILED, authorized=False, provenance=prov,
                     foreign_gate=foreign, interpreter=interp, cuda_readiness=cuda, authority=auth)

    consumed = check_consumed_evidence()
    if not consumed["ok"]:
        return _emit(T_CONSUMED_BIND_FAILED, authorized=False, consumed_evidence=consumed,
                     provenance=prov, foreign_gate=foreign, interpreter=interp,
                     cuda_readiness=cuda, authority=auth)

    preserved = check_v1_0_preserved()
    if not preserved["ok"]:
        return _emit(T_V1_0_PRESERVATION_FAILED, authorized=False, v1_0_preservation=preserved,
                     consumed_evidence=consumed, provenance=prov, foreign_gate=foreign,
                     interpreter=interp, cuda_readiness=cuda, authority=auth)

    ti = check_transitive_integrity()
    if not ti["ok"]:
        term = (T_AUTHORITY_EXACT_FAILED
                if ti.get("reason") == "SOURCE_MANIFEST_TRANSITIVE_AUTHORITY_MISMATCH"
                else T_TRANSITIVE_FAILED)
        return _emit(term, authorized=False, transitive_integrity=ti, v1_0_preservation=preserved,
                     consumed_evidence=consumed, provenance=prov, foreign_gate=foreign,
                     interpreter=interp, cuda_readiness=cuda, authority=auth)

    # (10) D52 — Phase27 FINAL authority pre-consumption gate
    fa = check_final_authority_preconsumption()
    if not fa["final_authority_preconsumption_pass"]:
        return _emit(T_FINAL_AUTHORITY_FAILED, authorized=False, final_authority=fa,
                     transitive_integrity=ti, v1_0_preservation=preserved,
                     consumed_evidence=consumed, provenance=prov, foreign_gate=foreign,
                     interpreter=interp, cuda_readiness=cuda, authority=auth)

    # (11) verify-only STOP (non-consuming)
    if a.verify_only:
        print(json.dumps({
            "launcher": "launch_phase36_final_probability_authority_diagnostic_v1_1",
            "authorized": True,
            "anchor_pass": True,
            "interpreter_pass": True,
            "cuda_readiness_pass": True,
            "foreign_v1_14_token_absent_pass": True,
            "prior_failure_provenance_pass": True,
            "consumed_evidence_binding_pass": True,
            "v1_0_preservation_pass": True,
            "transitive_integrity_pass": True,
            "source_manifest_transitive_authority_exact_match": ti["source_manifest_transitive_authority_exact_match"],
            "n_dependencies_verified": ti["n_dependencies"],
            "n_checkpoints_verified": ti["n_checkpoints"],
            "final_authority_preconsumption_pass": fa["final_authority_preconsumption_pass"],
            "final_authority_sha256": fa["final_authority_sha256"],
            "final_authority_shape": fa["final_authority_shape"],
            "final_authority_dtype": fa["final_authority_dtype"],
            "final_authority_sample_order_pass": fa["final_authority_sample_order_pass"],
            "terminal": T_VERIFY_ONLY_OK,
            "interpreter": interp,
            "cuda_readiness": cuda,
            "foreign_gate": foreign,
            "consumed_evidence_predicates": consumed["predicates"],
            "one_shot_gate_set": os.environ.get(ONE_SHOT_ENV) == "1",
        }, indent=1))
        return 0

    # (12) the ONLY write of the v1.1 launch-authority token (after the verify STOP)
    os.environ[LAUNCH_AUTHORITY_TOKEN] = "1"

    # (13) dispatch the diagnostic module ONLY
    import importlib.util
    spec = importlib.util.spec_from_file_location("phase36_final_prob_authority_diag_v1_1",
                                                  DIAGNOSTIC_SELF)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return int(mod.main())


if __name__ == "__main__":
    raise SystemExit(main())
