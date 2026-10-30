#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.17 — STATIC PREFLIGHT (SOURCE / AST / HASH ONLY; NO EXECUTION).

REBASED FROM v1.16 (D81/D82/D83 FINAL OPERATIONAL REPAIR).

Aggregates the v1.17 static/governance gates and proves, from source bytes and
AST only, that D61 (canonical Phase27 ACCEPT fusion) and D75/POLICY_B
(authoritative segmentation representation) are PRESERVED, the v1.17 operational
layer repairs D81 (unique namespace + fail-closed CSV), D82 (release contract
binding the HISTORICAL v1.14 smoke), and D83 (pure runtime release-state), and
all v1.17 attempt markers are ABSENT.

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

EXEC = ROOT / "scripts/analysis/phase36_robustness_execution_v1_17.py"
EXEC_V1_16 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_16.py"
EXEC_V1_14 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_14.py"
LAUNCHER = ROOT / "scripts/analysis/launch_phase36_v1_17.py"
SUPERVISOR = ROOT / "scripts/analysis/supervise_phase36_v1_17.py"
MANIFEST = ROOT / "reports/audits/phase36_v1_17_runtime_source_integrity_manifest.json"
RELEASE_ATT = ROOT / "reports/audits/phase36_v1_17_science_release_attestation.json"

FROZEN_V1_14_EXEC_SHA = "ac09ff8ded3610244920e66612145b246b33127140d344a9730d454bab27cff5"
FROZEN_V1_16_EXEC_SHA = "a96b74caa4587aa9d2f83b79ed39c13075a88086109e31d991695a75ec4abab9"
FROZEN_V1_17_EXEC_SHA = "81d78460b2f20f176bc697cba662c43bc7c7443ea555ba95a30609faf0ccbe31"
FROZEN_V1_17_MANIFEST_SHA = "729f3676c86ba687bf808f9d79bac38916252563fc4b5814dd75d3d3f6b2bfc9"
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


# ---------------------------------------------------------------- #
# A. Source identity + compile
# ---------------------------------------------------------------- #
check("A01_v1_14_frozen_unchanged", _sha(EXEC_V1_14) == FROZEN_V1_14_EXEC_SHA,
      {"sha256": _sha(EXEC_V1_14)})
check("A02_v1_16_frozen_unchanged", _sha(EXEC_V1_16) == FROZEN_V1_16_EXEC_SHA)
check("A03_v1_17_compiles", compile(SRC, str(EXEC), "exec") is not None)
check("A04_v1_17_source_sha", _sha(EXEC) == FROZEN_V1_17_EXEC_SHA)

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
# D. Launcher binding + ordering (v1.17 rebased)
# ---------------------------------------------------------------- #
check("D01_launcher_present", LAUNCHER.exists())
check("D02_launcher_binds_literal_v1_17_sha", FROZEN_V1_17_EXEC_SHA in LSRC)
check("D03_launcher_verify_only", "--verify-only" in LSRC)
check("D04_no_auto_relaunch",
      all(k not in LSRC for k in ("os.execv", "os.execve", "os.remove", "unlink")))
check("D05_launcher_tokens_v1_17",
      "PHASE36_V1_17_EXECUTE" in LSRC and "PHASE36_V1_17_LAUNCH_AUTHORITY" in LSRC)
check("D06_supervisor_present", SUPERVISOR.exists())

# ---------------------------------------------------------------- #
# E. D80 operational/governance rebase (PRESERVED) + v1.17 namespace
# ---------------------------------------------------------------- #
check("E01_launcher_dispatch_mode_science", 'DISPATCH_MODE_ARGS = ["--mode", "science"]' in LSRC)
check("E02_launcher_dispatch_cmd_uses_mode_args", "list(DISPATCH_MODE_ARGS)" in LSRC)
check("E03_execution_v1_17_result_artifact",
      "phase36_robustness_scientific_result_v1_17.json" in SRC)
check("E04_no_v1_16_science_start_residue",
      "phase36_robustness_science_start_v1_16.json" not in SRC)
check("E05_execution_launch_authority_v1_17",
      'LAUNCH_AUTHORITY_TOKEN = "PHASE36_V1_17_LAUNCH_AUTHORITY"' in SRC)
check("E06_explicit_science_gate", "PHASE36_V1_17_EXECUTE" in SRC)
check("E07_explicit_smoke_gate", "PHASE36_V1_17_SMOKE_EXECUTE" in SRC)
check("E08_no_v1_16_gate_residue",
      "PHASE36_V1_16_EXECUTE" not in SRC and "PHASE36_V1_16_SMOKE_EXECUTE" not in SRC)
check("E09_runtime_manifest_v1_17_path",
      "phase36_v1_17_runtime_source_integrity_manifest.json" in SRC)
check("E10_no_v1_16_manifest_residue",
      "phase36_v1_16_runtime_source_integrity_manifest.json" not in SRC)
