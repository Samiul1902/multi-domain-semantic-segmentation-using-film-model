#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build the Phase30 reviewer notebook (deterministic, evidence-replay only).

The notebook performs NO model inference and NO raw ROUTER_HOLDOUT image read.
It consumes only the frozen post-execution audit artifacts and tables.

Writes notebooks/phasewise/phase_30_final_validation/
       phase30_final_development_validation.ipynb

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/build_phase30_notebook.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")

SETUP = '''\
import hashlib
import json
from pathlib import Path

import numpy as np
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


print("Phase30 reviewer notebook — EVIDENCE REPLAY ONLY (no inference, no image read)")
print("ROUTER_HOLDOUT = FINAL DEVELOPMENT VALIDATION BENCHMARK (NOT TEST)")
'''

CELLS = []


def md(s):
    CELLS.append({"cell_type": "markdown", "metadata": {}, "source": s})


def code(s):
    CELLS.append({"cell_type": "code", "execution_count": None, "metadata": {},
                  "outputs": [], "source": s})


md("""# Phase 30 — Final Development Validation Benchmark
## One-Shot ROUTER_HOLDOUT Execution — A8/C9 Final Development Validation

**Method:** RA-MedFiLM-BARR
**Population:** ROUTER_HOLDOUT — **FINAL DEVELOPMENT VALIDATION BENCHMARK — NOT TEST**
**Specification:** `ra_medfilm_barr_phase30_final_dev_validation_v1_3`

This notebook is a **pure evidence-replay** document. It performs **no model inference** and reads
**no raw ROUTER_HOLDOUT image or GT**. Every number is read from the frozen Phase30 artifacts.

* Primary claim = **A8 vs global non-inferiority** (lower 95% bootstrap CI > −0.005, strict).
* **No p-value** is computed or adjudicated (CASE P2).
* A7 = **DESCRIPTIVE ONLY**.
* H3 = descriptive only, no numeric success threshold.
""")

md("## 2. Setup")
code(SETUP)

md("## 3. Population and first-open provenance")
code('''\
pop = jload(AUD / "phase30_execution_population_rebind.json")
marker = jload(AUD / "phase30_first_open_marker.json")
print("population:", pop["population"], "n =", pop["n"], "groups =", pop["groups"])
print("domain counts:", pop["domain_counts"])
print("split manifest SHA :", pop["split_manifest"]["sha256"])
print("G batch manifest SHA:", pop["g_batch_manifest"]["sha256"])
print("bootstrap plan SHA  :", pop["bootstrap_plan"]["sha256"])
print()
print("first-open marker UTC:", marker["utc_timestamp"])
print("pre-open counters    :", marker["pre_open_counters"])
print("marker SHA-256       :", sha256_file(AUD / "phase30_first_open_marker.json"))
''')

md("## 4. System under test (A8/C9 fixed Phase26 bundle)")
code('''\
sysb = jload(AUD / "phase30_execution_system_rebind.json")
print("bundle manifest:", sysb["bundle_manifest"]["path"], sysb["bundle_manifest"]["sha256"][:16])
for k, v in sysb["components"].items():
    print(f"  {k:8s} {v['sha256'][:16]}  match={v['match']}")
for k, v in sysb["normalizers"].items():
    print(f"  norm {k:14s} {v['sha256'][:16]}  match={v['match']}")
for k, v in sysb["schemas"].items():
    print(f"  schema {k:12s} {v['sha256'][:16]}  match={v['match']}")
''')

md("## 5. Stage A — image-only inference summary")
code('''\
sa = jload(AUD / "phase30_stage_a_inference_summary.json")
print("n =", sa["n"], "| logical G passes =", sa["logical_G_passes"],
      "| G batch forwards =", sa["G_batch_forwards"])
print("G batch forwards by domain:", sa["G_batch_forwards_by_domain"])
print("G semantics:", sa["G_semantics"])
print()
print("router policy:", sa["router"]["policy"], "| score:", sa["router"]["runtime_score"])
print("n_selected =", sa["n_selected"], "| n_skip =", sa["n_skip"],
      "| realized activation =", round(sa["realized_activation_fraction"], 6))
print("R_psi_exec =", sa["n_Rpsi_exec"], "| S_omega_exec =", sa["n_Somega_exec"])
print("accept =", sa["n_accept"], "| reject =", sa["n_reject"], "| forced_skip =", sa["n_forced_skip"])
print("A7 additional model forwards =", sa["A7_additional_model_forwards"])
''')

md("## 6. Prediction hash barrier (load-bearing)")
code('''\
bar = jload(AUD / "phase30_prediction_hash_barrier.json")
print("barrier token        :", bar["barrier_token"])
print("n_samples            :", bar["n_samples"])
print("GT reads at hash     :", bar["ROUTER_HOLDOUT_GT_reads_at_hash"])
print("GT loaded anywhere   :", bar["GT_loaded_anywhere"])
print("TEST reads           :", bar["TEST_reads"])
for k, v in bar["prediction_hashes"].items():
    print(f"  {k}: {v[:24]}")
assert bar["barrier_token"] == "PREDICTION_HASH_BARRIER_PASS"
assert bar["ROUTER_HOLDOUT_GT_reads_at_hash"] == 0
print("\\nPrediction hash barrier PASS.")
''')

