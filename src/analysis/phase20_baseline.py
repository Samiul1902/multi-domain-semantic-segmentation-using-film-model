"""Phase-20 shared four-domain baseline analysis.

The single reusable implementation behind the Phase-20 reviewer notebook. Every
function reads either

  * the persisted per-image metric table, or
  * the persisted per-sample NPZ predictions (prob float16 / pred uint8 / gt uint8)

and NEVER re-runs inference. That is deliberate: the canonical VAL evaluation
happens exactly once, and every derived table or figure is reproducible from
disk afterwards.

Writes nothing on import. See ``build_all`` for the full artifact set.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.metrics.evaluation_metrics import (
    average_precision,
    bootstrap_ci,
    brier_score,
    expected_calibration_error,
    maximum_calibration_error,
    pooled_segmentation_metrics,
    reliability_bins,
    roc_auc,
)

ROOT = Path(__file__).resolve().parent.parent.parent
EXPERIMENT_ID = "phase20_shared_unetpp_fourdomain_seed42_clean_v3"
DATASET_ORDER = ["ISIC", "BUSI", "KVASIR", "KUB"]

PRED_ROOT = ROOT / "reports/predictions" / EXPERIMENT_ID / "val"
EXP_DIR = ROOT / "experiments" / EXPERIMENT_ID
CKPT_DIR = ROOT / "checkpoints" / EXPERIMENT_ID
PROTOCOL_PATH = ROOT / "reports/audits/phase20_shared_global_baseline_protocol.json"
MANIFEST_DIR = ROOT / "manifests/phase4_v3"

PER_IMAGE_PATH = ROOT / "reports/tables/phase20_per_image_val_metrics.csv"
MANIFEST_CSV = ROOT / "reports/tables/phase20_prediction_manifest.csv"
DOMAIN_TABLE_PATH = ROOT / "reports/tables/phase20_domain_performance.csv"
CONFUSION_PATH = ROOT / "reports/tables/phase20_confusion_matrices.csv"
CALIB_PATH = ROOT / "reports/tables/phase20_calibration_ranking.csv"
CI_PATH = ROOT / "reports/tables/phase20_domain_bootstrap_ci.csv"
KUB_SUB_PATH = ROOT / "reports/tables/phase20_kub_subgroup_analysis.csv"
KUB_SIZE_PATH = ROOT / "reports/tables/phase20_kub_size_stratification.csv"
GALLERY_SEL_PATH = ROOT / "reports/tables/phase20_gallery_selection.csv"

FIG_DIR = ROOT / "reports/figures/phase20_multidomain_baseline"
AUDIT_DIR = ROOT / "reports/audits"

#: Deterministic pixel subsample stride used for calibration / ranking metrics.
#: 512x512 with stride 4 gives 16384 pixels per image, which is ample for a
#: histogram-based ECE and keeps the computation bounded and reproducible.
CALIBRATION_STRIDE = 4
CALIBRATION_BINS = 15
BOOTSTRAP = {"n_boot": 2000, "seed": 42, "alpha": 0.05}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


# --------------------------------------------------------------------------- #
# IO
# --------------------------------------------------------------------------- #
def load_protocol() -> dict:
    return json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))


def load_closure() -> dict:
    return json.loads((EXP_DIR / "closure.json").read_text(encoding="utf-8"))


def load_history() -> pd.DataFrame:
    return pd.read_csv(EXP_DIR / "history.csv")


def load_per_image() -> pd.DataFrame:
    return pd.read_csv(PER_IMAGE_PATH)


def load_prediction_manifest() -> pd.DataFrame:
    return pd.read_csv(MANIFEST_CSV)


def load_val_manifest() -> pd.DataFrame:
    return pd.read_csv(MANIFEST_DIR / "val.csv")


def load_prediction(npz_rel_path: str) -> dict:
    """Load one persisted prediction: prob (float16), pred (uint8), gt (uint8)."""
    z = np.load(ROOT / npz_rel_path)
    return {"prob": z["prob"].astype(np.float32), "pred": z["pred"].astype(bool),
            "gt": z["gt"].astype(bool)}


# --------------------------------------------------------------------------- #
# Tables
# --------------------------------------------------------------------------- #
def domain_summary(per_image: pd.DataFrame) -> pd.DataFrame:
    """Per-domain macro metrics + MACRO_DOMAIN + POOLED_DESCRIPTIVE."""
    metrics = ["dice", "iou", "precision", "recall", "specificity",
               "balanced_accuracy", "mcc", "hd95", "assd", "surface_dice"]
    rows = []
    for d in DATASET_ORDER:
        sub = per_image[per_image["dataset"] == d]
        row = {"row_type": "DOMAIN", "dataset": d, "n": int(len(sub))}
        for m in metrics:
            row[m] = float(sub[m].mean(skipna=True)) if m in sub else float("nan")
        row["hd95_valid_n"] = int(sub["hd95_valid"].sum())
        row["surface_dice_valid_n"] = int(sub["surface_dice_valid"].sum())
        rows.append(row)

    dom = pd.DataFrame(rows)
    macro = {"row_type": "MACRO_DOMAIN", "dataset": "MACRO_DOMAIN",
             "n": int(dom["n"].sum())}
    for m in metrics:
        macro[m] = float(dom[m].mean(skipna=True))
    macro["hd95_valid_n"] = int(dom["hd95_valid_n"].sum())
    macro["surface_dice_valid_n"] = int(dom["surface_dice_valid_n"].sum())
    rows.append(macro)

    # ``pooled_segmentation_metrics`` requires an explicit ``total`` key alongside
    # tp/tn/fp/fn, so build the full count dict rather than the four raw counts.
    confusions = [
        {"tp": int(r["tp"]), "tn": int(r["tn"]), "fp": int(r["fp"]), "fn": int(r["fn"]),
         "total": int(r["tp"]) + int(r["tn"]) + int(r["fp"]) + int(r["fn"])}
        for _, r in per_image.iterrows()
    ]
    pooled = pooled_segmentation_metrics(confusions)
    prow = {"row_type": "POOLED_DESCRIPTIVE", "dataset": "POOLED_DESCRIPTIVE",
            "n": int(len(per_image))}
    for m in metrics:
        prow[m] = float(pooled.get(m, float("nan")))
    prow["hd95_valid_n"] = int(dom["hd95_valid_n"].sum())
    prow["surface_dice_valid_n"] = int(dom["surface_dice_valid_n"].sum())
    rows.append(prow)

    out = pd.DataFrame(rows)
    out["is_macro"] = out["row_type"] == "MACRO_DOMAIN"
    out["is_pooled"] = out["row_type"] == "POOLED_DESCRIPTIVE"
    out["note"] = ("MACRO_DOMAIN = unweighted mean of the four per-domain per-image macro values; "
                   "POOLED_DESCRIPTIVE = pixel-pooled counts, descriptive only and never the sole "
                   "scientific summary")
    return out


def bootstrap_domain_cis(per_image: pd.DataFrame) -> pd.DataFrame:
    """Deterministic percentile bootstrap CI for per-domain and macro Dice/IoU."""
    rows = []
    for d in DATASET_ORDER:
        sub = per_image[per_image["dataset"] == d]
        for m in ("dice", "iou"):
            ci = bootstrap_ci(sub[m].tolist(), n_boot=BOOTSTRAP["n_boot"],
                              seed=BOOTSTRAP["seed"], alpha=BOOTSTRAP["alpha"])
            rows.append({"scope": d, "metric": m, **ci})
    for m in ("dice", "iou"):
        per_domain_means = [per_image[per_image["dataset"] == d][m].mean() for d in DATASET_ORDER]
        ci = bootstrap_ci(per_domain_means, n_boot=BOOTSTRAP["n_boot"],
                          seed=BOOTSTRAP["seed"], alpha=BOOTSTRAP["alpha"],
                          resampling_unit="domain")
        rows.append({"scope": "MACRO_DOMAIN", "metric": m, **ci})
    return pd.DataFrame(rows)


def confusion_matrices(per_image: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Raw and row-normalized pixel confusion matrices per domain (+ pooled)."""
    rows, payload = [], {}
    for d in DATASET_ORDER + ["POOLED_DESCRIPTIVE"]:
        sub = per_image if d == "POOLED_DESCRIPTIVE" else per_image[per_image["dataset"] == d]
        tp, tn, fp, fn = (int(sub[k].sum()) for k in ("tp", "tn", "fp", "fn"))
        total = tp + tn + fp + fn
        gt_fg, gt_bg = tp + fn, tn + fp
        rows.append({
            "scope": d, "tp": tp, "tn": tn, "fp": fp, "fn": fn, "total": total,
            "gt_foreground": gt_fg, "gt_background": gt_bg,
            "row_norm_gt_fg_tp": tp / gt_fg if gt_fg else float("nan"),
            "row_norm_gt_fg_fn": fn / gt_fg if gt_fg else float("nan"),
            "row_norm_gt_bg_fp": fp / gt_bg if gt_bg else float("nan"),
            "row_norm_gt_bg_tn": tn / gt_bg if gt_bg else float("nan"),
        })
        payload[d] = {"raw": [[tp, fn], [fp, tn]],
                      "row_normalized": [[tp / gt_fg if gt_fg else float("nan"),
                                          fn / gt_fg if gt_fg else float("nan")],
                                         [fp / gt_bg if gt_bg else float("nan"),
                                          tn / gt_bg if gt_bg else float("nan")]],
                      "layout": "rows = GT (foreground, background); cols = PRED (foreground, background)"}
    return pd.DataFrame(rows), payload


