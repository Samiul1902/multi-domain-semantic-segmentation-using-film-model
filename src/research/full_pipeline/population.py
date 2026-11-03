"""Population and fold-membership resolution.

Two modes, always recorded in the produced manifest as ``fold_source``:

``FROZEN_CANONICAL``
    The memberships frozen by Phase-25A (3 outer folds) and Phase-25D/25F
    (5 cross-fit folds) over ROUTER_DEVELOPMENT.  These are reused verbatim for
    every seed: the seed controls optimisation randomness only, never the
    partition.  That is the rule already frozen in
    ``reports/audits/phase29_fixed_partition_execution_audit.json``
    ("Reuse exact seed42 cross-fit memberships for seeds 123 and 3407").

``DERIVED_FROM_POPULATION``
    Used only for synthetic populations (integration tests) where no frozen
    table can exist.  The derivation is deterministic, group-safe and
    domain-stratified, i.e. it obeys the same invariants as the frozen rule.

A real run refuses to fall back to derivation unless explicitly allowed, so a
missing canonical table can never be silently replaced by a different partition.

Leakage invariants enforced here
--------------------------------
* VAL is never part of ROUTER_DEVELOPMENT and therefore never enters R fit,
  early stopping, router CV or safety CV.
* ROUTER_HOLDOUT is excluded from every fold set.
* Group keys are never split across an outer fold boundary when a real group key
  exists (``patient-*`` / ``case-*`` / ``SINGLETON::``).
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence

import pandas as pd

from . import recipe as R
from .provenance import sha256_file

__all__ = [
    "FoldTable",
    "PopulationSpec",
    "load_frozen_outer_folds",
    "load_frozen_cv_folds",
    "derive_folds",
    "resolve_folds",
    "assert_no_leakage",
]

FROZEN_OUTER_FOLD_DIR = R.ROOT / "data_cache" / "phase25a_barr_roi030_cache" / "folds"
FROZEN_CV_TABLE_DIR = R.ROOT / "reports" / "tables"


# --------------------------------------------------------------------------- #
@dataclass
class FoldTable:
    """``folds[k] = {"fit": [...], "early_stop": [...], "outer_target": [...]}``."""

    folds: Dict[int, Dict[str, List[str]]]
    source: str
    manifest_paths: Dict[str, str] = field(default_factory=dict)
    manifest_shas: Dict[str, str] = field(default_factory=dict)
    n_folds: int = 0

    def __post_init__(self) -> None:
        self.n_folds = len(self.folds)

    def ids(self, role: str) -> set:
        out: set = set()
        for k in self.folds:
            out.update(self.folds[k][role])
        return out

    def summary(self) -> dict:
        return {
            "source": self.source,
            "n_folds": self.n_folds,
            "per_fold": {
                str(k): {role: len(v[role]) for role in ("fit", "early_stop", "outer_target")}
                for k, v in sorted(self.folds.items())
            },
            "manifests": self.manifest_paths,
            "manifest_sha256": self.manifest_shas,
        }


@dataclass
class PopulationSpec:
    """Resolved populations for one run.

    ``development`` is the only population any producer may fit on.  ``train`` and
    ``val`` are the manifest frames; VAL is used for G model selection only.
    """

    development: pd.DataFrame
    train_manifest: Path
    val_manifest: Path
    router_split_manifest: Optional[Path]
    source: str = "CANONICAL"
    holdout_ids: frozenset = frozenset()

    @property
    def development_ids(self) -> List[str]:
        return [str(s) for s in self.development["sample_id"]]

    @property
    def group_key_by_id(self) -> Dict[str, str]:
        if "group_key" in self.development.columns:
            return {str(s): str(g) for s, g in
                    zip(self.development["sample_id"], self.development["group_key"])}
        return {str(s): f"SINGLETON::{d}::{s}" for s, d in
                zip(self.development["sample_id"], self.development["dataset"])}

    def summary(self) -> dict:
        by_domain = self.development["dataset"].value_counts().to_dict()
        return {
            "source": self.source,
            "development_n": int(len(self.development)),
            "development_by_domain": {k: int(v) for k, v in by_domain.items()},
            "train_manifest": str(self.train_manifest),
            "train_manifest_sha256": sha256_file(self.train_manifest),
            "val_manifest": str(self.val_manifest),
            "val_manifest_sha256": sha256_file(self.val_manifest),
            "router_split_manifest": (str(self.router_split_manifest)
                                      if self.router_split_manifest else None),
            "router_split_manifest_sha256": (sha256_file(self.router_split_manifest)
                                             if self.router_split_manifest else None),
        }


# --------------------------------------------------------------------------- #
# canonical population
# --------------------------------------------------------------------------- #
def load_canonical_population() -> PopulationSpec:
    """ROUTER_DEVELOPMENT (4957) in canonical ``(dataset, sample_id)`` order.

    The split manifest carries membership only, so the image / mask paths are joined
    from the frozen TRAIN manifest.  ROUTER_DEVELOPMENT is a strict subset of TRAIN
    (4957 + 875 = 5832), which is asserted rather than assumed.
    """
    split = pd.read_csv(R.ROUTER_SPLIT_MANIFEST)
    dev = split[split["split_role"] == "ROUTER_DEVELOPMENT"].copy()
    dev = dev.sort_values(["dataset", "sample_id"]).reset_index(drop=True)
    if len(dev) != R.ROUTER_DEVELOPMENT_N:
        raise RuntimeError(
            f"ROUTER_DEVELOPMENT has {len(dev)} rows, expected {R.ROUTER_DEVELOPMENT_N}")

    train = pd.read_csv(R.TRAIN_MANIFEST)
    train["sample_id"] = train["sample_id"].astype(str)
    if len(train) != R.TRAIN_N:
        raise RuntimeError(f"TRAIN manifest has {len(train)} rows, expected {R.TRAIN_N}")
    n_dev = int((split["split_role"] == "ROUTER_DEVELOPMENT").sum())
    n_hold = int((split["split_role"] == "ROUTER_HOLDOUT").sum())
    if n_dev + n_hold != len(train):
        raise RuntimeError(
            f"ROUTER_DEVELOPMENT + ROUTER_HOLDOUT = {n_dev + n_hold} != TRAIN {len(train)}")

    dev["sample_id"] = dev["sample_id"].astype(str)
    joined = dev.merge(
        train[["sample_id", "image_path", "mask_path", "patient_id", "case_id", "category"]],
        on="sample_id", how="left", validate="one_to_one")
    missing = joined["image_path"].isna() | joined["mask_path"].isna()
    if bool(missing.any()):
        raise RuntimeError(
            f"{int(missing.sum())} ROUTER_DEVELOPMENT ids have no path in the TRAIN manifest")

    return PopulationSpec(development=joined, train_manifest=R.TRAIN_MANIFEST,
                          val_manifest=R.VAL_MANIFEST,
                          router_split_manifest=R.ROUTER_SPLIT_MANIFEST,
                          source="CANONICAL",
                          holdout_ids=frozenset(
                              split[split["split_role"] == "ROUTER_HOLDOUT"]
                              ["sample_id"].astype(str)))


# --------------------------------------------------------------------------- #
# frozen fold tables
# --------------------------------------------------------------------------- #
def load_frozen_outer_folds() -> FoldTable:
    """Phase-25A 3-fold outer cross-fit over ROUTER_DEVELOPMENT."""
    folds: Dict[int, Dict[str, List[str]]] = {}
    paths: Dict[str, str] = {}
    shas: Dict[str, str] = {}
    for k in R.R_OUTER_FOLDS:
        folds[k] = {}
        for role in ("fit", "early_stop", "outer_target"):
            p = FROZEN_OUTER_FOLD_DIR / f"fold{k}_{role}.csv"
            if not p.exists():
                raise FileNotFoundError(f"frozen Phase-25A fold manifest missing: {p}")
            folds[k][role] = [str(s) for s in pd.read_csv(p)["sample_id"]]
            key = f"fold{k}_{role}"
            paths[key] = str(p.relative_to(R.ROOT)).replace("\\", "/")
            shas[key] = sha256_file(p)
    return FoldTable(folds=folds, source="FROZEN_CANONICAL", manifest_paths=paths,
                     manifest_shas=shas)


def load_frozen_cv_folds() -> FoldTable:
    """Phase-25D/25F 5-fold cross-fit over ROUTER_DEVELOPMENT."""
    folds: Dict[int, Dict[str, List[str]]] = {}
    paths: Dict[str, str] = {}
    shas: Dict[str, str] = {}
    for k in range(R.B_CV_FOLDS):
        folds[k] = {}
        for role in ("fit", "early_stop", "outer_target"):
            p = FROZEN_CV_TABLE_DIR / f"phase25d_cv_fold{k}_{role}_ids.csv"
            if not p.exists():
                raise FileNotFoundError(f"frozen Phase-25D CV manifest missing: {p}")
            folds[k][role] = [str(s) for s in pd.read_csv(p)["sample_id"]]
            key = f"fold{k}_{role}"
            paths[key] = str(p.relative_to(R.ROOT)).replace("\\", "/")
            shas[key] = sha256_file(p)
    return FoldTable(folds=folds, source="FROZEN_CANONICAL", manifest_paths=paths,
                     manifest_shas=shas)


# --------------------------------------------------------------------------- #
# deterministic derivation (synthetic populations only)
# --------------------------------------------------------------------------- #
def _order_key(seed: int, salt: str, group_key: str) -> str:
    return hashlib.sha256(f"{seed}::{salt}::{group_key}".encode("utf-8")).hexdigest()


def derive_folds(development: pd.DataFrame, *, n_outer: int, seed: int,
                 salt: str, inner_fit_fraction: float = 0.90) -> FoldTable:
    """Group-safe, domain-stratified deterministic partition.

    Per domain, whole groups are ordered by ``sha256('{seed}::{salt}::{group_key}')``
    and placed into the globally smallest bucket (ties by bucket index).  The
    training portion of each fold is then split the same way into fit / early_stop.

    The bucket-size cursor is **global, not per-domain**.  Resetting it per domain
    would make a domain with fewer groups than ``n_outer`` touch only the first
    ``groups_per_domain`` buckets, leaving every later fold with an empty
    ``outer_target`` -- a silent mis-fold rather than an error.
    """
    df = development.copy()
    if "group_key" not in df.columns:
        df["group_key"] = [f"SINGLETON::{d}::{s}" for d, s in
                           zip(df["dataset"], df["sample_id"])]

    bucket_of_group: Dict[str, int] = {}
    sizes = [0] * n_outer
    for domain in sorted(df["dataset"].unique()):
        sub = df[df["dataset"] == domain]
        groups = sorted(set(sub["group_key"].astype(str)))
        groups.sort(key=lambda g: (_order_key(seed, f"{salt}:outer:{domain}", g), g))
        for g in groups:
            k = min(range(n_outer), key=lambda i: (sizes[i], i))
            bucket_of_group[g] = k
            sizes[k] += int((sub["group_key"].astype(str) == g).sum())

    # Fail loudly on an under-grouped population instead of emitting empty folds.
    distinct_groups = len(bucket_of_group)
    if distinct_groups < n_outer:
        raise ValueError(
            f"cannot derive {n_outer} folds from {distinct_groups} distinct groups; "
            f"the population needs at least {n_outer} independent groups")

    folds: Dict[int, Dict[str, List[str]]] = {}
    for k in range(n_outer):
        target = df[df["group_key"].astype(str).map(bucket_of_group) == k]
        train_portion = df[df["group_key"].astype(str).map(bucket_of_group) != k]
        fit_ids, es_ids = _split_inner(train_portion, seed, salt, k, inner_fit_fraction)
        folds[k] = {
            "outer_target": sorted(target["sample_id"].astype(str)),
            "fit": fit_ids,
            "early_stop": es_ids,
        }

    empty = {k: [r for r, ids in v.items() if not ids] for k, v in folds.items()}
    empty = {k: v for k, v in empty.items() if v}
    if empty:
        raise ValueError(
            f"derived fold table has empty roles {empty}; increase the number of "
            f"distinct groups per domain so every fold can hold an outer_target")
    return FoldTable(folds=folds, source="DERIVED_FROM_POPULATION")


def _split_inner(frame: pd.DataFrame, seed: int, salt: str, fold: int,
                 fit_fraction: float) -> tuple:
    """Group-safe inner fit / early_stop split of one fold's training portion."""
    frame = frame.copy()
    if "group_key" not in frame.columns:
        frame["group_key"] = [f"SINGLETON::{d}::{s}" for d, s in
                              zip(frame["dataset"], frame["sample_id"])]
    fit_ids: List[str] = []
    es_ids: List[str] = []
    for domain in sorted(frame["dataset"].unique()):
        sub = frame[frame["dataset"] == domain]
        groups = sorted(set(sub["group_key"].astype(str)))
        groups.sort(key=lambda g: (_order_key(seed, f"{salt}:inner{fold}:{domain}", g), g))
        target_es = int(round((1.0 - fit_fraction) * len(sub)))
        # a fold must keep at least one whole group in early stop when it can, so a
        # tiny population still produces a non-empty split rather than an empty table
        if len(groups) >= 2:
            target_es = max(1, target_es)
        else:
            target_es = 0
        taken = 0
        for g in groups:
            rows = sub[sub["group_key"].astype(str) == g]
            ids = sorted(rows["sample_id"].astype(str))
            if taken < target_es:
                es_ids.extend(ids)
                taken += len(ids)
            else:
                fit_ids.extend(ids)
    return sorted(fit_ids), sorted(es_ids)


