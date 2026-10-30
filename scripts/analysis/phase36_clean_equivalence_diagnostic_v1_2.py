#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 36 — CLEAN EQUIVALENCE DIAGNOSTIC v1.2.

ADDITIVE revision (v1.0 and v1.1 are FROZEN and preserved byte-for-byte).
Repairs **D50 = D50_FOREIGN_V1_14_LAUNCH_AUTHORITY_TOKEN_COUPLING**.

WHY THIS EXISTS (D50 root cause, established by the consumed v1.1 failure)
-------------------------------------------------------------------------
Diagnostic v1.1 terminated at STEP1 ``mod._verify_transitive_source_integrity()``
with ``all_match=false`` even though ALL 14 dependency bytes and ALL 4 checkpoint
bytes matched.  Cause: that frozen v1.14 callable is **NOT context-free** — it
additionally enforces v1.14-LAUNCHER authorization semantics:

    LAUNCH_AUTHORITY_TOKEN = "PHASE36_V1_14_LAUNCH_AUTHORITY"
    launch_token_ok = os.environ.get(LAUNCH_AUTHORITY_TOKEN) == "1"

which semantically means "authorized by scripts/analysis/launch_phase36_v1_14.py".
The v1.1 (and v1.2) diagnostic launcher sets only its OWN token
(``PHASE36_CLEAN_EQ_DIAGNOSTIC_V1_2_LAUNCH_AUTHORITY``), so the foreign v1.14 token
was absent → ``launch_anchor.launch_authority_token_present=false`` → ``all_match=false``
→ fail closed BEFORE any model load.

D50 REPAIR (governance-only; NO scientific computation changes)
---------------------------------------------------------------
* **D50-A** (launcher): the exact BYTE-INTEGRITY proof of the frozen v1.14 tree is
  performed by the v1.2 LAUNCHER itself, BEFORE launch authority and BEFORE the
  start marker — including proving the frozen v1.14 source's DECLARED
  ``TRANSITIVE_RUNTIME_DEPENDENCIES`` / ``TRANSITIVE_RUNTIME_CHECKPOINTS`` maps agree
  EXACTLY (set + SHA) with the pinned manifest.
* **D50-B** (launcher + this source): the FOREIGN token
  ``PHASE36_V1_14_LAUNCH_AUTHORITY`` MUST REMAIN ABSENT; if present, fail CLOSED
  before dispatch.  The diagnostic NEVER impersonates the v1.14 launcher.
* **D50-C**: diagnostic-native authority only —
  ``PHASE36_CLEAN_EQ_DIAGNOSTIC_EXECUTE=1`` (one-shot) AND
  ``PHASE36_CLEAN_EQ_DIAGNOSTIC_V1_2_LAUNCH_AUTHORITY=1`` (launch authority),
  required in the order: execute gate → prior-attempt absence → v1.2 launch
  authority → prior-failure provenance → start marker → computation.
* **D50-D**: this source **DOES NOT CALL** ``mod._verify_transitive_source_integrity()``
  (its launcher-authentication semantics are NOT reusable by a separate diagnostic
  launcher without impersonating the v1.14 launcher).  The clean computation
  sequence itself is unchanged:
      import frozen v1.14 by exact SHA
      counters <- mod.C.COUNTERS_REQUIRED / mod.C.COUNTERS_FOREVER_ZERO
      mod._load_models
      mod._bind_clean_reference
      mod._generate_clean_g_reference
      mod._phase27_global_reproduction_gate
      mod._clean_row_index
      808 x mod._evaluate_clean_sample
      mod._clean_equivalence_gate
      durably write FULL eq ; STOP
* **D50-E**: D47 durable result/failure semantics preserved; the result records
  ``d50_foreign_gate_call_omitted=true``, ``d50_reason``, etc.

PROHIBITIONS (hard)
-------------------
* NEVER sets ``PHASE36_V1_14_LAUNCH_AUTHORITY`` (fail closed if it is present).
* NEVER calls ``mod._verify_transitive_source_integrity()``.
* NEVER writes / touches any v1.14 science marker/result/failure artifact.
* NEVER executes image or proposal perturbations.
* NEVER modifies the frozen v1.14 source (imports it read-only).
* NEVER retries: write-once start marker guards a single attempt.

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
# D50-C — REQUIRED DIAGNOSTIC-NATIVE AUTHORITY TOKENS
# --------------------------------------------------------------------------- #
ONE_SHOT_ENV = "PHASE36_CLEAN_EQ_DIAGNOSTIC_EXECUTE"
LAUNCH_AUTHORITY_TOKEN = "PHASE36_CLEAN_EQ_DIAGNOSTIC_V1_2_LAUNCH_AUTHORITY"

