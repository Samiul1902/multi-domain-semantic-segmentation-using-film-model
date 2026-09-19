"""Frozen Phase-13B soft-heatmap localization loss."""
import torch
from torch import nn

class SoftFocalDiceLoss(nn.Module):
    """0.75 sigmoid focal (alpha=.25,gamma=2) + 0.25 soft Dice."""
    def __init__(self,alpha=.25,gamma=2.,focal_weight=.75,dice_weight=.25,epsilon=1e-6):
        super().__init__();self.alpha=alpha;self.gamma=gamma;self.focal_weight=focal_weight;self.dice_weight=dice_weight;self.epsilon=epsilon
    def forward(self,logits,target):
        probability=torch.sigmoid(logits); ce=torch.nn.functional.binary_cross_entropy_with_logits(logits,target,reduction='none')
        pt=probability*target+(1-probability)*(1-target); alpha_t=self.alpha*target+(1-self.alpha)*(1-target)
        focal_values=alpha_t*(1-pt).pow(self.gamma)*ce
        positive=target.gt(0.01)
        # Normalize positive and background focal terms separately so a Gaussian
        # center cannot vanish inside millions of background pixels. The formula
        # remains sigmoid focal loss with the frozen alpha/gamma values.
        positive_focal=(focal_values*positive).sum()/positive.sum().clamp_min(1)
        negative_focal=(focal_values*~positive).sum()/(~positive).sum().clamp_min(1)
        focal=positive_focal+negative_focal
        focal=focal_values.mean()
        dims=tuple(range(1,logits.ndim)); intersection=(probability*target).sum(dims); dice=1-((2*intersection+self.epsilon)/(probability.sum(dims)+target.sum(dims)+self.epsilon)).mean()
        return self.focal_weight*focal+self.dice_weight*dice

class CenterNetFocalLoss(nn.Module):
    """Modified Focal Loss for CenterNet-style heatmaps.
    
    L_pos = - (1 - p)^alpha * log(p)
    L_neg = - (1 - y)^beta * p^alpha * log(1 - p)
    """
    def __init__(self, alpha=2.0, beta=4.0):
        super().__init__()
        self.alpha = alpha
        self.beta = beta
        
    def forward(self, logits, target):
        p = torch.sigmoid(logits)
        p = torch.sigmoid(logits.float()) # Compute in float32 to prevent AMP overflow
        target = target.float()
        
        # Safe clamping to avoid log(0) or nan
        p = torch.clamp(p, min=1e-6, max=1.0 - 1e-6)
        
        pos_inds = target.eq(1.0)
        neg_inds = target.lt(1.0)
        
        pos_loss = -torch.pow(1.0 - p, self.alpha) * torch.log(p)
        neg_loss = -torch.pow(1.0 - target, self.beta) * torch.pow(p, self.alpha) * torch.log(1.0 - p)
        
        pos_loss = pos_loss[pos_inds].sum()
        neg_loss = neg_loss[neg_inds].sum()
        
        num_pos = pos_inds.float().sum()
        if num_pos > 0:
            loss = (pos_loss + neg_loss) / num_pos
        else:
            loss = neg_loss
        
        return loss

