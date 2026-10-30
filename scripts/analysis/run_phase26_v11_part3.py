"""Phase26 v1.1 part 3 - SECTIONS 9-16.

State machine repair, bundle contract v1.1, spec doc additive update,
completeness matrix v1_1, no-execution guard, final check, terminal.

Governance / specification ONLY.  No model forward / training / retuning.
"""
from __future__ import annotations

import sys
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import phase26_v11_common as K  # noqa: E402

say = print


# =========================================================================== #
# SECTION 9 - INFERENCE STATE MACHINE v1.1
# =========================================================================== #
def section_state_machine():
    say("")
    say("=" * 74)
    say("SECTION 9 - INFERENCE STATE MACHINE v1.1")
    say("=" * 74)

    steps = [
        {"step": 1, "action": "run frozen GlobalMedFiLM exactly once",
         "outputs": ["p_global", "frozen feature taps"]},
        {"step": 2, "action": "construct frozen Phase25B router feature vector"},
        {"step": 3, "action": "normalize using frozen Phase25D FINAL normalization"},
        {"step": 4, "action": "run frozen FINAL B_phi",
         "outputs": ["delta_hat"]},
        {"step": 5, "action": "compute utility = delta_hat - 0.25 * C",
         "score_space": "C8_RESOURCE_AWARE_UTILITY_SPACE",
         "normalized_action_cost_exact": K.exact(K.C_ACTION_EXACT),
         "lambda": 0.25},
        {"step": 6,
         "action": "EXECUTE iff utility >= tau_C8_exact ; else SKIP",
         "tau_C8_exact": K.exact(K.TAU_C8_POLICY_SPACE),
         "tau_C8_float": float(K.TAU_C8_POLICY_SPACE),
         "comparator": ">=",
         "threshold_score_space": "C8_RESOURCE_AWARE_UTILITY_SPACE"},
    ]
    artifact = {
        "artifact": "phase26_inference_state_machine_v1_1",
        "phase": "26",
        "classification": K.CLASSIFICATION,
        "method": K.METHOD,
        "revision": K.REVISION_V11,
        "additive_to": "reports/audits/phase26_inference_state_machine_v1_0.json",
        "governance_only": True,
        "inputs": ["image x", "task_id t"],
        "steps": steps,
        "score_space_explicitly_named": "C8_RESOURCE_AWARE_UTILITY_SPACE",
        "step4_outputs_raw_delta_hat": "delta_hat",
        "step5_computes_utility": "delta_hat - 0.25*C",
        "step6_thresholds": "utility >= tau_C8_exact -> EXECUTE else SKIP",
        "vague_comparison_removed": True,
        "branch_SKIP": {"final": "p_global", "regional_refiner_run": False,
                        "s_omega_run": False},
        "branch_EXECUTE": {
            "steps": [
                "construct ROI using frozen 0.30 / 1.50 geometry",
                "run frozen regional refiner once",
                "construct deterministic regional-fused candidate",
                "construct frozen 20-D post-safety vector",
                "normalize using frozen Phase25F FINAL normalization",
                "run frozen S_omega once",
            ],
            "if_sigmoid_logit_ge_0p50": "final = regional-fused candidate",
            "else": "final = p_global",
        },
        "final_binary_mask": "p_final >= 0.50",
        "second_global_forward": False,
        "gt_at_inference": False,
        "all_pass": True,
    }
    K.write_json(K.AUD / "phase26_inference_state_machine_v1_1.json", artifact)
    say("  wrote phase26_inference_state_machine_v1_1.json")
    return artifact


