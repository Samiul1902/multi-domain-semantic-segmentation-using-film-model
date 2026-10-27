"""Epoch transactions with immutable payloads and one atomic commit pointer."""
from __future__ import annotations

import hashlib
import io
import json
import os
import socket
import uuid
from contextlib import contextmanager
from pathlib import Path

import torch


class RecoveryError(RuntimeError):
    pass


def atomic_bytes(path: Path, raw: bytes) -> None:
    temp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        with temp.open("xb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


@contextmanager
def writer_lock(root: Path, *, recover: bool = False):
    """Atomic exclusive creation; never reclaim a live/foreign/unknown writer."""
    from src.utils.run_lock import _pid_alive
    root.mkdir(parents=True, exist_ok=True)
    path = root / "writer.lock"
    owner = {"pid": os.getpid(), "host": socket.gethostname(), "token": uuid.uuid4().hex}
    if path.exists():
        try:
            previous = json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, OSError) as exc:
            raise RecoveryError("C1_LOCK_CORRUPT_REVIEW_REQUIRED") from exc
        if (not recover or previous.get("host") != owner["host"] or
                type(previous.get("pid")) is not int or previous["pid"] <= 0 or
                _pid_alive(previous["pid"])):
            raise RecoveryError("C1_WRITER_LOCK_CONFLICT")
        path.unlink()  # Explicit recovery, same host, proven dead owner only.
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    except FileExistsError as exc:
        raise RecoveryError("C1_CONCURRENT_WRITER") from exc
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(owner, handle)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        yield
    finally:
        if path.exists() and json.loads(path.read_text(encoding="utf-8")) == owner:
            path.unlink()


class EpochStore:
    def __init__(self, root: Path):
        self.root = Path(root)

    def commit(self, state: dict, fault=None) -> None:
        """Caller holds writer_lock. Pointer replacement is the commit point."""
        self.root.mkdir(parents=True, exist_ok=True)
        buf = io.BytesIO()
        torch.save(state, buf)
        raw = buf.getvalue()
        name = f"epoch-{state['epoch']:04d}-{uuid.uuid4().hex}.pt"
        if fault:
            fault("before_payload")
        atomic_bytes(self.root / name, raw)
        if fault:
            fault("after_payload")
        pointer = {"file": name, "sha256": hashlib.sha256(raw).hexdigest(),
                   "epoch": state["epoch"], "identity": state["identity"]}
        if fault:
            fault("before_pointer")
        atomic_bytes(self.root / "latest.json", json.dumps(pointer, sort_keys=True).encode())
        if fault:
            fault("after_pointer")

    def load(self, identity: str) -> dict:
        """Fail on committed corruption; never silently roll back to an older epoch."""
        try:
            pointer_path = self.root / "latest.json"
            if pointer_path.is_symlink():
                raise RecoveryError("C1_CHECKPOINT_POINTER_SYMLINK")
            pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
            name = pointer["file"]
            if (not isinstance(name, str) or Path(name).name != name or
                    not name.startswith("epoch-") or not name.endswith(".pt") or
                    pointer["identity"] != identity or (self.root / name).is_symlink()):
                raise RecoveryError("C1_CHECKPOINT_POINTER_IDENTITY")
            raw = (self.root / name).read_bytes()
            if hashlib.sha256(raw).hexdigest() != pointer["sha256"]:
                raise RecoveryError("C1_CHECKPOINT_CORRUPTED")
            state = torch.load(io.BytesIO(raw), map_location="cpu", weights_only=True)
            if state["identity"] != identity or state["epoch"] != pointer["epoch"]:
                raise RecoveryError("C1_CHECKPOINT_PAYLOAD_IDENTITY")
            return state
        except RecoveryError:
            raise
        except Exception as exc:
            raise RecoveryError("C1_CHECKPOINT_UNREADABLE") from exc

    def lifecycle(self, state: str, identity: str) -> None:
        atomic_bytes(self.root / "lifecycle.json",
                     json.dumps({"state": state, "identity": identity}).encode())
