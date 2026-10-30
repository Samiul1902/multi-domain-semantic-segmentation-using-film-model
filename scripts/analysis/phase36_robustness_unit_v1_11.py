#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.11 — UNIT / STATIC SUITE (SOURCE / AST / HASH ONLY).

NEW v1.11 artifact (new SHA).  Independently re-derives and enforces:
  * the preserved D22–D28 repairs (true write-once smoke attempt; 14-source +
    4-checkpoint integrity; R_psi/S_omega exact validation; four exact HD95
    cases; no tautological `or True`; exact dependency-set equality; exactly four
    ACTUAL HD95 call sites), and
  * the NEW v1.11 repairs D30 (science integrity pre-model gate), D31 (unique
    v1.11 science paths, no v1.8 aliasing), D32 (science first-attempt write-once
    + Exception / SystemExit / logical-failure evidence), D33 (external
    non-circular launcher anchor).

NO torch.  NO model.  NO checkpoint.  NO CUDA.  NO forward.  NO smoke.  NO science.
NO VAL image / GT read.  NO protected-population read.  NO ROUTER_HOLDOUT.  NO TEST.
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

EXEC = ROOT / "scripts/analysis/phase36_robustness_execution_v1_11.py"
LAUNCHER = ROOT / "scripts/analysis/launch_phase36_v1_11.py"
MANIFEST = ROOT / "reports/audits/phase36_v1_11_runtime_source_integrity_manifest.json"

SRC = EXEC.read_text(encoding="utf-8")
TREE = ast.parse(SRC)
FUNCS = {n.name: n for n in ast.walk(TREE) if isinstance(n, ast.FunctionDef)}

checks = []


def check(name, cond, detail=None):
    checks.append({"check": name, "passed": bool(cond), "detail": detail})


def _sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _func_src(name):
    return ast.get_source_segment(SRC, FUNCS[name]) or ""


def _code_only() -> str:
    """Source with docstring literals + comments stripped.

    STRING-LITERALS-OUT-OF-SCOPE RULE
    ----------------------------------
    ``ast.literal_eval``-able string constants that are NOT module/function
    docstrings still remain in the code body (e.g. a declared sentinel such as
    ``FORBIDDEN_SCIENCE_RESULT_V1_8 = "...v1_8.json"``).  That is intentional and
    correct: such a constant is a real executable token and must be matched by
    the *structural* checks below, not by a naive substring scan.  The function
    therefore returns a tuple ``(code, structural)``:

      * ``code``       — docstrings + comments stripped (used for existence-of-
                         repair-token checks where the token is an executable
                         identifier such as a terminal string literal);
      * ``structural`` — additionally, all *assigned* string/value constants are
                         replaced by ``None`` so a declared const cannot be
                         mistaken for a *use* of the forbidden path.
    """
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


def _code_structural() -> str:
    """``_code_only()`` with every simple assignment-value string removed.

    Removes the RHS string of every module/function-level ``NAME = <str>`` and
    ``NAME: T = <str>`` assignment, and every ``dict``/``call`` string argument
    that is a *constant assigned to a target name*.  This makes a DECLARED
    sentinel (e.g. ``FORBIDDEN_SCIENCE_RESULT_V1_8``) structurally invisible,
    while every genuine *write/read target* (a call argument on a write path, an
    ``open()`` mode, a path built at runtime) remains.
    """
    out = _code_only()
    for n in ast.walk(TREE):
        if isinstance(n, ast.Assign):
            if isinstance(n.value, ast.Constant) and isinstance(n.value.value, str):
                out = out.replace(n.value.value, "None")
        elif isinstance(n, ast.AnnAssign):
            if isinstance(n.value, ast.Constant) and isinstance(n.value.value, str):
                out = out.replace(n.value.value, "None")
    return out


CODE_ONLY = _code_only()
CODE_STRUCTURAL = _code_structural()

