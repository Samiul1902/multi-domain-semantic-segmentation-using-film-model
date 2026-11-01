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

# GlobalMedFiLM is the matched reference, not an additional baseline run here.
# Its three C1-T seeds are the planned comparator and must themselves complete.
REFERENCE_ARM = "C1-T (GlobalMedFiLM; same seeds and frozen C1 recipe)"
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
    if model_key not in ARCHITECTURES:
        raise C3ExecutionError(f"Unknown C3 architecture: {model_key}")
    if seed not in EXPECTED_SEEDS:
        raise C3ExecutionError(f"Seed must be one of {EXPECTED_SEEDS}, got {seed}")
    if sha256_file(PROTOCOL_PATH) != EXPECTED_PROTOCOL_SHA256:
        raise C3ExecutionError("Frozen C1 protocol digest mismatch; refusing to build C3 config")
    validate_manifest_contract()
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
        "schema": "controlled_c3_run_config_v1",
        "study_id": "C3_PROTOCOL_MATCHED_BASELINES_V1",
        "model_key": model_key,
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
        "reference_arm": REFERENCE_ARM,
        "dataset": {
            "manifest_version": "phase4_v3",
            "train_manifest": "manifests/phase4_v3/train.csv",
            "val_manifest": "manifests/phase4_v3/val.csv",
            "train_n": EXPECTED_COUNTS["TRAIN"],
            "val_n": EXPECTED_COUNTS["VAL"],
            "domains": list(DOMAIN_ORDER),
            "task_ids": {"ISIC": 0, "BUSI": 1, "KVASIR": 2, "KUB": 3},
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
        mapping = {"ISIC": 0, "BUSI": 1, "KVASIR": 2, "KUB": 3}
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
              device: torch.device, threshold: float, amp: bool) -> tuple[float, dict[str, dict[str, float]], list[dict[str, Any]]]:
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
            records.append({
                "sample_id": str(sample_id),
                "domain": str(batch["dataset"][i]),
                **{name: float(value[i].detach().cpu()) for name, value in metrics.items()},
            })
    if not records or len({r["sample_id"] for r in records}) != len(records):
        raise C3ExecutionError("empty or duplicate validation sample IDs")
    per_domain: dict[str, dict[str, float]] = {}
    for domain in DOMAIN_ORDER:
        subset = [r for r in records if r["domain"] == domain]
        if not subset:
            raise C3ExecutionError(f"validation domain missing: {domain}")
        per_domain[domain] = {
            key: float(np.mean([r[key] for r in subset]))
            for key in ("dice", "iou", "precision", "recall")
        }
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
        model, val_loader, BCEDiceLoss(0.5, 0.5, 1e-6), torch.device("cpu"), 0.5, False)
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
    _write_csv(dest / "per_image_metrics.csv", per_image)
    _write_csv(dest / "per_domain_metrics.csv", [
        {"domain": d, **by_domain[d], "n": sum(x["domain"] == d for x in per_image)}
        for d in DOMAIN_ORDER
    ])
    return result


def write_empty_results_schema(output: Path) -> dict[str, Any]:
    """Write all 15 expected cells as missing; never inserts fake metric values."""
    configs = [build_experiment_config(model, seed) for model in ARCHITECTURES for seed in EXPECTED_SEEDS]
    missing = [{"model_key": model, "seed": seed} for model in ARCHITECTURES for seed in EXPECTED_SEEDS]
    schema = {
        "schema": "controlled_c3_results_v1",
        "status": "NOT_ESTABLISHED",
        "evidence_class": "no controlled C3 runs completed",
        "reference_arm": REFERENCE_ARM,
        "historical_protocol_incomparable": {
            "source": "reports/tables/c3_baselines/c3_baseline_report.json",
            "status": "separate historical evidence; not merged",
        },
        "expected_runs": [
            {"model_key": c["model_key"], "seed": c["seed"], "status": "MISSING",
             "config_sha256": hashlib.sha256(json.dumps(c, sort_keys=True).encode()).hexdigest()}
            for c in configs
        ],
        "missing_runs": missing,
        "required_metrics": ["macro_equal_domain_dice", "per_domain_dice", "per_domain_iou",
                             "per_image_dice", "best_epoch", "parameter_count", "analytical_macs_lower_bound"],
        "comparison_policy": "Equal-domain macro Dice by paired seed against same-seed C1-T; no rank claim before all required runs are valid.",
        "protocol_sha256": EXPECTED_PROTOCOL_SHA256,
        "protected_data_accessed": False,
    }
    validate_controlled_results_schema(schema)
    _atomic_json(Path(output), schema)
    return schema


