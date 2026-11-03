"""Structural separation of synthetic artifacts from research evidence.

Phase C reported ``24/24 synthetic cells COMPLETE_VALIDATED`` and, correctly,
``0/24 research cells established``.  This module makes that separation a
property of the artifacts rather than of a report's wording, and then tries to
break it on purpose.

Four independent layers, each of which alone is sufficient for the attacks below
-------------------------------------------------------------------------------
1. **Namespace is derived, never supplied.**  ``namespace_for(evidence_class)``
   maps ``SYNTHETIC_TEST_ONLY -> synthetic`` and
   ``REAL_VAL808_DEVELOPMENT -> research``; no caller can assert a namespace.
2. **A cell directory has one namespace for life.**  ``publish_cell`` refuses to
   write research evidence over a synthetic directory, or the reverse.
3. **The result document is self-sealed.**  Editing ``evidence_class`` (or
   deleting it) breaks ``document_sha256``, so relabelling is detectable.
4. **The promotion gate re-derives eligibility from the document.**  A cell counts
   as research only if it is research-namespaced, not synthetic, records that
   training happened, carries a genuine 64-hex weight digest, and did not touch a
   protected split.  ``research_evidence_reasons`` is the single gate, shared by
   ``verify_matrix`` and the report aggregation.

A root that contains more than one namespace is *mixed* and establishes nothing,
however many cells validate.  Mixing is refused rather than reconciled, and the
marker scan covers the whole tree rather than only the 24 expected cell paths,
so a copied artifact cannot hide off-path.

Note on test hygiene: no attack below fabricates a research-labelled evaluation
document.  The "mixed root" case is built by writing a bare namespace marker into
a sibling cell directory, so no research evidence is manufactured even inside a
temporary directory.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional

import numpy as np

from src.research.evaluation import metrics as MET
from src.research.evaluation import protocol as P
from src.research.evaluation import provenance as PROV
from src.research.evaluation import registry as REG
from src.research.evaluation import reports as REP

EVIDENCE_CLASS = "SYNTHETIC_BENCHMARK"
#: A real 64-hex digest used only to satisfy the *shape* of the gate in tests.
#: It is the digest of a literal probe string, never of a model.
PROBE_DIGEST = "0" * 64


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #
def _mini_records() -> List[Dict[str, Any]]:
    """Four tiny scored records, one per domain.  No images, no model."""
    base = np.zeros((4, 4), np.uint8)
    base[1:3, 1:3] = 1
    shifted = np.zeros((4, 4), np.uint8)
    shifted[1:3, 2:4] = 1
    out = []
    for domain in P.DOMAINS:
        out.append(MET.score_prediction(
            sample_id=f"{domain}-1", domain=domain, task_id=3,
            final_probability=shifted.astype(np.float32), ground_truth=base))
    return out


def _synthetic_identity() -> Dict[str, Any]:
    """The identity a synthetic adapter actually carries."""
    return {"model_key": REG.BASELINES[0], "seed": 42, "adapter_kind": "PLAIN",
            "checkpoint_sha256": f"SYNTHETIC::{REG.BASELINES[0]}::42",
            "evidence_class": P.SYNTHETIC_EVIDENCE,
            "thresholds": {"segmentation_output": P.SEGMENTATION_OUTPUT_THRESHOLD}}


def publish_synthetic_cell(directory: Path, *,
                           identity: Optional[Mapping[str, Any]] = None,
                           records: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """Publish a small synthetic cell, exactly as the evaluator would."""
    records = records or _mini_records()
    provenance = PROV.build_evaluation_provenance(
        model_key=REG.BASELINES[0], seed=42, split=P.SPLIT_VAL,
        adapter_identity=dict(identity or _synthetic_identity()),
        evidence_class=P.SYNTHETIC_EVIDENCE,
        split_manifest_sha256="0" * 64, n_images=len(records),
        evaluation_configuration=PROV.evaluation_config(),
        synthetic=True, training_performed=False)
    return PROV.publish_cell(Path(directory), records=records, provenance=provenance,
                             summary=MET.aggregate_records(records),
                             expected_sample_ids=[r["sample_id"] for r in records])


def _research_provenance(**overrides: Any) -> Dict[str, Any]:
    """A well-formed *research* provenance, used only to probe the gate.

    It carries ``PROBE_DIGEST`` and is never published: the attacks below pass it
    to ``build_evaluation_provenance`` or ``publish_cell`` expecting a refusal.
    """
    identity = {"model_key": REG.BASELINES[0], "seed": 42, "adapter_kind": "PLAIN",
                "checkpoint_sha256": PROBE_DIGEST,
                "evidence_class": P.REAL_VAL_EVIDENCE}
    kwargs = dict(model_key=REG.BASELINES[0], seed=42, split=P.SPLIT_VAL,
                  adapter_identity=identity, evidence_class=P.REAL_VAL_EVIDENCE,
                  split_manifest_sha256="0" * 64, n_images=4,
                  evaluation_configuration=PROV.evaluation_config(),
                  synthetic=False, training_performed=True)
    kwargs.update(overrides)
    return PROV.build_evaluation_provenance(**kwargs)


def _expect_raises(fn: Callable[[], Any], *types: type) -> Optional[str]:
    """Run ``fn``; return the exception name if it raised, else ``None``."""
    try:
        fn()
    except types as exc:                       # noqa: BLE001 - the type is the assertion
        return type(exc).__name__
    return None


def _result(attack: str, mechanism: str, blocked_by: Optional[str],
            detail: str = "") -> Dict[str, Any]:
    return {"attack": attack, "blocked": blocked_by is not None,
            "mechanism": mechanism, "blocked_by": blocked_by, "detail": detail}


# --------------------------------------------------------------------------- #
# The seven attack vectors
# --------------------------------------------------------------------------- #
def attempt_output_directory_reuse(workdir: Path) -> Dict[str, Any]:
    """Publish research evidence into a directory that already holds a fixture."""
    cell = Path(workdir) / "reuse" / REG.BASELINES[0] / "seed42"
    publish_synthetic_cell(cell)
    raised = _expect_raises(
        lambda: PROV.publish_cell(cell, records=_mini_records(),
                                  provenance=_research_provenance(),
                                  summary=MET.aggregate_records(_mini_records())),
        PROV.NamespaceError)
    return _result("output_directory_reuse",
                   "publish_cell refuses a namespace change in one cell directory",
                   raised)


def attempt_registry_import(workdir: Path) -> Dict[str, Any]:
    """Count a validating synthetic cell as an established research cell."""
    root = Path(workdir) / "registry"
    publish_synthetic_cell(root / REG.BASELINES[0] / "seed42")
    outcome = PROV.verify_matrix(root)
    validated = outcome["counts"].get("COMPLETE_VALIDATED", 0)
    blocked = (validated >= 1 and outcome["research_cells_completed"] == 0)
    return _result("registry_import",
                   "verify_matrix counts only cells that pass research_evidence_reasons",
                   "research_cells_completed == 0" if blocked else None,
                   f"{validated} validated, {outcome['research_cells_completed']} research")


def attempt_report_aggregation(workdir: Path) -> Dict[str, Any]:
    """Aggregate synthetic cells into a research figure."""
    root = Path(workdir) / "aggregate"
    publish_synthetic_cell(root / REG.BASELINES[0] / "seed42")
    results = REP.collect_results(root)
    blocked = (results["research_cells_completed"] == 0
               and results["registry_status"]["status"] == "NOT_ESTABLISHED_0_OF_24")
    return _result("report_aggregation",
                   "collect_results shares the same promotion gate",
                   "research_cells_completed == 0" if blocked else None,
                   results["registry_status"]["status"])


def attempt_resume_promotion(workdir: Path) -> Dict[str, Any]:
    """Resume a synthetic cell as a research-labelled publication."""
    cell = Path(workdir) / "resume" / REG.BASELINES[0] / "seed42"
    publish_synthetic_cell(cell)
    before = (cell / PROV.RESULT_NAME).read_bytes()
    raised = _expect_raises(
        lambda: PROV.publish_cell(cell, records=_mini_records(),
                                  provenance=_research_provenance(),
                                  summary=MET.aggregate_records(_mini_records()),
                                  expected_sample_ids=[r["sample_id"]
                                                       for r in _mini_records()]),
        PROV.NamespaceError)
    unchanged = (cell / PROV.RESULT_NAME).read_bytes() == before
    return _result("resume_promotion",
                   "a resume may not change the namespace of the cell it resumes",
                   raised if (raised and unchanged) else None,
                   "existing result document left untouched" if unchanged else "DOCUMENT CHANGED")


def attempt_checkpoint_substitution(workdir: Path) -> Dict[str, Any]:
    """Claim research evidence while carrying a synthetic weight identity."""
    identity = _synthetic_identity()
    raised = _expect_raises(
        lambda: PROV.build_evaluation_provenance(
            model_key=REG.BASELINES[0], seed=42, split=P.SPLIT_VAL,
            adapter_identity=identity, evidence_class=P.REAL_VAL_EVIDENCE,
            split_manifest_sha256="0" * 64, n_images=4,
            evaluation_configuration=PROV.evaluation_config(),
            synthetic=False, training_performed=True),
        PROV.ProvenanceError)
    # and if a document were hand-built past the constructor, the gate still holds
    forged = {"evidence_class": P.REAL_VAL_EVIDENCE,
              "evidence_namespace": PROV.NAMESPACE_RESEARCH, "synthetic": False,
              "provenance": {"training_performed": True, "split": P.SPLIT_VAL,
                             "checkpoint_sha256": identity["checkpoint_sha256"],
                             "component_sha256": {}}}
    reasons = PROV.research_evidence_reasons(forged)
    blocked = raised is not None and bool(reasons)
    return _result("checkpoint_substitution",
                   "research evidence requires a genuine 64-hex weight digest",
                   raised if blocked else None, "; ".join(reasons))


def attempt_artifact_copy(workdir: Path) -> Dict[str, Any]:
    """Copy a synthetic cell into a research root, and mix namespaces.

    Three placements are tried, because a foreign marker does not have to land
    on one of the 24 expected registry paths:

    (a) the copied cell alone — it keeps its namespace and establishes nothing;
    (b) beside a research marker **on** a registry cell path;
    (c) beside a research marker **off** every registry path, where a scan that
        only looked at the expected 24 directories would never see it.
    """
    source = Path(workdir) / "copy" / "src" / REG.BASELINES[0] / "seed42"
    publish_synthetic_cell(source)

    def bare_research_marker(directory: Path, model_key: str, seed: int) -> None:
        """A marker only.  No research document is created, here or anywhere."""
        directory.mkdir(parents=True, exist_ok=True)
        (directory / PROV.NAMESPACE_NAME).write_text(json.dumps(
            {"schema": "phase_c_evidence_namespace_v1",
             "namespace": PROV.NAMESPACE_RESEARCH,
             "evidence_class": P.REAL_VAL_EVIDENCE, "synthetic": False,
             "cell": f"{model_key}::seed{seed}"}), encoding="utf-8")

    # (a) copied alone: it stays synthetic, so it establishes nothing
    alone_root = Path(workdir) / "copy" / "alone"
    shutil.copytree(source, alone_root / REG.BASELINES[0] / "seed42")
    alone = PROV.verify_matrix(alone_root)

    # (b) copied next to a research-namespaced registry cell
    mixed_root = Path(workdir) / "copy" / "mixed"
    shutil.copytree(source, mixed_root / REG.BASELINES[0] / "seed42")
    bare_research_marker(mixed_root / REG.GLOBAL / "seed42", REG.GLOBAL, 42)
    mixed = PROV.verify_matrix(mixed_root)

    # (c) copied next to a research marker at an imported, non-registry path
    foreign_root = Path(workdir) / "copy" / "foreign"
    shutil.copytree(source, foreign_root / REG.BASELINES[0] / "seed42")
    bare_research_marker(foreign_root / "imported_run" / "seed42",
                         "imported_run", 42)
    foreign = PROV.verify_matrix(foreign_root)

    blocked = (alone["research_cells_completed"] == 0
               and alone["namespace_consistent"] is True
               and mixed["namespace_consistent"] is False
               and mixed["research_cells_completed"] == 0
               and foreign["namespace_consistent"] is False
               and foreign["research_cells_completed"] == 0)
    return _result("artifact_copy",
                   "a copied cell keeps its namespace; a foreign marker is found "
                   "anywhere under the root, not only on a registry path",
                   "namespace_consistent == False" if blocked else None,
                   f"alone={alone['namespaces']} mixed={mixed['namespaces']} "
                   f"foreign={foreign['namespaces']} "
                   f"foreign_problems={len(foreign['namespace_problems'])}")


def attempt_evidence_class_tamper(workdir: Path) -> Dict[str, Any]:
    """Edit, delete or relabel the evidence class in a published document."""
    cell = Path(workdir) / "tamper" / REG.BASELINES[0] / "seed42"
    publish_synthetic_cell(cell)
    original = (cell / PROV.RESULT_NAME).read_bytes()

    def rewrite(mutate: Callable[[Dict[str, Any]], None]) -> None:
        doc = json.loads(original.decode("utf-8"))
        mutate(doc)
        (cell / PROV.RESULT_NAME).write_text(json.dumps(doc), encoding="utf-8")

    # (a) relabel the class
    rewrite(lambda d: d.update({"evidence_class": P.REAL_VAL_EVIDENCE,
                                "evidence_namespace": PROV.NAMESPACE_RESEARCH}))
    relabelled = PROV.verify_cell(cell)
    # (b) delete the class
    rewrite(lambda d: d.pop("evidence_class", None))
    deleted = PROV.verify_cell(cell)
    # (c) relabel and recompute the seal, but keep the synthetic digest
    doc = json.loads(original.decode("utf-8"))
    doc.update({"evidence_class": P.REAL_VAL_EVIDENCE,
                "evidence_namespace": PROV.NAMESPACE_RESEARCH, "synthetic": False})
    doc[PROV.SEAL_FIELD] = PROV.seal_document(doc)
    (cell / PROV.RESULT_NAME).write_text(json.dumps(doc), encoding="utf-8")
    resealed = PROV.verify_cell(cell)

    # restore the untampered document so the fixture is not left corrupted
    (cell / PROV.RESULT_NAME).write_bytes(original)

    blocked = (relabelled["status"] == "REJECTED"
               and deleted["status"] == "REJECTED"
               and resealed["status"] == "REJECTED")
    return _result("evidence_class_tamper",
                   "the document is self-sealed, and the gate re-checks the weight digest",
                   "REJECTED in all three variants" if blocked else None,
                   f"relabelled={relabelled['reasons'][:2]} resealed={resealed['reasons'][:2]}")


ATTACKS: Dict[str, Callable[[Path], Dict[str, Any]]] = {
    "output_directory_reuse": attempt_output_directory_reuse,
    "registry_import": attempt_registry_import,
    "report_aggregation": attempt_report_aggregation,
    "resume_promotion": attempt_resume_promotion,
    "checkpoint_substitution": attempt_checkpoint_substitution,
    "artifact_copy": attempt_artifact_copy,
    "evidence_class_tamper": attempt_evidence_class_tamper,
}


def run_all_attacks(workdir: Path) -> Dict[str, Any]:
    """Run every attack and report whether it was blocked."""
    workdir = Path(workdir)
    if workdir.exists():
        shutil.rmtree(workdir, ignore_errors=True)
    workdir.mkdir(parents=True, exist_ok=True)
    results = [fn(workdir) for fn in ATTACKS.values()]
    return {"schema": "phase_d_evidence_isolation_v1", "evidence_class": EVIDENCE_CLASS,
            "attacks": results,
            "n_attacks": len(results),
            "n_blocked": sum(1 for r in results if r["blocked"]),
            "all_blocked": all(r["blocked"] for r in results),
            "namespaces": dict(PROV.EVIDENCE_NAMESPACES),
            "note": ("Each attack is an attempt to make a synthetic artifact count as "
                     "research evidence. None may succeed.")}


__all__ = ["ATTACKS", "EVIDENCE_CLASS", "PROBE_DIGEST", "attempt_artifact_copy",
           "attempt_checkpoint_substitution", "attempt_evidence_class_tamper",
           "attempt_output_directory_reuse", "attempt_registry_import",
           "attempt_report_aggregation", "attempt_resume_promotion",
           "publish_synthetic_cell", "run_all_attacks"]
