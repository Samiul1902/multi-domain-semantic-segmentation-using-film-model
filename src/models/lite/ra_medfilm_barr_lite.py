"""Separate compact G and R_psi architectures for RA-MedFiLM-BARR-Lite.

These are new model families. Original FULL modules and checkpoints are never
modified or implicitly loaded. Router and safety components remain required.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import random
import tempfile
from typing import Mapping, Sequence

import numpy as np
import torch
from torch import Tensor, nn
from torch.nn import functional as F


@dataclass(frozen=True)
class LiteVariantSpec:
    """Immutable architecture definition for one Lite candidate."""

    variant_id: str
    global_channels: tuple[int, int, int, int, int]
    refiner_channels: tuple[int, int, int, int, int]
    embedding_dim: int
    film_hidden_dim: int
    block_kind: str
    skip_fusion: str

    def __post_init__(self) -> None:
        if self.block_kind not in {"standard", "depthwise"}:
            raise ValueError(f"unsupported block_kind: {self.block_kind}")
        if self.skip_fusion not in {"concat", "add"}:
            raise ValueError(f"unsupported skip_fusion: {self.skip_fusion}")
        if self.embedding_dim < 1 or self.film_hidden_dim < 1:
            raise ValueError("embedding and FiLM hidden dimensions must be positive")
        for label, widths in (
            ("global_channels", self.global_channels),
            ("refiner_channels", self.refiner_channels),
        ):
            if len(widths) != 5 or any(width < 4 for width in widths):
                raise ValueError(f"{label} must contain five widths of at least four")
            if any(width % 4 for width in widths):
                raise ValueError(f"{label} widths must be divisible by four for GroupNorm")

    def sha256(self) -> str:
        payload = json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


CANDIDATE_SPECS: Mapping[str, LiteVariantSpec] = {
    "width_compact": LiteVariantSpec(
        variant_id="ra_medfilm_barr_lite_width_compact_v1",
        global_channels=(12, 24, 48, 96, 128),
        refiner_channels=(8, 16, 32, 48, 64),
        embedding_dim=16,
        film_hidden_dim=32,
        block_kind="standard",
        skip_fusion="concat",
    ),
    "depthwise_compact": LiteVariantSpec(
        variant_id="ra_medfilm_barr_lite_depthwise_compact_v1",
        global_channels=(12, 24, 48, 96, 128),
        refiner_channels=(8, 16, 32, 48, 64),
        embedding_dim=16,
        film_hidden_dim=32,
        block_kind="depthwise",
        skip_fusion="concat",
    ),
    "ultralite_depthwise_add": LiteVariantSpec(
        variant_id="ra_medfilm_barr_lite_ultralite_depthwise_add_v1",
        global_channels=(8, 16, 24, 32, 48),
        refiner_channels=(8, 8, 16, 24, 32),
        embedding_dim=8,
        film_hidden_dim=16,
        block_kind="depthwise",
        skip_fusion="add",
    ),
}

LITE_SEEDS = (42, 123, 3407)
LITE_TRAINING_PRESET: Mapping[str, object] = {
    "protocol_id": "RA_MEDFILM_BARR_LITE_SECONDARY_V1",
    "status": "PROPOSED_UNAPPROVED_NOT_EXECUTED",
    "seed_list": LITE_SEEDS,
    "train_manifest": "manifests/phase4_v3/train.csv",
    "train_count": 5832,
    "validation_manifest": "manifests/phase4_v3/val.csv",
    "validation_count": 808,
    "prohibited_populations": ("TEST", "ROUTER_HOLDOUT", "EXTERNAL", "QUARANTINE"),
    "task_ids": {"ISIC": 0, "BUSI": 1, "KVASIR": 2, "KUB": 3},
    "input": "512x512 RGB, binary foreground",
    "optimizer": "AdamW",
    "learning_rate": 1e-4,
    "weight_decay": 1e-4,
    "batch_size": 4,
    "max_epochs": 100,
    "selection": "equal-domain macro Dice on VAL808; tie by lower loss then earlier epoch",
    "selection_is_validation_consumed": True,
    "training_recipe_basis": "compatible C1 recipe; separate Lite experiment, not a C1 modification",
    "loss": {
        "supervised_bce_weight": 0.5,
        "supervised_soft_dice_weight": 0.5,
        "dice_epsilon": 1e-6,
        "teacher_soft_mask_weight": 0.5,
        "teacher_temperature": 2.0,
        "intermediate_feature_weight_default": 0.0,
        "intermediate_feature_policy": (
            "only enable with an explicitly trained dimension-matching projection or "
            "same-shaped taps; original FULL/Lite taps differ, so direct feature loss is invalid"
        ),
    },
    "scheduler": "CosineAnnealingLR(T_max=100)",
    "early_stop_patience": 15,
    "augmentation": (
        "horizontal flip 0.5; rotation 5 degrees; brightness/contrast 0.1, "
        "matching C1 recipe; verify compatible tensor mapping before authorization"
    ),
    "seed_independence": (
        "each seed retrains G, R_psi, B_phi, and S_omega; never count downstream "
        "seeds over one shared G as independent full-system runs"
    ),
    "component_training_dependencies": (
        "train G per seed; train R_psi per seed on eligible TRAIN crops with same-seed G; "
        "derive GT-free Lite-specific router features and cross-fitted paired-gain labels "
        "from eligible TRAIN only; fit B_phi and S_omega per seed with frozen dependencies"
    ),
    "teacher": {
        "source": "canonical seed-42 FULL checkpoint bundle",
        "use": "optional GlobalMedFiLM soft-mask distillation on authorized TRAIN inputs only",
        "teacher_bundle_verified": True,
        "new_teacher_inference_performed": False,
        "teacher_outputs_cached_for_training": False,
    },
    "router_safety": (
        "retrain/calibrate per Lite seed from eligible training-derived data; "
        "do not load original B_phi/S_omega weights as validated Lite weights"
    ),
}

MODEL_COMPARISON_MATRIX: tuple[dict[str, str], ...] = (
    {
        "key": "ra_medfilm_barr_full",
        "identity": "RA-MedFiLM-BARR (FULL)",
        "role": "canonical_primary_method",
        "evidence_status": "existing_method; preserve as primary",
    },
    *(
        {
            "key": f"ra_medfilm_barr_lite_{key}",
            "identity": f"RA-MedFiLM-BARR-Lite/{key}",
            "role": "additional_candidate_not_yet_accuracy_evaluated",
            "evidence_status": "new training required; synthetic efficiency only",
        }
        for key in CANDIDATE_SPECS
    ),
    {
        "key": "global_medfilm",
        "identity": "GlobalMedFiLM",
        "role": "internal_ablation_reference",
        "evidence_status": "historical; not the complete proposed method",
    },
    *(
        {
            "key": key,
            "identity": label,
            "role": "external_architecture_baseline",
            "evidence_status": "C3 protocol-matched results not established",
        }
        for key, label in (
            ("unet", "U-Net"),
            ("unetpp", "U-Net++"),
            ("attention_unet", "Attention U-Net"),
            ("deeplabv3plus", "DeepLabV3+"),
            ("transformer_mit_unet", "Transformer/MiT-style U-Net"),
        )
    ),
    {
        "key": "mobilenetv3_large_encoder_decoder",
        "identity": "MobileNetV3-Large encoder-decoder",
        "role": "literature_or_separately_implemented_lightweight_reference",
        "evidence_status": "not implemented here; no matched local score",
    },
    {
        "key": "fast_scnn",
        "identity": "Fast-SCNN",
        "role": "literature_or_separately_implemented_lightweight_reference",
        "evidence_status": "not implemented here; no matched local score",
    },
)


def _groups(channels: int) -> int:
    for candidate in (8, 4, 2, 1):
        if channels % candidate == 0:
            return candidate
    return 1


class LiteResidualBlock(nn.Module):
    """Residual block with standard or depthwise-separable convolutions."""

    def __init__(self, in_channels: int, out_channels: int, kind: str) -> None:
        super().__init__()
        if kind == "standard":
            self.conv1: nn.Module = nn.Conv2d(
                in_channels, out_channels, 3, padding=1, bias=False
            )
            self.norm1 = nn.GroupNorm(_groups(out_channels), out_channels)
            self.conv2: nn.Module = nn.Conv2d(
                out_channels, out_channels, 3, padding=1, bias=False
            )
            self.norm2 = nn.GroupNorm(_groups(out_channels), out_channels)
        elif kind == "depthwise":
            self.conv1 = nn.Sequential(
                nn.Conv2d(in_channels, in_channels, 3, padding=1,
                          groups=in_channels, bias=False),
                nn.GroupNorm(_groups(in_channels), in_channels),
                nn.SiLU(inplace=True),
                nn.Conv2d(in_channels, out_channels, 1, bias=False),
            )
            self.norm1 = nn.GroupNorm(_groups(out_channels), out_channels)
            self.conv2 = nn.Sequential(
                nn.Conv2d(out_channels, out_channels, 3, padding=1,
                          groups=out_channels, bias=False),
                nn.GroupNorm(_groups(out_channels), out_channels),
                nn.SiLU(inplace=True),
                nn.Conv2d(out_channels, out_channels, 1, bias=False),
            )
            self.norm2 = nn.GroupNorm(_groups(out_channels), out_channels)
        else:
            raise ValueError(f"unsupported residual block kind: {kind}")
        self.activation = nn.SiLU(inplace=True)
        self.skip = (
            nn.Identity()
            if in_channels == out_channels
            else nn.Conv2d(in_channels, out_channels, 1, bias=False)
        )

    def forward(self, inputs: Tensor) -> Tensor:
        residual = self.skip(inputs)
        output = self.conv1(inputs)
        output = self.activation(self.norm1(output))
        output = self.norm2(self.conv2(output))
        return self.activation(output + residual)


class LiteFiLM(nn.Module):
    """Bounded task modulation, identity initialized like the canonical model."""

    def __init__(self, embedding_dim: int, hidden_dim: int, channels: int) -> None:
        super().__init__()
        self.hidden = nn.Sequential(nn.Linear(embedding_dim, hidden_dim), nn.SiLU())
        self.output = nn.Linear(hidden_dim, 2 * channels)
        nn.init.xavier_uniform_(self.hidden[0].weight)
        nn.init.zeros_(self.hidden[0].bias)
        nn.init.zeros_(self.output.weight)
        nn.init.zeros_(self.output.bias)

    def forward(self, feature: Tensor, embedding: Tensor) -> Tensor:
        gamma_raw, beta_raw = self.output(self.hidden(embedding)).chunk(2, dim=1)
        gamma = torch.tanh(gamma_raw).to(feature.dtype)[:, :, None, None]
        beta = torch.tanh(beta_raw).to(feature.dtype)[:, :, None, None]
        return (1.0 + gamma) * feature + beta


class LiteDecoderBlock(nn.Module):
    def __init__(
        self,
        input_channels: int,
        skip_channels: int,
        output_channels: int,
        kind: str,
        fusion: str,
    ) -> None:
        super().__init__()
        self.fusion = fusion
        if fusion == "concat":
            self.input_projection = nn.Identity()
            self.skip_projection = nn.Identity()
            block_input = input_channels + skip_channels
        elif fusion == "add":
            self.input_projection = (
                nn.Identity()
                if input_channels == output_channels
                else nn.Conv2d(input_channels, output_channels, 1, bias=False)
            )
            self.skip_projection = nn.Conv2d(skip_channels, output_channels, 1, bias=False)
            block_input = output_channels
        else:
            raise ValueError(f"unsupported skip fusion: {fusion}")
        self.block = LiteResidualBlock(block_input, output_channels, kind)

    def forward(self, inputs: Tensor, skip: Tensor) -> Tensor:
        inputs = F.interpolate(inputs, size=skip.shape[-2:], mode="bilinear",
                               align_corners=False)
        if self.fusion == "concat":
            fused = torch.cat((inputs, skip), dim=1)
        else:
            fused = self.input_projection(inputs) + self.skip_projection(skip)
        return self.block(fused)


class LiteGlobalMedFiLM(nn.Module):
    """Compact shared four-task global segmenter; returns foreground logits."""

    def __init__(self, spec: LiteVariantSpec, task_count: int = 4) -> None:
        super().__init__()
        self.spec = spec
        self.task_count = int(task_count)
        if self.task_count != 4:
            raise ValueError("RA-MedFiLM-BARR-Lite requires exactly four task identities")
        c1, c2, c3, c4, cb = spec.global_channels
        kind = spec.block_kind
        self.channels = spec.global_channels
        self.task_embedding = nn.Embedding(self.task_count, spec.embedding_dim)
        nn.init.normal_(self.task_embedding.weight, mean=0.0, std=0.02)
        self.encoder1 = LiteResidualBlock(3, c1, kind)
        self.encoder2 = LiteResidualBlock(c1, c2, kind)
        self.encoder3 = LiteResidualBlock(c2, c3, kind)
        self.encoder4 = LiteResidualBlock(c3, c4, kind)
        self.bridge = LiteResidualBlock(c4, cb, kind)
        self.pool = nn.MaxPool2d(2, 2)
        self.decoder4 = LiteDecoderBlock(cb, c4, c4, kind, spec.skip_fusion)
        self.decoder3 = LiteDecoderBlock(c4, c3, c3, kind, spec.skip_fusion)
        self.decoder2 = LiteDecoderBlock(c3, c2, c2, kind, spec.skip_fusion)
        self.decoder1 = LiteDecoderBlock(c2, c1, c1, kind, spec.skip_fusion)
        self.film_layers = nn.ModuleDict({
            "bridge": LiteFiLM(spec.embedding_dim, spec.film_hidden_dim, cb),
            "decoder4": LiteFiLM(spec.embedding_dim, spec.film_hidden_dim, c4),
            "decoder3": LiteFiLM(spec.embedding_dim, spec.film_hidden_dim, c3),
            "decoder2": LiteFiLM(spec.embedding_dim, spec.film_hidden_dim, c2),
            "decoder1": LiteFiLM(spec.embedding_dim, spec.film_hidden_dim, c1),
        })
        self.head = nn.Conv2d(c1, 1, 1)

    def _forward_with_features(
        self, images: Tensor, task_ids: Tensor
    ) -> tuple[Tensor, dict[str, Tensor]]:
        if images.ndim != 4 or images.shape[1] != 3:
            raise ValueError("images must have shape [B, 3, H, W]")
        if min(images.shape[-2:]) < 32:
            raise ValueError("spatial dimensions must both be at least 32")
        if task_ids.ndim != 1 or task_ids.shape[0] != images.shape[0]:
            raise ValueError("task_ids must have shape [B]")
        if task_ids.dtype not in (torch.int32, torch.int64):
            raise ValueError("task_ids must use an integer tensor dtype")
        if task_ids.numel() == 0 or int(task_ids.min()) < 0 or int(task_ids.max()) >= 4:
            raise ValueError("task_ids must contain IDs in [0, 3]")
        if not torch.isfinite(images).all():
            raise ValueError("images must contain only finite values")
        embedding = self.task_embedding(task_ids)
        skip1 = self.encoder1(images)
        skip2 = self.encoder2(self.pool(skip1))
        skip3 = self.encoder3(self.pool(skip2))
        skip4 = self.encoder4(self.pool(skip3))
        bridge = self.bridge(self.pool(skip4))
        taps = {"bridge": bridge}
        bridge = self.film_layers["bridge"](bridge, embedding)
        decoded = self.decoder4(bridge, skip4)
        decoded = self.film_layers["decoder4"](decoded, embedding)
        decoded = self.decoder3(decoded, skip3)
        decoded = self.film_layers["decoder3"](decoded, embedding)
        decoded = self.decoder2(decoded, skip2)
        taps["decoder2"] = decoded
        decoded = self.film_layers["decoder2"](decoded, embedding)
        decoded = self.decoder1(decoded, skip1)
        taps["decoder1"] = decoded
        decoded = self.film_layers["decoder1"](decoded, embedding)
        logits = self.head(decoded)
        if logits.shape[-2:] != images.shape[-2:]:
            logits = F.interpolate(logits, size=images.shape[-2:], mode="bilinear",
                                   align_corners=False)
        return logits, taps

    def forward(self, images: Tensor, task_ids: Tensor) -> Tensor:
        logits, _ = self._forward_with_features(images, task_ids)
        return logits

    def forward_with_features(
        self, images: Tensor, task_ids: Tensor
    ) -> tuple[Tensor, dict[str, Tensor]]:
        """Return logits and the canonical pre-FiLM router feature taps."""
        return self._forward_with_features(images, task_ids)


class LiteRegionalRefiner(nn.Module):
    """Compact four-channel regional refiner returning one foreground logit."""

    def __init__(self, spec: LiteVariantSpec) -> None:
        super().__init__()
        self.spec = spec
        c1, c2, c3, c4, cb = spec.refiner_channels
        kind = spec.block_kind
        self.stem = nn.Sequential(
            nn.Conv2d(4, c1, 3, padding=1, bias=False),
            nn.GroupNorm(_groups(c1), c1),
            nn.SiLU(inplace=True),
        )
        self.encoder1 = LiteResidualBlock(c1, c1, kind)
        self.encoder2 = LiteResidualBlock(c1, c2, kind)
        self.encoder3 = LiteResidualBlock(c2, c3, kind)
        self.encoder4 = LiteResidualBlock(c3, c4, kind)
        self.encoder5 = LiteResidualBlock(c4, cb, kind)
        self.bridge = LiteResidualBlock(cb, cb, kind)
        self.pool = nn.MaxPool2d(2, 2)
        self.decoder4 = LiteDecoderBlock(cb, c4, c4, kind, spec.skip_fusion)
        self.decoder3 = LiteDecoderBlock(c4, c3, c3, kind, spec.skip_fusion)
        self.decoder2 = LiteDecoderBlock(c3, c2, c2, kind, spec.skip_fusion)
        self.decoder1 = LiteDecoderBlock(c2, c1, c1, kind, spec.skip_fusion)
        self.head = nn.Conv2d(c1, 1, 1)

    def forward(self, inputs: Tensor) -> Tensor:
        if inputs.ndim != 4 or inputs.shape[1] != 4:
            raise ValueError("refiner inputs must have shape [B, 4, H, W]")
        if min(inputs.shape[-2:]) < 32:
            raise ValueError("refiner spatial dimensions must both be at least 32")
        if not torch.isfinite(inputs).all():
            raise ValueError("refiner inputs must contain only finite values")
        skip1 = self.encoder1(self.stem(inputs))
        skip2 = self.encoder2(self.pool(skip1))
        skip3 = self.encoder3(self.pool(skip2))
        skip4 = self.encoder4(self.pool(skip3))
        skip5 = self.encoder5(self.pool(skip4))
        bridge = self.bridge(self.pool(skip5))
        decoded = self.decoder4(bridge, skip4)
        decoded = self.decoder3(decoded, skip3)
        decoded = self.decoder2(decoded, skip2)
        decoded = self.decoder1(decoded, skip1)
        logits = self.head(decoded)
        if logits.shape[-2:] != inputs.shape[-2:]:
            logits = F.interpolate(logits, size=inputs.shape[-2:], mode="bilinear",
                                   align_corners=False)
        return logits


def count_unique_parameters(*modules: nn.Module) -> int:
    """Count registered parameter objects once, even when modules are shared."""
    seen: set[int] = set()
    count = 0
    for module in modules:
        for parameter in module.parameters():
            if id(parameter) not in seen:
                seen.add(id(parameter))
                count += parameter.numel()
    return count


def parameter_inventory(modules: Mapping[str, nn.Module]) -> dict[str, object]:
    """Return unique, trainable, and frozen counts with cross-module deduplication."""
    seen: set[int] = set()
    total = trainable = frozen = 0
    breakdown: dict[str, dict[str, int]] = {}
    for name, module in modules.items():
        local_seen: set[int] = set()
        local_total = local_trainable = local_frozen = 0
        for parameter in module.parameters():
            identity = id(parameter)
            if identity in local_seen:
                continue
            local_seen.add(identity)
            amount = parameter.numel()
            local_total += amount
            if parameter.requires_grad:
                local_trainable += amount
            else:
                local_frozen += amount
            if identity not in seen:
                seen.add(identity)
                total += amount
                if parameter.requires_grad:
                    trainable += amount
                else:
                    frozen += amount
        breakdown[name] = {
            "unique_parameters": local_total,
            "trainable_parameters": local_trainable,
            "frozen_parameters": local_frozen,
        }
    return {
        "unique_parameters": total,
        "trainable_parameters": trainable,
        "frozen_parameters": frozen,
        "by_component": breakdown,
    }


@dataclass(frozen=True)
class DistillationLossWeights:
    supervised_bce: float = 0.5
    supervised_dice: float = 0.5
    teacher_soft_mask: float = 0.5
    intermediate_feature: float = 0.0
    temperature: float = 2.0

    def __post_init__(self) -> None:
        values = (
            self.supervised_bce, self.supervised_dice,
            self.teacher_soft_mask, self.intermediate_feature,
        )
        if any(value < 0 for value in values) or self.temperature <= 0:
            raise ValueError("loss weights must be nonnegative and temperature positive")


def binary_distillation_loss(
    student_logits: Tensor,
    targets: Tensor,
    *,
    teacher_logits: Tensor | None = None,
    student_features: Tensor | None = None,
    teacher_features: Tensor | None = None,
    weights: DistillationLossWeights = DistillationLossWeights(),
) -> tuple[Tensor, dict[str, Tensor]]:
    """Supervised BCE+Dice with optional teacher soft-mask and feature losses."""
    if student_logits.shape != targets.shape:
        raise ValueError("student logits and binary targets must have identical shapes")
    if not torch.isfinite(student_logits).all() or not torch.isfinite(targets).all():
        raise ValueError("student logits and targets must be finite")
    if targets.numel() == 0 or bool(((targets < 0) | (targets > 1)).any()):
        raise ValueError("targets must be nonempty binary/probability masks in [0, 1]")
    bce = F.binary_cross_entropy_with_logits(student_logits, targets)
    probabilities = torch.sigmoid(student_logits)
    reduce_dims = tuple(range(1, student_logits.ndim))
    intersection = (probabilities * targets).sum(dim=reduce_dims)
    denominator = probabilities.sum(dim=reduce_dims) + targets.sum(dim=reduce_dims)
    dice = 1.0 - ((2.0 * intersection + 1e-6) / (denominator + 1e-6)).mean()
    losses = {
        "supervised_bce": bce,
        "supervised_dice": dice,
        "teacher_soft_mask": student_logits.new_zeros(()),
        "intermediate_feature": student_logits.new_zeros(()),
    }
    if weights.teacher_soft_mask > 0:
        if teacher_logits is None or teacher_logits.shape != student_logits.shape:
            raise ValueError("teacher logits matching student shape are required for distillation")
        if not torch.isfinite(teacher_logits).all():
            raise ValueError("teacher logits must be finite")
        temperature = weights.temperature
        teacher_probability = torch.sigmoid(
            teacher_logits.detach().clone() / temperature
        )
        losses["teacher_soft_mask"] = F.binary_cross_entropy_with_logits(
            student_logits / temperature, teacher_probability
        ) * temperature**2
    if weights.intermediate_feature > 0:
        if (student_features is None or teacher_features is None
                or student_features.shape != teacher_features.shape):
            raise ValueError("matching intermediate features are required when weighted")
        if not torch.isfinite(student_features).all() or not torch.isfinite(teacher_features).all():
            raise ValueError("intermediate features must be finite")
        losses["intermediate_feature"] = F.mse_loss(
            student_features, teacher_features.detach().clone()
        )
    total = (
        weights.supervised_bce * losses["supervised_bce"]
        + weights.supervised_dice * losses["supervised_dice"]
        + weights.teacher_soft_mask * losses["teacher_soft_mask"]
        + weights.intermediate_feature * losses["intermediate_feature"]
    )
    return total, losses


def lite_distillation_training_step(
    student: LiteGlobalMedFiLM,
    optimizer: torch.optim.Optimizer,
    images: Tensor,
    task_ids: Tensor,
    targets: Tensor,
    *,
    teacher_logits: Tensor | None,
    teacher_features: Tensor | None = None,
    feature_tap: str = "decoder2",
    weights: DistillationLossWeights = DistillationLossWeights(),
) -> dict[str, float]:
    """Run one supervised/teacher-distilled synthetic-or-training batch.

    The caller owns data eligibility and teacher inference. This function reads
    no files and rejects feature distillation unless the selected maps match.
    """
    if (weights.teacher_soft_mask > 0
            and (teacher_logits is None or teacher_logits.shape != targets.shape)):
        raise ValueError("teacher logits must match the target mask shape")
    student.train()
    optimizer.zero_grad(set_to_none=True)
    logits, student_taps = student.forward_with_features(images, task_ids)
    selected_student_features = None
    selected_teacher_features = None
    if weights.intermediate_feature > 0:
        if feature_tap not in student_taps or teacher_features is None:
            raise ValueError("requested intermediate feature tap is unavailable")
        selected_student_features = student_taps[feature_tap]
        selected_teacher_features = teacher_features.detach().clone()
    loss, parts = binary_distillation_loss(
        logits,
        targets,
        teacher_logits=teacher_logits,
        student_features=selected_student_features,
        teacher_features=selected_teacher_features,
        weights=weights,
    )
    loss.backward()
    optimizer.step()
    return {
        "total": float(loss.detach()),
        **{name: float(value.detach()) for name, value in parts.items()},
    }


def teacher_bundle_sha256(component_hashes: Mapping[str, str]) -> str:
    """Hash the exact four-component teacher identity in canonical key order."""
    required = {"G", "R_psi", "B_phi", "S_omega"}
    if set(component_hashes) != required:
        raise ValueError(f"teacher component hashes must contain exactly {sorted(required)}")
    for name, digest in component_hashes.items():
        if (len(digest) != 64
                or any(character not in "0123456789abcdef" for character in digest.lower())):
            raise ValueError(f"{name} teacher checkpoint hash must be 64 hex characters")
    payload = json.dumps(dict(sorted(component_hashes.items())), separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def atomic_save_lite_checkpoint(
    path: Path,
    *,
    model: nn.Module,
    spec: LiteVariantSpec,
    seed: int,
    teacher_checkpoint_sha256: str | None = None,
    teacher_component_sha256: Mapping[str, str] | None = None,
    run_id: str,
    training_protocol_id: str,
) -> None:
    """Atomically save weights with explicit architecture and teacher provenance."""
    if seed < 0 or not run_id or not training_protocol_id:
        raise ValueError("seed, run_id, and training_protocol_id are required")
    component_hashes = None
    if teacher_component_sha256 is not None:
        component_hashes = dict(sorted(teacher_component_sha256.items()))
        composite_hash = teacher_bundle_sha256(component_hashes)
        if teacher_checkpoint_sha256 is not None and teacher_checkpoint_sha256 != composite_hash:
            raise ValueError("teacher bundle hash does not match component hashes")
        teacher_checkpoint_sha256 = composite_hash
    if teacher_checkpoint_sha256 is not None and (
        len(teacher_checkpoint_sha256) != 64
        or any(character not in "0123456789abcdef" for character in teacher_checkpoint_sha256.lower())
    ):
        raise ValueError("teacher checkpoint SHA-256 must be 64 hexadecimal characters")
    payload = {
        "model_identity": "RA-MedFiLM-BARR-Lite",
        "architecture_id": spec.variant_id,
        "architecture_sha256": spec.sha256(),
        "spec": asdict(spec),
        "seed": seed,
        "run_id": run_id,
        "teacher_checkpoint_sha256": teacher_checkpoint_sha256,
        "teacher_component_sha256": component_hashes,
        "training_protocol_id": training_protocol_id,
        "state_dict": model.state_dict(),
    }
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp",
                                          dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            torch.save(payload, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, path)
    except Exception:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)
        raise


def seed_lite_training(seed: int) -> None:
    """Set all in-process RNGs and deterministic backend flags for Lite runs."""
    if seed < 0:
        raise ValueError("seed must be nonnegative")
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def seed_lite_worker(worker_id: int) -> None:
    """Seed NumPy and Python RNGs from PyTorch's reproducible worker seed."""
    del worker_id
    worker_seed = torch.initial_seed() % (2**32)
    random.seed(worker_seed)
    np.random.seed(worker_seed)


