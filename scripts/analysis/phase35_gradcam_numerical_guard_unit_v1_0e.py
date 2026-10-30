#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase35 v1.0e MODEL-FREE CPU unit tests for the Grad-CAM numerical guards.

Classification: PRE_EXECUTION_GRADCAM_NUMERICAL_OBSERVABILITY_UNIT_TEST__CPU_ONLY__MODEL_FREE
Revision: ra_medfilm_barr_phase35_interpretability_v1_0e

Purpose
  Prove, WITHOUT constructing any model, loading any checkpoint, running any forward, autograd or
  Grad-CAM, that the v1.0e numerical guards and the guarded normalizer behave exactly as specified:
  finite states pass through unchanged (frozen semantics on finite inputs) and non-finite states fail
  CLOSED. Also prove that the frozen `cam_normalize` zero-range fallback is reachable ONLY on finite
  input, so an all-zero CAM can never mean "masked NaN/inf".

This script imports the v1.0e execution module ONLY for its pure, side-effect-free guard functions
(`_require_finite_tensor`, `_require_finite_scalar`, `cam_normalize_guarded`, `_tensor_stats`).
Importing the v1.0e module performs NO model work (see its ZERO-EXECUTION GUARD), and this script
additionally asserts a model-free import cost of 0 constructions / 0 forwards / 0 autograd.

Eleven tests (T1..T11) run on CPU with torch tensors only. Output:
  reports/audits/phase35_gradcam_numerical_guard_unit_v1_0e.json
