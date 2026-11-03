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
NAMESPACE_NAME = "evidence_namespace.json"
SEAL_FIELD = "document_sha256"

#: The evidence namespace is **derived from the evidence class**, never supplied
#: independently by a caller.  Two namespaces exist and they never mix inside one
#: results root: a synthetic fixture and a real protocol-compliant evaluation are
#: different kinds of thing, and a root that contains both cannot be aggregated
#: into research evidence.
NAMESPACE_SYNTHETIC = "synthetic"
NAMESPACE_RESEARCH = "research"
EVIDENCE_NAMESPACES = {
    P.SYNTHETIC_EVIDENCE: NAMESPACE_SYNTHETIC,
    P.REAL_VAL_EVIDENCE: NAMESPACE_RESEARCH,
}
KNOWN_NAMESPACES = frozenset(EVIDENCE_NAMESPACES.values())


class NamespaceError(RuntimeError):
    """Raised when a cell's namespace contradicts its evidence class."""


def namespace_for(evidence_class: str) -> str:
    """The namespace an evidence class belongs to.  Raises for anything else."""
    try:
        return EVIDENCE_NAMESPACES[evidence_class]
    except KeyError:
        raise NamespaceError(
            f"evidence class {evidence_class!r} has no namespace; only "
            f"{sorted(EVIDENCE_NAMESPACES)} can be published in Phase C/D") from None


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
    # A real-evidence claim must be backed by a real run.  This is checked at
    # construction time as well as at verification time, so a synthetic identity
    # can never be wrapped in a research label in the first place.
    if evidence_class in P.RESEARCH_EVIDENCE_CLASSES:
        if synthetic:
            raise ProvenanceError("a synthetic run may not be labelled as research evidence")
        if not training_performed:
            raise ProvenanceError("research evidence requires training_performed=True")
        if not has_real_digest(adapter_identity):
            raise ProvenanceError(
                "research evidence requires a genuine SHA-256 weight digest; the adapter "
                "identity carries none (a synthetic adapter stamps SYNTHETIC::<component>)")
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


def seal_document(document: Mapping[str, Any]) -> str:
    """A self-seal over everything except the seal itself.

    Without it, editing ``evidence_class`` in ``cell_result.json`` would be
    invisible: the per-image hash covers the export, not the result document.
    """
    body = {k: v for k, v in document.items() if k != SEAL_FIELD}
    blob = json.dumps(body, sort_keys=True, allow_nan=False, default=_json_default).encode()
    return hashlib.sha256(blob).hexdigest()


def _namespace_document(*, model_key: str, seed: int, evidence_class: str,
                        synthetic: bool) -> Dict[str, Any]:
    return {"schema": "phase_c_evidence_namespace_v1",
            "namespace": namespace_for(evidence_class),
            "evidence_class": evidence_class,
            "synthetic": bool(synthetic),
            "cell": f"{model_key}::seed{int(seed)}",
            "note": ("A cell may only be aggregated as research evidence when its "
                     "namespace is 'research'. Synthetic cells are never promoted.")}


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

    # A cell directory belongs to exactly one namespace for its whole life.  A
    # synthetic fixture may not be relabelled by publishing a research run over
    # it, and a research cell may not be overwritten by a fixture.
    incoming_namespace = namespace_for(provenance["evidence_class"])
    marker_path = directory / NAMESPACE_NAME
    if marker_path.is_file():
        existing = json.loads(marker_path.read_text(encoding="utf-8")).get("namespace")
        if existing != incoming_namespace:
            raise NamespaceError(
                f"{directory} already holds {existing!r} evidence; refusing to publish "
                f"{incoming_namespace!r} evidence over it")

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
        "evidence_namespace": namespace_for(provenance["evidence_class"]),
        "synthetic": provenance["synthetic"],
        "per_image_sha256": per_image_sha,
        "per_image_rows": len(records),
        "summary": dict(summary),
        "provenance": dict(provenance),
        "config_sha256": config_sha256(provenance["evaluation_configuration"]),
        "statistics_policy": dict(provenance.get("statistics_policy", {})),
    }
    doc[SEAL_FIELD] = seal_document(doc)
    # The namespace marker is written before the result document and is sealed
    # into it, so a copied or relabelled cell contradicts itself.
    atomic_write_json(directory / NAMESPACE_NAME,
                      _namespace_document(model_key=provenance["model_key"],
                                          seed=provenance["seed"],
                                          evidence_class=provenance["evidence_class"],
                                          synthetic=provenance["synthetic"]))
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
_HEX_DIGITS = frozenset("0123456789abcdef")


