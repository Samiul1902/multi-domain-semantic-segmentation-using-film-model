#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build AND execute the Phase34 v1.4 latency-execution reviewer notebook.

Classification: READ_ONLY_PHASE34_LATENCY_EXECUTION_V1_4_REVIEWER_NOTEBOOK

Reads ONLY frozen v1.4 latency outputs and preserved v1.3 non-latency tables. Never constructs
models, loads checkpoints, runs forwards, reruns timing/throughput, measures memory, runs a
profiler, accesses protected data, opens TEST or trains.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/build_phase34_latency_execution_notebook_v1_4.py
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
      "phase34_latency_execution_v1_4_review.ipynb")
KERNEL = "jup-venv"
REVISION = "ra_medfilm_barr_phase34_efficiency_profiling_v1_4"

SETUP = '''\
import hashlib
import json
from pathlib import Path

import numpy as np
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


print("Phase34 v1.4 latency-only protocol-compliant re-execution review")
print("READ-ONLY. No checkpoint load, no model construction, no forward, no timing rerun,")
print("no throughput/memory rerun, no profiler, no protected data, no TEST, no training.")
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


md(f"""# Phase 34 — v1.4 Latency-Only Protocol-Compliant Re-Execution
## Reviewer Notebook

**Classification:** `READ_ONLY_PHASE34_LATENCY_EXECUTION_V1_4_REVIEWER_NOTEBOOK`
**Revision:** `{REVISION}`

Six canonical batch-1 arms profiled with **1000 per-forward CUDA-event observations each**
(6000 raw observations). Throughput, memory, static-resource and analytical MAC evidence from
v1.3 is **reused valid, not regenerated**.
""")

md("## 0. Setup")
code(SETUP)

md("## 1. Source preflight, environment and provenance")
code('''\
pf = jload(AUD / "phase34_latency_execution_source_preflight_v1_4.json")
print("preflight pass:", pf["all_pass"], "| sources:", pf["all_sources_match"],
      "| preserved v1.3:", pf["preserved_valid_v1_3_all_match"],
      "| checkpoints:", pf["all_checkpoints_match"])
env = jload(AUD / "phase34_latency_execution_environment_v1_4.json")
print("environment gate:", env["environment_gate_pass"])
for k, v in env["environment_checks"].items():
    print(f"  {k:28s} = {v}")
pv = jload(AUD / "phase34_latency_execution_provenance_v1_4.json")
print()
print("six-arm order:", pv["six_arm_order"])
print("physical worker count:", pv["physical_worker_count"],
      "| alias physical worker count:", pv["alias_physical_worker_count"])
print("CUDA-event granularity:", pv["cuda_event_granularity"])
''')

md("## 2. Raw observation integrity (independent, from CSV)")
code('''\
ig = jload(AUD / "phase34_latency_observation_integrity_v1_4.json")
print("rows:", ig["row_count"], "| arms:", ig["arm_count"],
      "| aliases present:", ig["aliases_physically_present"])
print("per-arm counts:", ig["per_arm_counts"])
print("duplicates:", ig["duplicate_key_count"], "| missing:", ig["missing_count"],
      "| non-finite:", ig["non_finite_latency_count"],
      "| non-positive:", ig["non_positive_latency_count"])
print("global index 0..999 per arm:", ig["global_iteration_index_0_999"])
print("task counts exact 250 each:", ig["task_counts_exact_250_each"])
print("integrity pass:", ig["all_pass"])
''')

md("## 3. Latency summary (six canonical arms)")
code('''\
sm = tshow("phase34_batch1_latency_results_v1_4.csv")
''')

md("## 4. Independent summary reproduction")
code('''\
rp = jload(AUD / "phase34_latency_summary_reproduction_v1_4.json")
print("means reproduced   :", rp["means_reproduced"], "/ 6")
print("std reproduced     :", rp["std_reproduced"], "/ 6")
print("p50 reproduced     :", rp["p50_reproduced"], "/ 6")
print("p90 reproduced     :", rp["p90_reproduced"], "/ 6")
print("p95 reproduced     :", rp["p95_reproduced"], "/ 6")
print("p99 reproduced     :", rp["p99_reproduced"], "/ 6")
print("min reproduced     :", rp["min_reproduced"], "/ 6")
print("max reproduced     :", rp["max_reproduced"], "/ 6")
print("all fields 6/6    :", rp["all_fields_6_of_6"])
''')

md("## 5. Per-forward latency distribution (illustrative recomputation from raw CSV)")
code('''\
obs = pd.read_csv(TAB / "phase34_batch1_latency_observations_v1_4.csv")
print("raw observation rows:", len(obs))
for arm in ["GLOBAL_ONLY_C1", "R_PSI_COMPONENT", "B_PHI_COMPONENT", "S_OMEGA_COMPONENT",
            "SKIP_CONTROLLED_PATH", "EXECUTE_CONTROLLED_PATH"]:
    v = obs.loc[obs["arm"] == arm, "latency_ms"].to_numpy(dtype=np.float64)
    q = np.quantile(v, [0.50, 0.90, 0.95, 0.99], method="linear")
    print(f"  {arm:24s} n={v.size} mean={np.mean(v):.6f} std={np.std(v, ddof=1):.6f} "
          f"p50={q[0]:.6f} p90={q[1]:.6f} p95={q[2]:.6f} p99={q[3]:.6f} "
          f"min={np.min(v):.6f} max={np.max(v):.6f}")
