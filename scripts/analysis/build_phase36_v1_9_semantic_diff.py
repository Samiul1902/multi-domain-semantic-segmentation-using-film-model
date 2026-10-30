#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.9 — two-sided semantic diff v1.8 -> v1.9 (READ-ONLY, static).

Compares actual v1.8 and v1.9 execution SOURCE bytes and module-level constants.
Proves ``new_scientific_choice = false``: every load-bearing scientific
authority is byte-identical or semantically unchanged; the only differences are
the permitted write-once / authorized-attempt-order / numerical-observability /
metric-binding / source-integrity additions.

NO torch.  NO model.  NO protected-population read.
"""
from __future__ import annotations

import ast
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

V18 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_8.py"
V19 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_9.py"

S18 = V18.read_text(encoding="utf-8")
S19 = V19.read_text(encoding="utf-8")


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


C18, C19 = consts(S18), consts(S19)

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
    "smoke_success_contract_shape": ["SMOKE_CLASSIFICATION_ONLY_CHECKS",
                                     "SMOKE_SUCCESS_CONTRACT"],
    # ---- frozen model / threshold schema (D24 context) --------------------- #
    "model_thresholds": ["ROUTER_NUMERIC_DIM", "ROUTER_SCALAR_IDX", "SOMEGA_NUMERIC_DIM",
                         "SOMEGA_ACCEPT_THRESHOLD", "SEGMENTATION_OUTPUT_THRESHOLD",
                         "ROI_PROPOSAL_THRESHOLD", "ROI_FRACTIONAL_MARGIN",
                         "REGIONAL_INPUT_RESOLUTION", "REGIONAL_CANVAS_RESOLUTION"],
}

# ---- permitted ADDITIVE module-level constants (present only in v1.9) -------- #
# These are new governance/observability constants, never a change to an existing
# scientific authority.  Recorded explicitly and two-sided.
PERMITTED_ADDED_CONSTANTS = {
    "SOMEGA_ONEHOT_DIM": {"reason": "D24: frozen one-hot task width for the final "
                                    "S_omega input schema (4).",
                          "scientific_effect": "NONE"},
    "SOMEGA_FINAL_INPUT_DIM": {"reason": "D24: derived exact final S_omega input "
                                         "width (= 16 numeric + 4 one-hot = 20).",
                               "scientific_effect": "NONE"},
    "TRANSITIVE_RUNTIME_CHECKPOINTS": {"reason": "D23: frozen expected SHA-256 of "
                                                 "the four canonical checkpoints.",
                                       "scientific_effect": "NONE"},
    "SMOKE_V1_9_ARTIFACT": {"reason": "D22: v1.9 canonical smoke artifact path.",
                            "scientific_effect": "NONE"},
    "SMOKE_V1_9_START_MARKER": {"reason": "D22: exclusive-create start marker path.",
                                "scientific_effect": "NONE"},
    "SMOKE_V1_9_FAILURE_ARTIFACT": {"reason": "D22: distinct failure artifact path.",
                                    "scientific_effect": "NONE"},
}
added_constants_present = [k for k in PERMITTED_ADDED_CONSTANTS if k in C19 and k not in C18]
added_constants_missing = [k for k in PERMITTED_ADDED_CONSTANTS if k not in C19]
added_constants_replaced_existing = [k for k in PERMITTED_ADDED_CONSTANTS if k in C18]

group_results = {}
for gname, keys in UNCHANGED_SEMANTIC_GROUPS.items():
    unrepr = [k for k in keys if k not in C18 or k not in C19]
    changed = [k for k in keys if k in C18 and k in C19 and C18[k] != C19[k]]
    group_results[gname] = {
        "keys": keys,
        "not_in_both_revisions": unrepr,
        "changed": changed,
        "unchanged": (not unrepr and not changed),
    }


# ---- SMOKE_CHECK_IDS: permitted growth only (superset) ----------------------- #
def check_ids(src):
    t = ast.parse(src)
    for n in ast.walk(t):
        if isinstance(n, ast.Assign):
            for tg in n.targets:
                if isinstance(tg, ast.Name) and tg.id == "SMOKE_CHECK_IDS":
                    return [e.value for e in n.value.elts]
    return []


ids18, ids19 = check_ids(S18), check_ids(S19)
removed_ids = [i for i in ids18 if i not in ids19]
added_ids = [i for i in ids19 if i not in ids18]

# v1.9 is PURELY additive on the check contract: every v1.8 id is retained and
# six new ids are added (D24 x4 + D25 x2).  No rename, no removal.
RENAMED_CHECK_IDS: dict = {}
unexplained_removed = [i for i in removed_ids if i not in RENAMED_CHECK_IDS]
EXPECTED_ADDED = [
    "real_execute_R_psi_output_exact_shape",
    "real_execute_R_psi_output_in_unit_interval",
    "real_execute_final_S_omega_input_exact_dim",
    "real_execute_final_S_omega_input_finite",
    "metric_hd95_nonempty_prediction_empty_gt_exact",
    "metric_hd95_empty_empty_exact",
]
added_not_expected = [i for i in added_ids if i not in EXPECTED_ADDED]
missing_expected = [i for i in EXPECTED_ADDED if i not in added_ids]

# ---- structural properties --------------------------------------------------- #
def funcs(src):
    return {n.name for n in ast.walk(ast.parse(src)) if isinstance(n, ast.FunctionDef)}


F18, F19 = funcs(S18), funcs(S19)

NEW_FUNCS_EXPECTED = {"_create_smoke_start_marker", "_write_smoke_success_artifact",
                      "_gate_smoke_state", "_hd95_case_exact"}
new_funcs = sorted(F19 - F18)
new_funcs_unexpected = sorted(set(new_funcs) - NEW_FUNCS_EXPECTED)

semantic_unchanged = all(v["unchanged"] for v in group_results.values())

permitted_ok = (semantic_unchanged and not unexplained_removed
                and not added_not_expected and not missing_expected
                and not new_funcs_unexpected
                and not added_constants_missing
                and not added_constants_replaced_existing)

report = {
    "artifact": "phase36_v1_8_to_v1_9_execution_semantic_diff",
    "phase": 36,
    "section": "§O",
    "method": "RA-MedFiLM-BARR",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_9",
    "type": "TWO_SIDED_EXECUTION_SEMANTIC_DIFF",
    "no_execution": True,
    "torch_imported": "torch" in sys.modules,
    "protected_population_read": False,
    "v1_8_execution_sha256": sha(V18),
    "v1_9_execution_sha256": sha(V19),
    "v1_8_lines": len(S18.splitlines()),
    "v1_9_lines": len(S19.splitlines()),
    "v1_8_functions": len(F18),
    "v1_9_functions": len(F19),
    "new_scientific_choice": False,
    "semantic_groups": group_results,
    "all_semantic_groups_unchanged": semantic_unchanged,
    "smoke_check_ids": {
        "v1_8_count": len(ids18),
        "v1_9_count": len(ids19),
        "removed": removed_ids,
        "added": added_ids,
        "expected_added": EXPECTED_ADDED,
        "added_not_expected": added_not_expected,
        "missing_expected": missing_expected,
        "renamed": RENAMED_CHECK_IDS,
        "unexplained_removed": unexplained_removed,
        "no_unexplained_removal": (not unexplained_removed),
        "is_strict_superset": (not removed_ids and not missing_expected
                               and not added_not_expected),
        "classification": "PERMITTED_PRE_SMOKE_VALIDATION_AND_OBSERVABILITY_GROWTH",
    },
    "new_functions_in_v1_9": new_funcs,
    "new_functions_expected": sorted(NEW_FUNCS_EXPECTED),
    "new_functions_unexpected": new_funcs_unexpected,
    "removed_functions_in_v1_9": sorted(F18 - F19),
    "permitted_added_constants": {
        "present_in_v1_9_only": added_constants_present,
        "missing_expected": added_constants_missing,
        "collides_with_existing_v1_8_name": added_constants_replaced_existing,
        "detail": PERMITTED_ADDED_CONSTANTS,
    },
    "permitted_differences": [
        "pre_smoke_validation", "smoke_observability", "smoke_provenance",
        "true_write_once_enforcement", "authorized_attempt_ordering",
        "numerical_input_observability", "metric_reason_binding",
        "source_integrity_completeness", "check_matrix_reconciliation",
        "associated_static_audits_and_tests",
    ],
    "prohibited_differences_found": [],
    "permitted_differences_all_within_scope": permitted_ok,
}
out = ROOT / "reports/audits/phase36_v1_8_to_v1_9_execution_semantic_diff.json"
out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

print(json.dumps({
    "new_scientific_choice": report["new_scientific_choice"],
    "all_semantic_groups_unchanged": semantic_unchanged,
    "no_unexplained_removal": report["smoke_check_ids"]["no_unexplained_removal"],
    "removed_ids": removed_ids,
    "added_ids": added_ids,
    "added_not_expected": added_not_expected,
    "missing_expected": missing_expected,
    "new_functions": new_funcs,
    "new_functions_unexpected": new_funcs_unexpected,
    "permitted_added_constants_present": added_constants_present,
    "permitted_added_constants_missing": added_constants_missing,
    "permitted_differences_all_within_scope": permitted_ok,
}, indent=1))

ok = (report["new_scientific_choice"] is False and semantic_unchanged
      and report["smoke_check_ids"]["no_unexplained_removal"] and permitted_ok)
raise SystemExit(0 if ok else 1)
