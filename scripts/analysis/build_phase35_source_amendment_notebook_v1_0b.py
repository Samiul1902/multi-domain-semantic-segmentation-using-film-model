#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build AND execute the Phase35 v1.0b executable-source-amendment reviewer notebook.

Classification: READ_ONLY_PHASE35_V1_0B_EXECUTABLE_SOURCE_AMENDMENT_REVIEWER_NOTEBOOK

Reads ONLY amendment artifacts. Never constructs models, deserializes checkpoints, runs forwards,
runs autograd, reads raw images, runs saliency/router attribution, opens protected data or trains.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/build_phase35_source_amendment_notebook_v1_0b.py
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(r"D:\Softfors\jup")
AUD = ROOT / "reports" / "audits"
NB = (ROOT / "notebooks" / "phasewise" / "phase_35_interpretability" /
      "phase35_interpretability_source_amendment_v1_0b_review.ipynb")
KERNEL = "jup-venv"
REVISION = "ra_medfilm_barr_phase35_interpretability_v1_0b"

SETUP = '''\
import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(r"D:\\Softfors\\jup")
AUD = ROOT / "reports" / "audits"


def jload(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def tshow(name, n=None):
    df = pd.read_csv(ROOT / name)
    print(name, "| shape:", df.shape)
    if n is not None:
        df = df.head(n)
    with pd.option_context("display.max_columns", None, "display.width", 260):
        print(df.to_string(index=False))
    return df


print("Phase35 v1.0b executable-source amendment review")
print("READ-ONLY. No model construction, no checkpoint deserialization, no forward, no autograd,")
print("no raw images, no saliency, no router attribution, no protected data, no training.")
'''

CELLS = []
_FIXED_META = {"kernelspec": {"display_name": "Python 3", "language": "python",
                              "name": KERNEL},
               "language_info": {"name": "python", "version": "3.11.9"}}


def md(s):
    CELLS.append({"cell_type": "markdown", "id": f"cell{len(CELLS):03d}",
                  "metadata": {}, "source": s})


def code(s):
    CELLS.append({"cell_type": "code", "id": f"cell{len(CELLS):03d}",
                  "execution_count": None, "metadata": {}, "outputs": [], "source": s})


md(f"""# Phase 35 v1.0b — Executable Interpretability Source Amendment
## Reviewer Notebook

**Classification:** `READ_ONLY_PHASE35_V1_0B_EXECUTABLE_SOURCE_AMENDMENT_REVIEWER_NOTEBOOK`
**Revision:** `{REVISION}`

Chronology: **v1.0** scientific specification = VALID, execution source = SKELETON/NON-EXECUTABLE ·
**v1.0a** = CORRECTLY BLOCKED PREMODEL (25/54 checks failed) · **v1.0b** = additive executable
implementation repair **before the first model construction**. No scientific output has occurred.
""")

md("## 0. Setup")
code(SETUP)

md("## 1. v1.0a blocked-attempt evidence (preserved)")
code('''\
pf0 = jload(AUD / "phase35_execution_source_static_preflight_v1_0a.json")
print("v1.0a static preflight:", pf0["n_checks"], "checks,", pf0["n_failed"], "failed",
      "| pass:", pf0["static_source_preflight_pass"])
for k in pf0["failed"]:
    print("  FAILED:", k)
t0 = jload(AUD / "phase35_preexecution_smoke_terminal_v1_0a.json")
print()
print("v1.0a terminal:", t0["terminal"])
''')

md("## 2. Gallery reconciliation (CASE 1)")
code('''\
rec = jload(AUD / "phase35_gallery_sha_reconciliation_v1_0a.json")
print("current gallery SHA :", rec["current_file_sha256"])
print("canonical gallery SHA:", rec["canonical_phase21_sha256"])
print("case:", rec["case"])
print("classification:", rec["classification"])
print("b7d8 files found:", rec["b7d8_files_found"] or "NONE")
print("additive rebind required:", rec["v1_0_artifact_requires_additive_rebind"])
''')

md("## 3. Defect record")
code('''\
dr = jload(AUD / "phase35_v1_0_execution_source_defect_record_v1_0b.json")
print("classification:", dr["classification"])
print("v1.0 specification invalidated:", dr["v1_0_scientific_specification_invalidated"])
print("v1.0 execution source executable for science:",
      dr["v1_0_execution_source_executable_for_science"])
print("v1.0a block correct:", dr["v1_0a_block_correct"],
      "| checks:", dr["v1_0a_static_checks"], "| failures:", dr["v1_0a_static_failures"])
print("model constructions before repair:", dr["model_constructions_before_repair"],
      "| raw VAL reads:", dr["raw_VAL_reads_before_repair"],
      "| scientific results invalidated:", dr["scientific_results_invalidated"])
''')

