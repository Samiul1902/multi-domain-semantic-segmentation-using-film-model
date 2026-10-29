"""RC3 host-clock verification module.

What RC3 adds (additive to RC2)
--------------------------------
RC2 proved that a *signature* over a time claim makes it attributable, not
true, and therefore preserved ``host_clock_trust = "NOT_ESTABLISHED"``
unconditionally. That is the correct decision for the *signing step*. But it
left the path to ``"VERIFIED"`` unimplemented, which makes the host-clock
blocker impossible to clear without a future release.

RC3 adds one narrow extension:

1. ``measure_ntp_offset()``: opens a direct UDP NTP exchange with a list of
   stratum-1 servers and returns the measured offset in seconds. This is
   genuine, independently sourced evidence from outside the host clock.
   The function does NOT call ``w32tm`` (which reads the same OS clock) and
   does NOT trust the Python ``datetime`` wall clock as ground truth.

2. ``write_host_clock_attestation()``: if the measured |offset| <= the
   operator-supplied tolerance (default 1.0 s), writes a signed attestation
   record to the trust store that the time authority endorses. The attestation
   records the measured offset, the server queried, and the reference UTC.

3. ``read_host_clock_attestation()``: reads and signature-verifies the
   attestation. Returns ``"VERIFIED"`` only when the record is present,
   unexpired, signed by a key with the ``TIME_AUTHORITY`` role, and the
   |offset| satisfies the tolerance. Returns ``"NOT_ESTABLISHED"`` otherwise.

4. ``effective_host_clock_trust()``: convenience wrapper used by the RC3 gate
   to replace the RC2 hardcoded constant.

What RC3 does NOT do
--------------------
* It does not modify RC1 or RC2 in any way.
* It does not weaken the signing requirement: a signed proof is still required.
* The ``HOST_CLOCK_TRUST = "NOT_ESTABLISHED"`` module-level constant is
  preserved (RC2 compatibility). Callers that want the dynamic value must call
  ``effective_host_clock_trust()``.
* ``effective_host_clock_trust()`` returns ``"NOT_ESTABLISHED"`` if the trust
  store is absent, the attestation is missing, the signature is invalid, the
  key lacks TIME_AUTHORITY role, the attestation is expired, or the recorded
  offset exceeds the tolerance. It never returns ``"VERIFIED"`` by default.
* This module cannot mint a LaunchGrant; it only provides attestation evidence
  to an RC3 gate.
* NTP exchange is a network I/O operation: it must be performed by the
  operator, not automatically at import time. No network I/O is performed at
  module import.
"""
from __future__ import annotations

import base64
import json
import os
import socket
import struct
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from cryptography.hazmat.primitives import hashes as crypto_hashes
from cryptography.hazmat.primitives.asymmetric import ec

from src.research.c1_film_launch.launch_gate import GateError
from src.research.c1_film_launch_rc2.trust_policy import (
    TIME_ROLES, canonical, verify_policy_signature,
)

# ---------------------------------------------------------------------------
# Module-level constant — RC2 compatible; do NOT remove or change.
# RC3 code that needs the dynamic value calls effective_host_clock_trust().
# ---------------------------------------------------------------------------
HOST_CLOCK_TRUST = "NOT_ESTABLISHED"

ATTESTATION_FILENAME = "c1_rc3_host_clock_attestation.json"
ATTESTATION_TYPE = "C1_RC3_HOST_CLOCK_ATTESTATION"
ATTESTATION_MAX_AGE_HOURS = 24          # attestation valid for one operational day
DEFAULT_TOLERANCE_SECONDS = 1.0         # |offset| must be < this to VERIFY

# NTP stratum-1 pool servers; queried in order, first success used.
NTP_SERVERS = [
    "time.windows.com",
    "pool.ntp.org",
    "time.google.com",
    "time.cloudflare.com",
]
NTP_PORT = 123
NTP_TIMEOUT = 5.0                        # seconds per server attempt
# Unix epoch offset: NTP epoch is 1900-01-01, Unix is 1970-01-01
NTP_DELTA = 2_208_988_800


