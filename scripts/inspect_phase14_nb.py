import nbformat
from pathlib import Path

nb_path = Path('notebooks/phasewise/phase_14_regional_refiner/phase14_regional_refiner_pipeline_and_diagnostic_analysis.ipynb')
nb = nbformat.read(str(nb_path), as_version=4)

for i, cell in enumerate(nb.cells):
    print(f"Cell {i} ({cell.cell_type}):")
    print(cell.source[:200])
    print("-" * 40)

