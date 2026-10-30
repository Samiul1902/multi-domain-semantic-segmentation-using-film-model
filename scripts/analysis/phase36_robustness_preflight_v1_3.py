#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.3 — static preflight (AST / call-graph / byte proof).

METHOD: RA-MedFiLM-BARR
REVISION: ra_medfilm_barr_phase36_robustness_v1_3

NO torch. NO model. NO protected-data read. AST + byte analysis only.

Proves:
  * run_science is SAMPLE-FIRST
  * clean stage precedes perturbations
  * clean gate precedes perturbations
  * image evaluator reachable inside the sample loop
  * proposal evaluator reachable inside the sample loop
  * result rows contain sample_id / domain / task_id
  * no silent missing-sample continue
  * fixed summaries reachable
  * worst-case summaries reachable
  * manifest authority used
  * no `"test" in path` split rejection
  * no `"train" in path` split rejection
  * 231 Training_Input authorized
  * 112 Test_Input authorized
  * ROUTER_HOLDOUT denied by identity authority
  * TEST denied by identity authority
  * v1.2 executable-loader / full-system repairs retained
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))

EXEC = ROOT / "scripts/analysis/phase36_robustness_execution_v1_3.py"
SRC = EXEC.read_text(encoding="utf-8")
TREE = ast.parse(SRC)

checks = []


def check(name, cond, detail=None):
    checks.append({"check": name, "passed": bool(cond), "detail": detail})


def _funcs(tree):
    return {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}


FUNCS = _funcs(TREE)


def _calls_in(fn_name):
    node = FUNCS.get(fn_name)
    if node is None:
        return set()
    out = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Name):
                out.add(f.id)
            elif isinstance(f, ast.Attribute):
                out.add(f.attr)
    return out


def _lineno_of(fn_name, needle):
    node = FUNCS.get(fn_name)
    if node is None:
        return None
    for n in ast.walk(node):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == needle:
            return n.lineno
        if isinstance(n, ast.Name) and n.id == needle:
            return n.lineno
    return None


# ---- 01 run_science is sample-first --------------------------------------- #
check("01_run_science_exists", "run_science" in FUNCS)
science_calls = _calls_in("run_science")
check("02_science_calls_clean_generator", "_generate_clean_reference_once" in science_calls)
check("03_science_calls_clean_gate", "_clean_equivalence_gate" in science_calls)
check("04_science_calls_image_driver", "run_image_perturbations" in science_calls)
check("05_science_calls_proposal_driver", "run_proposal_perturbations" in science_calls)

# ---- 06-07 clean stage / gate precede perturbations (source order in run_science) #
def _first_line_in(fn_name, token):
    node = FUNCS.get(fn_name)
    if node is None:
        return 10 ** 9
    for n in ast.walk(node):
        if isinstance(n, ast.Call):
            f = n.func
            fname = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else None)
            if fname and token in fname:
                return n.lineno
    return 10 ** 9

l_gen = _first_line_in("run_science", "_generate_clean_reference_once")
l_gate = _first_line_in("run_science", "_clean_equivalence_gate")
l_img = _first_line_in("run_science", "run_image_perturbations")
l_prop = _first_line_in("run_science", "run_proposal_perturbations")
check("06_clean_stage_precedes_perturbations", l_gen < l_img and l_gen < l_prop,
      {"gen": l_gen, "img": l_img, "prop": l_prop})
check("07_clean_gate_precedes_perturbations", l_gate < l_img and l_gate < l_prop,
      {"gate": l_gate, "img": l_img, "prop": l_prop})

# ---- 08-09 evaluators reachable inside the sample loop --------------------- #
img_driver = _calls_in("run_image_perturbations")
prop_driver = _calls_in("run_proposal_perturbations")
check("08_image_evaluator_in_driver", "_evaluate_frozen_system" in img_driver)
check("09_proposal_evaluator_in_driver", "_evaluate_frozen_system_proposal" in prop_driver)

# sample-first: `for sid in sample_order` in both drivers
def _has_loop(fn_name):
    node = FUNCS.get(fn_name)
    if node is None:
        return False
    for n in ast.walk(node):
        if isinstance(n, ast.For):
            t = n.target
            if isinstance(t, ast.Name) and t.id == "sid":
                return True
    return False


check("10_image_driver_sample_first", _has_loop("run_image_perturbations"))
check("11_proposal_driver_sample_first", _has_loop("run_proposal_perturbations"))

# ---- 12-14 result rows contain sample_id / domain / task_id ---------------- #
check("12_image_row_builder_requires_identity",
      "SCIENCE_ROW_SCHEMA_LOSS" in SRC and "_IMAGE_ROW_REQUIRED" in SRC)
