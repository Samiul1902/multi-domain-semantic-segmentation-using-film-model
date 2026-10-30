#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.10 — unit checks (source/AST/static only).

NO torch.  NO model.  NO protected-population read.

Additive over v1.9.  Repairs three under-constrained v1.9 unit tests:
  D26 — `15_run_smoke_provenance_is_derived_not_literal` was TAUTOLOGICAL
        (`... or True`) and always PASSed.  Replaced with a genuine AST
        data-flow assertion proving `smoke_attempt_is_first_write_once` is
        derived from actual attempt-provenance state.
  D27 — `28_transitive_deps_includes_v1_9_sources` only asserted
        `dep_count >= 13`.  Replaced with EXACT path-set equality (14 paths,
        no missing, no unexpected replacement).
  D28 — `41_hd95_four_cases` used a substring count that can match the
        function DEFINITION.  Replaced with an AST call-site proof: exactly
        four ACTUAL `_hd95_case_exact(...)` call sites, each bound to its
        exact expected (valid, reason).

The suite MUST contain no `or True`, no tautological boolean assertion, no
lower-bound count where an exact frozen set exists, and no substring-count
where actual call sites are required.
"""
from __future__ import annotations

import ast
import json
import sys
import hashlib
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
    defect-DOCUMENTATION text is never mistaken for an executable token."""
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
# §D26 SELF-GUARD: the unit suite itself must not contain tautologies.
# (This guards the VERY defect class D26 repairs; it is a genuine assertion,
#  not an `or True`.)
#
# AST-based, so string literals that merely QUOTE the pattern (this guard's
# own search token, D26 documentation text) can never false-trigger.  The real
# defect is a BoolOp(Or) with a literal True operand — or an unconditional
# literal-True assertion condition.  Both are forbidden in this suite.
# --------------------------------------------------------------------------- #
def _self_tautologies(tree):
    """Real tautology defects only: BoolOp(Or) containing a literal True
    operand (i.e. `... or True`).  AST-based, so string literals that merely
    QUOTE the pattern (this guard's own search token, D26 doc text) can never
    false-trigger."""
    offenders = []
    for n in ast.walk(tree):
        if isinstance(n, ast.BoolOp) and isinstance(n.op, ast.Or):
            if any(isinstance(v, ast.Constant) and v.value is True for v in n.values):
                offenders.append({"kind": "or_true_boolop",
                                  "lineno": getattr(n, "lineno", -1)})
    return offenders


SELF_TREE = ast.parse(Path(__file__).read_text(encoding="utf-8"))
self_or_true = _self_tautologies(SELF_TREE)
check("00_self_no_or_true_expression", len(self_or_true) == 0,
      detail=json.dumps({"offending": self_or_true}))


# --------------------------------------------------------------------------- #
# D22 — write-once + authorized-attempt order (retained v1.9 assertions)
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
check("17_run_smoke_fails_closed_on_bad_provenance",
      "D22_SMOKE_ATTEMPT_PROVENANCE_INVALID" in SRC)
check("18_run_smoke_exclusive_recreate_must_fail",
      "exclusive_recreate_forbidden" in SRC and "FileExistsError" in SRC)

# 19 — no automatic retry in main() (AST-level).
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
# §D26 — REAL provenance-derivation assertion (replaces the tautology).
# --------------------------------------------------------------------------- #
def _find_assigned_dict(func_name: str, target: str):
    """Return the ast.Dict assigned to `target` inside func_name, else None."""
    if func_name not in FUNCS:
        return None
    for n in ast.walk(FUNCS[func_name]):
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name) and t.id == target and isinstance(n.value, ast.Dict):
                    return n.value
    return None


def _dict_key_node(d: ast.Dict, key: str):
    for k, v in zip(d.keys, d.values):
        if isinstance(k, ast.Constant) and k.value == key:
            return v
    return None


