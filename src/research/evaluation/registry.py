"""The eight-model registry and the 24 model-seed cells.

The identifiers are the repository's own, taken from
:mod:`src.research.stage6.matrix` (which already owns the 24-cell matrix and its
acceptance gate) and :mod:`src.research.c3_baselines.experiment` (which already
owns the five external architectures).  No new model name is invented here.

This module adds only what the evaluator needs on top: an adapter kind per model
and a display order for reporting.  It deliberately does **not** re-implement
cell acceptance — that stays in ``matrix.validate_cell`` so there is exactly one
gate.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Tuple

from src.research.c3_baselines import experiment as C3
from src.research.stage6 import matrix as M

SEEDS: Tuple[int, ...] = M.SEEDS                       # (42, 123, 3407)
DOMAINS: Tuple[str, ...] = M.DOMAINS
TASK_IDS: Dict[str, int] = M.TASK_IDS

FULL = M.FULL
LITE = M.LITE
GLOBAL = M.GLOBAL
BASELINES = M.BASELINES
MODEL_KEYS = M.MODEL_KEYS

#: Reporting order, matching the mission's enumeration.
DISPLAY_ORDER: Tuple[str, ...] = (FULL, GLOBAL, LITE, *BASELINES)

#: Adapter kind.  ``ROUTED`` invokes the complete G/R/B/S graph through the
#: canonical GT-free state machine; ``TASK_CONDITIONED`` is the single
#: task-conditioned backbone; ``PLAIN`` is a single segmentation network.
ADAPTER_KINDS: Dict[str, str] = {
    FULL: "ROUTED",
    GLOBAL: "TASK_CONDITIONED",
    LITE: "ROUTED",
    **{key: "PLAIN" for key in BASELINES},
}

#: How each model consumes the task id.  A plain baseline has no task input at
#: all, so feeding it one would be a silent protocol difference rather than a
#: fairness improvement.
TAKES_TASK_ID: Dict[str, bool] = {
    FULL: True, GLOBAL: True, LITE: True,
    **{key: False for key in BASELINES},
}

C3_ARCHITECTURE_KEY: Dict[str, str] = {
    key: key.lower() for key in BASELINES
}

DISPLAY_NAME: Dict[str, str] = {
    FULL: "RA-MedFiLM-BARR (FULL)",
    GLOBAL: "GlobalMedFiLM",
    LITE: "RA-MedFiLM-BARR-Lite (depthwise_compact)",
    **{key: C3.ARCHITECTURES[key.lower()]["display_name"] for key in BASELINES},
}


class RegistryError(RuntimeError):
    pass


@dataclass(frozen=True)
class ModelSpec:
    """One registry row, resolved from the two canonical sources."""

    model_key: str
    display_name: str
    role: str
    adapter_kind: str
    takes_task_id: bool
    chain: Tuple[str, ...]
    producer: str

    def as_dict(self) -> Dict[str, Any]:
        return {"model_key": self.model_key, "display_name": self.display_name,
                "role": self.role, "adapter_kind": self.adapter_kind,
                "takes_task_id": self.takes_task_id, "chain": list(self.chain),
                "producer": self.producer,
                "c3_architecture_key": C3_ARCHITECTURE_KEY.get(self.model_key)}


def spec(model_key: str) -> ModelSpec:
    if model_key not in MODEL_KEYS:
        raise RegistryError(f"unknown model key {model_key!r}; known: {MODEL_KEYS}")
    entry = M.MODEL_REGISTRY[model_key]
    return ModelSpec(model_key=model_key, display_name=DISPLAY_NAME[model_key],
                     role=str(entry["role"]), adapter_kind=ADAPTER_KINDS[model_key],
                     takes_task_id=TAKES_TASK_ID[model_key],
                     chain=tuple(entry.get("chain", ())),
                     producer=str(entry.get("producer", "")))


def all_specs() -> Tuple[ModelSpec, ...]:
    return tuple(spec(key) for key in DISPLAY_ORDER)


def model_seed_cells() -> Tuple[Tuple[str, int], ...]:
    """The 24 (model, seed) cells in display order."""
    return tuple((model, seed) for model in DISPLAY_ORDER for seed in SEEDS)


def cell_id(model_key: str, seed: int) -> str:
    return f"{model_key}::seed{seed}"


def assert_complete_matrix() -> None:
    cells = model_seed_cells()
    if len(cells) != 24 or len(set(cells)) != 24:
        raise RegistryError(f"expected 24 distinct model-seed cells, got {len(cells)}")
    if set(model for model, _ in cells) != set(MODEL_KEYS):
        raise RegistryError("display order does not cover the canonical model keys")


def architecture_identity(model_key: str) -> Dict[str, Any]:
    """The architecture fact a checkpoint must match before it may be evaluated."""
    if model_key in (FULL, LITE):
        return {"kind": ADAPTER_KINDS[model_key], "chain": list(spec(model_key).chain),
                "requires_component_chain": True}
    if model_key == GLOBAL:
        return {"kind": "TASK_CONDITIONED", "architecture": "global_medfilm_film_5_sites",
                "requires_component_chain": False}
    arch = C3.ARCHITECTURES[C3_ARCHITECTURE_KEY[model_key]]
    return {"kind": "PLAIN", "architecture": arch["architecture"],
            "source_file": arch["source_file"], "class_name": arch["class_name"],
            "requires_component_chain": False}


assert_complete_matrix()

__all__ = ["ADAPTER_KINDS", "BASELINES", "C3_ARCHITECTURE_KEY", "DISPLAY_NAME",
           "DISPLAY_ORDER", "DOMAINS", "FULL", "GLOBAL", "LITE", "MODEL_KEYS",
           "ModelSpec", "RegistryError", "SEEDS", "TAKES_TASK_ID", "TASK_IDS",
           "all_specs", "architecture_identity", "assert_complete_matrix",
           "cell_id", "model_seed_cells", "spec"]
