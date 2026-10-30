"""Build the H2A-B2 downstream reviewer notebook."""
import json
from pathlib import Path

import nbformat

ROOT = Path(r"D:\Softfors\jup")
NB = (ROOT / "notebooks/phasewise/phase_13_predicted_roi_localization"
      / "post_phase13_h2a_downstream_analysis.ipynb")

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def md(text: str):
    return nbformat.v4.new_markdown_cell(text)

def code(source: str):
    return nbformat.v4.new_code_cell(source)

# ---------------------------------------------------------------------------
# Notebook cells
# ---------------------------------------------------------------------------
cells = []

# 1. Governance / adaptive-development disclosure
cells.append(md("""# POST-PHASE-13 H2-A-B2 — Downstream Regional Segmentation Analysis

## 1. Governance / Adaptive-Development Disclosure

This notebook is READ-ONLY. It contains no training, no localizer inference, and no segmentation inference.

H2A is an adaptive VAL-development revision undertaken after:
- Phase 13 `REVISE_LOCALIZER`
- H1 acceptance-only insufficiency

The H2A checkpoint-selection rule was frozen before H2A-B1 training.
The downstream protocol was frozen before H2A-B2 segmentation execution.

No H2A downstream result substitutes for final TEST evaluation.
TEST remains untouched.
"""))

cells.append(code("""
import hashlib, json, sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams["figure.dpi"] = 100
plt.rcParams["figure.figsize"] = (10, 5)

ROOT = Path(r"D:\Softfors\jup")
TABLES = ROOT / "reports" / "tables"
AUDITS = ROOT / "reports" / "audits"

def sha(p):
    p = Path(p)
    if not p.is_absolute():
        p = ROOT / p
    return hashlib.sha256(p.read_bytes()).hexdigest()

print("Environment OK")
"""))

# 2. H2A scientific question
cells.append(md("""## 2. H2A Scientific Question

> Does the H2A deployment-balanced checkpoint selection improve the complete GT-free predicted-region segmentation path when EVERYTHING downstream is held fixed?

Authorized:
- frozen H2A epoch-83 proposals
- four frozen segmentation architectures
- frozen global cache
- frozen fusion semantics

Not authorized (and not performed):
- localizer training / forward / proposal regeneration
- H1 filtering
- threshold search / proposal grid
- segmentation checkpoint change
- loss / target / architecture redesign
"""))

# 3. B1 identity and best epoch 83
cells.append(md("""## 3. B1 Identity and Best Epoch 83

H2A-B1 training evaluation artifact:
`reports/audits/post_phase13_h2a_training_evaluation.json`
"""))

cells.append(code("""
ev = json.loads((AUDITS / "post_phase13_h2a_training_evaluation.json").read_text("utf-8"))
print(f"status: {ev['status']}")
print(f"best_epoch: {ev['best_epoch']}")
print(f"completed_epochs: {ev['completed_epochs']}")
print(f"termination: {ev['termination']['reason']}")
print(f"best.pt SHA: {ev['checkpoint_shas']['best_pt']}")
print(f"best tuple: {ev['best_six_term_tuple']}")
"""))

# 4. B1 integrity evidence
cells.append(md("""## 4. B1 Integrity Evidence

- Trajectory reproduction: PASS (68 overlapping epochs, max abs val_loss diff 0.0)
- Selection replay: PASS (0 mismatches)
- Checkpoint cross-check limitation: disclosed (epochs 31/53/68 not retained)
"""))

cells.append(code("""
traj = json.loads((AUDITS / "post_phase13_h2a_training_trajectory_reproduction.json").read_text("utf-8"))
print(f"trajectory status: {traj['status']}")
print(f"overlapping epochs: {traj['comparison']['overlapping_epochs']}")
print(f"max abs train_loss diff: {traj['comparison']['max_abs_train_loss_diff']:.3e}")
print(f"max abs val_loss diff: {traj['comparison']['max_abs_val_loss_diff']:.3e}")

repl = json.loads((AUDITS / "post_phase13_h2a_selection_replay_verification.json").read_text("utf-8"))
print(f"selection replay status: {repl['status']}")
print(f"mismatch_count: {repl['mismatch_count']}")
"""))