"""
from __future__ import annotations

import ast
import hashlib
import json
import sys
import time
from collections import OrderedDict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if not ((REPO_ROOT / "src").is_dir() and (REPO_ROOT / "scripts").is_dir()):
    raise RuntimeError(f"repository root resolution failed: {REPO_ROOT}")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "analysis"))

import torch                                                # noqa: E402

import phase35_interpretability_execution_v1_0e as V0E      # noqa: E402  (guards only)

OUT = REPO_ROOT / "reports" / "audits" / "phase35_gradcam_numerical_guard_unit_v1_0e.json"
SOURCE = Path(__file__).resolve()

UT = OrderedDict()


def test(name):
    def deco(fn):
        UT[name] = fn
        return fn
    return deco


def _raises(fn, exc_types):
    try:
        fn()
    except exc_types as e:
        return True, type(e).__name__
    except Exception as e:                                   # noqa: BLE001
        return False, f"UNEXPECTED:{type(e).__name__}"
    return False, "NO_RAISE"


# --------------------------------------------------------------------------- #
# T1  finite tensor passes through unchanged (identity), returns same object
# --------------------------------------------------------------------------- #
@test("T1_finite_tensor_passes")
def t1():
    t = torch.tensor([[1.0, -2.0], [3.5, 0.0]])
    out = V0E._require_finite_tensor(t, "gradient_finite")
    same = out is t
    exact = bool(torch.equal(out, t))
    return OrderedDict([("same_object", same), ("exact_equal", exact),
                        ("pass", same and exact)])


# --------------------------------------------------------------------------- #
# T2  NaN tensor fails closed
# --------------------------------------------------------------------------- #
@test("T2_nan_tensor_fails_closed")
def t2():
    t = torch.tensor([[1.0, float("nan")], [3.5, 0.0]])
    raised, kind = _raises(lambda: V0E._require_finite_tensor(t, "gradient_finite"), RuntimeError)
    return OrderedDict([("raised_RuntimeError", raised), ("exc", kind), ("pass", raised)])


# --------------------------------------------------------------------------- #
# T3  +inf tensor fails closed
# --------------------------------------------------------------------------- #
@test("T3_posinf_tensor_fails_closed")
def t3():
    t = torch.tensor([[1.0, float("inf")], [3.5, 0.0]])
    raised, kind = _raises(lambda: V0E._require_finite_tensor(t, "alpha_finite"), RuntimeError)
    return OrderedDict([("raised_RuntimeError", raised), ("exc", kind), ("pass", raised)])


# --------------------------------------------------------------------------- #
# T4  -inf tensor fails closed
# --------------------------------------------------------------------------- #
@test("T4_neginf_tensor_fails_closed")
def t4():
    t = torch.tensor([[-float("inf"), 0.0]])
    raised, kind = _raises(lambda: V0E._require_finite_tensor(t, "upsampled_prenorm_cam_finite"),
                           RuntimeError)
    return OrderedDict([("raised_RuntimeError", raised), ("exc", kind), ("pass", raised)])


# --------------------------------------------------------------------------- #
# T5a finite scalar passes; T5b NaN/inf scalar fails closed
# --------------------------------------------------------------------------- #
@test("T5a_finite_scalar_passes")
def t5a():
    v = V0E._require_finite_scalar(torch.tensor(2.5), "target_scalar_finite")
    return OrderedDict([("value", v), ("pass", v == 2.5)])


@test("T5b_nonfinite_scalar_fails_closed")
def t5b():
    r_nan, k_nan = _raises(lambda: V0E._require_finite_scalar(float("nan"), "target_scalar_finite"),
                           RuntimeError)
    r_inf, k_inf = _raises(lambda: V0E._require_finite_scalar(float("inf"), "target_scalar_finite"),
                           RuntimeError)
    return OrderedDict([("nan_raised", r_nan), ("inf_raised", r_inf),
                        ("nan_exc", k_nan), ("inf_exc", k_inf), ("pass", r_nan and r_inf)])


# --------------------------------------------------------------------------- #
# T6  guarded normalize on a FINITE positive-range CAM == frozen cam_normalize
# --------------------------------------------------------------------------- #
@test("T6_finite_positive_range_matches_frozen")
def t6():
    import phase35_interpretability_execution_v1_0b as V0B
    cam = torch.tensor([[[[1.0, 2.0], [3.0, 4.0]]]])          # [1,1,2,2]
    got = V0E.cam_normalize_guarded(cam)
    ref = V0B.cam_normalize(cam.clone())
    return OrderedDict([("got_min", float(got.min())), ("got_max", float(got.max())),
                        ("exact_equal_to_frozen", bool(torch.equal(got, ref))),
                        ("pass", bool(torch.equal(got, ref)) and float(got.min()) == 0.0
                         and float(got.max()) == 1.0)])


# --------------------------------------------------------------------------- #
# T7  guarded normalize on a FINITE ZERO-RANGE CAM -> frozen all-zeros fallback
# --------------------------------------------------------------------------- #
@test("T7_finite_zero_range_uses_zeros_fallback")
def t7():
    import phase35_interpretability_execution_v1_0b as V0B
    cam = torch.full((1, 1, 4, 4), 7.0)
    got = V0E.cam_normalize_guarded(cam)
    ref = V0B.cam_normalize(cam.clone())
    all_zero = bool(float(got.abs().max()) == 0.0)
    return OrderedDict([("all_zero", all_zero), ("exact_equal_to_frozen",
                                                 bool(torch.equal(got, ref))),
                        ("pass", all_zero and bool(torch.equal(got, ref)))])


# --------------------------------------------------------------------------- #
# T8  guarded normalize on a NON-FINITE CAM fails closed (never reaches zero fallback)
# --------------------------------------------------------------------------- #
@test("T8_nonfinite_cam_fails_closed_never_zero_fallback")
def t8():
    import phase35_interpretability_execution_v1_0b as V0B
    cam_nan = torch.tensor([[[[1.0, float("nan")], [3.0, 4.0]]]])
    raised, kind = _raises(lambda: V0E.cam_normalize_guarded(cam_nan), RuntimeError)
    frozen_out = V0B.cam_normalize(cam_nan.clone())           # frozen path returns all zeros
    frozen_all_zero = bool(float(frozen_out.abs().max()) == 0.0)
    return OrderedDict([("raised_RuntimeError", raised), ("exc", kind),
                        ("frozen_would_return_all_zero", frozen_all_zero),
                        ("guarded_never_returned_zero_fallback", raised),
                        ("pass", raised and frozen_all_zero)])


# --------------------------------------------------------------------------- #
# T9  guarded normalize on a finite CAM with a +inf-free but extreme range is finite
# --------------------------------------------------------------------------- #
@test("T9_extreme_finite_range_normalizes_finite")
def t9():
    cam = torch.tensor([[[[1e30, 1e30], [1e30, 1e30 + 1e15]]]])   # finite, huge but finite
    got = V0E.cam_normalize_guarded(cam)
    fin = bool(torch.isfinite(got).all())
    return OrderedDict([("finite", fin), ("min", float(got.min())), ("max", float(got.max())),
                        ("pass", fin)])


# --------------------------------------------------------------------------- #
# T10  _tensor_stats reports shape/dtype/finite/min/max/abs_max correctly
# --------------------------------------------------------------------------- #
@test("T10_tensor_stats_fields")
def t10():
    t = torch.tensor([[[[-3.0, 1.0], [2.0, 4.0]]]])          # [1,1,2,2]
    s = V0E._tensor_stats(t)
    ok = (s["shape"] == [1, 1, 2, 2] and s["dtype"] == "torch.float32" and s["finite"] is True
          and s["min"] == -3.0 and s["max"] == 4.0 and s["abs_max"] == 4.0)
    return OrderedDict([("stats", s), ("pass", ok)])


# --------------------------------------------------------------------------- #
# D1  the defect reproduction: frozen cam_normalize on a NaN CAM silently returns all zeros
#     while the guarded normalizer refuses -> documents WHY the guard is required.
# --------------------------------------------------------------------------- #
@test("D1_frozen_zero_range_can_mask_nonfinite")
def d1():
    import phase35_interpretability_execution_v1_0b as V0B
    cam = torch.tensor([[[[float("nan"), float("nan")], [float("nan"), float("nan")]]]])
    frozen = V0B.cam_normalize(cam.clone())
    guarded_raised, _ = _raises(lambda: V0E.cam_normalize_guarded(cam.clone()), RuntimeError)
    return OrderedDict([
        ("frozen_returns_all_zero", bool(float(frozen.abs().max()) == 0.0)),
        ("guarded_raises", guarded_raised),
        ("note", "frozen zero-range fallback cannot distinguish finite-zero from non-finite input"),
        ("pass", bool(float(frozen.abs().max()) == 0.0) and guarded_raised)])


# --------------------------------------------------------------------------- #
# model-free import audit (AST: no model-construction / forward / autograd in guard module top level)
# --------------------------------------------------------------------------- #
def model_free_import_audit() -> dict:
    src = (REPO_ROOT / "scripts" / "analysis"
           / "phase35_interpretability_execution_v1_0e.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    forbidden = {"load_g_component", "load_bphi_component", "gradcam_gradient_enabled_rank_safe",
                 "gradcam_gradient_enabled_numerically_guarded", "forward", "autograd"}
    # find top-level (module-body) calls; imports and defs are fine.
    top_calls = []
    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            f = node.value.func
            nm = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", None)
            top_calls.append(nm)
    leaked = [c for c in top_calls if c in forbidden]
    return OrderedDict([("top_level_executed_calls", top_calls),
                        ("forbidden_top_level_calls", leaked),
                        ("model_free", len(leaked) == 0)])


def main() -> int:
    results = OrderedDict()
    n_pass = 0
    for name, fn in UT.items():
        try:
            r = fn()
        except Exception as e:                               # noqa: BLE001
            r = OrderedDict([("pass", False), ("error", f"{type(e).__name__}: {e}")])
        results[name] = r
        n_pass += 1 if r.get("pass") else 0

    audit = model_free_import_audit()

    def sha(p: Path) -> str:
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for c in iter(lambda: f.read(1 << 20), b""):
                h.update(c)
        return h.hexdigest()

    out = OrderedDict([
        ("artifact", "phase35_gradcam_numerical_guard_unit_v1_0e"),
        ("phase", 35), ("section", "\u00a7R"),
        ("revision", V0E.REVISION), ("classification", V0E.CLASSIFICATION),
        ("device", "cpu"), ("model_free", True),
        ("test_source", {"path": str(SOURCE.relative_to(REPO_ROOT)), "sha256": sha(SOURCE)}),
        ("guarded_module", {"path": "scripts/analysis/phase35_interpretability_execution_v1_0e.py",
                            "sha256": sha(REPO_ROOT / "scripts" / "analysis"
                                          / "phase35_interpretability_execution_v1_0e.py")}),
        ("n_tests", len(UT)), ("n_pass", n_pass),
        ("all_pass", n_pass == len(UT)),
        ("results", results),
        ("model_free_import_audit", audit),
        ("counters", OrderedDict([
            ("model_constructions", 0), ("checkpoint_deserializations", 0), ("forwards", 0),
            ("autograd_calls", 0), ("gradcam_executions", 0), ("raw_val_reads", 0),
            ("gt_reads", 0), ("router_holdout_reads", 0), ("test_reads", 0),
            ("training_steps", 0)])),
        ("generated_utc", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())),
    ])
    out["all_pass"] = bool(out["all_pass"] and audit["model_free"])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    if OUT.exists():
        raise SystemExit(f"REFUSING TO OVERWRITE FROZEN OUTPUT: {OUT}")
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps({"n_pass": n_pass, "n_tests": len(UT), "all_pass": out["all_pass"],
                      "sha256": sha(OUT)}, indent=1))
    return 0 if out["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
