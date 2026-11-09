import torch
from torch import nn


class DiceLoss(nn.Module):
    def __init__(self, epsilon=1e-6):
        super().__init__(); self.epsilon = epsilon

    def forward(self, logits, targets):
        probabilities = torch.sigmoid(logits)
        dims = tuple(range(1, logits.ndim))
        intersection = (probabilities * targets).sum(dims)
        denominator = probabilities.sum(dims) + targets.sum(dims)
        return (1 - (2 * intersection + self.epsilon) / (denominator + self.epsilon)).mean()


class BCEDiceLoss(nn.Module):
    def __init__(self, bce_weight=0.5, dice_weight=0.5, epsilon=1e-6):
        super().__init__(); self.bce_weight=bce_weight; self.dice_weight=dice_weight
        self.bce=nn.BCEWithLogitsLoss(); self.dice=DiceLoss(epsilon)

    def forward(self, logits, targets):
        return self.bce_weight*self.bce(logits, targets)+self.dice_weight*self.dice(logits, targets)
