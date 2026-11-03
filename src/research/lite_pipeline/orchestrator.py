"""Lite stage dependency resolution, resumable execution and family verification.

The Lite DAG has the same six nodes and the same edges as the FULL DAG::

    G  ->  CACHE  ->  R  ->  L  ->  B  ->  S

Execution rules are inherited from the FULL orchestrator rather than reinvented:

* a stage is skipped only when it is COMPLETE **and** its recorded upstream
  digests still match the artifacts on disk;
* before a stage runs, every upstream checkpoint is re-opened and its schema,
  component, seed, **family** and SHA chain are re-asserted, so a FULL checkpoint
  can never be consumed by a Lite stage and a seed-42 Lite refiner can never be
  consumed by a seed-123 Lite router;
* real (non-synthetic) execution requires an operator grant.

Authorization
-------------
The Lite family does **not** introduce a new gate.  It reuses the existing
operator grant surface (``authorize_full_training(contract)``) and presents the
Lite contract to it.  No credential is minted here, no policy exception is
created, and no existing gate is bypassed or modified.
"""
from __future__ import annotations

import importlib
import time
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Sequence

from src.research.full_pipeline.context import RunContext, StageRecord
from src.research.full_pipeline.orchestrator import AuthorizationRequired
from src.research.full_pipeline.provenance import (FamilyCompatibilityError,
                                                   assert_compatible, load_checkpoint,
                                                   read_json, sha256_file, utc_now)

from . import recipe as L
from .stages import MODULES

STAGE_ORDER = ("G", "CACHE", "R", "L", "B", "S")
DEPENDENCIES: Dict[str, tuple] = {
    "G": (),
    "CACHE": ("G",),
    "R": ("CACHE",),
    "L": ("R", "CACHE"),
    "B": ("L",),
    "S": ("L", "R"),
}
_DESCRIPTIONS = {
    "G": "Lite four-domain task-conditioned FiLM backbone (176,454 params)",
    "CACHE": "per-seed ROI-0.30 crop cache + Lite 202-D pre-refinement features",
    "R": "Lite Regional Refiner: 3 outer folds + median-epoch refit (58,129 params)",
    "L": "cross-fitted paired-gain labels + 16-D safety features",
    "B": "Benefit Router: canonical Phase-25 B_phi, 5 folds + refit (36,801 params)",
    "S": "Post-Refinement Safety: canonical Phase-25 S_omega, 5 folds + refit (1,217 params)",
}

__all__ = [
    "AuthorizationRequired",
    "DEPENDENCIES",
    "STAGE_ORDER",
    "StagePlan",
    "assert_lite_families_isolated",
    "family_contract",
    "lite_family_verification",
    "load_grant",
    "plan",
    "run_family",
    "run_stage",
    "verify_family",
]


@dataclass
class StagePlan:
    name: str
    depends_on: tuple
    description: str
    status: str            # COMPLETE | PENDING | BLOCKED
    reason: str = ""

    def as_dict(self) -> dict:
        return {"stage": self.name, "depends_on": list(self.depends_on),
                "description": self.description, "status": self.status,
                "reason": self.reason}


# --------------------------------------------------------------------------- #
def plan(ctx: RunContext) -> List[StagePlan]:
    """Resolve the execution plan without touching a model or a dataset."""
    out: List[StagePlan] = []
    done: Dict[str, bool] = {}
    for name in STAGE_ORDER:
        module = MODULES[name]
        blockers = [d for d in DEPENDENCIES[name] if not done.get(d)]
        try:
            complete = module.is_complete(ctx)
        except Exception as exc:                      # noqa: BLE001
            complete = False
            reason = f"is_complete raised {type(exc).__name__}: {exc}"
        else:
            reason = ""
        if blockers:
            status = "BLOCKED"
            reason = f"waiting on {blockers}"
        elif complete:
            status = "COMPLETE"
        else:
            status = "PENDING"
        done[name] = (status == "COMPLETE")
        out.append(StagePlan(name, DEPENDENCIES[name], _DESCRIPTIONS[name], status, reason))
    return out


# --------------------------------------------------------------------------- #
def load_grant(spec: Optional[str]):
    """Resolve ``module:callable`` into a grant object.  ``None`` yields no grant."""
    if not spec:
        return None
    module_name, sep, attr = spec.partition(":")
    if not sep or not module_name or not attr:
        raise AuthorizationRequired(
            "LITE_GRANT_PROVIDER_INVALID: expected 'package.module:callable'")
    try:
        provider = getattr(importlib.import_module(module_name), attr)
    except (ImportError, AttributeError) as exc:
        raise AuthorizationRequired(f"LITE_GRANT_PROVIDER_UNRESOLVABLE: {exc}") from exc
    if not callable(provider):
        raise AuthorizationRequired("LITE_GRANT_PROVIDER_INVALID: not callable")
    return provider()


