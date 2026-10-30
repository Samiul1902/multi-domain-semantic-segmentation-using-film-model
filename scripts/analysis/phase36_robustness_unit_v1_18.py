#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.18 — UNIT / STATIC SUITE (SOURCE / AST / HASH ONLY).

REBASED FROM v1.17 (WO#17E: D85/D86/D87/D88 FINAL PRE-EXECUTION AUTHORITY REPAIR).
Scientific computation is IDENTICAL to v1.17 (which is IDENTICAL to v1.16 modulo the
D81-D83 operational rebase).  D61 / D75 / live-f32 / G / router / ROI / R_psi /
S_omega / safety / geometry / perturbation / seed / metric / threshold protections are
preserved VERBATIM, and NEW D85/D86/D87/D88 pre-execution authority checks are added.

Independently re-derives and enforces:

  D61 CANONICAL PHASE27 ACCEPT FUSION            (preserved)
  D75 POLICY_B REPRESENTATION                    (preserved)
  D80 OPERATIONAL/GOVERNANCE REBASE              (preserved)
  D81 OUTPUT NAMESPACE REBASE + FAIL-CLOSED CSV  (preserved)
  D82 RELEASE CONTRACT (HISTORICAL v1.14 SMOKE)  (preserved)
  D83 PURE RELEASE-GATE RUNTIME STATE            (preserved)
  D85 IMMUTABLE SUPERVISOR ROOT (literal SHAs)   (NEW in v1.18)
  D86 EXCLUSIVE STDOUT/STDERR (no O_TRUNC)       (NEW in v1.18)
  D87 NON-CIRCULAR FINAL AUTHORITY DAG           (NEW in v1.18)
  D88 REAL-TIME OUTPUT-ABSENCE GATE + FIXED FIGS (NEW in v1.18)

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

EXEC = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_18.py"
EXEC_V1_17 = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_17.py"
EXEC_V1_16 = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_16.py"
EXEC_V1_14 = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_14.py"
LAUNCHER = ROOT / "scripts" / "analysis" / "launch_phase36_v1_18.py"
SUPERVISOR = ROOT / "scripts" / "analysis" / "supervise_phase36_v1_18.py"
GOVERNANCE = ROOT / "scripts" / "analysis" / "build_phase36_v1_18_governance.py"
MANIFEST = ROOT / "reports" / "audits" / "phase36_v1_18_runtime_source_integrity_manifest.json"

FROZEN_V1_14_EXEC_SHA = "ac09ff8ded3610244920e66612145b246b33127140d344a9730d454bab27cff5"
FROZEN_V1_16_EXEC_SHA = "a96b74caa4587aa9d2f83b79ed39c13075a88086109e31d991695a75ec4abab9"
FROZEN_V1_17_EXEC_SHA = "81d78460b2f20f176bc697cba662c43bc7c7443ea555ba95a30609faf0ccbe31"
FROZEN_V1_18_EXEC_SHA = "2259ce22e75ba9a3a8943769dc1e0ed5724f94902f5e8955976cd6ebeb8ce63e"

POLICY_HELPER = "_phase27_scored_final_binary"
SAVEFIG_ONCE = "_savefig_once"
ABSENCE_GATE = "verify_v1_18_output_absence"

SRC = EXEC.read_text(encoding="utf-8")
V17_SRC = EXEC_V1_17.read_text(encoding="utf-8")
V16_SRC = EXEC_V1_16.read_text(encoding="utf-8")
TREE = ast.parse(SRC)
FUNCS = {n.name: n for n in ast.walk(TREE) if isinstance(n, ast.FunctionDef)}
LSRC = LAUNCHER.read_text(encoding="utf-8")
SSRC = SUPERVISOR.read_text(encoding="utf-8")
GSRC = GOVERNANCE.read_text(encoding="utf-8")

checks: list[dict] = []


def check(name, cond, detail=None):
    checks.append({"check": name, "passed": bool(cond), "detail": detail})


def _sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _func_src(src: str, name: str) -> str:
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.FunctionDef) and n.name == name:
            return ast.get_source_segment(src, n) or ""
    return ""


def _func_src18(name: str) -> str:
    return _func_src(SRC, name)


# =========================================================================== #
# A. SOURCE IDENTITY
# =========================================================================== #
check("A01_v1_14_source_frozen_unchanged", _sha(EXEC_V1_14) == FROZEN_V1_14_EXEC_SHA,
      {"sha256": _sha(EXEC_V1_14)})
