#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 36 — CLEAN EQUIVALENCE DIAGNOSTIC v1.1.

ADDITIVE revision of diagnostic v1.0 (v1.0 is FROZEN / NEVER CONSUMED / NOT
AUTHORIZED and is preserved byte-for-byte).   v1.1 repairs D45–D49 found by
independent source-level review:

  D45  the diagnostic SOURCE now REQUIRES the launch-authority token (in addition
       to the one-shot execute gate) before any start marker may be created.
  D46  the counter authority is taken EXACTLY from the frozen v1.14 module
       (``mod.C.COUNTERS_REQUIRED`` / ``mod.C.COUNTERS_FOREVER_ZERO``); any
       standalone alternate common-module import and the empty-dict fallback are
       FORBIDDEN and removed; failure to obtain the authority is fail-closed.
  D47  the durable result write is INSIDE the guarded terminal-evidence region,
       so every terminal path after marker consumption attempts a durable
       result/failure artifact; the failure artifact records termination_kind,
       exception info, failing_stage, eq-computed state and the full eq if
       available.
  D48  (launcher-side) transitive hash-only integrity verification before
       launch authority is granted.  This source still calls the frozen
       ``_verify_transitive_source_integrity()`` after start as defense in depth.
  D49  (validator-side) real AST / control-flow bindings.

WHY THIS EXISTS
---------------
The single authorized Phase36 v1.14 scientific robustness attempt (CONSUMED
2026-10-06) terminated at the CLEAN EQUIVALENCE gate with
``CLEAN_EQUIVALENCE_GATE_FAILED__STOP_BEFORE_PERTURBATION`` and D44 recorded that
the full ``eq`` object was NOT durably preserved.  The Step-2 targeted static
audit returned ``STATIC_ROOT_CAUSE_NOT_ESTABLISHED``; the root cause therefore
requires a clean diagnostic re-execution with DURABLE eq capture.

EXECUTION SCOPE (clean only; steps 1..7 then STOP):
    STEP1 _verify_transitive_source_integrity()      (defense in depth)
    STEP2 _load_models()                              (CUDA fail-closed)
    STEP3 _bind_clean_reference()                     (authority bind)
    STEP4 _generate_clean_g_reference(ctx, counters)
    STEP5 _phase27_global_reproduction_gate(...)      (STOP on fail)
    STEP6 808 x _evaluate_clean_sample(...)
    STEP7 eq = _clean_equivalence_gate(...)           (DURABLE eq)
    STEP8 durably write the result (INSIDE guarded region — D47)
    STEP9 STOP (never perturbation)

PROHIBITIONS (hard)
-------------------
* NEVER writes / touches any v1.14 science marker/result/failure artifact.
* NEVER executes image or proposal perturbations.
* NEVER modifies the frozen v1.14 source (imports it read-only).
* NEVER retries: write-once start marker guards a single attempt.
* One-shot gate: ``PHASE36_CLEAN_EQ_DIAGNOSTIC_EXECUTE=1``.
* Launch authority: ``PHASE36_CLEAN_EQ_DIAGNOSTIC_V1_1_LAUNCH_AUTHORITY=1``.

This artifact is DIAGNOSTIC.  ``scientific_output`` is False and
``robustness_result`` is False; it MUST NOT be reported as a robustness result.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
import traceback
from collections import OrderedDict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "scripts" / "analysis") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts" / "analysis"))

# --------------------------------------------------------------------------- #
# D45 — REQUIRED AUTHORITY TOKENS (both must be "1" before a start marker)
# --------------------------------------------------------------------------- #
ONE_SHOT_ENV = "PHASE36_CLEAN_EQ_DIAGNOSTIC_EXECUTE"
LAUNCH_AUTHORITY_TOKEN = "PHASE36_CLEAN_EQ_DIAGNOSTIC_V1_1_LAUNCH_AUTHORITY"

DIAGNOSTIC_REVISION = "ra_medfilm_barr_phase36_clean_equivalence_diagnostic_v1_1"

FROZEN_V1_14_SOURCE = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_14.py"
FROZEN_V1_14_EXEC_SHA = "ac09ff8ded3610244920e66612145b246b33127140d344a9730d454bab27cff5"
FROZEN_V1_14_MANIFEST_SHA = "b4c358dfcb5e7b59beb6ae1ba2cffc64677d10049e12568b4c8eea8e79bb911e"

