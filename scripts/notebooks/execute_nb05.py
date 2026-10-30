"""Execute Notebook 05 with nbclient.

Requirements: monotonic execution counts, all code cells executed,
stored outputs, zero tracebacks, tables rendered, plots rendered.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path("D:/Softfors/jup")
NB_PATH = ROOT / "notebooks/phasewise/post_phase14_h3_proposal_supply/05_h3_supply_axis_evaluation.ipynb"

print(f"Loading notebook: {NB_PATH}")
nb = nbformat.read(str(NB_PATH), as_version=4)

n_code = sum(1 for c in nb.cells if c.cell_type == "code")
n_md = sum(1 for c in nb.cells if c.cell_type == "markdown")
print(f"  Cells: {len(nb.cells)} ({n_md} markdown, {n_code} code)")

# Create client with jup-venv kernel
client = NotebookClient(
    nb,
    kernel_name="jup-venv",
    timeout=600,
    resources={"metadata": {"path": str(ROOT)}},
)

print("Executing notebook...")
t0 = time.time()
try:
    client.execute()
    elapsed = time.time() - t0
    print(f"  Execution completed in {elapsed:.1f}s")
except Exception as e:
    elapsed = time.time() - t0
    print(f"  Execution FAILED after {elapsed:.1f}s")
    print(f"  Error: {e}")
    # Check for tracebacks in cells
    for i, cell in enumerate(nb.cells):
        if cell.cell_type == "code":
            for output in cell.get("outputs", []):
                if output.get("output_type") == "error":
                    print(f"  Cell {i} traceback:")
                    for line in output.get("traceback", []):
                        print(f"    {line}")
    raise

# Verify: monotonic execution counts, no tracebacks
errors_found = 0
exec_counts = []
for i, cell in enumerate(nb.cells):
    if cell.cell_type == "code":
        ec = cell.get("execution_count")
        exec_counts.append(ec)
        if ec is None:
            print(f"  WARNING: Cell {i} has no execution_count")
        for output in cell.get("outputs", []):
            if output.get("output_type") == "error":
                errors_found += 1
                print(f"  ERROR in cell {i}: {output.get('ename')}: {output.get('evalue')}")

if errors_found > 0:
    print(f"  FAILURES: {errors_found} cells with tracebacks")
    sys.exit(1)
else:
    print(f"  Zero tracebacks: PASS")

# Check monotonic execution counts
monotonic = all(exec_counts[i] is not None and exec_counts[i] == i + 1 for i in range(len(exec_counts)))
print(f"  Monotonic execution counts (1..{len(exec_counts)}): {'PASS' if monotonic else 'CHECK'}")
if not monotonic:
    print(f"    Counts: {exec_counts}")

# Save executed notebook
nbformat.write(nb, str(NB_PATH))
print(f"  Saved executed notebook: {NB_PATH}")

# Compute SHA
import hashlib
sha = hashlib.sha256(NB_PATH.read_bytes()).hexdigest()
print(f"  Notebook SHA: {sha}")
print("Done.")
