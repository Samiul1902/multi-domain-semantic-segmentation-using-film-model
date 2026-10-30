import random
import unittest
from pathlib import Path
import numpy as np
import torch
from PIL import Image

from src.data.kub_dataset import KUBDataset, TestAccessError
from src.data.transforms import SegmentationTransform

ROOT=Path(r"D:\Softfors\jup")


class TestKUBDataset(unittest.TestCase):
    def test_lengths_and_metadata(self):
        train=KUBDataset(ROOT/"manifests/train.csv","TRAIN",SegmentationTransform(256,False),ROOT/"reports/tables/kub_train_samples_sized.csv")
        val=KUBDataset(ROOT/"manifests/val.csv","VAL",SegmentationTransform(256,False),ROOT/"reports/tables/kub_val_samples_sized.csv")
        self.assertEqual(len(train),1979); self.assertEqual(len(val),283)
        item=train[0]
        self.assertIn(item["category"],{"Kidney_Stone","Bladder_Stone","Ureteric_Stone"})
        self.assertTrue(str(item["patient_id"]).startswith("patient-"))
        self.assertIn(item["view_type"],{"FULL_FIELD","ROI_CROP"})
        self.assertIn(item["dominant_object_stratum"],{"TINY","SMALL","MEDIUM","LARGE","ROI_NOT_PRIMARY_BINNED"})
        self.assertEqual(item["image"].shape,(1,256,256)); self.assertEqual(item["mask"].shape,(1,256,256))
        self.assertEqual(set(torch.unique(item["mask"]).tolist()).difference({0.0,1.0}),set())

    def test_mask_positive_semantics_and_alignment(self):
        image=Image.fromarray(np.zeros((10,20),dtype=np.uint8)); raw=np.zeros((10,20),dtype=np.uint8)
        raw[2:5,4:8]=1; raw[5:8,8:12]=2; raw[1,1]=3; raw[8,18]=255
        transform=SegmentationTransform(256,False); x,y,meta=transform(image,Image.fromarray(raw))
        self.assertEqual(set(torch.unique(y).tolist()),{0.0,1.0}); self.assertEqual(int(y.sum()),int((raw>0).sum()*0+ y.sum()))
        self.assertEqual(x.shape,y.shape); self.assertEqual(meta.padding,(0,64,0,64))

    def test_validation_is_deterministic(self):
        dataset=KUBDataset(ROOT/"manifests/val.csv","VAL",SegmentationTransform(256,False),ROOT/"reports/tables/kub_val_samples_sized.csv")
        first=dataset[0]; second=dataset[0]
        self.assertTrue(torch.equal(first["image"],second["image"])); self.assertTrue(torch.equal(first["mask"],second["mask"]))

    def test_train_randomness_does_not_apply_to_val(self):
        self.assertFalse(SegmentationTransform(256,False).train)
        self.assertTrue(SegmentationTransform(256,True).train)

    def test_test_blocked_without_reading(self):
        with self.assertRaises(TestAccessError):
            KUBDataset(ROOT/"manifests/test.csv","TEST")

if __name__=="__main__": unittest.main()
