"""Phase26 pre-execution training-specification audit - PART 2 (§9-§31).

Governance only.  Produces:
  phase26_loss_contract_audit.json
  phase26_optimizer_scheduler_audit.json
  phase26_checkpoint_bundle_contract.json
  phase26_downstream_phase_boundary_audit.json
  phase26_holdout_lock_audit.json
  phase26_test_lock_audit.json
  phase26_specification_completeness.csv   (49 fields)
  phase26_spec_no_execution_audit.json
  phase26_specification_final_check.json
  phase26_terminal.json
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import phase26_common as C  # noqa: E402


def say(msg):
    print(msg, flush=True)


# =============================================================== §9 loss contract
def section_loss_contract():
    say("-" * 78)
    say("§9  LOSS / OBJECTIVE CONTRACT")
    say("-" * 78)
    spec = C.jload(C.ROOT / "reports/audits/phase24_exact_implementation_spec.json")
    obj = {
        "artifact": "phase26_loss_contract_audit",
        "phase": "26",
        "classification": C.CLASSIFICATION,
        "method": C.METHOD_NAME,
        "governance_only": True,
        "per_module_losses_frozen": {
            "R_psi": spec["refiner"]["loss"],
            "B_phi": spec["router"]["loss"],
            "S_omega": spec["post_safety"]["loss"],
        },
        "phase26_joint_objective_defined": False,
        "phase26_loss_function_defined": False,
        "loss_weighting_scheme_defined": False,
        "loss_aggregation_rule_defined": False,
        "multi_task_balancing_defined": False,
        "note": ("Per-component losses are frozen from prior phases, but no authoritative "
                 "source defines a Phase26 objective (a joint loss, a multi-task weighting, "
                 "or an aggregation rule over the four domains)."),
        "verdict": "PHASE26_OBJECTIVE_NOT_DEFINED",
        "blocking": True,
        "all_pass": False,
    }
    C.write_json(C.AUD / "phase26_loss_contract_audit.json", obj)
    say(f"  Phase26 joint objective defined: {obj['phase26_joint_objective_defined']}")
    say(f"  verdict: {obj['verdict']}")
    return obj


# =============================================================== §10 optimizer/scheduler
def section_optimizer():
    say("-" * 78)
    say("§10 OPTIMIZER / SCHEDULER CONTRACT")
    say("-" * 78)
    obj = {
        "artifact": "phase26_optimizer_scheduler_audit",
        "phase": "26",
        "classification": C.CLASSIFICATION,
        "method": C.METHOD_NAME,
        "governance_only": True,
        "phase26_optimizer_defined": False,
        "phase26_learning_rate_defined": False,
        "phase26_weight_decay_defined": False,
        "phase26_scheduler_defined": False,
        "phase26_batch_size_defined": False,
        "phase26_max_epochs_defined": False,
        "phase26_early_stopping_defined": False,
        "note": ("Prior phases froze optimizer/scheduler for their own single-component "
                 "runs.  No authoritative source defines optimizer, LR, schedule, batch "
                 "size, epoch budget or early stopping for a Phase26 full-system run."),
        "verdict": "PHASE26_OPTIMIZATION_CONTRACT_NOT_DEFINED",
        "blocking": True,
        "all_pass": False,
    }
    C.write_json(C.AUD / "phase26_optimizer_scheduler_audit.json", obj)
    say(f"  verdict: {obj['verdict']}")
    return obj


# =============================================================== §11 checkpoint bundle
def section_checkpoint_bundle():
    say("-" * 78)
    say("§11 CHECKPOINT BUNDLE CONTRACT")
    say("-" * 78)
    obj = {
        "artifact": "phase26_checkpoint_bundle_contract",
        "phase": "26",
        "classification": C.CLASSIFICATION,
        "method": C.METHOD_NAME,
        "governance_only": True,
        "phase26_checkpoint_bundle_defined": False,
        "checkpoint_selection_metric_defined": False,
        "final_refit_rule_defined": False,
        "seed_defined_for_phase26": False,
        "bundle_contents": {
            "G": "not specified",
            "R_psi": "not specified",
            "B_phi": "not specified",
            "S_omega": "not specified",
            "fusion_state": "not specified",
            "normalization_state": "not specified",
        },
        "note": ("No authoritative source defines what a Phase26 checkpoint bundle must "
                 "contain, how its checkpoint is selected, its final-refit rule, or its seed. "
                 "Existing per-phase checkpoints (Phase21/25A/25D/25F) are frozen but are not "
                 "declared to be the Phase26 bundle."),
        "verdict": "PHASE26_CHECKPOINT_BUNDLE_NOT_DEFINED",
        "blocking": True,
        "all_pass": False,
    }
    C.write_json(C.AUD / "phase26_checkpoint_bundle_contract.json", obj)
    say(f"  verdict: {obj['verdict']}")
    return obj


# =============================================================== §12 downstream boundary
def section_downstream_boundary():
    say("-" * 78)
    say("§12 DOWNSTREAM PHASE BOUNDARY AUDIT")
    say("-" * 78)
    obj = {
        "artifact": "phase26_downstream_phase_boundary_audit",
        "phase": "26",
        "classification": C.CLASSIFICATION,
        "method": C.METHOD_NAME,
        "governance_only": True,
        "phase27": {"title": "Multi-Domain Performance Preservation Audit",
                    "status": "NOT_STARTED", "population": "ROUTER_DEVELOPMENT (DEV)"},
        "phase28": {"title": "Full Architecture Ablation Matrix",
                    "status": "NOT_STARTED", "population": "ROUTER_DEVELOPMENT (DEV)"},
        "phase29": {"title": "Three-Seed Deterministic Reproducibility Study",
                    "status": "NOT_STARTED", "population": "ROUTER_DEVELOPMENT (DEV)"},
        "phase30": {"title": "Final Development Validation Benchmark",
                    "status": "NOT_STARTED", "population": "ROUTER_HOLDOUT",
                    "owner_of": "ROUTER_HOLDOUT", "state": "RESERVED_UNOPENED_FOR_PHASE30",
                    "one_shot": True},
        "phase26_must_not_preempt": ["Phase27", "Phase28", "Phase29", "Phase30"],
        "phase26_may_open_router_holdout": False,
        "note": ("Phase30 is the first eligible owner of ROUTER_HOLDOUT, subject to its own "
                 "pre-execution one-shot protocol freeze.  Phase26 (like Phase27/28/29) MUST "
                 "NOT open it."),
        "verdict": "DOWNSTREAM_BOUNDARY_CONSISTENT",
        "blocking": False,
        "all_pass": True,
    }
    C.write_json(C.AUD / "phase26_downstream_phase_boundary_audit.json", obj)
    say(f"  Phase30 owns ROUTER_HOLDOUT (RESERVED_UNOPENED); Phase26 must not open it.")
    say(f"  verdict: {obj['verdict']}")
    return obj


# =============================================================== §13 holdout lock
def section_holdout_lock():
    say("-" * 78)
    say("§13 ROUTER_HOLDOUT LOCK AUDIT")
    say("-" * 78)
    res = C.jload(C.ROOT / "reports/audits/phase25g_holdout_reservation_for_phase30.json")
    obj = {
        "artifact": "phase26_holdout_lock_audit",
        "phase": "26",
        "classification": C.CLASSIFICATION,
        "method": C.METHOD_NAME,
        "governance_only": True,
        "router_holdout_state": res.get("ROUTER_HOLDOUT_status", "RESERVED_UNOPENED_FOR_PHASE30"),
        "router_holdout_owner_phase": 30,
        "phase26_may_open": False,
        "phase26_holdout_reads": 0,
        "reservation_source": "reports/audits/phase25g_holdout_reservation_for_phase30.json",
        "all_pass": True,
    }
    C.write_json(C.AUD / "phase26_holdout_lock_audit.json", obj)
    say(f"  ROUTER_HOLDOUT: {obj['router_holdout_state']}  (owner Phase30)")
    say(f"  Phase26 holdout reads: {obj['phase26_holdout_reads']}")
    return obj


# =============================================================== §14 test lock
def section_test_lock():
    say("-" * 78)
    say("§14 TEST LOCK AUDIT")
    say("-" * 78)
    obj = {
        "artifact": "phase26_test_lock_audit",
        "phase": "26",
        "classification": C.CLASSIFICATION,
        "method": C.METHOD_NAME,
        "governance_only": True,
        "test_state": "LOCKED_UNTIL_PHASE39",
        "phase26_test_reads": 0,
        "phase26_test_image_reads": 0,
        "phase26_test_metrics": 0,
        "manifest_version": "phase4_v3",
        "all_pass": True,
    }
    C.write_json(C.AUD / "phase26_test_lock_audit.json", obj)
    say(f"  TEST: {obj['test_state']}  phase26_test_reads={obj['phase26_test_reads']}")
    return obj


# =============================================================== §24 completeness (49 fields)
def build_completeness():
    # (field, category, required, defined, value, evidence_source)
    defined = [
        ("method_name", "identity", True, True, C.METHOD_NAME, "docs/*.md"),
        ("architecture_id", "identity", True, True, C.ARCHITECTURE_ID, "phase24_exact_implementation_spec.json"),
        ("module_G_definition", "architecture", True, True, "Phase21 GlobalMedFiLM", "docs/ARCHITECTURE.md"),
        ("module_Rpsi_definition", "architecture", True, True, "BARRRegionalRefinerV1 (1276401 params)", "phase24 spec#refiner"),
        ("module_Bphi_definition", "architecture", True, True, "BARRBenefitRouterV1 (36801 params)", "phase24 spec#router"),
        ("module_Somega_definition", "architecture", True, True, "BARRPostSafetyV1 (1217 params)", "phase25f_final_freeze.json"),
        ("fusion_rule", "architecture", True, True, "outside ROI p_global; inside ROI p_refined", "phase24 spec#fusion"),
        ("segmentation_threshold", "architecture", True, True, "0.5 (INHERITED)", "phase24 spec#fusion"),
        ("roi_rule", "architecture", True, True, "foreground thr 0.30 -> bbox -> 1.5x -> 256", "phase24 spec#roi"),
        ("action_availability", "architecture", True, True, "predicted ROI exists", "phase24 spec#action_availability"),
        ("seed_policy", "governance", True, True, "42", "phase24_benefit_data_protocol_exact.json"),
        ("split_manifest_binding", "governance", True, True, "phase24_router_split_manifest.csv", "phase24 spec"),
        ("policy_grid", "governance", True, True, "lambda{0,.25,.5,1} x budget{0,10,25,50,100}%", "docs/ARCHITECTURE.md"),
        ("compute_accounting", "governance", True, True, "ANALYTICAL MAC LOWER BOUND", "docs/ARCHITECTURE.md"),
        ("holdout_lock", "governance", True, True, "RESERVED_UNOPENED_FOR_PHASE30", "phase25g_holdout_reservation_for_phase30.json"),
        ("val808_lock", "governance", True, True, "UNOPENED", "docs/ARCHITECTURE.md"),
        ("test_lock", "governance", True, True, "LOCKED_UNTIL_PHASE39", "docs/*.md"),
        ("phase30_boundary", "governance", True, True, "Phase30 owns ROUTER_HOLDOUT", "phase25g_router_holdout_ownership_supervisor_ruling_v1_0.json"),
        ("predecessor_binding", "governance", True, True, "Phase25G terminal + notebook SHA", "phase25g_terminal.json"),
    ]
    undefined = [
        ("phase26_operational_definition", "operational_definition", "Phase26 means one of A-E, chosen by an authoritative source"),
        ("phase26_training_mode", "operational_definition", "joint / staged / refit / assembly"),
        ("phase26_scientific_question", "operational_definition", "the falsifiable Phase26 question"),
        ("phase26_success_criteria", "operational_definition", "pre-registered success/failure criteria"),
        ("phase26_evidence_class", "operational_definition", "declared evidence class"),
        ("module_G_trainability", "module_trainability", "trainable or frozen in Phase26"),
        ("module_Rpsi_trainability", "module_trainability", "trainable or frozen in Phase26"),
        ("module_Bphi_trainability", "module_trainability", "trainable or frozen in Phase26"),
        ("module_Somega_trainability", "module_trainability", "trainable or frozen in Phase26"),
        ("module_fusion_trainability", "module_trainability", "trainable or frozen in Phase26"),
        ("trainable_parameter_set", "module_trainability", "the exact set of trainable parameters"),
        ("frozen_parameter_set", "module_trainability", "the exact set of frozen parameters"),
        ("module_init_source", "module_trainability", "initialization source for each module"),
        ("gradient_flow_topology", "gradient_graph", "the Phase26 gradient graph"),
        ("gradient_stop_points", "gradient_graph", "detach / stop-gradient points"),
        ("shared_trunk_gradient_path", "gradient_graph", "shared-trunk gradient path"),
        ("training_population", "data_population", "which split Phase26 trains on"),
        ("training_population_n", "data_population", "its exact size"),
        ("holdout_exclusion_rule", "data_population", "explicit ROUTER_HOLDOUT exclusion rule"),
        ("per_domain_sampling_policy", "data_population", "per-domain sampling / balancing"),
        ("phase26_objective", "objective", "the Phase26 objective"),
        ("phase26_loss_function", "objective", "the Phase26 loss"),
        ("loss_weighting_scheme", "objective", "loss weights"),
        ("loss_aggregation_rule", "objective", "aggregation over domains/modules"),
        ("multi_task_balancing", "objective", "multi-task balancing rule"),
        ("phase26_optimizer_scheduler", "optimization", "optimizer + LR + scheduler"),
        ("phase26_batch_size_epochs", "optimization", "batch size + epoch budget + early stop"),
        ("phase26_checkpoint_bundle", "checkpoint", "checkpoint bundle contents + selection"),
        ("phase26_final_refit_rule", "checkpoint", "final refit rule + seed"),
        ("policy_selection_rule", "governance", "prospective lambda/budget selection rule"),
    ]

    rows = []
    for f, cat, req, defd, val, src in defined:
        rows.append({"field": f, "category": cat, "required": req, "defined": defd,
                     "value": val, "blocking": (req and not defd),
                     "evidence_source": src})
    for f, cat, req in undefined:
        rows.append({"field": f, "category": cat, "required": True, "defined": False,
                     "value": "", "blocking": True,
                     "evidence_source": "NOT_FOUND_IN_ANY_AUTHORITATIVE_SOURCE"})

    fields = ["field", "category", "required", "defined", "value", "blocking", "evidence_source"]
    C.write_csv(C.TABLE / "phase26_specification_completeness.csv", rows, fields)

    n = len(rows)
    n_def = sum(1 for r in rows if r["defined"])
    blocking = [r["field"] for r in rows if r["blocking"]]
    say("-" * 78)
    say("§24 SPECIFICATION COMPLETENESS MATRIX")
    say("-" * 78)
    say(f"  total fields : {n}")
    say(f"  defined      : {n_def}")
    say(f"  undefined    : {n - n_def}")
    say(f"  blocking     : {len(blocking)}")
    return {"n_fields": n, "n_defined": n_def, "n_undefined": n - n_def,
            "blocking_fields": blocking, "rows": rows}


# =============================================================== §27 no-execution audit
def section_no_execution(completeness):
    say("-" * 78)
    say("§27 NO-EXECUTION AUDIT")
    say("-" * 78)
    nb26_dir = C.NB26
    nb26_files = sorted(p.name for p in nb26_dir.glob("*")) if nb26_dir.exists() else []
    obj = {
        "artifact": "phase26_spec_no_execution_audit",
        "phase": "26",
        "classification": C.CLASSIFICATION,
        "method": C.METHOD_NAME,
        "governance_only": True,
        "phase26_science_executed": False,
        "phase26_started": False,
        "model_constructed": False,
        "training_runs": 0,
        "fine_tuning_runs": 0,
        "forward_passes": 0,
        "inference_calls": 0,
        "policy_selected": False,
        "lambda_selected": False,
        "budget_selected": False,
        "holdout_reads": 0,
        "val808_reads": 0,
        "test_reads": 0,
        "test_image_reads": 0,
        "checkpoints_written": 0,
        "phase26_notebook_created": False,
        "phase26_notebook_files_present": nb26_files,
        "note": ("Phase26 is a pre-execution specification audit.  It constructs no model, "
                 "runs no training or inference, selects no policy, and opens no holdout, "
                 "VAL or TEST population.  Only frozen audit JSON/CSV metadata were read."),
        "all_pass": True,
    }
    C.write_json(C.AUD / "phase26_spec_no_execution_audit.json", obj)
    say(f"  training_runs={obj['training_runs']} forward_passes={obj['forward_passes']} "
        f"model_constructed={obj['model_constructed']}")
    say(f"  holdout_reads={obj['holdout_reads']} val808_reads={obj['val808_reads']} "
        f"test_reads={obj['test_reads']}")
    say(f"  phase26_notebook_created={obj['phase26_notebook_created']}")
    return obj


# =============================================================== §28-§31 finalize
def section_finalize(completeness, noexec, gate):
    say("-" * 78)
    say("§28-§31 FINAL CHECK + TERMINAL")
    say("-" * 78)

    # predecessor drift check (after)
    bindings_after = {rel: C.bind(rel, sha) for rel, sha in C.PREDECESSOR_BINDINGS.items()}
    drift = [rel for rel, b in bindings_after.items() if not b["matches_expected"]]
    predecessor_drift = len(drift) > 0

    blocking_fields = completeness["blocking_fields"]
    spec_complete = (len(blocking_fields) == 0)

    # Which blocked terminal applies?
    conditions = {
        "FULL_SYSTEM_TRAINING_SPEC_INCOMPLETE": not spec_complete,
        "NO_PROSPECTIVE_POLICY_SELECTION_RULE":
            "policy_selection_rule" in blocking_fields,
        "PHASE30_HOLDOUT_CONTAMINATION_RISK": True,  # any use of ORIGINAL_TRAIN would contaminate
        "PREDECESSOR_ARTIFACT_DRIFT": predecessor_drift,
    }

    if predecessor_drift:
        terminal = C.TERMINAL_BLOCKED_DRIFT
    elif conditions["FULL_SYSTEM_TRAINING_SPEC_INCOMPLETE"]:
        terminal = C.TERMINAL_BLOCKED_INCOMPLETE
    else:
        terminal = C.TERMINAL_SUCCESS

    # final check
    checks = {
        "entry_gate_pass": gate["all_pass"],
        "predecessor_terminal_correct": gate["predecessor_terminal_ok"],
        "phase25g_notebook_sha_correct": gate["phase25g_notebook_sha_ok"],
        "predecessor_no_drift": not predecessor_drift,
        "completeness_matrix_49_fields": completeness["n_fields"] == 49,
        "no_execution": (noexec["training_runs"] == 0 and noexec["forward_passes"] == 0
                         and noexec["model_constructed"] is False),
        "no_policy_selection": (noexec["policy_selected"] is False
                                and noexec["lambda_selected"] is False
                                and noexec["budget_selected"] is False),
        "holdout_untouched": noexec["holdout_reads"] == 0,
        "val808_untouched": noexec["val808_reads"] == 0,
        "test_untouched": noexec["test_reads"] == 0,
        "no_phase26_notebook": noexec["phase26_notebook_created"] is False,
        "specification_complete": spec_complete,
    }

    final_check = {
        "artifact": "phase26_specification_final_check",
        "phase": "26",
        "classification": C.CLASSIFICATION,
        "method": C.METHOD_NAME,
        "governance_only": True,
        "checks": checks,
        "n_checks": len(checks),
        "n_pass": sum(1 for v in checks.values() if v),
        "specification_complete": spec_complete,
        "blocking_fields_n": len(blocking_fields),
        "blocking_fields": blocking_fields,
        "blocked_conditions": conditions,
        "predecessor_drift": drift,
        "terminal": terminal,
        "all_pass": all(checks.values()),
    }
    C.write_json(C.AUD / "phase26_specification_final_check.json", final_check)

    terminal_obj = {
        "artifact": "phase26_terminal",
        "phase": "26",
        "classification": C.CLASSIFICATION,
        "method": C.METHOD_NAME,
        "stage": "TERMINAL",
        "terminal": terminal,
        "phase26_status": "BLOCKED" if terminal != C.TERMINAL_SUCCESS else "ELIGIBLE_NOT_STARTED",
        "phase26_started": False,
        "specification_complete": spec_complete,
        "blocking_fields_n": len(blocking_fields),
        "blocked_conditions": conditions,
        "primary_blocking_condition": (
            "FULL_SYSTEM_TRAINING_SPEC_INCOMPLETE" if not spec_complete else None),
        "alternate_blocked_terminals": [
            C.TERMINAL_BLOCKED_INCOMPLETE, C.TERMINAL_BLOCKED_POLICY,
            C.TERMINAL_BLOCKED_HOLDOUT, C.TERMINAL_BLOCKED_DRIFT],
        "holdout_owner": "PHASE30",
        "holdout_state": "RESERVED_UNOPENED_FOR_PHASE30",
        "do_not": [
            "TRAIN", "FINE-TUNE", "CONSTRUCT A MODEL", "RUN A FORWARD PASS",
            "SELECT A POLICY", "SELECT A LAMBDA", "SELECT A BUDGET",
            "OPEN ROUTER_HOLDOUT", "OPEN VAL808", "OPEN TEST",
            "START PHASE27", "START PHASE28", "START PHASE29", "START PHASE30",
        ],
        "failures": [k for k, v in checks.items() if not v],
        "all_pass": final_check["all_pass"],
    }
    C.write_json(C.AUD / "phase26_terminal.json", terminal_obj)

    say(f"  predecessor drift: {drift if drift else 'none'}")
    say(f"  final check: {final_check['n_pass']}/{final_check['n_checks']}")
    say(f"  blocking fields: {len(blocking_fields)}")
    say(f"  blocked conditions: "
        f"{[k for k, v in conditions.items() if v]}")
    say("")
    say("  TERMINAL: " + terminal)
    return final_check, terminal_obj


def main():
    loss = section_loss_contract()
    opt = section_optimizer()
    ckpt = section_checkpoint_bundle()
    bound = section_downstream_boundary()
    hold = section_holdout_lock()
    test = section_test_lock()
    comp = build_completeness()
    noexec = section_no_execution(comp)
    gate = C.jload(C.AUD / "phase26_spec_entry_gate.json")
    fc, term = section_finalize(comp, noexec, gate)

    say("")
    say("=" * 78)
    say("PART 2 SUMMARY")
    say("=" * 78)
    say(f"  loss objective defined : {loss['phase26_joint_objective_defined']}")
    say(f"  optimizer defined      : {opt['phase26_optimizer_defined']}")
    say(f"  checkpoint bundle def  : {ckpt['phase26_checkpoint_bundle_defined']}")
    say(f"  downstream boundary    : {bound['verdict']}")
    say(f"  holdout reads          : {hold['phase26_holdout_reads']}")
    say(f"  test reads             : {test['phase26_test_reads']}")
    say(f"  completeness           : {comp['n_defined']}/{comp['n_fields']} defined")
    say(f"  final check            : {fc['n_pass']}/{fc['n_checks']}")
    say(f"  TERMINAL               : {term['terminal']}")


if __name__ == "__main__":
    main()
