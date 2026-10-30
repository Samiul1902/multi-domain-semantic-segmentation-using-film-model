#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build AND execute the Phase34 pre-execution specification reviewer notebook.

Classification: READ_ONLY_PHASE34_PRE_EXECUTION_EFFICIENCY_PROFILING_SPEC_REVIEWER_NOTEBOOK

The notebook renders Phase34 specification artifacts ONLY. It does NOT load models,
run forwards, run CUDA timing, profile memory, compute new model FLOPs/MACs, read raw
images/GT, open TEST or train.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/build_phase34_spec_reviewer_notebook.py
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
      "phase34_efficiency_profiling_spec_review.ipynb")
KERNEL = "jup-venv"
REVISION = "ra_medfilm_barr_phase34_efficiency_profiling_v1_0"

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
    with pd.option_context("display.max_columns", None, "display.width", 220):
        print(df.to_string(index=False))
    return df


print("Phase34 pre-execution efficiency-profiling SPECIFICATION reviewer notebook")
print("READ-ONLY. No model load, no forward, no CUDA timing, no memory profiling,")
print("no new FLOP/MAC profiler run, no raw image/GT access, no TEST, no training.")
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
## Pre-execution Specification Reviewer Notebook

**Classification:** `READ_ONLY_PHASE34_PRE_EXECUTION_EFFICIENCY_PROFILING_SPEC_REVIEWER_NOTEBOOK`
**Revision:** `{REVISION}`

This notebook reviews the **frozen Phase34 specification** before any measured
timing/memory/profiler execution. It performs **no** model execution and touches **no**
protected data. Every number shown is read from a frozen specification artifact.
""")

md("## 0. Setup")
code(SETUP)

md("## 1. Phase33 canonical closure binding")
code('''\
fc = jload(AUD / "phase33_final_closure.json")
fcc = jload(AUD / "phase33_final_closure_check.json")
ho = jload(AUD / "phase33_phase34_handoff.json")
print("Phase33 status:", fc["phase33_status"])
print("Phase33 terminal:")
print(" ", fc["terminal"])
print("closure check:", fcc["n_checks"], "checks,", fcc["n_failed"], "failed")
print("Phase34 eligibility:", ho["Phase34_eligibility"], "| started:", ho["Phase34_started"])
print("ROUTER_HOLDOUT:", ho["ROUTER_HOLDOUT"], "| TEST:", ho["TEST"])
assert fc["phase33_status"] == "COMPLETE_CANONICAL"
assert fcc["n_checks"] == 29 and fcc["n_failed"] == 0
assert ho["Phase34_eligibility"] == "ELIGIBLE_NOT_STARTED"
''')

md("## 2. Phase34 roadmap identity reconciliation")
code('''\
ri = jload(AUD / "phase34_roadmap_identity_reconciliation.json")
print("phase id:", ri["immutable_phase_id"])
print("canonical display title:", ri["canonical_display_title"])
print("alias / scope wording:", ri["alias_or_scope_wording"])
print("unresolved conflict:", ri["unresolved_conflict"],
      "| title resolution complete:", ri["title_resolution_complete"])
print()
for s in ri["sources_inspected"]:
    print(f"  {s['path']:58s} | {s['display_title']}")
''')

md("## 3. Historical compute provenance inventory")
code('''\
inv = tshow("phase34_historical_compute_provenance_inventory.csv")
print()
print("labels present:", sorted(set(inv["scientific_interpretation"])))
''')

md("## 4. Canonical component registry")
code('tshow("phase34_canonical_component_registry.csv")')

md("## 5. Profiling arm registry")
code('tshow("phase34_profiling_arm_registry.csv")')

md("## 6. MAC / FLOP reporting semantics")
code('''\
mf = jload(AUD / "phase34_mac_flop_reporting_contract.json")
print("primary metric:", mf["primary_structural_compute_metric"])
print("derived FLOPs convention:", mf["derived_flops_convention"],
      "->", mf["derived_flops_label"])
print("historical MAC values may be called FLOPs:", mf["historical_mac_values_may_be_called_flops"])
print("complete FLOP profiler available:", False)
print()
sem = jload(AUD / "phase34_historical_compute_semantics_contract.json")
print("ruling:", sem["ruling"])
print("must NOT be relabeled as:", sem["must_not_be_relabeled_as"])
print("counted ops:", sem["counted_operations"])
print("excluded ops:", sem["excluded_operations_confirmed_by_authority"])
''')

md("## 7. Hardware / software environment snapshot (pre-execution)")
code('''\
env = jload(AUD / "phase34_environment_snapshot_preexecution.json")["environment"]
for k in ["os", "python_version", "torch_version", "cuda_runtime", "cuda_driver_version",
          "cudnn_version", "cuda_available", "gpu_model", "gpu_compute_capability",
          "gpu_total_vram_bytes", "cpu_logical_cores", "system_ram_bytes",
          "torch_matmul_allow_tf32", "torch_cudnn_allow_tf32", "torch_cudnn_benchmark",
          "torch_deterministic_algorithms", "torch_profiler_available"]:
    print(f"  {k:34s} = {env[k]}")
print()
print("profiling packages:")
for k, v in env["profiling_packages"].items():
    print(f"  {k:10s} available={v['available']} version={v['version']}")
''')

md("## 8. Synthetic-input contract")
code('''\
si = jload(AUD / "phase34_synthetic_input_contract.json")
print("generator:", si["generator"], "| seed:", si["seed"], "| dtype:", si["dtype"])
for k, v in si["per_component"].items():
    print(f"  {k:8s} {v}")
print("values optimized for favorable runtime:", si["values_optimized_for_favorable_runtime"])
''')

md("## 9. Latency / throughput / memory / isolation / scope contracts")
code('''\
lat = jload(AUD / "phase34_latency_measurement_contract.json")
print("LATENCY: batch", lat["primary_batch_size"], "| warmup", lat["warmup_iterations"],
      "| blocks", lat["measurement_blocks"], "| iters/block", lat["measured_iterations_per_block"])
print("  timer:", lat["timer_implementation"][:90], "...")
print("  statistics:", lat["reported_statistics"])
thr = jload(AUD / "phase34_throughput_contract.json")
print("THROUGHPUT:", thr["definition"])
print("  fps from 1000/mean:", thr["fps_from_1000_over_mean_latency"])
mem = jload(AUD / "phase34_memory_measurement_contract.json")
print("MEMORY concepts:", len(mem["separate_concepts"]), "separate quantities")
iso = jload(AUD / "phase34_process_isolation_contract.json")
print("ISOLATION: fresh subprocess per arm:", iso["fresh_subprocess_per_measured_arm"],
      "| randomized:", iso["arm_order_randomized"])
sc = jload(AUD / "phase34_runtime_scope_contract.json")
print("SCOPE: PRIMARY", sc["PRIMARY"], "| cold start enabled:", sc["cold_start_enabled"])
bs = jload(AUD / "phase34_batch_size_contract.json")
print("BATCH: primary", bs["PRIMARY_LATENCY_BATCH_SIZE"],
      "| secondary", bs["SECONDARY_THROUGHPUT_BATCH_SIZE"], bs["SECONDARY_eligibility"])
''')

md("""## 10. Conditional-computation formula

