#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build the Phase33 TIER_0/TIER_1 execution reviewer notebook (fail-closed).

Classification: TIER0_TIER1_FROZEN_TABLE_DESCRIPTIVE_FAILURE_ANALYSIS_REVIEWER_NOTEBOOK.
Renders frozen preflight + §E block adjudication. No descriptive failure results exist to render
because the LOW_OVERLAP realization rule was not exactly frozen.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/build_phase33_execution_notebook.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
NB = (ROOT / "notebooks" / "phasewise" / "phase_33_final_failure_analysis" /
      "phase33_final_failure_analysis_review.ipynb")

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


print("Phase33 TIER_0/TIER_1 execution reviewer notebook (fail-closed)")
print("No raw images, no raw GT, no prediction/probability arrays, no TEST, no models.")
'''

CELLS = []


def md(s):
    CELLS.append({"cell_type": "markdown", "metadata": {}, "source": s})


def code(s):
    CELLS.append({"cell_type": "code", "execution_count": None, "metadata": {},
                  "outputs": [], "source": s})


md("""# Phase 33 — Final System Failure Analysis
## TIER_0 / TIER_1 Authorized Descriptive Execution — Reviewer Notebook (FAIL-CLOSED)

**Classification:** `TIER0_TIER1_FROZEN_TABLE_DESCRIPTIVE_FAILURE_ANALYSIS_REVIEWER_NOTEBOOK`
**Revision:** `ra_medfilm_barr_phase33_failure_boundary_v1_1`

**Outcome:** execution **BLOCKED at pre-analysis**. The LOW_OVERLAP realization rule was not
**exactly** frozen in the Phase33 authority, so — per the fail-closed rule — **no scientific results
were computed**.

This notebook renders the frozen preflight and the block adjudication only.
""")

md("## 2. Setup")
code(SETUP)

md("## 3. Phase33 purpose and authority")
code('''\
b = jload(AUD / "phase33_tier0_tier1_preflight.json")
print("revision:", b["revision"])
print("authority bindings all match:", b["all_authority_match"])
for x in b["authority_bindings"]:
    print(f"  {x['match']}  {x['path']}")
print()
print("final check v1.1:", b["final_check_v1_1"]["n_checks"],
      "failed:", b["final_check_v1_1"]["n_failed"])
''')

md("## 4. Mandatory Phase30 qualifier")
code('''\
print("QUALIFIER:")
print(" ", "ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_SCIENTIFIC_SOURCE_FREEZE_DEVIATION")
print()
print("Phase30 status: COMPLETE_WITH_PROTOCOL_DEVIATION__NOT_COMPLETE_CANONICAL (not upgraded)")
''')

md("""## 5. Execution boundary

Authorized: **TIER_0** (frozen table read-only) and **TIER_1** (derived from frozen non-pixel
fields). **TIER_2 / TIER_3 / TIER_4 not authorized.**""")
code('''\
for k, v in b["execution_eligibility"].items():
    print(f"  {k}: {v}")
''')

md("## 6. Population integrity")
code('''\
p = b["population"]
print("n =", p["n"], "| expected 875")
print("domain counts:", p["domain_counts"], "| expected", p["domain_counts_expected"])
print("total groups:", p["total_groups"], "| expected", p["groups_expected"])
print("duplicate sample ids:", p["duplicate_sample_ids"])
print("unmatched metadata rows:", p["unmatched_metadata_rows"])
''')

md("## 7. Eligible vs ineligible taxonomy (v1.1)")
code('''\
tx = jload(AUD / "phase33_failure_taxonomy_contract_v1_1.json")
print("ELIGIBLE (7):")
for f in tx["eligible_families"]:
    print("  -", f)
print()
print("INELIGIBLE (6):")
for f in tx["ineligible_families"]:
    print("  -", f)
print()
print("overlap:", len(set(tx["eligible_families"]) & set(tx["ineligible_families"])),
      "| disjoint:", tx["eligible_ineligible_disjoint"])
