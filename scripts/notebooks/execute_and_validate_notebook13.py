"""Execute and validate all cells in notebooks/13_phase14_regional_refiner_diagnostic.ipynb."""

import hashlib
import json
from pathlib import Path
import sys

from nbclient import NotebookClient
import nbformat as nbf

PROJECT_ROOT = Path(__file__).resolve().parents[2]
NB_PATH = PROJECT_ROOT / "notebooks" / "13_phase14_regional_refiner_diagnostic.ipynb"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    print(f"[Execute Notebook] Reading {NB_PATH}...")
    with open(NB_PATH, "r", encoding="utf-8") as f:
        nb = nbf.read(f, as_version=4)

    client = NotebookClient(
        nb,
        timeout=600,
        kernel_name="python3",
        resources={"metadata": {"path": str(PROJECT_ROOT / "notebooks")}},
    )

    print("[Execute Notebook] Executing all cells...")
    client.execute()

    print(f"[Execute Notebook] Saving executed notebook to {NB_PATH}...")
    with open(NB_PATH, "w", encoding="utf-8") as f:
        nbf.write(nb, f)

    # Validate cells and outputs
    error_count = 0
    executed_code_count = 0
    total_code_count = 0

    for idx, cell in enumerate(nb.cells):
        if cell.cell_type == "code":
            total_code_count += 1
            if cell.get("execution_count") is not None:
                executed_code_count += 1
            for out in cell.get("outputs", []):
                if out.get("output_type") == "error":
                    error_count += 1
                    print(f"Error in cell {idx}: {out.get('ename')}: {out.get('evalue')}")

    sha = sha256_file(NB_PATH)
    print(f"[Execute Notebook] Execution complete.")
    print(f"  Total code cells: {total_code_count}")
    print(f"  Executed code cells: {executed_code_count}")
    print(f"  Errors: {error_count}")
    print(f"  Final Notebook SHA-256: {sha}")

    if error_count > 0:
        raise RuntimeError(f"Notebook execution encountered {error_count} errors.")
    if executed_code_count != total_code_count:
        raise RuntimeError(f"Not all code cells were executed: {executed_code_count}/{total_code_count}")

    print("[Execute Notebook] PASS: 0 errors.")


if __name__ == "__main__":
    main()

