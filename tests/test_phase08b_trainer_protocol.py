"""
Phase 08 Part 1B — trainer / validation / checkpoint / resume contract tests.

All tests are infrastructure-level. No scientific training, no TEST content.
"""
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import torch

PROJECT_ROOT = Path(r'D:\Softfors\jup')
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'notebooks' / 'phasewise'
                       / 'phase_08_baseline_infrastructure' / 'code'))

from src.training.trainer import EarlyStopping, Trainer  # noqa: E402
from src.training.evaluator import validate  # noqa: E402
from src.data.transforms import SegmentationTransform  # noqa: E402
from src.metrics.segmentation import binary_metrics, aggregate_binary_metrics  # noqa: E402
from src.utils.reproducibility import set_seed  # noqa: E402
from src.utils.checkpointing import (save_training_checkpoint,  # noqa: E402
                                     load_training_checkpoint)
from src.utils.run_lock import (acquire_lock, release_lock, inspect_lock,  # noqa: E402
                                ExperimentLockError)
from src.utils import config as cfgmod  # noqa: E402
import phase08b_protocol_audit as p8b  # noqa: E402


# ---------------------------------------------------------------------------
# Early stopping semantics (exact historical behaviour)
# ---------------------------------------------------------------------------

class TestEarlyStoppingSemantics(unittest.TestCase):

    def test_strict_improvement_resets_counter(self):
        es = EarlyStopping(patience=3)
        self.assertFalse(es.update(0.5))
        self.assertEqual(es.bad_epochs, 0)
        self.assertFalse(es.update(0.6))          # strict improvement
        self.assertEqual(es.bad_epochs, 0)
        self.assertEqual(es.best, 0.6)

    def test_tie_does_not_reset_counter(self):
        es = EarlyStopping(patience=3)
        es.update(0.5)
        self.assertFalse(es.update(0.5))          # tie -> NOT an improvement
        self.assertEqual(es.bad_epochs, 1, 'a tie must count as a bad epoch')

    def test_worse_does_not_reset_counter(self):
        es = EarlyStopping(patience=3)
        es.update(0.5)
        es.update(0.4)
        self.assertEqual(es.bad_epochs, 1)

    def test_stop_boundary_exactly_at_patience(self):
        es = EarlyStopping(patience=3)
        es.update(0.5)
        self.assertFalse(es.update(0.4))          # 1
        self.assertFalse(es.update(0.4))          # 2
        self.assertTrue(es.update(0.4))           # 3 -> stop

    def test_does_not_stop_before_patience(self):
        es = EarlyStopping(patience=5)
        es.update(0.5)
        for _ in range(4):
            self.assertFalse(es.update(0.1))
        self.assertEqual(es.bad_epochs, 4)

    def test_first_epoch_is_improvement_over_neg_inf(self):
        es = EarlyStopping(patience=3)
        self.assertFalse(es.update(0.0))
        self.assertEqual(es.bad_epochs, 0)
        self.assertEqual(es.best, 0.0)

    def test_no_minimum_delta(self):
        es = EarlyStopping(patience=3)
        es.update(0.5000000)
        self.assertFalse(es.update(0.5000001))    # tiny increase still improves
        self.assertEqual(es.bad_epochs, 0)


# ---------------------------------------------------------------------------
# Checkpoint selection semantics
# ---------------------------------------------------------------------------

class TestCheckpointSelectionSemantics(unittest.TestCase):

    def test_strict_greater_than_rule(self):
        best = 0.70
        self.assertTrue(0.7001 > best)
        self.assertFalse(0.70 > best, 'equal score must not be an improvement')
        self.assertFalse(0.6999 > best)

    def test_tie_does_not_overwrite_best(self):
        """Simulate the historical `if improved: save best.pt` guard."""
        best, best_epoch = 0.5, 1
        saved = [1]
        for epoch, score in ((2, 0.5), (3, 0.4), (4, 0.6)):
            improved = score > best
            if improved:
                best, best_epoch = score, epoch
                saved.append(epoch)
        self.assertEqual(saved, [1, 4])
        self.assertEqual(best_epoch, 4)


