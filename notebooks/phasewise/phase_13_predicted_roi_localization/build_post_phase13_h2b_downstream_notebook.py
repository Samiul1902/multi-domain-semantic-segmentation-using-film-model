"""Build the H2B-B2 downstream reviewer notebook (READ-ONLY on rerun)."""
from pathlib import Path

import nbformat

ROOT = Path(r"D:\Softfors\jup")
NB = (ROOT / "notebooks/phasewise/phase_13_predicted_roi_localization"
      / "post_phase13_h2b_downstream_analysis.ipynb")
EID = ("post_phase13_h2b_kub_localizer_r512_h128_sigmaeq075_"
       "softtargetfocalgamma2_deploymentbalance_seed42_clean_v3")


def md(t):
    return nbformat.v4.new_markdown_cell(t)


def code(s):
    return nbformat.v4.new_code_cell(s)


cells = []

cells.append(md("""# POST-PHASE-13 H2-B-B2 — Downstream Regional Segmentation Analysis

## 1. Governance / Branch Identity

READ-ONLY on rerun. No training, no localizer inference, no hidden segmentation inference —
this notebook only reads on-disk artifacts produced by the H2B-B2 execution.

Branch: Phase 13 `REVISE_LOCALIZER` → H1 `CLOSED__PARTIAL_MITIGATION_INSUFFICIENT` →
H2A `CLOSED__SELECTION_REDESIGN_PARTIAL` → **H2B objective-only redesign**.

Run id: `post_phase13_h2b_downstream_best_native_policy`.
"""))

cells.append(code("""
import hashlib, json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams["figure.dpi"] = 100
plt.rcParams["figure.figsize"] = (10, 5)

ROOT = Path(r"D:\\Softfors\\jup")
AUDITS = ROOT / "reports" / "audits"
TABLES = ROOT / "reports" / "tables"
EID = ("post_phase13_h2b_kub_localizer_r512_h128_sigmaeq075_"
       "softtargetfocalgamma2_deploymentbalance_seed42_clean_v3")

def sha(p):
    p = Path(p)
    if not p.is_absolute():
        p = ROOT / p
    return hashlib.sha256(p.read_bytes()).hexdigest()

integ = json.loads((AUDITS / "post_phase13_h2b_b2_downstream_integrity.json").read_text("utf-8"))
case = pd.read_csv(TABLES / "post_phase13_h2b_downstream_case_model_metrics.csv")
comp = pd.read_csv(TABLES / "post_phase13_h2b_downstream_component_model_metrics.csv")
summary = pd.read_csv(TABLES / "post_phase13_h2b_downstream_model_summary.csv")
cross = pd.read_csv(TABLES / "post_phase13_h2b_downstream_cross_architecture_summary.csv")
link = pd.read_csv(TABLES / "post_phase13_h2b_localizer_to_downstream_comparison.csv")
print("Environment OK | case rows:", len(case), "| component rows:", len(comp))
"""))

cells.append(md("""## 2. H2B Objective-Only Rationale

H2A returned `H2A_SELECTION_REDESIGN_PARTIAL`: checkpoint selection improved the localizer but
left a substantial off-target proposal burden. H2B tests whether a **soft-target objective**
(`SoftTargetFocalBCE`, gamma=2.0) improves heatmap discrimination with everything else frozen.
This notebook evaluates whether that objective-level change translates into downstream regional
segmentation behaviour.
"""))

cells.append(md("## 3. B1 Best-Checkpoint Identity"))
cells.append(code("""
te = json.loads((AUDITS / "post_phase13_h2b_b1_training_evaluation.json").read_text("utf-8"))
print("experiment_id:", te["experiment_id"])
print("best epoch:", te["termination"]["best_epoch"], "| completed epochs:", te["termination"]["completed_epochs"])
print("termination:", te["termination"]["reason"])
print("best.pt SHA:", te["hashes"]["best_pt_sha"])
print("history SHA:", te["hashes"]["history_sha"])
print("loss:", te["loss"]["class"], "| gamma:", te["loss"]["gamma"])
"""))

