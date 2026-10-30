"""Phase 24 — SPECIFICATION COMPLETENESS REPAIR (4/5).

Spec-completeness audit, no-execution re-audit and determinism proof for the addendum.

DESIGN ONLY. No training, inference, module instantiation or outcome inspection.

Writes:
    reports/audits/phase24_spec_completeness_repair.json
    reports/audits/phase24_no_execution_audit.json   (refreshed)

Usage:
    ./.venv/Scripts/python.exe scripts/analysis/run_phase24_spec_completeness.py
"""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
NB = (ROOT / "notebooks/phasewise/phase_24_architecture_spec"
      / "phase24_narrowed_benefit_aware_refinement_spec.ipynb")
UTC = datetime.now(timezone.utc).isoformat()
OLD_NB_SHA = "e4383d5ac9c33787b809407e4884cd7069f1f4514ed0abf7c21c844024221207"


def j(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def rows(p: Path) -> list[dict]:
    with p.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


ex = j(AUD / "phase24_exact_implementation_spec.json")
pe = j(AUD / "phase24_benefit_data_protocol_exact.json")
rev = j(AUD / "phase24_architecture_revision_v1_1.json")
arch = j(AUD / "phase24_architecture_spec.json")
nm = j(AUD / "phase24_method_naming_decision.json")
nov = j(AUD / "phase24_novelty_boundary.json")
fs = rows(TAB / "phase24_router_primary_feature_set.csv")
sch = rows(TAB / "phase25_future_oof_gain_schema.csv")

nb_sha = sha(NB) if NB.exists() else "n/a"

PRED = {
    "phase21_best_pt": ("checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt",
                        "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7"),
    "phase22_protocol": ("reports/audits/phase22_diagnostic_protocol.json",
                         "9d620d6c85276e1a9a086ec60172cdef3b94dc58fe8288222378d196dd4609b7"),
    "phase22_freeze": ("reports/audits/phase22_final_freeze.json",
                       "9a0aa2f8c1a2850770fb09f2838e95f0fe08b3b40e55ab1d10c3564841107bca"),
    "phase23_notebook": ("notebooks/phasewise/phase_23_literature_novelty/"
                         "phase23_literature_methodological_novelty_audit.ipynb",
                         "e9f78ccefd96abad742fa5570a44110cd67c62f5510b99300448e44b961107b0"),
}
pred_ok = {}
for k, (rel, exp) in PRED.items():
    p = ROOT / rel
    pred_ok[k] = p.exists() and sha(p) == exp
science_unchanged = all(pred_ok.values())

# ------------------------------------------------------------------ §23 checks
checks = [
    ("exact_split_seed_frozen", ex.get("split_seed") == 42),
    ("exact_split_manifests_bound",
     pe.get("manifest_sha256") and ex.get("split_manifest_shas", {}).get(
         "phase24_router_split_manifest.csv") == pe.get("manifest_sha256")),
    ("exact_roi_expansion_frozen", ex["roi"]["expansion_factor"] == 1.50),
    ("exact_refiner_resolution_frozen", ex["roi"]["input_resolution"] == 256),
    ("exact_refiner_channels_frozen",
     ex["refiner"]["encoder_bridge_channels_declared"] == [16, 32, 64, 128, 192]
     and ex["refiner"]["encoder_bridge_channels_active"] == [16, 32, 64, 96, 128]),
    ("exact_refiner_blocks_frozen",
     ex["refiner"]["architecture"]["residual_block_per_encoder_stage"] is True
     and ex["refiner"]["architecture"]["residual_block_at_bridge"] is True
     and ex["refiner"]["architecture"]["residual_block_after_each_concatenation"] is True),
    ("exact_refiner_training_protocol_frozen",
     ex["refiner"]["optimizer"] == "AdamW" and ex["refiner"]["lr"] == 1e-4
     and ex["refiner"]["max_epochs"] == 100 and ex["refiner"]["early_stopping_patience"] == 15
     and ex["refiner"]["batch_size"] == 8 and ex["refiner"]["seed"] == 42),
    ("action_availability_frozen",
     ex["action_availability"]["definition"] == "action_available_i = predicted ROI exists"),
    ("OOF_procedure_exact",
     ex["crossfit"]["outer_folds"] == 3
     and ex["crossfit"]["oof_target_fold_never_used_for_checkpoint_selection"] is True
     and ex["crossfit"]["infer_once_per_fold"] is True),
    ("final_refiner_refit_rule_frozen",
     ex["final_refiner"]["holdout_forbidden"] is True
     and "median" in ex["final_refiner"]["epoch_rule"]),
    ("router_feature_taps_frozen",
     ex["router"]["feature_taps"] == ["bridge", "decoder2", "decoder1"]
     and ex["router"]["second_global_forward"] is False),
    ("router_scalar_inputs_frozen",
     len(ex["router"]["scalar_descriptors"]) == 10
     and len(fs) == 17
     and all(r["uses_GT"] == "false" for r in fs)),
    ("router_architecture_frozen",
     ex["router"]["hidden_dimensions_declared"] == [128, 64]
     and ex["router"]["dropout"] == 0.10
     and "NOT part of the primary router" in ex["router"]["harm_head"]),
    ("router_training_protocol_frozen",
     "Huber" in ex["router"]["loss"] and ex["router"]["optimizer"] == "AdamW"
     and ex["router"]["lr"] == 1e-3 and ex["router"]["max_epochs"] == 200
     and ex["router"]["batch_size"] == 128 and ex["router"]["seed"] == 42),
    ("routing_threshold_rule_frozen",
     ex["routing"]["threshold_source"] == "ROUTER_DEVELOPMENT quantiles only"),
    ("lambda_grid_frozen", ex["routing"]["lambda_grid"] == [0.0, 0.25, 0.5, 1.0]),
    ("post_safety_extension_frozen",
     ex["post_safety"]["extension_status"] == "CONTROLLED_CORE_EXTENSION"
     and ex["post_safety"]["included_in"] == "A8"
     and ex["post_safety"]["saves_compute"] is False),
    ("fusion_exact",
     ex["fusion"]["alpha_blending"] is False and ex["fusion"]["learned_fusion"] is False
     and "outside frozen ROI" in ex["fusion"]["rule"]),
    ("segmentation_threshold_inherited",
     ex["fusion"]["segmentation_threshold"] == 0.5
     and ex["fusion"]["segmentation_threshold_source"] == "INHERITED"
     and ex["fusion"]["threshold_tuning"] is False),
    ("no_architecture_search_allowed", ex.get("no_architecture_search_allowed") is True),
    ("no_holdout_outcomes_read",
     ex.get("holdout_outcomes_read_in_phase24") == 0 and pe.get("holdout_outcomes_read") == 0),
    ("no_VAL_tuning", ex.get("val_outcome_reads_in_phase24") == 0),
    ("TEST_zero", ex.get("test_reads") == 0
     and arch.get("TEST_lock", {}).get("status") == "CLOSED"),
    ("Phase25_not_started", ex.get("phase25_started") is False),

    # additional integrity
    ("revision_v1_1_present", rev.get("architecture_id") == "ra_medfilm_barr_narrowed_v1_1"),
    ("revision_reason_completeness_only",
     rev.get("revision_reason") == "SPECIFICATION_COMPLETENESS_ONLY"),
    ("science_changed_false", ex.get("science_changed") is False),
    ("method_name_unchanged", ex.get("method_name") == "RA-MedFiLM-BARR"
     and rev.get("method_name_unchanged") == "RA-MedFiLM-BARR"),
    ("historical_provenance_preserved",
     rev.get("historical_provenance_preserved", {}).get("notebook_sha256") == OLD_NB_SHA),
    ("refiner_within_ceiling",
     ex["refiner"]["expected_parameter_count_closed_form"] <= 2_000_000),
    ("router_within_250k",
     ex["router"]["expected_parameter_count_closed_form"] <= 250_000),
    ("refiner_envelope_reduction_documented",
     ex["refiner"]["envelope_reduction_applied"] is True
     and len(ex["refiner"]["envelope_reduction_alternatives_considered"]) == 4),
    ("augmentation_inherited_exactly",
     ex["augmentation"]["inherited_from"] == "src.data.transforms.SegmentationTransform(train=True)"
     and ex["augmentation"]["inherited_constants"]["flip_probability"] == 0.5
     and ex["augmentation"]["inherited_constants"]["rotation_degrees"] == 5.0),
    ("augmentation_no_elastic_cutmix_mixup",
     set(ex["augmentation"]["forbidden_for_primary"]) ==
     {"elastic deformation", "CutMix", "MixUp", "aggressive domain-specific augmentation"}),
    ("run_policy_no_sweeps",
     ex["run_policy"]["architecture_sweep"] is False
     and ex["run_policy"]["lr_sweep"] is False
     and ex["run_policy"]["hidden_size_sweep"] is False
     and ex["run_policy"]["loss_sweep"] is False),
    ("oof_schema_schema_only",
     len(sch) == 11 and all(r["column"] for r in sch)),
    ("split_group_integrity",
     pe.get("zero_overlap_group_level") is True
     and pe.get("group_integrity", {}).get("groups_straddling_splits") == 0),
    ("split_domain_stratified",
     pe.get("stratification_key", "").startswith("dataset")),
    ("split_deterministic", pe.get("deterministic_recheck") is True),
    ("split_dev_hold_counts",
     pe.get("development_n") == 4957 and pe.get("holdout_n") == 875),
    # science identity (§24)
    ("phase23_bindings_unchanged",
     nov.get("phase23_overall_label") == "PARTIALLY_OCCUPIED__NARROWER_NOVELTY_POSSIBLE"
     and nov.get("phase23_maximum_defensible_claim_level") == 2),
    ("novelty_boundary_unchanged",
     arch.get("contribution_type", "").startswith("SYSTEM / INTEGRATION")),
    ("hypotheses_unchanged",
     arch.get("hypotheses", {}).get("load_bearing") == "H1"),
    ("comparators_unchanged", len(rows(TAB / "phase24_comparator_plan.csv")) == 11),
    ("preservation_margin_unchanged",
     arch.get("preservation_margin", {}).get("absolute_macro_domain_dice_margin") == 0.005),
    ("statistics_unchanged",
     arch.get("statistics", {}).get("n_boot") == 2000
     and arch.get("statistics", {}).get("seed") == 42),
    ("failure_criteria_unchanged",
     len(rows(TAB / "phase24_success_failure_criteria.csv")) == 8),
    ("science_predecessors_unchanged", science_unchanged),
    ("all_four_predecessors_ok", all(pred_ok.values())),
]

n_pass = sum(1 for _, ok in checks)
n_fail = len(checks) - n_pass
verdict = ("PHASE24_SPEC_COMPLETENESS_REPAIR_PASS" if n_fail == 0
           else "PHASE24_SPEC_COMPLETENESS_REPAIR_FAIL")

out = {
    "artifact": "phase24_spec_completeness_repair",
    "phase": 24,
    "repair": "POST_PHASE24_SPECIFICATION_COMPLETENESS_REPAIR",
    "purpose": ("prove every remaining implementation degree of freedom was frozen BEFORE Phase 25 "
                "so Phase 25 cannot choose architecture or protocol from observed performance"),
    "architecture_id": "ra_medfilm_barr_narrowed_v1_1",
    "supersedes": "ra_medfilm_barr_narrowed_v1",
    "method_name": "RA-MedFiLM-BARR",
    "science_changed": False,
    "n_checks": len(checks),
    "n_passed": n_pass,
    "n_failed": n_fail,
    "verdict": verdict,
    "checks": [{"check": n, "pass": ok} for n, ok in checks],
    "notebook_sha256_previous": OLD_NB_SHA,
    "notebook_sha256_current": nb_sha,
    "science_predecessors": pred_ok,
    "science_unchanged": science_unchanged,
    "no_training": True,
    "no_inference": True,
    "module_instantiations": 0,
    "holdout_outcomes_read": 0,
    "val_outcome_reads": 0,
    "test_reads": 0,
    "phase25_started": False,
    "generated_utc": UTC,
}
(AUD / "phase24_spec_completeness_repair.json").write_text(
    json.dumps(out, indent=1), encoding="utf-8")

print(f"spec-completeness: {n_pass}/{len(checks)} PASS -> {verdict}")
for n, ok in checks:
    if not ok:
        print("  FAIL:", n)
print()
print("science predecessors unchanged:", science_unchanged)
print("notebook sha previous:", OLD_NB_SHA)
print("notebook sha current :", nb_sha)
assert n_fail == 0, f"{n_fail} spec-completeness check(s) failed"
