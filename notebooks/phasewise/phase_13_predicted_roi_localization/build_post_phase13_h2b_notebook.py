"""Build the H2B-B1 localizer training reviewer notebook (READ-ONLY on rerun)."""
from pathlib import Path

import nbformat

ROOT = Path(r"D:\Softfors\jup")
NB = (ROOT / "notebooks/phasewise/phase_13_predicted_roi_localization"
      / "post_phase13_h2b_localizer_training_review.ipynb")


def md(t):
    return nbformat.v4.new_markdown_cell(t)


def code(s):
    return nbformat.v4.new_code_cell(s)


cells = []

# 1. governance / adaptive-development disclosure
cells.append(md("""# POST-PHASE-13 H2B-B1 — Objective-Only Localizer Training Review

## 1. Governance / Adaptive-Development Disclosure

This notebook is **READ-ONLY**. It performs no training, no localizer inference and no
segmentation inference; it only reads on-disk artifacts.

H2B is adaptive VAL development informed by:
- Phase 13 `REVISE_LOCALIZER`
- H1 acceptance-only insufficiency
- `H2A_SELECTION_REDESIGN_PARTIAL`

The H2B objective and `gamma = 2.0` were frozen **before** H2B training. No objective grid was
run. VAL remains development data. H2B results do **not** replace final TEST evaluation.
TEST remains untouched until Phase 39.
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
EXP = ROOT / "experiments" / EID
CK = ROOT / "checkpoints" / EID

def sha(p):
    p = Path(p)
    if not p.is_absolute():
        p = ROOT / p
    return hashlib.sha256(p.read_bytes()).hexdigest()

hist = pd.read_csv(EXP / "history.csv")
te = json.loads((AUDITS / "post_phase13_h2b_b1_training_evaluation.json").read_text("utf-8"))
sa = json.loads((AUDITS / "post_phase13_h2b_best_checkpoint_standalone_evaluation.json").read_text("utf-8"))
print("Environment OK | epochs:", len(hist))
"""))

# 2. H2A partial outcome and H2B rationale
cells.append(md("""## 2. H2A Partial Outcome and H2B Rationale

H2A adjudication returned **`H2A_SELECTION_REDESIGN_PARTIAL`**: checkpoint-selection redesign
produced reproducible localizer-level and downstream improvement, but the complete GT-free
regional path remained substantially below GLOBAL. Selection alone was not sufficient.

H2A also left a substantial off-target proposal burden (pixel any-hit precision ~0.276).

H2B therefore asks: can a **soft-target objective** that treats the complete frozen Gaussian
target as continuous supervision improve heatmap discrimination and proposal precision while
preserving object coverage — with everything else held fixed?

This is a **hypothesis**, not a claim.
"""))

# 3. protocol identity
cells.append(md("""## 3. Protocol Identity

`reports/audits/post_phase13_h2b_protocol_frozen.json` —
`SUPERVISOR_FROZEN_H2B_OBJECTIVE_ONLY_READY_FOR_B1_AUTHORIZATION`
"""))
cells.append(code("""
print("experiment_id:", EID)
print("protocol sha:", sha(AUDITS / "post_phase13_h2b_protocol_frozen.json"))
print("protocol_identity:", te["bindings"]["h2b_protocol_sha"][:16], "...")
print("H2A adjudication sha:", te["bindings"]["h2a_adjudication_sha"])
print("runner sha:", te["bindings"]["runner_sha"])
print("config sha:", te["bindings"]["config_sha"])
"""))

# 4. one-axis scientific change
cells.append(md("""## 4. One-Axis Scientific Change

Exactly **one** new scientific axis: **LOSS / OBJECTIVE SEMANTICS**.

`CenterNetFocalLoss(alpha=2.0, beta=4.0)` → `SoftTargetFocalBCE(gamma=2.0)`

Everything else UNCHANGED: architecture, target, sigma, data, augmentation, optimizer,
scheduler, checkpoint selection, proposal config, fusion.
"""))
cells.append(code("""
d = json.loads((AUDITS / "post_phase13_h2b_b1_execution_diff_vs_h2a.json").read_text("utf-8"))
print("one-axis diff status:", d["status"])
print("scientific_axis_differences:", d["scientific_axis_differences"], "->", d["scientific_axis"])
print("gradient_affecting_beyond_criterion:", d["gradient_affecting_differences_beyond_criterion_objective"])
for k in ("architecture", "target", "optimizer", "scheduler", "data", "augmentation", "seed",
          "checkpoint_selection", "proposal_config", "initialization", "warm_start"):
    print(f"  {k}: {d[k]}")
"""))

