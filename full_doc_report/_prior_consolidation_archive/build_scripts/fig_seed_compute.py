"""Figure E: seed-wise macro delta-Dice (VAL808), shared frozen global backbone.
Figure F: accuracy (VAL808 macro Dice) vs analytical GMACs, marker size = parameters."""
import pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
OUT = ROOT / "full_doc_report" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
T = ROOT / "reports" / "tables"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8.5})

# ---------- Figure E ----------
ci = pd.read_csv(T / "phase29_phase_d_three_seed_delta_dice_ci.csv")
rep = pd.read_csv(T / "phase29_phase_d_three_seed_reproducibility_summary.csv")
d = rep[rep.metric == "macro_delta_dice"].iloc[0]
fig, ax = plt.subplots(figsize=(5.6, 3.0), dpi=300)
xs = list(range(len(ci)))
for i, r in enumerate(ci.itertuples()):
    ax.plot([i, i], [r.ci_low, r.ci_high], color="#0f766e", lw=2.2)
    ax.plot(i, r.point, "o", color="#13294b", ms=6)
    ax.text(i + 0.12, r.point, f"{r.point:.4f}", va="center", fontsize=7.5)
ax.axhline(d["mean"], color="#0f766e", ls=":", lw=1)
ax.text(2.45, d["mean"], f"mean {d['mean']:.4f}\nSD {d['sample_sd_ddof1']:.4f}",
        va="center", fontsize=7, color="#0f766e")
ax.axhline(0, color="#b91c1c", ls="--", lw=1)
ax.set_xticks(xs); ax.set_xticklabels([f"seed {int(s)}" for s in ci.master_seed])
ax.set_xlim(-0.5, 3.0)
ax.set_ylim(0, 0.005)
ax.set_ylabel("Macro delta-Dice vs global reference (VAL808)")
ax.set_title("Historical seed-wise reproducibility (shared frozen global backbone)",
             loc="left", fontsize=9, color="#13294b")
ax.spines[["top", "right"]].set_visible(False)
fig.text(0.01, 0.01,
         "Bars: 95% paired bootstrap CI per seed (teal). Seeds 42/123/3407 share ONE frozen Global G backbone;\n"
         "they vary the downstream router/refiner/safety stages only. Not independent end-to-end runs. Descriptive; no p-values.",
         fontsize=6.0, color="#444", va="bottom")
fig.tight_layout(rect=[0, 0.1, 1, 1])
for ext in ("png", "svg", "pdf"):
    fig.savefig(OUT / f"figE_seedwise_reproducibility_shared_backbone.{ext}", dpi=300 if ext == "png" else None)

# ---------- Figure F ----------
comp = pd.read_csv(T / "phase21_six_model_compute.csv")
acc = pd.read_csv(T / "phase21_six_model_comparison.csv")
m = comp.merge(acc[["model_key", "macro_domain_dice", "macro_domain_dice_ci_low", "macro_domain_dice_ci_high"]],
               on="model_key", how="left")
name = {"global_medfilm": "Global MedFiLM", "deeplabv3plus": "DeepLabV3+", "transformer_mit_unet": "Transformer/MiT",
        "unetpp": "U-Net++", "attention_unet": "Attention U-Net", "unet": "U-Net"}
fig, ax = plt.subplots(figsize=(6.0, 3.6), dpi=300)
for r in m.itertuples():
    proposed = r.model_key == "global_medfilm"
    ax.errorbar(r.gmacs, r.macro_domain_dice,
                yerr=[[r.macro_domain_dice - r.macro_domain_dice_ci_low], [r.macro_domain_dice_ci_high - r.macro_domain_dice]],
                fmt="D" if proposed else "o", color="#0f766e" if proposed else "#64748b",
                ms=7 if proposed else 6, capsize=2, lw=0.9)
    ax.annotate(f"{name[r.model_key]}\n{r.params/1e6:.1f} M params", (r.gmacs, r.macro_domain_dice),
                xytext=(6, -2), textcoords="offset points", fontsize=6.8, va="top")
ax.set_xlabel("Analytical GMACs at 1x3x512x512 (lower bound; Conv2d/Linear count)", labelpad=6)
ax.set_ylabel("Macro Dice, VAL808 (95% CI)")
ax.set_xlim(20, 150)
ax.set_ylim(0.76, 0.87)
ax.set_title("Accuracy versus analytical compute, VAL808 (n=808)", loc="left", fontsize=9, color="#13294b")
ax.spines[["top", "right"]].set_visible(False)
ax.grid(alpha=0.25, lw=0.5)
fig.text(0.01, 0.01,
         "Teal diamond: proposed family member (Global MedFiLM, G component only). Grey: conventional baselines.\n"
         "Axes are not truncated at zero; Dice axis spans 0.76–0.87. Sources: phase21_six_model_compute.csv, phase21_six_model_comparison.csv.\n"
         "RA-MedFiLM-BARR FULL is reported separately in Table 4 (GMACs 32.44). No latency shown here.",
         fontsize=5.9, color="#444", va="bottom")
fig.tight_layout(rect=[0, 0.1, 1, 1])
for ext in ("png", "svg", "pdf"):
    fig.savefig(OUT / f"figF_accuracy_vs_gmacs_pareto.{ext}", dpi=300 if ext == "png" else None)
print(m[["model_key", "params", "gmacs", "macro_domain_dice"]].round(4).to_string(index=False))
print(ci.round(6).to_string(index=False))
