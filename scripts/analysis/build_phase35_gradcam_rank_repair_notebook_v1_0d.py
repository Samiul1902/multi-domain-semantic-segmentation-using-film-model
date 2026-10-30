#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build AND execute the Phase35 v1.0d Grad-CAM rank-repair reviewer notebook (read-only).

Classification: READ_ONLY_PHASE35_V1_0D_GRADCAM_RANK_REPAIR_REVIEWER_NOTEBOOK
Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/build_phase35_gradcam_rank_repair_notebook_v1_0d.py
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
      "phase35_gradcam_rank_repair_v1_0d_review.ipynb")
KERNEL = "jup-venv"
REVISION = "ra_medfilm_barr_phase35_interpretability_v1_0d"

SETUP = '''\
import hashlib
import json
from pathlib import Path
ROOT = Path(r"D://Softfors//jup"); AUD = ROOT / "reports" / "audits"
def jload(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))
print("Phase35 v1.0d Grad-CAM target-mask rank-safety amendment review (READ-ONLY)")
print("No model construction, no checkpoint deserialization, no forward, no model autograd,")
print("no Grad-CAM execution, no router attribution, no images, no real p_global, no gate set.")
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


md(f"""# Phase 35 v1.0d — Grad-CAM Target-Mask Rank-Safety Amendment
## Reviewer Notebook (read-only)

**Classification:** `READ_ONLY_PHASE35_V1_0D_GRADCAM_RANK_REPAIR_REVIEWER_NOTEBOOK`
**Revision:** `{REVISION}`

Repairs the prospectively disclosed defect
`PHASE35_V1_0B_GRADCAM_TARGET_MASK_RANK_INCOMPATIBILITY` **before** the synthetic smoke re-run and
**before** any Phase35 scientific execution. Implementation-only amendment: no scientific protocol
change. **No scientific output exists and none is produced here.**
""")
md("## 0. Setup")
code(SETUP)

md("## 1. Defect B — what was wrong")
code('''\
d = jload(AUD / "phase35_gradcam_target_rank_defect_v1_0d.json")
print("defect id   :", d["defect_id"])
print("classification:", d["classification"])
print("frozen defective component:", d["frozen_defective_component"])
print()
for k, v in d["known_scientific_tensors"].items():
    print(f"  {k:34s} {v}")
print()
print("problem:", d["problem"])
print()
print("flags:")
for k in ("scientific_specification_changed", "scientific_population_changed",
          "target_threshold_changed", "target_selection_source_changed",
          "causal_or_scientific_interpretation_changed", "implementation_rank_contract_changed",
          "scientific_result_invalidated", "frozen_v1_0b_modified", "frozen_v1_0c_modified"):
    print(f"  {k:46s} = {d[k]}")
''')

md("## 2. Frozen specification target intent (unchanged)")
code('''\
for k, v in d["frozen_scientific_intent"].items():
    print(f"  {k:22s} : {v}")
print()
print("evidence:")
for e in d["evidence"]:
    print("  -", e)
''')

md("## 3. Rank-mismatch proof")
code('''\
import torch
logits = torch.arange(16, dtype=torch.float32).reshape(1, 1, 4, 4)
m2 = torch.zeros(4, 4, dtype=torch.bool); m2[0:2, 0:2] = True
print("canonical G logits rank/shape :", logits.ndim, tuple(logits.shape))
print("canonical scientific mask rank:", m2.ndim, tuple(m2.shape), m2.dtype)
try:
    _ = logits[m2]
    print("logits[mask] -> (unexpected) no error")
except Exception as e:
    print("frozen defective `logits[mask]` ->", type(e).__name__, ":", str(e)[:90])
print()
u = jload(AUD / "phase35_gradcam_target_rank_unit_v1_0d.json")
for r in u["results"]:
    if r["test"].startswith("D1"):
        print("reproduced in the frozen unit artifact:", r["test"], "->", r["observed"])
''')

md("## 4. Exact rank-safe contract (frozen by v1.0d)")
code('''\
t = jload(AUD / "phase35_gradcam_rank_repair_terminal_v1_0d.json")
for k, v in t["rank_safe_contract"].items():
    print(f"  {k:14s} = {v}")
