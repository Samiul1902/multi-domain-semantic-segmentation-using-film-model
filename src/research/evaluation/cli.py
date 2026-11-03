"""Phase C evaluation CLI.

``validate``        static and known-answer checks; opens no image
``plan``            the 24-cell plan and what each cell needs
``dry-run``         full 24-cell matrix on a synthetic fixture, published to a scratch root
``evaluate``        evaluate cells (synthetic or real) and publish atomically
``resume``          continue an interrupted evaluation without duplicating samples
``verify-results``  re-verify published cells and recompute their hashes
``aggregate``       assemble results.json from published cells
``profile``         measure parameters, MACs, latency and peak memory per cell
``report``          emit the nine report tables

The real path is not a bypass: it requires an explicit checkpoint root, refuses to
read the protected split, and reports a cell as MISSING when its artifacts are
absent rather than substituting random weights.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.evaluation import adapters as A          # noqa: E402
from src.research.evaluation import efficiency as EF      # noqa: E402
from src.research.evaluation import metrics as MET        # noqa: E402
from src.research.evaluation import protocol as P         # noqa: E402
from src.research.evaluation import provenance as PROV    # noqa: E402
from src.research.evaluation import registry as REG       # noqa: E402
from src.research.evaluation import reports as REP        # noqa: E402
from src.research.evaluation import runner as RN          # noqa: E402
from src.research.evaluation import stats as ST           # noqa: E402

DEFAULT_SYNTHETIC_ROOT = ROOT / "runs" / "phase_c_synthetic_matrix"
DEFAULT_TABLES = ROOT / "reports" / "tables" / "phase_c"


def _print(payload: Any) -> None:
    print(json.dumps(payload, indent=2, default=str))


def _models(values: Optional[Sequence[str]]) -> List[str]:
    if not values:
        return list(REG.DISPLAY_ORDER)
    unknown = [v for v in values if v not in REG.MODEL_KEYS]
    if unknown:
        raise SystemExit(f"unknown model key(s): {unknown}; known: {list(REG.MODEL_KEYS)}")
    return list(values)


# --------------------------------------------------------------------------- #
# validate
# --------------------------------------------------------------------------- #
def cmd_validate(args: argparse.Namespace) -> int:
    checks: Dict[str, Any] = {}
    checks["populations"] = P.population_audit()
    checks["known_answer_metrics"] = MET.verify_known_answers()
    checks["gt_free_adapters"] = A.audit_gt_free()

    from src.research.stage6.end_to_end import audit_ground_truth_free
    checks["gt_free_state_machine"] = audit_ground_truth_free()

    REG.assert_complete_matrix()
    checks["registry"] = {"n_models": len(REG.MODEL_KEYS), "n_cells": len(REG.model_seed_cells()),
                          "display_order": list(REG.DISPLAY_ORDER),
                          "adapter_kinds": dict(REG.ADAPTER_KINDS)}

    guard = P.ProtectedSplitGuard()
    refusals = {}
    for split in (P.SPLIT_TEST,):
        try:
            guard.open(split)
        except P.ProtectedSplitError:
            refusals[split] = "refused"
    checks["protected_split_guard"] = {**guard.report(), "refusals": refusals}

    checks["statistics_policy"] = {
        "inference_class": ST.EXPLORATORY,
        "confirmatory_authorized": ST.CONFIRMATORY_AUTHORIZED,
        "block_reason": ST.CONFIRMATORY_BLOCK_REASON,
        "non_inferiority_margin": ST.NON_INFERIORITY_MARGIN}

    ok = (checks["populations"]["consistent"]
          and checks["known_answer_metrics"]["all_match"]
          and checks["gt_free_adapters"]["gt_free"]
          and checks["gt_free_state_machine"]["gt_free"]
          and checks["protected_split_guard"]["protected_untouched"]
          and checks["registry"]["n_cells"] == 24)
    _print({"status": "VALIDATE_OK" if ok else "VALIDATE_FAILED", "checks": checks})
    return 0 if ok else 1


# --------------------------------------------------------------------------- #
# plan
# --------------------------------------------------------------------------- #
def cmd_plan(args: argparse.Namespace) -> int:
    cells = []
    for model_key, seed in REG.model_seed_cells():
        spec = REG.spec(model_key)
        cells.append({"cell": REG.cell_id(model_key, seed), "model_key": model_key,
                      "display_name": spec.display_name, "role": spec.role,
                      "seed": seed, "adapter_kind": spec.adapter_kind,
                      "takes_task_id": spec.takes_task_id,
                      "chain": list(spec.chain),
                      "architecture": REG.architecture_identity(model_key)})
    _print({"schema": "phase_c_plan_v1", "n_cells": len(cells),
            "splits": {s: P.SPLIT_SEMANTICS[s] for s in P.SPLIT_SEMANTICS},
            "evaluable_splits": [P.SPLIT_VAL],
            "protected_splits": sorted(P.PROTECTED_SPLITS),
            "cells": cells})
    return 0


# --------------------------------------------------------------------------- #
# dry-run
# --------------------------------------------------------------------------- #
def cmd_dry_run(args: argparse.Namespace) -> int:
    root = Path(args.root) if args.root else DEFAULT_SYNTHETIC_ROOT
    guard = P.ProtectedSplitGuard()
    samples = RN.synthetic_samples(root / "fixture", per_domain_val=args.per_domain_val,
                                  guard=guard)
    import hashlib
    manifest_sha = hashlib.sha256((root / "fixture" / "val.csv").read_bytes()).hexdigest()
    outcome = RN.run_matrix(root / "cells", samples, source="synthetic",
                            device=args.device, seeds=tuple(args.seeds),
                            models=_models(args.models),
                            split_manifest_sha256=manifest_sha,
                            progress=(lambda m, s, st: print(f"  {m} seed{s}: {st}",
                                                             file=sys.stderr)))
    outcome["protected_split_guard"] = guard.report()
    outcome["split_manifest_sha256"] = manifest_sha
    _print(outcome)
    return 0 if outcome["n_failed"] == 0 else 1


# --------------------------------------------------------------------------- #
# evaluate / resume
# --------------------------------------------------------------------------- #
def _load_samples(args: argparse.Namespace, guard: P.ProtectedSplitGuard):
    if args.source == "synthetic":
        root = Path(args.root)
        return RN.synthetic_samples(root / "fixture", per_domain_val=args.per_domain_val,
                                    guard=guard), root
    split = args.split
    if split in P.PROTECTED_SPLITS:
        raise SystemExit(f"{split} is protected and may not be evaluated")
    manifest = P.MANIFEST_FILES[split]
    samples = RN.load_manifest_samples(manifest, split, domains=args.domains,
                                       limit_per_domain=args.limit_per_domain,
                                       guard=guard)
    return samples, Path(args.root)


def cmd_evaluate(args: argparse.Namespace) -> int:
    guard = P.ProtectedSplitGuard()
    samples, root = _load_samples(args, guard)
    import hashlib
    if args.source == "synthetic":
        manifest_sha = hashlib.sha256((root / "fixture" / "val.csv").read_bytes()).hexdigest()
    else:
        manifest_sha = P.manifest_sha256(args.split)

    cells = []
    for model_key in _models(args.models):
        for seed in args.seeds:
            try:
                outcome = RN.run_cell(model_key, seed, samples, root=root / "cells",
                                      source=args.source, device=args.device,
                                      resume=args.resume, export_maps=args.export_maps,
                                      split=args.split,
                                      split_manifest_sha256=manifest_sha)
                cells.append({"model_key": model_key, "seed": seed, "status": "EXECUTED",
                              "evidence_class": outcome["evidence_class"],
                              "equal_domain_macro_dice":
                                  outcome["summary"]["equal_domain_macro_dice"],
                              "directory": outcome["directory"]})
            except Exception as exc:
                cells.append({"model_key": model_key, "seed": seed, "status": "FAILED",
                              "reason": f"{type(exc).__name__}: {exc}"})
    executed = sum(1 for c in cells if c["status"] == "EXECUTED")
    _print({"schema": "phase_c_evaluate_v1", "source": args.source, "device": args.device,
            "n_requested": len(cells), "n_executed": executed,
            "n_failed": len(cells) - executed,
            "protected_split_guard": guard.report(),
            "research_cells_completed": 0,
            "note": "Execution is not establishment; synthetic cells never complete a cell.",
            "cells": cells})
    return 0 if executed == len(cells) else 1


def cmd_resume(args: argparse.Namespace) -> int:
    args.resume = True
    return cmd_evaluate(args)


# --------------------------------------------------------------------------- #
# verify-results / aggregate / profile / report
# --------------------------------------------------------------------------- #
def cmd_verify_results(args: argparse.Namespace) -> int:
    outcome = PROV.verify_matrix(Path(args.root))
    _print(outcome)
    bad = outcome["counts"].get("REJECTED", 0)
    return 0 if bad == 0 else 1


def cmd_aggregate(args: argparse.Namespace) -> int:
    results = REP.collect_results(Path(args.root), bootstrap_unit=args.bootstrap_unit)
    out = Path(args.out) if args.out else (Path(args.root) / "results.json")
    PROV.atomic_write_json(out, results)
    _print({"status": "AGGREGATED", "out": str(out),
            "research_cells_completed": results["research_cells_completed"],
            "synthetic_cells_executed": results["synthetic_cells_executed"],
            "registry_status": results["registry_status"],
            "banner": results["banner"]})
    return 0


def cmd_profile(args: argparse.Namespace) -> int:
    import torch

    guard = P.ProtectedSplitGuard()
    samples, root = _load_samples(args, guard)
    image = samples[0].image
    task_id = samples[0].task_id
    # Conditional cost is only meaningful with the *measured* refiner invocation
    # rate, so the published per-image records are read back and passed through.
    published = RN.records_by_cell(root / "cells")
    rows = []
    for model_key in _models(args.models):
        for seed in args.seeds:
            try:
                adapter = A.build_adapter(model_key, seed, device=args.device,
                                          source=args.source)
                adapter.load()
                try:
                    profile = EF.profile_cell(adapter, image, task_id,
                                              records=published.get((model_key, seed)),
                                              warmup=args.warmup, repeats=args.repeats)
                    profile["total_flops"] = EF.total_flops(adapter)
                    profile["evidence_class"] = adapter.evidence_class
                finally:
                    adapter.close()
                directory = root / "cells" / model_key / f"seed{seed}"
                PROV.atomic_write_json(directory / "efficiency.json", profile)
                rows.append({"model_key": model_key, "seed": seed, "status": "PROFILED",
                             "parameters": profile["unique_inference_parameters"],
                             "latency_ms_p50": profile["latency_ms_p50"],
                             "peak_allocated_mib": profile["peak_allocated_mib"],
                             "macs_global_only": profile["macs_global_only"],
                             "macs_if_always_refine": profile["macs_if_always_refine"],
                             "effective_macs_per_image": profile["effective_macs_per_image"],
                             "refiner_invocation_rate":
                                 profile["conditional_refiner_invocation_rate"]})
            except Exception as exc:
                rows.append({"model_key": model_key, "seed": seed, "status": "FAILED",
                             "reason": f"{type(exc).__name__}: {exc}"})
    _print({"schema": "phase_c_profile_v1", "device": args.device,
            "device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu",
            "conditions": EF.profiling_conditions(warmup=args.warmup, repeats=args.repeats),
            "rows": rows})
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    results = REP.write_tables(Path(args.root), Path(args.out),
                               bootstrap_unit=args.bootstrap_unit)
    _print({"status": "REPORTED", "out": str(args.out),
            "banner": results["banner"],
            "registry_status": results["registry_status"],
            "tables": results["manifest"]["tables"],
            "statistics_policy": results["manifest"]["statistics_policy"]})
    return 0


# --------------------------------------------------------------------------- #
# parser
# --------------------------------------------------------------------------- #
def _common(parser: argparse.ArgumentParser, *, default_source: str) -> None:
    parser.add_argument("--root", type=Path, default=DEFAULT_SYNTHETIC_ROOT)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--source", choices=("synthetic", "real"), default=default_source)
    parser.add_argument("--models", nargs="*", default=None)
    parser.add_argument("--seeds", nargs="*", type=int, default=list(REG.SEEDS))
    parser.add_argument("--per-domain-val", type=int, default=3)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("validate", help="static, known-answer and guard checks")

    plan = sub.add_parser("plan", help="print the 24-cell plan")
    plan.add_argument("--json", action="store_true")

    dry = sub.add_parser("dry-run", help="24-cell synthetic matrix into a scratch root")
    _common(dry, default_source="synthetic")
    dry.set_defaults(func=cmd_dry_run)

    ev = sub.add_parser("evaluate", help="evaluate cells and publish atomically")
    _common(ev, default_source="real")
    ev.add_argument("--split", default=P.SPLIT_VAL)
    ev.add_argument("--domains", nargs="*", default=None)
    ev.add_argument("--limit-per-domain", type=int, default=None)
    ev.add_argument("--export-maps", action="store_true")
    ev.add_argument("--resume", action="store_true")
    ev.set_defaults(func=cmd_evaluate)

    rs = sub.add_parser("resume", help="continue an interrupted evaluation")
    _common(rs, default_source="real")
    rs.add_argument("--split", default=P.SPLIT_VAL)
    rs.add_argument("--domains", nargs="*", default=None)
    rs.add_argument("--limit-per-domain", type=int, default=None)
    rs.add_argument("--export-maps", action="store_true")
    rs.set_defaults(func=cmd_resume)

    vr = sub.add_parser("verify-results", help="re-verify published cells")
    vr.add_argument("--root", type=Path, default=DEFAULT_SYNTHETIC_ROOT)
    vr.set_defaults(func=cmd_verify_results)

    ag = sub.add_parser("aggregate", help="assemble results.json")
    ag.add_argument("--root", type=Path, default=DEFAULT_SYNTHETIC_ROOT)
    ag.add_argument("--out", type=Path, default=None)
    ag.add_argument("--bootstrap-unit", choices=("image", "patient", "group"),
                    default="image")
    ag.set_defaults(func=cmd_aggregate)

    pr = sub.add_parser("profile", help="measure parameters, MACs, latency and memory")
    _common(pr, default_source="real")
    pr.add_argument("--warmup", type=int, default=3)
    pr.add_argument("--repeats", type=int, default=20)
    pr.set_defaults(func=cmd_profile)

    rp = sub.add_parser("report", help="emit the nine report tables")
    rp.add_argument("--root", type=Path, default=DEFAULT_SYNTHETIC_ROOT)
    rp.add_argument("--out", type=Path, default=DEFAULT_TABLES)
    rp.add_argument("--bootstrap-unit", choices=("image", "patient", "group"),
                    default="image")
    rp.set_defaults(func=cmd_report)

    for name in ("validate", "plan"):
        sub.choices[name].set_defaults(func=(cmd_validate if name == "validate"
                                             else cmd_plan))
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
