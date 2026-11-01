"""Stage 6 eight-model matrix CLI (no training, no dataset access)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.research.stage6 import matrix as M  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("cells")
    sub.add_parser("audit-inference")
    smoke = sub.add_parser("cuda-smoke")
    smoke.add_argument("--device", default="cuda")
    agg = sub.add_parser("aggregate")
    agg.add_argument("--runs-root", type=Path, default=M.RUN_ROOT)
    agg.add_argument("--out", type=Path, default=ROOT / "reports" / "tables" / "stage6_eight_model" / "results.json")
    chk = sub.add_parser("baseline-loader-check", help="Read eligible TRAIN rows, one forward/backward pass, nothing saved")
    chk.add_argument("--model", choices=M.BASELINES, required=True)
    chk.add_argument("--device", default="cuda")
    run = sub.add_parser("baseline-run", help="Real TRAIN5832/VAL808 baseline training; fails closed without a launch grant")
    run.add_argument("--model", choices=M.BASELINES, required=True)
    run.add_argument("--seed", type=int, choices=M.SEEDS, required=True)
    run.add_argument("--resume", action="store_true")
    run.add_argument("--grant-provider", default=None, metavar="MODULE:CALLABLE",
                     help="callable returning a released-gate grant exposing authorize_baseline(contract); omitted = fail closed")
    gl = sub.add_parser("export-global-c1", help="Export a completed, compatible C1-T run into a GLOBAL_MEDFILM cell")
    gl.add_argument("--run-dir", type=Path, required=True)
    gl.add_argument("--seed", type=int, choices=M.SEEDS, required=True)
    gl.add_argument("--device", default="cuda")
    args = parser.parse_args(argv)
    if args.command == "cells":
        print(json.dumps({"models": {k: M.MODEL_REGISTRY[k] for k in M.MODEL_KEYS}, "cells": M.build_cells()}, indent=2))
    elif args.command == "audit-inference":
        from src.research.stage6.end_to_end import audit_ground_truth_free
        print(json.dumps(audit_ground_truth_free(), indent=2))
    elif args.command == "cuda-smoke":
        import torch
        from src.research.stage6.end_to_end import GTFreeBARRInference
        system = GTFreeBARRInference.from_canonical_seed(42, device=args.device)
        states = [system.infer(torch.rand(1, 3, 512, 512), t)["state"] for t in range(4)]
        print(json.dumps({"status": "SYNTHETIC_TEST_ONLY", "unique_parameters": system.unique_parameters(),
                          "states": states, "outputs_are_research_evidence": False}, indent=2))
    elif args.command == "baseline-loader-check":
        from src.research.stage6 import baseline_real as B
        print(json.dumps(B.loader_forward_backward_check(args.model, device=args.device), indent=2))
    elif args.command == "baseline-run":
        from src.research.stage6 import baseline_real as B
        try:
            grant = B.load_grant(args.grant_provider)
            doc = B.run_real_baseline(args.model, args.seed, grant=grant, resume=args.resume)
        except Exception as exc:  # noqa: BLE001 - every refusal or failure is reported, never swallowed silently
            print(f"[BASELINE RUN REFUSED / FAILED] {type(exc).__name__}: {exc}", file=sys.stderr)
            return 2
        print(json.dumps({"cell": args.model, "seed": args.seed, "macro": doc["summary"]["equal_domain_macro_dice"]}))
    elif args.command == "export-global-c1":
        from src.research.stage6 import baseline_real as B
        doc = B.export_global_cell_from_c1(args.run_dir, args.seed, M.cell_dir(M.RUN_ROOT, M.GLOBAL, args.seed),
                                           B.iter_real_val_samples(), device=args.device)
        print(json.dumps({"cell": M.GLOBAL, "seed": args.seed, "macro": doc["summary"]["equal_domain_macro_dice"]}))
    else:
        result = M.aggregate_stage6(args.runs_root, args.out)
        print(f"{result['status']}: {args.out}; missing={result['missing_cells']} rejected={result['rejected_cells']}")
        return 0 if result["status"].startswith("COMPLETE") else 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
