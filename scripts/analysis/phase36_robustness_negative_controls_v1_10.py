#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.10 — NEGATIVE CONTROLS NC63..NC70 (additive over v1.9 NC50..NC57).

These controls target the SPECIFIC v1.10 validation-gate repairs (D26/D27/D28).
The defect class here is DEFECTIVE-UNIT-ASSERTION, so each detector below is a
faithful standalone re-implementation of the corresponding repaired v1.10 unit
assertion, and each mutator perturbs the FROZEN v1.9 EXECUTION source in memory
so that a CORRECT detector MUST notice.

IN-MEMORY SOURCE MUTANTS ONLY.  Canonical files on disk are NEVER modified.
NO torch.  NO model.  NO checkpoint.  NO CUDA.  NO forward.  NO smoke.  NO science.
NO VAL image / GT read.  NO protected-population read.  NO ROUTER_HOLDOUT.  NO TEST.
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
CANONICAL_SRC = EXEC.read_text(encoding="utf-8")
CANONICAL_SHA = hashlib.sha256(EXEC.read_bytes()).hexdigest()


# --------------------------------------------------------------------------- #
# shared AST helpers (mirror the v1.10 unit suite)
# --------------------------------------------------------------------------- #
def _tree(src):
    return ast.parse(src)


def _funcs(tree):
    return {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}


def _is_literal_true(node) -> bool:
    return isinstance(node, ast.Constant) and node.value is True


def _is_literal_false(node) -> bool:
    return isinstance(node, ast.Constant) and node.value is False


def _collect_names(node) -> set:
    if node is None:
        return set()
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}


def _has_or_true(node) -> bool:
    if node is None:
        return False
    for n in ast.walk(node):
        if isinstance(n, ast.BoolOp) and isinstance(n.op, ast.Or):
            if any(_is_literal_true(x) for x in n.values):
                return True
    return False


def _find_assigned_dict(tree, func_name, var_name):
    f = _funcs(tree).get(func_name)
    if f is None:
        return None
    for n in ast.walk(f):
        if isinstance(n, (ast.Assign, ast.AnnAssign)):
            targets = n.targets if isinstance(n, ast.Assign) else [n.target]
            for t in targets:
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


def _assigned_module_dict(tree, var_name):
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name) and t.id == var_name \
                        and isinstance(n.value, ast.Dict):
                    return n.value
    return None


# --------------------------------------------------------------------------- #
# D26 detector — provenance is DERIVED, not literal / or-True / unconditional.
# --------------------------------------------------------------------------- #
def det_d26_provenance_derived(src: str) -> bool:
    t = _tree(src)
    f = _funcs(t)
    if "run_smoke" not in f:
        return False
    prov = _find_assigned_dict(t, "run_smoke", "attempt_provenance")
    if prov is None:
        return False
    val_node = _dict_key_node(prov, "is_first_write_once")
    if val_node is None:
        return False
    key_names = _collect_names(val_node)
    needs = {"_marker_exists", "_marker_sole_and_trueseal"}
    not_literal_true = not _is_literal_true(val_node)
    no_or_true = not _has_or_true(val_node)
    combines = bool(needs <= key_names)
    scope_names = {n.id for n in ast.walk(f["run_smoke"]) if isinstance(n, ast.Name)}
    has_marker_exists = "_marker_exists" in scope_names
    has_trueseal = "_marker_sole_and_trueseal" in scope_names
    # (f) probe sets the trueseal flag True inside a FileExistsError handler
    probe_ok = False
    for n in ast.walk(f["run_smoke"]):
        if isinstance(n, ast.Try):
            for h in n.handlers:
                exc = h.type
                nm = getattr(exc, "id", None) or getattr(exc, "attr", None)
                if nm == "FileExistsError":
                    for x in ast.walk(h):
                        if isinstance(x, ast.Assign):
                            for tg in x.targets:
                                if isinstance(tg, ast.Name) \
                                        and tg.id == "_marker_sole_and_trueseal" \
                                        and _is_literal_true(x.value):
                                    probe_ok = True
    # (g) exclusive-create `open(..., "x")` present in the try
    exclusive_call_ok = False
    for n in ast.walk(f["run_smoke"]):
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
    return (not_literal_true and no_or_true and combines and has_marker_exists
            and has_trueseal and probe_ok and exclusive_call_ok)


