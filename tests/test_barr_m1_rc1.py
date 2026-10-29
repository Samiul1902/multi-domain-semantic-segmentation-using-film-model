"""RC1 synthetic tests. No machine policy installation and no real data reads."""
import base64
import copy
from datetime import datetime, timezone
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
import test_barr_m1_v1_0d_repaired as original

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("rc1", ROOT / "scripts/analysis/barr_m1_release_candidate_v1_0d_rc1.py")
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


class RC1(unittest.TestCase):
    def setUp(self):
        helper = original.Authorization(); helper.setUp()
        self.key = helper.key
        self.payload = helper.payload
        self.payload["harness_sha256"] = r.executable_sha()
        self.now = datetime(2026, 10, 27, tzinfo=timezone.utc)
        raw = self.key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
        encoded = base64.b64encode(raw).decode()
        self.policy = dict(environment="PRODUCTION", keys={"test": dict(public_key=encoded,
            fingerprint_sha256=r.sha(raw), approver="TEST ONLY")}, revoked_authorization_ids=[],
            revoked_key_ids=[], time_public_key=encoded, time_key_sha256=r.sha(raw),
            time_url="https://unconfigured.invalid/barr-time")
        self.approval = self.sign(self.payload, named=True)
        self.launch_payload = dict(purpose="SEPARATE_EXPLICIT_LAUNCH_WORK_ORDER", study_identifier="BARR-M1",
            authorization_id=self.payload["authorization_id"], authorization_sha256=r.sha(r.c.canonical(self.approval)),
            harness_sha256=r.executable_sha(), output_relative=r.OUTPUT_RELATIVE,
            execution_mode="CPU_ONLY_RE_ANALYSIS_ONLY", work_order_id="SYNTHETIC-LAUNCH",
            issued_by="TEST ONLY", issued_at="2026-10-26T01:00:00Z", expires_at="2026-10-28T00:00:00Z")
        self.launch = self.sign(self.launch_payload, named=True)

    def sign(self, payload, named=False):
        envelope = dict(payload=copy.deepcopy(payload), signature=base64.b64encode(self.key.sign(r.c.canonical(payload))).decode())
        if named:
            envelope["key_id"] = "test"
        return envelope

    def verify(self):
        return r.verify_requests(self.approval, self.launch, self.policy, self.now, r.executable_sha())

    def test_positive_verifier_isolated(self):
        self.assertEqual(self.verify(), self.payload)

    def test_signed_synthetic_runner_only_with_mocked_boundaries(self):
        # Production policy and time are replaced ONLY in this test process.
        # The data loader is replaced by fabricated frames; output is temp-only.
        with tempfile.TemporaryDirectory() as tmp, \
             patch.object(r, "machine_policy", return_value=self.policy), \
             patch.object(r, "trusted_time", return_value=self.now), \
             patch.object(r, "load_sources", side_effect=original.fixture) as loader, \
             patch.object(r, "output_root", return_value=Path(tmp)):
            path = r.run_authorized(self.approval, self.launch)
            self.assertTrue(path.is_relative_to(Path(tmp)))
            self.assertEqual(len(json.loads(path.read_bytes())["body"]["result"]["per_case"]), 4957)
            self.assertEqual(path, r.run_authorized(self.approval, self.launch))
            self.assertEqual(loader.call_count, 2)

    def test_production_anchor_absent_no_source_access(self):
        with patch.object(r, "load_sources", side_effect=AssertionError("data must not be read")):
            with self.assertRaisesRegex(r.c.Refusal, "E_AUTHORIZATION_TRUST_ANCHOR_ABSENT"):
                r.run_authorized(self.approval, self.launch)

    def test_missing_authorization_no_source_access(self):
        with patch.object(r, "load_sources", side_effect=AssertionError("data must not be read")):
            with self.assertRaisesRegex(r.c.Refusal, "E_AUTHORIZATION_UNSIGNED"):
                r.run_authorized(None, self.launch)

    def test_approved_true_no_source_access(self):
        with patch.object(r, "load_sources", side_effect=AssertionError("data must not be read")):
            with self.assertRaisesRegex(r.c.Refusal, "E_AUTHORIZATION_UNSIGNED"):
                r.run_authorized({"approved": True}, self.launch)

    def test_wrong_signature(self):
        self.approval["signature"] = base64.b64encode(bytes(64)).decode()
        with self.assertRaisesRegex(r.c.Refusal, "E_AUTHORIZATION_SIGNATURE_INVALID"):
            self.verify()

    def test_untrusted_signer(self):
        self.approval["key_id"] = "unknown"
        with self.assertRaisesRegex(r.c.Refusal, "E_AUTHORIZATION_SIGNATURE_INVALID"):
            self.verify()

    def test_missing_launch(self):
        self.launch = None
        with self.assertRaisesRegex(r.c.Refusal, "E_LAUNCH_REQUIRED"):
            self.verify()

    def test_wrong_launch_signature(self):
        self.launch["signature"] = base64.b64encode(bytes(64)).decode()
        with self.assertRaisesRegex(r.c.Refusal, "E_AUTHORIZATION_SIGNATURE_INVALID"):
            self.verify()

    def test_launch_binds_approval(self):
        self.launch_payload["authorization_sha256"] = "0"*64
        self.launch = self.sign(self.launch_payload, named=True)
        with self.assertRaisesRegex(r.c.Refusal, "E_LAUNCH_SCOPE"):
            self.verify()

    def test_launch_binds_output_path(self):
        self.launch_payload["output_relative"] = "reports/audits"
        self.launch = self.sign(self.launch_payload, named=True)
        with self.assertRaisesRegex(r.c.Refusal, "E_LAUNCH_SCOPE"):
            self.verify()

    def test_clock_not_used_for_approval(self):
        class NoHostNow(datetime):
            @classmethod
            def now(cls, *args, **kwargs):
                raise AssertionError("host clock must not be used")
        with patch.object(r.auth, "datetime", NoHostNow):
            self.verify()

    def test_machine_policy_reader_mocked_registry(self):
        import winreg
        acl = dict(owner="S-1-5-18", rules=[dict(sid="S-1-5-32-544", rights=983103, allow=True)])
        with patch.object(winreg, "OpenKey", return_value=MagicMock()), \
             patch.object(winreg, "QueryValueEx", return_value=(json.dumps(self.policy), winreg.REG_SZ)), \
             patch.object(r.subprocess, "run", return_value=type("Result", (), {"stdout": json.dumps([acl, acl])})()):
            self.assertEqual(r.machine_policy(), self.policy)

    def test_time_service_mocked_transport(self):
        def respond(request, timeout):
            challenge = json.loads(request.data)
            body = self.sign(dict(challenge, utc="2026-10-27T00:00:00Z", authorization_and_launch_active=True))
            return io.BytesIO(r.c.canonical(body))
        opener = MagicMock(); opener.open.side_effect = respond
        with patch.object(r.urllib.request, "build_opener", return_value=opener):
            self.assertEqual(r.trusted_time(self.policy, self.approval, self.launch), self.now)

    def test_time_service_unavailable_no_source_access(self):
        with patch.object(r, "machine_policy", return_value=self.policy), \
             patch.object(r, "trusted_time", side_effect=r.c.Refusal("E_TRUSTED_TIME")), \
             patch.object(r, "load_sources", side_effect=AssertionError("data must not be read")):
            with self.assertRaisesRegex(r.c.Refusal, "E_TRUSTED_TIME"):
                r.run_authorized(self.approval, self.launch)

    def test_runner_wrong_signature_before_source_access(self):
        self.approval["signature"] = base64.b64encode(bytes(64)).decode()
        with patch.object(r, "machine_policy", return_value=self.policy), \
             patch.object(r, "trusted_time", return_value=self.now), \
             patch.object(r, "load_sources", side_effect=AssertionError("data must not be read")):
            with self.assertRaisesRegex(r.c.Refusal, "E_AUTHORIZATION_SIGNATURE_INVALID"):
                r.run_authorized(self.approval, self.launch)

    def challenge(self):
        return dict(nonce="synthetic-nonce", authorization_sha256=r.sha(r.c.canonical(self.approval)),
                    launch_sha256=r.sha(r.c.canonical(self.launch)))

    def time_envelope(self):
        return self.sign(dict(self.challenge(), utc="2026-10-27T00:00:00Z", authorization_and_launch_active=True))

    def test_signed_time_positive(self):
        self.assertEqual(r.check_time_response(self.time_envelope(), self.policy, self.challenge(), .2), self.now)

    def test_wrong_time_signature(self):
        envelope = self.time_envelope(); envelope["signature"] = base64.b64encode(bytes(64)).decode()
        with self.assertRaisesRegex(r.c.Refusal, "E_AUTHORIZATION_SIGNATURE_INVALID"):
            r.check_time_response(envelope, self.policy, self.challenge(), .2)

    def test_time_nonce_replay(self):
        challenge = self.challenge(); challenge["nonce"] = "new"
        with self.assertRaisesRegex(r.c.Refusal, "E_TRUSTED_TIME"):
            r.check_time_response(self.time_envelope(), self.policy, challenge, .2)

    def test_time_stale_round_trip(self):
        with self.assertRaisesRegex(r.c.Refusal, "E_TRUSTED_TIME"):
            r.check_time_response(self.time_envelope(), self.policy, self.challenge(), 11)

    def test_time_revoked(self):
        envelope = self.sign(dict(self.challenge(), utc="2026-10-27T00:00:00Z", authorization_and_launch_active=False))
        with self.assertRaisesRegex(r.c.Refusal, "E_TRUSTED_TIME"):
            r.check_time_response(envelope, self.policy, self.challenge(), .2)

    def test_time_missing(self):
        with self.assertRaisesRegex(r.c.Refusal, "E_TRUSTED_TIME"):
            r.verify_requests(self.approval, self.launch, self.policy, None, r.executable_sha())

    def test_untrusted_registry_owner(self):
        with self.assertRaisesRegex(r.c.Refusal, "E_TRUST_ACL"):
            r.validate_registry_acl(dict(owner="S-1-5-21-untrusted", rules=[]))

    def test_user_writable_registry(self):
        with self.assertRaisesRegex(r.c.Refusal, "E_TRUST_ACL"):
            r.validate_registry_acl(dict(owner="S-1-5-18", rules=[dict(sid="S-1-1-0", rights=2, allow=True)]))

    def test_registry_acl_positive(self):
        r.validate_registry_acl(dict(owner="S-1-5-18", rules=[dict(sid="S-1-5-32-544", rights=983103, allow=True),
                                                                dict(sid="S-1-1-0", rights=131097, allow=True)]))

    def test_wrong_policy_fingerprint(self):
        self.policy["keys"]["test"]["fingerprint_sha256"] = "0"*64
        with self.assertRaisesRegex(r.c.Refusal, "E_TRUST_FINGERPRINT"):
            self.verify()

    def test_synthetic_policy_label_production_rejected(self):
        self.policy["environment"] = "SYNTHETIC"
        with self.assertRaisesRegex(r.c.Refusal, "E_TRUST_POLICY"):
            r.validate_policy(self.policy)

    def test_duplicate_json_keys(self):
        with self.assertRaisesRegex(r.c.Refusal, "E_JSON_INVALID"):
            r.parse_json('{"approved":false,"approved":true}')

    def test_runtime_pin_mismatch(self):
        with patch.dict(r.PINNED, {"analysis.py": "0"*64}):
            with self.assertRaisesRegex(RuntimeError, "E_RUNTIME_SHA_MISMATCH"):
                r.verify_runtime()

    def test_loader_verifies_all_bytes_before_parse(self):
        # Use frozen SHAs with fabricated bytes: MUST reject before CSV parser.
        with patch.object(r.analysis, "checked_path", return_value=Path("synthetic.csv")), \
             patch.object(Path, "read_bytes", return_value=b"synthetic-corruption"), \
             patch.object(r.analysis.pd, "read_csv", side_effect=AssertionError("must not parse")):
            with self.assertRaisesRegex(r.c.Refusal, "E_INPUT_SHA_MISMATCH"):
                r.load_sources()


for name, field, value, code in [
    ("wrong_harness", "harness_sha256", "0"*64, "E_AUTHORIZATION_HARNESS_SHA_MISMATCH"),
    ("wrong_population", "population", "ROUTER_HOLDOUT", "E_AUTHORIZATION_SCOPE_MISMATCH"),
    ("wrong_arms", "arms", ["A7", "A8"], "E_AUTHORIZATION_SCOPE_MISMATCH"),
    ("expired", "expires_at", "2026-10-26T00:00:00Z", "E_AUTHORIZATION_SCOPE_MISMATCH"),
]:
    def _make_test(field=field, value=value, code=code):
        def test_fn(self):
            self.payload[field] = value
            self.approval = self.sign(self.payload, named=True)
            with self.assertRaisesRegex(r.c.Refusal, code):
                self.verify()
        return test_fn
    setattr(RC1, "test_"+name, _make_test(field, value, code))


if __name__ == "__main__":
    unittest.main()
