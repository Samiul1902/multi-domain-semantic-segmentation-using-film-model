"""Build + execute the Phase-20B full scientific-evidence reviewer notebook.

Canonical location::

    notebooks/phasewise/phase_20b_five_model_baselines/
        phase20b_five_model_conventional_baselines.ipynb

The notebook is a thin presentation layer: every table and figure comes from
``src.analysis.phase20b_reviewer`` / ``src.analysis.phase20b_figures``, the same
module functions the driver script calls, so notebook and driver outputs are
byte-identical.

Determinism: deterministic cell ids + stripped ``metadata.execution`` + coalesced
stream outputs + fixed pandas Styler uuids (``set_uuid``) + normalised object memory
addresses in every output text/plain/text/html.

Run::

    D:\\Softfors\\jup\\.venv\\Scripts\\python.exe scripts/notebooks/build_phase20b_notebook.py
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(r"D:/Softfors/jup")
NB_PATH = (ROOT / "notebooks/phasewise/phase_20b_five_model_baselines"
           / "phase20b_five_model_conventional_baselines.ipynb")
NB_PATH.parent.mkdir(parents=True, exist_ok=True)

md = lambda s: nbformat.v4.new_markdown_cell(s.strip("\n"))          # noqa: E731
code = lambda s: nbformat.v4.new_code_cell(s.strip("\n"))            # noqa: E731

cells: list = []

# --------------------------------------------------------------------------- #
# 01 Title
# ---------------------------------------------------------------------------
cells.append(md("""
# Phase 20B — Five-Model Conventional Baseline Benchmark
### Full scientific-evidence reviewer notebook

| Item | Value |
|---|---|
| Phase | 20 (subphase **20B**; 20A = frozen shared UNet++ reference) |
| Canonical folder | `notebooks/phasewise/phase_20b_five_model_baselines/` |
| Models | U-Net · Attention U-Net · U-Net++ (20A) · DeepLabV3+ · Transformer/MiT-style U-Net |
| Protocol | `reports/audits/phase20_shared_global_baseline_protocol.json` (frozen) |
| Manifest | `manifests/phase4_v3` |
| Selection rule | `phase20_macro_domain_mean_dice_v1` |
| Cohorts read | TRAIN and VAL only |
| TEST | `CLOSED` — 0 image reads, 0 mask reads, 0 inference, 0 visualizations |
| Canonical VAL inference runs | exactly **1 per model** |
| Scientific terminal state | `PHASE20_FIVE_MODEL_BASELINE_BENCHMARK_COMPLETE__PHASE21_ELIGIBLE_NOT_STARTED` |

**This notebook runs no training and no inference.** Every number, table and figure is
rebuilt from persisted artifacts (training histories, per-image metric tables, the
persisted per-sample prediction NPZ files, and the frozen comparison/freeze JSON).

**Architecture-naming cautions.** `deeplabv3plus` uses a **random-init** backbone — it is
*not* ImageNet-pretrained. `transformer_mit_unet` is `LOCAL_RANDOM_INIT` — a MiT-*style*
U-Net, *not* official pretrained MiT-B1.
"""))

# --------------------------------------------------------------------------- #
# setup
# ---------------------------------------------------------------------------
cells.append(code("""
import sys, json, warnings
from pathlib import Path
warnings.filterwarnings("ignore")

ROOT = Path(r"D:/Softfors/jup")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
from IPython.display import display, Markdown, Image

from src.analysis import phase20b_reviewer as R
from src.analysis import phase20b_figures as F

# Build every figure + the inventories from persisted artifacts (deterministic, no inference).
CACHE = F.build_all(progress=lambda *a, **k: None)
INV_OUT = F.write_inventories()
FIG = ROOT / "reports/figures/phase20b_five_model_baselines"

def sty(df, uid, fmt=None, **kw):
    \"\"\"Deterministic Styler (fixed uuid => SHA-stable notebook output).\"\"\"
    fmt = {**(fmt or {}), **kw}
    return df.style.format(fmt).set_uuid(uid)

def show_fig(fig_id, width=1150):
    inv = F.figure_inventory()
    row = inv[inv["figure_id"] == fig_id]
    assert len(row) == 1, f"missing figure: {fig_id}"
    p = ROOT / row.iloc[0]["saved_path"]
    display(Markdown(f"*Figure — {row.iloc[0]['title']}*  \\n`{row.iloc[0]['saved_path']}`"))
    display(Image(filename=str(p), width=width))

def show_figs(ids, width=1150):
    for i in ids:
        show_fig(i, width=width)

print("figures built      :", len(F.figure_inventory()))
print("embedded in notebook:", int(F.figure_inventory()["embedded_in_notebook"].sum()))
print("figure root         :", R.rel(FIG))
"""))

# --------------------------------------------------------------------------- #
# 02 Scientific question  +  03 20A -> 20B rationale
# --------------------------------------------------------------------------- #
cells.append(md("""
## 02 · Scientific question  ·  03 · Phase-20A → Phase-20B rationale

**Question.** Given ONE frozen shared four-domain training protocol (identical data,
sampler, loss, optimizer, scheduler, augmentation, threshold and selection rule), how do
**five conventional segmentation architectures** compare across ISIC / BUSI / KVASIR / KUB,
and is the resulting ranking statistically stable?

**Rationale.** Phase 20A established a single frozen shared **UNet++** as the reference
four-domain baseline. Phase 20B answers the obvious follow-up — *is that ranking an
architecture effect or a protocol artifact?* — by adding four more conventional
architectures under the **identical** protocol. Only the model constructor and the
experiment identity vary, so any difference is attributable to the architecture.

Phase 20B is a **subphase of Phase 20**, not a new roadmap phase. The canonical sequence
is `19 → 20A → 20B → 21 → 22 → …`.
"""))
cells.append(code("""
head = R.headline_table()
display(sty(head, "p20b_head",
            {"params": "{:,}", "macro_dice": "{:.6f}", "dice_ci_low": "{:.6f}",
             "dice_ci_high": "{:.6f}", "macro_iou": "{:.6f}"}))
