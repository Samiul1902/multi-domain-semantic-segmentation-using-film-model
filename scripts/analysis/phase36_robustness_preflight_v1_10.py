#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.10 — PREFLIGHT (source / AST / static only).

Validates the v1.10 validation-gate repair (D26 / D27 / D28) as a STATIC
property of the frozen v1.9 execution subject + the repaired v1.10 unit suite.
It additionally re-asserts the v1.9 governance invariants that must remain
untouched (protected-population flags, gate separation, no execution).

NO torch.  NO model.  NO checkpoint deserialization.  NO CUDA.  NO forward.
NO smoke.  NO science.  NO VAL image / GT read.  NO protected-population read.
"""
from __future__ import annotations

import ast
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

EXEC = ROOT / "scripts/analysis/phase36_robustness_execution_v1_9.py"
UNIT_V110 = ROOT / "scripts/analysis/phase36_robustness_unit_v1_10.py"
UNIT_V19 = ROOT / "scripts/analysis/phase36_robustness_unit_v1_9.py"

SRC = EXEC.read_text(encoding="utf-8")
TREE = ast.parse(SRC)
FUNCS = {n.name: n for n in ast.walk(TREE) if isinstance(n, ast.FunctionDef)}

U110 = UNIT_V110.read_text(encoding="utf-8")
U_TREE = ast.parse(U110)

FROZEN_V1_9_EXEC_SHA = "433bad87b4ef77fd6997c77f688eb295e526bfa3e88dece4ec5d3d550255cbd0"
FROZEN_V1_9_UNIT_SHA = "c39edd7764a0e9733cc5905e5e54935b1bcd9cc62c345189f618b0c6f4ea690e"

checks = []


def check(name, cond, detail=None):
    checks.append({"check": name, "passed": bool(cond), "detail": detail})


def _sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def seg(name):
    return ast.get_source_segment(SRC, FUNCS[name]) or ""


# ---- A. byte-preservation of the frozen v1.9 execution + unit history --------- #
check("A01_v1_9_execution_byte_preserved", _sha(EXEC) == FROZEN_V1_9_EXEC_SHA,
      {"expected": FROZEN_V1_9_EXEC_SHA, "observed": _sha(EXEC)})
check("A02_v1_9_unit_history_byte_preserved", _sha(UNIT_V19) == FROZEN_V1_9_UNIT_SHA,
      {"expected": FROZEN_V1_9_UNIT_SHA, "observed": _sha(UNIT_V19)})

# ---- B. v1.10 unit suite has no tautology of any kind ------------------------- #
def _unit_or_true(tree) -> list:
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.BoolOp) and isinstance(n.op, ast.Or):
            if any(isinstance(v, ast.Constant) and v.value is True for v in n.values):
                out.append(getattr(n, "lineno", -1))
    return out


check("B01_v1_10_unit_no_or_true_boolop", len(_unit_or_true(U_TREE)) == 0,
      {"offending_lines": _unit_or_true(U_TREE)})
check("B02_v1_10_unit_has_self_guard",
      "00_self_no_or_true_expression" in U110)


def _unit_code_only(src: str) -> str:
    """Strip docstrings + comments so D27/D28 defect-DOCUMENTATION text (which
    necessarily quotes `>= 13` and `SRC.count(...)`) is not mistaken for an
    executable lower-bound / substring-count assertion."""
    import io
    import tokenize
    kept = []
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type in (tokenize.COMMENT, tokenize.STRING):
            continue
        kept.append(tok)
    try:
        return tokenize.untokenize(kept)
    except Exception:
        return ""


U110_CODE = _unit_code_only(U110)
check("B03_v1_10_unit_no_lower_bound_transitive_count",
      ">= 13" not in U110_CODE and ">=13" not in U110_CODE)
check("B04_v1_10_unit_no_substring_call_count",
      'count("_hd95_case_exact(")' not in U110_CODE)

# D26/D27/D28 repairs present in the unit suite.
check("B05_unit_d26_ast_dataflow_assertion",
      "15_run_smoke_provenance_is_derived_not_literal" in U110
      and "_find_assigned_dict" in U110
      and "_has_or_true" in U110)
check("B06_unit_d27_exact_set_equality",
      "28b_transitive_dep_exact_set_equality" in U110
      and "EXPECTED_TRANSITIVE_DEPENDENCIES" in U110)
check("B07_unit_d28_ast_four_call_sites",
      "41_hd95_four_actual_call_sites" in U110
      and "42_hd95_call_sites_exact_semantics" in U110)

# ---- C. execution-subject invariants the repairs assert over ------------------ #
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

# ---- D. gate separation + non-execution --------------------------------------- #
check("D01_smoke_gate_separate_from_science_gate",
      "SMOKE_GATE_ENV" in SRC and "GATE_ENV" in SRC and "PHASE36_SMOKE_EXECUTE" in SRC)
check("D02_no_v1_9_smoke_artifact_exists_yet",
      not (ROOT / "reports/audits/phase36_robustness_smoke_v1_9.json").exists())
check("D03_no_v1_9_start_marker_exists_yet",
      not (ROOT / "reports/audits/phase36_robustness_smoke_start_v1_9.json").exists())
check("D04_no_v1_9_failure_artifact_exists_yet",
      not (ROOT / "reports/audits/phase36_robustness_smoke_failure_v1_9.json").exists())
check("D05_no_v1_9_science_output_exists",
      not (ROOT / "reports/audits/phase36_robustness_scientific_result_v1_9.json").exists())
check("D06_no_v1_10_smoke_or_science_output_exists",
      not (ROOT / "reports/audits/phase36_robustness_smoke_v1_10.json").exists()
      and not (ROOT / "reports/audits/phase36_robustness_scientific_result_v1_10.json").exists())
check("D07_entrypoint_guarded_by_main_guard", 'if __name__ == "__main__":' in SRC)

# ---- E. governance flags preserved -------------------------------------------- #
check("E01_test_runtime_reads_disallowed_flag",
      "TEST_RUNTIME_READS_ALLOWED = False" in SRC)
check("E02_holdout_runtime_reads_disallowed_flag",
      "ROUTER_HOLDOUT_RUNTIME_READS_ALLOWED = False" in SRC)
check("E03_val_manifest_only_runtime_authority",
      "VAL_MANIFEST_IS_ONLY_POPULATION_RUNTIME_AUTHORITY = True" in SRC)

# ---- F. v1.10 gate artifacts on disk ------------------------------------------ #
unit_rep = json.loads((ROOT / "reports/audits/phase36_robustness_unit_v1_10.json")
                      .read_text(encoding="utf-8"))
nc_rep = json.loads((ROOT / "reports/audits/phase36_v1_10_negative_controls.json")
                    .read_text(encoding="utf-8"))
check("F01_unit_report_all_pass", unit_rep["all_pass"],
      {"passed": unit_rep["passed"], "total": unit_rep["total"]})
check("F02_negative_controls_all_pass", nc_rep["all_pass"],
      {"passed": nc_rep["passed"], "total": nc_rep["total"]})
check("F03_unit_report_subject_is_v1_9_exec",
      unit_rep["subject_execution_sha256"] == FROZEN_V1_9_EXEC_SHA)

passed = sum(1 for c in checks if c["passed"])
total = len(checks)
report = {
    "artifact": "phase36_robustness_preflight_v1_10",
    "phase": 36,
    "section": "§N",
    "method": "RA-MedFiLM-BARR",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_10",
    "type": "PREFLIGHT_CHECK_REPORT",
    "static_only": True,
    "model_free": True,
    "torch_imported": "torch" in sys.modules,
    "protected_population_read": False,
    "subject_execution": "scripts/analysis/phase36_robustness_execution_v1_9.py",
    "subject_execution_sha256": _sha(EXEC),
    "subject_unit": "scripts/analysis/phase36_robustness_unit_v1_10.py",
    "subject_unit_sha256": _sha(UNIT_V110),
    "passed": passed,
    "total": total,
    "all_pass": passed == total,
    "checks": checks,
}
out = ROOT / "reports/audits/phase36_robustness_preflight_v1_10.json"
out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({"passed": passed, "total": total, "all_pass": passed == total}, indent=1))
for c in checks:
    if not c["passed"]:
        print("FAIL:", c["check"], json.dumps(c.get("detail"), default=str))
raise SystemExit(0 if passed == total else 1)