''')

md("""## 8. Realized low-overlap rule and cutoff — **BLOCKED**

The LOW_OVERLAP realization rule was adjudicated **not exactly frozen**. No cutoff was realized.""" )
code('''\
lo = jload(AUD / "phase33_low_overlap_realization_adjudication.json")
print("rule exactly frozen:", lo["rule_exactly_frozen"])
print("action:", lo["action"])
print("cutoff realized:", lo["cutoff_realized"], "| realized cutoff:", lo["realized_cutoff"])
print("dice distribution inspected:", lo["dice_distribution_inspected"])
print("historical Phase11 precedent used as permission:",
      lo["historical_phase11_precedent_used_as_permission"])
print()
print("required elements:")
for e in lo["required_elements"]:
    print(f"  {e['n']}. {e['element']:44s} {e['status']}")
print()
print("BLOCKING elements:")
for e in lo["blocking_elements"]:
    print(f"  - {e['element']}: {e['why_blocking']}")
''')

md("""## 9–19. Descriptive failure analyses

**NOT EXECUTED.** The fail-closed rule requires stopping before any scientific derivation when the
LOW_OVERLAP realization rule is not exactly frozen, and explicitly forbids partial outcome analysis.

Consequently there are **no** Phase33 prevalence / severity / router-state / selected-vs-skipped /
accepted-vs-rejected / group-concentration / cross-category-overlap / delta-error tables, and **no**
hard-case ID table.""")

md("## 20. Hard-case selection status")
code('''\
print("hard-case selection executed: False")
print("reason: blocked at §E before the low-overlap realization; selection depends on the "
      "low_dice stratum")
print("hard cases selected: 0")
''')

md("""## 21. Negative-provenance section (boundary / component / qualitative)

* **Boundary analysis:** `INELIGIBLE` — no valid boundary metric in frozen final-system evidence.
* **Component/object analysis:** `INELIGIBLE` — no component information in frozen evidence.
* **Qualitative gallery:** `INELIGIBLE` — raw images and prediction pixels not authorized.
* The six ineligible failure families (`FALSE_POSITIVE_BURDEN`, `FALSE_NEGATIVE_BURDEN`,
  `OBJECT_MISS`, `MULTI_COMPONENT_PARTIAL_DETECTION`, `MULTI_COMPONENT_COMPLETE_MISS`,
  `BOUNDARY_ERROR`) remain **absolutely blocked**.""")

md("## 22. Zero prohibited-access counters")
code('''\
a = jload(AUD / "phase33_tier0_tier1_execution_audit.json")
print("outcome:", a["outcome"])
print()
for k, v in a["prohibited_counters"].items():
    print(f"  {k} = {v}")
assert all(v == 0 for v in a["prohibited_counters"].values())
''')

md("""## 23. Scientific interpretation

Phase33's authorized TIER_0/TIER_1 descriptive failure analysis **could not begin** because the
LOW_OVERLAP stratum's realization rule is not exactly frozen in the Phase33 authority. The
fail-closed rule was honoured: **no partial outcome analysis was performed and no results were
computed**.

This is a **provenance gap**, not a scientific finding about the model. Resolving it requires a
prospective Phase33 amendment that fully specifies the target Dice field, the cutoff comparison
operator, and the missing/NaN handling **before** any outcome inspection.

**Phase30 qualifier remains mandatory. Phase34 not started. TEST reads = 0.**""")

md("""---
## Summary

| item | value |
|---|---|
| execution outcome | `BLOCKED_PREANALYSIS__NO_RESULTS_COMPUTED` |
| blocking rule | `LOW_OVERLAP_REALIZATION_RULE_NOT_EXACTLY_FROZEN` |
| blocking elements | target Dice field · comparison operator · missing/NaN handling |
| preflight | 11/11 pass (n=875, groups=628, dup=0) |
| results computed | **0** |
| raw image / GT / prediction / probability reads | 0 |
| model forwards · TEST reads · training | 0 |
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
