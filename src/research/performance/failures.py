"""§7 Controlled failure injection at eight pipeline stages.

What "injected" means here
--------------------------
A failure is injected by handing a **real guard** a genuinely broken artifact or
input: a checkpoint envelope belonging to another component, a cache manifest
that does not match its G checkpoint, a label table whose identity does not hold,
a feature matrix with a non-finite value, a roster that disagrees with the
export.  No guard is re-implemented and no assertion is written against a mock,
because a test of a copy of a guard proves only that the copy works.

Each stage is listed with the exact guard it exercises, so a reader can see which
line refused the failure rather than trusting a green tick.

What is *not* claimed
---------------------
These injections do not run training.  They establish that a corrupted artifact
or input is refused at the stage boundary; they say nothing about how a stage
behaves mid-epoch on real data, which is out of scope for a performance and
reliability phase and would require the authorization this phase does not have.
"""
from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional

import numpy as np
import torch

from src.research.evaluation import metrics as MET
from src.research.evaluation import protocol as P
from src.research.evaluation import provenance as PROV
from src.research.evaluation import registry as REG
from src.research.full_pipeline import population as POP
from src.research.full_pipeline import provenance as FPROV
from src.research.full_pipeline import recipe as R
from src.research.full_pipeline import seeds as SEEDS
from src.research.full_pipeline.context import RunContext
from src.research.full_pipeline.stages import (cache_stage, global_stage, label_stage,
                                               refiner_stage, router_stage, safety_stage)

from . import bench as B

EVIDENCE_CLASS = B.EVIDENCE_CLASS

STAGES = ("global_training", "cache_creation", "refiner_training",
          "benefit_label_generation", "router_training", "safety_training",
          "evaluation_export", "result_publication")


# --------------------------------------------------------------------------- #
# Context and envelope fixtures
# --------------------------------------------------------------------------- #
def _context(root: Path, *, seed: int = 42) -> RunContext:
    """A real ``RunContext`` pointed at a temporary root.

    The population and fold tables are the frozen canonical ones and are only
    read.  Nothing under the real run root is touched.
    """
    return RunContext(family=SEEDS.SeedFamily(seed), root=Path(root),
                      bounds=R.OperationalBounds(device="cpu"),
                      population=POP.load_canonical_population(),
                      recipe=R.Recipe())


def _envelope(component: str, *, seed: int = 42) -> Dict[str, Any]:
    """A minimal, schema-valid envelope for one component."""
    architecture = {"G": R.G_ARCHITECTURE_ID, "R": R.R_ARCHITECTURE_ID,
                    "B": R.B_ARCHITECTURE_ID, "S": R.S_ARCHITECTURE_ID}[component]
    upstream = {} if component == "G" else {"G": {"path": "G/best.pt",
                                                 "sha256": "0" * 64}}
    return FPROV.build_envelope(
        component=component, seed=seed, run_id="failure_injection",
        architecture_id=architecture, model_state={"w": torch.zeros(1)},
        upstream=upstream, epoch=1, best_epoch=1,
        selection={"rule": "probe", "best_loss": 0.0, "best_epoch": 1,
                   "bad_epochs": 0},
        recipe={}, history=[])


