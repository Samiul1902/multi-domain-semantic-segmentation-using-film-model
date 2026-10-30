#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build the Phase33 TIER_0/TIER_1 descriptive-failure reviewer notebook (v1.2, SUCCESSFUL run).

Classification: TIER0_TIER1_FROZEN_TABLE_DESCRIPTIVE_FAILURE_ANALYSIS_REVIEWER_NOTEBOOK.

Reads ONLY: frozen scored CSV, authorized metadata manifest, new Phase33 TIER_0/TIER_1 result
tables. NO images, NO GT, NO prediction/probability arrays, NO models, NO TEST.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/build_phase33_tier0_tier1_notebook_v1_2.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
NB = (ROOT / "notebooks" / "phasewise" / "phase_33_final_failure_analysis" /
      "phase33_final_failure_analysis_tier0_tier1_v1_2.ipynb")

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
    with pd.option_context("display.max_columns", None, "display.width", 200):
        print(df.to_string(index=False))
    return df


print("Phase33 TIER_0/TIER_1 descriptive failure reviewer notebook (v1.2)")
print("No raw images, no raw GT, no prediction/probability arrays, no TEST, no models.")
'''

CELLS = []


def md(s):
    CELLS.append({"cell_type": "markdown", "metadata": {}, "source": s})


def code(s):
    CELLS.append({"cell_type": "code", "execution_count": None, "metadata": {},
                  "outputs": [], "source": s})


md("""# Phase 33 — Final System Failure Analysis
## TIER_0 / TIER_1 Authorized Descriptive Execution — Reviewer Notebook (v1.2)

**Classification:** `TIER0_TIER1_FROZEN_TABLE_DESCRIPTIVE_FAILURE_ANALYSIS_REVIEWER_NOTEBOOK`
**Revision:** `ra_medfilm_barr_phase33_failure_boundary_v1_2`

**Outcome:** the LOW_OVERLAP realization rule is now **fully explicit** (spec v1.2) and the
authorized TIER_0/TIER_1 descriptive failure analysis executed successfully on the frozen
Phase30 ROUTER_HOLDOUT tables and the metadata-only group map.

This notebook is a **new** artifact. The earlier blocked notebook
(`phase33_final_failure_analysis_review.ipynb`) is preserved untouched as fail-closed provenance.
""")

md("## 0. Setup")
code(SETUP)

md("## 1. Phase33 authority and the v1.2 amendment")
code('''\
term = jload(AUD / "phase33_specification_terminal_v1_2.json")
fc = jload(AUD / "phase33_specification_final_check_v1_2.json")
print("v1.2 status:", term["status"])
print("v1.2 terminal:", term["terminal"])
print("final check v1.2:", fc["n_checks"], "checks,", fc["n_failed"], "failed")
print()
ct = jload(AUD / "phase33_low_overlap_realization_contract_v1_2.json")
print("contract: elements", ct["n_elements"], "| all explicit:", ct["all_elements_explicit"],
      "| rule exactly frozen:", ct["rule_exactly_frozen"])
''')

md("## 2. Prior blocked attempt — preserved as historical evidence")
code('''\
pb = jload(AUD / "phase33_tier0_tier1_prior_block_preservation_v1_2.json")
print("preserved byte-for-byte:", pb["n_match"], "/", pb["n_preserved"],
      "| all:", pb["all_preserved"])
for b in pb["preserved"]:
    print(f"  {b['match']}  {b['path']}")
''')

md("## 3. Mandatory Phase30 qualifier")
code('''\
print("QUALIFIER:")
print(" ", "ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_SCIENTIFIC_SOURCE_FREEZE_DEVIATION")
print()
print("Phase30 status: COMPLETE_WITH_PROTOCOL_DEVIATION__NOT_COMPLETE_CANONICAL (NOT upgraded)")
print("Phase33 = descriptive analysis of frozen QUALIFIED Phase30 evidence.")
''')

md("## 4. Population integrity")
code('''\
lab = pd.read_csv(TAB / "phase33_final_system_failure_labels_v1_2.csv")
print("labels rows:", len(lab), "| unique sample_id:", lab["sample_id"].nunique())
print("domain counts:", lab["dataset"].value_counts().to_dict())
gi = jload(AUD / "phase33_group_join_integrity_v1_2.json")
print("groups:", gi["n_groups"], "| unmatched:", gi["n_unmatched"],
      "| multiply matched:", gi["n_multiply_matched"])