# 5. SoftTargetFocalBCE exact formula
cells.append(md("""## 5. SoftTargetFocalBCE — Exact Frozen Formula

```
p          = sigmoid(z)
bce        = BCEWithLogits(z, y, reduction="none")
modulation = |p - y| ** gamma
loss_map   = modulation * bce
L          = mean(loss_map)
```

equivalently

```
L = mean( |sigmoid(z) - y|^2 * BCEWithLogits(z, y) )        # gamma = 2.0 FIXED
```

Modulation **not detached**. Target asserted finite and in `[0,1]` — never silently clamped.
No Dice, no alpha/beta, no auxiliary loss, no regularizer, no class weight.
"""))
cells.append(code("""
print("loss class:", te["loss"]["class"])
print("loss label:", te["loss"]["label"])
print("gamma:", te["loss"]["gamma"])
print("formula:", te["loss"]["formula"])
print("modulation detached:", te["loss"]["modulation_detached"])
print("dice term:", te["loss"]["dice_term"], "| auxiliary loss:", te["loss"]["auxiliary_loss"])
print("objective_change_id:", te["loss"]["objective_change_id"])
print("stale loss_alpha present:", te["loss"]["stale_loss_alpha_present"])
print("stale loss_beta present:", te["loss"]["stale_loss_beta_present"])
"""))

# 6. synthetic loss/gradient audit
cells.append(md("""## 6. Synthetic Loss / Gradient Audit (CPU-only)

`reports/audits/post_phase13_h2b_soft_target_focal_loss_unit_audit.json`
"""))
cells.append(code("""
ua = json.loads((AUDITS / "post_phase13_h2b_soft_target_focal_loss_unit_audit.json").read_text("utf-8"))
print("status:", ua["status"], "| execution:", ua["execution"])
print("modulation detached:", ua["modulation_detached"])
for k, v in ua["checks"].items():
    print(f"  [{'PASS' if v else 'FAIL'}] {k}")
g = pd.read_csv(TABLES / "post_phase13_h2b_soft_target_focal_gradient_sanity.csv")
print("gradient sanity rows:", len(g))
"""))

# 7. population
cells.append(md("""## 7. Population

TRAIN 770 FULL_FIELD / 1161 components · VAL 103 FULL_FIELD / 152 components · ROI EXCLUDED ·
manifest `phase4_v3` · taxonomy `kub_size_clean_v3_v1`.
"""))
cells.append(code("""
print("TRAIN:", te["training_contract"]["TRAIN"])
print("VAL:", te["training_contract"]["VAL"])
print("manifest:", te["training_contract"]["manifest"])
print("taxonomy:", te["training_contract"]["taxonomy"])
print("input:", te["training_contract"]["input"], "| heatmap:", te["training_contract"]["heatmap"],
      "| sigma:", te["training_contract"]["sigma"])
"""))

# 8. fresh initialization semantics
cells.append(md("""## 8. Fresh Initialization Semantics
"""))
cells.append(code("""
for k, v in te["initialization_semantics"].items():
    print(f"  {k}: {v}")
"""))

# 9. frozen training contract
cells.append(md("""## 9. Frozen Training Contract
"""))
cells.append(code("""
for k, v in te["training_contract"].items():
    print(f"  {k}: {v}")
"""))

# 10. frozen proposal evaluation
cells.append(md("""## 10. Frozen Proposal Evaluation — ONE configuration only
"""))
cells.append(code("""
for k, v in te["proposal_configuration"].items():
    print(f"  {k}: {v}")
"""))

# 11. unchanged H2A checkpoint selection
cells.append(md("""## 11. Unchanged H2A Checkpoint Selection

The H2B run inherits the accepted H2A six-term deployment-balanced rule verbatim.
"""))
cells.append(code("""
for k, v in te["selection_rule"].items():
    print(f"  {k}: {v}")
"""))

