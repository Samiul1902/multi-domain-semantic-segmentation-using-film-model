"""Synthetic-only C1 loop/recovery tests; no real manifests or prior checkpoints."""
import copy
import json
import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import torch

from src.research.c1_film.control import is_conditioning, verify_identity_control
from src.research.c1_film.integration_contract import make_contract, validate_contract
from src.research.c1_film.readiness import ReadinessError, load_protocol
from src.research.c1_film.recovery_store import EpochStore, RecoveryError, writer_lock
from src.research.c1_film.synthetic_fixture import fixture_loaders
from src.research.c1_film.train_driver import real_loader_factory, run_real, run_synthetic
from src.research.c1_film.training_engine import Trainer, capture_rng, restore_rng


def assert_nested_equal(test, a, b):
    if isinstance(a, torch.Tensor):
        test.assertTrue(torch.equal(a, b))
    elif isinstance(a, dict):
        test.assertEqual(set(a), set(b))
        for k in a:
            assert_nested_equal(test, a[k], b[k])
    elif isinstance(a, (list, tuple)):
        test.assertEqual(len(a), len(b))
        for x, y in zip(a, b):
            assert_nested_equal(test, x, y)
    else:
        test.assertEqual(a, b)


class TrainingIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old_threads = torch.get_num_threads()
        torch.set_num_threads(1)

    @classmethod
    def tearDownClass(cls):
        torch.set_num_threads(cls.old_threads)

    def contract(self, arm="C1-C", seed=42):
        return make_contract(arm, seed, synthetic=True)

    def test_initialization_and_optimization_for_both_arms(self):
        t = Trainer(self.contract("C1-T"))
        c = Trainer(self.contract("C1-C"))
        self.assertEqual(t.initial_sha256, c.initial_sha256)
        for trainer in (t, c):
            before = trainer.model.head.weight.detach().clone()
            conditioning = {n: p.detach().clone() for n, p in trainer.model.named_parameters()
                            if is_conditioning(n)}
            with tempfile.TemporaryDirectory() as d:
                trainer.run(Path(d), fixture_loaders, until_epoch=1)
                saved = EpochStore(Path(d)).load(trainer.identity)
                self.assertEqual(saved["epoch"], 1)
                self.assertTrue(saved["best_records"])
            self.assertFalse(torch.equal(before, trainer.model.head.weight))
            changed = [not torch.equal(conditioning[n], p) for n, p in trainer.model.named_parameters()
                       if is_conditioning(n)]
            if trainer.contract["arm"] == "C1-C":
                self.assertFalse(any(changed))
                verify_identity_control(trainer.model)
                self.assertTrue(all(p.grad is None for n, p in trainer.model.named_parameters()
                                    if is_conditioning(n)))
            else:
                self.assertTrue(any(changed))

    def test_resume_equals_uninterrupted_for_both_arms(self):
        for arm in ("C1-T", "C1-C"):
            with self.subTest(arm=arm), tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
                full = Trainer(self.contract(arm))
                full.run(Path(a), fixture_loaders)
                split = Trainer(self.contract(arm))
                split.run(Path(b), fixture_loaders, until_epoch=1)
                resumed = Trainer(self.contract(arm))
                resumed.run(Path(b), fixture_loaders, resume=True)
                x, y = full.state(), resumed.state()
                for key in ("model", "optimizer", "scheduler", "scaler", "history", "best_epoch",
                            "bad_epochs", "best_records", "best_model", "rng", "loader_states"):
                    assert_nested_equal(self, x[key], y[key])
                self.assertEqual(json.loads((Path(b) / "lifecycle.json").read_text())["state"], "COMPLETE")

    def test_rng_roundtrip_python_numpy_torch(self):
        random.seed(7)
        np.random.seed(7)
        torch.manual_seed(7)
        state = capture_rng()
        expected = (random.random(), np.random.random(), torch.rand(4))
        restore_rng(state)
        self.assertEqual(expected[0], random.random())
        self.assertEqual(expected[1], np.random.random())
        self.assertTrue(torch.equal(expected[2], torch.rand(4)))

    def test_contract_mutations_rejected(self):
        for field, value in (("arm", "C1-X"), ("seed", 99), ("protocol_sha256", "0" * 64)):
            c = self.contract()
            c[field] = value
            with self.subTest(field=field), self.assertRaises(ReadinessError):
                validate_contract(c)
        for field, value in (("resolution", 256), ("train_batch_size", 1), ("learning_rate", 0.01)):
            c = self.contract()
            c["recipe"][field] = value
            with self.assertRaises(ReadinessError):
                Trainer(c)

    def test_dataset_and_split_mutations_rejected(self):
        c = self.contract()
        c["dataset"]["populations"]["TRAIN"]["path"] = "manifests/phase4_v3/test.csv"
        with self.assertRaises(ReadinessError):
            Trainer(c)
        trainer = Trainer(self.contract())
        batch = next(iter(fixture_loaders(42, 1)[0]))
        batch["split"] = ["TEST"] * 4
        with self.assertRaisesRegex(RecoveryError, "SPLIT"):
            trainer.train_epoch([batch])

    def test_interruptions_before_and_after_commit_point(self):
        class SimulatedLoss(BaseException):
            pass
        with tempfile.TemporaryDirectory() as full_dir:
            reference = Trainer(self.contract())
            reference.run(Path(full_dir), fixture_loaders)
            for stage in ("before_payload", "after_payload", "before_pointer", "after_pointer"):
                with self.subTest(stage=stage), tempfile.TemporaryDirectory() as d:
                    root = Path(d)
                    first = Trainer(self.contract())
                    first.run(root, fixture_loaders, until_epoch=1)
                    def fault(current):
                        if current == stage:
                            raise SimulatedLoss()
                    attempt = Trainer(self.contract())
                    with self.assertRaises(SimulatedLoss):
                        attempt.run(root, fixture_loaders, resume=True, fault=fault)
                    self.assertEqual(json.loads((root / "lifecycle.json").read_text())["state"], "RUNNING")
                    stored = EpochStore(root).load(attempt.identity)
                    self.assertEqual(stored["epoch"], 2 if stage == "after_pointer" else 1)
                    with self.assertRaisesRegex(RecoveryError, "REQUIRES_RESUME"):
                        Trainer(self.contract()).run(root, fixture_loaders)
                    finished = Trainer(self.contract())
                    finished.run(root, fixture_loaders, resume=True)
                    assert_nested_equal(self, reference.model.state_dict(), finished.model.state_dict())
                    assert_nested_equal(self, reference.optimizer.state_dict(), finished.optimizer.state_dict())
                    self.assertEqual(reference.history, finished.history)

    def test_corruption_rejected_without_older_fallback(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            t = Trainer(self.contract())
            t.run(root, fixture_loaders, until_epoch=2)
            pointer = json.loads((root / "latest.json").read_text())
            (root / pointer["file"]).write_bytes(b"corrupted")
            with self.assertRaisesRegex(RecoveryError, "CORRUPTED"):
                Trainer(self.contract()).run(root, fixture_loaders, resume=True)

    def test_resume_cannot_switch_arm_seed_or_protocol(self):
        with tempfile.TemporaryDirectory() as d:
            t = Trainer(self.contract())
            t.run(Path(d), fixture_loaders, until_epoch=1)
            for arm, seed in (("C1-T", 42), ("C1-C", 123)):
                with self.assertRaisesRegex(RecoveryError, "IDENTITY"):
                    Trainer(self.contract(arm, seed)).run(Path(d), fixture_loaders, resume=True)
            state = EpochStore(Path(d)).load(t.identity)
            state["contract"]["protocol_sha256"] = "0" * 64
            with self.assertRaisesRegex(RecoveryError, "CONTRACT"):
                Trainer(self.contract()).restore(state)

    def test_selection_history_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            t = Trainer(self.contract())
            t.run(Path(d), fixture_loaders, until_epoch=1)
            state = EpochStore(Path(d)).load(t.identity)
            state["best_epoch"] = 99
            with self.assertRaisesRegex(RecoveryError, "SELECTION"):
                Trainer(self.contract()).restore(state)

    def test_resume_missing_and_pointer_escape_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            t = Trainer(self.contract())
            with self.assertRaises(RecoveryError):
                t.run(root, fixture_loaders, resume=True)
            pointer = {"file": "../outside.pt", "identity": t.identity, "sha256": "0" * 64}
            (root / "latest.json").write_text(json.dumps(pointer))
            with self.assertRaises(RecoveryError):
                EpochStore(root).load(t.identity)

    def test_exclusive_live_lock_never_reclaimed(self):
        with tempfile.TemporaryDirectory() as d:
            with writer_lock(Path(d)):
                for recover in (False, True):
                    with self.assertRaisesRegex(RecoveryError, "LOCK_CONFLICT"):
                        with writer_lock(Path(d), recover=recover):
                            self.fail("live writer lock was reclaimed")

    def test_real_launch_and_adapter_refused_before_readers(self):
        with patch("pathlib.Path.mkdir", side_effect=AssertionError("no output writes")):
            for fn in (lambda: run_real("C1-T", 42),
                       lambda: real_loader_factory(load_protocol()),
                       lambda: run_real("C1-C", 42, approval={"scope": "BARR-M1"})):
                with self.assertRaises(ReadinessError):
                    fn()
        with self.assertRaises(ReadinessError):
            Trainer(make_contract("C1-T", 42, synthetic=False, device="cuda"))

    def test_uncommitted_first_epoch_is_not_a_fresh_replicate(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            def fault(stage):
                if stage == "before_pointer":
                    raise RuntimeError("synthetic interruption")
            with self.assertRaises(RuntimeError):
                Trainer(self.contract()).run(root, fixture_loaders, fault=fault)
            with self.assertRaisesRegex(RecoveryError, "REQUIRES_RESUME"):
                Trainer(self.contract()).run(root, fixture_loaders)
            with self.assertRaisesRegex(RecoveryError, "UNREADABLE"):
                Trainer(self.contract()).run(root, fixture_loaders, resume=True)

    def test_interrupted_atomic_write_preserves_previous_pointer(self):
        from src.research.c1_film.recovery_store import atomic_bytes
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "pointer.json"
            atomic_bytes(p, b"original")
            with patch("src.research.c1_film.recovery_store.os.replace", side_effect=OSError("interrupted")):
                with self.assertRaises(OSError):
                    atomic_bytes(p, b"new")
            self.assertEqual(p.read_bytes(), b"original")
            self.assertFalse(list(Path(d).glob("*.tmp")))

    def test_history_trace_and_nonfinite_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            t = Trainer(self.contract())
            t.run(Path(d), fixture_loaders, until_epoch=1)
            state = EpochStore(Path(d)).load(t.identity)
            state["history"][0]["improved"] = False
            with self.assertRaisesRegex(RecoveryError, "TRACE"):
                Trainer(self.contract()).restore(state)
        trainer = Trainer(self.contract())
        batch = next(iter(fixture_loaders(42, 1)[0]))
        batch["image"][0, 0, 0, 0] = float("nan")
        with self.assertRaisesRegex(RecoveryError, "NONFINITE"):
            trainer.train_epoch([batch])

    def test_engine_refuses_repository_output_even_if_cli_bypassed(self):
        with self.assertRaisesRegex(ReadinessError, "TEMP_SUBDIRECTORY"):
            Trainer(self.contract()).run(Path(__file__).resolve().parents[1] / "experiments/bad", fixture_loaders)

    def test_mid_epoch_loss_replays_previous_committed_epoch(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            full = Trainer(self.contract())
            full.run(Path(a), fixture_loaders)
            first = Trainer(self.contract())
            first.run(Path(b), fixture_loaders, until_epoch=1)
            interrupted = Trainer(self.contract())
            original_step = interrupted.scaler.step
            def fail_after_update(optimizer):
                original_step(optimizer)
                raise RuntimeError("synthetic mid-epoch loss")
            with patch.object(interrupted.scaler, "step", side_effect=fail_after_update):
                with self.assertRaisesRegex(RuntimeError, "mid-epoch"):
                    interrupted.run(Path(b), fixture_loaders, resume=True)
            self.assertEqual(EpochStore(Path(b)).load(first.identity)["epoch"], 1)
            resumed = Trainer(self.contract())
            resumed.run(Path(b), fixture_loaders, resume=True)
            assert_nested_equal(self, full.model.state_dict(), resumed.model.state_dict())
            assert_nested_equal(self, full.optimizer.state_dict(), resumed.optimizer.state_dict())
            self.assertEqual(full.history, resumed.history)

    def test_dead_writer_requires_explicit_recovery_foreign_writer_refused(self):
        import socket
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            lock = root / "writer.lock"
            dead = {"pid": 99999999, "host": socket.gethostname(), "token": "synthetic-dead"}
            lock.write_text(json.dumps(dead))
            with patch("src.utils.run_lock._pid_alive", return_value=False):
                with self.assertRaisesRegex(RecoveryError, "LOCK_CONFLICT"):
                    with writer_lock(root):
                        self.fail("stale writer reclaimed without explicit permission")
                with writer_lock(root, recover=True):
                    self.assertNotEqual(json.loads(lock.read_text())["token"], dead["token"])
            dead["host"] = "synthetic-foreign-host"
            lock.write_text(json.dumps(dead))
            with self.assertRaisesRegex(RecoveryError, "LOCK_CONFLICT"):
                with writer_lock(root, recover=True):
                    self.fail("foreign writer reclaimed")

    def test_synthetic_cli_refuses_repository_outputs(self):
        with self.assertRaisesRegex(ReadinessError, "TEMP_SUBDIRECTORY"):
            run_synthetic("C1-T", 42, Path(__file__).resolve().parents[1] / "reports/science")


if __name__ == "__main__":
    unittest.main()
