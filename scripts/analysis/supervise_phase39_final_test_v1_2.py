"""Phase39 v1.2 supervisor — spawns exactly one v1.2 child, propagates rc.

No automatic relaunch. Interruption may NEVER become rc=0.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import scripts.analysis.phase39_final_test_common_v1_2 as C  # noqa: E402

EXECUTION_SOURCE = "scripts/analysis/phase39_final_test_execution_v1_2.py"


def main() -> int:
    try:
        proc = subprocess.run([sys.executable, str(ROOT / EXECUTION_SOURCE)], cwd=str(ROOT))
        rc = int(proc.returncode)
    except KeyboardInterrupt:
        rc = 130
    jp = ROOT / C.OUT["journal"]
    jp.parent.mkdir(parents=True, exist_ok=True)
    with open(jp, "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"supervisor": "v1_2", "child_rc": rc,
                             "termination_kind": "NORMAL_CHILD_COMPLETION" if rc >= 0 else "ABNORMAL",
                             "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}) + "\n")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
