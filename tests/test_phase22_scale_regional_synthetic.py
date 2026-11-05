"""Phase 22 coding verification — small deterministic SYNTHETIC fixtures only.

Scope: the computational primitives behind "Multi-Domain Scale & Transfer Gap
Analysis" (scale mapping, regional/ROI geometry, gap/regret statistics), plus a
read-only consistency check against existing frozen historical Phase-22 records.

This module NEVER reads a VAL/TEST manifest, checkpoint, image, mask or persisted
prediction. It runs no diagnostic inference, performs no training and produces no
new real-data experimental finding. Every array below is generated in memory.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest
import torch
from PIL import Image

from src.analysis import phase22_benefit as BEN
from src.analysis import phase22_common as C
from src.analysis import phase22_kub_domain as KUB
from src.analysis import phase22_resource as RES
from src.analysis import phase22_scale as SCALE

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_CLASS = "SYNTHETIC_TEST_ONLY"


def _synthetic_rgb(width: int, height: int, value: int = 120) -> Image.Image:
    array = np.full((height, width, 3), value, dtype=np.uint8)
    array[1:3, 2:5] = 255
    return Image.fromarray(array, "RGB")


def _synthetic_mask(width: int, height: int) -> Image.Image:
    return Image.fromarray(np.zeros((height, width), dtype=np.uint8), "L")


# --------------------------------------------------------------------------- #
# Scale mapping
# --------------------------------------------------------------------------- #
def test_aspect_resize_pad_geometry_is_deterministic_and_injective():
    image = _synthetic_rgb(13, 7)
    mask = _synthetic_mask(13, 7)
    tensor, mask_t, geom = C.aspect_resize_pad(image, mask, 256)
    assert tuple(tensor.shape) == (3, 256, 256)
    assert tensor.dtype == torch.float32 and torch.isfinite(tensor).all()
    assert 0.0 <= float(tensor.min()) <= float(tensor.max()) <= 1.0
    assert tuple(mask_t.shape) == (1, 256, 256)
    assert set(np.unique(mask_t.numpy()).tolist()) <= {0.0, 1.0}

    assert geom["size"] == 256 and geom["source_hw"] == (7, 13)
    assert geom["scale"] == pytest.approx(256 / 13)
    assert geom["resized_w"] == 256 and geom["resized_h"] == 138
    assert geom["pad_left"] == 0 and geom["pad_right"] == 0
    assert geom["pad_top"] == 59 and geom["pad_bottom"] == 59
    assert geom["pad_left"] + geom["resized_w"] + geom["pad_right"] == 256
    assert geom["pad_top"] + geom["resized_h"] + geom["pad_bottom"] == 256

    # deterministic on identical input; unsupported sizes fail closed
    tensor2, _, geom2 = C.aspect_resize_pad(image, mask, 256)
    assert torch.equal(tensor, tensor2) and geom == geom2
    with pytest.raises(ValueError, match="size must be one of"):
        C.aspect_resize_pad(image, mask, 128)
    # mask is optional
    _, none_mask, _ = C.aspect_resize_pad(image, None, 256)
    assert none_mask is None


def test_square_probability_map_roundtrip_and_pad_invariance():
    _, _, geom = C.aspect_resize_pad(_synthetic_rgb(13, 7), None, 256)
    native = np.full((7, 13), 0.7, dtype=np.float32)
    square = C.map_source_to_square_probability(native, geom)
    assert square.shape == (256, 256) and square.dtype == np.float32
    # centre padding is exactly zero
    assert float(square[: geom["pad_top"], :].max()) == 0.0
    assert float(square[geom["pad_top"] + geom["resized_h"]:, :].max()) == 0.0
    back = C.unmap_probability_to_source(square, geom)
    assert back.shape == native.shape
    assert np.isfinite(back).all() and float(back.min()) >= 0.0 and float(back.max()) <= 1.0
    np.testing.assert_allclose(back, native, atol=1e-6)

    # Values injected into the pad region cannot leak into native space.
    polluted = square.copy()
    polluted[: geom["pad_top"], :] = 0.99
    back_polluted = C.unmap_probability_to_source(polluted, geom)
    np.testing.assert_array_equal(back, back_polluted)

    # Non-constant synthetic map: shape and clipping contract still hold.
    ramp = np.linspace(0.0, 1.0, 7 * 13, dtype=np.float32).reshape(7, 13)
    ramp_square = C.map_source_to_square_probability(ramp, geom)
    ramp_back = C.unmap_probability_to_source(ramp_square, geom)
    assert ramp_back.shape == (7, 13)
    assert float(ramp_back.min()) >= 0.0 and float(ramp_back.max()) <= 1.0


def test_frozen_threshold_rule_is_lower_inclusive_float32():
    values = np.array([0.0, 0.4999, 0.5, 0.5001, 1.0], dtype=np.float32)
    np.testing.assert_array_equal(C.threshold_probability(values),
                                  np.array([0, 0, 1, 1, 1], dtype=np.uint8))
    # float16 storage quantisation: the adopted rule is declared, not inferred.
    half = np.array([np.float16(0.5), np.nextafter(np.float16(0.5), np.float16(0))],
                    dtype=np.float16)
    np.testing.assert_array_equal(C.threshold_probability(half),
                                  np.array([1, 0], dtype=np.uint8))
    assert C.threshold_probability(values, threshold=0.9)[3] == 0


def test_scale_boundary_tolerance_classifier():
    identical = np.array([0.1, 0.9], dtype=np.float32)
    assert SCALE._all_near_boundary(identical, identical,
                                   np.array([0, 1]), np.array([0, 1])) is True

    near_a = np.array([0.49], dtype=np.float32)
    near_b = np.array([0.51], dtype=np.float32)
    assert SCALE._all_near_boundary(near_a, near_b,
                                   np.array([0]), np.array([1])) is True

    far = np.array([0.10, 0.90], dtype=np.float32)
    assert SCALE._all_near_boundary(far, 1.0 - far,
                                   np.array([0, 1]), np.array([1, 0])) is False
    # Zero tolerance still admits exact-boundary disagreements only.
    exact = np.full(1, 0.5, dtype=np.float32)
    assert SCALE._all_near_boundary(exact, exact,
                                   np.array([0]), np.array([1]), tol=0.0) is True


# --------------------------------------------------------------------------- #
# Regional / ROI geometry (the "regional gap" side)
# --------------------------------------------------------------------------- #
def test_bbox_of_empty_single_and_rectangular_masks():
    assert C.bbox_of(np.zeros((8, 8), dtype=np.uint8)) is None
    single = np.zeros((8, 8), dtype=np.uint8)
    single[3, 4] = 1
    assert C.bbox_of(single) == {"min_y": 3, "max_y": 3, "min_x": 4, "max_x": 4,
                                 "bbox_h": 1, "bbox_w": 1}
    rect = np.zeros((100, 120), dtype=np.uint8)
    rect[10:30, 40:80] = 1
    box = C.bbox_of(rect)
    assert (box["min_y"], box["max_y"], box["min_x"], box["max_x"]) == (10, 29, 40, 79)
    assert (box["bbox_h"], box["bbox_w"]) == (20, 40)


def test_expanded_roi_preserves_centre_and_reports_clipping():
    rect = np.zeros((100, 120), dtype=np.uint8)
    rect[10:30, 40:80] = 1
    roi = C.expanded_roi_box(C.bbox_of(rect), (100, 120))
    assert (roi["expanded_h"], roi["expanded_w"]) == (30, 60)
    assert roi["expansion_factor"] == (1.5, 1.5)
    assert roi["clipped"] is False
    assert (roi["y0"] + roi["y1"]) / 2 == (10 + 29) / 2
    assert (roi["x0"] + roi["x1"]) / 2 == (40 + 79) / 2

    edge = np.zeros((100, 120), dtype=np.uint8)
    edge[0:20, 0:40] = 1
    clipped = C.expanded_roi_box(C.bbox_of(edge), (100, 120))
    assert clipped["clipped"] is True and clipped["y0"] == 0 and clipped["x0"] == 0
    assert clipped["y1"] <= 99 and clipped["x1"] <= 119
    assert clipped["roi_h"] == clipped["y1"] - clipped["y0"] + 1
    assert clipped["roi_w"] == clipped["x1"] - clipped["x0"] + 1


def test_square_pad_box_is_square_in_bounds_and_clamps_on_small_images():
    rect = np.zeros((100, 120), dtype=np.uint8)
    rect[10:30, 40:80] = 1
    roi = C.expanded_roi_box(C.bbox_of(rect), (100, 120))
    sq = C.square_pad_box(roi, (100, 120))
    assert sq["y1"] - sq["y0"] + 1 == sq["side"] == sq["x1"] - sq["x0"] + 1
    assert sq["fully_in_bounds"] is True
    assert sq["side"] == max(roi["roi_h"], roi["roi_w"])

    # Edge case: a narrow image forces clamping to min(H, W) but must stay square.
    tall = np.zeros((197, 40), dtype=np.uint8)
    tall[20:80, 5:35] = 1
    roi_tall = C.expanded_roi_box(C.bbox_of(tall), (197, 40))
    sq_tall = C.square_pad_box(roi_tall, (197, 40))
    assert sq_tall["side"] == 40
    assert sq_tall["y1"] - sq_tall["y0"] + 1 == 40 == sq_tall["x1"] - sq_tall["x0"] + 1
    assert sq_tall["fully_in_bounds"] is True
    assert sq_tall["clamped_to_image_min_side"] is True


# --------------------------------------------------------------------------- #
# Gap / resource / heterogeneity statistics
# --------------------------------------------------------------------------- #
def test_mac_scaling_is_exactly_quadratic():
    base = RES.GLOBAL_MACS_512
    assert RES._mac_scaling(512) == base
    assert RES._mac_scaling(1024) == pytest.approx(4 * base)
    assert RES._mac_scaling(256) == pytest.approx(base / 4)
    assert RES._mac_scaling(768) == pytest.approx(base * 2.25)


def test_gini_safe_corr_and_macro_dice_on_known_synthetic_values():
    assert BEN._gini(np.array([])) == 0.0
    assert BEN._gini(np.zeros(5)) == 0.0
    assert BEN._gini(np.ones(4)) == pytest.approx(0.0)
    assert BEN._gini(np.array([0.0, 0.0, 0.0, 1.0])) == pytest.approx(0.75)
    assert BEN._gini(np.array([-1.0, 0.0, 0.0, 3.0])) == pytest.approx(0.75)

    assert KUB._safe_corr([1, 2, 3], [2, 4, 6]) == pytest.approx(1.0)
    assert np.isnan(KUB._safe_corr([1, 2], [2, 4]))
    assert np.isnan(KUB._safe_corr([1, 1, 1], [1, 2, 3]))
    assert KUB._safe_corr([1, 2, 3, np.nan], [2, 4, 6, 999]) == pytest.approx(1.0)

    rows = [
        {"dataset": "ISIC", "dice": 1.0}, {"dataset": "ISIC", "dice": 0.0},
        {"dataset": "BUSI", "dice": 0.5},
        {"dataset": "KVASIR", "dice": 0.25}, {"dataset": "KVASIR", "dice": 0.75},
        {"dataset": "KUB", "dice": 1.0},
    ]
    macro, per_domain = C.macro_domain_dice(rows)
    assert per_domain == {"ISIC": 0.5, "BUSI": 0.5, "KVASIR": 0.5, "KUB": 1.0}
    assert macro == pytest.approx((0.5 + 0.5 + 0.5 + 1.0) / 4)
    absent, per_absent = C.macro_domain_dice([{"dataset": "KUB", "dice": 0.4}])
    assert absent == pytest.approx(0.4) and per_absent == {"KUB": 0.4}
    assert np.isnan(C.macro_domain_dice([])[0])


def test_paired_domain_stratified_bootstrap_is_reproducible_and_paired():
    a = np.array([0.10, 0.20, 0.30, 0.40])
    b = np.array([0.00, 0.10, 0.20, 0.30])
    domains = np.array(["ISIC", "ISIC", "BUSI", "BUSI"])
    first = C.paired_domain_stratified_bootstrap(a, b, domains, n_boot=200, seed=42)
    second = C.paired_domain_stratified_bootstrap(a, b, domains, n_boot=200, seed=42)
    assert first == second
    assert first["delta"] == pytest.approx(0.10)
    assert first["n_strata"] == 2 and first["paired"] and first["domain_stratified"]
    assert first["n_boot"] == 200 and first["seed"] == 42
    assert first["ci_low"] <= first["delta"] <= first["ci_high"]
    assert first["ci_excludes_zero"] is True
    with pytest.raises(ValueError, match="identically shaped"):
        C.paired_domain_stratified_bootstrap(a, b[:3], domains, n_boot=10)


def test_test_access_guard_refuses_test_resembling_paths():
    for path in ("manifests/phase4_v3/test.csv", "external_test_ds/sample.png",
                 "/data/test/image.png", "datasets\\test\\mask.png"):
        with pytest.raises(RuntimeError, match="TEST-resembling"):
            C.assert_no_test_path(path)
    C.assert_no_test_path("manifests/phase4_v3/val.csv")
    C.assert_no_test_path("reports/tables/phase22_scale_sensitivity.csv")


# --------------------------------------------------------------------------- #
# Read-only consistency against EXISTING frozen historical records.
# These are not new experiments: no value is recomputed from real data.
# --------------------------------------------------------------------------- #
def test_frozen_historical_records_agree_with_code_constants():
    audits = ROOT / "reports" / "audits"
    scale = json.loads((audits / "phase22_scale_sensitivity.json").read_text(encoding="utf-8"))
    gap = json.loads((audits / "phase22_resource_gap.json").read_text(encoding="utf-8"))
    rule = json.loads((audits / "phase22_threshold_rule_audit.json").read_text(encoding="utf-8"))

    assert list(scale["sizes_probed"]) == list(C.SUPPORTED_SIZES)
    assert scale["canonical_reference_size"] == C.CANONICAL_SIZE == 512
    assert scale["threshold"] == C.THRESHOLD == 0.5
    assert scale["training_jobs_started"] == 0 and scale["inference_only"] is True
    assert scale["no_threshold_tuning"] is True
    assert scale["decision_rule"]["rule"] == "pred = (float32(prob) >= 0.5)"
    assert rule["decision"]["adopted_rule"] == "pred = (float32(prob) >= 0.5)"
    assert rule["test_reads"] == 0 and rule["inference_performed"] is False
    assert gap["reference_params"] == 3_523_001
    assert gap["reference_gmacs_at_512"] == pytest.approx(
        RES.GLOBAL_MACS_512 / 1e9, abs=1e-4)
    assert gap["test_reads"] == 0 and gap["no_optimisation_performed"] is True

    # The declared rule is the one this module actually implements.
    np.testing.assert_array_equal(
        C.threshold_probability(np.array([0.4999, 0.5], dtype=np.float32)),
        np.array([0, 1], dtype=np.uint8))


def test_frozen_phase22_source_bytes_match_the_historical_pin():
    """Existing frozen audit pins the exact source bytes; no source drift."""
    audit = json.loads((ROOT / "reports" / "audits" /
                        "phase22_no_new_training_audit.json").read_text(encoding="utf-8"))
    per_file = audit["static_scan"]["per_file"]
    assert audit["static_scan"]["total_forbidden_construct_hits"] == 0
    for relative in ("src/analysis/phase22_common.py", "src/analysis/phase22_scale.py"):
        expected = per_file[relative]["sha256"]
        observed = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        assert observed == expected, f"source drift in {relative}"


def test_frozen_input_contract_is_unchanged():
    """The frozen Phase-22 input contract is preserved; evidence is synthetic only."""
    assert EVIDENCE_CLASS == "SYNTHETIC_TEST_ONLY"
    assert C.PHASE == 22
    assert C.MANIFEST_VERSION == "phase4_v3"
    assert C.CANONICAL_SIZE == 512 and C.THRESHOLD == 0.5
    assert C.CHANNEL_POLICY == "RGB_3CH"
    assert C.ORACLE_ROI_MARGIN == C.PRED_ROI_MARGIN == 0.25
    assert C.TASK_ID == {"ISIC": 0, "BUSI": 1, "KVASIR": 2, "KUB": 3}
    assert C.DATASET_ORDER == ["ISIC", "BUSI", "KVASIR", "KUB"]
    assert list(C.SCALE_PROBE_SIZES) == [256, 768, 1024]
