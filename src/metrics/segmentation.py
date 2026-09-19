"""Binary pixel metrics and HD95 with explicit empty-prediction handling."""
import numpy as np
import torch
from scipy.ndimage import binary_erosion, distance_transform_edt


def binary_metrics(logits, targets, threshold=0.5, epsilon=1e-7):
    predictions = torch.sigmoid(logits).ge(threshold)
    targets = targets.bool()
    dims = tuple(range(1, targets.ndim))
    tp=(predictions & targets).sum(dims).float(); fp=(predictions & ~targets).sum(dims).float()
    fn=(~predictions & targets).sum(dims).float()
    dice=(2*tp+epsilon)/(2*tp+fp+fn+epsilon); iou=(tp+epsilon)/(tp+fp+fn+epsilon)
    precision=(tp+epsilon)/(tp+fp+epsilon); recall=(tp+epsilon)/(tp+fn+epsilon)
    return {"dice":dice, "iou":iou, "precision":precision, "recall":recall}


def aggregate_binary_metrics(metric_batches):
    return {key: torch.cat([batch[key] for batch in metric_batches]).mean().item()
            for key in metric_batches[0]}


def hd95(prediction, target, empty_prediction_penalty=None):
    """95th percentile symmetric surface distance, 8-connected boundaries.

    A non-empty GT with empty prediction returns hd95_valid=False and either NaN
    or the explicitly supplied finite penalty; it never returns zero.
    """
    pred=np.asarray(prediction, dtype=bool); gt=np.asarray(target, dtype=bool)
    if not pred.any():
        return {"hd95": float("nan") if empty_prediction_penalty is None else float(empty_prediction_penalty),
                "hd95_valid": False, "empty_prediction": True,
                "invalid_reason": "both_empty" if not gt.any() else "empty_prediction"}
    if not gt.any():
        return {"hd95": float("nan"), "hd95_valid": False, "empty_prediction": False,
                "invalid_reason": "empty_ground_truth"}
    structure=np.ones((3,3), dtype=bool)
    ps=pred ^ binary_erosion(pred, structure=structure); gs=gt ^ binary_erosion(gt, structure=structure)
    d_gt=distance_transform_edt(~gs); d_pred=distance_transform_edt(~ps)
    distances=np.concatenate([d_gt[ps], d_pred[gs]])
    return {"hd95": float(np.percentile(distances,95)), "hd95_valid": True,
            "empty_prediction": False, "invalid_reason": ""}