cells.append(md("## 4. B1 Interruption / Resume Provenance"))
cells.append(code("""
h = pd.read_csv(ROOT / "experiments" / EID / "history.csv")
print("history rows:", len(h))
print("contiguous 1..N:", bool((h.epoch.diff().dropna() == 1).all()) and int(h.epoch.iloc[0]) == 1)
print("duplicate epochs:", int(h.epoch.duplicated().sum()))
print("logical_scientific_experiment_count:", te["counters"]["logical_training_experiments"])
print("execution_attempt_count:", te["counters"]["execution_attempt_count"])
print("note: first attempt was interrupted mid-epoch 44 and resumed with --resume (not a second experiment).")
"""))

cells.append(md("## 5. B1 Selection Replay"))
cells.append(code("""
rp = json.loads((AUDITS / "post_phase13_h2b_b1_selection_replay_verification.json").read_text("utf-8"))
print("status:", rp["status"], "| mismatches:", rp["mismatch_count"])
print("best epoch replayed/stored:", rp["replayed"]["best_epoch"], "/", rp["stored"]["best_epoch"])
print("max abs term diff:", rp["max_abs_term_diff"])
print("final bad epochs:", rp["replayed"]["final_bad_epochs"])
"""))

cells.append(md("## 6. Frozen 488-Proposal Identity"))
cells.append(code("""
prop = pd.read_csv(TABLES / "post_phase13_h2b_best_checkpoint_proposals.csv")
pcase = pd.read_csv(TABLES / "post_phase13_h2b_best_checkpoint_case_proposals.csv")
pcomp = pd.read_csv(TABLES / "post_phase13_h2b_best_checkpoint_component_coverage.csv")
print("proposals:", len(prop), "| cases:", len(pcase), "| components:", len(pcomp))
print("proposal config: threshold=0.10 margin=0.20 top_k=5 NMS=0.30")
assert len(prop) == 488 and len(pcase) == 103 and len(pcomp) == 152
print("CONFIRMED: 488 frozen H2B proposals (authoritative downstream identity)")
"""))

cells.append(md("## 7. H2B vs H2A Localizer Comparison"))
cells.append(code("""
l2 = pd.read_csv(TABLES / "post_phase13_h2b_vs_h2a_localizer_comparison.csv")
print(l2.to_string(index=False))
"""))

cells.append(md("## 8. Segmentation Checkpoint Bindings"))
cells.append(code("""
for k, v in integ["segmentation_checkpoint_shas"].items():
    print(f"  {k:<18} {v}")
"""))

cells.append(md("## 9. Global Cache Reproduction"))
cells.append(code("""
print("manifest SHA:", integ["global_cache_manifest_sha"])
print("expected    : 76e1034d2bc7925260af33826fc19565b2d5ef786c612a7ad71f3bde46fb89a8")
print("global reproduction:", integ["global_reproduction"])
"""))

cells.append(md("""## 10. Crop / Restore

Native valid region → zero-pad to full square → 512 bilinear → [0,1]. Restore: 512 regional
probability → full square bilinear (`align_corners=False`) → strip pad → native coordinates.
The frozen proposal margin is already baked into the proposal geometry — never applied twice.
"""))
cells.append(code("""
print("Part1D helper SHA:", integ["part1d_helper_sha"])
print("expected          : 8cd7e39814a049a025f706c57ccea0b535a230908a177690d6289318234c6284")
"""))

cells.append(md("""## 11. Fusion

`U_H2B` = union of clipped H2B proposal rectangles. Regional overlap: **MAX among regional
predictions only**. Final: `P(x) = R(x)` inside `U_H2B`, `P(x) = G(x)` outside. **Never**
`max(G,R)`. Zero proposals → `P == G` exactly. Threshold 0.5 after native fusion.
"""))
cells.append(code("""
print("regional crop evaluations:", integ["regional_crop_evaluations"], "/ 1952")
print("localizer forwards:", integ["localizer_forwards"])
print("proposal regeneration:", integ["proposal_regeneration"])
print("new global forwards:", integ["new_global_forwards"])
"""))

cells.append(md("## 12. Downstream Model Summary"))
cells.append(code("""
pd.set_option("display.max_columns", None); pd.set_option("display.width", 0)
print(summary.to_string(index=False))
"""))

cells.append(md("## 13. GLOBAL vs H2B"))
cells.append(code("""
cols = ["model_display", "global_macro_dice", "h2b_predicted_macro_dice", "DELTA_H2B_GLOBAL_DICE",
        "global_macro_precision", "h2b_predicted_macro_precision", "global_macro_recall",
        "h2b_predicted_macro_recall", "mean_global_fp", "mean_h2b_fp", "mean_global_fn", "mean_h2b_fn",
        "cases_improved_vs_global", "cases_same_vs_global", "cases_worse_vs_global"]
print(summary[cols].to_string(index=False))
"""))

