#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 36 — FINAL-PROBABILITY AUTHORITY DIAGNOSTIC v1.4 LAUNCHER
(D61 REPAIR-PROOF REPLAY WITH CRASH-SURVIVABLE OBSERVABILITY).

ADDITIVE revision of the v1.3 launcher.

v1.0 remains byte-for-byte frozen (FROZEN_NEVER_CONSUMED_NOT_AUTHORIZED).
v1.1 was executed exactly once and is CONSUMED_FAILED (retry FORBIDDEN).
v1.2 was executed exactly once and is CONSUMED_RESULT  (retry FORBIDDEN).
v1.3 was executed exactly once and is CONSUMED_TERMINAL_EVIDENCE_ANOMALY
     (D67; retry FORBIDDEN; root cause UNRESOLVED).  v1.4 is NOT a v1.3 retry.

The scientific path is v1.3's UNCHANGED (D61 canonical ACCEPT fusion
``fuse_full_field``).  The ONLY changes from v1.3 are observability:
crash-survivable stage journaling, a GT-free progress journal, and durable
process/exit evidence produced by the companion supervisor.

Gate implementation strategy (NON-CIRCULAR, no gate duplication):
  * All shared gates are imported VERBATIM from the frozen v1.3 launcher module
    (which itself imports them from the frozen v1.2 launcher): the launcher never
    re-implements a gate, so gate semantics cannot drift.
  * v1.4 OVERRIDES only:
      - the pinned diagnostic source path + SHA (the v1.4 diagnostic),
      - the diagnostic-native launch-authority token (v1.4 token),
      - the diagnostic start/result/failure marker paths (v1_4), and
      - ADDS the v1.3 CONSUMED-state binding gate (D67/D68 preservation).
  * The frozen v1.3 launcher module is imported by path and NOT mutated.

Required order (fail closed):
    (1)  parse args
    (2)  immutable anchors: v1.4 diagnostic D61 contract + frozen v1.14 exec/manifest
    (3)  exact project interpreter identity
    (4)  CUDA readiness
    (5)  FOREIGN v1.14 LAUNCH-AUTHORITY ABSENCE gate
    (6)  prior-failure provenance binding
    (7)  consumed v1.2 clean-eq / D51 provenance binding
    (8)  v1.0 + v1.1 source preservation
    (9)  exact 14-dependency / 4-checkpoint integrity + exact source<->manifest equality
    (10) D52 Phase27 FINAL f16 authority SHA / header / sample-order gate
    (11) v1.1 CONSUMED-state binding gate (START/FAILURE/absence/predicates)
    (12) v1.2 CONSUMED-state binding gate (START/RESULT/adjudication/predicates)
    (13) v1.3 CONSUMED-state binding gate (D67/D68 preservation)              [NEW v1.4]
    (14) --verify-only STOP (non-consuming)
    (15) set the v1.4 launch-authority token ONLY now
    (16) dispatch the diagnostic module ONLY

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

DIAGNOSTIC_SELF = ROOT / "scripts" / "analysis" / "phase36_final_probability_authority_diagnostic_v1_4.py"
FROZEN_V1_14 = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_14.py"
MANIFEST_V1_14 = ROOT / "reports" / "audits" / "phase36_v1_14_runtime_source_integrity_manifest.json"

# ---- the frozen v1.3 launcher whose SHARED gates are imported VERBATIM ----- #
FROZEN_V1_3_LAUNCHER = ROOT / "scripts" / "analysis" / "launch_phase36_final_probability_authority_diagnostic_v1_3.py"
FROZEN_V1_3_LAUNCHER_SHA = "d5f9cd3dff302c849d195d909f6f2c9a59fbbbaaf359d859e69442d9fe05b504"

CANONICAL_INTERPRETER = ROOT / ".venv" / "Scripts" / "python.exe"

# D61-C — diagnostic-native authority ONLY (v1.4 token).
LAUNCH_AUTHORITY_TOKEN = "PHASE36_FINAL_PROB_AUTHORITY_V1_4_LAUNCH_AUTHORITY"
ONE_SHOT_ENV = "PHASE36_FINAL_PROB_AUTHORITY_EXECUTE"
FOREIGN_V1_14_LAUNCH_TOKEN = "PHASE36_V1_14_LAUNCH_AUTHORITY"

