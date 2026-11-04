"""Write-once, byte-preserving research packages and local release bookkeeping.

No data discovery, checkpoint deserialization, authorization minting or scientific
execution occurs here. Trust in expected manifest hashes belongs to the caller.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import math
import platform
import re
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

SCHEMA = "ra_medfilm_barr_package_v1"
COMPONENTS = {"G", "R", "B", "S"}


class ArtifactError(ValueError):
    """An artifact violates its declared identity or structural contract."""


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _sha(value: Any) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ArtifactError("expected a complete lowercase SHA-256")
    return value


def _json(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def _write_once(path: Path, value: Any) -> None:
    with path.open("xb") as stream:
        stream.write(_json(value))
        stream.flush()
        import os
        os.fsync(stream.fileno())


def _member(root: Path, name: str) -> Path:
    p = PurePosixPath(name)
    if not name or "\\" in name or ":" in name or p.is_absolute() or ".." in p.parts:
        raise ArtifactError(f"unsafe package path: {name!r}")
    candidate = root.joinpath(*p.parts)
    if any(part.is_symlink() for part in (candidate, *candidate.parents)):
        raise ArtifactError("symlinks are not permitted in packages")
    if not candidate.resolve().is_relative_to(root.resolve()):
        raise ArtifactError("package path escapes root")
    return candidate


def validate_config(config: Mapping[str, Any]) -> None:
    required = {"family", "seed", "protocol_sha256", "source_sha256", "preprocessing",
                "roi_threshold", "segmentation_threshold", "safety_threshold",
                "router_numeric_dim", "task_embedding_dim", "router_total_dim",
                "evidence_class"}
    if set(config) != required:
        raise ArtifactError(f"configuration fields differ: {set(config) ^ required}")
    if config["family"] not in {"FULL", "LITE", "HISTORICAL_PHASE26"}:
        raise ArtifactError("unsupported checkpoint family")
    if type(config["seed"]) is not int or config["seed"] not in {42, 123, 3407}:
        raise ArtifactError("unsupported seed family")
    for key in ("protocol_sha256", "source_sha256"):
        _sha(config[key])
    for key, expected in {"roi_threshold": .30, "segmentation_threshold": .50,
                          "safety_threshold": .50, "router_numeric_dim": 202,
                          "task_embedding_dim": 16, "router_total_dim": 218}.items():
        if isinstance(config[key], bool) or config[key] != expected:
            raise ArtifactError(f"frozen contract mismatch: {key}")
    prep = config["preprocessing"]
    if not isinstance(prep, dict) or set(prep) != {"channels", "resolution", "implementation_sha256", "contract_id"}:
        raise ArtifactError("incomplete preprocessing identity")
    expected_channels = 1 if config["family"] == "HISTORICAL_PHASE26" else 3
    if type(prep["channels"]) is not int or prep["channels"] != expected_channels or prep["resolution"] != 512:
        raise ArtifactError("preprocessing channel/resolution mismatch")
    _sha(prep["implementation_sha256"])
    if not isinstance(prep["contract_id"], str) or not prep["contract_id"].strip() or prep["contract_id"].upper() in {"TODO", "TBD", "UNKNOWN"}:
        raise ArtifactError("missing preprocessing contract")
    if config["evidence_class"] not in {"SYNTHETIC_TEST_ONLY", "RESEARCH_ARTIFACT_NOT_DEPLOYMENT_AUTHORIZATION"}:
        raise ArtifactError("invalid evidence class")


def environment() -> dict:
    return {"python": platform.python_version(), "platform": platform.platform(),
            "dependencies": sorted({f"{d.metadata['Name']}=={d.version}" for d in importlib.metadata.distributions()})}


def package(destination: Path, components: Mapping[str, Path], expected: Mapping[str, str],
            config: Mapping[str, Any], *, evidence: Mapping[str, Path] | None = None) -> str:
    """Copy exact supplied bytes; publish manifest last. Returns its digest.

    Evidence files can bind protocol, manifest identity and manuscript references.
    Only pass permitted metadata artifacts, never protected dataset content.
    """
    validate_config(config)
    if set(components) != COMPONENTS or set(expected) != COMPONENTS:
        raise ArtifactError("exactly G/R/B/S identities are required")
    for name, path in components.items():
        if digest(path) != _sha(expected[name]):
            raise ArtifactError(f"checkpoint identity mismatch: {name}")
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    members = {}
    sources = {f"components/{k}.pt": Path(v) for k, v in components.items()}
    for name, path in (evidence or {}).items():
        sources[f"evidence/{name}"] = Path(path)
    # Never overwrite an incomplete attempt. Recovery uses a new version/path.
    for name, source in sorted(sources.items()):
        target = _member(destination, name)
        target.parent.mkdir(parents=True, exist_ok=True)
        before = digest(source)
        with source.open("rb") as src, target.open("xb") as dst:
            import shutil
            shutil.copyfileobj(src, dst)
        observed = digest(target)
        component = PurePosixPath(name).stem
        if observed != before or (name.startswith("components/") and observed != expected[component]):
            raise ArtifactError(f"source changed while packaging: {name}")
        members[name] = {"sha256": observed, "bytes": target.stat().st_size}
    _write_once(destination / "manifest.json", {"schema": SCHEMA, "config": dict(config),
                "members": members, "environment": environment(),
                "deployment_authorized": False})
    sha = digest(destination / "manifest.json")
    verify(destination, sha)
    return sha


def verify(root: Path, expected_manifest_sha256: str) -> dict:
    root = Path(root)
    manifest = _member(root, "manifest.json")
    if digest(manifest) != _sha(expected_manifest_sha256):
        raise ArtifactError("manifest identity mismatch")
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    if payload.get("schema") != SCHEMA or payload.get("deployment_authorized") is not False:
        raise ArtifactError("invalid package schema/authority")
    validate_config(payload["config"])
    members = payload["members"]
    if not {f"components/{c}.pt" for c in COMPONENTS}.issubset(members):
        raise ArtifactError("missing component identities")
    for name, identity in members.items():
        path = _member(root, name)
        if not path.is_file() or path.stat().st_size != identity["bytes"] or digest(path) != _sha(identity["sha256"]):
            raise ArtifactError(f"artifact identity mismatch: {name}")
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}
    if actual != set(members) | {"manifest.json"}:
        raise ArtifactError("unlisted package files")
    return payload


def register(registry: Path, version: str, root: Path, manifest_sha256: str) -> Path:
    """Register bytes, not permission to deploy them."""
    if not re.fullmatch(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", version):
        raise ArtifactError("version must be major.minor.patch")
    payload = verify(root, manifest_sha256)
    registry = Path(registry)
    registry.mkdir(parents=True, exist_ok=True)
    path = registry / f"{version}.json"
    _write_once(path, {"version": version, "package": str(Path(root).resolve()),
                      "manifest_sha256": manifest_sha256, "evidence_class": payload["config"]["evidence_class"]})
    return path


def rollback(registry: Path, from_version: str, to_version: str, event_id: str) -> Path:
    """Record a verified rollback request; activation remains an authorized operation."""
    if not re.fullmatch(r"[A-Za-z0-9_-]+", event_id):
        raise ArtifactError("invalid rollback event id")
    entries = []
    for version in (from_version, to_version):
        if not re.fullmatch(r"\d+\.\d+\.\d+", version):
            raise ArtifactError("invalid release version")
        entry = json.loads((Path(registry) / f"{version}.json").read_text())
        verify(Path(entry["package"]), entry["manifest_sha256"])
        entries.append(entry)
    path = Path(registry) / f"rollback-{event_id}.json"
    _write_once(path, {"from": entries[0], "to": entries[1], "status": "ROLLBACK_REQUEST_RECORDED__ACTIVATION_NOT_AUTHORIZED"})
    return path


def monitor(observed: Mapping[str, float], bounds: Mapping[str, tuple[float, float]],
            *, output_regression: bool) -> dict:
    if not bounds or set(observed) != set(bounds):
        raise ArtifactError("monitoring statistics/bounds mismatch")
    triggers = []
    for name, (low, high) in bounds.items():
        value = observed[name]
        if not all(math.isfinite(v) for v in (low, high, value)) or low > high:
            raise ArtifactError("nonfinite or inverted monitoring bounds")
        if not low <= value <= high:
            triggers.append(name)
    return {"status": "CHECK_REQUIRED" if triggers or output_regression else "WITHIN_DECLARED_BOUNDS",
            "input_drift_triggers": triggers, "output_regression": bool(output_regression),
            "recalibration_performed": False}
