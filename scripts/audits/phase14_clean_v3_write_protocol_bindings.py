"""Phase 14 clean-v3 — Write prospective protocol bindings (§3 checkpoint, §4 gate, §5 reference procedure).

Pure governance artifact writer. No training, no inference, no TEST reads.
Emits three FROZEN JSON artifacts with the verified clean-v3 bindings.
"""
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
AUDITS = PROJECT_ROOT / "reports" / "audits"

# ---- §3 verified clean-v3 checkpoint SHA-256 (computed 2026-09-23) ----
SHA_GLOBAL = "ec7eb13f32e43af27eab7fc617bd1a2a8fcce1d6651a1b4a3653f3e4d1283269"
SHA_REGIONAL = "2e09e3a9c39c731687db1a9fef0c80881ed6235e4cda070bb4b8b382caa45daa"
SHA_LOCALIZER = "7673c34a2f2c86eca2e45c1bc6abe77842d17cd09f122f2da0f2d414ca492273"


def write(path: Path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)
    print(f"[bind] Wrote {path}")


# ============================ §3 CHECKPOINT BINDING ============================
checkpoint_binding = {
    "artifact": "phase14_clean_v3_checkpoint_binding",
    "status": "BOUND_PROSPECTIVE",
    "verification_required_before_inference": True,
    "checkpoints": {
        "GLOBAL_unetpp": {
            "path": "checkpoints/phase10_kub_unetpp_seed42_512_clean_v3/best.pt",
            "sha256": SHA_GLOBAL,
            "selection": "best.pt (phase10 clean_v3 training best)",
            "note": "GLOBAL_ONLY baseline; also the SOURCE of the GLOBAL references Tg/Dg.",
        },
        "REGIONAL_refiner_unet": {
            "path": "checkpoints/phase14_kub_refiner_unet_a3_256_seed42_clean_v3/best.pt",
            "sha256": SHA_REGIONAL,
            "epoch": 56,
            "selection": "best_val_crop_dice epoch 56 (frozen checkpoint-selection replay PASS, 13/13)",
            "note": "Regional refiner trained on clean_v3 (OPTION B amendment).",
        },
        "LOCALIZER_stage4d": {
            "path": "checkpoints/phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_clean_v3/best.pt",
            "sha256": SHA_LOCALIZER,
            "epoch": 53,
            "config": {"threshold": 0.10, "margin": 0.20, "top_k": 5, "nms_iou": 0.30},
            "note": "Frozen Stage-4D proposal generator.",
        },
    },
    "proposal_contract": {"threshold": 0.10, "margin": 0.20, "top_k": 5, "nms_iou": 0.30},
    "oracle_downstream_margin": 0.20,
    "predicted_proposal_margin": 0.20,
    "role_resolved_margins": {
        "ORACLE_DERIVED_REFINER_TRAIN_MARGIN": 0.25,
        "ORACLE_DERIVED_REFINER_VAL_MARGIN": 0.25,
        "ORACLE_DOWNSTREAM_MARGIN": 0.20,
        "PREDICTED_PROPOSAL_MARGIN": 0.20,
    },
    "governance_note": (
        "All three SHAs MUST be re-verified by the evaluator (assert sha==expected) before any "
        "inference. No alternate checkpoint, no alternate epoch, no rerun permitted."
    ),
}

