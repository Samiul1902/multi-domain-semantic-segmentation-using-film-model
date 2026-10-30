#!/usr/bin/env python
"""WO#21 §3/§5/§7/§8 — BUILD the v1.21 LAUNCHER + SUPERVISOR + MANIFEST + BUNDLE.

MODE: NEW-REVISION PREPARATION ONLY.  NON-CONSUMING.

Creates NEW artifacts (v1.20 versions UNTOUCHED):

    scripts/analysis/launch_phase36_v1_21.py
    scripts/analysis/supervise_phase36_v1_21.py
    reports/audits/phase36_v1_21_runtime_source_integrity_manifest.json
    reports/audits/phase36_v1_21_launch_authority_sha.json
    reports/audits/phase36_v1_21_prelaunch_authority_bundle.json

LAUNCHER: STRICT mechanical rebase of the frozen v1.20 launcher plus:
    * V1_20_SOURCE_SHA -> new v1.21 exec SHA
    * §10 CONSUMED-HISTORY GATE replaced (v1.20 is now CONSUMED)

SUPERVISOR: mechanical rebase of the frozen v1.20 supervisor plus the D95
INTERRUPTION-SAFETY REPAIR:
    * KeyboardInterrupt (and ANY supervisor BaseException) can NEVER return rc 0
    * an unobserved child termination deterministically terminates/waits for the
      launcher child process TREE and records the cleanup evidence
    * PROCESS_EXIT distinguishes NORMAL_CHILD_COMPLETION /
      SUPERVISOR_INTERRUPTION / SUPERVISOR_INTERNAL_EXCEPTION
    * single dispatch; no retry; no relaunch; never writes a science marker

PIN RESOLUTION
--------------
All pins are fixed-width 64-hex literals; substituting one for another never
changes a file's BYTE LENGTH, so the builder converges in a few passes.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
AUD = ROOT / "reports" / "audits"

L_V120 = ROOT / "scripts" / "analysis" / "launch_phase36_v1_20.py"
S_V120 = ROOT / "scripts" / "analysis" / "supervise_phase36_v1_20.py"
E_V121 = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_21.py"

L_V121 = ROOT / "scripts" / "analysis" / "launch_phase36_v1_21.py"
S_V121 = ROOT / "scripts" / "analysis" / "supervise_phase36_v1_21.py"

MANIFEST_V121 = AUD / "phase36_v1_21_runtime_source_integrity_manifest.json"
LAUNCH_AUTH_V121 = AUD / "phase36_v1_21_launch_authority_sha.json"
BUNDLE_V121 = AUD / "phase36_v1_21_prelaunch_authority_bundle.json"

FROZEN_L_V120 = "8df467446a4fe7a1fdaf44a2e15889ea783ea2a8b4e81b773030c51d56697722"
FROZEN_S_V120 = "ce06475ea7030bd97b96f7fb1f61fdd5cb7f99254e821270f0a4dcbf32e9db46"
FROZEN_E_V121 = "312886c68f056375adc3f091766777da9e1caa47c1d422673de67751e8df7b97"

# v1.20 chain SHAs (literal lines being replaced in the rebased supervisor).
V120_BUNDLE_SHA = "989d5da60f41c75e9d8d0acc603cf453d3e2cfe7c14f26f261f739d92f90f7e0"
V120_AUTHFILE_SHA = "9122122a6f22e450b5d708bbea87ffd91b19a84d933b0f99a4264b8042583960"

# v1.21 governance authorities bound by the launch-authority file.
# These MUST already exist (built BEFORE the chain, so the DAG stays acyclic):
#   * v1.21 science release attestation (binds the v1.21 exec SHA)
#   * v1.21 D85/D86/D87/D88(+D92/D93A/D95) governance adjudication (carry-forward)
P_V1_21_ATTESTATION = AUD / "phase36_v1_21_science_release_attestation.json"
P_V1_21_ADJUDICATION = AUD / "phase36_v1_21_adjudication_d85_d86_d87_d88.json"

V1_20_INTERRUPTION_ADJUDICATION_SHA = (
    "31c29955380c6ec75d18f747dec4f91332177ddabeccef40cb0cafa8b37f5b72")
D85_D88_D92_ADJUDICATION_SHA = "8ec45fe9dc3a9c5f20f284f206cf464f79115ff246b4805aab56c8b2c6141e42"

ZERO64 = "0" * 64


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha_file(p: Path) -> str:
    return sha(Path(p).read_bytes())


def write_once(path: Path, data: bytes) -> str:
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    fd = os.open(str(path), flags, 0o644)
    try:
        w = 0
        while w < len(data):
            w += os.write(fd, data[w:])
        os.fsync(fd)
    finally:
        os.close(fd)
    if path.stat().st_size != len(data):
        raise OSError(f"POST_WRITE_SIZE_MISMATCH: {path}")
    return sha(data)


def rebase(s: str) -> str:
    s = s.replace("v1.20", "v1.21")
    s = s.replace("V1.20", "V1.21")
    s = s.replace("v1_20", "v1_21")
    s = s.replace("V1_20", "V1_21")
    return s


# sanity: frozen inputs unchanged
assert sha_file(L_V120) == FROZEN_L_V120, "frozen v1.20 launcher SHA drift"
assert sha_file(S_V120) == FROZEN_S_V120, "frozen v1.20 supervisor SHA drift"
assert sha_file(E_V121) == FROZEN_E_V121, "v1.21 exec SHA drift"


# =========================================================================== #
# §10 (v1.21) — CONSUMED-HISTORY GATE (v1.20 IS CONSUMED)                      #
# =========================================================================== #
CONSUMED_GATE_CODE = '''

# =========================================================================== #
# §10 (v1.21) — CONSUMED-HISTORY GATE (v1.20 IS CONSUMED)                      #
# =========================================================================== #
# v1.20 is CONSUMED (CONSUMED_INTERRUPTED_POST_START_PRE_SCIENTIFIC_RESULT; D95).
# v1.21 must NOT be mistaken for a clean-revision re-run of v1.20.  Before ANY
# real dispatch, the launcher REQUIRES that the v1.20 consumed history is EXACTLY
# the known recorded state: the v1.20 interruption adjudication exists with the
# expected SHA and classification, the v1.20 START marker is PRESENT, the v1.20
# RESULT and FAILURE markers are ABSENT, and the v1.20 PROCESS_EXIT evidence is
# PRESENT.  Any deviation -> FAIL CLOSED.
V1_20_CONSUMED_ADJUDICATION = (
    AUD / "phase36_v1_20_interruption_adjudication_v1_0.json")
V1_20_CONSUMED_ADJUDICATION_SHA = (
    "31c29955380c6ec75d18f747dec4f91332177ddabeccef40cb0cafa8b37f5b72")
V1_20_CONSUMED_EXPECTED_CLASSIFICATION = (
    "CONSUMED_INTERRUPTED_POST_START_PRE_SCIENTIFIC_RESULT")
V1_20_CONSUMED_START_MARKER = (
    AUD / "phase36_robustness_science_start_v1_20.json")
V1_20_CONSUMED_RESULT_MARKER = (
    AUD / "phase36_robustness_scientific_result_v1_20.json")
V1_20_CONSUMED_FAILURE_MARKER = (
    AUD / "phase36_robustness_science_failure_v1_20.json")
V1_20_CONSUMED_PROCESS_EXIT = (
    AUD / "phase36_robustness_science_process_exit_v1_20.json")


def verify_v1_20_consumed_history() -> dict:
    """§10: prove v1.20 is the EXACT known consumed-interruption state. FAIL CLOSED."""
    result = {"ok": False, "reasons": []}
    if not V1_20_CONSUMED_ADJUDICATION.exists():
        result["reasons"].append("v1_20_adjudication_absent")
        return result
    adj_sha = sha256_file(V1_20_CONSUMED_ADJUDICATION)
    if adj_sha != V1_20_CONSUMED_ADJUDICATION_SHA:
        result["reasons"].append("v1_20_adjudication_sha_mismatch")
    try:
        doc = json.loads(V1_20_CONSUMED_ADJUDICATION.read_text(encoding="utf-8"))
    except Exception:  # pragma: no cover
        result["reasons"].append("v1_20_adjudication_unreadable")
        return result
    if doc.get("classification") != V1_20_CONSUMED_EXPECTED_CLASSIFICATION:
        result["reasons"].append("v1_20_adjudication_classification_mismatch")
    if not V1_20_CONSUMED_START_MARKER.exists():
        result["reasons"].append("v1_20_start_marker_absent__expected_present")
    if V1_20_CONSUMED_RESULT_MARKER.exists():
        result["reasons"].append("v1_20_result_present__expected_absent")
    if V1_20_CONSUMED_FAILURE_MARKER.exists():
        result["reasons"].append("v1_20_failure_present__expected_absent")
    if not V1_20_CONSUMED_PROCESS_EXIT.exists():
        result["reasons"].append("v1_20_process_exit_absent__expected_present")
    result["ok"] = not result["reasons"]
    result["v1_20_adjudication_sha256"] = adj_sha
    result["terminal"] = ("PHASE36_V1_21_CONSUMED_HISTORY_GATE_PASS" if result["ok"]
                          else "PHASE36_V1_21_CONSUMED_HISTORY_GATE_FAIL_CLOSED")
    return result
'''


_IF_MAIN_MARKER = '\nif __name__ == "__main__":\n    sys.exit(main(sys.argv[1:]))\n'


def launcher_text() -> str:
    t = rebase(L_V120.read_text(encoding="utf-8"))
    old_src = 'V1_21_SOURCE_SHA = "b9d128240596c5c6b7c040480823f4cc653d26a4bc665fc69b396d00e4fe0ad8"'
    assert old_src in t, "v1.21 SOURCE_SHA anchor missing"
    t = t.replace(old_src, f'V1_21_SOURCE_SHA = "{FROZEN_E_V121}"')

    marker = "# §10 (v1.21) — CONSUMED-HISTORY GATE"
    assert marker in t, "§10 definition header not found post-rebase"
    old_def_start = t.index(
        "\n# =========================================================================== #\n"
        "# §10 (v1.21) — CONSUMED-HISTORY GATE")
    old_def_end = t.index(_IF_MAIN_MARKER, old_def_start)
    t = t[:old_def_start] + CONSUMED_GATE_CODE + t[old_def_end:]
    return t


# --------------------------------------------------------------------------- #
# D95 (REPAIR) — supervisor interruption-safety block.                          #
# --------------------------------------------------------------------------- #
_SUP_POPEN_SEAM = '''

# --------------------------------------------------------------------------- #
# D95 (REPAIR) — test-only subprocess injection seam.
#
# In the REAL launch path this is ALWAYS the real ``subprocess.Popen``.  It is
# rebound ONLY by isolated tests (never from env / CLI / config), so a synthetic
# KeyboardInterrupt can be injected into the EXACT real code path.
# --------------------------------------------------------------------------- #
_POPEN = subprocess.Popen
'''


_SUP_HELPERS_AND_SUPERVISE = '''# --------------------------------------------------------------------------- #
# D95 (REPAIR) — interruption-safe return-code decision.
#
# The supervisor MUST NEVER return 0 when the child termination was NOT observed.
# An unobserved child state is NEVER success.
# --------------------------------------------------------------------------- #
def _decide_return_code(*, termination_observed: bool, child_exit_code) -> int:
    """D95: a NON-ZERO rc whenever the child termination was NOT observed.

    * observed + concrete code -> that code (0 only if the child itself exited 0)
    * NOT observed (interrupt / supervisor internal exception / no child) -> 2
    """
    if termination_observed and child_exit_code is not None:
        return int(child_exit_code)
    return 2


def _force_kill_process_tree(proc) -> None:
    """D95: best-effort deterministic kill of the child process TREE (never raises)."""
    if proc is None:
        return
    pid = getattr(proc, "pid", None)
    try:
        if os.name == "nt" and pid is not None:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           check=False)
        else:
            import signal as _signal
            _sig = getattr(_signal, "SIGKILL", _signal.SIGTERM)
            try:
                os.killpg(os.getpgid(pid), _sig)
            except Exception:
                proc.kill()
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


def _terminate_child_tree(proc) -> dict:
    """D95: deterministically terminate + WAIT for the launcher child/process tree.

    Returns durable cleanup evidence.  Never raises.
    """
    out = {
        "cleanup_attempted": False,
        "terminate_signalled": False,
        "tree_kill_attempted": False,
        "cleanup_termination_observed": False,
        "cleanup_exit_code": None,
        "cleanup_error": None,
    }
    if proc is None:
        return out
    out["cleanup_attempted"] = True
    # 1) graceful terminate + bounded wait
    try:
        proc.terminate()
        out["terminate_signalled"] = True
    except Exception as exc:  # noqa: BLE001
        out["cleanup_error"] = f"terminate:{type(exc).__name__}"
    try:
        proc.wait(timeout=5)
        out["cleanup_termination_observed"] = True
        out["cleanup_exit_code"] = getattr(proc, "returncode", None)
    except Exception as exc:  # noqa: BLE001
        out["cleanup_error"] = (out["cleanup_error"] or "") + f"|wait:{type(exc).__name__}"
    # 2) forced tree kill + bounded wait
    if not out["cleanup_termination_observed"]:
        out["tree_kill_attempted"] = True
        _force_kill_process_tree(proc)
        try:
            proc.wait(timeout=5)
            out["cleanup_termination_observed"] = True
            out["cleanup_exit_code"] = getattr(proc, "returncode", None)
        except Exception as exc:  # noqa: BLE001
            out["cleanup_error"] = (out["cleanup_error"] or "") + f"|wait2:{type(exc).__name__}"
    return out


def _rel(p) -> str:
    """Path relative to ROOT when possible (preserves the v1.20 PROCESS_EXIT format)."""
    try:
        return str(Path(p).relative_to(ROOT))
    except Exception:
        return str(p)


# --------------------------------------------------------------------------- #
# Real supervised launch (single dispatch; durable exit evidence)
# --------------------------------------------------------------------------- #
def supervise_once(*, extra_env: dict | None = None, argv_extra: list | None = None) -> dict:
    attempt_id = f"v1_21sup_{os.getpid()}_{now()}"
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
    # D95 (REPAIR): interruption bookkeeping.
    termination_kind = "NOT_DISPATCHED"
    supervisor_exception_type = None
    supervisor_exception_message = None
    cleanup = {
        "cleanup_attempted": False, "terminate_signalled": False,
        "tree_kill_attempted": False, "cleanup_termination_observed": False,
        "cleanup_exit_code": None, "cleanup_error": None,
    }
    try:
        proc = _POPEN(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                      text=True, env=env)
        out, err = proc.communicate()
        child_exit_code = int(proc.returncode)
        termination_observed = True
        termination_kind = "NORMAL_CHILD_COMPLETION"
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
    except KeyboardInterrupt as exc:
        # D95 (REPAIR): SUPERVISOR INTERRUPTION.  The child termination was NOT
        # observed; deterministically terminate-and-wait the child tree and NEVER
        # return 0.
        termination_kind = "SUPERVISOR_INTERRUPTION"
        supervisor_exception_type = "KeyboardInterrupt"
        supervisor_exception_message = str(exc)
        termination_observed = False
        child_exit_code = None
        cleanup = _terminate_child_tree(proc)
    except BaseException as exc:  # noqa: BLE001 — durable evidence even on supervisor failure
        # D95 (REPAIR): SUPERVISOR INTERNAL EXCEPTION.  Same guarantees.
        termination_kind = "SUPERVISOR_INTERNAL_EXCEPTION"
        supervisor_exception_type = type(exc).__name__
        supervisor_exception_message = str(exc)
        termination_observed = False
        child_exit_code = None
        cleanup = _terminate_child_tree(proc)

    if not termination_observed:
        # Durable exception evidence (exclusive-create; never overwrite).
        try:
            if not STDOUT_PATH.exists():
                _write_text_exclusive(STDOUT_PATH, "")
        except FileExistsError:
            pass
        try:
            if not STDERR_PATH.exists():
                _write_text_exclusive(
                    STDERR_PATH,
                    f"SUPERVISOR_EXCEPTION::{supervisor_exception_type}::"
                    f"{supervisor_exception_message}")
        except FileExistsError:
            pass

    supervisor_rc = _decide_return_code(termination_observed=termination_observed,
                                        child_exit_code=child_exit_code)
    end_utc = now()
    payload = {
        "artifact_kind": "PHASE36_ROBUSTNESS_SCIENCE_PROCESS_EXIT_V1_21",
        "revision": SUPERVISOR_REVISION,
        "attempt_id": attempt_id,
        "supervisor_pid": supervisor_pid,
        "child_pid": (proc.pid if proc is not None else None),
        "start_utc": start_utc,
        "end_utc": end_utc,
        "child_exit_code": child_exit_code,
        "termination_observed": bool(termination_observed),
        "termination_kind": termination_kind,
        "supervisor_exception_type": supervisor_exception_type,
        "supervisor_exception_message": supervisor_exception_message,
        "cleanup_attempted": bool(cleanup["cleanup_attempted"]),
        "cleanup_terminate_signalled": bool(cleanup["terminate_signalled"]),
        "cleanup_tree_kill_attempted": bool(cleanup["tree_kill_attempted"]),
        "cleanup_termination_observed": bool(cleanup["cleanup_termination_observed"]),
        "cleanup_exit_code": cleanup["cleanup_exit_code"],
        "cleanup_error": cleanup["cleanup_error"],
        "supervisor_return_rc": supervisor_rc,
        "rc_zero_permitted": bool(termination_observed and child_exit_code == 0),
        "unobserved_state_masked_as_success": False,
        "stdout_path": _rel(STDOUT_PATH),
        "stderr_path": _rel(STDERR_PATH),
        "stdout_sha256": (sha256_file(STDOUT_PATH) if STDOUT_PATH.exists() else None),
        "stderr_sha256": (sha256_file(STDERR_PATH) if STDERR_PATH.exists() else None),
        "START_present": V1_21_START.exists(),
        "RESULT_present": V1_21_RESULT.exists(),
        "FAILURE_present": V1_21_FAILURE.exists(),
        "frozen_launcher_sha256": FROZEN_V1_21_LAUNCHER_SHA,
        "observed_launcher_sha256": pins["launcher_sha256"],
        "frozen_authority_bundle_sha256": FROZEN_V1_21_AUTHORITY_BUNDLE_SHA,
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
        "note": ("Supervisor dispatches the canonical v1.21 launcher exactly once and "
                 "records durable process/exit evidence.  It NEVER writes a scientific "
                 "START/RESULT/FAILURE marker and NEVER relaunches.  D95: an UNOBSERVED "
                 "child termination (KeyboardInterrupt / internal exception) NEVER "
                 "returns 0."),
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
    # D95 (REPAIR): NEVER mask an unobserved child state as success.
    return {"rc": supervisor_rc, "process_exit": payload,
            "returned_child_exit_code": False,
            "reason": "UNOBSERVED_CHILD_TERMINATION",
            "termination_kind": termination_kind}
'''


_OLD_SELF_TEST_LINE = '            "supervisor_single_dispatch": ("Popen" in body and "for " not in body),'

_NEW_SELF_TEST_LINES = '''            "supervisor_single_dispatch": (("Popen" in body or "_POPEN" in body)
                                           and "for " not in body),
            "no_retry_loop_in_real_path": (not any(
                isinstance(n, (_ast.For, _ast.While, _ast.AsyncFor))
                for n in _ast.walk(_ast.parse("def supervise_once" + body)))),
            "decide_rc_never_zero_on_unobserved": (
                _decide_return_code(termination_observed=False, child_exit_code=None) != 0
                and _decide_return_code(termination_observed=False, child_exit_code=0) != 0),
            "decide_rc_observed_zero_is_zero": (
                _decide_return_code(termination_observed=True, child_exit_code=0) == 0),
            "decide_rc_observed_nonzero_preserved": (
                _decide_return_code(termination_observed=True, child_exit_code=7) == 7),
            "keyboard_interrupt_handler_present": "except KeyboardInterrupt" in body,
            "internal_exception_handler_present": "except BaseException" in body,
            "cleanup_helper_present": "_terminate_child_tree(" in body,
            "termination_kind_recorded": "termination_kind" in body,
            "process_exit_distinguishes_kinds": (
                "NORMAL_CHILD_COMPLETION" in body
                and "SUPERVISOR_INTERRUPTION" in body
                and "SUPERVISOR_INTERNAL_EXCEPTION" in body),
            "no_rc_zero_fallthrough": ('return {"rc": 0, "process_exit"' not in body),'''


def supervisor_text(bundle_sha: str, authfile_sha: str, launcher_sha: str) -> str:
    s = rebase(S_V120.read_text(encoding="utf-8"))

    # pins
    assert f'FROZEN_V1_21_LAUNCHER_SHA = "{FROZEN_L_V120}"' in s, "sup launcher pin anchor"
    assert f'FROZEN_V1_21_AUTHORITY_BUNDLE_SHA = "{V120_BUNDLE_SHA}"' in s, "sup bundle pin anchor"
    assert f'FROZEN_V1_21_LAUNCH_AUTHORITY_FILE_SHA = "{V120_AUTHFILE_SHA}"' in s, "sup authfile pin anchor"
    s = s.replace(f'FROZEN_V1_21_LAUNCHER_SHA = "{FROZEN_L_V120}"',
                  f'FROZEN_V1_21_LAUNCHER_SHA = "{launcher_sha}"')
    s = s.replace(f'FROZEN_V1_21_AUTHORITY_BUNDLE_SHA = "{V120_BUNDLE_SHA}"',
                  f'FROZEN_V1_21_AUTHORITY_BUNDLE_SHA = "{bundle_sha}"')
    s = s.replace(f'FROZEN_V1_21_LAUNCH_AUTHORITY_FILE_SHA = "{V120_AUTHFILE_SHA}"',
                  f'FROZEN_V1_21_LAUNCH_AUTHORITY_FILE_SHA = "{authfile_sha}"')

    # import signal (for the process-tree kill)
    assert "import os\nimport subprocess\n" in s, "supervisor import anchor"
    s = s.replace("import os\nimport subprocess\n", "import os\nimport signal\nimport subprocess\n", 1)

    # _POPEN seam
    rev_anchor = f'SUPERVISOR_REVISION = "ra_medfilm_barr_phase36_robustness_supervisor_v1_21"\n'
    assert rev_anchor in s, "SUPERVISOR_REVISION anchor"
    s = s.replace(rev_anchor, rev_anchor + _SUP_POPEN_SEAM, 1)

    # replace supervise_once (helpers + repaired function)
    start_anchor = (
        "# --------------------------------------------------------------------------- #\n"
        "# Real supervised launch (single dispatch; durable exit evidence)\n"
        "# --------------------------------------------------------------------------- #\n")
    assert start_anchor in s, "supervise_once header anchor"
    a0 = s.index(start_anchor)
    a1 = s.index("\ndef main() -> int:", a0)
    s = s[:a0] + _SUP_HELPERS_AND_SUPERVISE + s[a1:]

    # extend the self-test check set
    assert _OLD_SELF_TEST_LINE in s, "self-test single-dispatch anchor"
    s = s.replace(_OLD_SELF_TEST_LINE, _NEW_SELF_TEST_LINES, 1)

    return s


# --------------------------------------------------------------------------- #
# FIXED-POINT PIN RESOLUTION                                                    #
# --------------------------------------------------------------------------- #
# Prerequisite governance artifacts MUST exist BEFORE the chain (acyclic DAG).
for _p in (P_V1_21_ATTESTATION, P_V1_21_ADJUDICATION):
    if not _p.exists():
        print(f"FAIL_CLOSED: prerequisite governance artifact missing: {_p.name} "
              "(build it BEFORE the chain)", file=sys.stderr)
        sys.exit(3)
V1_21_ATTESTATION_SHA = sha_file(P_V1_21_ATTESTATION)
V1_21_ADJUDICATION_SHA = sha_file(P_V1_21_ADJUDICATION)

launcher_sha = ZERO64
bundle_sha = ZERO64
authfile_sha = ZERO64

for _ in range(12):
    l_txt = launcher_text()
    l_bytes = l_txt.encode("utf-8")
    new_launcher_sha = sha(l_bytes)

    bundle_doc = {
        "artifact": "phase36_v1_21_prelaunch_authority_bundle",
        "phase": 36,
        "revision": "ra_medfilm_barr_phase36_robustness_v1_21",
        "type": "FINAL_PRELAUNCH_AUTHORITY_BUNDLE",
        "mode": "STATIC_NON_CONSUMING_GOVERNANCE_ONLY",
        "generated_utc": "2026-10-11T00:00:00Z",
        "authority_order": "ACYCLIC (A->B->C->D->E)",
        "supersedes_revision": "v1.20",
        "supervisor_sha256_present": False,
        "count_semantics": {
            "table_figure_target_count": 16,
            "total_reachable_write_target_count": 23,
            "unclassified_write_target_count": 0,
            "namespace_overlap_count": 0,
        },
        "v1_20_consumed_state": {
            "classification": "CONSUMED_INTERRUPTED_POST_START_PRE_SCIENTIFIC_RESULT",
            "defect": "D95",
            "attempt_consumed": True,
            "retry_permitted": False,
        },
        "binds": {
            "v1_21_execution_source": {
                "path": "scripts/analysis/phase36_robustness_execution_v1_21.py",
                "sha256": FROZEN_E_V121,
            },
            "v1_21_launcher": {
                "path": "scripts/analysis/launch_phase36_v1_21.py",
                "sha256": new_launcher_sha,
                "role": "PINNED_BY_DEDICATED_LAUNCH_AUTHORITY_FILE",
            },
            "v1_21_runtime_manifest": {
                "path": "reports/audits/phase36_v1_21_runtime_source_integrity_manifest.json",
                "sha256": "PENDING_MANIFEST_SHA",
            },
            "v1_20_interruption_adjudication": {
                "path": "reports/audits/phase36_v1_20_interruption_adjudication_v1_0.json",
                "sha256": V1_20_INTERRUPTION_ADJUDICATION_SHA,
            },
        },
        "acyclicity": {
            "bundle_contains_supervisor_sha256": False,
            "bundle_contains_launch_authority_file_sha256": False,
            "note": ("The bundle binds exec/manifest/governance. It NEVER carries "
                     "the supervisor SHA (acyclic by construction). The launcher's "
                     "expected SHAs are read from a SEPARATELY-FROZEN launch-authority "
                     "constant file whose OWN raw bytes are pinned by the supervisor."),
        },
        "terminal": "PHASE36_V1_21_PRELAUNCH_AUTHORITY_BUNDLE_WRITTEN",
    }

    m120 = json.loads(
        (AUD / "phase36_v1_20_runtime_source_integrity_manifest.json").read_text("utf-8"))
    manifest_doc = json.loads(rebase(json.dumps(m120)))
    manifest_doc["artifact"] = "phase36_v1_21_runtime_source_integrity_manifest"
    manifest_doc["revision"] = "ra_medfilm_barr_phase36_robustness_v1_21"
    manifest_doc["execution_source"] = "scripts/analysis/phase36_robustness_execution_v1_21.py"
    manifest_doc["execution_source_sha256"] = FROZEN_E_V121
    manifest_doc["supersedes_revision"] = "v1.20"
    manifest_doc["v1_20_consumed_state"] = "CONSUMED_INTERRUPTED_POST_START_PRE_SCIENTIFIC_RESULT"
    manifest_doc["d95_supervisor_interruption_repair"] = True
    manifest_doc["d95_repair_class"] = (
        "V1_20_SUPERVISOR_RETURNS_ZERO_ON_UNOBSERVED_CHILD_TERMINATION")
    dep_ok = True
    for rel, exp in manifest_doc["dependencies"].items():
        obs = sha_file(ROOT / rel)
        manifest_doc["dependency_verification"][rel] = {
            "expected": exp, "observed": obs, "match": obs == exp}
        dep_ok = dep_ok and obs == exp
    ck_ok = True
    for rel, exp in manifest_doc["checkpoints"].items():
        obs = sha_file(ROOT / rel)
        manifest_doc["checkpoint_verification"][rel] = {
            "expected": exp, "observed": obs, "match": obs == exp}
        ck_ok = ck_ok and obs == exp
    manifest_doc["all_dependencies_match"] = dep_ok
    manifest_doc["all_checkpoints_match"] = ck_ok
    manifest_doc["launcher_sha256_present"] = False
    manifest_doc["d61_canonical_fusion_preserved"] = True
    manifest_doc["d75_policy_b_preserved"] = True
    manifest_doc["d93a_journal_helper_defined"] = True
    manifest_doc["scientific_delta_distinct_classes"] = []
    manifest_doc["generated_utc"] = "2026-10-11T00:00:00Z"
    manifest_doc["non_circular_chain"] = [
        "SUPERVISOR pins frozen v1.21 launcher SHA + prelaunch-authority-bundle SHA before dispatch",
        "LAUNCHER pins literal v1.21 execution SHA + this manifest SHA + the v1.21 PRELAUNCH AUTHORITY BUNDLE SHA",
        "EXECUTION SOURCE reads this manifest, verifies its own bytes vs execution_source_sha256",
        "EXECUTION SOURCE requires the launch-authority token PHASE36_V1_21_LAUNCH_AUTHORITY",
    ]
    manifest_bytes = (json.dumps(manifest_doc, indent=1) + "\n").encode("utf-8")
    manifest_sha = sha(manifest_bytes)
    if not (dep_ok and ck_ok):
        print("WARN: manifest dependency/checkpoint mismatch", file=sys.stderr)
    bundle_doc["binds"]["v1_21_runtime_manifest"]["sha256"] = manifest_sha

    bundle_bytes = (json.dumps(bundle_doc, indent=1) + "\n").encode("utf-8")
    new_bundle_sha = sha(bundle_bytes)

    auth_doc = {
        "artifact": "phase36_v1_21_launch_authority_sha",
        "phase": 36,
        "revision": "ra_medfilm_barr_phase36_robustness_v1_21",
        "type": "LAUNCH_AUTHORITY_CONSTANT",
        "launcher": "scripts\\analysis\\launch_phase36_v1_21.py",
        "launcher_sha256": new_launcher_sha,
        "prelaunch_authority_bundle": "reports\\audits\\phase36_v1_21_prelaunch_authority_bundle.json",
        "prelaunch_authority_bundle_sha256": new_bundle_sha,
        "runtime_manifest_sha256": manifest_sha,
        "execution_source_sha256": FROZEN_E_V121,
        "release_attestation_sha256": V1_21_ATTESTATION_SHA,
        "d85_d88_d92_adjudication_sha256": D85_D88_D92_ADJUDICATION_SHA,
        "d85_d88_adjudication_sha256": V1_21_ADJUDICATION_SHA,
        "v1_20_interruption_adjudication_sha256": V1_20_INTERRUPTION_ADJUDICATION_SHA,
        "non_circular_note": ("The launcher reads its expected SHAs from this file; "
                              "the supervisor pins THIS FILE's raw bytes BEFORE Popen."),
        "terminal": "PHASE36_V1_21_LAUNCH_AUTHORITY_CONSTANT_WRITTEN",
    }
    auth_bytes = (json.dumps(auth_doc, indent=1) + "\n").encode("utf-8")
    new_authfile_sha = sha(auth_bytes)

    if (new_launcher_sha == launcher_sha and new_bundle_sha == bundle_sha
            and new_authfile_sha == authfile_sha):
        break
    launcher_sha, bundle_sha, authfile_sha = (
        new_launcher_sha, new_bundle_sha, new_authfile_sha)
else:
    print("FAIL_CLOSED: pin fixed point did not converge", file=sys.stderr)
    sys.exit(3)

s_txt = supervisor_text(bundle_sha, authfile_sha, launcher_sha)
s_bytes = s_txt.encode("utf-8")
supervisor_sha = sha(s_bytes)

# --------------------------------------------------------------------------- #
# WRITE (write-once)                                                            #
# --------------------------------------------------------------------------- #
results = {}
results["launcher"] = {
    "path": "scripts/analysis/launch_phase36_v1_21.py",
    "sha256": write_once(L_V121, l_bytes),
}
assert results["launcher"]["sha256"] == launcher_sha

results["supervisor"] = {
    "path": "scripts/analysis/supervise_phase36_v1_21.py",
    "sha256": write_once(S_V121, s_bytes),
}
results["manifest"] = {
    "path": str(MANIFEST_V121.relative_to(ROOT)).replace("\\", "/"),
    "sha256": write_once(MANIFEST_V121, manifest_bytes),
}
assert results["manifest"]["sha256"] == manifest_sha
results["bundle"] = {
    "path": str(BUNDLE_V121.relative_to(ROOT)).replace("\\", "/"),
    "sha256": write_once(BUNDLE_V121, bundle_bytes),
}
assert results["bundle"]["sha256"] == bundle_sha
results["launch_authority_file"] = {
    "path": str(LAUNCH_AUTH_V121.relative_to(ROOT)).replace("\\", "/"),
    "sha256": write_once(LAUNCH_AUTH_V121, auth_bytes),
}
assert results["launch_authority_file"]["sha256"] == authfile_sha

print(json.dumps({
    "built": results,
    "supervisor_sha256": supervisor_sha,
    "pins": {
        "v1_21_exec_sha256": FROZEN_E_V121,
        "v1_21_launcher_sha256": launcher_sha,
        "v1_21_manifest_sha256": manifest_sha,
        "v1_21_bundle_sha256": bundle_sha,
        "v1_21_launch_authority_file_sha256": authfile_sha,
    },
    "fixed_point_converged": True,
}, indent=2))