freeze = R.load_freeze()
display(Markdown(f"**Scientific terminal state:** `{freeze['terminal_state']}`  \\n"
                 f"**Top model (observed):** `{freeze['top_model']}`  ·  "
                 f"**top-two margin:** {freeze['top_two_margin']:.6f}  ·  "
                 f"**top-two significant:** {freeze['top_two_ranking_significant']}"))
"""))

# --------------------------------------------------------------------------- #
# 04 Governance / TEST lock  +  05 frozen data population
# --------------------------------------------------------------------------- #
cells.append(md("""
## 04 · Governance / TEST lock  ·  05 · Frozen data population

TEST is content-locked. Only manifest *metadata* is used; no TEST image or mask is ever
opened, decoded, rendered or inferred. Phase 39 remains the only TEST-evaluation phase.
"""))
cells.append(code("""
gov = pd.DataFrame([
    ("manifest version", R.load_protocol()["dataset_populations"]["manifest_version"]),
    ("cohorts read", "TRAIN, VAL"),
    ("TEST image reads", 0), ("TEST mask reads", 0),
    ("TEST inference", 0), ("TEST visualization", 0),
    ("VAL population", freeze["val_population"]),
    ("threshold (frozen)", freeze["threshold"]),
    ("input resolution", freeze["input_resolution"]),
    ("input channel policy", freeze["input_channel_policy"]),
    ("selection rule", freeze["selection_rule_id"]),
    ("canonical VAL inference runs / model", 1),
    ("per-model recipe/threshold change", freeze["no_per_model_recipe_or_threshold_change"]),
], columns=["governance item", "value"])
display(sty(gov, "p20b_gov"))

pop = R.population_table()
display(sty(pop, "p20b_pop"))
cov = R.coverage_matrix()
display(sty(cov, "p20b_cov", {d: "{:d}" for d in R.DATASET_ORDER + ["TOTAL"]}))
assert cov[[*R.DATASET_ORDER, "TOTAL"]].to_numpy().min() > 0
assert (cov["TOTAL"] == 808).all()
display(Markdown(f"Every model was evaluated on the **same 808 VAL cases** "
                 f"(ISIC 357 · BUSI 84 · KVASIR 87 · KUB 280)."))
"""))

# --------------------------------------------------------------------------- #
# 06 preprocessing / input contract  +  07 fairness contract
# --------------------------------------------------------------------------- #
cells.append(md("""
## 06 · Preprocessing / input contract  ·  07 · Fairness contract

The preprocessing and evaluation contracts are the frozen Phase-19 contracts, reused
verbatim. The fairness table below is a field-by-field proof that **only** the model
constructor and the experiment identity differ between the five runs.
"""))
cells.append(code("""
proto = R.load_protocol()
ir = proto["input_representation"]
pc = pd.DataFrame([
    ("preprocessing_contract_id", proto["preprocessing_contract_id"]),
    ("preprocessing_contract_sha256", proto["preprocessing_contract_sha256"]),
    ("evaluation_contract_id", proto["evaluation_contract_id"]),
    ("evaluation_contract_sha256", proto["evaluation_contract_sha256"]),
    ("channel_policy", ir["channel_policy"]),
    ("contract_label", ir["contract_label"]),
    ("intensity_normalization", ir["intensity_normalization"]),
    ("input_resolution", proto["input_resolution"]),
    ("model_input_excludes", ", ".join(ir["model_input_excludes"])),
], columns=["preprocessing field", "value"])
display(sty(pc, "p20b_preproc"))

fair = R.fairness_contract_table()
display(sty(fair, "p20b_fair"))
all_same = bool(fair[fair["field"] != "experiment_id"]["identical_across_models"].all())
display(Markdown(f"**All contract fields identical across the five models:** `{all_same}` — "
                 f"only the model constructor and experiment identity vary."))
assert all_same
"""))

# --------------------------------------------------------------------------- #
# 08 model definitions + 09 parameter counts + 10 provenance
# --------------------------------------------------------------------------- #
cells.append(md("""
## 08 · Five model definitions  ·  09 · Parameter counts  ·  10 · Model provenance / SHAs
"""))
cells.append(code("""
mdl = R.model_definition_table()
display(sty(mdl, "p20b_mdef", {"params": "{:,}"}))
show_fig("efficiency_params_macro")
prov = R.provenance_table()
display(sty(prov, "p20b_prov"))
assert prov["protocol_sha_matches_repo"].all()
display(Markdown("Every model's closure binds the **same** frozen protocol SHA and its own "
                 "model-source / binding / pre-execution-check / history / checkpoint SHAs."))
"""))

# --------------------------------------------------------------------------- #
# 11 training protocol + 12 termination
# --------------------------------------------------------------------------- #
cells.append(md("""
## 11 · Training protocol  ·  12 · Training termination
"""))
cells.append(code("""
tsum = R.training_summary()
display(sty(tsum, "p20b_tsum",
            {"params": "{:,}", "best_macro_domain_dice": "{:.6f}", "best_val_loss": "{:.6f}",
             "total_elapsed_seconds": "{:.1f}", "mean_epoch_seconds": "{:.1f}"}))
c0 = R.load_closure(R.MODEL_ORDER[0])
tp = pd.DataFrame([
    ("loss", json.dumps(c0["configuration"]["loss"])),
    ("optimizer", json.dumps(c0["configuration"]["optimizer"])),
    ("scheduler", json.dumps(c0["configuration"]["scheduler"])),
    ("batch_size / eval_batch_size", f"{c0['configuration']['training']['batch_size']} / "
                                     f"{c0['configuration']['training']['eval_batch_size']}"),
    ("max_epochs / patience", f"{c0['configuration']['training']['max_epochs']} / "
                              f"{c0['configuration']['training']['early_stopping_patience']}"),
    ("amp / seed / grad_accum", f"{c0['configuration']['training']['amp']} / "
                                f"{c0['configuration']['training']['seed']} / "
                                f"{c0['configuration']['training']['gradient_accumulation_steps']}"),
    ("sampling_policy", c0["configuration"]["training"]["sampling_policy"]),
    ("checkpoint_metric", c0["configuration"]["training"]["checkpoint_metric"]),
    ("augmentation", c0["configuration"]["augmentation_policy"]),
], columns=["protocol field", "value"])
display(sty(tp, "p20b_tp"))
display(Markdown(f"All five models stopped by **EARLY_STOPPING_PATIENCE**; "
                 f"no run hit `MAX_EPOCHS` and no `rc=2` governance abort occurred."))
