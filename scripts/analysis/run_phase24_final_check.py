"""Phase 24 (6/6) — final freeze, success-condition check and terminal state.

DESIGN ONLY. Writes:
    reports/audits/phase24_final_freeze.json
    reports/audits/phase24_final_check.json

Verifies the §42 bindings and the §43 success conditions, re-verifies every predecessor
science artifact byte-identical, and emits the §44 terminal state. Does NOT modify any
predecessor artifact.

Usage:
    ./.venv/Scripts/python.exe scripts/analysis/run_phase24_final_check.py
"""
from __future__ import annotations

import hashlib
import json
import re
import csv
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
FIG = ROOT / "reports" / "figures" / "phase24_architecture_spec"
NB = (ROOT / "notebooks/phasewise/phase_24_architecture_spec"
      / "phase24_narrowed_benefit_aware_refinement_spec.ipynb")
REPORT = ROOT / "reports/phase24_narrowed_architecture_spec.md"
PY = ROOT / ".venv/Scripts/python.exe"
UTC = datetime.now(timezone.utc).isoformat()

TERMINAL = ("PHASE24_NARROWED_BENEFIT_AWARE_REFINEMENT_SPEC_COMPLETE"
            "__PHASE25_ELIGIBLE_NOT_STARTED")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def j(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def _rows(p: Path) -> list[dict]:
    """Read a CSV into a list of dicts using the stdlib csv module."""
    if not p.exists():
        return []
    with p.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------- predecessor bindings
PRED = {
    "phase21_best_pt": ROOT / "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt",
    "phase22_protocol": AUD / "phase22_diagnostic_protocol.json",
    "phase22_final_freeze": AUD / "phase22_final_freeze.json",
    "phase23_notebook": (ROOT / "notebooks/phasewise/phase_23_literature_novelty"
                         / "phase23_literature_methodological_novelty_audit.ipynb"),
}
EXPECTED_PRED = {
    "phase21_best_pt": "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7",
    "phase22_protocol": "9d620d6c85276e1a9a086ec60172cdef3b94dc58fe8288222378d196dd4609b7",
    "phase22_final_freeze": "9a0aa2f8c1a2850770fb09f2838e95f0fe08b3b40e55ab1d10c3564841107bca",
    "phase23_notebook": "e9f78ccefd96abad742fa5570a44110cd67c62f5510b99300448e44b961107b0",
}
pred_actual = {k: sha(v) for k, v in PRED.items() if v.exists()}
pred_ok = {k: pred_actual.get(k) == EXPECTED_PRED[k] for k in EXPECTED_PRED}
science_unchanged = all(pred_ok.values())

gate = j(AUD / "phase24_entry_gate.json")
arch = j(AUD / "phase24_architecture_spec.json")
nm = j(AUD / "phase24_method_naming_decision.json")
nov = j(AUD / "phase24_novelty_boundary.json")
dp = j(AUD / "phase24_benefit_data_protocol.json")
gain = j(AUD / "phase24_paired_refinement_gain_contract.json")
res = j(AUD / "phase24_resource_utility_contract.json")
pres = j(AUD / "phase24_preservation_contract.json")
plan = j(AUD / "phase24_phase25_module_plan.json")
ne = j(AUD / "phase24_no_execution_audit.json")
det = j(AUD / "phase24_notebook_determinism.json")
fm = j(FIG / "phase24_figure_manifest.json")

nb_sha = sha(NB) if NB.exists() else "n/a"
fig_shas = {p.name: sha(p) for p in sorted(FIG.glob("*.png"))}

# ---------------------------------------------------------------- §42 bindings
bindings = {
    "phase21_best_pt_sha256": EXPECTED_PRED["phase21_best_pt"],
    "phase21_parameters": 3_523_001,
    "phase22_protocol_sha256": EXPECTED_PRED["phase22_protocol"],
    "phase22_final_freeze_sha256": EXPECTED_PRED["phase22_final_freeze"],
    "phase23_notebook_sha256": EXPECTED_PRED["phase23_notebook"],
    "phase23_verdict": nov.get("phase23_overall_label"),
    "phase23_max_claim_level": nov.get("phase23_maximum_defensible_claim_level"),
    "phase24_method_name": nm.get("frozen_method_name"),
    "phase24_method_name_expansion": nm.get("frozen_method_name_expansion"),
    "phase24_architecture_id": arch.get("architecture_id"),
    "phase24_status": arch.get("status"),
    "phase24_notebook_sha256": nb_sha,
    "phase24_determinism_sha256": det.get("sha256"),
    "phase24_entry_gate_verdict": gate.get("verdict"),
    "phase24_entry_gate_checks": f"{gate.get('n_passed')}/{gate.get('n_checks')}",
    "phase24_no_execution_verdict": ne.get("verdict"),
    "phase24_n_figures": fm.get("n_figures"),
    "phase24_val_role": arch.get("VAL_role", {}).get("role"),
    "phase24_test_lock": arch.get("TEST_lock", {}).get("status"),
    "phase25_started": False,
}

# ---------------------------------------------------------------- §43 success conditions
ne_scan = ne.get("static_scan", {})
checks = [
    ("entry_gate_27_of_27", gate.get("n_passed") == 27 and gate.get("n_failed") == 0),
    ("entry_gate_verdict", gate.get("verdict") == "PHASE24_ENTRY_GATE_PASS"),
    ("method_name_frozen", nm.get("frozen_method_name") == "RA-MedFiLM-BARR"),
    ("forbidden_name_tokens_absent",
     nm.get("forbidden_tokens_check", "").startswith("PASS")),
    ("retired_cbcr", "CBCR" in str(nm.get("retired_name", ""))),
    ("one_name_frozen", nm.get("frozen_method_name") == "RA-MedFiLM-BARR"
     and nm.get("frozen_for_phases") == "25-38"),
    ("arch_design_only", arch.get("status") == "DESIGN_ONLY_NOT_IMPLEMENTED"),
    ("arch_has_all_37_keys", len(arch) >= 44),
    ("global_params_measured_3523001", arch["global_reference"]["parameters"] == 3_523_001),
    ("global_sha_bound",
     arch["global_reference"]["sha256"] == EXPECTED_PRED["phase21_best_pt"]),
    ("refiner_env_0.5M_1.5M_2M",
     arch["regional_refiner"]["target_parameter_envelope"]["recommended_min"] == 500_000
     and arch["regional_refiner"]["target_parameter_envelope"]["recommended_max"] == 1_500_000
     and arch["regional_refiner"]["target_parameter_envelope"]["hard_ceiling"] == 2_000_000),
    ("refiner_env_unmeasured",
     arch["regional_refiner"]["target_parameter_envelope"]["measured"] is False),
    ("refiner_not_frozen_global",
     "frozen Global MedFiLM" in arch["regional_refiner"]["must_not_be"]),
    ("roi_gt_free", arch["region_proposal"]["gt_free"] is True),
    ("roi_no_val_tuning", arch["region_proposal"]["tuning_on_val_forbidden"] is True),
    ("roi_no_gt_rescue", arch["region_proposal"]["gt_rescue_forbidden"] is True),
    ("router_pre_refinement", arch["benefit_router"]["pre_refinement"] is True),
    ("router_gt_free", arch["benefit_router"]["gt_free"] is True),
    ("router_not_uncertainty_predictor",
     "NOT an uncertainty predictor" in arch["benefit_router"]["job"]),
    ("router_max_250k",
     arch["benefit_router"]["target_parameter_envelope"]["max_parameters"] == 250_000),
    ("router_env_unmeasured",
     arch["benefit_router"]["target_parameter_envelope"]["measured"] is False),
    ("router_macs_2pct_preferred_1pct",
     arch["benefit_router"]["compute_envelope"]
     ["max_analytical_macs_fraction_of_one_global_forward"] == 0.02
     and arch["benefit_router"]["compute_envelope"]["preferred_fraction"] == 0.01),
    ("router_macs_unmeasured",
     arch["benefit_router"]["compute_envelope"]["measured"] is False),
    ("feature_reuse_mandatory",
     "MUST reuse F_global" in arch["global_reference"]["feature_reuse_requirement"]),
    ("second_forward_forbidden",
     "FORBIDDEN" in arch["global_reference"]["feature_reuse_requirement"]),
    ("gain_contract_paired",
     gain.get("definition") == "DeltaDice_i = Dice(R_i, y_i) - Dice(G_i, y_i)"),
    ("gain_not_counterfactual",
     "counterfactual effect" in gain.get("must_not_be_described_as", [])),
    ("gain_gt_labels_only",
     gain.get("uses_GT_for_labels") is True and gain.get("uses_GT_for_inputs") is False),
    ("gain_not_router_input", gain.get("computation_used_as_router_input") is False),
    ("utility_form",
     res.get("utility") == "U_hat_i = Delta_hat_i - lambda * C_i"),
    ("single_lambda_forbidden", res.get("single_universal_lambda_forbidden") is True),
    ("budget_grid_5_points",
     res.get("fixed_budget_evaluation", {}).get("points")
     == ["0%", "10%", "25%", "50%", "100%"]),
    ("cost_is_analytical_macs",
     res.get("cost_proxy", {}).get("primary_for_phase25")
     == "normalized analytical incremental MACs"),
    ("analytical_not_latency",
     res.get("cost_proxy", {}).get("analytical_macs_is_not_latency") is True),
    ("device_measurement_phase34",
     res.get("cost_proxy", {}).get("device_measurement_phase") == 34),
    ("preservation_no_destructive_replace",
     pres.get("destructive_replacement_before_final_decision") is False),
    ("preservation_margin_0.005",
     pres.get("non_inferiority", {}).get("margin") == 0.005),
    ("preservation_lower_bound_-0.005",
     pres.get("non_inferiority", {}).get("claim_only_if",
                                        "").startswith("lower confidence bound of Delta > -0.005")),
    ("preservation_per_domain_mandatory",
     pres.get("non_inferiority", {}).get("per_domain_reporting") == "mandatory"),
    ("post_safety_no_compute_saving", arch["post_safety"]["saves_compute"] is False),
    ("post_safety_controlled_ext",
     arch["post_safety"]["classification"] == "CONTROLLED_CORE_EXTENSION"),
    ("post_safety_novelty_false", arch["post_safety"]["novelty_claimed"] is False),
    ("pre_gate_saves_compute_vs_post",
     arch["post_safety"]["saves_compute"] is False
     and arch["pre_execution_gate"]["rule"].startswith("if U_hat_i > tau")),
    ("fusion_no_learned_primary",
     arch["fusion_rule"]["learned_fusion_in_primary"] is False),
    ("one_shared_router",
     "ONE shared router" in arch["task_conditioning"]["primary_design"]),
    ("per_domain_routers_forbidden",
     arch["task_conditioning"]["separate_per_domain_routers"] == "forbidden in the primary design"),
    ("hypotheses_not_results", arch["hypotheses"]["status"] == "HYPOTHESES_NOT_RESULTS"),
    ("H1_load_bearing", arch["hypotheses"]["load_bearing"] == "H1"),
    ("crossfit_3_folds", arch["crossfit_contract"]["folds"] == 3),
    ("crossfit_not_executed", arch["crossfit_contract"]["executed_in_phase24"] is False),
    ("holdout_15pct_875",
     arch["router_holdout_contract"]["fraction_of_original_train"] == 0.15
     and arch["router_holdout_contract"]["approx_cases"] == 875),
    ("holdout_outcomes_zero",
     arch["router_holdout_contract"]["outcomes_read_in_phase24"] == 0),
    ("holdout_designated_before_fitting",
     len(arch["router_holdout_contract"]["designated_before"]) >= 5),
    ("train_only_protocol",
     dp.get("critical_leakage_constraint", "").startswith("Benefit-router training labels MUST NOT")),
    ("train_5832", dp.get("original_train", {}).get("n_cases") == 5832),
    ("dev_85pct_4957",
     dp.get("split", {}).get("ROUTER_DEVELOPMENT", {}).get("approx_cases") == 4957),
    ("split_no_overlap", dp.get("split", {}).get("overlap") == 0),
    ("split_group_safe", dp.get("split", {}).get("group_safe") is True),
    ("split_not_test", dp.get("split", {}).get("uses_test") is False),
    ("split_not_phase22_val", dp.get("split", {}).get("uses_phase22_val") is False),
    ("val_secondary_continuity",
     "SECONDARY" in arch["VAL_role"]["role"] and "CONTINUITY" in arch["VAL_role"]["role"]),
    ("val_not_router_training", arch["VAL_role"]["is_router_training_data"] is False),
    ("val_not_untouched_holdout", arch["VAL_role"]["is_untouched_routing_holdout"] is False),
    ("test_lock_closed", arch["TEST_lock"]["status"] == "CLOSED"),
    ("test_all_zero",
     all(v == 0 for k, v in arch["TEST_lock"].items() if k != "status")),
    ("statistics_boot_2000", arch["statistics"]["n_boot"] == 2000),
    ("statistics_seed_42", arch["statistics"]["seed"] == 42),
    ("statistics_test_unused", arch["statistics"]["test_used"] is False),
    ("comparators_11", len(_rows(TAB / "phase24_comparator_plan.csv")) == 11),
    ("comparators_C1_C11",
     [r["comparator_id"] for r in _rows(TAB / "phase24_comparator_plan.csv")]
     == [f"C{i}" for i in range(1, 12)]),
    ("comparator_C7_primary",
     any(r["comparator_id"] == "C7" and "primary" in r["role"]
         for r in _rows(TAB / "phase24_comparator_plan.csv"))),
    ("comparator_C10_not_deployable",
     any(r["comparator_id"] == "C10" and r["deployable"] == "NO"
         for r in _rows(TAB / "phase24_comparator_plan.csv"))),
    ("ablations_13", len(_rows(TAB / "phase24_ablation_plan.csv")) == 13),
    ("ablations_A0_A8",
     [r["ablation_id"] for r in _rows(TAB / "phase24_ablation_plan.csv")][:9]
     == [f"A{i}" for i in range(9)]),
    ("ablations_none_executed",
     all(r["executed_in_phase24"] == "no" for r in _rows(TAB / "phase24_ablation_plan.csv"))),
    ("criteria_8", len(_rows(TAB / "phase24_success_failure_criteria.csv")) == 8),
    ("criteria_all_frozen",
     all(r["frozen_before_phase25"] == "true"
         for r in _rows(TAB / "phase24_success_failure_criteria.csv"))),
    ("failure_types_F1_F5",
     [r["name"] for r in _rows(TAB / "phase24_success_failure_criteria.csv")][:5]
     == ["REFINER_FAILURE", "ROUTER_FAILURE", "PRESERVATION_FAILURE", "RESOURCE_FAILURE",
         "DOMAIN_COLLAPSE"]),
    ("router_input_contract_31",
     len(_rows(TAB / "phase24_router_input_contract.csv")) == 31),
    ("router_allowed_15_gt_free",
     all(r["uses_GT"] == "false" and r["available_pre_refinement"] == "true"
         and r["inference_available"] == "true"
         for r in _rows(TAB / "phase24_router_input_contract.csv")
         if r["allowed"] == "true")),
    ("router_forbidden_16",
     sum(1 for r in _rows(TAB / "phase24_router_input_contract.csv")
         if r["allowed"] == "false") == 16),
    ("prior_art_12_rows",
     len(_rows(TAB / "phase24_prior_art_differentiation.csv")) == 12),
    ("prior_art_no_ranking",
     not any(c in (_rows(TAB / "phase24_prior_art_differentiation.csv")[0].keys())
             for c in ("rank", "score", "novelty_score"))),
    ("module_plan_7_modules",
     [m["id"] for m in plan.get("modules", [])] == [f"25{c}" for c in "ABCDEFG"]),
    ("module_plan_not_started",
     plan.get("no_module_started") is True and plan.get("phase25_started") is False),
    ("module_25C_before_25D",
     set(plan["modules"][3]["starts_after"]) == {"25C"}),
    ("no_execution_verdict", ne.get("verdict") == "PHASE24_NO_EXECUTION_AUDIT_PASS"),
    ("no_execution_all_zero",
     all(ne.get(k) == 0 for k in
         ("training_runs", "segmentation_inference_calls", "benefit_router_inference_calls",
          "refinement_forward_passes", "optimizers_constructed", "backward_passes",
          "checkpoints_written", "router_holdout_outcomes_read", "val_outcome_reads",
          "test_image_reads", "test_mask_reads", "test_inference_calls",
          "test_visualizations", "phase25_modules_started", "models_instantiated",
          "parameters_measured_of_new_modules"))),
    ("no_execution_static_scan_zero",
     ne_scan.get("total_training_constructs") == 0
     and ne_scan.get("total_inference_constructs") == 0
     and ne_scan.get("total_test_constructs") == 0),
    ("notebook_determinism_3_builds", det.get("n_builds") == 3),
    ("notebook_byte_identical", det.get("byte_identical") is True),
    ("notebook_det_sha_matches", det.get("sha256") == nb_sha),
    ("figures_byte_identical", det.get("figures_byte_identical") is True),
    ("notebook_zero_tracebacks", det.get("zero_tracebacks") is True),
    ("notebook_36_markdown", det.get("n_markdown") == 36),
    ("notebook_6_embedded_png", det.get("embedded_png_outputs") == 6),
    ("figures_6", fm.get("n_figures") == 6 and len(fig_shas) == 6),
    ("figures_no_experimental_results",
     fm.get("contains_experimental_results") is False),
    ("figures_no_hypothetical_curves",
     fm.get("contains_hypothetical_performance_curves") is False),
    ("figures_design_specification_banner",
     fm.get("classification") == "DESIGN_SPECIFICATION_FIGURES"),
    ("report_present", REPORT.exists()),
    ("report_mentions_terminal", TERMINAL.split("__")[0]
     in REPORT.read_text(encoding="utf-8") if REPORT.exists() else False),
    ("novelty_level_2", nov.get("phase23_maximum_defensible_claim_level") == 2),
    ("novelty_level_3_not_supported", nov.get("level_3_status") == "NOT_SUPPORTED"),
    ("novelty_axis_D_strongest", nov.get("phase23_axes", {}).get("strongest_residual") == "D"),
    ("novelty_non_claims_6", len(nov.get("explicit_non_claims", [])) == 6),
    ("no_phase25_artifact", not list(AUD.glob("phase25_*"))),
    ("science_predecessors_unchanged", science_unchanged),
    ("pred_best_pt", pred_ok["phase21_best_pt"]),
    ("pred_protocol", pred_ok["phase22_protocol"]),
    ("pred_freeze", pred_ok["phase22_final_freeze"]),
    ("pred_p23_notebook", pred_ok["phase23_notebook"]),
]

n_pass = sum(1 for _, ok in checks)
n_fail = len(checks) - n_pass
verdict = ("PHASE24_FINAL_CHECK_PASS" if n_fail == 0
           else "PHASE24_FINAL_CHECK_FAIL")

freeze = {
    "artifact": "phase24_final_freeze",
    "phase": 24,
    "classification": "PRE_REGISTRATION_SPECIFICATION",
    "status": "DESIGN_ONLY_NOT_IMPLEMENTED",
    "is_final": True,
    "method_name": nm.get("frozen_method_name"),
    "method_name_expansion": nm.get("frozen_method_name_expansion"),
    "architecture_id": arch.get("architecture_id"),
    "bindings": bindings,
    "predecessor_sha256": pred_actual,
    "predecessor_unchanged": pred_ok,
    "science_unchanged": science_unchanged,
    "artifacts": {
        "audits": sorted(p.name for p in AUD.glob("phase24_*.json")),
        "tables": sorted(p.name for p in TAB.glob("phase24_*.csv")),
        "figures": sorted(fig_shas.keys()),
        "figure_sha256": fig_shas,
        "notebook": str(NB.relative_to(ROOT)).replace("\\", "/"),
        "notebook_sha256": nb_sha,
        "report": str(REPORT.relative_to(ROOT)).replace("\\", "/"),
        "report_sha256": sha(REPORT) if REPORT.exists() else "n/a",
    },
    "counters": {
        "training_runs": 0,
        "segmentation_inference_calls": 0,
        "benefit_router_inference_calls": 0,
        "refinement_forward_passes": 0,
        "router_holdout_outcomes_read": 0,
        "val_outcome_reads": 0,
        "test_image_reads": 0,
        "test_mask_reads": 0,
        "test_inference_calls": 0,
        "test_visualizations": 0,
        "phase25_modules_started": 0,
    },
    "success_conditions_passed": n_pass,
    "success_conditions_total": len(checks),
    "final_check_verdict": verdict,
    "terminal_state": TERMINAL if n_fail == 0 else "PHASE24_NARROWED_SPEC_BLOCKED__REDESIGN_REQUIRED",
    "phase25_started": False,
    "notes": (
        "Phase 24 is a DESIGN-ONLY pre-registration. All parameter and compute targets are "
        "DESIGN TARGETS flagged measured=false. The only measured parameter count is the frozen "
        "Phase-21 global model (3,523,001), measured in Phase 21. No predecessor artifact was "
        "modified by Phase 24."
    ),
    "generated_utc": UTC,
    "test_reads": 0,
}

final_check = {
    "artifact": "phase24_final_check",
    "phase": 24,
    "n_checks": len(checks),
    "n_passed": n_pass,
    "n_failed": n_fail,
    "verdict": verdict,
    "checks": [{"check": n, "pass": ok} for n, ok in checks],
    "terminal_state": freeze["terminal_state"],
    "science_unchanged": science_unchanged,
    "generated_utc": UTC,
    "test_reads": 0,
}

(AUD / "phase24_final_freeze.json").write_text(json.dumps(freeze, indent=1), encoding="utf-8")
(AUD / "phase24_final_check.json").write_text(json.dumps(final_check, indent=1), encoding="utf-8")

print(f"final check: {n_pass}/{len(checks)} PASS  ->  {verdict}")
for n, ok in checks:
    if not ok:
        print("  FAIL:", n)
print()
print("science predecessors unchanged:", science_unchanged)
for k, v in pred_ok.items():
    print(f"  {k:24s} {'OK' if v else 'CHANGED'}")
print()
print("notebook sha :", nb_sha)
print("determinism  :", det.get("sha256"))
print("is_final     :", freeze["is_final"])
print()
print(freeze["terminal_state"])
assert n_fail == 0, f"{n_fail} final-check condition(s) failed"
