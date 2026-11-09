"""Paired, aspect-ratio-preserving KUB transforms."""
import random
from dataclasses import dataclass

import numpy as np
import torch
from PIL import Image, ImageEnhance, ImageOps


@dataclass
class ResizePadMetadata:
    scale: float
    resized_height: int
    resized_width: int
    padding: tuple


class SegmentationTransform:
    def __init__(self, size=512, train=False, flip_probability=0.5,
                 rotation_degrees=5.0, brightness=0.1, contrast=0.1,
                 image_mode="L"):
        if size not in {256, 512, 768, 1024}:
            raise ValueError("Supported sizes are 256, 512, 768, and 1024")
        if image_mode not in {"L", "RGB"}:
            raise ValueError("image_mode must be 'L' or 'RGB'")
        self.size, self.train = size, train
        self.flip_probability = flip_probability
        self.rotation_degrees = rotation_degrees
        self.brightness, self.contrast = brightness, contrast
        self.image_mode = image_mode

    def __call__(self, image, mask):
        image, mask = image.convert(self.image_mode), mask.convert("L")
        if self.train:
            if random.random() < self.flip_probability:
                image, mask = ImageOps.mirror(image), ImageOps.mirror(mask)
            angle = random.uniform(-self.rotation_degrees, self.rotation_degrees)
            image = image.rotate(angle, resample=Image.Resampling.BILINEAR, fillcolor=0)
            mask = mask.rotate(angle, resample=Image.Resampling.NEAREST, fillcolor=0)
            image = ImageEnhance.Brightness(image).enhance(random.uniform(1-self.brightness, 1+self.brightness))
            image = ImageEnhance.Contrast(image).enhance(random.uniform(1-self.contrast, 1+self.contrast))
        width, height = image.size
        scale = min(self.size / width, self.size / height)
        rw, rh = max(1, round(width * scale)), max(1, round(height * scale))
        image = image.resize((rw, rh), Image.Resampling.BILINEAR)
        mask = mask.resize((rw, rh), Image.Resampling.NEAREST)
        left, top = (self.size-rw)//2, (self.size-rh)//2
        right, bottom = self.size-rw-left, self.size-rh-top
        padding = (left, top, right, bottom)
        image, mask = ImageOps.expand(image, padding), ImageOps.expand(mask, padding)
        image_arr = np.asarray(image, dtype=np.float32).copy()
        if image_arr.ndim == 2:
            image_t = torch.from_numpy(image_arr).unsqueeze(0) / 255.0        # (1, H, W)
        else:
            image_t = torch.from_numpy(image_arr).permute(2, 0, 1) / 255.0    # (3, H, W)
        mask_t = torch.from_numpy((np.asarray(mask).copy() > 0).astype(np.float32)).unsqueeze(0)
        metadata = ResizePadMetadata(scale, rh, rw, padding)
        return image_t, mask_t, metadata