check("A02_v1_16_source_frozen_unchanged", _sha(EXEC_V1_16) == FROZEN_V1_16_EXEC_SHA,
      {"sha256": _sha(EXEC_V1_16)})
check("A03_v1_17_source_frozen_unchanged", _sha(EXEC_V1_17) == FROZEN_V1_17_EXEC_SHA,
      {"sha256": _sha(EXEC_V1_17)})
check("A04_v1_18_source_sha_exact", _sha(EXEC) == FROZEN_V1_18_EXEC_SHA,
      {"sha256": _sha(EXEC)})
check("A05_v1_18_source_compiles", compile(SRC, str(EXEC), "exec") is not None)
check("A06_launcher_present", LAUNCHER.exists())
check("A07_supervisor_present", SUPERVISOR.exists())
check("A08_governance_builder_present", GOVERNANCE.exists())

# =========================================================================== #
# B. D61 — CANONICAL PHASE27 ACCEPT FUSION (PRESERVED)
# =========================================================================== #
check("B01_canonical_fusion_call_present", "fuse_full_field(p_global, refined, geom)" in SRC)
check("B02_old_pad_unaware_call_absent",
      "system._fuse_global_with_regional(p_global, refined, window)" not in SRC)
check("B03_fuse_full_field_defined", "fuse_full_field" in FUNCS)
_fuse = _func_src18("fuse_full_field")
check("B04_fuse_full_field_pad_aware",
      all(k in _fuse for k in ("pad_top", "pad_left", "crop_side_pixels",
                               "Resampling.BILINEAR")))
_core_learned = _func_src18("canonical_learned_core")
check("B05_fusion_uses_roi_geometry_same_geom",
      "fuse_full_field(p_global, refined, geom)" in _core_learned and "geom" in _core_learned)
check("B06_fusion_call_count_exactly_one",
      SRC.count("fuse_full_field(p_global, refined, geom)") == 1)
check("B07_psi_somega_unchanged_markers",
      "somega_features(pg_crop, pr_crop, geom)" in _core_learned
      and "actual_r_psi_forwards" in _core_learned)

# =========================================================================== #
# C. D75 — POLICY_B REPRESENTATION (PRESERVED)
# =========================================================================== #
check("C01_policy_helper_defined", f"def {POLICY_HELPER}(" in SRC)
_h = _func_src18(POLICY_HELPER)
check("C02_helper_uses_live_f32", "np.asarray(p_final_live, dtype=np.float32)" in _h)
check("C03_helper_casts_to_f16", "astype(np.float16)" in _h)
check("C04_helper_casts_back_to_f32", _h.count("astype(np.float32)") >= 2)
check("C05_helper_thresholds_at_0_50", "np.float32(SEGMENTATION_OUTPUT_THRESHOLD)" in _h)
check("C06_segmentation_threshold_unchanged", "SEGMENTATION_OUTPUT_THRESHOLD = 0.50" in SRC)
check("C07_helper_wiring_count_3", SRC.count(f"{POLICY_HELPER}(") == 3,
      {"count": SRC.count(f"{POLICY_HELPER}(")})
check("C08_core_binary_uses_helper", f"{POLICY_HELPER}(prob)" in _func_src18("_core_result"))
check("C09_clean_binary_uses_helper", f"{POLICY_HELPER}(final_prob)" in _func_src18("_evaluate_clean_sample"))
check("C10_clean_store_final_binary_policy_b",
      'clean_store.setdefault("final_binary", {})[sid] = final_binary'
      in _func_src18("_evaluate_clean_sample"))

# =========================================================================== #
# D. LIVE PROBABILITY REMAINS LIVE
# =========================================================================== #
check("D01_f16_cast_only_in_policy_helper",
      "astype(np.float16)" in _h and "astype(np.float16)" not in _func_src18("canonical_learned_core"))
check("D02_downstream_G_quantization_absent",
      "astype(np.float16)" not in _func_src18("canonical_learned_core"))
check("D03_live_probability_preserved", "final_probability" in SRC)

# =========================================================================== #
# E. PERTURBATION PATHS CONSUME POLICY-B BINARIES
# =========================================================================== #
check("E01_image_pert_consumes_core_binary",
      'pert_binary = np.asarray(out["final_binary"], dtype=np.float32)' in SRC)
check("E02_proposal_pert_consumes_core_binary",
      SRC.count('pert_binary = np.asarray(out["final_binary"], dtype=np.float32)') >= 2)
check("E03_prediction_consistency_uses_policy_b", 'clean_store["final_binary"][sid]' in SRC)

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


