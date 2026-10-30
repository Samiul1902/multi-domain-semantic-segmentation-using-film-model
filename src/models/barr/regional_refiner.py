"""Phase 25A — BARRRegionalRefinerV1 (symbol ``R_psi``).

The DEDICATED crop-trained regional segmentation action of RA-MedFiLM-BARR v1.1.

This module is explicitly NON-NOVEL. Its only scientific role is to provide the
later benefit router (Phase 25C) with a legitimate, prospectively specified
optional refinement action.

Frozen provenance
-----------------
The architecture is frozen by the Phase-24 v1.1 exact implementation spec
(``reports/audits/phase24_exact_implementation_spec.json``):

* input  : ``B x 4 x 256 x 256`` = ``[R, G, B, p_global_crop]``
* output : ``B x 1 x 256 x 256`` raw LOGITS (no internal sigmoid)
* channels (effective, pre-declared deterministic reduction):
  ``[16, 32, 64, 96, 128]``
* expected trainable parameters: **1,276,401** (closed form, no module instantiated)
* hard ceiling: 2,000,000

Prose/closed-form reconciliation
--------------------------------
The Phase-24 frozen *number* is derived from a specific closed-form block
enumeration. The Phase-25A instruction prose sketches the same network slightly
more loosely ("Stage 1: ResidualBlock(4 -> 16)"). This module implements the
structure the frozen count encodes, so the realised parameter count is exactly
1,276,401. The mapping is:

    prose "Stage 1: ResidualBlock(4 -> 16)"
        -> stem Conv3x3(4 -> 16) + GroupNorm(16)   (realises the 4->16 transition)
        -> ResidualBlock(16 -> 16)                 (the stage-1 residual block)
    prose "Stage 2: ResidualBlock(16 -> 32)"       -> ResidualBlock(16 -> 32)
    prose "Stage 3: ResidualBlock(32 -> 64)"       -> ResidualBlock(32 -> 64)
    prose "Stage 4: ResidualBlock(64 -> 96)"       -> ResidualBlock(64 -> 96)
    prose "Bridge:  ResidualBlock(96 -> 128)"      -> encoder ResidualBlock(96 -> 128)
                                                   + bridge ResidualBlock(128 -> 128)

The reconciliation is recorded (not silent) in
``reports/audits/phase25a_refiner_architecture_binding.json``.

Forbidden (frozen): SE blocks, attention, transformer, pretrained encoder,
foundation model, deep supervision, task FiLM, dropout, learned fusion.
"""
from __future__ import annotations

import torch
from torch import nn
import torch.nn.functional as F

__all__ = [
    "BARRRegionalRefinerV1",
    "ResidualBlock",
    "BARR_REFINER_ARCHITECTURE_ID",
    "BARR_REFINER_CHANNELS",
    "BARR_REFINER_INPUT_CHANNELS",
    "BARR_REFINER_OUTPUT_CHANNELS",
    "BARR_REFINER_INPUT_RESOLUTION",
    "BARR_REFINER_EXPECTED_PARAMETERS",
    "BARR_REFINER_HARD_CEILING",
    "group_count",
    "closed_form_parameter_count",
    "count_parameters",
    "assert_no_forbidden_modules",
]

BARR_REFINER_ARCHITECTURE_ID = "barr_regional_refiner_v1_narrowed_channels"
BARR_REFINER_CHANNELS = (16, 32, 64, 96, 128)
BARR_REFINER_INPUT_CHANNELS = 4
BARR_REFINER_OUTPUT_CHANNELS = 1
BARR_REFINER_INPUT_RESOLUTION = 256
BARR_REFINER_EXPECTED_PARAMETERS = 1_276_401
BARR_REFINER_HARD_CEILING = 2_000_000

#: Substrings that must NEVER appear in a module name of the primary refiner.
FORBIDDEN_MODULE_TOKENS = (
    "se_", "squeeze", "excitation", "attention", "transformer", "attn",
    "film", "task_embed", "dropout", "pretrained", "foundation", "sam",
    "deep_supervision", "aux_head", "router", "benefit", "gate",
)