def _is_literal_true(node) -> bool:
    return isinstance(node, ast.Constant) and node.value is True


def _is_literal_false(node) -> bool:
    return isinstance(node, ast.Constant) and node.value is False


def _collect_names(node) -> set:
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}


def _has_or_true(node) -> bool:
    for n in ast.walk(node):
        if isinstance(n, ast.BoolOp) and isinstance(n.op, ast.Or):
            if any(_is_literal_true(x) for x in n.values):
                return True
    return False


stmts = FUNCS["run_smoke"]
prov = _find_assigned_dict("run_smoke", "attempt_provenance")
derivation_ok = False
derivation_detail = {}
if prov is not None:
    val_node = _dict_key_node(prov, "is_first_write_once")
    key_names = _collect_names(val_node) if val_node is not None else set()
    # (a) must reference BOTH observed-provenance inputs
    needs = {"_marker_exists", "_marker_sole_and_trueseal"}
    # (b) must NOT be a bare literal True
    not_literal_true = (val_node is not None) and (not _is_literal_true(val_node))
    # (c) must NOT be a BoolOp containing a literal True (i.e. `... or True`)
    no_or_true = (val_node is not None) and (not _has_or_true(val_node))
    # (d) must actually combine the two provenance signals
    combines = bool(needs <= key_names)
    # (e) the two provenance signals must themselves be derived from real probes
    prov_names_in_scope = {n.id for n in ast.walk(FUNCS["run_smoke"])
                           if isinstance(n, ast.Name)}
    has_marker_exists = "_marker_exists" in prov_names_in_scope
    has_trueseal = "_marker_sole_and_trueseal" in prov_names_in_scope
    # (f) the exclusive-recreate probe must assign the trueseal flag inside a
    #     FileExistsError handler
    probe_ok = False
    for n in ast.walk(FUNCS["run_smoke"]):
        if isinstance(n, ast.Try):
            for h in n.handlers:
                exc = h.type
                exc_name = None
                if isinstance(exc, ast.Name):
                    exc_name = exc.id
                elif isinstance(exc, ast.Attribute):
                    exc_name = exc.attr
                if exc_name == "FileExistsError":
                    for x in ast.walk(h):
                        if isinstance(x, ast.Assign):
                            for t in x.targets:
                                if isinstance(t, ast.Name) and t.id == "_marker_sole_and_trueseal":
                                    if _is_literal_true(x.value):
                                        probe_ok = True
    # (g) the exclusive-create call must be present in the try body
    exclusive_call_ok = False
    for n in ast.walk(FUNCS["run_smoke"]):
        if isinstance(n, ast.Try):
            for x in ast.walk(n):
                if isinstance(x, ast.Call):
                    f = x.func
                    if isinstance(f, ast.Name) and f.id == "open":
                        for kw in x.keywords:
                            if kw.arg == "mode" and isinstance(kw.value, ast.Constant) \
                                    and kw.value.value == "x":
                                exclusive_call_ok = True
                        for a in x.args[1:2]:
                            if isinstance(a, ast.Constant) and a.value == "x":
                                exclusive_call_ok = True
    derivation_ok = (not_literal_true and no_or_true and combines
                     and has_marker_exists and has_trueseal
                     and probe_ok and exclusive_call_ok)
    derivation_detail = {
        "value_is_literal_true": bool(_is_literal_true(val_node)) if val_node else None,
        "value_is_or_true": bool(_has_or_true(val_node)) if val_node else None,
        "value_referenced_names": sorted(key_names),
        "combines_marker_exists_and_trueseal": combines,
        "marker_exists_defined": has_marker_exists,
        "trueseal_defined": has_trueseal,
        "trueseal_set_in_FileExistsError_handler": probe_ok,
        "exclusive_create_open_x_in_run_smoke_try": exclusive_call_ok,
    }
check("15_run_smoke_provenance_is_derived_not_literal", derivation_ok,
      detail=json.dumps(derivation_detail))

