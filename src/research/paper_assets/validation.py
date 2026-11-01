"""Validators that reject inconsistent or non-authentic paper-asset inputs."""
from __future__ import annotations

import math
from collections import Counter

REQUIRED_PROVENANCE = ("source_artifact", "population", "n", "metric_unit",
                       "evaluation_version", "provenance_run", "evidence_class")
EVIDENCE_CLASSES = {
    "matched",
    "exploratory",
    "descriptive",
    "analytical",
    "specification",
    "PROTOCOL_INCOMPARABLE",
}


class AssetValidationError(ValueError):
    pass


def require_unique_ids(ids, label="case"):
    ids = list(ids)
    if any(i is None or str(i).strip() == "" for i in ids):
        raise AssetValidationError(f"missing {label} id")
    dup = [k for k, v in Counter(ids).items() if v > 1]
    if dup:
        raise AssetValidationError(f"duplicate {label} ids: {dup[:3]}")


def require_finite(values, label="measurement"):
    for v in values:
        if v is None or isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
            raise AssetValidationError(f"nonfinite {label}: {v!r}")


def require_dataset_labels(labels, allowed):
    bad = sorted(set(labels) - set(allowed))
    if bad:
        raise AssetValidationError(f"incorrect dataset labels: {bad}")


def require_funnel(total, routed, adopted, rejected, beneficial=None, harmful=None, unchanged=0):
    if routed > total:
        raise AssetValidationError("routed exceeds total")
    if adopted + rejected != routed:
        raise AssetValidationError("adopted + rejected != routed")
    if beneficial is not None and beneficial + harmful + unchanged != adopted:
        raise AssetValidationError("outcome counts do not sum to adopted")


def require_paired_sign(treatment, control, delta, tol=1e-9):
    for t, c, d in zip(treatment, control, delta):
        if abs((t - c) - d) > tol:
            raise AssetValidationError("paired difference must equal treatment - control")


def require_pp_label(delta_proportion, delta_pp, tol=1e-6):
    if abs(delta_proportion * 100.0 - delta_pp) > tol:
        raise AssetValidationError("percentage-point value inconsistent with proportion difference")


def require_provenance(record: dict):
    missing = [k for k in REQUIRED_PROVENANCE if record.get(k) in (None, "")]
    if missing:
        raise AssetValidationError(f"missing provenance fields: {missing}")
    if record["evidence_class"] not in EVIDENCE_CLASSES:
        raise AssetValidationError(f"unknown evidence_class: {record['evidence_class']}")


def require_authentic(status):
    if "SYNTHETIC" in str(status).upper():
        raise AssetValidationError("synthetic result cannot be rendered as real")