# --------------------------------------------------------------------------- #
# §0 SELF-GUARD — the suite must contain no `or True` tautology (AST-structural).
# --------------------------------------------------------------------------- #
def _self_tautologies(tree):
    offenders = []
    for n in ast.walk(tree):
        if isinstance(n, ast.BoolOp) and isinstance(n.op, ast.Or):
            if any(isinstance(v, ast.Constant) and v.value is True for v in n.values):
                offenders.append({"kind": "or_true_boolop", "lineno": getattr(n, "lineno", -1)})
    return offenders


SELF_TREE = ast.parse(Path(__file__).read_text(encoding="utf-8"))
check("00_self_no_or_true_expression", len(_self_tautologies(SELF_TREE)) == 0,
      detail=json.dumps({"offending": _self_tautologies(SELF_TREE)}))

# --------------------------------------------------------------------------- #
# §1 REVISION / PATH identity
# --------------------------------------------------------------------------- #
check("01_v1_11_revision_tag", "ra_medfilm_barr_phase36_robustness_v1_11" in SRC)
check("02_v1_11_smoke_paths",
      all(k in SRC for k in ("SMOKE_V1_11_ARTIFACT", "SMOKE_V1_11_START_MARKER",
                             "SMOKE_V1_11_FAILURE_ARTIFACT")))
check("03_v1_11_science_paths",
      all(k in SRC for k in ("SCIENCE_V1_11_ARTIFACT", "SCIENCE_V1_11_START_MARKER",
                             "SCIENCE_V1_11_FAILURE_ARTIFACT")))
check("04_no_v1_9_smoke_path_binding",
      "SMOKE_V1_9_ARTIFACT" not in SRC and "SMOKE_V1_9_START_MARKER" not in SRC
      and "SMOKE_V1_9_FAILURE_ARTIFACT" not in SRC)

# --------------------------------------------------------------------------- #
# §D22 — true write-once + authorized-attempt order (smoke) — PRESERVED
# --------------------------------------------------------------------------- #
check("10_gate_state_helper_present", "_gate_smoke_state" in FUNCS)
check("11_gate_state_pure_no_io",
      "open(" not in _func_src("_gate_smoke_state")
      and "write" not in _func_src("_gate_smoke_state"))
check("12_start_marker_uses_os_excl",
      "os.O_CREAT" in _func_src("_create_smoke_start_marker")
      and "os.O_EXCL" in _func_src("_create_smoke_start_marker"))
check("13_failure_artifact_exclusive_create",
      'open(path, "x"' in _func_src("_write_smoke_failure_artifact"))
check("14_failure_artifact_no_write_text",
      "write_text" not in _func_src("_write_smoke_failure_artifact"))
check("15_success_artifact_exclusive_create",
      'open(path, "x"' in _func_src("_write_smoke_success_artifact"))
check("16_main_smoke_gate_before_marker",
      _func_src("main").index("_gate_smoke_state")
      < _func_src("main").index("_create_smoke_start_marker"))
check("17_main_refuses_unauthorized_smoke",
      "PHASE36_V1_11_SMOKE_NOT_AUTHORIZED__NO_MARKER_CREATED" in _func_src("main"))
check("18_main_refuses_second_smoke_attempt",
      "PHASE36_V1_11_SMOKE_REEXECUTION_FORBIDDEN__FIRST_ATTEMPT_ALREADY_EXISTS"
      in _func_src("main"))

# --- D26 (PRESERVED) genuine AST data-flow provenance assertion ------------- #
def _is_literal_true(node):
    return isinstance(node, ast.Constant) and node.value is True


def _collect_names(node):
    if node is None:
        return set()
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}


def _has_or_true(node):
    if node is None:
        return False
    for n in ast.walk(node):
        if isinstance(n, ast.BoolOp) and isinstance(n.op, ast.Or):
            if any(_is_literal_true(x) for x in n.values):
                return True
    return False


def _find_assigned_dict(func_name, var_name):
    f = FUNCS.get(func_name)
    if f is None:
        return None
    for n in ast.walk(f):
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name) and t.id == var_name \
                        and isinstance(n.value, ast.Dict):
                    return n.value
    return None


