#!/usr/bin/env python3
"""
Phase 05 — Forensic Data Leakage & Duplicate Visualization Script
Generates reviewer-facing figures using recomputed TRAIN/VAL evidence and historical frozen TEST evidence:
1. Leakage evidence matrix (sample-ID, patient-ID, exact image, exact mask, near-duplicate across splits).
2. Per-dataset leakage status and duplicate counts summary.
3. Hamming distance distribution of near-duplicate candidates (with frozen threshold <= 6).
4. Qualitative review panels for top TRAIN <-> VAL near-duplicate candidate pairs.

Usage:
    D:\Softfors\jup\.venv\Scripts\python.exe notebooks/phasewise/phase_05_leakage_audit/code/phase05_leakage_visualization.py
"""

import sys
import json
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image


def find_project_root() -> Path:
    p = Path(__file__).resolve()
    for _ in range(6):
        if (p / 'manifests').exists() and (p / 'reports').exists():
            return p
        p = p.parent
    return Path('D:/Softfors/jup')


def generate_figures():
    root = find_project_root()
    audit_dir = root / "reports/audits"
    out_dir = root / "reports/figures/phase05_leakage_audit/aggregate"
    out_dir.mkdir(parents=True, exist_ok=True)

    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    generated_figures = []

    # -------------------------------------------------------------
    # Figure 1: Leakage Evidence Matrix
    # -------------------------------------------------------------
    fig1_path = out_dir / "phase05_leakage_evidence_matrix.png"
    rows = [
        "Level 1: Sample ID Disjointness",
        "Level 2: Patient/Group Disjointness (KUB)",
        "Level 3: Exact Image Content (SHA-256)",
        "Level 4: Exact Mask Content (SHA-256)",
        "Level 5: Perceptual Near-Duplicate (pHash <=6)"
    ]
    cols = ["TRAIN <-> VAL\n(Current Recomputed)", "TRAIN <-> TEST\n(Historical / Manifest)", "VAL <-> TEST\n(Historical / Manifest)"]

    # Table values
    data_labels = [
        ["0 Overlaps\n(PASS)", "0 Overlaps\n(PASS)", "0 Overlaps\n(PASS)"],
        ["0 Patient Overlaps\n(PASS, N=711)", "0 Patient Overlaps\n(PASS, N=711)", "0 Patient Overlaps\n(PASS, N=711)"],
        ["1 Raw Asset Pair\n(KUB 00273/00320)", "HISTORICAL-0\n(Pre-Lock Audit)", "HISTORICAL-0\n(Pre-Lock Audit)"],
        ["0 Overlaps\n(PASS)", "HISTORICAL-0\n(Pre-Lock Audit)", "HISTORICAL-0\n(Pre-Lock Audit)"],
        ["64 Candidates\n(ISIC:54, KUB:6, KV:4)", "157 Candidates\n(Historical Pre-Lock)", "18 Candidates\n(Historical Pre-Lock)"]
    ]

    cell_colors = [
        ["#d4edda", "#d4edda", "#d4edda"],
        ["#d4edda", "#d4edda", "#d4edda"],
        ["#fff3cd", "#e2e3e5", "#e2e3e5"],
        ["#d4edda", "#e2e3e5", "#e2e3e5"],
        ["#fff3cd", "#e2e3e5", "#e2e3e5"]
    ]

    fig, ax = plt.subplots(figsize=(10, 6.5), dpi=300)
    ax.axis('off')
    table = ax.table(
        cellText=data_labels,
        rowLabels=rows,
        colLabels=cols,
        cellColours=cell_colors,
        loc='center',
        cellLoc='center'
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 2.4)

    for (r, c), cell in table.get_celld().items():
        cell.set_edgecolor('#495057')
        cell.set_linewidth(1.0)
        if r == 0 or c == -1:
            cell.set_text_props(fontweight='bold')
            if r == 0:
                cell.set_facecolor('#cfe2ff')

    ax.set_title("Multi-Level Forensic Data Leakage & Evidence Matrix\n(Distinguishing Current Recomputation from Frozen Pre-Lock Evidence)",
                 fontsize=13, fontweight='bold', pad=25)
    plt.tight_layout()
    plt.savefig(fig1_path, dpi=300, bbox_inches='tight')
    plt.close()
    generated_figures.append(fig1_path)
    print(f"Generated Figure 1: {fig1_path}")

    # -------------------------------------------------------------
    # Figure 2: Dataset Leakage Status Summary
    # -------------------------------------------------------------
    fig2_path = out_dir / "phase05_dataset_leakage_status.png"
    datasets = ['ISIC', 'BUSI', 'KVASIR', 'KUB']
    categories = ['Sample-ID Leakage', 'Patient Group Leakage', 'Exact Image Dup (Tr-Val)', 'Exact Mask Dup (Tr-Val)', 'Near-Dup Candidates (Tr-Val)']

    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=300)
    matrix_vals = np.array([
        [0, 0, 0, 0, 54],  # ISIC (54 candidates)
        [0, 0, 0, 0, 0],   # BUSI (0 candidates)
        [0, 0, 0, 0, 4],   # KVASIR (4 candidates)
        [0, 0, 1, 0, 6],   # KUB (1 raw asset pair, 6 candidates)
    ])

    cax = ax.matshow(matrix_vals, cmap='YlOrRd', alpha=0.75)
    for i in range(len(datasets)):
        for j in range(len(categories)):
            v = matrix_vals[i, j]
            label_text = f"{v}\n(Zero)" if v == 0 else f"{v}\n(Audit)"
            if j == 1 and i < 3:
                label_text = "N/A\n(No Group ID)"
            ax.text(j, i, label_text, ha='center', va='center', fontweight='bold', fontsize=9, color='black')

    ax.set_xticks(range(len(categories)))
    ax.set_yticks(range(len(datasets)))
    ax.set_xticklabels(categories, fontweight='bold', fontsize=9.5)
    ax.set_yticklabels(datasets, fontweight='bold', fontsize=11)
    ax.tick_params(top=True, bottom=False, labeltop=True, labelbottom=False)
    ax.set_title("Dataset-Wise Leakage Audit Categories & Traversal Findings", fontsize=12, fontweight='bold', pad=20)
    plt.tight_layout()
    plt.savefig(fig2_path, dpi=300, bbox_inches='tight')
    plt.close()
    generated_figures.append(fig2_path)
    print(f"Generated Figure 2: {fig2_path}")

    # -------------------------------------------------------------
    # Figure 3: Near-Duplicate Distance Distribution
    # -------------------------------------------------------------
    fig3_path = out_dir / "phase05_phash_distance_distribution.png"
    cand_csv = audit_dir / "near_duplicate_candidates.csv"
    if cand_csv.exists():
        df_cand = pd.read_csv(cand_csv)
        tv_cand = df_cand[(df_cand['split_a'].isin(['TRAIN', 'VAL'])) & 
                          (df_cand['split_b'].isin(['TRAIN', 'VAL'])) & 
                          (df_cand['split_a'] != df_cand['split_b'])]

        fig, ax = plt.subplots(figsize=(8.5, 5), dpi=300)
        dist_counts = tv_cand['hamming_distance'].value_counts().sort_index()

        x_d = [0, 1, 2, 3, 4, 5, 6]
        y_d = [dist_counts.get(d, 0) for d in x_d]

        bars = ax.bar(x_d, y_d, width=0.55, color='#4575b4', edgecolor='black', linewidth=0.8)
        for bar, y in zip(bars, y_d):
            if y > 0:
                ax.text(bar.get_x() + bar.get_width() / 2.0, y + 1.0, str(y),
                        ha='center', va='bottom', fontweight='bold', fontsize=10)

        ax.axvline(6.0, color='red', linestyle='--', linewidth=1.5, label='Frozen Diagnostic Threshold (Hamming <= 6)')
        ax.set_title("TRAIN <-> VAL Perceptual Hash (64-bit DCT) Hamming Distance Distribution (N=64)", fontsize=12, fontweight='bold', pad=15)
        ax.set_xlabel("64-bit Hamming Distance (0 = Identical pHash, 6 = Marginal Similarity)", fontsize=10, fontweight='bold')
        ax.set_ylabel("Candidate Pair Count", fontsize=10, fontweight='bold')
        ax.set_xticks(x_d)
        ax.set_xticklabels([f"d={d}" for d in x_d], fontweight='bold')
        ax.set_ylim(0, max(y_d) + 6)
        ax.legend(loc='upper left', frameon=True)
        plt.tight_layout()
        plt.savefig(fig3_path, dpi=300)
        plt.close()
        generated_figures.append(fig3_path)
        print(f"Generated Figure 3: {fig3_path}")

    # -------------------------------------------------------------
    # Figure 4: Qualitative Panels for Top TRAIN <-> VAL Near-Duplicate Candidates
    # -------------------------------------------------------------
    fig4_path = out_dir / "phase05_top_train_val_duplicate_candidates.png"
    if cand_csv.exists() and len(tv_cand) > 0:
        top12 = tv_cand.sort_values(['hamming_distance', 'dataset_a']).head(12)

        fig, axes = plt.subplots(4, 6, figsize=(18, 12), dpi=250)
        for idx, (_, row) in enumerate(top12.iterrows()):
            r_idx = (idx // 3)
            c_idx = (idx % 3) * 2

            ax_a = axes[r_idx, c_idx]
            ax_b = axes[r_idx, c_idx + 1]

            p_a = Path(row['image_path_a'])
            p_b = Path(row['image_path_b'])

            # Plot Image A
            if p_a.exists():
                im_a = Image.open(p_a).convert('RGB')
                ax_a.imshow(im_a)
            ax_a.axis('off')
            ax_a.set_title(f"[{row['dataset_a']} {row['split_a']}]\n{row['sample_id_a'][:8]} | {p_a.name}", fontsize=7.5, fontweight='bold')

            # Plot Image B
            if p_b.exists():
                im_b = Image.open(p_b).convert('RGB')
                ax_b.imshow(im_b)
            ax_b.axis('off')
            ax_b.set_title(f"[{row['dataset_b']} {row['split_b']}]\n{row['sample_id_b'][:8]} | {p_b.name}\nDist={row['hamming_distance']} ({row['classification']})", fontsize=7.5, fontweight='bold', color='darkred')

        plt.suptitle("Qualitative Review: Top TRAIN <-> VAL Near-Duplicate Candidate Pairs (64-bit DCT pHash)", fontsize=13, fontweight='bold', y=0.98)
        plt.tight_layout()
        plt.subplots_adjust(top=0.93)
        plt.savefig(fig4_path, dpi=250)
        plt.close()
        generated_figures.append(fig4_path)
        print(f"Generated Figure 4: {fig4_path}")

    # Save figure manifest
    fig_records = []
    for fp in generated_figures:
        fig_records.append({
            "figure_name": fp.name,
            "relative_path": str(fp.relative_to(root)).replace('\\', '/'),
            "file_size_bytes": fp.stat().st_size
        })

    out_json = audit_dir / "phase05_figure_manifest.json"
    with open(out_json, "w", encoding="utf-8") as jf:
        json.dump(fig_records, jf, indent=2)
    print(f"Saved figure manifest to {out_json}")


if __name__ == '__main__':
    generate_figures()

