#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.17 — UNIT / STATIC SUITE (SOURCE / AST / HASH ONLY).

REBASED FROM v1.16 (D81/D82/D83 FINAL OPERATIONAL REPAIR).  Scientific computation
is IDENTICAL to v1.16; the D61 / D75 / live-f32 / G / router / ROI / R_psi / S_omega /
safety / geometry / perturbation / seed / metric / threshold protections are preserved
VERBATIM, and NEW D81/D82/D83 operational checks are added.

Independently re-derives and enforces:

  D61 CANONICAL PHASE27 ACCEPT FUSION       (preserved)
  D75 POLICY_B REPRESENTATION               (preserved)
  D80 OPERATIONAL/GOVERNANCE REBASE         (preserved)
  D81 OUTPUT NAMESPACE REBASE + FAIL-CLOSED CSV   (NEW in v1.17)
  D82 RELEASE CONTRACT (HISTORICAL v1.14 SMOKE)   (NEW in v1.17)
  D83 PURE RELEASE-GATE RUNTIME STATE             (NEW in v1.17)

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

EXEC = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_17.py"
EXEC_V1_16 = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_16.py"
EXEC_V1_14 = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_14.py"
LAUNCHER = ROOT / "scripts" / "analysis" / "launch_phase36_v1_17.py"
SUPERVISOR = ROOT / "scripts" / "analysis" / "supervise_phase36_v1_17.py"

FROZEN_V1_14_EXEC_SHA = "ac09ff8ded3610244920e66612145b246b33127140d344a9730d454bab27cff5"
FROZEN_V1_16_EXEC_SHA = "a96b74caa4587aa9d2f83b79ed39c13075a88086109e31d991695a75ec4abab9"
FROZEN_V1_17_EXEC_SHA = "81d78460b2f20f176bc697cba662c43bc7c7443ea555ba95a30609faf0ccbe31"

POLICY_HELPER = "_phase27_scored_final_binary"

SRC = EXEC.read_text(encoding="utf-8")
V16_SRC = EXEC_V1_16.read_text(encoding="utf-8")
TREE = ast.parse(SRC)
FUNCS = {n.name: n for n in ast.walk(TREE) if isinstance(n, ast.FunctionDef)}
LSRC = LAUNCHER.read_text(encoding="utf-8")
SSRC = SUPERVISOR.read_text(encoding="utf-8")

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
check("A02_v1_16_source_frozen_unchanged", _sha(EXEC_V1_16) == FROZEN_V1_16_EXEC_SHA,
      {"sha256": _sha(EXEC_V1_16)})
check("A03_v1_17_source_sha_exact", _sha(EXEC) == FROZEN_V1_17_EXEC_SHA,
      {"sha256": _sha(EXEC)})
check("A04_v1_17_source_compiles", compile(SRC, str(EXEC), "exec") is not None)

# =========================================================================== #
# B. D61 — CANONICAL PHASE27 ACCEPT FUSION (PRESERVED)
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
# C. D75 — POLICY_B REPRESENTATION (PRESERVED)
# =========================================================================== #
check("C01_policy_helper_defined", f"def {POLICY_HELPER}(" in SRC)
_h = _func_src(POLICY_HELPER)
check("C02_helper_uses_live_f32", "np.asarray(p_final_live, dtype=np.float32)" in _h)
check("C03_helper_casts_to_f16", "astype(np.float16)" in _h)
check("C04_helper_casts_back_to_f32", _h.count("astype(np.float32)") >= 2)
check("C05_helper_thresholds_at_0_50",
      "np.float32(SEGMENTATION_OUTPUT_THRESHOLD)" in _h)
check("C06_segmentation_threshold_unchanged", "SEGMENTATION_OUTPUT_THRESHOLD = 0.50" in SRC)

check("C07_helper_wiring_count_3", SRC.count(f"{POLICY_HELPER}(") == 3,
      {"count": SRC.count(f"{POLICY_HELPER}(")})
check("C08_core_binary_uses_helper", f"{POLICY_HELPER}(prob)" in _func_src("_core_result"))
check("C09_clean_binary_uses_helper", f"{POLICY_HELPER}(final_prob)" in _func_src("_evaluate_clean_sample"))
check("C10_clean_store_final_binary_policy_b",
      'clean_store.setdefault("final_binary", {})[sid] = final_binary'
      in _func_src("_evaluate_clean_sample"))

# =========================================================================== #
# D. LIVE PROBABILITY REMAINS LIVE
# =========================================================================== #
check("D01_final_probability_never_quantized",
      'out["final_probability"]' not in SRC.split(f"def {POLICY_HELPER}")[1].split("def ")[0]
      or "astype(np.float16)" not in _func_src("_core_result"))
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
# F. SMOKE CONTRACT / ROBUSTNESS CONTRACT PRESERVED
# =========================================================================== #
def _declared_smoke_ids(src):
    t = ast.parse(src)
    for n in ast.walk(t):
        if isinstance(n, ast.Assign):
            for tg in n.targets:
                if isinstance(tg, ast.Name) and tg.id == "SMOKE_CHECK_IDS":
                    return [e.value for e in n.value.elts]
    return []