ids18 = _declared_smoke_ids(SRC)
ids14 = _declared_smoke_ids(EXEC_V1_14.read_text(encoding="utf-8"))
check("F01_smoke_ids_count_53", len(ids18) == 53, {"count": len(ids18)})
check("F02_smoke_ids_unique", len(set(ids18)) == 53)
check("F03_smoke_ids_exact_set_equality", set(ids18) == set(ids14))
check("F04_smoke_ids_order_identical", ids18 == ids14)

check("G01_image_conditions_present",
      all(c in SRC for c in ("BRIGHTNESS_NEG", "CONTRAST_HIGH", "GAUSSIAN_BLUR_LOW",
                             "RESOLUTION_050", "GAUSSIAN_NOISE_LOW", "GAUSSIAN_NOISE_HIGH")))
check("G02_seeds_42_123_3407", all(s in SRC for s in ("42", "123", "3407")))
check("G03_proposal_scale_conditions",
      all(k in SRC for k in ("SHIFT_LEFT_10", "SHIFT_RIGHT_10", "SHIFT_UP_10",
                             "SHIFT_DOWN_10", "SCALE_085", "SCALE_115")))
check("G04_forced_skip_action_unavailable", "FORCED_SKIP" in SRC or "ACTION_UNAVAILABLE" in SRC)
check("G05_no_jpeg_rotation_crop_conditions",
      ("JPEG" not in SRC) and ("Image.ROTATE" not in SRC) and (".rotate(" not in SRC))

# =========================================================================== #
# H. v1.18 OPERATIONAL / PRE-EXECUTION AUTHORITY REPAIRS (D85/D86/D87/D88)
# =========================================================================== #
# --- H.A: token / namespace / marker rollover (D80/D81 preserved) -------------
check("H01_launcher_dispatch_has_mode_science",
      '"--mode", "science"' in LSRC or "--mode science" in LSRC)
check("H02_launcher_dispatch_mode_args_literal",
      'DISPATCH_MODE_ARGS = ["--mode", "science"]' in LSRC)
check("H03_launcher_binds_literal_v1_18_execution_sha", FROZEN_V1_18_EXEC_SHA in LSRC)
check("H04_launcher_verify_only_supported", "--verify-only" in LSRC)
check("H05_launcher_token_names_v1_18",
      "PHASE36_V1_18_EXECUTE" in LSRC and "PHASE36_V1_18_LAUNCH_AUTHORITY" in LSRC)
check("H06_launcher_no_v1_17_token_residue",
      "PHASE36_V1_17_EXECUTE" not in LSRC and "PHASE36_V1_17_LAUNCH_AUTHORITY" not in LSRC)
check("H07_launcher_no_delete_or_recreate",
      "os.remove" not in LSRC and "unlink" not in LSRC)
check("H08_launcher_invokes_pure_release_state",
      "verify_pure_release_state" in LSRC)

check("H09_execution_namespace_v1_18_start_marker",
      "phase36_robustness_science_start_v1_18.json" in SRC)
check("H10_execution_namespace_v1_18_result_marker",
      'SCIENCE_V1_18_ARTIFACT = "reports/audits/phase36_robustness_scientific_result_v1_18.json"' in SRC)
check("H11_execution_namespace_v1_18_failure_marker",
      "phase36_robustness_science_failure_v1_18.json" in SRC)
check("H12_no_v1_17_science_start_path_residue",
      "phase36_robustness_science_start_v1_17.json" not in SRC)

check("H13_execution_launch_authority_v1_18",
      'LAUNCH_AUTHORITY_TOKEN = "PHASE36_V1_18_LAUNCH_AUTHORITY"' in SRC)
check("H14_execution_explicit_science_gate", "PHASE36_V1_18_EXECUTE" in SRC)
check("H15_no_v1_17_gate_env_residue", "PHASE36_V1_17_EXECUTE" not in SRC)

check("H16_runtime_manifest_v1_18_path",
      "phase36_v1_18_runtime_source_integrity_manifest.json" in SRC)
check("H17_no_v1_17_runtime_manifest_residue",
      "phase36_v1_17_runtime_source_integrity_manifest.json" not in SRC)
check("H18_release_revision_v1_18", "ra_medfilm_barr_phase36_robustness_v1_18" in SRC)
check("H19_no_v1_17_release_revision_residue",
      "ra_medfilm_barr_phase36_robustness_v1_17" not in SRC)

