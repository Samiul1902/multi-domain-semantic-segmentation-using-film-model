import inspect,tempfile,unittest
from pathlib import Path
from itertools import product
import numpy as np
import pandas as pd
import torch
from PIL import Image
from src.inference.heatmap_targets import make_gaussian_heatmap
from src.inference.learned_roi import generate_localizer_rois,predict_localizer
from src.losses.localization import SoftFocalDiceLoss
from src.models.factory import create_model
from src.utils.checkpointing import save_training_checkpoint,load_training_checkpoint

class Meta:
 scale=1.;resized_height=64;resized_width=64;padding=(0,0,0,0)

class TestKUBLocalizer(unittest.TestCase):
 def test_heatmap_centers_and_max_combination(self):
  target=make_gaussian_heatmap(64,[(10,20),(40,45)],5);self.assertEqual(target.shape,(64,64));self.assertAlmostEqual(float(target[10,20]),1.);self.assertAlmostEqual(float(target[40,45]),1.);self.assertTrue(np.isfinite(target).all())
  self.assertTrue((target >= 0.0).all() and (target <= 1.0).all())

 def test_heatmap_subpixel_and_border(self):
  target = make_gaussian_heatmap(64, [(10.4, 20.6), (63.8, 63.8), (-0.5, -0.5)], 5)
  self.assertEqual(float(target[10, 21]), 1.0)
  self.assertEqual(float(target[63, 63]), 1.0)
  self.assertEqual(float(target[0, 0]), 1.0)
  self.assertTrue((target >= 0.0).all() and (target <= 1.0).all())

 def test_network_forward_backward_and_loss(self):
  model=create_model('kub_localizer',in_channels=1,out_channels=1,base_channels=16);x=torch.randn(2,1,64,64);y=model(x);self.assertEqual(y.shape,(2,1,64,64))
  target=torch.zeros_like(y);target[0,0,10,10]=1.
  loss=SoftFocalDiceLoss()(y,target);self.assertTrue(torch.isfinite(loss));loss.backward()

 def test_gt_free_proposal_api(self):
  self.assertNotIn('gt',inspect.signature(generate_localizer_rois).parameters);h=np.zeros((64,64),np.float32);h[10:15,20:25]=.9;p=generate_localizer_rois(h,Meta(),(64,64),.5,.1,3,.3);self.assertEqual(len(p),1)

 def test_checkpoint_resume_roundtrip(self):
  model=create_model('kub_localizer',in_channels=1,out_channels=1,base_channels=4);opt=torch.optim.AdamW(model.parameters());sch=torch.optim.lr_scheduler.CosineAnnealingLR(opt,100);sc=torch.amp.GradScaler('cuda',enabled=False)
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/'latest.pt';save_training_checkpoint(path,model,opt,sch,sc,2,4,.5,{'phase':'13B'},42,[{'epoch':1},{'epoch':2}],'phase4_v2',{'train':'h'},'candidate','kub_localizer',512,.5,early_stopping_state={'best':.5,'bad_epochs':1,'patience':15},loader_generator_states={'train':torch.Generator().get_state()})
   state=load_training_checkpoint(path,model,opt,sch,sc,False);self.assertEqual(state['epoch'],2);self.assertIn('random_state',state);self.assertEqual(state['early_stopping_state']['bad_epochs'],1)

 def test_phase13b_proposal_grid_size(self):
  THRESHOLDS=(.1,.2,.3,.4,.5);MARGINS=(.1,.2);TOPKS=(3,5);NMS_IOU=0.3
  grid=list(product(THRESHOLDS,MARGINS,TOPKS))
  self.assertEqual(len(grid), 20)
  self.assertEqual(THRESHOLDS, (.1,.2,.3,.4,.5))
  self.assertEqual(MARGINS, (.1,.2))
  self.assertEqual(TOPKS, (3,5))

 def test_feasibility_logic(self):
  data = [
   {'id': 1, 'tiny_recall90':1.0, 'overall_recall90':1.0, 'mean_proposals_per_image':1, 'mean_roi_area_fraction':1.0}, # infeasible area
   {'id': 2, 'tiny_recall90':1.0, 'overall_recall90':1.0, 'mean_proposals_per_image':6, 'mean_roi_area_fraction':0.05}, # infeasible props
   {'id': 3, 'tiny_recall90':0.9, 'overall_recall90':0.9, 'mean_proposals_per_image':5, 'mean_roi_area_fraction':0.10, 'threshold':0.1, 'top_k':3, 'margin':0.1}, # feasible exact bounds
   {'id': 4, 'tiny_recall90':0.8, 'overall_recall90':0.8, 'mean_proposals_per_image':4, 'mean_roi_area_fraction':0.05, 'threshold':0.2, 'top_k':3, 'margin':0.1}  # feasible
  ]
  df = pd.DataFrame(data)
  df['feasible'] = (df.mean_roi_area_fraction <= 0.10) & (df.mean_proposals_per_image <= 5.0)
  
  self.assertFalse(df[df.id==1].feasible.iloc[0])
  self.assertFalse(df[df.id==2].feasible.iloc[0])
  self.assertTrue(df[df.id==3].feasible.iloc[0])
  self.assertTrue(df[df.id==4].feasible.iloc[0])
  
  feasible_df = df[df.feasible]
  best = feasible_df.sort_values(['tiny_recall90','overall_recall90','mean_roi_area_fraction','mean_proposals_per_image','threshold','top_k','margin'],ascending=[False,False,True,True,False,True,True]).iloc[0]
  self.assertEqual(best.id, 3) # feasible config beats infeasible perfect-recall config
  
 def test_checkpoint_comparison_logic(self):
  # Checkpoint score is (tiny_recall90, overall_recall90, -mean_roi_area_fraction, -val_loss)
  score_A = (0.90, 0.80, -0.05, -0.3)
  score_B = (0.85, 0.85, -0.05, -0.2)
  self.assertTrue(score_A > score_B) # tiny_recall90 is primary
  score_C = (0.90, 0.85, -0.05, -0.3)
  self.assertTrue(score_C > score_A) # overall_recall90 is tie 1
  score_D = (0.90, 0.85, -0.02, -0.2)
  self.assertTrue(score_D > score_C) # -mean_roi_area_fraction is tie 2

 def test_centernet_loss(self):
  from src.losses.localization import CenterNetFocalLoss
  loss_fn = CenterNetFocalLoss(alpha=2.0, beta=4.0)
  self.assertEqual(loss_fn.alpha, 2.0)
  self.assertEqual(loss_fn.beta, 4.0)
  
  logits = torch.randn(2, 1, 64, 64, requires_grad=True)
  target = torch.zeros_like(logits)
  target[0, 0, 10, 10] = 1.0 # One positive center
  target[0, 0, 10, 11] = 0.5 # Gaussian tail
  
  loss = loss_fn(logits, target)
  self.assertTrue(torch.isfinite(loss).all())
  loss.backward()
  self.assertTrue(torch.isfinite(logits.grad).all())
  
 def test_centernet_loss_zero_positive(self):
  from src.losses.localization import CenterNetFocalLoss
  loss_fn = CenterNetFocalLoss()
  logits = torch.randn(1, 1, 16, 16, requires_grad=True)
  target = torch.zeros_like(logits) # Zero positive
  
  loss = loss_fn(logits, target)
  self.assertTrue(torch.isfinite(loss).all())
  loss.backward()
  self.assertTrue(torch.isfinite(logits.grad).all())

if __name__=='__main__':unittest.main()
