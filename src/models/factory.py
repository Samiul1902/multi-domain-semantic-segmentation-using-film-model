from .attention_unet import AttentionUNet
from .deeplabv3plus import DeepLabV3Plus
from .unet import UNet
from .unetpp import UNetPlusPlus
from .kub_localizer import KUBLocalizer
from .film import GlobalMedFiLM
from .segformer_b0 import SegFormerB0Binary


def create_model(name, **kwargs):
    key = name.lower().replace("-", "_").replace("+", "plus")
    models = {
        "unet": UNet,
        "attention_unet": AttentionUNet,
        "unetpp": UNetPlusPlus,
        "unetplusplus": UNetPlusPlus,
        "deeplabv3plus": DeepLabV3Plus,
        "deeplabv3_plus": DeepLabV3Plus,
        "kub_localizer": KUBLocalizer,
        "medfilm": GlobalMedFiLM,
        "global_medfilm": GlobalMedFiLM,
        "segformer_b0": SegFormerB0Binary,
        "segformer": SegFormerB0Binary,
    }
    if key in models:
        return models[key](**kwargs)
    supported_future = "hybrid, transformer"
    raise NotImplementedError(f"{name!r} is not implemented. Future registry keys: {supported_future}")