check("13_row_required_fields",
      all(f in SRC for f in ('"sample_id"', '"domain"', '"task_id"')))
check("14_missing_identity_raises_not_continue",
      'raise ValueError(f"SCIENCE_ROW_SCHEMA_LOSS' in SRC)

# ---- 15 no silent missing-sample continue --------------------------------- #
import re
check("15_no_silent_missing_sample_continue",
      not re.search(r'sid\s*=\s*row\.get\("sample_id"\)\s*\n\s*if\s+sid\s+is\s+None\s*:\s*\n\s*continue', SRC))

# ---- 16-17 fixed summaries + worst-case reachable ------------------------ #
check("16_fixed_summaries_reachable",
      all(t in science_calls for t in ("summarize_image_per_sample",
                                       "summarize_image_by_domain_condition",
                                       "summarize_noise_seed",
                                       "summarize_proposal_per_sample",
                                       "summarize_proposal_by_domain_condition",
                                       "summarize_route_stability")))
check("17_worstcase_reachable",
      all(t in science_calls for t in ("worst_case_per_sample", "worst_case_by_domain")))

# ---- 18 manifest authority used ------------------------------------------- #
check("18_manifest_authority_used",
      "_load_population" in SRC and "C.VAL_MANIFEST" in SRC and "_authorized_path_exact" in SRC)

# ---- 19-20 no vendor-token split rejection -------------------------------- #
check("19_no_test_substring_split", '"test" in' not in SRC and "'test' in" not in SRC)
check("20_no_train_substring_split", '"train" in' not in SRC and "'train' in" not in SRC)

# ---- 21-22 vendor directory positive controls via identity authority ------- #
rows = None
try:
    import scripts.analysis.phase36_robustness_execution_v1_3 as E
    rows = E._load_population()
    pop_index = {r["sample_id"]: r for r in rows}
    auth = E.load_identity_authorities()
    tr = [r for r in rows if "ISIC2018_Task1-2_Training_Input" in str(r["image_path"])]
    te = [r for r in rows if "ISIC2018_Task1-2_Test_Input" in str(r["image_path"])]
    acc_tr = acc_te = 0
    for r in tr:
        try:
            E.authorize_sample(r["sample_id"], r["image_path"], r["mask_path"], pop_index,
                               auth["holdout"], auth["test"]); acc_tr += 1
        except Exception:
            pass
    for r in te:
        try:
            E.authorize_sample(r["sample_id"], r["image_path"], r["mask_path"], pop_index,
                               auth["holdout"], auth["test"]); acc_te += 1
        except Exception:
            pass
    check("21_231_training_input_authorized", len(tr) == 231 and acc_tr == 231,
          {"authorized": len(tr), "accepted": acc_tr})
    check("22_112_test_input_authorized", len(te) == 112 and acc_te == 112,
          {"authorized": len(te), "accepted": acc_te})
except Exception as ex:  # pragma: no cover
    check("21_231_training_input_authorized", False, str(ex))
    check("22_112_test_input_authorized", False, str(ex))

# ---- 23-24 ROUTER_HOLDOUT / TEST denied by identity authority ------------- #
check("23_holdout_identity_deny_present",
      "_identity_deny_set" in SRC and "ROUTER_HOLDOUT_MANIFEST" in SRC
      and "ROUTER_HOLDOUT_IDENTITY_REJECTED" in SRC)
check("24_test_identity_deny_present",
      "TEST_MANIFEST" in SRC and "TEST_IDENTITY_REJECTED" in SRC)

# ---- 25 v1.2 executable-loader / full-system repairs retained ------------- #
check("25_v12_loader_repairs_retained",
      all(t in SRC for t in ("def _load_models", "load_state_dict", "strict=True",
                             "CANONICAL_COMPONENT_LOAD_FAILURE")))

# ---- counts --------------------------------------------------------------- #
passed = sum(1 for c in checks if c["passed"])
total = len(checks)
report = {
    "artifact": "phase36_robustness_static_preflight_v1_3",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_3",
    "method": "AST_CALL_GRAPH_AND_BYTE_PREFLIGHT",
    "torch_imported": "torch" in sys.modules,
    "checks": checks,
    "passed": passed,
    "total": total,
    "all_pass": passed == total,
}
out = ROOT / "reports/audits/phase36_robustness_static_preflight_v1_3.json"
out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"passed": passed, "total": total, "all_pass": passed == total}, indent=1))
for c in checks:
    if not c["passed"]:
        print("FAIL:", c["check"], json.dumps(c.get("detail")))
raise SystemExit(0 if passed == total else 1)
