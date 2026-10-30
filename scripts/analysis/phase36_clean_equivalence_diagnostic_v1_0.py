#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 36 — CLEAN EQUIVALENCE DIAGNOSTIC v1.0.

PREPARED under Work Order H.  NOT executed as part of preparation.

WHY THIS EXISTS
---------------
The single authorized Phase36 v1.14 scientific robustness attempt (CONSUMED
2026-10-06) terminated at the CLEAN EQUIVALENCE gate with

    SystemExit("CLEAN_EQUIVALENCE_GATE_FAILED__STOP_BEFORE_PERTURBATION")

and defect D44 recorded that the FULL ``eq`` diagnostic object was NOT durably
preserved (only a generic failure artifact was written by
``_write_science_failure_artifact``).  The Step-2 targeted static audit returned
``STATIC_ROOT_CAUSE_NOT_ESTABLISHED`` — every equivalence dimension (Dice
definition, GT construction, C7/C8 threshold provenance, branch/safety
semantics, feature/runtime semantics) is statically PROVEN equivalent.

Therefore the root cause can only be resolved by a CLEAN DIAGNOSTIC
RE-EXECUTION that (a) reproduces the exact frozen clean pipeline, and (b)
DURABLY writes the complete ``eq`` object (per-check booleans, all mismatch
lists, all counters) so the failure is attributable without ambiguity.

WHAT THIS DOES
--------------
It imports the FROZEN v1.14 callables (never re-implements them) and runs ONLY
the clean scientific sequence — STEPS 1..7 below — with NO perturbation
execution whatsoever:

    STEP 1  _verify_transitive_source_integrity()          (fail closed)
    STEP 2  _load_models()                                  (CUDA fail-closed)
    STEP 3  _bind_clean_reference()                         (authority bind)
    STEP 4  _generate_clean_g_reference(ctx, counters)      (canonical G pass)
    STEP 5  _phase27_global_reproduction_gate(...)          (STOP on fail)
    STEP 6  808 x _evaluate_clean_sample(...)               (clean system eval)
    STEP 7  eq = _clean_equivalence_gate(...)               (DURABLE eq write)
    STEP 8  write the FULL eq durably (write-once result artifact)
    STEP 9  terminate (never proceed to image/proposal perturbation)

PROHIBITIONS (hard)
-------------------
* NEVER writes / touches any v1.14 science marker/result/failure artifact.
* NEVER executes image or proposal perturbations.
* NEVER modifies the frozen v1.14 source (imports it read-only).
* NEVER retries: write-once start marker guards a single attempt.
* One-shot gate: requires environment ``PHASE36_CLEAN_EQ_DIAGNOSTIC_EXECUTE=1``.

This artifact is DIAGNOSTIC.  ``scientific_output`` is False.  It does NOT
constitute a robustness result and MUST NOT be reported as one.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "scripts" / "analysis") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts" / "analysis"))

FROZEN_V1_14_SOURCE = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_14.py"
FROZEN_V1_14_EXEC_SHA = "ac09ff8ded3610244920e66612145b246b33127140d344a9730d454bab27cff5"
FROZEN_V1_14_MANIFEST_SHA = "b4c358dfcb5e7b59beb6ae1ba2cffc64677d10049e12568b4c8eea8e79bb911e"

DIAGNOSTIC_START = ROOT / "reports" / "audits" / "phase36_clean_equivalence_diagnostic_start_v1_0.json"
DIAGNOSTIC_RESULT = ROOT / "reports" / "audits" / "phase36_clean_equivalence_diagnostic_result_v1_0.json"
DIAGNOSTIC_FAILURE = ROOT / "reports" / "audits" / "phase36_clean_equivalence_diagnostic_failure_v1_0.json"

ONE_SHOT_ENV = "PHASE36_CLEAN_EQ_DIAGNOSTIC_EXECUTE"
DIAGNOSTIC_REVISION = "ra_medfilm_barr_phase36_clean_equivalence_diagnostic_v1_0"

# NEVER touched (guard: assert absence, then never write)
V14_SCIENCE_MARKERS = (
    ROOT / "reports" / "audits" / "phase36_robustness_science_start_v1_14.json",
    ROOT / "reports" / "audits" / "phase36_robustness_scientific_result_v1_14.json",
    ROOT / "reports" / "audits" / "phase36_robustness_science_failure_v1_14.json",
)


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def _import_frozen_v1_14():
    """Import the frozen v1.14 module by path (never mutating the source)."""
    if sha256_file(FROZEN_V1_14_SOURCE) != FROZEN_V1_14_EXEC_SHA:
        raise SystemExit(
            "PHASE36_CLEAN_EQ_DIAGNOSTIC_FAIL_CLOSED__FROZEN_V1_14_SOURCE_SHA_MISMATCH__NO_ATTEMPT_CONSUMED")
    spec = importlib.util.spec_from_file_location("_p36_v1_14_frozen_diag", FROZEN_V1_14_SOURCE)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_p36_v1_14_frozen_diag"] = mod
    spec.loader.exec_module(mod)
    return mod


def _write_once_json(path: Path, payload: dict) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    fd = os.open(str(path), flags, 0o644)
    try:
        os.write(fd, json.dumps(payload, indent=1, ensure_ascii=False,
                                default=str).encode("utf-8"))
    finally:
        os.close(fd)
    return True


