"""Tests for RC3 host-clock attestation and gate.

These are SYNTHETIC/offline tests only:
- No real NTP network calls in automated tests (mocked).
- No real trust store provisioning.
- No training, no data loading.
"""
from __future__ import annotations

import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from cryptography.hazmat.primitives.asymmetric import ec

from src.research.c1_film_launch.launch_gate import GateError
from src.research.c1_film_launch_rc3.time_status_rc3 import (
    ATTESTATION_FILENAME,
    ATTESTATION_MAX_AGE_HOURS,
    ATTESTATION_TYPE,
    DEFAULT_TOLERANCE_SECONDS,
    HOST_CLOCK_TRUST,
    effective_host_clock_trust,
    measure_ntp_offset,
    read_host_clock_attestation,
    write_host_clock_attestation,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _generate_test_key():
    """Generate an ephemeral ECDSA-P256 key for offline tests."""
    return ec.generate_private_key(ec.SECP256R1())


def _make_policy_with_key(private_key, key_id: str = "test-time-key-001") -> dict:
    """Build a minimal synthetic trust policy containing one TIME_AUTHORITY key."""
    pub = private_key.public_key()
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
    pub_bytes = pub.public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)
    import base64
    pub_b64 = base64.b64encode(pub_bytes).decode()

    return {
        "schema": 2,
        "policy_id": "test-policy-rc3",
        "keys": [
            {
                "key_id": key_id,
                "role": "TIME_AUTHORITY",
                "algorithm": "ECDSA-P256",
                "status": "ACTIVE",
                "public_key_uncompressed_base64": pub_b64,
            }
        ],
        # Required by verify_policy_signature: add stub signature fields
        "signature": "",  # will be populated or bypassed in unit tests
    }


def _synthetic_ntp_result(offset: float = 0.05, server: str = "time.windows.com") -> dict:
    now = datetime.now(timezone.utc)
    return {
        "server": server,
        "reference_utc": now.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "host_utc": now.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "offset_seconds": offset,
        "roundtrip_seconds": 0.012,
    }


# ---------------------------------------------------------------------------
# 1. Module-level constant preserved (RC2 compatibility)
# ---------------------------------------------------------------------------

class TestHostClockTrustConstant:
    def test_module_constant_is_not_established(self):
        """The hardcoded constant must remain NOT_ESTABLISHED (RC2 compat)."""
        assert HOST_CLOCK_TRUST == "NOT_ESTABLISHED"


# ---------------------------------------------------------------------------
# 2. measure_ntp_offset — network unreachable path (mocked)
# ---------------------------------------------------------------------------

class TestMeasureNtpOffset:
    def test_raises_when_all_servers_fail(self):
        """All servers timeout -> GateError C1_RC3_NTP_UNREACHABLE."""
        import socket
        with patch("socket.socket") as mock_sock_cls:
            mock_sock = MagicMock()
            mock_sock.__enter__ = lambda s: s
            mock_sock.__exit__ = MagicMock(return_value=False)
            mock_sock.recvfrom.side_effect = socket.timeout("timed out")
            mock_sock_cls.return_value = mock_sock
            with pytest.raises(GateError) as exc_info:
                measure_ntp_offset(servers=["fake.ntp.test"], timeout=0.001)
            assert "C1_RC3_NTP_UNREACHABLE" in str(exc_info.value)

    def test_returns_dict_shape_on_success(self):
        """Mock a valid 48-byte NTP response and verify return shape."""
        import struct
        import time as _time

        NTP_DELTA = 2_208_988_800
        tx_unix = _time.time()
        tx_ntp = tx_unix + NTP_DELTA
        tx_secs = int(tx_ntp)
        tx_frac = int((tx_ntp - tx_secs) * 2**32)
        response = b'\x00' * 40 + struct.pack("!II", tx_secs, tx_frac) + b'\x00' * 0

        with patch("socket.socket") as mock_sock_cls:
            mock_sock = MagicMock()
            mock_sock.__enter__ = lambda s: s
            mock_sock.__exit__ = MagicMock(return_value=False)
            mock_sock.recvfrom.return_value = (response, ("time.windows.com", 123))
            mock_sock_cls.return_value = mock_sock

            result = measure_ntp_offset(servers=["time.windows.com"], timeout=1.0)

        assert "server" in result
        assert "offset_seconds" in result
        assert "roundtrip_seconds" in result
        assert "reference_utc" in result
        assert result["roundtrip_seconds"] >= 0.0


