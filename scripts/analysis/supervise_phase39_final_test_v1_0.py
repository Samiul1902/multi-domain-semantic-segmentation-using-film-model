"""Phase39 supervisor (v1.0) — FROZEN DURING PHASE38.

Spawns exactly one execution-source child, captures stdout/stderr to a
journal, and propagates the child exit code. NO automatic relaunch.
Interruption (KeyboardInterrupt / SIGINT) may NEVER become rc=0.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import scripts.analysis.phase39_final_test_common_v1_0 as C  # noqa: E402

EXECUTION_SOURCE = "scripts/analysis/phase39_final_test_execution_v1_0.py"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> int:
    child_cmd = [sys.executable, str(ROOT / EXECUTION_SOURCE)]
    try:
        proc = subprocess.run(child_cmd, cwd=str(ROOT))
        rc = int(proc.returncode)
    except KeyboardInterrupt:
        # Interruption may NEVER become rc=0.
        rc = 130
    # journal the termination (append; not a write-once scientific artifact)
    jp = ROOT / C.OUT["journal"]
    jp.parent.mkdir(parents=True, exist_ok=True)
    with open(jp, "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"supervisor": "v1_0", "child_rc": rc,
                             "termination_kind": "NORMAL_CHILD_COMPLETION" if rc >= 0 else "ABNORMAL",
                             "generated_utc": _now()}) + "\n")
    return rc  # propagate exactly; no auto-relaunch


if __name__ == "__main__":
    raise SystemExit(main())
