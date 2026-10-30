"""Build the H2C-B1 localizer training reviewer notebook (READ-ONLY on rerun)."""
from pathlib import Path

import nbformat

ROOT = Path(r"D:\Softfors\jup")
NB = (ROOT / "notebooks/phasewise/phase_13_predicted_roi_localization"
      / "post_phase13_h2c_localizer_training_review.ipynb")


def md(t):
    return nbformat.v4.new_markdown_cell(t)


def code(s):
    return nbformat.v4.new_code_cell(s)


cells = []

cells.append(md("""# POST-PHASE13 H2C-B1 — Frozen Localizer-Head Architecture Training Review

## 1. Governance / Adaptive-Development Disclosure

READ-ONLY on rerun. No training, no localizer inference, no segmentation inference — this notebook
only reads on-disk artifacts.

H2C is adaptive VAL development informed by Phase 13 `REVISE_LOCALIZER`, H1 insufficiency,
`H2A_SELECTION_REDESIGN_PARTIAL` and `H2B_OBJECTIVE_REDESIGN_INSUFFICIENT`. The head architecture
and its initialization were frozen **before** training. VAL remains development data. No H2C result
substitutes for final TEST evaluation. TEST remains untouched.
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
EID = ("post_phase13_h2c_kub_localizer_spatialhead3x3relu_r512_h128_sigmaeq075_"
       "centernetfocal_deploymentbalance_seed42_clean_v3")

def sha(p):
    p = Path(p)
    if not p.is_absolute():
        p = ROOT / p
    return hashlib.sha256(p.read_bytes()).hexdigest()

hist = pd.read_csv(ROOT / "experiments" / EID / "history.csv")
te = json.loads((AUDITS / "post_phase13_h2c_b1_training_evaluation.json").read_text("utf-8"))
sa = json.loads((AUDITS / "post_phase13_h2c_best_checkpoint_standalone_evaluation.json").read_text("utf-8"))
print("Environment OK | epochs:", len(hist))
"""))

cells.append(md("""## 2. H2C Hypothesis and the Single Changed Axis

**Question.** Can a HEAD-ONLY spatial representation redesign improve heatmap discrimination and
proposal precision while preserving object coverage, holding backbone, target, sigma, loss,
optimizer, scheduler, augmentation, dataset, split, seed, checkpoint selection, proposal policy,
segmentation checkpoints, fusion and segmentation threshold fixed?

**Changed axis (exactly one):** `LOCALIZER_PREDICTION_HEAD_ARCHITECTURE` (`CHANGE_H2C_001`),
including its prospectively frozen initialization.

H2C branches from the **H2A** baseline and **retains the H2A `CenterNetFocalLoss(alpha=2.0,
beta=4.0)` objective** — the H2B soft-target objective is **not** used. H2C must not be described
as "H2B plus a new head".
"""))

cells.append(md("## 3. H2C Protocol Binding"))
cells.append(code("""
proto = json.loads((AUDITS / "post_phase13_h2c_protocol_frozen.json").read_text("utf-8"))
print("artifact:", proto["artifact"])
print("status:", proto["status"])
print("protocol SHA:", sha(AUDITS / "post_phase13_h2c_protocol_frozen.json"))
print("experiment_id:", proto["experiment_id"])
print("axis:", proto["purpose"]["changed_axis"])
"""))

cells.append(md("""## 4. RNG-Equivalence Preflight

`RNG_STREAMS_ALREADY_ISOLATED` — the H2C kaiming draws cannot alter TRAIN ordering or augmentation
because those streams are independently owned.
"""))
cells.append(code("""
rng = json.loads((AUDITS / "post_phase13_h2c_rng_equivalence_preflight.json").read_text("utf-8"))
e = rng["empirical_equivalence"]
print("classification:", rng["rng_classification"], "| fix required:", rng["execution_fix_required"])
print("TRAIN order equivalent:", e["train_order_equivalent"], "| hash:", e["train_trace_hash_h2a"][:16], "...")
print("VAL order equivalent:", e["val_order_equivalent"], "| hash:", e["val_trace_hash_h2a"][:16], "...")
print("augmentation RNG equivalent:", e["augmentation_rng_equivalent"], "| hash:", e["augmentation_trace_hash_h2a"][:16], "...")
print("python random state equivalent:", e["python_random_state_equivalent"])
print("numpy random state equivalent:", e["numpy_random_state_equivalent"])
print("train/val generator states equivalent:", e["train_generator_state_equivalent"], e["val_generator_state_equivalent"])
print()
print("=== torch global RNG ===")
print("torch_global_rng_state_equivalent:", e["torch_global_rng_state_equivalent"])
print("EXPECTED_INERT_DIFFERENCE_FROM_H2C_KAIMING_DRAWS")
print("  The H2C head performs additional kaiming draws, so the torch GLOBAL RNG state must")
print("  differ. No downstream stream consumes it, so the difference is inert.")
"""))