cells.append(md("## 14. Phase13 vs H2B"))
cells.append(code("""
cols = ["model_display", "phase13_predicted_macro_dice", "h2b_predicted_macro_dice",
        "DELTA_H2B_PHASE13_DICE", "mean_phase13_fp", "mean_h2b_fp", "mean_phase13_fn", "mean_h2b_fn",
        "cases_improved_vs_phase13", "cases_same_vs_phase13", "cases_worse_vs_phase13"]
print(summary[cols].to_string(index=False))
"""))

cells.append(md("## 15. H2A vs H2B"))
cells.append(code("""
cols = ["model_display", "h2a_predicted_macro_dice", "h2b_predicted_macro_dice",
        "DELTA_H2B_H2A_DICE", "fp_delta_vs_h2a",
        "cases_improved_vs_h2a", "cases_same_vs_h2a", "cases_worse_vs_h2a",
        "component_recoveries_vs_h2a", "component_losses_vs_h2a"]
print(summary[cols].to_string(index=False))
"""))

cells.append(md("## 16. ORACLE vs H2B"))
cells.append(code("""
cols = ["model_display", "oracle_macro_dice", "h2b_predicted_macro_dice", "H2B_ORACLE_GAP",
        "ORACLE_GAIN_FROM_GLOBAL", "H2B_ORACLE_BENEFIT_RETENTION"]
print(summary[cols].to_string(index=False))
"""))

cells.append(md("## 17. Dice / IoU"))
cells.append(code("""
fig, axes = plt.subplots(1, 2, figsize=(13, 4))
for ax, m in zip(axes, ["dice", "iou"]):
    x = np.arange(len(summary)); w = 0.2
    ax.bar(x - w, summary[f"global_macro_{m}"], w, label="GLOBAL")
    ax.bar(x, summary[f"phase13_predicted_macro_{m}"], w, label="Phase13")
    ax.bar(x + w, summary[f"h2a_predicted_macro_{m}"], w, label="H2A")
    ax.bar(x + 2*w, summary[f"h2b_predicted_macro_{m}"], w, label="H2B")
    ax.set_xticks(x); ax.set_xticklabels(summary["model_display"], rotation=15, ha="right")
    ax.set_title(m.capitalize()); ax.legend()
plt.tight_layout(); plt.show()
"""))

cells.append(md("## 18. Precision / Recall"))
cells.append(code("""
fig, axes = plt.subplots(1, 2, figsize=(13, 4))
for ax, m in zip(axes, ["precision", "recall"]):
    x = np.arange(len(summary)); w = 0.2
    ax.bar(x - w, summary[f"global_macro_{m}"], w, label="GLOBAL")
    ax.bar(x, summary[f"phase13_predicted_macro_{m}"], w, label="Phase13")
    ax.bar(x + w, summary[f"h2a_predicted_macro_{m}"], w, label="H2A")
    ax.bar(x + 2*w, summary[f"h2b_predicted_macro_{m}"], w, label="H2B")
    ax.set_xticks(x); ax.set_xticklabels(summary["model_display"], rotation=15, ha="right")
    ax.set_title(m.capitalize()); ax.legend()
plt.tight_layout(); plt.show()
"""))

cells.append(md("## 19. FP / FN"))
cells.append(code("""
fig, axes = plt.subplots(1, 2, figsize=(13, 4))
for ax, m in zip(axes, ["fp", "fn"]):
    x = np.arange(len(summary)); w = 0.2
    ax.bar(x - w, summary[f"mean_global_{m}"], w, label="GLOBAL")
    ax.bar(x, summary[f"mean_phase13_{m}"], w, label="Phase13")
    ax.bar(x + w, summary[f"mean_h2a_{m}"], w, label="H2A")
    ax.bar(x + 2*w, summary[f"mean_h2b_{m}"], w, label="H2B")
    ax.set_xticks(x); ax.set_xticklabels(summary["model_display"], rotation=15, ha="right")
    ax.set_title(f"Mean {m.upper()} (pixels)"); ax.legend()
plt.tight_layout(); plt.show()
"""))

