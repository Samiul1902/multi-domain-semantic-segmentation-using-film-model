#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build AND execute the Phase35 pre-execution interpretability SPEC reviewer notebook.

Classification: READ_ONLY_PHASE35_PRE_EXECUTION_INTERPRETABILITY_SPEC_REVIEWER_NOTEBOOK

Renders Phase35 specification artifacts ONLY. Never loads models, reads raw images, runs forwards
or backwards, runs Grad-CAM/router attribution, opens protected data/TEST or trains.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/build_phase35_spec_reviewer_notebook_v1_0.py
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(r"D:\Softfors\jup")
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
NB = (ROOT / "notebooks" / "phasewise" / "phase_35_interpretability" /
      "phase35_interpretability_spec_v1_0_review.ipynb")
KERNEL = "jup-venv"
REVISION = "ra_medfilm_barr_phase35_interpretability_v1_0"

SETUP = '''\
import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(r"D:\\Softfors\\jup")
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"


def jload(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def tshow(name, n=None):
    df = pd.read_csv(TAB / name)
    print(name, "| shape:", df.shape)
    if n is not None:
        df = df.head(n)
    with pd.option_context("display.max_columns", None, "display.width", 260):
        print(df.to_string(index=False))
    return df


print("Phase35 pre-execution feature-attribution / visual-interpretability SPEC review")
print("READ-ONLY. No model load, no raw image read, no forward, no backward, no Grad-CAM,")
print("no router attribution, no protected data, no TEST, no training.")
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


md(f"""# Phase 35 — Feature Attribution & Visual Interpretability
## Pre-Execution Specification Reviewer Notebook

**Classification:** `READ_ONLY_PHASE35_PRE_EXECUTION_INTERPRETABILITY_SPEC_REVIEWER_NOTEBOOK`
**Revision:** `{REVISION}`

Four evidence families frozen: **I1** FiLM parameter interpretability · **I2** segmentation
gradient saliency · **I3** ROI/proposal + regional behaviour visualization · **I4** benefit-router
feature attribution. No Phase35 execution has occurred.
""")

md("## 0. Setup")
code(SETUP)

md("## 1. Phase34 canonical handoff")
code('''\
h = jload(AUD / "phase34_phase35_handoff.json")
print("Phase34 status:", h["Phase34_status"])
print("Phase35 eligibility:", h["Phase35_eligibility"], "| started:", h["Phase35_started"])
print("Phase35:", h["Phase35_phase_id"], "|", h["Phase35_title"])
print("TEST:", h["TEST"], "| ROUTER_HOLDOUT:", h["ROUTER_HOLDOUT"])
''')

md("## 2. Roadmap identity")
code('''\
ri = jload(AUD / "phase35_roadmap_identity_reconciliation.json")
print("phase id:", ri["phase_id"])
print("canonical title:", ri["canonical_title"])
print("historical README alias:", ri["historical_readme_alias"],
      "| still present:", ri["historical_readme_alias_still_present"])
print("scientific scope:", ri["scientific_scope_wording"])
print("identity conflict:", ri["identity_conflict"])
print()
for s in ri["sources_inspected"]:
    print(f"  {s['source']:52s} exists={s['exists']}")
''')

md("## 3. Predecessor interpretability inventory")
code('''\
inv = tshow("phase35_predecessor_interpretability_inventory.csv")
print()
print("reuse eligibility values:", sorted(set(inv["phase35_reuse_eligibility"])))
''')

md("## 4. Gallery population ownership")
code('''\
own = jload(AUD / "phase35_gallery_population_ownership.json")
print("gallery:", own["gallery_path"])
print("n:", own["n"], "| unique:", own["unique_sample_id"], "| per domain:", own["per_domain"])
print("all belong to VAL808:", own["all_belong_to_VAL808"])
print("ROUTER_HOLDOUT overlap:", own["router_holdout_overlap"])
print("TEST overlap:", own["test_overlap"])
print("selection rule:", own["selection_rule"], "| prediction-dependent:", own["prediction_dependent"])
print()
print("display subset rule:", own["display_subset_rule"])
print("display subset n:", own["display_subset_n"],
      "| created at spec time:", own["display_subset_created_at_spec_time"])
''')

md("## 5. Canonical model binding")
code('''\
mb = jload(AUD / "phase35_canonical_model_binding.json")
for cid, c in mb["components"].items():
    print(f"  {cid:8s} {c['class']:24s} params={c['parameter_count']:>9,} role={c['role']}")
    print(f"           ckpt {c['checkpoint_path']}")
    print(f"           sha  {c['checkpoint_sha256_observed'][:32]}...")
print()
print("checkpoint deserialized during specification:",
      mb["checkpoint_deserialized"])
''')

md("## 6. Grad-CAM layer / target / algorithm contract")
code('''\
gl = jload(AUD / "phase35_gradcam_layer_contract.json")
print("family:", gl["family"], "| is attention model:", gl["global_medfilm_is_attention_model"])
for name, L in gl["layers"].items():
    print(f"  {name:20s} module={L['exact_module_path']:28s} shape={L['output_shape_expected']}")
