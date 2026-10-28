"""Additive RC2 trust/time layer; RC1 remains immutable and unmodified.

RC2 replaces RC1's two authorization defects — a hardcoded empty approval-key
allowlist and an unsigned caller-declared ``trusted_time`` — with an external
institutional trust store and a signed, identity-bound, single-use time proof.

RC2 ships no trust keys and no trust policy. Production trust is unprovisioned
and the gate is fail-closed. Host clock truth remains ``NOT_ESTABLISHED``, so
production training is refused even with a valid approval. No scientific
execution is enabled here.
"""
from __future__ import annotations

__all__ = ["LAUNCH_RELEASE_ID", "release_status"]

LAUNCH_RELEASE_ID = "C1_FILM_ATTRIBUTION_V1_LAUNCH_RC2"


def release_status() -> dict:
    """Read-only RC2 release identity report. Never authorizes anything."""
    from . import release_identity_rc2 as rid
    try:
        report = rid.verify_release_rc2()
        report["verified"] = True
    except rid.ReleaseIdentityError as exc:
        report = {"verified": False, "error": str(exc)}
    report["launch_release_id"] = LAUNCH_RELEASE_ID
    report["scientific_execution"] = "NOT_AUTHORIZED"
    return report
