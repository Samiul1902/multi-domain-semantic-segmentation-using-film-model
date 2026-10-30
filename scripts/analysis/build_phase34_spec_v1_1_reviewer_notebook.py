#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build AND execute the Phase34 v1.1 runtime-semantics reconciliation reviewer notebook.

Classification: READ_ONLY_PHASE34_V1_1_RUNTIME_SEMANTICS_RECONCILIATION_REVIEWER_NOTEBOOK

Renders v1.1 contracts and static arithmetic ONLY. Does NOT load models, run forwards, time
CUDA, measure memory, run profiler tools, access raw protected data, open TEST or train.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/build_phase34_spec_v1_1_reviewer_notebook.py
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
      "phase34_efficiency_profiling_spec_v1_1_review.ipynb")
KERNEL = "jup-venv"
REVISION = "ra_medfilm_barr_phase34_efficiency_profiling_v1_1"

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


print("Phase34 v1.1 runtime-semantics + analytical-comparator reconciliation")
print("READ-ONLY. No model load, no forward, no CUDA timing, no memory profiling,")
print("no profiler tools, no protected data, no TEST, no training.")
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


md(f"""# Phase 34 — Computational Efficiency & Runtime Profiling
## v1.1 Runtime-Semantics + Analytical-Comparator Reconciliation (Reviewer Notebook)

**Classification:** `READ_ONLY_PHASE34_V1_1_RUNTIME_SEMANTICS_RECONCILIATION_REVIEWER_NOTEBOOK`
**Revision:** `{REVISION}`

v1.0 was pre-execution and produced **no measurements**. v1.1 repairs two specification-level
issues before the first measurement. No measured Phase34 result changed, because none existed.
""")

md("## 0. Setup")
code(SETUP)

md("## 1. v1.0 preservation and defect classification")
code('''\
dr = jload(AUD / "phase34_v1_0_runtime_semantics_and_comparator_defect_record.json")
print("classification:", dr["classification"])
for i in dr["issues"]:
    print(f"  {i['issue_id']}: {i['code']}")
print()
print("model measurements already performed:", dr["model_measurements_already_performed"])
print("scientific runtime results exist:", dr["scientific_runtime_results_exist"])
print("latency results exist:", dr["latency_results_exist"])
print("memory results exist:", dr["memory_results_exist"])
print("runtime results invalidated:", dr["runtime_results_invalidated"])
print("repair required before first measurement:", dr["repair_required_before_first_measurement"])
print("v1.0 artifacts preserved:", dr["v1_0_artifacts_preserved"])
assert dr["model_measurements_already_performed"] is False
''')

md("""## 2. Issue 1 — canonical component-specific runtime precision

G is the **only** component whose canonical inference runs under `autocast(float16)` with
`torch.no_grad()` and `inference_mode = false`. R_psi / B_phi / S_omega run with autocast
disabled under `torch.inference_mode()`.""")
code('''\
pc = jload(AUD / "phase34_precision_execution_semantics_contract_v1_1.json")
print("primary runtime profile:", pc["primary_runtime_profile"])
print("secondary uniform FP32 profile:", pc["secondary_uniform_fp32_profile"])
print("component semantics not interchangeable:", pc["component_semantics_not_interchangeable"])
print()
for cid, s in pc["PRIMARY_CANONICAL_COMPONENT_SEMANTICS"].items():
    print(f"  {cid:8s} dtype={s['model_dtype']:8s} autocast={str(s['autocast_enabled']):5s} "
          f"dtype={s['autocast_dtype']} ctx={s['grad_context']:22s} "
          f"inference_mode={s['inference_mode']} sci_batch={s['canonical_scientific_batch_semantics']}")
print()
print("invariants:")
for inv in pc["invariants"]:
    print("  -", inv)
''')

md("""## 3. Batch-size semantics

Batch 1 remains the primary latency measurement but is **not** canonical numerical
reproduction: the frozen scientific G path uses batch 8 and is batch-membership sensitive
under autocast(fp16).""")
code('''\
print("batch1 label:")
print(" ", pc["PRIMARY_CANONICAL_COMPONENT_SEMANTICS"]["G"]["phase34_batch1_benchmark_semantics"])
sc = jload(AUD / "phase34_measured_runtime_scope_v1_1.json")
print()
print("timing-scope classifications:")
for arm, v in sc["per_arm_timing_scope"].items():
    print(f"  {arm:22s} -> {v['classification']}")
print()
print("END_TO_END_PIPELINE_RUNTIME used:", sc["end_to_end_pipeline_runtime_used"])
''')

md("""## 4. Issue 2 — analytical comparators reconciled

`LITERAL_ALWAYS_REFINE_C2` **bypasses routing** (`router_present = false`). A gated
execute-all C9 graph retains router overhead and is labelled separately.""")
code('''\
ac = jload(AUD / "phase34_analytical_compute_contract_v1_1.json")
print("label:", ac["label"])
print()
for name, c in ac["comparators"].items():
    print(f"  {name}")
    print(f"      formula = {c['formula']}")
    print(f"      MAC     = {c['mac']}")
    print(f"      router={c['router_present']} refiner={c['refiner_present']} "
          f"s_omega={c['s_omega_present']}")
    print(f"      label   = {c['scientific_label']}")
print()
print("C2 router present:", ac["literal_always_refine_C2_router_present"])
print("C2 != gated execute-all C9:", ac["literal_always_refine_C2_not_equal_gated_execute_all_C9"])
print("denominators merged:", ac["comparator_denominators_merged"])
''')

