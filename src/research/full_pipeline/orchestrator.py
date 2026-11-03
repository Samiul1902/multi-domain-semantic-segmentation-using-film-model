"""Stage dependency resolution, resumable execution and family verification.

The FULL family is a six-node DAG::

    G  ->  CACHE  ->  R  ->  L  ->  B  ->  S

``G``      GlobalMedFiLM                (no upstream)
``CACHE``  per-seed ROI crop cache + 202-D features (needs G)
``R``      Regional Refiner, 3 folds + refit         (needs CACHE, hence G)
``L``      OOF paired-gain labels + 16-D safety features (needs R, CACHE)
``B``      Benefit Router, 5 folds + refit           (needs L)
``S``      Post-Refinement Safety, 5 folds + refit   (needs L, R)

Execution rules
---------------
* A stage is skipped when it is already COMPLETE **and** its recorded upstream
  digests still match the artifacts on disk.  A drifted upstream invalidates the
  downstream stage instead of silently reusing it.
* Before a stage runs, every upstream checkpoint is re-opened and its family
  (schema / component / seed / SHA chain) is re-asserted.  A seed-42 refiner can
  never be consumed by a seed-123 router.
* Real (non-synthetic) execution requires an operator-supplied grant resolved from
  ``--grant-provider module:callable``.  Nothing is minted here and no gate is
  bypassed; absent a grant the orchestrator refuses to train on real data.
"""
from __future__ import annotations

import importlib
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Mapping, Optional, Sequence

from . import recipe as R
from .context import RunContext, StageRecord
from .provenance import (FamilyCompatibilityError, assert_compatible, atomic_write_json,
                         load_checkpoint, read_json, sha256_file, utc_now)
from .stages import (cache_stage, global_stage, label_stage, refiner_stage, router_stage,
                     safety_stage)

STAGE_ORDER = ("G", "CACHE", "R", "L", "B", "S")
DEPENDENCIES: Dict[str, tuple] = {
    "G": (),
    "CACHE": ("G",),
    "R": ("CACHE",),
    "L": ("R", "CACHE"),
    "B": ("L",),
    "S": ("L", "R"),
}
_MODULES = {"G": global_stage, "CACHE": cache_stage, "R": refiner_stage,
            "L": label_stage, "B": router_stage, "S": safety_stage}
_DESCRIPTIONS = {
    "G": "GlobalMedFiLM four-domain task-conditioned FiLM",
    "CACHE": "per-seed ROI-0.30 crop cache + 202-D pre-refinement features",
    "R": "Regional Refiner: 3 outer folds + median-epoch refit",
    "L": "OOF paired-gain labels + 16-D safety features",
    "B": "Benefit Router: 5 cross-fit folds + median-epoch refit",
    "S": "Post-Refinement Safety: 5 cross-fit folds + median-epoch refit",
}


class AuthorizationRequired(RuntimeError):
    """Raised when real training is requested without an operator grant."""


# --------------------------------------------------------------------------- #
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


def plan(ctx: RunContext) -> List[StagePlan]:
    """Resolve the execution plan without touching a model or a dataset."""
    out: List[StagePlan] = []
    done: Dict[str, bool] = {}
    for name in STAGE_ORDER:
        module = _MODULES[name]
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
def _authorize_real_training(ctx: RunContext, grant: Optional[object]) -> dict:
    """Fail closed unless an operator grant authorizes this exact family contract."""
    if ctx.synthetic:
        return {"authorization": "SYNTHETIC_INTEGRATION_TEST", "grant": None}
    if grant is None:
        raise AuthorizationRequired(
            "FULL_REAL_TRAINING_GRANT_REQUIRED: pass --grant-provider module:callable; "
            "this package mints no credential and bypasses no gate")
    authorize = getattr(grant, "authorize_full_training", None)
    if not callable(authorize):
        raise AuthorizationRequired(
            "FULL_REAL_TRAINING_GRANT_INVALID: grant object has no authorize_full_training()")
    contract = family_contract(ctx)
    authorize(dict(contract))
    return {"authorization": "OPERATOR_GRANT", "grant": type(grant).__name__,
            "contract_sha256": contract["contract_sha256"]}