check("E11_release_revision_v1_17", "ra_medfilm_barr_phase36_robustness_v1_17" in SRC)
check("E12_no_v1_16_release_revision_residue",
      "ra_medfilm_barr_phase36_robustness_v1_16" not in SRC)
check("E13_stage_journal_module", "V1_17_JOURNAL_STAGES" in SRC and "_ScienceJournal" in SRC)
check("E14_stage_journal_wired",
      "journal=_ScienceJournal(" in SRC and "_run_science_with_durable_evidence(journal=" in SRC)
check("E15_stage_journal_dir_v1_17",
      "phase36_robustness_science_v1_17_journal" in SRC)
check("E16_launcher_pins_literal_sha_constant",
      'V1_17_SOURCE_SHA = "' + FROZEN_V1_17_EXEC_SHA + '"' in LSRC)
check("E17_supervisor_enforces_launcher_pin",
      "launcher_sha_pin_enforced" in SSRC and "FAIL_CLOSED__LAUNCHER_SHA_MISMATCH" in SSRC)
check("E18_supervisor_no_relaunch",
      "for " not in SSRC.split("def supervise_once")[1].split("def main")[0])
check("E19_supervisor_returns_child_exit_code", "returned_child_exit_code" in SSRC)

# ---------------------------------------------------------------- #
# F. D81 namespace rebase + fail-closed CSV (NEW)
# ---------------------------------------------------------------- #
check("F01_tab_root_v1_17", 'TAB = ROOT / "reports" / "tables" / "phase36_robustness_v1_17"' in SRC)
check("F02_fig_root_v1_17", 'FIG = ROOT / "reports" / "figures" / "phase36_robustness_v1_17"' in SRC)
check("F03_arr_root_v1_17", 'ARR = ROOT / "reports" / "arrays" / "phase36_robustness_v1_17"' in SRC)
check("F04_no_unversioned_tab_root", 'TAB = ROOT / "reports" / "tables"\n' not in SRC)
check("F05_csv_writer_exclusive_create", 'open(path, "x", encoding="utf-8", newline="")' in SRC)
check("F06_csv_writer_refuses_existing",
      "V1_17_CSV_FAIL_CLOSED__TARGET_EXISTS__REFUSE_OVERWRITE" in SRC)
check("F07_csv_writer_no_open_w", 'path.open("w"' not in _func("_write_csv"))
check("F08_csv_writer_fsync", "os.fsync(f.fileno())" in _func("_write_csv"))

# ---------------------------------------------------------------- #
# G. D82 release contract (NEW)
# ---------------------------------------------------------------- #
check("G01_historical_v1_14_smoke_bound",
      'HISTORICAL_V1_14_SMOKE = "reports/audits/phase36_robustness_smoke_v1_14.json"' in SRC)
check("G02_historical_smoke_sha_pinned", HISTORICAL_V1_14_SMOKE_SHA in SRC)
check("G03_gate_no_v1_17_smoke_requirement",
      "phase36_robustness_smoke_v1_17.json" not in SRC)
check("G04_release_attestation_present", RELEASE_ATT.exists())
if RELEASE_ATT.exists():
    _att = json.loads(RELEASE_ATT.read_text(encoding="utf-8"))
    check("G05_attestation_has_d40_schema_fields",
          all(f in _att for f in ("smoke_artifact_sha256", "smoke_all_pass",
                                  "scientific_output", "release_gate")))
    check("G06_attestation_binds_v1_17_exec_sha",
          _att.get("execution_source_sha256") == FROZEN_V1_17_EXEC_SHA)
    check("G07_attestation_binds_historical_smoke_sha",
          _att.get("smoke_artifact_sha256") == HISTORICAL_V1_14_SMOKE_SHA)
    check("G08_attestation_does_not_require_v1_17_smoke",
          _att.get("requires_v1_17_smoke") is False)
    check("G09_attestation_no_d61_d75_claim_from_v1_14_smoke",
          _att["historical_runtime_evidence"]["v1_14_smoke_tested_d61"] is False
          and _att["historical_runtime_evidence"]["v1_14_smoke_tested_d75"] is False)
else:
    check("G05_attestation_has_d40_schema_fields", False)
    check("G06_attestation_binds_v1_17_exec_sha", False)
    check("G07_attestation_binds_historical_smoke_sha", False)
    check("G08_attestation_does_not_require_v1_17_smoke", False)
    check("G09_attestation_no_d61_d75_claim_from_v1_14_smoke", False)

# ---------------------------------------------------------------- #
# H. D83 pure release-gate runtime state (NEW)
# ---------------------------------------------------------------- #
check("H01_release_gate_function_present", "def _gate_science_release_state()" in SRC)
check("H02_launcher_invokes_pure_release_state",
      "verify_pure_release_state" in LSRC and "pure_release_state_released" in LSRC)
check("H03_launcher_requires_released",
      "results[\"pure_release_state_released\"]" in LSRC
      or 'results["pure_release_state_released"]' in LSRC)