cells.append(md("## 20. Component Recoveries / Losses"))
cells.append(code("""
cols = ["model_display", "component_recoveries_vs_global", "component_losses_vs_global",
        "component_recoveries_vs_phase13", "component_losses_vs_phase13",
        "component_recoveries_vs_h2a", "component_losses_vs_h2a"]
print(summary[cols].to_string(index=False))
"""))

cells.append(md("## 21. Empty Recoveries / New Empties"))
cells.append(code("""
print(summary[["model_display", "empty_recoveries", "new_empty_predictions"]].to_string(index=False))
"""))

cells.append(md("""## 22. Oracle-Benefit Retention

`H2B_ORACLE_BENEFIT_RETENTION = (H2B_Dice - GLOBAL_Dice) / (ORACLE_Dice - GLOBAL_Dice)`,
descriptive only. No success threshold; not redefined after seeing results.
"""))
cells.append(code("""
print(summary[["model_display", "H2B_ORACLE_BENEFIT_RETENTION", "H2B_ORACLE_GAP"]].to_string(index=False))
"""))

cells.append(md("## 23. Size Strata"))
cells.append(code("""
st = comp.groupby(["model", "size_stratum"]).agg(
    n=("native_component_id", "count"),
    global_detected=("global_detected", "sum"),
    h2b_detected=("h2b_predicted_detected", "sum"),
    h2a_detected=("h2a_predicted_detected", "sum"),
    recoveries=("GLOBAL_TO_H2B_RECOVERY", "sum"),
    losses=("GLOBAL_TO_H2B_LOSS", "sum")).reset_index()
print(st.to_string(index=False))
"""))

cells.append(md("## 24. Frozen Hard-Tiny"))
cells.append(code("""
ht = comp[comp["hard_tiny"]].groupby("model").agg(
    n=("native_component_id", "count"), global_detected=("global_detected", "sum"),
    h2b_detected=("h2b_predicted_detected", "sum"), h2a_detected=("h2a_predicted_detected", "sum"),
    recoveries=("GLOBAL_TO_H2B_RECOVERY", "sum"), losses=("GLOBAL_TO_H2B_LOSS", "sum"))
print(ht)
"""))

cells.append(md("""## 25. Frozen Global-Empty

5 frozen images containing 8 native components — reported as
`GLOBAL_EMPTY_COMPONENTS_WITHIN_5_FROZEN_IMAGES`, never as "8 global-empty images".
"""))
cells.append(code("""
ge = comp[comp["global_empty_image"]].groupby("model").agg(
    n=("native_component_id", "count"), global_detected=("global_detected", "sum"),
    h2b_detected=("h2b_predicted_detected", "sum"), h2a_detected=("h2a_predicted_detected", "sum"),
    recoveries=("GLOBAL_TO_H2B_RECOVERY", "sum"), losses=("GLOBAL_TO_H2B_LOSS", "sum"))
print("GLOBAL_EMPTY_COMPONENTS_WITHIN_5_FROZEN_IMAGES")
print(ge)
"""))

cells.append(md("## 26. Multi-Component"))
cells.append(code("""
mc = comp[comp["multi_component_image"]].groupby("model").agg(
    n=("native_component_id", "count"), global_detected=("global_detected", "sum"),
    h2b_detected=("h2b_predicted_detected", "sum"), recoveries=("GLOBAL_TO_H2B_RECOVERY", "sum"),
    losses=("GLOBAL_TO_H2B_LOSS", "sum"))
print(mc)
"""))

cells.append(md("## 27. Cross-Architecture Consistency"))
cells.append(code("""
print(cross.to_string(index=False))
"""))

cells.append(md("""## 28. Localizer → Downstream Translation

**No monotonic causality is claimed.** This table exists only to show whether the H2B
objective-level localizer changes translate into downstream regional segmentation behaviour.
"""))
cells.append(code("""
pd.set_option("display.max_columns", None); pd.set_option("display.width", 0)
print(link.to_string(index=False))
"""))

cells.append(md("""## 29. Limitations

1. Single-seed adaptive VAL-development evaluation.
2. H2B is worse than H2A on every frozen localizer proposal-quality metric; the downstream
   evaluation inherits that starting point.
3. Proposal scores are fully saturated (score IQR 0.0 at the B1 best checkpoint).
4. Descriptive comparison only — no statistical superiority claim, no winner.
5. No threshold search, no proposal grid, no H1 filtering.
6. TEST remains untouched; these are development-data results only.
"""))