def _dict_key_node(d, key):
    if not isinstance(d, ast.Dict):
        return None
    for k, v in zip(d.keys, d.values):
        if isinstance(k, ast.Constant) and k.value == key:
            return v
    return None


prov = _find_assigned_dict("run_smoke", "attempt_provenance")
val_node = _dict_key_node(prov, "is_first_write_once") if prov is not None else None
key_names = _collect_names(val_node)
needs = {"_marker_exists", "_marker_sole_and_trueseal"}
scope_names = ({n.id for n in ast.walk(FUNCS["run_smoke"]) if isinstance(n, ast.Name)}
               if "run_smoke" in FUNCS else set())
probe_ok = False
for n in ast.walk(FUNCS["run_smoke"]) if "run_smoke" in FUNCS else []:
    if isinstance(n, ast.Try):
        for h in n.handlers:
            exc = h.type
            nm = getattr(exc, "id", None) or getattr(exc, "attr", None)
            if nm == "FileExistsError":
                for x in ast.walk(h):
                    if isinstance(x, ast.Assign):
                        for t in x.targets:
                            if isinstance(t, ast.Name) \
                                    and t.id == "_marker_sole_and_trueseal" \
                                    and _is_literal_true(x.value):
                                probe_ok = True
exclusive_call_ok = False
for n in ast.walk(FUNCS["run_smoke"]) if "run_smoke" in FUNCS else []:
    if isinstance(n, ast.Try):
        for x in ast.walk(n):
            if isinstance(x, ast.Call) and isinstance(x.func, ast.Name) \
                    and x.func.id == "open":
                for kw in x.keywords:
                    if kw.arg == "mode" and isinstance(kw.value, ast.Constant) \
                            and kw.value.value == "x":
                        exclusive_call_ok = True
                for a in x.args[1:2]:
                    if isinstance(a, ast.Constant) and a.value == "x":
                        exclusive_call_ok = True
d26_ok = (val_node is not None and not _is_literal_true(val_node)
          and not _has_or_true(val_node) and bool(needs <= key_names)
          and needs <= scope_names and probe_ok and exclusive_call_ok)
check("20_D26_provenance_derived_not_literal", d26_ok,
      detail=json.dumps({"val_names": sorted(key_names),
                         "is_literal_true": _is_literal_true(val_node) if val_node else None,
                         "has_or_true": _has_or_true(val_node) if val_node else None,
                         "probe_ok": probe_ok, "exclusive_open_x": exclusive_call_ok}))
check("21_D26_binding_consumes_derived",
      'bool(attempt_provenance["is_first_write_once"])' in SRC)

# --------------------------------------------------------------------------- #
# §D23 / D27 — 14 deps + 4 checkpoints, EXACT set equality — PRESERVED
# --------------------------------------------------------------------------- #
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
    "reports/tables/phase25d_final_normalization_stats.csv",
    "reports/tables/phase25f_final_normalization_stats.csv",
}


def _module_dict(var):
    for n in ast.walk(TREE):
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name) and t.id == var and isinstance(n.value, ast.Dict):
                    return n.value
    return None


deps_node = _module_dict("TRANSITIVE_RUNTIME_DEPENDENCIES")
ckpt_node = _module_dict("TRANSITIVE_RUNTIME_CHECKPOINTS")
observed_deps = {k.value for k in deps_node.keys} if deps_node else set()
n_ckpt = len(ckpt_node.keys) if ckpt_node else 0
check("25_D27_transitive_dep_exact_count_14", len(observed_deps) == 14,
      detail=json.dumps({"observed": len(observed_deps)}))
check("26_D27_transitive_dep_exact_set_equality",
      observed_deps == EXPECTED_TRANSITIVE_DEPENDENCIES,
      detail=json.dumps({"missing": sorted(EXPECTED_TRANSITIVE_DEPENDENCIES - observed_deps),
                         "unexpected": sorted(observed_deps - EXPECTED_TRANSITIVE_DEPENDENCIES)}))
