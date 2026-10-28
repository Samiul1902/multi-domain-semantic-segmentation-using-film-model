"""Sole real-data entry point for a C1 launch. Requires a fully verified grant.

Nothing in this module can be reached without ``mint_grant`` returning, which
requires an allowlisted trust anchor — and this release ships an empty
allowlist. The module therefore exists to make the future launch boundary
concrete and testable, not to enable execution today.

The frozen preparation gate (``readiness.assert_launch_allowed``) is still called
through ``verify_preparation``/``make_contract`` and still raises unconditionally;
it has not been weakened.
"""
from __future__ import annotations

from pathlib import Path

from .launch_gate import GateError, LaunchGrant, mint_grant

STUDY_ID = "C1_FILM_ATTRIBUTION_V1"


def launch(arm: str, seed: int, *, expected_release_digest: str, approval: dict,
           instruction: dict, anchor_path, budget: dict, run_plan: list,
           recovery: dict, trusted_time: dict, output_root=None, resume: bool = False):
    """Authorize then run one C1 arm/seed. Raises GateError on any refusal."""
    from ..c1_film.integration_contract import make_contract, verify_preparation
    from ..c1_film.train_driver import real_loader_factory
    from ..c1_film.training_engine import Trainer

    protocol = verify_preparation()  # Frozen package must still be byte-identical.

    grant: LaunchGrant = mint_grant(
        expected_release_digest=expected_release_digest,
        approval=approval,
        instruction=instruction,
        anchor_path=anchor_path,
        budget=budget,
        run_plan=run_plan,
        recovery=recovery,
        trusted_time=trusted_time,
        output_root=output_root,
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
