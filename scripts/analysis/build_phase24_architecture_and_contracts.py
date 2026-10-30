"""Phase 24 (2/4) — architecture spec, contracts and control tables.

DESIGN ONLY. No training, no inference, no TEST access, no parameter counting of
any not-yet-built module (all targets are DESIGN TARGETS, explicitly unmeasured).

Writes:
    reports/audits/phase24_architecture_spec.json
    reports/audits/phase24_paired_refinement_gain_contract.json
    reports/audits/phase24_resource_utility_contract.json
    reports/audits/phase24_preservation_contract.json
    reports/audits/phase24_novelty_boundary.json
    reports/audits/phase24_benefit_data_protocol.json
    reports/audits/phase24_phase25_module_plan.json
    reports/tables/phase24_module_spec.csv
    reports/tables/phase24_router_input_contract.csv
    reports/tables/phase24_data_role_contract.csv
    reports/tables/phase24_comparator_plan.csv
    reports/tables/phase24_ablation_plan.csv
    reports/tables/phase24_success_failure_criteria.csv

Usage:
    ./.venv/Scripts/python.exe scripts/analysis/build_phase24_architecture_and_contracts.py
"""
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
TAB.mkdir(parents=True, exist_ok=True)
UTC = datetime.now(timezone.utc).isoformat()

METHOD = "RA-MedFiLM-BARR"
ARCH_ID = "ra_medfilm_barr_narrowed_v1"
GLOBAL_ARCH = "global_medfilm_shared_residual_unet_film5_no_se_no_deep_supervision_v1"
GLOBAL_PARAMS = 3_523_001


def w_json(name: str, obj: dict) -> None:
    obj.setdefault("test_reads", 0)
    (AUD / name).write_text(json.dumps(obj, indent=1), encoding="utf-8")
    print("  wrote", name)


def w_csv(name: str, cols: list[str], rows: list[list]) -> None:
    with (TAB / name).open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in rows:
            w.writerow(r)
    print(f"  wrote {name} ({len(rows)} rows x {len(cols)} cols)")


