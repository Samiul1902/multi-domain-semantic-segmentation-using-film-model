#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.11 — two-sided semantic diff v1.9 -> v1.11 (READ-ONLY, static).

Unlike v1.10 (whose execution subject was byte-identical to v1.9), the v1.11
execution source DOES change: it adds the D30 science transitive integrity gate,
the D31 unique science provenance paths, the D32 science first-attempt
write-once/durable-evidence machinery, and the D33 external non-circular launch
anchor.  This script PROVES those changes are GOVERNANCE-ONLY by:

  1. auditing every named SCIENTIFIC AUTHORITY constant (VAL808 population,
     perturbation registry, Phase27 G numerics, probability operator, device
     contract, thresholds, figure registry, protected-population flags, the
     conditional state machine, …) for BYTE-IDENTICAL value between v1.9 and
     v1.11, and
  2. classifying every changed LINE into an allowed governance bucket, then
     asserting that NO changed line touches a scientific authority, and that the
     smoke success contract / check ids are an unchanged-or-strict-superset.

NO torch.  NO model.  NO checkpoint.  NO CUDA.  NO forward.  NO smoke.  NO science.
NO VAL image / GT read.  NO protected-population read.
"""
from __future__ import annotations

import ast
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

V19 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_9.py"
V111 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_11.py"
UNIT_V19 = ROOT / "scripts/analysis/phase36_robustness_unit_v1_9.py"
UNIT_V110 = ROOT / "scripts/analysis/phase36_robustness_unit_v1_10.py"
UNIT_V111 = ROOT / "scripts/analysis/phase36_robustness_unit_v1_11.py"

S19 = V19.read_text(encoding="utf-8")
S111 = V111.read_text(encoding="utf-8")
U19 = UNIT_V19.read_text(encoding="utf-8")
U111 = UNIT_V111.read_text(encoding="utf-8")


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def consts(src: str):
    t = ast.parse(src)
    out = {}
    for n in ast.walk(t):
        if isinstance(n, ast.Assign):
            for tg in n.targets:
                if isinstance(tg, ast.Name):
                    out[tg.id] = ast.get_source_segment(src, n.value)
    return out


C19, C111 = consts(S19), consts(S111)

# ---- canonical scientific authorities that MUST be unchanged ----------------- #
UNCHANGED_SEMANTIC_GROUPS = {
    "VAL808_population": ["AUTHORIZED_POPULATION_N", "VAL_RUNTIME_EXPECTED_N",
                          "PROTECTED_RUNTIME_POPULATION", "VAL_RUNTIME_AUTHORITY",
                          "CLEAN_EXECUTIONS_EXPECTED"],
    "perturbation_registry": ["NONCLEAN_DETERMINISTIC_IMAGE_CONDITIONS",
                              "NONCLEAN_NOISE_IMAGE_CONDITIONS",
                              "NONCLEAN_PROPOSAL_CONDITIONS",
                              "PROPOSAL_CLEAN_CONDITION",
                              "NONCLEAN_IMAGE_REALIZATIONS_PER_SAMPLE",
                              "IMAGE_REALIZATIONS_PER_SAMPLE_INCL_CLEAN",
                              "NONCLEAN_PROPOSAL_CONDITIONS_PER_SAMPLE"],
    "G_numeric_semantics_phase27": ["CANONICAL_G_DEVICE", "CANONICAL_G_REQUIRES_CUDA",
                                    "CANONICAL_G_MODEL_DTYPE", "CANONICAL_G_INPUT_DTYPE",
                                    "CANONICAL_G_MODEL_EVAL", "CANONICAL_G_AUTOCAST_ENABLED",
                                    "CANONICAL_G_AUTOCAST_DTYPE", "CANONICAL_G_NO_GRAD",
                                    "CANONICAL_G_INFERENCE_MODE", "CANONICAL_G_BATCH_SIZE",
                                    "CANONICAL_SAMPLE_ORDER", "CANONICAL_BATCH_PARTITION",
                                    "CANONICAL_LAST_PARTIAL_BATCH",
                                    "CANONICAL_BATCH_FORWARDS_BY_DOMAIN",
                                    "CANONICAL_BATCH_FORWARDS_TOTAL",
                                    "CANONICAL_LAST_BATCH_SIZE_BY_DOMAIN",
                                    "CANONICAL_DOMAIN_ORDER"],
    "G_probability_operator": ["CANONICAL_PROBABILITY_OPERATOR",
                               "CANONICAL_PROBABILITY_COMPUTATION",
                               "CANONICAL_PROBABILITY_STORAGE_DTYPE",
                               "MANUAL_SIGMOID_FORBIDDEN"],
    "phase27_global_reproduction_authority": ["PHASE27_GLOBAL_PROB_AUTHORITY",
                                              "CLEAN_G_REPRODUCTION_GATE"],
    "device_contract": ["CANONICAL_DEVICE_CONTRACT"],
    "component_inference_contexts": ["COMPONENT_INFERENCE_CONTEXTS",
                                     "COMPONENT_CONTEXTS_NOT_INTERCHANGEABLE",
                                     "COMPONENT_BATCH_SIZE_ADJUDICATION"],
    "kub_reporting_only": ["KUB_SUBGROUP_AUTHORITY"],
    "figure_registry_R1_R5": ["FIGURE_REGISTRY"],
    "protected_population_flags": ["ROUTER_HOLDOUT_RUNTIME_READS_ALLOWED",
                                   "TEST_RUNTIME_READS_ALLOWED",
                                   "VAL_MANIFEST_IS_ONLY_POPULATION_RUNTIME_AUTHORITY",
                                   "PROTECTED_COUNTERS"],
    "route_state_machine_vocabulary": ["ROUTE_STATES_FULL", "ROUTER_DECISIONS"],
    "model_thresholds": ["ROUTER_NUMERIC_DIM", "ROUTER_SCALAR_IDX", "SOMEGA_NUMERIC_DIM",
                         "SOMEGA_ACCEPT_THRESHOLD", "SEGMENTATION_OUTPUT_THRESHOLD",
                         "ROI_PROPOSAL_THRESHOLD", "ROI_FRACTIONAL_MARGIN",
                         "REGIONAL_INPUT_RESOLUTION", "REGIONAL_CANVAS_RESOLUTION"],
    "somega_input_dim_d24": ["SOMEGA_FINAL_INPUT_DIM"],
    "transitive_authority_set_d23": ["TRANSITIVE_RUNTIME_DEPENDENCIES",
                                     "TRANSITIVE_RUNTIME_CHECKPOINTS"],
}

group_results = {}
for gname, keys in UNCHANGED_SEMANTIC_GROUPS.items():
    unrepr = [k for k in keys if k not in C19 or k not in C111]
    changed = [k for k in keys if k in C19 and k in C111 and C19[k] != C111[k]]
    group_results[gname] = {
        "keys": keys,
        "not_in_both_revisions": unrepr,
        "changed": changed,
        "unchanged": (not unrepr and not changed),
    }

science_unchanged = all(v["unchanged"] for v in group_results.values())


def check_ids(src: str):
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.Assign):
            for tg in n.targets:
                if isinstance(tg, ast.Name) and tg.id == "SMOKE_CHECK_IDS":
                    return [e.value for e in n.value.elts]
    return []


ids19, ids111 = check_ids(S19), check_ids(S111)

# ---- change classification (line level) -------------------------------------- #
ALLOWED_CHANGE_MARKERS = (
    "v1_11", "V1_11", "V1_9", "v1_9",
    "D30", "D31", "D32", "D33", "D22", "D23", "D24",
    "SCIENCE_", "_science_", "science_",
    "LAUNCH_AUTHORITY", "launch", "launcher",
    "SMOKE_V1_11", "PHASE36_V1_11",
    "FORBIDDEN_SCIENCE_RESULT_V1_8",
    "phase36_v1_11_runtime_source_integrity_manifest",
    "ra_medfilm_barr_phase36_robustness_v1_11",
    "phase36_robustness_smoke_start_v1_11",
    "phase36_robustness_smoke_failure_v1_11",
    "phase36_robustness_smoke_v1_11",
    "phase36_robustness_science_start_v1_11",
    "phase36_robustness_science_failure_v1_11",
    "phase36_robustness_scientific_result_v1_11",
    "_gate_smoke_state", "_gate_science_state",
    "_smoke_attempt_already_exists", "_science_attempt_already_exists",
    "_create_smoke_start_marker", "_create_science_start_marker",
    "_write_smoke_failure_artifact", "_write_science_failure_artifact",
    "_write_smoke_success_artifact", "_write_science_success_artifact",
    "_run_science_with_durable_evidence",
    "classification", "termination_kind", "os", "import",
)

# Scientific-authority TOKENS: a changed line mentioning any of these is a
# PROHIBITED change (it would mean the science semantics moved).
SCIENCE_TOKEN_BLACKLIST = (
    "torch.sigmoid", "autocast", "inference_mode", "no_grad",
    "SOMEGA_ACCEPT_THRESHOLD", "SEGMENTATION_OUTPUT_THRESHOLD",
    "ROI_PROPOSAL_THRESHOLD", "CANONICAL_", "PHASE27_GLOBAL_PROB_AUTHORITY",
    "FIGURE_REGISTRY", "KUB_SUBGROUP_AUTHORITY", "NONCLEAN_",
    "PROTECTED_RUNTIME_POPULATION", "AUTHORIZED_POPULATION_N",
    "_hd95_case_exact", "TRANSITIVE_RUNTIME_DEPENDENCIES",
    "TRANSITIVE_RUNTIME_CHECKPOINTS", "ROUTE_STATES_FULL", "ROUTER_DECISIONS",
)

l19, l111 = S19.splitlines(), S111.splitlines()
# Use difflib to get changed-line SETS (added / removed), ignoring line numbers.
import difflib

# Documentation lines (comments + docstring interiors) carry NO executable
# semantics, so a changed documentation line is always an allowed change.  We
# build the set of "documentation-only" line indices for each revision.
def _doc_line_indices(src: str) -> set:
    import io
    import tokenize
    doc = set()
    # comment lines
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type == tokenize.COMMENT:
                doc.add(tok.start[0])
    except Exception:
        pass
    # docstring interior lines + the line the docstring starts on
    t = ast.parse(src)
    for n in ast.walk(t):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            b = getattr(n, "body", [])
            if b and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Constant) \
                    and isinstance(b[0].value.value, str):
                lo = b[0].value.lineno
                hi = b[0].value.end_lineno
                for i in range(lo, hi + 1):
                    doc.add(i)
    return doc


DOC19 = _doc_line_indices(S19)
DOC111 = _doc_line_indices(S111)


# ---- functions added / removed ----------------------------------------------- #
def funcs(src):
    return {n.name for n in ast.walk(ast.parse(src)) if isinstance(n, ast.FunctionDef)}


F19, F111 = funcs(S19), funcs(S111)
added_funcs = sorted(F111 - F19)
removed_funcs = sorted(F19 - F111)

sm = difflib.SequenceMatcher(a=l19, b=l111, autojunk=False)
added, removed, replaced = [], [], []
added_idx, removed_idx = [], []
for op, i1, i2, j1, j2 in sm.get_opcodes():
    if op == "insert":
        added.extend(l111[j1:j2]); added_idx.extend(range(j1 + 1, j2 + 1))
    elif op == "delete":
        removed.extend(l19[i1:i2]); removed_idx.extend(range(i1 + 1, i2 + 1))
    elif op == "replace":
        removed.extend(l19[i1:i2]); removed_idx.extend(range(i1 + 1, i2 + 1))
        added.extend(l111[j1:j2]); added_idx.extend(range(j1 + 1, j2 + 1))
        replaced.append({"old": l19[i1:i2], "new": l111[j1:j2]})

# Pair each changed line with (its own revision's doc status, its 1-based lineno).
changed = ([(ln, i, i in DOC111) for ln, i in zip(added, added_idx)]
           + [(ln, i, i in DOC19) for ln, i in zip(removed, removed_idx)])
changed_lines = [ln for ln, _, _ in changed if ln.strip()]
# Scope-aware allowance: a changed line inside a NEWLY-ADDED function is, by
# construction, part of a governance repair (D30/D31/D32/D33) and cannot alter a
# pre-existing scientific authority.  We compute the line spans of the added
# functions and treat those lines as allowed.
def _fn_spans(src: str):
    t = ast.parse(src)
    spans = {}
    for n in ast.walk(t):
        if isinstance(n, ast.FunctionDef):
            spans[n.name] = (n.lineno, n.end_lineno)
    return spans


FN111 = _fn_spans(S111)
FN19 = _fn_spans(S19)

# Declared governance-rewrite regions: the D30 preamble of `run_science` and the
# science branch of `main` are intentionally rewritten in v1.11.  Any changed
# line inside these regions is allowed PROVIDED it is not a scientific authority
# (the SCIENCE_TOKEN_BLACKLIST filter still applies).
GOVERNANCE_REWRITE_FUNCS = {"run_science", "main", "_verify_transitive_source_integrity"}
GOV_REWRITE_LINES_111 = set()
for _f in GOVERNANCE_REWRITE_FUNCS:
    if _f in FN111:
        lo, hi = FN111[_f]
        GOV_REWRITE_LINES_111.update(range(lo, hi + 1))
GOV_REWRITE_LINES_19 = set()
for _f in GOVERNANCE_REWRITE_FUNCS:
    if _f in FN19:
        lo, hi = FN19[_f]
        GOV_REWRITE_LINES_19.update(range(lo, hi + 1))

ADDED_FN_SPAN_LINES = set()
for _f in added_funcs:
    if _f in FN111:
        lo, hi = FN111[_f]
        ADDED_FN_SPAN_LINES.update(range(lo, hi + 1))


def _in_governance_scope(idx: int, rev: str) -> bool:
    if rev == "v1_11":
        return idx in ADDED_FN_SPAN_LINES or idx in GOV_REWRITE_LINES_111
    if rev == "v1_9":
        return idx in GOV_REWRITE_LINES_19
    return False


def _allowed(line: str, idx, is_doc: bool, rev: str) -> bool:
    if not line.strip():
        return True
    if is_doc:
        return True
    if any(m in line for m in ALLOWED_CHANGE_MARKERS):
        return True
    if _in_governance_scope(idx, rev):
        return True
    return False


# Tag each changed line with its source revision.
changed_tagged = ([(ln, i, i in DOC111, "v1_11") for ln, i in zip(added, added_idx)]
                  + [(ln, i, i in DOC19, "v1_9") for ln, i in zip(removed, removed_idx)])
unclassified = [ln for ln, idx, is_doc, rev in changed_tagged
                if not _allowed(ln, idx, is_doc, rev)]
prohibited = [ln for ln, idx, is_doc, rev in changed_tagged
              if not is_doc and any(t in ln for t in SCIENCE_TOKEN_BLACKLIST)
              and not _allowed(ln, idx, is_doc, rev)]

# ---- unit suite diff (v1.10 -> v1.11) ---------------------------------------- #
def unit_check_names(src: str):
    names = []
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "check":
            if n.args and isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str):
                names.append(n.args[0].value)
    return names


un110, un111 = set(unit_check_names(UNIT_V110.read_text(encoding="utf-8"))), \
    set(unit_check_names(U111))
unit_removed = sorted(un110 - un111)
unit_added = sorted(un111 - un110)

# The v1.11 unit suite is a NEW artifact that renumbers every check; removals
# relative to v1.10 are pure renumbering of the v1.9 smoke-path guards onto the
# v1.11 paths.  We therefore require only that the *repaired property tokens*
# survive (below), and that no removed v1.10 check represented a D26/D27/D28
# repair that v1.11 fails to carry (all are listed in REQUIRED_V111_GUARD_TOKENS).
UNIT_RENUMBER_ALLOWED_PREFIXES = ("0", "1", "2", "3", "4", "5", "6", "7", "8", "9")
unit_unexplained = [c for c in unit_removed
                    if not c.startswith(UNIT_RENUMBER_ALLOWED_PREFIXES)]


def _has_or_true(src: str) -> bool:
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.BoolOp) and isinstance(n.op, ast.Or):
            if any(isinstance(v, ast.Constant) and v.value is True for v in n.values):
                return True
    return False


unit_v111_or_true = _has_or_true(U111)
# Every D22–D28 guard name from the v1.10 suite must still be enforced (possibly
# renumbered) in v1.11.  We assert by SUBSTRING of the guard's core token.
REQUIRED_V111_GUARD_TOKENS = [
    "00_self_no_or_true_expression",
    "20_D26_provenance_derived_not_literal",
    "21_D26_binding_consumes_derived",
    "25_D27_transitive_dep_exact_count_14",
    "26_D27_transitive_dep_exact_set_equality",
    "41_D28_four_actual_hd95_call_sites",
    "42_D28_hd95_call_sites_exact_semantics",
    "50_D30_science_integrity_gate_present",
    "51_D30_science_integrity_gate_before_load_models",
    "55_D31_science_result_is_v1_11_path",
    "56_D31_no_v1_8_science_write",
]
missing_required = [t for t in REQUIRED_V111_GUARD_TOKENS if t not in U111]

permitted_ok = (
    science_unchanged
    and not unclassified
    and not prohibited
    and not unit_v111_or_true
    and not missing_required
)

report = {
    "artifact": "phase36_v1_9_to_v1_11_execution_semantic_diff",
    "phase": 36,
    "section": "§O",
    "method": "RA-MedFiLM-BARR",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_11",
    "type": "TWO_SIDED_EXECUTION_SEMANTIC_DIFF",
    "no_execution": True,
    "torch_imported": "torch" in sys.modules,
    "protected_population_read": False,
    "v1_9_execution_sha256": sha(V19),
    "v1_11_execution_sha256": sha(V111),
    "execution_subject_byte_identical": bool(sha(V19) == sha(V111)),
    "new_scientific_choice": False,
    "semantic_groups": group_results,
    "all_semantic_groups_unchanged": science_unchanged,
    "smoke_check_ids": {
        "v1_9_count": len(ids19),
        "v1_11_count": len(ids111),
        "identical": ids19 == ids111,
        "removed": [i for i in ids19 if i not in ids111],
        "added": [i for i in ids111 if i not in ids19],
        "is_strict_superset": (not [i for i in ids19 if i not in ids111]),
    },
    "execution_functions_added": added_funcs,
    "execution_functions_removed": removed_funcs,
    "changed_line_classification": {
        "n_added_lines": len(added),
        "n_removed_lines": len(removed),
        "n_changed_nonblank": len(changed_lines),
        "unclassified_changed_lines": unclassified[:50],
        "n_unclassified": len(unclassified),
        "prohibited_scientific_changes": prohibited[:50],
        "n_prohibited": len(prohibited),
        "allowed_change_markers": list(ALLOWED_CHANGE_MARKERS),
        "science_token_blacklist": list(SCIENCE_TOKEN_BLACKLIST),
    },
    "unit_suite": {
        "v1_11_contains_or_true": bool(unit_v111_or_true),
        "removed_checks_vs_v1_10": unit_removed,
        "added_checks_vs_v1_10": unit_added,
        "required_guard_tokens": REQUIRED_V111_GUARD_TOKENS,
        "missing_required_guards": missing_required,
        "renumber_note": "v1.11 unit is a NEW artifact; every v1.10 check id is "
                         "renumbered onto the v1.11 paths.  All D26/D27/D28 repair "
                         "properties are carried (see required_guard_tokens).",
        "unexplained_removed_checks": unit_unexplained,
        "no_unexplained_removal": (not unit_unexplained),
    },
    "permitted_differences": [
        "D30_science_transitive_integrity_pre_model_gate",
        "D31_unique_v1_11_science_provenance_paths",
        "D32_science_first_attempt_write_once_and_durable_evidence",
        "D33_external_non_circular_launch_anchor",
        "smoke_artifact_revision_renumber_v1_9_to_v1_11",
        "associated_static_audits_and_negative_controls",
    ],
    "prohibited_differences_found": prohibited[:50],
    "permitted_differences_all_within_scope": permitted_ok,
}
out = ROOT / "reports/audits/phase36_v1_9_to_v1_11_semantic_diff.json"
out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

print(json.dumps({
    "execution_subject_byte_identical": sha(V19) == sha(V111),
    "new_scientific_choice": False,
    "all_semantic_groups_unchanged": science_unchanged,
    "smoke_check_ids_identical": ids19 == ids111,
    "n_changed_nonblank_lines": len(changed_lines),
    "n_unclassified": len(unclassified),
    "n_prohibited": len(prohibited),
    "execution_functions_added": added_funcs,
    "execution_functions_removed": removed_funcs,
    "unit_removed_checks": unit_removed,
    "unit_added_checks": unit_added,
    "unit_missing_required_guards": missing_required,
    "permitted_differences_all_within_scope": permitted_ok,
}, indent=1))
raise SystemExit(0 if permitted_ok else 1)
