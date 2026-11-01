"""CLI: validate / export C1 run artifacts (read-only on run directories).

  python scripts/analysis/c1_run_artifacts.py validate [--experiment-root DIR]
  python scripts/analysis/c1_run_artifacts.py export   [--experiment-root DIR] [--out-dir DIR]
Missing runs are reported as MISSING; nothing is fabricated. Exit 0 only if all six
runs validate; 3 if any is missing or invalid.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.research.paper_assets.c1_run_export import ARMS, SEEDS, RunArtifactError, export_run, validate_run  # noqa: E402

DEFAULT_ROOT = ROOT / "experiments" / "c1_film_attribution_v1"
DEFAULT_OUT = ROOT / "reports" / "tables" / "c1_results" / "run_exports"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["validate", "export"])
    ap.add_argument("--experiment-root", type=Path, default=DEFAULT_ROOT)
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--allow-synthetic", action="store_true", help="test fixtures only; output stamped SYNTHETIC")
    a = ap.parse_args(argv)
    status, ok = {}, 0
    for s in SEEDS:
        for arm in ARMS:
            d = a.experiment_root / f"seed{s}" / arm
            key = f"seed{s}/{arm}"
            if not d.exists():
                status[key] = "MISSING"
                continue
            try:
                kw = dict(expected_arm=arm, expected_seed=s, allow_synthetic=a.allow_synthetic)
                if a.command == "export":
                    rep = export_run(d, a.out_dir, **kw)
                else:
                    rep = validate_run(d, **kw)
                status[key] = "VALID" + (" (SYNTHETIC)" if rep["synthetic"] else "")
                ok += 1
            except RunArtifactError as e:
                status[key] = f"INVALID:{e}"
    print(json.dumps({"runs_valid": ok, "runs_required": 6, "status": status}, indent=2))
    return 0 if ok == 6 else 3


if __name__ == "__main__":
    raise SystemExit(main())
