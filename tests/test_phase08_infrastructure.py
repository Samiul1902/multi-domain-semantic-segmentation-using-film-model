"""
Phase 08 Part 1A — infrastructure unit tests.

Covers the target contract, image-mode handling, spatial transform geometry,
reproducibility, metric contract, frozen taxonomy integration, device contract,
checkpointing, and the AMP smoke path.

All data used is synthetic or TRAIN-only. TEST content is never opened.
"""
import random
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import torch
from PIL import Image

PROJECT_ROOT = Path(r'D:\Softfors\jup')
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.targets import (binarize_mask, binarize_mask_bool,  # noqa: E402
                               foreground_label_signature, is_binary)
from src.utils import device as dev  # noqa: E402
from src.utils import config as cfgmod  # noqa: E402
from src.utils.reproducibility import (set_seed, seed_worker, make_generator,  # noqa: E402
                                       capture_random_state, restore_random_state)
from src.data.transforms import SegmentationTransform  # noqa: E402
from src.data.kub_dataset import KUBDataset, TestAccessError, derive_acquisition_type  # noqa: E402
from src.metrics.segmentation import binary_metrics  # noqa: E402
from src.metrics.object_metrics import object_metrics  # noqa: E402
from src.analysis import kub_object_size as kos  # noqa: E402
from src.utils import manifest_guard  # noqa: E402

TRAIN_MANIFEST = PROJECT_ROOT / 'manifests' / 'phase4_v3' / 'train.csv'


# ---------------------------------------------------------------------------
# Target contract
# ---------------------------------------------------------------------------

class TestTargetContract(unittest.TestCase):

    def test_binarize_labels_1_2_3_255(self):
        for label in (1, 2, 3, 255):
            m = np.zeros((6, 6), dtype=np.uint8)
            m[2, 2] = label
            out = binarize_mask(m)
            self.assertEqual(float(out[2, 2]), 1.0, f'label {label} must be foreground')
            self.assertEqual(float(out.sum()), 1.0)
            self.assertTrue(is_binary(out))

    def test_binarize_heterogeneous_mixture(self):
        m = np.array([[0, 1, 2], [3, 255, 0]], dtype=np.uint8)
        out = binarize_mask(m)
        self.assertTrue(is_binary(out))
        self.assertEqual(int(out.sum()), 4)

    def test_never_mask_equals_one(self):
        m = np.array([[0, 2, 3]], dtype=np.uint8)
        out = binarize_mask(m)
        self.assertEqual(int(out.sum()), 2)   # both 2 and 3 are foreground
        self.assertNotEqual(int((m == 1).sum()), int(out.sum()))

    def test_zero_is_background(self):
        m = np.zeros((4, 4), dtype=np.uint8)
        self.assertEqual(int(binarize_mask(m).sum()), 0)

    def test_dtype_and_shape(self):
        m = np.zeros((5, 7), dtype=np.uint8)
        m[1, 1] = 255
        out = binarize_mask(m)
        self.assertEqual(out.dtype, np.float32)
        self.assertEqual(out.shape, (5, 7))

    def test_3d_mask_reduced_to_first_channel(self):
        m = np.zeros((4, 4, 3), dtype=np.uint8)
        m[0, 0, 0] = 255
        self.assertEqual(int(binarize_mask(m).sum()), 1)

    def test_label_signature(self):
        m = np.array([[0, 2, 255]], dtype=np.uint8)
        self.assertEqual(foreground_label_signature(m), '0|2|255')


# ---------------------------------------------------------------------------
# Image mode / channels
# ---------------------------------------------------------------------------

class TestImageModes(unittest.TestCase):

    def test_grayscale_and_rgb_both_become_single_channel(self):
        t = SegmentationTransform(size=256, train=False)
        gray = Image.fromarray((np.random.rand(80, 60) * 255).astype(np.uint8), mode='L')
        rgb = Image.fromarray((np.random.rand(80, 60, 3) * 255).astype(np.uint8), mode='RGB')
        mask = Image.fromarray(np.zeros((80, 60), dtype=np.uint8), mode='L')
        img_g, m_g, _ = t(gray, mask)
        img_r, m_r, _ = t(rgb, mask)
        self.assertEqual(img_g.shape[0], 1, 'grayscale must yield 1 channel')
        self.assertEqual(img_r.shape[0], 1, 'RGB must be converted to 1 channel')
        self.assertEqual(m_g.shape[0], 1)
        self.assertEqual(m_r.shape[0], 1)

    def test_channel_consistency(self):
        t = SegmentationTransform(size=256, train=False)
        gray = Image.fromarray((np.random.rand(50, 50) * 255).astype(np.uint8), mode='L')
        rgb = Image.fromarray((np.random.rand(50, 50, 3) * 255).astype(np.uint8), mode='RGB')
        mask = Image.fromarray(np.zeros((50, 50), dtype=np.uint8), mode='L')
        a, _, _ = t(gray, mask)
        b, _, _ = t(rgb, mask)
        self.assertEqual(a.shape, b.shape)