''')

md("## 6. Conditional weighted runtime")
code('''\
tshow("phase34_conditional_runtime_estimate_v1_4.csv")
''')

md("## 7. v1.4 vs v1.3 salvage (descriptive only)")
code('''\
tshow("phase34_v1_4_vs_v1_3_salvage_comparison.csv")
print()
print("NOTE: descriptive only - no acceptance range, no rerun trigger, no best-run selection.")
print("v1.3 has no valid per-iteration std/percentiles, so none are compared.")
''')

md("## 8. Preserved valid v1.3 non-latency evidence (reused, not regenerated)")
code('''\
tshow("phase34_batch8_throughput_results_v1_3.csv")
tshow("phase34_gpu_memory_results_v1_3.csv")
tshow("phase34_static_resource_profile_v1_3.csv")
tshow("phase34_analytical_compute_summary_v1_3.csv")
''')

md("## 9. Repaired composite result, audit and final check")
code('''\
res = jload(AUD / "phase34_efficiency_result_v1_4.json")
print("v1.3 latency superseded:", res["v1_3_latency_superseded_due_measurement_granularity_defect"])
print("v1.3 throughput reused valid:", res["v1_3_throughput_reused_valid"])
print("v1.3 memory reused valid:", res["v1_3_memory_reused_valid"])
print("v1.3 static resources reused valid:", res["v1_3_static_resources_reused_valid"])
print("v1.3 analytical MAC reused valid:", res["v1_3_analytical_MAC_reused_valid"])
print("claims not made:", res["claims_not_made"])
print()
au = jload(AUD / "phase34_latency_execution_audit_v1_4.json")
print("audit all_pass:", au["all_pass"], "| throughput reruns:", au["throughput_reruns"],
      "| memory reruns:", au["memory_reruns"])
fc = jload(AUD / "phase34_latency_execution_final_check_v1_4.json")
print("final check:", fc["n_checks"], "checks,", fc["n_failed"], "failed")
term = jload(AUD / "phase34_latency_execution_terminal_v1_4.json")
print()
print("terminal:")
print(" ", term["terminal"])
''')

md("""---
## Summary

| item | value |
|---|---|
| physical latency arms | 6 (aliases not physically re-executed) |
| observations | 1000 per arm · 6000 raw rows |
| observation unit | one CUDA-event interval per individual forward |
| statistics | mean · sample std (ddof=1) · linear p50/p90/p95/p99 · min · max |
| raw integrity | 0 duplicates · 0 missing · 0 non-finite · 0 non-positive |
| summary reproduction | 6/6 on all eight statistics |
| L_SKIP / L_EXECUTE / L_weighted | per-forward means from v1.4 protocol |
| v1.3 throughput / memory / static / MAC | preserved valid, reused |
| Phase34 closure | NOT performed · Phase35 NOT started · TEST locked |
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
        "artifact": "phase34_latency_execution_reviewer_notebook_audit_v1_4", "phase": 34,
        "section": "\u00A7Z", "method": "RA-MedFiLM-BARR", "revision": REVISION,
        "path": str(NB.relative_to(ROOT)).replace("\\", "/"), "sha256": hashes[-1],
        "cell_count": len(nb.cells), "markdown_cells": n_md, "code_cells": n_code,
        "executed_code_cells": n_exec, "error_cells": errs,
        "replay_count": 3, "replays_byte_identical": len(set(hashes)) == 1,
        "latency_rerun_between_renders": False,
        "counters": {"model_constructions": 0, "checkpoint_loads": 0, "model_forwards": 0,
                     "latency_reruns": 0, "throughput_reruns": 0, "memory_measurements": 0,
                     "MAC_or_FLOP_profile_executions": 0, "raw_image_reads": 0,
                     "raw_GT_reads": 0, "ROUTER_HOLDOUT_raw_reads": 0, "TEST_reads": 0,
                     "training_steps": 0},
        "all_counters_zero": True,
        "all_pass": errs == 0 and n_exec == n_code,
    }
    p = AUD / "phase34_latency_execution_reviewer_notebook_audit_v1_4.json"
    p.write_text(json.dumps(audit, indent=1) + "\n", encoding="utf-8")
    print("wrote", p)
    print("audit sha256:", sha256_file(p))


if __name__ == "__main__":
    main()
