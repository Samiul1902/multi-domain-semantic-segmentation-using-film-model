"""RC4 institutional trust root (DECISION_I).

Differences from the RC2/RC3 trust store:

* A new OS-scope root, ``%ProgramData%\\InstitutionalC1TrustRC4`` (POSIX:
  ``/etc/institutional-c1-trust-rc4``). The RC2/RC3 root is never read, accepted or
  used as authority; it is rejected by path before any file access.
* A production binding must identify the institution, the approving authority and
  the key custodian, and must reference the institutional provisioning record. Any
  PENDING / SYNTHETIC / TEST / placeholder value is refused.
* Every key carries a ``custodian``. Approval-role custodians must differ from the
  launch-role custodian and from the researcher identity declared in the binding.

RC4 ships no store, key or approval. Absence of the store is the expected state and
the gate fails closed without it. Windows ACLs are not inspected here (advisory
location check only, as in RC2); institutional ACLs are an administrator duty.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

from src.research.c1_film_launch.launch_gate import GateError
from src.research.c1_film_launch_rc2 import trust_policy as rc2_trust
from src.research.c1_film_launch_rc2.trust_policy import (
    APPROVAL_ROLES, LAUNCH_ROLES, assert_policy_owner, load_policy, spki_fingerprint,
    verify_signature,
)

STUDY_ID = "C1_FILM_ATTRIBUTION_V1"
BINDING_SCHEMA = 1
BINDING_FILENAME = "c1_rc4_binding.json"

PRODUCTION_ROOT = (
    Path(os.environ.get("ProgramData", "C:/ProgramData")) / "InstitutionalC1TrustRC4"
    if os.name == "nt" else Path("/etc/institutional-c1-trust-rc4")
)
LEGACY_ROOT = rc2_trust.DEFAULT_PRODUCTION_ROOT  # compared by path only, never read

_UNIDENTIFIED = re.compile(
    r"\b(PENDING|SYNTHETIC|TEST|TBD|PLACEHOLDER|UNKNOWN|NOT INSTITUTIONAL)\b", re.I)
_IDENTITY_FIELDS = ("owner_identity", "institution_name", "approving_authority",
                    "key_custodian", "provisioning_reference")


def _same(a, b) -> bool:
    return os.path.normcase(os.path.abspath(a)) == os.path.normcase(os.path.abspath(b))


def identified(value) -> bool:
    return isinstance(value, str) and bool(value.strip()) and not _UNIDENTIFIED.search(value)


def _check_root(root: Path, require_owner: bool) -> None:
    if _same(root, LEGACY_ROOT):
        raise GateError("C1_RC4_LEGACY_TRUST_STORE_REJECTED")
    if require_owner:
        if not _same(root, PRODUCTION_ROOT):
            raise GateError("C1_RC4_TRUST_STORE_NOT_PRODUCTION")
    elif _same(root, PRODUCTION_ROOT):
        raise GateError("C1_RC4_SYNTHETIC_STORE_AT_PRODUCTION_PATH")
    if not root.is_dir():
        raise GateError("C1_RC4_TRUST_ROOT_MISSING")


def load_binding(root: Path, *, require_owner: bool) -> dict:
    path = rc2_trust._checked_file(root / BINDING_FILENAME, require_owner=require_owner)
    binding = rc2_trust._load_json(path, "C1_RC4_BINDING_UNREADABLE")
    required = ("binding_id", "study_scope", "researcher_identity", "policy_relative_path",
                "policy_digest", "policy_owner_key_id", "policy_owner_public_key_pem",
                *_IDENTITY_FIELDS)
    if binding.get("schema") != BINDING_SCHEMA or any(not binding.get(k) for k in required):
        raise GateError("C1_RC4_BINDING_INCOMPLETE")
    if binding["study_scope"] != STUDY_ID:
        raise GateError("C1_RC4_BINDING_SCOPE_MISMATCH")
    if require_owner and not all(identified(binding[k]) for k in _IDENTITY_FIELDS):
        raise GateError("C1_RC4_TRUST_ROOT_UNIDENTIFIED")
    relative = Path(binding["policy_relative_path"])
    if relative.is_absolute() or ".." in relative.parts:
        raise GateError("C1_RC4_POLICY_PATH_INVALID")
    binding["_policy_path"] = (path.parent / relative).resolve()
    if binding["_policy_path"].parent != path.parent.resolve():
        raise GateError("C1_RC4_POLICY_PATH_ESCAPE")
    return binding


def load_trust_store_rc4(root, *, require_owner: bool = True) -> tuple[dict, dict]:
    """binding -> policy digest -> owner signature -> key records. Fails closed."""
    root = Path(root)
    _check_root(root, require_owner)
    enforcement = assert_policy_owner(root, require_owner=require_owner)
    binding = load_binding(root, require_owner=require_owner)
    binding["_owner_enforcement"] = enforcement["owner_enforcement"]
    policy = load_policy(binding["_policy_path"], expected_digest=binding["policy_digest"],
                         require_owner=require_owner)
    if policy.get("owner_identity") != binding["owner_identity"] or \
            policy.get("policy_owner_key_id") != binding["policy_owner_key_id"]:
        raise GateError("C1_RC4_TRUST_POLICY_OWNER_MISMATCH")
    if not verify_signature(binding["policy_owner_public_key_pem"], policy,
                            policy.get("policy_signature", ""),
                            exclude=("policy_signature",)):
        raise GateError("C1_RC4_TRUST_POLICY_SIGNATURE_INVALID")

    active = []
    for key in policy["keys"]:
        if not isinstance(key, dict) or not key.get("key_id") or \
                not key.get("public_key_pem") or not isinstance(key.get("roles"), list) \
                or not isinstance(key.get("custodian"), str) or not key["custodian"].strip():
            raise GateError("C1_RC4_TRUST_KEY_RECORD")
        if spki_fingerprint(key["public_key_pem"]) != key.get("fingerprint"):
            raise GateError("C1_RC4_TRUST_KEY_FINGERPRINT")
        if require_owner and not identified(key["custodian"]):
            raise GateError("C1_RC4_TRUST_ROOT_UNIDENTIFIED")
        if key.get("status") == "ACTIVE" and key.get("revoked") is not True:
            active.append(key)
    if not active:
        raise GateError("C1_RC4_NO_ACTIVE_TRUST_KEY")
    return binding, policy


def check_separation(binding: dict, approval_key: dict, launch_key: dict) -> None:
    """Approval signing authority is separate from the launch operator and researcher."""
    norm = lambda s: " ".join(str(s).split()).casefold()  # noqa: E731
    approver, operator = norm(approval_key["custodian"]), norm(launch_key["custodian"])
    if approver == operator or approver == norm(binding["researcher_identity"]):
        raise GateError("C1_RC4_SEPARATION_OF_DUTIES")
    if approval_key.get("roles") and not set(APPROVAL_ROLES) & set(approval_key["roles"]):
        raise GateError("C1_RC4_SEPARATION_OF_DUTIES")
    if not set(LAUNCH_ROLES) & set(launch_key.get("roles") or []):
        raise GateError("C1_RC4_SEPARATION_OF_DUTIES")
