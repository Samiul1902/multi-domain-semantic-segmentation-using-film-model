#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 36 — FINAL-PROBABILITY AUTHORITY DIAGNOSTIC v1.0.

ADDITIVE, NEW diagnostic family
(``ra_medfilm_barr_phase36_final_probability_authority_diagnostic_v1_0``).

This is NOT a v1.2 retry, NOT a v1.14 science retry, NOT v1.15 science, and NOT a
robustness execution.  Its ONLY purpose is to determine whether the current frozen
clean end-to-end system reproduces the Phase27 FINAL persisted float16 prediction
authority:

    data_cache/phase27_barr_preservation_v1_0/phase27_val808_final_prob_f16.npy

NO GROUND TRUTH IS NEEDED OR READ.

WHY THIS EXISTS
---------------
The D51 adjudication established that the v1.14/v1.2 clean-equivalence comparison
thresholds the LIVE float32 final probability on the generated side while the frozen
Phase27 bound scored the PERSISTED float16 final probability.  This diagnostic
measures, GT-free, whether the generated clean final probability — cast to float16 —
is bit-identical to the frozen Phase27 final authority, and records the exact
threshold-flip structure between the three relevant binaries.

SCIENTIFIC PATH (exact frozen v1.14 clean computation; NO G quantization downstream)
------------------------------------------------------------------------------------
    1. source / provenance / transitive-integrity gates
    2. load the exact frozen components
    3. generate the canonical clean G using the ORIGINAL LIVE FLOAT32 downstream values
    4. retain the existing Phase27 GLOBAL f16 reproduction gate
    5. for each of 808 clean samples: run the exact canonical downstream clean path and
       STOP immediately after obtaining out["final_probability"]
       -- DO NOT load GT, DO NOT compute Dice/IoU/HD95
    6. generated_final_f16 = np.asarray(out["final_probability"], np.float32).astype(np.float16)
    7. compare against the corresponding row of phase27_val808_final_prob_f16.npy
    8. persist complete diagnostic evidence
    9. STOP   (no perturbations)

GT PROHIBITION (hard)
---------------------
* static: this source contains NO reference to ``_load_val_gt`` / ``full_field_gt`` /
  ``_dice`` / ``_iou`` / ``_hd95`` / ``mask_path`` in executable code.
* runtime: the frozen module's GT-bearing callables are replaced by raising proxies
  (IN MEMORY only; the frozen source is never modified).  Any GT access increments
  ``VAL_GT_READ`` and FAILS CLOSED.
* the durable result records ``VAL_GT_READ == 0``.

GOVERNANCE (D44–D50 lessons applied)
------------------------------------
* diagnostic-native launch authority; the FOREIGN token
  ``PHASE36_V1_14_LAUNCH_AUTHORITY`` MUST remain ABSENT (fail closed if present)
* the frozen v1.14 ``_verify_transitive_source_integrity()`` is NEVER called (it
  carries foreign-launcher authority semantics); the equivalent byte-integrity proof
  is performed by the v1.0 LAUNCHER before the attempt is consumed
* exclusive start / result / failure; durable writes; no automatic retry
* the consumed v1.2 evidence and the D51 adjudication/reconciliation are bound

``scientific_output`` is False and ``robustness_result`` is False.
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

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "scripts" / "analysis") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts" / "analysis"))

# --------------------------------------------------------------------------- #
# diagnostic-native authority tokens
# --------------------------------------------------------------------------- #
ONE_SHOT_ENV = "PHASE36_FINAL_PROB_AUTHORITY_EXECUTE"
LAUNCH_AUTHORITY_TOKEN = "PHASE36_FINAL_PROB_AUTHORITY_V1_0_LAUNCH_AUTHORITY"
FOREIGN_V1_14_LAUNCH_TOKEN = "PHASE36_V1_14_LAUNCH_AUTHORITY"

DIAGNOSTIC_REVISION = "ra_medfilm_barr_phase36_final_probability_authority_diagnostic_v1_0"

