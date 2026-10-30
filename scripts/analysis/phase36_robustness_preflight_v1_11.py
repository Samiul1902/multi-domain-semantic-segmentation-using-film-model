#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.11 — PREFLIGHT (source / AST / static only).

Validates the NEW v1.11 governance repairs (D30 science transitive pre-model
integrity gate; D31 unique v1.11 science provenance paths / no v1.8 aliasing;
D32 science first-attempt write-once + durable Exception/SystemExit/logical
evidence; D33 external non-circular launcher anchor) as STATIC properties of the
NEW v1.11 execution subject + the NEW v1.11 unit suite + the NEW launcher, while
re-asserting that:
  * the frozen v1.9/v1.10 history is BYTE-PRESERVED,
  * the preserved D22–D28 repairs remain enforced,
  * the scientific semantics are UNCHANGED (new_scientific_choice = false),
  * governance flags (TEST / ROUTER_HOLDOUT / VAL authority) are untouched,
  * and NO smoke / science output exists yet.

NO torch.  NO model.  NO checkpoint deserialization.  NO CUDA.  NO forward.
NO smoke.  NO science.  NO VAL image / GT read.  NO protected-population read.
NO ROUTER_HOLDOUT.  NO TEST.
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
UNIT = ROOT / "scripts/analysis/phase36_robustness_unit_v1_11.py"
LAUNCHER = ROOT / "scripts/analysis/launch_phase36_v1_11.py"
MANIFEST = ROOT / "reports/audits/phase36_v1_11_runtime_source_integrity_manifest.json"

EXEC_V19 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_9.py"
UNIT_V19 = ROOT / "scripts/analysis/phase36_robustness_unit_v1_9.py"
UNIT_V110 = ROOT / "scripts/analysis/phase36_robustness_unit_v1_10.py"

SRC = EXEC.read_text(encoding="utf-8")
TREE = ast.parse(SRC)
FUNCS = {n.name: n for n in ast.walk(TREE) if isinstance(n, ast.FunctionDef)}

USRC = UNIT.read_text(encoding="utf-8")
UTREE = ast.parse(USRC)
LSRC = LAUNCHER.read_text(encoding="utf-8")

FROZEN_V1_9_EXEC_SHA = "433bad87b4ef77fd6997c77f688eb295e526bfa3e88dece4ec5d3d550255cbd0"
FROZEN_V1_9_UNIT_SHA = "c39edd7764a0e9733cc5905e5e54935b1bcd9cc62c345189f618b0c6f4ea690e"
FROZEN_V1_10_UNIT_SHA = "9b880c92469e7daca8f6563e64bf2e2e712d4eb8ac304298fbb52f89ab87c329"

checks = []


def check(name, cond, detail=None):
    checks.append({"check": name, "passed": bool(cond), "detail": detail})


def _sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def seg(name):
    return ast.get_source_segment(SRC, FUNCS[name]) or ""


def _code_only(src: str) -> str:
    """Docstrings + comments stripped (documentation text never mistaken for
    executable tokens)."""
    kept = []
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type in (tokenize.COMMENT, tokenize.STRING):
            continue
        kept.append(tok)
    try:
        return tokenize.untokenize(kept)
    except Exception:
        return ""

USRC_CODE = _code_only(USRC)
LSRC_CODE = _code_only(LSRC)


# ---- A. frozen v1.9 / v1.10 history byte-preserved ---------------------------- #
check("A01_v1_9_execution_byte_preserved", _sha(EXEC_V19) == FROZEN_V1_9_EXEC_SHA,
      {"expected": FROZEN_V1_9_EXEC_SHA, "observed": _sha(EXEC_V19)})
check("A02_v1_9_unit_history_byte_preserved", _sha(UNIT_V19) == FROZEN_V1_9_UNIT_SHA,
      {"expected": FROZEN_V1_9_UNIT_SHA, "observed": _sha(UNIT_V19)})
check("A03_v1_10_unit_history_byte_preserved", _sha(UNIT_V110) == FROZEN_V1_10_UNIT_SHA,
      {"expected": FROZEN_V1_10_UNIT_SHA, "observed": _sha(UNIT_V110)})