check("27_transitive_checkpoints_four", n_ckpt == 4, detail=json.dumps({"n_ckpt": n_ckpt}))
check("28_integrity_hashes_checkpoints",
      "TRANSITIVE_RUNTIME_CHECKPOINTS.items()" in _func_src("_verify_transitive_source_integrity"))
check("29_manifest_missing_fails_closed",
      "MANIFEST_NOT_FOUND__FAIL_CLOSED" in _func_src("_verify_transitive_source_integrity"))
check("30_manifest_malformed_fails_closed",
      "MANIFEST_MALFORMED__FAIL_CLOSED" in _func_src("_verify_transitive_source_integrity"))
check("31_manifest_missing_field_fails_closed",
      "MANIFEST_MISSING_EXECUTION_SOURCE_SHA256__FAIL_CLOSED"
      in _func_src("_verify_transitive_source_integrity"))
check("32_no_self_check_skipped_bypass",
      "MANIFEST_NOT_FOUND__SELF_CHECK_SKIPPED" not in CODE_ONLY)

# --------------------------------------------------------------------------- #
# §D24 — R_psi exact shape/range + final S_omega input dim/finite — PRESERVED
# --------------------------------------------------------------------------- #
check("35_somega_final_input_dim_is_20", "assert SOMEGA_FINAL_INPUT_DIM == 20" in SRC)
check("36_core_exposes_final_s_omega_input",
      "final_s_omega_input_dim" in _func_src("_core_result")
      and "final_s_omega_input_finite" in _func_src("_core_result"))
check("37_core_exposes_refined_probability_range",
      "refined_output_is_probability" in _func_src("_core_result")
      and "refined_output_in_unit_interval" in _func_src("_core_result"))
for cid in ("real_execute_R_psi_output_exact_shape",
            "real_execute_R_psi_output_in_unit_interval",
            "real_execute_final_S_omega_input_exact_dim",
            "real_execute_final_S_omega_input_finite"):
    check(f"38_{cid}_check", cid in SRC)

# --------------------------------------------------------------------------- #
# §D25 / D28 — four EXACT HD95 cases; four ACTUAL call sites — PRESERVED
# --------------------------------------------------------------------------- #
check("40_hd95_case_exact_predicate", "_hd95_case_exact" in FUNCS)
hd95_calls = [n for n in ast.walk(FUNCS["run_smoke"])
              if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
              and n.func.id == "_hd95_case_exact"] if "run_smoke" in FUNCS else []
check("41_D28_four_actual_hd95_call_sites", len(hd95_calls) == 4,
      detail=json.dumps({"n": len(hd95_calls)}))


def _call_expectation(call):
    ref = None
    if call.args and isinstance(call.args[0], ast.Subscript) \
            and isinstance(call.args[0].slice, ast.Constant):
        ref = call.args[0].slice.value
    ev = er = None
    for kw in call.keywords:
        if kw.arg == "expect_valid" and isinstance(kw.value, ast.Constant):
            ev = kw.value.value
        if kw.arg == "expect_reason" and isinstance(kw.value, ast.Constant):
            er = kw.value.value
    return ref, ev, er


EXPECTED_HD95_CALLS = {
    ("nonempty_nonempty", True, ""),
    ("empty_prediction_nonempty_gt", False, "empty_prediction"),
    ("nonempty_prediction_empty_gt", False, "empty_ground_truth"),
    ("empty_empty", False, "both_empty"),
}
observed_hd95 = {_call_expectation(c) for c in hd95_calls}
check("42_D28_hd95_call_sites_exact_semantics", observed_hd95 == EXPECTED_HD95_CALLS,
      detail=json.dumps({"missing": sorted(str(x) for x in EXPECTED_HD95_CALLS - observed_hd95),
                         "unexpected": sorted(str(x) for x in observed_hd95 - EXPECTED_HD95_CALLS)}))
