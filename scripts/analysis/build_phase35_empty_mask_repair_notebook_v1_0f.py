#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build AND execute the Phase35 v1.0f empty-mask actual-logits repair reviewer notebook (read-only).

Classification: READ_ONLY_PHASE35_V1_0F_EMPTY_MASK_ACTUAL_LOGITS_REPAIR_REVIEWER_NOTEBOOK
Reads only the produced v1.0f governance JSONs (defect, reconciliation, semantic diff, source
freeze, eligibility, unit-test artifact, static preflight, no-model-execution audit) and the
produced v1.0e block artifacts. Constructs no model, deserializes no checkpoint, runs no forward
or autograd, reads no medical data and no real p_global.

For THIS new notebook the physical representation is reported truthfully: it is rendered/executed
here, so its representation is EXECUTED_WITH_PERSISTED_OUTPUTS (it is NOT a stripped clean source).
Determinism = the notebook source is rendered 3x; the smoke is NOT run.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/build_phase35_empty_mask_repair_notebook_v1_0f.py
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
      "phase35_empty_mask_actual_logits_repair_v1_0f_review.ipynb")
KERNEL = "jup-venv"
REVISION = "ra_medfilm_barr_phase35_interpretability_v1_0f"

SETUP = '''\
import hashlib
import json
from pathlib import Path
ROOT = Path(r"D://Softfors//jup"); AUD = ROOT / "reports" / "audits"
def jload(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))
def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()
defect = jload(AUD / "phase35_v1_0e_actual_logits_empty_mask_defect_v1_0f.json")
recon  = jload(AUD / "phase35_v1_0e_blocked_smoke_notebook_metadata_reconciliation_v1_0f.json")
diff   = jload(AUD / "phase35_v1_0e_to_v1_0f_semantic_diff.json")
freeze = jload(AUD / "phase35_preexecution_source_freeze_v1_0f.json")
elig   = jload(AUD / "phase35_synthetic_smoke_eligibility_v1_0f.json")
unit   = jload(AUD / "phase35_empty_mask_actual_logits_unit_v1_0f.json")
pf     = jload(AUD / "phase35_execution_source_static_preflight_v1_0f.json")
nmea   = jload(AUD / "phase35_v1_0f_no_model_execution_audit.json")
block  = jload(AUD / "phase35_v1_0e_empty_mask_observability_block.json")
print("Phase35 v1.0f actual-logits empty-mask observability repair review (READ-ONLY)")
print("This notebook READS frozen v1.0f governance artifacts only; it does NOT run any model.")
print("No model construction, no checkpoint deserialization, no forward, no autograd, no Grad-CAM,")
print("no router attribution, no images, no real p_global, no VAL808 cache, no HOLDOUT/TEST.")
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


md(f"""# Phase 35 v1.0f — Actual-Logits Empty-Mask Observability Repair
## Reviewer Notebook (read-only)

**Classification:** `READ_ONLY_PHASE35_V1_0F_EMPTY_MASK_ACTUAL_LOGITS_REPAIR_REVIEWER_NOTEBOOK`
**Revision:** `{REVISION}`

Additive source/governance repair of the SINGLE defect that correctly blocked the first v1.0e
synthetic smoke: the frozen v1.0e empty-mask check validated the full-field fallback against a
fabricated `torch.zeros` logits **surrogate**. v1.0f validates the fallback against the **ACTUAL
logits** produced by the SAME synthetic G forward, using the SAME rank-safe helper, under a fixed
`atol=1e-7, rtol=0` comparison — with **no** second forward and **no** second autograd.

**No model was constructed, no checkpoint was loaded, no forward/autograd/Grad-CAM ran, no gate was
set, no mode was invoked.** Only CPU-only, model-free unit tests and static analysis were performed.
""")

md("## 0. Setup")
code(SETUP)

md("## 1. The preserved v1.0e block (not rewritten)")
code('''\
print("determination:", block["determination"])
print("smoke_run:", block["judgement"]["smoke_run"])
print("patch_attempted:", block["judgement"]["patch_attempted"],
      "| retry_attempted:", block["judgement"]["retry_attempted"])
print("is_prospective_source_level_block:", block["judgement"]["is_prospective_source_level_block"])
print()
print("block terminal SHA:", sha(AUD / "phase35_synthetic_smoke_terminal_v1_0e.json"))
print("block record SHA :", sha(AUD / "phase35_v1_0e_empty_mask_observability_block.json"))
''')

md("## 2. Defect record (§B)")
code('''\
print("classification:", defect["classification"])
for k in ("scientific_specification_changed", "gradcam_mathematics_changed",
          "target_mask_source_changed", "target_threshold_changed",
          "empty_mask_mathematical_fallback_changed", "numerical_finite_guards_changed",
          "scientific_result_invalidated", "v1_0e_smoke_block_correct"):
    print(f"  {k:44s} = {defect[k]}")
