#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build AND execute the Phase35 v1.0c smoke-amendment reviewer notebook (read-only).

Classification: READ_ONLY_PHASE35_V1_0C_SMOKE_AMENDMENT_REVIEWER_NOTEBOOK
Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/build_phase35_smoke_amendment_notebook_v1_0c.py
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
      "phase35_interpretability_smoke_amendment_v1_0c_review.ipynb")
KERNEL = "jup-venv"
REVISION = "ra_medfilm_barr_phase35_interpretability_v1_0c"

SETUP = '''\
import hashlib
import json
from pathlib import Path
ROOT = Path(r"D://Softfors//jup"); AUD = ROOT / "reports" / "audits"
def jload(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))
print("Phase35 v1.0c smoke-mode implementation amendment review (READ-ONLY)")
print("No model construction, no checkpoint deserialization, no forward, no autograd, no images,")
print("no gate environment variable set and no --mode invocation.")
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


md(f"""# Phase 35 v1.0c — Synthetic Smoke-Mode Implementation Amendment
## Reviewer Notebook (read-only)

**Classification:** `READ_ONLY_PHASE35_V1_0C_SMOKE_AMENDMENT_REVIEWER_NOTEBOOK`
**Revision:** `{REVISION}`

The v1.0b synthetic smoke was **correctly BLOCKED** because the frozen `--mode smoke` entry point
was a stub. This notebook reviews the additive v1.0c amendment that implements a **real** synthetic
smoke entry point for the canonical **G** and **B_phi** components, freezes the v1.0c source, and
discloses a newly discovered blocking defect in the frozen scientific Grad-CAM path.

**No scientific output exists and none is produced here.**
""")
md("## 0. Setup")
code(SETUP)

md("## 1. Defect record — what v1.0c repairs and what it discloses")
code('''\
d = jload(AUD / "phase35_v1_0b_smoke_stub_defect_record_v1_0c.json")
print("classification:", d["classification"])
print()
a = d["defect_A"]
print("DEFECT A:", a["id"])
print("  severity  :", a["severity"])
print("  component :", a["component"])
print("  disposition:", a["disposition"])
print("  repair    :", a["repair"][:120], "...")
print()
b = d["defect_B"]
print("DEFECT B:", b["id"])
print("  severity  :", b["severity"])
print("  repaired_in_v1_0c:", b["repaired_in_v1_0c"], "| frozen_v1_0b_modified:", b["frozen_v1_0b_modified"])
print("  summary   :", b["summary"])
print()
print("  evidence 1:", b["evidence_1_static_tensor_semantics_probe"][:150], "...")
print("  evidence 2:", b["evidence_2_persisted_artifact_rank"][:150], "...")
''')

md("## 2. Scientific-semantics diff (v1.0b → v1.0c)")
code('''\
df = jload(AUD / "phase35_v1_0b_to_v1_0c_scientific_semantics_diff.json")
print("verdict:", df["scientific_semantics_verdict"])
print("scientific_semantics_unchanged:", df["scientific_semantics_unchanged"])
print()
print("scientific modes bound verbatim from frozen v1.0b:")
for k, v in df["scientific_modes_bound_verbatim_from_frozen_v1_0b"].items():
    print(f"  {k:14s} redefined_in_v1_0c={not v}")
print()
print("scientific helpers redefined in v1.0c:", [k for k, v in
      df["scientific_helpers_not_redefined_in_v1_0c"].items() if not v] or "NONE")
print("smoke-only functions added by v1.0c:")
for k in df["smoke_only_functions_added_by_v1_0c"]:
    print("  ", k)
print()
print("functions whose semantics could have changed:", df["functions_whose_semantics_could_have_changed"])
print("thresholds changed by v1.0c:", df["thresholds"]["changed_by_v1_0c"])
print("gates:", df["gates"])
''')

md("## 3. Static source preflight (zero execution)")
code('''\
pf = jload(AUD / "phase35_execution_source_static_preflight_v1_0c.json")
print("effective execution source set:", pf["effective_execution_source_set"])
print("predecessors preserved:", pf["n_predecessors_preserved"],
      "| all match:", pf["preservation_all_match"])
print("original 54 checks:", pf["original_n_checks"], "| failed:", pf["original_n_failed"])
print("additional v1.0c checks:", pf["additional_n_checks"], "| failed:", pf["additional_n_failed"])
print("TOTAL:", pf["total_n_checks"], "checks,", pf["total_n_failed"], "failed")
print("static_source_preflight_pass:", pf["static_source_preflight_pass"])
print()
print("smoke mode AST node count:", pf["smoke_mode_node_count"], "(stub was a single return)")
print("no execution performed:", {k: pf[k] for k in
      ("model_constructed", "checkpoint_deserialized", "forward_executed", "backward_executed",
       "gradcam_executed", "router_attribution_executed", "gate_env_set", "mode_invoked")})
