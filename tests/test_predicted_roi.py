import inspect
import unittest
from dataclasses import dataclass
import numpy as np
from src.inference.predicted_roi import (
    ProposalConfig, apply_context_margin, compute_iou, evaluate_roi_coverage,
    extract_predicted_components, generate_predicted_rois, non_max_suppression,
    union_roi_area_fraction,
)

@dataclass
class Metadata:
    scale: float = 1.0
    resized_height: int = 64
    resized_width: int = 64
    padding: tuple = (0,0,0,0)

# ``extract_predicted_components`` is documented to take the **512-space** probability
# map and rescale by ``512 // h_map``.  Production callers pass ``*_probability_512.npy``,
# so a 64x64 fixture is interpreted as an 8x downsampled canvas and its coordinates are
# multiplied by 8 -- which silently pushes blobs outside the content region.  These
# fixtures therefore use 512x512 maps, matching the contract and the real callers.

class TestPredictedROI(unittest.TestCase):
    def test_threshold_component_score_and_determinism(self):
        p=np.zeros((512,512),np.float32); p[5:10,7:12]=.6; p[30:40,35:45]=.9
        meta=Metadata(resized_height=512,resized_width=512)
        a=extract_predicted_components(p,.5,(512,512),meta); b=extract_predicted_components(p,.5,(512,512),meta)
        self.assertEqual(a,b); self.assertEqual(len(a),2); self.assertAlmostEqual(a[0]['max_probability'],.9,places=5)
    def test_zero_proposal(self):
        proposals=generate_predicted_rois(np.zeros((64,64),np.float32),Metadata(),(64,64),.2,.1,3,.5)
        self.assertEqual(proposals,[]); self.assertEqual(union_roi_area_fraction([], (64,64)),(0.,0.))
    def test_nms_and_topk(self):
        items=[{'bbox':(0,0,10,10),'max_probability':.9},{'bbox':(1,1,10,10),'max_probability':.8},{'bbox':(30,30,35,35),'max_probability':.7}]
        self.assertEqual(len(non_max_suppression(items,.3)),2)
        p=np.zeros((512,512),np.float32); p[1:4,1:4]=.9;p[20:23,20:23]=.8;p[40:43,40:43]=.7
        meta=Metadata(resized_height=512,resized_width=512)
        self.assertEqual(len(generate_predicted_rois(p,meta,(512,512),.5,.1,2,.5)),2)
    def test_margin_square_and_boundary(self):
        g=apply_context_margin((0,0,10,20),(64,64),.15); self.assertEqual(g['crop_side_pixels'],g['y2']-g['y1']); self.assertGreater(g['pad_top']+g['pad_left'],0); self.assertGreaterEqual(g['clip_y1'],0)
    def test_coordinate_mapping_with_padding(self):
        # content region in 512 space is rows [top, top+resized_h) = [2, 42)
        meta=Metadata(scale=.5,resized_height=40,resized_width=60,padding=(2,12,2,12)); p=np.zeros((512,512),np.float32);p[10:16,20:26]=.8
        c=extract_predicted_components(p,.5,(80,120),meta); self.assertEqual(len(c),1); self.assertTrue(0<=c[0]['bbox'][0]<80)
    def test_evaluation_separation_and_coverage(self):
        self.assertNotIn('gt',inspect.signature(generate_predicted_rois).parameters)
        mask=np.zeros((20,20),bool);mask[5:10,5:10]=1; gt=[{'component_id':1,'min_y':5,'min_x':5,'max_y':9,'max_x':9,'mask':mask}]
        proposal={'rank':1,'score':.8,'crop_geometry':{'clip_y1':4,'clip_y2':11,'clip_x1':4,'clip_x2':11}}
        result=evaluate_roi_coverage([proposal],gt)[0];self.assertTrue(result['covered90']);self.assertEqual(result['coverage_fraction'],1.)
        # Slice-count implementation must retain partial pixel-exact coverage.
        proposal['crop_geometry'].update(clip_y1=5,clip_y2=8,clip_x1=5,clip_x2=10)
        partial=evaluate_roi_coverage([proposal],gt)[0]
        self.assertAlmostEqual(partial['coverage_fraction'],15/25)
    def test_iou(self):
        self.assertEqual(compute_iou((0,0,4,4),(10,10,12,12)),0.); self.assertAlmostEqual(compute_iou((0,0,4,4),(0,0,4,4)),1.)
if __name__=='__main__': unittest.main()
