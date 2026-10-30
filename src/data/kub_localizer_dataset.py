"""FULL_FIELD-only KUB center-heatmap dataset for Phase 13B."""
from pathlib import Path
import random
import numpy as np
import pandas as pd
import torch
from PIL import Image, ImageEnhance, ImageOps
from scipy.ndimage import label
from torch.utils.data import Dataset

from src.data.kub_dataset import TestAccessError
from src.inference.heatmap_targets import make_gaussian_heatmap, heatmap_space_component_areas


class KUBLocalizerDataset(Dataset):
    """Image plus TRAIN/VAL GT-derived soft center heatmap supervision."""
    def __init__(self, sample_table, split, resolution, sigma, cache_in_memory=True,
                 heatmap_resolution=None, size_adaptive_sigma=False, A_ref=14.0,
                 sigma_min=0.35, sigma_max=0.75, manifest_path=None):
        split = split.upper()
        if split == "TEST":
            raise TestAccessError("TEST localizer construction is blocked")
        if split not in {"TRAIN", "VAL"}:
            raise ValueError("split must be TRAIN or VAL")
        frame = pd.read_csv(sample_table) if not isinstance(sample_table, pd.DataFrame) else sample_table.copy()
        self.frame = frame[frame["view_type"].eq("FULL_FIELD")].reset_index(drop=True)
        # OPT-IN manifest filter (H3 / SUPERVISOR §2): restrict the FULL_FIELD
        # population to the canonical clean-v3 manifest membership. This is a pure
        # OPERATIONAL population-enforcement change — it does not alter any
        # scientific axis. When unset, behaviour is byte-identical to Phase-13B.
        self.manifest_path = manifest_path
        if manifest_path is not None:
            man = pd.read_csv(manifest_path) if not isinstance(manifest_path, pd.DataFrame) else manifest_path
            man_ids = set(man["sample_id"].astype(str))
            before = len(self.frame)
            self.frame = self.frame[self.frame["sample_id"].astype(str).isin(man_ids)].reset_index(drop=True)
            print(f"[KUBLocalizerDataset:{split}] manifest-filter applied: {before} FULL_FIELD -> {len(self.frame)} canonical (manifest={getattr(manifest_path, 'name', manifest_path)})")
        self.split, self.resolution, self.sigma = split, resolution, sigma
        self.heatmap_resolution = heatmap_resolution if heatmap_resolution is not None else resolution
        self.size_adaptive_sigma = bool(size_adaptive_sigma)
        self.A_ref = float(A_ref)
        self.sigma_min = float(sigma_min)
        self.sigma_max = float(sigma_max)
        self.cache_in_memory, self._cache = cache_in_memory, {}

    def __len__(self): return len(self.frame)

    def __getitem__(self, index):
        row = self.frame.iloc[index]
        with Image.open(row.image_path) as image_file, Image.open(row.mask_path) as mask_file:
            image, mask = image_file.convert("L"), mask_file.convert("L")
            
        # 1. Extract authoritative original-space components
        orig_mask_array = np.asarray(mask) > 0
        labels, count = label(orig_mask_array, np.ones((3, 3), int))
        orig_centroids = []
        for component_id in range(1, count+1):
            ys, xs = np.where(labels == component_id)
            orig_centroids.append((float(ys.mean()), float(xs.mean())))
            
        width, height = int(row.width), int(row.height)
        mirrored = False
        angle = 0.0
        
        if self.split == "TRAIN":
            if random.random() < .5:
                image, mask = ImageOps.mirror(image), ImageOps.mirror(mask)
                mirrored = True
            angle = random.uniform(-5., 5.)
            image = image.rotate(angle, Image.Resampling.BILINEAR, fillcolor=0)
            mask = mask.rotate(angle, Image.Resampling.NEAREST, fillcolor=0)
            image = ImageEnhance.Brightness(image).enhance(random.uniform(.9, 1.1))
            image = ImageEnhance.Contrast(image).enhance(random.uniform(.9, 1.1))
            
        scale = min(self.resolution / width, self.resolution / height)
        rw, rh = max(1, round(width*scale)), max(1, round(height*scale))
        image = image.resize((rw, rh), Image.Resampling.BILINEAR)
        mask = mask.resize((rw, rh), Image.Resampling.NEAREST)
        left, top = (self.resolution-rw)//2, (self.resolution-rh)//2
        right, bottom = self.resolution-rw-left, self.resolution-rh-top
        image = ImageOps.expand(image, (left, top, right, bottom)); mask = ImageOps.expand(mask, (left, top, right, bottom))
        
        # 2. Map coordinates
        import math
        mapped_centroids = []
        for cy, cx in orig_centroids:
            if mirrored:
                cx = width - 1 - cx
            if angle != 0.0:
                cx_c = width / 2
                cy_c = height / 2
                rad = math.radians(angle)
                cx_old = cx
                cx = cx_c + (cx_old - cx_c) * math.cos(rad) + (cy - cy_c) * math.sin(rad)
                cy = cy_c - (cx_old - cx_c) * math.sin(rad) + (cy - cy_c) * math.cos(rad)
            cx = cx * scale + left
            cy = cy * scale + top
            
            # 3. Check if component is still visible (authorized transforms)
            # KUB objects are never perfectly removed by these small transforms,
            # but we ensure they remain in target list even if slightly clipped.
            if self.heatmap_resolution != self.resolution:
                factor = self.resolution / self.heatmap_resolution
                cy = cy / factor
                cx = cx / factor
            mapped_centroids.append((cy, cx))

        if self.size_adaptive_sigma:
            # H3 / A_TARGET_SUPPORT_REDESIGN: assign each component a heatmap-space
            # area, then a size-adaptive sigma (frozen monotonic mapping). Default
            # branch (size_adaptive_sigma=False) is byte-identical to Phase-13B.
            mask_padded_np = np.asarray(mask) > 0
            label_map, areas = heatmap_space_component_areas(
                mask_padded_np, self.resolution, self.heatmap_resolution)
            component_areas = []
            for cy, cx in mapped_centroids:
                icy = max(0, min(self.heatmap_resolution - 1, int(round(cy))))
                icx = max(0, min(self.heatmap_resolution - 1, int(round(cx))))
                lbl = int(label_map[icy, icx])
                component_areas.append(int(areas[lbl]) if lbl > 0 else 0)
            target = make_gaussian_heatmap(
                self.heatmap_resolution, mapped_centroids, self.sigma,
                component_areas=component_areas, sigma_min=self.sigma_min,
                sigma_max=self.sigma_max, A_ref=self.A_ref)
        else:
            target = make_gaussian_heatmap(self.heatmap_resolution, mapped_centroids, self.sigma)
        return {"image": torch.from_numpy(np.asarray(image, np.float32).copy()).unsqueeze(0)/255.,
                "heatmap": torch.from_numpy(target).unsqueeze(0),
                "sample_id": row.sample_id, "image_path": row.image_path,
                "mask_path": row.mask_path, "patient_id": row.patient_id,
                "category": row.category, "original_height": height,
                "original_width": width, "scale": scale,
                "resized_height": rh, "resized_width": rw,
                "padding": torch.tensor((left, top, right, bottom))}
