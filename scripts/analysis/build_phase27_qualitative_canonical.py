"""Phase27 CANONICAL VISUAL REBUILD — Step 2: rebuild the reviewer qualitative figure
from FROZEN REVIEWER ARTIFACTS ONLY.

Classification: PHASE27_REVIEWER_VISUAL_CANONICAL_REBUILD__FROZEN_REVIEWER_ARTIFACTS_ONLY

Inputs (all frozen reviewer artifacts):
  * reports/figures/phase27_preservation/masks/<sid>_global.png   (frozen 512x512)
  * reports/figures/phase27_preservation/masks/<sid>_final.png    (frozen 512x512)
  * reports/figures/phase27_preservation/frozen_reviewer_panels/<sid>_rgb.png  (frozen extract)
  * reports/figures/phase27_preservation/frozen_reviewer_panels/<sid>_gt.png   (frozen extract)
  * reports/tables/phase27_qualitative_gallery_selection.csv      (frozen selection)

HARD BOUNDARIES:
  * NO raw VAL808 RGB reads           (raw_VAL808_RGB_reads = 0)
  * NO raw VAL808 GT reads            (raw_VAL808_GT_reads  = 0)
  * NO VAL808 dataset loader access
  * NO model execution                (model_forwards = 0)
  * NO metric recomputation, NO bootstrap, NO training

Layout retained (unchanged design): 2x2 domain groups BUSI|ISIC / KUB|KVASIR,
each domain = 4 samples x 5 columns [RGB | Global | Final A8 | GT | TP/FN/FP],
nearest interpolation, equal aspect, TP green / FN blue / FP red, compact legend.

SOURCE_LIMITATION = RELAYOUT_FROM_FROZEN_REVIEWER_RASTER
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from PIL import Image

ROOT = Path(r"D:/Softfors/jup")
FIG = ROOT / "reports" / "figures" / "phase27_preservation"
MASK = FIG / "masks"
PANELS = FIG / "frozen_reviewer_panels"
AUD = ROOT / "reports" / "audits"
CANVAS = 512
DOMAINS = ["BUSI", "ISIC", "KUB", "KVASIR"]

plt.rcParams.update({
    "figure.dpi": 250,
    "savefig.dpi": 250,
    "font.family": "DejaVu Sans",
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.15,
})


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def load_selection():
    rows = []
    with open(ROOT / "reports" / "tables" / "phase27_qualitative_gallery_selection.csv",
              newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append((r["domain"], r["sample_id"]))
    return rows


def load_mask_png(sid, which):
    p = MASK / f"{sid}_{which}.png"
    img = Image.open(p).convert("L")
    return (np.asarray(img) > 127)


def load_frozen_panel(sid, kind):
    """RGB or GT frozen reviewer raster panel (already 313x313)."""
    p = PANELS / f"{sid}_{kind}.png"
    img = Image.open(p).convert("RGB")
    return np.asarray(img, dtype=np.float32)


def gt_to_binary(gt_rgb):
    """GT panel is stored as a grayscale mask rendered in RGB; reduce to binary."""
    g = gt_rgb.mean(axis=2)
    return (g > 127)


def build_overlay(final_mask, gt_mask):
    tp = final_mask & gt_mask
    fn = (~final_mask) & gt_mask
    fpn = final_mask & (~gt_mask)
    overlay = np.zeros((CANVAS, CANVAS, 3), dtype=np.float32)
    overlay[..., 0] = fpn  # red = FP
    overlay[..., 1] = tp   # green = TP
    overlay[..., 2] = fn   # blue = FN
    return overlay


def resize_panel(arr, is_binary=False, size=CANVAS):
    """Resize a frozen panel into the fixed square canvas, nearest interpolation."""
    img = Image.fromarray(arr.astype(np.uint8))
    w, h = img.size
    scale = min(size / w, size / h)
    rw, rh = max(1, round(w * scale)), max(1, round(h * scale))
    resample = Image.Resampling.NEAREST
    img = img.resize((rw, rh), resample)
    canvas = Image.new("RGB", (size, size), (255, 255, 255))
    canvas.paste(img, ((size - rw) // 2, (size - rh) // 2))
    return np.asarray(canvas, dtype=np.float32)


def render_domain_block(ax_grid, domain, sample_ids):
    for r, sid in enumerate(sample_ids):
        rgb = resize_panel(load_frozen_panel(sid, "rgb"))                 # frozen reviewer raster
        gt_panel = load_frozen_panel(sid, "gt")
        gt = resize_panel((gt_to_binary(gt_panel).astype(np.uint8) * 255))  # frozen reviewer raster
        gt_bin = gt_to_binary(gt_panel)
        # resize binary mask to canvas for overlay math
        gt_canvas_bin = resize_panel((gt_bin.astype(np.uint8) * 255))[:, :, 0] > 127

        g_bin = load_mask_png(sid, "global")   # frozen 512 mask
        f_bin = load_mask_png(sid, "final")    # frozen 512 mask
        if g_bin.shape != (CANVAS, CANVAS):
            g_bin = np.asarray(Image.fromarray((g_bin * 255).astype(np.uint8)).resize(
                (CANVAS, CANVAS), Image.Resampling.NEAREST)) > 127
        if f_bin.shape != (CANVAS, CANVAS):
            f_bin = np.asarray(Image.fromarray((f_bin * 255).astype(np.uint8)).resize(
                (CANVAS, CANVAS), Image.Resampling.NEAREST)) > 127

        overlay = build_overlay(f_bin, gt_canvas_bin)

        panels = [
            (rgb.astype(np.uint8), None, "RGB"),
            (g_bin.astype(np.float32), "gray", "Global"),
            (f_bin.astype(np.float32), "gray", "Final A8"),
            (gt_canvas_bin.astype(np.float32), "gray", "GT"),
            (overlay.astype(np.float32), None, "TP/FN/FP"),
        ]
        for c, (panel, cmap, label) in enumerate(panels):
            ax = ax_grid[r, c]
            if cmap is None:
                ax.imshow(panel, interpolation="nearest")
            else:
                ax.imshow(panel, cmap="gray", vmin=0, vmax=1, interpolation="nearest")
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_aspect("equal")
            if r == 0:
                ax.set_title(label, fontsize=11, pad=6)
            if c == 0:
                ax.set_ylabel(f"{domain}\n{sid[:10]}", fontsize=9, rotation=0,
                              labelpad=28, va="center")


def main() -> int:
    sel = load_selection()
    assert len(sel) == 16
    per_domain = {}
    for d, sid in sel:
        per_domain.setdefault(d, []).append(sid)
    for d in DOMAINS:
        assert len(per_domain[d]) == 4

    fig = plt.figure(figsize=(20, 13))
    fig.suptitle(
        "Qualitative Panels (VAL808): RGB | Global | Final A8 | GT | TP/FN/FP",
        fontsize=18, y=0.98, ha="center",
    )
    outer = fig.add_gridspec(2, 2, wspace=0.10, hspace=0.18,
                             left=0.04, right=0.96, top=0.93, bottom=0.06)
    for idx, d in enumerate(DOMAINS):
        row, col = idx // 2, idx % 2
        inner = outer[row, col].subgridspec(4, 5, wspace=0.04, hspace=0.06)
        ax_grid = np.array([[fig.add_subplot(inner[r, c]) for c in range(5)] for r in range(4)])
        render_domain_block(ax_grid, d, per_domain[d])

    legend_elements = [
        mpatches.Patch(facecolor="green", edgecolor="black", linewidth=0.5, label="TP"),
        mpatches.Patch(facecolor="blue", edgecolor="black", linewidth=0.5, label="FN"),
        mpatches.Patch(facecolor="red", edgecolor="black", linewidth=0.5, label="FP"),
    ]
    fig.legend(handles=legend_elements, loc="lower center", ncol=3,
               fontsize=11, frameon=True, fancybox=False, edgecolor="black",
               bbox_to_anchor=(0.5, 0.01))

    out_png = FIG / "p27_qualitative_panels.png"
    out_pdf = FIG / "p27_qualitative_panels.pdf"
    fig.savefig(out_png, dpi=250, facecolor="white", pad_inches=0.2)
    fig.savefig(out_pdf, dpi=250, facecolor="white", pad_inches=0.2)
    plt.close(fig)

    print("wrote", out_png.relative_to(ROOT), "|", out_pdf.relative_to(ROOT))
    print("cases:", sum(len(v) for v in per_domain.values()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
