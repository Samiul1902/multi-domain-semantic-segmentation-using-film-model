#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build the Phase31 post-closure read-only reviewer notebook.

POST_CLOSURE_READ_ONLY_REVIEWER_NOTEBOOK__NO_NEW_SCIENTIFIC_EXECUTION.
The notebook reads ONLY frozen Phase31/Phase30 report artifacts, tables and Markdown.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/build_phase31_reviewer_notebook.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
NB = (ROOT / "notebooks" / "phasewise" / "phase_31_statistical_significance" /
      "phase31_statistical_significance_review.ipynb")

SETUP = '''\
import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(r"D:\\Softfors\\jup")
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
DOCS = ROOT / "docs"


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def jload(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


print("Phase31 reviewer notebook - POST-CLOSURE READ-ONLY EVIDENCE PACKAGING")
print("No statistical estimator, no inferential function, no model, no raw image/GT read.")
'''

CELLS = []


def md(s):
    CELLS.append({"cell_type": "markdown", "metadata": {}, "source": s})


def code(s):
    CELLS.append({"cell_type": "code", "execution_count": None, "metadata": {},
                  "outputs": [], "source": s})


md("""# Phase 31 — Statistical Significance & Hypothesis Testing
## Canonical Statistical Claim-Governance / Provenance Adjudication

**Classification:** `POST_CLOSURE_READ_ONLY_REVIEWER_NOTEBOOK__NO_NEW_SCIENTIFIC_EXECUTION`

This notebook renders **frozen** Phase31/Phase30 evidence only. It performs **no** statistical
estimator, **no** inferential function, **no** model load, and reads **no** raw image or GT.
""")

md("## 2. Setup")
code(SETUP)

md("## 3. Canonical status panel")
code('''\
t = jload(AUD / "phase31_closure_terminal.json")
print("Phase31 status      :", t["status"])
print("closure class       :", t["closure_class"])
print("scientific role     :", t["phase31_scientific_role"])
print("scientific conclusion:", t["scientific_conclusion"])
print("revision            :", jload(AUD / "phase31_final_closure.json")["revision"])
assert t["status"] == "COMPLETE_CANONICAL"
assert t["scientific_conclusion"] == "NO_NEW_CONFIRMATORY_SIGNIFICANCE_PROCEDURE_IS_ELIGIBLE"
''')

md("""## 4. Phase30 qualification panel (mandatory)

Any use of Phase30 evidence must carry this qualifier. Phase30 is **not** `COMPLETE_CANONICAL`.""")
code('''\
fc = jload(AUD / "phase31_final_closure.json")
print("Phase30 evidence class :", fc["Phase30_evidence_class"])
print("Phase30 status         :", fc["Phase30_status"])
print("Phase30 status upgraded:", not fc["Phase30_status_not_upgraded"])
print()
print("MANDATORY QUALIFIER:")
print(" ", "ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_SCIENTIFIC_SOURCE_FREEZE_DEVIATION")
''')

md("## 5. Hypothesis provenance (10 candidates, frozen v1.1 matrix)")
code('''\
hm = pd.read_csv(TAB / "phase31_hypothesis_provenance_matrix_v1_1.csv")
print(hm[["hypothesis_id", "current_Phase31_status"]].to_string(index=False))
counts = hm["current_Phase31_status"].value_counts().to_dict()
print()
print("status-count summary:")
for k in ["CONFIRMATORY_PREOUTCOME_EXACT_METHOD_FROZEN",
          "PREOUTCOME_HYPOTHESIS_METHOD_INCOMPLETE",
          "ALREADY_ADJUDICATED_BY_PREDECESSOR_PHASE",
          "DESCRIPTIVE_ONLY_BY_PREDECESSOR_AUTHORITY",
          "POST_HOC_EXPLORATORY_ONLY",
          "FORBIDDEN_OR_OUT_OF_SCOPE"]:
    print(f"  {k} = {counts.get(k, 0)}")
print("  total =", len(hm))
assert len(hm) == 10 and (hm["current_Phase31_status"].astype(str).str.len() > 0).all()
''')