cells.append(md("""## 5. Terminal-Zero Initialization Consequence

`FROZEN_INITIALIZATION_CONSEQUENCE` / `NOT_A_PROTOCOL_DEFECT`.

The terminal 1x1 weights initialize to ZERO, so the hidden 3x3 may receive zero gradient on the
first backward pass until the terminal layer updates. No warmup, no optimizer change, no
initialization change was applied.

**Measured consequence:** the H2A and H2C heads produce *identical initial logits*
(mean −2.197224, max−min exactly 0.0, p = 0.100000) and an identical initial loss of 19.119539.
However H2C's epoch-1 `train_loss` is far higher than H2A's, because H2C learns more slowly at
first. **H2C early-epoch losses are therefore NOT comparable in scale to H2A's.**
"""))
cells.append(code("""
print("H2C epoch-1 train_loss:", float(hist.train_loss.iloc[0]))
print("H2C epoch-2 train_loss:", float(hist.train_loss.iloc[1]))
print("(H2A epoch-1 train_loss was 0.001105 — scales are NOT comparable, by design.)")
"""))

cells.append(md("## 6. H2A → H2C Implementation Diff"))
cells.append(code("""
imp = json.loads((AUDITS / "post_phase13_h2c_b1_implementation_diff.json").read_text("utf-8"))
print("status:", imp["status"])
print("runner changed lines:", imp["runner_changed_lines"], "| config changed lines:", imp["config_changed_lines"])
print("all machinery probes unchanged:", imp["all_probes_unchanged"])
print("the only scientific change:", imp["the_only_scientific_change"]["change_id"],
      "-", imp["the_only_scientific_change"]["axis"])
print("  H2A head:", imp["the_only_scientific_change"]["h2a_head"])
print("  H2C head:", imp["the_only_scientific_change"]["h2c_head"])
print("  post-freeze initialization change:", imp["the_only_scientific_change"]["post_freeze_initialization_change"])
print("backbone module modified by H2C:", imp["backbone_module_untouched"]["modified_by_h2c"])
"""))

cells.append(md("""## 7. Audit-Identity Correction (disclosed defect)

The runner inherited Phase-13 audit payload identity strings. The completed run's start/completion
audit payloads mislabel the run; the **scientific state is correct** (the checkpoint records the
H2C head identity and the correct retained H2A focal objective). Corrected additively.
"""))
cells.append(code("""
corr = json.loads((AUDITS / "post_phase13_h2c_b1_audit_identity_correction.json").read_text("utf-8"))
print("classification:", corr["classification"])
print("scientific impact:", corr["scientific_impact"], "| scientific result changed:", corr["scientific_result_changed"])
print("training restarted:", corr["repair_applied"]["training_restarted"])
"""))

cells.append(md("## 8. Population and Training Contract"))
cells.append(code("""
for k, v in te["training_contract"].items():
    print(f"  {k}: {v}")
"""))

cells.append(md("## 9. Head Architecture Specification"))
cells.append(code("""
print("head:", te["head"]["name"])
for x in te["head"]["structure"]:
    print("   ", x)
print("hidden width:", te["head"]["hidden_width"])
print("init:", json.dumps(te["head"]["initialization"], indent=1))
print("parameter contract:", json.dumps(te["head"]["parameter_contract"]))
"""))

cells.append(md("""## 10. Complete Epoch-by-Epoch Table

One completed epoch per row — **all epochs, untruncated, no ellipsis**.
"""))
cells.append(code("""
import pandas as _pd
_pd.set_option("display.max_rows", None); _pd.set_option("display.max_columns", None)
_pd.set_option("display.width", 0); _pd.set_option("display.max_colwidth", None)

_ecols = ["epoch", "train_loss", "val_loss", "proposal_pixel_any_hit_precision",
          "tiny_recall90", "overall_recall90", "deployment_balance_hmean",
          "proposal_total_count", "mean_roi_area_fraction", "selection_tuple",
          "is_new_best", "bad_epochs"]
print("=" * 100)
print(f"COMPLETE EPOCH TABLE — {len(hist)} / {len(hist)} rows")
print("=" * 100)
print(hist[_ecols].to_string(index=False))
print()
assert hist.epoch.is_unique and int(hist.epoch.iloc[0]) == 1
assert bool((hist.epoch.diff().dropna() == 1).all())
print(f"CONFIRMED: {len(hist)} contiguous epochs 1..{int(hist.epoch.iloc[-1])}, no duplicates")
"""))

