"""Figure C: 13-arm ablation (routed mean delta-Dice and harmful activation share).
Figure D: paired contrasts with 95% bootstrap CIs (Phase 28, ROUTER_DEVELOPMENT n=4957)."""
import pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
OUT = ROOT / "full_doc_report" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
T = ROOT / "reports" / "tables"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8.5})

arm = pd.read_csv(T / "phase28_table_02_arm_primary_metrics.csv")
defs = pd.read_csv(T / "phase28_table_01_arm_definitions.csv")
arm = arm.merge(defs[["arm", "definition"]], on="arm", how="left")
arm["mean_delta_mdice"] = arm.mean_true_delta_dice_routed * 1000  # x10^-3 (milli-Dice)
arm["harm_pct"] = arm.harmful_activation_share * 100

# ---- Figure C: two-panel matrix (distinct units, no shared axis) ----
fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.0, 3.6), dpi=300, sharey=True,
                             gridspec_kw={"width_ratios": [1, 1]})
y = list(range(len(arm)))[::-1]
labels = [f"{r.arm}  {r.definition[:44]}" for r in arm.itertuples()]
colors1 = ["#0f766e" if (r.mean_delta_mdice > 0 and r.arm in ("A8", "A7", "A6", "A3", "A4", "A6")) else
           ("#b91c1c" if r.mean_delta_mdice < 0 else "#7a8799") for r in arm.itertuples()]
a1.barh(y, arm.mean_delta_mdice, color=colors1, height=0.62)
for yi, v in zip(y, arm.mean_delta_mdice):
    a1.text(v + (0.12 if v >= 0 else -0.12), yi, f"{v:+.2f}", va="center",
            ha="left" if v >= 0 else "right", fontsize=7)
a1.axvline(0, color="#1b2a41", lw=0.8)
a1.set_xlabel("Mean routed true delta-Dice (x10^-3)")
a1.set_yticks(y); a1.set_yticklabels(labels, fontsize=7)
a1.set_title("(A) Routed ΔDice", loc="left", fontsize=9, color="#13294b")
a2.barh(y, arm.harm_pct, color="#a16207", height=0.62)
for yi, v in zip(y, arm.harm_pct):
    a2.text(v + 1, yi, f"{v:.1f}%", va="center", fontsize=7)
a2.set_xlim(0, 85)
a2.set_xlabel("Harmful activation share (% of routed rows)")
a2.set_title("(B) Harmful activation", loc="left", fontsize=9, color="#13294b")
for ax in (a1, a2):
    ax.spines[["top", "right"]].set_visible(False)
fig.text(0.01, 0.01,
         "A0 (global-only) and A1 (always-refine) are endpoints by construction; A1 uses the full budget (n=4957).\n"
         "Descriptive ROUTER_DEVELOPMENT ablation (n=4957; 25% budget arms K=1239). Arms are not a cumulative progression.\n"
         "Source: phase28_table_02_arm_primary_metrics.csv.",
         fontsize=6.0, color="#444", va="bottom")
fig.tight_layout(rect=[0, 0.1, 1, 1])
for ext in ("png", "svg", "pdf"):
    fig.savefig(OUT / f"figC_ablation_13arm_routed_delta_harm.{ext}", dpi=300 if ext == "png" else None)

# ---- Figure D: paired contrasts forest ----
ct = pd.read_csv(T / "phase28_table_08_bootstrap_statistics.csv")
fig2, ax = plt.subplots(figsize=(6.6, 2.6), dpi=300)
ct = ct.iloc[::-1].reset_index(drop=True)
for i, r in enumerate(ct.itertuples()):
    x = r.mean_difference * 1000
    lo, hi = r.ci95_low * 1000, r.ci95_high * 1000
    inc0 = (lo > 0) or (hi < 0)
    col = "#0f766e" if inc0 else "#7a8799"
    ax.plot([lo, hi], [i, i], color=col, lw=2)
    ax.plot(x, i, "o", color="#13294b", ms=5)
    ax.text(0.12, i, f"{x:+.4f} [{lo:+.4f}, {hi:+.4f}] (x10^-3)", va="center", fontsize=7)
ax.axvline(0, color="#b91c1c", ls="--", lw=1)
ax.set_yticks(range(len(ct))); ax.set_yticklabels([c.replace("_", " ") for c in ct.contrast])
ax.set_xlabel("Paired mean difference in macro routed delta-Dice (x10^-3), 95% bootstrap CI")
ax.set_xlim(-2.2, 14)
ax.spines[["top", "right"]].set_visible(False)
ax.set_title("Paired ablation contrasts, ROUTER_DEVELOPMENT (n=4957, 2000 replicates, seed 42)",
             loc="left", fontsize=9, color="#13294b")
fig2.text(0.01, 0.01,
          "Teal: CI excludes zero. Grey: CI includes zero. Descriptive, no post-hoc correction. "
          "A8 vs A7 CI includes zero: no measurable mean gain established.\nSource: phase28_table_08_bootstrap_statistics.csv.",
          fontsize=6.0, color="#444", va="bottom")
fig2.tight_layout(rect=[0, 0.1, 1, 1])
for ext in ("png", "svg", "pdf"):
    fig2.savefig(OUT / f"figD_forest_ablation_contrasts.{ext}", dpi=300 if ext == "png" else None)
print(arm[["arm", "mean_delta_mdice", "harm_pct"]].round(3).to_string(index=False))
print(ct[["contrast", "mean_difference", "ci95_low", "ci95_high"]].to_string(index=False))