# 12. COMPLETE epoch-by-epoch table
cells.append(md("""## 12. Complete Epoch-by-Epoch Table

One completed epoch per row — **all 46 epochs, untruncated, no ellipsis**.
"""))
cells.append(code("""
import pandas as _pd
_pd.set_option("display.max_rows", None)
_pd.set_option("display.max_columns", None)
_pd.set_option("display.width", 0)
_pd.set_option("display.max_colwidth", None)

_ecols = ["epoch", "train_loss", "val_loss", "proposal_pixel_any_hit_precision",
          "tiny_recall90", "overall_recall90", "deployment_balance_hmean",
          "proposal_total_count", "mean_roi_area_fraction", "selection_tuple",
          "is_new_best", "bad_epochs"]
print("=" * 100)
print(f"COMPLETE EPOCH TABLE — {len(hist)} / {len(hist)} rows")
print("=" * 100)
print(hist[_ecols].to_string(index=False))
print()
assert len(hist) == 46, f"expected 46 epochs, got {len(hist)}"
assert hist.epoch.is_unique and int(hist.epoch.iloc[0]) == 1
assert bool((hist.epoch.diff().dropna() == 1).all())
print(f"CONFIRMED: {len(hist)} contiguous epochs 1..{int(hist.epoch.iloc[-1])}, no duplicates")
"""))

# 13. train/VAL loss curves
cells.append(md("## 13. Train / VAL Loss Curves"))
cells.append(code("""
fig, ax = plt.subplots()
ax.plot(hist.epoch, hist.train_loss, marker="o", ms=3, label="train_loss")
ax.plot(hist.epoch, hist.val_loss, marker="s", ms=3, label="val_loss")
ax.set_xlabel("epoch"); ax.set_ylabel("loss"); ax.set_yscale("log")
ax.set_title("H2B train / VAL loss (soft-target focal BCE; magnitudes not comparable to H2A)")
ax.legend(); plt.tight_layout(); plt.show()
"""))

# 14. P/T/O trajectories
cells.append(md("## 14. P / T / O Trajectories"))
cells.append(code("""
fig, ax = plt.subplots()
ax.plot(hist.epoch, hist.proposal_pixel_any_hit_precision, marker="o", ms=3, label="P (pixel any-hit precision)")
ax.plot(hist.epoch, hist.tiny_recall90, marker="s", ms=3, label="T (tiny recall90)")
ax.plot(hist.epoch, hist.overall_recall90, marker="^", ms=3, label="O (overall recall90)")
ax.set_xlabel("epoch"); ax.set_ylabel("value"); ax.set_title("P / T / O trajectories")
ax.legend(); plt.tight_layout(); plt.show()
"""))

# 15. deployment-balance trajectory
cells.append(md("## 15. Deployment-Balance Trajectory"))
cells.append(code("""
fig, ax = plt.subplots()
ax.plot(hist.epoch, hist.deployment_balance_hmean, marker="o", ms=3, color="tab:green")
be = int(hist.loc[hist.is_new_best.astype(bool), "epoch"].iloc[-1])
ax.axvline(be, color="red", ls="--", lw=1, label=f"best epoch {be}")
ax.set_xlabel("epoch"); ax.set_ylabel("DEPLOYMENT_BALANCE_HMEAN_P_TINY90_OVERALL90")
ax.set_title("Deployment-balance (primary selection term)"); ax.legend()
plt.tight_layout(); plt.show()
print("best epoch:", be, "| best hmean:", float(hist.loc[hist.epoch == be, "deployment_balance_hmean"].iloc[0]))
"""))

# 16. proposal count / union-area trajectory
cells.append(md("## 16. Proposal Count / Union-Area Trajectory"))
cells.append(code("""
fig, axes = plt.subplots(1, 2, figsize=(13, 4))
axes[0].plot(hist.epoch, hist.proposal_total_count, marker="o", ms=3, color="tab:blue")
axes[0].set_xlabel("epoch"); axes[0].set_ylabel("proposal_total_count"); axes[0].set_title("Proposal count")
axes[1].plot(hist.epoch, hist.mean_roi_area_fraction, marker="s", ms=3, color="tab:orange")
axes[1].set_xlabel("epoch"); axes[1].set_ylabel("mean_roi_area_fraction"); axes[1].set_title("Mean union area fraction")
plt.tight_layout(); plt.show()
"""))

