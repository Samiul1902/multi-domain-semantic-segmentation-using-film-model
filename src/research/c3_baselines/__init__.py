"""Controlled, synthetic-smoke-only C3 baseline experiment preparation."""

from .experiment import (
    ARCHITECTURES,
    C3ExecutionError,
    aggregate_controlled_results,
    build_experiment_config,
    build_model,
    evaluate_best_checkpoint,
    make_synthetic_loaders,
    train_run,
    write_empty_results_schema,
)

__all__ = [
    "ARCHITECTURES",
    "C3ExecutionError",
    "aggregate_controlled_results",
    "build_experiment_config",
    "build_model",
    "evaluate_best_checkpoint",
    "make_synthetic_loaders",
    "train_run",
    "write_empty_results_schema",
]
