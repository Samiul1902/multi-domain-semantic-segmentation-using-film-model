"""Phase39 frozen per-sample inference (v1.1) — imports v1.1 constants only.

Identical scientific semantics to v1.0 (scientific_delta = 0); the only change
is the constants module reference (v1_1).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

import scripts.analysis.phase39_final_test_common_v1_1 as C


def _global_probability(models, image_tensor):
    import torch
    g = models["G"]
    with torch.no_grad(), torch.autocast(device_type="cuda", dtype=torch.float16, enabled=True):
        logits = g(image_tensor)
    p = torch.sigmoid(logits.float())
    p_f16 = p.half()
    return p_f16.float().cpu().numpy()


def evaluate_sample(models, device, row, counters) -> dict:
    import torch
    from PIL import Image, ImageOps
    from src.data.transforms import SegmentationTransform
    from src.data.barr_roi import roi_geometry
    from src.models.barr.ra_medfilm_barr import canonical_utility, TAU_C8_FINAL_FLOAT
    from src.metrics import evaluation_metrics as M

    sid = str(row.get("sample_id", row.get("id", "")))
    domain = str(row.get("domain", ""))
    task_id = int(row.get("task_id", row.get("task", -1)))

    img_path = C.ROOT / str(row.get("image_path", row.get("image", "")))
    gt_path = C.ROOT / str(row.get("mask_path", row.get("mask", "")))
    img = ImageOps.exif_transpose(Image.open(img_path).convert("RGB"))
    gt = Image.open(gt_path).convert("L")
    counters["test_image_reads"] += 1
    counters["test_gt_reads"] += 1

    tf = SegmentationTransform(size=C.G_INPUT_SHAPE[1], train=False)
    x = tf(image=img, mask=gt)
    image_tensor = (x["image"] if isinstance(x, dict) else x[0]).unsqueeze(0).to(device)
    gt_np = (np.asarray(gt) > 0).astype(np.uint8)

    p_global = _global_probability(models, image_tensor)[0]
    counters["model_forwards"] += 1

    geom = roi_geometry(p_global, threshold=C.ROI_P_GLOBAL_THRESHOLD,
                        margin=C.ROI_MARGIN, expansion=C.ROI_EXPANSION,
                        canvas=C.ROI_CANVAS, crop=C.ROI_CROP)
    if geom.get("empty", False):
        state = "FORCED_SKIP"
        final_binary = (p_global >= C.SEGMENTATION_THRESHOLD).astype(np.uint8)
    else:
        utility = canonical_utility(float(geom.get("delta_hat", 0.0)))
        if utility < float(TAU_C8_FINAL_FLOAT):
            state = "SKIP_GLOBAL"
            final_binary = (p_global >= C.SEGMENTATION_THRESHOLD).astype(np.uint8)
        else:
            refined = models["R_psi"](image_tensor)
            accept = bool(models["S_omega"].accept(float(geom.get("s_omega_score", 0.0)),
                                                   C.S_OMEGA_ACCEPT_THRESHOLD))
            counters["model_forwards"] += 2
            fused = _fuse_full_field(p_global, refined, geom)
            state = "EXECUTE_THEN_ACCEPT" if accept else "EXECUTE_THEN_REJECT"
            source = fused if accept else p_global
            final_binary = (source >= C.SEGMENTATION_THRESHOLD).astype(np.uint8)

    counters["metric_evaluations"] += 1
    cm = _confusion(final_binary, gt_np)
    dice = float(M.dice(cm))
    iou = float(M.iou(cm))
    hd = M.hd95(final_binary, gt_np) if hasattr(M, "hd95") else {"hd95": float("nan"), "valid": False}
    return {"sample_id": sid, "domain": domain, "task_id": task_id,
            "dice": dice, "iou": iou,
            "hd95": float(hd.get("hd95", float("nan"))),
            "hd95_valid": bool(hd.get("valid", False)),
            "state_machine_branch": state}


def _confusion(pred, gt):
    tp = int(np.logical_and(pred == 1, gt == 1).sum())
    fp = int(np.logical_and(pred == 1, gt == 0).sum())
    fn = int(np.logical_and(pred == 0, gt == 1).sum())
    tn = int(np.logical_and(pred == 0, gt == 0).sum())
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn}


def _fuse_full_field(p_global, refined, geom):
    """Canonical D61 pad-aware fuse_full_field (frozen)."""
    from scripts.analysis import phase36_robustness_execution_v1_23 as _FROZEN_MOD
    if hasattr(_FROZEN_MOD, "fuse_full_field"):
        return _FROZEN_MOD.fuse_full_field(p_global, refined, geom)
    return np.asarray(p_global, dtype=np.float32)
