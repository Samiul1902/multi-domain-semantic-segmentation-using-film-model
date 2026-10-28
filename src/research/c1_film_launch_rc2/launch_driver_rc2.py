"""Sole real-data entry point for an RC2 launch. Requires a verified RC2 grant.

This module exists to make the future launch boundary concrete and testable. It
cannot execute today, and that is by construction rather than by accident:

* production trust is unprovisioned (no OS-scope trust store exists), so
  :func:`rc2_gate.mint_grant` refuses with ``C1_RC2_TRUST_STORE_MISSING_OR_SYMLINK``;
* even with a provisioned store and a perfectly signed approval, the grant is
  classed ``PRODUCTION`` only if the store is the canonical OS-scope path, and
  ``RC2Grant.authorize_trainer`` then still refuses with
  ``C1_RC2_HOST_CLOCK_UNVERIFIED`` because host time is not independently
  verified (O8 outstanding).

The frozen preparation gate (``readiness.assert_launch_allowed``) is still called
through ``verify_preparation``/``make_contract`` and still raises unconditionally;
it has not been weakened.
"""
from __future__ import annotations

from pathlib import Path

from .rc2_gate import GateError, RC2Grant, mint_grant

STUDY_ID = "C1_FILM_ATTRIBUTION_V1"


def launch(arm: str, seed: int, *, expected_release_digest: str, approval: dict,
           instruction: dict, time_status: dict, budget: dict, run_plan: list,
           recovery: dict, output_root=None, resume: bool = False,
           trust_store_root=None):
    """Authorize then run one C1 arm/seed under RC2. Raises GateError on refusal."""
    from ..c1_film.integration_contract import make_contract, verify_preparation
    from ..c1_film.train_driver import real_loader_factory
    from ..c1_film.training_engine import Trainer

    protocol = verify_preparation()  # Frozen package must still be byte-identical.

    grant: RC2Grant = mint_grant(
        expected_release_digest=expected_release_digest,
        approval=approval,
        instruction=instruction,
        time_status=time_status,
        budget=budget,
        run_plan=run_plan,
        recovery=recovery,
        output_root=output_root,
        trust_store_root=trust_store_root,
    )
    grant.authorize_launch(protocol, arm, seed)

    import torch
    if not torch.cuda.is_available():
        raise GateError("C1_CUDA_REQUIRED")

    contract = make_contract(arm, seed, synthetic=False, device="cuda")
    loaders = real_loader_factory(protocol, grant=grant)
    root = (Path(output_root) if output_root is not None
            else Path(__file__).resolve().parents[3] / "experiments/c1_film_attribution_v1")
    output = root / f"seed{seed}" / arm
    return Trainer(contract, grant=grant).run(output, loaders, resume=resume)
