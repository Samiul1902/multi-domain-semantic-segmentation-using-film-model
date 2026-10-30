#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build AND execute the Phase34 v1.4 latency-repair specification reviewer notebook.

Classification: READ_ONLY_PHASE34_LATENCY_REPAIR_SPEC_V1_4_REVIEWER_NOTEBOOK

Reads ONLY repair-spec artifacts. Never executes models or timing.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/build_phase34_latency_repair_notebook_v1_4.py
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
      "phase34_latency_repair_spec_v1_4_review.ipynb")
KERNEL = "jup-venv"
REVISION = "ra_medfilm_barr_phase34_efficiency_profiling_v1_4"

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
    with pd.option_context("display.max_columns", None, "display.width", 240):
        print(df.to_string(index=False))
    return df


print("Phase34 v1.4 latency-granularity + alias-deduplication REPAIR SPEC review")
print("READ-ONLY. No model construction, no forward, no timing, no protected data, no TEST.")
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


md(f"""# Phase 34 — v1.4 Latency-Granularity + Alias-Deduplication Repair
## Specification Reviewer Notebook

**Classification:** `READ_ONLY_PHASE34_LATENCY_REPAIR_SPEC_V1_4_REVIEWER_NOTEBOOK`
**Revision:** `{REVISION}`

The v1.3 batch-1 latency implementation timed one 200-iteration block per CUDA-event pair and
mislabeled the five block totals as 1000 per-iteration observations. Throughput, memory, static
resource and analytical MAC evidence remain **valid and preserved**.
""")

md("## 0. Setup")
code(SETUP)

md("## 1. Defect record")
code('''\
dr = jload(AUD / "phase34_v1_3_latency_granularity_and_alias_defect_record.json")
print("classification:", dr["classification"])
d1 = dr["DEFECT_1"]
print()
print("DEFECT 1:", d1["code"])
print("  recorded observations are:", d1["recorded_latency_observations_are"])
print("  block size:", d1["block_size"])
print("  reported unit semantics:", d1["reported_latency_unit_semantics"])
print("  NOT:", d1["not"])
print()
print("  observed evidence:", json.dumps(d1["observed_evidence"], indent=4))
d2 = dr["DEFECT_2"]
print()
print("DEFECT 2:", d2["code"])
print("  aliases:", d2["aliases"])
print("  deleted:", d2["deleted"], "| classification:", d2["classification"])
''')

md("## 2. Source-level root cause")
code('''\
rc = jload(AUD / "phase34_v1_3_latency_source_root_cause.json")
print("source:", rc["source"], "| SHA:", rc["source_sha256"][:16], "...")
print("function:", rc["function"], "lines", rc["line_span"])
print("timing captures:", rc["timing_captures"])
print("not:", rc["not"])
print("conclusion:", rc["conclusion"])
print()
for e in rc["evidence_lines"]:
    print("  -", e)
''')

md("## 3. Validity partition")
code('''\
vp = jload(AUD / "phase34_v1_3_result_validity_partition.json")
for k, v in vp.items():
    if k in ("artifact", "phase", "section", "method", "revision", "generated_utc",
             "all_pass"):
        continue
    print(f"  {k:52s} = {v}")
''')

md("## 4. ÷200 block-mean salvage arithmetic")
code('''\
sv = tshow("phase34_v1_3_block_mean_latency_salvage.csv")
print()
print("note: this is a MEAN-ONLY derivation from equal-size block totals.")
print("It cannot reconstruct per-iteration std / p50 / p90 / p95 / p99 / min / max.")
''')

md("## 5. Salvaged conditional mean runtime")
code('''\
tshow("phase34_v1_3_conditional_runtime_mean_salvage.csv")
''')

md("## 6. v1.4 six-arm latency registry")
code('''\
reg = tshow("phase34_latency_arm_registry_v1_4.csv")
print()
print("physical worker runs:", int(reg["physical_worker_runs"].sum()), "(expected 6)")
''')

md("## 7. v1.4 observation-unit contract")
code('''\
print("estimand            : PER_FORWARD_BATCH1_MODEL_COMPUTE_PATH_LATENCY_MS")
print("observation unit    : ONE model/path forward at batch size 1")
print("observations per arm: 1000 (5 blocks x 200)")
print("warmup              : 50 (same 0/1/2/3 task cycle)")
print("mean                : np.mean(values, dtype=float64)")
print("std                 : np.std(values, ddof=1, dtype=float64)")
print("percentiles         : np.quantile(values, [0.50,0.90,0.95,0.99], method='linear')")
print("min/max             : np.min / np.max")
print("no rounding, no outlier dropping, no winsorization, no retry on observed timing")
print()
print("raw observation artifact: 6 arms x 1000 = 6000 rows")
''')

