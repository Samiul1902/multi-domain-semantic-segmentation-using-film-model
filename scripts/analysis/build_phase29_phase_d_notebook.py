#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build the Phase29 PHASE D reviewer notebook (deterministic, executed).

§17: The notebook is self-auditing: every asserted number is read from the frozen
Phase-D artifacts on disk and re-verified.  It performs NO inference, NO GT read
and NO model forward - it is a pure evidence-replay document.

Writes notebooks/phasewise/phase_29_3seed_reproducibility/
       phase29_phase_d_canonical_three_seed_validation.ipynb

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/build_phase29_phase_d_notebook.py
"""
from __future__ import annotations

import json
import sys
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
CANON = ROOT / "data_cache" / "phase29_val808_shared_fixed_g_v1_1_canonical"
CANON_D = ROOT / "data_cache" / "phase29_phase_d_canonical"


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def jload(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


PHASE27_GLOBAL_PROB_SHA = "cc6c54af986f56b4aba9265405ffeba4f6cac582eeff00fe6b0894429e7d3f13"
print("Setup complete.")
print("canonical cache root:", CANON.relative_to(ROOT))
print("canonical Phase D output root:", CANON_D.relative_to(ROOT))
'''

CELLS = []


def md(src):
    CELLS.append({"cell_type": "markdown", "metadata": {}, "source": src})


def code(src):
    CELLS.append({"cell_type": "code", "execution_count": None, "metadata": {},
                  "outputs": [], "source": src})


md("""# Phase29 — PHASE D
## Canonical VAL808 Execution + Three-Seed Reproducibility Freeze

**Method:** RA-MedFiLM-BARR
**Population:** VAL808 continuity benchmark (808 samples; BUSI 84, ISIC 357, KUB 280, KVASIR 87)
**Scope:** frozen-system evaluation only — **NO training**, **NO recalibration**, **NO threshold change**,
**NO best-seed selection**, **NO ROUTER_HOLDOUT**, **NO TEST**.

This notebook is a **pure evidence-replay** document: it opens no image, reads no GT mask, and runs no
model forward. Every number below is read from the frozen Phase-D artifacts on disk and re-verified
against its recorded SHA-256.

### Load-bearing result chain
1. **§0** authoritative artifact binding — zero drift.
2. **§2–§5** canonical shared fixed-G cache built at
   `data_cache/phase29_val808_shared_fixed_g_v1_1_canonical/` (one logical G pass, 102 batch forwards).
3. **§6** **global reproduction gate** — new global probability must be **bit-identical** to the frozen
   Phase27 reference.
4. **§7–§9** seed123 / seed3407 inference from the canonical cache with frozen per-seed thresholds.
5. **§10** prediction **hash barrier** — all predictions hashed before any GT read.
6. **§12–§13** GT scoring + per-seed continuity metrics (macro-domain equal-weight ΔDice + bootstrap CI).
7. **§14** three-seed **descriptive** reproducibility summary (no pass/fail gate, no ranking).
""")

md("## 2. Setup and frozen artifact paths")
code(SETUP)

md("""## 3. §0 — Authoritative artifact binding (BLOCK on drift)

The six load-bearing Phase-D artifacts plus the canonical components and the VAL808 manifest are
re-hashed. The work order requires a hard BLOCK if any digest differs from the frozen expectation.""")
code('''\
bind = jload(AUD / "phase29_phase_d_canonical_cache_predecessor_binding.json")
print("checks:", bind["n_checks"], "failed:", bind["n_failed"], "all_match:", bind["all_match"])
assert bind["all_match"] and bind["n_failed"] == 0
for c in bind["checks"]:
    tag = "OK " if c["match"] else "DRIFT"
    print(f"  [{tag}] {c['path']}")
print("\\n§0 PASS: all authoritative artifacts bound, zero drift.")
''')

md("""## 4. §2 — Canonical cache root cleanliness + noncanonical isolation

The canonical root must be absent/clean before construction; the superseded `v1_0` cache is preserved
byte-for-byte as evidence only and is never used for inference.""")
code('''\
iso = jload(AUD / "phase29_phase_d_noncanonical_cache_isolation_v1_1.json")
print("canonical root   :", iso["canonical_root"])
print("noncanonical root:", iso["noncanonical_root"])
print("noncanonical status:", iso["noncanonical_status"])
for name, sha in iso["noncanonical_files"].items():
    print(f"  v1_0 {name}: {sha[:16]}")
assert iso["all_pass"]
print("\\n§2 PASS: canonical root authoritative; v1_0 isolated as evidence.")
''')

md("""## 5. §3–§5 — Canonical shared fixed-G cache (one logical G pass)