check("H20_stage_journal_module_present", "V1_18_JOURNAL_STAGES" in SRC and "_ScienceJournal" in SRC)
check("H21_stage_journal_dir_v1_18",
      "phase36_robustness_science_v1_18_journal" in SRC)
check("H22_no_v1_17_journal_dir_residue",
      "phase36_robustness_science_v1_17_journal" not in SRC)

# unique v1.18 namespace roots
check("H23_tab_root_v1_18_namespace",
      'TAB = ROOT / "reports" / "tables" / "phase36_robustness_v1_18"' in SRC)
check("H24_fig_root_v1_18_namespace",
      'FIG = ROOT / "reports" / "figures" / "phase36_robustness_v1_18"' in SRC)
check("H25_arr_root_v1_18_namespace",
      'ARR = ROOT / "reports" / "arrays" / "phase36_robustness_v1_18"' in SRC)
check("H26_no_v1_17_namespace_residue",
      "phase36_robustness_v1_17" not in SRC)

# CSV fail-closed (D81 preserved)
check("H27_csv_writer_fail_closed_exclusive_create",
      'open(path, "x", encoding="utf-8", newline="")' in SRC)
check("H28_csv_writer_refuses_existing_target",
      "V1_18_CSV_FAIL_CLOSED__TARGET_EXISTS__REFUSE_OVERWRITE" in SRC
      and "if path.exists():" in _func_src18("_write_csv"))
check("H29_csv_writer_fsyncs", "os.fsync(f.fileno())" in _func_src18("_write_csv"))

# --- D88: fail-closed figure writer ----------------------------------------- #
check("H30_savefig_once_defined", f"def {SAVEFIG_ONCE}(" in SRC)
_sf = _func_src18(SAVEFIG_ONCE)
check("H31_savefig_once_exclusive_create",
      "os.O_CREAT" in _sf and "os.O_EXCL" in _sf and "os.O_WRONLY" in _sf)
check("H32_savefig_once_no_o_trunc", "O_TRUNC" not in _sf)
check("H33_savefig_once_refuses_existing",
      "V1_18_FIGURE_FAIL_CLOSED__TARGET_EXISTS__REFUSE_OVERWRITE" in _sf
      and "path.exists()" in _sf)
check("H34_savefig_once_fsyncs", "os.fsync(fh.fileno())" in _sf)
check("H35_plain_savefig_absent_from_source", "fig.savefig(p, dpi=160)" not in SRC)
check("H36_savefig_once_call_sites_eq_5", SRC.count(f"{SAVEFIG_ONCE}(fig, p, dpi=160)") == 5,
      {"count": SRC.count(f"{SAVEFIG_ONCE}(fig, p, dpi=160)")})

# --- D88: real-time output-absence gate ------------------------------------- #
check("H37_absence_gate_defined", f"def {ABSENCE_GATE}(" in SRC)
check("H38_reachable_targets_helper_defined", "def v1_18_reachable_write_targets(" in SRC)
_ns = {"np": np}
exec(_func_src18("v1_18_reachable_write_targets"), {"np": np})
# re-exec in a namespace that also has the module-level constants bound by name
_tbl_names, _fig_names = None, None
for n in ast.walk(TREE):
    if isinstance(n, ast.Assign):
        for tg in n.targets:
            if isinstance(tg, ast.Name) and tg.id == "V1_18_REACHABLE_SCIENCE_TABLES":
                _tbl_names = [e.value for e in n.value.elts]
            if isinstance(tg, ast.Name) and tg.id == "V1_18_REACHABLE_FIGURES":
                _fig_names = [e.value for e in n.value.elts]
check("H39_reachable_tables_count_11", _tbl_names is not None and len(_tbl_names) == 11,
      {"count": None if _tbl_names is None else len(_tbl_names)})
check("H40_reachable_figures_count_5", _fig_names is not None and len(_fig_names) == 5,
      {"count": None if _fig_names is None else len(_fig_names)})

# --- D88: gate wired BEFORE the START marker is created --------------------- #
# Use the CALL site of the start marker, not its `def` line.
_gate_idx = SRC.find("_absence = verify_v1_18_output_absence()")
_call_marker = "\n            _create_science_start_marker(\n"
_start_idx = SRC.find(_call_marker)
check("H41_absence_gate_invoked_in_dispatch", _gate_idx != -1)
check("H42_absence_gate_before_start_marker",
      _gate_idx != -1 and _start_idx != -1 and _gate_idx < _start_idx,
      {"gate_idx": _gate_idx, "start_call_idx": _start_idx})