cells.append(md("## 11. Loss Curves"))
cells.append(code("""
fig, ax = plt.subplots()
ax.plot(hist.epoch, hist.train_loss, marker="o", ms=3, label="train_loss")
ax.plot(hist.epoch, hist.val_loss, marker="s", ms=3, label="val_loss")
ax.set_yscale("log"); ax.set_xlabel("epoch"); ax.set_ylabel("loss")
ax.set_title("H2C train / VAL loss (H2A focal objective; scales NOT comparable to H2A)")
ax.legend(); plt.tight_layout(); plt.show()
"""))

cells.append(md("## 12. P / tiny90 / overall90 Trajectories"))
cells.append(code("""
fig, ax = plt.subplots()
ax.plot(hist.epoch, hist.proposal_pixel_any_hit_precision, marker="o", ms=3, label="P (pixel any-hit precision)")
ax.plot(hist.epoch, hist.tiny_recall90, marker="s", ms=3, label="tiny recall90")
ax.plot(hist.epoch, hist.overall_recall90, marker="^", ms=3, label="overall recall90")
ax.set_xlabel("epoch"); ax.set_ylabel("value"); ax.set_title("P / tiny90 / overall90")
ax.legend(); plt.tight_layout(); plt.show()
"""))

cells.append(md("## 13. Deployment-Balance Trajectory"))
cells.append(code("""
fig, ax = plt.subplots()
ax.plot(hist.epoch, hist.deployment_balance_hmean, marker="o", ms=3, color="tab:green")
be = int(hist.loc[hist.is_new_best.astype(bool), "epoch"].iloc[-1])
ax.axvline(be, color="red", ls="--", lw=1, label=f"best epoch {be}")
ax.set_xlabel("epoch"); ax.set_ylabel("DEPLOYMENT_BALANCE_HMEAN_P_TINY90_OVERALL90")
ax.set_title("Deployment-balance (primary selection term)"); ax.legend()
plt.tight_layout(); plt.show()
print("best epoch:", be)
"""))

cells.append(md("## 14. Proposal Count / Union Area"))
cells.append(code("""
fig, axes = plt.subplots(1, 2, figsize=(13, 4))
axes[0].plot(hist.epoch, hist.proposal_total_count, marker="o", ms=3)
axes[0].set_xlabel("epoch"); axes[0].set_ylabel("proposal_total_count"); axes[0].set_title("Proposal count")
axes[1].plot(hist.epoch, hist.mean_roi_area_fraction, marker="s", ms=3, color="tab:orange")
axes[1].set_xlabel("epoch"); axes[1].set_ylabel("mean_roi_area_fraction"); axes[1].set_title("Mean union area fraction")
plt.tight_layout(); plt.show()
"""))

cells.append(md("## 15. Score-Distribution Diagnostics"))
cells.append(code("""
fig, axes = plt.subplots(1, 2, figsize=(13, 4))
axes[0].plot(hist.epoch, hist.proposal_score_mean, marker="o", ms=3, label="mean")
axes[0].plot(hist.epoch, hist.proposal_score_max, marker="^", ms=3, label="max")
axes[0].set_xlabel("epoch"); axes[0].set_ylabel("score"); axes[0].set_title("Proposal score"); axes[0].legend()
axes[1].plot(hist.epoch, hist.fraction_proposals_exactly_at_epoch_max_score, marker="o", ms=3, color="tab:red")
axes[1].set_ylim(0, 1.05); axes[1].set_xlabel("epoch")
axes[1].set_ylabel("fraction exactly at epoch max"); axes[1].set_title("Score saturation")
plt.tight_layout(); plt.show()
"""))

cells.append(md("## 16. Checkpoint-Selection Events"))
cells.append(code("""
best = hist[hist.is_new_best.astype(bool)]
print("new-best epochs:", best.epoch.tolist())
print()
print(hist[["epoch", "deployment_balance_hmean", "is_new_best", "best_epoch_so_far", "bad_epochs"]].tail(12).to_string(index=False))
"""))

cells.append(md("## 17. Independent Selection Replay"))
cells.append(code("""
rp = json.loads((AUDITS / "post_phase13_h2c_b1_selection_replay_verification.json").read_text("utf-8"))
print("status:", rp["status"], "| mismatches:", rp["mismatch_count"])
print("best epoch replayed/stored:", rp["replayed"]["best_epoch"], "/", rp["stored"]["best_epoch"])
print("max abs term diff:", rp["max_abs_term_diff"])
print("final bad epochs:", rp["replayed"]["final_bad_epochs"])
"""))

