"""H2-A-B1 §16-§18 — standalone best-checkpoint proposal evaluation + Phase-13 comparison.

Loads the H2A best.pt ONLY, runs exactly ONE deterministic fixed-config VAL proposal evaluation
(103 cases / 152 components), writes the four standalone tables, and compares against the FROZEN
Phase-13 Part-1C best-checkpoint tables (no Phase-13 re-inference).

NO downstream segmentation. NO proposal grid. NO threshold tuning. NO TEST access.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch

ROOT = Path(r"D:\Softfors\jup")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
TABLES = ROOT / "reports" / "tables"
AUDITS = ROOT / "reports" / "audits"
H2A_ID = "post_phase13_h2a_kub_localizer_r512_h128_sigmaeq075_centernetfocal_deploymentbalance_seed42_clean_v3"
H2A_CK = ROOT / "checkpoints" / H2A_ID / "best.pt"
THRESHOLD, MARGIN, TOP_K, NMS_IOU = 0.10, 0.20, 5, 0.30
INPUT_RESOLUTION, HEATMAP_RESOLUTION, BASE_CHANNELS = 512, 128, 16
STRATA = ["TINY", "SMALL", "MEDIUM", "LARGE"]


def sha(p) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


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

    # ---- VAL FULL_FIELD population (same frame the training used) ----
    from scripts.training.post_phase13_h2a_localizer_replay import _load_hard_sets  # noqa: E402
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
    load_training_checkpoint(H2A_CK, model, restore_rng=False, map_location=dev)
    model.eval()
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
    tiny = comp_df[comp_df.size_stratum == "TINY"]; over = comp_df
    tiny90 = float(tiny.covered90.mean()); overall90 = float(over.covered90.mean())
    recall50 = float(over.covered50.mean()); anyov = float(over.any_overlap.mean())
    mean_cov = float(over.coverage_fraction.mean())
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
        "score_max": smax, "score_iqr": float(np.percentile(sc, 75) - np.percentile(sc, 25)) if sc.size else None,
        "fraction_exactly_at_max": float(np.mean(sc >= smax - 1e-12)) if sc.size else None,
        "roc_auc_score_to_pixel_any_hit": roc(hh, sc), "pr_auc_score_to_pixel_any_hit": pr(hh, sc),
        "hard_tiny": cohort["hard_tiny"], "global_empty": cohort["global_empty"],
        "multi_component": cohort["multi_component"],
    }

    prop_df.to_csv(TABLES / "post_phase13_h2a_best_checkpoint_proposals.csv", index=False)
    case_df.to_csv(TABLES / "post_phase13_h2a_best_checkpoint_case_proposals.csv", index=False)
    comp_df.to_csv(TABLES / "post_phase13_h2a_best_checkpoint_component_coverage.csv", index=False)
    pd.DataFrame(strat).to_csv(TABLES / "post_phase13_h2a_best_checkpoint_size_stratified.csv", index=False)

    # ---------- §18 comparison vs FROZEN Phase-13 Part-1C tables ----------
    p13_prop = pd.read_csv(TABLES / "phase13_part1c_best_checkpoint_proposals.csv")
    p13_comp = pd.read_csv(TABLES / "phase13_part1c_best_checkpoint_component_coverage.csv")
    p13_case = pd.read_csv(TABLES / "phase13_part1c_best_checkpoint_case_proposals.csv")
    p13_total = len(p13_prop)
    p13_P = float(p13_prop.overlaps_any_gt_pixel.sum()) / p13_total if p13_total else 0.0
    p13_bP = float(p13_prop.overlaps_any_gt_bbox.sum()) / p13_total if p13_total else 0.0
    p13_tiny = p13_comp[p13_comp.size_stratum == "TINY"]
    p13_smax = float(p13_prop.proposal_score.max())
    cmp_rows = [
        ("proposal_total_count", p13_total, total, total - p13_total),
        ("proposal_pixel_any_hit_precision", p13_P, P, P - p13_P),
        ("proposal_bbox_any_hit_precision", p13_bP, bP, bP - p13_bP),
        ("tiny_recall90", float(p13_tiny.bbox_covered90.mean()), tiny90, tiny90 - float(p13_tiny.bbox_covered90.mean())),
        ("overall_recall90", float(p13_comp.bbox_covered90.mean()), overall90, overall90 - float(p13_comp.bbox_covered90.mean())),
        ("overall_recall50", float(p13_comp.bbox_covered50.mean()), recall50, recall50 - float(p13_comp.bbox_covered50.mean())),
        ("any_overlap_recall", float(p13_comp.bbox_any_overlap.mean()), anyov, anyov - float(p13_comp.bbox_any_overlap.mean())),
        ("mean_coverage", float(p13_comp.bbox_coverage_fraction.mean()), mean_cov, mean_cov - float(p13_comp.bbox_coverage_fraction.mean())),
        ("mean_proposal_union_area", float(p13_case.proposal_union_area_fraction.mean()),
         float(case_df.proposal_union_area_fraction.mean()),
         float(case_df.proposal_union_area_fraction.mean()) - float(p13_case.proposal_union_area_fraction.mean())),
        ("proposal_score_max", p13_smax, smax, (smax - p13_smax) if smax == smax else None),
        ("fraction_exactly_at_max", float((p13_prop.proposal_score >= p13_smax - 1e-12).mean()),
         float(np.mean(sc >= smax - 1e-12)), float(np.mean(sc >= smax - 1e-12)) - float((p13_prop.proposal_score >= p13_smax - 1e-12).mean())),
        ("proposal_count_per_image", p13_total / 103, total / len(case_df), total / len(case_df) - p13_total / 103),
    ]
    cmp_df = pd.DataFrame(cmp_rows, columns=["quantity", "phase13_best_epoch53", "h2a_best_epoch83", "delta_h2a_minus_phase13"])
    cmp_df.to_csv(TABLES / "post_phase13_h2a_vs_phase13_localizer_comparison.csv", index=False)

    obj = {
        "artifact": "POST_PHASE13_H2A_BEST_CHECKPOINT_STANDALONE_EVALUATION",
        "status": "COMPLETE", "created_utc": "2026-09-22T16:30:00Z", "h2a_experiment_id": H2A_ID,
        "checkpoint": str(H2A_CK.relative_to(ROOT)).replace("\\", "/"), "checkpoint_sha": sha(H2A_CK),
        "population": {"val_cases": 103, "val_components": 152, "roi": "EXCLUDED"},
        "proposal_configuration": {"threshold": THRESHOLD, "margin": MARGIN, "top_k": TOP_K, "nms_iou": NMS_IOU,
                                   "grid": "NONE", "threshold_tuning": "NONE"},
        "metrics": metrics,
        "size_stratified": strat,
        "phase13_comparison": {
            "reference": "FROZEN Phase-13 Part-1C best-checkpoint tables (epoch 53); no Phase-13 re-inference",
            "phase13_proposals_sha": sha(TABLES / "phase13_part1c_best_checkpoint_proposals.csv"),
            "phase13_component_sha": sha(TABLES / "phase13_part1c_best_checkpoint_component_coverage.csv"),
            "rows": [{"quantity": a, "phase13": b, "h2a": c, "delta": d} for a, b, c, d in cmp_rows],
            "language": "DESCRIPTIVE_DEVELOPMENT_COMPARISON__NO_SUPERIORITY_CLAIM__NO_SIGNIFICANCE_CLAIM",
        },
        "downstream_segmentation": "NOT_RUN (explicit stop boundary)",
        "counters": {"training": 0, "optimizer": 0, "downstream_segmentation_model_constructions": 0,
                     "downstream_segmentation_forwards": 0, "proposal_grid": 0, "oracle_reruns": 0,
                     "test_reads": 0, "external_test_reads": 0},
    }
    (AUDITS / "post_phase13_h2a_best_checkpoint_standalone_evaluation.json").write_text(
        json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("=== H2A best-checkpoint standalone evaluation ===")
    for k in ("proposal_total_count", "proposal_count_per_image", "proposal_pixel_hit_count",
              "proposal_pixel_any_hit_precision", "proposal_bbox_any_hit_precision",
              "tiny_recall90", "overall_recall90", "overall_recall50", "any_overlap_recall",
              "mean_coverage", "mean_proposal_union_area", "score_max", "score_iqr",
              "fraction_exactly_at_max", "roc_auc_score_to_pixel_any_hit", "pr_auc_score_to_pixel_any_hit"):
        print(f"  {k}: {metrics[k]}")
    print("  cohorts:", json.dumps(cohort))
    print("\n=== §18 comparison vs Phase-13 epoch 53 ===")
    print(cmp_df.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
