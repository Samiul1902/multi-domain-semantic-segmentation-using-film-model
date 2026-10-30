"""Execute the Phase25G notebook: Run All, visual integrity, 3x byte-identical determinism.

Presentation-only nondeterminism (timestamps, memory addresses, stream chunk boundaries) is
normalised; scientific values, CSV bytes and PNG bytes are never normalised.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import re
import sys
from pathlib import Path

import nbformat as nbf
from nbclient import NotebookClient
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase25g_common as C  # noqa: E402
import build_phase25g_notebook as B  # noqa: E402

NB_PATH = C.NB_DIR / "phase25g_integrated_controlled_evaluation.ipynb"
ADDR = re.compile(r"0x[0-9a-fA-F]{6,}")
ISO = re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(\.\d+)?")


def normalise(nb):
    for cell in nb.cells:
        if cell.get("cell_type") != "code":
            continue
        # presentation-only cell execution timestamps (iopub.execute_input / status.busy /
        # status.idle / shell.execute_reply) are wall-clock and never scientific
        ex = cell.get("metadata", {}).get("execution")
        if isinstance(ex, dict):
            cell["metadata"]["execution"] = {k: "<TS>" for k in sorted(ex)}
        outs = cell.get("outputs", [])
        merged = []
        for o in outs:
            if (merged and o.get("output_type") == "stream"
                    and merged[-1].get("output_type") == "stream"
                    and merged[-1].get("name") == o.get("name")):
                merged[-1]["text"] = "".join([merged[-1]["text"], o["text"]])
            else:
                merged.append(o)
        for o in merged:
            if o.get("output_type") == "stream":
                t = o.get("text", "")
                if isinstance(t, list):
                    t = "".join(t)
                o["text"] = ISO.sub("<TS>", ADDR.sub("0xADDR", t))
            data = o.get("data")
            if isinstance(data, dict):
                for k in ("text/plain", "text/html", "text/markdown", "text/latex"):
                    if k in data:
                        v = data[k]
                        if isinstance(v, list):
                            v = "".join(v)
                        data[k] = ISO.sub("<TS>", ADDR.sub("0xADDR", v))
        cell["outputs"] = merged
    return nb


def execute(nb):
    client = NotebookClient(nb, timeout=3600, kernel_name="jup-venv",
                            resources={"metadata": {"path": str(C.ROOT)}},
                            allow_errors=False)
    client.execute()
    return nb


def hash_nb(nb):
    return hashlib.sha256(nbf.writes(nb).encode("utf-8")).hexdigest()


def visual_integrity(nb):
    pngs, bad = 0, []
    for i, cell in enumerate(nb.cells):
        if cell.get("cell_type") != "code":
            continue
        for j, o in enumerate(cell.get("outputs", [])):
            data = o.get("data") or {}
            if "image/png" not in data:
                continue
            pngs += 1
            raw = data["image/png"]
            try:
                blob = base64.b64decode(raw, validate=True)
            except Exception as e:  # noqa: BLE001
                bad.append({"cell": i, "out": j, "reason": f"base64:{e}"})
                continue
            if not blob.startswith(b"\x89PNG\r\n\x1a\n"):
                bad.append({"cell": i, "out": j, "reason": "magic"})
            if b"IEND" not in blob[-16:]:
                bad.append({"cell": i, "out": j, "reason": "IEND"})
            try:
                Image.open(io.BytesIO(blob)).verify()
            except Exception as e:  # noqa: BLE001
                bad.append({"cell": i, "out": j, "reason": f"pil:{e}"})
    return pngs, bad


def main():
    C.NB_DIR.mkdir(parents=True, exist_ok=True)
    hashes, nb_canonical, errors = [], None, []
    for k in range(3):
        nb = B.build()
        nb = execute(nb)
        nb = normalise(nb)
        nbf.validate(nb)
        code_cells = [c for c in nb.cells if c["cell_type"] == "code"]
        unexec = [i for i, c in enumerate(code_cells) if not c.get("execution_count")]
        errs = [o for c in code_cells for o in c.get("outputs", [])
                if o.get("output_type") == "error"]
        if unexec or errs:
            errors.append({"build": k, "unexecuted": unexec, "errors": len(errs)})
        nbf.write(nb, str(NB_PATH))
        hashes.append(C.sha256_file(NB_PATH))
        if k == 0:
            nb_canonical = nb

    nbf.write(nb_canonical, str(NB_PATH))
    canon = nbf.read(str(NB_PATH), as_version=4)
    nbf.validate(canon)
    code_cells = [c for c in canon.cells if c["cell_type"] == "code"]
    unexecuted = sum(1 for c in code_cells if not c.get("execution_count"))
    ecs = [c.get("execution_count") for c in code_cells]
    monotonic = all(ecs[i] is None or ecs[i] >= (ecs[i - 1] or 0) for i in range(1, len(ecs)))
    err_count = sum(1 for c in code_cells for o in c.get("outputs", [])
                    if o.get("output_type") == "error")
    pngs, bad = visual_integrity(canon)

    det = {
        "artifact": "phase25g_notebook_determinism",
        "phase": "25G", "stage": "NOTEBOOK_DETERMINISM",
        "builds": 3, "sha1": hashes[0], "sha2": hashes[1], "sha3": hashes[2],
        "byte_identical": len(set(hashes)) == 1,
        "normalised_presentation_only": ["timestamps", "text memory addresses",
                                         "stdout stream chunk boundaries"],
        "scientific_values_normalised": False,
        "csv_bytes_normalised": False,
        "png_bytes_normalised": False,
        "errors": errors,
        "all_pass": len(set(hashes)) == 1 and not errors,
    }
    C.write_json(C.AUD / "phase25g_notebook_determinism.json", det)

    vis = {
        "artifact": "phase25g_notebook_visual_integrity",
        "phase": "25G", "stage": "NOTEBOOK_VISUAL_INTEGRITY",
        "embedded_png": pngs, "expected_png_min": 9,
        "strict_base64": True, "png_magic": True, "iend": True, "pil_verify": True,
        "invalid": bad,
        "no_text_regex_over_binary": True,
        "all_pass": len(bad) == 0 and pngs >= 9,
    }
    C.write_json(C.AUD / "phase25g_notebook_visual_integrity.json", vis)

    run = {
        "artifact": "phase25g_notebook_run_all",
        "phase": "25G", "stage": "NOTEBOOK_RUN_ALL",
        "notebook_path": str(NB_PATH.relative_to(C.ROOT)),
        "notebook_sha256": C.sha256_file(NB_PATH),
        "code_cells": len(code_cells),
        "unexecuted": unexecuted, "errors": err_count,
        "execution_counts_monotonic": monotonic,
        "embedded_png": pngs,
        "all_pass": unexecuted == 0 and err_count == 0,
    }
    C.write_json(C.AUD / "phase25g_notebook_run_all.json", run)

    print("NOTEBOOK_SHA", C.sha256_file(NB_PATH))
    print("byte_identical", det["byte_identical"], "| unexecuted", unexecuted,
          "| errors", err_count, "| pngs", pngs, "| invalid", len(bad))
    return 0 if (det["all_pass"] and vis["all_pass"] and run["all_pass"]) else 1


if __name__ == "__main__":
    sys.exit(main())
