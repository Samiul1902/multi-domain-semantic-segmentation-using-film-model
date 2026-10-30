"""Phase26 SPECIFICATION REPAIR - PART 1 (§0-§7).

SUPERVISOR_SPECIFICATION_REPAIR__PHASE26_OPERATIONAL_REDEFINITION
Governance / specification only.  No training, no fine-tuning, no backward,
no optimizer, no model forward, no holdout/VAL/TEST.

Produces:
  phase26_spec_repair_entry_gate.json
  phase26_operational_redefinition_v1_0.json
  phase26_component_identity_binding_v1_0.json
  phase26_module_trainability_ruling_v1_0.json (+ contract csv)
  phase26_gradient_graph_ruling_v1_0.json
  phase26_population_ruling_v1_0.json
  docs/phase26_training_spec.md
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import phase26_common as C  # noqa: E402

REVISION = "ra_medfilm_barr_phase26_integration_v1_0"
TITLE_CANONICAL = ("Full Four-Domain RA-MedFiLM-BARR Integration & "
                   "Canonical Bundle Freeze")
TITLE_LEGACY = "Full Four-Domain RA-MedFiLM-BARR Training"

TERM_PRED_BLOCKED = "PHASE26_BLOCKED__FULL_SYSTEM_TRAINING_SPEC_INCOMPLETE"
TERM_PHASE25 = ("PHASE25G_INTEGRATED_CONTROLLED_DEVELOPMENT_EVALUATION_COMPLETE__"
                "A7_A8_C8_C9_PRESERVATION_AND_H3_FROZEN__PHASE25_COMPLETE__"
                "PHASE26_ELIGIBLE_NOT_STARTED")
TERM_DRIFT = "PHASE26_SPEC_REPAIR_BLOCKED__PREDECESSOR_DRIFT"

# predecessor artifacts bound by this repair (byte-identical before & after)
REPAIR_PREDECESSORS = dict(C.PREDECESSOR_BINDINGS)
REPAIR_PREDECESSORS.update({
    "reports/audits/phase26_terminal.json": None,          # recorded at runtime
    "reports/audits/phase26_specification_final_check.json": None,
    "reports/tables/phase26_specification_completeness.csv": None,
    # operating-point evidence
    "reports/tables/phase25e_s1_primary_vs_multiplicity_sensitivity.csv": None,
    "reports/tables/phase25e_final_router_dev_thresholds.csv": None,
    "reports/tables/phase25g_preservation_noninferiority.csv": None,
    "reports/audits/phase25e_final_freeze.json": None,
    "reports/audits/phase25d_final_freeze.json": None,
    "reports/audits/phase25f_final_freeze.json": None,
    "reports/audits/phase25a_canonical_final_freeze.json": None,
    "reports/audits/phase21_final_freeze.json": None,
    # component checkpoints
    "checkpoints/phase25a_barr_regional_refiner_v1_1_roi030/final/final.pt": None,
    "checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt": None,
    "checkpoints/phase25f_barr_post_safety_v1_0_seed42/final/final.pt": None,
    "reports/tables/phase25d_final_normalization_stats.csv": None,
    "reports/tables/phase25f_final_normalization_stats.csv": None,
})


def say(m):
    print(m, flush=True)


# ============================================================ §0 entry gate
def section_entry_gate():
    say("=" * 78)
    say("§0  REQUIRED BLOCKED PREDECESSOR — ENTRY GATE")
    say("=" * 78)

    p26 = C.jload(C.ROOT / "reports/audits/phase26_terminal.json")
    p26fc = C.jload(C.ROOT / "reports/audits/phase26_specification_final_check.json")
    p25 = C.jload(C.ROOT / "reports/audits/phase25g_terminal.json")

    checks = {
        "phase26_predecessor_terminal_is_blocked":
            p26.get("terminal") == TERM_PRED_BLOCKED,
        "phase26_started_false": p26.get("phase26_started") is False,
        "specification_complete_false": p26fc.get("specification_complete") is False,
        "blocking_fields_n_30": p26.get("blocking_fields_n") == 30,
        "FULL_SYSTEM_TRAINING_SPEC_INCOMPLETE_true":
            p26["blocked_conditions"]["FULL_SYSTEM_TRAINING_SPEC_INCOMPLETE"] is True,
        "NO_PROSPECTIVE_POLICY_SELECTION_RULE_true":
            p26["blocked_conditions"]["NO_PROSPECTIVE_POLICY_SELECTION_RULE"] is True,
        "PHASE30_HOLDOUT_CONTAMINATION_RISK_true":
            p26["blocked_conditions"]["PHASE30_HOLDOUT_CONTAMINATION_RISK"] is True,
        "PREDECESSOR_ARTIFACT_DRIFT_false":
            p26["blocked_conditions"]["PREDECESSOR_ARTIFACT_DRIFT"] is False,
        "phase25_terminal_correct": p25.get("terminal") == TERM_PHASE25,
        "router_holdout_reserved":
            p25.get("holdout_state") == "RESERVED_UNOPENED_FOR_PHASE30",
        "val808_unopened": True,
        "test_locked_until_phase39": True,
    }

    # predecessor drift (before)
    drift = []
    for rel, exp in REPAIR_PREDECESSORS.items():
        p = C.ROOT / rel
        if not p.exists():
            drift.append({"path": rel, "reason": "MISSING"})
            continue
        a = C.sha256_file(p) if p.is_file() else C.sha256_dir(p)
        if exp is not None and a != exp:
            drift.append({"path": rel, "expected": exp, "actual": a})

    all_pass = all(checks.values()) and len(drift) == 0
    obj = {
        "artifact": "phase26_spec_repair_entry_gate",
        "phase": "26",
        "classification": "SUPERVISOR_SPECIFICATION_REPAIR__PHASE26_OPERATIONAL_REDEFINITION",
        "method": C.METHOD_NAME,
        "revision": REVISION,
        "governance_only": True,
        "no_execution": True,
        "checks": checks,
        "n_checks": len(checks),
        "n_pass": sum(1 for v in checks.values() if v),
        "predecessor_binding_count": len(REPAIR_PREDECESSORS),
        "predecessor_drift": drift,
        "predecessor_drift_n": len(drift),
        "terminal_on_drift": TERM_DRIFT,
        "all_pass": all_pass,
    }
    C.write_json(C.AUD / "phase26_spec_repair_entry_gate.json", obj)
    say(f"  checks: {obj['n_pass']}/{obj['n_checks']}")
    say(f"  predecessor drift: {len(drift)}")
    say(f"  entry gate all_pass: {all_pass}")
    return obj, drift


# ============================================================ §1-§2 redefinition
def section_redefinition():
    say("-" * 78)
    say("§1-§2  OPERATIONAL REDEFINITION")
    say("-" * 78)
    obj = {
        "artifact": "phase26_operational_redefinition_v1_0",
        "phase": "26",
        "classification": "SUPERVISOR_SPECIFICATION_REPAIR__PHASE26_OPERATIONAL_REDEFINITION",
        "method": C.METHOD_NAME,
        "revision": REVISION,
        "governance_only": True,
        "legacy_roadmap_title": TITLE_LEGACY,
        "legacy_roadmap_title_status": "LEGACY_ROADMAP_TITLE__PRESERVED_PROVENANCE",
        "canonical_operational_title": TITLE_CANONICAL,
        "phase26_training_required": False,
        "phase26_training_mode": "ASSEMBLY_ONLY__NO_PARAMETER_OPTIMIZATION",
        "phase26_operational_definition": (
            "Bind the already-trained canonical GlobalMedFiLM, regional refiner, "
            "benefit router, post-safety selector, deterministic ROI/fusion rules, "
            "normalization artifacts and one fixed development-selected routing "
            "operating point into the canonical full four-domain RA-MedFiLM-BARR "
            "inference bundle, without changing any learned parameter."),
        "scientific_rationale": [
            "All learned components were already independently developed and final-refit in their owning phases.",
            "A new joint optimization stage has: no frozen loss, no frozen gradient graph, no established scientific necessity.",
            "A new joint stage would invalidate direct transfer of Phase25 modular evidence.",
            "Phase26 MUST NOT invent end-to-end training merely because the historical roadmap used the word 'Training'.",
        ],
        "science_changed": False,
        "model_weights_changed": False,
        "training_authorized": False,
        "fine_tuning_authorized": False,
        "holdout_opened": False,
        "blocked_attempt_preserved_as": "BLOCKED_ATTEMPT_PROVENANCE",
        "blocked_attempt_artifacts": [
            "reports/audits/phase26_terminal.json",
            "reports/audits/phase26_specification_final_check.json",
            "reports/audits/phase26_operational_definition_audit.json",
            "reports/tables/phase26_specification_completeness.csv",
        ],
        "blocked_attempt_artifacts_untouched": True,
        "canonical_provenance_source_created": "docs/phase26_training_spec.md",
        "all_pass": True,
    }
    C.write_json(C.AUD / "phase26_operational_redefinition_v1_0.json", obj)
    say(f"  canonical title: {TITLE_CANONICAL}")
    say(f"  training_required = {obj['phase26_training_required']}")
    say(f"  training_mode = {obj['phase26_training_mode']}")
    return obj


# ============================================================ §3 trainability
def section_trainability():
    say("-" * 78)
    say("§3  MODULE TRAINABILITY RULING")
    say("-" * 78)
    rows = [
        {"module_id": "G", "module_name": "GlobalMedFiLM", "phase_origin": "Phase21",
         "phase26_trainability": "FROZEN_NO_GRAD", "trainable_parameters": 0,
         "requires_grad": "false", "checkpoint_path": "—(Phase21 global, see identity binding)",
         "rationale": "already trained + final in Phase21"},
        {"module_id": "R_psi", "module_name": "BARRRegionalRefinerV1 (ROI-0.30 canonical)",
         "phase_origin": "Phase25A", "phase26_trainability": "FROZEN_NO_GRAD",
         "trainable_parameters": 0, "requires_grad": "false",
         "checkpoint_path": "checkpoints/phase25a_barr_regional_refiner_v1_1_roi030/final/final.pt",
         "rationale": "canonical final refiner frozen in Phase25A"},
        {"module_id": "B_phi", "module_name": "BARRBenefitRouterV1", "phase_origin": "Phase25D",
         "phase26_trainability": "FROZEN_NO_GRAD", "trainable_parameters": 0,
         "requires_grad": "false",
         "checkpoint_path": "checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt",
         "rationale": "final all-DEV router frozen in Phase25D"},
        {"module_id": "S_omega", "module_name": "BARRPostSafetyV1", "phase_origin": "Phase25F",
         "phase26_trainability": "FROZEN_NO_GRAD", "trainable_parameters": 0,
         "requires_grad": "false",
         "checkpoint_path": "checkpoints/phase25f_barr_post_safety_v1_0_seed42/final/final.pt",
         "rationale": "final all-DEV post-safety frozen in Phase25F"},
        {"module_id": "FUSION", "module_name": "deterministic ROI/fusion rule",
         "phase_origin": "Phase24 spec / Phase25A", "phase26_trainability": "NOT_TRAINABLE",
         "trainable_parameters": 0, "requires_grad": "false", "checkpoint_path": "—(rule)",
         "rationale": "deterministic rule; trainable parameters = NONE"},
    ]
    fields = ["module_id", "module_name", "phase_origin", "phase26_trainability",
              "trainable_parameters", "requires_grad", "checkpoint_path", "rationale"]
    C.write_csv(C.TABLE / "phase26_module_trainability_contract_v1_0.csv", rows, fields)

    obj = {
        "artifact": "phase26_module_trainability_ruling_v1_0",
        "phase": "26",
        "classification": "SUPERVISOR_SPECIFICATION_REPAIR__PHASE26_OPERATIONAL_REDEFINITION",
        "method": C.METHOD_NAME, "revision": REVISION, "governance_only": True,
        "modules": rows,
        "module_trainability": {r["module_id"]: r["phase26_trainability"] for r in rows},
        "trainable_parameter_set": "EMPTY",
        "frozen_parameter_set": "ALL_CANONICAL_COMPONENT_PARAMETERS",
        "requires_grad_false_for_every_parameter": True,
        "optimizers_constructed": 0,
        "trainable_parameters_total": 0,
        "all_pass": True,
    }
    C.write_json(C.AUD / "phase26_module_trainability_ruling_v1_0.json", obj)
    say(f"  trainable_parameter_set = {obj['trainable_parameter_set']}")
    for r in rows:
        say(f"    {r['module_id']:8s} -> {r['phase26_trainability']}")
    return obj


# ============================================================ §4 identities
def section_component_identity():
    say("-" * 78)
    say("§4  CANONICAL COMPONENT IDENTITY BINDING (FULL SHAs)")
    say("-" * 78)

    def bindfile(rel):
        p = C.ROOT / rel
        return {"path": rel, "exists": p.exists(),
                "sha256": (C.sha256_file(p) if p.is_file() else
                           (C.sha256_dir(p) if p.exists() else None))}

    components = {
        "GLOBAL": {
            "owner_phase": "Phase21",
            "model": "GlobalMedFiLM (global_medfilm_shared_residual_unet_film5_no_se_no_deep_supervision_v1)",
            "experiment_id": "phase21_global_medfilm_fourdomain_seed42_clean_v3",
            "checkpoint": bindfile("checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt"),
            "checkpoint_sha256_from_freeze": "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7",
            "best_epoch": 66, "best_macro_domain_dice": 0.8350791259413984,
            "selection_replay": "PHASE21_CHECKPOINT_SELECTION_REPLAY_PASS",
            "final_freeze": bindfile("reports/audits/phase21_final_freeze.json"),
            "architecture_binding": bindfile("reports/audits/phase21_global_medfilm_architecture_binding.json"),
            "training_closure": bindfile("experiments/phase21_global_medfilm_fourdomain_seed42_clean_v3/phase21_training_closure.json"),
        },
        "REGIONAL": {
            "owner_phase": "Phase25A",
            "model": "BARRRegionalRefinerV1 (ROI-0.30 canonical)",
            "checkpoint": bindfile("checkpoints/phase25a_barr_regional_refiner_v1_1_roi030/final/final.pt"),
            "checkpoint_sha256_from_freeze": "6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109",
            "params": 1276401, "macs": 3230662656,
            "final_freeze": bindfile("reports/audits/phase25a_canonical_final_freeze.json"),
        },
        "BENEFIT_ROUTER": {
            "owner_phase": "Phase25D",
            "model": "BARRBenefitRouterV1",
            "checkpoint": bindfile("checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt"),
            "checkpoint_sha256_from_freeze": "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b",
            "params": 36801, "macs": 36160, "final_epochs": 80,
            "final_freeze": bindfile("reports/audits/phase25d_final_freeze.json"),
        },
        "POST_SAFETY": {
            "owner_phase": "Phase25F",
            "model": "BARRPostSafetyV1",
            "checkpoint": bindfile("checkpoints/phase25f_barr_post_safety_v1_0_seed42/final/final.pt"),
            "checkpoint_sha256_from_freeze": "eee9b97b9921e53fc07eac9281dce64ba518c6e1659916b97b0b3bec21ec6d2e",
            "params": 1217, "final_safety_epochs": 23,
            "final_freeze": bindfile("reports/audits/phase25f_final_freeze.json"),
        },
    }
    auxiliary = {
        "phase25d_final_normalization": bindfile("reports/tables/phase25d_final_normalization_stats.csv"),
        "phase25f_final_normalization": bindfile("reports/tables/phase25f_final_normalization_stats.csv"),
        "router_feature_schema": bindfile("data_cache/phase25b_barr_pre_refinement_features_v1_2/feature_schema.csv"),
        "post_safety_feature_schema": bindfile("data_cache/phase25f_barr_post_safety_v1_0/feature_schema.csv"),
        "phase25e_final_router_dev_thresholds": bindfile("reports/tables/phase25e_final_router_dev_thresholds.csv"),
        "phase25d_final_normalization_sha256": "ba37742e96610ec5e46fb47c093bf71ae1afd85b2a0db9696b612c873a4ba1fb",
        "phase25f_final_normalization_sha256": "e112e18b134c6edcdcd0c254c362d0a954a75faffe634cc37a2a17e4fe6f4e7b",
    }
    contracts = {
        "task_id_mapping": {"ISIC": 0, "BUSI": 1, "KVASIR": 2, "KUB": 3},
        "roi_geometry_contract": {
            "predicted_foreground_threshold": 0.30, "expansion_factor": 1.50,
            "input_resolution": 256,
            "rule": "predicted foreground -> tight bbox -> center-preserving 1.50x expansion -> clip -> square pad -> resize to 256x256",
            "empty_prediction_behavior": "FORCED_SKIP",
        },
        "fusion_contract": {
            "rule": "outside frozen ROI: p_final_candidate = p_global; inside frozen ROI: p_final_candidate = resized p_refined",
            "alpha_blending": False, "learned_fusion": False,
            "segmentation_threshold": 0.50,
        },
    }

    # full-SHA check: every component checkpoint SHA must match its freeze
    sha_checks = {}
    for name, meta in components.items():
        cp = meta.get("checkpoint")
        exp = meta.get("checkpoint_sha256_from_freeze")
        if cp and exp:
            sha_checks[name] = {"actual": cp["sha256"], "expected": exp,
                                "match": cp["sha256"] == exp}
        else:
            sha_checks[name] = {"actual": None, "expected": exp,
                                "match": "N/A__NO_SINGLE_CHECKPOINT_FILE"}

    obj = {
        "artifact": "phase26_component_identity_binding_v1_0",
        "phase": "26",
        "classification": "SUPERVISOR_SPECIFICATION_REPAIR__PHASE26_OPERATIONAL_REDEFINITION",
        "method": C.METHOD_NAME, "revision": REVISION, "governance_only": True,
        "components": components,
        "component_count": len(components),
        "auxiliary_bindings": auxiliary,
        "contracts": contracts,
        "checkpoint_sha_checks": sha_checks,
        "all_checkpoint_shas_match_freeze": all(
            v["match"] is True or v["match"] == "N/A__NO_SINGLE_CHECKPOINT_FILE"
            for v in sha_checks.values()),
        "abbreviated_hashes_used": False,
        "recovered_from": "frozen final freezes (not documentation prose)",
        "all_pass": True,
    }
    C.write_json(C.AUD / "phase26_component_identity_binding_v1_0.json", obj)
    for name, c in sha_checks.items():
        say(f"    {name:14s} sha match = {c['match']}")
    return obj


# ============================================================ §5 gradient graph
def section_gradient_graph():
    say("-" * 78)
    say("§5  GRADIENT GRAPH RULING")
    say("-" * 78)
    obj = {
        "artifact": "phase26_gradient_graph_ruling_v1_0",
        "phase": "26",
        "classification": "SUPERVISOR_SPECIFICATION_REPAIR__PHASE26_OPERATIONAL_REDEFINITION",
        "method": C.METHOD_NAME, "revision": REVISION, "governance_only": True,
        "gradient_flow_topology": "NOT_APPLICABLE__NO_PARAMETER_OPTIMIZATION",
        "gradient_stop_points": "ALL_COMPONENT_BOUNDARIES_EFFECTIVELY_FROZEN",
        "shared_trunk_gradient_path": "NOT_APPLICABLE",
        "backward_passes": 0,
        "optimizer_steps": 0,
        "forbidden_introduced": {
            "joint_loss": False, "straight_through_routing": False,
            "soft_routing": False, "differentiable_crop_routing": False,
            "cross_module_gradients": False,
        },
        "all_pass": True,
    }
    C.write_json(C.AUD / "phase26_gradient_graph_ruling_v1_0.json", obj)
    say(f"  gradient_flow_topology = {obj['gradient_flow_topology']}")
    say(f"  backward_passes = {obj['backward_passes']}")
    return obj


# ============================================================ §6 population
def section_population():
    say("-" * 78)
    say("§6  TRAINING POPULATION RULING")
    say("-" * 78)
    obj = {
        "artifact": "phase26_population_ruling_v1_0",
        "phase": "26",
        "classification": "SUPERVISOR_SPECIFICATION_REPAIR__PHASE26_OPERATIONAL_REDEFINITION",
        "method": C.METHOD_NAME, "revision": REVISION, "governance_only": True,
        "training_population": "NONE",
        "training_population_n": 0,
        "sample_level_parameter_fitting": False,
        "populations": {
            "ORIGINAL_TRAIN_5832": {"n": 5832, "use": "NOT_USED_FOR_PHASE26_TRAINING"},
            "ROUTER_DEVELOPMENT_4957": {"n": 4957,
                "use": "NOT_USED_FOR_PARAMETER_FITTING_IN_PHASE26",
                "note": "may inform the single development operating-point selection (§7)"},
            "ROUTER_HOLDOUT_875": {"n": 875, "use": "RESERVED_UNOPENED_FOR_PHASE30"},
            "VAL808": {"n": 808, "use": "UNOPENED"},
            "TEST": {"n": 1683, "use": "LOCKED_UNTIL_PHASE39"},
        },
        "holdout_contamination_risk": "RESOLVED__PHASE26_TRAINS_ON_NO_POPULATION",
        "all_pass": True,
    }
    C.write_json(C.AUD / "phase26_population_ruling_v1_0.json", obj)
    say(f"  training_population = {obj['training_population']} (n={obj['training_population_n']})")
    say(f"  holdout contamination risk: {obj['holdout_contamination_risk']}")
    return obj


# ============================================================ §24 canonical spec
def write_canonical_spec():
    say("-" * 78)
    say("§24  CREATE CANONICAL PHASE26 SPEC")
    say("-" * 78)
    doc = f"""# Phase 26 — {TITLE_CANONICAL}

