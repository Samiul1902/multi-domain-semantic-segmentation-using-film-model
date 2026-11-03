"""Per-family run context for the Lite pipeline.

The Lite pipeline reuses :class:`src.research.full_pipeline.context.RunContext`
verbatim -- the stage producers read the seed family, the operational bounds, the
population, the fold tables and the artifact root exclusively through it.  Only
three things differ, and all three are expressed as overrides here rather than by
forking the class:

1. ``family_name`` -> ``"LITE"``, which is stamped into every checkpoint envelope
   and manifest and is what stops a Lite checkpoint being read as a FULL one;
2. the artifact root is ``runs/lite/<tag>`` and the tag is ``lite_seed<seed>``, so
   the two families can share a parent directory without ever colliding;
3. the ``recipe`` block describes the Lite architectures while leaving the
   canonical B/S/threshold/population blocks untouched.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

from src.models.lite.ra_medfilm_barr_lite import LiteVariantSpec
from src.research.full_pipeline import recipe as R
from src.research.full_pipeline.context import RunContext, StageRecord
from src.research.full_pipeline.population import PopulationSpec
from src.research.full_pipeline.seeds import SeedFamily

from . import recipe as L

__all__ = ["LiteRunContext", "StageRecord", "make_lite_context", "lite_seed_family"]


def lite_seed_family(seed: int) -> SeedFamily:
    """A seed family whose derived-seed namespace is ``LITE``.

    The label is ``lite_seed<seed>`` so the run directory and every log line
    identify the family unambiguously, and the namespace guarantees the Lite
    components never draw the same initialisation stream as their FULL
    counterparts.
    """
    return SeedFamily(int(seed), label=f"lite_seed{int(seed)}", namespace="LITE")


@dataclass
class LiteRunContext(RunContext):
    """A :class:`RunContext` for one Lite seed family."""

    recipe: R.Recipe = field(default_factory=L.lite_recipe)
    variant: str = L.DEFAULT_VARIANT

    def __post_init__(self) -> None:
        if self.variant not in L.VARIANT_IDS:
            raise ValueError(
                f"unknown Lite variant {self.variant!r}; available: {sorted(L.VARIANT_IDS)}")

    @property
    def family_name(self) -> str:
        return "LITE"

    @property
    def spec(self) -> LiteVariantSpec:
        return L.spec(self.variant)

    @property
    def variant_id(self) -> str:
        return self.spec.variant_id

    @property
    def architecture_sha256(self) -> str:
        return self.spec.sha256()

    # ---- Lite-specific identity helpers ------------------------------- #
    def parameter_identity(self) -> dict:
        return L.parameter_identity(self.variant)

    def g_architecture_id(self) -> str:
        return L.global_architecture_id(self.variant)

    def r_architecture_id(self) -> str:
        return L.refiner_architecture_id(self.variant)

    def base_manifest(self) -> dict:
        manifest = super().base_manifest()
        manifest.update({
            "artifact": "lite_barr_family_manifest",
            "model_identity": "RA-MedFiLM-BARR-Lite",
            "variant": self.variant,
            "variant_id": self.variant_id,
            "architecture_sha256": self.architecture_sha256,
            "training_protocol_id": L.LITE_PROTOCOL_ID,
            "parameter_identity": self.parameter_identity(),
            "family_relationship": (
                "separate secondary experiment; the FULL family and its frozen "
                "protocol are unmodified by this pipeline"),
            "real_training_started": False,
        })
        return manifest


def make_lite_context(seed: int, *, root: Optional[Path] = None, synthetic: bool = False,
                      bounds: Optional[R.OperationalBounds] = None,
                      population: Optional[PopulationSpec] = None,
                      variant: str = L.DEFAULT_VARIANT) -> LiteRunContext:
    """Assemble a Lite context for one seed.

    ``population`` and ``bounds`` are injected by the caller so this module never
    reaches for a global path and never decides on its own whether a run is
    synthetic.  A synthetic run is always stamped as such.
    """
    if population is None:
        raise ValueError("population is required; the context never guesses one")
    return LiteRunContext(
        family=lite_seed_family(seed),
        root=Path(root) if root is not None else (R.ROOT / "runs" / "lite"),
        bounds=bounds or R.OperationalBounds(),
        population=population,
        recipe=L.lite_recipe(variant),
        allow_derived_folds=bool(synthetic),
        synthetic=bool(synthetic),
        variant=variant,
    )


def lite_artifact_layout(ctx: LiteRunContext) -> Dict[str, str]:
    """The artifact directories this context resolves to, for reporting."""
    return {
        "run_root": str(ctx.run_root),
        "G": str(ctx.g_dir),
        "cache": str(ctx.cache_dir),
        "R": str(ctx.r_dir),
        "L": str(ctx.l_dir),
        "B": str(ctx.b_dir),
        "S": str(ctx.s_dir),
        "inference": str(ctx.inference_dir),
    }