cells.append(md("## 18. Standalone Best-Checkpoint Results"))
cells.append(code("""
m = sa["metrics"]
for k in ("proposal_total_count", "proposal_count_per_image", "proposal_pixel_any_hit_precision",
          "proposal_bbox_any_hit_precision", "tiny_recall90", "overall_recall90",
          "overall_recall50", "any_overlap_recall", "mean_coverage", "mean_proposal_union_area",
          "score_max", "score_iqr", "fraction_exactly_at_max",
          "roc_auc_score_to_pixel_any_hit", "pr_auc_score_to_pixel_any_hit"):
    print(f"  {k}: {m[k]}")
print()
print("head statistics at the selected checkpoint (DESCRIPTIVE ONLY):")
for k, v in sa["head_statistics"].items():
    print(f"  {k}: {v}")
"""))

cells.append(md("## 19. Size-Stratified Evidence"))
cells.append(code("""
st = pd.read_csv(TABLES / "post_phase13_h2c_best_checkpoint_size_stratified.csv")
print(st.to_string(index=False))
"""))

cells.append(md("""## 20. Frozen Difficult Cohorts

Global-empty is reported as `GLOBAL_EMPTY_COMPONENTS_WITHIN_5_FROZEN_IMAGES` — never as
"8 global-empty images".
"""))
cells.append(code("""
print("hard_tiny:", json.dumps(sa["metrics"]["hard_tiny"]))
print("global_empty:", json.dumps(sa["metrics"]["global_empty"]))
print("multi_component:", json.dumps(sa["metrics"]["multi_component"]))
"""))

cells.append(md("""## 21. Comparison vs H2A and Phase13

Descriptive single-seed development evidence only. **No winner, no superiority claim, no
significance claim.**
"""))
cells.append(code("""
cmp = pd.read_csv(TABLES / "post_phase13_h2c_vs_h2a_vs_phase13_localizer_comparison.csv")
print(cmp.to_string(index=False))
"""))

cells.append(md("""## 22. Limitations

1. Single-seed adaptive VAL-development evidence.
2. H2C train/val loss magnitudes are **not** comparable to H2A's: the frozen zero-terminal
   initialization makes H2C learn more slowly at first (identical initial loss of 19.119539, but a
   far higher epoch-1 train_loss). There is no cross-branch loss-trajectory gate.
3. The deployment-balanced rule cannot discriminate epochs before proposals appear.
4. Descriptive comparison only — no statistical superiority claim.
5. No threshold search, no proposal grid, no head-family search, no hidden-width search.
6. Head statistics are descriptive only and never influenced selection.
7. The runner's inherited audit-payload identity strings were corrected additively (see §7);
   scientific state unaffected.
8. TEST remains untouched.
"""))

cells.append(md("""## 23. Explicit Downstream Stop Boundary

**H2C-B1 DOES NOT run downstream segmentation.**

Not authorized and not performed: H2C-B2, UNet/Attention/UNet++/DeepLabV3+ regional evaluation,
H1 selective acceptance, fusion redesign, objective change, another head variant, H3, Phase 14,
TEST access.

**H2C outcome is NOT adjudicated here.**
"""))

cells.append(md("## 24. Artifact SHA Registry"))
cells.append(code("""
artifacts = [
    "reports/audits/post_phase13_h2c_protocol_frozen.json",
    "reports/audits/post_phase13_h2c_rng_equivalence_preflight.json",
    "reports/audits/post_phase13_h2c_preexecution_counter_clarification.json",
    "reports/audits/post_phase13_h2c_b1_implementation_diff.json",
    "reports/audits/post_phase13_h2c_b1_training_start.json",
    "reports/audits/post_phase13_h2c_b1_training_completion.json",
    "reports/audits/post_phase13_h2c_b1_audit_identity_correction.json",
    "reports/audits/post_phase13_h2c_b1_selection_replay_verification.json",
    "reports/audits/post_phase13_h2c_best_checkpoint_standalone_evaluation.json",
    "reports/audits/post_phase13_h2c_b1_training_evaluation.json",
    "reports/tables/post_phase13_h2c_best_checkpoint_case_proposals.csv",
    "reports/tables/post_phase13_h2c_best_checkpoint_proposals.csv",
    "reports/tables/post_phase13_h2c_best_checkpoint_component_coverage.csv",
    "reports/tables/post_phase13_h2c_best_checkpoint_size_stratified.csv",
    "reports/tables/post_phase13_h2c_vs_h2a_vs_phase13_localizer_comparison.csv",
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
    _c["id"] = f"h2c{_i:03d}"
nbformat.write(nb, str(NB))
print(f"wrote {len(cells)} cells -> {NB}")