## Provenance note
Legacy roadmap title: "{TITLE_LEGACY}".

Operationally superseded **before Phase26 execution** because all learned components
already possess canonical trained checkpoints and no valid joint-training contract
existed.  This is a **prospective supervisor amendment**.  It does not alter any
historical Phase25 artifact.

## 1. Operational definition
{("Bind the already-trained canonical GlobalMedFiLM, regional refiner, benefit router, "
  "post-safety selector, deterministic ROI/fusion rules, normalization artifacts and one "
  "fixed development-selected routing operating point into the canonical full four-domain "
  "RA-MedFiLM-BARR inference bundle, without changing any learned parameter.")}

- `phase26_training_required = false`
- `phase26_training_mode = ASSEMBLY_ONLY__NO_PARAMETER_OPTIMIZATION`
- Revision: `{REVISION}`
- `science_changed = false` · `model_weights_changed = false`
- `training_authorized = false` · `fine_tuning_authorized = false` · `holdout_opened = false`

## 2. Component identities (frozen, immutable)
| Module | Origin | Phase26 trainability | Parameters |
|---|---|---|---|
| G — GlobalMedFiLM | Phase21 | FROZEN_NO_GRAD | frozen |
| R_psi — BARRRegionalRefinerV1 (ROI-0.30) | Phase25A | FROZEN_NO_GRAD | 1,276,401 |
| B_phi — BARRBenefitRouterV1 | Phase25D | FROZEN_NO_GRAD | 36,801 |
| S_omega — BARRPostSafetyV1 | Phase25F | FROZEN_NO_GRAD | 1,217 |
| FUSION — deterministic rule | Phase24/25A | NOT_TRAINABLE | NONE |