md("## 6. Statistical-test registry (T01–T04)")
code('''\
reg = pd.read_csv(TAB / "phase31_statistical_test_registry_v1_1.csv")
cols = ["test_id", "hypothesis_id", "provenance_class", "disposition_v1_1",
        "execution_authorized", "execution_eligible", "execution_ineligibility_reason"]
print(reg[cols].to_string(index=False))
print()
assert (reg["execution_authorized"].astype(str) == "False").all()
assert (reg["execution_eligible"].astype(str) == "False").all()
t04 = reg[reg["test_id"] == "T04"]["disposition_v1_1"].iloc[0]
print("T04 canonical disposition:", t04)
assert t04 == "PREOUTCOME_HYPOTHESIS_METHOD_INCOMPLETE"
''')

md("""## 7. Why T01 is not executable

**T01** is a sample-level 875-row paired Wilcoxon. ROUTER_HOLDOUT contains **875 rows in 628
groups** (`group_key`). A naive sample-level test ignores the frozen group dependence and is
therefore **forbidden** — `SAMPLE_LEVEL_875_ROW_TEST_IGNORES_FROZEN_GROUP_DEPENDENCE`.""")

md("""## 8. Why T02 is not executable

**T02** proposes a new bootstrap **p-value** estimand. The frozen Phase30 bootstrap plan
(`59c97ccf…`) is authorized only for its already-frozen CI outputs, **not** for a newly invented
p-value estimand — `EXISTING_BOOTSTRAP_PLAN_DOES_NOT_AUTHORIZE_NEW_PVALUE_ESTIMAND`.""")

md("""## 9. T03 / T04

* **T03** — `DESCRIPTIVE_ONLY_BY_PREDECESSOR_AUTHORITY` (a descriptive companion, not a test).
* **T04** — `PREOUTCOME_HYPOTHESIS_METHOD_INCOMPLETE` (no exact method was ever frozen).""")

md("## 10. Phase30 frozen numerical result (unchanged; qualifier applies)")
code('''\
pr = jload(AUD / "phase30_primary_noninferiority_result.json")
print("global macro Dice :", pr["global_macro_dice"])
print("A8 macro Dice     :", pr["a8_macro_dice"])
print("macro DeltaDice   :", pr["macro_delta_dice"])
print("macro 95% CI      :", pr["macro_ci"])
print("PRESERVATION_ASSERTED:", pr["PRESERVATION_ASSERTED"])
print("Phase30 p-values  :", pr["p_values_computed"])
print()
print("QUALIFIER: ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_SCIENTIFIC_SOURCE_FREEZE_DEVIATION")
''')

md("## 11. Zero-execution panel")
code('''\
aud = jload(AUD / "phase31_no_execution_audit_v1_1.json")
for k in ["new_statistical_tests", "new_p_values", "new_effect_sizes",
          "new_bootstrap_computations", "raw_ROUTER_HOLDOUT_image_reads",
          "raw_ROUTER_HOLDOUT_GT_reads", "model_forwards", "training_steps", "TEST_reads"]:
    print(f"  {k} = {aud[k]}")
assert aud["new_p_values"] == 0 and aud["model_forwards"] == 0 and aud["TEST_reads"] == 0
''')

md("""## 12. Scientific interpretation

Phase31 did **not** conclude that "the method is not significant".

It concluded: **NO NEW CONFIRMATORY SIGNIFICANCE PROCEDURE IS ELIGIBLE.**""")

md("## 13. Closure artifacts")
code('''\
for p in ["phase31_closure_terminal.json", "phase31_final_closure.json",
          "phase31_final_closure_check.json"]:
    d = jload(AUD / p)
    print(f"{p}: {sha256_file(AUD / p)}")
    if "terminal" in d:
        print("   terminal:", d["terminal"])
    if "all_pass" in d:
        print("   all_pass:", d["all_pass"])
chk = jload(AUD / "phase31_final_closure_check.json")
print()
print("final closure check:", chk["n_checks"] - chk["n_failed"], "/", chk["n_checks"],
      "failed:", chk["n_failed"])
''')

md("""---
## Summary

* Phase31 = **COMPLETE_CANONICAL**, governance-only statistical claim-provenance adjudication.
* **No** new confirmatory or exploratory statistical execution is eligible.
* Hypothesis distribution: 0 confirmatory / 1 method-incomplete / 5 already-adjudicated /
  2 descriptive-only / 1 post-hoc exploratory / 1 forbidden.
* Registry T01–T04: all `execution_authorized = false`, `execution_eligible = false`.
* Phase30 qualifier remains mandatory; Phase30 status **not** upgraded.
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