# ===========================================================================
# ARCHITECTURE SPEC (§37)
# ===========================================================================
architecture = {
    "artifact": "phase24_architecture_spec",
    "phase": 24,
    "status": "DESIGN_ONLY_NOT_IMPLEMENTED",
    "architecture_id": ARCH_ID,
    "method_name": METHOD,
    "method_name_expansion":
        "Resource-Aware MedFiLM with Benefit-Aware Refinement Routing",
    "scientific_scope": (
        "A pre-registered design for a learned GT-free predictor of PAIRED REFINEMENT GAIN, "
        "evaluated BEFORE an optional expensive regional refinement, used for execute/skip "
        "routing inside a shared multi-domain medical-segmentation system, with a structural "
        "preservation fallback and an explicit resource-cost term in the decision utility."
    ),
    "contribution_type": (
        "SYSTEM / INTEGRATION contribution. Phase 23 established that each individual primitive "
        "(gate mechanism, paired-gain target, multi-domain sharing, resource awareness) is "
        "OCCUPIED. No novelty is claimed for any primitive."
    ),
    "novelty_boundary_ref": "phase24_novelty_boundary.json",

    "global_reference": {
        "role": "frozen anchor; produces the fallback output and the reusable features",
        "phase21_checkpoint":
            "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt",
        "sha256": "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7",
        "architecture": GLOBAL_ARCH,
        "parameters": GLOBAL_PARAMS,
        "signature": "G(x, t) -> (p_global, F_global)",
        "x": "input image",
        "t": "allowed task/domain ID",
        "p_global": "global probability map",
        "F_global": "reusable intermediate features already produced by the global forward",
        "modification_policy": (
            "MUST NOT be modified during the initial controlled Phase-25 experiments. Any "
            "fine-tuning of the global model is a separate, later, explicitly authorised change."
        ),
        "feature_reuse_requirement": (
            "The router MUST reuse F_global. A SECOND full Global MedFiLM forward purely to make "
            "the routing decision is FORBIDDEN: it would destroy the compute-saving claim (C4)."
        ),
    },

    "region_proposal": {
        "gt_free": True,
        "frozen_rule": (
            "p_global predicted foreground -> tight bounding box -> fixed context expansion -> "
            "clip to image -> square pad -> resize to regional-refiner resolution"
        ),
        "constants_source": "TRAIN only (context expansion factor, refiner resolution)",
        "tuning_on_val_forbidden": True,
        "empty_global_prediction_primary_behavior": "A_SKIP_REFINEMENT",
        "empty_global_prediction_justification": (
            "Option A (skip) is chosen as the PRIMARY prospective behaviour because it is the "
            "minimal, GT-free, zero-extra-cost rule: if the global model predicts no foreground, "
            "there is no region to refine and the global output is preserved by the fallback. "
            "Option B (deterministic cheap uncertainty-based rescue) is retained ONLY as a "
            "pre-registered controlled ablation, and any constant it uses must be derived from "
            "TRAIN only, frozen before Phase 25."
        ),
        "gt_rescue_forbidden": True,
    },

    "regional_refiner": {
        "symbol": "R_psi",
        "role": "produces the optional refinement R(x_crop)",
        "must_not_be": (
            "the frozen Global MedFiLM checkpoint reused on resampled crops. Phase 22 showed "
            "that reuse was HARMFUL in aggregate."
        ),
        "class": "dedicated crop-trained lightweight residual U-Net / encoder-decoder",
        "input_contract": {
            "channels": ["R", "G", "B", "p_global_crop"],
            "conceptual": "[R, G, B, p_global]",
            "task_conditioning": "allowed (task/domain embedding, e.g. FiLM-style)",
            "forbidden_inputs": [
                "GT mask", "GT geometry", "GT size category", "any GT-derived score",
            ],
        },
        "target_parameter_envelope": {
            "recommended_min": 500_000,
            "recommended_max": 1_500_000,
            "hard_ceiling": 2_000_000,
            "measured": False,
            "note": "DESIGN TARGETS ONLY. Not implemented, not counted, not achieved.",
        },
        "avoid": ["large transformer", "foundation-model decoder",
                  "oversized pretrained backbone"],
        "conditioning": "task/domain embedding permitted; shared across domains",
        "fusion_role": "its output is a CANDIDATE, never a replacement, until the final selection",
        "novelty_claimed": False,
    },

    "benefit_router": {
        "symbol": "B_phi",
        "job": (
            "estimate the expected PAIRED REFINEMENT GAIN before R_psi executes. It is NOT an "
            "uncertainty predictor."
        ),
        "pre_refinement": True,
        "gt_free": True,
        "allowed_inputs_ref": "reports/tables/phase24_router_input_contract.csv",
        "forbidden_inputs": [
            "GT mask", "GT foreground fraction", "GT size label", "Dice", "IoU", "recall",
            "precision", "specificity", "MCC", "GT-derived ECE", "GT-derived Brier",
            "oracle ROI", "true DeltaDice", "refined prediction", "refiner feature maps",
            "post-refinement statistics",
        ],
        "output": {
            "primary": "Delta_hat_Dice (predicted paired Dice gain)",
            "optional_auxiliary": "p_harm (probability the refinement is harmful)",
        },
        "architecture_family": "small MLP / shallow feature-fusion network",
        "forbidden_architecture": [
            "transformer router", "foundation model", "second image encoder",
        ],
        "target_parameter_envelope": {
            "max_parameters": 250_000,
            "measured": False,
            "note": "DESIGN TARGET ONLY.",
        },
        "compute_envelope": {
            "max_analytical_macs_fraction_of_one_global_forward": 0.02,
            "preferred_fraction": 0.01,
            "measured": False,
            "note": "DESIGN TARGET ONLY; measured in Phase 25.",
        },
    },

    "paired_gain_target_ref": "phase24_paired_refinement_gain_contract.json",
    "resource_utility_ref": "phase24_resource_utility_contract.json",
    "pre_execution_gate": {
        "rule": "if U_hat_i > tau then EXECUTE else SKIP",
        "U_hat_i": "Delta_hat_i - lambda * C_i",
        "evaluated_before": "R_psi execution",
        "single_universal_lambda_forbidden": True,
        "fixed_budget_points": ["0%", "10%", "25%", "50%", "100%"],
        "threshold_calibration": "TRAIN development only",
    },
    "post_safety": {
        "symbol": "S_omega",
        "role": "quality preservation AFTER refinement",
        "saves_compute": False,
        "importance": (
            "This is the component closest to JFS. S_omega must NEVER be presented as the "
            "compute-saving mechanism, because JFS already occupies the post-hoc decision."
        ),
        "deployment_inputs_gt_free": True,
        "classification": "CONTROLLED_CORE_EXTENSION",
        "mandatory_ablation": "A7 (router, no post-safety) vs A8 (router + post-safety)",
        "novelty_claimed": False,
    },
    "fusion_rule": {
        "primary": "outside ROI retain p_global; inside ROI replace with p_refined",
        "learned_fusion_in_primary": False,
        "reason": "avoid confounding the benefit-routing hypothesis",
        "learned_fusion": "future controlled ablation only",
    },
    "fallback_rule_ref": "phase24_preservation_contract.json",
    "task_conditioning": {
        "primary_design": "ONE shared router with task/domain conditioning allowed",
        "separate_per_domain_routers": "forbidden in the primary design",
        "reason": "preserve the shared multi-domain system contribution",
        "domain_specific_routers": "later controlled ablations only",
    },
    "training_stage_contract": {
        "stages_executed_in_phase24": 0,
        "plan": "Phase 25 modules 25A-25G (see phase24_phase25_module_plan.json)",
        "stage_ordering_constraint": (
            "The benefit router may only be fitted AFTER out-of-fold gain labels exist (25C "
            "precedes 25D). The refiner must be cross-fitted, never fit and evaluated on the "
            "same samples."
        ),
    },
    "data_role_contract_ref": "reports/tables/phase24_data_role_contract.csv",
    "crossfit_contract": {
        "folds": 3,
        "within": "ROUTER_DEVELOPMENT subset of original TRAIN",
        "procedure": (
            "For fold k: train R_psi on folds != k, infer R_psi on fold k, compute "
            "DeltaDice_i = Dice(R_i, GT) - Dice(G_i, GT) for fold-k samples."
        ),
        "output": "concatenated out-of-fold (OOF) paired-gain labels",
        "executed_in_phase24": False,
    },
    "router_holdout_contract": {
        "fraction_of_original_train": 0.15,
        "approx_cases": 875,
        "designated_before": [
            "refiner performance inspection", "benefit-router fitting",
            "feature selection based on performance", "lambda selection",
            "threshold fitting",
        ],
        "inspected_in_phase24": ["sample_ids", "domain_counts", "group_integrity",
                                 "manifest_sha", "split_seed"],
        "must_not_inspect_in_phase24": [
            "DeltaDice distribution", "Dice", "router AUC", "benefit distribution",
            "routing policy performance",
        ],
        "outcomes_read_in_phase24": 0,
    },
    "VAL_role": {
        "population": "existing frozen Phase-22 808-case VAL",
        "role": "SECONDARY / CONTINUITY DEVELOPMENT BENCHMARK",
        "is_router_training_data": False,
        "is_untouched_routing_holdout": False,
        "explicit_in_all_protocol_artifacts": True,
    },
    "TEST_lock": {
        "image_reads": 0, "mask_reads": 0, "inference": 0, "visualization": 0,
        "status": "CLOSED",
    },
    "hypotheses": {
        "H1": (
            "A learned pre-execution GT-free predictor of paired refinement gain can allocate "
            "optional regional refinement more effectively than simple GT-free uncertainty/"
            "geometry proxies at equal refinement-activation budgets."
        ),
        "load_bearing": "H1",
        "H2": ("benefit-aware routing captures more positive gain per unit compute than "
               "random/entropy/margin/ROI-size routing."),
        "H3": ("post-refinement fallback reduces harmful replacement relative to always "
               "accepting an executed refinement."),
        "H4": ("a dedicated crop-trained regional refiner yields a more useful action "
               "distribution than the Phase-22 diagnostic reuse of the full-field model."),
        "H5": "benefit-aware routing produces a measurable accuracy-compute frontier.",
        "H6": ("learned paired refinement gain contains information beyond ordinary global "
               "uncertainty."),
        "status": "HYPOTHESES_NOT_RESULTS",
    },
    "comparators_ref": "reports/tables/phase24_comparator_plan.csv",
    "metrics": {
        "benefit_prediction": ["MAE", "RMSE", "Spearman", "Pearson",
                               "ROC-AUC for useful-benefit detection", "PR-AUC"],
        "routing": ["precision@budget", "benefit capture@budget",
                    "mean true DeltaDice among routed cases", "harmful activation rate",
                    "missed-benefit rate", "routing regret vs oracle"],
        "segmentation": ["macro-domain Dice", "per-domain Dice", "IoU",
                         "existing standardized boundary metrics"],
        "compute": ["activation fraction", "incremental MACs", "average total MACs",
                    "ratio vs global-only", "ratio vs always-refine"],
        "preservation": ["harmful replacement rate", "fallback rate",
                         "per-domain degradation"],
    },
    "statistics": {
        "method": "paired bootstrap",
        "n_boot": 2000,
        "seed": 42,
        "domain_stratified_for": "macro-domain metrics",
        "report": ["point estimate", "95% CI", "paired p-value where appropriate"],
        "test_used": False,
    },
    "preservation_margin": {
        "metric": "Delta = Dice(final routed system) - Dice(global reference)",
        "absolute_macro_domain_dice_margin": 0.005,
        "non_inferiority_lower_bound_must_exceed": -0.005,
        "frozen_before_phase25": True,
        "per_domain_reporting_mandatory": True,
        "warning": "macro preservation must not hide severe domain-specific harm",
    },
    "success_criteria_ref": "reports/tables/phase24_success_failure_criteria.csv",
    "failure_criteria_ref": "reports/tables/phase24_success_failure_criteria.csv",
    "ablation_plan_ref": "reports/tables/phase24_ablation_plan.csv",
    "phase25_module_plan_ref": "phase24_phase25_module_plan.json",
    "forbidden_claims": [
        "first-ever", "first in the world", "never done before",
        "counterfactual causal effect", "certified", "guaranteed",
        "novel value-of-computation", "novel gating mechanism", "novel CATE target",
        "novel multi-domain segmentation", "novel tiny-lesion segmentation",
        "mobile ready", "real-time", "resource optimal", "best method",
        "performance preserving (until the frozen non-inferiority criterion is actually met)",
    ],
    "current_allowed_wording":
        "We specify a benefit-aware refinement-routing system...",
    "level_2_wording_condition": (
        "Future Level-2 wording may be used only after empirical support and only for the exact "
        "integrated contribution identified by Phase 23."
    ),
    "no_training": True,
    "no_inference": True,
    "no_implementation": True,
    "phase25_started": False,
    "generated_utc": UTC,
}
w_json("phase24_architecture_spec.json", architecture)

