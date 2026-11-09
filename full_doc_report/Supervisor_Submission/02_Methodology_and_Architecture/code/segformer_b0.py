"""Canonical SegFormer-B0 binary segmentation model (EXT-03R).

Config-only instantiation (NO pretrained weights, NO from_pretrained download),
num_labels=1, raw logits, output deterministically resized to [B, 1, 512, 512].
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


SEGFORMER_B0_CONFIG = dict(
    hidden_sizes=[32, 64, 160, 256],
    depths=[2, 2, 2, 2],
    num_attention_heads=[1, 2, 5, 8],
    sr_ratios=[8, 4, 2, 1],
    decoder_hidden_size=256,
    num_labels=1,
    image_size=512,
)
FROZEN_INPUT_SIZE = 512
FROZEN_INTERPOLATION = "bilinear"


class SegFormerB0Binary(nn.Module):
    """SegFormer-B0 + binary head, raw logits, output resized to [B,1,512,512]."""

    def __init__(self, in_channels=3, out_size=FROZEN_INPUT_SIZE):
        super().__init__()
        from transformers import SegformerConfig, SegformerForSemanticSegmentation
        cfg = SegformerConfig(
            num_channels=in_channels,
            hidden_sizes=list(SEGFORMER_B0_CONFIG["hidden_sizes"]),
            depths=list(SEGFORMER_B0_CONFIG["depths"]),
            num_attention_heads=list(SEGFORMER_B0_CONFIG["num_attention_heads"]),
            sr_ratios=list(SEGFORMER_B0_CONFIG["sr_ratios"]),
            decoder_hidden_size=SEGFORMER_B0_CONFIG["decoder_hidden_size"],
            num_labels=SEGFORMER_B0_CONFIG["num_labels"],
        )
        # config-only: no pretrained weights downloaded
        self.backbone = SegformerForSemanticSegmentation(cfg)
        self.out_size = int(out_size)

    def forward(self, x):
        out = self.backbone(pixel_values=x)
        logits = out.logits  # [B, 1, h/4, w/4]
        if logits.shape[-2:] != (self.out_size, self.out_size):
            logits = F.interpolate(logits, size=(self.out_size, self.out_size),
                                   mode=FROZEN_INTERPOLATION, align_corners=False)
        return logits  # raw logits, [B, 1, 512, 512]
