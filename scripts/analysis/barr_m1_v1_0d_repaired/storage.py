"""Single-bundle write-once commit with explicit partial recovery.

All per-case/per-domain/contrast outputs live in one canonical JSON bundle, so
there is no partially committed multi-file result. A hash receipt is embedded.
"""
import json
import os
from contextlib import contextmanager
from pathlib import Path
from .contracts import require, Refusal, canonical, digest, valid_sha, INPUT_SHAS, CHECKPOINT_SHAS


def validate_binding(binding):
    require(set(binding) == {"input_shas", "checkpoint_shas", "authorization_id", "harness_sha256"}, "E_OUTPUT_BINDING")
    require(binding["input_shas"] == INPUT_SHAS and binding["checkpoint_shas"] == CHECKPOINT_SHAS,
            "E_OUTPUT_INPUT_SHA")
    require(valid_sha(binding["harness_sha256"]) and isinstance(binding["authorization_id"], str)
            and bool(binding["authorization_id"].strip()), "E_OUTPUT_BINDING")


def encode_result(binding, result):
    validate_binding(binding)
    require(isinstance(result, dict) and "per_case" in result, "E_OUTPUT_SCHEMA")
    cases = result["per_case"]
    require(isinstance(cases, list) and len(cases) > 0 and all(isinstance(x, dict) and
            isinstance(x.get("sample_id"), str) and x["sample_id"].strip() for x in cases), "E_OUTPUT_SCHEMA")
    require(len({x["sample_id"] for x in cases}) == len(cases), "E_SAMPLE_ID_DUPLICATE")
    # Caller supplies deterministic statistics; sort case output for stable identity.
    result = dict(result, per_case=sorted(cases, key=lambda x: x["sample_id"]))
    body = dict(binding=binding, result=result)
    return canonical(dict(body=body, sha256=digest(canonical(body))))


def verify_committed(path, expected):
    require(not path.is_symlink(), "E_PATH_UNAUTHORIZED")
    try:
        data = path.read_bytes()
        envelope = json.loads(data)
        require(digest(canonical(envelope["body"])) == envelope["sha256"], "E_OUTPUT_CORRUPT")
        require(data == expected, "E_OUTPUT_CONFLICT")
    except (ValueError, KeyError, OSError) as exc:
        if isinstance(exc, Refusal):
            raise
        raise Refusal("E_OUTPUT_CORRUPT") from exc


def finalize(stage, final):
    if os.name == "nt":
        import ctypes
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.MoveFileExW.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint32]
        kernel.MoveFileExW.restype = ctypes.c_int
        # Same-directory rename; WRITE_THROUGH, without REPLACE_EXISTING.
        if not kernel.MoveFileExW(str(stage), str(final), 8):
            raise OSError(ctypes.get_last_error(), "atomic non-replacing commit failed")
    else:
        os.link(stage, final)  # atomic create, fails if destination exists
        stage.unlink()
        fd = os.open(final.parent, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


@contextmanager
def exclusive_run_lock(path):
    """OS lock is released even on process death; never delete the lock inode."""
    require(not path.is_symlink(), "E_PATH_UNAUTHORIZED")
    with path.open("a+b") as stream:
        stream.seek(0, os.SEEK_END)
        if stream.tell() == 0:
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise Refusal("E_OUTPUT_CONCURRENT_OR_CONFLICT") from exc
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == "nt":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def commit(root, binding, result, *, recover=False, fault=None):
    """fault is a test-only callback, never an execution or authorization switch."""
    expected = encode_result(binding, result)
    root = Path(root).absolute()
    require(not any(p.is_symlink() or getattr(p, "is_junction", lambda: False)()
                    for p in [root, *root.parents]), "E_PATH_UNAUTHORIZED")
    identity = digest(canonical(binding))
    root.mkdir(parents=True, exist_ok=True)
    with exclusive_run_lock(root / (identity + ".lock")):
        return _commit_locked(root, identity, expected, recover=recover, fault=fault)


def _commit_locked(root, identity, expected, *, recover, fault):
    final, stage = root / (identity + ".json"), root / (identity + ".partial")
    require(not stage.is_symlink() and not final.is_symlink(), "E_PATH_UNAUTHORIZED")
    if final.exists():
        verify_committed(final, expected)
        if stage.exists():
            require(recover, "E_PARTIAL_RECOVERY_REQUIRED")
            require(expected.startswith(stage.read_bytes()), "E_PARTIAL_CONFLICT")
            stage.unlink()
        return final
    if stage.exists():
        require(recover, "E_PARTIAL_RECOVERY_REQUIRED")
        require(expected.startswith(stage.read_bytes()), "E_PARTIAL_CONFLICT")
        # No committed bytes exist. Explicitly discard only this verified prefix.
        stage.unlink()
    def point(name):
        if fault:
            fault(name)
    point("before_write")
    try:
        with stage.open("xb") as stream:
            middle = len(expected) // 2
            stream.write(expected[:middle])
            stream.flush()
            os.fsync(stream.fileno())
            point("during_write")
            stream.write(expected[middle:])
            stream.flush()
            os.fsync(stream.fileno())
        point("before_commit")
        finalize(stage, final)
        point("after_commit")
    except FileExistsError as exc:
        raise Refusal("E_OUTPUT_CONCURRENT_OR_CONFLICT") from exc
    verify_committed(final, expected)
    return final