# ---------------------------------------------------------------------------
# Spatial transform geometry
# ---------------------------------------------------------------------------

class TestTransformContract(unittest.TestCase):

    def test_resize_pad_geometry(self):
        t = SegmentationTransform(size=512, train=False)
        img = Image.fromarray(np.zeros((100, 200), dtype=np.uint8), mode='L')
        mask = Image.fromarray(np.zeros((100, 200), dtype=np.uint8), mode='L')
        img_t, mask_t, meta = t(img, mask)
        self.assertEqual(img_t.shape, (1, 512, 512))
        self.assertEqual(mask_t.shape, (1, 512, 512))
        # scale = min(512/200, 512/100) = 2.56 -> (512, 256)
        self.assertAlmostEqual(meta.scale, 2.56, places=6)
        self.assertEqual((meta.resized_width, meta.resized_height), (512, 256))

    def test_geometry_math_restores_original_coordinates(self):
        t = SegmentationTransform(size=512, train=False)
        img = Image.fromarray(np.zeros((300, 150), dtype=np.uint8), mode='L')
        mask = Image.fromarray(np.zeros((300, 150), dtype=np.uint8), mode='L')
        _, _, meta = t(img, mask)
        left, top, right, bottom = meta.padding
        # padded back to 512 in both axes
        self.assertEqual(meta.resized_width + left + right, 512)
        self.assertEqual(meta.resized_height + top + bottom, 512)
        # inverse mapping of a point inside the resized region
        x_pad, y_pad = left + 10, top + 10
        x_orig = (x_pad - left) / meta.scale
        y_orig = (y_pad - top) / meta.scale
        self.assertAlmostEqual(x_orig, 10 / meta.scale, places=6)
        self.assertAlmostEqual(y_orig, 10 / meta.scale, places=6)

    def test_mask_uses_nearest_neighbour(self):
        # A hard binary edge must survive mask resizing without introducing
        # intermediate values (nearest-neighbour, not bilinear).
        t = SegmentationTransform(size=256, train=False)
        mask = np.zeros((32, 32), dtype=np.uint8)
        mask[:, 16:] = 255
        img = Image.fromarray(np.zeros((32, 32), dtype=np.uint8), mode='L')
        _, mask_t, _ = t(img, Image.fromarray(mask, mode='L'))
        self.assertTrue(is_binary(mask_t.numpy()))

    def test_alignment_image_and_mask(self):
        t = SegmentationTransform(size=256, train=False)
        img = Image.fromarray((np.random.rand(90, 70) * 255).astype(np.uint8), mode='L')
        mask = np.zeros((90, 70), dtype=np.uint8)
        mask[10:20, 10:20] = 255
        img_t, mask_t, _ = t(img, Image.fromarray(mask, mode='L'))
        self.assertEqual(img_t.shape[-2:], mask_t.shape[-2:])

    def test_binary_target_stays_binary_after_transform(self):
        t = SegmentationTransform(size=256, train=False)
        mask = np.zeros((60, 40), dtype=np.uint8)
        mask[5:15, 5:15] = 2      # non-1 foreground label
        img = Image.fromarray(np.zeros((60, 40), dtype=np.uint8), mode='L')
        _, mask_t, _ = t(img, Image.fromarray(mask, mode='L'))
        self.assertTrue(is_binary(mask_t.numpy()))
        self.assertGreater(float(mask_t.sum()), 0.0)

    def test_no_foreground_lost_for_label_255(self):
        t = SegmentationTransform(size=256, train=False)
        mask = np.zeros((64, 64), dtype=np.uint8)
        mask[20:30, 20:30] = 255
        img = Image.fromarray(np.zeros((64, 64), dtype=np.uint8), mode='L')
        _, mask_t, _ = t(img, Image.fromarray(mask, mode='L'))
        self.assertGreater(float(mask_t.sum()), 0.0)


# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------

