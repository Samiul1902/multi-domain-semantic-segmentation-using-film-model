#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Execute the Phase29 PHASE D notebook 3x and verify deterministic output."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(r"D:\Softfors\jup")
NB = (ROOT / "notebooks" / "phasewise" / "phase_29_3seed_reproducibility" /
      "phase29_phase_d_canonical_three_seed_validation.ipynb")


def code_hashes(nb):
    out = []
    for c in nb.cells:
        if c.cell_type == "code":
            txt = "".join(o.get("text", "") for o in c.get("outputs", [])
                          if o.get("output_type") == "stream")
            out.append(hashlib.sha256(txt.encode("utf-8")).hexdigest())
    return out


runs = []
for i in range(3):
    nb = nbformat.read(str(NB), as_version=4)
    client = NotebookClient(nb, timeout=600, kernel_name="python3",
                            resources={"metadata": {"path": str(ROOT)}})
    client.execute()
    runs.append(code_hashes(nb))
    print(f"run {i+1}: {len(runs[-1])} code cells executed")

deterministic = runs[0] == runs[1] == runs[2]
print("deterministic across 3 runs:", deterministic)

# persist the executed notebook (last run)
nbformat.write(nb, str(NB))
print("saved executed notebook:", NB)
assert deterministic, "notebook output not deterministic"
