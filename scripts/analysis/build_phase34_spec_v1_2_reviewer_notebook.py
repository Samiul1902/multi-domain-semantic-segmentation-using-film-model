#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build AND execute the Phase34 v1.2 executable-harness / task-binding reviewer notebook.

Classification: READ_ONLY_PHASE34_V1_2_EXECUTABLE_HARNESS_AND_TASK_BINDING_REVIEWER_NOTEBOOK

Renders v1.2 contracts and static audits ONLY. Does NOT load checkpoints into models, does
NOT construct canonical models, does NOT run forwards, does NOT time, does NOT measure
memory, does NOT touch protected data, does NOT open TEST and does NOT train.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/build_phase34_spec_v1_2_reviewer_notebook.py
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
NB = (ROOT / "notebooks" / "phasewise" / "phase_34_efficiency_profiling" /
      "phase34_efficiency_profiling_spec_v1_2_review.ipynb")
KERNEL = "jup-venv"
REVISION = "ra_medfilm_barr_phase34_efficiency_profiling_v1_2"

SETUP = '''\
import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(r"D:\\Softfors\\jup")
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def jload(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def tshow(name, n=None):
    df = pd.read_csv(TAB / name)
    print(name, "| shape:", df.shape)
    if n is not None:
        df = df.head(n)
    with pd.option_context("display.max_columns", None, "display.width", 240):
        print(df.to_string(index=False))
    return df


print("Phase34 v1.2 executable-harness + synthetic task-conditioning binding review")
print("READ-ONLY. No checkpoint load, no model construction, no forward, no timing,")
print("no memory measurement, no profiler, no protected data, no TEST, no training.")
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


md(f"""# Phase 34 — v1.2 Executable Harness & Task-Conditioning Binding
## Reviewer Notebook

**Classification:** `READ_ONLY_PHASE34_V1_2_EXECUTABLE_HARNESS_AND_TASK_BINDING_REVIEWER_NOTEBOOK`
**Revision:** `{REVISION}`

v1.0 = specification only · v1.1 = semantics repair only · first v1.1 execution attempt =
correctly **BLOCKED_PREMODEL**. No model was loaded, constructed, deserialized or forwarded,
and no runtime/memory measurement exists. v1.2 replaces only the non-executable harness and
the missing synthetic task-conditioning binding.
""")

md("## 0. Setup")
code(SETUP)

md("## 1. v1.1 blocked attempt — preserved")
code('''\
bt = jload(AUD / "phase34_execution_blocked_terminal_v1_1.json")
print("terminal:", bt["terminal"])
print("status:", bt["status"])
print("blockers:", bt["blockers"])
print("measurements_performed:", bt["measurements_performed"])
pf11 = jload(AUD / "phase34_execution_source_preflight_v1_1.json")
print("v1.1 preflight pass:", pf11["preflight_pass"])
print("v1.1 missing executable behaviours:",
      pf11["static_semantic_audit"]["required_executable_behaviours_missing"])
''')

md("## 2. v1.2 blocker record")
code('''\
br = jload(AUD / "phase34_v1_1_execution_harness_blocker_record.json")
print("BLOCKER_1:", br["BLOCKER_1"])
print("BLOCKER_2:", br["BLOCKER_2"])
print("v1.1 source hashes were correct:", br["v1_1_source_hashes_were_correct"])
print("v1.1 measurements exist:", br["v1_1_measurements_exist"])
print("repair before first measurement:", br["repair_occurs_before_first_measurement"])
''')

md("## 3. v1.2 static source-semantic audit (AST only)")
code('''\
pf = jload(AUD / "phase34_execution_source_preflight_v1_2.json")
print("inspection:", pf["method_of_inspection"])
print("checks:", pf["n_checks"], "| failed:", pf["n_failed"],
      "| pass:", pf["static_preflight_pass"])
print()
for k, v in pf["checks"].items():
    print(f"  {'PASS' if v else 'FAIL'}  {k}")
