"""H2C-B1 SEC 16-18 -- standalone best-checkpoint localizer evaluation + 3-way comparison.

Loads the H2C best.pt ONLY (with the frozen H2C head), runs exactly ONE deterministic
fixed-config VAL proposal evaluation (103 cases / 152 components), writes the four standalone
tables plus the 3-way comparison, and records head diagnostics at the selected checkpoint.

NO downstream segmentation. NO proposal grid. NO threshold tuning. NO TEST access.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn

ROOT = Path(r"D:\Softfors\jup")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
TABLES = ROOT / "reports" / "tables"
AUDITS = ROOT / "reports" / "audits"

H2C_ID = ("post_phase13_h2c_kub_localizer_spatialhead3x3relu_r512_h128_sigmaeq075_"
          "centernetfocal_deploymentbalance_seed42_clean_v3")
H2C_CK = ROOT / "checkpoints" / H2C_ID / "best.pt"
THRESHOLD, MARGIN, TOP_K, NMS_IOU = 0.10, 0.20, 5, 0.30
INPUT_RESOLUTION, HEATMAP_RESOLUTION = 512, 128
STRATA = ["TINY", "SMALL", "MEDIUM", "LARGE"]


class FrozenH2CSpatialHead(nn.Module):
    def __init__(self, in_ch=16, out_ch=1):
        super().__init__()
        self.conv3x3 = nn.Conv2d(in_ch, in_ch, 3, 1, 1, bias=True)
        self.relu = nn.ReLU(inplace=False)
        self.conv1x1 = nn.Conv2d(in_ch, out_ch, 1, 1, 0, bias=True)

    def forward(self, x):
        return self.conv1x1(self.relu(self.conv3x3(x)))


def sha(p) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def head_statistics(model) -> dict:
    """SEC 13/14 -- descriptive only; never gates selection."""
    h3 = model.head.conv3x3.weight.detach().float().cpu()
    t1 = model.head.conv1x1.weight.detach().float().cpu()
    ch_norms = h3.flatten(1).norm(dim=1)
    return {
        "hidden_3x3_weight_mean": float(h3.mean()),
        "hidden_3x3_weight_std": float(h3.std(unbiased=False)),
        "hidden_3x3_weight_min": float(h3.min()),
        "hidden_3x3_weight_max": float(h3.max()),
        "hidden_3x3_fraction_positive": float((h3 > 0).float().mean()),
        "hidden_3x3_fraction_negative": float((h3 < 0).float().mean()),
        "hidden_3x3_channel_norm_min": float(ch_norms.min()),
        "hidden_3x3_channel_norm_max": float(ch_norms.max()),
        "hidden_3x3_channel_norm_mean": float(ch_norms.mean()),
        "terminal_1x1_weight_mean": float(t1.mean()),
        "terminal_1x1_weight_std": float(t1.std(unbiased=False)),
        "terminal_1x1_weight_min": float(t1.min()),
        "terminal_1x1_weight_max": float(t1.max()),
        "terminal_1x1_fraction_positive": float((t1 > 0).float().mean()),
        "terminal_1x1_fraction_negative": float((t1 < 0).float().mean()),
        "terminal_bias": float(model.head.conv1x1.bias.detach().float().mean()),
        "role": "DESCRIPTIVE_ONLY__NOT_USED_FOR_SELECTION",
    }


def main() -> int:
    from PIL import Image

    from src.data.transforms import SegmentationTransform
    from src.inference.clean_v3_components import build_clean_v3_val_components
    from src.inference.clean_v3_coverage import evaluate_historical_bbox_coverage
    from src.inference.predicted_roi import generate_predicted_rois, union_roi_area_fraction
    from src.inference.learned_roi_clean_v3 import build_clean_v3_localizer
    from src.utils.checkpointing import load_training_checkpoint
    from src.utils.device import get_device
    from src.utils.manifest_guard import validate_manifest_version_strict

    validate_manifest_version_strict("phase4_v3")
    dev = get_device(require_cuda=True)
    if dev.type != "cuda":
        raise RuntimeError("CPU fallback FORBIDDEN")

    from scripts.training.post_phase13_h2c_localizer_train import _load_hard_sets  # noqa: E402

    man = pd.read_csv(ROOT / "manifests" / "phase4_v3" / "val.csv")
    val_ids = set(man["sample_id"].astype(str))
    _vf = pd.read_csv(TABLES / "kub_val_samples_sized.csv")
    ff = _vf[_vf["view_type"].eq("FULL_FIELD")
              & _vf["sample_id"].astype(str).isin(val_ids)].reset_index(drop=True)
    if len(ff) != 103:
        raise RuntimeError(f"VAL FULL_FIELD is {len(ff)}, expected 103. STOP.")
    ff = ff.rename(columns={"view_type": "acquisition_type"})

    geom = pd.read_csv(TABLES / "phase12_clean_v3_oracle_geometry.csv")
    hard_tiny_keys, global_empty_ids = _load_hard_sets()
    grouped = build_clean_v3_val_components(
        geom, ff, hard_tiny_keys=hard_tiny_keys, global_empty_ids=global_empty_ids)

    model = build_clean_v3_localizer(device=dev)
    model.head = FrozenH2CSpatialHead(16, 1).to(dev)   # frozen H2C head
    load_training_checkpoint(H2C_CK, model, restore_rng=False, map_location=dev)
    model.eval()
    hstats = head_statistics(model)
    transform = SegmentationTransform(INPUT_RESOLUTION, False)

    prop_rows, case_rows, comp_rows = [], [], []
    scores, hits = [], []
    for r in ff.itertuples():
        sid = str(r.sample_id)
        image_path = Path(str(r.image_path))
        with Image.open(image_path) as handle:
            native = handle.convert("L")
        tensor, _m, metadata = transform(native, Image.new("L", native.size))
        with torch.inference_mode():
            with torch.amp.autocast("cuda", enabled=True):
                logits = model(tensor.unsqueeze(0).to(dev))
        prob = torch.sigmoid(logits.float())[0, 0].cpu().numpy()
        if prob.shape != (HEATMAP_RESOLUTION, HEATMAP_RESOLUTION):
            raise RuntimeError(f"heatmap shape {prob.shape} != 128x128. STOP.")
        shape = (int(native.height), int(native.width))
        proposals = generate_predicted_rois(prob, metadata, shape, THRESHOLD, MARGIN, TOP_K, NMS_IOU)

        components = grouped[sid]
        gt_union = np.zeros(shape, dtype=bool)
        gt_boxes = []
        for c in components:
            gt_union |= np.asarray(c["mask"], dtype=bool)
            gt_boxes.append((int(c["min_y"]), int(c["min_x"]), int(c["max_y"]), int(c["max_x"])))

        for p in proposals:
            g = p["crop_geometry"]
            cy1, cy2, cx1, cx2 = (int(g["clip_y1"]), int(g["clip_y2"]),
                                  int(g["clip_x1"]), int(g["clip_x2"]))
            hit = bool(gt_union[cy1:cy2, cx1:cx2].any())
            py1, px1, py2, px2 = (int(v) for v in p["proposal_bbox"])
            bhit = any(not (py2 < b[0] or py1 > b[2] or px2 < b[1] or px1 > b[3]) for b in gt_boxes)
            scores.append(float(p["score"])); hits.append(1 if hit else 0)
            prop_rows.append({"sample_id": sid, "proposal_rank": int(p["rank"]),
                              "proposal_score": float(p["score"]),
                              "native_proposal_area": int((cy2 - cy1) * (cx2 - cx1)),
                              "proposal_area_fraction": float((cy2 - cy1) * (cx2 - cx1)) / (shape[0] * shape[1]),
                              "clip_y1": cy1, "clip_y2": cy2, "clip_x1": cx1, "clip_x2": cx2,
                              "crop_side_pixels": int(g["crop_side_pixels"]),
                              "overlaps_any_gt_pixel": hit, "overlaps_any_gt_bbox": bhit})

        uf, _ = union_roi_area_fraction(proposals, shape) if proposals else (0.0, 0.0)
        bbox_rows = evaluate_historical_bbox_coverage(proposals, components)
        case_rows.append({"sample_id": sid, "native_H": shape[0], "native_W": shape[1],
                          "proposal_count": len(proposals),
                          "proposal_union_area_fraction": float(uf),
                          "mean_proposal_score": float(np.mean([p["score"] for p in proposals])) if proposals else np.nan,
                          "number_of_components": len(components)})
        for cr, c in zip(bbox_rows, components):
            comp_rows.append({"sample_id": sid, "native_component_id": int(c["component_id"]),
                              "size_stratum": c["size_stratum"], "hard_tiny": bool(c["hard_tiny"]),
                              "global_empty_image": bool(c["global_empty_image"]),
                              "component_pixels": int(np.asarray(c["mask"]).sum()),
                              "coverage_fraction": float(cr["coverage_fraction"]),
                              "covered90": bool(cr["covered90"]), "covered50": bool(cr["covered50"]),
                              "any_overlap": bool(cr["any_overlap"])})
    del model
    torch.cuda.empty_cache()

    prop_df = pd.DataFrame(prop_rows)
    case_df = pd.DataFrame(case_rows).sort_values("sample_id").reset_index(drop=True)
    comp_df = pd.DataFrame(comp_rows).sort_values(["sample_id", "native_component_id"]).reset_index(drop=True)
    assert len(case_df) == 103 and len(comp_df) == 152, (len(case_df), len(comp_df))

    total = len(prop_df); hitc = int(prop_df.overlaps_any_gt_pixel.sum()); bhitc = int(prop_df.overlaps_any_gt_bbox.sum())
    P = hitc / total if total else 0.0
    bP = bhitc / total if total else 0.0
    tiny = comp_df[comp_df.size_stratum == "TINY"]
    tiny90 = float(tiny.covered90.mean()); overall90 = float(comp_df.covered90.mean())
    recall50 = float(comp_df.covered50.mean()); anyov = float(comp_df.any_overlap.mean())
    mean_cov = float(comp_df.coverage_fraction.mean())
    sc = prop_df.proposal_score.to_numpy(); hh = prop_df.overlaps_any_gt_pixel.astype(int).to_numpy()
    smax = float(sc.max()) if sc.size else float("nan")

    def roc(y, s):
        n1 = int(y.sum()); n0 = len(y) - n1
        if n0 == 0 or n1 == 0:
            return float("nan")
        o = np.argsort(s, kind="mergesort"); r = np.empty(len(s)); r[o] = np.arange(1, len(s) + 1)
        r = pd.Series(r).groupby(pd.Series(s)).transform("mean").to_numpy()
        return float((r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n0 * n1))

    def pr(y, s):
        o = np.argsort(-s, kind="mergesort"); ys = y[o]
        tp = np.cumsum(ys); fp = np.cumsum(1 - ys)
        prec = tp / np.maximum(tp + fp, 1); rec = tp / max(int(tp[-1]), 1)
        t = np.trapezoid if hasattr(np, "trapezoid") else np.trapz
        return float(t(prec, rec))

    cohort = {}
    for name, mask in (("hard_tiny", comp_df.hard_tiny), ("global_empty", comp_df.global_empty_image)):
        g = comp_df[mask]
        cohort[name] = {"n": len(g), "covered90": int(g.covered90.sum()),
                        "covered90_rate": float(g.covered90.mean()) if len(g) else None,
                        "any_overlap": int(g.any_overlap.sum())}
    multi = comp_df.groupby("sample_id").size()
    multi_ids = set(multi[multi > 1].index)
    mg = comp_df[comp_df.sample_id.isin(multi_ids)]
    cohort["multi_component"] = {"n": len(mg), "covered90": int(mg.covered90.sum()),
                                 "covered90_rate": float(mg.covered90.mean()) if len(mg) else None}

    strat = []
    for st in STRATA + ["ALL"]:
        g = comp_df if st == "ALL" else comp_df[comp_df.size_stratum == st]
        strat.append({"stratum": st, "n_components": len(g),
                      "covered90_count": int(g.covered90.sum()),
                      "covered90_rate": float(g.covered90.mean()) if len(g) else np.nan,
                      "covered50_count": int(g.covered50.sum()),
                      "covered50_rate": float(g.covered50.mean()) if len(g) else np.nan,
                      "any_overlap_count": int(g.any_overlap.sum()),
                      "any_overlap_rate": float(g.any_overlap.mean()) if len(g) else np.nan,
                      "mean_coverage": float(g.coverage_fraction.mean()) if len(g) else np.nan,
                      "mean_component_pixels": float(g.component_pixels.mean()) if len(g) else np.nan})

    metrics = {
        "proposal_total_count": total, "proposal_count_per_image": total / len(case_df),
        "proposal_pixel_hit_count": hitc, "proposal_bbox_hit_count": bhitc,
        "proposal_pixel_any_hit_precision": P, "proposal_bbox_any_hit_precision": bP,
        "tiny_recall90": tiny90, "overall_recall90": overall90,
        "overall_recall50": recall50, "any_overlap_recall": anyov, "mean_coverage": mean_cov,
        "mean_proposal_union_area": float(case_df.proposal_union_area_fraction.mean()),
        "score_mean": float(sc.mean()) if sc.size else None,
        "score_median": float(np.median(sc)) if sc.size else None,
        "score_q25": float(np.percentile(sc, 25)) if sc.size else None,
        "score_q75": float(np.percentile(sc, 75)) if sc.size else None,
        "score_max": smax,
        "score_iqr": float(np.percentile(sc, 75) - np.percentile(sc, 25)) if sc.size else None,
        "score_std": float(sc.std()) if sc.size else None,
        "distinct_score_values": int(len(np.unique(sc))) if sc.size else 0,
        "fraction_exactly_at_max": float(np.mean(sc >= smax - 1e-12)) if sc.size else None,
        "roc_auc_score_to_pixel_any_hit": roc(hh, sc), "pr_auc_score_to_pixel_any_hit": pr(hh, sc),
        "hard_tiny": cohort["hard_tiny"], "global_empty": cohort["global_empty"],
        "multi_component": cohort["multi_component"],
    }

    prop_df.to_csv(TABLES / "post_phase13_h2c_best_checkpoint_proposals.csv", index=False)
    case_df.to_csv(TABLES / "post_phase13_h2c_best_checkpoint_case_proposals.csv", index=False)
    comp_df.to_csv(TABLES / "post_phase13_h2c_best_checkpoint_component_coverage.csv", index=False)
    pd.DataFrame(strat).to_csv(TABLES / "post_phase13_h2c_best_checkpoint_size_stratified.csv", index=False)

    # ---------------- SEC 17: 3-way descriptive comparison ----------------
    h2a = json.loads((AUDITS / "post_phase13_h2a_best_checkpoint_standalone_evaluation.json").read_text("utf-8"))["metrics"]
    p13_prop = pd.read_csv(TABLES / "phase13_part1c_best_checkpoint_proposals.csv")
    p13_comp = pd.read_csv(TABLES / "phase13_part1c_best_checkpoint_component_coverage.csv")
    p13_case = pd.read_csv(TABLES / "phase13_part1c_best_checkpoint_case_proposals.csv")
    p13_total = len(p13_prop)
    p13_smax = float(p13_prop.proposal_score.max())
    p13 = {
        "proposal_total_count": p13_total,
        "proposal_pixel_any_hit_precision": float(p13_prop.overlaps_any_gt_pixel.sum()) / p13_total,
        "proposal_bbox_any_hit_precision": float(p13_prop.overlaps_any_gt_bbox.sum()) / p13_total,
        "tiny_recall90": float(p13_comp[p13_comp.size_stratum == "TINY"].bbox_covered90.mean()),
        "overall_recall90": float(p13_comp.bbox_covered90.mean()),
        "overall_recall50": float(p13_comp.bbox_covered50.mean()),
        "any_overlap_recall": float(p13_comp.bbox_any_overlap.mean()),
        "mean_coverage": float(p13_comp.bbox_coverage_fraction.mean()),
        "mean_proposal_union_area": float(p13_case.proposal_union_area_fraction.mean()),
        "score_max": p13_smax,
        "score_iqr": float(np.percentile(p13_prop.proposal_score, 75) - np.percentile(p13_prop.proposal_score, 25)),
        "fraction_exactly_at_max": float((p13_prop.proposal_score >= p13_smax - 1e-12).mean()),
    }
    rows = []
    for q in ["proposal_total_count", "proposal_pixel_any_hit_precision",
              "proposal_bbox_any_hit_precision", "tiny_recall90", "overall_recall90",
              "overall_recall50", "any_overlap_recall", "mean_coverage",
              "mean_proposal_union_area", "score_max", "score_iqr", "fraction_exactly_at_max",
              "roc_auc_score_to_pixel_any_hit", "pr_auc_score_to_pixel_any_hit"]:
        rows.append({"quantity": q, "phase13_best_epoch53": p13.get(q),
                     "h2a_best_epoch83": h2a.get(q), "h2c_best": metrics.get(q),
                     "delta_h2c_minus_h2a": (metrics[q] - h2a[q]) if (q in metrics and q in h2a) else None,
                     "delta_h2c_minus_phase13": (metrics[q] - p13[q]) if (q in metrics and q in p13) else None})
    cmp_df = pd.DataFrame(rows)
    cmp_df.to_csv(TABLES / "post_phase13_h2c_vs_h2a_vs_phase13_localizer_comparison.csv", index=False)

    obj = {
        "artifact": "POST_PHASE13_H2C_BEST_CHECKPOINT_STANDALONE_EVALUATION",
        "status": "COMPLETE", "created_utc": "2026-09-23T16:42:00Z",
        "h2c_experiment_id": H2C_ID,
        "checkpoint": str(H2C_CK.relative_to(ROOT)).replace("\\", "/"),
        "checkpoint_sha": sha(H2C_CK),
        "head": "SPATIAL_DISCRIMINATIVE_HEAD_3X3_RELU_1X1_V1",
        "population": {"val_cases": 103, "val_components": 152, "roi": "EXCLUDED"},
        "proposal_configuration": {"threshold": THRESHOLD, "margin": MARGIN, "top_k": TOP_K,
                                   "nms_iou": NMS_IOU, "grid": "NONE", "threshold_tuning": "NONE"},
        "metrics": metrics, "head_statistics": hstats, "size_stratified": strat,
        "comparison": {"reference": "frozen H2A best + frozen Phase13 best",
                       "rows": rows,
                       "language": "DESCRIPTIVE_SINGLE_SEED__NO_WINNER__NO_SUPERIORITY__NO_SIGNIFICANCE"},
        "downstream_segmentation": "NOT_RUN (explicit stop boundary)",
        "counters": {"training": 0, "optimizer": 0, "downstream_segmentation_model_constructions": 0,
                     "downstream_segmentation_forwards": 0, "proposal_grid": 0, "oracle_reruns": 0,
                     "test_reads": 0, "external_test_reads": 0},
    }
    (AUDITS / "post_phase13_h2c_best_checkpoint_standalone_evaluation.json").write_text(
        json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("=== H2C best-checkpoint standalone evaluation ===")
    for k in ("proposal_total_count", "proposal_count_per_image", "proposal_pixel_hit_count",
              "proposal_pixel_any_hit_precision", "proposal_bbox_any_hit_precision",
              "tiny_recall90", "overall_recall90", "overall_recall50", "any_overlap_recall",
              "mean_coverage", "mean_proposal_union_area", "score_max", "score_iqr",
              "fraction_exactly_at_max", "roc_auc_score_to_pixel_any_hit",
              "pr_auc_score_to_pixel_any_hit"):
        print(f"  {k}: {metrics[k]}")
    print("  cohorts:", json.dumps(cohort))
    print("  head stats:", json.dumps(hstats))
    print("\n=== 3-way comparison ===")
    print(cmp_df.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
