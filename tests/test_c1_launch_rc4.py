"""RC4 release-identity and authorization tests.

Every key, store, approval and time proof here is a SYNTHETIC TEST FIXTURE created in
a temporary directory. None is an institutional credential, none is ever written to
a production trust directory, and no test can mint a PRODUCTION grant from fixtures
except through an explicitly labelled, in-process patch of the trust loader.
"""
from __future__ import annotations

import base64
import copy
import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

from src.research.c1_film_launch import launch_gate as rc1
from src.research.c1_film_launch import release_identity as rc1_rid
from src.research.c1_film_launch_rc2 import release_identity_rc2 as rc2_rid
from src.research.c1_film_launch_rc2 import time_status
from src.research.c1_film_launch_rc2.trust_policy import canonical, policy_digest, spki_fingerprint
from src.research.c1_film_launch_rc3 import rc3_gate
from src.research.c1_film_launch_rc3 import release_identity_rc3 as rc3_rid
from src.research.c1_film_launch_rc4 import rc4_gate, trust_rc4
from src.research.c1_film_launch_rc4 import release_identity_rc4 as rid

ROOT = Path(__file__).resolve().parents[1]
NOW = datetime.now(timezone.utc).replace(microsecond=0)

# Independent literals: the frozen predecessor identities must never change.
RC1_DIGEST = "1aec5e17ee79eb8845ea36808d5a087ea99c091be798ec5a41b4e412f93ff9c1"
RC2_DIGEST = "54794efc6d99d94fae9eaebd992e01e4e9923b5055d024ea1d5f02a8a5e737ed"
RC3_DIGEST = "54d1273a53db7dae58118a4bb69c2a96ba2e474a72512a9dccb4c98c9513549f"
PROTOCOL_SHA = "531e3eb255a66381201d1aaf49bbe55abfdbe529640f5c584ef100d298087a61"


def _key():
    key = ec.generate_private_key(ec.SECP256R1())
    pem = key.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode()
    return key, pem


def _sign(key, payload: dict, exclude=("signature",)) -> str:
    body = {k: v for k, v in payload.items() if k not in exclude}
    return base64.b64encode(key.sign(canonical(body), ec.ECDSA(hashes.SHA256()))).decode()


