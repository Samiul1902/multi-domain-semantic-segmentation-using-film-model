"""C1 launch release: identity, gate, and authorization negative controls.

Synthetic only. No real data, no TEST/ROUTER_HOLDOUT access, no approval fabricated
as production authority. Ephemeral keys are generated inside temporary directories
and are refused by the empty anchor allowlist by construction.
"""
from __future__ import annotations

import base64
import copy
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

import torch

from src.research.c1_film import readiness
from src.research.c1_film.integration_contract import make_contract
from src.research.c1_film.training_engine import Trainer
from src.research.c1_film import train_driver
from src.research.c1_film_launch import release_identity as rid
from src.research.c1_film_launch.launch_gate import (
    APPROVED_ARMS, APPROVED_SEEDS, REQUIRED_EXCLUSIONS, GateError, LaunchGrant,
    assert_launch_authorized, anchor_fingerprint, expected_run_plan, mint_grant,
    run_identity, verify_detached_signature,
)

NOW = datetime.now(timezone.utc)


def _iso(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ephemeral_key():
    key = ec.generate_private_key(ec.SECP256R1())
    pem = key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo).decode()
    return key, pem


def _sign(key, payload: dict) -> str:
    return base64.b64encode(key.sign(rid.canonical_json(payload),
                                     ec.ECDSA(hashes.SHA256()))).decode()


def _protocol() -> dict:
    return json.loads(rid.PROTOCOL_PATH.read_text(encoding="utf-8-sig"))


def build_valid_authorization(release_digest: str):
    """A structurally complete, correctly scoped, correctly signed authorization.

    This is a *test fixture*, never production authority. The gate must refuse it
    because no anchor fingerprint is allowlisted in this release.
    """
    key, pem = _ephemeral_key()
    protocol = _protocol()
    approval = {
        "authorization_id": "SYNTHETIC-NOT-AUTHORITY-0001",
        "authorized_by": "Synthetic Test Institution",
        "institutional_role": "TEST_FIXTURE_ONLY",
        "decision_record": "SYNTHETIC-NOT-AUTHORITY-RECORD",
        "authorized_at": _iso(NOW - timedelta(hours=2)),
        "scope": rid.STUDY_ID,
        "protocol_sha256": rid.PROTOCOL_SHA256,
        "release_digest": release_digest,
        "arms": list(APPROVED_ARMS),
        "seeds": list(APPROVED_SEEDS),
        "exclusions": sorted(REQUIRED_EXCLUSIONS),
        "populations": copy.deepcopy(protocol["dataset"]["populations"]),
        "requested_paths": [protocol["dataset"]["populations"]["TRAIN"]["path"],
                            protocol["dataset"]["populations"]["VAL"]["path"]],
        "requested_splits": ["TRAIN", "VAL"],
    }
    approval["signature"] = _sign(key, approval)
    run_plan = expected_run_plan()
    instruction = {
        "launch_id": "SYNTHETIC-LAUNCH-0001",
        "authorization_id": approval["authorization_id"],
        "release_digest": release_digest,
        "issued_at": _iso(NOW - timedelta(hours=1)),
        "run_plan": run_plan,
    }
    instruction["signature"] = _sign(key, instruction)
    anchor = {
        "institution": approval["authorized_by"],
        "public_key_pem": pem,
        "authorized_roles": [approval["institutional_role"]],
        "valid_from": _iso(NOW - timedelta(days=1)),
        "valid_until": _iso(NOW + timedelta(days=1)),
    }
    budget = {"logical_runs": 6, "max_epochs": 100, "max_cumulative_active_hours": 96}
    trusted_time = {"source": "NTP", "server": "synthetic.invalid", "synchronized": True,
                    "abs_offset_seconds": 0.05,
                    "measured_at_utc": _iso(NOW - timedelta(minutes=30))}
    recovery = {"mode": "FRESH", "arm": "C1-T", "seed": 42}
    return {"approval": approval, "instruction": instruction, "anchor": anchor,
            "budget": budget, "run_plan": run_plan, "trusted_time": trusted_time,
            "recovery": recovery, "key": key, "pem": pem}


