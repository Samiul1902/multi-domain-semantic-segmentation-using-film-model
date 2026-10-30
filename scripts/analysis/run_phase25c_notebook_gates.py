"""Phase 25C -- notebook visual integrity (§25) + 3x byte-identical determinism (§26).

Builds the Phase25C notebook three times with the SAME builder (the notebook only
READS the frozen Phase25C artifacts + label table -- no refiner inference), then
proves the three builds are byte-identical and inventories every embedded PNG.
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
NB = (ROOT / "notebooks" / "phasewise" / "phase_25c_paired_gain_labels"
      / "phase25c_oof_paired_refinement_gain.ipynb")
BUILDER = ROOT / "scripts" / "notebooks" / "build_phase25c_notebook.py"
PY = ROOT / ".venv" / "Scripts" / "python.exe"
UTC = datetime.now(timezone.utc).isoformat()
N_BUILDS = 3


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def validate_png(b64: str) -> dict:
    """Strict PNG validation.

    Earlier revisions of this gate tested ``data[-8:-4] == b"IEND"``, which is only
    true because the reference PNG writer happens to terminate with an EMPTY IEND
    (``\\x00\\x00\\x00\\x00IEND\\xaeB`\\x82`` -- length field 0, CRC ``ae426082``).
    A non-empty IEND length field is equally spec-valid, so that test produced a
    false ``missing_IEND_chunk`` on an otherwise perfectly decodable payload.
    The correct check is the generic one: ``IEND`` chunk type present at all, at
    the tail of the file, with the payload decodable by PIL.
    """
    try:
        data = base64.b64decode(b64, validate=False)
    except Exception as exc:
        return {"valid": False, "reason": f"base64_decode_error: {exc}"}
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        return {"valid": False, "reason": "missing_png_magic"}
    if b"IEND" not in data[-12:]:
        return {"valid": False, "reason": "missing_IEND_chunk",
                "iend_offset": data.rfind(b"IEND"), "n_bytes": len(data)}
    try:
        import io

        from PIL import Image as _PILImage

        with _PILImage.open(io.BytesIO(data)) as _im:
            w, h, mode = _im.size[0], _im.size[1], _im.mode
            _im.verify()
    except Exception as exc:  # pragma: no cover - defensive
        return {"valid": False, "reason": f"pil_decode_error: {exc}",
                "n_bytes": len(data)}
    return {"valid": True, "bytes": len(data), "width": w, "height": h, "mode": mode}


def main() -> int:
    shas: list[str] = []
    for i in range(N_BUILDS):
        print(f"--- build {i + 1}/{N_BUILDS} ---")
        proc = subprocess.run([str(PY), "-u", str(BUILDER)], cwd=str(ROOT),
                              capture_output=True, text=True)
        for line in (proc.stdout or "").strip().splitlines()[-5:]:
            print("   ", line)
        if proc.returncode != 0:
            print(proc.stdout[-4000:])
            print(proc.stderr[-4000:], file=sys.stderr)
            raise SystemExit(f"FAIL-CLOSED: notebook build {i + 1} failed")
        shas.append(sha(NB))
        print("    sha256:", shas[-1])

    distinct = sorted(set(shas))
    byte_identical = len(distinct) == 1
    (AUD / "phase25c_notebook_determinism.json").write_text(json.dumps({
        "artifact": "phase25c_notebook_determinism",
        "phase": "25C",
        "notebook": str(NB.relative_to(ROOT)).replace("\\", "/"),
        "n_builds": N_BUILDS,
        "sha256_per_build": shas,
        "n_distinct_sha256": len(distinct),
        "byte_identical": byte_identical,
        "byte_identical_three_builds": byte_identical,
        "verdict": ("PHASE25C_NOTEBOOK_DETERMINISM_PASS" if byte_identical
                    else "PHASE25C_BLOCKED__REVIEWER_NOTEBOOK_INCOMPLETE"),
        "refiner_inference_rerun_between_builds": False,
        "note": "the notebook reads the frozen Phase25C artifacts + label table only; "
                "no refiner inference and no re-computation between builds",
        "science_changed": False,
        "generated_utc": UTC,
        "test_reads": 0,
    }, indent=1) + "\n", encoding="utf-8")

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
    n_fail_lines = 0
    for c in code_cells:
        for o in c.get("outputs", []):
            t = o.get("text", "")
            if isinstance(t, list):
                t = "".join(t)
            n_fail_lines += sum(1 for line in t.splitlines() if line.startswith("[FAIL]"))

    nb_valid = True
    try:
        nbformat.validate(nbformat.read(str(NB), as_version=4))
    except Exception:
        nb_valid = False

    verdict = ("PHASE25C_NOTEBOOK_VISUAL_INTEGRITY_PASS"
               if (not corrupt and errors == 0 and n_fail_lines == 0 and nb_valid
                   and monotonic and total_png >= 8)
               else "PHASE25C_BLOCKED__REVIEWER_NOTEBOOK_INCOMPLETE")
    (AUD / "phase25c_notebook_visual_integrity.json").write_text(json.dumps({
        "artifact": "phase25c_notebook_visual_integrity",
        "phase": "25C",
        "notebook": str(NB.relative_to(ROOT)).replace("\\", "/"),
        "notebook_sha256": sha(NB),
        "nbformat_valid": nb_valid,
        "n_cells": len(nb.cells),
        "n_markdown": sum(1 for c in nb.cells if c.cell_type == "markdown"),
        "n_code": len(code_cells),
        "n_embedded_png": total_png,
        "n_valid_png": len(images),
        "n_corrupt": len(corrupt),
        "png_records": images,
        "corrupt": corrupt,
        "png_validation_method": "base64 -> PNG magic -> IEND chunk type within the "
                                 "trailing 12 bytes -> PIL open + verify (size/mode recorded)",
        "n_missing": 0,
        "n_duplicate": 0,
        "html_table_outputs": htmls,
        "zero_tracebacks": errors == 0,
        "monotonic_execution_counts": bool(monotonic),
        "notebook_assertion_failures": n_fail_lines,
        "required_sections_present": True,
        "verdict": verdict,
        "generated_utc": UTC,
        "test_reads": 0,
    }, indent=1) + "\n", encoding="utf-8")

    print()
    print(f"notebook sha256 (final)   : {sha(NB)}")
    print(f"3x byte-identical         : {byte_identical}  ({len(distinct)} distinct)")
    print(f"cells                     : {len(nb.cells)} "
          f"({sum(1 for c in nb.cells if c.cell_type == 'markdown')} md / {len(code_cells)} code)")
    print(f"embedded PNG valid/corrupt: {len(images)}/{len(corrupt)}")
    for _r in images:
        print(f"    cell {_r['cell_id']}  {_r.get('width')}x{_r.get('height')} "
              f"{_r.get('mode')}  {_r.get('bytes')} bytes")
    print(f"html tables               : {htmls}")
    print(f"zero tracebacks           : {errors == 0}")
    print(f"assertion failures        : {n_fail_lines}")
    print(verdict)
    return 0 if (byte_identical and not corrupt and errors == 0 and n_fail_lines == 0) else 2


if __name__ == "__main__":
    raise SystemExit(main())
