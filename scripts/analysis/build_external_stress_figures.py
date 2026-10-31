"""External stress-test prediction figures (8 columns, Global + BARR).

Column set is fixed by the pre-registered plan
(``reports/audits/c1_external_stress_v1_0/EXTERNAL_STRESS_TEST_PLAN.md`` §10):

    1 input image            5 global probability map
    2 ground truth           6 BARR final prediction
    3 global prediction      7 BARR error map
    4 global error map       8 BARR decision trace

Error palette is identical to the already-published figures so the two sets stay
visually comparable.

Row selection is by rule, not by eye: per cohort the median-Dice, worst and best
case; for Stones also the largest and smallest non-empty ground-truth lesion.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from PIL import Image  # noqa: E402

ROOT = Path(r"D:\Softfors\jup")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))

from src.data.barr_roi import roi_geometry  # noqa: E402
from src.data.transforms import SegmentationTransform  # noqa: E402
from c1_external_stress_eval import (  # noqa: E402
    ROI_MARGIN, ROI_PROPOSAL_THRESHOLD, SEG_THRESHOLD, build_cohorts, load_stones_coco,
)

AUD = ROOT / "reports" / "audits" / "c1_external_stress_v1_0"
TAB = ROOT / "reports" / "tables"
CACHE = ROOT / "data_cache" / "c1_external_stress_v1_0"
FIG = ROOT / "reports" / "figures"
FIG.mkdir(parents=True, exist_ok=True)

TP_RGB = (0, 230, 0)
FP_RGB = (255, 32, 32)
FN_RGB = (32, 96, 255)
TN_RGB = (24, 24, 24)
INK = "#1e3d59"

COHORTS = [("cvc", "CVC-ClinicDB", "KVASIR", "fig6_external_cvc.png"),
           ("breast", "BrEaST-Lesions-USG", "BUSI", "fig7_external_breast.png"),
           ("stones", "Stones_where_are_you", "KUB", "fig8_external_stones.png")]

HEADERS = [
    "Column 1\nInput image\n(512x512 canvas)",
    "Column 2\nGround truth",
    "Column 3\nGlobal prediction\n(threshold 0.50)",
    "Column 4\nGlobal error map\nTP / FP / FN / TN",
    "Column 5\nGlobal probability\n(sigmoid)",
    "Column 6\nBARR final prediction\n(threshold 0.50)",
    "Column 7\nBARR error map\nTP / FP / FN / TN",
    "Column 8\nBARR decision trace\n(ROI + state + scores)",
]


def error_rgb(pred: np.ndarray, gt: np.ndarray) -> np.ndarray:
    out = np.zeros((*pred.shape, 3), dtype=np.uint8)
    out[...] = TN_RGB
    out[pred & gt] = TP_RGB
    out[pred & ~gt] = FP_RGB
    out[~pred & gt] = FN_RGB
    return out


def dice(pred: np.ndarray, gt: np.ndarray) -> float:
    tp = np.count_nonzero(pred & gt)
    den = 2 * tp + np.count_nonzero(pred & ~gt) + np.count_nonzero(~pred & gt)
    return (2 * tp / den) if den else float("nan")


def select_rows(key: str, pc: pd.DataFrame) -> list[int]:
    g = pc[(pc.cohort_key == key) & (pc.arm == "global")].sort_values("index")
    picks = {}
    d = g["Dice"].to_numpy()
    order = np.argsort(np.where(np.isfinite(d), d, -1))
    picks["best"] = int(g.iloc[order[-1]]["index"])
    picks["worst"] = int(g.iloc[order[0]]["index"])
    picks["median"] = int(g.iloc[order[len(order) // 2]]["index"])
    if key == "stones":
        nz = g[g["gt_pixels"] > 0]
        if len(nz):
            picks["largest_gt"] = int(nz.sort_values("gt_pixels").iloc[-1]["index"])
            picks["smallest_gt"] = int(nz.sort_values("gt_pixels").iloc[0]["index"])
            # the cohort-wide median is a stone-free case (14/20 have Dice 0), which is
            # itself the headline finding; add the stone-positive median so the reader
            # sees both regimes without either being hidden by the other
            nzs = nz.sort_values("Dice")
            picks["median_positive"] = int(nzs.iloc[len(nzs) // 2]["index"])
    out = []
    for k in ("median", "best", "worst", "largest_gt", "smallest_gt", "median_positive"):
        if k in picks and picks[k] not in out:
            out.append(picks[k])
    return out


def build(key: str, name: str, analogue: str, outfile: str) -> dict:
    d = CACHE / key
    pg = np.load(d / "prob_global.npy")
    pb = np.load(d / "prob_barr.npy")
    gt = np.load(d / "gt.npy").astype(bool)
    ids = json.loads((d / "sample_ids.json").read_text(encoding="utf-8"))
    states = pd.read_csv(d / "barr_states.csv")
    pc = pd.read_csv(TAB / "c1_external_stress_per_case.csv")

    co = build_cohorts()[key]
    coco = load_stones_coco()
    transform = SegmentationTransform(size=512, train=False, image_mode="RGB")

    rows = select_rows(key, pc)
    n = len(rows)
    fig = plt.figure(figsize=(34, 4.35 * n + 2.4), dpi=200)
    plt.subplots_adjust(top=0.895, bottom=0.075, left=0.145, right=0.992,
                        hspace=0.42, wspace=0.10)

    fig.suptitle(f"Figure — External stress test, {name} (task id {co['task_id']}, "
                 f"{analogue} analogue), n = {len(ids)}",
                 fontsize=19, fontweight="bold", y=0.977, color=INK)
    fig.text(0.5, 0.951,
             "RETROSPECTIVE_EXTERNAL_STRESS_TEST — descriptive only, no confirmatory "
             "p-value. Surface metrics, where quoted, are in pixels.",
             fontsize=11.5, ha="center", style="italic", color="#555555")

    for r, idx in enumerate(rows):
        case = co["cases"][idx]
        img = Image.open(case["image_path"])
        img_t, gt_t, _ = transform(img, Image.fromarray(
            (gt[idx].astype(np.uint8) * 255), mode="L"))
        disp = np.clip(img_t.permute(1, 2, 0).numpy() * 255.0, 0, 255).astype(np.uint8)
        g = gt[idx]
        p_g, p_b = pg[idx], pb[idx]
        pred_g, pred_b = p_g >= SEG_THRESHOLD, p_b >= SEG_THRESHOLD
        st = states.iloc[idx]

        dg, db = dice(pred_g, g), dice(pred_b, g)
        tp = int(np.count_nonzero(pred_g & g))
        fp = int(np.count_nonzero(pred_g & ~g))
        fn = int(np.count_nonzero(~pred_g & g))

        geom = roi_geometry(p_g, threshold=ROI_PROPOSAL_THRESHOLD, margin=ROI_MARGIN)
        roi_txt = ("no ROI (empty prediction at 0.30)" if geom is None else
                   f"ROI y[{geom['clip_y1']},{geom['clip_y2']}) "
                   f"x[{geom['clip_x1']},{geom['clip_x2']})")
        rs = st["router_score"]
        sp = st["safety_prob"]
        rs_txt = "not evaluated" if pd.isna(rs) else f"{float(rs):+.6f}"
        sp_txt = "not reached" if pd.isna(sp) else f"{float(sp):.4f}"

        label = (
            f"{name}\n"
            f"Case: {case['sample_id'].split('::')[-1][:34]}\n"
            f"GT area {int(g.sum()):,} px  |  pred {int(pred_g.sum()):,} px\n"
            f"------------------------------\n"
            f"GLOBAL   Dice {dg * 100:6.2f}%   (TP {tp:,}  FP {fp:,}  FN {fn:,})\n"
            f"BARR     Dice {db * 100:6.2f}%\n"
            f"delta    {(db - dg) * 100:+6.2f} pp\n"
            f"------------------------------\n"
            f"BARR state: {st['state']}\n"
            f"router score: {rs_txt}\n"
            f"tau_C7 = +0.001240\n"
            f"S_omega p(accept): {sp_txt}"
        )

        cols = [
            ("img", disp, None),
            ("gt", g, None),
            ("pred_g", pred_g, None),
            ("err_g", error_rgb(pred_g, g), None),
            ("prob", p_g, "plasma"),
            ("pred_b", pred_b, None),
            ("err_b", error_rgb(pred_b, g), None),
            ("trace", disp, None),
        ]

        for c, (kind, data, cmap) in enumerate(cols):
            ax = fig.add_subplot(n, 8, r * 8 + c + 1)
            if kind == "gt":
                ax.imshow(data, cmap="gray", vmin=0, vmax=1)
            elif kind == "prob":
                ax.imshow(data, cmap="plasma", vmin=0.0, vmax=1.0)
            else:
                ax.imshow(data)
            ax.set_xticks([]); ax.set_yticks([])
            if r == 0:
                ax.set_title(HEADERS[c], fontsize=11.5, fontweight="bold", pad=9)
            if kind == "trace" and geom is not None:
                rect = mpatches.Rectangle(
                    (geom["clip_x1"], geom["clip_y1"]),
                    geom["clip_x2"] - geom["clip_x1"],
                    geom["clip_y2"] - geom["clip_y1"],
                    fill=False, edgecolor="#00E6E6", linewidth=1.8)
                ax.add_patch(rect)
            if c == 0:
                pos = ax.get_position()
                fig.text(0.008, (pos.y0 + pos.y1) / 2, label, fontsize=9.6,
                         ha="left", va="center", family="DejaVu Sans", linespacing=1.5)

        # per-column footers
        fig.axes[-8].set_xlabel(f"GT {int(g.sum()):,} px", fontsize=9, labelpad=3)
        fig.axes[-6].set_xlabel(f"Dice {dg * 100:.1f}%", fontsize=9, labelpad=3)
        fig.axes[-5].set_xlabel(f"TP {tp:,} FP {fp:,} FN {fn:,}", fontsize=9, labelpad=3)
        fig.axes[-4].set_xlabel(f"p in [0,1], mean {p_g.mean():.3f}", fontsize=9, labelpad=3)
        fig.axes[-3].set_xlabel(f"Dice {db * 100:.1f}%", fontsize=9, labelpad=3)
        fig.axes[-1].set_xlabel(roi_txt, fontsize=8.5, labelpad=3)

    legend = [
        mpatches.Patch(color=np.array(TP_RGB) / 255, label="TP — correct foreground"),
        mpatches.Patch(color=np.array(FP_RGB) / 255, label="FP — over-segmented"),
        mpatches.Patch(color=np.array(FN_RGB) / 255, label="FN — missed"),
        mpatches.Patch(color=np.array(TN_RGB) / 255, label="TN — correct background"),
        mpatches.Patch(facecolor="none", edgecolor="#00E6E6", label="frozen ROI window"),
    ]
    fig.legend(handles=legend, loc="lower center", ncol=5, frameon=False,
               fontsize=10.5, bbox_to_anchor=(0.55, 0.012))
    fig.text(0.008, 0.012,
             "Row selection is by rule (median / best / worst Dice; Stones also largest "
             "and smallest non-empty lesion),\nnot by eye. Panels are illustrative cases, "
             "not dataset-level estimates. No clinical verdict is implied.",
             fontsize=9, ha="left", va="bottom", color="#555555")

    out = FIG / outfile
    fig.savefig(out, dpi=200, facecolor="white", bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)
    print(f"wrote {out.name}  rows={rows}")
    return {"figure": outfile, "rows": rows,
            "sample_ids": [co["cases"][i]["sample_id"] for i in rows]}


def main() -> int:
    rec = {"artifact": "c1_external_stress_figures",
           "columns": 8, "error_palette_rgb": {"TP": TP_RGB, "FP": FP_RGB,
                                               "FN": FN_RGB, "TN": TN_RGB},
           "figures": []}
    for key, name, analogue, outfile in COHORTS:
        rec["figures"].append(build(key, name, analogue, outfile))
    (AUD / "figures_manifest.json").write_text(json.dumps(rec, indent=2) + "\n",
                                               encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
