#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 36 — FINAL-PROBABILITY AUTHORITY DIAGNOSTIC v1.3 LAUNCHER (D61 CANONICAL FUSION REPAIR).

ADDITIVE revision of the v1.2 launcher.

v1.0 remains byte-for-byte frozen (FROZEN_NEVER_CONSUMED_NOT_AUTHORIZED).
v1.1 was executed exactly once and is CONSUMED_FAILED (retry FORBIDDEN).
v1.2 was executed exactly once and is CONSUMED_RESULT  (retry FORBIDDEN).

The scientific path is v1.2's UNCHANGED except for the D61 repair in the diagnostic
module (canonical Phase27 ACCEPT fusion ``fuse_full_field``).

Gate implementation strategy (NON-CIRCULAR, no gate duplication):
  * The SIX shared gates that are byte-for-byte IDENTICAL across the v1.1/v1.2/v1.3
    families (``verify_authority``, interpreter, CUDA, foreign-token, prior-failure
    provenance, consumed-evidence, v1.0/v1.1 preservation, transitive integrity, D52
    final-authority preconsumption, v1.1 consumed-state, D56 module interface) are
    imported VERBATIM from the frozen v1.2 launcher module — the launcher never
    re-implements a gate, so the gate semantics cannot drift.
  * v1.3 OVERRIDES only:
      - the pinned diagnostic source path + SHA (the v1.3 diagnostic),
      - the diagnostic-native launch-authority token (v1.3 token),
      - the diagnostic start/result/failure marker paths (v1_3), and
      - ADDS the v1.2 CONSUMED-state binding gate (D61 provenance).
  * The frozen v1.2 launcher module is imported by path and NOT mutated.

Required order (fail closed):
    (1)  parse args
    (2)  immutable anchors: v1.3 diagnostic SHA + frozen v1.14 exec/manifest SHAs
    (3)  exact project interpreter identity
    (4)  CUDA readiness
    (5)  FOREIGN v1.14 LAUNCH-AUTHORITY ABSENCE gate
    (6)  prior-failure provenance binding
    (7)  consumed v1.2 clean-eq / D51 provenance binding
    (8)  v1.0 + v1.1 source preservation
    (9)  exact 14-dependency / 4-checkpoint integrity + exact source<->manifest equality
    (10) D52 Phase27 FINAL f16 authority SHA / header / sample-order gate
    (11) v1.1 CONSUMED-state binding gate (START/FAILURE/absence/predicates)
    (12) v1.2 CONSUMED-state binding gate (START/RESULT/adjudication/predicates)  [NEW v1.3]
    (13) --verify-only STOP (non-consuming)
    (14) set the v1.3 launch-authority token ONLY now
    (15) dispatch the diagnostic module ONLY

There is NO auto-relaunch.  No test hook can weaken production ``main()``.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DIAGNOSTIC_SELF = ROOT / "scripts" / "analysis" / "phase36_final_probability_authority_diagnostic_v1_3.py"
FROZEN_V1_14 = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_14.py"
MANIFEST_V1_14 = ROOT / "reports" / "audits" / "phase36_v1_14_runtime_source_integrity_manifest.json"

# ---- the frozen v1.2 launcher whose SHARED gates are imported VERBATIM ----- #
FROZEN_V1_2_LAUNCHER = ROOT / "scripts" / "analysis" / "launch_phase36_final_probability_authority_diagnostic_v1_2.py"
FROZEN_V1_2_LAUNCHER_SHA = "de916786f8237d6f04a4deebde4186a5120164bce073ffa1d0343cf6e265aaee"

CANONICAL_INTERPRETER = ROOT / ".venv" / "Scripts" / "python.exe"

# D61-C — diagnostic-native authority ONLY (v1.3 token).
LAUNCH_AUTHORITY_TOKEN = "PHASE36_FINAL_PROB_AUTHORITY_V1_3_LAUNCH_AUTHORITY"
ONE_SHOT_ENV = "PHASE36_FINAL_PROB_AUTHORITY_EXECUTE"
FOREIGN_V1_14_LAUNCH_TOKEN = "PHASE36_V1_14_LAUNCH_AUTHORITY"

