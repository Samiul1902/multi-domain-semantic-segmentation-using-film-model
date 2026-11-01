"""CLI for preparing and smoke-testing controlled C3 baseline runs."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.research.c3_baselines.experiment import main

if __name__ == "__main__":
    raise SystemExit(main())