# ===========================================================================
# PAIRED REFINEMENT GAIN CONTRACT (§12)
# ===========================================================================
gain = {
    "artifact": "phase24_paired_refinement_gain_contract",
    "phase": 24,
    "primary_term": "PAIRED REFINEMENT GAIN",
    "definition": "DeltaDice_i = Dice(R_i, y_i) - Dice(G_i, y_i)",
    "symbols": {
        "G_i": "frozen global output for sample i",
        "R_i": "dedicated crop-trained refiner result under the frozen regional rule",
        "y_i": "ground-truth mask (label side only)",
    },
    "nature": "supervised paired contrast (both arms fully observed during TRAIN development)",
    "must_not_be_described_as": [
        "causal treatment effect", "counterfactual effect",
        "individual treatment effect",
    ],
    "why_not_causal": (
        "Both potential outcomes are fully observed for every development image because the "
        "system may simply run the refinement during development. There is no missing arm and "
        "therefore no identification problem. The refinement is also deterministic given "
        "(x, frozen model, frozen ROI rule). See Phase-23 outcome PREFER_PAIRED_REFINEMENT_GAIN."
    ),
    "formal_analogy": (
        "Formally analogous to a CATE, but that analogy may be stated at most once, with the "
        "clarification that the estimand is a deterministic paired contrast."
    ),
    "primary_target": "continuous DeltaDice (regression)",
    "optional_development_labels": {
        "beneficial": "DeltaDice >= +0.02",
        "harmful": "DeltaDice <= -0.01",
        "neutral": "otherwise",
    },
    "label_status": (
        "PROSPECTIVE. If changed, the change must be justified BEFORE Phase 25 and must NEVER be "
        "tuned on VAL."
    ),
    "uses_GT_for_labels": True,
    "uses_GT_for_inputs": False,
    "computation_requires_refinement_to_have_run": True,
    "computation_used_as_router_input": False,
    "training_population": "original TRAIN only (never Phase-22 VAL, never TEST)",
    "generated_utc": UTC,
}
w_json("phase24_paired_refinement_gain_contract.json", gain)