md("## 4. v1.0b static preflight (54 original + additional)")
code('''\
pf = jload(AUD / "phase35_execution_source_static_preflight_v1_0b.json")
print("inspection:", pf["method_of_inspection"])
print("ORIGINAL 54 checks:", pf["original_n_checks"], "| failed:", pf["original_n_failed"],
      "| all pass:", pf["original_54_all_pass"])
print("ADDITIONAL v1.0b checks:", pf["additional_n_checks"], "| failed:",
      pf["additional_n_failed"])
print("TOTAL:", pf["total_n_checks"], "checks,", pf["total_n_failed"], "failed")
print("static_source_preflight_pass:", pf["static_source_preflight_pass"])
print()
print("additional v1.0b checks:")
for k, v in pf["additional_v1_0b_checks"].items():
    print(f"  {'PASS' if v else 'FAIL'}  {k}")
''')

md("## 5. Implementation map — gates, guards, loaders")
code('''\
ex = (ROOT / "scripts/analysis/phase35_interpretability_execution_v1_0b.py").read_text(encoding="utf-8")
cm = (ROOT / "scripts/analysis/phase35_interpretability_common_v1_0b.py").read_text(encoding="utf-8")
for label, token in [
    ("repo root from __file__", "Path(__file__).resolve().parents[2]"),
    ("authority gates", "AUTHORITY_GATES"),
    ("gallery allow-list", "load_gallery_allowlist"),
    ("protected-data guard", "guard_raw_path"),
    ("GT-key prohibition", "PERSISTED_KEYS_FORBIDDEN"),
    ("R_psi/S_omega guard", "_assert_executable_component"),
    ("G loader", "def load_g_component"),
    ("B_phi loader", "def load_bphi_component"),
    ("strict load", "strict=True"),
    ("FiLM accessor", "film_parameters_for_tasks"),
    ("task embeddings", "extract_task_embeddings"),
    ("bridge hook", 'film_layers["bridge"]'),
    ("decoder1 hook", 'film_layers["decoder1"]'),
    ("persisted p_global", "load_persisted_p_global"),
    ("seg 0.50 mask", "build_target_mask"),
    ("ROI 0.30 mask", "build_roi_mask"),
    ("autograd.grad CAM", "torch.autograd.grad"),
    ("router normalization", "router_normalized_features"),
    ("router Gradient x Input", "router_gradient_x_input"),
    ("zero-denominator policy", "ZERO_ROUTER_GRAD_ATTRIBUTION"),
    ("claim guard", "assert_claim_language"),
    ("display subset", "resolve_display_subset"),
]:
    src = cm if token in cm else ex
    print(f"  {'OK ' if token in src else 'MISSING'}  {label:28s} <- {token}")
''')

md("## 6. Threshold separation and target provenance")
code('''\
for line in cm.splitlines():
    if "T_SEGMENTATION_OUTPUT =" in line or "T_ROI_PROPOSAL =" in line or "assert T_" in line:
        print("  ", line.strip())
print()
print("target mask source:", [l.strip() for l in cm.splitlines()
                              if "TARGET_MASK_SOURCE" in l][0])
print("current-forward mask prohibited:", "TARGET_MASK_FROM_CURRENT_FORWARD_PROHIBITED" in cm)
''')

md("## 7. Router population and feature schema")
code('''\
for line in cm.splitlines():
    if any(t in line for t in ("ROUTER_CACHE_ROOT", "ROUTER_POPULATION_N",
                               "ROUTER_NORMALIZED_SCALAR_INDICES",
                               "ROUTER_NORMALIZATION_AUTHORITY =", "ROUTER_FEATURE_SCHEMA =")):
        print("  ", line.strip())
print()
print("feature groups:", [l.strip() for l in cm.splitlines() if "bridge_global" in l][0])
''')

md("## 8. Source freeze and execution eligibility")
code('''\
sf = jload(AUD / "phase35_preexecution_source_freeze_v1_0b.json")
for k, v in sf["frozen_sources"].items():
    print(f"  {v['sha256'][:16]}...  {k:26s} {v['path']}")
print()
print("v1.0 specification preserved:", sf["v1_0_specification_preserved"])
print("v1.0a block preserved:", sf["v1_0a_block_preserved"])
print("v1.0 execution source superseded:", sf["v1_0_execution_source_superseded_for_future_execution"])
print("Phase35 scientific output already produced:", sf["Phase35_scientific_output_already_produced"])
print()
el = jload(AUD / "phase35_execution_eligibility_adjudication_v1_0b.json")
for k, v in el["families"].items():
    print(f"  {k:52s} = {str(v['value']):5s}")
''')

md("## 9. Zero-execution audit, final check and terminal")
code('''\
ne = jload(AUD / "phase35_v1_0b_no_execution_audit.json")
for k, v in ne["counters"].items():
    print(f"  {k:36s} = {v}")
print("all zero:", ne["all_zero"])
assert ne["all_zero"]
print()
fc = jload(AUD / "phase35_source_amendment_final_check_v1_0b.json")
print("final check:", fc["n_checks"], "checks,", fc["n_failed"], "failed")
t = jload(AUD / "phase35_source_amendment_terminal_v1_0b.json")
print()
print("terminal:")
print(" ", t["terminal"])
''')

