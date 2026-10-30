import sys
import traceback
from pathlib import Path

PROJECT_ROOT = Path(r"D:\Softfors\jup")
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "notebooks" / "phasewise" / "phase_12_oracle_roi" / "code"))

from post_phase13_h2a_downstream_eval import main

try:
    result = main()
    print(f"\nResult: {result['status']}")
    sys.exit(0)
except Exception:
    traceback.print_exc()
    sys.exit(1)
