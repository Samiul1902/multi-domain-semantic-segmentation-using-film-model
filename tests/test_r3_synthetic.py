import numpy as np
import pandas as pd
from src.data.kub_localizer_dataset import KUBLocalizerDataset
import torch
from PIL import Image, ImageOps
import tempfile
from pathlib import Path
import unittest

class TestR3Synthetic(unittest.TestCase):
    def test_synthetic_component_mapping(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            w, h = 100, 200
            img = Image.new('L', (w, h), 0)
            mask = Image.new('L', (w, h), 0)
            mask.putpixel((10, 10), 255)
            mask.putpixel((50, 50), 255)
            mask.putpixel((52, 52), 255)
            mask.putpixel((0, 199), 255)
            img_path = td / 'img.png'
            mask_path = td / 'mask.png'
            img.save(img_path)
            mask.save(mask_path)
            df = pd.DataFrame([{'sample_id': 'synth', 'view_type': 'FULL_FIELD', 'image_path': str(img_path), 'mask_path': str(mask_path), 'width': w, 'height': h, 'patient_id': 'p1', 'category': 'KUB'}])
            ds = KUBLocalizerDataset(df, 'VAL', 512, 3)
            hm = ds[0]['heatmap']
            
            self.assertTrue(torch.equal(hm, ds[0]['heatmap']))
            
            def assert_peak(cx, cy):
                icx = max(0, min(511, int(round(cx))))
                icy = max(0, min(511, int(round(cy))))
                self.assertEqual(hm[0, icy, icx].item(), 1.0)
                
            assert_peak(153.6, 25.6)
            assert_peak(256.0, 128.0)
            assert_peak(261.12, 133.12)
            assert_peak(128.0, 509.44)
            
            self.assertTrue(0.9 < hm[0, 128, 257].item() < 0.99)