def calibration_and_ranking(manifest: pd.DataFrame, stride: int = CALIBRATION_STRIDE,
                            n_bins: int = CALIBRATION_BINS) -> pd.DataFrame:
    """Brier / ECE / MCE / ROC-AUC / PR-AUC per domain on a deterministic pixel subsample."""
    rows = []
    for d in DATASET_ORDER:
        sub = manifest[manifest["dataset"] == d]
        probs, gts = [], []
        for _, r in sub.iterrows():
            z = load_prediction(r["npz_path"])
            p = z["prob"][::stride, ::stride].ravel()
            g = z["gt"][::stride, ::stride].ravel().astype(np.float64)
            probs.append(p)
            gts.append(g)
        p = np.concatenate(probs).astype(np.float64)
        g = np.concatenate(gts)
        rows.append({
            "dataset": d,
            "n_images": int(len(sub)),
            "n_pixels_subsampled": int(p.size),
            "subsample_stride": int(stride),
            "brier": brier_score(g, p),
            "ece": expected_calibration_error(g, p, n_bins),
            "mce": maximum_calibration_error(g, p, n_bins),
            "roc_auc": roc_auc(g, p),
            "pr_auc_average_precision": average_precision(g, p),
            "prevalence": float(g.mean()),
        })
    out = pd.DataFrame(rows)
    out.attrs["reliability"] = {
        d: reliability_bins(
            np.concatenate([load_prediction(r["npz_path"])["gt"][::stride, ::stride].ravel()
                            for _, r in manifest[manifest["dataset"] == d].iterrows()]).astype(np.float64),
            np.concatenate([load_prediction(r["npz_path"])["prob"][::stride, ::stride].ravel()
                            for _, r in manifest[manifest["dataset"] == d].iterrows()]).astype(np.float64),
            n_bins)
        for d in DATASET_ORDER}
    return out