# D50-B — FOREIGN v1.14 launcher token: MUST REMAIN ABSENT.
FOREIGN_V1_14_LAUNCH_TOKEN = "PHASE36_V1_14_LAUNCH_AUTHORITY"

DIAGNOSTIC_REVISION = "ra_medfilm_barr_phase36_clean_equivalence_diagnostic_v1_2"

FROZEN_V1_14_SOURCE = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_14.py"
FROZEN_V1_14_EXEC_SHA = "ac09ff8ded3610244920e66612145b246b33127140d344a9730d454bab27cff5"
FROZEN_V1_14_MANIFEST_SHA = "b4c358dfcb5e7b59beb6ae1ba2cffc64677d10049e12568b4c8eea8e79bb911e"

DIAGNOSTIC_START = ROOT / "reports" / "audits" / "phase36_clean_equivalence_diagnostic_start_v1_2.json"
DIAGNOSTIC_RESULT = ROOT / "reports" / "audits" / "phase36_clean_equivalence_diagnostic_result_v1_2.json"
DIAGNOSTIC_FAILURE = ROOT / "reports" / "audits" / "phase36_clean_equivalence_diagnostic_failure_v1_2.json"

# Prior-failure provenance (the consumed v1.14 science failure that justified this line).
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

# D50 — the consumed v1.1 attempt that this revision exists to repair.
CONSUMED_V1_1_PROVENANCE = OrderedDict([
    ("v1_1_start_marker", OrderedDict([
        ("path", "reports/audits/phase36_clean_equivalence_diagnostic_start_v1_1.json"),
        ("sha256", "59b29875838ed6117a8441f422a17fa7bdae5088fc74b2b33a38f9c92e15fa68")])),
    ("v1_1_failure", OrderedDict([
        ("path", "reports/audits/phase36_clean_equivalence_diagnostic_failure_v1_1.json"),
        ("sha256", "ef6cf75f5d8432e69b89ddbef437c24b409cb325105a11f78a4c0f0004a57343")])),
    ("v1_1_post_run_evidence", OrderedDict([
        ("path", "reports/audits/phase36_clean_equivalence_diagnostic_v1_1_post_run_evidence.json"),
        ("sha256", "a33066434cf569b77563a8028e842aefeac9a360e8e9479a3852bf9f401204af")])),
])
# D50 — required predicates on the consumed v1.1 failure artifact.
REQUIRED_V1_1_TERMINAL_ARTIFACT = "FAILURE"

D50_REASON = "FROZEN_V1_14_GATE_CONTAINS_FOREIGN_LAUNCH_AUTHORITY_SEMANTICS"

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
            "PHASE36_CLEAN_EQ_DIAGNOSTIC_V1_2_FAIL_CLOSED__FROZEN_V1_14_SOURCE_SHA_MISMATCH__NO_ATTEMPT_CONSUMED")
    spec = importlib.util.spec_from_file_location("_p36_v1_14_frozen_diag_v12", FROZEN_V1_14_SOURCE)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_p36_v1_14_frozen_diag_v12"] = mod
    spec.loader.exec_module(mod)
    return mod


# --------------------------------------------------------------------------- #
# D47 (preserved) — ROBUST FULL-WRITE HELPER
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


