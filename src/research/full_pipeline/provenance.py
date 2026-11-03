"""Identity, atomic persistence and family-compatibility enforcement.

Three concerns, deliberately kept in one place so every producer behaves the same
way:

1. **SHA-256 identity** -- always ``Path(p).read_bytes()``; never a streamed read
   of a partially-written file, never a value carried in from memory.
2. **Atomic persistence** -- a checkpoint or JSON record is either the previous
   complete file or the new complete file, never a truncated one.  The execution
   harness can tear the process tree down at any instant.
3. **Family compatibility** -- a checkpoint carries the seed and the full upstream
   SHA chain of the family it belongs to.  Loading a component into a family it
   was not trained for raises instead of silently proceeding.

The envelope schema is versioned.  A checkpoint written by a different schema is
rejected rather than coerced.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import time
from pathlib import Path
from typing import Any, Mapping, Optional

import torch

__all__ = [
    "CHECKPOINT_SCHEMA",
    "FamilyCompatibilityError",
    "sha256_file",
    "sha256_bytes",
    "sha256_array",
    "atomic_write_bytes",
    "atomic_write_text",
    "atomic_write_json",
    "atomic_torch_save",
    "read_json",
    "build_envelope",
    "assert_compatible",
    "load_checkpoint",
    "describe_checkpoint",
    "utc_now",
]

#: bumped only when the envelope layout changes incompatibly
CHECKPOINT_SCHEMA = "ra_medfilm_barr_full_family_checkpoint_v1"

COMPONENTS = ("G", "R", "B", "S")


class FamilyCompatibilityError(RuntimeError):
    """Raised when a checkpoint is loaded into a family it does not belong to."""


# --------------------------------------------------------------------------- #
# identity
# --------------------------------------------------------------------------- #
def sha256_file(path: os.PathLike | str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_array(arr) -> str:
    import numpy as np

    return hashlib.sha256(np.ascontiguousarray(arr).tobytes()).hexdigest()


def utc_now() -> str:
    """Host clock is not synchronised; the value is recorded, not trusted.

    ``provenance.host_clock_trust`` in every manifest says so explicitly.
    """
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def relpath_str(path: os.PathLike | str, base: os.PathLike | str | None = None) -> str:
    """Repo-relative POSIX path when possible, otherwise the absolute path.

    A run root may legitimately live outside the repository (tests use a temp
    directory), so this never raises.
    """
    p = Path(path).resolve()
    root = Path(base).resolve() if base is not None else Path(__file__).resolve().parents[3]
    try:
        return p.relative_to(root).as_posix()
    except ValueError:
        return p.as_posix()


# --------------------------------------------------------------------------- #
# atomic persistence
# --------------------------------------------------------------------------- #
def atomic_write_bytes(data: bytes, path: os.PathLike | str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "wb") as fh:
        fh.write(data)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def atomic_write_text(text: str, path: os.PathLike | str) -> None:
    atomic_write_bytes(text.encode("utf-8"), path)


def atomic_write_json(obj: Any, path: os.PathLike | str) -> None:
    atomic_write_text(json.dumps(_jsonable(obj), indent=1, ensure_ascii=False) + "\n", path)


def atomic_torch_save(obj: Any, path: os.PathLike | str) -> None:
    """Serialise to memory first, then a single atomic byte write.

    ``torch.save`` straight to the destination can leave a zero-length file if the
    process dies mid-write; buffering removes that window entirely.
    """
    buf = io.BytesIO()
    torch.save(obj, buf)
    atomic_write_bytes(buf.getvalue(), path)


def read_json(path: os.PathLike | str, default: Optional[dict] = None) -> dict:
    p = Path(path)
    if not p.exists():
        return {} if default is None else default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {} if default is None else default


def _jsonable(o):
    import numpy as np

    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (np.float32, np.float64)):
        return float(o)
    if isinstance(o, (np.int32, np.int64)):
        return int(o)
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, Path):
        return str(o)
    if isinstance(o, dict):
        return {str(k): _jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_jsonable(v) for v in o]
    return o


# --------------------------------------------------------------------------- #
# envelope
# --------------------------------------------------------------------------- #
def build_envelope(*, component: str, seed: int, run_id: str, architecture_id: str,
                   model_state: Mapping[str, Any], upstream: Mapping[str, Mapping[str, str]],
                   epoch: int, best_epoch: int, selection: Mapping[str, Any],
                   recipe: Mapping[str, Any], history: Optional[list] = None,
                   optimizer_state=None, scheduler_state=None, rng_state=None,
                   extra: Optional[Mapping[str, Any]] = None,
                   family: str = "FULL") -> dict:
    """Assemble a versioned checkpoint envelope.

    ``upstream`` maps component -> ``{"path": <repo-relative>, "sha256": <hex>}``
    for every component this checkpoint depends on.  An empty mapping is only
    legitimate for ``G``.

    ``family`` discriminates the model family that produced the weights
    (``FULL`` or ``LITE``).  The *schema* is deliberately shared: both families
    use the same envelope layout, so one loader can read either, while the
    ``family`` field is what prevents a Lite checkpoint from being consumed as a
    FULL component (or the reverse).  The default keeps every existing caller
    byte-identical.
    """
    if component not in COMPONENTS:
        raise ValueError(f"unknown component {component!r}")
    if component != "G" and not upstream:
        raise ValueError(f"component {component} must record its upstream SHA chain")
    for name, ref in upstream.items():
        if "sha256" not in ref or not ref["sha256"]:
            raise ValueError(f"upstream {name} carries no sha256")
    env = {
        "schema": CHECKPOINT_SCHEMA,
        "method": "RA-MedFiLM-BARR",
        "family": str(family),
        "component": component,
        "seed": int(seed),
        "run_id": str(run_id),
        "architecture_id": str(architecture_id),
        "upstream": {k: dict(v) for k, v in upstream.items()},
        "epoch": int(epoch),
        "best_epoch": int(best_epoch),
        "selection": dict(selection),
        "recipe": dict(recipe),
        "model_state": model_state,
        "optimizer_state": optimizer_state,
        "scheduler_state": scheduler_state,
        "rng": rng_state,
        "history": list(history or []),
        "created_utc": utc_now(),
        "host_clock_trust": "NOT_ESTABLISHED",
        "test_reads": 0,
        "router_holdout_reads": 0,
    }
    if extra:
        env.update(dict(extra))
    return env


def describe_checkpoint(ckpt: Mapping[str, Any]) -> dict:
    """Small, hash-free summary used in logs and manifests."""
    return {
        "schema": ckpt.get("schema"),
        "component": ckpt.get("component"),
        "seed": ckpt.get("seed"),
        "run_id": ckpt.get("run_id"),
        "architecture_id": ckpt.get("architecture_id"),
        "epoch": ckpt.get("epoch"),
        "best_epoch": ckpt.get("best_epoch"),
        "upstream": {k: v.get("sha256", "")[:16] for k, v in (ckpt.get("upstream") or {}).items()},
    }


def assert_compatible(ckpt: Mapping[str, Any], *, component: str, seed: int,
                      upstream: Optional[Mapping[str, str]] = None,
                      family: Optional[str] = None,
                      path: Optional[os.PathLike | str] = None) -> None:
    """Fail closed unless ``ckpt`` belongs to the requested family.

    Checks, in order: schema, component, seed, model family (when requested) and
    every expected upstream digest.  ``upstream`` here maps component -> expected
    SHA-256.
    """
    where = f" ({path})" if path else ""
    if ckpt.get("schema") != CHECKPOINT_SCHEMA:
        raise FamilyCompatibilityError(
            f"checkpoint schema {ckpt.get('schema')!r} != {CHECKPOINT_SCHEMA!r}{where}")
    if ckpt.get("component") != component:
        raise FamilyCompatibilityError(
            f"checkpoint component {ckpt.get('component')!r} != {component!r}{where}")
    if int(ckpt.get("seed", -1)) != int(seed):
        raise FamilyCompatibilityError(
            f"checkpoint seed {ckpt.get('seed')!r} != {seed!r}{where}")
    if family is not None and ckpt.get("family") != family:
        raise FamilyCompatibilityError(
            f"checkpoint family {ckpt.get('family')!r} != {family!r}{where}")
    have = {k: (v or {}).get("sha256") for k, v in (ckpt.get("upstream") or {}).items()}
    for name, expected in (upstream or {}).items():
        if have.get(name) != expected:
            raise FamilyCompatibilityError(
                f"checkpoint upstream {name} {str(have.get(name))[:16]} != "
                f"expected {str(expected)[:16]}{where}")


def load_checkpoint(path: os.PathLike | str, *, map_location="cpu",
                    component: Optional[str] = None, seed: Optional[int] = None,
                    upstream: Optional[Mapping[str, str]] = None,
                    family: Optional[str] = None) -> dict:
    """Load and (optionally) verify a checkpoint envelope."""
    ck = torch.load(Path(path), map_location=map_location, weights_only=False)
    if not isinstance(ck, dict) or ck.get("schema") != CHECKPOINT_SCHEMA:
        raise FamilyCompatibilityError(f"{path} is not a {CHECKPOINT_SCHEMA} checkpoint")
    if component is not None or seed is not None or family is not None:
        assert_compatible(ck, component=component or ck.get("component"),
                          seed=seed if seed is not None else int(ck.get("seed")),
                          upstream=upstream, family=family, path=path)
    return ck
