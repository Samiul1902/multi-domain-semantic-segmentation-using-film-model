#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 36 — FINAL-PROBABILITY AUTHORITY DIAGNOSTIC v1.2 LAUNCHER.

ADDITIVE revision of the v1.1 launcher.  v1.0 remains byte-for-byte frozen; v1.1 is
CONSUMED_FAILED (retry FORBIDDEN).  The scientific path is UNCHANGED — v1.2 only
repairs D56 (frozen-module SUBSCRIPT -> ATTRIBUTE access) in the diagnostic module.

Repairs:
  * **D56** DIAGNOSTIC_FROZEN_MODULE_SUBSCRIPT_MISMATCH — verified at the source
    level (the launcher pins the exact v1.2 diagnostic SHA, which contains the
    attribute-access repair).
  * D52 (retained): the launcher verifies the exact Phase27 FINAL float16 prediction
    authority (exists / raw-byte SHA / ``.npy`` header shape + dtype / GT-free
    sample-order binding) BEFORE the v1.2 launch-authority token, dispatch, start
    marker, checkpoint load, model construction and VAL image read.
  * D50 (retained): the frozen v1.14 ``_verify_transitive_source_integrity()`` is
    NEVER called; the FOREIGN token ``PHASE36_V1_14_LAUNCH_AUTHORITY`` is NEVER set
    and its presence FAILS CLOSED.
  * v1.0 AND v1.1 source preservation is verified (all v1.0 + v1.1 SHAs pinned).
  * NEW: v1.1 CONSUMED-state binding gate (START/FAILURE raw SHA + RESULT absence +
    failure predicates + D56 adjudication).

Required order (fail closed):
    (1) parse args
    (2) immutable anchors: v1.2 diagnostic SHA + frozen v1.14 exec/manifest SHAs
    (3) exact project interpreter identity
    (4) CUDA readiness
    (5) FOREIGN v1.14 LAUNCH-AUTHORITY ABSENCE gate
    (6) prior-failure provenance binding
    (7) consumed v1.2 / D51 provenance binding
    (8) v1.0 + v1.1 source preservation + v1.1 governance reconciliation preservation
    (9) exact 14-dependency / 4-checkpoint integrity + exact source<->manifest equality
    (10) **D52** Phase27 FINAL f16 authority SHA / header / sample-order gate
    (11) **v1.1 CONSUMED-state** binding gate (START/FAILURE/absence/predicates)
    (12) --verify-only STOP (non-consuming)
    (13) set the v1.2 launch-authority token ONLY now
    (14) dispatch the diagnostic module ONLY

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

DIAGNOSTIC_SELF = ROOT / "scripts" / "analysis" / "phase36_final_probability_authority_diagnostic_v1_2.py"
FROZEN_V1_14 = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_14.py"
MANIFEST_V1_14 = ROOT / "reports" / "audits" / "phase36_v1_14_runtime_source_integrity_manifest.json"

CANONICAL_INTERPRETER = ROOT / ".venv" / "Scripts" / "python.exe"

# D56-C — diagnostic-native authority ONLY (v1.2 token).
LAUNCH_AUTHORITY_TOKEN = "PHASE36_FINAL_PROB_AUTHORITY_V1_2_LAUNCH_AUTHORITY"
ONE_SHOT_ENV = "PHASE36_FINAL_PROB_AUTHORITY_EXECUTE"
FOREIGN_V1_14_LAUNCH_TOKEN = "PHASE36_V1_14_LAUNCH_AUTHORITY"

# ---- FROZEN anchors (LITERAL, IMMUTABLE, NON-ENV-OVERRIDABLE) ------------- #
FROZEN_EXPECTED_DIAGNOSTIC_SHA = "981f772fd42e35ac8e3acde17344e9bcd3fb48c39aba191200a0d811f76f29f9"
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

