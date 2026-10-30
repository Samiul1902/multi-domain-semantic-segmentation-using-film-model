"""Phase 23 — fail-closed notebook VISUAL integrity gate.

Reopens the ACTUAL ``.ipynb`` bytes, strictly base64-decodes every embedded PNG,
verifies it with ``PIL.Image.verify()``, and records the cell index, figure id and
SHA-256. Any corruption, missing required figure, or unintended duplicate is a
hard failure.

PRESENTATION-ONLY. Reads the notebook and the figure manifest; touches nothing else.

Writes:
    reports/audits/phase23_notebook_visual_integrity.json

Usage
-----
    ./.venv/Scripts/python.exe scripts/analysis/run_phase23_visual_integrity.py
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import io
import json
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
FIG = ROOT / "reports" / "figures" / "phase23_novelty_audit"
NB = ROOT / "notebooks/phasewise/phase_23_literature_novelty/phase23_literature_methodological_novelty_audit.ipynb"

# figure file -> the section it is expected to be embedded in
REQUIRED = {
    "p23_search_coverage.png": "§6.1 Search coverage",
    "p23_concept_taxonomy.png": "§7.1 Concept taxonomy",
    "p23_prior_art_mechanism_matrix.png": "§7.2 Prior-art mechanism coverage",
    "p23_novelty_axes_matrix.png": "§18.1 Novelty-axis matrix",
}
OPTIONAL = {
    "p23_closest_prior_work_matrix.png": "§17.1 Closest works comparison",
}


def main() -> int:
    manifest_p = FIG / "phase23_figure_manifest.json"
    if not manifest_p.exists():
        print("FAIL-CLOSED: figure manifest missing; run build_phase23_visuals.py first")
        return 1
    manifest = json.loads(manifest_p.read_text(encoding="utf-8"))

    if not NB.exists():
        print(f"FAIL-CLOSED: notebook missing: {NB}")
        return 1
    nb = json.loads(NB.read_text(encoding="utf-8"))

    # ---- inventory every embedded PNG from the raw notebook bytes -------------
    embedded: list[dict] = []
    for ci, c in enumerate(nb.get("cells", [])):
        if c.get("cell_type") != "code":
            continue
        for oi, o in enumerate(c.get("outputs", []) or []):
            d = o.get("data", {}) or {}
            if "image/png" not in d:
                continue
            v = d["image/png"]
            if isinstance(v, list):
                v = "".join(v)
            rec = {"cell_index": ci, "cell_id": c.get("id"), "output_index": oi}
            try:
                raw = base64.b64decode(v, validate=True)
            except (binascii.Error, ValueError) as e:
                rec.update({"decoded": False, "error": f"base64: {e}"})
                embedded.append(rec)
                continue
            rec["bytes"] = len(raw)
            rec["sha256"] = hashlib.sha256(raw).hexdigest()
            # strict PNG signature
            rec["png_signature"] = raw.startswith(b"\x89PNG\r\n\x1a\n")
            try:
                im = Image.open(io.BytesIO(raw))
                im.verify()                      # integrity check (must come first)
                im2 = Image.open(io.BytesIO(raw))  # reopen to read real dims
                im2.load()
                rec["format"] = im2.format
                rec["size"] = list(im2.size)
                rec["mode"] = im2.mode
                rec["pil_verify"] = True
                rec["decoded"] = True
            except Exception as e:               # noqa: BLE001
                rec["pil_verify"] = False
                rec["decoded"] = True
                rec["error"] = f"PIL: {e}"
            embedded.append(rec)

    # ---- match embedded PNGs to the manifest by SHA --------------------------
    fig_by_sha = {v["sha256"]: k for k, v in manifest["figures"].items()}
    for rec in embedded:
        rec["figure_id"] = fig_by_sha.get(rec.get("sha256", ""))

    present_required = {r["figure_id"] for r in embedded if r.get("figure_id") in REQUIRED}
    present_optional = {r["figure_id"] for r in embedded if r.get("figure_id") in OPTIONAL}

    missing = sorted(set(REQUIRED) - present_required)
    valid_required = sorted(
        r["figure_id"] for r in embedded
        if r.get("figure_id") in REQUIRED and r.get("pil_verify") and r.get("png_signature"))
    corrupt = [
        {"figure_id": r.get("figure_id"), "cell_index": r.get("cell_index"),
         "error": r.get("error", "unknown")}
        for r in embedded
        if not r.get("pil_verify") or not r.get("png_signature")
    ]
    unexpected = sorted({r["figure_id"] for r in embedded
                         if r.get("figure_id")
                         and r["figure_id"] not in REQUIRED
                         and r["figure_id"] not in OPTIONAL})

    # unintended duplicates: the same figure embedded more than once
    seen: dict[str, int] = {}
    for r in embedded:
        fid = r.get("figure_id")
        if fid:
            seen[fid] = seen.get(fid, 0) + 1
    unintended_duplicates = sorted(k for k, n in seen.items() if n > 1)

    # a corrupted payload that cannot be matched is still a failure
    unmatched_broken = [r for r in embedded
                        if not r.get("figure_id") and not r.get("pil_verify")]

    ok = (
        len(REQUIRED) == 4
        and len(valid_required) == 4
        and not corrupt
        and not missing
        and not unexpected
        and not unintended_duplicates
        and not unmatched_broken
    )

    integrity = {
        "artifact": "phase23_notebook_visual_integrity",
        "phase": 23,
        "classification": "REVIEWER_PRESENTATION_REPAIR",
        "fail_closed": True,
        "notebook": str(NB.relative_to(ROOT)).replace("\\", "/"),
        "notebook_sha256": hashlib.sha256(NB.read_bytes()).hexdigest(),
        "required_by_section": REQUIRED,
        "optional_by_section": OPTIONAL,
        "expected_required_figures": 4,
        "embedded_required_figures": len(present_required),
        "valid_required_figures": len(valid_required),
        "corrupt": len(corrupt),
        "missing": missing,
        "unexpected": unexpected,
        "unintended_duplicates": unintended_duplicates,
        "optional_figures": {
            "expected": len(OPTIONAL),
            "embedded": len(present_optional),
            "valid": sorted(
                r["figure_id"] for r in embedded
                if r.get("figure_id") in OPTIONAL and r.get("pil_verify")),
            "reported_separately": True,
        },
        "embedded_report": embedded,
        "total_embedded_png": len(embedded),
        "all_passed": ok,
        "training": False,
        "inference": False,
        "test_reads": 0,
        "phase24_started": False,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
    }
    (AUD / "phase23_notebook_visual_integrity.json").write_text(
        json.dumps(integrity, indent=1), encoding="utf-8")

    print(f"  expected required figures : {integrity['expected_required_figures']}")
    print(f"  embedded required figures : {integrity['embedded_required_figures']}")
    print(f"  valid required figures    : {integrity['valid_required_figures']}")
    print(f"  corrupt                   : {integrity['corrupt']}")
    print(f"  missing                   : {missing}")
    print(f"  unexpected                : {unexpected}")
    print(f"  unintended_duplicates     : {unintended_duplicates}")
    print(f"  optional embedded / valid : {integrity['optional_figures']['embedded']} / "
          f"{len(integrity['optional_figures']['valid'])}")
    print()
    print(f"  ALL PASSED                : {ok}")
    if not ok:
        print("FAIL-CLOSED: visual integrity gate FAILED")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
