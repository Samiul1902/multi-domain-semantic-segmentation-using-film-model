"""Standard non-deep-supervision UNet++ (Nested U-Net)."""
import torch
from torch import nn

from .unet import DoubleConv


class UNetPlusPlus(nn.Module):
    """Four-level nested dense skip UNet++ with one final segmentation head."""
    def __init__(self, in_channels=1, out_channels=1, base_channels=32):
        super().__init__()
        b = base_channels
        channels = [b, b * 2, b * 4, b * 8, b * 16]
        self.pool = nn.MaxPool2d(2)
        self.up = nn.Upsample(scale_factor=2, mode="bilinear", align_corners=True)
        self.x00 = DoubleConv(in_channels, channels[0])
        self.x10 = DoubleConv(channels[0], channels[1])
        self.x20 = DoubleConv(channels[1], channels[2])
        self.x30 = DoubleConv(channels[2], channels[3])
        self.x40 = DoubleConv(channels[3], channels[4])
        self.x01 = DoubleConv(channels[0] + channels[1], channels[0])
        self.x11 = DoubleConv(channels[1] + channels[2], channels[1])
        self.x21 = DoubleConv(channels[2] + channels[3], channels[2])
        self.x31 = DoubleConv(channels[3] + channels[4], channels[3])
        self.x02 = DoubleConv(channels[0] * 2 + channels[1], channels[0])
        self.x12 = DoubleConv(channels[1] * 2 + channels[2], channels[1])
        self.x22 = DoubleConv(channels[2] * 2 + channels[3], channels[2])
        self.x03 = DoubleConv(channels[0] * 3 + channels[1], channels[0])
        self.x13 = DoubleConv(channels[1] * 3 + channels[2], channels[1])
        self.x04 = DoubleConv(channels[0] * 4 + channels[1], channels[0])
        self.head = nn.Conv2d(channels[0], out_channels, 1)
        self.apply(self._init)

    @staticmethod
    def _init(module):
        if isinstance(module, nn.Conv2d):
            nn.init.kaiming_normal_(module.weight, nonlinearity="relu")
            if module.bias is not None:
                nn.init.zeros_(module.bias)

    def forward(self, x):
        x00 = self.x00(x); x10 = self.x10(self.pool(x00)); x20 = self.x20(self.pool(x10))
        x30 = self.x30(self.pool(x20)); x40 = self.x40(self.pool(x30))
        x01 = self.x01(torch.cat([x00, self.up(x10)], 1))
        x11 = self.x11(torch.cat([x10, self.up(x20)], 1))
        x21 = self.x21(torch.cat([x20, self.up(x30)], 1))
        x31 = self.x31(torch.cat([x30, self.up(x40)], 1))
        x02 = self.x02(torch.cat([x00, x01, self.up(x11)], 1))
        x12 = self.x12(torch.cat([x10, x11, self.up(x21)], 1))
        x22 = self.x22(torch.cat([x20, x21, self.up(x31)], 1))
        x03 = self.x03(torch.cat([x00, x01, x02, self.up(x12)], 1))
        x13 = self.x13(torch.cat([x10, x11, x12, self.up(x22)], 1))
        x04 = self.x04(torch.cat([x00, x01, x02, x03, self.up(x13)], 1))
        return self.head(x04)