# ---- v1.1 source pins (CONSUMED family; must remain byte-for-byte) -------- #
V1_1_PINS = {
    "scripts/analysis/phase36_final_probability_authority_diagnostic_v1_1.py":
        "b9f6a449445d8ac5edd1dafe30e2f0b5005d487be314011bd2ff9162db770672",
    "scripts/analysis/launch_phase36_final_probability_authority_diagnostic_v1_1.py":
        "4c9737362fcf01f0ef8ef629f489cdff07c72e63b46f34e4ea508b7ba0df83ae",
    "scripts/analysis/phase36_final_probability_authority_diagnostic_unit_v1_1.py":
        "0358ed115dcedea612aae1b7f0311ea08b97ba212b893a10c51ddae606fbabea",
    "scripts/analysis/phase36_final_probability_authority_diagnostic_preflight_v1_1.py":
        "7ba8899b25fbddbcebd42971eedd1bca4b2ca8d06d33629cec7a286e01227925",
    "scripts/analysis/phase36_final_probability_authority_diagnostic_negative_controls_v1_1.py":
        "ef7a7d8c5b7d9699fa375b2bcfccc3c482ac9e4d1b4ce9a1c3807142100a6950",
    "scripts/analysis/build_phase36_final_probability_authority_diagnostic_v1_1.py":
        "498c7460c3e588317f3741da8fbcbf4886a660aec5ba0aa880422f8d7f6200f8",
    "reports/audits/phase36_final_probability_authority_diagnostic_v1_1_governance_reconciliation_v1_0.json":
        "124327dca073afa440e187aa1999c4f463fb97a1fe62e30ce19b6bcfa8b966f4",
    "scripts/analysis/build_phase36_final_probability_authority_diagnostic_v1_1_governance_reconciliation_v1_0.py":
        "9518a0ceef65bb3a4ce97d4e2fa6fe89f881b03674e49b1ea593e429ec5d9309",
    "reports/audits/phase36_final_probability_authority_diagnostic_contract_v1_1.json":
        "84398af09ad814c8d1d326bac20aaee9ee1400e09d1a18baf12b8448b543967c",
    "reports/audits/phase36_final_probability_authority_diagnostic_source_freeze_v1_1.json":
        "a93a9aaa7e22b96d42c80a64d08f2576fcdfcf08e947643c7272d593ab967b0b",
    "reports/audits/phase36_final_probability_authority_diagnostic_preflight_v1_1.json":
        "0bfc783b342a5c9f9e1ae7473240c80b442a27e85ed4a0b61af3c80652c42819",
    "reports/audits/phase36_final_probability_authority_diagnostic_negative_controls_v1_1.json":
        "a8ff8347fc0a54ebfb4ffefadfe8d94163f8026186c4c51224dee24f2aa7fb34",
    "reports/audits/phase36_final_probability_authority_diagnostic_eligibility_v1_1.json":
        "bd2fd129f59848faaaed9fa7c400eca0ce693d2d3cb25beaa18d8c0488210aac",
    "reports/audits/phase36_final_probability_authority_diagnostic_no_execution_audit_v1_1.json":
        "6394c88552ef9a1ebd57de2e023466a256596f09affd20582b95db8b119e2a29",
    "reports/audits/phase36_final_probability_authority_diagnostic_v1_0_to_v1_1_diff.json":
        "3c88a2173854774f9d8bba242ce84d83d4984c66eb4f34f5ec7b26cfbfc37a17",
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

# Consumed-evidence binding (v1.2 clean-eq attempt + D51 line).
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

# ---- v1.1 CONSUMED-state binding (D56) ------------------------------------ #
V1_1_START_PATH = "reports/audits/phase36_final_probability_authority_diagnostic_start_v1_1.json"
V1_1_START_SHA = "0bfb452ef81e6e0c8880d9b333abcb6514dff7dbb3a37476da3242beeab73aec"
V1_1_FAILURE_PATH = "reports/audits/phase36_final_probability_authority_diagnostic_failure_v1_1.json"
V1_1_FAILURE_SHA = "9f1b38431228ec584150da37501199ea580b26339be6d8e20a2fcba72b5cd960"
V1_1_RESULT_PATH = "reports/audits/phase36_final_probability_authority_diagnostic_result_v1_1.json"
D56_FAILURE_ADJUDICATION_PATH = (
    "reports/audits/phase36_final_probability_authority_diagnostic_v1_1_failure_adjudication_v1_0.json")
D56_FAILURE_ADJUDICATION_SHA = "b796cc8d49df32513d2c6a4c5700a253d66a49e171def1772e1617ff4855fc80"
REQUIRED_V1_1_FAILURE_PREDICATES = {
    "termination_kind": "EXCEPTION",
    "exception_type": "TypeError",
    "exception_message": "'module' object is not subscriptable",
    "failing_stage": "run_diagnostic",
    "marker_consumed": True,
    "VAL_GT_READ": 0,
    "final_authority_computed": False,
    "result_write_attempted": False,
}
REQUIRED_D56_CLASSIFICATION = "DIAGNOSTIC_FROZEN_MODULE_SUBSCRIPT_MISMATCH"

T_ANCHOR_FAILED = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_2_LAUNCH_FAIL_CLOSED__ANCHOR_VERIFICATION_FAILED__NO_ATTEMPT_CONSUMED"
T_WRONG_INTERPRETER = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_2_LAUNCH_FAIL_CLOSED__WRONG_INTERPRETER__NO_ATTEMPT_CONSUMED"
T_CUDA_UNAVAILABLE = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_2_LAUNCH_FAIL_CLOSED__CUDA_READINESS_FAILED__NO_ATTEMPT_CONSUMED"
T_FOREIGN_TOKEN_PRESENT = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_2_FAIL_CLOSED__FOREIGN_V1_14_LAUNCH_AUTHORITY_PRESENT__NO_ATTEMPT_CONSUMED"
T_PROVENANCE_FAILED = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_2_LAUNCH_FAIL_CLOSED__PRIOR_FAILURE_PROVENANCE_NOT_BOUND__NO_ATTEMPT_CONSUMED"
T_CONSUMED_BIND_FAILED = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_2_LAUNCH_FAIL_CLOSED__CONSUMED_EVIDENCE_NOT_BOUND__NO_ATTEMPT_CONSUMED"
T_V1_0_PRESERVATION_FAILED = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_2_LAUNCH_FAIL_CLOSED__V1_0_SOURCE_NOT_PRESERVED__NO_ATTEMPT_CONSUMED"
T_TRANSITIVE_FAILED = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_2_FAIL_CLOSED__TRANSITIVE_INTEGRITY_FAILED__NO_ATTEMPT_CONSUMED"
T_AUTHORITY_EXACT_FAILED = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_2_FAIL_CLOSED__SOURCE_MANIFEST_TRANSITIVE_AUTHORITY_MISMATCH__NO_ATTEMPT_CONSUMED"
T_FINAL_AUTHORITY_FAILED = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_2_FAIL_CLOSED__FINAL_AUTHORITY_PRECONSUMPTION_GATE_FAILED__NO_ATTEMPT_CONSUMED"
T_V1_1_CONSUMED_FAILED = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_2_FAIL_CLOSED__V1_1_CONSUMED_STATE_NOT_BOUND__NO_ATTEMPT_CONSUMED"
T_VERIFY_ONLY_OK = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_2_LAUNCH_READINESS_VERIFIED__DISPATCH_SUPPRESSED_BY_VERIFY_ONLY"


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


def check_v1_1_preserved(root: Path | None = None) -> dict:
    base = Path(root) if root is not None else ROOT
    out = {"ok": True, "items": {}}
    for rel, exp in V1_1_PINS.items():
        p = base / rel
        obs = sha(p) if p.exists() else None
        m = (obs == exp)
        out["items"][rel] = {"present": p.exists(), "expected": exp, "observed": obs, "match": bool(m)}
        if not m:
            out["ok"] = False
    return out


def check_v1_1_consumed_state(root: Path | None = None) -> dict:
    """D56 provenance gate: bind v1.1 consumed evidence + required failure predicates."""
    base = Path(root) if root is not None else ROOT
    out = {"ok": True, "items": {}, "predicates": {}, "predicates_match": {}, "result_absent": None}
    for name, rel, exp in (
        ("v1_1_start", V1_1_START_PATH, V1_1_START_SHA),
        ("v1_1_failure", V1_1_FAILURE_PATH, V1_1_FAILURE_SHA),
        ("d56_failure_adjudication", D56_FAILURE_ADJUDICATION_PATH, D56_FAILURE_ADJUDICATION_SHA),
    ):
        p = base / rel
        obs = sha(p) if p.exists() else None
        m = (obs == exp)
        out["items"][name] = {"path": rel, "present": p.exists(), "expected": exp,
                              "observed": obs, "match": bool(m)}
        if not m:
            out["ok"] = False
    out["result_absent"] = not (base / V1_1_RESULT_PATH).exists()
    if not out["result_absent"]:
        out["ok"] = False

    fp = base / V1_1_FAILURE_PATH
    if fp.exists():
        try:
            fj = json.loads(fp.read_text(encoding="utf-8"))
            pred = {k: fj.get(k) for k in REQUIRED_V1_1_FAILURE_PREDICATES}
            out["predicates"] = pred
            out["predicates_match"] = {k: bool(pred.get(k) == v)
                                       for k, v in REQUIRED_V1_1_FAILURE_PREDICATES.items()}
        except Exception as exc:  # noqa: BLE001
            out["predicates"] = {"parse_error": type(exc).__name__}
            out["predicates_match"] = {}
            out["ok"] = False
    if not (out["predicates_match"] and all(out["predicates_match"].values())):
        out["ok"] = False

    adj = base / D56_FAILURE_ADJUDICATION_PATH
    if adj.exists():
        try:
            aj = json.loads(adj.read_text(encoding="utf-8"))
            out["d56_classification"] = aj.get("d56_classification")
            out["d56_root_cause_established"] = aj.get("d56_root_cause_established")
            out["d56_adjudication_v1_1_state"] = aj.get("v1_1_state")
        except Exception as exc:  # noqa: BLE001
            out["d56_parse_error"] = type(exc).__name__
            out["ok"] = False
    if out.get("d56_classification") != REQUIRED_D56_CLASSIFICATION:
        out["ok"] = False
    if out.get("d56_root_cause_established") is not True:
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
    """Verify the exact Phase27 FINAL float16 prediction authority BEFORE consumption."""
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
        "torch_load": False, "checkpoint_deserialization": False,
        "model_construction": False, "val_image_read": False, "gt_read": False,
    }

    if not auth_p.exists():
        out["reason"] = "FINAL_AUTHORITY_ABSENT"
        return out

    out["final_authority_sha256"] = sha(auth_p)
    if out["final_authority_sha256"] != PHASE27_FINAL_PROB_AUTHORITY_SHA:
        out["reason"] = "FINAL_AUTHORITY_SHA_MISMATCH"
        return out

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

    if csv_ids != canonical_ids:
        out["reason"] = "FINAL_AUTHORITY_SAMPLE_ORDER_MISMATCH"
        out["sample_order_detail"] = "CSV_SAMPLE_ID_ORDER != CANONICAL_(dataset,sample_id)_ORDER"
        return out

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


