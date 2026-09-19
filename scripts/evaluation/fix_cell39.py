import json
from pathlib import Path

NOTEBOOK_PATH = Path("notebooks/13_phase14_regional_refiner_diagnostic.ipynb")

def fix_cell_39():
    with open(NOTEBOOK_PATH, "r", encoding="utf-8") as f:
        nb = json.load(f)

    # Update Cell 39
    nb["cells"][39]["source"] = [
        "# Figure A: Mode Dice Comparison\n",
        "import matplotlib\n",
        "matplotlib.use(\"Agg\")\n",
        "import matplotlib.pyplot as plt\n",
        "\n",
        "img_metrics = pd.read_csv(TABLES_DIR / \"phase14_part3_image_metrics.csv\")\n",
        "fig, axes = plt.subplots(1, 2, figsize=(14, 5))\n",
        "\n",
        "# Dice Distribution Boxplot\n",
        "dice_data = [img_metrics[\"global_dice_512\"], img_metrics[\"oracle_dice_512\"], img_metrics[\"predicted_dice_512\"]]\n",
        "bp = axes[0].boxplot(dice_data, patch_artist=True,\n",
        "                     boxprops=dict(facecolor=\"#ccebc5\", color=\"#2b8cbe\"),\n",
        "                     medianprops=dict(color=\"red\", linewidth=2))\n",
        "axes[0].set_xticks([1, 2, 3])\n",
        "axes[0].set_xticklabels([\"GLOBAL_ONLY\", \"ORACLE_REGIONAL\", \"PREDICTED_REGIONAL\"])\n",
        "axes[0].set_ylabel(\"FULL_FIELD Dice\")\n",
        "axes[0].set_title(\"Validation FULL_FIELD Dice Distribution (N=106)\")\n",
        "axes[0].grid(True, linestyle=\"--\", alpha=0.5)\n",
        "\n",
        "# Component Recall by Size Barplot (Authoritative Object Recall)\n",
        "strata = [\"TINY\", \"SMALL\", \"MEDIUM\", \"LARGE\"]\n",
        "x = np.arange(len(strata))\n",
        "width = 0.25\n",
        "\n",
        "g_rec = [df_size.loc[df_size[\"Size Stratum\"] == s, \"Global Obj Recall\"].values[0] for s in strata]\n",
        "o_rec = [df_size.loc[df_size[\"Size Stratum\"] == s, \"Oracle Obj Recall\"].values[0] for s in strata]\n",
        "p_rec = [df_size.loc[df_size[\"Size Stratum\"] == s, \"Pred Obj Recall\"].values[0] for s in strata]\n",
        "\n",
        "axes[1].bar(x - width, g_rec, width, label=\"GLOBAL_ONLY\", color=\"#41b6c4\")\n",
        "axes[1].bar(x, o_rec, width, label=\"ORACLE_REGIONAL\", color=\"#225ea8\")\n",
        "axes[1].bar(x + width, p_rec, width, label=\"PREDICTED_REGIONAL\", color=\"#e7298a\")\n",
        "axes[1].set_xticks(x)\n",
        "axes[1].set_xticklabels(strata)\n",
        "axes[1].set_ylabel(\"Object Recall (overlap >= 1 px)\")\n",
        "axes[1].set_title(\"Object Detection Recall by Size Stratum\")\n",
        "axes[1].set_ylim(0, 1.1)\n",
        "axes[1].grid(True, linestyle=\"--\", alpha=0.5)\n",
        "axes[1].legend()\n",
        "\n",
        "plt.tight_layout()\n",
        "fig_path = FIG_DIR / \"phase14_part3_diagnostic_summary.png\"\n",
        "plt.savefig(fig_path, dpi=150)\n",
        "plt.close(fig)\n",
        "print(f\"Saved figure to: {fig_path}\")\n"
    ]

    with open(NOTEBOOK_PATH, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1)
    print("Updated Cell 39 in notebook successfully.")

if __name__ == "__main__":
    fix_cell_39()

