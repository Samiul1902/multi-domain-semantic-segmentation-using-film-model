import tempfile
import unittest
from pathlib import Path
import torch
from src.models.unet import UNet
from src.utils.checkpointing import save_training_checkpoint, load_training_checkpoint


class TestCheckpointing(unittest.TestCase):
    def test_roundtrip_and_metadata(self):
        torch.manual_seed(42); model=UNet(1,1,4).eval(); optimizer=torch.optim.AdamW(model.parameters(),lr=1e-4)
        scheduler=torch.optim.lr_scheduler.CosineAnnealingLR(optimizer,T_max=100); scaler=torch.amp.GradScaler('cuda',enabled=False)
        x=torch.randn(1,1,32,32)
        with torch.no_grad(): expected=model(x).clone()
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'latest.pt'
            save_training_checkpoint(path,model,optimizer,scheduler,scaler,3,12,.4,{"a":1},42,[{"epoch":3}],
                                     "phase4_v2",{"train":"hash"},"smoke","unet",512,.5)
            for parameter in model.parameters(): parameter.data.zero_()
            state=load_training_checkpoint(path,model,optimizer,scheduler,scaler,restore_rng=False)
            with torch.no_grad(): actual=model(x)
            self.assertTrue(torch.equal(expected,actual)); self.assertEqual(state["epoch"],3)
            self.assertEqual(state["manifest_version"],"phase4_v2"); self.assertIn("random_state",state)

if __name__=="__main__": unittest.main()
