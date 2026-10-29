"""Fail-closed, in-memory prediction contract; no filesystem data loader."""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
import numpy as np
from . import DOMAINS, SCHEMA_VERSION, VERSION, code_identity


def array_sha256(array):
    a = np.asarray(array)
    header = json.dumps({"dtype": a.dtype.str, "shape": list(a.shape)}, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(header + b"\n" + np.ascontiguousarray(a).tobytes()).hexdigest()


def validate_artifacts(records):
    """Validate a single experiment/model/seed/checkpoint set in memory.

    Hashes bind array dtype, shape and C-order bytes; metadata must carry a
    canonical JSON SHA-256 (excluding its own hash). This is integrity, not
    authentication or proof that a caller supplied an authorized population.
    """
    required = {"experiment_id", "model_id", "checkpoint_sha256", "seed", "dataset_id", "split",
                "sample_id", "domain_id", "class_schema_version", "probability_shape", "ground_truth_encoding",
                "threshold", "spacing", "evaluation_code_version", "probability_sha256", "ground_truth_sha256", "metadata_sha256",
                "release_id", "dataset_version", "split_sha256", "evaluation_code_sha256"}
    if not records:
        raise ValueError("empty artifact set")
    seen, identity = set(), None
    for record in records:
        if not isinstance(record, dict) or set(record) != {"metadata", "probability", "ground_truth"}:
            raise ValueError("invalid artifact envelope")
        m = record["metadata"]
        if not isinstance(m, dict) or not required.issubset(m):
            raise ValueError("missing required metadata")
        # Reject declared protected references, including optional path/source fields,
        # before inspecting arrays. No path is ever opened by this validator.
        def protected(value):
            if isinstance(value, dict):
                return any(protected(k) or protected(v) for k, v in value.items())
            if isinstance(value, (list, tuple)):
                return any(protected(v) for v in value)
            return isinstance(value, str) and bool(re.search(r"(^|[^a-z0-9])(test|router[_-]holdout|external|quarantin(?:e|ed))($|[^a-z0-9])", value, re.I))
        if any(protected(v) for k, v in m.items() if k not in {"experiment_id", "model_id"}):
            raise ValueError("prohibited population reference")
        for key in ("patient_id", "subgroup", "source_id"):
            if key in m and m[key] is not None and (not isinstance(m[key], str) or not m[key].strip()):
                raise ValueError("invalid optional grouping metadata")
        for key in ("experiment_id", "model_id", "dataset_id", "sample_id", "release_id", "dataset_version"):
            if not isinstance(m[key], str) or not m[key].strip():
                raise ValueError("empty identity")
        if m["split"] not in {"TRAIN", "VAL", "SYNTHETIC"}:
            raise ValueError("prohibited or unknown split")
        if m["domain_id"] not in DOMAINS or m["class_schema_version"] != SCHEMA_VERSION:
            raise ValueError("unknown domain or class schema")
        if m["evaluation_code_version"] != VERSION or m["evaluation_code_sha256"] != code_identity() or m["ground_truth_encoding"] != "binary_0_1":
            raise ValueError("unsupported version or encoding")
        if type(m["seed"]) is not int or not isinstance(m["threshold"], (int, float)) or isinstance(m["threshold"], bool) or not np.isfinite(m["threshold"]) or not 0 <= m["threshold"] <= 1:
            raise ValueError("invalid seed or threshold")
        if m["spacing"] is not None:
            s = np.asarray(m["spacing"], dtype=float)
            if s.shape != (2,) or not np.isfinite(s).all() or np.any(s <= 0):
                raise ValueError("invalid spacing")
        for key in ("checkpoint_sha256", "probability_sha256", "ground_truth_sha256", "metadata_sha256", "split_sha256", "evaluation_code_sha256"):
            if not isinstance(m[key], str) or not re.fullmatch(r"[0-9a-f]{64}", m[key]):
                raise ValueError("invalid digest")
        meta = {k: v for k, v in m.items() if k != "metadata_sha256"}
        try:
            actual = hashlib.sha256(json.dumps(meta, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
        except (ValueError, TypeError) as exc:
            raise ValueError("metadata is not canonical JSON") from exc
        if actual != m["metadata_sha256"]:
            raise ValueError("metadata hash mismatch")
        p, g = np.asarray(record["probability"]), np.asarray(record["ground_truth"])
        if p.ndim != 2 or not p.size or p.shape != g.shape or list(p.shape) != m["probability_shape"]:
            raise ValueError("shape mismatch")
        if p.dtype.kind not in "fiu" or not np.isfinite(p).all() or np.any((p < 0) | (p > 1)):
            raise ValueError("invalid probabilities")
        if g.dtype.kind not in "biuf" or not np.isfinite(g).all() or not np.isin(g, [0, 1]).all():
            raise ValueError("unknown ground-truth class IDs")
        if array_sha256(p) != m["probability_sha256"] or array_sha256(g) != m["ground_truth_sha256"]:
            raise ValueError("artifact hash mismatch")
        key = m["sample_id"]
        if key in seen:
            raise ValueError("duplicate sample ID")
        seen.add(key)
        current = tuple(m[k] for k in ("experiment_id", "model_id", "checkpoint_sha256", "seed", "dataset_id", "split", "class_schema_version", "evaluation_code_version", "threshold", "release_id", "dataset_version", "split_sha256", "evaluation_code_sha256"))
        if identity is not None and current != identity:
            raise ValueError("inconsistent artifact set identity")
        identity = current
    return {"valid": True, "sample_count": len(seen), "schema": SCHEMA_VERSION}


@dataclass(frozen=True)
class ArtifactSnapshot:
    """Owned immutable bytes, detached from the caller's mutable dictionaries."""
    metadata_json: bytes
    probability_bytes: bytes
    probability_dtype: str
    truth_bytes: bytes
    truth_dtype: str
    shape: tuple

    def record(self):
        return {"metadata": json.loads(self.metadata_json),
                "probability": np.frombuffer(self.probability_bytes, dtype=self.probability_dtype).reshape(self.shape),
                "ground_truth": np.frombuffer(self.truth_bytes, dtype=self.truth_dtype).reshape(self.shape)}


def freeze_artifacts(records):
    """Take an owned snapshot, validate it, return immutable contract objects.

    Copies occur before validation to prevent later caller mutation from changing
    the evaluated arrays. Authentication and concurrent hostile code are outside
    this integrity contract.
    """
    snapshots = []
    for r in records:
        try:
            if not isinstance(r, dict) or set(r) != {"metadata", "probability", "ground_truth"}:
                raise ValueError("invalid artifact envelope")
            p, g = np.asarray(r["probability"]), np.asarray(r["ground_truth"])
            snapshot = ArtifactSnapshot(json.dumps(r["metadata"], sort_keys=True, separators=(",", ":"), allow_nan=False).encode(),
                                        np.ascontiguousarray(p).tobytes(), p.dtype.str,
                                        np.ascontiguousarray(g).tobytes(), g.dtype.str, tuple(p.shape))
            # Different GT shape must be refused before byte reconstruction.
            if p.shape != g.shape or p.dtype.hasobject or g.dtype.hasobject:
                raise ValueError("shape or object dtype invalid")
            snapshots.append(snapshot)
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("invalid snapshot envelope") from exc
    validate_artifacts([s.record() for s in snapshots])
    return tuple(snapshots)

