"""Phase 25G spec audit — ORCHESTRATOR.

Runs PART 1 (§0-§3), PART 2 (§4-§12), PART 3 (§13-§26) in order.

GOVERNANCE / SPECIFICATION ONLY. No execution. No holdout/VAL808/TEST reads.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_phase25g_spec_audit_part1 as P1  # noqa: E402
import run_phase25g_spec_audit_part2 as P2  # noqa: E402
import run_phase25g_spec_audit_part3 as P3  # noqa: E402
import phase25g_spec_common as C  # noqa: E402


def main() -> int:
    print("=" * 72)
    print("PHASE 25G — PRE-EXECUTION INTEGRATED EVALUATION SPECIFICATION AUDIT")
    print("=" * 72)

    rc = P1.main()
    if rc != 0:
        print("\nPART 1 failed; aborting (predecessor drift).")
        return rc
    print()
    P2.main()
    print()
    P3.main()

    term = C.jload(C.AUD / "phase25g_specification_terminal.json")
    print()
    print("=" * 72)
    print("phase25g_spec   :", term.get("phase25g_spec"))
    print("phase25g_status :", term.get("phase25g_status"))
    print("TERMINAL        :", term.get("terminal"))
    print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
