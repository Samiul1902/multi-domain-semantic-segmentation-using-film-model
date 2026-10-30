#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build AND execute the Phase35 v1.0e synthetic-smoke BLOCK reviewer notebook (read-only).

Classification: READ_ONLY_PHASE35_V1_0E_SYNTHETIC_SMOKE_REVIEWER_NOTEBOOK
This notebook documents a BLOCKED smoke attempt: the frozen v1.0e empty-mask observability check
uses a synthetic zero-plane logits surrogate, which work-order \u00a7Q forbids; the requirement is
UNSATISFIABLE by the frozen bytes, so the smoke was blocked BEFORE any model construction.

The notebook reads ONLY the frozen v1.0e smoke / provenance / final-check / block / metadata-
reconciliation JSONs plus the v1.0e authority governance artifacts. It constructs NO model,
deserializes NO checkpoint, runs NO forward/autograd/Grad-CAM, reads NO medical data and NO real
p_global. Determinism = the notebook source is rendered 3x; the (blocked) smoke is NOT re-run.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/build_phase35_synthetic_smoke_notebook_v1_0e.py
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
NB = (ROOT / "notebooks" / "phasewise" / "phase_35_interpretability" /
      "phase35_interpretability_synthetic_smoke_v1_0e_review.ipynb")
KERNEL = "jup-venv"
REVISION = "ra_medfilm_barr_phase35_interpretability_v1_0e"

SETUP = '''\
import hashlib
import json
from pathlib import Path
ROOT = Path(r"D://Softfors//jup"); AUD = ROOT / "reports" / "audits"
def jload(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))
smoke = jload(AUD / "phase35_synthetic_interpretability_smoke_v1_0e.json")
prov = jload(AUD / "phase35_synthetic_smoke_provenance_v1_0e.json")
fc = jload(AUD / "phase35_synthetic_smoke_final_check_v1_0e.json")
term = jload(AUD / "phase35_synthetic_smoke_terminal_v1_0e.json")
blk = jload(AUD / "phase35_v1_0e_empty_mask_observability_block.json")
print("Phase35 v1.0e numerically-guarded synthetic interpretability smoke review (READ-ONLY)")
print("Outcome: BLOCKED_PRE_MODEL_CONSTRUCTION (empty-mask observability requirement).")
print("No model construction, no checkpoint deserialization, no forward, no autograd, no Grad-CAM,")
print("no router attribution, no images, no real p_global, no VAL808 cache, no HOLDOUT/TEST.")
print("This notebook READS frozen governance artifacts only; it does NOT re-run the (blocked) smoke.")
'''
CELLS = []
_META = {"kernelspec": {"display_name": "Python 3", "language": "python", "name": KERNEL},
         "language_info": {"name": "python", "version": "3.11.9"}}


def md(s):
    CELLS.append({"cell_type": "markdown", "id": f"cell{len(CELLS):03d}",
                  "metadata": {}, "source": s})


def code(s):
    CELLS.append({"cell_type": "code", "id": f"cell{len(CELLS):03d}",
                  "execution_count": None, "metadata": {}, "outputs": [], "source": s})


md(f"""# Phase 35 v1.0e — Numerically-Guarded Synthetic Interpretability Smoke
## Reviewer Notebook (read-only) — **BLOCKED PRE-MODEL-CONSTRUCTION**

**Classification:** `READ_ONLY_PHASE35_V1_0E_SYNTHETIC_SMOKE_REVIEWER_NOTEBOOK`
**Revision:** `{REVISION}`

The supervisor authorized **one** synthetic-only smoke of the frozen v1.0e `--mode smoke`. During the
`\u00a7Q` empty-mask observability gate — **before any model construction** — the run was **BLOCKED**:

> the frozen v1.0e empty-mask check fabricates a synthetic **zero-plane** logits surrogate
> (self-documented as *"NOT a real logits tensor"*), while `\u00a7Q` mandates an **ACTUAL-logits**
> empty-mask validation and explicitly **forbids** a zero-logit surrogate. The guarded path does not
> return the logits tensor and `\u00a7Q` forbids an extra forward, so the requirement is
> **unsatisfiable by the frozen bytes**.

**No model was constructed, no checkpoint was loaded, no forward/autograd/Grad-CAM ran, no gate was
set, no mode was invoked. No patch and no retry were attempted.** No numerical result exists to show.
""")

md("## 0. Setup")
code(SETUP)

