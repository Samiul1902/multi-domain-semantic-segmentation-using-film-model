"""Phase 21 — GLOBAL MedFiLM reference model package."""
from .global_medfilm import (
    GlobalMedFiLM,
    FeatureWiseLinearModulation,
    GLOBAL_MEDFILM_ARCHITECTURE_ID,
    GLOBAL_MEDFILM_FILM_SITES,
    GLOBAL_MEDFILM_CHANNELS,
    GLOBAL_MEDFILM_TASK_EMBEDDING_DIM,
    GLOBAL_MEDFILM_FILM_HIDDEN_DIM,
)

__all__ = [
    "GlobalMedFiLM",
    "FeatureWiseLinearModulation",
    "GLOBAL_MEDFILM_ARCHITECTURE_ID",
    "GLOBAL_MEDFILM_FILM_SITES",
    "GLOBAL_MEDFILM_CHANNELS",
    "GLOBAL_MEDFILM_TASK_EMBEDDING_DIM",
    "GLOBAL_MEDFILM_FILM_HIDDEN_DIM",
]
