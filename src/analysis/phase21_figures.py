"""Phase 21 — figure generation for the Global MedFiLM reference.

Every figure is built from persisted artifacts only (training history, metric
tables, prediction NPZs, manifest image paths). No inference, no TEST, no
checkpoint load (except the pure-metadata efficiency figures).

Figures are written under ``reports/figures/phase21_global_medfilm/<group>/`` and
registered so the notebook can embed the exact same bytes and the figure
inventory / visualization-coverage audits can be produced.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
TABLE_DIR = ROOT / "reports" / "tables"
AUDIT_DIR = ROOT / "reports" / "audits"
FIG_ROOT = ROOT / "reports" / "figures" / "phase21_global_medfilm"

EXP = "phase21_global_medfilm_fourdomain_seed42_clean_v3"
DATASET_ORDER = ["ISIC", "BUSI", "KVASIR", "KUB"]
MODEL_ORDER = ["unet", "attention_unet", "unetpp", "deeplabv3plus",
               "transformer_mit_unet", "global_medfilm"]
DISPLAY = {"unet": "U-Net", "attention_unet": "Attention U-Net", "unetpp": "U-Net++",
           "deeplabv3plus": "DeepLabV3+", "transformer_mit_unet": "Transformer/MiT",
           "global_medfilm": "Global MedFiLM"}
SLUG = {"global_medfilm": "global_medfilm"}

_REG: list[dict] = []


def _mpl():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    return plt


def rel(p: Path) -> str:
    return str(Path(p).relative_to(ROOT)).replace("\\", "/")


def _save_fig(fig, group: str, name: str, *, fig_id: str, title: str, purpose: str,
              source: str, models: str, datasets: str, metrics: str,
              embedded: bool = True, category: str = "", dpi: int = 110) -> Path:
    plt = _mpl()
    d = FIG_ROOT / group
    d.mkdir(parents=True, exist_ok=True)
    p = d / name
    fig.tight_layout()
    fig.savefig(p, dpi=dpi)
    plt.close(fig)
    _REG.append({
        "figure_id": fig_id, "title": title, "scientific_purpose": purpose,
        "source_artifacts": source, "models": models, "datasets": datasets,
        "metrics": metrics, "saved_path": rel(p), "group": group,
        "category": category, "embedded_in_notebook": bool(embedded),
        "image_png_output_present": bool(embedded), "status": "OK",
    })
    return p


def reset_registry() -> None:
    _REG.clear()


def figure_inventory() -> pd.DataFrame:
    cols = ["figure_id", "title", "scientific_purpose", "source_artifacts", "models",
            "datasets", "metrics", "saved_path", "group", "category",
            "embedded_in_notebook", "image_png_output_present", "status"]
    return pd.DataFrame(_REG)[cols] if _REG else pd.DataFrame(columns=cols)


# --------------------------------------------------------------------------- #
# loaders
# --------------------------------------------------------------------------- #
def load_history() -> pd.DataFrame:
    return pd.read_csv(ROOT / "experiments" / EXP / "history.csv")


def load_comparison() -> pd.DataFrame:
    return pd.read_csv(TABLE_DIR / "phase21_six_model_comparison.csv")


def load_domain_perf() -> pd.DataFrame:
    return pd.read_csv(TABLE_DIR / "phase21_global_medfilm_domain_performance.csv")


def load_paired() -> pd.DataFrame:
    return pd.read_csv(TABLE_DIR / "phase21_paired_bootstrap_vs_baselines.csv")


def load_kub_subgroup() -> pd.DataFrame:
    return pd.read_csv(TABLE_DIR / "phase21_kub_subgroup_analysis.csv")


def load_kub_size() -> pd.DataFrame:
    return pd.read_csv(TABLE_DIR / "phase21_kub_size_stratification.csv")


def load_film_summary() -> pd.DataFrame:
    return pd.read_csv(TABLE_DIR / "phase21_film_parameter_summary.csv")


def load_conditioning() -> pd.DataFrame:
    return pd.read_csv(TABLE_DIR / "phase21_task_conditioning_diagnostic.csv")


def load_per_image(model_key: str) -> pd.DataFrame:
    if model_key == "global_medfilm":
        df = pd.read_csv(TABLE_DIR / "phase21_per_image_val_metrics.csv")
    elif model_key == "unetpp":
        df = pd.read_csv(TABLE_DIR / "phase20_per_image_val_metrics.csv")
    else:
        df = pd.read_csv(TABLE_DIR / f"phase20b_{model_key}_per_image_val_metrics.csv")
    df["sample_id"] = df["sample_id"].astype(str)
    return df


def load_val_manifest() -> pd.DataFrame:
    df = pd.read_csv(ROOT / "manifests" / "phase4_v3" / "val.csv")
    df["sample_id"] = df["sample_id"].astype(str)
    return df


def load_pred_manifest() -> pd.DataFrame:
    df = pd.read_csv(TABLE_DIR / "phase21_prediction_manifest.csv")
    df["sample_id"] = df["sample_id"].astype(str)
    return df


def load_prediction(npz_rel: str) -> dict:
    z = np.load(ROOT / npz_rel)
    return {"prob": z["prob"].astype(np.float32), "pred": z["pred"].astype(bool),
            "gt": z["gt"].astype(bool)}


# --------------------------------------------------------------------------- #
# 1. training figures
# --------------------------------------------------------------------------- #
def build_training_figures() -> None:
    plt = _mpl()
    h = load_history()
    best_ep = int(h.loc[h["macro_domain_dice"].idxmax(), "epoch"])
    src = f"experiments/{EXP}/history.csv"

    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.plot(h["epoch"], h["train_loss"], label="train loss", lw=1.6)
    ax.plot(h["epoch"], h["val_loss"], label="val loss", lw=1.6)
    ax.axvline(best_ep, color="crimson", ls="--", lw=1.2, label=f"best epoch {best_ep}")
    ax.set_xlabel("epoch"); ax.set_ylabel("loss")
    ax.set_title("Global MedFiLM — training and validation loss")
    ax.legend(); ax.grid(alpha=0.3)
    _save_fig(fig, "training", "training_loss.png", fig_id="p21_train_loss",
              title="Training and validation loss",
              purpose="Show optimisation progress and whether the run overfits.",
              source=src, models="global_medfilm", datasets="ALL",
              metrics="loss", category="TRAINING")

    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.plot(h["epoch"], h["macro_domain_dice"], lw=1.8, color="tab:blue",
            label="macro-domain VAL Dice")
    ax.plot(h["epoch"], h["best_so_far"], lw=1.3, ls="--", color="tab:green",
            label="best so far")
    ax.scatter([best_ep], [h["macro_domain_dice"].max()], s=60, zorder=5,
               color="crimson", label=f"selected epoch {best_ep}")
    ax.set_xlabel("epoch"); ax.set_ylabel("macro-domain Dice")
    ax.set_title("Global MedFiLM — macro-domain VAL Dice and frozen selection")
    ax.legend(); ax.grid(alpha=0.3)
    _save_fig(fig, "training", "training_macro_dice.png", fig_id="p21_train_macro",
              title="Macro-domain VAL Dice with the frozen selection marker",
              purpose="Evidence that checkpoint selection used the frozen macro-domain rule.",
              source=src, models="global_medfilm", datasets="MACRO_DOMAIN",
              metrics="dice", category="TRAINING")

    fig, ax = plt.subplots(figsize=(8, 4.2))
    for d in DATASET_ORDER:
        ax.plot(h["epoch"], h[f"val_dice_{d}"], lw=1.5, label=d)
    ax.axvline(best_ep, color="crimson", ls="--", lw=1.1)
    ax.set_xlabel("epoch"); ax.set_ylabel("per-domain Dice")
    ax.set_title("Global MedFiLM — per-domain VAL Dice")
    ax.legend(ncol=4, fontsize=8); ax.grid(alpha=0.3)
    _save_fig(fig, "training", "training_per_domain_dice.png", fig_id="p21_train_domain_dice",
              title="Per-domain VAL Dice curves",
              purpose="Show how each of the four domains evolved and which one dominates the macro mean.",
              source=src, models="global_medfilm", datasets="ISIC/BUSI/KVASIR/KUB",
              metrics="dice", category="TRAINING")

    fig, ax = plt.subplots(figsize=(8, 3.6))
    ax.plot(h["epoch"], h["learning_rate"], lw=1.6, color="tab:orange")
    ax.set_xlabel("epoch"); ax.set_ylabel("learning rate")
    ax.set_title("Cosine annealing schedule (T_max=100)")
    ax.grid(alpha=0.3)
    _save_fig(fig, "training", "training_lr_schedule.png", fig_id="p21_train_lr",
              title="Learning-rate schedule",
              purpose="Confirm the inherited CosineAnnealingLR schedule stepped once per epoch.",
              source=src, models="global_medfilm", datasets="ALL",
              metrics="learning_rate", category="TRAINING")

    fig, ax = plt.subplots(figsize=(8, 3.6))
    ax.plot(h["epoch"], h["bad_epochs"], lw=1.6, color="tab:red")
    ax.axhline(15, color="black", ls=":", lw=1.2, label="patience = 15")
    ax.set_xlabel("epoch"); ax.set_ylabel("consecutive non-improving epochs")
    ax.set_title("Early-stopping counter")
    ax.legend(); ax.grid(alpha=0.3)
    _save_fig(fig, "training", "training_early_stop.png", fig_id="p21_train_earlystop",
              title="Early-stopping counter",
              purpose="Show the frozen patience-15 rule and where it tripped.",
              source=src, models="global_medfilm", datasets="ALL",
              metrics="bad_epochs", category="TRAINING")

    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.plot(h["epoch"], h["epoch_seconds"], lw=1.2, color="tab:purple")
    ax.axhline(h["epoch_seconds"].median(), color="black", ls="--", lw=1.1,
               label=f"median {h['epoch_seconds'].median():.0f}s")
    ax.set_xlabel("epoch"); ax.set_ylabel("seconds per epoch")
    ax.set_title("Per-epoch wall time")
    ax.legend(); ax.grid(alpha=0.3)
    _save_fig(fig, "training", "training_epoch_time.png", fig_id="p21_train_epoch_time",
              title="Per-epoch wall time",
              purpose="Document training throughput for the compute accounting.",
              source=src, models="global_medfilm", datasets="ALL",
              metrics="epoch_seconds", category="TRAINING")


# --------------------------------------------------------------------------- #
# 2. six-model comparison
# --------------------------------------------------------------------------- #
def build_primary_figures() -> None:
    plt = _mpl()
    c = load_comparison().sort_values("macro_domain_dice", ascending=False)
    src = "reports/tables/phase21_six_model_comparison.csv"

    fig, ax = plt.subplots(figsize=(9, 4.6))
    colors = ["crimson" if m == "global_medfilm" else "tab:grey" for m in c["model_key"]]
    x = np.arange(len(c))
    ax.bar(x, c["macro_domain_dice"], color=colors, alpha=0.85)
    ax.errorbar(x, c["macro_domain_dice"],
                yerr=[c["macro_domain_dice"] - c["macro_domain_dice_ci_low"],
                      c["macro_domain_dice_ci_high"] - c["macro_domain_dice"]],
                fmt="none", ecolor="black", capsize=4, lw=1.2)
    ax.set_xticks(x)
    ax.set_xticklabels([DISPLAY[m] for m in c["model_key"]], rotation=20, ha="right", fontsize=8)
    ax.set_ylabel("macro-domain VAL Dice (95% CI)")
    ax.set_title("Six-model benchmark — macro-domain VAL Dice")
    ax.grid(alpha=0.3, axis="y")
    _save_fig(fig, "comparison", "six_model_macro_dice.png", fig_id="p21_cmp_macro",
              title="Six-model macro-domain VAL Dice with bootstrap CI",
              purpose="Primary benchmark comparison against the five frozen baselines.",
              source=src, models=",".join(MODEL_ORDER), datasets="MACRO_DOMAIN",
              metrics="dice", category="PRIMARY_COMPARISON")

    mat = c.set_index("model_key")[[f"dice_{d}" for d in DATASET_ORDER]]
    mat.index = [DISPLAY[m] for m in mat.index]
    mat.columns = DATASET_ORDER
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    im = ax.imshow(mat.to_numpy(float), cmap="viridis", aspect="auto")
    ax.set_xticks(range(4)); ax.set_xticklabels(DATASET_ORDER, fontsize=9)
    ax.set_yticks(range(len(mat))); ax.set_yticklabels(mat.index, fontsize=8)
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            ax.text(j, i, f"{mat.iat[i, j]:.3f}", ha="center", va="center",
                    fontsize=8, color="white")
    fig.colorbar(im, ax=ax, label="Dice")
    ax.set_title("Per-domain VAL Dice across six models")
    _save_fig(fig, "comparison", "six_model_per_domain_matrix.png",
              fig_id="p21_cmp_domain_matrix",
              title="Per-domain Dice matrix",
              purpose="Show whether the Global MedFiLM advantage/disadvantage is domain-specific.",
              source=src, models=",".join(MODEL_ORDER), datasets="ISIC/BUSI/KVASIR/KUB",
              metrics="dice", category="PRIMARY_COMPARISON")

    p = load_paired()
    fig, ax = plt.subplots(figsize=(8.6, 4.4))
    y = np.arange(len(p))
    ax.errorbar(p["observed_diff"], y,
                xerr=[p["observed_diff"] - p["diff_ci_low"], p["diff_ci_high"] - p["observed_diff"]],
                fmt="o", capsize=4, color="tab:blue")
    ax.axvline(0, color="black", ls="--", lw=1.2)
    ax.set_yticks(y)
    ax.set_yticklabels([f"vs {DISPLAY[m]}" for m in p["model_b"]], fontsize=9)
    ax.set_xlabel("macro-domain Dice difference (Global MedFiLM - baseline), 95% CI")
    ax.set_title("Paired domain-stratified bootstrap vs each frozen baseline")
    for i, (_, r) in enumerate(p.iterrows()):
        tag = "SIGNIFICANT" if r["significant_at_0.05"] else "CI OVERLAPS 0 (not separable)"
        ax.text(r["diff_ci_high"] + 0.0015, i, tag, va="center", fontsize=7,
                color="darkgreen" if r["significant_at_0.05"] else "darkorange")
    ax.grid(alpha=0.3, axis="x")
    _save_fig(fig, "comparison", "paired_bootstrap_forest.png", fig_id="p21_cmp_paired",
              title="Paired bootstrap difference forest plot",
              purpose="Report which differences are statistically separable and which are not.",
              source="reports/tables/phase21_paired_bootstrap_vs_baselines.csv",
              models="global_medfilm vs 5 baselines", datasets="MACRO_DOMAIN",
              metrics="dice", category="PRIMARY_COMPARISON")

    fig, ax = plt.subplots(figsize=(8, 4.4))
    c2 = c.sort_values("params")
    ax.barh([DISPLAY[m] for m in c2["model_key"]], c2["params"] / 1e6, color="tab:cyan", alpha=0.85)
    for i, v in enumerate(c2["params"] / 1e6):
        ax.text(v, i, f" {v:.2f}M", va="center", fontsize=8)
    ax.set_xlabel("trainable parameters (millions)")
    ax.set_title("Model capacity across the six-model panel")
    ax.grid(alpha=0.3, axis="x")
    _save_fig(fig, "comparison", "parameter_comparison.png", fig_id="p21_cmp_params",
              title="Parameter count comparison",
              purpose="Contextualise the Global MedFiLM result by model capacity (measurement only).",
              source=src, models=",".join(MODEL_ORDER), datasets="ALL",
              metrics="params", category="EFFICIENCY")


# --------------------------------------------------------------------------- #
# 3. metric heatmaps + confusion
# --------------------------------------------------------------------------- #
def build_metric_heatmaps() -> None:
    plt = _mpl()
    per_model = {m: load_per_image(m) for m in MODEL_ORDER}
    metrics = ["dice", "iou", "precision", "recall", "specificity", "mcc",
               "balanced_accuracy", "hd95", "assd", "surface_dice"]
    rows = []
    for m, df in per_model.items():
        for d in DATASET_ORDER:
            sub = df[df["dataset"] == d]
            for k in metrics:
                rows.append({"model": DISPLAY[m], "dataset": d, "metric": k,
                             "value": float(sub[k].mean(skipna=True))})
    long = pd.DataFrame(rows)
    for k in metrics:
        mat = long[long["metric"] == k].pivot(index="model", columns="dataset", values="value")
        mat = mat.reindex([DISPLAY[m] for m in MODEL_ORDER])[DATASET_ORDER]
        fig, ax = plt.subplots(figsize=(5.6, 3.6))
        im = ax.imshow(mat.to_numpy(float), cmap="viridis", aspect="auto")
        ax.set_xticks(range(4)); ax.set_xticklabels(DATASET_ORDER, fontsize=9)
        ax.set_yticks(range(len(mat))); ax.set_yticklabels(mat.index, fontsize=8)
        for i in range(mat.shape[0]):
            for j in range(mat.shape[1]):
                v = mat.iat[i, j]
                if not np.isnan(v):
                    ax.text(j, i, f"{v:.3f}", ha="center", va="center", fontsize=7, color="white")
        fig.colorbar(im, ax=ax, label=k)
        ax.set_title(f"{k} — six models x four domains")
        _save_fig(fig, "comparison", f"metric_matrix_{k}.png", fig_id=f"p21_metric_{k}",
                  title=f"{k} matrix",
                  purpose=f"Full {k} breakdown by model and domain.",
                  source="phase21/phase20b per-image metric tables",
                  models=",".join(MODEL_ORDER), datasets="ISIC/BUSI/KVASIR/KUB",
                  metrics=k, category="PRIMARY_COMPARISON")


def build_confusion_figures() -> None:
    plt = _mpl()
    df = pd.read_csv(TABLE_DIR / "phase21_global_medfilm_confusion_matrices.csv")
    scopes = [s for s in df["scope"].tolist()]
    fig, axes = plt.subplots(1, len(scopes), figsize=(3.0 * len(scopes), 3.2))
    if len(scopes) == 1:
        axes = [axes]
    for ax, s in zip(axes, scopes):
        r = df[df["scope"] == s].iloc[0]
        mat = np.array([[r["row_norm_gt_fg_tp"], r["row_norm_gt_fg_fn"]],
                        [r["row_norm_gt_bg_fp"], r["row_norm_gt_bg_tn"]]], dtype=float)
        im = ax.imshow(mat, cmap="Blues", vmin=0, vmax=1)
        ax.set_xticks([0, 1]); ax.set_xticklabels(["pred FG", "pred BG"], fontsize=8)
        ax.set_yticks([0, 1]); ax.set_yticklabels(["GT FG", "GT BG"], fontsize=8)
        for i in range(2):
            for j in range(2):
                ax.text(j, i, f"{mat[i, j]:.3f}", ha="center", va="center", fontsize=8)
        ax.set_title(f"{s}\nn={int(r['total'])}", fontsize=9)
    fig.suptitle("Global MedFiLM — row-normalised pixel confusion matrices", fontsize=10)
    _save_fig(fig, "comparison", "confusion_matrices.png", fig_id="p21_confusion",
              title="Confusion matrices per domain and pooled",
              purpose="Show the FG/BG error structure behind the Dice values.",
              source="reports/tables/phase21_global_medfilm_confusion_matrices.csv",
              models="global_medfilm", datasets="ISIC/BUSI/KVASIR/KUB/POOLED",
              metrics="tp/tn/fp/fn", category="PRIMARY_COMPARISON")


# --------------------------------------------------------------------------- #
# 4. calibration / ranking
# --------------------------------------------------------------------------- #
def build_calibration_figures() -> None:
    plt = _mpl()
    cal = pd.read_csv(TABLE_DIR / "phase21_global_medfilm_calibration_ranking.csv")
    fig, ax = plt.subplots(figsize=(7.4, 4.2))
    x = np.arange(len(cal))
    w = 0.38
    ax.bar(x - w / 2, cal["roc_auc"], w, label="ROC-AUC", color="tab:blue", alpha=0.85)
    ax.bar(x + w / 2, cal["pr_auc_average_precision"], w, label="PR-AUC", color="tab:orange",
           alpha=0.85)
    ax.set_xticks(x); ax.set_xticklabels(cal["dataset"], fontsize=9)
    ax.set_ylim(0, 1.05); ax.set_ylabel("score")
    ax.set_title("Global MedFiLM — pixel-level ranking metrics by domain")
    ax.legend(); ax.grid(alpha=0.3, axis="y")
    _save_fig(fig, "comparison", "ranking_metrics.png", fig_id="p21_ranking",
              title="ROC-AUC and PR-AUC by domain",
              purpose="Report probability-ranking quality independently of the 0.5 threshold.",
              source="reports/tables/phase21_global_medfilm_calibration_ranking.csv",
              models="global_medfilm", datasets="ISIC/BUSI/KVASIR/KUB",
              metrics="roc_auc, pr_auc", category="PRIMARY_COMPARISON")

    fig, ax = plt.subplots(figsize=(7.4, 4.2))
    x = np.arange(len(cal)); w = 0.27
    ax.bar(x - w, cal["brier"], w, label="Brier", color="tab:green", alpha=0.85)
    ax.bar(x, cal["ece"], w, label="ECE", color="tab:red", alpha=0.85)
    ax.bar(x + w, cal["mce"], w, label="MCE", color="tab:purple", alpha=0.85)
    ax.set_xticks(x); ax.set_xticklabels(cal["dataset"], fontsize=9)
    ax.set_ylabel("score (lower is better)")
    ax.set_title("Global MedFiLM — calibration metrics by domain")
    ax.legend(); ax.grid(alpha=0.3, axis="y")
    _save_fig(fig, "comparison", "calibration_metrics.png", fig_id="p21_calibration",
              title="Brier / ECE / MCE by domain",
              purpose="Report probability calibration of the single shared output head.",
              source="reports/tables/phase21_global_medfilm_calibration_ranking.csv",
              models="global_medfilm", datasets="ISIC/BUSI/KVASIR/KUB",
              metrics="brier, ece, mce", category="PRIMARY_COMPARISON")


# --------------------------------------------------------------------------- #
# 5. KUB strata
# --------------------------------------------------------------------------- #
def build_kub_figures() -> None:
    plt = _mpl()
    sub = load_kub_subgroup()
    fig, ax = plt.subplots(figsize=(7.6, 4.2))
    s = sub[sub["scope"] == "KUB_SUBGROUP"]
    x = np.arange(len(s))
    ax.bar(x, s["dice"], color="tab:brown", alpha=0.85)
    for i, v in enumerate(s["dice"]):
        ax.text(i, v, f"{v:.3f}\nn={int(s.iloc[i]['n'])}", ha="center", va="bottom", fontsize=8)
    overall = float(sub[sub["scope"] == "KUB_ALL"]["dice"].iloc[0])
    ax.axhline(overall, color="black", ls="--", lw=1.2, label=f"KUB overall {overall:.3f}")
    ax.set_xticks(x); ax.set_xticklabels(s["subgroup"], fontsize=9)
    ax.set_ylim(0, 1.05); ax.set_ylabel("Dice")
    ax.set_title("Global MedFiLM — KUB performance by stone category (REPORTING ONLY)")
    ax.legend(); ax.grid(alpha=0.3, axis="y")
    _save_fig(fig, "kub", "kub_subgroup_dice.png", fig_id="p21_kub_subgroup",
              title="KUB subgroup Dice",
              purpose="Report KUB performance by stone category without optimising on it.",
              source="reports/tables/phase21_kub_subgroup_analysis.csv",
              models="global_medfilm", datasets="KUB", metrics="dice",
              category="KUB_ANALYSIS")

    ks = load_kub_size()
    fig, ax = plt.subplots(figsize=(8.4, 4.2))
    x = np.arange(len(ks))
    colors = ["crimson" if s_ == "TINY" else "tab:blue" for s_ in ks["stratum"]]
    ax.bar(x, ks["dice"], color=colors, alpha=0.85)
    for i, r in ks.reset_index().iterrows():
        ax.text(i, r["dice"], f"{r['dice']:.3f}\nn={int(r['n'])}", ha="center", va="bottom",
                fontsize=8)
    ax.set_xticks(x); ax.set_xticklabels(ks["stratum"], rotation=15, ha="right", fontsize=8)
    ax.set_ylim(0, 1.05); ax.set_ylabel("Dice")
    ax.set_title("Global MedFiLM — KUB by frozen object-size stratum "
                 "(kub_size_clean_v3_v1, REPORTING ONLY)")
    ax.grid(alpha=0.3, axis="y")
    _save_fig(fig, "kub", "kub_size_strata_dice.png", fig_id="p21_kub_size",
              title="KUB size-stratum Dice",
              purpose="Preserve the TINY stratum evidence for Phase 22 without optimising on it.",
              source="reports/tables/phase21_kub_size_stratification.csv",
              models="global_medfilm", datasets="KUB", metrics="dice",
              category="KUB_ANALYSIS")


# --------------------------------------------------------------------------- #
# 6. conditioning + FiLM
# --------------------------------------------------------------------------- #
def build_conditioning_figures() -> None:
    plt = _mpl()
    diag = load_conditioning()
    fig, ax = plt.subplots(figsize=(8.2, 4.2))
    x = np.arange(len(diag))
    ax.bar(x, diag["mean_abs_delta_dice_wrong_task"], color="tab:olive", alpha=0.85)
    ax.axhline(0.005, color="crimson", ls="--", lw=1.2,
               label="CONDITIONING_EFFECT_WEAK threshold = 0.005")
    for i, r in diag.reset_index().iterrows():
        ax.text(i, r["mean_abs_delta_dice_wrong_task"],
                f"{r['mean_abs_delta_dice_wrong_task']:.4f}\nn={int(r['n'])}",
                ha="center", va="bottom", fontsize=8)
    ax.set_xticks(x); ax.set_xticklabels(diag["scope"], fontsize=8)
    ax.set_ylabel("mean |delta Dice| with an INCORRECT task ID")
    ax.set_title("Task-conditioning diagnostic (frozen 64-case gallery)")
    ax.legend(); ax.grid(alpha=0.3, axis="y")
    _save_fig(fig, "conditioning", "conditioning_diagnostic.png", fig_id="p21_conditioning",
              title="Task-conditioning effect size",
              purpose="Measure whether the FiLM conditioning actually changes predictions.",
              source="reports/tables/phase21_task_conditioning_diagnostic.csv",
              models="global_medfilm", datasets="ISIC/BUSI/KVASIR/KUB",
              metrics="delta_dice", category="CONDITIONING")

    film = load_film_summary()
    for kind in ("gamma", "beta"):
        sub = film[film["parameter"] == kind]
        for stat, label in (("mean_abs", "mean_abs"), ("l2_norm", "l2_norm")):
            mat = sub.pivot(index="task", columns="film_site", values=stat)
            mat = mat.reindex(["ISIC", "BUSI", "KVASIR", "KUB"])[
                ["bridge", "decoder4", "decoder3", "decoder2", "decoder1"]]
            fig, ax = plt.subplots(figsize=(6.4, 3.4))
            im = ax.imshow(mat.to_numpy(float), cmap="magma", aspect="auto")
            ax.set_xticks(range(mat.shape[1])); ax.set_xticklabels(mat.columns, fontsize=9)
            ax.set_yticks(range(mat.shape[0])); ax.set_yticklabels(mat.index, fontsize=9)
            for i in range(mat.shape[0]):
                for j in range(mat.shape[1]):
                    ax.text(j, i, f"{mat.iat[i, j]:.3f}", ha="center", va="center",
                            fontsize=8, color="white")
            fig.colorbar(im, ax=ax, label=stat)
            ax.set_title(f"FiLM {kind} — {label} per task x site")
            _save_fig(fig, "conditioning", f"film_{kind}_{label}.png",
                      fig_id=f"p21_film_{kind}_{label}",
                      title=f"FiLM {kind} {label}",
                      purpose=f"Show what the FiLM {kind} modulation learned per task and site.",
                      source="reports/tables/phase21_film_parameter_summary.csv",
                      models="global_medfilm", datasets="ISIC/BUSI/KVASIR/KUB",
                      metrics=kind, category="CONDITIONING")


# --------------------------------------------------------------------------- #
# 7. galleries
# --------------------------------------------------------------------------- #
def _load_rgb(path, size: int = 256) -> np.ndarray:
    from PIL import Image
    im = Image.open(path).convert("RGB")
    im.thumbnail((size, size))
    return np.asarray(im)


def _npz_lookup() -> dict:
    man = load_pred_manifest()
    return {r["sample_id"]: r["npz_path"] for _, r in man.iterrows()}


def _gallery_meta() -> dict:
    v = load_val_manifest()
    return {r["sample_id"]: r for _, r in v.iterrows()}


def build_gallery_figures() -> None:
    """Six-model panel on the frozen 64 gallery cases (16 per domain)."""
    plt = _mpl()
    gallery = pd.read_csv(TABLE_DIR / "phase21_gallery_selection_64.csv")
    meta = _gallery_meta()
    lookups = {}
    for m in MODEL_ORDER:
        if m == "global_medfilm":
            man = load_pred_manifest()
        else:
            if m == "unetpp":
                man = pd.read_csv(TABLE_DIR / "phase20_prediction_manifest.csv")
            else:
                man = pd.read_csv(TABLE_DIR / f"phase20b_{m}_prediction_manifest.csv")
        man["sample_id"] = man["sample_id"].astype(str)
        lookups[m] = {r["sample_id"]: r["npz_path"] for _, r in man.iterrows()}

    for dsname, grp in gallery.groupby("dataset"):
        ids = grp.sort_values("rank")["sample_id"].astype(str).tolist()[:16]
        n = len(ids)
        fig, axes = plt.subplots(n, len(MODEL_ORDER) + 2, figsize=(2.0 * (len(MODEL_ORDER) + 2), 2.0 * n))
        if n == 1:
            axes = axes.reshape(1, -1)
        for i, sid in enumerate(ids):
            row = meta[sid]
            axes[i, 0].imshow(_load_rgb(row["image_path"]), cmap="gray")
            axes[i, 0].set_ylabel(sid[:8], fontsize=6)
            axes[i, 1].imshow(np.load(ROOT / lookups["global_medfilm"][sid])["gt"], cmap="gray")
            for j, m in enumerate(MODEL_ORDER):
                z = np.load(ROOT / lookups[m][sid])
                axes[i, j + 2].imshow(z["pred"], cmap="gray")
            for j in range(len(MODEL_ORDER) + 2):
                axes[i, j].set_xticks([]); axes[i, j].set_yticks([])
            if i == 0:
                titles = ["image", "GT"] + [DISPLAY[m] for m in MODEL_ORDER]
                for j, t in enumerate(titles):
                    axes[i, j].set_title(t, fontsize=7)
        fig.suptitle(f"Frozen 64-case gallery — {dsname} (six-model panel)", fontsize=10)
        _save_fig(fig, "gallery", f"gallery_six_model_{dsname}.png",
                  fig_id=f"p21_gallery_six_{dsname}",
                  title=f"Six-model gallery — {dsname}",
                  purpose="Qualitative side-by-side of all six models on the frozen gallery.",
                  source="reports/predictions + frozen phase20_gallery_selection.csv",
                  models=",".join(MODEL_ORDER), datasets=dsname,
                  metrics="prediction maps", category="GALLERY_FIXED_64", dpi=100)


def build_detailed_gallery_figures(min_per_domain: int = 16) -> None:
    """Phase-21 detailed gallery: >=16 cases per domain, outcome-selected."""
    plt = _mpl()
    per = load_per_image("global_medfilm")
    meta = _gallery_meta()
    lookups = _npz_lookup()
    for dsname in DATASET_ORDER:
        sub = per[per["dataset"] == dsname].sort_values("dice")
        sel = pd.concat([sub.head(min_per_domain // 2),
                         sub.tail(min_per_domain - min_per_domain // 2)])
        sel = sel.drop_duplicates("sample_id")
        n = len(sel)
        fig, axes = plt.subplots(n, 4, figsize=(8.4, 1.9 * n))
        if n == 1:
            axes = axes.reshape(1, -1)
        for i, (_, r) in enumerate(sel.iterrows()):
            sid = r["sample_id"]
            z = np.load(ROOT / lookups[sid])
            gt, pred, prob = z["gt"].astype(bool), z["pred"].astype(bool), z["prob"].astype(float)
            err = np.zeros((*gt.shape, 3), dtype=np.uint8)
            err[..., 1] = (gt & pred) * 180
            err[..., 0] = (gt & ~pred) * 255
            err[..., 2] = (~gt & pred) * 255
            axes[i, 0].imshow(_load_rgb(meta[sid]["image_path"]), cmap="gray")
            axes[i, 1].imshow(gt, cmap="gray")
            axes[i, 2].imshow(pred, cmap="gray")
            axes[i, 3].imshow(err)
            axes[i, 0].set_ylabel(f"{sid[:8]}\nD={r['dice']:.2f}", fontsize=6)
            for j in range(4):
                axes[i, j].set_xticks([]); axes[i, j].set_yticks([])
            if i == 0:
                for j, t in enumerate(["image", "GT", "prediction",
                                       "error (R=miss, B=false+)"]):
                    axes[i, j].set_title(t, fontsize=7)
        fig.suptitle(f"Phase-21 detailed gallery — {dsname} "
                     f"(ANALYTICAL_OUTCOME_SELECTED)", fontsize=10)
        _save_fig(fig, "gallery", f"detailed_gallery_{dsname}.png",
                  fig_id=f"p21_detailed_gallery_{dsname}",
                  title=f"Detailed gallery — {dsname}",
                  purpose="Outcome-selected cases showing where the reference model succeeds and fails.",
                  source="reports/predictions/phase21_global_medfilm/val",
                  models="global_medfilm", datasets=dsname, metrics="dice, error map",
                  category="GALLERY_DETAILED", dpi=100)


def build_failure_gallery_figures() -> None:
    """Failure-analysis gallery, explicitly labelled ANALYTICAL_OUTCOME_SELECTED."""
    plt = _mpl()
    per = load_per_image("global_medfilm")
    meta = _gallery_meta()
    lookups = _npz_lookup()
    worst = per.sort_values("dice").head(16)
    fig, axes = plt.subplots(4, 4, figsize=(9.6, 9.6))
    for i, (_, r) in enumerate(worst.iterrows()):
        ax = axes[i // 4, i % 4]
        sid = r["sample_id"]
        z = np.load(ROOT / lookups[sid])
        gt, pred = z["gt"].astype(bool), z["pred"].astype(bool)
        err = np.zeros((*gt.shape, 3), dtype=np.uint8)
        err[..., 1] = (gt & pred) * 180
        err[..., 0] = (gt & ~pred) * 255
        err[..., 2] = (~gt & pred) * 255
        ax.imshow(err)
        ax.set_title(f"{r['dataset']} {sid[:6]}\nD={r['dice']:.3f}", fontsize=7)
        ax.set_xticks([]); ax.set_yticks([])
    fig.suptitle("Global MedFiLM — worst-16 failure analysis "
                 "(ANALYTICAL_OUTCOME_SELECTED)", fontsize=11)
    _save_fig(fig, "failure", "failure_worst16.png", fig_id="p21_failure_worst16",
              title="Worst-16 failure gallery",
              purpose="Identify the dominant failure modes of the global reference.",
              source="reports/predictions/phase21_global_medfilm/val",
              models="global_medfilm", datasets="ALL", metrics="dice, error map",
              category="FAILURE_ANALYSIS", dpi=100)

    fig, ax = plt.subplots(figsize=(8.4, 4.2))
    for d in DATASET_ORDER:
        ax.hist(per[per["dataset"] == d]["dice"], bins=24, alpha=0.5, label=d)
    ax.set_xlabel("per-image Dice"); ax.set_ylabel("count")
    ax.set_title("Global MedFiLM — per-image Dice distribution by domain")
    ax.legend(); ax.grid(alpha=0.3)
    _save_fig(fig, "failure", "dice_distribution.png", fig_id="p21_failure_dist",
              title="Per-image Dice distribution",
              purpose="Show dispersion and the low-Dice tail that drives the KUB bottleneck.",
              source="reports/tables/phase21_per_image_val_metrics.csv",
              models="global_medfilm", datasets="ISIC/BUSI/KVASIR/KUB",
              metrics="dice", category="FAILURE_ANALYSIS")


# --------------------------------------------------------------------------- #
# 8. efficiency
# --------------------------------------------------------------------------- #
def build_efficiency_figures() -> None:
    plt = _mpl()
    eff = pd.read_csv(TABLE_DIR / "phase21_efficiency_accounting.csv")
    e = dict(zip(eff["metric"], eff["value"]))

    fig, ax = plt.subplots(figsize=(8, 3.6))
    labels = [f"batch {b}" for b in (1, 8)]
    vals = [float(e.get("gpu_latency_median_batch1", np.nan)),
            float(e.get("gpu_latency_median_batch8", np.nan))]
    ax.bar(labels, vals, color="tab:blue", alpha=0.85)
    for i, v in enumerate(vals):
        if not np.isnan(v):
            ax.text(i, v, f"{v:.1f} ms", ha="center", va="bottom", fontsize=9)
    ax.set_ylabel("median forward latency (ms)")
    ax.set_title("GPU forward latency at 512x512 (measurement only)")
    ax.grid(alpha=0.3, axis="y")
    _save_fig(fig, "efficiency", "gpu_latency.png", fig_id="p21_eff_gpu_latency",
              title="GPU forward latency",
              purpose="Report inference cost of the reference model (no optimisation).",
              source="reports/tables/phase21_efficiency_accounting.csv",
              models="global_medfilm", datasets="ALL", metrics="latency_ms",
              category="EFFICIENCY")

    fig, ax = plt.subplots(figsize=(8, 3.6))
    labels = [f"batch {b}" for b in (1, 4)]
    vals = [float(e.get("cpu_latency_median_batch1", np.nan)),
            float(e.get("cpu_latency_median_batch4", np.nan))]
    ax.bar(labels, vals, color="tab:orange", alpha=0.85)
    for i, v in enumerate(vals):
        if not np.isnan(v):
            ax.text(i, v, f"{v:.0f} ms", ha="center", va="bottom", fontsize=9)
    ax.set_ylabel("median forward latency (ms)")
    ax.set_title("CPU forward latency at 512x512 (synthetic input, measurement only)")
    ax.grid(alpha=0.3, axis="y")
    _save_fig(fig, "efficiency", "cpu_latency.png", fig_id="p21_eff_cpu_latency",
              title="CPU forward latency",
              purpose="Report CPU inference cost on synthetic input (never TEST).",
              source="reports/tables/phase21_efficiency_accounting.csv",
              models="global_medfilm", datasets="SYNTHETIC", metrics="latency_ms",
              category="EFFICIENCY")

    # Six-model compute (analytical MACs) — only once the table exists.
    comp_path = TABLE_DIR / "phase21_six_model_compute.csv"
    if comp_path.exists():
        comp = pd.read_csv(comp_path).sort_values("gmacs")
        fig, ax = plt.subplots(figsize=(8.4, 4.2))
        colors = ["crimson" if m == "global_medfilm" else "tab:blue" for m in comp["model_key"]]
        x = np.arange(len(comp))
        ax.bar(x, comp["gmacs"], color=colors, alpha=0.85)
        for i, r in comp.reset_index().iterrows():
            ax.text(i, r["gmacs"], f"{r['gmacs']:.2f}", ha="center", va="bottom", fontsize=8)
        ax.set_xticks(x)
        ax.set_xticklabels([DISPLAY.get(m, m) for m in comp["model_key"]],
                           rotation=20, ha="right", fontsize=8)
        ax.set_ylabel("G MACs at 1x3x512x512")
        ax.set_title("Six-model compute — analytical Conv2d/Linear MACs (lower bound)")
        ax.grid(alpha=0.3, axis="y")
        _save_fig(fig, "efficiency", "six_model_compute.png", fig_id="p21_eff_six_model_compute",
                  title="Six-model compute comparison",
                  purpose="Contextualise the Global MedFiLM result by inference cost, not just "
                          "parameter count (measurement only).",
                  source="reports/tables/phase21_six_model_compute.csv",
                  models=",".join(MODEL_ORDER), datasets="ALL", metrics="macs",
                  category="EFFICIENCY")


# --------------------------------------------------------------------------- #
def build_all(progress=print) -> dict:
    reset_registry()
    steps = [
        ("training", build_training_figures),
        ("primary", build_primary_figures),
        ("metric_heatmaps", build_metric_heatmaps),
        ("confusion", build_confusion_figures),
        ("calibration", build_calibration_figures),
        ("kub", build_kub_figures),
        ("conditioning", build_conditioning_figures),
        ("gallery", build_gallery_figures),
        ("detailed_gallery", build_detailed_gallery_figures),
        ("failure", build_failure_gallery_figures),
        ("efficiency", build_efficiency_figures),
    ]
    for name, fn in steps:
        progress(f"[figures] {name} ...")
        fn()
        progress(f"[figures] {name} done ({len(_REG)} figures so far)")
    inv = figure_inventory()
    return {"n_figures": int(len(inv)), "inventory": inv}


def write_inventories() -> dict:
    inv = figure_inventory()
    FIG_ROOT.mkdir(parents=True, exist_ok=True)
    csv_path = FIG_ROOT / "phase21_figure_inventory.csv"
    json_path = FIG_ROOT / "phase21_figure_inventory.json"
    inv.to_csv(csv_path, index=False)
    payload = {
        "artifact": "phase21_figure_inventory",
        "phase": 21,
        "n_figures": int(len(inv)),
        "n_embedded_in_notebook": int(inv["embedded_in_notebook"].sum()) if len(inv) else 0,
        "groups": {k: int(v) for k, v in inv.groupby("group").size().items()} if len(inv) else {},
        "figure_root": rel(FIG_ROOT),
        "figures": inv.to_dict("records"),
        "test_reads": 0,
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return {"csv": rel(csv_path), "json": rel(json_path), "n_figures": int(len(inv)),
            "n_embedded": payload["n_embedded_in_notebook"]}
