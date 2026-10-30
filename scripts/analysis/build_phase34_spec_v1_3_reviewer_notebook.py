#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build AND execute the Phase34 v1.3 worker-import / smoke-mode amendment reviewer notebook.

Classification: READ_ONLY_PHASE34_V1_3_WORKER_IMPORT_AND_SMOKE_MODE_REVIEWER_NOTEBOOK

Renders v1.3 contracts and static audits ONLY. Does NOT construct models, deserialize
checkpoints, run forwards, run CUDA timing, measure memory, access protected data, open TEST
or train.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/build_phase34_spec_v1_3_reviewer_notebook.py
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
      "phase34_efficiency_profiling_spec_v1_3_review.ipynb")
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


print("Phase34 v1.3 worker-import + untimed smoke-mode amendment review")
print("READ-ONLY. No model construction, no checkpoint deserialization, no forward, no timing,")
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


md(f"""# Phase 34 — v1.3 Worker Import & Untimed Smoke-Mode Amendment
## Reviewer Notebook

**Classification:** `READ_ONLY_PHASE34_V1_3_WORKER_IMPORT_AND_SMOKE_MODE_REVIEWER_NOTEBOOK`
**Revision:** `{REVISION}`

Disclosure chain: v1.0 specification only · v1.1 semantics repair · v1.1 execution BLOCKED before
model construction · v1.2 executable-harness/task-binding amendment · v1.2 execution BLOCKED at the
smoke gate after B_phi/S_omega construction, before any forward or timing · **v1.3** repairs the
repository import path and adds executable untimed smoke modes. No timing result has ever existed.
""")

md("## 0. Setup")
code(SETUP)

md("## 1. v1.2 blocked smoke evidence (preserved)")
code('''\
bt = jload(AUD / "phase34_execution_blocked_terminal_v1_2.json")
print("historical terminal:", bt["terminal"])
print("status:", bt["status"])
sm = jload(AUD / "phase34_model_identity_and_smoke_gate_v1_2.json")
print()
print("smoke gate pass:", sm["smoke_gate_pass"])
print("components constructed:", sm["components_constructed"])
print("components not constructed:", sm["components_not_constructed"])
print("smoke forwards executed:", sm["smoke_forwards_executed"])
print("measurement iterations:", sm["measurement_iterations_completed"])
for cid, v in sm["per_component"].items():
    print(f"  {cid:8s} constructed={v['constructed']} param_count={v['parameter_count']} "
          f"failure={v.get('failure')}")
''')

md("## 2. Defect record and terminal-label clarification")
code('''\
dr = jload(AUD / "phase34_v1_2_smoke_gate_defect_record.json")
print("classification:", dr["classification"])
print("root cause 1:", dr["root_cause_1"])
print("root cause 2:", dr["root_cause_2"])
print("affected:", dr["affected_components"], "| unaffected:", dr["unaffected_successfully_constructed_components"])
print()
print("precise state clarification:", dr["precise_state_clarification"])
print("historical terminal rewritten:", dr["historical_terminal_rewritten"])
print("clarification is reporting-label only:", dr["clarification_is_reporting_label_only"])
''')

md("## 3. Preflight-output regeneration provenance")
code('''\
pv = jload(AUD / "phase34_v1_2_preflight_output_regeneration_provenance.json")
print("frozen original SHA:", pv["frozen_original_preflight_output_sha"])
print("regenerated SHA   :", pv["execution_time_regenerated_sha"])
print("reason:", pv["reason"])
print("semantic checks:", pv["semantic_checks"])
print("load-bearing source hashes changed:", pv["load_bearing_source_hashes_changed"])
print("classification:", pv["classification"])
print()
print("policy from v1.3 onward:", pv["policy_from_v1_3_onward"])
''')

md("## 4. Repository-root import contract")
code('''\
ic = jload(AUD / "phase34_worker_import_root_contract_v1_3.json")
for k in ["repository_root_resolution", "repo_root_parent_depth", "cwd_independent",
          "external_PYTHONPATH_required", "depends_on_current_working_directory",
          "depends_on_manual_cd", "depends_on_machine_specific_absolute_path",
          "inserts_only_scripts_analysis_as_root_for_src",
          "root_insert_line_worker", "first_src_import_line_worker"]:
    print(f"  {k:52s} = {ic[k]}")
print()
print("implementation:", ic["implementation"])
''')

md("## 5. Importability probe")
code('''\
ip = jload(AUD / "phase34_v1_3_importability_probe.json")
print("G class import      :", ip["G_class_import"])
print("R_psi class import  :", ip["R_psi_class_import"])
print("B_phi authority     :", ip["B_phi_authority_import"])
print("S_omega authority   :", ip["S_omega_authority_import"])
print("repo-root cwd pass  :", ip["repo_root_cwd_pass"])
print("non-repo cwd pass   :", ip["non_repo_cwd_pass"])
print("cwd independent     :", ip["cwd_independent"])
print()
print("model constructions:", ip["model_constructions"],
      "| checkpoint deserializations:", ip["checkpoint_deserializations"],
      "| forwards:", ip["forwards"])
''')

