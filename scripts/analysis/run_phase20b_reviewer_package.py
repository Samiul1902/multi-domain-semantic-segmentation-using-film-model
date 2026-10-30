"""Build the Phase-20B reviewer-package figures + inventories from persisted artifacts.

Reads ONLY persisted artifacts. No training, no inference, no TEST, no checkpoint load.

    ./.venv/Scripts/python.exe scripts/analysis/run_phase20b_reviewer_package.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.analysis import phase20b_figures as F  # noqa: E402
from src.analysis import phase20b_reviewer as R  # noqa: E402


def main() -> int:
    t0 = time.time()
    print("=== PHASE-20B REVIEWER PACKAGE — FIGURE BUILD ===")
    F.build_all()
    out = F.write_inventories()
    inv = out["inventory"]
    cov = out["coverage"]

    print()
    print(f"figures total      : {len(inv)}")
    print(f"embedded in notebook: {int(inv['embedded_in_notebook'].sum())}")
    print("by group:")
    for g, n in inv.groupby("group").size().items():
        print(f"   {g:<16} {n}")
    print()
    print(f"evaluation matrices: {len(cov)} | visualized: {(cov['status'] == 'VISUALIZED').sum()} "
          f"| coverage: {(cov['status'] == 'VISUALIZED').mean():.4f}")
    missing = cov[cov["status"] != "VISUALIZED"]
    if len(missing):
        print("MISSING:", missing["matrix_name"].tolist())
    print()
    print("inventory csv :", R.rel(out["inventory_csv"]))
    print("inventory json:", R.rel(out["inventory_json"]))
    print("coverage csv  :", R.rel(out["coverage_csv"]))
    print(f"elapsed: {time.time() - t0:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
