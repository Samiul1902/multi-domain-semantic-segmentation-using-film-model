#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build AND execute the Phase35 v1.0b synthetic-smoke reviewer notebook (read-only).

Classification: READ_ONLY_PHASE35_V1_0B_SYNTHETIC_SMOKE_REVIEWER_NOTEBOOK
Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/build_phase35_synthetic_smoke_notebook_v1_0b.py
"""
from __future__ import annotations
import hashlib, json
from pathlib import Path
import nbformat
from nbclient import NotebookClient

ROOT = Path(r"D:/Softfors/jup"); AUD = ROOT / "reports" / "audits"
NB = (ROOT / "notebooks" / "phasewise" / "phase_35_interpretability" /
      "phase35_interpretability_synthetic_smoke_v1_0b_review.ipynb")
KERNEL = "jup-venv"; REVISION = "ra_medfilm_barr_phase35_interpretability_v1_0b"
SETUP = '''\
import hashlib
import json
from pathlib import Path
import pandas as pd
ROOT = Path(r"D://Softfors//jup"); AUD = ROOT / "reports" / "audits"
def jload(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))
print("Phase35 v1.0b synthetic-smoke gate review (READ-ONLY)")
print("No model construction, no checkpoint deserialization, no forward, no autograd, no images.")
'''
CELLS = []
_META = {"kernelspec": {"display_name": "Python 3", "language": "python", "name": KERNEL},
         "language_info": {"name": "python", "version": "3.11.9"}}
def md(s): CELLS.append({"cell_type": "markdown", "id": f"cell{len(CELLS):03d}", "metadata": {}, "source": s})
def code(s): CELLS.append({"cell_type": "code", "id": f"cell{len(CELLS):03d}", "execution_count": None, "metadata": {}, "outputs": [], "source": s})

md(f"""# Phase 35 v1.0b — Synthetic Interpretability Smoke Gate
## Reviewer Notebook (read-only)

**Classification:** `READ_ONLY_PHASE35_V1_0B_SYNTHETIC_SMOKE_REVIEWER_NOTEBOOK`
**Revision:** `{REVISION}`

This notebook reviews the synthetic smoke gate outcome. The authorized synthetic interface
validation could **not** be performed because the frozen v1.0b `--mode smoke` entry point is a stub.
""")
md("## 0. Setup"); code(SETUP)
md("## 1. Gates (source, gallery, environment, checkpoints)")
code('''\
sm = jload(AUD / "phase35_synthetic_interpretability_smoke_v1_0b.json")
print("source hash gate:", sm["source_hash_gate"])
print("gallery authority gate:", sm["gallery_authority_gate"])
print("environment gate pass:", sm["environment_gate_pass"])
print("all checkpoint hashes match:", sm["all_checkpoint_hashes_match"])
for c in sm["checkpoint_sha_results"]:
    print(f"  {c['component']:8s} match={c['match']} deserialized={c['deserialized']}")
''')
md("## 2. Frozen --mode smoke outcome (the block)")
code('''\
print("frozen smoke mode invoked:", sm["frozen_smoke_mode_invoked"])
print("frozen smoke mode implemented the authorized smoke:",
      sm["frozen_smoke_mode_implemented_the_authorized_smoke"])
print("counts match expected:", sm["counts_match"])
print()
print("expected counts:", json.dumps(sm["expected_counts"], indent=1))
print("actual frozen counts:", json.dumps(sm["actual_frozen_counts"], indent=1))
print()
print("root cause:", sm["root_cause"])
''')
md("## 3. Interface checks not reached")
code('''\
for k in ("strict_load_results", "parameter_identities", "film_smoke", "embedding_smoke",
          "gradcam_smoke", "router_smoke", "zero_denominator_policy_test",
          "parameter_immutability"):
    print(f"  {k:32s} = {sm[k]}")
''')
md("## 4. Protected-data counters")
code('''\
for k, v in sm["protected_data_counters"].items():
    print(f"  {k:42s} = {v}")
''')
md("## 5. Final check and terminal")
code('''\
fc = jload(AUD / "phase35_synthetic_smoke_final_check_v1_0b.json")
print("final check:", fc["n_checks"], "checks,", fc["n_failed"], "failed")
t = jload(AUD / "phase35_synthetic_smoke_terminal_v1_0b.json")
print()
print("terminal:"); print(" ", t["terminal"])
print()
print("required remediation:"); print(" ", t["required_remediation"])
''')
md("""---
## Summary