# --------------------------------------------------------------------------- #
# D27 detector — transitive dependency set is EXACTLY the frozen 14 paths.
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


def det_d27_exact_dep_set(src: str) -> bool:
    t = _tree(src)
    d = _assigned_module_dict(t, "TRANSITIVE_RUNTIME_DEPENDENCIES")
    if d is None:
        return False
    observed = {k.value for k in d.keys if isinstance(k, ast.Constant)}
    return (len(observed) == 14
            and observed == EXPECTED_TRANSITIVE_DEPENDENCIES
            and len(EXPECTED_TRANSITIVE_DEPENDENCIES - observed) == 0
            and len(observed - EXPECTED_TRANSITIVE_DEPENDENCIES) == 0)


# --------------------------------------------------------------------------- #
# D28 detector — four ACTUAL hd95 call sites with exact frozen semantics.
# --------------------------------------------------------------------------- #
EXPECTED_HD95_CALLS = {
    ("nonempty_nonempty", True, ""),
    ("empty_prediction_nonempty_gt", False, "empty_prediction"),
    ("nonempty_prediction_empty_gt", False, "empty_ground_truth"),
    ("empty_empty", False, "both_empty"),
}


def _call_expectation(call: ast.Call):
    case_ref = None
    if call.args:
        a0 = call.args[0]
        if isinstance(a0, ast.Subscript) and isinstance(a0.slice, ast.Constant):
            case_ref = a0.slice.value
    ev = None
    er = None
    for kw in call.keywords:
        if kw.arg == "expect_valid" and isinstance(kw.value, ast.Constant):
            ev = kw.value.value
        if kw.arg == "expect_reason" and isinstance(kw.value, ast.Constant):
            er = kw.value.value
    return case_ref, ev, er


def det_d28_four_call_sites(src: str) -> bool:
    t = _tree(src)
    f = _funcs(t)
    if "run_smoke" not in f or "_hd95_case_exact" not in f:
        return False
    calls = [n for n in ast.walk(f["run_smoke"])
             if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
             and n.func.id == "_hd95_case_exact"]
    if len(calls) != 4:
        return False
    observed = {_call_expectation(c) for c in calls}
    return observed == EXPECTED_HD95_CALLS


# --------------------------------------------------------------------------- #
# Mutators (in-memory string surgery only)
# --------------------------------------------------------------------------- #
def mut_d26_hardcode_true(src: str) -> str:
    """D26 mutant: replace the DERIVED value with a bare literal True."""
    return src.replace(
        '"is_first_write_once": bool(_marker_exists and _marker_sole_and_trueseal),',
        '"is_first_write_once": True,', 1)


def mut_d26_or_true(src: str) -> str:
    """D26 mutant: make the value an `... or True` tautology."""
    return src.replace(
        '"is_first_write_once": bool(_marker_exists and _marker_sole_and_trueseal),',
        '"is_first_write_once": bool(_marker_exists and _marker_sole_and_trueseal) or True,', 1)


def mut_d26_drop_probe(src: str) -> str:
    """D26 mutant: sever one provenance input (drop _marker_sole_and_trueseal)."""
    return src.replace(
        '"is_first_write_once": bool(_marker_exists and _marker_sole_and_trueseal),',
        '"is_first_write_once": bool(_marker_exists),', 1)


def mut_d26_drop_exclusive_open(src: str) -> str:
    """D26 mutant: remove the exclusive `open(..., "x")` probe call entirely."""
    return src.replace(
        'with open(start_marker_path, "x", encoding="utf-8"):',
        'with open(start_marker_path, "w", encoding="utf-8"):', 1)


def mut_d27_drop_one_dep(src: str) -> str:
    """D27 mutant: remove one legitimate frozen dependency path (count -> 13)."""
    return src.replace(
        '    "src/utils/device.py":', '    "src/utils/device_PLACEHOLDER.py":', 1)