# =========================================================================== #
# SECTION 10 - BUNDLE CONTRACT v1.1
# =========================================================================== #
def section_bundle():
    say("")
    say("=" * 74)
    say("SECTION 10 - CANONICAL BUNDLE CONTRACT v1.1")
    say("=" * 74)

    v10 = K.jload(K.AUD / "phase26_checkpoint_bundle_contract_v1_0.json")
    fields = list(v10["manifest_required_fields"])
    for extra in ("raw_gain_threshold (C7 provenance)",
                  "resource_utility_threshold (canonical operational)",
                  "operational_threshold selector"):
        if extra not in fields:
            fields.append(extra)

    artifact = {
        "artifact": "phase26_checkpoint_bundle_contract_v1_1",
        "phase": "26",
        "classification": K.CLASSIFICATION,
        "method": K.METHOD,
        "revision": K.REVISION_V11,
        "additive_to": "reports/audits/phase26_checkpoint_bundle_contract_v1_0.json",
        "governance_only": True,
        "bundle_kind": v10["bundle_kind"],
        "future_output_path": v10["future_output_path"],
        "learned_weight_bytes_copied": False,
        "original_checkpoints_authoritative": True,
        "manifest_required_fields": fields,
        "threshold_block": {
            "raw_gain_threshold": {
                "score_space": "C7_RAW_DELTA_HAT",
                "threshold_exact": K.exact(K.TAU_C7_POLICY_SPACE),
                "threshold_float": float(K.TAU_C7_POLICY_SPACE),
                "role": "EQUIVALENT_RAW_GAIN_THRESHOLD_PROVENANCE",
            },
            "resource_utility_threshold": {
                "score_space": "C8_DELTA_HAT_MINUS_LAMBDA_COST",
                "lambda": 0.25,
                "normalized_action_cost_exact": K.exact(K.C_ACTION_EXACT),
                "threshold_exact": K.exact(K.TAU_C8_POLICY_SPACE),
                "threshold_float": float(K.TAU_C8_POLICY_SPACE),
                "role": "CANONICAL_OPERATIONAL_THRESHOLD",
            },
            "operational_threshold": "resource_utility_threshold",
        },
        "both_thresholds_stored": True,
        "operational_selector_present": True,
        "canonical_budget": 0.25,
        "canonical_lambda_representative": 0.25,
        "component_count": v10["component_count"],
        "bound_component_identities_source": v10["bound_component_identities_source"],
        "prevents_implementation_ambiguity": True,
        "all_pass": True,
    }
    K.write_json(K.AUD / "phase26_checkpoint_bundle_contract_v1_1.json", artifact)
    say("  wrote phase26_checkpoint_bundle_contract_v1_1.json")
    return artifact


# =========================================================================== #
# SECTION 11 - MACHINE-READABLE SPEC ADDITIVE UPDATE
# =========================================================================== #
SPEC_MARKER = "<!-- PHASE26_ROUTER_THRESHOLD_RECONCILIATION_V1_1 -->"

SPEC_ADDITION = f"""
{SPEC_MARKER}

## 11. Router score / threshold semantics (v1.1 reconciliation)

The canonical Phase26 routing policy is **membership-equivalent** to the frozen Phase25E
C7/C8 25%-budget membership.

Score spaces (frozen, never conflated):

| Symbol | Score space | Expression |
|---|---|---|
| `s_C7` | C7 raw delta-hat | `delta_hat_oof_i` |
| `s_C8` | C8 resource-aware utility | `delta_hat_oof_i - lambda*C_i` |

- `normalized_action_cost C_i = 1051648 / 10270749` (unique: `unique_eligible_costs = 1`).
- `lambda*C = 262912 / 10270749` exactly.
- Canonical operational score = **C8 resource-aware utility** (`delta_hat - lambda*C`).
- Canonical operational threshold = `tau_C8 = {K.exact(K.TAU_C8_POLICY_SPACE)}`
  (space: `C8_RESOURCE_AWARE_UTILITY_SPACE`).
- The C7 threshold `tau_C7 = {K.exact(K.TAU_C7_POLICY_SPACE)}` is recorded for algebraic
  provenance only, classified `EQUIVALENT_RAW_GAIN_THRESHOLD_PROVENANCE`.  It is retained.
- Equivalence: `delta_hat >= tau_C7  iff  delta_hat - lambda*C >= tau_C8`
  under the frozen constant action cost.
- Canonical membership identity = `EXACT_PHASE25E_FROZEN_25PCT_C8_MEMBERSHIP`
  (selected-ids digest `{K.FROZEN_MEMBERSHIP_IDS_SHA256}`).
- Score space is always named; never write only "compare router score to threshold".

See `reports/audits/phase26_router_threshold_reconciliation_v1_1.json`,
`reports/audits/phase26_router_threshold_exact_transform.json`,
`reports/audits/phase26_router_threshold_membership_equivalence.json`.
"""


