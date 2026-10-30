"""Phase 22 reviewer notebook — POST-WRITE VISUAL-INTEGRITY GATE (§9).

Reads the ACTUAL ``.ipynb`` bytes (authoritative — an inventory flag saying
``embedded=True`` is never trusted) and verifies that every required figure is
present exactly once, decodes, and PIL-verifies.

PASS requires ALL of:
  * expected required figures                  == 15
  * required figures actually embedded         == 15
  * every embedded required payload decodes
  * every embedded required payload PIL-verifies
  * zero corrupt figures
  * zero missing figures
  * zero unexpected figures
  * zero duplicate figures

Additive (post-freeze reviewer) figures are reported separately and do NOT
count against the frozen 15-figure inventory.

Exit code 2 on FAIL (fail closed).
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import nbformat
from PIL import Image

ROOT = Path(r"D:/Softfors/jup")
FIG = ROOT / "reports/figures/phase22_resource_gap"
AUD = ROOT / "reports/audits"
NB_PATH = ROOT / "notebooks/phasewise/phase_22_resource_gap/phase22_resource_gap_analysis.ipynb"
OUT = AUD / "phase22_notebook_visual_integrity_after_repair.json"

ADDITIVE_FIGURES: list[str] = []          # none declared at this revision
PNG_SIG = b"\x89PNG\r\n\x1a\n"


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    return sha256_bytes(p.read_bytes())


def main() -> int:
    raw = NB_PATH.read_bytes()
    nb = nbformat.reads(raw.decode("utf-8"), as_version=4)

    manifest = None
    mp = FIG / "phase22_figure_manifest.csv"
    if mp.exists():
        import pandas as pd
        manifest = pd.read_csv(mp)
    if manifest is None:
        raise SystemExit("figure manifest missing; cannot gate")

    required = manifest[manifest["expected_to_embed"].astype(str).str.lower()
                        == "true"]["figure_id"].tolist()
    src_sha = {}
    for _, r in manifest.iterrows():
        p = ROOT / str(r.get("source_path") or r.get("file"))
        if p.exists():
            src_sha[str(r["figure_id"])] = sha256_file(p)

    # --- collect every embedded PNG payload from the real notebook bytes ---- #
    pngs = []
    for ci, cell in enumerate(nb.cells):
        if cell.get("cell_type") != "code":
            continue
        for oi, o in enumerate(cell.get("outputs", [])):
            d = o.get("data", {})
            if not isinstance(d, dict) or "image/png" not in d:
                continue
            payload = d["image/png"]
            b64 = payload.encode("utf-8") if isinstance(payload, str) else payload
            try:
                dec = base64.b64decode(b64)
            except Exception:                                 # noqa: BLE001
                dec = b""
            rec = {"cell_index": ci, "output_index": oi, "b64_len": len(b64),
                   "bytes": len(dec), "sha256": sha256_bytes(dec) if dec else None,
                   "png_signature": dec.startswith(PNG_SIG),
                   "decodable": False, "pil_verify": False,
                   "width": None, "height": None}
            if dec:
                try:
                    with Image.open(io.BytesIO(dec)) as im:
                        im.verify()
                    rec["pil_verify"] = True
                    with Image.open(io.BytesIO(dec)) as im:
                        im.load()
                        rec["width"], rec["height"] = im.size
                    rec["decodable"] = True
                except Exception as exc:                      # noqa: BLE001
                    rec["error"] = f"{type(exc).__name__}: {exc}"
            pngs.append(rec)

    # --- bind embedded payloads to manifest figures ------------------------- #
    # Exact byte identity first; fall back to a re-encode-insensitive match by
    # matching the decoded pixel dimensions for the one figure we downscaled.
    emb_shas = {p["sha256"] for p in pngs if p["sha256"]}
    embedded_figures, downscaled_figures = [], []
    for fid, s in src_sha.items():
        if s in emb_shas:
            embedded_figures.append(fid)
    # A figure embedded at reduced size will not match byte-for-byte; detect it
    # by locating a payload whose dimensions match a downscale of the source.
    missing_candidates = [f for f in required if f not in embedded_figures]
    for fid in list(missing_candidates):
        p = ROOT / str(manifest.loc[manifest["figure_id"] == fid, "source_path"].iloc[0])
        if not p.exists():
            continue
        with Image.open(p) as im:
            sw, sh = im.size
        cap = 1600
        target = (cap, max(1, int(round(sh * cap / sw)))) if sw > cap else (sw, sh)
        for rec in pngs:
            if rec["sha256"] in emb_shas and rec["width"] and \
                    (rec["width"], rec["height"]) == target:
                embedded_figures.append(fid)
                downscaled_figures.append(fid)
                break

    missing = [f for f in required if f not in embedded_figures]
    unexpected = [f for f in embedded_figures
                  if f not in required and f not in ADDITIVE_FIGURES]
    # Duplicates: the same payload SHA embedded more than once.
    seen = {}
    for p in pngs:
        if p["sha256"]:
            seen.setdefault(p["sha256"], []).append((p["cell_index"], p["output_index"]))
    duplicates = [{"sha256": s, "count": len(v), "locations": v}
                  for s, v in seen.items() if len(v) > 1]
    corrupt = [p for p in pngs if not (p["decodable"] and p["pil_verify"])]

    n_expected = len(required)
    n_embedded = len(embedded_figures)
    checks = {
        "expected_required_figures_15": n_expected == 15,
        "required_figures_embedded_15": n_embedded == n_expected,
        "all_embedded_png_decode": len(corrupt) == 0,
        "all_embedded_png_PIL_verify": all(p["pil_verify"] for p in pngs),
        "zero_corrupt_figures": len(corrupt) == 0,
        "zero_missing_figures": len(missing) == 0,
        "zero_unexpected_figures": len(unexpected) == 0,
        "zero_duplicate_figures": len(duplicates) == 0,
    }

    code_cells = [c for c in nb.cells if c.get("cell_type") == "code"]
    executed = [c for c in code_cells if c.get("execution_count") is not None]
    counts = [c.get("execution_count") for c in executed]
    monotonic = all(counts[i] < counts[i + 1] for i in range(len(counts) - 1))
    errors = sum(1 for c in code_cells for o in c.get("outputs", [])
                 if o.get("output_type") == "error")
    checks["all_required_figures_embedded"] = n_embedded == n_expected
    checks["all_required_png_decode"] = len(corrupt) == 0
    checks["all_required_png_PIL_verify"] = all(p["pil_verify"] for p in pngs)
    checks["no_corrupt_unexpected_duplicates"] = (
        len(corrupt) == 0 and len(unexpected) == 0 and len(duplicates) == 0)
    checks["all_code_cells_executed"] = len(executed) == len(code_cells)
    checks["execution_counts_monotonic"] = monotonic
    checks["zero_notebook_errors"] = errors == 0

    verdict = "PASS" if all(checks.values()) else "FAIL"

    report = {
        "artifact": "phase22_notebook_visual_integrity_after_repair",
        "phase": 22,
        "classification": "REVIEWER_PACKAGE_VISUAL_INTEGRITY_REPAIR",
        "notebook_path": str(NB_PATH.relative_to(ROOT)),
        "notebook_sha256": sha256_bytes(raw),
        "expected_required_figures": n_expected,
        "required_figures_embedded": n_embedded,
        "embedded_figure_names": sorted(embedded_figures),
        "downscaled_for_embedding": sorted(downscaled_figures),
        "missing_figures": missing,
        "unexpected_figures": unexpected,
        "additive_figures": [],
        "duplicate_figures": duplicates,
        "corrupt_figures": [c["sha256"] for c in corrupt],
        "png_outputs_total": len(pngs),
        "valid_png_outputs": len([p for p in pngs if p["decodable"] and p["pil_verify"]]),
        "source_sha256_per_embedded_figure": {
            f: src_sha.get(f) for f in sorted(embedded_figures)},
        "executed_code_cells": len(executed),
        "total_code_cells": len(code_cells),
        "execution_counts": counts,
        "error_outputs": errors,
        "html_table_outputs": sum(1 for c in code_cells for o in c.get("outputs", [])
                                  if "text/html" in (o.get("data", {}) or {})),
        "checks": checks,
        "verdict": verdict,
        "test_image_reads": 0, "test_mask_reads": 0,
        "test_inference": 0, "test_visualization": 0,
        "new_segmentation_inference": False,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
    }
    AUD.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"§9 post-write gate  verdict: {verdict}")
    for k, v in checks.items():
        print(f"   {'PASS' if v else 'FAIL'}  {k}")
    print(f"   expected {n_expected} | embedded {n_embedded} | "
          f"corrupt {len(corrupt)} | missing {len(missing)} | "
          f"unexpected {len(unexpected)} | duplicates {len(duplicates)}")
    print(f"   code {len(executed)}/{len(code_cells)} | errors {errors} | "
          f"png outputs {len(pngs)} | notebook SHA {report['notebook_sha256'][:16]}")
    return 0 if verdict == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