`E[MAC] = MAC(G) + MAC(B_phi) + p_activate * (MAC(R_psi) + MAC(S_omega))`

The two EXECUTE states (`EXECUTE_THEN_ACCEPT`, `EXECUTE_THEN_REJECT`) have **identical**
compute per the frozen Phase26 state machine (refiner=1, s_omega=1 for both).""")
code('''\
ac = jload(AUD / "phase34_analytical_compute_contract.json")
print("label:", ac["label"])
print("component MACs:", ac["component_macs"])
print("formula:", ac["expected_conditional_mac_formula"])
print("p_activate (frozen Phase30):", ac["p_activate_from_frozen_phase30_frequencies"])
print("absolute expected MACs:", ac["absolute_expected_macs"])
print("global-only MACs:", ac["global_only_macs"])
print("always-refine MACs:", ac["always_refine_macs"])
print("ratio vs global-only:", ac["relative_expected_vs_global_only"])
print("ratio vs always-refine:", ac["relative_expected_vs_always_refine"])
print("analytical saving vs always-refine:", ac["absolute_analytical_saving_vs_always_refine_macs"],
      "MACs")
print()
print("NOTE:", ac["numeric_preview_note"])
''')

md("## 11. Conditional execution state contract (weighting source)")
code('''\
cs = jload(AUD / "phase34_conditional_execution_state_contract.json")
print("anchors verified:", cs["anchors_verified"], "| forced:", cs["anchors_forced"])
print("accept/reject identical compute:", cs["accept_reject_compute_identical"])
print("weighted estimate is literal holdout runtime:",
      cs["weighted_estimate_is_literal_holdout_runtime"])
print("Phase30 qualifier:", cs["phase30_qualifier"])
''')

md("## 12. Pre-execution source freeze")
code('''\
sf = jload(AUD / "phase34_preexecution_source_freeze.json")
for s in sf["frozen_sources"]:
    print(f"  {s['sha256'][:16]}...  {s['role']:52s} {s['path']}")
print("future execution must use exact frozen bytes:",
      sf["future_execution_must_use_exact_frozen_bytes"])
''')

md("## 13. Execution eligibility adjudication")
code('''\
ea = jload(AUD / "phase34_execution_eligibility_adjudication.json")
for k, v in ea["families"].items():
    print(f"  {k:56s} = {str(v['value']):5s}  ({v['basis']})")
''')

md("## 14. Zero-execution counters")
code('''\
ne = jload(AUD / "phase34_no_execution_audit.json")
for k, v in ne["counters"].items():
    print(f"  {k:42s} = {v}")
print("all zero:", ne["all_zero"])
print("Phase35 started:", ne["phase35_started"])
assert ne["all_zero"]
''')

md("## 15. Specification completeness and final check")
code('''\
comp = tshow("phase34_specification_completeness.csv")
print()
print("status counts:", comp["status"].value_counts().to_dict())
fc2 = jload(AUD / "phase34_specification_final_check.json")
print("final check:", fc2["n_checks"], "checks,", fc2["n_failed"], "failed")
term = jload(AUD / "phase34_specification_terminal.json")
print("terminal:")
print(" ", term["terminal"])
''')

md("""---
## Summary

