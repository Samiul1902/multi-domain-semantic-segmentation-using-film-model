"""PHASE-13 PART-1C — derived tables + reproduction gate + audit.

Reads the frozen Part-1C tables produced by the single authorized inference pass
and derives: stratified coverage, special cohorts, uncovered inventory, historical
provenance context, and the evaluation audit with the reproduction gate.

No inference. No training. No grid. No regional segmentation. No gate decision.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

EXP = "phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_clean_v3"
TABLES = ROOT / "reports" / "tables"
AUDITS = ROOT / "reports" / "audits"
TOL = 1e-12

EXPECTED_BBOX = {
    "tiny_recall90": 0.6805555555555556,
    "overall_recall90": 0.5986842105263158,
    "mean_roi_area_fraction": 0.004846047236646169,
    "hard_tiny_recovered90": 4,
    "global_empty_images_covered90": 1,
    "multi_component_recall90": 0.5714285714285714,
    "mean_proposals_per_image": 4.796116504854369,
    "overall_recall50": 0.7894736842105263,
    "any_overlap_recall": 0.8486842105263158,
    "mean_coverage": 0.7584022780771768,
}
EXPECTED_PIXEL = {
    "tiny_recall90": 0.6944444444444444,
    "overall_recall90": 0.6644736842105263,
    "hard_tiny_recovered90": 5,
    "global_empty_images_covered90": 1,
    "multi_component_recall90": 0.6224489795918368,
    "overall_recall50": 0.8026315789473685,
    "any_overlap_recall": 0.8486842105263158,
    "mean_coverage": 0.7768993431799454,
}
HIST_V2 = {
    "val_images": 106, "val_components": 156, "tiny": 73,
    "tiny_recall90": 0.726027397260274, "overall_recall90": 0.6410256410256411,
    "hard_tiny": "7 / 16", "global_empty": "3 / 7",
    "mean_roi_area_fraction": 0.005898906179948982,
    "mean_proposals_per_image": 4.660377358490566,
}


def sha(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _rate(series) -> float:
    return float(series.mean()) if len(series) else 0.0


def main() -> int:
    case = pd.read_csv(TABLES / "phase13_part1c_best_checkpoint_case_proposals.csv")
    prop = pd.read_csv(TABLES / "phase13_part1c_best_checkpoint_proposals.csv")
    comp = pd.read_csv(TABLES / "phase13_part1c_best_checkpoint_component_coverage.csv")

    assert len(case) == 103 and len(comp) == 152, (len(case), len(comp))
    assert len(prop) == 494, len(prop)

    # ---- stratified -------------------------------------------------------
    rows = []
    for stratum in ["TINY", "SMALL", "MEDIUM", "LARGE", "ALL"]:
        s = comp if stratum == "ALL" else comp[comp.size_stratum == stratum]
        b, p = s["bbox_coverage_fraction"], s["pixel_coverage_fraction"]
        rows.append({
            "stratum": stratum, "n_components": len(s),
            "bbox_covered90_count": int(s["bbox_covered90"].sum()),
            "bbox_covered90_rate": _rate(s["bbox_covered90"]),
            "bbox_covered50_count": int(s["bbox_covered50"].sum()),
            "bbox_covered50_rate": _rate(s["bbox_covered50"]),
            "bbox_any_overlap_count": int(s["bbox_any_overlap"].sum()),
            "bbox_any_overlap_rate": _rate(s["bbox_any_overlap"]),
            "bbox_mean_coverage": float(b.mean()) if len(s) else 0.0,
            "bbox_median_coverage": float(b.median()) if len(s) else 0.0,
            "bbox_q25_coverage": float(b.quantile(0.25)) if len(s) else 0.0,
            "bbox_q75_coverage": float(b.quantile(0.75)) if len(s) else 0.0,
            "pixel_covered90_count": int(s["pixel_covered90"].sum()),
            "pixel_covered90_rate": _rate(s["pixel_covered90"]),
            "pixel_covered50_count": int(s["pixel_covered50"].sum()),
            "pixel_covered50_rate": _rate(s["pixel_covered50"]),
            "pixel_any_overlap_count": int(s["pixel_any_overlap"].sum()),
            "pixel_any_overlap_rate": _rate(s["pixel_any_overlap"]),
            "pixel_mean_coverage": float(p.mean()) if len(s) else 0.0,
            "pixel_median_coverage": float(p.median()) if len(s) else 0.0,
            "pixel_q25_coverage": float(p.quantile(0.25)) if len(s) else 0.0,
            "pixel_q75_coverage": float(p.quantile(0.75)) if len(s) else 0.0,
        })
    pd.DataFrame(rows).to_csv(TABLES / "phase13_part1c_size_stratified_coverage.csv", index=False)

    # ---- special cohorts --------------------------------------------------
    multi_ids = set(comp.groupby("sample_id").size().loc[lambda v: v > 1].index)
    hard = comp[comp.hard_tiny]
    empty_ids = set(comp[comp.global_empty_image].sample_id)
    multi = comp[comp.sample_id.isin(multi_ids)]
    cohort_rows = []
    for name, s, unit in [
        ("hard_tiny", hard, "COMPONENT"),
        ("global_empty", comp[comp.sample_id.isin(empty_ids)], "IMAGE"),
        ("multi_component", multi, "COMPONENT"),
    ]:
        if unit == "IMAGE":
            n = len(empty_ids)
            b90 = len({r.sample_id for r in s.itertuples() if r.bbox_covered90})
            p90 = len({r.sample_id for r in s.itertuples() if r.pixel_covered90})
            b_den = p_den = n
        else:
            b_den = p_den = len(s)
            b90 = int(s["bbox_covered90"].sum()); p90 = int(s["pixel_covered90"].sum())
        cohort_rows.append({
            "cohort": name, "denominator_unit": unit, "denominator": b_den,
            "bbox_covered90_count": b90, "bbox_covered90_rate": (b90 / b_den if b_den else 0.0),
            "pixel_covered90_count": p90, "pixel_covered90_rate": (p90 / p_den if p_den else 0.0),
        })
    pd.DataFrame(cohort_rows).to_csv(TABLES / "phase13_part1c_special_cohort_coverage.csv", index=False)

    # ---- uncovered inventory ---------------------------------------------
    unc = comp[~comp["bbox_covered90"]].copy()
    pc = case.set_index("sample_id")["proposal_count"].to_dict()
    mx = {}
    for sid, grp in prop.groupby("sample_id"):
        mx[sid] = float(grp["proposal_score"].max()) if len(grp) else 0.0
    unc["proposal_count"] = unc["sample_id"].map(pc).fillna(0).astype(int)
    unc["max_proposal_score"] = unc["sample_id"].map(mx).fillna(0.0)
    unc_out = unc[[
        "sample_id", "native_component_id", "size_stratum", "hard_tiny",
        "global_empty_image", "bbox_coverage_fraction", "pixel_coverage_fraction",
        "proposal_count", "max_proposal_score", "component_ratio",
    ]].rename(columns={"native_component_id": "component_id"})
    unc_out.to_csv(TABLES / "phase13_part1c_uncovered_components.csv", index=False)

    # ---- historical provenance context ------------------------------------
    ctx = pd.DataFrame([
        {"population": "historical_phase4_v2", "val_images": HIST_V2["val_images"],
         "val_components": HIST_V2["val_components"], "tiny": HIST_V2["tiny"],
         "tiny_recall90": HIST_V2["tiny_recall90"],
         "overall_recall90": HIST_V2["overall_recall90"],
         "hard_tiny": HIST_V2["hard_tiny"], "global_empty": HIST_V2["global_empty"],
         "mean_roi_area_fraction": HIST_V2["mean_roi_area_fraction"],
         "mean_proposals_per_image": HIST_V2["mean_proposals_per_image"]},
        {"population": "clean_v3_part1c", "val_images": 103, "val_components": 152,
         "tiny": 72, "tiny_recall90": 49 / 72, "overall_recall90": 91 / 152,
         "hard_tiny": "4 / 15", "global_empty": "1 / 5",
         "mean_roi_area_fraction": float(case["proposal_union_area_fraction"].mean()),
         "mean_proposals_per_image": float(case["proposal_count"].mean())},
    ])
    ctx["comparison_label"] = "DIFFERENT_POPULATIONS_DESCRIPTIVE_PROVENANCE_ONLY"
    ctx.to_csv(TABLES / "phase13_part1c_historical_context.csv", index=False)

    # ---- aggregate metrics ------------------------------------------------
    bbox = {
        "tiny_recall90": _rate(comp[comp.size_stratum == "TINY"]["bbox_covered90"]),
        "overall_recall90": _rate(comp["bbox_covered90"]),
        "mean_roi_area_fraction": float(case["proposal_union_area_fraction"].mean()),
        "hard_tiny_recovered90": int(hard["bbox_covered90"].sum()),
        "global_empty_images_covered90": len({r.sample_id for r in comp[comp.sample_id.isin(empty_ids)].itertuples() if r.bbox_covered90}),
        "multi_component_recall90": _rate(multi["bbox_covered90"]),
        "mean_proposals_per_image": float(case["proposal_count"].mean()),
        "overall_recall50": _rate(comp["bbox_covered50"]),
        "any_overlap_recall": _rate(comp["bbox_any_overlap"]),
        "mean_coverage": float(comp["bbox_coverage_fraction"].mean()),
    }
    pixel = {
        "tiny_recall90": _rate(comp[comp.size_stratum == "TINY"]["pixel_covered90"]),
        "overall_recall90": _rate(comp["pixel_covered90"]),
        "hard_tiny_recovered90": int(hard["pixel_covered90"].sum()),
        "global_empty_images_covered90": len({r.sample_id for r in comp[comp.sample_id.isin(empty_ids)].itertuples() if r.pixel_covered90}),
        "multi_component_recall90": _rate(multi["pixel_covered90"]),
        "overall_recall50": _rate(comp["pixel_covered50"]),
        "any_overlap_recall": _rate(comp["pixel_any_overlap"]),
        "mean_coverage": float(comp["pixel_coverage_fraction"].mean()),
    }

    mismatches = []
    for k, v in EXPECTED_BBOX.items():
        if abs(bbox[k] - v) > TOL:
            mismatches.append(f"bbox.{k}: got {bbox[k]!r} expected {v!r}")
    for k, v in EXPECTED_PIXEL.items():
        if abs(pixel[k] - v) > TOL:
            mismatches.append(f"pixel.{k}: got {pixel[k]!r} expected {v!r}")
    if len(prop) != 494:
        mismatches.append(f"total proposals: {len(prop)} != 494")

    precision = {
        "proposal_bbox_any_hit_precision": float(prop["overlaps_any_gt_bbox"].mean()),
        "proposal_pixel_any_hit_precision": float(prop["overlaps_any_gt_pixel"].mean()),
        "role": "DESCRIPTIVE_ONLY_NOT_SELECTION_NOT_GATE_NOT_TUNED",
    }

    disagreement = {
        "covered90_disagreements": int((comp["bbox_covered90"] != comp["pixel_covered90"]).sum()),
        "covered50_disagreements": int((comp["bbox_covered50"] != comp["pixel_covered50"]).sum()),
        "any_overlap_disagreements": int((comp["bbox_any_overlap"] != comp["pixel_any_overlap"]).sum()),
        "mean_bbox_minus_pixel": float(comp["bbox_minus_pixel_coverage"].mean()),
        "median_bbox_minus_pixel": float(comp["bbox_minus_pixel_coverage"].median()),
        "largest_positive": float(comp["bbox_minus_pixel_coverage"].max()),
        "largest_negative": float(comp["bbox_minus_pixel_coverage"].min()),
        "by_stratum_mean": {s: float(comp[comp.size_stratum == s]["bbox_minus_pixel_coverage"].mean())
                            for s in ["TINY", "SMALL", "MEDIUM", "LARGE"]},
    }

    payload = {
        "artifact": "PHASE13_PART1C_BEST_CHECKPOINT_PROPOSAL_EVALUATION",
        "created_utc": datetime.datetime.utcnow().isoformat() + "Z",
        "experiment_id": EXP,
        "checkpoint_path": str(ROOT / "checkpoints" / EXP / "best.pt"),
        "checkpoint_sha": sha(ROOT / "checkpoints" / EXP / "best.pt"),
        "checkpoint_epoch": 53,
        "lineage": "R2 + R2A + NON_SCIENTIFIC_PROVENANCE_BINDING + R2B(provenance) + R2C",
        "manifest": "phase4_v3", "taxonomy": "kub_size_clean_v3_v1",
        "val_images": 103, "val_components": 152,
        "strata": {"TINY": 72, "SMALL": 28, "MEDIUM": 36, "LARGE": 16},
        "proposal_config": {"threshold": 0.10, "margin": 0.20, "top_k": 5, "nms_iou": 0.30},
        "heatmap_contract": {"input": 512, "output": 128},
        "primary_coverage": "HISTORICAL_EXECUTING_BBOX_COVERAGE",
        "secondary_sensitivity": "PIXEL_MASK_COMPONENT_COVERAGE",
        "bbox_metrics": bbox, "pixel_metrics": pixel,
        "total_proposals": int(len(prop)),
        "proposal_any_hit_precision": precision,
        "stratified_summary": rows,
        "special_cohorts": cohort_rows,
        "bbox_pixel_disagreement": disagreement,
        "uncovered_component_count": int(len(unc_out)),
        "reproduction_gate": {
            "expected_bbox": EXPECTED_BBOX, "expected_pixel": EXPECTED_PIXEL,
            "expected_total_proposals": 494,
            "mismatches": mismatches,
            "tolerance": TOL,
            "status": "PASS" if not mismatches else "CHECK_REQUIRED",
        },
        "new_full_val_inference_passes": 1,
        "model_constructions": 1,
        "training": 0, "optimizer": 0, "grid_configs": 0,
        "test_reads": 0, "regional_segmentation": 0,
        "gate_decision": "NOT_DECIDED",
    }
    payload["status"] = payload["reproduction_gate"]["status"]
    (AUDITS / "phase13_part1c_best_checkpoint_proposal_evaluation.json").write_text(
        json.dumps(payload, indent=2, default=str), encoding="utf-8")

    print("reproduction mismatches:", len(mismatches))
    for m in mismatches:
        print("  -", m)
    print("bbox:", json.dumps({k: round(v, 6) if isinstance(v, float) else v for k, v in bbox.items()}))
    print("pixel:", json.dumps({k: round(v, 6) if isinstance(v, float) else v for k, v in pixel.items()}))
    print("precision:", precision["proposal_bbox_any_hit_precision"], precision["proposal_pixel_any_hit_precision"])
    print("disagreement:", disagreement["covered90_disagreements"], disagreement["covered50_disagreements"], disagreement["any_overlap_disagreements"])
    print("uncovered:", len(unc_out))
    print("STATUS:", payload["status"])
    return 0 if not mismatches else 1


if __name__ == "__main__":
    raise SystemExit(main())