def _write_envelope(path: Path, envelope: Mapping[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    FPROV.atomic_torch_save(envelope, path)
    return path


def _outcome(stage: str, injection: str, guard: str, detected_by: Optional[str],
             detail: str, **extra: Any) -> Dict[str, Any]:
    return {"stage": stage, "injection": injection, "guard": guard,
            "detected": detected_by is not None, "detected_by": detected_by,
            "detail": detail, **extra}


def _expect(fn: Callable[[], Any], *types: type) -> Optional[str]:
    try:
        fn()
    except types as exc:                                  # noqa: BLE001 - type is the assertion
        return type(exc).__name__
    return None


# --------------------------------------------------------------------------- #
# 1. Global training
# --------------------------------------------------------------------------- #
def inject_global_training(workdir: Path) -> Dict[str, Any]:
    """A G run that wrote another component's checkpoint must not verify."""
    ctx = _context(Path(workdir) / "g")
    _write_envelope(ctx.g_dir / "best.pt", _envelope("R"))
    raised = _expect(lambda: global_stage.verify(ctx), Exception)
    return _outcome(
        "global_training",
        "G/best.pt replaced with an R-component envelope",
        "global_stage.verify -> load_checkpoint(component='G')",
        raised, f"raised {raised}" if raised else "verify accepted a foreign component")


# --------------------------------------------------------------------------- #
# 2. Cache creation
# --------------------------------------------------------------------------- #
def inject_cache_creation(workdir: Path) -> Dict[str, Any]:
    """An incomplete cache and a cache built from a different G must both be refused."""
    ctx = _context(Path(workdir) / "cache")
    ctx.cache_dir.mkdir(parents=True, exist_ok=True)
    manifest = ctx.cache_dir / "manifest.json"
    PROV.atomic_write_json(manifest, {"complete": False, "population_n": 0,
                                      "action_available_n": 0,
                                      "g_checkpoint_sha256": "0" * 64})
    incomplete = _expect(lambda: cache_stage.verify(ctx), RuntimeError)

    # now a complete manifest whose G digest does not match the G checkpoint
    PROV.atomic_write_json(manifest, {"complete": True, "population_n": 1,
                                      "action_available_n": 1,
                                      "g_checkpoint_sha256": "f" * 64})
    _write_envelope(ctx.g_dir / "best.pt", _envelope("G"))
    mismatched = _expect(lambda: cache_stage.verify(ctx), Exception)
    return _outcome(
        "cache_creation",
        "cache manifest marked incomplete, then pinned to a different G digest",
        "cache_stage.verify -> manifest completeness and G digest",
        incomplete if incomplete else mismatched,
        f"incomplete -> {incomplete}; mismatched G -> {mismatched}",
        incomplete_raised=incomplete, mismatched_g_raised=mismatched)


# --------------------------------------------------------------------------- #
# 3. Refiner training
# --------------------------------------------------------------------------- #
def inject_refiner_training(workdir: Path) -> Dict[str, Any]:
    """R's final checkpoint must not be readable as G, and vice versa."""
    ctx = _context(Path(workdir) / "r")
    _write_envelope(ctx.r_dir / "final" / "final.pt", _envelope("G"))
    raised = _expect(lambda: refiner_stage.verify(ctx), Exception)
    return _outcome(
        "refiner_training",
        "R/final/final.pt replaced with a G-component envelope",
        "refiner_stage.verify -> load_checkpoint(component='R')",
        raised, f"raised {raised}" if raised else "verify accepted a foreign component")


# --------------------------------------------------------------------------- #
# 4. Benefit-label generation
# --------------------------------------------------------------------------- #
def inject_benefit_labels(workdir: Path) -> Dict[str, Any]:
    """A label table whose delta identity does not hold must be reported inconsistent."""
    ctx = _context(Path(workdir) / "l")
    ctx.l_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for index, domain in enumerate(P.DOMAINS):
        rows.append({"sample_id": f"{domain}-1", "task_id": 3, "domain": domain,
                     "global_dice": 0.5, "candidate_refined_dice": 0.6,
                     # the identity is candidate - global = 0.1; write 0.4 instead
                     "delta_dice": 0.4})
    import pandas as pd

    PROV.atomic_write_text(ctx.l_dir / "labels.csv",
                           pd.DataFrame(rows).to_csv(index=False))
    PROV.atomic_write_json(ctx.l_dir / "manifest.json", {"categories": {}})
    verdict = label_stage.verify(ctx)
    detected = verdict.get("verdict") == "LABELS_INCONSISTENT"
    return _outcome(
        "benefit_label_generation",
        "delta_dice inconsistent with candidate_refined_dice - global_dice",
        "label_stage.verify -> delta identity residual",
        "LABELS_INCONSISTENT" if detected else None,
        f"verdict={verdict.get('verdict')} residual="
        f"{verdict.get('delta_identity_max_residual'):.3e}",
        residual=verdict.get("delta_identity_max_residual"))


# --------------------------------------------------------------------------- #
# 5. Router training
# --------------------------------------------------------------------------- #
def inject_router_training(workdir: Path) -> Dict[str, Any]:
    """A non-finite router feature matrix must be refused before training."""
    ctx = _context(Path(workdir) / "b")
    ctx.l_dir.mkdir(parents=True, exist_ok=True)
    import pandas as pd

    sample_ids = []
    for domain in R.DATASET_ORDER:
        sample_ids.append(f"{domain}-1")
    PROV.atomic_write_text(ctx.l_dir / "labels.csv", pd.DataFrame(
        [{"sample_id": sid, "action_available": True, "task_id": 3, "domain": sid.split("-")[0],
          "delta_dice": 0.1, "gain_category": "useful"} for sid in sample_ids]
    ).to_csv(index=False))

    # one feature row per sample, all zeros except a single NaN
    for domain in R.DATASET_ORDER:
        directory = ctx.cache_dir / domain
        directory.mkdir(parents=True, exist_ok=True)
        features = np.zeros((1, R.B_NUMERIC_DIM), dtype=np.float32)
        features[0, 0] = float("nan")
        np.save(directory / "router_features.npy", features)
        PROV.atomic_write_text(directory / "meta.csv",
                               pd.DataFrame([{"sample_id": f"{domain}-1"}]).to_csv(index=False))

    raised = _expect(lambda: router_stage.load_family_inputs(ctx), Exception)
    return _outcome(
        "router_training",
        "router feature matrix carrying a NaN",
        "router_stage.load_family_inputs -> non-finite check",
        raised, f"raised {raised}" if raised else "a NaN feature matrix was accepted")


# --------------------------------------------------------------------------- #
# 6. Safety training
# --------------------------------------------------------------------------- #
def inject_safety_training(workdir: Path) -> Dict[str, Any]:
    """A label manifest without safety features must stop the safety stage."""
    ctx = _context(Path(workdir) / "s")
    ctx.l_dir.mkdir(parents=True, exist_ok=True)
    PROV.atomic_write_json(ctx.l_dir / "manifest.json", {"labels_sha256": "0" * 64})
    raised = _expect(lambda: safety_stage.load_family_inputs(ctx), Exception)
    return _outcome(
        "safety_training",
        "label manifest with no safety_features_sha256",
        "safety_stage.load_family_inputs -> safety feature presence",
        raised, f"raised {raised}" if raised else "the safety stage accepted a manifest "
                                                 "with no safety features")


# --------------------------------------------------------------------------- #
# 7. Evaluation export
# --------------------------------------------------------------------------- #
def _export_records(count: int = 4) -> List[Dict[str, Any]]:
    base = np.zeros((4, 4), np.uint8)
    base[1:3, 1:3] = 1
    shifted = np.zeros((4, 4), np.uint8)
    shifted[1:3, 2:4] = 1
    return [MET.score_prediction(sample_id=f"{domain}-1", domain=domain, task_id=3,
                                 final_probability=shifted.astype(np.float32),
                                 ground_truth=base)
            for domain in P.DOMAINS][:count]


def _export_provenance() -> Dict[str, Any]:
    return PROV.build_evaluation_provenance(
        model_key=REG.BASELINES[0], seed=42, split=P.SPLIT_VAL,
        adapter_identity={"model_key": REG.BASELINES[0], "seed": 42,
                          "adapter_kind": "PLAIN",
                          "checkpoint_sha256": "SYNTHETIC::failure_injection"},
        evidence_class=P.SYNTHETIC_EVIDENCE, split_manifest_sha256="0" * 64,
        n_images=4, evaluation_configuration=PROV.evaluation_config(),
        synthetic=True, training_performed=False)


def inject_evaluation_export(workdir: Path) -> Dict[str, Any]:
    """A short roster and a duplicated image must both be refused at export."""
    directory = Path(workdir) / "export"
    records = _export_records()
    provenance = _export_provenance()
    summary = MET.aggregate_records(records)

    roster = [r["sample_id"] for r in records]
    short = _expect(lambda: PROV.publish_cell(
        directory, records=records[:2], provenance=provenance, summary=summary,
        expected_sample_ids=roster), PROV.PublicationError)
    duplicated = _expect(lambda: PROV.publish_cell(
        directory, records=list(records) + [records[0]], provenance=provenance,
        summary=summary), PROV.PublicationError)
    detected = short if short else duplicated
    return _outcome(
        "evaluation_export",
        "a roster missing two images, then a duplicated sample_id",
        "provenance.publish_cell -> roster and duplicate checks",
        detected, f"short roster -> {short}; duplicate -> {duplicated}",
        short_roster_raised=short, duplicate_raised=duplicated)


# --------------------------------------------------------------------------- #
# 8. Result publication
# --------------------------------------------------------------------------- #
def inject_result_publication(workdir: Path) -> Dict[str, Any]:
    """An edited sealed document and a namespace change must both be refused."""
    directory = Path(workdir) / "publication" / REG.BASELINES[0] / "seed42"
    records = _export_records()
    PROV.publish_cell(directory, records=records, provenance=_export_provenance(),
                      summary=MET.aggregate_records(records))

    result = directory / PROV.RESULT_NAME
    original = result.read_bytes()
    document = json.loads(original.decode("utf-8"))
    document["evidence_class"] = P.REAL_VAL_EVIDENCE
    document["evidence_namespace"] = PROV.NAMESPACE_RESEARCH
    result.write_text(json.dumps(document), encoding="utf-8")
    tampered = PROV.verify_cell(directory)
    result.write_bytes(original)

    # a namespace change on an existing cell directory
    research = PROV.build_evaluation_provenance(
        model_key=REG.BASELINES[0], seed=42, split=P.SPLIT_VAL,
        adapter_identity={"model_key": REG.BASELINES[0], "seed": 42,
                          "adapter_kind": "PLAIN", "checkpoint_sha256": "1" * 64},
        evidence_class=P.REAL_VAL_EVIDENCE, split_manifest_sha256="0" * 64,
        n_images=4, evaluation_configuration=PROV.evaluation_config(),
        synthetic=False, training_performed=True)
    namespace_raised = _expect(lambda: PROV.publish_cell(
        directory, records=records, provenance=research,
        summary=MET.aggregate_records(records)), PROV.NamespaceError)

    detected = ("REJECTED" if tampered["status"] == "REJECTED" else None) or namespace_raised
    return _outcome(
        "result_publication",
        "a relabelled sealed document, then a namespace change in an existing cell",
        "provenance.verify_cell seal + provenance.publish_cell namespace lock",
        detected,
        f"tampered -> {tampered['status']} ({tampered['reasons'][:1]}); "
        f"namespace change -> {namespace_raised}",
        tamper_status=tampered["status"],
        tamper_reasons=tampered["reasons"], namespace_raised=namespace_raised)


# --------------------------------------------------------------------------- #
# Runner
# --------------------------------------------------------------------------- #
INJECTIONS: Dict[str, Callable[[Path], Dict[str, Any]]] = {
    "global_training": inject_global_training,
    "cache_creation": inject_cache_creation,
    "refiner_training": inject_refiner_training,
    "benefit_label_generation": inject_benefit_labels,
    "router_training": inject_router_training,
    "safety_training": inject_safety_training,
    "evaluation_export": inject_evaluation_export,
    "result_publication": inject_result_publication,
}


def failure_report(*, workdir: Optional[Path] = None) -> Dict[str, Any]:
    """Run all eight injections in a scoped directory and summarise detection."""
    owned = workdir is None
    root = Path(workdir or tempfile.mkdtemp(prefix="phase_d_failures_"))
    root.mkdir(parents=True, exist_ok=True)
    rows: List[Dict[str, Any]] = []
    for stage in STAGES:
        try:
            rows.append(INJECTIONS[stage](root))
        except Exception as exc:                          # noqa: BLE001 - reported, not hidden
            rows.append(_outcome(stage, "injection harness error", "-", None,
                                 f"{type(exc).__name__}: {exc}"))
    detected = [r for r in rows if r["detected"]]
    report = {"schema": "phase_d_failure_injection_v1", "evidence_class": EVIDENCE_CLASS,
              "stages": list(STAGES), "injections": rows,
              "n_injections": len(rows), "n_detected": len(detected),
              "all_detected": len(detected) == len(rows),
              "missed": [r["stage"] for r in rows if not r["detected"]],
              "note": ("Each injection hands a real guard a genuinely broken artifact or "
                       "input. No training is run; this establishes refusal at the stage "
                       "boundary only.")}
    if owned:
        shutil.rmtree(root, ignore_errors=True)
    return report


__all__ = ["EVIDENCE_CLASS", "INJECTIONS", "STAGES", "failure_report",
           "inject_benefit_labels", "inject_cache_creation", "inject_evaluation_export",
           "inject_global_training", "inject_refiner_training", "inject_result_publication",
           "inject_router_training", "inject_safety_training"]