def is_hex_digest(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and set(value) <= _HEX_DIGITS


def has_real_digest(provenance: Mapping[str, Any]) -> bool:
    """True only when the cell carries a genuine SHA-256 for its weights.

    A synthetic adapter stamps ``SYNTHETIC::<component>::<seed>`` instead, which
    is not a digest and therefore can never satisfy this.
    """
    if is_hex_digest(provenance.get("checkpoint_sha256")):
        return True
    components = provenance.get("component_sha256") or {}
    return bool(components) and all(is_hex_digest(v) for v in components.values())


def research_evidence_reasons(document: Mapping[str, Any]) -> List[str]:
    """Why a document is **not** eligible to count as research evidence.

    Empty list means eligible.  Every reason is structural: evidence class,
    namespace, the synthetic flag, whether training actually happened, and
    whether the weights carry a real digest.
    """
    reasons: List[str] = []
    prov = document.get("provenance") or {}
    evidence = document.get("evidence_class")
    if evidence not in P.RESEARCH_EVIDENCE_CLASSES:
        reasons.append(f"evidence class {evidence!r} is not research evidence")
    if document.get("evidence_namespace") != NAMESPACE_RESEARCH:
        reasons.append(f"namespace {document.get('evidence_namespace')!r} is not 'research'")
    if document.get("synthetic"):
        reasons.append("the cell is marked synthetic")
    if not prov.get("training_performed"):
        reasons.append("the cell records no training")
    if not has_real_digest(prov):
        reasons.append("the cell carries no genuine SHA-256 weight digest")
    if prov.get("split") in P.PROTECTED_SPLITS:
        reasons.append("the cell evaluated a protected split")
    if prov.get("test_reads"):
        reasons.append("the cell records protected-split reads")
    return reasons


def assert_research_evidence(document: Mapping[str, Any]) -> None:
    """Raise unless a document may be aggregated as research evidence."""
    reasons = research_evidence_reasons(document)
    if reasons:
        raise NamespaceError("not research evidence: " + "; ".join(reasons))


def _read_marker(directory: Path) -> Optional[Dict[str, Any]]:
    """The namespace marker in ``directory``, or ``None`` if absent/unreadable."""
    path = Path(directory) / NAMESPACE_NAME
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return {"namespace": None, "unreadable": True}
    return payload if isinstance(payload, dict) else {"namespace": None, "unreadable": True}


def _read_marker_namespace(directory: Path) -> Optional[str]:
    marker = _read_marker(directory)
    return None if marker is None else marker.get("namespace")


def scan_namespace_markers(root: Path) -> Dict[str, Any]:
    """Every namespace marker under ``root``, wherever it sits.

    The 24 registry paths are not the only place an artifact can land: a copied
    cell, a stray recursive copy, a nested results directory or a hand-made
    import all carry a marker at some other path.  Scanning the tree rather than
    only the expected 24 directories is what makes a mixed root detectable no
    matter where the foreign marker was put.

    A marker that is unreadable, carries an unknown namespace, or sits outside
    every registry cell path is recorded as a **problem**.  Problems are not
    repaired and not ignored: a contaminated root establishes nothing.
    """
    root = Path(root)
    expected = {f"{model}/seed{seed}" for model, seed in REG.model_seed_cells()}
    markers: List[Dict[str, Any]] = []
    problems: List[str] = []
    namespaces: set = set()
    if not root.exists():
        return {"markers": [], "namespaces": [], "problems": []}
    for path in sorted(root.rglob(NAMESPACE_NAME)):
        try:
            rel = path.parent.relative_to(root).as_posix()
        except ValueError:                                   # pragma: no cover - defensive
            rel = str(path.parent)
        on_cell = rel in expected
        marker = _read_marker(path.parent)
        namespace = None if marker is None else marker.get("namespace")
        markers.append({"path": rel, "namespace": namespace,
                        "cell": (marker or {}).get("cell"),
                        "evidence_class": (marker or {}).get("evidence_class"),
                        "on_registry_cell": on_cell})
        if (marker or {}).get("unreadable"):
            problems.append(f"{rel}: evidence namespace marker is unreadable")
        elif namespace in KNOWN_NAMESPACES:
            namespaces.add(namespace)
        else:
            problems.append(f"{rel}: unknown evidence namespace {namespace!r}")
        if not on_cell:
            problems.append(f"{rel}: evidence namespace marker outside every registry cell path")
    return {"markers": markers, "namespaces": sorted(namespaces),
            "problems": problems}


def verify_cell(directory: Path) -> Dict[str, Any]:
    """Re-read a published cell and recompute everything that can be recomputed."""
    directory = Path(directory)
    result_path = directory / RESULT_NAME
    reasons: List[str] = []
    if not result_path.is_file():
        # ``document`` is always present so a caller never has to distinguish
        # "absent" from "not in the payload" and crash on the difference.
        #
        # The namespace is still read from a marker if one exists.  An orphan
        # marker is exactly what a copied or half-migrated artifact leaves
        # behind, and hiding its namespace here would let it sit inside a root
        # without the matrix ever noticing that two namespaces coexist.
        missing = ["cell_result.json absent"]
        orphan = _read_marker_namespace(directory)
        if orphan is not None:
            missing.append(
                f"an evidence namespace marker ({orphan!r}) exists without a result document")
        return {"status": "MISSING", "reasons": missing,
                "document": None, "namespace": orphan}
    doc = json.loads(result_path.read_text(encoding="utf-8"))

    # 1. the document's own seal, so editing evidence_class cannot go unnoticed
    recorded_seal = doc.get(SEAL_FIELD)
    if not recorded_seal:
        reasons.append("result document carries no integrity seal")
    elif seal_document(doc) != recorded_seal:
        reasons.append("result document seal mismatch (the document was edited)")

    # 2. the namespace marker must exist and agree with the document
    namespace: Optional[str] = None
    marker_path = directory / NAMESPACE_NAME
    if not marker_path.is_file():
        reasons.append("evidence namespace marker absent")
    else:
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
        namespace = marker.get("namespace")
        if namespace != doc.get("evidence_namespace"):
            reasons.append(
                f"evidence namespace mismatch: marker {namespace!r} vs document "
                f"{doc.get('evidence_namespace')!r}")
        if marker.get("evidence_class") != doc.get("evidence_class"):
            reasons.append("evidence namespace marker disagrees on evidence class")
        if bool(marker.get("synthetic")) != bool(doc.get("synthetic")):
            reasons.append("evidence namespace marker disagrees on the synthetic flag")
        if marker.get("cell") != f"{doc.get('model_key')}::seed{doc.get('seed')}":
            reasons.append("evidence namespace marker names a different cell")

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

    # 3. a cell that claims real evidence must actually look real
    if doc.get("evidence_class") == P.REAL_VAL_EVIDENCE:
        if doc.get("synthetic"):
            reasons.append("a real-evidence cell is marked synthetic")
        if not prov.get("training_performed"):
            reasons.append("a real-evidence cell records no training")
        if not has_real_digest(prov):
            reasons.append("a real-evidence cell carries no genuine SHA-256 weight digest")

    return {"status": "COMPLETE_VALIDATED" if not reasons else "REJECTED",
            "reasons": reasons, "document": doc if not reasons else None,
            "namespace": namespace}


def verify_matrix(root: Path) -> Dict[str, Any]:
    """Verify all 24 cells; nothing is repaired and nothing is imputed.

    A root whose cells disagree about their evidence namespace is **mixed**: it
    contains both synthetic and research artifacts, which cannot be aggregated
    together.  Such a root establishes nothing, however many cells validate.
    """
    root = Path(root)
    cells = []
    for model_key, seed in REG.model_seed_cells():
        directory = root / model_key / f"seed{seed}"
        outcome = verify_cell(directory)
        cells.append({"model_key": model_key, "seed": seed,
                      "status": outcome["status"],
                      "reasons": outcome["reasons"],
                      "namespace": outcome.get("namespace")})
    counts: Dict[str, int] = {}
    for cell in cells:
        counts[cell["status"]] = counts.get(cell["status"], 0) + 1
    # Registry paths are not the only place evidence can sit, so the namespace
    # set is the union of what the 24 cells declare and what every marker under
    # the root declares.  Without the second half, copying a synthetic cell next
    # to a research marker anywhere off the expected 24 paths would go unnoticed.
    scan = scan_namespace_markers(root)
    namespaces = sorted({c["namespace"] for c in cells if c["namespace"]}
                        | set(scan["namespaces"]))
    consistent = len(namespaces) <= 1 and not scan["problems"]
    completed = 0
    if consistent:
        for cell in cells:
            if cell["status"] != "COMPLETE_VALIDATED":
                continue
            path = root / cell["model_key"] / f"seed{cell['seed']}" / RESULT_NAME
            doc = json.loads(path.read_text(encoding="utf-8"))
            if not research_evidence_reasons(doc):
                completed += 1
    return {"schema": "phase_c_24_cell_verification_v1", "root": str(root),
            "cells": cells, "counts": counts, "n_cells": len(cells),
            "namespaces": namespaces, "namespace_consistent": consistent,
            "namespace_markers": scan["markers"],
            "namespace_problems": scan["problems"],
            "research_cells_completed": completed,
            "note": ("A mixed root (synthetic and research artifacts together) "
                     "establishes nothing; it is refused rather than reconciled."
                     if not consistent else
                     "Synthetic cells validate but never count as established research.")}


__all__ = ["EVIDENCE_NAMESPACES", "INCOMPLETE_NAME", "KNOWN_NAMESPACES", "MAPS_DIR",
           "NAMESPACE_NAME", "NAMESPACE_RESEARCH", "NAMESPACE_SYNTHETIC", "NamespaceError",
           "PER_IMAGE_NAME", "PROGRESS_NAME", "ProvenanceError", "ProgressLedger",
           "PublicationError", "RESULT_NAME", "SCHEMA", "SEAL_FIELD",
           "assert_research_evidence", "atomic_write_bytes", "atomic_write_json",
           "atomic_write_text", "build_evaluation_provenance", "config_sha256",
           "evaluation_config", "export_maps", "has_real_digest", "hardware_identity",
           "is_hex_digest", "mark_incomplete", "namespace_for", "publish_cell",
           "research_evidence_reasons", "scan_namespace_markers", "seal_document",
           "verify_cell", "verify_matrix"]