cells.append(md("""## 30. Adaptive VAL-Development Disclosure

H2B is adaptive VAL development undertaken after upstream regional-revision evidence. The
`SoftTargetFocalBCE(gamma=2.0)` objective was frozen **before** H2B training. The H2B best
checkpoint was frozen **before** downstream evaluation. No proposal threshold or search was
performed. No H2B result substitutes for final TEST evaluation. TEST remains untouched.
"""))

cells.append(md("""## 31. Adjudication Stop Boundary

**This notebook does NOT adjudicate H2B.**

The execution returns evidence only. H2B outcome adjudication is a separate supervisor step.

Not authorized and not performed: H2B sufficiency/partial/insufficiency declarations, winner,
optimal loss, superiority, GO/NO_GO, regional mechanism promotion, Phase14/H2C/H3 authorization,
TEST access.
"""))

cells.append(md("## 32. Artifact SHA Registry"))
cells.append(code("""
artifacts = [
    "reports/audits/post_phase13_h2b_protocol_frozen.json",
    "reports/audits/post_phase13_h2b_b1_training_evaluation.json",
    "reports/audits/post_phase13_h2b_b1_selection_replay_verification.json",
    "reports/audits/post_phase13_h2b_best_checkpoint_standalone_evaluation.json",
    "reports/audits/post_phase13_h2b_b2_downstream_integrity.json",
    "reports/tables/post_phase13_h2b_best_checkpoint_case_proposals.csv",
    "reports/tables/post_phase13_h2b_best_checkpoint_proposals.csv",
    "reports/tables/post_phase13_h2b_best_checkpoint_component_coverage.csv",
    "reports/tables/post_phase13_h2b_best_checkpoint_size_stratified.csv",
    "reports/tables/post_phase13_h2b_vs_h2a_localizer_comparison.csv",
    "reports/tables/post_phase13_h2b_downstream_case_model_metrics.csv",
    "reports/tables/post_phase13_h2b_downstream_component_model_metrics.csv",
    "reports/tables/post_phase13_h2b_downstream_model_summary.csv",
    "reports/tables/post_phase13_h2b_downstream_cross_architecture_summary.csv",
    "reports/tables/post_phase13_h2b_localizer_to_downstream_comparison.csv",
]
for a in artifacts:
    p = ROOT / a
    print(f"{sha(p) if p.exists() else 'MISSING':64s}  {Path(a).name}")
"""))

# complete untruncated tables
cells.append(md("""## 33. Mandatory Complete Tables (Untruncated)

Rendered in full — no `head()`, no `tail()`, no notebook ellipsis.
"""))
cells.append(code("""
_pd = pd
_pd.set_option("display.max_rows", None); _pd.set_option("display.max_columns", None)
_pd.set_option("display.width", 0); _pd.set_option("display.max_colwidth", None)

print("=" * 100); print(f"MODEL SUMMARY — {len(summary)} / 4 rows"); print("=" * 100)
print(summary.to_string(index=False)); print()
assert len(summary) == 4, f"model summary rows {len(summary)} != 4"
"""))
cells.append(code("""
print("=" * 100); print(f"CASE-MODEL METRICS — {len(case)} / 412 rows (103 cases x 4 models)"); print("=" * 100)
print(case.to_string(index=False)); print()
assert len(case) == 412, f"case rows {len(case)} != 412"
assert case["sample_id"].nunique() == 103 and case["model"].nunique() == 4
print(f"CONFIRMED: {len(case)} rows | {case['sample_id'].nunique()} cases | {case['model'].nunique()} models")
"""))
cells.append(code("""
print("=" * 100); print(f"COMPONENT-MODEL METRICS — {len(comp)} / 608 rows (152 components x 4 models)"); print("=" * 100)
print(comp.to_string(index=False)); print()
assert len(comp) == 608, f"component rows {len(comp)} != 608"
print(f"CONFIRMED: {len(comp)} rows | {comp['model'].nunique()} models")
"""))

nb = nbformat.v4.new_notebook(cells=cells)
for _i, _c in enumerate(nb.cells):
    _c["id"] = f"h2bb2{_i:03d}"
nbformat.write(nb, str(NB))
print(f"wrote {len(cells)} cells -> {NB}")
