"""
Loss formulation and gradient unit tests for Phase 15.
Loss formulation, autograd agreement, and gradient unit tests for Phase 15.
Tests deterministic behavior across all candidate losses:
L0: 0.5 BCEWithLogits + 0.5 SoftDice
L1: 0.5 BinaryFocal + 0.5 SoftDice
L2: Tversky(alpha=0.30, beta=0.70)
L3: FocalTversky(alpha=0.30, beta=0.70, gamma=0.75)
"""
import torch
import torch.nn as nn
import numpy as np

class DiceLoss(nn.Module):
    def __init__(self, epsilon=1e-6):
        super().__init__()
        self.epsilon = epsilon

    def forward(self, logits, targets):
        probs = torch.sigmoid(logits)
        dims = tuple(range(1, logits.ndim))
        intersection = (probs * targets).sum(dims)
        denominator = probs.sum(dims) + targets.sum(dims)
        return (1.0 - (2.0 * intersection + self.epsilon) / (denominator + self.epsilon)).mean()

class BCEDiceLoss(nn.Module):
    def __init__(self, bce_weight=0.5, dice_weight=0.5, epsilon=1e-6):
        super().__init__()
        self.bce_weight = bce_weight
        self.dice_weight = dice_weight
        self.bce = nn.BCEWithLogitsLoss()
        self.dice = DiceLoss(epsilon)

    def forward(self, logits, targets):
        return self.bce_weight * self.bce(logits, targets) + self.dice_weight * self.dice(logits, targets)

class BinaryFocalLoss(nn.Module):
    def __init__(self, alpha=0.25, gamma=2.0, reduction='mean'):
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.reduction = reduction

    def forward(self, logits, targets):
        p = torch.sigmoid(logits)
        p_t = targets * p + (1.0 - targets) * (1.0 - p)
        alpha_t = targets * self.alpha + (1.0 - targets) * (1.0 - self.alpha)
        focal_weight = alpha_t * torch.pow(1.0 - p_t, self.gamma)
        loss = -focal_weight * torch.log(torch.clamp(p_t, min=1e-7, max=1.0))
        if self.reduction == 'mean':
            return loss.mean()
        elif self.reduction == 'sum':
            return loss.sum()
        return loss

class FocalDiceLoss(nn.Module):
    def __init__(self, focal_weight=0.5, dice_weight=0.5, alpha=0.25, gamma=2.0, epsilon=1e-6):
        super().__init__()
        self.focal_weight = focal_weight
        self.dice_weight = dice_weight
        self.focal = BinaryFocalLoss(alpha=alpha, gamma=gamma, reduction='mean')
        self.dice = DiceLoss(epsilon)

    def forward(self, logits, targets):
        return self.focal_weight * self.focal(logits, targets) + self.dice_weight * self.dice(logits, targets)

class TverskyLoss(nn.Module):
    def __init__(self, alpha=0.30, beta=0.70, epsilon=1e-6, reduction='mean'):
        super().__init__()
        self.alpha = alpha
        self.beta = beta
        self.epsilon = epsilon
        self.reduction = reduction

    def forward(self, logits, targets):
        probs = torch.sigmoid(logits)
        dims = tuple(range(1, logits.ndim))
        tp = (probs * targets).sum(dims)
        fp = (probs * (1.0 - targets)).sum(dims)
        fn = ((1.0 - probs) * targets).sum(dims)
        ti = (tp + self.epsilon) / (tp + self.alpha * fp + self.beta * fn + self.epsilon)
        loss = 1.0 - ti
        if self.reduction == 'mean':
            return loss.mean()
        elif self.reduction == 'sum':
            return loss.sum()
        return loss

class FocalTverskyLoss(nn.Module):
    def __init__(self, alpha=0.30, beta=0.70, gamma=0.75, epsilon=1e-6, reduction='mean'):
        super().__init__()
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.epsilon = epsilon
        self.reduction = reduction

    def forward(self, logits, targets):
        probs = torch.sigmoid(logits)
        dims = tuple(range(1, logits.ndim))
        tp = (probs * targets).sum(dims)
        fp = (probs * (1.0 - targets)).sum(dims)
        fn = ((1.0 - probs) * targets).sum(dims)
        ti = (tp + self.epsilon) / (tp + self.alpha * fp + self.beta * fn + self.epsilon)
        loss = torch.pow(1.0 - ti, self.gamma)
        if self.reduction == 'mean':
            return loss.mean()
        elif self.reduction == 'sum':
            return loss.sum()
        return loss

def run_tests():
    print("=== 1. Focal Tversky Derivative Analysis ===")
