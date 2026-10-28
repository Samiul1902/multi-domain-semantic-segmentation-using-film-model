"""C1 synthetic CPU tests only: no dataset or historical checkpoint loading."""
import copy
from pathlib import Path
import unittest
from unittest.mock import patch

import torch

from src.research.c1_film.control import (
    build_matched_arms, is_conditioning, optimizer_group_spec,
    parameter_accounting, verify_identity_control,
)
from src.research.c1_film.readiness import (
    EXCLUSIONS, PROTOCOL_SHA256, ReadinessError, assert_launch_allowed,
    load_protocol, main, validate_dataset_contract, validate_population_request,
)

ROOT = Path(__file__).resolve().parents[1]


class MatchedControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.previous_threads = torch.get_num_threads()
        torch.set_num_threads(1)

    @classmethod
    def tearDownClass(cls):
        torch.set_num_threads(cls.previous_threads)

    def test_counts_and_optimizer_group_membership(self):
        t, c = build_matched_arms(42)
        self.assertEqual(parameter_accounting(t)["total"], 3523001)
        self.assertEqual(parameter_accounting(t)["trainable"], 3523001)
        self.assertEqual(parameter_accounting(c)["trainable"], 3432233)
        self.assertEqual(parameter_accounting(c)["frozen"], 90768)
        for model in (t, c):
            groups = optimizer_group_spec(model)
            self.assertEqual(len(groups), 1)
            actual = {id(p) for p in groups[0]["params"]}
            self.assertEqual(actual, {id(p) for p in model.parameters() if p.requires_grad})
            self.assertEqual(groups[0]["lr"], 1e-4)
            self.assertEqual(groups[0]["weight_decay"], 1e-4)

    def test_every_site_is_identity_for_all_tasks(self):
        _, control = build_matched_arms(42)
        task_ids = torch.arange(4)
        emb = control.task_embedding(task_ids)
        for site, layer in control.film_layers.items():
            with self.subTest(site=site):
                features = torch.linspace(-2, 2, 4 * layer.channels * 4).reshape(
                    4, layer.channels, 2, 2)
                out, gamma, beta = layer(features, emb)
                self.assertTrue(torch.equal(out, features))
                self.assertEqual(torch.count_nonzero(gamma).item(), 0)
                self.assertEqual(torch.count_nonzero(beta).item(), 0)

    def test_full_network_matches_site_bypass_and_ignores_task(self):
        _, control = build_matched_arms(123)
        control.eval()
        bypass = copy.deepcopy(control)
        handles = [layer.register_forward_hook(lambda module, args, out: (args[0], out[1], out[2]))
                   for layer in bypass.film_layers.values()]
        x = torch.linspace(0, 1, 3 * 32 * 32).reshape(1, 3, 32, 32)
        try:
            with torch.no_grad():
                reference = bypass(x, torch.tensor([0]))
                for task in range(4):
                    self.assertTrue(torch.equal(reference, control(x, torch.tensor([task]))))
        finally:
            for h in handles:
                h.remove()

    def test_control_backbone_updates_conditioning_does_not(self):
        _, control = build_matched_arms(3407)
        frozen_before = {n: p.detach().clone() for n, p in control.named_parameters()
                         if is_conditioning(n)}
        head_before = control.head.weight.detach().clone()
        opt = torch.optim.AdamW(optimizer_group_spec(control))
        x = torch.ones(1, 3, 32, 32)
        loss = torch.nn.functional.binary_cross_entropy_with_logits(
            control(x, torch.tensor([1])), torch.zeros(1, 1, 32, 32))
        loss.backward()
        self.assertIsNotNone(control.encoder1.block1[0].weight.grad)
        self.assertIsNotNone(control.head.weight.grad)
        for n, p in control.named_parameters():
            if is_conditioning(n):
                self.assertIsNone(p.grad)
        opt.step()
        self.assertFalse(torch.equal(head_before, control.head.weight))
        for n, p in control.named_parameters():
            if is_conditioning(n):
                self.assertTrue(torch.equal(frozen_before[n], p))
        verify_identity_control(control)

    def test_all_seed_initial_states_match_without_rng_side_effect(self):
        for seed in (42, 123, 3407):
            before = torch.get_rng_state().clone()
            t, c = build_matched_arms(seed)
            self.assertTrue(torch.equal(before, torch.get_rng_state()))
            for n, p in t.state_dict().items():
                self.assertTrue(torch.equal(p, c.state_dict()[n]), n)

    def test_treatment_modulation_can_learn(self):
        treatment, _ = build_matched_arms(42)
        y = treatment(torch.ones(1, 3, 32, 32), torch.tensor([2]))
        y.square().mean().backward()
        self.assertTrue(any(layer.output.bias.grad is not None and
                            torch.count_nonzero(layer.output.bias.grad).item()
                            for layer in treatment.film_layers.values()))
        self.assertTrue(all(p.requires_grad for p in treatment.task_embedding.parameters()))

    def test_architecture_source_drift_blocks_construction(self):
        with patch.object(Path, "read_bytes", return_value=b"mutated model source"):
            with self.assertRaisesRegex(RuntimeError, "ARCHITECTURE_SOURCE_DRIFT"):
                build_matched_arms(42)

    def test_corrupted_projection_or_unfrozen_path_rejected(self):
        _, c = build_matched_arms(42)
        with torch.no_grad():
            c.film_layers["decoder1"].output.bias[0] = 0.01
        with self.assertRaisesRegex(RuntimeError, "NONIDENTITY"):
            verify_identity_control(c)
        _, c = build_matched_arms(42)
        c.task_embedding.weight.requires_grad_(True)
        with self.assertRaisesRegex(RuntimeError, "NOT_FROZEN"):
            verify_identity_control(c)