def kub_subgroup_analysis(per_image: pd.DataFrame, val_frame: pd.DataFrame) -> pd.DataFrame:
    """KUB reporting subgroups by native category. REPORTING ONLY, never a model input."""
    kub = per_image[per_image["dataset"] == "KUB"].copy()
    cat = {r["sample_id"]: str(r.get("category", "NOT_AVAILABLE"))
           for _, r in val_frame[val_frame["dataset"] == "KUB"].iterrows()}
    kub["subgroup"] = kub["sample_id"].map(cat)
    rows = [{"scope": "KUB_ALL", "subgroup": "KUB_ALL", "n": int(len(kub)),
             "dice": float(kub["dice"].mean()), "iou": float(kub["iou"].mean()),
             "precision": float(kub["precision"].mean(skipna=True)),
             "recall": float(kub["recall"].mean(skipna=True)),
             "hd95": float(kub["hd95"].mean(skipna=True)),
             "empty_prediction_rate": float(kub["pred_empty"].mean()),
             "role": "REPORTING_ONLY"}]
    for sg in sorted(kub["subgroup"].dropna().unique()):
        s = kub[kub["subgroup"] == sg]
        rows.append({"scope": "KUB_SUBGROUP", "subgroup": sg, "n": int(len(s)),
                     "dice": float(s["dice"].mean()), "iou": float(s["iou"].mean()),
                     "precision": float(s["precision"].mean(skipna=True)),
                     "recall": float(s["recall"].mean(skipna=True)),
                     "hd95": float(s["hd95"].mean(skipna=True)),
                     "empty_prediction_rate": float(s["pred_empty"].mean()),
                     "role": "REPORTING_ONLY"})
    return pd.DataFrame(rows)


