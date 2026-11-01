"""Launch-path review tests for RC4 (additive; not bound by the RC4 manifest).

All keys/stores are SYNTHETIC fixtures in temporary directories. No production trust
directory is read or written, and no dataset file is opened.
"""
from __future__ import annotations

import os
import unittest
from datetime import timedelta
from pathlib import Path
from unittest import mock

from src.research.c1_film_launch_rc3 import time_status_rc3 as ts3
from src.research.c1_film_launch_rc4 import rc4_gate, trust_rc4
from src.research.c1_film_launch_rc4 import release_identity_rc4 as rid
from tests.test_c1_launch_rc4 import NOW, Base, _key, _sign, build_authorization, build_store


class AttackerControlledWorkspaceTests(Base):
    """Attacker edits code, regenerates manifest + digest, supplies own key and store."""

    def _attacker(self, name):
        store = build_store(Path(self.tmp.name) / name)
        return store

    def test_modified_release_cannot_reuse_institutional_approval(self):
        # Attacker regenerates manifest/digest => a different, self-consistent digest.
        forged_digest = "a" * 64
        forged = dict(rid.verify_release_rc4(), release_digest=forged_digest)
        with mock.patch.object(rc4_gate, "_verify_release", return_value=forged):
            with self.assertRaises(rc4_gate.GateError):
                self.call(expected_release_digest=forged_digest)  # approval signed for real digest

    def test_attacker_store_outside_production_root_refused(self):
        attacker = self._attacker("attacker_store")
        auth = build_authorization(attacker, self.digest)
        with self.assertRaisesRegex(rc4_gate.GateError, "TRUST_STORE_NOT_PRODUCTION"):
            rc4_gate.validate_authorization(**self.kwargs(
                trust_store_root=attacker["root"], require_owner=True, approval=auth["approval"],
                instruction=auth["instruction"], time_status=auth["time_status"]))

    def test_self_certified_authority_cannot_be_the_default_root(self):
        # Even with the default root silently replaced by an attacker store, a store whose
        # identity fields self-declare as synthetic/placeholder is refused.
        attacker = self._attacker("attacker_default")
        with mock.patch.object(trust_rc4, "PRODUCTION_ROOT", attacker["root"]):
            with self.assertRaisesRegex(rc4_gate.GateError,
                                        "TRUST_ROOT_UNIDENTIFIED|INSIDE_REPOSITORY|NOT_OS_SCOPE"):
                trust_rc4.load_trust_store_rc4(attacker["root"], require_owner=True)

    def test_legacy_store_path_refused_for_attacker_and_operator_alike(self):
        with self.assertRaisesRegex(rc4_gate.GateError, "LEGACY_TRUST_STORE_REJECTED"):
            trust_rc4.load_trust_store_rc4(trust_rc4.LEGACY_ROOT, require_owner=True)

    @unittest.expectedFailure
    def test_known_gap_attacker_store_under_programdata_with_plausible_names(self):
        """DESIRED property: an attacker-created store under the OS-scope root is refused.

        Currently NOT enforced: on Windows the ACL check is advisory (location only), and
        no independently pinned institutional key fingerprint exists. Reported as defect
        D3; expectedFailure marks the gap and flips to 'unexpected success' once fixed.
        """
        attacker = build_store(Path(self.tmp.name) / "ProgramData" / "InstitutionalC1TrustRC4")
        for field in ("institution_name", "approving_authority", "key_custodian",
                      "provisioning_reference", "owner_identity"):
            attacker["binding"][field] = "Plausible University Research Office"
        import json
        policy = attacker["policy"]
        policy["owner_identity"] = "Plausible University Research Office"
        for key in policy["keys"]:
            key["custodian"] = {"supervisor-1": "Dr A Approver", "launch-1": "B Operator",
                                "time-1": "C Timekeeper"}[key["key_id"]]
        from src.research.c1_film_launch_rc2.trust_policy import policy_digest
        owner_key, owner_pem = _key()
        policy.pop("policy_signature", None)
        policy["policy_digest"] = policy_digest(policy)
        policy["policy_signature"] = _sign(owner_key, policy, ("policy_signature",))
        attacker["binding"].update(policy_digest=policy["policy_digest"],
                                   policy_owner_public_key_pem=owner_pem)
        root = attacker["root"]
        (root / "policy.json").write_text(json.dumps(policy), encoding="utf-8")
        (root / "c1_rc4_binding.json").write_text(json.dumps(attacker["binding"]),
                                                  encoding="utf-8")
        env = dict(os.environ, ProgramData=str(root.parent))
        with mock.patch.dict(os.environ, env), \
                mock.patch.object(trust_rc4, "PRODUCTION_ROOT", root):
            with self.assertRaises(rc4_gate.GateError):
                trust_rc4.load_trust_store_rc4(root, require_owner=True)


