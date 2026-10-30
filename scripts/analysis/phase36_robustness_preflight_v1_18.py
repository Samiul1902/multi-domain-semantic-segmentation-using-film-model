#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.18 — STATIC PREFLIGHT (SOURCE / AST / HASH ONLY; NO EXECUTION).

REBASED FROM v1.17 (WO#17E: D85/D86/D87/D88 FINAL PRE-EXECUTION AUTHORITY REPAIR).

Aggregates the v1.18 static/governance gates and proves, from source bytes and AST
only, that D61 (canonical Phase27 ACCEPT fusion) and D75/POLICY_B are PRESERVED, the
v1.17 operational layer (D81/D82/D83) is PRESERVED, and the NEW v1.18 pre-execution
authority repairs D85 (immutable supervisor root), D86 (exclusive stdout/stderr),
D87 (non-circular final authority DAG) and D88 (real-time output-absence gate +
fail-closed figure writer) are in place.  All v1.18 attempt markers must be ABSENT.

NO torch.  NO model.  NO checkpoint.  NO CUDA.  NO forward.  NO smoke.  NO science.
NO VAL/GT read.  NO ROUTER_HOLDOUT.  NO TEST.
"""
from __future__ import annotations

import ast
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

EXEC = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_18.py"
EXEC_V1_17 = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_17.py"
EXEC_V1_16 = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_16.py"
EXEC_V1_14 = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_14.py"
LAUNCHER = ROOT / "scripts" / "analysis" / "launch_phase36_v1_18.py"
SUPERVISOR = ROOT / "scripts" / "analysis" / "supervise_phase36_v1_18.py"
MANIFEST = ROOT / "reports" / "audits" / "phase36_v1_18_runtime_source_integrity_manifest.json"
RELEASE_ATT = ROOT / "reports" / "audits" / "phase36_v1_18_science_release_attestation.json"
ADJUDICATION = ROOT / "reports" / "audits" / "phase36_v1_18_adjudication_d85_d86_d87_d88.json"
BUNDLE = ROOT / "reports" / "audits" / "phase36_v1_18_prelaunch_authority_bundle.json"
RW_INVENTORY = ROOT / "reports" / "audits" / "phase36_v1_18_reachable_write_target_inventory.json"
LAUNCH_AUTHORITY = ROOT / "reports" / "audits" / "phase36_v1_18_launch_authority_sha.json"

FROZEN_V1_14_EXEC_SHA = "ac09ff8ded3610244920e66612145b246b33127140d344a9730d454bab27cff5"
FROZEN_V1_16_EXEC_SHA = "a96b74caa4587aa9d2f83b79ed39c13075a88086109e31d991695a75ec4abab9"
FROZEN_V1_17_EXEC_SHA = "81d78460b2f20f176bc697cba662c43bc7c7443ea555ba95a30609faf0ccbe31"
FROZEN_V1_18_EXEC_SHA = "2259ce22e75ba9a3a8943769dc1e0ed5724f94902f5e8955976cd6ebeb8ce63e"
HISTORICAL_V1_14_SMOKE_SHA = "53543729fb0c48695c2af202c5f3d2f5ebdfc29d87c7a7f100bcde9f94882441"

checks = []


def check(name, cond, detail=None):
    checks.append({"check": name, "passed": bool(cond), "detail": detail})


def _sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


SRC = EXEC.read_text(encoding="utf-8")
TREE = ast.parse(SRC)
FUNCS = {n.name: n for n in ast.walk(TREE) if isinstance(n, ast.FunctionDef)}
LSRC = LAUNCHER.read_text(encoding="utf-8")
SSRC = SUPERVISOR.read_text(encoding="utf-8")


def _func(name):
    return ast.get_source_segment(SRC, FUNCS[name]) or ""


def _func_in(src, name):
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.FunctionDef) and n.name == name:
            return ast.get_source_segment(src, n) or ""
    return ""


# ---------------------------------------------------------------- #
# A. Source identity + compile
# ---------------------------------------------------------------- #
check("A01_v1_14_frozen_unchanged", _sha(EXEC_V1_14) == FROZEN_V1_14_EXEC_SHA,
      {"sha256": _sha(EXEC_V1_14)})
check("A02_v1_16_frozen_unchanged", _sha(EXEC_V1_16) == FROZEN_V1_16_EXEC_SHA)
check("A03_v1_17_frozen_unchanged", _sha(EXEC_V1_17) == FROZEN_V1_17_EXEC_SHA)
check("A04_v1_18_compiles", compile(SRC, str(EXEC), "exec") is not None)
check("A05_v1_18_source_sha", _sha(EXEC) == FROZEN_V1_18_EXEC_SHA)

# ---------------------------------------------------------------- #
# B. D61 canonical fusion (PRESERVED)
# ---------------------------------------------------------------- #
check("B01_canonical_fusion_present", "fuse_full_field(p_global, refined, geom)" in SRC)
check("B02_old_fusion_absent",
      "system._fuse_global_with_regional(p_global, refined, window)" not in SRC)
check("B03_fuse_full_field_pad_aware",
      all(k in _func("fuse_full_field") for k in ("pad_top", "pad_left", "crop_side_pixels")))

# ---------------------------------------------------------------- #
# C. D75 POLICY_B (PRESERVED)
# ---------------------------------------------------------------- #
check("C01_policy_helper_defined", "_phase27_scored_final_binary" in FUNCS)
check("C02_helper_wiring_3", SRC.count("_phase27_scored_final_binary(") == 3)
check("C03_threshold_0_50", "SEGMENTATION_OUTPUT_THRESHOLD = 0.50" in SRC)
check("C04_core_binary_helper", "_phase27_scored_final_binary(prob)" in _func("_core_result"))
check("C05_clean_binary_helper",
      "_phase27_scored_final_binary(final_prob)" in _func("_evaluate_clean_sample"))
check("C06_no_downstream_G_quantization",
      "astype(np.float16)" not in _func("canonical_learned_core"))

# ---------------------------------------------------------------- #
# D. Launcher binding + ordering (v1.18 rebased)
# ---------------------------------------------------------------- #
check("D01_launcher_present", LAUNCHER.exists())
check("D02_launcher_binds_literal_v1_18_sha", FROZEN_V1_18_EXEC_SHA in LSRC)
check("D03_launcher_verify_only", "--verify-only" in LSRC)
check("D04_no_auto_relaunch",
      all(k not in LSRC for k in ("os.execv", "os.execve", "os.remove", "unlink")))
check("D05_launcher_tokens_v1_18",
      "PHASE36_V1_18_EXECUTE" in LSRC and "PHASE36_V1_18_LAUNCH_AUTHORITY" in LSRC)
check("D06_supervisor_present", SUPERVISOR.exists())
check("D07_launcher_pins_literal_sha_constant",
      'V1_18_SOURCE_SHA = "' + FROZEN_V1_18_EXEC_SHA + '"' in LSRC)

# ---------------------------------------------------------------- #
# E. D80 operational/governance rebase (PRESERVED) + v1.18 namespace
# ---------------------------------------------------------------- #
check("E01_launcher_dispatch_mode_science", 'DISPATCH_MODE_ARGS = ["--mode", "science"]' in LSRC)
check("E02_launcher_dispatch_cmd_uses_mode_args", "list(DISPATCH_MODE_ARGS)" in LSRC)
check("E03_execution_v1_18_result_artifact",
      "phase36_robustness_scientific_result_v1_18.json" in SRC)
check("E04_no_v1_17_science_start_residue",
      "phase36_robustness_science_start_v1_17.json" not in SRC)
check("E05_execution_launch_authority_v1_18",
      'LAUNCH_AUTHORITY_TOKEN = "PHASE36_V1_18_LAUNCH_AUTHORITY"' in SRC)
check("E06_explicit_science_gate", "PHASE36_V1_18_EXECUTE" in SRC)
check("E07_no_v1_17_gate_residue", "PHASE36_V1_17_EXECUTE" not in SRC)
check("E08_runtime_manifest_v1_18_path",
      "phase36_v1_18_runtime_source_integrity_manifest.json" in SRC)
check("E09_no_v1_17_manifest_residue",
      "phase36_v1_17_runtime_source_integrity_manifest.json" not in SRC)
check("E10_release_revision_v1_18", "ra_medfilm_barr_phase36_robustness_v1_18" in SRC)
check("E11_no_v1_17_release_revision_residue",
      "ra_medfilm_barr_phase36_robustness_v1_17" not in SRC)
check("E12_stage_journal_module", "V1_18_JOURNAL_STAGES" in SRC and "_ScienceJournal" in SRC)
check("E13_stage_journal_wired",
      "journal=_ScienceJournal(" in SRC and "_run_science_with_durable_evidence(journal=" in SRC)
check("E14_stage_journal_dir_v1_18",
      "phase36_robustness_science_v1_18_journal" in SRC)

# ---------------------------------------------------------------- #
# F. D81 namespace rebase + fail-closed CSV (PRESERVED)
# ---------------------------------------------------------------- #
check("F01_tab_root_v1_18", 'TAB = ROOT / "reports" / "tables" / "phase36_robustness_v1_18"' in SRC)
check("F02_fig_root_v1_18", 'FIG = ROOT / "reports" / "figures" / "phase36_robustness_v1_18"' in SRC)
check("F03_arr_root_v1_18", 'ARR = ROOT / "reports" / "arrays" / "phase36_robustness_v1_18"' in SRC)
check("F04_no_v1_17_namespace_residue", "phase36_robustness_v1_17" not in SRC)
check("F05_csv_writer_exclusive_create", 'open(path, "x", encoding="utf-8", newline="")' in SRC)
check("F06_csv_writer_refuses_existing",
      "V1_18_CSV_FAIL_CLOSED__TARGET_EXISTS__REFUSE_OVERWRITE" in SRC)
check("F07_csv_writer_no_open_w", 'path.open("w"' not in _func("_write_csv"))
check("F08_csv_writer_fsync", "os.fsync(f.fileno())" in _func("_write_csv"))

# ---------------------------------------------------------------- #
# G. D82 release contract (PRESERVED)
# ---------------------------------------------------------------- #
check("G01_historical_v1_14_smoke_bound",
      'HISTORICAL_V1_14_SMOKE = "reports/audits/phase36_robustness_smoke_v1_14.json"' in SRC)
check("G02_historical_smoke_sha_pinned", HISTORICAL_V1_14_SMOKE_SHA in SRC)
check("G03_gate_no_v1_18_smoke_requirement",
      "phase36_robustness_smoke_v1_18.json" not in SRC)
check("G04_release_attestation_present", RELEASE_ATT.exists())
if RELEASE_ATT.exists():
    _att = json.loads(RELEASE_ATT.read_text(encoding="utf-8"))
    check("G05_attestation_has_d40_schema_fields",
          all(f in _att for f in ("smoke_artifact_sha256", "smoke_all_pass",
                                  "scientific_output", "release_gate")))
    check("G06_attestation_binds_v1_18_exec_sha",
          _att.get("execution_source_sha256") == FROZEN_V1_18_EXEC_SHA)
    check("G07_attestation_binds_historical_smoke_sha",
          _att.get("smoke_artifact_sha256") == HISTORICAL_V1_14_SMOKE_SHA)
    check("G08_attestation_does_not_require_v1_18_smoke",
          _att.get("requires_v1_18_smoke") is False)
else:
    for k in ("G05_attestation_has_d40_schema_fields", "G06_attestation_binds_v1_18_exec_sha",
              "G07_attestation_binds_historical_smoke_sha",
              "G08_attestation_does_not_require_v1_18_smoke"):
        check(k, False)

# ---------------------------------------------------------------- #
# H. D83 pure release-gate runtime state (PRESERVED)
# ---------------------------------------------------------------- #
check("H01_release_gate_function_present", "def _gate_science_release_state()" in SRC)
check("H02_launcher_invokes_pure_release_state",
      "verify_pure_release_state" in LSRC and "pure_release_state_released" in LSRC)
check("H03_launcher_requires_released",
      'results["pure_release_state_released"]' in LSRC)

# ---------------------------------------------------------------- #
# I. Manifest non-circularity + transitive integrity
# ---------------------------------------------------------------- #
_man = json.loads(MANIFEST.read_text(encoding="utf-8"))
check("I01_manifest_no_launcher_sha256", "launcher_sha256" not in _man)
check("I02_manifest_binds_v1_18_exec_source",
      _man.get("execution_source_sha256") == FROZEN_V1_18_EXEC_SHA)
check("I03_manifest_14_deps_4_ckpts",
      _man["n_dependencies"] == 14 and _man["n_checkpoints"] == 4)
check("I04_all_deps_match",
      all(_sha(ROOT / r) == (e["expected"] if isinstance(e, dict) else e)
          for r, e in _man["dependency_verification"].items()))
check("I05_all_ckpts_match",
      all(_sha(ROOT / r) == (e["expected"] if isinstance(e, dict) else e)
          for r, e in _man["checkpoint_verification"].items()))

# ---------------------------------------------------------------- #
# J. D87 non-circular final authority DAG
# ---------------------------------------------------------------- #
check("J01_prelaunch_bundle_exists", BUNDLE.exists())
if BUNDLE.exists():
    _b = json.loads(BUNDLE.read_text(encoding="utf-8"))
    _binds = _b.get("binds", {})
    check("J02_bundle_excludes_supervisor_sha",
          _b.get("supervisor_sha256_present") is False
          and "supervisor_sha256" not in _b)
    check("J03_bundle_binds_launcher_sha",
          _binds.get("v1_18_launcher", {}).get("sha256") == _sha(LAUNCHER))
    check("J04_bundle_binds_manifest_sha",
          _binds.get("v1_18_runtime_manifest", {}).get("sha256") == _sha(MANIFEST))
    check("J05_bundle_binds_exec_sha",
          _binds.get("v1_18_execution_source", {}).get("sha256") == FROZEN_V1_18_EXEC_SHA)
else:
    for k in ("J02_bundle_excludes_supervisor_sha", "J03_bundle_binds_launcher_sha",
              "J04_bundle_binds_manifest_sha", "J05_bundle_binds_exec_sha"):
        check(k, False)
check("J06_launch_authority_file_exists", LAUNCH_AUTHORITY.exists())
if LAUNCH_AUTHORITY.exists():
    _la = json.loads(LAUNCH_AUTHORITY.read_text(encoding="utf-8"))
    check("J07_launch_authority_binds_launcher_sha",
          _la.get("launcher_sha256") == _sha(LAUNCHER))
    check("J08_launch_authority_binds_bundle_sha",
          _la.get("prelaunch_authority_bundle_sha256") == _sha(BUNDLE))
else:
    check("J07_launch_authority_binds_launcher_sha", False)
    check("J08_launch_authority_binds_bundle_sha", False)
check("J09_supervisor_pins_launch_authority_file_sha",
      "FROZEN_V1_18_LAUNCH_AUTHORITY_FILE_SHA" in SSRC)
check("J10_supervisor_literal_launcher_sha", "FROZEN_V1_18_LAUNCHER_SHA =" in SSRC)
check("J11_supervisor_literal_bundle_sha", "FROZEN_V1_18_AUTHORITY_BUNDLE_SHA =" in SSRC)

# ---------------------------------------------------------------- #
# K. D85/D86/D88 supervisor-level repairs
# ---------------------------------------------------------------- #
check("K01_supervisor_no_launcher_sha_env_override",
      "PHASE36_V1_18_LAUNCHER_SHA" not in SSRC)
check("K02_supervisor_exclusive_stdout_stderr",
      "_write_text_exclusive" in SSRC)
_we = _func_in(SSRC, "_write_text_exclusive")
check("K03_exclusive_writer_no_o_trunc_flag", _we != "" and "os.O_TRUNC" not in _we)
check("K04_supervisor_predispatch_absence_check", "_predispatch_absence_check" in SSRC)
check("K05_exec_figure_writer_def", "def _savefig_once(" in SRC)
check("K06_exec_plain_savefig_absent", "fig.savefig(p, dpi=160)" not in SRC)
check("K07_exec_absence_gate_def", "def verify_v1_18_output_absence(" in SRC)

# ---------------------------------------------------------------- #
# L. D88 reachable-write inventory
# ---------------------------------------------------------------- #
check("L01_reachable_inventory_exists", RW_INVENTORY.exists())
if RW_INVENTORY.exists():
    _rw = json.loads(RW_INVENTORY.read_text(encoding="utf-8"))
    check("L02_inventory_total_23", _rw.get("total_reachable_write_target_count") == 23,
          {"value": _rw.get("total_reachable_write_target_count")})
    check("L03_inventory_table_figure_16",
          _rw.get("table_figure_target_count") == 16,
          {"value": _rw.get("table_figure_target_count")})
    check("L04_inventory_unclassified_0",
          _rw.get("unclassified_write_target_count") == 0)
    check("L05_inventory_namespace_overlap_0",
          _rw.get("namespace_overlap_count") == 0)
else:
    for k in ("L02_inventory_total_23", "L03_inventory_table_figure_16",
              "L04_inventory_unclassified_0", "L05_inventory_namespace_overlap_0"):
        check(k, False)

# ---------------------------------------------------------------- #
# M. v1.18 attempt markers ABSENT (+ v1.17/v1.16/v1.15 preserved absent)
# ---------------------------------------------------------------- #
v18_attempts = [
    "reports/audits/phase36_robustness_science_start_v1_18.json",
    "reports/audits/phase36_robustness_scientific_result_v1_18.json",
    "reports/audits/phase36_robustness_science_failure_v1_18.json",
    "reports/audits/phase36_robustness_science_process_exit_v1_18.json",
    "reports/audits/phase36_robustness_science_stdout_v1_18.txt",
    "reports/audits/phase36_robustness_science_stderr_v1_18.txt",
]
check("M01_v1_18_markers_absent", not any((ROOT / p).exists() for p in v18_attempts))
_jdir = ROOT / "reports/audits/phase36_robustness_science_v1_18_journal"
check("M02_v1_18_journal_empty",
      (not _jdir.exists()) or (len([f for f in _jdir.iterdir() if f.is_file()]) == 0))

v17_attempts = [
    "reports/audits/phase36_robustness_science_start_v1_17.json",
    "reports/audits/phase36_robustness_scientific_result_v1_17.json",
    "reports/audits/phase36_robustness_science_failure_v1_17.json",
    "reports/audits/phase36_robustness_science_process_exit_v1_17.json",
]
check("M03_v1_17_markers_still_absent", not any((ROOT / p).exists() for p in v17_attempts))

v16_attempts = [
    "reports/audits/phase36_robustness_science_start_v1_16.json",
    "reports/audits/phase36_robustness_scientific_result_v1_16.json",
    "reports/audits/phase36_robustness_science_failure_v1_16.json",
    "reports/audits/phase36_robustness_science_process_exit_v1_16.json",
]
check("M04_v1_16_markers_still_absent", not any((ROOT / p).exists() for p in v16_attempts))

# v1.18 science output namespaces must not exist (or be empty)
for _root, _tag in (("tables", "M05_v1_18_tables_namespace_absent"),
                    ("figures", "M06_v1_18_figures_namespace_absent"),
                    ("arrays", "M07_v1_18_arrays_namespace_absent")):
    _d = ROOT / "reports" / _root / "phase36_robustness_v1_18"
    check(_tag, (not _d.exists()) or (len([f for f in _d.rglob("*") if f.is_file()]) == 0))

check("M08_test_router_holdout_prohibitions_declared",
      ("ROUTER_HOLDOUT_RUNTIME_READS_ALLOWED = False" in SRC)
      and ('PROTECTED_COUNTERS = ("router_holdout_reads", "test_reads")' in SRC)
      and ("TEST_GT_READ" not in SRC))

# ---------------------------------------------------------------- #
# N. Adjudication + v1.14 evidence preserved (consumed/failed) — do not touch
# ---------------------------------------------------------------- #
check("N01_d85_d88_adjudication_exists", ADJUDICATION.exists())
check("N02_v1_14_failure_provenance_present",
      (ROOT / "reports/audits/phase36_robustness_science_failure_v1_14.json").exists())
check("N03_historical_v1_14_smoke_present",
      (ROOT / "reports/audits/phase36_robustness_smoke_v1_14.json").exists())

# ---------------------------------------------------------------- #
n_pass = sum(1 for c in checks if c["passed"])
n_total = len(checks)
report = {
    "artifact": "phase36_robustness_preflight_v1_18",
    "phase": 36,
    "method": "RA-MedFiLM-BARR",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_18",
    "type": "STATIC_PREFLIGHT_REPORT",
    "defects_repaired": ["D85", "D86", "D87", "D88"],
    "model_free": True,
    "torch_imported": False,
    "cuda_initialized": False,
    "protected_population_read": False,
    "subject_execution_sha256": _sha(EXEC),
    "subject_launcher_sha256": _sha(LAUNCHER),
    "subject_supervisor_sha256": _sha(SUPERVISOR) if SUPERVISOR.exists() else None,
    "subject_manifest_sha256": _sha(MANIFEST),
    "new_scientific_choice": False,
    "checks_total": n_total,
    "checks_passed": n_pass,
    "checks_failed": n_total - n_pass,
    "all_pass": n_pass == n_total,
    "failed_checks": [c["check"] for c in checks if not c["passed"]],
    "checks": checks,
}
out_path = ROOT / "reports/audits/phase36_robustness_preflight_v1_18.json"
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(report, indent=1), encoding="utf-8")
for c in checks:
    if not c["passed"]:
        print(f"FAIL {c['check']} :: {c.get('detail')}")
print(f"PREFLIGHT v1.18: {n_pass}/{n_total} pass")
print(f"terminal: {'PHASE36_V1_18_PREFLIGHT_PASS' if n_pass == n_total else 'PHASE36_V1_18_PREFLIGHT_FAIL'}")
raise SystemExit(0 if n_pass == n_total else 1)