# 17. score-distribution trajectory
cells.append(md("## 17. Score-Distribution Trajectory"))
cells.append(code("""
fig, ax = plt.subplots()
ax.plot(hist.epoch, hist.proposal_score_mean, marker="o", ms=3, label="mean")
ax.plot(hist.epoch, hist.proposal_score_median, marker="s", ms=3, label="median")
ax.plot(hist.epoch, hist.proposal_score_max, marker="^", ms=3, label="max")
ax.set_xlabel("epoch"); ax.set_ylabel("proposal score"); ax.set_title("Proposal score distribution")
ax.legend(); plt.tight_layout(); plt.show()
"""))

# 18. score-saturation trajectory
cells.append(md("## 18. Score-Saturation Trajectory"))
cells.append(code("""
fig, ax = plt.subplots()
ax.plot(hist.epoch, hist.fraction_proposals_exactly_at_epoch_max_score, marker="o", ms=3, color="tab:red")
ax.set_ylim(0, 1.05)
ax.set_xlabel("epoch"); ax.set_ylabel("fraction exactly at epoch max")
ax.set_title("Score saturation (fraction of proposals at the epoch maximum)")
plt.tight_layout(); plt.show()
"""))

# 19. ROC-AUC / PR-AUC trajectory
cells.append(md("## 19. ROC-AUC / PR-AUC Trajectory"))
cells.append(code("""
fig, ax = plt.subplots()
ax.plot(hist.epoch, hist.proposal_roc_auc_score_to_pixel_any_hit, marker="o", ms=3, label="ROC-AUC")
ax.plot(hist.epoch, hist.proposal_pr_auc_score_to_pixel_any_hit, marker="s", ms=3, label="PR-AUC")
ax.set_xlabel("epoch"); ax.set_ylabel("AUC"); ax.set_title("Score discrimination (score -> pixel any-hit)")
ax.legend(); plt.tight_layout(); plt.show()
"""))

# 20. head-weight/bias diagnostics
cells.append(md("""## 20. Head-Weight / Bias Diagnostics

**DIAGNOSTIC ONLY — never used for checkpoint selection or stopping.**
"""))
cells.append(code("""
for k, v in sa["head_statistics"].items():
    print(f"  {k}: {v}")
"""))

# 21. independent selection replay
cells.append(md("## 21. Independent Selection Replay"))
cells.append(code("""
rp = json.loads((AUDITS / "post_phase13_h2b_b1_selection_replay_verification.json").read_text("utf-8"))
print("status:", rp["status"])
print("mismatch_count:", rp["mismatch_count"])
print("replayed best_epoch:", rp["replayed"]["best_epoch"], "| stored:", rp["stored"]["best_epoch"])
print("max_abs_term_diff:", rp["max_abs_term_diff"])
print("final bad_epochs:", rp["replayed"]["final_bad_epochs"])
print("trajectory reproduction vs H2A:", rp["trajectory_reproduction_vs_h2a"])
"""))

# 22. best-checkpoint standalone proposal evaluation
cells.append(md("## 22. Best-Checkpoint Standalone Proposal Evaluation"))
cells.append(code("""
m = sa["metrics"]
for k in ("proposal_total_count", "proposal_count_per_image", "proposal_pixel_any_hit_precision",
          "proposal_bbox_any_hit_precision", "tiny_recall90", "overall_recall90",
          "overall_recall50", "any_overlap_recall", "mean_coverage", "mean_proposal_union_area",
          "score_max", "score_iqr", "fraction_exactly_at_max",
          "roc_auc_score_to_pixel_any_hit", "pr_auc_score_to_pixel_any_hit"):
    print(f"  {k}: {m[k]}")
"""))

# 23. size-stratified results
cells.append(md("## 23. Size-Stratified Results"))
cells.append(code("""
st = pd.read_csv(TABLES / "post_phase13_h2b_best_checkpoint_size_stratified.csv")
print(st.to_string(index=False))
"""))

# 24. difficult frozen cohorts
cells.append(md("## 24. Difficult Frozen Cohorts"))
cells.append(code("""
print("hard_tiny:", json.dumps(sa["metrics"]["hard_tiny"]))
print("global_empty:", json.dumps(sa["metrics"]["global_empty"]))
print("multi_component:", json.dumps(sa["metrics"]["multi_component"]))
"""))

