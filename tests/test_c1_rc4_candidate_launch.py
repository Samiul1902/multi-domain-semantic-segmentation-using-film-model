"""Synthetic-only acceptance tests for the DRAFT RC4 campaign candidate.

Every key, trust store, approval and time proof is a SYNTHETIC TEST FIXTURE in a
temporary directory. No real image, mask, TRAIN/VAL/TEST/ROUTER_HOLDOUT file is opened
and no production trust directory is read or written.
"""
from __future__ import annotations

import copy
import json
import os
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path
from unittest import mock

import torch

from src.research.c1_film.integration_contract import make_contract
from src.research.c1_film.synthetic_fixture import fixture_loaders
from src.research.c1_film.train_driver import real_loader_factory
from src.research.c1_film.training_engine import Trainer
from src.research.c1_film_launch import launch_gate as rc1
from src.research.c1_film_launch import release_identity as rc1_rid
from src.research.c1_film_launch_rc2 import time_status
from src.research.c1_film_launch_rc2.trust_policy import policy_digest, spki_fingerprint
from src.research.c1_film_launch_rc4 import rc4_gate, trust_rc4
from src.research.c1_film_launch_rc4 import release_identity_rc4 as rid
from src.research.c1_rc4_candidate import campaign_rc4_draft as draft
from tests.test_c1_launch_rc4 import (NOW, Base, _iso_z, _key, _sign, build_authorization,
                                      build_store)

G = rc4_gate.GateError


def fingerprint(store) -> str:
    return spki_fingerprint(store["binding"]["policy_owner_public_key_pem"]).lower()


class CandidateBase(Base):
    def setUp(self):
        super().setUp()
        self.fp = fingerprint(self.store)
        self.artifacts = self.build_artifacts(self.store)

    def build_artifacts(self, store, digest=None, recovery_overrides=None):
        digest = digest or self.digest
        auth = build_authorization(store, digest)
        proofs, recoveries = {}, {}
        for i, item in enumerate(draft.frozen_run_plan()):
            key = draft.run_key(item["arm"], item["seed"])
            proof = copy.deepcopy(auth["time_status"])
            proof["nonce"] = f"{i:02d}" + "abcdef0123456789" * 4
            proof["signature"] = _sign(store["keys"]["time-1"], proof)
            proofs[key] = proof
            recoveries[key] = {"mode": "FRESH", "arm": item["arm"], "seed": item["seed"]}
        recoveries.update(recovery_overrides or {})
        return {"approval": auth["approval"], "instruction": auth["instruction"],
                "budget": auth["budget"], "time_status": proofs, "recovery": recoveries}

    def run_all(self, **over):
        kw = dict(expected_release_digest=self.digest, owner_key_fingerprint=self.fp,
                  artifacts=self.artifacts, trust_store_root=self.store["root"],
                  output_root=self.out, require_owner=False)
        kw.update(over)
        return draft.execute_campaign(**kw)

    def refused(self, code, **over):
        with self.assertRaises(G) as ctx:
            self.run_all(**over)
        self.assertIn(code, str(ctx.exception))


class PositivePathTests(CandidateBase):
    def test_all_six_frozen_runs_preflight_with_distinct_proofs(self):
        with mock.patch("src.data.multidomain_dataset.MultiDomainDataset") as dataset:
            records = self.run_all()
            dataset.assert_not_called()
        self.assertEqual(len(records), 6)
        self.assertEqual({r["release_id"] for r in records}, {rid.RELEASE_ID})
        self.assertEqual({r["release_digest"] for r in records}, {self.digest})
        self.assertEqual(len({r["nonce_sha256"] for r in records}), 6)
        self.assertEqual({(e["arm"], e["seed"]) for e in draft.frozen_run_plan()},
                         {(a, s) for a in ("C1-T", "C1-C") for s in (42, 123, 3407)})

    def test_each_run_proof_is_single_use(self):
        draft.preflight_run("C1-T", 42, expected_release_digest=self.digest,
                            owner_key_fingerprint=self.fp, artifacts=self.artifacts,
                            trust_store_root=self.store["root"], require_owner=False,
                            output_root=self.out, consume_nonce=True)
        with self.assertRaises(G) as ctx:
            draft.preflight_run("C1-T", 42, expected_release_digest=self.digest,
                                owner_key_fingerprint=self.fp, artifacts=self.artifacts,
                                trust_store_root=self.store["root"], require_owner=False,
                                output_root=self.out, consume_nonce=True)
        self.assertIn("TIME_NONCE_REPLAY", str(ctx.exception))

    def test_real_execution_refused_for_draft(self):
        self.refused("C1_RC4_DRAFT_LAUNCHER_NOT_AUTHORIZED", execute=True)
        self.assertFalse(draft.DRAFT_AUTHORIZED)

    def test_candidate_never_imports_rc2_rc3_launch_drivers(self):
        source = Path(draft.__file__).read_text(encoding="utf-8")
        for banned in ("launch_driver_rc3", "rc3_gate", "launch_driver_rc2", "DEFAULT_PRODUCTION_ROOT",
                       "InstitutionalC1Trust\""):
            self.assertNotIn(banned, source)
        self.assertIn("launch_driver_rc4", source)


