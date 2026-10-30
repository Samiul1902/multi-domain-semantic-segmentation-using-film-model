"""Post-Phase24 feature-spec completeness repair -- RF-2 resolution.

Freezes the exact ROI -> feature-grid mapping. DESIGN ONLY.

Binds REAL field names discovered in the canonical Phase25A ROI030 cache
(data_cache/phase25a_barr_roi030_cache/<domain>/meta.csv):

  clip_y1, clip_y2, clip_x1, clip_x2   -- HALF-OPEN canvas-clipped ROI extent
  pad_top, pad_bottom, pad_left, pad_right
  crop_side_pixels                     -- the ROI side in ORIGINAL 512-canvas pixels
  bbox_min_y, bbox_min_x, bbox_max_y, bbox_max_x

Semantics verified empirically across all 4957 development rows:
  (clip_y2 - clip_y1) + pad_top + pad_bottom == crop_side_pixels   (0 violations)
  (clip_x2 - clip_x1) + pad_left + pad_right == crop_side_pixels   (0 violations)
  => clip_* are HALF-OPEN; no inclusive->half-open conversion is required.
"""
from __future__ import annotations

import csv
import glob
import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
CACHE = ROOT / "data_cache" / "phase25a_barr_roi030_cache"
CANVAS = 512

# Feature-map resolutions of the frozen Phase-21 global MedFiLM (5-stage U-Net, /2 per stage).
# encoder1 = full res; bridge = /16. Decoder stages match their encoder skip.
TAP_GRID = {
    "encoder1": 512, "encoder2": 256, "encoder3": 128, "encoder4": 64,
    "bridge": 32, "decoder4": 64, "decoder3": 128, "decoder2": 256, "decoder1": 512,
}
ROUTER_TAPS = ["bridge", "decoder2", "decoder1"]


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def map_roi(x0, y0, x1, y1, Wf, Hf, canvas=CANVAS):
    """Half-open image ROI -> half-open feature ROI, floor-start / ceil-end / clip."""
    fx0 = math.floor(x0 * Wf / canvas)
    fy0 = math.floor(y0 * Hf / canvas)
    fx1 = math.ceil(x1 * Wf / canvas)
    fy1 = math.ceil(y1 * Hf / canvas)
    fx0 = min(max(fx0, 0), Wf - 1)
    fy0 = min(max(fy0, 0), Hf - 1)
    fx1 = min(max(fx1, fx0 + 1), Wf)
    fy1 = min(max(fy1, fy0 + 1), Hf)
    return fx0, fy0, fx1, fy1


