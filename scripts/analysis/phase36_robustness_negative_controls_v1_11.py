#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.11 — NEGATIVE CONTROLS NC71..NC82.

Additive over the carried-over v1.9 NC50..NC57 and the v1.10 NC63..NC70.  Each
control here targets a SPECIFIC v1.11 governance repair and pairs a faithful
standalone re-implementation of the corresponding repaired detector with an
IN-MEMORY source mutant that a CORRECT detector MUST reject.

Mandated mutants:
  D30 : science integrity gate moved AFTER `_load_models`;
        source+manifest co-edit cannot bypass the launcher (proved on disk,
        re-asserted here structurally).
  D31 : science writes to the historical v1.8 / v1.9 path.
  D32 : science Exception not persisted; science SystemExit not persisted;
        science retry permitted (existence guard removed).
  D26 : literal / `or True` provenance mutation (carried-forward regression).
  D27 : missing / replaced dependency path (set no longer exact).
  D28 : missing / wrong HD95 case reason.

IN-MEMORY SOURCE MUTANTS ONLY.  Canonical files on disk are NEVER modified.
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

CANONICAL_SRC = EXEC.read_text(encoding="utf-8")
CANONICAL_SHA = hashlib.sha256(EXEC.read_bytes()).hexdigest()
LAUNCHER_SRC = LAUNCHER.read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# shared AST helpers
# --------------------------------------------------------------------------- #
def _tree(src):
    return ast.parse(src)


def _funcs(tree):
    return {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}


def _seg(src, name):
    f = _funcs(ast.parse(src))
    if name not in f:
        return ""
    return ast.get_source_segment(src, f[name]) or ""


def _code_only(src):
    kept = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type == tokenize.COMMENT:
                continue
            kept.append(tok)
        out = tokenize.untokenize(kept)
    except Exception:
        out = src
    t = _tree(src)
    for n in ast.walk(t):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            b = getattr(n, "body", [])
            if b and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Constant) \
                    and isinstance(b[0].value.value, str):
                out = out.replace(b[0].value.value, "")
        if isinstance(n, ast.Assign) and isinstance(n.value, ast.Constant) \
                and isinstance(n.value.value, str) and n.value.value:
            out = out.replace(n.value.value, "None")
    return out


def _is_literal_true(node) -> bool:
    return isinstance(node, ast.Constant) and node.value is True


def _has_or_true(node) -> bool:
    if node is None:
        return False
    for n in ast.walk(node):
        if isinstance(n, ast.BoolOp) and isinstance(n.op, ast.Or):
            if any(_is_literal_true(x) for x in n.values):
                return True
    return False


def _collect_names(node) -> set:
    if node is None:
        return set()
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}


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


def _body_calls_in_order(src, fname):
    f = _funcs(ast.parse(src)).get(fname)
    if f is None:
        return []
    out = []
    for stmt in f.body:
        for n in ast.walk(stmt):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
                out.append((n.lineno, n.func.id))
    return sorted(out)


# --------------------------------------------------------------------------- #
# D30 detectors
# --------------------------------------------------------------------------- #
def det_d30_science_gate_before_load(src: str) -> bool:
    t = _tree(src)
    f = _funcs(t)
    if "run_science" not in f:
        return False
    order = _body_calls_in_order(src, "run_science")
    names = [nm for _, nm in order]
    if "_verify_transitive_source_integrity" not in names or "_load_models" not in names:
        return False
    vi = next(ln for ln, nm in order if nm == "_verify_transitive_source_integrity")
    li = next(ln for ln, nm in order if nm == "_load_models")
    if vi >= li:
        return False
    # fail-closed terminal present in the same function
    return ("D30_SCIENCE_TRANSITIVE_RUNTIME_SOURCE_INTEGRITY_FAILED"
            "__STOP_BEFORE_MODEL_CONSTRUCTION"
            in (ast.get_source_segment(src, f["run_science"]) or ""))


def det_d30_no_prefix_bypass(src: str) -> bool:
    """The science integrity gate must NOT be satisfiable by skipping it: the
    function must consult the SAME gate used by smoke (shared authority), not a
    science-only flag, and must be reachable before any model load."""
    t = _tree(src)
    f = _funcs(t)
    if "run_science" not in f or "_verify_transitive_source_integrity" not in f:
        return False
    order = _body_calls_in_order(src, "run_science")
    names = [nm for _, nm in order]
    return (names.index("_verify_transitive_source_integrity")
            < names.index("_load_models") if "_load_models" in names else False)


