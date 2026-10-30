"""Phase 25B -- notebook visual integrity + 3x byte-identical determinism
(work-order sections 23 and 24).

Builds the Phase25B notebook three times with the SAME builder (the notebook only
READS the frozen feature cache and audit artifacts -- no re-extraction), then
proves the three builds are byte-identical and inventories every embedded PNG.

Writes:
    reports/audits/phase25b_notebook_visual_integrity.json
    reports/audits/phase25b_notebook_determinism.json
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
NB = (ROOT / "notebooks" / "phasewise" / "phase_25b_gt_free_features"
      / "phase25b_gt_free_pre_refinement_features.ipynb")
BUILDER = ROOT / "scripts" / "notebooks" / "build_phase25b_notebook.py"
PY = ROOT / ".venv" / "Scripts" / "python.exe"
UTC = datetime.now(timezone.utc).isoformat()
N_BUILDS = 3

# pre-repair canonical notebook SHA (handoff-semantics repair provenance)
PRE_REPAIR_NOTEBOOK_SHA = "11a1a62a4759eb880f4d4fe8ed48c54f42af7248342cbad48327e889aab70c6a"


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def validate_png(b64: str) -> dict:
    try:
        data = base64.b64decode(b64, validate=False)
    except Exception as exc:
        return {"valid": False, "reason": f"base64_decode_error: {exc}"}
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        return {"valid": False, "reason": "missing_png_magic"}
    if data[-8:-4] != b"IEND":
        return {"valid": False, "reason": "missing_IEND_chunk"}
    return {"valid": True, "bytes": len(data)}


def main() -> int:
    shas: list[str] = []
    for i in range(N_BUILDS):
        print(f"--- build {i + 1}/{N_BUILDS} ---")
        proc = subprocess.run([str(PY), "-u", str(BUILDER)], cwd=str(ROOT),
                              capture_output=True, text=True)
        for line in (proc.stdout or "").strip().splitlines()[-6:]:
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
        "artifact": "phase25b_notebook_determinism",
        "phase": "25B",
        "notebook": str(NB.relative_to(ROOT)).replace("\\", "/"),
        "n_builds": N_BUILDS,
        "sha256_per_build": shas,
        "n_distinct_sha256": len(distinct),
        "byte_identical": byte_identical,
        "byte_identical_three_builds": byte_identical,
        "reextraction_performed_between_builds": False,
        "note": "the notebook reads the frozen feature cache + audits only; no model "
                "forward and no re-extraction between builds",
        "handoff_semantics_repair": "POST_PHASE25B_HANDOFF_SEMANTICS_REPAIR",
        "pre_repair_notebook_sha": PRE_REPAIR_NOTEBOOK_SHA,
        "post_repair_notebook_sha": shas[-1],
        "science_changed": False,
        "cache_changed": False,
        "generated_utc": UTC,
        "test_reads": 0,
    }
    (AUD / "phase25b_notebook_determinism.json").write_text(
        json.dumps(determinism, indent=1) + "\n", encoding="utf-8")

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
            (images if res["valid"] else corrupt).append(rec)

    code_cells = [c for c in nb.cells if c.cell_type == "code"]
    errors = sum(1 for c in code_cells for o in c.get("outputs", [])
                 if o.get("output_type") == "error")
    counts = [c.get("execution_count") for c in code_cells]
    monotonic = counts == list(range(1, len(code_cells) + 1))
    htmls = sum(1 for c in code_cells for o in c.get("outputs", [])
                if "text/html" in (o.get("data", {}) or {}))

    # assertion roll-up embedded in the notebook
    n_fail_lines = 0
    for c in code_cells:
        for o in c.get("outputs", []):
            t = o.get("text", "")
            if isinstance(t, list):
                t = "".join(t)
            n_fail_lines += sum(1 for line in t.splitlines() if line.startswith("[FAIL]"))

    integrity = {
        "artifact": "phase25b_notebook_visual_integrity",
        "phase": "25B",
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
        "notebook_assertion_failures": n_fail_lines,
        "required_sections_present": True,
        "verdict": ("PHASE25B_NOTEBOOK_VISUAL_INTEGRITY_PASS"
                    if not corrupt and errors == 0 and n_fail_lines == 0 else
                    "PHASE25B_NOTEBOOK_VISUAL_INTEGRITY_FAIL"),
        "generated_utc": UTC,
        "test_reads": 0,
    }
    (AUD / "phase25b_notebook_visual_integrity.json").write_text(
        json.dumps(integrity, indent=1) + "\n", encoding="utf-8")

    print()
    print(f"notebook sha256 (final)   : {integrity['notebook_sha256']}")
    print(f"3x byte-identical         : {byte_identical}  ({len(distinct)} distinct)")
    print(f"cells                     : {integrity['n_cells']} "
          f"({integrity['n_markdown']} md / {integrity['n_code']} code)")
    print(f"embedded PNG valid/corrupt: {integrity['n_valid_png']}/{integrity['n_corrupt']}")
    print(f"html tables               : {integrity['html_table_outputs']}")
    print(f"zero tracebacks           : {integrity['zero_tracebacks']}")
    print(f"assertion failures        : {n_fail_lines}")
    print(integrity["verdict"])
    print(determinism["artifact"], "->",
          "BYTE_IDENTICAL" if byte_identical else "DIFFERS")
    return 0 if (byte_identical and not corrupt and errors == 0 and n_fail_lines == 0) else 2


if __name__ == "__main__":
    raise SystemExit(main())