class NegativePathTests(CandidateBase):
    def test_wrong_and_predecessor_release_digests_refused(self):
        self.refused("C1_RC4_RELEASE_DIGEST_MISMATCH", expected_release_digest="0" * 64)
        for old in rid.PREDECESSOR_DIGESTS:
            self.refused("C1_RC4_PREDECESSOR_IDENTITY_REJECTED", expected_release_digest=old)

    def test_missing_institution_approved_trust_fails_closed(self):
        with mock.patch.object(trust_rc4, "PRODUCTION_ROOT", Path(self.tmp.name) / "absent"):
            self.refused("C1_RC4_TRUST_ROOT_MISSING", trust_store_root=None, require_owner=True)
        self.refused("C1_RC4_LEGACY_TRUST_STORE_REJECTED",
                     trust_store_root=trust_rc4.LEGACY_ROOT, require_owner=True)

    def test_invalid_and_forged_signatures_refused(self):
        bad = copy.deepcopy(self.artifacts)
        bad["approval"]["authorized_by"] = "SOMEONE ELSE"
        self.refused("SIGNATURE_INVALID", artifacts=bad)
        forged = copy.deepcopy(self.artifacts)
        forged["approval"]["signature"] = _sign(_key()[0], forged["approval"])
        self.refused("SIGNATURE_INVALID", artifacts=forged)
        unsigned = copy.deepcopy(self.artifacts)
        del unsigned["approval"]["signature"]
        self.refused("SIGNATURE_MISSING", artifacts=unsigned)

    def test_clock_failure_in_one_run_refuses_campaign(self):
        bad = copy.deepcopy(self.artifacts)
        proof = bad["time_status"]["C1-C_seed3407"]
        proof["expires_at_utc"] = _iso_z(NOW - timedelta(seconds=5))
        proof["signature"] = _sign(self.store["keys"]["time-1"], proof)
        self.refused("TIME_PROOF_EXPIRED", artifacts=bad)

    def test_reused_nonce_across_runs_refused_at_load(self):
        base = Path(self.tmp.name)
        for name in ("tp", "rc"):
            (base / name).mkdir()
        for key, proof in self.artifacts["time_status"].items():
            proof = dict(proof, nonce=self.artifacts["time_status"]["C1-T_seed42"]["nonce"])
            (base / "tp" / f"{key}.json").write_text(json.dumps(proof), encoding="utf-8")
            (base / "rc" / f"{key}.json").write_text(
                json.dumps(self.artifacts["recovery"][key]), encoding="utf-8")
        for name, payload in (("approval", self.artifacts["approval"]),
                              ("instruction", self.artifacts["instruction"]),
                              ("budget", self.artifacts["budget"])):
            (base / f"{name}.json").write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaisesRegex(G, "TIME_PROOF_NOT_DISTINCT"):
            draft.load_artifacts(approval=base / "approval.json", instruction=base / "instruction.json",
                                 budget=base / "budget.json", time_proof_dir=base / "tp",
                                 recovery_dir=base / "rc")

    def test_wrong_signing_role_refused(self):
        bad = copy.deepcopy(self.artifacts)
        bad["approval"]["key_id"] = "time-1"
        bad["approval"]["signature"] = _sign(self.store["keys"]["time-1"], bad["approval"])
        self.refused("SIGNATURE_KEY_ROLE", artifacts=bad)

    def test_unauthorized_run_and_split_refused(self):
        with self.assertRaises(G):
            draft.preflight_run("C1-T", 7, expected_release_digest=self.digest,
                                owner_key_fingerprint=self.fp, artifacts=self.artifacts,
                                trust_store_root=self.store["root"], require_owner=False)
        bad = copy.deepcopy(self.artifacts)
        bad["approval"]["requested_splits"] = ["TRAIN", "VAL", "TEST"]
        bad["approval"]["signature"] = _sign(self.store["keys"]["supervisor-1"], bad["approval"])
        self.refused("C1_PROHIBITED_SPLIT", artifacts=bad)

    def test_unauthorized_real_data_access_refused_before_reader(self):
        protocol = json.loads(rc1_rid.PROTOCOL_PATH.read_text(encoding="utf-8-sig"))
        grant = rc4_gate.mint_rc4_grant(**self.kwargs())
        with mock.patch("src.data.multidomain_dataset.MultiDomainDataset") as dataset:
            with self.assertRaisesRegex(G, "SYNTHETIC_GRANT_CANNOT_ACCESS_DATA"):
                real_loader_factory(protocol, grant=grant)
            dataset.assert_not_called()