print()
print("required_defect:", defect["required_defect"])
print("required_repair:", defect["required_repair"])
''')

md("## 3. Semantic diff (§K) — implementation only, no scientific change")
code('''\
print("only_implementation_change:", diff["only_implementation_change"])
print("predecessor:", diff["predecessor_revision"], diff["predecessor_source_sha256"][:16])
print("successor  :", diff["successor_source_sha256"][:16])
print()
for k in ("scientific_specification_changed", "target_scalar_changed",
          "empty_mask_mathematical_fallback_changed", "rank_contract_changed",
          "target_mask_authority_changed", "gradcam_layers_changed", "gradcam_alpha_changed",
          "cam_relu_changed", "upsampling_changed", "normalization_changed",
          "numerical_finite_guards_changed", "router_semantics_changed", "film_semantics_changed"):
    print(f"  {k:42s} = {diff[k]}")
''')

md("## 4. Model-free actual-logits unit tests (§L)")
code('''\
print("all_pass:", unit["all_pass"], "| n_tests:", unit["n_tests"],
      "| n_pass:", unit["n_pass"], "| n_fail:", unit["n_fail"])
print()
for name, r in unit["results"].items():
    print(f"  [{'PASS' if r.get('pass') else 'FAIL'}] {name}")
    if "helper_return" in r and "expected_full_plane_mean" in r:
        print(f"        helper_return={r['helper_return']} expected={r['expected_full_plane_mean']} "
              f"diff={r['difference']} comparison_pass={r['comparison_pass']}")
print()
print("model_free_import_audit:", json.dumps(unit["model_free_import_audit"], indent=1))
print("counters:", json.dumps(unit["counters"]))
''')

md("## 5. Static preflight (§M) — zero-surrogate reachability proof")
code('''\
print("static_source_preflight_pass:", pf["static_source_preflight_pass"])
print("TOTAL checks:", pf["total_n_checks"], "| failed:", pf["total_n_failed"])
print("predecessors preserved:", pf["n_predecessors_preserved"],
      "| all match:", pf["preservation_all_match"])
print()
print("originals  :", pf["original_n_checks"], "failed", pf["original_n_failed"])
print("cumulative :", pf["cumulative_n_checks"], "failed", pf["cumulative_n_failed"])
print("v1.0e guard:", pf["numerical_guard_n_checks"], "failed", pf["numerical_guard_n_failed"])
print("v1.0f logs :", pf["actual_logits_n_checks"], "failed", pf["actual_logits_n_failed"])
print()
print("zero_logit_surrogate_unreachable_from_v1_0f_smoke:",
      pf["zero_logit_surrogate_unreachable_from_v1_0f_smoke"])
print("actual_logits_check_reachable_from_v1_0f_smoke:",
      pf["actual_logits_check_reachable_from_v1_0f_smoke"])
print()
print("call_graph_reachability:")
for k, v in pf["call_graph_reachability"].items():
    print(f"  {k:58s} = {v}")
''')

md("## 6. Notebook-metadata reconciliation (§C) — truthful representation")
code('''\
print("classification:", recon["classification"])
print("historical_audit_field:", recon["historical_audit_field"])
print("historical_audit_field_matches_delivered_bytes:",
      recon["historical_audit_field_matches_delivered_bytes"])
print("observed_delivered_representation:", recon["observed_delivered_representation"])
print()
print("direct notebook byte inspection:", json.dumps(
    recon["direct_notebook_byte_inspection"], indent=1))
print("notebook_read_only:", recon["notebook_read_only"])
print("model_construction_from_notebook:", recon["model_construction_from_notebook"])
''')

md("## 7. Source freeze (§N)")
code('''\
print("v1_0e_block_preserved:", freeze["v1_0e_block_preserved"])
print("v1_0e_source_preserved:", freeze["v1_0e_source_preserved"])
print("notebook_metadata_discrepancy_disclosed:", freeze["notebook_metadata_discrepancy_disclosed"])
print("v1_0f_empty_mask_repair_complete:", freeze["v1_0f_empty_mask_repair_complete"])
print("future_smoke_must_use_exact_v1_0f_bytes:",
      freeze["future_smoke_must_use_exact_v1_0f_bytes"])
print("scientific_execution_started:", freeze["scientific_execution_started"])
print()
print("frozen sources:")
for k, v in freeze["frozen_sources"].items():
    print(f"  {k:42s} {v['sha256'][:16]}  {v['path']}")