def validate_controlled_results_schema(result: dict[str, Any]) -> None:
    required = ("status", "evidence_class", "reference_arm", "expected_runs",
                "missing_runs", "protocol_sha256", "protected_data_accessed")
    if result.get("schema") != "controlled_c3_results_v1" or any(k not in result for k in required):
        raise C3ExecutionError("controlled C3 result schema top-level validation failed")
    if result["protocol_sha256"] != EXPECTED_PROTOCOL_SHA256 or result["protected_data_accessed"] is not False:
        raise C3ExecutionError("controlled C3 result scope validation failed")
    expected = {(m, s) for m in ARCHITECTURES for s in EXPECTED_SEEDS}
    rows = result["expected_runs"]
    keys = {(r.get("model_key"), r.get("seed")) for r in rows}
    if len(rows) != len(expected) or keys != expected:
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
            required_run = ("best_epoch", "macro_equal_domain_dice", "per_domain",
                            "parameter_count", "analytical_compute", "config_sha256",
                            "history_sha256", "best_checkpoint_sha256")
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


def aggregate_controlled_results(
    run_dirs: Iterable[Path], output: Path, *, c1_export_dir: Path | None = None
) -> dict[str, Any]:
    """Validate future real run artifacts; synthetic outputs are never accepted."""
    expected = {(m, s) for m in ARCHITECTURES for s in EXPECTED_SEEDS}
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
        if key in accepted:
            raise C3ExecutionError(f"duplicate model/seed cell: {key}")
        for artifact_name, digest_key in (("best.pt", "best_checkpoint_sha256"),
                                          ("history.jsonl", "history_sha256"),
                                          ("config.json", "config_file_sha256")):
            artifact = path / artifact_name
            if not artifact.is_file() or sha256_file(artifact) != manifest.get(digest_key):
                raise C3ExecutionError(f"missing or hash-mismatched {artifact_name}: {path}")
        if int(manifest.get("parameters_trainable", 0)) <= 0 or not manifest.get("analytical_compute"):
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
        if (evaluation.get("source_manifest_sha256") != sha256_file(path / "run_manifest.json")
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
        counts = {d: sum(row.get("domain") == d for row in per_image) for d in DOMAIN_ORDER}
        if counts != {"ISIC": 357, "BUSI": 84, "KVASIR": 87, "KUB": 280}:
            raise C3ExecutionError(f"VAL808 domain denominators mismatch: {path}: {counts}")
        for row in per_image:
            vals = [float(row[k]) for k in ("dice", "iou", "precision", "recall")]
            if any(not math.isfinite(v) or not 0 <= v <= 1 for v in vals):
                raise C3ExecutionError(f"invalid per-image metric: {path}")
        recomputed = macro_domain_dice({
            d: float(np.mean([float(r["dice"]) for r in per_image if r["domain"] == d]))
            for d in DOMAIN_ORDER
        })
        if abs(recomputed - score) > 1e-10:
            raise C3ExecutionError(f"macro Dice does not match per-image results: {path}")
        if set(evaluation.get("per_domain", {})) != set(DOMAIN_ORDER):
            raise C3ExecutionError(f"per-domain result rows missing: {path}")
        for domain in DOMAIN_ORDER:
            expected_domain_dice = float(np.mean([float(r["dice"]) for r in per_image if r["domain"] == domain]))
            actual_domain_dice = float(evaluation["per_domain"][domain]["dice"])
            if not math.isfinite(actual_domain_dice) or abs(expected_domain_dice - actual_domain_dice) > 1e-10:
                raise C3ExecutionError(f"per-domain Dice mismatch: {path} domain={domain}")
        accepted[key] = {"manifest": manifest, "evaluation": evaluation}
    missing = sorted(expected - set(accepted))
    result = {
        "schema": "controlled_c3_results_v1",
        "status": "NOT_ESTABLISHED" if missing else "COMPLETE_REQUIRES_REVIEW",
        "evidence_class": "protocol-matched controlled evidence" if not missing else "incomplete controlled runs",
        "reference_arm": REFERENCE_ARM,
        "historical_protocol_incomparable": {
            "source": "reports/tables/c3_baselines/c3_baseline_report.json",
            "status": "separate historical evidence; not merged",
        },
        "expected_runs": [
            {"model_key": m, "seed": s,
             "status": "COMPLETE" if (m, s) in accepted else "MISSING",
             **({
                 "macro_equal_domain_dice": accepted[(m, s)]["evaluation"]["macro_equal_domain_dice"],
                 "best_epoch": accepted[(m, s)]["manifest"]["best_epoch"],
                 "config_sha256": accepted[(m, s)]["manifest"]["config_sha256"],
                 "best_checkpoint_sha256": accepted[(m, s)]["manifest"]["best_checkpoint_sha256"],
                 "history_sha256": accepted[(m, s)]["manifest"]["history_sha256"],
                 "per_domain": accepted[(m, s)]["evaluation"]["per_domain"],
                 "parameter_count": accepted[(m, s)]["manifest"]["parameters_trainable"],
                 "analytical_compute": accepted[(m, s)]["manifest"]["analytical_compute"],
             }
                if (m, s) in accepted else {})}
            for m, s in sorted(expected)
        ],
        "missing_runs": [{"model_key": m, "seed": s} for m, s in missing],
        "paired_reference": "C1-T same seed; currently NOT_ESTABLISHED until the C1-T runs and all C3 cells are valid",
        "paired_seed_effects": [],
        "protocol_sha256": EXPECTED_PROTOCOL_SHA256,
        "protected_data_accessed": False,
    }
    if c1_export_dir is not None:
        refs = load_c1_reference_exports(c1_export_dir)
        result["paired_seed_effects"] = paired_seed_effects(accepted, refs)
        result["paired_reference"] = "C1-T same seed, exact VAL808 sample roster; descriptive only"
        by_model: dict[str, list[float]] = {model: [] for model in ARCHITECTURES}
        for effect in result["paired_seed_effects"]:
            by_model[effect["model_key"]].append(float(effect["macro_delta"]))
        result["paired_seed_summary"] = {
            model: {
                "n_seeds": len(values),
                "mean_baseline_minus_c1t": float(np.mean(values)) if values else None,
                "sample_sd": float(np.std(values, ddof=1)) if len(values) > 1 else None,
                "min": min(values) if values else None,
                "max": max(values) if values else None,
                "evidence_class": "descriptive across fixed seeds; no population-seed inference",
            }
            for model, values in by_model.items()
        }
    validate_controlled_results_schema(result)
    _atomic_json(Path(output), result)
    return result


def load_c1_reference_exports(export_dir: Path) -> dict[int, list[dict[str, Any]]]:
    """Load authentic same-seed C1-T selected-epoch VAL808 exports."""
    import csv
    directory = Path(export_dir)
    references: dict[int, list[dict[str, Any]]] = {}
    for seed in EXPECTED_SEEDS:
        tag = f"seed{seed}_C1-T"
        prov_path = directory / f"{tag}_provenance.json"
        image_path = directory / f"{tag}_per_image.csv"
        if not prov_path.is_file() or not image_path.is_file():
            raise C3ExecutionError(f"missing C1-T reference export for seed {seed}")
        provenance = json.loads(prov_path.read_text(encoding="utf-8"))
        if provenance.get("synthetic") is not False or provenance.get("protocol_sha256") != EXPECTED_PROTOCOL_SHA256:
            raise C3ExecutionError(f"C1-T reference is synthetic or protocol-mismatched for seed {seed}")
        with image_path.open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        if len(rows) != EXPECTED_COUNTS["VAL"]:
            raise C3ExecutionError(f"C1-T reference VAL count mismatch for seed {seed}")
        ids = [r["sample_id"] for r in rows]
        if len(set(ids)) != EXPECTED_COUNTS["VAL"]:
            raise C3ExecutionError(f"C1-T reference duplicate IDs for seed {seed}")
        for row in rows:
            for field in ("dice", "iou", "precision", "recall"):
                row[field] = float(row[field])
        references[seed] = rows
    return references


def paired_seed_effects(
    accepted: dict[tuple[str, int], dict[str, Any]],
    references: dict[int, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    effects = []
    for model_key in ARCHITECTURES:
        for seed in EXPECTED_SEEDS:
            key = (model_key, seed)
            if key not in accepted:
                continue
            ref = {r["sample_id"]: r for r in references[seed]}
            target_rows = accepted[key]["evaluation"]["per_image"]
            target = {str(r["sample_id"]): r for r in target_rows}
            if set(ref) != set(target):
                raise C3ExecutionError(f"sample roster mismatch for {model_key} seed {seed}")
            per_domain = {}
            for domain in DOMAIN_ORDER:
                shared = [sid for sid, row in ref.items() if row["domain"] == domain]
                if not shared or any(target[sid]["domain"] != ref[sid]["domain"] for sid in shared):
                    raise C3ExecutionError(f"paired domain mismatch for {model_key} seed {seed}")
                ref_mean = float(np.mean([ref[sid]["dice"] for sid in shared]))
                model_mean = float(np.mean([float(target[sid]["dice"]) for sid in shared]))
                per_domain[domain] = {
                    "n": len(shared),
                    "reference_dice": ref_mean,
                    "baseline_dice": model_mean,
                    "baseline_minus_reference": model_mean - ref_mean,
                }
            effects.append({
                "model_key": model_key,
                "seed": seed,
                "estimand": "equal-domain mean of paired-domain per-image Dice difference",
                "per_domain": per_domain,
                "macro_delta": float(np.mean([per_domain[d]["baseline_minus_reference"] for d in DOMAIN_ORDER])),
                "evidence_class": "descriptive paired-seed contrast; no inferential claim",
            })
    return effects


def _write_plan(path: Path) -> None:
    payload = {
        "schema": "controlled_c3_experiment_plan_v1",
        "status": "PREPARED_NOT_EXECUTED",
        "reference_arm": REFERENCE_ARM,
        "architecture_keys": list(ARCHITECTURES),
        "seeds": list(EXPECTED_SEEDS),
        "planned_real_runs": len(ARCHITECTURES) * len(EXPECTED_SEEDS),
        "training_priority": "C1 six-run campaign takes priority; do not start C3 training concurrently.",
        "real_execution": "BLOCKED_PENDING_SEPARATE_AUTHORIZATION",
        "configurations": [build_experiment_config(m, s) for m in ARCHITECTURES for s in EXPECTED_SEEDS],
        "protocol_sha256": EXPECTED_PROTOCOL_SHA256,
    }
    _atomic_json(path, payload)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Controlled C3 baseline preparation (synthetic smoke only).")
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
    p_run = sub.add_parser("run-real")
    p_run.add_argument("--model", choices=tuple(ARCHITECTURES), required=True)
    p_run.add_argument("--seed", type=int, choices=EXPECTED_SEEDS, required=True)
    p_agg = sub.add_parser("aggregate")
    p_agg.add_argument("--runs-root", type=Path, default=ROOT / "experiments" / "c3_controlled")
    p_agg.add_argument("--c1-export-dir", type=Path, required=True)
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
        raise C3ExecutionError("C3_REAL_EXECUTION_BLOCKED_PENDING_SEPARATE_AUTHORIZATION")
    if args.command == "aggregate":
        runs = [args.runs_root / model / f"seed{seed}" for model in ARCHITECTURES for seed in EXPECTED_SEEDS]
        existing = [p for p in runs if p.is_dir()]
        result = aggregate_controlled_results(existing, args.out, c1_export_dir=args.c1_export_dir)
        print(f"{result['status']}: {args.out}; missing={len(result['missing_runs'])}")
        return 0 if not result["missing_runs"] or args.allow_incomplete else 3
    if args.command == "benchmark":
        print(json.dumps(benchmark_synthetic_step(args.model, device=args.device,
                                                  image_size=args.image_size, batch_size=args.batch_size,
                                                  measured_steps=args.measured_steps), indent=2))
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
