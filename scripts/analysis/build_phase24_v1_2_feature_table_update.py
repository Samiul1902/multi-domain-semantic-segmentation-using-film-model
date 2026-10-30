"""Project governance sync -- section 6 (cont.): update the v1.2 primary feature-set table.

Bind the corrected predicted_roi_area_fraction formula into the additive v1.2 CSV.
The historical (non-v1.2) table is NOT touched.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(r"D:/Softfors/jup")
TAB = ROOT / "reports" / "tables" / "phase24_router_primary_feature_set_v1_2.csv"
CSV = TAB


def main() -> int:
    df = pd.read_csv(CSV)
    n_fail = 0
    checks = []

    def chk(name, ok, detail=None):
        nonlocal n_fail
        checks.append({"check": name, "passed": bool(ok), "detail": detail})
        if not ok:
            n_fail += 1

    chk("sixteen_rows", len(df) == 16, len(df))
    chk("no_duplicate_feature_names",
        df["feature_name"].duplicated().sum() == 0,
        int(df["feature_name"].duplicated().sum()))

    m = df["feature_name"] == "predicted_roi_area_fraction"
    chk("area_fraction_row_present", int(m.sum()) == 1, int(m.sum()))
    df.loc[m, "formula"] = (
        "roi_in_canvas_area/(512^2); roi_in_canvas_area = "
        "max(0,min(512,x2)-max(0,x1)) * max(0,min(512,y2)-max(0,y1))")
    df.loc[m, "units"] = "fraction of native 512x512 canvas (clipped in-canvas ROI); external padding excluded"
    df.loc[m, "notes"] = ("RESOLVED (D1/C3): clipped in-canvas area fraction; "
                          "old crop_side_pixels^2/512^2 SUPERSEDED; "
                          "see phase24_predicted_roi_area_fraction_adjudication.json")

    s = df["feature_name"] == "predicted_roi_side"
    df.loc[s, "notes"] = ("retains the pre-resize square crop side (crop_side_pixels); "
                          "crop-scale information is preserved here, not inside the area fraction")

    df.to_csv(CSV, index=False, encoding="utf-8")

    df2 = pd.read_csv(CSV)
    chk("no_defect_marker_remains",
        not df2["notes"].astype(str).str.contains("DEFECT").any())
    chk("area_fraction_bound_to_new_formula",
        "roi_in_canvas_area" in str(df2.loc[df2["feature_name"] ==
                                            "predicted_roi_area_fraction", "formula"].iloc[0]))

    for c in checks:
        print(f"[{'PASS' if c['passed'] else 'FAIL'}] {c['check']} :: {c['detail']}")
    print(f"{len(checks) - n_fail}/{len(checks)} PASS")
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