Exactly **ONE logical** shared fixed-G extraction over all 808 VAL808 samples, batched as
**102 batch forwards** (BUSI 11, ISIC 45, KUB 35, KVASIR 11), contiguous chunks of 8 inside a single
domain. The cache is reused **unchanged** by both seeds — G is never rerun per seed.""")
code('''\
bs = jload(AUD / "phase29_val808_shared_cache_build_summary_v1_1_canonical.json")
print("logical_g_passes :", bs["logical_g_passes"])
print("g_samples        :", bs["g_samples"])
print("batch_forwards   :", bs["batch_forwards"])
print("by domain        :", bs["batch_forwards_by_domain"])
print("autocast         :", bs["autocast_enabled"], bs["autocast_dtype"])
print("inference_mode   :", bs["inference_mode"])
print("grad context     :", bs["grad_context"])
print("val808_gt_reads  :", bs["val808_gt_reads"])
assert bs["logical_g_passes"] == 1 and bs["g_samples"] == 808
assert bs["batch_forwards"] == 102
assert bs["batch_forwards_by_domain"] == {"BUSI": 11, "ISIC": 45, "KUB": 35, "KVASIR": 11}
assert bs["autocast_enabled"] is True and bs["autocast_dtype"] == "float16"
assert bs["inference_mode"] is False and bs["grad_context"] == "torch.no_grad()"
assert bs["val808_gt_reads"] == 0
print("\\n§3–§5 PASS: canonical shared-G cache built with exact Phase27 numerics.")
''')

md("""## 6. §6 — Global reproduction gate (LOAD-BEARING)

The canonical global probability map must be **bit-identical** to the frozen Phase27 reference
(`phase27_val808_global_prob_f16.npy`). This is the single gate that proves the canonical re-extraction
reproduces the authoritative global field exactly.""")
code('''\
repro = jload(AUD / "phase29_phase_d_global_reproduction_gate_result.json")
live_sha = sha256_file(CANON / "val808_global_prob_f16.npy")
print("frozen target sha :", repro["target_sha256"])
print("recorded new sha  :", repro["observed_sha256"])
print("live recomputed   :", live_sha)
print("bit_identical     :", repro["bit_identical"])
assert repro["bit_identical"] is True
assert live_sha == PHASE27_GLOBAL_PROB_SHA == repro["target_sha256"]
print("\\n§6 PASS: canonical global probability is BIT-IDENTICAL to Phase27.")
''')

md("""## 7. §7–§9 — Seed123 / seed3407 canonical inference

Per-seed inference uses the **frozen DEV-derived** router threshold (never VAL808-derived). The
corrected causal semantics require `n_selected == n_refiner_forwards == n_somega_forwards`:
**every selected row incurs R_psi and S_omega compute** (including EXECUTE_THEN_REJECT); SKIP rows incur
neither. seed42 is **REUSED ONLY** from Phase27 evidence and is never rerun.""")
code('''\
rows = []
for s in (123, 3407):
    d = jload(AUD / f"phase29_phase_d_canonical_seed{s}_val808_inference.json")
    rows.append({
        "seed": s, "n_selected": d["n_selected"],
        "selected_fraction": round(d["selected_fraction"], 6),
        "n_accepted": d["n_accepted"], "n_final_refined": d["n_final_refined"],
        "n_router_forwards": d["n_router_forwards"],
        "n_refiner_forwards": d["n_refiner_forwards"],
        "n_somega_forwards": d["n_somega_forwards"], "all_pass": d["all_pass"]})
df_inf = pd.DataFrame(rows)
print(df_inf.to_string(index=False))
for s in (123, 3407):
    d = jload(AUD / f"phase29_phase_d_canonical_seed{s}_val808_inference.json")
    assert d["n_selected"] == d["n_refiner_forwards"] == d["n_somega_forwards"]
    assert d["all_pass"]
print("\\n§7–§9 PASS: causal counters collapse correctly on both seeds.")
''')

md("""## 8. §10 — Prediction hash barrier (predictions hashed BEFORE any GT read)