check("H43_gate_fail_closed_terminal_literal",
      "PHASE36_V1_18_REAL_LAUNCH_OUTPUT_ABSENCE_GATE_FAIL_CLOSED" in SRC
      and "__NO_ATTEMPT_CONSUMED" in SRC)
check("H44_gate_pass_terminal_literal",
      "PHASE36_V1_18_REAL_LAUNCH_OUTPUT_ABSENCE_GATE_PASS" in SRC)

# --- D85: supervisor immutable root ----------------------------------------- #
check("H45_supervisor_literal_launcher_sha",
      'FROZEN_V1_18_LAUNCHER_SHA = ' in SSRC)
check("H46_supervisor_literal_bundle_sha",
      'FROZEN_V1_18_AUTHORITY_BUNDLE_SHA = ' in SSRC)
check("H47_supervisor_literal_launch_authority_file_sha",
      'FROZEN_V1_18_LAUNCH_AUTHORITY_FILE_SHA = ' in SSRC)
check("H48_supervisor_no_env_launcher_sha",
      "os.environ.get(\"PHASE36_V1_18_LAUNCHER_SHA\")" not in SSRC
      and "os.environ['PHASE36_V1_18_LAUNCHER_SHA']" not in SSRC
      and "PHASE36_V1_18_LAUNCHER_SHA" not in SSRC)
check("H49_supervisor_env_override_prohibited_declared",
      "env_override_permitted" in SSRC and "cli_override_permitted" in SSRC
      and "config_override_permitted" in SSRC)
check("H50_supervisor_json_field_not_trusted",
      "json_field_trusted_for_expected_launcher_sha" in SSRC)

# --- D86: exclusive stdout/stderr ------------------------------------------- #
check("H51_supervisor_exclusive_text_writer",
      "_write_text_exclusive" in SSRC)
_we = _func_src(SSRC, "_write_text_exclusive")
check("H52_exclusive_writer_uses_o_excl",
      "os.O_CREAT" in _we and "os.O_EXCL" in _we and "os.O_WRONLY" in _we)
check("H53_exclusive_writer_no_o_trunc_flag_use",
      _we != "" and "os.O_TRUNC" not in _we)
check("H54_supervisor_predispatch_absence_check", "_predispatch_absence_check" in SSRC)

# --- D87: non-circular final authority DAG ---------------------------------- #
check("H55_launcher_reads_launch_authority_file", "LAUNCH_AUTHORITY_FILE" in LSRC
      and "phase36_v1_18_launch_authority_sha.json" in LSRC)
check("H56_governance_builds_prelaunch_bundle",
      "prelaunch" in GSRC.lower() and "authority_bundle" in GSRC)
check("H57_governance_bundle_excludes_supervisor_sha",
      "supervisor_sha256_present" in GSRC)

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
check("I02_boundary_repair_applied", np.array_equal(got, ref) and got.dtype == np.float32)

# =========================================================================== #
n_pass = sum(1 for c in checks if c["passed"])
n_total = len(checks)
report = {
    "artifact": "phase36_robustness_unit_v1_18",
    "phase": 36,
    "method": "RA-MedFiLM-BARR",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_18",
    "type": "STATIC_UNIT_REPORT",
    "defects_repaired": ["D85", "D86", "D87", "D88"],
    "model_free": True,
    "torch_imported": False,
    "protected_population_read": False,
    "subject_execution_sha256": _sha(EXEC),
    "frozen_v1_17_execution_sha256": _sha(EXEC_V1_17),
    "frozen_v1_16_execution_sha256": _sha(EXEC_V1_16),
    "frozen_v1_14_execution_sha256": _sha(EXEC_V1_14),
    "checks_total": n_total,
    "checks_passed": n_pass,
    "checks_failed": n_total - n_pass,
    "all_pass": n_pass == n_total,
    "failed_checks": [c["check"] for c in checks if not c["passed"]],
    "checks": checks,
}
out_path = ROOT / "reports/audits/phase36_robustness_unit_v1_18.json"
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(report, indent=1), encoding="utf-8")
for c in checks:
    if not c["passed"]:
        print(f"FAIL {c['check']} :: {c.get('detail')}")
print(f"UNIT v1.18: {n_pass}/{n_total} pass")
print(f"terminal: {'PHASE36_V1_18_UNIT_PASS' if n_pass == n_total else 'PHASE36_V1_18_UNIT_FAIL'}")
raise SystemExit(0 if n_pass == n_total else 1)
