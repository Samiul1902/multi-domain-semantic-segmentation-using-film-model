"""Sole real-data entry point for an RC4 launch. Requires a verified RC4 grant.

The scientific path is unchanged from RC3; only the grant (release identity and
institutional trust root) differs. ``require_owner`` is not exposed here, so this
driver can only produce PRODUCTION grants against the RC4 institutional root.
Each logical run needs its own freshly signed, single-use time proof.
"""
from __future__ import annotations

from pathlib import Path

from .rc4_gate import GateError, RC4Grant, mint_rc4_grant


def launch(arm: str, seed: int, *, expected_release_digest: str, approval: dict,
           instruction: dict, time_status: dict, budget: dict, run_plan: list,
           recovery: dict, output_root=None, resume: bool = False,
           ntp_tolerance_seconds: float = 1.0):
    """Authorize then run one C1 arm/seed under RC4. Raises GateError on refusal."""
    from ..c1_film.integration_contract import make_contract, verify_preparation
    from ..c1_film.train_driver import real_loader_factory
    from ..c1_film.training_engine import Trainer

    protocol = verify_preparation()  # frozen package must still be byte-identical

    grant: RC4Grant = mint_rc4_grant(
        expected_release_digest=expected_release_digest, approval=approval,
        instruction=instruction, time_status=time_status, budget=budget,
        run_plan=run_plan, recovery=recovery, output_root=output_root,
        ntp_tolerance_seconds=ntp_tolerance_seconds)
    grant.authorize_launch(protocol, arm, seed)

    import torch
    if not torch.cuda.is_available():
        raise GateError("C1_CUDA_REQUIRED")

    contract = make_contract(arm, seed, synthetic=False, device="cuda")
    loaders = real_loader_factory(protocol, grant=grant)
    root = (Path(output_root) if output_root is not None
            else Path(__file__).resolve().parents[3] / "experiments/c1_film_attribution_v1")
    return Trainer(contract, grant=grant).run(root / f"seed{seed}" / arm, loaders,
                                              resume=resume)
