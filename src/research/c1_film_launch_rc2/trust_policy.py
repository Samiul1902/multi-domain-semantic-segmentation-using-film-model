"""RC2 external trust policy and deployment-binding verification.

Where trust comes from
----------------------
Production trust is **not** a Python constant and **not** anything carried inside
an approval payload. It comes from an institutionally controlled trust store at a
fixed OS-scope location (``%ProgramData%\\InstitutionalC1Trust`` on Windows,
``/etc/institutional-c1-trust`` elsewhere), which lives outside the repository and
is therefore provisionable without a release revision.

Layout of the store::

    <root>/c1_rc2_binding.json     deployment binding (declares the policy)
    <root>/<policy_relative_path>  signed trust policy

The binding declares the policy path, the policy digest, the policy owner's
identity and the policy owner's public key. The policy is signed by the policy
owner, so its *content* is authenticated rather than merely digest-bound. The
policy lists approval keys with roles, status and revocation.

Because the policy is signed data, adding, rotating or revoking an approval key is
an institutional data operation. Only the store *location* is fixed by this
release.

Honest limitation
-----------------
A Python module cannot protect against arbitrary in-process tampering: a caller
who can already execute code here can patch anything. ``tuple``/``frozenset`` are
not immutability guarantees against that. The defence boundary is external OS
ownership/ACLs plus independent institutional provisioning — and on Windows this
module can only *advisory*-check location, not ACLs (see ``assert_policy_owner``).
RC2 ships no production trust store; its absence is the expected production state
and the gate is fail-closed without it.
"""
from __future__ import annotations

import hashlib
import json
import os
import stat
from pathlib import Path

from src.research.c1_film_launch.launch_gate import GateError

BINDING_SCHEMA = 1
POLICY_SCHEMA = 2

#: Fixed, OS-scope production location. Never derived from a caller argument.
DEFAULT_PRODUCTION_ROOT = (
    Path(os.environ.get("ProgramData", "C:/ProgramData")) / "InstitutionalC1Trust"
    if os.name == "nt" else Path("/etc/institutional-c1-trust")
)

APPROVAL_ROLES = ("SUPERVISOR", "INSTITUTIONAL_APPROVER")
LAUNCH_ROLES = ("LAUNCH_OPERATOR",)
TIME_ROLES = ("TIME_AUTHORITY",)


