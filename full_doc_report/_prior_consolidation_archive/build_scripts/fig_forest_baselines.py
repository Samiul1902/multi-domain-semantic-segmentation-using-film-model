"""Figure B: paired macro-Dice difference forest plot, Global MedFiLM minus each baseline (VAL808)."""
import pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
OUT = ROOT / "full_doc_report" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

p = pd.read_csv(ROOT / "reports" / "tables" / "phase21_paired_bootstrap_vs_baselines.csv")
label = {"deeplabv3plus": "DeepLabV3+", "transformer_mit_unet": "Transformer/MiT U-Net",
         "unetpp": "U-Net++", "attention_unet": "Attention U-Net", "unet": "U-Net"}
p = p[p.model_a == "global_medfilm"].copy()
p["name"] = p.model_b.map(label)
p = p.sort_values("observed_diff")

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})
fig, ax = plt.subplots(figsize=(6.4, 3.0), dpi=300)
y = range(len(p))
for i, r in enumerate(p.itertuples()):
    col = "#0f766e" if r.diff_ci_low > 0 else "#7a8799"
    ax.plot([r.diff_ci_low, r.diff_ci_high], [i, i], color=col, lw=2)
    ax.plot(r.observed_diff, i, "o", color="#13294b", ms=5)
    ax.text(0.0665, i, f"{r.observed_diff:+.4f} [{r.diff_ci_low:+.4f}, {r.diff_ci_high:+.4f}]",
            va="center", fontsize=7.5, color="#1b2a41")
ax.axvline(0, color="#b91c1c", lw=1, ls="--")
ax.set_yticks(list(y)); ax.set_yticklabels(p.name)
ax.set_xlim(-0.005, 0.11)
ax.set_xlabel("Macro Dice difference: Global MedFiLM minus baseline (95% paired bootstrap CI)", labelpad=8)
ax.tick_params(axis="x", pad=4)
ax.set_title("Paired macro-Dice difference, VAL808 (n=808; 2000 bootstrap replicates, seed 42)",
             loc="left", color="#13294b", fontsize=9.5)
ax.spines[["top", "right"]].set_visible(False)
fig.text(0.01, 0.01,
         "Teal: CI excludes zero. Grey: CI includes zero (no difference claimed). Resampling is domain-stratified paired "
         "image bootstrap.\nSource: phase21_paired_bootstrap_vs_baselines.csv. Development-set comparison; no causal FiLM attribution.",
         fontsize=6.2, color="#444", va="bottom")
fig.tight_layout(rect=[0, 0.14, 1, 1])
for ext in ("png", "svg", "pdf"):
    fig.savefig(OUT / f"figB_forest_paired_baselines_val808.{ext}", dpi=300 if ext == "png" else None)
print(p[["name", "observed_diff", "diff_ci_low", "diff_ci_high"]].round(6).to_string(index=False))