def _attempt_already_consumed() -> bool:
    return any(p.exists() for p in (DIAGNOSTIC_START, DIAGNOSTIC_RESULT, DIAGNOSTIC_FAILURE))


def _write_failure(*, termination_kind, exc_type=None, exc_msg=None,
                   failing_stage=None, eq=None) -> None:
    if DIAGNOSTIC_FAILURE.exists():
        return
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
        "clean_equivalence_full": eq,
        "frozen_v1_14_exec_source_sha256": FROZEN_V1_14_EXEC_SHA,
        "scientific_output": False,
        "generated_utc": now(),
        "write_semantics": "O_CREAT|O_EXCL (exclusive-create, write-once)",
    }
    _write_once_json(DIAGNOSTIC_FAILURE, payload)


def run_diagnostic() -> dict:
    mod = _import_frozen_v1_14()
    counters = {}
    # Reuse the frozen OrderedDict counter scaffold if present.
    try:
        import phase36_robustness_common_v1_0 as C
        from collections import OrderedDict
        counters = OrderedDict((k, 0) for k in C.COUNTERS_REQUIRED)
        for k in C.COUNTERS_FOREVER_ZERO:
            counters[k] = 0
    except Exception:
        counters = {}

    stages: dict = {}
    eq = None

    # STEP 1 — transitive runtime source integrity (fail closed)
    si = mod._verify_transitive_source_integrity()
    stages["step1_source_integrity_all_match"] = bool(si.get("all_match"))
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

    # STEP 7 — strict clean-equivalence gate  (DURABLE eq capture — the D44 repair)
    eq = mod._clean_equivalence_gate(clean_ref_bound, generated, counters)
    stages["step7_clean_equivalence"] = eq

    # ---- DIAGNOSTIC OUTCOME ------------------------------------------------ #
    all_pass = bool(eq.get("all_pass"))
    diag = {
        "artifact_kind": "PHASE36_CLEAN_EQUIVALENCE_DIAGNOSTIC_RESULT",
        "revision": DIAGNOSTIC_REVISION,
        "purpose": "DURABLE_CLEAN_EQUIVALENCE_DIAGNOSTIC__D44_REPAIR",
        "execution_scope": "CLEAN_ONLY__STEPS_1_THROUGH_7__NO_PERTURBATION",
        "frozen_v1_14_exec_source_sha256": FROZEN_V1_14_EXEC_SHA,
        "frozen_v1_14_manifest_sha256": FROZEN_V1_14_MANIFEST_SHA,
        "clean_equivalence_full": eq,
        "stages": stages,
        "counters": dict(counters),
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
        "write_semantics": "O_CREAT|O_EXCL (exclusive-create, write-once)",
    }
    return diag


def main() -> int:
    # ---- one-shot gate ---------------------------------------------------- #
    if os.environ.get(ONE_SHOT_ENV) != "1":
        print(json.dumps({
            "status": "REFUSED__ONE_SHOT_GATE_NOT_SET",
            "required_env": f"{ONE_SHOT_ENV}=1",
            "attempt_consumed": False}, indent=1))
        return 3

    if _attempt_already_consumed():
        print(json.dumps({
            "status": "REFUSED__DIAGNOSTIC_ATTEMPT_ALREADY_CONSUMED",
            "automatic_retry": False,
            "attempt_consumed": False}, indent=1))
        return 4

    # ---- hard guard: never touch v1.14 science markers -------------------- #
    if any(p.exists() for p in V14_SCIENCE_MARKERS):
        touch_guard = {str(p.name): p.exists() for p in V14_SCIENCE_MARKERS}
    else:
        touch_guard = {str(p.name): False for p in V14_SCIENCE_MARKERS}

    # ---- write-once start marker ------------------------------------------ #
    _write_once_json(DIAGNOSTIC_START, {
        "artifact_kind": "PHASE36_CLEAN_EQUIVALENCE_DIAGNOSTIC_START",
        "revision": DIAGNOSTIC_REVISION,
        "attempted": True,
        "authorized_attempt": True,
        "frozen_v1_14_exec_source_sha256": FROZEN_V1_14_EXEC_SHA,
        "frozen_v1_14_manifest_sha256": FROZEN_V1_14_MANIFEST_SHA,
        "v1_14_science_marker_presence_at_start": touch_guard,
        "automatic_retry": False,
        "overwrite_permitted": False,
        "scientific_output": False,
        "generated_utc": now(),
        "write_semantics": "O_CREAT|O_EXCL (exclusive-create, write-once)",
    })

    try:
        diag = run_diagnostic()
    except SystemExit as exc:
        _write_failure(termination_kind="SYSTEM_EXIT", exc_type="SystemExit",
                       exc_msg=str(exc.code), failing_stage="run_diagnostic")
        print(json.dumps({"status": "DIAGNOSTIC_TERMINATED", "message": str(exc.code)},
                         indent=1))
        return 1
    except BaseException as exc:  # noqa: BLE001
        _write_failure(termination_kind="EXCEPTION", exc_type=type(exc).__name__,
                       exc_msg=str(exc), failing_stage="run_diagnostic",
                       eq=None)
        traceback.print_exc()
        return 2

    _write_once_json(DIAGNOSTIC_RESULT, diag)
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