class ReleaseIdentityTests(unittest.TestCase):
    def test_release_verifies_and_covers_all_c1_modules(self):
        report = rid.verify_release()
        self.assertTrue(report["published_digest_matches"])
        self.assertEqual(report["c1_module_count"], 8)
        self.assertGreaterEqual(report["bound_source_count"], len(rid.REQUIRED_COVERAGE))
        self.assertEqual(report["protocol_sha256"], rid.PROTOCOL_SHA256)
        self.assertEqual(report["architecture_sha256"], rid.ARCHITECTURE_SHA256)
        self.assertEqual(len(report["release_digest"]), 64)

    def test_digest_is_recomputable_without_this_module(self):
        manifest = json.loads(rid.MANIFEST_PATH.read_text(encoding="utf-8"))
        independent = rid.sha256_bytes(
            json.dumps(manifest, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False).encode("utf-8"))
        self.assertEqual(independent, rid.verify_release()["release_digest"])

    def test_manifest_does_not_bind_itself(self):
        manifest = json.loads(rid.MANIFEST_PATH.read_text(encoding="utf-8"))
        bound = {e["path"] for e in manifest["bound_sources"]}
        for excluded in rid.SELF_EXCLUDED:
            self.assertNotIn(excluded, bound)

    def test_modified_executable_source_detected(self):
        target = "src/research/c1_film/control.py"
        real = rid.sha256_file

        def fake(path):
            return "0" * 64 if str(path).replace("\\", "/").endswith(target) else real(path)

        with patch.object(rid, "sha256_file", fake):
            with self.assertRaisesRegex(rid.ReleaseIdentityError, "C1_RELEASE_SOURCE_DRIFT"):
                rid.verify_release()

    def test_missing_module_coverage_detected(self):
        manifest = json.loads(rid.MANIFEST_PATH.read_text(encoding="utf-8"))
        manifest["bound_sources"] = [e for e in manifest["bound_sources"]
                                     if not e["path"].endswith("recovery_store.py")]
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "manifest_v2.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            with patch.object(rid, "MANIFEST_PATH", path):
                with self.assertRaisesRegex(rid.ReleaseIdentityError,
                                            "C1_RELEASE_COVERAGE_INCOMPLETE"):
                    rid.verify_release(require_published=False)

    def test_self_binding_manifest_rejected(self):
        manifest = json.loads(rid.MANIFEST_PATH.read_text(encoding="utf-8"))
        manifest["bound_sources"].append({"path": rid.SELF_EXCLUDED[0], "sha256": "0" * 64,
                                          "bytes": 1})
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "manifest_v2.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            with patch.object(rid, "MANIFEST_PATH", path):
                with self.assertRaisesRegex(rid.ReleaseIdentityError, "C1_RELEASE_SELF_BINDING"):
                    rid.verify_release(require_published=False)

    def test_stale_published_digest_detected(self):
        real = rid.published_digest
        with patch.object(rid, "published_digest",
                          lambda: {**real(), "release_digest": "f" * 64}):
            with self.assertRaisesRegex(rid.ReleaseIdentityError, "C1_RELEASE_DIGEST_STALE"):
                rid.verify_release()

    def test_protocol_and_architecture_are_frozen(self):
        self.assertEqual(rid.sha256_file(rid.PROTOCOL_PATH), rid.PROTOCOL_SHA256)
        self.assertEqual(rid.sha256_file(rid.ARCHITECTURE_PATH), rid.ARCHITECTURE_SHA256)


