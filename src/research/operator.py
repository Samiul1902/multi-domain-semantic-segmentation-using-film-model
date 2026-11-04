"""Explicit operator entrypoints; existing training authorization stays authoritative."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("environment", "eligibility", "c1-prepare", "baseline-prepare"):
        sub.add_parser(name)
    verify = sub.add_parser("verify-full")
    verify.add_argument("--root", type=Path, required=True)
    verify.add_argument("--seed", type=int, choices=(42, 123, 3407), required=True)
    launch = sub.add_parser("c1-launch")
    launch.add_argument("--arm", choices=("C1-T", "C1-C"), required=True)
    launch.add_argument("--seed", type=int, choices=(42, 123, 3407), required=True)
    launch.add_argument("--release-digest", required=True)
    for name in ("approval", "instruction", "time-status", "budget", "run-plan", "recovery"):
        launch.add_argument(f"--{name}", type=Path, required=True)
    launch.add_argument("--output-root", type=Path, required=True)
    launch.add_argument("--resume", action="store_true")
    baseline = sub.add_parser("baseline-run")
    baseline.add_argument("--model", required=True)
    baseline.add_argument("--seed", type=int, choices=(42, 123, 3407), required=True)
    baseline.add_argument("--grant-provider", required=True)
    baseline.add_argument("--resume", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "environment":
        import sys
        import torch
        from .deployment.artifacts import environment
        result = environment()
        result.update(executable=sys.executable, cuda_available=torch.cuda.is_available(),
                      torch=str(torch.__version__), cuda_build=torch.version.cuda,
                      gpu=torch.cuda.get_device_name(0) if torch.cuda.is_available() else None)
    elif args.command == "eligibility":
        from .c1_film_launch_rc4 import trust_rc4, release_identity_rc4
        result = {"release": release_identity_rc4.verify_release_rc4(),
                  "institutional_root_exists": trust_rc4.PRODUCTION_ROOT.exists(),
                  "authorization": "NOT_ESTABLISHED_BY_INSPECTION"}
    elif args.command == "c1-prepare":
        from .c1_film.integration_contract import make_contract
        result = [make_contract(arm, seed, synthetic=False, device="cuda")
                  for seed in (42, 123, 3407) for arm in ("C1-T", "C1-C")]
    elif args.command == "baseline-prepare":
        from .stage6.baseline_real import make_contract
        from .evaluation.registry import BASELINES
        result = [make_contract(model, seed) for seed in (42, 123, 3407) for model in BASELINES]
    elif args.command == "verify-full":
        from .full_pipeline.cli import make_context
        from .full_pipeline.orchestrator import verify_family
        result = verify_family(make_context(args.seed, root=args.root))
        if result["verdict"] != "PASS":
            print(json.dumps(result, indent=2, default=str))
            return 1
    elif args.command == "baseline-run":
        from .stage6.baseline_real import load_grant, run_real_baseline
        result = run_real_baseline(args.model, args.seed,
                                  grant=load_grant(args.grant_provider), resume=args.resume)
    else:
        from .c1_film_launch_rc4.launch_driver_rc4 import launch
        payload = {name: json.loads(getattr(args, name).read_text(encoding="utf-8-sig"))
                   for name in ("approval", "instruction", "time_status", "budget", "run_plan", "recovery")}
        result = launch(args.arm, args.seed, expected_release_digest=args.release_digest,
                        output_root=args.output_root, resume=args.resume, **payload)
    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
