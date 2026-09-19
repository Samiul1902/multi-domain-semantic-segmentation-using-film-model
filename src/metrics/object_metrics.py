"""Explicit 8-connected object metrics using overlap-based matching."""
import numpy as np
from scipy.ndimage import label


def object_metrics(prediction, target, minimum_overlap_pixels=1):
    structure=np.ones((3,3), dtype=int)
    pred_labels,n_pred=label(np.asarray(prediction)>0, structure)
    gt_labels,n_gt=label(np.asarray(target)>0, structure)
    detected=0; matched_pred=set()
    for gt_id in range(1,n_gt+1):
        overlapping=np.unique(pred_labels[gt_labels==gt_id]); overlapping=overlapping[overlapping>0]
        valid=[pid for pid in overlapping if np.sum((pred_labels==pid)&(gt_labels==gt_id))>=minimum_overlap_pixels]
        if valid: detected+=1; matched_pred.update(valid)
    missed=n_gt-detected; false_positive=n_pred-len(matched_pred)
    recall=detected/n_gt if n_gt else float("nan")
    return {"gt_component_count":n_gt,"predicted_component_count":n_pred,"detected_gt_components":detected,
            "missed_gt_components":missed,"object_recall":recall,"missed_object_rate":1-recall if n_gt else float("nan"),
            "false_positive_predicted_components":false_positive,"connectivity":8,"minimum_overlap_pixels":minimum_overlap_pixels}