| item | value |
|---|---|
| source / gallery / environment / checkpoint gates | ALL PASS |
| frozen `--mode smoke` | invoked; **stub** (0 constructions, 0 forwards, 0 autograd, 0 CAM) |
| authorized synthetic smoke | **NOT PERFORMED** (blocked) |
| raw VAL · persisted VAL prob · GT · holdout · TEST reads | 0 · 0 · 0 · 0 · 0 |
| scientific outputs · training | 0 · 0 |
| Phase35 scientific execution | NOT started · Phase36 NOT started · TEST locked |
""")

def build():
    nb = {"cells": CELLS, "metadata": dict(_META), "nbformat": 4, "nbformat_minor": 5}
    NB.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(nbformat.from_dict(nb), str(NB)); return nbformat.read(str(NB), as_version=4)
def normalize(nb):
    for i, c in enumerate(nb.cells):
        c["id"] = f"cell{i:03d}"; c.setdefault("metadata", {}).pop("execution", None)
        merged = []
        for o in c.get("outputs", []):
            o.pop("metadata", None)
            if (merged and o.get("output_type") == "stream" and merged[-1].get("output_type") == "stream"
                    and merged[-1].get("name") == o.get("name")):
                merged[-1]["text"] = merged[-1]["text"] + o["text"]
            else: merged.append(o)
        if c.cell_type == "code": c["outputs"] = merged
    nb.metadata = dict(_META); return nb
def execute(nb):
    NotebookClient(nb, kernel_name=KERNEL, timeout=900, allow_errors=False, record_timing=False).execute()
    normalize(nb); nbformat.write(nb, str(NB)); return nb
def sha256_file(p):
    h = hashlib.sha256(); h.update(Path(p).read_bytes()); return h.hexdigest()
def main():
    build(); hashes = []
    for _ in range(3):
        nb = nbformat.read(str(NB), as_version=4); execute(nb); hashes.append(sha256_file(NB))
    nb = nbformat.read(str(NB), as_version=4)
    n_md = sum(1 for c in nb.cells if c.cell_type == "markdown")
    n_code = sum(1 for c in nb.cells if c.cell_type == "code")
    n_exec = sum(1 for c in nb.cells if c.cell_type == "code" and c.get("execution_count") is not None)
    errs = sum(1 for c in nb.cells for o in c.get("outputs", []) if o.get("output_type") == "error")
    print("notebook:", NB); print("cells:", len(nb.cells), "| md:", n_md, "| code:", n_code, "| executed:", n_exec)
    print("errors:", errs); print("3 replays byte-identical:", len(set(hashes)) == 1)
    print("notebook sha256:", hashes[-1])
    audit = {"artifact": "phase35_synthetic_smoke_reviewer_notebook_audit_v1_0b", "phase": 35,
             "section": "\u00A7W", "method": "RA-MedFiLM-BARR", "revision": REVISION,
             "path": str(NB.relative_to(ROOT)).replace("\\", "/"), "sha256": hashes[-1],
             "cell_count": len(nb.cells), "markdown_cells": n_md, "code_cells": n_code,
             "executed_code_cells": n_exec, "error_cells": errs, "replay_count": 3,
             "replays_byte_identical": len(set(hashes)) == 1,
             "synthetic_smoke_rerun_between_renders": False,
             "counters": {"model_constructions": 0, "checkpoint_deserializations": 0,
                          "model_forwards": 0, "autograd_calls": 0, "raw_image_reads": 0,
                          "persisted_val_probability_reads": 0, "raw_GT_reads": 0,
                          "ROUTER_HOLDOUT_raw_reads": 0, "TEST_reads": 0, "training_steps": 0},
             "all_counters_zero": True, "all_pass": errs == 0 and n_exec == n_code}
    p = AUD / "phase35_synthetic_smoke_reviewer_notebook_audit_v1_0b.json"
    p.write_text(json.dumps(audit, indent=1) + "\n", encoding="utf-8")
    print("wrote", p); print("audit sha256:", sha256_file(p))
if __name__ == "__main__":
    main()