# The smoke_checks binding must consume `attempt_provenance["is_first_write_once"]`
# and must NOT be a bare literal True/False.
binding_node = _dict_key_node(_find_assigned_dict("run_smoke", "smoke_checks") or ast.Dict(
    keys=[], values=[]), "smoke_attempt_is_first_write_once")
binding_is_bool_call = isinstance(binding_node, ast.Call) and \
    isinstance(binding_node.func, ast.Name) and binding_node.func.id == "bool"
binding_names = sorted(_collect_names(binding_node)) if binding_node is not None else []
check("16_write_once_check_consumes_derived_provenance",
      binding_is_bool_call
      and "attempt_provenance" in binding_names
      and not _is_literal_true(binding_node)
      and not _is_literal_false(binding_node),
      detail=json.dumps({"binding_names": binding_names,
                         "is_bool_call": bool(binding_is_bool_call)}))

check("20_run_smoke_derives_attempt_provenance",
      "attempt_provenance" in _func_src("run_smoke"))


# --------------------------------------------------------------------------- #
# D23 — transitive integrity (retained) + §D27 EXACT dependency set.
# --------------------------------------------------------------------------- #
check("21_transitive_runtime_checkpoints_dict_present",
      "TRANSITIVE_RUNTIME_CHECKPOINTS = {" in SRC)
check("22_integrity_hashes_checkpoints",
      "TRANSITIVE_RUNTIME_CHECKPOINTS.items()" in _func_src("_verify_transitive_source_integrity"))
check("23_manifest_missing_fails_closed",
      "MANIFEST_NOT_FOUND__FAIL_CLOSED" in _func_src("_verify_transitive_source_integrity"))
check("24_no_self_check_skipped_bypass",
      "MANIFEST_NOT_FOUND__SELF_CHECK_SKIPPED" not in CODE_ONLY)
check("25_manifest_malformed_fails_closed",
      "MANIFEST_MALFORMED__FAIL_CLOSED" in _func_src("_verify_transitive_source_integrity"))
check("26_manifest_missing_field_fails_closed",
      "MANIFEST_MISSING_EXECUTION_SOURCE_SHA256__FAIL_CLOSED"
      in _func_src("_verify_transitive_source_integrity"))
check("27_integrity_called_before_load_models",
      _func_src("run_smoke").index("_verify_transitive_source_integrity")
      < _func_src("run_smoke").index("_load_models"))
check("28_integrity_hashes_self_source",
      "_sha(Path(__file__))" in _func_src("_verify_transitive_source_integrity"))

# §D27 EXACT expected transitive-dependency PATH SET (14, frozen in v1.9).
EXPECTED_TRANSITIVE_DEPENDENCIES = {
    "scripts/analysis/phase36_robustness_common_v1_1.py",
    "scripts/analysis/train_phase25d_router.py",
    "scripts/analysis/phase25f_execution_common.py",
    "scripts/analysis/phase25f_post_safety_features.py",
    "src/features/barr_pre_refinement_features.py",
    "src/data/barr_roi.py",
    "src/models/film/global_medfilm.py",
    "src/models/barr/regional_refiner.py",
    "src/models/barr/ra_medfilm_barr.py",
    "src/utils/device.py",
    "src/metrics/evaluation_metrics.py",
    "experiments/phase21_global_medfilm_fourdomain_seed42_clean_v3/config.json",
    "reports/tables/phase25d_final_normalization_stats.json".replace(".json", ".csv"),
    "reports/tables/phase25f_final_normalization_stats.csv",
}
deps_node = None
for n in ast.walk(TREE):
    if isinstance(n, ast.Assign):
        for t in n.targets:
            if isinstance(t, ast.Name) and t.id == "TRANSITIVE_RUNTIME_DEPENDENCIES":
                deps_node = n.value
observed_deps = set()
if isinstance(deps_node, ast.Dict):
    observed_deps = {k.value for k in deps_node.keys}