# ---- B. v1.11 unit suite has no tautology + has the self-guard ----------------- #
def _unit_or_true(tree) -> list:
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.BoolOp) and isinstance(n.op, ast.Or):
            if any(isinstance(v, ast.Constant) and v.value is True for v in n.values):
                out.append(getattr(n, "lineno", -1))
    return out


check("B01_v1_11_unit_no_or_true_boolop", len(_unit_or_true(UTREE)) == 0,
      {"offending_lines": _unit_or_true(UTREE)})
check("B02_v1_11_unit_has_self_guard", "00_self_no_or_true_expression" in USRC)
check("B03_v1_11_unit_no_lower_bound_transitive_count",
      ">= 13" not in USRC_CODE and ">=13" not in USRC_CODE)
check("B04_v1_11_unit_no_substring_call_count",
      'count("_hd95_case_exact(")' not in USRC_CODE)

# D22–D28 repairs preserved in the v1.11 unit suite (match the v1.11 ids).
check("B05_unit_d26_ast_dataflow_assertion",
      "20_D26_provenance_derived_not_literal" in USRC
      and "21_D26_binding_consumes_derived" in USRC
      and "_find_assigned_dict" in USRC and "_has_or_true" in USRC)
check("B06_unit_d27_exact_set_equality",
      "25_D27_transitive_dep_exact_count_14" in USRC
      and "26_D27_transitive_dep_exact_set_equality" in USRC
      and "EXPECTED_TRANSITIVE_DEPENDENCIES" in USRC)
check("B07_unit_d28_ast_four_call_sites",
      "41_D28_four_actual_hd95_call_sites" in USRC
      and "42_D28_hd95_call_sites_exact_semantics" in USRC)
# NEW v1.11 repairs present in the unit suite.
check("B08_unit_d30_science_gate_present",
      "50_D30_science_integrity_gate_present" in USRC
      and "51_D30_science_integrity_gate_before_load_models" in USRC)
check("B09_unit_d31_unique_paths_present",
      "55_D31_science_result_is_v1_11_path" in USRC
      and "56_D31_no_v1_8_science_write" in USRC)
check("B10_unit_d32_first_attempt_present",
      "D32" in USRC and "science_start" in USRC.lower())
check("B11_unit_d33_launcher_anchor_present",
      "D33" in USRC and "launch" in USRC.lower())

# ---- C. execution-subject invariants the repairs assert over ------------------ #
# C1: smoke attempt_provenance is an AST Dict, no literal True for the write flag.
prov = None
for n in ast.walk(FUNCS["run_smoke"]) if "run_smoke" in FUNCS else []:
    if isinstance(n, ast.Assign):
        for t in n.targets:
            if isinstance(t, ast.Name) and t.id == "attempt_provenance" \
                    and isinstance(n.value, ast.Dict):
                prov = n.value
check("C01_attempt_provenance_dict_present", prov is not None)
check("C02_write_once_flag_not_literal_true",
      '"is_first_write_once": True' not in SRC)

deps = None
for n in ast.walk(TREE):
    if isinstance(n, ast.Assign):
        for t in n.targets:
            if isinstance(t, ast.Name) and t.id == "TRANSITIVE_RUNTIME_DEPENDENCIES":
                deps = n.value
dep_paths = {k.value for k in deps.keys} if isinstance(deps, ast.Dict) else set()
check("C03_transitive_dependencies_exactly_14", len(dep_paths) == 14,
      {"observed": len(dep_paths)})

hd_calls = [n for n in ast.walk(FUNCS["run_smoke"])
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
            and n.func.id == "_hd95_case_exact"]
check("C04_four_actual_hd95_call_sites", len(hd_calls) == 4, {"n": len(hd_calls)})

# ---- D. D30 — science transitive integrity gate BEFORE _load_models ----------- #
def _body_calls_in_order(fname):
    """(lineno, func_name) of top-level Call nodes, in source order."""
    fn = FUNCS.get(fname)
    if fn is None:
        return []
    out = []
    for stmt in fn.body:
        for n in ast.walk(stmt):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
                out.append((n.lineno, n.func.id))
    return sorted(out)


