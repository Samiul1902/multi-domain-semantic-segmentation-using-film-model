"""Phase 28 -- trained controlled router ablation variants R1 / R2 / R3.

Frozen by ``docs/phase28_ablation_execution_spec_v1_2.md`` (v1.2) sections 6-9.

These are **SEPARATELY_TRAINED_CONTROLLED_ABLATION_VARIANT** models -- NOT
inference-time feature zeroing, NOT input occlusion, NOT post-hoc masking of the
canonical Phase25D ``B_phi``.

The architecture after the input stage is *identical* to the canonical Phase25D
``BARRBenefitRouterV1``::

    Linear(., 128) -> LayerNorm(128) -> SiLU -> Dropout(0.10)
                   -> Linear(128, 64) -> LayerNorm(64) -> SiLU -> Dropout(0.10)
                   -> Linear(64, 1)

Only the input dimensionality / presence of the task embedding changes.

* R1 -- no deep global features: 10 scalars + Embedding(4,16)  -> width 26
* R2 -- no task_id: all 202 numeric features, NO embedding      -> width 202
* R3 -- scalar-only FEATURE-SET CONTROL: 10 scalars, no emb.    -> width 10

R3 must NOT be described as a single-input-variable causal isolation.
"""
from __future__ import annotations

import torch
import torch.nn.functional as F
from torch import nn

from .regional_refiner import (
    BARR_REFINER_CHANNELS,
    ResidualBlock,
    group_count as _group_count,
)

__all__ = [
    "BARRBenefitRouterR1NoDeep",
    "BARRBenefitRouterR2NoTask",
    "BARRBenefitRouterR3ScalarOnly",
    "BARRRegionalRefinerF1NoPGlobal",
    "ROUTER_VARIANT_EXPECTED_PARAMETERS",
    "REFINER_F1_EXPECTED_PARAMETERS",
    "build_router_variant",
    "build_refiner_f1",
    "count_params",
]

#: Frozen expected trainable parameter counts (spec v1.2 §7-§9, work order §7-§9).
ROUTER_VARIANT_EXPECTED_PARAMETERS = {
    # R1: Embedding(4,16)=64 ; Linear(26,128)=26*128+128=3456 ; LN(128)=256
    #     Linear(128,64)=128*64+64=8256 ; LN(64)=128 ; Linear(64,1)=65
    #     64 + 3456 + 256 + 8256 + 128 + 65 = 12225
    "R1": 12_225,
    # R2: Linear(202,128)=202*128+128=25984 ; LN(128)=256
    #     Linear(128,64)=8256 ; LN(64)=128 ; Linear(64,1)=65
    #     25984 + 256 + 8256 + 128 + 65 = 34689
    "R2": 34_689,
    # R3: Linear(10,128)=10*128+128=1408 ; LN(128)=256
    #     Linear(128,64)=8256 ; LN(64)=128 ; Linear(64,1)=65
    #     1408 + 256 + 8256 + 128 + 65 = 10113
    "R3": 10_113,
}


def _hidden_topology(in_width: int) -> nn.Sequential:
    """Identical hidden topology to the canonical Phase25D router (spec v1.2 §6-§9)."""
    return nn.Sequential(
        nn.Linear(in_width, 128),
        nn.LayerNorm(128, elementwise_affine=True),
        nn.SiLU(),
        nn.Dropout(0.10),
        nn.Linear(128, 64),
        nn.LayerNorm(64, elementwise_affine=True),
        nn.SiLU(),
        nn.Dropout(0.10),
        nn.Linear(64, 1),
    )