# ---------------------------------------------------------------- #
# I. Manifest non-circularity + transitive integrity
# ---------------------------------------------------------------- #
_man = json.loads(MANIFEST.read_text(encoding="utf-8"))
check("I01_manifest_sha_frozen", _sha(MANIFEST) == FROZEN_V1_17_MANIFEST_SHA)
check("I02_manifest_no_launcher_sha256", "launcher_sha256" not in _man)
check("I03_manifest_binds_v1_17_exec_source",
      _man.get("execution_source_sha256") == FROZEN_V1_17_EXEC_SHA)
check("I04_manifest_14_deps_4_ckpts",
      _man["n_dependencies"] == 14 and _man["n_checkpoints"] == 4)
check("I05_all_deps_match",
      all(_sha(ROOT / r) == (e["expected"] if isinstance(e, dict) else e)
          for r, e in _man["dependency_verification"].items()))
check("I06_all_ckpts_match",
      all(_sha(ROOT / r) == (e["expected"] if isinstance(e, dict) else e)
          for r, e in _man["checkpoint_verification"].items()))

# ---------------------------------------------------------------- #
# J. v1.17 attempt markers ABSENT + v1.16/v1.15 still absent
# ---------------------------------------------------------------- #
v17_attempts = [
    "reports/audits/phase36_robustness_science_start_v1_17.json",
    "reports/audits/phase36_robustness_scientific_result_v1_17.json",
    "reports/audits/phase36_robustness_science_failure_v1_17.json",
    "reports/audits/phase36_robustness_science_process_exit_v1_17.json",
]
check("J01_v1_17_markers_absent", not any((ROOT / p).exists() for p in v17_attempts))
_jdir = ROOT / "reports/audits/phase36_robustness_science_v1_17_journal"
check("J02_v1_17_journal_empty",
      (not _jdir.exists()) or (len([f for f in _jdir.iterdir() if f.is_file()]) == 0))
check("J03_v1_17_stdout_absent",
      not (ROOT / "reports/audits/phase36_robustness_science_stdout_v1_17.txt").exists())
check("J04_v1_17_stderr_absent",
      not (ROOT / "reports/audits/phase36_robustness_science_stderr_v1_17.txt").exists())

v16_attempts = [
    "reports/audits/phase36_robustness_science_start_v1_16.json",
    "reports/audits/phase36_robustness_scientific_result_v1_16.json",
    "reports/audits/phase36_robustness_science_failure_v1_16.json",
    "reports/audits/phase36_robustness_science_process_exit_v1_16.json",
]
check("J05_v1_16_markers_still_absent", not any((ROOT / p).exists() for p in v16_attempts))
_j16 = ROOT / "reports/audits/phase36_robustness_science_v1_16_journal"
check("J06_v1_16_journal_empty",
      (not _j16.exists()) or (len([f for f in _j16.iterdir() if f.is_file()]) == 0))

v15_attempts = [
    "reports/audits/phase36_robustness_science_start_v1_15.json",
    "reports/audits/phase36_robustness_science_result_v1_15.json",
    "reports/audits/phase36_robustness_science_failure_v1_15.json",
    "reports/audits/phase36_robustness_science_process_exit_v1_15.json",
]
check("J07_v1_15_markers_still_absent", not any((ROOT / p).exists() for p in v15_attempts))
_j15 = ROOT / "reports/audits/phase36_robustness_science_v1_15_journal"
check("J08_v1_15_journal_empty",
      (not _j15.exists()) or (len([f for f in _j15.iterdir() if f.is_file()]) == 0))

check("J09_no_test_router_holdout_access_static",
      "TEST_GT_READ" not in SRC or "TEST_GT_READ = 0" in SRC or "test_gt_read" not in SRC.lower())

# ---------------------------------------------------------------- #
# K. v1.14 science evidence preserved (consumed/failed) — do not touch
# ---------------------------------------------------------------- #
check("K01_v1_14_failure_provenance_present",
      (ROOT / "reports/audits/phase36_robustness_science_failure_v1_14.json").exists())
check("K02_historical_v1_14_smoke_present",
      (ROOT / "reports/audits/phase36_robustness_smoke_v1_14.json").exists())

# ---------------------------------------------------------------- #
n_pass = sum(1 for c in checks if c["passed"])
n_total = len(checks)
report = {
    "artifact": "phase36_robustness_preflight_v1_17",
    "phase": 36,
    "method": "RA-MedFiLM-BARR",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_17",
    "type": "STATIC_PREFLIGHT_REPORT",
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
out_path = ROOT / "reports/audits/phase36_robustness_preflight_v1_17.json"
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(report, indent=1), encoding="utf-8")
for c in checks:
    if not c["passed"]:
        print(f"FAIL {c['check']} :: {c.get('detail')}")
print(f"PREFLIGHT v1.17: {n_pass}/{n_total} pass")
print(f"terminal: {'PHASE36_V1_17_PREFLIGHT_PASS' if n_pass == n_total else 'PHASE36_V1_17_PREFLIGHT_FAIL'}")
raise SystemExit(0 if n_pass == n_total else 1)