print("group_key present:", "group_key" in lab.columns)
''')

md("## 5. Exact LOW_OVERLAP realization contract (8/8 explicit)")
code('''\
for e in ct["elements"]:
    print(f"  {e['n']}. {e['element']:38s} -> {e['value']}")
print()
print("target column:", ct["low_overlap_target_column"],
      "| reference-only:", ct["reference_only_column"])
print("comparison:", ct["comparison_operator"], "| ties included:", ct["ties_included"])
print("missing policy:", ct["missing_policy"], "| scope:", ct["scope"])
''')

md("## 6. Realized LOW_OVERLAP cutoff")
code('''\
co = jload(AUD / "phase33_low_overlap_cutoff_realization.json")
print("finite gate pass:", co["finite_gate_pass"], "| gate:", co["finite_gate"])
print("cutoff:", co["realized_cutoff_repr"])
print("ties exactly equal to cutoff:", co["n_exactly_equal_to_cutoff"])
print("LOW_OVERLAP n:", co["low_overlap_n"], "| rate:", co["low_overlap_rate"])
print("cutoff realized exactly once:", co["cutoff_realization_count"] == 1)
print("science definition changed:", co["science_definition_changed"])
''')

md("## 7. Overall failure prevalence")
code('tshow("phase33_failure_prevalence_overall_v1_2.csv")')

md("## 8. Domain failure prevalence")
code('tshow("phase33_failure_prevalence_by_domain_v1_2.csv")')

md("## 9. Router-state failure analysis")
code('tshow("phase33_router_state_failure_summary_v1_2.csv")')

md("## 10. Benefit classes")
code('''\
print("BENEFICIAL delta_dice_a8 >= +0.02 ; HARMFUL <= -0.01 ; NEUTRAL otherwise")
print(lab["benefit_class"].value_counts().to_dict())
print()
print("cross-tab benefit_class x state_machine:")
print(pd.crosstab(lab["state_machine"], lab["benefit_class"]).to_string())
''')

md("## 11. Router harmful activation")
code('''\
print("definition: EXECUTE and delta_dice_a8 <= -0.01")
ha = lab[lab["router_harmful_activation"]]
print("n:", len(ha), "| rate over EXECUTE:",
      len(ha) / int((lab["router_decision"] == "EXECUTE").sum()))
print("by domain:", ha["dataset"].value_counts().to_dict())
''')

md("## 12. Router missed benefit")
code('''\
print("definition: SKIP and delta_dice_a8 >= +0.02")
mb = lab[lab["router_missed_benefit"]]
print("n:", len(mb), "| rate over SKIP:",
      len(mb) / int((lab["router_decision"] == "SKIP").sum()))
''')

md("## 13. EXECUTE_THEN_REJECT")
code('''\
er = lab[lab["execute_then_reject"]]
print("n:", len(er), "| by domain:", er["dataset"].value_counts().to_dict())
tshow("phase33_accepted_vs_rejected_summary_v1_2.csv")
''')

md("""## 14. EMPTY_PREDICTION — Dice-zero proxy ONLY

`empty_prediction_proxy` is the frozen **Dice == 0 proxy**. It is **not** a confirmed empty
segmentation mask; no predicted-positive-area computation was performed.""")
code('''\
print("dice_zero_proxy n:", int(lab["empty_prediction_proxy"].sum()))
print("authorized derivation: DICE_ZERO_PROXY_ONLY")
print("predicted-area computation authorized: False")
''')

md("## 15. Selected vs skipped")
code('tshow("phase33_selected_vs_skipped_summary_v1_2.csv")')

md("## 16. Accepted vs rejected")
code('tshow("phase33_accepted_vs_rejected_summary_v1_2.csv")')

md("## 17. Group concentration")
code('''\
gc = pd.read_csv(TAB / "phase33_group_failure_concentration_v1_2.csv")
print("groups:", len(gc), "| samples:", int(gc["n_samples"].sum()))
print("groups with any failure:", int((gc["union_failure_count"] > 0).sum()))
print("top 10 groups by union_failure_count:")
with pd.option_context("display.max_columns", None, "display.width", 200):
    print(gc.sort_values(["union_failure_count", "group_key"], ascending=[False, True])
          .head(10).to_string(index=False))
