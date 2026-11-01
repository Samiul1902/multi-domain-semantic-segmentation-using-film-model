"""Matched C3 baseline runner.

The CLI only permits synthetic smoke runs. Real-data execution is deliberately
blocked until a separately reviewed C3 execution authorization exists.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import pickle
import random
import tempfile
import time
from pathlib import Path
from typing import Any, Callable, Iterable

import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset

from scripts.training.phase21_common import per_image_dice_iou_precision_recall
from src.data.domain_balanced_sampler import (
    BALANCED_SAMPLING_POLICY_ID,
    build_domain_balanced_sampler,
    derive_epoch_seed,
)
from src.losses.segmentation import BCEDiceLoss
from src.metrics.segmentation import hd95 as binary_hd95
from src.training.phase20_selection import (
    DOMAIN_ORDER,
    SELECTION_RULE_ID,
    is_new_best,
    macro_domain_dice,
    select_best_epoch,
)

ROOT = Path(__file__).resolve().parents[3]
PROTOCOL_PATH = ROOT / "reports" / "planning" / "c1_film_attribution_v1" / "protocol.json"
EXPECTED_PROTOCOL_SHA256 = "531e3eb255a66381201d1aaf49bbe55abfdbe529640f5c584ef100d298087a61"
MANIFEST_TRAIN = ROOT / "manifests" / "phase4_v3" / "train.csv"
MANIFEST_VAL = ROOT / "manifests" / "phase4_v3" / "val.csv"
EXPECTED_SEEDS = (42, 123, 3407)
EXPECTED_COUNTS = {"TRAIN": 5832, "VAL": 808}
BASE_CHANNELS = 32


class C3ExecutionError(RuntimeError):
    """Raised when an artifact, run, or execution precondition is invalid."""


ARCHITECTURES: dict[str, dict[str, str]] = {
    "unet": {
        "display_name": "U-Net",
        "class_name": "UNet",
        "module": "src.models.unet",
        "source_file": "src/models/unet.py",
        "architecture": "unet_4_stage_plain_skip_base32",
        "historical_experiment": "phase20b_shared_unet_fourdomain_seed42_clean_v3",
        "historical_config": "experiments/phase20b_shared_unet_fourdomain_seed42_clean_v3/config.json",
        "historical_closure": "reports/audits/phase20b_unet_training_closure.json",
        "historical_architecture_detail": "four encoder/decoder stages; concatenative plain skips",
        "historical_params": "7,763,041",
    },
    "attention_unet": {
        "display_name": "Attention U-Net",
        "class_name": "AttentionUNet",
        "module": "src.models.attention_unet",
        "source_file": "src/models/attention_unet.py",
        "architecture": "attention_unet_4_stage_additive_skip_gates_base32",
        "historical_experiment": "phase20b_shared_attention_unet_fourdomain_seed42_clean_v3",
        "historical_config": "experiments/phase20b_shared_attention_unet_fourdomain_seed42_clean_v3/config.json",
        "historical_closure": "reports/audits/phase20b_attention_unet_training_closure.json",
        "historical_architecture_detail": "four additive attention gates on encoder skips",
        "historical_params": "7,851,285",
    },
    "deeplabv3plus": {
        "display_name": "DeepLabV3+",
        "class_name": "DeepLabV3Plus",
        "module": "src.models.deeplabv3plus",
        "source_file": "src/models/deeplabv3plus.py",
        "architecture": "deeplabv3plus_resnet50_os16_random_init_aspp_6_12_18",
        "historical_experiment": "phase20b_shared_deeplabv3plus_fourdomain_seed42_clean_v3",
        "historical_config": "experiments/phase20b_shared_deeplabv3plus_fourdomain_seed42_clean_v3/config.json",
        "historical_closure": "reports/audits/phase20b_deeplabv3plus_training_closure.json",
        "historical_architecture_detail": "random-init ResNet-50 OS16 encoder, ASPP rates 6/12/18, low-level decoder",
        "historical_params": "40,347,041",
    },
    "transformer_mit_unet": {
        "display_name": "Transformer/MiT-style U-Net",
        "class_name": "TransformerMiTUNet",
        "module": "src.models.transformer_mit_unet",
        "source_file": "src/models/transformer_mit_unet.py",
        "architecture": "mit_style_transformer_encoder_unet_decoder_random_init",
        "historical_experiment": "phase20b_shared_transformer_mit_unet_fourdomain_seed42_clean_v3",
        "historical_config": "experiments/phase20b_shared_transformer_mit_unet_fourdomain_seed42_clean_v3/config.json",
        "historical_closure": "reports/audits/phase20b_transformer_mit_unet_training_closure.json",
        "historical_architecture_detail": "random-init MiT-style transformer stages with U-Net decoder",
        "historical_params": "16,347,777",
    },
    "unetpp": {
        "display_name": "U-Net++",
        "class_name": "UNetPlusPlus",
        "module": "src.models.unetpp",
        "source_file": "src/models/unetpp.py",
        "architecture": "unetpp_4_level_nested_dense_skip_base32_single_head",
        "historical_experiment": "phase20_shared_unetpp_fourdomain_seed42_clean_v3",
        "historical_config": "experiments/phase20_shared_unetpp_fourdomain_seed42_clean_v3/config.json",
        "historical_closure": "reports/audits/phase20_training_closure.json",
        "historical_architecture_detail": "four-level nested dense skip connections; one segmentation head",
        "historical_params": "9,159,681",
    },
}

FULL_MODEL_KEY = "ra_medfilm_barr_full"
FULL_MODEL_IDENTITY = "RA-MedFiLM-BARR (FULL)"
EXTERNAL_BASELINE_KEYS = (
    "unet",
    "unetpp",
    "attention_unet",
    "deeplabv3plus",
    "transformer_mit_unet",
)
EXPERIMENT_MODEL_KEYS = (FULL_MODEL_KEY, *EXTERNAL_BASELINE_KEYS)
REFERENCE_ARM = FULL_MODEL_IDENTITY
TASK_IDS = {"ISIC": 0, "BUSI": 1, "KVASIR": 2, "KUB": 3}
FULL_MODEL_COMPONENTS = ("G", "R_psi", "B_phi", "S_omega", "routing_fusion")
FULL_MODEL_PARAMETER_COUNTS = {
    "G": 3_523_001,
    "R_psi": 1_276_401,
    "B_phi": 36_801,
    "S_omega": 1_217,
}
FULL_MODEL_PARAMETER_COUNT = sum(FULL_MODEL_PARAMETER_COUNTS.values())
FULL_MODEL_BUNDLE_SCHEMA = "ra_medfilm_barr_full_bundle_v1"
RECIPE: dict[str, Any] = {
    "source": "C1 frozen protocol recipe; copied for prospective C3 baseline matching",
    "resolution": 512,
    "channels": 3,
    "channel_policy": "RGB_3CH",
    "loss": {"name": "BCE+soft Dice", "bce_weight": 0.5, "dice_weight": 0.5, "epsilon": 1e-6},
    "optimizer": {"name": "AdamW", "learning_rate": 1e-4, "weight_decay": 1e-4},
    "scheduler": {"name": "CosineAnnealingLR", "T_max": 100, "step_after_epoch": True},
    "batch_size": 4,
    "eval_batch_size": 8,
    "max_epochs": 100,
    "early_stopping_patience": 15,
    "amp": True,
    "threshold": 0.5,
    "sampling_policy": BALANCED_SAMPLING_POLICY_ID,
    "augmentation": "canonical SegmentationTransform(train=True), horizontal flip/rotation/brightness/contrast; mask nearest",
    "model_inputs": "image only; domain/task id is sampling/bookkeeping, never model input",
    "selection_rule": SELECTION_RULE_ID,
    "selection_tie_break": "lower validation loss, then earlier epoch",
    "seeds": list(EXPECTED_SEEDS),
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump(payload, f, indent=2, sort_keys=True, allow_nan=False)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


def build_experiment_config(model_key: str, seed: int) -> dict[str, Any]:
    if model_key not in EXPERIMENT_MODEL_KEYS:
        raise C3ExecutionError(f"Unknown C3 architecture: {model_key}")
    if seed not in EXPECTED_SEEDS:
        raise C3ExecutionError(f"Seed must be one of {EXPECTED_SEEDS}, got {seed}")
    if sha256_file(PROTOCOL_PATH) != EXPECTED_PROTOCOL_SHA256:
        raise C3ExecutionError("Frozen C1 protocol digest mismatch; refusing to build C3 config")
    validate_manifest_contract()
    if model_key == FULL_MODEL_KEY:
        return {
            "schema": "controlled_c3_run_config_v2",
            "study_id": "C3_FULL_METHOD_VS_EXTERNAL_BASELINES_V1",
            "model_key": FULL_MODEL_KEY,
            "model": {
                "display_name": FULL_MODEL_IDENTITY,
                "architecture": "GlobalMedFiLM -> B_phi route -> R_psi ROI refinement -> S_omega acceptance -> regional replacement fusion",
                "component_keys": list(FULL_MODEL_COMPONENTS),
                "parameter_count": FULL_MODEL_PARAMETER_COUNT,
                "component_parameter_counts": FULL_MODEL_PARAMETER_COUNTS,
            },
            "role": "PRIMARY_PROPOSED_METHOD",
            "seed": seed,
            "dataset": {
                "manifest_version": "phase4_v3",
                "train_manifest": "manifests/phase4_v3/train.csv",
                "val_manifest": "manifests/phase4_v3/val.csv",
                "train_n": EXPECTED_COUNTS["TRAIN"],
                "val_n": EXPECTED_COUNTS["VAL"],
                "domains": list(DOMAIN_ORDER),
                "task_ids": TASK_IDS,
                "train_manifest_sha256": sha256_file(MANIFEST_TRAIN),
                "val_manifest_sha256": sha256_file(MANIFEST_VAL),
                "test_access": False,
                "external_access": False,
            },
            "protocol": {"path": "reports/planning/c1_film_attribution_v1/protocol.json",
                         "sha256": EXPECTED_PROTOCOL_SHA256},
            "selection": {
                "primary_metric": "equal-domain macro VAL Dice",
                "same_rule_for_all_models": True,
                "population_role": "selection-consumed VAL808",
                "tie_break": "lower validation loss, then earlier epoch",
            },
            "component_dependencies": {
                "required": list(FULL_MODEL_COMPONENTS),
                "same_master_seed": seed,
                "global_backbone_seed": seed,
                "downstream_training_must_bind_exact_global_checkpoint": True,
                "router_must_bind_exact_global_and_refiner_family": True,
                "safety_must_bind_exact_global_refiner_router_family": True,
                "normalization_statistics_must_be_component_bound": True,
                "phase29_fixed_global_seed42_artifacts_are_not_end_to_end_seed_replicates": True,
                "training_order": ["G", "R_psi", "B_phi", "S_omega", "full_system_validation"],
            },
            "architecture_specific_difference": {
                "task_conditioning": "learned task-conditioned FiLM in G; task identity also enters B_phi/S_omega as specified",
                "regional_modules": ["R_psi", "B_phi", "S_omega"],
                "execution": "conditional; final mask is the canonical fused full-system output",
                "checkpoint_family": "new per-seed compatible full-system bundle required",
            },
            "existing_phase29_evidence": {
                "classification": "DOWNSTREAM_REPRODUCIBILITY_CONDITIONED_ON_FIXED_GLOBAL",
                "global_backbone_seed": 42,
                "counts_as_end_to_end_c3_cell": False,
            },
            "run_mode": "PREPARED_NOT_EXECUTED",
        }
    spec = ARCHITECTURES[model_key]
    source = ROOT / spec["source_file"]
    closure_path = ROOT / spec["historical_closure"]
    historical_config_path = ROOT / spec["historical_config"]
    try:
        closure = json.loads(closure_path.read_text(encoding="utf-8"))
        historical_config = json.loads(historical_config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise C3ExecutionError(f"historical config/closure missing or corrupt for {model_key}: {exc}") from exc
    if closure.get("experiment_id") != spec["historical_experiment"]:
        raise C3ExecutionError(f"historical checkpoint closure identity mismatch: {model_key}")
    if historical_config.get("experiment_id") != spec["historical_experiment"] or historical_config.get("training", {}).get("seed") != 42:
        raise C3ExecutionError(f"historical configuration identity/seed mismatch: {model_key}")
    historical_checkpoint_path = ROOT / str(closure.get("best_checkpoint_path", ""))
    if (not source.is_file() or not historical_checkpoint_path.is_file()
            or not closure.get("best_checkpoint_sha256")):
        raise C3ExecutionError(f"historical source/checkpoint provenance incomplete: {model_key}")
    return {
        "schema": "controlled_c3_run_config_v2",
        "study_id": "C3_FULL_METHOD_VS_EXTERNAL_BASELINES_V1",
        "model_key": model_key,
        "role": "EXTERNAL_ARCHITECTURE_BASELINE",
        "model": {
            "display_name": spec["display_name"],
            "class_name": spec["class_name"],
            "architecture": spec["architecture"],
            "architecture_detail": spec["historical_architecture_detail"],
            "in_channels": 3,
            "out_channels": 1,
            "base_channels": BASE_CHANNELS,
        },
        "seed": seed,
        "primary_comparator": FULL_MODEL_IDENTITY,
        "dataset": {
            "manifest_version": "phase4_v3",
            "train_manifest": "manifests/phase4_v3/train.csv",
            "val_manifest": "manifests/phase4_v3/val.csv",
            "train_n": EXPECTED_COUNTS["TRAIN"],
            "val_n": EXPECTED_COUNTS["VAL"],
            "domains": list(DOMAIN_ORDER),
            "task_ids": TASK_IDS,
            "train_manifest_sha256": sha256_file(MANIFEST_TRAIN),
            "val_manifest_sha256": sha256_file(MANIFEST_VAL),
            "test_access": False,
            "external_access": False,
        },
        "protocol": {"path": "reports/planning/c1_film_attribution_v1/protocol.json",
                     "sha256": EXPECTED_PROTOCOL_SHA256},
        "recipe": RECIPE,
        "architecture_specific_difference": {
            "parameterization": spec["architecture"],
            "pretrained_weights": False,
            "task_conditioning": False,
            "regional_modules": False,
        },
        "source": {
            "model_source": spec["source_file"],
            "model_source_sha256": sha256_file(source),
            "historical_experiment": spec["historical_experiment"],
            "historical_checkpoint": closure["best_checkpoint_path"],
            "historical_checkpoint_sha256_recorded": closure["best_checkpoint_sha256"],
            "historical_checkpoint_seed": 42,
            "historical_best_epoch": int(closure["best_epoch"]),
            "historical_closure": spec["historical_closure"],
            "historical_closure_sha256": sha256_file(closure_path),
            "historical_config": spec["historical_config"],
            "historical_config_sha256": sha256_file(historical_config_path),
            "historical_recipe": historical_config,
            "historical_parameter_count_reported": spec["historical_params"],
        },
        "run_mode": "PREPARED_NOT_EXECUTED",
    }


def validate_manifest_contract() -> dict[str, Any]:
    """Validate metadata-only TRAIN/VAL membership against the frozen C1 protocol."""
    for path, split in ((MANIFEST_TRAIN, "TRAIN"), (MANIFEST_VAL, "VAL")):
        if not path.is_file():
            raise C3ExecutionError(f"required manifest missing: {path.name}")
    expected_hashes = {
        "TRAIN": "28702fc3a5ff8b950db372f03232d335e3a30b1fc2f21db7cd8c066055826ed6",
        "VAL": "082c80b2bda63fd73f371f109c34643adf01edaead921643fb2e44993ba53315",
    }
    frames: dict[str, pd.DataFrame] = {}
    for path, split in ((MANIFEST_TRAIN, "TRAIN"), (MANIFEST_VAL, "VAL")):
        if sha256_file(path) != expected_hashes[split]:
            raise C3ExecutionError(f"{split} manifest digest mismatch")
        frame = pd.read_csv(path)
        if len(frame) != EXPECTED_COUNTS[split] or frame["split"].astype(str).str.upper().ne(split).any():
            raise C3ExecutionError(f"{split} membership/row count mismatch")
        required = {"sample_id", "dataset", "task_id", "split"}
        if not required.issubset(frame.columns) or frame["sample_id"].duplicated().any():
            raise C3ExecutionError(f"{split} manifest columns or IDs are invalid")
        mapping = TASK_IDS
        if set(frame["dataset"].astype(str)) != set(DOMAIN_ORDER):
            raise C3ExecutionError(f"{split} domain roster mismatch")
        if any(mapping.get(str(d)) != int(t) for d, t in zip(frame["dataset"], frame["task_id"])):
            raise C3ExecutionError(f"{split} task-id mapping mismatch")
        frames[split] = frame
    overlap = set(frames["TRAIN"]["sample_id"].astype(str)) & set(frames["VAL"]["sample_id"].astype(str))
    if overlap:
        raise C3ExecutionError(f"TRAIN/VAL overlap detected: {len(overlap)} IDs")
    return {
        "train_n": len(frames["TRAIN"]),
        "val_n": len(frames["VAL"]),
        "train_domains": {str(k): int(v) for k, v in frames["TRAIN"]["dataset"].value_counts().items()},
        "val_domains": {str(k): int(v) for k, v in frames["VAL"]["dataset"].value_counts().items()},
        "train_val_overlap": 0,
    }


def build_model(model_key: str, *, base_channels: int = BASE_CHANNELS) -> nn.Module:
    if model_key not in ARCHITECTURES:
        raise C3ExecutionError(f"Unknown C3 architecture: {model_key}")
    import importlib
    spec = ARCHITECTURES[model_key]
    cls = getattr(importlib.import_module(spec["module"]), spec["class_name"])
    return cls(in_channels=3, out_channels=1, base_channels=base_channels)


def parameter_count(model: nn.Module) -> int:
    return sum(int(p.numel()) for p in model.parameters() if p.requires_grad)


def estimate_optimizer_checkpoint_bytes(trainable_parameters: int) -> int:
    """Approximate two float32 checkpoints with Adam moments, excluding metadata."""
    if trainable_parameters <= 0:
        raise C3ExecutionError("parameter count must be positive")
    return int(trainable_parameters * 4 * (1 + 2) * 2)


def analytical_macs_lower_bound(model: nn.Module, input_shape: tuple[int, int, int, int]) -> dict[str, Any]:
    """Count Conv2d/Linear MACs; transformer attention matmuls are excluded."""
    macs = 0
    handles = []

    def hook(module: nn.Module, inputs: tuple[Any, ...], output: torch.Tensor) -> None:
        nonlocal macs
        if isinstance(module, nn.Conv2d):
            out = output
            kernel = module.kernel_size[0] * module.kernel_size[1]
            macs += int(out.numel() * (module.in_channels // module.groups) * kernel)
        elif isinstance(module, nn.Linear):
            macs += int(output.numel() * module.in_features)

    for module in model.modules():
        if isinstance(module, (nn.Conv2d, nn.Linear)):
            handles.append(module.register_forward_hook(hook))
    was_training = model.training
    model.eval()
    try:
        with torch.no_grad():
            parameter = next(model.parameters())
            model(torch.zeros(input_shape, device=parameter.device, dtype=parameter.dtype))
    finally:
        for handle in handles:
            handle.remove()
        model.train(was_training)
    return {
        "macs_lower_bound": macs,
        "gmacs_lower_bound": macs / 1e9,
        "method": "Conv2d+Linear hooks; excludes attention tensor matmuls and non-learned ops",
        "input_shape": list(input_shape),
    }


class SyntheticSegmentationDataset(Dataset):
    """Deterministic synthetic-only smoke data; never accepted as research evidence."""

    def __init__(self, split: str, *, size: int = 64, samples_per_domain: int = 2, seed: int = 42):
        if split not in ("TRAIN", "VAL"):
            raise C3ExecutionError("Synthetic dataset only supports TRAIN and VAL")
        if size < 16 or size % 16:
            raise C3ExecutionError("Synthetic image size must be >=16 and divisible by 16")
        self.split, self.size, self.seed = split, size, seed
        self.rows = [(domain, i) for domain in DOMAIN_ORDER for i in range(samples_per_domain)]

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int) -> dict[str, Any]:
        domain, local_index = self.rows[index]
        domain_index = DOMAIN_ORDER.index(domain)
        generator = torch.Generator().manual_seed(self.seed + domain_index * 1009 + local_index)
        image = torch.rand((3, self.size, self.size), generator=generator)
        mask = torch.zeros((1, self.size, self.size), dtype=torch.float32)
        margin = max(2, self.size // 8)
        y = margin + (local_index % max(1, self.size // 4))
        x = margin + (domain_index % max(1, self.size // 4))
        extent = max(3, self.size // 4)
        mask[:, y:y + extent, x:x + extent] = 1.0
        return {
            "image": image,
            "mask": mask,
            "dataset": domain,
            "task_id": domain_index,
            "sample_id": f"SYNTHETIC:{self.split}:{domain}:{local_index}",
            "split": self.split,
        }


def _collate(samples: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "image": torch.stack([x["image"] for x in samples]),
        "mask": torch.stack([x["mask"] for x in samples]),
        "dataset": [x["dataset"] for x in samples],
        "task_id": torch.tensor([x["task_id"] for x in samples], dtype=torch.long),
        "sample_id": [x["sample_id"] for x in samples],
        "split": [x["split"] for x in samples],
    }


def make_synthetic_loaders(
    seed: int, *, image_size: int = 64, samples_per_domain: int = 2, batch_size: int = 2
) -> tuple[Callable[[int], DataLoader], DataLoader]:
    train_ds = SyntheticSegmentationDataset("TRAIN", size=image_size, samples_per_domain=samples_per_domain, seed=seed)
    val_ds = SyntheticSegmentationDataset("VAL", size=image_size, samples_per_domain=samples_per_domain, seed=seed + 1)

    def train_factory(epoch: int) -> DataLoader:
        sampler = build_domain_balanced_sampler([d for d, _ in train_ds.rows], seed, epoch)
        return DataLoader(train_ds, batch_size=batch_size, sampler=sampler, collate_fn=_collate, num_workers=0)

    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, collate_fn=_collate, num_workers=0)
    return train_factory, val_loader


def _seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def _validate_batch(batch: dict[str, Any], split: str) -> None:
    n = len(batch["sample_id"])
    if any(len(batch[k]) != n for k in ("dataset", "split")):
        raise C3ExecutionError("batch metadata length mismatch")
    if any(str(s) != split for s in batch["split"]):
        raise C3ExecutionError(f"expected {split} batch")
    if tuple(batch["image"].shape[1:]) != (3, batch["image"].shape[-2], batch["image"].shape[-1]):
        raise C3ExecutionError("expected three-channel image tensor")
    if batch["mask"].shape != (n, 1, *batch["image"].shape[-2:]):
        raise C3ExecutionError("mask shape does not match image batch")
    if not torch.isfinite(batch["image"]).all() or not torch.isfinite(batch["mask"]).all():
        raise C3ExecutionError("nonfinite image or mask")
    if not torch.isin(batch["mask"], torch.tensor([0.0, 1.0], device=batch["mask"].device)).all():
        raise C3ExecutionError("mask targets must be binary")
    if any(d not in DOMAIN_ORDER for d in batch["dataset"]):
        raise C3ExecutionError("unknown dataset domain")


@torch.no_grad()
def _evaluate(model: nn.Module, loader: Iterable[dict[str, Any]], criterion: nn.Module,
              device: torch.device, threshold: float, amp: bool, *,
              include_hd95: bool = False) -> tuple[float, dict[str, dict[str, Any]], list[dict[str, Any]]]:
    model.eval()
    losses: list[float] = []
    records: list[dict[str, Any]] = []
    for batch in loader:
        _validate_batch(batch, "VAL")
        images = batch["image"].to(device)
        masks = batch["mask"].to(device)
        with torch.amp.autocast(device_type=device.type, enabled=amp):
            logits = model(images)
            loss = criterion(logits, masks)
        if not torch.isfinite(loss):
            raise C3ExecutionError("nonfinite validation loss")
        losses.append(float(loss.item()))
        metrics = per_image_dice_iou_precision_recall(logits, masks, threshold)
        for i, sample_id in enumerate(batch["sample_id"]):
            record: dict[str, Any] = {
                "sample_id": str(sample_id),
                "domain": str(batch["dataset"][i]),
                "task_id": int(batch["task_id"][i]),
                "split": str(batch["split"][i]),
                **{name: float(value[i].detach().cpu()) for name, value in metrics.items()},
            }
            if include_hd95:
                prediction = torch.sigmoid(logits[i, 0]).ge(threshold).cpu().numpy()
                target = masks[i, 0].bool().cpu().numpy()
                boundary = binary_hd95(prediction, target)
                record["hd95"] = boundary["hd95"] if boundary["hd95_valid"] else None
                record["hd95_undefined_reason"] = (
                    None if boundary["hd95_valid"] else boundary["invalid_reason"]
                )
            records.append(record)
    if not records or len({r["sample_id"] for r in records}) != len(records):
        raise C3ExecutionError("empty or duplicate validation sample IDs")
    per_domain: dict[str, dict[str, Any]] = {}
    for domain in DOMAIN_ORDER:
        subset = [r for r in records if r["domain"] == domain]
        if not subset:
            raise C3ExecutionError(f"validation domain missing: {domain}")
        per_domain[domain] = {
            key: float(np.mean([r[key] for r in subset]))
            for key in ("dice", "iou", "precision", "recall")
        }
        if include_hd95:
            defined_hd95 = [r["hd95"] for r in subset if r["hd95"] is not None]
            per_domain[domain]["hd95"] = (
                float(np.mean(defined_hd95)) if defined_hd95 else None
            )
            per_domain[domain]["hd95_n_defined"] = len(defined_hd95)
    return float(np.mean(losses)), per_domain, records


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise C3ExecutionError(f"refusing to write empty CSV: {path.name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def train_run(
    model_key: str,
    seed: int,
    train_loader_factory: Callable[[int], Iterable[dict[str, Any]]],
    val_loader: Iterable[dict[str, Any]],
    output_dir: Path,
    *,
    epochs: int = 1,
    device: str | torch.device = "cpu",
    synthetic: bool,
    resume: bool = False,
    base_channels: int = BASE_CHANNELS,
    amp: bool | None = None,
) -> dict[str, Any]:
    """Train one run from supplied loaders; real runs require an opaque grant."""
    if not synthetic:
        raise C3ExecutionError("C3_REAL_EXECUTION_BLOCKED_PENDING_SEPARATE_AUTHORIZATION")
    if epochs <= 0:
        raise C3ExecutionError("epochs must be positive")
    if seed not in EXPECTED_SEEDS or model_key not in ARCHITECTURES:
        raise C3ExecutionError("invalid model key or seed")
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    config = build_experiment_config(model_key, seed)
    config["run_mode"] = "SYNTHETIC_ONLY"
    config["smoke_overrides"] = {"base_channels": base_channels}
    config_digest = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()
    device_t = torch.device(device)
    amp_enabled = bool(RECIPE["amp"] if amp is None else amp) and device_t.type == "cuda"
    if device_t.type == "cuda" and not torch.cuda.is_available():
        raise C3ExecutionError("CUDA requested but unavailable")

    _seed_everything(seed)
    model = build_model(model_key, base_channels=base_channels).to(device_t)
    optimizer = torch.optim.AdamW(model.parameters(), lr=RECIPE["optimizer"]["learning_rate"],
                                  weight_decay=RECIPE["optimizer"]["weight_decay"])
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=RECIPE["scheduler"]["T_max"])
    scaler = torch.amp.GradScaler("cuda", enabled=amp_enabled)
    criterion = BCEDiceLoss(0.5, 0.5, 1e-6)
    history_path = out / "history.jsonl"
    latest_path, best_path = out / "latest.pt", out / "best.pt"
    history: list[dict[str, Any]] = []
    start_epoch, best_macro, best_loss, best_epoch, bad_epochs = 1, -math.inf, math.inf, 0, 0
    if resume:
        if not latest_path.is_file() or not history_path.is_file():
            raise C3ExecutionError("resume requires both latest.pt and history.jsonl")
        try:
            checkpoint = torch.load(latest_path, map_location="cpu", weights_only=False)
            if checkpoint.get("config_sha256") != config_digest or checkpoint.get("model_key") != model_key or checkpoint.get("seed") != seed:
                raise C3ExecutionError("resume configuration/model/seed mismatch")
            model.load_state_dict(checkpoint["model_state"], strict=True)
            optimizer.load_state_dict(checkpoint["optimizer_state"])
            scheduler.load_state_dict(checkpoint["scheduler_state"])
            scaler.load_state_dict(checkpoint["scaler_state"])
            checkpoint_history = checkpoint["history_rows"]
            if len(checkpoint_history) != int(checkpoint["epoch"]) or [r["epoch"] for r in checkpoint_history] != list(range(1, len(checkpoint_history) + 1)):
                raise C3ExecutionError("checkpoint history is incomplete or non-contiguous")
            try:
                with history_path.open(encoding="utf-8") as f:
                    disk_history = [json.loads(line) for line in f if line.strip()]
            except (OSError, json.JSONDecodeError):
                disk_history = []
            history = checkpoint_history
            if disk_history != history:
                with history_path.open("w", encoding="utf-8", newline="\n") as f:
                    for row in history:
                        f.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")
            start_epoch = int(checkpoint["epoch"]) + 1
            best_macro, best_loss = float(checkpoint["best_macro"]), float(checkpoint["best_loss"])
            best_epoch, bad_epochs = int(checkpoint["best_epoch"]), int(checkpoint["bad_epochs"])
        except (OSError, KeyError, ValueError, RuntimeError, EOFError, pickle.UnpicklingError) as exc:
            if isinstance(exc, C3ExecutionError):
                raise
            raise C3ExecutionError(f"corrupt or incomplete checkpoint: {exc}") from exc

    for epoch in range(start_epoch, epochs + 1):
        epoch_seed = derive_epoch_seed(seed, epoch)
        _seed_everything(epoch_seed)
        model.train()
        epoch_started = time.perf_counter()
        train_losses = []
        for batch in train_loader_factory(epoch):
            _validate_batch(batch, "TRAIN")
            images, masks = batch["image"].to(device_t), batch["mask"].to(device_t)
            optimizer.zero_grad(set_to_none=True)
            with torch.amp.autocast(device_type=device_t.type, enabled=amp_enabled):
                logits = model(images)
                loss = criterion(logits, masks)
            if not torch.isfinite(loss):
                raise C3ExecutionError("nonfinite training loss")
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            train_losses.append(float(loss.detach().cpu()))
        if not train_losses:
            raise C3ExecutionError("empty training loader")
        val_loss, per_domain, _ = _evaluate(model, val_loader, criterion, device_t, 0.5, amp_enabled)
        macro = macro_domain_dice({d: per_domain[d]["dice"] for d in DOMAIN_ORDER})
        improved = is_new_best(macro, val_loss, best_macro, best_loss)
        if improved:
            best_macro, best_loss, best_epoch, bad_epochs = macro, val_loss, epoch, 0
        else:
            bad_epochs += 1
        row = {
            "epoch": epoch,
            "train_loss": float(np.mean(train_losses)),
            "val_loss": val_loss,
            "macro_domain_dice": macro,
            **{f"val_dice_{d}": per_domain[d]["dice"] for d in DOMAIN_ORDER},
            **{f"val_iou_{d}": per_domain[d]["iou"] for d in DOMAIN_ORDER},
            "learning_rate": float(optimizer.param_groups[0]["lr"]),
            "is_new_best": improved,
            "seconds_measured": time.perf_counter() - epoch_started,
        }
        history.append(row)
        with history_path.open("w", encoding="utf-8", newline="\n") as f:
            for history_row in history:
                f.write(json.dumps(history_row, sort_keys=True, allow_nan=False) + "\n")
        scheduler.step()
        checkpoint = {
            "schema": "controlled_c3_checkpoint_v1",
            "model_key": model_key,
            "seed": seed,
            "epoch": epoch,
            "config_sha256": config_digest,
            "model_state": model.state_dict(),
            "optimizer_state": optimizer.state_dict(),
            "scheduler_state": scheduler.state_dict(),
            "scaler_state": scaler.state_dict(),
            "best_macro": best_macro,
            "best_loss": best_loss,
            "best_epoch": best_epoch,
            "bad_epochs": bad_epochs,
            "history_rows": history,
            "synthetic_only": True,
        }
        _atomic_torch_save(latest_path, checkpoint)
        if improved:
            _atomic_torch_save(best_path, checkpoint)
        if bad_epochs >= int(RECIPE["early_stopping_patience"]):
            break

    if not best_path.is_file():
        raise C3ExecutionError("best checkpoint was not produced")
    try:
        best_state = torch.load(best_path, map_location="cpu", weights_only=False)
    except (OSError, RuntimeError, EOFError, pickle.UnpicklingError) as exc:
        raise C3ExecutionError(f"best checkpoint is corrupt: {exc}") from exc
    replay = select_best_epoch(history)
    if (best_state.get("model_key") != model_key or best_state.get("seed") != seed
            or best_state.get("config_sha256") != config_digest
            or best_state.get("epoch") != replay["selected_epoch"]
            or replay["selected_epoch"] != best_epoch):
        raise C3ExecutionError("best checkpoint does not match replayed validation selection")
    _atomic_json(out / "config.json", config)
    manifest = {
        "schema": "controlled_c3_run_manifest_v1",
        "model_key": model_key,
        "seed": seed,
        "status": "SYNTHETIC_TEST_ONLY",
        "synthetic_only": True,
        "training_performed": True,
        "best_epoch": best_epoch,
        "completed_epochs": len(history),
        "selection_rule": SELECTION_RULE_ID,
        "config_sha256": config_digest,
        "config_file_sha256": sha256_file(out / "config.json"),
        "history_sha256": sha256_file(history_path),
        "best_checkpoint_sha256": sha256_file(best_path),
        "latest_checkpoint_sha256": sha256_file(latest_path),
        "model_source_sha256": config["source"]["model_source_sha256"],
        "protocol_sha256": EXPECTED_PROTOCOL_SHA256,
        "protected_splits_accessed": [],
        "device": str(device_t),
        "parameters_trainable": parameter_count(model),
        "analytical_compute": analytical_macs_lower_bound(model, (1, 3, 64 if synthetic else 512, 64 if synthetic else 512)),
    }
    _atomic_json(out / "run_manifest.json", manifest)
    return manifest


def _atomic_torch_save(path: Path, value: dict[str, Any]) -> None:
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    os.close(fd)
    try:
        torch.save(value, temp_name)
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


def benchmark_synthetic_step(
    model_key: str, *, device: str = "cuda", image_size: int = 512,
    batch_size: int = 2, measured_steps: int = 3
) -> dict[str, Any]:
    """Measure short random synthetic forward/backward steps; not an epoch estimate."""
    device_t = torch.device(device)
    if device_t.type != "cuda" or not torch.cuda.is_available():
        raise C3ExecutionError("synthetic resource benchmark requires CUDA")
    _seed_everything(42)
    model = build_model(model_key).to(device_t)
    model.train()
    x = torch.rand(batch_size, 3, image_size, image_size, device=device_t)
    y = (torch.rand(batch_size, 1, image_size, image_size, device=device_t) > 0.9).float()
    criterion = BCEDiceLoss(0.5, 0.5, 1e-6)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4, weight_decay=1e-4)
    torch.cuda.empty_cache()
    if measured_steps < 1:
        raise C3ExecutionError("measured_steps must be positive")

    def step() -> None:
        optimizer.zero_grad(set_to_none=True)
        with torch.amp.autocast(device_type="cuda", enabled=True):
            loss = criterion(model(x), y)
        loss.backward()
        optimizer.step()

    try:
        step()
        torch.cuda.synchronize(device_t)
        torch.cuda.reset_peak_memory_stats(device_t)
        samples = []
        for _ in range(measured_steps):
            started = time.perf_counter()
            step()
            torch.cuda.synchronize(device_t)
            samples.append(time.perf_counter() - started)
    except torch.cuda.OutOfMemoryError:
        optimizer.zero_grad(set_to_none=True)
        torch.cuda.empty_cache()
        raise C3ExecutionError(
            f"synthetic forward/backward benchmark OOM: {model_key}, batch={batch_size}, size={image_size}"
        )
    result = {
        "model_key": model_key,
        "device": torch.cuda.get_device_name(device_t),
        "batch_size": batch_size,
        "image_size": image_size,
        "median_synthetic_forward_backward_step_seconds": float(np.median(samples)),
        "measured_steps": measured_steps,
        "warmup_steps": 1,
        "peak_cuda_memory_bytes": int(torch.cuda.max_memory_allocated(device_t)),
        "parameter_count": parameter_count(model),
        "two_checkpoint_plus_adam_storage_estimate_bytes": estimate_optimizer_checkpoint_bytes(parameter_count(model)),
        "analytical_compute": analytical_macs_lower_bound(model, (1, 3, image_size, image_size)),
        "not_full_epoch_or_campaign_runtime": True,
    }
    del model, optimizer, x, y, criterion
    torch.cuda.empty_cache()
    return result


def evaluate_best_checkpoint(run_dir: Path, output_dir: Path | None = None) -> dict[str, Any]:
    """Regenerate per-domain/per-image metrics from a saved best checkpoint."""
    run_dir = Path(run_dir)
    manifest_path = run_dir / "run_manifest.json"
    config_path = run_dir / "config.json"
    best_path = run_dir / "best.pt"
    for path in (manifest_path, config_path, best_path):
        if not path.is_file():
            raise C3ExecutionError(f"missing result input: {path.name}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not manifest.get("synthetic_only"):
        raise C3ExecutionError("real evaluation requires the separately authorized C3 runner")
    if sha256_file(config_path) != manifest.get("config_file_sha256"):
        raise C3ExecutionError("run configuration hash mismatch")
    if sha256_file(best_path) != manifest.get("best_checkpoint_sha256"):
        raise C3ExecutionError("best checkpoint hash mismatch")
    history_path = run_dir / "history.jsonl"
    if not history_path.is_file() or sha256_file(history_path) != manifest.get("history_sha256"):
        raise C3ExecutionError("history missing or hash-mismatched")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    model_key, seed = config["model_key"], int(config["seed"])
    checkpoint = torch.load(best_path, map_location="cpu", weights_only=False)
    if checkpoint.get("synthetic_only") is not True:
        raise C3ExecutionError("checkpoint synthetic provenance mismatch")
    if (checkpoint.get("config_sha256") != manifest.get("config_sha256")
            or checkpoint.get("model_key") != model_key
            or checkpoint.get("seed") != seed
            or checkpoint.get("epoch") != manifest.get("best_epoch")):
        raise C3ExecutionError("best checkpoint identity/selection mismatch")
    model = build_model(model_key, base_channels=int(config["smoke_overrides"]["base_channels"]))
    model.load_state_dict(checkpoint["model_state"], strict=True)
    _, val_loader = make_synthetic_loaders(seed, image_size=64, samples_per_domain=2, batch_size=2)
    _, by_domain, per_image = _evaluate(
        model, val_loader, BCEDiceLoss(0.5, 0.5, 1e-6), torch.device("cpu"), 0.5, False,
        include_hd95=True)
    result = {
        "schema": "controlled_c3_evaluation_v1",
        "status": "SYNTHETIC_TEST_ONLY",
        "synthetic_only": True,
        "model_key": model_key,
        "seed": seed,
        "population": "synthetic smoke fixtures",
        "selection": {"rule": SELECTION_RULE_ID, "best_epoch": manifest["best_epoch"]},
        "per_domain": by_domain,
        "macro_equal_domain_dice": macro_domain_dice({d: by_domain[d]["dice"] for d in DOMAIN_ORDER}),
        "per_image": per_image,
        "source_manifest_sha256": sha256_file(manifest_path),
        "checkpoint_sha256": sha256_file(best_path),
    }
    dest = Path(output_dir) if output_dir else run_dir
    _atomic_json(dest / "evaluation.json", result)
    per_image_path = dest / "per_image_metrics.csv"
    per_domain_path = dest / "per_domain_metrics.csv"
    _write_csv(per_image_path, per_image)
    _write_csv(per_domain_path, [
        {"domain": d, **by_domain[d], "n": sum(x["domain"] == d for x in per_image)}
        for d in DOMAIN_ORDER
    ])
    if dest.resolve() == run_dir.resolve():
        manifest["pre_evaluation_manifest_sha256"] = result["source_manifest_sha256"]
        manifest["evaluation_sha256"] = sha256_file(dest / "evaluation.json")
        manifest["per_image_metrics_sha256"] = sha256_file(per_image_path)
        manifest["per_domain_metrics_sha256"] = sha256_file(per_domain_path)
        _atomic_json(manifest_path, manifest)
    return result


def write_empty_results_schema(output: Path) -> dict[str, Any]:
    """Write the full-method plus five-baseline matrix with all 18 cells missing."""
    configs = [build_experiment_config(model, seed) for model in EXPERIMENT_MODEL_KEYS for seed in EXPECTED_SEEDS]
    missing = [{"model_key": model, "seed": seed} for model in EXPERIMENT_MODEL_KEYS for seed in EXPECTED_SEEDS]
    schema = {
        "schema": "controlled_c3_results_v2",
        "status": "NOT_ESTABLISHED",
        "evidence_class": "no protocol-matched full-method C3 runs completed",
        "primary_model": FULL_MODEL_IDENTITY,
        "primary_model_key": FULL_MODEL_KEY,
        "internal_ablation_reference": "GlobalMedFiLM without BARR; not the proposed-method row",
        "external_baselines": [
            {"model_key": key, "display_name": ARCHITECTURES[key]["display_name"]}
            for key in EXTERNAL_BASELINE_KEYS
        ],
        "comparison_direction": "RA-MedFiLM-BARR (FULL) minus external baseline",
        "historical_protocol_incomparable": {
            "source": "reports/tables/c3_baselines/c3_baseline_report.json",
            "status": "separate historical evidence; GlobalMedFiLM is retained only as an internal ablation reference",
        },
        "expected_runs": [
            {"model_key": c["model_key"], "seed": c["seed"], "status": "MISSING",
             "role": c["role"],
             "config_sha256": hashlib.sha256(json.dumps(c, sort_keys=True).encode()).hexdigest()}
            for c in configs
        ],
        "missing_runs": missing,
        "required_metrics": ["macro_equal_domain_dice", "per_domain_dice", "per_domain_iou",
                             "per_domain_precision", "per_domain_recall", "per_domain_hd95",
                             "per_image_metrics", "per_image_hd95_with_undefined_reason",
                             "best_epoch", "parameter_count", "analytical_compute", "measured_latency"],
        "comparison_policy": (
            "Primary estimand is the paired-seed difference in equal-domain macro Dice, "
            "RA-MedFiLM-BARR (FULL) minus each baseline, on identical VAL808 sample IDs. "
            "No superiority or inferential claim is available until all 18 compatible cells pass validation."
        ),
        "full_model_component_contract": {
            "bundle_schema": FULL_MODEL_BUNDLE_SCHEMA,
            "required_components": list(FULL_MODEL_COMPONENTS),
            "same_seed_end_to_end": True,
            "component_checkpoint_family_binding_required": True,
            "historical_fixed_global_seed42_phase29_runs_accepted": False,
        },
        "c1_status": "separate internal FiLM attribution; frozen 6-run protocol unchanged",
        "protocol_sha256": EXPECTED_PROTOCOL_SHA256,
        "protected_data_accessed": False,
    }
    validate_controlled_results_schema(schema)
    _atomic_json(Path(output), schema)
    return schema


def validate_controlled_results_schema(result: dict[str, Any]) -> None:
    required = ("status", "evidence_class", "primary_model", "primary_model_key",
                "comparison_direction", "expected_runs", "missing_runs",
                "protocol_sha256", "protected_data_accessed")
    if result.get("schema") != "controlled_c3_results_v2" or any(k not in result for k in required):
        raise C3ExecutionError("controlled C3 result schema top-level validation failed")
    if result["protocol_sha256"] != EXPECTED_PROTOCOL_SHA256 or result["protected_data_accessed"] is not False:
        raise C3ExecutionError("controlled C3 result scope validation failed")
    if (result["primary_model_key"] != FULL_MODEL_KEY
            or result["primary_model"] != FULL_MODEL_IDENTITY
            or result["comparison_direction"] != "RA-MedFiLM-BARR (FULL) minus external baseline"):
        raise C3ExecutionError("controlled C3 primary model identity/direction is invalid")
    expected = {(m, s) for m in EXPERIMENT_MODEL_KEYS for s in EXPECTED_SEEDS}
    rows = result["expected_runs"]
    keys = {(r.get("model_key"), r.get("seed")) for r in rows}
    if len(rows) != 18 or len(expected) != 18 or keys != expected:
        raise C3ExecutionError("controlled C3 result run matrix invalid")
    missing = {(r.get("model_key"), r.get("seed")) for r in result["missing_runs"]}
    if missing != { (r["model_key"], r["seed"]) for r in rows if r.get("status") == "MISSING" }:
        raise C3ExecutionError("controlled C3 missing-run roster is inconsistent")
    forbidden = {"SYNTHETIC_TEST_ONLY", "PROTOCOL_INCOMPARABLE"}
    if result["evidence_class"] in forbidden or any(r.get("evidence_class") in forbidden for r in rows):
        raise C3ExecutionError("non-production evidence class in controlled C3 result")
    for row in rows:
        if row.get("status") not in ("MISSING", "COMPLETE"):
            raise C3ExecutionError("unknown controlled C3 run status")
        if row.get("status") == "COMPLETE":
            required_run = ("macro_equal_domain_dice", "per_domain",
                            "parameter_count", "analytical_compute", "config_sha256",
                            "history_sha256", "best_checkpoint_sha256")
            if row["model_key"] != FULL_MODEL_KEY:
                required_run = (*required_run, "best_epoch")
            if any(k not in row for k in required_run):
                raise C3ExecutionError("completed controlled C3 row is incomplete")
            score = float(row["macro_equal_domain_dice"])
            if not math.isfinite(score) or not 0 <= score <= 1:
                raise C3ExecutionError("completed controlled C3 row has invalid metric")
            if set(row["per_domain"]) != set(DOMAIN_ORDER):
                raise C3ExecutionError("completed controlled C3 per-domain map is invalid")
            for metrics in row["per_domain"].values():
                dice_value = float(metrics["dice"])
                if not math.isfinite(dice_value) or not 0 <= dice_value <= 1:
                    raise C3ExecutionError("completed controlled C3 domain metric is invalid")
            if row["model_key"] == FULL_MODEL_KEY:
                if row.get("model_identity") != FULL_MODEL_IDENTITY:
                    raise C3ExecutionError("completed primary result is not the complete RA-MedFiLM-BARR model")
                if row.get("full_model_bundle_manifest_sha256") is None:
                    raise C3ExecutionError("completed primary result lacks component-bundle provenance")


def validate_full_model_bundle(bundle: dict[str, Any], seed: int) -> None:
    """Reject mixed-seed or cross-checkpoint-family FULL bundles."""
    if bundle.get("schema") != FULL_MODEL_BUNDLE_SCHEMA:
        raise C3ExecutionError("full-model bundle schema mismatch")
    if bundle.get("model_identity") != FULL_MODEL_IDENTITY or bundle.get("master_seed") != seed:
        raise C3ExecutionError("full-model bundle identity/seed mismatch")
    components = bundle.get("components")
    if not isinstance(components, dict) or set(components) != set(FULL_MODEL_COMPONENTS):
        raise C3ExecutionError("full-model bundle component roster mismatch")
    for key in ("G", "R_psi", "B_phi", "S_omega"):
        item = components.get(key)
        if not isinstance(item, dict):
            raise C3ExecutionError(f"full-model component metadata missing: {key}")
        digest = item.get("checkpoint_sha256")
        if (not isinstance(digest, str) or len(digest) != 64
                or any(char not in "0123456789abcdef" for char in digest.lower())):
            raise C3ExecutionError(f"full-model component digest missing: {key}")
        if not isinstance(item.get("checkpoint_path"), str) or not item["checkpoint_path"]:
            raise C3ExecutionError(f"full-model component path missing: {key}")
        if item.get("master_seed") != seed:
            raise C3ExecutionError(f"full-model component seed mismatch: {key}")
    g_sha = components["G"]["checkpoint_sha256"]
    r_sha = components["R_psi"]["checkpoint_sha256"]
    if components["R_psi"].get("trained_against_global_sha256") != g_sha:
        raise C3ExecutionError("refiner was not trained against this exact global checkpoint")
    if (components["B_phi"].get("trained_against_global_sha256") != g_sha
            or components["B_phi"].get("trained_against_refiner_sha256") != r_sha):
        raise C3ExecutionError("router training checkpoint family is incompatible")
    if (components["S_omega"].get("trained_against_global_sha256") != g_sha
            or components["S_omega"].get("trained_against_refiner_sha256") != r_sha
            or components["S_omega"].get("trained_against_router_sha256")
            != components["B_phi"]["checkpoint_sha256"]):
        raise C3ExecutionError("safety training checkpoint family is incompatible")
    source_digest = components["routing_fusion"].get("source_sha256")
    if (not isinstance(source_digest, str) or len(source_digest) != 64
            or any(char not in "0123456789abcdef" for char in source_digest.lower())):
        raise C3ExecutionError("routing/fusion source provenance missing")


def aggregate_controlled_results(
    run_dirs: Iterable[Path], output: Path
) -> dict[str, Any]:
    """Validate future real run artifacts; synthetic outputs are never accepted."""
    validate_manifest_contract()
    expected_val_ids = set(pd.read_csv(MANIFEST_VAL)["sample_id"].astype(str))
    expected = {(m, s) for m in EXPERIMENT_MODEL_KEYS for s in EXPECTED_SEEDS}
    accepted: dict[tuple[str, int], dict[str, Any]] = {}
    for directory in run_dirs:
        path = Path(directory)
        try:
            manifest = json.loads((path / "run_manifest.json").read_text(encoding="utf-8"))
            evaluation = json.loads((path / "evaluation.json").read_text(encoding="utf-8"))
            config = json.loads((path / "config.json").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise C3ExecutionError(f"incomplete/corrupt run artifact at {path}: {exc}") from exc
        if manifest.get("synthetic_only") or manifest.get("status") == "SYNTHETIC_TEST_ONLY":
            raise C3ExecutionError(f"synthetic fixture rejected as production C3 evidence: {path}")
        if manifest.get("status") != "CONFIRMED_EXECUTED_RESULT" or manifest.get("training_performed") is not True:
            raise C3ExecutionError(f"run lacks completed-execution provenance: {path}")
        release_digest = manifest.get("authorization_release_sha256", "")
        if not isinstance(release_digest, str) or len(release_digest) != 64:
            raise C3ExecutionError(f"run lacks a reviewed execution-release digest: {path}")
        if manifest.get("protected_splits_accessed") != []:
            raise C3ExecutionError(f"run reports protected-split access: {path}")
        if config.get("protocol", {}).get("sha256") != EXPECTED_PROTOCOL_SHA256:
            raise C3ExecutionError(f"protocol digest mismatch: {path}")
        expected_config_hash = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()
        if manifest.get("config_sha256") != expected_config_hash:
            raise C3ExecutionError(f"configuration hash mismatch: {path}")
        key = (str(config.get("model_key")), int(config.get("seed", -1)))
        if key not in expected:
            raise C3ExecutionError(f"unexpected model/seed cell: {key}")
        if manifest.get("model_key") != key[0] or int(manifest.get("seed", -1)) != key[1]:
            raise C3ExecutionError(f"run manifest model/seed identity mismatch: {path}")
        if key in accepted:
            raise C3ExecutionError(f"duplicate model/seed cell: {key}")
        for artifact_name, digest_key in (
                ("best.pt", "best_checkpoint_sha256"),
                ("history.jsonl", "history_sha256"),
                ("config.json", "config_file_sha256"),
                ("evaluation.json", "evaluation_sha256"),
                ("per_image_metrics.csv", "per_image_metrics_sha256"),
                ("per_domain_metrics.csv", "per_domain_metrics_sha256")):
            artifact = path / artifact_name
            if not artifact.is_file() or sha256_file(artifact) != manifest.get(digest_key):
                raise C3ExecutionError(f"missing or hash-mismatched {artifact_name}: {path}")
        if key[0] == FULL_MODEL_KEY:
            bundle_path = path / "full_model_bundle_manifest.json"
            if (not bundle_path.is_file()
                    or sha256_file(bundle_path) != manifest.get("full_model_bundle_manifest_sha256")):
                raise C3ExecutionError(f"missing or hash-mismatched full-model bundle manifest: {path}")
            try:
                bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise C3ExecutionError(f"corrupt full-model bundle manifest: {path}: {exc}") from exc
            validate_full_model_bundle(bundle, key[1])
            for component_key in ("G", "R_psi", "B_phi", "S_omega"):
                checkpoint = (path / bundle["components"][component_key]["checkpoint_path"]).resolve()
                if not checkpoint.is_relative_to(path.resolve()):
                    raise C3ExecutionError(f"full-model checkpoint escapes its run directory: {path}")
                if (not checkpoint.is_file()
                        or sha256_file(checkpoint) != bundle["components"][component_key]["checkpoint_sha256"]):
                    raise C3ExecutionError(f"full-model component checkpoint missing or corrupt: {component_key}")
            if int(manifest.get("parameters_total", 0)) != FULL_MODEL_PARAMETER_COUNT:
                raise C3ExecutionError(f"full-model parameter count mismatch: {path}")
        parameter_count_value = (
            int(manifest.get("parameters_total", 0)) if key[0] == FULL_MODEL_KEY
            else int(manifest.get("parameters_trainable", 0))
        )
        if parameter_count_value <= 0 or not manifest.get("analytical_compute"):
            raise C3ExecutionError(f"parameter/compute provenance missing: {path}")
        try:
            history = [json.loads(line) for line in (path / "history.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
        except (OSError, json.JSONDecodeError) as exc:
            raise C3ExecutionError(f"history missing or corrupt: {path}: {exc}") from exc
        try:
            replay = select_best_epoch(history)
        except (KeyError, ValueError, TypeError) as exc:
            raise C3ExecutionError(f"invalid selection history: {path}: {exc}") from exc
        if replay["selected_epoch"] != manifest.get("best_epoch"):
            raise C3ExecutionError(f"best-checkpoint selection mismatch: {path}")
        if evaluation.get("synthetic_only") is not False:
            raise C3ExecutionError(f"evaluation is not authenticated as real: {path}")
        if key[0] == FULL_MODEL_KEY and evaluation.get("model_identity") != FULL_MODEL_IDENTITY:
            raise C3ExecutionError(f"primary evaluation does not identify the complete full system: {path}")
        if int(evaluation.get("seed", -1)) != key[1]:
            raise C3ExecutionError(f"evaluation seed identity mismatch: {path}")
        if (evaluation.get("source_manifest_sha256") != manifest.get("pre_evaluation_manifest_sha256")
                or evaluation.get("checkpoint_sha256") != manifest.get("best_checkpoint_sha256")):
            raise C3ExecutionError(f"evaluation provenance mismatch: {path}")
        score = float(evaluation["macro_equal_domain_dice"])
        if not math.isfinite(score) or not 0 <= score <= 1:
            raise C3ExecutionError(f"invalid macro Dice: {path}")
        per_image = evaluation.get("per_image")
        if not isinstance(per_image, list) or len(per_image) != EXPECTED_COUNTS["VAL"]:
            raise C3ExecutionError(f"VAL808 per-image results missing or incomplete: {path}")
        ids = [str(row.get("sample_id", "")) for row in per_image]
        if not all(ids) or len(set(ids)) != EXPECTED_COUNTS["VAL"]:
            raise C3ExecutionError(f"VAL808 per-image IDs missing or duplicate: {path}")
        if set(ids) != expected_val_ids:
            raise C3ExecutionError(f"VAL808 sample roster differs from the frozen manifest: {path}")
        counts = {d: sum(row.get("domain") == d for row in per_image) for d in DOMAIN_ORDER}
        if counts != {"ISIC": 357, "BUSI": 84, "KVASIR": 87, "KUB": 280}:
            raise C3ExecutionError(f"VAL808 domain denominators mismatch: {path}: {counts}")
        for row in per_image:
            vals = [float(row[k]) for k in ("dice", "iou", "precision", "recall")]
            if any(not math.isfinite(v) or not 0 <= v <= 1 for v in vals):
                raise C3ExecutionError(f"invalid per-image metric: {path}")
            domain = row.get("domain")
            if row.get("task_id") != TASK_IDS.get(domain) or row.get("split") != "VAL":
                raise C3ExecutionError(f"per-image task/split identity mismatch: {path}")
            hd95_value = row.get("hd95")
            undefined_reason = row.get("hd95_undefined_reason")
            if hd95_value is None:
                if undefined_reason not in {
                        "both_empty", "empty_prediction", "empty_ground_truth"}:
                    raise C3ExecutionError(f"undefined HD95 lacks an explicit reason: {path}")
            elif (isinstance(hd95_value, bool) or not isinstance(hd95_value, (int, float))
                  or not math.isfinite(float(hd95_value)) or float(hd95_value) < 0
                  or undefined_reason is not None):
                raise C3ExecutionError(f"invalid HD95 result: {path}")
        recomputed = macro_domain_dice({
            d: float(np.mean([float(r["dice"]) for r in per_image if r["domain"] == d]))
            for d in DOMAIN_ORDER
        })
        if abs(recomputed - score) > 1e-10:
            raise C3ExecutionError(f"macro Dice does not match per-image results: {path}")
        if set(evaluation.get("per_domain", {})) != set(DOMAIN_ORDER):
            raise C3ExecutionError(f"per-domain result rows missing: {path}")
        for domain in DOMAIN_ORDER:
            domain_rows = [r for r in per_image if r["domain"] == domain]
            for metric in ("dice", "iou", "precision", "recall"):
                expected_metric = float(np.mean([float(r[metric]) for r in domain_rows]))
                actual_metric = float(evaluation["per_domain"][domain][metric])
                if (not math.isfinite(actual_metric) or not 0 <= actual_metric <= 1
                        or abs(expected_metric - actual_metric) > 1e-10):
                    raise C3ExecutionError(
                        f"per-domain {metric} mismatch: {path} domain={domain}"
                    )
            defined_hd95 = [
                float(row["hd95"]) for row in per_image
                if row["domain"] == domain and row["hd95"] is not None
            ]
            domain_metrics = evaluation["per_domain"][domain]
            defined_count = domain_metrics.get("hd95_n_defined")
            if (not isinstance(defined_count, int) or isinstance(defined_count, bool)
                    or defined_count != len(defined_hd95)):
                raise C3ExecutionError(f"per-domain HD95 denominator mismatch: {path} domain={domain}")
            expected_hd95 = float(np.mean(defined_hd95)) if defined_hd95 else None
            actual_hd95 = domain_metrics.get("hd95")
            if expected_hd95 is None:
                valid_hd95 = actual_hd95 is None
            else:
                valid_hd95 = (
                    isinstance(actual_hd95, (int, float))
                    and not isinstance(actual_hd95, bool)
                    and math.isfinite(float(actual_hd95))
                    and abs(float(actual_hd95) - expected_hd95) <= 1e-10
                )
            if not valid_hd95:
                raise C3ExecutionError(f"per-domain HD95 mismatch: {path} domain={domain}")
        accepted[key] = {"manifest": manifest, "evaluation": evaluation, "config": config}
    for (model, seed), record in accepted.items():
        dataset = record["config"].get("dataset", {})
        if (dataset.get("train_manifest_sha256") != sha256_file(MANIFEST_TRAIN)
                or dataset.get("val_manifest_sha256") != sha256_file(MANIFEST_VAL)
                or dataset.get("train_n") != EXPECTED_COUNTS["TRAIN"]
                or dataset.get("val_n") != EXPECTED_COUNTS["VAL"]):
            raise C3ExecutionError(f"dataset contract mismatch for {model} seed {seed}")
    missing = sorted(expected - set(accepted))
    result = {
        "schema": "controlled_c3_results_v2",
        "status": "NOT_ESTABLISHED" if missing else "COMPLETE_REQUIRES_REVIEW",
        "evidence_class": "protocol-matched full-method evidence" if not missing else "incomplete controlled full-method comparison",
        "primary_model": FULL_MODEL_IDENTITY,
        "primary_model_key": FULL_MODEL_KEY,
        "internal_ablation_reference": "GlobalMedFiLM without BARR; C1 attribution remains separate",
        "external_baselines": list(EXTERNAL_BASELINE_KEYS),
        "comparison_direction": "RA-MedFiLM-BARR (FULL) minus external baseline",
        "historical_protocol_incomparable": {
            "source": "reports/tables/c3_baselines/c3_baseline_report.json",
            "status": "separate historical evidence; not merged",
        },
        "expected_runs": [
            {"model_key": m, "seed": s,
             "role": "PRIMARY_PROPOSED_METHOD" if m == FULL_MODEL_KEY else "EXTERNAL_ARCHITECTURE_BASELINE",
             "status": "COMPLETE" if (m, s) in accepted else "MISSING",
             **({
                 "macro_equal_domain_dice": accepted[(m, s)]["evaluation"]["macro_equal_domain_dice"],
                 "best_epoch": accepted[(m, s)]["manifest"]["best_epoch"],
                 "config_sha256": accepted[(m, s)]["manifest"]["config_sha256"],
                 "best_checkpoint_sha256": accepted[(m, s)]["manifest"]["best_checkpoint_sha256"],
                 "history_sha256": accepted[(m, s)]["manifest"]["history_sha256"],
                 "per_domain": accepted[(m, s)]["evaluation"]["per_domain"],
                 "parameter_count": (
                     accepted[(m, s)]["manifest"]["parameters_total"] if m == FULL_MODEL_KEY
                     else accepted[(m, s)]["manifest"]["parameters_trainable"]
                 ),
                 "analytical_compute": accepted[(m, s)]["manifest"]["analytical_compute"],
                 **({"model_identity": FULL_MODEL_IDENTITY,
                     "full_model_bundle_manifest_sha256": accepted[(m, s)]["manifest"]["full_model_bundle_manifest_sha256"]}
                    if m == FULL_MODEL_KEY else {}),
             }
                if (m, s) in accepted else {})}
            for m, s in sorted(expected, key=lambda x: (EXPERIMENT_MODEL_KEYS.index(x[0]), x[1]))
        ],
        "missing_runs": [{"model_key": m, "seed": s} for m, s in missing],
        "paired_reference": "RA-MedFiLM-BARR (FULL), same seed and exact VAL808 sample IDs",
        "paired_comparisons": [],
        "protocol_sha256": EXPECTED_PROTOCOL_SHA256,
        "protected_data_accessed": False,
    }
    result["paired_comparisons"] = paired_full_vs_baselines(accepted)
    validate_controlled_results_schema(result)
    _atomic_json(Path(output), result)
    return result


def paired_full_vs_baselines(
    accepted: dict[tuple[str, int], dict[str, Any]],
) -> list[dict[str, Any]]:
    """Compute matched per-seed FULL-minus-baseline effects on exact VAL IDs."""
    effects = []
    for seed in EXPECTED_SEEDS:
        full_key = (FULL_MODEL_KEY, seed)
        if full_key not in accepted:
            continue
        full_rows = accepted[full_key]["evaluation"]["per_image"]
        full_by_id = {str(row["sample_id"]): row for row in full_rows}
        if len(full_by_id) != len(full_rows):
            raise C3ExecutionError(f"duplicate full-model sample IDs for seed {seed}")
        for sample_id, row in full_by_id.items():
            score = row.get("dice")
            if (not sample_id or row.get("split") != "VAL"
                    or row.get("task_id") != TASK_IDS.get(row.get("domain"))
                    or not isinstance(score, (int, float)) or isinstance(score, bool)
                    or not math.isfinite(float(score)) or not 0 <= float(score) <= 1):
                raise C3ExecutionError(f"invalid full-model paired result row for seed {seed}")
        for baseline in EXTERNAL_BASELINE_KEYS:
            baseline_key = (baseline, seed)
            if baseline_key not in accepted:
                continue
            base_rows = accepted[baseline_key]["evaluation"]["per_image"]
            base_by_id = {str(row["sample_id"]): row for row in base_rows}
            if len(base_by_id) != len(base_rows):
                raise C3ExecutionError(f"duplicate {baseline} sample IDs for seed {seed}")
            for sample_id, row in base_by_id.items():
                score = row.get("dice")
                if (not sample_id or row.get("split") != "VAL"
                        or row.get("task_id") != TASK_IDS.get(row.get("domain"))
                        or not isinstance(score, (int, float)) or isinstance(score, bool)
                        or not math.isfinite(float(score)) or not 0 <= float(score) <= 1):
                    raise C3ExecutionError(f"invalid {baseline} paired result row for seed {seed}")
            if set(full_by_id) != set(base_by_id):
                raise C3ExecutionError(f"paired sample roster mismatch for {FULL_MODEL_IDENTITY} vs {baseline}, seed {seed}")
            if any(
                full_by_id[sid]["domain"] != base_by_id[sid]["domain"]
                or full_by_id[sid].get("task_id") != base_by_id[sid].get("task_id")
                or full_by_id[sid].get("task_id") != TASK_IDS.get(full_by_id[sid]["domain"])
                or full_by_id[sid].get("split") != base_by_id[sid].get("split")
                for sid in full_by_id
            ):
                raise C3ExecutionError(f"paired domain/task mismatch for {FULL_MODEL_IDENTITY} vs {baseline}, seed {seed}")
            per_domain = {}
            for domain in DOMAIN_ORDER:
                ids = [sid for sid, row in full_by_id.items() if row["domain"] == domain]
                if not ids:
                    raise C3ExecutionError(f"empty paired domain {domain}, seed {seed}")
                full_mean = float(np.mean([float(full_by_id[sid]["dice"]) for sid in ids]))
                base_mean = float(np.mean([float(base_by_id[sid]["dice"]) for sid in ids]))
                per_domain[domain] = {
                    "n": len(ids),
                    "full_dice": full_mean,
                    "baseline_dice": base_mean,
                    "full_minus_baseline": full_mean - base_mean,
                }
            effects.append({
                "primary_model": FULL_MODEL_IDENTITY,
                "baseline_model_key": baseline,
                "seed": seed,
                "estimand": "equal-domain mean of paired per-image Dice difference",
                "direction": "full_minus_baseline",
                "per_domain": per_domain,
                "macro_delta": float(np.mean([per_domain[d]["full_minus_baseline"] for d in DOMAIN_ORDER])),
                "evidence_class": "descriptive paired-seed contrast; no inferential claim",
            })
    return effects


def _write_plan(path: Path) -> None:
    payload = {
        "schema": "controlled_c3_experiment_plan_v2",
        "status": "PREPARED_NOT_EXECUTED",
        "primary_model": FULL_MODEL_IDENTITY,
        "primary_model_key": FULL_MODEL_KEY,
        "external_baseline_keys": list(EXTERNAL_BASELINE_KEYS),
        "architecture_keys": list(EXPERIMENT_MODEL_KEYS),
        "seeds": list(EXPECTED_SEEDS),
        "planned_real_runs": len(EXPERIMENT_MODEL_KEYS) * len(EXPECTED_SEEDS),
        "training_priority": "C1 attribution remains separate; full-model C3 requires compatible same-seed G/R/B/S bundles before comparison.",
        "real_execution": "BLOCKED_PENDING_SEPARATE_AUTHORIZATION",
        "configurations": [build_experiment_config(m, s) for m in EXPERIMENT_MODEL_KEYS for s in EXPECTED_SEEDS],
        "protocol_sha256": EXPECTED_PROTOCOL_SHA256,
    }
    _atomic_json(path, payload)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Controlled full RA-MedFiLM-BARR versus baseline C3 preparation.")
    sub = parser.add_subparsers(dest="command", required=True)
    p_plan = sub.add_parser("prepare")
    p_plan.add_argument("--out", type=Path, default=ROOT / "reports" / "tables" / "c3_controlled" / "experiment_plan.json")
    p_plan = sub.add_parser("schema")
    p_plan.add_argument("--out", type=Path, default=ROOT / "reports" / "tables" / "c3_controlled" / "results.json")
    p_smoke = sub.add_parser("smoke")
    p_smoke.add_argument("--model", choices=tuple(ARCHITECTURES), required=True)
    p_smoke.add_argument("--seed", type=int, choices=EXPECTED_SEEDS, default=42)
    p_smoke.add_argument("--out", type=Path, required=True)
    p_smoke.add_argument("--epochs", type=int, default=1)
    p_smoke.add_argument("--device", default="cpu")
    p_smoke.add_argument("--image-size", type=int, default=64)
    p_smoke.add_argument("--base-channels", type=int, default=4)
    p_full_smoke = sub.add_parser("full-smoke")
    p_full_smoke.add_argument("--device", default="cpu")
    p_full_smoke.add_argument("--image-size", type=int, default=64)
    p_run = sub.add_parser("run-real")
    p_run.add_argument("--model", choices=EXPERIMENT_MODEL_KEYS, required=True)
    p_run.add_argument("--seed", type=int, choices=EXPECTED_SEEDS, required=True)
    p_agg = sub.add_parser("aggregate")
    p_agg.add_argument("--runs-root", type=Path, default=ROOT / "experiments" / "c3_controlled")
    p_agg.add_argument("--out", type=Path, default=ROOT / "reports" / "tables" / "c3_controlled" / "results.json")
    p_agg.add_argument("--allow-incomplete", action="store_true")
    p_bench = sub.add_parser("benchmark")
    p_bench.add_argument("--model", choices=tuple(ARCHITECTURES), required=True)
    p_bench.add_argument("--device", default="cuda")
    p_bench.add_argument("--image-size", type=int, default=512)
    p_bench.add_argument("--batch-size", type=int, default=2)
    p_bench.add_argument("--measured-steps", type=int, default=3)
    args = parser.parse_args(argv)
    if args.command == "prepare":
        _write_plan(args.out)
        print(f"PREPARED_NOT_EXECUTED: {args.out}")
        return 0
    if args.command == "schema":
        result = write_empty_results_schema(args.out)
        print(f"{result['status']}: {args.out} ({len(result['expected_runs'])} missing cells)")
        return 0
    if args.command == "run-real":
        if args.model == FULL_MODEL_KEY:
            raise C3ExecutionError(
                "FULL_MODEL_REAL_EXECUTION_BLOCKED_PENDING_COMPATIBLE_COMPONENT_BUNDLE_AND_SEPARATE_AUTHORIZATION"
            )
        raise C3ExecutionError("C3_REAL_EXECUTION_BLOCKED_PENDING_SEPARATE_AUTHORIZATION")
    if args.command == "aggregate":
        runs = [args.runs_root / model / f"seed{seed}" for model in EXPERIMENT_MODEL_KEYS for seed in EXPECTED_SEEDS]
        existing = [p for p in runs if p.is_dir()]
        result = aggregate_controlled_results(existing, args.out)
        print(f"{result['status']}: {args.out}; missing={len(result['missing_runs'])}")
        return 0 if not result["missing_runs"] or args.allow_incomplete else 3
    if args.command == "benchmark":
        print(json.dumps(benchmark_synthetic_step(args.model, device=args.device,
                                                  image_size=args.image_size, batch_size=args.batch_size,
                                                  measured_steps=args.measured_steps), indent=2))
        return 0
    if args.command == "full-smoke":
        from .full_system_smoke import run_synthetic_full_system_smoke
        result = run_synthetic_full_system_smoke(device=args.device, image_size=args.image_size)
        print(json.dumps(result, indent=2))
        return 0
    train_factory, val_loader = make_synthetic_loaders(
        args.seed, image_size=args.image_size, samples_per_domain=2, batch_size=2)
    run = train_run(args.model, args.seed, train_factory, val_loader, args.out,
                    epochs=args.epochs, device=args.device, synthetic=True,
                    base_channels=args.base_channels)
    evaluate_best_checkpoint(args.out)
    print(f"SYNTHETIC_TEST_ONLY: {args.model} seed={args.seed} epochs={run['completed_epochs']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except C3ExecutionError as exc:
        raise SystemExit(f"C3_ERROR: {exc}")
