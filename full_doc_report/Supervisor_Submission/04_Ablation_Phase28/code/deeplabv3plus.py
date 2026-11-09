"""DeepLabV3+ with a randomly initialized ResNet-50 output-stride-16 backbone."""
import torch
from torch import nn
from torch.nn import functional as F
from torchvision.models import resnet50


class ASPPConv(nn.Sequential):
    def __init__(self, in_channels, out_channels, dilation):
        super().__init__(
            nn.Conv2d(in_channels, out_channels, 3, padding=dilation, dilation=dilation, bias=False),
            nn.BatchNorm2d(out_channels), nn.ReLU(inplace=True),
        )


class ASPPPooling(nn.Sequential):
    def __init__(self, in_channels, out_channels):
        super().__init__(nn.AdaptiveAvgPool2d(1), nn.Conv2d(in_channels, out_channels, 1, bias=False),
                         nn.BatchNorm2d(out_channels), nn.ReLU(inplace=True))

    def forward(self, x):
        return F.interpolate(super().forward(x), size=x.shape[-2:], mode="bilinear", align_corners=False)


class ASPP(nn.Module):
    def __init__(self, in_channels=2048, out_channels=256, rates=(6, 12, 18)):
        super().__init__()
        self.branches = nn.ModuleList([
            nn.Sequential(nn.Conv2d(in_channels, out_channels, 1, bias=False),
                          nn.BatchNorm2d(out_channels), nn.ReLU(inplace=True)),
            *[ASPPConv(in_channels, out_channels, rate) for rate in rates],
            ASPPPooling(in_channels, out_channels),
        ])
        self.project = nn.Sequential(
            nn.Conv2d(out_channels * 5, out_channels, 1, bias=False),
            nn.BatchNorm2d(out_channels), nn.ReLU(inplace=True), nn.Dropout(0.1),
        )

    def forward(self, x):
        return self.project(torch.cat([branch(x) for branch in self.branches], dim=1))


class DeepLabV3Plus(nn.Module):
    """Canonical V3+ ASPP/low-level decoder; no pretrained weights are requested."""
    def __init__(self, in_channels=1, out_channels=1, base_channels=32):
        super().__init__()
        del base_channels  # Common factory signature; canonical decoder width remains 256.
        backbone = resnet50(weights=None, replace_stride_with_dilation=[False, False, True])
        backbone.conv1 = nn.Conv2d(in_channels, 64, 7, stride=2, padding=3, bias=False)
        self.stem = nn.Sequential(backbone.conv1, backbone.bn1, backbone.relu, backbone.maxpool)
        self.layer1, self.layer2, self.layer3, self.layer4 = (
            backbone.layer1, backbone.layer2, backbone.layer3, backbone.layer4)
        self.aspp = ASPP(2048, 256, (6, 12, 18))
        self.low_project = nn.Sequential(nn.Conv2d(256, 48, 1, bias=False),
                                         nn.BatchNorm2d(48), nn.ReLU(inplace=True))
        self.decoder = nn.Sequential(
            nn.Conv2d(304, 256, 3, padding=1, bias=False), nn.BatchNorm2d(256), nn.ReLU(inplace=True),
            nn.Conv2d(256, 256, 3, padding=1, bias=False), nn.BatchNorm2d(256), nn.ReLU(inplace=True),
            nn.Conv2d(256, out_channels, 1),
        )
        self._init_new_layers()

    def _init_new_layers(self):
        # ResNet was also randomly initialized by torchvision (weights=None).
        for module in [self.stem[0], self.aspp, self.low_project, self.decoder]:
            for layer in module.modules() if isinstance(module, nn.Module) else []:
                if isinstance(layer, nn.Conv2d):
                    nn.init.kaiming_normal_(layer.weight, nonlinearity="relu")
                    if layer.bias is not None:
                        nn.init.zeros_(layer.bias)

    def forward(self, x):
        input_size = x.shape[-2:]
        x = self.stem(x)
        low = self.layer1(x)
        x = self.layer2(low); x = self.layer3(x); x = self.layer4(x)
        x = self.aspp(x)
        x = F.interpolate(x, size=low.shape[-2:], mode="bilinear", align_corners=False)
        x = self.decoder(torch.cat([x, self.low_project(low)], dim=1))
        return F.interpolate(x, size=input_size, mode="bilinear", align_corners=False)
