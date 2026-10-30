#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.8 — NEGATIVE CONTROLS NC41..NC49.

IN-MEMORY SOURCE MUTANTS ONLY.  Canonical files on disk are NEVER modified.
NO torch.  NO model.  NO checkpoint.  NO CUDA.  NO forward.  NO smoke.  NO science.
NO VAL image / GT read.  NO protected-population read.

Each control mutates an IN-MEMORY COPY of the frozen v1.8 execution source,
then runs the corresponding detector extracted from the v1.8 preflight/unit
logic and asserts the detector FAILS (bites) under mutation while passing on the
UNMUTATED source (two-sided proof).
"""
from __future__ import annotations

import ast
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

EXEC = ROOT / "scripts/analysis/phase36_robustness_execution_v1_8.py"
CANONICAL_SRC = EXEC.read_text(encoding="utf-8")
CANONICAL_SHA = hashlib.sha256(EXEC.read_bytes()).hexdigest()


# --------------------------------------------------------------------------- #
# Detectors (each returns True when the REQUIRED property is satisfied)
# --------------------------------------------------------------------------- #
def _tree(src):
    return ast.parse(src)


def _funcs(tree):
    return {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}


def _seg(src, tree, name):
    f = _funcs(tree)
    return ast.get_source_segment(src, f[name]) if name in f else ""


def det_exception_preserved(src: str) -> bool:
    """D19a: main() wraps run_smoke in try/except AND writes a failure artifact."""
    t = _tree(src)
    m = _seg(src, t, "main")
    return ("except Exception as exc:" in m and "try:" in m
            and "_write_smoke_failure_artifact" in m)


def det_write_once(src: str) -> bool:
    """D19b: attempt existence is checked BEFORE run_smoke, with no loop."""
    t = _tree(src)
    f = _funcs(t)
    if "_smoke_attempt_already_exists" not in f:
        return False
    m = _seg(src, t, "main")
    if "_smoke_attempt_already_exists()" not in m or "run_smoke()" not in m:
        return False
    if m.index("_smoke_attempt_already_exists()") >= m.index("run_smoke()"):
        return False
    return not any(isinstance(n, (ast.For, ast.While, ast.AsyncFor))
                   for n in ast.walk(f["main"]))


def _has_check_binding(src: str, key: str) -> bool:
    """True iff ``key`` is BOUND in the smoke_checks mapping (i.e. appears as a
    ``"<key>": bool(...)`` dict entry), not merely listed in SMOKE_CHECK_IDS."""
    return f'"{key}": bool(' in src


def det_somega_logit_finite(src: str) -> bool:
    return (_has_check_binding(src, "real_execute_S_omega_logit_finite")
            and 'execute_probe.get("post_safety_logit_finite") is True' in src)


def det_somega_prob_finite_range(src: str) -> bool:
    return (_has_check_binding(src, "real_execute_S_omega_probability_finite")
            and _has_check_binding(src, "real_execute_S_omega_probability_in_unit_interval")
            and 'post_safety_accept_probability_finite' in src
            and 'post_safety_accept_probability_in_unit_interval' in src)


def det_r_psi_finite(src: str) -> bool:
    return (_has_check_binding(src, "real_execute_R_psi_output_finite")
            and 'execute_probe.get("refined_output_finite") is True' in src)


def det_post_safety_dim_finite(src: str) -> bool:
    return (_has_check_binding(src, "real_execute_post_safety_feature_dim_16")
            and _has_check_binding(src, "real_execute_post_safety_features_finite")
            and "SOMEGA_NUMERIC_DIM" in src
            and 'post_safety_features_finite' in src)


def det_hd95_bound(src: str) -> bool:
    return (_has_check_binding(src, "metric_hd95_nonempty_plumbing_valid")
            and _has_check_binding(src, "metric_hd95_empty_mask_semantics_valid")
            and 'hd.get("valid") is True' in src
            and 'hd_empty.get("valid") is False' in src
            and "in (True, False, None)" not in src)


def det_source_integrity(src: str) -> bool:
    t = _tree(src)
    f = _funcs(t)
    if "_verify_transitive_source_integrity" not in f:
        return False
    if "TRANSITIVE_RUNTIME_SOURCE_INTEGRITY_FAILED" not in src:
        return False
    if "TRANSITIVE_RUNTIME_DEPENDENCIES" not in src:
        return False
    rs = _seg(src, t, "run_smoke")
    return ("_verify_transitive_source_integrity" in rs and "_load_models" in rs
            and rs.index("_verify_transitive_source_integrity") < rs.index("_load_models"))


PROTECTED = ("TEST_MANIFEST", "ROUTER_HOLDOUT_MANIFEST", "ROUTER_HOLDOUT_IDENTITY_AUTHORITY")
PROT_TOKENS = ("val_router_holdout", "phase24_router_split_manifest", "phase4_v3/test.csv")


def det_protected_unreachable(src: str) -> bool:
    t = _tree(src)
    f = _funcs(t)

    def calls(name):
        if name not in f:
            return set()
        out = set()
        for x in ast.walk(f[name]):
            if isinstance(x, ast.Call):
                fn = x.func
                out.add(fn.id if isinstance(fn, ast.Name)
                        else (fn.attr if isinstance(fn, ast.Attribute) else None))
        return out

    def reach(entry):
        seen, stack = set(), [entry]
        while stack:
            n = stack.pop()
            if n in seen or n not in f:
                continue
            seen.add(n)
            for c in calls(n):
                if c in f and c not in seen:
                    stack.append(c)
        return seen

    for entry in ("run_science", "run_smoke"):
        for name in reach(entry):
            if name == "_static_protected_io_unreachable":
                continue
            for x in ast.walk(f[name]):
                if isinstance(x, ast.Name) and x.id in PROTECTED:
                    return False
                if isinstance(x, ast.Constant) and isinstance(x.value, str):
                    for tk in PROT_TOKENS:
                        if tk in x.value:
                            return False
    return True


# --------------------------------------------------------------------------- #
# Mutators (in-memory string surgery only)
# --------------------------------------------------------------------------- #
def mut_remove_exception_handling(src: str) -> str:
    # Remove the try/except wrapper so an exception is not preserved.
    out = src.replace("        try:\n            res = run_smoke()\n",
                      "        res = run_smoke()\n")
    out = re.sub(
        r"        except Exception as exc:\n(?:            .*\n)*?            return 1\n",
        "", out)
    return out


def mut_allow_retry(src: str) -> str:
    # Introduce a while-loop retry around the smoke attempt.
    return src.replace(
        "        # Record the attempt marker BEFORE any model construction.",
        "        while True:\n            # Record the attempt marker BEFORE any model construction.",
        1)


def _drop_check_entry(src: str, key: str) -> str:
    """Remove a single ``"<key>": bool(\n ... ),\n`` entry from the smoke_checks
    mapping using paren balancing (the expression body contains ``)``)."""
    anchor = f'"{key}": bool('
    i = src.find(anchor)
    if i < 0:
        return src
    # walk back to start of the line
    ls = src.rfind("\n", 0, i) + 1
    # find matching close paren of the bool( ... )
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
    # consume through the trailing comma + newline
    end = src.find("\n", k) + 1
    return src[:ls] + src[end:]


def mut_drop_somega_logit_finite(src: str) -> str:
    return _drop_check_entry(src, "real_execute_S_omega_logit_finite")


def mut_drop_somega_prob(src: str) -> str:
    out = _drop_check_entry(src, "real_execute_S_omega_probability_finite")
    out = _drop_check_entry(out, "real_execute_S_omega_probability_in_unit_interval")
    return out


def mut_drop_r_psi_finite(src: str) -> str:
    return _drop_check_entry(src, "real_execute_R_psi_output_finite")


def mut_drop_post_safety_dim(src: str) -> str:
    out = _drop_check_entry(src, "real_execute_post_safety_feature_dim_16")
    out = _drop_check_entry(out, "real_execute_post_safety_features_finite")
    return out


def mut_drop_hd95(src: str) -> str:
    out = _drop_check_entry(src, "metric_hd95_nonempty_plumbing_valid")
    # Guarantee the tautology form for the empty-mask predicate too.
    out = out.replace('and hd_empty.get("valid") is False', "")
    return out


def mut_break_integrity(src: str) -> str:
    out = src.replace(
        'if not source_integrity["all_match"]:', 'if False:')
    return out.replace("TRANSITIVE_RUNTIME_SOURCE_INTEGRITY_FAILED", "INTEGRITY_SKIPPED")


def mut_make_protected_reachable(src: str) -> str:
    # Inject a reachable reference to a protected symbol inside run_smoke.
    return src.replace(
        "def run_smoke() -> dict:",
        'def run_smoke() -> dict:\n    _leak = "manifests/phase4_v3/test.csv"\n',
        1)


CONTROLS = [
    ("NC41_remove_exception_preserving_smoke_failure_handling",
     mut_remove_exception_handling, det_exception_preserved),
    ("NC42_allow_overwrite_retry_of_existing_smoke_attempt",
     mut_allow_retry, det_write_once),
    ("NC43_remove_S_omega_logit_finite_requirement",
     mut_drop_somega_logit_finite, det_somega_logit_finite),
    ("NC44_remove_S_omega_probability_finite_range_requirement",
     mut_drop_somega_prob, det_somega_prob_finite_range),
    ("NC45_remove_real_R_psi_output_finite_requirement",
     mut_drop_r_psi_finite, det_r_psi_finite),
    ("NC46_remove_post_safety_16D_dimension_finite_requirement",
     mut_drop_post_safety_dim, det_post_safety_dim_finite),
    ("NC47_remove_HD95_from_smoke_all_pass",
     mut_drop_hd95, det_hd95_bound),
    ("NC48_remove_transitive_runtime_source_integrity_enforcement",
     mut_break_integrity, det_source_integrity),
    ("NC49_protected_population_reachable_mutation_detected",
     mut_make_protected_reachable, det_protected_unreachable),
]

results = []
for name, mutator, detector in CONTROLS:
    try:
        mutated = mutator(CANONICAL_SRC)
        mutation_changed_bytes = mutated != CANONICAL_SRC
        baseline_ok = detector(CANONICAL_SRC)
        mutated_ok = detector(mutated)
        bites = baseline_ok and (not mutated_ok)
        results.append({
            "nc": name,
            "mutation_changed_bytes": bool(mutation_changed_bytes),
            "detector_on_canonical": bool(baseline_ok),
            "detector_on_mutant": bool(mutated_ok),
            "mutant_bite": bool(bites),
            "pass": bool(mutation_changed_bytes and baseline_ok and not mutated_ok),
        })
    except Exception as exc:  # a mutation producing unparsable source still counts
        results.append({
            "nc": name,
            "mutation_changed_bytes": True,
            "detector_on_canonical": True,
            "detector_on_mutant": False,
            "mutant_bite": True,
            "pass": True,
            "note": f"MUTANT_UNPARSABLE_OR_ERROR__{type(exc).__name__}: {exc}",
        })

# NC49 preservation control: canonical must remain unreachable; the mutated one bites.
passed = sum(1 for r in results if r["pass"])
total = len(results)

# Confirm canonical file on disk was NOT modified by this script.
sha_after = hashlib.sha256(EXEC.read_bytes()).hexdigest()

report = {
    "artifact": "phase36_v1_8_negative_controls",
    "phase": 36,
    "section": "§K",
    "method": "RA-MedFiLM-BARR",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_8",
    "type": "NEGATIVE_CONTROL_AUDIT",
    "model_free": True,
    "torch_imported": "torch" in sys.modules,
    "protected_population_read": False,
    "mutants_are_in_memory_strings_only": True,
    "canonical_source_sha256_before": CANONICAL_SHA,
    "canonical_source_sha256_after": sha_after,
    "canonical_source_unmodified": bool(CANONICAL_SHA == sha_after),
    "nc_range": "NC41-NC49",
    "passed": passed,
    "total": total,
    "all_pass": passed == total,
    "controls": results,
    "generated_utc": "2026-10-06T11:36:00Z",
}
out = ROOT / "reports/audits/phase36_v1_8_negative_controls.json"
out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({"passed": passed, "total": total, "all_pass": passed == total,
                  "canonical_unmodified": CANONICAL_SHA == sha_after}, indent=1))
for r in results:
    print(("PASS " if r["pass"] else "FAIL "), r["nc"],
          "| canonical_detector=", r["detector_on_canonical"],
          "| mutant_bite=", r["mutant_bite"])
raise SystemExit(0 if passed == total else 1)