def kub_size_stratification(per_image: pd.DataFrame, val_frame: pd.DataFrame) -> pd.DataFrame:
    """Descriptive KUB performance by the FROZEN clean-v3 object-size taxonomy.

    ``component_ratio = component_pixels / (native_h * native_w)``; FULL_FIELD only,
    ROI crops are reported as ``ROI_NOT_PRIMARY_BINNED``. Reporting only.
    """
    from scipy.ndimage import label as _label
    from PIL import Image

    from src.analysis.kub_object_size import (
        classify_component_ratio,
        classify_view_type,
        get_kub_size_taxonomy,
    )

    thresholds = get_kub_size_taxonomy("kub_size_clean_v3_v1")
    kub = per_image[per_image["dataset"] == "KUB"]
    meta = {r["sample_id"]: r for _, r in val_frame.iterrows()}

    rows = []
    for _, r in kub.iterrows():
        sid = r["sample_id"]
        m = meta[sid]
        view = classify_view_type(m["image_path"])
        if view != "FULL_FIELD":
            rows.append({"sample_id": sid, "view_type": view, "stratum": "ROI_NOT_PRIMARY_BINNED",
                         "dice": r["dice"], "iou": r["iou"], "component_ratio": float("nan")})
            continue
        arr = np.asarray(Image.open(m["mask_path"]).convert("L")) > 0
        lab, n = _label(arr, structure=np.ones((3, 3), dtype=int))
        h, w = arr.shape
        if n == 0:
            rows.append({"sample_id": sid, "view_type": view, "stratum": "EMPTY_GT",
                         "dice": r["dice"], "iou": r["iou"], "component_ratio": float("nan")})
            continue
        sizes = np.bincount(lab.ravel())[1:]
        ratio = float(sizes.max()) / float(h * w)
        rows.append({"sample_id": sid, "view_type": view,
                     "stratum": classify_component_ratio(ratio, thresholds),
                     "dice": r["dice"], "iou": r["iou"], "component_ratio": ratio})
    per_sample = pd.DataFrame(rows)

    out_rows = []
    for stratum in ["TINY", "SMALL", "MEDIUM", "LARGE", "ROI_NOT_PRIMARY_BINNED", "EMPTY_GT"]:
        s = per_sample[per_sample["stratum"] == stratum]
        if not len(s):
            continue
        out_rows.append({"stratum": stratum, "n": int(len(s)),
                         "dice": float(s["dice"].mean()), "iou": float(s["iou"].mean()),
                         "median_component_ratio": float(s["component_ratio"].median(skipna=True)),
                         "taxonomy_id": "kub_size_clean_v3_v1",
                         "role": "REPORTING_ONLY__DESCRIPTIVE"})
    out = pd.DataFrame(out_rows)
    out.attrs["per_sample"] = per_sample
    out.attrs["thresholds"] = thresholds
    return out