# ===========================================================================
# RESOURCE UTILITY CONTRACT (§17-18)
# ===========================================================================
resource = {
    "artifact": "phase24_resource_utility_contract",
    "phase": 24,
    "utility": "U_hat_i = Delta_hat_i - lambda * C_i",
    "terms": {
        "Delta_hat_i": "predicted Dice improvement from the benefit router",
        "C_i": "explicit incremental resource cost of running the refinement",
        "lambda": "resource trade-off coefficient",
    },
    "decision_rule": {"if": "U_hat_i > tau", "then": "EXECUTE", "else": "SKIP"},
    "single_universal_lambda_forbidden": True,
    "lambda_policy": (
        "Pre-register a small SET of lambda values and the fixed-budget sweep. Do not select one "
        "arbitrary universal lambda and report it as THE result."
    ),
    "fixed_budget_evaluation": {
        "points": ["0%", "10%", "25%", "50%", "100%"],
        "0_percent": "global-only",
        "100_percent": "always-refine",
        "intermediate_thresholds": "calibrated on TRAIN development only",
    },
    "cost_proxy": {
        "primary_for_phase25": "normalized analytical incremental MACs",
        "terminology_kept_separate": [
            "ANALYTICAL MACs", "MEASURED latency", "MEASURED memory", "MEASURED energy",
        ],
        "analytical_macs_is_not_latency": True,
        "device_measurement_phase": 34,
        "note": (
            "Analytical MACs MUST NOT be described as CPU/mobile latency. Actual device "
            "measurement belongs primarily to Phase 34."
        ),
    },
    "cost_term_required_by": "Phase-23 constraint C6",
    "measured_in_phase24": False,
    "generated_utc": UTC,
}
w_json("phase24_resource_utility_contract.json", resource)

# ===========================================================================
# PRESERVATION CONTRACT (§19)
# ===========================================================================
preservation = {
    "artifact": "phase24_preservation_contract",
    "phase": 24,
    "principle": (
        "The global output must remain AVAILABLE until the final selection. No destructive "
        "replacement may occur before the final decision."
    ),
    "outcomes": {
        "SKIP": "final = global",
        "EXECUTE_THEN_REJECT": "final = global",
        "EXECUTE_THEN_ACCEPT": "final = regional-fused",
    },
    "destructive_replacement_before_final_decision": False,
    "structural_enforcement": (
        "The global probability map is retained in memory for the whole sample lifetime; the "
        "regional candidate is stored separately and only composed at the final selection step."
    ),
    "non_inferiority": {
        "metric": "Delta = Dice(final routed system) - Dice(global reference)",
        "margin": 0.005,
        "claim_only_if": "lower confidence bound of Delta > -0.005",
        "per_domain_reporting": "mandatory",
        "macro_may_not_hide_domain_harm": True,
        "frozen_before_phase25": True,
    },
    "generated_utc": UTC,
}
w_json("phase24_preservation_contract.json", preservation)

