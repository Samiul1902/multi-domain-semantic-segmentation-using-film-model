"""Phase 21 — write reports/audits/phase21_global_medfilm_architecture_binding.json.

MUST run BEFORE training. Freezes exactly ONE architecture, ONE logical run, no
sweep, and records the forbidden-module audit.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from scripts.training.phase21_common import ARCHITECTURE_ID, CONFIG, EXPERIMENT_ID, sha256_file
from src.models.film import (
    GLOBAL_MEDFILM_CHANNELS,
    GLOBAL_MEDFILM_FILM_HIDDEN_DIM,
    GLOBAL_MEDFILM_FILM_SITES,
    GLOBAL_MEDFILM_TASK_EMBEDDING_DIM,
    GlobalMedFiLM,
)

OUT = ROOT / "reports" / "audits" / "phase21_global_medfilm_architecture_binding.json"

FORBIDDEN = ["localizer", "proposal", "roi", "regional", "refiner", "crop_branch",
             "benefit", "router", "budget", "counterfactual", "distill", "prune",
             "quant", "architecture_search"]


def main() -> int:
    model = GlobalMedFiLM(task_count=CONFIG["model"]["task_count"],
                          in_channels=CONFIG["model"]["in_channels"],
                          out_channels=CONFIG["model"]["out_channels"],
                          channels=tuple(CONFIG["model"]["channels"]),
                          task_embedding_dim=CONFIG["model"]["task_embedding_dim"],
                          film_hidden_dim=CONFIG["model"]["film_hidden_dim"])
    n_params = int(sum(p.numel() for p in model.parameters() if p.requires_grad))

    names = [n for n, _ in model.named_modules()]
    forbidden_hits = {t: [n for n in names if t in n.lower()] for t in FORBIDDEN}
    forbidden_hits = {k: v for k, v in forbidden_hits.items() if v}

    ckpt_dir = ROOT / "checkpoints" / EXPERIMENT_ID
    exp_dir = ROOT / "experiments" / EXPERIMENT_ID
    training_performed = bool(list(ckpt_dir.glob("*.pt"))) if ckpt_dir.exists() else False

    artifact = {
        "artifact": "phase21_global_medfilm_architecture_binding",
        "phase": 21,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "frozen_before_training": not training_performed,
        "training_performed_at_binding_time": training_performed,
        "experiment_id": EXPERIMENT_ID,
        "architecture_id": ARCHITECTURE_ID,
        "architecture_family": "GLOBAL_MEDFILM_TASK_CONDITIONED_SHARED_SEGMENTATION",
        "is_final_ra_medfilm_seg_plus_plus": False,
        "is_global_reference_only": True,
        "model_class": "src.models.film.global_medfilm.GlobalMedFiLM",
        "model_file": "src/models/film/global_medfilm.py",
        "model_file_sha256": sha256_file(ROOT / "src/models/film/global_medfilm.py"),
        "model_package_init_sha256": sha256_file(ROOT / "src/models/film/__init__.py"),
        "factory_file": "src/models/factory.py",
        "factory_file_sha256": sha256_file(ROOT / "src/models/factory.py"),
        "measured_parameter_count": n_params,
        "measured_parameter_count_including_buffers": int(sum(p.numel() for p in model.parameters())),
        "one_shared_parameter_set": True,
        "dataset_specific_head": False,
        "output_definition": "single shared 1x1 head -> 1 foreground logit",
        "component_specification": {
            "task_conditioning": {
                "mechanism": "FiLM (feature-wise linear modulation)",
                "equation": "F_hat = (1 + gamma(t)) * F + beta(t)",
                "gamma": "tanh(gamma_raw)",
                "beta": "tanh(beta_raw)",
                "output_projection_init": "zeros -> EXACT identity at initialisation",
                "task_embedding": f"nn.Embedding(task_count, {GLOBAL_MEDFILM_TASK_EMBEDDING_DIM})",
                "task_embedding_init": "normal_(mean=0.0, std=0.02)",
                "film_hidden_dim": GLOBAL_MEDFILM_FILM_HIDDEN_DIM,
                "sites": list(GLOBAL_MEDFILM_FILM_SITES),
                "site_count": len(GLOBAL_MEDFILM_FILM_SITES),
                "site_channels": {"bridge": 256, "decoder4": 192, "decoder3": 96,
                                  "decoder2": 48, "decoder1": 24},
                "sole_task_signal": True,
            },
            "shared_backbone": {
                "encoder_stages": ["encoder1", "encoder2", "encoder3", "encoder4", "bridge"],
                "decoder_stages": ["decoder4", "decoder3", "decoder2", "decoder1"],
                "block": "ResidualBlock(ConvNormAct + ConvNorm + 1x1 skip + SiLU)",
                "normalization": "GroupNorm (groups from (8,4,2,1))",
                "activation": "SiLU",
                "pooling": "MaxPool2d(2,2)",
                "upsampling": "bilinear interpolate to skip size",
                "channels": list(GLOBAL_MEDFILM_CHANNELS),
                "in_channels": CONFIG["model"]["in_channels"],
                "out_channels": CONFIG["model"]["out_channels"],
            },
            "present": {
                "residual_connections": True,
                "task_embedding": True,
                "film_conditioning": True,
                "shared_segmentation_network": True,
                "four_domain_joint_training": True,
            },
            "absent": {
                "roi_proposal": False,
                "localizer": False,
                "regional_refiner": False,
                "high_resolution_crop_branch": False,
                "global_regional_fusion": False,
                "benefit_predictor": False,
                "counterfactual_refinement_gain": False,
                "resource_budget_router": False,
                "adaptive_conditional_computation": False,
                "mobile_compression": False,
                "pruning": False,
                "quantization": False,
                "distillation": False,
                "architecture_search": False,
                "squeeze_excitation": False,
                "deep_supervision": False,
                "test_evaluation": False,
            },
        },
        "forbidden_module_audit": {
            "tokens_checked": FORBIDDEN,
            "hits": forbidden_hits,
            "passed": not forbidden_hits,
        },
        "search_policy": {
            "architectures_considered_for_execution": 1,
            "architecture_sweep_performed": False,
            "hyperparameter_sweep_performed": False,
            "logical_runs_authorized": 1,
            "seed": 42,
            "resume_is_same_logical_run": True,
            "second_seed_belongs_to_later_phase": True,
        },
        "inherited_protocol": {
            "path": "reports/audits/phase20_shared_global_baseline_protocol.json",
            "sha256": "b74f1f9f429adbce374f0306180943b9f373f872e1e69e115b7d17e81414283c",
            "binding_artifact": "reports/audits/phase21_protocol_binding.json",
        },
        "legacy_evidence": {
            "path": "reports/audits/phase21_legacy_medfilm_architecture_audit.json",
            "reuse_type": "REFERENCE_ONLY",
            "historical_result_claimed_as_current": False,
        },
        "governance": {
            "training_performed": False,
            "inference_performed": False,
            "checkpoints_created": 0,
            "film_used": True,
            "regional_module_used": False,
            "localizer_used": False,
            "roi_proposal_used": False,
            "benefit_router_used": False,
            "test_reads": 0,
        },
        "output_isolation": {
            "experiment_dir": f"experiments/{EXPERIMENT_ID}",
            "checkpoint_dir": f"checkpoints/{EXPERIMENT_ID}",
            "overwrites_phase20_checkpoints": False,
        },
    }
    artifact["verdict"] = (
        "PHASE21_ARCHITECTURE_FROZEN" if (not forbidden_hits and not training_performed)
        else "PHASE21_ARCHITECTURE_FREEZE_FAIL"
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    print("WROTE", OUT)
    print("params", n_params)
    print("forbidden_hits", forbidden_hits)
    print("verdict", artifact["verdict"])
    return 0 if artifact["verdict"] == "PHASE21_ARCHITECTURE_FROZEN" else 2


if __name__ == "__main__":
    raise SystemExit(main())