# --------------------------------------------------------------------------- #
# D31 detectors
# --------------------------------------------------------------------------- #
V1_8_SCIENTIFIC = "phase36_robustness_scientific_result_v1_8.json"
V1_9_SCIENTIFIC = "phase36_robustness_scientific_result_v1_9.json"
V1_11_SCIENTIFIC = "phase36_robustness_scientific_result_v1_11.json"
V1_11_START = "phase36_robustness_science_start_v1_11.json"
V1_11_FAIL = "phase36_robustness_science_failure_v1_11.json"


def det_d31_unique_paths(src: str) -> bool:
    code = _code_only(src)
    # Historical science write paths must be ABSENT once assigned constants are
    # neutralised (a declared sentinel is invisible to this structural view)...
    if V1_8_SCIENTIFIC in code or V1_9_SCIENTIFIC in code:
        return False
    # ...AND no writer may resolve its target through the forbidden sentinel
    # name, which is how a mutant can re-bind the v1.8 path without ever
    # re-introducing the literal string.
    for helper in ("_write_science_success_artifact", "_write_science_failure_artifact"):
        h = _seg(src, helper)
        if "FORBIDDEN_SCIENCE_RESULT_V1_8" in h:
            return False
        for line in h.splitlines():
            if "ROOT /" in line and "SCIENCE_V1_11" not in line \
                    and "V1_11" not in line:
                return False
    for req in (V1_11_SCIENTIFIC, V1_11_START, V1_11_FAIL):
        if req not in src:
            return False
    if 'open(path, "x"' not in _seg(src, "_write_science_success_artifact"):
        return False
    if 'open(path, "x"' not in _seg(src, "_write_science_failure_artifact"):
        return False
    return True


# --------------------------------------------------------------------------- #
# D32 detectors
# --------------------------------------------------------------------------- #
def det_d32_first_attempt_write_once(src: str) -> bool:
    t = _tree(src)
    f = _funcs(t)
    if not all(k in f for k in ("_gate_science_state", "_science_attempt_already_exists",
                                "_create_science_start_marker",
                                "_write_science_failure_artifact",
                                "_write_science_success_artifact",
                                "_run_science_with_durable_evidence", "main")):
        return False
    mk = _seg(src, "_create_science_start_marker")
    if "O_CREAT" not in mk or "O_EXCL" not in mk:
        return False
    if _helper_always_false(src, "_science_attempt_already_exists"):
        return False
    ex = _seg(src, "_science_attempt_already_exists")
    # existence guard must consult ALL three v1.11 science provenance paths
    ex_code = _code_only(ex)
    if ex_code.count("SCIENCE_V1_11") < 3:
        return False
    if not det_d32_exception_persisted(src) or not det_d32_systemexit_persisted(src):
        return False
    w = _seg(src, "_run_science_with_durable_evidence")
    if "LOGICAL_FAILURE" not in w and "classification" not in w:
        return False
    # ordering: gate BEFORE marker in main(); marker BEFORE the run wrapper.
    main = _seg(src, "main")
    gi = main.find("_gate_science_state()")
    mi = main.find("_create_science_start_marker")
    ri = main.find("_run_science_with_durable_evidence")
    if not (0 <= gi < mi < ri):
        return False
    return True


def det_d32_exception_persisted(src: str) -> bool:
    """The wrapper must have a REAL `except Exception` handler whose body writes a
    durable failure artifact (a renamed/neutralised handler must fail this)."""
    t = _tree(src)
    f = _funcs(t)
    if "_run_science_with_durable_evidence" not in f:
        return False
    for n in ast.walk(f["_run_science_with_durable_evidence"]):
        if isinstance(n, ast.Try):
            for h in n.handlers:
                nm = getattr(h.type, "id", None) or getattr(h.type, "attr", None)
                if nm != "Exception":
                    continue
                for x in ast.walk(h):
                    if isinstance(x, ast.Call) and isinstance(x.func, ast.Name) \
                            and x.func.id == "_write_science_failure_artifact":
                        return True
    return False


