#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build the Phase32 read-only external-provenance reviewer notebook.

READ_ONLY_EXTERNAL_PROVENANCE_REVIEWER_NOTEBOOK__NO_EXTERNAL_SCIENTIFIC_EXECUTION.
Consumes ONLY Phase32 frozen report artifacts.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/build_phase32_reviewer_notebook.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
NB = (ROOT / "notebooks" / "phasewise" / "phase_32_external_validation" /
      "phase32_external_domain_shift_review.ipynb")

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


print("Phase32 reviewer notebook - READ-ONLY EXTERNAL PROVENANCE PACKAGING")
print("No external image/GT read, no model, no metric computation.")
'''

CELLS = []


def md(s):
    CELLS.append({"cell_type": "markdown", "metadata": {}, "source": s})


def code(s):
    CELLS.append({"cell_type": "code", "execution_count": None, "metadata": {},
                  "outputs": [], "source": s})


md("""# Phase 32 — External Dataset & Domain Shift Evaluation
## External-Cohort Provenance & Domain-Shift Eligibility Adjudication

**Revision:** `ra_medfilm_barr_phase32_external_domain_shift_v1_0`
**Classification:** `READ_ONLY_EXTERNAL_PROVENANCE_REVIEWER_NOTEBOOK__NO_EXTERNAL_SCIENTIFIC_EXECUTION`

This notebook consumes **only** frozen Phase32 report artifacts. It reads **no** external image pixels
or masks, performs **no** model inference, and computes **no** metrics.
""")

md("## 2. Setup")
code(SETUP)

md("## 3. Phase31 → Phase32 authority binding")
code('''\
b = jload(AUD / "phase32_entry_authority_binding.json")
print("Phase31 closure terminal:", b["phase31_status"])
print("Phase31 terminal token  :", b["phase31_terminal_token"])
print("Phase32 roadmap identity:", b["phase32_roadmap_identity"])
print("all bindings match      :", b["all_bindings_match"])
for x in b["phase31_bindings"]:
    print(f"  {x['match']}  {x['path']}")
''')

md("## 4. Mandatory Phase30 qualifier")
code('''\
print("QUALIFIER:")
print(" ", "ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_SCIENTIFIC_SOURCE_FREEZE_DEVIATION")
print()
print("Phase30 status:", "COMPLETE_WITH_PROTOCOL_DEVIATION__NOT_COMPLETE_CANONICAL")
print("Phase30 status upgraded:", False)
''')

md("""## 5. Scientific question

**How does the frozen RA-MedFiLM-BARR system generalize under external dataset / domain shift?**

This is **external / domain-shift evidence only** — not training, model/threshold/policy selection,
calibration, or a Phase39 TEST substitute.""")

md("## 6. Discovered external candidates")
code('''\
disc = pd.read_csv(TAB / "phase32_external_dataset_discovery.csv")
print("candidates discovered:", len(disc))
print(disc[["candidate_id", "dataset_name", "filesystem_exists", "n_files_total",
            "known_domain_modality", "candidate_status"]].to_string(index=False))
''')

md("## 7. Historical exposure table")
code('''\
exp = pd.read_csv(TAB / "phase32_external_prior_exposure_matrix.csv")
print(exp[["candidate_id", "dataset_name", "exposure_class",
           "legacy_notebook_reference_count", "outcome_exposed"]].to_string(index=False))
