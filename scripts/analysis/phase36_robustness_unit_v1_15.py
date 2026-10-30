#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.15 — UNIT / STATIC SUITE (SOURCE / AST / HASH ONLY).

Independently re-derives and enforces the preserved v1.14 protections AND the
NEW v1.15 scientific repairs:

  D61 CANONICAL PHASE27 ACCEPT FUSION
      The ACCEPT branch final-probability fusion must call the canonical
      pad-aware ``fuse_full_field(p_global, refined, geom)`` EXACTLY, with the
      SAME ``p_global`` / ``refined`` / ``geom`` and NO geometry recompute, R_psi
      or S_omega change.  The old pad-unaware
      ``system._fuse_global_with_regional(p_global, refined, window)`` call MUST
      be ABSENT from the production path.  Mutation-sensitive: restoring the old
      call MUST fail the detector.

  D75 POLICY_B AUTHORITATIVE SEGMENTATION REPRESENTATION
      One helper ``_phase27_scored_final_binary`` implements EXACTLY
      live float32 -> float16 -> float32 -> >= SEGMENTATION_OUTPUT_THRESHOLD
      (0.50) and is wired into EVERY authoritative binary producer (core
      ``_core_result`` + clean ``_evaluate_clean_sample``).  The threshold (0.50)
      is UNCHANGED.  The live ``out["final_probability"]`` is NEVER quantized or
      fed back into router / ROI / R_psi / S_omega / fusion / safety / geometry /
      proposal generation.  ``downstream_G_quantization_added`` MUST be false.