def family_contract(ctx: RunContext) -> dict:
    """Hash-bound description of what would be trained.  No data is touched."""
    import hashlib
    import json

    body = {
        "schema": "ra_medfilm_barr_lite_family_contract_v1",
        "method": "RA-MedFiLM-BARR",
        "family": "LITE",
        "model_identity": "RA-MedFiLM-BARR-Lite",
        "variant": getattr(ctx, "variant", None),
        "variant_id": getattr(ctx, "variant_id", None),
        "architecture_sha256": getattr(ctx, "architecture_sha256", None),
        "training_protocol_id": L.LITE_PROTOCOL_ID,
        "parameter_identity": (ctx.parameter_identity()
                               if hasattr(ctx, "parameter_identity") else None),
        "seed": ctx.seed,
        "recipe": ctx.recipe.as_dict(),
        "operational_override": ctx.bounds.overrides(),
        "population": ctx.population.summary(),
        "stages": list(STAGE_ORDER),
        "dependencies": {k: list(v) for k, v in DEPENDENCIES.items()},
        "device": ctx.bounds.device,
        "synthetic": bool(ctx.synthetic),
        "real_training": not bool(ctx.synthetic),
        "relationship_to_full": (
            "separate secondary experiment; the FULL family, its frozen protocol and "
            "its checkpoints are unmodified"),
        "test_reads": 0,
        "router_holdout_reads": 0,
    }
    body["contract_sha256"] = hashlib.sha256(
        json.dumps(body, sort_keys=True, default=str).encode("utf-8")).hexdigest()
    return body


def _authorize_real_training(ctx: RunContext, grant: Optional[object]) -> dict:
    """Fail closed unless an operator grant authorizes this exact Lite contract."""
    if ctx.synthetic:
        return {"authorization": "SYNTHETIC_INTEGRATION_TEST", "grant": None}
    if grant is None:
        raise AuthorizationRequired(
            "LITE_REAL_TRAINING_GRANT_REQUIRED: pass --grant-provider module:callable. "
            "The Lite family reuses the existing operator grant surface "
            "(authorize_full_training); this package mints no credential, creates no "
            "new gate and bypasses no existing one")
    authorize = getattr(grant, "authorize_full_training", None)
    if not callable(authorize):
        raise AuthorizationRequired(
            "LITE_REAL_TRAINING_GRANT_INVALID: grant object has no "
            "authorize_full_training() method")
    contract = family_contract(ctx)
    authorize(dict(contract))
    return {"authorization": "OPERATOR_GRANT", "grant": type(grant).__name__,
            "contract_sha256": contract["contract_sha256"]}


# --------------------------------------------------------------------------- #
def _assert_upstream_intact(ctx: RunContext, stage: str) -> None:
    """Re-assert the family identity of every upstream checkpoint before a stage runs."""
    for dep in DEPENDENCIES[stage]:
        if dep == "G":
            ck = load_checkpoint(ctx.g_checkpoint(), component="G", seed=ctx.seed,
                                 family="LITE")
            assert_compatible(ck, component="G", seed=ctx.seed, family="LITE")
        elif dep == "R":
            ck = load_checkpoint(ctx.r_dir / "final" / "final.pt", component="R",
                                 seed=ctx.seed, family="LITE")
            assert_compatible(ck, component="R", seed=ctx.seed, family="LITE",
                              upstream={"G": ctx.g_sha()})
        elif dep == "L":
            m = read_json(ctx.l_dir / "manifest.json")
            if not m.get("labels_sha256"):
                raise FamilyCompatibilityError(f"{ctx.tag}: labels for {stage} are missing")
            if m["labels_sha256"] != sha256_file(ctx.l_dir / "labels.csv"):
                raise FamilyCompatibilityError(
                    f"{ctx.tag}: labels drifted since {stage} was planned")
        elif dep == "CACHE":
            m = read_json(ctx.cache_dir / "manifest.json")
            if m.get("g_checkpoint_sha256") != ctx.g_sha():
                raise FamilyCompatibilityError(
                    f"{ctx.tag}: crop cache does not belong to the current G family")


