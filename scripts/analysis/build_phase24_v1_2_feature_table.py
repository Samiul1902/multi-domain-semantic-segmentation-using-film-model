"""Post-Phase24 repair -- build the additive v1.2 primary feature-set table."""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
TAB = ROOT / "reports" / "tables"

K = 32
GROUPS = [
    ("bridge_global", "bridge", "GLOBAL", 256, "spatial mean over all cells"),
    ("bridge_roi", "bridge", "ROI", 256, "spatial mean over mapped ROI cells"),
    ("decoder2_global", "decoder2", "GLOBAL", 48, "spatial mean over all cells"),
    ("decoder2_roi", "decoder2", "ROI", 48, "spatial mean over mapped ROI cells"),
    ("decoder1_global", "decoder1", "GLOBAL", 24, "spatial mean over all cells"),
    ("decoder1_roi", "decoder1", "ROI", 24, "spatial mean over mapped ROI cells"),
]

SCALARS = [
    ("entropy_proxy_mean", "probability_entropy_summaries", "THRESHOLD_FREE", "",
     "mean over N pixels of -[q ln q + (1-q) ln(1-q)]/ln2, q=clip(P,1e-7,1-1e-7)",
     "dimensionless [0,1]", "P (512x512 float32)"),
    ("frac_prob_within_0p05_of_boundary", "predicted_boundary_area_statistics",
     "SEGMENTATION_OUTPUT_PROBABILITY_BOUNDARY", "0.50",
     "(1/N) sum 1[|P-0.50|<=0.05]", "fraction [0,1]", "P"),
    ("frac_prob_within_0p02_of_boundary", "predicted_boundary_area_statistics",
     "SEGMENTATION_OUTPUT_PROBABILITY_BOUNDARY", "0.50",
     "(1/N) sum 1[|P-0.50|<=0.02]", "fraction [0,1]", "P"),
    ("mean_boundary_margin", "probability_margin_summaries",
     "SEGMENTATION_OUTPUT_PROBABILITY_BOUNDARY", "0.50",
     "mean over N pixels of |P-0.50| (not negated)", "probability distance [0,0.5]", "P"),
    ("pred_foreground_pixels", "predicted_foreground_fraction", "ROI_PROPOSAL", "0.30",
     "sum M_roi, M_roi=1[P>=0.30]", "pixels on 512x512 canvas", "P"),
    ("pred_foreground_fraction", "predicted_foreground_fraction", "ROI_PROPOSAL", "0.30",
     "pred_foreground_pixels / N", "fraction [0,1]", "P"),
    ("pred_roi_exists", "predicted_component_count", "ROI_PROPOSAL", "0.30",
     "1.0 if pred_foreground_pixels>0 else 0.0", "binary indicator", "P"),
    ("pred_empty", "predicted_component_count", "ROI_PROPOSAL", "0.30",
     "1.0 - pred_roi_exists", "binary indicator", "P"),
    ("predicted_roi_side", "predicted_bbox_width_height", "ROI_PROPOSAL", "0.30",
     "canonical cache field crop_side_pixels", "pixels on 512 canvas", "ROI030 crop metadata"),
    ("predicted_roi_area_fraction", "predicted_roi_fraction", "ROI_PROPOSAL", "0.30",
     "(crop_side_pixels^2)/(512^2)", "DECLARED fraction; MEASURED [0,2.25] -- DEFECT",
     "ROI030 crop metadata"),
]

FIELDS = ["index_or_group", "feature_name", "feature_group", "native_source", "native_width",
          "pool_scope", "reduction_operation", "output_width", "formula", "threshold_role",
          "threshold_value", "uses_GT", "pre_refinement", "inference_available", "dtype",
          "units", "notes"]


def main() -> int:
    rows = []
    base = 0
    for name, tap, scope, C, pool in GROUPS:
        rows.append({
            "index_or_group": f"[{base}:{base+K}]",
            "feature_name": f"{name}[0:{K}]",
            "feature_group": "deep",
            "native_source": f"global MedFiLM {tap} tap",
            "native_width": C,
            "pool_scope": scope,
            "reduction_operation": "DETERMINISTIC_CHANNEL_ADAPTIVE_AVG_POOL_1D_V1",
            "output_width": K,
            "formula": (f"v[c]={pool}; then z[j]=mean(v[floor(j*C/32):ceil((j+1)*C/32)])"),
            "threshold_role": "NONE",
            "threshold_value": "",
            "uses_GT": "false",
            "pre_refinement": "true",
            "inference_available": "true",
            "dtype": "float32",
            "units": "deep feature",
            "notes": f"native C={C}; non-trainable; uses every source channel",
        })
        base += K

    for i, (nm, grp, role, tv, formula, units, src) in enumerate(SCALARS):
        rows.append({
            "index_or_group": f"[{192+i}]",
            "feature_name": nm,
            "feature_group": "scalar",
            "native_source": src,
            "native_width": 1,
            "pool_scope": "N/A",
            "reduction_operation": "NONE",
            "output_width": 1,
            "formula": formula,
            "threshold_role": role,
            "threshold_value": tv,
            "uses_GT": "false",
            "pre_refinement": "true",
            "inference_available": "true",
            "dtype": "float32",
            "units": units,
            "notes": ("DEFECT REPORTED -- see phase24_scalar_feature_contract_v1_2.json"
                      if nm == "predicted_roi_area_fraction" else ""),
        })

    out = TAB / "phase24_router_primary_feature_set_v1_2.csv"
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)

    print(f"wrote {out} ({len(rows)} rows)")
    print(f"  deep rows: {sum(1 for r in rows if r['feature_group']=='deep')}")
    print(f"  scalar rows: {sum(1 for r in rows if r['feature_group']=='scalar')}")
    print(f"  columns: {len(FIELDS)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
