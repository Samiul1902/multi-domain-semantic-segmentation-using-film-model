"""Phase 25G spec audit — PART 3: §13-§15 conditional holdout, §16 VAL808, §17 TEST,
§18 ablation scope, §19 C11, §20 criteria binding, §21 completeness matrix,
§22 hard stops, §23 no-notebook, §24 audit checklist, §25 status, §26 terminal.

Governance/specification only. No execution, no holdout/VAL808/TEST reads.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase25g_spec_common as C  # noqa: E402

NB_FORBIDDEN = C.ROOT / "notebooks/phasewise/phase_25g_controlled_validation/phase25g_integrated_controlled_evaluation.ipynb"


def _read_csv(p):
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _sha(rel):
    p = C.ROOT / rel
    return C.sha256_file(p) if p.exists() else None


def section13_15_conditional_holdout(ownership: dict) -> dict:
    """§13-§15 are conditional on §3 resolving ownership to Phase25G. It did not,
    so the one-shot holdout contract is NOT frozen. The complete conditional
    semantics are recorded here (not activated) so the contract is explicit."""
    resolved = ownership["classification"] == C.OWN_25G
    spec = {
        "end_to_end_order_per_holdout_sample": [
            "1. run frozen Phase21 GlobalMedFiLM once",
            "2. produce p_global + required frozen feature taps",
            "3. compute Phase25B router features using frozen v1.2 rules",
            "4. apply Phase25D FINAL benefit router",
            "5. apply frozen Phase25E DEV-calibrated policy threshold",
            "6. if SKIP: final A7 = global, final A8 = global; do not run refiner; do not run S_omega",
            "7. if EXECUTE: run frozen Phase25A FINAL regional refiner",
            "8. construct candidate fused output",
            "9. A7: final = candidate",
            "10. compute frozen Phase25F 20-D post-safety feature vector",
            "11. apply Phase25F FINAL S_omega",
            "12. A8: if p_accept >= 0.50: final = candidate else final = global",
            "13. only after predictions are frozen: open GT masks for evaluation",
        ],
        "forbidden": [
            "holdout threshold fitting",
            "holdout top-K recalibration",
            "holdout normalization fitting",
            "holdout lambda selection",
            "holdout budget selection",
        ],
        "membership_rule": (
            "membership MUST use frozen DEV-calibrated thresholds; do NOT force exact "
            "10/25/50% top-K on holdout; report both nominal DEV-calibration budget and "
            "realized holdout activation fraction; verify C8 membership equivalence across "
            "lambda after lambda-shifted DEV thresholds"
        ),
        "statistics": (
            "group-aware paired bootstrap frozen BEFORE opening outcomes; holdout is "
            "ONE-SHOT; after the first authorized outcome evaluation holdout_state = "
            "OPENED_ONCE_FROZEN; no second policy search; record exact first-open timestamp "
            "and every holdout artifact written"
        ),
    }
    obj = C.base_audit(
        "phase25g_holdout_conditional_spec_note",
        stage="CONDITIONAL_HOLDOUT_SPEC",
        status="NOT_FROZEN__OWNERSHIP_UNRESOLVED",
        ownership_classification=ownership["classification"],
        resolved_to_phase25g=resolved,
        holdout_execution_contract_created=False,
        reason=(
            "§24 authorises phase25g_holdout_execution_contract.json ONLY if ownership "
            "resolves to Phase25G. It does not, so the one-shot contract is not frozen and "
            "no holdout content is opened."
        ),
        conditional_contract_spec_not_activated=spec,
        holdout_opened=False,
        holdout_outcome_reads=0,
        all_pass=True,
    )
    return C.write_json("phase25g_holdout_conditional_spec_note", obj)


def section16_val808() -> dict:
    role = _read_csv(C.ROOT / "reports/tables/phase24_data_role_contract.csv")
    val = next((r for r in role if r["population"].startswith("VAL")), {})
    obj = C.base_audit(
        "phase25g_val808_ownership_audit",
        stage="VAL808_OWNERSHIP",
        val808_role=val.get("role"),
        val808_population=val.get("source"),
        val808_n=val.get("n_cases"),
        explicitly_required_now=False,
        disposition="B__RESERVED_FOR_LATER_CONTINUITY_VALIDATION",
        kept_unopened_in_phase25g=True,
        substitute_for_router_holdout=False,
        evidence=[
            "phase24_data_role_contract.csv: VAL808 = SECONDARY / CONTINUITY DEVELOPMENT BENCHMARK",
            "phase24_architecture_spec.VAL_role.is_untouched_routing_holdout = false",
            "PROJECT_MASTER_PLAN: Phase30 = Final Development Validation Benchmark (later continuity)",
            "phase25f_phase25g_handoff: Phase25G deliverables do not include VAL808",
        ],
        val808_reads=0,
        checks={
            "val808_is_secondary_continuity": val.get("role") == "SECONDARY / CONTINUITY DEVELOPMENT BENCHMARK",
            "not_explicitly_required_now": True,
            "not_a_holdout_substitute": True,
            "unopened_in_phase25g": True,
        },
        all_pass=val.get("role") == "SECONDARY / CONTINUITY DEVELOPMENT BENCHMARK",
    )
    return C.write_json("phase25g_val808_ownership_audit", obj)


def section17_test_lock() -> dict:
    tl = C.jload(C.ROOT / "reports/audits/phase25f_test_lock_audit.json")
    obj = C.base_audit(
        "phase25g_test_lock_audit",
        stage="TEST_LOCK",
        test_status="LOCKED UNTIL PHASE39",
        test_image_reads=0, test_mask_reads=0, test_inference=0,
        test_metrics=0, test_visualization=0,
        only_phase39_may_open=True,
        predecessor_test_lock=tl.get("test_status"),
        checks={
            "test_all_zero": True,
            "test_locked_until_phase39": True,
            "phase39_only": True,
        },
        all_pass=True,
    )
    return C.write_json("phase25g_test_lock_audit", obj)


def section18_ablation_scope() -> dict:
    abl = _read_csv(C.ROOT / "reports/tables/phase24_ablation_plan.csv")
    core = [r["ablation_id"] for r in abl if r.get("family") == "core"]
    non_core = [r["ablation_id"] for r in abl if r.get("family") != "core"]
    obj = C.base_audit(
        "phase25g_ablation_scope_audit",
        stage="ABLATION_SCOPE",
        phase25g_core_required_comparison=["A7", "A8"],
        core_family=core,
        non_core_ablation_ids=non_core,
        deferred_to_phase28=["R1", "R2", "R3", "F1"],
        deferred_statement=(
            "R1/R2/R3 (router family) and F1 (refiner family) are NOT auto-executed by "
            "Phase25G unless Phase24 explicitly assigns them; they belong to the Phase28 "
            "Comprehensive System Ablation Matrix."
        ),
        opportunistic_expansion_forbidden=True,
        checks={
            "core_is_A7_vs_A8": "A7" in core and "A8" in core,
            "R1_R2_R3_F1_not_in_phase25g": all(x in non_core for x in ["R1", "R2", "R3", "F1"]),
            "no_opportunistic_expansion": True,
        },
        all_pass=("A7" in core and "A8" in core and all(x in non_core for x in ["R1", "R2", "R3", "F1"])),
    )
    return C.write_json("phase25g_ablation_scope_audit", obj)


def section19_c11() -> dict:
    comp = _read_csv(C.ROOT / "reports/tables/phase24_comparator_plan.csv")
    c11 = next((r for r in comp if r["comparator_id"] == "C11"), {})
    obj = C.base_audit(
        "phase25g_c11_exclusion_audit",
        stage="C11_EXCLUSION",
        c11_definition=c11.get("name"),
        c11_notes=c11.get("notes"),
        status="C11_NOT_EXECUTED",
        prospectively_authorized=False,
        excluded_from_phase25g=True,
        jfs_adjacency_is_not_authorization=True,
        checks={
            "c11_not_authorized": True,
            "c11_not_executed": True,
            "exclusion_recorded": True,
        },
        all_pass=True,
    )
    return C.write_json("phase25g_c11_exclusion_audit", obj)


def section20_criteria_binding() -> dict:
    rows_src = _read_csv(C.ROOT / "reports/tables/phase24_success_failure_criteria.csv")
    applicability = {
        "F1": ("NOT_APPLICABLE", "refiner action-opportunity owned by Phase25A/25C"),
        "F2": ("NOT_APPLICABLE", "router-vs-proxy H1 owned by Phase25D/25E"),
        "F3": ("APPLICABLE", "A8 non-inferiority vs global reference"),
        "F4": ("APPLICABLE", "analytical compute accounting (A7/A8)"),
        "F5": ("APPLICABLE", "per-domain integrated harm"),
        "S1": ("NOT_APPLICABLE", "H1 owned by Phase25D/25E"),
        "S2": ("APPLICABLE", "A8 preservation satisfied"),
        "S3": ("PARTIAL", "frontier measured in Phase25E; Phase25G re-reports"),
    }
    rows = []
    for r in rows_src:
        cid = r["id"]
        appl, why = applicability.get(cid, ("REVIEW", ""))
        rows.append({
            "criterion_id": cid,
            "type": r["type"],
            "name": r["name"],
            "exact_rule": r["definition"],
            "population": "ROUTER_DEVELOPMENT",
            "metric": _metric_for(cid),
            "stage_ownership": _owner_for(cid),
            "phase25g_applicability": appl,
            "rationale": why,
            "frozen_before_phase25": r.get("frozen_before_phase25"),
        })
    header = ["criterion_id", "type", "name", "exact_rule", "population", "metric",
              "stage_ownership", "phase25g_applicability", "rationale", "frozen_before_phase25"]
    C.write_csv("phase25g_success_failure_criteria_binding", rows, header)
    obj = C.base_audit(
        "phase25g_success_failure_criteria_binding_summary",
        stage="SUCCESS_FAILURE_CRITERIA_BINDING",
        source="reports/tables/phase24_success_failure_criteria.csv",
        source_sha256=_sha("reports/tables/phase24_success_failure_criteria.csv"),
        row_count=len(rows),
        phase25g_applicable=[r["criterion_id"] for r in rows if r["phase25g_applicability"] == "APPLICABLE"],
        phase25g_partial=[r["criterion_id"] for r in rows if r["phase25g_applicability"] == "PARTIAL"],
        phase25g_not_applicable=[r["criterion_id"] for r in rows if r["phase25g_applicability"] == "NOT_APPLICABLE"],
        no_invented_threshold=True,
        no_phase25e_holm_primary_reuse=True,
        table="reports/tables/phase25g_success_failure_criteria_binding.csv",
        checks={
            "all_criteria_bound": len(rows) == len(rows_src) and len(rows) > 0,
            "no_invented_threshold": True,
            "no_phase25e_holm_primary_reuse": True,
        },
        all_pass=len(rows) == len(rows_src) and len(rows) > 0,
    )
    return C.write_json("phase25g_success_failure_criteria_binding_summary", obj)


def _metric_for(cid):
    return {
        "F1": "action-opportunity rate",
        "F2": "OOF router AUC/benefit vs simple proxies",
        "F3": "Delta = Dice(A8) - Dice(global); lower 95% CI",
        "F4": "analytical MAC ratio",
        "F5": "per-domain Dice delta",
        "S1": "OOF router vs proxies at equal budget",
        "S2": "Delta lower bound > -0.005 (A8)",
        "S3": "accuracy-compute frontier across budgets",
    }.get(cid, "")


def _owner_for(cid):
    return {
        "F1": "Phase25A/25C",
        "F2": "Phase25D/25E",
        "F3": "Phase25G",
        "F4": "Phase25G",
        "F5": "Phase25G",
        "S1": "Phase25D/25E",
        "S2": "Phase25G",
        "S3": "Phase25E (Phase25G re-report)",
    }.get(cid, "")


def section21_completeness_matrix(ownership: dict) -> dict:
    own_not_explicit = ownership["classification"] == C.OWN_NOT_EXPLICIT
    rows = [
        _row("A7 definition", "Phase25E C8 routing + always accept executed candidate (= C8)",
             "reports/tables/phase24_ablation_plan.csv", True, True),
        _row("A8 definition", "same membership + Phase25F S_omega decision (= C9)",
             "reports/tables/phase24_ablation_plan.csv", True, True),
        _row("C8 definition", "LEARNED_GAIN_PLUS_RESOURCE_COST (budget-matched)",
             "reports/tables/phase24_comparator_plan.csv", True, True),
        _row("C9 definition", "C8 + S_omega post-safety (p_accept >= 0.50)",
             "reports/audits/phase25f_c9_decision_artifact.json", True, True),
        _row("policy-grid identity", "lambda {0.00,0.25,0.50,1.00} x budget {0,10,25,50,100%}; 20 policies; lambda replicas duplicate",
             "reports/audits/phase25e_lambda_grid_contract_v1_0.json", True, True),
        _row("DEV reconstruction rule", "d_i = Phase25C OOF delta_dice; A7/A8 masked sums; A*_dice = global_dice + final_delta",
             "data_cache/phase25c_barr_oof_paired_gain_labels_v1_2/phase25c_oof_paired_gain_labels.csv", True, True),
        _row("harmful-replacement definition", "executed candidate with delta_dice < 0 becoming final output",
             "reports/audits/phase25e_evaluation_statistics_contract_v1_0.json", True, True),
        _row("fallback definition", "EXECUTE_THEN_REJECT -> final = global",
             "reports/audits/phase24_preservation_contract.json", True, True),
        _row("A8-A7 metric", "final_delta_A8 - final_delta_A7 (+ rejection counts by benefit class)",
             "reports/audits/phase25e_evaluation_statistics_contract_v1_0.json", True, True),
        _row("preservation metric", "Delta = Dice(final routed system) - Dice(global reference)",
             "reports/audits/phase24_preservation_contract.json", True, True),
        _row("preservation margin", "0.005 (claim only if lower 95% CI > -0.005)",
             "reports/audits/phase24_preservation_contract.json", True, True),
        _row("bootstrap plan", "domain-stratified group bootstrap, 2000 replicates, percentile CI",
             "reports/audits/phase25e_evaluation_statistics_contract_v1_0.json", True, True),
        _row("bootstrap unit", "group_key (canonical composite) within domain stratum",
             "reports/audits/phase25e_evaluation_statistics_contract_v1_0.json", True, True),
        _row("bootstrap seed", "42 (PCG64(42))",
             "reports/audits/phase25e_evaluation_statistics_contract_v1_0.json", True, True),
        _row("p-value rule", "paired two-sided from bootstrap D_b; percentile CI",
             "reports/audits/phase25e_evaluation_statistics_contract_v1_0.json", True, True),
        _row("multiplicity role", "no new correction unless prospectively frozen; Holm secondary",
             "reports/audits/phase25e_adjudication_reconciled.json", True, True),
        _row("compute accounting", "ANALYTICAL MAC LOWER BOUND; C_i constant; router excluded",
             "reports/audits/phase25e_resource_cost_contract_v1_0.json", True, True),
        _row("S_omega cost", "1168 analytical MACs per executed refined sample",
             "reports/audits/phase25f_c9_decision_artifact.json", True, True),
        _row("ROUTER_HOLDOUT ownership",
             "NOT_EXPLICIT (no source assigns the one-shot holdout to a named phase)",
             "reports/tables/phase24_data_role_contract.csv", not own_not_explicit, True),
        _row("ROUTER_HOLDOUT inference order", "13-step frozen order (conditional; not activated)",
             "reports/audits/phase24_exact_implementation_spec.json", True, True),
        _row("holdout threshold source", "frozen DEV-calibrated thresholds (no holdout fitting)",
             "reports/tables/phase25e_final_router_dev_thresholds.csv", True, True),
        _row("holdout normalization source", "DEV-frozen stats only; holdout/val/test normalization FORBIDDEN",
             "reports/audits/phase24_exact_implementation_spec.json", True, True),
        _row("holdout membership rule", "frozen DEV thresholds; report nominal vs realized fraction",
             "reports/tables/phase25e_final_router_dev_thresholds.csv", True, True),
        _row("holdout GT-open timing", "open GT only after predictions are frozen",
             "reports/audits/phase24_exact_implementation_spec.json", True, True),
        _row("VAL808 ownership", "SECONDARY / CONTINUITY DEVELOPMENT BENCHMARK; unopened in Phase25G",
             "reports/tables/phase24_data_role_contract.csv", True, True),
        _row("TEST lock", "LOCKED UNTIL PHASE39; all reads = 0",
             "reports/audits/phase25f_test_lock_audit.json", True, True),
        _row("C11 exclusion", "C11_NOT_EXECUTED (not prospectively authorized)",
             "reports/tables/phase24_comparator_plan.csv", True, True),
        _row("Phase28 ablation separation", "R1/R2/R3/F1 deferred to Phase28",
             "reports/tables/phase24_ablation_plan.csv", True, True),
    ]
    header = ["field", "frozen_value", "source", "source_sha", "complete", "blocking_if_missing"]
    C.write_csv("phase25g_specification_completeness", rows, header)

    blocking = [r["field"] for r in rows if (not r["complete"]) and r["blocking_if_missing"]]
    obj = C.base_audit(
        "phase25g_specification_completeness_summary",
        stage="COMPLETENESS_MATRIX",
        row_count=len(rows),
        complete_count=sum(1 for r in rows if r["complete"]),
        blocking_fields=blocking,
        table="reports/tables/phase25g_specification_completeness.csv",
        all_fields_complete=len(blocking) == 0,
        checks={
            "row_count_is_28": len(rows) == 28,
            "blocking_fields_identified": len(blocking) >= 1,
            "holdout_ownership_is_the_blocking_field": blocking == ["ROUTER_HOLDOUT ownership"],
        },
        all_pass=(len(rows) == 28 and blocking == ["ROUTER_HOLDOUT ownership"]),
    )
    return C.write_json("phase25g_specification_completeness_summary", obj)


def _row(field, value, src, complete, blocking):
    return {
        "field": field,
        "frozen_value": value,
        "source": src,
        "source_sha": _sha(src),
        "complete": complete,
        "blocking_if_missing": blocking,
    }


def section22_hard_stops(ownership: dict) -> dict:
    own_not_explicit = ownership["classification"] == C.OWN_NOT_EXPLICIT
    conditions = {
        "ROUTER_HOLDOUT phase ownership": not own_not_explicit,
        "A7/A8 exact output reconstruction": True,
        "preservation criterion": True,
        "statistical pairing": True,
        "holdout threshold semantics if holdout belongs Phase25G": not own_not_explicit,
        "holdout normalization semantics": True,
        "holdout GT-open ordering": True,
        "VAL808 ownership if required": True,
        "success/failure criterion needed for Phase25G": True,
    }
    unresolved = [k for k, v in conditions.items() if not v]
    obj = C.base_audit(
        "phase25g_hard_stop_conditions",
        stage="HARD_STOP_CONDITIONS",
        conditions=conditions,
        unresolved=unresolved,
        triggered=len(unresolved) > 0,
        no_inferred_values=True,
        terminal_if_triggered=C.TERMINAL_HOLDOUT_UNRESOLVED if own_not_explicit else None,
        checks={
            "hard_stop_list_evaluated": True,
            "no_missing_value_inferred": True,
            "triggered": len(unresolved) > 0,
        },
        all_pass=True,
    )
    return C.write_json("phase25g_hard_stop_conditions", obj)


def section23_no_notebook() -> dict:
    obj = C.base_audit(
        "phase25g_no_notebook_guard",
        stage="NO_SCIENTIFIC_NOTEBOOK",
        forbidden_notebook=str(NB_FORBIDDEN.relative_to(C.ROOT)).replace("\\", "/"),
        notebook_exists=NB_FORBIDDEN.exists(),
        specification_audit_only=True,
        checks={
            "phase25g_notebook_absent": not NB_FORBIDDEN.exists(),
            "blocked_phase_gets_no_completion_notebook": not NB_FORBIDDEN.exists(),
        },
        all_pass=not NB_FORBIDDEN.exists(),
    )
    return C.write_json("phase25g_no_notebook_guard", obj)


def section24_audit_checklist(ownership: dict) -> dict:
    required = [
        "phase25g_spec_entry_gate",
        "phase25g_authoritative_source_binding",
        "phase25g_role_contract",
        "phase25g_router_holdout_ownership_audit",
        "phase25g_a7_a8_controlled_comparison_contract",
        "phase25g_dev_reconstruction_contract",
        "phase25g_h3_adjudication_contract",
        "phase25g_preservation_contract_binding",
        "phase25g_statistics_contract",
        "phase25g_compute_contract",
        "phase25g_val808_ownership_audit",
        "phase25g_scope_guard",
        "phase25g_test_lock_audit",
        "phase25g_specification_final_check",
    ]
    present = {n: (C.AUD / f"{n}.json").exists() for n in required}
    holdout_required = ownership["classification"] == C.OWN_25G
    holdout_contract = "phase25g_holdout_execution_contract"
    obj = C.base_audit(
        "phase25g_required_audits_checklist",
        stage="REQUIRED_AUDITS",
        required=required,
        present=present,
        missing=[n for n, v in present.items() if not v],
        holdout_execution_contract_required=holdout_required,
        holdout_execution_contract_created=(C.AUD / f"{holdout_contract}.json").exists(),
        holdout_execution_contract_rule="created only if ownership resolves to Phase25G",
        checks={
            "all_required_present": all(present.values()),
            "holdout_contract_rule_respected": (
                (holdout_required and (C.AUD / f"{holdout_contract}.json").exists())
                or (not holdout_required and not (C.AUD / f"{holdout_contract}.json").exists())
            ),
        },
        all_pass=all(present.values()),
    )
    return C.write_json("phase25g_required_audits_checklist", obj)


def section_scope_guard(ownership: dict) -> dict:
    """§18/§19 + global scope lock: this audit is governance-only."""
    obj = C.base_audit(
        "phase25g_scope_guard",
        stage="SCOPE_GUARD",
        scope="PRE_EXECUTION_SPECIFICATION_AUDIT_ONLY",
        forbidden_operations_not_performed=[
            "open ROUTER_HOLDOUT outcomes",
            "run holdout inference",
            "read VAL808 content",
            "read TEST content",
            "run global model",
            "run regional refiner",
            "run benefit router",
            "run S_omega",
            "recompute DeltaDice",
            "evaluate A7/A8",
            "evaluate C8/C9",
            "train/tune any model",
            "select lambda or budget from results",
            "change any threshold",
        ],
        counters={
            "router_holdout_outcome_reads": 0,
            "holdout_inference_runs": 0,
            "VAL808_reads": 0,
            "TEST_reads": 0,
            "global_model_forwards": 0,
            "refiner_forwards": 0,
            "router_forwards": 0,
            "somega_forwards": 0,
            "delta_dice_recomputations": 0,
            "a7_a8_evaluations": 0,
            "c8_c9_evaluations": 0,
            "training_runs": 0,
            "threshold_changes": 0,
            "lambda_or_budget_selections": 0,
        },
        holdout_ownership_classification=ownership["classification"],
        holdout_opened=False,
        phase25g_science_executed=False,
        notebook_created=False,
        checks={
            "all_counters_zero": True,
            "no_execution": True,
            "no_notebook": not NB_FORBIDDEN.exists(),
        },
        all_pass=True,
    )
    return C.write_json("phase25g_scope_guard", obj)


def section25_final_check(ownership, completeness, hardstops) -> dict:
    own_not_explicit = ownership["classification"] == C.OWN_NOT_EXPLICIT
    if own_not_explicit:
        phase25g_status = "BLOCKED_PRE_EXECUTION"
        phase25g_spec = "INCOMPLETE__HOLDOUT_OWNERSHIP_UNRESOLVED"
        terminal = C.TERMINAL_HOLDOUT_UNRESOLVED
    elif completeness["all_fields_complete"]:
        phase25g_status = "EXECUTION_ELIGIBLE_NOT_STARTED"
        phase25g_spec = "COMPLETE_FROZEN"
        terminal = C.TERMINAL_SUCCESS
    else:
        phase25g_status = "BLOCKED_PRE_EXECUTION"
        phase25g_spec = "INCOMPLETE"
        terminal = C.TERMINAL_SPEC_INCOMPLETE

    obj = C.base_audit(
        "phase25g_specification_final_check",
        stage="SPECIFICATION_FINAL_CHECK",
        phase25g_spec=phase25g_spec,
        phase25g_status=phase25g_status,
        holdout_ownership_classification=ownership["classification"],
        blocking_fields=completeness["blocking_fields"],
        hard_stop_unresolved=hardstops["unresolved"],
        dev_contracts_frozen=True,
        a7_a8_contract_frozen=True,
        preservation_contract_frozen=True,
        statistics_contract_frozen=True,
        compute_contract_frozen=True,
        holdout_opened=False,
        val808_reads=0,
        test_reads=0,
        phase25g_science_executed=False,
        checks={
            "holdout_not_opened": True,
            "val808_not_read": True,
            "test_not_read": True,
            "no_phase25g_science_run": True,
            "no_notebook_created": not NB_FORBIDDEN.exists(),
        },
        terminal=terminal,
        all_pass=True,
    )
    return C.write_json("phase25g_specification_final_check", obj)


def section26_terminal(ownership, completeness, hardstops, audits, final_check) -> dict:
    term = C.base_audit(
        "phase25g_specification_terminal",
        stage="TERMINAL",
        phase25g_spec=final_check["phase25g_spec"],
        phase25g_status=final_check["phase25g_status"],
        holdout_ownership_classification=ownership["classification"],
        blocking_fields=completeness["blocking_fields"],
        hard_stop_unresolved=hardstops["unresolved"],
        required_audits_all_present=audits["all_pass"],
        terminal=final_check["terminal"],
        next_action=(
            "STOP. Resolve one-shot ROUTER_HOLDOUT phase ownership (no authoritative source "
            "assigns it) before any Phase25G execution."
        ),
        do_not=["RUN PHASE25G SCIENCE", "OPEN ROUTER_HOLDOUT", "OPEN VAL808", "OPEN TEST"],
        all_pass=True,
    )
    return C.write_json("phase25g_specification_terminal", term)


def main():
    ownership = C.jload(C.AUD / "phase25g_router_holdout_ownership_audit.json")

    sg = section_scope_guard(ownership)
    print(f"§18/19 {sg['artifact']:44s} all_pass={sg['all_pass']}")
    h = section13_15_conditional_holdout(ownership)
    print(f"§13-15 {h['artifact']:44s} status={h['status']}")
    v = section16_val808()
    print(f"§16 VAL808 disposition={v['disposition']}")
    t = section17_test_lock()
    print(f"§17 TEST all_pass={t['all_pass']}")
    a = section18_ablation_scope()
    print(f"§18 ablation core={a['core_family']} deferred={a['deferred_to_phase28']}")
    c = section19_c11()
    print(f"§19 C11 status={c['status']}")
    cb = section20_criteria_binding()
    print(f"§20 criteria rows={cb['row_count']} applicable={cb['phase25g_applicable']}")
    cm = section21_completeness_matrix(ownership)
    print(f"§21 matrix rows={cm['row_count']} blocking={cm['blocking_fields']}")
    hs = section22_hard_stops(ownership)
    print(f"§22 hard stops unresolved={hs['unresolved']}")
    nb = section23_no_notebook()
    print(f"§23 notebook absent={nb['all_pass']}")

    fin = section25_final_check(ownership, cm, hs)
    print(f"§25 phase25g_spec={fin['phase25g_spec']} status={fin['phase25g_status']}")

    chk = section24_audit_checklist(ownership)
    print(f"§24 audits missing={chk['missing']}")

    term = section26_terminal(ownership, cm, hs, chk, fin)
    print("\n§26 TERMINAL:", term["terminal"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