def _d56_subscript_sites(diag_path: Path | None = None) -> list:
    """D56 AST control: return every ``_FROZEN_MOD[...]`` subscript site.

    A non-empty result means the frozen-module SUBSCRIPT defect is present.
    v1.2 MUST return an empty list (attribute access only).
    """
    p = Path(diag_path) if diag_path is not None else DIAGNOSTIC_SELF
    tree = ast.parse(p.read_text(encoding="utf-8"))
    sites = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Subscript) and isinstance(n.value, ast.Name) \
                and n.value.id == "_FROZEN_MOD":
            sl = n.slice
            key = (sl.value if isinstance(sl, ast.Constant) else "<expr>")
            sites.append({"line": n.lineno, "key": key})
    return sites


def _d56_attribute_sites(diag_path: Path | None = None) -> list:
    """D56 AST control: return every ``_FROZEN_MOD.<attr>`` attribute site."""
    p = Path(diag_path) if diag_path is not None else DIAGNOSTIC_SELF
    tree = ast.parse(p.read_text(encoding="utf-8"))
    sites = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) \
                and n.value.id == "_FROZEN_MOD":
            sites.append({"line": n.lineno, "attr": n.attr})
    return sites


def check_d56_module_interface(diag_path: Path | None = None) -> dict:
    """D56 launcher-side control (no model, no CUDA, no IO)."""
    sites = _d56_subscript_sites(diag_path)
    attrs = _d56_attribute_sites(diag_path)
    attr_names = {a["attr"] for a in attrs}
    return {
        "d56_subscript_sites": sites,
        "d56_subscript_free": not sites,
        "d56_load_clean_image_tensor_attribute_access": "_load_clean_image_tensor" in attr_names,
        "d56_canonical_learned_core_attribute_access": "canonical_learned_core" in attr_names,
        "ok": bool(not sites
                   and "_load_clean_image_tensor" in attr_names
                   and "canonical_learned_core" in attr_names),
    }


