#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.9 — PREFLIGHT (source / AST / static only).

NO torch.  NO model.  NO checkpoint deserialization.  NO CUDA.  NO forward.
NO smoke.  NO science.  NO VAL image / GT read.  NO protected-population read.

Additive over v1.8: verifies the STATIC properties required by the
D22 / D23 / D24 / D25 repairs AND the v1.8 D19 / D20 / D21 repairs, plus the
check-matrix reconciliation.
"""
from __future__ import annotations

import ast
import hashlib
import io
import json
import sys
import tokenize
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))

EXEC = ROOT / "scripts/analysis/phase36_robustness_execution_v1_9.py"
V1_8 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_8.py"
V1_7 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_7.py"

SRC = EXEC.read_text(encoding="utf-8")
TREE = ast.parse(SRC)
FUNCS = {n.name: n for n in ast.walk(TREE) if isinstance(n, ast.FunctionDef)}


def _sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def seg(name: str) -> str:
    return ast.get_source_segment(SRC, FUNCS[name]) or ""


def code_only() -> str:
    """Strip docstrings AND comments so defect-documentation text is not
    mistaken for executable tokens."""
    out = SRC
    for n in ast.walk(TREE):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            b = getattr(n, "body", [])
            if b and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Constant) \
                    and isinstance(b[0].value.value, str):
                out = out.replace(b[0].value.value, "")
    kept = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(SRC).readline):
            if tok.type == tokenize.COMMENT:
                continue
            kept.append(tok)
        out = tokenize.untokenize(kept)
    except Exception:
        pass
    for n in ast.walk(TREE):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            b = getattr(n, "body", [])
            if b and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Constant) \
                    and isinstance(b[0].value.value, str):
                out = out.replace(b[0].value.value, "")
    return out


CODE_ONLY = code_only()


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


def smoke_checks_keys() -> list:
    for n in ast.walk(FUNCS["run_smoke"]):
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name) and t.id == "smoke_checks":
                    return [k.value for k in n.value.keys]
    return []


checks = []


def check(name, cond, detail=None):
    checks.append({"check": name, "passed": bool(cond), "detail": detail})


V1_8_SHA = "c95ff9884ec05a859b39ce7976376bf40e4543b1a8d8a19830e5893120039f4d"
V1_7_SHA = "87062d2b38232c73b8ce620d7bfafb389658c4b877d9196a26b8b01d09daf192"
V1_7_AUDIT_SHA = "3a7a11d13b683b223c967ee86ddb1e5df6e5f90469d4a1e112cee1b774bca43e"
V1_7_FREEZE_SHA = "e4e86cd9a3e297d8b4f0a52591be6b88d27cef9897b933d427aa9c15f15fa62f"

# ---- A. v1.8 / v1.7 preservation -------------------------------------------- #
check("A01_v1_8_execution_bytes_unchanged", _sha(V1_8) == V1_8_SHA,
      detail={"observed": _sha(V1_8), "expected": V1_8_SHA})
check("A02_v1_7_execution_bytes_unchanged", _sha(V1_7) == V1_7_SHA)
check("A03_v1_7_direct_byte_audit_unchanged",
      _sha(ROOT / "reports/audits/phase36_v1_7_direct_source_byte_audit.json") == V1_7_AUDIT_SHA)
check("A04_v1_7_source_freeze_unchanged",
      _sha(ROOT / "reports/audits/phase36_preexecution_source_freeze_v1_7.json") == V1_7_FREEZE_SHA)
check("A05_v1_8_history_sha_quoted_in_v1_9_docstring", V1_8_SHA in SRC)
check("A06_v1_7_history_sha_quoted_in_v1_9_docstring", V1_7_SHA in SRC)

# ---- B. D22 — true write-once + authorized-attempt ordering ------------------ #
check("B01_v1_9_paths_declared",
      all(k in SRC for k in ("SMOKE_V1_9_ARTIFACT", "SMOKE_V1_9_START_MARKER",
                             "SMOKE_V1_9_FAILURE_ARTIFACT")))
check("B02_no_v1_8_residual_paths",
      "SMOKE_V1_8_ARTIFACT" not in SRC and "SMOKE_V1_8_ATTEMPT" not in SRC)
check("B03_gate_state_pure_helper", "_gate_smoke_state" in FUNCS
      and "open(" not in seg("_gate_smoke_state"))
check("B04_start_marker_exclusive_create_helper", "_create_smoke_start_marker" in FUNCS)
check("B05_start_marker_os_excl",
      "os.O_CREAT" in seg("_create_smoke_start_marker")
      and "os.O_EXCL" in seg("_create_smoke_start_marker"))
check("B06_gate_before_marker_in_main",
      seg("main").index("_gate_smoke_state") < seg("main").index("_create_smoke_start_marker"))
check("B07_unauthorized_path_returns_before_marker",
      seg("main").index("PHASE36_V1_9_SMOKE_NOT_AUTHORIZED__NO_MARKER_CREATED")
      < seg("main").index("_create_smoke_start_marker"))
check("B08_second_attempt_refused",
      "PHASE36_V1_9_SMOKE_REEXECUTION_FORBIDDEN__FIRST_ATTEMPT_ALREADY_EXISTS"
      in seg("main"))
check("B09_failure_artifact_exclusive_create",
      'open(path, "x"' in seg("_write_smoke_failure_artifact"))
check("B10_failure_artifact_no_write_text",
      "write_text" not in seg("_write_smoke_failure_artifact"))
check("B11_success_artifact_exclusive_create",
      'open(path, "x"' in seg("_write_smoke_success_artifact"))
check("B12_failure_artifact_marked_incomplete",
      '"completed": False' in seg("_write_smoke_failure_artifact")
      and '"attempted": True' in seg("_write_smoke_failure_artifact"))
check("B13_failure_artifact_records_exception_fields",
      all(k in seg("_write_smoke_failure_artifact") for k in
          ("exception_type", "exception_message", "failing_stage")))
check("B14_failure_artifact_no_retry_no_overwrite_flags",
      '"automatic_retry": False' in seg("_write_smoke_failure_artifact")
      and '"overwrite_permitted": False' in seg("_write_smoke_failure_artifact"))
check("B15_provenance_derived_in_run_smoke",
      "attempt_provenance" in seg("run_smoke")
      and 'is_first_write_once' in seg("run_smoke"))
check("B16_write_once_check_derived_not_literal",
      'bool(attempt_provenance["is_first_write_once"])' in SRC)
check("B17_run_smoke_provenance_fail_closed",
      "D22_SMOKE_ATTEMPT_PROVENANCE_INVALID" in SRC)
check("B18_run_smoke_exclusive_recreate_probe",
      "FileExistsError" in seg("run_smoke")
      and "exclusive_recreate_forbidden" in seg("run_smoke"))
check("B19_no_loop_in_main", not any(isinstance(n, (ast.For, ast.While, ast.AsyncFor))
                                     for n in ast.walk(FUNCS["main"])))
check("B20_run_smoke_single_call_site_in_main",
      sum(1 for n in ast.walk(FUNCS["main"])
          if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
          and n.func.id == "run_smoke") <= 1)
check("B21_no_unlink_or_os_remove_overwrite",
      "unlink" not in CODE_ONLY and "os.remove" not in CODE_ONLY)

# ---- C. D23 — complete transitive integrity + checkpoint pre-hash ------------ #
check("C01_transitive_deps_dict_present",
      "TRANSITIVE_RUNTIME_DEPENDENCIES" in assigned_names(TREE))
check("C02_transitive_checkpoints_dict_present",
      "TRANSITIVE_RUNTIME_CHECKPOINTS" in assigned_names(TREE))
check("C03_integrity_function_present", "_verify_transitive_source_integrity" in FUNCS)
check("C04_integrity_hashes_checkpoints",
      "TRANSITIVE_RUNTIME_CHECKPOINTS.items()" in seg("_verify_transitive_source_integrity"))
ckpt = next((n.value for n in ast.walk(TREE) if isinstance(n, ast.Assign)
             and any(getattr(t, "id", None) == "TRANSITIVE_RUNTIME_CHECKPOINTS" for t in n.targets)),
            None)
check("C05_four_checkpoints_declared", ckpt is not None and len(ckpt.keys) == 4,
      detail={"n": (len(ckpt.keys) if ckpt is not None else 0)})
check("C06_integrity_gate_before_load_models_in_run_smoke",
      seg("run_smoke").index("_verify_transitive_source_integrity")
      < seg("run_smoke").index("_load_models"))
check("C07_integrity_fails_closed_on_mismatch",
      "TRANSITIVE_RUNTIME_SOURCE_INTEGRITY_FAILED" in SRC
      and 'if not source_integrity["all_match"]:' in SRC)
check("C08_manifest_missing_fails_closed",
      "MANIFEST_NOT_FOUND__FAIL_CLOSED" in seg("_verify_transitive_source_integrity"))
check("C09_no_self_check_skipped_bypass_token",
      "MANIFEST_NOT_FOUND__SELF_CHECK_SKIPPED" not in CODE_ONLY)
check("C10_manifest_malformed_fails_closed",
      "MANIFEST_MALFORMED__FAIL_CLOSED" in seg("_verify_transitive_source_integrity"))
check("C11_manifest_missing_field_fails_closed",
      "MANIFEST_MISSING_EXECUTION_SOURCE_SHA256__FAIL_CLOSED"
      in seg("_verify_transitive_source_integrity"))
check("C12_integrity_verifies_self_via_external_manifest",
      "execution_source_sha256" in SRC
      and "phase36_v1_9_runtime_source_integrity_manifest.json" in SRC)
check("C13_integrity_covers_common_authority",
      "phase36_robustness_common_v1_1.py" in SRC)
deps = next((n.value for n in ast.walk(TREE) if isinstance(n, ast.Assign)
             and any(getattr(t, "id", None) == "TRANSITIVE_RUNTIME_DEPENDENCIES" for t in n.targets)),
            None)
dep_keys = [k.value for k in deps.keys] if deps is not None else []
D23_NEW = ["scripts/analysis/train_phase25d_router.py",
           "scripts/analysis/phase25f_execution_common.py",
           "scripts/analysis/phase25f_post_safety_features.py",
           "src/features/barr_pre_refinement_features.py",
           "src/data/barr_roi.py"]
check("C14_integrity_covers_v1_9_load_bearing_sources",
      all(k in dep_keys for k in D23_NEW),
      detail={"missing": [k for k in D23_NEW if k not in dep_keys]})
check("C15_integrity_covers_g_and_system",
      "src/models/film/global_medfilm.py" in dep_keys
      and "src/models/barr/ra_medfilm_barr.py" in dep_keys)
check("C16_integrity_covers_device_and_metrics",
      "src/utils/device.py" in dep_keys and "src/metrics/evaluation_metrics.py" in dep_keys)
check("C17_all_four_checkpoints_bound",
      ckpt is not None and all(
          "checkpoints/" in k.value for k in ckpt.keys))

# ---- D. smoke success contract + check-matrix reconciliation ----------------- #
ids = smoke_check_ids()
keys = smoke_checks_keys()
check("D01_smoke_check_ids_declared", len(ids) > 0, detail={"n": len(ids)})
check("D02_smoke_all_pass_derives_from_all_checks",
      "smoke_all_pass = bool(all(smoke_checks.values()))" in SRC)
check("D03_set_equality_guard_present", "SMOKE_CHECK_CONTRACT_SET_MISMATCH" in SRC)
check("D04_count_equality_guard_present", "SMOKE_CHECK_CONTRACT_COUNT_MISMATCH" in SRC)
check("D05_declared_ids_equal_dict_keys", set(ids) == set(keys),
      detail={"declared": len(ids), "dict": len(keys),
              "missing": sorted(set(ids) - set(keys)),
              "extra": sorted(set(keys) - set(ids))})
check("D06_no_duplicate_ids", len(ids) == len(set(ids)) and len(keys) == len(set(keys)))

# ---- E. D20 (retained) — real-execute numerical binding ---------------------- #
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
check("E01_all_d20_ids_declared", all(i in ids for i in D20_IDS),
      detail={"missing": [i for i in D20_IDS if i not in ids]})
check("E02_d20_ids_bound_in_smoke_checks_mapping",
      all(f'"{i}": bool(' in SRC for i in D20_IDS),
      detail={"unbound": [i for i in D20_IDS if f'"{i}": bool(' not in SRC]})
check("E03_real_execute_probe_leaves_somega_logit_none",
      "forced_s_omega_logit=None" in seg("smoke_real_execute_component_probe"))
check("E04_real_execute_probe_forces_router_execute",
      "control_router_score = +50.0" in seg("smoke_real_execute_component_probe"))
check("E05_real_R_psi_forward_count_bound_to_1",
      'execute_probe["actual_R_psi_forward_count"] == 1' in SRC)
check("E06_real_S_omega_forward_count_bound_to_1",
      'execute_probe["actual_S_omega_forward_count"] == 1' in SRC)
check("E07_real_execute_valid_states_restricted",
      'in ("EXECUTE_THEN_ACCEPT", "EXECUTE_THEN_REJECT")' in SRC)

# ---- F. D24 — R_psi exact shape/range + final S_omega input exact dim/finite -- #
check("F01_somega_final_input_dim_derived",
      "SOMEGA_FINAL_INPUT_DIM = SOMEGA_NUMERIC_DIM + SOMEGA_ONEHOT_DIM" in SRC)
check("F02_somega_final_input_dim_asserted_20",
      "assert SOMEGA_FINAL_INPUT_DIM == 20" in SRC)
check("F03_core_result_exposes_final_input",
      "final_s_omega_input_dim" in seg("_core_result")
      and "final_s_omega_input_finite" in seg("_core_result"))
check("F04_core_result_exposes_refined_range",
      "refined_output_is_probability" in seg("_core_result")
      and "refined_output_in_unit_interval" in seg("_core_result"))
check("F05_core_captures_actual_final_input",
      "final_s_omega_input_capture" in seg("canonical_learned_core")
      and "post_safety_numeric_normalized_capture" in seg("canonical_learned_core"))
check("F06_core_capture_only_on_real_branch",
      seg("canonical_learned_core").index("if forced_s_omega_logit is not None:")
      < seg("canonical_learned_core").index(
          "final_s_omega_input_capture = np.asarray(full"))
check("F07_probe_surfaces_d24_fields",
      all(k in seg("smoke_real_execute_component_probe") for k in
          ("final_s_omega_input_dim", "final_s_omega_input_finite",
           "refined_output_is_probability", "refined_output_in_unit_interval")))
D24_IDS = ["real_execute_R_psi_output_exact_shape",
           "real_execute_R_psi_output_in_unit_interval",
           "real_execute_final_S_omega_input_exact_dim",
           "real_execute_final_S_omega_input_finite"]
check("F08_all_d24_ids_declared_and_bound",
      all(i in ids and f'"{i}": bool(' in SRC for i in D24_IDS),
      detail={"missing": [i for i in D24_IDS if i not in ids
                          or f'"{i}": bool(' not in SRC]})
check("F09_refined_sigmoid_probability_in_source",
      "torch.sigmoid(ctx[\"r_psi\"]" in SRC)
check("F10_final_input_schema_20_matches_frozen",
      "SOMEGA_NUMERIC_DIM = 16" in SRC and "SOMEGA_ONEHOT_DIM = 4" in SRC)

# ---- G. D25 — HD95 exact empty-case semantics -------------------------------- #
check("G01_hd95_case_exact_predicate", "_hd95_case_exact" in FUNCS)
check("G02_hd95_four_cases_bound", SRC.count("_hd95_case_exact(") >= 4)
check("G03_hd95_exact_reason_empty_prediction", '"empty_prediction"' in SRC)
check("G04_hd95_exact_reason_empty_ground_truth", '"empty_ground_truth"' in SRC)
check("G05_hd95_exact_reason_both_empty", '"both_empty"' in SRC)
check("G06_hd95_metric_domain_bound",
      'case.get("metric_domain") != "BOUNDARY_DISTANCE"' in CODE_ONLY)
check("G07_hd95_unit_bound", 'case.get("unit") != "pixel"' in CODE_ONLY)
check("G08_hd95_nonempty_requires_valid_true_and_finite",
      'expect_valid=True, expect_reason=""' in SRC)
check("G09_hd95_empty_requires_nonfinite",
      "bool(not np.isfinite(case.get(\"hd95\", np.nan)))" in SRC)
check("G10_no_tautological_none_acceptance",
      'in (True, False, None)' not in SRC)
check("G11_metric_authority_bound_to_frozen_module",
      "src.metrics import evaluation_metrics as M" in SRC)
D25_IDS = ["metric_hd95_nonempty_prediction_empty_gt_exact",
           "metric_hd95_empty_empty_exact"]
check("G12_all_d25_ids_declared_and_bound",
      all(i in ids and f'"{i}": bool(' in SRC for i in D25_IDS),
      detail={"missing": [i for i in D25_IDS if i not in ids
                          or f'"{i}": bool(' not in SRC]})
check("G13_dice_iou_bound_in_contract", "metric_dice_iou_plumbing_valid" in ids)

# ---- H. scientific-semantics preservation ------------------------------------ #
check("H01_canonical_sigmoid_operator_preserved", "torch.sigmoid(t.float())" in SRC)
check("H02_cuda_fail_closed_preserved", "get_device(require_cuda=True)" in SRC)
check("H03_val808_only_preserved", "VAL808_ONLY" in SRC)
check("H04_g_context_preserved",
      "CANONICAL_G_INFERENCE_MODE = False" in SRC
      and "canonical_g_forward_batched" in FUNCS)
check("H05_component_contexts_preserved",
      "component_inference_context" in FUNCS and "component_autocast_disabled" in FUNCS)
check("H06_router_vector_dim_202", "ROUTER_NUMERIC_DIM" in SRC)
check("H07_conditional_execution_order_preserved",
      "actual_r_psi_forwards" in SRC and "actual_s_omega_forwards" in SRC)
check("H08_thresholds_030_and_050_preserved",
      "ROI_PROPOSAL_THRESHOLD" in SRC and "SEGMENTATION_OUTPUT_THRESHOLD" in SRC)
check("H09_kub_subgroup_reporting_only_preserved",
      "reporting_only" in SRC and "kub_subgroup_map" in FUNCS)
check("H10_figure_registry_preserved",
      "FIGURE_REGISTRY" in SRC and all(f"figure_R{i}" in FUNCS for i in range(1, 6)))

# ---- I. protected-population unreachability ---------------------------------- #
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
check("I01_no_protected_symbol_reachable", len(prot) == 0, detail={"hits": prot[:10]})
check("I02_protected_counters_forever_zero_preserved", "COUNTERS_FOREVER_ZERO" in SRC)
check("I03_static_protected_io_detector_present",
      "_static_protected_io_unreachable" in FUNCS)
check("I04_val_manifest_is_only_runtime_authority",
      "VAL_MANIFEST_IS_ONLY_POPULATION_RUNTIME_AUTHORITY = True" in SRC)
check("I05_test_runtime_reads_disallowed_flag",
      "TEST_RUNTIME_READS_ALLOWED = False" in SRC)
check("I06_holdout_runtime_reads_disallowed_flag",
      "ROUTER_HOLDOUT_RUNTIME_READS_ALLOWED = False" in SRC)

# ---- J. gate separation + non-execution -------------------------------------- #
check("J01_smoke_gate_separate_from_science_gate",
      "SMOKE_GATE_ENV" in SRC and "GATE_ENV" in SRC and "PHASE36_SMOKE_EXECUTE" in SRC)
check("J02_no_v1_9_smoke_artifact_exists_yet",
      not (ROOT / "reports/audits/phase36_robustness_smoke_v1_9.json").exists())
check("J03_no_v1_9_start_marker_exists_yet",
      not (ROOT / "reports/audits/phase36_robustness_smoke_start_v1_9.json").exists())
check("J04_no_v1_9_failure_artifact_exists_yet",
      not (ROOT / "reports/audits/phase36_robustness_smoke_failure_v1_9.json").exists())
check("J05_no_v1_9_science_output_exists",
      not (ROOT / "reports/audits/phase36_robustness_scientific_result_v1_9.json").exists())
check("J06_ast_parse_ok", True)
check("J07_entrypoint_guarded_by_main_guard", 'if __name__ == "__main__":' in SRC)

passed = sum(1 for c in checks if c["passed"])
total = len(checks)
report = {
    "artifact": "phase36_robustness_preflight_v1_9",
    "phase": 36,
    "section": "§N",
    "method": "RA-MedFiLM-BARR",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_9",
    "type": "PREFLIGHT_CHECK_REPORT",
    "static_only": True,
    "model_free": True,
    "torch_imported": "torch" in sys.modules,
    "protected_population_read": False,
    "subject": "scripts/analysis/phase36_robustness_execution_v1_9.py",
    "subject_sha256": _sha(EXEC),
    "v1_8_preserved": {
        "execution_sha256": V1_8_SHA,
        "all_unchanged": _sha(V1_8) == V1_8_SHA,
    },
    "v1_7_preserved": {
        "execution_sha256": V1_7_SHA,
        "direct_byte_audit_sha256": V1_7_AUDIT_SHA,
        "source_freeze_sha256": V1_7_FREEZE_SHA,
        "all_unchanged": _sha(V1_7) == V1_7_SHA,
    },
    "n_declared_check_ids": len(ids),
    "passed": passed,
    "total": total,
    "all_pass": passed == total,
    "checks": checks,
}
out = ROOT / "reports/audits/phase36_robustness_preflight_v1_9.json"
out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({"passed": passed, "total": total, "all_pass": passed == total,
                  "n_declared_check_ids": len(ids)}, indent=1))
for c in checks:
    if not c["passed"]:
        print("FAIL:", c["check"], json.dumps(c.get("detail"), default=str))
raise SystemExit(0 if passed == total else 1)