DIAGNOSTIC_START = ROOT / "reports" / "audits" / "phase36_clean_equivalence_diagnostic_start_v1_1.json"
DIAGNOSTIC_RESULT = ROOT / "reports" / "audits" / "phase36_clean_equivalence_diagnostic_result_v1_1.json"
DIAGNOSTIC_FAILURE = ROOT / "reports" / "audits" / "phase36_clean_equivalence_diagnostic_failure_v1_1.json"

# Prior-failure provenance (machine-bound release; D45/D48 handoff contract).
PRIOR_FAILURE_PROVENANCE = OrderedDict([
    ("v1_14_science_start", OrderedDict([
        ("path", "reports/audits/phase36_robustness_science_start_v1_14.json"),
        ("sha256", "e2c42b05f4fd0450022d7bcde091c0bea13638788b4f83a123016ab894630e0a")])),
    ("v1_14_science_failure", OrderedDict([
        ("path", "reports/audits/phase36_robustness_science_failure_v1_14.json"),
        ("sha256", "0fcc3c211d7bcd53b4f8e53d7b09f518fd83a929e8a979c7174762958fff754b")])),
    ("v1_14_forensic_adjudication", OrderedDict([
        ("path", "reports/audits/phase36_v1_14_science_failure_forensic_adjudication.json"),
        ("sha256", "f1d4712ae7b3f0b333a22c852f99d6b3812218ffb258f8f58ddba62c7193c17e")])),
    ("forensic_reconciliation_v2", OrderedDict([
        ("path", "reports/audits/phase36_v1_14_science_failure_forensic_reconciliation_v2.json"),
        ("sha256", "cc9a3b502f59e3855c395b9d6afa2f5616f513d60af4756e4477a9370889cc3c")])),
    ("targeted_static_audit", OrderedDict([
        ("path", "reports/audits/phase36_clean_equivalence_targeted_static_audit_v1_0.json"),
        ("sha256", "8def086c44a7e80461c729f41ab61c0be347ef1589c94d6884a082adbde64ed4")])),
])
REQUIRED_STATIC_AUDIT_VERDICT = "STATIC_ROOT_CAUSE_NOT_ESTABLISHED"

# NEVER touched (guard: assert absence, then never write)
V14_SCIENCE_MARKERS = (
    ROOT / "reports" / "audits" / "phase36_robustness_science_start_v1_14.json",
    ROOT / "reports" / "audits" / "phase36_robustness_scientific_result_v1_14.json",
    ROOT / "reports" / "audits" / "phase36_robustness_science_failure_v1_14.json",
)


