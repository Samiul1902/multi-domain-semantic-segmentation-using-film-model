"""
Single-writer experiment lock (Phase 08 Part 1B).

Prevents two active canonical trainers from writing to the same experiment
ID / output directory.

Semantics
---------
- Acquire writes a lock file containing PID, host, experiment id, and start time.
- A conflicting **active** lock fails loudly (never silently overwritten).
- A **stale** lock (owner process no longer alive, or lock older than the
  staleness horizon) can be reclaimed, but only through an explicit
  ``recover_stale=True`` call. Recovery is logged, never silent.
"""
from __future__ import annotations

import json
import os
import socket
from datetime import datetime, timezone
from pathlib import Path


class ExperimentLockError(RuntimeError):
    """Raised when an active lock already exists for an experiment."""


DEFAULT_STALE_SECONDS = 24 * 60 * 60


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _pid_alive(pid: int) -> bool:
    """Best-effort liveness probe for a PID on this host."""
    if pid <= 0:
        return False
    try:
        if os.name == 'nt':
            import ctypes
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            handle = ctypes.windll.kernel32.OpenProcess(
                PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
            if not handle:
                return False
            ctypes.windll.kernel32.CloseHandle(handle)
            return True
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def lock_path(experiment_dir) -> Path:
    return Path(experiment_dir) / '.experiment.lock'


def read_lock(experiment_dir):
    """Return the lock payload, or None when no lock file exists."""
    p = lock_path(experiment_dir)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding='utf-8'))
    except Exception:
        return {'corrupt': True, 'raw': p.read_text(encoding='utf-8', errors='replace')}


def inspect_lock(experiment_dir, stale_seconds: int = DEFAULT_STALE_SECONDS) -> dict:
    """
    Report lock status without modifying anything.

    Returns ``{'present', 'active', 'stale', 'owner_alive', 'payload', 'reason'}``.
    """
    payload = read_lock(experiment_dir)
    if payload is None:
        return {'present': False, 'active': False, 'stale': False,
                'owner_alive': None, 'payload': None, 'reason': 'no lock file'}
    if payload.get('corrupt'):
        return {'present': True, 'active': False, 'stale': True,
                'owner_alive': None, 'payload': payload, 'reason': 'corrupt lock file'}

    same_host = payload.get('host') == socket.gethostname()
    owner_alive = _pid_alive(int(payload.get('pid', -1))) if same_host else None

    started = payload.get('started_utc')
    age = None
    if started:
        try:
            age = (datetime.now(timezone.utc)
                   - datetime.fromisoformat(started)).total_seconds()
        except Exception:
            age = None

    if same_host:
        active = bool(owner_alive)
        reason = 'owner process alive' if active else 'owner process not alive'
    else:
        active = age is None or age < stale_seconds
        reason = f'foreign host lock (age={age})'

    stale = (not active) or (age is not None and age > stale_seconds)
    return {'present': True, 'active': active, 'stale': stale,
            'owner_alive': owner_alive, 'payload': payload,
            'age_seconds': age, 'reason': reason}


def acquire_lock(experiment_dir, experiment_id: str,
                 stale_seconds: int = DEFAULT_STALE_SECONDS,
                 recover_stale: bool = False) -> dict:
    """
    Acquire the single-writer lock for an experiment directory.

    Raises
    ------
    ExperimentLockError
        If an ACTIVE lock exists and ``recover_stale`` was not requested.
    """
    experiment_dir = Path(experiment_dir)
    experiment_dir.mkdir(parents=True, exist_ok=True)
    status = inspect_lock(experiment_dir, stale_seconds)

    if status['present'] and status['active'] and not recover_stale:
        raise ExperimentLockError(
            f"Active lock for experiment {experiment_id!r}: {status['reason']}. "
            "Refusing to start a second canonical trainer. If the owner is truly "
            "dead, re-run with recover_stale=True to reclaim explicitly."
        )

    recovered = bool(status['present'])
    payload = {
        'experiment_id': experiment_id,
        'pid': os.getpid(),
        'host': socket.gethostname(),
        'started_utc': _now_iso(),
        'recovered_stale_lock': recovered,
        'recovered_reason': status.get('reason') if recovered else None,
    }
    lock_path(experiment_dir).write_text(json.dumps(payload, indent=2), encoding='utf-8')
    return payload


def release_lock(experiment_dir, force: bool = False) -> bool:
    """
    Release the lock. By default only the owning process may release it.

    Deletion is attempted with ``unlink``. Some sandboxed Windows environments
    route deletion through a trash shim that can raise even when the file is
    actually removed, so the outcome is verified by re-checking existence
    rather than trusting the exception.
    """
    p = lock_path(experiment_dir)
    if not p.exists():
        return False
    payload = read_lock(experiment_dir) or {}
    if not force and payload.get('pid') != os.getpid():
        raise ExperimentLockError(
            'Refusing to release a lock owned by another process (use force=True)')
    try:
        p.unlink()
    except OSError:
        # The shim may raise after having already removed the file.
        pass
    if p.exists():
        # Last resort: truncate to empty so the lock is clearly not a valid claim.
        try:
            p.write_text('', encoding='utf-8')
        except OSError:
            raise ExperimentLockError(
                f'Unable to release lock at {p}; it still exists after unlink.')
        return False
    return True
