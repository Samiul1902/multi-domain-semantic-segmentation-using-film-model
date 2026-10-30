"""Unit tests for src/metrics/evaluation_metrics.py.

Covers the edge cases required by the project-wide evaluation-metrics audit:
perfect / all-background / all-foreground prediction, all empty-mask
combinations, single-pixel objects, highly imbalanced masks, identical and
disjoint masks, plus reference cross-checks against scipy/sklearn-style
definitions implemented independently in the test.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.metrics.evaluation_metrics import (  # noqa: E402
    assd, average_precision, balanced_accuracy, binary_confusion_counts, bootstrap_ci,
    brier_score, cohen_kappa, component_detection_metrics, dice, expected_calibration_error,
    hd95, iou, mcc, paired_bootstrap_ci, pooled_segmentation_metrics, precision, recall,
    roc_auc, segmentation_metrics, specificity, surface_dice,
)

F = np.zeros((8, 8), dtype=np.uint8)
T = np.ones((8, 8), dtype=np.uint8)
BLOCK = np.zeros((8, 8), dtype=np.uint8)
BLOCK[2:6, 2:6] = 1
BLOCK_SHIFT = np.zeros((8, 8), dtype=np.uint8)
BLOCK_SHIFT[3:7, 2:6] = 1


def test_confusion_counts_basic():
    c = binary_confusion_counts(BLOCK, BLOCK)
    assert c["tp"] == 16 and c["fp"] == 0 and c["fn"] == 0 and c["tn"] == 48
    assert c["total"] == 64


def test_perfect_prediction():
    m = segmentation_metrics(BLOCK, BLOCK)
    assert m["dice"] == pytest.approx(1.0)
    assert m["iou"] == pytest.approx(1.0)
    assert m["precision"] == pytest.approx(1.0)
    assert m["recall"] == pytest.approx(1.0)
    assert m["mcc"] == pytest.approx(1.0)
    assert m["cohen_kappa"] == pytest.approx(1.0)
    assert m["empty_case"] == "both_nonempty"


def test_all_background_prediction():
    m = segmentation_metrics(F, BLOCK)
    assert m["empty_case"] == "gt_nonempty_pred_empty"
    assert m["dice"] == 0.0 and m["recall"] == 0.0 and m["fnr"] == pytest.approx(1.0)
    assert m["specificity"] == pytest.approx(1.0)
    assert np.isnan(m["precision"])  # undefined without predicted positives
    assert "precision" in m["undefined"]


def test_all_foreground_prediction():
    m = segmentation_metrics(T, BLOCK)
    assert m["empty_case"] == "both_nonempty"
    assert m["recall"] == pytest.approx(1.0)
    assert m["precision"] == pytest.approx(16 / 64)
    assert m["dice"] == pytest.approx(2 * 16 / (2 * 16 + 48 + 0))


def test_both_empty():
    m = segmentation_metrics(F, F)
    assert m["empty_case"] == "gt_empty_pred_empty"
    assert m["dice"] == 1.0 and m["specificity"] == 1.0
    assert np.isnan(hd95(F, F)["hd95"])
    assert hd95(F, F)["valid"] is False


def test_gt_empty_pred_nonempty():
    m = segmentation_metrics(BLOCK, F)
    assert m["empty_case"] == "gt_empty_pred_nonempty"
    assert m["dice"] == 0.0 and m["fpr"] == pytest.approx(1.0)
    assert np.isnan(m["recall"]) and "recall" in m["undefined"]
    assert np.isnan(surface_dice(BLOCK, F)["surface_dice"])


def test_gt_nonempty_pred_empty():
    m = segmentation_metrics(F, BLOCK)
    assert m["dice"] == 0.0 and m["fnr"] == pytest.approx(1.0)
    assert np.isnan(m["precision"])
    assert np.isnan(assd(F, BLOCK)["assd"])


def test_single_pixel_object():
    p = np.zeros((5, 5), dtype=np.uint8)
    g = np.zeros((5, 5), dtype=np.uint8)
    p[2, 2] = 1
    g[2, 2] = 1
    m = segmentation_metrics(p, g)
    assert m["tp"] == 1 and m["dice"] == pytest.approx(1.0)
    assert hd95(p, g)["hd95"] == pytest.approx(0.0)


def test_highly_imbalanced_mask():
    p = np.zeros((100, 100), dtype=np.uint8)
    g = np.zeros((100, 100), dtype=np.uint8)
    g[10:12, 10:12] = 1  # 4 foreground pixels of 10000
    p[90, 90] = 1        # one foreground pixel, nowhere near the target
    m = segmentation_metrics(p, g)
    # Accuracy is misleadingly high despite zero overlap.
    assert m["accuracy"] > 0.99
    assert m["dice"] == pytest.approx(0.0, abs=1e-6)
    assert m["mcc"] < 0.0  # negative because prediction is anti-correlated


def test_disjoint_masks():
    p = np.zeros((8, 8), dtype=np.uint8)
    g = np.zeros((8, 8), dtype=np.uint8)
    p[0:2, 0:2] = 1
    g[6:8, 6:8] = 1
    m = segmentation_metrics(p, g)
    # The project convention adds a 1e-7 epsilon, so disjoint masks give ~0, not exactly 0.
    assert m["dice"] == pytest.approx(0.0, abs=1e-6) and m["iou"] == pytest.approx(0.0, abs=1e-6)
    assert m["tp"] == 0 and m["fp"] == 4 and m["fn"] == 4


def test_identical_masks_hd95_zero():
    assert hd95(BLOCK, BLOCK)["hd95"] == pytest.approx(0.0)
    assert assd(BLOCK, BLOCK)["assd"] == pytest.approx(0.0)
    assert surface_dice(BLOCK, BLOCK, tolerance=1.0)["surface_dice"] == pytest.approx(1.0)


def test_boundary_shift_positive_distance():
    r = hd95(BLOCK, BLOCK_SHIFT)
    assert r["valid"] is True and r["hd95"] > 0.0
    assert r["unit"] == "pixel"
    assert assd(BLOCK, BLOCK_SHIFT)["assd"] > 0.0
    sd = surface_dice(BLOCK, BLOCK_SHIFT, tolerance=0.5)["surface_dice"]
    assert 0.0 < sd < 1.0


def test_mcc_and_kappa_reference():
    # 2x2 reference: tp=10, fp=5, fn=5, tn=80
    c = {"tp": 10, "tn": 80, "fp": 5, "fn": 5, "total": 100}
    num = 10 * 80 - 5 * 5
    den = np.sqrt((10 + 5) * (10 + 5) * (80 + 5) * (80 + 5))
    assert mcc(c) == pytest.approx(num / den)
    po = 0.90
    pe = ((10 + 5) * (10 + 5) + (80 + 5) * (80 + 5)) / 10000
    assert cohen_kappa(c) == pytest.approx((po - pe) / (1 - pe))
    assert balanced_accuracy(c) == pytest.approx(0.5 * (10 / 15 + 80 / 85))


def test_pooled_vs_image_level_separation():
    confusions = [binary_confusion_counts(BLOCK, BLOCK), binary_confusion_counts(F, BLOCK)]
    pooled = pooled_segmentation_metrics(confusions)
    assert pooled["tp"] == 16 and pooled["fn"] == 16
    assert pooled["metric_domain"] == "PIXEL_SEGMENTATION_POOLED"
    assert 0.0 < pooled["dice"] < 1.0


def test_roc_auc_reference():
    y = np.array([0, 0, 1, 1], dtype=float)
    p = np.array([0.1, 0.4, 0.35, 0.8], dtype=float)
    # Exact rank-based AUC for this example is 0.75.
    assert roc_auc(y, p, n_bins=4096) == pytest.approx(0.75, abs=0.02)
    assert roc_auc(y, y, n_bins=4096) == pytest.approx(1.0, abs=0.02)


def test_average_precision_perfect():
    y = np.array([0.0, 0.0, 1.0, 1.0])
    p = np.array([0.01, 0.02, 0.9, 0.95])
    assert average_precision(y, p, n_bins=1024) == pytest.approx(1.0, abs=1e-3)


def test_calibration_metrics():
    y = np.array([0, 0, 1, 1], dtype=float)
    p = np.array([0.0, 0.0, 1.0, 1.0], dtype=float)
    assert brier_score(y, p) == pytest.approx(0.0)
    assert expected_calibration_error(y, p, n_bins=10) == pytest.approx(0.0)
    p_bad = np.array([0.9, 0.9, 0.9, 0.9])
    assert brier_score(y, p_bad) == pytest.approx(0.41)
    assert expected_calibration_error(y, p_bad, n_bins=10) > 0.0


def test_component_detection_metrics():
    labeled = np.zeros((10, 10), dtype=np.int32)
    labeled[1:3, 1:3] = 1
    labeled[6:8, 6:8] = 2
    pred = np.zeros((10, 10), dtype=np.uint8)
    pred[1:3, 1:3] = 1  # detects component 1 only
    r = component_detection_metrics(labeled, pred, size_labels={1: "TINY", 2: "SMALL"})
    assert r["gt_components"] == 2 and r["tp_components"] == 1 and r["fn_components"] == 1
    assert r["fp_components"] == 0
    assert r["component_recall"] == pytest.approx(0.5)
    assert r["component_precision"] == pytest.approx(1.0)
    assert r["tn_defined"] is False
    assert r["per_size"]["TINY"]["detected"] == 1
    assert r["per_size"]["SMALL"]["detected"] == 0


def test_bootstrap_determinism_and_paired():
    vals = [0.5, 0.6, 0.7, 0.8, 0.9]
    a = bootstrap_ci(vals, n_boot=500, seed=7)
    b = bootstrap_ci(vals, n_boot=500, seed=7)
    assert a == b
    assert a["ci_low"] <= a["estimate"] <= a["ci_high"]
    assert a["resampling_unit"] == "image" and a["seed"] == 7

    x = [0.8, 0.7, 0.9, 0.6]
    y = [0.5, 0.5, 0.6, 0.4]
    pb = paired_bootstrap_ci(x, y, n_boot=500, seed=3)
    assert pb["mean_difference"] == pytest.approx(np.mean(np.array(x) - np.array(y)))
    assert pb["ci_low"] <= pb["mean_difference"] <= pb["ci_high"]


def test_shape_mismatch_raises():
    with pytest.raises(ValueError):
        binary_confusion_counts(np.zeros((4, 4)), np.zeros((5, 5)))
    with pytest.raises(ValueError):
        paired_bootstrap_ci([1.0, 2.0], [1.0])
