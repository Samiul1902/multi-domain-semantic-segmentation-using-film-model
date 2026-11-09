"""Transformer / MiT-style U-Net for the Phase-20B conventional baseline benchmark.

PROVENANCE - READ THIS FIRST
----------------------------
This is a **LOCAL, RANDOMLY INITIALIZED** MiT-style hierarchical transformer
encoder with a U-Net decoder. It is **NOT** official pretrained MiT-B1 and it
loads **NO** pretrained weights of any kind.

    label: LOCAL_RANDOM_INIT__NOT_OFFICIAL_PRETRAINED_MIT_B1

Justification for including it in Phase 20B:

* ``timm`` / ``transformers`` / ``segmentation-models-pytorch`` are NOT installed
  in this environment, and the only cached pretrained weight is
  ``resnet34-b627a593.pth`` (unrelated to MiT). No official MiT checkpoint exists
  locally, so "official pretrained MiT-B1" cannot be claimed.
* The DeepLabV3+ baseline already in this benchmark is likewise randomly
  initialized (``torchvision resnet50(weights=None)``), so a randomly initialized
  transformer baseline is methodologically consistent with it.

Architecture (conventional MiT / SegFormer encoder design, no novel components)
------------------------------------------------------------------------------
Encoder - the four canonical MiT stages:

    stage 1 : overlap patch embed 7x7 / stride 4  -> H/4   dim  64  1 head  sr 8
    stage 2 : overlap patch embed 3x3 / stride 2  -> H/8   dim 128  2 heads sr 4
    stage 3 : overlap patch embed 3x3 / stride 2  -> H/16  dim 320  5 heads sr 2
    stage 4 : overlap patch embed 3x3 / stride 2  -> H/32  dim 512  8 heads sr 1

Each stage is ``depth=2`` identical transformer blocks containing:

    * **Efficient self-attention** - keys/values are spatially reduced by a
      stride-``sr_ratio`` convolution before the projection (the MiT memory trick).
    * **Mix-FFN** - a 3x3 depthwise convolution inside the MLP, which is how MiT
      injects positional information without positional encodings.
    * LayerNorm + residual connections, ``mlp_ratio = 4``.

Widths are expressed through the project-wide ``base_channels=32`` convention as
``[2b, 4b, 10b, 16b]``, which reproduces the canonical MiT-B1 widths
``[64, 128, 320, 512]`` at ``base_channels=32``.

Decoder - a plain U-Net decoder (no deep supervision, no ASPP, no SE, no FiLM):

    stage4 (H/32) -> up -> concat stage3 (H/16) -> DoubleConv
                  -> up -> concat stage2 (H/8)  -> DoubleConv
                  -> up -> concat stage1 (H/4)  -> DoubleConv
                  -> bilinear to input size -> 3x3 conv -> 1x1 head

Governance
----------
One shared parameter set across all four domains. No FiLM, no task embedding, no
domain embedding, no regional branch, no localizer, no ROI proposal, no routing,
no dataset-specific head. ``forward`` takes the image only - ``task_id`` is never
an input.
"""
from __future__ import annotations

import torch
from torch import nn
from torch.nn import functional as F

__all__ = ["TransformerMiTUNet", "OverlapPatchEmbed", "EfficientSelfAttention", "MixFFN"]

# Canonical MiT stage configuration. Widths scale with base_channels as
# [2b, 4b, 10b, 16b] -> canonical MiT-B1 [64, 128, 320, 512] at base_channels=32.
_WIDTH_MULT = (2, 4, 10, 16)
_HEADS = (1, 2, 5, 8)
_DEPTH = 2
_SR_RATIO = (8, 4, 2, 1)
_MLP_RATIO = 4
_PATCH_SIZES = (7, 3, 3, 3)
_PATCH_STRIDES = (4, 2, 2, 2)


