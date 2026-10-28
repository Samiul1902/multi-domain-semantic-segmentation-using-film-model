"""C1 CLI: synthetic mini-loops supported; real-data entry is hard blocked.

The frozen protocol disables scientific execution. This adapter integrates its
future loader path but never treats local dictionaries as authentic approval.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from .integration_contract import make_contract, validate_synthetic_output, verify_preparation
from .readiness import ROOT, ReadinessError, assert_launch_allowed


def _require_grant(grant):
    if grant is None:
        raise ReadinessError("C1_LAUNCH_GRANT_REQUIRED")
    authorize = getattr(grant, "authorize_loader", None)
    if not callable(authorize):
        raise ReadinessError("C1_LAUNCH_GRANT_INVALID")
    return authorize


def real_loader_factory(protocol, *, grant=None):
    """Integrated adapter; refuses before importing any data reader unless granted."""
    _require_grant(grant)(protocol)
    return _verified_loader_adapter(protocol, grant=grant)


def _verified_loader_adapter(protocol, *, grant=None):
    # Internal integration body; still gated if invoked directly.
    _require_grant(grant)(protocol)
    import hashlib
    from src.data.domain_balanced_sampler import build_domain_balanced_sampler, derive_epoch_seed
    from src.data.loaders import create_loader
    from src.data.multidomain_dataset import MultiDomainDataset, harmonized_collate
    from .readiness import validate_population_request

    datasets = {}
    for split, info in protocol["dataset"]["populations"].items():
        validate_population_request(protocol["dataset"], split, info["path"], info["n"], info["sha256"])
        path = ROOT / info["path"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != info["sha256"]:
            raise ReadinessError("C1_MANIFEST_BYTES_CHANGED")
        ds = MultiDomainDataset(path, split, size=512, train=split == "TRAIN", channel_policy="RGB_3CH")
        if len(ds) != info["n"] or ds.frame["sample_id"].duplicated().any():
            raise ReadinessError("C1_POPULATION_ROWS_CHANGED")
        from .readiness import TASK_IDS
        if any(TASK_IDS.get(str(d)) != int(t) for d, t in zip(ds.frame["dataset"], ds.frame["task_id"])):
            raise ReadinessError("C1_MANIFEST_TASK_MAPPING")
        datasets[split] = ds
    if set(datasets["TRAIN"].frame["sample_id"]) & set(datasets["VAL"].frame["sample_id"]):
        raise ReadinessError("C1_TRAIN_VAL_OVERLAP")

    def factory(seed, epoch):
        tr, va = datasets["TRAIN"], datasets["VAL"]
        sampler = build_domain_balanced_sampler(tr.frame["dataset"].tolist(), seed, epoch)
        return (create_loader(tr, 4, False, derive_epoch_seed(seed, epoch), num_workers=4,
                              persistent_workers=False, collate_fn=harmonized_collate, sampler=sampler),
                create_loader(va, 8, False, seed, num_workers=2, collate_fn=harmonized_collate))
    return factory


def run_real(arm, seed, *, approval=None, launch=None, grant=None):
    """Real-data entry. Requires a verified LaunchGrant; approval dicts never suffice.

    ``approval`` and ``launch`` are retained only so that legacy self-asserted
    dictionaries raise a scope error instead of a TypeError. They are never
    consulted for authorization: a local dict containing approved=true, an
    institutional name, or a signature-shaped string cannot grant execution.
    """
    protocol = verify_preparation()  # Frozen package must still be intact.
    if grant is None:
        raise ReadinessError("C1_LAUNCH_GRANT_REQUIRED")
    authorize = getattr(grant, "authorize_launch", None)
    if not callable(authorize):
        raise ReadinessError("C1_LAUNCH_GRANT_INVALID")
    authorize(protocol, arm, seed)
    import torch
    from .training_engine import Trainer
    if not torch.cuda.is_available():
        raise ReadinessError("C1_CUDA_REQUIRED")
    contract = make_contract(arm, seed, synthetic=False, device="cuda")
    loaders = real_loader_factory(protocol, grant=grant)
    output = ROOT / "experiments/c1_film_attribution_v1" / f"seed{seed}" / arm
    return Trainer(contract, grant=grant).run(output, loaders)


def run_synthetic(arm, seed, output: Path, *, resume=False):
    from .synthetic_fixture import fixture_loaders
    from .training_engine import Trainer
    root = validate_synthetic_output(output)
    contract = make_contract(arm, seed, synthetic=True)
    return Trainer(contract).run(root, fixture_loaders, resume=resume)


def main(argv=None):
    p = argparse.ArgumentParser(description="C1 gated training integration; synthetic-only in this release")
    p.add_argument("--arm", choices=("C1-T", "C1-C"), required=True)
    p.add_argument("--seed", choices=(42, 123, 3407), type=int, required=True)
    p.add_argument("--synthetic", action="store_true")
    p.add_argument("--output", type=Path)
    p.add_argument("--resume", action="store_true")
    args = p.parse_args(argv)
    if not args.synthetic:
        run_real(args.arm, args.seed)
    if args.output is None:
        p.error("synthetic mode requires an external temporary output directory")
    result = run_synthetic(args.arm, args.seed, args.output, resume=args.resume)
    print({"synthetic_only": True, "complete": result["complete"], "epochs": result["epochs"]})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