# ---------------------------------------------------------------------------
# NTP measurement (no OS clock dependency for the reference)
# ---------------------------------------------------------------------------

def measure_ntp_offset(servers: list = NTP_SERVERS,
                       timeout: float = NTP_TIMEOUT) -> dict:
    """Query NTP servers directly and return measured clock offset.

    Returns
    -------
    dict with keys:
        server              : str   -- server that responded
        reference_utc       : str   -- UTC time per NTP (ISO 8601 Z)
        host_utc            : str   -- UTC per host clock at send time (ISO 8601 Z)
        offset_seconds      : float -- host_clock - ntp_reference (signed)
        roundtrip_seconds   : float

    Raises
    ------
    GateError("C1_RC3_NTP_UNREACHABLE") if no server responds.

    Notes
    -----
    The NTP packet format is the standard 48-byte client request (LI=0, VN=3,
    Mode=3). We record the host clock *before* the send (t0) and *after* the
    receive (t3), and use the NTP transmit timestamp (T_s) as the reference:

        offset ~= ((t0 + t3) / 2) - T_s

    This is the standard Cristian algorithm approximation. The host time is
    only used to compute the offset, never as the ground truth.
    """
    ntp_packet = b'\x1b' + 47 * b'\x00'

    for server in servers:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.settimeout(timeout)
                t0 = time.time()
                sock.sendto(ntp_packet, (server, NTP_PORT))
                data, _ = sock.recvfrom(1024)
                t3 = time.time()

            if len(data) < 48:
                continue

            # Transmit timestamp: bytes 40-47 (seconds + fraction, big-endian)
            tx_secs = struct.unpack("!I", data[40:44])[0]
            tx_frac = struct.unpack("!I", data[44:48])[0]
            ntp_time = tx_secs + tx_frac / 2**32 - NTP_DELTA  # Unix timestamp

            roundtrip = t3 - t0
            host_mid = (t0 + t3) / 2.0
            offset = host_mid - ntp_time

            def _unix_to_utc(ts: float) -> str:
                return datetime.fromtimestamp(ts, tz=timezone.utc).strftime(
                    "%Y-%m-%dT%H:%M:%S.%fZ"
                )

            return {
                "server": server,
                "reference_utc": _unix_to_utc(ntp_time),
                "host_utc": _unix_to_utc(host_mid),
                "offset_seconds": float(offset),
                "roundtrip_seconds": float(roundtrip),
            }
        except (OSError, socket.timeout):
            continue

    raise GateError("C1_RC3_NTP_UNREACHABLE")


# ---------------------------------------------------------------------------
# Attestation write/read
# ---------------------------------------------------------------------------

def _attestation_path(trust_store_root) -> Optional[Path]:
    if trust_store_root is None:
        return None
    return Path(trust_store_root) / ATTESTATION_FILENAME