class GateRefusalTests(unittest.TestCase):
    """Every refusal is a specific, named defect — not a generic failure."""

    def setUp(self):
        self.release = rid.verify_release()
        self.digest = self.release["release_digest"]
        self.fixture = build_valid_authorization(self.digest)
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.anchor_path = Path(self.tmp.name) / "trust_anchor.json"
        self.anchor_path.write_text(json.dumps(self.fixture["anchor"]), encoding="utf-8")

    def _call(self, **overrides):
        kwargs = {
            "expected_release_digest": self.digest,
            "approval": self.fixture["approval"],
            "instruction": self.fixture["instruction"],
            "anchor_path": self.anchor_path,
            "budget": self.fixture["budget"],
            "run_plan": self.fixture["run_plan"],
            "recovery": self.fixture["recovery"],
            "trusted_time": self.fixture["trusted_time"],
            "output_root": Path(self.tmp.name) / "outputs",
            "now": NOW,
        }
        kwargs.update(overrides)
        return assert_launch_authorized(**kwargs)

    # -- the central claim -------------------------------------------------
    def test_complete_valid_authorization_still_refused(self):
        """A well-formed, correctly scoped, correctly signed approval cannot launch.

        The anchor allowlist is empty, so no key can be trusted in this release.
        """
        self.assertTrue(verify_detached_signature(
            self.fixture["pem"], self.fixture["approval"], self.fixture["approval"]["signature"]))
        with self.assertRaisesRegex(GateError, "C1_TRUST_ANCHOR_NOT_ALLOWLISTED"):
            self._call()

    def test_forged_signature_refused_at_anchor_not_signature(self):
        approval = copy.deepcopy(self.fixture["approval"])
        approval["signature"] = base64.b64encode(b"\x00" * 70).decode()
        with self.assertRaisesRegex(GateError, "C1_TRUST_ANCHOR_NOT_ALLOWLISTED"):
            self._call(approval=approval)

    def test_signature_primitive_rejects_wrong_payload(self):
        pem = self.fixture["pem"]
        payload = copy.deepcopy(self.fixture["approval"])
        self.assertTrue(verify_detached_signature(pem, payload, payload["signature"]))
        payload["arms"] = ["C1-T"]
        self.assertFalse(verify_detached_signature(pem, payload, payload["signature"]))

    def test_signature_primitive_rejects_non_ecdsa_key(self):
        from cryptography.hazmat.primitives.asymmetric import ed25519
        pem = ed25519.Ed25519PrivateKey.generate().public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo).decode()
        self.assertFalse(verify_detached_signature(pem, {"a": 1}, "AAAA"))

    # -- Phase A specific refusals ----------------------------------------
    def test_missing_approval(self):
        with self.assertRaisesRegex(GateError, "C1_AUTHORIZATION_REQUIRED"):
            self._call(approval=None)

    def test_incomplete_approval(self):
        approval = copy.deepcopy(self.fixture["approval"])
        approval["decision_record"] = "  "
        with self.assertRaisesRegex(GateError, "C1_AUTHORIZATION_INCOMPLETE"):
            self._call(approval=approval)

    def test_wrong_scope_barr_m1_rejected(self):
        approval = copy.deepcopy(self.fixture["approval"])
        approval["scope"] = "BARR-M1"
        with self.assertRaisesRegex(GateError, "C1_AUTHORIZATION_SCOPE_MISMATCH"):
            self._call(approval=approval)

    def test_wrong_protocol_digest(self):
        approval = copy.deepcopy(self.fixture["approval"])
        approval["protocol_sha256"] = "0" * 64
        with self.assertRaisesRegex(GateError, "C1_AUTHORIZATION_PROTOCOL_MISMATCH"):
            self._call(approval=approval)

    def test_wrong_release_digest_in_approval(self):
        approval = copy.deepcopy(self.fixture["approval"])
        approval["release_digest"] = "1" * 64
        with self.assertRaisesRegex(GateError, "C1_AUTHORIZATION_RELEASE_MISMATCH"):
            self._call(approval=approval)

    def test_stale_expected_release_digest(self):
        with self.assertRaisesRegex(GateError, "C1_RELEASE_DIGEST_MISMATCH"):
            self._call(expected_release_digest="2" * 64)

    def test_wrong_arms(self):
        approval = copy.deepcopy(self.fixture["approval"])
        approval["arms"] = ["C1-T"]
        with self.assertRaisesRegex(GateError, "C1_AUTHORIZATION_ARMS_MISMATCH"):
            self._call(approval=approval)

    def test_extra_arm_rejected(self):
        approval = copy.deepcopy(self.fixture["approval"])
        approval["arms"] = ["C1-T", "C1-C", "C1-X"]
        with self.assertRaisesRegex(GateError, "C1_AUTHORIZATION_ARMS_MISMATCH"):
            self._call(approval=approval)

    def test_wrong_seeds(self):
        approval = copy.deepcopy(self.fixture["approval"])
        approval["seeds"] = [42, 123]
        with self.assertRaisesRegex(GateError, "C1_AUTHORIZATION_SEEDS_MISMATCH"):
            self._call(approval=approval)

    def test_missing_exclusions(self):
        approval = copy.deepcopy(self.fixture["approval"])
        approval["exclusions"] = ["TEST"]
        with self.assertRaisesRegex(GateError, "C1_AUTHORIZATION_EXCLUSIONS_MISSING"):
            self._call(approval=approval)

    def test_wrong_dataset_manifest(self):
        approval = copy.deepcopy(self.fixture["approval"])
        approval["populations"]["VAL"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(GateError, "C1_POPULATION_IDENTITY_MISMATCH"):
            self._call(approval=approval)

    def test_wrong_population_count(self):
        approval = copy.deepcopy(self.fixture["approval"])
        approval["populations"]["TRAIN"]["n"] = 1
        with self.assertRaisesRegex(GateError, "C1_POPULATION_IDENTITY_MISMATCH"):
            self._call(approval=approval)

    def test_prohibited_test_path(self):
        approval = copy.deepcopy(self.fixture["approval"])
        approval["requested_paths"] = ["manifests/phase4_v3/test.csv"]
        with self.assertRaisesRegex(GateError, "C1_PROHIBITED_SPLIT"):
            self._call(approval=approval)

    def test_prohibited_router_holdout_path(self):
        approval = copy.deepcopy(self.fixture["approval"])
        approval["requested_paths"] = ["manifests/phase4_v3/router_holdout.csv"]
        with self.assertRaisesRegex(GateError, "C1_PROHIBITED_SPLIT"):
            self._call(approval=approval)

    def test_prohibited_split_name(self):
        approval = copy.deepcopy(self.fixture["approval"])
        approval["requested_splits"] = ["TRAIN", "VAL", "ROUTER_HOLDOUT"]
        with self.assertRaisesRegex(GateError, "C1_PROHIBITED_SPLIT"):
            self._call(approval=approval)

    def test_budget_exceeded_epochs(self):
        budget = dict(self.fixture["budget"], max_epochs=101)
        with self.assertRaisesRegex(GateError, "C1_BUDGET_EXCEEDED"):
            self._call(budget=budget)

    def test_budget_exceeded_hours(self):
        budget = dict(self.fixture["budget"], max_cumulative_active_hours=97)
        with self.assertRaisesRegex(GateError, "C1_BUDGET_EXCEEDED"):
            self._call(budget=budget)

    def test_budget_wrong_run_count(self):
        budget = dict(self.fixture["budget"], logical_runs=7)
        with self.assertRaisesRegex(GateError, "C1_BUDGET_EXCEEDED"):
            self._call(budget=budget)

    def test_duplicate_logical_run(self):
        plan = expected_run_plan()
        plan[-1] = dict(plan[0])
        with self.assertRaisesRegex(GateError, "C1_DUPLICATE_LOGICAL_RUN"):
            self._call(run_plan=plan)

    def test_invalid_resume_identity(self):
        recovery = {"mode": "RESUME", "arm": "C1-T", "seed": 42, "identity": "deadbeef"}
        with self.assertRaisesRegex(GateError, "C1_RECOVERY_IDENTITY_INVALID"):
            self._call(recovery=recovery)

    def test_valid_resume_identity_shape_accepted(self):
        identity = run_identity(self.digest, "C1-T", 42)
        recovery = {"mode": "RESUME", "arm": "C1-T", "seed": 42, "identity": identity}
        # Reaches Phase B; still refused there because no anchor is allowlisted.
        with self.assertRaisesRegex(GateError, "C1_TRUST_ANCHOR_NOT_ALLOWLISTED"):
            self._call(recovery=recovery)

    def test_fresh_launch_over_existing_attempt_rejected(self):
        root = Path(self.tmp.name) / "outputs"
        attempt = root / "seed42" / "C1-T"
        attempt.mkdir(parents=True)
        (attempt / "latest.json").write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(GateError, "C1_RECOVERY_IDENTITY_INVALID"):
            self._call(output_root=root)

    def test_missing_trusted_time(self):
        with self.assertRaisesRegex(GateError, "C1_TRUSTED_TIME_UNVERIFIED"):
            self._call(trusted_time=None)

    def test_unsynchronized_trusted_time(self):
        attestation = dict(self.fixture["trusted_time"], synchronized=False)
        with self.assertRaisesRegex(GateError, "C1_TRUSTED_TIME_UNVERIFIED"):
            self._call(trusted_time=attestation)

    def test_excessive_clock_offset(self):
        attestation = dict(self.fixture["trusted_time"], abs_offset_seconds=5.0)
        with self.assertRaisesRegex(GateError, "C1_TRUSTED_TIME_UNVERIFIED"):
            self._call(trusted_time=attestation)

    def test_stale_trusted_time(self):
        attestation = dict(self.fixture["trusted_time"],
                           measured_at_utc=_iso(NOW - timedelta(days=3)))
        with self.assertRaisesRegex(GateError, "C1_TRUSTED_TIME_UNVERIFIED"):
            self._call(trusted_time=attestation)

    def test_missing_launch_instruction(self):
        with self.assertRaisesRegex(GateError, "C1_SEPARATE_LAUNCH_REQUIRED"):
            self._call(instruction=None)

    def test_launch_instruction_copied_from_approval_rejected(self):
        instruction = copy.deepcopy(self.fixture["instruction"])
        instruction["launch_id"] = instruction["authorization_id"]
        with self.assertRaisesRegex(GateError, "C1_SEPARATE_LAUNCH_REQUIRED"):
            self._call(instruction=instruction)

    def test_launch_instruction_wrong_release(self):
        instruction = copy.deepcopy(self.fixture["instruction"])
        instruction["release_digest"] = "3" * 64
        with self.assertRaisesRegex(GateError, "C1_LAUNCH_INSTRUCTION_MISMATCH"):
            self._call(instruction=instruction)

    def test_launch_instruction_wrong_run_plan(self):
        instruction = copy.deepcopy(self.fixture["instruction"])
        instruction["run_plan"] = instruction["run_plan"][:5]
        with self.assertRaisesRegex(GateError, "C1_LAUNCH_INSTRUCTION_MISMATCH"):
            self._call(instruction=instruction)

    def test_launch_issued_before_approval_rejected(self):
        instruction = copy.deepcopy(self.fixture["instruction"])
        instruction["issued_at"] = _iso(NOW - timedelta(hours=5))
        with self.assertRaisesRegex(GateError, "C1_LAUNCH_ORDER_VIOLATION"):
            self._call(instruction=instruction)

    def test_missing_trust_anchor(self):
        with self.assertRaisesRegex(GateError, "C1_TRUST_ANCHOR_MISSING"):
            self._call(anchor_path=Path(self.tmp.name) / "absent.json")

    def test_self_asserted_approval_flag_insufficient(self):
        approval = copy.deepcopy(self.fixture["approval"])
        approval.update(approved=True, authorized=True, trusted=True,
                        note="institutional sign-off attached")
        with self.assertRaisesRegex(GateError, "C1_TRUST_ANCHOR_NOT_ALLOWLISTED"):
            self._call(approval=approval)

    def test_release_drift_detected_by_gate(self):
        target = "src/research/c1_film/train_driver.py"
        real = rid.sha256_file

        def fake(path):
            return "0" * 64 if str(path).replace("\\", "/").endswith(target) else real(path)

        with patch.object(rid, "sha256_file", fake):
            with self.assertRaisesRegex(GateError, "C1_RELEASE_SOURCE_DRIFT"):
                self._call()


class GrantAndEntryPointTests(unittest.TestCase):
    def test_grant_cannot_be_constructed_directly(self):
        with self.assertRaisesRegex(GateError, "C1_LAUNCH_GRANT_FORGED"):
            LaunchGrant({"release_digest": "0" * 64, "run_plan": []})

    def test_mint_grant_refuses_without_allowlisted_anchor(self):
        digest = rid.verify_release()["release_digest"]
        fixture = build_valid_authorization(digest)
        with tempfile.TemporaryDirectory() as d:
            anchor = Path(d) / "anchor.json"
            anchor.write_text(json.dumps(fixture["anchor"]), encoding="utf-8")
            with self.assertRaisesRegex(GateError, "C1_TRUST_ANCHOR_NOT_ALLOWLISTED"):
                mint_grant(expected_release_digest=digest,
                           approval=fixture["approval"],
                           instruction=fixture["instruction"],
                           anchor_path=anchor, budget=fixture["budget"],
                           run_plan=fixture["run_plan"], recovery=fixture["recovery"],
                           trusted_time=fixture["trusted_time"],
                           output_root=Path(d) / "out", now=NOW)

    def test_trainer_refuses_real_contract_without_grant(self):
        with self.assertRaisesRegex(readiness.ReadinessError, "C1_LAUNCH_GRANT_REQUIRED"):
            Trainer(make_contract("C1-T", 42, synthetic=False, device="cuda"))

    def test_trainer_refuses_forged_grant_object(self):
        with self.assertRaisesRegex(readiness.ReadinessError, "C1_LAUNCH_GRANT_INVALID"):
            Trainer(make_contract("C1-T", 42, synthetic=False, device="cuda"),
                    grant=object())

    def test_run_real_refuses_without_grant(self):
        for kwargs in ({}, {"approval": {"scope": "BARR-M1"}},
                       {"approval": {"scope": rid.STUDY_ID, "approved": True}}):
            with self.assertRaisesRegex(readiness.ReadinessError, "C1_LAUNCH_GRANT_REQUIRED"):
                train_driver.run_real("C1-T", 42, **kwargs)

    def test_loader_factory_refuses_without_grant(self):
        protocol = _protocol()
        with self.assertRaisesRegex(readiness.ReadinessError, "C1_LAUNCH_GRANT_REQUIRED"):
            train_driver.real_loader_factory(protocol)

    def test_frozen_preparation_gate_still_refuses(self):
        protocol = readiness.load_protocol()
        with self.assertRaises(readiness.ReadinessError):
            readiness.assert_launch_allowed(protocol)
        with patch("sys.stderr"):
            with self.assertRaises(SystemExit):
                readiness.main(["--execute"])

    def test_synthetic_mode_unaffected_by_grant_requirement(self):
        with tempfile.TemporaryDirectory() as d:
            trainer = Trainer(make_contract("C1-C", 42, synthetic=True))
            trainer.run(Path(d), lambda seed, epoch: __import__(
                "src.research.c1_film.synthetic_fixture", fromlist=["fixture_loaders"]
            ).fixture_loaders(seed, epoch), until_epoch=1)
            self.assertEqual(len(trainer.history), 1)


class EndpointClarificationTests(unittest.TestCase):
    """Selected-epoch results: stored best_records vs recomputed best-checkpoint pass."""

    @classmethod
    def setUpClass(cls):
        cls.old_threads = torch.get_num_threads()
        torch.set_num_threads(1)

    @classmethod
    def tearDownClass(cls):
        torch.set_num_threads(cls.old_threads)

    def test_best_records_agree_with_recomputed_selected_checkpoint_pass(self):
        from src.research.c1_film.synthetic_fixture import fixture_loaders

        with tempfile.TemporaryDirectory() as d:
            trainer = Trainer(make_contract("C1-T", 42, synthetic=True))
            trainer.run(Path(d), fixture_loaders, until_epoch=2)
            self.assertTrue(trainer.best_records)
            self.assertIsNotNone(trainer.best_model)

            original = {k: v.detach().clone() for k, v in trainer.model.state_dict().items()}
            try:
                trainer.model.load_state_dict(trainer.best_model, strict=True)
                _, recomputed_domains, recomputed = trainer.evaluate(fixture_loaders(42, 0)[1])
            finally:
                trainer.model.load_state_dict(original, strict=True)

        stored = {row["sample_id"]: row for row in trainer.best_records}
        fresh = {row["sample_id"]: row for row in recomputed}
        self.assertEqual(set(stored), set(fresh))
        for sid in stored:
            self.assertAlmostEqual(stored[sid]["dice"], fresh[sid]["dice"], places=6)

        stored_domains = {}
        for row in trainer.best_records:
            stored_domains.setdefault(row["domain"], []).append(row["dice"])
        for domain, values in stored_domains.items():
            self.assertAlmostEqual(sum(values) / len(values), recomputed_domains[domain], places=6)


if __name__ == "__main__":
    unittest.main()