md("## 8. v1.4 static preflight")
code('''\
pf = jload(AUD / "phase34_latency_preflight_v1_4.json")
print("inspection:", pf["method_of_inspection"])
print("checks:", pf["n_checks"], "| failed:", pf["n_failed"],
      "| pass:", pf["static_preflight_pass"])
print()
for k, v in pf["checks"].items():
    print(f"  {'PASS' if v else 'FAIL'}  {k}")
''')

md("## 9. v1.4 source freeze")
code('''\
sf = jload(AUD / "phase34_preexecution_source_freeze_v1_4.json")
for k, v in sf["frozen_sources"].items():
    print(f"  {v['sha256'][:16]}...  {k:30s} {v['path']}")
print()
print("v1.3 measured attempt preserved:", sf["v1_3_measured_attempt_preserved"])
print("v1.3 latency result not canonicalized:", sf["v1_3_latency_result_not_canonicalized"])
print("v1.3 throughput preserved valid:", sf["v1_3_throughput_preserved_valid"])
print("v1.3 memory preserved valid:", sf["v1_3_memory_preserved_valid"])
print("v1.3 static resources preserved valid:", sf["v1_3_static_resources_preserved_valid"])
print("v1.3 analytical MAC preserved valid:", sf["v1_3_analytical_MAC_preserved_valid"])
''')

md("## 10. Execution eligibility and no-execution audit")
code('''\
el = jload(AUD / "phase34_latency_execution_eligibility_v1_4.json")
print("latency rerun authorized:", el["latency_rerun_authorized"])
print("reason:", el["reason"])
print("throughput/memory/static/MAC rerun:",
      el["throughput_rerun_authorized"], el["memory_rerun_authorized"],
      el["static_resource_rerun_authorized"], el["analytical_MAC_rerun_authorized"])
print("alias physical rerun:", el["alias_physical_rerun_authorized"])
print()
ne = jload(AUD / "phase34_v1_4_no_execution_audit.json")
for k, v in ne["counters"].items():
    print(f"  {k:32s} = {v}")
print("all zero:", ne["all_zero"])
assert ne["all_zero"]
''')

md("## 11. Repair final check and terminal")
code('''\
fc = jload(AUD / "phase34_latency_repair_final_check_v1_4.json")
print("final check:", fc["n_checks"], "checks,", fc["n_failed"], "failed")
term = jload(AUD / "phase34_latency_repair_terminal_v1_4.json")
print()
print("terminal:")
print(" ", term["terminal"])
''')

md("""---
## Summary

| item | value |
|---|---|
| v1.3 latency defect | 200-iteration block totals mislabeled as per-iteration ms |
| source proof | one CUDA-event pair per 200-iteration block (`time_latency` L285–L295) |
| v1.3 latency as per-forward | INVALID · std/p50/p90/p95/p99/min/max INVALID |
| v1.3 throughput / memory / static / MAC | **VALID and preserved** |
| mean-only salvage | reported block total ÷ 200 |
| v1.4 canonical arms | 6 (aliases not physically executed) |
| v1.4 observations | 1000 per-forward per arm · 6000 raw rows |
| v1.4 statistics | mean · std ddof=1 · linear quantiles · min/max |
| latency re-execution | ELIGIBLE, NOT started |
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
        "artifact": "phase34_latency_repair_notebook_audit_v1_4", "phase": 34,
        "section": "\u00A7U", "method": "RA-MedFiLM-BARR", "revision": REVISION,
        "path": str(NB.relative_to(ROOT)).replace("\\", "/"), "sha256": hashes[-1],
        "cell_count": len(nb.cells), "markdown_cells": n_md, "code_cells": n_code,
        "executed_code_cells": n_exec, "error_cells": errs,
        "replay_count": 3, "replays_byte_identical": len(set(hashes)) == 1,
        "counters": {"model_constructions": 0, "checkpoint_loads": 0, "model_forwards": 0,
                     "latency_measurements": 0, "throughput_measurements": 0,
                     "memory_measurements": 0, "MAC_or_FLOP_profile_executions": 0,
                     "raw_image_reads": 0, "raw_GT_reads": 0, "ROUTER_HOLDOUT_raw_reads": 0,
                     "TEST_reads": 0, "training_steps": 0},
        "all_counters_zero": True,
        "all_pass": errs == 0 and n_exec == n_code,
    }
    p = AUD / "phase34_latency_repair_notebook_audit_v1_4.json"
    p.write_text(json.dumps(audit, indent=1) + "\n", encoding="utf-8")
    print("wrote", p)
    print("audit sha256:", sha256_file(p))


if __name__ == "__main__":
    main()
