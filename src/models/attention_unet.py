"""Standard four-stage Attention U-Net with additive skip attention gates."""
import torch
from torch import nn

from .unet import DoubleConv


class AttentionGate(nn.Module):
    """Additive attention gate for a skip tensor conditioned on decoder context."""
    def __init__(self, skip_channels, gate_channels, intermediate_channels):
        super().__init__()
        self.skip_projection = nn.Sequential(
            nn.Conv2d(skip_channels, intermediate_channels, 1, bias=False),
            nn.BatchNorm2d(intermediate_channels),
        )
        self.gate_projection = nn.Sequential(
            nn.Conv2d(gate_channels, intermediate_channels, 1, bias=False),
            nn.BatchNorm2d(intermediate_channels),
        )
        self.score = nn.Sequential(
            nn.ReLU(inplace=True),
            nn.Conv2d(intermediate_channels, 1, 1),
            nn.Sigmoid(),
        )

    def forward(self, skip, gate):
        return skip * self.score(self.skip_projection(skip) + self.gate_projection(gate))


class AttentionUNet(nn.Module):
    """Attention U-Net with gates on all four encoder skip connections."""
    def __init__(self, in_channels=1, out_channels=1, base_channels=32):
        super().__init__()
        b = base_channels
        self.enc1, self.enc2 = DoubleConv(in_channels, b), DoubleConv(b, b * 2)
        self.enc3, self.enc4 = DoubleConv(b * 2, b * 4), DoubleConv(b * 4, b * 8)
        self.pool = nn.MaxPool2d(2)
        self.bottleneck = DoubleConv(b * 8, b * 16)
        self.up4 = nn.ConvTranspose2d(b * 16, b * 8, 2, 2)
        self.up3 = nn.ConvTranspose2d(b * 8, b * 4, 2, 2)
        self.up2 = nn.ConvTranspose2d(b * 4, b * 2, 2, 2)
        self.up1 = nn.ConvTranspose2d(b * 2, b, 2, 2)
        self.att4 = AttentionGate(b * 8, b * 8, b * 4)
        self.att3 = AttentionGate(b * 4, b * 4, b * 2)
        self.att2 = AttentionGate(b * 2, b * 2, b)
        self.att1 = AttentionGate(b, b, max(1, b // 2))
        self.dec4, self.dec3 = DoubleConv(b * 16, b * 8), DoubleConv(b * 8, b * 4)
        self.dec2, self.dec1 = DoubleConv(b * 4, b * 2), DoubleConv(b * 2, b)
        self.head = nn.Conv2d(b, out_channels, 1)
        self.apply(self._init)

    @staticmethod
    def _init(module):
        if isinstance(module, (nn.Conv2d, nn.ConvTranspose2d)):
            nn.init.kaiming_normal_(module.weight, nonlinearity="relu")
            if module.bias is not None:
                nn.init.zeros_(module.bias)

    def forward(self, x):
        e1 = self.enc1(x); e2 = self.enc2(self.pool(e1))
        e3 = self.enc3(self.pool(e2)); e4 = self.enc4(self.pool(e3))
        z = self.bottleneck(self.pool(e4))
        g4 = self.up4(z); d4 = self.dec4(torch.cat([g4, self.att4(e4, g4)], dim=1))
        g3 = self.up3(d4); d3 = self.dec3(torch.cat([g3, self.att3(e3, g3)], dim=1))
        g2 = self.up2(d3); d2 = self.dec2(torch.cat([g2, self.att2(e2, g2)], dim=1))
        g1 = self.up1(d2); d1 = self.dec1(torch.cat([g1, self.att1(e1, g1)], dim=1))
        return self.head(d1)