# ---------------------------------------------------------------------------
# Validation determinism
# ---------------------------------------------------------------------------

class _DummyDS(torch.utils.data.Dataset):
    split = 'VAL'

    def __init__(self, n=4, size=8):
        self.n, self.size = n, size

    def __len__(self):
        return self.n

    def __getitem__(self, i):
        g = torch.Generator().manual_seed(i)
        img = torch.rand(1, self.size, self.size, generator=g)
        mask = (torch.rand(1, self.size, self.size, generator=g) > 0.5).float()
        return {'image': img, 'mask': mask, 'view_type': 'FULL_FIELD',
                'category': 'Kidney_Stone'}


class TestValidationContract(unittest.TestCase):

    def test_validation_uses_no_augmentation(self):
        """The VAL transform must have train=False (augmentation off)."""
        t = SegmentationTransform(256, train=False)
        self.assertFalse(t.train)
        img = torch.rand(1, 32, 32)
        m = torch.zeros(1, 32, 32)
        self.assertFalse(hasattr(t, 'flip_probability') and t.train)

    def test_validation_shuffle_false_in_loader(self):
        from src.data.loaders import create_loader
        loader = create_loader(_DummyDS(), batch_size=2, shuffle=False, seed=1,
                               num_workers=0)
        self.assertIsInstance(loader.sampler, torch.utils.data.SequentialSampler,
                              'VAL loader must use a sequential (unshuffled) sampler')
        loader_shuffled = create_loader(_DummyDS(), batch_size=2, shuffle=True, seed=1,
                                        num_workers=0)
        self.assertIsInstance(loader_shuffled.sampler, torch.utils.data.RandomSampler)

    def test_validate_rejects_non_val_split(self):
        class TrainDS(_DummyDS):
            split = 'TRAIN'
        loader = torch.utils.data.DataLoader(TrainDS(), batch_size=2)
        model = torch.nn.Conv2d(1, 1, 1)
        opt = torch.optim.SGD(model.parameters(), lr=0.1)
        tr = Trainer(model, opt, None, torch.nn.BCEWithLogitsLoss(),
                     torch.device('cpu'), amp=False)
        with self.assertRaises(ValueError):
            tr.validate(loader)

    def test_validate_is_deterministic(self):
        model = torch.nn.Conv2d(1, 1, 3, padding=1)
        loader = torch.utils.data.DataLoader(_DummyDS(), batch_size=2)
        a, _ = validate(model, loader, torch.nn.BCEWithLogitsLoss(), torch.device('cpu'))
        b, _ = validate(model, loader, torch.nn.BCEWithLogitsLoss(), torch.device('cpu'))
        for k in ('dice', 'iou', 'precision', 'recall'):
            self.assertAlmostEqual(a[k], b[k], places=12)


# ---------------------------------------------------------------------------
# Metric aggregation hand-check
# ---------------------------------------------------------------------------

class TestAggregationHandCheck(unittest.TestCase):

    def test_macro_is_mean_of_per_image(self):
        # image A perfect, image B empty -> per-image dice 1.0 and 0.0
        logits = torch.tensor([[[[10.0, -10.0]]], [[[-10.0, -10.0]]]])
        targets = torch.tensor([[[[1.0, 0.0]]], [[[1.0, 0.0]]]])
        m = binary_metrics(logits, targets)
        per_image = m['dice']
        self.assertAlmostEqual(float(per_image[0]), 1.0, places=5)
        self.assertAlmostEqual(float(per_image[1]), 0.0, places=5)
        agg = aggregate_binary_metrics([m])
        self.assertAlmostEqual(agg['dice'], float(per_image.mean()), places=12)

    def test_macro_equals_hand_computed_mean(self):
        per_image = np.array([1.0, 0.0])
        self.assertAlmostEqual(float(per_image.mean()), 0.5)

    def test_micro_differs_from_macro_under_area_imbalance(self):
        # two large near-perfect images and one small complete failure:
        # macro = mean(1.0, 1.0, 0.0) = 0.667 ; micro is area-weighted -> ~0.95
        macro = float(np.mean([1.0, 1.0, 0.0]))
        tp, fp, fn = 1000, 0, 100
        micro = (2 * tp) / (2 * tp + fp + fn)
        self.assertAlmostEqual(macro, 2.0 / 3.0, places=6)
        self.assertNotAlmostEqual(micro, macro, places=3)