def run_stage(ctx: RunContext, stage: str, *, resume: bool = False, force: bool = False,
              grant: Optional[object] = None,
              log: Callable[[str], None] = print) -> StageRecord:
    if stage not in MODULES:
        raise ValueError(f"unknown stage {stage!r}")
    module = MODULES[stage]

    if not force and module.is_complete(ctx):
        log(f"[{stage}/{ctx.tag}] already complete; skipping")
        return StageRecord(stage=stage, status="COMPLETE", detail={"skipped": True})

    for dep in DEPENDENCIES[stage]:
        if not MODULES[dep].is_complete(ctx):
            raise RuntimeError(f"stage {stage} cannot run: dependency {dep} is incomplete")
    _assert_upstream_intact(ctx, stage)
    _authorize_real_training(ctx, grant)

    t0 = time.time()
    record = module.run(ctx, resume=resume, log=log)
    state = record.as_dict()
    state.update({"elapsed_seconds": round(time.time() - t0, 3),
                  "protocol_faithful": ctx.bounds.is_protocol_faithful,
                  "operational_override": ctx.bounds.overrides(),
                  "family": "LITE"})
    ctx.set_stage_state(stage, state)
    return record


def run_family(ctx: RunContext, *, stages: Optional[Sequence[str]] = None,
               resume: bool = False, force: bool = False, grant: Optional[object] = None,
               log: Callable[[str], None] = print) -> dict:
    """Execute the Lite DAG in dependency order for one seed family."""
    wanted = list(stages) if stages else list(STAGE_ORDER)
    unknown = [s for s in wanted if s not in MODULES]
    if unknown:
        raise ValueError(f"unknown stages {unknown}")

    ctx.run_root.mkdir(parents=True, exist_ok=True)
    ctx.write_family_manifest()
    authorization = _authorize_real_training(ctx, grant)

    results: Dict[str, dict] = {}
    for stage in STAGE_ORDER:
        if stage not in wanted:
            continue
        rec = run_stage(ctx, stage, resume=resume, force=force, grant=grant, log=log)
        results[stage] = {"status": rec.status, "detail": rec.detail}

    ctx.write_family_manifest(extra={
        "stages": {k: v["status"] for k, v in results.items()},
        "authorization": {k: v for k, v in authorization.items() if k != "grant"},
        "completed_utc": utc_now(),
    })
    return {"seed": ctx.seed, "tag": ctx.tag, "variant": getattr(ctx, "variant", None),
            "stages": results, "authorization": authorization}


# --------------------------------------------------------------------------- #
def verify_family(ctx: RunContext) -> dict:
    """Full-chain verification from disk.  Raises on any identity violation."""
    out: Dict[str, dict] = {}

    g_ck = load_checkpoint(ctx.g_checkpoint(), component="G", seed=ctx.seed, family="LITE")
    g_sha = sha256_file(ctx.g_checkpoint())
    out["G"] = {"sha256": g_sha, "best_epoch": g_ck["best_epoch"],
                "architecture_id": g_ck.get("architecture_id"),
                "architecture_sha256": g_ck.get("architecture_sha256"),
                "parameter_count": g_ck.get("expected_parameters")
                or L.G_EXPECTED_PARAMETERS}
    expected_id = getattr(ctx, "g_architecture_id", lambda: None)()
    if expected_id is not None and g_ck.get("architecture_id") != expected_id:
        raise FamilyCompatibilityError(
            f"{ctx.tag}: G architecture {g_ck.get('architecture_id')!r} != {expected_id!r}")
    g_arch = L.checkpoint_architecture_sha256(g_ck, block="g")
    expected_arch = getattr(ctx, "architecture_sha256", None)
    if expected_arch is not None and g_arch != expected_arch:
        raise FamilyCompatibilityError(
            f"{ctx.tag}: G architecture digest {g_arch} != variant spec {expected_arch}")
    out["G"]["architecture_sha256"] = g_arch

    cache_manifest = read_json(ctx.cache_dir / "manifest.json")
    if cache_manifest.get("g_checkpoint_sha256") != g_sha:
        raise FamilyCompatibilityError(f"{ctx.tag}: cache is not bound to this G")
    out["CACHE"] = {"population_n": cache_manifest.get("population_n"),
                    "action_available_n": cache_manifest.get("action_available_n"),
                    "g_checkpoint_sha256": g_sha}

    r_ck = load_checkpoint(ctx.r_dir / "final" / "final.pt", component="R", seed=ctx.seed,
                           family="LITE")
    assert_compatible(r_ck, component="R", seed=ctx.seed, family="LITE",
                      upstream={"G": g_sha})
    r_sha = sha256_file(ctx.r_dir / "final" / "final.pt")
    out["R"] = {"sha256": r_sha, "upstream": {"G": g_sha},
                "architecture_id": r_ck.get("architecture_id")}

    labels_manifest = read_json(ctx.l_dir / "manifest.json")
    if labels_manifest.get("labels_sha256") != sha256_file(ctx.l_dir / "labels.csv"):
        raise FamilyCompatibilityError(f"{ctx.tag}: label table drifted")
    contract = labels_manifest.get("oof_contract") or {}
    if contract.get("backbone_out_of_fold") is not False:
        raise FamilyCompatibilityError(
            f"{ctx.tag}: the primary construction must declare backbone_out_of_fold=false; "
            f"found {contract.get('backbone_out_of_fold')!r}")
    out["L"] = {"population_n": labels_manifest.get("population_n"),
                "categories": labels_manifest.get("categories"),
                "backbone_out_of_fold": contract.get("backbone_out_of_fold"),
                "refiner_out_of_fold": contract.get("refiner_out_of_fold"),
                "protocol_version": contract.get("experimental_protocol_version")}

    b_ck = load_checkpoint(ctx.b_dir / "final" / "final.pt", component="B", seed=ctx.seed,
                           family="LITE")
    assert_compatible(b_ck, component="B", seed=ctx.seed, family="LITE",
                      upstream={"G": g_sha, "R": r_sha})
    out["B"] = {"sha256": sha256_file(ctx.b_dir / "final" / "final.pt"),
                "upstream": {"G": g_sha, "R": r_sha},
                "normalizer_index": b_ck.get("normalizer_index")}

    s_ck = load_checkpoint(ctx.s_dir / "final" / "final.pt", component="S", seed=ctx.seed,
                           family="LITE")
    assert_compatible(s_ck, component="S", seed=ctx.seed, family="LITE",
                      upstream={"G": g_sha, "R": r_sha})
    out["S"] = {"sha256": sha256_file(ctx.s_dir / "final" / "final.pt"),
                "upstream": {"G": g_sha, "R": r_sha}}

    return {"seed": ctx.seed, "tag": ctx.tag, "family": "LITE",
            "variant": getattr(ctx, "variant", None),
            "components": out, "family_isolated": True,
            "verdict": "LITE_FAMILY_CHAIN_VERIFIED"}