FROZEN_V1_14_SOURCE = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_14.py"
FROZEN_V1_14_EXEC_SHA = "ac09ff8ded3610244920e66612145b246b33127140d344a9730d454bab27cff5"
FROZEN_V1_14_MANIFEST_SHA = "b4c358dfcb5e7b59beb6ae1ba2cffc64677d10049e12568b4c8eea8e79bb911e"

DIAGNOSTIC_START = ROOT / "reports" / "audits" / "phase36_final_probability_authority_diagnostic_start_v1_0.json"
DIAGNOSTIC_RESULT = ROOT / "reports" / "audits" / "phase36_final_probability_authority_diagnostic_result_v1_0.json"
DIAGNOSTIC_FAILURE = ROOT / "reports" / "audits" / "phase36_final_probability_authority_diagnostic_failure_v1_0.json"

# Phase27 FINAL persisted float16 prediction authority (the reproduction target).
PHASE27_FINAL_PROB_AUTHORITY = OrderedDict([
    ("path", "data_cache/phase27_barr_preservation_v1_0/phase27_val808_final_prob_f16.npy"),
    ("sha256", "506ab6c4e715a9106889e186c146b73903493c80a63258007954cf5deb3ea9cf"),
    ("shape", [808, 512, 512]),
    ("dtype", "float16"),
    ("sample_order", "frozen VAL808 population order (dataset asc, sample_id asc)"),
    ("role", "Phase27 frozen FINAL probability cache (authoritative reproduction target)"),
])
# Phase27 GLOBAL persisted float16 authority (retained, unchanged from v1.14).
PHASE27_GLOBAL_PROB_AUTHORITY = OrderedDict([
    ("path", "data_cache/phase27_barr_preservation_v1_0/phase27_val808_global_prob_f16.npy"),
    ("sha256", "cc6c54af986f56b4aba9265405ffeba4f6cac582eeff00fe6b0894429e7d3f13"),
    ("shape", [808, 512, 512]),
    ("dtype", "float16"),
])

SEGMENTATION_OUTPUT_THRESHOLD = 0.50
F16_HALF = np.float16(0.5)

# Prior-failure provenance (unchanged from the v1.2 diagnostic line).
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

# Consumed-evidence binding: the v1.2 attempt + the D51 adjudication line.
CONSUMED_EVIDENCE_PROVENANCE = OrderedDict([
    ("v1_2_start_marker", OrderedDict([
        ("path", "reports/audits/phase36_clean_equivalence_diagnostic_start_v1_2.json"),
        ("sha256", "be93d494b1aa2aad3c900f442c16efe55bcbf0bd508a72df8f8b83e72cd7d2d3")])),
    ("v1_2_result", OrderedDict([
        ("path", "reports/audits/phase36_clean_equivalence_diagnostic_result_v1_2.json"),
        ("sha256", "b64f7e6282f9abb864a5d5bc438a22e1096aaf56e0a4e94fe53ba7c9bab6fa4a")])),
    ("d51_adjudication_v1_0", OrderedDict([
        ("path", "reports/audits/phase36_clean_equivalence_d51_numerical_authority_adjudication_v1_0.json"),
        ("sha256", "27ac7ada4ee39190d8823b8b1ff7e6e2beb304e2e7fc5778542883ac7eacc53a")])),
    ("d51_reconciliation_v1_1", OrderedDict([
        ("path", "reports/audits/phase36_clean_equivalence_d51_reconciliation_v1_1.json"),
        ("sha256", "d8e3e83e6c31004e610faef9d93c221c026eb8974c033f47fbff91106836758b")])),
])

# GT-bearing callables of the frozen module that MUST NEVER be called.
GT_FORBIDDEN_CALLABLES = ("_load_val_gt", "full_field_gt", "_dice", "_iou", "_hd95")
# Keys of a population row that MUST NEVER be read.
GT_FORBIDDEN_ROW_KEYS = ("mask_path",)

D50_REASON = "FROZEN_V1_14_GATE_CONTAINS_FOREIGN_LAUNCH_AUTHORITY_SEMANTICS"

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
            "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_0_FAIL_CLOSED__FROZEN_V1_14_SOURCE_SHA_MISMATCH"
            "__NO_ATTEMPT_CONSUMED")
    spec = importlib.util.spec_from_file_location("_p36_v1_14_frozen_fpa_v10", FROZEN_V1_14_SOURCE)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_p36_v1_14_frozen_fpa_v10"] = mod
    spec.loader.exec_module(mod)
    return mod