# ===========================================================================
# NOVELTY BOUNDARY (§2, §4, §32)
# ===========================================================================
novelty = {
    "artifact": "phase24_novelty_boundary",
    "phase": 24,
    "inherits_from": "phase23_novelty_verdict.json",
    "phase23_overall_label": "PARTIALLY_OCCUPIED__NARROWER_NOVELTY_POSSIBLE",
    "phase23_maximum_defensible_claim_level": 2,
    "phase23_axes": {
        "A_problem_formulation": "OCCUPIED",
        "B_learning_target": "NOT_OCCUPIED_AS_A_LEARNED_SEGMENTATION_TARGET",
        "C_decision_mechanism": "PARTIALLY_OCCUPIED",
        "D_system_integration": "NOT_OCCUPIED_AS_A_COMBINATION",
        "strongest_residual": "D",
    },
    "novelty_bearing_component": (
        "PRE-EXECUTION learned benefit gate in the integrated system: a learned, GT-free, "
        "pre-refinement predictor of the paired refinement gain, used to route an optional "
        "regional refinement, with preservation fallback and an explicit resource-cost term, "
        "inside one shared multi-domain medical segmentation system."
    ),
    "non_novel_preserved_components": [
        "post-refinement acceptance / fallback (S_omega) — closest to JFS",
        "the gate mechanism itself (metareasoning 1991; cascades 2001/2021)",
        "the paired-gain target formulation (CATE, 2019)",
        "shared multi-domain medical segmentation",
        "resource-aware inference as engineering practice",
        "tiny-structure segmentation",
    ],
    "explicit_non_claims": [
        "no novelty for the gate mechanism",
        "no novelty for the paired-gain estimand",
        "no novelty for multi-domain sharing",
        "no novelty for resource awareness",
        "no novelty for tiny-lesion segmentation",
        "no algorithmic novelty at all (Phase-23 status OCCUPIED_AT_THE_MECHANISM_LEVEL)",
    ],
    "claim_level_permitted_now": "Level 0/1 (investigate / propose). Level 2 only after "
                                 "empirical support, scoped strictly to the integrated residual.",
    "level_3_status": "NOT_SUPPORTED",
    "differentiation_ref": "reports/tables/phase24_prior_art_differentiation.csv",
    "generated_utc": UTC,
}
w_json("phase24_novelty_boundary.json", novelty)

# ===========================================================================
# BENEFIT DATA PROTOCOL (§13-16)
# ===========================================================================
data = {
    "artifact": "phase24_benefit_data_protocol",
    "phase": 24,
    "critical_leakage_constraint": (
        "Benefit-router training labels MUST NOT be generated from the existing Phase-22 VAL "
        "population. Only original TRAIN may be used."
    ),
    "original_train": {
        "manifest": "manifests/phase4_v3/train.csv",
        "n_cases": 5832,
        "manifest_version": "phase4_v3",
        "domains": {"KUB": 1978, "KVASIR": 696, "ISIC": 2556, "BUSI": 602},
        "grouping_key": "patient_id",
    },
    "split": {
        "ROUTER_HOLDOUT": {
            "fraction": 0.15,
            "approx_cases": 875,
            "status": "designated_never_inspected_for_outcomes",
        },
        "ROUTER_DEVELOPMENT": {
            "fraction": 0.85,
            "approx_cases": 4957,
            "status": "used for cross-fitted label generation and router fitting in Phase 25",
        },
        "seed": "TO_BE_FROZEN_IN_PHASE25_FROM_A_FIXED_CONSTANT",
        "deterministic": True,
        "domain_stratified": True,
        "group_safe": True,
        "grouping_key": "patient_id",
        "overlap": 0,
        "train_only": True,
        "uses_phase22_val": False,
        "uses_test": False,
    },
    "phase24_inspection_allowed": ["sample ids", "domain counts", "group integrity",
                                   "manifest sha", "split seed"],
    "phase24_inspection_forbidden": [
        "DeltaDice distribution", "Dice", "router AUC", "benefit distribution",
        "routing policy performance",
    ],
    "holdout_outcomes_read_in_phase24": 0,
    "crossfit": {
        "folds": 3,
        "within": "ROUTER_DEVELOPMENT",
        "purpose": "prevent refiner-overfit gain labels from entering the router target",
        "executed_in_phase24": False,
    },
    "existing_val_role": {
        "population": "frozen Phase-22 808-case VAL",
        "role": "SECONDARY / CONTINUITY DEVELOPMENT BENCHMARK",
        "is_router_training_data": False,
        "is_untouched_routing_holdout": False,
    },
    "generated_utc": UTC,
}
w_json("phase24_benefit_data_protocol.json", data)

