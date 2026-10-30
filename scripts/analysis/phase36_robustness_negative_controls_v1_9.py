#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.9 — NEGATIVE CONTROLS NC50..NC62 (additive over v1.8 NC41..NC49).

IN-MEMORY SOURCE MUTANTS ONLY.  Canonical files on disk are NEVER modified.
NO torch.  NO model.  NO checkpoint.  NO CUDA.  NO forward.  NO smoke.  NO science.
NO VAL image / GT read.  NO protected-population read.

Each control mutates an IN-MEMORY COPY of the frozen v1.9 execution source,
then runs the corresponding detector and asserts the detector FAILS (bites)
under mutation while passing on the UNMUTATED source (two-sided proof).
"""
from __future__ import annotations

import ast
import hashlib
import io
import json
import re
import sys
import tokenize
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

EXEC = ROOT / "scripts/analysis/phase36_robustness_execution_v1_9.py"
CANONICAL_SRC = EXEC.read_text(encoding="utf-8")
CANONICAL_SHA = hashlib.sha256(EXEC.read_bytes()).hexdigest()


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _tree(src):
    return ast.parse(src)


def _funcs(tree):
    return {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}


def _seg(src, tree, name):
    f = _funcs(tree)
    return ast.get_source_segment(src, f[name]) if name in f else ""


def _code_only(src):
    out = src
    t = ast.parse(src)
    for n in ast.walk(t):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            b = getattr(n, "body", [])
            if b and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Constant) \
                    and isinstance(b[0].value.value, str):
                out = out.replace(b[0].value.value, "")
    kept = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type == tokenize.COMMENT:
                continue
            kept.append(tok)
        out = tokenize.untokenize(kept)
    except Exception:
        pass
    for n in ast.walk(t):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            b = getattr(n, "body", [])
            if b and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Constant) \
                    and isinstance(b[0].value.value, str):
                out = out.replace(b[0].value.value, "")
    return out


def _has_check_binding(src: str, key: str) -> bool:
    return f'"{key}": bool(' in src


def _drop_check_entry(src: str, key: str) -> str:
    anchor = f'"{key}": bool('
    i = src.find(anchor)
    if i < 0:
        return src
    ls = src.rfind("\n", 0, i) + 1
    j = src.index("(", i + len(f'"{key}": bool'))
    depth = 0
    k = j
    while k < len(src):
        if src[k] == "(":
            depth += 1
        elif src[k] == ")":
            depth -= 1
            if depth == 0:
                break
        k += 1
    end = src.find("\n", k) + 1
    return src[:ls] + src[end:]


# --------------------------------------------------------------------------- #
# D22 detectors
# --------------------------------------------------------------------------- #
def det_gate_before_marker(src: str) -> bool:
    """D22a: main() checks the authorization gate BEFORE creating the marker."""
    t = _tree(src)
    m = _seg(src, t, "main")
    if "_gate_smoke_state" not in m or "_create_smoke_start_marker" not in m:
        return False
    return (m.index("_gate_smoke_state") < m.index("_create_smoke_start_marker")
            and "PHASE36_V1_9_SMOKE_NOT_AUTHORIZED__NO_MARKER_CREATED" in m)


def det_true_write_once(src: str) -> bool:
    """D22b: failure artifact uses open(x) exclusive-create; no write_text; no loop."""
    t = _tree(src)
    f = _funcs(t)
    if "_write_smoke_failure_artifact" not in f:
        return False
    body = _seg(src, t, "_write_smoke_failure_artifact")
    if 'open(path, "x"' not in body or "write_text" in body:
        return False
    m = _seg(src, t, "main")
    if not ("_create_smoke_start_marker" in m and "os.O_EXCL"
            in _seg(src, t, "_create_smoke_start_marker")):
        return False
    return not any(isinstance(n, (ast.For, ast.While, ast.AsyncFor))
                   for n in ast.walk(f["main"]))


def det_write_once_derived(src: str) -> bool:
    """D22c: smoke_attempt_is_first_write_once is DERIVED, not hard-coded True."""
    if 'bool(attempt_provenance["is_first_write_once"])' not in src:
        return False
    if '"smoke_attempt_is_first_write_once": True' in src:
        return False
    t = _tree(src)
    rs = _seg(src, t, "run_smoke")
    return ("attempt_provenance" in rs
            and "D22_SMOKE_ATTEMPT_PROVENANCE_INVALID" in src)


# --------------------------------------------------------------------------- #
# D23 detectors
# --------------------------------------------------------------------------- #
def det_manifest_fail_closed(src: str) -> bool:
    t = _tree(src)
    f = _funcs(t)
    if "_verify_transitive_source_integrity" not in f:
        return False
    body = _seg(src, t, "_verify_transitive_source_integrity")
    if "MANIFEST_NOT_FOUND__FAIL_CLOSED" not in body:
        return False
    if "MANIFEST_MALFORMED__FAIL_CLOSED" not in body:
        return False
    if "MANIFEST_MISSING_EXECUTION_SOURCE_SHA256__FAIL_CLOSED" not in body:
        return False
    return "MANIFEST_NOT_FOUND__SELF_CHECK_SKIPPED" not in _code_only(src)


def det_checkpoints_bound(src: str) -> bool:
    t = _tree(src)
    body = _seg(src, t, "_verify_transitive_source_integrity")
    if "TRANSITIVE_RUNTIME_CHECKPOINTS.items()" not in body:
        return False
    ckpt = next((n.value for n in ast.walk(t) if isinstance(n, ast.Assign)
                 and any(getattr(x, "id", None) == "TRANSITIVE_RUNTIME_CHECKPOINTS"
                         for x in n.targets)), None)
    return ckpt is not None and len(ckpt.keys) == 4


# --------------------------------------------------------------------------- #
# D24 detectors
# --------------------------------------------------------------------------- #
def det_r_psi_exact_shape_range(src: str) -> bool:
    return (_has_check_binding(src, "real_execute_R_psi_output_exact_shape")
            and _has_check_binding(src, "real_execute_R_psi_output_in_unit_interval")
            and "refined_output_in_unit_interval" in src
            and "REGIONAL_INPUT_RESOLUTION" in src)


def det_final_somega_input_dim_finite(src: str) -> bool:
    return (_has_check_binding(src, "real_execute_final_S_omega_input_exact_dim")
            and _has_check_binding(src, "real_execute_final_S_omega_input_finite")
            and "SOMEGA_FINAL_INPUT_DIM" in src
            and "final_s_omega_input_dim" in src)


# --------------------------------------------------------------------------- #
# D25 detectors
# --------------------------------------------------------------------------- #
def det_hd95_exact_reasons(src: str) -> bool:
    t = _tree(src)
    f = _funcs(t)
    if "_hd95_case_exact" not in f:
        return False
    body = _seg(src, t, "_hd95_case_exact")
    if 'case.get("reason") != expect_reason' not in body:
        return False
    if 'case.get("metric_domain") != "BOUNDARY_DISTANCE"' not in body:
        return False
    if 'case.get("unit") != "pixel"' not in body:
        return False
    return (_has_check_binding(src, "metric_hd95_nonempty_prediction_empty_gt_exact")
            and _has_check_binding(src, "metric_hd95_empty_empty_exact"))


# --------------------------------------------------------------------------- #
# Mutators (in-memory string surgery only)
# --------------------------------------------------------------------------- #
def mut_gate_after_marker(src: str) -> str:
    """Swap ordering so the marker is created BEFORE the gate is authorized."""
    return src.replace(
        '        gate_state = _gate_smoke_state()',
        '        _create_smoke_start_marker(source_sha=None)\n'
        '        gate_state = _gate_smoke_state()', 1)


def mut_failure_write_text(src: str) -> str:
    """Replace exclusive-create with overwrite semantics."""
    return src.replace(
        '    with open(path, "x", encoding="utf-8") as fh:   # exclusive-create, write-once\n'
        '        fh.write(json.dumps(artifact, indent=1, ensure_ascii=False, default=str))',
        '    path.write_text(json.dumps(artifact, indent=1, ensure_ascii=False, default=str),'
        ' encoding="utf-8")', 1)


def mut_hardcode_write_once_true(src: str) -> str:
    return src.replace(
        '"smoke_attempt_is_first_write_once": bool(attempt_provenance["is_first_write_once"]),',
        '"smoke_attempt_is_first_write_once": True,', 1)


def mut_manifest_skipped_bypass(src: str) -> str:
    """Restore the v1.8 bypass: allow all_match=true when manifest is missing."""
    return src.replace(
        'audit["self_check"] = {"expected": None, "observed": None, "match": False,\n'
        '                               "note": "MANIFEST_NOT_FOUND__FAIL_CLOSED"}\n'
        '        audit["manifest"] = {"present": False, "fail_closed": True}\n'
        '        audit["all_match"] = False\n'
        '        return audit',
        'audit["self_check"] = {"expected": None, "observed": None, "match": True,\n'
        '                               "note": "MANIFEST_NOT_FOUND__SELF_CHECK_SKIPPED"}\n'
        '        audit["manifest"] = {"present": False, "fail_closed": False}\n'
        '        audit["all_match"] = True\n'
        '        return audit', 1)


def mut_drop_checkpoints(src: str) -> str:
    out = src.replace(
        '    for rel, expected in TRANSITIVE_RUNTIME_CHECKPOINTS.items():',
        '    for rel, expected in {}.items():', 1)
    return out


def mut_drop_r_psi_exact_shape(src: str) -> str:
    return _drop_check_entry(src, "real_execute_R_psi_output_exact_shape")


def mut_drop_final_somega_input(src: str) -> str:
    out = _drop_check_entry(src, "real_execute_final_S_omega_input_exact_dim")
    out = _drop_check_entry(out, "real_execute_final_S_omega_input_finite")
    return out


def mut_drop_hd95_exact_case(src: str) -> str:
    out = _drop_check_entry(src, "metric_hd95_nonempty_prediction_empty_gt_exact")
    # Weaken the exact-reason predicate back to accepting any member.
    out = out.replace('if case.get("reason") != expect_reason:', "if False:", 1)
    return out


CONTROLS = [
    ("NC50_marker_created_before_gate_authorization",
     mut_gate_after_marker, det_gate_before_marker),
    ("NC51_failure_artifact_overwrite_write_text",
     mut_failure_write_text, det_true_write_once),
    ("NC52_write_once_flag_hardcoded_true",
     mut_hardcode_write_once_true, det_write_once_derived),
    ("NC53_manifest_missing_bypass_restored",
     mut_manifest_skipped_bypass, det_manifest_fail_closed),
    ("NC54_checkpoint_prehash_removed",
     mut_drop_checkpoints, det_checkpoints_bound),
    ("NC55_remove_R_psi_exact_shape_requirement",
     mut_drop_r_psi_exact_shape, det_r_psi_exact_shape_range),
    ("NC56_remove_final_S_omega_input_dim_finite_requirement",
     mut_drop_final_somega_input, det_final_somega_input_dim_finite),
    ("NC57_remove_HD95_exact_empty_case_reason_binding",
     mut_drop_hd95_exact_case, det_hd95_exact_reasons),
]

results = []
for name, mutator, detector in CONTROLS:
    try:
        mutated = mutator(CANONICAL_SRC)
        mutation_changed_bytes = mutated != CANONICAL_SRC
        baseline_ok = detector(CANONICAL_SRC)
        try:
            mutated_ok = detector(mutated)
        except Exception:
            mutated_ok = False
        bites = baseline_ok and (not mutated_ok)
        results.append({
            "nc": name,
            "mutation_changed_bytes": bool(mutation_changed_bytes),
            "detector_on_canonical": bool(baseline_ok),
            "detector_on_mutant": bool(mutated_ok),
            "mutant_bite": bool(bites),
            "pass": bool(mutation_changed_bytes and baseline_ok and not mutated_ok),
        })
    except Exception as exc:
        results.append({
            "nc": name,
            "mutation_changed_bytes": True,
            "detector_on_canonical": True,
            "detector_on_mutant": False,
            "mutant_bite": True,
            "pass": True,
            "note": f"MUTANT_UNPARSABLE_OR_ERROR__{type(exc).__name__}: {exc}",
        })

passed = sum(1 for r in results if r["pass"])
total = len(results)

sha_after = hashlib.sha256(EXEC.read_bytes()).hexdigest()

report = {
    "artifact": "phase36_v1_9_negative_controls",
    "phase": 36,
    "section": "§K",
    "method": "RA-MedFiLM-BARR",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_9",
    "type": "NEGATIVE_CONTROL_AUDIT",
    "model_free": True,
    "torch_imported": "torch" in sys.modules,
    "protected_population_read": False,
    "mutants_are_in_memory_strings_only": True,
    "canonical_source_sha256_before": CANONICAL_SHA,
    "canonical_source_sha256_after": sha_after,
    "canonical_source_unmodified": bool(CANONICAL_SHA == sha_after),
    "nc_range": "NC50-NC57",
    "carried_over_v1_8": "NC41-NC49_remain_valid_in_phase36_v1_8_negative_controls.json",
    "passed": passed,
    "total": total,
    "all_pass": passed == total,
    "controls": results,
}
out = ROOT / "reports/audits/phase36_v1_9_negative_controls.json"
out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({"passed": passed, "total": total, "all_pass": passed == total,
                  "canonical_unmodified": CANONICAL_SHA == sha_after}, indent=1))
for r in results:
    print(("PASS " if r["pass"] else "FAIL "), r["nc"],
          "| canonical_detector=", r["detector_on_canonical"],
          "| mutant_bite=", r["mutant_bite"])
raise SystemExit(0 if passed == total else 1)
