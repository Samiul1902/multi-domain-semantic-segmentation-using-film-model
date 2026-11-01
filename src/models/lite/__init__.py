"""Parameter-efficient, separately identified RA-MedFiLM-BARR variants."""

from .ra_medfilm_barr_lite import (
    CANDIDATE_SPECS,
    DistillationLossWeights,
    LiteGlobalMedFiLM,
    LiteRegionalRefiner,
    LiteVariantSpec,
    LITE_SEEDS,
    LITE_TRAINING_PRESET,
    MODEL_COMPARISON_MATRIX,
    binary_distillation_loss,
    count_unique_parameters,
    lite_distillation_training_step,
    parameter_inventory,
    seed_lite_training,
    seed_lite_worker,
    teacher_bundle_sha256,
)

__all__ = [
    "CANDIDATE_SPECS",
    "DistillationLossWeights",
    "LiteGlobalMedFiLM",
    "LiteRegionalRefiner",
    "LiteVariantSpec",
    "LITE_SEEDS",
    "LITE_TRAINING_PRESET",
    "MODEL_COMPARISON_MATRIX",
    "binary_distillation_loss",
    "count_unique_parameters",
    "lite_distillation_training_step",
    "parameter_inventory",
    "seed_lite_training",
    "seed_lite_worker",
    "teacher_bundle_sha256",
]