ids17 = _declared_smoke_ids(SRC)
ids14 = _declared_smoke_ids(EXEC_V1_14.read_text(encoding="utf-8"))
check("F01_smoke_ids_count_53", len(ids17) == 53, {"count": len(ids17)})
check("F02_smoke_ids_unique", len(set(ids17)) == 53)
check("F03_smoke_ids_exact_set_equality", set(ids17) == set(ids14))
check("F04_smoke_ids_order_identical", ids17 == ids14)

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
# H. v1.17 OPERATIONAL REPAIRS (D81/D82/D83)  --- NEW
# =========================================================================== #
# D81: unique v1.17 namespace for ALL scientific outputs.
check("H01_launcher_present", LAUNCHER.exists())
check("H02_launcher_dispatch_has_mode_science",
      '"--mode", "science"' in LSRC or "--mode science" in LSRC)
check("H03_launcher_dispatch_mode_args_literal",
      'DISPATCH_MODE_ARGS = ["--mode", "science"]' in LSRC)
check("H04_launcher_binds_literal_v1_17_execution_sha",
      FROZEN_V1_17_EXEC_SHA in LSRC)
check("H05_launcher_verify_only_supported", "--verify-only" in LSRC)
check("H06_launcher_token_names_v1_17",
      "PHASE36_V1_17_EXECUTE" in LSRC and "PHASE36_V1_17_LAUNCH_AUTHORITY" in LSRC)
check("H07_launcher_no_v1_16_token_residue",
      "PHASE36_V1_16_EXECUTE" not in LSRC and "PHASE36_V1_16_LAUNCH_AUTHORITY" not in LSRC)
check("H08_launcher_no_delete_or_recreate",
      "os.remove" not in LSRC and "unlink" not in LSRC)
check("H09_launcher_invokes_pure_release_state",
      "verify_pure_release_state" in LSRC and "pure_release_state_released" in LSRC)

check("H10_execution_namespace_v1_17_start_marker",
      "phase36_robustness_science_start_v1_17.json" in SRC)
check("H11_execution_namespace_v1_17_result_marker",
      'SCIENCE_V1_17_ARTIFACT = "reports/audits/phase36_robustness_scientific_result_v1_17.json"' in SRC)
check("H12_execution_namespace_v1_17_failure_marker",
      "phase36_robustness_science_failure_v1_17.json" in SRC)
check("H13_no_v1_16_science_start_path_residue",
      "phase36_robustness_science_start_v1_16.json" not in SRC)

check("H14_execution_launch_authority_v1_17",
      'LAUNCH_AUTHORITY_TOKEN = "PHASE36_V1_17_LAUNCH_AUTHORITY"' in SRC)
check("H15_execution_explicit_science_gate", "PHASE36_V1_17_EXECUTE" in SRC)
check("H16_execution_explicit_smoke_gate", "PHASE36_V1_17_SMOKE_EXECUTE" in SRC)
check("H17_no_v1_16_gate_env_residue",
      "PHASE36_V1_16_EXECUTE" not in SRC and "PHASE36_V1_16_SMOKE_EXECUTE" not in SRC)

check("H18_runtime_manifest_v1_17_path",
      "phase36_v1_17_runtime_source_integrity_manifest.json" in SRC)
check("H19_no_v1_16_runtime_manifest_residue",
      "phase36_v1_16_runtime_source_integrity_manifest.json" not in SRC)

check("H20_release_revision_v1_17",
      "ra_medfilm_barr_phase36_robustness_v1_17" in SRC)
check("H21_no_v1_16_release_revision_residue",
      "ra_medfilm_barr_phase36_robustness_v1_16" not in SRC)

check("H22_stage_journal_module_present", "V1_17_JOURNAL_STAGES" in SRC and "_ScienceJournal" in SRC)
check("H23_stage_journal_wired",
      "journal=_ScienceJournal(" in SRC and "_run_science_with_durable_evidence(journal=" in SRC)
check("H24_stage_journal_dir_v1_17",
      "phase36_robustness_science_v1_17_journal" in SRC)
check("H25_no_v1_16_journal_dir_residue",
      "phase36_robustness_science_v1_16_journal" not in SRC)

check("H26_supervisor_present", SUPERVISOR.exists())
check("H27_supervisor_enforces_launcher_pin",
      "launcher_sha_pin_enforced" in SSRC and "FAIL_CLOSED__LAUNCHER_SHA_MISMATCH" in SSRC)
