"""``G_LITE`` -- the Lite global backbone producer.

Reuses the FULL G trainer end to end (domain-balanced sampler, derived per-epoch
seeds, BCE+Dice loss, cosine schedule, macro-domain-Dice selection with the
validation-loss tie-break, early stopping, atomic envelope, bit-exact resume) and
substitutes only the model.

Why the FULL G weights are never reused
--------------------------------------
A Lite family must be a *self-contained* replicate.  Loading the FULL G and then
fine-tuning it would (a) make the Lite result a function of a 3.5M-parameter
model, defeating the efficiency claim, and (b) break the requirement that the
three Lite seeds are independent families.  The only accepted starting point is
fresh initialisation from the Lite derived seed.
"""
from __future__ import annotations

from typing import Optional

from src.models.lite.ra_medfilm_barr_lite import (LiteGlobalMedFiLM,
                                                  count_unique_parameters)
from src.research.full_pipeline.context import RunContext, StageRecord
from src.research.full_pipeline.stages import global_stage

from .. import recipe as L
from ..features import lite_feature_schema

STAGE = "G"

#: Module-name fragments a global backbone must never contain.  Same intent as the
#: FULL guard: a backbone that already embeds the regional/routing machinery would
#: make the Lite ablation meaningless.
FORBIDDEN_MODULE_KEYS = ("localizer", "proposal", "roi", "regional", "refiner", "router")


def build_lite_global(ctx: RunContext) -> LiteGlobalMedFiLM:
    """Construct the selected Lite variant and assert its architecture contract."""
    spec = ctx.spec                                   # type: ignore[attr-defined]
    model = LiteGlobalMedFiLM(spec, task_count=4)

    n = count_unique_parameters(model)
    if n != L.G_EXPECTED_PARAMETERS:
        raise RuntimeError(
            f"G_Lite parameter count {n} != frozen {L.G_EXPECTED_PARAMETERS} "
            f"for variant {spec.variant_id}")

    # the tap interface the 202-D feature builder depends on
    if not hasattr(model, "forward_with_features"):
        raise RuntimeError("G_Lite exposes no forward_with_features tap interface")
    for tap in L.FEATURE_TAPS:
        if not hasattr(model, tap):
            raise RuntimeError(f"G_Lite has no tap module {tap!r}")

    bad = [name for name, _ in model.named_modules()
           if any(key in name.lower() for key in FORBIDDEN_MODULE_KEYS)]
    if bad:
        raise RuntimeError(f"Lite G must not contain regional/routing modules: {bad[:5]}")

    if not getattr(model, "task_count", None) == 4:
        raise RuntimeError("Lite G must accept exactly four task identities")
    return model


def run(ctx: RunContext, *, resume: bool = False, log=print,
        variant: Optional[str] = None) -> StageRecord:
    """Train the Lite global backbone for ``ctx``."""
    if variant is not None and variant != ctx.variant:      # type: ignore[attr-defined]
        raise ValueError(
            f"requested variant {variant!r} does not match the context variant "
            f"{ctx.variant!r}")                            # type: ignore[attr-defined]
    log(f"[G/{ctx.tag}] Lite variant={ctx.variant} "              # type: ignore[attr-defined]
        f"architecture={ctx.architecture_sha256[:16]}")           # type: ignore[attr-defined]
    record = global_stage.run(
        ctx, resume=resume, log=log,
        model_factory=build_lite_global,
        expected_parameters=L.G_EXPECTED_PARAMETERS,
        architecture_id=ctx.g_architecture_id(),                  # type: ignore[attr-defined]
    )
    record.detail = dict(record.detail or {})
    record.detail.update({
        "model_identity": "RA-MedFiLM-BARR-Lite",
        "variant": ctx.variant,                                   # type: ignore[attr-defined]
        "architecture_sha256": ctx.architecture_sha256,           # type: ignore[attr-defined]
        "feature_schema": lite_feature_schema(),
        "initialisation": "fresh; no FULL weight is loaded or transferred",
    })
    return record


def is_complete(ctx: RunContext) -> bool:
    return global_stage.is_complete(ctx)


def verify(ctx: RunContext) -> dict:
    out = global_stage.verify(ctx)
    out["family"] = "LITE"
    out["variant"] = getattr(ctx, "variant", None)
    out["verdict"] = "G_LITE_VERIFIED"
    return out