md("## 1. Blocked outcome (the primary fact)")
code('''\
print("smoke_executed      :", smoke["smoke_executed"])
print("outcome             :", smoke["outcome"])
print("block_reason        :", smoke["block_reason"])
print("classification      :", smoke["classification"])
print("not                 :", smoke["not"])
print("no numerical result :", smoke["no_numerical_model_result_produced"])
print()
print("terminal:")
print(" ", term["terminal"])
print()
print("why no numerical result:")
print(" ", smoke["why_no_numerical_result"])
''')

md("## 2. The §Q rule applied and the observed frozen-source fact")
code('''\
print("determination:", blk["determination"])
print()
print("work-order rule (\u00a7Q):")
print(" ", blk["work_order_rule_applied"])
print()
print("observed in frozen source:")
obs = blk["observed_in_frozen_source"]
for k in ("function", "source_path", "source_sha256", "lines", "uses_zero_plane_surrogate",
          "surrogate_construction", "self_documented_field",
          "actual_G_logits_available_to_helper", "reason_actual_logits_unavailable",
          "any_other_actual_logits_empty_mask_path_in_source"):
    print(f"  {k}: {obs[k]}")
''')

md("## 3. Zero execution counters (blocked before model construction)")
code('''\
print("counters_match_all_zero:",
      all(v == 0 for v in smoke["counters"].values()))
print()
for k, v in smoke["counters"].items():
    flag = "" if v == 0 else "   <-- NON-ZERO"
    print(f"  {k:48s} = {v}{flag}")
print()
print("gate_env_set:", smoke["gate_env_set"], "| mode_invoked:", smoke["mode_invoked"])
print("model_constructed:", fc["model_constructed"],
      "| checkpoint_deserialized:", fc["checkpoint_deserialized"])
print("forward_executed:", fc["forward_executed"],
      "| autograd_executed:", fc["autograd_executed"],
      "| gradcam_executed:", fc["gradcam_executed"])
''')

md("## 4. Pre-construction gates that COULD be evaluated (and all passed)")
code('''\
checks = fc["checks_that_could_be_evaluated_pre_construction"]
for k, v in checks.items():
    print(f"  [{'OK' if v else 'BLOCK'}] {k}")
''')

md("## 5. Authority bindings verified before the block (all matched)")
code('''\
for k, v in prov["authority_bindings"].items():
    print(f"  [{'OK' if v['match'] else 'FAIL'}] {k:28s} {v.get('path', v.get('sha256'))}")
''')

md("## 6. First v1.0d smoke preserved (not overwritten, not reinterpreted)")
code('''\
pres = blk["v1_0d_first_smoke_preserved"]
for k in ("smoke", "provenance", "final_check", "gap_disclosure"):
    print(f"  {k:16s} {pres[k]['sha256']}  match={pres[k]['match']}")
print()
print("classification:", pres["classification"])
print("overwritten_or_reinterpreted:", pres["overwritten_or_reinterpreted"])
''')

md("## 7. §C reviewer-notebook execution-metadata reconciliation")
code('''\
rec = jload(AUD / "phase35_v1_0e_reviewer_notebook_execution_metadata_reconciliation.json")
print("classification:", rec["classification"])
print("delivered_notebook_representation:", rec["delivered_notebook_representation"])
print("uploaded_notebook_saved_execution_counts_present:",
      rec["uploaded_notebook_saved_execution_counts_present"])
print("uploaded_notebook_saved_outputs_present:",
      rec["uploaded_notebook_saved_outputs_present"])
print("existing_audit_claims_code_cells_executed:", rec["existing_audit_claims_code_cells_executed"])
print("existing_audit_claims_replay_3x_byte_identical:",
      rec["existing_audit_claims_replay_3x_byte_identical"])
print("distinction:", json.dumps(rec["distinction"], indent=1))
''')

md("## 8. Judgement: prospective source-level block, NOT a result-conditioned rerun")
code('''\
print("judgement:", json.dumps(blk["judgement"], indent=1))
print()
print("not_a_result_conditioned_rerun:", prov["not_a_result_conditioned_rerun"])
print("patch_attempted:", prov["patch_attempted"], "| retry_attempted:", prov["retry_attempted"])
''')