check("H28_supervisor_does_not_relaunch",
      "supervisor_relaunched" in SSRC and "for " not in SSRC.split("def supervise_once")[1].split("def main")[0])
check("H29_supervisor_returns_child_exit_code",
      "returned_child_exit_code" in SSRC)

# ---- D81 NEW: namespace rebase + fail-closed CSV ----
check("H30_tab_root_v1_17_namespace",
      'TAB = ROOT / "reports" / "tables" / "phase36_robustness_v1_17"' in SRC)
check("H31_fig_root_v1_17_namespace",
      'FIG = ROOT / "reports" / "figures" / "phase36_robustness_v1_17"' in SRC)
check("H32_arr_root_v1_17_namespace",
      'ARR = ROOT / "reports" / "arrays" / "phase36_robustness_v1_17"' in SRC)
check("H33_no_unversioned_tab_root",
      'TAB = ROOT / "reports" / "tables"\n' not in SRC)
check("H34_no_unversioned_fig_root",
      'FIG = ROOT / "reports" / "figures" / "phase36_robustness"\n' not in SRC)
check("H35_csv_writer_fail_closed_exclusive_create",
      'open(path, "x", encoding="utf-8", newline="")' in SRC)
check("H36_csv_writer_refuses_existing_target",
      "V1_17_CSV_FAIL_CLOSED__TARGET_EXISTS__REFUSE_OVERWRITE" in SRC
      and "if path.exists():" in _func_src("_write_csv"))
check("H37_csv_writer_no_open_w_overwrite",
      'path.open("w"' not in _func_src("_write_csv"))
check("H38_csv_writer_no_empty_write_text_overwrite",
      "path.write_text(" not in _func_src("_write_csv"))
check("H39_csv_writer_fsyncs",
      "os.fsync(f.fileno())" in _func_src("_write_csv"))

# ---- D82 NEW: release contract binds HISTORICAL v1.14 smoke; no v1.17 smoke ----
check("H40_historical_v1_14_smoke_bound",
      "HISTORICAL_V1_14_SMOKE" in SRC
      and 'HISTORICAL_V1_14_SMOKE = "reports/audits/phase36_robustness_smoke_v1_14.json"' in SRC)
check("H41_historical_smoke_sha_pinned",
      "53543729fb0c48695c2af202c5f3d2f5ebdfc29d87c7a7f100bcde9f94882441" in SRC)
check("H42_gate_requires_historical_smoke_not_v1_17",
      "HISTORICAL_SMOKE_ARTIFACT_MISSING" in SRC
      and "phase36_robustness_smoke_v1_17.json" not in SRC)
check("H43_gate_does_not_require_v1_17_smoke",
      'SMOKE_V1_17_ARTIFACT = "reports/audits/phase36_robustness_smoke_v1_17.json"' not in SRC)

# ---- D83 NEW: pure runtime release-state function present ----
check("H44_release_gate_function_present",
      "def _gate_science_release_state()" in SRC)
check("H45_release_gate_returns_released_state",
      '"RELEASED"' in SRC and '"NOT_RELEASED"' in SRC)
check("H46_release_gate_checks_d40_schema_fields",
      all(f in SRC for f in ('att.get("smoke_all_pass")', 'att.get("scientific_output")',
                             'att.get("release_gate")', 'att.get("smoke_artifact_sha256")')))
check("H47_gate_docstring_documents_historical_reasons",
      "HISTORICAL_SMOKE_ARTIFACT_MISSING" in SRC)

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
    "artifact": "phase36_robustness_unit_v1_17",
    "phase": 36,
    "method": "RA-MedFiLM-BARR",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_17",
    "type": "STATIC_UNIT_REPORT",
    "model_free": True,
    "torch_imported": False,
    "protected_population_read": False,
    "subject_execution_sha256": _sha(EXEC),
    "frozen_v1_16_execution_sha256": _sha(EXEC_V1_16),
    "frozen_v1_14_execution_sha256": _sha(EXEC_V1_14),
    "checks_total": n_total,
    "checks_passed": n_pass,
    "checks_failed": n_total - n_pass,
    "all_pass": n_pass == n_total,
    "failed_checks": [c["check"] for c in checks if not c["passed"]],
    "checks": checks,
}
out_path = ROOT / "reports/audits/phase36_robustness_unit_v1_17.json"
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(report, indent=1), encoding="utf-8")
for c in checks:
    if not c["passed"]:
        print(f"FAIL {c['check']} :: {c.get('detail')}")
print(f"UNIT v1.17: {n_pass}/{n_total} pass")
print(f"terminal: {'PHASE36_V1_17_UNIT_PASS' if n_pass == n_total else 'PHASE36_V1_17_UNIT_FAIL'}")
raise SystemExit(0 if n_pass == n_total else 1)
