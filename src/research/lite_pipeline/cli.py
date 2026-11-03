"""Executable entry point for the RA-MedFiLM-BARR-Lite pipeline.

Subcommands
-----------
``prepare``        materialise a seed-specific Lite run directory and its manifest
``validate``       check every dependency without training (identity, population,
                   folds, upstream checkpoints, family compatibility)
``plan``           print the resolved stage plan with per-stage status
``dry-run``        run the whole G -> CACHE -> R -> L -> B -> S DAG on a synthetic
                   population (integration test; never a scientific result)
``run``            execute the real pipeline (requires an operator grant)
``resume``         continue an interrupted real run from its last atomic checkpoint
``export``         export a prediction from an already-complete Lite checkpoint family
``verify-family``  re-verify the full SHA chain of a completed Lite family

Authorization
-------------
``run`` and ``resume`` stay behind the operator grant surface that already exists
for the FULL pipeline: ``--grant-provider module:callable`` must resolve to an
object exposing ``authorize_full_training(contract)``.  This CLI mints no
credential, creates no new gate and bypasses no existing one.  A synthetic
``dry-run`` is not training and needs no grant, but it is stamped
``synthetic: true`` and can never be cited as a result.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from src.research.full_pipeline import recipe as R
from src.research.full_pipeline.population import load_canonical_population
from src.research.full_pipeline.provenance import atomic_write_json, utc_now
from src.research.full_pipeline.synth import build_synthetic_population

from . import recipe as L
from . import strict_oof
from .context import LiteRunContext, make_lite_context
from .inference import LiteBundle, audit_lite_gt_free, export_prediction, verify_all_branches
from .orchestrator import (AuthorizationRequired, STAGE_ORDER, assert_lite_families_isolated,
                           family_contract, lite_family_verification, load_grant, plan,
                           run_family)

DEFAULT_ROOT = R.ROOT / "runs" / "lite"
DEFAULT_SYNTH_ROOT = R.ROOT / "runs" / "lite_synthetic"


# --------------------------------------------------------------------------- #
def _log(msg: str) -> None:
    print(msg, flush=True)


def make_context(seed: int, *, root: Optional[Path] = None, synthetic: bool = False,
                 synth_root: Optional[Path] = None,
                 bounds: Optional[R.OperationalBounds] = None,
                 variant: str = L.DEFAULT_VARIANT,
                 per_domain_dev: int = 9, per_domain_val: int = 3,
                 per_domain_holdout: int = 3) -> LiteRunContext:
    if synthetic:
        base = Path(synth_root or DEFAULT_SYNTH_ROOT)
        bundle = build_synthetic_population(base / "data", per_domain_dev=per_domain_dev,
                                            per_domain_val=per_domain_val,
                                            per_domain_holdout=per_domain_holdout)
        return make_lite_context(
            seed, root=Path(root or base / "runs"),
            bounds=bounds or R.OperationalBounds.synthetic(),
            population=bundle.spec, synthetic=True, variant=variant)
    return make_lite_context(
        seed, root=Path(root or DEFAULT_ROOT),
        bounds=bounds or R.OperationalBounds(),
        population=load_canonical_population(), synthetic=False, variant=variant)


def _print_plan(rows) -> None:
    width = max(len(r.name) for r in rows)
    for r in rows:
        deps = ",".join(r.depends_on) or "-"
        print(f"  {r.name:<{width}}  {r.status:<9}  deps={deps:<14}  {r.description}")
        if r.reason:
            print(f"  {'':<{width}}  {'':<9}  {r.reason}")


def _print_identity(ctx: LiteRunContext) -> None:
    ident = ctx.parameter_identity()
    print(f"  variant         : {ctx.variant} ({ctx.variant_id})")
    print(f"  architecture    : {ctx.architecture_sha256}")
    print(f"  parameters      : {ident['components']} total={ident['total_unique_parameters']}")
    print(f"  vs FULL family  : {ident['full_family_total_parameters']} "
          f"-> {ident['reduction_percent_vs_full_family']:.4f}% reduction")


# --------------------------------------------------------------------------- #
def cmd_prepare(args) -> int:
    ctx = make_context(args.seed, root=args.root, variant=args.variant)
    ctx.run_root.mkdir(parents=True, exist_ok=True)
    path = ctx.write_family_manifest()
    contract = family_contract(ctx)
    atomic_write_json(contract, ctx.run_root / "contract.json")
    print(f"prepared {ctx.tag} at {ctx.run_root}")
    _print_identity(ctx)
    print(f"  family manifest : {path}")
    print(f"  contract sha256 : {contract['contract_sha256']}")
    print(f"  protocol-faithful: {ctx.bounds.is_protocol_faithful}")
    return 0


def cmd_validate(args) -> int:
    ctx = make_context(args.seed, root=args.root, synthetic=args.synthetic,
                       synth_root=args.synth_root, variant=args.variant)
    problems = []
    print(f"validating {ctx.tag} (synthetic={ctx.synthetic})")
    _print_identity(ctx)

    # population
    pop = ctx.population.summary()
    print(f"  population      : {pop['development_n']} development rows "
          f"{pop['development_by_domain']}")
    if not ctx.synthetic and pop["development_n"] != R.ROUTER_DEVELOPMENT_N:
        problems.append("development population size differs from 4957")

    # folds + leakage
    from src.research.full_pipeline.population import assert_no_leakage

    for kind in ("outer3", "cv5"):
        try:
            table = ctx.folds(kind)
            audit = assert_no_leakage(spec=ctx.population, folds=table.folds, label=kind)
            print(f"  folds[{kind:<6}]   : {table.n_folds} folds, source={table.source}, "
                  f"{audit['verdict']}")
        except Exception as exc:                       # noqa: BLE001
            problems.append(f"{kind} folds: {type(exc).__name__}: {exc}")
            print(f"  folds[{kind:<6}]   : FAIL {exc}")

    # strict-OOF interface (buildable, not executed)
    try:
        strict = strict_oof.build_strict_folds(
            ctx.population, seed=ctx.seed,
            allow_derived=ctx.synthetic or ctx.allow_derived_folds)
        print(f"  strict-OOF      : {len(strict)} folds, target exclusion PASS "
              f"(interface only; no strict-OOF result exists)")
    except Exception as exc:                           # noqa: BLE001
        problems.append(f"strict-OOF folds: {type(exc).__name__}: {exc}")
        print(f"  strict-OOF      : FAIL {exc}")

    # component checkpoints
    for name, path in (("G", ctx.g_dir / "best.pt"),
                       ("R", ctx.r_dir / "final" / "final.pt"),
                       ("B", ctx.b_dir / "final" / "final.pt"),
                       ("S", ctx.s_dir / "final" / "final.pt")):
        print(f"  component {name:<5}   : "
              f"{'present' if path.exists() else 'ABSENT'}  {path}")

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
                       synth_root=args.synth_root, variant=args.variant)
    print(f"stage plan for {ctx.tag} (family=LITE, variant={ctx.variant})")
    _print_plan(plan(ctx))
    return 0


def cmd_dry_run(args) -> int:
    ctx = make_context(args.seed, root=args.root, synthetic=True,
                       synth_root=args.synth_root, variant=args.variant)
    print(f"synthetic dry run for {ctx.tag} at {ctx.run_root}")
    _print_identity(ctx)
    print(f"  operational bounds: {ctx.bounds.overrides()}")
    result = run_family(ctx, resume=False, log=_log)
    statuses = {k: v["status"] for k, v in result["stages"].items()}
    print(f"  stage status: {statuses}")
    verification = lite_family_verification(ctx)
    print(f"  verification: {verification['verdict']}")
    branches = verify_all_branches()
    print(f"  inference branches: {branches['verdict']}")

    atomic_write_json({"artifact": "lite_barr_synthetic_dry_run",
                       "synthetic": True,
                       "not_scientific_evidence": True,
                       "seed": ctx.seed, "tag": ctx.tag, "variant": ctx.variant,
                       "parameter_identity": ctx.parameter_identity(),
                       "stage_status": statuses, "verification": verification,
                       "branches": branches, "completed_utc": utc_now()},
                      ctx.run_root / "dry_run_report.json")
    ok = all(s == "COMPLETE" for s in statuses.values())
    print("DRY RUN PASS" if ok else "DRY RUN FAIL")
    return 0 if ok else 1


def cmd_run(args) -> int:
    ctx = make_context(args.seed, root=args.root, variant=args.variant)
    grant = load_grant(args.grant_provider)
    stages = args.stages.split(",") if args.stages else None
    result = run_family(ctx, stages=stages, resume=args.resume, force=args.force,
                        grant=grant, log=_log)
    print(json.dumps({k: v["status"] for k, v in result["stages"].items()}, indent=1))
    return 0


def cmd_resume(args) -> int:
    ctx = make_context(args.seed, root=args.root, variant=args.variant)
    grant = load_grant(args.grant_provider)
    result = run_family(ctx, resume=True, grant=grant, log=_log)
    print(json.dumps({k: v["status"] for k, v in result["stages"].items()}, indent=1))
    return 0


def cmd_export(args) -> int:
    ctx = make_context(args.seed, root=args.root, variant=args.variant)
    bundle = LiteBundle.load(ctx, device="cpu")
    if args.image:
        import numpy as np
        import torch
        from PIL import Image

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
    print(f"  variant={record['variant_id']} state={record['state']} "
          f"probability_sha256={record['probability_sha256'][:16]}")
    return 0


def cmd_verify_family(args) -> int:
    ctx = make_context(args.seed, root=args.root, synthetic=args.synthetic,
                       synth_root=args.synth_root, variant=args.variant)
    out = lite_family_verification(ctx)
    if args.all_seeds:
        contexts = [make_context(s, root=args.root, synthetic=args.synthetic,
                                 synth_root=args.synth_root, variant=args.variant)
                    for s in L.LITE_SEEDS]
        isolation = assert_lite_families_isolated(contexts)
        out["seed_family_isolation"] = isolation
        print(f"  seed isolation : {isolation['verdict']}")
    out["gt_free_audit"] = audit_lite_gt_free()
    print(json.dumps(out, indent=1, default=str))
    path = ctx.run_root / "verify_family.json"
    atomic_write_json(out, path)
    print(f"verification written to {path}")
    return 0


# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="lite_barr_three_seed",
        description="RA-MedFiLM-BARR-Lite three-seed training pipeline (Phase B)")
    sub = ap.add_subparsers(dest="command", required=True)

    def _common(p, *, synthetic_allowed: bool = False):
        p.add_argument("--seed", type=int, required=True, choices=list(L.LITE_SEEDS))
        p.add_argument("--root", type=Path, default=None,
                       help=f"family root (default {DEFAULT_ROOT})")
        p.add_argument("--variant", default=L.DEFAULT_VARIANT, choices=list(L.VARIANT_IDS),
                       help=f"Lite variant (default {L.DEFAULT_VARIANT})")
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

    p = sub.add_parser("verify-family", help="re-verify a completed Lite family chain")
    _common(p, synthetic_allowed=True)
    p.add_argument("--all-seeds", action="store_true",
                   help="also prove the three seed families share no artifact")
    p.set_defaults(func=cmd_verify_family)

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
