"""Phase 28 -- §40 eight reviewers figures.

Figures (8)
-----------
p28_fig1_arm_matrix_overview.png          -- 13-arm mean ΔD + harmful share
p28_fig2_router_variant_vs_full.png       -- R1/R2/R3 vs A6/C7
p28_fig3_router_membership_overlap.png    -- membership Jaccard vs canonical router
p28_fig4_bootstrap_ci_forest.png          -- paired-difference forest with CI95
p28_fig5_f1_refiner_level_delta.png       -- F1 vs canonical refiner-level ΔD
p28_fig6_f1_integrated_vs_canonical.png   -- F1 integrated vs canonical A8
p28_fig7_fixed_budget_capture.png         -- benefit capture across arms at K=1239
p28_fig8_training_health.png              -- epoch histories / best epochs for 18 folds

Usage:
    ./.venv/Scripts/python.exe scripts/analysis/build_phase28_figures.py
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

AUD = ROOT / "reports" / "audits"
TABLES = ROOT / "reports" / "tables"
FIG = ROOT / "reports" / "figures"
D28 = ROOT / "data_cache" / "phase28_router_variants_v1_2"
F1_CK = ROOT / "checkpoints" / "phase28_refiner_F1_no_pglobal"
F1_EXP = ROOT / "experiments" / "phase28_refiner_F1_no_pglobal"
R_CK = {
    "R1": ROOT / "checkpoints" / "phase28_router_R1_no_deep",
    "R2": ROOT / "checkpoints" / "phase28_router_R2_no_task",
    "R3": ROOT / "checkpoints" / "phase28_router_R3_scalar_only",
}

plt.rcParams.update({"figure.dpi": 130, "savefig.dpi": 130,
                     "font.size": 9, "axes.grid": True,
                     "grid.alpha": 0.25, "axes.spines.top": False,
                     "axes.spines.right": False})


def rows_of(p: Path):
    return list(csv.DictReader(open(p, encoding="utf-8")))


def main() -> int:
    FIG.mkdir(parents=True, exist_ok=True)
    t02 = rows_of(TABLES / "phase28_table_02_arm_primary_metrics.csv")
    order = [r["arm"] for r in t02]
    mean_d = [float(r["mean_true_delta_dice_routed"]) for r in t02]
    harm_s = [float(r["harmful_activation_share"]) for r in t02]
    n_r = [int(r["n_routed"]) for r in t02]

    role_color = {"A": "#4c72b0", "R": "#dd8452", "F": "#c44e52"}

    # ---- fig 1: arm matrix overview ----
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
    cols = [role_color[a[0]] for a in order]
    ax[0].bar(order, mean_d, color=cols)
    ax[0].axhline(0, color="k", lw=0.8)
    ax[0].set_title("mean true ΔDice among routed (K=1239)")
    ax[0].set_ylabel("mean ΔDice")
    ax[0].tick_params(axis="x", rotation=90)
    ax[1].bar(order, harm_s, color=cols)
    ax[1].set_title("harmful activation share among routed")
    ax[1].set_ylabel("share")
    ax[1].tick_params(axis="x", rotation=90)
    fig.suptitle("Phase 28 — 13-arm comprehensive ablation matrix (A0–A8, R1–R3, F1)", y=1.02)
    fig.tight_layout()
    fig.savefig(FIG / "p28_fig1_arm_matrix_overview.png")
    plt.close(fig)

    # ---- fig 2: router variant vs full ----
    t03 = rows_of(TABLES / "phase28_table_03_router_variant_vs_full.csv")
    labels = [r["variant"] for r in t03]
    vv = [float(r["variant_mean_delta"]) for r in t03]
    rv = [float(r["reference_mean_delta"]) for r in t03]
    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(6.2, 4))
    ax.bar(x - 0.2, vv, 0.4, label="variant", color="#dd8452")
    ax.bar(x + 0.2, rv, 0.4, label="A6/C7 full router", color="#4c72b0")
    for i, (a, b) in enumerate(zip(vv, rv)):
        ax.annotate(f"{a-b:+.5f}", (i, max(a, b)), textcoords="offset points",
                    xytext=(0, 4), ha="center", fontsize=8)
    ax.set_xticks(x, labels)
    ax.set_ylabel("mean ΔDice (routed)")
    ax.set_title("Router ablation variants vs full router (K=1239, budget 0.25)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG / "p28_fig2_router_variant_vs_full.png")
    plt.close(fig)

    # ---- fig 3: membership overlap ----
    t04 = rows_of(TABLES / "phase28_table_04_router_membership_overlap.csv")
    labels = [r["variant"] for r in t04]
    jac = [float(r["jaccard"]) for r in t04]
    ov = [int(r["n_overlap_with_A6C7"]) for r in t04]
    fig, ax = plt.subplots(1, 2, figsize=(9, 3.8))
    ax[0].bar(labels, ov, color="#55a868")
    ax[0].set_title(f"overlap with canonical A6/C7 membership (K={t04[0]['K_reference']})")
    ax[0].set_ylabel("n overlapping samples")
    ax[1].bar(labels, jac, color="#8172b3")
    ax[1].set_title("Jaccard(variant, A6/C7)")
    ax[1].set_ylabel("Jaccard")
    fig.suptitle("Phase 28 — router variant membership overlap")
    fig.tight_layout()
    fig.savefig(FIG / "p28_fig3_router_membership_overlap.png")
    plt.close(fig)

    # ---- fig 4: bootstrap forest ----
    t08 = rows_of(TABLES / "phase28_table_08_bootstrap_statistics.csv")
    names = [r["contrast"] for r in t08]
    md = [float(r["mean_difference"]) for r in t08]
    lo = [float(r["ci95_low"]) for r in t08]
    hi = [float(r["ci95_high"]) for r in t08]
    y = np.arange(len(names))
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.errorbar(md, y, xerr=[np.array(md) - np.array(lo), np.array(hi) - np.array(md)],
                fmt="o", color="#c44e52", ecolor="#c44e52", capsize=3)
    ax.axvline(0, color="k", lw=0.9, ls="--")
    ax.set_yticks(y, names)
    ax.set_xlabel("paired mean difference (variant − reference), ΔDice")
    ax.set_title("Phase 28 — paired bootstrap contrasts (2000 reps, seed 42, CI95)")
    fig.tight_layout()
    fig.savefig(FIG / "p28_fig4_bootstrap_ci_forest.png")
    plt.close(fig)

    # ---- fig 5: F1 refiner-level ----
    rl = json.load(open(AUD / "phase28_f1_refiner_level_comparison.json", encoding="utf-8"))
    paired = rows_of(TABLES / "phase28_f1_refiner_level_paired.csv")
    dc = np.array([float(r["delta_canonical"]) for r in paired])
    df = np.array([float(r["delta_f1"]) for r in paired])
    fig, ax = plt.subplots(1, 2, figsize=(10, 4))
    ax[0].hist(dc, bins=50, alpha=0.6, label=f"canonical (μ={dc.mean():+.4f})", color="#4c72b0")
    ax[0].hist(df, bins=50, alpha=0.6, label=f"F1 (μ={df.mean():+.4f})", color="#c44e52")
    ax[0].axvline(0, color="k", lw=0.8, ls="--")
    ax[0].set_title("refiner-level ΔDice distribution (A7 membership)")
    ax[0].set_xlabel("ΔDice"); ax[0].legend(fontsize=7)
    ax[1].hist(dc - df, bins=50, color="#8172b3")
    ax[1].axvline(0, color="k", lw=0.8, ls="--")
    ax[1].axvline(rl["paired_mean_delta_difference_f1_minus_canonical"], color="r", lw=1.2,
                  ls="--", label=f"mean={rl['paired_mean_delta_difference_f1_minus_canonical']:+.4f}")
    ax[1].set_title("paired difference (canonical − F1)"); ax[1].legend(fontsize=7)
    fig.suptitle("Phase 28 — F1 refiner without p_global: refiner-level (NEGATIVE, genuine)")
    fig.tight_layout()
    fig.savefig(FIG / "p28_fig5_f1_refiner_level_delta.png")
    plt.close(fig)

    # ---- fig 6: F1 integrated vs canonical A8 ----
    fi = json.load(open(AUD / "phase28_f1_integrated_secondary.json", encoding="utf-8"))
    fig, ax = plt.subplots(figsize=(6.4, 4))
    bars = ["canonical A8\n(accept 1205)", f"F1 integrated\n(accept {fi['n_f1_accept']})"]
    vals = [fi["canonical_A8_mean_delta_dice"], fi["f1_integrated_mean_delta_dice"]]
    ax.bar(bars, vals, color=["#4c72b0", "#c44e52"])
    for i, v in enumerate(vals):
        ax.annotate(f"{v:+.5f}", (i, v), textcoords="offset points", xytext=(0, 4 if v > 0 else -12),
                    ha="center", fontsize=9)
    ax.axhline(0, color="k", lw=0.8)
    ax.set_ylabel("mean ΔDice (routed, K=1239)")
    ax.set_title("Phase 28 — F1 integrated secondary vs canonical A8\n"
                 f"paired diff {fi['paired_mean_difference_f1_minus_canonical']:+.5f} "
                 f"CI95 [{fi['paired_bootstrap_ci95'][0]:+.5f}, {fi['paired_bootstrap_ci95'][1]:+.5f}]")
    fig.tight_layout()
    fig.savefig(FIG / "p28_fig6_f1_integrated_vs_canonical.png")
    plt.close(fig)

    # ---- fig 7: fixed-budget capture ----
    cap = [float(r["benefit_capture_vs_positive_mass"]) for r in t02]
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.bar(order, cap, color=[role_color[a[0]] for a in order])
    ax.set_ylabel("benefit capture (fraction of total positive ΔDice mass)")
    ax.set_title("Phase 28 — benefit capture at fixed 25% budget (K=1239)")
    ax.tick_params(axis="x", rotation=90)
    fig.tight_layout()
    fig.savefig(FIG / "p28_fig7_fixed_budget_capture.png")
    plt.close(fig)

    # ---- fig 8: training health (18 folds) ----
    fig, axes = plt.subplots(2, 1, figsize=(11, 6))
    # router variants
    for v, col in zip(("R1", "R2", "R3"), ("#4c72b0", "#55a868", "#dd8452")):
        for k in range(5):
            hp = R_CK[v] / f"fold{k}" / "history.csv"
            if hp.exists():
                hh = rows_of(hp)
                ep = [int(r["epoch"]) for r in hh]
                es = [float(r["early_stop_huber"]) for r in hh]
                axes[0].plot(ep, es, color=col, alpha=0.5, lw=1,
                             label=v if k == 0 else None)
    axes[0].set_title("Router variant EARLY_STOP Huber loss per fold (15 runs)")
    axes[0].set_xlabel("epoch"); axes[0].set_ylabel("ES Huber"); axes[0].legend(fontsize=7)
    # F1
    for k in range(3):
        hp = F1_EXP / f"fold{k}" / "history.csv"
        if hp.exists():
            hh = rows_of(hp)
            ep = [int(r["epoch"]) for r in hh]
            es = [float(r["early_stop_loss"]) for r in hh]
            axes[1].plot(ep, es, label=f"F1 fold{k}", lw=1.2)
    axes[1].set_title("F1 refiner total loss per fold (3 runs)")
    axes[1].set_xlabel("epoch"); axes[1].set_ylabel("ES total loss"); axes[1].legend(fontsize=7)
    fig.suptitle("Phase 28 — training health (18 new folds)")
    fig.tight_layout()
    fig.savefig(FIG / "p28_fig8_training_health.png")
    plt.close(fig)

    print("8 figures written to", FIG)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
