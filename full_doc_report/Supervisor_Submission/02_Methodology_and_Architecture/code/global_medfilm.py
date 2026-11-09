"""Phase 21 — GLOBAL MedFiLM reference (task-conditioned, single shared network).

Frozen BEFORE training. Exactly ONE architecture, ONE logical run, no sweep.

Design (reconstructed from the best-supported historical GLOBAL MedFiLM,
see reports/audits/phase21_legacy_medfilm_architecture_audit.json):

* ONE shared encoder-decoder across ISIC / BUSI / KVASIR / KUB.
* Task conditioning enters ONLY through a task embedding + FiLM sites.
  ``task_id`` is never concatenated, never a channel, never a separate head.
* FiLM: ``F_hat = (1 + gamma(t)) * F + beta(t)`` with
  ``gamma = tanh(gamma_raw)`` and ``beta = tanh(beta_raw)``.
  The FiLM output projection is zero-initialised, so every site begins as an
  EXACT identity and task conditioning is learned, not injected.
* FiLM sites (5): ``bridge, decoder4, decoder3, decoder2, decoder1``.
* Residual blocks: YES. Squeeze-and-Excitation: NO. Deep supervision: NO.
* ONE shared 1x1 output head producing a single foreground logit
  (no dataset-specific head, no per-task head).

Explicitly ABSENT (Phase 21 is a GLOBAL reference only): ROI proposal,
localizer, regional refiner, high-resolution crop branch, global-regional
fusion, benefit predictor, counterfactual refinement gain, resource/budget
router, adaptive conditional computation, pruning/quantization/distillation,
architecture search, TEST evaluation.
"""
from __future__ import annotations

import torch
from torch import nn
import torch.nn.functional as F

__all__ = [
    "FeatureWiseLinearModulation",
    "ResidualBlock",
    "DecoderBlock",
    "GlobalMedFiLM",
    "GLOBAL_MEDFILM_ARCHITECTURE_ID",
    "GLOBAL_MEDFILM_FILM_SITES",
    "GLOBAL_MEDFILM_CHANNELS",
    "GLOBAL_MEDFILM_TASK_EMBEDDING_DIM",
    "GLOBAL_MEDFILM_FILM_HIDDEN_DIM",
]

GLOBAL_MEDFILM_ARCHITECTURE_ID = "global_medfilm_shared_residual_unet_film5_no_se_no_deep_supervision_v1"
GLOBAL_MEDFILM_FILM_SITES = ("bridge", "decoder4", "decoder3", "decoder2", "decoder1")
GLOBAL_MEDFILM_CHANNELS = (24, 48, 96, 192, 256)
GLOBAL_MEDFILM_TASK_EMBEDDING_DIM = 32
GLOBAL_MEDFILM_FILM_HIDDEN_DIM = 64

FORBIDDEN_MODULE_TOKENS = (
    "localizer", "proposal", "roi", "regional", "refiner", "crop",
    "benefit", "router", "budget", "counterfactual", "distill",
    "prune", "quant", "nas",
)


def _group_count(channels: int) -> int:
    """Legacy grouping rule: first of (8, 4, 2, 1) that divides the width."""
    for groups in (8, 4, 2, 1):
        if channels % groups == 0:
            return groups
    return 1