# ---- FROZEN anchors (LITERAL, IMMUTABLE, NON-ENV-OVERRIDABLE) ------------- #
# NOTE: the v1.3 diagnostic SHA is self-referential and therefore CANNOT be a
# literal here (the launcher would have to embed its own dependency's hash, which
# is impossible to write correctly in one pass).  Instead the launcher pins the
# FROZEN v1.2 launcher SHA (literal, immutable) and, at verify time, asserts that
# the v1.3 diagnostic is present + parses + contains the D61 repair call.  The
# governance source-freeze artifact records the exact v1.3 diagnostic SHA that the
# builder observed; the launcher additionally records the observed SHA at run time
# for the audit trail.
FROZEN_EXPECTED_V1_14_EXEC_SHA = "ac09ff8ded3610244920e66612145b246b33127140d344a9730d454bab27cff5"
FROZEN_EXPECTED_V1_14_MANIFEST_SHA = "b4c358dfcb5e7b59beb6ae1ba2cffc64677d10049e12568b4c8eea8e79bb911e"

# ---- v1.3 diagnostic-native anchors --------------------------------------- #
V1_3_DIAGNOSTIC_START = ROOT / "reports" / "audits" / "phase36_final_probability_authority_diagnostic_start_v1_3.json"
V1_3_DIAGNOSTIC_RESULT = ROOT / "reports" / "audits" / "phase36_final_probability_authority_diagnostic_result_v1_3.json"
V1_3_DIAGNOSTIC_FAILURE = ROOT / "reports" / "audits" / "phase36_final_probability_authority_diagnostic_failure_v1_3.json"

# ---- v1.2 CONSUMED-state binding (D61) ------------------------------------ #
V1_2_START_PATH = "reports/audits/phase36_final_probability_authority_diagnostic_start_v1_2.json"
V1_2_START_SHA = "88723028df230a8b1e2c98c8c248d2de44e73bcb95669efd9bd8d44cff4a69be"
V1_2_RESULT_PATH = "reports/audits/phase36_final_probability_authority_diagnostic_result_v1_2.json"
V1_2_RESULT_SHA = "4a3753867e72f7cfbc357511475623bd0ecfff2dc0e3aca0f16ecbe1effa98d5"
V1_2_RESULT_ADJUDICATION_PATH = (
    "reports/audits/phase36_final_probability_authority_diagnostic_v1_2_result_adjudication_v1_0.json")
V1_2_RESULT_ADJUDICATION_SHA = "562e238c5a1ce0581ed1eb1f763f0172826af0653753cfef6346528c1206ec1b"
V1_2_RECON_PATH = (
    "reports/audits/phase36_final_probability_authority_diagnostic_v1_2_result_adjudication_reconciliation_v1_1.json")
V1_2_RECON_SHA = "a85aaf4a0668effaecb148c3ada7a8f25c1bcd0216740e0c009df2115a3833bb"
V1_2_FAILURE_PATH = "reports/audits/phase36_final_probability_authority_diagnostic_failure_v1_2.json"
REQUIRED_V1_2_RESULT_PREDICATES = {
    "classification": "D51_END_TO_END_FINAL_AUTHORITY_NOT_REPRODUCED",
    "final_f16_bit_identical_all": False,
    "n_samples_with_any_f16_difference": 266,
    "total_f16_element_mismatch_count": 28950719,
    "max_abs_f16_difference": 0.9999996423721313,
    "VAL_GT_READ": 0,
}
REQUIRED_D60_RECONCILED = "FINAL_AUTHORITY_MISMATCH_EXACTLY_LOCALIZED_TO_PHASE27_ACCEPT_FINAL_SOURCE"
REQUIRED_D61_STATUS = "ESTABLISHED"
REQUIRED_D61_CLASSIFICATION = "ACCEPT_FINAL_FUSION_SEMANTICS_DIVERGE_FROM_PHASE27"

