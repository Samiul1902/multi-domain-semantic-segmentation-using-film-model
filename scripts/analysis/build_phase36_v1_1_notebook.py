#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the Phase 36 v1.1 reviewer notebook (READ-ONLY governance summary).

The notebook reads ONLY Phase36 governance/smoke artifacts. It NEVER:
  constructs models, loads checkpoints, runs forward, generates perturbations,
  reads medical data, reads VAL808, reads GT, reads ROUTER_HOLDOUT, reads TEST,
  or trains.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NB_DIR = ROOT / "notebooks" / "phasewise" / "phase_36_robustness"
NB = NB_DIR / "phase36_synthetic_full_pipeline_smoke_v1_1_review.ipynb"
AUD = ROOT / "reports" / "audits"

CELLS = []


def md(src):
    CELLS.append({"cell_type": "markdown", "metadata": {}, "source": src.splitlines(keepends=True)})


def code(src):
    CELLS.append({"cell_type": "code", "execution_count": None, "metadata": {},
                  "outputs": [], "source": src.splitlines(keepends=True)})


md("""# Phase 36 v1.1 — Executable Robustness Source Completion
## Reviewer Notebook (READ-ONLY)

**CLASSIFICATION:** `PRE_SCIENTIFIC_EXECUTABLE_SOURCE_COMPLETION_AND_PROSPECTIVE_PROTOCOL_AMENDMENT`
**REVISION:** `ra_medfilm_barr_phase36_robustness_v1_1`

This notebook summarises the **v1.0 block**, the **v1.1 amendment**, and the
verification state. It reads **only** governance artifacts.

It does **NOT**: construct models, load checkpoints, run forward passes, generate
perturbations, read medical data, read VAL808, read GT, read ROUTER_HOLDOUT,
read TEST, or train.""")

md("## 1. v1.0 pre-construction block (disclosed, preserved)")
code("""import json, hashlib
from pathlib import Path
ROOT = Path.cwd()
while not (ROOT / "reports" / "audits").exists() and ROOT != ROOT.parent:
    ROOT = ROOT.parent
AUD = ROOT / "reports" / "audits"

def jload(name):
    return json.loads((AUD / name).read_text(encoding="utf-8"))

block = jload("phase36_v1_0_preconstruction_smoke_block_record_v1_1.json")
print("classification:", block["classification"])
print("execution_source_invocations:", block["counters"]["execution_source_invocations"])
print("model_constructions:", block["counters"]["model_constructions"])
print("protected_data_reads:",
      block["counters"]["raw_VAL_reads"] + block["counters"]["VAL_GT_reads"]
      + block["counters"]["ROUTER_HOLDOUT_reads"] + block["counters"]["TEST_reads"])
print("defects:", len(block["defects_discovered"]))""")

md("## 2. v1.1 amendment + verification")
code("""unit = jload("phase36_robustness_unit_v1_1.json")
pre  = jload("phase36_robustness_static_preflight_v1_1.json")
elig = jload("phase36_synthetic_smoke_eligibility_v1_1.json")
print("unit      :", f"{unit['passed']}/{unit['total_checks']}", "all_pass =", unit["all_pass"])
print("preflight :", f"{pre['passed']}/{pre['total_checks']}", "all_pass =", pre["all_pass"])
print("smoke eligible:", elig["synthetic_smoke_eligible"], "| started:", elig["synthetic_smoke_started"])
print("science eligible:", elig["scientific_execution_eligible"], "| started:", elig["scientific_execution_started"])""")

md("## 3. Load-bearing amendments")
code("""for name in ("phase36_phase25b_feature_extractor_binding_v1_1.json",
             "phase36_phase26_full_system_execution_binding_v1_1.json"):
    a = jload(name)
    print("---", a["artifact"], "---")
    print("  classification:", a["classification"])
    print("  all_pass      :", a["all_pass"])""")

md("## 4. Semantic diff — unchanged vs clarified")
code("""d = jload("phase36_v1_0_to_v1_1_execution_semantic_diff.json")
print("amendment:", d["scientific_protocol_amendment"])
print("results before amendment:", d["scientific_results_existed_before_amendment"])
print("protected data before amendment:", d["protected_data_opened_before_amendment"])
print("UNCHANGED:", ", ".join(k for k, v in d["unchanged"].items() if v))
print("CLARIFIED:", ", ".join(d["added_or_clarified_prospectively"].keys()))""")

md("## 5. Zero-execution audit")
code("""z = jload("phase36_v1_1_source_repair_no_execution_audit.json")
print("all_counters_zero:", z["all_counters_zero"])
for k, v in z["counters"].items():
    print(f"  {k}: {v}")""")

md("## 6. Terminal")
code("""t = jload("phase36_v1_1_executable_source_repair_terminal.json")
print("final_check:", t["final_check"])
print("smoke:", t["phase36_smoke_status"], "| science:", t["phase36_science_status"])
print("phase37:", t["phase37_status"], "| TEST:", t["test_state"])
print()
print(t["terminal_string"])""")

md("""## 7. Reviewer statement

- The v1.0 smoke was **blocked** before any model construction; that block is preserved.
- v1.1 resolves **one** load-bearing ambiguity prospectively: the proposal-perturbation
  insertion / recomputation contract, bound to the canonical executable rather than prose.
- A **disclosed** prospective change to the noise-seed conversion (8 hex chars, 32-bit)
  supersedes the v1.0 8-byte/64-bit rule for all future v1.1 execution; no scientific
  result existed before the change.
- Phase36 scientific execution remains **NOT_STARTED**. TEST remains
  **LOCKED_UNTIL_PHASE39**.""")

NB_DIR.mkdir(parents=True, exist_ok=True)
nb = {"cells": CELLS, "metadata": {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": "3.11.9"}},
    "nbformat": 4, "nbformat_minor": 5}
NB.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
print(json.dumps({"notebook": str(NB.relative_to(ROOT)),
                  "sha256": hashlib.sha256(NB.read_bytes()).hexdigest(),
                  "n_cells": len(CELLS)}, indent=1))
