"""Optional strict backbone-out-of-fold construction -- versioned, NOT primary.

Why this module exists
----------------------
The primary Lite (and FULL) label construction is *matched* to the frozen
Phase-25D/25F artefacts: the refiner, router and safety modules are genuinely
cross-fitted, but the backbone is trained once on all of TRAIN -- which contains
every labelling sample.  That is disclosed in
:func:`src.research.lite_pipeline.stages.label_lite.lite_oof_contract`, and it is
**not** repaired, because repairing it would make Lite labels incomparable with
the historical FULL labels.

A reviewer can legitimately ask for the stronger construction anyway: retrain the
backbone per outer fold on the complement of that fold, so that no labelling
sample was ever seen by *any* component.  This module implements the parts of
that construction which can be built and tested without running a real
experiment:

* a **reusable fold-aware interface** (:class:`StrictFoldRecord`) that names, for
  each outer fold, exactly which sample ids the backbone may train on and which
  are reserved for label generation;
* **target-fold exclusion validation** that fails closed if the two sets touch --
  which is the single failure mode that would silently invalidate the whole
  construction;
* **checkpoint provenance** requirements so a backbone checkpoint can prove which
  fold's complement produced it, rather than being trusted by filename;
* an explicit contract declaring this construction is *not* the primary one and
  *must not* silently replace it.

What is deliberately NOT here
-----------------------------
No strict-OOF model is trained, no strict-OOF metric is produced, and no code path
in the primary pipeline can reach this module.  Enabling it for real requires
``3 x len(SEEDS)`` additional backbone trainings and a separate evaluation, which
is a future phase, not this one.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Dict, Iterable, Mapping, Optional, Tuple

from src.research.full_pipeline import recipe as R
from src.research.full_pipeline.population import (PopulationSpec, resolve_folds)

from . import recipe as L

__all__ = [
    "STRICT_OOF_PROTOCOL_VERSION",
    "StrictOOFError",
    "StrictFoldRecord",
    "backbone_fit_sha256",
    "build_strict_folds",
    "validate_target_exclusion",
    "assert_strict_checkpoint_provenance",
    "strict_oof_contract",
    "future_requirement",
]

#: A different version string from the primary construction
#: (``R.EXPERIMENTAL_PROTOCOL_VERSION``) so the two can never be conflated in a
#: manifest, a table or a sentence.
STRICT_OOF_PROTOCOL_VERSION = "ra_medfilm_barr_lite_strict_backbone_oof_v1"

#: Keys a strict-OOF backbone checkpoint must carry.
PROVENANCE_KEYS = ("strict_oof_protocol_version", "strict_oof_fold",
                   "strict_oof_backbone_fit_sha256")


class StrictOOFError(RuntimeError):
    """Raised when a strict-OOF fold assignment would leak the target fold."""


def backbone_fit_sha256(sample_ids: Iterable[str]) -> str:
    """Stable digest of a backbone training population (order-independent)."""
    ids = sorted({str(s) for s in sample_ids})
    return hashlib.sha256("\n".join(ids).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class StrictFoldRecord:
    """One outer fold of the strict construction.

    ``backbone_fit`` is the ONLY population the fold's backbone may train on.
    ``refiner_fit`` / ``refiner_early_stop`` must be subsets of it, because the
    refiner's input is the backbone's output.  ``target`` is reserved exclusively
    for label generation and must be disjoint from all three.
    """

    fold: int
    target: Tuple[str, ...]
    backbone_fit: Tuple[str, ...]
    refiner_fit: Tuple[str, ...]
    refiner_early_stop: Tuple[str, ...]
    backbone_checkpoint_sha256: Optional[str] = None

    def __post_init__(self) -> None:
        if int(self.fold) < 0:
            raise StrictOOFError(f"fold index must be non-negative, got {self.fold}")
        for name in ("target", "backbone_fit", "refiner_fit", "refiner_early_stop"):
            ids = getattr(self, name)
            if len(set(ids)) != len(ids):
                raise StrictOOFError(f"fold {self.fold}: duplicate ids in {name}")
            if not ids:
                raise StrictOOFError(f"fold {self.fold}: {name} is empty")
        validate_target_exclusion(self)

    @property
    def backbone_fit_sha256(self) -> str:
        return backbone_fit_sha256(self.backbone_fit)

    def as_dict(self) -> dict:
        return {
            "fold": int(self.fold),
            "n_target": len(self.target),
            "n_backbone_fit": len(self.backbone_fit),
            "n_refiner_fit": len(self.refiner_fit),
            "n_refiner_early_stop": len(self.refiner_early_stop),
            "backbone_fit_sha256": self.backbone_fit_sha256,
            "backbone_checkpoint_sha256": self.backbone_checkpoint_sha256,
            "target_disjoint_from_backbone_fit": True,
        }


def validate_target_exclusion(record: StrictFoldRecord) -> dict:
    """Fail closed unless the target fold is excluded from every training role.

    Four independent things can go wrong, and each is checked separately so the
    error message names the actual defect:

    1. the target overlaps the backbone training population (the defining leak);
    2. the refiner trains on something the backbone never saw (impossible input);
    3. the refiner fit and early-stop sets overlap;
    4. the refiner or its early-stop set touches the target.
    """
    target = set(record.target)
    backbone = set(record.backbone_fit)
    refit = set(record.refiner_fit)
    res = set(record.refiner_early_stop)

    overlap = target & backbone
    if overlap:
        raise StrictOOFError(
            f"fold {record.fold}: {len(overlap)} target ids are in the backbone "
            f"training population -- the strict construction is void")
    if not refit <= backbone or not res <= backbone:
        raise StrictOOFError(
            f"fold {record.fold}: refiner populations must be subsets of "
            f"backbone_fit ({len(refit - backbone)} fit and {len(res - backbone)} "
            f"early-stop ids lie outside it)")
    if refit & res:
        raise StrictOOFError(
            f"fold {record.fold}: refiner fit and early_stop overlap by {len(refit & res)}")
    for name, ids in (("refiner_fit", refit), ("refiner_early_stop", res)):
        if ids & target:
            raise StrictOOFError(
                f"fold {record.fold}: {name} touches {len(ids & target)} target ids")

    return {
        "fold": int(record.fold),
        "target_disjoint_from_backbone_fit": True,
        "refiner_populations_inside_backbone_fit": True,
        "refiner_roles_disjoint": True,
        "target_absent_from_refiner_roles": True,
        "verdict": "STRICT_TARGET_EXCLUSION_PASS",
    }


def build_strict_folds(spec: PopulationSpec, *, n_outer: int = len(R.R_OUTER_FOLDS),
                       seed: int = 42, allow_derived: bool = False,
                       kind: str = "outer3") -> Dict[int, StrictFoldRecord]:
    """Derive the strict fold assignment from the canonical partition.

    The partition itself is **not** invented here: it is the same outer partition
    the primary construction uses (frozen Phase-25A for a canonical population,
    deterministic derivation for a synthetic one).  Only the *roles* are
    re-labelled -- what the primary construction calls the training portion
    becomes the backbone's exclusive training population.

    Reusing the partition is deliberate: a strict-OOF result computed on a
    different partition would not be comparable with the primary one, and the
    comparison is the only reason to build it.
    """
    table = resolve_folds(spec, kind=kind, seed=seed, allow_derived=allow_derived)
    if len(table.folds) != n_outer:
        raise StrictOOFError(
            f"expected {n_outer} outer folds, the {kind} table has {len(table.folds)}")

    population = set(spec.development_ids)
    records: Dict[int, StrictFoldRecord] = {}
    for k, roles in table.folds.items():
        target = tuple(sorted(str(s) for s in roles["outer_target"]))
        backbone_fit = tuple(sorted({str(s) for s in roles["fit"]}
                                    | {str(s) for s in roles["early_stop"]}))
        if set(target) | set(backbone_fit) != population:
            raise StrictOOFError(
                f"fold {k}: target + backbone_fit does not cover the label population "
                f"({len(set(target) | set(backbone_fit))} of {len(population)})")
        records[int(k)] = StrictFoldRecord(
            fold=int(k), target=target, backbone_fit=backbone_fit,
            refiner_fit=tuple(sorted(str(s) for s in roles["fit"])),
            refiner_early_stop=tuple(sorted(str(s) for s in roles["early_stop"])),
        )

    covered = [sid for r in records.values() for sid in r.target]
    if len(covered) != len(set(covered)):
        raise StrictOOFError("strict outer targets are not mutually disjoint")
    if set(covered) != population:
        raise StrictOOFError(
            f"strict outer targets cover {len(set(covered))} ids, population has "
            f"{len(population)}")
    return records


def assert_strict_checkpoint_provenance(ckpt: Mapping[str, object],
                                        record: StrictFoldRecord) -> dict:
    """Require a backbone checkpoint to prove which fold's complement produced it.

    Trusting a filename or a directory name is exactly how a strict-OOF claim
    would silently become a primary-construction claim.  The checkpoint must
    therefore carry the protocol version, the fold index and a digest of the exact
    training population.
    """
    missing = [key for key in PROVENANCE_KEYS if key not in ckpt]
    if missing:
        raise StrictOOFError(
            f"backbone checkpoint lacks strict-OOF provenance {missing}; it cannot "
            "be used in a strict construction")
    if ckpt.get("strict_oof_protocol_version") != STRICT_OOF_PROTOCOL_VERSION:
        raise StrictOOFError(
            f"backbone checkpoint protocol {ckpt.get('strict_oof_protocol_version')!r} "
            f"!= {STRICT_OOF_PROTOCOL_VERSION!r}")
    if int(ckpt.get("strict_oof_fold", -1)) != int(record.fold):
        raise StrictOOFError(
            f"backbone checkpoint was trained for fold {ckpt.get('strict_oof_fold')}, "
            f"required for fold {record.fold}")
    if ckpt.get("strict_oof_backbone_fit_sha256") != record.backbone_fit_sha256:
        raise StrictOOFError(
            "backbone checkpoint training population digest does not match this fold; "
            "the checkpoint was trained on a different population")
    return {
        "fold": int(record.fold),
        "protocol_version": STRICT_OOF_PROTOCOL_VERSION,
        "backbone_fit_sha256": record.backbone_fit_sha256,
        "verdict": "STRICT_CHECKPOINT_PROVENANCE_PASS",
    }


def strict_oof_contract() -> dict:
    """Machine-readable declaration of what this construction is and is not."""
    return {
        "protocol_version": STRICT_OOF_PROTOCOL_VERSION,
        "primary_construction_protocol_version": R.EXPERIMENTAL_PROTOCOL_VERSION,
        "is_primary_construction": False,
        "replaces_primary_construction": False,
        "must_not_silently_replace_primary": True,
        "optional": True,
        "implementation_status": "INTERFACE_AND_VALIDATION_IMPLEMENTED__NOT_EXECUTED",
        "backbone_out_of_fold": True,
        "refiner_out_of_fold": True,
        "router_out_of_fold": True,
        "safety_out_of_fold": True,
        "label_generation_population": "ROUTER_DEVELOPMENT",
        "backbone_training_population": "complement of the outer target within ROUTER_DEVELOPMENT",
        "backbone_training_population_excludes_validation": True,
        "partition_reused_from_primary": True,
        "partition_reuse_reason": (
            "a strict result computed on a different partition would not be comparable "
            "with the primary result, which is the only reason to compute it"),
        "real_training_performed": False,
        "strict_oof_metric_available": False,
        "cannot_be_claimed": (
            "no strict-OOF Dice, harm rate, router calibration or safety acceptance "
            "rate exists; this module produces no performance number"),
    }


def future_requirement() -> dict:
    """The exact work needed to make the strict construction executable."""
    return {
        "protocol_version": STRICT_OOF_PROTOCOL_VERSION,
        "additional_backbone_trainings": len(R.R_OUTER_FOLDS) * len(L.LITE_SEEDS),
        "per_fold_steps": [
            "train G_Lite on StrictFoldRecord.backbone_fit only",
            "stamp strict_oof_protocol_version / strict_oof_fold / "
            "strict_oof_backbone_fit_sha256 into the checkpoint envelope",
            "rebuild the crop cache and the 202-D features from that fold's backbone",
            "train R_Lite on refiner_fit with refiner_early_stop, predict target",
            "derive delta_dice labels on target only",
            "cross-fit B_phi and S_omega on those labels",
        ],
        "blocking_requirements": [
            "an operator grant covering the additional backbone trainings",
            "a separate evaluation contract; the primary VAL808 evaluation is not reusable",
            "a distinct result namespace so strict and primary numbers cannot be pooled",
        ],
        "verification_available_now": [
            "build_strict_folds() on the frozen partition",
            "validate_target_exclusion() on any proposed assignment",
            "assert_strict_checkpoint_provenance() on any proposed checkpoint",
        ],
        "not_required_for_phase_b": True,
    }