# 5. B1 checkpoint-crosscheck limitation
cells.append(md("""## 5. B1 Checkpoint-Crosscheck Limitation

The original H2A-B1 protocol requested model-tensor cross-checks at historical epochs 31 / 53 / 68.
The completed H2A run did NOT retain epoch-specific model snapshots at those epochs.

Therefore the model-tensor cross-check is **NOT_RECOVERABLE_FROM_RETAINED_H2A_CHECKPOINTS**.

The 68-epoch loss/LR trajectory reproduction provides strong empirical support that gradient-update semantics were unchanged. Direct model-tensor equality at epochs 31/53/68 was not available because H2A did not retain epoch-specific snapshots at those epochs.

Classification: NONBLOCKING_SECONDARY_INTEGRITY_CHECK_UNAVAILABLE
"""))

# 6. Frozen H2A proposal identity
cells.append(md("""## 6. Frozen H2A Proposal Identity

The 457 proposals from H2A-B1 standalone evaluation are the authoritative downstream input.
"""))

cells.append(code("""
prop = pd.read_csv(TABLES / "post_phase13_h2a_best_checkpoint_proposals.csv")
case = pd.read_csv(TABLES / "post_phase13_h2a_best_checkpoint_case_proposals.csv")
comp = pd.read_csv(TABLES / "post_phase13_h2a_best_checkpoint_component_coverage.csv")
print(f"proposals: {len(prop)} rows")
print(f"cases: {len(case)} rows")
print(f"components: {len(comp)} rows")
print(f"proposal config: threshold=0.10 margin=0.20 top_k=5 NMS=0.30")
for k, fname in (("case","post_phase13_h2a_best_checkpoint_case_proposals.csv"),
                       ("proposals","post_phase13_h2a_best_checkpoint_proposals.csv"),
                       ("component","post_phase13_h2a_best_checkpoint_component_coverage.csv"),
                       ("stratified","post_phase13_h2a_best_checkpoint_size_stratified.csv")):
    p = TABLES / fname
    print(f"  {k} SHA: {sha(p)[:16]}...")
"""))

# 7. Segmentation checkpoint bindings
cells.append(md("""## 7. Segmentation Checkpoint Bindings

Four frozen architectures loaded with strict state_dict matching (missing=0, unexpected=0).
"""))

cells.append(code("""
checks = {
    "unet": (str(ROOT / "checkpoints/phase9_kub_unet_baseline_seed42_512_clean_v3/best.pt"),
             "7b955ba86464a2fec2d569ecb6124de1fa9a4e66d0b5d58b267be9a280b4c2c0"),
    "attention_unet": (str(ROOT / "checkpoints/phase10_kub_attention_unet_seed42_512_clean_v3/best.pt"),
                       "a49b19d66e43b57ed082ea6efc0ac10bccf444277abd3540dc68612bf30b88b3"),
    "unetpp": (str(ROOT / "checkpoints/phase10_kub_unetpp_seed42_512_clean_v3/best.pt"),
               "ec7eb13f32e43af27eab7fc617bd1a2a8fcce1d6651a1b4a3653f3e4d1283269"),
    "deeplabv3plus": (str(ROOT / "checkpoints/phase10_kub_deeplabv3plus_seed42_512_clean_v3/best.pt"),
                      "f519027ba1a3a4d6212d83fecd4379f61f71bc05b0751924b9660da08d597dad"),
}
for name, (path, expected) in checks.items():
    actual = sha(path)
    match = actual == expected
    print(f"  {name:<16} {'PASS' if match else 'FAIL'}  {actual[:16]}...")
"""))

# 8. Global cache reproduction
cells.append(md("""## 8. Global Cache Reproduction

Reused the frozen Phase13 Part1D-B FLOAT32 global cache.
Manifest: 412 items = 103 cases x 4 models.
"""))

cells.append(code("""
man = pd.read_csv(ROOT / "data_cache/phase13_part1d_b_predicted_region_clean_v3/global_512_manifest.csv")
print(f"manifest items: {len(man)}")
print(f"models: {sorted(man.model.unique())}")
print(f"dtype: {man['dtype'].unique().tolist()}")
print(f"manifest SHA: {sha('data_cache/phase13_part1d_b_predicted_region_clean_v3/global_512_manifest.csv')[:16]}...")
print(f"expected SHA: 76e1034d2bc7925260af33826fc19565b2d5ef786c612a7ad71f3bde46fb89a8")
"""))

# 9. Regional crop/restore semantics
cells.append(md("""## 9. Regional Crop / Restore Semantics

Frozen Part1D helper (`phase13_part1d_predicted_region_inference.py`) SHA:
`8cd7e39814a049a025f706c57ccea0b535a230908a177690d6289318234c6284`

- Native proposal rectangle already includes margin 0.20 (not applied twice)
- Input: valid native region -> zero-pad to square -> resize to 512 bilinear -> [0,1]
- Restore: regional prob 512 -> full square bilinear -> strip padding -> native coords
"""))