def test_autograd_derivative_agreement():
    print("=== 1. Autograd vs Analytic Derivative Agreement for L3 ===")
    tis = [0.00, 0.25, 0.50, 0.75, 0.90, 0.99]
    gamma = 0.75
    tis = [0.0, 0.25, 0.50, 0.75, 0.90, 0.99]
    print(f"L = (1 - TI)^{gamma}")
    print("TI    | Loss   | dL/dTI  | |dL/dTI|")
    print("-----------------------------------")
    for ti in tis:
        loss_val = (1.0 - ti) ** gamma
        diff = max(1e-12, 1.0 - ti)
        deriv = -gamma * (diff ** (gamma - 1.0))
        print(f"{ti:.2f}  | {loss_val:.4f} | {deriv:7.4f} | {abs(deriv):7.4f}")

    print("TI    | Analytic dL/dTI | Autograd dL/dTI | |dL/dTI|  | Abs Diff")
    print("----------------------------------------------------------------")
    for ti_val in tis:
        ti = torch.tensor(ti_val, dtype=torch.float64, requires_grad=True)
        loss = torch.pow(1.0 - ti, gamma)
        loss.backward()

        autograd_deriv = ti.grad.item()
        autograd_mag = abs(autograd_deriv)

        # Exact formula: dL/dTI = -0.75 * (1 - TI)^(-0.25)
        diff_term = max(1e-12, 1.0 - ti_val)
        analytic_deriv = -gamma * (diff_term ** (-0.25))
        analytic_mag = gamma * (diff_term ** (-0.25))

        diff = abs(autograd_mag - analytic_mag)
        print(f"{ti_val:.2f}  | {analytic_deriv:15.6f} | {autograd_deriv:15.6f} | {analytic_mag:8.6f}  | {diff:.1e}")
        assert diff < 1e-10, f"Autograd mismatch at TI={ti_val}!"
    print("Autograd agreement check: PASS")

def run_tests():
    test_autograd_derivative_agreement()

    print("\n=== 2. Numerical Sanity on Controlled Test Cases ===")
    test_cases = [
        ("Perfect Prediction", torch.tensor([[[[10.0, -10.0], [-10.0, 10.0]]]]), torch.tensor([[[[1.0, 0.0], [0.0, 1.0]]]])),
        ("All-Background Prediction", torch.tensor([[[[-10.0, -10.0], [-10.0, -10.0]]]]), torch.tensor([[[[1.0, 0.0], [0.0, 1.0]]]])),
        ("All-Foreground Prediction", torch.tensor([[[[10.0, 10.0], [10.0, 10.0]]]]), torch.tensor([[[[1.0, 0.0], [0.0, 1.0]]]])),
        ("One TP / One FN", torch.tensor([[[[10.0, -10.0], [-10.0, -10.0]]]]), torch.tensor([[[[1.0, 1.0], [0.0, 0.0]]]])),
        ("One TP / One FP", torch.tensor([[[[10.0, 10.0], [-10.0, -10.0]]]]), torch.tensor([[[[1.0, 0.0], [0.0, 0.0]]]])),
        ("Mixed Logits", torch.tensor([[[[1.5, -0.8], [0.2, -2.1]]]]), torch.tensor([[[[1.0, 0.0], [1.0, 0.0]]]]))
    ]

    l0_fn = BCEDiceLoss(0.5, 0.5, epsilon=1e-6)
    l1_fn = FocalDiceLoss(0.5, 0.5, alpha=0.25, gamma=2.0, epsilon=1e-6)
    l2_fn = TverskyLoss(alpha=0.30, beta=0.70, epsilon=1e-6)
    l3_fn = FocalTverskyLoss(alpha=0.30, beta=0.70, gamma=0.75, epsilon=1e-6)

    for name, logits, targets in test_cases:
        v0 = l0_fn(logits, targets).item()
        v1 = l1_fn(logits, targets).item()
        v2 = l2_fn(logits, targets).item()
        v3 = l3_fn(logits, targets).item()
        assert np.isfinite([v0, v1, v2, v3]).all(), f"Non-finite loss on {name}"
        print(f"Case '{name}': L0={v0:.4f}, L1={v1:.4f}, L2={v2:.4f}, L3={v3:.4f}")

    print("\n=== 3. Negative-Target (Zero Ground-Truth) Gradient Audit ===")
    neg_target = torch.zeros(1, 1, 16, 16)
    fp_logits = torch.ones(1, 1, 16, 16, requires_grad=True) * 2.0 # Confident false-positives

    losses = [("L0 (BCE+Dice)", l0_fn), ("L1 (Focal+Dice)", l1_fn), ("L2 (Tversky)", l2_fn), ("L3 (FocalTversky)", l3_fn)]
    for lname, fn in losses:
        inp = fp_logits.clone().detach().requires_grad_(True)
        val = fn(inp, neg_target)
        val.backward()
        gnorm = inp.grad.norm().item()
        print(f"{lname:20s}: Loss={val.item():.6f}, Gradient Norm={gnorm:.6f}")

    print("\nAll loss tests PASSED successfully.")

if __name__ == "__main__":
    run_tests()