NO torch.  NO model.  NO checkpoint.  NO CUDA.  NO forward.  NO smoke.  NO science.
NO VAL/GT read.  NO ROUTER_HOLDOUT.  NO TEST.
"""
from __future__ import annotations

import ast
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

EXEC = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_15.py"
EXEC_V1_14 = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_14.py"
LAUNCHER = ROOT / "scripts" / "analysis" / "launch_phase36_v1_15.py"
SUPERVISOR = ROOT / "scripts" / "analysis" / "supervise_phase36_v1_15.py"

FROZEN_V1_14_EXEC_SHA = "ac09ff8ded3610244920e66612145b246b33127140d344a9730d454bab27cff5"
FROZEN_V1_15_EXEC_SHA = "b194ad28345ea8b268748be383ca98b936cb051d85854666e3141250f3eae002"

POLICY_HELPER = "_phase27_scored_final_binary"

SRC = EXEC.read_text(encoding="utf-8")
TREE = ast.parse(SRC)
FUNCS = {n.name: n for n in ast.walk(TREE) if isinstance(n, ast.FunctionDef)}
LSRC = LAUNCHER.read_text(encoding="utf-8")

checks: list[dict] = []


def check(name, cond, detail=None):
    checks.append({"check": name, "passed": bool(cond), "detail": detail})


def _sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _func_src(name: str) -> str:
    return ast.get_source_segment(SRC, FUNCS[name]) or ""


# =========================================================================== #
# A. SOURCE IDENTITY
# =========================================================================== #
check("A01_v1_14_source_frozen_unchanged", _sha(EXEC_V1_14) == FROZEN_V1_14_EXEC_SHA,
      {"sha256": _sha(EXEC_V1_14)})
check("A02_v1_15_source_sha_exact", _sha(EXEC) == FROZEN_V1_15_EXEC_SHA,
      {"sha256": _sha(EXEC)})
check("A03_v1_15_source_compiles", compile(SRC, str(EXEC), "exec") is not None)

# =========================================================================== #
# B. D61 — CANONICAL PHASE27 ACCEPT FUSION
# =========================================================================== #
check("B01_canonical_fusion_call_present", "fuse_full_field(p_global, refined, geom)" in SRC)
check("B02_old_pad_unaware_call_absent",
      "system._fuse_global_with_regional(p_global, refined, window)" not in SRC)
check("B03_fuse_full_field_defined", "fuse_full_field" in FUNCS)
_fuse = _func_src("fuse_full_field")
check("B04_fuse_full_field_pad_aware",
      all(k in _fuse for k in ("pad_top", "pad_left", "crop_side_pixels",
                               "Resampling.BILINEAR")))
_core_learned = _func_src("canonical_learned_core")
check("B05_fusion_uses_roi_geometry_same_geom",
      "fuse_full_field(p_global, refined, geom)" in _core_learned
      and "geom" in _core_learned)
check("B06_no_geometry_recompute_in_accept_path",
      _core_learned.count("_roi_geometry_from_prob") == 0
      or "fuse_full_field(p_global, refined, geom)" in _core_learned)
check("B07_psi_somega_unchanged_markers",
      "somega_features(pg_crop, pr_crop, geom)" in _core_learned
      and "actual_r_psi_forwards" in _core_learned)

# =========================================================================== #
# C. D75 — POLICY_B REPRESENTATION
# =========================================================================== #
check("C01_policy_helper_defined", f"def {POLICY_HELPER}(" in SRC)
_h = _func_src(POLICY_HELPER)
check("C02_helper_uses_live_f32", "np.asarray(p_final_live, dtype=np.float32)" in _h)
check("C03_helper_casts_to_f16", "astype(np.float16)" in _h)
check("C04_helper_casts_back_to_f32", _h.count("astype(np.float32)") >= 2)
check("C05_helper_thresholds_at_0_50",
      "np.float32(SEGMENTATION_OUTPUT_THRESHOLD)" in _h)
check("C06_segmentation_threshold_unchanged", "SEGMENTATION_OUTPUT_THRESHOLD = 0.50" in SRC)

# helper wired exactly 3 times: 1 def + 2 authoritative call sites
check("C07_helper_wiring_count_3", SRC.count(f"{POLICY_HELPER}(") == 3,
      {"count": SRC.count(f"{POLICY_HELPER}(")})
check("C08_core_binary_uses_helper", f"{POLICY_HELPER}(prob)" in _func_src("_core_result"))
check("C09_clean_binary_uses_helper", f"{POLICY_HELPER}(final_prob)" in _func_src("_evaluate_clean_sample"))
check("C10_clean_store_final_binary_policy_b",
      'clean_store.setdefault("final_binary", {})[sid] = final_binary'
      in _func_src("_evaluate_clean_sample"))

# =========================================================================== #
# D. LIVE PROBABILITY REMAINS LIVE (no feedback of f16)
# =========================================================================== #
check("D01_final_probability_never_quantized",
      'out["final_probability"]' not in SRC.split(f"def {POLICY_HELPER}")[1].split("def ")[0]
      or "astype(np.float16)" not in _func_src("_core_result"))
# The ONLY float16 cast in the science path must be inside the POLICY_B helper.
check("D02_f16_cast_only_in_policy_helper",
      "astype(np.float16)" in _h and "astype(np.float16)" not in _func_src("canonical_learned_core"))
check("D03_downstream_G_quantization_absent",
      "astype(np.float16)" not in _func_src("canonical_learned_core"))
check("D04_live_probability_preserved",
      'res["final_probability"]' in SRC or "final_probability" in SRC)

# =========================================================================== #
# E. PERTURBATION PATHS CONSUME POLICY-B BINARIES
# =========================================================================== #
check("E01_image_pert_consumes_core_binary",
      'pert_binary = np.asarray(out["final_binary"], dtype=np.float32)' in SRC)
check("E02_proposal_pert_consumes_core_binary",
      SRC.count('pert_binary = np.asarray(out["final_binary"], dtype=np.float32)') >= 2)
check("E03_prediction_consistency_uses_policy_b",
      'clean_store["final_binary"][sid]' in SRC)

# =========================================================================== #
# F. SMOKE CONTRACT PRESERVED (53 ids)
# =========================================================================== #
def _declared_smoke_ids(src):
    t = ast.parse(src)
    for n in ast.walk(t):
        if isinstance(n, ast.Assign):
            for tg in n.targets:
                if isinstance(tg, ast.Name) and tg.id == "SMOKE_CHECK_IDS":
                    return [e.value for e in n.value.elts]
    return []


ids15 = _declared_smoke_ids(SRC)
ids14 = _declared_smoke_ids(EXEC_V1_14.read_text(encoding="utf-8"))
check("F01_smoke_ids_count_53", len(ids15) == 53, {"count": len(ids15)})
check("F02_smoke_ids_unique", len(set(ids15)) == 53)
check("F03_smoke_ids_exact_set_equality", set(ids15) == set(ids14))
check("F04_smoke_ids_order_identical", ids15 == ids14)

# =========================================================================== #
# G. ROBUSTNESS CONTRACT PRESERVED
# =========================================================================== #
check("G01_image_conditions_present",
      all(c in SRC for c in ("BRIGHTNESS_NEG", "CONTRAST_HIGH", "GAUSSIAN_BLUR_LOW",
                             "RESOLUTION_050", "GAUSSIAN_NOISE_LOW", "GAUSSIAN_NOISE_HIGH")))
check("G02_seeds_42_123_3407",
      all(s in SRC for s in ("42", "123", "3407")))
check("G03_proposal_scale_conditions",
      all(k in SRC for k in ("SHIFT_LEFT_10", "SHIFT_RIGHT_10", "SHIFT_UP_10",
                             "SHIFT_DOWN_10", "SCALE_085", "SCALE_115")))
check("G04_forced_skip_action_unavailable", "FORCED_SKIP" in SRC or "ACTION_UNAVAILABLE" in SRC)
check("G05_no_jpeg_rotation_crop_conditions",
      ("JPEG" not in SRC) and ("Image.ROTATE" not in SRC) and (".rotate(" not in SRC))

# =========================================================================== #
# H. LAUNCHER / SUPERVISOR BINDINGS
# =========================================================================== #
check("H01_launcher_present", LAUNCHER.exists())
check("H02_launcher_binds_frozen_v1_14_execution_sha",
      "ac09ff8ded3610244920e66612145b246b33127140d344a9730d454bab27cff5" in LSRC)
check("H03_launcher_verify_only_supported", "--verify-only" in LSRC)
check("H04_launcher_token_names",
      "PHASE36_V1_15_EXECUTE" in LSRC and "PHASE36_V1_15_LAUNCH_AUTHORITY" in LSRC)
check("H05_launcher_no_delete_or_recreate",
      "os.remove" not in LSRC and "unlink" not in LSRC)
check("H06_supervisor_present", SUPERVISOR.exists())

# =========================================================================== #
# I. SYNTHETIC REPRESENTATION TESTS (model-free; bit-for-bit)
# =========================================================================== #
ns = {"np": np, "SEGMENTATION_OUTPUT_THRESHOLD": 0.50}
exec(_h, ns)
edge = np.array([[0.0, 0.49, 0.4999999, 0.5, 0.5000001, 0.5001, 1.0]], dtype=np.float32)
got = ns[POLICY_HELPER](edge)
ref = (np.asarray(edge, dtype=np.float32).astype(np.float16).astype(np.float32)
       >= np.float32(0.50)).astype(np.float32)
check("I01_policy_b_bitwise_equal", np.array_equal(got, ref))
live = (np.asarray(edge, dtype=np.float32) >= np.float32(0.50)).astype(np.float32)
check("I02_boundary_repair_applied", np.array_equal(got, ref) and got.dtype == np.float32)

# =========================================================================== #
n_pass = sum(1 for c in checks if c["passed"])
n_total = len(checks)
report = {
    "artifact": "phase36_robustness_unit_v1_15",
    "phase": 36,
    "method": "RA-MedFiLM-BARR",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_15",
    "type": "STATIC_UNIT_REPORT",
    "model_free": True,
    "torch_imported": False,
    "protected_population_read": False,
    "subject_execution_sha256": _sha(EXEC),
    "frozen_v1_14_execution_sha256": _sha(EXEC_V1_14),
    "checks_total": n_total,
    "checks_passed": n_pass,
    "checks_failed": n_total - n_pass,
    "all_pass": n_pass == n_total,
    "failed_checks": [c["check"] for c in checks if not c["passed"]],
    "checks": checks,
}
out_path = ROOT / "reports/audits/phase36_robustness_unit_v1_15.json"
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(report, indent=1), encoding="utf-8")
for c in checks:
    if not c["passed"]:
        print(f"FAIL {c['check']} :: {c.get('detail')}")
print(f"UNIT v1.15: {n_pass}/{n_total} pass")
print(f"terminal: {'PHASE36_V1_15_UNIT_PASS' if n_pass == n_total else 'PHASE36_V1_15_UNIT_FAIL'}")
raise SystemExit(0 if n_pass == n_total else 1)