def load_lite_checkpoint(
    path: Path,
    *,
    model: nn.Module,
    spec: LiteVariantSpec,
    expected_teacher_checkpoint_sha256: str | None,
    expected_seed: int,
    expected_run_id: str,
    expected_training_protocol_id: str,
    expected_teacher_component_sha256: Mapping[str, str] | None = None,
) -> dict[str, object]:
    """Load only an exact Lite family/configuration and declared teacher family."""
    payload = torch.load(Path(path), map_location="cpu", weights_only=True)
    if not isinstance(payload, dict):
        raise ValueError("Lite checkpoint payload must be a mapping")
    if payload.get("model_identity") != "RA-MedFiLM-BARR-Lite":
        raise ValueError("checkpoint belongs to a different model family")
    if payload.get("architecture_id") != spec.variant_id:
        raise ValueError("Lite checkpoint architecture ID mismatch")
    if payload.get("architecture_sha256") != spec.sha256():
        raise ValueError("Lite checkpoint architecture configuration mismatch")
    if payload.get("seed") != expected_seed or payload.get("run_id") != expected_run_id:
        raise ValueError("Lite checkpoint run/seed identity mismatch")
    if payload.get("training_protocol_id") != expected_training_protocol_id:
        raise ValueError("Lite checkpoint training protocol mismatch")
    if payload.get("teacher_checkpoint_sha256") != expected_teacher_checkpoint_sha256:
        raise ValueError("Lite checkpoint teacher provenance mismatch")
    stored_components = payload.get("teacher_component_sha256")
    if expected_teacher_component_sha256 is not None:
        expected_components = dict(sorted(expected_teacher_component_sha256.items()))
        if stored_components != expected_components:
            raise ValueError("Lite checkpoint teacher component provenance mismatch")
        if teacher_bundle_sha256(expected_components) != expected_teacher_checkpoint_sha256:
            raise ValueError("expected teacher bundle hash does not match its components")
    elif stored_components is not None:
        raise ValueError("expected teacher component provenance was not provided")
    state_dict = payload.get("state_dict")
    if not isinstance(state_dict, dict):
        raise ValueError("Lite checkpoint has no valid state_dict")
    model.load_state_dict(state_dict, strict=True)
    return payload