| item | value |
|---|---|
| classification | `READ_ONLY_PHASE34_PRE_EXECUTION_EFFICIENCY_PROFILING_SPEC_REVIEWER_NOTEBOOK` |
| Phase33 closure | `COMPLETE_CANONICAL` (bound, unchanged) |
| canonical display title | `Computational Efficiency & Runtime Profiling` |
| alias scope wording | `Computational Efficiency & Conditional-Computation Profiling` |
| components | G · R_psi · B_phi · S_omega (+ normalizations, fusion) |
| MAC convention | analytical Conv/Linear lower bound; FLOPs = 2x MACs (derived, labelled) |
| primary / secondary batch | 1 / 8 |
| latency protocol | warmup 50, 5 blocks x 200 iters, CUDA Events synchronized |
| new FLOP/MAC profiler | INELIGIBLE (none installed) |
| model loads · forwards · timing · memory | 0 · 0 · 0 · 0 |
| TEST | `LOCKED_UNTIL_PHASE39` |
| Phase34 execution | NOT started |
| Phase35 | NOT started |
""")


def build():
    nb = {"cells": CELLS, "metadata": dict(_FIXED_META),
          "nbformat": 4, "nbformat_minor": 5}
    NB.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(nbformat.from_dict(nb), str(NB))
    return nbformat.read(str(NB), as_version=4)


def normalize(nb):
    """Deterministic serialization: stable cell ids, merged streams, no timestamps."""
    for i, c in enumerate(nb.cells):
        c["id"] = f"cell{i:03d}"
        md_ = c.setdefault("metadata", {})
        md_.pop("execution", None)
        outs = c.get("outputs", [])
        merged = []
        for o in outs:
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
    client = NotebookClient(nb, kernel_name=KERNEL, timeout=900,
                            allow_errors=False, record_timing=False)
    client.execute()
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
    nb = build()
    hashes = []
    for _ in range(3):
        nb = nbformat.read(str(NB), as_version=4)
        nb = execute(nb)
        hashes.append(sha256_file(NB))
    nb = nbformat.read(str(NB), as_version=4)
    n_md = sum(1 for c in nb.cells if c.cell_type == "markdown")
    n_code = sum(1 for c in nb.cells if c.cell_type == "code")
    n_exec = sum(1 for c in nb.cells if c.cell_type == "code"
                 and c.get("execution_count") is not None)
    errs = sum(1 for c in nb.cells for o in c.get("outputs", [])
               if o.get("output_type") == "error")
    exec_counts = [c["execution_count"] for c in nb.cells if c.cell_type == "code"]
    print("notebook:", NB)
    print("cells:", len(nb.cells), "| md:", n_md, "| code:", n_code, "| executed:", n_exec)
    print("errors:", errs)
    print("execution counts:", exec_counts)
    print("3 replays byte-identical:", len(set(hashes)) == 1, hashes)
    print("notebook sha256:", hashes[-1])

    audit = {
        "artifact": "phase34_spec_reviewer_notebook_audit", "phase": 34,
        "section": "\u00a7AC", "method": "RA-MedFiLM-BARR", "revision": REVISION,
        "path": str(NB.relative_to(ROOT)).replace("\\", "/"),
        "sha256": hashes[-1],
        "cell_count": len(nb.cells), "markdown_cells": n_md, "code_cells": n_code,
        "executed_code_cells": n_exec, "error_cells": errs,
        "execution_counts_monotonic": exec_counts == sorted(exec_counts),
        "replay_count": 3, "replays_byte_identical": len(set(hashes)) == 1,
        "replay_hashes": hashes,
        "counters": {"model_loads": 0, "model_forwards": 0, "CUDA_profile_iterations": 0,
                     "new_latency_measurements": 0, "new_FPS_measurements": 0,
                     "new_peak_memory_measurements": 0,
                     "new_model_MAC_or_FLOP_profile_executions": 0, "raw_image_reads": 0,
                     "raw_GT_reads": 0, "ROUTER_HOLDOUT_raw_reads": 0, "TEST_reads": 0,
                     "training_steps": 0},
        "all_counters_zero": True,
        "all_pass": errs == 0 and n_exec == n_code,
    }
    p = AUD / "phase34_spec_reviewer_notebook_audit.json"
    p.write_text(json.dumps(audit, indent=1) + "\n", encoding="utf-8")
    print("wrote", p)
    print("audit sha256:", sha256_file(p))


if __name__ == "__main__":
    main()
