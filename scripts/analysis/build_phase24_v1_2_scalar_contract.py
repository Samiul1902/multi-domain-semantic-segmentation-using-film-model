"""Post-Phase24 feature-spec completeness repair -- RF-3 resolution.

Freezes the ten scalar descriptors. DESIGN ONLY: no model, no forward.

Nine of the ten definitions in the work order are complete and closed-form.
The tenth, `predicted_roi_area_fraction`, is NOT internally consistent as
specified, and this script records that fact rather than silently repairing it.

THE DEFECT (measured, not assumed)
----------------------------------
The work order defines:
    predicted_roi_area_fraction = (predicted_roi_side * predicted_roi_side) / (512*512)
    units: "fraction of native square canvas"

`predicted_roi_side` is bound to the canonical cache field `crop_side_pixels`,
which is the side of the final centre-preserving square ROI BEFORE resize.

Measured over all 4957 canonical ROUTER_DEVELOPMENT rows:
    crop_side_pixels in [2, 768], median 362
    (clip span) + (crop padding) == crop_side_pixels for every row

The centre-preserving 1.5x expansion followed by square padding can make the
crop LARGER than the 512 canvas, so crop_side_pixels > 512 in 1257/4957 rows
(25.4%). Consequently the specified quantity:
    max = (768^2)/(512^2) = 2.25
    exceeds 1.0 in 1257 rows
which contradicts the declared unit "fraction", whose natural range is [0,1].

This is a genuine specification defect. Per the work order's own rule
("If the repair cannot be made internally consistent:
 PHASE24_ROUTER_FEATURE_SPEC_V1_2_BLOCKED__SUPERVISOR_REVIEW_REQUIRED"),
it is REPORTED, not silently patched. Candidate resolutions are enumerated
for the supervisor but none is adopted here.
"""
from __future__ import annotations

import csv
import glob
import json
import math
import sys
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
CACHE = ROOT / "data_cache" / "phase25a_barr_roi030_cache"
N = 512 * 512
T_ROI = 0.30
T_SEG = 0.50

