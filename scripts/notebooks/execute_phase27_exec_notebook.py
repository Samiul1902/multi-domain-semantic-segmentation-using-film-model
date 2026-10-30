"""Execute the Phase27 reviewer notebook and prove 3x byte-identical determinism.

Workflow
--------
1. Execute a fresh build of the notebook with nbclient (kernel ``jup-venv``).
2. Normalise presentation-only nondeterminism (merge consecutive same-name
   stream outputs, normalise memory addresses and cell execution timestamps).
   Scientific/configuration numbers, artifact SHAs and PNG bytes are NEVER
   normalised.
3. Write the file, hash the FILE (not the in-memory object).
4. Repeat 3x and require a single SHA.
5. Write the visual-integrity and determinism audits.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/notebooks/execute_phase27_exec_notebook.py
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import re
import subprocess
import sys
from pathlib import Path

import nbformat as nbf
from nbclient import NotebookClient

ROOT = Path(r"D:\Softfors\jup")
NB = (ROOT / "notebooks" / "phasewise" / "phase_27_preservation"
      / "phase27_multidomain_preservation_audit.ipynb")
AUD = ROOT / "reports" / "audits"
BUILDER = ROOT / "scripts" / "notebooks" / "build_phase27_exec_notebook.py"

ADDR_RE = re.compile(r"0x[0-9a-fA-F]{6,}")
CONST_TS = "1970-01-01T00:00:00.000000Z"


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def rebuild():
    subprocess.run([sys.executable, str(BUILDER)], check=True,
                   capture_output=True, text=True)


def normalise(nb):
    for cell in nb.cells:
        if cell.cell_type != "code":
            continue
        outs = cell.get("outputs", [])
        merged = []
        for o in outs:
            if (merged and o.get("output_type") == "stream"
                    and merged[-1].get("output_type") == "stream"
                    and merged[-1].get("name") == o.get("name")):
                merged[-1]["text"] = (merged[-1].get("text") or "") + (o.get("text") or "")
            else:
                merged.append(o)
        for o in merged:
            if isinstance(o.get("text"), str):
                o["text"] = ADDR_RE.sub("0xADDR", o["text"])
            data = o.get("data")
            if isinstance(data, dict):
                for key in ("text/plain", "text/html", "text/markdown"):
                    if key in data:
                        v = data[key]
                        if isinstance(v, list):
                            v = "".join(v)
                        data[key] = ADDR_RE.sub("0xADDR", v)
        cell["outputs"] = merged
        md = cell.get("metadata", {})
        if "execution" in md:
            md["execution"] = {k: CONST_TS for k in md["execution"]}
    return nb


def execute_once():
    rebuild()
    nb = nbf.read(str(NB), as_version=4)
    client = NotebookClient(nb, timeout=1800, kernel_name="jup-venv",
                            resources={"metadata": {"path": str(ROOT)}},
                            allow_errors=False)
    client.execute()
    nb = normalise(nb)
    nbf.validate(nb)
    nbf.write(nb, str(NB))
    return sha256_file(NB)


def stats():
    nb = nbf.read(str(NB), as_version=4)
    code = [c for c in nb.cells if c.cell_type == "code"]
    unexecuted = [c for c in code if not c.get("execution_count")]
    errors = [o for c in code for o in c.get("outputs", [])
              if o.get("output_type") == "error"]
    pngs = [o for c in code for o in c.get("outputs", [])
            if "image/png" in (o.get("data", {}) or {})]
    counts = [c.get("execution_count") for c in code if c.get("execution_count")]
    monotonic = counts == sorted(counts)
    return {"n_code": len(code), "unexecuted": len(unexecuted), "errors": len(errors),
            "embedded_png": len(pngs), "execution_counts_monotonic": monotonic,
            "execution_counts": counts}


def visual_integrity():
    from PIL import Image
    nb = nbf.read(str(NB), as_version=4)
    results = []
    for c in nb.cells:
        if c.cell_type != "code":
            continue
        for o in c.get("outputs", []):
            data = o.get("data", {}) or {}
            if "image/png" not in data:
                continue
            b64 = data["image/png"]
            if isinstance(b64, list):
                b64 = "".join(b64)
            raw = base64.b64decode(b64, validate=True)
            magic = raw[:8] == b"\x89PNG\r\n\x1a\n"
            iend = b"IEND" in raw[-16:]
            try:
                Image.open(io.BytesIO(raw)).verify()
                pil = True
            except Exception:  # noqa: BLE001
                pil = False
            results.append({"base64_valid": True, "png_magic": magic,
                            "iend": iend, "pil_verify": pil, "bytes": len(raw)})
    return results


def main():
    shas = [execute_once() for _ in range(3)]
    st = stats()
    vi = visual_integrity()
    deterministic = len(set(shas)) == 1

    vis = {
        "artifact": "phase27_notebook_visual_integrity",
        "phase": "27",
        "method": "RA-MedFiLM-BARR",
        "notebook_path": str(NB.relative_to(ROOT)).replace("\\", "/"),
        "embedded_png_count": len(vi),
        "all_base64_valid": all(r["base64_valid"] for r in vi),
        "all_png_magic_valid": all(r["png_magic"] for r in vi),
        "all_iend_valid": all(r["iend"] for r in vi),
        "all_pil_verify_pass": all(r["pil_verify"] for r in vi),
        "per_png": vi,
        "all_pass": bool(vi) and all(r["png_magic"] and r["iend"] and r["pil_verify"] for r in vi),
    }
    (AUD / "phase27_notebook_visual_integrity.json").write_text(
        json.dumps(vis, indent=1) + "\n", encoding="utf-8")

    det = {
        "artifact": "phase27_notebook_determinism",
        "phase": "27",
        "method": "RA-MedFiLM-BARR",
        "notebook_path": str(NB.relative_to(ROOT)).replace("\\", "/"),
        "builds": 3,
        "shas": shas,
        "three_builds_byte_identical": deterministic,
        "notebook_sha256": shas[-1],
        "normalised_presentation_only": [
            "stdout stream splitting", "memory addresses in text",
            "cell execution timestamps", "stable cell ids",
        ],
        "scientific_numbers_not_normalised": True,
        "artifact_shas_not_normalised": True,
        "png_bytes_not_normalised": True,
        "stats": st,
        "unexecuted": st["unexecuted"],
        "errors": st["errors"],
        "all_pass": bool(deterministic and st["unexecuted"] == 0 and st["errors"] == 0),
    }
    (AUD / "phase27_notebook_determinism.json").write_text(
        json.dumps(det, indent=1) + "\n", encoding="utf-8")

    print("notebook  :", NB)
    print("sha256    :", shas[-1])
    print("3x ident  :", deterministic)
    print("stats     :", st)
    print("pngs      :", len(vi), "valid:", vis["all_png_magic_valid"])
    return 0 if det["all_pass"] and vis["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
