"""Build the Phase25G reviewer notebook (41 sections, evaluation-only).

The notebook imports the SAME module functions the driver uses, so driver and notebook
outputs are byte-identical.  It reads frozen Phase25G evaluation artifacts only.
"""
from __future__ import annotations

import nbformat as nbf

SETUP = r'''import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(r"D:\Softfors\jup\scripts\analysis")))
import phase25g_common as C
import phase25g_eval as E
import phase25g_figures as F
import phase25g_nb_support as S

R = E.compute_all()
FIG_PATHS = F.build_all(R)
print("Phase25G reviewer notebook - setup complete")
print("policies:", len(R["pol"]), "| C9 rows:", len(R["c9df"]), "| n_dev:", len(R["ids"]))
print("figures:", len(FIG_PATHS))
print("evidence_class:", C.EVIDENCE_CLASS)
'''


def _cells():
    cells = []
    md = lambda t: cells.append(("md", t))          # noqa: E731
    code = lambda t: cells.append(("code", t))      # noqa: E731

    md("""# Phase25G - Integrated Controlled Development Evaluation (RA-MedFiLM-BARR)

**A7 vs A8 · C8 vs C9 · post-safety effect · integrated preservation · analytical resource accounting**

* Population: **ROUTER_DEVELOPMENT only (n = 4957)**
* ROUTER_HOLDOUT: **RESERVED_UNOPENED_FOR_PHASE30** · VAL808: **UNOPENED** · TEST: **LOCKED UNTIL PHASE39**
* No model training · no forward passes · no new refinement · no router inference · no S_omega inference.
* All scientific results are **reconstructed from the frozen OOF / policy / C9 artifacts**.

This notebook is **evaluation-only** and runs no model.""")
    code(SETUP)

    md("## 1. Title / scope")
    code('S.say("scope: artifact-level integrated development evaluation; '
         'population=ROUTER_DEVELOPMENT (4957); no model, no training, no forward pass")')

    md("## 2. Phase25G v1.1 specification terminal")
    code('S.audit("phase25g_specification_terminal_v1_1.json", '
         '["terminal","phase25g_spec","phase25g_status","holdout_owner","holdout_state","supersedes"])')

    md("## 3. Phase25F predecessor binding")
    code('''d = S.audit("phase25g_predecessor_immutability_gate.json",
            ["n_bound","n_drift","all_pass","bound","drift"])
print()
for k, v in d["bound"].items():
    print(f"{k:58s} {v['sha256'][:16]}")
print()
print("drift:", d["drift"])''')

    md("## 4. Phase30 holdout reservation")
    code('S.audit("phase25g_holdout_reservation_for_phase30.json", '
         '["ROUTER_HOLDOUT_status","one_shot","holdout_opened","before_phase30","all_pass"])')

    md("## 5. No ROUTER_HOLDOUT / VAL808 / TEST assertion")
    code('''print("router_holdout_reads:", 0)
print("val808_reads:", 0)
print("test_reads:", 0)
S.audit("phase25g_phase30_holdout_lock_audit.json", ["router_holdout_state","counters","all_pass"])
S.audit("phase25g_val808_lock_audit.json", ["val808_state","val808_reads","all_pass"])
S.audit("phase25g_test_lock_audit.json", ["test_state","test_reads","all_pass"])''')

    md("""## 6. Controlled meta-level OOF disclosure

Phase25G development results are reconstructed from the **Phase25C OOF refiner outcomes**, the
**Phase25E prospective OOF routing memberships** and the **Phase25F OOF post-safety decisions**.
Phase25F safety OOF operates on a fixed upstream Phase25C OOF feature cache, but upstream 3-fold
refinement cross-fitting and downstream 5-fold safety CV are **not a fully nested end-to-end CV
hierarchy**.  Evidence class = `CONTROLLED_META_LEVEL_OOF_DEVELOPMENT_EVIDENCE`.""")
    code('print("evidence_class:", C.EVIDENCE_CLASS)\n'
         'print("nested_end_to_end_cv:", False)\n'
         'print("independent_validation:", False)\n'
         'print("one_shot_holdout_evidence:", False)')

    md("## 7. Population integrity")
    code('S.audit("phase25g_dev_population_join_integrity.json", '
         '["population","n_expected","n_unique_sample_ids","duplicate_ids","per_source_n",'
         '"identical_across_sources","c9_rows","all_pass"])')

    md("## 8. C8 policy grid")
    code('S.audit("phase25g_policy_grid_integrity.json", '
         '["lambda_grid","budget_grid","n_policies","expected_rows","observed_c9_rows",'
         '"budget_cardinalities","single_lambda_or_budget_selected","all_pass"])')

    md("## 9. Lambda membership redundancy")
    code('''d = S.audit("phase25g_lambda_membership_redundancy_audit.json",
            ["membership_equivalence_group","unique_membership_sets","duplicate_membership_tagged",
             "all_pass","per_budget"])
print()
for b, v in d["per_budget"].items():
    print(f"budget {b}: distinct membership sigs={v['n_distinct_membership_signatures']} "
          f"lambda replicas={v['n_lambda_replicas']} c9_identical={v['c9_identical']}")''')

    md("## 10. C9 manifest integrity")
    code('S.audit("phase25g_c9_integrity.json", '
         '["rows","rows_expected","policies","c9_outcome_domain","c9_state_domain",'
         '"lambda_outcome_consistent_within_budget","all_pass"])')

    md("""## 11. A7 definition

`A7 = Phase25E C8 routing policy + always accept the executed regional candidate` (= C8).
`A7_final_delta_ip = selected_ip * d_i`; `A7_final_dice = global_dice + A7_final_delta`.""")
    code('S.audit("phase25g_reconstruction_integrity.json", ["A7_definition","max_abs_residual_A7","checks"])')

    md("""## 12. A8 definition

`A8 = the exact same routing membership + Phase25F S_omega post-safety decision` (= C9).
`A8_final_delta = d_i if c9_outcome == EXECUTE_THEN_ACCEPT else 0`.""")
    code('S.audit("phase25g_reconstruction_integrity.json", ["A8_definition","max_abs_residual_A8","checks"])')

    md("## 13. A7 / A8 controlled identity")
    code('''d = S.audit("phase25g_a7_a8_identity_control_audit.json",
            ["only_difference","shared_controls","all_pass","per_policy"])
bad = [r["policy_id"] for r in d["per_policy"] if not all(
    v for k, v in r.items() if k not in ("policy_id","shared_lambda","shared_budget"))]
print("policies failing identity control:", bad)''')

    md("## 14. Delta reconstruction identity")
    code('''d = S.audit("phase25g_reconstruction_integrity.json",
            ["identity","max_abs_residual_effect_identity","rows_checked","all_pass"])
print("post_safety_effect identity verified for", d["rows_checked"], "rows")''')

    md("""## 15. Harmful replacement definition

A candidate is harmful for the H3 replacement analysis iff `delta_dice < 0`
(**distinct** from the Phase25C reporting label `HARMFUL <= -0.01`).""")
    code('S.table("phase25g_harmful_replacement_analysis.csv", '
         '["policy_id","lambda","budget","A7_harmful_replacement_count","A7_harmful_replacement_rate",'
         '"A8_harmful_replacement_count","A8_harmful_replacement_rate","absolute_reduction",'
         '"relative_reduction","harm_prevented"])')

    md("## 16. Post-safety rejection accounting")
    code('S.table("phase25g_post_safety_rejection_accounting.csv")\n'
         'S.fig("p25g_rejected_delta_distribution.png")')

    md("## 17. Rejected negative vs positive gain (S_omega trade-off)")
    code('S.table("phase25g_post_safety_tradeoff.csv")\n'
         'S.fig("p25g_harm_prevented_vs_benefit_sacrificed.png")')

    md("## 18. Five unique budgets")
    code('S.table("phase25g_unique_budget_primary_results.csv")')

    md("## 19. Complete 20-policy table")
    code('S.table("phase25g_policy_metrics.csv")')

    md("## 20. A7 integrated results")
    code('S.table("phase25g_policy_metrics.csv", '
         '["policy_id","lambda","budget","selected_count","A7_mean_dice","A7_delta_vs_global",'
         '"A7_macro_domain_delta_vs_global","A7_harmful_replacement_count","A7_harmful_replacement_rate"])')

    md("## 21. A8 integrated results")
    code('S.table("phase25g_policy_metrics.csv", '
         '["policy_id","lambda","budget","selected_count","A8_mean_dice","A8_delta_vs_global",'
         '"A8_macro_domain_delta_vs_global","A8_harmful_replacement_count","A8_harmful_replacement_rate",'
         '"A8_accept_count","A8_reject_count"])')

    md("## 22. A8 - A7 results")
    code('S.table("phase25g_policy_metrics.csv", '
         '["policy_id","lambda","budget","A8_minus_A7","A8_minus_A7_macro_domain","harm_prevented",'
         '"A7_harmful_replacement_rate_minus_A8"])')

    md("## 23. Per-domain results")
    code('S.table("phase25g_integrated_results_by_domain_unique_budget.csv")\n'
         'S.fig("p25g_domain_a7_vs_a8_delta.png")')

    md("## 24. H3 result")
    code('''d = S.audit("phase25g_h3_result.json",
            ["exact_hypothesis","verdict","H3_NUMERICAL_SUCCESS_THRESHOLD_NOT_PRE_REGISTERED",
             "invented_threshold","per_budget"])
print()
for r in d["per_budget"]:
    print({k: r[k] for k in ("budget","A7_harmful_replacement_count","A8_harmful_replacement_count",
                             "absolute_reduction","relative_reduction","paired_p_two_sided")})''')

    md("""## 25. H3 no-pre-registered-numeric-threshold disclosure

No numeric H3 success threshold was pre-registered.  We therefore **do not** manufacture
`PASS` / `FAIL` / `SUPPORTED` / `NOT_SUPPORTED` from an invented cutoff.
`H3_NUMERICAL_SUCCESS_THRESHOLD_NOT_PRE_REGISTERED = true`.""")
    code('print("H3_NUMERICAL_SUCCESS_THRESHOLD_NOT_PRE_REGISTERED = true")\n'
         'print("allowed interpretation: descriptive / statistical report of the reduction in harmful replacement")')

    md("""## 26. Preservation contract

`Delta_preservation = Dice(final routed system) - Dice(global reference)`, margin **0.005**,
claim only if **lower 95% CI > -0.005** (strict).  Per-domain reporting is mandatory; the macro
result may not hide domain harm.  The final integrated statement refers to **A8**.""")
    code('S.audit("phase25g_preservation_adjudication.json", '
         '["rule","margin","claim_only_if","per_domain_reporting","final_integrated_claim_refers_to",'
         '"policy_specific","policy_selected","A8_preservation_all_policies_pass","A8_min_ci_lower",'
         '"any_domain_collapse_A8"])')

    md("## 27. A7 preservation")
    code('S.table_where("phase25g_preservation_noninferiority.csv","arm","A7_PRE_SAFETY_PRESERVATION")\n'
         'S.fig("p25g_preservation_ci_vs_margin.png")')

    md("## 28. A8 preservation")
    code('S.table_where("phase25g_preservation_noninferiority.csv","arm","A8_POST_SAFETY_PRESERVATION")')

    md("## 29. Per-domain preservation")
    code('S.table("phase25g_preservation_by_domain.csv")')

    md("## 30. Bootstrap plan reuse")
    code('S.audit("phase25g_bootstrap_plan_reuse_audit.json", '
         '["bootstrap_type","plan_file_sha256","plan_file_sha256_expected","n_boot","seed",'
         '"total_groups","sample_universe","n_new_bootstrap_samples","all_pass"])')

    md("## 31. Paired bootstrap results")
    code('S.table("phase25g_a8_minus_a7_paired_statistics.csv")\n'
         'S.fig("p25g_a8_minus_a7_effect_by_budget.png")\n'
         'S.fig("p25g_harmful_replacement_rate_by_budget.png")\n'
         'S.fig("p25g_accept_reject_fraction_by_budget.png")')

    md("## 32. Analytical compute contract")
    code('S.audit("phase25g_compute_accounting_audit.json", '
         '["accounting_label","GLOBAL_MACS","ROUTER_MACS","REFINER_MACS","S_OMEGA_MACS",'
         '"A7_average_cost","A8_average_cost","somega_saves_compute",'
         '"A8_minus_A7_equals_a_times_1168","forbidden_claims","all_pass"])')

    md("## 33. A7 / A8 compute comparison")
    code('S.table("phase25g_analytical_compute_accounting.csv", '
         '["policy_id","lambda","budget","activation_fraction","A7_avg_analytical_macs",'
         '"A8_avg_analytical_macs","A8_minus_A7_macs","ratio_A7_vs_global"])')

    md("## 34. Resource / preservation frontier")
    code('S.table("phase25g_resource_preservation_frontier.csv")\n'
         'S.fig("p25g_analytical_compute_frontier.png")\n'
         'S.fig("p25g_a7_vs_a8_macro_delta_by_budget.png")')

    md("## 35. C11 exclusion")
    code('S.audit("phase25g_c11_exclusion_audit.json", '
         '["c11_definition","status","prospectively_authorized","excluded_from_phase25g","all_pass"])')

    md("## 36. Broader-ablation exclusion")
    code('S.audit("phase25g_ablation_scope_audit.json", '
         '["phase25g_core_required_comparison","non_core_ablation_ids","deferred_to_phase28",'
         '"opportunistic_expansion_forbidden","all_pass"])')

    md("""## 37. Interpretation discipline

Phase25G may report: controlled DEV effect of post-safety, policy-specific DEV preservation,
harmful replacement reduction, beneficial-refinement rejection cost, analytical compute increment,
domain heterogeneity.  It may **not** claim holdout/external/TEST performance, deployment safety,
certification, guaranteed preservation, mobile readiness, real-time performance, resource
optimality, best budget, best lambda, best method, or first-ever.""")
    code('''forbidden = ["holdout validation","external validation","TEST performance","deployment safety",
             "certification","guaranteed preservation","mobile readiness","real-time performance",
             "resource optimality","best budget","best lambda","best method","first-ever"]
print("forbidden claims (not made):", forbidden)
print("lambda_selected:", False, "| best_budget_selected:", False, "| policy_selected:", False)''')

    md("""## 38. Phase25 completion implications

Phase25G completes the Phase25 chain (25A–25G).  Phase25 = COMPLETE_CANONICAL.
The integrated controlled development evaluation is frozen; no policy is selected.""")
    code('print("Phase25A..25G = COMPLETE_CANONICAL")\n'
         'print("Phase25 = COMPLETE_CANONICAL")\n'
         'print("policy_selected = false ; lambda_selected = false ; best_budget_selected = false")')

    md("""## 39. Phase26 handoff

Phase26 = ELIGIBLE_NOT_STARTED.  Phase26 may not open ROUTER_HOLDOUT; the one-shot holdout
remains reserved for Phase30.""")
    code('print("Phase26 = ELIGIBLE_NOT_STARTED")\n'
         'print("Phase26 must not open ROUTER_HOLDOUT")')

    md("## 40. Phase30 holdout reservation")
    code('S.audit("phase25g_holdout_reservation_for_phase30.json", '
         '["ROUTER_HOLDOUT_status","phase_gates","one_shot","holdout_opened","all_pass"])')

    md("## 41. Final assertions")
    code('''import numpy as np
assert len(R["pol"]) == 20
assert len(R["c9df"]) == 20 * 4957
assert len(R["ids"]) == 4957
assert R["boot_ci"]["0.10"]["A8_macro"][1] is not None
assert S.audit("phase25g_scope_guard.json", ["all_pass"])["all_pass"]
assert S.audit("phase25g_lambda_membership_redundancy_audit.json", ["all_pass"])["all_pass"]
assert S.audit("phase25g_a7_a8_identity_control_audit.json", ["all_pass"])["all_pass"]
assert S.audit("phase25g_reconstruction_integrity.json", ["all_pass"])["all_pass"]
assert S.audit("phase25g_compute_accounting_audit.json", ["all_pass"])["all_pass"]
assert len(FIG_PATHS) == 9
print("ALL PHASE25G NOTEBOOK ASSERTIONS PASS")
print("policies=20  unique_membership_budgets=5  n_dev=4957  figures=9")''')
    return cells


def build():
    nb = nbf.v4.new_notebook()
    nb.cells = []
    for i, (kind, text) in enumerate(_cells()):
        if kind == "md":
            cell = nbf.v4.new_markdown_cell(text)
        else:
            cell = nbf.v4.new_code_cell(text)
        cell["id"] = f"p25g-cell-{i:03d}"
        nb.cells.append(cell)
    nb.metadata["kernelspec"] = {"name": "jup-venv", "display_name": "jup-venv", "language": "python"}
    nb.metadata["language_info"] = {"name": "python"}
    return nb


if __name__ == "__main__":
    import phase25g_common as C
    C.NB_DIR.mkdir(parents=True, exist_ok=True)
    nbf.write(build(), str(C.NB_DIR / "phase25g_integrated_controlled_evaluation.ipynb"))
    print("written")