"""))

# --------------------------------------------------------------------------- #
# 13 per-model training histories
# --------------------------------------------------------------------------- #
cells.append(md("""
## 13 · Per-model training histories

For every model: train/val loss, macro-domain Dice, per-domain Dice and IoU, learning-rate
schedule, early-stopping counter, epoch wall-clock duration and best-checkpoint
progression. All curves come from the persisted `history.csv`; **no epoch row is omitted**
and missing data is never plotted as zero.
"""))
for _m in ["unet", "attention_unet", "unetpp", "deeplabv3plus", "transformer_mit_unet"]:
    cells.append(code(f"""
display(Markdown("**{_m}**"))
show_fig("train_overview_{_m}", width=1400)
"""))

cells.append(md("### 13b · Cross-model training overlays"))
cells.append(code("""
show_figs(["train_macro_domain_dice_overlay", "train_val_loss_overlay",
           "train_val_dice_KUB_overlay", "train_epoch_seconds_overlay"], width=1250)
"""))

# --------------------------------------------------------------------------- #
# 14 checkpoint replay + 15 VAL evaluation status
# --------------------------------------------------------------------------- #
cells.append(md("""
## 14 · Checkpoint replay status  ·  15 · Canonical VAL evaluation status

The selection rule is replayed **on disk** over the saved history (no inference): the
history-selected epoch must equal the stored best epoch and the `best.pt` epoch.
"""))
cells.append(code("""
rep = R.replay_summary()
display(sty(rep, "p20b_rep"))
assert rep["all_checks_passed"].all()
assert (rep["history_selected_epoch"] == rep["stored_best_epoch"]).all()
assert (rep["stored_best_epoch"] == rep["best_pt_epoch"]).all()
ve = R.val_eval_summary()
display(sty(ve, "p20b_ve", {"elapsed_seconds": "{:.1f}"}))
assert (ve["samples_evaluated"] == 808).all()
assert (ve["canonical_val_inference_runs"] == 1).all()
assert ve[["test_image_reads", "test_mask_reads", "test_inference", "test_visualization"]].to_numpy().sum() == 0
display(Markdown("All four Phase-20B replays PASS; every model has exactly one canonical "
                 "808-sample VAL pass and **zero** TEST reads."))
"""))

# --------------------------------------------------------------------------- #
# 16 primary five-model comparison
# --------------------------------------------------------------------------- #
cells.append(md("""
## 16 · Primary five-model comparison

Ranked at each model's own best epoch on the identical 808 VAL cases. Error bars are the
deterministic percentile bootstrap 95% CI of the macro-domain mean Dice.
"""))
cells.append(code("""
display(sty(head, "p20b_head2",
            {"params": "{:,}", "macro_dice": "{:.6f}", "dice_ci_low": "{:.6f}",
             "dice_ci_high": "{:.6f}", "macro_iou": "{:.6f}"}))
show_figs(["primary_macro_dice_ci", "primary_macro_iou_bar"], width=1200)
"""))

# --------------------------------------------------------------------------- #
# 17 domain-specific + 18 advanced metric comparison
# --------------------------------------------------------------------------- #
cells.append(md("""
## 17 · Domain-specific results  ·  18 · Complete advanced metric comparison

Every advanced metric that is persisted (Dice, IoU, precision, recall, specificity,
balanced accuracy, MCC, HD95, ASSD, Surface Dice, ROC-AUC, PR-AUC, Brier, ECE, MCE) is
shown as a full model × domain matrix **and** as a heatmap. Unavailable entries are shown
as `NA` — never fabricated.
"""))
cells.append(code("""
d_dice = R.per_domain_table("dice")
display(sty(d_dice, "p20b_pdd", {d: "{:.5f}" for d in R.DATASET_ORDER + ["MACRO"]}))
d_iou = R.per_domain_table("iou")
display(sty(d_iou, "p20b_pdi", {d: "{:.5f}" for d in R.DATASET_ORDER + ["MACRO"]}))
show_fig("primary_per_domain_dice_grouped")
adv = R.macro_advanced_table()
display(sty(adv, "p20b_adv", {m: "{:.4f}" for m in R.ADVANCED_METRICS}))
show_fig("metric_heat_comprehensive", width=1500)
"""))
cells.append(code("""
show_figs(["primary_dice_heatmap", "primary_iou_heatmap",
           "metric_heat_precision", "metric_heat_recall",
           "metric_heat_specificity", "metric_heat_balanced_accuracy",
           "metric_heat_mcc", "metric_heat_hd95",
           "metric_heat_assd", "metric_heat_surface_dice",
           "metric_heat_roc_auc", "metric_heat_pr_auc",
           "metric_heat_brier", "metric_heat_ece",
           "metric_heat_mce"], width=950)
"""))

# --------------------------------------------------------------------------- #
# 19 bootstrap uncertainty + 20 pairwise statistical comparison
# --------------------------------------------------------------------------- #
cells.append(md("""
## 19 · Bootstrap uncertainty  ·  20 · Pairwise statistical comparison

Every model saw the **same 808 VAL samples**, so models are compared *pairwise* with a
**paired domain-stratified percentile bootstrap**: within each domain the same resampled
indices are used for both models, so per-sample difficulty cancels
(`n_boot=2000`, `seed=42`, `alpha=0.05`). A pair is significant when the 95% CI of the
macro-Dice difference excludes zero.
"""))
cells.append(code("""
paired = R.load_paired_bootstrap()
display(sty(paired[["model_a", "model_b", "observed_diff", "diff_ci_low", "diff_ci_high",
                    "p_value_two_sided", "significant_at_0.05"]],
            "p20b_paired",
            {"observed_diff": "{:+.6f}", "diff_ci_low": "{:+.6f}",
             "diff_ci_high": "{:+.6f}", "p_value_two_sided": "{:.3f}"}))
display(sty(R.paired_delta_matrix(), "p20b_delta", {c: "{:+.4f}" for c in R.paired_delta_matrix().columns}))
display(sty(R.pvalue_matrix(), "p20b_pval", {c: "{:.3f}" for c in R.pvalue_matrix().columns}))
show_figs(["boot_delta_matrix", "boot_significance_matrix",
           "boot_pvalue_heatmap", "boot_effect_direction"], width=1000)