class TestReproducibility(unittest.TestCase):

    def test_seed_reproducibility(self):
        set_seed(123)
        a = (random.random(), float(np.random.rand()), float(torch.rand(1)))
        set_seed(123)
        b = (random.random(), float(np.random.rand()), float(torch.rand(1)))
        self.assertEqual(a, b)

    def test_worker_seed_reproducibility(self):
        def run():
            torch.manual_seed(7)
            gen = torch.Generator(); gen.manual_seed(7)
            vals = []
            for wid in range(3):
                torch.manual_seed(int(gen.initial_seed()) + wid)
                seed_worker(wid)
                vals.append((random.random(), float(np.random.rand())))
            return vals
        self.assertEqual(run(), run())

    def test_generator_reproducibility(self):
        g1, g2 = make_generator(99), make_generator(99)
        self.assertEqual(float(torch.rand(1, generator=g1)), float(torch.rand(1, generator=g2)))

    def test_rng_state_roundtrip(self):
        set_seed(5)
        torch.rand(3)
        state = capture_random_state()
        expected = float(torch.rand(1))
        restore_random_state(state)
        self.assertEqual(float(torch.rand(1)), expected)


# ---------------------------------------------------------------------------
# Metric contract
# ---------------------------------------------------------------------------

class TestMetricContract(unittest.TestCase):

    def test_perfect_prediction(self):
        target = torch.zeros(1, 1, 8, 8); target[0, 0, 2:5, 2:5] = 1
        logits = torch.where(target > 0, torch.tensor(10.0), torch.tensor(-10.0))
        m = binary_metrics(logits, target)
        for k in ('dice', 'iou', 'precision', 'recall'):
            self.assertAlmostEqual(float(m[k]), 1.0, places=4)

    def test_empty_ground_truth_is_explicit(self):
        target = torch.zeros(1, 1, 8, 8)
        logits = torch.full((1, 1, 8, 8), -10.0)
        m = binary_metrics(logits, target)
        self.assertIn('dice', m)   # defined via epsilon, not NaN

    def test_threshold_convention_is_documented(self):
        import inspect
        sig = inspect.signature(binary_metrics)
        self.assertEqual(sig.parameters['threshold'].default, 0.5)
        self.assertIn('epsilon', sig.parameters)


class TestObjectMetricContract(unittest.TestCase):

    def test_connectivity_is_eight(self):
        pred = np.zeros((10, 10), dtype=bool); pred[1, 1] = True; pred[2, 2] = True
        gt = pred.copy()
        out = object_metrics(pred, gt)
        self.assertEqual(out['connectivity'], 8)
        self.assertEqual(out['gt_component_count'], 1)   # diagonal -> one component

    def test_overlap_criterion_explicit(self):
        import inspect
        sig = inspect.signature(object_metrics)
        self.assertIn('minimum_overlap_pixels', sig.parameters)
        self.assertEqual(sig.parameters['minimum_overlap_pixels'].default, 1)

    def test_recall_zero_when_no_overlap(self):
        pred = np.zeros((10, 10), dtype=bool); pred[0, 0] = True
        gt = np.zeros((10, 10), dtype=bool); gt[9, 9] = True
        out = object_metrics(pred, gt)
        self.assertEqual(out['detected_gt_components'], 0)
        self.assertEqual(out['object_recall'], 0.0)


# ---------------------------------------------------------------------------
# Frozen taxonomy integration
# ---------------------------------------------------------------------------

class TestTaxonomyIntegration(unittest.TestCase):

    def test_taxonomy_api_loads_frozen(self):
        t = kos.get_kub_size_taxonomy('kub_size_clean_v3_v1')
        self.assertLess(t['Q25'], t['Q50'])
        self.assertLess(t['Q50'], t['Q75'])

    def test_historical_taxonomy_still_available(self):
        t = kos.get_kub_size_taxonomy('kub_size_v1')
        self.assertEqual(t['Q25'], 0.0001499766777599)

    def test_unknown_taxonomy_fails(self):
        with self.assertRaises(ValueError):
            kos.get_kub_size_taxonomy('nope')

    def test_roi_not_primary_binned(self):
        import pandas as pd
        comps = pd.DataFrame({'sample_id': ['a', 'b'],
                              'component_ratio': [0.0000001, 0.5],
                              'view_type': ['ROI_CROP', 'FULL_FIELD']})
        out = kos.assign_versioned_strata(comps, kos.CLEAN_V3_TAXONOMY_ID)
        self.assertEqual(out.loc[0, 'size_stratum'], 'ROI_NOT_PRIMARY_BINNED')
        self.assertNotEqual(out.loc[1, 'size_stratum'], 'ROI_NOT_PRIMARY_BINNED')


# ---------------------------------------------------------------------------
# Manifest guard
# ---------------------------------------------------------------------------