print()
import re
src = (ROOT / "scripts/analysis/phase35_interpretability_execution_v1_0d.py").read_text(encoding="utf-8")
body = src.split("def gradcam_target_scalar_rank_safe(logits, mask):")[1].split("def gradcam_gradient")[0]
for line in body.splitlines():
    if line.strip() and not line.strip().startswith("#"):
        print(line)
''')

md("## 5. Model-free unit-test results (CPU only)")
code('''\
print("tested object:", u["tested_object"]["function"], "in", u["tested_object"]["module"])
print("device:", u["device"], "| cuda used:", u["cuda_used"])
print()
for r in u["results"]:
    print(f"  [{'PASS' if r['pass'] else 'FAIL'}] {r['test']:52s} expected={r['expected']} observed={r['observed']}")
print()
print("TOTAL:", u["n_tests"], "tests,", u["n_failed"], "failed | all_pass:", u["all_pass"])
print()
print("execution counters:", json.dumps(u["execution_counters"], indent=1))
''')

md("## 6. Semantic diff v1.0c → v1.0d")
code('''\
df = jload(AUD / "phase35_v1_0c_to_v1_0d_semantic_diff.json")
for k in ("scientific_specification_changed", "gradcam_scalar_scientific_intent_changed",
          "target_population_changed", "target_mask_source_changed", "target_threshold_changed",
          "empty_mask_fallback_changed", "gradcam_layers_changed", "gradcam_algorithm_changed",
          "cam_normalization_changed", "precision_context_changed", "router_science_changed",
          "film_science_changed"):
    print(f"  {k:46s} = {df[k]}")
print()
print("only implementation change :", df["only_implementation_change"])
print("scientific change class    :", df["scientific_semantic_change_class"])
print("functions added in v1.0d   :", df["functions_added_in_v1_0d"])
print("functions wrapped in v1.0d :", df["functions_wrapped_in_v1_0d"])
print("thresholds                 :", df["thresholds"])
''')

md("## 7. Call graph — modes reach the repaired helper")
code('''\
pf = jload(AUD / "phase35_execution_source_static_preflight_v1_0d.json")
for k, v in pf["call_graph_reachability"].items():
    print(f"  {k:66s} = {v}")
''')

md("## 8. Static preflight (zero execution)")
code('''\
print("effective execution source set:", pf["effective_execution_source_set"])
print("predecessors preserved:", pf["n_predecessors_preserved"],
      "| all match:", pf["preservation_all_match"])
print("original 54 checks :", pf["original_n_checks"], "| failed:", pf["original_n_failed"])
print("additional v1.0d   :", pf["additional_n_checks"], "| failed:", pf["additional_n_failed"])
print("rank-safety checks :", pf["rank_safety_n_checks"], "| failed:", pf["rank_safety_n_failed"])
print("TOTAL              :", pf["total_n_checks"], "checks,", pf["total_n_failed"], "failed")
print("static_source_preflight_pass:", pf["static_source_preflight_pass"])
print()
print("rank-safety checks:")
for k, v in pf["rank_safety_checks"].items():
    print(f"  [{'PASS' if v else 'FAIL'}] {k}")
''')

md("## 9. Source freeze")
code('''\
fz = jload(AUD / "phase35_preexecution_source_freeze_v1_0d.json")
for name, spec in fz["frozen_source_set"].items():
    print(f"  {name:32s} {spec['sha256']}")
print()
for k in ("v1_0_spec_preserved", "v1_0b_source_preserved", "v1_0c_source_preserved",
          "v1_0c_smoke_amendment_preserved", "v1_0d_rank_repair_complete",
          "future_smoke_must_use_exact_v1_0d_bytes", "first_scientific_execution_started"):
    print(f"  {k:44s} = {fz[k]}")
print()
print("frozen authorities:")
for name, spec in fz["frozen_authorities"].items():
    print(f"  {name:38s} {spec.get('sha256','')}")
''')

md("## 10. Eligibility adjudication")
code('''\
el = jload(AUD / "phase35_execution_eligibility_adjudication_v1_0d.json")
for k in ("film_parameter_analysis_source_eligible", "router_VAL808_attribution_source_eligible",
          "gradcam_bridge_source_eligible", "gradcam_decoder1_source_eligible",
          "first_scientific_gradcam_execution_eligible",
          "first_phase35_scientific_execution_eligible",
          "scientific_gradcam_authorized_by_static_checks_alone",
          "synthetic_smoke_reexecution_eligible", "synthetic_smoke_executed_in_v1_0d"):
    print(f"  {k:56s} = {el[k]}")