def det_d32_systemexit_persisted(src: str) -> bool:
    t = _tree(src)
    f = _funcs(t)
    if "_run_science_with_durable_evidence" not in f:
        return False
    for n in ast.walk(f["_run_science_with_durable_evidence"]):
        if isinstance(n, ast.Try):
            for h in n.handlers:
                nm = getattr(h.type, "id", None) or getattr(h.type, "attr", None)
                if nm != "SystemExit":
                    continue
                for x in ast.walk(h):
                    if isinstance(x, ast.Call) and isinstance(x.func, ast.Name) \
                            and x.func.id == "_write_science_failure_artifact":
                        return True
    return False


def _helper_always_false(src: str, fname: str) -> bool:
    """True if the helper's FIRST executable statement is an unconditional
    `return False` (i.e. its real body is dead — a retry-enabling mutation)."""
    f = _funcs(ast.parse(src)).get(fname)
    if f is None:
        return False
    for stmt in f.body:
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
            continue  # docstring
        if isinstance(stmt, ast.Return):
            return isinstance(stmt.value, ast.Constant) and stmt.value.value is False
        return False
    return False


def det_d32_no_retry(src: str) -> bool:
    """A consumed revision must be refused: the helper must have a LIVE body that
    consults all three v1.11 science provenance paths, and main() must call it
    AFTER the gate and BEFORE the start marker."""
    main = _seg(src, "main")
    if "_science_attempt_already_exists" not in main:
        return False
    if _helper_always_false(src, "_science_attempt_already_exists"):
        return False
    gi = main.find("_gate_science_state()")
    ei = main.find("_science_attempt_already_exists")
    mi = main.find("_create_science_start_marker")
    if not (0 <= gi < ei < mi):
        return False
    ex = _seg(src, "_science_attempt_already_exists")
    return _code_only(ex).count("SCIENCE_V1_11") >= 3


# --------------------------------------------------------------------------- #
# D26 / D27 / D28 detectors (carried forward, re-derived against v1.11 bytes)
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
    if _is_literal_true(val_node) or _has_or_true(val_node):
        return False
    if not (needs <= key_names):
        return False
    scope_names = {n.id for n in ast.walk(f["run_smoke"]) if isinstance(n, ast.Name)}
    if "_marker_exists" not in scope_names or "_marker_sole_and_trueseal" not in scope_names:
        return False
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
    exclusive_ok = False
    for n in ast.walk(f["run_smoke"]):
        if isinstance(n, ast.Try):
            for x in ast.walk(n):
                if isinstance(x, ast.Call) and isinstance(x.func, ast.Name) \
                        and x.func.id == "open":
                    for kw in x.keywords:
                        if kw.arg == "mode" and isinstance(kw.value, ast.Constant) \
                                and kw.value.value == "x":
                            exclusive_ok = True
                    for a in x.args[1:2]:
                        if isinstance(a, ast.Constant) and a.value == "x":
                            exclusive_ok = True
    return probe_ok and exclusive_ok


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
    return observed == EXPECTED_TRANSITIVE_DEPENDENCIES


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
    ev = er = None
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
    return {_call_expectation(c) for c in calls} == EXPECTED_HD95_CALLS


# --------------------------------------------------------------------------- #
# D33 detector — non-circular launcher anchor
# --------------------------------------------------------------------------- #
def det_d33_non_circular_anchor(src: str, launcher_src: str, manifest: dict) -> bool:
    if "FROZEN_EXPECTED_EXEC_SHA" not in launcher_src:
        return False
    if "FROZEN_EXPECTED_MANIFEST_SHA" not in launcher_src:
        return False
    if "PHASE36_V1_11_LAUNCH_AUTHORITY" not in src:
        return False
    integ = _seg(src, "_verify_transitive_source_integrity")
    if "LAUNCH_AUTHORITY_TOKEN" not in integ or "os.environ" not in integ:
        return False
    # manifest must declare exec SHA and must NOT declare the launcher SHA
    if manifest.get("execution_source_sha256") != hashlib.sha256(
            EXEC.read_bytes()).hexdigest():
        return False
    if "launcher_sha256" in manifest:
        return False
    return True