# ===========================================================================
# PHASE-25 MODULE PLAN (§34)
# ===========================================================================
plan = {
    "artifact": "phase24_phase25_module_plan",
    "phase": 24,
    "status": "PRE_REGISTERED_NOT_STARTED",
    "phase25_started": False,
    "modules": [
        {"id": "25A", "name": "Dedicated crop-trained regional refiner",
         "deliverable": "R_psi trained on TRAIN crops within ROUTER_DEVELOPMENT folds",
         "starts_after": []},
        {"id": "25B", "name": "GT-free feature extraction / ROI pipeline",
         "deliverable": "frozen ROI rule + reusable global feature pooling",
         "starts_after": []},
        {"id": "25C", "name": "Out-of-fold paired-gain label generation",
         "deliverable": "concatenated OOF DeltaDice target table",
         "starts_after": ["25A", "25B"]},
        {"id": "25D", "name": "Lightweight paired-gain benefit router",
         "deliverable": "B_phi fitted on OOF labels",
         "starts_after": ["25C"]},
        {"id": "25E", "name": "Resource-aware pre-execution gate",
         "deliverable": "U_hat = Delta_hat - lambda*C, budget sweep calibration",
         "starts_after": ["25D"]},
        {"id": "25F", "name": "Post-refinement preservation selector + fusion",
         "deliverable": "S_omega + ROI-weighted fusion",
         "starts_after": ["25A"]},
        {"id": "25G", "name": "Integrated controlled development evaluation / freeze",
         "deliverable": "comparator + ablation evaluation report and freeze",
         "starts_after": ["25E", "25F"]},
    ],
    "no_module_started": True,
    "generated_utc": UTC,
}
w_json("phase24_phase25_module_plan.json", plan)

# ===========================================================================
# TABLES
# ===========================================================================
w_csv("phase24_module_spec.csv",
      ["module_id", "name", "symbol", "role", "novelty_bearing", "parameter_target",
       "gt_free_at_inference", "executed_in_phase24", "notes"],
      [
          ["GLOBAL", "Frozen Global MedFiLM reference", "G", "fallback output + reusable features",
           "no", f"{GLOBAL_PARAMS} (frozen, measured in Phase 21)", "yes", "no",
           "Phase-21 SHA bound; MUST NOT be modified in initial Phase-25 experiments"],
          ["ROI", "GT-free region proposal", "P_roi", "propose refinement region",
           "no", "0 (rule-based)", "yes", "no",
           "foreground bbox + fixed context expansion; constants from TRAIN only"],
          ["R", "Dedicated regional refiner", "R_psi", "produce optional refinement",
           "no", "0.5M-1.5M recommended, <=2.0M hard ceiling (TARGET, unmeasured)", "yes", "no",
           "crop-trained lightweight residual U-Net; NOT the frozen global model on crops"],
          ["B", "Benefit router (paired-gain predictor)", "B_phi",
           "predict paired refinement gain BEFORE refinement",
           "YES (in integration)", "<=250k params; <=2% global MACs (preferred 1%) (TARGET, unmeasured)",
           "yes", "no", "small MLP / shallow feature fusion; no transformer/encoder"],
          ["GATE", "Pre-execution resource-aware gate", "U_hat > tau",
           "EXECUTE/SKIP decision", "YES (with B)", "0", "yes", "no",
           "must not require running R_psi (C4)"],
          ["S", "Post-refinement safety selector", "S_omega",
           "preserve quality after refinement", "no (closest to JFS)", "0", "yes", "no",
           "does NOT save compute; CONTROLLED_CORE_EXTENSION"],
          ["FUSE", "Fusion rule", "F", "compose final mask", "no", "0", "yes", "no",
           "outside ROI global, inside ROI refined; no learned fusion in primary"],
      ])

# ---------------- router input contract (fail-closed) ----------------
ROUTER_COLS = ["feature", "source", "available_pre_refinement", "uses_GT",
               "inference_available", "primary_or_optional", "allowed", "reason"]

allowed_rows = [
    ["global_encoder_pooled_features", "F_global (global forward)", "true", "false", "true", "primary", "true",
     "reuses the already-computed global forward; no second pass"],
    ["global_decoder_pooled_features", "F_global (global forward)", "true", "false", "true", "primary", "true",
     "same reuse argument"],
    ["roi_pooled_global_features", "F_global pooled over the proposed ROI", "true", "false", "true", "primary", "true",
     "ROI is GT-free; pooling adds negligible cost"],
    ["probability_entropy_summaries", "p_global", "true", "false", "true", "primary", "true",
     "computed from the predicted map only"],
    ["probability_margin_summaries", "p_global", "true", "false", "true", "primary", "true",
     "predicted-map statistic"],
    ["probability_percentiles", "p_global", "true", "false", "true", "optional", "true",
     "cheap predicted-map summary"],
    ["predicted_foreground_fraction", "p_global (thresholded)", "true", "false", "true", "primary", "true",
     "from the PREDICTION, not the label"],
    ["predicted_component_count", "p_global (connected components)", "true", "false", "true", "optional", "true",
     "predicted-map topology"],
    ["predicted_largest_component_ratio", "p_global", "true", "false", "true", "optional", "true",
     "predicted-map topology"],
    ["predicted_bbox_width_height", "p_global (ROI bbox)", "true", "false", "true", "primary", "true",
     "geometry of the PREDICTED foreground"],
    ["predicted_roi_fraction", "p_global (ROI area / image area)", "true", "false", "true", "optional", "true",
     "predicted ROI size proxy"],
    ["predicted_boundary_area_statistics", "p_global", "true", "false", "true", "optional", "true",
     "prediction-only boundary statistics"],
    ["crop_magnification_factor", "ROI rule (deterministic)", "true", "false", "true", "optional", "true",
     "known before refinement by construction"],
    ["allowed_task_domain_embedding", "task_id t", "true", "false", "true", "primary", "true",
     "permitted conditioning; shared router"],
    ["device_resource_descriptor", "deployment configuration", "true", "false", "true", "optional", "true",
     "explicit resource context for the utility term (C6)"],
]

