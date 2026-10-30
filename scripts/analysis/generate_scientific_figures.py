"""
Deterministic generation of publication-ready scientific figures for RA-MedFiLM-BARR.
Figures 1 and 2: Structural and architectural schematics (source-grounded).
Figures 3, 4, 5, 6, 7: Require genuine production results or remain explicitly marked PENDING.
"""
from __future__ import annotations

import os
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

FIGURES_DIR = Path("reports/figures/scientific_manuscript")


def generate_figure_1_architecture(out_dir: Path = FIGURES_DIR) -> Path:
    """Figure 1 — GlobalMedFiLM architecture and 5 FiLM modulation sites (source-grounded)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "fig1_model_architecture_and_film_sites.png"

    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
    ax.axis("off")

    # Draw Title
    ax.text(0.5, 0.95, "RA-MedFiLM: Global Architecture & 5 FiLM Modulation Sites",
            ha="center", va="top", fontsize=14, fontweight="bold")

    # Encoder Boxes
    encoder_stages = ["Encoder S1\n(16 ch)", "Encoder S2\n(32 ch)", "Encoder S3\n(64 ch)", "Encoder S4\n(128 ch)"]
    for i, name in enumerate(encoder_stages):
        rect = patches.FancyBboxPatch((0.08 + i * 0.16, 0.65), 0.12, 0.12,
                                      boxstyle="round,pad=0.02", ec="#2b5c8f", fc="#d0e1f9")
        ax.add_patch(rect)
        ax.text(0.14 + i * 0.16, 0.71, name, ha="center", va="center", fontsize=9)
        if i < 3:
            ax.annotate("", xy=(0.08 + (i+1)*0.16, 0.71), xytext=(0.20 + i*0.16, 0.71),
                        arrowprops=dict(arrowstyle="->", color="#2b5c8f", lw=1.5))

    # Bottleneck / Bridge (FiLM site 1)
    bridge_rect = patches.FancyBboxPatch((0.72, 0.48), 0.14, 0.12,
                                         boxstyle="round,pad=0.02", ec="#d9534f", fc="#f2dede")
    ax.add_patch(bridge_rect)
    ax.text(0.79, 0.54, "Bridge (256 ch)\n[FiLM Site 1]", ha="center", va="center", fontsize=9, fontweight="bold", color="#a94442")

    # Decoder Blocks (FiLM sites 2, 3, 4, 5)
    decoders = [
        ("Decoder D4 (128 ch)\n[FiLM Site 2]", 0.56, 0.32),
        ("Decoder D3 (64 ch)\n[FiLM Site 3]", 0.40, 0.32),
        ("Decoder D2 (32 ch)\n[FiLM Site 4]", 0.24, 0.32),
        ("Decoder D1 (16 ch)\n[FiLM Site 5]", 0.08, 0.32),
    ]
    for name, x, y in decoders:
        rect = patches.FancyBboxPatch((x, y), 0.12, 0.12,
                                      boxstyle="round,pad=0.02", ec="#d9534f", fc="#f2dede")
        ax.add_patch(rect)
        ax.text(x + 0.06, y + 0.06, name, ha="center", va="center", fontsize=8, fontweight="bold", color="#a94442")

    # Task Embedding Generator
    task_rect = patches.FancyBboxPatch((0.35, 0.10), 0.30, 0.10,
                                       boxstyle="round,pad=0.02", ec="#5cb85c", fc="#dff0d8")
    ax.add_patch(task_rect)
    ax.text(0.50, 0.15, "Task Embedding E(t) + MLP\nt in {0:KUB, 1:ISIC, 2:BUSI, 3:KVASIR}",
            ha="center", va="center", fontsize=9, fontweight="bold", color="#3c763d")

    # Annotation notes
    ax.text(0.5, 0.02, "Exact FiLM Form: F_hat = (1 + tanh(gamma(t))) * F + tanh(beta(t))\nIdentity Control: gamma = 0, beta = 0 (3,432,233 params vs 3,523,001 params)",
            ha="center", va="bottom", fontsize=8, style="italic")

    fig.tight_layout()
    fig.savefig(out_path, dpi=300)
    plt.close(fig)
    return out_path


def generate_figure_2_data_structure(out_dir: Path = FIGURES_DIR) -> Path:
    """Figure 2 — Four-domain clinical tasks and Manifest v3 partitioning."""
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "fig2_four_domain_task_and_manifest_structure.png"

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), dpi=300)

    # Subplot 1: Domain Modalities & Tasks
    domains = ["KUB-StoneX\n(Abdominal Radiography)", "ISIC 2018\n(Dermoscopy)", "BUSI\n(Breast Ultrasound)", "Kvasir-SEG\n(Polyp Endoscopy)"]
    targets = ["Kidney/Ureter/Bladder Stones\n(Tiny, Low-Contrast)", "Cutaneous Melanoma\n(Variable Lesion Margins)", "Breast Lesions\n(High Speckle Noise)", "Colorectal Polyps\n(Specular Reflections)"]
    colors = ["#4e79a7", "#f28e2c", "#e15759", "#76b7b2"]

    y_pos = np.arange(len(domains))
    ax1.barh(y_pos, [1, 1, 1, 1], color=colors, alpha=0.7, edgecolor="black")
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(domains, fontsize=10, fontweight="bold")
    ax1.set_xticks([])
    for i, target in enumerate(targets):
        ax1.text(0.5, i, target, ha="center", va="center", fontsize=9, fontweight="semibold")
    ax1.set_title("Clinical Modalities & Target Lesions", fontsize=12, fontweight="bold")

    # Subplot 2: Manifest v3 Split Accounting
    splits = ["TRAIN\n(5,832)", "VAL808\n(808)", "TEST (Locked)\n(1,683)", "QUARANTINED\n(118)"]
    counts = [5832, 808, 1683, 118]
    split_colors = ["#59a14f", "#edc949", "#af7aa1", "#bab0ac"]

    bars = ax2.bar(splits, counts, color=split_colors, edgecolor="black")
    ax2.set_ylabel("Patient / Image Records", fontsize=10)
    ax2.set_title("Manifest v3 Cryptographic Partitioning (N=8,441)", fontsize=12, fontweight="bold")
    for bar in bars:
        h = bar.get_height()
        ax2.annotate(f"{h:,}", xy=(bar.get_x() + bar.get_width() / 2, h),
                     xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=9)

    fig.tight_layout()
    fig.savefig(out_path, dpi=300)
    plt.close(fig)
    return out_path


def generate_figure_pending(fig_num: int, title: str, description: str, out_dir: Path = FIGURES_DIR) -> Path:
    """Generate explicit pending placeholder for figures requiring genuine production results."""
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"fig{fig_num}_pending.png"

    fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
    ax.axis("off")

    rect = patches.FancyBboxPatch((0.1, 0.1), 0.8, 0.8,
                                  boxstyle="round,pad=0.05", ec="#d9534f", fc="#fff", lw=2, ls="--")
    ax.add_patch(rect)

    ax.text(0.5, 0.70, f"Figure {fig_num}: {title}", ha="center", va="center", fontsize=13, fontweight="bold")
    ax.text(0.5, 0.50, "[STATUS: PENDING SCIENTIFIC EXECUTION]", ha="center", va="center",
            fontsize=12, fontweight="bold", color="#d9534f")
    ax.text(0.5, 0.35, description, ha="center", va="center", fontsize=9, wrap=True, style="italic")
    ax.text(0.5, 0.20, "Will be automatically populated upon completion of the authorized 6-run campaign.",
            ha="center", va="center", fontsize=8, color="#666")

    fig.tight_layout()
    fig.savefig(out_path, dpi=300)
    plt.close(fig)
    return out_path


def run_all_figures():
    print("Generating Figure 1 (Architecture)...")
    p1 = generate_figure_1_architecture()
    print("Generated:", p1)

    print("Generating Figure 2 (Data Structure)...")
    p2 = generate_figure_2_data_structure()
    print("Generated:", p2)

    pending_figs = [
        (3, "C1-T vs C1-C Paired Dice Differences Across Seeds",
         "Awaiting genuine 6-run production training outputs to compute exact paired seed deltas."),
        (4, "Domain-wise Dice and IoU Comparisons",
         "Awaiting genuine production evaluation on KUB, ISIC, BUSI, and KVASIR."),
        (5, "Paired Effect Distribution and Prespecified Confidence Interval",
         "Awaiting 2,000 paired cluster bootstrap resamples on genuine case-level evaluation."),
        (6, "Computation, Parameters, and Training Efficiency",
         "Awaiting execution duration and GPU memory profiling from production trainer runs."),
        (7, "Failure-Case Categories and Supported Boundary Metrics",
         "Awaiting genuine post-inference boundary metrics (NSD, HD95) across lesion cohorts."),
    ]

    for num, title, desc in pending_figs:
        print(f"Generating Figure {num} (Pending)...")
        p = generate_figure_pending(num, title, desc)
        print("Generated:", p)


if __name__ == "__main__":
    run_all_figures()
