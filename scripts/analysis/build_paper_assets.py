"""Single entry point for publication figures, tables and the asset manifest.

Partial build (default): builds everything supported by authentic artifacts and
lists pending items. --strict: exits non-zero if any essential asset is not Ready.
No result is simulated; C1 figures stay Pending until the aggregator reports a
complete, non-synthetic result.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch  # noqa: E402

from src.research.paper_assets import validation as V  # noqa: E402
import c1_results_aggregator as AGG  # noqa: E402

T = ROOT / "reports" / "tables"
FIG = ROOT / "paper_doc" / "figures"
TAB = ROOT / "paper_doc" / "tables"
MANIFEST = ROOT / "paper_asset_manifest.json"
SHORT = {"CVC-ClinicDB": "CVC", "BrEaST-Lesions-USG": "BrEaST", "Stones_where_are_you": "Stones"}
DOMAINS = ("ISIC", "BUSI", "KVASIR", "KUB")
DOMAIN_NAMES = {"ISIC": "ISIC2018", "BUSI": "BUSI-WHU", "KVASIR": "Kvasir-SEG", "KUB": "KUB-StoneX"}
COL = {"global": "#0072B2", "barr": "#D55E00", "grey": "#666666", "ok": "#009E73", "bad": "#CC79A7"}
PLOT_STYLE = {"font.family": "DejaVu Sans", "font.size": 9, "axes.titlesize": 10,
              "axes.labelsize": 9, "svg.fonttype": "none", "pdf.fonttype": 42,
              "svg.hashsalt": "ra-medfilm-barr-assets", "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 100}
plt.rcParams.update(PLOT_STYLE)
EVAL_VER = "frozen_phase21_metric_v1 (Dice/IoU on binary masks, threshold 0.5)"


def rd(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def rel(p):
    return str(Path(p).resolve().relative_to(ROOT)).replace("\\", "/")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    cols = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def save_fig(fig, name, rows=None):
    FIG.mkdir(parents=True, exist_ok=True)
    files = []
    fig.savefig(FIG / f"{name}.pdf", bbox_inches="tight", metadata={"CreationDate": None, "Creator": None, "Producer": None})
    fig.savefig(FIG / f"{name}.svg", bbox_inches="tight", metadata={"Date": None})
    fig.savefig(FIG / f"{name}.png", bbox_inches="tight", dpi=600)
    files += [rel(FIG / f"{name}.{e}") for e in ("pdf", "svg", "png")]
    if rows:
        write_csv(FIG / f"{name}_source.csv", rows)
        files.append(rel(FIG / f"{name}_source.csv"))
    plt.close(fig)
    return files


REG = {}


def ready(fid, title, files, sources, evidence, caveat):
    REG[fid] = {"title": title, "status": "READY", "files": files, "sources": sources,
                "source_sha256": {s: sha(ROOT / s) for s in sources},
                "evidence_class": evidence, "caveat": caveat}


def pending(fid, title, reason, status="PENDING_GENUINE_EXPERIMENTAL_DATA"):
    REG[fid] = {"title": title, "status": status, "reason": reason, "files": []}


def box(ax, xy, w, h, text, fc, ec="#222222", fs=8, bold=False):
    ax.add_patch(FancyBboxPatch(xy, w, h, boxstyle="round,pad=0.01,rounding_size=0.015", fc=fc, ec=ec, lw=1))
    ax.text(xy[0] + w / 2, xy[1] + h / 2, text, ha="center", va="center", fontsize=fs,
            fontweight="bold" if bold else "normal")


def arrow(ax, a, b, color="#222222", style="-|>"):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle=style, mutation_scale=10, lw=1, color=color))


# ---------------------------------------------------------------- Figure 1
def fig1():
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.add_patch(FancyBboxPatch((0.01, 0.42), 0.60, 0.55, boxstyle="round,pad=0.01", fc="#EAF2FB", ec=COL["global"], lw=1.2, ls="--"))
    ax.text(0.02, 0.95, "C1: task-conditioned FiLM", fontsize=8, color=COL["global"], va="top", fontweight="bold")
    ax.add_patch(FancyBboxPatch((0.01, 0.02), 0.98, 0.34, boxstyle="round,pad=0.01", fc="#FDF0E6", ec=COL["barr"], lw=1.2, ls="--"))
    ax.text(0.98, 0.34, "C2: budget-aware regional refinement (BARR),\napplied to selected cases only", fontsize=8, color=COL["barr"], va="top", ha="right", fontweight="bold")
    box(ax, (0.03, 0.62), 0.12, 0.14, "Image\n512x512", "white")
    box(ax, (0.03, 0.45), 0.12, 0.12, "Task ID\n(4 domains)", "white")
    box(ax, (0.20, 0.60), 0.13, 0.18, "Shared\nencoder", "#D6E6F5")
    box(ax, (0.20, 0.45), 0.13, 0.11, "Task embed.\n(32-d) + FiLM", "#B8D4EE", fs=6.5)
    box(ax, (0.38, 0.60), 0.13, 0.18, "Bridge +\nDecoder\n(4 blocks)", "#D6E6F5")
    box(ax, (0.66, 0.62), 0.30, 0.14, "Global mask (binary)", "white")
    arrow(ax, (0.15, 0.69), (0.20, 0.69)); arrow(ax, (0.15, 0.51), (0.20, 0.51))
    arrow(ax, (0.33, 0.50), (0.42, 0.60), COL["global"]); arrow(ax, (0.33, 0.69), (0.38, 0.69))
    ax.text(0.03, 0.86, "FiLM (gamma, beta) sites: bridge + decoder4-1\n(5 total); none in the encoder", fontsize=6.5, color=COL["global"], va="center")
    arrow(ax, (0.51, 0.69), (0.66, 0.69))
    box(ax, (0.34, 0.08), 0.16, 0.16, "Benefit router\nB_phi\n(budgeted)", "#F9D9C2", fs=7)
    box(ax, (0.54, 0.08), 0.14, 0.16, "ROI crop +\nregional\nrefiner", "#F9D9C2", fs=7)
    box(ax, (0.72, 0.08), 0.12, 0.16, "Safety\nfilter\nS_omega", "#F9D9C2", fs=7)
    box(ax, (0.87, 0.08), 0.11, 0.16, "Final mask:\nrefined if\naccepted", "white", fs=6)
    arrow(ax, (0.50, 0.16), (0.54, 0.16), COL["barr"]); arrow(ax, (0.68, 0.16), (0.72, 0.16), COL["barr"]); arrow(ax, (0.84, 0.16), (0.87, 0.16), COL["barr"])
    arrow(ax, (0.42, 0.60), (0.42, 0.24), COL["barr"])
    ax.text(0.03, 0.16, "Architectural specification;\nno performance values.", ha="left", va="center", fontsize=7, color=COL["grey"])
    ax.set_title("Figure 1. RA-MedFiLM-BARR overview", loc="left")
    files = save_fig(fig, "fig01_method_architecture")
    ready("fig01", "Method architecture", files, ["docs/ARCHITECTURE.md", "src/models/film/global_medfilm.py"], "specification",
          "Specification drawing; mapping to code in manuscript Methods.")


# ---------------------------------------------------------------- Figure 2
def fig2():
    val = {"ISIC": 357, "BUSI": 84, "KVASIR": 87, "KUB": 280}
    patient = {"ISIC": "not available", "BUSI": "not available", "KVASIR": "not available", "KUB": "available (111 VAL clusters)"}
    rows = [{"domain": DOMAIN_NAMES[d], "task_id": i, "val808_n": val[d], "patient_level_grouping": patient[d]}
            for i, d in enumerate(DOMAINS)]
    V.require_finite([r["val808_n"] for r in rows])
    assert sum(val.values()) == 808
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 3.1), gridspec_kw={"width_ratios": [1.1, 1]})
    a.barh([DOMAIN_NAMES[d] for d in DOMAINS][::-1], [val[d] for d in DOMAINS][::-1], color=COL["global"])
    for i, d in enumerate(DOMAINS[::-1]):
        a.text(val[d] + 5, i, f"{val[d]}  (patient IDs: {'yes' if d == 'KUB' else 'no'})", va="center", fontsize=7)
    a.set_xlim(0, 520); a.set_xlabel("Validation images (count, VAL808)")
    a.set_title("VAL808 composition")
    b.axis("off"); b.set_xlim(0, 1); b.set_ylim(0, 1)
    for k, (t, y, fc) in enumerate([("TRAIN5832 (used for training)", .86, "#D6E6F5"), ("VAL808 (selection-consumed)", .68, "#D6E6F5"),
                                    ("TEST1683 (protected, unopened)", .50, "#EEEEEE"), ("ROUTER_HOLDOUT875 (historical, no reuse)", .32, "#EEEEEE")]):
        box(b, (0.02, y - 0.06), 0.96, 0.11, t, fc, fs=7)
    box(b, (0.02, 0.02), 0.96, 0.15, "C1-T (learned FiLM) vs C1-C (frozen identity FiLM)\nseeds 42, 123, 3407 -> 6 runs; 0/6 completed", "#FDF0E6", fs=6.5)
    fig.suptitle("Figure 2. Domains, frozen splits and matched-control design", x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    files = save_fig(fig, "fig02_dataset_protocol", rows)
    ready("fig02", "Dataset and experimental protocol", files, ["reports/planning/c1_film_attribution_v1/protocol.json", "manifests/phase4_v3/val.csv"],
          "descriptive", "Counts for VAL808 per domain; ISIC/BUSI/Kvasir lack patient IDs.")


# ---------------------------------------------------------------- Figure 5
def funnel_data():
    t2 = {r["arm"]: r for r in rd(T / "phase28_table_02_arm_primary_metrics.csv")}
    total, routed = int(t2["A1"]["n_routed"]), int(t2["A7"]["n_routed"])
    adopted, ben, harm = int(t2["A8"]["n_routed"]), int(t2["A8"]["n_beneficial_routed"]), int(t2["A8"]["n_harmful_routed"])
    V.require_funnel(total, routed, adopted, routed - adopted, ben, harm)
    paired = rd(T / "c1_external_stress_paired.csv")
    V.require_unique_ids([p["sample_id"] for p in paired], "external case")
    ext = {"total": len(paired)}
    ext["attempted"] = sum(p["state"] != "NOT_ATTEMPTED" for p in paired)
    ext["adopted"] = sum(p["state"] == "ACCEPTED" for p in paired)
    ext["rejected"] = sum(p["state"] == "REJECTED" for p in paired)
    ext["improved"] = sum(p["state"] == "ACCEPTED" and p["outcome"] == "improved" for p in paired)
    ext["worsened"] = sum(p["state"] == "ACCEPTED" and p["outcome"] == "worsened" for p in paired)
    ext["unchanged"] = ext["adopted"] - ext["improved"] - ext["worsened"]
    V.require_funnel(ext["total"], ext["attempted"], ext["adopted"], ext["rejected"], ext["improved"], ext["worsened"], ext["unchanged"])
    dev = {"total": total, "attempted": routed, "adopted": adopted, "rejected": routed - adopted,
           "improved": ben, "worsened": harm, "unchanged": 0}
    return dev, ext


def fig5():
    dev, ext = funnel_data()
    rows = []
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.4))
    for ax, (name, d, note) in zip(axes, [("ROUTER_DEVELOPMENT (in-sample)", dev, "arm A8"), ("External retrospective (884 cases)", ext, "exploratory")]):
        labs = ["All cases", "Routed", "Adopted", "Rejected", "Adopted:\nimproved", "Adopted:\nworsened", "Adopted:\nunchanged"]
        vals = [d["total"], d["attempted"], d["adopted"], d["rejected"], d["improved"], d["worsened"], d["unchanged"]]
        cols = [COL["grey"], COL["barr"], COL["ok"], "#E69F00", COL["ok"], COL["bad"], "#BBBBBB"]
        ax.barh(labs[::-1], vals[::-1], color=cols[::-1])
        for i, v in enumerate(vals[::-1]):
            ax.text(v + d["total"] * 0.01, i, f"{v:,}", va="center", fontsize=7)
        ax.set_xlim(0, d["total"] * 1.3); ax.set_xlabel("Cases (count)"); ax.set_title(name, fontsize=8)
        for l, v in zip(labs, vals):
            rows.append({"panel": name, "stage": l.replace("\n", " "), "count": v})
    fig.suptitle("Figure 5. BARR routing funnel (counts; routed = adopted + rejected; outcomes are subsets of adopted)", x=0.01, ha="left", fontsize=8)
    fig.tight_layout(rect=(0, 0, 1, 0.94), w_pad=2.5)
    files = save_fig(fig, "fig05_barr_routing_safety", rows)
    ready("fig05", "BARR routing and safety funnel", files,
          ["reports/tables/phase28_table_02_arm_primary_metrics.csv", "reports/tables/c1_external_stress_paired.csv"],
          "descriptive", "Development panel is in-sample (subset of TRAIN5832); external panel exploratory. Adopted-case outcomes are conditional, not all-case averages.")
    return dev, ext


# ---------------------------------------------------------------- Figure 6
def fig6():
    rows = rd(T / "phase29_val808_seedwise_domain_metrics.csv")
    V.require_dataset_labels([r["domain"] for r in rows], DOMAINS)
    seeds = sorted({r["master_seed"] for r in rows})
    out = []
    fig, ax = plt.subplots(figsize=(7.2, 3.2))
    w = 0.38
    for i, d in enumerate(DOMAINS):
        rr = [r for r in rows if r["domain"] == d]
        g = float(rr[0]["global_dice"]); f = [float(r["final_dice"]) for r in rr]
        V.require_finite([g] + f)
        ax.bar(i - w / 2, g, w, color=COL["global"], label="GlobalMedFiLM" if i == 0 else None)
        ax.bar(i + w / 2, sum(f) / len(f), w, color=COL["barr"], label="GlobalMedFiLM + BARR (mean of 3 seeds)" if i == 0 else None)
        ax.scatter([i + w / 2] * len(f), f, c="k", s=8, zorder=3, label="Individual BARR seed" if i == 0 else None)
        for r in rr:
            out.append({"domain": DOMAIN_NAMES[d], "n": r["n"], "seed": r["master_seed"], "global_dice": r["global_dice"], "barr_dice": r["final_dice"]})
        ax.text(i, 1.02, f"n={rr[0]['n']}", ha="center", fontsize=7)
    ax.set_xticks(range(4)); ax.set_xticklabels([DOMAIN_NAMES[d] for d in DOMAINS])
    ax.set_ylim(0, 1.1); ax.set_ylabel("Dice (proportion, 0-1)")
    ax.legend(fontsize=7, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=3, frameon=False)
    ax.set_title("Figure 6. VAL808 (selection-consumed): same images, fixed global backbone; no uncertainty interval shown", loc="left", fontsize=8)
    files = save_fig(fig, "fig06_internal_performance", out)
    ready("fig06", "Internal VAL808 Global vs BARR", files, ["reports/tables/phase29_val808_seedwise_domain_metrics.csv"], "descriptive",
          "Development-selected population; global backbone fixed across seeds, so seed spread excludes backbone variability; no CI.")


# ---------------------------------------------------------------- Figure 7
def fig7():
    ds = rd(T / "c1_external_stress_domain_shift.csv")
    out = []
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 3.1), gridspec_kw={"width_ratios": [1.3, 1, 1]})
    names = [r["cohort"] for r in ds]
    short = [f"{r['cohort'].split('_')[0].split('-Lesions')[0]}\n(n={r['n']})" for r in ds]
    x = range(len(ds)); w = 0.38
    gl = [float(r["external_global_dice"]) for r in ds]; br = [float(r["external_barr_dice"]) for r in ds]
    intl = [float(r["internal_val808_dice"]) for r in ds]
    V.require_finite(gl + br + intl)
    a, b, c = axes
    a.bar([i - w / 2 for i in x], gl, w, color=COL["global"], label="Global")
    a.bar([i + w / 2 for i in x], br, w, color=COL["barr"], label="BARR")
    a.set_xticks(list(x)); a.set_xticklabels(short, fontsize=7); a.set_ylim(0, 1); a.set_ylabel("Dice (proportion)")
    a.legend(fontsize=7, frameon=False); a.set_title("Performance level", fontsize=8)
    d = [(y - g) * 100 for g, y in zip(gl, br)]
    b.bar(list(x), d, color=COL["barr"]); b.axhline(0, color="k", lw=0.8)
    brief = [s.split("\n")[0].replace("CVC-ClinicDB", "CVC").replace("BrEaST-Lesions-USG", "BrEaST") for s in short]
    b.set_xticks(list(x)); b.set_xticklabels(brief, fontsize=7)
    b.set_ylabel("BARR minus Global (Dice, pp)"); b.set_title("Difference (descriptive, no CI)", fontsize=8)
    b.set_ylim(0, max(d) * 1.2)
    for i, v in enumerate(d):
        b.text(i, v, f"{v:+.2f}", ha="center", va="bottom", fontsize=7)
    shift = [float(r["delta_vs_internal_pp"]) for r in ds]
    for g, i_, s in zip(gl, intl, shift):
        V.require_pp_label(g - i_, s, 1e-6)
    c.bar(list(x), shift, color=COL["grey"]); c.axhline(0, color="k", lw=0.8)
    c.set_xticks(list(x)); c.set_xticklabels(brief, fontsize=7)
    c.set_ylabel("Global external minus VAL808 anchor (pp)"); c.set_title("Domain shift", fontsize=8)
    for r, i, g, y, dd, s in zip(ds, x, gl, br, d, shift):
        out.append({"cohort": r["cohort"], "n": r["n"], "internal_val808_dice": r["internal_val808_dice"], "global_dice": g, "barr_dice": y,
                    "barr_minus_global_pp": dd, "global_minus_internal_pp": s})
    fig.suptitle("Figure 7. Retrospective external stress test (exploratory; not prospective validation)", x=0.01, ha="left", fontsize=9)
    fig.tight_layout()
    files = save_fig(fig, "fig07_external_stress_test", out)
    ready("fig07", "External retrospective stress test", files, ["reports/tables/c1_external_stress_domain_shift.csv"], "exploratory",
          "884 cases; Stones n=20 (14 stone-free); no pixel spacing; internal anchor is a VAL808 reference, not the same population. pp = percentage points of Dice.")


# ---------------------------------------------------------------- Figures 8, 9
def fig8():
    import matplotlib.image as mpimg
    panels = [("fig6_external_cvc.png", "CVC-ClinicDB"), ("fig7_external_breast.png", "BrEaST-Lesions-USG"), ("fig8_external_stones.png", "Stones")]
    fig, axes = plt.subplots(3, 1, figsize=(7.2, 7.5))
    rows = []
    srcs = []
    for ax, (f, t) in zip(axes, panels):
        p = ROOT / "reports" / "figures" / f
        ax.imshow(mpimg.imread(p)); ax.axis("off"); ax.set_title(t, fontsize=8, loc="left")
        rows.append({"cohort": t, "reused_panel": rel(p), "sha256": sha(p)}); srcs.append(rel(p))
    fig.suptitle("Figure 8 (supplementary overview). Reused external qualitative composites; rows chosen by rule (median/best/worst Dice;\nStones also largest/smallest lesion), including non-adopted cases. In-panel text is legible only in the full-resolution source files.", x=0.01, ha="left", fontsize=7)
    files = save_fig(fig, "fig08_qualitative_reused", rows)
    ready("fig08", "Qualitative comparisons (reused)", files, srcs, "descriptive",
          "Composites reused from reports/figures (generated by build_external_stress_figures.py with rule-based row selection). Unreadable at journal column width: supplementary only; a legible main-text qualitative figure is pending regeneration.")


def fig9():
    paired = rd(T / "c1_external_stress_paired.csv")
    st = {k: sum(1 for p in paired if (p["state"], p["outcome"]) == k) for k in
          [("ACCEPTED", "worsened"), ("ACCEPTED", "improved"), ("REJECTED", "unchanged"), ("NOT_ATTEMPTED", "unchanged")]}
    stone = [p for p in rd(T / "c1_external_stress_per_case.csv") if p["cohort_key"] == "stones" and p["arm"] == "global"]
    free = [p for p in stone if p["has_stone_annotation"] in ("False", "0", "false")]
    fp_only = sum(p["fp_only_case"] in ("True", "1", "true") for p in free)
    ds = rd(T / "c1_external_stress_domain_shift.csv")
    rows = [{"category": "Accepted refinement that improved Dice", "count": st[("ACCEPTED", "improved")], "denominator": 884},
            {"category": "Accepted refinement that worsened Dice", "count": st[("ACCEPTED", "worsened")], "denominator": 884},
            {"category": "Safety-rejected refinement", "count": st[("REJECTED", "unchanged")], "denominator": 884},
            {"category": "Not selected (unchanged)", "count": st[("NOT_ATTEMPTED", "unchanged")], "denominator": 884},
            {"category": "Stone-free images with foreground predicted (global)", "count": fp_only, "denominator": len(free)}]
    for r in rows:
        assert r["count"] <= r["denominator"]
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 3.2), gridspec_kw={"width_ratios": [1.5, 1]})
    a.barh([r["category"] for r in rows][::-1], [100 * r["count"] / r["denominator"] for r in rows][::-1], color=[COL["ok"], COL["bad"], "#E69F00", "#BBBBBB", "#000000"][::-1])
    for i, r in enumerate(rows[::-1]):
        a.text(100 * r["count"] / r["denominator"] + 1, i, f"{r['count']}/{r['denominator']}", va="center", fontsize=7)
    a.set_xlim(0, 115); a.set_xlabel("Percent of stated denominator"); a.tick_params(axis="y", labelsize=7)
    b.bar([r["cohort"].split("_")[0].split("-Lesions")[0].replace("CVC-ClinicDB", "CVC").replace("BrEaST-USG", "BrEaST") for r in ds], [float(r["delta_vs_internal_pp"]) for r in ds], color=COL["grey"])
    b.axhline(0, color="k", lw=0.8); b.set_ylabel("Global external minus VAL808 anchor (pp)"); b.tick_params(axis="x", labelsize=7); b.set_title("Domain shift", fontsize=8)
    fig.suptitle("Figure 9. Failure behavior (external retrospective cases; denominators differ by bar)", x=0.01, ha="left", fontsize=9)
    fig.tight_layout()
    files = save_fig(fig, "fig09_failure_analysis", rows)
    ready("fig09", "Failure analysis", files, ["reports/tables/c1_external_stress_paired.csv", "reports/tables/c1_external_stress_per_case.csv",
                                              "reports/tables/c1_external_stress_domain_shift.csv"], "exploratory",
          "Stone-free failure shown unhidden; per-case qualitative examples are in Figure 8's reused panels (adopted/not-adopted).")
    return rows


# ---------------------------------------------------------------- Figure 10
def fig10():
    comp = rd(T / "phase21_six_model_compute.csv")
    perf = {r["model_key"]: r for r in rd(T / "phase21_six_model_comparison.csv")}
    lat = {r["arm"]: r for r in rd(T / "phase34_batch1_latency_results_v1_4.csv")}
    ana = {r["reference"]: r for r in rd(T / "phase34_analytical_compute_summary_v1_3.csv")}
    rows = []
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 3.3))
    for r in comp:
        g = float(r["gmacs"]); dsc = float(perf[r["model_key"]]["macro_domain_dice"])
        a.scatter(g, dsc, s=max(float(r["params"]) / 1e6 * 6, 12), color=COL["global"] if r["model_key"] == "global_medfilm" else COL["grey"], alpha=0.85)
        a.annotate(r["display_name"], (g, dsc), fontsize=6, xytext=(3, 6 if r["model_key"] != "unet" else -9), textcoords="offset points")
        rows.append({"panel": "analytical", "model": r["display_name"], "params": r["params"], "analytical_gmacs": g, "macro_dice": dsc})
    a1 = float(ana["FINAL_A8_C9_EXPECTED_CONDITIONAL"]["macs"]) / 1e9
    a.axvline(float(ana["LITERAL_GLOBAL_ONLY_C1"]["macs"]) / 1e9, color=COL["global"], lw=0.5, ls=":")
    a.set_xlabel("Analytical GMACs (lower bound, not measured)"); a.set_ylabel("Macro Dice (0-1)")
    a.text(0.98, 0.03, "y-axis truncated at 0.70;\nbaselines protocol-incomparable", transform=a.transAxes, ha="right", va="bottom", fontsize=6, color=COL["grey"])
    a.set_ylim(0.7, 0.9); a.set_title("Analytical cost vs accuracy\n(marker area ~ parameters)", fontsize=8)
    labs = [("GLOBAL_ONLY_C1", "Global only"), ("SKIP_CONTROLLED_PATH", "BARR\nskip path"), ("EXECUTE_CONTROLLED_PATH", "BARR\nexecute path")]
    vals = [float(lat[k]["mean_ms"]) for k, _ in labs]; sds = [float(lat[k]["std_ms"]) for k, _ in labs]
    b.bar([l for _, l in labs], vals, yerr=sds, color=[COL["global"], COL["grey"], COL["barr"]], capsize=3)
    for i, v in enumerate(vals):
        b.text(i, v + 0.9, f"{v:.2f}", ha="center", fontsize=7)
    b.set_ylabel("Latency (ms, mean +/- SD)"); b.tick_params(axis="x", labelsize=7)
    b.set_title("Measured latency, RTX 3060 Ti\n(1000 forwards; non-end-to-end)", fontsize=8)
    for (k, l), v, s in zip(labs, vals, sds):
        rows.append({"panel": "measured_latency", "model": l, "mean_ms": v, "std_ms": s, "n": lat[k]["n"]})
    rows.append({"panel": "analytical", "model": "BARR A8 expected conditional", "analytical_gmacs": a1})
    fig.suptitle("Figure 10. Accuracy versus computational cost: analytical and measured quantities kept separate", x=0.01, ha="left", fontsize=8)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    files = save_fig(fig, "fig10_accuracy_vs_cost", [{k: r.get(k, "") for k in ("panel", "model", "params", "analytical_gmacs", "macro_dice", "mean_ms", "std_ms", "n")} for r in rows])
    ready("fig10", "Accuracy versus computational cost", files,
          ["reports/tables/phase21_six_model_compute.csv", "reports/tables/phase21_six_model_comparison.csv",
           "reports/tables/phase34_batch1_latency_results_v1_4.csv", "reports/tables/phase34_analytical_compute_summary_v1_3.csv"], "descriptive",
          "Baseline Dice values are protocol-incomparable; latency covers Global/skip/execute paths only and BARR is not shown to be cheaper than Global.")


# ---------------------------------------------------------------- Tables
def prov(source, population, n, unit, version, run, cls):
    return {"source_artifact": source, "population": population, "n": n, "metric_unit": unit,
            "evaluation_version": version, "provenance_run": run, "evidence_class": cls}


def write_table(name, rows, caption):
    for r in rows:
        V.require_provenance(r)
    TAB.mkdir(parents=True, exist_ok=True)
    write_csv(TAB / f"{name}.csv", rows)
    cols = list(rows[0].keys())
    md = [f"**{caption}**", "", "| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    md += ["| " + " | ".join(str(r[c]) for c in cols) + " |" for r in rows]
    (TAB / f"{name}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    esc = lambda s: str(s).replace("_", r"\_").replace("%", r"\%").replace("&", r"\&")
    tex = ["\\begin{tabular}{" + "l" * len(cols) + "}", "\\hline", " & ".join(esc(c) for c in cols) + " \\\\", "\\hline"]
    tex += [" & ".join(esc(r[c]) for c in cols) + " \\\\" for r in rows] + ["\\hline", "\\end{tabular}"]
    (TAB / f"{name}.tex").write_text("\n".join(tex) + "\n", encoding="utf-8")
    return [rel(TAB / f"{name}.{e}") for e in ("csv", "md", "tex")]


def tables(dev, ext, fail_rows, c1):
    out = {}
    val = {"ISIC": 357, "BUSI": 84, "KVASIR": 87, "KUB": 280}
    out["table1_dataset_splits"] = write_table("table1_dataset_splits", [
        {"domain": DOMAIN_NAMES[d], "split": "VAL808", "images": val[d], "patient_level_grouping": "available" if d == "KUB" else "not available",
         **prov("reports/planning/c1_film_attribution_v1/protocol.json", "VAL808", val[d], "count", "manifest phase4_v3", "n/a", "descriptive")} for d in DOMAINS] +
        [{"domain": "All four", "split": s, "images": n, "patient_level_grouping": "see domain rows",
          **prov("reports/planning/c1_film_attribution_v1/protocol.json", s, n, "count", "manifest phase4_v3", "n/a", "descriptive")}
         for s, n in [("TRAIN5832", 5832), ("VAL808", 808)]], "Table 1. Dataset and split description (TEST1683 and ROUTER_HOLDOUT875 not opened)")
    comp = {r["model_key"]: r for r in rd(T / "phase21_six_model_compute.csv")}
    perf = rd(T / "phase21_six_model_comparison.csv")
    out["table2_architecture_params"] = write_table("table2_architecture_params", [
        {"model": r["display_name"], "trainable_params": int(float(comp[r["model_key"]]["params"])), "gmacs_analytical": comp[r["model_key"]]["gmacs"],
         **prov("reports/tables/phase21_six_model_compute.csv", "input 1x3x512x512", 1, "parameters; GMACs (lower bound)", "phase21", "n/a", "analytical")} for r in perf],
        "Table 2. Architecture and parameter comparison")
    out["table3_c1_paired"] = write_table("table3_c1_paired", [
        {"result": c1["status"], "estimate": "NOT_ESTABLISHED" if "estimate" not in c1 else c1["estimate"],
         "runs_completed": f"{c1.get('runs_completed', 6)}/6", **prov("reports/tables/c1_results/c1_aggregate.json", "VAL808", 808, "Dice proportion difference (T-C)", "frozen protocol 531e3eb2...", "0/6 real runs", "matched")}],
        "Table 3. C1 paired attribution (pending: no real runs exist)")
    t2 = {r["arm"]: r for r in rd(T / "phase28_table_02_arm_primary_metrics.csv")}
    out["table4_c2_ablation"] = write_table("table4_c2_ablation", [
        {"arm": a, "n_routed": r["n_routed"], "budget_fraction": r["budget_fraction"], "mean_delta_dice_routed_proportion": r["mean_true_delta_dice_routed"],
         "beneficial": r["n_beneficial_routed"], "harmful": r["n_harmful_routed"], "harmful_share_of_routed_proportion": r["harmful_activation_share"],
         **prov("reports/tables/phase28_table_02_arm_primary_metrics.csv", "ROUTER_DEVELOPMENT (in-sample, subset of TRAIN5832)", 4957, "Dice proportion", "phase28 frozen ablations", "single canonical run", "descriptive")}
        for a, r in t2.items()], "Table 4. C2 routing/safety ablation (in-sample; conditional on routed set, not all-image averages)")
    out["table5_c3_baselines"] = write_table("table5_c3_baselines", [
        {"model": r["display_name"], "macro_dice_proportion": round(float(r["macro_domain_dice"]), 4), "isic": round(float(r["dice_ISIC"]), 4), "busi": round(float(r["dice_BUSI"]), 4),
         "kvasir": round(float(r["dice_KVASIR"]), 4), "kub": round(float(r["dice_KUB"]), 4), "seeds": 1,
         "protocol": "PROTOCOL_INCOMPARABLE (historical manifest v2)",
         **prov("reports/tables/phase21_six_model_comparison.csv", "VAL808 (selection-consumed)", 808, "Dice proportion", EVAL_VER, "historical single run", "descriptive")} for r in perf],
        "Table 5. Historical baseline comparison (not a controlled comparison)")
    ds = rd(T / "c1_external_stress_domain_shift.csv")
    out["table6_external"] = write_table("table6_external", [
        {"cohort": r["cohort"], "analogue": r["domain_analogue"], "n": r["n"], "global_dice": round(float(r["external_global_dice"]), 4),
         "barr_dice": round(float(r["external_barr_dice"]), 4), "barr_minus_global_pp": round((float(r["external_barr_dice"]) - float(r["external_global_dice"])) * 100, 3),
         **prov("reports/tables/c1_external_stress_domain_shift.csv", r["cohort"], r["n"], "Dice proportion; difference in pp", "c1_external_stress v1", "single retrospective evaluation", "exploratory")} for r in ds],
        "Table 6. External retrospective stress test (exploratory)")
    ana = rd(T / "phase34_analytical_compute_summary_v1_3.csv")
    lat = rd(T / "phase34_batch1_latency_results_v1_4.csv")
    out["table7_complexity"] = write_table("table7_complexity", [
        {"kind": "analytical", "item": r["reference"], "value": r["macs"] or r["formula"], "unit": "MACs",
         **prov("reports/tables/phase34_analytical_compute_summary_v1_3.csv", "canonical architecture", 1, "MACs (lower bound)", "phase34 v1.3", "n/a", "analytical")} for r in ana if r["macs"]] +
        [{"kind": "measured", "item": r["arm"], "value": round(float(r["mean_ms"]), 3), "unit": "ms (mean, batch 1)",
          **prov("reports/tables/phase34_batch1_latency_results_v1_4.csv", "RTX 3060 Ti, 1000 forwards", r["n"], "milliseconds", "phase34 v1.4", "single hardware session", "descriptive")} for r in lat],
        "Table 7. Computational complexity (analytical and measured kept separate)")
    out["table8_failures"] = write_table("table8_failures", [
        {"failure_case": r["category"], "count": r["count"], "denominator": r["denominator"],
         **prov("reports/tables/c1_external_stress_paired.csv", "external retrospective", r["denominator"], "count", "c1_external_stress v1", "single retrospective evaluation", "exploratory")} for r in fail_rows],
        "Table 8. Failure-case summary")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true", help="fail if any essential asset is not READY")
    ap.add_argument("--experiment-root", type=Path, default=AGG.DEFAULT_ROOT)
    a = ap.parse_args(argv)
    c1 = AGG.aggregate(a.experiment_root)
    AGG.write_outputs(c1, AGG.DEFAULT_OUT)
    fig1(); fig2(); dev, ext = fig5(); fig6(); fig7(); fig8(); fail = fig9(); fig10()
    tabs = tables(dev, ext, fail, c1)
    if c1["status"] == "CONFIRMED_EXECUTED_RESULT" and c1["complete"]:
        pending("fig03", "C1 paired FiLM attribution", "Real results exist; renderer for fig03 not yet implemented", "VALIDATION_FAILURE")
        pending("fig04", "C1 learning dynamics", "Real run logs exist; renderer not yet implemented", "VALIDATION_FAILURE")
    else:
        pending("fig03", "C1 paired FiLM attribution", f"C1 status {c1['status']}: {c1['runs_completed']}/6 runs completed")
        pending("fig04", "C1 learning dynamics", "No real C1 run logs exist")
    manifest = {"schema": "paper_asset_manifest_v1", "c1_status": c1["status"], "c1_runs_completed": c1.get("runs_completed"),
                "protocol_sha256": "531e3eb255a66381201d1aaf49bbe55abfdbe529640f5c584ef100d298087a61",
                "figures": REG, "tables": {k: {"status": "READY", "files": v} for k, v in tabs.items()},
                "unsupported_by_existing_evidence": ["Per-case Phase-29 BARR qualitative panels (no regenerated panels; Figure 8 reuses external panels only)"],
                "protected_data_accessed": False}
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    bad = [k for k, v in REG.items() if v["status"] != "READY"]
    print("READY:", sorted(k for k, v in REG.items() if v["status"] == "READY"), "NOT READY:", bad)
    if a.strict and bad:
        print("STRICT BUILD FAILED: essential assets not ready:", bad, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