missing_deps = sorted(EXPECTED_TRANSITIVE_DEPENDENCIES - observed_deps)
unexpected_deps = sorted(observed_deps - EXPECTED_TRANSITIVE_DEPENDENCIES)
check("28_transitive_dep_exact_count_14",
      len(observed_deps) == 14,
      detail=json.dumps({"observed": len(observed_deps)}))
check("28b_transitive_dep_exact_set_equality",
      observed_deps == EXPECTED_TRANSITIVE_DEPENDENCIES,
      detail=json.dumps({"missing": missing_deps, "unexpected": unexpected_deps}))
check("28c_transitive_dep_no_missing",
      len(missing_deps) == 0, detail=json.dumps(missing_deps))
check("28d_transitive_dep_no_unexpected_replacement",
      len(unexpected_deps) == 0, detail=json.dumps(unexpected_deps))

ckpt_node = None
for n in ast.walk(TREE):
    if isinstance(n, ast.Assign):
        for t in n.targets:
            if isinstance(t, ast.Name) and t.id == "TRANSITIVE_RUNTIME_CHECKPOINTS":
                ckpt_node = n.value
n_ckpt = len(ckpt_node.keys) if isinstance(ckpt_node, ast.Dict) else 0
check("29_transitive_checkpoints_four", n_ckpt == 4, detail=json.dumps({"n_ckpt": n_ckpt}))


# --------------------------------------------------------------------------- #
# D24 — R_psi exact shape/range + S_omega final input exact dim/finite.
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
# §D28 — HD95 FOUR ACTUAL CALL SITES (AST), exact reasons. Replaces substring count.
# --------------------------------------------------------------------------- #
check("40_hd95_case_exact_predicate", "_hd95_case_exact" in FUNCS)

# Collect ACTUAL call sites: calls whose func is Name('_hd95_case_exact').
hd95_calls = []
for n in ast.walk(FUNCS["run_smoke"]):
    if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) \
            and n.func.id == "_hd95_case_exact":
        hd95_calls.append(n)
check("41_hd95_four_actual_call_sites", len(hd95_calls) == 4,
      detail=json.dumps({"n_actual_call_sites": len(hd95_calls)}))


def _call_expectation(call: ast.Call):
    """Extract (case_key_ref, expect_valid, expect_reason) from one call site."""
    case_ref = None
    if call.args:
        a0 = call.args[0]
        # hd_cases["<key>"]
        if isinstance(a0, ast.Subscript):
            sl = a0.slice
            if isinstance(sl, ast.Constant):
                case_ref = sl.value
    ev = None
    er = None
    for kw in call.keywords:
        if kw.arg == "expect_valid":
            if isinstance(kw.value, ast.Constant):
                ev = kw.value.value
        if kw.arg == "expect_reason":
            if isinstance(kw.value, ast.Constant):
                er = kw.value.value
    return case_ref, ev, er


EXPECTED_HD95_CALLS = {
    # (case-key, expect_valid, expect_reason) for the four frozen synthetic cases
    ("nonempty_nonempty", True, ""),
    ("empty_prediction_nonempty_gt", False, "empty_prediction"),
    ("nonempty_prediction_empty_gt", False, "empty_ground_truth"),
    ("empty_empty", False, "both_empty"),
}
observed_hd95 = set()
for c in hd95_calls:
    ref, ev, er = _call_expectation(c)
    observed_hd95.add((ref, ev, er))
check("42_hd95_call_sites_exact_semantics",
      observed_hd95 == EXPECTED_HD95_CALLS,
      detail=json.dumps({"missing": sorted(str(x) for x in EXPECTED_HD95_CALLS - observed_hd95),
                         "unexpected": sorted(str(x) for x in observed_hd95 - EXPECTED_HD95_CALLS)}))