def group_count(channels: int) -> int:
    """Largest divisor of ``channels`` that is <= 8 (deterministic).

    For every channel width used here (16, 32, 64, 96, 128) this returns 8.
    """
    for groups in range(8, 0, -1):
        if channels % groups == 0:
            return groups
    return 1


class ResidualBlock(nn.Module):
    """Conv3x3 -> GN -> SiLU -> Conv3x3 -> GN -> (+skip) -> SiLU.

    ``skip`` is a 1x1 convolution (bias=False) when ``in_channels != out_channels``,
    otherwise an identity. Every convolution followed by GroupNorm has bias=False.
    """

    def __init__(self, in_channels: int, out_channels: int):
        super().__init__()
        self.in_channels = int(in_channels)
        self.out_channels = int(out_channels)
        self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, bias=False)
        self.norm1 = nn.GroupNorm(group_count(out_channels), out_channels)
        self.conv2 = nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=False)
        self.norm2 = nn.GroupNorm(group_count(out_channels), out_channels)
        self.skip = (
            nn.Identity() if in_channels == out_channels
            else nn.Conv2d(in_channels, out_channels, kernel_size=1, bias=False)
        )
        self.activation = nn.SiLU(inplace=True)

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        residual = self.skip(inputs)
        out = self.activation(self.norm1(self.conv1(inputs)))
        out = self.norm2(self.conv2(out))
        return self.activation(out + residual)


class BARRRegionalRefinerV1(nn.Module):
    """Dedicated crop-trained regional refiner ``R_psi`` (frozen, non-novel).

    Parameters
    ----------
    in_channels : int
        Must be 4 (``[R, G, B, p_global_crop]``).
    out_channels : int
        Must be 1 (single foreground logit channel).
    channels : sequence of int
        Effective encoder/bridge channel schedule; frozen to
        ``(16, 32, 64, 96, 128)``.
    """

    def __init__(self, in_channels: int = BARR_REFINER_INPUT_CHANNELS,
                 out_channels: int = BARR_REFINER_OUTPUT_CHANNELS,
                 channels=BARR_REFINER_CHANNELS):
        super().__init__()
        in_channels = int(in_channels)
        out_channels = int(out_channels)
        channels = tuple(int(c) for c in channels)
        if in_channels != BARR_REFINER_INPUT_CHANNELS:
            raise ValueError(f"R_psi input channels are frozen at {BARR_REFINER_INPUT_CHANNELS}, "
                             f"got {in_channels}")
        if out_channels != BARR_REFINER_OUTPUT_CHANNELS:
            raise ValueError(f"R_psi output channels are frozen at {BARR_REFINER_OUTPUT_CHANNELS}, "
                             f"got {out_channels}")
        if len(channels) != 5:
            raise ValueError("channels must contain five stages")

        self.in_channels = in_channels
        self.out_channels = out_channels
        self.channels = channels
        self.architecture_id = BARR_REFINER_ARCHITECTURE_ID

        c1, c2, c3, c4, cb = channels

        # ---- encoder: stem + residual blocks -------------------------------- #
        # stem realises the 4 -> c1 transition (prose "Stage 1: ResidualBlock(4 -> 16)")
        self.stem = nn.Sequential(
            nn.Conv2d(in_channels, c1, kernel_size=3, padding=1, bias=False),
            nn.GroupNorm(group_count(c1), c1),
            nn.SiLU(inplace=True),
        )
        self.encoder1 = ResidualBlock(c1, c1)
        self.encoder2 = ResidualBlock(c1, c2)
        self.encoder3 = ResidualBlock(c2, c3)
        self.encoder4 = ResidualBlock(c3, c4)
        self.encoder5 = ResidualBlock(c4, cb)
        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)

        # ---- bridge ---------------------------------------------------------- #
        self.bridge = ResidualBlock(cb, cb)

        # ---- decoder: bilinear up x2, concat skip, residual block ------------ #
        self.decoder4 = ResidualBlock(cb + c4, c4)   # 128 + 96 -> 96
        self.decoder3 = ResidualBlock(c4 + c3, c3)   # 96 + 64 -> 64
        self.decoder2 = ResidualBlock(c3 + c2, c2)   # 64 + 32 -> 32
        self.decoder1 = ResidualBlock(c2 + c1, c1)   # 32 + 16 -> 16

        # ---- single 1x1 logit head (bias=True: NOT followed by GroupNorm) ---- #
        self.head = nn.Conv2d(c1, out_channels, kernel_size=1, bias=True)

        self.reset_parameters()

    # ------------------------------------------------------------------ #
    @staticmethod
    def _up(x: torch.Tensor, size) -> torch.Tensor:
        return F.interpolate(x, size=size, mode="bilinear", align_corners=False)

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        if inputs.ndim != 4:
            raise ValueError("inputs must have shape [B, C, H, W]")
        if inputs.shape[1] != self.in_channels:
            raise ValueError(f"inputs must have {self.in_channels} channels, "
                             f"got {inputs.shape[1]}")

        s1 = self.encoder1(self.stem(inputs))       # H
        s2 = self.encoder2(self.pool(s1))           # H/2
        s3 = self.encoder3(self.pool(s2))           # H/4
        s4 = self.encoder4(self.pool(s3))           # H/8
        s5 = self.encoder5(self.pool(s4))           # H/16
        b = self.bridge(self.pool(s5))              # H/32

        d = self.decoder4(torch.cat([self._up(b, s4.shape[-2:]), s4], dim=1))
        d = self.decoder3(torch.cat([self._up(d, s3.shape[-2:]), s3], dim=1))
        d = self.decoder2(torch.cat([self._up(d, s2.shape[-2:]), s2], dim=1))
        d = self.decoder1(torch.cat([self._up(d, s1.shape[-2:]), s1], dim=1))

        logits = self.head(d)
        if logits.shape[-2:] != inputs.shape[-2:]:
            logits = F.interpolate(logits, size=inputs.shape[-2:], mode="bilinear",
                                   align_corners=False)
        return logits

    # ------------------------------------------------------------------ #
    def reset_parameters(self) -> None:
        """Deterministic, seed-independent-in-form initialisation."""
        for module in self.modules():
            if isinstance(module, nn.Conv2d):
                nn.init.kaiming_normal_(module.weight, mode="fan_out", nonlinearity="relu")
                if module.bias is not None:
                    nn.init.zeros_(module.bias)
        # Low-gain head keeps the initial BCE near log(2).
        nn.init.normal_(self.head.weight, mean=0.0, std=0.01)
        nn.init.zeros_(self.head.bias)