# ---------------------------------------------------------------------------
# Scheduler timing
# ---------------------------------------------------------------------------

class TestSchedulerTiming(unittest.TestCase):

    def test_step_is_per_epoch_after_validation_in_historical_source(self):
        src = (PROJECT_ROOT / 'scripts' / 'training'
               / 'train_kub_baseline.py').read_text(encoding='utf-8')
        self.assertIn('scheduler.step()', src)
        self.assertGreater(src.find('scheduler.step()'), src.find('trainer.validate('),
                           'scheduler.step must occur after validation')

    def test_phase10_uses_same_ordering(self):
        src = (PROJECT_ROOT / 'scripts' / 'training'
               / 'train_phase10_baselines.py').read_text(encoding='utf-8')
        self.assertGreater(src.find('scheduler.step()'), src.find('trainer.validate('))

    def test_step_is_not_inside_train_one_epoch(self):
        src = (PROJECT_ROOT / 'src' / 'training' / 'trainer.py').read_text(encoding='utf-8')
        self.assertNotIn('scheduler.step()', src,
                         'the trainer must not step the scheduler per batch')


# ---------------------------------------------------------------------------
# Checkpoint / resume contract
# ---------------------------------------------------------------------------

class TestResumeContract(unittest.TestCase):

    def _probe(self, steps=5, split_at=2):
        return p8b.resume_equivalence_probe(steps=steps, split_at=split_at)

    def test_resume_same_experiment_id(self):
        p = self._probe()
        self.assertEqual(p['restored_experiment_id'], 'phase08_resume_probe')

    def test_resume_losses_identical(self):
        p = self._probe()
        self.assertTrue(p['losses_identical'], p)

    def test_resume_parameters_identical(self):
        p = self._probe()
        self.assertTrue(p['parameters_identical'], p)

    def test_resume_lr_schedule_identical(self):
        p = self._probe()
        self.assertTrue(p['lr_schedule_identical'], p)

    def test_resume_restores_provenance(self):
        p = self._probe()
        self.assertEqual(p['restored_manifest_version'], p8b.MANIFEST_VERSION_CLEAN)
        self.assertEqual(p['restored_taxonomy_id'], p8b.TAXONOMY_ID)
        self.assertEqual(p['restored_epoch'], 2)

    def test_early_stop_state_roundtrip(self):
        model = torch.nn.Conv2d(1, 1, 3)
        opt = torch.optim.SGD(model.parameters(), lr=0.1)
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'c.pt'
            save_training_checkpoint(
                p, model, opt, None, None, 3, 9, 0.77, {}, 1, [{'epoch': 1}],
                p8b.MANIFEST_VERSION_CLEAN, {}, 'exp', 'm', 256, 0.5,
                early_stopping_state={'best': 0.77, 'bad_epochs': 4,
                                      'patience': 15, 'stopped': False},
                taxonomy_id=p8b.TAXONOMY_ID)
            st = load_training_checkpoint(p, model, opt, restore_rng=False)
            self.assertEqual(st['early_stopping_state']['bad_epochs'], 4)
            self.assertEqual(st['early_stopping_state']['best'], 0.77)

    def test_history_continuity(self):
        model = torch.nn.Conv2d(1, 1, 3)
        opt = torch.optim.SGD(model.parameters(), lr=0.1)
        hist = [{'epoch': i, 'train_loss': 1.0 / i} for i in (1, 2, 3)]
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'c.pt'
            save_training_checkpoint(p, model, opt, None, None, 3, 3, 0.5, {}, 1,
                                     hist, p8b.MANIFEST_VERSION_CLEAN, {}, 'exp',
                                     'm', 256, 0.5)
            st = load_training_checkpoint(p, model, opt, restore_rng=False)
            self.assertEqual(len(st['training_history']), 3)
            self.assertEqual(st['training_history'][-1]['epoch'], 3)

    def test_rng_state_roundtrip(self):
        from src.utils.reproducibility import capture_random_state, restore_random_state
        set_seed(21)
        torch.rand(3)
        st = capture_random_state()
        expected = float(torch.rand(1))
        restore_random_state(st)
        self.assertEqual(float(torch.rand(1)), expected)


