"""Compact U-Net heatmap localizer for FULL_FIELD KUB images."""
import math
import torch
from torch import nn
from .unet import DoubleConv


class KUBLocalizer(nn.Module):
    """Three-stage compact U-Net producing one objectness-logit channel."""
    def __init__(self, in_channels=1, out_channels=1, base_channels=16, heatmap_resolution=512):
        super().__init__()
        b = base_channels
        self.pool = nn.MaxPool2d(2)
        self.heatmap_resolution = heatmap_resolution
        self.e1 = DoubleConv(in_channels, b)
        self.e2 = DoubleConv(b, 2 * b)
        self.e3 = DoubleConv(2 * b, 4 * b)
        self.bridge = DoubleConv(4 * b, 8 * b)
        self.u3 = nn.ConvTranspose2d(8 * b, 4 * b, 2, 2)
        self.d3 = DoubleConv(8 * b, 4 * b)
        self.u2 = nn.ConvTranspose2d(4 * b, 2 * b, 2, 2)
        self.d2 = DoubleConv(4 * b, 2 * b)
        self.u1 = nn.ConvTranspose2d(2 * b, b, 2, 2)
        self.d1 = DoubleConv(2 * b, b)
        self.head = nn.Conv2d(b, out_channels, 1)

        if heatmap_resolution < 512:
            stride = 512 // heatmap_resolution
            self.logit_downsample = nn.AvgPool2d(kernel_size=stride, stride=stride)
        else:
            self.logit_downsample = nn.Identity()

        self.apply(self._init)

        # phase13b_centernet_head_init_p01_v1
        nn.init.constant_(self.head.weight, 0.0)
        nn.init.constant_(self.head.bias, math.log(0.1 / 0.9))

    @staticmethod
    def _init(module):
        if isinstance(module, (nn.Conv2d, nn.ConvTranspose2d)):
            nn.init.kaiming_normal_(module.weight, nonlinearity='relu')
            if module.bias is not None:
                nn.init.zeros_(module.bias)

    def forward(self, x):
        e1 = self.e1(x)
        e2 = self.e2(self.pool(e1))
        e3 = self.e3(self.pool(e2))
        z = self.bridge(self.pool(e3))
        d3 = self.d3(torch.cat([self.u3(z), e3], 1))
        d2 = self.d2(torch.cat([self.u2(d3), e2], 1))
        d1 = self.d1(torch.cat([self.u1(d2), e1], 1))
        logits = self.head(d1)
        return self.logit_downsample(logits)