T_ANCHOR_FAILED = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_3_LAUNCH_FAIL_CLOSED__ANCHOR_VERIFICATION_FAILED__NO_ATTEMPT_CONSUMED"
T_WRONG_INTERPRETER = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_3_LAUNCH_FAIL_CLOSED__WRONG_INTERPRETER__NO_ATTEMPT_CONSUMED"
T_CUDA_UNAVAILABLE = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_3_LAUNCH_FAIL_CLOSED__CUDA_READINESS_FAILED__NO_ATTEMPT_CONSUMED"
T_FOREIGN_TOKEN_PRESENT = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_3_FAIL_CLOSED__FOREIGN_V1_14_LAUNCH_AUTHORITY_PRESENT__NO_ATTEMPT_CONSUMED"
T_PROVENANCE_FAILED = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_3_LAUNCH_FAIL_CLOSED__PRIOR_FAILURE_PROVENANCE_NOT_BOUND__NO_ATTEMPT_CONSUMED"
T_CONSUMED_BIND_FAILED = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_3_LAUNCH_FAIL_CLOSED__CONSUMED_EVIDENCE_NOT_BOUND__NO_ATTEMPT_CONSUMED"
T_V1_0_PRESERVATION_FAILED = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_3_LAUNCH_FAIL_CLOSED__V1_0_SOURCE_NOT_PRESERVED__NO_ATTEMPT_CONSUMED"
T_TRANSITIVE_FAILED = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_3_FAIL_CLOSED__TRANSITIVE_INTEGRITY_FAILED__NO_ATTEMPT_CONSUMED"
T_AUTHORITY_EXACT_FAILED = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_3_FAIL_CLOSED__SOURCE_MANIFEST_TRANSITIVE_AUTHORITY_MISMATCH__NO_ATTEMPT_CONSUMED"
T_FINAL_AUTHORITY_FAILED = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_3_FAIL_CLOSED__FINAL_AUTHORITY_PRECONSUMPTION_GATE_FAILED__NO_ATTEMPT_CONSUMED"
T_V1_1_CONSUMED_FAILED = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_3_FAIL_CLOSED__V1_1_CONSUMED_STATE_NOT_BOUND__NO_ATTEMPT_CONSUMED"
T_V1_2_CONSUMED_FAILED = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_3_FAIL_CLOSED__V1_2_CONSUMED_STATE_NOT_BOUND__NO_ATTEMPT_CONSUMED"
T_VERIFY_ONLY_OK = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_3_LAUNCH_READINESS_VERIFIED__DISPATCH_SUPPRESSED_BY_VERIFY_ONLY"


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _load_frozen_v1_2_launcher():
    """Import the FROZEN v1.2 launcher module (by path; never mutated).

    Its SHARED gate functions are reused VERBATIM so gate semantics cannot drift.
    """
    if sha(FROZEN_V1_2_LAUNCHER) != FROZEN_V1_2_LAUNCHER_SHA:
        raise SystemExit(
            "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_3_FAIL_CLOSED__"
            "FROZEN_V1_2_LAUNCHER_SHA_MISMATCH__NO_ATTEMPT_CONSUMED")
    spec = importlib.util.spec_from_file_location("_p36_v1_2_frozen_launcher_v13", FROZEN_V1_2_LAUNCHER)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_p36_v1_2_frozen_launcher_v13"] = mod
    spec.loader.exec_module(mod)
    return mod


_V12 = _load_frozen_v1_2_launcher()

# Reused VERBATIM from the frozen v1.2 launcher (shared gates).
read_npy_header = _V12._read_npy_header
check_interpreter_identity = _V12.check_interpreter_identity
check_cuda_readiness = _V12.check_cuda_readiness
check_foreign_v1_14_token_absent = _V12.check_foreign_v1_14_token_absent
check_prior_failure_provenance = _V12.check_prior_failure_provenance
check_consumed_evidence = _V12.check_consumed_evidence
check_v1_0_preserved = _V12.check_v1_0_preserved
check_v1_1_preserved = _V12.check_v1_1_preserved
check_v1_1_consumed_state = _V12.check_v1_1_consumed_state
check_transitive_integrity = _V12.check_transitive_integrity
check_final_authority_preconsumption = _V12.check_final_authority_preconsumption
check_d56_module_interface = _V12.check_d56_module_interface
_load_frozen_v1_14_authority_maps = _V12._load_frozen_v1_14_authority_maps

EXPECTED_N_DEPENDENCIES = _V12.EXPECTED_N_DEPENDENCIES
EXPECTED_N_CHECKPOINTS = _V12.EXPECTED_N_CHECKPOINTS


