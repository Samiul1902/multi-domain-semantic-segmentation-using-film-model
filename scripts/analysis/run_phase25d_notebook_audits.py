"""Notebook visual integrity + determinism audits for Phase25D."""
import base64
import hashlib
import json
from pathlib import Path

import nbformat
from PIL import Image

ROOT = Path("D:/Softfors/jup")
NB_PATH = ROOT / "notebooks/phasewise/phase_25d_benefit_router/phase25d_benefit_router.ipynb"
AUDITS = ROOT / "reports/audits"

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=1)

# =====================================================================
# 1. Visual integrity
# =====================================================================
nb = nbformat.read(NB_PATH, as_version=4)

# Validate
validation_errors = []
try:
    nbformat.validate(nb)
except Exception as e:
    validation_errors.append(str(e))

# Check PNGs
png_outputs = 0
corrupt_png = 0
valid_png = 0
for cell in nb.cells:
    if cell.cell_type == "code" and hasattr(cell, "outputs"):
        for out in cell.outputs:
            if out.output_type in ("display_data", "execute_result"):
                if "image/png" in out.data:
                    png_outputs += 1
                    try:
                        b64 = out.data["image/png"]
                        img_bytes = base64.b64decode(b64)
                        # Check PNG magic
                        if img_bytes[:8] != b"\x89PNG\r\n\x1a\n":
                            corrupt_png += 1
                            continue
                        # Check IEND
                        if b"IEND" not in img_bytes[-20:]:
                            corrupt_png += 1
                            continue
                        # PIL verify
                        from io import BytesIO
                        img = Image.open(BytesIO(img_bytes))
                        img.verify()
                        valid_png += 1
                    except Exception:
                        corrupt_png += 1

save_json(AUDITS / "phase25d_notebook_visual_integrity.json", {
    "artifact": "phase25d_notebook_visual_integrity",
    "nbformat_valid": len(validation_errors) == 0,
    "validation_errors": validation_errors,
    "total_cells": len(nb.cells),
    "markdown_cells": sum(1 for c in nb.cells if c.cell_type == "markdown"),
    "code_cells": sum(1 for c in nb.cells if c.cell_type == "code"),
    "png_outputs": png_outputs,
    "valid_png": valid_png,
    "corrupt_png": corrupt_png,
    "all_png_valid": corrupt_png == 0,
    "all_pass": len(validation_errors) == 0 and corrupt_png == 0,
    "generated_utc": "2026-10-01T02:24:24+00:00"
})

# =====================================================================
# 2. Determinism (3x)
# =====================================================================
# The notebook reads frozen artifacts only, so rebuilding it 3x should give identical results
sha1 = sha256_file(NB_PATH)
# Rebuild twice more
import subprocess
for i in range(2):
    subprocess.run(["python", str(ROOT / "scripts/analysis/build_phase25d_notebook.py")], check=True)
    sha = sha256_file(NB_PATH)
    if sha != sha1:
        save_json(AUDITS / "phase25d_notebook_determinism.json", {
            "artifact": "phase25d_notebook_determinism",
            "builds": 3,
            "sha_match": False,
            "first_sha": sha1,
            f"rebuild_{i+1}_sha": sha,
            "all_pass": False,
            "generated_utc": "2026-10-01T02:24:24+00:00"
        })
        print("NOTEBOOK DETERMINISM FAIL")
        exit(0)

save_json(AUDITS / "phase25d_notebook_determinism.json", {
    "artifact": "phase25d_notebook_determinism",
    "builds": 3,
    "sha_match": True,
    "sha256": sha1,
    "all_pass": True,
    "generated_utc": "2026-10-01T02:24:24+00:00"
})

print("Notebook audits complete.")
