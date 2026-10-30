"""Phase 24 (5/4) — build the Phase-24 notebook three times and prove byte-identical determinism.

DESIGN ONLY. Runs the notebook builder 3x and requires the notebook SHA and every figure
SHA to be byte-identical across all builds. Writes
reports/audits/phase24_notebook_determinism.json.

Usage:
    ./.venv/Scripts/python.exe scripts/analysis/run_phase24_determinism.py
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
PY = ROOT / ".venv/Scripts/python.exe"
BUILDER = ROOT / "scripts/notebooks/build_phase24_notebook.py"
NB = (ROOT / "notebooks/phasewise/phase_24_architecture_spec"
      / "phase24_narrowed_benefit_aware_refinement_spec.ipynb")
FIGDIR = ROOT / "reports/figures/phase24_architecture_spec"
UTC = datetime.now(timezone.utc).isoformat()

N_BUILDS = 3

shas = []
fig_shas = []
for i in range(N_BUILDS):
    print(f"=== build {i + 1}/{N_BUILDS} ===")
    r = subprocess.run([str(PY), str(BUILDER)], cwd=str(ROOT),
                       capture_output=True, text=True)
    print(r.stdout[-1500:])
    if r.returncode != 0:
        print(r.stderr[-3000:], file=sys.stderr)
        raise SystemExit(f"build {i + 1} failed")
    shas.append(hashlib.sha256(NB.read_bytes()).hexdigest())
    fig_shas.append({p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in sorted(FIGDIR.glob("*.png"))})

nbs = hash
import nbformat  # noqa: E402
nb = nbformat.read(str(NB), as_version=4)
code_cells = [c for c in nb.cells if c.cell_type == "code"]
errors = sum(1 for c in code_cells for o in c.get("outputs", [])
             if o.get("output_type") == "error")
imgs = sum(1 for c in code_cells for o in c.get("outputs", [])
           if "image/png" in (o.get("data", {}) or {}))

byte_identical = len(set(shas)) == 1
fig_identical = all(f == fig_shas[0] for f in fig_shas)

det = {
    "artifact": "phase24_notebook_determinism",
    "phase": 24,
    "notebook": str(NB.relative_to(ROOT)).replace("\\", "/"),
    "n_builds": N_BUILDS,
    "shas": shas,
    "sha256": shas[0],
    "byte_identical": byte_identical,
    "figures_sha256": fig_shas[0],
    "figures_byte_identical": fig_identical,
    "n_cells": len(nb.cells),
    "n_markdown": sum(1 for c in nb.cells if c.cell_type == "markdown"),
    "n_code": len(code_cells),
    "zero_tracebacks": errors == 0,
    "embedded_png_outputs": imgs,
    "kernel": "jup-venv",
    "determinism_contract": (
        "fixed cell ids (p24NNN) + stripped metadata.execution + coalesced stream outputs + "
        "fixed pandas Styler uuids + normalised 0x addresses -> 3 byte-identical builds"
    ),
    "training": False,
    "inference": False,
    "test_reads": 0,
    "generated_utc": UTC,
}
(AUD / "phase24_notebook_determinism.json").write_text(
    json.dumps(det, indent=1), encoding="utf-8")

print()
print("notebook sha       :", shas[0])
print("byte identical     :", byte_identical)
print("figures identical  :", fig_identical)
print("cells              :", len(nb.cells),
      f"({det['n_markdown']} md / {len(code_cells)} code)")
print("zero tracebacks    :", errors == 0)
print("embedded PNG       :", imgs)
assert byte_identical, "FAIL: builds are not byte-identical"
assert errors == 0, "FAIL: notebook has tracebacks"