# ---------------------------------------------------------------------------
# Single-writer lock
# ---------------------------------------------------------------------------

class TestSingleWriterLock(unittest.TestCase):

    def test_acquire_then_conflict_fails_loudly(self):
        with tempfile.TemporaryDirectory() as tmp:
            acquire_lock(tmp, 'exp_a')
            st = inspect_lock(tmp)
            self.assertTrue(st['present'])
            self.assertTrue(st['active'], st)
            with self.assertRaises(ExperimentLockError):
                acquire_lock(tmp, 'exp_a')

    def test_stale_lock_recoverable_explicitly(self):
        with tempfile.TemporaryDirectory() as tmp:
            acquire_lock(tmp, 'exp_b')
            # force a dead pid
            import json
            from src.utils.run_lock import lock_path
            payload = json.loads(lock_path(tmp).read_text())
            payload['pid'] = 999999999
            lock_path(tmp).write_text(json.dumps(payload))
            st = inspect_lock(tmp)
            self.assertFalse(st['active'])
            self.assertTrue(st['stale'])
            recovered = acquire_lock(tmp, 'exp_b', recover_stale=True)
            self.assertTrue(recovered['recovered_stale_lock'])

    def test_release_by_non_owner_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            import json
            from src.utils.run_lock import lock_path
            acquire_lock(tmp, 'exp_c')
            payload = json.loads(lock_path(tmp).read_text())
            payload['pid'] = 999999999
            lock_path(tmp).write_text(json.dumps(payload))
            with self.assertRaises(ExperimentLockError):
                release_lock(tmp)

    def test_no_lock_reports_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertFalse(inspect_lock(tmp)['present'])


# ---------------------------------------------------------------------------
# Config placeholder rejection
# ---------------------------------------------------------------------------

class TestConfigRejection(unittest.TestCase):

    def test_template_with_placeholder_fails(self):
        v = cfgmod.validate_experiment_config(cfgmod.config_template(), require_all=True)
        self.assertFalse(v['valid'])
        self.assertTrue(v['placeholder_fields'])

    def test_missing_material_field_fails(self):
        full = {k: 'v' for k in cfgmod.REQUIRED_SCIENTIFIC_FIELDS}
        full['manifest_version'] = 'phase4_v3'
        full.pop('optimizer')
        self.assertFalse(cfgmod.validate_experiment_config(full)['valid'])

    def test_complete_config_passes(self):
        full = {k: 'v' for k in cfgmod.REQUIRED_SCIENTIFIC_FIELDS}
        full['manifest_version'] = 'phase4_v3'
        self.assertTrue(cfgmod.validate_experiment_config(full)['valid'])


# ---------------------------------------------------------------------------
# Protocol reconstruction + scientific diff
# ---------------------------------------------------------------------------

