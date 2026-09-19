import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

out_dir = Path("reports/figures/phase03_dataset_discovery/aggregate")
out_dir.mkdir(parents=True, exist_ok=True)

df = pd.read_csv("reports/tables/phase03_dataset_discovery_summary.csv")

fig, ax = plt.subplots(figsize=(10, 5))
colors = ["#2980b9", "#27ae60", "#e67e22", "#8e44ad"]
bars = ax.bar(df["dataset"], df["paired_count"], color=colors, width=0.55, edgecolor="#2c3e50", lw=1.5)

for bar, count in zip(bars, df["paired_count"]):
    yval = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2, yval + 60, f"{count:,}", ha="center", va="bottom", fontsize=11, fontweight="bold")

total_count = df["paired_count"].sum()
ax.set_ylim(0, max(df["paired_count"]) * 1.15)
ax.set_title(f"RA-MedFiLM-Seg++ Authoritative Paired Dataset Inventory (Total: {total_count:,} Cases)", fontsize=13, fontweight="bold", pad=12)
ax.set_ylabel("Paired Image/Mask Count", fontsize=11, fontweight="bold")
ax.grid(axis="y", linestyle="--", alpha=0.5)

plt.tight_layout()
fig_p = out_dir / "phase03_paired_dataset_counts.png"
plt.savefig(str(fig_p), dpi=150, bbox_inches="tight")
# Also copy to parent phase03 figure directory
plt.savefig(str(Path("reports/figures/phase03_dataset_discovery/phase03_paired_dataset_counts.png")), dpi=150, bbox_inches="tight")
plt.close()
print(f"Saved dataset counts bar chart to {fig_p}")

