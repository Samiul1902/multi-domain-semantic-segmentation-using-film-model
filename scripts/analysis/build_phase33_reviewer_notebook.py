#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build the Phase33 pre-analysis read-only reviewer notebook.

READ_ONLY_PHASE33_PRE_ANALYSIS_REVIEWER_NOTEBOOK.
Renders frozen Phase33 specification/provenance artifacts only.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/build_phase33_reviewer_notebook.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
NB = (ROOT / "notebooks" / "phasewise" / "phase_33_final_failure_analysis" /
      "phase33_failure_boundary_spec_review.ipynb")

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


print("Phase33 reviewer notebook - READ-ONLY PRE-ANALYSIS SPECIFICATION PACKAGING")
print("No failure analysis, no hard-case selection, no metric computation, no model, no raw read.")
'''

CELLS = []


def md(s):
    CELLS.append({"cell_type": "markdown", "metadata": {}, "source": s})


def code(s):
    CELLS.append({"cell_type": "code", "execution_count": None, "metadata": {},
                  "outputs": [], "source": s})


md("""# Phase 33 — Final System Failure & Boundary Error Analysis
## Pre-Analysis Specification Review

**Roadmap identity:** `FINAL SYSTEM FAILURE & BOUNDARY ERROR ANALYSIS`
**Revision:** `ra_medfilm_barr_phase33_failure_boundary_v1_0`
**Classification:** `READ_ONLY_PHASE33_PRE_ANALYSIS_REVIEWER_NOTEBOOK`

This notebook renders **frozen** Phase33 specification/provenance artifacts only. It does **not**
select hard cases, run failure analysis, compute metrics, open raw images/GT, load models, or run
inference.
""")

md("## 2. Setup")
code(SETUP)

md("## 3. Phase32 → Phase33 authority binding")
code('''\
b = jload(AUD / "phase33_entry_authority_binding.json")
print("Phase32 status:", b["phase32_status"])
print("Phase32 terminal:", b["phase32_terminal_token"])
print("Phase33 roadmap identity:", b["phase33_roadmap_identity"])
print("all bindings match:", b["all_bindings_match"])
for x in b["bindings"]:
    print(f"  {x['match']}  {x['path']}")
''')

md("## 4. Protected-population states")
code('''\
for k, v in b["protected_population_rules"].items():
    print(f"  {k}: {v}")
print()
print("MANDATORY Phase30 QUALIFIER:")
print(" ", "ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_SCIENTIFIC_SOURCE_FREEZE_DEVIATION")
''')

md("## 5. Candidate evidence inventory")
code('''\
inv = pd.read_csv(TAB / "phase33_candidate_evidence_inventory.csv")
print("candidates:", len(inv))
print(inv[["artifact_id", "path", "phase", "population", "n_if_known",
           "scientific_status", "candidate_Phase33_use"]].to_string(index=False))
''')

md("## 6. Population ownership")
code('''\
po = jload(AUD / "phase33_population_ownership_contract.json")
for p in po["populations"]:
    print(f"  {p['population']:36s} {p['classification']}")
print()
print("TEST classification:", po["TEST_classification"])
''')

md("## 7. Frozen-artifact schema registry")
code('''\
sch = pd.read_csv(TAB / "phase33_frozen_artifact_schema_registry.csv")
print(sch[["artifact", "column/key", "dtype", "GT-derived yes/no",
           "prediction-derived yes/no", "safe for Phase33 descriptive use yes/no"]].to_string(index=False))
s = jload(AUD / "phase33_schema_registry_summary.json")
print()
print("absent from frozen final-system tables:", s["absent_from_frozen_final_system_tables"])
''')

md("## 8. Historical Phase11 taxonomy provenance")
code('''\
h = jload(AUD / "phase33_phase11_failure_taxonomy_provenance.json")
print("Phase11 population:", h["phase11_authority"]["population"],
      "| n =", h["phase11_authority"]["n"])
print("Phase11 models:", h["phase11_authority"]["models"])
print("not the final system:", h["phase11_authority"]["not_the_final_system"])
print()
for c in h["concepts"]:
    print(f"  {c['classification']:60s} {c['concept']}")
''')

md("## 9. Phase33 failure taxonomy")
code('''\
tx = jload(AUD / "phase33_failure_taxonomy_contract.json")
for f in tx["families"]:
    print(f"  {f['family']:36s} evidence_sufficient={f['existing_evidence_sufficient']:32s} "
          f"derivation_authorized={f['derivation_authorized']}")
print()
print("INELIGIBLE families:", tx["ineligible_families"])
''')

md("## 10. Threshold provenance")
code('''\
tp = jload(AUD / "phase33_failure_threshold_provenance_contract.json")
for s in tp["strata"]:
    print(f"  {s['stratum']:36s} {s['classification']}")
print()
print("outcome-optimized threshold selected:", tp["outcome_optimized_threshold_selected"])
''')

md("## 11. Routing-failure contract")
code('''\
rc = jload(AUD / "phase33_router_failure_analysis_contract.json")
print("system is selective:", rc["system_is_selective"])
print("frozen benefit categories:", rc["frozen_benefit_categories"])
print()
for a in rc["analyses"]:
    print("  -", a)