print()
print("target:", json.dumps(gl["target"], indent=2))
print()
print("algorithm:", json.dumps(gl["algorithm"], indent=2))
print()
print("execution semantics:", json.dumps(gl["execution_semantics"], indent=2))
''')

md("## 7. ROI proposal contract")
code('''\
rp = jload(AUD / "phase35_roi_proposal_visualization_contract.json")
print("t_roi proposal:", rp["roi_proposal_threshold"])
print("t_seg output  :", rp["segmentation_threshold"])
print("panel elements:", rp["panel_elements"])
print("ground truth required:", rp["ground_truth_required"])
''')

md("## 8. Router population and attribution contract")
code('''\
rc = jload(AUD / "phase35_router_population_contract.json")
print("population:", rc["population"], "| n:", rc["n"])
print("holdout rows:", rc["router_holdout_rows"], "| TEST rows:", rc["test_rows"])
print("raw image reads for router attribution:", rc["raw_image_reads_for_router_attribution"])
print()
print("feature groups:", rc["feature_groups"])
print("scalar features:", rc["scalar_features"])
print()
print("attribution:", json.dumps(rc["attribution"], indent=2))
print("task-id policy:", json.dumps(rc["task_id_policy"], indent=2))
''')

md("## 9. Figure contract")
code('''\
fg = jload(AUD / "phase35_figure_contract.json")
for k, v in fg["figures"].items():
    print(f"  {k}: {v}")
print()
print("optional:", fg["optional_figures"])
print("outcome-selected galleries forbidden:",
      fg["outcome_selected_best_looking_gradcam_galleries"])
''')

md("## 10. Source freeze and execution eligibility")
code('''\
sf = jload(AUD / "phase35_preexecution_source_freeze_v1_0.json")
for k, v in sf["frozen_sources"].items():
    print(f"  {(v['sha256'] or 'MISSING')[:16]}...  {k:26s} {v['path']}")
print()
el = jload(AUD / "phase35_execution_eligibility_adjudication_v1_0.json")
for k, v in el["families"].items():
    print(f"  {k:52s} = {str(v['value']):5s}")
''')

md("## 11. Entry gate, final check and zero-execution counters")
code('''\
eg = jload(AUD / "phase35_entry_gate_v1_0.json")
print("entry gate:", eg["n_checks"], "checks,", eg["n_failed"], "failed")
fc = jload(AUD / "phase35_specification_final_check_v1_0.json")
print("final check:", fc["n_checks"], "checks,", fc["n_failed"], "failed")
print("completeness:", fc["completeness"])
print()
ne = jload(AUD / "phase35_no_execution_audit_v1_0.json")
for k, v in ne["counters"].items():
    print(f"  {k:34s} = {v}")
print("all zero:", ne["all_zero"])
assert ne["all_zero"]
print()
term = jload(AUD / "phase35_specification_terminal_v1_0.json")
print("terminal:")
print(" ", term["terminal"])
''')

md("""---
## Summary

| item | value |
|---|---|
| Phase34 | `COMPLETE_CANONICAL`, handoff bound |
| Phase35 | `phase_35_interpretability` — Feature Attribution & Visual Interpretability |
| evidence families | I1 FiLM · I2 Grad-CAM · I3 ROI/regional · I4 router attribution |
| visual cohort | 64-case frozen VAL gallery (16/domain), 0 holdout, 0 TEST |
| display subset | 16 (lowest frozen rank per domain), rule frozen |
| Grad-CAM layers | `film_layers["bridge"]` `[1,256,32,32]` · `film_layers["decoder1"]` `[1,24,512,512]` |
| router population | VAL808 non-holdout, 202-D (192 deep + 10 scalars) |
| router method | Gradient × Input on raw `delta_hat` |
| thresholds | proposal 0.30 · segmentation output 0.50 |
| model loads · forwards · backward · Grad-CAM · attribution | 0 · 0 · 0 · 0 · 0 |
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
        "artifact": "phase35_spec_reviewer_notebook_audit_v1_0", "phase": 35,
        "section": "\u00A7AD", "method": "RA-MedFiLM-BARR", "revision": REVISION,
        "path": str(NB.relative_to(ROOT)).replace("\\", "/"), "sha256": hashes[-1],
        "cell_count": len(nb.cells), "markdown_cells": n_md, "code_cells": n_code,
        "executed_code_cells": n_exec, "error_cells": errs,
        "replay_count": 3, "replays_byte_identical": len(set(hashes)) == 1,
        "counters": {"model_loads": 0, "model_constructions": 0, "forwards": 0,
                     "backward_calls": 0, "gradcam_executions": 0,
                     "router_attribution_executions": 0, "raw_image_reads": 0,
                     "raw_GT_reads": 0, "ROUTER_HOLDOUT_raw_reads": 0, "TEST_reads": 0,
                     "training_steps": 0},
        "all_counters_zero": True,
        "all_pass": errs == 0 and n_exec == n_code,
    }
    p = AUD / "phase35_spec_reviewer_notebook_audit_v1_0.json"
    p.write_text(json.dumps(audit, indent=1) + "\n", encoding="utf-8")
    print("wrote", p)
    print("audit sha256:", sha256_file(p))


if __name__ == "__main__":
    main()
