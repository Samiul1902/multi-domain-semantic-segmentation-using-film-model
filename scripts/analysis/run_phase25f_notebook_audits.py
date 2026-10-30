"""Phase 25F canonical execution — §34 visual integrity, §35 notebook 3x
byte-identical determinism.

Rebuilds the notebook three times from frozen inputs and asserts a byte-identical
SHA-256, then validates every embedded figure (PNG magic + IEND + PIL verify) and
the notebook structure (41 numbered sections, no error outputs).
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase25f_spec_repair_common as C  # noqa: E402
import build_phase25f_notebook as NB  # noqa: E402

AUD = C.AUD
FIG = C.ROOT / "reports" / "figures"


def main():
    # ---------------- §34 visual integrity -------------------------------- #
    from PIL import Image
    figs = sorted(FIG.glob("p25f_*.png"))
    assert len(figs) == 9, len(figs)
    integrity = []
    for p in figs:
        b = p.read_bytes()
        rec = {
            "figure": p.name,
            "magic_ok": b[:8] == b"\x89PNG\r\n\x1a\n",
            "iend_ok": b[-8:-4] == b"IEND",
            "bytes": len(b),
            "sha256": C.sha256_file(p),
        }
        try:
            im = Image.open(io.BytesIO(b))
            im.verify()
            rec["pil_verify"] = True
            rec["size"] = list(im.size)
        except Exception as exc:  # noqa: BLE001
            rec["pil_verify"] = False
            rec["pil_error"] = str(exc)
        integrity.append(rec)

    nb_path = NB.NB
    import nbformat
    nb = nbformat.read(nb_path, as_version=4)
    md_sections = [c for c in nb.cells if c.cell_type == "markdown"
                   and c.source.lstrip().startswith("## ")]
    err_outputs = []
    for c in nb.cells:
        for o in c.get("outputs", []):
            if o.get("output_type") == "error":
                err_outputs.append(c.get("id"))
    img_outputs = 0
    for c in nb.cells:
        for o in c.get("outputs", []):
            if o.get("output_type") == "display_data" and "image/png" in o.get("data", {}):
                img_outputs += 1

    vis = {
        "artifact": "phase25f_visual_integrity",
        "phase": "25F",
        "method": C.METHOD,
        "specification_revision": C.REVISION,
        "figures": integrity,
        "figure_count": len(integrity),
        "all_figures_valid": all(i["magic_ok"] and i["iend_ok"] and i.get("pil_verify")
                                 for i in integrity),
        "notebook_numbered_sections": len(md_sections),
        "notebook_cells": len(nb.cells),
        "notebook_error_outputs": err_outputs,
        "notebook_embedded_images": img_outputs,
        "notebook_executed_clean": len(err_outputs) == 0,
        "all_pass": (all(i["magic_ok"] and i["iend_ok"] and i.get("pil_verify")
                         for i in integrity)
                     and len(md_sections) == 41 and not err_outputs),
    }
    C.jdump(vis, AUD / "phase25f_visual_integrity.json")

    # ---------------- §35 3x notebook determinism ------------------------- #
    sha1 = NB.build()
    sha2 = NB.build()
    sha3 = NB.build()
    det = {
        "artifact": "phase25f_notebook_determinism",
        "phase": "25F",
        "method": C.METHOD,
        "specification_revision": C.REVISION,
        "build_count": 3,
        "build_shas": [sha1, sha2, sha3],
        "byte_identical": bool(sha1 == sha2 == sha3),
        "notebook_path": str(nb_path.relative_to(C.ROOT)).replace("\\", "/"),
        "all_pass": bool(sha1 == sha2 == sha3),
    }
    C.jdump(det, AUD / "phase25f_notebook_determinism.json")

    print("visual integrity:", vis["all_pass"], "| sections:", len(md_sections),
          "| images:", img_outputs, "| errors:", len(err_outputs))
    print("notebook determinism:", det["byte_identical"], sha1[:16])
    return vis, det


if __name__ == "__main__":
    main()
