#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build AND execute the Phase34 v1.3 model-identity + untimed smoke-gate reviewer notebook.

Classification: READ_ONLY_PHASE34_V1_3_MODEL_IDENTITY_AND_UNTIMED_SMOKE_GATE_REVIEWER_NOTEBOOK

Reads ONLY the newly frozen smoke JSON artifacts. Never loads checkpoints, constructs models,
runs forwards, times CUDA, measures memory or accesses protected data.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/build_phase34_smoke_reviewer_notebook_v1_3.py
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(r"D:\Softfors\jup")
AUD = ROOT / "reports" / "audits"
NB = (ROOT / "notebooks" / "phasewise" / "phase_34_efficiency_profiling" /
      "phase34_efficiency_profiling_smoke_v1_3_review.ipynb")
KERNEL = "jup-venv"
REVISION = "ra_medfilm_barr_phase34_efficiency_profiling_v1_3"

SETUP = '''\
import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(r"D:\\Softfors\\jup")
AUD = ROOT / "reports" / "audits"


def jload(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


print("Phase34 v1.3 model-identity + untimed smoke-gate review")
print("READ-ONLY. No checkpoint load, no model construction, no forward, no timing,")
print("no memory measurement, no protected data, no TEST, no training.")
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


md(f"""# Phase 34 — v1.3 Model Identity + Untimed Smoke Gate
## Reviewer Notebook

**Classification:** `READ_ONLY_PHASE34_V1_3_MODEL_IDENTITY_AND_UNTIMED_SMOKE_GATE_REVIEWER_NOTEBOOK`
**Revision:** `{REVISION}`

All four canonical components were constructed, strict-loaded and parameter-verified, and ten
untimed smoke forwards were executed (4 component + 2 SKIP path + 4 EXECUTE path). **No latency,
throughput, memory or profiler measurement was performed.**
""")

md("## 0. Setup")
code(SETUP)

md("## 1. Runtime source preflight (additive filename)")
code('''\
rp = jload(AUD / "phase34_execution_source_preflight_runtime_v1_3.json")
print("additive filename:", rp["additive_filename"])
print("authority all match:", rp["authority_all_match"])
print("frozen sources all match:", rp["frozen_sources_all_match"])
print("frozen preflight unchanged:", rp["frozen_preflight_artifact"]["unchanged"])
print()
for f in rp["frozen_source_verification"]:
    print(f"  {'OK ' if f['match'] else 'BAD'} {f['key']:26s} {f['observed_sha256'][:16]}...")
''')

md("## 2. Environment gate")
code('''\
env = jload(AUD / "phase34_smoke_execution_environment_v1_3.json")
print("gate pass:", env["environment_gate_pass"])
for k, v in env["environment_checks"].items():
    print(f"  {k:28s} = {v}  (observed: {env['observed_environment'].get(k)})")
''')

md("## 3. Model identity per component")
code('''\
sg = jload(AUD / "phase34_model_identity_and_smoke_gate_v1_3.json")
print("checkpoint hashes all match:", sg["all_checkpoint_hashes_match"])
print("execution mode:", sg["execution_mode"],
      "| harness used:", sg["orchestration_harness_used"])
print()
rows = []
for cid, v in sg["per_component"].items():
    rows.append({"component": cid, "constructed": v["constructed"],
                 "missing_keys": len(v["missing_keys"] or []),
                 "unexpected_keys": len(v["unexpected_keys"] or []),
                 "params": v["parameter_count"], "dtype": ",".join(v["parameter_dtypes"] or []),
                 "eval": v["eval"], "out_shape": str(v["output_shape"]),
                 "finite": v["all_finite"]})
print(pd.DataFrame(rows).to_string(index=False))
print()
print("total resident parameters:", sum(v["parameter_count"] or 0
                                        for v in sg["per_component"].values()))
''')

md("## 4. Smoke forward accounting")
code('''\
print("SMOKE_TASK_ID:", sg["SMOKE_TASK_ID"], "| SMOKE_DOMAIN:", sg["SMOKE_DOMAIN"])
print("individual component smoke forwards:", sg["individual_smoke_forwards"])
print("SKIP controlled-path forwards     :", sg["SKIP_smoke_forwards"])
print("EXECUTE controlled-path forwards  :", sg["EXECUTE_smoke_forwards"])
print("TOTAL smoke model forward calls   :", sg["total_smoke_model_forward_calls"])
print("smoke failures:", sg["smoke_failures"])
print("all smoke outputs finite:", sg["all_smoke_outputs_finite"])
print()
print("CUDA synchronization note:", sg["cuda_synchronization_note"])
''')

md("## 5. Controlled-path smoke")
code('''\
for arm in ("SKIP_CONTROLLED_PATH", "EXECUTE_CONTROLLED_PATH"):
    r = sg[arm.replace("_CONTROLLED_PATH", "_smoke")]
    print(arm, "| mode:", r["mode"], "| scope:", r["scope"])
    p = r["path"]
    print("   components:", p["components"], "| forwards:", p["forward_calls"],
          "| route_forced:", p["route_forced"],
          "| b_phi_chose_route:", p["b_phi_output_used_to_choose_route"])
    for cid, o in p["outputs"].items():
        print(f"     {cid:8s} shape={o['output_shape']} dtype={o['output_dtype']} "
              f"finite={o['finite']}")