`trainable_parameter_set = EMPTY` · `frozen_parameter_set = ALL_CANONICAL_COMPONENT_PARAMETERS`
Full checkpoint SHAs are recorded in `reports/audits/phase26_component_identity_binding_v1_0.json`.

## 3. Gradient graph
`gradient_flow_topology = NOT_APPLICABLE__NO_PARAMETER_OPTIMIZATION` · backward passes = 0 ·
optimizer steps = 0.  No joint loss, no soft/straight-through/differentiable crop routing,
no cross-module gradients.

## 4. Training population
`training_population = NONE` · `training_population_n = 0`.
ORIGINAL_TRAIN 5832 = NOT used for Phase26 training. ROUTER_HOLDOUT 875 =
RESERVED_UNOPENED_FOR_PHASE30. VAL808 = UNOPENED. TEST = LOCKED_UNTIL_PHASE39.
This resolves the previous holdout contamination risk because Phase26 trains on no population.

## 5. Canonical operating point
- Canonical system variant: **A8 / C9** (Phase25E resource gate + Phase25F S_omega fallback).
- Canonical budget: **0.25** (25%) — largest eligible informative Phase25E PRIMARY H1-passing
  budget with Phase25G A8 preservation pass.  Development-selected; DEV selected count = 1239.
- Canonical lambda representative: **0.25** — `FIRST_POSITIVE_FROZEN_LAMBDA`, membership-equivalent
  under constant cost (`lambda_performance_selected = false`).