"""))
cells.append(code("""
show_fig("boot_ci_forest", width=1150)
tt = freeze["top_two_paired_bootstrap"]
display(Markdown(
  f"**Top-two result.** `{tt['model_a']}` vs `{tt['model_b']}`: "
  f"Δ {tt['observed_diff']:+.6f}, 95% CI "
  f"[{tt['diff_ci_low']:+.6f}, {tt['diff_ci_high']:+.6f}], p={tt['p_value_two_sided']:.3f} → "
  f"**CI crosses zero; the top-two ordering is NOT statistically significant.** "
  f"DeepLabV3+ has the highest *observed* macro-domain Dice but must **not** be called the "
  f"definitive winner."))
assert tt["ci_excludes_zero"] is False
assert tt["significant_at_0.05"] is False
"""))

# --------------------------------------------------------------------------- #
# 26 rank stability
# --------------------------------------------------------------------------- #
cells.append(md("""
## 26 · Rank-stability visualization  *(DESCRIPTIVE_BOOTSTRAP_ANALYSIS)*

Reconstructing the frozen paired resampling and re-ranking the five models in every
replicate shows how stable the ordering is. This is descriptive uncertainty only — it is
**not** a new selection gate.
"""))
cells.append(code("""
rs = R.rank_stability()
display(sty(rs["rank_frequency"], "p20b_rankfreq", {c: "{:.3f}" for c in rs["rank_frequency"].columns}))
show_fig("boot_rank_stability", width=1250)
sup = rs["pairwise_superiority"][("deeplabv3plus", "transformer_mit_unet")]
display(Markdown(f"DeepLabV3+ out-ranks Transformer/MiT-style U-Net in "
                 f"**{sup:.3f}** of bootstrap replicates — i.e. they swap the top two ranks "
                 f"in {1 - sup:.3f} of replicates. Labelled `{rs['label']}`."))
"""))

# --------------------------------------------------------------------------- #
# 21 per-case distributions + 17b model x sample
# --------------------------------------------------------------------------- #
cells.append(md("""
## 21 · Per-case distributions  ·  17b · model × sample performance

Averages hide the tails. Below are per-image box plots, ECDF and violin plots by domain,
plus median/IQR/mean/95% CI summaries.
"""))
cells.append(code("""
pi5 = R.load_per_image_all5()
summ = []
for m in R.MODEL_ORDER:
    for d in R.DATASET_ORDER:
        v = pi5[(pi5["model_key"] == m) & (pi5["dataset"] == d)]["dice"].dropna()
        summ.append({"model": R.DISPLAY[m], "dataset": d, "n": len(v),
                     "median": v.median(), "iqr": v.quantile(.75) - v.quantile(.25),
                     "mean": v.mean(), "p05": v.quantile(.05), "p95": v.quantile(.95)})
summ = pd.DataFrame(summ)
display(sty(summ, "p20b_distsum", {"median": "{:.4f}", "iqr": "{:.4f}", "mean": "{:.4f}",
                                   "p05": "{:.4f}", "p95": "{:.4f}"}))
show_figs(["dist_boxplots", "dist_ecdf_dice", "dist_violin_dice"], width=1400)
"""))
cells.append(code("""
show_fig("dist_sample_heatmap_global", width=1500)
show_fig("dist_sample_heatmap_domains", width=1400)
show_fig("dist_difficult_heatmap", width=1500)
display(Markdown("Sample ordering is deterministic (domain, then `sample_id`) and never "
                 "re-ordered by any single model."))
"""))

# --------------------------------------------------------------------------- #
# 22 confusion-matrix analysis
# --------------------------------------------------------------------------- #
cells.append(md("""
## 22 · Confusion-matrix analysis

Raw and row-normalised pixel confusion matrices for all **5 models × 4 domains** (= 20
groups), plus the pooled descriptive cell, derived sensitivity / FPR / FNR heatmaps.
"""))
cells.append(code("""
ct = R.confusion_table()
display(sty(ct[["model", "scope", "tp", "tn", "fp", "fn",
                "row_norm_gt_fg_tp", "row_norm_gt_fg_fn",
                "row_norm_gt_bg_fp", "row_norm_gt_bg_tn"]], "p20b_conf",
            {"tp": "{:,}", "tn": "{:,}", "fp": "{:,}", "fn": "{:,}",
             "row_norm_gt_fg_tp": "{:.4f}", "row_norm_gt_fg_fn": "{:.4f}",
             "row_norm_gt_bg_fp": "{:.4f}", "row_norm_gt_bg_tn": "{:.4f}"}))
show_figs([f"confusion_{m}" for m in R.MODEL_ORDER], width=1500)
"""))
cells.append(code("""
show_figs(["confusion_sensitivity", "confusion_fpr", "confusion_fnr"], width=1000)
display(Markdown("`row_norm_gt_fg_tp` is the sensitivity (recall); `row_norm_gt_bg_fp` is the "
                 "false-positive rate. Pooled rows are descriptive only."))
"""))

# --------------------------------------------------------------------------- #
# 23 ROC / PR
# --------------------------------------------------------------------------- #
cells.append(md("""
## 23 · ROC / PR analysis

Computed from the **persisted probability maps only** (deterministic pixel subsample,
stride 4 — the same protocol as Phase 20A). No model inference is run. Because
segmentation foreground is highly sparse, **PR-AUC is more informative than ROC-AUC**.
"""))
cells.append(code("""
scal = CACHE["scalars"]
roc = scal.pivot(index="model", columns="dataset", values="roc_auc").reindex(
    [R.DISPLAY[m] for m in R.MODEL_ORDER])[R.DATASET_ORDER]
pr = scal.pivot(index="model", columns="dataset", values="pr_auc").reindex(
    [R.DISPLAY[m] for m in R.MODEL_ORDER])[R.DATASET_ORDER]
