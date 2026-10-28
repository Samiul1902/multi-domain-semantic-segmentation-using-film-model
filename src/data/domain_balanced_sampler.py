"""Deterministic domain-balanced sampler for the Phase-20 shared four-domain model.

Why this exists
---------------
The four development domains are strongly imbalanced in TRAIN:

    ISIC 2556 | KUB 1978 | KVASIR 696 | BUSI 602      (total 5832)

A plain shuffle would let ISIC and KUB dominate BUSI and Kvasir (ISIC alone is
4.2x BUSI). Phase 20 therefore freezes an explicit **domain-balanced** sampling
policy so that every domain contributes an equal expected share of each epoch.

Governance
----------
``task_id`` / ``dataset`` may be used for SAMPLING and BOOKKEEPING only. They are
never passed to the model forward pass. This module is sampler-side only; it
touches no model input.

Determinism
-----------
The sampler is driven by an explicitly seeded ``torch.Generator``, so a given
(base_seed, epoch) pair always yields the same index stream. That property is
what makes the trainer resumable bit-exactly: epoch k is a pure function of
(base_seed, k) and does not depend on how many epochs ran before it.
"""
from __future__ import annotations

from typing import Dict, List

import numpy as np
import torch
from torch.utils.data import WeightedRandomSampler

__all__ = [
    "BALANCED_SAMPLING_POLICY_ID",
    "derive_epoch_seed",
    "domain_weights",
    "build_domain_balanced_sampler",
    "expected_domain_proportions",
]

BALANCED_SAMPLING_POLICY_ID = "phase20_domain_balanced_uniform_v1"


def derive_epoch_seed(base_seed: int, epoch: int) -> int:
    """Deterministic per-epoch seed.

    ``epoch k`` is reproducible independently of the epochs that preceded it,
    which is what makes a resumed run bit-exact.
    """
    return int((base_seed * 1_000_003 + int(epoch) * 7919) % (2**31 - 1))


def domain_weights(datasets: List[str]) -> np.ndarray:
    """Per-sample weights giving every domain an equal total weight."""
    arr = np.asarray(datasets)
    counts = {d: int((arr == d).sum()) for d in np.unique(arr)}
    return np.array([1.0 / counts[d] for d in arr], dtype=np.float64)


def build_domain_balanced_sampler(datasets: List[str], base_seed: int, epoch: int,
                                  num_samples: int | None = None) -> WeightedRandomSampler:
    """WeightedRandomSampler with per-domain equal expected mass.

    ``num_samples`` defaults to the dataset size, i.e. one balanced epoch keeps
    the same number of optimisation steps as an ordinary epoch.
    """
    weights = torch.as_tensor(domain_weights(datasets), dtype=torch.double)
    n = int(num_samples if num_samples is not None else len(datasets))
    generator = torch.Generator()
    generator.manual_seed(derive_epoch_seed(base_seed, epoch))
    return WeightedRandomSampler(weights, num_samples=n, replacement=True,
                                 generator=generator)


def expected_domain_proportions(datasets: List[str]) -> Dict[str, dict]:
    """Prospective audit of the expected per-domain sampling proportions."""
    arr = np.asarray(datasets)
    w = domain_weights(datasets)
    total = float(w.sum())
    out: Dict[str, dict] = {}
    for d in sorted(np.unique(arr)):
        m = arr == d
        share = float(w[m].sum() / total)
        out[str(d)] = {
            "dataset_size": int(m.sum()),
            "dataset_share_of_pool": round(float(m.sum() / len(arr)), 6),
            "expected_sampling_proportion": round(share, 6),
            "expected_samples_per_balanced_epoch": round(share * len(arr), 2),
        }
    return out