def sha256_file(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def _import_frozen_v1_14():
    """Import the frozen v1.14 module by path (never mutating the source)."""
    if sha256_file(FROZEN_V1_14_SOURCE) != FROZEN_V1_14_EXEC_SHA:
        raise SystemExit(
            "PHASE36_CLEAN_EQ_DIAGNOSTIC_V1_1_FAIL_CLOSED__FROZEN_V1_14_SOURCE_SHA_MISMATCH__NO_ATTEMPT_CONSUMED")
    spec = importlib.util.spec_from_file_location("_p36_v1_14_frozen_diag_v11", FROZEN_V1_14_SOURCE)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_p36_v1_14_frozen_diag_v11"] = mod
    spec.loader.exec_module(mod)
    return mod


# --------------------------------------------------------------------------- #
# D47 — ROBUST FULL-WRITE HELPER (exclusive-create; full write; fsync; loud fail)
# --------------------------------------------------------------------------- #
def _write_once_json(path: Path, payload: dict) -> bool:
    """Exclusive-create write of a JSON payload.

    O_CREAT|O_EXCL, write ALL bytes (looping on short writes), fsync before close,
    and fail LOUDLY on any short/failed write.  Returns True on success.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, indent=1, ensure_ascii=False, default=str).encode("utf-8")
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    fd = os.open(str(path), flags, 0o644)
    try:
        total = 0
        while total < len(data):
            n = os.write(fd, data[total:])
            if n is None or n <= 0:
                raise OSError(f"SHORT_WRITE at offset {total} of {len(data)} for {path}")
            total += n
        if total != len(data):
            raise OSError(f"SHORT_WRITE total={total} expected={len(data)} for {path}")
        os.fsync(fd)
    finally:
        os.close(fd)
    # Post-condition: exact byte length on disk.
    if path.stat().st_size != len(data):
        raise OSError(f"POST_WRITE_SIZE_MISMATCH for {path}")
    return True


def _attempt_already_consumed() -> bool:
    return any(p.exists() for p in (DIAGNOSTIC_START, DIAGNOSTIC_RESULT, DIAGNOSTIC_FAILURE))


def _prior_failure_provenance_state() -> dict:
    out = {"all_match": True, "items": {}, "static_audit_verdict": None}
    for name, spec in PRIOR_FAILURE_PROVENANCE.items():
        p = ROOT / spec["path"]
        ok = p.exists() and sha256_file(p) == spec["sha256"]
        out["items"][name] = {"path": spec["path"], "present": p.exists(),
                              "expected": spec["sha256"],
                              "observed": (sha256_file(p) if p.exists() else None),
                              "match": bool(ok)}
        if not ok:
            out["all_match"] = False
    audit_p = ROOT / PRIOR_FAILURE_PROVENANCE["targeted_static_audit"]["path"]
    if audit_p.exists():
        try:
            out["static_audit_verdict"] = json.loads(
                audit_p.read_text(encoding="utf-8")).get("root_cause_static_verdict")
        except Exception as exc:  # noqa: BLE001
            out["static_audit_verdict"] = f"UNPARSEABLE::{type(exc).__name__}"
    if out["static_audit_verdict"] != REQUIRED_STATIC_AUDIT_VERDICT:
        out["all_match"] = False
    return out


def _build_counters(mod) -> "OrderedDict":
    """D46 — EXACT frozen v1.14 counter authority.

    Uses ``mod.C.COUNTERS_REQUIRED`` / ``mod.C.COUNTERS_FOREVER_ZERO`` ONLY.
    NO alternate common module; NO empty-dict fallback; NO exception swallowing.
    Fails CLOSED if the frozen counter authority is unavailable.
    """
    try:
        C = mod.C
        required = list(C.COUNTERS_REQUIRED)
        forever_zero = list(C.COUNTERS_FOREVER_ZERO)
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(
            "PHASE36_CLEAN_EQ_DIAGNOSTIC_V1_1_FAIL_CLOSED__FROZEN_COUNTER_AUTHORITY_UNAVAILABLE: "
            f"{type(exc).__name__}: {exc}")
    if not required:
        raise SystemExit(
            "PHASE36_CLEAN_EQ_DIAGNOSTIC_V1_1_FAIL_CLOSED__FROZEN_COUNTER_AUTHORITY_EMPTY")
    counters = OrderedDict((k, 0) for k in required)
    for k in forever_zero:
        counters[k] = 0
    counters["_counter_authority_required_n"] = len(required)
    counters["_counter_authority_forever_zero_n"] = len(forever_zero)
    return counters


def _resolve_authority_paths(mod) -> dict:
    """Reference authority paths + SHA-256 (for the durable result artifact).

    Reads the paths from the frozen v1.14 module's own ``mod.C`` reference
    (never a standalone alternate import).
    """
    out: dict = {}
    try:
        CR = mod.C.CLEAN_REFERENCE
        for key in ("per_sample_scores", "routing_state"):
            spec = CR[key]
            p = ROOT / spec["path"]
            out[key] = {"path": spec["path"], "expected_sha256": spec["sha256"],
                        "present": p.exists(),
                        "observed_sha256": (sha256_file(p) if p.exists() else None)}
    except Exception as exc:  # noqa: BLE001
        out["CLEAN_REFERENCE_error"] = f"{type(exc).__name__}: {exc}"
    return out


def _resolve_frozen_path_authorities(mod) -> dict:
    """VAL808 manifest + phase27 global probability authority (from frozen v1.14)."""
    out: dict = {}
    try:
        gp = mod.PHASE27_GLOBAL_PROB_AUTHORITY
        p = ROOT / gp["path"]
        out["phase27_clean_global_prob_authority"] = {
            "path": gp["path"], "expected_sha256": gp["sha256"], "present": p.exists(),
            "observed_sha256": (sha256_file(p) if p.exists() else None),
            "shape": list(gp.get("shape", [])), "dtype": gp.get("dtype"),
            "byte_identical_twin": gp.get("byte_identical_twin")}
    except Exception as exc:  # noqa: BLE001
        out["phase27_clean_global_prob_authority_error"] = f"{type(exc).__name__}: {exc}"
    try:
        vm_path = mod.C.VAL_MANIFEST
        vm_sha = mod.C.VAL_MANIFEST_SHA
        p = ROOT / vm_path
        out["val808_manifest"] = {"path": vm_path, "expected_sha256": vm_sha,
                                  "present": p.exists(),
                                  "observed_sha256": (sha256_file(p) if p.exists() else None)}
    except Exception as exc:  # noqa: BLE001
        out["val808_manifest_error"] = f"{type(exc).__name__}: {exc}"
    return out


# --------------------------------------------------------------------------- #
# D47 — DURABLE TERMINAL EVIDENCE
# --------------------------------------------------------------------------- #
def _write_failure(*, termination_kind, exc_type=None, exc_msg=None,
                   failing_stage=None, eq=None, marker_consumed=True,
                   extra=None) -> bool:
    """Exclusive-create the diagnostic failure artifact (best-effort but loud).

    Includes D47-required fields.  Returns True iff written.
    """
    if DIAGNOSTIC_FAILURE.exists():
        print(json.dumps({"note": "FAILURE_ARTIFACT_ALREADY_EXISTS", "path": str(DIAGNOSTIC_FAILURE)}))
        return False
    payload = {
        "artifact_kind": "PHASE36_CLEAN_EQUIVALENCE_DIAGNOSTIC_FAILURE",
        "revision": DIAGNOSTIC_REVISION,
        "automatic_retry": False,
        "overwrite_permitted": False,
        "termination_kind": termination_kind,
        "exception": exc_type is not None,
        "exception_type": exc_type,
        "exception_message": exc_msg,
        "failing_stage": failing_stage,
        "marker_consumed": bool(marker_consumed),
        "clean_equivalence_computed": bool(eq is not None),
        "clean_equivalence_full": eq,
        "frozen_v1_14_exec_source_sha256": FROZEN_V1_14_EXEC_SHA,
        "frozen_v1_14_manifest_sha256": FROZEN_V1_14_MANIFEST_SHA,
        "scientific_output": False,
        "robustness_result": False,
        "perturbation_executed": False,
        "generated_utc": now(),
        "write_semantics": "O_CREAT|O_EXCL + full-write + fsync (exclusive-create, write-once)",
    }
    if extra:
        payload.update(extra)
    try:
        _write_once_json(DIAGNOSTIC_FAILURE, payload)
        return True
    except Exception as exc:  # noqa: BLE001
        # D47: fail LOUDLY — never silently swallow a failed terminal-evidence write.
        print(json.dumps({
            "error": "FAILURE_ARTIFACT_WRITE_FAILED",
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "path": str(DIAGNOSTIC_FAILURE)}, indent=1))
        return False


# --------------------------------------------------------------------------- #
# DIAGNOSTIC EXECUTION
# --------------------------------------------------------------------------- #
def run_diagnostic() -> dict:
    mod = _import_frozen_v1_14()

    # D46 — exact frozen counter authority (fail closed if unavailable).
    counters = _build_counters(mod)

    stages: dict = {}
    eq = None

    # STEP 1 — transitive runtime source integrity (defense in depth)
    si = mod._verify_transitive_source_integrity()
    stages["step1_source_integrity_all_match"] = bool(si.get("all_match"))
    stages["step1_source_integrity"] = si
    if not si.get("all_match"):
        raise SystemExit(
            "DIAGNOSTIC_SOURCE_INTEGRITY_FAILED: " + json.dumps(si, default=str))

    # STEP 2 — load models (CUDA fail-closed inside)
    ctx = mod._load_models()
    stages["step2_models_loaded"] = True
    stages["step2_component_load_audit"] = ctx.get("load_audit")

    # STEP 3 — bind clean reference authority
    clean_ref_bound = mod._bind_clean_reference()
    stages["step3_clean_reference_bound"] = clean_ref_bound is not None
    if clean_ref_bound is None:
        raise SystemExit("DIAGNOSTIC_CLEAN_REFERENCE_BIND_FAILED")

    # STEP 4 — canonical batched CLEAN G pass
    generated = mod._generate_clean_g_reference(ctx, counters)
    stages["step4_generation_n"] = len(generated.get("sample_order", []))

    # STEP 5 — Phase27 clean global reproduction gate (STOP on fail)
    g_gate = mod._phase27_global_reproduction_gate(
        generated["p_global_f16"], generated["sample_order"], counters)
    stages["step5_phase27_reproduction_gate"] = g_gate
    if not g_gate.get("pass"):
        raise SystemExit(
            "DIAGNOSTIC_PHASE27_GLOBAL_REPRODUCTION_GATE_FAILED: "
            + json.dumps(g_gate, default=str))

    # STEP 6 — 808 clean system evaluations
    clean_store = {}
    clean_records = []
    rows, row_index = mod._clean_row_index()
    for r in rows:
        sid = r["sample_id"]
        clean_records.append(
            mod._evaluate_clean_sample(sid, r, ctx, generated, counters, clean_store))
        counters["clean_passes"] = counters.get("clean_passes", 0) + 1
    generated["records"] = clean_records
    stages["step6_clean_records"] = len(clean_records)

    # STEP 7 — strict clean-equivalence gate (DURABLE eq capture — the D44 repair)
    eq = mod._clean_equivalence_gate(clean_ref_bound, generated, counters)
    stages["step7_clean_equivalence"] = eq

    # ---- DIAGNOSTIC OUTCOME (durably persisted by the caller, D47) --------- #
    all_pass = bool(eq.get("all_pass"))
    diag = {
        "artifact_kind": "PHASE36_CLEAN_EQUIVALENCE_DIAGNOSTIC_RESULT",
        "revision": DIAGNOSTIC_REVISION,
        "purpose": "DURABLE_CLEAN_EQUIVALENCE_DIAGNOSTIC__D44_REPAIR",
        "execution_scope": "CLEAN_ONLY__STEPS_1_THROUGH_7__NO_PERTURBATION",
        "exact_diagnostic_source_sha256": sha256_file(Path(__file__)),
        "frozen_v1_14_source_sha256": sha256_file(FROZEN_V1_14_SOURCE),
        "frozen_v1_14_manifest_sha256": FROZEN_V1_14_MANIFEST_SHA,
        "clean_equivalence_full": eq,
        "stages": stages,
        "counters": dict(counters),
        "authorized_population_count": 808,
        "reference_authority_paths_and_sha256": _resolve_authority_paths(mod),
        "frozen_path_authorities": _resolve_frozen_path_authorities(mod),
        "prior_failure_provenance_bound": _prior_failure_provenance_state(),
        "all_pass": all_pass,
        "diagnosis": (
            "CLEAN_EQUIVALENCE_PASSES__ORIGINAL_V1_14_FAILURE_NOT_REPRODUCED_ON_CLEAN_SEQUENCE"
            if all_pass else
            "CLEAN_EQUIVALENCE_FAILS__REPRODUCED__SEE_FAILING_CHECKS_AND_MISMATCH_LISTS"),
        "failing_checks": ([k for k, v in (eq.get("checks") or {}).items() if not v]),
        "perturbation_executed": False,
        "scientific_output": False,
        "robustness_result": False,
        "v1_14_science_markers_touched": False,
        "generated_utc": now(),
        "write_semantics": "O_CREAT|O_EXCL + full-write + fsync (exclusive-create, write-once)",
    }
    return diag


def main() -> int:
    # ---- D45 (1) one-shot execute gate ------------------------------------ #
    if os.environ.get(ONE_SHOT_ENV) != "1":
        print(json.dumps({
            "status": "REFUSED__ONE_SHOT_GATE_NOT_SET",
            "required_env": f"{ONE_SHOT_ENV}=1",
            "attempt_consumed": False}, indent=1))
        return 3

    # ---- D45 (2) prior-attempt absence ------------------------------------ #
    if _attempt_already_consumed():
        print(json.dumps({
            "status": "REFUSED__DIAGNOSTIC_ATTEMPT_ALREADY_CONSUMED",
            "automatic_retry": False,
            "attempt_consumed": False}, indent=1))
        return 4

    # ---- D45 (3) launch-authority token (FAIL CLOSED before any marker) --- #
    launch_authority_ok = os.environ.get(LAUNCH_AUTHORITY_TOKEN) == "1"
    if not launch_authority_ok:
        print(json.dumps({
            "status": "PHASE36_CLEAN_EQ_DIAGNOSTIC_V1_1_FAIL_CLOSED__LAUNCH_AUTHORITY_REQUIRED__NO_ATTEMPT_CONSUMED",
            "required_env": f"{LAUNCH_AUTHORITY_TOKEN}=1",
            "launch_authority_present": False,
            "attempt_consumed": False,
            "marker_created": False,
            "model_constructed": False,
            "checkpoint_loaded": False,
            "val_or_gt_read": False}, indent=1))
        return 5

    # ---- D45 (4) preserved prior-failure provenance gate ------------------ #
    prov = _prior_failure_provenance_state()
    if not prov["all_match"]:
        print(json.dumps({
            "status": "PHASE36_CLEAN_EQ_DIAGNOSTIC_V1_1_FAIL_CLOSED__PRIOR_FAILURE_PROVENANCE_NOT_BOUND__NO_ATTEMPT_CONSUMED",
            "provenance": prov,
            "attempt_consumed": False}, indent=1))
        return 6

    # ---- guard: never touch v1.14 science markers ------------------------- #
    touch_guard = {p.name: p.exists() for p in V14_SCIENCE_MARKERS}

    # ---- D45 (5) write-once start marker (authorized_attempt DERIVED) ----- #
    authorized_attempt = bool(
        os.environ.get(ONE_SHOT_ENV) == "1"
        and os.environ.get(LAUNCH_AUTHORITY_TOKEN) == "1"
        and not _attempt_already_consumed()
        and prov["all_match"]
        and prov["static_audit_verdict"] == REQUIRED_STATIC_AUDIT_VERDICT)
    if not authorized_attempt:
        print(json.dumps({
            "status": "PHASE36_CLEAN_EQ_DIAGNOSTIC_V1_1_FAIL_CLOSED__AUTHORIZATION_STATE_NOT_SATISFIED__NO_ATTEMPT_CONSUMED",
            "attempt_consumed": False}, indent=1))
        return 7

    _write_once_json(DIAGNOSTIC_START, {
        "artifact_kind": "PHASE36_CLEAN_EQ_DIAGNOSTIC_START",
        "revision": DIAGNOSTIC_REVISION,
        "attempted": True,
        "authorized_attempt": authorized_attempt,
        "authorization_derivation": "derived: one_shot_gate AND launch_authority_token AND no_prior_attempt AND prior_failure_provenance_bound AND static_audit_verdict==STATIC_ROOT_CAUSE_NOT_ESTABLISHED",
        "one_shot_gate_env": ONE_SHOT_ENV,
        "launch_authority_token_env": LAUNCH_AUTHORITY_TOKEN,
        "exact_diagnostic_source_sha256": sha256_file(Path(__file__)),
        "frozen_v1_14_exec_source_sha256": FROZEN_V1_14_EXEC_SHA,
        "frozen_v1_14_manifest_sha256": FROZEN_V1_14_MANIFEST_SHA,
        "prior_failure_provenance": prov,
        "v1_14_science_marker_presence_at_start": touch_guard,
        "automatic_retry": False,
        "overwrite_permitted": False,
        "scientific_output": False,
        "generated_utc": now(),
        "write_semantics": "O_CREAT|O_EXCL + full-write + fsync (exclusive-create, write-once)",
    })

    # ---- D45 (6) / D47 — GUARDED TERMINAL-EVIDENCE REGION ----------------- #
    #   BOTH run_diagnostic() AND the durable result write live INSIDE this
    #   try-block, so every terminal path after marker consumption attempts
    #   durable result/failure evidence.
    eq = None
    try:
        diag = run_diagnostic()
        eq = diag.get("clean_equivalence_full")
        _write_once_json(DIAGNOSTIC_RESULT, diag)
    except SystemExit as exc:
        _write_failure(termination_kind="SYSTEM_EXIT", exc_type="SystemExit",
                       exc_msg=str(exc.code), failing_stage="run_diagnostic",
                       eq=eq, marker_consumed=True)
        print(json.dumps({"status": "DIAGNOSTIC_TERMINATED", "message": str(exc.code)},
                         indent=1))
        return 1
    except BaseException as exc:  # noqa: BLE001
        _write_failure(termination_kind="EXCEPTION", exc_type=type(exc).__name__,
                       exc_msg=str(exc), failing_stage="run_diagnostic_or_result_write",
                       eq=eq, marker_consumed=True)
        traceback.print_exc()
        return 2

    print(json.dumps({
        "status": "DIAGNOSTIC_COMPLETE",
        "all_pass": diag["all_pass"],
        "diagnosis": diag["diagnosis"],
        "failing_checks": diag["failing_checks"],
        "result_path": str(DIAGNOSTIC_RESULT.relative_to(ROOT)),
        "result_sha256": sha256_file(DIAGNOSTIC_RESULT),
        "perturbation_executed": False,
        "scientific_output": False}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
