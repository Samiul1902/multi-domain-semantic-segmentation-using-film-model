"""Phase39 v1.2 launcher — post-protocol technical-recovery revision.

Authority: reports/audits/phase39_post_protocol_technical_recovery_amendment.json.
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

import scripts.analysis.phase39_final_test_common_v1_2 as C  # noqa: E402

EXECUTION_SOURCE = "scripts/analysis/phase39_final_test_execution_v1_2.py"
SUPERVISOR_SOURCE = "scripts/analysis/supervise_phase39_final_test_v1_2.py"
LAUNCH_AUTH = "reports/audits/phase39_v1_2_launch_authority_sha.json"


def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def verify_only() -> dict:
    checks = {}
    auth_p = ROOT / LAUNCH_AUTH
    checks["launch_auth_present"] = auth_p.exists()
    if not auth_p.exists():
        return checks
    auth = json.loads(auth_p.read_text(encoding="utf-8"))
    checks["amendment_sha_match"] = _sha(ROOT / C.AMENDMENT) == auth["amendment_sha256"]
    checks["authority_bundle_sha_match"] = _sha(ROOT / C.AUTHORITY_BUNDLE) == auth["authority_bundle_sha256"]
    checks["execution_source_sha_match"] = _sha(ROOT / EXECUTION_SOURCE) == auth["execution_source_sha256"]
    checks["supervisor_sha_match"] = _sha(ROOT / SUPERVISOR_SOURCE) == auth["supervisor_sha256"]
    checks["launcher_sha_match"] = _sha(Path(__file__)) == auth["launcher_sha256"]
    checks["all_v1_2_targets_absent"] = all(not (ROOT / C.OUT[k]).exists() for k in
                                             ("START", "RESULT", "FAILURE", "PROCESS_EXIT"))
    return checks


def main() -> int:
    checks = verify_only()
    if not all(checks.values()):
        print(f"PHASE39_V1_2_LAUNCH_FAIL_CLOSED: {checks}", file=sys.stderr)
        return 2
    env = dict(os.environ)
    env[C.GATE_ENV] = C.GATE_ENV_VALUE
    proc = subprocess.run([sys.executable, str(ROOT / SUPERVISOR_SOURCE)], env=env, cwd=str(ROOT))
    return int(proc.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
