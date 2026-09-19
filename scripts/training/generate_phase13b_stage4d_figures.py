"""Generate publication-quality figures for Phase 13B Stage-4D Final Bounded Localizer."""
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
FIG_DIR = ROOT / "reports/figures/phase13b_stage4d_final_localizer"
FIG_DIR.mkdir(parents=True, exist_ok=True)

def main():
    exp_id = "phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_v1"
    hist_path = ROOT / "experiments" / exp_id / "history.csv"
    if not hist_path.exists():
        print(f"History file not found: {hist_path}")
        return

    s4d_hist = pd.read_csv(hist_path)
    epochs = s4d_hist["epoch"]

    # Optional comparison data
    v3_hist_path = ROOT / "experiments/phase13b_kub_localizer_r512_s3_centernetfocal_seed42_v3/history.csv"
    v3_hist = pd.read_csv(v3_hist_path) if v3_hist_path.exists() else None

    # Figure A: Train vs Validation Loss by Epoch
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(epochs, s4d_hist["train_loss"], label="Train Loss (Stage-4D 128-grid)", color="#1f77b4", lw=2)
    ax.plot(epochs, s4d_hist["val_loss"], label="Val Loss (Stage-4D 128-grid)", color="#ff7f0e", lw=2)
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Loss")
    ax.set_title("Phase 13B Stage-4D: Train vs Validation Loss (CenterNet Focal Loss)")
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend()
    plt.tight_layout()
    fig.savefig(FIG_DIR / "fig_a_loss_by_epoch.png", dpi=200)
    plt.close(fig)

    # Figure B: Tiny recall90 and overall recall90 vs Epoch
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(epochs, s4d_hist["val_tiny_recall90"], label="VAL Tiny Recall@90", color="#2ca02c", lw=2)
    ax.plot(epochs, s4d_hist["val_overall_recall90"], label="VAL Overall Recall@90", color="#9467bd", lw=2)
    ax.axhline(0.50, color="r", linestyle=":", label="Stage-4D Gate Target (>= 0.50)")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Recall@90")
    ax.set_title("Phase 13B Stage-4D: Validation Recall@90 over Epochs")
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend()
    plt.tight_layout()
    fig.savefig(FIG_DIR / "fig_b_recall_by_epoch.png", dpi=200)
    plt.close(fig)

    # Figure C: Hard-Tiny Recovery over Training
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(epochs, s4d_hist["val_hard_tiny_recovered90"], label="Hard Tiny Recovered (out of 16)", color="#d62728", lw=2)
    ax.plot(epochs, s4d_hist["val_global_empty_images_covered90"], label="Global Empty Covered (out of 7)", color="#8c564b", lw=2, linestyle="--")
    ax.axhline(2, color="black", linestyle=":", label="Stage-4D Gate Threshold (>= 2 hard tiny)")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Recovered Count")
    ax.set_title("Phase 13B Stage-4D: Hard-Case Recovery vs Epoch")
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend()
    plt.tight_layout()
    fig.savefig(FIG_DIR / "fig_c_hard_cases_by_epoch.png", dpi=200)
    plt.close(fig)

    # Figure D: Mean and Median Max Heatmap Probability vs Epoch
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(epochs, s4d_hist["mean_max_heatmap"], label="Mean Max Heatmap Prob", color="#e377c2", lw=2)
    ax.plot(epochs, s4d_hist["median_max_heatmap"], label="Median Max Heatmap Prob", color="#7f7f7f", lw=2, linestyle="--")
    ax.axhline(0.10, color="blue", linestyle=":", label="Initial Prior (p=0.10)")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Heatmap Probability")
    ax.set_title("Phase 13B Stage-4D: Maximum Heatmap Probability Evolution")
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend()
    plt.tight_layout()
    fig.savefig(FIG_DIR / "fig_d_heatmap_probs_by_epoch.png", dpi=200)
    plt.close(fig)

    # Figure E: ROI-Area Burden vs Epoch
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(epochs, s4d_hist["mean_roi_area_fraction"], label="Mean Union ROI Area Fraction", color="#bcbd22", lw=2)
    ax.axhline(0.10, color="r", linestyle=":", label="Feasibility Constraint (<= 0.10)")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Area Fraction")
    ax.set_title("Phase 13B Stage-4D: ROI Area Burden over Training")
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend()
    plt.tight_layout()
    fig.savefig(FIG_DIR / "fig_e_roi_area_by_epoch.png", dpi=200)
    plt.close(fig)

    # Figure F: Proposals/Image vs Epoch
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(epochs, s4d_hist["mean_proposals_per_image"], label="Mean Proposals per Image", color="#17becf", lw=2)
    ax.axhline(5.0, color="r", linestyle=":", label="Feasibility Constraint (<= 5.0)")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Proposals / Image")
    ax.set_title("Phase 13B Stage-4D: Proposals Generated per Image")
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend()
    plt.tight_layout()
    fig.savefig(FIG_DIR / "fig_f_proposals_by_epoch.png", dpi=200)
    plt.close(fig)

    # Figure G: Stage-4C (512-grid) vs Stage-4D (128-grid) Comparison
    if v3_hist is not None:
        fig, ax = plt.subplots(figsize=(9, 5.5))
        metrics = ["Tiny Recall@90", "Overall Recall@90", "Hard Tiny (/16)", "Max Heatmap"]
        v3_best_tiny = v3_hist["val_tiny_recall90"].max()
        v3_best_overall = v3_hist["val_overall_recall90"].max()
        v3_best_hard = v3_hist["val_hard_tiny_recovered90"].max()
        v3_best_maxh = v3_hist["mean_max_heatmap"].max()

        s4d_best_tiny = s4d_hist["val_tiny_recall90"].max()
        s4d_best_overall = s4d_hist["val_overall_recall90"].max()
        s4d_best_hard = s4d_hist["val_hard_tiny_recovered90"].max()
        s4d_best_maxh = s4d_hist["mean_max_heatmap"].max()

        v3_vals = [v3_best_tiny, v3_best_overall, v3_best_hard / 16.0, v3_best_maxh]
        s4d_vals = [s4d_best_tiny, s4d_best_overall, s4d_best_hard / 16.0, s4d_best_maxh]

        x = np.arange(len(metrics))
        width = 0.35
        b1 = ax.bar(x - width/2, v3_vals, width, label="Stage-4C V3 (512x512 Heatmap)", color="#dd8452")
        b2 = ax.bar(x + width/2, s4d_vals, width, label="Stage-4D (128x128 Heatmap)", color="#2ca02c")

        ax.axhline(0.50, color="r", linestyle=":", label="Stage-4D Gate (0.50)")
        ax.set_ylabel("Normalized Metric Value")
        ax.set_title("Comparison: Stage-4C (512-grid) vs Stage-4D (128-grid)")
        ax.set_xticks(x)
        ax.set_xticklabels(metrics)
        ax.grid(True, linestyle="--", alpha=0.6, axis="y")
        ax.legend()

        for bar in list(b1) + list(b2):
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, h + 0.015, f"{h:.2f}", ha="center", va="bottom", fontsize=9, fontweight="bold")

        plt.tight_layout()
        fig.savefig(FIG_DIR / "fig_g_stage4c_vs_stage4d_comparison.png", dpi=200)
        plt.close(fig)

    # Figure H: Size-Stratified Recall Comparison
    s4d_size_path = ROOT / "reports/tables/phase13b_stage4d_size_summary.csv"
    p13_size_path = ROOT / "reports/tables/phase13_predicted_roi_size_summary.csv"
    v3_comp_path = ROOT / "reports/tables/phase13b_centernet_v3_best_val_per_component.csv"

    if s4d_size_path.exists() and p13_size_path.exists():
        s4d_size = pd.read_csv(s4d_size_path)
        p13_size = pd.read_csv(p13_size_path)
        strata = ["TINY", "SMALL", "MEDIUM", "LARGE"]

        p13_rec = [p13_size.loc[p13_size["Size"] == s, "recall90"].values[0] for s in strata]
        s4d_rec = [s4d_size.loc[s4d_size["Size"] == s, "recall90"].values[0] for s in strata]

        fig, ax = plt.subplots(figsize=(9, 5.5))
        x = np.arange(len(strata))
        width = 0.25

        if v3_comp_path.exists():
            v3_comp = pd.read_csv(v3_comp_path)
            v3_rec = [v3_comp.loc[v3_comp["kub_size_v1"] == s, "covered90"].mean() for s in strata]
            ax.bar(x - width, p13_rec, width, label="Phase 13 Simple ROI", color="#4c72b0")
            ax.bar(x, v3_rec, width, label="Stage-4C V3 (512x512)", color="#dd8452")
            ax.bar(x + width, s4d_rec, width, label="Stage-4D (128x128)", color="#2ca02c")
        else:
            ax.bar(x - width/2, p13_rec, width, label="Phase 13 Simple ROI", color="#4c72b0")
            ax.bar(x + width/2, s4d_rec, width, label="Stage-4D (128x128)", color="#2ca02c")

        ax.axhline(0.50, color="r", linestyle=":", label="Stage-4D Gate (0.50)")
        ax.set_ylabel("Recall@90")
        ax.set_title("Recall@90 by Component Size Stratum Across Milestones")
        ax.set_xticks(x)
        ax.set_xticklabels(strata)
        ax.grid(True, linestyle="--", alpha=0.6, axis="y")
        ax.legend()
        plt.tight_layout()
        fig.savefig(FIG_DIR / "fig_h_size_stratified_recall.png", dpi=200)
        plt.close(fig)

    print("All Stage-4D figures generated successfully.")


if __name__ == "__main__":
    main()