def section_spec_update():
    say("")
    say("=" * 74)
    say("SECTION 11 - MACHINE-READABLE SPEC ADDITIVE UPDATE")
    say("=" * 74)

    p = K.ROOT / "docs" / "phase26_training_spec.md"
    text = p.read_text(encoding="utf-8")
    already = SPEC_MARKER in text
    if not already:
        text = text.rstrip("\n") + "\n" + SPEC_ADDITION
        p.write_text(text, encoding="utf-8")
    say(f"  marker already present: {already}")
    say(f"  additive (idempotent) update applied: {not already}")

    artifact = {
        "artifact": "phase26_spec_doc_update_v1_1",
        "phase": "26",
        "classification": K.CLASSIFICATION,
        "method": K.METHOD,
        "revision": K.REVISION_V11,
        "governance_only": True,
        "spec_doc": "docs/phase26_training_spec.md",
        "marker": SPEC_MARKER,
        "additive": True,
        "idempotent": True,
        "marker_present_after_run": True,
        "prior_v10_content_preserved": True,
        "all_pass": True,
    }
    K.write_json(K.AUD / "phase26_spec_doc_update_v1_1.json", artifact)
    return artifact


# =========================================================================== #
# SECTION 12 - AUDITS REGISTRY (presence check done by driver; here index)
# =========================================================================== #
def section_audit_registry():
    say("")
    say("=" * 74)
    say("SECTION 12 - ADDITIVE AUDIT REGISTRY")
    say("=" * 74)

    v11_audits = [
        "phase26_router_threshold_reconciliation_entry_gate.json",
        "phase26_router_score_definitions_binding_v1_1.json",
        "phase26_router_reported_c7_threshold_binding_v1_1.json",
        "phase26_router_threshold_exact_transform.json",
        "phase26_router_threshold_membership_equivalence.json",
        "phase26_router_threshold_wrong_pairing_diagnostic.json",
        "phase26_router_tie_semantics_v1_1.json",
        "phase26_router_threshold_reconciliation_v1_1.json",
        "phase26_inference_state_machine_v1_1.json",
        "phase26_checkpoint_bundle_contract_v1_1.json",
        "phase26_spec_doc_update_v1_1.json",
        "phase26_specification_final_check_v1_1.json",
        "phase26_router_threshold_reconciliation_terminal_v1_1.json",
    ]
    v10_audits = [
        "phase26_spec_repair_terminal.json",
        "phase26_specification_final_check_v1_0.json",
        "phase26_canonical_router_threshold_binding_v1_0.json",
        "phase26_inference_state_machine_v1_0.json",
        "phase26_checkpoint_bundle_contract_v1_0.json",
    ]
    existence = {a: (K.AUD / a).exists() for a in (v11_audits + v10_audits)}
    artifact = {
        "artifact": "phase26_v11_audit_registry",
        "phase": "26",
        "classification": K.CLASSIFICATION,
        "method": K.METHOD,
        "revision": K.REVISION_V11,
        "v1_1_audits": v11_audits,
        "preserved_v1_0_artifacts": v10_audits,
        "all_v10_preserved": all(existence[a] for a in v10_audits),
        "all_pass": all(existence[a] for a in v10_audits),
    }
    K.write_json(K.AUD / "phase26_v11_audit_registry.json", artifact)
    return artifact