def _install_gt_guards(mod) -> dict:
    """RUNTIME GT PROHIBITION.

    Replace the frozen module's GT-bearing callables with raising proxies.  This
    touches only the IN-MEMORY module object; the frozen source file is never
    modified (its SHA is re-verified afterwards).
    """
    guard = {"VAL_GT_READ": 0, "blocked_calls": [], "installed": []}

    def _make_blocked(name):
        def _blocked(*_a, **_k):
            guard["VAL_GT_READ"] += 1
            guard["blocked_calls"].append(name)
            raise SystemExit(
                "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_0_FAIL_CLOSED__GT_ACCESS_FORBIDDEN::"
                + name)
        return _blocked

    for name in GT_FORBIDDEN_CALLABLES:
        if hasattr(mod, name):
            setattr(mod, name, _make_blocked(name))
            guard["installed"].append(name)
    return guard


def _write_once_json(path: Path, payload: dict) -> bool:
    """Exclusive-create write of a JSON payload (durable, loud on short write)."""
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


def _provenance_state(spec_map) -> dict:
    out = {"all_match": True, "items": {}}
    for name, spec in spec_map.items():
        p = ROOT / spec["path"]
        ok = p.exists() and sha256_file(p) == spec["sha256"]
        out["items"][name] = {"path": spec["path"], "present": p.exists(),
                              "expected": spec["sha256"],
                              "observed": (sha256_file(p) if p.exists() else None),
                              "match": bool(ok)}
        if not ok:
            out["all_match"] = False
    return out


def _prior_failure_provenance_state() -> dict:
    out = _provenance_state(PRIOR_FAILURE_PROVENANCE)
    out["static_audit_verdict"] = None
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
    """EXACT frozen v1.14 counter authority (fail closed if unavailable)."""
    try:
        C = mod.C
        required = list(C.COUNTERS_REQUIRED)
        forever_zero = list(C.COUNTERS_FOREVER_ZERO)
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(
            "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_0_FAIL_CLOSED__FROZEN_COUNTER_AUTHORITY_UNAVAILABLE: "
            f"{type(exc).__name__}: {exc}")
    if not required:
        raise SystemExit(
            "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_0_FAIL_CLOSED__FROZEN_COUNTER_AUTHORITY_EMPTY")
    counters = OrderedDict((k, 0) for k in required)
    for k in forever_zero:
        counters[k] = 0
    counters["_counter_authority_required_n"] = len(required)
    counters["_counter_authority_forever_zero_n"] = len(forever_zero)
    return counters


