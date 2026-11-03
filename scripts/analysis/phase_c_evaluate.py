"""Phase C unified eight-model evaluation CLI (no training, no protected access)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.research.evaluation.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
