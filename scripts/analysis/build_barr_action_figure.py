"""Focused BARR-action figures: what BARR actually did, not what it skipped.

The per-cohort external figures (fig6-fig8) are dominated by NOT_ATTEMPTED cases,
because the router declines most of them.  They are kept as illustrative
"Global and BARR unchanged" examples.  These two figures are the complement:
four cases chosen by explicit rule from the saved records.

  fig9  — refinements that were ADOPTED
          A  accepted, largest Dice gain
          B  accepted, largest Dice loss (harmful)
  fig10 — outcomes that were NOT adopted
          C  rejected by the post-safety gate
          D  never selected by the router

They are drawn at approximately final print size (7.4 in wide, placed at 6.9 in)
so the annotation is real point size rather than a reduced thumbnail.  Selection
is deterministic and documented in ``SELECTION_RULE``; nothing is picked by eye
and no case is re-inferred.

Colour contract (identical to fig6-fig8): TP #00E600, FP #FF2020, FN #2060FF,
TN #181818.
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
CACHE = ROOT / "data_cache" / "c1_external_stress_v1_0"
FIG = ROOT / "reports" / "figures"

TP_RGB = (0, 230, 0)
FP_RGB = (255, 32, 32)
FN_RGB = (32, 96, 255)
TN_RGB = (24, 24, 24)
INK = "#1e3d59"
ROI_EDGE = "#00E6E6"

TAU_C7 = 0.001239805482327938
EPS = 1e-12

COHORTS = [("cvc", "CVC-ClinicDB"), ("breast", "BrEaST-Lesions-USG"),
           ("stones", "Stones_where_are_you")]

SELECTION_RULE = {
    "A": ("ACCEPTED case with the largest positive Dice change; ties broken by "
          "ascending sample_id"),
    "B": ("ACCEPTED case with the largest negative Dice change, restricted to cases "
          "whose change is < 0; ties broken by ascending sample_id"),
    "C": ("REJECTED case with the highest S_omega acceptance probability, i.e. the "
          "most borderline rejection; ties broken by ascending sample_id"),
    "D": ("case the router did not select, whose global Dice is closest to its own "
          "cohort median; ties broken by ascending sample_id"),
}

HEADERS = [
    "Input image\n+ candidate ROI",
    "Ground truth",
    "Global probability\n(sigmoid, cut at 0.50)",
    "Global error map\nTP / FP / FN / TN",
    "BARR final prediction\n(cut at 0.50)",
    "BARR error map\nTP / FP / FN / TN",
]

TITLES = {
    "A": "A   Accepted refinement, largest Dice gain",
    "B": "B   Accepted refinement, largest Dice loss (harmful)",
    "C": "C   Rejected candidate (S_omega declined the refinement)",
    "D": "D   Not selected by the router (unchanged by construction)",
}


def error_rgb(pred: np.ndarray, gt: np.ndarray) -> np.ndarray:
    out = np.zeros((*pred.shape, 3), dtype=np.uint8)
    out[...] = TN_RGB
    out[pred & gt] = TP_RGB
    out[pred & ~gt] = FP_RGB
    out[~pred & gt] = FN_RGB
    return out


def dice(pred: np.ndarray, gt: np.ndarray) -> float:
    tp = int(np.count_nonzero(pred & gt))
    fp = int(np.count_nonzero(pred & ~gt))
    fn = int(np.count_nonzero(~pred & gt))
    den = 2 * tp + fp + fn
    return (2 * tp / den) if den else float("nan")


def load_all() -> dict:
    rec = {}
    for key, name in COHORTS:
        d = CACHE / key
        rec[key] = {
            "name": name,
            "pg": np.load(d / "prob_global.npy"),
            "pb": np.load(d / "prob_barr.npy"),
            "gt": np.load(d / "gt.npy").astype(bool),
            "ids": json.loads((d / "sample_ids.json").read_text(encoding="utf-8")),
            "states": pd.read_csv(d / "barr_states.csv"),
        }
    return rec


def build_table(rec: dict) -> pd.DataFrame:
    rows = []
    for key, r in rec.items():
        for i, sid in enumerate(r["ids"]):
            pg, pb, gt = r["pg"][i], r["pb"][i], r["gt"][i]
            dg = dice(pg >= SEG_THRESHOLD, gt)
            db = dice(pb >= SEG_THRESHOLD, gt)
            st = r["states"].iloc[i]
            rows.append({
                "cohort_key": key, "cohort": r["name"], "index": i,
                "sample_id": sid, "dice_global": dg, "dice_barr": db,
                "delta": db - dg, "state": st["state"],
                "router_score": st["router_score"],
                "safety_prob": st["safety_prob"],
                "selected": bool(st["selected"]) if not pd.isna(st["selected"]) else False,
            })
    return pd.DataFrame(rows).sort_values(
        ["cohort_key", "sample_id"]).reset_index(drop=True)


def select(df: pd.DataFrame) -> dict:
    acc = df[df.state == "ACCEPTED"]
    a = acc.sort_values(["delta", "sample_id"], ascending=[False, True]).iloc[0]

    neg = acc[acc.delta < -EPS]
    b = (neg.sort_values(["delta", "sample_id"], ascending=[True, True]).iloc[0]
         if len(neg) else None)

    rej = df[df.state == "REJECTED"]
    c = (rej.sort_values(["safety_prob", "sample_id"], ascending=[False, True]).iloc[0]
         if len(rej) else None)

    uns = df[(~df.selected) & (df.state == "NOT_ATTEMPTED")]
    grp = uns[uns.cohort_key == a.cohort_key]
    med = grp.dice_global.median()
    d = grp.assign(_dist=(grp.dice_global - med).abs()).sort_values(
        ["_dist", "sample_id"]).iloc[0]

    return {"A": a, "B": b, "C": c, "D": d}


def trace_text(row, rec, geom) -> str:
    rs, sp = row["router_score"], row["safety_prob"]
    rs_txt = "not evaluated" if pd.isna(rs) else f"{float(rs):+.6f}"
    sp_txt = "not reached" if pd.isna(sp) else f"{float(sp):.4f}"

    if pd.isna(rs):
        decision, refiner, verdict = "no ROI candidate", "NOT RUN", ""
    elif not row["selected"]:
        decision, refiner, verdict = "NOT SELECTED", "NOT RUN", ""
    elif row["state"] == "ACCEPTED":
        decision, refiner = "SELECTED", "EXECUTED"
        verdict = ">= 0.50 ACCEPTED"
    elif row["state"] == "REJECTED":
        decision, refiner = "SELECTED", "EXECUTED, discarded"
        verdict = "< 0.50 REJECTED"
    else:
        decision = refiner = row["state"]
        verdict = ""

    roi = "none" if geom is None else (
        f"y[{geom['clip_y1']},{geom['clip_y2']}) x[{geom['clip_x1']},{geom['clip_x2']})")
    dg, db = row["dice_global"], row["dice_barr"]
    return (
        f"{row['cohort']}\n"
        f"Case {row['sample_id'].split('::')[-1][:22]}  ·  {row['state']}\n"
        f"--------------------------\n"
        f"router score  {rs_txt}\n"
        f"decision      {decision}\n"
        f"tau_C7        {TAU_C7:+.6f}\n"
        f"ROI           {roi}\n"
        f"refiner       {refiner}\n"
        f"S_omega p     {sp_txt}  {verdict}\n"
        f"--------------------------\n"
        f"Dice {dg * 100:5.2f}% -> {db * 100:5.2f}%  ({(db - dg) * 100:+5.2f} pp)"
    )


def draw(letters: list[str], sel: dict, rec: dict, co: dict, transform,
         outfile: str, suptitle: str) -> list[dict]:
    """Place every axes by explicit inch geometry so no row carries dead space."""
    n = len(letters)

    W = 7.4
    x_text, w_text = 0.045, 1.92
    gap = 0.07
    x_img0 = x_text + w_text + gap
    cw = (W - x_img0 - 0.03) / 6.0          # square panel edge, inches
    row_h = cw + 0.34                        # panel + label band
    header = 0.98 if n else 0.62
    legend_h = 0.34
    H = header + n * row_h + legend_h

    fig = plt.figure(figsize=(W, H), dpi=320)

    fig.text(0.5, 1 - 0.10 / H, suptitle, fontsize=9.2, fontweight="bold",
             ha="center", va="top", color=INK)
    fig.text(0.5, 1 - 0.30 / H,
             "RETROSPECTIVE_EXTERNAL_STRESS_TEST — rule-selected from saved records, "
             "no re-inference; illustrative cases, not dataset-level estimates.",
             fontsize=5.5, ha="center", va="top", style="italic", color="#555555")

    out_rows = []
    for r, letter in enumerate(letters):
        row = sel[letter]
        key = row["cohort_key"]
        idx = int(row["index"])
        case = co[key]["cases"][idx]
        img = Image.open(case["image_path"])
        img_t, _gt_t, _ = transform(img, Image.fromarray(
            (rec[key]["gt"][idx].astype(np.uint8) * 255), mode="L"))
        disp = np.clip(img_t.permute(1, 2, 0).numpy() * 255.0, 0, 255).astype(np.uint8)

        g = rec[key]["gt"][idx]
        p_g, p_b = rec[key]["pg"][idx], rec[key]["pb"][idx]
        pred_g, pred_b = p_g >= SEG_THRESHOLD, p_b >= SEG_THRESHOLD
        geom = roi_geometry(p_g, threshold=ROI_PROPOSAL_THRESHOLD, margin=ROI_MARGIN)

        y_top = H - header - r * row_h
        y0 = y_top - cw

        # row banner sits in the band above the panels; on the first row that band
        # also carries the column headers, so the banner is lifted clear of them
        banner_y = y_top + (0.40 if r == 0 else 0.06)
        fig.text(x_img0 / W, banner_y / H, TITLES[letter], fontsize=6.8,
                 fontweight="bold", ha="left", va="bottom", color=INK)

        axt = fig.add_axes([x_text / W, y0 / H, w_text / W, (cw + 0.02) / H])
        axt.axis("off")
        axt.text(0.0, 1.0, trace_text(row, rec, geom), transform=axt.transAxes,
                 va="top", ha="left", fontsize=5.0, family="DejaVu Sans",
                 linespacing=1.42)

        cols = [(disp, "img"), (g, "gt"), (p_g, "prob"),
                (error_rgb(pred_g, g), "err"), (pred_b, "bin"),
                (error_rgb(pred_b, g), "err")]
        for c, (data, kind) in enumerate(cols):
            ax = fig.add_axes([(x_img0 + c * cw) / W, y0 / H, cw / W, cw / H])
            if kind == "gt":
                ax.imshow(data, cmap="gray", vmin=0, vmax=1)
            elif kind == "prob":
                ax.imshow(data, cmap="plasma", vmin=0.0, vmax=1.0)
            else:
                ax.imshow(data)
            ax.set_xticks([]); ax.set_yticks([])
            if kind == "img" and geom is not None:
                ax.add_patch(mpatches.Rectangle(
                    (geom["clip_x1"], geom["clip_y1"]),
                    geom["clip_x2"] - geom["clip_x1"],
                    geom["clip_y2"] - geom["clip_y1"],
                    fill=False, edgecolor=ROI_EDGE, linewidth=1.4))
            if r == 0:
                ax.set_title(HEADERS[c], fontsize=5.7, fontweight="bold", pad=4)
            if r == n - 1:
                if kind == "gt":
                    ax.set_xlabel(f"GT {int(g.sum()):,} px", fontsize=4.7,
                                  labelpad=1.5)
                elif kind == "prob":
                    ax.set_xlabel(f"mean {p_g.mean():.3f}", fontsize=4.7,
                                  labelpad=1.5)
                elif kind == "bin":
                    ax.set_xlabel(f"BARR Dice {row['dice_barr'] * 100:.2f}%",
                                  fontsize=4.7, labelpad=1.5)
                elif kind == "err" and c == 3:
                    ax.set_xlabel(f"global Dice {row['dice_global'] * 100:.2f}%",
                                  fontsize=4.7, labelpad=1.5)

        out_rows.append({
            "panel": letter, "cohort": row["cohort"],
            "sample_id": row["sample_id"], "state": row["state"],
            "dice_global": float(row["dice_global"]),
            "dice_barr": float(row["dice_barr"]),
            "delta": float(row["delta"]),
            "router_score": None if pd.isna(row["router_score"])
            else float(row["router_score"]),
            "safety_prob": None if pd.isna(row["safety_prob"])
            else float(row["safety_prob"]),
            "roi_present": geom is not None,
        })

    legend = [
        mpatches.Patch(color=np.array(TP_RGB) / 255, label="TP correct foreground"),
        mpatches.Patch(color=np.array(FP_RGB) / 255, label="FP over-segmented"),
        mpatches.Patch(color=np.array(FN_RGB) / 255, label="FN missed"),
        mpatches.Patch(color=np.array(TN_RGB) / 255, label="TN correct background"),
        mpatches.Patch(facecolor="none", edgecolor=ROI_EDGE, label="candidate ROI"),
    ]
    fig.legend(handles=legend, loc="lower center", ncol=5, frameon=False,
               fontsize=5.4, bbox_to_anchor=(0.60, 0.004),
               handlelength=1.3, columnspacing=1.2)

    out = FIG / outfile
    fig.savefig(out, dpi=320, facecolor="white", bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    print(f"wrote {out.name}  rows={letters}")
    return out_rows


def main() -> int:
    rec = load_all()
    df = build_table(rec)
    sel = select(df)
    co = build_cohorts()
    _ = load_stones_coco()
    transform = SegmentationTransform(size=512, train=False, image_mode="RGB")

    if sel["B"] is None:
        raise SystemExit("no accepted case with a negative Dice change exists")
    if sel["C"] is None:
        raise SystemExit("no rejected case exists")

    rows9 = draw(["A", "B"], sel, rec, co, transform,
                 "fig9_external_barr_action_adopted.png",
                 "BARR refinements that were adopted: one helping, one harming")
    rows10 = draw(["C", "D"], sel, rec, co, transform,
                  "fig10_external_barr_action_notadopted.png",
                  "BARR outcomes that were not adopted: rejected and never selected")

    stones_acc = df[(df.cohort_key == "stones") & (df.state == "ACCEPTED")]
    neg_counts = {
        "cvc": int((df[(df.cohort_key == "cvc")
                       & (df.state == "ACCEPTED")].delta < -EPS).sum()),
        "breast": int((df[(df.cohort_key == "breast")
                           & (df.state == "ACCEPTED")].delta < -EPS).sum()),
        "stones": int((stones_acc.delta < -EPS).sum()),
    }
    manifest = {
        "artifact": "c1_external_barr_action_figures",
        "inference_rerun": False,
        "source": "saved prob/pred arrays and barr_states.csv from the 884-case campaign",
        "error_palette_rgb": {"TP": TP_RGB, "FP": FP_RGB, "FN": FN_RGB, "TN": TN_RGB},
        "selection_rule": SELECTION_RULE,
        "figures": {
            "fig9_external_barr_action_adopted.png": rows9,
            "fig10_external_barr_action_notadopted.png": rows10,
        },
        "accepted_with_negative_change": neg_counts,
        "stones_accepted_n": int(len(stones_acc)),
        "stones_harmful_example": "ABSENT__no_accepted_case_lost_dice",
        "stones_min_accepted_delta": float(stones_acc.delta.min()),
        "rejected_delta_note": ("every REJECTED case has delta == 0 exactly, because the "
                                "refined output is discarded and the global mask retained"),
        "legend_note": ("A rejected candidate still executed the refiner and the safety "
                        "head; only its output was discarded, so its BARR panels equal "
                        "Global by construction. That equality is the rejection, not a "
                        "missing panel."),
    }
    (AUD / "barr_action_figure.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    for r in rows9 + rows10:
        print(f"  {r['panel']}  {r['cohort']:22s} {r['sample_id']:26s} "
              f"{r['state']:14s} delta={r['delta'] * 100:+6.2f} pp")
    print("accepted-with-negative-change:", neg_counts,
          "| stones accepted:", len(stones_acc),
          "min delta:", f"{stones_acc.delta.min():+.5f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