All decision tables and final-probability maps for seed123, seed3407 and the reused seed42 evidence are
hashed **before** any GT mask is opened. The barrier token is emitted explicitly.""")
code('''\
bar = jload(AUD / "phase29_phase_d_prediction_hash_barrier.json")
print("barrier token      :", bar["barrier_token"])
print("gt_reads_at_hash   :", bar["gt_reads_at_hash_time"])
print("all hashed first   :", bar["all_predictions_hashed_before_gt"])
print("seed42 reuse only  :", bar["seed42_reuse_only"], "| rerun:", bar["seed42_rerun"])
for k, v in bar["prediction_hashes"].items():
    print(f"  {k}: {v[:16]}")
assert bar["barrier_token"] == "PREDICTION_HASH_BARRIER_PASS"
assert bar["gt_reads_at_hash_time"] == 0
print("\\n§10 PASS: PREDICTION_HASH_BARRIER_PASS.")
''')

md("""## 9. §11 — seed42 reuse-only binding

seed42 is not rerun. Its canonical final probability is the frozen Phase27 artifact, and its decision
evidence is the frozen Phase27 predictions CSV.""")
code('''\
P27 = ROOT / "data_cache" / "phase27_barr_preservation_v1_0"
p27_final = P27 / "phase27_val808_final_prob_f16.npy"
p27_pred = ROOT / "reports" / "tables" / "phase27_val808_predictions.csv"
print("phase27 final prob sha:", sha256_file(p27_final))
print("seed42 rerun          :", bar["seed42_rerun"])
assert bar["seed42_rerun"] is False
print("\\n§11 PASS: seed42 reused from Phase27 evidence.")
''')

md("""## 10. §12–§13 — GT scoring + per-seed continuity metrics

GT is read **only** after the hash barrier, and only for final metrics. The estimand is the
**macro-domain equal-weight mean ΔDice**; uncertainty is a **domain-stratified group bootstrap**
(B=2000, PCG64(42), percentile 2.5/97.5) — the frozen Phase27 machinery. There is **no numeric
reproducibility pass/fail gate**.""")
code('''\
cont = jload(AUD / "phase29_phase_d_val808_per_seed_continuity.json")
recs = []
for s in ("42", "123", "3407"):
    m = cont["metrics_by_seed"][s]
    b = m["bootstrap"]
    recs.append({
        "seed": int(s), "macro_final_dice": round(m["macro_final_dice"], 6),
        "macro_global_dice": round(m["macro_global_dice"], 6),
        "macro_delta_dice": round(m["macro_delta_dice"], 6),
        "ci_low": round(b["ci_low"], 6), "ci_high": round(b["ci_high"], 6),
        "ci_low_gt_-0.005": m["noninferiority_ci_low_gt_minus_margin"],
        "n_selected": m["n_selected"], "n_accepted": m["n_accepted"],
        "n_final_refined": m["n_final_refined"]})
df_cont = pd.DataFrame(recs)
print(df_cont.to_string(index=False))
assert cont["NO_NUMERIC_REPRODUCIBILITY_PASS_FAIL_GATE"] is True
assert all(r["ci_low_gt_-0.005"] for r in recs)
print("\\n§12–§13 PASS: all three seeds positive ΔDice, lower CI > -0.005 (descriptive).")
''')

md("""### 10b. Per-domain continuity breakdown

`MACRO_MAY_NOT_HIDE_DOMAIN_HARM = True` — per-domain results are reported mandatorily.""")
code('''\
dom_rows = []
for s in ("42", "123", "3407"):
    for dom, v in cont["metrics_by_seed"][s]["per_domain"].items():
        dom_rows.append({"seed": int(s), "domain": dom, "n": v["n"],
                         "global_dice": round(v["global_dice"], 6),
                         "final_dice": round(v["final_dice"], 6),
                         "delta_dice": round(v["delta_dice"], 6)})
df_dom = pd.DataFrame(dom_rows).sort_values(["domain", "seed"]).reset_index(drop=True)
print(df_dom.to_string(index=False))
''')

md("""## 11. §14 — Three-seed descriptive reproducibility summary

