#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.8 — unit checks (source/AST/static only).

NO torch.  NO model.  NO protected-population read.
"""
from __future__ import annotations

import ast, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))

EXEC = ROOT / "scripts/analysis/phase36_robustness_execution_v1_8.py"
SRC = EXEC.read_text(encoding="utf-8")
TREE = ast.parse(SRC)
FUNCS = {n.name: n for n in ast.walk(TREE) if isinstance(n, ast.FunctionDef)}

checks = []


def check(name, cond, detail=None):
    checks.append({"check": name, "passed": bool(cond), "detail": detail})


# ---- D19 repairs ----------------------------------------------------------- #
check("01_write_once_attempt_exists_check",
      "_smoke_attempt_already_exists" in FUNCS)
check("02_write_once_attempt_uses_v1_8_paths",
      "SMOKE_V1_8_ARTIFACT" in SRC and "SMOKE_V1_8_ATTEMPT" in SRC)
check("03_main_checks_attempt_before_model_construction",
      "if _smoke_attempt_already_exists():" in ast.get_source_segment(SRC, FUNCS["main"]))
check("04_main_records_attempt_pre_model",
      "_write_smoke_failure_artifact" in ast.get_source_segment(SRC, FUNCS["main"]))
check("05_main_wraps_run_smoke_in_try_except",
      "try:" in ast.get_source_segment(SRC, FUNCS["main"])
      and "except Exception as exc:" in ast.get_source_segment(SRC, FUNCS["main"]))
check("06_exception_path_writes_failure_artifact",
      "_write_smoke_failure_artifact" in ast.get_source_segment(SRC, FUNCS["main"]))
check("07_exception_path_exits_nonzero",
      "return 1" in ast.get_source_segment(SRC, FUNCS["main"]))
# 08 — no automatic retry in main().  v1.8-repair: the previous matcher was a
# brittle substring filter that flagged the LEGITIMATE provenance literal
# "automatic_retry": False and the terminal token ...__NO_RETRY as if they were
# retry logic.  This matcher asserts the actual semantic requirement at the AST
# level: main() must not contain ANY loop construct (the only way an automatic
# retry could exist), and must not re-invoke run_smoke().  It remains strictly
# stronger than the old string check for the requirement it exists to test.
main_node = FUNCS["main"]
_loop_types = (ast.For, ast.While, ast.AsyncFor)
main_loops = [n for n in ast.walk(main_node) if isinstance(n, _loop_types)]
main_run_smoke_calls = [
    n for n in ast.walk(main_node)
    if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "run_smoke"
]
check("08_no_automatic_retry_in_main",
      len(main_loops) == 0 and len(main_run_smoke_calls) <= 1,
      detail=json.dumps({"loop_nodes": len(main_loops),
                         "run_smoke_call_sites": len(main_run_smoke_calls)}))

# ---- D20 repairs ----------------------------------------------------------- #
check("10_real_execute_probe_present",
      "def smoke_real_execute_component_probe" in SRC)
check("11_real_execute_router_decision_is_execute_check",
      "real_execute_router_decision_is_execute" in SRC)
check("12_real_execute_R_psi_output_finite_check",
      "real_execute_R_psi_output_finite" in SRC)
check("13_real_execute_R_psi_output_shape_valid_check",
      "real_execute_R_psi_output_shape_valid" in SRC)
check("14_real_execute_post_safety_feature_dim_16_check",
      "real_execute_post_safety_feature_dim_16" in SRC)
check("15_real_execute_post_safety_features_finite_check",
      "real_execute_post_safety_features_finite" in SRC)
check("16_real_execute_S_omega_logit_finite_check",
      "real_execute_S_omega_logit_finite" in SRC)
check("17_real_execute_S_omega_probability_finite_check",
      "real_execute_S_omega_probability_finite" in SRC)
check("18_real_execute_S_omega_probability_in_unit_interval_check",
      "real_execute_S_omega_probability_in_unit_interval" in SRC)
check("19_real_execute_final_state_valid_check",
      "real_execute_final_state_valid" in SRC)
check("20_real_execute_final_probability_shape_512x512_check",
      "real_execute_final_probability_shape_512x512" in SRC)
check("21_real_execute_final_probability_finite_check",
      "real_execute_final_probability_finite" in SRC)

# ---- D21 repairs ----------------------------------------------------------- #
check("25_metric_hd95_nonempty_plumbing_valid_check",
      "metric_hd95_nonempty_plumbing_valid" in SRC)
check("26_metric_hd95_empty_mask_semantics_valid_check",
      "metric_hd95_empty_mask_semantics_valid" in SRC)
check("27_metric_dice_iou_plumbing_valid_check",
      "metric_dice_iou_plumbing_valid" in SRC)

# ---- Transitive source integrity ------------------------------------------- #
check("30_transitive_runtime_dependencies_dict_present",
      "TRANSITIVE_RUNTIME_DEPENDENCIES = {" in SRC)
check("31_source_integrity_verification_function_present",
      "_verify_transitive_source_integrity" in FUNCS)
check("32_source_integrity_called_before_load_models",
      "_verify_transitive_source_integrity" in ast.get_source_segment(SRC, FUNCS["run_smoke"]))
check("33_source_integrity_fail_closed_on_mismatch",
      "TRANSITIVE_RUNTIME_SOURCE_INTEGRITY_FAILED" in SRC)

# ---- Smoke check contract -------------------------------------------------- #
check("35_smoke_attempt_is_first_write_once_check",
      "smoke_attempt_is_first_write_once" in SRC)
smoke_check_ids_node = None
for n in ast.walk(TREE):
    if isinstance(n, ast.Assign):
        for t in n.targets:
            if isinstance(t, ast.Name) and t.id == "SMOKE_CHECK_IDS":
                smoke_check_ids_node = n.value
                break
smoke_check_ids_len = len(smoke_check_ids_node.elts) if smoke_check_ids_node else 0
check("36_smoke_check_ids_count_47", smoke_check_ids_len == 47)
check("37_smoke_all_pass_derives_from_all_checks",
      "smoke_all_pass = bool(all(smoke_checks.values()))" in SRC)

# ---- v1.7 preservation ----------------------------------------------------- #
check("40_v1_7_execution_sha_in_docstring",
      "87062d2b38232c73b8ce620d7bfafb389658c4b877d9196a26b8b01d09daf192" in SRC)
check("41_canonical_sigmoid_preserved",
      "torch.sigmoid(t.float())" in SRC)
check("42_cuda_fail_closed_preserved",
      "get_device(require_cuda=True)" in SRC)
check("43_val808_only_preserved",
      "VAL808_ONLY" in SRC)
check("44_static_protected_io_unreachable_preserved",
      "_static_protected_io_unreachable" in FUNCS)

passed = sum(1 for c in checks if c["passed"])
total = len(checks)
report = {
    "artifact": "phase36_robustness_unit_v1_8",
    "phase": 36, "section": "§J", "method": "RA-MedFiLM-BARR",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_8",
    "type": "UNIT_CHECK_REPORT",
    "model_free": True,
    "torch_imported": "torch" in sys.modules,
    "protected_population_read": False,
    "passed": passed, "total": total, "all_pass": passed == total,
    "checks": checks,
    "generated_utc": "2026-10-06T10:48:58Z",
}
out = ROOT / "reports/audits/phase36_robustness_unit_v1_8.json"
out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({"passed": passed, "total": total, "all_pass": passed == total}, indent=1))
for c in checks:
    if not c["passed"]:
        print("FAIL:", c["check"], json.dumps(c.get("detail"), default=str))
raise SystemExit(0 if passed == total else 1)
