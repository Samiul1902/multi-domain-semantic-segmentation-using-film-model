"""RA-MedFiLM-BARR-Lite -- three-seed training orchestrator (executable entry point).

Usage
-----
    .\\.venv\\Scripts\\python.exe -u scripts/training/lite_barr_three_seed.py --help

    # inspect (no training, no writes)
    .\\.venv\\Scripts\\python.exe -u scripts/training/lite_barr_three_seed.py validate --seed 42
    .\\.venv\\Scripts\\python.exe -u scripts/training/lite_barr_three_seed.py plan     --seed 123

    # synthetic end-to-end integration run (never a scientific result)
    .\\.venv\\Scripts\\python.exe -u scripts/training/lite_barr_three_seed.py dry-run  --seed 42

    # real execution (refused without an operator grant)
    .\\.venv\\Scripts\\python.exe -u scripts/training/lite_barr_three_seed.py run      --seed 42 ^
        --grant-provider my_gate:grant

    # re-verify a completed family, and prove the seeds share no artifact
    .\\.venv\\Scripts\\python.exe -u scripts/training/lite_barr_three_seed.py ^
        verify-family --seed 42 --all-seeds

The script is a thin shell: every behaviour lives in
``src.research.lite_pipeline``.  The Lite family is a separate secondary
experiment; the FULL pipeline and its frozen protocol are untouched by it.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.lite_pipeline.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