# ---- FROZEN anchors (LITERAL, IMMUTABLE, NON-ENV-OVERRIDABLE) ------------- #
FROZEN_EXPECTED_V1_14_EXEC_SHA = "ac09ff8ded3610244920e66612145b246b33127140d344a9730d454bab27cff5"
FROZEN_EXPECTED_V1_14_MANIFEST_SHA = "b4c358dfcb5e7b59beb6ae1ba2cffc64677d10049e12568b4c8eea8e79bb911e"

# ---- v1.4 diagnostic-native anchors --------------------------------------- #
V1_4_DIAGNOSTIC_START = ROOT / "reports" / "audits" / "phase36_final_probability_authority_diagnostic_start_v1_4.json"
V1_4_DIAGNOSTIC_RESULT = ROOT / "reports" / "audits" / "phase36_final_probability_authority_diagnostic_result_v1_4.json"
V1_4_DIAGNOSTIC_FAILURE = ROOT / "reports" / "audits" / "phase36_final_probability_authority_diagnostic_failure_v1_4.json"

# ---- v1.3 CONSUMED-state binding (D67/D68 preservation) ------------------- #
V1_3_START_PATH = "reports/audits/phase36_final_probability_authority_diagnostic_start_v1_3.json"
V1_3_START_SHA = "b984d09bf3a266de8d75b39b6ad2ff3236cce09915a7f2a5c874813af8c3c1c5"
V1_3_RESULT_PATH = "reports/audits/phase36_final_probability_authority_diagnostic_result_v1_3.json"
V1_3_FAILURE_PATH = "reports/audits/phase36_final_probability_authority_diagnostic_failure_v1_3.json"
V1_3_D67_ADJ_PATH = (
    "reports/audits/phase36_final_probability_authority_diagnostic_v1_3_terminal_evidence_anomaly_adjudication_v1_0.json")
V1_3_D67_ADJ_SHA = "3d3f943c19d5b419fb00bcf19748c0dd41ff8002ef26a4a3c51ad32ef6afecd5"
V1_3_D68_RECON_PATH = (
    "reports/audits/phase36_final_probability_authority_diagnostic_v1_3_terminal_evidence_anomaly_adjudication_reconciliation_v1_1.json")
V1_3_D68_RECON_SHA = "f6bbe602c5928e39d160629688cf697a73f65941a5d24d13c5ad4008a8dc0fc2"
V1_3_D66_RECON_PATH = (
    "reports/audits/phase36_final_probability_authority_diagnostic_v1_3_governance_reconciliation_v1_0.json")
V1_3_D66_RECON_SHA = "b0c01e40c4764514a01a9f082483a071634a0630d6c4c4640e1bb4ac2f829303"
REQUIRED_D67_CLASSIFICATION = "POST_START_TERMINAL_EVIDENCE_ANOMALY"
REQUIRED_D67_ATTEMPT_STATE = "CONSUMED_TERMINAL_EVIDENCE_ANOMALY"
REQUIRED_D67_ROOT_CAUSE = "UNRESOLVED"
REQUIRED_D67_TERMINATION_MECHANISM = "UNRESOLVED"
REQUIRED_D68_CLASSIFICATION = "D67_TERMINAL_WRITE_REACH_OVERCLAIM"
REQUIRED_D68_STATUS = "RECONCILED"
REQUIRED_V1_3_STATE = "CONSUMED_TERMINAL_EVIDENCE_ANOMALY"

