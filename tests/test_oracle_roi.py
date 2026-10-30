import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from PIL import Image

from src.analysis.oracle_roi import (
    compute_square_crop,
    crop_and_preprocess,
    extract_gt_components,
    restore_crop_probability,
    fuse_probability_maps,
    run_oracle_roi_image,
)
from src.data.kub_dataset import TestAccessError
from src.models.factory import create_model

ROOT = Path(__file__).resolve().parents[1]


class TestOracleROI(unittest.TestCase):
    def test_extract_gt_components(self):
        gt_mask = np.zeros((100, 100), dtype=np.uint8)
        gt_mask[10:30, 20:50] = 1
        gt_mask[60:80, 70:90] = 1

        components, labeled = extract_gt_components(gt_mask)
        self.assertEqual(len(components), 2)
        self.assertEqual(components[0]["component_pixels"], 20 * 30)
        self.assertEqual(components[1]["component_pixels"], 20 * 20)

    def test_compute_square_crop(self):
        bbox = {"min_y": 20, "max_y": 40, "min_x": 30, "max_x": 70}
        image_shape = (200, 200)
        crop_geom = compute_square_crop(bbox, image_shape, margin=0.25)

        # bbox_h = 21, bbox_w = 41
        # m_y = round(0.25*21) = 5, m_x = round(0.25*41) = 10
        # exp_h = 31, exp_w = 61 -> side = 61
        self.assertEqual(crop_geom["crop_side_pixels"], 61)
        self.assertAlmostEqual(crop_geom["effective_magnification"], 512.0 / 61.0)
        self.assertEqual(crop_geom["clip_y2"] - crop_geom["clip_y1"] + crop_geom["pad_top"] + crop_geom["pad_bottom"], 61)
        self.assertEqual(crop_geom["clip_x2"] - crop_geom["clip_x1"] + crop_geom["pad_left"] + crop_geom["pad_right"], 61)

    def test_crop_and_preprocess_and_restore(self):
        img_arr = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        raw_image = Image.fromarray(img_arr)
        bbox = {"min_y": 10, "max_y": 30, "min_x": 20, "max_x": 40}
        crop_geom = compute_square_crop(bbox, (100, 100), margin=0.25)

        tensor = crop_and_preprocess(raw_image, crop_geom, target_size=512)
        self.assertEqual(tensor.shape, (1, 1, 512, 512))

        prob_512 = np.ones((512, 512), dtype=np.float32)
        prob_restored = restore_crop_probability(prob_512, crop_geom, (100, 100))
        self.assertEqual(prob_restored.shape, (100, 100))

        c_y1, c_y2 = crop_geom["clip_y1"], crop_geom["clip_y2"]
        c_x1, c_x2 = crop_geom["clip_x1"], crop_geom["clip_x2"]
        self.assertTrue((prob_restored[c_y1:c_y2, c_x1:c_x2] > 0.99).all())

    def test_multiple_component_probability_fusion(self):
        first = np.zeros((4, 5), dtype=np.float32); first[1, 1] = 0.7
        second = np.zeros((4, 5), dtype=np.float32); second[2, 3] = 0.9; second[1, 1] = 0.2
        fused = fuse_probability_maps([first, second], (4, 5))
        self.assertEqual(fused.shape, (4, 5))
        self.assertAlmostEqual(float(fused[1, 1]), 0.7)
        self.assertAlmostEqual(float(fused[2, 3]), 0.9)
        self.assertEqual(fuse_probability_maps([], (3, 2)).shape, (3, 2))

    def test_model_input_is_image_only_one_channel(self):
        image = Image.fromarray(np.zeros((40, 60), dtype=np.uint8))
        bbox = {"min_y": 5, "max_y": 15, "min_x": 10, "max_x": 25}
        geometry = compute_square_crop(bbox, (40, 60), margin=0.25)
        model_input = crop_and_preprocess(image, geometry, 512)
        self.assertEqual(model_input.shape, (1, 1, 512, 512))

    def test_test_rejection(self):
        model = create_model("unetpp", in_channels=1, out_channels=1, base_channels=32)
        test_df = pd.read_csv(ROOT / "manifests/test.csv")
        test_row = test_df[test_df["dataset"] == "KUB"].iloc[0]
        with self.assertRaises(TestAccessError):
            run_oracle_roi_image(test_row["image_path"], test_row["mask_path"], model, torch.device("cpu"))

        with self.assertRaises(TestAccessError):
            run_oracle_roi_image(ROOT / "external_test_ds/sample.png", ROOT / "external_test_ds/mask.png", model, torch.device("cpu"))


if __name__ == "__main__":
    unittest.main()