class ConvNormAct(nn.Sequential):
    def __init__(self, in_channels: int, out_channels: int, kernel_size: int = 3):
        super().__init__(
            nn.Conv2d(in_channels, out_channels, kernel_size=kernel_size,
                      padding=kernel_size // 2, bias=False),
            nn.GroupNorm(_group_count(out_channels), out_channels),
            nn.SiLU(inplace=True),
        )


class ResidualBlock(nn.Module):
    """ConvNormAct + ConvNorm + skip(1x1 when channels differ) + SiLU."""

    def __init__(self, in_channels: int, out_channels: int):
        super().__init__()
        self.block1 = ConvNormAct(in_channels, out_channels)
        self.block2 = nn.Sequential(
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.GroupNorm(_group_count(out_channels), out_channels),
        )
        self.skip = (
            nn.Identity()
            if in_channels == out_channels
            else nn.Conv2d(in_channels, out_channels, kernel_size=1, bias=False)
        )
        self.activation = nn.SiLU(inplace=True)

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        residual = self.skip(inputs)
        output = self.block2(self.block1(inputs))
        return self.activation(output + residual)


class DecoderBlock(nn.Module):
    def __init__(self, in_channels: int, skip_channels: int, out_channels: int):
        super().__init__()
        self.block = ResidualBlock(in_channels + skip_channels, out_channels)

    def forward(self, inputs: torch.Tensor, skip: torch.Tensor) -> torch.Tensor:
        inputs = F.interpolate(inputs, size=skip.shape[-2:], mode="bilinear",
                               align_corners=False)
        return self.block(torch.cat([inputs, skip], dim=1))


class FeatureWiseLinearModulation(nn.Module):
    """Task-conditioned channel modulation (legacy FiLM, reused verbatim in form).

    ``F_hat = (1 + gamma(t)) * F + beta(t)``

    The output projection is zero-initialised, so every site begins as an exact
    identity transformation while remaining trainable.
    """

    def __init__(self, embedding_dim: int, hidden_dim: int, channels: int):
        super().__init__()
        self.channels = int(channels)
        self.hidden = nn.Sequential(
            nn.Linear(int(embedding_dim), int(hidden_dim)),
            nn.SiLU(inplace=True),
        )
        self.output = nn.Linear(int(hidden_dim), 2 * self.channels)
        nn.init.xavier_uniform_(self.hidden[0].weight)
        nn.init.zeros_(self.hidden[0].bias)
        nn.init.zeros_(self.output.weight)
        nn.init.zeros_(self.output.bias)

    def parameters_from_embedding(self, task_embedding: torch.Tensor):
        parameters = self.output(self.hidden(task_embedding))
        gamma_raw, beta_raw = parameters.chunk(2, dim=1)
        # Bounded modulation: protects early training from large task-conditioned
        # scale/shift values.
        gamma = torch.tanh(gamma_raw)
        beta = torch.tanh(beta_raw)
        return gamma, beta

    def forward(self, features: torch.Tensor, task_embedding: torch.Tensor):
        gamma, beta = self.parameters_from_embedding(task_embedding)
        gamma_spatial = gamma.to(features.dtype).unsqueeze(-1).unsqueeze(-1)
        beta_spatial = beta.to(features.dtype).unsqueeze(-1).unsqueeze(-1)
        modulated = (1.0 + gamma_spatial) * features + beta_spatial
        return modulated, gamma, beta


class GlobalMedFiLM(nn.Module):
    """One shared four-domain task-conditioned segmentation network.

    Parameters
    ----------
    task_count : int
        Number of tasks (4 for ISIC/BUSI/KVASIR/KUB). The task-ID registry is
        frozen by the data contract; this class only owns the embedding table.
    in_channels : int
        Inherited from the frozen Phase-20 protocol (RGB_3CH -> 3).
    out_channels : int
        Single foreground logit -> 1.
    """

    def __init__(
        self,
        task_count: int = 4,
        in_channels: int = 3,
        out_channels: int = 1,
        channels=GLOBAL_MEDFILM_CHANNELS,
        task_embedding_dim: int = GLOBAL_MEDFILM_TASK_EMBEDDING_DIM,
        film_hidden_dim: int = GLOBAL_MEDFILM_FILM_HIDDEN_DIM,
    ):
        super().__init__()
        task_count = int(task_count)
        if task_count < 2:
            raise ValueError("task_count must be at least 2.")
        channels = tuple(int(c) for c in channels)
        if len(channels) != 5:
            raise ValueError("channels must contain five stages.")
        c1, c2, c3, c4, cb = channels
        self.task_count = task_count
        self.in_channels = int(in_channels)
        self.out_channels = int(out_channels)
        self.channels = channels
        self.task_embedding_dim = int(task_embedding_dim)
        self.film_hidden_dim = int(film_hidden_dim)
        self.architecture_id = GLOBAL_MEDFILM_ARCHITECTURE_ID
        self.medfilm_components_present = True

        # ---- shared encoder ------------------------------------------------
        self.encoder1 = ResidualBlock(self.in_channels, c1)
        self.encoder2 = ResidualBlock(c1, c2)
        self.encoder3 = ResidualBlock(c2, c3)
        self.encoder4 = ResidualBlock(c3, c4)
        self.bridge = ResidualBlock(c4, cb)
        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)

        # ---- shared decoder ------------------------------------------------
        self.decoder4 = DecoderBlock(cb, c4, c4)
        self.decoder3 = DecoderBlock(c4, c3, c3)
        self.decoder2 = DecoderBlock(c3, c2, c2)
        self.decoder1 = DecoderBlock(c2, c1, c1)

        # ---- ONE shared output head (no dataset-specific head) -------------
        self.head = nn.Conv2d(c1, self.out_channels, kernel_size=1)

        # ---- task conditioning (the ONLY task signal) ----------------------
        self.task_embedding = nn.Embedding(task_count, self.task_embedding_dim)
        nn.init.normal_(self.task_embedding.weight, mean=0.0, std=0.02)
        self.film_location_channels = {
            "bridge": cb,
            "decoder4": c4,
            "decoder3": c3,
            "decoder2": c2,
            "decoder1": c1,
        }
        self.film_layers = nn.ModuleDict({
            name: FeatureWiseLinearModulation(
                embedding_dim=self.task_embedding_dim,
                hidden_dim=self.film_hidden_dim,
                channels=site_channels,
            )
            for name, site_channels in self.film_location_channels.items()
        })

        self.reset_parameters()

    # ------------------------------------------------------------------ #
    @property
    def film_locations(self):
        return tuple(self.film_location_channels)

    def reset_parameters(self) -> None:
        for module in self.modules():
            if isinstance(module, nn.Conv2d):
                nn.init.kaiming_normal_(module.weight, mode="fan_out", nonlinearity="relu")
                if module.bias is not None:
                    nn.init.zeros_(module.bias)
        # Low-gain shared head: keeps initial BCE near log(2).
        nn.init.normal_(self.head.weight, mean=0.0, std=0.01)
        if self.head.bias is not None:
            nn.init.zeros_(self.head.bias)
        # Re-assert FiLM identity-at-init after the blanket conv init.
        for layer in self.film_layers.values():
            nn.init.xavier_uniform_(layer.hidden[0].weight)
            nn.init.zeros_(layer.hidden[0].bias)
            nn.init.zeros_(layer.output.weight)
            nn.init.zeros_(layer.output.bias)

    def _validate_task_ids(self, task_ids: torch.Tensor, batch_size: int) -> None:
        if task_ids.ndim != 1 or task_ids.shape[0] != batch_size:
            raise ValueError("task_ids must have shape [B].")
        if task_ids.numel() == 0:
            raise ValueError("task_ids cannot be empty.")
        if int(task_ids.min()) < 0 or int(task_ids.max()) >= self.task_count:
            raise ValueError("An unknown task ID was supplied.")

    def film_parameters_for_tasks(self, task_ids: torch.Tensor):
        """Diagnostic accessor: gamma/beta per FiLM site for the given task IDs."""
        self._validate_task_ids(task_ids, task_ids.shape[0])
        embedding = self.task_embedding(task_ids)
        return {
            name: self.film_layers[name].parameters_from_embedding(embedding)
            for name in self.film_locations
        }

    # ------------------------------------------------------------------ #
    def forward(self, images: torch.Tensor, task_ids: torch.Tensor):
        if images.ndim != 4:
            raise ValueError("images must have shape [B, C, H, W].")
        if images.shape[1] != self.in_channels:
            raise ValueError(
                f"images must have {self.in_channels} channels, got {images.shape[1]}."
            )
        self._validate_task_ids(task_ids, images.shape[0])

        embedding = self.task_embedding(task_ids)

        skip1 = self.encoder1(images)
        skip2 = self.encoder2(self.pool(skip1))
        skip3 = self.encoder3(self.pool(skip2))
        skip4 = self.encoder4(self.pool(skip3))
        bridge = self.bridge(self.pool(skip4))

        bridge, _, _ = self.film_layers["bridge"](bridge, embedding)
        decoded = self.decoder4(bridge, skip4)
        decoded, _, _ = self.film_layers["decoder4"](decoded, embedding)
        decoded = self.decoder3(decoded, skip3)
        decoded, _, _ = self.film_layers["decoder3"](decoded, embedding)
        decoded = self.decoder2(decoded, skip2)
        decoded, _, _ = self.film_layers["decoder2"](decoded, embedding)
        decoded = self.decoder1(decoded, skip1)
        decoded, _, _ = self.film_layers["decoder1"](decoded, embedding)

        logits = self.head(decoded)
        if logits.shape[-2:] != images.shape[-2:]:
            logits = F.interpolate(logits, size=images.shape[-2:], mode="bilinear",
                                   align_corners=False)
        return logits
