#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build AND execute the Phase35 v1.0d synthetic-smoke reviewer notebook (read-only).

Classification: READ_ONLY_PHASE35_V1_0D_SYNTHETIC_SMOKE_REVIEWER_NOTEBOOK
Reads only the produced smoke / provenance / final-check / environment / reporting-gap JSONs and
predecessor governance artifacts. Constructs no model, deserializes no checkpoint, runs no forward
or autograd, reads no medical data and no real p_global. Determinism = the notebook is rendered 3x;
the synthetic smoke is NOT re-run.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/build_phase35_synthetic_smoke_notebook_v1_0d.py
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
      "phase35_interpretability_synthetic_smoke_v1_0d_review.ipynb")
KERNEL = "jup-venv"
REVISION = "ra_medfilm_barr_phase35_interpretability_v1_0d"

SETUP = '''\
import hashlib
import json
from pathlib import Path
ROOT = Path(r"D://Softfors//jup"); AUD = ROOT / "reports" / "audits"
def jload(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))
smoke = jload(AUD / "phase35_synthetic_interpretability_smoke_v1_0d.json")
r = smoke["frozen_smoke_report"]
print("Phase35 v1.0d rank-safe synthetic interpretability smoke review (READ-ONLY)")
print("No model construction, no checkpoint deserialization, no forward, no autograd, no Grad-CAM,")
print("no router attribution, no images, no real p_global, no VAL808 cache, no HOLDOUT/TEST.")
print("The synthetic smoke was executed exactly ONCE and is NOT re-run by this notebook.")
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


md(f"""# Phase 35 v1.0d — Rank-Safe Synthetic Interpretability Smoke
## Reviewer Notebook (read-only)

**Classification:** `READ_ONLY_PHASE35_V1_0D_SYNTHETIC_SMOKE_REVIEWER_NOTEBOOK`
**Revision:** `{REVISION}`

The first authorized model execution in Phase 35: the frozen v1.0d `--mode smoke`, which now
validates the **real** rank contract (rank-4 logits + rank-2 mask) through the **same** repaired
target helper used by scientific Grad-CAM. **No scientific output exists and none is produced here.**
""")
md("## 0. Setup")
code(SETUP)

md("## 1. Authority, source and invocation gates")
code('''\
print("outcome:", smoke["outcome"], "| classification:", smoke["classification"])
print("not:", smoke["not"])
print()
print("authority gates:")
for k, v in smoke["authority_gates"].items():
    print(f"  [{'OK' if v['match'] else 'FAIL'}] {k}")
print()
print("frozen source bytes:")
for k, v in smoke["frozen_source_bytes"].items():
    print(f"  [{'OK' if v['match'] else 'FAIL'}] {k}")
print()
print("invocation:", json.dumps(smoke["invocation"], indent=1))
''')

md("## 2. Environment gate")
code('''\
e = smoke["environment"]
for k in ("gpu", "compute_capability", "vram_bytes", "python", "torch", "cuda_runtime",
          "cudnn", "driver_version", "matches_expected"):
    print(f"  {k:20s} = {e[k]}")
''')

md("## 3. Checkpoint identity (hashed BEFORE deserialization)")
code('''\
for cid, c in smoke["checkpoint_identities"].items():
    print(f"  {cid:6s} match={c['match']} deserialized_yet={c['deserialized_yet']} {c['path']}")
''')

md("## 4. Exact execution counters")
code('''\
print("counts_match_expected:", r["counts_match_expected"], "| smoke all_pass:", r["all_pass"])
print()
for k, v in r["counters"].items():
    exp = r["expected_counters"].get(k)
    flag = "" if exp is None or exp == v else f"   <-- expected {exp}"
    print(f"  {k:42s} = {v}{flag}")
''')

md("## 5. Canonical G / B_phi strict load")
code('''\
print("G     :", json.dumps(r["G_identity"]))
print("B_phi :", json.dumps(r["B_phi_identity"]))
print()
print("G parameter count 3,523,001:", r["G_identity"]["parameter_count"] == 3523001)
print("B_phi parameter count 36,801:", r["B_phi_identity"]["parameter_count"] == 36801)
print("B_phi task embedding [4,16]:", r["B_phi_identity"]["task_embedding_shape"] == [4, 16])
print("R_psi construction/load/forward:",
      [r["counters"]["R_psi_model_constructions"], r["counters"]["R_psi_checkpoint_loads"],
       r["counters"]["R_psi_forwards"]])
