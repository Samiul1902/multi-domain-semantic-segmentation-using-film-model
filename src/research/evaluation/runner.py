"""The evaluation driver: ground-truth-free inference, then separate scoring.

The loop is deliberately split in two so the separation is visible in the code
and testable from outside::

    prediction = adapter.predict(sample["image"], sample["task_id"])   # no GT
    record     = metrics.score_prediction(..., ground_truth=sample["mask"])

``adapter.predict`` never receives the mask, and
``tests/test_evaluation_phase_c.py::test_gt_never_reaches_model_inference`` spies
on it to prove that rather than trusting the shape of the loop.

Resumption is sample-level: a scored sample is recorded in the cell's progress
ledger and skipped on the next pass, so an interrupted run neither re-scores nor
duplicates.  The final export is checked for duplicate ids before publication.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Iterator, List, Mapping, Optional, Sequence

import numpy as np
import torch
from PIL import Image

from src.data.transforms import SegmentationTransform

from . import adapters as A
from . import metrics as MET
from . import protocol as P
from . import provenance as PROV
from . import registry as REG


class RunnerError(RuntimeError):
    pass


@dataclass
class Sample:
    """One image to evaluate.  ``mask`` is only read by the scorer."""

    sample_id: str
    domain: str
    task_id: int
    image: torch.Tensor
    mask: np.ndarray
    patient_id: Optional[str] = None
    group_key: Optional[str] = None
    original_height: int = 0
    original_width: int = 0

    def as_meta(self) -> Dict[str, Any]:
        return {"sample_id": self.sample_id, "domain": self.domain,
                "task_id": self.task_id, "patient_id": self.patient_id,
                "group_key": self.group_key,
                "original_height": self.original_height,
                "original_width": self.original_width}


# --------------------------------------------------------------------------- #
# Sample loading
# --------------------------------------------------------------------------- #
def _transform() -> SegmentationTransform:
    return SegmentationTransform(P.RESOLUTION, train=False, image_mode=P.CHANNEL_POLICY[:3])


def load_manifest_samples(manifest_path: Path, split: str, *,
                          domains: Optional[Sequence[str]] = None,
                          limit_per_domain: Optional[int] = None,
                          guard: Optional[P.ProtectedSplitGuard] = None,
                          root: Optional[Path] = None) -> List[Sample]:
    """Read images and masks for an allowed split, deterministically ordered.

    ``split`` is checked before a single file is opened, so a protected split can
    never be reached through this function even by accident.
    """
    import pandas as pd

    if guard is not None:
        guard.open(split)
    else:
        P.assert_split_readable(split)

    frame = pd.read_csv(manifest_path)
    if "sample_id" not in frame:
        raise RunnerError(f"{manifest_path} has no sample_id column")
    frame = frame.sort_values(["dataset", "sample_id"]).reset_index(drop=True)
    wanted = set(domains) if domains else set(P.DOMAINS)
    transform = _transform()

    samples: List[Sample] = []
    seen: Dict[str, int] = {}
    base = Path(root) if root is not None else P.ROOT
    for row in frame.itertuples():
        domain = str(row.dataset)
        if domain not in wanted:
            continue
        if limit_per_domain is not None and seen.get(domain, 0) >= limit_per_domain:
            continue
        image_path = _resolve(str(row.image_path), base)
        mask_path = _resolve(str(row.mask_path), base)
        if not image_path.is_file() or not mask_path.is_file():
            raise RunnerError(f"{row.sample_id}: missing image or mask on disk")
        with Image.open(image_path) as handle:
            image = handle.convert(P.CHANNEL_POLICY[:3])
            height, width = image.height, image.width
        with Image.open(mask_path) as handle:
            mask = handle.convert("L")
        tensor, mask_tensor, _meta = transform(image, mask)
        samples.append(Sample(
            sample_id=str(row.sample_id), domain=domain, task_id=int(row.task_id),
            image=tensor.unsqueeze(0), mask=(mask_tensor[0].numpy() > 0),
            patient_id=_optional(getattr(row, "patient_id", None)),
            group_key=_optional(getattr(row, "case_id", None)),
            original_height=int(height), original_width=int(width)))
        seen[domain] = seen.get(domain, 0) + 1
    if not samples:
        raise RunnerError(f"no samples selected from {manifest_path}")
    return samples


def _optional(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value)
    return None if text in ("", "nan", "None", "NOT_AVAILABLE") else text


def _resolve(path_text: str, base: Path) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else (base / path)


def synthetic_samples(bundle_root: Path, *, per_domain_val: int = 3,
                      guard: Optional[P.ProtectedSplitGuard] = None) -> List[Sample]:
    """Deterministic synthetic VAL samples with patient and group identifiers."""
    from src.research.full_pipeline.synth import build_synthetic_population

    if guard is not None:
        guard.open(P.SPLIT_VAL)
    # Resolve first: the generator writes absolute paths into the manifest, so a
    # relative bundle root would produce paths that do not resolve from the CWD.
    resolved = Path(bundle_root).resolve()
    bundle = build_synthetic_population(resolved, per_domain_val=per_domain_val)
    return load_manifest_samples(bundle.val_csv, P.SPLIT_VAL, guard=guard, root=resolved)


# --------------------------------------------------------------------------- #
# Cell evaluation
# --------------------------------------------------------------------------- #
def evaluate_cell(adapter: A.ModelAdapter, samples: Sequence[Sample], *,
                  directory: Optional[Path] = None,
                  threshold: float = P.SEGMENTATION_OUTPUT_THRESHOLD,
                  export_maps: bool = False,
                  resume: bool = False,
                  warmup: int = 2) -> Dict[str, Any]:
    """Score one (model, seed) cell.  Inference first, scoring second.

    On ``resume`` the returned ``records`` are the **whole roster**, not just the
    samples scored this pass: the earlier pass's records are read back from the
    progress ledger and merged in roster order.  Without that merge a resumed cell
    could never be published, because its export would be missing every image the
    first pass already scored.
    """
    if not samples:
        raise RunnerError("no samples")
    # The ledger is written on EVERY pass, not only on resume: otherwise an
    # interrupted first pass would leave nothing to resume from.  ``resume`` only
    # decides whether entries already present are honoured.
    ledger = PROV.ProgressLedger(directory) if directory else None
    if directory:
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        if not resume:
            PROV.mark_incomplete(directory)
            ledger.reset()   # a fresh pass owns the ledger

    roster = [s.sample_id for s in samples]
    records: List[Dict[str, Any]] = []
    scored_now = 0
    started = time.perf_counter()
    for sample in samples:
        if resume and ledger is not None and ledger.has(sample.sample_id):
            records.append(ledger.record_for(sample.sample_id))
            continue
        prediction = adapter.predict(sample.image, sample.task_id)      # no GT here
        record = MET.score_prediction(
            sample_id=sample.sample_id, domain=sample.domain, task_id=sample.task_id,
            final_probability=prediction.probability,
            global_probability=prediction.global_probability,
            ground_truth=sample.mask, state=prediction.state, threshold=threshold,
            patient_id=sample.patient_id, group_key=sample.group_key)
        record["original_height"] = sample.original_height
        record["original_width"] = sample.original_width
        record["original_non_square"] = bool(sample.original_height != sample.original_width)
        records.append(record)
        scored_now += 1
        if ledger is not None:
            ledger.record(sample.sample_id, record)
        if directory and export_maps:
            PROV.export_maps(Path(directory), sample.sample_id,
                             prediction.probability, prediction.binary(threshold))

    if not records:
        raise RunnerError("no samples were scored")
    if [r["sample_id"] for r in records] != roster:
        raise RunnerError("resumed roster does not match the requested sample order")
    elapsed = time.perf_counter() - started
    summary = MET.aggregate_records(records)
    summary["elapsed_seconds"] = elapsed
    summary["images_per_second"] = (scored_now / elapsed) if (scored_now and elapsed > 0) else None
    summary["n_scored_this_pass"] = scored_now
    summary["n_from_ledger"] = len(records) - scored_now
    return {"records": records, "summary": summary,
            "adapter_identity": adapter.identity(),
            "parameter_count": adapter.parameter_count(),
            "evidence_class": adapter.evidence_class,
            "synthetic": adapter.source == "synthetic"}


def run_cell(model_key: str, seed: int, samples: Sequence[Sample], *, root: Path,
             source: str = "synthetic", device: str = "cpu",
             resume: bool = False, export_maps: bool = False,
             threshold: float = P.SEGMENTATION_OUTPUT_THRESHOLD,
             split: str = P.SPLIT_VAL,
             split_manifest_sha256: Optional[str] = None,
             adapter: Optional[A.ModelAdapter] = None,
             publish: bool = True) -> Dict[str, Any]:
    """Build (or accept) an adapter, evaluate, and publish atomically."""
    directory = Path(root) / model_key / f"seed{seed}"
    own_adapter = adapter is None
    if own_adapter:
        adapter = A.build_adapter(model_key, seed, device=device, source=source)
    try:
        if own_adapter:
            adapter.load()
        outcome = evaluate_cell(adapter, samples, directory=directory,
                                threshold=threshold, export_maps=export_maps,
                                resume=resume)
        config = PROV.evaluation_config(threshold=threshold, export_maps=export_maps)
        provenance = PROV.build_evaluation_provenance(
            model_key=model_key, seed=seed, split=split,
            adapter_identity=outcome["adapter_identity"],
            evidence_class=outcome["evidence_class"],
            split_manifest_sha256=(split_manifest_sha256
                                   or P.manifest_sha256(P.SPLIT_VAL)),
            n_images=len(outcome["records"]),
            evaluation_configuration=config,
            synthetic=outcome["synthetic"],
            training_performed=not outcome["synthetic"])
        outcome["provenance"] = provenance
        outcome["directory"] = str(directory)
        if publish:
            outcome["document"] = PROV.publish_cell(
                directory, records=outcome["records"], provenance=provenance,
                summary=outcome["summary"],
                expected_sample_ids=[s.sample_id for s in samples])
        return outcome
    finally:
        if own_adapter and adapter is not None:
            adapter.close()


def run_matrix(root: Path, samples: Sequence[Sample], *, source: str = "synthetic",
               device: str = "cpu", seeds: Sequence[int] = REG.SEEDS,
               models: Sequence[str] = REG.DISPLAY_ORDER,
               resume: bool = False, export_maps: bool = False,
               split_manifest_sha256: Optional[str] = None,
               progress: Optional[Callable[[str, int, str], None]] = None) -> Dict[str, Any]:
    """Execute every requested cell.  A failing cell is reported, never faked."""
    root = Path(root)
    cells: List[Dict[str, Any]] = []
    for model_key in models:
        for seed in seeds:
            if progress is not None:
                progress(model_key, seed, "start")
            try:
                outcome = run_cell(model_key, seed, samples, root=root, source=source,
                                   device=device, resume=resume,
                                   export_maps=export_maps,
                                   split_manifest_sha256=split_manifest_sha256)
                cells.append({"model_key": model_key, "seed": seed,
                              "status": "EXECUTED",
                              "evidence_class": outcome["evidence_class"],
                              "equal_domain_macro_dice":
                                  outcome["summary"]["equal_domain_macro_dice"],
                              "parameters": outcome["parameter_count"],
                              "directory": outcome["directory"]})
            except Exception as exc:
                cells.append({"model_key": model_key, "seed": seed,
                              "status": "FAILED",
                              "reason": f"{type(exc).__name__}: {exc}"})
            if progress is not None:
                progress(model_key, seed, cells[-1]["status"])
    executed = sum(1 for c in cells if c["status"] == "EXECUTED")
    return {"schema": "phase_c_matrix_execution_v1",
            "source": source, "device": device,
            "n_cells": len(cells), "n_executed": executed,
            "n_failed": len(cells) - executed,
            "research_cells_completed": 0,
            "evidence_class": (P.SYNTHETIC_EVIDENCE if source == "synthetic"
                               else P.REAL_VAL_EVIDENCE),
            "cells": cells,
            "note": ("Executed is not the same as established. Synthetic cells can "
                     "never complete a research cell.")}


def records_by_cell(root: Path) -> Dict[tuple, List[Dict[str, Any]]]:
    """Re-read published per-image exports, keyed by (model, seed)."""
    import csv

    out: Dict[tuple, List[Dict[str, Any]]] = {}
    for model_key, seed in REG.model_seed_cells():
        path = Path(root) / model_key / f"seed{seed}" / PROV.PER_IMAGE_NAME
        if not path.is_file():
            continue
        rows: List[Dict[str, Any]] = []
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                for key in ("dice", "iou", "precision", "recall", "hd95",
                            "global_dice", "delta_dice_vs_global"):
                    if key in row and row[key] != "":
                        try:
                            row[key] = float(row[key])
                        except ValueError:
                            row[key] = float("nan")
                for key in ("refiner_executed", "accepted", "harmful_accepted",
                            "gt_empty", "pred_empty", "empty_gt_false_positive"):
                    if key in row:
                        row[key] = str(row[key]).strip().lower() == "true"
                rows.append(row)
        if rows:
            out[(model_key, seed)] = rows
    return out


__all__ = ["RunnerError", "Sample", "evaluate_cell", "load_manifest_samples",
           "records_by_cell", "run_cell", "run_matrix", "synthetic_samples"]
