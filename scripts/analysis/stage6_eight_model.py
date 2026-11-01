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
    else:
        result = M.aggregate_stage6(args.runs_root, args.out)
        print(f"{result['status']}: {args.out}; missing={result['missing_cells']} rejected={result['rejected_cells']}")
        return 0 if result["status"].startswith("COMPLETE") else 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
