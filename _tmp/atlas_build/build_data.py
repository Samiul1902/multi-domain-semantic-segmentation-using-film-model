"""Build the provenance-tagged data model and generated figures for the Results Atlas.

Reads only existing verified artifacts. Writes atlas_data.json + atlas_index.csv/json.
No training, no TEST access, no mutation of source artifacts.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(r"D:\Softfors\jup")
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
FIG = ROOT / "reports" / "figures"
OUT = Path(__file__).resolve().parent
GEN = OUT / "figures"
GEN.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 8.5,
    "axes.titlesize": 9.5, "axes.labelsize": 8.5,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.dpi": 200, "savefig.dpi": 220, "savefig.bbox": "tight",
})
C = {"navy": "#1f3b63", "blue": "#2e6f9e", "teal": "#2a9d8f",
     "amber": "#e9a03b", "red": "#c0504d", "grey": "#8a8f98", "light": "#dbe4ee"}

DATA = {}
TABLES = []
FIGURES = []
MISSING = []


def jload(name):
    return json.loads((AUD / name).read_text(encoding="utf-8"))


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def add_table(tid, section, title, sources, population, n, status="REAL", notes=""):
    TABLES.append({"id": tid, "type": "table", "section": section, "title": title,
                   "sources": sources if isinstance(sources, list) else [sources],
                   "population": population, "n": n, "status": status, "notes": notes})


def add_fig(fid, section, title, path, sources, population, status="REAL", notes=""):
    FIGURES.append({"id": fid, "type": "figure", "section": section, "title": title,
                    "path": str(path), "sources": sources if isinstance(sources, list) else [sources],
                    "population": population, "status": status, "notes": notes})


# --------------------------------------------------------------------------- #
# Section 1 — progression
# --------------------------------------------------------------------------- #
allm = pd.read_csv(TAB / "phase21_all_trained_models_comparison.csv")
six = pd.read_csv(TAB / "phase21_six_model_comparison.csv").set_index("model_key")
p27 = jload("phase27_preservation_result.json")
p29 = jload("phase29_phase_d_three_seed_descriptive_summary.json")

s1 = []
for _, r in allm.iterrows():
    m = r["model_key"]
    s1.append({
        "model": r["model"], "key": m, "phase": str(r["phase"]),
        "params": int(r["params"]), "gmacs": float(r["gmacs"]),
        "best_epoch": int(r["best_epoch"]), "stop_reason": r["stop_reason"],
        "macro_dice": float(r["macro_dice"]),
        "macro_iou": float(six.loc[m, "macro_domain_iou"]),
        "dice_ISIC": float(r["ISIC"]), "dice_BUSI": float(r["BUSI"]),
        "dice_KVASIR": float(r["KVASIR"]), "dice_KUB": float(r["KUB"]),
        "status": "COMPLETE",
    })
# BARR FULL (seed 42) real VAL808 macro Dice from Phase 27 per-domain points
barr_macro = float(np.mean([d["final_dice_point"] for d in p27["per_domain"]]))
s1.append({"model": "RA-MedFiLM-BARR FULL (seed 42)", "key": "barr_full", "phase": "27",
           "params": 4837420, "gmacs": 32.437902022582854, "best_epoch": None,
           "stop_reason": "n/a (diagnostic evaluation; no new training)",
           "macro_dice": barr_macro, "macro_iou": None,
           "dice_ISIC": [d["final_dice_point"] for d in p27["per_domain"] if d["domain"] == "ISIC"][0],
           "dice_BUSI": [d["final_dice_point"] for d in p27["per_domain"] if d["domain"] == "BUSI"][0],
           "dice_KVASIR": [d["final_dice_point"] for d in p27["per_domain"] if d["domain"] == "KVASIR"][0],
           "dice_KUB": [d["final_dice_point"] for d in p27["per_domain"] if d["domain"] == "KUB"][0],
           "status": "COMPLETE"})
s1.append({"model": "RA-MedFiLM-BARR LITE (depthwise)", "key": "barr_lite", "phase": "B",
           "params": 272601, "gmacs": 1.619485760, "best_epoch": None,
           "stop_reason": "n/a", "macro_dice": None, "macro_iou": None,
           "dice_ISIC": None, "dice_BUSI": None, "dice_KVASIR": None, "dice_KUB": None,
           "status": "NO_REAL_DATA_EVALUATION"})
MISSING.append({"item": "Lite real-data VAL808 macro Dice/IoU",
                "reason": "Lite pipeline real training was never executed; only synthetic chain tests exist",
                "source_checked": "src/research/lite_pipeline, reports/audits/phase_b_lite_pipeline_completion_v1_0.md",
                "status": "UNAVAILABLE"})
DATA["s1"] = {"rows": s1}
add_table("T1.1", 1, "Model progression and frozen VAL808 performance",
          ["reports/tables/phase21_all_trained_models_comparison.csv",
           "reports/tables/phase21_six_model_comparison.csv",
           "reports/audits/phase27_preservation_result.json"],
          "VAL808", 808, notes="Macro Dice = unweighted mean of four per-domain per-image mean Dice")

# Figure F1 — progression
fig, ax = plt.subplots(figsize=(6.4, 3.0))
rows = [r for r in s1 if r["macro_dice"] is not None]
rows = sorted(rows, key=lambda r: r["macro_dice"])
labels = [r["model"] for r in rows]
vals = [r["macro_dice"] for r in rows]
cols = [C["navy"] if r["key"] == "global_medfilm" else (C["teal"] if r["key"] == "barr_full" else C["blue"])
        for r in rows]
bars = ax.barh(range(len(rows)), vals, color=cols, height=.62)
ax.set_yticks(range(len(rows)))
ax.set_yticklabels(labels, fontsize=7.5)
ax.set_xlim(0.75, 0.85)
ax.set_xlabel("Macro-domain Dice (VAL808, n = 808)")
for i, (b, r) in enumerate(zip(bars, rows)):
    ax.text(b.get_width() + .0012, i, f"{r['macro_dice']:.4f}  ({r['params']/1e6:.2f}M params)",
            va="center", fontsize=6.8)
ax.set_title("Model progression — frozen VAL808 macro-domain Dice")
f1 = GEN / "F01_progression.png"; fig.savefig(f1); plt.close(fig)
add_fig("F1.1", 1, "Model progression: macro-domain Dice with parameter counts", f1,
        "reports/tables/phase21_all_trained_models_comparison.csv", "VAL808", notes="BARR FULL from Phase 27; Lite excluded (no real evaluation)")

# --------------------------------------------------------------------------- #
# Section 2 — 13-arm ablation + contrasts
# --------------------------------------------------------------------------- #
arm2 = pd.read_csv(TAB / "phase28_table_02_arm_primary_metrics.csv")
mat = jload("phase28_comprehensive_ablation_matrix.json")
roles = {a["arm"]: a["role"] for a in mat["arms"]}
defs = {a["arm"]: a["definition"] for a in mat["arms"]}
s2_arms = []
for _, r in arm2.iterrows():
    s2_arms.append({"arm": r["arm"], "role": roles.get(r["arm"], ""), "definition": defs.get(r["arm"], ""),
                    "n_routed": int(r["n_routed"]), "budget": float(r["budget_fraction"]),
                    "mean_delta": float(r["mean_true_delta_dice_routed"]),
                    "sum_delta": float(r["sum_true_delta_dice"]),
                    "n_beneficial": int(r["n_beneficial_routed"]),
                    "n_harmful": int(r["n_harmful_routed"]),
                    "harmful_share": float(r["harmful_activation_share"])})
con = pd.read_csv(TAB / "phase28_table_08_bootstrap_statistics.csv")
s2_con = []
for _, r in con.iterrows():
    s2_con.append({"contrast": r["contrast"], "reference": r["reference_arm"], "variant": r["variant_arm"],
                   "n": int(r["n"]), "mean_diff": float(r["mean_difference"]),
                   "se": float(r["se_bootstrap"]), "lo": float(r["ci95_low"]), "hi": float(r["ci95_high"]),
                   "excludes_zero": bool(r["ci95_low"] > 0 or r["ci95_high"] < 0)})
DATA["s2"] = {"arms": s2_arms, "contrasts": s2_con,
              "population": "ROUTER_DEVELOPMENT", "n": 4957, "fixed_budget_K": 1239}
add_table("T2.1", 2, "13-arm ablation matrix (arm-level point summaries)",
          ["reports/tables/phase28_table_02_arm_primary_metrics.csv",
           "reports/audits/phase28_comprehensive_ablation_matrix.json"],
          "ROUTER_DEVELOPMENT", 4957, notes="mean delta over routed rows; A0/A1 are endpoints")
add_table("T2.2", 2, "Pre-registered and descriptive paired contrasts with 95% bootstrap CIs",
          ["reports/tables/phase28_table_08_bootstrap_statistics.csv",
           "reports/tables/phase28_table_07_matched_paired_contrasts.csv"],
          "ROUTER_DEVELOPMENT", 4957,
          notes="paired bootstrap, common resampled indices; 2000 replicates, seed 42; descriptive, no post-hoc correction")

fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.0), gridspec_kw={"width_ratios": [1.55, 1]})
ax = axes[0]
order = [a["arm"] for a in s2_arms]
vals = [a["mean_delta"] for a in s2_arms]
colors = []
for a in s2_arms:
    if a["arm"] in ("A0", "A1"):
        colors.append(C["grey"])
    elif a["arm"] in ("R1", "R2", "R3"):
        colors.append(C["amber"])
    elif a["arm"] == "F1":
        colors.append(C["red"])
    else:
        colors.append(C["blue"])
bars = ax.bar(range(len(order)), vals, color=colors, width=.68)
ax.axhline(0, color="k", lw=.7)
for b, v in zip(bars, vals):
    ax.text(b.get_x() + b.get_width() / 2, v + (0.0012 if v >= 0 else -0.0018),
            f"{v:+.4f}", ha="center", va="bottom" if v >= 0 else "top", fontsize=5.6,
            rotation=90)
ax.set_xticks(range(len(order)))
ax.set_xticklabels(order, fontsize=7)
ax.set_ylabel("Mean true ΔDice (routed)")
ax.set_title("Arm-level mean ΔDice")
ax.tick_params(axis="x", rotation=0)
ax2 = axes[1]
hs = [a["harmful_share"] * 100 for a in s2_arms]
ax2.barh(range(len(order)), hs, color=[C["red"] if h > 40 else C["blue"] for h in hs], height=.62)
ax2.set_yticks(range(len(order)))
ax2.set_yticklabels(order, fontsize=7)
ax2.invert_yaxis()
ax2.set_xlabel("Harmful activation share (%)")
ax2.set_title("Harmful activation")
fig.suptitle("Phase 28 — 13-arm ablation on ROUTER_DEVELOPMENT (n = 4,957; K = 1,239)", fontsize=9.5, y=1.02)
f2 = GEN / "F02_ablation.png"; fig.savefig(f2); plt.close(fig)
add_fig("F2.1", 2, "13-arm ablation: mean ΔDice and harmful activation share", f2,
        "reports/tables/phase28_table_02_arm_primary_metrics.csv", "ROUTER_DEVELOPMENT", notes="Point estimates only; CIs in Table T2.2")

fig, ax = plt.subplots(figsize=(6.2, 2.3))
ys = np.arange(len(s2_con))
for i, c in enumerate(s2_con):
    col = C["red"] if not c["excludes_zero"] else C["navy"]
    ax.plot([c["lo"], c["hi"]], [i, i], color=col, lw=2.2, solid_capstyle="round")
    ax.plot(c["mean_diff"], i, "o", color=col, ms=5)
ax.axvline(0, color="k", lw=.8, ls="--")
ax.set_yticks(ys)
ax.set_yticklabels([c["contrast"] for c in s2_con], fontsize=7.2)
ax.invert_yaxis()
ax.set_xlabel("Paired mean difference in ΔDice (95% bootstrap CI)")
ax.set_title("Phase 28 — paired contrasts (n = 4,957); red = CI includes zero")
f3 = GEN / "F03_contrasts.png"; fig.savefig(f3); plt.close(fig)
add_fig("F2.2", 2, "Paired contrast forest plot with 95% bootstrap CIs", f3,
        "reports/tables/phase28_table_08_bootstrap_statistics.csv", "ROUTER_DEVELOPMENT", notes="A8_vs_A7 is the only frozen matched contrast")

# --------------------------------------------------------------------------- #
# Section 3 — six-model evaluation matrix
# --------------------------------------------------------------------------- #
per = pd.read_csv(TAB / "phase21_per_image_all_models.csv")
s3 = []
for _, r in six.reset_index().iterrows():
    m = r["model_key"]
    g = per[per.model_key == m]
    def macro(col):
        return float(g.groupby("dataset")[col].mean().mean())
    s3.append({"model": r["display_name"], "key": m, "phase": str(r["phase"]),
               "params": int(r["params"]) if pd.notna(r["params"]) else 3523001,
               "dice": float(r["macro_domain_dice"]), "iou": float(r["macro_domain_iou"]),
               "precision": macro("precision"), "recall": macro("recall"),
               "hd95": macro("hd95"),
               "precision_valid_n": int(g["precision"].notna().sum()),
               "hd95_valid_n": int(g["hd95_valid"].sum()),
               "dice_ISIC": float(r["dice_ISIC"]), "dice_BUSI": float(r["dice_BUSI"]),
               "dice_KVASIR": float(r["dice_KVASIR"]), "dice_KUB": float(r["dice_KUB"])})
gd = pd.read_csv(TAB / "phase21_global_medfilm_domain_performance.csv")
gd = gd[gd.row_type.isin(["DOMAIN", "MACRO_DOMAIN"])]
s3_dom = []
for _, r in gd.iterrows():
    s3_dom.append({"domain": r["dataset"], "n": int(r["n"]), "dice": float(r["dice"]),
                   "iou": float(r["iou"]), "precision": float(r["precision"]),
                   "recall": float(r["recall"]), "hd95": float(r["hd95"]),
                   "hd95_valid_n": int(r["hd95_valid_n"]),
                   "dice_ci_low": (None if pd.isna(r["dice_ci_low"]) else float(r["dice_ci_low"])),
                   "dice_ci_high": (None if pd.isna(r["dice_ci_high"]) else float(r["dice_ci_high"]))})
DATA["s3"] = {"models": s3, "global_domain": s3_dom}
add_table("T3.1", 3, "Six-model evaluation matrix (VAL808): Dice, IoU, Precision, Recall, HD95",
          ["reports/tables/phase21_six_model_comparison.csv",
           "reports/tables/phase21_per_image_all_models.csv"],
          "VAL808", 808,
          notes="Dice/IoU published macro; Precision/Recall/HD95 derived as unweighted mean of domain means from per-image table (reproduces published Dice exactly)")
add_table("T3.2", 3, "Global MedFiLM per-domain metrics with Dice 95% CI",
          "reports/tables/phase21_global_medfilm_domain_performance.csv", "VAL808", 808)

# --------------------------------------------------------------------------- #
# Section 4 — seeds
# --------------------------------------------------------------------------- #
s4 = []
for m in p29["per_metric"]:
    s4.append({"metric": m["metric"], "s42": m["seed42"], "s123": m["seed123"],
               "s3407": m["seed3407"], "mean": m["mean"], "sd": m["sample_sd_ddof1"],
               "range": m["range"], "sign_consistent": m["sign_consistent"]})
DATA["s4"] = {"metrics": s4, "gate": p29["numeric_reproducibility_pass_fail_gate"],
              "all_positive": p29["macro_delta_dice"]["all_positive"]}
add_table("T4.1", 4, "Three-seed descriptive summary (VAL808)",
          "reports/audits/phase29_phase_d_three_seed_descriptive_summary.json", "VAL808", 808,
          notes="No numeric reproducibility pass/fail gate; no best-seed selection")

fig, ax = plt.subplots(figsize=(4.6, 2.5))
seeds = ["42", "123", "3407"]
dv = [p29["macro_delta_dice"][f"seed{s}"] for s in seeds]
ax.plot(seeds, dv, "o-", color=C["navy"], lw=1.6, ms=6)
ax.axhline(p29["macro_delta_dice"]["mean"], color=C["teal"], ls="--", lw=1,
           label=f"mean {p29['macro_delta_dice']['mean']:.5f}")
ax.fill_between(range(3),
                p29["macro_delta_dice"]["mean"] - p29["macro_delta_dice"]["sample_sd_ddof1"],
                p29["macro_delta_dice"]["mean"] + p29["macro_delta_dice"]["sample_sd_ddof1"],
                color=C["teal"], alpha=.15, label="±1 SD")
ax.set_ylabel("Macro ΔDice (final − global)")
ax.set_xlabel("Seed")
ax.set_title("Phase 29 — three-seed macro ΔDice (shared frozen backbone)")
ax.legend(fontsize=6.5, frameon=False)
f4 = GEN / "F04_seeds.png"; fig.savefig(f4); plt.close(fig)
add_fig("F4.1", 4, "Three-seed macro ΔDice with mean and ±1 SD", f4,
        "reports/audits/phase29_phase_d_three_seed_descriptive_summary.json", "VAL808", notes="Seeds share the frozen global backbone; not independent")

# --------------------------------------------------------------------------- #
# Section 5 — accuracy vs compute
# --------------------------------------------------------------------------- #
compute = pd.read_csv(TAB / "phase21_six_model_compute.csv").set_index("model_key")
# Phase D table values are taken from the frozen completion report (seed 42)
lat = {
    "global_medfilm": (15.14, 322.5), "unet": (12.41, 282.8), "attention_unet": (14.06, 343.1),
    "unetpp": (35.05, 712.2), "deeplabv3plus": (16.08, 308.2), "transformer_mit_unet": (11.83, 208.6),
}
s5 = []
for r in s3:
    p50, mem = lat[r["key"]]
    s5.append({"model": r["model"], "key": r["key"], "params": r["params"],
               "gmacs": float(compute.loc[r["key"], "gmacs"]),
               "macro_dice": r["dice"], "forward_p50_ms": p50, "peak_alloc_mib": mem})
DATA["s5"] = {"rows": s5}
add_table("T5.1", 5, "Accuracy (real, VAL808) beside architectural cost and synthetic latency",
          ["reports/tables/phase21_six_model_compute.csv",
           "reports/tables/phase21_six_model_comparison.csv",
           "reports/performance/phase_d/phase_d_completion_report.md"],
          "VAL808 accuracy; SYNTHETIC_BENCHMARK latency", 808,
          status="MIXED_LABELLED", notes="Latency is SYNTHETIC_BENCHMARK (fixture weights); never a real-data result")

SHORT = {"global_medfilm": "Global MedFiLM", "deeplabv3plus": "DeepLabV3+",
         "transformer_mit_unet": "MiT U-Net", "unetpp": "U-Net++",
         "attention_unet": "Attention U-Net", "unet": "U-Net"}
OFF = {"global_medfilm": (6, 4, "left"), "deeplabv3plus": (6, 4, "left"),
       "transformer_mit_unet": (6, 4, "left"), "unetpp": (-6, 5, "right"),
       "attention_unet": (-7, 3, "right"), "unet": (7, -3, "left")}
fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.7))
ax = axes[0]
for r in s5:
    col = C["navy"] if r["model"].startswith("Global") else C["blue"]
    ax.scatter(r["gmacs"], r["macro_dice"], s=42, color=col, zorder=3)
    dx, dy, ha = OFF[r["key"]]
    ax.annotate(SHORT[r["key"]], (r["gmacs"], r["macro_dice"]), fontsize=6.2,
                xytext=(dx, dy), textcoords="offset points", ha=ha, annotation_clip=True)
ax.set_xlim(20, 160)
ax.set_ylim(0.780, 0.840)
ax.set_xlabel("Analytical GMACs @ 1×3×512×512 (lower bound)")
ax.set_ylabel("Macro Dice (VAL808)")
ax.set_title("Real accuracy vs architectural cost")
ax2 = axes[1]
names = [SHORT[r["key"]] for r in s5]
ax2.barh(range(len(s5)), [r["forward_p50_ms"] for r in s5], color=C["amber"], height=.62)
ax2.set_yticks(range(len(s5)))
ax2.set_yticklabels(names, fontsize=6.5)
ax2.invert_yaxis()
ax2.set_xlabel("Forward p50 (ms), batch 1")
ax2.set_title("SYNTHETIC_BENCHMARK latency")
fig.suptitle("Phase 21 accuracy vs Phase D synthetic cost — different evidence classes", fontsize=9.5, y=1.03)
f5 = GEN / "F05_accuracy_cost.png"; fig.savefig(f5); plt.close(fig)
add_fig("F5.1", 5, "Accuracy vs compute: real VAL808 accuracy and synthetic latency shown separately", f5,
        ["reports/tables/phase21_six_model_compute.csv", "reports/performance/phase_d/phase_d_completion_report.md"],
        "MIXED (labelled)", status="MIXED_LABELLED")

# --------------------------------------------------------------------------- #
# Section 6 — distributions
# --------------------------------------------------------------------------- #
gmed = per[per.model_key == "global_medfilm"]
q = []
for d in ["ISIC", "BUSI", "KVASIR", "KUB"]:
    v = gmed[gmed.dataset == d]["dice"].to_numpy()
    q.append({"domain": d, "n": int(v.size), "mean": float(v.mean()), "sd": float(v.std(ddof=1)),
              "p05": float(np.percentile(v, 5)), "q1": float(np.percentile(v, 25)),
              "median": float(np.median(v)), "q3": float(np.percentile(v, 75)),
              "p95": float(np.percentile(v, 95))})
DATA["s6"] = {"global_quartiles": q, "phase27": p27["per_domain"]}
add_table("T6.1", 6, "Per-domain per-image Dice distribution (Global MedFiLM, VAL808)",
          "reports/tables/phase21_per_image_all_models.csv", "VAL808", 808)

fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.7))
ax = axes[0]
data = [gmed[gmed.dataset == d]["dice"].to_numpy() for d in ["ISIC", "BUSI", "KVASIR", "KUB"]]
parts = ax.violinplot(data, showmedians=True, widths=.8)
for pc in parts["bodies"]:
    pc.set_facecolor(C["blue"]); pc.set_alpha(.55); pc.set_edgecolor(C["navy"])
ax.set_xticks(range(1, 5))
ax.set_xticklabels(["ISIC\nn=357", "BUSI\nn=84", "KVASIR\nn=87", "KUB\nn=280"], fontsize=7)
ax.set_ylabel("Per-image Dice")
ax.set_title("Global MedFiLM per-image Dice by domain")
ax2 = axes[1]
dom = [d["domain"] for d in p27["per_domain"]]
pt = [d["delta_point"] for d in p27["per_domain"]]
lo = [d["delta_ci_lower"] for d in p27["per_domain"]]
hi = [d["delta_ci_upper"] for d in p27["per_domain"]]
ax2.errorbar(range(len(dom)), pt, yerr=[np.array(pt) - np.array(lo), np.array(hi) - np.array(pt)],
             fmt="o", color=C["navy"], ecolor=C["teal"], capsize=4, ms=5)
ax2.axhline(0, color="k", lw=.7, ls="--")
ax2.set_xticks(range(len(dom)))
ax2.set_xticklabels(dom, fontsize=7)
ax2.set_ylabel("ΔDice (final − global)")
ax2.set_title("Phase 27 per-domain preservation")
fig.suptitle("Per-sample and per-domain distributions (VAL808)", fontsize=9.5, y=1.03)
f6 = GEN / "F06_distributions.png"; fig.savefig(f6); plt.close(fig)
add_fig("F6.1", 6, "Per-image Dice distributions and per-domain ΔDice with 95% CI", f6,
        ["reports/tables/phase21_per_image_all_models.csv", "reports/audits/phase27_preservation_result.json"],
        "VAL808", notes="Bootstrap CIs from Phase 27 (2000 replicates)")

# --------------------------------------------------------------------------- #
# Section 7 — interpretability + robustness (reuse published figures)
# --------------------------------------------------------------------------- #
p35 = jload("phase35_interpretability_scientific_result_v1_0.json")
p36 = json.loads((AUD / "phase36_robustness_scientific_result_v1_23.json").read_text(encoding="utf-8"))
s7_figs = []
for k in ["phase35_f1_film_gamma_heatmap", "phase35_f3_task_embedding_geometry",
          "phase35_f5_saliency_self_consistency", "phase35_f6_router_group_attribution"]:
    p = ROOT / p35["figures"][k]["png"].replace("\\", "/")
    s7_figs.append({"id": k, "path": str(p), "exists": p.exists(), "phase": 35})
for k in ["R1", "R2", "R5"]:
    p = FIG / "phase36_robustness_v1_23" / {
        "R1": "R1_image_perturbation_mean_paired_delta_dice_heatmap.png",
        "R2": "R2_severity_curves_noise_blur_resolution.png",
        "R5": "R5_worst_case_delta_dice_distribution_by_domain.png"}[k]
    s7_figs.append({"id": k, "path": str(p), "exists": p.exists(), "phase": 36})
DATA["s7"] = {"figures": s7_figs,
              "p36_worst_by_domain": p36["worst_case_by_domain"],
              "p36_counters": {k: p36["counters"][k] for k in
                               ("unique_raw_val_images", "perturbed_g_forwards", "test_reads",
                                "router_holdout_reads", "training", "optimizer_steps")},
              "p36_clean_equiv": p36["clean_equivalence"]["all_pass"]}
for _i, f in enumerate(s7_figs, 1):
    add_fig(f"F7.{_i}", 7, f"Phase {f['phase']} — {f['id']}", f["path"],
            "reports/audits/phase35_interpretability_scientific_result_v1_0.json" if f["phase"] == 35
            else "reports/audits/phase36_robustness_scientific_result_v1_23.json",
            "VAL808", notes="Published frozen figure, reused unchanged")
add_table("T7.1", 7, "Phase 36 worst-case per-sample ΔDice by domain",
          "reports/audits/phase36_robustness_scientific_result_v1_23.json", "VAL808", 808,
          notes="Development-set synthetic perturbation evidence; test_reads=0")

# --------------------------------------------------------------------------- #
# Section 8 — qualitative + failure
# --------------------------------------------------------------------------- #
ext = pd.read_csv(ROOT / "paper_doc/figures/fig08_main_qualitative_source.csv")
s8_ext = ext.to_dict("records")
DATA["s8"] = {"external_rows": s8_ext,
              "external_population": "EXTERNAL 884 (CVC 612 / BrEaST 252 / Stones 20)",
              "internal_gallery": str(FIG / "phase21_global_medfilm/gallery/gallery_six_model_KUB.png")}
add_table("T8.1", 8, "External qualitative case selection (CVC-ClinicDB examples)",
          "paper_doc/figures/fig08_main_qualitative_source.csv", "EXTERNAL 884", 884,
          notes="External retrospective cohort; not VAL808 and not TEST")
add_fig("F8.1", 8, "Six-model qualitative gallery (KUB, VAL808)", DATA["s8"]["internal_gallery"],
        "reports/figures/phase21_global_medfilm/gallery/gallery_six_model_KUB.png", "VAL808")
add_fig("F8.2", 8, "External qualitative refinement examples (CVC-ClinicDB)",
        ROOT / "paper_doc/figures/fig08_main_qualitative.png",
        "paper_doc/figures/fig08_main_qualitative_source.csv", "EXTERNAL 884")
add_fig("F8.3", 8, "External failure taxonomy counts",
        ROOT / "paper_doc/figures/fig09_failure_analysis.png",
        "paper_doc/figures/fig09_failure_analysis_source.csv", "EXTERNAL 884")

# --------------------------------------------------------------------------- #
# Section 9 — TEST
# --------------------------------------------------------------------------- #
p39 = jload("phase39_final_test_v1_2_scientific_result.json")
DATA["s9"] = {"per_domain": p39["summary"]["per_domain"], "macro_dice": p39["summary"]["macro_dice"],
              "counters": p39["counters"], "evidence_class": p39["evidence_class"],
              "access": [
                  {"revision": "v1.0", "stage": "MODEL_LOAD", "inference_started": False,
                   "reads": "0 (failed before manifest open)", "result": "NONE"},
                  {"revision": "v1.1", "stage": "SCIENCE_LOOP", "inference_started": True,
                   "reads": "partial (inference started; failed)", "result": "NONE"},
                  {"revision": "v1.2", "stage": "COMPLETE", "inference_started": True,
                   "reads": "1683 images + 1683 GT", "result": "SCIENTIFIC_RESULT"}],
              "missing_metrics": ["IoU", "Precision", "Recall", "HD95", "per-sample table"],
              "missing_endpoint": "No C1-T/C1-C, C2 ablation or C3 baseline on TEST"}
add_table("T9.1", 9, "Historical Phase 39 TEST1683 descriptive result",
          "reports/audits/phase39_final_test_v1_2_scientific_result.json", "TEST1683", 1683,
          notes="One-shot consumed; descriptive only; no comparative endpoint")
add_table("T9.2", 9, "Phase 39 access reconciliation (v1.0 / v1.1 / v1.2)",
          ["reports/audits/phase39_final_test_failure.json",
           "reports/audits/phase39_final_test_v1_1_failure.json",
           "reports/audits/phase39_final_test_v1_2_scientific_result.json"],
          "TEST1683", 1683, notes="Recent zero-read claims apply to the coding-verification session only")

fig, ax = plt.subplots(figsize=(4.8, 2.4))
doms = [d["domain"] for d in p39["summary"]["per_domain"]]
vals = [d["dice_mean"] for d in p39["summary"]["per_domain"]]
ns = [d["n"] for d in p39["summary"]["per_domain"]]
bars = ax.bar(doms, vals, color=[C["navy"], C["blue"], C["teal"], C["amber"]], width=.6)
ax.axhline(p39["summary"]["macro_dice"], color=C["red"], ls="--", lw=1,
           label=f"macro {p39['summary']['macro_dice']:.4f}")
for b, v, n in zip(bars, vals, ns):
    ax.text(b.get_x() + b.get_width()/2, v + .008, f"{v:.4f}\nn={n}", ha="center", fontsize=6.5)
ax.set_ylim(0, 1.0)
ax.set_ylabel("Dice (mean)")
ax.set_title("Phase 39 TEST1683 — descriptive per-domain Dice (one-shot)")
ax.legend(fontsize=6.5, frameon=False)
f9 = GEN / "F09_test.png"; fig.savefig(f9); plt.close(fig)
add_fig("F9.1", 9, "TEST1683 per-domain mean Dice (historical one-shot result)", f9,
        "reports/audits/phase39_final_test_v1_2_scientific_result.json", "TEST1683")

# --------------------------------------------------------------------------- #
# Section 10 — missing evidence
# --------------------------------------------------------------------------- #
s10 = [
    {"claim": "C1 FiLM attribution (C1-T vs C1-C)", "required": "6 matched runs, seeds 42/123/3407, VAL808 paired endpoint",
     "available": "0/6 runs; design + synthetic chain only", "blocker": "Institutional authorization pending (RC4 trust root absent); no licence/ethics record",
     "status": "NOT_ESTABLISHED"},
    {"claim": "C2 BARR router/safety causal ablation", "required": "pre-registered matched ablation with approval",
     "available": "BARR-M1 design ready; policy comparison only; no causal ablation", "blocker": "approval NOT APPROVED; in-sample; zero GPU",
     "status": "NOT_ESTABLISHED"},
    {"claim": "C3 protocol-faithful baseline comparison", "required": "full-protocol baseline matrix",
     "available": "EXT-03 15/15 reduced protocol only", "blocker": "no protocol-faithful runs",
     "status": "NOT_ESTABLISHED"},
]
DATA["s10"] = {"rows": s10}
add_table("T10.1", 10, "Missing-evidence matrix for C1, C2 and C3", "multiple (see report §10)",
          "n/a", 0, status="MISSING_EVIDENCE")

labels = ["Design / software", "Synthetic verification", "Real experiment", "Authorization"]
claims = ["C1 FiLM attribution", "C2 BARR causal ablation", "C3 protocol-faithful baselines"]
grid = np.array([[1, 1, 0, 0], [1, 1, 0, 0], [1, 0, 0, 0]], dtype=float)
fig, ax = plt.subplots(figsize=(5.4, 2.0))
cmap = matplotlib.colors.ListedColormap([C["red"], C["teal"]])
ax.imshow(grid, cmap=cmap, vmin=0, vmax=1, aspect="auto")
ax.set_xticks(range(4)); ax.set_xticklabels(labels, fontsize=6.8)
ax.set_yticks(range(3)); ax.set_yticklabels(claims, fontsize=7)
for i in range(3):
    for j in range(4):
        ax.text(j, i, "PRESENT" if grid[i, j] else "ABSENT", ha="center", va="center",
                fontsize=6.2, color="white", fontweight="bold")
ax.set_title("Missing-evidence matrix — C1 / C2 / C3")
ax.set_xticks(np.arange(-.5, 4, 1), minor=True)
ax.set_yticks(np.arange(-.5, 3, 1), minor=True)
ax.grid(which="minor", color="white", lw=2)
ax.tick_params(which="minor", length=0)
f10 = GEN / "F10_missing.png"; fig.savefig(f10); plt.close(fig)
add_fig("F10.1", 10, "Missing-evidence matrix for C1, C2 and C3", f10,
        "reports/audits (C1/C2/C3 evidence survey)", "n/a", status="MISSING_EVIDENCE")

# --------------------------------------------------------------------------- #
# Index + write
# --------------------------------------------------------------------------- #
git_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
DATA["meta"] = {
    "title": "RA-MedFiLM-BARR — Research Results Atlas",
    "subtitle": "Consolidated verified evidence for Phases 21, 27–30, 33–36 and historical Phase 39",
    "git_head": git_head,
    "repository": str(ROOT),
    "scope": "Evidence consolidation only; no training, no TEST access, no new experimental results",
    "evidence_policy": "Every number is traceable to a source artifact; synthetic benchmarks are labelled and never merged with real results",
    "populations": {"TRAIN": 5832, "VAL": 808, "TEST": 1683, "ROUTER_DEVELOPMENT": 4957,
                    "ROUTER_HOLDOUT": 875, "EXTERNAL": 884},
}
DATA["tables"] = TABLES
DATA["figures"] = FIGURES
DATA["missing_sources"] = MISSING

(OUT / "atlas_data.json").write_text(json.dumps(DATA, indent=2), encoding="utf-8")
pd.DataFrame(TABLES).to_csv(OUT / "atlas_table_index.csv", index=False)
pd.DataFrame(FIGURES).to_csv(OUT / "atlas_figure_index.csv", index=False)
(OUT / "atlas_index.json").write_text(json.dumps({"tables": TABLES, "figures": FIGURES,
                                                  "missing_sources": MISSING}, indent=2), encoding="utf-8")
print("TABLES", len(TABLES), "FIGURES", len(FIGURES), "MISSING", len(MISSING))
print("WROTE", OUT / "atlas_data.json")
