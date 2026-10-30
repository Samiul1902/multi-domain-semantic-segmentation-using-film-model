#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase35 v1.0f MODEL-FREE CPU unit tests for the ACTUAL-LOGITS empty-mask observability repair.

Classification: PRE_EXECUTION_ACTUAL_LOGITS_EMPTY_MASK_OBSERVABILITY_UNIT_TEST__CPU_ONLY__MODEL_FREE
Revision: ra_medfilm_barr_phase35_interpretability_v1_0f

Purpose
  Prove, WITHOUT constructing any model, loading any checkpoint, running any forward, autograd or
  Grad-CAM, that the v1.0f actual-logits empty-mask fallback validation behaves exactly as specified:
    * the same rank-safe helper reduces the ACTUAL logits with an all-False mask to the full-field
      foreground mean (frozen empty-mask fallback arithmetic unchanged);
    * the independent `expected_full_plane_mean` agrees to the fixed `atol=1e-7, rtol=0` contract;
    * a non-empty mask is unchanged relative to the rank-safe contract;
    * NaN actual logits still fail CLOSED through the numerical finite guard;
    * NO zero-logit surrogate is required (or used) on the acceptance path;
    * NO additional forward / autograd is conceptually present in the helper path.

This script imports the v1.0f execution module ONLY for its pure, side-effect-free helper
(`empty_mask_helper_check_insession_actual_logits`) and the frozen v1.0d rank-safe target scalar.
Importing the v1.0f module performs NO model work (see its ZERO-EXECUTION GUARD), and this script
additionally asserts a model-free import cost of 0 constructions / 0 forwards / 0 autograd.

Tests (T1..T7) run on CPU with torch tensors only. Output:
  reports/audits/phase35_empty_mask_actual_logits_unit_v1_0f.json
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

import torch                                                  # noqa: E402

import phase35_interpretability_execution_v1_0d as V0D        # noqa: E402  (rank-safe helper)
import phase35_interpretability_execution_v1_0f as V0F        # noqa: E402  (actual-logits repair)

OUT = (REPO_ROOT / "reports" / "audits"
       / "phase35_empty_mask_actual_logits_unit_v1_0f.json")
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


def _empty_mask(shape=(4, 4)):
    return torch.zeros(*shape, dtype=torch.bool)


# --------------------------------------------------------------------------- #
# T1  actual-logits empty mask -> full-field mean 7.5; independent expected agrees; diff 0; PASS
# --------------------------------------------------------------------------- #
@test("T1_actual_logits_empty_mask_full_field_mean")
def t1():
    logits = torch.arange(16, dtype=torch.float32).reshape(1, 1, 4, 4)
    expected_manual = float(logits.float()[0, 0, :, :].mean())      # = 7.5
    res = V0F.empty_mask_helper_check_insession_actual_logits(logits, _empty_mask())
    ok = (res["same_actual_G_logits_used"] is True
          and res["surrogate_zero_logits_used"] is False
          and res["empty_mask_rank"] == 2
          and res["empty_mask_shape"] == [4, 4]
          and res["empty_mask_dtype"] == "bool"
          and res["empty_mask_true_pixels"] == 0
          and res["fallback_selected"] is True
          and res["helper_return"] == 7.5
          and res["expected_full_plane_mean"] == 7.5
          and res["expected_full_plane_mean"] == expected_manual
          and res["difference"] == 0.0
          and res["comparison_pass"] is True
          and res["finite"] is True
          and res["additional_G_forwards"] == 0
          and res["additional_autograd_calls"] == 0)
    return OrderedDict([("helper_return", res["helper_return"]),
                        ("expected_full_plane_mean", res["expected_full_plane_mean"]),
                        ("difference", res["difference"]),
                        ("comparison_pass", res["comparison_pass"]),
                        ("finite", res["finite"]),
                        ("same_actual_G_logits_used", res["same_actual_G_logits_used"]),
                        ("surrogate_zero_logits_used", res["surrogate_zero_logits_used"]),
                        ("pass", ok)])


# --------------------------------------------------------------------------- #
# T2  non-empty mask unchanged vs rank-safe contract (mean of selected pixels only)
# --------------------------------------------------------------------------- #
@test("T2_non_empty_mask_rank_safe_unchanged")
def t2():
    logits = torch.arange(16, dtype=torch.float32).reshape(1, 1, 4, 4)
    mask = torch.zeros(4, 4, dtype=torch.bool)
    mask[0, 0] = True
    mask[1, 1] = True
    direct = float(V0D.gradcam_target_scalar_rank_safe(logits, mask))
    expected = float(logits.float()[0, 0][mask].mean())
    return OrderedDict([("direct_helper", direct), ("expected_selected_mean", expected),
                        ("pass", direct == expected and direct != 7.5)])


# --------------------------------------------------------------------------- #
# T3  comparison contract uses atol=1e-7, rtol=0 exactly (frozen, declared in-source)
# --------------------------------------------------------------------------- #
@test("T3_fixed_atol_rtol_contract")
def t3():
    a = torch.tensor(1.0)
    b = torch.tensor(1.0 + 5e-8)     # inside atol 1e-7 -> close
    c = torch.tensor(1.0 + 2e-6)     # outside atol 1e-7 -> not close (rtol=0)
    close_in = bool(torch.isclose(a, b, atol=1e-7, rtol=0))
    close_out = bool(torch.isclose(a, c, atol=1e-7, rtol=0))
    return OrderedDict([("declared_atol", V0F.EMPTY_MASK_ATOL),
                        ("declared_rtol", V0F.EMPTY_MASK_RTOL),
                        ("close_within_atol", close_in), ("close_outside_atol", close_out),
                        ("pass", (V0F.EMPTY_MASK_ATOL == 1e-7 and V0F.EMPTY_MASK_RTOL == 0.0
                                  and close_in and (not close_out)))])


