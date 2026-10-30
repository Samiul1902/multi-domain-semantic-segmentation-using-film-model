import unittest
import torch
from src.losses.segmentation import BCEDiceLoss


class TestSegmentationLoss(unittest.TestCase):
    def test_finite_backward_and_direction(self):
        criterion=BCEDiceLoss(); target=torch.tensor([[[[1.,0.],[0.,1.]]]])
        good=torch.tensor([[[[10.,-10.],[-10.,10.]]]],requires_grad=True)
        poor=torch.zeros_like(good,requires_grad=True)
        good_loss=criterion(good,target); poor_loss=criterion(poor,target)
        self.assertTrue(torch.isfinite(good_loss)); self.assertLess(good_loss.item(),poor_loss.item())
        poor_loss.backward(); self.assertTrue(torch.isfinite(poor.grad).all())

if __name__=="__main__": unittest.main()