# ---------------------------------------------------------------------------
# 3. write_host_clock_attestation
# ---------------------------------------------------------------------------

class TestWriteHostClockAttestation:
    def test_write_creates_file(self):
        key = _generate_test_key()
        ntp_result = _synthetic_ntp_result(offset=0.05)
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch(
                "src.research.c1_film_launch_rc3.time_status_rc3.verify_policy_signature"
            ):
                attestation = write_host_clock_attestation(
                    key, "key-001", ntp_result,
                    trust_store_root=tmpdir,
                )
            path = Path(tmpdir) / ATTESTATION_FILENAME
            assert path.is_file()
            on_disk = json.loads(path.read_text())
            assert on_disk["type"] == ATTESTATION_TYPE
            assert on_disk["verdict"] == "VERIFIED"
            assert abs(on_disk["offset_seconds"] - 0.05) < 1e-9

    def test_refuses_large_offset(self):
        key = _generate_test_key()
        ntp_result = _synthetic_ntp_result(offset=2.0)  # > 1.0s tolerance
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(GateError) as exc_info:
                write_host_clock_attestation(
                    key, "key-001", ntp_result,
                    trust_store_root=tmpdir,
                    tolerance_seconds=1.0,
                )
            assert "C1_RC3_CLOCK_OFFSET_EXCEEDS_TOLERANCE" in str(exc_info.value)

    def test_negative_offset_within_tolerance_accepted(self):
        """Negative offset (host fast) within tolerance is valid."""
        key = _generate_test_key()
        ntp_result = _synthetic_ntp_result(offset=-0.8)
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch(
                "src.research.c1_film_launch_rc3.time_status_rc3.verify_policy_signature"
            ):
                attestation = write_host_clock_attestation(
                    key, "key-001", ntp_result,
                    trust_store_root=tmpdir,
                    tolerance_seconds=1.0,
                )
            assert attestation["verdict"] == "VERIFIED"


# ---------------------------------------------------------------------------
# 4. read_host_clock_attestation
# ---------------------------------------------------------------------------

