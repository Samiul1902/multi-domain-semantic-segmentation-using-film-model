"""C1 launch release package (additive). No scientific execution is enabled here.

This package closes the executable-identity gap left by the frozen preparation
package without modifying it. The frozen manifest binds only three of the eight
``src/research/c1_film`` modules; ``manifest_v2.json`` binds all eight plus both
C1 test files, every launch source, and the result-affecting data/loss/selection
dependencies.

``AUTHORIZED_ANCHOR_SHA256`` in :mod:`launch_gate` is empty, so no approval —
local dict, institutional string, or synthetic key — can authorize execution in
this release. See that module's docstring for the two-phase rationale.
"""
from __future__ import annotations

__all__ = [
    "LAUNCH_RELEASE_ID",
    "release_status",
]

LAUNCH_RELEASE_ID = "C1_FILM_ATTRIBUTION_V1_LAUNCH_RC1"


def release_status() -> dict:
    """Read-only release identity report. Never authorizes anything."""
    from . import release_identity as rid
    try:
        report = rid.verify_release()
        report["verified"] = True
    except rid.ReleaseIdentityError as exc:
        report = {"verified": False, "error": str(exc)}
    report["launch_release_id"] = LAUNCH_RELEASE_ID
    report["scientific_execution"] = "NOT_AUTHORIZED"
    return report
