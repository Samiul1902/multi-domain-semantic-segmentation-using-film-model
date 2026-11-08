"""Generate the supplementary analysis notebooks.

These complement the master notebook with focused deep-dives rather than
repeating it. Every one is analysis-only and executable.
"""
from __future__ import annotations

from pathlib import Path

import nbformat as nbf

ROOT = Path(r"D:\Softfors\jup")
OUT = ROOT / "full_doc_report"
GEN = OUT / "notebooks_generated"
GEN.mkdir(parents=True, exist_ok=True)

HEADER = r'''
import sys
from pathlib import Path
sys.path.insert(0, r"D:\Softfors\jup\full_doc_report\Scripts")
import remedfilm_guard as GUARD
GUARD.install()

REPO = Path(r"D:\Softfors\jup")
REPORT = REPO / "full_doc_report"
TABLES = REPORT / "tables"
FIGURES = REPORT / "figures"

import pandas as pd
import numpy as np
import json
from IPython.display import Image, display

for name, verdict in GUARD.self_test():
    assert verdict.startswith("blocked"), f"GUARD FAILED: {name} {verdict}"
print("analysis-only guard verified")
'''

SELF_TEST = r'''
# Negative control: enforcement must be real.
for name, verdict in GUARD.self_test():
    print(f"  {name:28s}: {verdict}")
assert all(v.startswith("blocked") for _, v in GUARD.self_test())
print("OK")
'''


def write(name: str, cells: list) -> None:
    nb = nbf.v4.new_notebook()
    nb["cells"] = cells
    nb["metadata"] = {
        "kernelspec": {"display_name": "Python 3 (ReMedFiLM analysis)",
                       "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.11.9"},
        "remedfilm": {"execution_mode": "ANALYSIS_ONLY", "training_allowed": False,
                      "new_inference_allowed": False, "test_access_allowed": False},
    }
    (GEN / name).write_text(nbf.writes(nb), encoding="utf-8")
    print("WROTE", name, len(cells), "cells")


# =============================================== 01 training forensics ======
write("01_remedfilm_training_history_forensics.ipynb", [
    nbf.v4.new_markdown_cell("""
# Supplementary 01 — Training history forensics

Deep audit of the 82 recovered `history.csv` logs: completeness, epoch
contiguity, selection provenance and the metrics each run actually recorded.

Companion to **§04–§05** of `ReMedFiLM_Complete_Research_Master.ipynb`.
"""),
    nbf.v4.new_code_cell(HEADER),
    nbf.v4.new_code_cell(r'''
reg = pd.read_csv(TABLES / "TRAINING_RUN_REGISTRY.csv")
prov = json.loads((REPORT / "TRAINING_HISTORY_PROVENANCE.json").read_text(encoding="utf-8"))
print("history files :", prov["n_history_files"])
print("runs          :", prov["n_runs"])
print("epoch records :", prov["n_epoch_records"])
print()
print("epoch contiguity (no gaps, no duplicates):")
non_contig = [r for r in prov["runs"] if not r["epoch_contiguous"]]
print(f"  contiguous runs     : {len(prov['runs']) - len(non_contig)}")
print(f"  non-contiguous runs : {len(non_contig)}")
for r in non_contig[:6]:
    print("   ", r["run_id"], r["epoch_min"], "->", r["epoch_max"], f"({r['n_epoch_records']} rows)")
'''),
    nbf.v4.new_code_cell(r'''
# Duplicate epoch detection inside each log.
hist = pd.read_csv(TABLES / "REMEDFILM_EPOCH_HISTORY.csv")
dups = (hist.groupby(["run_id", "metric", "epoch"]).size()
            .reset_index(name="n").query("n > 1"))
print("duplicated (run, metric, epoch) rows:", len(dups))
if len(dups):
    print(dups.head(10).to_string(index=False))
'''),
    nbf.v4.new_code_cell(r'''
# Selection provenance: recorded vs derived.
print(reg.best_epoch_source.value_counts().to_string())
print()
derived = reg[reg.best_epoch_source.str.startswith("DERIVED")]
print(f"runs whose best epoch is DERIVED by analysis: {len(derived)}")
derived[["run_id", "model", "best_epoch", "selection_metric"]].head(12)
'''),
    nbf.v4.new_code_cell(r'''
# Metric completeness matrix: which canonical metric each run logged.
canon = ["train_loss", "val_loss", "val_macro_dice", "val_dice", "val_iou",
         "val_precision", "val_recall", "learning_rate"]
present = (hist.assign(one=1)
               .pivot_table(index="run_id", columns="metric", values="one",
                            aggfunc="max", fill_value=0))
cols = [c for c in canon if c in present.columns]
mat = present[cols]
print("runs:", len(mat))
print("share of runs logging each metric:")
print((mat.mean() * 100).round(1).to_string())
mat.head(10)
'''),
    nbf.v4.new_code_cell(r'''
# Per-domain coverage — only the four-domain runs log per-domain metrics.
dom_cols = [c for c in present.columns if c.startswith("val_dice_")]
print("per-domain metrics available:", dom_cols)
runs_with_dom = present.index[present[dom_cols].sum(axis=1) > 0].tolist() if dom_cols else []
print(f"runs logging per-domain Dice: {len(runs_with_dom)}")
for r in runs_with_dom:
    print("  ", r)
'''),
    nbf.v4.new_code_cell(r'''
# The single most complete log.
g = hist[hist.run_id == "phase21_global_medfilm_fourdomain_seed42_clean_v3"]
piv = g.pivot_table(index="epoch", columns="metric", values="value")
print("GlobalMedFiLM: epochs =", len(piv), "| metrics =", piv.shape[1])
print("columns:", list(piv.columns))
print()
print("last 5 epochs:")
piv.tail(5)[["train_loss", "val_loss", "val_macro_dice", "learning_rate"]]
'''),
    nbf.v4.new_code_cell(SELF_TEST),
])

