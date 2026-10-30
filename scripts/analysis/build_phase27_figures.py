"""Phase27 EXECUTION - deterministic RESULT figures.

Reads ONLY the frozen Phase27 Phase B artifacts (no model, no GT re-read, no
recompute) and renders:

    reports/figures/phase27_preservation/
        p27_domain_delta_forest.png        per-domain DeltaDice point + 95% CI
        p27_macro_ci_vs_margin.png         macro estimand CI vs the -0.005 margin
        p27_state_machine_activation.png   branch counts + realized activation
        p27_dice_distributions.png         global vs final-A8 Dice per domain

Usage:
    D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/build_phase27_figures.py
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(r"D:/Softfors/jup")
FIG = ROOT / "reports" / "figures" / "phase27_preservation"
FIG.mkdir(parents=True, exist_ok=True)
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"

plt.rcParams.update({
    "figure.dpi": 110, "savefig.dpi": 110, "font.family": "DejaVu Sans",
    "font.size": 10, "figure.facecolor": "white", "axes.facecolor": "white",
    "savefig.facecolor": "white", "savefig.bbox": "tight", "savefig.pad_inches": 0.22,
})

INK = "#2C2C2A"
MUTED = "#5F5E5A"
GRID = "#D9D7CE"
C_NEUTRAL = "#7A9BC4"
C_GOOD = "#5C9E5C"
C_BAD = "#C06A6A"
C_MARGIN = "#B0651C"
STRATA = ["BUSI", "ISIC", "KUB", "KVASIR"]

dom = pd.read_csv(TAB / "phase27_preservation_domain_summary.csv")
mac = pd.read_csv(TAB / "phase27_preservation_macro_bootstrap.csv").iloc[0]
res = json.loads((AUD / "phase27_preservation_result.json").read_text(encoding="utf-8"))


def _style(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=9)


# ------------------------------------------------------------------ fig 1
def fig_domain_forest():
    fig, ax = plt.subplots(figsize=(6.6, 3.2))
    order = STRATA
    ypos = np.arange(len(order))[::-1]
    for y, d in zip(ypos, order):
        r = dom[dom.domain == d].iloc[0]
        lo, pt, hi = float(r.delta_ci_lower), float(r.delta_point), float(r.delta_ci_upper)
        col = C_GOOD if lo > 0 else C_NEUTRAL
        ax.plot([lo, hi], [y, y], color=col, lw=2.2, solid_capstyle="round", zorder=2)
        ax.plot([lo, lo], [y - .10, y + .10], color=col, lw=1.4, zorder=2)
        ax.plot([hi, hi], [y - .10, y + .10], color=col, lw=1.4, zorder=2)
        ax.scatter([pt], [y], s=48, color=col, edgecolor="white", linewidth=0.8, zorder=3)
        ax.text(hi + 0.0004, y, f"{pt:+.5f}  (n={int(r.n)}, g={int(r.groups)})",
                va="center", ha="left", fontsize=8.3, color=MUTED)
    ax.axvline(0.0, color=GRID, lw=1.0, zorder=1)
    ax.axvline(-0.005, color=C_MARGIN, lw=1.2, ls="--", zorder=1)
    ax.text(-0.005, len(order) - 0.35, " margin -0.005", color=C_MARGIN,
            fontsize=8, va="top", ha="left")
    ax.set_yticks(ypos)
    ax.set_yticklabels(order, fontsize=9.5, color=INK)
    ax.set_xlabel("Dice(final_A8) - Dice(global)   [per-domain point + 95% CI]", color=MUTED)
    ax.set_title("Phase27 - per-domain preservation delta (VAL808, n=808)",
                 color=INK, fontsize=11, loc="left")
    _style(ax)
    fig.savefig(FIG / "p27_domain_delta_forest.png")
    plt.close(fig)


# ------------------------------------------------------------------ fig 2
def fig_macro_vs_margin():
    fig, ax = plt.subplots(figsize=(6.6, 2.9))
    lo, hi = float(mac.macro_ci_lower), float(mac.macro_ci_upper)
    pt = float(mac.macro_point)
    ax.axvspan(-0.005, hi + 0.001, color="#EEF3EC", zorder=0)
    ax.axvline(-0.005, color=C_MARGIN, lw=1.4, ls="--", zorder=2)
    ax.text(-0.005, 0.72, "non-inferiority margin -0.005", color=C_MARGIN,
            fontsize=8.6, va="center", ha="left", rotation=0)
    ax.plot([lo, hi], [0.35, 0.35], color=C_GOOD, lw=3.0, solid_capstyle="round", zorder=3)
    ax.scatter([pt], [0.35], s=70, color=C_GOOD, edgecolor="white", linewidth=1.0, zorder=4)
    ax.text(pt, 0.16, f"macro = {pt:+.6f}", ha="center", va="top", fontsize=9, color=INK)
    ax.text((lo + hi) / 2, 0.44, f"95% CI [{lo:+.6f}, {hi:+.6f}]",
            ha="center", va="bottom", fontsize=8.6, color=MUTED)
    ax.set_ylim(0.0, 1.0)
    ax.set_yticks([])
    ax.set_xlabel("macro-domain equal-weight mean Dice delta", color=MUTED)
    verdict = "PRESERVATION ASSERTED" if res["preservation_asserted"] else "NOT ASSERTED"
    ax.set_title(f"Phase27 - macro estimand vs margin  ({verdict})",
                 color=INK, fontsize=11, loc="left")
    _style(ax)
    fig.savefig(FIG / "p27_macro_ci_vs_margin.png")
    plt.close(fig)


# ------------------------------------------------------------------ fig 3
def fig_activation():
    act = res["per_domain"]
    sc = json.loads((AUD / "phase27_phaseB_scoring_summary.json").read_text(encoding="utf-8"))["activation"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.4, 3.2),
                                 gridspec_kw={"width_ratios": [1.3, 1.0]})
    # per-domain state stacks
    preds = pd.read_csv(TAB / "phase27_val808_predictions.csv")
    states = ["EXECUTE_THEN_ACCEPT", "EXECUTE_THEN_REJECT", "SKIP_GLOBAL", "FORCED_SKIP"]
    cols = [C_GOOD, C_MARGIN, C_NEUTRAL, "#B4B2A9"]
    ct = pd.crosstab(preds["dataset"], preds["state_machine_branch"]).reindex(STRATA).fillna(0)
    left = np.zeros(len(STRATA))
    ypos = np.arange(len(STRATA))
    for st, c in zip(states, cols):
        v = ct[st].to_numpy() if st in ct.columns else np.zeros(len(STRATA))
        a1.barh(ypos, v, left=left, color=c, label=st.replace("_", " "), height=0.58)
        left += v
    a1.set_yticks(ypos)
    a1.set_yticklabels(STRATA, fontsize=9.5, color=INK)
    a1.set_xlabel("samples", color=MUTED)
    a1.set_title("branch composition by domain", color=INK, fontsize=10, loc="left")
    a1.legend(fontsize=7.4, frameon=False, loc="lower right")
    _style(a1)
    # realized activation
    labels = ["action\navailable", "router\nexecute", "S_omega\naccept|exec", "S_omega\nreject|exec"]
    vals = [sc["action_available_fraction"], sc["router_execute_fraction"],
            sc["somega_accept_among_executed"], sc["somega_reject_among_executed"]]
    b = a2.bar(range(len(vals)), vals, color=[C_NEUTRAL, C_MARGIN, C_GOOD, C_BAD], width=0.6)
    for r, v in zip(b, vals):
        a2.text(r.get_x() + r.get_width() / 2, v + 0.02, f"{v:.3f}",
                ha="center", va="bottom", fontsize=8.4, color=INK)
    a2.axhline(0.25, color=C_MARGIN, ls="--", lw=1.1)
    a2.text(0.02, 0.27, "nominal 25% budget", color=C_MARGIN, fontsize=7.8, transform=a2.get_yaxis_transform())
    a2.set_xticks(range(len(vals)))
    a2.set_xticklabels(labels, fontsize=7.8, color=MUTED)
    a2.set_ylim(0, 1.05)
    a2.set_title("realized routing activation", color=INK, fontsize=10, loc="left")
    _style(a2)
    fig.suptitle("Phase27 - state machine activation (VAL808)", color=INK,
                 fontsize=11, x=0.02, ha="left")
    fig.savefig(FIG / "p27_state_machine_activation.png")
    plt.close(fig)


# ------------------------------------------------------------------ fig 4
def fig_dice_dist():
    sc = pd.read_csv(TAB / "phase27_val808_per_sample_scores.csv")
    fig, axes = plt.subplots(1, 4, figsize=(10.4, 2.9), sharey=True)
    for ax, d in zip(axes, STRATA):
        s = sc[sc.dataset == d]
        g = s.global_dice.astype(float).to_numpy()
        f = s.final_dice.astype(float).to_numpy()
        bins = np.linspace(min(g.min(), f.min(), 0.0), 1.0, 22)
        ax.hist(g, bins=bins, color=C_NEUTRAL, alpha=0.62, label="global")
        ax.hist(f, bins=bins, color=C_GOOD, alpha=0.52, label="final A8")
        ax.set_title(f"{d} (n={len(s)})", color=INK, fontsize=9.6)
        ax.set_xlabel("Dice", color=MUTED, fontsize=8.4)
        _style(ax)
        ax.tick_params(labelsize=7.6)
    axes[0].set_ylabel("samples", color=MUTED, fontsize=8.6)
    axes[-1].legend(fontsize=7.6, frameon=False)
    fig.suptitle("Phase27 - global vs final-A8 Dice distributions (VAL808)",
                 color=INK, fontsize=11, x=0.02, ha="left")
    fig.savefig(FIG / "p27_dice_distributions.png")
    plt.close(fig)


def main():
    fig_domain_forest()
    fig_macro_vs_margin()
    fig_activation()
    fig_dice_dist()
    for f in sorted(FIG.glob("p27_*.png")):
        print("wrote", f.relative_to(ROOT), f.stat().st_size, "bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