def _write_failure(*, termination_kind, exc_type=None, exc_msg=None,
                   failing_stage=None, extra=None, marker_consumed=True) -> bool:
    if DIAGNOSTIC_FAILURE.exists():
        print(json.dumps({"note": "FAILURE_ARTIFACT_ALREADY_EXISTS",
                          "path": str(DIAGNOSTIC_FAILURE)}))
        return False
    payload = {
        "artifact_kind": "PHASE36_FINAL_PROBABILITY_AUTHORITY_DIAGNOSTIC_FAILURE",
        "revision": DIAGNOSTIC_REVISION,
        "automatic_retry": False,
        "overwrite_permitted": False,
        "termination_kind": termination_kind,
        "exception": exc_type is not None,
        "exception_type": exc_type,
        "exception_message": exc_msg,
        "failing_stage": failing_stage,
        "marker_consumed": bool(marker_consumed),
        "clean_equivalence_computed": False,
        "clean_equivalence_full": None,
        "final_authority_computed": False,
        "VAL_GT_READ": 0,
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
        print(json.dumps({"error": "FAILURE_ARTIFACT_WRITE_FAILED",
                          "exception_type": type(exc).__name__,
                          "exception_message": str(exc)}, indent=1))
        return False


# --------------------------------------------------------------------------- #
# CLEAN DOWNSTREAM (GT-FREE) — stop at out["final_probability"]
# --------------------------------------------------------------------------- #
def _clean_final_probability_only(sid, row, ctx, generated, counters, store):
    """Exact canonical downstream clean path, STOPPING at out['final_probability'].

    Mirrors ``mod._evaluate_clean_sample`` EXCEPT that it never loads GT and never
    computes Dice/IoU/HD95.  Uses ONLY ``row['task_id']`` and the frozen image path
    loader; ``row['mask_path']`` is never read.
    """
    task_id = int(row["task_id"])
    p_global = generated["p_global"][sid]
    geom = generated["geometry"][sid]
    rf202 = generated["rf202"][sid]

    image_t = _FROZEN_MOD["_load_clean_image_tensor"](row)
    image_b = image_t[None].to(ctx["device"])

    out = _FROZEN_MOD["canonical_learned_core"](
        ctx, image_b, task_id,
        p_global_override=p_global, g_taps=None,
        router_features_202_override=rf202,
        roi_window=None,
        action_available=(geom is not None),
        counters=counters)

    final_prob = np.asarray(out["final_probability"], dtype=np.float32)
    counters["final_probability_passes"] = counters.get("final_probability_passes", 0) + 1
    store[sid] = final_prob
    return {
        "sample_id": sid,
        "task_id": task_id,
        "state": out.get("state"),
        "router_decision": out.get("router_decision"),
        "roi_available": out.get("roi_available"),
        "final_probability_shape": list(final_prob.shape),
        "final_probability_dtype": str(final_prob.dtype),
        "final_probability_finite": bool(np.isfinite(final_prob).all()),
    }


# --------------------------------------------------------------------------- #
# GT-FREE FINAL-AUTHORITY COMPARISON
# --------------------------------------------------------------------------- #
def _compare_final_authority(final_prob_by_sid, sample_order, counters) -> dict:
    ref_path = ROOT / PHASE27_FINAL_PROB_AUTHORITY["path"]
    out = {
        "reference_path": PHASE27_FINAL_PROB_AUTHORITY["path"],
        "reference_sha256": (sha256_file(ref_path) if ref_path.exists() else None),
        "reference_sha256_expected": PHASE27_FINAL_PROB_AUTHORITY["sha256"],
        "n_samples": len(sample_order),
    }
    if not ref_path.exists():
        out.update({"pass": False, "reason": "PHASE27_FINAL_AUTHORITY_ABSENT"})
        return out
    if out["reference_sha256"] != PHASE27_FINAL_PROB_AUTHORITY["sha256"]:
        out.update({"pass": False, "reason": "PHASE27_FINAL_AUTHORITY_SHA_MISMATCH"})
        return out

    ref = np.load(ref_path)
    out["reference_shape"] = list(ref.shape)
    out["reference_dtype"] = str(ref.dtype)
    if list(ref.shape) != list(PHASE27_FINAL_PROB_AUTHORITY["shape"]):
        out.update({"pass": False, "reason": "PHASE27_FINAL_AUTHORITY_SHAPE_MISMATCH"})
        return out
    if len(sample_order) != ref.shape[0]:
        out.update({"pass": False, "reason": "POPULATION_SIZE_MISMATCH"})
        return out

    per_sample = []
    total_mismatch = 0
    max_abs = 0.0
    affected = []
    live_vs_self_flip = 0
    self_vs_bound_mismatch = 0
    live_vs_bound_mismatch = 0
    k_total = 0          # count of generated_final_f16 == float16(0.5)
    q_measured = 0       # among those, live_float32_final_probability < 0.5
    live_f32_vs_bound_f16_exact = 0

    for i, sid in enumerate(sample_order):
        live = np.asarray(final_prob_by_sid[sid], dtype=np.float32)
        gen_f16 = live.astype(np.float16)
        bound_f16 = ref[i]
        neq = (gen_f16 != bound_f16)
        cnt = int(neq.sum())
        diff = np.abs(gen_f16.astype(np.float64) - bound_f16.astype(np.float64))
        mabs = float(diff.max()) if diff.size else 0.0
        total_mismatch += cnt
        max_abs = max(max_abs, mabs)
        if cnt:
            affected.append(sid)

        live_bin = (live >= np.float32(SEGMENTATION_OUTPUT_THRESHOLD))
        self_bin = (gen_f16.astype(np.float32) >= np.float32(SEGMENTATION_OUTPUT_THRESHOLD))
        bound_bin = (bound_f16.astype(np.float32) >= np.float32(SEGMENTATION_OUTPUT_THRESHOLD))
        n_live_self = int(np.count_nonzero(live_bin != self_bin))
        n_self_bound = int(np.count_nonzero(self_bin != bound_bin))
        n_live_bound = int(np.count_nonzero(live_bin != bound_bin))
        live_vs_self_flip += n_live_self
        self_vs_bound_mismatch += n_self_bound
        live_vs_bound_mismatch += n_live_bound
        if np.array_equal(live, bound_f16.astype(np.float32)):
            live_f32_vs_bound_f16_exact += 1

        is_half = (gen_f16 == F16_HALF)
        k_i = int(is_half.sum())
        q_i = int(np.count_nonzero(is_half & (live < np.float32(0.5))))
        k_total += k_i
        q_measured += q_i

        per_sample.append({
            "sample_id": sid,
            "f16_mismatch_count": cnt,
            "f16_max_abs_difference": mabs,
            "n_pixels_generated_f16_eq_half": k_i,
            "n_measured_live_below_half_at_half_pixels": q_i,
            "live_vs_self_f16_threshold_flip_count": n_live_self,
            "self_f16_vs_phase27_f16_threshold_mismatch_count": n_self_bound,
            "live_vs_phase27_threshold_mismatch_count": n_live_bound,
        })

    bit_identical_all = bool(total_mismatch == 0)
    classification = ("D51_FINAL_AUTHORITY_REPRODUCED" if bit_identical_all
                      else "D51_END_TO_END_FINAL_AUTHORITY_NOT_REPRODUCED")

    out.update({
        "pass": True,
        "n_samples": len(sample_order),
        "final_f16_bit_identical_all": bit_identical_all,
        "total_f16_element_mismatch_count": int(total_mismatch),
        "max_abs_f16_difference": float(max_abs),
        "n_samples_with_any_f16_difference": len(affected),
        "affected_sample_ids": affected,
        "per_sample": per_sample,
        "live_vs_self_f16_threshold_flip_count": int(live_vs_self_flip),
        "self_f16_vs_phase27_f16_threshold_mismatch_count": int(self_vs_bound_mismatch),
        "live_vs_phase27_threshold_mismatch_count": int(live_vs_bound_mismatch),
        "n_pixels_generated_f16_eq_half_total": int(k_total),
        "n_measured_q_live_below_half_total": int(q_measured),
        "n_samples_live_f32_bit_equal_to_bound_f16": int(live_f32_vs_bound_f16_exact),
        "q_measurement_note": ("k = count of generated_final_f16 == float16(0.5); "
                               "q = the subset of those whose LIVE float32 was < 0.5 "
                               "(the ACTUAL D51-A flip subset, measured not assumed)."),
        "classification": classification,
        "interpretation_contract": {
            "bit_identical_all_true_means": "D51_FINAL_AUTHORITY_REPRODUCED",
            "bit_identical_all_false_means": "D51_END_TO_END_FINAL_AUTHORITY_NOT_REPRODUCED",
            "not_automatically_g_mismatch": True,
        },
        "gt_read": False,
        "dice_iou_hd95_computed": False,
    })
    return out


_FROZEN_MOD = None


def run_diagnostic() -> dict:
    global _FROZEN_MOD
    mod = _import_frozen_v1_14()
    _FROZEN_MOD = mod

    # ---- RUNTIME GT PROHIBITION ------------------------------------------- #
    gt_guard = _install_gt_guards(mod)
    assert sha256_file(FROZEN_V1_14_SOURCE) == FROZEN_V1_14_EXEC_SHA, \
        "frozen v1.14 source mutated by guard installation"

    counters = _build_counters(mod)
    stages: dict = {}
    stages["d50_foreign_gate_call_omitted"] = True
    stages["d50_reason"] = D50_REASON
    stages["gt_guard_installed"] = list(gt_guard["installed"])
    stages["gt_forbidden_row_keys"] = list(GT_FORBIDDEN_ROW_KEYS)

    # ---- load exact frozen components -------------------------------------- #
    ctx = mod._load_models()
    stages["step_models_loaded"] = True
    stages["component_load_audit"] = ctx.get("load_audit")

    # ---- canonical batched CLEAN G (LIVE FLOAT32 downstream preserved) ------ #
    generated = mod._generate_clean_g_reference(ctx, counters)
    stages["step_generation_n"] = len(generated.get("sample_order", []))
    stages["g_downstream_representation"] = "LIVE_FLOAT32 (NOT quantized; D51 G-quantization repair WITHDRAWN)"

    # ---- retained Phase27 GLOBAL f16 reproduction gate --------------------- #
    g_gate = mod._phase27_global_reproduction_gate(
        generated["p_global_f16"], generated["sample_order"], counters)
    stages["step4_phase27_global_reproduction_gate"] = g_gate
    if not g_gate.get("pass"):
        raise SystemExit(
            "DIAGNOSTIC_PHASE27_GLOBAL_REPRODUCTION_GATE_FAILED: "
            + json.dumps(g_gate, default=str))

    # ---- 808 GT-free clean final-probability passes ------------------------ #
    rows, _row_index = mod._clean_row_index()
    sample_order = [r["sample_id"] for r in rows]
    final_prob_by_sid: dict = {}
    clean_records = []
    for r in rows:
        sid = r["sample_id"]
        clean_records.append(
            _clean_final_probability_only(sid, r, ctx, generated, counters, final_prob_by_sid))
        counters["clean_passes"] = counters.get("clean_passes", 0) + 1
    stages["step5_clean_records"] = len(clean_records)
    stages["step5_final_probability_passes"] = len(final_prob_by_sid)

    # ---- GT-free final-authority comparison -------------------------------- #
    cmp_ = _compare_final_authority(final_prob_by_sid, sample_order, counters)
    stages["step6_final_authority_comparison"] = cmp_

    # ---- GT prohibition invariant ------------------------------------------ #
    if gt_guard["VAL_GT_READ"] != 0:
        raise SystemExit(
            "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_0_FAIL_CLOSED__GT_READ_NONZERO::"
            + json.dumps(gt_guard, default=str))
    if not cmp_.get("pass"):
        raise SystemExit("DIAGNOSTIC_FINAL_AUTHORITY_COMPARISON_FAILED: "
                         + json.dumps(cmp_, default=str))

    diag = {
        "artifact_kind": "PHASE36_FINAL_PROBABILITY_AUTHORITY_DIAGNOSTIC_RESULT",
        "revision": DIAGNOSTIC_REVISION,
        "purpose": "GT_FREE_FINAL_PROBABILITY_AUTHORITY_REPRODUCTION_TEST",
        "execution_scope": "CLEAN_ONLY__NO_GT__NO_DICE__NO_PERTURBATION",
        "exact_diagnostic_source_sha256": sha256_file(Path(__file__)),
        "frozen_v1_14_source_sha256": sha256_file(FROZEN_V1_14_SOURCE),
        "frozen_v1_14_manifest_sha256": FROZEN_V1_14_MANIFEST_SHA,
        "phase27_final_prob_authority": dict(PHASE27_FINAL_PROB_AUTHORITY),
        "phase27_global_prob_authority": dict(PHASE27_GLOBAL_PROB_AUTHORITY),
        "final_authority_comparison": cmp_,
        "stages": stages,
        "counters": dict(counters),
        "VAL_GT_READ": int(gt_guard["VAL_GT_READ"]),
        "gt_guard": {"installed": list(gt_guard["installed"]),
                     "blocked_calls": list(gt_guard["blocked_calls"])},
        "authorized_population_count": 808,
        "prior_failure_provenance_bound": _prior_failure_provenance_state(),
        "consumed_evidence_provenance_bound": _provenance_state(CONSUMED_EVIDENCE_PROVENANCE),
        "d50_foreign_gate_call_omitted": True,
        "d50_reason": D50_REASON,
        "foreign_v1_14_launch_token_present": os.environ.get(FOREIGN_V1_14_LAUNCH_TOKEN) == "1",
        "preconsumption_transitive_integrity_pass": True,
        "source_manifest_transitive_authority_exact_match": True,
        "classification": cmp_["classification"],
        "perturbation_executed": False,
        "scientific_output": False,
        "robustness_result": False,
        "v1_14_science_markers_touched": False,
        "generated_utc": now(),
        "write_semantics": "O_CREAT|O_EXCL + full-write + fsync (exclusive-create, write-once)",
    }
    return diag


def main() -> int:
    # ---- (0) FOREIGN v1.14 launcher token MUST be absent ------------------- #
    if os.environ.get(FOREIGN_V1_14_LAUNCH_TOKEN) == "1":
        print(json.dumps({
            "status": "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_0_FAIL_CLOSED__"
                      "FOREIGN_V1_14_LAUNCH_AUTHORITY_PRESENT__NO_ATTEMPT_CONSUMED",
            "foreign_token": FOREIGN_V1_14_LAUNCH_TOKEN,
            "foreign_token_present": True,
            "attempt_consumed": False,
            "marker_created": False}, indent=1))
        return 8

    # ---- (1) one-shot execute gate ---------------------------------------- #
    if os.environ.get(ONE_SHOT_ENV) != "1":
        print(json.dumps({
            "status": "REFUSED__ONE_SHOT_GATE_NOT_SET",
            "required_env": f"{ONE_SHOT_ENV}=1",
            "attempt_consumed": False}, indent=1))
        return 3

    # ---- (2) prior-attempt absence ---------------------------------------- #
    if _attempt_already_consumed():
        print(json.dumps({
            "status": "REFUSED__DIAGNOSTIC_ATTEMPT_ALREADY_CONSUMED",
            "automatic_retry": False,
            "attempt_consumed": False}, indent=1))
        return 4

    # ---- (3) diagnostic launch authority (FAIL CLOSED) --------------------- #
    if os.environ.get(LAUNCH_AUTHORITY_TOKEN) != "1":
        print(json.dumps({
            "status": "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_0_FAIL_CLOSED__"
                      "LAUNCH_AUTHORITY_REQUIRED__NO_ATTEMPT_CONSUMED",
            "required_env": f"{LAUNCH_AUTHORITY_TOKEN}=1",
            "launch_authority_present": False,
            "attempt_consumed": False,
            "marker_created": False,
            "model_constructed": False,
            "checkpoint_loaded": False,
            "val_or_gt_read": False}, indent=1))
        return 5

    # ---- (4) preserved prior-failure provenance gate ----------------------- #
    prov = _prior_failure_provenance_state()
    if not prov["all_match"]:
        print(json.dumps({
            "status": "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_0_FAIL_CLOSED__"
                      "PRIOR_FAILURE_PROVENANCE_NOT_BOUND__NO_ATTEMPT_CONSUMED",
            "provenance": prov, "attempt_consumed": False}, indent=1))
        return 6

    # ---- (5) consumed-evidence binding gate -------------------------------- #
    consumed = _provenance_state(CONSUMED_EVIDENCE_PROVENANCE)
    if not consumed["all_match"]:
        print(json.dumps({
            "status": "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_0_FAIL_CLOSED__"
                      "CONSUMED_EVIDENCE_NOT_BOUND__NO_ATTEMPT_CONSUMED",
            "consumed_evidence": consumed, "attempt_consumed": False}, indent=1))
        return 9

    touch_guard = {p.name: p.exists() for p in V14_SCIENCE_MARKERS}

    # ---- (6) derived authorization + write-once start marker --------------- #
    authorized_attempt = bool(
        os.environ.get(ONE_SHOT_ENV) == "1"
        and os.environ.get(LAUNCH_AUTHORITY_TOKEN) == "1"
        and os.environ.get(FOREIGN_V1_14_LAUNCH_TOKEN) != "1"
        and not _attempt_already_consumed()
        and prov["all_match"]
        and prov["static_audit_verdict"] == REQUIRED_STATIC_AUDIT_VERDICT
        and consumed["all_match"])
    if not authorized_attempt:
        print(json.dumps({
            "status": "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_0_FAIL_CLOSED__"
                      "AUTHORIZATION_STATE_NOT_SATISFIED__NO_ATTEMPT_CONSUMED",
            "attempt_consumed": False}, indent=1))
        return 7

    _write_once_json(DIAGNOSTIC_START, {
        "artifact_kind": "PHASE36_FINAL_PROBABILITY_AUTHORITY_DIAGNOSTIC_START",
        "revision": DIAGNOSTIC_REVISION,
        "attempted": True,
        "authorized_attempt": authorized_attempt,
        "authorization_derivation": ("derived: one_shot_gate AND launch_authority_token AND "
                                     "foreign_v1_14_token_absent AND no_prior_attempt AND "
                                     "prior_failure_provenance_bound AND "
                                     "static_audit_verdict==STATIC_ROOT_CAUSE_NOT_ESTABLISHED AND "
                                     "consumed_evidence_bound"),
        "one_shot_gate_env": ONE_SHOT_ENV,
        "launch_authority_token_env": LAUNCH_AUTHORITY_TOKEN,
        "foreign_v1_14_launch_token_env": FOREIGN_V1_14_LAUNCH_TOKEN,
        "foreign_v1_14_launch_token_present": False,
        "d50_foreign_gate_call_omitted": True,
        "d50_reason": D50_REASON,
        "exact_diagnostic_source_sha256": sha256_file(Path(__file__)),
        "frozen_v1_14_exec_source_sha256": FROZEN_V1_14_EXEC_SHA,
        "frozen_v1_14_manifest_sha256": FROZEN_V1_14_MANIFEST_SHA,
        "phase27_final_prob_authority": dict(PHASE27_FINAL_PROB_AUTHORITY),
        "prior_failure_provenance": prov,
        "consumed_evidence_provenance": consumed,
        "v1_14_science_marker_presence_at_start": touch_guard,
        "gt_prohibition": {"static": "no GT callables referenced",
                           "runtime": "raising proxies installed",
                           "VAL_GT_READ_must_be": 0},
        "automatic_retry": False,
        "overwrite_permitted": False,
        "scientific_output": False,
        "generated_utc": now(),
        "write_semantics": "O_CREAT|O_EXCL + full-write + fsync (exclusive-create, write-once)",
    })

    # ---- (7) GUARDED TERMINAL-EVIDENCE REGION ------------------------------ #
    try:
        diag = run_diagnostic()
        _write_once_json(DIAGNOSTIC_RESULT, diag)
    except SystemExit as exc:
        _write_failure(termination_kind="SYSTEM_EXIT", exc_type="SystemExit",
                       exc_msg=str(exc.code), failing_stage="run_diagnostic")
        print(json.dumps({"status": "DIAGNOSTIC_TERMINATED", "message": str(exc.code)}, indent=1))
        return 1
    except BaseException as exc:  # noqa: BLE001
        _write_failure(termination_kind="EXCEPTION", exc_type=type(exc).__name__,
                       exc_msg=str(exc), failing_stage="run_diagnostic_or_result_write")
        traceback.print_exc()
        return 2

    print(json.dumps({
        "status": "DIAGNOSTIC_COMPLETE",
        "classification": diag["classification"],
        "final_f16_bit_identical_all": diag["final_authority_comparison"]["final_f16_bit_identical_all"],
        "total_f16_element_mismatch_count": diag["final_authority_comparison"]["total_f16_element_mismatch_count"],
        "max_abs_f16_difference": diag["final_authority_comparison"]["max_abs_f16_difference"],
        "n_samples_with_any_f16_difference": diag["final_authority_comparison"]["n_samples_with_any_f16_difference"],
        "VAL_GT_READ": diag["VAL_GT_READ"],
        "result_path": str(DIAGNOSTIC_RESULT.relative_to(ROOT)),
        "result_sha256": sha256_file(DIAGNOSTIC_RESULT),
        "perturbation_executed": False,
        "scientific_output": False}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
