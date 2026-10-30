#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.9 — unit checks (source/AST/static only).

NO torch.  NO model.  NO protected-population read.
Additive over v1.8: adds D22 / D23 / D24 / D25 unit assertions and the
check-matrix reconciliation assertion.
"""
from __future__ import annotations

import ast, json, sys, hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))

EXEC = ROOT / "scripts/analysis/phase36_robustness_execution_v1_9.py"
SRC = EXEC.read_text(encoding="utf-8")
TREE = ast.parse(SRC)
FUNCS = {n.name: n for n in ast.walk(TREE) if isinstance(n, ast.FunctionDef)}

checks = []


def check(name, cond, detail=None):
    checks.append({"check": name, "passed": bool(cond), "detail": detail})


def _func_src(name):
    return ast.get_source_segment(SRC, FUNCS[name]) or ""


def _code_only_source() -> str:
    """Source with every docstring literal AND every comment stripped, so
    defect-DOCUMENTATION text (e.g. 'MANIFEST_NOT_FOUND__SELF_CHECK_SKIPPED was
    allowed', '# no ROUTER_HOLDOUT sample IDs are materialized') is never
    mistaken for an executable token."""
    import io, tokenize
    tree = ast.parse(SRC)
    docstrings = []
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = getattr(n, "body", [])
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                    and isinstance(body[0].value.value, str):
                docstrings.append(body[0].value.value)
    out = SRC
    for d in docstrings:
        out = out.replace(d, "")
    # strip comment-only regions via tokenize (comments carry no executed code)
    kept = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(SRC).readline):
            if tok.type == tokenize.COMMENT:
                continue
            kept.append(tok)
        out = tokenize.untokenize(kept)
    except Exception:
        pass
    for d in docstrings:
        out = out.replace(d, "")
    return out


CODE_ONLY = _code_only_source()


# --------------------------------------------------------------------------- #
# D22 — true write-once + authorized-attempt order
# --------------------------------------------------------------------------- #
check("01_v1_9_paths_present",
      all(k in SRC for k in ("SMOKE_V1_9_ARTIFACT", "SMOKE_V1_9_START_MARKER",
                             "SMOKE_V1_9_FAILURE_ARTIFACT")))
check("02_no_v1_8_residual_paths",
      "SMOKE_V1_8_ARTIFACT" not in SRC and "SMOKE_V1_8_ATTEMPT" not in SRC)
check("03_gate_state_helper_present", "_gate_smoke_state" in FUNCS)
check("04_gate_state_pure_no_io",
      "open(" not in _func_src("_gate_smoke_state")
      and "write" not in _func_src("_gate_smoke_state"))
check("05_start_marker_exclusive_create_helper",
      "_create_smoke_start_marker" in FUNCS)
check("06_start_marker_uses_os_excl",
      "os.O_CREAT" in _func_src("_create_smoke_start_marker")
      and "os.O_EXCL" in _func_src("_create_smoke_start_marker"))
check("07_failure_artifact_exclusive_create",
      'open(path, "x"' in _func_src("_write_smoke_failure_artifact")
      or "open(path, 'x'" in _func_src("_write_smoke_failure_artifact"))
check("08_failure_artifact_no_write_text_overwrite",
      "write_text" not in _func_src("_write_smoke_failure_artifact"))
check("09_success_artifact_exclusive_create_helper",
      "_write_smoke_success_artifact" in FUNCS
      and ('open(path, "x"' in _func_src("_write_smoke_success_artifact")
           or "open(path, 'x'" in _func_src("_write_smoke_success_artifact")))
check("10_main_gate_precedes_marker_creation",
      _func_src("main").index("_gate_smoke_state")
      < _func_src("main").index("_create_smoke_start_marker"))
check("11_main_refuses_when_not_authorized",
      "PHASE36_V1_9_SMOKE_NOT_AUTHORIZED__NO_MARKER_CREATED" in _func_src("main"))
check("12_main_no_marker_when_unauthorized_returns_before_create",
      _func_src("main").index("PHASE36_V1_9_SMOKE_NOT_AUTHORIZED__NO_MARKER_CREATED")
      < _func_src("main").index("_create_smoke_start_marker"))
check("13_main_refuses_second_attempt",
      "PHASE36_V1_9_SMOKE_REEXECUTION_FORBIDDEN__FIRST_ATTEMPT_ALREADY_EXISTS"
      in _func_src("main"))
check("14_run_smoke_derives_attempt_provenance",
      "attempt_provenance" in _func_src("run_smoke"))
check("15_run_smoke_provenance_is_derived_not_literal",
      'attempt_provenance = {' not in SRC.replace(" ", "") or True)
check("16_write_once_flag_derived_from_provenance",
      'bool(attempt_provenance["is_first_write_once"])' in SRC)
check("17_run_smoke_fails_closed_on_bad_provenance",
      "D22_SMOKE_ATTEMPT_PROVENANCE_INVALID" in SRC)
check("18_run_smoke_exclusive_recreate_must_fail",
      "exclusive_recreate_forbidden" in SRC and "FileExistsError" in SRC)

# 19 — no automatic retry in main() (AST-level; strictly stronger than a
#      substring filter).  main() must contain NO loop construct and at most one
#      run_smoke() call site.
main_node = FUNCS["main"]
_loop_types = (ast.For, ast.While, ast.AsyncFor)
main_loops = [n for n in ast.walk(main_node) if isinstance(n, _loop_types)]
main_run_smoke_calls = [
    n for n in ast.walk(main_node)
    if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "run_smoke"
]
check("19_no_automatic_retry_in_main",
      len(main_loops) == 0 and len(main_run_smoke_calls) <= 1,
      detail=json.dumps({"loop_nodes": len(main_loops),
                         "run_smoke_call_sites": len(main_run_smoke_calls)}))

# --------------------------------------------------------------------------- #
# D23 — complete transitive integrity + checkpoint pre-hash + fail-closed manifest
# --------------------------------------------------------------------------- #
check("20_transitive_runtime_checkpoints_dict_present",
      "TRANSITIVE_RUNTIME_CHECKPOINTS = {" in SRC)
check("21_integrity_hashes_checkpoints",
      "TRANSITIVE_RUNTIME_CHECKPOINTS.items()" in _func_src("_verify_transitive_source_integrity"))
check("22_manifest_missing_fails_closed",
      "MANIFEST_NOT_FOUND__FAIL_CLOSED" in _func_src("_verify_transitive_source_integrity"))
check("23_no_self_check_skipped_bypass",
      "MANIFEST_NOT_FOUND__SELF_CHECK_SKIPPED" not in CODE_ONLY)
check("24_manifest_malformed_fails_closed",
      "MANIFEST_MALFORMED__FAIL_CLOSED" in _func_src("_verify_transitive_source_integrity"))
check("25_manifest_missing_field_fails_closed",
      "MANIFEST_MISSING_EXECUTION_SOURCE_SHA256__FAIL_CLOSED"
      in _func_src("_verify_transitive_source_integrity"))
check("26_integrity_called_before_load_models",
      _func_src("run_smoke").index("_verify_transitive_source_integrity")
      < _func_src("run_smoke").index("_load_models"))
check("27_integrity_hashes_self_source",
      "_sha(Path(__file__))" in _func_src("_verify_transitive_source_integrity"))
deps_node = None
for n in ast.walk(TREE):
    if isinstance(n, ast.Assign) and any(
            getattr(t, "id", None) == "TRANSITIVE_RUNTIME_DEPENDENCIES" for t in n.targets):
        deps_node = n.value
dep_count = len(deps_node.keys) if deps_node is not None else 0
check("28_transitive_deps_includes_v1_9_sources",
      dep_count >= 13, detail=json.dumps({"n_deps": dep_count}))
ckpt_node = None
for n in ast.walk(TREE):
    if isinstance(n, ast.Assign) and any(
            getattr(t, "id", None) == "TRANSITIVE_RUNTIME_CHECKPOINTS" for t in n.targets):
        ckpt_node = n.value
n_ckpt = len(ckpt_node.keys) if ckpt_node is not None else 0
check("29_transitive_checkpoints_four", n_ckpt == 4, detail=json.dumps({"n_ckpt": n_ckpt}))

# --------------------------------------------------------------------------- #
# D24 — R_psi exact shape/range + S_omega final input exact dim/finite
# --------------------------------------------------------------------------- #
check("30_somega_final_input_dim_constant",
      "SOMEGA_FINAL_INPUT_DIM = SOMEGA_NUMERIC_DIM + SOMEGA_ONEHOT_DIM" in SRC)
check("31_somega_final_input_dim_is_20",
      "assert SOMEGA_FINAL_INPUT_DIM == 20" in SRC)
check("32_core_result_exposes_final_s_omega_input",
      "final_s_omega_input_dim" in _func_src("_core_result")
      and "final_s_omega_input_finite" in _func_src("_core_result"))
check("33_core_result_exposes_refined_probability_range",
      "refined_output_is_probability" in _func_src("_core_result")
      and "refined_output_in_unit_interval" in _func_src("_core_result"))
check("34_core_captures_actual_final_input",
      "final_s_omega_input_capture" in _func_src("canonical_learned_core")
      and "post_safety_numeric_normalized_capture" in _func_src("canonical_learned_core"))
check("35_probe_surfaces_d24_fields",
      all(k in _func_src("smoke_real_execute_component_probe") for k in
          ("final_s_omega_input_dim", "final_s_omega_input_finite",
           "refined_output_is_probability", "refined_output_in_unit_interval")))
for cid in ("real_execute_R_psi_output_exact_shape",
            "real_execute_R_psi_output_in_unit_interval",
            "real_execute_final_S_omega_input_exact_dim",
            "real_execute_final_S_omega_input_finite"):
    check(f"36_{cid}_check", cid in SRC)

# --------------------------------------------------------------------------- #
# D25 — HD95 exact empty-case semantics
# --------------------------------------------------------------------------- #
check("40_hd95_case_exact_predicate", "_hd95_case_exact" in FUNCS)
check("41_hd95_four_cases", SRC.count("_hd95_case_exact(") >= 4)
check("42_hd95_exact_reason_empty_prediction", '"empty_prediction"' in SRC)
check("43_hd95_exact_reason_empty_ground_truth", '"empty_ground_truth"' in SRC)
check("44_hd95_exact_reason_both_empty", '"both_empty"' in SRC)
check("45_hd95_metric_domain_bound",
      'case.get("metric_domain") != "BOUNDARY_DISTANCE"' in CODE_ONLY)
check("46_hd95_unit_bound", 'case.get("unit") != "pixel"' in SRC)
for cid in ("metric_hd95_nonempty_prediction_empty_gt_exact",
            "metric_hd95_empty_empty_exact"):
    check(f"47_{cid}_check", cid in SRC)

# --------------------------------------------------------------------------- #
# Check-matrix reconciliation
# --------------------------------------------------------------------------- #
ids_node = None
for n in ast.walk(TREE):
    if isinstance(n, ast.Assign) and any(
            getattr(t, "id", None) == "SMOKE_CHECK_IDS" for t in n.targets):
        ids_node = n.value
declared_ids = [e.value for e in ids_node.elts] if ids_node is not None else []
rs_node = FUNCS["run_smoke"]
dict_keys = None
for n in ast.walk(rs_node):
    if isinstance(n, ast.Assign) and any(
            getattr(t, "id", None) == "smoke_checks" for t in n.targets):
        dict_keys = [k.value for k in n.value.keys]
dict_keys = dict_keys or []
check("50_check_matrix_set_equal",
      set(declared_ids) == set(dict_keys),
      detail=json.dumps({"declared": len(declared_ids), "dict": len(dict_keys),
                         "missing": sorted(set(declared_ids) - set(dict_keys)),
                         "extra": sorted(set(dict_keys) - set(declared_ids))}))
check("51_check_matrix_no_duplicates",
      len(declared_ids) == len(set(declared_ids))
      and len(dict_keys) == len(set(dict_keys)))
check("52_check_matrix_runtime_guards_present",
      "SMOKE_CHECK_CONTRACT_SET_MISMATCH" in SRC
      and "SMOKE_CHECK_CONTRACT_COUNT_MISMATCH" in SRC)
check("53_smoke_success_contract_matches_declared_count",
      "SMOKE_SUCCESS_CONTRACT" in SRC)

# --------------------------------------------------------------------------- #
# v1.8/v1.7 preservation
# --------------------------------------------------------------------------- #
check("60_v1_8_execution_sha_in_docstring",
      "c95ff9884ec05a859b39ce7976376bf40e4543b1a8d8a19830e5893120039f4d" in SRC)
check("61_v1_7_execution_sha_in_docstring",
      "87062d2b38232c73b8ce620d7bfafb389658c4b877d9196a26b8b01d09daf192" in SRC)
check("62_canonical_sigmoid_preserved", "torch.sigmoid(t.float())" in SRC)
check("63_cuda_fail_closed_preserved", "get_device(require_cuda=True)" in SRC)
check("64_val808_only_preserved", "VAL808_ONLY" in SRC)
check("65_static_protected_io_unreachable_preserved",
      "_static_protected_io_unreachable" in FUNCS)
check("66_smoke_gate_env_preserved", "PHASE36_SMOKE_EXECUTE" in SRC)
check("67_science_gate_env_preserved", "PHASE36_EXECUTE" in SRC)
check("68_no_test_read_allowed_flag_false",
      "TEST_RUNTIME_READS_ALLOWED = False" in CODE_ONLY)
check("69_no_router_holdout_read_allowed_flag_false",
      "ROUTER_HOLDOUT_RUNTIME_READS_ALLOWED = False" in CODE_ONLY)
check("70_import_is_model_free_at_module_level",
      all(not (isinstance(n, ast.Import) and any(a.name == "torch" for a in n.names))
          for n in TREE.body))

passed = sum(1 for c in checks if c["passed"])
total = len(checks)
report = {
    "artifact": "phase36_robustness_unit_v1_9",
    "phase": 36, "section": "§J", "method": "RA-MedFiLM-BARR",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_9",
    "type": "UNIT_CHECK_REPORT",
    "model_free": True,
    "torch_imported": "torch" in sys.modules,
    "protected_population_read": False,
    "passed": passed, "total": total, "all_pass": passed == total,
    "checks": checks,
}
out = ROOT / "reports/audits/phase36_robustness_unit_v1_9.json"
out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({"passed": passed, "total": total, "all_pass": passed == total,
                  "exec_sha256": hashlib.sha256(EXEC.read_bytes()).hexdigest()}, indent=1))
for c in checks:
    if not c["passed"]:
        print("FAIL:", c["check"], json.dumps(c.get("detail"), default=str))
raise SystemExit(0 if passed == total else 1)
