"""Manifest-backed KUB dataset with development TEST lock."""
from pathlib import Path
import pandas as pd
import torch
from PIL import Image
import numpy as np

from torch.utils.data import Dataset

from .transforms import SegmentationTransform


class TestAccessError(RuntimeError):
    pass


class KUBDataset(Dataset):
    def __init__(self, manifest_path, split, transform=None, metadata_path=None, allow_test=False, cache_in_memory=True, target_size=512):
        split = split.upper()
        if split == "TEST" and not allow_test:
            raise TestAccessError("TEST is frozen; development dataset construction is blocked")
        if split not in {"TRAIN", "VAL", "TEST"}:
            raise ValueError("split must be TRAIN, VAL, or TEST")
        frame = pd.read_csv(manifest_path)
        frame = frame[(frame["dataset"] == "KUB") & (frame["split"].str.upper() == split)].copy()
        self.frame = frame.reset_index(drop=True)
        self.split = split
        self.transform = transform or SegmentationTransform(size=target_size, train=split == "TRAIN")
        self.metadata = None
        if metadata_path and Path(metadata_path).exists() and split != "TEST":
            self.metadata = pd.read_csv(metadata_path).set_index("sample_id")
        self.cache_in_memory = cache_in_memory
        self.target_size = self.transform.size if hasattr(self.transform, "size") else target_size
        self._cache = {}

    def __len__(self):
        return len(self.frame)

    def _load_and_resize(self, image_path, mask_path):
        from PIL import ImageOps
        with Image.open(image_path) as img_file, Image.open(mask_path) as mask_file:
            raw_image = img_file.convert("L")
            raw_mask = mask_file.convert("L")
            original_width, original_height = raw_image.size
            
            scale = min(self.target_size / original_width, self.target_size / original_height)
            rw, rh = max(1, round(original_width * scale)), max(1, round(original_height * scale))
            proc_img = raw_image.resize((rw, rh), Image.Resampling.BILINEAR)
            proc_mask = raw_mask.resize((rw, rh), Image.Resampling.NEAREST)
            
            left, top = (self.target_size - rw) // 2, (self.target_size - rh) // 2
            right, bottom = self.target_size - rw - left, self.target_size - rh - top
            padding = (left, top, right, bottom)
            
            padded_img = ImageOps.expand(proc_img, padding)
            padded_mask = ImageOps.expand(proc_mask, padding)
            
            return padded_img, padded_mask, original_width, original_height, scale, padding

    def __getitem__(self, index):
        row = self.frame.iloc[index]
        if self.cache_in_memory and index in self._cache:
            raw_image, raw_mask, original_width, original_height, scale, padding = self._cache[index]
        else:
            raw_image, raw_mask, original_width, original_height, scale, padding = self._load_and_resize(row.image_path, row.mask_path)
            if self.cache_in_memory:
                self._cache[index] = (raw_image, raw_mask, original_width, original_height, scale, padding)

        # Apply augmentation if train
        if self.transform and self.transform.train:
            # Quick 512x512 augmentation
            import random
            from PIL import ImageEnhance, ImageOps
            img, mask = raw_image, raw_mask
            if random.random() < self.transform.flip_probability:
                img, mask = ImageOps.mirror(img), ImageOps.mirror(mask)
            angle = random.uniform(-self.transform.rotation_degrees, self.transform.rotation_degrees)
            img = img.rotate(angle, resample=Image.Resampling.BILINEAR, fillcolor=0)
            mask = mask.rotate(angle, resample=Image.Resampling.NEAREST, fillcolor=0)
            img = ImageEnhance.Brightness(img).enhance(random.uniform(1-self.transform.brightness, 1+self.transform.brightness))
            img = ImageEnhance.Contrast(img).enhance(random.uniform(1-self.transform.contrast, 1+self.transform.contrast))
            
            image_t = torch.from_numpy(np.asarray(img, dtype=np.float32).copy()).unsqueeze(0) / 255.0
            mask_t = torch.from_numpy((np.asarray(mask).copy() > 0).astype(np.float32)).unsqueeze(0)
        else:
            image_t = torch.from_numpy(np.asarray(raw_image, dtype=np.float32).copy()).unsqueeze(0) / 255.0
            mask_t = torch.from_numpy((np.asarray(raw_mask).copy() > 0).astype(np.float32)).unsqueeze(0)

        item = {
            "image": image_t, "mask": mask_t, "sample_id": row.sample_id,
            "patient_id": row.patient_id, "category": row.category,
            "view_type": "NOT_AVAILABLE", "dominant_object_stratum": "NOT_AVAILABLE",
            "component_count": -1, "original_height": original_height,
            "original_width": original_width, "image_path": row.image_path,
            "mask_path": row.mask_path, "resize_scale": scale,
            "padding": torch.tensor(padding),
        }
        if self.metadata is not None and row.sample_id in self.metadata.index:
            meta = self.metadata.loc[row.sample_id]
            for key in ("view_type", "dominant_object_stratum", "component_count"):
                if key in meta:
                    item[key] = meta[key]
        return item


