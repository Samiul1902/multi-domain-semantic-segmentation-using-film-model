"""Shared paths, registry access and helpers for the Phase-20B post-training chain.

This module exists so the four Phase-20B models can be post-processed with the
IDENTICAL methodology used for Phase-20A (UNet++), without duplicating it.

Design rules (governance)
-------------------------
* It never re-implements a metric, threshold or selection rule. Everything is
  imported from the frozen Phase-20 implementation:
    - ``src.training.phase20_selection``  (checkpoint selection rule)
    - ``src.metrics.evaluation_metrics``  (segmentation metrics + bootstrap)
    - ``src.analysis.phase20_baseline``   (tables / CIs / confusion / KUB strata)
    - ``scripts/training/train_phase20b_shared_baseline.MODEL_REGISTRY``
  so Phase-20B cannot drift from the frozen protocol.
* It writes ONLY to ``phase20b_``-prefixed artifacts. The Phase-20A (UNet++)
  artifacts keep their original names and are never overwritten.
* TEST is never referenced. VAL is the only split read.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
_TRAINING = ROOT / "scripts" / "training"
if str(_TRAINING) not in sys.path:
    sys.path.insert(0, str(_TRAINING))

# Re-export the single source of truth for model identity.
from train_phase20b_shared_baseline import MODEL_REGISTRY, ORDER, resolve_model_class  # noqa: E402,F401

PY = str(ROOT / ".venv" / "Scripts" / "python.exe")

AUDIT_DIR = ROOT / "reports" / "audits"
TABLE_DIR = ROOT / "reports" / "tables"
FIG_DIR = ROOT / "reports" / "figures" / "phase20b_multidomain_baselines"
PRED_ROOT = ROOT / "reports" / "predictions"
MANIFEST_DIR = ROOT / "manifests" / "phase4_v3"
PROTOCOL_PATH = AUDIT_DIR / "phase20_shared_global_baseline_protocol.json"

#: Phase-20A experiment, used as the reference row in the five-model comparison.
PHASE20A_EXPERIMENT_ID = "phase20_shared_unetpp_fourdomain_seed42_clean_v3"

NATURAL_STOP_REASONS = {"EARLY_STOPPING_PATIENCE", "MAX_EPOCHS"}


def experiment_id(model_key: str) -> str:
    return MODEL_REGISTRY[model_key]["experiment_id"]


def slug(model_key: str) -> str:
    return MODEL_REGISTRY[model_key]["binding_slug"]


def exp_dir(model_key: str) -> Path:
    return ROOT / "experiments" / experiment_id(model_key)


def ckpt_dir(model_key: str) -> Path:
    return ROOT / "checkpoints" / experiment_id(model_key)


def pred_root(model_key: str) -> Path:
    return PRED_ROOT / experiment_id(model_key)


# ---- per-model artifact names (phase20b_ prefixed; never clobber Phase-20A) ---- #
def replay_json(model_key: str) -> Path:
    return AUDIT_DIR / f"phase20b_{slug(model_key)}_checkpoint_selection_replay.json"


def closure_json(model_key: str) -> Path:
    return AUDIT_DIR / f"phase20b_{slug(model_key)}_training_closure.json"


def val_eval_json(model_key: str) -> Path:
    return AUDIT_DIR / f"phase20b_{slug(model_key)}_val_evaluation.json"


def prediction_manifest_json(model_key: str) -> Path:
    return AUDIT_DIR / f"phase20b_{slug(model_key)}_prediction_manifest.json"


def per_image_csv(model_key: str) -> Path:
    return TABLE_DIR / f"phase20b_{slug(model_key)}_per_image_val_metrics.csv"


def prediction_manifest_csv(model_key: str) -> Path:
    return TABLE_DIR / f"phase20b_{slug(model_key)}_prediction_manifest.csv"


# ---- shared five-model artifacts ---- #
FIVE_MODEL_COMPARISON_CSV = TABLE_DIR / "phase20b_five_model_comparison_final.csv"
PAIRED_BOOTSTRAP_CSV = TABLE_DIR / "phase20b_five_model_paired_bootstrap.csv"
FREEZE_JSON = AUDIT_DIR / "phase20_five_model_baseline_benchmark_freeze.json"
GALLERY_SELECTION_CSV = TABLE_DIR / "phase20b_gallery_selection.csv"
PER_IMAGE_ALL_CSV = TABLE_DIR / "phase20b_five_model_per_image_val_metrics.csv"

#: Reused verbatim from the frozen Phase-20 gallery contract so the SAME 64 VAL
#: cases carry across Phase-20A/20B and into Phase 21.
GALLERY_PER_DOMAIN = 16
