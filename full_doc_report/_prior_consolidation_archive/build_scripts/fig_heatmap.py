"""Figure A: six-model x four-domain Dice heatmap (VAL808, derived from per-image table)."""
import pandas as pd, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
OUT = ROOT / "full_doc_report" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(ROOT / "reports" / "tables" / "phase21_per_image_all_models.csv")
order = ["global_medfilm", "deeplabv3plus", "transformer_mit_unet", "unetpp", "attention_unet", "unet"]
names = ["Global MedFiLM", "DeepLabV3+", "Transformer/MiT U-Net", "U-Net++", "Attention U-Net", "U-Net"]
doms = ["ISIC", "BUSI", "KVASIR", "KUB"]
dd = {"ISIC": "dataset", "BUSI": "dataset", "KVASIR": "dataset", "KUB": "dataset"}

mat = np.zeros((6, 4)); n = np.zeros(4, dtype=int)
for i, k in enumerate(order):
    s = df[df.model_key == k]
    for j, d in enumerate(doms):
        v = s[s.dataset == d]["dice"]
        mat[i, j] = v.mean()
        if i == 0:
            n[j] = len(v)
macro = mat.mean(axis=1)

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})
fig, ax = plt.subplots(figsize=(6.6, 3.9), dpi=300)
im = ax.imshow(mat, cmap="Blues", vmin=0.70, vmax=0.95, aspect="auto")
ax.set_xticks(range(4)); ax.set_xticklabels([f"{d} (n={n[j]})" for j, d in enumerate(doms)], fontsize=7.5)
ax.set_yticks(range(6)); ax.set_yticklabels(names)
for i in range(6):
    for j in range(4):
        c = "white" if mat[i, j] > 0.85 else "#1b2a41"
        ax.text(j, i, f"{mat[i, j]:.4f}", ha="center", va="center", color=c, fontsize=8.5)
ax.axvline(-0.5, color="white", lw=0)
ax.set_title("Dice per domain, VAL808 (development set)", loc="left", color="#13294b", fontsize=10, pad=8)
cb = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
cb.set_label("Mean per-image Dice", fontsize=8)
fig.text(0.01, 0.01,
         "Macro Dice (unweighted mean of 4 domain means): " +
         ", ".join(f"{names[i]} {macro[i]:.4f}" for i in range(6)) +
         ".\nDerived from phase21_per_image_all_models.csv. Shared development split; not a TEST result.",
         fontsize=6.3, color="#444", va="bottom")
fig.tight_layout(rect=[0, 0.13, 1, 1])
for ext in ("png", "svg", "pdf"):
    fig.savefig(OUT / f"figA_dice_heatmap_six_model_val808.{ext}", dpi=300 if ext == "png" else None)
print("macro", dict(zip(names, np.round(macro, 6))))
print("n per domain", dict(zip(doms, n.tolist())))