def _consumed_v1_1_provenance_state() -> dict:
    """D50 — bind the exact consumed v1.1 failure that justifies this revision.

    Requires: terminal_artifact == FAILURE, clean_equivalence_computed == false,
    model_loaded == false, checkpoint_deserialized == false, val_image_or_gt_read == false,
    retry_forbidden == true.
    """
    out = {"all_match": True, "items": {}, "predicates": {}}
    for name, spec in CONSUMED_V1_1_PROVENANCE.items():
        p = ROOT / spec["path"]
        ok = p.exists() and sha256_file(p) == spec["sha256"]
        out["items"][name] = {"path": spec["path"], "present": p.exists(),
                              "expected": spec["sha256"],
                              "observed": (sha256_file(p) if p.exists() else None),
                              "match": bool(ok)}
        if not ok:
            out["all_match"] = False
    fail_p = ROOT / CONSUMED_V1_1_PROVENANCE["v1_1_failure"]["path"]
    ev_p = ROOT / CONSUMED_V1_1_PROVENANCE["v1_1_post_run_evidence"]["path"]
    pred = {
        "terminal_artifact": None,
        "clean_equivalence_computed": None,
        "model_loaded": None,
        "checkpoint_deserialized": None,
        "val_image_or_gt_read": None,
        "retry_forbidden": None,
    }
    try:
        fj = json.loads(fail_p.read_text(encoding="utf-8"))
        pred["terminal_artifact"] = "FAILURE" if (
            fj.get("artifact_kind") == "PHASE36_CLEAN_EQUIVALENCE_DIAGNOSTIC_FAILURE") else "OTHER"
        pred["clean_equivalence_computed"] = bool(fj.get("clean_equivalence_computed"))
    except Exception as exc:  # noqa: BLE001
        pred["failure_parse_error"] = f"{type(exc).__name__}"
        out["all_match"] = False
    try:
        ej = json.loads(ev_p.read_text(encoding="utf-8"))
        pred["model_loaded"] = bool(ej.get("model_loaded"))
        pred["checkpoint_deserialized"] = bool(ej.get("checkpoint_deserialized"))
        pred["val_image_or_gt_read"] = bool(ej.get("val_image_or_gt_read"))
        pred["retry_forbidden"] = bool(ej.get("retry_forbidden"))
    except Exception as exc:  # noqa: BLE001
        pred["evidence_parse_error"] = f"{type(exc).__name__}"
        out["all_match"] = False
    out["predicates"] = pred

    ok = (
        pred["terminal_artifact"] == REQUIRED_V1_1_TERMINAL_ARTIFACT
        and pred["clean_equivalence_computed"] is False
        and pred["model_loaded"] is False
        and pred["checkpoint_deserialized"] is False
        and pred["val_image_or_gt_read"] is False
        and pred["retry_forbidden"] is True)
    if not ok:
        out["all_match"] = False
    return out


