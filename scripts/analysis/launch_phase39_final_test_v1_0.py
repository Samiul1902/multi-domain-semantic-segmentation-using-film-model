"""Phase39 launcher (v1.0) — FROZEN DURING PHASE38.

Pins and verifies the authority bundle + execution/supervisor source SHAs,
enforces output absence, sets the execution gate env var (ONLY when invoked),
and starts the supervisor. Propagates the supervisor exit code. No auto-retry.

DO NOT run this during Phase38. It is the sole Phase39 entry point.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import scripts.analysis.phase39_final_test_common_v1_0 as C  # noqa: E402

EXECUTION_SOURCE = "scripts/analysis/phase39_final_test_execution_v1_0.py"
SUPERVISOR_SOURCE = "scripts/analysis/supervise_phase39_final_test_v1_0.py"


def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main() -> int:
    # 1. authority bundle bound + hash pin verified against the frozen launch authority
    bundle = ROOT / C.AUTHORITY_BUNDLE
    if not bundle.exists():
        print("PHASE39_LAUNCH_FAIL_CLOSED: authority bundle absent", file=sys.stderr)
        return 2
    launch_auth = ROOT / "reports/audits/phase38_phase39_launch_authority_sha.json"
    if not launch_auth.exists():
        print("PHASE39_LAUNCH_FAIL_CLOSED: launch authority absent", file=sys.stderr)
        return 2
    auth = json.loads(launch_auth.read_text(encoding="utf-8"))
    if _sha(bundle) != auth["authority_bundle_sha256"]:
        print("PHASE39_LAUNCH_FAIL_CLOSED: authority bundle SHA mismatch", file=sys.stderr)
        return 2
    if _sha(ROOT / EXECUTION_SOURCE) != auth["execution_source_sha256"]:
        print("PHASE39_LAUNCH_FAIL_CLOSED: execution source SHA mismatch", file=sys.stderr)
        return 2
    if _sha(ROOT / SUPERVISOR_SOURCE) != auth["supervisor_sha256"]:
        print("PHASE39_LAUNCH_FAIL_CLOSED: supervisor source SHA mismatch", file=sys.stderr)
        return 2

    # 2. output absence gate (no duplicate attempt)
    for rel in (C.OUT["START"], C.OUT["RESULT"], C.OUT["FAILURE"], C.OUT["PROCESS_EXIT"]):
        if (ROOT / rel).exists():
            print(f"PHASE39_LAUNCH_FAIL_CLOSED: output target exists: {rel}", file=sys.stderr)
            return 2

    # 3. set the one-shot execution gate env var and start the supervisor
    env = dict(os.environ)
    env[C.GATE_ENV] = C.GATE_ENV_VALUE
    proc = subprocess.run([sys.executable, str(ROOT / SUPERVISOR_SOURCE)], env=env, cwd=str(ROOT))
    return int(proc.returncode)  # propagate exactly; no auto-retry


if __name__ == "__main__":
    raise SystemExit(main())
