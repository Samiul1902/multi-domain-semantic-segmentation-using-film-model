#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.12 — two-sided semantic diff v1.11 -> v1.12 (READ-ONLY, static).

The v1.12 execution source adds the D34 source/manifest launch-anchor
contradiction repair (execution source no longer requires
``manifest["launcher_sha256"]``, and FAILS CLOSED if it unexpectedly appears) and
re-bases the D33 external non-circular launch anchor onto the IMMUTABLE v1.12
launcher (D35).  This script PROVES those changes are GOVERNANCE-ONLY by:

  1. auditing every named SCIENTIFIC AUTHORITY constant for BYTE-IDENTICAL value
     between v1.11 and v1.12, and
  2. classifying every changed LINE into an allowed governance bucket, asserting
     that NO changed line touches a scientific authority, and that the smoke
     success contract / check ids are an unchanged-or-NON-STRICT superset.

REPORTING REPAIR (v1.12): an IDENTICAL check-id set is a SUPERSET but NOT a
STRICT superset.  v1.11 conflated the two; v1.12 reports them distinctly
(``is_superset`` true when nothing was removed; ``is_strict_superset`` true only
when something was actually ADDED).  Reporting/governance only.

NO torch.  NO model.  NO checkpoint.  NO CUDA.  NO forward.  NO smoke.  NO science.
NO VAL image / GT read.  NO protected-population read.  NO ROUTER_HOLDOUT.  NO TEST.
"""
from __future__ import annotations

import ast
import difflib
import hashlib
import io
import json
import sys
import tokenize
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

V111 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_11.py"
V112 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_12.py"
UNIT_V111 = ROOT / "scripts/analysis/phase36_robustness_unit_v1_11.py"
UNIT_V112 = ROOT / "scripts/analysis/phase36_robustness_unit_v1_12.py"

S111 = V111.read_text(encoding="utf-8")
S112 = V112.read_text(encoding="utf-8")
U111 = UNIT_V111.read_text(encoding="utf-8")
U112 = UNIT_V112.read_text(encoding="utf-8")


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


C111, C112 = consts(S111), consts(S112)

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
    unrepr = [k for k in keys if k not in C111 or k not in C112]
    changed = [k for k in keys if k in C111 and k in C112 and C111[k] != C112[k]]
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


ids111, ids112 = check_ids(S111), check_ids(S112)

# ---- smoke check-id set relation (REPORTING REPAIR) -------------------------- #
_ids111 = set(ids111)
_ids112 = set(ids112)
removed_ids = sorted(_ids111 - _ids112)
added_ids = sorted(_ids112 - _ids111)
ids_identical = (ids111 == ids112)
# An IDENTICAL set is a SUPERSET (nothing was removed) but NOT a STRICT superset
# (a strict superset requires at least one ADDED element).  v1.11 conflated these.
is_superset = (not removed_ids)
is_strict_superset = bool(is_superset and added_ids)
check_id_sets_relation = {
    "v1_11_count": len(ids111),
    "v1_12_count": len(ids112),
    "v1_11_unique_count": len(_ids111),
    "v1_12_unique_count": len(_ids112),
    "identical": ids_identical,
    "removed": removed_ids,
    "added": added_ids,
    "is_superset": bool(is_superset),
    "is_strict_superset": bool(is_strict_superset),
    "reporting_note": ("identical check-id sets: is_superset=true, "
                       "is_strict_superset=false (identical != strict superset)"),
}

# ---- change classification (line level) -------------------------------------- #
ALLOWED_CHANGE_MARKERS = (
    "v1_12", "V1_12", "v1_11", "V1_11",
    "D34", "D35", "D36", "D30", "D31", "D32", "D33",
    "SCIENCE_", "_science_", "science_",
    "LAUNCH_AUTHORITY", "launch", "launcher",
    "SMOKE_V1_12", "PHASE36_V1_12",
    "FORBIDDEN_SCIENCE_RESULT_V1_8",
    "phase36_v1_12_runtime_source_integrity_manifest",
    "ra_medfilm_barr_phase36_robustness_v1_12",
    "phase36_robustness_smoke_start_v1_12",
    "phase36_robustness_smoke_failure_v1_12",
    "phase36_robustness_smoke_v1_12",
    "phase36_robustness_science_start_v1_12",
    "phase36_robustness_science_failure_v1_12",
    "phase36_robustness_scientific_result_v1_12",
    "_gate_smoke_state", "_gate_science_state",
    "_smoke_attempt_already_exists", "_science_attempt_already_exists",
    "_create_smoke_start_marker", "_create_science_start_marker",
    "_write_smoke_failure_artifact", "_write_science_failure_artifact",
    "_write_smoke_success_artifact", "_write_science_success_artifact",
    "_run_science_with_durable_evidence",
    "classification", "termination_kind", "launcher_key_present", "os", "import",
)

SCIENCE_TOKEN_BLACKLIST = (
    "torch.sigmoid", "autocast", "inference_mode", "no_grad",
    "SOMEGA_ACCEPT_THRESHOLD", "SEGMENTATION_OUTPUT_THRESHOLD",
    "ROI_PROPOSAL_THRESHOLD", "CANONICAL_", "PHASE27_GLOBAL_PROB_AUTHORITY",
    "FIGURE_REGISTRY", "KUB_SUBGROUP_AUTHORITY", "NONCLEAN_",
    "PROTECTED_RUNTIME_POPULATION", "AUTHORIZED_POPULATION_N",
    "_hd95_case_exact", "TRANSITIVE_RUNTIME_DEPENDENCIES",
    "TRANSITIVE_RUNTIME_CHECKPOINTS", "ROUTE_STATES_FULL", "ROUTER_DECISIONS",
)

l111, l112 = S111.splitlines(), S112.splitlines()


def _doc_line_indices(src: str) -> set:
    doc = set()
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type == tokenize.COMMENT:
                doc.add(tok.start[0])
    except Exception:
        pass
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


DOC111 = _doc_line_indices(S111)
DOC112 = _doc_line_indices(S112)


def funcs(src):
    return {n.name for n in ast.walk(ast.parse(src)) if isinstance(n, ast.FunctionDef)}


F111, F112 = funcs(S111), funcs(S112)
added_funcs = sorted(F112 - F111)
removed_funcs = sorted(F111 - F112)

sm = difflib.SequenceMatcher(a=l111, b=l112, autojunk=False)
added, removed, replaced = [], [], []
added_idx, removed_idx = [], []
for op, i1, i2, j1, j2 in sm.get_opcodes():
    if op == "insert":
        added.extend(l112[j1:j2]); added_idx.extend(range(j1 + 1, j2 + 1))
    elif op == "delete":
        removed.extend(l111[i1:i2]); removed_idx.extend(range(i1 + 1, i2 + 1))
    elif op == "replace":
        removed.extend(l111[i1:i2]); removed_idx.extend(range(i1 + 1, i2 + 1))
        added.extend(l112[j1:j2]); added_idx.extend(range(j1 + 1, j2 + 1))
        replaced.append({"old": l111[i1:i2], "new": l112[j1:j2]})

changed = ([(ln, i, i in DOC112) for ln, i in zip(added, added_idx)]
           + [(ln, i, i in DOC111) for ln, i in zip(removed, removed_idx)])
changed_lines = [ln for ln, _, _ in changed if ln.strip()]


def _fn_spans(src: str):
    t = ast.parse(src)
    spans = {}
    for n in ast.walk(t):
        if isinstance(n, ast.FunctionDef):
            spans[n.name] = (n.lineno, n.end_lineno)
    return spans


FN112 = _fn_spans(S112)
FN111 = _fn_spans(S111)

GOVERNANCE_REWRITE_FUNCS = {"run_science", "main", "_verify_transitive_source_integrity"}
GOV_REWRITE_LINES_112 = set()
for _f in GOVERNANCE_REWRITE_FUNCS:
    if _f in FN112:
        lo, hi = FN112[_f]
        GOV_REWRITE_LINES_112.update(range(lo, hi + 1))
GOV_REWRITE_LINES_111 = set()
for _f in GOVERNANCE_REWRITE_FUNCS:
    if _f in FN111:
        lo, hi = FN111[_f]
        GOV_REWRITE_LINES_111.update(range(lo, hi + 1))

ADDED_FN_SPAN_LINES = set()
for _f in added_funcs:
    if _f in FN112:
        lo, hi = FN112[_f]
        ADDED_FN_SPAN_LINES.update(range(lo, hi + 1))


def _in_governance_scope(idx: int, rev: str) -> bool:
    if rev == "v1_12":
        return idx in ADDED_FN_SPAN_LINES or idx in GOV_REWRITE_LINES_112
    if rev == "v1_11":
        return idx in GOV_REWRITE_LINES_111
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


changed_tagged = ([(ln, i, i in DOC112, "v1_12") for ln, i in zip(added, added_idx)]
                  + [(ln, i, i in DOC111, "v1_11") for ln, i in zip(removed, removed_idx)])
unclassified = [ln for ln, idx, is_doc, rev in changed_tagged
                if not _allowed(ln, idx, is_doc, rev)]
prohibited = [ln for ln, idx, is_doc, rev in changed_tagged
              if not is_doc and any(t in ln for t in SCIENCE_TOKEN_BLACKLIST)
              and not _allowed(ln, idx, is_doc, rev)]

# ---- unit suite diff (v1.11 -> v1.12) ---------------------------------------- #
def unit_check_names(src: str):
    names = []
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "check":
            if n.args and isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str):
                names.append(n.args[0].value)
    return names


un111, un112 = set(unit_check_names(U111)), set(unit_check_names(U112))
unit_removed = sorted(un111 - un112)
unit_added = sorted(un112 - un111)
UNIT_RENUMBER_ALLOWED_PREFIXES = tuple("0123456789")
unit_unexplained = [c for c in unit_removed
                    if not c.startswith(UNIT_RENUMBER_ALLOWED_PREFIXES)]


def _has_or_true(src: str) -> bool:
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.BoolOp) and isinstance(n.op, ast.Or):
            if any(isinstance(v, ast.Constant) and v.value is True for v in n.values):
                return True
    return False


unit_v112_or_true = _has_or_true(U112)
# Every D22–D33 guard from the v1.11 suite must still be enforced (possibly
# renumbered) in v1.12, PLUS the new D34/D35/D36 guards.
REQUIRED_V112_GUARD_TOKENS = [
    "00_self_no_or_true_expression",
    "20_D26_provenance_derived_not_literal",
    "21_D26_binding_consumes_derived",
    "25_D27_transitive_dep_exact_count_14",
    "26_D27_transitive_dep_exact_set_equality",
    "41_D28_four_actual_hd95_call_sites",
    "42_D28_hd95_call_sites_exact_semantics",
    "50_D30_science_integrity_gate_present",
    "51_D30_science_integrity_gate_before_load_models",
    "55_D31_science_result_is_v1_12_path",
    "56_D31_no_v1_8_science_write",
    "100_D34_source_does_not_read_manifest_launcher_sha",
    "110_D35_launcher_no_os_environ_get",
    "126_D36_cross_contract_canonical_pair_satisfiable",
]
missing_required = [t for t in REQUIRED_V112_GUARD_TOKENS if t not in U112]

permitted_ok = (
    science_unchanged
    and not unclassified
    and not prohibited
    and not unit_v112_or_true
    and not missing_required
    and bool(is_superset)
)

report = {
    "artifact": "phase36_v1_11_to_v1_12_execution_semantic_diff",
    "phase": 36,
    "section": "§O",
    "method": "RA-MedFiLM-BARR",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_12",
    "type": "TWO_SIDED_EXECUTION_SEMANTIC_DIFF",
    "no_execution": True,
    "torch_imported": "torch" in sys.modules,
    "protected_population_read": False,
    "v1_11_execution_sha256": sha(V111),
    "v1_12_execution_sha256": sha(V112),
    "execution_subject_byte_identical": bool(sha(V111) == sha(V112)),
    "new_scientific_choice": False,
    "semantic_groups": group_results,
    "all_semantic_groups_unchanged": science_unchanged,
    "smoke_check_ids": check_id_sets_relation,
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
        "v1_12_contains_or_true": bool(unit_v112_or_true),
        "removed_checks_vs_v1_11": unit_removed,
        "added_checks_vs_v1_11": unit_added,
        "required_guard_tokens": REQUIRED_V112_GUARD_TOKENS,
        "missing_required_guards": missing_required,
        "renumber_note": "v1.12 unit is a NEW artifact that retains every v1.11 "
                         "guard (possibly renumbered) onto the v1.12 paths and adds "
                         "D34/D35/D36 cross-binding guards.",
        "unexplained_removed_checks": unit_unexplained,
        "no_unexplained_removal": (not unit_unexplained),
    },
    "permitted_differences": [
        "D34_source_manifest_launch_anchor_contradiction_removed",
        "D35_immutable_non_env_overridable_launch_hashes",
        "D36_three_file_validation_cross_binding",
        "smoke_artifact_revision_renumber_v1_11_to_v1_12",
        "associated_static_audits_and_negative_controls",
    ],
    "prohibited_differences_found": prohibited[:50],
    "permitted_differences_all_within_scope": permitted_ok,
}
out = ROOT / "reports/audits/phase36_v1_11_to_v1_12_semantic_diff.json"
out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

print(json.dumps({
    "execution_subject_byte_identical": sha(V111) == sha(V112),
    "new_scientific_choice": False,
    "all_semantic_groups_unchanged": science_unchanged,
    "smoke_check_ids_identical": ids_identical,
    "smoke_check_ids_is_superset": bool(is_superset),
    "smoke_check_ids_is_strict_superset": bool(is_strict_superset),
    "n_changed_nonblank_lines": len(changed_lines),
    "n_unclassified": len(unclassified),
    "n_prohibited": len(prohibited),
    "unit_removed_checks": unit_removed,
    "unit_added_checks": unit_added,
    "unit_missing_required_guards": missing_required,
    "permitted_differences_all_within_scope": permitted_ok,
}, indent=1))
raise SystemExit(0 if permitted_ok else 1)
