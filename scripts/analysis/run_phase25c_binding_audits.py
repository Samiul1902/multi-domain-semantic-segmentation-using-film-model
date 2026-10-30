"""Phase 25C -- binding audits for Phase24 (§24), Phase25A, Phase25B (§5) and the
canonical global-cache provenance (§6).

These are read-only provenance bindings; no inference happens here.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
sys.path.insert(0, str(ROOT))
CODE = ROOT / "notebooks" / "phasewise" / "phase_25c_paired_gain_labels" / "code"
sys.path.insert(0, str(CODE))
import phase25c_common as C  # noqa: E402

AUD = ROOT / "reports" / "audits"
UTC = "2026-09-30T16:57:00+00:00"

NB = {
    "phase24": ROOT / "notebooks/phasewise/phase_24_architecture_spec/"
               "phase24_narrowed_benefit_aware_refinement_spec.ipynb",
    "phase25a": ROOT / "notebooks/phasewise/phase_25a_regional_refiner/"
                "phase25a_dedicated_regional_refiner.ipynb",
    "phase25b": ROOT / "notebooks/phasewise/phase_25b_gt_free_features/"
                "phase25b_gt_free_pre_refinement_features.ipynb",
}


def main() -> int:
    # ---------------- Phase24 binding -------------------------------------- #
    p24 = C.jload(AUD / "phase24_v1_2_feature_spec_final_check.json")
    p24state = C.jload(AUD / "project_state_after_phase24_v1_2_closure.json")
    canon = C.jload(AUD / "phase25a_canonical_governance_pointer.json")
    C.jdump({
        "artifact": "phase25c_phase24_binding",
        "phase": "25C",
        "method": C.METHOD,
        "architecture_revision": C.ARCH_REVISION,
        "phase24_notebook_path": str(NB["phase24"].relative_to(ROOT)).replace("\\", "/"),
        "phase24_notebook_sha256": C.sha256_file(NB["phase24"]),
        "phase24_notebook_sha_expected": C.EXPECTED["phase24_notebook_sha256"],
        "phase24_notebook_sha_matches": (C.sha256_file(NB["phase24"])
                                         == C.EXPECTED["phase24_notebook_sha256"]),
        "phase24_v1_2_status": p24state.get("phase_status", {}).get(
            "phase_24_router_feature_spec_v1_2")
        or p24state.get("phase_24_router_feature_spec_v1_2"),
        "phase24_v1_2_final_check_all_pass":
            (p24.get("all_pass") if "all_pass" in p24 else p24.get("D1_RESOLVED") and p24.get("D2_RESOLVED")),
        "phase24_v1_2_final_check_verdict": p24.get("verdict"),
        "roi_proposal_threshold": C.ROI_PROPOSAL_THRESHOLD,
        "segmentation_output_threshold": C.SEGMENTATION_OUTPUT_THRESHOLD,
        "categories": {"BENEFICIAL": f">= +{C.BENEFICIAL_DELTA}",
                       "HARMFUL": f"<= {C.HARMFUL_DELTA}",
                       "NEUTRAL": f"({C.HARMFUL_DELTA}, +{C.BENEFICIAL_DELTA})"},
        "test_reads": 0,
        "generated_utc": UTC,
    }, AUD / "phase25c_phase24_binding.json")

    # ---------------- Phase25A binding ------------------------------------- #
    xfit = C.jload(AUD / "phase25a_crossfit_protocol.json")
    C.jdump({
        "artifact": "phase25c_phase25a_binding",
        "phase": "25C",
        "method": C.METHOD,
        "phase25a_notebook_path": str(NB["phase25a"].relative_to(ROOT)).replace("\\", "/"),
        "phase25a_notebook_sha256": C.sha256_file(NB["phase25a"]),
        "phase25a_notebook_sha_matches": (C.sha256_file(NB["phase25a"])
                                          == C.EXPECTED["phase25a_notebook_sha256"]),
        "phase25a_classification": canon.get("classification"),
        "crossfit_protocol_verdict": xfit.get("verdict"),
        "outer_folds": xfit.get("outer_folds"),
        "final_refiner_used_for_oof": False,
        "roi030_cache_root": str(C.ROI030_CACHE.relative_to(ROOT)).replace("\\", "/"),
        "roi030_cache_manifest_sha256": C.sha256_file(C.ROI030_MANIFEST),
        "test_reads": 0,
        "generated_utc": UTC,
    }, AUD / "phase25c_phase25a_binding.json")

    # ---------------- Phase25B binding (§5) -------------------------------- #
    C.jdump({
        "artifact": "phase25c_phase25b_binding",
        "phase": "25C",
        "method": C.METHOD,
        "architecture_revision": C.ARCH_REVISION,
        "phase25b_notebook_path": str(NB["phase25b"].relative_to(ROOT)).replace("\\", "/"),
        "phase25b_notebook_sha256": C.sha256_file(NB["phase25b"]),
        "phase25b_notebook_sha_matches": (C.sha256_file(NB["phase25b"])
                                          == C.EXPECTED["phase25b_notebook_sha256"]),
        "feature_cache_dir": str(C.PHASE25B_CACHE.relative_to(ROOT)).replace("\\", "/"),
        "matrix_sha256": C.sha256_file(C.PHASE25B_CACHE / "features.npy"),
        "metadata_sha256": C.sha256_file(C.PHASE25B_CACHE / "metadata.csv"),
        "schema_sha256": C.sha256_file(C.PHASE25B_CACHE / "feature_schema.csv"),
        "matrix_sha_matches": (C.sha256_file(C.PHASE25B_CACHE / "features.npy")
                               == C.EXPECTED["phase25b_matrix_sha256"]),
        "metadata_sha_matches": (C.sha256_file(C.PHASE25B_CACHE / "metadata.csv")
                                 == C.EXPECTED["phase25b_metadata_sha256"]),
        "schema_sha_matches": (C.sha256_file(C.PHASE25B_CACHE / "feature_schema.csv")
                               == C.EXPECTED["phase25b_schema_sha256"]),
        "phase25b_feature_values_used_for_label_generation": False,
        "phase25b_allowed_reads": ["metadata.csv", "feature_schema.csv", "cache hashes",
                                   "sample_id", "feature_row_index", "outer_fold",
                                   "task_id/domain metadata"],
        "phase25c_label_source": "candidate-refined vs global full-field Dice against GT",
        "role_separation": {
            "phase25b": "202-D GT-free pre-refinement features (identity join only)",
            "phase25c": "OOF paired refinement-gain labels",
            "phase25d": "benefit-router training (owns the 16-D task embedding)",
        },
        "test_reads": 0,
        "generated_utc": UTC,
    }, AUD / "phase25c_phase25b_binding.json")

    # ---------------- Global cache binding (§6) ---------------------------- #
    cm = C.jload(C.ROI030_MANIFEST)
    C.jdump({
        "artifact": "phase25c_global_cache_binding",
        "phase": "25C",
        "method": C.METHOD,
        "purpose": "bind the canonical ROI-0.30 global prediction cache as the p_global source",
        "global_model_forward_passes": 0,
        "global_probability_source": "frozen Phase25A ROI-0.30 prob512.npy (float32)",
        "global_checkpoint_sha256": cm.get("global_checkpoint_sha256"),
        "global_checkpoint_sha_matches": (cm.get("global_checkpoint_sha256")
                                          == C.EXPECTED["phase21_global_sha256"]),
        "cache_root": str(C.ROI030_CACHE.relative_to(ROOT)).replace("\\", "/"),
        "cache_manifest_sha256": C.sha256_file(C.ROI030_MANIFEST),
        "population": cm.get("population"),
        "population_n": cm.get("population_n"),
        "action_available_n": cm.get("action_available_n"),
        "prob512_dtype": "float32",
        "prob512_resolution": 512,
        "roi_proposal_threshold": cm.get("roi_proposal_threshold"),
        "segmentation_output_threshold": cm.get("segmentation_output_threshold"),
        "preprocessing_binding": cm.get("preprocessing_binding"),
        "router_holdout_used": False,
        "val_used": False,
        "test_reads": 0,
        "verdict": "PHASE25C_GLOBAL_CACHE_BOUND",
        "generated_utc": UTC,
    }, AUD / "phase25c_global_cache_binding.json")

    print("Phase24 / Phase25A / Phase25B / global-cache binding audits written.")
    print("  phase24 nb match :", C.sha256_file(NB["phase24"]) == C.EXPECTED["phase24_notebook_sha256"])
    print("  phase25a nb match:", C.sha256_file(NB["phase25a"]) == C.EXPECTED["phase25a_notebook_sha256"])
    print("  phase25b nb match:", C.sha256_file(NB["phase25b"]) == C.EXPECTED["phase25b_notebook_sha256"])
    print("  global ckpt match:", cm.get("global_checkpoint_sha256") == C.EXPECTED["phase21_global_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
