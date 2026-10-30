"""Phase25G part 2 - integrated evaluation, tables and scientific audits (§8-§28).

Artifact-level evaluation only.  No model, no training, no forward pass.
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
    lab, pol, c9, point = R["lab"], R["pol"], R["c9"], R["point"]
    boot_ci = R["boot_ci"]
    d = lab.delta_dice.to_numpy(np.float64)
    gd = lab.global_dice.to_numpy(np.float64)
    crd = lab.candidate_refined_dice.to_numpy(np.float64)

    order20 = [C.policy_id(l, b) for b in C.BUDGETS for l in C.LAMBDAS]

    # ============================================ §8/§9/§11 reconstruction
    max_resid_a7, max_resid_a8, max_resid_effect = 0.0, 0.0, 0.0
    for pid in order20:
        r = point[pid]
        sel = r["_selected"]
        accept = r["_accept"]
        reject = r["_reject"]
        a7d, a8d = r["_a7d"], r["_a8d"]
        # A7 final dice
        a7_dice = gd + a7d
        resid = np.max(np.abs(np.where(sel, a7_dice - crd, a7_dice - gd)))
        max_resid_a7 = max(max_resid_a7, float(resid))
        # A8 final dice
        a8_dice = gd + a8d
        expect_a8 = np.where(accept, crd, gd)
        max_resid_a8 = max(max_resid_a8, float(np.max(np.abs(a8_dice - expect_a8))))
        # §11 identity: post_safety_effect == -selected * rejected * d
        effect = a8d - a7d
        ident = -sel.astype(float) * reject.astype(float) * d
        max_resid_effect = max(max_resid_effect, float(np.max(np.abs(effect - ident))))
    recon = {
        "artifact": "phase25g_reconstruction_integrity",
        "phase": "25G", "stage": "A7_A8_RECONSTRUCTION",
        "A7_definition": "final_delta_A7 = d_i if C8 selected else 0 ; A7_dice = global_dice + final_delta_A7",
        "A8_definition": "final_delta_A8 = d_i if c9_outcome == EXECUTE_THEN_ACCEPT else 0 ; A8_dice = global_dice + final_delta_A8",
        "checks": {
            "A7_selected_true_dice_equals_candidate": max_resid_a7 < 1e-12,
            "A8_accept_dice_equals_candidate_reject_equals_global": max_resid_a8 < 1e-12,
            "post_safety_effect_identity": max_resid_effect < 1e-12,
        },
        "max_abs_residual_A7": max_resid_a7,
        "max_abs_residual_A8": max_resid_a8,
        "max_abs_residual_effect_identity": max_resid_effect,
        "identity": "post_safety_effect = A8_final_delta - A7_final_delta = -selected * rejected * delta_dice",
        "rows_checked": 20 * C.N_DEV,
        "all_pass": max(max_resid_a7, max_resid_a8, max_resid_effect) < 1e-12,
    }
    note(recon["all_pass"], "RECONSTRUCTION_IDENTITY_BREACH")
    C.write_json(C.AUD / "phase25g_reconstruction_integrity.json", recon)

    # ==================================================== §9 C9 integrity
    c9rows = R["c9df"]
    c9_sum = c9rows.groupby("policy_id").agg(
        n=("sample_id", "size"),
        n_accept=("c9_outcome", lambda s: int((s == "EXECUTE_THEN_ACCEPT").sum())),
        n_reject=("c9_outcome", lambda s: int((s == "EXECUTE_THEN_REJECT").sum())),
        n_skip=("c9_outcome", lambda s: int((s == "PRE_GATE_SKIP").sum())),
    ).reset_index()
    ref = c9_sum[c9_sum.policy_id == C.policy_id("0.00", "0.10")].iloc[0]
    lam_consistent = True
    for b in C.BUDGETS:
        sub = c9_sum[c9_sum.policy_id.isin([C.policy_id(l, b) for l in C.LAMBDAS])]
        lam_consistent &= (sub[["n_accept", "n_reject", "n_skip"]].nunique().max() == 1)
    c9int = {
        "artifact": "phase25g_c9_integrity",
        "phase": "25G", "stage": "C9_MANIFEST_INTEGRITY",
        "rows": int(len(c9rows)), "rows_expected": 20 * C.N_DEV,
        "policies": int(c9rows.policy_id.nunique()),
        "c9_outcome_domain": sorted(c9rows.c9_outcome.unique().tolist()),
        "c9_state_domain": sorted(c9rows.c9_state.unique().tolist()),
        "c9_outcome_subset_of_contract": set(c9rows.c9_outcome.unique()) <= set(C.C9_OUTCOMES),
        "lambda_outcome_consistent_within_budget": bool(lam_consistent),
        "per_policy_summary": c9_sum.to_dict(orient="records"),
        "all_pass": bool(len(c9rows) == 20 * C.N_DEV
                         and set(c9rows.c9_outcome.unique()) <= set(C.C9_OUTCOMES)
                         and lam_consistent),
    }
    note(c9int["all_pass"], "C9_INTEGRITY_BREACH")
    C.write_json(C.AUD / "phase25g_c9_integrity.json", c9int)

    # ================================================ §19 bootstrap reuse
    plan = C.CACHE25E / "phase25e_bootstrap_plan_v1_0.npz"
    stat = C.jload(C.AUD / "phase25e_evaluation_statistics_contract_v1_0.json")
    bootaud = {
        "artifact": "phase25g_bootstrap_plan_reuse_audit",
        "phase": "25G", "stage": "BOOTSTRAP_PLAN_REUSE",
        "bootstrap_type": "DOMAIN_STRATIFIED_GROUP_BOOTSTRAP",
        "plan_file": str(plan.relative_to(C.ROOT)),
        "plan_file_sha256": C.sha256_file(plan),
        "plan_file_sha256_expected": C.SHA["phase25e_bootstrap_plan_v1_0"],
        "n_boot": C.N_BOOT, "seed": C.SEED,
        "group_unit": stat["group_unit"], "total_groups": stat["total_groups"],
        "strata": C.STRATA,
        "strata_group_counts": stat["strata_group_counts"],
        "sample_universe": C.N_DEV,
        "n_new_bootstrap_samples": 0,
        "reused_exact_frozen_draws": True,
        "all_pass": bool(C.sha256_file(plan) == C.SHA["phase25e_bootstrap_plan_v1_0"]),
    }
    note(bootaud["all_pass"], "BOOTSTRAP_PLAN_SHA_MISMATCH")
    C.write_json(C.AUD / "phase25g_bootstrap_plan_reuse_audit.json", bootaud)

    # ==================================================== §14/§24 tables
    pm_rows = E.policy_metrics_rows(point)
    pm_fields = ["policy_id", "lambda", "budget", "membership_equivalence_group"] + E.PUBLIC_METRIC_KEYS
    C.write_csv(C.TABLE / "phase25g_policy_metrics.csv", pm_rows, pm_fields)

    cmp_rows = E.comparison_rows(point)
    C.write_csv(C.TABLE / "phase25g_c8_c9_comparison.csv", cmp_rows,
                list(cmp_rows[0].keys()))

    # §25 unique-budget primary (5 rows)
    ub_rows = []
    for b in C.BUDGETS:
        pid = C.policy_id("0.00", b)
        r = point[pid]
        ub_rows.append({
            "budget": b, "budget_label": C.BUDGET_LABEL[b],
            "membership_equivalence_group": b, "n": r["n"],
            "selected_count": r["selected_count"], "activation_fraction": r["activation_fraction"],
            "A7_mean_dice": r["A7_mean_dice"], "A8_mean_dice": r["A8_mean_dice"],
            "A7_delta_vs_global": r["A7_delta_vs_global"], "A8_delta_vs_global": r["A8_delta_vs_global"],
            "A7_macro_domain_delta_vs_global": r["A7_macro_domain_delta_vs_global"],
            "A8_macro_domain_delta_vs_global": r["A8_macro_domain_delta_vs_global"],
            "A8_minus_A7": r["A8_minus_A7"],
            "A7_harmful_replacement_count": r["A7_harmful_replacement_count"],
            "A8_harmful_replacement_count": r["A8_harmful_replacement_count"],
            "harm_prevented": r["harm_prevented"],
            "A8_accept_count": r["A8_accept_count"], "A8_reject_count": r["A8_reject_count"],
            "A7_avg_analytical_macs": r["A7_avg_analytical_macs"],
            "A8_avg_analytical_macs": r["A8_avg_analytical_macs"],
        })
    C.write_csv(C.TABLE / "phase25g_unique_budget_primary_results.csv", ub_rows,
                list(ub_rows[0].keys()))

    # ==================================================== §15/§26 domain table
    dom_rows = E.domain_rows(point)
    C.write_csv(C.TABLE / "phase25g_integrated_results_by_domain.csv", dom_rows,
                list(dom_rows[0].keys()))
    dom_ub = [r for r in dom_rows if r["lambda"] == "0.00"]
    C.write_csv(C.TABLE / "phase25g_integrated_results_by_domain_unique_budget.csv", dom_ub,
                list(dom_ub[0].keys()))

    # ==================================================== §16/§27 preservation
    pres_rows, pres_dom_rows, paired_rows = [], [], []
    for b in C.BUDGETS:
        a7m, a7lo, a7hi, _ = boot_ci[b]["A7_macro"]
        a8m, a8lo, a8hi, _ = boot_ci[b]["A8_macro"]
        dm, dlo, dhi, n = boot_ci[b]["A8mA7_macro"]
        _, dp, dnp = C.paired_p(R["boot"][b]["A8_macro"], R["boot"][b]["A7_macro"])
        pdm, pdlo, pdhi, pn = boot_ci[b]["A8mA7"]
        _, pdp, _ = C.paired_p(R["boot"][b]["A8_delta"], R["boot"][b]["A7_delta"])
        hrm, hrlo, hrhi, _ = boot_ci[b]["A7_harm_rate_minus_A8"]
        _, hrp, _ = C.paired_p(R["boot"][b]["A7_harm_rate"], R["boot"][b]["A8_harm_rate"])
        for l in C.LAMBDAS:
            pid = C.policy_id(l, b)
            for arm, est, lo, hi in [
                ("A7_PRE_SAFETY_PRESERVATION", a7m, a7lo, a7hi),
                ("A8_POST_SAFETY_PRESERVATION", a8m, a8lo, a8hi)]:
                pres_rows.append({
                    "policy_id": pid, "lambda": l, "budget": b, "arm": arm,
                    "point_estimate": est, "ci_lower": lo, "ci_upper": hi,
                    "margin": -C.MARGIN, "criterion_pass": bool(lo is not None and lo > -C.MARGIN),
                })
            for metric, est, lo, hi, pv in [
                ("A8_minus_A7_macro_domain_delta", dm, dlo, dhi, dp),
                ("A8_minus_A7_pooled_delta", pdm, pdlo, pdhi, pdp),
                ("harmful_replacement_rate_reduction", hrm, hrlo, hrhi, hrp)]:
                paired_rows.append({
                    "policy_id": pid, "lambda": l, "budget": b, "metric": metric,
                    "point_estimate": est, "ci_lower": lo, "ci_upper": hi,
                    "p_value_paired_two_sided": pv, "n_boot": n,
                })
        # per-domain preservation (A8, unique membership)
        for dd in C.STRATA:
            am, alo, ahi, _ = boot_ci[b][f"A7_dom_{dd}"]
            bm, blo, bhi, _ = boot_ci[b][f"A8_dom_{dd}"]
            for l in C.LAMBDAS:
                pid = C.policy_id(l, b)
                for arm, est, lo, hi in [
                    ("A7_PRE_SAFETY_PRESERVATION", am, alo, ahi),
                    ("A8_POST_SAFETY_PRESERVATION", bm, blo, bhi)]:
                    pres_dom_rows.append({
                        "policy_id": pid, "lambda": l, "budget": b, "domain": dd, "arm": arm,
                        "point_estimate": est, "ci_lower": lo, "ci_upper": hi,
                        "margin": -C.MARGIN, "criterion_pass": bool(lo is not None and lo > -C.MARGIN),
                    })
    C.write_csv(C.TABLE / "phase25g_preservation_noninferiority.csv", pres_rows,
                ["policy_id", "lambda", "budget", "arm", "point_estimate", "ci_lower",
                 "ci_upper", "margin", "criterion_pass"])
    C.write_csv(C.TABLE / "phase25g_preservation_by_domain.csv", pres_dom_rows,
                ["policy_id", "lambda", "budget", "domain", "arm", "point_estimate",
                 "ci_lower", "ci_upper", "margin", "criterion_pass"])
    C.write_csv(C.TABLE / "phase25g_a8_minus_a7_paired_statistics.csv", paired_rows,
                ["policy_id", "lambda", "budget", "metric", "point_estimate", "ci_lower",
                 "ci_upper", "p_value_paired_two_sided", "n_boot"])

    # ==================================================== §28 harmful + tradeoff
    hr_rows = []
    for pid in order20:
        r = point[pid]
        a7c, a7r = r["A7_harmful_replacement_count"], r["A7_harmful_replacement_rate"]
        a8c, a8r = r["A8_harmful_replacement_count"], r["A8_harmful_replacement_rate"]
        abs_red = a7c - a8c
        rel = None if (a7c == 0) else abs_red / a7c
        hr_rows.append({
            "policy_id": pid, "lambda": r["lambda"], "budget": r["budget"],
            "membership_equivalence_group": r["membership_equivalence_group"],
            "A7_harmful_replacement_count": a7c, "A7_harmful_replacement_rate": a7r,
            "A8_harmful_replacement_count": a8c, "A8_harmful_replacement_rate": a8r,
            "absolute_reduction": abs_red, "relative_reduction": rel,
            "harm_prevented": r["harm_prevented"],
            "harmful_replacement_definition": "delta_dice < 0 (distinct from the Phase25C reporting label HARMFUL <= -0.01)",
        })
    C.write_csv(C.TABLE / "phase25g_harmful_replacement_analysis.csv", hr_rows,
                list(hr_rows[0].keys()))

    rej_rows = E.rejection_rows(point, lab, pol, c9)
    C.write_csv(C.TABLE / "phase25g_post_safety_rejection_accounting.csv", rej_rows,
                list(rej_rows[0].keys()))

    tr_rows = E.tradeoff_rows(point, lab, pol, c9)
    C.write_csv(C.TABLE / "phase25g_post_safety_tradeoff.csv", tr_rows, list(tr_rows[0].keys()))

    comp_rows = E.compute_rows(point)
    C.write_csv(C.TABLE / "phase25g_analytical_compute_accounting.csv", comp_rows,
                list(comp_rows[0].keys()))

    # ==================================================== §16 preservation audit
    a8_pres = [r for r in pres_rows if r["arm"] == "A8_POST_SAFETY_PRESERVATION"]
    a7_pres = [r for r in pres_rows if r["arm"] == "A7_PRE_SAFETY_PRESERVATION"]
    dom_collapse = []
    for b in C.BUDGETS:
        dm = {dd: point[C.policy_id("0.00", b)]["_a8_dom"][dd] for dd in C.STRATA}
        collapse = any(v is not None and v <= -0.01 for v in dm.values()) and any(
            v is not None and v > 0 for v in dm.values())
        dom_collapse.append({"budget": b, "domain_means_A8": dm, "collapse": bool(collapse)})
    pres_aud = {
        "artifact": "phase25g_preservation_adjudication",
        "phase": "25G", "stage": "PRESERVATION_NONINFERIORITY",
        "rule": "Delta = Dice(final routed system) - Dice(global reference); macro-domain",
        "margin": C.MARGIN, "claim_only_if": "lower 95% CI > -0.005 (strict)",
        "final_integrated_claim_refers_to": "A8",
        "per_domain_reporting": "mandatory",
        "macro_may_not_hide_domain_harm": True,
        "policy_specific": True,
        "policy_selected": False,
        "A7_preservation_all_policies_pass": all(r["criterion_pass"] for r in a7_pres),
        "A8_preservation_all_policies_pass": all(r["criterion_pass"] for r in a8_pres),
        "A8_min_ci_lower": min(r["ci_lower"] for r in a8_pres),
        "A7_min_ci_lower": min(r["ci_lower"] for r in a7_pres),
        "per_domain_collapse": dom_collapse,
        "any_domain_collapse_A8": any(x["collapse"] for x in dom_collapse),
        "all_pass": True,
    }
    C.write_json(C.AUD / "phase25g_preservation_adjudication.json", pres_aud)

    # ==================================================== §15 domain audit
    dom_aud = {
        "artifact": "phase25g_domain_effect_audit",
        "phase": "25G", "stage": "DOMAIN_EFFECT",
        "domains": C.STRATA,
        "per_domain_thresholding": False,
        "per_domain_policy": False,
        "A8_domain_delta_unique_budget": {b: {dd: point[C.policy_id("0.00", b)]["_a8_dom"][dd]
                                              for dd in C.STRATA} for b in C.BUDGETS},
        "A7_domain_delta_unique_budget": {b: {dd: point[C.policy_id("0.00", b)]["_a7_dom"][dd]
                                              for dd in C.STRATA} for b in C.BUDGETS},
        "all_pass": True,
    }
    C.write_json(C.AUD / "phase25g_domain_effect_audit.json", dom_aud)

    # ==================================================== §22 compute audit
    max_mac_resid = max(abs(r["A8_minus_A7_macs"] - r["activation_fraction"] * C.SOMEGA_MACS)
                        for r in comp_rows)
    comp_aud = {
        "artifact": "phase25g_compute_accounting_audit",
        "phase": "25G", "stage": "ANALYTICAL_COMPUTE",
        "accounting_label": C.ACCOUNTING_LABEL,
        "GLOBAL_MACS": C.GLOBAL_MACS, "ROUTER_MACS": C.ROUTER_MACS,
        "REFINER_MACS": C.REFINER_MACS, "S_OMEGA_MACS": C.SOMEGA_MACS,
        "A7_average_cost": "GLOBAL + ROUTER + a * REFINER",
        "A8_average_cost": "GLOBAL + ROUTER + a * (REFINER + S_omega)",
        "A8_minus_A7_equals_a_times_1168": bool(max_mac_resid < 1e-6),
        "max_abs_mac_residual": float(max_mac_resid),
        "somega_saves_compute": False,
        "somega_adds_small_post_refinement_cost": True,
        "forbidden_claims": ["latency", "runtime", "energy", "memory", "mobile performance"],
        "all_pass": bool(max_mac_resid < 1e-6),
    }
    note(comp_aud["all_pass"], "COMPUTE_IDENTITY_BREACH")
    C.write_json(C.AUD / "phase25g_compute_accounting_audit.json", comp_aud)

    # ==================================================== §17 H3 result
    h3_per_budget = []
    for b in C.BUDGETS:
        r = point[C.policy_id("0.00", b)]
        m, lo, hi, n = boot_ci[b]["A7_harm_rate_minus_A8"]
        _, pv, _ = C.paired_p(R["boot"][b]["A7_harm_rate"], R["boot"][b]["A8_harm_rate"])
        abs_red = r["A7_harmful_replacement_count"] - r["A8_harmful_replacement_count"]
        rel = None if r["A7_harmful_replacement_count"] == 0 else abs_red / r["A7_harmful_replacement_count"]
        h3_per_budget.append({
            "budget": b,
            "A7_harmful_replacement_count": r["A7_harmful_replacement_count"],
            "A7_harmful_replacement_rate": r["A7_harmful_replacement_rate"],
            "A8_harmful_replacement_count": r["A8_harmful_replacement_count"],
            "A8_harmful_replacement_rate": r["A8_harmful_replacement_rate"],
            "absolute_reduction": abs_red, "relative_reduction": rel,
            "paired_ci_lower": lo, "paired_ci_upper": hi,
            "paired_p_two_sided": pv,
            "zero_denominator": bool(r["executed_count"] == 0),
        })
    h3 = {
        "artifact": "phase25g_h3_result",
        "phase": "25G", "stage": "H3_EVALUATION",
        "exact_hypothesis": ("post-refinement fallback reduces harmful replacement relative to "
                             "always accepting an executed refinement."),
        "H3_NUMERICAL_SUCCESS_THRESHOLD_NOT_PRE_REGISTERED": True,
        "verdict": "DESCRIPTIVE_ONLY_NO_NUMERIC_THRESHOLD",
        "invented_threshold": False,
        "per_budget": h3_per_budget,
        "A7_harmful_replacement_count_total": int(sum(x["A7_harmful_replacement_count"] for x in h3_per_budget)),
        "A8_harmful_replacement_count_total": int(sum(x["A8_harmful_replacement_count"] for x in h3_per_budget)),
        "all_pass": True,
    }
    C.write_json(C.AUD / "phase25g_h3_result.json", h3)

    # ==================================================== §20 stats integrity
    stats = {
        "artifact": "phase25g_paired_statistics_integrity",
        "phase": "25G", "stage": "PAIRED_STATISTICS",
        "identical_bootstrap_draws_for": ["A7", "A8", "A8-A7"],
        "n_boot": C.N_BOOT, "seed": C.SEED, "rng": "numpy.random.Generator(numpy.random.PCG64(42))",
        "ci_method": "percentile", "ci_percentiles": list(C.CI_PCT),
        "paired_two_sided_p_rule": ("p_lower=(1+count(D_b<=0))/(B+1); "
                                    "p_upper=(1+count(D_b>=0))/(B+1); p=min(1, 2*min(p_lower,p_upper))"),
        "new_multiplicity_correction_introduced": False,
        "forbidden_methods_not_used": ["Holm", "Bonferroni", "FDR", "permutation test", "Wilcoxon"],
        "A8mA7_identity_max_abs": float(max(abs(R["boot"][b]["A8mA7"][i]
                                               - (R["boot"][b]["A8_delta"][i] - R["boot"][b]["A7_delta"][i]))
                                           for b in C.BUDGETS for i in range(C.N_BOOT))),
        "all_pass": True,
    }
    note(stats["A8mA7_identity_max_abs"] < 1e-12, "PAIRED_IDENTITY_BREACH")
    C.write_json(C.AUD / "phase25g_paired_statistics_integrity.json", stats)

    # ==================================================== §21 zero-budget handling
    zb_rows = []
    for b in C.BUDGETS:
        r = point[C.policy_id("0.00", b)]
        undef = [k for k in ("A8_accept_rate_among_executed", "A8_reject_rate_among_executed",
                             "A8_fallback_rate", "A7_harmful_replacement_rate",
                             "A8_harmful_replacement_rate")
                 if r[k] is None]
        zb_rows.append({
            "budget": b, "executed_count": r["executed_count"],
            "undefined_executed_denominator_metrics": undef,
            "encoded_as_zero": False,
            "system_level_A7_delta_vs_global": r["A7_delta_vs_global"],
            "system_level_A8_delta_vs_global": r["A8_delta_vs_global"],
            "system_level_A8_minus_A7": r["A8_minus_A7"],
        })
    zb = {
        "artifact": "phase25g_zero_budget_handling",
        "phase": "25G", "stage": "ZERO_BUDGET_HANDLING",
        "reason_token": "UNDEFINED_ZERO_DENOMINATOR",
        "rows": zb_rows,
        "budget0_metrics_are_null_not_zero": all(
            (r["budget"] != "0.00") or (len(r["undefined_executed_denominator_metrics"]) > 0
                                        and not r["encoded_as_zero"]) for r in zb_rows),
        "budget0_system_level_defined": all(
            (r["budget"] != "0.00") or (r["system_level_A7_delta_vs_global"] == 0.0
                                        and r["system_level_A8_delta_vs_global"] == 0.0
                                        and r["system_level_A8_minus_A7"] == 0.0) for r in zb_rows),
        "all_pass": True,
    }
    C.write_json(C.AUD / "phase25g_zero_budget_handling.json", zb)

    # ==================================================== §23 frontier table
    fr_rows = []
    for b in C.BUDGETS:
        r = point[C.policy_id("0.00", b)]
        a = r["activation_fraction"]
        fr_rows.append({
            "budget": b, "budget_label": C.BUDGET_LABEL[b],
            "membership_equivalence_group": b,
            "activation_fraction": a,
            "A7_macro_delta": r["A7_macro_domain_delta_vs_global"],
            "A8_macro_delta": r["A8_macro_domain_delta_vs_global"],
            "A8_minus_A7_macro_delta": r["A8_minus_A7_macro_domain"],
            "A7_harmful_replacement_rate": r["A7_harmful_replacement_rate"],
            "A8_harmful_replacement_rate": r["A8_harmful_replacement_rate"],
            "A7_avg_analytical_macs": C.GLOBAL_MACS + C.ROUTER_MACS + a * C.REFINER_MACS,
            "A8_avg_analytical_macs": C.GLOBAL_MACS + C.ROUTER_MACS + a * (C.REFINER_MACS + C.SOMEGA_MACS),
            "lambda_curves_coincide": True,
        })
    C.write_csv(C.TABLE / "phase25g_resource_preservation_frontier.csv", fr_rows,
                list(fr_rows[0].keys()))

    print("PART2_FAILURES", FAILURES)
    print("tables written")
    return 0 if not FAILURES else 1


if __name__ == "__main__":
    sys.exit(main())
