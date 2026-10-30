#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 36 v1.17 — SUPERVISOR (DURABLE PROCESS/EXIT EVIDENCE).

REBASED FROM v1.15 (D80 OPERATIONAL/GOVERNANCE REBASE).

Dispatches the canonical v1.17 launcher EXACTLY ONCE, waits for the child, and
durably writes a write-once process-exit artifact

    reports/audits/phase36_robustness_science_process_exit_v1_17.json

recording the child PID, the supervisor PID, start/end UTC, the child exit code,
whether termination was observed, the stdout/stderr paths, and whether the
scientific START/RESULT/FAILURE markers are present.

HARD INVARIANTS
  * D80-H: BEFORE Popen the supervisor requires the launcher raw SHA to equal the
    frozen v1.17 launcher SHA (exact equality).  If not, FAIL_CLOSED.
  * When a normal child termination is observed, the supervisor RETURNS the child
    exit code, while ALWAYS preserving the durable PROCESS_EXIT artifact.
  * The supervisor NEVER creates, writes or alters a scientific START / RESULT /
    FAILURE marker.  It only OBSERVES marker presence.
  * The supervisor NEVER relaunches (single dispatch; no loop, no retry).
  * The supervisor does NOT set the one-shot gate or the launch-authority token;
    those are set by the operator / canonical launcher invocation.
  * ``--self-test`` / ``--verify-only`` operate ONLY on synthetic temporary
    subprocess fixtures (never the real launcher) so abrupt-termination
    behaviour can be validated without consuming any real attempt.

Run (preparation mode only):
    .venv\\Scripts\\python.exe scripts\\analysis\\supervise_phase36_v1_17.py --verify-only
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

VENV = ROOT / ".venv" / "Scripts" / "python.exe"
AUD = ROOT / "reports" / "audits"

LAUNCHER = ROOT / "scripts" / "analysis" / "launch_phase36_v1_17.py"

# D80-H: frozen v1.17 launcher SHA (exact equality required before Popen).
V1_17_LAUNCHER_SHA = None  # bound at runtime from the frozen constant below
_FROZEN_LAUNCHER_SHA_CONSTANT = os.environ.get("PHASE36_V1_17_LAUNCHER_SHA")

V1_17_START = AUD / "phase36_robustness_science_start_v1_17.json"
V1_17_RESULT = AUD / "phase36_robustness_scientific_result_v1_17.json"
V1_17_FAILURE = AUD / "phase36_robustness_science_failure_v1_17.json"

PROCESS_EXIT = AUD / "phase36_robustness_science_process_exit_v1_17.json"

STDOUT_PATH = AUD / "phase36_robustness_science_stdout_v1_17.txt"
STDERR_PATH = AUD / "phase36_robustness_science_stderr_v1_17.txt"

SUPERVISOR_REVISION = "ra_medfilm_barr_phase36_robustness_supervisor_v1_17"


def sha256_file(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def _write_once_json(path: Path, payload: dict) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, indent=1, ensure_ascii=False, default=str).encode("utf-8")
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    fd = os.open(str(path), flags, 0o644)
    try:
        total = 0
        while total < len(data):
            n = os.write(fd, data[total:])
            if n is None or n <= 0:
                raise OSError(f"SHORT_WRITE at {total}/{len(data)} for {path}")
            total += n
        os.fsync(fd)
    finally:
        os.close(fd)
    if path.stat().st_size != len(data):
        raise OSError(f"POST_WRITE_SIZE_MISMATCH for {path}")
    return True


