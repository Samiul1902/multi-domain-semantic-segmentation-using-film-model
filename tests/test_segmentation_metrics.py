import unittest
import torch
from src.metrics.segmentation import binary_metrics


class TestSegmentationMetrics(unittest.TestCase):
    def metrics(self,pred,target):
        logits=torch.where(torch.tensor(pred).bool(),torch.tensor(10.),torch.tensor(-10.)).reshape(1,1,2,2)
        target=torch.tensor(target,dtype=torch.float32).reshape(1,1,2,2)
        return {k:v.item() for k,v in binary_metrics(logits,target).items()}

    def test_perfect(self):
        m=self.metrics([1,0,0,1],[1,0,0,1])
        for value in m.values(): self.assertAlmostEqual(value,1.0,places=5)

    def test_no_overlap(self):
        m=self.metrics([1,1,0,0],[0,0,1,1])
        for value in m.values(): self.assertAlmostEqual(value,0.0,places=5)

    def test_partial_overlap(self):
        m=self.metrics([1,1,0,0],[1,0,1,0])
        self.assertAlmostEqual(m["dice"],0.5,places=5); self.assertAlmostEqual(m["iou"],1/3,places=5)
        self.assertAlmostEqual(m["precision"],0.5,places=5); self.assertAlmostEqual(m["recall"],0.5,places=5)

if __name__=="__main__": unittest.main()