display(sty(roc, "p20b_roc", {d: "{:.4f}" for d in R.DATASET_ORDER}))
display(sty(pr, "p20b_prauc", {d: "{:.4f}" for d in R.DATASET_ORDER}))
show_figs(["roc_per_domain", "pr_per_domain", "roc_pr_roc_auc", "roc_pr_pr_auc"], width=1400)
"""))

# --------------------------------------------------------------------------- #
# 24 calibration
# --------------------------------------------------------------------------- #
cells.append(md("""
## 24 · Calibration analysis

Reliability diagrams plus Brier / ECE / MCE per model and domain, using the identical
deterministic calibration protocol as Phase 20A (stride 4, 15 bins).
"""))
cells.append(code("""
brier = scal.pivot(index="model", columns="dataset", values="brier").reindex(
    [R.DISPLAY[m] for m in R.MODEL_ORDER])[R.DATASET_ORDER]
ece = scal.pivot(index="model", columns="dataset", values="ece").reindex(
    [R.DISPLAY[m] for m in R.MODEL_ORDER])[R.DATASET_ORDER]
mce = scal.pivot(index="model", columns="dataset", values="mce").reindex(
    [R.DISPLAY[m] for m in R.MODEL_ORDER])[R.DATASET_ORDER]
display(sty(brier, "p20b_brier", {d: "{:.4f}" for d in R.DATASET_ORDER}))
display(sty(ece, "p20b_ece", {d: "{:.4f}" for d in R.DATASET_ORDER}))
display(sty(mce, "p20b_mce", {d: "{:.4f}" for d in R.DATASET_ORDER}))
show_figs(["calib_reliability", "calib_ece", "calib_brier", "calib_mce"], width=1250)
"""))

# --------------------------------------------------------------------------- #
# 25 boundary quality
# --------------------------------------------------------------------------- #
cells.append(md("""
## 25 · Boundary-quality analysis

HD95, ASSD and Surface Dice per model and domain. Boundary metrics are computed only where
both masks are non-empty; the frozen sentinel rule excludes invalid cases from the mean and
reports the valid count (`hd95_valid_n`, `surface_dice_valid_n`).
"""))
cells.append(code("""
for met, uid in [("hd95", "p20b_hd95"), ("assd", "p20b_assd"), ("surface_dice", "p20b_sd")]:
    m = R.domain_metric_matrix(met).set_index("model")[R.DATASET_ORDER]
    display(sty(m.reset_index(), uid, {d: "{:.4f}" for d in R.DATASET_ORDER}))
show_figs(["boundary_hd95", "boundary_assd", "boundary_surface_dice", "boundary_grouped_bars"],
          width=1400)
"""))

# --------------------------------------------------------------------------- #
# 27 KUB subgroups
# --------------------------------------------------------------------------- #
cells.append(md("""
## 27 · KUB subgroup analysis  *(REPORTING ONLY)*

Kidney / Bladder / Ureteric stone subgroups plus `KUB_ALL`. These native category labels are
**reporting only** and are never model inputs.
"""))
cells.append(code("""
subs = ["Kidney_Stone", "Bladder_Stone", "Ureteric_Stone", "KUB_ALL"]
for met, uid in [("dice", "p20b_subd"), ("recall", "p20b_subr")]:
    m = R.kub_subgroup_matrix(met)
    display(sty(m, uid, {s: "{:.4f}" for s in subs}))
show_figs(["kubsub_dice_heatmap", "kubsub_dice_bars",
           "kubsub_recall_heatmap", "kubsub_empty_rate"], width=1100)
"""))

# --------------------------------------------------------------------------- #
# 28 KUB size strata
# --------------------------------------------------------------------------- #
cells.append(md("""
## 28 · KUB size-stratification analysis

Frozen taxonomy `kub_size_clean_v3_v1` only: FULL_FIELD strata TINY / SMALL / MEDIUM /
LARGE, with `ROI_NOT_PRIMARY_BINNED` kept **separate** because ROI crops are a different
acquisition regime and are not directly comparable.
"""))
cells.append(code("""
strata = ["TINY", "SMALL", "MEDIUM", "LARGE", "ROI_NOT_PRIMARY_BINNED"]
ns = R.kub_size_n()
display(Markdown("stratum n: " + ", ".join(f"{k}={v}" for k, v in ns.items())))
for met, uid in [("dice", "p20b_szd"), ("iou", "p20b_szi")]:
    m = R.kub_size_matrix(met)
    display(sty(m, uid, {s: "{:.4f}" for s in strata}))
show_figs(["kubsize_dice_heatmap", "kubsize_dice_bars",
           "kubsize_interaction", "kubsize_roi_vs_ff"], width=1150)
"""))

# --------------------------------------------------------------------------- #
# 29 TINY-target analysis
# --------------------------------------------------------------------------- #
cells.append(md("""
## 29 · TINY-target special analysis

KUB tiny objects are the project's known bottleneck. Below: TINY Dice distribution, TINY
per-case heatmap, and TINY-vs-overall decoupling, for all five models.
"""))
cells.append(code("""
tiny = R.tiny_per_sample()
tstat = tiny.groupby("model")["dice"].agg(["count", "mean", "median",
                                           lambda s: s.quantile(.25),
                                           lambda s: s.quantile(.75)])
tstat.columns = ["n", "mean", "median", "q25", "q75"]
display(sty(tstat.reset_index(), "p20b_tiny", {"mean": "{:.4f}", "median": "{:.4f}",
                                               "q25": "{:.4f}", "q75": "{:.4f}"}))
show_figs(["tiny_dice_distribution", "tiny_case_heatmap", "tiny_vs_macro"], width=1300)
"""))

# --------------------------------------------------------------------------- #
# 30 empty prediction + 31 FP/FN burden
# --------------------------------------------------------------------------- #
cells.append(md("""
## 30 · Empty-prediction analysis  ·  31 · FP / FN burden analysis
"""))
cells.append(code("""
emp = R.empty_prediction_table()
display(sty(emp[["model", "dataset", "n", "gt_empty_n", "pred_empty_n", "empty_prediction_rate",
                 "gt_empty_pred_nonempty_n", "gt_nonempty_pred_empty_n"]], "p20b_empty",
            {"empty_prediction_rate": "{:.4f}"}))