# --------------------------------------------------------------------------- #
# T4  surrogate zero-logit path is NOT required (actual path works with nonzero logits)
# --------------------------------------------------------------------------- #
@test("T4_surrogate_zero_logits_not_required")
def t4():
    # nonzero logits: a zero-logit surrogate would give 0.0, the actual path gives the true mean
    logits = (torch.arange(16, dtype=torch.float32).reshape(1, 1, 4, 4) + 100.0)
    res = V0F.empty_mask_helper_check_insession_actual_logits(logits, _empty_mask())
    not_zero = res["helper_return"] != 0.0
    matches_actual = res["comparison_pass"] and res["helper_return"] == res["expected_full_plane_mean"]
    return OrderedDict([("helper_return", res["helper_return"]),
                        ("surrogate_would_be", 0.0),
                        ("not_zero_surrogate", not_zero),
                        ("matches_actual", matches_actual),
                        ("pass", not_zero and matches_actual)])


# --------------------------------------------------------------------------- #
# T5  no additional forward / autograd is conceptually present in the helper path
# --------------------------------------------------------------------------- #
@test("T5_no_additional_forward_or_autograd")
def t5():
    src = (REPO_ROOT / "scripts" / "analysis"
           / "phase35_interpretability_execution_v1_0f.py").read_text(encoding="utf-8")
    fn = None
    tree = ast.parse(src)
    for n in tree.body:
        if isinstance(n, ast.FunctionDef) and n.name == "empty_mask_helper_check_insession_actual_logits":
            fn = n
    calls = set()
    if fn is not None:
        for n in ast.walk(fn):
            if isinstance(n, ast.Call):
                f = n.func
                calls.add(f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", None))
    forbidden = {"autograd", "grad", "forward", "backward"}
    leaked = sorted(c for c in calls if c in forbidden)
    # also assert the emitted counters confirm 0 extra forward/autograd
    res = V0F.empty_mask_helper_check_insession_actual_logits(
        torch.arange(16, dtype=torch.float32).reshape(1, 1, 4, 4), _empty_mask())
    ok = (not leaked and res["additional_G_forwards"] == 0
          and res["additional_autograd_calls"] == 0
          and res["extra_forward_performed"] is False
          and res["extra_autograd_performed"] is False)
    return OrderedDict([("helper_calls", sorted(c for c in calls if c)),
                        ("forbidden_calls_leaked", leaked),
                        ("additional_G_forwards", res["additional_G_forwards"]),
                        ("additional_autograd_calls", res["additional_autograd_calls"]),
                        ("pass", ok)])


# --------------------------------------------------------------------------- #
# T6  NaN actual logits fail CLOSED via the numerical finite guard (before any acceptance output)
# --------------------------------------------------------------------------- #
@test("T6_nan_actual_logits_fail_closed")
def t6():
    logits = torch.arange(16, dtype=torch.float32).reshape(1, 1, 4, 4)
    logits[0, 0, 0, 0] = float("nan")
    raised, kind = _raises(
        lambda: V0F.empty_mask_helper_check_insession_actual_logits(logits, _empty_mask()),
        RuntimeError)
    return OrderedDict([("raised_RuntimeError", raised), ("exc", kind), ("pass", raised)])


# --------------------------------------------------------------------------- #
# T7  dtype / rank fail-closed on the actual-logits helper input
# --------------------------------------------------------------------------- #
@test("T7_helper_input_type_and_rank_fail_closed")
def t7():
    r_notensor, k_notensor = _raises(
        lambda: V0F.empty_mask_helper_check_insession_actual_logits([1, 2, 3], _empty_mask()),
        TypeError)
    r_rank, k_rank = _raises(
        lambda: V0F.empty_mask_helper_check_insession_actual_logits(
            torch.arange(16, dtype=torch.float32).reshape(4, 4), _empty_mask()),
        RuntimeError)
    return OrderedDict([("nontensor_raised", r_notensor), ("nontensor_exc", k_notensor),
                        ("badrank_raised", r_rank), ("badrank_exc", k_rank),
                        ("pass", r_notensor and r_rank)])


# --------------------------------------------------------------------------- #
# model-free import audit (AST: no model-construction / forward / autograd at v1.0f module top level)
# --------------------------------------------------------------------------- #
def model_free_import_audit() -> dict:
    src = (REPO_ROOT / "scripts" / "analysis"
           / "phase35_interpretability_execution_v1_0f.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    forbidden = {"load_g_component", "load_bphi_component", "gradcam_gradient_enabled_numerically_guarded_v1_0f",
                 "forward", "autograd", "load_state_dict"}
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
        ("artifact", "phase35_empty_mask_actual_logits_unit_v1_0f"),
        ("phase", 35), ("section", "\u00A7L"),
        ("revision", V0F.REVISION), ("classification", V0F.CLASSIFICATION),
        ("device", "cpu"), ("model_free", True),
        ("test_source", {"path": str(SOURCE.relative_to(REPO_ROOT)), "sha256": sha(SOURCE)}),
        ("guarded_module", {"path": "scripts/analysis/phase35_interpretability_execution_v1_0f.py",
                            "sha256": sha(REPO_ROOT / "scripts" / "analysis"
                                          / "phase35_interpretability_execution_v1_0f.py")}),
        ("n_tests", len(UT)), ("n_pass", n_pass),
        ("n_fail", len(UT) - n_pass),
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