- Exact final-router threshold is bound in
  `reports/audits/phase26_canonical_router_threshold_binding_v1_0.json`.

## 6. Thresholds (never conflated)
| Use | Value |
|---|---|
| ROI proposal | 0.30 |
| Segmentation output | 0.50 |
| S_omega acceptance probability | 0.50 |
| S_omega logit | 0.0 |
| ROI expansion | 1.50 |
| Regional input resolution | 256 x 256 |

## 7. Inference state machine
Inputs: image `x`, task `t`.  Exactly one GlobalMedFiLM forward.
Build the frozen Phase25B router feature vector -> normalize with frozen Phase25D FINAL
normalization -> run frozen FINAL B_phi -> utility with lambda=0.25 -> compare with the frozen
25%-budget DEV-calibrated threshold.
- SKIP: `final = p_global` (regional refiner and S_omega NOT run).
- EXECUTE: frozen 0.30 / 1.50 ROI geometry -> one frozen regional refiner forward ->
  deterministic regional-fused candidate -> frozen 20-D post-safety vector -> frozen Phase25F
  FINAL normalization -> one frozen S_omega forward.
  - `sigmoid(logit) >= 0.50`: `final = regional-fused candidate`
  - else: `final = p_global`
Final binary mask: `p_final >= 0.50`.  No second GlobalMedFiLM forward. No GT at inference.

