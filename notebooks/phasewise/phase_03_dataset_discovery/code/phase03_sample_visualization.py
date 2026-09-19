#!/usr/bin/env python3
"""
Phase 03 — Multi-Domain Dataset Sample Visualization Script
Renders 12 deterministic TRAIN samples per dataset across 3 pages (4 cases/page).
Each row displays: Original Image | Ground-Truth Binary Mask | High-Contrast Contour Overlay.

Usage:
    D:\\Softfors\\jup\\.venv\\Scripts\\python.exe notebooks/phasewise/phase_03_dataset_discovery/code/phase03_sample_visualization.py
"""

import sys
import json
import hashlib
from pathlib import Path
import pandas as pd
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt


def find_project_root() -> Path:
    p = Path(__file__).resolve()
    for _ in range(6):
        if (p / 'reports').exists() and (p / 'manifests').exists():
            return p
        p = p.parent
    return Path('D:/Softfors/jup')


def compute_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def render_dataset_pages():
    root = find_project_root()
    selection_csv = root / "reports/tables/phase03_train_sample_selection.csv"
    if not selection_csv.exists():
        print(f"Error: Selection CSV not found: {selection_csv}")
        return 1

    df_sel = pd.read_csv(selection_csv)
    print(f"Loaded {len(df_sel)} selected cases from {selection_csv.name}")

    out_dir = root / "reports/figures/phase03_dataset_discovery/sample_data"
    out_dir.mkdir(parents=True, exist_ok=True)

    datasets = ["ISIC", "BUSI", "KVASIR", "KUB"]
    figure_manifest = []

    for ds in datasets:
        ds_cases = df_sel[df_sel["dataset"] == ds].sort_values("sample_rank").reset_index(drop=True)
        assert len(ds_cases) == 12, f"Expected 12 cases for {ds}, got {len(ds_cases)}"

        # Render 3 pages, 4 cases per page
        for page_idx in range(3):
            page_num = page_idx + 1
            cases_page = ds_cases.iloc[page_idx * 4 : (page_idx + 1) * 4]

            fig, axes = plt.subplots(4, 3, figsize=(14, 16))
            page_sample_ids = []

            for row_idx, (_, row) in enumerate(cases_page.iterrows()):
                sample_id = str(row["sample_id"])
                page_sample_ids.append(sample_id)
                img_p = Path(row["image_path_or_canonical_reference"])
                mask_p = Path(row["mask_path_or_canonical_reference"])

                # Load image
                pil_img = Image.open(img_p)
                img_mode = pil_img.mode
                img_arr = np.array(pil_img)

                # Load mask
                pil_mask = Image.open(mask_p).convert("L")
                mask_arr = (np.array(pil_mask) > 127).astype(np.uint8)

                # Format RGB image for display
                if img_arr.ndim == 2: # Grayscale
                    disp_img = np.stack([img_arr]*3, axis=-1)
                elif img_arr.ndim == 3 and img_arr.shape[2] == 4: # RGBA
                    disp_img = img_arr[:, :, :3]
                else:
                    disp_img = img_arr

                # Create high-contrast green contour overlay
                overlay = disp_img.copy()
                # Find boundary pixels of mask
                pad_m = np.pad(mask_arr, 1, mode='constant', constant_values=0)
                # Compute morphological boundary
                boundary = mask_arr & ~((pad_m[:-2, 1:-1] & pad_m[2:, 1:-1] & pad_m[1:-1, :-2] & pad_m[1:-1, 2:]))
                # Thicken boundary slightly for visibility
                from scipy.ndimage import binary_dilation
                dilated_b = binary_dilation(boundary, iterations=max(1, int(img_arr.shape[0] / 300)))
                overlay[dilated_b] = [0, 255, 0] # Bright green contour

                # Column 0: Original Image
                ax_orig = axes[row_idx, 0]
                if ds in ["KUB", "BUSI"] and img_mode == "L":
                    ax_orig.imshow(img_arr, cmap="gray")
                else:
                    ax_orig.imshow(disp_img)
                ax_orig.set_title(f"Case {row['sample_rank']:02d}: {sample_id[:20]}\n{img_arr.shape[1]}x{img_arr.shape[0]} | Split: {row['split']}", fontsize=10, fontweight="bold")
                ax_orig.axis("off")

                # Column 1: Ground-Truth Binary Mask
                ax_mask = axes[row_idx, 1]
                ax_mask.imshow(mask_arr, cmap="gray", vmin=0, vmax=1)
                fg_px = int(mask_arr.sum())
                fg_pct = (fg_px / mask_arr.size) * 100
                ax_mask.set_title(f"Ground-Truth Mask\nFG Pixels: {fg_px:,} ({fg_pct:.2f}%)", fontsize=10)
                ax_mask.axis("off")

                # Column 2: High-Contrast Contour Overlay
                ax_over = axes[row_idx, 2]
                ax_over.imshow(overlay)
                cat_info = f" | {row['category']}" if row['category'] != "N/A" else ""
                ax_over.set_title(f"Overlay (Green Contour){cat_info}", fontsize=10)
                ax_over.axis("off")

            fig.suptitle(f"{ds} Modality — Deterministic TRAIN Samples (Page {page_num} of 3, Cases {page_idx*4+1}–{(page_idx+1)*4})", fontsize=14, fontweight="bold", y=0.99)
            plt.tight_layout()

            page_file = out_dir / f"{ds.lower()}_samples_page{page_num:02d}.png"
            plt.savefig(str(page_file), dpi=130, bbox_inches="tight")
            plt.close()

            page_sha = compute_sha256(page_file)
            figure_manifest.append({
                "dataset": ds,
                "page": page_num,
                "figure_file": str(page_file.relative_to(root)).replace("\\", "/"),
                "sample_ids": page_sample_ids,
                "sha256": page_sha
            })
            print(f"Rendered {ds} Page {page_num} -> {page_file.name} (SHA: {page_sha[:12]}...)")

    manifest_p = root / "reports/audits/phase03_figure_manifest.json"
    with open(manifest_p, "w", encoding="utf-8") as jf:
        json.dump(figure_manifest, jf, indent=2)
    print(f"\nSaved Phase 03 figure manifest ({len(figure_manifest)} pages) to {manifest_p.name}")
    return 0


if __name__ == "__main__":
    sys.exit(render_dataset_pages())