check("43_hd95_case_exact_predicate_binds_reason",
      'case.get("reason") != expect_reason' in _func_src("_hd95_case_exact"))
check("44_hd95_case_exact_predicate_binds_domain_unit",
      'case.get("metric_domain") != "BOUNDARY_DISTANCE"' in _func_src("_hd95_case_exact")
      and 'case.get("unit") != "pixel"' in _func_src("_hd95_case_exact"))
check("45_hd95_case_exact_binds_validity",
      'case.get("valid") is not expect_valid' in _func_src("_hd95_case_exact"))
check("46_hd95_exact_reasons_absent_from_tautology",
      "in (True, False, None)" not in SRC)
for cid in ("metric_hd95_nonempty_prediction_empty_gt_exact",
            "metric_hd95_empty_empty_exact"):
    check(f"47_{cid}_check", cid in SRC)


# --------------------------------------------------------------------------- #
# Check-matrix reconciliation
# --------------------------------------------------------------------------- #
ids_node = None
for n in ast.walk(TREE):
    if isinstance(n, ast.Assign):
        for t in n.targets:
            if isinstance(t, ast.Name) and t.id == "SMOKE_CHECK_IDS":
                ids_node = n.value
declared_ids = [e.value for e in ids_node.elts] if isinstance(ids_node, ast.List) else []
dict_keys = None
for n in ast.walk(FUNCS["run_smoke"]):
    if isinstance(n, ast.Assign):
        for t in n.targets:
            if isinstance(t, ast.Name) and t.id == "smoke_checks":
                dict_keys = [k.value for k in n.value.keys]
dict_keys = dict_keys or []
check("50_check_matrix_set_equal",
      set(declared_ids) == set(dict_keys),
      detail=json.dumps({"declared": len(declared_ids), "dict": len(dict_keys)}))
check("51_check_matrix_no_duplicates",
      len(declared_ids) == len(set(declared_ids))
      and len(dict_keys) == len(set(dict_keys)))
check("52_check_matrix_runtime_guards_present",
      "SMOKE_CHECK_CONTRACT_SET_MISMATCH" in SRC
      and "SMOKE_CHECK_CONTRACT_COUNT_MISMATCH" in SRC)
check("53_smoke_success_contract_matches_declared_count",
      "SMOKE_SUCCESS_CONTRACT" in SRC)


# --------------------------------------------------------------------------- #
# v1.8 / v1.7 preservation
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
    "artifact": "phase36_robustness_unit_v1_10",
    "phase": 36, "section": "§J", "method": "RA-MedFiLM-BARR",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_10",
    "type": "UNIT_CHECK_REPORT",
    "model_free": True,
    "torch_imported": "torch" in sys.modules,
    "protected_population_read": False,
    "repairs": {
        "D26_TAUTOLOGICAL_D22_PROVENANCE_UNIT": "REPLACED_WITH_AST_DATAFLOW_ASSERTION",
        "D27_TRANSITIVE_DEPENDENCY_COUNT_UNDERCONSTRAINED": "EXACT_SET_EQUALITY_14",
        "D28_HD95_FOUR_CASE_CALLSITE_UNDERCONSTRAINED": "AST_FOUR_ACTUAL_CALL_SITES",
    },
    "subject_execution_source": "scripts/analysis/phase36_robustness_execution_v1_9.py",
    "subject_execution_sha256": hashlib.sha256(EXEC.read_bytes()).hexdigest(),
    "passed": passed, "total": total, "all_pass": passed == total,
    "checks": checks,
}
out = ROOT / "reports/audits/phase36_robustness_unit_v1_10.json"
out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({"passed": passed, "total": total, "all_pass": passed == total,
                  "exec_sha256": report["subject_execution_sha256"],
                  "unit_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
                 indent=1))
for c in checks:
    if not c["passed"]:
        print("FAIL:", c["check"], json.dumps(c.get("detail"), default=str))
raise SystemExit(0 if passed == total else 1)
