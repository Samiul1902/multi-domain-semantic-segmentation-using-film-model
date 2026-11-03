"""Executable entry point for the FULL three-seed pipeline.

Subcommands
-----------
``prepare``   materialise a seed-specific run directory and its family manifest
``validate``  check every dependency without training (recipe, population, folds,
              upstream checkpoints, family identity)
``plan``      print the resolved stage plan with per-stage status
``dry-run``   run the whole G -> CACHE -> R -> L -> B -> S DAG on a synthetic
              population (integration test; never a scientific result)
``run``       execute the real pipeline (requires an operator grant)
``resume``    continue an interrupted real run from its last atomic checkpoint
``export``    export a prediction from an already-complete checkpoint family

Real execution stays behind the existing authorization surface: ``run``/``resume``
refuse to train on real data unless ``--grant-provider module:callable`` resolves to
an object exposing ``authorize_full_training(contract)``.  This CLI mints no
credential and creates no policy exception.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from . import recipe as R
from .context import RunContext
from .inference import FamilyBundle, export_prediction, verify_all_branches
from .orchestrator import (AuthorizationRequired, STAGE_ORDER, assert_seed_families_isolated,
                           family_contract, load_grant, plan, run_family, verify_family)
from .population import load_canonical_population
from .provenance import atomic_write_json, utc_now
from .seeds import FAMILY_SEEDS, SeedFamily
from .synth import build_synthetic_population

DEFAULT_ROOT = R.ROOT / "runs" / "full"
DEFAULT_SYNTH_ROOT = R.ROOT / "runs" / "full_synthetic"


# --------------------------------------------------------------------------- #
def _log(msg: str) -> None:
    print(msg, flush=True)


def make_context(seed: int, *, root: Optional[Path] = None, synthetic: bool = False,
                 synth_root: Optional[Path] = None, bounds: Optional[R.OperationalBounds] = None,
                 per_domain_dev: int = 9, per_domain_val: int = 3,
                 per_domain_holdout: int = 3) -> RunContext:
    family = SeedFamily(int(seed))
    if synthetic:
        base = Path(synth_root or DEFAULT_SYNTH_ROOT)
        bundle = build_synthetic_population(base / "data", per_domain_dev=per_domain_dev,
                                            per_domain_val=per_domain_val,
                                            per_domain_holdout=per_domain_holdout)
        ctx = RunContext(family=family, root=Path(root or base / "runs"),
                         bounds=bounds or R.OperationalBounds.synthetic(),
                         population=bundle.spec, allow_derived_folds=True, synthetic=True)
    else:
        ctx = RunContext(family=family, root=Path(root or DEFAULT_ROOT),
                         bounds=bounds or R.OperationalBounds(),
                         population=load_canonical_population(), allow_derived_folds=False,
                         synthetic=False)
    return ctx


def _print_plan(rows) -> None:
    width = max(len(r.name) for r in rows)
    for r in rows:
        deps = ",".join(r.depends_on) or "-"
        print(f"  {r.name:<{width}}  {r.status:<9}  deps={deps:<14}  {r.description}")
        if r.reason:
            print(f"  {'':<{width}}  {'':<9}  {r.reason}")


# --------------------------------------------------------------------------- #
def cmd_prepare(args) -> int:
    ctx = make_context(args.seed, root=args.root)
    ctx.run_root.mkdir(parents=True, exist_ok=True)
    path = ctx.write_family_manifest()
    contract = family_contract(ctx)
    atomic_write_json(contract, ctx.run_root / "contract.json")
    print(f"prepared {ctx.tag} at {ctx.run_root}")
    print(f"  family manifest : {path}")
    print(f"  contract sha256 : {contract['contract_sha256']}")
    print(f"  protocol-faithful: {ctx.bounds.is_protocol_faithful}")
    return 0


def cmd_validate(args) -> int:
    ctx = make_context(args.seed, root=args.root, synthetic=args.synthetic,
                       synth_root=args.synth_root)
    problems = []
    print(f"validating {ctx.tag} (synthetic={ctx.synthetic})")

    # recipe / population
    pop = ctx.population.summary()
    print(f"  population      : {pop['development_n']} development rows "
          f"{pop['development_by_domain']}")
    if not ctx.synthetic and pop["development_n"] != R.ROUTER_DEVELOPMENT_N:
        problems.append("development population size differs from 4957")

    # folds + leakage
    from .population import assert_no_leakage
    for kind in ("outer3", "cv5"):
        try:
            table = ctx.folds(kind)
            audit = assert_no_leakage(spec=ctx.population, folds=table.folds, label=kind)
            print(f"  folds[{kind:<6}]   : {table.n_folds} folds, source={table.source}, "
                  f"{audit['verdict']}")
        except Exception as exc:                       # noqa: BLE001
            problems.append(f"{kind} folds: {type(exc).__name__}: {exc}")
            print(f"  folds[{kind:<6}]   : FAIL {exc}")

    # component checkpoints
    for name, path in (("G", ctx.g_dir / "best.pt"),
                       ("R", ctx.r_dir / "final" / "final.pt"),
                       ("B", ctx.b_dir / "final" / "final.pt"),
                       ("S", ctx.s_dir / "final" / "final.pt")):
        state = "present" if path.exists() else "ABSENT"
        print(f"  component {name:<5}   : {state}  {path}")
    if not ctx.synthetic:
        missing = [n for n, p in (("G", ctx.g_dir / "best.pt"),
                                  ("R", ctx.r_dir / "final" / "final.pt"),
                                  ("B", ctx.b_dir / "final" / "final.pt"),
                                  ("S", ctx.s_dir / "final" / "final.pt")) if not p.exists()]
        if missing:
            print(f"  note            : {missing} not yet trained for this family")

    print("  stage plan      :")
    _print_plan(plan(ctx))

    if problems:
        print("VALIDATION FAILED")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("VALIDATION PASS")
    return 0


def cmd_plan(args) -> int:
    ctx = make_context(args.seed, root=args.root, synthetic=args.synthetic,
                       synth_root=args.synth_root)
    print(f"stage plan for {ctx.tag}")
    _print_plan(plan(ctx))
    return 0


def cmd_dry_run(args) -> int:
    ctx = make_context(args.seed, root=args.root, synthetic=True,
                       synth_root=args.synth_root)
    print(f"synthetic dry run for {ctx.tag} at {ctx.run_root}")
    print(f"  operational bounds: {ctx.bounds.overrides()}")
    result = run_family(ctx, resume=False, log=_log)
    statuses = {k: v["status"] for k, v in result["stages"].items()}
    print(f"  stage status: {statuses}")
    verification = verify_family(ctx)
    print(f"  verification: {verification['verdict']}")
    branches = verify_all_branches()
    print(f"  inference branches: {branches['verdict']}")

    atomic_write_json({"artifact": "full_barr_synthetic_dry_run",
                       "seed": ctx.seed, "tag": ctx.tag,
                       "stage_status": statuses, "verification": verification,
                       "branches": branches, "completed_utc": utc_now()},
                      ctx.run_root / "dry_run_report.json")
    ok = all(s == "COMPLETE" for s in statuses.values())
    print("DRY RUN PASS" if ok else "DRY RUN FAIL")
    return 0 if ok else 1


def cmd_run(args) -> int:
    ctx = make_context(args.seed, root=args.root)
    grant = load_grant(args.grant_provider)
    stages = args.stages.split(",") if args.stages else None
    result = run_family(ctx, stages=stages, resume=args.resume, force=args.force,
                        grant=grant, log=_log)
    print(json.dumps({k: v["status"] for k, v in result["stages"].items()}, indent=1))
    return 0


def cmd_resume(args) -> int:
    ctx = make_context(args.seed, root=args.root)
    grant = load_grant(args.grant_provider)
    result = run_family(ctx, resume=True, grant=grant, log=_log)
    print(json.dumps({k: v["status"] for k, v in result["stages"].items()}, indent=1))
    return 0


def cmd_export(args) -> int:
    ctx = make_context(args.seed, root=args.root)
    bundle = FamilyBundle.load(ctx, device="cpu")
    if args.image:
        from PIL import Image
        import numpy as np
        import torch

        img = Image.open(args.image).convert("RGB").resize(
            (R.REGIONAL_CANVAS_RESOLUTION, R.REGIONAL_CANVAS_RESOLUTION),
            Image.Resampling.BILINEAR)
        arr = (np.asarray(img, dtype=np.float32) / 255.0).transpose(2, 0, 1)
        tensor = torch.from_numpy(arr)[None]
    else:
        import torch

        tensor = torch.rand(1, 3, R.REGIONAL_CANVAS_RESOLUTION, R.REGIONAL_CANVAS_RESOLUTION,
                            generator=torch.Generator().manual_seed(0))
        print("  no --image given: using a seeded synthetic image")

    record = export_prediction(bundle, tensor, args.task_id, device=args.device)
    out = Path(args.out) if args.out else ctx.inference_dir / f"prediction_{args.task_id}.npz"
    out.parent.mkdir(parents=True, exist_ok=True)
    import numpy as np

    np.savez_compressed(out, final_probability=record["final_probability"],
                        final_binary=record["final_binary"])
    meta = {k: v for k, v in record.items()
            if k not in ("final_probability", "final_binary")}
    atomic_write_json(meta, out.with_suffix(".json"))
    print(f"exported {out}")
    print(f"  state={record['state']} probability_sha256={record['probability_sha256'][:16]}")
    return 0


# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="full_barr_three_seed",
        description="FULL RA-MedFiLM-BARR three-seed training pipeline (Phase A)")
    sub = ap.add_subparsers(dest="command", required=True)

    def _common(p, *, synthetic_allowed: bool = False):
        p.add_argument("--seed", type=int, required=True, choices=list(FAMILY_SEEDS))
        p.add_argument("--root", type=Path, default=None,
                       help=f"family root (default {DEFAULT_ROOT})")
        if synthetic_allowed:
            p.add_argument("--synthetic", action="store_true",
                           help="use a generated synthetic population")
            p.add_argument("--synth-root", type=Path, default=None,
                           help=f"synthetic workspace (default {DEFAULT_SYNTH_ROOT})")

    p = sub.add_parser("prepare", help="materialise a seed-specific run directory")
    _common(p)
    p.set_defaults(func=cmd_prepare)

    p = sub.add_parser("validate", help="check every dependency without training")
    _common(p, synthetic_allowed=True)
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("plan", help="print the resolved stage plan")
    _common(p, synthetic_allowed=True)
    p.set_defaults(func=cmd_plan)

    p = sub.add_parser("dry-run", help="synthetic end-to-end integration run")
    _common(p, synthetic_allowed=True)
    p.set_defaults(func=cmd_dry_run, synthetic=True)

    p = sub.add_parser("run", help="execute the real pipeline (requires a grant)")
    _common(p)
    p.add_argument("--resume", action="store_true")
    p.add_argument("--force", action="store_true",
                   help="re-run stages even when they are already complete")
    p.add_argument("--stages", default=None,
                   help=f"comma-separated subset of {','.join(STAGE_ORDER)}")
    p.add_argument("--grant-provider", default=None, metavar="MODULE:CALLABLE")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("resume", help="resume an interrupted real run")
    _common(p)
    p.add_argument("--grant-provider", default=None, metavar="MODULE:CALLABLE")
    p.set_defaults(func=cmd_resume)

    p = sub.add_parser("export", help="export a prediction from a complete family")
    _common(p)
    p.add_argument("--image", default=None, help="image path; omit for a seeded synthetic")
    p.add_argument("--task-id", type=int, required=True, choices=[0, 1, 2, 3])
    p.add_argument("--device", default="cpu")
    p.add_argument("--out", default=None)
    p.set_defaults(func=cmd_export)

    return ap


def main(argv: Optional[list] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except AuthorizationRequired as exc:
        print(f"AUTHORIZATION REQUIRED: {exc}", file=sys.stderr)
        return 3
    except FileNotFoundError as exc:
        print(f"MISSING ARTIFACT: {exc}", file=sys.stderr)
        return 4
    except Exception as exc:                            # noqa: BLE001
        print(f"FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
