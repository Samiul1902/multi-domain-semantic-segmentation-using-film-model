#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Execute notebooks/RA_MedFiLM_Phase_Handoff_Builder.ipynb once under the
canonical jup-venv kernel, in-place.  Packaging-only; no science.

Runs with the PROJECT interpreter (this file is invoked via .venv/Scripts/python.exe).
"""
from pathlib import Path
import nbformat
from nbclient import NotebookClient

ROOT = Path(r"D:/Softfors/jup")
NB = ROOT / "notebooks" / "RA_MedFiLM_Phase_Handoff_Builder.ipynb"
nb = nbformat.read(NB, as_version=4)
client = NotebookClient(nb, timeout=600, kernel_name="jup-venv",
                        resources={"metadata": {"path": str(ROOT)}})
client.execute()
nbformat.write(nb, NB)

# print stdout of each code cell
for i, c in enumerate(nb.cells):
    if c.cell_type != "code":
        continue
    for o in c.get("outputs", []):
        if o.get("output_type") == "stream":
            print(o.get("text", ""), end="")
        elif o.get("output_type") == "error":
            print(f"[ERROR {o.get('ename')}] {o.get('evalue')}")
print("NOTEBOOK EXECUTION COMPLETE")
