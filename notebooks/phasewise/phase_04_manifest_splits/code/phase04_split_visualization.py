#!/usr/bin/env python3
"""
Phase 04 — Split Visualization Script
Generates publication-quality charts depicting dataset split counts,
normalized proportions, KUB patient-level split partitioning, split overlap matrix,
and optional KUB stone anatomical category split distribution.

Usage:
    D:\Softfors\jup\.venv\Scripts\python.exe notebooks/phasewise/phase_04_manifest_splits/code/phase04_split_visualization.py
"""

import sys
import json
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def find_project_root() -> Path:
    p = Path(__file__).resolve()
    for _ in range(6):
        if (p / 'manifests').exists() and (p / 'reports').exists():
            return p
        p = p.parent
    return Path('D:/Softfors/jup')


def generate_figures():
    root = find_project_root()
    manifest_p = root / "manifests/all_paired.csv"
    if not manifest_p.exists():
        raise FileNotFoundError(f"Canonical manifest missing: {manifest_p}")

    df = pd.read_csv(manifest_p)

    out_dir = root / "reports/figures/phase04_manifest_splits/aggregate"
    out_dir.mkdir(parents=True, exist_ok=True)

    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    colors = {'TRAIN': '#1f77b4', 'VAL': '#ff7f0e', 'TEST': '#2ca02c'}

    generated_figures = []

    # -------------------------------------------------------------
    # Figure 1: Dataset Split Counts (Stacked Bar Chart)
    # -------------------------------------------------------------
    fig1_path = out_dir / "phase04_dataset_split_counts.png"
    datasets = ['ISIC', 'BUSI', 'KVASIR', 'KUB']
    ct = pd.crosstab(df['dataset'], df['split']).reindex(datasets)[['TRAIN', 'VAL', 'TEST']]

    fig, ax = plt.subplots(figsize=(9, 6), dpi=300)
    x = np.arange(len(datasets))
    width = 0.55

    bottom = np.zeros(len(datasets))
    for sp in ['TRAIN', 'VAL', 'TEST']:
        vals = ct[sp].values
        bars = ax.bar(x, vals, width, bottom=bottom, label=sp, color=colors[sp], edgecolor='black', linewidth=0.8)
        for i, val in enumerate(vals):
            if val > 0:
                ax.text(x[i], bottom[i] + val / 2.0, f"{val:,}\n({val/ct.loc[datasets[i]].sum()*100:.1f}%)",
                        ha='center', va='center', color='white', fontweight='bold', fontsize=9)
        bottom += vals

    for i, d in enumerate(datasets):
        total = ct.loc[d].sum()
        ax.text(x[i], total + 70, f"Total: {total:,}", ha='center', va='bottom', fontweight='bold', fontsize=10)

    ax.set_title("Canonical Population Partitioning by Dataset & Split (N=8,441)", fontsize=13, fontweight='bold', pad=15)
    ax.set_xlabel("Dataset Cohort", fontsize=11, fontweight='bold')
    ax.set_ylabel("Paired Image-Mask Sample Count", fontsize=11, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(datasets, fontsize=10, fontweight='bold')
    ax.set_ylim(0, 4200)
    ax.legend(title="Split Allocation", frameon=True, loc='upper right')
    plt.tight_layout()
    plt.savefig(fig1_path, dpi=300)
    plt.close()
    generated_figures.append(fig1_path)
    print(f"Generated Figure 1: {fig1_path}")

    # -------------------------------------------------------------
    # Figure 2: Normalized 100% Stacked Bar Chart
    # -------------------------------------------------------------
    fig2_path = out_dir / "phase04_dataset_split_proportions.png"
    ct_norm = ct.div(ct.sum(axis=1), axis=0) * 100.0

    fig, ax = plt.subplots(figsize=(9, 6), dpi=300)
    bottom = np.zeros(len(datasets))
    for sp in ['TRAIN', 'VAL', 'TEST']:
        vals = ct_norm[sp].values
        ax.bar(x, vals, width, bottom=bottom, label=sp, color=colors[sp], edgecolor='black', linewidth=0.8)
        for i, val in enumerate(vals):
            ax.text(x[i], bottom[i] + val / 2.0, f"{val:.1f}%",
                    ha='center', va='center', color='white', fontweight='bold', fontsize=10)
        bottom += vals

    ax.set_title("Canonical Split Proportions Across Datasets (Normalized 100%)", fontsize=13, fontweight='bold', pad=15)
    ax.set_xlabel("Dataset Cohort", fontsize=11, fontweight='bold')
    ax.set_ylabel("Percentage (%)", fontsize=11, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(datasets, fontsize=10, fontweight='bold')
    ax.set_ylim(0, 105)
    ax.axhline(70, color='gray', linestyle='--', alpha=0.5, label='~70% Train Reference')
    ax.legend(title="Split Allocation", frameon=True, loc='upper right')
    plt.tight_layout()
    plt.savefig(fig2_path, dpi=300)
    plt.close()
    generated_figures.append(fig2_path)
    print(f"Generated Figure 2: {fig2_path}")

    # -------------------------------------------------------------
    # Figure 3: KUB Patient-Level Split Partitioning
    # -------------------------------------------------------------
    fig3_path = out_dir / "phase04_kub_patient_split_counts.png"
    kub = df[df['dataset'] == 'KUB']
    pt_counts = {sp: kub[kub['split'] == sp]['patient_id'].nunique() for sp in ['TRAIN', 'VAL', 'TEST']}
    total_pts = kub['patient_id'].nunique()

    fig, ax = plt.subplots(figsize=(8, 5.5), dpi=300)
    splits = ['TRAIN', 'VAL', 'TEST']
    pt_vals = [pt_counts[sp] for sp in splits]
    bar_colors = [colors[sp] for sp in splits]

    bars = ax.bar(splits, pt_vals, width=0.5, color=bar_colors, edgecolor='black', linewidth=0.8)
    for bar, sp, val in zip(bars, splits, pt_vals):
        pct = val / total_pts * 100.0
        ax.text(bar.get_x() + bar.get_width() / 2.0, bar.get_height() + 8,
                f"{val} Patients\n({pct:.1f}%)", ha='center', va='bottom', fontweight='bold', fontsize=10)

    ax.set_title(f"KUB-Stone Patient-Level Split Partitioning (N={total_pts} Patients, 0 Overlap)", fontsize=13, fontweight='bold', pad=15)
    ax.set_xlabel("Split Allocation", fontsize=11, fontweight='bold')
    ax.set_ylabel("Unique Patient Count", fontsize=11, fontweight='bold')
    ax.set_ylim(0, 370)
    plt.tight_layout()
    plt.savefig(fig3_path, dpi=300)
    plt.close()
    generated_figures.append(fig3_path)
    print(f"Generated Figure 3: {fig3_path}")

    # -------------------------------------------------------------
    # Figure 4: Split Overlap Matrix (Heatmap)
    # -------------------------------------------------------------
    fig4_path = out_dir / "phase04_split_overlap_matrix.png"
    train_ids = set(df[df['split'] == 'TRAIN']['sample_id'])
    val_ids = set(df[df['split'] == 'VAL']['sample_id'])
    test_ids = set(df[df['split'] == 'TEST']['sample_id'])

    split_sets = [('TRAIN', train_ids), ('VAL', val_ids), ('TEST', test_ids)]
    overlap_matrix = np.zeros((3, 3), dtype=int)
    for i, (_, set_i) in enumerate(split_sets):
        for j, (_, set_j) in enumerate(split_sets):
            overlap_matrix[i, j] = len(set_i & set_j)

    fig, ax = plt.subplots(figsize=(6.5, 5.5), dpi=300)
    cax = ax.matshow(overlap_matrix, cmap='Blues', alpha=0.85)

    for i in range(3):
        for j in range(3):
            val = overlap_matrix[i, j]
            color = 'white' if val > 2000 else 'black'
            label_text = f"{val:,}\n(Disjoint)" if (i != j and val == 0) else f"{val:,}"
            ax.text(j, i, label_text, ha='center', va='center',
                    fontweight='bold', fontsize=11, color=color)

    labels = ['TRAIN', 'VAL', 'TEST']
    ax.set_xticks(range(3))
    ax.set_yticks(range(3))
    ax.set_xticklabels(labels, fontweight='bold', fontsize=10)
    ax.set_yticklabels(labels, fontweight='bold', fontsize=10)
    ax.tick_params(top=True, bottom=False, labeltop=True, labelbottom=False)
    ax.set_title("Canonical Split Membership Disjointness Matrix\n(All Off-Diagonals Exactly 0)", fontsize=12, fontweight='bold', pad=20)
    fig.colorbar(cax, ax=ax, fraction=0.046, pad=0.04)
    plt.tight_layout()
    plt.savefig(fig4_path, dpi=300)
    plt.close()
    generated_figures.append(fig4_path)
    print(f"Generated Figure 4: {fig4_path}")

    # -------------------------------------------------------------
    # Figure 5 (Optional/Bonus): KUB Category x Split Distribution
    # -------------------------------------------------------------
    fig5_path = out_dir / "phase04_kub_category_split_distribution.png"
    cat_ct = pd.crosstab(kub['category'], kub['split'])[['TRAIN', 'VAL', 'TEST']]

    fig, ax = plt.subplots(figsize=(8.5, 5.5), dpi=300)
    x_cat = np.arange(len(cat_ct))
    w = 0.25
    for idx, sp in enumerate(['TRAIN', 'VAL', 'TEST']):
        ax.bar(x_cat + (idx - 1) * w, cat_ct[sp].values, w, label=sp, color=colors[sp], edgecolor='black', linewidth=0.8)
        for i, val in enumerate(cat_ct[sp].values):
            ax.text(x_cat[i] + (idx - 1) * w, val + 15, str(val), ha='center', va='bottom', fontsize=9, fontweight='bold')

    clean_cats = [c.replace('_', ' ') for c in cat_ct.index]
    ax.set_xticks(x_cat)
    ax.set_xticklabels(clean_cats, fontsize=10, fontweight='bold')
    ax.set_title("KUB-Stone Anatomical Category Case-Level Distribution by Split", fontsize=13, fontweight='bold', pad=15)
    ax.set_xlabel("Anatomical Category Metadata (Not Multiclass Pixel Mask)", fontsize=11, fontweight='bold')
    ax.set_ylabel("Case Count", fontsize=11, fontweight='bold')
    ax.set_ylim(0, 1300)
    ax.legend(title="Split Allocation", frameon=True, loc='upper right')
    plt.tight_layout()
    plt.savefig(fig5_path, dpi=300)
    plt.close()
    generated_figures.append(fig5_path)
    print(f"Generated Figure 5: {fig5_path}")

    # Save Figure Manifest
    manifest_records = []
    for fp in generated_figures:
        manifest_records.append({
            "figure_name": fp.name,
            "relative_path": str(fp.relative_to(root)).replace('\\', '/'),
            "file_size_bytes": fp.stat().st_size
        })

    out_json = root / "reports/audits/phase04_figure_manifest.json"
    with open(out_json, "w", encoding="utf-8") as jf:
        json.dump(manifest_records, jf, indent=2)
    print(f"Saved figure manifest: {out_json}")


if __name__ == '__main__':
    generate_figures()

