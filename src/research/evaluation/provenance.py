"""Evaluation provenance, atomic publication and safe resumption.

Three properties are enforced here rather than documented:

**Atomic publication.** A cell directory is only readable as complete once
``cell_result.json`` exists.  Every file is written to a temporary name in the
same directory, flushed, ``fsync``-ed and then ``os.replace``-d into place, so an
interrupted write can never leave a half-file that looks finished.  The result
document is written **last**.

**No silent duplication.** A resumed run reads ``_state/progress.jsonl`` and
skips the samples it already scored.  The final export is checked for duplicate
``sample_id`` values and for a roster that differs from the requested one; either
fails the cell instead of publishing it.

**Provenance is mandatory and verifiable.** :func:`build_evaluation_provenance`
produces the block every cell carries, and :func:`verify_cell_provenance` re-reads
it from disk and recomputes every hash it can.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

import numpy as np

from . import metrics as MET
from . import protocol as P
from . import registry as REG
from . import stats as ST

SCHEMA = "phase_c_evaluation_cell_v1"
PROGRESS_NAME = "progress.jsonl"
RESULT_NAME = "cell_result.json"
PER_IMAGE_NAME = "per_image.csv"
INCOMPLETE_NAME = ".incomplete"
MAPS_DIR = "maps"


class ProvenanceError(RuntimeError):
    pass


class PublicationError(RuntimeError):
    pass


# --------------------------------------------------------------------------- #
# Atomic IO
# --------------------------------------------------------------------------- #
def atomic_write_bytes(path: Path, payload: bytes) -> str:
    """Write ``payload`` atomically and return its SHA-256."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp{os.getpid()}")
    with open(tmp, "wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)
    if path.stat().st_size != len(payload):
        raise PublicationError(f"{path}: size {path.stat().st_size} != {len(payload)}")
    return hashlib.sha256(payload).hexdigest()


def atomic_write_text(path: Path, text: str) -> str:
    return atomic_write_bytes(path, text.encode("utf-8"))


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> str:
    return atomic_write_text(path, json.dumps(payload, indent=2, sort_keys=True,
                                              allow_nan=False, default=_json_default))


def _json_default(value: Any) -> Any:
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    raise TypeError(f"not JSON serialisable: {type(value).__name__}")


# --------------------------------------------------------------------------- #
# Provenance block
# --------------------------------------------------------------------------- #
def hardware_identity() -> Dict[str, Any]:
    import torch

    cuda = torch.cuda.is_available()
    return {"platform": platform.platform(), "processor": platform.processor(),
            "python": platform.python_version(), "torch": torch.__version__,
            "cuda": torch.version.cuda if cuda else None,
            "device_name": torch.cuda.get_device_name(0) if cuda else "cpu",
            "device_count": torch.cuda.device_count() if cuda else 0}


def build_evaluation_provenance(*, model_key: str, seed: int, split: str,
                                adapter_identity: Mapping[str, Any],
                                evidence_class: str,
                                split_manifest_sha256: str,
                                n_images: int,
                                evaluation_configuration: Mapping[str, Any],
                                synthetic: bool,
                                training_performed: bool,
                                protected_reads: int = 0) -> Dict[str, Any]:
    """The block a cell carries.  Every field is either measured or declared."""
    if split in P.PROTECTED_SPLITS:
        raise ProvenanceError(f"{split} may not be evaluated in Phase C")
    if protected_reads:
        raise ProvenanceError(f"{protected_reads} protected-split reads occurred")
    return {
        "schema": SCHEMA,
        "model_key": model_key,
        "model_display_name": REG.DISPLAY_NAME[model_key],
        "seed": int(seed),
        "adapter_kind": adapter_identity.get("adapter_kind"),
        "adapter_identity": dict(adapter_identity),
        "checkpoint_sha256": adapter_identity.get("checkpoint_sha256"),
        "component_sha256": adapter_identity.get("component_sha256"),
        "training_protocol_version": adapter_identity.get("training_protocol_version",
                                                          "unknown"),
        "split": split,
        "split_semantics": P.SPLIT_SEMANTICS[split]["label"],
        "split_manifest_sha256": split_manifest_sha256,
        "n_images": int(n_images),
        "preprocessing_id": P.PREPROCESSING_ID,
        "preprocessing_sha256": P.preprocessing_sha256(),
        "metric_implementation_version": P.METRIC_IMPLEMENTATION_VERSION,
        "evaluation_configuration": dict(evaluation_configuration),
        "evidence_class": evidence_class,
        "evidence_label": P.evidence_label(evidence_class),
        "synthetic": bool(synthetic),
        "training_performed": bool(training_performed),
        "protected_splits_accessed": False,
        "test_reads": 0,
        "hardware": hardware_identity(),
        "statistics_policy": {"inference_class": ST.EXPLORATORY,
                              "confirmatory_authorized": ST.CONFIRMATORY_AUTHORIZED,
                              "p_value": None},
    }


def evaluation_config(*, threshold: float = P.SEGMENTATION_OUTPUT_THRESHOLD,
                      unit: str = "image", n_boot: int = ST.DEFAULT_N_BOOT,
                      bootstrap_seed: int = ST.DEFAULT_SEED,
                      export_maps: bool = False, batch_size: int = 1) -> Dict[str, Any]:
    return {"threshold": float(threshold), "threshold_role": "SEGMENTATION_OUTPUT_THRESHOLD",
            "roi_proposal_threshold": P.ROI_PROPOSAL_THRESHOLD,
            "safety_accept_threshold": P.SOMEGA_ACCEPT_THRESHOLD,
            "resolution": P.RESOLUTION, "channel_policy": P.CHANNEL_POLICY,
            "batch_size": int(batch_size), "export_maps": bool(export_maps),
            "bootstrap": {"n_boot": int(n_boot), "seed": int(bootstrap_seed),
                          "resampling_unit": unit, "alpha": 0.05},
            "hd95_unit": "pixel", "hd95_spacing_mm": None,
            "metric_implementation_version": P.METRIC_IMPLEMENTATION_VERSION}


def config_sha256(config: Mapping[str, Any]) -> str:
    return hashlib.sha256(json.dumps(config, sort_keys=True, default=str).encode()).hexdigest()


# --------------------------------------------------------------------------- #
# Progress ledger (resume without duplication)
# --------------------------------------------------------------------------- #
class ProgressLedger:
    """Append-only record of scored samples for one cell.

    Each line carries the **whole per-image record**, not just its identity.  That
    is what makes resumption able to publish a complete cell: a resumed pass has
    to emit the union of what it just scored and what an earlier pass scored, and
    the earlier records exist nowhere else.  A line written by an older format
    (identity only) is therefore refused rather than silently dropped, because
    dropping it would publish a roster that is missing images.
    """

    def __init__(self, directory: Path) -> None:
        self.path = Path(directory) / PROGRESS_NAME
        self.done: Dict[str, str] = {}
        self._records: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.is_file():
            return
        with self.path.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    # a torn final line from an interrupted append is discarded
                    continue
                sample_id = str(row["sample_id"])
                self.done[sample_id] = str(row.get("dice_sha256", ""))
                if isinstance(row.get("record"), dict):
                    self._records[sample_id] = row["record"]

    def has(self, sample_id: str) -> bool:
        return str(sample_id) in self.done

    def record_for(self, sample_id: str) -> Dict[str, Any]:
        """The stored record for an already-scored sample."""
        key = str(sample_id)
        if key not in self.done:
            raise ProvenanceError(f"{key} is not in the progress ledger")
        if key not in self._records:
            raise ProvenanceError(
                f"{key}: the ledger entry carries no record payload, so a resumed pass "
                "cannot rebuild a complete roster; delete the ledger and re-score the cell")
        return dict(self._records[key])

    def record(self, sample_id: str, record: Mapping[str, Any]) -> None:
        payload = {"sample_id": str(sample_id),
                   "dice_sha256": hashlib.sha256(
                       f"{record['dice']:.12f}".encode()).hexdigest(),
                   "record": dict(record)}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True, default=_json_default) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        self.done[str(sample_id)] = payload["dice_sha256"]
        self._records[str(sample_id)] = dict(record)

    def reset(self) -> None:
        """Discard a previous pass so a fresh run cannot append to stale state."""
        self.done.clear()
        self._records.clear()
        if self.path.exists():
            self.path.unlink()

    @property
    def count(self) -> int:
        return len(self.done)