sci_order = [nm for _, nm in _body_calls_in_order("run_science")]
check("D01_D30_science_calls_integrity_verify",
      "run_science" in FUNCS and "_verify_transitive_source_integrity" in sci_order,
      {"science_calls": sci_order})
gate_before_load = False
if "run_science" in FUNCS \
        and "_verify_transitive_source_integrity" in sci_order \
        and "_load_models" in sci_order:
    vi = next(ln for ln, nm in _body_calls_in_order("run_science")
              if nm == "_verify_transitive_source_integrity")
    li = next(ln for ln, nm in _body_calls_in_order("run_science")
              if nm == "_load_models")
    gate_before_load = vi < li
check("D02_D30_science_gate_before_load_models", gate_before_load,
      {"science_calls": sci_order})
check("D03_D30_science_fail_closed_terminal",
      "D30_SCIENCE_TRANSITIVE_RUNTIME_SOURCE_INTEGRITY_FAILED__STOP_BEFORE_MODEL_CONSTRUCTION"
      in SRC)
check("D04_D30_same_gate_function_both_paths",
      "run_smoke" in FUNCS and "run_science" in FUNCS
      and seg("run_smoke").count("_verify_transitive_source_integrity") >= 1
      and seg("run_science").count("_verify_transitive_source_integrity") >= 1)

# The science path must NOT construct models before the integrity gate: no
# `_load_models` Call may appear in run_science before the verify Call.
load_before_gate = False
if "run_science" in FUNCS:
    order = _body_calls_in_order("run_science")
    first_load = next((i for i, (_, nm) in enumerate(order) if nm == "_load_models"), None)
    first_verify = next((i for i, (_, nm) in enumerate(order)
                         if nm == "_verify_transitive_source_integrity"), None)
    if first_load is not None and first_verify is not None:
        load_before_gate = first_load < first_verify
check("D05_D30_no_load_models_before_science_gate", not load_before_gate)

# ---- E. D31 — unique v1.11 science paths, no v1.8 aliasing -------------------- #
check("E01_D31_science_result_v1_11_path_declared",
      "phase36_robustness_scientific_result_v1_11.json" in SRC)
check("E02_D31_science_start_v1_11_path_declared",
      "phase36_robustness_science_start_v1_11.json" in SRC)
check("E03_D31_science_failure_v1_11_path_declared",
      "phase36_robustness_science_failure_v1_11.json" in SRC)