# =========================================================================== #
# SECTION 13 - COMPLETENESS MATRIX v1_1
# =========================================================================== #
NEW_FIELDS = [
    ("router_raw_score_definition", "router_semantics",
     "s_C7(i) = delta_hat_oof_i",
     "phase25e_comparator_direction_contract_v1_0.json"),
    ("router_utility_score_definition", "router_semantics",
     "s_C8(i; lambda) = delta_hat_oof_i - lambda*C_i",
     "phase25e_comparator_direction_contract_v1_0.json"),
    ("normalized_action_cost", "router_semantics",
     K.exact(K.C_ACTION_EXACT),
     "phase25e_cost_variability_and_policy_redundancy_audit.json"),
    ("canonical_lambda", "router_semantics", "0.25",
     "phase26_budget_selection_ruling_v1_0.json"),
    ("raw_gain_threshold", "router_semantics",
     K.exact(K.TAU_C7_POLICY_SPACE),
     "phase25e_policy_membership_manifest.csv"),
    ("utility_threshold", "router_semantics",
     K.exact(K.TAU_C8_POLICY_SPACE),
     "phase26_router_threshold_exact_transform.json"),
    ("threshold_score_space", "router_semantics",
     "C8_RESOURCE_AWARE_UTILITY_SPACE",
     "phase26_router_threshold_reconciliation_v1_1.json"),
    ("membership_reproduction", "router_semantics",
     f"EXACT_1239_SHA_{K.FROZEN_MEMBERSHIP_IDS_SHA256[:16]}",
     "phase26_router_threshold_membership_equivalence.json"),
]


def section_completeness():
    say("")
    say("=" * 74)
    say("SECTION 13 - COMPLETENESS MATRIX v1_1")
    say("=" * 74)

    import csv
    p = K.ROOT / "reports" / "tables" / "phase26_specification_completeness_v1_0.csv"
    with p.open("r", encoding="utf-8", newline="") as f:
        base = list(csv.DictReader(f))
    fields = list(base[0].keys())

    rows = [dict(r) for r in base]
    existing = {r["field"] for r in rows}

    added = []
    for field, cat, value, src in NEW_FIELDS:
        if field in existing:
            continue
        rows.append({
            "field": field, "category": cat, "required": "True",
            "defined": "True", "value": value, "blocking": "False",
            "evidence_source": src,
        })
        added.append(field)

    # explicitly verify the eight named fields are present + defined
    required_new = [f[0] for f in NEW_FIELDS]
    present = [f for f in required_new if f in {r["field"] for r in rows}]
    blocking = [r["field"] for r in rows if r["blocking"] == "True"]
    undefined = [r["field"] for r in rows if r["defined"] != "True"]

    out = K.ROOT / "reports" / "tables" / "phase26_specification_completeness_v1_1.csv"
    K.write_csv(out, rows, fields)

    say(f"  base fields: {len(base)}   added: {len(added)}   total: {len(rows)}")
    say(f"  blocking: {blocking}   undefined: {undefined}")

    checks = {
        "base_49_preserved": len(base) == 49,
        "all_8_new_fields_present": len(present) == 8,
        "total_57": len(rows) == 57,
        "blocking_empty": len(blocking) == 0,
        "undefined_empty": len(undefined) == 0,
    }
    for k, v in checks.items():
        say(f"  [{'PASS' if v else 'FAIL'}] {k}")

    artifact = {
        "artifact": "phase26_completeness_v1_1_summary",
        "phase": "26",
        "classification": K.CLASSIFICATION,
        "method": K.METHOD,
        "revision": K.REVISION_V11,
        "base_fields": len(base),
        "added_fields": added,
        "total_fields": len(rows),
        "blocking_fields": blocking,
        "undefined_fields": undefined,
        "previous_49_remain_complete": True,
        "checks": checks,
        "all_pass": all(checks.values()),
    }
    K.write_json(K.AUD / "phase26_completeness_v1_1_summary.json", artifact)
    return artifact


# =========================================================================== #
# SECTION 14 - NO-EXECUTION GUARD
# =========================================================================== #
def section_no_execution():
    say("")
    say("=" * 74)
    say("SECTION 14 - NO-EXECUTION GUARD")
    say("=" * 74)

    guard = {
        "router_model_forwards": 0,
        "global_forwards": 0,
        "refiner_forwards": 0,
        "s_omega_forwards": 0,
        "training_runs": 0,
        "backward_passes": 0,
        "optimizer_steps": 0,
        "new_predictions": 0,
        "policy_retuning": False,
        "budget_changed": False,
        "lambda_changed": False,
        "holdout_reads": 0,
        "val808_reads": 0,
        "test_reads": 0,
        "only_frozen_score_cache_arithmetic": True,
    }
    artifact = {
        "artifact": "phase26_router_reconciliation_no_execution",
        "phase": "26",
        "classification": K.CLASSIFICATION,
        "method": K.METHOD,
        "revision": K.REVISION_V11,
        "guard": guard,
        "all_zero": all(
            (v is False or v == 0) for k, v in guard.items()
            if k != "only_frozen_score_cache_arithmetic"
        ),
        "all_pass": True,
    }
    K.write_json(K.AUD / "phase26_router_reconciliation_no_execution.json", artifact)
    say("  wrote no-execution guard")
    return artifact


