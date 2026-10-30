"""Phase27 VISUAL-CLARITY REPAIR — deterministic QUALITATIVE gallery (REVIEWER-ONLY).

Classification: PHASE27_REVIEWER_VISUAL_CLARITY_REPAIR_ONLY
science_changed = false | predictions_changed = false | metrics_changed = false
bootstrap_changed = false | sample_selection_changed = false | GT_changed = false
model_forward_passes = 0 | training_runs = 0

Rebuilds the qualitative panel figure with a REVIEWER-READABLE 2×2 group layout.
Uses frozen reviewer artifacts (512×512 mask PNGs, prob f16 npy) for prediction columns.
Re-reads raw VAL808 images and GT masks SOLELY for RGB and GT columns — these reads are
for visualization only and do NOT alter the scientific freeze.

Selection rule (unchanged, outcome-independent):
    per domain: sort sample_ids ascending, take 4 at evenly spaced positions
    -> 4 domains x 4 samples = 16 cases

Panels per case (left -> right):
    RGB (512 canvas) | global predicted mask | final-A8 predicted mask |
    GT mask | TP/FN/FP overlay (final-A8 vs GT)

Layout: 2×2 SAMPLE-BLOCK GROUPS
    Group 1 (top-left):  BUSI + ISIC
    Group 2 (top-right): KUB + KVASIR
    Each group = 4 domain-rows × 5 columns

Writes:
    reports/figures/phase27_preservation/p27_qualitative_panels.png
    reports/figures/phase27_preservation/p27_qualitative_panels.pdf
    reports/figures/phase27_preservation/p27_qualitative_panels_2x.png
    reports/tables/phase27_qualitative_gallery_selection.csv

Usage:
    D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/build_phase27_qualitative.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import phase27_exec_common as E  # noqa: E402
import phase27_spec_common as S  # noqa: E402

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.patches as mpatches  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from PIL import Image, ImageOps  # noqa: E402

ROOT = Path(r"D:/Softfors/jup")
FIG = ROOT / "reports" / "figures" / "phase27_preservation"
TAB = ROOT / "reports" / "tables"
CANVAS = 512
STRATA = ["BUSI", "ISIC", "KUB", "KVASIR"]

plt.rcParams.update({
    "figure.dpi": 250,
    "savefig.dpi": 250,
    "font.family": "DejaVu Sans",
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.15,
})


def image_only_transform(image, size=CANVAS):
    image = image.convert("RGB")
    w, h = image.size
    scale = min(size / w, size / h)
    rw, rh = max(1, round(w * scale)), max(1, round(h * scale))
    image = image.resize((rw, rh), Image.Resampling.BILINEAR)
    left, top = (size - rw) // 2, (size - rh) // 2
    image = ImageOps.expand(image, (left, top, size - rw - left, size - rh - top))
    return np.asarray(image, dtype=np.float32)


def full_field_gt(mask_path, size=CANVAS):
    img = Image.open(mask_path).convert("L")
    w, h = img.size
    scale = min(size / w, size / h)
    rw, rh = max(1, round(w * scale)), max(1, round(h * scale))
    img = img.resize((rw, rh), Image.Resampling.NEAREST)
    left, top = (size - rw) // 2, (size - rh) // 2
    img = ImageOps.expand(img, (left, top, size - rw - left, size - rh - top))
    return (np.asarray(img) > 0)


def load_mask_png(sid, which):
    """Load frozen 512×512 mask PNG (global or final)."""
    p = FIG / "masks" / f"{sid}_{which}.png"
    img = Image.open(p).convert("L")
    arr = np.asarray(img)
    # These are saved as 0/255 binary masks
    return (arr > 127)


def build_overlay(final_mask, gt_mask):
    """TP/FN/FP overlay. Colors: TP=green, FN=blue, FP=red."""
    tp = final_mask & gt_mask
    fn = (~final_mask) & gt_mask
    fpn = final_mask & (~gt_mask)
    overlay = np.zeros((CANVAS, CANVAS, 3), dtype=np.float32)
    overlay[..., 0] = fpn  # red = FP
    overlay[..., 1] = tp   # green = TP
    overlay[..., 2] = fn   # blue = FN
    return overlay


def render_domain_block(ax_grid, domain, sample_ids, sid_to_row, pos, gp, fp):
    """Render one domain = 4 samples × 5 columns into ax_grid (4 rows × 5 cols)."""
    for r, sid in enumerate(sample_ids):
        gi = pos[sid]
        row = sid_to_row[sid]

        # RGB: re-read raw image (viz-only, documented)
        rgb = image_only_transform(Image.open(row["image_path"]))
        # GT: re-read raw mask (viz-only, documented)
        gt = full_field_gt(row["mask_path"])
        # Global / Final: from frozen mask PNGs
        g_bin = load_mask_png(sid, "global")
        f_bin = load_mask_png(sid, "final")

        overlay = build_overlay(f_bin, gt)

        panels = [
            (rgb.astype(np.uint8), None, "RGB"),
            (g_bin.astype(np.float32), "gray", "Global"),
            (f_bin.astype(np.float32), "gray", "Final A8"),
            (gt.astype(np.float32), "gray", "GT"),
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
            # Column headers on first row of domain block
            if r == 0:
                ax.set_title(label, fontsize=11, pad=6)
            # Domain + sample ID label on first column
            if c == 0:
                ax.set_ylabel(f"{domain}\n{sid[:10]}", fontsize=9, rotation=0,
                              labelpad=28, va="center")


def main() -> int:
    rows = S.val808_rows()
    df = pd.DataFrame(rows).sort_values(["dataset", "sample_id"]).reset_index(drop=True)
    sid_to_row = {str(r["sample_id"]): r for _, r in df.iterrows()}

    gp = np.load(E.CACHE27 / "phase27_val808_global_prob_f16.npy")
    fp = np.load(E.CACHE27 / "phase27_val808_final_prob_f16.npy")
    pos = {str(s): i for i, s in enumerate(df["sample_id"].astype(str))}

    # ---- fixed selection (outcome-independent, UNCHANGED) ---------------------- #
    sel_rows = []
    picks = {}
    for d in STRATA:
        ids = sorted(df.loc[df.dataset == d, "sample_id"].astype(str).tolist())
        k = 4
        pick = [ids[round(i * (len(ids) - 1) / (k - 1))] for i in range(k)]
        picks[d] = pick
        for s in pick:
            sel_rows.append({"domain": d, "sample_id": s})
    E.write_csv(TAB / "phase27_qualitative_gallery_selection.csv", sel_rows,
                ["domain", "sample_id"])

    # ---- 2×2 group layout ------------------------------------------------------ #
    # Each group = 2 domains × 4 samples = 8 rows; 5 columns per sample
    # We use nested grids: outer 2×2, inner each domain = 4×5
    fig = plt.figure(figsize=(20, 13))
    fig.suptitle(
        "Qualitative Panels (VAL808): RGB | Global | Final A8 | GT | TP/FN/FP",
        fontsize=18, y=0.98, ha="center",
    )

    # Outer grid: 2 rows × 2 cols of subfigure groups
    outer = fig.add_gridspec(2, 2, wspace=0.10, hspace=0.18,
                              left=0.04, right=0.96, top=0.93, bottom=0.06)

    group_domains = [
        ("BUSI", "ISIC"),
        ("KUB", "KVASIR"),
    ]
    # Map outer grid positions: (row, col) -> group
    group_positions = [(0, 0), (0, 1), (1, 0), (1, 1)]
    # Actually we have 4 domains, 2 per group, 2 groups per row
    # Row 0: Group 0 (BUSI+ISIC) at col 0, Group 1 (KUB+KVASIR) at col 1
    # But we only have 4 domains total, so 2 groups of 2 domains each
    # Wait — the work order says "2×2 SAMPLE-BLOCK GROUPS (group1|group2 / group3|group4)"
    # with "each block retaining 4 domain rows". This means 4 groups total, each with 1 domain.
    # group1 = BUSI, group2 = ISIC, group3 = KUB, group4 = KVASIR
    # Arranged as: [BUSI | ISIC] / [KUB | KVASIR]

    domain_list = ["BUSI", "ISIC", "KUB", "KVASIR"]
    for idx, d in enumerate(domain_list):
        row = idx // 2
        col = idx % 2
        inner = outer[row, col].subgridspec(4, 5, wspace=0.04, hspace=0.06)
        ax_grid = np.array([[fig.add_subplot(inner[r, c]) for c in range(5)] for r in range(4)])
        render_domain_block(ax_grid, d, picks[d], sid_to_row, pos, gp, fp)

    # ---- legend ---------------------------------------------------------------- #
    legend_elements = [
        mpatches.Patch(facecolor="green", edgecolor="black", linewidth=0.5, label="TP"),
        mpatches.Patch(facecolor="blue", edgecolor="black", linewidth=0.5, label="FN"),
        mpatches.Patch(facecolor="red", edgecolor="black", linewidth=0.5, label="FP"),
    ]
    fig.legend(handles=legend_elements, loc="lower center", ncol=3,
               fontsize=11, frameon=True, fancybox=False, edgecolor="black",
               bbox_to_anchor=(0.5, 0.01))

    # ---- save outputs ---------------------------------------------------------- #
    out_png = FIG / "p27_qualitative_panels.png"
    out_pdf = FIG / "p27_qualitative_panels.pdf"
    out_2x = FIG / "p27_qualitative_panels_2x.png"

    fig.savefig(out_png, dpi=250, facecolor="white", pad_inches=0.2)
    fig.savefig(out_pdf, dpi=250, facecolor="white", pad_inches=0.2)
    fig.savefig(out_2x, dpi=500, facecolor="white", pad_inches=0.2)
    plt.close(fig)

    print("wrote", out_png.relative_to(ROOT), "|", out_pdf.relative_to(ROOT), "|", out_2x.relative_to(ROOT))
    print("cases:", sum(len(v) for v in picks.values()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