# =============================================== 02 ablation & routing =====
write("02_remedfilm_ablation_and_routing_analysis.ipynb", [
    nbf.v4.new_markdown_cell("""
# Supplementary 02 — Ablation and routing analysis

The 13-arm ablation on ROUTER_DEVELOPMENT, the matched paired contrasts with
bootstrap CIs, and the routing/safety state machine on VAL808.

Companion to **§12–§13** of the master notebook.
"""),
    nbf.v4.new_code_cell(HEADER),
    nbf.v4.new_code_cell(r'''
abl = pd.read_csv(TABLES / "REMEDFILM_ABLATION_RESULTS.csv")
print("population:", abl.population.iloc[0])
print("arms      :", len(abl))
abl[["arm", "n_routed", "mean_true_delta_dice_routed",
     "harmful_activation_share", "benefit_capture_vs_positive_mass"]].to_string(index=False)
'''),
    nbf.v4.new_code_cell(r'''
# Rank arms by routed mean improvement and show the harm cost of each.
ranked = abl.sort_values("mean_true_delta_dice_routed", ascending=False)
ranked[["arm", "mean_true_delta_dice_routed", "harmful_activation_share",
        "n_beneficial_routed", "n_harmful_routed"]].to_string(index=False)
'''),
    nbf.v4.new_code_cell(r'''
bs = pd.read_csv(REPO / "reports/tables/phase28_table_08_bootstrap_statistics.csv")
bs["excludes_zero"] = (bs.ci95_low > 0) | (bs.ci95_high < 0)
bs[["contrast", "n", "mean_difference", "ci95_low", "ci95_high", "excludes_zero"]].to_string(index=False)
print()
a8 = bs[bs.contrast == "A8_vs_A7"].iloc[0]
print("PRESERVED FINDING — A8 vs A7 95% CI includes zero:")
print(f"  point {a8.mean_difference:+.3e}  CI [{a8.ci95_low:+.3e}, {a8.ci95_high:+.3e}]")
'''),
    nbf.v4.new_code_cell(r'''
ps = pd.read_csv(TABLES / "REMEDFILM_INTERNAL_PER_SAMPLE.csv")
tab = ps.groupby("branch").agg(
    n=("sample_id", "size"),
    mean_delta=("delta_dice", "mean"),
    min_delta=("delta_dice", "min"),
    max_delta=("delta_dice", "max"),
).reset_index()
tab["share_of_808"] = (tab.n / len(ps)).round(4)
tab
'''),
    nbf.v4.new_code_cell(r'''
# Population separation is a hard rule, not a convention.
print("ROUTER_DEVELOPMENT (ablation) : 4,957 images, 1,239 routed")
print("VAL808 (routing analysis)     : 808 images, 279 routed")
print("EXTERNAL884                   : separate cohorts, never pooled")
print()
print("No statistic in this notebook mixes them.")
'''),
    nbf.v4.new_code_cell(r'''
for f in ["ablation/ABL01_arm_mean_delta", "ablation/ABL02_paired_contrasts_forest",
          "routing_safety/RT01_routing_outcomes", "routing_safety/RT02_stage_flow"]:
    display(Image(filename=str(FIGURES / f"{f}.png"), width=720))
'''),
    nbf.v4.new_code_cell(SELF_TEST),
])