# --------------------------------------------------------------------------- #
# Deterministic gallery selection
# --------------------------------------------------------------------------- #
def select_gallery_cases(val_frame: pd.DataFrame, per_domain: int = 16,
                         seed: int = 42) -> pd.DataFrame:
    """Deterministic, prediction-independent case selection.

    Within each domain, VAL samples are sorted by ``sample_id`` and an evenly
    spaced set of indices is taken. The rule depends only on the manifest, never
    on any model output, so the same 64 sample IDs can be reused in Phase 21.
    """
    rows = []
    for d in DATASET_ORDER:
        ids = sorted(val_frame[val_frame["dataset"] == d]["sample_id"].astype(str).tolist())
        if len(ids) <= per_domain:
            chosen = ids
        else:
            idx = np.linspace(0, len(ids) - 1, per_domain).round().astype(int)
            chosen = [ids[i] for i in idx]
        for rank, sid in enumerate(chosen):
            rows.append({"dataset": d, "rank": rank, "sample_id": sid,
                         "selection_rule": "sorted_by_sample_id_evenly_spaced",
                         "prediction_dependent": False, "seed": seed})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# Figures
# --------------------------------------------------------------------------- #
DOMAIN_COLORS = {"ISIC": "#1f77b4", "BUSI": "#ff7f0e", "KVASIR": "#2ca02c", "KUB": "#d62728"}


def _mpl():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    return plt


def build_training_figures(history: pd.DataFrame, closure: dict) -> dict:
    """All required training curves. No epoch row is omitted."""
    plt = _mpl()
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    out = {}
    ep = history["epoch"].values

    # 1. losses
    fig, ax = plt.subplots(figsize=(8.6, 4.4))
    ax.plot(ep, history["train_loss"], marker="o", ms=2.5, lw=1.2, label="train loss")
    ax.plot(ep, history["val_loss"], marker="s", ms=2.5, lw=1.2, label="val loss")
    ax.axvline(closure["best_epoch"], color="green", ls="--", lw=1.1,
               label=f"best epoch {closure['best_epoch']}")
    ax.set_xlabel("epoch"); ax.set_ylabel("BCE+Dice loss"); ax.legend(); ax.grid(alpha=0.25)
    ax.set_title("Phase-20 shared UNet++ — training / validation loss")
    p = FIG_DIR / "fig_train_val_loss.png"; fig.tight_layout(); fig.savefig(p, dpi=150); plt.close(fig)
    out["loss"] = p

    # 2. macro-domain Dice
    fig, ax = plt.subplots(figsize=(8.6, 4.4))
    ax.plot(ep, history["macro_domain_dice"], marker="o", ms=2.5, lw=1.4,
            color="#6a1b9a", label="macro-domain VAL Dice")
    ax.axhline(closure["best_macro_domain_dice"], color="green", ls="--", lw=1.1,
               label=f"best = {closure['best_macro_domain_dice']:.6f} @ epoch {closure['best_epoch']}")
    ax.set_xlabel("epoch"); ax.set_ylabel("macro-domain Dice"); ax.legend(); ax.grid(alpha=0.25)
    ax.set_title("Macro-domain mean VAL Dice (checkpoint-selection metric)")
    p = FIG_DIR / "fig_macro_domain_dice.png"; fig.tight_layout(); fig.savefig(p, dpi=150); plt.close(fig)
    out["macro_dice"] = p

    # 3. per-domain Dice
    fig, ax = plt.subplots(figsize=(9.0, 4.6))
    for d in DATASET_ORDER:
        ax.plot(ep, history[f"val_dice_{d}"], marker="o", ms=2.2, lw=1.2,
                color=DOMAIN_COLORS[d], label=d)
    ax.axvline(closure["best_epoch"], color="green", ls="--", lw=1.0)
    ax.set_xlabel("epoch"); ax.set_ylabel("VAL Dice"); ax.legend(ncol=2); ax.grid(alpha=0.25)
    ax.set_title("Per-domain VAL Dice")
    p = FIG_DIR / "fig_per_domain_dice.png"; fig.tight_layout(); fig.savefig(p, dpi=150); plt.close(fig)
    out["per_domain_dice"] = p

    # 4. per-domain IoU
    fig, ax = plt.subplots(figsize=(9.0, 4.6))
    for d in DATASET_ORDER:
        ax.plot(ep, history[f"val_iou_{d}"], marker="o", ms=2.2, lw=1.2,
                color=DOMAIN_COLORS[d], label=d)
    ax.set_xlabel("epoch"); ax.set_ylabel("VAL IoU"); ax.legend(ncol=2); ax.grid(alpha=0.25)
    ax.set_title("Per-domain VAL IoU")
    p = FIG_DIR / "fig_per_domain_iou.png"; fig.tight_layout(); fig.savefig(p, dpi=150); plt.close(fig)
    out["per_domain_iou"] = p

    # 5. learning rate
    fig, ax = plt.subplots(figsize=(8.6, 3.8))
    ax.plot(ep, history["learning_rate"], marker="o", ms=2.2, lw=1.2, color="#b8860b")
    ax.set_xlabel("epoch"); ax.set_ylabel("learning rate"); ax.grid(alpha=0.25)
    ax.set_title("CosineAnnealingLR schedule (stepped per epoch after train+val)")
    p = FIG_DIR / "fig_learning_rate.png"; fig.tight_layout(); fig.savefig(p, dpi=150); plt.close(fig)
    out["lr"] = p

    # 6. early-stopping counter
    fig, ax = plt.subplots(figsize=(8.6, 3.8))
    ax.plot(ep, history["bad_epochs"], marker="o", ms=2.2, lw=1.2, color="#c0392b")
    ax.axhline(closure["early_stopping_patience"], color="black", ls=":", lw=1.1,
               label=f"patience = {closure['early_stopping_patience']}")
    ax.set_xlabel("epoch"); ax.set_ylabel("consecutive bad epochs"); ax.legend(); ax.grid(alpha=0.25)
    ax.set_title("Early-stopping counter")
    p = FIG_DIR / "fig_early_stopping.png"; fig.tight_layout(); fig.savefig(p, dpi=150); plt.close(fig)
    out["early_stopping"] = p

    # 7. epoch duration
    fig, ax = plt.subplots(figsize=(8.6, 3.8))
    ax.bar(ep, history["epoch_seconds"], color="#4682b4")
    ax.axhline(float(history["epoch_seconds"].mean()), color="black", ls="--", lw=1.0,
               label=f"mean = {history['epoch_seconds'].mean():.0f} s")
    ax.set_xlabel("epoch"); ax.set_ylabel("seconds"); ax.legend(); ax.grid(alpha=0.25, axis="y")
    ax.set_title("Epoch wall-clock duration")
    p = FIG_DIR / "fig_epoch_seconds.png"; fig.tight_layout(); fig.savefig(p, dpi=150); plt.close(fig)
    out["epoch_seconds"] = p

    # 8. best-checkpoint progression
    fig, ax = plt.subplots(figsize=(8.6, 4.2))
    best_so_far = history["macro_domain_dice"].cummax()
    ax.step(ep, best_so_far, where="post", lw=1.6, color="#00695c", label="best macro Dice so far")
    improved = history[history["is_new_best"]]
    ax.scatter(improved["epoch"], improved["macro_domain_dice"], s=22, color="#e65100",
               zorder=3, label=f"improvement events (n={len(improved)})")
    ax.set_xlabel("epoch"); ax.set_ylabel("macro-domain Dice"); ax.legend(); ax.grid(alpha=0.25)
    ax.set_title("Best-checkpoint progression")
    p = FIG_DIR / "fig_best_progression.png"; fig.tight_layout(); fig.savefig(p, dpi=150); plt.close(fig)
    out["best_progression"] = p

    return out