''')

md("## 12. Boundary-metric provenance ruling")
code('''\
bm = jload(AUD / "phase33_boundary_metric_provenance_contract.json")
print("frozen final-system boundary metric present:", bm["frozen_final_system_boundary_metric_present"])
print("FINAL_SYSTEM_BOUNDARY_ERROR_NEW_COMPUTATION_ELIGIBLE:",
      bm["FINAL_SYSTEM_BOUNDARY_ERROR_NEW_COMPUTATION_ELIGIBLE"])
print("reason:", bm["reason"])
print("Phase11 boundary evidence:", bm["phase11_boundary_evidence_classification"])
print("ROUTER_HOLDOUT GT reopened for boundary:", bm["router_holdout_gt_reopened_for_boundary"])
''')

md("## 13. Component / object analysis ruling")
code('''\
cm = jload(AUD / "phase33_component_object_analysis_ruling.json")
print("frozen component information present:", cm["frozen_final_system_component_information_present"])
print("NEW_COMPONENT_ANALYSIS_ELIGIBLE:", cm["NEW_COMPONENT_ANALYSIS_ELIGIBLE"])
print("manufactured:", cm["manufactured"])
''')

md("## 14. Hard-case selection contract")
code('''\
hc = jload(AUD / "phase33_hard_case_selection_contract.json")
print("label:", hc["label"], "| not unbiased estimation:", hc["not_unbiased_performance_estimation"])
print("cases selected in this task:", hc["cases_selected_in_this_task"])
print("procedure:")
for k, v in hc["procedure"].items():
    print(f"  {k}: {v}")
''')

md("## 15. Qualitative evidence eligibility")
code('''\
qe = jload(AUD / "phase33_qualitative_evidence_contract.json")
print("QUALITATIVE_GALLERY_ELIGIBLE:", qe["QUALITATIVE_GALLERY_ELIGIBLE"])
print("raw image reread permitted:", qe["raw_image_reread_permitted"])
print("GT visualization permitted:", qe["gt_visualization_permitted"])
print("panels generated:", qe["qualitative_panels_generated"])
''')

md("## 16. Quantitative analysis contract")
code('''\
qa = jload(AUD / "phase33_quantitative_analysis_contract.json")
for a in qa["plan"]:
    print("  -", a)
print()
print("new significance test required:", qa["new_significance_test_required"])
''')

md("## 17. Analysis-tier registry")
code('''\
tr = pd.read_csv(TAB / "phase33_analysis_tier_registry.csv")
print(tr.to_string(index=False))
''')

md("## 18. Execution-eligibility matrix")
code('''\
ee = jload(AUD / "phase33_execution_eligibility_adjudication.json")
for k in ["table_only_execution_eligible", "derived_nonpixel_execution_eligible",
          "prediction_pixel_execution_eligible", "raw_image_execution_eligible",
          "raw_GT_execution_eligible", "qualitative_gallery_eligible",
          "boundary_metric_execution_eligible", "component_metric_execution_eligible",
          "model_rerun_eligible"]:
    print(f"  {k}: {ee[k]}")
''')

md("## 19. Zero-execution counters")
code('''\
ne = jload(AUD / "phase33_no_execution_audit.json")
for k in ["new_raw_image_reads", "new_raw_GT_reads", "ROUTER_HOLDOUT_raw_image_reads",
          "ROUTER_HOLDOUT_raw_GT_reads", "TEST_reads", "model_loads", "model_forwards",
          "prediction_generation", "training_steps", "new_Dice_computations",
          "new_IoU_computations", "new_HD95_computations", "new_component_computations",
          "hard_cases_selected", "qualitative_panels_generated"]:
    print(f"  {k} = {ne[k]}")
assert ne["hard_cases_selected"] == 0 and ne["model_forwards"] == 0 and ne["TEST_reads"] == 0
''')

md("""## 20. TEST lock

`TEST` = `LOCKED_UNTIL_PHASE39` — 0 reads. ROUTER_HOLDOUT raw images/GT are protected; no reread.

---
## Summary

* Phase33 specification complete; **failure analysis NOT executed**.
* Eligible: **table-only** and **derived non-pixel** descriptive failure analysis.
* Ineligible: boundary metric, component/object metric, qualitative gallery, prediction-pixel,
  raw image, raw GT, model rerun.
* Hard-case procedure frozen with **0 cases selected**; 0 qualitative panels generated.
* Phase30 qualifier remains mandatory; Phase34 not started.
""")


def build():
    nb = {"cells": CELLS,
          "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python",
                                      "name": "python3"},
                       "language_info": {"name": "python", "version": "3.11.9"}},
          "nbformat": 4, "nbformat_minor": 5}
    NB.parent.mkdir(parents=True, exist_ok=True)
    NB.write_text(json.dumps(nb, indent=1) + "\n", encoding="utf-8")
    print("wrote", NB, "cells:", len(CELLS))


if __name__ == "__main__":
    build()