class ScopeTests(unittest.TestCase):
    def setUp(self):
        self.protocol = load_protocol()

    def test_canonical_contract_without_manifest_access(self):
        with patch.object(Path, "read_bytes", side_effect=AssertionError("no data reads")):
            validate_dataset_contract(self.protocol["dataset"])
            for split, info in self.protocol["dataset"]["populations"].items():
                validate_population_request(self.protocol["dataset"], split,
                                            info["path"], info["n"], info["sha256"])

    def test_dataset_task_split_path_count_hash_mutations_fail_closed(self):
        for key, value in (("dataset_id", "OTHER"), ("manifest_version", "phase4_v2"),
                           ("task_ids", {"ISIC": 1}), ("prohibited", [])):
            mutated = copy.deepcopy(self.protocol["dataset"])
            mutated[key] = value
            with self.subTest(key=key), self.assertRaises(ReadinessError):
                validate_dataset_contract(mutated)
        good = self.protocol["dataset"]["populations"]["TRAIN"]
        for split in ("TEST", "ROUTER_HOLDOUT", "EXTERNAL", "train", "QUARANTINE"):
            with self.subTest(split=split), self.assertRaises(ReadinessError):
                validate_population_request(self.protocol["dataset"], split,
                                            good["path"], good["n"], good["sha256"])
        for path, n, digest in (("manifests/phase4_v3/test.csv", good["n"], good["sha256"]),
                                (good["path"], 1, good["sha256"]),
                                (good["path"], good["n"], "0" * 64)):
            with self.assertRaises(ReadinessError):
                validate_population_request(self.protocol["dataset"], "TRAIN", path, n, digest)

    def test_no_approval_refused_before_any_training(self):
        with self.assertRaisesRegex(ReadinessError, "AUTHORIZATION_REQUIRED"):
            assert_launch_allowed(self.protocol)

    def test_barr_approval_cannot_authorize_c1(self):
        with self.assertRaises(ReadinessError):
            assert_launch_allowed(self.protocol, {"scope": "BARR-M1"})

    def test_even_fabricated_complete_approval_cannot_enable_preparation(self):
        approval = {k: "SYNTHETIC_NOT_AUTHORITY" for k in
                    ("authorization_id", "authorized_by", "institutional_role",
                     "decision_record", "authorized_at")}
        approval.update(scope="C1_FILM_ATTRIBUTION_V1", protocol_sha256=PROTOCOL_SHA256,
                        arms=["C1-T", "C1-C"], seeds=[42, 123, 3407],
                        exclusions=sorted(EXCLUSIONS))
        with self.assertRaisesRegex(ReadinessError, "SEPARATE_LAUNCH_REQUIRED"):
            assert_launch_allowed(self.protocol, approval)
        with self.assertRaisesRegex(ReadinessError, "PREPARATION_ONLY"):
            assert_launch_allowed(self.protocol, approval,
                                 {"authorization_id": approval["authorization_id"]})

    def test_execution_flag_is_not_silently_accepted(self):
        with patch("sys.stderr"):
            with self.assertRaises(SystemExit) as caught:
                main(["--execute"])
        self.assertEqual(caught.exception.code, 2)

    def test_protocol_corruption_rejected_before_json_parsing(self):
        with patch.object(Path, "read_bytes", return_value=b"not the frozen protocol"):
            with self.assertRaisesRegex(ReadinessError, "DIGEST_DRIFT"):
                load_protocol()


if __name__ == "__main__":
    unittest.main()
