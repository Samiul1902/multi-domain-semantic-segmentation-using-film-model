"""Phase-20 deterministic 64-case detailed prediction gallery + success/failure views.

Selection is deterministic and PREDICTION-INDEPENDENT (see
``phase20_baseline.select_gallery_cases``): within each domain, VAL samples are
sorted by ``sample_id`` and evenly spaced, 16 per domain, 64 total. The same 64
sample IDs are intended for reuse in Phase 21 so the two models can be compared
on identical cases.

Panels per case (3x3):
    A native image            B GT mask                 C GT contour on image
    D model input (512)       E probability map         F thresholded prediction
    G TP/FP/FN error map      H prediction overlay      I GT-vs-pred contour overlay

Cases are paginated 4 per page (16 pages) so no panel becomes unreadable.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch
from PIL import Image
from scipy.ndimage import binary_erosion

from src.analysis.phase20_baseline import (
    DATASET_ORDER,
    FIG_DIR,
    GALLERY_SEL_PATH,
    load_prediction,
    load_val_manifest,
    select_gallery_cases,
)

CASES_PER_PAGE = 4
PANEL_TITLES = ["A native image", "B GT mask", "C GT contour",
                "D model input", "E probability", "F prediction",
                "G TP/FP/FN", "H pred overlay", "I contour overlay"]


def _contour(mask: np.ndarray) -> np.ndarray:
    m = np.asarray(mask, dtype=bool)
    if not m.any():
        return m
    return m ^ binary_erosion(m, structure=np.ones((3, 3), dtype=bool), border_value=0)


def _overlay_contours(ax, base, gt, pred, title=None):
    ax.imshow(base, cmap="gray" if base.ndim == 2 else None)
    gc, pc = _contour(gt), _contour(pred)
    if gc.any():
        ax.contour(gc, levels=[0.5], colors=["#00d26a"], linewidths=1.1)
    if pc.any():
        ax.contour(pc, levels=[0.5], colors=["#ff2d55"], linewidths=1.1)
    ax.set_xticks([]); ax.set_yticks([])
    if title:
        ax.set_title(title, fontsize=8)


def build_gallery(per_image: pd.DataFrame, per_domain: int = 16,
                  cases_per_page: int = CASES_PER_PAGE) -> dict:
    """Render the paginated 64-case gallery. Returns paths + metadata."""
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    val_frame = load_val_manifest()
    sel = select_gallery_cases(val_frame, per_domain=per_domain)
    sel.to_csv(GALLERY_SEL_PATH, index=False)

    meta = {r["sample_id"]: r for _, r in val_frame.iterrows()}
    metrics = {r["sample_id"]: r for _, r in per_image.iterrows()}
    man = pd.read_csv(
        Path(__file__).resolve().parent.parent.parent
        / "reports/tables/phase20_prediction_manifest.csv")
    npz_of = {r["sample_id"]: r["npz_path"] for _, r in man.iterrows()}

    pages, per_case = [], []
    for _, s in sel.iterrows():
        sid = s["sample_id"]
        z = load_prediction(npz_of[sid])
        prob, pred, gt = z["prob"], z["pred"], z["gt"]
        m = metrics[sid]
        per_case.append({
            "dataset": s["dataset"], "rank": int(s["rank"]), "sample_id": sid,
            "dice": float(m["dice"]), "iou": float(m["iou"]),
            "precision": float(m["precision"]) if pd.notna(m["precision"]) else float("nan"),
            "recall": float(m["recall"]) if pd.notna(m["recall"]) else float("nan"),
            "gt_empty": bool(m["gt_empty"]), "pred_empty": bool(m["pred_empty"]),
            "tp": int(m["tp"]), "fp": int(m["fp"]), "fn": int(m["fn"]),
        })

        native_img = np.asarray(Image.open(meta[sid]["image_path"]).convert("RGB"))
        native_gt = np.asarray(Image.open(meta[sid]["mask_path"]).convert("L")) > 0

        fig, axes = plt.subplots(3, 3, figsize=(7.2, 7.6))
        fig.suptitle(
            f"{s['dataset']} | rank {int(s['rank']):02d} | {sid[:12]}… | "
            f"Dice={m['dice']:.4f} IoU={m['iou']:.4f} "
            f"P={m['precision'] if pd.notna(m['precision']) else float('nan'):.4f} "
            f"R={m['recall'] if pd.notna(m['recall']) else float('nan'):.4f}",
            fontsize=8.5)

        axes[0, 0].imshow(native_img); axes[0, 0].set_title(PANEL_TITLES[0], fontsize=8)
        axes[0, 0].set_xticks([]); axes[0, 0].set_yticks([])

        axes[0, 1].imshow(native_gt, cmap="gray"); axes[0, 1].set_title(PANEL_TITLES[1], fontsize=8)
        axes[0, 1].set_xticks([]); axes[0, 1].set_yticks([])

        _overlay_contours(axes[0, 2], native_img, native_gt, np.zeros_like(native_gt),
                          PANEL_TITLES[2])

        inp = prob * 0 + np.asarray(Image.open(meta[sid]["image_path"]).convert("L").resize(
            (prob.shape[1], prob.shape[0])))[None]
        # Panel D must show the ACTUAL model input. The VAL transform is deterministic
        # (train=False), so replaying it reproduces the exact tensor the model consumed.
        from src.data.transforms import SegmentationTransform
        _t = SegmentationTransform(size=prob.shape[0], train=False, image_mode="RGB")
        _img_t, _mask_t, _ = _t(Image.open(meta[sid]["image_path"]).convert("RGB"),
                                Image.open(meta[sid]["mask_path"]))
        inp = _img_t.numpy()[:3]
        axes[1, 0].imshow(np.transpose(inp, (1, 2, 0)))
        axes[1, 0].set_title(PANEL_TITLES[3], fontsize=8)
        axes[1, 0].set_xticks([]); axes[1, 0].set_yticks([])

        im = axes[1, 1].imshow(prob, cmap="magma", vmin=0, vmax=1)
        axes[1, 1].set_title(PANEL_TITLES[4], fontsize=8)
        axes[1, 1].set_xticks([]); axes[1, 1].set_yticks([])
        plt.colorbar(im, ax=axes[1, 1], fraction=0.046, pad=0.02)

        axes[1, 2].imshow(pred, cmap="gray"); axes[1, 2].set_title(PANEL_TITLES[5], fontsize=8)
        axes[1, 2].set_xticks([]); axes[1, 2].set_yticks([])

        err = np.zeros((*gt.shape, 3), dtype=np.float32)
        err[gt & pred] = [0.0, 0.85, 0.35]     # TP green
        err[~gt & pred] = [1.0, 0.15, 0.15]    # FP red
        err[gt & ~pred] = [0.15, 0.45, 1.0]    # FN blue
        axes[2, 0].imshow(err); axes[2, 0].set_title(PANEL_TITLES[6], fontsize=8)
        axes[2, 0].set_xticks([]); axes[2, 0].set_yticks([])
        axes[2, 0].legend(handles=[Patch(color="#00d95a", label="TP"),
                                   Patch(color="#ff2626", label="FP"),
                                   Patch(color="#2673ff", label="FN")],
                          fontsize=5.5, loc="lower right", framealpha=0.75)

        base = np.asarray(Image.open(meta[sid]["image_path"]).convert("L").resize(
            (prob.shape[1], prob.shape[0])))
        _overlay_contours(axes[2, 1], base, np.zeros_like(gt), pred, PANEL_TITLES[7])
        _overlay_contours(axes[2, 2], base, gt, pred, PANEL_TITLES[8])

        fig.tight_layout(rect=(0, 0, 1, 0.97))
        pages.append(fig)

    # ---- paginate ---------------------------------------------------------
    paths = []
    n_pages = int(np.ceil(len(pages) / cases_per_page))
    for pi in range(n_pages):
        chunk = pages[pi * cases_per_page:(pi + 1) * cases_per_page]
        big = plt.figure(figsize=(7.4 * len(chunk), 8.0))
        for ci, f in enumerate(chunk):
            ax = big.add_axes([ci / len(chunk), 0.0, 1.0 / len(chunk), 1.0])
            ax.axis("off")
            f.canvas.draw()
            img = np.asarray(f.canvas.buffer_rgba())
            ax.imshow(img)
            ax.set_xticks([]); ax.set_yticks([])
        big.suptitle(f"Phase-20 detailed prediction gallery — page {pi+1}/{n_pages} "
                     f"(deterministic, prediction-independent selection)", fontsize=10)
        out = FIG_DIR / f"gallery_page_{pi+1:02d}.png"
        big.savefig(out, dpi=96, bbox_inches="tight")
        plt.close(big)
        for f in chunk:
            plt.close(f)
        paths.append(out)

    return {"n_cases": len(per_case), "n_pages": n_pages, "page_paths": paths,
            "selection": sel, "per_case": pd.DataFrame(per_case)}


def build_success_failure_figures(per_image: pd.DataFrame, per_domain: int = 16) -> dict:
    """Dice distribution, low-performing cases, FP/FN-dominant cases, empty predictions."""
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    out = {}

    # 1. Dice distribution by domain (box + strip)
    fig, ax = plt.subplots(figsize=(8.5, 4.4))
    data = [per_image[per_image["dataset"] == d]["dice"].values for d in DATASET_ORDER]
    # NOTE: matplotlib >= 3.9 renamed ``boxplot(labels=...)`` to ``tick_labels``;
    # this environment runs matplotlib 3.11, where ``labels`` raises TypeError.
    bp = ax.boxplot(data, tick_labels=DATASET_ORDER, showfliers=True, patch_artist=True)
    for patch in bp["boxes"]:
        patch.set_facecolor("#cfe3ff"); patch.set_edgecolor("#2b5c9b")
    for i, vals in enumerate(data, start=1):
        x = np.random.default_rng(42).normal(i, 0.055, size=len(vals))
        ax.scatter(x, vals, s=6, alpha=0.45, color="#1f4e79")
    ax.set_ylabel("per-image Dice"); ax.set_ylim(-0.02, 1.02)
    ax.set_title("VAL Dice distribution by domain (all 808 VAL samples)")
    ax.grid(alpha=0.25, axis="y")
    p = FIG_DIR / "fig_dice_distribution_by_domain.png"
    fig.tight_layout(); fig.savefig(p, dpi=150); plt.close(fig); out["dice_distribution"] = p

    # 2. Low-performing cases
    low = per_image.nsmallest(24, "dice")[["dataset", "sample_id", "dice", "iou",
                                           "gt_empty", "pred_empty", "fp", "fn"]]
    fig, ax = plt.subplots(figsize=(9.2, 5.2))
    colors = {"ISIC": "#1f77b4", "BUSI": "#ff7f0e", "KVASIR": "#2ca02c", "KUB": "#d62728"}
    ax.barh(range(len(low)), low["dice"].values,
            color=[colors[d] for d in low["dataset"]])
    ax.set_yticks(range(len(low)))
    ax.set_yticklabels([f"{d} {s[:10]}" for d, s in zip(low["dataset"], low["sample_id"])],
                       fontsize=6.5)
    ax.invert_yaxis(); ax.set_xlabel("Dice"); ax.set_xlim(0, 1)
    ax.set_title("24 lowest-Dice VAL cases (descriptive; checkpoint unchanged)")
    ax.grid(alpha=0.25, axis="x")
    p = FIG_DIR / "fig_low_performing_cases.png"
    fig.tight_layout(); fig.savefig(p, dpi=150); plt.close(fig); out["low_performing"] = p

    # 3. FP-dominant vs FN-dominant
    pi = per_image.copy()
    pi["fp_ratio"] = pi["fp"] / (pi["fp"] + pi["fn"]).replace(0, np.nan)
    fpd = pi.dropna(subset=["fp_ratio"]).nlargest(20, "fp_ratio")
    fnd = pi.dropna(subset=["fp_ratio"]).nsmallest(20, "fp_ratio")
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.8))
    for ax, sub, name in ((axes[0], fpd, "FP-dominant (over-segmentation)"),
                          (axes[1], fnd, "FN-dominant (under-segmentation)")):
        cnt = sub.groupby("dataset").size().reindex(DATASET_ORDER).fillna(0)
        ax.bar(cnt.index, cnt.values, color=[colors[d] for d in cnt.index])
        ax.set_title(f"{name}: top-20 by FP/(FP+FN)", fontsize=9)
        ax.set_ylabel("cases"); ax.grid(alpha=0.25, axis="y")
    p = FIG_DIR / "fig_fp_fn_dominant.png"
    fig.tight_layout(); fig.savefig(p, dpi=150); plt.close(fig); out["fp_fn_dominant"] = p

    # 4. Empty predictions / empty GT
    fig, ax = plt.subplots(figsize=(7.6, 4.2))
    emp = per_image.groupby("dataset")[["gt_empty", "pred_empty"]].sum().reindex(DATASET_ORDER)
    x = np.arange(len(DATASET_ORDER)); w = 0.38
    ax.bar(x - w / 2, emp["gt_empty"], w, label="empty GT", color="#8e44ad")
    ax.bar(x + w / 2, emp["pred_empty"], w, label="empty prediction", color="#e67e22")
    ax.set_xticks(x); ax.set_xticklabels(DATASET_ORDER)
    ax.set_ylabel("count"); ax.legend()
    ax.set_title("Empty-GT and empty-prediction counts per domain (VAL)")
    ax.grid(alpha=0.25, axis="y")
    p = FIG_DIR / "fig_empty_cases.png"
    fig.tight_layout(); fig.savefig(p, dpi=150); plt.close(fig); out["empty_cases"] = p

    return out
