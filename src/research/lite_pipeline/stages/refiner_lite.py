"""``R_LITE`` -- the Lite regional refiner producer.

Reuses the frozen FULL refiner producer: three group-safe outer folds over
ROUTER_DEVELOPMENT with a 90/10 fit/early-stop split, BCE+Dice loss, AdamW 1e-4,
cosine annealing, patience 15, minimum-early-stop-loss selection, and a refit at
the median of the three fold best-epochs over all of ROUTER_DEVELOPMENT.

Only the model changes.  The fold manifests, the crop dataset and the collate
function are the shared ones, which is what makes the Lite and FULL refiner
*comparable* rather than merely similar.
"""
from __future__ import annotations

from src.models.lite.ra_medfilm_barr_lite import (LiteRegionalRefiner,
                                                  count_unique_parameters)
from src.research.full_pipeline.context import RunContext, StageRecord
from src.research.full_pipeline.stages import refiner_stage

from .. import recipe as L

STAGE = "R"


def build_lite_refiner(ctx: RunContext) -> LiteRegionalRefiner:
    """Construct the Lite refiner and assert its parameter identity."""
    model = LiteRegionalRefiner(ctx.spec)                      # type: ignore[attr-defined]
    n = count_unique_parameters(model)
    if n != L.R_EXPECTED_PARAMETERS:
        raise RuntimeError(
            f"R_Lite parameter count {n} != frozen {L.R_EXPECTED_PARAMETERS}")
    return model


def run(ctx: RunContext, *, resume: bool = False, log=print) -> StageRecord:
    record = refiner_stage.run(
        ctx, resume=resume, log=log,
        model_factory=build_lite_refiner,
        architecture_id=ctx.r_architecture_id(),               # type: ignore[attr-defined]
        expected_parameters=L.R_EXPECTED_PARAMETERS,
    )
    record.detail = dict(record.detail or {})
    record.detail.update({
        "model_identity": "RA-MedFiLM-BARR-Lite",
        "variant": ctx.variant,                                # type: ignore[attr-defined]
        "architecture_sha256": ctx.architecture_sha256,         # type: ignore[attr-defined]
        "initialisation": "fresh; no FULL refiner weight is loaded or transferred",
    })
    return record


def is_complete(ctx: RunContext) -> bool:
    return refiner_stage.is_complete(ctx)


def verify(ctx: RunContext) -> dict:
    out = refiner_stage.verify(ctx)
    out["family"] = "LITE"
    out["variant"] = getattr(ctx, "variant", None)
    out["verdict"] = "R_LITE_VERIFIED"
    return out
