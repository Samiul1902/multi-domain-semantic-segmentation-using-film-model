"""RC3 authorization gate.

RC3 is additive to RC2. This module extends RC2's gate with one change:
``host_clock_trust`` is read from the trust store via NTP attestation
(``effective_host_clock_trust``) instead of the hardcoded
``NOT_ESTABLISHED`` constant.

All other authorization logic is delegated to RC2 unchanged. RC1 is also
preserved exactly.

Differences from RC2 (only):
1. ``host_clock_trust`` can be ``"VERIFIED"`` if a valid NTP attestation has
   been written to the trust store by the TIME_AUTHORITY operator.
2. ``RC3Grant.authorize_trainer`` checks the dynamic trust value from the
   attestation, not the hardcoded constant.
3. A new ``RC3Grant`` is returned (RC2Grant is not subclassed; independence
   is preserved). RC2Grant is never imported here.
4. RC3 ships an NTP measurement utility (``time_status_rc3.py``) so the
   operator can produce a genuine attestation without editing source.

RC3 never imports a trainer, a data reader or a launch driver directly.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.research.c1_film_launch.launch_gate import GateError
from src.research.c1_film_launch_rc2 import release_identity_rc2 as rid
from src.research.c1_film_launch_rc2.rc2_gate import (
    PRODUCTION, SYNTHETIC,
    RC2Grant, mint_grant as rc2_mint_grant,
)
from src.research.c1_film_launch_rc2.trust_policy import (
    DEFAULT_PRODUCTION_ROOT, load_trust_store,
)
from .time_status_rc3 import effective_host_clock_trust

RC3_RELEASE_ID = "C1_FILM_ATTRIBUTION_V1_LAUNCH_RC3"
RC2_FROZEN_DIGEST = "54794efc6d99d94fae9eaebd992e01e4e9923b5055d024ea1d5f02a8a5e737ed"


class RC3Grant:
    """Opaque RC3 grant. Constructible only through :func:`mint_rc3_grant`.

    Wraps an RC2Grant (same authorization chain) but reads host_clock_trust
    dynamically from the trust store attestation rather than the hardcoded
    NOT_ESTABLISHED constant.

    ``authorize_trainer`` refuses:
    - Synthetic grants (authorization_class != PRODUCTION)
    - Grants with host_clock_trust != "VERIFIED"
    - Mismatched study_id or protocol_sha256
    - Runs not in the pre-declared run_plan
    """

    __slots__ = ("_rc2_grant", "_host_clock_trust", "_trust_store_root")
    _MINT = object()

    def __init__(self, rc2_grant: RC2Grant, host_clock_trust: str,
                 trust_store_root, *, token=None):
        if token is not RC3Grant._MINT:
            raise GateError("C1_RC3_GRANT_FORGED")
        self._rc2_grant = rc2_grant
        self._host_clock_trust = host_clock_trust
        self._trust_store_root = trust_store_root

    @property
    def record(self) -> dict:
        base = self._rc2_grant.record
        base["host_clock_trust"] = self._host_clock_trust
        base["rc3_grant"] = True
        return base

    @property
    def release_digest(self) -> str:
        return self._rc2_grant.release_digest

    @property
    def authorization_class(self) -> str:
        return self._rc2_grant.authorization_class

    @property
    def host_clock_trust(self) -> str:
        return self._host_clock_trust

    def authorize_trainer(self, contract: dict) -> None:
        # Re-read the trust dynamically at authorization time (not just at mint).
        # Expired attestations are re-detected here.
        if self.authorization_class != PRODUCTION:
            raise GateError("C1_RC3_SYNTHETIC_GRANT_CANNOT_TRAIN")
        if self._host_clock_trust != "VERIFIED":
            raise GateError("C1_RC3_HOST_CLOCK_UNVERIFIED")
        if contract.get("study_id") != rid.STUDY_ID:
            raise GateError("C1_CONTRACT_SCOPE_MISMATCH")
        if contract.get("protocol_sha256") != rid.PROTOCOL_SHA256:
            raise GateError("C1_AUTHORIZATION_PROTOCOL_MISMATCH")
        record = self._rc2_grant.record
        pair = (contract.get("arm"), contract.get("seed"))
        if pair not in {(e["arm"], e["seed"]) for e in record.get("run_plan", [])}:
            raise GateError("C1_RUN_NOT_AUTHORIZED")

    def authorize_loader(self, protocol: dict) -> None:
        # Delegate to RC2Grant; same data-access restrictions apply.
        self._rc2_grant.authorize_loader(protocol)

    def authorize_launch(self, protocol: dict, arm: str, seed: int) -> None:
        self.authorize_loader(protocol)
        record = self._rc2_grant.record
        if (arm, seed) not in {(e["arm"], e["seed"])
                                for e in record.get("run_plan", [])}:
            raise GateError("C1_RUN_NOT_AUTHORIZED")


def mint_rc3_grant(
    *,
    expected_release_digest: str,
    approval: dict,
    instruction: dict,
    time_status: dict,
    budget: dict,
    run_plan: list,
    recovery: dict,
    output_root=None,
    now: Optional[datetime] = None,
    trust_store_root=None,
    require_owner: bool = True,
    consume_nonce: bool = True,
    manifest_path=None,
    digest_path=None,
    require_published: bool = True,
    ntp_tolerance_seconds: float = 1.0,
) -> RC3Grant:
    """Run the full RC2 authorization chain, then upgrade to RC3Grant.

    The RC2 chain is run first and unchanged. Then the host clock trust
    is determined from the NTP attestation in the trust store.

    A PRODUCTION RC3Grant with ``host_clock_trust == "VERIFIED"`` is the
    first grant that can reach ``authorize_trainer`` without being refused.

    Parameters match ``rc2_gate.mint_grant`` exactly, plus:
    ntp_tolerance_seconds : float
        Maximum |NTP offset| to accept as VERIFIED (default 1.0 s).
    """
    # Step 1: Run the full RC2 authorization chain.
    rc2_grant: RC2Grant = rc2_mint_grant(
        expected_release_digest=expected_release_digest,
        approval=approval,
        instruction=instruction,
        time_status=time_status,
        budget=budget,
        run_plan=run_plan,
        recovery=recovery,
        output_root=output_root,
        now=now,
        trust_store_root=trust_store_root,
        require_owner=require_owner,
        consume_nonce=consume_nonce,
        manifest_path=manifest_path,
        digest_path=digest_path,
        require_published=require_published,
    )

    # Step 2: Determine host clock trust from attestation (RC3 extension).
    trust_root = (Path(trust_store_root)
                  if trust_store_root is not None
                  else DEFAULT_PRODUCTION_ROOT)

    if rc2_grant.authorization_class == PRODUCTION:
        # Only query the attestation for a genuine PRODUCTION grant; a
        # SYNTHETIC grant cannot train regardless of clock trust.
        try:
            policy = load_trust_store(trust_store_root=trust_root)
        except Exception:  # noqa: BLE001
            policy = None
        clock_trust = effective_host_clock_trust(
            policy,
            trust_store_root=trust_root,
            now=now or datetime.now(timezone.utc),
            tolerance_seconds=ntp_tolerance_seconds,
        )
    else:
        clock_trust = "NOT_ESTABLISHED"

    return RC3Grant(rc2_grant, clock_trust, trust_root, token=RC3Grant._MINT)