forbidden_rows = [
    ["GT_mask", "ground truth", "n/a", "true", "false", "n/a", "false", "direct label leakage"],
    ["GT_foreground_fraction", "ground truth", "n/a", "true", "false", "n/a", "false", "direct label leakage"],
    ["GT_size_label", "ground truth", "n/a", "true", "false", "n/a", "false", "direct label leakage"],
    ["Dice", "ground-truth metric", "n/a", "true", "false", "n/a", "false",
     "the target itself; unavailable at deployment"],
    ["IoU", "ground-truth metric", "n/a", "true", "false", "n/a", "false", "GT-derived"],
    ["recall", "ground-truth metric", "n/a", "true", "false", "n/a", "false", "GT-derived"],
    ["precision", "ground-truth metric", "n/a", "true", "false", "n/a", "false", "GT-derived"],
    ["specificity", "ground-truth metric", "n/a", "true", "false", "n/a", "false", "GT-derived"],
    ["MCC", "ground-truth metric", "n/a", "true", "false", "n/a", "false", "GT-derived"],
    ["GT_derived_ECE", "ground-truth calibration", "n/a", "true", "false", "n/a", "false", "GT-derived"],
    ["GT_derived_Brier", "ground-truth calibration", "n/a", "true", "false", "n/a", "false", "GT-derived"],
    ["oracle_ROI", "ground truth", "n/a", "true", "false", "n/a", "false",
     "would require the label to locate the region"],
    ["true_DeltaDice", "ground truth", "n/a", "true", "false", "n/a", "false",
     "the prediction target; using it as an input is leakage"],
    ["refined_prediction", "R_psi output", "false", "false", "false", "n/a", "false",
     "requires the refinement to have run; breaks C1/C4"],
    ["refiner_feature_maps", "R_psi internals", "false", "false", "false", "n/a", "false",
     "available only after refinement; breaks pre-execution"],
    ["post_refinement_statistics", "computed after R_psi", "false", "false", "false", "n/a", "false",
     "post-hoc quantities cannot drive a pre-execution gate"],
]

w_csv("phase24_router_input_contract.csv", ROUTER_COLS, allowed_rows + forbidden_rows)

# ---------------- data role contract ----------------
w_csv("phase24_data_role_contract.csv",
      ["population", "source", "n_cases", "role", "may_train_router",
       "may_select_lambda_or_threshold", "is_untouched_holdout", "inspected_in_phase24"],
      [
          ["TRAIN (original)", "manifests/phase4_v3/train.csv", 5832,
           "source of ROUTER_HOLDOUT + ROUTER_DEVELOPMENT", "yes (via ROUTER_DEVELOPMENT only)",
           "yes (ROUTER_DEVELOPMENT only)", "partially (ROUTER_HOLDOUT)", "counts only"],
          ["ROUTER_DEVELOPMENT", "85% of original TRAIN", "~4957",
           "cross-fitted gain labels + router fitting + threshold calibration", "yes", "yes", "no",
           "counts only"],
          ["ROUTER_HOLDOUT", "15% of original TRAIN", "~875",
           "clean out-of-sample routing evaluation", "NO", "NO",
           "YES (outcomes never inspected)", "ids/counts/groups only"],
          ["VAL (existing)", "manifests/phase4_v3/val.csv (Phase-22 frozen)", 808,
           "SECONDARY / CONTINUITY DEVELOPMENT BENCHMARK", "NO", "NO", "NO", "not used"],
          ["TEST", "manifests/phase4_v3/test.csv", 1683, "CLOSED", "NO", "NO",
           "YES", "0 reads"],
      ])