# --------------------------------------------------------------------------- #
# Publication
# --------------------------------------------------------------------------- #
def publish_cell(directory: Path, *, records: Sequence[Mapping[str, Any]],
                 provenance: Mapping[str, Any], summary: Mapping[str, Any],
                 expected_sample_ids: Optional[Iterable[str]] = None) -> Dict[str, Any]:
    """Publish a completed cell atomically.  ``cell_result.json`` is written last."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    if not records:
        raise PublicationError("refusing to publish a cell with no records")

    ids = [str(r["sample_id"]) for r in records]
    if len(ids) != len(set(ids)):
        dupes = sorted({i for i in ids if ids.count(i) > 1})[:5]
        raise PublicationError(f"duplicate sample_id values in the export: {dupes}")
    if expected_sample_ids is not None:
        expected = {str(i) for i in expected_sample_ids}
        if set(ids) != expected:
            raise PublicationError(
                f"roster mismatch: missing {len(expected - set(ids))}, "
                f"unexpected {len(set(ids) - expected)}")

    columns = sorted({k for r in records for k in r})
    lines = [",".join(columns)]
    for record in records:
        lines.append(",".join(_csv_cell(record.get(c)) for c in columns))
    csv_payload = ("\n".join(lines) + "\n").encode("utf-8")
    per_image_sha = atomic_write_bytes(directory / PER_IMAGE_NAME, csv_payload)

    doc = {
        "schema": SCHEMA,
        "model_key": provenance["model_key"], "seed": provenance["seed"],
        "split": provenance["split"], "n_images": len(records),
        "evidence_class": provenance["evidence_class"],
        "evidence_label": provenance["evidence_label"],
        "synthetic": provenance["synthetic"],
        "per_image_sha256": per_image_sha,
        "per_image_rows": len(records),
        "summary": dict(summary),
        "provenance": dict(provenance),
        "config_sha256": config_sha256(provenance["evaluation_configuration"]),
        "statistics_policy": dict(provenance.get("statistics_policy", {})),
    }
    # Last write: the cell is not complete until this file exists.
    atomic_write_json(directory / RESULT_NAME, doc)
    marker = directory / INCOMPLETE_NAME
    if marker.exists():
        marker.unlink()
    return doc


def mark_incomplete(directory: Path) -> None:
    atomic_write_text(Path(directory) / INCOMPLETE_NAME, "incomplete\n")


def _csv_cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, float):
        if value != value:
            return "nan"
        return repr(value)
    text = str(value)
    if any(ch in text for ch in ',"\n'):
        return '"' + text.replace('"', '""') + '"'
    return text


def export_maps(directory: Path, sample_id: str, probability: np.ndarray,
                binary: np.ndarray) -> Dict[str, str]:
    """Persist one probability map and its binary mask, atomically."""
    maps = Path(directory) / MAPS_DIR
    maps.mkdir(parents=True, exist_ok=True)
    safe = hashlib.sha256(str(sample_id).encode()).hexdigest()[:16]
    prob_payload = np.ascontiguousarray(probability, dtype=np.float32).tobytes()
    bin_payload = np.ascontiguousarray(binary, dtype=np.uint8).tobytes()
    return {"probability": atomic_write_bytes(maps / f"{safe}.prob.f32", prob_payload),
            "binary": atomic_write_bytes(maps / f"{safe}.mask.u8", bin_payload),
            "probability_file": str((maps / f"{safe}.prob.f32").relative_to(directory)),
            "binary_file": str((maps / f"{safe}.mask.u8").relative_to(directory))}


# --------------------------------------------------------------------------- #
# Verification
# --------------------------------------------------------------------------- #
def verify_cell(directory: Path) -> Dict[str, Any]:
    """Re-read a published cell and recompute everything that can be recomputed."""
    directory = Path(directory)
    result_path = directory / RESULT_NAME
    reasons: List[str] = []
    if not result_path.is_file():
        # ``document`` is always present so a caller never has to distinguish
        # "absent" from "not in the payload" and crash on the difference.
        return {"status": "MISSING", "reasons": ["cell_result.json absent"],
                "document": None}
    doc = json.loads(result_path.read_text(encoding="utf-8"))

    per_image = directory / PER_IMAGE_NAME
    if not per_image.is_file():
        reasons.append("per_image.csv absent")
    else:
        digest = hashlib.sha256(per_image.read_bytes()).hexdigest()
        if digest != doc.get("per_image_sha256"):
            reasons.append("per_image.csv hash mismatch")

    prov = doc.get("provenance", {})
    if prov.get("synthetic") and doc.get("evidence_class") != P.SYNTHETIC_EVIDENCE:
        reasons.append("synthetic run not labelled SYNTHETIC_TEST_ONLY")
    if prov.get("protected_splits_accessed"):
        reasons.append("protected split accessed")
    if prov.get("split") in P.PROTECTED_SPLITS:
        reasons.append(f"cell evaluated a protected split ({prov.get('split')})")
    if doc.get("config_sha256") != config_sha256(prov.get("evaluation_configuration", {})):
        reasons.append("evaluation configuration hash mismatch")
    if prov.get("metric_implementation_version") != P.METRIC_IMPLEMENTATION_VERSION:
        reasons.append("metric implementation version mismatch")
    if prov.get("preprocessing_sha256") != P.preprocessing_sha256():
        reasons.append("preprocessing identity mismatch")
    stats_policy = doc.get("statistics_policy") or {}
    if stats_policy.get("p_value") is not None:
        reasons.append("a p-value was recorded without a frozen procedure")
    summary = doc.get("summary") or {}
    if "equal_domain_macro_dice" not in summary:
        reasons.append("summary missing equal_domain_macro_dice")

    return {"status": "COMPLETE_VALIDATED" if not reasons else "REJECTED",
            "reasons": reasons, "document": doc if not reasons else None}


def verify_matrix(root: Path) -> Dict[str, Any]:
    """Verify all 24 cells; nothing is repaired and nothing is imputed."""
    root = Path(root)
    cells = []
    for model_key, seed in REG.model_seed_cells():
        directory = root / model_key / f"seed{seed}"
        outcome = verify_cell(directory)
        cells.append({"model_key": model_key, "seed": seed,
                      "status": outcome["status"],
                      "reasons": outcome["reasons"]})
    counts: Dict[str, int] = {}
    for cell in cells:
        counts[cell["status"]] = counts.get(cell["status"], 0) + 1
    return {"schema": "phase_c_24_cell_verification_v1", "root": str(root),
            "cells": cells, "counts": counts, "n_cells": len(cells),
            "research_cells_completed": sum(
                1 for c in cells
                if c["status"] == "COMPLETE_VALIDATED"
                and (root / c["model_key"] / f"seed{c['seed']}" / RESULT_NAME).is_file()
                and json.loads((root / c["model_key"] / f"seed{c['seed']}"
                                / RESULT_NAME).read_text(encoding="utf-8")
                               ).get("evidence_class") in P.RESEARCH_EVIDENCE_CLASSES)}


__all__ = ["INCOMPLETE_NAME", "MAPS_DIR", "PER_IMAGE_NAME", "PROGRESS_NAME",
           "ProvenanceError", "ProgressLedger", "PublicationError", "RESULT_NAME",
           "SCHEMA", "atomic_write_bytes", "atomic_write_json", "atomic_write_text",
           "build_evaluation_provenance", "config_sha256", "evaluation_config",
           "export_maps", "hardware_identity", "mark_incomplete", "publish_cell",
           "verify_cell", "verify_matrix"]