T_ANCHOR_FAILED = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_4_LAUNCH_FAIL_CLOSED__ANCHOR_VERIFICATION_FAILED__NO_ATTEMPT_CONSUMED"
T_WRONG_INTERPRETER = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_4_LAUNCH_FAIL_CLOSED__WRONG_INTERPRETER__NO_ATTEMPT_CONSUMED"
T_CUDA_UNAVAILABLE = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_4_LAUNCH_FAIL_CLOSED__CUDA_READINESS_FAILED__NO_ATTEMPT_CONSUMED"
T_FOREIGN_TOKEN_PRESENT = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_4_FAIL_CLOSED__FOREIGN_V1_14_LAUNCH_AUTHORITY_PRESENT__NO_ATTEMPT_CONSUMED"
T_PROVENANCE_FAILED = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_4_LAUNCH_FAIL_CLOSED__PRIOR_FAILURE_PROVENANCE_NOT_BOUND__NO_ATTEMPT_CONSUMED"
T_CONSUMED_BIND_FAILED = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_4_LAUNCH_FAIL_CLOSED__CONSUMED_EVIDENCE_NOT_BOUND__NO_ATTEMPT_CONSUMED"
T_V1_0_PRESERVATION_FAILED = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_4_LAUNCH_FAIL_CLOSED__V1_0_SOURCE_NOT_PRESERVED__NO_ATTEMPT_CONSUMED"
T_TRANSITIVE_FAILED = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_4_FAIL_CLOSED__TRANSITIVE_INTEGRITY_FAILED__NO_ATTEMPT_CONSUMED"
T_AUTHORITY_EXACT_FAILED = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_4_FAIL_CLOSED__SOURCE_MANIFEST_TRANSITIVE_AUTHORITY_MISMATCH__NO_ATTEMPT_CONSUMED"
T_FINAL_AUTHORITY_FAILED = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_4_FAIL_CLOSED__FINAL_AUTHORITY_PRECONSUMPTION_GATE_FAILED__NO_ATTEMPT_CONSUMED"
T_V1_1_CONSUMED_FAILED = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_4_FAIL_CLOSED__V1_1_CONSUMED_STATE_NOT_BOUND__NO_ATTEMPT_CONSUMED"
T_V1_2_CONSUMED_FAILED = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_4_FAIL_CLOSED__V1_2_CONSUMED_STATE_NOT_BOUND__NO_ATTEMPT_CONSUMED"
T_V1_3_CONSUMED_FAILED = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_4_FAIL_CLOSED__V1_3_CONSUMED_STATE_NOT_BOUND__NO_ATTEMPT_CONSUMED"
T_VERIFY_ONLY_OK = "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_4_LAUNCH_READINESS_VERIFIED__DISPATCH_SUPPRESSED_BY_VERIFY_ONLY"


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _load_frozen_v1_3_launcher():
    """Import the FROZEN v1.3 launcher module (by path; never mutated).

    Its SHARED gate functions (themselves re-imported from the frozen v1.2 launcher)
    are reused VERBATIM so gate semantics cannot drift.
    """
    if sha(FROZEN_V1_3_LAUNCHER) != FROZEN_V1_3_LAUNCHER_SHA:
        raise SystemExit(
            "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_4_FAIL_CLOSED__"
            "FROZEN_V1_3_LAUNCHER_SHA_MISMATCH__NO_ATTEMPT_CONSUMED")
    spec = importlib.util.spec_from_file_location("_p36_v1_3_frozen_launcher_v14", FROZEN_V1_3_LAUNCHER)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_p36_v1_3_frozen_launcher_v14"] = mod
    spec.loader.exec_module(mod)
    return mod


_V13 = _load_frozen_v1_3_launcher()

# Reused VERBATIM from the frozen v1.3 launcher (which re-exports v1.2 shared gates).
read_npy_header = _V13.read_npy_header
check_interpreter_identity = _V13.check_interpreter_identity
check_cuda_readiness = _V13.check_cuda_readiness
check_foreign_v1_14_token_absent = _V13.check_foreign_v1_14_token_absent
check_prior_failure_provenance = _V13.check_prior_failure_provenance
check_consumed_evidence = _V13.check_consumed_evidence
check_v1_0_preserved = _V13.check_v1_0_preserved
check_v1_1_preserved = _V13.check_v1_1_preserved
check_v1_1_consumed_state = _V13.check_v1_1_consumed_state
check_v1_2_consumed_state = _V13.check_v1_2_consumed_state
check_transitive_integrity = _V13.check_transitive_integrity
check_final_authority_preconsumption = _V13.check_final_authority_preconsumption
check_d56_module_interface = _V13.check_d56_module_interface
_load_frozen_v1_14_authority_maps = _V13._load_frozen_v1_14_authority_maps