''')

md("## 4. Domain → task-id mapping")
code('''\
tc = jload(AUD / "phase34_synthetic_task_conditioning_contract_v1_2.json")
print("authority line:", tc["registry_authority_line"])
for d, v in tc["domain_task_registry"].items():
    print(f"  {d:8s} -> task_id {v['task_id']}  ({v['dtype']}, shape {v['shape_rule']}, "
          f"device {v['device_rule']})")
print()
print("authority:", tc["domain_task_registry"]["ISIC"]["source_authority"])
print("inferred/arbitrary task id permitted during measurement:",
      tc["inferred_or_arbitrary_task_id_permitted_during_measurement"])
''')

md("## 5. Batch-1 task schedule and batch-8 task vector")
code('''\
sc = jload(AUD / "phase34_synthetic_task_schedule_contract_v1_2.json")
print("batch1 schedule:", sc["batch1_task_schedule"])
print("batch1 order:", sc["batch1_task_order"])
print("per 200-iteration block:", sc["per_200_iteration_block"])
print("conditions per task id across 5 blocks:", sc["across_5_blocks_conditions_per_task_id"])
print("total measured iterations:", sc["total_measured_iterations"])
print("warmup iterations:", sc["warmup_iterations"], "| same cycle:",
      sc["warmup_uses_same_deterministic_cycle"],
      "| weighting interpretation:", sc["warmup_has_scientific_weighting_interpretation"])
print()
print("batch8 task vector:", sc["batch8_task_vector"], sc["batch8_task_vector_dtype"])
print("batch8 exactly balanced:", sc["batch8_is_exactly_balanced_four_domain"])
print("batch8 reproduces protected Phase30 membership:",
      sc["batch8_reproduces_protected_phase30_batch_membership"])
print()
print("batch1 classification:", sc["batch1_classification"])
print("batch8 classification:", sc["batch8_classification"])
''')

md("## 6. Structured synthetic feature conditioning")
code('''\
sf = jload(AUD / "phase34_synthetic_structured_feature_contract_v1_2.json")
print("S_omega:")
print("  numeric indices:", sf["S_omega"]["numeric_indices"])
print("  one-hot indices:", sf["S_omega"]["onehot_indices"])
print("  all-20-as-randn:", sf["S_omega"]["all_20_as_unconstrained_randn"])
print("B_phi:")
print("  numeric dim:", sf["B_phi"]["numeric_feature_dim"])
print("  vector contains categorical/one-hot:", sf["B_phi"]["feature_vector_contains_categorical_or_onehot_fields"])
print("  B_PHI_EXPLICIT_TASK_CONDITIONING:", sf["B_phi"]["B_PHI_EXPLICIT_TASK_CONDITIONING"])
print("R_psi:")
print("  R_PSI_EXPLICIT_TASK_CONDITIONING:", sf["R_psi"]["R_PSI_EXPLICIT_TASK_CONDITIONING"])
print("G:")
print("  G_TASK_CONDITIONING:", sf["G"]["G_TASK_CONDITIONING"])
gen = jload(AUD / "phase34_synthetic_generator_terminology_v1_2.json")
print()
print("generator:", gen["generator_construction"], "->", gen["terminology"])
print("NumPy PCG64 used:", gen["numpy_pcg64_used"])
''')

md("## 7. Timed-operation registry")
code('''\
tr = jload(AUD / "phase34_timed_operation_registry_v1_2.json")
for arm, v in tr["arms"].items():
    print(f"  {arm}")
    print(f"      scope    = {v['scope']}")
    print(f"      included = {v['included_operations']}")
    print(f"      preconstructed_inputs={v['input_tensors_preconstructed']} "
          f"checkpoint_load_included={v['checkpoint_load_included']} "
          f"fusion_included={v['fusion_included']} "
          f"decision_logic_included={v['decision_logic_included']}")
print()
print("END_TO_END_PIPELINE_RUNTIME used:", tr["end_to_end_pipeline_runtime_used"])
''')

md("## 8. v1.2 source freeze")
code('''\
sfz = jload(AUD / "phase34_preexecution_source_freeze_v1_2.json")
for k, v in sfz["frozen_sources"].items():
    print(f"  {v['sha256'][:16]}...  {k:18s} {v['path']}")
