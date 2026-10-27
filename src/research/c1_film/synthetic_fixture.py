"""Explicit tensor-only fixture; never reads manifests, pixels, or checkpoints."""
import random

import numpy as np
import torch
from torch.utils.data import Dataset

from src.data.domain_balanced_sampler import build_domain_balanced_sampler, derive_epoch_seed
from src.data.loaders import create_loader
from src.data.multidomain_dataset import DATASET_ORDER


class ArtificialDataset(Dataset):
    def __init__(self, split):
        if split not in ("TRAIN", "VAL"):
            raise ValueError("C1_SYNTHETIC_SPLIT")
        self.split = split
        self.domains = [d for d in DATASET_ORDER for _ in range(2)]

    def __len__(self):
        return 8

    def __getitem__(self, index):
        g = torch.Generator().manual_seed(100 + index)
        x = torch.rand(3, 32, 32, generator=g)
        if self.split == "TRAIN":
            # Exercise all three RNG restorations and matched epoch seeding.
            x = x * (0.8 + 0.1 * random.random() + 0.1 * np.random.random())
            x = x + torch.rand((), dtype=torch.float32) * 0.01
        return {"image": x, "mask": (x[:1] > 0.5).float(),
                "dataset": self.domains[index], "task_id": index // 2,
                "sample_id": f"artificial-{self.split}-{index}", "split": self.split}


def fixture_loaders(seed, epoch):
    train, val = ArtificialDataset("TRAIN"), ArtificialDataset("VAL")
    sampler = build_domain_balanced_sampler(train.domains, seed, epoch)
    return (create_loader(train, 4, False, derive_epoch_seed(seed, epoch), num_workers=0,
                          pin_memory=False, sampler=sampler),
            create_loader(val, 4, False, seed, num_workers=0, pin_memory=False))
