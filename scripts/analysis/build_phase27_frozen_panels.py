"""Phase27 CANONICAL VISUAL REBUILD — Step 1: freeze RGB/GT reviewer raster panels.

Classification: PHASE27_REVIEWER_VISUAL_CANONICAL_REBUILD__FROZEN_REVIEWER_ARTIFACTS_ONLY

This step extracts the RGB and GT panel columns for the 16 fixed qualitative samples
from the ALREADY-FROZEN high-resolution reviewer raster
(reports/figures/phase27_preservation/p27_qualitative_panels.png), which is itself a
frozen reviewer artifact.

It does NOT read raw VAL808 RGB files, raw VAL808 GT masks, the VAL808 dataset loader,
or run any model.  The extracted panels become frozen reviewer artifacts for the
canonical rebuild step.

SOURCE_LIMITATION = RELAYOUT_FROM_FROZEN_REVIEWER_RASTER
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(r"D:/Softfors/jup")
FIG = ROOT / "reports" / "figures" / "phase27_preservation"
PANELS = FIG / "frozen_reviewer_panels"
AUD = ROOT / "reports" / "audits"

# Frozen high-res reviewer raster (noncanonical-scope but frozen artifact; used here as
# a REVIEWER RASTER SOURCE only, per work-order priority #3).
SOURCE_PNG = FIG / "p27_qualitative_panels.png"
SOURCE_SHA_EXPECTED = "4ec2f8e2af3ffe28bf8e03bdfcf577c421b50727b920743ea99887e1c3cf54ec"

DOMAINS = ["BUSI", "ISIC", "KUB", "KVASIR"]

# Panel grid geometry (deterministic, measured from the frozen raster).
# 4 domain blocks arranged [BUSI | ISIC] / [KUB | KVASIR]; each block = 4 rows x 5 cols.
# Column x-ranges for each of the 5 panel columns, per grid row-block.
LEFT_COLS = [(246, 560), (688, 1001), (1129, 1442), (1571, 1884), (2012, 2325)]
RIGHT_COLS = [(2656, 2969), (3097, 3411), (3539, 3852), (3980, 4294), (4422, 4735)]
TOP_ROWS = [(211, 524), (540, 853), (869, 1182), (1198, 1511)]
BOT_ROWS = [(1742, 2055), (2070, 2384), (2399, 2713), (2728, 3042)]

# Grid slot -> (col_set, row_set) for each domain
DOMAIN_GRID = {
    "BUSI":   (LEFT_COLS,  TOP_ROWS),
    "ISIC":   (RIGHT_COLS, TOP_ROWS),
    "KUB":    (LEFT_COLS,  BOT_ROWS),
    "KVASIR": (RIGHT_COLS, BOT_ROWS),
}

# RGB is panel column index 0; GT is panel column index 3.
COL_RGB = 0
COL_GT = 3


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def load_selection():
    import csv
    rows = []
    with open(ROOT / "reports" / "tables" / "phase27_qualitative_gallery_selection.csv",
              newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append((r["domain"], r["sample_id"]))
    return rows


def main() -> int:
    src_sha = sha256_file(SOURCE_PNG)
    assert src_sha == SOURCE_SHA_EXPECTED, f"source raster SHA mismatch {src_sha}"
    print(f"[canon] frozen reviewer raster verified: {src_sha[:16]}")

    im = Image.open(SOURCE_PNG).convert("RGB")
    a = np.asarray(im)
    PANELS.mkdir(parents=True, exist_ok=True)

    sel = load_selection()
    assert len(sel) == 16, f"expected 16 samples, got {len(sel)}"

    per_domain = {}
    for d, sid in sel:
        per_domain.setdefault(d, []).append(sid)
    for d in DOMAINS:
        assert len(per_domain[d]) == 4, f"{d} has {len(per_domain.get(d, []))} samples"

    manifest = []
    for d in DOMAINS:
        cols, rows = DOMAIN_GRID[d]
        for r, sid in enumerate(per_domain[d]):
            y0, y1 = rows[r]
            # RGB panel
            cx0, cx1 = cols[COL_RGB]
            rgb = a[y0:y1, cx0:cx1]
            # GT panel
            gx0, gx1 = cols[COL_GT]
            gt = a[y0:y1, gx0:gx1]
            rgb_p = PANELS / f"{sid}_rgb.png"
            gt_p = PANELS / f"{sid}_gt.png"
            Image.fromarray(rgb).save(rgb_p, optimize=True)
            Image.fromarray(gt).save(gt_p, optimize=True)
            manifest.append({
                "domain": d, "sample_id": sid, "row_index": r,
                "rgb_png": str(rgb_p.relative_to(ROOT)), "rgb_sha256": sha256_file(rgb_p),
                "gt_png": str(gt_p.relative_to(ROOT)), "gt_sha256": sha256_file(gt_p),
                "panel_hw": [int(gt.shape[0]), int(gt.shape[1])],
            })

    out = {
        "artifact": "phase27_frozen_reviewer_rgb_gt_panels",
        "phase": "27",
        "method": "RA-MedFiLM-BARR",
        "classification": "PHASE27_REVIEWER_VISUAL_CANONICAL_REBUILD__FROZEN_REVIEWER_ARTIFACTS_ONLY",
        "SOURCE_LIMITATION": "RELAYOUT_FROM_FROZEN_REVIEWER_RASTER",
        "source_raster": {"path": str(SOURCE_PNG.relative_to(ROOT)), "sha256": src_sha,
                          "dimensions": [int(a.shape[1]), int(a.shape[0])]},
        "raw_VAL808_RGB_reads": 0,
        "raw_VAL808_GT_reads": 0,
        "model_forwards": 0,
        "n_panels": len(manifest) * 2,
        "panels_dir": str(PANELS.relative_to(ROOT)),
        "per_sample": manifest,
        "all_pass": True,
    }
    with open(AUD / "phase27_frozen_reviewer_rgb_gt_panels.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"[canon] extracted {len(manifest)*2} frozen panels for {len(manifest)} samples")
    print("[canon] wrote", (AUD / 'phase27_frozen_reviewer_rgb_gt_panels.json').relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