def assert_lite_families_isolated(contexts: Sequence[RunContext],
                                  components: Sequence[str] = ("G", "R", "B", "S")) -> dict:
    """Prove no two Lite families share a trained artifact.

    Two families legitimately share data, partitions and the frozen recipe.  They
    must not share a checkpoint: an identical digest across seeds would mean a
    family was reused rather than retrained, which would make the three-seed
    spread meaningless.
    """
    paths = {"G": lambda c: c.g_dir / "best.pt",
             "R": lambda c: c.r_dir / "final" / "final.pt",
             "B": lambda c: c.b_dir / "final" / "final.pt",
             "S": lambda c: c.s_dir / "final" / "final.pt"}
    seen: Dict[str, int] = {}
    collisions = []
    per_family: Dict[int, Dict[str, str]] = {}
    for ctx in contexts:
        digests = {}
        for name in components:
            path = paths[name](ctx)
            if not path.exists():
                raise FileNotFoundError(f"{ctx.tag}: {name} checkpoint missing")
            d = sha256_file(path)
            digests[name] = d
            key = f"{name}:{d}"
            if key in seen and seen[key] != ctx.seed:
                collisions.append({"component": name, "digest": d,
                                   "seeds": sorted({seen[key], ctx.seed})})
            seen[key] = ctx.seed
        per_family[ctx.seed] = digests
    if collisions:
        raise FamilyCompatibilityError(
            "Lite seed families share trained artifacts (not independent): "
            + ", ".join(f"{c['component']} shared by {c['seeds']}" for c in collisions))
    return {"per_family": per_family, "collisions": [],
            "n_families": len(contexts), "verdict": "LITE_SEED_FAMILIES_INDEPENDENT"}


def lite_family_verification(ctx: RunContext) -> dict:
    """``verify_family`` plus the Lite-specific identity assertions."""
    base = verify_family(ctx)
    identity = ctx.parameter_identity() if hasattr(ctx, "parameter_identity") else {}
    if identity and identity.get("total_unique_parameters") != L.TOTAL_EXPECTED_PARAMETERS:
        raise FamilyCompatibilityError(
            f"{ctx.tag}: parameter identity {identity.get('total_unique_parameters')} != "
            f"{L.TOTAL_EXPECTED_PARAMETERS}")
    base["parameter_identity"] = identity
    return base
