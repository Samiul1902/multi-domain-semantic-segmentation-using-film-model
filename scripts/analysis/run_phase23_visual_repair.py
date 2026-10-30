"""Phase 23 — reviewer-visual repair: determinism verifier + provenance writer.

PRESENTATION-ONLY REPAIR. This script does NOT rerun literature research, does NOT
change the novelty verdict, does NOT train, does NOT run inference, and does NOT
touch TEST.

It:
  1. builds the Phase-23 notebook THREE consecutive times;
  2. requires the three SHA-256 values to be byte-identical;
  3. writes reports/audits/phase23_notebook_visual_determinism.json
  4. writes reports/audits/phase23_reviewer_visual_repair.json (provenance)

Usage
-----
    ./.venv/Scripts/python.exe scripts/analysis/run_phase23_visual_repair.py
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
FIG = ROOT / "reports" / "figures" / "phase23_novelty_audit"
NB = ROOT / "notebooks/phasewise/phase_23_literature_novelty/phase23_literature_methodological_novelty_audit.ipynb"
PY = ROOT / ".venv/Scripts/python.exe"

OLD_NB_SHA = "cc86153c5011cc83ff787dcda797ecf5a20ef50c15f76eceeba5c9d911934f2e"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    builds = []
    for i in range(3):
        r = subprocess.run(
            [str(PY), "scripts/notebooks/build_phase23_notebook.py"],
            cwd=str(ROOT), capture_output=True, text=True, timeout=5400,
        )
        if r.returncode != 0:
            print(f"BUILD {i + 1} FAILED\n{r.stdout[-3000:]}\n{r.stderr[-3000:]}")
            return 1
        h = sha(NB)
        builds.append(h)
        print(f"  build {i + 1}: {h}")

    identical = len(set(builds)) == 1
    new_sha = builds[-1]

    # rebuild figures 3x as well and require identical SHAs
    fig_shas = []
    for i in range(3):
        r = subprocess.run(
            [str(PY), "scripts/analysis/build_phase23_visuals.py"],
            cwd=str(ROOT), capture_output=True, text=True, timeout=1800,
        )
        if r.returncode != 0:
            print(f"FIGURE BUILD {i + 1} FAILED\n{r.stderr[-2000:]}")
            return 1
        fig_shas.append({p.name: sha(p) for p in sorted(FIG.glob("p23_*.png"))})

    figs_identical = all(f == fig_shas[0] for f in fig_shas)

    # notebook-level visual census from the actual bytes
    import base64
    import ast
    nb = json.loads(NB.read_text(encoding="utf-8"))
    pngs = []
    for ci, c in enumerate(nb["cells"]):
        if c.get("cell_type") != "code":
            continue
        for oi, o in enumerate(c.get("outputs", []) or []):
            d = o.get("data", {}) or {}
            if "image/png" in d:
                v = d["image/png"]
                if isinstance(v, list):
                    v = "".join(v)
                raw = base64.b64decode(v)
                pngs.append({"cell_index": ci, "cell_id": c.get("id"),
                             "output_index": oi, "bytes": len(raw),
                             "sha256": hashlib.sha256(raw).hexdigest()})
    code_cells = [c for c in nb["cells"] if c.get("cell_type") == "code"]
    errors = sum(1 for c in code_cells for o in (c.get("outputs") or [])
                 if o.get("output_type") == "error")
    counts = [c.get("execution_count") for c in code_cells]
    monotonic = all(counts[i] == i + 1 for i in range(len(counts)))

    det = {
        "artifact": "phase23_notebook_visual_determinism",
        "phase": 23,
        "classification": "REVIEWER_PRESENTATION_REPAIR",
        "old_notebook_sha256": OLD_NB_SHA,
        "new_notebook_sha256": new_sha,
        "three_build_sha256": builds,
        "three_builds_byte_identical": identical,
        "figures_three_build_sha256": fig_shas[0],
        "figures_three_builds_byte_identical": figs_identical,
        "visual_count": len(pngs),
        "visuals": pngs,
        "error_count": errors,
        "monotonic_execution_counts": monotonic,
        "n_cells": len(nb["cells"]),
        "n_markdown": sum(1 for c in nb["cells"] if c.get("cell_type") == "markdown"),
        "n_code": len(code_cells),
        "phase24_started": False,
        "training": False,
        "inference": False,
        "test_reads": 0,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
    }
    (AUD / "phase23_notebook_visual_determinism.json").write_text(
        json.dumps(det, indent=1), encoding="utf-8")

    print()
    print(f"  three builds identical : {identical}")
    print(f"  figures identical      : {figs_identical}")
    print(f"  visuals in notebook    : {len(pngs)}")
    print(f"  0 errors               : {errors == 0}")
    print(f"  monotonic exec counts  : {monotonic}")

    if not (identical and figs_identical and errors == 0 and monotonic):
        print("FAIL-CLOSED: determinism contract not met")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
