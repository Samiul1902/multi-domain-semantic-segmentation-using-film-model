"""Pure, importable definitions of the frozen Phase-25 router and safety modules.

Why this module exists
----------------------
The canonical producers are top-level *scripts*:

* ``scripts/analysis/train_phase25d_router.py``   -> ``BARRBenefitRouterV1``
* ``scripts/analysis/phase25f_execution_common.py`` -> ``BARRPostSafetyV1``

Both execute training/data loading at import time, so neither can be imported.
Several audit scripts therefore re-extract the class text with a regex, and the
FULL three-seed pipeline previously carried its own verbatim copies.  That is
two independent ways for the architecture to drift away from the frozen
checkpoints it must remain bit-compatible with.

This module is the single source of truth.  It contains **only** pure model
definitions -- no data access, no training loop, no argparse, no side effects at
import time.  The legacy scripts are deliberately left untouched so frozen
historical behaviour is preserved; ``tests/test_phase25_architecture_drift.py``
extracts the classes from those scripts and asserts the two definitions are
identical in state-dict keys, shapes, parameter counts and forward output.

Any change here that is not mirrored in the frozen producers (or vice versa)
fails that test.
"""
from __future__ import annotations

import hashlib
import json
from typing import Sequence

import numpy as np
import torch
from torch import nn

# --------------------------------------------------------------------------- #
# Benefit router B_phi -- frozen Phase-25D architecture
# --------------------------------------------------------------------------- #
ROUTER_TASK_COUNT = 4
ROUTER_NUMERIC_DIM = 202
ROUTER_TASK_EMBED_DIM = 16
ROUTER_TOTAL_DIM = ROUTER_NUMERIC_DIM + ROUTER_TASK_EMBED_DIM
ROUTER_HIDDEN: Sequence[int] = (128, 64)
ROUTER_DROPOUT = 0.10
ROUTER_EXPECTED_PARAMETERS = 36_801
ROUTER_ARCHITECTURE_ID = "barr_benefit_router_v1"

#: the eight scalar columns standardised on the FIT split only
ROUTER_SCALAR_NORMALIZE_IDX = (192, 193, 194, 195, 196, 197, 200, 201)


class BARRBenefitRouterV1(nn.Module):
    """Pre-refinement counterfactual-gain regressor (frozen Phase-25D).

    ``Linear(218,128) -> LayerNorm -> SiLU -> Dropout(0.10) -> Linear(128,64)
    -> LayerNorm -> SiLU -> Dropout(0.10) -> Linear(64,1)``, with a learned
    task embedding concatenated to the 202 numeric features.  Returns one raw
    scalar per sample (no activation).
    """

    def __init__(self) -> None:
        super().__init__()
        self.task_embedding = nn.Embedding(ROUTER_TASK_COUNT, ROUTER_TASK_EMBED_DIM)
        self.net = nn.Sequential(
            nn.Linear(ROUTER_TOTAL_DIM, ROUTER_HIDDEN[0]),
            nn.LayerNorm(ROUTER_HIDDEN[0], elementwise_affine=True),
            nn.SiLU(),
            nn.Dropout(ROUTER_DROPOUT),
            nn.Linear(ROUTER_HIDDEN[0], ROUTER_HIDDEN[1]),
            nn.LayerNorm(ROUTER_HIDDEN[1], elementwise_affine=True),
            nn.SiLU(),
            nn.Dropout(ROUTER_DROPOUT),
            nn.Linear(ROUTER_HIDDEN[1], 1),
        )

    def forward(self, x_numeric: torch.Tensor, task_ids: torch.Tensor) -> torch.Tensor:
        emb = self.task_embedding(task_ids)
        return self.net(torch.cat([x_numeric, emb], dim=-1)).squeeze(-1)


# --------------------------------------------------------------------------- #
# Post-refinement safety gate S_omega -- frozen Phase-25F architecture
# --------------------------------------------------------------------------- #
SAFETY_FEATURE_DIM = 20
SAFETY_NUMERIC_DIM = 16
SAFETY_ONEHOT_DIM = 4
SAFETY_HIDDEN: Sequence[int] = (32, 16)
SAFETY_EXPECTED_PARAMETERS = 1_217
SAFETY_ARCHITECTURE_ID = "barr_post_safety_v1"