def count_parameters(model: nn.Module) -> int:
    return int(sum(p.numel() for p in model.parameters() if p.requires_grad))


def closed_form_parameter_count(channels=BARR_REFINER_CHANNELS) -> int:
    """Closed-form parameter arithmetic, mirroring the frozen Phase-24 derivation."""
    def gn(c: int) -> int:
        return 2 * c

    def conv(k: int, cin: int, cout: int, bias: bool = False) -> int:
        return k * k * cin * cout + (cout if bias else 0)

    def resblock(cin: int, cout: int) -> int:
        p = conv(3, cin, cout) + gn(cout) + conv(3, cout, cout) + gn(cout)
        if cin != cout:
            p += conv(1, cin, cout)
        return p

    ch = tuple(int(c) for c in channels)
    total = conv(3, BARR_REFINER_INPUT_CHANNELS, ch[0]) + gn(ch[0])   # stem
    total += resblock(ch[0], ch[0])                                   # stage-0 residual block
    for i in range(1, len(ch)):
        total += resblock(ch[i - 1], ch[i])
    total += resblock(ch[-1], ch[-1])                                 # bridge
    cur = ch[-1]
    for s in ch[-2::-1]:
        total += resblock(cur + s, s)
        cur = s
    total += conv(1, ch[0], BARR_REFINER_OUTPUT_CHANNELS, bias=True)  # head
    return int(total)


def assert_no_forbidden_modules(model: nn.Module) -> None:
    """Raise if any forbidden module type/name is present."""
    for name, module in model.named_modules():
        low = name.lower()
        for token in FORBIDDEN_MODULE_TOKENS:
            if token in low:
                raise AssertionError(f"forbidden module token {token!r} found in {name!r}")
        if isinstance(module, (nn.Dropout, nn.Dropout2d, nn.MultiheadAttention,
                               nn.TransformerEncoder, nn.LayerNorm)):
            raise AssertionError(f"forbidden module type {type(module).__name__} at {name!r}")
