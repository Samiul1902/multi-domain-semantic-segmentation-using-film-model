"""Project-wide evaluation-metrics DESCRIPTIVE BACKFILL (single safe VAL replay).

Purpose
-------
The KUB evaluation pipeline persisted only aggregate metrics and
per-image / per-component tables. It never persisted pixel masks or probability
maps, so pixel confusion matrices, boundary metrics (HD95/ASSD/surface Dice) and
calibration metrics were NOT derivable from saved artifacts.

This script performs exactly ONE deterministic VAL-only replay to generate those
missing DESCRIPTIVE metrics for four arms on the canonical clean-v3 FULL_FIELD
VAL population (103 images):

    GLOBAL              : Phase-10 UNet++ (epoch 70)
    ORACLE_REGIONAL     : GT-bbox proposals + Phase-14 refiner
    PREDICTED_REGIONAL  : Phase-13B localizer (frozen 512 construction) + refiner
    H3_DOWNSTREAM       : H3 localizer (epoch 54, 128 heatmap) + refiner

SAFE REPLAY RULE — all eight conditions are checked and recorded:
  1. exact checkpoint frozen + SHA verified        -> checked below
  2. exact evaluator/preprocessing frozen          -> reuses the frozen modules verbatim
  3. no TEST access                                -> test_lock verified
  4. no threshold search                           -> fixed frozen policy only
  5. strictly to generate missing DESCRIPTIVE metrics
  6. existing primary metrics reproduced first     -> hard reproduction gate below
  7. replay does not change frozen decisions       -> writes only new artifacts
  8. replay explicitly logged                      -> project_evaluation_metrics_backfill.json

NOTHING frozen is modified. No gate, threshold, checkpoint or decision changes.

Usage (from project root):
    python scripts/evaluation/project_evaluation_metrics_backfill.py
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from PIL import Image
import torch
from scipy.ndimage import label as _label

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.analysis.oracle_roi import extract_gt_components
from src.data.regional_dataset import crop_and_preprocess
from src.data.transforms import SegmentationTransform
from src.inference.kub_predict import _preprocess_image, _restore_original_coordinates
from src.inference.predicted_roi import apply_context_margin, generate_predicted_rois
from src.inference.regional_evaluator import aggregate_and_fuse, restore_regional_probability
from src.inference.learned_roi_clean_v3 import build_clean_v3_localizer, HEATMAP_RESOLUTION
from src.metrics.evaluation_metrics import (
    binary_confusion_counts, bootstrap_ci, component_detection_metrics, dice, hd95, assd,
    surface_dice, expected_calibration_error, maximum_calibration_error, brier_score,
    roc_auc, average_precision, paired_bootstrap_ci, iou, precision, recall, specificity,
    npv, accuracy, balanced_accuracy, mcc, cohen_kappa, false_positive_rate, false_negative_rate,
)
from src.models.factory import create_model
from src.models.unet import UNet
from src.utils.checkpointing import load_training_checkpoint
from src.utils.manifest_guard import validate_manifest_version_strict
from src.utils.test_lock import verify_test_lock

AUDITS = PROJECT_ROOT / "reports" / "audits"
TABLES = PROJECT_ROOT / "reports" / "tables"

GLOBAL_CKPT = PROJECT_ROOT / "checkpoints" / "phase10_kub_unetpp_seed42_512_clean_v3" / "best.pt"
GLOBAL_SHA = "ec7eb13f32e43af27eab7fc617bd1a2a8fcce1d6651a1b4a3653f3e4d1283269"
P13B_CKPT = PROJECT_ROOT / "checkpoints" / "phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_clean_v3" / "best.pt"
P13B_SHA = "7673c34a2f2c86eca2e45c1bc6abe77842d17cd09f122f2da0f2d414ca492273"
REFINER_CKPT = PROJECT_ROOT / "checkpoints" / "phase14_kub_refiner_unet_a3_256_seed42_clean_v3" / "best.pt"
REFINER_SHA = "2e09e3a9c39c731687db1a9fef0c80881ed6235e4cda070bb4b8b382caa45daa"
H3_CKPT = PROJECT_ROOT / "checkpoints" / "h3_kub_localizer_sigma_adaptive_sizeaware_seed42_clean_v3" / "best.pt"
H3_SHA = "d875cac7d09bbc3d32232191f0af2c138e5a74682fc63e4d6e01f30345eca75e"

POLICY = {"threshold": 0.10, "margin": 0.20, "top_k": 5, "nms_iou": 0.30}
GLOBAL_THRESHOLD = 0.50
FUSION_THRESHOLD = 0.50
SURFACE_TOLERANCE_PX = 2.0
BOUNDARY_CROP_MARGIN = 256
CALIB_BINS = 256  # frozen restore quantizes probabilities to 1/255 levels

VAL_SAMPLES = TABLES / "kub_val_samples_sized_clean_v3.csv"
VAL_COMPONENTS = TABLES / "kub_val_components_sized_clean_v3.csv"

# ── Reproduction gate references (frozen primary metrics) ───────────────────
REFERENCE_DICE = {
    "GLOBAL": 0.6359172411726776,
    "ORACLE_REGIONAL": 0.8024158112932394,
    "PREDICTED_REGIONAL": 0.4185309062818487,
    "H3_DOWNSTREAM": 0.38862753520437243,
}
REFERENCE_TINY_DET = {
    "GLOBAL": 57 / 72,
    "PREDICTED_REGIONAL": 57 / 72,
    "ORACLE_REGIONAL": 1.0,
    "H3_DOWNSTREAM": 59 / 72,
}
REPRO_TOL = 1e-6


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


class CalibrationAccumulator:
    """Streaming (score, label) histogram for calibration + ROC/PR curves."""

    def __init__(self, n_bins: int = CALIB_BINS):
        self.n_bins = n_bins
        self.edges = np.linspace(0.0, 1.0, n_bins + 1)
        self.pos = np.zeros(n_bins, dtype=np.float64)
        self.neg = np.zeros(n_bins, dtype=np.float64)
        self.sum_pos = np.zeros(n_bins, dtype=np.float64)
        self.sum_neg = np.zeros(n_bins, dtype=np.float64)
        self.brier_sum = 0.0
        self.n_pixels = 0

    def update(self, prob: np.ndarray, gt: np.ndarray) -> None:
        p = np.asarray(prob, dtype=np.float64).ravel()
        y = (np.asarray(gt).ravel() > 0)
        idx = np.clip(np.digitize(p, self.edges[1:-1], right=False), 0, self.n_bins - 1)
        self.pos += np.bincount(idx[y], minlength=self.n_bins)
        self.neg += np.bincount(idx[~y], minlength=self.n_bins)
        self.sum_pos += np.bincount(idx[y], weights=p[y], minlength=self.n_bins)
        self.sum_neg += np.bincount(idx[~y], weights=p[~y], minlength=self.n_bins)
        self.brier_sum += float(np.sum((p - y.astype(np.float64)) ** 2))
        self.n_pixels += int(p.size)

    def summary(self) -> Dict[str, Any]:
        n = self.pos + self.neg
        conf = np.where(n > 0, (self.sum_pos + self.sum_neg) / np.maximum(n, 1e-12), np.nan)
        acc = np.where(n > 0, self.pos / np.maximum(n, 1e-12), np.nan)
        total = float(self.n_pixels) or 1.0
        valid = n > 0
        ece = float(np.sum((n[valid] / total) * np.abs(acc[valid] - conf[valid])))
        mce = float(np.max(np.abs(acc[valid] - conf[valid]))) if valid.any() else float("nan")

        total_pos = float(self.pos.sum()) or 1.0
        total_neg = float(self.neg.sum()) or 1.0
        tp_c = np.cumsum(self.pos[::-1]) / total_pos
        fp_c = np.cumsum(self.neg[::-1]) / total_neg
        fpr = np.concatenate([[0.0], fp_c])
        tpr = np.concatenate([[0.0], tp_c])
        trapz = getattr(np, "trapezoid", None) or np.trapz
        auc = float(trapz(tpr, fpr))
        tp_raw = np.cumsum(self.pos[::-1])
        fp_raw = np.cumsum(self.neg[::-1])
        rec = tp_raw / total_pos
        prec = np.where((tp_raw + fp_raw) > 0, tp_raw / np.maximum(tp_raw + fp_raw, 1e-12), 1.0)
        ap = 0.0
        prev = 0.0
        for r, p in zip(rec, prec):
            ap += max(0.0, r - prev) * p
            prev = r
        return {
            "brier": self.brier_sum / total,
            "ece": ece,
            "mce": mce,
            "roc_auc": auc,
            "average_precision": float(ap),
            "n_pixels": int(self.n_pixels),
            "n_bins": self.n_bins,
            "positive_fraction": float(self.pos.sum() / total),
            "reliability_bins": {
                "bin_count": n.astype(int).tolist(),
                "bin_confidence": [None if np.isnan(x) else float(x) for x in conf],
                "bin_accuracy": [None if np.isnan(x) else float(x) for x in acc],
            },
        }


def boundary_metrics_cropped(pred: np.ndarray, gt: np.ndarray) -> Dict[str, Any]:
    """HD95 / ASSD / surface Dice computed inside a padded union crop (exact here)."""
    p = pred > 0
    g = gt > 0
    if not p.any() or not g.any():
        r = hd95(p, g)
        return {"hd95": r["hd95"], "assd": float("nan"), "surface_dice": float("nan"),
                "valid": False, "reason": r["reason"], "unit": "pixel",
                "crop_margin_px": BOUNDARY_CROP_MARGIN}
    ys, xs = np.where(p | g)
    y0 = max(0, int(ys.min()) - BOUNDARY_CROP_MARGIN)
    y1 = min(p.shape[0], int(ys.max()) + BOUNDARY_CROP_MARGIN + 1)
    x0 = max(0, int(xs.min()) - BOUNDARY_CROP_MARGIN)
    x1 = min(p.shape[1], int(xs.max()) + BOUNDARY_CROP_MARGIN + 1)
    pc, gc = p[y0:y1, x0:x1], g[y0:y1, x0:x1]
    return {
        "hd95": hd95(pc, gc)["hd95"],
        "assd": assd(pc, gc)["assd"],
        "surface_dice": surface_dice(pc, gc, tolerance=SURFACE_TOLERANCE_PX)["surface_dice"],
        "valid": True, "reason": "", "unit": "pixel",
        "crop_margin_px": BOUNDARY_CROP_MARGIN,
        "surface_tolerance_px": SURFACE_TOLERANCE_PX,
    }


def main() -> Dict[str, Any]:
    t0 = time.time()
    validate_manifest_version_strict("phase4_v3")
    verify_test_lock(PROJECT_ROOT)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type != "cuda":
        raise RuntimeError("CUDA is required for the backfill replay.")

    # ── Safe-replay condition 1: checkpoint SHAs ────────────────────────────
    shas = {"global": sha256_file(GLOBAL_CKPT), "p13b": sha256_file(P13B_CKPT),
            "refiner": sha256_file(REFINER_CKPT), "h3": sha256_file(H3_CKPT)}
    assert shas["global"] == GLOBAL_SHA, shas["global"]
    assert shas["p13b"] == P13B_SHA, shas["p13b"]
    assert shas["refiner"] == REFINER_SHA, shas["refiner"]
    assert shas["h3"] == H3_SHA, shas["h3"]
    print("[backfill] All 4 checkpoint SHAs verified.")

    df_samples = pd.read_csv(VAL_SAMPLES)
    ff = df_samples[df_samples["view_type"] == "FULL_FIELD"].copy().reset_index(drop=True)
    assert len(ff) == 103
    df_comp = pd.read_csv(VAL_COMPONENTS)
    ff_comp = df_comp[df_comp["view_type"] == "FULL_FIELD"].copy().reset_index(drop=True)
    assert len(ff_comp) == 152

    # ── Load models ─────────────────────────────────────────────────────────
    global_model = create_model("unetpp", in_channels=1, out_channels=1, base_channels=32).to(device)
    load_training_checkpoint(GLOBAL_CKPT, global_model, restore_rng=False, map_location=device)
    global_model.eval()

    p13b_model = create_model("kub_localizer", in_channels=1, out_channels=1, base_channels=16).to(device)
    load_training_checkpoint(P13B_CKPT, p13b_model, restore_rng=False, map_location=device)
    p13b_model.eval()

    h3_model = build_clean_v3_localizer(device=device)
    assert getattr(h3_model, "heatmap_resolution", None) == HEATMAP_RESOLUTION
    load_training_checkpoint(H3_CKPT, h3_model, restore_rng=False, map_location=device)
    h3_model.eval()

    refiner = UNet(in_channels=1, out_channels=1, base_channels=32).to(device)
    load_training_checkpoint(REFINER_CKPT, refiner, restore_rng=False, map_location=device)
    refiner.eval()

    loc_transform = SegmentationTransform(512, False)
    ARMS = ["GLOBAL", "ORACLE_REGIONAL", "PREDICTED_REGIONAL", "H3_DOWNSTREAM"]

    per_image: List[Dict[str, Any]] = []
    per_component: List[Dict[str, Any]] = []
    calib = {a: CalibrationAccumulator() for a in ARMS}
    pooled_conf = {a: {"tp": 0, "tn": 0, "fp": 0, "fn": 0, "total": 0} for a in ARMS}
    comp_totals = {a: {"gt": 0, "detected": 0, "pred": 0, "fp": 0, "matched": 0} for a in ARMS}
    per_size_totals = {a: {} for a in ARMS}

    print("[backfill] Running single deterministic VAL replay over 103 FULL_FIELD images...")
    with torch.inference_mode():
        for idx, srow in ff.iterrows():
            sid = srow["sample_id"]
            img_path = Path(srow["image_path"])
            mask_path = Path(srow["mask_path"])
            with Image.open(img_path) as im:
                raw_img = im.convert("L")
            with Image.open(mask_path) as mf:
                raw_mask_pil = mf.convert("L")
                raw_mask = (np.array(raw_mask_pil) > 0).astype(np.uint8)
            h_img, w_img = raw_mask.shape
            orig_comps, labeled_gt = extract_gt_components(raw_mask)
            sub = ff_comp[ff_comp["sample_id"] == sid].set_index("component_id")
            size_labels = {int(cid): str(r["size_stratum"]) for cid, r in sub.iterrows()}

            # ---- GLOBAL ----
            t512, _, meta_g = _preprocess_image(raw_img, 512)
            prob512 = torch.sigmoid(global_model(t512.to(device))).squeeze().cpu().numpy()
            prob_g, mask_g = _restore_original_coordinates(
                prob512, (prob512 >= GLOBAL_THRESHOLD).astype(np.uint8), meta_g)

            def refiner_arm(proposals):
                probs, supps = [], []
                for prop in proposals:
                    geom = prop["crop_geometry"]
                    crop_pil, _ = crop_and_preprocess(raw_img, raw_mask_pil, geom, 256)
                    ct = torch.from_numpy(np.asarray(crop_pil, dtype=np.float32)).unsqueeze(0).unsqueeze(0) / 255.0
                    pr = torch.sigmoid(refiner(ct.to(device)))[0, 0].cpu().numpy()
                    rp, sp = restore_regional_probability(pr, geom, (h_img, w_img))
                    probs.append(rp); supps.append(sp)
                fused = aggregate_and_fuse(prob_g, probs, supps)
                return fused, (fused >= FUSION_THRESHOLD).astype(np.uint8)

            # ---- ORACLE ----
            oracle_props = [{"crop_geometry": apply_context_margin(
                (c["min_y"], c["min_x"], c["max_y"], c["max_x"]), (h_img, w_img), margin=POLICY["margin"])}
                for c in orig_comps]
            prob_o, mask_o = refiner_arm(oracle_props)

            # ---- PREDICTED (frozen Phase-14 construction: localizer at 512 default) ----
            dummy = Image.new("L", raw_img.size)
            tl, _, meta_l = loc_transform(raw_img, dummy)
            hm = torch.sigmoid(p13b_model(tl.unsqueeze(0).to(device)))[0, 0].float().cpu().numpy()
            props_p = generate_predicted_rois(hm, meta_l, (h_img, w_img),
                                              POLICY["threshold"], POLICY["margin"], POLICY["top_k"], POLICY["nms_iou"])
            prob_p, mask_p = refiner_arm(props_p)

            # ---- H3 DOWNSTREAM (128 heatmap) ----
            hm3 = torch.sigmoid(h3_model(tl.unsqueeze(0).to(device)))[0, 0].float().cpu().numpy()
            props_h = generate_predicted_rois(hm3, meta_l, (h_img, w_img),
                                              POLICY["threshold"], POLICY["margin"], POLICY["top_k"], POLICY["nms_iou"])
            prob_h, mask_h = refiner_arm(props_h)

            arm_data = {
                "GLOBAL": (mask_g, prob_g, None),
                "ORACLE_REGIONAL": (mask_o, prob_o, None),
                "PREDICTED_REGIONAL": (mask_p, prob_p, len(props_p)),
                "H3_DOWNSTREAM": (mask_h, prob_h, len(props_h)),
            }

            for arm in ARMS:
                mask_a, prob_a, n_props = arm_data[arm]
                m = binary_confusion_counts(mask_a, raw_mask)
                for k in ("tp", "tn", "fp", "fn", "total"):
                    pooled_conf[arm][k] += m[k]
                calib[arm].update(prob_a, raw_mask)
                bd = boundary_metrics_cropped(mask_a, raw_mask)
                cdm = component_detection_metrics(labeled_gt, mask_a, size_labels=size_labels)
                comp_totals[arm]["gt"] += cdm["gt_components"]
                comp_totals[arm]["detected"] += cdm["tp_components"]
                comp_totals[arm]["pred"] += cdm["predicted_components"]
                comp_totals[arm]["fp"] += cdm["fp_components"]
                comp_totals[arm]["matched"] += cdm["predicted_components"] - cdm["fp_components"]
                for s, d in cdm["per_size"].items():
                    tgt = per_size_totals[arm].setdefault(s, {"gt": 0, "detected": 0})
                    tgt["gt"] += d["gt"]; tgt["detected"] += d["detected"]

                per_image.append({
                    "sample_id": sid, "arm": arm, "metric_domain": "PIXEL_SEGMENTATION",
                    "tp": m["tp"], "tn": m["tn"], "fp": m["fp"], "fn": m["fn"],
                    "dice": dice(m), "iou": iou(m), "precision": precision(m), "recall": recall(m),
                    "specificity": specificity(m), "npv": npv(m), "accuracy": accuracy(m),
                    "balanced_accuracy": balanced_accuracy(m), "mcc": mcc(m), "cohen_kappa": cohen_kappa(m),
                    "fpr": false_positive_rate(m), "fnr": false_negative_rate(m),
                    "hd95": bd["hd95"], "assd": bd["assd"], "surface_dice": bd["surface_dice"],
                    "boundary_valid": bd["valid"], "boundary_unit": bd["unit"],
                    "gt_empty": bool(m["foreground_gt"] == 0), "pred_empty": bool(m["foreground_pred"] == 0),
                    "gt_components": cdm["gt_components"], "pred_components": cdm["predicted_components"],
                    "tp_components": cdm["tp_components"], "fn_components": cdm["fn_components"],
                    "fp_components": cdm["fp_components"],
                    "component_precision": cdm["component_precision"],
                    "component_recall": cdm["component_recall"],
                    "component_f1": cdm["component_f1"],
                    "proposals": n_props if n_props is not None else len(oracle_props),
                    "detected_gt_components": cdm["tp_components"],
                })
                for gid, s in size_labels.items():
                    gm = labeled_gt == gid
                    ov = int(np.count_nonzero(mask_a & gm))
                    per_component.append({
                        "sample_id": sid, "component_id": gid, "arm": arm, "size_stratum": s,
                        "component_pixels": int(np.count_nonzero(gm)),
                        "overlap_pixels": ov,
                        "detection": bool(ov >= 1),
                        "coverage50": bool(ov / max(1, int(np.count_nonzero(gm))) >= 0.50),
                        "coverage90": bool(ov / max(1, int(np.count_nonzero(gm))) >= 0.90),
                        "metric_domain": "COMPONENT_DETECTION",
                    })
            if (idx + 1) % 20 == 0 or (idx + 1) == len(ff):
                print(f"  {idx + 1}/{len(ff)}")

    img_df = pd.DataFrame(per_image)
    comp_df = pd.DataFrame(per_component)

    # ── Safe-replay condition 6: reproduce frozen primary metrics FIRST ─────
    repro = {}
    ok = True
    for arm in ARMS:
        d = float(img_df[img_df["arm"] == arm]["dice"].mean())
        ref = REFERENCE_DICE[arm]
        good = abs(d - ref) < REPRO_TOL
        repro[arm] = {"replayed_mean_dice": d, "frozen_reference": ref, "match": bool(good)}
        ok &= good
    for arm in ARMS:
        tiny = comp_df[(comp_df["arm"] == arm) & (comp_df["size_stratum"] == "TINY")]
        r = float(tiny["detection"].mean())
        ref = REFERENCE_TINY_DET[arm]
        good = abs(r - ref) < REPRO_TOL
        repro[arm]["replayed_tiny_detection"] = r
        repro[arm]["frozen_tiny_detection"] = ref
        repro[arm]["tiny_match"] = bool(good)
        ok &= good

    print("[backfill] Reproduction gate:")
    for arm in ARMS:
        print(f"   {arm}: dice {repro[arm]['replayed_mean_dice']:.10f} vs {repro[arm]['frozen_reference']:.10f} "
              f"-> {'OK' if repro[arm]['match'] else 'MISMATCH'}; tiny {repro[arm]['replayed_tiny_detection']:.6f} "
              f"-> {'OK' if repro[arm]['tiny_match'] else 'MISMATCH'}")
    if not ok:
        raise RuntimeError("Reproduction gate FAILED — refusing to write descriptive backfill artifacts.")

    # ── Aggregates ──────────────────────────────────────────────────────────
    summary_rows = []
    for arm in ARMS:
        sub = img_df[img_df["arm"] == arm]
        c = pooled_conf[arm]
        pooled = {"dice": dice(c), "iou": iou(c), "precision": precision(c), "recall": recall(c),
                  "specificity": specificity(c), "npv": npv(c), "accuracy": accuracy(c),
                  "balanced_accuracy": balanced_accuracy(c), "mcc": mcc(c), "cohen_kappa": cohen_kappa(c)}
        cs = calib[arm].summary()
        row = {"arm": arm, "metric_domain": "PIXEL_SEGMENTATION", "n_images": int(len(sub))}
        row.update({f"pooled_{k}": v for k, v in pooled.items()})
        row.update({f"pooled_{k}": c[k] for k in ("tp", "tn", "fp", "fn")})
        for metric in ("dice", "iou", "precision", "recall", "specificity", "mcc", "balanced_accuracy"):
            v = sub[metric].astype(float).dropna()
            ci = bootstrap_ci(v.tolist(), n_boot=2000, seed=42)
            row[f"image_mean_{metric}"] = float(v.mean())
            row[f"image_median_{metric}"] = float(v.median())
            row[f"image_std_{metric}"] = float(v.std(ddof=1)) if len(v) > 1 else float("nan")
            row[f"image_iqr_{metric}"] = float(v.quantile(0.75) - v.quantile(0.25))
            row[f"image_min_{metric}"] = float(v.min())
            row[f"image_max_{metric}"] = float(v.max())
            row[f"{metric}_ci_low"] = ci["ci_low"]
            row[f"{metric}_ci_high"] = ci["ci_high"]
        for metric in ("hd95", "assd", "surface_dice"):
            v = sub[metric].astype(float).dropna()
            if len(v):
                ci = bootstrap_ci(v.tolist(), n_boot=2000, seed=42)
                row[f"image_mean_{metric}"] = float(v.mean())
                row[f"image_median_{metric}"] = float(v.median())
                row[f"{metric}_ci_low"] = ci["ci_low"]
                row[f"{metric}_ci_high"] = ci["ci_high"]
                row[f"n_valid_{metric}"] = int(len(v))
            else:
                row[f"image_mean_{metric}"] = float("nan")
                row[f"n_valid_{metric}"] = 0
        row.update({"brier": cs["brier"], "ece": cs["ece"], "mce": cs["mce"],
                    "roc_auc": cs["roc_auc"], "average_precision": cs["average_precision"],
                    "positive_fraction": cs["positive_fraction"]})
        row["unit_boundary"] = "pixel"
        row["surface_tolerance_px"] = SURFACE_TOLERANCE_PX
        ct = comp_totals[arm]
        row.update({"component_gt_total": ct["gt"], "component_tp_total": ct["detected"],
                    "component_fn_total": ct["gt"] - ct["detected"], "component_fp_total": ct["fp"],
                    "component_precision_overall": (ct["matched"] / ct["pred"]) if ct["pred"] else float("nan"),
                    "component_recall_overall": ct["detected"] / ct["gt"] if ct["gt"] else float("nan"),
                    "mean_fp_components_per_image": float(sub["fp_components"].mean()),
                    "mean_detected_components_per_image": float(sub["detected_gt_components"].mean())})
        summary_rows.append(row)
    summary_df = pd.DataFrame(summary_rows)

    # Per-size component recall
    size_rows = []
    for arm in ARMS:
        for s in ("TINY", "SMALL", "MEDIUM", "LARGE"):
            d = per_size_totals[arm].get(s)
            if d and d["gt"]:
                size_rows.append({"arm": arm, "size_stratum": s, "gt_components": d["gt"],
                                  "detected": d["detected"], "detection_recall": d["detected"] / d["gt"],
                                  "metric_domain": "COMPONENT_DETECTION"})
    size_df = pd.DataFrame(size_rows)

    # Strict coverage sensitivity (component level)
    cov_rows = []
    for arm in ARMS:
        s = comp_df[comp_df["arm"] == arm]
        cov_rows.append({"arm": arm,
                         "coverage50_overall": float(s["coverage50"].mean()),
                         "coverage90_overall": float(s["coverage90"].mean()),
                         "detection_overall": float(s["detection"].mean()),
                         "tiny_detection": float(s[s["size_stratum"] == "TINY"]["detection"].mean()),
                         "tiny_coverage50": float(s[s["size_stratum"] == "TINY"]["coverage50"].mean()),
                         "tiny_coverage90": float(s[s["size_stratum"] == "TINY"]["coverage90"].mean()),
                         "metric_domain": "COMPONENT_DETECTION"})
    cov_df = pd.DataFrame(cov_rows)

    # Paired comparisons (same images)
    paired_rows = []
    pivot = img_df.pivot_table(index="sample_id", columns="arm", values="dice")
    for a, b in [("H3_DOWNSTREAM", "GLOBAL"), ("PREDICTED_REGIONAL", "GLOBAL"),
                 ("H3_DOWNSTREAM", "PREDICTED_REGIONAL"), ("ORACLE_REGIONAL", "GLOBAL")]:
        if a in pivot and b in pivot:
            x = pivot[a].to_numpy(); y = pivot[b].to_numpy()
            pb = paired_bootstrap_ci(x, y, n_boot=2000, seed=42)
            d = x - y
            try:
                from scipy.stats import wilcoxon
                w = wilcoxon(x, y)
                wstat, wp = float(w.statistic), float(w.pvalue)
            except Exception:
                wstat, wp = float("nan"), float("nan")
            paired_rows.append({"comparison": f"{a} - {b}", "metric": "dice", "n_pairs": int(d.size),
                                "mean_difference": pb["mean_difference"], "median_difference": pb["median_difference"],
                                "ci_low": pb["ci_low"], "ci_high": pb["ci_high"],
                                "wilcoxon_statistic": wstat, "wilcoxon_p": wp,
                                "label": "DESCRIPTIVE_POST_HOC_STATISTICAL_SUPPORT",
                                "metric_domain": "PIXEL_SEGMENTATION"})
    paired_df = pd.DataFrame(paired_rows)

    # ── Persist ─────────────────────────────────────────────────────────────
    img_path = TABLES / "project_evaluation_per_image_metrics.csv"
    comp_path = TABLES / "project_evaluation_per_component_metrics.csv"
    summ_path = TABLES / "project_evaluation_segmentation_summary.csv"
    size_path = TABLES / "project_evaluation_component_recall_by_size.csv"
    cov_path = TABLES / "project_evaluation_coverage_sensitivity.csv"
    pair_path = TABLES / "project_evaluation_paired_comparisons.csv"
    img_df.to_csv(img_path, index=False)
    comp_df.to_csv(comp_path, index=False)
    summary_df.to_csv(summ_path, index=False)
    size_df.to_csv(size_path, index=False)
    cov_df.to_csv(cov_path, index=False)
    paired_df.to_csv(pair_path, index=False)

    conf_matrices = {}
    for arm in ARMS:
        c = pooled_conf[arm]
        tot = float(c["tp"] + c["tn"] + c["fp"] + c["fn"])
        row_tot = {"fg": float(c["tp"] + c["fn"]), "bg": float(c["tn"] + c["fp"])}
        conf_matrices[arm] = {
            "metric_domain": "PIXEL_SEGMENTATION",
            "raw_counts": {"tn": c["tn"], "fp": c["fp"], "fn": c["fn"], "tp": c["tp"]},
            "matrix_raw": [[c["tn"], c["fp"]], [c["fn"], c["tp"]]],
            "matrix_row_normalized": [[c["tn"] / row_tot["bg"] if row_tot["bg"] else 0.0,
                                       c["fp"] / row_tot["bg"] if row_tot["bg"] else 0.0],
                                      [c["fn"] / row_tot["fg"] if row_tot["fg"] else 0.0,
                                       c["tp"] / row_tot["fg"] if row_tot["fg"] else 0.0]],
            "labels": ["Background", "Foreground"],
            "pooled_pixels": int(tot),
            "positive_fraction": float((c["tp"] + c["fn"]) / tot) if tot else float("nan"),
            "calibration": calib[arm].summary(),
        }
    conf_path = TABLES / "project_evaluation_confusion_matrices.json"
    conf_path.write_text(json.dumps(conf_matrices, indent=2), encoding="utf-8")

    artifact = {
        "artifact": "project_evaluation_metrics_backfill",
        "status": "PROJECT_EVALUATION_METRICS_BACKFILL_COMPLETE__DESCRIPTIVE_ONLY",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "purpose": "Generate missing DESCRIPTIVE pixel/boundary/calibration metrics that were never persisted.",
        "safe_replay_rule": {
            "1_checkpoints_frozen_and_sha_verified": True,
            "2_evaluator_preprocessing_frozen": True,
            "2_note": "Reuses the frozen modules verbatim: _preprocess_image, _restore_original_coordinates, "
                      "generate_predicted_rois, crop_and_preprocess, restore_regional_probability, aggregate_and_fuse.",
            "3_no_test_access": True,
            "4_no_threshold_search": True,
            "5_strictly_descriptive_missing_metrics": True,
            "6_existing_primary_metrics_reproduced_first": True,
            "7_does_not_change_frozen_decisions": True,
            "8_explicitly_logged": True,
            "verdict": "REPLAY_PERFORMED_LAWFULLY",
        },
        "checkpoint_shas": shas,
        "population": {"view_type": "FULL_FIELD", "images": 103, "components": 152,
                       "size_strata": {"TINY": 72, "SMALL": 28, "MEDIUM": 36, "LARGE": 16}},
        "frozen_proposal_policy": POLICY,
        "fusion_threshold": FUSION_THRESHOLD,
        "global_threshold": GLOBAL_THRESHOLD,
        "boundary_units": "pixel",
        "pixel_spacing_available": False,
        "pixel_spacing_note": "No spacing/calibration metadata exists in the repository; all boundary distances are in PIXELS, never mm.",
        "surface_tolerance_px": SURFACE_TOLERANCE_PX,
        "boundary_crop_margin_px": BOUNDARY_CROP_MARGIN,
        "calibration_bins": CALIB_BINS,
        "calibration_quantization_note": "The frozen restore path quantizes probabilities to 1/255 levels; "
                                          "calibration metrics are computed on those quantized maps.",
        "reproduction_gate": repro,
        "metric_labels": {
            "all_new_metrics": "DESCRIPTIVE_SUPPORTING_METRIC__NOT_PROSPECTIVE_GATE",
            "h3_specific": "DESCRIPTIVE_SUPPORTING_METRIC__NOT_H3_GATE",
            "paired_statistics": "DESCRIPTIVE_POST_HOC_STATISTICAL_SUPPORT",
        },
        "bootstrap": {"n_boot": 2000, "seed": 42, "ci_method": "percentile",
                      "resampling_unit": "image (per-image metric); component tables use component rows"},
        "artifacts": {
            "per_image_metrics": {"path": "reports/tables/project_evaluation_per_image_metrics.csv",
                                   "rows": int(len(img_df)), "sha256": sha256_file(img_path)},
            "per_component_metrics": {"path": "reports/tables/project_evaluation_per_component_metrics.csv",
                                       "rows": int(len(comp_df)), "sha256": sha256_file(comp_path)},
            "segmentation_summary": {"path": "reports/tables/project_evaluation_segmentation_summary.csv",
                                      "rows": int(len(summary_df)), "sha256": sha256_file(summ_path)},
            "component_recall_by_size": {"path": "reports/tables/project_evaluation_component_recall_by_size.csv",
                                          "rows": int(len(size_df)), "sha256": sha256_file(size_path)},
            "coverage_sensitivity": {"path": "reports/tables/project_evaluation_coverage_sensitivity.csv",
                                      "rows": int(len(cov_df)), "sha256": sha256_file(cov_path)},
            "paired_comparisons": {"path": "reports/tables/project_evaluation_paired_comparisons.csv",
                                    "rows": int(len(paired_df)), "sha256": sha256_file(pair_path)},
            "confusion_matrices": {"path": "reports/tables/project_evaluation_confusion_matrices.json",
                                    "sha256": sha256_file(conf_path)},
        },
        "governance": {
            "test_reads": 0, "external_test_reads": 0, "training_executed": False,
            "thresholds_changed": False, "checkpoints_changed": False,
            "frozen_gates_changed": False, "phase15_status": "NOT_STARTED_AND_NOT_AUTHORIZED",
        },
        "runtime_seconds": time.time() - t0,
        "device": str(device),
    }
    out = AUDITS / "project_evaluation_metrics_backfill.json"
    out.write_text(json.dumps(artifact, indent=2), encoding="utf-8")

    print("\n" + "=" * 74)
    print("PROJECT EVALUATION METRICS BACKFILL")
    print("=" * 74)
    cols = ["arm", "pooled_dice", "pooled_iou", "pooled_recall", "pooled_specificity", "pooled_mcc",
            "hd95", "assd", "surface_dice", "brier", "ece", "roc_auc", "average_precision"]
    print(summary_df[[c for c in cols if c in summary_df.columns]].to_string(index=False))
    print(f"\nArtifact: {out}")
    print("=" * 74)
    return artifact


if __name__ == "__main__":
    main()
