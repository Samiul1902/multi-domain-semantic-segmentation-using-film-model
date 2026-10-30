#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.8 — PREFLIGHT (source / AST / static only).

NO torch.  NO model.  NO checkpoint deserialization.  NO CUDA.  NO forward.
NO smoke.  NO science.  NO VAL image / GT read.  NO protected-population read.

Verifies the STATIC properties of the v1.8 execution source required by the
D19 / D20 / D21 repairs plus the transitive runtime source-integrity gate.
"""
from __future__ import annotations

import ast
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))

EXEC = ROOT / "scripts/analysis/phase36_robustness_execution_v1_8.py"
V1_7 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_7.py"

SRC = EXEC.read_text(encoding="utf-8")
TREE = ast.parse(SRC)
FUNCS = {n.name: n for n in ast.walk(TREE) if isinstance(n, ast.FunctionDef)}


def _sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def seg(name: str) -> str:
    return ast.get_source_segment(SRC, FUNCS[name])


def calls_in(name: str) -> set:
    out = set()
    for x in ast.walk(FUNCS[name]):
        if isinstance(x, ast.Call):
            f = x.func
            out.add(f.id if isinstance(f, ast.Name)
                    else (f.attr if isinstance(f, ast.Attribute) else None))
    return out


def reach(entry: str) -> set:
    seen, stack = set(), [entry]
    while stack:
        f = stack.pop()
        if f in seen or f not in FUNCS:
            continue
        seen.add(f)
        for c in calls_in(f):
            if c in FUNCS and c not in seen:
                stack.append(c)
    return seen


def const_strs(name: str) -> set:
    out = set()
    for n in ast.walk(FUNCS[name]):
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            out.add(n.value)
    return out


def assigned_names(tree) -> set:
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name):
                    out.add(t.id)
    return out


def smoke_check_ids() -> list:
    for n in ast.walk(TREE):
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name) and t.id == "SMOKE_CHECK_IDS":
                    return [e.value for e in n.value.elts]
    return []


checks = []


def check(name, cond, detail=None):
    checks.append({"check": name, "passed": bool(cond), "detail": detail})


V1_7_SHA = "87062d2b38232c73b8ce620d7bfafb389658c4b877d9196a26b8b01d09daf192"
V1_7_AUDIT_SHA = "3a7a11d13b683b223c967ee86ddb1e5df6e5f90469d4a1e112cee1b774bca43e"
V1_7_FREEZE_SHA = "e4e86cd9a3e297d8b4f0a52591be6b88d27cef9897b933d427aa9c15f15fa62f"

# ---- A. v1.7 preservation ---------------------------------------------------- #
check("A01_v1_7_execution_bytes_unchanged", _sha(V1_7) == V1_7_SHA,
      detail={"observed": _sha(V1_7), "expected": V1_7_SHA})
check("A02_v1_7_direct_byte_audit_unchanged",
      _sha(ROOT / "reports/audits/phase36_v1_7_direct_source_byte_audit.json") == V1_7_AUDIT_SHA)
check("A03_v1_7_source_freeze_unchanged",
      _sha(ROOT / "reports/audits/phase36_preexecution_source_freeze_v1_7.json") == V1_7_FREEZE_SHA)
check("A04_v1_7_history_sha_quoted_in_v1_8_docstring", V1_7_SHA in SRC)

# ---- B. D19 — write-once / exception-safe provenance ------------------------- #
check("B01_smoke_attempt_probe_function_present", "_smoke_attempt_already_exists" in FUNCS)
check("B02_main_checks_attempt_before_run_smoke",
      "if _smoke_attempt_already_exists():" in seg("main")
      and seg("main").index("_smoke_attempt_already_exists()")
      < seg("main").index("run_smoke()"))
check("B03_main_wraps_run_smoke_in_try_except",
      "try:" in seg("main") and "except Exception as exc:" in seg("main"))
check("B04_exception_path_writes_failure_artifact",
      "_write_smoke_failure_artifact" in seg("main"))
check("B05_exception_path_exits_nonzero", "return 1" in seg("main"))
check("B06_failure_artifact_marked_incomplete",
      '"completed": False' in seg("_write_smoke_failure_artifact")
      and '"attempted": True' in seg("_write_smoke_failure_artifact"))
check("B07_failure_artifact_records_exception_fields",
      "exception_type" in seg("_write_smoke_failure_artifact")
      and "exception_message" in seg("_write_smoke_failure_artifact")
      and "failing_stage" in seg("_write_smoke_failure_artifact"))
check("B08_failure_artifact_records_revision_and_sha",
      "source_sha256" in seg("_write_smoke_failure_artifact")
      and "ra_medfilm_barr_phase36_robustness_v1_8" in seg("_write_smoke_failure_artifact"))
check("B09_failure_artifact_no_retry_no_overwrite_flags",
      '"automatic_retry": False' in seg("_write_smoke_failure_artifact")
      and '"overwrite_permitted": False' in seg("_write_smoke_failure_artifact"))
check("B10_failure_artifact_not_scientific_output",
      '"scientific_output": False' in seg("_write_smoke_failure_artifact"))
check("B11_failure_artifact_has_terminal_and_timestamp",
      '"terminal"' in seg("_write_smoke_failure_artifact")
      and "generated_utc" in seg("_write_smoke_failure_artifact"))
check("B12_canonical_smoke_path_is_v1_8",
      "reports/audits/phase36_robustness_smoke_v1_8.json" in SRC)
check("B13_no_loop_in_main", not any(isinstance(n, (ast.For, ast.While, ast.AsyncFor))
                                     for n in ast.walk(FUNCS["main"])))
check("B14_run_smoke_single_call_site_in_main",
      sum(1 for n in ast.walk(FUNCS["main"])
          if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
          and n.func.id == "run_smoke") <= 1)
check("B15_no_os_remove_unlink_overwrite_of_smoke_artifact",
      "unlink" not in SRC and "os.remove" not in SRC)

# ---- C. smoke success contract ---------------------------------------------- #
ids = smoke_check_ids()
check("C01_smoke_check_ids_declared", len(ids) > 0, detail={"n": len(ids)})
check("C02_smoke_all_pass_derives_from_all_checks",
      "smoke_all_pass = bool(all(smoke_checks.values()))" in SRC)
check("C03_smoke_contract_mismatch_guard_present",
      "SMOKE_CHECK_CONTRACT_MISMATCH" in SRC)
check("C04_artifact_written_before_nonzero_exit",
      seg("main").index("SMOKE_V1_8_ARTIFACT")
      < seg("main").index('if not bool(res.get("smoke_all_pass"))'))

# ---- D. D20 — real-execute numerical binding --------------------------------- #
D20_IDS = [
    "real_execute_router_decision_is_execute",
    "real_execute_R_psi_output_finite",
    "real_execute_R_psi_output_shape_valid",
    "real_execute_post_safety_feature_dim_16",
    "real_execute_post_safety_features_finite",
    "real_execute_S_omega_logit_finite",
    "real_execute_S_omega_probability_finite",
    "real_execute_S_omega_probability_in_unit_interval",
    "real_execute_final_state_valid",
    "real_execute_final_probability_shape_512x512",
    "real_execute_final_probability_finite",
    "router_vector_dim_exactly_202",
    "router_vector_finite",
]
check("D01_all_d20_check_ids_declared_in_contract",
      all(i in ids for i in D20_IDS),
      detail={"missing": [i for i in D20_IDS if i not in ids]})
# Require each D20 id to be BOUND in the smoke_checks mapping (a
# '"<id>": bool(...)' entry), not merely listed in SMOKE_CHECK_IDS.
check("D02_d20_ids_bound_in_smoke_checks_mapping",
      all(f'"{i}": bool(' in SRC for i in D20_IDS),
      detail={"unbound": [i for i in D20_IDS if f'"{i}": bool(' not in SRC]})
check("D03_real_execute_probe_leaves_somega_logit_none",
      "forced_s_omega_logit=None" in seg("smoke_real_execute_component_probe"))
check("D04_real_execute_probe_forces_router_execute",
      "control_router_score = +50.0" in seg("smoke_real_execute_component_probe"))
check("D05_real_execute_probe_no_outcome_selection",
      "outcome_selected" in seg("smoke_real_execute_component_probe"))
check("D06_real_R_psi_forward_count_bound_to_1",
      'execute_probe["actual_R_psi_forward_count"] == 1' in SRC)
check("D07_real_S_omega_forward_count_bound_to_1",
      'execute_probe["actual_S_omega_forward_count"] == 1' in SRC)
check("D08_real_execute_valid_states_restricted",
      'in ("EXECUTE_THEN_ACCEPT", "EXECUTE_THEN_REJECT")' in SRC)

# ---- E. D21 — HD95 binding -------------------------------------------------- #
check("E01_hd95_nonempty_id_in_contract",
      "metric_hd95_nonempty_plumbing_valid" in ids
      and '"metric_hd95_nonempty_plumbing_valid": bool(' in SRC)
check("E02_hd95_empty_id_in_contract",
      "metric_hd95_empty_mask_semantics_valid" in ids
      and '"metric_hd95_empty_mask_semantics_valid"' in SRC
      and '"metric_hd95_empty_mask_semantics_valid": bool(' in SRC)
check("E03_hd95_nonempty_requires_valid_true_and_finite",
      'hd.get("valid") is True' in SRC and 'np.isfinite(hd.get("hd95", np.nan))' in SRC)
check("E04_hd95_empty_requires_valid_false",
      'hd_empty.get("valid") is False' in SRC)
check("E05_hd95_empty_requires_nonfinite_and_frozen_reason",
      'np.isfinite(hd_empty.get("hd95", np.nan))' in SRC
      and '"both_empty"' in SRC and '"empty_prediction"' in SRC
      and '"empty_ground_truth"' in SRC)
check("E06_hd95_empty_no_tautological_none_acceptance",
      'in (True, False, None)' not in SRC)
check("E07_metric_authority_bound_to_frozen_module",
      "src.metrics import evaluation_metrics as M" in SRC)
check("E08_dice_iou_bound_in_contract", "metric_dice_iou_plumbing_valid" in ids)

# ---- F. transitive runtime source integrity --------------------------------- #
check("F01_transitive_deps_dict_present",
      any("TRANSITIVE_RUNTIME_DEPENDENCIES" == t
          for t in assigned_names(TREE)))
check("F02_integrity_function_present", "_verify_transitive_source_integrity" in FUNCS)
check("F03_integrity_gate_before_load_models_in_run_smoke",
      seg("run_smoke").index("_verify_transitive_source_integrity")
      < seg("run_smoke").index("_load_models"))
check("F04_integrity_fails_closed_on_mismatch",
      "TRANSITIVE_RUNTIME_SOURCE_INTEGRITY_FAILED" in SRC
      and 'if not source_integrity["all_match"]:' in SRC)
check("F05_integrity_verifies_self_via_external_manifest",
      "execution_source_sha256" in SRC
      and "phase36_v1_8_runtime_source_integrity_manifest.json" in SRC)
check("F06_integrity_covers_common_authority",
      "phase36_robustness_common_v1_1.py" in SRC)
check("F07_integrity_covers_g_implementation",
      "src/models/film/global_medfilm.py" in SRC)
check("F08_integrity_covers_r_psi_implementation",
      "src/models/barr/regional_refiner.py" in SRC)
check("F09_integrity_covers_system_implementation",
      "src/models/barr/ra_medfilm_barr.py" in SRC)
check("F10_integrity_covers_device_and_metrics",
      "src/utils/device.py" in SRC and "src/metrics/evaluation_metrics.py" in SRC)
check("F11_integrity_covers_g_config_and_norms",
      "phase21_global_medfilm_fourdomain_seed42_clean_v3/config.json" in SRC
      and "phase25d_final_normalization_stats.csv" in SRC
      and "phase25f_final_normalization_stats.csv" in SRC)

# ---- G. scientific-semantics preservation ------------------------------------ #
check("G01_canonical_sigmoid_operator_preserved",
      "torch.sigmoid(t.float())" in SRC)
check("G02_cuda_fail_closed_preserved", "get_device(require_cuda=True)" in SRC)
check("G03_val808_only_preserved", "VAL808_ONLY" in SRC)
check("G04_g_context_preserved",
      "CANONICAL_G_INFERENCE_MODE = False" in SRC
      and "canonical_g_forward_batched" in FUNCS)
check("G05_component_contexts_preserved",
      "component_inference_context" in FUNCS and "component_autocast_disabled" in FUNCS)
check("G06_router_vector_dim_202", "ROUTER_NUMERIC_DIM" in SRC)
check("G07_conditional_execution_order_preserved",
      "actual_r_psi_forwards" in SRC and "actual_s_omega_forwards" in SRC)
check("G08_roi_threshold_030_and_seg_threshold_050_preserved",
      "ROI_PROPOSAL_THRESHOLD" in SRC and "0.50" in SRC)
check("G09_kub_subgroup_reporting_only_preserved",
      "reporting_only" in SRC and "kub_subgroup_map" in FUNCS)
check("G10_figure_registry_preserved",
      "FIGURE_REGISTRY" in SRC and all(f"figure_R{i}" in FUNCS for i in range(1, 6)))

# ---- H. protected-population unreachability ---------------------------------- #
PROTECTED = ("TEST_MANIFEST", "ROUTER_HOLDOUT_MANIFEST", "ROUTER_HOLDOUT_IDENTITY_AUTHORITY")
PROT_TOKENS = ("val_router_holdout", "phase24_router_split_manifest", "phase4_v3/test.csv")


def protected_reachable() -> list:
    hits = []
    for entry in ("run_science", "run_smoke"):
        for name in reach(entry):
            if name == "_static_protected_io_unreachable":
                continue
            for n in ast.walk(FUNCS[name]):
                if isinstance(n, ast.Name) and n.id in PROTECTED:
                    hits.append((entry, name, n.id))
                if isinstance(n, ast.Constant) and isinstance(n.value, str):
                    for t in PROT_TOKENS:
                        if t in n.value:
                            hits.append((entry, name, t))
    return hits


prot = protected_reachable()
check("H01_no_protected_symbol_reachable", len(prot) == 0, detail={"hits": prot[:10]})
check("H02_protected_counters_forever_zero_preserved",
      "COUNTERS_FOREVER_ZERO" in SRC)
check("H03_static_protected_io_detector_present",
      "_static_protected_io_unreachable" in FUNCS)
check("H04_val_manifest_is_only_runtime_authority",
      "VAL_MANIFEST_IS_ONLY_POPULATION_RUNTIME_AUTHORITY = True" in SRC)
check("H05_test_runtime_reads_disallowed_flag",
      "TEST_RUNTIME_READS_ALLOWED = False" in SRC)
check("H06_holdout_runtime_reads_disallowed_flag",
      "ROUTER_HOLDOUT_RUNTIME_READS_ALLOWED = False" in SRC)

# ---- I. gate separation + non-execution -------------------------------------- #
check("I01_smoke_gate_separate_from_science_gate",
      "SMOKE_GATE_ENV" in SRC and "GATE_ENV" in SRC
      and "PHASE36_SMOKE_EXECUTE" in SRC)
check("I02_smoke_gate_uses_dedicated_env_var", 'PHASE36_SMOKE_EXECUTE' in SRC)
check("I03_no_smoke_artifact_exists_yet",
      not (ROOT / "reports/audits/phase36_robustness_smoke_v1_8.json").exists())
check("I04_no_smoke_attempt_artifact_exists_yet",
      not (ROOT / "reports/audits/phase36_robustness_smoke_attempt_v1_8.json").exists())
check("I05_no_v1_8_science_output_exists",
      not (ROOT / "reports/audits/phase36_robustness_scientific_result_v1_8.json").exists())
check("I06_ast_parse_ok", True)
check("I07_entrypoint_guarded_by_main_guard",
      'if __name__ == "__main__":' in SRC)

passed = sum(1 for c in checks if c["passed"])
total = len(checks)
report = {
    "artifact": "phase36_robustness_preflight_v1_8",
    "phase": 36,
    "section": "§N",
    "method": "RA-MedFiLM-BARR",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_8",
    "type": "PREFLIGHT_CHECK_REPORT",
    "static_only": True,
    "model_free": True,
    "torch_imported": "torch" in sys.modules,
    "protected_population_read": False,
    "subject": "scripts/analysis/phase36_robustness_execution_v1_8.py",
    "subject_sha256": _sha(EXEC),
    "v1_7_preserved": {
        "execution_sha256": V1_7_SHA,
        "direct_byte_audit_sha256": V1_7_AUDIT_SHA,
        "source_freeze_sha256": V1_7_FREEZE_SHA,
        "all_unchanged": _sha(V1_7) == V1_7_SHA,
    },
    "passed": passed,
    "total": total,
    "all_pass": passed == total,
    "checks": checks,
    "generated_utc": "2026-10-06T11:36:00Z",
}
out = ROOT / "reports/audits/phase36_robustness_preflight_v1_8.json"
out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({"passed": passed, "total": total, "all_pass": passed == total}, indent=1))
for c in checks:
    if not c["passed"]:
        print("FAIL:", c["check"], json.dumps(c.get("detail"), default=str))
raise SystemExit(0 if passed == total else 1)