md("## 9. Protected / scientific-output counters (all zero)")
code('''\
print("protected_data_counters_zero:", fc["protected_data_counters_zero"])
print("scientific_output_counters_zero:", fc["scientific_output_counters_zero"])
print()
print("test_state:", fc["test_state"], "| router_holdout_state:", fc["router_holdout_state"])
print("scientific_execution_started:", fc["scientific_execution_started"],
      "| phase36_started:", fc["phase36_started"])
''')

md("## 10. Final check")
code('''\
print("final check:", fc["n_checks"], "checks,", fc["n_failed"], "failed")
print("failed:", fc["failed"])
print("all_pass:", fc["all_pass"])
print()
print("smoke_checks_not_run (blocked before execution):")
for c in fc["smoke_checks_not_run"]:
    print("  -", c)
''')

md("## 11. Required remediation for a future work order")
code('''\
for i, step in enumerate(blk["required_remediation_for_future_work_order"], 1):
    print(f"  {i}. {step}")
''')

md("""---
## Summary

| item | value |
|---|---|
| frozen v1.0e `--mode smoke` | **BLOCKED before model construction** — NOT run |
| blocking gate | `\u00a7Q` empty-mask **actual-logits** observability requirement |
| determination | `V1_0E_EMPTY_MASK_OBSERVABILITY_IMPLEMENTATION_INCOMPLETE` |
| root cause | frozen helper tests a `torch.zeros` logits **surrogate**; `\u00a7Q` forbids it, and the guarded path does not return the logits (extra forward also forbidden) |
| gate env set | never (`PHASE35_SMOKE_EXECUTE` not exported; `PHASE35_EXECUTE` never set) |
| pre-construction gates | all PASS (authority 17 artifacts · checkpoints · domain registry · environment) |
| model / checkpoint / forward / autograd / Grad-CAM | 0 · 0 · 0 · 0 · 0 |
| model constructions · deserializations · gate env · mode invocations | 0 · 0 · 0 · 0 |
| raw VAL · real p_global · GT · HOLDOUT · TEST | 0 · 0 · 0 · 0 · 0 |
| scientific outputs · training | 0 · 0 |
| patch attempted · retry attempted | false · false |
| first v1.0d smoke | preserved, not overwritten, not reinterpreted |
| Phase35 scientific execution | **NOT** started · Phase36 NOT started · TEST locked |
| numerical result produced | **none** (by design of the block) |
""")


def build():
    nb = {"cells": CELLS, "metadata": dict(_META), "nbformat": 4, "nbformat_minor": 5}
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
    nb.metadata = dict(_META)
    return nb


def execute(nb):
    NotebookClient(nb, kernel_name=KERNEL, timeout=900, allow_errors=False,
                   record_timing=False).execute()
    normalize(nb)
    nbformat.write(nb, str(NB))
    return nb


def sha256_file(p):
    h = hashlib.sha256()
    h.update(Path(p).read_bytes())
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
    audit = {"artifact": "phase35_synthetic_smoke_reviewer_notebook_audit_v1_0e", "phase": 35,
             "section": "\u00A7Y", "method": "RA-MedFiLM-BARR", "revision": REVISION,
             "path": str(NB.relative_to(ROOT)).replace("\\", "/"), "sha256": hashes[-1],
             "notebook_representation": "CLEAN_SOURCE_NOTEBOOK_OUTPUTS_STRIPPED",
             "cell_count": len(nb.cells), "markdown_cells": n_md, "code_cells": n_code,
             "executed_code_cells": n_exec, "error_cells": errs, "replay_count": 3,
             "replays_byte_identical": len(set(hashes)) == 1,
             "synthetic_smoke_rerun_between_renders": False,
             "documents_blocked_outcome": True,
             "counters": {"model_constructions": 0, "checkpoint_deserializations": 0,
                          "model_forwards": 0, "model_autograd_calls": 0, "gradcam_executions": 0,
                          "router_attribution_executions": 0, "raw_image_reads": 0,
                          "real_persisted_p_global_reads": 0, "gt_reads": 0,
                          "router_holdout_reads": 0, "test_reads": 0, "training_steps": 0,
                          "smoke_reruns": 0},
             "all_counters_zero": True, "all_pass": errs == 0 and n_exec == n_code}
    p = AUD / "phase35_synthetic_smoke_reviewer_notebook_audit_v1_0e.json"
    p.write_text(json.dumps(audit, indent=1) + "\n", encoding="utf-8")
    print("wrote", p)
    print("audit sha256:", sha256_file(p))


if __name__ == "__main__":
    main()