def _emit(terminal: str, **extra) -> int:
    payload = {"launcher": "launch_phase36_final_probability_authority_diagnostic_v1_2",
               "terminal": terminal}
    payload.update(extra)
    print(json.dumps(payload, indent=1))
    return 2


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify-only", action="store_true",
                    help="verify all gates incl. the D52 final-authority and the v1.1 "
                         "consumed-state gates, and exit WITHOUT dispatching.")
    a = ap.parse_args()

    auth = verify_authority()
    if not auth["authorized"]:
        return _emit(T_ANCHOR_FAILED, authorized=False, authority=auth)

    interp = check_interpreter_identity()
    if not interp["ok"]:
        return _emit(T_WRONG_INTERPRETER, authorized=False, interpreter=interp, authority=auth,
                     hint=r"Invoke the canonical interpreter explicitly, e.g. "
                          r"D:\Softfors\jup\.venv\Scripts\python.exe "
                          r"scripts\analysis\launch_phase36_final_probability_authority_diagnostic_v1_2.py --verify-only")

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

    preserved_v11 = check_v1_1_preserved()
    if not preserved_v11["ok"]:
        return _emit(T_V1_0_PRESERVATION_FAILED, authorized=False, v1_1_preservation=preserved_v11,
                     v1_0_preservation=preserved, consumed_evidence=consumed, provenance=prov,
                     foreign_gate=foreign, interpreter=interp, cuda_readiness=cuda, authority=auth)

    ti = check_transitive_integrity()
    if not ti["ok"]:
        term = (T_AUTHORITY_EXACT_FAILED
                if ti.get("reason") == "SOURCE_MANIFEST_TRANSITIVE_AUTHORITY_MISMATCH"
                else T_TRANSITIVE_FAILED)
        return _emit(term, authorized=False, transitive_integrity=ti, v1_0_preservation=preserved,
                     v1_1_preservation=preserved_v11, consumed_evidence=consumed, provenance=prov,
                     foreign_gate=foreign, interpreter=interp, cuda_readiness=cuda, authority=auth)

    # (10) D52 — Phase27 FINAL authority pre-consumption gate
    fa = check_final_authority_preconsumption()
    if not fa["final_authority_preconsumption_pass"]:
        return _emit(T_FINAL_AUTHORITY_FAILED, authorized=False, final_authority=fa,
                     transitive_integrity=ti, v1_0_preservation=preserved,
                     v1_1_preservation=preserved_v11, consumed_evidence=consumed,
                     provenance=prov, foreign_gate=foreign, interpreter=interp,
                     cuda_readiness=cuda, authority=auth)

    # (11) v1.1 CONSUMED-state binding gate (D56)
    v11 = check_v1_1_consumed_state()
    if not v11["ok"]:
        return _emit(T_V1_1_CONSUMED_FAILED, authorized=False, v1_1_consumed_state=v11,
                     final_authority=fa, transitive_integrity=ti, v1_0_preservation=preserved,
                     v1_1_preservation=preserved_v11, consumed_evidence=consumed,
                     provenance=prov, foreign_gate=foreign, interpreter=interp,
                     cuda_readiness=cuda, authority=auth)

    # (11b) D56 static module-interface control (attribute access, not subscript)
    d56 = check_d56_module_interface()
    if not d56["ok"]:
        return _emit(T_ANCHOR_FAILED, authorized=False, d56_module_interface=d56,
                     v1_1_consumed_state=v11, final_authority=fa, transitive_integrity=ti,
                     v1_0_preservation=preserved, v1_1_preservation=preserved_v11,
                     consumed_evidence=consumed, provenance=prov, foreign_gate=foreign,
                     interpreter=interp, cuda_readiness=cuda, authority=auth)

    # (12) verify-only STOP (non-consuming)
    if a.verify_only:
        print(json.dumps({
            "launcher": "launch_phase36_final_probability_authority_diagnostic_v1_2",
            "authorized": True,
            "anchor_pass": True,
            "interpreter_pass": True,
            "cuda_readiness_pass": True,
            "foreign_v1_14_token_absent_pass": True,
            "prior_failure_provenance_pass": True,
            "consumed_evidence_binding_pass": True,
            "v1_0_preservation_pass": True,
            "v1_1_preservation_pass": True,
            "transitive_integrity_pass": True,
            "source_manifest_transitive_authority_exact_match": ti["source_manifest_transitive_authority_exact_match"],
            "n_dependencies_verified": ti["n_dependencies"],
            "n_checkpoints_verified": ti["n_checkpoints"],
            "final_authority_preconsumption_pass": fa["final_authority_preconsumption_pass"],
            "final_authority_sha256": fa["final_authority_sha256"],
            "final_authority_shape": fa["final_authority_shape"],
            "final_authority_dtype": fa["final_authority_dtype"],
            "final_authority_sample_order_pass": fa["final_authority_sample_order_pass"],
            "v1_1_consumed_state_binding_pass": v11["ok"],
            "v1_1_result_absent": v11["result_absent"],
            "d56_classification_bound": v11.get("d56_classification"),
            "d56_module_interface_pass": d56["ok"],
            "d56_subscript_free": d56["d56_subscript_free"],
            "d56_load_clean_image_tensor_attribute_access":
                d56["d56_load_clean_image_tensor_attribute_access"],
            "d56_canonical_learned_core_attribute_access":
                d56["d56_canonical_learned_core_attribute_access"],
            "terminal": T_VERIFY_ONLY_OK,
            "interpreter": interp,
            "cuda_readiness": cuda,
            "foreign_gate": foreign,
            "consumed_evidence_predicates": consumed["predicates"],
            "one_shot_gate_set": os.environ.get(ONE_SHOT_ENV) == "1",
        }, indent=1))
        return 0

    # (13) the ONLY write of the v1.2 launch-authority token (after the verify STOP)
    os.environ[LAUNCH_AUTHORITY_TOKEN] = "1"

    # (14) dispatch the diagnostic module ONLY
    import importlib.util
    spec = importlib.util.spec_from_file_location("phase36_final_prob_authority_diag_v1_2",
                                                  DIAGNOSTIC_SELF)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return int(mod.main())


if __name__ == "__main__":
    raise SystemExit(main())
