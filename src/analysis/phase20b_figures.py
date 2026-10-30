"""Phase-20B reviewer-package figures + inventories.

Every figure is built from persisted artifacts only (histories, metric tables,
prediction NPZs, manifest image paths). No inference, no TEST, no checkpoint load.

Figures are written under ``reports/figures/phase20b_five_model_baselines/<group>/``
and simultaneously registered so the notebook can embed the exact same bytes and the
figure inventory / visualization-coverage audits can be generated.

matplotlib PNG output is byte-deterministic (verified), so rebuilding reproduces the
same files and the notebook stays SHA-stable.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.analysis import phase20b_reviewer as R

# --------------------------------------------------------------------------- #
# Registry
# --------------------------------------------------------------------------- #
_REG: list[dict] = []


def _mpl():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    return plt


def _save_fig(fig, group: str, name: str, *, fig_id: str, title: str, purpose: str,
              source: str, models: str, datasets: str, metrics: str,
              embedded: bool = True, category: str = "", dpi: int = 110) -> Path:
    plt = _mpl()
    d = R.FIG_ROOT / group
    d.mkdir(parents=True, exist_ok=True)
    p = d / name
    fig.tight_layout()
    fig.savefig(p, dpi=dpi)
    plt.close(fig)
    _REG.append({
        "figure_id": fig_id, "title": title, "scientific_purpose": purpose,
        "source_artifacts": source, "models": models, "datasets": datasets,
        "metrics": metrics, "saved_path": R.rel(p), "group": group,
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


def _heatmap(ax, mat: pd.DataFrame, title: str, *, cmap: str = "viridis", fmt: str = "{:.3f}",
             vmin=None, vmax=None, cbar_label: str = "", fontsize: int = 8):
    plt = _mpl()
    data = mat.to_numpy(dtype=float)
    im = ax.imshow(data, cmap=cmap, vmin=vmin, vmax=vmax, aspect="auto")
    ax.set_xticks(range(mat.shape[1])); ax.set_xticklabels(mat.columns, rotation=0, fontsize=fontsize)
    ax.set_yticks(range(mat.shape[0])); ax.set_yticklabels(mat.index, fontsize=fontsize)
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            v = data[i, j]
            if np.isnan(v):
                ax.text(j, i, "NA", ha="center", va="center", fontsize=fontsize - 1, color="grey")
                continue
            norm = (v - np.nanmin(data)) / (np.nanmax(data) - np.nanmin(data) + 1e-12)
            ax.text(j, i, fmt.format(v), ha="center", va="center", fontsize=fontsize - 1,
                    color="white" if norm < 0.45 else "black")
    ax.set_title(title, fontsize=fontsize + 2)
    cb = ax.figure.colorbar(im, ax=ax, fraction=0.025, pad=0.02)
    if cbar_label:
        cb.set_label(cbar_label, fontsize=fontsize)
    return im


# --------------------------------------------------------------------------- #
# 8. Training figures
# --------------------------------------------------------------------------- #
def build_training_figures() -> None:
    plt = _mpl()
    histories = {m: R.load_history(m) for m in R.MODEL_ORDER}
    closures = {m: R.load_closure(m) for m in R.MODEL_ORDER}

    for m in R.MODEL_ORDER:
        h, c = histories[m], closures[m]
        ep = h["epoch"].values
        fig, axes = plt.subplots(2, 4, figsize=(19, 8.6))
        ax = axes[0, 0]
        ax.plot(ep, h["train_loss"], lw=1.2, label="train loss")
        ax.plot(ep, h["val_loss"], lw=1.2, label="val loss")
        ax.axvline(c["best_epoch"], color="green", ls="--", lw=1.0, label=f"best ep {c['best_epoch']}")
        ax.set_title("1-2. train / val loss"); ax.set_xlabel("epoch"); ax.set_ylabel("BCE+Dice loss")
        ax.legend(fontsize=7); ax.grid(alpha=0.25)

        ax = axes[0, 1]
        ax.plot(ep, h["macro_domain_dice"], lw=1.4, color="#6a1b9a")
        ax.axhline(c["best_macro_domain_dice"], color="green", ls="--", lw=1.0,
                   label=f"best {c['best_macro_domain_dice']:.4f}")
        ax.axvline(c["best_epoch"], color="green", ls=":", lw=1.0)
        ax.set_title("3. macro-domain Dice"); ax.set_xlabel("epoch"); ax.set_ylabel("Dice")
        ax.legend(fontsize=7); ax.grid(alpha=0.25)

        ax = axes[0, 2]
        for d in R.DATASET_ORDER:
            ax.plot(ep, h[f"val_dice_{d}"], lw=1.1, color=R.DOMAIN_COLORS[d], label=d)
        ax.axvline(c["best_epoch"], color="green", ls=":", lw=1.0)
        ax.set_title("4-7. per-domain Dice"); ax.set_xlabel("epoch"); ax.set_ylabel("Dice")
        ax.legend(fontsize=7, ncol=2); ax.grid(alpha=0.25)

        ax = axes[0, 3]
        for d in R.DATASET_ORDER:
            ax.plot(ep, h[f"val_iou_{d}"], lw=1.1, color=R.DOMAIN_COLORS[d], label=d)
        ax.set_title("per-domain IoU"); ax.set_xlabel("epoch"); ax.set_ylabel("IoU")
        ax.legend(fontsize=7, ncol=2); ax.grid(alpha=0.25)

        ax = axes[1, 0]
        ax.plot(ep, h["learning_rate"], lw=1.2, color="#b8860b")
        ax.set_title("8. learning rate"); ax.set_xlabel("epoch"); ax.set_ylabel("LR")
        ax.grid(alpha=0.25)

        ax = axes[1, 1]
        ax.plot(ep, h["bad_epochs"], lw=1.2, color="#c0392b")
        ax.axhline(c["early_stopping_patience"], color="black", ls=":", lw=1.0,
                   label=f"patience {c['early_stopping_patience']}")
        ax.set_title("9. early-stop counter"); ax.set_xlabel("epoch"); ax.set_ylabel("bad epochs")
        ax.legend(fontsize=7); ax.grid(alpha=0.25)

        ax = axes[1, 2]
        ax.bar(ep, h["epoch_seconds"], color="#4682b4")
        ax.axhline(h["epoch_seconds"].mean(), color="black", ls="--", lw=1.0,
                   label=f"mean {h['epoch_seconds'].mean():.0f}s")
        ax.set_title("10. epoch duration"); ax.set_xlabel("epoch"); ax.set_ylabel("seconds")
        ax.legend(fontsize=7); ax.grid(alpha=0.25, axis="y")

        ax = axes[1, 3]
        ax.step(ep, h["macro_domain_dice"].cummax(), where="post", lw=1.6, color="#00695c",
                label="best so far")
        imp = h[h["is_new_best"]]
        ax.scatter(imp["epoch"], imp["macro_domain_dice"], s=18, color="#e65100", zorder=3,
                   label=f"improvements (n={len(imp)})")
        ax.set_title("11-12. best progression + checkpoint marker")
        ax.set_xlabel("epoch"); ax.set_ylabel("macro Dice"); ax.legend(fontsize=7); ax.grid(alpha=0.25)

        fig.suptitle(f"{R.DISPLAY[m]} ({R.PHASE[m]}) — training overview  ·  "
                     f"{c['model_params']:,} params  ·  best epoch {c['best_epoch']}  ·  "
                     f"macro Dice {c['best_macro_domain_dice']:.6f}  ·  {c['stop_reason']}", fontsize=12)
        _save_fig(fig, "training", f"{m}_training_overview.png",
                  fig_id=f"train_overview_{m}", title=f"{R.DISPLAY[m]} training overview",
                  purpose="All required training curves for one model (losses, macro/per-domain Dice & IoU, LR, early-stop, epoch time, best progression).",
                  source="experiments/<exp>/history.csv, closure.json",
                  models=R.DISPLAY[m], datasets=",".join(R.DATASET_ORDER),
                  metrics="train_loss,val_loss,macro_dice,dice,iou,learning_rate,bad_epochs,epoch_seconds",
                  category="training")

    # cross-model overlays
    overlays = [
        ("macro_domain_dice", "Macro-domain Dice", "macro Dice", "overlay_macro_dice.png"),
        ("val_loss", "Validation loss", "BCE+Dice loss", "overlay_val_loss.png"),
        ("val_dice_KUB", "KUB Dice", "Dice", "overlay_kub_dice.png"),
        ("epoch_seconds", "Epoch duration", "seconds", "overlay_epoch_seconds.png"),
    ]
    for col, title, ylab, fname in overlays:
        fig, ax = plt.subplots(figsize=(10, 4.8))
        for m in R.MODEL_ORDER:
            h = histories[m]
            ax.plot(h["epoch"], h[col], lw=1.3, color=R.COLORS[m], label=R.DISPLAY[m])
        ax.set_title(f"Cross-model overlay — {title}"); ax.set_xlabel("epoch"); ax.set_ylabel(ylab)
        ax.legend(fontsize=8); ax.grid(alpha=0.25)
        _save_fig(fig, "training", fname, fig_id=f"train_{col}_overlay",
                  title=f"Cross-model overlay — {title}",
                  purpose="Compare the five models' training trajectories on one axis.",
                  source="experiments/<exp>/history.csv", models="ALL",
                  datasets=",".join(R.DATASET_ORDER), metrics=col, category="training")


# --------------------------------------------------------------------------- #
# 9-10. Primary comparison + metric heatmaps
# --------------------------------------------------------------------------- #
def build_primary_figures() -> None:
    plt = _mpl()
    head = R.headline_table()
    labels = head["model"].tolist()
    vals = head["macro_dice"].to_numpy()
    lo = head["dice_ci_low"].to_numpy()
    hi = head["dice_ci_high"].to_numpy()
    colors = [R.COLORS[m] for m in head["model_key"]]

    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(labels))
    ax.bar(x, vals, yerr=[vals - lo, hi - vals], color=colors, alpha=0.9,
           error_kw={"ecolor": "#333", "capsize": 4, "lw": 1})
    for i, v in enumerate(vals):
        ax.text(i, v + 0.004, f"{v:.6f}", ha="center", fontsize=8)
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=12, fontsize=9)
    ax.set_ylabel("macro-domain mean VAL Dice (95% CI)")
    ax.set_title("Primary result — five-model macro-domain VAL Dice (n=808)\n"
                 "top-two difference NOT statistically significant (p=0.282)")
    ax.set_ylim(min(lo) - 0.02, max(hi) + 0.02); ax.grid(alpha=0.25, axis="y")
    _save_fig(fig, "primary_comparison", "macro_dice_ci.png", fig_id="primary_macro_dice_ci",
              title="Macro-domain Dice with 95% CI",
              purpose="Primary five-model comparison with uncertainty.",
              source="phase20b_five_model_comparison_final.csv", models="ALL",
              datasets="MACRO_DOMAIN", metrics="macro_domain_dice", category="primary")

    fig, ax = plt.subplots(figsize=(10, 4.6))
    ax.bar(x, head["macro_iou"], color=colors, alpha=0.9)
    for i, v in enumerate(head["macro_iou"]):
        ax.text(i, v + 0.002, f"{v:.6f}", ha="center", fontsize=8)
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=12, fontsize=9)
    ax.set_ylabel("macro-domain mean VAL IoU")
    ax.set_title("Macro-domain mean VAL IoU (five models)"); ax.grid(alpha=0.25, axis="y")
    _save_fig(fig, "primary_comparison", "macro_iou_bar.png", fig_id="primary_macro_iou_bar",
              title="Macro-domain IoU bar chart", purpose="Primary IoU comparison.",
              source="phase20b_five_model_comparison_final.csv", models="ALL",
              datasets="MACRO_DOMAIN", metrics="macro_domain_iou", category="primary")

    # per-domain grouped bars
    fig, ax = plt.subplots(figsize=(11, 5))
    w = 0.16
    xs = np.arange(len(R.DATASET_ORDER))
    for i, m in enumerate(R.MODEL_ORDER):
        row = R.per_domain_table("dice")
        r = row[row["model_key"] == m].iloc[0]
        ax.bar(xs + (i - 2) * w, [r[d] for d in R.DATASET_ORDER], w, label=R.DISPLAY[m],
               color=R.COLORS[m])
    ax.set_xticks(xs); ax.set_xticklabels(R.DATASET_ORDER)
    ax.set_ylabel("per-image macro VAL Dice"); ax.set_ylim(0.55, 0.95)
    ax.set_title("Per-domain VAL Dice by model"); ax.legend(fontsize=8, ncol=5); ax.grid(alpha=0.25, axis="y")
    _save_fig(fig, "primary_comparison", "per_domain_dice_grouped.png",
              fig_id="primary_per_domain_dice_grouped", title="Per-domain Dice grouped bars",
              purpose="Domain-specific comparison of the five models.",
              source="phase20b_<model>_domain_performance.csv", models="ALL",
              datasets=",".join(R.DATASET_ORDER), metrics="dice", category="primary")

    for metric, name, cbar in [("dice", "model_domain_dice_heatmap.png", "Dice"),
                               ("iou", "model_domain_iou_heatmap.png", "IoU")]:
        mat = R.domain_metric_matrix(metric).set_index("model")[R.DATASET_ORDER]
        fig, ax = plt.subplots(figsize=(7.5, 4.6))
        _heatmap(ax, mat, f"model × domain {cbar}", cmap="viridis", fmt="{:.4f}",
                 vmin=float(np.nanmin(mat.to_numpy())), vmax=float(np.nanmax(mat.to_numpy())),
                 cbar_label=cbar, fontsize=10)
        _save_fig(fig, "primary_comparison", name, fig_id=f"primary_{metric}_heatmap",
                  title=f"model × domain {cbar} heatmap",
                  purpose=f"Compact {cbar} comparison across all model/domain cells.",
                  source="phase20b_<model>_domain_performance.csv", models="ALL",
                  datasets=",".join(R.DATASET_ORDER), metrics=metric, category="primary")


def build_metric_heatmaps() -> None:
    plt = _mpl()
    labels = {
        "dice": "Dice", "iou": "IoU", "precision": "Precision", "recall": "Recall",
        "specificity": "Specificity", "balanced_accuracy": "Balanced accuracy", "mcc": "MCC",
        "hd95": "HD95 (px)", "assd": "ASSD (px)", "surface_dice": "Surface Dice",
        "roc_auc": "ROC-AUC", "pr_auc": "PR-AUC", "brier": "Brier", "ece": "ECE", "mce": "MCE",
    }
    for metric, lab in labels.items():
        mat = R.domain_metric_matrix(metric).set_index("model")[R.DATASET_ORDER]
        if mat.isna().all().all():
            continue
        higher = metric in R.HIGHER_IS_BETTER
        cmap = "viridis" if higher else "viridis_r"
        fig, ax = plt.subplots(figsize=(7.6, 4.6))
        _heatmap(ax, mat, f"model × domain — {lab}" + ("" if higher else "  (lower is better)"),
                 cmap=cmap, fmt="{:.4f}", cbar_label=lab, fontsize=10)
        _save_fig(fig, "metric_heatmaps", f"heatmap_{metric}.png", fig_id=f"metric_heat_{metric}",
                  title=f"model × domain {lab} heatmap",
                  purpose=f"Visual counterpart of the {lab} evaluation matrix.",
                  source="phase20b_<model>_domain_performance.csv", models="ALL",
                  datasets=",".join(R.DATASET_ORDER), metrics=metric, category="metric_heatmap")

    # comprehensive metric heatmap (metrics x (model,domain)), min-max normalized per metric
    comp = R.comprehensive_metric_matrix()
    cols, data = [], []
    for _, r in comp.iterrows():
        cols.append(f"{R.SHORT[r['model_key']]}\n{r['dataset']}")
        data.append([r[m] for m in R.ADVANCED_METRICS])
    raw = pd.DataFrame(data, index=cols, columns=[labels[m] for m in R.ADVANCED_METRICS]).T
    norm = raw.copy()
    for i in range(len(norm)):
        row = norm.iloc[i]
        lo, hi = np.nanmin(row), np.nanmax(row)
        norm.iloc[i] = (row - lo) / (hi - lo + 1e-12)
    fig, ax = plt.subplots(figsize=(26, 9))
    im = ax.imshow(norm.to_numpy(dtype=float), cmap="RdYlGn", aspect="auto", vmin=0, vmax=1)
    ax.set_xticks(range(raw.shape[1])); ax.set_xticklabels(raw.columns, fontsize=7, rotation=90)
    ax.set_yticks(range(raw.shape[0])); ax.set_yticklabels(raw.index, fontsize=9)
    for i in range(raw.shape[0]):
        for j in range(raw.shape[1]):
            v = raw.iloc[i, j]
            ax.text(j, i, "NA" if np.isnan(v) else (f"{v:.2f}" if abs(v) < 100 else f"{v:.0f}"),
                    ha="center", va="center", fontsize=6)
    ax.set_title("Comprehensive metric heatmap — 15 metrics × 20 (model, domain) cells\n"
                 "colour = per-metric min-max normalisation (raw values annotated)", fontsize=13)
    fig.colorbar(im, ax=ax, fraction=0.012, pad=0.01, label="normalised (per metric)")
    _save_fig(fig, "metric_heatmaps", "comprehensive_metric_heatmap.png",
              fig_id="metric_heat_comprehensive", title="Comprehensive metric heatmap",
              purpose="One figure showing all 15 persisted metrics across all model/domain cells.",
              source="phase20b_<model>_domain_performance.csv", models="ALL",
              datasets=",".join(R.DATASET_ORDER), metrics=",".join(R.ADVANCED_METRICS),
              category="metric_heatmap")


# --------------------------------------------------------------------------- #
# 11. Confusion matrices
# --------------------------------------------------------------------------- #
def build_confusion_figures() -> None:
    plt = _mpl()
    for m in R.MODEL_ORDER:
        c = R.load_confusion(m)
        scopes = R.DATASET_ORDER + ["POOLED_DESCRIPTIVE"]
        fig, axes = plt.subplots(2, len(scopes), figsize=(4.1 * len(scopes), 8.4))
        for j, scope in enumerate(scopes):
            r = c[c["scope"] == scope].iloc[0]
            raw = np.array([[r["tp"], r["fn"]], [r["fp"], r["tn"]]], dtype=float)
            rn = np.array([[r["row_norm_gt_fg_tp"], r["row_norm_gt_fg_fn"]],
                           [r["row_norm_gt_bg_fp"], r["row_norm_gt_bg_tn"]]], dtype=float)
            for i, (mat, cmap, vmax, fmt) in enumerate(
                    [(raw, "Blues", raw.max(), "{:.3g}"), (rn, "Blues", 1.0, "{:.3f}")]):
                ax = axes[i, j]
                im = ax.imshow(mat, cmap=cmap, vmin=0, vmax=vmax)
                for a in range(2):
                    for b in range(2):
                        ax.text(b, a, fmt.format(mat[a, b]), ha="center", va="center",
                                fontsize=9, color="white" if mat[a, b] > 0.55 * vmax else "black")
                ax.set_xticks([0, 1]); ax.set_xticklabels(["pred FG", "pred BG"], fontsize=8)
                ax.set_yticks([0, 1]); ax.set_yticklabels(["GT FG", "GT BG"], fontsize=8)
                ax.set_title(("raw" if i == 0 else "row-normalised") + f" — {scope}", fontsize=9)
        fig.suptitle(f"{R.DISPLAY[m]} — pixel confusion matrices "
                     f"(rows = GT, cols = prediction; bottom row is row-normalised)", fontsize=12)
        _save_fig(fig, "confusion", f"confusion_{m}.png", fig_id=f"confusion_{m}",
                  title=f"{R.DISPLAY[m]} confusion matrices (raw + row-normalised)",
                  purpose="Pixel-level confusion for each domain plus the pooled descriptive cell.",
                  source="phase20b_<model>_confusion_matrices.csv", models=R.DISPLAY[m],
                  datasets=",".join(R.DATASET_ORDER) + ",POOLED", metrics="tp,tn,fp,fn",
                  category="confusion")

    # aggregate confusion-derived metric heatmap + FPR/FNR heatmap
    ctab = R.confusion_table()
    rows = []
    for m in R.MODEL_ORDER:
        sub = ctab[(ctab["model_key"] == m) & (ctab["scope"].isin(R.DATASET_ORDER))]
        for _, r in sub.iterrows():
            tp, tn, fp, fn = r["tp"], r["tn"], r["fp"], r["fn"]
            rows.append({"model_key": m, "model": R.DISPLAY[m], "dataset": r["scope"],
                         "sensitivity": tp / max(1, tp + fn), "specificity": tn / max(1, tn + fp),
                         "fpr": fp / max(1, fp + tn), "fnr": fn / max(1, fn + tp),
                         "ppv": tp / max(1, tp + fp), "npv": tn / max(1, tn + fn)})
    der = pd.DataFrame(rows)

    for metric, name, lab in [("sensitivity", "confusion_metric_heatmap.png", "Sensitivity"),
                              ("fpr", "fpr_heatmap.png", "False-positive rate"),
                              ("fnr", "fnr_heatmap.png", "False-negative rate")]:
        mat = der.pivot(index="model", columns="dataset", values=metric).reindex(
            [R.DISPLAY[m] for m in R.MODEL_ORDER])[R.DATASET_ORDER]
        fig, ax = plt.subplots(figsize=(7.6, 4.6))
        _heatmap(ax, mat, f"model × domain — {lab}", cmap="viridis_r" if metric in ("fpr", "fnr") else "viridis",
                 fmt="{:.4f}", cbar_label=lab, fontsize=10)
        _save_fig(fig, "confusion", name, fig_id=f"confusion_{metric}",
                  title=f"model × domain {lab}",
                  purpose=f"Confusion-derived {lab} across models and domains.",
                  source="phase20b_<model>_confusion_matrices.csv", models="ALL",
                  datasets=",".join(R.DATASET_ORDER), metrics=metric, category="confusion")


# --------------------------------------------------------------------------- #
# 12-13. ROC / PR + calibration
# --------------------------------------------------------------------------- #
def build_roc_pr_figures(cache: dict) -> None:
    plt = _mpl()
    curves = cache["curves"]
    scal = cache["scalars"]

    for kind, fname, ylab, fig_id in [
            ("roc", "roc_per_domain.png", "true-positive rate", "roc_per_domain"),
            ("pr", "pr_per_domain.png", "precision", "pr_per_domain")]:
        fig, axes = plt.subplots(1, 4, figsize=(20, 5))
        for ax, d in zip(axes, R.DATASET_ORDER):
            if kind == "roc":
                ax.plot([0, 1], [0, 1], "k--", lw=1.0, label="chance")
                for m in R.MODEL_ORDER:
                    cv = curves[(m, d)]
                    auc = scal[(scal["model_key"] == m) & (scal["dataset"] == d)]["roc_auc"].iloc[0]
                    ax.plot(cv["fpr"], cv["tpr"], lw=1.2, color=R.COLORS[m],
                            label=f"{R.SHORT[m]} ({auc:.3f})")
                ax.set_xlabel("false-positive rate"); ax.set_ylabel(ylab)
            else:
                prev = scal[(scal["model_key"] == R.MODEL_ORDER[0]) & (scal["dataset"] == d)]["prevalence"].iloc[0]
                ax.axhline(prev, color="k", ls="--", lw=1.0, label=f"prevalence {prev:.3f}")
                for m in R.MODEL_ORDER:
                    cv = curves[(m, d)]
                    ap = scal[(scal["model_key"] == m) & (scal["dataset"] == d)]["pr_auc"].iloc[0]
                    ax.plot(cv["recall"], cv["precision"], lw=1.2, color=R.COLORS[m],
                            label=f"{R.SHORT[m]} (AP {ap:.3f})")
                ax.set_xlabel("recall"); ax.set_ylabel(ylab)
            ax.set_title(d); ax.legend(fontsize=7); ax.grid(alpha=0.25)
        fig.suptitle(("ROC curves per domain — all five models" if kind == "roc"
                      else "Precision–Recall curves per domain — all five models\n"
                           "(PR-AUC is more informative than ROC-AUC under sparse foreground)"), fontsize=13)
        _save_fig(fig, "roc_pr", fname, fig_id=fig_id,
                  title=("ROC per domain" if kind == "roc" else "PR per domain"),
                  purpose=("Ranking quality per domain." if kind == "roc"
                           else "Ranking quality under class imbalance (more informative for sparse foreground)."),
                  source="persisted prediction NPZ (prob) + gt", models="ALL",
                  datasets=",".join(R.DATASET_ORDER),
                  metrics=("roc_auc" if kind == "roc" else "pr_auc"), category="roc_pr")

    for metric, fname, lab in [("roc_auc", "roc_auc_heatmap.png", "ROC-AUC"),
                               ("pr_auc", "pr_auc_heatmap.png", "PR-AUC (average precision)")]:
        mat = scal.pivot(index="model", columns="dataset", values=metric).reindex(
            [R.DISPLAY[m] for m in R.MODEL_ORDER])[R.DATASET_ORDER]
        fig, ax = plt.subplots(figsize=(7.6, 4.6))
        _heatmap(ax, mat, f"model × domain — {lab}", cmap="viridis", fmt="{:.4f}",
                 cbar_label=lab, fontsize=10)
        _save_fig(fig, "roc_pr", fname, fig_id=f"roc_pr_{metric}",
                  title=f"model × domain {lab}", purpose=f"{lab} across models and domains.",
                  source="persisted prediction NPZ (prob) + gt", models="ALL",
                  datasets=",".join(R.DATASET_ORDER), metrics=metric, category="roc_pr")


def build_calibration_figures(cache: dict) -> None:
    plt = _mpl()
    rel = cache["reliability"]
    scal = cache["scalars"]

    fig, axes = plt.subplots(1, 4, figsize=(20, 5))
    for ax, d in zip(axes, R.DATASET_ORDER):
        ax.plot([0, 1], [0, 1], "k--", lw=1.0, label="perfect")
        for m in R.MODEL_ORDER:
            rb = rel[(m, d)]
            conf = np.array(rb["bin_confidence"], dtype=float)
            acc = np.array(rb["bin_accuracy"], dtype=float)
            ok = ~np.isnan(conf) & ~np.isnan(acc)
            ece = scal[(scal["model_key"] == m) & (scal["dataset"] == d)]["ece"].iloc[0]
            ax.plot(conf[ok], acc[ok], marker="o", ms=3, lw=1.1, color=R.COLORS[m],
                    label=f"{R.SHORT[m]} (ECE {ece:.3f})")
        ax.set_xlabel("mean predicted probability"); ax.set_ylabel("empirical foreground rate")
        ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.set_title(d); ax.legend(fontsize=7); ax.grid(alpha=0.25)
    fig.suptitle(f"Reliability diagrams per domain — deterministic pixel subsample "
                 f"(stride {R.CALIBRATION_STRIDE}, {R.CALIBRATION_BINS} bins)", fontsize=13)
    _save_fig(fig, "calibration", "reliability_per_domain.png", fig_id="calib_reliability",
              title="Reliability diagrams per domain",
              purpose="Calibration quality of the persisted probability maps.",
              source="persisted prediction NPZ (prob) + gt", models="ALL",
              datasets=",".join(R.DATASET_ORDER), metrics="ece,reliability", category="calibration")

    for metric, fname, lab in [("ece", "ece_heatmap.png", "Expected calibration error"),
                               ("brier", "brier_heatmap.png", "Brier score"),
                               ("mce", "mce_heatmap.png", "Maximum calibration error")]:
        mat = scal.pivot(index="model", columns="dataset", values=metric).reindex(
            [R.DISPLAY[m] for m in R.MODEL_ORDER])[R.DATASET_ORDER]
        fig, ax = plt.subplots(figsize=(7.6, 4.6))
        _heatmap(ax, mat, f"model × domain — {lab} (lower is better)", cmap="viridis_r",
                 fmt="{:.4f}", cbar_label=lab, fontsize=10)
        _save_fig(fig, "calibration", fname, fig_id=f"calib_{metric}",
                  title=f"model × domain {lab}", purpose=f"{lab} across models and domains.",
                  source="persisted prediction NPZ (prob) + gt", models="ALL",
                  datasets=",".join(R.DATASET_ORDER), metrics=metric, category="calibration")


# --------------------------------------------------------------------------- #
# 14. Boundary metrics
# --------------------------------------------------------------------------- #
def build_boundary_figures() -> None:
    plt = _mpl()
    for metric, fname, lab in [("hd95", "hd95_heatmap.png", "HD95 (pixels)"),
                               ("assd", "assd_heatmap.png", "ASSD (pixels)"),
                               ("surface_dice", "surface_dice_heatmap.png", "Surface Dice")]:
        mat = R.domain_metric_matrix(metric).set_index("model")[R.DATASET_ORDER]
        higher = metric == "surface_dice"
        fig, ax = plt.subplots(figsize=(7.6, 4.6))
        _heatmap(ax, mat, f"model × domain — {lab}" + ("" if higher else "  (lower is better)"),
                 cmap="viridis" if higher else "viridis_r", fmt="{:.4f}", cbar_label=lab, fontsize=10)
        _save_fig(fig, "boundary", fname, fig_id=f"boundary_{metric}",
                  title=f"model × domain {lab}", purpose=f"Boundary-quality {lab} across models/domains.",
                  source="phase20b_<model>_domain_performance.csv", models="ALL",
                  datasets=",".join(R.DATASET_ORDER), metrics=metric, category="boundary")

    fig, axes = plt.subplots(1, 3, figsize=(20, 5))
    for ax, metric, lab in zip(axes, ["hd95", "assd", "surface_dice"],
                               ["HD95 (px)", "ASSD (px)", "Surface Dice"]):
        w = 0.16
        xs = np.arange(len(R.DATASET_ORDER))
        for i, m in enumerate(R.MODEL_ORDER):
            row = R.domain_metric_matrix(metric)
            r = row[row["model_key"] == m].iloc[0]
            ax.bar(xs + (i - 2) * w, [r[d] for d in R.DATASET_ORDER], w,
                   label=R.DISPLAY[m], color=R.COLORS[m])
        ax.set_xticks(xs); ax.set_xticklabels(R.DATASET_ORDER)
        ax.set_title(lab); ax.grid(alpha=0.25, axis="y")
        if metric == "hd95":
            ax.legend(fontsize=7)
    fig.suptitle("Boundary metrics by domain and model (mean over VAL images where valid; "
                 "invalid/empty cases excluded per the frozen sentinel rule)", fontsize=12)
    _save_fig(fig, "boundary", "boundary_grouped_bars.png", fig_id="boundary_grouped_bars",
              title="Boundary metrics grouped bars",
              purpose="HD95 / ASSD / Surface Dice compared per domain across models.",
              source="phase20b_<model>_domain_performance.csv", models="ALL",
              datasets=",".join(R.DATASET_ORDER), metrics="hd95,assd,surface_dice",
              category="boundary")


# --------------------------------------------------------------------------- #
# 15 + 26. Bootstrap / statistical + rank stability
# --------------------------------------------------------------------------- #
def build_bootstrap_figures() -> None:
    plt = _mpl()
    labels = [R.DISPLAY[m] for m in R.MODEL_ORDER]

    # A. observed delta matrix
    dmat = R.paired_delta_matrix()
    fig, ax = plt.subplots(figsize=(7.6, 5.6))
    vmax = float(np.nanmax(np.abs(dmat.to_numpy())))
    _heatmap(ax, dmat, "Paired observed Δ macro-Dice (row − column)", cmap="RdBu_r",
             fmt="{:+.4f}", vmin=-vmax, vmax=vmax, cbar_label="Δ Dice", fontsize=10)
    _save_fig(fig, "bootstrap", "pairwise_delta_matrix.png", fig_id="boot_delta_matrix",
              title="Pairwise ΔDice matrix",
              purpose="Observed paired macro-Dice difference for every model pair.",
              source="phase20b_five_model_paired_bootstrap.csv", models="ALL",
              datasets="MACRO_DOMAIN", metrics="macro_domain_dice", category="bootstrap")

    # B. significance matrix
    smat = R.significance_matrix()
    code = smat.replace({"significant": 2, "n.s.": 1, "diagonal": 0})
    fig, ax = plt.subplots(figsize=(7.6, 5.6))
    im = ax.imshow(code.to_numpy(dtype=float), cmap="RdYlGn", vmin=-0.2, vmax=2.2, aspect="auto")
    ax.set_xticks(range(len(labels))); ax.set_xticklabels(labels, rotation=20, ha="right", fontsize=9)
    ax.set_yticks(range(len(labels))); ax.set_yticklabels(labels, fontsize=9)
    for i in range(len(labels)):
        for j in range(len(labels)):
            ax.text(j, i, smat.iloc[i, j], ha="center", va="center", fontsize=8)
    ax.set_title("Paired-bootstrap significance matrix\n"
                 "green = significant at 0.05 · yellow = not significant · grey = diagonal", fontsize=11)
    _save_fig(fig, "bootstrap", "significance_matrix.png", fig_id="boot_significance_matrix",
              title="Statistical significance matrix",
              purpose="Which pairwise differences are statistically significant.",
              source="phase20b_five_model_paired_bootstrap.csv", models="ALL",
              datasets="MACRO_DOMAIN", metrics="macro_domain_dice", category="bootstrap")

    # C. forest plot
    paired = R.load_paired_bootstrap().copy()
    paired["label"] = paired.apply(
        lambda r: f"{R.SHORT[r['model_a']]} − {R.SHORT[r['model_b']]}", axis=1)
    paired = paired.sort_values("observed_diff")
    fig, ax = plt.subplots(figsize=(9.5, 6))
    y = np.arange(len(paired))
    ax.errorbar(paired["observed_diff"], y,
                xerr=[paired["observed_diff"] - paired["diff_ci_low"],
                      paired["diff_ci_high"] - paired["observed_diff"]],
                fmt="o", color="#333", ecolor="#888", capsize=3, lw=1.1)
    for i, (_, r) in enumerate(paired.iterrows()):
        ax.plot(r["observed_diff"], i, "o", color="#d62728" if r["significant_at_0.05"] else "#1f77b4")
    ax.axvline(0, color="black", ls="--", lw=1.2, label="zero (no difference)")
    ax.set_yticks(y); ax.set_yticklabels(paired["label"], fontsize=9)
    ax.set_xlabel("Δ macro-domain Dice (95% paired-bootstrap CI)")
    ax.set_title("Forest plot — all 10 pairwise comparisons\n"
                 "red = CI excludes zero (significant) · blue = crosses zero", fontsize=11)
    ax.legend(fontsize=8); ax.grid(alpha=0.25, axis="x")
    _save_fig(fig, "bootstrap", "ci_forest.png", fig_id="boot_ci_forest",
              title="Pairwise CI forest plot",
              purpose="Point estimate and 95% CI of every pairwise macro-Dice difference.",
              source="phase20b_five_model_paired_bootstrap.csv", models="ALL",
              datasets="MACRO_DOMAIN", metrics="macro_domain_dice", category="bootstrap")

    # D. p-value heatmap
    pmat = R.pvalue_matrix()
    fig, ax = plt.subplots(figsize=(7.6, 5.6))
    _heatmap(ax, pmat, "Paired-bootstrap two-sided p-value", cmap="viridis_r",
             fmt="{:.3f}", vmin=0, vmax=1, cbar_label="p", fontsize=10)
    _save_fig(fig, "bootstrap", "pvalue_heatmap.png", fig_id="boot_pvalue_heatmap",
              title="Pairwise p-value heatmap", purpose="Two-sided p-values for every model pair.",
              source="phase20b_five_model_paired_bootstrap.csv", models="ALL",
              datasets="MACRO_DOMAIN", metrics="p_value", category="bootstrap")

    # E. effect-direction heatmap
    _dv = dmat.to_numpy(dtype=float)
    dir_mat = pd.DataFrame(np.where(np.isnan(_dv), np.nan, np.sign(_dv)),
                           index=dmat.index, columns=dmat.columns)
    fig, ax = plt.subplots(figsize=(7.6, 5.6))
    im = ax.imshow(dir_mat.to_numpy(dtype=float), cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
    ax.set_xticks(range(len(labels))); ax.set_xticklabels(labels, rotation=20, ha="right", fontsize=9)
    ax.set_yticks(range(len(labels))); ax.set_yticklabels(labels, fontsize=9)
    for i in range(len(labels)):
        for j in range(len(labels)):
            v = dir_mat.iloc[i, j]
            ax.text(j, i, "0" if pd.isna(v) else ("+" if v > 0 else ("−" if v < 0 else "=")),
                    ha="center", va="center", fontsize=13)
    ax.set_title("Effect direction (row − column)\n+ = row higher, − = row lower", fontsize=11)
    _save_fig(fig, "bootstrap", "effect_direction_heatmap.png", fig_id="boot_effect_direction",
              title="Effect-direction heatmap",
              purpose="Sign of every pairwise difference at a glance.",
              source="phase20b_five_model_paired_bootstrap.csv", models="ALL",
              datasets="MACRO_DOMAIN", metrics="macro_domain_dice", category="bootstrap")


def build_rank_stability_figure() -> None:
    plt = _mpl()
    rs = R.rank_stability()
    freq = rs["rank_frequency"]

    fig, axes = plt.subplots(1, 2, figsize=(18, 6))
    ax = axes[0]
    xs = np.arange(len(R.MODEL_ORDER))
    bottom = np.zeros(len(R.MODEL_ORDER))
    rank_colors = ["#2ca02c", "#8cbf3f", "#ffd92f", "#f47c3c", "#d62728"]
    for r in range(1, len(R.MODEL_ORDER) + 1):
        vals = np.array([freq.loc[f"rank_{r}", R.DISPLAY[m]] for m in R.MODEL_ORDER])
        ax.bar(xs, vals, bottom=bottom, color=rank_colors[r - 1], label=f"rank {r}")
        bottom += vals
    ax.set_xticks(xs); ax.set_xticklabels([R.DISPLAY[m] for m in R.MODEL_ORDER], rotation=15, fontsize=8)
    ax.set_ylabel("bootstrap frequency"); ax.set_ylim(0, 1)
    ax.set_title(f"Rank frequency over {rs['n_boot']} bootstrap replicates")
    ax.legend(fontsize=8, ncol=5); ax.grid(alpha=0.25, axis="y")

    ax = axes[1]
    macro = rs["macro_boot"]
    data = [macro[i] for i in range(len(R.MODEL_ORDER))]
    bp = ax.boxplot(data, tick_labels=[R.DISPLAY[m] for m in R.MODEL_ORDER], patch_artist=True, showfliers=False)
    for patch, m in zip(bp["boxes"], R.MODEL_ORDER):
        patch.set_facecolor(R.COLORS[m]); patch.set_alpha(0.7)
    ax.set_ylabel("bootstrap macro-domain Dice")
    ax.set_title("Bootstrap distribution of macro-domain Dice\nDESCRIPTIVE_BOOTSTRAP_ANALYSIS (not a selection gate)")
    ax.tick_params(axis="x", labelsize=8, rotation=15); ax.grid(alpha=0.25, axis="y")

    fig.suptitle("Rank stability — DeepLabV3+ and Transformer/MiT-style U-Net exchange the top two ranks",
                 fontsize=13)
    _save_fig(fig, "bootstrap", "rank_stability.png", fig_id="boot_rank_stability",
              title="Bootstrap rank stability",
              purpose="DESCRIPTIVE bootstrap analysis of how often each model attains each rank.",
              source="phase20b_five_model_per_image_val_metrics.csv (reconstructed paired resampling)",
              models="ALL", datasets="MACRO_DOMAIN", metrics="macro_domain_dice", category="bootstrap")


# --------------------------------------------------------------------------- #
# 16-17. Distributions + model x sample
# --------------------------------------------------------------------------- #
def build_distribution_figures() -> None:
    plt = _mpl()
    pi = R.load_per_image_all5()
    metrics = ["dice", "iou", "precision", "recall", "mcc"]

    fig, axes = plt.subplots(len(metrics), len(R.DATASET_ORDER), figsize=(20, 22))
    for i, metric in enumerate(metrics):
        for j, d in enumerate(R.DATASET_ORDER):
            ax = axes[i, j]
            data = [pi[(pi["model_key"] == m) & (pi["dataset"] == d)][metric].dropna().to_numpy()
                    for m in R.MODEL_ORDER]
            bp = ax.boxplot(data, patch_artist=True, showfliers=False,
                            tick_labels=[R.SHORT[m] for m in R.MODEL_ORDER])
            for patch, m in zip(bp["boxes"], R.MODEL_ORDER):
                patch.set_facecolor(R.COLORS[m]); patch.set_alpha(0.7)
            ax.set_title(f"{metric} — {d}", fontsize=9)
            ax.tick_params(axis="x", labelsize=7, rotation=20); ax.grid(alpha=0.25, axis="y")
            if j == 0:
                ax.set_ylabel(metric)
    fig.suptitle("Per-image metric distributions by domain (box plots, outliers hidden)", fontsize=14)
    _save_fig(fig, "distributions", "boxplots_by_domain.png", fig_id="dist_boxplots",
              title="Per-image distribution box plots",
              purpose="Per-case dispersion of Dice/IoU/precision/recall/MCC by domain and model.",
              source="phase20b_five_model_per_image_val_metrics.csv", models="ALL",
              datasets=",".join(R.DATASET_ORDER), metrics=",".join(metrics), category="distribution")

    # ECDF of Dice + violin of Dice
    fig, axes = plt.subplots(1, 4, figsize=(20, 5))
    for ax, d in zip(axes, R.DATASET_ORDER):
        for m in R.MODEL_ORDER:
            v = np.sort(pi[(pi["model_key"] == m) & (pi["dataset"] == d)]["dice"].dropna().to_numpy())
            ax.plot(v, np.arange(1, len(v) + 1) / len(v), lw=1.3, color=R.COLORS[m], label=R.DISPLAY[m])
        ax.set_title(f"Dice ECDF — {d}"); ax.set_xlabel("Dice"); ax.set_ylabel("ECDF")
        ax.legend(fontsize=7); ax.grid(alpha=0.25)
    fig.suptitle("Empirical CDF of per-image Dice by domain", fontsize=13)
    _save_fig(fig, "distributions", "ecdf_dice.png", fig_id="dist_ecdf_dice",
              title="Dice ECDF per domain", purpose="Full distribution comparison, not just the mean.",
              source="phase20b_five_model_per_image_val_metrics.csv", models="ALL",
              datasets=",".join(R.DATASET_ORDER), metrics="dice", category="distribution")

    fig, axes = plt.subplots(1, 4, figsize=(20, 5))
    for ax, d in zip(axes, R.DATASET_ORDER):
        data = [pi[(pi["model_key"] == m) & (pi["dataset"] == d)]["dice"].dropna().to_numpy()
                for m in R.MODEL_ORDER]
        parts = ax.violinplot(data, showmedians=True)
        for pc, m in zip(parts["bodies"], R.MODEL_ORDER):
            pc.set_facecolor(R.COLORS[m]); pc.set_alpha(0.7)
        ax.set_xticks(range(1, len(R.MODEL_ORDER) + 1))
        ax.set_xticklabels([R.SHORT[m] for m in R.MODEL_ORDER], rotation=20, fontsize=8)
        ax.set_title(f"Dice violin — {d}"); ax.grid(alpha=0.25, axis="y")
    fig.suptitle("Violin plots of per-image Dice by domain", fontsize=13)
    _save_fig(fig, "distributions", "violin_dice.png", fig_id="dist_violin_dice",
              title="Dice violin plots per domain", purpose="Distribution shape comparison per domain.",
              source="phase20b_five_model_per_image_val_metrics.csv", models="ALL",
              datasets=",".join(R.DATASET_ORDER), metrics="dice", category="distribution")


def build_sample_heatmap_figures() -> None:
    plt = _mpl()
    dmap = R.sample_domain_map()

    # A. ordered global heatmap (samples ordered by domain then sample_id)
    mat = R.model_sample_matrix("dice")
    ordered = sorted(mat.columns, key=lambda s: (R.DATASET_ORDER.index(dmap[s]), s))
    mat_ord = mat[ordered]
    fig, ax = plt.subplots(figsize=(20, 4.2))
    im = ax.imshow(mat_ord.to_numpy(dtype=float), cmap="viridis", aspect="auto", vmin=0, vmax=1)
    ax.set_yticks(range(len(mat_ord))); ax.set_yticklabels(mat_ord.index, fontsize=9)
    bounds = np.cumsum([sum(1 for s in ordered if dmap[s] == d) for d in R.DATASET_ORDER])
    for b in bounds[:-1]:
        ax.axvline(b - 0.5, color="white", lw=1.2)
    for d, b0, b1 in zip(R.DATASET_ORDER, np.concatenate([[0], bounds[:-1]]), bounds):
        ax.text((b0 + b1) / 2, -0.9, d, ha="center", fontsize=10, color=R.DOMAIN_COLORS[d])
    ax.set_title("model × sample Dice — all 808 VAL cases (ordered by domain, then sample_id)", fontsize=12)
    fig.colorbar(im, ax=ax, fraction=0.02, pad=0.01, label="Dice")
    _save_fig(fig, "distributions", "sample_heatmap_global.png", fig_id="dist_sample_heatmap_global",
              title="model × sample Dice heatmap (global)",
              purpose="Every VAL case × every model; ordering is deterministic (domain, sample_id).",
              source="phase20b_five_model_per_image_val_metrics.csv", models="ALL",
              datasets=",".join(R.DATASET_ORDER), metrics="dice", category="distribution")

    fig, axes = plt.subplots(4, 1, figsize=(20, 12))
    for ax, d in zip(axes, R.DATASET_ORDER):
        cols = sorted([s for s in mat.columns if dmap[s] == d])
        sub = mat[cols]
        im = ax.imshow(sub.to_numpy(dtype=float), cmap="viridis", aspect="auto", vmin=0, vmax=1)
        ax.set_yticks(range(len(sub))); ax.set_yticklabels(sub.index, fontsize=8)
        ax.set_title(f"{d} — {len(cols)} cases", fontsize=10)
        fig.colorbar(im, ax=ax, fraction=0.02, pad=0.01)
    fig.suptitle("model × sample Dice — domain-separated", fontsize=13)
    _save_fig(fig, "distributions", "sample_heatmap_domains.png", fig_id="dist_sample_heatmap_domains",
              title="model × sample Dice heatmap (by domain)",
              purpose="Domain-separated per-case performance for all models.",
              source="phase20b_five_model_per_image_val_metrics.csv", models="ALL",
              datasets=",".join(R.DATASET_ORDER), metrics="dice", category="distribution")

    # C. difficult-case subset (mean Dice across models in the lowest quartile)
    mean_dice = mat.mean(axis=0)
    thr = mean_dice.quantile(0.25)
    hard = sorted(mean_dice[mean_dice <= thr].index, key=lambda s: (dmap[s], s))
    sub = mat[hard]
    fig, ax = plt.subplots(figsize=(20, 4.4))
    im = ax.imshow(sub.to_numpy(dtype=float), cmap="magma", aspect="auto", vmin=0, vmax=1)
    ax.set_yticks(range(len(sub))); ax.set_yticklabels(sub.index, fontsize=9)
    ax.set_title(f"Difficult-case subset — mean-across-models Dice ≤ Q25 ({thr:.3f}); "
                 f"n={len(hard)} cases (ordering: domain, sample_id)", fontsize=11)
    fig.colorbar(im, ax=ax, fraction=0.02, pad=0.01, label="Dice")
    _save_fig(fig, "distributions", "difficult_cases_heatmap.png", fig_id="dist_difficult_heatmap",
              title="Difficult-case heatmap",
              purpose="The hardest quartile of cases, showing which models recover them.",
              source="phase20b_five_model_per_image_val_metrics.csv", models="ALL",
              datasets=",".join(R.DATASET_ORDER), metrics="dice", category="distribution")


# --------------------------------------------------------------------------- #
# 18. Agreement / disagreement
# --------------------------------------------------------------------------- #
def build_agreement_figures() -> None:
    plt = _mpl()
    corr = R.cross_model_dice_correlation("dice")
    fig, ax = plt.subplots(figsize=(7.4, 6.2))
    _heatmap(ax, corr, "Cross-model Pearson correlation of per-image Dice", cmap="viridis",
             fmt="{:.3f}", vmin=float(corr.to_numpy().min()), vmax=1.0,
             cbar_label="Pearson r", fontsize=10)
    _save_fig(fig, "agreement", "dice_correlation_matrix.png", fig_id="agree_corr_matrix",
              title="Cross-model Dice correlation matrix",
              purpose="How strongly models agree on per-case difficulty.",
              source="phase20b_five_model_per_image_val_metrics.csv", models="ALL",
              datasets="ALL", metrics="dice", category="agreement")

    # pairwise scatter grid (10 pairs)
    pi = R.load_per_image_all5()
    wide = pi.pivot_table(index="sample_id", columns="model_key", values="dice", aggfunc="mean")
    wide = wide[R.MODEL_ORDER]
    pairs = [(a, b) for i, a in enumerate(R.MODEL_ORDER) for b in R.MODEL_ORDER[i + 1:]]
    fig, axes = plt.subplots(2, 5, figsize=(22, 8.6))
    for ax, (a, b) in zip(axes.ravel(), pairs):
        x = wide[a].to_numpy(); y = wide[b].to_numpy()
        ok = ~(np.isnan(x) | np.isnan(y))
        ax.scatter(x[ok], y[ok], s=6, alpha=0.35, color="#333")
        ax.plot([0, 1], [0, 1], "r--", lw=1.0)
        r = float(np.corrcoef(x[ok], y[ok])[0, 1])
        ax.set_title(f"{R.SHORT[a]} vs {R.SHORT[b]}  (r={r:.3f})", fontsize=9)
        ax.set_xlabel(R.SHORT[a], fontsize=8); ax.set_ylabel(R.SHORT[b], fontsize=8)
        ax.grid(alpha=0.25)
    fig.suptitle("Pairwise per-image Dice scatter (red = identity)", fontsize=13)
    _save_fig(fig, "agreement", "pairwise_scatter.png", fig_id="agree_pairwise_scatter",
              title="Pairwise model Dice scatter grid",
              purpose="Per-case agreement/disagreement between every model pair.",
              source="phase20b_five_model_per_image_val_metrics.csv", models="ALL",
              datasets="ALL", metrics="dice", category="agreement")

    # disagreement magnitude
    mat = R.model_sample_matrix("dice")
    spread = mat.max(axis=0) - mat.min(axis=0)
    by_dom = pd.DataFrame({"dataset": [R.sample_domain_map()[s] for s in spread.index],
                           "spread": spread.to_numpy()})
    fig, axes = plt.subplots(1, 2, figsize=(18, 5))
    ax = axes[0]
    data = [by_dom[by_dom["dataset"] == d]["spread"].to_numpy() for d in R.DATASET_ORDER]
    bp = ax.boxplot(data, patch_artist=True, showfliers=False, tick_labels=R.DATASET_ORDER)
    for patch, d in zip(bp["boxes"], R.DATASET_ORDER):
        patch.set_facecolor(R.DOMAIN_COLORS[d]); patch.set_alpha(0.7)
    ax.set_ylabel("max − min Dice across the five models")
    ax.set_title("Cross-model disagreement per case (by domain)"); ax.grid(alpha=0.25, axis="y")

    ax = axes[1]
    order = spread.sort_values(ascending=False).head(30)
    ax.barh(range(len(order)), order.to_numpy(),
            color=[R.DOMAIN_COLORS[R.sample_domain_map()[s]] for s in order.index])
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels([f"{s[:10]}… ({R.sample_domain_map()[s]})" for s in order.index], fontsize=6)
    ax.invert_yaxis(); ax.set_xlabel("max − min Dice")
    ax.set_title("Top-30 highest-disagreement cases"); ax.grid(alpha=0.25, axis="x")
    fig.suptitle("Cross-model disagreement", fontsize=13)
    _save_fig(fig, "agreement", "disagreement_magnitude.png", fig_id="agree_disagreement",
              title="Cross-model disagreement magnitude",
              purpose="Where models disagree most, and by how much.",
              source="phase20b_five_model_per_image_val_metrics.csv", models="ALL",
              datasets=",".join(R.DATASET_ORDER), metrics="dice", category="agreement")


# --------------------------------------------------------------------------- #
# 19-20. KUB subgroups + size strata
# --------------------------------------------------------------------------- #
def build_kub_subgroup_figures() -> None:
    plt = _mpl()
    subs = ["Kidney_Stone", "Bladder_Stone", "Ureteric_Stone", "KUB_ALL"]

    mat = R.kub_subgroup_matrix("dice").set_index("model")[subs]
    fig, ax = plt.subplots(figsize=(8.6, 5))
    _heatmap(ax, mat, "model × KUB subgroup — Dice (REPORTING ONLY)", cmap="viridis",
             fmt="{:.4f}", cbar_label="Dice", fontsize=10)
    _save_fig(fig, "kub_subgroups", "subgroup_dice_heatmap.png", fig_id="kubsub_dice_heatmap",
              title="KUB subgroup Dice heatmap",
              purpose="Subgroup-level Dice for every model (reporting only, never a model input).",
              source="phase20b_<model>_kub_subgroup_analysis.csv", models="ALL",
              datasets="KUB", metrics="dice", category="kub_subgroup")

    fig, ax = plt.subplots(figsize=(11, 5))
    w = 0.16
    xs = np.arange(len(subs))
    for i, m in enumerate(R.MODEL_ORDER):
        row = R.kub_subgroup_matrix("dice")
        r = row[row["model_key"] == m].iloc[0]
        ax.bar(xs + (i - 2) * w, [r[s] for s in subs], w, label=R.DISPLAY[m], color=R.COLORS[m])
    ax.set_xticks(xs); ax.set_xticklabels(subs)
    ax.set_ylabel("Dice"); ax.set_ylim(0.55, 0.95)
    ax.set_title("KUB subgroup Dice by model (REPORTING ONLY)")
    ax.legend(fontsize=8, ncol=5); ax.grid(alpha=0.25, axis="y")
    _save_fig(fig, "kub_subgroups", "subgroup_dice_bars.png", fig_id="kubsub_dice_bars",
              title="KUB subgroup Dice grouped bars", purpose="Subgroup comparison across models.",
              source="phase20b_<model>_kub_subgroup_analysis.csv", models="ALL",
              datasets="KUB", metrics="dice", category="kub_subgroup")

    mat = R.kub_subgroup_matrix("recall").set_index("model")[subs]
    fig, ax = plt.subplots(figsize=(8.6, 5))
    _heatmap(ax, mat, "model × KUB subgroup — Recall (REPORTING ONLY)", cmap="viridis",
             fmt="{:.4f}", cbar_label="Recall", fontsize=10)
    _save_fig(fig, "kub_subgroups", "subgroup_recall_heatmap.png", fig_id="kubsub_recall_heatmap",
              title="KUB subgroup recall heatmap", purpose="Subgroup recall across models.",
              source="phase20b_<model>_kub_subgroup_analysis.csv", models="ALL",
              datasets="KUB", metrics="recall", category="kub_subgroup")

    rows = []
    for m in R.MODEL_ORDER:
        s = R.load_kub_subgroup(m)
        for _, r in s.iterrows():
            rows.append({"model_key": m, "model": R.DISPLAY[m], "subgroup": r["subgroup"],
                         "empty_prediction_rate": r["empty_prediction_rate"]})
    ep = pd.DataFrame(rows)
    mat = ep.pivot(index="model", columns="subgroup", values="empty_prediction_rate").reindex(
        [R.DISPLAY[m] for m in R.MODEL_ORDER])[subs]
    fig, ax = plt.subplots(figsize=(8.6, 5))
    _heatmap(ax, mat, "model × KUB subgroup — empty-prediction rate", cmap="viridis_r",
             fmt="{:.4f}", cbar_label="empty rate", fontsize=10)
    _save_fig(fig, "kub_subgroups", "subgroup_empty_rate.png", fig_id="kubsub_empty_rate",
              title="KUB subgroup empty-prediction rate",
              purpose="How often each model predicts nothing, by subgroup.",
              source="phase20b_<model>_kub_subgroup_analysis.csv", models="ALL",
              datasets="KUB", metrics="empty_prediction_rate", category="kub_subgroup")


def build_kub_size_figures() -> None:
    plt = _mpl()
    strata = ["TINY", "SMALL", "MEDIUM", "LARGE", "ROI_NOT_PRIMARY_BINNED"]
    ns = R.kub_size_n()

    for metric, fname, lab, rev in [("dice", "size_dice_heatmap.png", "Dice", False),
                                    ("iou", "size_iou_heatmap.png", "IoU", False)]:
        mat = R.kub_size_matrix(metric).set_index("model")[strata]
        fig, ax = plt.subplots(figsize=(9.6, 5))
        _heatmap(ax, mat, f"model × KUB size stratum — {lab} (frozen kub_size_clean_v3_v1)",
                 cmap="viridis_r" if rev else "viridis", fmt="{:.4f}", cbar_label=lab, fontsize=10)
        _save_fig(fig, "kub_size", fname, fig_id=f"kubsize_{metric}_heatmap",
                  title=f"KUB size-stratum {lab} heatmap",
                  purpose="Frozen clean-v3 size strata; ROI_NOT_PRIMARY_BINNED kept separate.",
                  source="phase20b_<model>_kub_size_stratification.csv", models="ALL",
                  datasets="KUB", metrics=metric, category="kub_size")

    fig, ax = plt.subplots(figsize=(12, 5.4))
    w = 0.16
    xs = np.arange(len(strata))
    for i, m in enumerate(R.MODEL_ORDER):
        row = R.kub_size_matrix("dice")
        r = row[row["model_key"] == m].iloc[0]
        ax.bar(xs + (i - 2) * w, [r[s] for s in strata], w, label=R.DISPLAY[m], color=R.COLORS[m])
    ax.set_xticks(xs)
    ax.set_xticklabels([f"{s}\n(n={ns.get(s, 'NA')})" for s in strata], fontsize=9)
    ax.set_ylabel("Dice"); ax.set_title("KUB size-stratum Dice by model "
                                        "(FULL_FIELD TINY/SMALL/MEDIUM/LARGE; ROI reported separately)")
    ax.legend(fontsize=8, ncol=5); ax.grid(alpha=0.25, axis="y")
    _save_fig(fig, "kub_size", "size_dice_grouped_bars.png", fig_id="kubsize_dice_bars",
              title="KUB size-stratum Dice grouped bars",
              purpose="Size-stratum comparison with sample counts.",
              source="phase20b_<model>_kub_size_stratification.csv", models="ALL",
              datasets="KUB", metrics="dice", category="kub_size")

    # interaction plot (line per model across strata)
    fig, ax = plt.subplots(figsize=(10, 5.2))
    rowt = R.kub_size_matrix("dice")
    for m in R.MODEL_ORDER:
        r = rowt[rowt["model_key"] == m].iloc[0]
        ax.plot(strata, [r[s] for s in strata], marker="o", lw=1.5, color=R.COLORS[m], label=R.DISPLAY[m])
    ax.set_ylabel("Dice"); ax.set_title("Size stratum × model interaction (Dice)")
    ax.legend(fontsize=8); ax.grid(alpha=0.25)
    _save_fig(fig, "kub_size", "size_stratum_model_interaction.png", fig_id="kubsize_interaction",
              title="Size-stratum × model interaction",
              purpose="Whether the model ranking changes with object size.",
              source="phase20b_<model>_kub_size_stratification.csv", models="ALL",
              datasets="KUB", metrics="dice", category="kub_size")

    # FULL_FIELD vs ROI descriptive comparison
    fig, ax = plt.subplots(figsize=(10, 5.2))
    ff = ["TINY", "SMALL", "MEDIUM", "LARGE"]
    rowt = R.kub_size_matrix("dice")
    xs = np.arange(len(R.MODEL_ORDER))
    ff_vals = [float(np.nanmean([rowt[rowt["model_key"] == m].iloc[0][s] for s in ff])) for m in R.MODEL_ORDER]
    roi_vals = [float(rowt[rowt["model_key"] == m].iloc[0]["ROI_NOT_PRIMARY_BINNED"]) for m in R.MODEL_ORDER]
    ax.bar(xs - 0.2, ff_vals, 0.4, label="FULL_FIELD (TINY…LARGE mean)", color="#4c72b0")
    ax.bar(xs + 0.2, roi_vals, 0.4, label="ROI_NOT_PRIMARY_BINNED", color="#dd8452")
    ax.set_xticks(xs); ax.set_xticklabels([R.DISPLAY[m] for m in R.MODEL_ORDER], rotation=15, fontsize=8)
    ax.set_ylabel("Dice"); ax.set_title("FULL_FIELD vs ROI acquisition regimes — descriptive only\n"
                                        "(ROI and FULL_FIELD are different acquisition regimes; not directly comparable)")
    ax.legend(fontsize=8); ax.grid(alpha=0.25, axis="y")
    _save_fig(fig, "kub_size", "roi_vs_fullfield.png", fig_id="kubsize_roi_vs_ff",
              title="FULL_FIELD vs ROI descriptive comparison",
              purpose="Keep the two acquisition regimes visibly separate.",
              source="phase20b_<model>_kub_size_stratification.csv", models="ALL",
              datasets="KUB", metrics="dice", category="kub_size")


# --------------------------------------------------------------------------- #
# 21-22. TINY + failure burden
# --------------------------------------------------------------------------- #
def build_tiny_figures() -> None:
    plt = _mpl()
    tiny = R.tiny_per_sample()

    fig, ax = plt.subplots(figsize=(11, 5))
    data = [tiny[tiny["model_key"] == m]["dice"].dropna().to_numpy() for m in R.MODEL_ORDER]
    bp = ax.boxplot(data, patch_artist=True, showfliers=True, tick_labels=[R.DISPLAY[m] for m in R.MODEL_ORDER])
    for patch, m in zip(bp["boxes"], R.MODEL_ORDER):
        patch.set_facecolor(R.COLORS[m]); patch.set_alpha(0.7)
    for i, m in enumerate(R.MODEL_ORDER):
        v = tiny[tiny["model_key"] == m]["dice"].dropna()
        ax.scatter(np.full(len(v), i + 1) + np.random.default_rng(0).normal(0, 0.04, len(v)),
                   v, s=10, color="black", alpha=0.4, zorder=3)
    ax.set_ylabel("Dice"); ax.set_title(f"KUB TINY-object Dice distribution (n={len(data[0])} FULL_FIELD TINY cases)")
    ax.tick_params(axis="x", labelsize=8, rotation=12); ax.grid(alpha=0.25, axis="y")
    _save_fig(fig, "tiny", "tiny_dice_distribution.png", fig_id="tiny_dice_distribution",
              title="KUB TINY Dice distribution",
              purpose="The scientifically important tiny-object regime, per model.",
              source="phase20b_<model>_kub_size_stratification_per_sample.csv", models="ALL",
              datasets="KUB", metrics="dice", category="tiny")

    mat = tiny.pivot_table(index="model", columns="sample_id", values="dice", aggfunc="mean").reindex(
        [R.DISPLAY[m] for m in R.MODEL_ORDER])
    mat = mat[sorted(mat.columns)]
    fig, ax = plt.subplots(figsize=(18, 3.6))
    im = ax.imshow(mat.to_numpy(dtype=float), cmap="magma", aspect="auto", vmin=0, vmax=1)
    ax.set_yticks(range(len(mat))); ax.set_yticklabels(mat.index, fontsize=9)
    ax.set_xlabel("TINY case (ordered by sample_id)")
    ax.set_title(f"TINY per-case Dice heatmap — {mat.shape[1]} cases × 5 models", fontsize=11)
    fig.colorbar(im, ax=ax, fraction=0.02, pad=0.01, label="Dice")
    _save_fig(fig, "tiny", "tiny_case_heatmap.png", fig_id="tiny_case_heatmap",
              title="TINY per-case Dice heatmap",
              purpose="Which tiny cases every model misses vs recovers.",
              source="phase20b_<model>_kub_size_stratification_per_sample.csv", models="ALL",
              datasets="KUB", metrics="dice", category="tiny")

    # TINY per-case comparison: TINY vs macro performance per model
    head = R.headline_table()
    fig, ax = plt.subplots(figsize=(9, 5.2))
    for _, r in head.iterrows():
        m = r["model_key"]
        tiny_mean = tiny[tiny["model_key"] == m]["dice"].mean()
        ax.scatter(r["macro_dice"], tiny_mean, s=120, color=R.COLORS[m], label=R.DISPLAY[m], zorder=3)
        ax.annotate(R.SHORT[m], (r["macro_dice"], tiny_mean), fontsize=8,
                    xytext=(5, 5), textcoords="offset points")
    ax.set_xlabel("macro-domain Dice"); ax.set_ylabel("KUB TINY Dice")
    ax.set_title("TINY performance vs overall performance\n(tiny-object performance does not track overall performance)")
    ax.grid(alpha=0.25)
    _save_fig(fig, "tiny", "tiny_vs_macro.png", fig_id="tiny_vs_macro",
              title="TINY vs macro performance",
              purpose="Show that tiny-object performance is largely decoupled from overall Dice.",
              source="phase20b_five_model_comparison_final.csv + TINY per-sample table", models="ALL",
              datasets="KUB", metrics="dice", category="tiny")


def build_failure_figures() -> None:
    plt = _mpl()
    fb = R.failure_burden_table()

    for metric, fname, lab in [("fp_burden_ratio", "fp_burden_heatmap.png", "FP burden ratio (FP / GT-FG px)"),
                               ("fn_burden_ratio", "fn_burden_heatmap.png", "FN burden ratio (FN / GT-FG px)")]:
        mat = fb.pivot(index="model", columns="dataset", values=metric).reindex(
            [R.DISPLAY[m] for m in R.MODEL_ORDER])[R.DATASET_ORDER]
        fig, ax = plt.subplots(figsize=(7.6, 4.6))
        _heatmap(ax, mat, f"model × domain — {lab}", cmap="viridis_r", fmt="{:.4f}",
                 cbar_label=lab, fontsize=10)
        _save_fig(fig, "failure_cases", fname, fig_id=f"failure_{metric}",
                  title=f"model × domain {lab}", purpose=f"{lab} across models and domains.",
                  source="phase20b_<model>_per_image_val_metrics.csv", models="ALL",
                  datasets=",".join(R.DATASET_ORDER), metrics=metric, category="failure")

    fig, axes = plt.subplots(1, 2, figsize=(18, 5.4))
    ax = axes[0]
    mat = fb.pivot(index="model", columns="dataset", values="complete_miss_n").reindex(
        [R.DISPLAY[m] for m in R.MODEL_ORDER])[R.DATASET_ORDER]
    _heatmap(ax, mat, "complete-miss count (GT non-empty, prediction empty)", cmap="Reds",
             fmt="{:.0f}", cbar_label="cases", fontsize=9)
    ax = axes[1]
    mat = fb.pivot(index="model", columns="dataset", values="fp_on_empty_gt_n").reindex(
        [R.DISPLAY[m] for m in R.MODEL_ORDER])[R.DATASET_ORDER]
    _heatmap(ax, mat, "false-positive on empty-GT cases", cmap="Reds", fmt="{:.0f}",
             cbar_label="cases", fontsize=9)
    fig.suptitle("Failure burden — complete misses and false positives on empty GT", fontsize=12)
    _save_fig(fig, "failure_cases", "failure_counts.png", fig_id="failure_counts",
              title="Failure counts heatmaps",
              purpose="Counts of the two extreme failure modes per model and domain.",
              source="phase20b_<model>_per_image_val_metrics.csv", models="ALL",
              datasets=",".join(R.DATASET_ORDER), metrics="complete_miss,fp_on_empty_gt",
              category="failure")


# --------------------------------------------------------------------------- #
# 23-25. Efficiency / Pareto / radar
# --------------------------------------------------------------------------- #
def build_efficiency_figures() -> None:
    plt = _mpl()
    eff = R.efficiency_table()
    head = R.headline_table()
    tiny = R.tiny_per_sample()
    tiny_mean = {m: float(tiny[tiny["model_key"] == m]["dice"].mean()) for m in R.MODEL_ORDER}
    kub_dice = R.per_domain_table("dice").set_index("model_key")["KUB"].to_dict()

    specs = [
        ("params", "macro_dice", "params_vs_macro.png", "Parameters", "macro-domain Dice", "efficiency_params_macro"),
        ("params", "kub", "params_vs_kub.png", "Parameters", "KUB Dice", "efficiency_params_kub"),
        ("params", "tiny", "params_vs_tiny.png", "Parameters", "KUB TINY Dice", "efficiency_params_tiny"),
        ("total_training_seconds", "macro_dice", "time_vs_macro.png", "Total training time (s)",
         "macro-domain Dice", "efficiency_time_macro"),
        ("inference_ms_per_sample", "macro_dice", "inference_vs_macro.png",
         "Inference ms / sample (808 VAL)", "macro-domain Dice", "efficiency_inference_macro"),
    ]
    for xcol, ycol, fname, xlab, ylab, fig_id in specs:
        fig, ax = plt.subplots(figsize=(8.4, 5.4))
        for _, r in eff.iterrows():
            m = r["model_key"]
            yv = {"macro_dice": r["params"] * 0 + head.set_index("model_key").loc[m, "macro_dice"],
                  "kub": kub_dice[m], "tiny": tiny_mean[m]}[ycol]
            xv = r[xcol]
            if pd.isna(xv) or pd.isna(yv):
                continue
            ax.scatter(xv, yv, s=140, color=R.COLORS[m], zorder=3, label=R.DISPLAY[m])
            ax.annotate(R.SHORT[m], (xv, yv), fontsize=8, xytext=(6, 5), textcoords="offset points")
        ax.set_xlabel(xlab); ax.set_ylabel(ylab)
        ax.set_title(f"{xlab} vs {ylab}")
        ax.grid(alpha=0.25)
        _save_fig(fig, "efficiency", fname, fig_id=fig_id, title=f"{xlab} vs {ylab}",
                  purpose="Efficiency / complexity trade-off (descriptive).",
                  source="experiments/<exp>/closure.json, history.csv, val_evaluation.json",
                  models="ALL", datasets="ALL", metrics=ylab, category="efficiency")

    # Pareto fronts
    def _pareto(xs, ys):
        pts = sorted(zip(xs, ys))
        front, best = [], -np.inf
        for x, y in pts:
            if y > best:
                front.append((x, y)); best = y
        return front

    for xcol, ycol, fname, xlab, ylab, fig_id in [
            ("params", "macro_dice", "pareto_params_macro.png", "Parameters", "macro-domain Dice",
             "pareto_params_macro"),
            ("total_training_seconds", "macro_dice", "pareto_time_macro.png", "Total training time (s)",
             "macro-domain Dice", "pareto_time_macro"),
            ("macro_dice", "tiny", "pareto_tiny_macro.png", "macro-domain Dice", "KUB TINY Dice",
             "pareto_tiny_macro")]:
        fig, ax = plt.subplots(figsize=(8.4, 5.4))
        xs, ys, labels = [], [], []
        for _, r in eff.iterrows():
            m = r["model_key"]
            xv = {"params": r["params"], "total_training_seconds": r["total_training_seconds"],
                  "macro_dice": head.set_index("model_key").loc[m, "macro_dice"]}[xcol]
            yv = {"macro_dice": head.set_index("model_key").loc[m, "macro_dice"],
                  "tiny": tiny_mean[m]}[ycol]
            xs.append(xv); ys.append(yv); labels.append(m)
        ax.scatter(xs, ys, s=140, c=[R.COLORS[m] for m in labels], zorder=3)
        for x, y, m in zip(xs, ys, labels):
            ax.annotate(R.SHORT[m], (x, y), fontsize=8, xytext=(6, 5), textcoords="offset points")
        front = _pareto(xs, ys)
        ax.plot([p[0] for p in front], [p[1] for p in front], "k--", lw=1.2, label="non-dominated front")
        ax.set_xlabel(xlab); ax.set_ylabel(ylab); ax.set_title(f"Pareto front — {ylab} vs {xlab}")
        ax.legend(fontsize=8); ax.grid(alpha=0.25)
        _save_fig(fig, "efficiency", fname, fig_id=fig_id, title=f"Pareto — {ylab} vs {xlab}",
                  purpose="Descriptive trade-off; no absolute winner is declared.",
                  source="experiments/<exp>/closure.json + headline/TINY tables", models="ALL",
                  datasets="ALL", metrics=f"{xlab},{ylab}", category="efficiency")

    # radar (supplemental)
    metrics = ["dice_ISIC", "dice_BUSI", "dice_KVASIR", "dice_KUB"]
    macro_adv = R.macro_advanced_table().set_index("model_key")
    radar_metrics = metrics + ["precision", "recall", "specificity", "mcc"]
    angles = np.linspace(0, 2 * np.pi, len(radar_metrics), endpoint=False).tolist()
    angles += angles[:1]
    fig = plt.figure(figsize=(8.4, 8.4))
    ax = fig.add_subplot(111, polar=True)
    comp = R.load_comparison().set_index("model_key")
    for m in R.MODEL_ORDER:
        vals = []
        for rmet in radar_metrics:
            if rmet.startswith("dice_"):
                vals.append(float(comp.loc[m, rmet]))
            else:
                vals.append(float(macro_adv.loc[m, rmet]))
        vals += vals[:1]
        ax.plot(angles, vals, lw=1.5, color=R.COLORS[m], label=R.DISPLAY[m])
        ax.fill(angles, vals, color=R.COLORS[m], alpha=0.08)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels([m.replace("dice_", "") for m in radar_metrics], fontsize=9)
    ax.set_title("Radar — per-domain Dice + macro precision/recall/specificity/MCC\n"
                 "(supplemental only; all axes higher-is-better, raw scale)", fontsize=11)
    ax.legend(fontsize=8, loc="upper right", bbox_to_anchor=(1.25, 1.1))
    _save_fig(fig, "efficiency", "radar.png", fig_id="efficiency_radar",
              title="Radar / spider plot (supplemental)",
              purpose="Supplemental multi-axis profile; never primary evidence.",
              source="phase20b_five_model_comparison_final.csv + macro advanced table",
              models="ALL", datasets=",".join(R.DATASET_ORDER),
              metrics=",".join(radar_metrics), category="efficiency")


# --------------------------------------------------------------------------- #
# 27-29. Galleries (same-case cross-model, detailed per-model, failure)
# --------------------------------------------------------------------------- #
def _load_rgb(path, size: int = 256) -> np.ndarray:
    """Gallery panels are deliberately downsampled: the full-resolution evidence is the
    persisted NPZ, and a reviewer gallery only needs readable, not native, pixels."""
    from PIL import Image
    im = Image.open(path).convert("RGB").resize((size, size), Image.BILINEAR)
    return np.asarray(im)


def _half(a: np.ndarray) -> np.ndarray:
    return a[::2, ::2]


def _error_map(gt: np.ndarray, pred: np.ndarray) -> np.ndarray:
    """TP = green, FP = red, FN = blue, TN = white."""
    out = np.ones((*gt.shape, 3), dtype=np.float32)
    out[gt & pred] = [0.16, 0.65, 0.20]     # TP
    out[~gt & pred] = [0.84, 0.15, 0.16]    # FP
    out[gt & ~pred] = [0.12, 0.47, 0.71]    # FN
    return out


def _npz_lookup(model_key: str) -> dict:
    man = R.load_pred_manifest(model_key)
    return dict(zip(man["sample_id"], man["npz_path"]))


def _val_meta() -> dict:
    val = R.load_val_manifest()
    return {r["sample_id"]: r for _, r in val.iterrows()}


def build_gallery_figures(embed_detailed_per_model_dataset: bool = True) -> None:
    """Same-case cross-model pages (64 cases) + detailed per-model pages.

    The 64-case gallery is the FROZEN, prediction-independent canonical set
    (``phase20b_gallery_selection.csv``). The detailed per-model galleries are a
    separate, larger qualitative evidence set (5 models x 4 datasets x 16 cases).
    """
    plt = _mpl()
    gal = R.load_gallery()
    meta = _val_meta()
    lookups = {m: _npz_lookup(m) for m in R.MODEL_ORDER}

    # ---- A. cross-model pages: 4 cases/page, 7 columns ---------------------
    per_page = 4
    pages = [gal.iloc[i:i + per_page] for i in range(0, len(gal), per_page)]
    for pi_, page in enumerate(pages, start=1):
        n = len(page)
        fig, axes = plt.subplots(n, 2 + len(R.MODEL_ORDER), figsize=(2.0 * (2 + len(R.MODEL_ORDER)), 2.1 * n))
        if n == 1:
            axes = axes.reshape(1, -1)
        for r, (_, row) in enumerate(page.iterrows()):
            sid, d = row["sample_id"], row["dataset"]
            m = meta[sid]
            img = _load_rgb(m["image_path"])
            z0 = R.load_prediction(lookups[R.MODEL_ORDER[0]][sid])
            gt = _half(z0["gt"])
            axes[r, 0].imshow(img); axes[r, 0].set_ylabel(f"{d}\n{sid[:10]}…", fontsize=7)
            axes[r, 1].imshow(gt, cmap="gray")
            for c, mk in enumerate(R.MODEL_ORDER, start=2):
                z = R.load_prediction(lookups[mk][sid])
                axes[r, c].imshow(_error_map(_half(z["gt"]), _half(z["pred"])))
            for c in range(2 + len(R.MODEL_ORDER)):
                axes[r, c].set_xticks([]); axes[r, c].set_yticks([])
            if r == 0:
                for c, name in enumerate(["Original", "GT"] + [R.SHORT[mk] for mk in R.MODEL_ORDER]):
                    axes[0, c].set_title(name, fontsize=8)
        fig.suptitle(f"Canonical 64-case gallery — cross-model error maps (TP green / FP red / FN blue) "
                     f"— page {pi_}/{len(pages)}", fontsize=12)
        _save_fig(fig, "galleries", f"cross_model_page_{pi_:02d}.png",
                  fig_id=f"gallery_cross_{pi_:02d}",
                  title=f"Cross-model same-case gallery page {pi_}",
                  purpose="Compare all five models on identical frozen VAL cases.",
                  source="phase20b_gallery_selection.csv + prediction NPZ + manifest images",
                  models="ALL", datasets=",".join(R.DATASET_ORDER), metrics="dice",
                  category="gallery", dpi=90)

    # ---- B. detailed per-model pages: 8 cases/page, 8 panels ---------------
    per_page = 8
    for mk in R.MODEL_ORDER:
        for d in R.DATASET_ORDER:
            ids = gal[gal["dataset"] == d]["sample_id"].tolist()
            pages_d = [ids[i:i + per_page] for i in range(0, len(ids), per_page)]
            for pg, chunk in enumerate(pages_d, start=1):
                n = len(chunk)
                fig, axes = plt.subplots(n, 8, figsize=(1.7 * 8, 1.8 * n))
                if n == 1:
                    axes = axes.reshape(1, -1)
                for r, sid in enumerate(chunk):
                    m = meta[sid]
                    img = _load_rgb(m["image_path"])
                    z = R.load_prediction(lookups[mk][sid])
                    gt, pred, prob = _half(z["gt"]), _half(z["pred"]), _half(z["prob"])
                    overlay = img.copy()
                    overlay[pred] = (0.6 * overlay[pred] + 0.4 * np.array([255, 0, 0])).astype(np.uint8)
                    contour = np.stack([gt, gt, gt], axis=-1).astype(np.uint8)
                    panels = [
                        (img, None, "Original"),
                        (gt, "gray", "GT"),
                        (np.where(gt[..., None], np.array([0, 255, 0], np.uint8), img), None, "GT overlay"),
                        (prob, "magma", "probability"),
                        (pred, "gray", "binary pred"),
                        (_error_map(gt, pred), None, "TP/FP/FN"),
                        (overlay, None, "pred overlay"),
                        (np.maximum(img // 2, contour * 255), None, "GT contour"),
                    ]
                    for c, (arr, cmap, name) in enumerate(panels):
                        ax = axes[r, c]
                        ax.imshow(arr, cmap=cmap) if cmap else ax.imshow(arr)
                        ax.set_xticks([]); ax.set_yticks([])
                        if r == 0:
                            ax.set_title(name, fontsize=8)
                    axes[r, 0].set_ylabel(sid[:10] + "…", fontsize=6)
                fig.suptitle(f"{R.DISPLAY[mk]} — {d} detailed gallery (page {pg}/{len(pages_d)}; "
                             f"{len(chunk)} cases)", fontsize=12)
                # Embed one representative page per model (ISIC p1) to keep the notebook compact;
                # every page is saved to disk and listed in the figure inventory.
                embed = embed_detailed_per_model_dataset and pg == 1 and d == "ISIC"
                _save_fig(fig, "galleries", f"detailed_{mk}_{d}_p{pg}.png",
                          fig_id=f"gallery_detailed_{mk}_{d}_{pg}",
                          title=f"{R.DISPLAY[mk]} {d} detailed gallery p{pg}",
                          purpose="Per-case qualitative evidence: original, GT, overlays, probability, prediction, error map, contour.",
                          source="prediction NPZ + manifest images", models=R.DISPLAY[mk],
                          datasets=d, metrics="dice", embedded=embed, category="gallery", dpi=90)


def build_failure_gallery_figures() -> None:
    """Deterministic, OUTCOME-BASED analytical galleries (distinct from the canonical 64)."""
    plt = _mpl()
    gal = R.load_gallery()
    meta = _val_meta()
    lookups = {m: _npz_lookup(m) for m in R.MODEL_ORDER}
    mat = R.model_sample_matrix("dice")
    dmap = R.sample_domain_map()

    all_ids = list(mat.columns)
    mean_d = mat.mean(axis=0)
    min_d = mat.min(axis=0)
    max_d = mat.max(axis=0)

    def _sel(ids, n=8):
        return ids[:n]

    rules = {}
    rules["all_models_fail"] = _sel(sorted(mean_d[mean_d <= mean_d.quantile(0.05)].index.tolist(),
                                           key=lambda s: (dmap[s], s)))
    two_stage = ["deeplabv3plus", "transformer_mit_unet"]
    unet_family = ["unet", "attention_unet", "unetpp"]
    ok_two = mat.loc[[R.DISPLAY[m] for m in two_stage]].min(axis=0) >= 0.8
    bad_unet = mat.loc[[R.DISPLAY[m] for m in unet_family]].max(axis=0) < 0.6
    rules["two_stage_success_unet_fail"] = _sel(sorted(mat.columns[ok_two & bad_unet].tolist(),
                                                       key=lambda s: (dmap[s], s)))
    ok_unet = mat.loc[[R.DISPLAY[m] for m in unet_family]].min(axis=0) >= 0.8
    bad_two = mat.loc[[R.DISPLAY[m] for m in two_stage]].max(axis=0) < 0.6
    rules["unet_family_success"] = _sel(sorted(mat.columns[ok_unet & bad_two].tolist(),
                                               key=lambda s: (dmap[s], s)))
    rules["max_disagreement"] = _sel(sorted((max_d - min_d).sort_values(ascending=False).index.tolist(),
                                            key=lambda s: s))

    tiny = R.tiny_per_sample()
    tiny_pivot = tiny.pivot_table(index="model", columns="sample_id", values="dice", aggfunc="mean")
    tiny_miss = tiny_pivot.mean(axis=0).sort_values()
    rules["kub_tiny_misses"] = _sel(sorted(tiny_miss.index.tolist()))

    pi = R.load_per_image_all5()
    fp_rank = pi[pi["model_key"] == "unet"].set_index("sample_id")["fp"].sort_values(ascending=False)
    fn_rank = pi[pi["model_key"] == "unet"].set_index("sample_id")["fn"].sort_values(ascending=False)
    rules["fp_heavy"] = _sel(fp_rank.index.tolist())
    rules["fn_heavy"] = _sel(fn_rank.index.tolist())

    rules_report = {}
    _EMBED_RULES = {"all_models_fail", "two_stage_success_unet_fail", "kub_tiny_misses"}
    for name, ids in rules.items():
        ids = [s for s in ids if s in meta]
        rules_report[name] = ids
        if not ids:
            continue
        n = len(ids)
        fig, axes = plt.subplots(n, 2 + len(R.MODEL_ORDER), figsize=(2.0 * (2 + len(R.MODEL_ORDER)), 2.1 * n))
        if n == 1:
            axes = axes.reshape(1, -1)
        for r, sid in enumerate(ids):
            m = meta[sid]
            img = _load_rgb(m["image_path"])
            z0 = R.load_prediction(lookups[R.MODEL_ORDER[0]][sid])
            axes[r, 0].imshow(img); axes[r, 0].set_ylabel(f"{dmap[sid]}\n{sid[:8]}…", fontsize=6)
            axes[r, 1].imshow(_half(z0["gt"]), cmap="gray")
            for c, mk in enumerate(R.MODEL_ORDER, start=2):
                z = R.load_prediction(lookups[mk][sid])
                axes[r, c].imshow(_error_map(_half(z["gt"]), _half(z["pred"])))
                d_i = mat.loc[R.DISPLAY[mk], sid]
                axes[r, c].set_xlabel(f"{d_i:.2f}", fontsize=6)
            for c in range(2 + len(R.MODEL_ORDER)):
                axes[r, c].set_xticks([]); axes[r, c].set_yticks([])
            if r == 0:
                for c, nm in enumerate(["Original", "GT"] + [R.SHORT[mk] for mk in R.MODEL_ORDER]):
                    axes[0, c].set_title(nm, fontsize=8)
        fig.suptitle(f"Failure gallery — {name}  (OUTCOME-BASED selection, NOT the canonical 64-case set)",
                     fontsize=12)
        _save_fig(fig, "failure_cases", f"gallery_{name}.png", fig_id=f"failure_gallery_{name}",
                  title=f"Failure gallery — {name}",
                  purpose=f"Outcome-based analytical gallery: {name}.",
                  source="per-image metrics + prediction NPZ + manifest images", models="ALL",
                  datasets=",".join(R.DATASET_ORDER), metrics="dice",
                  embedded=(name in _EMBED_RULES), category="failure", dpi=90)

    _REG.append({
        "figure_id": "failure_gallery_selection_rules", "title": "Failure-gallery selection rules",
        "scientific_purpose": "Deterministic, explicitly-reported outcome-based selection rules for the failure galleries.",
        "source_artifacts": "phase20b_five_model_per_image_val_metrics.csv",
        "models": "ALL", "datasets": ",".join(R.DATASET_ORDER), "metrics": "dice",
        "saved_path": "", "group": "failure_cases", "category": "failure",
        "embedded_in_notebook": True, "image_png_output_present": False,
        "status": "RULESET:" + json.dumps({k: v[:4] for k, v in rules_report.items()}),
    })


# --------------------------------------------------------------------------- #
# Orchestration + inventories
# --------------------------------------------------------------------------- #
def build_all(progress=print) -> dict:
    """Build every figure. Returns the curves/calibration cache for notebook reuse."""
    reset_registry()
    R.FIG_ROOT.mkdir(parents=True, exist_ok=True)
    progress("  [1/16] curves + calibration (persisted probabilities) ...")
    cache = R.curves_and_calibration()
    progress("  [2/16] training figures ..."); build_training_figures()
    progress("  [3/16] primary comparison ..."); build_primary_figures()
    progress("  [4/16] metric heatmaps ..."); build_metric_heatmaps()
    progress("  [5/16] confusion matrices ..."); build_confusion_figures()
    progress("  [6/16] ROC / PR ..."); build_roc_pr_figures(cache)
    progress("  [7/16] calibration ..."); build_calibration_figures(cache)
    progress("  [8/16] boundary metrics ..."); build_boundary_figures()
    progress("  [9/16] bootstrap + rank stability ...")
    build_bootstrap_figures(); build_rank_stability_figure()
    progress("  [10/16] distributions + sample heatmaps ...")
    build_distribution_figures(); build_sample_heatmap_figures()
    progress("  [11/16] agreement ..."); build_agreement_figures()
    progress("  [12/16] KUB subgroups ..."); build_kub_subgroup_figures()
    progress("  [13/16] KUB size strata ..."); build_kub_size_figures()
    progress("  [14/16] TINY ..."); build_tiny_figures()
    progress("  [15/16] efficiency / Pareto / radar ..."); build_efficiency_figures()
    progress("  [16/16] galleries + failure cases ...")
    build_gallery_figures(); build_failure_figures(); build_failure_gallery_figures()
    return cache


# ---- evaluation-matrix visualization coverage ----------------------------- #
#: (matrix_name, source_artifact, metrics, figure_id, visualization_type)
MATRIX_COVERAGE_SPEC = [
    ("macro_domain_dice_ci", "phase20b_five_model_comparison_final.csv", "macro_domain_dice",
     "primary_macro_dice_ci", "bar + 95% CI"),
    ("macro_domain_iou", "phase20b_five_model_comparison_final.csv", "macro_domain_iou",
     "primary_macro_iou_bar", "bar"),
    ("per_domain_dice", "phase20b_<model>_domain_performance.csv", "dice",
     "primary_per_domain_dice_grouped", "grouped bars"),
    ("model_x_domain_dice", "phase20b_<model>_domain_performance.csv", "dice",
     "primary_dice_heatmap", "heatmap"),
    ("model_x_domain_iou", "phase20b_<model>_domain_performance.csv", "iou",
     "primary_iou_heatmap", "heatmap"),
    ("model_x_domain_precision", "phase20b_<model>_domain_performance.csv", "precision",
     "metric_heat_precision", "heatmap"),
    ("model_x_domain_recall", "phase20b_<model>_domain_performance.csv", "recall",
     "metric_heat_recall", "heatmap"),
    ("model_x_domain_specificity", "phase20b_<model>_domain_performance.csv", "specificity",
     "metric_heat_specificity", "heatmap"),
    ("model_x_domain_balanced_accuracy", "phase20b_<model>_domain_performance.csv", "balanced_accuracy",
     "metric_heat_balanced_accuracy", "heatmap"),
    ("model_x_domain_mcc", "phase20b_<model>_domain_performance.csv", "mcc",
     "metric_heat_mcc", "heatmap"),
    ("model_x_domain_hd95", "phase20b_<model>_domain_performance.csv", "hd95",
     "metric_heat_hd95", "heatmap"),
    ("model_x_domain_assd", "phase20b_<model>_domain_performance.csv", "assd",
     "metric_heat_assd", "heatmap"),
    ("model_x_domain_surface_dice", "phase20b_<model>_domain_performance.csv", "surface_dice",
     "metric_heat_surface_dice", "heatmap"),
    ("model_x_domain_roc_auc", "persisted NPZ probs", "roc_auc", "roc_pr_roc_auc", "heatmap"),
    ("model_x_domain_pr_auc", "persisted NPZ probs", "pr_auc", "roc_pr_pr_auc", "heatmap"),
    ("model_x_domain_brier", "persisted NPZ probs", "brier", "calib_brier", "heatmap"),
    ("model_x_domain_ece", "persisted NPZ probs", "ece", "calib_ece", "heatmap"),
    ("model_x_domain_mce", "persisted NPZ probs", "mce", "calib_mce", "heatmap"),
    ("comprehensive_metric_matrix", "phase20b_<model>_domain_performance.csv",
     "15 metrics", "metric_heat_comprehensive", "normalised heatmap"),
    ("confusion_raw_normalised", "phase20b_<model>_confusion_matrices.csv", "tp,tn,fp,fn",
     "confusion_<model>", "confusion heatmaps"),
    ("confusion_sensitivity", "phase20b_<model>_confusion_matrices.csv", "sensitivity",
     "confusion_sensitivity", "heatmap"),
    ("confusion_fpr", "phase20b_<model>_confusion_matrices.csv", "fpr", "confusion_fpr", "heatmap"),
    ("confusion_fnr", "phase20b_<model>_confusion_matrices.csv", "fnr", "confusion_fnr", "heatmap"),
    ("roc_curves", "persisted NPZ probs", "roc", "roc_per_domain", "ROC curves"),
    ("pr_curves", "persisted NPZ probs", "pr", "pr_per_domain", "PR curves"),
    ("reliability_diagrams", "persisted NPZ probs", "reliability", "calib_reliability", "reliability diagram"),
    ("boundary_hd95", "phase20b_<model>_domain_performance.csv", "hd95", "boundary_hd95", "heatmap"),
    ("boundary_assd", "phase20b_<model>_domain_performance.csv", "assd", "boundary_assd", "heatmap"),
    ("boundary_surface_dice", "phase20b_<model>_domain_performance.csv", "surface_dice",
     "boundary_surface_dice", "heatmap"),
    ("pairwise_delta_matrix", "phase20b_five_model_paired_bootstrap.csv", "observed_diff",
     "boot_delta_matrix", "heatmap"),
    ("pairwise_significance", "phase20b_five_model_paired_bootstrap.csv", "significant_at_0.05",
     "boot_significance_matrix", "categorical heatmap"),
    ("pairwise_ci_forest", "phase20b_five_model_paired_bootstrap.csv", "diff CI",
     "boot_ci_forest", "forest plot"),
    ("pairwise_pvalue", "phase20b_five_model_paired_bootstrap.csv", "p_value",
     "boot_pvalue_heatmap", "heatmap"),
    ("pairwise_effect_direction", "phase20b_five_model_paired_bootstrap.csv", "sign",
     "boot_effect_direction", "categorical heatmap"),
    ("bootstrap_rank_stability", "per-image metrics", "rank frequency", "boot_rank_stability",
     "stacked bars + box"),
    ("kub_subgroup_dice", "phase20b_<model>_kub_subgroup_analysis.csv", "dice",
     "kubsub_dice_heatmap", "heatmap"),
    ("kub_subgroup_recall", "phase20b_<model>_kub_subgroup_analysis.csv", "recall",
     "kubsub_recall_heatmap", "heatmap"),
    ("kub_subgroup_empty_rate", "phase20b_<model>_kub_subgroup_analysis.csv", "empty_prediction_rate",
     "kubsub_empty_rate", "heatmap"),
    ("kub_size_dice", "phase20b_<model>_kub_size_stratification.csv", "dice",
     "kubsize_dice_heatmap", "heatmap"),
    ("kub_size_iou", "phase20b_<model>_kub_size_stratification.csv", "iou",
     "kubsize_iou_heatmap", "heatmap"),
    ("kub_size_interaction", "phase20b_<model>_kub_size_stratification.csv", "dice",
     "kubsize_interaction", "line interaction"),
    ("kub_tiny_dice", "phase20b_<model>_kub_size_stratification_per_sample.csv", "dice",
     "tiny_dice_distribution", "box + strip"),
    ("kub_tiny_case_matrix", "phase20b_<model>_kub_size_stratification_per_sample.csv", "dice",
     "tiny_case_heatmap", "heatmap"),
    ("failure_burden_fp", "phase20b_<model>_per_image_val_metrics.csv", "fp_burden_ratio",
     "failure_fp_burden_ratio", "heatmap"),
    ("failure_burden_fn", "phase20b_<model>_per_image_val_metrics.csv", "fn_burden_ratio",
     "failure_fn_burden_ratio", "heatmap"),
    ("failure_counts", "phase20b_<model>_per_image_val_metrics.csv", "complete_miss,fp_on_empty",
     "failure_counts", "heatmap"),
    ("efficiency_params", "experiments/<exp>/closure.json", "params",
     "efficiency_params_macro", "scatter"),
    ("efficiency_time", "experiments/<exp>/closure.json", "total_elapsed_seconds",
     "efficiency_time_macro", "scatter"),
    ("cross_model_correlation", "phase20b_five_model_per_image_val_metrics.csv", "dice",
     "agree_corr_matrix", "correlation heatmap"),
    ("model_x_sample_dice", "phase20b_five_model_per_image_val_metrics.csv", "dice",
     "dist_sample_heatmap_global", "ordered heatmap"),
    ("per_image_distributions", "phase20b_five_model_per_image_val_metrics.csv", "dice,iou,prec,rec,mcc",
     "dist_boxplots", "box plots"),
]


def matrix_coverage() -> pd.DataFrame:
    inv = figure_inventory()
    have = set(inv["figure_id"]) if len(inv) else set()
    rows = []
    for name, source, metrics, fig_id, viz in MATRIX_COVERAGE_SPEC:
        if "<model>" in fig_id:
            present = any(f.startswith(fig_id.split("<model>")[0]) for f in have)
        else:
            present = fig_id in have
        rows.append({
            "matrix_name": name, "source_artifact": source, "metrics": metrics,
            "table_displayed": True, "visualization_type": viz, "figure_id": fig_id,
            "figure_path": (inv[inv["figure_id"] == fig_id]["saved_path"].iloc[0]
                            if fig_id in have else ""),
            "embedded_in_notebook": bool(present), "status": "VISUALIZED" if present else "MISSING",
        })
    return pd.DataFrame(rows)


def write_inventories() -> dict:
    inv = figure_inventory()
    inv_path_csv = R.AUDIT_DIR / "phase20b_figure_inventory.csv"
    inv_path_json = R.AUDIT_DIR / "phase20b_figure_inventory.json"
    inv.to_csv(inv_path_csv, index=False)
    payload = {
        "artifact": "phase20b_figure_inventory",
        "figures_total": int(len(inv)),
        "embedded_total": int(inv["embedded_in_notebook"].sum()),
        "by_group": inv.groupby("group").size().to_dict(),
        "by_category": inv.groupby("category").size().to_dict(),
        "figure_root": R.rel(R.FIG_ROOT),
        "figures": inv.to_dict("records"),
    }
    inv_path_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    cov = matrix_coverage()
    cov_path = R.AUDIT_DIR / "phase20b_evaluation_matrix_visualization_coverage.csv"
    cov.to_csv(cov_path, index=False)
    return {"inventory_csv": inv_path_csv, "inventory_json": inv_path_json,
            "coverage_csv": cov_path, "inventory": inv, "coverage": cov}
