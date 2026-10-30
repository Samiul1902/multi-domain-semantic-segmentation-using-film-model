"""H2B frozen objective: SoftTargetFocalBCE (gamma = 2.0).

H2B single scientific axis: LOSS / OBJECTIVE SEMANTICS ONLY.

Frozen definition (post_phase13_h2b_protocol_frozen):

    p          = sigmoid(z)
    bce        = BCEWithLogits(z, y, reduction="none")
    modulation = |p - y| ** gamma
    loss_map   = modulation * bce
    L          = mean(loss_map)

equivalently

    L = mean( |sigmoid(z) - y|^2 * BCEWithLogits(z, y) )

with gamma = 2.0 FIXED prospectively (no grid, no sweep, no coefficient search).

The target `y` is the UNCHANGED frozen Gaussian heatmap (128x128, sigma=0.75,
center exactly 1.0, values in [0, 1]). This module never builds targets.

Gradients flow through BOTH the BCE term and the modulation term.
`p` is NEVER detached from the modulation term.

This module contains loss only: no dataset logic, no proposal logic, no
checkpoint logic, no architecture logic, no target generation, no threshold
selection.
"""
import torch
from torch import nn
from torch.nn import functional as F


class SoftTargetFocalBCE(nn.Module):
    """Soft-target focal BCE. gamma is fixed at 2.0 and must not be tuned."""

    def __init__(self, gamma: float = 2.0):
        super().__init__()
        self.gamma = float(gamma)

    def forward(self, logits: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        # --- target contract (do NOT silently clamp) -------------------------
        if not torch.isfinite(target).all():
            raise AssertionError("SoftTargetFocalBCE: target contains non-finite values")
        if target.numel() > 0 and (target.min().item() < 0.0 or target.max().item() > 1.0):
            raise AssertionError(
                "SoftTargetFocalBCE: target must lie in [0, 1]; "
                f"observed range [{target.min().item()}, {target.max().item()}]"
            )

        # float32 compute to keep AMP numerically safe (same convention as the
        # frozen CenterNetFocalLoss). This does not detach anything.
        z = logits.float()
        y = target.float()

        probability = torch.sigmoid(z)

        # BCE term -- gradients flow.
        bce = F.binary_cross_entropy_with_logits(z, y, reduction="none")

        # Modulation term -- p is NOT detached; gradients flow through here too.
        modulation = (probability - y).abs().pow(self.gamma)

        loss_map = modulation * bce
        return loss_map.mean()