''')

md("## 4. v1.0c amendment checks (subset)")
code('''\
keys = ["v1_0b_smoke_stub_still_present_in_frozen_v1_0b", "v1_0c_supersedes_smoke_entrypoint_only",
        "scientific_modes_not_redefined_in_v1_0c", "smoke_gate_env_distinct_from_science_gate_env",
        "smoke_mode_is_not_a_stub", "smoke_constructs_G_and_B_phi",
        "smoke_runs_canonical_gradcam_path", "smoke_runs_canonical_router_gradient_x_input",
        "smoke_tests_zero_denominator_policy", "smoke_verifies_parameter_immutability",
        "smoke_uses_no_real_data_loader", "smoke_emits_no_scientific_output",
        "disclosed_defect_gradcam_mask_rank_incompatibility"]
for k in keys:
    print(f"  {k:56s} = {pf['additional_v1_0c_checks'][k]}")
''')

md("## 5. Source freeze")
code('''\
fz = jload(AUD / "phase35_preexecution_source_freeze_v1_0c.json")
for name, spec in fz["frozen_source_set"].items():
    print(f"  {name:34s} {spec['sha256']}")
    print(f"  {'':34s} {spec['path']}")
print()
print("static preflight:", fz["static_preflight"])
print("source_freeze_complete:", fz["source_freeze_complete"])
print("smoke_entry_point_is_stub:", fz["smoke_entry_point_is_stub"])
print("predecessor drift:", fz["predecessor_drift"])
''')

md("## 6. Synthetic smoke eligibility (re-execution NOT started)")
code('''\
el = jload(AUD / "phase35_synthetic_smoke_eligibility_v1_0c.json")
print("classification:", el["classification"])
print("not:", el["not"])
print("gate:", el["gate"])
print("reexecution eligible:", el["synthetic_smoke_reexecution_eligible"])
print("executed in v1.0c:", el["synthetic_smoke_executed_in_v1_0c"])
print()
print("smoke will exercise:")
for s in el["smoke_will_exercise"]:
    print("  -", s)
print()
print("expected counts:", json.dumps(el["expected_counts"], indent=1))
print()
print("disclosed condition:", json.dumps(el["disclosed_condition"], indent=1))
''')

md("## 7. No-execution audit")
code('''\
ne = jload(AUD / "phase35_v1_0c_no_execution_audit.json")
print("zero_execution_declaration:", ne["zero_execution_declaration"])
for k, v in ne["counters"].items():
    print(f"  {k:34s} = {v}")
print()
print("gate env checks:", ne["gate_env_checks"])
''')

md("## 8. Final check and terminal")
code('''\
fc = jload(AUD / "phase35_smoke_amendment_final_check_v1_0c.json")
print("final check:", fc["n_checks"], "checks,", fc["n_failed"], "failed")
print("defect A:", fc["defect_A"], "->", fc["defect_A_status"])
print("defect B:", fc["defect_B"], "->", fc["defect_B_status"])
print()
t = jload(AUD / "phase35_smoke_amendment_terminal_v1_0c.json")
print("terminal:"); print(" ", t["terminal"])
''')

md("""---
## Summary

| item | value |
|---|---|
| v1.0b blocked smoke | preserved byte-for-byte |
| real synthetic smoke entry point | **IMPLEMENTED** (`mode_smoke`, G + B_phi only) |
| smoke gate | `PHASE35_SMOKE_EXECUTE` (distinct from scientific `PHASE35_EXECUTE`) |
| scientific modes | **UNCHANGED** (bound verbatim to frozen v1.0b function objects) |
| static preflight | 94 checks · 0 failed · 22 predecessors byte-identical |
| smoke re-execution | **ELIGIBLE, NOT STARTED** |
| disclosed defect B | `PHASE35_V1_0B_GRADCAM_TARGET_MASK_RANK_INCOMPATIBILITY` — scientific Grad-CAM blocked pending v1.0d |
| model constructions · checkpoint loads · forwards · autograd | 0 · 0 · 0 · 0 |
| raw VAL · GT · ROUTER_HOLDOUT · TEST reads | 0 · 0 · 0 · 0 |
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
    audit = {"artifact": "phase35_smoke_amendment_reviewer_notebook_audit_v1_0c", "phase": 35,
             "section": "\u00A7Z", "method": "RA-MedFiLM-BARR", "revision": REVISION,
             "path": str(NB.relative_to(ROOT)).replace("\\", "/"), "sha256": hashes[-1],
             "cell_count": len(nb.cells), "markdown_cells": n_md, "code_cells": n_code,
             "executed_code_cells": n_exec, "error_cells": errs, "replay_count": 3,
             "replays_byte_identical": len(set(hashes)) == 1,
             "smoke_rerun_between_renders": False,
             "counters": {"model_constructions": 0, "checkpoint_deserializations": 0,
                          "model_forwards": 0, "autograd_calls": 0, "gradcam_calls": 0,
                          "router_attribution_calls": 0, "raw_image_reads": 0,
                          "persisted_val_probability_reads": 0, "raw_GT_reads": 0,
                          "ROUTER_HOLDOUT_raw_reads": 0, "TEST_reads": 0,
                          "gate_env_vars_set": 0, "mode_invocations": 0, "training_steps": 0},
             "all_counters_zero": True, "all_pass": errs == 0 and n_exec == n_code}
    p = AUD / "phase35_smoke_amendment_reviewer_notebook_audit_v1_0c.json"
    p.write_text(json.dumps(audit, indent=1) + "\n", encoding="utf-8")
    print("wrote", p)
    print("audit sha256:", sha256_file(p))


if __name__ == "__main__":
    main()