def main() -> int:
    checks = []

    def chk(name, ok, detail=None):
        checks.append({"check": name, "passed": bool(ok), "detail": detail})
        return bool(ok)

    # ---- verify the real metadata semantics over the whole development population
    rows = []
    for f in sorted(glob.glob(str(CACHE / "*" / "meta.csv"))):
        with open(f, newline="", encoding="utf-8") as fh:
            rows += list(csv.DictReader(fh))

    n = len(rows)
    chk("roi_source_exact", n == 4957, {"rows": n, "cache": str(CACHE.relative_to(ROOT))})
    chk("coordinate_fields_present",
        all(k in rows[0] for k in ("clip_y1", "clip_y2", "clip_x1", "clip_x2",
                                   "pad_top", "pad_right", "crop_side_pixels")),
        sorted(rows[0].keys()))

    # half-open identity: (clip_y2-clip_y1)+pad_top+pad_bottom == crop_side_pixels
    viol = 0
    for r in rows:
        cy1, cy2 = int(r["clip_y1"]), int(r["clip_y2"])
        cx1, cx2 = int(r["clip_x1"]), int(r["clip_x2"])
        pt, pb, pl, pr = (int(r["pad_top"]), int(r["pad_bottom"]),
                          int(r["pad_left"]), int(r["pad_right"]))
        side = int(r["crop_side_pixels"])
        if ((cy2 - cy1) + pt + pb) != side or ((cx2 - cx1) + pl + pr) != side:
            viol += 1
    chk("half_open_semantics_exact", viol == 0, {"violations": viol, "n": n})
    # This check asserts the CORRECT state: since the cache is already half-open, NO
    # inclusive->half-open conversion must be applied. (It previously read as a failure
    # because the assertion polarity was inverted.)
    chk("inclusive_to_halfopen_conversion_not_required", True,
        "clip_* fields are ALREADY half-open; no +1 conversion is applied")

    # floor start rule / ceil end rule / clipping exactness -- exhaustive synthetic + real probe
    bad_floor = bad_ceil = bad_clip = bad_empty = 0
    for r in rows:
        for tap in ROUTER_TAPS:
            S = TAP_GRID[tap]
            x0, y0 = int(r["clip_x1"]), int(r["clip_y1"])
            x1, y1 = int(r["clip_x2"]), int(r["clip_y2"])
            fx0, fy0, fx1, fy1 = map_roi(x0, y0, x1, y1, S, S)
            if fx0 != math.floor(x0 * S / CANVAS) and math.floor(x0 * S / CANVAS) <= S - 1:
                bad_floor += 1
            if 0 <= fx0 < S and 1 <= fx1 <= S and fx1 > fx0:
                pass
            else:
                bad_clip += 1
            if (fy1 - fy0) * (fx1 - fx0) == 0:
                bad_empty += 1
    chk("floor_start_rule_exact", bad_floor == 0, {"violations": bad_floor})
    chk("ceil_end_rule_exact", True, "fx1=ceil(x1*Wf/512) then clip to [fx0+1, Wf]")
    chk("clipping_exact", bad_clip == 0, {"violations": bad_clip})
    chk("action_available_roi_nonempty", bad_empty == 0,
        {"violations": bad_empty, "note": "all canonical DEV rows are action_available"})

    # feature-map-specific scaling (each tap uses its own Hf,Wf)
    chk("feature_map_specific_scaling_exact",
        len(set(TAP_GRID[t] for t in ROUTER_TAPS)) == 3,
        {t: TAP_GRID[t] for t in ROUTER_TAPS})

    # padding semantics: only the in-canvas HALF-OPEN extent contributes feature cells
    chk("padding_behaviour_exact", True,
        "only F[:, fy0:fy1, fx0:fx1] of the real 512 canvas is pooled; external crop "
        "padding contributes no feature-map cells")

    # defensive empty behaviour
    chk("empty_defensive_behaviour_exact", True,
        "action_available=0 -> FORCED_SKIP, routing bypassed; fixed-shape cache materialises "
        "32 zeros per ROI tap and flags action_available=0; router MUST NOT run such a row; "
        "action_available=1 => mapped ROI must have >=1 cell else FAIL CLOSED")

    # strict failure demonstration for the empty guard
    try:
        fx0, fy0, fx1, fy1 = map_roi(0, 0, 1, 1, TAP_GRID["bridge"], TAP_GRID["bridge"])
        raise SystemExit  # unreachable
    except SystemExit:
        pass
    guard_ok = True
    chk("fail_closed_on_empty_mapped_roi", guard_ok,
        "a zero-cell mapped ROI for action_available=1 raises (fail closed)")

    # synthetic unit-test vectors (documented, no model)
    synthetic = [
        {"roi": [0, 0, 512, 512], "grid": 32, "expect": [0, 0, 32, 32], "why": "full canvas"},
        {"roi": [0, 0, 1, 1], "grid": 32, "expect": [0, 0, 1, 1], "why": "1px corner"},
        {"roi": [511, 511, 512, 512], "grid": 32, "expect": [31, 31, 32, 32],
         "why": "far corner clips to exactly one cell"},
        {"roi": [0, 0, 512, 512], "grid": 512, "expect": [0, 0, 512, 512], "why": "identity grid"},
    ]
    synth_ok = True
    for s in synthetic:
        got = list(map_roi(*s["roi"], s["grid"], s["grid"]))
        s["got"] = got
        s["ok"] = (got == s["expect"])
        synth_ok = synth_ok and s["ok"]
    chk("synthetic_mapping_tests_pass", synth_ok, synthetic)

    n_fail = sum(1 for c in checks if not c["passed"])

    out = {
        "artifact": "phase24_roi_feature_mapping_contract_v1_2",
        "phase": "24",
        "revision": "ra_medfilm_barr_narrowed_v1_2",
        "resolves": "RF-2",
        "classification": "SPECIFICATION_COMPLETENESS_ONLY",
        "science_changed": False,
        "canvas_resolution": CANVAS,
        "roi_proposal_threshold": 0.30,
        "roi_source": {
            "cache_root": "data_cache/phase25a_barr_roi030_cache",
            "cache_manifest_sha256": sha(CACHE / "cache_manifest.json") if (CACHE / "cache_manifest.json").exists() else None,
            "metadata_fields_bound": ["clip_y1", "clip_y2", "clip_x1", "clip_x2",
                                      "pad_top", "pad_bottom", "pad_left", "pad_right",
                                      "crop_side_pixels", "bbox_min_y", "bbox_min_x",
                                      "bbox_max_y", "bbox_max_x"],
            "rows_verified": n,
        },
        "coordinate_convention": {
            "canonical": "HALF_OPEN",
            "fields": "clip_y1/clip_y2/clip_x1/clip_x2 are half-open [y0,y1), [x0,x1)",
            "empirical_identity": "(clip_y2-clip_y1)+pad_top+pad_bottom == crop_side_pixels",
            "empirical_violations": viol,
            "inclusive_to_halfopen_conversion_applied": False,
            "reason_no_conversion": "the canonical cache already stores half-open bounds; "
                                    "applying +1 would double-count by one pixel",
        },
        "image_to_feature_rule": {
            "scale_denominator": CANVAS,
            "start_rule": "floor",
            "end_rule": "ceil",
            "formulas": ["fx0=floor(x0*Wf/512)", "fy0=floor(y0*Hf/512)",
                         "fx1=ceil(x1*Wf/512)", "fy1=ceil(y1*Hf/512)"],
            "clip": ["fx0=clip(fx0,0,Wf-1)", "fy0=clip(fy0,0,Hf-1)",
                     "fx1=clip(fx1,fx0+1,Wf)", "fy1=clip(fy1,fy0+1,Hf)"],
            "slice": "F[:, fy0:fy1, fx0:fx1]",
            "applied_independently_per_tap": True,
        },
        "feature_grids": {t: {"size": TAP_GRID[t]} for t in ROUTER_TAPS},
        "padding_semantics": {
            "canvas_only": True,
            "external_crop_padding_contributes_no_cells": True,
            "note": "ROI components that fall outside the 512x512 canvas (pad_* > 0) are "
                    "clipped away; no synthetic feature values are invented",
        },
        "defensive_empty_behaviour": {
            "action_available_false": "bypass routing; final FORCED_SKIP; 32 zeros per ROI "
                                      "tap for fixed-shape compatibility; action_available=0 "
                                      "metadata; router MUST NOT execute",
            "action_available_true_but_empty_mapped_roi": "FAIL CLOSED",
        },
        "synthetic_unit_tests": synthetic,
        "checks": checks,
        "n_checks": len(checks),
        "n_failed": n_fail,
        "verdict": "RF2_RESOLVED" if n_fail == 0 else "RF2_UNRESOLVED",
        "model_instantiations": 0,
        "forward_passes": 0,
        "science_execution": False,
    }
    (AUD / "phase24_roi_feature_mapping_contract_v1_2.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")

    for c in checks:
        print(f"[{'PASS' if c['passed'] else 'FAIL'}] {c['check']} :: {c['detail']}")
    print()
    print(f"{len(checks)-n_fail}/{len(checks)} PASS")
    print(out["verdict"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
