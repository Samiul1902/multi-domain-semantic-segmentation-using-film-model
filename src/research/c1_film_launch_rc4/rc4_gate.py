"""RC4 authorization gate.

Verified call chain (contrast with RC3, which delegated to RC2 and never invoked
``verify_release_rc3``):

    mint_rc4_grant
      -> release_identity_rc4.verify_release_rc4      (own identity, live predecessors)
      -> expected digest compared to the RC4 digest   (RC1/RC2/RC3 digests refused)
      -> approval.release_id / release_digest bound to RC4
      -> rc1 structural checks (scope, populations, prohibited splits, budget,
         recovery, launch instruction) reused read-only with the RC4 digest
      -> trust_rc4.load_trust_store_rc4               (RC4 root; legacy root refused)
      -> approval / launch signatures, custodian separation, revocation, expiry
      -> rc2 verify_time_status (digest-bound, signed, single-use nonce ledger)
    RC4Grant.authorize_trainer / authorize_loader / authorize_launch
      -> _reverify: RC4 release re-verified, digest compared to the grant, trust store
         reloaded, policy digest compared, revocation re-checked, clock re-evaluated.

Nothing here imports a trainer or data reader; ``launch_driver_rc4`` is the only
real-data entry point.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.research.c1_film_launch import launch_gate as rc1
from src.research.c1_film_launch.launch_gate import GateError
from src.research.c1_film_launch_rc2.rc2_gate import PRODUCTION, SYNTHETIC, _structural
from src.research.c1_film_launch_rc2.time_status import parse_utc, verify_time_status
from src.research.c1_film_launch_rc2.trust_policy import (
    APPROVAL_ROLES, LAUNCH_ROLES, verify_policy_signature,
)
from src.research.c1_film_launch_rc3.time_status_rc3 import effective_host_clock_trust

from . import release_identity_rc4 as rid
from . import trust_rc4

RC4_RELEASE_ID = rid.RELEASE_ID
DEFAULT_TOLERANCE_SECONDS = 1.0


def _verify_release() -> dict:
    try:
        return rid.verify_release_rc4()
    except rid.ReleaseIdentityError as exc:
        raise GateError(str(exc)) from exc


def _clock_trust(policy: dict, root, now: datetime, tolerance: float) -> str:
    return effective_host_clock_trust(policy, trust_store_root=root, now=now,
                                      tolerance_seconds=tolerance)


def _check_approval_identity(approval: dict, release: dict, policy: dict, now: datetime) -> None:
    if approval.get("release_id") != rid.RELEASE_ID:
        raise GateError("C1_RC4_APPROVAL_RELEASE_ID_MISMATCH")
    if approval.get("authorization_id") in (policy.get("revoked_authorizations") or []):
        raise GateError("C1_RC4_AUTHORIZATION_REVOKED")
    if approval.get("expires_at") is not None and now > parse_utc(approval["expires_at"],
                                                                  "C1_RC4_APPROVAL_EXPIRY_FORMAT"):
        raise GateError("C1_RC4_APPROVAL_EXPIRED")


def validate_authorization(*, expected_release_digest: str, approval: dict,
                           instruction: dict, time_status: dict, budget: dict,
                           run_plan: list, recovery: dict, output_root=None,
                           now: Optional[datetime] = None, trust_store_root=None,
                           require_owner: bool = True, consume_nonce: bool = True,
                           ntp_tolerance_seconds: float = DEFAULT_TOLERANCE_SECONDS) -> dict:
    now = now or datetime.now(timezone.utc)
    output_root = (Path(output_root) if output_root is not None
                   else rid.ROOT / "experiments/c1_film_attribution_v1")

    release = _verify_release()
    if not isinstance(expected_release_digest, str):
        raise GateError("C1_RC4_RELEASE_DIGEST_MISMATCH")
    if expected_release_digest in rid.PREDECESSOR_DIGESTS:
        raise GateError("C1_RC4_PREDECESSOR_IDENTITY_REJECTED")
    if expected_release_digest != release["release_digest"]:
        raise GateError("C1_RC4_RELEASE_DIGEST_MISMATCH")

    if not isinstance(approval, dict):
        raise GateError("C1_AUTHORIZATION_REQUIRED")
    if approval.get("release_digest") in rid.PREDECESSOR_DIGESTS or \
            approval.get("release_id") in rid.PREDECESSOR_IDS:
        raise GateError("C1_RC4_PREDECESSOR_IDENTITY_REJECTED")

    root = Path(trust_store_root) if trust_store_root is not None else trust_rc4.PRODUCTION_ROOT
    binding, policy = trust_rc4.load_trust_store_rc4(root, require_owner=require_owner)

    _check_approval_identity(approval, release, policy, now)
    protocol = _structural(release, approval, instruction, budget, run_plan, recovery,
                           output_root, now)

    approval_key = verify_policy_signature(policy, approval, APPROVAL_ROLES)
    launch_key = verify_policy_signature(policy, instruction, LAUNCH_ROLES)
    trust_rc4.check_separation(binding, approval_key, launch_key)

    status = verify_time_status(
        policy, time_status, release_digest=release["release_digest"],
        authorization_id=approval["authorization_id"], launch_id=instruction["launch_id"],
        now=now, ledger_root=output_root, consume_nonce=consume_nonce)

    authorization_class = PRODUCTION if require_owner else SYNTHETIC
    return {
        "classification": "NON_SCIENTIFIC_RC4_AUTHORIZATION_VALIDATION",
        "release_id": release["release_id"],
        "release_digest": release["release_digest"],
        "code_digest": release["code_digest"],
        "protocol_sha256": rid.PROTOCOL_SHA256,
        "supersedes": dict(release["supersedes"]),
        "authorization_class": authorization_class,
        "trust_root": str(root),
        "policy_digest": policy.get("policy_digest"),
        "institution_name": binding["institution_name"],
        "approving_authority": binding["approving_authority"],
        "approval_key_id": approval_key["key_id"],
        "launch_key_id": launch_key["key_id"],
        "time_key_id": status["key_id"],
        "nonce_sha256": status["nonce_sha256"],
        "host_clock_trust": (_clock_trust(policy, root, now, ntp_tolerance_seconds)
                             if authorization_class == PRODUCTION else "NOT_ESTABLISHED"),
        "ntp_tolerance_seconds": ntp_tolerance_seconds,
        "study_id": rid.STUDY_ID,
        "authorization_id": approval["authorization_id"],
        "launch_id": instruction["launch_id"],
        "run_plan": list(run_plan),
    }


class RC4Grant:
    """Opaque capability, constructible only through :func:`mint_rc4_grant`."""

    __slots__ = ("_record",)
    _MINT = object()

    def __init__(self, record: dict, *, token=None):
        if token is not RC4Grant._MINT:
            raise GateError("C1_RC4_GRANT_FORGED")
        self._record = dict(record)

    @property
    def record(self) -> dict:
        return dict(self._record)

    @property
    def release_id(self) -> str:
        return self._record["release_id"]

    @property
    def release_digest(self) -> str:
        return self._record["release_digest"]

    @property
    def authorization_class(self) -> str:
        return self._record["authorization_class"]

    def _reverify(self, *, require_clock: bool) -> None:
        """Re-establish release identity, trust and clock at the moment of use."""
        record = self._record
        if record["release_id"] != rid.RELEASE_ID or \
                record["release_digest"] in rid.PREDECESSOR_DIGESTS:
            raise GateError("C1_RC4_PREDECESSOR_IDENTITY_REJECTED")
        release = _verify_release()
        if release["release_digest"] != record["release_digest"] or \
                release["code_digest"] != record["code_digest"]:
            raise GateError("C1_RC4_RELEASE_DIGEST_STALE")

        production = record["authorization_class"] == PRODUCTION
        root = Path(record["trust_root"])
        _, policy = trust_rc4.load_trust_store_rc4(root, require_owner=production)
        if policy.get("policy_digest") != record["policy_digest"]:
            raise GateError("C1_RC4_TRUST_POLICY_CHANGED")
        if record["authorization_id"] in (policy.get("revoked_authorizations") or []):
            raise GateError("C1_RC4_AUTHORIZATION_REVOKED")
        if production and require_clock and _clock_trust(
                policy, root, datetime.now(timezone.utc),
                record["ntp_tolerance_seconds"]) != "VERIFIED":
            raise GateError("C1_RC4_HOST_CLOCK_UNVERIFIED")

    def authorize_trainer(self, contract: dict) -> None:
        self._reverify(require_clock=False)
        if self.authorization_class != PRODUCTION:
            raise GateError("C1_RC4_SYNTHETIC_GRANT_CANNOT_TRAIN")
        self._reverify(require_clock=True)
        if contract.get("study_id") != rid.STUDY_ID:
            raise GateError("C1_CONTRACT_SCOPE_MISMATCH")
        if contract.get("protocol_sha256") != rid.PROTOCOL_SHA256:
            raise GateError("C1_AUTHORIZATION_PROTOCOL_MISMATCH")
        self._require_run(contract.get("arm"), contract.get("seed"))

    def authorize_loader(self, protocol: dict) -> None:
        self._reverify(require_clock=False)
        if self.authorization_class != PRODUCTION:
            raise GateError("C1_RC4_SYNTHETIC_GRANT_CANNOT_ACCESS_DATA")
        self._reverify(require_clock=True)
        if protocol.get("study_id") != rid.STUDY_ID:
            raise GateError("C1_PROTOCOL_IDENTITY_DRIFT")
        if set(protocol["dataset"]["populations"]) != {"TRAIN", "VAL"}:
            raise GateError("C1_PROHIBITED_SPLIT")
        rc1._check_prohibited_paths(protocol, {})

    def authorize_launch(self, protocol: dict, arm: str, seed: int) -> None:
        self.authorize_loader(protocol)
        self._require_run(arm, seed)

    def _require_run(self, arm, seed) -> None:
        if (arm, seed) not in {(e["arm"], e["seed"]) for e in self._record["run_plan"]}:
            raise GateError("C1_RUN_NOT_AUTHORIZED")


def mint_rc4_grant(**kwargs) -> RC4Grant:
    return RC4Grant(validate_authorization(**kwargs), token=RC4Grant._MINT)