md("""## 7. Primary result — A8 vs global non-inferiority

**Primary adjudication = bootstrap non-inferiority CI.**
Criterion = **lower macro 95% CI > −0.005 (strict)**. No p-value.""")
code('''\
pr = jload(AUD / "phase30_primary_noninferiority_result.json")
print("estimand        :", pr["estimand"])
print("global macro Dice:", round(pr["global_macro_dice"], 6))
print("A8 macro Dice    :", round(pr["a8_macro_dice"], 6))
print("macro DeltaDice  :", round(pr["macro_delta_dice"], 6))
print("macro 95% CI     :", [round(x, 6) for x in pr["macro_ci"]])
print("margin           :", pr["noninferiority_margin"], "(strict)")
print("PRESERVATION_ASSERTED =", pr["PRESERVATION_ASSERTED"])
print("p_values_computed =", pr["p_values_computed"])
assert pr["p_values_computed"] == 0
''')

md("## 8. Per-domain results (macro may not hide domain harm)")
code('''\
df = pd.read_csv(TAB / "phase30_router_holdout_per_domain_results.csv")
print(df.to_string(index=False))
''')

md("## 9. Router metrics (frozen category semantics)")
code('''\
rm = jload(AUD / "phase30_router_metric_results.json")
for k in ("n_selected", "n_skip", "realized_activation_fraction", "precision_among_selected",
          "beneficial_coverage", "harmful_activation_share", "missed_benefit_rate",
          "mean_true_delta_dice_among_selected", "state_counts"):
    print(f"  {k}: {rm.get(k)}")
''')

md("## 10. A7 descriptive companion (DESCRIPTIVE ONLY)")
code('''\
a7 = jload(AUD / "phase30_a7_descriptive_companion_result.json")
print("role:", a7["role"])
print("A7 macro Dice:", round(a7["a7_macro_dice"], 6), "| A8 macro Dice:", round(a7["a8_macro_dice"], 6))
print("A8 - A7 point difference:", round(a7["a8_minus_a7_point_difference"], 6))
print("A7 harmful-replacement count:", a7["a7_harmful_replacement_count"],
      "| A8:", a7["a8_harmful_replacement_count"],
      "| reduction:", a7["absolute_harmful_replacement_reduction"])
print("uncertainty classification:", a7["descriptive_uncertainty"]["classification"])
print("A7 additional model forwards:", a7["A7_additional_model_forwards"])
''')

md("## 11. H3 descriptive result (no numeric gate)")
code('''\
h3 = jload(AUD / "phase30_h3_descriptive_result.json")
print("status:", h3["status"])
print("A7 harmful:", h3["a7_harmful_replacement_count"], "| A8 harmful:",
      h3["a8_harmful_replacement_count"], "| reduction:", h3["absolute_reduction"])
print("H3_PASS:", h3["H3_PASS"], "| H3_FAIL:", h3["H3_FAIL"],
      "| threshold:", h3["minimum_reduction_threshold"])
''')

md("## 12. Analytical compute (ANALYTICAL MAC LOWER BOUND)")
code('''\
cp = jload(AUD / "phase30_compute_results.json")
print("label:", cp["accounting_label"])
print("realized activation fraction:", round(cp["realized_activation_fraction"], 6))
print("A8 analytical average cost:", f"{cp['A8_analytical_average_cost']:.0f}")
print("A7 analytical average cost:", f"{cp['A7_analytical_average_cost']:.0f}")
print("s_omega saves compute:", cp["s_omega_saves_compute"])
print("forbidden labels used:", cp["forbidden_labels_used"])
''')

md("## 13. Post-open immutability + final freeze")
code('''\
imm = jload(AUD / "phase30_post_open_immutability_audit.json")
ff = jload(AUD / "phase30_final_freeze.json")
fc = jload(AUD / "phase30_execution_final_check.json")
print("post-open immutability all_pass:", imm["all_pass"])
print("execution final check:", fc["n_checks"] - fc["n_failed"], "/", fc["n_checks"],
      "failed:", fc["failed"])
print("terminal:", ff["terminal"])
print("ROUTER_HOLDOUT:", ff["ROUTER_HOLDOUT_state"], "| preservation_asserted:",
      ff["preservation_asserted"])
''')

md("""---
## Summary

* ROUTER_HOLDOUT is the **FINAL DEVELOPMENT VALIDATION BENCHMARK — NOT TEST**.
* One logical G extraction pass (111 batch forwards) over 875 samples, exact frozen order.
* Prediction hash barrier **PASS**; GT reads at hash = 0.
* Primary claim = **A8 vs global non-inferiority** (lower 95% CI > −0.005, strict).
* **No p-value** computed or adjudicated.
* A7 = descriptive only; H3 = descriptive only, no numeric gate.
* TEST reads = 0; training = 0.
""")


def build(out_path: Path) -> None:
    nb = {"cells": CELLS,
          "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python",
                                      "name": "python3"},
                       "language_info": {"name": "python", "version": "3.11.9"}},
          "nbformat": 4, "nbformat_minor": 5}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(nb, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    out = (ROOT / "notebooks" / "phasewise" / "phase_30_final_validation" /
           "phase30_final_development_validation.ipynb")
    build(out)
    print("wrote", out, "cells:", len(CELLS))
