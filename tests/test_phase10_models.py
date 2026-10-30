import tempfile
import unittest
from pathlib import Path

import torch

from src.losses.segmentation import BCEDiceLoss
from src.models.factory import create_model
from src.utils.checkpointing import load_training_checkpoint, save_training_checkpoint


class TestPhase10Models(unittest.TestCase):
    MODEL_KEYS = ("attention_unet", "unetpp", "deeplabv3plus")

    def test_construction_shape_and_finite_forward(self):
        for key in self.MODEL_KEYS:
            with self.subTest(model=key):
                model = create_model(key, in_channels=1, out_channels=1, base_channels=32).eval()
                with torch.no_grad():
                    output = model(torch.randn(1, 1, 64, 64))
                self.assertEqual(output.shape, (1, 1, 64, 64))
                self.assertTrue(torch.isfinite(output).all())

    def test_finite_backward(self):
        criterion = BCEDiceLoss()
        for key in self.MODEL_KEYS:
            with self.subTest(model=key):
                model = create_model(key, in_channels=1, out_channels=1, base_channels=32).train()
                output = model(torch.randn(2, 1, 64, 64))
                loss = criterion(output, torch.zeros_like(output))
                self.assertTrue(torch.isfinite(loss))
                loss.backward()
                self.assertTrue(any(p.grad is not None and torch.isfinite(p.grad).all() for p in model.parameters()))

    def test_attention_unet_checkpoint_roundtrip(self):
        model = create_model("attention_unet", in_channels=1, out_channels=1, base_channels=4).eval()
        optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4)
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=100)
        scaler = torch.amp.GradScaler("cuda", enabled=False)
        sample = torch.randn(1, 1, 32, 32)
        with torch.no_grad():
            expected = model(sample).clone()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "latest.pt"
            save_training_checkpoint(path, model, optimizer, scheduler, scaler, 1, 1, 0.1,
                                     {"phase": 10}, 42, [{"epoch": 1}], "phase4_v2",
                                     {"train": "hash"}, "smoke", "attention_unet", 512, 0.5)
            for parameter in model.parameters():
                parameter.data.zero_()
            load_training_checkpoint(path, model, optimizer, scheduler, scaler, restore_rng=False)
            with torch.no_grad():
                actual = model(sample)
            self.assertTrue(torch.equal(expected, actual))


if __name__ == "__main__":
    unittest.main()