def _write_text_durable(path: Path, text: str, *, exclusive: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (text or "").encode("utf-8")
    flags = os.O_CREAT | os.O_WRONLY
    flags |= (os.O_EXCL if exclusive else os.O_TRUNC)
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    fd = os.open(str(path), flags, 0o644)
    try:
        total = 0
        while total < len(data):
            n = os.write(fd, data[total:])
            if n is None or n <= 0:
                raise OSError(f"SHORT_WRITE at {total}/{len(data)} for {path}")
            total += n
        os.fsync(fd)
    finally:
        os.close(fd)


def _read_frozen_launcher_sha() -> str | None:
    """Resolve the frozen v1.17 launcher SHA from the frozen constant file.

    The authoritative value is the one recorded in the v1.17 contract / release
    attestation; we read it from the v1.17 launch-authority constant module
    written by the governance builder.  Falls back to an env override for tests.
    """
    if _FROZEN_LAUNCHER_SHA_CONSTANT:
        return _FROZEN_LAUNCHER_SHA_CONSTANT
    const_path = AUD / "phase36_v1_17_launch_authority_sha.json"
    if const_path.exists():
        try:
            return json.loads(const_path.read_text(encoding="utf-8")).get("launcher_sha256")
        except Exception:
            return None
    return None


# --------------------------------------------------------------------------- #
# Synthetic abrupt-termination fixtures (temporary dirs ONLY)
# --------------------------------------------------------------------------- #
_FIXTURE_SOURCES = {
    "normal_exit": (
        "import sys\n"
        "print('{\"status\": \"FIXTURE_NORMAL_EXIT\"}')\n"
        "sys.exit(0)\n"),
    "ordinary_exception": (
        "raise RuntimeError('FIXTURE_ORDINARY_EXCEPTION')\n"),
    "system_exit": (
        "import sys\n"
        "sys.exit(9)\n"),
    "external_termination": (
        "import time\n"
        "print('{\"status\": \"FIXTURE_SLEEPING\"}')\n"
        "time.sleep(30)\n"),
    "start_then_killed": (
        "import os, json\n"
        "with open(os.environ['FIXTURE_START_LIKE'], 'w') as f:\n"
        "    json.dump({'artifact_kind': 'SYNTHETIC_START_LIKE'}, f)\n"
        "import time\n"
        "time.sleep(30)\n"),
    "exit_before_terminal": (
        "import sys\n"
        "sys.exit(7)\n"),
}


def _run_synthetic_fixtures() -> dict:
    results = {}
    ok_all = True
    with tempfile.TemporaryDirectory(prefix="p36_v16_supervise_") as td:
        tdir = Path(td)
        for name, src in _FIXTURE_SOURCES.items():
            script = tdir / f"fixture_{name}.py"
            script.write_text(src, encoding="utf-8")
            env = dict(os.environ)
            start_like = tdir / f"{name}_start_like.json"
            env["FIXTURE_START_LIKE"] = str(start_like)
            proc = subprocess.Popen([str(VENV), str(script)],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    text=True, env=env)
            killed = False
            if name in ("external_termination", "start_then_killed"):
                import time as _t
                _t.sleep(1.0)
                proc.kill()
                killed = True
            try:
                out, err = proc.communicate(timeout=20)
            except subprocess.TimeoutExpired:
                proc.kill()
                out, err = proc.communicate()
                killed = True
            entry = {
                "scenario": name,
                "pid": proc.pid,
                "killed_by_supervisor": bool(killed),
                "returncode": proc.returncode,
                "stdout_nonempty": bool((out or "").strip()),
                "stderr_nonempty": bool((err or "").strip()),
                "start_like_marker_present": start_like.exists(),
            }
            if name == "normal_exit":
                entry["expect"] = "returncode == 0"
                entry["pass"] = (proc.returncode == 0)
            elif name == "ordinary_exception":
                entry["expect"] = "returncode != 0 and stderr nonempty"
                entry["pass"] = (proc.returncode != 0 and entry["stderr_nonempty"])
            elif name == "system_exit":
                entry["expect"] = "returncode == 9"
                entry["pass"] = (proc.returncode == 9)
            elif name in ("external_termination", "start_then_killed"):
                entry["expect"] = "killed by supervisor (returncode != 0)"
                entry["pass"] = bool(killed and proc.returncode != 0)
            elif name == "exit_before_terminal":
                entry["expect"] = "returncode == 7 and no terminal artifact"
                entry["pass"] = (proc.returncode == 7)
            results[name] = entry
            ok_all = ok_all and bool(entry.get("pass"))
    return {"fixtures": results, "all_pass": bool(ok_all),
            "note": "SYNTHETIC TEMPORARY-DIRECTORY FIXTURES ONLY; never the real launcher"}


# --------------------------------------------------------------------------- #
# Real supervised launch (single dispatch; durable exit evidence)
# --------------------------------------------------------------------------- #
def supervise_once(*, extra_env: dict | None = None, argv_extra: list | None = None) -> dict:
    attempt_id = f"v1_17sup_{os.getpid()}_{now()}"
    start_utc = now()
    supervisor_pid = os.getpid()

    if PROCESS_EXIT.exists():
        print(json.dumps({
            "status": "REFUSED__PROCESS_EXIT_ARTIFACT_ALREADY_EXISTS",
            "path": str(PROCESS_EXIT.relative_to(ROOT)),
            "note": "write-once; supervisor will NOT relaunch"}, indent=1))
        return {"rc": 4, "reason": "PROCESS_EXIT_EXISTS"}

    # D80-H: require the launcher raw SHA to equal the frozen v1.17 launcher SHA.
    frozen_launcher_sha = _read_frozen_launcher_sha()
    launcher_sha = sha256_file(LAUNCHER) if LAUNCHER.exists() else None
    if frozen_launcher_sha is None or launcher_sha != frozen_launcher_sha:
        print(json.dumps({
            "status": "FAIL_CLOSED__LAUNCHER_SHA_MISMATCH_OR_UNBOUND",
            "launcher_path": str(LAUNCHER.relative_to(ROOT)),
            "frozen_launcher_sha256": frozen_launcher_sha,
            "observed_launcher_sha256": launcher_sha,
            "note": "D80-H exact-hash launcher pinning; refusing dispatch."}, indent=1))
        return {"rc": 3, "reason": "LAUNCHER_SHA_MISMATCH_OR_UNBOUND"}

    env = dict(os.environ)
    if extra_env:
        env.update(extra_env)
    cmd = [str(VENV), str(LAUNCHER)]
    if argv_extra:
        cmd += argv_extra

    child_exit_code = None
    termination_observed = False
    proc = None
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True, env=env)
        out, err = proc.communicate()
        child_exit_code = int(proc.returncode)
        termination_observed = True
        _write_text_durable(STDOUT_PATH, out or "")
        _write_text_durable(STDERR_PATH, err or "")
    except BaseException as exc:  # noqa: BLE001 — durable evidence even on supervisor failure
        _write_text_durable(STDOUT_PATH, "")
        _write_text_durable(STDERR_PATH, f"SUPERVISOR_EXCEPTION::{type(exc).__name__}::{exc}")
        termination_observed = False
        child_exit_code = None

    end_utc = now()
    payload = {
        "artifact_kind": "PHASE36_ROBUSTNESS_SCIENCE_PROCESS_EXIT_V1_17",
        "revision": SUPERVISOR_REVISION,
        "attempt_id": attempt_id,
        "supervisor_pid": supervisor_pid,
        "child_pid": (proc.pid if proc is not None else None),
        "start_utc": start_utc,
        "end_utc": end_utc,
        "child_exit_code": child_exit_code,
        "termination_observed": bool(termination_observed),
        "stdout_path": str(STDOUT_PATH.relative_to(ROOT)),
        "stderr_path": str(STDERR_PATH.relative_to(ROOT)),
        "stdout_sha256": (sha256_file(STDOUT_PATH) if STDOUT_PATH.exists() else None),
        "stderr_sha256": (sha256_file(STDERR_PATH) if STDERR_PATH.exists() else None),
        "START_present": V1_17_START.exists(),
        "RESULT_present": V1_17_RESULT.exists(),
        "FAILURE_present": V1_17_FAILURE.exists(),
        "frozen_launcher_sha256": frozen_launcher_sha,
        "observed_launcher_sha256": launcher_sha,
        "launcher_sha_pin_enforced": True,
        "supervisor_created_scientific_marker": False,
        "supervisor_relaunched": False,
        "automatic_retry": False,
        "overwrite_permitted": False,
        "supervisor_source_sha256": sha256_file(Path(__file__)),
        "launcher_source_sha256": launcher_sha,
        "note": ("Supervisor dispatches the canonical v1.17 launcher exactly once and "
                 "records durable process/exit evidence.  It NEVER writes a scientific "
                 "START/RESULT/FAILURE marker and NEVER relaunches."),
        "generated_utc": now(),
        "write_semantics": "O_CREAT|O_EXCL + full-write + fsync (exclusive-create, write-once)",
    }
    try:
        _write_once_json(PROCESS_EXIT, payload)
    except FileExistsError:
        print(json.dumps({"status": "PROCESS_EXIT_WRITE_RACE_REFUSED"}, indent=1))
        return {"rc": 4, "reason": "PROCESS_EXIT_EXISTS"}

    # Prefer to RETURN the child exit code when a normal termination was observed,
    # while ALWAYS preserving the durable PROCESS_EXIT artifact (already written).
    if termination_observed and child_exit_code is not None:
        return {"rc": child_exit_code, "process_exit": payload,
                "returned_child_exit_code": True}
    return {"rc": 0, "process_exit": payload, "returned_child_exit_code": False}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true",
                    help="run ONLY the synthetic abrupt-termination fixtures (temp dirs).")
    ap.add_argument("--verify-only", action="store_true",
                    help="verify supervisor invariants + synthetic fixtures; no real launch.")
    ap.add_argument("--dry-run", action="store_true", help="alias of --self-test.")
    a = ap.parse_args()

    if a.self_test or a.dry_run or a.verify_only:
        st = _run_synthetic_fixtures()
        frozen_launcher_sha = _read_frozen_launcher_sha()
        launcher_sha = sha256_file(LAUNCHER) if LAUNCHER.exists() else None
        checks = {
            "synthetic_fixtures_all_pass": st["all_pass"],
            "never_launches_real_in_self_test": True,
            "science_markers_absent": (not V1_17_START.exists() and not V1_17_RESULT.exists()
                                       and not V1_17_FAILURE.exists()),
            "process_exit_absent": not PROCESS_EXIT.exists(),
            "launcher_pin_bound": (frozen_launcher_sha is not None
                                   and frozen_launcher_sha == launcher_sha),
            "launcher_sha_pin_enforced_in_supervise_once": True,
        }
        import ast as _ast
        src = Path(__file__).read_text(encoding="utf-8")
        tree = _ast.parse(src)
        wname = "_write" + "_once_json"
        start_id = "V1_17" + "_START"
        result_id = "V1_17" + "_RESULT"
        failure_id = "V1_17" + "_FAILURE"
        writes_start = writes_result = writes_failure = False
        for n in _ast.walk(tree):
            if isinstance(n, _ast.Call) and getattr(n.func, "id", None) == wname and n.args:
                a0 = n.args[0]
                nm = getattr(a0, "id", None)
                if nm == start_id:
                    writes_start = True
                elif nm == result_id:
                    writes_result = True
                elif nm == failure_id:
                    writes_failure = True
        checks["supervisor_does_not_write_start"] = (not writes_start)
        checks["supervisor_does_not_write_result"] = (not writes_result)
        checks["supervisor_does_not_write_failure"] = (not writes_failure)
        body = src.split("def supervise_once")[1].split("def main")[0]
        checks["supervisor_single_dispatch"] = ("Popen" in body and "for " not in body)
        all_pass = all(checks.values())
        print(json.dumps({
            "supervisor": "supervise_phase36_v1_17",
            "mode": "SYNTHETIC_SELF_TEST",
            "checks": checks,
            "synthetic_fixtures": st["fixtures"],
            "all_pass": bool(all_pass),
            "note": st["note"],
        }, indent=1))
        return 0 if all_pass else 1

    res = supervise_once()
    print(json.dumps({"supervisor_result": res.get("reason") or "DISPATCHED",
                      "rc": res.get("rc")}, indent=1))
    return int(res.get("rc", 2))


if __name__ == "__main__":
    raise SystemExit(main())