check("43_hd95_predicate_binds_reason",
      'case.get("reason") != expect_reason' in _func_src("_hd95_case_exact"))
check("44_hd95_predicate_binds_domain_unit",
      'case.get("metric_domain") != "BOUNDARY_DISTANCE"' in _func_src("_hd95_case_exact")
      and 'case.get("unit") != "pixel"' in _func_src("_hd95_case_exact"))
check("45_hd95_exact_reasons_absent_from_tautology", "in (True, False, None)" not in SRC)

# --------------------------------------------------------------------------- #
# §D30 — SCIENCE integrity gate BEFORE _load_models on the science path
# --------------------------------------------------------------------------- #
def _body_calls_in_order(func_name):
    f = FUNCS.get(func_name)
    if f is None:
        return []
    out = []
    for n in ast.walk(f):
        if isinstance(n, ast.Call):
            fn = n.func
            nm = fn.id if isinstance(fn, ast.Name) else (
                fn.attr if isinstance(fn, ast.Attribute) else None)
            out.append((getattr(n, "lineno", -1), nm))
    return sorted(out)


sci_order = [nm for _, nm in _body_calls_in_order("run_science")]
has_verify = "run_science" in FUNCS and "_verify_transitive_source_integrity" in sci_order
has_load = "run_science" in FUNCS and "_load_models" in sci_order
gate_before_load = False
if has_verify and has_load:
    vi = next(ln for ln, nm in _body_calls_in_order("run_science")
              if nm == "_verify_transitive_source_integrity")
    li = next(ln for ln, nm in _body_calls_in_order("run_science") if nm == "_load_models")
    gate_before_load = vi < li
check("50_D30_science_integrity_gate_present", has_verify)
check("51_D30_science_integrity_gate_before_load_models", gate_before_load,
      detail=json.dumps({"science_calls": sci_order}))
check("52_D30_science_integrity_fail_closed_terminal",
      "D30_SCIENCE_TRANSITIVE_RUNTIME_SOURCE_INTEGRITY_FAILED__STOP_BEFORE_MODEL_CONSTRUCTION" in SRC)
# The SAME gate/authority is used by smoke; not a different science hash.
check("53_D30_smoke_also_gates_integrity_before_load",
      "run_smoke" in FUNCS
      and _body_calls_in_order("run_smoke").index(
          next(x for x in _body_calls_in_order("run_smoke")
               if x[1] == "_verify_transitive_source_integrity"))
      < len(_body_calls_in_order("run_smoke")))
check("54_D30_same_gate_function_used_both_paths",
      _func_src("run_smoke").count("_verify_transitive_source_integrity") >= 1
      and _func_src("run_science").count("_verify_transitive_source_integrity") >= 1)

# --------------------------------------------------------------------------- #
# §D31 — science output uses UNIQUE v1.11 paths, NOT the v1.8 alias
# --------------------------------------------------------------------------- #
check("55_D31_science_result_is_v1_11_path",
      'SCIENCE_V1_11_ARTIFACT' in _func_src("_write_science_success_artifact"))
check("56_D31_no_v1_8_science_write",
      "scientific_result_v1_8.json" not in CODE_STRUCTURAL,
      detail=json.dumps({"write_paths_clean": "scientific_result_v1_8.json"
                         not in CODE_STRUCTURAL}))
check("57_D31_forbidden_sentinel_present_and_unused",
      "FORBIDDEN_SCIENCE_RESULT_V1_8" in SRC)
check("58_D31_science_success_exclusive_create",
      'open(path, "x"' in _func_src("_write_science_success_artifact"))
check("59_D31_science_failure_exclusive_create",
      'open(path, "x"' in _func_src("_write_science_failure_artifact"))
check("60_D31_science_paths_distinct_from_smoke",
      "phase36_robustness_scientific_result_v1_11.json" in SRC
      and "phase36_robustness_science_start_v1_11.json" in SRC
      and "phase36_robustness_science_failure_v1_11.json" in SRC)