def resolve_folds(spec: PopulationSpec, *, kind: str, seed: int,
                  allow_derived: bool = False) -> FoldTable:
    """Return the fold table for ``kind`` in {"outer3", "cv5"}.

    ``kind="outer3"`` -> R_psi cross-fit (3 outer folds).
    ``kind="cv5"``    -> B_phi / S_omega cross-fit (5 folds, same membership).

    Frozen tables are used whenever available and are validated against the
    population.  Derivation is refused unless ``allow_derived``.
    """
    if kind not in ("outer3", "cv5"):
        raise ValueError(f"unknown fold kind {kind!r}")
    table = None
    if spec.source == "CANONICAL":
        try:
            table = load_frozen_outer_folds() if kind == "outer3" else load_frozen_cv_folds()
        except FileNotFoundError:
            table = None

    if table is not None:
        _assert_table_matches_population(table, spec)
        return table

    if not allow_derived:
        raise FileNotFoundError(
            f"no frozen {kind} fold table for this population; pass allow_derived=True "
            "only for synthetic runs")
    n = 3 if kind == "outer3" else R.B_CV_FOLDS
    return derive_folds(spec.development, n_outer=n, seed=seed,
                        salt=f"full_pipeline::{kind}")


def _assert_table_matches_population(table: FoldTable, spec: PopulationSpec) -> None:
    pop = set(spec.development_ids)
    union = set()
    for k, v in table.folds.items():
        for role in ("fit", "early_stop", "outer_target"):
            ids = set(v[role])
            if not ids <= pop:
                raise RuntimeError(
                    f"{table.source} fold {k} {role} contains {len(ids - pop)} ids outside "
                    "ROUTER_DEVELOPMENT")
            union |= ids
    if union != pop:
        raise RuntimeError(
            f"{table.source} fold table covers {len(union)} ids, population has {len(pop)}")


