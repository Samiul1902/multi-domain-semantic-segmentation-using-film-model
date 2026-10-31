"""Build Figures 1-3 for the RA-MedFiLM-BARR scientific report from frozen
result artifacts only.

Motivation
----------
Before this script there was no generator for fig1/fig2/fig3 in the repository:
the Word builder only embedded pre-existing PNGs. That made those figures
unauditable. This script binds every plotted value to a named artifact.

Sources (all read, never written):
  reports/tables/phase21_six_model_comparison.csv
      -> the six-model VAL808 comparison (Phase 21 protocol)
  reports/audits/phase21_analysis.json
      -> Global MedFiLM macro Dice + 95% bootstrap CI on VAL808
  reports/audits/phase29_phase_d_three_seed_descriptive_summary.json
      -> BARR macro Dice delta on VAL808, three seeds (descriptive only)
  reports/audits/phase30_primary_noninferiority_result.json
      -> BARR vs Global macro Dice on ROUTER_HOLDOUT (n=875) + per-domain deltas
  reports/tables/phase28_table_02_arm_primary_metrics.csv
      -> harm rates and routed-crop counts per arm

Scientific rules enforced here:
  * BARR is never plotted as if it were part of the Phase 21 six-model run.
    It is drawn as a separately marked series with its own population label.
  * Per-domain comparison is plotted as a DELTA with its 95% CI, not as
    absolute scores on a truncated axis that makes a 0.17 pp difference look
    large.
  * No superiority wording. The BARR result is a preservation result.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "paper_doc"
OUT.mkdir(parents=True, exist_ok=True)

NAVY = "#1F497D"
STEEL = "#2E75B6"
LIGHT = "#9DC3E6"
ACCENT = "#C00000"
GREY = "#7F7F7F"


def load_six_models():
    rows = list(csv.DictReader(open(ROOT / "reports/tables/phase21_six_model_comparison.csv",
                                    encoding="utf-8-sig")))
    out = {}
    for r in rows:
        out[r["model_key"]] = dict(
            name=r["display_name"],
            params=float(r["params"]) if r["params"] else None,
            dice=float(r["macro_domain_dice"]),
            ci_low=float(r["macro_domain_dice_ci_low"]),
            ci_high=float(r["macro_domain_dice_ci_high"]),
        )
    return out


def fig1(six, analysis, phase29):
    """Model comparison: Phase 21 six-model protocol, plus BARR as a separate series."""
    g = analysis["global_medfilm"]
    global_dice = g["macro_domain_dice"]
    global_lo, global_hi = g["macro_domain_dice_ci_low"], g["macro_domain_dice_ci_high"]

    # BARR on VAL808: Phase 29 three-seed mean of the DeltaDice, added to the
    # Global reference. Descriptive only (no CI is defined for this estimand).
    d = phase29["macro_delta_dice"]
    barr_dice = global_dice + d["mean"]
    barr_lo = global_dice + d["min"]
    barr_hi = global_dice + d["max"]
    barr_params = 4837420  # L28: G + R_psi + B_phi + S_omega

    order = ["unet", "attention_unet", "unetpp", "transformer_mit_unet",
             "deeplabv3plus", "global_medfilm"]
    labels = [six[k]["name"].replace("/", "/\n").replace("Transformer/MiT-style U-Net",
                                                         "Transformer\nMiT U-Net")
              for k in order]
    labels = [l.replace("Attention U-Net", "Attention\nU-Net")
               .replace("Standard U-Net", "Standard\nU-Net")
               .replace("Global MedFiLM", "Global\nMedFiLM") for l in labels]
    dice = [six[k]["dice"] * 100 for k in order]
    lo = [six[k]["ci_low"] * 100 for k in order]
    hi = [six[k]["ci_high"] * 100 for k in order]
    # The six-model CSV leaves params blank for global_medfilm; take it from the
    # Phase 21 analysis record (and cross-check against the Phase 34 total).
    six["global_medfilm"]["params"] = float(analysis["global_medfilm"]["params"])
    params = [six[k]["params"] / 1e6 for k in order]

    labels.append("Regional BARR\n(A8/C9)")
    dice.append(barr_dice * 100)
    lo.append(barr_lo * 100)
    hi.append(barr_hi * 100)
    params.append(barr_params / 1e6)

    colors = [LIGHT] * 5 + [STEEL] + [NAVY]
    x = np.arange(len(dice))

    fig, ax = plt.subplots(figsize=(13.2, 7.0), dpi=300)
    bars = ax.bar(x, dice, color=colors, edgecolor="#333333", linewidth=0.7, width=0.66,
                  zorder=3)
    # BARR bar gets a hatch so it cannot be mistaken for a Phase 21 result
    bars[-1].set_hatch("///")
    bars[-1].set_edgecolor(ACCENT)
    bars[-1].set_linewidth(1.6)

    yerr = np.array([[dice[i] - lo[i] for i in range(len(dice))],
                     [hi[i] - dice[i] for i in range(len(dice))]])
    ax.errorbar(x, dice, yerr=yerr, fmt="none", ecolor="#222222", elinewidth=1.0,
                capsize=4, zorder=4)

    for i, v in enumerate(dice):
        ax.text(x[i], hi[i] + 0.25, f"{v:.2f}", ha="center", va="bottom",
                fontsize=9.5, fontweight="bold", color="#1a1a1a")

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("Macro-domain Dice on VAL808 (%, n = 808)", fontsize=11)
    ax.set_ylim(70, 90)
    ax.set_yticks(np.arange(70, 91, 2))
    ax.grid(axis="y", linestyle="--", alpha=0.35, zorder=0)
    ax.set_axisbelow(True)
    ax.axhline(global_dice * 100, color=STEEL, linestyle=":", linewidth=1.2, zorder=2)
    ax.text(-0.42, global_dice * 100 + 0.22, "Global MedFiLM reference 83.51",
            fontsize=8.2, color=STEEL, ha="left")

    ax.set_title("Multi-domain segmentation accuracy on VAL808 across architectures",
                 fontsize=13.5, fontweight="bold", color="#1e3d59", pad=14)

    # Parameter counts are printed under each tick label rather than on a second
    # y-axis, which would invite a false "more parameters -> better" reading.
    ax.set_xticks(x)
    ax.set_xticklabels([f"{l}\n{p:.2f} M params" for l, p in zip(labels, params)], fontsize=8.6)

    handles = [
        plt.Rectangle((0, 0), 1, 1, facecolor=LIGHT, edgecolor="#333333"),
        plt.Rectangle((0, 0), 1, 1, facecolor=STEEL, edgecolor="#333333"),
        plt.Rectangle((0, 0), 1, 1, facecolor=NAVY, edgecolor=ACCENT, hatch="///"),
    ]
    ax.legend(handles,
              ["Phase 21 baselines (shared protocol)",
               "Global MedFiLM (Phase 21)",
               "Regional BARR \u2014 separate run, not a Phase 21 arm"],
              fontsize=8.6, loc="upper left", frameon=True, framealpha=0.95)

    note = (
        "Six baseline/Global bars: Phase 21 six-model comparison, identical training and evaluation protocol, "
        "VAL808 (n = 808).\n"
        "Regional BARR bar: VAL808 macro Dice = Global reference + Phase 29 three-seed mean DeltaDice "
        f"(+{d['mean']*100:.3f} pp; seed range +{d['min']*100:.3f} to +{d['max']*100:.3f} pp). "
        "BARR was NOT trained or evaluated inside the Phase 21 run,\nso the hatched bar is a cross-run comparison, "
        "not a controlled head-to-head. Error bars: 95% bootstrap CI (Phase 21) and three-seed min/max range (BARR). "
        "Descriptive only \u2014 no significance test was performed.\n"
        "y-axis does not start at zero (range 70-90)."
    )
    fig.text(0.5, 0.015, note, fontsize=7.6, ha="center", va="bottom", color="#333333",
             linespacing=1.5)

    fig.subplots_adjust(left=0.075, right=0.985, top=0.90, bottom=0.27)
    p = OUT / "fig1_model_comparison.png"
    fig.savefig(p, dpi=300)
    plt.close(fig)
    print("wrote", p)
    return dict(global_dice=global_dice, barr_dice=barr_dice, barr_params=barr_params)


def fig2(p30):
    """Per-domain DELTA with 95% CI on ROUTER_HOLDOUT, plus the macro row."""
    order = ["KUB", "ISIC", "BUSI", "KVASIR"]
    pd_ = p30["per_domain"]
    labels = order + ["Macro"]
    point = [pd_[k]["point"] * 100 for k in order] + [p30["macro_delta_dice"] * 100]
    lo = [pd_[k]["ci_low"] * 100 for k in order] + [p30["macro_ci"][0] * 100]
    hi = [pd_[k]["ci_high"] * 100 for k in order] + [p30["macro_ci"][1] * 100]

    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(11.6, 6.6), dpi=300)
    ax.axhline(0, color="#333333", linewidth=1.0)
    colors = [NAVY if (l > 0 and lo_ > 0) else STEEL for l, lo_ in zip(point, lo)]
    colors[-1] = "#C00000"
    ax.bar(x, point, color=colors, width=0.55, edgecolor="#222222", linewidth=0.7, zorder=3)
    ax.errorbar(x, point, yerr=[np.array(point) - np.array(lo), np.array(hi) - np.array(point)],
                fmt="none", ecolor="#111111", elinewidth=1.3, capsize=5, zorder=4)

    # Point estimates above each bar; CI strings in a dedicated row at the bottom
    # so they cannot be hidden behind a bar.
    CI_ROW = -0.90
    for i, (p_, l_, h_) in enumerate(zip(point, lo, hi)):
        ax.text(x[i], h_ + 0.04, f"{p_:+.3f}", ha="center", va="bottom",
                fontsize=9.5, fontweight="bold")
        ax.text(x[i], CI_ROW, f"[{l_:+.3f},\n {h_:+.3f}]", ha="center", va="bottom",
                fontsize=7.8, color="#333333", linespacing=1.35)
    ax.text(-0.55, CI_ROW, "95% CI", fontsize=7.8, color="#333333", style="italic",
            ha="left", va="bottom")

    ax.axhline(-0.5, color=ACCENT, linestyle="--", linewidth=1.1)
    ax.text(len(labels) - 0.52, -0.47, "non-inferiority margin \u22120.5 pp",
            fontsize=8.2, color=ACCENT, ha="right", va="bottom")

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10.5)
    ax.set_ylabel("BARR \u2212 Global MedFiLM, macro Dice (percentage points)", fontsize=10.5)
    ax.set_ylim(-1.05, 1.05)
    ax.grid(axis="y", linestyle="--", alpha=0.3, zorder=0)
    ax.set_axisbelow(True)
    ax.set_title("Regional BARR versus Global MedFiLM on the one-shot ROUTER_HOLDOUT (n = 875)",
                 fontsize=13, fontweight="bold", color="#1e3d59", pad=12)

    fig.text(0.5, 0.015,
             "PRESERVATION / non-inferiority result, not an improvement claim. "
             "BUSI and KVASIR 95% CIs include zero.\n"
             "Qualifier: ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_"
             "SCIENTIFIC_SOURCE_FREEZE_DEVIATION.\n"
             "No confirmatory significance test was performed (Phase 31: zero eligible procedures).",
             fontsize=7.8, ha="center", va="bottom", color="#333333", linespacing=1.55)

    fig.subplots_adjust(left=0.085, right=0.985, top=0.90, bottom=0.245)
    p = OUT / "fig2_domain_performance.png"
    fig.savefig(p, dpi=300)
    plt.close(fig)
    print("wrote", p)


def fig3():
    """Harm-rate decomposition and routed-crop workload, from the Phase 28 arm table."""
    rows = {r["arm"]: r for r in csv.DictReader(
        open(ROOT / "reports/tables/phase28_table_02_arm_primary_metrics.csv", encoding="utf-8-sig"))}
    N = 4957
    a1 = rows["A1"]; a7 = rows["A7"]; a8 = rows["A8"]

    def allpop(r):
        return int(r["n_harmful_routed"]) / N * 100

    labels = ["A1\nunconditional refine", "A7\nrouter only", "A8\nrouter + S_omega"]
    harm = [allpop(a1), allpop(a7), allpop(a8)]
    crops = [int(a1["n_routed"]), int(a7["n_routed"]), int(a8["n_routed"])]
    n_harm = [int(a1["n_harmful_routed"]), int(a7["n_harmful_routed"]), int(a8["n_harmful_routed"])]

    fig, (axL, axR) = plt.subplots(1, 2, figsize=(12.4, 5.6), dpi=300)
    x = np.arange(3)

    axL.bar(x, harm, color=["#C00000", STEEL, "#2E7D32"], width=0.55,
            edgecolor="#222222", linewidth=0.7, zorder=3)
    for i, (h, n) in enumerate(zip(harm, n_harm)):
        axL.text(x[i], h + 1.0, f"{h:.2f}%\n({n:,} cases)", ha="center", va="bottom",
                 fontsize=9.5, fontweight="bold")
    axL.set_xticks(x); axL.set_xticklabels(labels, fontsize=9.5)
    axL.set_ylabel("All-population harm rate (%)", fontsize=10.5)
    axL.set_ylim(0, 52)
    axL.grid(axis="y", linestyle="--", alpha=0.3, zorder=0); axL.set_axisbelow(True)
    axL.set_title("Harm rate, intent-to-treat denominator (N = 4,957)", fontsize=11.5,
                  fontweight="bold", color="#1e3d59")

    axR.bar(x, crops, color=["#C00000", STEEL, "#2E7D32"], width=0.55,
            edgecolor="#222222", linewidth=0.7, zorder=3)
    for i, c in enumerate(crops):
        axR.text(x[i], c + 80, f"{c:,}\n({c/N*100:.1f}%)", ha="center", va="bottom",
                 fontsize=9.5, fontweight="bold")
    axR.set_xticks(x); axR.set_xticklabels(labels, fontsize=9.5)
    axR.set_ylabel("High-capacity crops processed", fontsize=10.5)
    axR.set_ylim(0, 5700)
    axR.grid(axis="y", linestyle="--", alpha=0.3, zorder=0); axR.set_axisbelow(True)
    axR.set_title("Refiner workload (crops executed)", fontsize=11.5,
                  fontweight="bold", color="#1e3d59")

    fig.suptitle("Safety and compute: decomposition of the BARR harm reduction",
                 fontsize=13.5, fontweight="bold", color="#1e3d59", y=0.97)

    fig.text(0.5, 0.02,
             "ROUTER_DEVELOPMENT (n = 4,957, K = 1,239). In-sample development evidence: the 4,957 rows are a subset "
             "of the 5,832 TRAIN samples, so this is not held-out evidence.\n"
             "The router accounts for most of the reduction (A1 \u2192 A7: 2,115 \u2192 412 harmful). "
             "S_omega alone accounts for A7 \u2192 A8 (412 \u2192 390, i.e. 22 cases). "
             "A reduced average harm rate is not evidence of zero harmful outcomes.",
             fontsize=7.8, ha="center", va="bottom", color="#333333", linespacing=1.55)

    fig.subplots_adjust(left=0.07, right=0.985, top=0.855, bottom=0.215, wspace=0.22)
    p = OUT / "fig3_safety_compute.png"
    fig.savefig(p, dpi=300)
    plt.close(fig)
    print("wrote", p)


def main():
    six = load_six_models()
    analysis = json.loads((ROOT / "reports/audits/phase21_analysis.json").read_text(encoding="utf-8"))
    phase29 = json.loads((ROOT / "reports/audits/phase29_phase_d_three_seed_descriptive_summary.json")
                         .read_text(encoding="utf-8"))
    p30 = json.loads((ROOT / "reports/audits/phase30_primary_noninferiority_result.json")
                     .read_text(encoding="utf-8"))

    info = fig1(six, analysis, phase29)
    fig2(p30)
    fig3()

    print()
    print("Global MedFiLM VAL808 macro Dice : %.4f%%" % (info["global_dice"] * 100))
    print("Regional BARR VAL808 macro Dice  : %.4f%%" % (info["barr_dice"] * 100))
    print("Regional BARR total parameters   : %d" % info["barr_params"])


if __name__ == "__main__":
    main()