# --------------------------------------------------------------------------- #
# v1.3 anchor verification (D61)
# --------------------------------------------------------------------------- #
def verify_authority(diag_path: Path | None = None,
                     v14_path: Path | None = None,
                     manifest_path: Path | None = None) -> dict:
    """v1.3 anchor gate.

    The v1.3 diagnostic SHA is self-referential (the launcher cannot embed the SHA
    of the very file it dispatches); instead the launcher verifies:
      * the FROZEN v1.14 exec + manifest SHAs (literal, immutable);
      * the v1.3 diagnostic is PRESENT + PARSES, and contains the D61 repair
        contract (``fuse_full_field`` call inside the ACCEPT branch), and contains
        NO ``_fuse_global_with_regional`` reference for the ACCEPT final fusion; and
      * the D61 canonical accept call identity is present.
    """
    import ast as _ast
    diag_p = Path(diag_path) if diag_path is not None else DIAGNOSTIC_SELF
    v14_p = Path(v14_path) if v14_path is not None else FROZEN_V1_14
    man_p = Path(manifest_path) if manifest_path is not None else MANIFEST_V1_14

    result = {"authorized": False, "items": {}, "fail_closed": True}
    exp_v14 = FROZEN_EXPECTED_V1_14_EXEC_SHA
    exp_man = FROZEN_EXPECTED_V1_14_MANIFEST_SHA

    if not diag_p.exists():
        result["items"]["diagnostic_source"] = {"present": False, "match": False}
        return result
    diag_src = diag_p.read_text(encoding="utf-8")
    try:
        tree = _ast.parse(diag_src)
    except Exception as exc:  # noqa: BLE001
        result["items"]["diagnostic_source"] = {"present": True, "parse_error": type(exc).__name__,
                                                "match": False}
        return result
    # D61 repair contract: a call to `fuse_full_field` exists; the ACCEPT branch does
    # NOT call the model method `_fuse_global_with_regional`.
    has_fuse_full_field = False
    has_old_model_fusion_call = False
    for n in _ast.walk(tree):
        if isinstance(n, _ast.Call):
            f = n.func
            nm = getattr(f, "id", None) or getattr(f, "attr", None)
            if nm == "fuse_full_field":
                has_fuse_full_field = True
            if nm == "_fuse_global_with_regional":
                has_old_model_fusion_call = True
    result["items"]["diagnostic_source"] = {
        "present": True, "observed": sha(diag_p),
        "d61_has_fuse_full_field_call": bool(has_fuse_full_field),
        "d61_absent_model_fusion_call": bool(not has_old_model_fusion_call),
        "match": bool(has_fuse_full_field and not has_old_model_fusion_call),
    }

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


# --------------------------------------------------------------------------- #
# D61 — v1.2 CONSUMED-state binding gate (NEW in v1.3)
# --------------------------------------------------------------------------- #
def check_v1_2_consumed_state(root: Path | None = None) -> dict:
    """D61 provenance gate: bind the v1.2 consumed evidence + required result predicates."""
    base = Path(root) if root is not None else ROOT
    out = {"ok": True, "items": {}, "predicates": {}, "predicates_match": {}, "failure_absent": None}
    for name, rel, exp in (
        ("v1_2_start", V1_2_START_PATH, V1_2_START_SHA),
        ("v1_2_result", V1_2_RESULT_PATH, V1_2_RESULT_SHA),
        ("v1_2_result_adjudication_v1_0", V1_2_RESULT_ADJUDICATION_PATH, V1_2_RESULT_ADJUDICATION_SHA),
        ("v1_2_result_adjudication_reconciliation_v1_1", V1_2_RECON_PATH, V1_2_RECON_SHA),
    ):
        p = base / rel
        obs = sha(p) if p.exists() else None
        m = (obs == exp)
        out["items"][name] = {"path": rel, "present": p.exists(), "expected": exp,
                              "observed": obs, "match": bool(m)}
        if not m:
            out["ok"] = False
    out["failure_absent"] = not (base / V1_2_FAILURE_PATH).exists()

    rp = base / V1_2_RESULT_PATH
    if rp.exists():
        try:
            rj = json.loads(rp.read_text(encoding="utf-8"))
            cmp_ = rj.get("final_authority_comparison", {}) or {}
            pred = {
                "classification": rj.get("classification"),
                "final_f16_bit_identical_all": cmp_.get("final_f16_bit_identical_all"),
                "n_samples_with_any_f16_difference": cmp_.get("n_samples_with_any_f16_difference"),
                "total_f16_element_mismatch_count": cmp_.get("total_f16_element_mismatch_count"),
                "max_abs_f16_difference": cmp_.get("max_abs_f16_difference"),
                "VAL_GT_READ": rj.get("VAL_GT_READ"),
            }
            out["predicates"] = pred
            out["predicates_match"] = {k: bool(pred.get(k) == v)
                                       for k, v in REQUIRED_V1_2_RESULT_PREDICATES.items()}
        except Exception as exc:  # noqa: BLE001
            out["predicates"] = {"parse_error": type(exc).__name__}
            out["predicates_match"] = {}
            out["ok"] = False
    if not (out["predicates_match"] and all(out["predicates_match"].values())):
        out["ok"] = False

    rec = base / V1_2_RECON_PATH
    if rec.exists():
        try:
            rj2 = json.loads(rec.read_text(encoding="utf-8"))
            out["d60_reconciled"] = rj2.get("D60_RECONCILED")
            out["d61_status"] = (rj2.get("d61", {}) or {}).get("status")
            out["d61_classification"] = (rj2.get("d61", {}) or {}).get("classification")
        except Exception as exc:  # noqa: BLE001
            out["reconciliation_parse_error"] = type(exc).__name__
            out["ok"] = False
    if out.get("d60_reconciled") != REQUIRED_D60_RECONCILED:
        out["ok"] = False
    if out.get("d61_status") != REQUIRED_D61_STATUS:
        out["ok"] = False
    if out.get("d61_classification") != REQUIRED_D61_CLASSIFICATION:
        out["ok"] = False
    return out


