"""Ed25519 envelope verification. No repository-supplied production trust root."""
import base64
from datetime import datetime, timezone
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from .contracts import (require, Refusal, canonical, CONFIG, INPUT_SHAS,
                        CHECKPOINT_SHAS, PROTOCOL_SHA, ERRATUM_SHA, EXCLUSIONS)


def production_authorization(envelope=None):
    # Deliberately no path, env, CLI key, or test-key injection option. A future
    # release must integrate an independently provisioned institutional trust
    # service, revocation policy, and explicit launch record, then be rehashed.
    raise Refusal("E_AUTHORIZATION_TRUST_ANCHOR_ABSENT",
                  "No independently established supervisor trust service; production blocked")


def verify_envelope(envelope, trusted_keys, harness_sha, *, now=None,
                    revoked_ids=frozenset(), revoked_keys=frozenset()):
    """Pure verifier. trusted_keys MUST come from a trusted caller, never envelope.

    This primitive is used by isolated tests only in this disabled release.
    Each key record binds raw public-key bytes AND the independently named approver.
    """
    require(isinstance(envelope, dict) and bool(envelope.get("signature")),
            "E_AUTHORIZATION_UNSIGNED")
    require(bool(trusted_keys), "E_AUTHORIZATION_TRUST_ANCHOR_ABSENT")
    require(set(envelope) == {"key_id", "payload", "signature"}, "E_AUTHORIZATION_SCOPE_MISMATCH")
    kid = envelope["key_id"]
    require(isinstance(kid, str) and kid in trusted_keys and kid not in revoked_keys,
            "E_AUTHORIZATION_SIGNATURE_INVALID", "untrusted or revoked signer")
    payload = envelope["payload"]
    try:
        signature = base64.b64decode(envelope["signature"], validate=True)
        Ed25519PublicKey.from_public_bytes(trusted_keys[kid]["public_key"]).verify(signature, canonical(payload))
    except (InvalidSignature, ValueError, TypeError, KeyError):
        raise Refusal("E_AUTHORIZATION_SIGNATURE_INVALID") from None
    expected = dict(study_identifier="BARR-M1", classification="DESCRIPTIVE_POLICY_COMPARISON",
        arms=CONFIG["arms"], population="ROUTER_DEVELOPMENT", population_n=4957,
        evaluation_class="IN_SAMPLE", execution_mode="CPU_ONLY_RE_ANALYSIS_ONLY",
        input_shas=INPUT_SHAS, checkpoint_shas=CHECKPOINT_SHAS,
        protocol_sha256=PROTOCOL_SHA, erratum_sha256=ERRATUM_SHA, exclusions=EXCLUSIONS)
    fields = set(expected) | {"authorization_id", "authorized_by", "approval_date",
                            "expires_at", "harness_sha256"}
    require(isinstance(payload, dict) and set(payload) == fields, "E_AUTHORIZATION_SCOPE_MISMATCH")
    require(all(canonical(payload[k]) == canonical(v) for k, v in expected.items()),
            "E_AUTHORIZATION_SCOPE_MISMATCH")
    require(payload["harness_sha256"] == harness_sha, "E_AUTHORIZATION_HARNESS_SHA_MISMATCH")
    require(isinstance(payload["authorization_id"], str) and bool(payload["authorization_id"].strip())
            and payload["authorization_id"] not in revoked_ids, "E_AUTHORIZATION_SCOPE_MISMATCH")
    require(payload["authorized_by"] == trusted_keys[kid]["approver"], "E_AUTHORIZATION_SCOPE_MISMATCH")
    try:
        start = datetime.fromisoformat(payload["approval_date"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(payload["expires_at"].replace("Z", "+00:00"))
        current = now or datetime.now(timezone.utc)
        require(start.tzinfo is not None and end.tzinfo is not None and start <= current < end,
                "E_AUTHORIZATION_SCOPE_MISMATCH", "invalid approval validity interval")
    except (ValueError, TypeError, AttributeError):
        raise Refusal("E_AUTHORIZATION_SCOPE_MISMATCH", "invalid date or validity interval") from None
    return payload.copy()
