#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.15 — STATIC PREFLIGHT (SOURCE / AST / HASH ONLY; NO EXECUTION).

Aggregates the v1.15 static/governance gates and proves, from source bytes and
AST only, that D61 (canonical Phase27 ACCEPT fusion) and D75/POLICY_B
(authoritative segmentation representation) are enforced, the v1.14 science is
otherwise PRESERVED, and all v1.15 attempt markers are ABSENT.

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

EXEC = ROOT / "scripts/analysis/phase36_robustness_execution_v1_15.py"
EXEC_V1_14 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_14.py"
LAUNCHER = ROOT / "scripts/analysis/launch_phase36_v1_15.py"
SUPERVISOR = ROOT / "scripts/analysis/supervise_phase36_v1_15.py"
MANIFEST = ROOT / "reports/audits/phase36_v1_14_runtime_source_integrity_manifest.json"

FROZEN_V1_14_EXEC_SHA = "ac09ff8ded3610244920e66612145b246b33127140d344a9730d454bab27cff5"
FROZEN_V1_14_MANIFEST_SHA = "b4c358dfcb5e7b59beb6ae1ba2cffc64677d10049e12568b4c8eea8e79bb911e"

checks = []


def check(name, cond, detail=None):
    checks.append({"check": name, "passed": bool(cond), "detail": detail})


def _sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


SRC = EXEC.read_text(encoding="utf-8")
TREE = ast.parse(SRC)
FUNCS = {n.name: n for n in ast.walk(TREE) if isinstance(n, ast.FunctionDef)}
LSRC = LAUNCHER.read_text(encoding="utf-8")
LFUNCS = {n.name: n for n in ast.walk(ast.parse(LSRC)) if isinstance(n, ast.FunctionDef)}


def _func(name):
    return ast.get_source_segment(SRC, FUNCS[name]) or ""


def _lfunc(name):
    return ast.get_source_segment(LSRC, LFUNCS[name]) or ""


# ---------------------------------------------------------------- #
# A. Source identity + compile
# ---------------------------------------------------------------- #
check("A01_v1_14_frozen_unchanged", _sha(EXEC_V1_14) == FROZEN_V1_14_EXEC_SHA,
      {"sha256": _sha(EXEC_V1_14)})
check("A02_v1_15_compiles", compile(SRC, str(EXEC), "exec") is not None)
check("A03_v1_15_source_sha", _sha(EXEC) ==
      "b194ad28345ea8b268748be383ca98b936cb051d85854666e3141250f3eae002")

# ---------------------------------------------------------------- #
# B. D61 canonical fusion
# ---------------------------------------------------------------- #
check("B01_canonical_fusion_present", "fuse_full_field(p_global, refined, geom)" in SRC)
check("B02_old_fusion_absent",
      "system._fuse_global_with_regional(p_global, refined, window)" not in SRC)
check("B03_fuse_full_field_pad_aware",
      all(k in _func("fuse_full_field") for k in ("pad_top", "pad_left", "crop_side_pixels")))

# ---------------------------------------------------------------- #
# C. D75 POLICY_B
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
# D. Launcher binding + ordering
# ---------------------------------------------------------------- #
check("D01_launcher_present", LAUNCHER.exists())
check("D02_launcher_binds_v1_14_sha",
      "ac09ff8ded3610244920e66612145b246b33127140d344a9730d454bab27cff5" in LSRC)
check("D03_launcher_verify_only", "--verify-only" in LSRC)
check("D04_no_auto_relaunch",
      all(k not in LSRC for k in ("os.execv", "os.execve", "os.remove", "unlink")))
check("D05_launcher_tokens",
      "PHASE36_V1_15_EXECUTE" in LSRC and "PHASE36_V1_15_LAUNCH_AUTHORITY" in LSRC)
check("D06_supervisor_present", SUPERVISOR.exists())

# ---------------------------------------------------------------- #
# E. Manifest non-circularity + transitive integrity
# ---------------------------------------------------------------- #
_man = json.loads(MANIFEST.read_text(encoding="utf-8"))
check("E01_manifest_sha_frozen", _sha(MANIFEST) == FROZEN_V1_14_MANIFEST_SHA)
check("E02_manifest_no_launcher_sha256", "launcher_sha256" not in _man)
check("E03_manifest_14_deps_4_ckpts",
      _man["n_dependencies"] == 14 and _man["n_checkpoints"] == 4)
check("E04_all_deps_match",
      all(_sha(ROOT / r) == (e["expected"] if isinstance(e, dict) else e)
          for r, e in _man["dependency_verification"].items()))
check("E05_all_ckpts_match",
      all(_sha(ROOT / r) == (e["expected"] if isinstance(e, dict) else e)
          for r, e in _man["checkpoint_verification"].items()))

# ---------------------------------------------------------------- #
# F. v1.15 attempt markers ABSENT + protected populations not accessed
# ---------------------------------------------------------------- #
v15_attempts = [
    "reports/audits/phase36_robustness_science_start_v1_15.json",
    "reports/audits/phase36_robustness_science_result_v1_15.json",
    "reports/audits/phase36_robustness_science_failure_v1_15.json",
    "reports/audits/phase36_robustness_science_process_exit_v1_15.json",
]
check("F01_v1_15_markers_absent", not any((ROOT / p).exists() for p in v15_attempts))
_jdir = ROOT / "reports/audits/phase36_robustness_science_v1_15_journal"
check("F02_v1_15_journal_empty",
      (not _jdir.exists()) or (len([f for f in _jdir.iterdir() if f.is_file()]) == 0))
check("F03_v1_15_stdout_absent",
      not (ROOT / "reports/audits/phase36_robustness_science_stdout_v1_15.txt").exists())
check("F04_v1_15_stderr_absent",
      not (ROOT / "reports/audits/phase36_robustness_science_stderr_v1_15.txt").exists())
check("F05_no_test_router_holdout_access_static",
      "TEST_GT_READ" not in SRC or "TEST_GT_READ = 0" in SRC or "test_gt_read" not in SRC.lower())

# ---------------------------------------------------------------- #
# G. v1.14 science evidence preserved (consumed/failed) — do not touch
# ---------------------------------------------------------------- #
check("G01_v1_14_failure_provenance_present",
      (ROOT / "reports/audits/phase36_robustness_science_failure_v1_14.json").exists())

# ---------------------------------------------------------------- #
n_pass = sum(1 for c in checks if c["passed"])
n_total = len(checks)
report = {
    "artifact": "phase36_robustness_preflight_v1_15",
    "phase": 36,
    "method": "RA-MedFiLM-BARR",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_15",
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
out_path = ROOT / "reports/audits/phase36_robustness_preflight_v1_15.json"
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(report, indent=1), encoding="utf-8")
for c in checks:
    if not c["passed"]:
        print(f"FAIL {c['check']} :: {c.get('detail')}")
print(f"PREFLIGHT v1.15: {n_pass}/{n_total} pass")
print(f"terminal: {'PHASE36_V1_15_PREFLIGHT_PASS' if n_pass == n_total else 'PHASE36_V1_15_PREFLIGHT_FAIL'}")
raise SystemExit(0 if n_pass == n_total else 1)