print("note: singleton groups are NOT assumed to be known patients.")
''')

md("## 18. Failure category overlap")
code('tshow("phase33_failure_category_overlap_matrix_v1_2.csv")')
code('tshow("phase33_failure_combination_counts_v1_2.csv")')

md("""## 19. delta_hat diagnostics

`delta_prediction_error = delta_hat - delta_dice_a8`. Descriptive only. No model fitting, no
threshold recalibration, no new router rule, no formal calibration claim.""")
code('tshow("phase33_delta_prediction_error_summary_v1_2.csv")')

md("## 20. Hard-case ID selection status")
code('''\
hc = pd.read_csv(TAB / "phase33_hard_case_ids_v1_2.csv")
print("classification: DESCRIPTIVE_FAILURE_CASE_SELECTION")
print("selected:", len(hc))
print("by stratum:", hc["stratum"].value_counts().to_dict())
print("IDs / metadata ONLY — no image, no mask, no prediction pixel.")
''')

md("""## 21. Boundary / component / qualitative — INELIGIBLE

* **BOUNDARY_ERROR** = `INELIGIBLE`
* **COMPONENT_ANALYSIS** = `INELIGIBLE`
* **QUALITATIVE_GALLERY** = `INELIGIBLE`

The six blocked families (`FALSE_POSITIVE_BURDEN`, `FALSE_NEGATIVE_BURDEN`, `OBJECT_MISS`,
`MULTI_COMPONENT_PARTIAL_DETECTION`, `MULTI_COMPONENT_COMPLETE_MISS`, `BOUNDARY_ERROR`) were
**not** computed.""")
code('''\
tx = jload(AUD / "phase33_failure_taxonomy_contract_v1_1.json")
print("ELIGIBLE (7):", tx["eligible_families"])
print("BLOCKED  (6):", tx["ineligible_families"])
print("partition disjoint:", tx["eligible_ineligible_disjoint"])
''')

md("## 22. Zero prohibited-access counters")
code('''\
pc = jload(AUD / "phase33_tier0_tier1_prohibited_counters_v1_2.json")
for k, v in pc["counters"].items():
    print(f"  {k} = {v}")
print("all zero:", pc["all_zero"])
assert pc["all_zero"]
''')

md("""## 23. Scientific interpretation

The authorized **TIER_0/TIER_1 descriptive failure analysis** of the frozen, qualified Phase30
ROUTER_HOLDOUT evidence completed successfully. The LOW_OVERLAP stratum was realized exactly once
from the frozen `a8_dice` column using a single **global** bottom-decile cutoff
(`np.quantile(a8_dice[float64], 0.10, 'linear')`, inclusive `<=`, ties included).

All reported quantities are **descriptive summaries of frozen scalar metrics**. There is
**no causal claim**, **no significance claim**, **no confidence interval**, and **no new
statistical test**. The boundary, component/object, qualitative-gallery and model-rerun paths
remain **blocked**.

**Phase30 qualifier remains mandatory and Phase30 status is not upgraded. Phase34 not started.
TEST reads = 0.**""")

md("""---
## Summary

| item | value |
|---|---|
| execution outcome | `TIER0_TIER1_DESCRIPTIVE_FAILURE_ANALYSIS_COMPLETE` |
| LOW_OVERLAP rule | `a8_dice <= np.quantile(float64, 0.10, 'linear')`, GLOBAL, ties included |
| eligible failure families | 7 (5 per-sample + 2 aggregate) |
| blocked families | 6 (not computed) |
| boundary / component / qualitative | `INELIGIBLE` |
| raw image / GT / prediction / probability reads | 0 |
| model forwards · TEST reads · training | 0 |
| Phase33 closure | NOT closed (eligible, not started) |
| Phase34 | NOT started |
""")


def build():
    nb = {"cells": CELLS,
          "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python",
                                      "name": "python3"},
                       "language_info": {"name": "python", "version": "3.11.9"}},
          "nbformat": 4, "nbformat_minor": 5}
    NB.parent.mkdir(parents=True, exist_ok=True)
    NB.write_text(json.dumps(nb, indent=1) + "\n", encoding="utf-8")
    print("wrote", NB, "cells:", len(CELLS),
          "code cells:", sum(1 for c in CELLS if c["cell_type"] == "code"))


if __name__ == "__main__":
    build()