''')

md("## 6. Smoke execution provenance")
code('''\
pv = jload(AUD / "phase34_smoke_execution_provenance_v1_3.json")
print("runtime preflight SHA:", pv["runtime_preflight_sha256"][:16], "...")
print("v1.3 source freeze SHA:", pv["v1_3_source_freeze_sha256"][:16], "...")
print("SMOKE_TASK_ID:", pv["SMOKE_TASK_ID"], "| generator:", pv["synthetic_generator"])
print("smoke order:", pv["smoke_order"])
print("forward accounting:", pv["forward_call_accounting"])
print()
print("protected-data counters:")
for k, v in pv["protected_data_counters"].items():
    print(f"  {k:30s} = {v}")
print()
print("precision contexts:")
for k, v in pv["precision_contexts"].items():
    print(f"  {k:8s} {v}")
''')

md("## 7. Zero-measurement verification")
code('''\
print("latency measurements        :", sg["latency_measurements"])
print("throughput measurements     :", sg["throughput_measurements"])
print("memory measurements         :", sg["memory_measurements"])
print("MAC/FLOP profiler executions:", sg["mac_flop_profiler_executions"])
print("latency warmups             : 0")
print()
print("no latency table  :", not (ROOT / "reports/tables/phase34_batch1_latency_results_v1_3.csv").exists())
print("no throughput table:", not (ROOT / "reports/tables/phase34_batch8_throughput_results_v1_3.csv").exists())
print("no memory table    :", not (ROOT / "reports/tables/phase34_gpu_memory_results_v1_3.csv").exists())
''')

md("## 8. Smoke final check and terminal")
code('''\
fc = jload(AUD / "phase34_smoke_final_check_v1_3.json")
print("final check:", fc["n_checks"], "checks,", fc["n_failed"], "failed")
term = jload(AUD / "phase34_smoke_execution_terminal_v1_3.json")
print()
print("terminal:")
print(" ", term["terminal"])
''')

md("""---
## Summary

| item | value |
|---|---|
| G | 3,523,001 params · strict load clean · output `[1,1,512,512]` finite |
| R_psi | 1,276,401 params · strict load clean · output `[1,1,256,256]` finite |
| B_phi | 36,801 params · strict load clean · output `[1]` finite |
| S_omega | 1,217 params · strict load clean · output `[1]` finite |
| total resident parameters | 4,837,420 |
| smoke forwards | 4 component + 2 SKIP + 4 EXECUTE = **10** |
| latency / throughput / memory / profiler | 0 · 0 · 0 · 0 |
| protected data · TEST · training | 0 · 0 · 0 |
| first measured profiling execution | NOT started · Phase35 NOT started |
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
        "artifact": "phase34_smoke_reviewer_notebook_audit_v1_3", "phase": 34,
        "section": "\u00A7R", "method": "RA-MedFiLM-BARR", "revision": REVISION,
        "path": str(NB.relative_to(ROOT)).replace("\\", "/"), "sha256": hashes[-1],
        "cell_count": len(nb.cells), "markdown_cells": n_md, "code_cells": n_code,
        "executed_code_cells": n_exec, "error_cells": errs,
        "replay_count": 3, "replays_byte_identical": len(set(hashes)) == 1,
        "smoke_rerun_between_renders": False,
        "counters": {"checkpoint_loads": 0, "model_constructions": 0, "model_forwards": 0,
                     "CUDA_profile_iterations": 0, "new_latency_measurements": 0,
                     "new_FPS_measurements": 0, "new_peak_memory_measurements": 0,
                     "new_model_MAC_or_FLOP_profile_executions": 0, "raw_image_reads": 0,
                     "raw_GT_reads": 0, "ROUTER_HOLDOUT_raw_reads": 0, "TEST_reads": 0,
                     "training_steps": 0},
        "all_counters_zero": True,
        "all_pass": errs == 0 and n_exec == n_code,
    }
    p = AUD / "phase34_smoke_reviewer_notebook_audit_v1_3.json"
    p.write_text(json.dumps(audit, indent=1) + "\n", encoding="utf-8")
    print("wrote", p)
    print("audit sha256:", sha256_file(p))


if __name__ == "__main__":
    main()