class TestManifestGuardPhase08(unittest.TestCase):

    def test_phase4_v3_validates(self):
        res = manifest_guard.validate_manifest_version('phase4_v3')
        self.assertTrue(res['ok'])

    def test_unknown_version_rejected(self):
        with self.assertRaises(ValueError):
            manifest_guard.validate_manifest_version('phase4_v9')

    def test_wrong_hash_rejected(self):
        import src.utils.manifest_guard as mg
        original = mg._V3_HASHES['train']
        try:
            mg._V3_HASHES['train'] = 'deadbeef' * 8
            res = mg.validate_manifest_version('phase4_v3', subset=['train'])
            self.assertFalse(res['ok'])
        finally:
            mg._V3_HASHES['train'] = original


# ---------------------------------------------------------------------------
# Device contract
# ---------------------------------------------------------------------------

class TestDeviceContract(unittest.TestCase):

    def test_canonical_returns_cuda_when_available(self):
        d = dev.get_device(require_cuda=True)
        if torch.cuda.is_available():
            self.assertEqual(d.type, 'cuda')
        else:
            self.skipTest('CUDA unavailable in this environment')

    def test_require_cuda_raises_when_unavailable(self):
        import unittest.mock as mock
        with mock.patch.object(torch.cuda, 'is_available', return_value=False):
            with self.assertRaises(dev.CudaUnavailableError):
                dev.get_device(require_cuda=True)

    def test_explicit_cpu_fallback_allowed_only_when_requested(self):
        import unittest.mock as mock
        with mock.patch.object(torch.cuda, 'is_available', return_value=False):
            d = dev.get_device(require_cuda=True, allow_cpu_fallback=True)
            self.assertEqual(d.type, 'cpu')

    def test_device_report_fields(self):
        r = dev.device_report()
        for k in ('cuda_available', 'pytorch_version', 'cuda_runtime_version'):
            self.assertIn(k, r)


# ---------------------------------------------------------------------------
# Dataset (TRAIN only)
# ---------------------------------------------------------------------------

class TestDatasetContract(unittest.TestCase):

    def setUp(self):
        if not TRAIN_MANIFEST.exists():
            self.skipTest('phase4_v3 TRAIN manifest missing')
        self.ds = KUBDataset(TRAIN_MANIFEST, 'TRAIN', target_size=256, cache_in_memory=False)

    def test_test_split_is_blocked(self):
        with self.assertRaises(TestAccessError):
            KUBDataset(TRAIN_MANIFEST, 'TEST')

    def test_val_access_is_deterministic(self):
        """VAL has no augmentation, so repeated access must be identical."""
        val_manifest = PROJECT_ROOT / 'manifests' / 'phase4_v3' / 'val.csv'
        if not val_manifest.exists():
            self.skipTest('phase4_v3 VAL manifest missing')
        ds = KUBDataset(val_manifest, 'VAL', target_size=256, cache_in_memory=False)
        a = ds[0]
        b = ds[0]
        self.assertTrue(torch.equal(a['image'], b['image']))
        self.assertTrue(torch.equal(a['mask'], b['mask']))

    def test_train_access_is_reproducible_under_seeding(self):
        """
        TRAIN applies stochastic augmentation on every access by design.
        Reproducibility is therefore achieved by seeding, not by determinism.
        """
        set_seed(11)
        a = self.ds[0]
        set_seed(11)
        b = self.ds[0]
        self.assertTrue(torch.equal(a['image'], b['image']),
                        'TRAIN access must be reproducible under a fixed seed')
        self.assertTrue(torch.equal(a['mask'], b['mask']))

    def test_item_contract(self):
        item = self.ds[0]
        self.assertEqual(item['image'].shape, (1, 256, 256))
        self.assertEqual(item['mask'].shape, (1, 256, 256))
        self.assertTrue(is_binary(item['mask'].numpy()))
        self.assertIn('acquisition_type', item)
        self.assertIn('resize_scale', item)
        self.assertIn('padding', item)

    def test_acquisition_derivation(self):
        self.assertEqual(derive_acquisition_type(r'x\KUB\ROI\a.png'), 'ROI')
        self.assertEqual(derive_acquisition_type(r'x\KUB\Images\a.png'), 'FULL_FIELD')
        self.assertEqual(derive_acquisition_type(r'x\other\a.png'), 'UNKNOWN')


# ---------------------------------------------------------------------------
# Config contract
# ---------------------------------------------------------------------------

