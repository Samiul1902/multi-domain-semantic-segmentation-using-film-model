"""RC2 authorization gate: external trust policy + signed time/status proof.

Differences from RC1, all of which the RC1 audit identified as defects:

1. **Trust is external.** The approval-key allowlist is no longer a Python
   constant. Trust comes from a signed policy in an OS-scope trust store outside
   the repository (see :mod:`.trust_policy`). This release ships no trust store,
   so production is unprovisioned and fail-closed — but provisioning is an
   institutional data operation, not a source edit.
2. **Refusals are diagnostic.** An untrusted key, a revoked key, a role failure
   and a bad signature each produce a distinct code. RC1 collapsed all of them
   into ``C1_TRUST_ANCHOR_NOT_ALLOWLISTED``.
3. **Time is signed and bound.** An unsigned caller-declared ``trusted_time``
   dictionary is no longer accepted. A signed, identity-bound, single-use proof
   is required (see :mod:`.time_status`).
4. **Synthetic authority cannot train.** A grant minted against a non-production
   trust store is classed ``SYNTHETIC_TEST`` and ``authorize_trainer`` refuses it
   unconditionally, so the positive test path can never enable real training.
5. **The host-clock blocker is preserved.** A signature over a time claim makes
   the claim attributable, not true. ``host_clock_trust`` is ``NOT_ESTABLISHED``
   and production training is refused until host time is independently verified
   (O8). This module does not touch the Windows clock.

RC2 never imports a trainer, a data reader or a launch driver; it produces a
validation record and an opaque grant only.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from src.research.c1_film_launch import launch_gate as rc1
from src.research.c1_film_launch import release_identity as rc1_identity

from . import release_identity_rc2 as rid
from .time_status import HOST_CLOCK_TRUST, verify_time_status
from .trust_policy import (APPROVAL_ROLES, DEFAULT_PRODUCTION_ROOT, LAUNCH_ROLES,
                           GateError, load_trust_store, verify_policy_signature)

RC2_RELEASE_ID = "C1_FILM_ATTRIBUTION_V1_LAUNCH_RC2"
PRODUCTION = "PRODUCTION"
SYNTHETIC = "SYNTHETIC_TEST"


def _structural(release: dict, approval, instruction, budget, run_plan, recovery,
                output_root, now) -> dict:
    """Phase A — structural validation, reusing RC1's precise named refusals.

    RC1's validators are imported read-only; nothing in RC1 is modified. They are
    reused deliberately so that scope, budget, population, prohibited-split,
    recovery and separate-launch semantics are identical between releases.
    """
    protocol = rc1_identity.json.loads(rc1_identity.PROTOCOL_PATH.read_text(encoding="utf-8-sig"))
    if protocol.get("study_id") != rid.STUDY_ID:
        raise GateError("C1_PROTOCOL_IDENTITY_DRIFT")
    if protocol.get("execution", {}).get("separate_launch_required") is not True:
        raise GateError("C1_PROTOCOL_IDENTITY_DRIFT")

    approved = rc1._check_approval_structure(approval)
    if approved["release_digest"] != release["release_digest"]:
        raise GateError("C1_AUTHORIZATION_RELEASE_MISMATCH")
    rc1._check_populations(protocol, approved)
    rc1._check_prohibited_paths(protocol, approved)
    rc1._check_budget(budget, run_plan)
    rc1._check_recovery(recovery, release["release_digest"], output_root)
    rc1._check_launch_instruction(instruction, approved, release["release_digest"],
                                  run_plan, now)
    return protocol


def validate_authorization(*, expected_release_digest: str, approval: dict,
                           instruction: dict, time_status: dict, budget: dict,
                           run_plan: list, recovery: dict, output_root=None,
                           now: datetime | None = None,
                           trust_store_root=None, require_owner: bool = True,
                           consume_nonce: bool = True,
                           manifest_path=None, digest_path=None,
                           require_published: bool = True) -> dict:
    """Run the full RC2 chain. Returns a validation record; raises on refusal."""
    now = now or datetime.now(timezone.utc)
    output_root = (Path(output_root) if output_root is not None
                   else rid.ROOT / "experiments/c1_film_attribution_v1")

    release = rid.verify_release_rc2(require_published=require_published,
                                     manifest_path=manifest_path)
    if not isinstance(expected_release_digest, str) or \
            expected_release_digest != release["release_digest"]:
        raise GateError("C1_RC2_RELEASE_DIGEST_MISMATCH")

    protocol = _structural(release, approval, instruction, budget, run_plan,
                           recovery, output_root, now)

    # --- Trust: external store, not a module constant ------------------------
    root = Path(trust_store_root) if trust_store_root is not None else DEFAULT_PRODUCTION_ROOT
    if require_owner:
        if root.resolve() != Path(DEFAULT_PRODUCTION_ROOT).resolve():
            raise GateError("C1_RC2_TRUST_STORE_NOT_PRODUCTION")
        authorization_class = PRODUCTION
    else:
        authorization_class = SYNTHETIC

    binding, policy = load_trust_store(root, require_owner=require_owner)
    approval_key = verify_policy_signature(policy, approval, APPROVAL_ROLES)
    launch_key = verify_policy_signature(policy, instruction, LAUNCH_ROLES)

    # --- Time: signed, bound, single-use ------------------------------------
    status = verify_time_status(
        policy, time_status,
        release_digest=release["release_digest"],
        authorization_id=approval["authorization_id"],
        launch_id=instruction["launch_id"],
        now=now, ledger_root=output_root, consume_nonce=consume_nonce)

    return {
        "classification": "NON_SCIENTIFIC_RC2_AUTHORIZATION_VALIDATION",
        "release_id": release["release_id"],
        "release_digest": release["release_digest"],
        "supersedes_release_digest": release["rc1_release_digest"],
        "authorization_class": authorization_class,
        "policy_digest": policy.get("policy_digest"),
        "policy_owner_identity": binding["owner_identity"],
        "policy_owner_enforcement": binding.get("_owner_enforcement"),
        "approval_key_id": approval_key["key_id"],
        "launch_key_id": launch_key["key_id"],
        "time_key_id": status["key_id"],
        "nonce_sha256": status["nonce_sha256"],
        "host_clock_trust": status["host_clock_trust"],
        "study_id": protocol["study_id"],
        "authorization_id": approval["authorization_id"],
        "launch_id": instruction["launch_id"],
        "run_plan": list(run_plan),
    }


class RC2Grant:
    """Opaque capability. Constructible only through :func:`mint_grant`.

    ``authorize_trainer`` refuses synthetic grants unconditionally and refuses
    production grants while host time is unverified. RC2 therefore cannot launch
    science even with a perfectly formed approval: external authorization and
    host remediation are both still outstanding.
    """

    __slots__ = ("_record",)
    _MINT = object()

    def __init__(self, record: dict, *, token=None):
        if token is not RC2Grant._MINT:
            raise GateError("C1_RC2_GRANT_FORGED")
        self._record = dict(record)

    @property
    def record(self) -> dict:
        return dict(self._record)

    @property
    def release_digest(self) -> str:
        return self._record["release_digest"]

    @property
    def authorization_class(self) -> str:
        return self._record["authorization_class"]

    @property
    def host_clock_trust(self) -> str:
        return self._record["host_clock_trust"]

    def _reverify(self) -> str:
        try:
            release = rid.verify_release_rc2()
        except rid.ReleaseIdentityError as exc:
            raise GateError(str(exc)) from exc
        if release["release_digest"] != self._record["release_digest"]:
            raise GateError("C1_RC2_RELEASE_DIGEST_STALE")
        return release["release_digest"]

    def authorize_trainer(self, contract: dict) -> None:
        self._reverify()
        if self.authorization_class != PRODUCTION:
            raise GateError("C1_RC2_SYNTHETIC_GRANT_CANNOT_TRAIN")
        if self.host_clock_trust != "VERIFIED":
            raise GateError("C1_RC2_HOST_CLOCK_UNVERIFIED")
        if contract.get("study_id") != rid.STUDY_ID:
            raise GateError("C1_CONTRACT_SCOPE_MISMATCH")
        if contract.get("protocol_sha256") != rid.PROTOCOL_SHA256:
            raise GateError("C1_AUTHORIZATION_PROTOCOL_MISMATCH")
        pair = (contract.get("arm"), contract.get("seed"))
        if pair not in {(e["arm"], e["seed"]) for e in self._record["run_plan"]}:
            raise GateError("C1_RUN_NOT_AUTHORIZED")

    def authorize_loader(self, protocol: dict) -> None:
        """Gate for real-data loader construction.

        A synthetic grant is refused here as well as in ``authorize_trainer``.
        This matters because ``real_loader_factory`` reaches the real datasets
        through this method: allowing a synthetic grant through would let the
        positive test path touch real data even without training.
        """
        self._reverify()
        if self.authorization_class != PRODUCTION:
            raise GateError("C1_RC2_SYNTHETIC_GRANT_CANNOT_ACCESS_DATA")
        if protocol.get("study_id") != rid.STUDY_ID:
            raise GateError("C1_PROTOCOL_IDENTITY_DRIFT")
        if set(protocol["dataset"]["populations"]) != {"TRAIN", "VAL"}:
            raise GateError("C1_PROHIBITED_SPLIT")

    def authorize_launch(self, protocol: dict, arm: str, seed: int) -> None:
        self.authorize_loader(protocol)
        if (arm, seed) not in {(e["arm"], e["seed"]) for e in self._record["run_plan"]}:
            raise GateError("C1_RUN_NOT_AUTHORIZED")


def mint_grant(**kwargs) -> RC2Grant:
    record = validate_authorization(**kwargs)
    return RC2Grant(record, token=RC2Grant._MINT)
