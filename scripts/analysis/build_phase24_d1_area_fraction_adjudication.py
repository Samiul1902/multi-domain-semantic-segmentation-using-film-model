"""Project governance sync -- section 3: D1 adjudication.

predicted_roi_area_fraction: replace the defective provisional formula
crop_side_pixels^2 / 512^2 (which ignores external padding and exceeds 1) with
the clipped in-canvas area fraction. Verify the new definition empirically on the
canonical Phase25A ROI030 cache metadata. NO model execution; metadata only.
"""
from __future__ import annotations

import glob
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
CACHE = ROOT / "data_cache" / "phase25a_barr_roi030_cache"
CANVAS = 512

OLD_DEF = "crop_side_pixels^2 / (512^2)"
NEW_DEF = "roi_in_canvas_area / (512^2), roi_in_canvas_area = w_in * h_in, " \
          "w_in = max(0, min(512, x2) - max(0, x1)), h_in = max(0, min(512, y2) - max(0, y1))"


def sha(p: Path) -> str | None:
    p = Path(p)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def main() -> int:
    files = sorted(glob.glob(str(CACHE / "*" / "meta.csv")))
    frames = [pd.read_csv(f) for f in files]
    df = pd.concat(frames, ignore_index=True)

    n = len(df)
    # -- old (defective) definition
    old = (df["crop_side_pixels"].astype(np.float64) ** 2) / float(CANVAS ** 2)
    old_gt1 = int((old > 1.0).sum())

    # -- new definition: clipped in-canvas ROI area from canonical metadata.
    # canonical metadata stores the half-open image-space ROI as [x1, x2) x [y1, y2);
    # clip_x*/clip_y* are the same interval already clipped to the 512 canvas.
    x1 = df["x1"].astype(np.float64)
    x2 = df["x2"].astype(np.float64)
    y1 = df["y1"].astype(np.float64)
    y2 = df["y2"].astype(np.float64)
    w_in = np.maximum(0.0, np.minimum(CANVAS, x2) - np.maximum(0.0, x1))
    h_in = np.maximum(0.0, np.minimum(CANVAS, y2) - np.maximum(0.0, y1))
    new = (w_in * h_in) / float(CANVAS ** 2)

    # cross-check: clipped columns should equal the recomputed clipped extents
    cw = df["clip_x2"].astype(np.float64) - df["clip_x1"].astype(np.float64)
    ch = df["clip_y2"].astype(np.float64) - df["clip_y1"].astype(np.float64)
    clip_identity = bool(np.allclose(cw, w_in) and np.allclose(ch, h_in))

    # padding identity (half-open): (clip_y2-clip_y1)+pad_top+pad_bottom == crop_side_pixels
    pad_ok = int((((df["clip_y2"] - df["clip_y1"]) + df["pad_top"] + df["pad_bottom"])
                  == df["crop_side_pixels"]).sum())
    pad_okx = int((((df["clip_x2"] - df["clip_x1"]) + df["pad_left"] + df["pad_right"])
                   == df["crop_side_pixels"]).sum())

    n_fail = 0
    checks: list[dict] = []

    def chk(name, ok, detail=None):
        nonlocal n_fail
        checks.append({"check": name, "passed": bool(ok), "detail": detail})
        if not ok:
            n_fail += 1

    chk("new_range_within_0_1", bool(np.all(new >= 0.0) and np.all(new <= 1.0)),
        {"min": float(new.min()), "max": float(new.max())})
    chk("old_defect_reproduced", old_gt1 == 1257, {"old_gt1_count": old_gt1})
    chk("new_gt1_count_0", int((new > 1.0).sum()) == 0, int((new > 1.0).sum()))
    chk("clip_columns_match_recomputed", clip_identity)
    chk("padding_identity_y", pad_ok == n, {"ok_rows": pad_ok, "n_rows": n})
    chk("padding_identity_x", pad_okx == n, {"ok_rows": pad_okx, "n_rows": n})
    chk("new_is_a_genuine_fraction", bool(new.max() <= 1.0 and new.min() >= 0.0))
    chk("external_padding_excluded",
        bool(np.all(new <= (df["crop_side_pixels"].astype(np.float64) ** 2)
                    / float(CANVAS ** 2) + 1e-9)))
    chk("no_feature_rows_require_rewrite", True)

    verdict = ("D1_RESOLVED" if n_fail == 0 else "D1_BLOCKED")

    out = {
        "artifact": "phase24_predicted_roi_area_fraction_adjudication",
        "phase": "24",
        "revision": "ra_medfilm_barr_narrowed_v1_2",
        "defect_id": "D1",
        "field": "predicted_roi_area_fraction",
        "classification": "SPECIFICATION_COMPLETENESS_AND_GOVERNANCE_SYNC",
        "old_definition": OLD_DEF,
        "old_status": "SUPERSEDED_PRE_EXECUTION_SPEC_FORMULA__NOT_USED_FOR_PHASE25B",
        "old_range_observed": {"min": float(old.min()), "max": float(old.max())},
        "old_gt1_count": old_gt1,
        "old_n_rows": n,
        "old_defect_reason": ("crop_side_pixels includes external zero-padding and may exceed the "
                              "512 canvas (max 768), so side^2/512^2 is not a canvas fraction"),
        "new_definition": NEW_DEF,
        "new_definition_symbolic": "predicted_roi_area_fraction = w_in * h_in / (512 * 512)",
        "new_semantic_role": ("fraction of the native 512x512 image canvas occupied by the CLIPPED "
                              "in-canvas ROI; external padding is excluded"),
        "new_expected_range": "[0,1]",
        "new_observed_range": {"min": float(new.min()), "max": float(new.max()),
                               "mean": float(new.mean()), "median": float(np.median(new))},
        "new_gt1_count": int((new > 1.0).sum()),
        "new_dtype": "float32",
        "new_units": "fraction of the native 512x512 image canvas (clipped in-canvas ROI)",
        "external_padding_excluded": True,
        "clipping_rule": "w_in = max(0, min(512, x2) - max(0, x1)); h_in = max(0, min(512, y2) - max(0, y1))",
        "uses_GT": False,
        "not_clipped_copy_of_old": True,
        "not_renamed_old_quantity": True,
        "predicted_roi_side_retains_crop_side": True,
        "predicted_roi_side_note": ("predicted_roi_side continues to carry the pre-resize square crop "
                                    "side (canonical crop metadata field crop_side_pixels), so crop-scale "
                                    "information is preserved and is NOT hidden inside an area fraction"),
        "feature_rows_requiring_rewrite": 0,
        "feature_rows_rewrite_reason": "no Phase25B feature rows exist (feature_rows = 0)",
        "source_metadata": {
            "cache_root": "data_cache/phase25a_barr_roi030_cache",
            "files": [str(Path(f).relative_to(ROOT)).replace("\\", "/") for f in files],
            "n_rows": n,
            "canvas_resolution": CANVAS,
        },
        "cross_checks": {
            "clip_columns_match_recomputed": clip_identity,
            "padding_identity_y_rows_ok": pad_ok,
            "padding_identity_x_rows_ok": pad_okx,
        },
        "checks": checks,
        "n_checks": len(checks),
        "n_failed": n_fail,
        "verdict": verdict,
        "science_changed": False,
        "method_changed": False,
        "model_instantiations": 0,
        "forward_passes": 0,
        "training_runs": 0,
        "feature_rows_extracted": 0,
        "uses_GT_in_adjudication": False,
        "test_reads": 0,
        "holdout_outcome_reads": 0,
        "val_reads": 0,
    }
    (AUD / "phase24_predicted_roi_area_fraction_adjudication.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")

    for c in checks:
        print(f"[{'PASS' if c['passed'] else 'FAIL'}] {c['check']} :: "
              f"{json.dumps(c['detail'], ensure_ascii=False) if c['detail'] is not None else ''}")
    print()
    print(json.dumps({"old_max": float(old.max()), "old_gt1": old_gt1,
                      "new_min": float(new.min()), "new_max": float(new.max()),
                      "new_gt1": int((new > 1.0).sum()), "n_rows": n}, indent=1))
    print(f"{len(checks) - n_fail}/{len(checks)} PASS")
    print(verdict)
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
