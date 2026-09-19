"""Standard four-stage U-Net baseline."""
import torch
from torch import nn


class DoubleConv(nn.Sequential):
    def __init__(self, in_channels, out_channels):
        super().__init__(
            nn.Conv2d(in_channels, out_channels, 3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels), nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, 3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels), nn.ReLU(inplace=True),
        )


class UNet(nn.Module):
    def __init__(self, in_channels=1, out_channels=1, base_channels=32):
        super().__init__()
        b = base_channels
        self.enc1, self.enc2 = DoubleConv(in_channels,b), DoubleConv(b,b*2)
        self.enc3, self.enc4 = DoubleConv(b*2,b*4), DoubleConv(b*4,b*8)
        self.pool = nn.MaxPool2d(2)
        self.bottleneck = DoubleConv(b*8,b*16)
        self.up4, self.dec4 = nn.ConvTranspose2d(b*16,b*8,2,2), DoubleConv(b*16,b*8)
        self.up3, self.dec3 = nn.ConvTranspose2d(b*8,b*4,2,2), DoubleConv(b*8,b*4)
        self.up2, self.dec2 = nn.ConvTranspose2d(b*4,b*2,2,2), DoubleConv(b*4,b*2)
        self.up1, self.dec1 = nn.ConvTranspose2d(b*2,b,2,2), DoubleConv(b*2,b)
        self.head = nn.Conv2d(b,out_channels,1)
        self.apply(self._init)

    @staticmethod
    def _init(module):
        if isinstance(module, nn.Conv2d):
            nn.init.kaiming_normal_(module.weight, nonlinearity="relu")
            if module.bias is not None: nn.init.zeros_(module.bias)

    def forward(self, x):
        e1=self.enc1(x); e2=self.enc2(self.pool(e1)); e3=self.enc3(self.pool(e2)); e4=self.enc4(self.pool(e3))
        z=self.bottleneck(self.pool(e4))
        d4=self.dec4(torch.cat([self.up4(z),e4],1)); d3=self.dec3(torch.cat([self.up3(d4),e3],1))
        d2=self.dec2(torch.cat([self.up2(d3),e2],1)); d1=self.dec1(torch.cat([self.up1(d2),e1],1))
        return self.head(d1)