print()
print("v1.1 source freeze preserved:", sfz["v1_1_source_freeze_preserved"])
print("v1.1 blocked attempt preserved:", sfz["v1_1_blocked_attempt_preserved"])
print("v1.2 supersedes v1.1 for future execution:",
      sfz["v1_2_supersedes_v1_1_for_future_execution"])
print("v1.2 measurements already performed:", sfz["v1_2_measurements_already_performed"])
''')

md("## 9. v1.2 execution eligibility")
code('''\
ea = jload(AUD / "phase34_execution_eligibility_adjudication_v1_2.json")
for k, v in ea["families"].items():
    print(f"  {k:52s} = {str(v['value']):5s}")
print()
print("first measured execution started:", ea["first_measured_execution_started"])
''')

md("## 10. Zero-execution audit")
code('''\
ne = jload(AUD / "phase34_v1_2_no_execution_audit.json")
for k, v in ne["counters"].items():
    print(f"  {k:50s} = {v}")
print("all zero:", ne["all_zero"])
assert ne["all_zero"]
''')

md("## 11. v1.2 final check and terminal")
code('''\
fc = jload(AUD / "phase34_specification_final_check_v1_2.json")
print("final check:", fc["n_checks"], "checks,", fc["n_failed"], "failed")
term = jload(AUD / "phase34_specification_terminal_v1_2.json")
print()
print("terminal:")
print(" ", term["terminal"])
''')

md("""---
## Summary

| item | value |
|---|---|
| v1.1 execution attempt | correctly `BLOCKED_PREMODEL`, preserved |
| v1.2 static preflight | PASS (AST only, 0 failures) |
| domain→task_id | ISIC 0 · BUSI 1 · KVASIR 2 · KUB 3 |
| batch-1 schedule | `iteration_index mod 4`, 50/task/block, 250/task, 1000 total |
| batch-8 vector | `[0,1,2,3,0,1,2,3]` (balanced) |
| S_omega tail | valid one-hot at indices 16..19 |
| B_phi conditioning | integer task id → `Embedding(4,16)` |
| R_psi conditioning | NONE |
| generator | `PYTORCH_CUDA_GENERATOR_SEED_42` (not PCG64) |
| model constructions · loads · forwards · timing · memory | 0 · 0 · 0 · 0 · 0 |
| first measured execution | NOT started |
| TEST | `LOCKED_UNTIL_PHASE39` · Phase35 NOT started |
""")


def build():
    nb = {"cells": CELLS, "metadata": dict(_FIXED_META), "nbformat": 4,
          "nbformat_minor": 5}
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
        "artifact": "phase34_spec_v1_2_reviewer_notebook_audit", "phase": 34,
        "section": "\u00a7AA", "method": "RA-MedFiLM-BARR", "revision": REVISION,
        "path": str(NB.relative_to(ROOT)).replace("\\", "/"), "sha256": hashes[-1],
        "cell_count": len(nb.cells), "markdown_cells": n_md, "code_cells": n_code,
        "executed_code_cells": n_exec, "error_cells": errs,
        "replay_count": 3, "replays_byte_identical": len(set(hashes)) == 1,
        "counters": {"model_loads": 0, "model_constructions": 0, "model_forwards": 0,
                     "CUDA_profile_iterations": 0, "new_latency_measurements": 0,
                     "new_FPS_measurements": 0, "new_peak_memory_measurements": 0,
                     "new_model_MAC_or_FLOP_profile_executions": 0, "raw_image_reads": 0,
                     "raw_GT_reads": 0, "ROUTER_HOLDOUT_raw_reads": 0, "TEST_reads": 0,
                     "training_steps": 0},
        "all_counters_zero": True,
        "all_pass": errs == 0 and n_exec == n_code,
    }
    p = AUD / "phase34_spec_v1_2_reviewer_notebook_audit.json"
    p.write_text(json.dumps(audit, indent=1) + "\n", encoding="utf-8")
    print("wrote", p)
    print("audit sha256:", sha256_file(p))


if __name__ == "__main__":
    main()