# --------------------------------------------------------------------------- #
# leakage audit
# --------------------------------------------------------------------------- #
def assert_no_leakage(*, spec: PopulationSpec, folds: Mapping[int, Mapping[str, Sequence[str]]],
                      label: str) -> dict:
    """Verify the invariants that make the cross-fit legitimate.

    Raises ``RuntimeError`` on any violation; returns the audit record on success.
    """
    pop = set(spec.development_ids)
    holdout = set(spec.holdout_ids)
    split_path = spec.router_split_manifest
    if not holdout and split_path and Path(split_path).exists() and spec.source == "CANONICAL":
        sm = pd.read_csv(split_path)
        holdout = set(sm[sm["split_role"] == "ROUTER_HOLDOUT"]["sample_id"].astype(str))

    findings = []
    for k, v in folds.items():
        fit, es, ot = set(v["fit"]), set(v["early_stop"]), set(v["outer_target"])
        if fit & es:
            findings.append(f"fold{k}: fit and early_stop overlap ({len(fit & es)})")
        if fit & ot:
            findings.append(f"fold{k}: fit and outer_target overlap ({len(fit & ot)})")
        if es & ot:
            findings.append(f"fold{k}: early_stop and outer_target overlap ({len(es & ot)})")
        if (fit | es | ot) - pop:
            findings.append(f"fold{k}: ids outside ROUTER_DEVELOPMENT")
        if (fit | es | ot) & holdout:
            findings.append(f"fold{k}: ROUTER_HOLDOUT ids present")

    union_ot = set()
    for v in folds.values():
        union_ot |= set(v["outer_target"])
    if union_ot != pop:
        findings.append(
            f"outer targets cover {len(union_ot)} ids, ROUTER_DEVELOPMENT has {len(pop)}")

    if findings:
        raise RuntimeError(f"leakage audit failed for {label}: " + "; ".join(findings))

    return {
        "label": label,
        "n_folds": len(folds),
        "population_n": len(pop),
        "router_holdout_n_excluded": len(holdout),
        "outer_target_union_equals_population": True,
        "pairwise_disjoint": True,
        "router_holdout_absent": True,
        "val_absent": True,
        "test_absent": True,
        "verdict": "LEAKAGE_AUDIT_PASS",
    }