# ============================ §4 GATE ALGEBRA FREEZE ============================
gate_algebra = {
    "artifact": "phase14_clean_v3_gate_algebra_freeze",
    "status": "FROZEN_UNCHANGED_SEMANTICS",
    "source_of_truth": "scripts/evaluation/evaluate_phase14_diagnostic.py (v2-era; adapted verbatim for clean_v3)",
    "gate_hierarchy": {
        "step_1_refiner_potential": {
            "condition": "G >= 0.05 AND Do >= 0.632776",
            "definition": "G = To - Tg  (Tg = clean_v3 GLOBAL Tiny Recall@90 reference)",
            "semantics_unchanged": True,
        },
        "step_2_proposal_retention": {
            "condition": "R >= 0.50  (only evaluated if G > 0; else NOT_DEFINED)",
            "definition": "R = (Tp - Tg) / G",
            "semantics_unchanged": True,
        },
        "step_3_practical_net_benefit": {
            "condition": "Tp >= 0.780822 AND Dp >= 0.632776 AND hard_tiny_recovered >= 2/15 AND global_empty_recovered >= 1/5",
            "note": (
                "Denominators 15 and 5 are the clean_v3 EXECUTABLE special-set sizes "
                "(population-dependent). v2-era denominators were 16/7 (provenance-only)."
            ),
            "semantics_unchanged_except_population_denominators": True,
        },
    },
    "population_dependent_items_remeasured": [
        "Tg (clean_v3 GLOBAL Tiny Recall@90)",
        "Dg (clean_v3 GLOBAL mean Dice)",
        "hard_tiny_denominator (15)",
        "global_empty_denominator (5)",
    ],
    "population_independent_items_frozen": [
        "step1_delta_threshold = 0.05",
        "step1_dice_floor = 0.632776",
        "step2_retention = 0.50",
        "step3_tiny_floor = 0.780822",
        "step3_dice_floor = 0.632776",
        "metric_definitions",
        "fusion_semantics (MAX, threshold 0.50 strictly after fusion)",
    ],
    "governance_note": (
        "Gate algebra preserved bit-for-bit except population-dependent denominators. No redefinition "
        "of thresholds, metric definitions, or fusion semantics."
    ),
}

# ============================ §5 REFERENCE PROCEDURE FREEZE ============================
reference_procedure = {
    "artifact": "phase14_clean_v3_reference_procedure_freeze",
    "status": "FROZEN_PROSPECTIVE_PROCEDURE",
    "derive": {
        "Tg_clean_v3": "GLOBAL_ONLY mode Tiny Recall@90 on the 103-image FULL_FIELD clean_v3 VAL population",
        "Dg_clean_v3": "GLOBAL_ONLY mode mean Dice on the same 103-image FULL_FIELD clean_v3 VAL population",
    },
    "procedure": {
        "checkpoint": "checkpoints/phase10_kub_unetpp_seed42_512_clean_v3/best.pt (sha " + SHA_GLOBAL[:12] + "...)",
        "population": "103 FULL_FIELD KUB VAL images (phase4_v3); exact table reports/tables/kub_val_samples_sized_clean_v3.csv",
        "preprocessing": "identical to v2-era: resize to 512, sigmoid, threshold 0.50, restore to native coordinates",
        "metric_definitions": "dice_binary + object_metrics recall@90 (>=90% component-pixel coverage; >=1px overlap for detection); identical to v2",
        "component_matching": "8-connected GT components via extract_gt_components; identical to v2",
        "size_strata": "TINY/SMALL/MEDIUM/LARGE from reports/tables/kub_val_components_sized_clean_v3.csv",
        "aggregation": "mean over population (Tiny Recall@90 = mean of per-TINY-component recall90_success)",
        "NOT_used": "val_macro_dice = 0.7641601653354622 (all-view-types macro; NOT the FULL_FIELD mean-dice reference)",
    },
    "forbidden_before_freeze": "Inspecting Oracle/Predicted diagnostic results prior to deriving and freezing Tg/Dg",
    "generation_rule": (
        "Generate ONCE; write reports/audits/phase14_clean_v3_global_reference_freeze.json; "
        "thereafter FROZEN with no favorability-driven reruns."
    ),
    "governance_note": (
        "Procedure frozen prospectively. The numeric Tg/Dg are written by the reference-generation "
        "run (§6), NOT hardcoded here. The full-precision values and forward count are recorded then."
    ),
}

write(AUDITS / "phase14_clean_v3_checkpoint_binding.json", checkpoint_binding)
write(AUDITS / "phase14_clean_v3_gate_algebra_freeze.json", gate_algebra)
write(AUDITS / "phase14_clean_v3_reference_procedure_freeze.json", reference_procedure)
print("[bind] §3/§4/§5 protocol bindings written.")
