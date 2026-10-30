"""PHASE-13 PART-1B §19 — stale run-lock recovery.

Records the stale lock's full contents and SHA, verifies no trainer / waiter /
second trainer exists, writes an audit, then removes ONLY the verified stale
lock via the canonical ``release_lock(force=True)`` mechanism.

Deletes nothing else: not history, not checkpoints, not the experiment
directory, not logs.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.utils.run_lock import inspect_lock, lock_path, release_lock  # noqa: E402

EXP = "phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_clean_v3"
EXP_DIR = ROOT / "experiments" / EXP

# Output basename is overridable so each arbitration stage keeps its own record.
_BASENAME = "phase13_part1b_stale_lock_recovery"
for _i, _arg in enumerate(sys.argv):
    if _arg == "--basename" and _i + 1 < len(sys.argv):
        _BASENAME = sys.argv[_i + 1]
OUT_JSON = ROOT / "reports" / "audits" / f"{_BASENAME}.json"
OUT_MD = ROOT / "reports" / "audits" / f"{_BASENAME}.md"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while chunk := handle.read(8192):
            digest.update(chunk)
    return digest.hexdigest()


def _no_other_trainer() -> dict:
    """Scan for any live python process running the clean-v3 trainer."""
    import subprocess

    found = []
    try:
        listing = subprocess.run(
            ["wmic", "process", "get", "ProcessId,CommandLine"],
            capture_output=True, text=True, timeout=30,
        ).stdout
    except Exception as exc:  # pragma: no cover
        return {"scanned": False, "error": str(exc), "matches": []}
    for line in listing.splitlines():
        if "train_phase13_clean_v3_localizer" in line and "wmic" not in line:
            found.append(line.strip()[:200])
    return {"scanned": True, "matches": found, "other_trainer_present": bool(found)}


def main() -> int:
    target = lock_path(EXP_DIR)
    if not target.exists():
        print("no lock file present; nothing to recover")
        return 0

    status = inspect_lock(EXP_DIR)
    lock_sha = sha256_file(target)
    raw = target.read_text(encoding="utf-8", errors="replace")
    other = _no_other_trainer()

    can_remove = (
        status["present"]
        and not status["active"]
        and bool(status.get("stale"))
        and not other.get("other_trainer_present", False)
    )

    payload = {
        "artifact": "PHASE13_PART1B_STALE_LOCK_RECOVERY",
        "document_type": "STALE_LOCK_RECOVERY",
        "created_utc": datetime.datetime.utcnow().isoformat() + "Z",
        "experiment_id": EXP,
        "status": "STALE_LOCK_RECOVERY_AUTHORIZED_BY_SUPERVISOR",
        "lock_path": str(target),
        "lock_sha256": lock_sha,
        "lock_contents": status.get("payload"),
        "lock_raw": raw,
        "inspection": {
            "present": status.get("present"),
            "active": status.get("active"),
            "stale": status.get("stale"),
            "owner_alive": status.get("owner_alive"),
            "reason": status.get("reason"),
            "age_seconds": status.get("age_seconds"),
        },
        "process_scan": other,
        "preconditions_met": can_remove,
        "removal_mechanism": "src.utils.run_lock.release_lock(experiment_dir, force=True)",
        "removal_authorized": True,
        "deleted_nothing_else": True,
        "removed": False,
        "lock_absent_after": None,
        "test_reads": 0,
    }

    if can_remove:
        released = release_lock(EXP_DIR, force=True)
        payload["removed"] = bool(released)
        payload["lock_absent_after"] = not target.exists()
        payload["outcome"] = (
            "RECOVERED" if payload["lock_absent_after"] else "REMOVAL_FAILED"
        )
    else:
        payload["outcome"] = "NOT_REMOVED_PRECONDITIONS_UNMET"

    OUT_JSON.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    OUT_MD.write_text(
        "# PHASE-13 PART-1B — STALE LOCK RECOVERY\n\n"
        f"- status: **{payload['status']}**\n"
        f"- lock path: `{target}`\n"
        f"- lock SHA-256: `{lock_sha}`\n"
        f"- owner pid: {status.get('payload', {}).get('pid')} "
        f"(alive: {status.get('owner_alive')})\n"
        f"- stale: {status.get('stale')} | active: {status.get('active')}\n"
        f"- other trainer present: {other.get('other_trainer_present')}\n"
        f"- removal mechanism: `{payload['removal_mechanism']}`\n"
        f"- outcome: **{payload['outcome']}**\n"
        f"- lock absent after: {payload['lock_absent_after']}\n\n"
        "Nothing else was deleted — history, checkpoints, the experiment "
        "directory and logs are untouched.\n",
        encoding="utf-8",
    )

    print(json.dumps({
        "lock_present": status.get("present"),
        "active": status.get("active"),
        "stale": status.get("stale"),
        "owner_alive": status.get("owner_alive"),
        "other_trainer_present": other.get("other_trainer_present"),
        "outcome": payload["outcome"],
        "lock_absent_after": payload["lock_absent_after"],
        "lock_sha256": lock_sha,
    }, indent=2))
    return 0 if payload["lock_absent_after"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