# --------------------------------------------------------------------------- #
# Canonicalisation and signatures
# --------------------------------------------------------------------------- #
def canonical(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def _exclude(value: dict, keys) -> dict:
    return {k: v for k, v in value.items() if k not in keys}


def policy_body(policy: dict) -> dict:
    """The signed substance of a policy: everything except its digest and signature."""
    return _exclude(policy, ("policy_digest", "policy_signature"))


def policy_digest(policy: dict) -> str:
    return hashlib.sha256(canonical(policy_body(policy))).hexdigest()


def spki_fingerprint(public_key_pem: str) -> str:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.serialization import load_pem_public_key
    try:
        key = load_pem_public_key(public_key_pem.encode("utf-8"))
    except (ValueError, TypeError) as exc:
        raise GateError("C1_RC2_TRUST_KEY_UNREADABLE") from exc
    der = key.public_bytes(serialization.Encoding.DER,
                           serialization.PublicFormat.SubjectPublicKeyInfo)
    return hashlib.sha256(der).hexdigest()


def verify_signature(public_key_pem: str, payload: dict, signature_b64: str,
                     *, exclude=("signature",)) -> bool:
    """ECDSA-P256/SHA-256 detached signature over canonical JSON. Never raises.

    ``exclude`` names the keys removed before canonicalisation, so a record can
    carry its own signature without a circular definition. RC2 uses two names:
    ``signature`` for payloads and ``policy_signature`` for policies.
    """
    import base64
    import binascii

    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives.serialization import load_pem_public_key

    if not isinstance(payload, dict) or not isinstance(signature_b64, str) or not signature_b64:
        return False
    try:
        signature = base64.b64decode(signature_b64, validate=True)
    except (binascii.Error, ValueError):
        return False
    try:
        key = load_pem_public_key(public_key_pem.encode("utf-8"))
    except (ValueError, TypeError):
        return False
    if not isinstance(key, ec.EllipticCurvePublicKey):
        return False
    try:
        key.verify(signature, canonical(_exclude(payload, exclude)), ec.ECDSA(hashes.SHA256()))
    except InvalidSignature:
        return False
    return True


# --------------------------------------------------------------------------- #
# Filesystem checks
# --------------------------------------------------------------------------- #
def _checked_file(path: Path, *, require_owner: bool) -> Path:
    path = Path(path).resolve()
    if not path.is_file() or path.is_symlink():
        raise GateError("C1_RC2_TRUST_STORE_MISSING_OR_SYMLINK")
    if require_owner and os.name != "nt":
        mode = path.stat().st_mode
        if mode & (stat.S_IWGRP | stat.S_IWOTH):
            raise GateError("C1_RC2_TRUST_STORE_WRITABLE_BY_OTHER")
    return path


def assert_policy_owner(root: Path, *, require_owner: bool) -> dict:
    """Ownership/ACL enforcement.

    POSIX: group/world-writable files are refused.

    Windows: ACLs cannot be inspected reliably from portable Python without shelling
    out, so RC2 performs a *location* check instead — the store must sit under the
    OS-scope ProgramData root and outside the repository — and reports
    ``owner_enforcement="ADVISORY_WINDOWS"``. Institutional ACLs must be applied by
    the OS administrator; this is a declared provisioning requirement, not a
    guarantee made here.

    ``require_owner=False`` is the synthetic path: only the repository-containment
    guard applies, so a temporary test store outside the repo is permitted.
    """
    root = Path(root).resolve()
    repo = Path(__file__).resolve().parents[3].resolve()
    try:
        root.relative_to(repo)
    except ValueError:
        pass
    else:
        raise GateError("C1_RC2_TRUST_STORE_INSIDE_REPOSITORY")

    if not require_owner:
        return {"owner_enforcement": "NOT_REQUIRED_SYNTHETIC"}

    if not root.is_dir():
        raise GateError("C1_RC2_TRUST_STORE_MISSING_OR_SYMLINK")

    if os.name != "nt":
        st = root.stat()
        if st.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
            raise GateError("C1_RC2_TRUST_STORE_WRITABLE_BY_OTHER")
        return {"owner_enforcement": "POSIX_MODE_BITS"}

    program_data = Path(os.environ.get("ProgramData", "C:/ProgramData")).resolve()
    try:
        root.relative_to(program_data)
    except ValueError as exc:
        raise GateError("C1_RC2_TRUST_STORE_NOT_OS_SCOPE") from exc
    return {"owner_enforcement": "ADVISORY_WINDOWS"}


def _load_json(path: Path, code: str) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise GateError(code) from exc
    if not isinstance(data, dict):
        raise GateError(code)
    return data


# --------------------------------------------------------------------------- #
# Binding and policy
# --------------------------------------------------------------------------- #
def load_binding(root: Path, *, require_owner: bool) -> dict:
    path = _checked_file(Path(root) / "c1_rc2_binding.json", require_owner=require_owner)
    binding = _load_json(path, "C1_RC2_DEPLOYMENT_BINDING_UNREADABLE")
    required = ("binding_id", "owner_identity", "policy_relative_path",
                "policy_digest", "policy_owner_key_id", "policy_owner_public_key_pem")
    if binding.get("schema") != BINDING_SCHEMA or any(not binding.get(k) for k in required):
        raise GateError("C1_RC2_DEPLOYMENT_BINDING_INCOMPLETE")
    relative = Path(binding["policy_relative_path"])
    if relative.is_absolute() or ".." in relative.parts:
        raise GateError("C1_RC2_POLICY_PATH_INVALID")
    binding["_path"] = path
    binding["_policy_path"] = (path.parent / relative).resolve()
    if binding["_policy_path"].parent != path.parent:
        raise GateError("C1_RC2_POLICY_PATH_ESCAPE")
    return binding


def load_policy(policy_path: Path, *, expected_digest: str | None = None,
                require_owner: bool = False) -> dict:
    """Load and structurally validate a policy document (no signature check)."""
    path = _checked_file(policy_path, require_owner=require_owner)
    policy = _load_json(path, "C1_RC2_TRUST_POLICY_UNREADABLE")
    if policy.get("schema") != POLICY_SCHEMA or not isinstance(policy.get("keys"), list):
        raise GateError("C1_RC2_TRUST_POLICY_SCHEMA")
    computed = policy_digest(policy)
    if policy.get("policy_digest") != computed:
        raise GateError("C1_RC2_TRUST_POLICY_DIGEST")
    if expected_digest is not None and computed != expected_digest:
        raise GateError("C1_RC2_TRUST_POLICY_DIGEST")
    return policy


def load_trust_store(root, *, require_owner: bool = True) -> tuple[dict, dict]:
    """Full trust-store verification: binding -> policy -> owner signature -> keys."""
    root = Path(root)
    enforcement = assert_policy_owner(root, require_owner=require_owner)
    binding = load_binding(root, require_owner=require_owner)
    binding["_owner_enforcement"] = enforcement["owner_enforcement"]
    policy = load_policy(binding["_policy_path"], expected_digest=binding["policy_digest"],
                         require_owner=require_owner)

    if policy.get("owner_identity") != binding["owner_identity"]:
        raise GateError("C1_RC2_TRUST_POLICY_OWNER_MISMATCH")
    if policy.get("policy_owner_key_id") != binding["policy_owner_key_id"]:
        raise GateError("C1_RC2_TRUST_POLICY_OWNER_MISMATCH")

    # The policy's own signature: content is authenticated, not just digest-bound.
    if not verify_signature(binding["policy_owner_public_key_pem"], policy,
                            policy.get("policy_signature", ""),
                            exclude=("policy_signature",)):
        raise GateError("C1_RC2_TRUST_POLICY_SIGNATURE_INVALID")

    active = []
    for key in policy["keys"]:
        if not isinstance(key, dict) or not key.get("key_id") or \
                not key.get("public_key_pem") or not isinstance(key.get("roles"), list):
            raise GateError("C1_RC2_TRUST_KEY_RECORD")
        if spki_fingerprint(key["public_key_pem"]) != key.get("fingerprint"):
            raise GateError("C1_RC2_TRUST_KEY_FINGERPRINT")
        if key.get("status") == "ACTIVE" and key.get("revoked") is not True:
            active.append(key)
    if not active:
        raise GateError("C1_RC2_NO_ACTIVE_TRUST_KEY")
    return binding, policy


def verify_policy_signature(policy: dict, payload: dict, roles=()) -> dict:
    """Verify a payload signature against a key authorised by the policy.

    Refusals are deliberately distinct so negative controls stay diagnostic:
    an untrusted key, a revoked key, a role failure and a bad signature are four
    different codes, unlike RC1 where every one of them collapsed into
    ``C1_TRUST_ANCHOR_NOT_ALLOWLISTED``.
    """
    if not isinstance(payload, dict):
        raise GateError("C1_RC2_PAYLOAD_INVALID")
    signature = payload.get("signature")
    key_id = payload.get("key_id")
    if not isinstance(signature, str) or not signature:
        raise GateError("C1_RC2_SIGNATURE_MISSING")
    if not isinstance(key_id, str) or not key_id:
        raise GateError("C1_RC2_SIGNATURE_KEY_UNTRUSTED")

    candidates = [k for k in policy["keys"] if k.get("key_id") == key_id]
    if not candidates:
        raise GateError("C1_RC2_SIGNATURE_KEY_UNTRUSTED")
    key = candidates[0]

    if key.get("revoked") is True or key.get("status") != "ACTIVE":
        raise GateError("C1_RC2_SIGNATURE_KEY_REVOKED")
    if roles and not set(roles) & set(key.get("roles") or []):
        raise GateError("C1_RC2_SIGNATURE_KEY_ROLE")
    if not verify_signature(key["public_key_pem"], payload, signature):
        raise GateError("C1_RC2_SIGNATURE_INVALID")
    return key