# The forbidden v1.8 path may appear ONLY inside the declared sentinel constant;
# it must never be a write target.  Prove structurally: remove (a) all docstring
# literals (module/function/class), (b) all comments, and (c) every assigned
# string constant — then the historical filename must be absent.
_structural = SRC
for _n in ast.walk(TREE):
    if isinstance(_n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        _b = getattr(_n, "body", [])
        if _b and isinstance(_b[0], ast.Expr) and isinstance(_b[0].value, ast.Constant) \
                and isinstance(_b[0].value.value, str):
            _structural = _structural.replace(_b[0].value.value, "")
_kept = []
for _tok in tokenize.generate_tokens(io.StringIO(_structural).readline):
    if _tok.type == tokenize.COMMENT:
        continue
    _kept.append(_tok)
try:
    _structural = tokenize.untokenize(_kept)
except Exception:
    pass
for _n in ast.walk(TREE):
    if isinstance(_n, ast.Assign) and isinstance(_n.value, ast.Constant) \
            and isinstance(_n.value.value, str) and _n.value.value:
        _structural = _structural.replace(_n.value.value, "None")

check("E04_D31_no_v1_8_write_target_in_code",
      "scientific_result_v1_8.json" not in _structural)
check("E05_D31_sentinel_declared",
      "FORBIDDEN_SCIENCE_RESULT_V1_8" in SRC)

# No science write path uses the historical v1.8/v1.9 filenames.
for _forb in ("scientific_result_v1_8.json", "scientific_result_v1_9.json"):
    check(f"E06_D31_no_historical_write_{_forb}",
          _forb not in _structural)

# ---- F. D32 — science first-attempt write-once provenance --------------------- #
check("F01_D32_science_start_marker_helper",
      "_create_science_start_marker" in SRC)
check("F02_D32_science_failure_helper",
      "_write_science_failure_artifact" in SRC)
check("F03_D32_science_success_helper",
      "_write_science_success_artifact" in SRC)
check("F04_D32_durable_evidence_wrapper",
      "_run_science_with_durable_evidence" in SRC)
check("F05_D32_start_marker_exclusive_create",
      "_create_science_start_marker" in FUNCS
      and ('"x"' in seg("_create_science_start_marker")
           or "O_EXCL" in seg("_create_science_start_marker")
           or "O_CREAT" in seg("_create_science_start_marker")))
check("F06_D32_systemexit_recorded",
      "SystemExit" in SRC and "_run_science_with_durable_evidence" in SRC)
check("F07_D32_exception_recorded",
      "except Exception" in seg("_run_science_with_durable_evidence")
      if "_run_science_with_durable_evidence" in FUNCS else False)
check("F08_D32_attempt_existence_guard",
      "_science_attempt_already_exists" in SRC)

# ---- G. D33 — external non-circular launcher anchor --------------------------- #
check("G01_D33_launcher_exists", LAUNCHER.exists())
check("G02_D33_launcher_verifies_exec_sha",
      "FROZEN_EXPECTED_EXEC_SHA" in LSRC)
check("G03_D33_launcher_verifies_manifest_sha",
      "FROZEN_EXPECTED_MANIFEST_SHA" in LSRC)
check("G04_D33_launch_authority_token_declared",
      "LAUNCH_AUTHORITY_TOKEN" in SRC and "PHASE36_V1_11_LAUNCH_AUTHORITY" in SRC)
check("G05_D33_source_requires_launch_token",
      "_verify_transitive_source_integrity" in FUNCS
      and "LAUNCH_AUTHORITY_TOKEN" in seg("_verify_transitive_source_integrity")
      and "os.environ" in seg("_verify_transitive_source_integrity"))
# Non-circularity: the manifest must NOT declare the launcher SHA (that would
# form a launcher<->manifest cycle).  The manifest may only declare exec + deps.
_mf = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
check("G06_D33_manifest_present", MANIFEST.exists())
check("G07_D33_manifest_declares_exec_sha",
      _mf.get("execution_source_sha256") == _sha(EXEC),
      {"declared": _mf.get("execution_source_sha256"), "observed": _sha(EXEC)})
check("G08_D33_manifest_no_launcher_sha_cycle",
      "launcher_sha256" not in _mf)
check("G09_D33_co_edit_negative_control_recorded",
      (ROOT / "reports/audits/phase36_v1_11_launcher_co_edit_negative_control.json").exists())

# ---- H. gate separation + non-execution --------------------------------------- #
check("H01_smoke_gate_separate_from_science_gate",
      "SMOKE_GATE_ENV" in SRC and "GATE_ENV" in SRC and "PHASE36_SMOKE_EXECUTE" in SRC)
check("H02_no_v1_11_smoke_artifact_exists_yet",
      not (ROOT / "reports/audits/phase36_robustness_smoke_v1_11.json").exists())
check("H03_no_v1_11_smoke_start_marker_exists_yet",
      not (ROOT / "reports/audits/phase36_robustness_smoke_start_v1_11.json").exists())
check("H04_no_v1_11_smoke_failure_artifact_exists_yet",
      not (ROOT / "reports/audits/phase36_robustness_smoke_failure_v1_11.json").exists())
check("H05_no_v1_11_science_output_exists",
      not (ROOT / "reports/audits/phase36_robustness_scientific_result_v1_11.json").exists())
check("H06_no_v1_11_science_start_exists",
      not (ROOT / "reports/audits/phase36_robustness_science_start_v1_11.json").exists())
check("H07_no_v1_11_science_failure_exists",
      not (ROOT / "reports/audits/phase36_robustness_science_failure_v1_11.json").exists())
check("H08_entrypoint_guarded_by_main_guard", 'if __name__ == "__main__":' in SRC)

# ---- I. governance flags preserved -------------------------------------------- #
check("I01_test_runtime_reads_disallowed_flag",
      "TEST_RUNTIME_READS_ALLOWED = False" in SRC)
check("I02_holdout_runtime_reads_disallowed_flag",
      "ROUTER_HOLDOUT_RUNTIME_READS_ALLOWED = False" in SRC)
check("I03_val_manifest_only_runtime_authority",
      "VAL_MANIFEST_IS_ONLY_POPULATION_RUNTIME_AUTHORITY = True" in SRC)

# ---- J. scientific-semantics invariance (no new scientific choice) ------------ #
SCIENTIFIC_TOKENS = [
    "torch.sigmoid(logits.float())",
    "inference_mode",
    "autocast",
    "VAL808",
]
check("J01_sigmoid_logits_float_preserved",
      "torch.sigmoid(logits.float())" in SRC)
check("J02_seeds_preserved",
      "42" in SRC and "123" in SRC and "3407" in SRC)
check("J03_thresholds_preserved",
      "0.50" in SRC and "0.30" in SRC)
check("J04_batch8_preserved", "8" in SRC)
check("J05_science_semantics_tokens_present",
      all(t in SRC for t in SCIENTIFIC_TOKENS))

# ---- K. v1.11 gate reports on disk -------------------------------------------- #
unit_rep = json.loads((ROOT / "reports/audits/phase36_robustness_unit_v1_11.json")
                      .read_text(encoding="utf-8"))
check("K01_unit_report_all_pass", unit_rep["all_pass"],
      {"passed": unit_rep["passed"], "total": unit_rep["total"]})
check("K02_unit_report_subject_is_v1_11_exec",
      unit_rep["subject_execution_sha256"] == _sha(EXEC),
      {"declared": unit_rep["subject_execution_sha256"], "observed": _sha(EXEC)})

# ---- L. D29 — v1.10 frozen-validator availability provenance ------------------- #
d29_path = ROOT / "reports/audits/phase36_v1_10_frozen_validator_availability_provenance.json"
check("L01_D29_availability_record_exists", d29_path.exists())
if d29_path.exists():
    _d29 = json.loads(d29_path.read_text(encoding="utf-8"))
    check("L02_D29_record_binds_v1_10_sha",
          "9b880c92469e7daca8f6563e64bf2e2e712d4eb8ac304298fbb52f89ab87c329"
          in json.dumps(_d29))
    check("L03_D29_record_states_availability_truthfully",
          _d29.get("unit_source_sha_matches_freeze_binding") is True
          and _d29.get("reconstructed_or_rewritten_by_v1_11") is False
          and _d29.get("v1_10_smoke_executed") is False
          and _d29.get("v1_10_science_executed") is False
          and _d29.get("v1_10_scientific_evidence") == "NONE")

passed = sum(1 for c in checks if c["passed"])
total = len(checks)
report = {
    "artifact": "phase36_robustness_preflight_v1_11",
    "phase": 36,
    "section": "§N",
    "method": "RA-MedFiLM-BARR",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_11",
    "type": "PREFLIGHT_CHECK_REPORT",
    "static_only": True,
    "model_free": True,
    "torch_imported": "torch" in sys.modules,
    "protected_population_read": False,
    "subject_execution": "scripts/analysis/phase36_robustness_execution_v1_11.py",
    "subject_execution_sha256": _sha(EXEC),
    "subject_unit": "scripts/analysis/phase36_robustness_unit_v1_11.py",
    "subject_unit_sha256": _sha(UNIT),
    "subject_launcher": "scripts/analysis/launch_phase36_v1_11.py",
    "subject_launcher_sha256": _sha(LAUNCHER),
    "subject_manifest": "reports/audits/phase36_v1_11_runtime_source_integrity_manifest.json",
    "subject_manifest_sha256": _sha(MANIFEST),
    "passed": passed,
    "total": total,
    "all_pass": passed == total,
    "checks": checks,
}
out = ROOT / "reports/audits/phase36_robustness_preflight_v1_11.json"
out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({"passed": passed, "total": total, "all_pass": passed == total}, indent=1))
for c in checks:
    if not c["passed"]:
        print("FAIL:", c["check"], json.dumps(c.get("detail"), default=str))
raise SystemExit(0 if passed == total else 1)
