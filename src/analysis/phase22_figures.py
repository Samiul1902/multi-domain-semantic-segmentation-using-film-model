"""Phase 22 — figures.

Deterministic matplotlib rendering (Agg backend, fixed dpi, no timestamps, no
random layout). Every figure is rebuilt from persisted artifacts; nothing here
performs inference or training.

Figures are grouped so the inventory can be filtered:

    atlas       global failure atlas: distributions and taxonomy
    scale       scale-sensitivity curves
    regional    regional intervention: gain distribution, harm, ROI geometry
    routing     routing regret and the resource frontier
    resource    compute envelopes and the six-model compute gap
    kub         KUB size strata and the TINY stratum
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
from src.analysis import phase22_common as C  # noqa: E402

FIG = C.FIGURES
FIG.mkdir(parents=True, exist_ok=True)

DOMAIN_COLOR = {"ISIC": "#2b6cb0", "BUSI": "#c05621",
                "KVASIR": "#2f855a", "KUB": "#6b46c1", "ALL": "#4a5568"}

_INVENTORY: list[dict] = []


def _save(fig, name: str, group: str, caption: str) -> str:
    out = FIG / f"{name}.png"
    fig.tight_layout()
    fig.savefig(out, dpi=120, facecolor="white")
    plt.close(fig)
    _INVENTORY.append({"name": name, "group": group, "file": str(out.relative_to(ROOT)),
                       "caption": caption})
    return str(out)


def _load(p):
    p = Path(p)
    return pd.read_csv(p) if p.exists() else pd.DataFrame()


def _json(p):
    p = Path(p)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


# --------------------------------------------------------------------------- #
def fig_atlas_dice_distribution() -> None:
    df = _load(C.TABLES / "phase22_global_failure_atlas.csv")
    if df.empty:
        return
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.4))
    order = C.DATASET_ORDER
    # matplotlib 3.11 removed Axes.boxplot(labels=...); use tick_labels= when available
    # and fall back to set_xticklabels otherwise, so the builder works on both.
    try:
        axes[0].boxplot([df[df.dataset == d]["dice"].values for d in order],
                        tick_labels=order, showfliers=True)
    except TypeError:
        axes[0].boxplot([df[df.dataset == d]["dice"].values for d in order],
                        showfliers=True)
        axes[0].set_xticklabels(order)
    axes[0].set_ylabel("per-image Dice")
    axes[0].set_title("Per-image Dice by domain (frozen reference)")
    axes[0].grid(alpha=0.25)
    for i, d in enumerate(order, 1):
        s = df[df.dataset == d]["dice"]
        axes[0].text(i, s.median(), f"{s.median():.3f}", ha="center",
                     va="bottom", fontsize=8)
    axes[1].hist(df["dice"], bins=40, color="#4a5568", alpha=0.85)
    axes[1].axvline(df["dice"].median(), color="#c53030", ls="--",
                    label=f"median {df['dice'].median():.3f}")
    axes[1].set_xlabel("per-image Dice")
    axes[1].set_ylabel("count")
    axes[1].set_title("Pooled Dice distribution (808 VAL)")
    axes[1].legend()
    axes[1].grid(alpha=0.25)
    _save(fig, "p22_atlas_dice_distribution", "atlas",
          "Per-image Dice distribution by domain and pooled.")


def fig_atlas_taxonomy() -> None:
    d = _json(C.AUDITS / "phase22_global_failure_atlas.json")
    if not d:
        return
    counts = d.get("taxonomy_counts", {})
    if not counts:
        return
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.4))
    names = list(counts)
    vals = [counts[k] for k in names]
    cols = ["#2f855a" if k == "GOOD" else "#c53030" for k in names]
    axes[0].barh(names, vals, color=cols, alpha=0.9)
    axes[0].set_xlabel("count")
    axes[0].set_title("Failure taxonomy (808 VAL)")
    for i, v in enumerate(vals):
        axes[0].text(v, i, f" {v}", va="center", fontsize=8)
    axes[0].grid(alpha=0.25, axis="x")

    tax = _load(C.TABLES / "phase22_failure_taxonomy.csv")
    if not tax.empty:
        pct_cols = [c for c in tax.columns if c.endswith("_pct")]
        bottom = np.zeros(len(tax))
        for c in pct_cols:
            axes[1].bar(tax["dataset"], tax[c], bottom=bottom, label=c[:-4],
                        alpha=0.9)
            bottom += tax[c].values
        axes[1].set_ylabel("% of domain")
        axes[1].set_title("Failure mode composition by domain")
        axes[1].legend(fontsize=7, ncol=2)
        axes[1].grid(alpha=0.25, axis="y")
    _save(fig, "p22_atlas_taxonomy", "atlas",
          "Failure taxonomy counts overall and composition by domain.")


def fig_atlas_worst_cases() -> None:
    w = _load(C.TABLES / "phase22_worst_cases_per_domain.csv")
    if w.empty:
        return
    fig, ax = plt.subplots(figsize=(11, 4.6))
    x = np.arange(len(w))
    colors = [DOMAIN_COLOR.get(d, "#4a5568") for d in w["dataset"]]
    ax.bar(x, w["dice"], color=colors, alpha=0.9)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{r.dataset[:3]}\n{i}" for i, r in
                        zip(w["rank_within_domain"], w.itertuples())], fontsize=6)
    ax.set_ylabel("Dice")
    ax.set_title("Ten worst-Dice cases per domain (frozen reference)")
    ax.grid(alpha=0.25, axis="y")
    handles = [plt.Rectangle((0, 0), 1, 1, color=v) for v in DOMAIN_COLOR.values()
               if v is not None]
    ax.legend(handles, list(DOMAIN_COLOR), fontsize=8)
    _save(fig, "p22_atlas_worst_cases", "atlas",
          "Ten worst-Dice cases per domain.")


# --------------------------------------------------------------------------- #
def fig_scale_curve() -> None:
    s = _load(C.TABLES / "phase22_scale_sensitivity.csv")
    if s.empty:
        return
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.4))
    s = s.sort_values("probe_size")
    axes[0].plot(s["probe_size"], s["macro_domain_dice_native"], "o-",
                 color="#2b6cb0", lw=2)
    for _, r in s.iterrows():
        axes[0].annotate(f"{r['macro_domain_dice_native']:.4f}",
                         (r["probe_size"], r["macro_domain_dice_native"]),
                         textcoords="offset points", xytext=(0, 8),
                         ha="center", fontsize=8)
    axes[0].axvline(512, color="#a0aec0", ls=":", lw=1)
    axes[0].set_xscale("log", base=2)
    axes[0].set_xticks(sorted(set(s["probe_size"])))
    axes[0].set_xticklabels([str(int(v)) for v in sorted(set(s["probe_size"]))])
    axes[0].set_xlabel("input resolution (px)")
    axes[0].set_ylabel("macro-domain Dice (native space)")
    axes[0].set_title("Scale sensitivity (trained at 512)")
    axes[0].grid(alpha=0.25)

    for d in C.DATASET_ORDER:
        col = f"dice_{d}"
        if col in s.columns:
            axes[1].plot(s["probe_size"], s[col], "o-",
                         color=DOMAIN_COLOR[d], label=d)
    axes[1].axvline(512, color="#a0aec0", ls=":", lw=1)
    axes[1].set_xscale("log", base=2)
    axes[1].set_xticks(sorted(set(s["probe_size"])))
    axes[1].set_xticklabels([str(int(v)) for v in sorted(set(s["probe_size"]))])
    axes[1].set_xlabel("input resolution (px)")
    axes[1].set_ylabel("per-domain Dice (native space)")
    axes[1].set_title("Per-domain scale sensitivity")
    axes[1].legend(fontsize=8)
    axes[1].grid(alpha=0.25)
    _save(fig, "p22_scale_curve", "scale",
          "Scale sensitivity of the frozen 512-trained reference at 256/512/768/1024.")


def fig_scale_delta_ci() -> None:
    s = _load(C.TABLES / "phase22_scale_sensitivity.csv")
    if s.empty or "delta_ci_low" not in s.columns:
        return
    s = s[s["probe_size"] != 512].sort_values("probe_size")
    fig, ax = plt.subplots(figsize=(8, 4.2))
    y = np.arange(len(s))
    ax.errorbar(s["macro_domain_dice_delta_vs_512"], y,
                xerr=[s["macro_domain_dice_delta_vs_512"] - s["delta_ci_low"],
                      s["delta_ci_high"] - s["macro_domain_dice_delta_vs_512"]],
                fmt="o", color="#2b6cb0", capsize=5, lw=2)
    ax.axvline(0, color="#c53030", ls="--", lw=1)
    ax.set_yticks(y)
    ax.set_yticklabels([f"{int(v)} px" for v in s["probe_size"]])
    ax.set_xlabel("Δ macro-domain Dice vs 512 (95% paired CI)")
    ax.set_title("Scale delta with paired CIs (native space)")
    ax.grid(alpha=0.25, axis="x")
    _save(fig, "p22_scale_delta_ci", "scale",
          "Paired Δ Dice against the 512 reference, with 95% CIs.")


# --------------------------------------------------------------------------- #
def fig_regional_gain_distribution() -> None:
    r = _load(C.TABLES / "phase22_regional_intervention_per_image.csv")
    if r.empty:
        return
    ok = r[r["oracle_status"] == "OK"]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.4))
    d = ok["oracle_delta_dice"]
    axes[0].hist(d, bins=50, color="#2f855a", alpha=0.85)
    axes[0].axvline(0, color="#c53030", ls="--", lw=1.5)
    axes[0].axvline(d.mean(), color="#2b6cb0", ls="-", lw=1.5,
                    label=f"mean {d.mean():+.4f}")
    axes[0].set_xlabel("Δ Dice (regional oracle − global)")
    axes[0].set_ylabel("count")
    axes[0].set_title(f"Oracle regional gain (n={len(ok)})")
    axes[0].legend()
    axes[0].grid(alpha=0.25)

    axes[1].scatter(ok["global_dice"], ok["oracle_delta_dice"],
                    c=[DOMAIN_COLOR.get(x, "#4a5568") for x in ok["dataset"]],
                    s=14, alpha=0.75)
    axes[1].axhline(0, color="#c53030", ls="--", lw=1)
    axes[1].set_xlabel("baseline global Dice")
    axes[1].set_ylabel("Δ Dice")
    axes[1].set_title("Gain vs baseline difficulty")
    axes[1].grid(alpha=0.25)
    _save(fig, "p22_regional_gain_distribution", "regional",
          "Distribution of the oracle regional gain and its relation to baseline Dice.")


def fig_regional_harm() -> None:
    h = _json(C.AUDITS / "phase22_harm_analysis.json")
    if not h:
        return
    rows = h.get("harm_by_domain", [])
    if not rows:
        return
    fig, ax = plt.subplots(figsize=(9, 4.2))
    x = np.arange(len(rows))
    ax.bar(x - 0.2, [r["harm_rate"] * 100 for r in rows], width=0.4,
           color="#c53030", alpha=0.85, label="harm rate (%)")
    ax.bar(x + 0.2, [r["n_harmed"] for r in rows], width=0.4,
           color="#dd6b20", alpha=0.85, label="n harmed")
    ax.set_xticks(x)
    ax.set_xticklabels([r["dataset"] for r in rows])
    ax.set_title(f"Harm from the oracle regional arm "
                 f"(overall {h.get('n_harmed')}/{h.get('n_executed')})")
    ax.legend()
    ax.grid(alpha=0.25, axis="y")
    _save(fig, "p22_regional_harm", "regional",
          "Harm rate and harm count per domain for the oracle regional arm.")


def fig_regional_roi_geometry() -> None:
    g = _load(C.TABLES / "phase22_roi_geometry.csv")
    if g.empty:
        return
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.4))
    axes[0].hist(g["roi_area_fraction"] * 100, bins=40, color="#6b46c1",
                 alpha=0.85)
    axes[0].set_xlabel("ROI area (% of image)")
    axes[0].set_ylabel("count")
    axes[0].set_title("Oracle ROI footprint")
    axes[0].grid(alpha=0.25)

    axes[1].scatter(g["roi_area_fraction"] * 100, g["effective_magnification"],
                    s=12, alpha=0.6, color="#2b6cb0")
    axes[1].set_xlabel("ROI area (% of image)")
    axes[1].set_ylabel("effective magnification (512 / ROI side)")
    axes[1].set_title("Magnification vs ROI footprint")
    axes[1].grid(alpha=0.25)
    _save(fig, "p22_regional_roi_geometry", "regional",
          "Oracle ROI footprint and the resulting effective magnification.")


# --------------------------------------------------------------------------- #
def fig_routing_regret() -> None:
    p = _load(C.TABLES / "phase22_routing_regret.csv")
    if p.empty:
        return
    p = p.sort_values("macroR_dice_pooled")
    fig, ax = plt.subplots(figsize=(11, 4.6))
    cols = ["#2f855a" if s else "#2b6cb0" for s in p["deployable_shape"]]
    ax.barh(p["policy"], p["macroR_dice_pooled"], color=cols, alpha=0.9)
    base = float(p.loc[p.policy == "ALWAYS_GLOBAL", "macroR_dice_pooled"].iloc[0])
    ax.axvline(base, color="#c53030", ls="--", lw=1.2,
               label=f"always-global {base:.4f}")
    ax.set_xlabel("pooled VAL Dice")
    ax.set_title("Routing policies (green = deployable shape, blue = uses ground truth)")
    for i, v in enumerate(p["macroR_dice_pooled"]):
        ax.text(v, i, f" {v:.4f}", va="center", fontsize=8)
    ax.legend(fontsize=8)
    ax.grid(alpha=0.25, axis="x")
    _save(fig, "p22_routing_regret", "routing",
          "Pooled Dice of each routing policy against the always-global baseline.")


def fig_resource_frontier() -> None:
    f = _load(C.TABLES / "phase22_resource_frontier.csv")
    if f.empty:
        return
    fig, ax = plt.subplots(figsize=(10, 4.8))
    for _, r in f.iterrows():
        col = "#c53030" if "ORACLE" in r["policy"] else "#2b6cb0"
        ax.scatter(r["mean_macs_gmacs"], r["pooled_dice"], s=90, color=col,
                   zorder=3,
                   marker="D" if r["policy"] == "ORACLE_ACCEPT_IF_BENEFICIAL" else "o")
        ax.annotate(r["policy"], (r["mean_macs_gmacs"], r["pooled_dice"]),
                    textcoords="offset points", xytext=(6, 5), fontsize=7)
    ax.set_xlabel("expected G MACs per image")
    ax.set_ylabel("pooled VAL Dice")
    ax.set_title("Resource frontier (red = uses ground truth)")
    ax.grid(alpha=0.25)
    _save(fig, "p22_resource_frontier", "routing",
          "Pooled Dice versus expected compute for each routing policy.")


# --------------------------------------------------------------------------- #
def fig_resource_envelopes() -> None:
    e = _load(C.TABLES / "phase22_conditional_compute_envelopes.csv")
    if e.empty:
        return
    e = e.sort_values("mean_macs_gmacs")
    fig, ax = plt.subplots(figsize=(11, 4.4))
    x = np.arange(len(e))
    cols = ["#c53030" if "ORACLE" in p else "#2b6cb0" for p in e["policy"]]
    ax.bar(x, e["multiplier_vs_always_global"], color=cols, alpha=0.9)
    ax.axhline(1.0, color="#4a5568", ls="--", lw=1)
    ax.set_xticks(x)
    ax.set_xticklabels([p.replace("_", "\n") for p in e["policy"]], fontsize=7)
    ax.set_ylabel("compute multiplier vs always-global")
    ax.set_title("Conditional-compute envelopes")
    ax.grid(alpha=0.25, axis="y")
    _save(fig, "p22_resource_envelopes", "resource",
          "Expected compute of each routing policy as a multiple of always-global.")


def fig_resource_six_model() -> None:
    s = _load(C.TABLES / "phase21_six_model_compute.csv")
    if s.empty:
        return
    s = s.sort_values("gmacs")
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.6))
    cols = ["#2f855a" if m == "global_medfilm" else "#4a5568"
            for m in s["model_key"]]
    axes[0].barh(s["display_name"], s["gmacs"], color=cols, alpha=0.9)
    axes[0].set_xlabel("G MACs @ 1x3x512x512 (analytical lower bound)")
    axes[0].set_title("Compute of the six-model panel")
    for i, v in enumerate(s["gmacs"]):
        axes[0].text(v, i, f" {v:.2f}", va="center", fontsize=8)
    axes[0].grid(alpha=0.25, axis="x")

    axes[1].barh(s["display_name"], s["params"] / 1e6, color=cols, alpha=0.9)
    axes[1].set_xlabel("parameters (millions)")
    axes[1].set_title("Parameters of the six-model panel")
    for i, v in enumerate(s["params"] / 1e6):
        axes[1].text(v, i, f" {v:.3f}M", va="center", fontsize=8)
    axes[1].grid(alpha=0.25, axis="x")
    _save(fig, "p22_resource_six_model", "resource",
          "Six-model compute and parameter panel with the reference highlighted.")


# --------------------------------------------------------------------------- #
def fig_kub_strata() -> None:
    k = _load(C.TABLES / "phase22_kub_tiny_analysis.csv")
    if k.empty or "stratum" not in k.columns:
        return
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.4))
    order = [s for s in ("TINY", "SMALL", "MEDIUM", "LARGE",
                         "ROI_NOT_PRIMARY_BINNED") if s in set(k["stratum"])]
    k = k.set_index("stratum").reindex(order).reset_index()
    axes[0].bar(k["stratum"], k["mean_dice"], color="#6b46c1", alpha=0.9)
    for i, r in k.iterrows():
        axes[0].text(i, r["mean_dice"], f"{r['mean_dice']:.3f}", ha="center",
                     va="bottom", fontsize=8)
        axes[0].text(i, 0.01, f"n={int(r['n'])}", ha="center", fontsize=7,
                     color="white")
    axes[0].set_ylabel("mean Dice")
    axes[0].set_title("KUB Dice by frozen size stratum")
    axes[0].tick_params(axis="x", labelrotation=20)
    axes[0].grid(alpha=0.25, axis="y")

    axes[1].bar(k["stratum"], k["n_dice_below_0p5"], color="#c53030", alpha=0.9)
    axes[1].set_ylabel("count of cases with Dice < 0.5")
    axes[1].set_title("Low-Dice burden by stratum")
    axes[1].tick_params(axis="x", labelrotation=20)
    axes[1].grid(alpha=0.25, axis="y")
    _save(fig, "p22_kub_strata", "kub",
          "Frozen KUB size strata: mean Dice and low-Dice burden.")


def fig_uncertainty_vs_benefit() -> None:
    """Do DEPLOYABLE signals predict where the regional arm helps?

    SEMANTIC REPAIR (post-freeze, presentation-only)
    ------------------------------------------------
    The original version of this figure read the frozen
    ``phase22_uncertainty_vs_benefit.json`` and plotted
    ``ranked_abs_spearman`` under the title "Do deployable signals predict
    where the regional arm helps?".  That ranking mixed ground-truth-derived
    quantities (``recall``, ``dice``, ``iou``, ``precision``, ``mce``, ...)
    with genuinely deployable ones and put ``recall`` at the top — a metric a
    deployment can never compute.

    The primary panel is now rendered from the corrected GT-free table
    ``reports/tables/phase22_gt_free_proxy_vs_benefit.csv``, which contains
    deployable signals ONLY (``uses_GT=false``, available before refinement
    and at inference time).  The GT-derived quantities are shown in a second
    panel that is explicitly labelled ``POST_HOC_GT_AWARE_DIAGNOSTIC`` so they
    can never be mistaken for routable signals.

    Both source tables are persisted artifacts of the post-freeze semantic
    repair; this function performs NO inference and reads NO probability maps.
    """
    gtfree = _load(C.TABLES / "phase22_gt_free_proxy_vs_benefit.csv")
    if gtfree.empty or "spearman_r" not in gtfree.columns:
        raise FileNotFoundError(
            "GT-free proxy table missing or malformed: "
            f"{C.TABLES / 'phase22_gt_free_proxy_vs_benefit.csv'}"
        )
    if "uses_GT" in gtfree.columns:
        leaked = gtfree[gtfree["uses_GT"].astype(str).str.lower() != "false"]
        if len(leaked):
            raise ValueError(
                "GT-free proxy table contains GT-derived rows: "
                f"{sorted(leaked['signal'])}"
            )
    r = gtfree.sort_values("spearman_r").reset_index(drop=True)

    gtaware = _load(C.TABLES / "phase22_gt_aware_posthoc_associations.csv")
    non_trivial = pd.DataFrame()
    if not gtaware.empty and "spearman_r" in gtaware.columns:
        non_trivial = gtaware[gtaware["spearman_r"].abs() < 1.0].copy()
        non_trivial = non_trivial.sort_values("spearman_r").reset_index(drop=True)

    ncol = 2 if len(non_trivial) else 1
    fig, axes = plt.subplots(1, ncol, figsize=(7.0 * ncol, 5.0))
    axes = np.atleast_1d(axes)

    # ---- panel 1: DEPLOYABLE (GT-free) signals -------------------------- #
    ax = axes[0]
    y = np.arange(len(r))
    ax.barh(y, r["spearman_r"], color="#2b6cb0", alpha=0.9)
    ax.set_yticks(y)
    ax.set_yticklabels(r["signal"], fontsize=8)
    ax.axvline(0, color="#4a5568", lw=1)
    ax.set_xlabel("Spearman ρ with oracle regional gain")
    ax.set_title("DEPLOYABLE signals only (GT-free)", fontsize=10)
    lo = min(-0.08, float(r["spearman_r"].min()) - 0.02)
    hi = max(0.08, float(r["spearman_r"].max()) + 0.02)
    ax.set_xlim(lo, hi)
    for i, v in enumerate(r["spearman_r"]):
        ax.text(v + (0.002 if v >= 0 else -0.002), i, f"{v:+.4f}",
                va="center", ha="left" if v >= 0 else "right", fontsize=7)
    best = r.iloc[int(r["spearman_r"].abs().argmax())]
    ax.text(0.5, -0.20,
            f"best |ρ| = {abs(best['spearman_r']):.4f} ({best['signal']}) — "
            "weak; descriptive only, no threshold fitted",
            transform=ax.transAxes, ha="center", va="top", fontsize=8,
            color="#742a2a",
            bbox=dict(boxstyle="round,pad=0.35", fc="#fff5f5", ec="#c53030",
                      lw=0.8))
    ax.grid(alpha=0.25, axis="x")

    # ---- panel 2: GT-AWARE post-hoc diagnostic -------------------------- #
    if len(non_trivial):
        ax2 = axes[1]
        y2 = np.arange(len(non_trivial))
        ax2.barh(y2, non_trivial["spearman_r"], color="#c53030", alpha=0.9)
        ax2.set_yticks(y2)
        ax2.set_yticklabels(non_trivial["signal"], fontsize=8)
        ax2.axvline(0, color="#4a5568", lw=1)
        ax2.set_xlabel("Spearman ρ with oracle regional gain")
        ax2.set_title("POST_HOC_GT_AWARE_DIAGNOSTIC\n"
                      "(NOT deployable — requires ground truth)", fontsize=10)
        for i, v in enumerate(non_trivial["spearman_r"]):
            ax2.text(v + (0.008 if v >= 0 else -0.008), i,
                     f"{v:+.4f}", va="center",
                     ha="left" if v >= 0 else "right", fontsize=7)
        lim = float(non_trivial["spearman_r"].abs().max()) + 0.06
        ax2.set_xlim(-lim, lim)
        ax2.grid(alpha=0.25, axis="x")

    _save(fig, "p22_uncertainty_vs_benefit", "regional",
          "LEFT: deployable (GT-free) signal association with oracle regional gain. "
          "RIGHT (where shown): POST_HOC_GT_AWARE_DIAGNOSTIC associations, which "
          "require ground truth and are NOT deployable.")


def fig_scale_vs_regional() -> None:
    s = _json(C.AUDITS / "phase22_scale_vs_regional.json")
    if not s:
        return
    axes_d = s.get("axes", {})
    pts = []
    for k, v in axes_d.items():
        dice = v.get("macro_domain_dice", v.get("mean_pooled_dice"))
        cost = v.get("relative_cost_vs_512", v.get("relative_cost_vs_512_always_global"))
        if dice is None or cost is None:
            continue
        family = "SCALE" if v.get("axis") == "SCALE" else (
            "BASELINE" if v.get("axis") == "BASELINE" else "REGIONAL")
        pts.append({"label": k, "dice": dice, "cost": cost, "family": family,
                    "gt": bool(v.get("uses_ground_truth", False))})
    if not pts:
        return
    p = pd.DataFrame(pts)
    fig, ax = plt.subplots(figsize=(9, 5))
    fam_col = {"SCALE": "#2b6cb0", "REGIONAL": "#2f855a", "BASELINE": "#4a5568"}
    for _, r in p.iterrows():
        ax.scatter(r["cost"], r["dice"], s=110, color=fam_col[r["family"]],
                   marker="D" if r["gt"] else "o", zorder=3)
        ax.annotate(r["label"], (r["cost"], r["dice"]),
                    textcoords="offset points", xytext=(6, 6), fontsize=8)
    ax.set_xlabel("relative compute vs always-global 512")
    ax.set_ylabel("Dice")
    ax.set_title("Scale axis vs regional axis (diamond = uses ground truth)")
    ax.grid(alpha=0.25)
    _save(fig, "p22_scale_vs_regional", "resource",
          "Dice versus relative compute for the scale and regional axes.")


# --------------------------------------------------------------------------- #
BUILDERS = [
    ("p22_atlas_dice_distribution", fig_atlas_dice_distribution),
    ("p22_atlas_taxonomy", fig_atlas_taxonomy),
    ("p22_atlas_worst_cases", fig_atlas_worst_cases),
    ("p22_scale_curve", fig_scale_curve),
    ("p22_scale_delta_ci", fig_scale_delta_ci),
    ("p22_regional_gain_distribution", fig_regional_gain_distribution),
    ("p22_regional_harm", fig_regional_harm),
    ("p22_regional_roi_geometry", fig_regional_roi_geometry),
    ("p22_routing_regret", fig_routing_regret),
    ("p22_resource_frontier", fig_resource_frontier),
    ("p22_resource_envelopes", fig_resource_envelopes),
    ("p22_resource_six_model", fig_resource_six_model),
    ("p22_kub_strata", fig_kub_strata),
    ("p22_uncertainty_vs_benefit", fig_uncertainty_vs_benefit),
    ("p22_scale_vs_regional", fig_scale_vs_regional),
]


# --------------------------------------------------------------------------- #
# Explicit figure manifest (§6 of the reviewer visual-integrity repair).
#
# Every figure the reviewer package REQUIRES is declared here, together with its
# section, caption, semantic role and whether it must be embedded in the
# notebook. ``build_all`` FAILS CLOSED: if any required figure cannot be built,
# written, decoded and dimension-checked, the build raises instead of printing
# "figure unavailable" and continuing.
#
# ``semantic_role`` values
#   GT_FREE_DEPLOYABLE_RANKING  deployable-only association (no ground truth)
#   POST_HOC_GT_AWARE           displayed but must be labelled GT-aware
#   DESCRIPTIVE                 purely descriptive, no significance claimed
#   CI_CAVEATED                 paired CI shown; CI includes zero somewhere
# --------------------------------------------------------------------------- #
FIG_MANIFEST: list[dict] = [
    {"figure_id": "p22_atlas_dice_distribution", "section": 6,
     "semantic_role": "DESCRIPTIVE", "expected_to_embed": True,
     "uses_GT": True, "deployable_interpretation_allowed": False},
    {"figure_id": "p22_atlas_taxonomy", "section": 6,
     "semantic_role": "DESCRIPTIVE", "expected_to_embed": True,
     "uses_GT": True, "deployable_interpretation_allowed": False},
    {"figure_id": "p22_atlas_worst_cases", "section": 6,
     "semantic_role": "DESCRIPTIVE", "expected_to_embed": True,
     "uses_GT": True, "deployable_interpretation_allowed": False},
    {"figure_id": "p22_scale_curve", "section": 11,
     "semantic_role": "DESCRIPTIVE", "expected_to_embed": True,
     "uses_GT": True, "deployable_interpretation_allowed": False},
    {"figure_id": "p22_scale_delta_ci", "section": 11,
     "semantic_role": "CI_CAVEATED", "expected_to_embed": True,
     "uses_GT": True, "deployable_interpretation_allowed": False},
    {"figure_id": "p22_regional_gain_distribution", "section": 12,
     "semantic_role": "DESCRIPTIVE", "expected_to_embed": True,
     "uses_GT": True, "deployable_interpretation_allowed": False},
    {"figure_id": "p22_regional_harm", "section": 12,
     "semantic_role": "DESCRIPTIVE", "expected_to_embed": True,
     "uses_GT": True, "deployable_interpretation_allowed": False},
    {"figure_id": "p22_regional_roi_geometry", "section": 12,
     "semantic_role": "DESCRIPTIVE", "expected_to_embed": True,
     "uses_GT": True, "deployable_interpretation_allowed": False},
    {"figure_id": "p22_routing_regret", "section": 15,
     "semantic_role": "DESCRIPTIVE", "expected_to_embed": True,
     "uses_GT": True, "deployable_interpretation_allowed": False},
    {"figure_id": "p22_resource_frontier", "section": 15,
     "semantic_role": "DESCRIPTIVE", "expected_to_embed": True,
     "uses_GT": True, "deployable_interpretation_allowed": False},
    {"figure_id": "p22_resource_envelopes", "section": 15,
     "semantic_role": "DESCRIPTIVE", "expected_to_embed": True,
     "uses_GT": True, "deployable_interpretation_allowed": False},
    {"figure_id": "p22_resource_six_model", "section": 16,
     "semantic_role": "DESCRIPTIVE", "expected_to_embed": True,
     "uses_GT": False, "deployable_interpretation_allowed": False},
    {"figure_id": "p22_kub_strata", "section": 13,
     "semantic_role": "CI_CAVEATED", "expected_to_embed": True,
     "uses_GT": True, "deployable_interpretation_allowed": False},
    {"figure_id": "p22_uncertainty_vs_benefit", "section": 14,
     "semantic_role": "GT_FREE_DEPLOYABLE_RANKING", "expected_to_embed": True,
     "uses_GT": False, "deployable_interpretation_allowed": True},
    {"figure_id": "p22_scale_vs_regional", "section": 17,
     "semantic_role": "DESCRIPTIVE", "expected_to_embed": True,
     "uses_GT": True, "deployable_interpretation_allowed": False},
]
EXPECTED_N_FIGURES = len(FIG_MANIFEST)


def _check_png(path: Path) -> dict:
    """Strictly decode and verify a written PNG (fail closed on any problem)."""
    from PIL import Image as _PILImage
    if not path.exists():
        raise FileNotFoundError(f"figure not written: {path}")
    size = path.stat().st_size
    if size <= 0:
        raise ValueError(f"figure is empty: {path}")
    with _PILImage.open(path) as im:
        im.verify()
    with _PILImage.open(path) as im:
        w, h = im.size
        mode = im.mode
    if w <= 0 or h <= 0:
        raise ValueError(f"figure has degenerate dimensions: {path} {w}x{h}")
    return {"path": str(path.relative_to(ROOT)), "bytes": size,
            "width": w, "height": h, "mode": mode}


def build_all(progress=print, fail_closed: bool = True) -> list[dict]:
    """Build every declared figure and verify each written PNG.

    ``fail_closed=True`` (the default, and the only reviewed configuration)
    raises on the first builder that fails or the first PNG that cannot be
    decoded, so a partial figure set can never be silently declared a success.
    """
    _INVENTORY.clear()
    for name, fn in BUILDERS:
        try:
            fn()
        except Exception as exc:                           # noqa: BLE001
            if fail_closed:
                raise RuntimeError(
                    f"FAIL CLOSED: figure builder {name!r} raised "
                    f"{type(exc).__name__}: {exc}"
                ) from exc
            progress(f"  [fig] {name} SKIPPED: {type(exc).__name__}: {exc}")
            continue
        png = FIG / f"{name}.png"
        try:
            info = _check_png(png)
        except Exception as exc:                           # noqa: BLE001
            if fail_closed:
                raise RuntimeError(
                    f"FAIL CLOSED: figure {name!r} failed PNG verification: "
                    f"{type(exc).__name__}: {exc}"
                ) from exc
            progress(f"  [fig] {name} UNVERIFIED: {type(exc).__name__}: {exc}")
            continue
        progress(f"  [fig] {name}  {info['width']}x{info['height']} "
                 f"{info['bytes']}B")

    declared = [m["figure_id"] for m in FIG_MANIFEST]
    built = [r["name"] for r in _INVENTORY]
    if fail_closed:
        missing = [d for d in declared if d not in built]
        undeclared = [b for b in built if b not in declared]
        if missing:
            raise RuntimeError(
                f"FAIL CLOSED: required figures not built: {missing}"
            )
        if undeclared:
            raise RuntimeError(
                f"FAIL CLOSED: figures built but not declared in the manifest: "
                f"{undeclared}"
            )
    return list(_INVENTORY)


def write_inventories() -> dict:
    inv = pd.DataFrame(_INVENTORY)
    inv.to_csv(FIG / "phase22_figure_inventory.csv", index=False)
    # Manifest companion: declares every required figure with its semantic role
    # and the SHA-256 of the file actually written, so the reviewer gate can
    # bind a manifest row to a concrete on-disk payload.
    import hashlib
    rows = []
    by_name = {r["name"]: r for r in _INVENTORY}
    for m in FIG_MANIFEST:
        got = by_name.get(m["figure_id"])
        p = FIG / f"{m['figure_id']}.png"
        sha = ""
        if p.exists():
            sha = hashlib.sha256(p.read_bytes()).hexdigest()
        rows.append({**m,
                     "filename": f"{m['figure_id']}.png",
                     "built": got is not None,
                     "file": str(p.relative_to(ROOT)),
                     "source_path": str(p.relative_to(ROOT)),
                     "source_sha256": sha,
                     "caption": (got or {}).get("caption", "")})
    man = pd.DataFrame(rows)
    man.to_csv(FIG / "phase22_figure_manifest.csv", index=False)
    return {"n_figures": len(_INVENTORY),
            "n_declared": EXPECTED_N_FIGURES,
            "groups": {k: int(v) for k, v in
                       inv.groupby("group").size().items()} if len(inv) else {},
            "inventory": str((FIG / "phase22_figure_inventory.csv").relative_to(ROOT)),
            "manifest": str((FIG / "phase22_figure_manifest.csv").relative_to(ROOT))}


if __name__ == "__main__":
    built = build_all()
    print(write_inventories())