class BARRBenefitRouterR1NoDeep(nn.Module):
    """R1 -- router without deep global features (spec v1.2 §6).

    Input : 10 frozen scalar features + ``Embedding(4, 16)`` task conditioning.
    Width : 10 + 16 = 26.
    """

    VARIANT = "R1"
    SCALAR_SLICE = slice(0, 10)      # R1 receives the 10 scalars re-indexed to 0..9
    USES_TASK_EMBEDDING = True
    INPUT_WIDTH = 26

    def __init__(self) -> None:
        super().__init__()
        self.task_embedding = nn.Embedding(4, 16)
        self.net = _hidden_topology(self.INPUT_WIDTH)

    def forward(self, x_numeric: torch.Tensor, task_ids: torch.Tensor) -> torch.Tensor:
        emb = self.task_embedding(task_ids)
        x = torch.cat([x_numeric, emb], dim=-1)
        return self.net(x).squeeze(-1)


class BARRBenefitRouterR2NoTask(nn.Module):
    """R2 -- router without task_id (spec v1.2 §8).

    Input : all 202 canonical numeric features.
    Width : 202. The embedding module does NOT exist (no zero vector).
    """

    VARIANT = "R2"
    USES_TASK_EMBEDDING = False
    INPUT_WIDTH = 202

    def __init__(self) -> None:
        super().__init__()
        self.net = _hidden_topology(self.INPUT_WIDTH)

    def forward(self, x_numeric: torch.Tensor, task_ids: torch.Tensor | None = None) -> torch.Tensor:
        return self.net(x_numeric).squeeze(-1)


class BARRBenefitRouterR3ScalarOnly(nn.Module):
    """R3 -- scalar-only FEATURE-SET CONTROL (spec v1.2 §9).

    Input : ONLY the 10 frozen scalar features (re-indexed to 0..9).
    Width : 10. No embedding, no task_id, no deep features.

    NOT a single-input-variable causal isolation.
    """

    VARIANT = "R3"
    SCALAR_SLICE = slice(0, 10)
    USES_TASK_EMBEDDING = False
    INPUT_WIDTH = 10

    def __init__(self) -> None:
        super().__init__()
        self.net = _hidden_topology(self.INPUT_WIDTH)

    def forward(self, x_numeric: torch.Tensor, task_ids: torch.Tensor | None = None) -> torch.Tensor:
        return self.net(x_numeric).squeeze(-1)


_VARIANT_CLASSES = {
    "R1": BARRBenefitRouterR1NoDeep,
    "R2": BARRBenefitRouterR2NoTask,
    "R3": BARRBenefitRouterR3ScalarOnly,
}


def build_router_variant(variant: str) -> nn.Module:
    """Instantiate a Phase-28 router variant and assert its frozen parameter count."""
    key = str(variant).upper()
    if key not in _VARIANT_CLASSES:
        raise ValueError(f"unknown router variant {variant!r}; expected one of {sorted(_VARIANT_CLASSES)}")
    model = _VARIANT_CLASSES[key]()
    n = count_params(model)
    expected = ROUTER_VARIANT_EXPECTED_PARAMETERS[key]
    if n != expected:
        raise AssertionError(f"{key} parameter count {n} != frozen {expected}")
    return model


def count_params(model: nn.Module) -> int:
    return int(sum(p.numel() for p in model.parameters() if p.requires_grad))


# =====================================================================
# Phase 28 -- F1 refiner variant (spec v1.2 §18-§20)
# =====================================================================
#: F1 expected trainable parameter count = canonical 1,276,401 - 144
#: (stem Conv3x3(4->16)=576 -> Conv3x3(3->16)=432, a reduction of 144).
REFINER_F1_EXPECTED_PARAMETERS = 1_276_257