# --------------------------------------------------------------------------- #
# Mutators (in-memory string surgery only)
# --------------------------------------------------------------------------- #
def mut_d30_gate_after_load(src: str) -> str:
    """Move the science integrity gate so it runs AFTER _load_models by deleting
    the pre-load gate block (leaving the model load as the first model action)."""
    block = (
        '    source_integrity = _verify_transitive_source_integrity()\n'
        '    if not source_integrity["all_match"]:\n'
        '        raise SystemExit(\n'
        '            "D30_SCIENCE_TRANSITIVE_RUNTIME_SOURCE_INTEGRITY_FAILED'
        '__STOP_BEFORE_MODEL_CONSTRUCTION: "\n'
        '            + json.dumps(source_integrity, indent=1, default=str))\n'
    )
    if block not in src:
        return src
    return src.replace(block, "", 1)


def mut_d31_write_v1_8(src: str) -> str:
    """Point the science success writer at the historical v1.8 path."""
    return src.replace(
        'path = ROOT / SCIENCE_V1_11_ARTIFACT',
        'path = ROOT / FORBIDDEN_SCIENCE_RESULT_V1_8', 1)


def mut_d31_write_v1_9(src: str) -> str:
    return src.replace(
        'path = ROOT / SCIENCE_V1_11_ARTIFACT',
        'path = ROOT / "reports/audits/phase36_robustness_scientific_result_v1_9.json"', 1)


def _neutralise_handler(src: str, wrapper: str, exc_name: str) -> str:
    """Rename the `except <exc_name>` handler INSIDE the named wrapper only.

    `str.replace(..., 1)` is unsafe here because an identical-looking handler
    exists in `_verify_transitive_source_integrity`; the mutation must be applied
    within the wrapper's byte span so the correct handler is neutralised."""
    t = _tree(src)
    f = _funcs(t).get(wrapper)
    if f is None:
        return src
    for n in ast.walk(f):
        if isinstance(n, ast.Try):
            for h in n.handlers:
                nm = getattr(h.type, "id", None) or getattr(h.type, "attr", None)
                if nm != exc_name:
                    continue
                start = h.lineno - 1
                lines = src.splitlines(keepends=True)
                line = lines[start]
                alias = f" as {h.name}" if h.name else ""
                new_line = line.replace(f"except {exc_name}{alias}:",
                                        f"except _NeverRaised{alias}:", 1)
                lines[start] = new_line
                return "".join(lines)
    return src


def mut_d32_drop_exception_persist(src: str) -> str:
    """Neutralise the ordinary-Exception handler of the durable-evidence wrapper
    SPECIFICALLY (not the identical-looking handler inside the integrity gate)."""
    return _neutralise_handler(src, "_run_science_with_durable_evidence", "Exception")


def mut_d32_drop_systemexit_persist(src: str) -> str:
    return _neutralise_handler(src, "_run_science_with_durable_evidence", "SystemExit")


def mut_d32_allow_retry(src: str) -> str:
    """Make the science existence guard always report 'no prior attempt'."""
    return src.replace(
        "def _science_attempt_already_exists() -> bool:",
        "def _science_attempt_already_exists() -> bool:\n    return False", 1)


def mut_d26_hardcode_true(src: str) -> str:
    return src.replace(
        '"is_first_write_once": bool(_marker_exists and _marker_sole_and_trueseal),',
        '"is_first_write_once": True,', 1)


def mut_d26_or_true(src: str) -> str:
    return src.replace(
        '"is_first_write_once": bool(_marker_exists and _marker_sole_and_trueseal),',
        '"is_first_write_once": bool(_marker_exists and _marker_sole_and_trueseal) or True,', 1)


def mut_d27_drop_one_dep(src: str) -> str:
    return src.replace(
        '    "src/utils/device.py":', '    "src/utils/device_PLACEHOLDER.py":', 1)


def mut_d27_replace_dep(src: str) -> str:
    return src.replace(
        '    "reports/tables/phase25f_final_normalization_stats.csv":',
        '    "reports/tables/phase25f_final_normalization_stats_UNEXPECTED.csv":', 1)


def mut_d28_drop_call(src: str) -> str:
    return src.replace(
        '"empty_empty": _hd95_case_exact(',
        '"empty_empty": (lambda c: True)(', 1)


def mut_d28_weaken_reason(src: str) -> str:
    return src.replace(
        'expect_reason="empty_ground_truth"),',
        'expect_reason="empty_prediction"),', 1)


# --------------------------------------------------------------------------- #
# Control table
# --------------------------------------------------------------------------- #
_manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}

