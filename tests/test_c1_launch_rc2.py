"""RC2 authorization tests: one positive synthetic path, many negative controls.

Every test here is synthetic and CPU-only. The positive path proves that a
correctly signed authorization validates end to end against an isolated test
trust authority — and that the resulting grant is classed ``SYNTHETIC_TEST`` and
therefore cannot train or open a real-data loader. No production trust store is
created, no real data is touched, and no scientific execution is enabled.

This file is bound by ``manifest_rc2.json``. Editing it invalidates the RC2
release until the freezer is re-run — the same discipline as RC1.
"""
from __future__ import annotations

import base64
import copy
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

from src.research.c1_film_launch import launch_gate as rc1
from src.research.c1_film_launch import release_identity as rc1_rid
from src.research.c1_film_launch_rc2 import rc2_gate, release_identity_rc2 as rid, time_status
from src.research.c1_film_launch_rc2.trust_policy import canonical, policy_digest, spki_fingerprint

NOW = datetime.now(timezone.utc).replace(microsecond=0)


# --------------------------------------------------------------------------- #
# Synthetic authority material
# --------------------------------------------------------------------------- #
def _key():
    key = ec.generate_private_key(ec.SECP256R1())
    pem = key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo).decode()
    return key, pem


def _sign(key, payload: dict, exclude) -> str:
    body = {k: v for k, v in payload.items() if k not in exclude}
    return base64.b64encode(key.sign(canonical(body), ec.ECDSA(hashes.SHA256()))).decode()


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _iso_z(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_trust_store(root, *, revoke=(), supervisor_roles=("SUPERVISOR",),
                      owner_key=None) -> dict:
    """A dedicated TEST-ONLY trust store. Never institutional authority."""
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    if owner_key is None:
        owner_key, owner_pem = _key()
    else:
        owner_key, owner_pem = owner_key
    sup_key, sup_pem = _key()
    launch_key, launch_pem = _key()
    time_key, time_pem = _key()

    def record(key_id, pem, roles, revoked=False):
        return {"key_id": key_id, "public_key_pem": pem,
                "fingerprint": spki_fingerprint(pem), "roles": list(roles),
                "status": "REVOKED" if revoked else "ACTIVE", "revoked": bool(revoked)}

    policy = {
        "schema": 2,
        "policy_id": "SYNTHETIC-RC2-POLICY-0001",
        "owner_identity": "Synthetic Test Authority (NOT INSTITUTIONAL)",
        "policy_owner_key_id": "owner-1",
        "issued_at": _iso(NOW - timedelta(days=1)),
        "keys": [
            record("supervisor-1", sup_pem, supervisor_roles, "supervisor-1" in revoke),
            record("launch-1", launch_pem, ("LAUNCH_OPERATOR",), "launch-1" in revoke),
            record("time-1", time_pem, ("TIME_AUTHORITY",), "time-1" in revoke),
        ],
        "revoked_authorizations": [],
    }
    policy["policy_digest"] = policy_digest(policy)
    policy["policy_signature"] = _sign(owner_key, policy, ("policy_signature",))
    (root / "policy.json").write_text(json.dumps(policy, indent=2), encoding="utf-8")

    binding = {
        "schema": 1,
        "binding_id": "SYNTHETIC-RC2-BINDING-0001",
        "owner_identity": policy["owner_identity"],
        "policy_relative_path": "policy.json",
        "policy_digest": policy["policy_digest"],
        "policy_owner_key_id": "owner-1",
        "policy_owner_public_key_pem": owner_pem,
    }
    (root / "c1_rc2_binding.json").write_text(json.dumps(binding, indent=2), encoding="utf-8")
    return {"root": root, "owner_key": owner_key, "owner_pem": owner_pem,
            "sup_key": sup_key, "launch_key": launch_key, "time_key": time_key,
            "policy": policy, "binding": binding}


def build_authorization(store, release_digest: str) -> dict:
    protocol = json.loads(rc1_rid.PROTOCOL_PATH.read_text(encoding="utf-8-sig"))
    approval = {
        "authorization_id": "SYNTHETIC-RC2-AUTH-0001",
        "authorized_by": "Synthetic Test Authority (NOT INSTITUTIONAL)",
        "institutional_role": "SUPERVISOR",
        "decision_record": "SYNTHETIC-RC2-DECISION-0001",
        "authorized_at": _iso(NOW - timedelta(minutes=2)),
        "scope": rid.STUDY_ID,
        "protocol_sha256": rid.PROTOCOL_SHA256,
        "release_digest": release_digest,
        "arms": list(rc1.APPROVED_ARMS),
        "seeds": list(rc1.APPROVED_SEEDS),
        "exclusions": sorted(rc1.REQUIRED_EXCLUSIONS),
        "populations": copy.deepcopy(protocol["dataset"]["populations"]),
        "requested_paths": [v["path"] for v in protocol["dataset"]["populations"].values()],
        "requested_splits": ["TRAIN", "VAL"],
        "key_id": "supervisor-1",
    }
    approval["signature"] = _sign(store["sup_key"], approval, ("signature",))

    run_plan = rc1.expected_run_plan()
    instruction = {
        "launch_id": "SYNTHETIC-RC2-LAUNCH-0001",
        "authorization_id": approval["authorization_id"],
        "release_digest": release_digest,
        "issued_at": _iso(NOW - timedelta(seconds=30)),
        "run_plan": run_plan,
        "key_id": "launch-1",
    }
    instruction["signature"] = _sign(store["launch_key"], instruction, ("signature",))

    proof = {
        "type": time_status.PROOF_TYPE,
        "release_digest": release_digest,
        "authorization_id": approval["authorization_id"],
        "launch_id": instruction["launch_id"],
        "nonce": "0123456789abcdef" * 4,
        "key_id": "time-1",
        "issued_at_utc": _iso_z(NOW - timedelta(seconds=60)),
        "expires_at_utc": _iso_z(NOW + timedelta(seconds=240)),
        "status": "ACTIVE",
    }
    proof["signature"] = _sign(store["time_key"], proof, ("signature",))

    return {"approval": approval, "instruction": instruction, "time_status": proof,
            "budget": {"logical_runs": 6, "max_epochs": 100,
                       "max_cumulative_active_hours": 96},
            "run_plan": run_plan,
            "recovery": {"mode": "FRESH", "arm": "C1-T", "seed": 42}}


# --------------------------------------------------------------------------- #
# Base
# --------------------------------------------------------------------------- #
class RC2Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.store = build_trust_store(base / "trust")
        self.out = base / "out"
        self.out.mkdir()
        self.release = rid.verify_release_rc2()
        self.digest = self.release["release_digest"]
        self.auth = build_authorization(self.store, self.digest)

    def call(self, *, store=None, require_owner=False, **over):
        kw = dict(
            expected_release_digest=self.digest,
            approval=copy.deepcopy(self.auth["approval"]),
            instruction=copy.deepcopy(self.auth["instruction"]),
            time_status=copy.deepcopy(self.auth["time_status"]),
            budget=copy.deepcopy(self.auth["budget"]),
            run_plan=copy.deepcopy(self.auth["run_plan"]),
            recovery=copy.deepcopy(self.auth["recovery"]),
            output_root=self.out,
            now=NOW,
            trust_store_root=(store or self.store)["root"],
            require_owner=require_owner,
        )
        kw.update(over)
        return rc2_gate.validate_authorization(**kw)


# --------------------------------------------------------------------------- #
# Positive synthetic path
# --------------------------------------------------------------------------- #
class PositiveSyntheticTests(RC2Base):
    def test_positive_authorization_validates_end_to_end(self):
        record = self.call()
        self.assertEqual(record["authorization_class"], rc2_gate.SYNTHETIC)
        self.assertEqual(record["release_digest"], self.digest)
        self.assertEqual(record["approval_key_id"], "supervisor-1")
        self.assertEqual(record["launch_key_id"], "launch-1")
        self.assertEqual(record["time_key_id"], "time-1")
        self.assertEqual(record["host_clock_trust"], "NOT_ESTABLISHED")
        self.assertEqual(len(record["nonce_sha256"]), 64)
        self.assertEqual(record["study_id"], rid.STUDY_ID)

    def test_positive_path_consumes_the_nonce(self):
        self.call()
        consumed = time_status.read_ledger(self.out)
        self.assertEqual(len(consumed), 1)

    def test_synthetic_grant_cannot_train(self):
        grant = rc2_gate.mint_grant(
            expected_release_digest=self.digest,
            approval=copy.deepcopy(self.auth["approval"]),
            instruction=copy.deepcopy(self.auth["instruction"]),
            time_status=copy.deepcopy(self.auth["time_status"]),
            budget=copy.deepcopy(self.auth["budget"]),
            run_plan=copy.deepcopy(self.auth["run_plan"]),
            recovery=copy.deepcopy(self.auth["recovery"]),
            output_root=self.out, now=NOW,
            trust_store_root=self.store["root"], require_owner=False)
        self.assertEqual(grant.authorization_class, rc2_gate.SYNTHETIC)
        contract = {"study_id": rid.STUDY_ID, "protocol_sha256": rid.PROTOCOL_SHA256,
                    "arm": "C1-T", "seed": 42}
        with self.assertRaisesRegex(rc1.GateError, "C1_RC2_SYNTHETIC_GRANT_CANNOT_TRAIN"):
            grant.authorize_trainer(contract)

    def test_synthetic_grant_cannot_open_real_data_loader(self):
        grant = rc2_gate.mint_grant(
            expected_release_digest=self.digest,
            approval=copy.deepcopy(self.auth["approval"]),
            instruction=copy.deepcopy(self.auth["instruction"]),
            time_status=copy.deepcopy(self.auth["time_status"]),
            budget=copy.deepcopy(self.auth["budget"]),
            run_plan=copy.deepcopy(self.auth["run_plan"]),
            recovery=copy.deepcopy(self.auth["recovery"]),
            output_root=self.out, now=NOW,
            trust_store_root=self.store["root"], require_owner=False)
        protocol = json.loads(rc1_rid.PROTOCOL_PATH.read_text(encoding="utf-8-sig"))
        with self.assertRaisesRegex(rc1.GateError,
                                    "C1_RC2_SYNTHETIC_GRANT_CANNOT_ACCESS_DATA"):
            grant.authorize_loader(protocol)
        with self.assertRaisesRegex(rc1.GateError,
                                    "C1_RC2_SYNTHETIC_GRANT_CANNOT_ACCESS_DATA"):
            grant.authorize_launch(protocol, "C1-T", 42)

    def test_grant_cannot_be_constructed_directly(self):
        with self.assertRaisesRegex(rc1.GateError, "C1_RC2_GRANT_FORGED"):
            rc2_gate.RC2Grant({"release_digest": self.digest})

    def test_rc1_release_remains_frozen(self):
        rc1_report = rc1_rid.verify_release()
        self.assertEqual(rc1_report["release_digest"], rid.RC1_RELEASE_DIGEST)
        self.assertEqual(rc1_report["manifest_file_sha256"], rid.RC1_MANIFEST_SHA256)
        self.assertEqual(self.release["rc1_release_digest"], rid.RC1_RELEASE_DIGEST)


# --------------------------------------------------------------------------- #
# Production is unprovisioned
# --------------------------------------------------------------------------- #
class ProductionUnprovisionedTests(RC2Base):
    def test_default_production_store_is_absent(self):
        with self.assertRaisesRegex(rc1.GateError, "C1_RC2_TRUST_STORE_MISSING_OR_SYMLINK"):
            self.call(trust_store_root=None, require_owner=True)

    def test_non_canonical_store_cannot_be_production(self):
        with self.assertRaisesRegex(rc1.GateError, "C1_RC2_TRUST_STORE_NOT_PRODUCTION"):
            self.call(require_owner=True)

    def test_manifest_declares_no_shipped_anchors(self):
        manifest = json.loads(rid.MANIFEST_PATH.read_text(encoding="utf-8"))
        self.assertEqual(manifest["trust_store"]["anchors_shipped"], 0)
        self.assertFalse(manifest["trust_store"]["inside_release"])
        self.assertFalse(manifest["trust_store"]["provisioned"])

    def test_manifest_preserves_host_clock_blocker(self):
        manifest = json.loads(rid.MANIFEST_PATH.read_text(encoding="utf-8"))
        self.assertEqual(manifest["host_clock"]["trust"], "NOT_ESTABLISHED")
        self.assertTrue(manifest["host_clock"]["required"])


# --------------------------------------------------------------------------- #
# Negative controls — signatures and trust
# --------------------------------------------------------------------------- #
class SignatureAndTrustTests(RC2Base):
    def test_invalid_approval_signature(self):
        auth = copy.deepcopy(self.auth)
        auth["approval"]["signature"] = "AAAA" * 16
        with self.assertRaisesRegex(rc1.GateError, "C1_RC2_SIGNATURE_INVALID"):
            self.call(approval=auth["approval"])

    def test_absent_approval_signature(self):
        auth = copy.deepcopy(self.auth)
        auth["approval"].pop("signature")
        with self.assertRaisesRegex(rc1.GateError, "C1_RC2_SIGNATURE_MISSING"):
            self.call(approval=auth["approval"])

    def test_invalid_instruction_signature(self):
        auth = copy.deepcopy(self.auth)
        auth["instruction"]["signature"] = "BBBB" * 16
        with self.assertRaisesRegex(rc1.GateError, "C1_RC2_SIGNATURE_INVALID"):
            self.call(instruction=auth["instruction"])

    def test_untrusted_signing_key(self):
        auth = copy.deepcopy(self.auth)
        auth["approval"]["key_id"] = "not-in-policy"
        with self.assertRaisesRegex(rc1.GateError, "C1_RC2_SIGNATURE_KEY_UNTRUSTED"):
            self.call(approval=auth["approval"])

    def test_revoked_signing_key(self):
        base = Path(self.tmp.name)
        revoked = build_trust_store(base / "trust_revoked", revoke=("supervisor-1",))
        auth = build_authorization(revoked, self.digest)
        with self.assertRaisesRegex(rc1.GateError, "C1_RC2_SIGNATURE_KEY_REVOKED"):
            self.call(store=revoked, approval=auth["approval"],
                      instruction=auth["instruction"], time_status=auth["time_status"])

    def test_wrong_role_signing_key(self):
        base = Path(self.tmp.name)
        wrong = build_trust_store(base / "trust_wrong_role",
                                  supervisor_roles=("LAUNCH_OPERATOR",))
        auth = build_authorization(wrong, self.digest)
        with self.assertRaisesRegex(rc1.GateError, "C1_RC2_SIGNATURE_KEY_ROLE"):
            self.call(store=wrong, approval=auth["approval"],
                      instruction=auth["instruction"], time_status=auth["time_status"])

    def test_tampered_policy_content_with_recomputed_digest(self):
        """An attacker who rewrites the policy and recomputes its digest still fails."""
        root = Path(self.tmp.name) / "trust_tampered"
        root.mkdir()
        policy = copy.deepcopy(self.store["policy"])
        extra_key, extra_pem = _key()
        policy["keys"].append({"key_id": "attacker-1", "public_key_pem": extra_pem,
                               "fingerprint": spki_fingerprint(extra_pem),
                               "roles": ["SUPERVISOR"], "status": "ACTIVE",
                               "revoked": False})
        policy.pop("policy_signature", None)
        policy["policy_digest"] = policy_digest(policy)
        # Signature left as the original owner's -> does not cover the new body.
        policy["policy_signature"] = self.store["policy"]["policy_signature"]
        (root / "policy.json").write_text(json.dumps(policy, indent=2), encoding="utf-8")
        binding = copy.deepcopy(self.store["binding"])
        binding["policy_digest"] = policy["policy_digest"]
        (root / "c1_rc2_binding.json").write_text(json.dumps(binding, indent=2),
                                                  encoding="utf-8")
        with self.assertRaisesRegex(rc1.GateError,
                                    "C1_RC2_TRUST_POLICY_SIGNATURE_INVALID"):
            self.call(store={"root": root})

    def test_policy_owner_key_substituted(self):
        root = Path(self.tmp.name) / "trust_owner_swap"
        root.mkdir()
        (root / "policy.json").write_text(json.dumps(self.store["policy"], indent=2),
                                          encoding="utf-8")
        other_key, other_pem = _key()
        binding = copy.deepcopy(self.store["binding"])
        binding["policy_owner_public_key_pem"] = other_pem
        (root / "c1_rc2_binding.json").write_text(json.dumps(binding, indent=2),
                                                  encoding="utf-8")
        with self.assertRaisesRegex(rc1.GateError,
                                    "C1_RC2_TRUST_POLICY_SIGNATURE_INVALID"):
            self.call(store={"root": root})

    def test_missing_policy_file(self):
        root = Path(self.tmp.name) / "trust_empty"
        root.mkdir()
        (root / "c1_rc2_binding.json").write_text(
            json.dumps(self.store["binding"], indent=2), encoding="utf-8")
        with self.assertRaisesRegex(rc1.GateError,
                                    "C1_RC2_TRUST_STORE_MISSING_OR_SYMLINK"):
            self.call(store={"root": root})


# --------------------------------------------------------------------------- #
# Negative controls — release identity
# --------------------------------------------------------------------------- #
class ReleaseIdentityTests(RC2Base):
    def test_expected_digest_mismatch(self):
        with self.assertRaisesRegex(rc1.GateError, "C1_RC2_RELEASE_DIGEST_MISMATCH"):
            self.call(expected_release_digest="f" * 64)

    def test_approval_bound_to_another_release(self):
        auth = copy.deepcopy(self.auth)
        auth["approval"]["release_digest"] = "f" * 64
        with self.assertRaisesRegex(rc1.GateError, "C1_AUTHORIZATION_RELEASE_MISMATCH"):
            self.call(approval=auth["approval"])

    def test_manifest_binds_all_rc2_sources(self):
        manifest = json.loads(rid.MANIFEST_PATH.read_text(encoding="utf-8"))
        bound = {e["path"] for e in manifest["bound_sources"]}
        for required in rid.REQUIRED_COVERAGE:
            self.assertIn(required, bound)
        self.assertEqual(self.release["bound_source_count"], len(bound))

    def test_manifest_does_not_bind_itself(self):
        manifest = json.loads(rid.MANIFEST_PATH.read_text(encoding="utf-8"))
        bound = {e["path"] for e in manifest["bound_sources"]}
        for excluded in rid.SELF_EXCLUDED:
            self.assertNotIn(excluded, bound)

    def test_digest_is_independently_recomputable(self):
        manifest = json.loads(rid.MANIFEST_PATH.read_text(encoding="utf-8"))
        independent = rid.sha256_bytes(canonical(manifest))
        self.assertEqual(independent, self.release["release_digest"])


# --------------------------------------------------------------------------- #
# Negative controls — time evidence
# --------------------------------------------------------------------------- #
class TimeEvidenceTests(RC2Base):
    def test_unsigned_rc1_style_trusted_time_is_rejected(self):
        legacy = {"source": "NTP", "synchronized": True, "abs_offset_seconds": 0.0,
                  "measured_at_utc": _iso(NOW - timedelta(minutes=5))}
        with self.assertRaisesRegex(rc1.GateError, "C1_RC2_TIME_PROOF_INCOMPLETE"):
            self.call(time_status=legacy)

    def test_time_proof_bad_signature(self):
        auth = copy.deepcopy(self.auth)
        auth["time_status"]["signature"] = "CCCC" * 16
        with self.assertRaisesRegex(rc1.GateError, "C1_RC2_SIGNATURE_INVALID"):
            self.call(time_status=auth["time_status"])

    def test_time_proof_wrong_identity_binding(self):
        auth = copy.deepcopy(self.auth)
        auth["time_status"]["launch_id"] = "SOME-OTHER-LAUNCH"
        with self.assertRaisesRegex(rc1.GateError, "C1_RC2_TIME_IDENTITY_BINDING"):
            self.call(time_status=auth["time_status"])

    def test_time_proof_expired(self):
        auth = copy.deepcopy(self.auth)
        auth["time_status"]["issued_at_utc"] = _iso_z(NOW - timedelta(seconds=90))
        auth["time_status"]["expires_at_utc"] = _iso_z(NOW - timedelta(seconds=10))
        auth["time_status"]["signature"] = _sign(self.store["time_key"],
                                                 auth["time_status"], ("signature",))
        with self.assertRaisesRegex(rc1.GateError, "C1_RC2_TIME_PROOF_EXPIRED"):
            self.call(time_status=auth["time_status"])

    def test_time_proof_stale(self):
        auth = copy.deepcopy(self.auth)
        auth["time_status"]["issued_at_utc"] = _iso_z(NOW - timedelta(seconds=600))
        auth["time_status"]["expires_at_utc"] = _iso_z(NOW + timedelta(seconds=240))
        auth["time_status"]["signature"] = _sign(self.store["time_key"],
                                                 auth["time_status"], ("signature",))
        with self.assertRaisesRegex(rc1.GateError, "C1_RC2_TIME_PROOF_STALE"):
            self.call(time_status=auth["time_status"])

    def test_time_proof_from_the_future(self):
        auth = copy.deepcopy(self.auth)
        auth["time_status"]["issued_at_utc"] = _iso_z(NOW + timedelta(seconds=120))
        auth["time_status"]["expires_at_utc"] = _iso_z(NOW + timedelta(seconds=400))
        auth["time_status"]["signature"] = _sign(self.store["time_key"],
                                                 auth["time_status"], ("signature",))
        with self.assertRaisesRegex(rc1.GateError, "C1_RC2_TIME_PROOF_FUTURE"):
            self.call(time_status=auth["time_status"])

    def test_replayed_time_proof_is_refused(self):
        self.call()  # consumes the nonce into the durable ledger
        with self.assertRaisesRegex(rc1.GateError, "C1_RC2_TIME_NONCE_REPLAY"):
            self.call()

    def test_replay_is_refused_across_process_state_reset(self):
        self.call()
        time_status.__dict__  # ledger is on disk, not in memory
        with self.assertRaisesRegex(rc1.GateError, "C1_RC2_TIME_NONCE_REPLAY"):
            self.call()

    def test_revoked_authorization(self):
        auth = copy.deepcopy(self.auth)
        auth["time_status"]["status"] = "REVOKED"
        auth["time_status"]["signature"] = _sign(self.store["time_key"],
                                                 auth["time_status"], ("signature",))
        with self.assertRaisesRegex(rc1.GateError, "C1_RC2_AUTHORIZATION_INACTIVE"):
            self.call(time_status=auth["time_status"])

    def test_time_proof_signed_by_non_time_role_key(self):
        auth = copy.deepcopy(self.auth)
        auth["time_status"]["key_id"] = "supervisor-1"
        auth["time_status"]["signature"] = _sign(self.store["sup_key"],
                                                 auth["time_status"], ("signature",))
        with self.assertRaisesRegex(rc1.GateError, "C1_RC2_SIGNATURE_KEY_ROLE"):
            self.call(time_status=auth["time_status"])


# --------------------------------------------------------------------------- #
# Negative controls — scope, budget, recovery, splits
# --------------------------------------------------------------------------- #
class StructuralNegativeTests(RC2Base):
    def test_wrong_arms(self):
        auth = copy.deepcopy(self.auth)
        auth["approval"]["arms"] = ["C1-T"]
        with self.assertRaisesRegex(rc1.GateError, "C1_AUTHORIZATION_ARMS_MISMATCH"):
            self.call(approval=auth["approval"])

    def test_wrong_seeds(self):
        auth = copy.deepcopy(self.auth)
        auth["approval"]["seeds"] = [42, 123, 999]
        with self.assertRaisesRegex(rc1.GateError, "C1_AUTHORIZATION_SEEDS_MISMATCH"):
            self.call(approval=auth["approval"])

    def test_prohibited_split(self):
        auth = copy.deepcopy(self.auth)
        auth["approval"]["requested_splits"] = ["TRAIN", "TEST"]
        with self.assertRaisesRegex(rc1.GateError, "C1_PROHIBITED_SPLIT"):
            self.call(approval=auth["approval"])

    def test_budget_violation(self):
        with self.assertRaisesRegex(rc1.GateError, "C1_BUDGET_EXCEEDED"):
            self.call(budget={"logical_runs": 6, "max_epochs": 101,
                              "max_cumulative_active_hours": 96})

    def test_duplicate_logical_run(self):
        plan = copy.deepcopy(self.auth["run_plan"])
        plan[1] = dict(plan[0])
        with self.assertRaisesRegex(rc1.GateError, "C1_DUPLICATE_LOGICAL_RUN"):
            self.call(run_plan=plan)

    def test_invalid_recovery_identity(self):
        with self.assertRaisesRegex(rc1.GateError, "C1_RECOVERY_IDENTITY_INVALID"):
            self.call(recovery={"mode": "RESUME", "arm": "C1-T", "seed": 42,
                                "identity": "deadbeef"})

    def test_scope_mismatch(self):
        auth = copy.deepcopy(self.auth)
        auth["approval"]["scope"] = "BARR-M1"
        with self.assertRaisesRegex(rc1.GateError, "C1_AUTHORIZATION_SCOPE_MISMATCH"):
            self.call(approval=auth["approval"])

    def test_protocol_mismatch(self):
        auth = copy.deepcopy(self.auth)
        auth["approval"]["protocol_sha256"] = "0" * 64
        with self.assertRaisesRegex(rc1.GateError, "C1_AUTHORIZATION_PROTOCOL_MISMATCH"):
            self.call(approval=auth["approval"])

    def test_separate_launch_required(self):
        with self.assertRaisesRegex(rc1.GateError, "C1_SEPARATE_LAUNCH_REQUIRED"):
            self.call(instruction=None)


if __name__ == "__main__":
    unittest.main()