class BARRRegionalRefinerF1NoPGlobal(nn.Module):
    """F1 -- trained regional refiner WITHOUT the ``p_global`` input channel.

    Spec v1.2 §18: the ``p_global`` channel is physically ABSENT from the model
    input. Do NOT feed zeros as a fourth channel, mask the fourth channel, or
    reuse the 4-channel weights.

    Only the first input stage changes (``Conv3x3(4->16)`` -> ``Conv3x3(3->16)``);
    every other architecture and training choice is frozen identical to
    ``BARRRegionalRefinerV1``.

    Input : ``[R, G, B]`` -> ``(3, 256, 256)``.
    Output: raw LOGITS ``(1, 256, 256)`` (no internal sigmoid).
    """

    VARIANT = "F1"
    in_channels = 3
    out_channels = 1
    channels = BARR_REFINER_CHANNELS
    architecture_id = "barr_regional_refiner_f1_no_pglobal"

    def __init__(self, channels=BARR_REFINER_CHANNELS) -> None:
        super().__init__()
        channels = tuple(int(c) for c in channels)
        if len(channels) != 5:
            raise ValueError("channels must contain five stages")
        self.channels = channels
        c1, c2, c3, c4, cb = channels

        self.stem = nn.Sequential(
            nn.Conv2d(3, c1, kernel_size=3, padding=1, bias=False),
            nn.GroupNorm(_group_count(c1), c1),
            nn.SiLU(inplace=True),
        )
        self.encoder1 = ResidualBlock(c1, c1)
        self.encoder2 = ResidualBlock(c1, c2)
        self.encoder3 = ResidualBlock(c2, c3)
        self.encoder4 = ResidualBlock(c3, c4)
        self.encoder5 = ResidualBlock(c4, cb)
        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)

        self.bridge = ResidualBlock(cb, cb)

        self.decoder4 = ResidualBlock(cb + c4, c4)
        self.decoder3 = ResidualBlock(c4 + c3, c3)
        self.decoder2 = ResidualBlock(c3 + c2, c2)
        self.decoder1 = ResidualBlock(c2 + c1, c1)

        self.head = nn.Conv2d(c1, 1, kernel_size=1, bias=True)

        self.reset_parameters()

    @staticmethod
    def _up(x: torch.Tensor, size) -> torch.Tensor:
        return F.interpolate(x, size=size, mode="bilinear", align_corners=False)

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        if inputs.ndim != 4:
            raise ValueError("inputs must have shape [B, C, H, W]")
        if inputs.shape[1] != 3:
            raise ValueError(f"F1 inputs must have 3 channels (RGB only), got {inputs.shape[1]}")

        s1 = self.encoder1(self.stem(inputs))
        s2 = self.encoder2(self.pool(s1))
        s3 = self.encoder3(self.pool(s2))
        s4 = self.encoder4(self.pool(s3))
        s5 = self.encoder5(self.pool(s4))
        b = self.bridge(self.pool(s5))

        d = self.decoder4(torch.cat([self._up(b, s4.shape[-2:]), s4], dim=1))
        d = self.decoder3(torch.cat([self._up(d, s3.shape[-2:]), s3], dim=1))
        d = self.decoder2(torch.cat([self._up(d, s2.shape[-2:]), s2], dim=1))
        d = self.decoder1(torch.cat([self._up(d, s1.shape[-2:]), s1], dim=1))

        logits = self.head(d)
        if logits.shape[-2:] != inputs.shape[-2:]:
            logits = F.interpolate(logits, size=inputs.shape[-2:], mode="bilinear",
                                   align_corners=False)
        return logits

    def reset_parameters(self) -> None:
        for module in self.modules():
            if isinstance(module, nn.Conv2d):
                nn.init.kaiming_normal_(module.weight, mode="fan_out", nonlinearity="relu")
                if module.bias is not None:
                    nn.init.zeros_(module.bias)
        nn.init.normal_(self.head.weight, mean=0.0, std=0.01)
        nn.init.zeros_(self.head.bias)


def build_refiner_f1(channels=BARR_REFINER_CHANNELS) -> nn.Module:
    """Instantiate the F1 refiner and assert its frozen parameter count."""
    model = BARRRegionalRefinerF1NoPGlobal(channels=channels)
    n = count_params(model)
    if n != REFINER_F1_EXPECTED_PARAMETERS:
        raise AssertionError(f"F1 parameter count {n} != frozen {REFINER_F1_EXPECTED_PARAMETERS}")
    return model
