"""Frozen research identity of the RA-MedFiLM-BARR-Lite family.

The Lite family is a **separate experiment**, not a modification of the FULL
protocol.  Everything scientific that is shared with FULL (thresholds, the ROI
rule, the label categories, the fold partitions, the B_phi/S_omega recipes) is
*imported* from :mod:`src.research.full_pipeline.recipe` rather than restated
here, so the two families cannot drift apart on a shared constant.

What is genuinely Lite-specific and therefore frozen here
---------------------------------------------------------
* the selected variant (``depthwise_compact``) and its architecture digest;
* the per-component expected parameter counts and their unique sum;
* the Lite tap channel/grid contract used by the 202-D feature builder;
* the training protocol identifier stamped into every Lite checkpoint.

Parameter identity (verified against the built models, never assumed)
--------------------------------------------------------------------
``G_Lite 176,454`` + ``R_Lite 58,129`` + ``B_phi 36,801`` + ``S_omega 1,217``
= **272,601**.  The FULL family sums to **4,837,420** over the same four
components (``3,523,001`` G + ``1,276,401`` R + ``36,801`` B + ``1,217`` S), so
the reduction is ``1 - 272601/4837420 = 94.3647%``.

Note the two numbers that are easy to confuse:

* ``3,523,001`` is the FULL **G alone**, not the FULL family.  Comparing
  ``272,601`` against it yields 92.26%, which is the wrong denominator.
* The reduction is computed here, never typed in as a literal, so it cannot
  silently disagree with the component counts.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from src.models.lite.ra_medfilm_barr_lite import CANDIDATE_SPECS, LiteVariantSpec
from src.research.full_pipeline import recipe as R

__all__ = [
    "DEFAULT_VARIANT",
    "VARIANT_IDS",
    "LITE_PROTOCOL_ID",
    "LITE_SEEDS",
    "G_EXPECTED_PARAMETERS",
    "R_EXPECTED_PARAMETERS",
    "B_EXPECTED_PARAMETERS",
    "S_EXPECTED_PARAMETERS",
    "TOTAL_EXPECTED_PARAMETERS",
    "FULL_FAMILY_TOTAL_PARAMETERS",
    "LITE_NATIVE_CHANNELS",
    "LITE_FEATURE_GRID",
    "FEATURE_TAPS",
    "reduction_fraction",
    "reduction_percent",
    "parameter_identity",
    "checkpoint_architecture_sha256",
    "spec",
    "global_architecture_id",
    "refiner_architecture_id",
    "lite_recipe",
]

# --------------------------------------------------------------------------- #
# selection
# --------------------------------------------------------------------------- #
#: The selected first Lite training candidate.  Chosen on the frozen profile
#: artifact, not on any accuracy result -- no Lite accuracy result exists.
DEFAULT_VARIANT = "depthwise_compact"
VARIANT_IDS: Tuple[str, ...] = tuple(CANDIDATE_SPECS)

LITE_PROTOCOL_ID = "RA_MEDFILM_BARR_LITE_SECONDARY_V1"
LITE_SEEDS: Tuple[int, ...] = (42, 123, 3407)

# --------------------------------------------------------------------------- #
# parameter identity
# --------------------------------------------------------------------------- #
G_EXPECTED_PARAMETERS = 176_454
R_EXPECTED_PARAMETERS = 58_129
#: B_phi and S_omega are the canonical Phase-25 models, unchanged.
B_EXPECTED_PARAMETERS = R.B_EXPECTED_PARAMETERS        # 36,801
S_EXPECTED_PARAMETERS = R.S_EXPECTED_PARAMETERS        # 1,217

TOTAL_EXPECTED_PARAMETERS = (G_EXPECTED_PARAMETERS + R_EXPECTED_PARAMETERS
                             + B_EXPECTED_PARAMETERS + S_EXPECTED_PARAMETERS)

#: FULL family total over the SAME four components.  This is the correct
#: denominator for the reduction claim.
FULL_FAMILY_TOTAL_PARAMETERS = (R.G_EXPECTED_PARAMETERS + R.R_EXPECTED_PARAMETERS
                                + R.B_EXPECTED_PARAMETERS + R.S_EXPECTED_PARAMETERS)

# --------------------------------------------------------------------------- #
# tap contract for the 202-D router feature vector
# --------------------------------------------------------------------------- #
FEATURE_TAPS: Tuple[str, ...] = R.CACHE_FEATURE_TAPS    # bridge / decoder2 / decoder1

#: Lite native tap widths.  The feature *order* and the ten scalar descriptors
#: are identical to FULL; only these widths differ, and the frozen
#: ``DETERMINISTIC_CHANNEL_ADAPTIVE_AVG_POOL_1D_V1`` reduction maps any C -> 32.
LITE_NATIVE_CHANNELS: Dict[str, int] = {"bridge": 128, "decoder2": 24, "decoder1": 12}

#: Feature-grid side of each tap for a 512x512 input.  These are IDENTICAL to the
#: FULL grids (32 / 256 / 512) because the Lite encoder keeps the same
#: downsampling schedule; only the channel counts changed.
LITE_FEATURE_GRID: Dict[str, int] = {"bridge": 32, "decoder2": 256, "decoder1": 512}

#: The FULL widths, recorded so a mismatch can be reported rather than assumed.
FULL_NATIVE_CHANNELS: Dict[str, int] = dict(R.CACHE_NATIVE_CHANNELS)


# --------------------------------------------------------------------------- #
def spec(variant: str = DEFAULT_VARIANT) -> LiteVariantSpec:
    """The immutable architecture definition for ``variant``."""
    try:
        return CANDIDATE_SPECS[variant]
    except KeyError:
        raise ValueError(
            f"unknown Lite variant {variant!r}; available: {sorted(CANDIDATE_SPECS)}") from None


def global_architecture_id(variant: str = DEFAULT_VARIANT) -> str:
    """Architecture id stamped into the Lite G checkpoint envelope."""
    return f"{spec(variant).variant_id}::global"


def refiner_architecture_id(variant: str = DEFAULT_VARIANT) -> str:
    """Architecture id stamped into the Lite R_psi checkpoint envelope."""
    return f"{spec(variant).variant_id}::refiner"


def reduction_fraction() -> float:
    """``1 - Lite total / FULL family total`` -- computed, never hard-coded."""
    return 1.0 - (TOTAL_EXPECTED_PARAMETERS / FULL_FAMILY_TOTAL_PARAMETERS)


def reduction_percent() -> float:
    return 100.0 * reduction_fraction()


def checkpoint_architecture_sha256(ck: dict, *, block: str = "g") -> Optional[str]:
    """Read the architecture digest a Lite checkpoint was stamped with.

    The digest lives in the checkpoint's ``recipe[<block>]`` block (written by
    :func:`lite_recipe`), because that is where the stage producers already store
    the recipe they ran with.  A top-level ``architecture_sha256`` is accepted too
    if a future producer stamps one, but the recipe block is authoritative.

    Returning ``None`` rather than raising lets the caller decide whether an absent
    digest is a hard error -- it is for the Lite family, and the callers say so.
    """
    direct = ck.get("architecture_sha256")
    if isinstance(direct, str) and len(direct) == 64:
        return direct
    block_value = (ck.get("recipe") or {}).get(block) or {}
    digest = block_value.get("architecture_sha256")
    return digest if isinstance(digest, str) and len(digest) == 64 else None


def parameter_identity(variant: str = DEFAULT_VARIANT) -> dict:
    """Machine-readable parameter identity block for manifests."""
    s = spec(variant)
    return {
        "variant": variant,
        "variant_id": s.variant_id,
        "architecture_sha256": s.sha256(),
        "components": {
            "G": G_EXPECTED_PARAMETERS,
            "R_psi": R_EXPECTED_PARAMETERS,
            "B_phi": B_EXPECTED_PARAMETERS,
            "S_omega": S_EXPECTED_PARAMETERS,
        },
        "total_unique_parameters": TOTAL_EXPECTED_PARAMETERS,
        "full_family_total_parameters": FULL_FAMILY_TOTAL_PARAMETERS,
        "full_global_only_parameters": R.G_EXPECTED_PARAMETERS,
        "reduction_fraction_vs_full_family": reduction_fraction(),
        "reduction_percent_vs_full_family": reduction_percent(),
        "reduction_note": (
            "the reduction denominator is the FULL G+R+B+S family total "
            f"({FULL_FAMILY_TOTAL_PARAMETERS}); the FULL G alone "
            f"({R.G_EXPECTED_PARAMETERS}) is NOT the correct denominator"),
        "native_tap_channels": dict(LITE_NATIVE_CHANNELS),
        "full_native_tap_channels": dict(FULL_NATIVE_CHANNELS),
        "feature_grid": dict(LITE_FEATURE_GRID),
        "router_numeric_dim": R.B_NUMERIC_DIM,
    }


# --------------------------------------------------------------------------- #
def lite_recipe(variant: str = DEFAULT_VARIANT) -> R.Recipe:
    """A :class:`Recipe` whose ``g`` and ``r`` blocks describe the Lite models.

    The ``b``, ``s``, ``thresholds`` and ``populations`` blocks are the canonical
    ones, because B_phi, S_omega and every threshold are genuinely unchanged.
    Stamping the Lite architecture into the checkpoint recipe is what makes a
    Lite checkpoint self-describing: loading it into a FULL model is then a
    digest mismatch rather than a silent shape error.
    """
    s = spec(variant)
    base = R.Recipe()
    g = dict(base.g)
    g.update({
        "architecture_id": global_architecture_id(variant),
        "architecture_sha256": s.sha256(),
        "model": {
            "name": "RA-MedFiLM-BARR-Lite",
            "task_count": 4,
            "in_channels": 3,
            "out_channels": 1,
            "global_channels": list(s.global_channels),
            "embedding_dim": s.embedding_dim,
            "film_hidden_dim": s.film_hidden_dim,
            "block_kind": s.block_kind,
            "skip_fusion": s.skip_fusion,
            "feature_taps": list(FEATURE_TAPS),
            "native_tap_channels": dict(LITE_NATIVE_CHANNELS),
        },
        "expected_parameters": G_EXPECTED_PARAMETERS,
        "training_protocol_id": LITE_PROTOCOL_ID,
        "variant": variant,
        "variant_id": s.variant_id,
    })
    r = dict(base.r)
    r.update({
        "architecture_id": refiner_architecture_id(variant),
        "architecture_sha256": s.sha256(),
        "channels": list(s.refiner_channels),
        "input_channels": R.R_INPUT_CHANNELS,
        "expected_parameters": R_EXPECTED_PARAMETERS,
        "training_protocol_id": LITE_PROTOCOL_ID,
        "variant": variant,
        "variant_id": s.variant_id,
    })
    return R.Recipe(g=g, r=r, b=base.b, s=base.s,
                    thresholds=base.thresholds, populations=base.populations)
