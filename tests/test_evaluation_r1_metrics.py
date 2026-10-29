"""Analytical tests on fabricated arrays only."""
import numpy as np
import pytest
from sklearn.metrics import confusion_matrix
from src.research.evaluation_r1.metrics import binary_metrics, multiclass_metrics, surface_metrics, c1_compatibility


def test_confusion_and_overlap():
    p = np.array([[1, 1], [0, 0]])
    g = np.array([[1, 0], [1, 0]])
    m = binary_metrics(p, g)
    tn, fp, fn, tp = confusion_matrix(g.ravel(), p.ravel(), labels=[0, 1]).ravel()
    assert (m["tn"], m["fp"], m["fn"], m["tp"]) == (tn, fp, fn, tp) == (1, 1, 1, 1)
    assert m["dice"] == .5 and m["iou"] == pytest.approx(1/3)
    assert m["precision"] == m["recall"] == m["specificity"] == m["npv"] == m["balanced_accuracy"] == .5
    assert m["relative_area_error"] == 0


@pytest.mark.parametrize("p,g,dice,case", [([0,0],[0,0],1,"both_empty"), ([1,0],[0,0],0,"reference_empty"), ([0,0],[1,0],0,"prediction_empty"), ([0,1],[1,0],0,"both_nonempty"), ([1,0],[1,0],1,"both_nonempty")])
def test_empty_and_wrong(p, g, dice, case):
    m = binary_metrics(np.array([p]), np.array([g]))
    assert m["dice"] == dice and m["empty_case"] == case
    if case == "both_empty":
        assert m["precision"] is None and m["recall"] is None and m["relative_area_error"] is None


def test_imbalance_and_disconnected():
    g = np.zeros((20, 20), dtype=int); g[0, 0] = g[19, 19] = 1
    p = g.copy(); p[19, 19] = 0; p[10, 10] = 1
    m = binary_metrics(p, g)
    assert (m["tp"], m["fp"], m["fn"], m["tn"]) == (1, 1, 1, 397)
    assert m["dice"] == .5 and m["specificity"] == pytest.approx(397/398)


def test_surface_anisotropic_and_empty():
    p = np.zeros((4,4), int); g = p.copy(); p[1,1] = 1; g[2,1] = 1
    m = surface_metrics(p, g, (2, 1), tolerance=1)
    assert m["unit"] == "mm" and m["hd95"] == m["hausdorff"] == m["assd"] == 2
    assert m["surface_dice"] == m["surface_precision"] == m["surface_recall"] == 0
    assert surface_metrics(p, p, tolerance=0)["surface_dice"] == 1
    assert surface_metrics(p, np.zeros_like(p))["hd95"] is None
    assert surface_metrics(p, g)["unit"] == "pixel"
    with pytest.raises(ValueError): surface_metrics(p, g, (0, 1))


def test_touching_boundaries():
    p = np.array([[1,1,0],[1,1,0],[0,0,0]])
    g = np.array([[0,1,1],[0,1,1],[0,0,0]])
    m = surface_metrics(p, g, tolerance=0)
    assert m["surface_precision"] == .5 and m["surface_recall"] == .5
    assert m["assd"] == .5 and m["hausdorff"] == 1


def test_multiclass():
    p = np.array([[0, 1, 2, 2]]); g = np.array([[0, 1, 1, 2]])
    m = multiclass_metrics(p, g, [0,1,2])
    assert m["per_class"][1]["dice"] == pytest.approx(2/3)
    assert m["per_class"][2]["iou"] == .5
    assert m["micro_dice"] == .75 and m["micro_iou"] == .6
    assert m["weighted_dice"] == pytest.approx((1 + 2*(2/3) + 2/3)/4)
    with pytest.raises(ValueError): multiclass_metrics(p, g, [0,1])


def test_c1_against_frozen_helper():
    import torch
    from scripts.training.phase21_common import per_image_dice_iou_precision_recall
    logits = torch.tensor([[[[0., -2.], [2., 0.]]]])
    gt = torch.tensor([[[[1., 1.], [0., 0.]]]])
    ref = per_image_dice_iou_precision_recall(logits, gt, .5)
    got = c1_compatibility(torch.sigmoid(logits).numpy()[0,0], gt.numpy()[0,0])
    assert got["dice"] == ref["dice"].item() and got["iou"] == ref["iou"].item()
    assert c1_compatibility(np.zeros((1,1)), np.zeros((1,1)))["dice"] == 1


@pytest.mark.parametrize("bad", [np.nan, np.inf, -1, 2])
def test_invalid_inputs(bad):
    with pytest.raises(ValueError): binary_metrics(np.array([[bad]]), np.array([[0]]))
    with pytest.raises(ValueError): c1_compatibility(np.array([[bad]]), np.array([[0]]))


def test_invalid_shapes():
    with pytest.raises(ValueError): binary_metrics(np.zeros((2,2)), np.zeros((1,2)))
    with pytest.raises(ValueError): surface_metrics(np.zeros((1,2,2)), np.zeros((1,2,2)))
