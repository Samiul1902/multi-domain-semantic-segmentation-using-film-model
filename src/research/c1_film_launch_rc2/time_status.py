"""Signed RC2 time/status evidence.

What this establishes, and what it does not
-------------------------------------------
A time proof is an ECDSA-P256 statement, signed by a key the trust policy
authorises for the ``TIME_AUTHORITY`` role, binding:

* the release digest,
* the authorization id,
* the launch id,
* a single-use nonce,
* an issuance/expiry window and a status.

So the proof is **attributable** (a named authority asserted it), **bound** (it
cannot be transplanted to another release, approval or launch) and **single-use**
(replay is refused against a durable ledger). That is a genuine improvement on
RC1, which accepted an unsigned caller-supplied ``trusted_time`` dictionary.

It does **not** establish that the host clock is correct. A signature over the
sentence "the time is X" makes the sentence attributable, not true. RC2 therefore
reports ``host_clock_trust = "NOT_ESTABLISHED"`` unconditionally, and the grant
refuses production training while it is not ``VERIFIED``. Independently verified
host time (O8: CMOS battery, UPS, NTP) remains a blocking external requirement.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
from datetime import datetime, timedelta, timezone

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec

from src.research.c1_film_launch.launch_gate import GateError
from .trust_policy import TIME_ROLES, canonical, verify_policy_signature

PROOF_TYPE = "C1_RC2_TIME_STATUS"
MAX_AGE_SECONDS = 300
CLOCK_SKEW_SECONDS = 5
LEDGER_NAME = "c1_rc2_nonce_ledger.jsonl"

#: Host clock truth is never established by a signature. Preserved blocker.
HOST_CLOCK_TRUST = "NOT_ESTABLISHED"


def parse_utc(value, code: str = "C1_RC2_TIME_FORMAT") -> datetime:
    if not isinstance(value, str) or not value:
        raise GateError(code)
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise GateError(code) from exc
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


# --------------------------------------------------------------------------- #
# Durable replay ledger
# --------------------------------------------------------------------------- #
def _ledger_path(ledger_root) -> "os.PathLike | None":
    if ledger_root is None:
        return None
    return os.path.join(str(ledger_root), LEDGER_NAME)


def read_ledger(ledger_root) -> set:
    """Return the set of consumed nonce digests recorded on disk."""
    path = _ledger_path(ledger_root)
    if path is None or not os.path.isfile(path):
        return set()
    seen = set()
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except ValueError:
                continue
            digest = record.get("nonce_sha256")
            if isinstance(digest, str):
                seen.add(digest)
    return seen


def append_ledger(ledger_root, record: dict) -> None:
    """Write-once append: O_CREAT|O_APPEND, full write loop, fsync."""
    path = _ledger_path(ledger_root)
    if path is None:
        return
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    payload = (json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    flags = os.O_CREAT | os.O_APPEND | os.O_WRONLY | getattr(os, "O_BINARY", 0)
    fd = os.open(path, flags, 0o600)
    try:
        written = 0
        while written < len(payload):
            written += os.write(fd, payload[written:])
        os.fsync(fd)
    finally:
        os.close(fd)


# --------------------------------------------------------------------------- #
# Verification
# --------------------------------------------------------------------------- #
def verify_time_status(policy: dict, proof: dict, *, release_digest: str,
                       authorization_id: str, launch_id: str, now: datetime,
                       ledger_root=None, consume_nonce: bool = True) -> dict:
    required = ("type", "release_digest", "authorization_id", "launch_id", "nonce",
                "key_id", "issued_at_utc", "expires_at_utc", "status", "signature")
    if not isinstance(proof, dict) or any(not proof.get(k) for k in required):
        raise GateError("C1_RC2_TIME_PROOF_INCOMPLETE")
    if proof["type"] != PROOF_TYPE:
        raise GateError("C1_RC2_TIME_PROOF_TYPE")

    # Identity binding: a proof for another release/approval/launch is worthless.
    if (proof["release_digest"], proof["authorization_id"], proof["launch_id"]) != (
            release_digest, authorization_id, launch_id):
        raise GateError("C1_RC2_TIME_IDENTITY_BINDING")

    if proof["status"] != "ACTIVE":
        raise GateError("C1_RC2_AUTHORIZATION_INACTIVE")

    issued = parse_utc(proof["issued_at_utc"])
    expires = parse_utc(proof["expires_at_utc"])
    if expires <= issued:
        raise GateError("C1_RC2_TIME_PROOF_WINDOW")
    if now < issued - timedelta(seconds=CLOCK_SKEW_SECONDS):
        raise GateError("C1_RC2_TIME_PROOF_FUTURE")
    if now > expires:
        raise GateError("C1_RC2_TIME_PROOF_EXPIRED")
    if now - issued > timedelta(seconds=MAX_AGE_SECONDS):
        raise GateError("C1_RC2_TIME_PROOF_STALE")

    nonce = proof["nonce"]
    if not isinstance(nonce, str) or len(nonce) < 32:
        raise GateError("C1_RC2_TIME_NONCE_INVALID")
    nonce_sha256 = hashlib.sha256(nonce.encode("utf-8")).hexdigest()

    if consume_nonce and nonce_sha256 in read_ledger(ledger_root):
        raise GateError("C1_RC2_TIME_NONCE_REPLAY")

    key = verify_policy_signature(policy, proof, TIME_ROLES)

    if consume_nonce:
        append_ledger(ledger_root, {
            "nonce_sha256": nonce_sha256,
            "release_digest": release_digest,
            "authorization_id": authorization_id,
            "launch_id": launch_id,
            "issued_at_utc": proof["issued_at_utc"],
            "consumed_by": "c1_film_launch_rc2",
        })

    return {"key_id": key["key_id"], "issued": issued, "expires": expires,
            "nonce_sha256": nonce_sha256, "host_clock_trust": HOST_CLOCK_TRUST}


def sign_for_test(private_key, payload: dict) -> str:
    """Test-only helper: detached signature over the payload minus ``signature``."""
    body = {k: v for k, v in payload.items() if k != "signature"}
    return base64.b64encode(private_key.sign(canonical(body),
                                             ec.ECDSA(hashes.SHA256()))).decode()
