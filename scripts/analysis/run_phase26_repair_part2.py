"""Phase26 SPECIFICATION REPAIR - PART 2 (§7-§13).

Canonical operating-point freeze: variant, budget selection rule, lambda
representative, exact final-router threshold, other thresholds, state machine.

Governance only - reads frozen Phase25E/25G artifacts, computes no new outcome.

Produces:
  phase26_policy_selection_provenance_v1_0.json
  phase26_budget_selection_ruling_v1_0.json
  phase26_lambda_representative_ruling_v1_0.json
  phase26_canonical_router_threshold_binding_v1_0.json
  phase26_inference_state_machine_v1_0.json
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import phase26_common as C  # noqa: E402

import pandas as pd  # noqa: E402

REVISION = "ra_medfilm_barr_phase26_integration_v1_0"
CLASS = "SUPERVISOR_SPECIFICATION_REPAIR__PHASE26_OPERATIONAL_REDEFINITION"

TERM_THRESHOLD_UNRESOLVED = "PHASE26_SPEC_REPAIR_BLOCKED__CANONICAL_FINAL_ROUTER_THRESHOLD_UNRESOLVED"
TERM_POLICY_BINDING_FAILURE = "PHASE26_SPEC_REPAIR_BLOCKED__DEVELOPMENT_POLICY_RULE_BINDING_FAILURE"

EXPECTED_S1_PASS = {"0.10": True, "0.25": True, "0.50": False}
CANDIDATE_BUDGETS = ["0.10", "0.25", "0.50"]


def say(m):
    print(m, flush=True)


def _sha(rel):
    p = C.ROOT / rel
    return {"path": rel, "exists": p.exists(),
            "sha256": (C.sha256_file(p) if p.is_file() else
                       (C.sha256_dir(p) if p.exists() else None))}


# ============================================================ §8 canonical variant
def section_canonical_variant():
    say("=" * 78)
    say("§8  CANONICAL SYSTEM VARIANT")
    say("=" * 78)
    obj = {
        "artifact": "phase26_canonical_variant_ruling_v1_0",
        "phase": "26", "classification": CLASS, "method": C.METHOD_NAME,
        "revision": REVISION, "governance_only": True,
        "canonical_system_variant": "A8_C9",
        "components": ["Phase25E pre-execution resource gate",
                       "Phase25F post-refinement S_omega fallback"],
        "not_A7_C8": True,
        "reason": ("A8 is the complete Phase24/25 architecture including the frozen "
                   "post-safety component."),
        "h3_formally_passed_claimed": False,
        "h3_note": "No numerical H3 success threshold was pre-registered.",
        "all_pass": True,
    }
    C.write_json(C.AUD / "phase26_canonical_variant_ruling_v1_0.json", obj)
    say(f"  canonical variant = {obj['canonical_system_variant']}")
    return obj


# ============================================================ §9 budget selection
def section_budget_selection():
    say("-" * 78)
    say("§9  CANONICAL BUDGET SELECTION RULE")
    say("-" * 78)

    s1 = pd.read_csv(C.ROOT / "reports/tables/phase25e_s1_primary_vs_multiplicity_sensitivity.csv")
    pres = pd.read_csv(C.ROOT / "reports/tables/phase25g_preservation_noninferiority.csv")

    s1_primary = s1[s1["role"] == "PRIMARY"].copy()
    budgets = []
    binding_disagreement = []

    for b in CANDIDATE_BUDGETS:
        bf = float(b)
        g = s1_primary[s1_primary["budget"] == bf]
        raw_vals = g["raw_significant_at_0.05"].tolist()
        # S1 budget_pass: PRIMARY H1 supported at this budget == ALL PRIMARY comparators significant
        s1_pass = bool(all(raw_vals)) if raw_vals else False
        # A8 preservation
        a8 = pres[(pres["budget"] == bf) & (pres["arm"] == "A8_POST_SAFETY_PRESERVATION")]
        a8_pass = bool(a8["criterion_pass"].all()) if len(a8) else False
        eligible = bool(s1_pass and a8_pass)
        budgets.append({
            "budget": b,
            "s1_primary_pass": s1_pass,
            "s1_primary_raw_significant_values": raw_vals,
            "s1_primary_comparators": g["comparator"].tolist(),
            "a8_preservation_pass": a8_pass,
            "a8_ci_lower_min": float(a8["ci_lower"].min()) if len(a8) else None,
            "eligible": eligible,
        })
        if s1_pass != EXPECTED_S1_PASS[b]:
            binding_disagreement.append(
                {"budget": b, "expected_s1_primary_pass": EXPECTED_S1_PASS[b],
                 "actual_s1_primary_pass": s1_pass})

    eligible_budgets = [r["budget"] for r in budgets if r["eligible"]]
    selected_budget = max(eligible_budgets, key=float) if eligible_budgets else None

    # expected DEV selected count
    exp_count = {"0.00": 0, "0.10": 495, "0.25": 1239, "0.50": 2478, "1.00": 4957}
    selected_count = exp_count.get(selected_budget)

    policy_rule_ok = (binding_disagreement == [] and selected_budget == "0.25")

    obj = {
        "artifact": "phase26_budget_selection_ruling_v1_0",
        "phase": "26", "classification": CLASS, "method": C.METHOD_NAME,
        "revision": REVISION, "governance_only": True,
        "selection_rule": ("largest informative Phase25E PRIMARY H1-passing budget with "
                           "Phase25G A8 preservation pass"),
        "candidate_budgets": CANDIDATE_BUDGETS,
        "excluded_budgets": {"0.00": "endpoint anchor", "1.00": "endpoint anchor"},
        "eligibility_definition": [
            "Phase25E reconciled PRIMARY S1 budget_pass[b] == true",
            "AND Phase25G A8 preservation criterion_pass[b] == true",
        ],
        "per_candidate_binding": budgets,
        "physical_evidence_sources": {
            "s1": _sha("reports/tables/phase25e_s1_primary_vs_multiplicity_sensitivity.csv"),
            "preservation": _sha("reports/tables/phase25g_preservation_noninferiority.csv"),
        },
        "expected_s1_primary_pass": EXPECTED_S1_PASS,
        "binding_disagreements": binding_disagreement,
        "eligible_budgets": eligible_budgets,
        "selected_budget": selected_budget,
        "canonical_budget": 0.25,
        "expected_dev_selected_count": 1239,
        "selected_dev_count": selected_count,
        "selection_rule_frozen_before_holdout": True,
        "selection_rule_frozen_before_phase25g": False,
        "selection_uses_development_evidence": True,
        "holdout_used": False,
        "terminal_on_policy_binding_failure": TERM_POLICY_BINDING_FAILURE,
        "policy_rule_binding_ok": policy_rule_ok,
        "all_pass": policy_rule_ok,
    }
    C.write_json(C.AUD / "phase26_budget_selection_ruling_v1_0.json", obj)

    for r in budgets:
        say(f"    budget {r['budget']}: S1_pass={r['s1_primary_pass']} "
            f"A8_pres={r['a8_preservation_pass']} -> eligible={r['eligible']}")
    say(f"  eligible budgets = {eligible_budgets}")
    say(f"  SELECTED budget = {selected_budget} (DEV count {selected_count})")
    say(f"  binding disagreements = {len(binding_disagreement)}")
    return obj, policy_rule_ok


# ============================================================ §10 lambda
def section_lambda():
    say("-" * 78)
    say("§10 CANONICAL LAMBDA REPRESENTATIVE")
    say("-" * 78)
    obj = {
        "artifact": "phase26_lambda_representative_ruling_v1_0",
        "phase": "26", "classification": CLASS, "method": C.METHOD_NAME,
        "revision": REVISION, "governance_only": True,
        "constant_incremental_action_cost": True,
        "lambda_grid": [0.00, 0.25, 0.50, 1.00],
        "premise": ("Phase25E/25G proved constant incremental action cost; therefore at "
                    "each fixed budget every lambda produces identical membership, so no "
                    "lambda has independent performance evidence."),
        "canonical_lambda_rule": "FIRST_POSITIVE_FROZEN_LAMBDA",
        "canonical_lambda": 0.25,
        "lambda_performance_selected": False,
        "lambda_membership_redundant": True,
        "purpose": "retain an explicit non-zero resource term in the deployed utility expression",
        "forbidden_wording": "'lambda 0.25 performed best'",
        "all_pass": True,
    }
    C.write_json(C.AUD / "phase26_lambda_representative_ruling_v1_0.json", obj)
    say(f"  canonical_lambda = {obj['canonical_lambda']} "
        f"({obj['canonical_lambda_rule']})")
    return obj


# ============================================================ §11 router threshold
def section_router_threshold():
    say("-" * 78)
    say("§11 EXACT FINAL ROUTER THRESHOLD BINDING")
    say("-" * 78)
    from fractions import Fraction

    df = pd.read_csv(C.ROOT / "reports/tables/phase25e_final_router_dev_thresholds.csv",
                     dtype={"budget": str})
    row = df[(df["budget"] == "0.25") & (df["comparator"] == "C7")]
    if len(row) != 1:
        say("  STOP: threshold row not uniquely found")
        return None, False
    r = row.iloc[0]

    tau = Fraction(r["tau"])
    tau_lo = Fraction(r["tau_low"])
    tau_hi = Fraction(r["tau_high"])

    obj = {
        "artifact": "phase26_canonical_router_threshold_binding_v1_0",
        "phase": "26", "classification": CLASS, "method": C.METHOD_NAME,
        "revision": REVISION, "governance_only": True,
        "source_artifact": "reports/tables/phase25e_final_router_dev_thresholds.csv",
        "source_sha256": C.sha256_file(C.ROOT / "reports/tables/phase25e_final_router_dev_thresholds.csv"),
        "policy_id": r["policy_id"],
        "comparator": r["comparator"],
        "budget": "0.25",
        "lambda": 0.25,
        "K_b": int(r["K_b"]),
        "selected_count": int(r["selected_count"]),
        "tau_exact": f"{tau.numerator}/{tau.denominator}",
        "tau_float": float(tau),
        "tau_low_exact": f"{tau_lo.numerator}/{tau_lo.denominator}",
        "tau_high_exact": f"{tau_hi.numerator}/{tau_hi.denominator}",
        "boundary_tied": bool(r["boundary_tied"]),
        "sample_id_cutoff_rank_K": r["sample_id_cutoff_rank_K"],
        "sample_id_cutoff_rank_K1": r["sample_id_cutoff_rank_K1"],
        "threshold_policy": r["threshold_policy"],
        "comparison_operator": "score >= tau -> EXECUTE (rank-based); scalar tau equivalent",
        "score_definition": "routing_score = Delta_hat_Dice - lambda * C_i  (C7 comparator, lambda=0.25)",
        "sample_id_tie_semantics": "rank by score descending, sample_id ascending (lexicographic)",
        "boundary_tie_rule": "persist score boundary and sample_id cutoff; scalar tau alone does not reproduce DEV exact K",
        "normalization_sha256": "ba37742e96610ec5e46fb47c093bf71ae1afd85b2a0db9696b612c873a4ba1fb",
        "router_checkpoint_sha256": "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b",
        "oof_score_threshold_used_for_inference": False,
        "recalibrated": False,
        "holdout_top_k_forcing": False,
        "uniquely_recovered": True,
        "terminal_on_unresolved": TERM_THRESHOLD_UNRESOLVED,
        "all_pass": True,
    }
    C.write_json(C.AUD / "phase26_canonical_router_threshold_binding_v1_0.json", obj)
    say(f"  tau (exact) = {obj['tau_exact']}  (= {obj['tau_float']:.12f})")
    say(f"  K_b = {obj['K_b']}  selected = {obj['selected_count']}")
    say(f"  boundary_tied = {obj['boundary_tied']}")
    return obj, True


# ============================================================ §12 other thresholds
def section_other_thresholds():
    say("-" * 78)
    say("§12 OTHER CANONICAL THRESHOLDS")
    say("-" * 78)
    obj = {
        "artifact": "phase26_other_thresholds_binding_v1_0",
        "phase": "26", "classification": CLASS, "method": C.METHOD_NAME,
        "revision": REVISION, "governance_only": True,
        "roi_proposal_threshold": 0.30,
        "segmentation_output_threshold": 0.50,
        "s_omega_acceptance_probability_threshold": 0.50,
        "s_omega_logit_threshold": 0.0,
        "roi_expansion": 1.50,
        "regional_input_resolution": "256x256",
        "two_distinct_0p50_semantics_conflated": False,
        "all_pass": True,
    }
    C.write_json(C.AUD / "phase26_other_thresholds_binding_v1_0.json", obj)
    say(f"  ROI 0.30 | SEG 0.50 | S_omega prob 0.50 (logit 0.0) | expansion 1.50 | 256x256")
    return obj


# ============================================================ §13 state machine
def section_state_machine():
    say("-" * 78)
    say("§13 INFERENCE STATE MACHINE")
    say("-" * 78)
    obj = {
        "artifact": "phase26_inference_state_machine_v1_0",
        "phase": "26", "classification": CLASS, "method": C.METHOD_NAME,
        "revision": REVISION, "governance_only": True,
        "inputs": ["image x", "task_id t"],
        "steps": [
            {"step": 1, "action": "run frozen GlobalMedFiLM exactly once",
             "outputs": ["p_global", "required frozen feature taps"]},
            {"step": 2, "action": "construct frozen Phase25B router feature vector"},
            {"step": 3, "action": "normalize using frozen Phase25D FINAL normalization"},
            {"step": 4, "action": "run frozen FINAL B_phi"},
            {"step": 5, "action": "compute resource utility using canonical lambda = 0.25"},
            {"step": 6, "action": "compare against frozen canonical 25%-budget DEV-calibrated threshold"},
        ],
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
    C.write_json(C.AUD / "phase26_inference_state_machine_v1_0.json", obj)
    say("  state machine frozen (1 global forward max; SKIP -> p_global; EXECUTE -> S_omega gate)")
    return obj


# ============================================================ §26 provenance
def section_provenance(budget_obj, lam_obj, thr_obj, variant_obj):
    say("-" * 78)
    say("§26 POLICY-SELECTION PROVENANCE")
    say("-" * 78)
    obj = {
        "artifact": "phase26_policy_selection_provenance_v1_0",
        "phase": "26", "classification": CLASS, "method": C.METHOD_NAME,
        "revision": REVISION, "governance_only": True,
        "selection_time": "POST_PHASE25_DEVELOPMENT__PRE_PHASE30_HOLDOUT",
        "development_data_used": True,
        "holdout_used": False,
        "pre_registered_before_phase25": False,
        "frozen_before_phase30": True,
        "selected_system_variant": "A8_C9",
        "selected_budget": 0.25,
        "selected_budget_rule": ("largest informative Phase25E PRIMARY H1-passing budget "
                                 "with Phase25G A8 preservation pass"),
        "lambda_representative": 0.25,
        "lambda_selection_basis": "FIRST_POSITIVE_FROZEN_LAMBDA__MEMBERSHIP_EQUIVALENT",
        "lambda_performance_selected": False,
        "router_threshold_tau_exact": thr_obj["tau_exact"] if thr_obj else None,
        "selection_classification": "DEVELOPMENT_SELECTED_OPERATING_POINT__PRE_HOLDOUT_FREEZE",
        "must_not_be_called": ["pre-registered before Phase25", "holdout-selected",
                               "externally validated", "deployment optimal"],
        "all_pass": True,
    }
    C.write_json(C.AUD / "phase26_policy_selection_provenance_v1_0.json", obj)
    say(f"  selection_time = {obj['selection_time']}")
    say(f"  development_data_used={obj['development_data_used']} holdout_used={obj['holdout_used']}")
    return obj


def main():
    variant = section_canonical_variant()
    budget, policy_ok = section_budget_selection()
    lam = section_lambda()
    thr, thr_ok = section_router_threshold()
    if not thr_ok:
        say("STOP: " + TERM_THRESHOLD_UNRESOLVED)
        return
    section_other_thresholds()
    section_state_machine()
    section_provenance(budget, lam, thr, variant)
    say("")
    say(f"PART 2 complete. policy_rule_binding_ok = {policy_ok}")


if __name__ == "__main__":
    main()
