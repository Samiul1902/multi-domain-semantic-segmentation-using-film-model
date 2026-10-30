"""Phase 22 — regional intervention: ORACLE (GT-defined) and PREDICTION-DERIVED.

Both variants answer the same counterfactual question:

    "If a region of interest were cropped out of the native image, resampled to
     512x512 with the frozen contract, re-run through the SAME frozen checkpoint,
     and re-projected into the full-field probability map, what would change?"

The ONLY difference between the two variants is where the ROI comes from:

  ORACLE      the tight bounding box of the GROUND-TRUTH foreground. This is an
              upper bound: it knows the answer. It is NOT a deployable method and
              must never be reported as one.
  PREDICTED   the tight bounding box of the FROZEN MODEL'S OWN thresholded
              prediction. This is deployable in principle, but it inherits every
              failure of the global prediction, including a total miss producing
              no ROI at all (recorded as ``NO_PREDICTED_ROI``).

FROZEN ROI RULE (prospectively declared, identical for both variants)
--------------------------------------------------------------------
  1. tight bounding box of the relevant binary mask (native space)
  2. CENTRE-PRESERVING expansion by ``margin`` on each side along each axis;
     margin = 0.25 gives an expanded extent of 1.5 x bbox width and height
  3. clip to the source-image boundary (the box is NOT re-centred after clipping)
  4. square-pad about the box centre, staying inside the image
  5. aspect-preserving resize + centre pad to 512x512 via the frozen contract
     (the crop is already square, so this is a plain square->square resample that
     preserves the ROI centre exactly)
  6. paste the regional probability back ONLY over the ROI footprint
  7. outside the ROI: keep the ORIGINAL global probability, unchanged

The comparison is always: regional-fused map vs the global map, on the SAME
native pixel population, thresholded by ONE declared rule.

No training. No TEST. No threshold tuning. No TTA. No morphology.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.analysis import phase22_common as C          # noqa: E402
from src.metrics.evaluation_metrics import segmentation_metrics  # noqa: E402
from src.utils.device import get_device               # noqa: E402

OUT_AUDIT = C.AUDITS / "phase22_oracle_regional_intervention.json"
OUT_PER_IMAGE = C.TABLES / "phase22_regional_intervention_per_image.csv"
OUT_TABLE = C.TABLES / "phase22_oracle_gain.csv"
OUT_BY_DOMAIN = C.TABLES / "phase22_oracle_gain_by_domain.csv"
OUT_ROI = C.TABLES / "phase22_roi_geometry.csv"
OUT_FIDELITY = C.AUDITS / "phase22_regional_fidelity.json"

VARIANTS = ("oracle", "predicted")


def _load_val() -> pd.DataFrame:
    frame = pd.read_csv(C.MANIFEST_DIR / "val.csv")
    frame = frame[frame["split"].astype(str).str.upper() == "VAL"].copy()
    return frame.sort_values(["dataset", "sample_id"]).reset_index(drop=True)


def _regional_probability(model, device, raw_image: Image.Image, roi_box: dict,
                          task_id: torch.Tensor, size: int = C.DIAGNOSTIC_SIZE):
    """Crop a square ROI, run the frozen model, return the native-space crop prob.

    Returns ``(prob_native_roi, geom, crop_side)`` where ``prob_native_roi`` has
    shape ``(side, side)`` in native pixel units.
    """
    y0, y1, x0, x1 = roi_box["y0"], roi_box["y1"], roi_box["x0"], roi_box["x1"]
    crop = raw_image.crop((x0, y0, x1 + 1, y1 + 1))
    side = roi_box["side"]
    if crop.size != (side, side):
        # square_pad_box guarantees a square box; this is a defensive assertion
        raise RuntimeError(
            f"ROI crop is not square: crop.size={crop.size} vs side={side} "
            f"(box y0={y0} y1={y1} x0={x0} x1={x1}, image={raw_image.size})")

    img_t, _, geom = C.aspect_resize_pad(crop, None, size, image_mode="RGB")
    x = img_t.unsqueeze(0).to(device)
    with torch.no_grad():
        with torch.amp.autocast(device_type=device.type, enabled=True):
            logits = model(x, task_id)
    prob_sq = torch.sigmoid(logits.float()).cpu().numpy()[0, 0]
    prob_native = C.unmap_probability_to_source(prob_sq, geom)
    return prob_native, geom, side, prob_sq


def run(device_spec: str = "auto", margin: float = C.ORACLE_ROI_MARGIN,
        limit: int | None = None) -> int:
    t0 = time.time()
    C.verify_no_test_access()
    device = get_device(require_cuda=False) if device_spec == "auto" else torch.device(device_spec)
    model, prov = C.load_frozen_medfilm(device)
    print(f"loaded frozen checkpoint epoch={prov['checkpoint_epoch']} "
          f"sha={prov['checkpoint_sha256'][:16]} device={device}")

    frame = _load_val()
    if limit:
        frame = frame.groupby("dataset", group_keys=False).head(max(1, limit // 4))
        frame = frame.reset_index(drop=True)
    print(f"population: {len(frame)} VAL samples; margin={margin}")

    manifest = pd.read_csv(C.TABLES / "phase21_prediction_manifest.csv")
    npz_of = dict(zip(manifest["sample_id"], manifest["npz_path"]))

    rows, roi_rows, fid_rows = [], [], []
    for i, rec in enumerate(frame.itertuples(index=False), 1):
        sid, ds = str(rec.sample_id), str(rec.dataset)
        task_id = torch.tensor([C.TASK_ID[ds]], dtype=torch.long, device=device)

        with Image.open(rec.image_path) as fh:
            raw = fh.convert("RGB")
        with Image.open(rec.mask_path) as fh:
            native_gt = (np.asarray(fh.convert("L")) > 0).astype(np.uint8)
        native_shape = native_gt.shape

        # ---- global reference, recomputed from the frozen checkpoint ------ #
        img_t, _, ggeom = C.aspect_resize_pad(raw, None, C.DIAGNOSTIC_SIZE, "RGB")
        with torch.no_grad():
            with torch.amp.autocast(device_type=device.type, enabled=True):
                glog = model(img_t.unsqueeze(0).to(device), task_id)
        gprob_sq = torch.sigmoid(glog.float()).cpu().numpy()[0, 0]
        gprob_native = C.unmap_probability_to_source(gprob_sq, ggeom)

        # fidelity: recomputed global vs the canonical persisted probability
        ref = np.load(ROOT / npz_of[sid])
        fid_rows.append({
            "sample_id": sid, "dataset": ds,
            "global_vs_canonical_prob_max_abs_diff_square": float(np.abs(
                ref["prob"].astype(np.float32) - gprob_sq).max()),
            "global_vs_canonical_rule_disagreement_pixels": int(np.count_nonzero(
                C.threshold_probability(gprob_sq)
                != C.threshold_probability(ref["prob"].astype(np.float32)))),
        })

        g_pred = C.threshold_probability(gprob_native)
        g_m = segmentation_metrics(g_pred, native_gt)

        base = {
            "sample_id": sid, "dataset": ds, "task_id": C.TASK_ID[ds],
            "native_h": int(native_shape[0]), "native_w": int(native_shape[1]),
            "gt_foreground_pixels": int(native_gt.sum()),
            "global_dice": float(g_m["dice"]), "global_iou": float(g_m["iou"]),
            "global_precision": float(g_m["precision"]),
            "global_recall": float(g_m["recall"]),
            "global_empty_case": g_m["empty_case"],
            "gt_empty": bool(g_m["gt_empty"]),
            "global_pred_foreground_pixels": int(g_pred.sum()),
        }

        for variant in VARIANTS:
            if variant == "oracle":
                seed_mask = native_gt
            else:
                seed_mask = g_pred

            bbox = C.bbox_of(seed_mask)
            if bbox is None:
                base.update({
                    f"{variant}_status": ("NO_GT_ROI" if variant == "oracle"
                                          else "NO_PREDICTED_ROI"),
                    f"{variant}_roi_side": 0, f"{variant}_roi_area_fraction": 0.0,
                    f"{variant}_dice": float(g_m["dice"]),
                    f"{variant}_delta_dice": 0.0,
                    f"{variant}_delta_iou": 0.0,
                    f"{variant}_delta_precision": 0.0,
                    f"{variant}_delta_recall": 0.0,
                    f"{variant}_fused_foreground_pixels": int(g_pred.sum()),
                })
                continue

            roi = C.expanded_roi_box(bbox, native_shape, margin=margin)
            sq = C.square_pad_box(roi, native_shape)
            prob_native_roi, rgeom, side, prob_sq = _regional_probability(
                model, device, raw, sq, task_id)

            # ---- splice: regional prob INSIDE the ROI, global prob OUTSIDE -- #
            fused = gprob_native.copy()
            y0, y1, x0, x1 = sq["y0"], sq["y1"], sq["x0"], sq["x1"]
            block = fused[y0:y1 + 1, x0:x1 + 1]
            if block.shape != prob_native_roi.shape:
                raise RuntimeError(f"ROI paste shape mismatch: {block.shape} "
                                   f"vs {prob_native_roi.shape}")
            fused[y0:y1 + 1, x0:x1 + 1] = prob_native_roi
            f_pred = C.threshold_probability(fused)
            f_m = segmentation_metrics(f_pred, native_gt)

            roi_area = float((y1 - y0 + 1) * (x1 - x0 + 1))
            roi_frac = roi_area / float(native_shape[0] * native_shape[1])
            eff_mag = float(side) / float(sq["side"]) if sq["side"] else float("nan")

            base.update({
                f"{variant}_status": "OK",
                f"{variant}_roi_side": int(sq["side"]),
                f"{variant}_roi_area_fraction": round(roi_frac, 8),
                f"{variant}_effective_magnification": round(
                    C.DIAGNOSTIC_SIZE / float(sq["side"]), 6),
                f"{variant}_roi_h": int(sq["side"]), f"{variant}_roi_w": int(sq["side"]),
                f"{variant}_clipped": bool(roi["clipped"]),
                f"{variant}_dice": float(f_m["dice"]),
                f"{variant}_iou": float(f_m["iou"]),
                f"{variant}_precision": float(f_m["precision"]),
                f"{variant}_recall": float(f_m["recall"]),
                f"{variant}_delta_dice": float(f_m["dice"] - g_m["dice"]),
                f"{variant}_delta_iou": float(f_m["iou"] - g_m["iou"]),
                f"{variant}_delta_precision": float(f_m["precision"] - g_m["precision"]),
                f"{variant}_delta_recall": float(f_m["recall"] - g_m["recall"]),
                f"{variant}_fused_foreground_pixels": int(f_pred.sum()),
                f"{variant}_gain_pixels_outside_roi": 0,
            })
            if variant == "oracle":
                roi_rows.append({
                    "sample_id": sid, "dataset": ds,
                    "gt_bbox_h": bbox["bbox_h"], "gt_bbox_w": bbox["bbox_w"],
                    "gt_bbox_area": int(bbox["bbox_h"] * bbox["bbox_w"]),
                    "expanded_h_requested": roi["expanded_h"],
                    "expanded_w_requested": roi["expanded_w"],
                    "expansion_factor_h": roi["expansion_factor"][0],
                    "expansion_factor_w": roi["expansion_factor"][1],
                    "clipped": bool(roi["clipped"]),
                    "roi_side": int(sq["side"]),
                    "roi_area_fraction": round(roi_frac, 8),
                    "effective_magnification": round(
                        C.DIAGNOSTIC_SIZE / float(sq["side"]), 6),
                    "square_pad_shift_y": int(sq["shift_y"]),
                    "square_pad_shift_x": int(sq["shift_x"]),
                    "centre_preserved": bool(
                        abs(sq["shift_y"]) <= 1 and abs(sq["shift_x"]) <= 1),
                    "mask_bbox_fraction_of_image": round(
                        (bbox["bbox_h"] * bbox["bbox_w"])
                        / float(native_shape[0] * native_shape[1]), 8),
                })

        rows.append(base)
        if i % 80 == 0:
            print(f"  {i}/{len(frame)}  ({time.time()-t0:.0f}s)")

    per_image = pd.DataFrame(rows)
    per_image.to_csv(OUT_PER_IMAGE, index=False)
    pd.DataFrame(roi_rows).to_csv(OUT_ROI, index=False)

    fid = pd.DataFrame(fid_rows)
    fid_max = float(fid["global_vs_canonical_prob_max_abs_diff_square"].max())
    fid_px = int(fid["global_vs_canonical_rule_disagreement_pixels"].sum())
    C.write_json(OUT_FIDELITY, {
        "artifact": "phase22_regional_fidelity",
        "phase": 22,
        "test": ("recomputed global pass vs the canonical persisted probability map, "
                 "shared 512 square canvas"),
        "n_samples": int(len(fid)),
        "max_abs_probability_difference_square": fid_max,
        "total_thresholded_disagreement_pixels": fid_px,
        "denominator_pixels": int(len(fid) * 512 * 512),
        "verdict": "PASS" if fid_max <= 5e-3 else "REVIEW",
        "note": ("the recomputed global map is the correct baseline for the regional "
                 "comparison: both arms then share one inference path"),
        "test_reads": 0,
    })
    print(f"fidelity: max|dp|={fid_max:.3e}  thresholded px={fid_px}")

    # ---- gain summary ---------------------------------------------------- #
    def summarise(variant: str) -> dict:
        col = f"{variant}_status"
        ok = per_image[per_image[col] == "OK"]
        nonp = per_image[per_image[col].str.startswith("NO_")]
        out = {
            "variant": variant,
            "n_total": int(len(per_image)),
            "n_ok": int(len(ok)), "n_no_roi": int(len(nonp)),
            "no_roi_reason": (nonp[col].value_counts().to_dict() if len(nonp) else {}),
        }
        if len(ok):
            out.update({
                "mean_global_dice_on_ok": float(ok["global_dice"].mean()),
                "mean_regional_dice_on_ok": float(ok[f"{variant}_dice"].mean()),
                "mean_delta_dice_on_ok": float(ok[f"{variant}_delta_dice"].mean()),
                "mean_delta_iou_on_ok": float(ok[f"{variant}_delta_iou"].mean()),
                "n_improved_on_ok": int((ok[f"{variant}_delta_dice"] > 0).sum()),
                "n_worsened_on_ok": int((ok[f"{variant}_delta_dice"] < 0).sum()),
                "n_unchanged_on_ok": int((ok[f"{variant}_delta_dice"] == 0).sum()),
                "median_delta_dice_on_ok": float(ok[f"{variant}_delta_dice"].median()),
                "p05_delta_dice_on_ok": float(ok[f"{variant}_delta_dice"].quantile(0.05)),
                "p95_delta_dice_on_ok": float(ok[f"{variant}_delta_dice"].quantile(0.95)),
                "max_delta_dice_on_ok": float(ok[f"{variant}_delta_dice"].max()),
                "min_delta_dice_on_ok": float(ok[f"{variant}_delta_dice"].min()),
                "mean_roi_area_fraction": float(ok[f"{variant}_roi_area_fraction"].mean()),
                "median_roi_area_fraction": float(ok[f"{variant}_roi_area_fraction"].median()),
                "mean_effective_magnification": float(
                    ok[f"{variant}_effective_magnification"].mean()),
                "n_clipped_roi": int(ok[f"{variant}_clipped"].sum()),
            })
        # INTENT-TO-TREAT: no-ROI cases count as zero gain
        out["mean_delta_dice_intent_to_treat"] = (
            float(per_image[f"{variant}_delta_dice"].mean())
            if f"{variant}_delta_dice" in per_image.columns else 0.0)
        return out

    gain = pd.concat(
        [per_image.assign(variant="oracle")[[
            "sample_id", "dataset", "global_dice", "oracle_dice", "oracle_delta_dice",
            "oracle_status", "oracle_roi_area_fraction"]],
         per_image.assign(variant="predicted")[[
            "sample_id", "dataset", "global_dice", "predicted_dice",
            "predicted_delta_dice", "predicted_status", "predicted_roi_area_fraction"]]],
        ignore_index=True)
    gain.to_csv(OUT_TABLE, index=False)

    summaries = {v: summarise(v) for v in VARIANTS}

    # per-domain oracle gain
    dom_rows = []
    for name in C.DATASET_ORDER:
        sub = per_image[per_image["dataset"] == name]
        ok = sub[sub["oracle_status"] == "OK"]
        dom_rows.append({
            "dataset": name, "n": int(len(sub)), "n_oracle_ok": int(len(ok)),
            "mean_global_dice": float(sub["global_dice"].mean()),
            "mean_oracle_dice": float(ok["oracle_dice"].mean()) if len(ok) else float("nan"),
            "mean_oracle_delta_dice": float(ok["oracle_delta_dice"].mean()) if len(ok) else float("nan"),
            "mean_oracle_delta_dice_intent_to_treat": float(
                sub["oracle_delta_dice"].mean()) if "oracle_delta_dice" in sub else float("nan"),
            "n_oracle_improved": int((ok["oracle_delta_dice"] > 0).sum()),
            "n_oracle_worsened": int((ok["oracle_delta_dice"] < 0).sum()),
            "mean_predicted_delta_dice": float(sub["predicted_delta_dice"].mean()),
            "n_no_predicted_roi": int(
                (sub["predicted_status"] == "NO_PREDICTED_ROI").sum()),
            "mean_roi_area_fraction": float(ok["oracle_roi_area_fraction"].mean()) if len(ok) else float("nan"),
            "mean_effective_magnification": float(
                ok["oracle_effective_magnification"].mean()) if len(ok) else float("nan"),
        })
    dom = pd.DataFrame(dom_rows)
    dom.to_csv(OUT_BY_DOMAIN, index=False)

    payload = {
        "artifact": "phase22_oracle_regional_intervention",
        "phase": 22,
        "protocol_id": "phase22_diagnostic_protocol_v1",
        "inference_only": True,
        "training_jobs_started": 0,
        "checkpoint": prov,
        "roi_rule": {
            "margin": float(margin),
            "expansion": "centre-preserving, margin on each side along each axis",
            "expanded_extent_factor": 1.0 + 2 * float(margin),
            "clip_to_source_boundary": True,
            "recentre_after_clip": False,
            "square_pad_about_box_centre": True,
            "crop_resample": "aspect-preserving resize + centre pad to 512 (crop is square)",
            "reprojection": "paste regional probability over the ROI footprint only",
            "outside_roi": "original recomputed global probability, unchanged",
            "declared_prospectively": True,
        },
        "variants": {
            "oracle": ("tight GT foreground bounding box. UPPER BOUND / diagnostic "
                       "only. NOT deployable: it uses the ground truth."),
            "predicted": ("tight bounding box of the frozen model's own thresholded "
                          "prediction. Deployable in principle; inherits global "
                          "failures, and yields NO_PREDICTED_ROI on a total miss."),
        },
        "global_baseline": ("recomputed in the SAME run through the same code path, "
                            "so the regional comparison is not contaminated by "
                            "comparing across different inference implementations"),
        "decision_rule": "pred = (float32(prob) >= 0.5), applied to every arm",
        "summaries": summaries,
        "fidelity": {
            "max_abs_probability_difference_square": fid_max,
            "total_thresholded_disagreement_pixels": fid_px,
            "artifact": "reports/audits/phase22_regional_fidelity.json",
        },
        "interpretation_guard": (
            "The ORACLE variant is an upper bound that uses ground-truth geometry. "
            "It must NEVER be presented as a deployable gain, and no claim may be "
            "made that a regional mechanism 'achieves' or 'would achieve' it. The "
            "PREDICTED variant is the deployable-shaped diagnostic, but it is still "
            "an oracle-FREE offline estimate: no benefit predictor, router, or "
            "threshold policy was trained."),
        "tables": {
            "per_image": "reports/tables/phase22_regional_intervention_per_image.csv",
            "oracle_gain": "reports/tables/phase22_oracle_gain.csv",
            "by_domain": "reports/tables/phase22_oracle_gain_by_domain.csv",
            "roi_geometry": "reports/tables/phase22_roi_geometry.csv",
        },
        "elapsed_seconds": round(time.time() - t0, 1),
        "test_reads": {"test_image_reads": 0, "test_mask_reads": 0,
                       "test_inference": 0, "test_visualization": 0},
    }
    C.write_json(OUT_AUDIT, payload)
    print(f"\nWROTE {OUT_AUDIT}")
    for v, s in summaries.items():
        print(f"\n[{v}] n_ok={s.get('n_ok')} n_no_roi={s.get('n_no_roi')} "
              f"mean_delta_dice(ok)={s.get('mean_delta_dice_on_ok')}")
        if "n_improved_on_ok" in s:
            print(f"        improved={s['n_improved_on_ok']} worsened={s['n_worsened_on_ok']} "
                  f"unchanged={s['n_unchanged_on_ok']}")
        print(f"        mean_delta_dice_ITT={s['mean_delta_dice_intent_to_treat']}")
    print(f"\nelapsed {time.time()-t0:.0f}s")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Phase-22 regional intervention (oracle + predicted).")
    ap.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"])
    ap.add_argument("--margin", type=float, default=C.ORACLE_ROI_MARGIN)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    return run(device_spec=args.device, margin=args.margin, limit=args.limit)


if __name__ == "__main__":
    raise SystemExit(main())
