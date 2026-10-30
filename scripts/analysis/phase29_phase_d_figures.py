#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 29 — PHASE D STAGE 6: VAL808 figures (§23).

Five descriptive figures (no ranking, no best-seed selection):
    fig_val808_seedwise_macro_delta_dice.png
    fig_val808_per_domain_delta_dice.png
    fig_val808_router_safety_activation.png
    fig_val808_cross_seed_final_activation_overlap.png
    fig_val808_per_sample_final_dice_distribution.png

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase29_phase_d_figures.py
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase29_phase_d_common as D  # noqa: E402

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

FIGDIR = D.FIG / "phase29_val808"
DOMAINS = D.DOMAINS
SEEDS = D.MASTER_SEEDS


def rows(name):
    return list(csv.DictReader(open(D.TAB / name, encoding="utf-8")))


def main() -> int:
    FIGDIR.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"figure.dpi": 130, "font.size": 9,
                         "axes.grid": True, "grid.alpha": 0.3})
    made = []

    prim = {int(r["master_seed"]): r for r in rows(
        "phase29_val808_seedwise_primary_metrics.csv")}
    dom = rows("phase29_val808_seedwise_domain_metrics.csv")

    # ---- 1. seed-wise macro DeltaDice ------------------------------------- #
    fig, ax = plt.subplots(figsize=(5.6, 3.4))
    vals = [float(prim[s]["macro_delta_dice"]) for s in SEEDS]
    ax.bar([f"seed {s}" for s in SEEDS], vals, color="#c0392b")
    for i, v in enumerate(vals):
        ax.text(i, v, f"{v:+.6f}", ha="center", va="bottom", fontsize=8)
    ax.set_ylabel("macro-domain DeltaDice")
    ax.set_title("VAL808 macro DeltaDice by seed")
    fig.tight_layout()
    p = FIGDIR / "fig_val808_seedwise_macro_delta_dice.png"
    fig.savefig(p); plt.close(fig); made.append(p)

    # ---- 2. per-domain DeltaDice across seeds ----------------------------- #
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    w = 0.26
    x = np.arange(len(DOMAINS))
    for k, s in enumerate(SEEDS):
        v = [float(next(r for r in dom
                        if int(r["master_seed"]) == s and r["domain"] == d)["delta_dice"])
             for d in DOMAINS]
        ax.bar(x + (k - 1) * w, v, w, label=f"seed {s}")
    ax.axhline(0, color="k", lw=0.8)
    ax.set_xticks(x); ax.set_xticklabels(DOMAINS)
    ax.set_ylabel("DeltaDice"); ax.legend()
    ax.set_title("VAL808 per-domain DeltaDice across seeds")
    fig.tight_layout()
    p = FIGDIR / "fig_val808_per_domain_delta_dice.png"
    fig.savefig(p); plt.close(fig); made.append(p)

    # ---- 3. router / safety activation fractions --------------------------- #
    fig, ax = plt.subplots(figsize=(6.0, 3.4))
    x = np.arange(len(SEEDS)); w = 0.35
    rsf = [float(prim[s]["selected_fraction"]) for s in SEEDS]
    saf = [float(prim[s]["safety_accept_fraction"]) for s in SEEDS]
    ax.bar(x - w / 2, rsf, w, label="router selected fraction", color="#2980b9")
    ax.bar(x + w / 2, saf, w, label="safety accept | selected", color="#27ae60")
    ax.set_xticks(x); ax.set_xticklabels([f"seed {s}" for s in SEEDS])
    ax.set_ylim(0, 1.05); ax.set_ylabel("fraction"); ax.legend()
    ax.set_title("VAL808 router selection and safety acceptance")
    fig.tight_layout()
    p = FIGDIR / "fig_val808_router_safety_activation.png"
    fig.savefig(p); plt.close(fig); made.append(p)

    # ---- 4. cross-seed final-activation overlap ---------------------------- #
    ov = {r["statistic"]: r["value"] for r in rows(
        "phase29_val808_final_activation_overlap.csv")}
    fig, ax = plt.subplots(figsize=(5.6, 3.4))
    keys = ["all3_intersection", "exactly2", "exactly1", "none"]
    vals = [int(float(ov[k])) for k in keys]
    ax.bar([k.replace("_", " ") for k in keys], vals, color="#8e44ad")
    for i, v in enumerate(vals):
        ax.text(i, v, str(v), ha="center", va="bottom", fontsize=8)
    ax.set_ylabel("VAL808 samples")
    ax.set_title("Cross-seed final-refinement activation overlap")
    fig.tight_layout()
    p = FIGDIR / "fig_val808_cross_seed_final_activation_overlap.png"
    fig.savefig(p); plt.close(fig); made.append(p)

    # ---- 5. per-sample final-Dice differences ------------------------------ #
    preds = {}
    for s in SEEDS:
        preds[s] = list(csv.DictReader(open(
            D.TAB / f"phase29_seed{s}_val808_predictions.csv", encoding="utf-8")))
    fig, ax = plt.subplots(figsize=(6.0, 3.6))
    for s in SEEDS:
        dd = np.array([float(r["final_dice"]) - float(r["global_dice"])
                       for r in preds[s] if r["selected"] == "True"])
        ax.hist(dd, bins=60, range=(-0.3, 0.3), histtype="step",
                lw=1.3, label=f"seed {s} (n={dd.size})")
    ax.axvline(0, color="k", lw=0.8)
    ax.set_xlabel("per-sample final Dice - global Dice (selected only)")
    ax.set_ylabel("count"); ax.legend()
    ax.set_title("VAL808 per-sample refinement effect distribution")
    fig.tight_layout()
    p = FIGDIR / "fig_val808_per_sample_final_dice_distribution.png"
    fig.savefig(p); plt.close(fig); made.append(p)

    D.write_json({
        "artifact": "phase29_val808_figure_manifest",
        "phase": 29, "stage": "VAL808_FIGURES",
        "method": D.METHOD, "generated_utc": D.now_utc(),
        "figures": [str(p.relative_to(D.ROOT)) for p in made],
        "titles_have_no_figure_number": True,
        "ranking_performed": False,
        "all_pass": True,
    }, D.AUD / "phase29_val808_figure_manifest.json")

    print("figures written:")
    for p in made:
        print("  ", p.relative_to(D.ROOT))
    print("PHASE29_PHASE_D_FIGURES_COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