#: 16 numeric columns standardised on FIT only; 16..19 are the task one-hot
SAFETY_NUMERIC_IDX = tuple(range(0, 16))
SAFETY_ONEHOT_IDX = tuple(range(16, 20))


class BARRPostSafetyV1(nn.Module):
    """Refined-crop acceptance classifier (frozen Phase-25F).

    ``Linear(20,32) -> SiLU -> Linear(32,16) -> SiLU -> Linear(16,1)``.
    Returns one RAW logit -- the sigmoid belongs to the caller's threshold rule.
    """

    def __init__(self) -> None:
        super().__init__()
        self.fc1 = nn.Linear(SAFETY_FEATURE_DIM, SAFETY_HIDDEN[0])
        self.fc2 = nn.Linear(SAFETY_HIDDEN[0], SAFETY_HIDDEN[1])
        self.fc3 = nn.Linear(SAFETY_HIDDEN[1], 1)
        self.reset_parameters()

    def reset_parameters(self) -> None:
        """Exactly the standard PyTorch ``Linear`` initialisation, made explicit.

        Kept as a named method because the frozen producer calls it explicitly;
        removing it would silently change initial weights for a given seed.
        """
        for lin in (self.fc1, self.fc2, self.fc3):
            nn.init.kaiming_uniform_(lin.weight, a=np.sqrt(5))
            bound = 1.0 / np.sqrt(lin.in_features)
            nn.init.uniform_(lin.bias, -bound, bound)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = nn.functional.silu(self.fc1(x))
        x = nn.functional.silu(self.fc2(x))
        return self.fc3(x).squeeze(-1)


# --------------------------------------------------------------------------- #
def count_trainable_parameters(model: nn.Module) -> int:
    """Matches ``count_params`` in both canonical producers."""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def architecture_fingerprint() -> str:
    """SHA-256 over the structural facts a checkpoint depends on."""
    body = {
        "router": {
            "architecture_id": ROUTER_ARCHITECTURE_ID,
            "task_count": ROUTER_TASK_COUNT,
            "numeric_dim": ROUTER_NUMERIC_DIM,
            "task_embed_dim": ROUTER_TASK_EMBED_DIM,
            "hidden": list(ROUTER_HIDDEN),
            "dropout": ROUTER_DROPOUT,
            "parameters": ROUTER_EXPECTED_PARAMETERS,
            "normalize_idx": list(ROUTER_SCALAR_NORMALIZE_IDX),
        },
        "safety": {
            "architecture_id": SAFETY_ARCHITECTURE_ID,
            "feature_dim": SAFETY_FEATURE_DIM,
            "numeric_dim": SAFETY_NUMERIC_DIM,
            "onehot_dim": SAFETY_ONEHOT_DIM,
            "hidden": list(SAFETY_HIDDEN),
            "parameters": SAFETY_EXPECTED_PARAMETERS,
        },
    }
    payload = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


__all__ = [
    "BARRBenefitRouterV1",
    "BARRPostSafetyV1",
    "ROUTER_ARCHITECTURE_ID",
    "ROUTER_DROPOUT",
    "ROUTER_EXPECTED_PARAMETERS",
    "ROUTER_HIDDEN",
    "ROUTER_NUMERIC_DIM",
    "ROUTER_SCALAR_NORMALIZE_IDX",
    "ROUTER_TASK_COUNT",
    "ROUTER_TASK_EMBED_DIM",
    "ROUTER_TOTAL_DIM",
    "SAFETY_ARCHITECTURE_ID",
    "SAFETY_EXPECTED_PARAMETERS",
    "SAFETY_FEATURE_DIM",
    "SAFETY_HIDDEN",
    "SAFETY_NUMERIC_DIM",
    "SAFETY_NUMERIC_IDX",
    "SAFETY_ONEHOT_DIM",
    "SAFETY_ONEHOT_IDX",
    "architecture_fingerprint",
    "count_trainable_parameters",
]