md("## 5. Static comparator arithmetic (no model, no profiler)")
code('''\
r = ac["ratios"]
print("ratio vs LITERAL_GLOBAL_ONLY_C1        :", r["ratio_vs_LITERAL_GLOBAL_ONLY_C1"])
print("ratio vs LITERAL_ALWAYS_REFINE_C2      :", r["ratio_vs_LITERAL_ALWAYS_REFINE_C2"])
print("saving vs LITERAL_ALWAYS_REFINE_C2     :",
      r["absolute_saving_vs_LITERAL_ALWAYS_REFINE_C2"], "MACs")
print("ratio vs gated execute-all C9          :", r["ratio_vs_gated_execute_all_C9"])
print("saving vs gated execute-all C9         :",
      r["absolute_saving_vs_gated_execute_all_C9"], "MACs")
print()
C1 = ac["comparators"]["literal_global_only_C1"]["mac"]
C2 = ac["comparators"]["literal_always_refine_C2"]["mac"]
E = ac["comparators"]["final_A8_C9_expected_conditional"]["mac"]
assert C1 == 31551740928 and C2 == 34782403584
assert abs(r["ratio_vs_LITERAL_ALWAYS_REFINE_C2"] - E / C2) < 1e-12
print("assertions OK: C1/C2 exact; ratio reproduced from frozen integers")
''')

md("## 6. v1.1 profiling arm registry")
code('tshow("phase34_profiling_arm_registry_v1_1.csv")')

md("## 7. v1.1 source freeze")
code('''\
sf = jload(AUD / "phase34_preexecution_source_freeze_v1_1.json")
for s in sf["frozen_sources"]:
    h = s["sha256"][:16] if s["sha256"] else "MISSING"
    print(f"  {h}...  {s['role']:52s} {s['path']}")
print()
print("v1.0 source freeze preserved:", sf["v1_0_source_freeze_preserved"])
print("v1.1 supersedes v1.0 for future measurement:",
      sf["v1_1_supersedes_v1_0_for_future_measurement"])
print("no v1.0 measurement executed:", sf["no_v1_0_measurement_was_executed"])
''')

md("## 8. v1.1 execution eligibility")
code('''\
ea = jload(AUD / "phase34_execution_eligibility_adjudication_v1_1.json")
for k, v in ea["families"].items():
    print(f"  {k:56s} = {str(v['value']):5s}")
print()
print("canonical component semantics runtime ready:",
      ea["canonical_component_semantics_runtime_ready"])
print("batch1 role:", ea["batch1_runtime_role"])
print("batch8 role:", ea["batch8_runtime_role"])
print("literal C2 reconciled:", ea["literal_C2_comparator_semantics_reconciled"])
print("measured runtime execution eligible:", ea["measured_runtime_execution_eligible"])
''')

md("## 9. Zero-execution audit")
code('''\
ne = jload(AUD / "phase34_v1_1_no_execution_audit.json")
for k, v in ne["counters"].items():
    print(f"  {k:46s} = {v}")
print("all zero:", ne["all_zero"])
assert ne["all_zero"]
''')

md("## 10. v1.1 final check and terminal")
code('''\
fc = jload(AUD / "phase34_specification_final_check_v1_1.json")
print("final check:", fc["n_checks"], "checks,", fc["n_failed"], "failed")
term = jload(AUD / "phase34_specification_terminal_v1_1.json")
print()
print("terminal:")
print(" ", term["terminal"])
''')

md("""---
## Summary

| item | value |
|---|---|
| v1.0 measurements produced | 0 (pre-execution) |
| G canonical runtime | float32 + autocast(fp16) + no_grad + inference_mode FALSE |
| R_psi / B_phi / S_omega | float32 + autocast OFF + inference_mode |
| primary runtime profile | `COMPONENT_SPECIFIC_CANONICAL_PRECISION_SEMANTICS` |
| uniform FP32 profile | `INELIGIBLE_NOT_REQUIRED` |
| batch-1 role | hardware microbenchmark, NOT canonical numerical reproduction |
| LITERAL C1 | MAC(G) |
| LITERAL C2 | MAC(G) + MAC(R_psi) — routing bypassed |
| gated execute-all C9 | separate label, router retained |
| model loads · forwards · timing · memory | 0 · 0 · 0 · 0 |
| TEST | `LOCKED_UNTIL_PHASE39` |
| Phase34 execution | NOT started |
| Phase35 | NOT started |
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
        "artifact": "phase34_spec_v1_1_reviewer_notebook_audit", "phase": 34,
        "section": "\u00a7P", "method": "RA-MedFiLM-BARR", "revision": REVISION,
        "path": str(NB.relative_to(ROOT)).replace("\\", "/"), "sha256": hashes[-1],
        "cell_count": len(nb.cells), "markdown_cells": n_md, "code_cells": n_code,
        "executed_code_cells": n_exec, "error_cells": errs,
        "replay_count": 3, "replays_byte_identical": len(set(hashes)) == 1,
        "counters": {"model_loads": 0, "model_forwards": 0, "CUDA_profile_iterations": 0,
                     "new_latency_measurements": 0, "new_FPS_measurements": 0,
                     "new_peak_memory_measurements": 0,
                     "new_model_MAC_or_FLOP_profile_executions": 0, "raw_image_reads": 0,
                     "raw_GT_reads": 0, "ROUTER_HOLDOUT_raw_reads": 0, "TEST_reads": 0,
                     "training_steps": 0},
        "all_counters_zero": True,
        "all_pass": errs == 0 and n_exec == n_code,
    }
    p = AUD / "phase34_spec_v1_1_reviewer_notebook_audit.json"
    p.write_text(json.dumps(audit, indent=1) + "\n", encoding="utf-8")
    print("wrote", p)
    print("audit sha256:", sha256_file(p))


if __name__ == "__main__":
    main()