# 25. H2B vs H2A localizer comparison
cells.append(md("""## 25. H2B vs H2A Localizer Comparison

Descriptive development comparison. **No superiority claim. No significance language.
No checkpoint re-selection from this comparison.**
"""))
cells.append(code("""
cmp = pd.read_csv(TABLES / "post_phase13_h2b_vs_h2a_localizer_comparison.csv")
print(cmp.to_string(index=False))
"""))

# 26. Phase13 historical context
cells.append(md("""## 26. Phase-13 Historical Context

Phase-13 epoch-53 values appear as the leftmost comparator column above. Phase 13 is
**historical context only** — H2B's immediate baseline is H2A, not Phase 13.
"""))
cells.append(code("""
print(cmp[["quantity", "phase13_best_epoch53", "h2a_best_epoch83", "h2b_best"]].to_string(index=False))
"""))

# 27. limitations
cells.append(md("""## 27. Limitations

1. H2B is a single-seed adaptive VAL-development experiment.
2. H2B train/val loss magnitudes are **not** comparable to H2A/Phase-13 — the objective changed.
   There is no loss-trajectory reproduction gate across branches.
3. The deployment-balanced rule cannot discriminate epochs before proposals appear.
4. Descriptive comparison only — no statistical superiority claim.
5. No threshold search, no proposal grid, no gamma sweep.
6. Head statistics are diagnostic only and never influenced selection.
7. TEST remains untouched; these are development-data results only.
"""))

# 28. explicit downstream stop boundary
cells.append(md("""## 28. Explicit Downstream Stop Boundary

**H2B-B1 DOES NOT run downstream segmentation.**

Not authorized and not performed:
- UNet / Attention U-Net / UNet++ / DeepLabV3+ regional evaluation
- H2B-B2
- H1 selective acceptance
- fusion redesign
- objective change or another gamma
- representation / head redesign
- H3, Phase 14
- TEST access

**H2B outcome is NOT adjudicated here.**
"""))

# 29. adaptive-development disclosure
cells.append(md("""## 29. Adaptive-Development Disclosure

H2B is adaptive VAL development informed by Phase 13 `REVISE_LOCALIZER`, H1 insufficiency and
`H2A_SELECTION_REDESIGN_PARTIAL`. The objective and `gamma = 2.0` were frozen **before** H2B
training and no objective grid was run. VAL remains development data. H2B results do not
replace final TEST evaluation. TEST remains untouched until Phase 39.
"""))

# 30. artifact SHA registry
cells.append(md("## 30. Artifact SHA Registry"))
cells.append(code("""
artifacts = [
    "reports/audits/post_phase13_h2b_protocol_frozen.json",
    "reports/audits/post_phase13_h2b_soft_target_focal_loss_unit_audit.json",
    "reports/audits/post_phase13_h2b_b1_execution_diff_vs_h2a.json",
    "reports/audits/post_phase13_h2b_b1_pre_fix_execution_invalidation.json",
    "reports/audits/post_phase13_h2b_b1_defect_linkage.json",
    "reports/audits/post_phase13_h2b_b1_provenance_repair_tests.json",
    "reports/audits/post_phase13_h2b_b1_training_start.json",
    "reports/audits/post_phase13_h2b_b1_training_completion.json",
    "reports/audits/post_phase13_h2b_b1_selection_replay_verification.json",
    "reports/audits/post_phase13_h2b_best_checkpoint_standalone_evaluation.json",
    "reports/audits/post_phase13_h2b_b1_training_evaluation.json",
    "reports/tables/post_phase13_h2b_best_checkpoint_case_proposals.csv",
    "reports/tables/post_phase13_h2b_best_checkpoint_proposals.csv",
    "reports/tables/post_phase13_h2b_best_checkpoint_component_coverage.csv",
    "reports/tables/post_phase13_h2b_best_checkpoint_size_stratified.csv",
    "reports/tables/post_phase13_h2b_vs_h2a_localizer_comparison.csv",
    "experiments/" + EID + "/history.csv",
    "checkpoints/" + EID + "/best.pt",
    "checkpoints/" + EID + "/latest.pt",
]
for a in artifacts:
    p = ROOT / a
    print(f"{sha(p) if p.exists() else 'MISSING':64s}  {Path(a).name}")
"""))

nb = nbformat.v4.new_notebook(cells=cells)
for _i, _c in enumerate(nb.cells):
    _c["id"] = f"h2b{_i:03d}"
nbformat.write(nb, str(NB))
print(f"wrote {len(cells)} cells -> {NB}")
