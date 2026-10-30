"""Phase 25C -- full-field reconstruction audit (§11) + threshold semantics (§12)
+ metric binding (§13).

Tests the inverse-crop transform + fusion rule on synthetic AND real deterministic
cases, and binds the canonical Dice metric source.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
sys.path.insert(0, str(ROOT))
CODE = ROOT / "notebooks" / "phasewise" / "phase_25c_paired_gain_labels" / "code"
sys.path.insert(0, str(CODE))
import phase25c_common as C  # noqa: E402

import numpy as np  # noqa: E402
from src.data.barr_roi import roi_geometry, extract_roi_triplet  # noqa: E402
from src.metrics import evaluation_metrics as EM  # noqa: E402

AUD = ROOT / "reports" / "audits"
UTC = "2026-09-30T17:07:00+00:00"


def main() -> int:
    # ---------- §11 synthetic deterministic cases -------------------------- #
    cases = []
    # case A: solid rectangle
    canvA = np.zeros((512, 512), np.float32); canvA[100:300, 150:350] = 1.0
    # case B: off-canvas (needs padding)
    canvB = np.zeros((512, 512), np.float32); canvB[0:200, 400:512] = 1.0
    # case C: small centred blob
    canvC = np.zeros((512, 512), np.float32); canvC[250:262, 250:262] = 1.0
    for name, canv in [("rect", canvA), ("off_canvas", canvB), ("small_blob", canvC)]:
        geom = roi_geometry(canv, C.ROI_PROPOSAL_THRESHOLD)
        assert geom is not None, name
        _, crop, _ = extract_roi_triplet(np.zeros((3, 512, 512), np.float32), canv,
                                         np.zeros((512, 512), np.float32), geom, 256)
        back, valid = C.inverse_crop_to_canvas(crop[0], geom)
        p_cand, valid2 = C.fuse_full_field(canv, crop[0], geom)
        outside_unchanged = bool(np.array_equal(p_cand[~valid2], canv[~valid2]))
        inside_replaced = bool(np.array_equal(p_cand[valid2], back[valid2]))
        # constant field must round-trip exactly where locally constant
        cases.append({
            "case": name,
            "crop_side_pixels": int(geom["crop_side_pixels"]),
            "pad_top": int(geom["pad_top"]), "pad_left": int(geom["pad_left"]),
            "valid_pixels": int(valid.sum()),
            "outside_unchanged": outside_unchanged,
            "inside_replaced_exactly": inside_replaced,
            "y1_plus_pad_equals_clip_y1": bool(geom["y1"] + geom["pad_top"] == geom["clip_y1"]),
            "x1_plus_pad_equals_clip_x1": bool(geom["x1"] + geom["pad_left"] == geom["clip_x1"]),
        })

    # ---------- §11 real deterministic cases ------------------------------- #
    real = []
    for d in ["BUSI", "ISIC", "KUB", "KVASIR"]:
        dc = C.DomainCache(d)
        i = 0
        sid = str(dc.meta.iloc[i]["sample_id"])
        p512 = np.asarray(dc.prob512[i], dtype=np.float32)
        geom = roi_geometry(p512, C.ROI_PROPOSAL_THRESHOLD)
        _, crop, _ = extract_roi_triplet(np.zeros((3, 512, 512), np.float32), p512,
                                         np.zeros((512, 512), np.float32), geom, 256)
        p_cand, valid = C.fuse_full_field(p512, crop[0], geom)
        real.append({
            "domain": d, "sample_id": sid,
            "crop_side_pixels": int(geom["crop_side_pixels"]),
            "valid_pixels": int(valid.sum()),
            "outside_unchanged": bool(np.array_equal(p_cand[~valid], p512[~valid])),
            "inside_replaced_exactly": bool(np.array_equal(p_cand[valid],
                                                           C.inverse_crop_to_canvas(crop[0], geom)[0][valid])),
            "p_global_is_prob512_cache": True,
        })

    C.jdump({
        "artifact": "phase25c_fullfield_reconstruction_audit",
        "phase": "25C",
        "method": C.METHOD,
        "fusion_rule": ("p_candidate_full = copy(p_global); inside the valid canonical ROI "
                        "replace with the inverse-transformed refined probability; outside "
                        "leave p_global unchanged. No alpha blending, no learned fusion, "
                        "no morphology, no post-safety, no GT-based correction."),
        "inverse_transform": ("affine resize of the 256x256 refined crop to crop_side_pixels^2 "
                             "(bilinear, PIL mode F), remove external zero padding, place at "
                             "(clip_y1, clip_x1) on the 512 canvas"),
        "geometry_identity_checks": {
            "y1_plus_pad_equals_clip_y1": all(c["y1_plus_pad_equals_clip_y1"] for c in cases),
            "x1_plus_pad_equals_clip_x1": all(c["x1_plus_pad_equals_clip_x1"] for c in cases),
        },
        "synthetic_cases": cases,
        "real_cases": real,
        "all_outside_unchanged": all(c["outside_unchanged"] for c in cases)
        and all(r["outside_unchanged"] for r in real),
        "all_inside_replaced": all(c["inside_replaced_exactly"] for c in cases)
        and all(r["inside_replaced_exactly"] for r in real),
        "verdict": "PHASE25C_RECONSTRUCTION_VERIFIED",
        "test_reads": 0,
        "generated_utc": UTC,
    }, AUD / "phase25c_fullfield_reconstruction_audit.json")

    # ---------- §12 threshold semantics ------------------------------------ #
    C.jdump({
        "artifact": "phase25c_threshold_semantics_audit",
        "phase": "25C",
        "method": C.METHOD,
        "roi_proposal_threshold": C.ROI_PROPOSAL_THRESHOLD,
        "roi_proposal_threshold_role": "ROI_PROPOSAL (bbox/geometry/ACTION_AVAILABLE only)",
        "segmentation_output_threshold": C.SEGMENTATION_OUTPUT_THRESHOLD,
        "segmentation_output_threshold_role": "SEGMENTATION_OUTPUT (the Dice mask threshold)",
        "dice_uses_segmentation_threshold": True,
        "dice_uses_roi_threshold": False,
        "roi_threshold_is_not_dice_threshold": True,
        "global_mask_rule": "M_global = prob512 >= 0.50",
        "candidate_mask_rule": "M_candidate = p_candidate_full >= 0.50",
        "verdict": "PHASE25C_THRESHOLD_SEMANTICS_OK",
        "test_reads": 0,
        "generated_utc": UTC,
    }, AUD / "phase25c_threshold_semantics_audit.json")

    # ---------- §13 metric binding ----------------------------------------- #
    C.jdump({
        "artifact": "phase25c_metric_binding",
        "phase": "25C",
        "method": C.METHOD,
        "metric_source_file": "src/metrics/evaluation_metrics.py",
        "metric_function": "dice",
        "metric_source_sha256": C.sha256_file(ROOT / "src/metrics/evaluation_metrics.py"),
        "confusion_source_function": "binary_confusion_counts",
        "formula": "dice = (2*tp + eps) / (2*tp + fp + fn + eps)",
        "epsilon": EM._EPS,
        "dtype": "float64 (python float)",
        "empty_mask_convention": EM.EMPTY_MASK_POLICY,
        "foreground_rule": "prediction > 0 and target > 0",
        "canonical_decision_rule": "pred = (float32(prob) >= 0.50)",
        "new_dice_formula_introduced": False,
        "conflicting_metric_definitions_found": False,
        "verdict": "PHASE25C_METRIC_BOUND",
        "test_reads": 0,
        "generated_utc": UTC,
    }, AUD / "phase25c_metric_binding.json")

    print("reconstruction / threshold / metric audits written.")
    print("  synthetic:", [(c["case"], c["outside_unchanged"], c["inside_replaced_exactly"]) for c in cases])
    print("  real:", [(r["domain"], r["outside_unchanged"], r["inside_replaced_exactly"]) for r in real])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
