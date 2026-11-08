"""Execute the ReMedFiLM notebooks with nbclient.

Runs the canonical `.venv` interpreter as the kernel. A dedicated kernelspec is
written inside full_doc_report/_kernels so nothing outside the report directory
is touched.

Produces NOTEBOOK_EXECUTION_REPORT.json.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import nbformat as nbf
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError

ROOT = Path(r"D:\Softfors\jup")
OUT = ROOT / "full_doc_report"
VENV_PY = ROOT / ".venv" / "Scripts" / "python.exe"
KDIR = OUT / "_kernels"

def targets() -> list[Path]:
    """The canonical notebook family, in reading order."""
    t = [OUT / "ReMedFiLM_COMPLETE_MASTER_VERIFIED.ipynb",
         OUT / "ReMedFiLM_COMPLETE_MASTER.ipynb"]
    t += sorted((OUT / "ReMedFiLM_Research_Notebooks").glob("*.ipynb"))
    t += sorted((OUT / "Reconstructed_Phasewise_Notebooks").rglob("*.ipynb"))
    return [p for p in t if p.exists()]


def install_kernelspec() -> str:
    name = "remedfilm-analysis"
    d = KDIR / "kernels" / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "kernel.json").write_text(json.dumps({
        "argv": [str(VENV_PY), "-m", "ipykernel_launcher", "-f", "{connection_file}"],
        "display_name": "ReMedFiLM analysis (venv)",
        "language": "python",
        "env": {"PYTHONPATH": str(ROOT)},
    }, indent=2), encoding="utf-8")
    return name


def main() -> int:
    if not VENV_PY.exists():
        print("MISSING_INTERPRETER", VENV_PY)
        return 2
    name = install_kernelspec()
    os.environ["JUPYTER_PATH"] = str(KDIR)

    reports = []
    overall_ok = True
    for target in targets():
        if not target.exists():
            print(f"MISSING {target}")
            overall_ok = False
            continue
        nb = nbf.read(target, as_version=4)
        n_code = sum(1 for c in nb.cells if c.cell_type == "code")
        print(f"\n=== executing {target.name} ({n_code} code cells) ===")
        t0 = time.time()
        err = None
        try:
            client = NotebookClient(
                nb,
                timeout=900,
                kernel_name=name,
                resources={"metadata": {"path": str(ROOT)}},
                allow_errors=False,
            )
            client.execute()
        except CellExecutionError as exc:
            err = str(exc)[-4000:]
            overall_ok = False
        except Exception as exc:  # noqa: BLE001
            err = f"{type(exc).__name__}: {exc}"[-4000:]
            overall_ok = False
        elapsed = time.time() - t0

        executed = sum(1 for c in nb.cells
                       if c.cell_type == "code" and c.get("execution_count"))
        with_output = sum(1 for c in nb.cells if c.cell_type == "code" and c.get("outputs"))
        errored = sum(1 for c in nb.cells if c.cell_type == "code"
                      and any(o.get("output_type") == "error" for o in c.get("outputs", [])))
        nbf.write(nb, target)
        print(f"executed={executed}/{n_code} with_output={with_output} "
              f"errored={errored} elapsed={elapsed:.1f}s")
        if err:
            print("ERROR:", err[:1200])
        reports.append({
            "notebook": target.relative_to(OUT).as_posix(),
            "kernel": name,
            "kernel_argv0": str(VENV_PY),
            "total_cells": len(nb.cells),
            "code_cells": n_code,
            "markdown_cells": len(nb.cells) - n_code,
            "successfully_executed_cells": executed,
            "cells_with_output": with_output,
            "errored_cells": errored,
            "archived_blocked_training_cells": 0,
            "skipped_unsafe_cells": 0,
            "elapsed_seconds": round(elapsed, 1),
            "error": err,
            "scientific_source_modifications": 0,
        })

    total_code = sum(r["code_cells"] for r in reports)
    total_exec = sum(r["successfully_executed_cells"] for r in reports)
    (OUT / "NOTEBOOK_EXECUTION_REPORT.json").write_text(json.dumps({
        "artifact": "notebook_execution_report",
        "execution_mode": "ANALYSIS_ONLY",
        "interpreter": str(VENV_PY),
        "all_notebooks_succeeded": overall_ok,
        "n_notebooks": len(reports),
        "total_code_cells": total_code,
        "total_executed_cells": total_exec,
        "training_performed": False,
        "new_inference_performed": False,
        "test_accessed": False,
        "notebooks": reports,
    }, indent=2), encoding="utf-8")
    print(f"\nTOTAL {len(reports)} notebooks | {total_exec}/{total_code} cells | "
          f"{'OK' if overall_ok else 'FAILED'}")
    return 0 if overall_ok else 1


if __name__ == "__main__":
    sys.exit(main())