# 10. Fusion semantics
cells.append(md("""## 10. Fusion Semantics

- U_H2A = union of clipped frozen H2A proposal rectangles
- Regional overlaps: MAX among regional probability maps only
- Final P(x) = R(x) inside U_H2A, G(x) outside U_H2A
- NEVER max(G,R) inside the proposal union
- Zero proposals -> P == G exactly
- Threshold: 0.5 after complete fusion
"""))

# 11. Localizer epoch53 -> epoch83 comparison
cells.append(md("""## 11. Localizer Epoch 53 -> Epoch 83 Comparison
"""))

cells.append(code("""
loc = pd.read_csv(TABLES / "post_phase13_h2a_vs_phase13_localizer_comparison.csv")
print(loc.to_string(index=False))
"""))

# 12. Model-level downstream summary
cells.append(md("""## 12. Model-Level Downstream Summary
"""))

cells.append(code("""
sum_df = pd.read_csv(TABLES / "post_phase13_h2a_downstream_model_summary.csv")
print(sum_df.to_string(index=False))
"""))

# 13. GLOBAL vs H2A
cells.append(md("""## 13. GLOBAL vs H2A

H2A predicted-region path compared against the frozen GLOBAL comparator.
"""))

cells.append(code("""
sum_df = pd.read_csv(TABLES / "post_phase13_h2a_downstream_model_summary.csv")
_cols = ["model_display", "global_macro_dice", "h2a_predicted_macro_dice",
         "DELTA_H2A_GLOBAL_DICE", "global_macro_precision", "h2a_predicted_macro_precision",
         "global_macro_recall", "h2a_predicted_macro_recall",
         "mean_global_fp", "mean_h2a_fp", "mean_global_fn", "mean_h2a_fn",
         "cases_improved_vs_global", "cases_same_vs_global", "cases_worse_vs_global"]
print(sum_df[_cols].to_string(index=False))
"""))

# 14. Phase13 predicted vs H2A
cells.append(md("""## 14. Phase13 Predicted vs H2A

H2A predicted-region path compared against the frozen Phase13 epoch-53
predicted-region comparator (`PREDICTED_REGION_FLOAT_GLOBAL_RETAINED`).
"""))

cells.append(code("""
_cols = ["model_display", "phase13_predicted_macro_dice", "h2a_predicted_macro_dice",
         "DELTA_H2A_PHASE13_DICE", "phase13_predicted_macro_precision", "h2a_predicted_macro_precision",
         "phase13_predicted_macro_recall", "h2a_predicted_macro_recall",
         "mean_phase13_fp", "mean_h2a_fp", "mean_phase13_fn", "mean_h2a_fn",
         "cases_improved_vs_phase13", "cases_same_vs_phase13", "cases_worse_vs_phase13"]
print(sum_df[_cols].to_string(index=False))
"""))

# 15. ORACLE vs H2A
cells.append(md("""## 15. ORACLE vs H2A

H2A predicted-region path compared against the frozen Phase12 oracle comparator
(`ORACLE_FLOAT_GLOBAL_RETAINED`, GT-derived localization). No comparator is a
winner or reference architecture.
"""))

cells.append(code("""
_cols = ["model_display", "oracle_macro_dice", "h2a_predicted_macro_dice",
         "H2A_ORACLE_GAP", "ORACLE_GAIN_FROM_GLOBAL", "H2A_ORACLE_BENEFIT_RETENTION",
         "oracle_macro_precision", "h2a_predicted_macro_precision",
         "oracle_macro_recall", "h2a_predicted_macro_recall"]
print(sum_df[_cols].to_string(index=False))
"""))

# 16-18. Dice / IoU, Precision / Recall, FP / FN
cells.append(md("""## 16. Dice / IoU
## 17. Precision / Recall
## 18. FP / FN
"""))