''')

md("## 8. Smoke eligibility (§O)")
code('''\
print("static_preflight_pass:", elig["static_preflight_pass"])
print("actual_logits_unit_tests_pass:", elig["actual_logits_unit_tests_pass"])
print("v1_0f_synthetic_smoke_eligible:", elig["v1_0f_synthetic_smoke_eligible"])
print("v1_0f_synthetic_smoke_started:", elig["v1_0f_synthetic_smoke_started"])
print("scientific_gradcam_execution_eligible:", elig["scientific_gradcam_execution_eligible"])
print("first_phase35_scientific_execution_eligible:",
      elig["first_phase35_scientific_execution_eligible"])
print("reason:", elig["reason"])
''')

md("## 9. No-model-execution audit (§P)")
code('''\
for k, v in nmea.items():
    if isinstance(v, (int, bool)) or k in ("model_free_cpu_unit_tests_run", "allowed"):
        print(f"  {k:40s} = {v}")
''')

md("""---
## Summary

| item | value |
|---|---|
| v1.0e block | **PRESERVED** (`aff064e2…` / `eef4f2b9…`), not rewritten |
| defect | `empty_mask_helper_check_insession` used a zero-logit surrogate |
| repair | validate the empty-mask fallback with the **actual same-forward logits**, in-scope |
| comparison | `torch.isclose(..., atol=1e-7, rtol=0)` — frozen before the smoke |
| extra forward / autograd | 0 / 0 |
| zero-logit surrogate reachable from smoke | **False** |
| actual-logits check reachable from smoke | **True** |
| v1.0e 8-stage finite guards | **preserved verbatim** (reused from `V0E`) |
| G / B_phi direct `.grad` audit | **preserved verbatim** |
| scientific semantics | **unchanged** (implementation-only amendment) |
| router / FiLM semantics | **unchanged** |
| model-free unit tests | **7/7 pass** |
| static preflight | **112/112 pass**, 75 predecessors preserved |
| source freeze / eligibility | complete · smoke **ELIGIBLE, NOT STARTED** |
| scientific execution | **NOT** started · Phase36 NOT started · TEST locked |
| models / checkpoints / forwards / autograd / Grad-CAM | 0 · 0 · 0 · 0 · 0 |
| raw VAL · real p_global · GT · HOLDOUT · TEST | 0 · 0 · 0 · 0 · 0 |
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
    n_out = sum(1 for c in nb.cells if c.cell_type == "code" and c.get("outputs"))
    errs = sum(1 for c in nb.cells for o in c.get("outputs", [])
               if o.get("output_type") == "error")
    print("notebook:", NB)
    print("cells:", len(nb.cells), "| md:", n_md, "| code:", n_code, "| executed:", n_exec,
          "| output-bearing:", n_out)
    print("errors:", errs)
    print("3 replays byte-identical:", len(set(hashes)) == 1)
    print("notebook sha256:", hashes[-1])
    audit = {"artifact": "phase35_empty_mask_actual_logits_repair_reviewer_notebook_audit_v1_0f",
             "phase": 35, "section": "\u00A7Q", "method": "RA-MedFiLM-BARR", "revision": REVISION,
             "path": str(NB.relative_to(ROOT)).replace("\\", "/"), "sha256": hashes[-1],
             "notebook_representation": "EXECUTED_WITH_PERSISTED_OUTPUTS",
             "cell_count": len(nb.cells), "markdown_cells": n_md, "code_cells": n_code,
             "executed_code_cells": n_exec, "output_bearing_code_cells": n_out,
             "error_cells": errs, "replay_count": 3,
             "replays_byte_identical": len(set(hashes)) == 1,
             "model_run_between_renders": False,
             "notebook_read_only": True,
             "model_construction_from_notebook": False,
             "checkpoint_loading_from_notebook": False,
             "model_forward_from_notebook": False,
             "autograd_from_notebook": False,
             "protected_data_reads_from_notebook": False,
             "counters": {"model_constructions": 0, "checkpoint_deserializations": 0,
                          "model_forwards": 0, "model_autograd_calls": 0, "gradcam_executions": 0,
                          "router_attribution_executions": 0, "raw_image_reads": 0,
                          "real_persisted_p_global_reads": 0, "gt_reads": 0,
                          "router_holdout_reads": 0, "test_reads": 0, "training_steps": 0},
             "all_counters_zero": True, "all_pass": errs == 0 and n_exec == n_code}
    p = AUD / "phase35_empty_mask_actual_logits_repair_reviewer_notebook_audit_v1_0f.json"
    p.write_text(json.dumps(audit, indent=1) + "\n", encoding="utf-8")
    print("wrote", p)
    print("audit sha256:", sha256_file(p))


if __name__ == "__main__":
    main()
