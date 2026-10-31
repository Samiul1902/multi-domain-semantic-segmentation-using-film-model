"""Freeze the external stress-test evaluation plan as machine-readable artefacts.

Writes, under ``reports/audits/c1_external_stress_v1_0/``:

  * ``external_stress_plan.json``  -- the plan as data
  * ``plan_manifest.json``         -- SHA-256 of every bound input, plus the SHA-256
                                      of the plan documents themselves

Non-circular: ``plan_manifest.json`` never contains its own digest, and it is written
last.  No hash in this file is hand-typed; every one is read from disk at write time.

This script performs NO inference.  It is the pre-registration step only.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
AUD = ROOT / "reports" / "audits" / "c1_external_stress_v1_0"

PLAN_MD = AUD / "EXTERNAL_STRESS_TEST_PLAN.md"
PLAN_JSON = AUD / "external_stress_plan.json"
PLAN_MANIFEST = AUD / "plan_manifest.json"

REVISION = "c1_external_stress_plan_v1_0"

# --------------------------------------------------------------------------- #
# bound inputs (paths only; every digest is computed, never authored)
# --------------------------------------------------------------------------- #
BOUND_INPUTS = {
    "global_checkpoint":
        "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt",
    "global_config":
        "experiments/phase21_global_medfilm_fourdomain_seed42_clean_v3/config.json",
    "refiner_checkpoint":
        "checkpoints/phase25a_barr_regional_refiner_v1_1_roi030/final/final.pt",
    "router_checkpoint":
        "checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt",
    "safety_checkpoint":
        "checkpoints/phase25f_barr_post_safety_v1_0_seed42/final/final.pt",
    "cvc_manifest":
        "reports/external_extension/manifests/ext02_cvc_clinicdb_manifest.csv",
    "breast_manifest":
        "reports/external_extension/manifests/ext02_breast_us_manifest.csv",
    "stones_manifest":
        "reports/external_extension/manifests/ext02_1_stones_manifest_reconciled.csv",
    "transform_source": "src/data/transforms.py",
    "roi_source": "src/data/barr_roi.py",
    "pre_refinement_features_source": "src/features/barr_pre_refinement_features.py",
    "global_model_source": "src/models/film/global_medfilm.py",
    "refiner_source": "src/models/barr/regional_refiner.py",
    "router_class_source": "scripts/analysis/train_phase25d_router.py",
    "safety_class_source": "scripts/analysis/phase25f_execution_common.py",
    "safety_features_source": "scripts/analysis/phase25f_post_safety_features.py",
    "phase29_canonical_reference":
        "scripts/analysis/phase29_phase_d_canonical_seed_inference.py",
}

# Digests that were established by prior frozen phases and are re-asserted here.
# These are NOT the authority -- the authority is the file on disk.  A mismatch
# between this table and disk aborts the freeze.
PRIOR_BINDINGS = {
    "global_checkpoint":
        "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7",
    "refiner_checkpoint":
        "6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109",
    "router_checkpoint":
        "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b",
    "safety_checkpoint":
        "eee9b97b9921e53fc07eac9281dce64ba518c6e1659916b97b0b3bec21ec6d2e",
    "router_class_source":
        "fc7c1bdf263ae4551dcb8f170d3203adb8540fbc189846265b74f6eca1541e91",
    "safety_class_source":
        "98cf958a377e2de30e0b67e63fd56bafea418b2b061a362ee7284e852012cd2e",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write_json(obj, path: Path) -> None:
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")


def main() -> int:
    AUD.mkdir(parents=True, exist_ok=True)

    digests = {}
    for key, rel in BOUND_INPUTS.items():
        p = ROOT / rel
        if not p.is_file():
            raise SystemExit(f"ABORT: bound input missing: {rel}")
        digests[key] = sha256_file(p)

    # re-assert the digests that earlier frozen phases established
    mismatches = {
        k: {"prior": v, "on_disk": digests[k]}
        for k, v in PRIOR_BINDINGS.items() if digests[k] != v
    }
    if mismatches:
        raise SystemExit(f"ABORT: bound input drifted from prior frozen binding: {mismatches}")

    plan = {
        "artifact": "c1_external_stress_plan",
        "revision": REVISION,
        "status": "PRE_REGISTERED__FROZEN_BEFORE_ANY_EXTERNAL_INFERENCE",
        "classification": "RETROSPECTIVE_EXTERNAL_STRESS_TEST",
        "written_utc_host_clock": "2026-10-31T03:59:29Z",
        "clock_caveat": (
            "Host RTC is not synchronised (no NTP source). The absolute time carries "
            "an unquantified offset. The binding claim is the ordering: this plan was "
            "written before any external probability array, binary mask or metric "
            "existed."
        ),

        "cohorts": [
            {
                "cohort": "CVC-ClinicDB",
                "manifest": BOUND_INPUTS["cvc_manifest"],
                "manifest_sha256": digests["cvc_manifest"],
                "n_evaluable": 612,
                "n_analysed": 612,
                "task_id": 2,
                "domain_analogue": "KVASIR",
                "cluster_unit": "sequence_id",
                "n_clusters": 29,
                "included": True,
            },
            {
                "cohort": "BrEaST-Lesions-USG",
                "manifest": BOUND_INPUTS["breast_manifest"],
                "manifest_sha256": digests["breast_manifest"],
                "n_evaluable": 252,
                "n_analysed": 252,
                "task_id": 1,
                "domain_analogue": "BUSI",
                "cluster_unit": "case_id",
                "n_clusters": 252,
                "included": True,
            },
            {
                "cohort": "Stones_where_are_you",
                "manifest": BOUND_INPUTS["stones_manifest"],
                "manifest_sha256": digests["stones_manifest"],
                "split_filter": {"column": "original_split", "value": "test"},
                "n_evaluable": 20,
                "n_analysed": 20,
                "task_id": 3,
                "domain_analogue": "KUB",
                "cluster_unit": "image",
                "n_clusters": 20,
                "stone_positive": 6,
                "stone_absent": 14,
                "foreground_rule": "category_id == 7 ('stone') -> foreground; all others -> background",
                "subgroup_reporting": ["all_20", "six_positive", "fourteen_absent"],
                "included": True,
            },
            {
                "cohort": "HAM10000",
                "included": False,
                "status": "HAM10000_EXCLUDED__MASK_PROVENANCE_UNVERIFIED",
                "reason": (
                    "The HAM10000 folder is the ISIC-2018 Task 3 classification release, "
                    "which ships no segmentation masks. 10,015 mask files exist with no "
                    "recorded provenance, so Dice against them would not measure the model. "
                    "No inference is run and the previously quoted 79.15% is not citable."
                ),
            },
        ],
        "total_analysed_images": 884,

        "exclusion_rule": (
            "Row included iff evaluable == True in the frozen manifest AND image_path "
            "resolves AND the ground-truth reference resolves AND the mask rasterises. "
            "Applied mechanically; no post-hoc row drops."
        ),

        "prior_consultation_disclosure": (
            "All three included cohorts were previously used to build the ext02 manifests "
            "and to classify evidence provenance, and a figure pilot previously ran the "
            "global model on 8 hand-picked single cases using a NON-CANONICAL plain "
            "512x512 stretch resize. Those pilot numbers are superseded and are not "
            "pooled with this study. No checkpoint, threshold, seed or preprocessing "
            "choice was selected on the basis of external aggregate performance."
        ),

        "frozen_identities": {
            "global_checkpoint": BOUND_INPUTS["global_checkpoint"],
            "global_checkpoint_sha256": digests["global_checkpoint"],
            "global_config": BOUND_INPUTS["global_config"],
            "global_config_sha256": digests["global_config"],
            "refiner_checkpoint": BOUND_INPUTS["refiner_checkpoint"],
            "refiner_checkpoint_sha256": digests["refiner_checkpoint"],
            "router_checkpoint": BOUND_INPUTS["router_checkpoint"],
            "router_checkpoint_sha256": digests["router_checkpoint"],
            "safety_checkpoint": BOUND_INPUTS["safety_checkpoint"],
            "safety_checkpoint_sha256": digests["safety_checkpoint"],
            "refiner_note": (
                "The _roi030 refiner variant is used, matching the Phase 29 seed-42 "
                "binding. phase25a_barr_regional_refiner_v1_1 is a different artefact "
                "and is NOT used."
            ),
            "state_dict_loading": "strict=True required; no partial reload",
        },

        "preprocessing": {
            "transform": "src.data.transforms.SegmentationTransform(size=512, train=False, image_mode='RGB')",
            "image": "RGB -> aspect-preserving bilinear resize (scale=min(512/W,512/H)) -> centre on 512x512 canvas with zero pad -> /255",
            "ground_truth": "same geometry, NEAREST resize, same pad, binarise > 0",
            "coco_rasterisation": "rasterise polygons at NATIVE resolution first, then apply the geometry",
            "superseded_convention": (
                "A plain 512x512 stretch resize was used by an earlier figure pilot. It is "
                "NOT used here; stress-test numbers and figures both use the "
                "aspect-preserving convention."
            ),
        },

        "thresholds": {
            "probability": "sigmoid, float32",
            "segmentation_output": 0.5,
            "comparison": "prob >= 0.5 (lower-inclusive, float32)",
            "per_cohort_tuning": False,
            "test_time_augmentation": False,
            "ensembling": False,
            "post_processing": "none",
        },

        "barr": {
            "determination": "BARR_EXECUTABLE_FROM_VERIFIED_ARTIFACTS",
            "justification": (
                "A frozen end-to-end composition exists at "
                "scripts/analysis/phase29_phase_d_canonical_seed_inference.py. The 202-D "
                "router features come from src/features/barr_pre_refinement_features.py "
                "reading three Global MedFiLM taps via read-only forward hooks; the 16-D "
                "safety features come from "
                "scripts/analysis/phase25f_post_safety_features.py. Both class-defining "
                "sources still hash-match their Phase 29 bindings. All four checkpoints "
                "hash-match."
            ),
            "driver_note": (
                "The Phase 29 driver is hard-wired to VAL808 and its precomputed cache. "
                "The external run uses a new driver that supplies only the population and "
                "per-case bookkeeping; every frozen component and feature extractor is "
                "reused verbatim. This distinction must be stated whenever BARR external "
                "results are reported."
            ),
            "tau_c7_exact": "24796109646558761/20000000000000000000",
            "lambda_c_exact": "(1/4)*(1051648/10270749)",
            "tau_c8_exact": "tau_c7 - lambda_c",
            "router_scalar_indices": [192, 193, 194, 195, 196, 197, 200, 201],
            "router_normalisation": (
                "Only the 8 frozen scalar indices are standardised, using the "
                "checkpoint's own normalizer_mu/sigma/constant_mask. The 192 deep "
                "features are passed raw. This reproduces the Phase 29 convention."
            ),
            "safety_input": "16 standardised numeric features + 4-D task one-hot",
            "safety_accept_threshold": 0.5,
            "roi": "src.data.barr_roi.roi_geometry(p_global, threshold=0.30, margin=0.25)",
            "state_vocabulary": [
                "NOT_ATTEMPTED", "ROUTED", "EXECUTED", "ACCEPTED",
                "REJECTED", "FALLBACK_TO_GLOBAL", "FAILED",
            ],
            "state_note": (
                "ROUTED and EXECUTED are staged, not terminal. The terminal state of a "
                "selected case is ACCEPTED, REJECTED, FALLBACK_TO_GLOBAL or FAILED. Stage "
                "counts and terminal counts must both be reported."
            ),
            "abort_condition": (
                "Any component hash mismatch, any strict state-dict failure, or any "
                "disagreement between the two decision forms aborts the run and BARR is "
                "reported as BARR_NOT_EXECUTABLE_FROM_VERIFIED_ARTIFACTS."
            ),
        },

        "metrics": {
            "pixel": ["TP", "FP", "FN", "TN", "Dice", "IoU", "Precision", "Recall",
                      "Specificity", "Accuracy"],
            "surface": ["HD95", "ASSD", "NSD@2px"],
            "surface_units": "pixels",
            "surface_units_reason": (
                "No external cohort ships physical pixel spacing. Millimetre surface "
                "metrics are forbidden. Cross-cohort surface-metric comparison is "
                "prohibited; only within-cohort Global vs BARR comparison is permitted."
            ),
            "other": ["region_size_error", "empty_mask_frequency", "fp_only_case",
                      "fn_only_case", "latency_seconds"],
            "degenerate_policy": (
                "Degenerate GT and degenerate prediction cases are kept and scored. "
                "Undefined metrics are NaN with a recorded reason; NaN is never replaced "
                "by 0 and never silently dropped."
            ),
            "aggregation": (
                "Primary = per-cohort macro mean over cases (equal case weight). Pooled "
                "pixel-level aggregation is secondary and must be labelled as such."
            ),
            "cross_cohort_pooling": False,
        },

        "statistics": {
            "p_values_computed": 0,
            "bootstrap": {
                "scheme": "percentile",
                "resamples": 2000,
                "seed": 42,
                "cluster_level": True,
                "per_cohort_cluster": {
                    "CVC-ClinicDB": "sequence_id (29)",
                    "BrEaST-Lesions-USG": "case_id (252)",
                    "Stones_where_are_you": "none -- n=20, point estimates only",
                },
            },
            "multiplicity_correction": "not applicable -- no hypothesis family",
            "labelling": "descriptive interval under a stated resampling scheme",
        },

        "figures": {
            "columns_global_only": [
                "input_image", "ground_truth", "global_prediction",
                "global_error_map", "global_probability_map",
            ],
            "columns_with_barr": [
                "input_image", "ground_truth", "global_prediction",
                "global_error_map", "global_probability_map",
                "barr_final_prediction", "barr_error_map", "barr_decision_trace",
            ],
            "error_palette_rgb": {
                "TP": [0, 230, 0], "FP": [255, 32, 32],
                "FN": [32, 96, 255], "TN": [24, 24, 24],
            },
            "case_selection_rule": (
                "Per cohort: median-Dice case, worst case, best case; for Stones also the "
                "largest and smallest ground-truth lesion. Degenerate cases must be "
                "labelled on the panel face."
            ),
        },

        "prohibitions": [
            "No training, fine-tuning or parameter update.",
            "No threshold tuning, per-cohort calibration or operating-point selection.",
            "No access to the locked internal TEST split or ROUTER_HOLDOUT.",
            "No HAM10000 inference.",
            "No fabricated, interpolated or hand-edited predictions.",
            "No millimetre surface metrics.",
            "No pooled cross-cohort Dice.",
            "No confirmatory p-values.",
            "No change to any C1 trust boundary, approval state or scientific_execution_enabled.",
            "No modification of a frozen component source file.",
        ],

        "c1_status": {
            "scientific_execution_enabled": False,
            "approval": False,
            "launch": False,
            "decision": "NO-GO",
            "note": "This study reads no C1 trust store and provisions no key.",
        },

        "bound_inputs": {k: {"path": v, "sha256": digests[k]} for k, v in BOUND_INPUTS.items()},
    }

    write_json(plan, PLAN_JSON)

    if not PLAN_MD.is_file():
        raise SystemExit(f"ABORT: plan markdown missing: {PLAN_MD}")

    manifest = {
        "artifact": "c1_external_stress_plan_manifest",
        "revision": REVISION,
        "self_digest_included": False,
        "non_circular": (
            "This manifest does not contain its own digest. It is written last, after the "
            "plan documents it binds."
        ),
        "documents": {
            "EXTERNAL_STRESS_TEST_PLAN.md": sha256_file(PLAN_MD),
            "external_stress_plan.json": sha256_file(PLAN_JSON),
        },
        "bound_inputs": {k: {"path": v, "sha256": digests[k]}
                         for k, v in BOUND_INPUTS.items()},
        "prior_binding_reassertion": {
            "checked": sorted(PRIOR_BINDINGS),
            "mismatches": 0,
            "all_match": True,
        },
    }
    write_json(manifest, PLAN_MANIFEST)

    print("PLAN FROZEN")
    print(f"  plan.md    {manifest['documents']['EXTERNAL_STRESS_TEST_PLAN.md']}")
    print(f"  plan.json  {manifest['documents']['external_stress_plan.json']}")
    print(f"  manifest   {sha256_file(PLAN_MANIFEST)}")
    print(f"  bound inputs verified: {len(BOUND_INPUTS)}")
    print(f"  prior bindings re-asserted: {len(PRIOR_BINDINGS)} (0 mismatches)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