class ClockEvidenceTests(Base):
    """Real RC3 clock-attestation reader (reused by RC4) against synthetic evidence."""

    def _ntp(self, offset):
        return {"offset_seconds": offset, "server": "synthetic.invalid",
                "reference_utc": "x", "host_utc": "x", "roundtrip_seconds": 0.01}

    def trust(self, root=None):
        return rc4_gate._clock_trust(self.store["policy"], root or self.store["root"],
                                     NOW, 1.0)

    def test_missing_attestation_not_established(self):
        self.assertEqual(self.trust(), "NOT_ESTABLISHED")

    def test_valid_attestation_verified_and_invalid_variants_refused(self):
        root = self.store["root"]
        ts3.write_host_clock_attestation(self.store["keys"]["time-1"], "time-1",
                                         self._ntp(0.1), trust_store_root=root)
        self.assertEqual(rc4_gate._clock_trust(self.store["policy"], root,
                                               ts3.datetime.now(ts3.timezone.utc), 1.0),
                         "VERIFIED")
        future = ts3.datetime.now(ts3.timezone.utc) + timedelta(days=30)
        self.assertEqual(rc4_gate._clock_trust(self.store["policy"], root, future, 1.0),
                         "NOT_ESTABLISHED")
        with self.assertRaises(Exception):
            ts3.write_host_clock_attestation(self.store["keys"]["time-1"], "time-1",
                                             self._ntp(5.0), trust_store_root=root)
        # Signed by a key without TIME_AUTHORITY role -> refused.
        ts3.write_host_clock_attestation(self.store["keys"]["launch-1"], "launch-1",
                                         self._ntp(0.1), trust_store_root=root)
        self.assertEqual(rc4_gate._clock_trust(self.store["policy"], root,
                                               ts3.datetime.now(ts3.timezone.utc), 1.0),
                         "NOT_ESTABLISHED")


class EndToEndSyntheticTests(Base):
    def test_accept_then_replay_refused(self):
        grant = self.synthetic_grant()
        self.assertEqual(grant.release_digest, self.digest)
        with self.assertRaisesRegex(rc4_gate.GateError, "TIME_NONCE_REPLAY"):
            self.call()

    def test_trainer_construction_requires_grant_and_refuses_synthetic_grant(self):
        from src.research.c1_film.readiness import ReadinessError
        from src.research.c1_film.training_engine import Trainer
        contract = {"mode": "REAL"}
        with mock.patch("src.research.c1_film.training_engine.validate_contract"):
            with self.assertRaises(ReadinessError):
                Trainer(contract)
            with self.assertRaisesRegex(rc4_gate.GateError, "SYNTHETIC_GRANT_CANNOT_TRAIN"):
                Trainer(contract, grant=self.synthetic_grant())

    def test_loader_factory_refuses_synthetic_grant_before_any_data_read(self):
        import json
        from src.research.c1_film.train_driver import real_loader_factory
        from src.research.c1_film_launch import release_identity as rc1_rid
        protocol = json.loads(rc1_rid.PROTOCOL_PATH.read_text(encoding="utf-8-sig"))
        with mock.patch("src.data.multidomain_dataset.MultiDomainDataset") as dataset:
            with self.assertRaisesRegex(rc4_gate.GateError, "SYNTHETIC_GRANT_CANNOT_ACCESS_DATA"):
                real_loader_factory(protocol, grant=self.synthetic_grant())
            dataset.assert_not_called()


if __name__ == "__main__":
    unittest.main()