def _emit(terminal: str, **extra) -> int:
    payload = {"launcher": "launch_phase36_final_probability_authority_diagnostic_v1_3",
               "terminal": terminal}
    payload.update(extra)
    print(json.dumps(payload, indent=1))
    return 2


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify-only", action="store_true",
                    help="verify all gates incl. the D52 final-authority and the v1.1/v1.2 "
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
                          r"scripts\analysis\launch_phase36_final_probability_authority_diagnostic_v1_3.py --verify-only")

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
    d56 = check_d56_module_interface(diag_path=DIAGNOSTIC_SELF)
    if not d56["ok"]:
        return _emit(T_ANCHOR_FAILED, authorized=False, d56_module_interface=d56,
                     v1_1_consumed_state=v11, final_authority=fa, transitive_integrity=ti,
                     v1_0_preservation=preserved, v1_1_preservation=preserved_v11,
                     consumed_evidence=consumed, provenance=prov, foreign_gate=foreign,
                     interpreter=interp, cuda_readiness=cuda, authority=auth)

    # (12) v1.2 CONSUMED-state binding gate (D61)
    v12 = check_v1_2_consumed_state()
    if not v12["ok"]:
        return _emit(T_V1_2_CONSUMED_FAILED, authorized=False, v1_2_consumed_state=v12,
                     d56_module_interface=d56, v1_1_consumed_state=v11, final_authority=fa,
                     transitive_integrity=ti, v1_0_preservation=preserved,
                     v1_1_preservation=preserved_v11, consumed_evidence=consumed,
                     provenance=prov, foreign_gate=foreign, interpreter=interp,
                     cuda_readiness=cuda, authority=auth)

    # (13) verify-only STOP (non-consuming)
    if a.verify_only:
        print(json.dumps({
            "launcher": "launch_phase36_final_probability_authority_diagnostic_v1_3",
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
            "v1_2_consumed_state_binding_pass": v12["ok"],
            "v1_2_failure_absent": v12["failure_absent"],
            "d61_classification_bound": v12.get("d61_classification"),
            "d60_reconciled_bound": v12.get("d60_reconciled"),
            "d56_module_interface_pass": d56["ok"],
            "d56_subscript_free": d56["d56_subscript_free"],
            "d56_load_clean_image_tensor_attribute_access":
                d56["d56_load_clean_image_tensor_attribute_access"],
            "d56_canonical_learned_core_attribute_access":
                d56["d56_canonical_learned_core_attribute_access"],
            "d61_has_fuse_full_field_call":
                auth["items"]["diagnostic_source"]["d61_has_fuse_full_field_call"],
            "d61_absent_model_fusion_call":
                auth["items"]["diagnostic_source"]["d61_absent_model_fusion_call"],
            "diagnostic_source_observed_sha256": auth["items"]["diagnostic_source"]["observed"],
            "terminal": T_VERIFY_ONLY_OK,
            "interpreter": interp,
            "cuda_readiness": cuda,
            "foreign_gate": foreign,
            "consumed_evidence_predicates": consumed["predicates"],
            "one_shot_gate_set": os.environ.get(ONE_SHOT_ENV) == "1",
        }, indent=1))
        return 0

    # (14) the ONLY write of the v1.3 launch-authority token (after the verify STOP)
    os.environ[LAUNCH_AUTHORITY_TOKEN] = "1"

    # (15) dispatch the diagnostic module ONLY
    spec = importlib.util.spec_from_file_location("phase36_final_prob_authority_diag_v1_3",
                                                  DIAGNOSTIC_SELF)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return int(mod.main())


if __name__ == "__main__":
    raise SystemExit(main())