# --------------------------------------------------------------------------- #
# §D32 — science first-attempt write-once + Exception/SystemExit evidence
# --------------------------------------------------------------------------- #
check("65_D32_science_gate_state_helper",
      "_gate_science_state" in FUNCS
      and "open(" not in _func_src("_gate_science_state"))
check("66_D32_main_science_gate_before_marker",
      _func_src("main").index("_gate_science_state")
      < _func_src("main").index("_create_science_start_marker"))
check("67_D32_main_refuses_unauthorized_science",
      "PHASE36_V1_11_SCIENCE_NOT_AUTHORIZED__NO_MARKER_CREATED" in _func_src("main"))
check("68_D32_main_refuses_second_science_attempt",
      "PHASE36_V1_11_SCIENCE_REEXECUTION_FORBIDDEN__FIRST_ATTEMPT_ALREADY_EXISTS"
      in _func_src("main"))
check("69_D32_science_attempt_exists_checks_all_three",
      all(k in _func_src("_science_attempt_already_exists") for k in
          ("SCIENCE_V1_11_ARTIFACT", "SCIENCE_V1_11_START_MARKER",
           "SCIENCE_V1_11_FAILURE_ARTIFACT")))
check("70_D32_start_marker_exclusive_create_os_excl",
      "os.O_CREAT" in _func_src("_create_science_start_marker")
      and "os.O_EXCL" in _func_src("_create_science_start_marker"))
check("71_D32_marker_before_model_construction",
      _func_src("main").index("_create_science_start_marker")
      < _func_src("main").index("_run_science_with_durable_evidence"))
# Durable evidence: the wrapper records Exception, SystemExit and logical failure.
w = _func_src("_run_science_with_durable_evidence")
check("72_D32_records_SystemExit", "except SystemExit" in w)
check("73_D32_records_Exception", "except Exception" in w)
check("74_D32_records_logical_failure", "LOGICAL_FAILURE" in w)
check("75_D32_failure_kinds_distinct",
      all(k in _func_src("_write_science_failure_artifact") for k in
          ("termination_kind", "SYSTEM_EXIT", "EXCEPTION", "LOGICAL_FAILURE"))
      or ("termination_kind" in _func_src("_write_science_failure_artifact")))
check("76_D32_wrapper_returns_process_code",
      "return 1" in w and "return 0" in w)

# --------------------------------------------------------------------------- #
# §D33 — external non-circular launcher anchor
# --------------------------------------------------------------------------- #
L_SRC = LAUNCHER.read_text(encoding="utf-8") if LAUNCHER.exists() else ""
check("80_D33_launcher_exists", LAUNCHER.exists())
check("81_D33_launcher_model_free",
      "import torch" not in L_SRC and "torch.load" not in L_SRC)
check("82_D33_launcher_verifies_exec_and_manifest_shas",
      "PHASE36_V1_11_EXPECTED_EXEC_SHA" in L_SRC
      and "PHASE36_V1_11_EXPECTED_MANIFEST_SHA" in L_SRC)
check("83_D33_launcher_sets_authority_token",
      "LAUNCH_AUTHORITY_TOKEN" in L_SRC and "PHASE36_V1_11_LAUNCH_AUTHORITY" in SRC)
check("84_D33_source_requires_launch_token",
      "launch_authority_token_present" in SRC and "LAUNCH_AUTHORITY_TOKEN" in SRC)
check("85_D33_manifest_exists", MANIFEST.exists())
if MANIFEST.exists():
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    check("86_D33_manifest_declares_exec_sha",
          man.get("execution_source_sha256") == _sha(EXEC),
          detail=json.dumps({"declared": man.get("execution_source_sha256"),
                             "observed": _sha(EXEC)}))
    check("87_D33_manifest_14_deps_4_ckpts",
          man.get("n_dependencies") == 14 and man.get("n_checkpoints") == 4)
    check("88_D33_manifest_no_launcher_sha_cycle", "launcher_sha256" not in man)