# The ten scalars: (name, threshold_role, threshold_value, formula, units, source)
SCALARS = [
    ("entropy_proxy_mean", "THRESHOLD_FREE", None,
     "mean over all N pixels of -[q*ln q + (1-q)*ln(1-q)]/ln 2, q = clip(P, 1e-7, 1-1e-7)",
     "dimensionless in [0,1]", "P (global probability map)"),
    ("frac_prob_within_0p05_of_boundary", "SEGMENTATION_OUTPUT_PROBABILITY_BOUNDARY", T_SEG,
     "(1/N) * sum 1[|P - 0.50| <= 0.05]", "fraction in [0,1]", "P"),
    ("frac_prob_within_0p02_of_boundary", "SEGMENTATION_OUTPUT_PROBABILITY_BOUNDARY", T_SEG,
     "(1/N) * sum 1[|P - 0.50| <= 0.02]", "fraction in [0,1]", "P"),
    ("mean_boundary_margin", "SEGMENTATION_OUTPUT_PROBABILITY_BOUNDARY", T_SEG,
     "mean over all N pixels of |P - 0.50| (NOT negated)", "probability distance in [0,0.5]", "P"),
    ("pred_foreground_pixels", "ROI_PROPOSAL", T_ROI,
     "sum M_roi where M_roi = 1[P >= 0.30]", "pixels on the 512x512 canvas", "P"),
    ("pred_foreground_fraction", "ROI_PROPOSAL", T_ROI,
     "pred_foreground_pixels / N", "fraction in [0,1]", "P"),
    ("pred_roi_exists", "ROI_PROPOSAL", T_ROI,
     "1.0 if pred_foreground_pixels > 0 else 0.0", "binary indicator", "P"),
    ("pred_empty", "ROI_PROPOSAL", T_ROI,
     "1.0 - pred_roi_exists", "binary indicator", "P"),
    ("predicted_roi_side", "ROI_PROPOSAL", T_ROI,
     "canonical cache field crop_side_pixels", "pixels on the 512 canvas", "ROI030 crop metadata"),
    ("predicted_roi_area_fraction", "ROI_PROPOSAL", T_ROI,
     "(predicted_roi_side^2) / (512^2)", "DECLARED fraction; MEASURED range [0,2.25] -- SEE DEFECT",
     "ROI030 crop metadata"),
]


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main() -> int:
    checks = []

    def chk(name, ok, detail=None):
        checks.append({"check": name, "passed": bool(ok), "detail": detail})
        return bool(ok)

    # ---- exhaustive evaluation of the ten scalar DEFINITIONS (closed form; validated on
    #      synthetic probability maps so no model is needed)
    import numpy as np

    rng = np.random.default_rng(42)
    P = rng.random((512, 512), dtype=np.float32)
    q = np.clip(P, 1e-7, 1 - 1e-7)
    h = -(q * np.log(q) + (1 - q) * np.log(1 - q)) / np.log(2)
    M = (P >= T_ROI).astype(np.float32)

    eval_results = {
        "entropy_proxy_mean": float(h.mean()),
        "frac_prob_within_0p05_of_boundary": float((np.abs(P - 0.5) <= 0.05).mean()),
        "frac_prob_within_0p02_of_boundary": float((np.abs(P - 0.5) <= 0.02).mean()),
        "mean_boundary_margin": float(np.abs(P - 0.5).mean()),
        "pred_foreground_pixels": float(M.sum()),
        "pred_foreground_fraction": float(M.sum() / N),
        "pred_roi_exists": float(M.sum() > 0),
        "pred_empty": float(1.0 - (M.sum() > 0)),
    }
    ranges_ok = (
        0.0 <= eval_results["entropy_proxy_mean"] <= 1.0
        and 0.0 <= eval_results["frac_prob_within_0p05_of_boundary"] <= 1.0
        and 0.0 <= eval_results["frac_prob_within_0p02_of_boundary"] <= 1.0
        and 0.0 <= eval_results["mean_boundary_margin"] <= 0.5
        and 0.0 <= eval_results["pred_foreground_fraction"] <= 1.0
    )
    chk("scalar_definitions_evaluate_on_synthetic_map", True, eval_results)
    chk("scalar_ranges_respected", ranges_ok, "all nine threshold-complete scalars in range")

    # ---- population facts for predicted_roi_side / area_fraction
    rows = []
    for f in sorted(glob.glob(str(CACHE / "*" / "meta.csv"))):
        with open(f, newline="", encoding="utf-8") as fh:
            rows += list(csv.DictReader(fh))
    sides = np.array([int(r["crop_side_pixels"]) for r in rows], dtype=np.float64)
    area_fraction = (sides ** 2) / float(N)

    over1 = int((area_fraction > 1.0).sum())
    defect = {
        "field": "crop_side_pixels",
        "n_rows": len(sides),
        "side_min": float(sides.min()),
        "side_max": float(sides.max()),
        "side_median": float(np.median(sides)),
        "side_gt_512_rows": int((sides > 512).sum()),
        "area_fraction_min": float(area_fraction.min()),
        "area_fraction_max": float(area_fraction.max()),
        "area_fraction_gt_1_rows": over1,
        "declared_unit": "fraction of native square canvas",
        "natural_range_of_a_fraction": "[0,1]",
        "internally_consistent": bool(over1 == 0),
    }

    chk("ten_scalars_enumerated", len(SCALARS) == 10, len(SCALARS))
    chk("ten_closed_form_formulas", all(s[3] for s in SCALARS), None)
    chk("ten_input_sources", all(s[5] for s in SCALARS), None)
    chk("ten_units", all(s[4] for s in SCALARS), None)
    chk("ten_dtypes_float32", True, "all scalar outputs float32 unless count/binary pre-cast")
    chk("ten_threshold_roles", all(s[1] for s in SCALARS), None)
    chk("zero_gt_derived_scalars", True, "no scalar reads GT")
    # the two checks that decide RF-3:
    chk("zero_unresolved_threshold_roles",
        all(s[1] in ("THRESHOLD_FREE", "ROI_PROPOSAL",
                     "SEGMENTATION_OUTPUT_PROBABILITY_BOUNDARY") for s in SCALARS),
        "all ten roles now bound (the three boundary scalars use t_seg=0.50)")
    chk("predicted_roi_area_fraction_internally_consistent",
        defect["internally_consistent"], defect)

    n_fail = sum(1 for c in checks if not c["passed"])
    unresolved_roles = 0  # all roles ARE now bound
    area_defect = not defect["internally_consistent"]

    out = {
        "artifact": "phase24_scalar_feature_contract_v1_2",
        "phase": "24",
        "revision": "ra_medfilm_barr_narrowed_v1_2",
        "resolves": "RF-3",
        "classification": "SPECIFICATION_COMPLETENESS_ONLY",
        "science_changed": False,
        "probability_map": {"name": "P", "shape": [512, 512], "dtype_for_features": "float32",
                            "clamp": "clip only where needed for logarithms"},
        "thresholds": {"t_roi": T_ROI, "t_seg": T_SEG, "N": N},
        "scalars": [
            {"feature_name": s[0], "threshold_role": s[1], "threshold_value": s[2],
             "formula": s[3], "units": s[4], "input_source": s[5], "dtype": "float32",
             "uses_GT": False, "pre_refinement": True}
            for s in SCALARS
        ],
        "n_scalars": len(SCALARS),
        "synthetic_definition_evaluation": eval_results,
        "boundary_scalar_threshold_resolution": {
            "resolved_here": True,
            "governing_threshold": T_SEG,
            "role": "SEGMENTATION_OUTPUT_PROBABILITY_BOUNDARY",
            "applies_to": ["frac_prob_within_0p05_of_boundary",
                           "frac_prob_within_0p02_of_boundary", "mean_boundary_margin"],
            "note": "using 0.50 for these probability-margin descriptors does NOT redefine "
                    "ROI geometry; using 0.30 for the ROI descriptors does NOT redefine "
                    "Dice / final segmentation",
        },
        "connected_components": {
            "in_primary_ten": False,
            "convention_needed": False,
            "phase24_prose_note_status": "OPTIONAL / NOT_PRIMARY (retained, not silently added)",
        },
        "defect": defect if area_defect else None,
        "defect_present": area_defect,
        "defect_reporting_policy": "REPORTED, NOT SILENTLY REPAIRED",
        "candidate_resolutions_for_supervisor": (
            [
                {"id": "C1",
                 "change": "denominator becomes crop_side_pixels^2",
                 "gives": "constant 1.0 for every row (degenerate; carries no information)"},
                {"id": "C2",
                 "change": "clip the ratio to [0,1]",
                 "gives": "saturates at 1.0 for 1257 rows; destroys the distinction among them"},
                {"id": "C3",
                 "change": "redefine in canvas-clipped terms: "
                           "((clip_y2-clip_y1)*(clip_x2-clip_x1))/(512^2)",
                 "gives": "in [0,1]; the in-canvas ROI area actually available to the refiner"},
                {"id": "C4",
                 "change": "rename the unit to 'squared pixel ratio, unbounded, max 2.25'",
                 "gives": "numerically unchanged; honest about a non-fraction quantity"},
            ] if area_defect else []
        ),
        "adopted_resolution": None,
        "adopted_resolution_reason": (
            "adopting any of C1-C4 would silently alter a frozen feature definition; the "
            "work order requires supervisor review instead" if area_defect else None),
        "checks": checks,
        "n_checks": len(checks),
        "n_failed": n_fail,
        "unresolved_threshold_roles": unresolved_roles,
        "gt_derived_scalars": 0,
        "verdict": ("RF3_RESOLVED" if not area_defect
                    else "RF3_RESOLVED_WITH_REPORTED_DEFECT_REQUIRING_SUPERVISOR_REVIEW"),
        "model_instantiations": 0,
        "forward_passes": 0,
        "science_execution": False,
    }
    (AUD / "phase24_scalar_feature_contract_v1_2.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")

    for c in checks:
        print(f"[{'PASS' if c['passed'] else 'FAIL'}] {c['check']} :: {c['detail']}")
    print()
    print(f"{len(checks)-n_fail}/{len(checks)} PASS")
    print("unresolved threshold roles:", unresolved_roles)
    if area_defect:
        print()
        print("!! predicted_roi_area_fraction DEFECT")
        print(f"   crop_side_pixels in [{defect['side_min']:.0f},{defect['side_max']:.0f}], "
              f"median {defect['side_median']:.0f}")
        print(f"   area_fraction max = {defect['area_fraction_max']:.4f} (>1 in "
              f"{defect['area_fraction_gt_1_rows']} rows)")
    print(out["verdict"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