def load_grant(spec: Optional[str]):
    """Resolve ``module:callable`` into a grant object.  ``None`` yields no grant."""
    if not spec:
        return None
    module_name, sep, attr = spec.partition(":")
    if not sep or not module_name or not attr:
        raise AuthorizationRequired(
            "FULL_GRANT_PROVIDER_INVALID: expected 'package.module:callable'")
    try:
        provider = getattr(importlib.import_module(module_name), attr)
    except (ImportError, AttributeError) as exc:
        raise AuthorizationRequired(f"FULL_GRANT_PROVIDER_UNRESOLVABLE: {exc}") from exc
    if not callable(provider):
        raise AuthorizationRequired("FULL_GRANT_PROVIDER_INVALID: not callable")
    return provider()


def family_contract(ctx: RunContext) -> dict:
    """Hash-bound description of what would be trained.  No data is touched."""
    import hashlib
    import json

    body = {
        "schema": "ra_medfilm_barr_full_family_contract_v1",
        "method": "RA-MedFiLM-BARR",
        "family": "FULL",
        "seed": ctx.seed,
        "recipe": ctx.recipe.as_dict(),
        "operational_override": ctx.bounds.overrides(),
        "population": ctx.population.summary(),
        "stages": list(STAGE_ORDER),
        "dependencies": {k: list(v) for k, v in DEPENDENCIES.items()},
        "device": ctx.bounds.device,
        "test_reads": 0,
        "router_holdout_reads": 0,
    }
    body["contract_sha256"] = hashlib.sha256(
        json.dumps(body, sort_keys=True, default=str).encode("utf-8")).hexdigest()
    return body


# --------------------------------------------------------------------------- #
def _assert_upstream_intact(ctx: RunContext, stage: str) -> None:
    """Re-assert the family identity of every upstream checkpoint before a stage runs."""
    for dep in DEPENDENCIES[stage]:
        if dep == "G":
            ck = load_checkpoint(ctx.g_checkpoint(), component="G", seed=ctx.seed)
            assert_compatible(ck, component="G", seed=ctx.seed)
        elif dep == "R":
            ck = load_checkpoint(ctx.r_dir / "final" / "final.pt", component="R",
                                 seed=ctx.seed)
            assert_compatible(ck, component="R", seed=ctx.seed,
                              upstream={"G": ctx.g_sha()})
        elif dep == "L":
            m = read_json(ctx.l_dir / "manifest.json")
            if not m.get("labels_sha256"):
                raise FamilyCompatibilityError(f"{ctx.tag}: labels for {stage} are missing")
            if m["labels_sha256"] != sha256_file(ctx.l_dir / "labels.csv"):
                raise FamilyCompatibilityError(f"{ctx.tag}: labels drifted since {stage} was planned")
        elif dep == "CACHE":
            m = read_json(ctx.cache_dir / "manifest.json")
            if m.get("g_checkpoint_sha256") != ctx.g_sha():
                raise FamilyCompatibilityError(
                    f"{ctx.tag}: crop cache does not belong to the current G family")


def run_stage(ctx: RunContext, stage: str, *, resume: bool = False, force: bool = False,
              grant: Optional[object] = None, log: Callable[[str], None] = print) -> StageRecord:
    if stage not in _MODULES:
        raise ValueError(f"unknown stage {stage!r}")
    module = _MODULES[stage]

    if not force and module.is_complete(ctx):
        log(f"[{stage}/{ctx.tag}] already complete; skipping")
        return StageRecord(stage=stage, status="COMPLETE", detail={"skipped": True})

    for dep in DEPENDENCIES[stage]:
        if not _MODULES[dep].is_complete(ctx):
            raise RuntimeError(f"stage {stage} cannot run: dependency {dep} is incomplete")
    _assert_upstream_intact(ctx, stage)
    _authorize_real_training(ctx, grant)

    t0 = time.time()
    record = module.run(ctx, resume=resume, log=log)
    state = record.as_dict()
    state.update({"elapsed_seconds": round(time.time() - t0, 3),
                  "protocol_faithful": ctx.bounds.is_protocol_faithful,
                  "operational_override": ctx.bounds.overrides()})
    ctx.set_stage_state(stage, state)
    return record