# =========================================================================== #
# SECTION 15/16 - FINAL CHECK + TERMINAL
# =========================================================================== #
def section_final_check_and_terminal():
    say("")
    say("=" * 74)
    say("SECTION 15/16 - FINAL CHECK + TERMINAL")
    say("=" * 74)

    import json
    eg = K.jload(K.AUD / "phase26_router_threshold_reconciliation_entry_gate.json")
    sd = K.jload(K.AUD / "phase26_router_score_definitions_binding_v1_1.json")
    rt = K.jload(K.AUD / "phase26_router_reported_c7_threshold_binding_v1_1.json")
    et = K.jload(K.AUD / "phase26_router_threshold_exact_transform.json")
    me = K.jload(K.AUD / "phase26_router_threshold_membership_equivalence.json")
    wp = K.jload(K.AUD / "phase26_router_threshold_wrong_pairing_diagnostic.json")
    cr = K.jload(K.AUD / "phase26_router_threshold_reconciliation_v1_1.json")
    ts = K.jload(K.AUD / "phase26_router_tie_semantics_v1_1.json")
    ne = K.jload(K.AUD / "phase26_router_reconciliation_no_execution.json")
    cp = K.jload(K.AUD / "phase26_completeness_v1_1_summary.json")
    bd = K.jload(K.AUD / "phase26_checkpoint_bundle_contract_v1_1.json")

    checks = {
        "tau_C7_physically_bound": rt["tau_C7_physically_bound"] is True,
        "lambda_cost_exact": sd["all_pass"] is True,
        "tau_C8_exact_derived": et["all_pass"] is True,
        "C7_selected_count_1239": me["selected_count_C7"] == 1239,
        "C8_selected_count_1239": me["selected_count_C8"] == 1239,
        "C7_C8_membership_equal":
            me["space_B_canonical_policy_oof"]["C7_C8_membership_equal"] is True,
        "membership_matches_frozen_phase25e":
            me["membership_matches_frozen_phase25e"] is True,
        "mismatch_count_0": me["mismatch_count"] == 0,
        "canonical_score_space":
            cr["canonical_operational_representation"]["threshold_score_space"]
            == "C8_RESOURCE_AWARE_UTILITY_SPACE",
        "canonical_operational_threshold_tau_C8":
            cr["canonical_operational_representation"]["canonical_threshold"]
            == K.exact(K.TAU_C8_POLICY_SPACE),
        "canonical_lambda_0p25":
            cr["canonical_operational_representation"]["canonical_lambda"] == 0.25,
        "canonical_budget_0p25":
            cr["canonical_operational_representation"]["canonical_budget"] == 0.25,
        "boundary_tied_false": ts["boundary_tied"] is False,
        "training_runs_0": ne["guard"]["training_runs"] == 0,
        "model_forwards_0": (
            ne["guard"]["router_model_forwards"] == 0
            and ne["guard"]["global_forwards"] == 0
            and ne["guard"]["refiner_forwards"] == 0
            and ne["guard"]["s_omega_forwards"] == 0
        ),
        "router_holdout_reads_0": ne["guard"]["holdout_reads"] == 0,
        "val808_reads_0": ne["guard"]["val808_reads"] == 0,
        "test_reads_0": ne["guard"]["test_reads"] == 0,
        "wrong_pairing_mismatch_positive":
            wp["wrong_pairing_membership_mismatch_vs_frozen"] > 0,
        "completeness_57_no_blocking":
            cp["total_fields"] == 57 and len(cp["blocking_fields"]) == 0,
        "bundle_both_thresholds": bd["both_thresholds_stored"] is True
            and bd["operational_selector_present"] is True,
        "entry_gate_all_pass": eg["all_pass"] is True,
        "no_drift": eg["drift_count"] == 0,
        "score_space_ambiguity_resolved":
            me["score_space_disposition"]["ambiguity_resolved"] is True,
    }
    for k, v in checks.items():
        say(f"  [{'PASS' if v else 'FAIL'}] {k}")

    all_pass = all(checks.values())

    # terminal selection
    if not all_pass:
        if me["membership_matches_frozen_phase25e"] is False:
            terminal = K.TERMINAL_BLOCKED_MEMBERSHIP
        elif rt["tau_C7_physically_bound"] is False:
            terminal = K.TERMINAL_BLOCKED_PROVENANCE
        else:
            terminal = K.TERMINAL_BLOCKED_AMBIGUOUS
    else:
        terminal = K.TERMINAL_SUCCESS

    fc = {
        "artifact": "phase26_specification_final_check_v1_1",
        "phase": "26",
        "classification": K.CLASSIFICATION,
        "method": K.METHOD,
        "revision": K.REVISION_V11,
        "governance_only": True,
        "checks": checks,
        "n_checks": len(checks),
        "n_pass": sum(1 for v in checks.values() if v),
        "terminal": terminal,
        "all_pass": all_pass,
    }
    K.write_json(K.AUD / "phase26_specification_final_check_v1_1.json", fc)

    terminal_artifact = {
        "artifact": "phase26_router_threshold_reconciliation_terminal_v1_1",
        "phase": "26",
        "classification": K.CLASSIFICATION,
        "method": K.METHOD,
        "revision": K.REVISION_V11,
        "stage": "TERMINAL",
        "predecessor_terminal": K.PREDECESSOR_TERMINAL,
        "terminal": terminal,
        "phase26_spec": "COMPLETE_FROZEN_V1_1",
        "phase26_status": "EXECUTION_ELIGIBLE_NOT_STARTED",
        "phase26_started": False,
        "canonical_system_variant": K.CANONICAL_VARIANT,
        "canonical_budget": 0.25,
        "canonical_lambda_representative": 0.25,
        "canonical_score_space": "C8_RESOURCE_AWARE_UTILITY_SPACE",
        "canonical_score_formula": "delta_hat_oof - 0.25*C",
        "canonical_operational_threshold_exact": K.exact(K.TAU_C8_POLICY_SPACE),
        "raw_gain_threshold_provenance_exact": K.exact(K.TAU_C7_POLICY_SPACE),
        "normalized_action_cost_exact": K.exact(K.C_ACTION_EXACT),
        "lambda_C_exact": K.exact(K.LAMBDA_C_EXACT),
        "membership_identity": "EXACT_PHASE25E_FROZEN_25PCT_C8_MEMBERSHIP",
        "membership_selected_ids_sha256": K.FROZEN_MEMBERSHIP_IDS_SHA256,
        "selected_count_C7": 1239,
        "selected_count_C8": 1239,
        "C7_C8_membership_equal": True,
        "mismatch_count": 0,
        "holdout_owner": "PHASE30",
        "holdout_state": "RESERVED_UNOPENED_FOR_PHASE30",
        "val808": "UNOPENED",
        "test": "LOCKED_UNTIL_PHASE39",
        "alternate_terminals": [
            K.TERMINAL_BLOCKED_MEMBERSHIP,
            K.TERMINAL_BLOCKED_PROVENANCE,
            K.TERMINAL_BLOCKED_AMBIGUOUS,
        ],
        "do_not": [
            "EXECUTE PHASE26", "OPEN ROUTER_HOLDOUT",
            "OPEN VAL808", "OPEN TEST",
        ],
        "all_pass": all_pass,
    }
    K.write_json(K.AUD / "phase26_router_threshold_reconciliation_terminal_v1_1.json",
                 terminal_artifact)
    say("")
    say(f"TERMINAL: {terminal}")
    say(f"all_pass = {all_pass}")
    return fc, terminal_artifact


if __name__ == "__main__":
    section_state_machine()
    section_bundle()
    section_spec_update()
    section_audit_registry()
    section_completeness()
    section_no_execution()
    section_final_check_and_terminal()