def plausible_attacker_store(base: Path):
    """Self-generated keys, plausible institutional names, placed under a fake ProgramData."""
    root = base / "ProgramData" / "InstitutionalC1TrustRC4"
    store = build_store(root)
    owner_key, owner_pem = _key()
    names = {"supervisor-1": "Dr A Approver", "launch-1": "B Operator", "time-1": "C Timekeeper"}
    policy = store["policy"]
    policy.pop("policy_signature", None)
    policy["owner_identity"] = "Plausible University Research Office"
    for key in policy["keys"]:
        key["custodian"] = names[key["key_id"]]
    policy["policy_digest"] = policy_digest(policy)
    policy["policy_signature"] = _sign(owner_key, policy, ("policy_signature",))
    binding = store["binding"]
    for field in ("institution_name", "approving_authority", "key_custodian",
                  "provisioning_reference", "owner_identity"):
        binding[field] = "Plausible University Research Office"
    binding.update(policy_digest=policy["policy_digest"], policy_owner_public_key_pem=owner_pem)
    (root / "policy.json").write_text(json.dumps(policy), encoding="utf-8")
    (root / "c1_rc4_binding.json").write_text(json.dumps(binding), encoding="utf-8")
    return store


class TrustAnchorTests(CandidateBase):
    def test_attacker_store_with_plausible_names_cannot_authorize(self):
        attacker = plausible_attacker_store(Path(self.tmp.name))
        artifacts = self.build_artifacts(attacker)
        env = dict(os.environ, ProgramData=str(attacker["root"].parent))
        with mock.patch.dict(os.environ, env), \
                mock.patch.object(trust_rc4, "PRODUCTION_ROOT", attacker["root"]):
            # Control: the store passes the location/identity-text checks (the known gap).
            trust_rc4.load_trust_store_rc4(attacker["root"], require_owner=True)
            # Institution-provided fingerprint (a different key) => refused.
            with self.assertRaises(G) as ctx:
                draft.execute_campaign(
                    expected_release_digest=self.digest, owner_key_fingerprint=self.fp,
                    artifacts=artifacts, trust_store_root=None, output_root=self.out,
                    require_owner=True)
            self.assertIn("C1_RC4_EXTERNAL_ANCHOR_MISMATCH", str(ctx.exception))

    def test_fingerprint_must_be_supplied_out_of_band(self):
        for missing in (None, "", "abc", "z" * 64):
            self.refused("C1_RC4_EXTERNAL_ANCHOR_REQUIRED", owner_key_fingerprint=missing)

    def test_fingerprint_formatting_is_normalized_but_not_loosened(self):
        pretty = ":".join(self.fp[i:i + 2] for i in range(0, 64, 2)).upper()
        self.assertEqual(len(self.run_all(owner_key_fingerprint=pretty)), 6)
        self.refused("C1_RC4_EXTERNAL_ANCHOR_MISMATCH", owner_key_fingerprint="0" * 64)


class SyntheticRecoveryChainTests(CandidateBase):
    @classmethod
    def setUpClass(cls):
        cls.threads = torch.get_num_threads()
        torch.set_num_threads(1)

    @classmethod
    def tearDownClass(cls):
        torch.set_num_threads(cls.threads)

    def test_authorize_then_synthetic_checkpoint_resume_and_recovery_identity(self):
        # 1. Authorization chain (synthetic trust) for the run under test.
        record = draft.preflight_run("C1-C", 42, expected_release_digest=self.digest,
                                     owner_key_fingerprint=self.fp, artifacts=self.artifacts,
                                     trust_store_root=self.store["root"], require_owner=False,
                                     output_root=self.out)
        self.assertEqual(record["release_digest"], self.digest)
        # 2. Synthetic-only training fixture: interrupt after epoch 1, resume to completion.
        attempt = self.out / "seed42" / "C1-C"
        contract = make_contract("C1-C", 42, synthetic=True)
        Trainer(contract).run(attempt, fixture_loaders, until_epoch=1)
        resumed = Trainer(make_contract("C1-C", 42, synthetic=True))
        resumed.run(attempt, fixture_loaders, resume=True)
        lifecycle = json.loads((attempt / "lifecycle.json").read_text(encoding="utf-8"))
        self.assertEqual(lifecycle["state"], "COMPLETE")
        # 3. A FRESH launch over an existing attempt is refused; correct RESUME identity is accepted.
        with self.assertRaisesRegex(G, "C1_RECOVERY_IDENTITY_INVALID"):
            draft.preflight_run("C1-C", 42, expected_release_digest=self.digest,
                                owner_key_fingerprint=self.fp, artifacts=self.artifacts,
                                trust_store_root=self.store["root"], require_owner=False,
                                output_root=self.out)
        identity = rc1.run_identity(self.digest, "C1-C", 42)
        artifacts = copy.deepcopy(self.artifacts)
        artifacts["recovery"]["C1-C_seed42"] = {"mode": "RESUME", "arm": "C1-C", "seed": 42,
                                                "identity": identity}
        draft.preflight_run("C1-C", 42, expected_release_digest=self.digest,
                            owner_key_fingerprint=self.fp, artifacts=artifacts,
                            trust_store_root=self.store["root"], require_owner=False,
                            output_root=self.out)


if __name__ == "__main__":
    unittest.main()