fb = R.failure_burden_table()
display(sty(fb[["model", "dataset", "mean_fp_pixels", "mean_fn_pixels",
                "fp_burden_ratio", "fn_burden_ratio", "complete_miss_n", "fp_on_empty_gt_n"]],
            "p20b_fb", {"mean_fp_pixels": "{:.1f}", "mean_fn_pixels": "{:.1f}",
                        "fp_burden_ratio": "{:.4f}", "fn_burden_ratio": "{:.4f}"}))
show_figs(["failure_fp_burden_ratio", "failure_fn_burden_ratio", "failure_counts"], width=1400)
"""))

# --------------------------------------------------------------------------- #
# 32 common failure analysis
# --------------------------------------------------------------------------- #
cells.append(md("""
## 32 · Common-failure analysis  *(OUTCOME-BASED galleries)*

These galleries are **outcome-based analytical** selections with deterministic, reported
rules. They are deliberately **not** the prediction-independent canonical 64-case gallery.
"""))
cells.append(code("""
rules = F.figure_inventory()
rules = rules[rules["figure_id"] == "failure_gallery_selection_rules"]
if len(rules):
    display(Markdown("**Selection rules (first cases per rule):**  \\n`" +
                     rules.iloc[0]["status"] + "`"))
show_figs(["failure_gallery_all_models_fail", "failure_gallery_two_stage_success_unet_fail",
           "failure_gallery_unet_family_success", "failure_gallery_max_disagreement",
           "failure_gallery_kub_tiny_misses", "failure_gallery_fp_heavy",
           "failure_gallery_fn_heavy"], width=1400)
"""))

# --------------------------------------------------------------------------- #
# 33 efficiency + 34 Pareto + 35 radar
# --------------------------------------------------------------------------- #
cells.append(md("""
## 33 · Efficiency / complexity analysis  ·  34 · Pareto analysis  ·  35 · Radar (supplemental)

Parameters, checkpoint size, training cost and (where persisted) inference cost. `NA` is
used where a quantity was never measured — nothing is re-benchmarked to fill a gap.
"""))
cells.append(code("""
eff = R.efficiency_table()
display(sty(eff, "p20b_eff",
            {"params": "{:,}", "checkpoint_bytes": "{:,.0f}", "total_training_seconds": "{:,.1f}",
             "mean_epoch_seconds": "{:,.1f}", "inference_seconds_808": "{:,.1f}",
             "inference_ms_per_sample": "{:,.2f}"}))
show_figs(["efficiency_params_macro", "efficiency_params_kub", "efficiency_params_tiny",
           "efficiency_time_macro", "efficiency_inference_macro"], width=1050)
"""))
cells.append(code("""
show_figs(["pareto_params_macro", "pareto_time_macro", "pareto_tiny_macro"], width=1050)
show_fig("efficiency_radar", width=1000)
display(Markdown("Pareto fronts are **descriptive** — they show trade-offs and do not declare "
                 "an absolute winner. The radar is supplemental only."))
"""))

# --------------------------------------------------------------------------- #
# 36 cross-model agreement
# --------------------------------------------------------------------------- #
cells.append(md("""
## 36 · Cross-model agreement / disagreement
"""))
cells.append(code("""
corr = R.cross_model_dice_correlation("dice")
display(sty(corr.reset_index(), "p20b_corr", {c: "{:.3f}" for c in corr.columns}))
show_figs(["agree_corr_matrix", "agree_pairwise_scatter", "agree_disagreement"], width=1400)
"""))

# --------------------------------------------------------------------------- #
# 37 same-case cross-model gallery
# --------------------------------------------------------------------------- #
cells.append(md("""
## 37 · Qualitative same-case comparison — the frozen 64-case gallery

The **same** 64 deterministically selected VAL cases (16 per domain, prediction-independent,
seed 42) shown for all five models. Error maps: **TP green / FP red / FN blue**. The sample
IDs are byte-identical to the frozen Phase-20A gallery set, so Phase 21 can reuse them.
"""))
cells.append(code("""
gal = R.load_gallery()
display(sty(gal.groupby("dataset").size().reset_index(name="cases"), "p20b_gal"))
assert len(gal) == 64 and freeze["gallery_ids_match_phase20a_frozen_set"]
show_figs([f"gallery_cross_{i:02d}" for i in range(1, 17)], width=1500)
"""))

# --------------------------------------------------------------------------- #
# 38 detailed per-model galleries
# --------------------------------------------------------------------------- #
cells.append(md("""
## 38 · Detailed per-model prediction evidence

Per model × dataset × 16 cases, with panels: Original · GT · GT overlay · probability ·
binary prediction · TP/FP/FN error map · prediction overlay · GT contour. The full set is
**5 models × 4 datasets × 16 cases = 320 cases**; all pages are saved to disk and listed in
the figure inventory. One representative page per model/dataset is embedded here.
"""))
cells.append(code("""
det = F.figure_inventory()
det = det[det["category"] == "gallery"]
det = det[det["figure_id"].str.startswith("gallery_detailed_")]
print("detailed gallery pages on disk:", len(det))
display(sty(det[["figure_id", "saved_path", "embedded_in_notebook"]].reset_index(drop=True),
            "p20b_det"))
show_figs([f"gallery_detailed_{m}_{d}_1" for m in R.MODEL_ORDER for d in R.DATASET_ORDER],
          width=1500)
"""))

# --------------------------------------------------------------------------- #
# 39 what all models solve / fail
# --------------------------------------------------------------------------- #
cells.append(md("""
## 39 · What all models solve  ·  40 · What all models fail
"""))
cells.append(code("""
mat = R.model_sample_matrix("dice")
dmap = R.sample_domain_map()
solved = (mat.min(axis=0) >= 0.90)
failed = (mat.max(axis=0) <= 0.30)
df = pd.DataFrame({"dataset": [dmap[s] for s in mat.columns],
                   "solved_by_all": solved.to_numpy(), "failed_by_all": failed.to_numpy()})
summ = df.groupby("dataset")[["solved_by_all", "failed_by_all"]].sum().reset_index()
summ["n"] = summ["dataset"].map(df.groupby("dataset").size())
display(sty(summ, "p20b_sf"))
display(Markdown(f"**Solved by all five models (Dice ≥ 0.90 in every model): "
                 f"{int(solved.sum())}/{len(mat.columns)} cases.**  \\n"
                 f"**Failed by all five models (best model Dice ≤ 0.30): {int(failed.sum())} cases.**"))