md("""---
## Summary

| item | value |
|---|---|
| v1.0 specification | VALID and preserved byte-for-byte |
| v1.0a block | preserved; 25/54 defects disclosed |
| v1.0b static preflight | 54 original + 18 additional = **72 checks, 0 failures** |
| gallery | `2bc7c162…` canonical, 64 unique, 16/domain, 0 holdout, 0 TEST |
| executable components | G · B_phi only (R_psi / S_omega raise) |
| Grad-CAM hooks | `film_layers["bridge"]` `[1,256,32,32]` · `film_layers["decoder1"]` `[1,24,512,512]` |
| target mask | persisted `p_global >= 0.50`; current-forward mask forbidden |
| thresholds | segmentation 0.50 · ROI proposal 0.30 (asserted distinct) |
| router | VAL808 n=808, canonical Phase25D normalization, Gradient × Input on raw `delta_hat` |
| model loads · forwards · autograd · saliency · attribution | 0 · 0 · 0 · 0 · 0 |
| raw VAL / GT / holdout / TEST reads | 0 · 0 · 0 · 0 |
| Phase35 execution | NOT started · Phase36 NOT started · TEST locked |
""")


def build():
    nb = {"cells": CELLS, "metadata": dict(_FIXED_META), "nbformat": 4, "nbformat_minor": 5}
    NB.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(nbformat.from_dict(nb), str(NB))
    return nbformat.read(str(NB), as_version=4)


def normalize(nb):
    for i, c in enumerate(nb.cells):
        c["id"] = f"cell{i:03d}"
        c.setdefault("metadata", {}).pop("execution", None)
        merged = []
        for o in c.get("outputs", []):
            o.pop("metadata", None)
            if (merged and o.get("output_type") == "stream"
                    and merged[-1].get("output_type") == "stream"
                    and merged[-1].get("name") == o.get("name")):
                merged[-1]["text"] = merged[-1]["text"] + o["text"]
            else:
                merged.append(o)
        if c.cell_type == "code":
            c["outputs"] = merged
    nb.metadata = dict(_FIXED_META)
    return nb


def execute(nb):
    NotebookClient(nb, kernel_name=KERNEL, timeout=900, allow_errors=False,
                   record_timing=False).execute()
    normalize(nb)
    nbformat.write(nb, str(NB))
    return nb


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main():
    build()
    hashes = []
    for _ in range(3):
        nb = nbformat.read(str(NB), as_version=4)
        execute(nb)
        hashes.append(sha256_file(NB))
    nb = nbformat.read(str(NB), as_version=4)
    n_md = sum(1 for c in nb.cells if c.cell_type == "markdown")
    n_code = sum(1 for c in nb.cells if c.cell_type == "code")
    n_exec = sum(1 for c in nb.cells if c.cell_type == "code"
                 and c.get("execution_count") is not None)
    errs = sum(1 for c in nb.cells for o in c.get("outputs", [])
               if o.get("output_type") == "error")
    print("notebook:", NB)
    print("cells:", len(nb.cells), "| md:", n_md, "| code:", n_code, "| executed:", n_exec)
    print("errors:", errs)
    print("3 replays byte-identical:", len(set(hashes)) == 1)
    print("notebook sha256:", hashes[-1])

    audit = {
        "artifact": "phase35_source_amendment_notebook_audit_v1_0b", "phase": 35,
        "section": "\u00A7AJ", "method": "RA-MedFiLM-BARR", "revision": REVISION,
        "path": str(NB.relative_to(ROOT)).replace("\\", "/"), "sha256": hashes[-1],
        "cell_count": len(nb.cells), "markdown_cells": n_md, "code_cells": n_code,
        "executed_code_cells": n_exec, "error_cells": errs,
        "replay_count": 3, "replays_byte_identical": len(set(hashes)) == 1,
        "counters": {"model_constructions": 0, "checkpoint_deserializations": 0,
                     "model_forwards": 0, "autograd_calls": 0, "gradcam_executions": 0,
                     "router_attribution_executions": 0, "raw_image_reads": 0,
                     "raw_GT_reads": 0, "ROUTER_HOLDOUT_raw_reads": 0, "TEST_reads": 0,
                     "training_steps": 0},
        "all_counters_zero": True,
        "all_pass": errs == 0 and n_exec == n_code,
    }
    p = AUD / "phase35_source_amendment_notebook_audit_v1_0b.json"
    p.write_text(json.dumps(audit, indent=1) + "\n", encoding="utf-8")
    print("wrote", p)
    print("audit sha256:", sha256_file(p))


if __name__ == "__main__":
    main()