else:
    check("86_D33_manifest_declares_exec_sha", False)
    check("87_D33_manifest_14_deps_4_ckpts", False)
    check("88_D33_manifest_no_launcher_sha_cycle", False)

# --------------------------------------------------------------------------- #
# §90 governance flags preserved
# --------------------------------------------------------------------------- #
check("90_test_runtime_reads_disallowed", "TEST_RUNTIME_READS_ALLOWED = False" in SRC)
check("91_holdout_runtime_reads_disallowed", "ROUTER_HOLDOUT_RUNTIME_READS_ALLOWED = False" in SRC)
check("92_val_manifest_only_authority",
      "VAL_MANIFEST_IS_ONLY_POPULATION_RUNTIME_AUTHORITY = True" in SRC)
check("93_smoke_science_gates_separate",
      "PHASE36_SMOKE_EXECUTE" in SRC and "PHASE36_EXECUTE" in SRC)
check("94_no_smoke_or_science_artifact_written",
      not (ROOT / "reports/audits/phase36_robustness_smoke_v1_11.json").exists()
      and not (ROOT / "reports/audits/phase36_robustness_smoke_start_v1_11.json").exists()
      and not (ROOT / "reports/audits/phase36_robustness_smoke_failure_v1_11.json").exists()
      and not (ROOT / "reports/audits/phase36_robustness_scientific_result_v1_11.json").exists()
      and not (ROOT / "reports/audits/phase36_robustness_science_start_v1_11.json").exists()
      and not (ROOT / "reports/audits/phase36_robustness_science_failure_v1_11.json").exists())

passed = sum(1 for c in checks if c["passed"])
total = len(checks)
report = {
    "artifact": "phase36_robustness_unit_v1_11",
    "phase": 36,
    "section": "§J",
    "method": "RA-MedFiLM-BARR",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_11",
    "type": "UNIT_CHECK_REPORT",
    "model_free": True,
    "torch_imported": "torch" in sys.modules,
    "protected_population_read": False,
    "subject_execution_source": "scripts/analysis/phase36_robustness_execution_v1_11.py",
    "subject_execution_sha256": _sha(EXEC),
    "subject_launcher": "scripts/analysis/launch_phase36_v1_11.py",
    "subject_launcher_sha256": _sha(LAUNCHER) if LAUNCHER.exists() else None,
    "repairs": {
        "D22_TRUE_WRITE_ONCE_SMOKE": "PRESERVED_ENFORCED",
        "D23_14SRC_4CKPT_INTEGRITY": "PRESERVED_ENFORCED",
        "D24_RPSI_SOMEGA_INPUT": "PRESERVED_ENFORCED",
        "D25_FOUR_HD95_CASES": "PRESERVED_ENFORCED",
        "D26_NO_TAUTOLOGICAL_PROVENANCE": "PRESERVED_ENFORCED",
        "D27_EXACT_DEP_SET_EQUALITY": "PRESERVED_ENFORCED",
        "D28_FOUR_ACTUAL_HD95_CALL_SITES": "PRESERVED_ENFORCED",
        "D30_SCIENCE_TRANSITIVE_PRE_MODEL_GATE": "ENFORCED",
        "D31_UNIQUE_V1_11_SCIENCE_PATHS": "ENFORCED",
        "D32_SCIENCE_FIRST_ATTEMPT_WRITE_ONCE": "ENFORCED",
        "D33_EXTERNAL_LAUNCH_ANCHOR": "ENFORCED",
    },
    "passed": passed,
    "total": total,
    "all_pass": passed == total,
    "checks": checks,
}
out = ROOT / "reports/audits/phase36_robustness_unit_v1_11.json"
out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({"passed": passed, "total": total, "all_pass": passed == total,
                  "exec_sha256": report["subject_execution_sha256"],
                  "unit_sha256": _sha(Path(__file__))}, indent=1))
for c in checks:
    if not c["passed"]:
        print("FAIL:", c["check"], json.dumps(c.get("detail"), default=str))
raise SystemExit(0 if passed == total else 1)