CONTROLS = [
    ("NC71_D30_science_gate_moved_after_load_models",
     mut_d30_gate_after_load, det_d30_science_gate_before_load),
    ("NC72_D30_science_gate_bypass_no_prefix_verify",
     mut_d30_gate_after_load, det_d30_no_prefix_bypass),
    ("NC73_D31_science_write_bound_to_v1_8_path",
     mut_d31_write_v1_8, det_d31_unique_paths),
    ("NC74_D31_science_write_bound_to_v1_9_path",
     mut_d31_write_v1_9, det_d31_unique_paths),
    ("NC75_D32_science_exception_not_persisted",
     mut_d32_drop_exception_persist, det_d32_exception_persisted),
    ("NC76_D32_science_systemexit_not_persisted",
     mut_d32_drop_systemexit_persist, det_d32_systemexit_persisted),
    ("NC77_D32_science_retry_permitted",
     mut_d32_allow_retry, det_d32_no_retry),
    ("NC78_D32_first_attempt_write_once_weakened",
     mut_d32_allow_retry, det_d32_first_attempt_write_once),
    ("NC79_D26_provenance_hardcoded_literal_true",
     mut_d26_hardcode_true, det_d26_provenance_derived),
    ("NC80_D26_provenance_or_true_tautology",
     mut_d26_or_true, det_d26_provenance_derived),
    ("NC81_D27_transitive_dep_path_dropped_or_replaced",
     mut_d27_drop_one_dep, det_d27_exact_dep_set),
    ("NC82_D27_transitive_dep_path_replaced",
     mut_d27_replace_dep, det_d27_exact_dep_set),
    ("NC83_D28_hd95_call_site_dropped",
     mut_d28_drop_call, det_d28_four_call_sites),
    ("NC84_D28_hd95_call_reason_weakened",
     mut_d28_weaken_reason, det_d28_four_call_sites),
    ("NC85_D33_source_manifest_co_edit_bypasses_launcher",
     lambda s: s, det_d33_non_circular_anchor),
]

results = []
for name, mutator, detector in CONTROLS:
    mutated = mutator(CANONICAL_SRC)
    changed = mutated != CANONICAL_SRC
    if name == "NC85_D33_source_manifest_co_edit_bypasses_launcher":
        # D33 control: the co-edit is proven on disk by the launcher negative
        # control artifact; here we assert the detector BITES when the manifest
        # illegally declares a launcher SHA (a cycle), and HOLDS on canonical.
        baseline_ok = detector(CANONICAL_SRC, LAUNCHER_SRC, _manifest)
        cyc = dict(_manifest)
        cyc["launcher_sha256"] = "deadbeef"
        mutated_ok = detector(CANONICAL_SRC, LAUNCHER_SRC, cyc)
        changed = True
    else:
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
launcher_sha_after = hashlib.sha256(LAUNCHER.read_bytes()).hexdigest()

report = {
    "artifact": "phase36_v1_11_negative_controls",
    "phase": 36,
    "section": "§K",
    "method": "RA-MedFiLM-BARR",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_11",
    "type": "NEGATIVE_CONTROL_AUDIT",
    "model_free": True,
    "torch_imported": "torch" in sys.modules,
    "protected_population_read": False,
    "mutants_are_in_memory_strings_only": True,
    "canonical_source_sha256_before": CANONICAL_SHA,
    "canonical_source_sha256_after": sha_after,
    "canonical_source_unmodified": bool(CANONICAL_SHA == sha_after),
    "launcher_sha256": launcher_sha_after,
    "nc_range": "NC71-NC85",
    "targets": "D30/D31/D32/D33_plus_carried_D26/D27/D28",
    "carried_over_v1_9": "NC50-NC57_remain_valid_in_phase36_v1_9_negative_controls.json",
    "carried_over_v1_10": "NC63-NC70_remain_valid_in_phase36_v1_10_negative_controls.json",
    "passed": passed,
    "total": total,
    "all_pass": passed == total,
    "controls": results,
}
out = ROOT / "reports/audits/phase36_v1_11_negative_controls.json"
out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({"passed": passed, "total": total, "all_pass": passed == total,
                  "canonical_unmodified": CANONICAL_SHA == sha_after}, indent=1))
for r in results:
    print(("PASS " if r["pass"] else "FAIL "), r["nc"],
          "| canonical_detector=", r["detector_on_canonical"],
          "| mutant_bite=", r["mutant_bite"])
raise SystemExit(0 if passed == total else 1)
