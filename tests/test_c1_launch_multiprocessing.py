"""C1 recovery under the real production worker topology (train 4 / eval 2).

Synthetic images and artificial metadata only. No real research images are read.

These are CPU tests, so exact equality is required and asserted. The CUDA path is
knowingly nondeterministic in backward kernels (measured max |delta| 2.82e-4 on
the model in the earlier readiness assessment); no bitwise CUDA claim is made
here or anywhere else.
"""
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import torch

from src.research.c1_film.integration_contract import make_contract
from src.research.c1_film.recovery_store import EpochStore, RecoveryError
from src.research.c1_film.synthetic_fixture import (
    ArtificialDataset, fixture_loaders, fixture_loaders_workers,
)
from src.research.c1_film.training_engine import Trainer
from src.research.c1_film_launch.launch_gate import expected_run_plan, run_identity

TRAIN_WORKERS = 4
EVAL_WORKERS = 2


def _fingerprint(loader) -> str:
    digest = hashlib.sha256()
    for batch in loader:
        digest.update(batch["image"].contiguous().numpy().tobytes())
        digest.update("|".join(batch["sample_id"]).encode())
        digest.update(batch["task_id"].to(torch.int64).numpy().tobytes())
    return digest.hexdigest()


class WorkerTopologyTests(unittest.TestCase):
    def test_production_topology_matches_protocol(self):
        train, val = fixture_loaders_workers(42, 1)
        self.assertEqual(train.num_workers, TRAIN_WORKERS)
        self.assertEqual(val.num_workers, EVAL_WORKERS)
        self.assertFalse(train.persistent_workers)
        self.assertFalse(val.persistent_workers)

    def test_worker_spawn_and_dataset_pickling(self):
        """Iterating proves the dataset pickled into 4 spawned worker processes."""
        train, val = fixture_loaders_workers(42, 1)
        train_batches = list(train)
        val_batches = list(val)
        self.assertEqual(len(train_batches), 2)
        self.assertEqual(len(val_batches), 2)
        seen = []
        for batch in train_batches:
            self.assertEqual(tuple(batch["image"].shape[1:]), (3, 32, 32))
            self.assertEqual(len(batch["sample_id"]), batch["image"].shape[0])
            seen.extend(batch["sample_id"])
        # WeightedRandomSampler samples with replacement: 8 draws from 8 items.
        self.assertEqual(len(seen), 8)
        self.assertTrue(all(sid.startswith("artificial-TRAIN-") for sid in seen))
        self.assertIsInstance(ArtificialDataset("TRAIN"), ArtificialDataset)

    def test_deterministic_worker_seeding(self):
        """Identical (seed, epoch) must reproduce identical worker output."""
        first = _fingerprint(fixture_loaders_workers(42, 1)[0])
        second = _fingerprint(fixture_loaders_workers(42, 1)[0])
        self.assertEqual(first, second)

    def test_epoch_derived_sampling_is_stable_and_epoch_specific(self):
        epoch_one_a = _fingerprint(fixture_loaders_workers(42, 1)[0])
        epoch_one_b = _fingerprint(fixture_loaders_workers(42, 1)[0])
        epoch_two = _fingerprint(fixture_loaders_workers(42, 2)[0])
        self.assertEqual(epoch_one_a, epoch_one_b)
        self.assertNotEqual(epoch_one_a, epoch_two)

    def test_worker_count_preserves_sampling_but_changes_augmentation_rng(self):
        """Documented boundary: sampling is worker-invariant, augmentation is not.

        The domain-balanced sampler owns its own generator, so the drawn sample_id
        sequence is identical whether the loader runs with 0 or 4 workers. The
        synthetic TRAIN augmentation, however, draws from ``random``/``numpy``
        seeded per worker by ``seed_worker``, so pixel values differ with worker
        count (measured max |delta| ~0.12 on this fixture).

        This is a property of the *fixture's* augmentation, not a recovery defect:
        resume at a fixed worker count is bit-exact (verified above), and the
        frozen protocol pins train_workers=4, so production always uses the
        worker-local stream.
        """
        single_batches = list(fixture_loaders(42, 1)[0])
        multi_batches = list(fixture_loaders_workers(42, 1)[0])

        single_ids = [sid for batch in single_batches for sid in batch["sample_id"]]
        multi_ids = [sid for batch in multi_batches for sid in batch["sample_id"]]
        self.assertEqual(single_ids, multi_ids)

        single_pixels = torch.cat([batch["image"] for batch in single_batches])
        multi_pixels = torch.cat([batch["image"] for batch in multi_batches])
        self.assertEqual(single_pixels.shape, multi_pixels.shape)
        self.assertFalse(torch.equal(single_pixels, multi_pixels))

    def test_worker_count_is_reproducible_at_fixed_topology(self):
        """The property that actually matters: same topology, same stream."""
        first = _fingerprint(fixture_loaders_workers(42, 1)[0])
        second = _fingerprint(fixture_loaders_workers(42, 1)[0])
        self.assertEqual(first, second)


class WorkerRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old_threads = torch.get_num_threads()
        torch.set_num_threads(1)

    @classmethod
    def tearDownClass(cls):
        torch.set_num_threads(cls.old_threads)

    def _trainer(self, arm="C1-C", seed=42):
        return Trainer(make_contract(arm, seed, synthetic=True))

    def test_uninterrupted_equals_resumed_with_workers(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            reference = self._trainer()
            reference.run(Path(a), fixture_loaders_workers)

            split = self._trainer()
            split.run(Path(b), fixture_loaders_workers, until_epoch=1)

            resumed = self._trainer()
            resumed.run(Path(b), fixture_loaders_workers, resume=True)

            left, right = reference.model.state_dict(), resumed.model.state_dict()
            self.assertEqual(set(left), set(right))
            for key in left:
                self.assertTrue(torch.equal(left[key], right[key]), key)
            self.assertEqual(reference.history, resumed.history)
            self.assertEqual(reference.best_epoch, resumed.best_epoch)
            self.assertEqual(reference.best_macro, resumed.best_macro)
            self.assertEqual(
                json.loads((Path(b) / "lifecycle.json").read_text())["state"], "COMPLETE")

    def test_partial_checkpoint_transaction_recovers_with_workers(self):
        with tempfile.TemporaryDirectory() as reference_dir, \
                tempfile.TemporaryDirectory() as work:
            reference = self._trainer()
            reference.run(Path(reference_dir), fixture_loaders_workers)

            root = Path(work)
            first = self._trainer()
            first.run(root, fixture_loaders_workers, until_epoch=1)

            class SimulatedLoss(BaseException):
                pass

            def fault(stage):
                if stage == "before_pointer":
                    raise SimulatedLoss()

            attempt = self._trainer()
            with self.assertRaises(SimulatedLoss):
                attempt.run(root, fixture_loaders_workers, resume=True, fault=fault)
            self.assertEqual(
                json.loads((root / "lifecycle.json").read_text())["state"], "RUNNING")
            self.assertEqual(EpochStore(root).load(attempt.identity)["epoch"], 1)

            with self.assertRaisesRegex(RecoveryError, "REQUIRES_RESUME"):
                self._trainer().run(root, fixture_loaders_workers)

            finished = self._trainer()
            finished.run(root, fixture_loaders_workers, resume=True)
            for key, value in reference.model.state_dict().items():
                self.assertTrue(torch.equal(value, finished.model.state_dict()[key]), key)
            self.assertEqual(reference.history, finished.history)

    def test_treatment_and_control_identity_with_workers(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            treatment = self._trainer("C1-T")
            control = self._trainer("C1-C")
            self.assertEqual(treatment.initial_sha256, control.initial_sha256)
            self.assertNotEqual(treatment.identity, control.identity)

            treatment.run(Path(a), fixture_loaders_workers, until_epoch=1)
            control.run(Path(b), fixture_loaders_workers, until_epoch=1)
            self.assertEqual(len(treatment.history), 1)
            self.assertEqual(len(control.history), 1)
            # The control must remain an exact identity at every site after training.
            from src.research.c1_film.control import verify_identity_control
            verify_identity_control(control.model)

    def test_no_duplicate_logical_runs(self):
        digest = "a" * 64
        identities = [run_identity(digest, entry["arm"], entry["seed"])
                      for entry in expected_run_plan()]
        self.assertEqual(len(identities), 6)
        self.assertEqual(len(set(identities)), 6)

    def test_resume_refuses_switched_arm_with_workers(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._trainer("C1-C").run(root, fixture_loaders_workers, until_epoch=1)
            with self.assertRaisesRegex(RecoveryError, "IDENTITY"):
                self._trainer("C1-T").run(root, fixture_loaders_workers, resume=True)
            with self.assertRaisesRegex(RecoveryError, "IDENTITY"):
                self._trainer("C1-C", 123).run(root, fixture_loaders_workers, resume=True)

    def test_resume_refuses_corrupted_checkpoint_with_workers(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._trainer().run(root, fixture_loaders_workers, until_epoch=1)
            pointer = json.loads((root / "latest.json").read_text())
            (root / pointer["file"]).write_bytes(b"corrupted")
            with self.assertRaisesRegex(RecoveryError, "CORRUPTED"):
                self._trainer().run(root, fixture_loaders_workers, resume=True)

    def test_resume_refuses_tampered_protocol_identity_with_workers(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            trainer = self._trainer()
            trainer.run(root, fixture_loaders_workers, until_epoch=1)
            state = EpochStore(root).load(trainer.identity)
            state["contract"]["protocol_sha256"] = "0" * 64
            with self.assertRaisesRegex(RecoveryError, "CONTRACT"):
                self._trainer().restore(state)


if __name__ == "__main__":
    unittest.main()