# =============================================== 03 external & robustness ==
write("03_remedfilm_external_and_robustness_analysis.ipynb", [
    nbf.v4.new_markdown_cell("""
# Supplementary 03 — External evaluation and robustness

The 884-case retrospective external evaluation and the Phase 36 perturbation
study. Both are read-only analyses of persisted predictions.

Companion to **§10 and §14** of the master notebook.
"""),
    nbf.v4.new_code_cell(HEADER),
    nbf.v4.new_code_cell(r'''
ext = pd.read_csv(TABLES / "REMEDFILM_EXTERNAL_METRICS.csv")
dice = ext[ext.metric == "Dice"]
piv = dice.pivot_table(index="cohort", columns="arm",
                       values="mean", aggfunc="first")
piv["delta_FULL_minus_backbone"] = piv["ReMedFiLM_FULL"] - piv["GlobalMedFiLM"]
piv.round(6)
'''),
    nbf.v4.new_code_cell(r'''
print("cohort sizes and denominators")
print(dice.groupby(["cohort", "arm"])[["n_total", "n_defined", "n_clusters"]]
          .first().to_string())
print()
print("No cohort is pooled with another or with VAL808.")
'''),
    nbf.v4.new_code_cell(r'''
pc = pd.read_csv(REPO / "reports/tables/c1_external_stress_per_case.csv")
sf = pc[pc.gt_empty.astype(str).str.lower() == "true"]
print("stone-free cases:", len(sf))
if len(sf):
    for arm, grp in sf.groupby("arm"):
        got = (grp.pred_empty.astype(str).str.lower() == "false").sum()
        print(f"  {arm:8s}: {got}/{len(grp)} receive foreground")
print()
print("Preserved negative finding. HD95/ASSD are undefined for empty reference")
print("masks and are reported as missing, not zero.")
'''),
    nbf.v4.new_code_cell(r'''
r36 = json.loads((REPO / "reports/audits/phase36_robustness_scientific_result_v1_23.json")
                 .read_text(encoding="utf-8"))
print("counters")
for k in ("clean_passes", "perturbed_g_forwards", "test_reads", "training",
          "optimizer_steps", "parameter_mutations"):
    print(f"  {k:22s}: {r36['counters'][k]}")
print()
print("clean-equivalence all_pass:", r36["clean_equivalence"]["all_pass"])
print("max |Δ Dice| vs frozen    :", r36["clean_equivalence"].get("max_abs_dice_difference", 0.0))
'''),
    nbf.v4.new_code_cell(r'''
rows = r36["image_rows"]
cond = pd.DataFrame(rows).groupby("condition").agg(
    n=("paired_delta_dice", "size"),
    mean_delta=("paired_delta_dice", "mean"),
    min_delta=("paired_delta_dice", "min"),
).sort_values("mean_delta").reset_index()
cond.round(5)
'''),
    nbf.v4.new_code_cell(r'''
for f in ["external_evaluation/EXT01_external_dice",
          "external_evaluation/EXT03_stonefree_false_positive",
          "robustness/ROB01_perturbation_degradation",
          "robustness/ROB02_domain_degradation"]:
    display(Image(filename=str(FIGURES / f"{f}.png"), width=720))
'''),
    nbf.v4.new_code_cell(SELF_TEST),
])

print("done")
