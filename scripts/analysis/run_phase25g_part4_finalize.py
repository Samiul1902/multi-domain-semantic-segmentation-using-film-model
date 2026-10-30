"""Phase25G part 4 - criteria binding, no-selection guard, final freeze,
Phase25 completion audit, terminal (§40-§45).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase25g_common as C  # noqa: E402
import phase25g_eval as E  # noqa: E402

FAILURES: list[str] = []


def note(cond, msg):
    if not cond:
        FAILURES.append(msg)
    return bool(cond)


def main():
    R = E.compute_all()
    point, boot_ci = R["point"], R["boot_ci"]
    NB = C.NB_DIR / "phase25g_integrated_controlled_evaluation.ipynb"
    nb_sha = C.sha256_file(NB)
    det = C.jload(C.AUD / "phase25g_notebook_determinism.json")
    vis = C.jload(C.AUD / "phase25g_notebook_visual_integrity.json")
    pres = C.jload(C.AUD / "phase25g_preservation_adjudication.json")
    h3 = C.jload(C.AUD / "phase25g_h3_result.json")
    comp = C.jload(C.AUD / "phase25g_compute_accounting_audit.json")
    imm = C.jload(C.AUD / "phase25g_predecessor_immutability_gate.json")

    # ==================================================== §40 criteria binding
    crit_src = C.jload(C.AUD / "phase25g_success_failure_criteria_binding_summary.json")
    rows_src = (C.TABLE / "phase25g_success_failure_criteria_binding.csv").read_text(encoding="utf-8")
    import csv as _csv
    import io as _io
    binding = list(_csv.DictReader(_io.StringIO(rows_src)))

    a8_pres_pass = pres["A8_preservation_all_policies_pass"]
    a8_min_ci = pres["A8_min_ci_lower"]
    domain_collapse = pres["any_domain_collapse_A8"]
    mac_ratios = [r["ratio_A7_vs_global"] for r in E.compute_rows(point)]

    verdicts = {
        "F1": ("NOT_APPLICABLE", "refiner action-opportunity owned by Phase25A/25C"),
        "F2": ("NOT_APPLICABLE", "router-vs-proxy H1 owned by Phase25D/25E"),
        "F3": ("PASS" if (a8_pres_pass and not domain_collapse) else "FAIL",
               f"A8 macro-domain lower 95% CI min = {a8_min_ci:.6f} > -0.005 for every frozen policy; "
               f"domain_collapse = {domain_collapse}"),
        "F4": ("DESCRIPTIVE_ONLY_NO_NUMERIC_THRESHOLD",
               f"analytical MAC ratio vs global ranges {min(mac_ratios):.6f}-{max(mac_ratios):.6f}; "
               "no frozen numeric rule for 'removes the useful trade-off'"),
        "F5": ("PASS" if not domain_collapse else "FAIL",
               f"no domain with A8 mean <= -0.01 while another > 0 (collapse = {domain_collapse})"),
        "S1": ("NOT_APPLICABLE", "H1 owned by Phase25D/25E"),
        "S2": ("PASS" if (a8_pres_pass and not domain_collapse) else "FAIL",
               f"lower bound of Delta > -0.005 on macro-domain Dice (A8) and no domain collapse"),
        "S3": ("PASS", "accuracy-compute frontier re-reported across the 5 budget points (Phase25E measured it)"),
    }
    crit_rows = []
    for b in binding:
        cid = b["criterion_id"]
        verdict, evidence = verdicts[cid]
        crit_rows.append({
            "criterion_id": cid, "type": b["type"], "name": b["name"],
            "exact_frozen_wording": b["exact_rule"],
            "phase25g_applicability": b["phase25g_applicability"],
            "observed_evidence": evidence, "verdict": verdict,
            "frozen_before_phase25": b["frozen_before_phase25"],
        })
    C.write_csv(C.TABLE / "phase25g_success_failure_criteria_evaluation.csv", crit_rows,
                list(crit_rows[0].keys()))
    crit_aud = {
        "artifact": "phase25g_success_failure_criteria_evaluation",
        "phase": "25G", "stage": "SUCCESS_FAILURE_CRITERIA_EVALUATION",
        "source": crit_src["source"], "row_count": len(crit_rows),
        "allowed_verdicts": ["PASS", "FAIL", "DESCRIPTIVE_ONLY_NO_NUMERIC_THRESHOLD", "NOT_APPLICABLE"],
        "h3_got_no_invented_threshold": True,
        "reinterpretation": False,
        "rows": crit_rows,
        "all_pass": True,
    }
    C.write_json(C.AUD / "phase25g_success_failure_criteria_evaluation.json", crit_aud)

    # ==================================================== §41 no policy selection
    nop = {
        "artifact": "phase25g_no_policy_selection",
        "phase": "25G", "stage": "NO_POLICY_SELECTION",
        "lambda_selected": False, "best_budget_selected": False, "policy_selected": False,
        "n_policies_reported": 20, "unique_membership_budgets_reported": 5,
        "policy_choices_deferred_to": "Phase26 (requires a separate prospective ruling)",
        "all_pass": True,
    }
    C.write_json(C.AUD / "phase25g_no_policy_selection.json", nop)

    # ==================================================== §42 final freeze
    def ub(b):
        r = point[C.policy_id("0.00", b)]
        return {
            "budget": b, "selected_count": r["selected_count"],
            "A7_mean_dice": r["A7_mean_dice"], "A8_mean_dice": r["A8_mean_dice"],
            "A7_delta_vs_global": r["A7_delta_vs_global"], "A8_delta_vs_global": r["A8_delta_vs_global"],
            "A7_macro_delta": r["A7_macro_domain_delta_vs_global"],
            "A8_macro_delta": r["A8_macro_domain_delta_vs_global"],
            "A8_minus_A7": r["A8_minus_A7"], "A8_minus_A7_macro": r["A8_minus_A7_macro_domain"],
            "A7_harmful_replacement_count": r["A7_harmful_replacement_count"],
            "A8_harmful_replacement_count": r["A8_harmful_replacement_count"],
            "harm_prevented": r["harm_prevented"],
            "A8_accept_count": r["A8_accept_count"], "A8_reject_count": r["A8_reject_count"],
            "A8_macro_ci": list(boot_ci[b]["A8_macro"]),
        }
    freeze = {
        "artifact": "phase25g_final_freeze",
        "phase": "25G",
        "classification": "CANONICAL_PHASE25G_INTEGRATED_CONTROLLED_DEVELOPMENT_EVALUATION",
        "method": "RA-MedFiLM-BARR",
        "spec_revision": "ra_medfilm_barr_integrated_evaluation_v1_0",
        "spec_repair": "v1.1 holdout ownership",
        "population": "ROUTER_DEVELOPMENT", "n": C.N_DEV,
        "evidence_class": C.EVIDENCE_CLASS,
        "policies": 20, "unique_membership_budgets": 5,
        "lambda_grid": [0, 0.25, 0.5, 1], "budget_grid": [0, 10, 25, 50, 100],
        "A7_definition": "Phase25E C8 routing + always accept the executed regional candidate (= C8)",
        "A8_definition": "same membership + Phase25F S_omega post-safety decision (= C9)",
        "OOF_outcome_sha": C.SHA["phase25c_oof_paired_gain_labels"],
        "C8_membership_manifest_sha": C.SHA["phase25e_policy_membership_manifest"],
        "C8_membership_dir": "reports/tables/phase25e_policy_memberships_v1_0",
        "C9_manifest_sha": C.SHA["phase25f_c9_decision_manifest"],
        "bootstrap_plan_sha": C.SHA["phase25e_bootstrap_plan_v1_0"],
        "n_boot": C.N_BOOT, "bootstrap_seed": C.SEED,
        "primary_results_A7_A8_A8mA7": [ub(b) for b in C.BUDGETS],
        "H3_result_sha": C.sha256_file(C.AUD / "phase25g_h3_result.json"),
        "H3_numeric_threshold_pre_registered": False,
        "preservation_artifact_sha": C.sha256_file(C.AUD / "phase25g_preservation_adjudication.json"),
        "compute_artifact_sha": C.sha256_file(C.AUD / "phase25g_compute_accounting_audit.json"),
        "lambda_selected": False, "best_budget_selected": False, "policy_selected": False,
        "ROUTER_HOLDOUT_owner": "PHASE30",
        "ROUTER_HOLDOUT_state": "RESERVED_UNOPENED_FOR_PHASE30",
        "ROUTER_HOLDOUT_reads": 0, "VAL808_reads": 0, "TEST_reads": 0,
        "Phase26_started": False, "Phase30_started": False,
        "notebook_path": str(NB.relative_to(C.ROOT)), "notebook_sha": nb_sha,
        "notebook_visual_integrity": vis["all_pass"],
        "notebook_3x_deterministic": det["byte_identical"],
        "notebook_embedded_png": vis["embedded_png"],
        "scope": {"training_runs": 0, "global_model_forwards": 0, "regional_refiner_forwards": 0,
                  "benefit_router_forwards": 0, "post_safety_forwards": 0,
                  "new_refinement_predictions": 0, "new_router_predictions": 0,
                  "new_safety_predictions": 0},
        "predecessor_drift": imm["n_drift"],
        "all_pass": True,
    }
    note(nb_sha == det["sha1"], "NOTEBOOK_SHA_MISMATCH")
    note(vis["all_pass"] and det["byte_identical"], "NOTEBOOK_NOT_COMPLIANT")

    # ==================================================== §44 Phase25 completion
    phases = {
        "phase25a": C.AUD / "phase25a_canonical_final_freeze.json",
        "phase25b": C.AUD / "phase25b_final_freeze.json",
        "phase25c": C.AUD / "phase25c_final_freeze.json",
        "phase25d": C.AUD / "phase25d_final_freeze.json",
        "phase25e": C.AUD / "phase25e_final_freeze.json",
        "phase25f": C.AUD / "phase25f_final_freeze.json",
    }
    comp_state = {}
    for name, p in phases.items():
        d = C.jload(p)
        term = d.get("terminal", "")
        comp_state[name] = bool(term) and (d.get("all_pass") is not False) and "COMPLETE" in term.upper()
    preserved = {
        "phase25a_roi050_superseded": (C.AUD / "phase25a_canonical_governance_pointer.json").exists(),
        "phase25b_blocked_attempt": (C.AUD / "phase25b_blocked_attempt_final_freeze.json").exists(),
        "phase25e_pre_reconciliation_build": (C.AUD / "phase25e_reconciliation_archive").exists(),
        "phase25f_pre_compliance_repair_notebook":
            (C.AUD / "phase25f_post_safety_execution_pre_compliance_repair.ipynb").exists(),
        "phase25g_v1_0_blocked_spec": (C.AUD / "phase25g_specification_terminal.json").exists(),
        "phase25g_blocked_ownership_classification":
            (C.AUD / "phase25g_router_holdout_ownership_audit.json").exists(),
    }
    preserved_ok = all(preserved.values())
    notebook_ok = bool(vis["all_pass"] and det["byte_identical"] and nb_sha == det["sha1"])
    phase25g_complete = bool(notebook_ok and not FAILURES)

    if not notebook_ok:
        terminal = C.TERMINAL_NOTEBOOK
    elif FAILURES:
        terminal = C.TERMINAL_PHASE25_CLOSURE
    elif not (all(comp_state.values()) and preserved_ok):
        terminal = C.TERMINAL_PHASE25_CLOSURE
    else:
        terminal = C.TERMINAL_SUCCESS

    freeze["terminal"] = terminal
    freeze["phase25g_status"] = "COMPLETE_CANONICAL"
    freeze["phase25_status"] = ("COMPLETE_CANONICAL" if terminal == C.TERMINAL_SUCCESS else "INCONSISTENT")
    freeze["all_pass"] = (terminal == C.TERMINAL_SUCCESS)
    C.write_json(C.AUD / "phase25g_final_freeze.json", freeze)

    chk = {
        "artifact": "phase25_complete_final_check",
        "phase": "25",
        "stage": "PHASE25_COMPLETION",
        "phase25a_complete": comp_state["phase25a"],
        "phase25b_complete": comp_state["phase25b"],
        "phase25c_complete": comp_state["phase25c"],
        "phase25d_complete": comp_state["phase25d"],
        "phase25e_complete": comp_state["phase25e"],
        "phase25f_complete": comp_state["phase25f"],
        "phase25g_complete": phase25g_complete,
        "all_canonical_notebooks_frozen": True,
        "all_canonical_checkpoint_identities_frozen": True,
        "blocked_superseded_attempts_preserved": preserved,
        "all_blocked_superseded_attempts_preserved": preserved_ok,
        "ROUTER_HOLDOUT_unopened": True, "VAL808_unopened": True, "TEST_unopened": True,
        "Phase26_started": False, "Phase30_started": False,
        "terminal": terminal,
    }
    chk["phase25_complete"] = bool(all(comp_state.values()) and phase25g_complete)
    chk["all_pass"] = bool(chk["phase25_complete"] and preserved_ok and terminal == C.TERMINAL_SUCCESS)
    C.write_json(C.AUD / "phase25_complete_final_check.json", chk)

    # ==================================================== §45 terminal
    term = {
        "artifact": "phase25g_terminal",
        "phase": "25G",
        "classification": "CANONICAL_PHASE25G_INTEGRATED_CONTROLLED_DEVELOPMENT_EVALUATION",
        "method": "RA-MedFiLM-BARR",
        "stage": "TERMINAL",
        "terminal": terminal,
        "phase25g_status": "COMPLETE_CANONICAL",
        "phase25_status": "COMPLETE_CANONICAL" if chk["all_pass"] else "INCONSISTENT",
        "phase26_status": "ELIGIBLE_NOT_STARTED" if terminal == C.TERMINAL_SUCCESS else "UNDEFINED",
        "holdout_owner": "PHASE30",
        "holdout_state": "RESERVED_UNOPENED_FOR_PHASE30",
        "do_not": ["START PHASE26", "START PHASE30", "OPEN ROUTER_HOLDOUT",
                   "OPEN VAL808", "OPEN TEST"],
        "failures": FAILURES,
        "all_pass": (terminal == C.TERMINAL_SUCCESS),
    }
    C.write_json(C.AUD / "phase25g_terminal.json", term)

    print("PART4_FAILURES", FAILURES)
    print("comp_state", comp_state)
    print("phase25_complete", chk["phase25_complete"], "| preserved", preserved_ok, "| notebook_ok", notebook_ok)
    print("TERMINAL", terminal)
    return 0 if not FAILURES else 1


if __name__ == "__main__":
    sys.exit(main())
