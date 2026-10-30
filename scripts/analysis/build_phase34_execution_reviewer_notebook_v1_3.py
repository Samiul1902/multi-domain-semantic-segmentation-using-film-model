#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build AND execute the Phase34 v1.3 MEASURED efficiency/runtime reviewer notebook.

Classification: READ_ONLY_PHASE34_V1_3_MEASURED_EFFICIENCY_RUNTIME_PROFILING_REVIEWER_NOTEBOOK

Reads ONLY already-created measured profiling tables/JSONs. Never loads checkpoints, constructs
models, runs forwards, reruns latency/throughput, measures memory, profiles MAC/FLOP, accesses
protected data, opens TEST or trains.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/build_phase34_execution_reviewer_notebook_v1_3.py
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
      "phase34_efficiency_profiling_execution_v1_3_review.ipynb")
KERNEL = "jup-venv"
REVISION = "ra_medfilm_barr_phase34_efficiency_profiling_v1_3"

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


print("Phase34 v1.3 measured efficiency / runtime profiling review")
print("READ-ONLY. No checkpoint load, no model construction, no forward, no timing rerun,")
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


md(f"""# Phase 34 — v1.3 First Measured Computational Efficiency / Runtime Profiling
## Reviewer Notebook

**Classification:** `READ_ONLY_PHASE34_V1_3_MEASURED_EFFICIENCY_RUNTIME_PROFILING_REVIEWER_NOTEBOOK`
**Revision:** `{REVISION}`

Frozen v1.3 harness + worker were used with canonical component semantics. Evidence classes are
kept separate: historical analytical compute · static model resources · measured
hardware-specific runtime · conditional computation.
""")

md("## 0. Setup")
code(SETUP)

md("## 1. Authority, source freeze and gates")
code('''\
pf = jload(AUD / "phase34_execution_source_preflight_measured_v1_3.json")
print("additive preflight:", pf["additive_filename"],
      "| all sources match:", pf["all_sources_match"],
      "| smoke driver used:", pf["smoke_only_driver_used_for_measurement"])
sd = jload(AUD / "phase34_smoke_only_driver_scope_record_v1_3.json")
print("smoke driver role:", sd["driver_role"],
      "| eligible for measured execution:", sd["eligible_for_measured_execution"])
env = jload(AUD / "phase34_measured_execution_environment_v1_3.json")
print("environment gate:", env["environment_gate_pass"])
for k, v in env["environment_checks"].items():
    print(f"  {k:28s} = {v}")
''')

md("## 2. Component / checkpoint identity and parameters")
code('tshow("phase34_static_resource_profile_v1_3.csv")')

md("## 3. Historical analytical MAC comparators")
code('tshow("phase34_analytical_compute_summary_v1_3.csv")')

md("## 4. Batch-1 latency (synthetic hardware microbenchmark)")
code('tshow("phase34_batch1_latency_results_v1_3.csv")')

md("## 5. Batch-8 throughput")
code('tshow("phase34_batch8_throughput_results_v1_3.csv")')

md("## 6. GPU memory")
code('tshow("phase34_gpu_memory_results_v1_3.csv")')

md("## 7. Controlled SKIP / EXECUTE path runtime")
code('''\
lat = pd.read_csv(TAB / "phase34_batch1_latency_results_v1_3.csv")
for arm in ("SKIP_CONTROLLED_PATH", "EXECUTE_CONTROLLED_PATH"):
    r = lat[lat["arm"] == arm].iloc[0]
    print(f"  {arm:24s} mean={r['mean_ms']:.6f} ms  p50={r['p50_ms']:.6f} "
          f"scope={r['scope']}")
''')

md("## 8. Conditional weighted runtime estimate")
code('tshow("phase34_conditional_runtime_estimate_v1_3.csv")')

md("## 9. Claim limitations and protected-access state")
code('''\
res = jload(AUD / "phase34_efficiency_result_v1_3.json")
print("claims not made:", res["claims_not_made"])
print()
print("scope limitations:", res["scope_limitations"])
print()
prov = jload(AUD / "phase34_runtime_execution_provenance_v1_3.json")
print("protected-data counters:")
for k, v in prov["protected_data_counters"].items():
    print(f"  {k:28s} = {v}")
print()
print("aliases (measured once, not double-counted):", prov["aliases"])
print("distinct measured arms:", prov["distinct_measured_arms"])
print("pre-timing smoke forwards during measured run:", prov["premeasurement_smoke_forwards"])
''')

md("## 10. Execution audit and final check")
code('''\
au = jload(AUD / "phase34_efficiency_execution_audit_v1_3.json")
print("audit all_pass:", au["all_pass"], "| harness:", au["frozen_harness_used"],
      "| worker:", au["frozen_worker_used"])
fc = jload(AUD / "phase34_execution_final_check_v1_3.json")
print("final check:", fc["n_checks"], "checks,", fc["n_failed"], "failed")
term = jload(AUD / "phase34_execution_terminal_v1_3.json")
print()
print("terminal:")
print(" ", term["terminal"])
''')

md("""---
## Summary

| evidence class | content |
|---|---|
| HISTORICAL_ANALYTICAL_COMPUTE | C1 31,551,740,928 · C2 34,782,403,584 · A8/C9 32,437,902,022.58 · gated C9 34,782,440,912 MACs |
| STATIC_MODEL_RESOURCE_PROFILE | G 3,523,001 · R_psi 1,276,401 · B_phi 36,801 · S_omega 1,217 (total 4,837,420) |
| MEASURED_HARDWARE_SPECIFIC_RUNTIME_PROFILE | batch-1 latency + batch-8 throughput + GPU memory on RTX 3060 Ti |
| CONDITIONAL_COMPUTATION_PROFILE | weighted runtime from frozen Phase30 states (qualified) |

Scope labels: `MODEL_COMPUTE_PATH_RUNTIME` / `SYNTHETIC_COMPONENT_RUNTIME`.
`END_TO_END_PIPELINE_RUNTIME` **not** claimed. TEST locked · Phase35 not started.
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
        "artifact": "phase34_execution_reviewer_notebook_audit_v1_3", "phase": 34,
        "section": "\u00A7W", "method": "RA-MedFiLM-BARR", "revision": REVISION,
        "path": str(NB.relative_to(ROOT)).replace("\\", "/"), "sha256": hashes[-1],
        "cell_count": len(nb.cells), "markdown_cells": n_md, "code_cells": n_code,
        "executed_code_cells": n_exec, "error_cells": errs,
        "replay_count": 3, "replays_byte_identical": len(set(hashes)) == 1,
        "gpu_profiling_rerun_between_renders": False,
        "counters": {"checkpoint_loads": 0, "model_constructions": 0, "model_forwards": 0,
                     "latency_reruns": 0, "throughput_reruns": 0, "memory_measurements": 0,
                     "MAC_or_FLOP_profile_executions": 0, "raw_image_reads": 0,
                     "raw_GT_reads": 0, "ROUTER_HOLDOUT_raw_reads": 0, "TEST_reads": 0,
                     "training_steps": 0},
        "all_counters_zero": True,
        "all_pass": errs == 0 and n_exec == n_code,
    }
    p = AUD / "phase34_execution_reviewer_notebook_audit_v1_3.json"
    p.write_text(json.dumps(audit, indent=1) + "\n", encoding="utf-8")
    print("wrote", p)
    print("audit sha256:", sha256_file(p))


if __name__ == "__main__":
    main()