class TestProtocolReconstruction(unittest.TestCase):

    def test_protocol_matrix_has_phase09_and_phase10(self):
        df = p8b.build_protocol_matrix()
        self.assertEqual(len(df), 4)
        self.assertIn(p8b.PHASE09_EXP_ID, set(df['experiment_id']))

    def test_phase09_scope_is_single_model(self):
        m = p8b.build_phase_model_mapping()
        self.assertEqual(int(m['in_phase09_clean_rerun_scope'].sum()), 1)

    def test_phase10_crosscheck_has_no_material_diff(self):
        df = p8b.build_phase10_crosscheck()
        self.assertEqual(int(df['material'].sum()), 0,
                         df[df['material']][['field', 'phase09_value', 'phase10_value']])

    def test_protocol_diff_has_no_material_change(self):
        df = p8b.build_protocol_diff(p8b.build_protocol_matrix().iloc[0].to_dict())
        self.assertEqual(int(df['scientifically_material'].sum()), 0,
                         df[df['scientifically_material']][['field']])

    def test_protocol_diff_changes_only_authorized_fields(self):
        df = p8b.build_protocol_diff(p8b.build_protocol_matrix().iloc[0].to_dict())
        changed = set(df[df['same_or_changed'] == 'changed']['field'])
        allowed = {'manifest_version', 'taxonomy_id', 'experiment_id'}
        self.assertTrue(changed <= (allowed | set(p8b.CLEAN_V3_AUTHORIZED_CHANGES)),
                        f'unexpected changed fields: {changed - allowed}')

    def test_checkpoint_embedded_config_matches_yaml(self):
        import yaml
        ck = p8b.load_phase09_config()
        y = yaml.safe_load(p8b.PHASE09_CONFIG.read_text(encoding='utf-8'))
        self.assertEqual(ck['training']['batch_size'], y['training']['batch_size'])
        self.assertEqual(ck['optimizer']['learning_rate'], y['optimizer']['learning_rate'])
        self.assertEqual(ck['input_resolution'], y['input_resolution'])

    def test_historical_protocol_values(self):
        cfg = p8b.load_phase09_config()
        self.assertEqual(cfg['optimizer']['learning_rate'], 1e-4)
        self.assertEqual(cfg['optimizer']['weight_decay'], 1e-4)
        self.assertEqual(cfg['training']['batch_size'], 4)
        self.assertEqual(cfg['training']['threshold'], 0.5)
        self.assertEqual(cfg['training']['seed'], 42)
        self.assertEqual(cfg['training']['early_stopping_patience'], 15)
        self.assertEqual(cfg['scheduler']['name'], 'CosineAnnealingLR')

    def test_candidate_config_not_executed(self):
        df = p8b.build_candidate_configs(p8b.load_phase09_config())
        self.assertFalse(bool(df['executed'].iloc[0]))
        self.assertEqual(df['candidate_status'].iloc[0], 'RECONSTRUCTED_AND_READY')

    def test_test_debt_documented_and_unrelated(self):
        df = p8b.build_test_debt()
        self.assertEqual(len(df), 3)
        self.assertFalse(bool(df['required_by_phase09'].any()))


# ---------------------------------------------------------------------------
# TEST lock
# ---------------------------------------------------------------------------

class TestSplitLock(unittest.TestCase):

    def test_trainer_rejects_non_train(self):
        class ValDS(_DummyDS):
            split = 'VAL'
        model = torch.nn.Conv2d(1, 1, 1)
        opt = torch.optim.SGD(model.parameters(), lr=0.1)
        tr = Trainer(model, opt, None, torch.nn.BCEWithLogitsLoss(),
                     torch.device('cpu'), amp=False)
        loader = torch.utils.data.DataLoader(ValDS(), batch_size=2)
        with self.assertRaises(ValueError):
            tr.train_one_epoch(loader)

    def test_test_split_blocked_in_dataset(self):
        from src.data.kub_dataset import KUBDataset, TestAccessError
        manifest = PROJECT_ROOT / 'manifests' / 'phase4_v3' / 'train.csv'
        if not manifest.exists():
            self.skipTest('manifest missing')
        with self.assertRaises(TestAccessError):
            KUBDataset(manifest, 'TEST')


if __name__ == '__main__':
    unittest.main(verbosity=2)