print()
print("exposure-class counts:", exp["exposure_class"].value_counts().to_dict())
''')

md("## 8. Phase32 role registry")
code('''\
reg = pd.read_csv(TAB / "phase32_external_cohort_role_registry.csv")
print(reg[["candidate_id", "dataset_name", "exposure_class", "phase32_role"]].to_string(index=False))
print()
print("role counts:", reg["phase32_role"].value_counts().to_dict())
''')

md("## 9. Summary counts")
code('''\
summary = pd.DataFrame({
    "metric": ["discovered candidates", "outcome-exposed historically",
               "historically-exposed benchmarks", "overlap-risk",
               "provenance-ambiguous", "task mismatch",
               "primary eligible", "secondary eligible", "supplementary stress test"],
    "count": [len(disc), 9, 8, 2, 4, 5, 0, 0, 0],
})
print(summary.to_string(index=False))
assert len(disc) == 19
''')

md("""## 10. Why 9 outcome-exposed ≠ 8 historical-benchmark roles

**EXT-13** (`medfilm_seg/data_external/CVC_ClinicDB`) is historically outcome-exposed **but** it is a
duplicate copy of `EXT-03`, so its Phase32 role is `INELIGIBLE_OVERLAP_RISK` — not a benchmark.
The 9-vs-8 difference is therefore **expected** and must not be "repaired".""")

md("## 11. System under test (frozen A8/C9)")
code('''\
sut = jload(AUD / "phase32_system_under_test_binding.json")
print("system:", sut["system"])
for k, v in sut["components"].items():
    print(f"  {k:8s} {v['sha256']}  match={v['match']}")
print()
print("bundle manifest SHA:", sut["bundle_manifest"]["sha256"])
print("retraining:", sut["retraining"], "| fine_tuning:", sut["fine_tuning"],
      "| threshold_tuning:", sut["threshold_tuning"])
''')

md("## 12. Preprocessing contract")
code('''\
pp = jload(AUD / "phase32_preprocessing_compatibility_contract.json")
for k, v in pp["frozen_deployment_preprocessing"].items():
    print(f"  {k}: {v}")
print()
print("dataset-specific preprocessing created:", pp["dataset_specific_preprocessing_created"])
''')

md("## 13. Metric contract")
code('''\
mc = jload(AUD / "phase32_metric_contract.json")
for k, v in mc["metrics"].items():
    print(f"  {k}: {v['status']}")
print()
print("empty-mask policy:", mc["empty_mask_policy"])
''')

md("## 14. Task mapping summary")
code('''\
tm = pd.read_csv(TAB / "phase32_external_task_mapping.csv")
print(tm[["candidate_id", "dataset_name", "modality",
          "proposed_existing_task_id", "status"]].to_string(index=False))
''')

md("## 15. Open-state registry summary")
code('''\
osr = jload(AUD / "phase32_external_open_state_registry.json")
states = {}
for cid, v in osr["states"].items():
    states.setdefault(v["open_state"], []).append(cid)
for st, ids in states.items():
    print(f"  {st}: {len(ids)}  {ids}")
print()
print("falsely reset to unopened:", osr["falsely_reset_to_unopened"])
''')

md("""## 16. Final Phase32 conclusion

**NO_PROSPECTIVE_CLEAN_EXTERNAL_COHORT_ELIGIBLE**

No Phase32 external model evaluation was performed.""")

md("## 17. Zero-action counters")
code('''\
ne = jload(AUD / "phase32_no_execution_audit.json")
for k in ["external_image_content_reads", "external_GT_content_reads", "model_forwards",
          "prediction_generation", "metric_computations", "threshold_tuning", "calibration",
          "training", "ROUTER_HOLDOUT_reads", "TEST_reads"]:
    print(f"  {k} = {ne[k]}")
assert ne["external_image_content_reads"] == 0 and ne["model_forwards"] == 0
''')

md("""---
## Summary

* 19 external candidates discovered; **0 primary / 0 secondary / 0 stress-test-only**.
* 9 historically outcome-exposed (8 benchmark roles + 1 overlap-risk duplicate).
* 11 ineligible (2 overlap-risk, 4 provenance-ambiguous, 5 task-mismatch).
* Frozen A8/C9 system bound; preprocessing/metric/estimand/claim/statistics contracts frozen.
* **No external execution performed**; execution eligible = **false**.
* Phase30 qualifier remains mandatory.
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