"""))

# --------------------------------------------------------------------------- #
# 41 statistical interpretation
# --------------------------------------------------------------------------- #
cells.append(md("""
## 41 · Statistical interpretation

- **Two-tier structure is significant.** Each two-stage architecture (DeepLabV3+,
  Transformer/MiT-style U-Net) beats every U-Net-family variant with a paired CI that
  excludes zero (p ≈ 0.000).
- **The top-two ordering is NOT significant.** DeepLabV3+ vs Transformer/MiT-style U-Net
  gives Δ ≈ +0.005270 with a 95% CI that crosses zero (p ≈ 0.282), and the two models swap
  the top-two ranks in ≈10% of bootstrap replicates. DeepLabV3+ has the highest *observed*
  macro-domain Dice; it is **not** a statistically separated winner.
"""))
cells.append(code("""
two_tier = paired[(paired["model_a"].isin(["deeplabv3plus", "transformer_mit_unet"])
                   & paired["model_b"].isin(["unet", "attention_unet", "unetpp"]))
                  | (paired["model_b"].isin(["deeplabv3plus", "transformer_mit_unet"])
                     & paired["model_a"].isin(["unet", "attention_unet", "unetpp"]))]
display(sty(two_tier[["model_a", "model_b", "observed_diff", "diff_ci_low", "diff_ci_high",
                      "p_value_two_sided", "significant_at_0.05"]], "p20b_2tier",
            {"observed_diff": "{:+.6f}", "diff_ci_low": "{:+.6f}",
             "diff_ci_high": "{:+.6f}", "p_value_two_sided": "{:.3f}"}))
assert two_tier["significant_at_0.05"].all()
assert freeze["top_two_ranking_significant"] is False
display(Markdown("Tier separation significant ✓ · top-two ordering not significant ✓"))
"""))

# --------------------------------------------------------------------------- #
# 42 limitations
# --------------------------------------------------------------------------- #
cells.append(md("""
## 42 · Limitations

- **VAL-only.** All numbers are on the 808-case VAL split. TEST stays closed (Phase 39).
- **Single seed (42) per model.** No seed-replication, so architecture-level variance is not
  separated from seed variance; the paired bootstrap quantifies *sampling* uncertainty on
  the fixed VAL set, not training-seed uncertainty.
- **Top-two tie.** DeepLabV3+ and Transformer/MiT-style U-Net are statistically
  indistinguishable under this protocol; no definitive winner is claimed.
- **`deeplabv3plus` is random-init** (not ImageNet-pretrained) and `transformer_mit_unet` is
  `LOCAL_RANDOM_INIT` (not official pretrained MiT-B1) — so these are *not* the published
  pretrained variants.
- **KUB ROI vs FULL_FIELD** are different acquisition regimes; ROI cases are reported
  separately and are not directly comparable with FULL_FIELD strata.
- **Boundary metrics** are undefined for empty masks; the frozen sentinel rule excludes
  those cases and reports valid counts.
- **Descriptive additions.** ROC/PR curves, reliability diagrams, rank stability, efficiency
  and Pareto analyses are *descriptive*; they reuse frozen artifacts and change no frozen
  value.
"""))

# --------------------------------------------------------------------------- #
# 43 freeze + 44 provenance / hashes
# --------------------------------------------------------------------------- #
cells.append(md("""
## 43 · Baseline benchmark freeze  ·  44 · Provenance / hashes
"""))
cells.append(code("""
display(Markdown(f"**Frozen science artifact:** `reports/audits/phase20_five_model_baseline_benchmark_freeze.json`"))
display(sty(pd.DataFrame(sorted({
    "terminal_state": freeze["terminal_state"],
    "protocol_sha256": freeze["protocol_sha256"],
    "protocol_matches_expected": freeze["protocol_sha256"] == freeze["protocol_sha256_expected"],
    "per_model_replay_all_pass": freeze["per_model_replay_all_pass"],
    "gallery_ids_match_phase20a": freeze["gallery_ids_match_phase20a_frozen_set"],
    "test_reads_total_zero": all(v == 0 for v in freeze["test_reads_total"].values()),
    "phase21_started": freeze["phase21_started"],
}.items()), columns=["freeze item", "value"]), "p20b_fz"))
display(sty(prov, "p20b_prov2"))
display(Markdown("**Additive reviewer-package companion:** "
                 "`reports/audits/phase20b_reviewer_package_freeze.json` (documentation/provenance only; "
                 "the historical freeze is not rewritten)."))
assert freeze["protocol_sha256"] == freeze["protocol_sha256_expected"]
assert freeze["per_model_replay_all_pass"] is True
assert all(v == 0 for v in freeze["test_reads_total"].values())
"""))

# --------------------------------------------------------------------------- #
# 30b visualization coverage + 43b determinism
# --------------------------------------------------------------------------- #
cells.append(md("""
## 45 · Evaluation-matrix visualization coverage  ·  46 · Notebook determinism

Every important evaluation matrix has a visual counterpart. The coverage table below is the
machine-checkable proof, and the notebook itself is byte-deterministic across rebuilds.
"""))
cells.append(code("""
cov = F.matrix_coverage()
display(sty(cov[["matrix_name", "source_artifact", "visualization_type", "status"]], "p20b_covm"))
frac = (cov["status"] == "VISUALIZED").mean()
print("evaluation matrices:", len(cov), "| visualized:", int((cov['status'] == 'VISUALIZED').sum()),
      "| coverage:", round(float(frac), 4))
assert frac == 1.0
inv = F.figure_inventory()
print("figures total:", len(inv), "| embedded:", int(inv['embedded_in_notebook'].sum()))
display(sty(inv.groupby("category").size().reset_index(name="figures"), "p20b_invg"))
"""))

# --------------------------------------------------------------------------- #
# 47 Phase-21 entry status
# --------------------------------------------------------------------------- #
cells.append(md("""
## 47 · Phase-21 entry status