def write_host_clock_attestation(
    private_key,
    key_id: str,
    ntp_result: dict,
    *,
    trust_store_root,
    tolerance_seconds: float = DEFAULT_TOLERANCE_SECONDS,
) -> dict:
    """Write a signed host-clock attestation to the trust store.

    Only the operator (holder of TIME_AUTHORITY private key) calls this.
    Raises GateError if the measured |offset| exceeds tolerance.

    Parameters
    ----------
    private_key : EC private key (cryptography library, ECDSA-P256)
    key_id : str            -- identifier of the TIME_AUTHORITY key in the policy
    ntp_result : dict       -- output of measure_ntp_offset()
    trust_store_root        -- path-like, OS-scope trust store directory
    tolerance_seconds       -- maximum acceptable |offset| in seconds

    Returns
    -------
    The attestation dict as written (including signature).
    """
    offset = ntp_result["offset_seconds"]
    if abs(offset) > tolerance_seconds:
        raise GateError(
            f"C1_RC3_CLOCK_OFFSET_EXCEEDS_TOLERANCE: "
            f"|{offset:.4f}| > {tolerance_seconds}"
        )

    now_utc = datetime.now(timezone.utc)
    expires_utc = now_utc + timedelta(hours=ATTESTATION_MAX_AGE_HOURS)

    payload: dict = {
        "type": ATTESTATION_TYPE,
        "key_id": key_id,
        "issued_at_utc": now_utc.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "expires_at_utc": expires_utc.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "ntp_server": ntp_result["server"],
        "ntp_reference_utc": ntp_result["reference_utc"],
        "host_utc": ntp_result["host_utc"],
        "offset_seconds": offset,
        "roundtrip_seconds": ntp_result["roundtrip_seconds"],
        "tolerance_seconds": tolerance_seconds,
        "verdict": "VERIFIED",
    }
    body = {k: v for k, v in payload.items()}
    sig_bytes = private_key.sign(canonical(body), ec.ECDSA(crypto_hashes.SHA256()))
    payload["signature"] = base64.b64encode(sig_bytes).decode()

    path = _attestation_path(trust_store_root)
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    return payload


def read_host_clock_attestation(
    policy: dict,
    *,
    trust_store_root,
    now: Optional[datetime] = None,
    tolerance_seconds: float = DEFAULT_TOLERANCE_SECONDS,
) -> str:
    """Read and verify a host-clock attestation from the trust store.

    Returns ``"VERIFIED"`` only when ALL of the following hold:
        - attestation file exists and parses as JSON
        - type == ATTESTATION_TYPE
        - not expired (expires_at_utc > now)
        - signature verifies against a TIME_AUTHORITY key in the policy
        - verdict == "VERIFIED"
        - |recorded offset| <= tolerance_seconds

    Returns ``"NOT_ESTABLISHED"`` for every other case (missing file,
    bad signature, expired, wrong type, offset exceeds tolerance).
    Never raises on benign missing/corrupt attestation.
    """
    path = _attestation_path(trust_store_root)
    if path is None or not path.is_file():
        return "NOT_ESTABLISHED"

    try:
        attestation = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return "NOT_ESTABLISHED"

    if attestation.get("type") != ATTESTATION_TYPE:
        return "NOT_ESTABLISHED"
    if attestation.get("verdict") != "VERIFIED":
        return "NOT_ESTABLISHED"

    _now = now or datetime.now(timezone.utc)
    try:
        expires_str = attestation["expires_at_utc"]
        expires_text = (expires_str[:-1] + "+00:00"
                        if expires_str.endswith("Z") else expires_str)
        expires = datetime.fromisoformat(expires_text)
        if not expires.tzinfo:
            expires = expires.replace(tzinfo=timezone.utc)
    except (KeyError, ValueError):
        return "NOT_ESTABLISHED"

    if _now > expires:
        return "NOT_ESTABLISHED"

    try:
        offset = float(attestation["offset_seconds"])
    except (KeyError, TypeError, ValueError):
        return "NOT_ESTABLISHED"
    if abs(offset) > tolerance_seconds:
        return "NOT_ESTABLISHED"

    try:
        verify_policy_signature(policy, attestation, TIME_ROLES)
    except Exception:  # noqa: BLE001
        return "NOT_ESTABLISHED"

    return "VERIFIED"


def effective_host_clock_trust(
    policy: Optional[dict],
    *,
    trust_store_root,
    now: Optional[datetime] = None,
    tolerance_seconds: float = DEFAULT_TOLERANCE_SECONDS,
) -> str:
    """Return dynamic host clock trust for an RC3 gate.

    Returns ``"VERIFIED"`` only if a valid, unexpired, correctly signed
    attestation exists in the trust store. Returns ``"NOT_ESTABLISHED"``
    in every other case, including when policy is None.
    """
    if policy is None:
        return "NOT_ESTABLISHED"
    return read_host_clock_attestation(
        policy,
        trust_store_root=trust_store_root,
        now=now,
        tolerance_seconds=tolerance_seconds,
    )

