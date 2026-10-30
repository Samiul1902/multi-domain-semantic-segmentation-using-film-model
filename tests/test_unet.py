import unittest
import torch
from src.models.unet import UNet


class TestUNet(unittest.TestCase):
    def test_forward_and_gradients(self):
        model=UNet(1,1,8); x=torch.randn(2,1,64,64); y=model(x)
        self.assertEqual(y.shape,x.shape); self.assertTrue(torch.isfinite(y).all())
        y.mean().backward()
        self.assertTrue(all(torch.isfinite(p.grad).all() for p in model.parameters() if p.grad is not None))

    def test_supported_non_square_shape(self):
        model=UNet(1,1,8).eval()
        with torch.no_grad(): y=model(torch.randn(1,1,80,96))
        self.assertEqual(y.shape,(1,1,80,96))

if __name__=="__main__": unittest.main()