def _iso_z(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_store(root, *, revoke=(), revoked_authorizations=(), approver="Synthetic Approver",
                operator="Synthetic Operator", researcher="Synthetic Researcher") -> dict:
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    owner_key, owner_pem = _key()
    keys = {name: _key() for name in ("supervisor-1", "launch-1", "time-1")}
    spec = {"supervisor-1": ("SUPERVISOR", approver), "launch-1": ("LAUNCH_OPERATOR", operator),
            "time-1": ("TIME_AUTHORITY", "Synthetic Time Authority")}

    def record(key_id):
        pem = keys[key_id][1]
        return {"key_id": key_id, "public_key_pem": pem, "fingerprint": spki_fingerprint(pem),
                "roles": [spec[key_id][0]], "custodian": spec[key_id][1],
                "status": "REVOKED" if key_id in revoke else "ACTIVE",
                "revoked": key_id in revoke}

    policy = {"schema": 2, "policy_id": "SYNTHETIC-RC4-POLICY",
              "owner_identity": "SYNTHETIC TEST AUTHORITY (NOT INSTITUTIONAL)",
              "policy_owner_key_id": "owner-1",
              "keys": [record(k) for k in keys],
              "revoked_authorizations": list(revoked_authorizations)}
    policy["policy_digest"] = policy_digest(policy)
    policy["policy_signature"] = _sign(owner_key, policy, ("policy_signature",))
    (root / "policy.json").write_text(json.dumps(policy), encoding="utf-8")
    binding = {"schema": 1, "binding_id": "SYNTHETIC-RC4-BINDING",
               "study_scope": rid.STUDY_ID, "researcher_identity": researcher,
               "owner_identity": policy["owner_identity"],
               "institution_name": "SYNTHETIC TEST INSTITUTION",
               "approving_authority": "SYNTHETIC TEST APPROVER",
               "key_custodian": "SYNTHETIC TEST CUSTODIAN",
               "provisioning_reference": "SYNTHETIC-NOT-A-PROVISIONING-RECORD",
               "policy_relative_path": "policy.json", "policy_digest": policy["policy_digest"],
               "policy_owner_key_id": "owner-1", "policy_owner_public_key_pem": owner_pem}
    (root / "c1_rc4_binding.json").write_text(json.dumps(binding), encoding="utf-8")
    return {"root": root, "keys": {k: v[0] for k, v in keys.items()},
            "policy": policy, "binding": binding}


def build_authorization(store, digest: str) -> dict:
    protocol = json.loads(rc1_rid.PROTOCOL_PATH.read_text(encoding="utf-8-sig"))
    approval = {
        "authorization_id": "SYNTHETIC-RC4-AUTH-0001",
        "authorized_by": "SYNTHETIC TEST AUTHORITY", "institutional_role": "SUPERVISOR",
        "decision_record": "SYNTHETIC-RC4-DECISION-0001",
        "authorized_at": (NOW - timedelta(minutes=2)).isoformat(),
        "scope": rid.STUDY_ID, "protocol_sha256": PROTOCOL_SHA,
        "release_id": rid.RELEASE_ID, "release_digest": digest,
        "arms": list(rc1.APPROVED_ARMS), "seeds": list(rc1.APPROVED_SEEDS),
        "exclusions": sorted(rc1.REQUIRED_EXCLUSIONS),
        "populations": copy.deepcopy(protocol["dataset"]["populations"]),
        "requested_paths": [v["path"] for v in protocol["dataset"]["populations"].values()],
        "requested_splits": ["TRAIN", "VAL"], "key_id": "supervisor-1",
    }
    approval["signature"] = _sign(store["keys"]["supervisor-1"], approval)
    run_plan = rc1.expected_run_plan()
    instruction = {"launch_id": "SYNTHETIC-RC4-LAUNCH-0001",
                   "authorization_id": approval["authorization_id"], "release_digest": digest,
                   "issued_at": (NOW - timedelta(seconds=30)).isoformat(),
                   "run_plan": run_plan, "key_id": "launch-1"}
    instruction["signature"] = _sign(store["keys"]["launch-1"], instruction)
    proof = {"type": time_status.PROOF_TYPE, "release_digest": digest,
             "authorization_id": approval["authorization_id"],
             "launch_id": instruction["launch_id"], "nonce": "0123456789abcdef" * 4,
             "key_id": "time-1", "issued_at_utc": _iso_z(NOW - timedelta(seconds=60)),
             "expires_at_utc": _iso_z(NOW + timedelta(seconds=240)), "status": "ACTIVE"}
    proof["signature"] = _sign(store["keys"]["time-1"], proof)
    return {"approval": approval, "instruction": instruction, "time_status": proof,
            "budget": {"logical_runs": 6, "max_epochs": 100, "max_cumulative_active_hours": 96},
            "run_plan": run_plan, "recovery": {"mode": "FRESH", "arm": "C1-T", "seed": 42}}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.store = build_store(base / "trust")
        self.out = base / "out"
        self.out.mkdir()
        self.digest = rid.verify_release_rc4()["release_digest"]
        self.auth = build_authorization(self.store, self.digest)

    def kwargs(self, **over):
        kw = dict(expected_release_digest=self.digest,
                  approval=copy.deepcopy(self.auth["approval"]),
                  instruction=copy.deepcopy(self.auth["instruction"]),
                  time_status=copy.deepcopy(self.auth["time_status"]),
                  budget=copy.deepcopy(self.auth["budget"]),
                  run_plan=copy.deepcopy(self.auth["run_plan"]),
                  recovery=copy.deepcopy(self.auth["recovery"]),
                  output_root=self.out, now=NOW, trust_store_root=self.store["root"],
                  require_owner=False)
        kw.update(over)
        return kw

    def call(self, **over):
        return rc4_gate.validate_authorization(**self.kwargs(**over))

    def resigned(self, **changes):
        approval = copy.deepcopy(self.auth["approval"])
        approval.update(changes)
        approval["signature"] = _sign(self.store["keys"]["supervisor-1"], approval)
        return approval

    def refused(self, code, **over):
        with self.assertRaises(rc4_gate.GateError) as ctx:
            self.call(**over)
        self.assertIn(code, str(ctx.exception))

    def synthetic_grant(self):
        return rc4_gate.mint_rc4_grant(**self.kwargs())


class ReleaseIdentityTests(Base):
    def test_correct_successor_identity_accepted(self):
        record = self.call()
        self.assertEqual(record["release_id"], rid.RELEASE_ID)
        self.assertEqual(record["release_digest"], self.digest)
        self.assertEqual(record["authorization_class"], rc4_gate.SYNTHETIC)
        self.assertEqual(record["protocol_sha256"], PROTOCOL_SHA)
        self.assertNotIn(self.digest, (RC1_DIGEST, RC2_DIGEST, RC3_DIGEST))
        self.assertEqual(record["supersedes"], {"rc1": RC1_DIGEST, "rc2": RC2_DIGEST,
                                                "rc3": RC3_DIGEST})

    def test_wrong_digest_rejected(self):
        self.refused("C1_RC4_RELEASE_DIGEST_MISMATCH", expected_release_digest="0" * 64)
        self.refused("C1_RC4_RELEASE_DIGEST_MISMATCH", expected_release_digest=None)

    def test_predecessor_identity_never_substitutes(self):
        for digest in (RC1_DIGEST, RC2_DIGEST, RC3_DIGEST):
            self.refused("C1_RC4_PREDECESSOR_IDENTITY_REJECTED", expected_release_digest=digest)
        self.refused("C1_RC4_PREDECESSOR_IDENTITY_REJECTED",
                     approval=self.resigned(release_digest=RC2_DIGEST))
        self.refused("C1_RC4_PREDECESSOR_IDENTITY_REJECTED",
                     approval=self.resigned(release_id=rc3_rid.RELEASE_ID))
        self.refused("C1_RC4_APPROVAL_RELEASE_ID_MISMATCH",
                     approval=self.resigned(release_id="UNKNOWN"))
        self.refused("C1_RC4_APPROVAL_RELEASE_ID_MISMATCH",
                     approval=self.resigned(release_id=None))

    def test_frozen_rc3_still_exhibits_the_defect_and_rc4_does_not(self):
        with self.assertRaises(rc3_gate.GateError) as ctx:
            rc3_gate.mint_rc3_grant(expected_release_digest=RC3_DIGEST, approval={},
                                    instruction={}, time_status={}, budget={}, run_plan=[],
                                    recovery={})
        self.assertIn("C1_RC2_RELEASE_DIGEST_MISMATCH", str(ctx.exception))
        self.assertEqual(self.call()["release_digest"], self.digest)

    def _tampered(self, mutate):
        manifest = json.loads(rid.MANIFEST_PATH.read_text(encoding="utf-8"))
        mutate(manifest)
        path = Path(self.tmp.name) / "tampered_manifest.json"
        path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return path

    def test_tampered_manifest_rejected(self):
        def alter_hash(m):
            m["bound_sources"][0]["sha256"] = "0" * 64
        path = self._tampered(alter_hash)
        with self.assertRaisesRegex(rid.ReleaseIdentityError, "SOURCE_MODIFIED"):
            rid.verify_release_rc4(path, require_published=False)
        with self.assertRaisesRegex(rid.ReleaseIdentityError, "SOURCE_MODIFIED|STALE"):
            rid.verify_release_rc4(path, require_published=True)

        path = self._tampered(lambda m: m.__setitem__("release_id", rc3_rid.RELEASE_ID))
        with self.assertRaisesRegex(rid.ReleaseIdentityError, "IDENTITY_HEADER_DRIFT"):
            rid.verify_release_rc4(path, require_published=False)
        path = self._tampered(lambda m: m.__setitem__("code_digest", "0" * 64))
        with self.assertRaisesRegex(rid.ReleaseIdentityError, "CODE_DIGEST_MISMATCH"):
            rid.verify_release_rc4(path, require_published=False)
        path = self._tampered(lambda m: m["protocol"].__setitem__("sha256", "0" * 64))
        with self.assertRaisesRegex(rid.ReleaseIdentityError, "PROTOCOL_BINDING_MISMATCH"):
            rid.verify_release_rc4(path, require_published=False)
        path = self._tampered(lambda m: m["supersedes"]["rc3"].__setitem__(
            "release_digest", "0" * 64))
        with self.assertRaisesRegex(rid.ReleaseIdentityError, "PREDECESSOR_PIN_MISMATCH"):
            rid.verify_release_rc4(path, require_published=False)
        path = self._tampered(lambda m: m["bound_sources"][0].__setitem__("path", "../x"))
        with self.assertRaisesRegex(rid.ReleaseIdentityError, "BOUND_PATH_INVALID|COVERAGE"):
            rid.verify_release_rc4(path, require_published=False)
        # Any manifest edit that keeps every check valid still changes the digest.
        path = self._tampered(lambda m: m["trust_model"].__setitem__("anchors_shipped", 1))
        with self.assertRaisesRegex(rid.ReleaseIdentityError, "STALE"):
            rid.verify_release_rc4(path, require_published=True)

    def test_digest_scheme_is_not_self_referential(self):
        manifest = json.loads(rid.MANIFEST_PATH.read_text(encoding="utf-8"))
        self.assertNotIn(self.digest, json.dumps(manifest))
        paths = {e["path"] for e in manifest["bound_sources"]}
        for excluded in manifest["self_excluded"]:
            self.assertNotIn(excluded, paths)
        recomputed = hashlib.sha256(rid.canonical_json(manifest)).hexdigest()
        self.assertEqual(recomputed, self.digest)

    def test_original_releases_unchanged(self):
        self.assertEqual(rc1_rid.verify_release()["release_digest"], RC1_DIGEST)
        self.assertEqual(rc2_rid.verify_release()["release_digest"], RC2_DIGEST)
        self.assertEqual(rc3_rid.verify_release_rc3()["release_digest"], RC3_DIGEST)
        for pin in rid.PREDECESSORS.values():
            self.assertEqual(rid.sha256_file(ROOT / pin["manifest_path"]), pin["manifest_sha256"])
        self.assertEqual(rid.sha256_file(rid.PROTOCOL_PATH), PROTOCOL_SHA)


class TrustAndSignatureTests(Base):
    def test_wrong_signing_authority_rejected(self):
        approval = self.resigned(key_id="time-1")  # signed by a TIME_AUTHORITY-only key
        approval["signature"] = _sign(self.store["keys"]["time-1"], approval)
        self.refused("SIGNATURE_KEY_ROLE", approval=approval)
        self.refused("SIGNATURE_KEY_UNTRUSTED", approval=self.resigned(key_id="nobody"))

    def test_invalid_signature_rejected(self):
        approval = copy.deepcopy(self.auth["approval"])
        approval["authorized_by"] = "SOMEONE ELSE"  # content changed after signing
        self.refused("SIGNATURE_INVALID", approval=approval)
        attacker, _ = _key()
        forged = self.resigned()
        forged["signature"] = _sign(attacker, forged)
        self.refused("SIGNATURE_INVALID", approval=forged)
        unsigned = self.resigned()
        del unsigned["signature"]
        self.refused("SIGNATURE_MISSING", approval=unsigned)

    def test_revoked_key_authorization_and_expiry_refused(self):
        store = build_store(Path(self.tmp.name) / "revoked_key", revoke=("supervisor-1",))
        self.refused("SIGNATURE_KEY_REVOKED", trust_store_root=store["root"])
        store = build_store(Path(self.tmp.name) / "revoked_auth",
                            revoked_authorizations=["SYNTHETIC-RC4-AUTH-0001"])
        self.refused("C1_RC4_AUTHORIZATION_REVOKED", trust_store_root=store["root"])
        past = (NOW - timedelta(minutes=1)).isoformat()
        self.refused("C1_RC4_APPROVAL_EXPIRED", approval=self.resigned(expires_at=past))

    def test_separation_of_duties_enforced(self):
        for kwargs in ({"operator": "Synthetic Approver"}, {"researcher": "synthetic  approver"}):
            store = build_store(Path(self.tmp.name) / ("sep" + str(len(kwargs))), **kwargs)
            auth = build_authorization(store, self.digest)
            with self.assertRaises(rc4_gate.GateError) as ctx:
                rc4_gate.validate_authorization(**self.kwargs(
                    trust_store_root=store["root"], approval=auth["approval"],
                    instruction=auth["instruction"], time_status=auth["time_status"]))
            self.assertIn("C1_RC4_SEPARATION_OF_DUTIES", str(ctx.exception))

    def test_tampered_policy_refused(self):
        path = self.store["root"] / "policy.json"
        policy = json.loads(path.read_text(encoding="utf-8"))
        policy["keys"][0]["roles"] = ["SUPERVISOR", "TIME_AUTHORITY", "LAUNCH_OPERATOR"]
        path.write_text(json.dumps(policy), encoding="utf-8")
        self.refused("TRUST_POLICY_DIGEST")

    def test_missing_or_unidentified_production_root_refused(self):
        missing = Path(self.tmp.name) / "does_not_exist"
        with mock.patch.object(trust_rc4, "PRODUCTION_ROOT", missing):
            self.refused("C1_RC4_TRUST_ROOT_MISSING", require_owner=True, trust_store_root=None)
        # The shipped default must be outside the repository and never the legacy root.
        self.assertFalse(trust_rc4._same(trust_rc4.PRODUCTION_ROOT, trust_rc4.LEGACY_ROOT))
        with self.assertRaises(ValueError):
            trust_rc4.PRODUCTION_ROOT.resolve().relative_to(ROOT)
        self.refused("C1_RC4_TRUST_STORE_NOT_PRODUCTION", require_owner=True)
        # A fixture store placed at the production path is still refused as unidentified.
        with mock.patch.object(trust_rc4, "PRODUCTION_ROOT", self.store["root"]), \
                mock.patch.object(trust_rc4, "assert_policy_owner",
                                  return_value={"owner_enforcement": "TEST"}):
            self.refused("C1_RC4_TRUST_ROOT_UNIDENTIFIED", require_owner=True,
                         trust_store_root=None)
            self.refused("C1_RC4_SYNTHETIC_STORE_AT_PRODUCTION_PATH", require_owner=False)

    def test_legacy_trust_store_never_accepted(self):
        for owner in (True, False):
            self.refused("C1_RC4_LEGACY_TRUST_STORE_REJECTED", require_owner=owner,
                         trust_store_root=trust_rc4.LEGACY_ROOT)

    def test_no_genuine_authorization_means_refusal(self):
        missing = Path(self.tmp.name) / "unprovisioned"
        with mock.patch.object(trust_rc4, "PRODUCTION_ROOT", missing):
            with self.assertRaises(rc4_gate.GateError):
                rc4_gate.mint_rc4_grant(**self.kwargs(require_owner=True, trust_store_root=None))


class TimeAndStructuralTests(Base):
    def test_replayed_nonce_rejected(self):
        self.call()
        self.assertEqual(len(time_status.read_ledger(self.out)), 1)
        self.refused("TIME_NONCE_REPLAY")

    def test_expired_malformed_or_foreign_time_proof_rejected(self):
        proof = copy.deepcopy(self.auth["time_status"])
        proof["expires_at_utc"] = _iso_z(NOW - timedelta(seconds=10))
        proof["signature"] = _sign(self.store["keys"]["time-1"], proof)
        self.refused("TIME_PROOF_EXPIRED", time_status=proof)
        proof = copy.deepcopy(self.auth["time_status"])
        proof["release_digest"] = RC3_DIGEST
        proof["signature"] = _sign(self.store["keys"]["time-1"], proof)
        self.refused("TIME_IDENTITY_BINDING", time_status=proof)
        self.refused("TIME_PROOF_INCOMPLETE", time_status={})

    def test_unauthorized_dataset_access_rejected(self):
        self.refused("C1_PROHIBITED_SPLIT",
                     approval=self.resigned(requested_splits=["TRAIN", "VAL", "TEST"]))
        self.refused("C1_PROHIBITED_SPLIT",
                     approval=self.resigned(requested_paths=["data/test_split.csv"]))
        self.refused("C1_AUTHORIZATION_EXCLUSIONS_MISSING",
                     approval=self.resigned(exclusions=["EXTERNAL"]))

    def test_run_ids_budget_and_plan_preserved(self):
        self.refused("C1_BUDGET_EXCEEDED", budget={"logical_runs": 7, "max_epochs": 100,
                                                  "max_cumulative_active_hours": 96})
        self.refused("C1_BUDGET_EXCEEDED", run_plan=self.auth["run_plan"][:5])
        self.refused("C1_AUTHORIZATION_SEEDS_MISMATCH", approval=self.resigned(seeds=[1, 2, 3]))
        self.refused("C1_RECOVERY_IDENTITY_INVALID",
                     recovery={"mode": "RESUME", "arm": "C1-T", "seed": 42, "identity": "x"})


class GrantEnforcementTests(Base):
    def production_grant(self):
        """TEST-ONLY: forge PRODUCTION class from a synthetic record to exercise grant logic."""
        record = dict(self.synthetic_grant().record, authorization_class=rc4_gate.PRODUCTION)
        return rc4_gate.RC4Grant(record, token=rc4_gate.RC4Grant._MINT)

    def patched(self, clock):
        loaded = (self.store["binding"], self.store["policy"])
        return (mock.patch.object(trust_rc4, "load_trust_store_rc4", return_value=loaded),
                mock.patch.object(rc4_gate, "_clock_trust", return_value=clock))

    def contract(self, **over):
        contract = {"study_id": rid.STUDY_ID, "protocol_sha256": PROTOCOL_SHA,
                    "arm": "C1-T", "seed": 42}
        contract.update(over)
        return contract

    def test_grant_cannot_be_forged_and_reports_rc4_identity(self):
        with self.assertRaises(rc4_gate.GateError):
            rc4_gate.RC4Grant({"release_digest": self.digest})
        grant = self.synthetic_grant()
        self.assertEqual(grant.release_id, rid.RELEASE_ID)
        self.assertEqual(grant.release_digest, self.digest)
        self.assertNotIn(grant.release_digest, rid.PREDECESSOR_DIGESTS)

    def test_synthetic_grant_cannot_train_or_read_data(self):
        grant = self.synthetic_grant()
        with self.assertRaisesRegex(rc4_gate.GateError, "SYNTHETIC_GRANT_CANNOT_TRAIN"):
            grant.authorize_trainer(self.contract())
        protocol = json.loads(rc1_rid.PROTOCOL_PATH.read_text(encoding="utf-8-sig"))
        with self.assertRaisesRegex(rc4_gate.GateError, "SYNTHETIC_GRANT_CANNOT_ACCESS_DATA"):
            grant.authorize_loader(protocol)

    def test_identity_checked_again_at_trainer_authorization(self):
        grant = self.synthetic_grant()
        for changed in ({"release_digest": "1" * 64}, {"code_digest": "2" * 64}):
            report = dict(rid.verify_release_rc4(), **changed)
            with mock.patch.object(rc4_gate, "_verify_release", return_value=report):
                with self.assertRaisesRegex(rc4_gate.GateError, "RELEASE_DIGEST_STALE"):
                    grant.authorize_trainer(self.contract())
        with mock.patch.object(rc4_gate, "_verify_release",
                               side_effect=rc4_gate.GateError("C1_RC4_SOURCE_MODIFIED:x")):
            with self.assertRaisesRegex(rc4_gate.GateError, "SOURCE_MODIFIED"):
                grant.authorize_loader({})
        forged = rc4_gate.RC4Grant(dict(grant.record, release_digest=RC3_DIGEST),
                                   token=rc4_gate.RC4Grant._MINT)
        with self.assertRaisesRegex(rc4_gate.GateError, "PREDECESSOR_IDENTITY_REJECTED"):
            forged.authorize_trainer(self.contract())

    def test_unverified_clock_fails_closed_at_trainer_and_loader(self):
        protocol = json.loads(rc1_rid.PROTOCOL_PATH.read_text(encoding="utf-8-sig"))
        grant = self.production_grant()
        trust, clock = self.patched("NOT_ESTABLISHED")
        with trust, clock:
            with self.assertRaisesRegex(rc4_gate.GateError, "HOST_CLOCK_UNVERIFIED"):
                grant.authorize_trainer(self.contract())
            with self.assertRaisesRegex(rc4_gate.GateError, "HOST_CLOCK_UNVERIFIED"):
                grant.authorize_loader(protocol)

    def test_fixture_grant_logic_with_verified_clock(self):
        protocol = json.loads(rc1_rid.PROTOCOL_PATH.read_text(encoding="utf-8-sig"))
        grant = self.production_grant()
        trust, clock = self.patched("VERIFIED")
        with trust, clock:
            grant.authorize_trainer(self.contract())
            grant.authorize_launch(protocol, "C1-C", 3407)
            with self.assertRaisesRegex(rc4_gate.GateError, "RUN_NOT_AUTHORIZED"):
                grant.authorize_trainer(self.contract(seed=7))
            with self.assertRaisesRegex(rc4_gate.GateError, "AUTHORIZATION_PROTOCOL_MISMATCH"):
                grant.authorize_trainer(self.contract(protocol_sha256="0" * 64))
            with self.assertRaisesRegex(rc4_gate.GateError, "CONTRACT_SCOPE_MISMATCH"):
                grant.authorize_trainer(self.contract(study_id="OTHER"))
            leaky = copy.deepcopy(protocol)
            leaky["dataset"]["populations"]["TEST"] = {"path": "x/test.csv", "n": 1, "sha256": "0"}
            with self.assertRaisesRegex(rc4_gate.GateError, "PROHIBITED_SPLIT"):
                grant.authorize_loader(leaky)

    def test_revocation_after_mint_is_detected(self):
        grant = self.production_grant()
        policy = dict(self.store["policy"], revoked_authorizations=[
            self.auth["approval"]["authorization_id"]])
        with mock.patch.object(trust_rc4, "load_trust_store_rc4",
                               return_value=(self.store["binding"], policy)):
            with self.assertRaisesRegex(rc4_gate.GateError, "POLICY_CHANGED|REVOKED"):
                grant.authorize_trainer(self.contract())


if __name__ == "__main__":
    unittest.main()