class TestReadHostClockAttestation:
    def _write_attestation(self, tmpdir, offset=0.05, hours_from_now=1,
                           verdict="VERIFIED", typ=ATTESTATION_TYPE):
        now = datetime.now(timezone.utc)
        expires = now + timedelta(hours=hours_from_now)
        record = {
            "type": typ,
            "key_id": "key-001",
            "issued_at_utc": now.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "expires_at_utc": expires.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "ntp_server": "time.windows.com",
            "ntp_reference_utc": now.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "host_utc": now.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "offset_seconds": offset,
            "roundtrip_seconds": 0.01,
            "tolerance_seconds": DEFAULT_TOLERANCE_SECONDS,
            "verdict": verdict,
            "signature": "MOCK_SIG",
        }
        path = Path(tmpdir) / ATTESTATION_FILENAME
        path.write_text(json.dumps(record), encoding="utf-8")
        return record

    def test_returns_verified_with_valid_attestation(self):
        """Valid attestation + valid signature -> VERIFIED."""
        with tempfile.TemporaryDirectory() as tmpdir:
            self._write_attestation(tmpdir)
            with patch(
                "src.research.c1_film_launch_rc3.time_status_rc3.verify_policy_signature"
            ) as mock_verify:
                mock_verify.return_value = {"key_id": "key-001"}
                result = read_host_clock_attestation(
                    policy={}, trust_store_root=tmpdir
                )
            assert result == "VERIFIED"

    def test_returns_not_established_when_file_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = read_host_clock_attestation(policy={}, trust_store_root=tmpdir)
            assert result == "NOT_ESTABLISHED"

    def test_returns_not_established_when_expired(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._write_attestation(tmpdir, hours_from_now=-1)  # already expired
            with patch(
                "src.research.c1_film_launch_rc3.time_status_rc3.verify_policy_signature"
            ):
                result = read_host_clock_attestation(
                    policy={}, trust_store_root=tmpdir,
                    now=datetime.now(timezone.utc),
                )
            assert result == "NOT_ESTABLISHED"

    def test_returns_not_established_with_bad_signature(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._write_attestation(tmpdir)
            with patch(
                "src.research.c1_film_launch_rc3.time_status_rc3.verify_policy_signature",
                side_effect=GateError("C1_BAD_SIG"),
            ):
                result = read_host_clock_attestation(
                    policy={}, trust_store_root=tmpdir
                )
            assert result == "NOT_ESTABLISHED"

    def test_returns_not_established_with_wrong_type(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._write_attestation(tmpdir, typ="WRONG_TYPE")
            with patch(
                "src.research.c1_film_launch_rc3.time_status_rc3.verify_policy_signature"
            ):
                result = read_host_clock_attestation(
                    policy={}, trust_store_root=tmpdir
                )
            assert result == "NOT_ESTABLISHED"

    def test_returns_not_established_when_offset_exceeds_tolerance(self):
        """Attestation with offset=0.9 but tolerance=0.5 must return NOT_ESTABLISHED."""
        with tempfile.TemporaryDirectory() as tmpdir:
            self._write_attestation(tmpdir, offset=0.9)
            with patch(
                "src.research.c1_film_launch_rc3.time_status_rc3.verify_policy_signature"
            ) as mock_verify:
                mock_verify.return_value = {"key_id": "key-001"}
                result = read_host_clock_attestation(
                    policy={}, trust_store_root=tmpdir,
                    tolerance_seconds=0.5,
                )
            assert result == "NOT_ESTABLISHED"

    def test_returns_not_established_when_verdict_not_verified(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._write_attestation(tmpdir, verdict="FAILED")
            with patch(
                "src.research.c1_film_launch_rc3.time_status_rc3.verify_policy_signature"
            ):
                result = read_host_clock_attestation(
                    policy={}, trust_store_root=tmpdir
                )
            assert result == "NOT_ESTABLISHED"

    def test_returns_not_established_with_corrupt_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / ATTESTATION_FILENAME
            path.write_text("NOT JSON {{{", encoding="utf-8")
            result = read_host_clock_attestation(policy={}, trust_store_root=tmpdir)
            assert result == "NOT_ESTABLISHED"

    def test_returns_not_established_when_trust_store_none(self):
        result = read_host_clock_attestation(policy={}, trust_store_root=None)
        assert result == "NOT_ESTABLISHED"


# ---------------------------------------------------------------------------
# 5. effective_host_clock_trust
# ---------------------------------------------------------------------------

class TestEffectiveHostClockTrust:
    def test_returns_not_established_when_policy_none(self):
        result = effective_host_clock_trust(None, trust_store_root="/nonexistent")
        assert result == "NOT_ESTABLISHED"

    def test_returns_not_established_when_no_attestation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = effective_host_clock_trust({}, trust_store_root=tmpdir)
            assert result == "NOT_ESTABLISHED"


# ---------------------------------------------------------------------------
# 6. RC3Grant authorization controls
# ---------------------------------------------------------------------------

class TestRC3GrantAuthorizationControls:
    """Verify that RC3Grant enforces all authorization gates without real data."""

    def _make_synthetic_rc3_grant(
        self, authorization_class="SYNTHETIC_TEST", clock_trust="NOT_ESTABLISHED"
    ):
        from src.research.c1_film_launch_rc3.rc3_gate import RC3Grant
        mock_rc2 = MagicMock()
        mock_rc2.authorization_class = authorization_class
        mock_rc2.record = {
            "authorization_class": authorization_class,
            "run_plan": [{"arm": "C1-T", "seed": 42}, {"arm": "C1-C", "seed": 42}],
        }
        return RC3Grant(mock_rc2, clock_trust, "/tmp/test_trust",
                        token=RC3Grant._MINT)

    def test_synthetic_grant_cannot_train(self):
        from src.research.c1_film_launch_rc3.rc3_gate import RC3Grant
        grant = self._make_synthetic_rc3_grant(
            authorization_class="SYNTHETIC_TEST", clock_trust="VERIFIED"
        )
        with pytest.raises(GateError) as exc_info:
            grant.authorize_trainer({
                "study_id": "C1_FILM_ATTRIBUTION_V1",
                "protocol_sha256": "531e3eb255a66381201d1aaf49bbe55abfdbe529640f5c584ef100d298087a61",
                "arm": "C1-T", "seed": 42,
            })
        assert "C1_RC3_SYNTHETIC_GRANT_CANNOT_TRAIN" in str(exc_info.value)

    def test_production_grant_with_unverified_clock_cannot_train(self):
        from src.research.c1_film_launch_rc3.rc3_gate import RC3Grant
        grant = self._make_synthetic_rc3_grant(
            authorization_class="PRODUCTION", clock_trust="NOT_ESTABLISHED"
        )
        with pytest.raises(GateError) as exc_info:
            grant.authorize_trainer({
                "study_id": "C1_FILM_ATTRIBUTION_V1",
                "protocol_sha256": "531e3eb255a66381201d1aaf49bbe55abfdbe529640f5c584ef100d298087a61",
                "arm": "C1-T", "seed": 42,
            })
        assert "C1_RC3_HOST_CLOCK_UNVERIFIED" in str(exc_info.value)

    def test_rc3_grant_forged_without_token(self):
        from src.research.c1_film_launch_rc3.rc3_gate import RC3Grant
        with pytest.raises(GateError) as exc_info:
            RC3Grant(MagicMock(), "NOT_ESTABLISHED", "/tmp")
        assert "C1_RC3_GRANT_FORGED" in str(exc_info.value)

    def test_unauthorized_run_refused(self):
        """A run not in run_plan is refused even with PRODUCTION + VERIFIED."""
        from src.research.c1_film_launch_rc3.rc3_gate import RC3Grant
        mock_rc2 = MagicMock()
        mock_rc2.authorization_class = "PRODUCTION"
        mock_rc2.record = {
            "authorization_class": "PRODUCTION",
            "run_plan": [{"arm": "C1-T", "seed": 42}],  # only seed 42 C1-T
        }
        grant = RC3Grant(mock_rc2, "VERIFIED", "/tmp/trust",
                         token=RC3Grant._MINT)
        with pytest.raises(GateError) as exc_info:
            grant.authorize_trainer({
                "study_id": "C1_FILM_ATTRIBUTION_V1",
                "protocol_sha256": "531e3eb255a66381201d1aaf49bbe55abfdbe529640f5c584ef100d298087a61",
                "arm": "C1-T", "seed": 999,   # not authorized
            })
        assert "C1_RUN_NOT_AUTHORIZED" in str(exc_info.value)

    def test_wrong_study_id_refused(self):
        from src.research.c1_film_launch_rc3.rc3_gate import RC3Grant
        mock_rc2 = MagicMock()
        mock_rc2.authorization_class = "PRODUCTION"
        mock_rc2.record = {
            "authorization_class": "PRODUCTION",
            "run_plan": [{"arm": "C1-T", "seed": 42}],
        }
        grant = RC3Grant(mock_rc2, "VERIFIED", "/tmp/trust",
                         token=RC3Grant._MINT)
        with pytest.raises(GateError) as exc_info:
            grant.authorize_trainer({
                "study_id": "WRONG_STUDY",
                "protocol_sha256": "531e3eb255a66381201d1aaf49bbe55abfdbe529640f5c584ef100d298087a61",
                "arm": "C1-T", "seed": 42,
            })
        assert "C1_CONTRACT_SCOPE_MISMATCH" in str(exc_info.value)



# ---------------------------------------------------------------------------
# 7. Complete integration chain & security controls (Task 2 & Task 3)
# ---------------------------------------------------------------------------

class TestRC3FullIntegrationAndSecurityControls:
    def test_rc3_preserves_rc2_structural_checks(self):
        """Mismatched protocol or budget raises GateError before grant minting."""
        from src.research.c1_film_launch_rc3.rc3_gate import mint_rc3_grant
        with pytest.raises(GateError):
            mint_rc3_grant(
                expected_release_digest="INVALID_DIGEST",
                approval={"authorization_id": "a1"},
                instruction={"launch_id": "l1"},
                time_status={},
                budget={},
                run_plan=[],
                recovery={},
            )

    def test_synthetic_grant_refused_at_authorize_loader(self):
        """Synthetic RC3Grant is strictly refused from accessing real dataset loader."""
        from src.research.c1_film_launch_rc3.rc3_gate import RC3Grant
        mock_rc2 = MagicMock()
        mock_rc2.authorization_class = "SYNTHETIC_TEST"
        mock_rc2.authorize_loader.side_effect = GateError("C1_RC2_SYNTHETIC_GRANT_CANNOT_ACCESS_DATA")
        grant = RC3Grant(mock_rc2, "VERIFIED", "/tmp/trust", token=RC3Grant._MINT)
        with pytest.raises(GateError) as exc_info:
            grant.authorize_loader({"study_id": "C1_FILM_ATTRIBUTION_V1"})
        assert "C1_RC2_SYNTHETIC_GRANT_CANNOT_ACCESS_DATA" in str(exc_info.value)

    def test_production_grant_unverified_clock_refuses_trainer_directly(self):
        """Production RC3Grant with NOT_ESTABLISHED clock strictly halts trainer."""
        from src.research.c1_film_launch_rc3.rc3_gate import RC3Grant
        mock_rc2 = MagicMock()
        mock_rc2.authorization_class = "PRODUCTION"
        mock_rc2.record = {
            "authorization_class": "PRODUCTION",
            "run_plan": [{"arm": "C1-T", "seed": 42}],
        }
        grant = RC3Grant(mock_rc2, "NOT_ESTABLISHED", "/tmp/trust", token=RC3Grant._MINT)
        with pytest.raises(GateError) as exc_info:
            grant.authorize_trainer({
                "study_id": "C1_FILM_ATTRIBUTION_V1",
                "protocol_sha256": "531e3eb255a66381201d1aaf49bbe55abfdbe529640f5c584ef100d298087a61",
                "arm": "C1-T", "seed": 42,
            })
        assert "C1_RC3_HOST_CLOCK_UNVERIFIED" in str(exc_info.value)

    def test_tampered_time_attestation_payload_returns_not_established(self):
        """Tampering with attestation offset or timestamp breaks verification."""
        key = _generate_test_key()
        ntp_result = _synthetic_ntp_result(offset=0.01)
        with tempfile.TemporaryDirectory() as tmpdir:
            attestation = write_host_clock_attestation(
                key, "time-key-1", ntp_result, trust_store_root=tmpdir
            )
            # Tamper the offset in JSON on disk
            path = Path(tmpdir) / ATTESTATION_FILENAME
            data = json.loads(path.read_text())
            data["offset_seconds"] = 0.99  # tampered
            path.write_text(json.dumps(data))

            policy = _make_policy_with_key(key, "time-key-1")
            res = read_host_clock_attestation(policy, trust_store_root=tmpdir)
            assert res == "NOT_ESTABLISHED"

    def test_recomputed_rc3_release_identity(self):
        """Verify that release identity RC3 computes expected release digest."""
        from src.research.c1_film_launch_rc3 import release_identity_rc3 as rid
        report = rid.verify_release_rc3(require_published=True)
        assert report["release_id"] == "C1_FILM_ATTRIBUTION_V1_LAUNCH_RC3"
        assert report["rc1_release_digest"] == "1aec5e17ee79eb8845ea36808d5a087ea99c091be798ec5a41b4e412f93ff9c1"
        assert report["rc2_release_digest"] == "54794efc6d99d94fae9eaebd992e01e4e9923b5055d024ea1d5f02a8a5e737ed"