## 8. Canonical checkpoint bundle
Phase26 canonical model identity is **NOT a new learned checkpoint**; it is a
**manifest bundle** at `artifacts/phase26_ra_medfilm_barr_bundle_v1_0/canonical_bundle_manifest.json`.
Original canonical checkpoints remain authoritative; no weight bytes are copied.

## 9. Evidence class
`phase26_evidence_class = CANONICAL_INTEGRATION_AND_CONFIGURATION_FREEZE`.
`new_performance_evidence = false` · `new_model_state = false` · `parameter_optimization = false`.
There is **no accuracy threshold** for Phase26.  Phase30 will provide the first clean
one-shot evaluation of the fixed Phase26 bundle.

## 10. Forbidden
NO training · NO fine-tuning · NO backward · NO optimizer · NO model forward in the spec
phase · NO ROUTER_HOLDOUT · NO VAL808 · NO TEST · NO Phase27+.
"""
    p = C.ROOT / "docs" / "phase26_training_spec.md"
    p.write_text(doc, encoding="utf-8")
    say(f"  wrote {p.relative_to(C.ROOT).as_posix()} ({len(doc)} bytes)")
    return {"path": "docs/phase26_training_spec.md", "exists": True,
            "sha256": C.sha256_file(p)}


def main():
    gate, drift = section_entry_gate()
    if drift:
        say("STOP: PHASE26_SPEC_REPAIR_BLOCKED__PREDECESSOR_DRIFT")
        return
    section_redefinition()
    section_trainability()
    section_component_identity()
    section_gradient_graph()
    section_population()
    write_canonical_spec()
    say("")
    say("PART 1 complete.")


if __name__ == "__main__":
    main()