print("S_omega construction/load/forward:",
      [r["counters"]["S_omega_model_constructions"], r["counters"]["S_omega_checkpoint_loads"],
       r["counters"]["S_omega_forwards"]])
''')

md("## 6. FiLM accessor and task embeddings")
code('''\
fs = r["film_smoke"]
print("FiLM all_pass:", fs["all_pass"], "| task/site entries:", len(fs["per_task_site"]))
for k, v in fs["per_task_site"].items():
    print(f"  {k:20s} gamma={v['gamma_len']:4d} beta={v['beta_len']:4d} "
          f"expected={v['expected_channels']:4d} finite={v['finite']} exact={v['channel_count_exact']}")
print("scientific FiLM table emitted:", fs["scientific_film_tables_emitted"])
print()
print("embeddings:", json.dumps(r["embedding_smoke"], indent=1))
''')

md("## 7. Rank-safe target contract (rank-4 logits + rank-2 mask, same scientific helper)")
code('''\
g = r["gradcam_smoke"]
print("target helper:", g["target_scalar_impl"])
print("smoke mask shape/rank:", g["target_mask_shape"], g["target_mask_rank"])
print("geometry:", g["target_mask_geometry"])
print("rank-4 workaround used:", g["rank4_workaround_used"])
print("scientific target selection used:", g["scientific_target_selection_used"])
print()
print("mask rank contract:", json.dumps(g["mask_rank_contract"], indent=1))
print()
print("activation shapes:", json.dumps(g["activation_shapes"]))
print("scalar target evaluations:", g["scalar_target_evaluations"],
      "| autograd calls:", g["autograd_calls"])
''')

md("## 8. Synthetic CAMs")
code('''\
for name, c in g["cams"].items():
    print(f"  {name:9s} shape={c['shape']} dtype={c['dtype']} finite={c['finite']} "
          f"min={c['min']} max={c['max']}")
print()
gap = jload(AUD / "phase35_synthetic_smoke_reporting_gap_disclosure_v1_0d.json")
print("all CAMs all-zero:", gap["observed_cam_degeneracy"]["all_cams_all_zero"])
print("interpretation:", gap["observed_cam_degeneracy"]["interpretation"])
''')

md("## 9. Router preprocessing, raw delta_hat and Gradient x Input")
code('''\
rt = r["router_smoke"]
for k in ("raw_router_input_shape", "raw_router_input_dtype", "raw_router_input_finite",
          "normalized_router_input_shape", "normalized_router_input_dtype",
          "normalized_router_input_finite", "raw_delta_hat_shape", "raw_delta_hat_finite",
          "sigmoid_applied", "sigmoid_count", "router_gradient_shape", "router_gradient_finite",
          "gradient_x_input_shape", "gradient_x_input_finite", "task_id_dtype",
          "task_id_requires_grad", "task_id_numeric_attribution"):
    print(f"  {k:34s} = {rt[k]}")
''')

md("## 10. Zero-denominator policy")
code('''\
print(json.dumps(r["zero_denominator_policy"], indent=1))
''')

md("## 11. Model state / gradient immutability")
code('''\
pi = r["parameter_immutability"]
for k in ("G_state_tensors_unchanged", "B_phi_state_tensors_unchanged", "parameter_mutations",
          "MODEL_PARAMETERS_UNCHANGED"):
    print(f"  {k:32s} = {pi[k]}")
print("  G     state identity before/after:", pi["G_identity_before"][:16], pi["G_identity_after"][:16])
print("  B_phi state identity before/after:",
      pi["B_phi_identity_before"][:16], pi["B_phi_identity_after"][:16])
print()
print("grad mechanism demonstration:", json.dumps(smoke["grad_mechanism_demonstration"], indent=1))
''')

md("## 12. Protected / real-data counters")
code('''\
for k, v in smoke["protected_data_counters"].items():
    print(f"  {k:42s} = {v}")
