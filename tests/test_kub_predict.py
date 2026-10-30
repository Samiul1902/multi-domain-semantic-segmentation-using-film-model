import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from PIL import Image

from src.data.kub_dataset import TestAccessError
from src.inference.kub_predict import predict_kub, show_kub_prediction
from src.inference.predict import predict

ROOT = Path(__file__).resolve().parents[1]


class TestKUBPredict(unittest.TestCase):
    def setUp(self):
        val_df = pd.read_csv(ROOT / "manifests/val.csv")
        kub_val = val_df[val_df["dataset"] == "KUB"]
        self.sample_image_path = Path(kub_val.iloc[0]["image_path"])
        self.checkpoint_path = ROOT / "checkpoints/phase10_kub_unetpp_seed42_512/best.pt"

    def test_predict_kub_basic_and_restoration(self):
        result = predict_kub(
            image_path=self.sample_image_path,
            model_name="unetpp",
            checkpoint_path=self.checkpoint_path,
            threshold=0.5,
            device="cpu",
        )
        self.assertEqual(result["domain"], "KUB")
        self.assertEqual(result["task_id"], 3)
        self.assertEqual(result["threshold"], 0.5)
        self.assertEqual(result["probability_512"].shape, (512, 512))
        self.assertEqual(result["mask_512"].shape, (512, 512))

        orig_h, orig_w = result["original_shape"]
        self.assertEqual(result["probability_original"].shape, (orig_h, orig_w))
        self.assertEqual(result["mask_original"].shape, (orig_h, orig_w))
        self.assertEqual(result["overlay_original"].shape, (orig_h, orig_w, 3))

        self.assertTrue(np.isin(result["mask_512"], [0, 1]).all())
        self.assertTrue(np.isin(result["mask_original"], [0, 1]).all())

    def test_save_dir_output(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            result = predict_kub(
                image_path=self.sample_image_path,
                model_name="unetpp",
                checkpoint_path=self.checkpoint_path,
                threshold=0.5,
                device="cpu",
                save_dir=tmp_dir,
            )
            stem = self.sample_image_path.stem
            tmp_path = Path(tmp_dir)
            self.assertTrue((tmp_path / f"{stem}_probability.png").exists())
            self.assertTrue((tmp_path / f"{stem}_mask.png").exists())
            self.assertTrue((tmp_path / f"{stem}_overlay.png").exists())
            self.assertTrue((tmp_path / f"{stem}_prediction.json").exists())

    def test_show_kub_prediction(self):
        result = predict_kub(
            image_path=self.sample_image_path,
            model_name="unetpp",
            checkpoint_path=self.checkpoint_path,
            threshold=0.5,
            device="cpu",
        )
        fig, axes = show_kub_prediction(result)
        self.assertEqual(len(axes), 4)
        import matplotlib.pyplot as plt
        plt.close(fig)

    def test_missing_file_handling(self):
        with self.assertRaises(FileNotFoundError):
            predict_kub("non_existent_file_path_12345.png")

    def test_test_rejection_manifest_and_external(self):
        test_df = pd.read_csv(ROOT / "manifests/test.csv")
        test_image_path = test_df.iloc[0]["image_path"]
        with self.assertRaises(TestAccessError):
            predict_kub(test_image_path, checkpoint_path=self.checkpoint_path)

        with self.assertRaises(TestAccessError):
            predict_kub(ROOT / "external_test_ds/sample.png", checkpoint_path=self.checkpoint_path)

    def test_generic_predict_interface(self):
        # task="auto" raises NotImplementedError
        with self.assertRaises(NotImplementedError):
            predict(self.sample_image_path, task="auto")

        # task="ISIC" raises NotImplementedError
        with self.assertRaises(NotImplementedError):
            predict(self.sample_image_path, task="ISIC")

        # task="invalid" raises ValueError
        with self.assertRaises(ValueError):
            predict(self.sample_image_path, task="invalid_task_xyz")

        # task="KUB" delegates to predict_kub and succeeds
        res = predict(
            self.sample_image_path,
            task="KUB",
            model_name="unetpp",
            checkpoint_path=self.checkpoint_path,
            device="cpu",
        )
        self.assertEqual(res["domain"], "KUB")


if __name__ == "__main__":
    unittest.main()
