"""Execute the H2B-B1 reviewer notebook (READ-ONLY Run-All)."""
import sys
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(r"D:/Softfors/jup")
NB = (ROOT / "notebooks/phasewise/phase_13_predicted_roi_localization"
      / "post_phase13_h2c_downstream_analysis.ipynb")
nb = nbformat.read(str(NB), as_version=4)
client = NotebookClient(nb, timeout=1800, kernel_name="jup-venv", record_timing=False,
                        resources={"metadata": {"path": str(NB.parent)}})
client.execute()
for cell in nb.cells:
    cell.get("metadata", {}).pop("execution", None)
    merged = []
    for out in cell.get("outputs", []):
        if (merged and out.get("output_type") == "stream"
                and merged[-1].get("output_type") == "stream"
                and merged[-1].get("name") == out.get("name")):
            prev = merged[-1]["text"]; prev = "".join(prev) if isinstance(prev, list) else prev
            cur = out["text"]; cur = "".join(cur) if isinstance(cur, list) else cur
            merged[-1]["text"] = prev + cur
        else:
            if out.get("output_type") == "stream" and isinstance(out.get("text"), list):
                out["text"] = "".join(out["text"])
            merged.append(out)
    if "outputs" in cell:
        cell["outputs"] = merged
nbformat.write(nb, str(NB))
code = [c for c in nb.cells if c.cell_type == "code"]
unex = [i for i, c in enumerate(code) if c.get("execution_count") is None]
errs = [i for i, c in enumerate(code) if any(o.get("output_type") == "error" for o in c.get("outputs", []))]
print(f"cells={len(nb.cells)} code={len(code)} unexecuted={len(unex)} errors={len(errs)}")
for i in errs:
    for o in code[i].get("outputs", []):
        if o.get("output_type") == "error":
            print(f"ERROR cell {i}:", o.get("ename"), o.get("evalue"))
sys.exit(1 if (unex or errs) else 0)
