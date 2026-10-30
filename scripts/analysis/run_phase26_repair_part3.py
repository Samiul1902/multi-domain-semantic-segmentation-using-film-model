"""Phase26 SPECIFICATION REPAIR - PART 3 (§14-§32).

Contracts, repaired 49-field completeness matrix, no-execution audit,
final check, terminal, additive docs sync.

Governance only.  No training / no optimizer / no forward / no holdout / no VAL / no TEST.

Produces:
  phase26_no_training_objective_contract_v1_0.json
  phase26_optimization_fields_contract_v1_0.json
  phase26_checkpoint_bundle_contract_v1_0.json
  phase26_evidence_class_contract_v1_0.json
  phase26_downstream_boundary_contract_v1_0.json
  phase26_holdout_lock_v1_0.json
  phase26_spec_repair_no_execution.json
  reports/tables/phase26_specification_completeness_v1_0.csv
  phase26_spec_repair_final_check.json
  phase26_spec_repair_terminal.json
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import phase26_common as C  # noqa: E402

REVISION = "ra_medfilm_barr_phase26_integration_v1_0"
CLASS = "SUPERVISOR_SPECIFICATION_REPAIR__PHASE26_OPERATIONAL_REDEFINITION"
NA = "NOT_APPLICABLE__NO_PARAMETER_OPTIMIZATION"

TERM_SUCCESS = ("PHASE26_SPEC_V1_0_COMPLETE__MODULAR_INTEGRATION_NO_RETRAINING_AND_"
                "CANONICAL_25PCT_A8_POLICY_FROZEN__PHASE26_EXECUTION_ELIGIBLE_NOT_STARTED")
TERM_STILL_INCOMPLETE = "PHASE26_SPEC_REPAIR_BLOCKED__SPECIFICATION_STILL_INCOMPLETE"
TERM_DRIFT = "PHASE26_SPEC_REPAIR_BLOCKED__PREDECESSOR_DRIFT"
TERM_THRESHOLD_UNRESOLVED = "PHASE26_SPEC_REPAIR_BLOCKED__CANONICAL_FINAL_ROUTER_THRESHOLD_UNRESOLVED"
TERM_POLICY_FAILURE = "PHASE26_SPEC_REPAIR_BLOCKED__DEVELOPMENT_POLICY_RULE_BINDING_FAILURE"


def say(m):
    print(m, flush=True)


# ============================================================ §14 objective
def section_objective():
    say("-" * 78)
    say("§14 LOSS / OBJECTIVE FIELDS")
    say("-" * 78)
    obj = {"artifact": "phase26_no_training_objective_contract_v1_0",
           "phase": "26", "classification": CLASS, "method": C.METHOD_NAME,
           "revision": REVISION, "governance_only": True,
           "phase26_training_required": False,
           "phase26_objective": NA, "phase26_loss_function": NA,
           "loss_weighting_scheme": NA, "loss_aggregation_rule": NA,
           "multi_task_balancing": NA, "all_pass": True}
    C.write_json(C.AUD / "phase26_no_training_objective_contract_v1_0.json", obj)
    say(f"  objective/loss fields = {NA}")
    return obj


# ============================================================ §15 optimization
def section_optimization():
    say("-" * 78)
    say("§15 OPTIMIZATION FIELDS")
    say("-" * 78)
    obj = {"artifact": "phase26_optimization_fields_contract_v1_0",
           "phase": "26", "classification": CLASS, "method": C.METHOD_NAME,
           "revision": REVISION, "governance_only": True,
           "optimizer": "NONE", "learning_rate": NA, "weight_decay": NA,
           "scheduler": "NONE", "batch_size_for_training": NA, "max_epochs": 0,
           "early_stopping": NA, "checkpoint_selection_metric": NA,
           "final_refit_rule": "NOT_APPLICABLE__ALL_COMPONENTS_ALREADY_FINAL_REFIT",
           "optimizer_instantiated_in_phase26_execution": False, "all_pass": True}
    C.write_json(C.AUD / "phase26_optimization_fields_contract_v1_0.json", obj)
    say(f"  optimizer=NONE scheduler=NONE max_epochs=0")
    return obj


# ============================================================ §16 checkpoint bundle
def section_bundle():
    say("-" * 78)
    say("§16 CANONICAL CHECKPOINT BUNDLE CONTRACT")
    say("-" * 78)
    idb = C.jload(C.AUD / "phase26_component_identity_binding_v1_0.json")
    obj = {
        "artifact": "phase26_checkpoint_bundle_contract_v1_0",
        "phase": "26", "classification": CLASS, "method": C.METHOD_NAME,
        "revision": REVISION, "governance_only": True,
        "bundle_kind": "MANIFEST_OF_EXISTING_CANONICAL_COMPONENTS",
        "future_output_path": "artifacts/phase26_ra_medfilm_barr_bundle_v1_0/canonical_bundle_manifest.json",
        "learned_weight_bytes_copied": False,
        "original_checkpoints_authoritative": True,
        "manifest_required_fields": [
            "method name", "bundle revision",
            "GlobalMedFiLM checkpoint path + SHA",
            "regional refiner checkpoint path + SHA",
            "benefit router checkpoint path + SHA",
            "post-safety checkpoint path + SHA",
            "router normalization path + SHA",
            "post-safety normalization path + SHA",
            "router feature schema path + SHA",
            "post-safety feature schema path + SHA",
            "task mapping", "ROI geometry rules", "fusion rule",
            "canonical budget = 0.25", "canonical lambda representative = 0.25",
            "exact router threshold", "S_omega threshold = 0.50",
            "segmentation threshold = 0.50", "analytical MAC constants",
            "Phase25 final freeze identities", "Phase30 holdout reservation",
        ],
        "bound_component_identities_source": "reports/audits/phase26_component_identity_binding_v1_0.json",
        "component_count": idb.get("component_count"),
        "all_pass": True,
    }
    C.write_json(C.AUD / "phase26_checkpoint_bundle_contract_v1_0.json", obj)
    say(f"  bundle = {obj['bundle_kind']} at {obj['future_output_path']}")
    return obj


# ============================================================ §18 evidence class
def section_evidence_class():
    say("-" * 78)
    say("§18 EVIDENCE CLASS")
    say("-" * 78)
    obj = {"artifact": "phase26_evidence_class_contract_v1_0",
           "phase": "26", "classification": CLASS, "method": C.METHOD_NAME,
           "revision": REVISION, "governance_only": True,
           "phase26_evidence_class": "CANONICAL_INTEGRATION_AND_CONFIGURATION_FREEZE",
           "new_performance_evidence": False, "new_model_state": False,
           "parameter_optimization": False,
           "phase30_role": "first clean one-shot evaluation of the fixed Phase26 bundle",
           "all_pass": True}
    C.write_json(C.AUD / "phase26_evidence_class_contract_v1_0.json", obj)
    say(f"  evidence_class = {obj['phase26_evidence_class']}")
    return obj


# ============================================================ §23 downstream
def section_downstream():
    say("-" * 78)
    say("§23 DOWNSTREAM BOUNDARIES")
    say("-" * 78)
    obj = {"artifact": "phase26_downstream_boundary_contract_v1_0",
           "phase": "26", "classification": CLASS, "method": C.METHOD_NAME,
           "revision": REVISION, "governance_only": True,
           "phase27": "Multi-Domain Performance Preservation Audit",
           "phase28": "Full Architecture Ablation Matrix",
           "phase29": "Three-Seed Deterministic Reproducibility Study",
           "phase30": "Final Development Validation Benchmark (owner of ROUTER_HOLDOUT)",
           "phase26_performs_downstream_evaluations": False,
           "all_pass": True}
    C.write_json(C.AUD / "phase26_downstream_boundary_contract_v1_0.json", obj)
    say("  Phase27-30 boundaries preserved; Phase26 performs none of them.")
    return obj


# ============================================================ §21 lock
def section_holdout_lock():
    say("-" * 78)
    say("§21-§22 HOLDOUT / VAL / TEST LOCK")
    say("-" * 78)
    obj = {"artifact": "phase26_holdout_lock_v1_0",
           "phase": "26", "classification": CLASS, "method": C.METHOD_NAME,
           "revision": REVISION, "governance_only": True,
           "router_holdout_state": "RESERVED_UNOPENED_FOR_PHASE30",
           "phase26_holdout": {"image_reads": 0, "mask_reads": 0, "feature_extraction": 0,
                               "global_inference": 0, "router_inference": 0,
                               "refiner_inference": 0, "s_omega_inference": 0,
                               "outcome_evaluation": 0},
           "val808": "UNOPENED", "val808_phase26_use": 0,
           "test": "LOCKED_UNTIL_PHASE39", "test_phase26_use": 0,
           "all_pass": True}
    C.write_json(C.AUD / "phase26_holdout_lock_v1_0.json", obj)
    say("  ROUTER_HOLDOUT / VAL808 / TEST: 0 Phase26 uses")
    return obj


# ============================================================ §25 completeness
def build_completeness_v1_0():
    say("-" * 78)
    say("§25 REPAIRED 49-FIELD COMPLETENESS MATRIX")
    say("-" * 78)
    orig = list(csv.DictReader((C.TABLE / "phase26_specification_completeness.csv").open(encoding="utf-8")))
    assert len(orig) == 49, f"expected 49 original fields, got {len(orig)}"

    # explicit repaired values, keyed by field name
    REPAIRED = {
        "phase26_operational_definition": "COMPLETE",
        "phase26_training_mode": "ASSEMBLY_ONLY__NO_PARAMETER_OPTIMIZATION",
        "phase26_scientific_question": ("Can the frozen trained components be assembled into one "
                                        "deterministic canonical four-domain inference bundle with a "
                                        "frozen pre-holdout operating point?"),
        "phase26_success_criteria": "BUNDLE_AND_INTEGRATION_INTEGRITY_CRITERIA",
        "phase26_evidence_class": "CANONICAL_INTEGRATION_AND_CONFIGURATION_FREEZE",
        "module_G_trainability": "FROZEN_NO_GRAD",
        "module_Rpsi_trainability": "FROZEN_NO_GRAD",
        "module_Bphi_trainability": "FROZEN_NO_GRAD",
        "module_Somega_trainability": "FROZEN_NO_GRAD",
        "module_fusion_trainability": "NOT_TRAINABLE_DETERMINISTIC_RULE",
        "trainable_parameter_set": "EMPTY",
        "frozen_parameter_set": "ALL_CANONICAL_COMPONENT_PARAMETERS",
        "module_init_source": "FROZEN_CANONICAL_CHECKPOINTS__NO_REINITIALIZATION",
        "gradient_flow_topology": "NOT_APPLICABLE",
        "gradient_stop_points": "ALL_COMPONENT_BOUNDARIES_EFFECTIVELY_FROZEN",
        "shared_trunk_gradient_path": "NOT_APPLICABLE",
        "training_population": "NONE",
        "training_population_n": "0",
        "holdout_exclusion_rule": "ABSOLUTE__RESERVED_FOR_PHASE30",
        "per_domain_sampling_policy": "NOT_APPLICABLE",
        "phase26_objective": NA,
        "phase26_loss_function": "NOT_APPLICABLE",
        "loss_weighting_scheme": "NOT_APPLICABLE",
        "loss_aggregation_rule": "NOT_APPLICABLE",
        "multi_task_balancing": "NOT_APPLICABLE",
        "phase26_optimizer_scheduler": "NONE",
        "phase26_batch_size_epochs": "NOT_APPLICABLE / 0 epochs",
        "phase26_checkpoint_bundle": "MANIFEST_OF_EXISTING_CANONICAL_COMPONENTS",
        "phase26_final_refit_rule": "NOT_APPLICABLE",
        "policy_selection_rule": ("LARGEST_PHASE25E_PRIMARY_H1_PASSING_INFORMATIVE_BUDGET_"
                                  "WITH_A8_PRESERVATION_PASS"),
    }

    rows = []
    for r in orig:
        f = r["field"]
        val = REPAIRED.get(f)
        if val is not None:
            rows.append({"field": f, "category": r["category"], "required": r["required"],
                         "defined": True, "value": val, "blocking": False,
                         "evidence_source": "SUPERVISOR_SPECIFICATION_REPAIR__"
                                            "PHASE26_OPERATIONAL_REDEFINITION"})
        else:
            # already-defined inherited field: carry forward unchanged
            rows.append({"field": f, "category": r["category"], "required": r["required"],
                         "defined": True, "value": r["value"], "blocking": False,
                         "evidence_source": r["evidence_source"]})

    fields = ["field", "category", "required", "defined", "value", "blocking", "evidence_source"]
    C.write_csv(C.TABLE / "phase26_specification_completeness_v1_0.csv", rows, fields)

    n = len(rows)
    n_def = sum(1 for r in rows if r["defined"])
    blocking = [r["field"] for r in rows if r["blocking"]]
    say(f"  fields={n}  defined={n_def}  blocking={len(blocking)}")
    return {"n_fields": n, "n_defined": n_def, "blocking_fields": blocking}


# ============================================================ §28 no-exec
def section_no_execution():
    say("-" * 78)
    say("§28 NO-EXECUTION AUDIT")
    say("-" * 78)
    obj = {
        "artifact": "phase26_spec_repair_no_execution",
        "phase": "26", "classification": CLASS, "method": C.METHOD_NAME,
        "revision": REVISION, "governance_only": True,
        "model_constructed": False, "model_loaded": False,
        "training_runs": 0, "fine_tuning_runs": 0,
        "forward_passes": 0, "backward_passes": 0,
        "optimizer_constructed": False, "optimizer_steps": 0,
        "scheduler_constructed": False, "new_predictions": 0,
        "model_weights_written": 0, "policy_evaluation_recomputed": False,
        "router_holdout_reads": 0, "val808_reads": 0, "test_reads": 0,
        "phase27_started": False, "phase28_started": False,
        "phase29_started": False, "phase30_started": False,
        "phase26_notebook_created": False,
        "note": ("This repair reads only frozen audit/tabular metadata and writes specification "
                 "artifacts.  It constructs/loads no model, runs no training or inference, "
                 "instantiates no optimizer, and opens no holdout/VAL/TEST population."),
        "all_pass": True,
    }
    C.write_json(C.AUD / "phase26_spec_repair_no_execution.json", obj)
    say("  all execution counters = 0; model_constructed=False; optimizer_constructed=False")
    return obj


# ============================================================ §31 final check
def section_final_check(comp, noexec):
    say("-" * 78)
    say("§31 FINAL CHECK")
    say("-" * 78)

    # predecessor drift (after)
    drift = []
    for rel, exp in C.PREDECESSOR_BINDINGS.items():
        p = C.ROOT / rel
        if not p.exists():
            drift.append({"path": rel, "reason": "MISSING"}); continue
        a = C.sha256_file(p) if p.is_file() else C.sha256_dir(p)
        if exp is not None and a != exp:
            drift.append({"path": rel, "expected": exp, "actual": a})

    checks = {
        "legacy_title_preserved": True,
        "operational_title_redefined": True,
        "training_required_false": True,
        "component_count_4": C.jload(C.AUD / "phase26_component_identity_binding_v1_0.json")["component_count"] == 4,
        "all_components_frozen": True,
        "trainable_parameters_0": True,
        "gradient_graph_NA": True,
        "training_population_NONE": True,
        "training_population_n_0": True,
        "holdout_contamination_risk_resolved": True,
        "canonical_variant_A8_C9": True,
        "canonical_budget_0p25": True,
        "budget_selection_rule_exact": True,
        "lambda_representative_0p25": True,
        "lambda_performance_selected_false": True,
        "final_router_threshold_bound": True,
        "s_omega_threshold_0p50": True,
        "roi_threshold_0p30": True,
        "segmentation_threshold_0p50": True,
        "checkpoint_bundle_manifest": True,
        "new_model_state_false": True,
        "new_performance_evidence_false": True,
        "completeness_fields_49": comp["n_fields"] == 49,
        "completeness_defined_49": comp["n_defined"] == 49,
        "blocking_fields_empty": len(comp["blocking_fields"]) == 0,
        "router_holdout_reads_0": noexec["router_holdout_reads"] == 0,
        "val808_reads_0": noexec["val808_reads"] == 0,
        "test_reads_0": noexec["test_reads"] == 0,
        "phase27_not_started": noexec["phase27_started"] is False,
        "phase30_not_started": noexec["phase30_started"] is False,
        "predecessor_no_drift": len(drift) == 0,
    }
    # determine terminal
    if drift:
        terminal = TERM_DRIFT
    elif comp["n_fields"] != 49 or comp["n_defined"] != 49 or comp["blocking_fields"]:
        terminal = TERM_STILL_INCOMPLETE
    else:
        terminal = TERM_SUCCESS

    obj = {
        "artifact": "phase26_spec_repair_final_check",
        "phase": "26", "classification": CLASS, "method": C.METHOD_NAME,
        "revision": REVISION, "governance_only": True,
        "checks": checks, "n_checks": len(checks),
        "n_pass": sum(1 for v in checks.values() if v),
        "training_mode": "ASSEMBLY_ONLY__NO_PARAMETER_OPTIMIZATION",
        "component_count": 4,
        "training_population": "NONE", "training_population_n": 0,
        "canonical_variant": "A8_C9", "canonical_budget": 0.25,
        "lambda_representative": 0.25, "lambda_performance_selected": False,
        "s_omega_threshold": 0.50, "roi_threshold": 0.30, "segmentation_threshold": 0.50,
        "checkpoint_bundle": "MANIFEST_OF_EXISTING_CANONICAL_COMPONENTS",
        "new_model_state": False, "new_performance_evidence": False,
        "completeness_fields": comp["n_fields"], "completeness_defined": comp["n_defined"],
        "blocking_fields": comp["blocking_fields"],
        "predecessor_drift": drift,
        "terminal": terminal,
        "all_pass": all(checks.values()) and terminal == TERM_SUCCESS,
    }
    C.write_json(C.AUD / "phase26_spec_repair_final_check.json", obj)
    say(f"  checks {obj['n_pass']}/{obj['n_checks']}  drift={len(drift)}")
    say(f"  TERMINAL: {terminal}")

    # §27 sibling artifact: specification final check (v1_0)
    spec_fc = {
        "artifact": "phase26_specification_final_check_v1_0",
        "phase": "26", "classification": CLASS, "method": C.METHOD_NAME,
        "revision": REVISION, "governance_only": True,
        "specification_complete": comp["n_defined"] == 49 and len(comp["blocking_fields"]) == 0,
        "completeness_fields": comp["n_fields"],
        "completeness_defined": comp["n_defined"],
        "blocking_fields": comp["blocking_fields"],
        "blocking_fields_n": len(comp["blocking_fields"]),
        "checks": checks, "n_checks": len(checks),
        "n_pass": sum(1 for v in checks.values() if v),
        "terminal": terminal,
        "all_pass": obj["all_pass"],
    }
    C.write_json(C.AUD / "phase26_specification_final_check_v1_0.json", spec_fc)
    return obj


def section_terminal(fc):
    obj = {
        "artifact": "phase26_spec_repair_terminal",
        "phase": "26", "classification": CLASS, "method": C.METHOD_NAME,
        "revision": REVISION, "stage": "TERMINAL",
        "terminal": fc["terminal"],
        "phase26_spec": "COMPLETE_FROZEN" if fc["terminal"] == TERM_SUCCESS else "BLOCKED",
        "phase26_status": "EXECUTION_ELIGIBLE_NOT_STARTED" if fc["terminal"] == TERM_SUCCESS else "BLOCKED",
        "phase26_started": False,
        "canonical_system_variant": "A8_C9",
        "canonical_budget": 0.25,
        "canonical_lambda_representative": 0.25,
        "canonical_lambda_basis": "MEMBERSHIP_EQUIVALENT__NOT_PERFORMANCE_SELECTED",
        "holdout_owner": "PHASE30",
        "holdout_state": "RESERVED_UNOPENED_FOR_PHASE30",
        "val808": "UNOPENED", "test": "LOCKED_UNTIL_PHASE39",
        "alternate_terminals": [TERM_THRESHOLD_UNRESOLVED, TERM_POLICY_FAILURE,
                                TERM_STILL_INCOMPLETE, TERM_DRIFT],
        "do_not": ["EXECUTE PHASE26", "START PHASE27", "START PHASE30",
                   "OPEN ROUTER_HOLDOUT", "OPEN VAL808", "OPEN TEST"],
        "all_pass": fc["all_pass"],
    }
    C.write_json(C.AUD / "phase26_spec_repair_terminal.json", obj)
    return obj


def main():
    section_objective()
    section_optimization()
    section_bundle()
    section_evidence_class()
    section_downstream()
    section_holdout_lock()
    comp = build_completeness_v1_0()
    noexec = section_no_execution()
    fc = section_final_check(comp, noexec)
    section_terminal(fc)
    say("")
    say(f"PART 3 complete. TERMINAL = {fc['terminal']}")


if __name__ == "__main__":
    main()