cells.append(code("""
fig, axes = plt.subplots(2, 3, figsize=(14, 8))

metrics = [
    ("global_macro_dice", "h2a_predicted_macro_dice", "Dice"),
    ("global_macro_iou", "h2a_predicted_macro_iou", "IoU"),
    ("global_macro_precision", "h2a_predicted_macro_precision", "Precision"),
    ("global_macro_recall", "h2a_predicted_macro_recall", "Recall"),
    ("mean_global_fp", "mean_h2a_fp", "Mean FP (pixels)"),
    ("mean_global_fn", "mean_h2a_fn", "Mean FN (pixels)"),
]

for ax, (gcol, hcol, title) in zip(axes.flat, metrics):
    x = np.arange(len(sum_df))
    width = 0.35
    ax.bar(x - width/2, sum_df[gcol], width, label="GLOBAL")
    ax.bar(x + width/2, sum_df[hcol], width, label="H2A")
    ax.set_xticks(x)
    ax.set_xticklabels(sum_df["model_display"], rotation=15, ha="right")
    ax.set_title(title)
    ax.legend()

plt.tight_layout()
plt.show()
"""))

# 19. Component recoveries/losses
cells.append(md("""## 19. Component Recoveries / Losses
"""))

cells.append(code("""
fig, ax = plt.subplots(figsize=(8, 4))
x = np.arange(len(sum_df))
width = 0.35
ax.bar(x - width/2, sum_df["component_recoveries_vs_global"], width, label="Recoveries vs GLOBAL")
ax.bar(x + width/2, sum_df["component_losses_vs_global"], width, label="Losses vs GLOBAL")
ax.set_xticks(x)
ax.set_xticklabels(sum_df["model_display"], rotation=15, ha="right")
ax.set_title("Component Recoveries / Losses vs GLOBAL")
ax.legend()
plt.tight_layout()
plt.show()
"""))

# 20. Empty recoveries / new empties
cells.append(md("""## 20. Empty Recoveries / New Empties
"""))

cells.append(code("""
fig, ax = plt.subplots(figsize=(8, 4))
x = np.arange(len(sum_df))
width = 0.35
ax.bar(x - width/2, sum_df["empty_recoveries"], width, label="Empty recoveries")
ax.bar(x + width/2, sum_df["new_empty_predictions"], width, label="New empty predictions")
ax.set_xticks(x)
ax.set_xticklabels(sum_df["model_display"], rotation=15, ha="right")
ax.set_title("Empty Recoveries / New Empty Predictions")
ax.legend()
plt.tight_layout()
plt.show()
"""))

# 21. Oracle-benefit retention
cells.append(md("""## 21. Oracle-Benefit Retention

H2A_ORACLE_BENEFIT_RETENTION = (H2A_Dice - GLOBAL_Dice) / (ORACLE_Dice - GLOBAL_Dice)
"""))

cells.append(code("""
print("Retention by model:")
for _, r in sum_df.iterrows():
    ret = r["H2A_ORACLE_BENEFIT_RETENTION"]
    print(f"  {r['model_display']:<18} {ret:.4f}" if ret is not None else f"  {r['model_display']:<18} N/A")
"""))

# 22. Size-stratified results
cells.append(md("""## 22. Size-Stratified Results
"""))

cells.append(code("""
comp_df = pd.read_csv(TABLES / "post_phase13_h2a_downstream_component_model_metrics.csv")
strat = comp_df.groupby(["size_stratum", "model"]).agg(
    n=("native_component_id", "count"),
    global_detected=("global_detected", "sum"),
    h2a_detected=("h2a_predicted_detected", "sum"),
    oracle_detected=("oracle_detected", "sum"),
    recoveries=("GLOBAL_TO_H2A_RECOVERY", "sum"),
    losses=("GLOBAL_TO_H2A_LOSS", "sum"),
).reset_index()
print(strat.to_string(index=False))
"""))

# 23. Frozen Hard-Tiny cohort
cells.append(md("""## 23. Frozen Hard-Tiny Cohort

15 components. Preserved from Phase13.
"""))

cells.append(code("""
ht = comp_df[comp_df["hard_tiny"]].groupby("model").agg(
    n=("native_component_id", "count"),
    global_detected=("global_detected", "sum"),
    h2a_detected=("h2a_predicted_detected", "sum"),
    oracle_detected=("oracle_detected", "sum"),
    recoveries=("GLOBAL_TO_H2A_RECOVERY", "sum"),
    losses=("GLOBAL_TO_H2A_LOSS", "sum"),
)
print(ht)
"""))

# 24. Frozen Global-empty cohort
cells.append(md("""## 24. Frozen Global-Empty Cohort

5 IMAGES from the frozen Phase13 global-empty cohort. Preserved from Phase13.

Those 5 frozen images contain **8 native components**. Where a component-level
table reports `n = 8`, that count is explicitly labelled
**`GLOBAL_EMPTY_COMPONENTS_WITHIN_5_FROZEN_IMAGES`** — it is a component count
within 5 frozen images, and is **never** to be reported as "8 global-empty images".
"""))