class OverlapPatchEmbed(nn.Module):
    """Overlapping patch embedding: strided conv + LayerNorm (channels-first)."""

    def __init__(self, in_channels: int, embed_dim: int, patch_size: int, stride: int):
        super().__init__()
        self.proj = nn.Conv2d(in_channels, embed_dim, kernel_size=patch_size,
                              stride=stride, padding=patch_size // 2)
        self.norm = nn.LayerNorm(embed_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.proj(x)
        b, c, h, w = x.shape
        x = x.flatten(2).transpose(1, 2)          # B, N, C
        x = self.norm(x)
        return x.transpose(1, 2).reshape(b, c, h, w)


class EfficientSelfAttention(nn.Module):
    """MiT efficient self-attention with stride-``sr_ratio`` key/value reduction."""

    def __init__(self, dim: int, num_heads: int, sr_ratio: int):
        super().__init__()
        if dim % num_heads != 0:
            raise ValueError(f"dim={dim} must be divisible by num_heads={num_heads}")
        self.dim = dim
        self.num_heads = num_heads
        self.head_dim = dim // num_heads
        self.scale = self.head_dim ** -0.5
        self.sr_ratio = sr_ratio
        self.q = nn.Linear(dim, dim)
        if sr_ratio > 1:
            self.sr = nn.Conv2d(dim, dim, kernel_size=sr_ratio, stride=sr_ratio)
            self.norm = nn.LayerNorm(dim)
        self.kv = nn.Linear(dim, dim * 2)
        self.proj = nn.Linear(dim, dim)

    def forward(self, x: torch.Tensor, h: int, w: int) -> torch.Tensor:
        b, n, c = x.shape
        q = self.q(x).reshape(b, n, self.num_heads, self.head_dim).permute(0, 2, 1, 3)

        if self.sr_ratio > 1:
            x_ = x.transpose(1, 2).reshape(b, c, h, w)
            x_ = self.sr(x_).reshape(b, c, -1).transpose(1, 2)
            x_ = self.norm(x_)
        else:
            x_ = x
        kv = self.kv(x_).reshape(b, -1, 2, self.num_heads, self.head_dim).permute(2, 0, 3, 1, 4)
        k, v = kv[0], kv[1]

        attn = (q @ k.transpose(-2, -1)) * self.scale
        attn = attn.softmax(dim=-1)
        out = (attn @ v).transpose(1, 2).reshape(b, n, c)
        return self.proj(out)


class MixFFN(nn.Module):
    """MiT Mix-FFN: Linear -> 3x3 depthwise conv -> GELU -> Linear."""

    def __init__(self, in_features: int, hidden_features: int):
        super().__init__()
        self.fc1 = nn.Linear(in_features, hidden_features)
        self.dwconv = nn.Conv2d(hidden_features, hidden_features, 3, padding=1,
                                groups=hidden_features)
        self.act = nn.GELU()
        self.fc2 = nn.Linear(hidden_features, in_features)

    def forward(self, x: torch.Tensor, h: int, w: int) -> torch.Tensor:
        b, n, c = x.shape
        x = self.fc1(x)
        x = x.transpose(1, 2).reshape(b, -1, h, w)
        x = self.act(self.dwconv(x))
        x = x.flatten(2).transpose(1, 2)
        return self.fc2(x)


class TransformerBlock(nn.Module):
    """LayerNorm -> efficient attention -> residual; LayerNorm -> Mix-FFN -> residual."""

    def __init__(self, dim: int, num_heads: int, sr_ratio: int, mlp_ratio: int = _MLP_RATIO):
        super().__init__()
        self.norm1 = nn.LayerNorm(dim)
        self.attn = EfficientSelfAttention(dim, num_heads, sr_ratio)
        self.norm2 = nn.LayerNorm(dim)
        self.mlp = MixFFN(dim, int(dim * mlp_ratio))

    def forward(self, x: torch.Tensor, h: int, w: int) -> torch.Tensor:
        x = x + self.attn(self.norm1(x), h, w)
        x = x + self.mlp(self.norm2(x), h, w)
        return x


class MiTStage(nn.Module):
    """One MiT stage: overlap patch embed, then ``depth`` transformer blocks."""

    def __init__(self, in_channels: int, embed_dim: int, num_heads: int, sr_ratio: int,
                 depth: int, patch_size: int, stride: int):
        super().__init__()
        self.patch_embed = OverlapPatchEmbed(in_channels, embed_dim, patch_size, stride)
        self.blocks = nn.ModuleList(
            [TransformerBlock(embed_dim, num_heads, sr_ratio) for _ in range(depth)])
        self.norm = nn.LayerNorm(embed_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.patch_embed(x)
        _, _, h, w = x.shape
        b, c = x.shape[0], x.shape[1]
        tokens = x.flatten(2).transpose(1, 2)
        for block in self.blocks:
            tokens = block(tokens, h, w)
        tokens = self.norm(tokens)
        return tokens.transpose(1, 2).reshape(b, c, h, w)


class DoubleConv(nn.Sequential):
    """Two 3x3 convolutions with BatchNorm and ReLU (U-Net decoder building block)."""

    def __init__(self, in_channels: int, out_channels: int):
        super().__init__(
            nn.Conv2d(in_channels, out_channels, 3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels), nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, 3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels), nn.ReLU(inplace=True),
        )


class TransformerMiTUNet(nn.Module):
    """MiT-style transformer encoder + conventional U-Net decoder.

    ``base_channels=32`` reproduces the canonical MiT-B1 widths [64, 128, 320, 512].
    Randomly initialized - no pretrained weights are loaded.
    """

    def __init__(self, in_channels: int = 1, out_channels: int = 1, base_channels: int = 32):
        super().__init__()
        b = base_channels
        dims = [m * b for m in _WIDTH_MULT]

        # --- MiT encoder ----------------------------------------------------- #
        self.stage1 = MiTStage(in_channels, dims[0], _HEADS[0], _SR_RATIO[0], _DEPTH,
                               _PATCH_SIZES[0], _PATCH_STRIDES[0])
        self.stage2 = MiTStage(dims[0], dims[1], _HEADS[1], _SR_RATIO[1], _DEPTH,
                               _PATCH_SIZES[1], _PATCH_STRIDES[1])
        self.stage3 = MiTStage(dims[1], dims[2], _HEADS[2], _SR_RATIO[2], _DEPTH,
                               _PATCH_SIZES[2], _PATCH_STRIDES[2])
        self.stage4 = MiTStage(dims[2], dims[3], _HEADS[3], _SR_RATIO[3], _DEPTH,
                               _PATCH_SIZES[3], _PATCH_STRIDES[3])

        # --- U-Net decoder --------------------------------------------------- #
        dec = (256, 128, 64, b)
        self.up4 = nn.ConvTranspose2d(dims[3], dec[0], 2, 2)
        self.dec4 = DoubleConv(dec[0] + dims[2], dec[0])
        self.up3 = nn.ConvTranspose2d(dec[0], dec[1], 2, 2)
        self.dec3 = DoubleConv(dec[1] + dims[1], dec[1])
        self.up2 = nn.ConvTranspose2d(dec[1], dec[2], 2, 2)
        self.dec2 = DoubleConv(dec[2] + dims[0], dec[2])
        self.up1 = nn.ConvTranspose2d(dec[2], dec[3], 2, 2)
        self.dec1 = DoubleConv(dec[3], dec[3])
        self.refine = nn.Sequential(
            nn.Conv2d(dec[3], dec[3], 3, padding=1, bias=False),
            nn.BatchNorm2d(dec[3]), nn.ReLU(inplace=True),
        )
        self.head = nn.Conv2d(dec[3], out_channels, 1)
        self.apply(self._init_weights)

    @staticmethod
    def _init_weights(module: nn.Module) -> None:
        if isinstance(module, (nn.Conv2d, nn.ConvTranspose2d)):
            nn.init.kaiming_normal_(module.weight, nonlinearity="relu")
            if module.bias is not None:
                nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Linear):
            nn.init.trunc_normal_(module.weight, std=0.02)
            if module.bias is not None:
                nn.init.zeros_(module.bias)
        elif isinstance(module, (nn.LayerNorm, nn.BatchNorm2d)):
            if module.weight is not None:
                nn.init.ones_(module.weight)
            if module.bias is not None:
                nn.init.zeros_(module.bias)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        input_size = x.shape[-2:]

        e1 = self.stage1(x)          # H/4,  dims[0]
        e2 = self.stage2(e1)         # H/8,  dims[1]
        e3 = self.stage3(e2)         # H/16, dims[2]
        e4 = self.stage4(e3)         # H/32, dims[3]

        d4 = self.dec4(torch.cat([self.up4(e4), e3], dim=1))
        d3 = self.dec3(torch.cat([self.up3(d4), e2], dim=1))
        d2 = self.dec2(torch.cat([self.up2(d3), e1], dim=1))
        d1 = self.dec1(self.up1(d2))

        d1 = F.interpolate(d1, size=input_size, mode="bilinear", align_corners=False)
        return self.head(self.refine(d1))