# ---------------- comparator plan ----------------
w_csv("phase24_comparator_plan.csv",
      ["comparator_id", "name", "compute_order", "uses_GT", "deployable", "role", "notes"],
      [
          ["C1", "GLOBAL_ONLY", "1x (global forward only)", "false", "yes", "lower compute anchor",
           "defines the preservation reference"],
          ["C2", "ALWAYS_REFINE", "1x + refinement always", "false", "yes", "upper compute anchor",
           "maximum action, no routing"],
          ["C3", "RANDOM_ROUTING", "budget-matched", "false", "yes", "null routing baseline",
           "seeded, budget-matched"],
          ["C4", "ENTROPY_ROUTING", "budget-matched", "false", "yes",
           "simple GT-free uncertainty proxy", "occupies the 'uncertainty' objection"],
          ["C5", "MARGIN_ROUTING", "budget-matched", "false", "yes",
           "simple GT-free margin proxy", "second simple proxy"],
          ["C6", "PREDICTED_ROI_SIZE_ROUTING", "budget-matched", "false", "yes",
           "simple GT-free geometry proxy", "tests the 'just use ROI size' objection"],
          ["C7", "LEARNED_PAIRED_GAIN_ROUTING", "budget-matched", "false", "yes",
           "primary proposed method (H1 test)", "the load-bearing comparator"],
          ["C8", "LEARNED_GAIN_PLUS_RESOURCE_COST", "budget-matched", "false", "yes",
           "adds explicit lambda*C term (C6)", "tests H5"],
          ["C9", "LEARNED_GAIN_PLUS_RESOURCE_COST_PLUS_POST_SAFETY", "budget-matched", "false", "yes",
           "adds S_omega preservation", "tests H3"],
          ["C10", "ORACLE_BENEFIT_ROUTING", "budget-matched", "true", "NO",
           "upper bound only; not deployable", "uses true DeltaDice; never a result"],
          ["C11", "JFS_LIKE_POST_HOC_SELECTOR (optional)", "full refinement compute ALWAYS PAID",
           "false", "yes", "post-hoc comparison point",
           "if included, must record FULL refinement compute because the expensive operation "
           "already occurred"],
      ])

# ---------------- ablation plan ----------------
w_csv("phase24_ablation_plan.csv",
      ["ablation_id", "name", "family", "purpose", "executed_in_phase24"],
      [
          ["A0", "global-only", "core", "compute floor / preservation reference", "no"],
          ["A1", "always-refine", "core", "compute ceiling / no-routing reference", "no"],
          ["A2", "random routing", "core", "null routing baseline", "no"],
          ["A3", "entropy routing", "core", "simple GT-free uncertainty proxy", "no"],
          ["A4", "margin routing", "core", "simple GT-free margin proxy", "no"],
          ["A5", "predicted-ROI-size routing", "core", "simple GT-free geometry proxy", "no"],
          ["A6", "learned paired-gain router", "core", "H1 test", "no"],
          ["A7", "A6 + resource cost", "core", "H5 test", "no"],
          ["A8", "A7 + post-safety", "core", "H3 test; isolates S_omega", "no"],
          ["R1", "router without deep global features", "router", "does depth matter?", "no"],
          ["R2", "router without task_id", "router", "does conditioning matter?", "no"],
          ["R3", "router with scalar-only features", "router", "minimal-feature control", "no"],
          ["F1", "refiner without p_global channel", "refiner", "is the global map useful?", "no"],
      ])

# ---------------- success / failure criteria ----------------
w_csv("phase24_success_failure_criteria.csv",
      ["id", "type", "name", "definition", "consequence_if_triggered", "frozen_before_phase25"],
      [
          ["F1", "failure", "REFINER_FAILURE",
           "dedicated refiner does not create enough positive action opportunity",
           "report as a failure; routing has nothing to route", "true"],
          ["F2", "failure", "ROUTER_FAILURE",
           "learned paired gain fails to outperform simple GT-free routing signals out of sample",
           "report H1 as unsupported", "true"],
          ["F3", "failure", "PRESERVATION_FAILURE",
           "routed system materially degrades the global reference",
           "report; non-inferiority claim NOT permitted", "true"],
          ["F4", "failure", "RESOURCE_FAILURE",
           "router/refiner cost removes the useful compute-performance trade-off",
           "report; resource-aware claim NOT permitted", "true"],
          ["F5", "failure", "DOMAIN_COLLAPSE",
           "benefit is concentrated in one domain while another is materially harmed",
           "report per-domain harm; macro average may not hide it", "true"],
          ["S1", "success", "H1_SUPPORTED",
           "learned pre-execution GT-free predictor beats simple proxies at equal budget",
           "enables scoped Level-2 wording for the integrated residual", "true"],
          ["S2", "success", "PRESERVATION_SATISFIED",
           "lower bound of Delta > -0.005 on macro-domain Dice and no domain collapse",
           "allows the phrase 'performance preserving'", "true"],
          ["S3", "success", "FRONTIER_MEASURED",
           "a measurable accuracy-compute frontier exists across budget points",
           "supports H5", "true"],
      ])

print()
print("architecture spec written:", ARCH_ID)
print("frozen method name:", METHOD)
print("router input contract: allowed =", len(allowed_rows), "forbidden =", len(forbidden_rows))
print("all allowed rows fail-closed GT-free:", all(r[3] == "false" and r[2] == "true"
                                                  and r[4] == "true" for r in allowed_rows))