cells.append(code("""
ge = comp_df[comp_df["global_empty_image"]].groupby("model").agg(
    n=("native_component_id", "count"),
    global_detected=("global_detected", "sum"),
    h2a_detected=("h2a_predicted_detected", "sum"),
    oracle_detected=("oracle_detected", "sum"),
    recoveries=("GLOBAL_TO_H2A_RECOVERY", "sum"),
    losses=("GLOBAL_TO_H2A_LOSS", "sum"),
)
print("GLOBAL_EMPTY_COMPONENTS_WITHIN_5_FROZEN_IMAGES")
print(ge)
_frozen_ge_images = int(comp_df.loc[comp_df["global_empty_image"], "sample_id"].nunique())
print(f"frozen global-empty IMAGES: {_frozen_ge_images} | components within them (per model): {int(ge['n'].iloc[0])}")
assert _frozen_ge_images == 5, f"frozen global-empty images {_frozen_ge_images} != 5"
"""))

# 25. Multi-component cohort
cells.append(md("""## 25. Multi-Component Cohort
"""))

cells.append(code("""
mc = comp_df[comp_df["multi_component_image"]].groupby("model").agg(
    n=("native_component_id", "count"),
    global_detected=("global_detected", "sum"),
    h2a_detected=("h2a_predicted_detected", "sum"),
    oracle_detected=("oracle_detected", "sum"),
    recoveries=("GLOBAL_TO_H2A_RECOVERY", "sum"),
    losses=("GLOBAL_TO_H2A_LOSS", "sum"),
)
print(mc)
"""))

# 26. Cross-architecture consistency
cells.append(md("""## 26. Cross-Architecture Consistency
"""))

cells.append(code("""
cross = pd.read_csv(TABLES / "post_phase13_h2a_downstream_cross_architecture_summary.csv")
print(cross.to_string(index=False))
"""))

# 27. Localizer-to-downstream translation
cells.append(md("""## 27. Localizer-to-Downstream Translation
"""))

cells.append(code("""
link = pd.read_csv(TABLES / "post_phase13_h2a_localizer_to_downstream_comparison.csv")
print(link.to_string(index=False))
"""))

# 28. Limitations
cells.append(md("""## 28. Limitations

1. H2A is a single-seed adaptive VAL-development experiment.
2. The deployment-balanced selection rule structurally cannot discriminate epochs 1-30 (proposals appear only from epoch 31).
3. No direct model-tensor cross-check at epochs 31/53/68 (snapshots not retained).
4. Descriptive comparison only — no statistical superiority claim.
5. No threshold search or proposal grid was run.
6. TEST remains untouched; these are development-data results only.
"""))

# 29. Adaptive-development disclosure
cells.append(md("""## 29. Adaptive-Development Disclosure

H2A is an adaptive VAL-development revision initiated after Phase 13 `REVISE_LOCALIZER` and H1 acceptance-only insufficiency.

- The H2A checkpoint-selection rule was frozen BEFORE H2A-B1 training.
- The downstream protocol was frozen BEFORE H2A-B2 segmentation execution.
- VAL remains development data.
- No H2A result substitutes for final TEST evaluation.
- TEST remains untouched.
"""))

# 30. Explicit adjudication stop boundary
cells.append(md("""## 30. Explicit Adjudication Stop Boundary

**H2A-B2 DOES NOT adjudicate H2A.**

The execution returns evidence only. H2A outcome adjudication is a separate supervisor step.

The following are NOT authorized and NOT performed:
- R1 selective acceptance
- Loss / target / sigma redesign
- Architecture redesign
- H2B / H3
- Phase14
- TEST access
"""))

# 30b. MANDATORY COMPLETE TABLES (untruncated) — HARD PASS GATE
cells.append(md("""## 30b. Mandatory Complete Tables (Untruncated)

These tables are rendered **in full** — no `head()`, no `tail()`, no notebook ellipsis.
Source: the immutable on-disk artifacts written by the H2A-B2 execution.

- Model summary: 4 / 4 rows
- Case-model metrics: 412 / 412 rows (103 cases x 4 models)
- Component-model metrics: 608 / 608 rows (152 components x 4 models)
"""))