Phase 21 (Global MedFiLM) is **ELIGIBLE but NOT STARTED**. All entry criteria are met and
the Phase-20 five-model baseline is frozen, but starting Phase 21 requires **fresh
supervisor authorization**. Phase 21 must be compared on the **same 64** gallery cases.
"""))
cells.append(code("""
p21 = json.loads((ROOT / "reports/audits/phase20_phase21_entry_criteria.json").read_text(encoding="utf-8"))
crit = pd.DataFrame(p21["criteria"])
display(sty(crit, "p20b_p21"))
met = int(crit["met"].sum()) if "met" in crit.columns else sum(1 for c in p21["criteria"] if c["met"])
print(f"Phase-21 entry criteria met: {met}/{len(p21['criteria'])} | may_start: {p21.get('phase21_may_start')}")
assert p21.get("phase21_may_start") is False
assert freeze["phase21_started"] is False
"""))

# --------------------------------------------------------------------------- #
# 45 final assertions
# --------------------------------------------------------------------------- #
cells.append(md("## 48 · Final assertions"))
cells.append(code("""
checks = {
  "five models present": len(head) == 5,
  "terminal state correct": freeze["terminal_state"] == "PHASE20_FIVE_MODEL_BASELINE_BENCHMARK_COMPLETE__PHASE21_ELIGIBLE_NOT_STARTED",
  "protocol SHA matches": freeze["protocol_sha256"] == freeze["protocol_sha256_expected"],
  "all replays PASS": freeze["per_model_replay_all_pass"] is True,
  "every model 808 VAL": (ve["samples_evaluated"] == 808).all(),
  "exactly 1 canonical pass/model": (ve["canonical_val_inference_runs"] == 1).all(),
  "TEST reads total = 0": all(v == 0 for v in freeze["test_reads_total"].values()),
  "no per-model recipe change": freeze["no_per_model_recipe_or_threshold_change"] is True,
  "threshold unchanged (0.5)": freeze["threshold"] == 0.5,
  "top-two NOT significant": freeze["top_two_ranking_significant"] is False,
  "gallery = 64 frozen IDs": len(gal) == 64 and freeze["gallery_ids_match_phase20a_frozen_set"],
  "matrix coverage = 100%": (cov["status"] == "VISUALIZED").all(),
  "figures embedded": int(inv["embedded_in_notebook"].sum()) > 0,
  "phase21 not started": freeze["phase21_started"] is False,
}
res = pd.DataFrame(sorted(checks.items()), columns=["assertion", "passed"])
display(sty(res, "p20b_assert"))
assert all(checks.values()), [k for k, v in checks.items() if not v]
print("All Phase-20B reviewer-package assertions passed.")
print("SCIENTIFIC TERMINAL STATE:", freeze["terminal_state"])
print("REVIEWER-PACKAGE STATE   : PHASE20B_REVIEWER_PACKAGE_COMPLETE__FULL_VISUAL_EVIDENCE__PHASE21_ELIGIBLE_NOT_STARTED")
"""))

# --------------------------------------------------------------------------- #
# write + execute
# --------------------------------------------------------------------------- #
nb = nbformat.v4.new_notebook(cells=cells)
for _i, _c in enumerate(nb.cells):
    _c["id"] = f"p20b{_i:03d}"
nbformat.write(nb, str(NB_PATH))
print(f"Wrote {NB_PATH} ({len(nb.cells)} cells)")
print("Executing ...")
client = NotebookClient(nb, kernel_name="jup-venv", timeout=5400,
                        resources={"metadata": {"path": str(ROOT)}})
client.execute()

# deterministic post-processing
for _c in nb.cells:
    if isinstance(_c.get("metadata"), dict):
        _c["metadata"].pop("execution", None)
    _outs = _c.get("outputs")
    if _outs:
        _merged = []
        for _o in _outs:
            if (_o.get("output_type") == "stream" and _merged
                    and _merged[-1].get("output_type") == "stream"
                    and _merged[-1].get("name") == _o.get("name")):
                _p = _merged[-1]
                _pt, _ct = _p.get("text", ""), _o.get("text", "")
                if isinstance(_pt, list):
                    _pt = "".join(_pt)
                if isinstance(_ct, list):
                    _ct = "".join(_ct)
                _p["text"] = _pt + _ct
            else:
                _merged.append(_o)
        _c["outputs"] = _merged

# normalise object memory addresses (pandas Styler reprs print "<... at 0x...>")
_ADDR = re.compile(r"0x[0-9a-fA-F]{6,}")
for _c in nb.cells:
    for _o in _c.get("outputs", []) or []:
        _d = _o.get("data")
        if isinstance(_d, dict):
            for _k, _v in list(_d.items()):
                if isinstance(_v, str):
                    _d[_k] = _ADDR.sub("0xADDR", _v)
                elif isinstance(_v, list):
                    _d[_k] = [_ADDR.sub("0xADDR", _s) if isinstance(_s, str) else _s for _s in _v]
        _t = _o.get("text")
        if isinstance(_t, str):
            _o["text"] = _ADDR.sub("0xADDR", _t)
        elif isinstance(_t, list):
            _o["text"] = [_ADDR.sub("0xADDR", _s) if isinstance(_s, str) else _s for _s in _t]
nbformat.write(nb, str(NB_PATH))

code_cells = [c for c in nb.cells if c.cell_type == "code"]
errors = sum(1 for c in code_cells for o in c.get("outputs", []) if o.get("output_type") == "error")
counts = [c.get("execution_count") for c in code_cells]
monotonic = all(counts[i] == i + 1 for i in range(len(counts)))
pngs = sum(1 for c in code_cells for o in c.get("outputs", [])
           if "image/png" in (o.get("data", {}) or {}))
htmls = sum(1 for c in code_cells for o in c.get("outputs", [])
            if "text/html" in (o.get("data", {}) or {}))
print(f"Cells: {len(nb.cells)} | markdown: {sum(1 for c in nb.cells if c.cell_type=='markdown')} "
      f"| code: {len(code_cells)}")
print("Zero tracebacks:", "PASS" if errors == 0 else f"FAIL ({errors})")
print("Monotonic exec counts (1..%d): %s" % (len(code_cells), "PASS" if monotonic else "FAIL"))
print(f"image/png outputs: {pngs} | html table outputs: {htmls}")
print("Notebook SHA:", hashlib.sha256(NB_PATH.read_bytes()).hexdigest())
