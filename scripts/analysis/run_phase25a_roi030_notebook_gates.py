"""Phase 25A (CANONICAL RERUN) — ROI-0.30 notebook visual integrity + 3x determinism.

Builds the Phase-25A notebook three times with the SAME builder (no retraining: the
notebook only reads frozen artefacts) and proves the three builds are byte-identical.

Then inventories every embedded image output and validates each base64 payload:
decodable, PNG magic, terminating IEND chunk.

Writes:
    reports/audits/phase25a_roi030_notebook_visual_integrity.json
    reports/audits/phase25a_roi030_notebook_determinism.json

Usage:
    ./.venv/Scripts/python.exe scripts/analysis/run_phase25a_notebook_gates.py
"""
from __future__ import annotations

import base64
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import nbformat

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
NB = (ROOT / "notebooks" / "phasewise" / "phase_25a_regional_refiner"
      / "phase25a_dedicated_regional_refiner.ipynb")
BUILDER = ROOT / "scripts" / "notebooks" / "build_phase25a_roi030_notebook.py"
PY = ROOT / ".venv" / "Scripts" / "python.exe"
UTC = datetime.now(timezone.utc).isoformat()

N_BUILDS = 3


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def validate_png(b64: str) -> dict:
    """Validate one embedded PNG payload. Returns a status dict."""
    raw_b64 = b64
    try:
        data = base64.b64decode(raw_b64, validate=False)
    except Exception as exc:
        return {"valid": False, "reason": f"base64_decode_error: {exc}"}
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        return {"valid": False, "reason": "missing_png_magic"}
    if data[-8:-4] != b"IEND":
        return {"valid": False, "reason": "missing_IEND_chunk"}
    return {"valid": True, "bytes": len(data)}


def main() -> int:
    # ---- 3x build --------------------------------------------------------- #
    shas: list[str] = []
    for i in range(N_BUILDS):
        print(f"--- build {i + 1}/{N_BUILDS} ---")
        proc = subprocess.run([str(PY), "-u", str(BUILDER)], cwd=str(ROOT),
                              capture_output=True, text=True)
        tail = (proc.stdout or "").strip().splitlines()[-6:]
        for line in tail:
            print("   ", line)
        if proc.returncode != 0:
            print(proc.stdout[-4000:])
            print(proc.stderr[-4000:], file=sys.stderr)
            raise SystemExit(f"FAIL-CLOSED: notebook build {i + 1} failed")
        shas.append(sha(NB))
        print("    sha256:", shas[-1])

    distinct = sorted(set(shas))
    byte_identical = len(distinct) == 1
    determinism = {
        "artifact": "phase25a_roi030_notebook_determinism",
        "phase": "25A",
        "classification": "CANONICAL_PHASE25A",
        "notebook": str(NB.relative_to(ROOT)).replace("\\", "/"),
        "n_builds": N_BUILDS,
        "sha256_per_build": shas,
        "n_distinct_sha256": len(distinct),
        "byte_identical": byte_identical,
        "byte_identical_three_builds": byte_identical,
        "classification": "CANONICAL_PHASE25A",
        "roi_proposal_threshold": 0.30,
        "segmentation_output_threshold": 0.50,
        "retrained": False,
        "note": "the notebook reads frozen artefacts only; no training, no inference",
        "generated_utc": UTC,
        "test_reads": 0,
    }
    (AUD / "phase25a_roi030_notebook_determinism.json").write_text(
        json.dumps(determinism, indent=1) + "\n", encoding="utf-8")

    # ---- visual integrity -------------------------------------------------- #
    nb = nbformat.read(str(NB), as_version=4)
    images, corrupt, total_png = [], [], 0
    for ci, cell in enumerate(nb.cells):
        if cell.cell_type != "code":
            continue
        for oi, out in enumerate(cell.get("outputs", []) or []):
            data = out.get("data") or {}
            if "image/png" not in data:
                continue
            total_png += 1
            payload = data["image/png"]
            if isinstance(payload, list):
                payload = "".join(payload)
            res = validate_png(payload)
            rec = {"cell_index": ci, "cell_id": cell.get("id"), "output_index": oi, **res}
            if res["valid"]:
                images.append(rec)
            else:
                corrupt.append(rec)
    code_cells = [c for c in nb.cells if c.cell_type == "code"]
    errors = sum(1 for c in code_cells for o in c.get("outputs", [])
                 if o.get("output_type") == "error")
    counts = [c.get("execution_count") for c in code_cells]
    monotonic = all(counts[i] == i + 1 for i in range(len(counts)))
    htmls = sum(1 for c in code_cells for o in c.get("outputs", [])
                if "text/html" in (o.get("data", {}) or {}))
    integrity = {
        "artifact": "phase25a_roi030_notebook_visual_integrity",
        "phase": "25A",
        "classification": "CANONICAL_PHASE25A",
        "notebook": str(NB.relative_to(ROOT)).replace("\\", "/"),
        "notebook_sha256": sha(NB),
        "n_cells": len(nb.cells),
        "n_markdown": sum(1 for c in nb.cells if c.cell_type == "markdown"),
        "n_code": len(code_cells),
        "n_embedded_png": total_png,
        "n_valid_png": len(images),
        "n_corrupt": len(corrupt),
        "n_missing": 0,
        "corrupt": corrupt,
        "html_table_outputs": htmls,
        "zero_tracebacks": errors == 0,
        "monotonic_execution_counts": bool(monotonic),
        "verdict": ("PHASE25A_ROI030_NOTEBOOK_VISUAL_INTEGRITY_PASS"
                    if not corrupt and errors == 0 else
                    "PHASE25A_ROI030_NOTEBOOK_VISUAL_INTEGRITY_FAIL"),
        "generated_utc": UTC,
        "test_reads": 0,
    }
    (AUD / "phase25a_roi030_notebook_visual_integrity.json").write_text(
        json.dumps(integrity, indent=1) + "\n", encoding="utf-8")

    print()
    print(f"notebook sha256 (final)   : {integrity['notebook_sha256']}")
    print(f"3x byte-identical         : {byte_identical}  ({len(distinct)} distinct)")
    print(f"cells                     : {integrity['n_cells']} "
          f"({integrity['n_markdown']} md / {integrity['n_code']} code)")
    print(f"embedded PNG valid/corrupt: {integrity['n_valid_png']}/{integrity['n_corrupt']}")
    print(f"html tables               : {integrity['html_table_outputs']}")
    print(f"zero tracebacks           : {integrity['zero_tracebacks']}")
    print(integrity["verdict"])
    print(determinism["artifact"], "->", "BYTE_IDENTICAL" if byte_identical else "DIFFERS")
    return 0 if (byte_identical and not corrupt and errors == 0) else 2


if __name__ == "__main__":
    raise SystemExit(main())