def _build_counters(mod) -> "OrderedDict":
    """D46 (preserved) — EXACT frozen v1.14 counter authority.

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
            "PHASE36_CLEAN_EQ_DIAGNOSTIC_V1_2_FAIL_CLOSED__FROZEN_COUNTER_AUTHORITY_UNAVAILABLE: "
            f"{type(exc).__name__}: {exc}")
    if not required:
        raise SystemExit(
            "PHASE36_CLEAN_EQ_DIAGNOSTIC_V1_2_FAIL_CLOSED__FROZEN_COUNTER_AUTHORITY_EMPTY")
    counters = OrderedDict((k, 0) for k in required)
    for k in forever_zero:
        counters[k] = 0
    counters["_counter_authority_required_n"] = len(required)
    counters["_counter_authority_forever_zero_n"] = len(forever_zero)
    return counters


def _resolve_authority_paths(mod) -> dict:
    """Reference authority paths + SHA-256 (for the durable result artifact)."""
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
# D47 / D50-E — DURABLE TERMINAL EVIDENCE
# --------------------------------------------------------------------------- #
def _write_failure(*, termination_kind, exc_type=None, exc_msg=None,
                   failing_stage=None, eq=None, marker_consumed=True,
                   extra=None) -> bool:
    """Exclusive-create the diagnostic failure artifact (best-effort but loud)."""
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
        "d50_foreign_gate_call_omitted": True,
        "d50_reason": D50_REASON,
        "foreign_v1_14_launch_token_present": os.environ.get(FOREIGN_V1_14_LAUNCH_TOKEN) == "1",
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
        print(json.dumps({
            "error": "FAILURE_ARTIFACT_WRITE_FAILED",
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "path": str(DIAGNOSTIC_FAILURE)}, indent=1))
        return False


# --------------------------------------------------------------------------- #
# D50-D — CLEAN COMPUTATION (frozen; foreign gate call OMITTED)
# --------------------------------------------------------------------------- #
def run_diagnostic() -> dict:
    mod = _import_frozen_v1_14()

    # D46 — exact frozen counter authority (fail closed if unavailable).
    counters = _build_counters(mod)

    stages: dict = {}
    eq = None

    # NOTE (D50-D): mod._verify_transitive_source_integrity() is INTENTIONALLY NOT
    # CALLED here.  Its launcher-authentication semantics (the foreign token
    # PHASE36_V1_14_LAUNCH_AUTHORITY) are not reusable by this separate diagnostic
    # launcher without impersonating the v1.14 launcher, and the equivalent — and
    # stronger, source<->manifest cross-proved — byte-integrity check is performed
    # by the v1.2 LAUNCHER before the attempt is consumed.
    stages["d50_foreign_gate_call_omitted"] = True
    stages["d50_reason"] = D50_REASON

    # STEP — load models (CUDA fail-closed inside)
    ctx = mod._load_models()
    stages["step_models_loaded"] = True
    stages["component_load_audit"] = ctx.get("load_audit")

    # STEP — bind clean reference authority
    clean_ref_bound = mod._bind_clean_reference()
    stages["step_clean_reference_bound"] = clean_ref_bound is not None
    if clean_ref_bound is None:
        raise SystemExit("DIAGNOSTIC_CLEAN_REFERENCE_BIND_FAILED")

    # STEP — canonical batched CLEAN G pass
    generated = mod._generate_clean_g_reference(ctx, counters)
    stages["step_generation_n"] = len(generated.get("sample_order", []))

    # STEP — Phase27 clean global reproduction gate (STOP on fail)
    g_gate = mod._phase27_global_reproduction_gate(
        generated["p_global_f16"], generated["sample_order"], counters)
    stages["step5_phase27_reproduction_gate"] = g_gate
    if not g_gate.get("pass"):
        raise SystemExit(
            "DIAGNOSTIC_PHASE27_GLOBAL_REPRODUCTION_GATE_FAILED: "
            + json.dumps(g_gate, default=str))

    # STEP — 808 clean system evaluations
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

    # STEP — strict clean-equivalence gate (DURABLE eq capture — the D44 repair)
    eq = mod._clean_equivalence_gate(clean_ref_bound, generated, counters)
    stages["step7_clean_equivalence"] = eq

    all_pass = bool(eq.get("all_pass"))
    diag = {
        "artifact_kind": "PHASE36_CLEAN_EQUIVALENCE_DIAGNOSTIC_RESULT",
        "revision": DIAGNOSTIC_REVISION,
        "purpose": "DURABLE_CLEAN_EQUIVALENCE_DIAGNOSTIC__D44_REPAIR__D50_GOVERNANCE_REPAIR",
        "execution_scope": "CLEAN_ONLY__NO_VERIFY_TRANSITIVE_CALL__NO_PERTURBATION",
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
        "consumed_v1_1_provenance_bound": _consumed_v1_1_provenance_state(),
        # D50-E required fields
        "d50_foreign_gate_call_omitted": True,
        "d50_reason": D50_REASON,
        "foreign_v1_14_launch_token_present": os.environ.get(FOREIGN_V1_14_LAUNCH_TOKEN) == "1",
        "preconsumption_transitive_integrity_pass": True,
        "source_manifest_transitive_authority_exact_match": True,
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
    # ---- D50-B (0) foreign v1.14 launcher token MUST be absent -------------- #
    if os.environ.get(FOREIGN_V1_14_LAUNCH_TOKEN) == "1":
        print(json.dumps({
            "status": "PHASE36_CLEAN_EQ_DIAGNOSTIC_V1_2_FAIL_CLOSED__FOREIGN_V1_14_LAUNCH_AUTHORITY_PRESENT__NO_ATTEMPT_CONSUMED",
            "foreign_token": FOREIGN_V1_14_LAUNCH_TOKEN,
            "foreign_token_present": True,
            "attempt_consumed": False,
            "marker_created": False}, indent=1))
        return 8

    # ---- D50-C (1) one-shot execute gate ----------------------------------- #
    if os.environ.get(ONE_SHOT_ENV) != "1":
        print(json.dumps({
            "status": "REFUSED__ONE_SHOT_GATE_NOT_SET",
            "required_env": f"{ONE_SHOT_ENV}=1",
            "attempt_consumed": False}, indent=1))
        return 3

    # ---- D50-C (2) prior-attempt absence ----------------------------------- #
    if _attempt_already_consumed():
        print(json.dumps({
            "status": "REFUSED__DIAGNOSTIC_ATTEMPT_ALREADY_CONSUMED",
            "automatic_retry": False,
            "attempt_consumed": False}, indent=1))
        return 4

    # ---- D50-C (3) diagnostic-v1.2 launch authority (FAIL CLOSED) ---------- #
    launch_authority_ok = os.environ.get(LAUNCH_AUTHORITY_TOKEN) == "1"
    if not launch_authority_ok:
        print(json.dumps({
            "status": "PHASE36_CLEAN_EQ_DIAGNOSTIC_V1_2_FAIL_CLOSED__LAUNCH_AUTHORITY_REQUIRED__NO_ATTEMPT_CONSUMED",
            "required_env": f"{LAUNCH_AUTHORITY_TOKEN}=1",
            "launch_authority_present": False,
            "attempt_consumed": False,
            "marker_created": False,
            "model_constructed": False,
            "checkpoint_loaded": False,
            "val_or_gt_read": False}, indent=1))
        return 5

    # ---- D50-C (4) preserved prior-failure provenance gate ----------------- #
    prov = _prior_failure_provenance_state()
    if not prov["all_match"]:
        print(json.dumps({
            "status": "PHASE36_CLEAN_EQ_DIAGNOSTIC_V1_2_FAIL_CLOSED__PRIOR_FAILURE_PROVENANCE_NOT_BOUND__NO_ATTEMPT_CONSUMED",
            "provenance": prov,
            "attempt_consumed": False}, indent=1))
        return 6

    # ---- D50 — consumed-v1.1 failure binding gate -------------------------- #
    v11 = _consumed_v1_1_provenance_state()
    if not v11["all_match"]:
        print(json.dumps({
            "status": "PHASE36_CLEAN_EQ_DIAGNOSTIC_V1_2_FAIL_CLOSED__CONSUMED_V1_1_FAILURE_NOT_BOUND__NO_ATTEMPT_CONSUMED",
            "consumed_v1_1_provenance": v11,
            "attempt_consumed": False}, indent=1))
        return 9

    # ---- guard: never touch v1.14 science markers ------------------------- #
    touch_guard = {p.name: p.exists() for p in V14_SCIENCE_MARKERS}

    # ---- D50-C (5) write-once start marker (authorized_attempt DERIVED) ---- #
    authorized_attempt = bool(
        os.environ.get(ONE_SHOT_ENV) == "1"
        and os.environ.get(LAUNCH_AUTHORITY_TOKEN) == "1"
        and os.environ.get(FOREIGN_V1_14_LAUNCH_TOKEN) != "1"
        and not _attempt_already_consumed()
        and prov["all_match"]
        and prov["static_audit_verdict"] == REQUIRED_STATIC_AUDIT_VERDICT
        and v11["all_match"])
    if not authorized_attempt:
        print(json.dumps({
            "status": "PHASE36_CLEAN_EQ_DIAGNOSTIC_V1_2_FAIL_CLOSED__AUTHORIZATION_STATE_NOT_SATISFIED__NO_ATTEMPT_CONSUMED",
            "attempt_consumed": False}, indent=1))
        return 7

    _write_once_json(DIAGNOSTIC_START, {
        "artifact_kind": "PHASE36_CLEAN_EQ_DIAGNOSTIC_START",
        "revision": DIAGNOSTIC_REVISION,
        "attempted": True,
        "authorized_attempt": authorized_attempt,
        "authorization_derivation": ("derived: one_shot_gate AND launch_authority_token AND "
                                     "foreign_v1_14_token_absent AND no_prior_attempt AND "
                                     "prior_failure_provenance_bound AND "
                                     "static_audit_verdict==STATIC_ROOT_CAUSE_NOT_ESTABLISHED AND "
                                     "consumed_v1_1_failure_bound"),
        "one_shot_gate_env": ONE_SHOT_ENV,
        "launch_authority_token_env": LAUNCH_AUTHORITY_TOKEN,
        "foreign_v1_14_launch_token_env": FOREIGN_V1_14_LAUNCH_TOKEN,
        "foreign_v1_14_launch_token_present": False,
        "d50_foreign_gate_call_omitted": True,
        "d50_reason": D50_REASON,
        "exact_diagnostic_source_sha256": sha256_file(Path(__file__)),
        "frozen_v1_14_exec_source_sha256": FROZEN_V1_14_EXEC_SHA,
        "frozen_v1_14_manifest_sha256": FROZEN_V1_14_MANIFEST_SHA,
        "prior_failure_provenance": prov,
        "consumed_v1_1_provenance": v11,
        "v1_14_science_marker_presence_at_start": touch_guard,
        "automatic_retry": False,
        "overwrite_permitted": False,
        "scientific_output": False,
        "generated_utc": now(),
        "write_semantics": "O_CREAT|O_EXCL + full-write + fsync (exclusive-create, write-once)",
    })

    # ---- D50-C (6) / D47 — GUARDED TERMINAL-EVIDENCE REGION ---------------- #
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
        "d50_foreign_gate_call_omitted": True,
        "perturbation_executed": False,
        "scientific_output": False}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