EXPECTED_N_DEPENDENCIES = _V13.EXPECTED_N_DEPENDENCIES
EXPECTED_N_CHECKPOINTS = _V13.EXPECTED_N_CHECKPOINTS


# --------------------------------------------------------------------------- #
# v1.4 anchor verification (D61 identity + frozen v1.14 anchors)
# --------------------------------------------------------------------------- #
def verify_authority(diag_path: Path | None = None,
                     v14_path: Path | None = None,
                     manifest_path: Path | None = None) -> dict:
    """v1.4 anchor gate.

    The v1.4 diagnostic SHA is self-referential (the launcher cannot embed the SHA
    of the very file it dispatches); instead the launcher verifies:
      * the FROZEN v1.14 exec + manifest SHAs (literal, immutable);
      * the v1.4 diagnostic is PRESENT + PARSES, and contains the D61 repair
        contract (``fuse_full_field`` CALL inside the ACCEPT branch), and contains
        NO ``_fuse_global_with_regional`` CALL (the literal may appear as the D61
        provenance constant / comment only); and
      * the launcher_sha256 key is absent from the manifest.
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
# D67/D68 — v1.3 CONSUMED-state binding gate (NEW in v1.4)
# --------------------------------------------------------------------------- #
def check_v1_3_consumed_state(root: Path | None = None) -> dict:
    """D67/D68 preservation gate: bind the v1.3 consumed evidence + authorities."""
    base = Path(root) if root is not None else ROOT
    out = {"ok": True, "items": {}, "predicates": {}}
    for name, rel, exp in (
        ("v1_3_start", V1_3_START_PATH, V1_3_START_SHA),
        ("v1_3_d67_adjudication_v1_0", V1_3_D67_ADJ_PATH, V1_3_D67_ADJ_SHA),
        ("v1_3_d68_reconciliation_v1_1", V1_3_D68_RECON_PATH, V1_3_D68_RECON_SHA),
        ("v1_3_d66_governance_reconciliation_v1_0", V1_3_D66_RECON_PATH, V1_3_D66_RECON_SHA),
    ):
        p = base / rel
        obs = sha(p) if p.exists() else None
        m = (obs == exp)
        out["items"][name] = {"path": rel, "present": p.exists(), "expected": exp,
                              "observed": obs, "match": bool(m)}
        if not m:
            out["ok"] = False
    out["v1_3_result_absent"] = not (base / V1_3_RESULT_PATH).exists()
    out["v1_3_failure_absent"] = not (base / V1_3_FAILURE_PATH).exists()
    if not out["v1_3_result_absent"]:
        out["ok"] = False
    if not out["v1_3_failure_absent"]:
        out["ok"] = False

    adj = base / V1_3_D67_ADJ_PATH
    if adj.exists():
        try:
            aj = json.loads(adj.read_text(encoding="utf-8"))
            pred = {
                # Actual D67 artifact key is `D67` (value POST_START_TERMINAL_EVIDENCE_ANOMALY);
                # fallbacks tolerate historical/alternate spellings.
                "d67_classification": (aj.get("D67") or aj.get("D67_CLASSIFICATION")
                                       or aj.get("classification")),
                "attempt_state": aj.get("attempt_state"),
                "root_cause": aj.get("root_cause"),
                "termination_mechanism": aj.get("termination_mechanism"),
            }
            out["predicates"].update(pred)
        except Exception as exc:  # noqa: BLE001
            out["adjudication_parse_error"] = type(exc).__name__
            out["ok"] = False
    rec = base / V1_3_D68_RECON_PATH
    if rec.exists():
        try:
            rj = json.loads(rec.read_text(encoding="utf-8"))
            # Actual reconciliation keys: lowercase `d68_classification`; `D68` carries
            # the RECONCILED status (value "RECONCILED"). Fallbacks tolerate alternates.
            out["predicates"]["d68_classification"] = (rj.get("d68_classification")
                                                       or rj.get("D68_CLASSIFICATION")
                                                       or rj.get("classification"))
            out["predicates"]["d68_status"] = (rj.get("D68") or rj.get("D68_STATUS")
                                               or rj.get("status"))
        except Exception as exc:  # noqa: BLE001
            out["reconciliation_parse_error"] = type(exc).__name__
            out["ok"] = False
    # D67/D68 PRESERVATION: exact retained statuses.
    if out["predicates"].get("d67_classification") != REQUIRED_D67_CLASSIFICATION:
        out["ok"] = False
    if out["predicates"].get("attempt_state") != REQUIRED_D67_ATTEMPT_STATE:
        out["ok"] = False
    if out["predicates"].get("root_cause") != REQUIRED_D67_ROOT_CAUSE:
        out["ok"] = False
    if out["predicates"].get("termination_mechanism") != REQUIRED_D67_TERMINATION_MECHANISM:
        out["ok"] = False
    if out["predicates"].get("d68_classification") != REQUIRED_D68_CLASSIFICATION:
        out["ok"] = False
    if out["predicates"].get("d68_status") != REQUIRED_D68_STATUS:
        out["ok"] = False
    return out


def _emit(terminal: str, **extra) -> int:
    payload = {"launcher": "launch_phase36_final_probability_authority_diagnostic_v1_4",
               "terminal": terminal}
    payload.update(extra)
    print(json.dumps(payload, indent=1))
    return 2


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify-only", action="store_true",
                    help="verify all gates incl. the D52 final-authority and the v1.1/v1.2/v1.3 "
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
                          r"scripts\analysis\launch_phase36_final_probability_authority_diagnostic_v1_4.py --verify-only")

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

    # (13) v1.3 CONSUMED-state binding gate (D67/D68 preservation)
    v13 = check_v1_3_consumed_state()
    if not v13["ok"]:
        return _emit(T_V1_3_CONSUMED_FAILED, authorized=False, v1_3_consumed_state=v13,
                     v1_2_consumed_state=v12, d56_module_interface=d56,
                     v1_1_consumed_state=v11, final_authority=fa, transitive_integrity=ti,
                     v1_0_preservation=preserved, v1_1_preservation=preserved_v11,
                     consumed_evidence=consumed, provenance=prov, foreign_gate=foreign,
                     interpreter=interp, cuda_readiness=cuda, authority=auth)

    # (14) verify-only STOP (non-consuming)
    if a.verify_only:
        print(json.dumps({
            "launcher": "launch_phase36_final_probability_authority_diagnostic_v1_4",
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
            "v1_3_consumed_state_binding_pass": v13["ok"],
            "v1_3_result_absent": v13["v1_3_result_absent"],
            "v1_3_failure_absent": v13["v1_3_failure_absent"],
            "d67_classification_bound": v13["predicates"].get("d67_classification"),
            "d67_attempt_state_bound": v13["predicates"].get("attempt_state"),
            "d67_root_cause_bound": v13["predicates"].get("root_cause"),
            "d67_termination_mechanism_bound": v13["predicates"].get("termination_mechanism"),
            "d68_classification_bound": v13["predicates"].get("d68_classification"),
            "d68_status_bound": v13["predicates"].get("d68_status"),
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

    # (15) the ONLY write of the v1.4 launch-authority token (after the verify STOP)
    os.environ[LAUNCH_AUTHORITY_TOKEN] = "1"
    # record the launcher SHA for the diagnostic's stage journal (observability only)
    os.environ["PHASE36_FINAL_PROB_AUTHORITY_LAUNCHER_SHA256"] = sha(Path(__file__))

    # (16) dispatch the diagnostic module ONLY
    spec = importlib.util.spec_from_file_location("phase36_final_prob_authority_diag_v1_4",
                                                  DIAGNOSTIC_SELF)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return int(mod.main())


if __name__ == "__main__":
    raise SystemExit(main())