print()
print("block reason:", el["first_scientific_gradcam_execution_block_reason"])
print("gates:", el["smoke_gate_env"], "|", el["science_gate_env"])
''')

md("## 11. No-model-execution audit")
code('''\
ne = jload(AUD / "phase35_v1_0d_no_model_execution_audit.json")
for k, v in ne["model_execution_counters"].items():
    print(f"  {k:34s} = {v}")
print()
print("allowed separately (recorded distinctly):")
for k, v in ne["allowed_separately"].items():
    print(f"  {k:44s} = {v}")
''')

md("## 12. Final check and terminal")
code('''\
fc = jload(AUD / "phase35_gradcam_rank_repair_final_check_v1_0d.json")
print("final check:", fc["n_checks"], "checks,", fc["n_failed"], "failed")
print("defect:", fc["defect"], "->", fc["defect_status"])
print()
tm = jload(AUD / "phase35_gradcam_rank_repair_terminal_v1_0d.json")
print("terminal:"); print(" ", tm["terminal"])
''')

md("""---
## Summary

| item | value |
|---|---|
| defect `PHASE35_V1_0B_GRADCAM_TARGET_MASK_RANK_INCOMPATIBILITY` | **REPAIRED** (implementation only) |
| scientific specification / target source / threshold / fallback | **UNCHANGED** |
| canonical logits contract | rank 4, `[1,1,H,W]`, batch 1, channels 1 |
| canonical mask contract | rank 2, `[H,W]`, Boolean |
| repaired helper | `gradcam_target_scalar_rank_safe` |
| `mode_gradcam` / `mode_science` / `mode_smoke` → repaired helper | YES / YES / YES |
| frozen defective `logits[mask]` path | UNREACHABLE |
| static preflight | 96 checks · 0 failed · 34 predecessors byte-identical |
| model-free CPU rank unit tests | 11 tests · 0 failed |
| v1.0d source freeze | COMPLETE |
| synthetic smoke | ELIGIBLE, NOT STARTED |
| first scientific Grad-CAM execution | NOT eligible (pending successful v1.0d smoke) |
| model constructions · checkpoint loads · forwards · model autograd | 0 · 0 · 0 · 0 |
| raw VAL · real p_global · GT · ROUTER_HOLDOUT · TEST | 0 · 0 · 0 · 0 · 0 |
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
    audit = {"artifact": "phase35_gradcam_rank_repair_reviewer_notebook_audit_v1_0d", "phase": 35,
             "section": "\u00A7T", "method": "RA-MedFiLM-BARR", "revision": REVISION,
             "path": str(NB.relative_to(ROOT)).replace("\\", "/"), "sha256": hashes[-1],
             "cell_count": len(nb.cells), "markdown_cells": n_md, "code_cells": n_code,
             "executed_code_cells": n_exec, "error_cells": errs, "replay_count": 3,
             "replays_byte_identical": len(set(hashes)) == 1,
             "unit_test_rerun_between_renders": False,
             "model_free_cpu_tensor_probe_in_notebook": True,
             "counters": {"model_constructions": 0, "checkpoint_deserializations": 0,
                          "model_forwards": 0, "model_autograd_calls": 0, "gradcam_executions": 0,
                          "router_attribution_executions": 0, "raw_image_reads": 0,
                          "real_persisted_p_global_reads": 0, "gt_reads": 0,
                          "router_holdout_reads": 0, "test_reads": 0, "gate_env_vars_set": 0,
                          "mode_invocations": 0, "training_steps": 0},
             "all_counters_zero": True, "all_pass": errs == 0 and n_exec == n_code}
    p = AUD / "phase35_gradcam_rank_repair_reviewer_notebook_audit_v1_0d.json"
    p.write_text(json.dumps(audit, indent=1) + "\n", encoding="utf-8")
    print("wrote", p)
    print("audit sha256:", sha256_file(p))


if __name__ == "__main__":
    main()