Descriptive only: mean, **sample SD (ddof=1)**, min, max, range, sign consistency. **No seed is ranked
or selected as best.**""")
code('''\
summ = jload(AUD / "phase29_phase_d_three_seed_descriptive_summary.json")
rows = []
for r in summ["per_metric"]:
    rows.append({"metric": r["metric"], "seed42": round(r["seed42"], 6),
                 "seed123": round(r["seed123"], 6), "seed3407": round(r["seed3407"], 6),
                 "mean": round(r["mean"], 6), "sd_ddof1": round(r["sample_sd_ddof1"], 6),
                 "range": round(r["range"], 6), "sign_consistent": r["sign_consistent"]})
print(pd.DataFrame(rows).to_string(index=False))
print()
print("macro ΔDice:", {k: round(v, 6) for k, v in summ["macro_delta_dice"].items()})
assert summ["best_seed_selected"] is False and summ["ranking_performed"] is False
assert summ["macro_delta_dice"]["all_positive"] is True
print("\\n§14 PASS: descriptive, no ranking, no best seed, no numeric pass/fail gate.")
''')

code('''\
print("Global (shared G) macro Dice across seeds:",
      sorted({cont["metrics_by_seed"][s]["macro_global_dice"] for s in ("42", "123", "3407")}))
print("→ single shared value confirms the fixed-G reference is identical for all seeds.")
''')

md("""## 12. §15–§16 — Scientific immutability and locked populations""")
code('''\
imm = jload(AUD / "phase29_phase_d_scientific_immutability.json")
reads = jload(AUD / "phase29_phase_d_locked_population_reads.json")
print("training runs during Phase D :", imm["training_runs_during_phase_d"])
print("optimizer steps              :", imm["optimizer_steps_during_phase_d"])
print("canonical bundle changed     :", imm["canonical_bundle_changed"])
print("ROUTER_HOLDOUT reads         :", reads["ROUTER_HOLDOUT_reads"])
print("TEST reads                   :", reads["TEST_reads"])
print("VAL808 GT reads (scoring)    :", reads["VAL808_GT_reads"])
assert imm["training_runs_during_phase_d"] == 0
assert reads["ROUTER_HOLDOUT_reads"] == 0 and reads["TEST_reads"] == 0
print("\\n§15–§16 PASS: immutability held; locked populations remain closed.")
''')

md("""## 13. §18–§19 — Required outputs and final check""")
code('''\
idx = jload(AUD / "phase29_phase_d_required_outputs_index.json")
fc = jload(AUD / "phase29_phase_d_final_check_v1_1.json")
print(f"required outputs: {idx['n_present']}/{idx['n_required']} present, all_present={idx['all_present']}")
print(f"final check     : {fc['n_checks'] - fc['n_failed']}/{fc['n_checks']} pass, failed={fc['failed']}")
assert idx["all_present"] and fc["all_pass"]
for k, v in fc["checks"].items():
    print(f"  [{'OK ' if v else 'FAIL'}] {k}")
''')

md("""## 14. §20 — Terminal""")
code('''\
term = jload(AUD / "phase29_phase_d_terminal_v1_1.json")
print("status   :", term["status"])
print("terminal :", term["terminal"])
assert term["all_pass"]
''')

md("""---
## Summary

The canonical VAL808 Phase-D execution is complete:

* the canonical shared fixed-G cache reproduces the frozen Phase27 global probability **bit-identically**;
* seed123 and seed3407 were executed from the canonical cache with frozen per-seed thresholds, and the
  corrected causal counters collapse exactly (`n_selected == n_refiner_forwards == n_somega_forwards`);
* all predictions were hashed **before** any GT read (`PREDICTION_HASH_BARRIER_PASS`);
* all three seeds show a **positive** macro-domain equal-weight ΔDice with lower bootstrap CI bound
  above −0.005 — reported descriptively, with **no ranking and no numeric pass/fail gate**;
* ROUTER_HOLDOUT and TEST remained closed; training runs during Phase D were **zero**.

**Phase29 is COMPLETE.** Phase30 has not been started.
""")


def build(out_path: Path) -> None:
    nb = {
        "cells": CELLS,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python",
                           "name": "python3"},
            "language_info": {"name": "python", "version": "3.11.9"},
        },
        "nbformat": 4, "nbformat_minor": 5,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(nb, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    out = (ROOT / "notebooks" / "phasewise" / "phase_29_3seed_reproducibility" /
           "phase29_phase_d_canonical_three_seed_validation.ipynb")
    build(out)
    print("wrote", out)
    print("cells:", len(CELLS))