''')

md("## 13. Disclosed reporting gaps (adjudicated, not patched)")
code('''\
for gid, gv in gap["gaps"].items():
    print(f"--- {gid} ---")
    for k, v in gv.items():
        print(f"    {k}: {v}")
    print()
print("recommended follow-up:", json.dumps(gap["recommended_follow_up"], indent=1))
''')

md("## 14. Final check and terminal")
code('''\
fc = jload(AUD / "phase35_synthetic_smoke_final_check_v1_0d.json")
print("final check:", fc["n_checks"], "checks,", fc["n_failed"], "failed")
print()
print("terminal:"); print(" ", fc["terminal"])
print()
print("phase35_scientific_execution_started:", fc["phase35_scientific_execution_started"])
print("phase36_started:", fc["phase36_started"], "| TEST:", fc["TEST"])
''')

md("""---
## Summary

| item | value |
|---|---|
| frozen v1.0d `--mode smoke` | executed **once**; returncode 0 |
| gate env | `PHASE35_SMOKE_EXECUTE=1` only (`PHASE35_EXECUTE` never set) |
| authority / source gates | 6/6 · 7/7 |
| environment | RTX 3060 Ti · cc 8.6 · 8,589,279,232 B · torch 2.6.0+cu124 · cuDNN 90100 |
| G / B_phi strict load | PASS · 0 missing / 0 unexpected |
| parameters | G 3,523,001 · B_phi 36,801 · float32 · eval |
| FiLM 4×5 / embeddings | PASS · G `[4,32]` · B_phi `[4,16]` |
| rank contract | logits `[1,1,512,512]` + mask rank-2 `[512,512]` bool, **same scientific helper** |
| Grad-CAM | 1 forward · 1 autograd · 2 CAMs `[512,512]` float32 finite (all-zero content — disclosed) |
| router | raw `delta_hat` `[4]` · sigmoid 0 · gradient `[4,202]` · Gradient×Input `[4,202]` |
| zero-denominator policy | denominator 0 · NULL shares · flag true · no epsilon/renormalization |
| model parameters | **UNCHANGED** (state identity before == after) |
| raw VAL · real p_global · GT · VAL808 cache · HOLDOUT · TEST | 0 · 0 · 0 · 0 · 0 · 0 |
| scientific outputs · training | 0 · 0 |
| disclosed gaps | empty-mask counter, parameter-grad counts, gradient finiteness (adjudicated) |
| Phase35 scientific execution | NOT started · Phase36 NOT started · TEST locked |
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
    audit = {"artifact": "phase35_synthetic_smoke_reviewer_notebook_audit_v1_0d", "phase": 35,
             "section": "\u00A7X", "method": "RA-MedFiLM-BARR", "revision": REVISION,
             "path": str(NB.relative_to(ROOT)).replace("\\", "/"), "sha256": hashes[-1],
             "cell_count": len(nb.cells), "markdown_cells": n_md, "code_cells": n_code,
             "executed_code_cells": n_exec, "error_cells": errs, "replay_count": 3,
             "replays_byte_identical": len(set(hashes)) == 1,
             "synthetic_smoke_rerun_between_renders": False,
             "counters": {"model_constructions": 0, "checkpoint_deserializations": 0,
                          "model_forwards": 0, "model_autograd_calls": 0, "gradcam_executions": 0,
                          "router_attribution_executions": 0, "raw_image_reads": 0,
                          "real_persisted_p_global_reads": 0, "gt_reads": 0,
                          "router_holdout_reads": 0, "test_reads": 0, "training_steps": 0,
                          "smoke_reruns": 0},
             "all_counters_zero": True, "all_pass": errs == 0 and n_exec == n_code}
    p = AUD / "phase35_synthetic_smoke_reviewer_notebook_audit_v1_0d.json"
    p.write_text(json.dumps(audit, indent=1) + "\n", encoding="utf-8")
    print("wrote", p)
    print("audit sha256:", sha256_file(p))


if __name__ == "__main__":
    main()