def run_family(ctx: RunContext, *, stages: Optional[Sequence[str]] = None,
               resume: bool = False, force: bool = False, grant: Optional[object] = None,
               log: Callable[[str], None] = print) -> dict:
    """Execute the DAG in dependency order for one seed family."""
    wanted = list(stages) if stages else list(STAGE_ORDER)
    unknown = [s for s in wanted if s not in _MODULES]
    if unknown:
        raise ValueError(f"unknown stages {unknown}")

    ctx.run_root.mkdir(parents=True, exist_ok=True)
    ctx.write_family_manifest()
    _authorize_real_training(ctx, grant)

    results: Dict[str, dict] = {}
    for stage in STAGE_ORDER:
        if stage not in wanted:
            continue
        rec = run_stage(ctx, stage, resume=resume, force=force, grant=grant, log=log)
        results[stage] = {"status": rec.status, "detail": rec.detail}

    ctx.write_family_manifest(extra={
        "stages": {k: v["status"] for k, v in results.items()},
        "completed_utc": utc_now(),
    })
    return {"seed": ctx.seed, "tag": ctx.tag, "stages": results}


# --------------------------------------------------------------------------- #
def verify_family(ctx: RunContext) -> dict:
    """Full-chain verification from disk.  Raises on any identity violation."""
    out: Dict[str, dict] = {}

    g_ck = load_checkpoint(ctx.g_checkpoint(), component="G", seed=ctx.seed)
    g_sha = sha256_file(ctx.g_checkpoint())
    out["G"] = {"sha256": g_sha, "best_epoch": g_ck["best_epoch"]}

    cache_manifest = read_json(ctx.cache_dir / "manifest.json")
    if cache_manifest.get("g_checkpoint_sha256") != g_sha:
        raise FamilyCompatibilityError(f"{ctx.tag}: cache is not bound to this G")
    out["CACHE"] = {"population_n": cache_manifest.get("population_n"),
                    "action_available_n": cache_manifest.get("action_available_n"),
                    "g_checkpoint_sha256": g_sha}

    r_ck = load_checkpoint(ctx.r_dir / "final" / "final.pt", component="R", seed=ctx.seed)
    assert_compatible(r_ck, component="R", seed=ctx.seed, upstream={"G": g_sha})
    r_sha = sha256_file(ctx.r_dir / "final" / "final.pt")
    out["R"] = {"sha256": r_sha, "upstream": {"G": g_sha}}

    labels_manifest = read_json(ctx.l_dir / "manifest.json")
    if labels_manifest.get("labels_sha256") != sha256_file(ctx.l_dir / "labels.csv"):
        raise FamilyCompatibilityError(f"{ctx.tag}: label table drifted")
    out["L"] = {"population_n": labels_manifest.get("population_n"),
                "categories": labels_manifest.get("categories")}

    b_ck = load_checkpoint(ctx.b_dir / "final" / "final.pt", component="B", seed=ctx.seed)
    assert_compatible(b_ck, component="B", seed=ctx.seed,
                      upstream={"G": g_sha, "R": r_sha})
    out["B"] = {"sha256": sha256_file(ctx.b_dir / "final" / "final.pt"),
                "upstream": {"G": g_sha, "R": r_sha}}

    s_ck = load_checkpoint(ctx.s_dir / "final" / "final.pt", component="S", seed=ctx.seed)
    assert_compatible(s_ck, component="S", seed=ctx.seed,
                      upstream={"G": g_sha, "R": r_sha})
    out["S"] = {"sha256": sha256_file(ctx.s_dir / "final" / "final.pt"),
                "upstream": {"G": g_sha, "R": r_sha}}

    return {"seed": ctx.seed, "tag": ctx.tag, "components": out,
            "family_isolated": True, "verdict": "FULL_FAMILY_CHAIN_VERIFIED"}


def assert_seed_families_isolated(contexts: Sequence[RunContext],
                                  components: Sequence[str] = ("G", "R", "B", "S")) -> dict:
    """Prove that no two families share a component checkpoint.

    Two families may legitimately share *data* and *partitions*; they must not share
    a trained artifact.  Identical digests across families would mean a family was
    reused rather than retrained.
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
            "seed families share trained artifacts (not independent): "
            + ", ".join(f"{c['component']} shared by {c['seeds']}" for c in collisions))
    return {"per_family": per_family, "collisions": [],
            "n_families": len(contexts), "verdict": "SEED_FAMILIES_INDEPENDENT"}