md("## 6. v1.3 static source preflight (AST only)")
code('''\
pf = jload(AUD / "phase34_execution_source_preflight_v1_3.json")
print("inspection:", pf["method_of_inspection"])
print("immutable preflight output:", pf["immutable_preflight_output"])
print("execution-time reruns must use:", pf["execution_time_reruns_must_use"])
print("checks:", pf["n_checks"], "| failed:", pf["n_failed"],
      "| pass:", pf["static_preflight_pass"])
print()
for k, v in pf["checks"].items():
    print(f"  {'PASS' if v else 'FAIL'}  {k}")
''')

md("## 7. Smoke-mode source contract")
code('''\
sm = jload(AUD / "phase34_model_identity_and_smoke_gate_v1_2.json")
print("v1.2 smoke mode existed:", False)
print("v1.3 smoke modes:", ["smoke", "identity", "latency", "throughput", "memory"])
print("smoke classification: UNTIMED_INTERFACE_AND_IDENTITY_VALIDATION")
print("SMOKE_TASK_ID = 0 (ISIC), no scientific weighting interpretation")
print()
print("component smoke order:", ["G", "R_psi", "B_phi", "S_omega"])
print("SKIP controlled smoke: G + B_phi (route forced, B_phi output does not choose route)")
print("EXECUTE controlled smoke: G + B_phi + R_psi + S_omega")
''')

md("## 8. v1.3 source freeze")
code('''\
sf = jload(AUD / "phase34_preexecution_source_freeze_v1_3.json")
for k, v in sf["frozen_sources"].items():
    print(f"  {v['sha256'][:16]}...  {k:22s} {v['path']}")
print()
print("v1.2 source freeze preserved:", sf["v1_2_source_freeze_preserved"])
print("v1.2 blocked attempt preserved:", sf["v1_2_blocked_attempt_preserved"])
print("v1.3 supersedes v1.2:", sf["v1_3_supersedes_v1_2_for_future_execution"])
print("no v1.2 timing measurement exists:", sf["no_v1_2_timing_measurement_exists"])
''')

md("## 9. v1.3 execution eligibility")
code('''\
ea = jload(AUD / "phase34_execution_eligibility_adjudication_v1_3.json")
for k, v in ea["families"].items():
    print(f"  {k:52s} = {str(v['value']):5s}")
print()
print("first measured execution started:", ea["first_measured_execution_started"])
''')

md("## 10. Zero-measurement counters")
code('''\
ne = jload(AUD / "phase34_v1_3_no_execution_audit.json")
for k, v in ne["counters"].items():
    print(f"  {k:50s} = {v}")
print("all zero:", ne["all_zero"])
print("module/class import probes (separately counted):", ne["module_class_import_probes"])
assert ne["all_zero"]
''')

md("## 11. v1.3 final check and terminal")
code('''\
fc = jload(AUD / "phase34_specification_final_check_v1_3.json")
print("final check:", fc["n_checks"], "checks,", fc["n_failed"], "failed")
term = jload(AUD / "phase34_specification_terminal_v1_3.json")
print()
print("terminal:")
print(" ", term["terminal"])
''')

md("""---
## Summary

| item | value |
|---|---|
| v1.2 smoke failure | G, R_psi `No module named 'src'`; B_phi/S_omega loaded |
| v1.2 timing results | none (never existed) |
| root resolution | `Path(__file__).resolve().parents[2]` (FILE_RELATIVE, cwd independent) |
| import probe | G/R_psi/B_phi/S_omega PASS from repo root **and** non-repo cwd |
| smoke mode | `--mode smoke` = UNTIMED_INTERFACE_AND_IDENTITY_VALIDATION |
| smoke task identity | `SMOKE_TASK_ID = 0` (ISIC), no weighting meaning |
| measured schedules | unchanged (batch1 0/1/2/3; batch8 `[0,1,2,3,0,1,2,3]`) |
| model constructions · deserializations · forwards · timing · memory | 0 · 0 · 0 · 0 · 0 |
| first measured execution | NOT started · Phase35 NOT started · TEST locked |
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
        "artifact": "phase34_spec_v1_3_reviewer_notebook_audit", "phase": 34,
        "section": "\u00A7T", "method": "RA-MedFiLM-BARR", "revision": REVISION,
        "path": str(NB.relative_to(ROOT)).replace("\\", "/"), "sha256": hashes[-1],
        "cell_count": len(nb.cells), "markdown_cells": n_md, "code_cells": n_code,
        "executed_code_cells": n_exec, "error_cells": errs,
        "replay_count": 3, "replays_byte_identical": len(set(hashes)) == 1,
        "counters": {"model_constructions": 0, "model_loads": 0, "model_forwards": 0,
                     "smoke_forwards": 0, "CUDA_profile_iterations": 0,
                     "new_latency_measurements": 0, "new_FPS_measurements": 0,
                     "new_peak_memory_measurements": 0,
                     "new_model_MAC_or_FLOP_profile_executions": 0, "raw_image_reads": 0,
                     "raw_GT_reads": 0, "ROUTER_HOLDOUT_raw_reads": 0, "TEST_reads": 0,
                     "training_steps": 0},
        "all_counters_zero": True,
        "all_pass": errs == 0 and n_exec == n_code,
    }
    p = AUD / "phase34_spec_v1_3_reviewer_notebook_audit.json"
    p.write_text(json.dumps(audit, indent=1) + "\n", encoding="utf-8")
    print("wrote", p)
    print("audit sha256:", sha256_file(p))


if __name__ == "__main__":
    main()