cells.append(code("""
import pandas as _pd
_pd.set_option("display.max_rows", None)
_pd.set_option("display.max_columns", None)
_pd.set_option("display.width", 0)
_pd.set_option("display.max_colwidth", None)

# --- 4 / 4 model summary rows ------------------------------------------------
_ms = pd.read_csv(TABLES / "post_phase13_h2a_downstream_model_summary.csv")
print("=" * 100)
print(f"MODEL SUMMARY — {len(_ms)} / 4 rows")
print("=" * 100)
print(_ms.to_string(index=False))
print()
assert len(_ms) == 4, f"model summary rows {len(_ms)} != 4"
"""))

cells.append(code("""
# --- 412 / 412 case-model rows ----------------------------------------------
_cm = pd.read_csv(TABLES / "post_phase13_h2a_downstream_case_model_metrics.csv")
print("=" * 100)
print(f"CASE-MODEL METRICS — {len(_cm)} / 412 rows (103 cases x 4 models)")
print("=" * 100)
print(_cm.to_string(index=False))
print()
assert len(_cm) == 412, f"case-model rows {len(_cm)} != 412"
assert _cm["sample_id"].nunique() == 103, f"case-model cases {_cm['sample_id'].nunique()} != 103"
assert _cm["model"].nunique() == 4, f"case-model models {_cm['model'].nunique()} != 4"
print(f"CONFIRMED: {len(_cm)} rows | {_cm['sample_id'].nunique()} cases | {_cm['model'].nunique()} models")
"""))

cells.append(code("""
# --- 608 / 608 component-model rows -----------------------------------------
_km = pd.read_csv(TABLES / "post_phase13_h2a_downstream_component_model_metrics.csv")
print("=" * 100)
print(f"COMPONENT-MODEL METRICS — {len(_km)} / 608 rows (152 components x 4 models)")
print("=" * 100)
print(_km.to_string(index=False))
print()
assert len(_km) == 608, f"component-model rows {len(_km)} != 608"
assert _km["native_component_id"].notna().sum() == 608
print(f"CONFIRMED: {len(_km)} rows | {_km['model'].nunique()} models | "
      f"{_km.groupby('model')['native_component_id'].count().to_dict()}")
"""))

# 31. Artifact SHA registry
cells.append(md("""## 31. Artifact SHA Registry
"""))

cells.append(code("""
artifacts = [
    str(ROOT / "reports/audits/post_phase13_h2a_protocol_frozen.json"),
    str(ROOT / "reports/audits/post_phase13_h2a_training_evaluation.json"),
    str(ROOT / "reports/audits/post_phase13_h2a_training_trajectory_reproduction.json"),
    str(ROOT / "reports/audits/post_phase13_h2a_selection_replay_verification.json"),
    str(ROOT / "reports/audits/post_phase13_h2a_b1_checkpoint_crosscheck_limitation.json"),
    str(ROOT / "reports/audits/post_phase13_h2a_downstream_integrity.json"),
    str(ROOT / "reports/audits/post_phase13_h2a_best_checkpoint_standalone_evaluation.json"),
    str(ROOT / "reports/tables/post_phase13_h2a_best_checkpoint_case_proposals.csv"),
    str(ROOT / "reports/tables/post_phase13_h2a_best_checkpoint_proposals.csv"),
    str(ROOT / "reports/tables/post_phase13_h2a_best_checkpoint_component_coverage.csv"),
    str(ROOT / "reports/tables/post_phase13_h2a_best_checkpoint_size_stratified.csv"),
    str(ROOT / "reports/tables/post_phase13_h2a_downstream_case_model_metrics.csv"),
    str(ROOT / "reports/tables/post_phase13_h2a_downstream_component_model_metrics.csv"),
    str(ROOT / "reports/tables/post_phase13_h2a_downstream_model_summary.csv"),
    str(ROOT / "reports/tables/post_phase13_h2a_downstream_cross_architecture_summary.csv"),
    str(ROOT / "reports/tables/post_phase13_h2a_localizer_to_downstream_comparison.csv"),
    str(ROOT / "reports/tables/post_phase13_h2a_vs_phase13_localizer_comparison.csv"),
]
for a in artifacts:
    p = Path(a)
    print(f"{sha(p)}  {p.name}")
"""))

# ---------------------------------------------------------------------------
# Assemble and write
# ---------------------------------------------------------------------------
nb = nbformat.v4.new_notebook(cells=cells)

# Deterministic per-cell ids so the executed notebook hashes reproducibly.
for _i, _c in enumerate(nb.cells):
    _c["id"] = f"p13b2{_i:03d}"

nbformat.write(nb, str(NB))
print(f"wrote {len(cells)} cells -> {NB}")
