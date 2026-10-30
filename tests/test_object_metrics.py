import unittest
import numpy as np
from src.metrics.object_metrics import object_metrics
from src.metrics.segmentation import hd95


class TestObjectMetrics(unittest.TestCase):
    def test_object_counts(self):
        gt=np.zeros((8,8),np.uint8); gt[1:3,1:3]=1; gt[5:7,5:7]=1
        pred=np.zeros_like(gt); pred[1:3,1:3]=1; pred[3:4,6:7]=1
        m=object_metrics(pred,gt)
        self.assertEqual(m["gt_component_count"],2); self.assertEqual(m["detected_gt_components"],1)
        self.assertEqual(m["missed_gt_components"],1); self.assertAlmostEqual(m["object_recall"],0.5)
        self.assertEqual(m["false_positive_predicted_components"],1)

    def test_hd95_empty_prediction(self):
        gt=np.zeros((8,8)); gt[2:5,2:5]=1
        result=hd95(np.zeros_like(gt),gt)
        self.assertFalse(result["hd95_valid"]); self.assertTrue(result["empty_prediction"]); self.assertTrue(np.isnan(result["hd95"]))

if __name__=="__main__": unittest.main()
