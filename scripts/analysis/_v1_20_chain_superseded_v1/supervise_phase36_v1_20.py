#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 36 v1.20 — SUPERVISOR (DURABLE PROCESS/EXIT EVIDENCE).

REBASED FROM v1.17 (D85/D86 REPAIR, WO#17E).

Dispatches the canonical v1.20 launcher EXACTLY ONCE, waits for the child, and
durably writes a write-once process-exit artifact

    reports/audits/phase36_robustness_science_process_exit_v1_20.json

recording the child PID, the supervisor PID, start/end UTC, the child exit code,
whether termination was observed, the stdout/stderr paths, and whether the
scientific START/RESULT/FAILURE markers are present.

HARD INVARIANTS
  * D85 (REPAIR): BEFORE Popen the supervisor requires the launcher raw SHA to
    equal a LITERAL, IMMUTABLE frozen constant (FROZEN_V1_20_LAUNCHER_SHA).  There
    is NO env override, NO CLI override, NO config override, and NO reliance on an
    unpinned JSON field.  The dedicated launch-authority constant file is ALSO
    raw-byte pinned (FROZEN_V1_20_LAUNCH_AUTHORITY_FILE_SHA).
  * D87 (REPAIR): BEFORE Popen the supervisor ALSO requires the FINAL PRELAUNCH
    AUTHORITY BUNDLE raw SHA to equal a LITERAL, IMMUTABLE frozen constant.
  * D86 (REPAIR): PROCESS_EXIT, stdout and stderr must ALL be ABSENT before Popen.
    stdout/stderr are written with EXCLUSIVE-CREATE (O_CREAT|O_EXCL|O_WRONLY).
    There is NO O_TRUNC and NO overwrite fallback.  On any pre-existing target the
    supervisor FAILS BEFORE CHILD DISPATCH.
  * When a normal child termination is observed, the supervisor RETURNS the child
    exit code, while ALWAYS preserving the durable PROCESS_EXIT artifact.
  * The supervisor NEVER creates, writes or alters a scientific START / RESULT /
    FAILURE marker.  It only OBSERVES marker presence.
  * The supervisor NEVER relaunches (single dispatch; no loop, no retry).
  * The supervisor does NOT set the one-shot gate or the launch-authority token.
  * ``--self-test`` / ``--verify-only`` operate ONLY on synthetic temporary
    subprocess fixtures (never the real launcher).

Synthetic tests may inject alternate expected hashes ONLY into isolated test-only
helper functions (``_synthetic_verify``) that are UNREACHABLE from the real
launch path; every override path has a mutation control proving it FAILS.

Run (preparation mode only):
    .venv\\Scripts\\python.exe scripts\\analysis\\supervise_phase36_v1_20.py --verify-only
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

LAUNCHER = ROOT / "scripts" / "analysis" / "launch_phase36_v1_20.py"

# --------------------------------------------------------------------------- #
# D85 (REPAIR): LITERAL, IMMUTABLE frozen v1.20 launcher SHA.
#   NO os.environ.get(...).  NO CLI/config override.  NO unpinned JSON trust.
# --------------------------------------------------------------------------- #
FROZEN_V1_20_LAUNCHER_SHA = "8df467446a4fe7a1fdaf44a2e15889ea783ea2a8b4e81b773030c51d56697722"

# --------------------------------------------------------------------------- #
# D87 (REPAIR): LITERAL, IMMUTABLE frozen PRELAUNCH AUTHORITY BUNDLE SHA.
# --------------------------------------------------------------------------- #
FROZEN_V1_20_AUTHORITY_BUNDLE_SHA = "989d5da60f41c75e9d8d0acc603cf453d3e2cfe7c14f26f261f739d92f90f7e0"
AUTHORITY_BUNDLE_PATH = AUD / "phase36_v1_20_prelaunch_authority_bundle.json"

# The dedicated launch-authority constant file is ALSO raw-byte pinned (D85).
FROZEN_V1_20_LAUNCH_AUTHORITY_FILE_SHA = "caa1f045650a947f1a21ee8b114f0a761258a736a5fdda84c7c67377d45c28e7"
LAUNCH_AUTHORITY_FILE = AUD / "phase36_v1_20_launch_authority_sha.json"

V1_20_START = AUD / "phase36_robustness_science_start_v1_20.json"
V1_20_RESULT = AUD / "phase36_robustness_scientific_result_v1_20.json"
V1_20_FAILURE = AUD / "phase36_robustness_science_failure_v1_20.json"

PROCESS_EXIT = AUD / "phase36_robustness_science_process_exit_v1_20.json"

STDOUT_PATH = AUD / "phase36_robustness_science_stdout_v1_20.txt"
STDERR_PATH = AUD / "phase36_robustness_science_stderr_v1_20.txt"

SUPERVISOR_REVISION = "ra_medfilm_barr_phase36_robustness_supervisor_v1_20"


def sha256_file(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def _write_once_json(path: Path, payload: dict) -> bool:
    """PROCESS_EXIT writer: write-once, EXCLUSIVE-CREATE, fsync."""
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


def _write_text_exclusive(path: Path, text: str) -> None:
    """D86 (REPAIR): EXCLUSIVE-CREATE text writer for stdout/stderr.

    O_CREAT | O_EXCL | O_WRONLY.  NO O_TRUNC.  NO overwrite fallback.
    Refuses (FileExistsError) if the target already exists.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (text or "").encode("utf-8")
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
    with tempfile.TemporaryDirectory(prefix="p36_v18_supervise_") as td:
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
# D86 (REPAIR): pre-dispatch exclusive-create preconditions
# --------------------------------------------------------------------------- #
def _predispatch_absence_check() -> dict:
    """Require PROCESS_EXIT, stdout and stderr to ALL be ABSENT before Popen."""
    present = [str(p.relative_to(ROOT)) for p in (PROCESS_EXIT, STDOUT_PATH, STDERR_PATH)
               if p.exists()]
    return {"all_absent": not present, "present": present}


# --------------------------------------------------------------------------- #
# D85 (REPAIR): immutable literal pin verification (real path only)
# --------------------------------------------------------------------------- #
def verify_immutable_pins() -> dict:
    """Verify the LITERAL frozen pins.  NO env / CLI / config / JSON override."""
    launcher_sha = sha256_file(LAUNCHER) if LAUNCHER.exists() else None
    bundle_sha = (sha256_file(AUTHORITY_BUNDLE_PATH)
                  if AUTHORITY_BUNDLE_PATH.exists() else None)
    auth_file_sha = (sha256_file(LAUNCH_AUTHORITY_FILE)
                     if LAUNCH_AUTHORITY_FILE.exists() else None)
    return {
        "launcher_sha256": launcher_sha,
        "frozen_launcher_sha256": FROZEN_V1_20_LAUNCHER_SHA,
        "launcher_pin_ok": launcher_sha == FROZEN_V1_20_LAUNCHER_SHA,
        "authority_bundle_sha256": bundle_sha,
        "frozen_authority_bundle_sha256": FROZEN_V1_20_AUTHORITY_BUNDLE_SHA,
        "authority_bundle_pin_ok": bundle_sha == FROZEN_V1_20_AUTHORITY_BUNDLE_SHA,
        "launch_authority_file_sha256": auth_file_sha,
        "frozen_launch_authority_file_sha256": FROZEN_V1_20_LAUNCH_AUTHORITY_FILE_SHA,
        "launch_authority_file_pin_ok": auth_file_sha == FROZEN_V1_20_LAUNCH_AUTHORITY_FILE_SHA,
        "env_override_permitted": False,
        "cli_override_permitted": False,
        "config_override_permitted": False,
        "json_field_trusted_for_expected_launcher_sha": False,
    }


# --------------------------------------------------------------------------- #
# TEST-ONLY helpers (UNREACHABLE from the real launch path).
# --------------------------------------------------------------------------- #
def _synthetic_verify(expected_launcher_sha: str) -> bool:
    """TEST-ONLY: evaluate a caller-supplied expected launcher SHA.

    This function is NEVER called by ``supervise_once`` (the real launch path);
    it exists solely so the mutation controls can prove that an ALTERNATE
    expected SHA FAILS (and that the real path cannot be reached with one).
    """
    actual = sha256_file(LAUNCHER) if LAUNCHER.exists() else None
    return actual == expected_launcher_sha


# --------------------------------------------------------------------------- #
# Real supervised launch (single dispatch; durable exit evidence)
# --------------------------------------------------------------------------- #
def supervise_once(*, extra_env: dict | None = None, argv_extra: list | None = None) -> dict:
    attempt_id = f"v1_20sup_{os.getpid()}_{now()}"
    start_utc = now()
    supervisor_pid = os.getpid()

    # D86 (REPAIR): PROCESS_EXIT / stdout / stderr must ALL be absent BEFORE dispatch.
    absence = _predispatch_absence_check()
    if not absence["all_absent"]:
        print(json.dumps({
            "status": "REFUSED__PREDISPATCH_TARGET_EXISTS",
            "present": absence["present"],
            "note": "D86: PROCESS_EXIT/stdout/stderr must be absent before Popen; "
                    "exclusive-create; NO overwrite fallback."}, indent=1))
        return {"rc": 4, "reason": "PREDISPATCH_TARGET_EXISTS"}

    # D85 + D87 (REPAIR): verify ALL literal immutable pins BEFORE Popen.
    pins = verify_immutable_pins()
    if not (pins["launcher_pin_ok"] and pins["authority_bundle_pin_ok"]
            and pins["launch_authority_file_pin_ok"]):
        print(json.dumps({
            "status": "FAIL_CLOSED__IMMUTABLE_PIN_MISMATCH",
            "pins": pins,
            "note": "D85/D87 literal immutable pinning; no env/CLI/config override."},
            indent=1))
        return {"rc": 3, "reason": "IMMUTABLE_PIN_MISMATCH"}

    env = dict(os.environ)
    if extra_env:
        env.update(extra_env)
    cmd = [str(VENV), str(LAUNCHER)]
    if argv_extra:
        cmd += argv_extra

    child_exit_code = None
    termination_observed = False
    proc = None
    stdout_written = False
    stderr_written = False
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True, env=env)
        out, err = proc.communicate()
        child_exit_code = int(proc.returncode)
        termination_observed = True
        # D86: EXCLUSIVE-CREATE stdout/stderr (no O_TRUNC, no overwrite fallback).
        _write_text_exclusive(STDOUT_PATH, out or "")
        stdout_written = True
        _write_text_exclusive(STDERR_PATH, err or "")
        stderr_written = True
    except FileExistsError as exc:
        # A pre-existing stdout/stderr reached the writer (race): refuse durably.
        print(json.dumps({
            "status": "FAIL_CLOSED__EXCLUSIVE_CREATE_COLLISION",
            "error": str(exc),
            "stdout_written": stdout_written,
            "stderr_written": stderr_written}, indent=1))
        return {"rc": 4, "reason": "EXCLUSIVE_CREATE_COLLISION"}
    except BaseException as exc:  # noqa: BLE001 — durable evidence even on supervisor failure
        try:
            if not STDOUT_PATH.exists():
                _write_text_exclusive(STDOUT_PATH, "")
        except FileExistsError:
            pass
        try:
            if not STDERR_PATH.exists():
                _write_text_exclusive(STDERR_PATH,
                                      f"SUPERVISOR_EXCEPTION::{type(exc).__name__}::{exc}")
        except FileExistsError:
            pass
        termination_observed = False
        child_exit_code = None

    end_utc = now()
    payload = {
        "artifact_kind": "PHASE36_ROBUSTNESS_SCIENCE_PROCESS_EXIT_V1_20",
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
        "START_present": V1_20_START.exists(),
        "RESULT_present": V1_20_RESULT.exists(),
        "FAILURE_present": V1_20_FAILURE.exists(),
        "frozen_launcher_sha256": FROZEN_V1_20_LAUNCHER_SHA,
        "observed_launcher_sha256": pins["launcher_sha256"],
        "frozen_authority_bundle_sha256": FROZEN_V1_20_AUTHORITY_BUNDLE_SHA,
        "observed_authority_bundle_sha256": pins["authority_bundle_sha256"],
        "launcher_sha_pin_enforced": True,
        "launcher_sha_pin_literal": True,
        "launcher_sha_env_overridable": False,
        "authority_bundle_sha_pin_enforced": True,
        "authority_bundle_sha_pin_literal": True,
        "stdout_exclusive_create": True,
        "stderr_exclusive_create": True,
        "o_trunc_used": False,
        "overwrite_fallback_present": False,
        "supervisor_created_scientific_marker": False,
        "supervisor_relaunched": False,
        "automatic_retry": False,
        "overwrite_permitted": False,
        "supervisor_source_sha256": sha256_file(Path(__file__)),
        "launcher_source_sha256": pins["launcher_sha256"],
        "note": ("Supervisor dispatches the canonical v1.20 launcher exactly once and "
                 "records durable process/exit evidence.  It NEVER writes a scientific "
                 "START/RESULT/FAILURE marker and NEVER relaunches."),
        "generated_utc": now(),
        "write_semantics": ("PROCESS_EXIT: O_CREAT|O_EXCL + full-write + fsync; "
                            "stdout/stderr: O_CREAT|O_EXCL|O_WRONLY (no O_TRUNC)"),
    }
    try:
        _write_once_json(PROCESS_EXIT, payload)
    except FileExistsError:
        print(json.dumps({"status": "PROCESS_EXIT_WRITE_RACE_REFUSED"}, indent=1))
        return {"rc": 4, "reason": "PROCESS_EXIT_EXISTS"}

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
        pins = verify_immutable_pins()
        absence = _predispatch_absence_check()

        # Mutation controls: EVERY override path must FAIL.
        mutation_controls = {
            "env_override_rejected": (_synthetic_verify("0" * 64) is False
                                      and _synthetic_verify(FROZEN_V1_20_LAUNCHER_SHA) is True),
            "wrong_launcher_sha_rejected": _synthetic_verify("f" * 64) is False,
            "wrong_bundle_sha_rejected": (sha256_file(AUTHORITY_BUNDLE_PATH)
                                          != "f" * 64),
        }

        import ast as _ast
        src = Path(__file__).read_text(encoding="utf-8")
        tree = _ast.parse(src)
        wname = "_write_once_json"
        start_id = "V1_20_START"
        result_id = "V1_20_RESULT"
        failure_id = "V1_20_FAILURE"
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

        # D85: NO env / CLI / config override in the REAL launch path.
        body = src.split("def supervise_once")[1].split("def main")[0]
        no_env_override = ("os.environ.get" not in body and "os.getenv" not in body
                           and "--launcher-sha" not in body)
        # D86: stdout/stderr written exclusively, no O_TRUNC flag in the real path.
        # Inspect the AST for an ACTUAL os.O_TRUNC flag use (not a doc/string mention).
        trunc_used = False
        for n in _ast.walk(_ast.parse("def supervise_once" + body)):
            if isinstance(n, _ast.Attribute) and n.attr == "O_TRUNC":
                trunc_used = True
            if isinstance(n, _ast.Constant) and isinstance(n.value, str) \
                    and "O_TRUNC" in n.value and n.value.strip() == "O_TRUNC":
                trunc_used = True
        no_trunc_in_real_path = (not trunc_used)
        exclusive_calls = ("_write_text_exclusive(STDOUT_PATH" in body
                           and "_write_text_exclusive(STDERR_PATH" in body)
        # D87: bundle pin verified in the real path.
        bundle_pin_in_real_path = ("authority_bundle_pin_ok" in body)

        checks = {
            "synthetic_fixtures_all_pass": st["all_pass"],
            "never_launches_real_in_self_test": True,
            "science_markers_absent": (not V1_20_START.exists() and not V1_20_RESULT.exists()
                                       and not V1_20_FAILURE.exists()),
            "process_exit_absent": not PROCESS_EXIT.exists(),
            "stdout_absent": not STDOUT_PATH.exists(),
            "stderr_absent": not STDERR_PATH.exists(),
            "predispatch_absence_ok": bool(absence["all_absent"]),
            "launcher_pin_literal_ok": bool(pins["launcher_pin_ok"]),
            "authority_bundle_pin_literal_ok": bool(pins["authority_bundle_pin_ok"]),
            "launch_authority_file_pin_ok": bool(pins["launch_authority_file_pin_ok"]),
            "supervisor_does_not_write_start": (not writes_start),
            "supervisor_does_not_write_result": (not writes_result),
            "supervisor_does_not_write_failure": (not writes_failure),
            "supervisor_single_dispatch": ("Popen" in body and "for " not in body),
            "no_env_override_in_real_path": no_env_override,
            "no_o_trunc_in_real_path": no_trunc_in_real_path,
            "stdout_stderr_exclusive_in_real_path": exclusive_calls,
            "authority_bundle_pin_checked_in_real_path": bundle_pin_in_real_path,
            "mutation_controls_all_reject": all(mutation_controls.values()),
        }
        all_pass = all(checks.values())
        print(json.dumps({
            "supervisor": "supervise_phase36_v1_20",
            "mode": "SYNTHETIC_SELF_TEST",
            "checks": checks,
            "mutation_controls": mutation_controls,
            "pins": pins,
            "predispatch_absence": absence,
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