def build_result_figures(domain_table: pd.DataFrame, conf: dict,
                         calib: pd.DataFrame) -> dict:
    """Domain summary bars, confusion heatmaps, calibration reliability."""
    plt = _mpl()
    import numpy as np
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    out = {}
    dom = domain_table[domain_table["row_type"] == "DOMAIN"]

    # 1. domain summary grouped bars
    metrics = ["dice", "iou", "precision", "recall", "specificity", "mcc"]
    fig, ax = plt.subplots(figsize=(10.2, 4.6))
    x = np.arange(len(metrics)); w = 0.2
    for i, d in enumerate(DATASET_ORDER):
        row = dom[dom["dataset"] == d].iloc[0]
        ax.bar(x + (i - 1.5) * w, [row[m] for m in metrics], w,
               label=d, color=DOMAIN_COLORS[d])
    macro = domain_table[domain_table["row_type"] == "MACRO_DOMAIN"].iloc[0]
    ax.plot(x, [macro[m] for m in metrics], "k_", ms=26, mew=2.4, label="MACRO_DOMAIN")
    ax.set_xticks(x); ax.set_xticklabels(metrics, rotation=12)
    ax.set_ylabel("value"); ax.legend(ncol=5, fontsize=8); ax.grid(alpha=0.25, axis="y")
    ax.set_title("Phase-20 shared UNet++ — per-domain VAL metrics (macro over images)")
    p = FIG_DIR / "fig_domain_summary_bars.png"; fig.tight_layout(); fig.savefig(p, dpi=150); plt.close(fig)
    out["domain_bars"] = p

    # 2. confusion heatmaps (row-normalized) per domain
    fig, axes = plt.subplots(1, 5, figsize=(17.5, 3.9))
    for ax, scope in zip(axes, DATASET_ORDER + ["POOLED_DESCRIPTIVE"]):
        m = np.array(conf[scope]["row_normalized"], dtype=float)
        im = ax.imshow(m, cmap="Blues", vmin=0, vmax=1)
        for i in range(2):
            for j in range(2):
                ax.text(j, i, f"{m[i, j]:.3f}", ha="center", va="center",
                        color="white" if m[i, j] > 0.55 else "black", fontsize=9)
        ax.set_xticks([0, 1]); ax.set_xticklabels(["pred FG", "pred BG"], fontsize=8)
        ax.set_yticks([0, 1]); ax.set_yticklabels(["GT FG", "GT BG"], fontsize=8)
        ax.set_title(scope, fontsize=9)
    fig.suptitle("Row-normalized pixel confusion matrices (rows = GT, cols = prediction)", fontsize=11)
    p = FIG_DIR / "fig_confusion_row_normalized.png"
    fig.tight_layout(rect=(0, 0, 1, 0.93)); fig.savefig(p, dpi=150); plt.close(fig)
    out["confusion"] = p

    # 3. calibration reliability
    rel = calib.attrs.get("reliability") if hasattr(calib, "attrs") else None
    if rel:
        fig, ax = plt.subplots(figsize=(7.4, 5.4))
        ax.plot([0, 1], [0, 1], "k--", lw=1.0, label="perfect calibration")
        for d in DATASET_ORDER:
            r = rel[d]
            conf_v = np.array(r["bin_confidence"], dtype=float)
            acc_v = np.array(r["bin_accuracy"], dtype=float)
            ok = ~np.isnan(conf_v) & ~np.isnan(acc_v)
            ax.plot(conf_v[ok], acc_v[ok], marker="o", ms=3.5, lw=1.2,
                    color=DOMAIN_COLORS[d], label=d)
        ax.set_xlabel("mean predicted probability"); ax.set_ylabel("empirical foreground rate")
        ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.legend(); ax.grid(alpha=0.25)
        ax.set_title("Reliability diagram (deterministic pixel subsample, stride "
                     f"{CALIBRATION_STRIDE}, {CALIBRATION_BINS} bins)")
        p = FIG_DIR / "fig_calibration_reliability.png"
        fig.tight_layout(); fig.savefig(p, dpi=150); plt.close(fig)
        out["calibration"] = p

    # 4. boundary metrics per domain
    fig, axes = plt.subplots(1, 3, figsize=(14.2, 4.2))
    for ax, metric in zip(axes, ["hd95", "assd", "surface_dice"]):
        vals, labels = [], []
        for d in DATASET_ORDER:
            sub = dom[dom["dataset"] == d].iloc[0]
            vals.append(sub[metric]); labels.append(d)
        ax.bar(labels, vals, color=[DOMAIN_COLORS[d] for d in labels])
        ax.set_title(metric.upper() if metric != "surface_dice" else "Surface Dice")
        ax.grid(alpha=0.25, axis="y")
        if metric != "surface_dice":
            ax.set_ylabel("pixels")
    fig.suptitle("Boundary metrics per domain (mean over VAL images where valid)", fontsize=11)
    p = FIG_DIR / "fig_boundary_metrics.png"
    fig.tight_layout(rect=(0, 0, 1, 0.93)); fig.savefig(p, dpi=150); plt.close(fig)
    out["boundary"] = p

    return out