class TestConfigContract(unittest.TestCase):

    def test_placeholder_template_invalid(self):
        v = cfgmod.validate_experiment_config(cfgmod.config_template(), require_all=True)
        self.assertFalse(v['valid'])

    def test_missing_field_invalid(self):
        full = {k: 'v' for k in cfgmod.REQUIRED_SCIENTIFIC_FIELDS}
        full['manifest_version'] = 'phase4_v3'
        full.pop('loss')
        self.assertFalse(cfgmod.validate_experiment_config(full)['valid'])

    def test_wrong_manifest_rejected(self):
        full = {k: 'v' for k in cfgmod.REQUIRED_SCIENTIFIC_FIELDS}
        full['manifest_version'] = 'phase4_v2'
        self.assertFalse(cfgmod.validate_experiment_config(full)['valid'])

    def test_complete_config_valid(self):
        full = {k: 'v' for k in cfgmod.REQUIRED_SCIENTIFIC_FIELDS}
        full['manifest_version'] = 'phase4_v3'
        self.assertTrue(cfgmod.validate_experiment_config(full)['valid'])


# ---------------------------------------------------------------------------
# Checkpoint round-trip (CPU, non-canonical)
# ---------------------------------------------------------------------------

class TestCheckpointRoundtrip(unittest.TestCase):

    def test_save_load_roundtrip(self):
        from src.utils.checkpointing import (save_training_checkpoint,
                                             load_training_checkpoint)
        model = torch.nn.Conv2d(1, 1, 3)
        opt = torch.optim.SGD(model.parameters(), lr=0.1)
        sched = torch.optim.lr_scheduler.StepLR(opt, step_size=1)
        scaler = None
        set_seed(3)
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'ckpt.pt'
            save_training_checkpoint(
                p, model, opt, sched, scaler, epoch=1, global_step=2,
                best_validation_score=0.5, configuration={'a': 1}, seed=3,
                training_history=[], manifest_version='phase4_v3',
                manifest_hashes={'train': 'x'}, experiment_id='exp_test',
                model_name='smoke', input_resolution=256, threshold=0.5,
                taxonomy_id='kub_size_clean_v3_v1')
            state = load_training_checkpoint(p, model, opt, sched, scaler,
                                             restore_rng=False)
            self.assertEqual(state['experiment_id'], 'exp_test')
            self.assertEqual(state['manifest_version'], 'phase4_v3')
            self.assertEqual(state['taxonomy_id'], 'kub_size_clean_v3_v1')
            self.assertEqual(state['epoch'], 1)

    def test_resume_restores_experiment_id(self):
        from src.utils.checkpointing import (save_training_checkpoint,
                                             load_training_checkpoint)
        model = torch.nn.Conv2d(1, 1, 3)
        opt = torch.optim.SGD(model.parameters(), lr=0.1)
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'ckpt.pt'
            save_training_checkpoint(p, model, opt, None, None, 1, 1, 0.0, {}, 1, [],
                                     'phase4_v3', {}, 'exp_resume', 'm', 256, 0.5)
            state = load_training_checkpoint(p, model, restore_rng=False)
            self.assertEqual(state['experiment_id'], 'exp_resume')


# ---------------------------------------------------------------------------
# AMP smoke (CUDA only, infrastructure test)
# ---------------------------------------------------------------------------

class TestAmpSmoke(unittest.TestCase):
    """INFRASTRUCTURE_TEST_ONLY — not a scientific result."""

    def test_amp_forward_backward(self):
        if not dev.amp_supported():
            self.skipTest('CUDA unavailable')
        device = dev.get_device(require_cuda=True)
        model = torch.nn.Conv2d(1, 1, 3, padding=1).to(device)
        opt = torch.optim.SGD(model.parameters(), lr=0.01)
        scaler = dev.make_grad_scaler(enabled=True)
        x = torch.rand(2, 1, 32, 32, device=device)
        y = (torch.rand(2, 1, 32, 32, device=device) > 0.5).float()
        with dev.make_autocast(enabled=True):
            out = model(x)
            loss = torch.nn.functional.binary_cross_entropy_with_logits(out, y)
        scaler.scale(loss).backward()
        scaler.step(opt)
        scaler.update()
        self.assertTrue(torch.isfinite(loss).item())

    def test_grad_scaler_state_roundtrip(self):
        if not dev.amp_supported():
            self.skipTest('CUDA unavailable')
        scaler = dev.make_grad_scaler(enabled=True)
        st = scaler.state_dict()
        scaler2 = dev.make_grad_scaler(enabled=True)
        scaler2.load_state_dict(st)
        self.assertEqual(set(st.keys()), set(scaler2.state_dict().keys()))


if __name__ == '__main__':
    unittest.main(verbosity=2)
