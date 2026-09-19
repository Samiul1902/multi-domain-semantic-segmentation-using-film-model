import json
from pathlib import Path

NOTEBOOK_DIR = Path(r'D:\Softfors\jup\notebooks')

nb_cells = [
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "# Phase 6-R2 — KUB Characterization & Publication-Ready Data Analysis\n",
            "\n",
            "This notebook provides a rigorous, publication-ready characterization of the **KUB-StoneX** segmentation dataset using the authoritative `phase4_v2` TRAIN split (n=1,979 samples across 318 unique patients). All statistics are derived deterministically from measured mask parameters.\n",
            "\n",
            "**Test-Set Protection**: Test-set mask morphology is **100% frozen** and was NOT accessed during this analysis."
        ]
    },
    {
        "cell_type": "code",
        "execution_count": 1,
        "metadata": {},
        "outputs": [],
        "source": [
            "import pandas as pd\n",
            "import json\n",
            "import hashlib\n",
            "from pathlib import Path\n",
            "from IPython.display import Image, display\n",
            "\n",
            "tables_dir = Path(r'D:\\Softfors\\jup\\reports\\tables')\n",
            "figures_dir = Path(r'D:\\Softfors\\jup\\reports\\figures\\kub_characterization')\n",
            "qual_dir = Path(r'D:\\Softfors\\jup\\reports\\qualitative\\kub_characterization')\n",
            "manifest_dir = Path(r'D:\\Softfors\\jup\\manifests')\n",
            "\n",
            "# 1. Manifest Hash Guard Check\n",
            "with open(manifest_dir / 'manifest_metadata.json', 'r') as f:\n",
            "    meta = json.load(f)\n",
            "frozen_hashes = meta.get('hashes', {})\n",
            "for fname, expected_hash in frozen_hashes.items():\n",
            "    p = manifest_dir / f'{fname}.csv'\n",
            "    h = hashlib.sha256(open(p, 'rb').read()).hexdigest()\n",
            "    assert h == expected_hash, f'Manifest hash mismatch for {fname}.csv'\n",
            "print('Manifest Guard Verification: PASS (phase4_v2 frozen)')\n",
            "\n",
            "# 2. Load derived v2 tables\n",
            "df_samples = pd.read_csv(tables_dir / 'kub_train_sample_characteristics_v2.csv')\n",
            "df_cat = pd.read_csv(tables_dir / 'kub_category_characteristics_v2.csv')\n",
            "df_summary = pd.read_csv(tables_dir / 'kub_dataset_summary_v2.csv')\n",
            "df_tv = pd.read_csv(tables_dir / 'kub_train_val_distribution_summary_v2.csv')\n",
            "df_components = pd.read_csv(tables_dir / 'kub_train_components_v2.csv')\n",
            "\n",
            "# Invariant Assertions\n",
            "assert len(df_samples) == 1979, 'Sample count != 1979'\n",
            "assert (df_samples['component_count'] >= 1).all(), 'Found empty TRAIN mask!'\n",
            "assert len(df_components) == df_samples['component_count'].sum(), 'Component count mismatch'\n",
            "print('All Data Consistency Invariants PASSED.')\n",
            "\n",
            "print('\\n--- KUB TRAIN DATASET SUMMARY ---')"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": 2,
        "metadata": {},
        "outputs": [],
        "source": [
            "display(df_summary)\n",
            "print('\\n--- KUB CATEGORY CHARACTERISTICS ---')\n",
            "display(df_cat)"
        ]
    }
]


nb_cells.extend([
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## Publication Figures\n",
            "\n",
            "Below are the publication-ready diagnostic figures generated at 300 DPI (saved in `reports/figures/kub_characterization/`)."
        ]
    },
    {
        "cell_type": "code",
        "execution_count": 3,
        "metadata": {},
        "outputs": [],
        "source": [
            "print('Figure A: Category Composition')\n",
            "display(Image(filename=str(figures_dir / 'kub_category_composition_v2.png')))\n",
            "\n",
            "print('Figure B: Foreground Ratio Distribution by Category')\n",
            "display(Image(filename=str(figures_dir / 'kub_foreground_ratio_by_category_v2.png')))\n",
            "\n",
            "print('Figure C: Component Size Distribution')\n",
            "display(Image(filename=str(figures_dir / 'kub_component_size_distribution_v2.png')))\n",
            "\n",
            "print('Figure D: Components per Image')\n",
            "display(Image(filename=str(figures_dir / 'kub_components_per_image_v2.png')))\n",
            "\n",
            "print('Figure E: Component Spatial Centroid Distribution')\n",
            "display(Image(filename=str(figures_dir / 'kub_component_centroids_v2.png')))\n",
            "\n",
            "print('Figure F: Train vs Val Distribution Comparison')\n",
            "display(Image(filename=str(figures_dir / 'kub_train_val_distribution_v2.png')))"
        ]
    },
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## Deterministic Qualitative Panel (TRAIN ONLY)\n",
            "\n",
            "Representative samples spanning lower-tail, median, and upper-tail foreground ratios across stone categories."
        ]
    },
    {
        "cell_type": "code",
        "execution_count": 4,
        "metadata": {},
        "outputs": [],
        "source": [
            "display(Image(filename=str(qual_dir / 'kub_train_qualitative_panel_v2.png')))"
        ]
    },
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## Scientific Interpretation\n",
            "\n",
            "1. **Analysis Population & FOV Mix**: KUB TRAIN contains 1,979 paired samples across 318 unique patients (Kidney_Stone = 1,133, Bladder_Stone = 635, Ureteric_Stone = 211). Raw image dimensions vary from 47x49 cropped ROIs to 3096x3528 radiography plates (median width = 141, height = 154).\n",
            "2. **Foreground Ratio & Semantics**: Measured foreground ratios (`foreground = (mask > 0)`) span from 0.000027 to 0.658871 (median = 0.209896). The elevated median foreground ratio is due to the presence of cropped ROI cutouts in the raw KUB dataset.\n",
            "3. **Connected Components**: 8-connectivity labeling yields 2,376 total components (mean = 1.20 components/image, max = 11). 210 images (10.6%) contain multiple distinct foreground components.\n",
            "4. **Spatial Localization**: Normalized centroids demonstrate clear anatomical distribution (Bladder y_norm median = 0.5374, Kidney y_norm median = 0.4356, Ureteric y_norm median = 0.4964).\n",
            "5. **Train vs Val Density**: Kernel density estimations show consistent distribution alignment between TRAIN (median ratio = 0.209896) and VAL (median ratio = 0.186214)."
        ]
    }
])

nb_json = {
    "cells": nb_cells,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "name": "python",
            "version": "3.11.9"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 4
}

with open(NOTEBOOK_DIR / '04_kub_characterization.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb_json, f, indent=2)

print("Notebook 04 updated successfully.")