def mut_d27_replace_dep(src: str) -> str:
    """D27 mutant: substitute an unexpected replacement path (set no longer equal)."""
    return src.replace(
        '    "reports/tables/phase25f_final_normalization_stats.csv":',
        '    "reports/tables/phase25f_final_normalization_stats_UNEXPECTED.csv":', 1)


def mut_d28_drop_call(src: str) -> str:
    """D28 mutant: drop one of the four hd95 call sites (-> 3)."""
    return src.replace(
        '"empty_empty": _hd95_case_exact(',
        '"empty_empty": (lambda c: True)(', 1)


def mut_d28_weaken_reason(src: str) -> str:
    """D28 mutant: weaken a call-site reason binding to a wrong value."""
    return src.replace(
        'expect_reason="empty_ground_truth"),',
        'expect_reason="empty_prediction"),', 1)


CONTROLS = [
    ("NC63_D26_provenance_hardcoded_literal_true",
     mut_d26_hardcode_true, det_d26_provenance_derived),
    ("NC64_D26_provenance_or_true_tautology",
     mut_d26_or_true, det_d26_provenance_derived),
    ("NC65_D26_provenance_missing_one_input_signal",
     mut_d26_drop_probe, det_d26_provenance_derived),
    ("NC66_D26_exclusive_create_open_x_removed",
     mut_d26_drop_exclusive_open, det_d26_provenance_derived),
    ("NC67_D27_transitive_dep_path_dropped",
     mut_d27_drop_one_dep, det_d27_exact_dep_set),
    ("NC68_D27_transitive_dep_path_replaced",
     mut_d27_replace_dep, det_d27_exact_dep_set),
    ("NC69_D28_hd95_call_site_dropped",
     mut_d28_drop_call, det_d28_four_call_sites),
    ("NC70_D28_hd95_call_site_reason_weakened",
     mut_d28_weaken_reason, det_d28_four_call_sites),
]

results = []
for name, mutator, detector in CONTROLS:
    mutated = mutator(CANONICAL_SRC)
    changed = mutated != CANONICAL_SRC
    baseline_ok = detector(CANONICAL_SRC)
    try:
        mutated_ok = detector(mutated)
    except Exception:
        mutated_ok = False
    bites = baseline_ok and (not mutated_ok)
    results.append({
        "nc": name,
        "mutation_changed_bytes": bool(changed),
        "detector_on_canonical": bool(baseline_ok),
        "detector_on_mutant": bool(mutated_ok),
        "mutant_bite": bool(bites),
        "pass": bool(changed and baseline_ok and not mutated_ok),
    })

passed = sum(1 for r in results if r["pass"])
total = len(results)
sha_after = hashlib.sha256(EXEC.read_bytes()).hexdigest()

report = {
    "artifact": "phase36_v1_10_negative_controls",
    "phase": 36,
    "section": "§K",
    "method": "RA-MedFiLM-BARR",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_10",
    "type": "NEGATIVE_CONTROL_AUDIT",
    "model_free": True,
    "torch_imported": "torch" in sys.modules,
    "protected_population_read": False,
    "mutants_are_in_memory_strings_only": True,
    "canonical_source_sha256_before": CANONICAL_SHA,
    "canonical_source_sha256_after": sha_after,
    "canonical_source_unmodified": bool(CANONICAL_SHA == sha_after),
    "nc_range": "NC63-NC70",
    "targets": "D26/D27/D28_unit_gate_repairs",
    "carried_over_v1_9": "NC50-NC57_remain_valid_in_phase36_v1_9_negative_controls.json",
    "passed": passed,
    "total": total,
    "all_pass": passed == total,
    "controls": results,
}
out = ROOT / "reports/audits/phase36_v1_10_negative_controls.json"
out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({"passed": passed, "total": total, "all_pass": passed == total,
                  "canonical_unmodified": CANONICAL_SHA == sha_after}, indent=1))
for r in results:
    print(("PASS " if r["pass"] else "FAIL "), r["nc"],
          "| canonical_detector=", r["detector_on_canonical"],
          "| mutant_bite=", r["mutant_bite"])
raise SystemExit(0 if passed == total else 1)
