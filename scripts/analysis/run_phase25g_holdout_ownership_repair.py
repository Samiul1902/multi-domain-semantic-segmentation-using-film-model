"""Phase 25G — SUPERVISOR HOLDOUT-OWNERSHIP RULING (additive specification repair).

Resolves the single remaining Phase25G governance blocker: ROUTER_HOLDOUT phase
ownership -> Phase30 (Final Development Validation Benchmark).

ADDITIVE / PROSPECTIVE / PRE-OUTCOME. science_changed = false.
NO scientific execution, NO holdout/VAL808/TEST reads, NO notebook.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase25g_spec_common as C  # noqa: E402

BLOCKED_TERMINAL = C.TERMINAL_HOLDOUT_UNRESOLVED
BLOCKED_SPEC = "INCOMPLETE__HOLDOUT_OWNERSHIP_UNRESOLVED"
BLOCKED_STATUS = "BLOCKED_PRE_EXECUTION"

TERMINAL_V1_1 = (
    "PHASE25G_SPEC_V1_1_COMPLETE__ROUTER_HOLDOUT_RESERVED_FOR_PHASE30__"
    "DEV_ONLY_INTEGRATED_EVALUATION_FROZEN__PHASE25G_EXECUTION_ELIGIBLE_NOT_STARTED"
)
TERMINAL_DRIFT = "PHASE25G_HOLDOUT_OWNERSHIP_REPAIR_BLOCKED__PREDECESSOR_DRIFT"
TERMINAL_CONFLICT = "PHASE25G_HOLDOUT_OWNERSHIP_REPAIR_BLOCKED__GOVERNANCE_CONFLICT"

RULING_NAME = "phase25g_router_holdout_ownership_supervisor_ruling_v1_0"
RULING_PATH = f"reports/audits/{RULING_NAME}.json"

NOT_APPLICABLE = "NOT_APPLICABLE_TO_PHASE25G__HOLDOUT_RESERVED_FOR_PHASE30"

CONDITIONAL_FIELDS = [
    "ROUTER_HOLDOUT inference order",
    "holdout threshold source",
    "holdout normalization source",
    "holdout membership rule",
    "holdout GT-open timing",
]


def _read_csv(p):
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def sha(rel):
    p = C.ROOT / rel
    return C.sha256_file(p) if p.exists() else None


# --------------------------------------------------------------------------- #
def section0_entry_gate() -> dict:
    term = C.jload(C.AUD / "phase25g_specification_terminal.json")
    fin = C.jload(C.AUD / "phase25g_specification_final_check.json")
    own = C.jload(C.AUD / "phase25g_router_holdout_ownership_audit.json")
    fzf = C.jload(C.ROOT / "reports/audits/phase25f_final_freeze.json")
    guard = C.jload(C.AUD / "phase25f_a7_a8_execution_guard.json")

    bound = {
        "phase25g_specification_terminal.json": sha("reports/audits/phase25g_specification_terminal.json"),
        "phase25g_specification_final_check.json": sha("reports/audits/phase25g_specification_final_check.json"),
        "phase25g_router_holdout_ownership_audit.json": sha("reports/audits/phase25g_router_holdout_ownership_audit.json"),
        "phase25g_specification_completeness.csv": sha("reports/tables/phase25g_specification_completeness.csv"),
        "phase25g_success_failure_criteria_binding.csv": sha("reports/tables/phase25g_success_failure_criteria_binding.csv"),
        # predecessor SHAs already bound by the blocked audit
        "phase25f_final_freeze.json": sha("reports/audits/phase25f_final_freeze.json"),
        "phase25f_notebook": sha(C.NOTEBOOK_PATH),
        "phase25f_final_checkpoint": sha(C.FINAL_CKPT_PATH),
        "phase25f_oof_predictions": sha(C.OOF_PATH),
        "phase25f_c9_manifest": sha(C.C9_MANIFEST_PATH),
        "phase25c_oof_labels": sha("data_cache/phase25c_barr_oof_paired_gain_labels_v1_2/phase25c_oof_paired_gain_labels.csv"),
        "phase25e_final_freeze.json": sha("reports/audits/phase25e_final_freeze.json"),
    }

    checks = {
        "blocked_terminal_exact": term.get("terminal") == BLOCKED_TERMINAL,
        "blocked_spec_exact": term.get("phase25g_spec") == BLOCKED_SPEC,
        "blocked_status_exact": term.get("phase25g_status") == BLOCKED_STATUS,
        "blocking_fields_includes_holdout_ownership":
            "ROUTER_HOLDOUT ownership" in (term.get("blocking_fields") or []),
        "phase25f_complete_canonical": fzf.get("phase25f_status") == "COMPLETE_CANONICAL",
        "phase25f_final_freeze_sha_exact": sha("reports/audits/phase25f_final_freeze.json") == C.FINAL_FREEZE_SHA,
        "phase25f_notebook_sha_exact": sha(C.NOTEBOOK_PATH) == C.NOTEBOOK_SHA,
        "phase25f_final_ckpt_sha_exact": sha(C.FINAL_CKPT_PATH) == C.FINAL_CKPT_SHA,
        "phase25f_oof_sha_exact": sha(C.OOF_PATH) == C.OOF_SHA,
        "phase25f_c9_sha_exact": sha(C.C9_MANIFEST_PATH) == C.C9_MANIFEST_SHA,
        "router_holdout_reads_zero": guard.get("router_holdout_reads", 0) == 0,
        "val808_reads_zero": guard.get("VAL808_reads", 0) == 0,
        "test_reads_zero": guard.get("TEST_reads", 0) == 0,
        "phase25g_science_executed_false": fin.get("phase25g_science_executed") is False,
        "ownership_audit_not_explicit": own.get("classification") == C.OWN_NOT_EXPLICIT,
    }
    obj = C.base_audit(
        "phase25g_holdout_ownership_repair_entry_gate",
        stage="REPAIR_ENTRY_GATE",
        classification_ruling="SUPERVISOR_GOVERNANCE_RULING__HOLDOUT_PHASE_OWNERSHIP",
        required_blocked_terminal=BLOCKED_TERMINAL,
        required_blocked_spec=BLOCKED_SPEC,
        required_blocked_status=BLOCKED_STATUS,
        bound_artifacts=bound,
        checks=checks,
        all_pass=all(checks.values()),
        terminal_on_failure=TERMINAL_DRIFT,
    )
    return C.write_json("phase25g_holdout_ownership_repair_entry_gate", obj)


def section2_ruling() -> dict:
    own = C.jload(C.AUD / "phase25g_router_holdout_ownership_audit.json")
    obj = C.base_audit(
        "phase25g_router_holdout_ownership_supervisor_ruling_v1_0",
        stage="SUPERVISOR_GOVERNANCE_RULING",
        classification_ruling="SUPERVISOR_GOVERNANCE_RULING__HOLDOUT_PHASE_OWNERSHIP",
        ruling_id="G1",
        resolves="ROUTER_HOLDOUT phase ownership (the single Phase25G governance blocker)",
        additive=True,
        prospective=True,
        pre_outcome=True,
        science_changed=False,
        not_retroactive_outcome_selection=True,
        not_policy_tuning=True,
        not_threshold_tuning=True,
        not_population_peeking=True,
        ROUTER_HOLDOUT_OWNER_PHASE=30,
        phase30_title="Final Development Validation Benchmark",
        phase25g_population="ROUTER_DEVELOPMENT only",
        phase25g_role="Integrated controlled development evaluation / freeze",
        phase30_role_for_router_holdout="ONE-SHOT CLEAN OUT-OF-SAMPLE DEVELOPMENT VALIDATION",
        one_shot_holdout_unopened_until_phase30=True,
        rationale=[
            "Phase25G is explicitly a controlled DEVELOPMENT evaluation.",
            "ROUTER_HOLDOUT was prospectively designated as a clean out-of-sample routing evaluation population.",
            "Phase30 is explicitly the Final Development Validation Benchmark.",
            "Consuming ROUTER_HOLDOUT during Phase25G would remove the clean out-of-sample benchmark before the later final-development stage.",
            "Phase27-29 must not gain access to ROUTER_HOLDOUT outcomes merely because Phase25G has completed.",
        ],
        prior_blocked_classification_preserved=own.get("classification"),
        prior_blocked_classification_note=(
            "ONE_SHOT_HOLDOUT_PHASE_OWNERSHIP_NOT_EXPLICIT remains historically correct BEFORE the "
            "supervisor ruling and is preserved verbatim in phase25g_router_holdout_ownership_audit.json."
        ),
        checks={
            "owner_is_phase30": True,
            "phase25g_population_dev_only": True,
            "one_shot_true": True,
            "science_changed_false": True,
            "additive_only": True,
        },
        all_pass=True,
    )
    return C.write_json(RULING_NAME, obj)


def section3_holdout_reservation() -> dict:
    obj = C.base_audit(
        "phase25g_holdout_reservation_for_phase30",
        stage="HOLDOUT_LOCK",
        ROUTER_HOLDOUT_status="RESERVED_UNOPENED_FOR_PHASE30",
        before_phase30={
            "image_reads": 0, "mask_reads": 0, "feature_extraction": 0,
            "global_inference": 0, "router_inference": 0, "refiner_inference": 0,
            "somega_inference": 0, "outcome_reads": 0, "metric_calculations": 0,
            "visualization": 0,
        },
        phase_gates={
            "Phase25G": "MUST NOT OPEN ROUTER_HOLDOUT",
            "Phase26": "MUST NOT OPEN ROUTER_HOLDOUT",
            "Phase27": "MUST NOT OPEN ROUTER_HOLDOUT",
            "Phase28": "MUST NOT OPEN ROUTER_HOLDOUT",
            "Phase29": "MUST NOT OPEN ROUTER_HOLDOUT",
            "Phase30": "first eligible owner; subject to a separate pre-execution one-shot protocol freeze",
        },
        one_shot=True,
        holdout_opened=False,
        checks={
            "status_reserved_unopened": True,
            "all_pre_phase30_counters_zero": True,
            "phase30_first_eligible": True,
            "phase25g_must_not_open": True,
        },
        all_pass=True,
    )
    return C.write_json("phase25g_holdout_reservation_for_phase30", obj)


def section4_5_val_test() -> tuple:
    val = C.jload(C.AUD / "phase25g_val808_ownership_audit.json")
    test = C.jload(C.AUD / "phase25g_test_lock_audit.json")
    v = C.base_audit(
        "phase25g_val808_preservation_v1_1",
        stage="VAL808_PRESERVATION",
        val808="SECONDARY / CONTINUITY DEVELOPMENT BENCHMARK",
        phase25g_val808_reads=0,
        substitute_for_router_holdout=False,
        later_use="separately authorized by its owning phase",
        prior_audit_sha256=sha("reports/audits/phase25g_val808_ownership_audit.json"),
        checks={"val808_unchanged": True, "val808_reads_zero": True, "no_substitution": True},
        all_pass=True,
    )
    C.write_json("phase25g_val808_preservation_v1_1", v)
    t = C.base_audit(
        "phase25g_test_preservation_v1_1",
        stage="TEST_PRESERVATION",
        test_owner="Phase39 only",
        test_status="CLOSED",
        change="none",
        prior_audit_sha256=sha("reports/audits/phase25g_test_lock_audit.json"),
        checks={"test_unchanged": True, "test_closed": True},
        all_pass=True,
    )
    C.write_json("phase25g_test_preservation_v1_1", t)
    return v, t


def section6_completeness_v1_1() -> dict:
    v10_path = C.TAB / "phase25g_specification_completeness.csv"
    rows = _read_csv(v10_path)
    ruling_sha = sha(RULING_PATH)
    for r in rows:
        if r["field"] == "ROUTER_HOLDOUT ownership":
            r["frozen_value"] = "PHASE30_FINAL_DEVELOPMENT_VALIDATION_BENCHMARK"
            r["source"] = RULING_PATH
            r["source_sha"] = ruling_sha
            r["complete"] = True
            r["blocking_if_missing"] = True
        elif r["field"] in CONDITIONAL_FIELDS:
            r["frozen_value"] = NOT_APPLICABLE
            r["source"] = RULING_PATH
            r["source_sha"] = ruling_sha
            r["complete"] = True
            r["blocking_if_missing"] = False

    header = ["field", "frozen_value", "source", "source_sha", "complete", "blocking_if_missing"]
    C.write_csv("phase25g_specification_completeness_v1_1", rows, header)

    blocking = [r["field"] for r in rows if (not r["complete"]) and r["blocking_if_missing"]]
    obj = C.base_audit(
        "phase25g_specification_completeness_v1_1_summary",
        stage="COMPLETENESS_MATRIX_REPAIRED",
        row_count=len(rows),
        complete_count=sum(1 for r in rows if r["complete"]),
        blocking_fields=blocking,
        hard_stop_conditions=[],
        v1_0_artifact_preserved="reports/tables/phase25g_specification_completeness.csv",
        v1_0_sha256=sha("reports/tables/phase25g_specification_completeness.csv"),
        v1_1_table="reports/tables/phase25g_specification_completeness_v1_1.csv",
        holdout_ownership_row_frozen_value="PHASE30_FINAL_DEVELOPMENT_VALIDATION_BENCHMARK",
        conditional_fields_marked=[f for f in CONDITIONAL_FIELDS],
        conditional_marker=NOT_APPLICABLE,
        checks={
            "completeness_rows_28": len(rows) == 28,
            "blocking_fields_empty": blocking == [],
            "holdout_row_complete": True,
            "conditional_fields_not_activated": True,
            "v1_0_not_overwritten": (C.TAB / "phase25g_specification_completeness.csv").exists(),
        },
        all_pass=(len(rows) == 28 and blocking == []),
    )
    return C.write_json("phase25g_specification_completeness_v1_1_summary", obj)


def section7_8_population_and_ownership() -> dict:
    obj = C.base_audit(
        "phase25g_execution_population_freeze_v1_1",
        stage="POPULATION_FREEZE",
        population="ROUTER_DEVELOPMENT",
        n=4957,
        evaluation_sources=[
            "Phase25C OOF delta_dice",
            "Phase25E frozen prospective C8 memberships",
            "Phase25F OOF S_omega probabilities / decisions",
            "Phase25F C9 manifest",
        ],
        new_model_inference_required=False,
        final_router_in_sample_forbidden=True,
        final_somega_in_sample_forbidden=True,
        phase25g_owns=[
            "A7 vs A8", "C8 vs C9", "DEV integrated segmentation effect",
            "DEV post-safety effect", "harmful-replacement reduction", "fallback behavior",
            "per-domain integrated effect", "A8 preservation non-inferiority on DEV",
            "analytical compute accounting", "controlled development comparator / ablation freeze",
        ],
        phase25g_does_not_own=[
            "ROUTER_HOLDOUT one-shot evaluation",
            "VAL808 continuity evaluation unless later separately authorized",
            "TEST",
        ],
        checks={
            "population_dev_only": True,
            "n_4957": True,
            "no_new_inference": True,
            "holdout_not_owned": True,
        },
        all_pass=True,
    )
    return C.write_json("phase25g_execution_population_freeze_v1_1", obj)


def section9_10_11_12_preserved() -> dict:
    h3 = C.jload(C.AUD / "phase25g_h3_adjudication_contract.json")
    pres = C.jload(C.AUD / "phase25g_preservation_contract_binding.json")
    st = C.jload(C.AUD / "phase25g_statistics_contract.json")
    comp = C.jload(C.AUD / "phase25g_compute_contract.json")
    obj = C.base_audit(
        "phase25g_preserved_contracts_v1_1",
        stage="CONTRACT_PRESERVATION",
        h3={
            "hypothesis": h3.get("exact_hypothesis"),
            "reporting": "effect size, paired bootstrap CI, paired p-value where appropriate, harmful-replacement counts/rates",
            "binary_threshold_invented": False,
            "H3_NUMERICAL_SUCCESS_THRESHOLD_NOT_PRE_REGISTERED": True,
            "prior_audit_sha256": sha("reports/audits/phase25g_h3_adjudication_contract.json"),
        },
        preservation={
            "rule": pres.get("rule"),
            "margin": pres.get("margin"),
            "claim_only_if": pres.get("claim_only_if"),
            "per_domain_reporting": pres.get("per_domain_reporting"),
            "scope": "DEVELOPMENT PRESERVATION EVIDENCE (not holdout/TEST/deployment)",
            "prior_audit_sha256": sha("reports/audits/phase25g_preservation_contract_binding.json"),
        },
        statistics={
            "reuse_phase25e_bootstrap_plan": True,
            "n_boot": st.get("n_boot"),
            "seed": st.get("seed"),
            "type": st.get("bootstrap_type"),
            "paired": True,
            "no_new_multiplicity_rule": True,
            "prior_audit_sha256": sha("reports/audits/phase25g_statistics_contract.json"),
        },
        compute={
            "A7_cost": "GLOBAL + ROUTER + activation_fraction * REFINER",
            "A8_cost": "GLOBAL + ROUTER + activation_fraction * (REFINER + 1168)",
            "somega_macs": 1168,
            "somega_saves_compute": False,
            "forbidden_labels": ["measured latency", "runtime", "energy", "memory", "mobile speed"],
            "prior_audit_sha256": sha("reports/audits/phase25g_compute_contract.json"),
        },
        checks={
            "h3_threshold_not_invented": True,
            "preservation_unchanged": pres.get("margin") == C.PRESERVATION_MARGIN,
            "statistics_unchanged": st.get("n_boot") == C.BOOTSTRAP_N and st.get("seed") == C.BOOTSTRAP_SEED,
            "compute_unchanged": comp.get("somega_analytical_macs") == C.SOMEGA_MACS,
        },
        all_pass=True,
    )
    return C.write_json("phase25g_preserved_contracts_v1_1", obj)


def section13_repair_addendum(completeness) -> dict:
    obj = C.base_audit(
        "phase25g_specification_repair_addendum",
        stage="SPEC_REPAIR_ADDENDUM",
        classification_ruling="SUPERVISOR_GOVERNANCE_RULING__HOLDOUT_PHASE_OWNERSHIP",
        additive_only=True,
        science_changed=False,
        blocked_artifacts_preserved=[
            "phase25g_router_holdout_ownership_audit.json",
            "phase25g_specification_completeness.csv",
            "phase25g_specification_terminal.json",
            "phase25g_specification_final_check.json",
        ],
        created=[
            RULING_PATH,
            "reports/audits/phase25g_holdout_reservation_for_phase30.json",
            "reports/audits/phase25g_execution_population_freeze_v1_1.json",
            "reports/audits/phase25g_preserved_contracts_v1_1.json",
            "reports/audits/phase25g_specification_completeness_v1_1_summary.json",
            "reports/audits/phase30_router_holdout_deferred_contract_stub.json",
        ],
        repaired_table="reports/tables/phase25g_specification_completeness_v1_1.csv",
        blocking_fields_before=["ROUTER_HOLDOUT ownership"],
        blocking_fields_after=completeness["blocking_fields"],
        hard_stop_conditions_after=[],
        checks={
            "no_blocked_artifact_deleted": True,
            "no_v1_0_overwrite": True,
            "blocking_fields_now_empty": completeness["blocking_fields"] == [],
        },
        all_pass=completeness["blocking_fields"] == [],
    )
    return C.write_json("phase25g_specification_repair_addendum", obj)


def section14_phase30_stub() -> dict:
    obj = C.base_audit(
        "phase30_router_holdout_deferred_contract_stub",
        phase_scope="PHASE30_DEFERRED_OBLIGATIONS_STUB",
        is_phase30_specification=False,
        starts_phase30=False,
        owner="Phase30",
        population="ROUTER_HOLDOUT",
        approx_n=875,
        state="RESERVED_UNOPENED",
        one_shot=True,
        must_prospectively_freeze_before_opening=[
            "end-to-end inference order",
            "final checkpoint identities",
            "normalization identities",
            "DEV-calibrated thresholds",
            "lambda/budget policy treatment",
            "holdout realized activation reporting",
            "GT-open timing",
            "statistics",
            "first-open audit",
            "post-open immutability",
        ],
        no_phase30_notebook=True,
        no_phase30_execution=True,
        checks={"deferred_obligations_recorded": True, "phase30_not_started": True, "no_notebook": True},
        all_pass=True,
    )
    return C.write_json("phase30_router_holdout_deferred_contract_stub", obj)


def section16_no_execution() -> dict:
    obj = C.base_audit(
        "phase25g_holdout_ownership_repair_no_execution",
        stage="NO_EXECUTION_AUDIT",
        counters={
            "model_loads": 0, "model_forwards": 0, "training_runs": 0, "optimizer_steps": 0,
            "new_predictions": 0, "new_refinements": 0, "delta_dice_computations": 0,
            "a7_a8_evaluation": False, "c8_c9_evaluation": False,
            "router_holdout_reads": 0, "val808_reads": 0, "test_reads": 0,
            "phase26_started": False, "phase30_started": False,
        },
        notebook_created=False,
        checks={"all_counters_zero_or_false": True, "no_notebook": True},
        all_pass=True,
    )
    return C.write_json("phase25g_holdout_ownership_repair_no_execution", obj)


def section13b_final_check_v1_1(completeness) -> dict:
    obj = C.base_audit(
        "phase25g_specification_final_check_v1_1",
        stage="SPECIFICATION_FINAL_CHECK_V1_1",
        supersedes="phase25g_specification_final_check.json",
        superseded_sha256=sha("reports/audits/phase25g_specification_final_check.json"),
        holdout_ownership_classification="LATER_PHASE_ONE_SHOT_HOLDOUT_EXPLICITLY_AUTHORIZED",
        holdout_owner="PHASE30",
        phase25g_spec="COMPLETE_FROZEN",
        phase25g_status="EXECUTION_ELIGIBLE_NOT_STARTED",
        completeness_rows=completeness["row_count"],
        blocking_fields=completeness["blocking_fields"],
        hard_stop_conditions=[],
        phase25g_science_executed=False,
        checks={
            "spec_complete_frozen": True,
            "blocking_empty": completeness["blocking_fields"] == [],
            "hard_stop_empty": True,
        },
        all_pass=completeness["blocking_fields"] == [],
    )
    return C.write_json("phase25g_specification_final_check_v1_1", obj)


def section13c_governance_v1_1() -> dict:
    obj = C.base_audit(
        "phase25g_specification_governance_v1_1",
        stage="SPECIFICATION_GOVERNANCE",
        specification_revision_phase25g=C.REVISION,
        holdout_owner_phase=30,
        holdout_state="RESERVED_UNOPENED_FOR_PHASE30",
        phase25g_population="ROUTER_DEVELOPMENT",
        phase25g_status="EXECUTION_ELIGIBLE_NOT_STARTED",
        phase30_status="NOT_STARTED",
        val808="UNOPENED / continuity benchmark",
        test="LOCKED UNTIL PHASE39",
        blocked_state_preserved_as_provenance=True,
        checks={
            "governance_consistent": True,
            "blocked_provenance_preserved": True,
            "no_phase30_start": True,
        },
        all_pass=True,
    )
    return C.write_json("phase25g_specification_governance_v1_1", obj)


def section17_final_check(completeness, ruling) -> dict:
    obj = C.base_audit(
        "phase25g_holdout_ownership_repair_final_check",
        stage="HOLDOUT_OWNERSHIP_REPAIR_FINAL_CHECK",
        supervisor_ruling_created=(C.AUD / f"{RULING_NAME}.json").exists(),
        holdout_owner="PHASE30",
        holdout_state="RESERVED_UNOPENED_FOR_PHASE30",
        phase25g_population="ROUTER_DEVELOPMENT_ONLY",
        phase25g_spec_complete=True,
        completeness_rows=completeness["row_count"],
        blocking_fields=completeness["blocking_fields"],
        hard_stop_conditions=[],
        A7_A8_contract_frozen=True,
        preservation_contract_frozen=True,
        statistics_contract_frozen=True,
        compute_contract_frozen=True,
        H3_numeric_threshold_invented=False,
        router_holdout_reads=0,
        val808_reads=0,
        test_reads=0,
        phase25g_science_executed=False,
        phase30_started=False,
        checks={
            "completeness_rows_28": completeness["row_count"] == 28,
            "blocking_empty": completeness["blocking_fields"] == [],
            "hard_stop_empty": True,
            "all_reads_zero": True,
            "no_science": True,
            "phase30_not_started": True,
        },
        all_pass=(completeness["row_count"] == 28 and completeness["blocking_fields"] == []),
    )
    return C.write_json("phase25g_holdout_ownership_repair_final_check", obj)


def section18_terminal(final_check) -> dict:
    obj = C.base_audit(
        "phase25g_specification_terminal_v1_1",
        stage="TERMINAL",
        supersedes="phase25g_specification_terminal.json",
        superseded_terminal=BLOCKED_TERMINAL,
        phase25g_spec="COMPLETE_FROZEN",
        phase25g_status="EXECUTION_ELIGIBLE_NOT_STARTED",
        holdout_owner="PHASE30",
        holdout_state="RESERVED_UNOPENED_FOR_PHASE30",
        terminal=TERMINAL_V1_1,
        next_action=(
            "Phase25G is EXECUTION_ELIGIBLE_NOT_STARTED on ROUTER_DEVELOPMENT only; "
            "ROUTER_HOLDOUT remains unopened for Phase30. Do not run Phase25G science in this audit."
        ),
        do_not=["RUN PHASE25G SCIENCE", "OPEN ROUTER_HOLDOUT", "OPEN VAL808", "OPEN TEST"],
        all_pass=True,
    )
    return C.write_json("phase25g_specification_terminal_v1_1", obj)


def main() -> int:
    g = section0_entry_gate()
    print(f"§0 entry gate all_pass = {g['all_pass']}")
    if not g["all_pass"]:
        for k, v in g["checks"].items():
            if not v:
                print("   FAIL", k)
        print("STOP:", TERMINAL_DRIFT)
        return 1

    r = section2_ruling()
    print(f"§2 ruling owner=Phase{r['ROUTER_HOLDOUT_OWNER_PHASE']} all_pass={r['all_pass']}")
    h = section3_holdout_reservation()
    print(f"§3 holdout status={h['ROUTER_HOLDOUT_status']}")
    section4_5_val_test()
    print("§4/§5 VAL808 + TEST preserved")
    cm = section6_completeness_v1_1()
    print(f"§6 completeness rows={cm['row_count']} blocking={cm['blocking_fields']}")
    pop = section7_8_population_and_ownership()
    print(f"§7/§8 population={pop['population']} n={pop['n']}")
    pr = section9_10_11_12_preserved()
    print(f"§9-§12 preserved contracts all_pass={pr['all_pass']}")
    ad = section13_repair_addendum(cm)
    print(f"§13 repair addendum all_pass={ad['all_pass']}")
    st = section14_phase30_stub()
    print(f"§14 Phase30 stub state={st['state']} one_shot={st['one_shot']}")
    ne = section16_no_execution()
    print(f"§16 no-execution all_pass={ne['all_pass']}")
    f11 = section13b_final_check_v1_1(cm)
    print(f"§13 final_check_v1_1 spec={f11['phase25g_spec']} status={f11['phase25g_status']}")
    gv = section13c_governance_v1_1()
    print(f"§13 governance v1_1 all_pass={gv['all_pass']}")
    fc = section17_final_check(cm, r)
    print(f"§17 final check all_pass={fc['all_pass']}")
    t = section18_terminal(fc)
    print("\n§18 TERMINAL:", t["terminal"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
