"""Phase 22 — prospectively freeze the diagnostic protocol BEFORE outcome analysis.

Requirement (§8 of the Phase-22 instruction): the protocol must be frozen before
results are inspected, and must not be changed afterwards. This script therefore
writes a single declarative artifact and verifies it against the frozen Phase-21
and Phase-20 bindings it depends on. It performs no inference and no training.

Run this BEFORE the scale / regional probes. Re-running it later must produce the
same content; the script is idempotent and will refuse to overwrite a frozen
protocol whose content differs, unless ``--force`` is given (which is itself
recorded).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.analysis import phase22_common as C  # noqa: E402

OUT = C.AUDITS / "phase22_diagnostic_protocol.json"

PROTOCOL = {
    "artifact": "phase22_diagnostic_protocol",
    "protocol_id": "phase22_diagnostic_protocol_v1",
    "phase": 22,
    "title": "PHASE 22 — MULTI-DOMAIN SCALE, REGIONAL-BENEFIT & RESOURCE GAP ANALYSIS",
    "declared_before_outcome_analysis": True,
    "frozen": True,
    "is_training_phase": False,
    "is_diagnostic_only": True,
    "reference_model_is_final_ra_medfilm_seg_plus_plus": False,
    "reference_model_is_global_reference_only": True,

    "hard_boundaries": [
        "no model training",
        "no fine-tuning",
        "no architecture modification",
        "no benefit-predictor training",
        "no localizer / refiner / router training",
        "no pruning / quantization / distillation / NAS",
        "no TEST access of any kind",
        "no external-dataset evaluation",
        "no Phase-23 literature audit",
        "the Phase-21 canonical VAL pass must NOT be re-run or replaced",
        "no threshold tuning, no TTA, no morphology",
    ],

    "cohorts": {
        "manifest_version": C.MANIFEST_VERSION,
        "TRAIN": {"ISIC": 2556, "BUSI": 602, "KVASIR": 696, "KUB": 1978, "total": 5832},
        "VAL": {"ISIC": 357, "BUSI": 84, "KVASIR": 87, "KUB": 280, "total": 808},
        "TEST": "LOCKED — 0 image reads, 0 mask reads, 0 inference, 0 visualization",
        "allowable_cohorts_for_phase22": ["TRAIN", "VAL"],
        "task_ids": {"ISIC": 0, "BUSI": 1, "KVASIR": 2, "KUB": 3},
        "task_id_role": "FiLM conditioning only (Phase-21 architecture)",
    },

    "reference_model": {
        "experiment_id": C.EXPERIMENT_ID,
        "architecture_id": C.ARCHITECTURE_ID,
        "checkpoint": "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt",
        "checkpoint_sha256_expected": None,      # filled at freeze time
        "best_epoch": 66,
        "parameter_count": 3523001,
        "frozen": True,
        "no_further_training": True,
    },

    "input_representation": {
        "channel_policy": C.CHANNEL_POLICY,
        "native_L_domains_replicated_to_3_chunks": True,
        "intensity_normalization": "divide by 255.0 -> [0,1]",
        "no_learned_modality_adapter": True,
        "no_domain_specific_normalization_branch": True,
    },

    "spatial_contract": {
        "policy": "aspect-preserving resize + centre pad",
        "scale_formula": "scale = min(size / width, size / height)",
        "resized_formula": "rw, rh = max(1, round(width*scale)), max(1, round(height*scale))",
        "image_resample": "BILINEAR",
        "mask_resample": "NEAREST",
        "pad_fill": 0,
        "padding_alignment": "left, top = (size-rw)//2, (size-rh)//2",
        "supported_sizes": list(C.SUPPORTED_SIZES),
        "canonical_size": C.CANONICAL_SIZE,
        "implementation": "src.analysis.phase22_common.aspect_resize_pad (byte-verified "
                          "equivalent to src.data.transforms.SegmentationTransform)",
        "train_augmentation": "NOT APPLIED (diagnostic inference is deterministic)",
    },

    "decision_rule": {
        "rule": "pred = (float32(prob) >= 0.5)",
        "threshold": C.THRESHOLD,
        "applied_identically_to": ["canonical reference maps", "every diagnostic probe"],
        "justification_artifact": "reports/audits/phase22_threshold_rule_audit.json",
        "known_limitation": ("the persisted float16 probability maps cannot reproduce "
                             "the persisted uint8 predictions; exact-0.5 pixels are "
                             "labelled both ways on disk. The residual is bounded, "
                             "declared, and identical in form on every arm."),
    },

    "scale_probe": {
        "sizes": [C.CANONICAL_SIZE, *C.SCALE_PROBE_SIZES],
        "reference": "persisted Phase-21 canonical VAL probability maps",
        "comparison_space": "NATIVE_IMAGE",
        "why_native_space": ("the canonical maps are square 512 canvases with centred "
                             "padding; comparing without returning to native space "
                             "would conflate padding with image content"),
        "is_a_resolution_search": False,
        "may_claim_optimal_resolution": False,
    },

    "regional_probe": {
        "roi_rule": {
            "source_oracle": "tight bounding box of the GROUND-TRUTH foreground",
            "source_predicted": "tight bounding box of the frozen model's thresholded prediction",
            "margin": C.ORACLE_ROI_MARGIN,
            "expansion": "centre-preserving, margin on EACH side along EACH axis",
            "expanded_extent_factor": 1.0 + 2 * C.ORACLE_ROI_MARGIN,
            "clip_to_source_boundary": True,
            "recentre_after_clipping": False,
            "square_pad_about_box_centre": True,
            "crop_resample": "aspect-preserving resize + centre pad to 512",
            "reprojection": "paste regional probability over the ROI footprint only",
            "outside_roi": "original recomputed global probability, unchanged",
        },
        "frozen_before_outcomes": True,
        "no_learned_roi_proposal": True,
        "empty_predicted_roi_behaviour": "status NO_PREDICTED_ROI, delta recorded as 0",
    },

    "statistics": {
        "bootstrap": {"n_boot": 2000, "seed": 42, "alpha": 0.05, "unit": "image",
                      "paired": True, "domain_stratified": True,
                      "identical_resampled_indices_for_both_arms": True},
        "ci_overlap_rule": ("where a paired CI overlaps zero the arms are NOT "
                            "separable and no ordering claim may be made"),
        "aggregation": {"per_domain": "unweighted mean of per-image metrics",
                        "macro_domain": "unweighted mean of the four per-domain values"},
        "metrics": {
            "pixel": ["dice", "iou", "precision", "recall"],
            "boundary": ["hd95"],
            "implementation": "src.metrics.evaluation_metrics.segmentation_metrics",
        },
    },

    "failure_taxonomy": {
        "order_of_assignment": ["EMPTY_CASE_BOTH", "EMPTY_CASE_FALSE_POS",
                                "EMPTY_CASE_MISSED", "OVER_SEGMENTATION",
                                "UNDER_SEGMENTATION", "MIXED_BOUNDARY", "GOOD"],
        "thresholds": {"good_precision": 0.60, "good_recall": 0.60,
                       "imbalance_precision": 0.80, "imbalance_recall": 0.80},
        "declared_prospectively": True,
        "used_for_model_selection": False,
    },

    "forbidden_claims": [
        "that the ORACLE regional variant is a deployable method or an achieved result",
        "that any regional mechanism 'achieves' the oracle upper bound",
        "that FiLM caused any measured difference (no architecture-matched control exists)",
        "that a single model is the winner where the paired CI overlaps zero",
        "that the persisted float16 probability maps reproduce the persisted predictions",
        "that Phase 22 identifies the optimal inference resolution",
        "any TEST-derived statement of any kind",
    ],

    "required_outputs": [
        "reports/audits/phase22_diagnostic_protocol.json",
        "reports/audits/phase22_phase21_reference_binding.json",
        "reports/audits/phase22_global_failure_atlas.json",
        "reports/audits/phase22_scale_sensitivity.json",
        "reports/audits/phase22_scale_probe_fidelity.json",
        "reports/audits/phase22_threshold_rule_audit.json",
        "reports/audits/phase22_oracle_regional_intervention.json",
        "reports/audits/phase22_regional_fidelity.json",
        "reports/audits/phase22_benefit_heterogeneity.json",
        "reports/audits/phase22_oracle_accept_if_beneficial.json",
        "reports/audits/phase22_resource_frontier.json",
        "reports/audits/phase22_prediction_derived_roi.json",
        "reports/audits/phase22_uncertainty_vs_benefit.json",
        "reports/audits/phase22_routing_regret.json",
        "reports/audits/phase22_harm_analysis.json",
        "reports/audits/phase22_resource_gap.json",
        "reports/audits/phase22_conditional_compute_envelopes.json",
        "reports/audits/phase22_cpu_baseline.json",
        "reports/audits/phase22_kub_tiny_analysis.json",
        "reports/audits/phase22_domain_preservation.json",
        "reports/audits/phase22_statistics.json",
        "reports/audits/phase22_scale_vs_regional.json",
        "reports/audits/phase22_future_benefit_label_contract.json",
        "reports/audits/phase22_candidate_method_evidence.json",
        "reports/audits/phase22_no_new_training_audit.json",
        "reports/audits/phase22_final_freeze.json",
        "reports/audits/phase22_governance_sync.json",
        "reports/phase22_resource_gap_report.md",
        "notebooks/phasewise/phase_22_resource_gap/phase22_resource_gap_analysis.ipynb",
    ],

    "terminal_state_on_success":
        "PHASE22_MULTIDOMAIN_SCALE_REGIONAL_RESOURCE_GAP_ANALYSIS_COMPLETE__"
        "PHASE23_ELIGIBLE_NOT_STARTED",

    "test_reads": {"test_image_reads": 0, "test_mask_reads": 0,
                   "test_inference": 0, "test_visualization": 0},
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    C.verify_no_test_access()

    freeze = C.load_json(C.PHASE21_FREEZE)
    if freeze.get("freeze_verified") is not True:
        raise SystemExit("FAIL-CLOSED: Phase-21 freeze is not verified")
    proto_sha = C.sha256_file(ROOT / C.PROTOCOL_PATH)
    if proto_sha != C.PROTOCOL_SHA256:
        raise SystemExit(f"FAIL-CLOSED: frozen Phase-20 protocol SHA drift: {proto_sha}")

    payload = dict(PROTOCOL)
    payload["reference_model"] = dict(PROTOCOL["reference_model"])
    payload["reference_model"]["checkpoint_sha256_expected"] = (
        freeze["training"]["best_checkpoint_sha256"])
    payload["frozen_bindings"] = {
        "phase20_protocol_path": C.PROTOCOL_PATH,
        "phase20_protocol_sha256": proto_sha,
        "phase21_final_freeze": "reports/audits/phase21_final_freeze.json",
        "phase21_final_freeze_sha256": C.sha256_file(C.PHASE21_FREEZE),
        "phase21_terminal_state": freeze["terminal_state"],
        "phase21_canonical_val_inference_runs": freeze["canonical_val_evaluation"][
            "canonical_val_inference_runs"],
        "phase22_entry_gate": "reports/audits/phase22_entry_gate.json",
        "phase22_entry_gate_verdict": C.load_json(
            C.AUDITS / "phase22_entry_gate.json")["verdict"],
    }

    if OUT.exists() and not args.force:
        prior = C.load_json(OUT)
        prior_cmp = {k: v for k, v in prior.items() if k != "generated_utc"}
        new_cmp = {k: v for k, v in payload.items() if k != "generated_utc"}
        if prior_cmp == new_cmp:
            print(f"protocol already frozen and IDENTICAL: {OUT}")
            return 0
        raise SystemExit(
            "FAIL-CLOSED: a frozen Phase-22 protocol already exists and differs. "
            "The protocol must not change after outcomes are seen. "
            "Re-run with --force only if outcomes have NOT yet been analysed.")

    from datetime import datetime, timezone
    payload["generated_utc"] = datetime.now(timezone.utc).isoformat()
    payload["forced_overwrite"] = bool(args.force)
    C.write_json(OUT, payload)
    print(f"FROZEN {OUT}")
    print(f"  checkpoint expected: {payload['reference_model']['checkpoint_sha256_expected'][:16]}")
    print(f"  decision rule      : {payload['decision_rule']['rule']}")
    print(f"  scales             : {payload['scale_probe']['sizes']}")
    print(f"  required outputs   : {len(payload['required_outputs'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
