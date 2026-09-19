import nbformat
from pathlib import Path

nb_path = Path('notebooks/phasewise/phase_14_regional_refiner/phase14_regional_refiner_pipeline_and_diagnostic_analysis.ipynb')
nb = nbformat.read(str(nb_path), as_version=4)

# Update Cell 1
nb.cells[1].source = """from pathlib import Path
import os
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display, Image

def find_root():
    p = Path.cwd()
    for _ in range(5):
        if (p / 'reports').exists() and (p / 'manifests').exists():
            return p
        p = p.parent
    return Path('D:/Softfors/jup')

ROOT = find_root()
mode_path = ROOT / 'reports/tables/phase14_part3_mode_summary.csv'
df_mode = pd.read_csv(mode_path)
display(df_mode[['mode', 'mean_dice_512', 'median_dice_512', 'object_recall_tiny_512', 'hard_tiny_recovered_512', 'global_empty_recovered_512', 'mean_fp_per_image']])
"""

# Update Cell 5
nb.cells[5].source = """import glob
fig_paths = sorted(glob.glob(str(ROOT / 'reports/figures/retrospective/phase10_baselines/case_*.png')))[:16]
print(f"Loaded {len(fig_paths)} deterministic qualitative baseline prediction panels:")
for fp in fig_paths[:4]:
    display(Image(filename=fp, width=800))
print(f"... and {len(fig_paths)-4} more panels available in reports/figures/retrospective/phase10_baselines/")
"""

nbformat.write(nb, str(nb_path))
print("Phase 14 notebook paths updated successfully!")

