"""``LABELS_LITE`` -- cross-fitted paired-gain labels and 16-D safety features.

Reuses the frozen FULL label producer: fold-k's refiner labels fold-k's outer
target, the candidate is fused by the frozen inverse-crop rule, Dice is measured
at the segmentation threshold 0.50 (never the ROI threshold 0.30), and
``safety_target = 1 iff delta_dice > 0``.

Two substitutions only
----------------------
``refiner_factory``
    the Lite refiner class, so the labelling pass uses this family's refiner.
``contract_provider``
    :func:`lite_oof_contract`, which is the canonical contract **plus** the Lite
    architecture identity.  The out-of-fold booleans themselves are not restated
    here -- they are inherited from the canonical producer, so the two families
    cannot disagree about what "OOF" means.

The honest limitation is unchanged and is stated in the contract: the labels are
refiner-OOF / router-OOF / safety-OOF but **backbone-in-sample**, because the Lite
G is trained once on all 5,832 TRAIN rows, which include every
ROUTER_DEVELOPMENT sample.  That is inherited deliberately so the Lite labels are
constructed identically to the FULL ones; it is not repaired, it is disclosed.
"""
from __future__ import annotations

from src.models.lite.ra_medfilm_barr_lite import LiteRegionalRefiner
from src.research.full_pipeline.context import RunContext, StageRecord
from src.research.full_pipeline.stages import label_stage

from .. import recipe as L
from ..features import lite_feature_schema

STAGE = "L"


def lite_oof_contract(ctx: RunContext) -> dict:
    """The canonical out-of-fold contract, extended with Lite identity.

    Delegates to :func:`src.research.full_pipeline.stages.label_stage.oof_contract`
    so the load-bearing booleans (``refiner_out_of_fold``,
    ``backbone_out_of_fold``, ``router_out_of_fold``, ``safety_out_of_fold``,
    ``backbone_sees_target_sample``) have exactly one definition in the codebase.
    """
    contract = label_stage.oof_contract(ctx)
    contract["family"] = "LITE"
    contract["model_identity"] = "RA-MedFiLM-BARR-Lite"
    contract["variant"] = getattr(ctx, "variant", None)
    contract["variant_id"] = getattr(ctx, "variant_id", None)
    contract["architecture_sha256"] = getattr(ctx, "architecture_sha256", None)
    contract["training_protocol_id"] = L.LITE_PROTOCOL_ID
    contract["lite"] = {
        "parameter_identity": L.parameter_identity(getattr(ctx, "variant", L.DEFAULT_VARIANT)),
        "backbone": "G_Lite",
        "refiner": "R_Lite",
        "router": "B_phi (canonical Phase-25 model, retrained on Lite features)",
        "safety": "S_omega (canonical Phase-25 model, retrained on Lite features)",
        "feature_schema": lite_feature_schema(),
        "label_construction_matches_full": True,
        "label_construction_reason": (
            "the Lite labels use the identical fold partitions and the identical "
            "fusion/threshold rule as FULL, so Lite and FULL are comparable; changing "
            "the backbone training population here would break that comparability"),
    }
    contract["not_fully_oof"] = True
    contract["not_fully_oof_reason"] = (
        "backbone_in_sample: G_Lite trained on all of TRAIN, including every "
        "ROUTER_DEVELOPMENT sample; only the refiner, router and safety stages are "
        "genuinely cross-fitted")
    contract["strict_backbone_oof_available"] = True
    contract["strict_backbone_oof_is_primary"] = False
    return contract


def run(ctx: RunContext, *, resume: bool = False, log=print) -> StageRecord:
    spec = ctx.spec                                            # type: ignore[attr-defined]
    record = label_stage.run(
        ctx, resume=resume, log=log,
        refiner_factory=lambda: LiteRegionalRefiner(spec),
        contract_provider=lite_oof_contract,
    )
    record.detail = dict(record.detail or {})
    record.detail.update({
        "model_identity": "RA-MedFiLM-BARR-Lite",
        "variant": getattr(ctx, "variant", None),
        "oof_contract": lite_oof_contract(ctx),
    })
    return record


def is_complete(ctx: RunContext) -> bool:
    return label_stage.is_complete(ctx)


def verify(ctx: RunContext) -> dict:
    out = label_stage.verify(ctx)
    out["family"] = "LITE"
    out["oof_contract"] = lite_oof_contract(ctx)
    out["verdict"] = ("LABELS_LITE_VERIFIED" if out.get("verdict") == "LABELS_VERIFIED"
                      else out.get("verdict"))
    return out
