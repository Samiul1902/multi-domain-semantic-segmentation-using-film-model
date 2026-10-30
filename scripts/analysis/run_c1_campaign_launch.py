"""
Non-executing preflight validator and operator launch runner for the genuine C1 6-run campaign.

Enforces:
- Exact frozen RC3 release digest: 54d1273a53db7dae58118a4bb69c2a96ba2e474a72512a9dccb4c98c9513549f
- Exact 6-run matrix: C1-T & C1-C across seeds (42, 123, 3407)
- Independent operator authorization artifacts (policy.json, approval.json, instruction.json, host_clock_attestation.json)
- Validation without executing training unless explicitly invoked by operator with --execute
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

FROZEN_RC3_RELEASE_DIGEST = "54d1273a53db7dae58118a4bb69c2a96ba2e474a72512a9dccb4c98c9513549f"
FROZEN_PROTOCOL_SHA256 = "531e3eb255a66381201d1aaf49bbe55abfdbe529640f5c584ef100d298087a61"
EXPECTED_RUN_PLAN = [
    {"arm": "C1-T", "seed": 42},
    {"arm": "C1-C", "seed": 42},
    {"arm": "C1-T", "seed": 123},
    {"arm": "C1-C", "seed": 123},
    {"arm": "C1-T", "seed": 3407},
    {"arm": "C1-C", "seed": 3407},
]


def validate_operator_artifacts(
    *,
    trust_store_root: Path,
    approval_path: Path,
    instruction_path: Path,
    time_status_path: Path,
    budget_path: Path,
    recovery_path: Path,
) -> dict:
    """Read and structurally validate required operator artifacts before launch."""
    print("=== C1 Production Launch Preflight Validation ===")

    # 1. Trust store check
    if not trust_store_root.exists() or not trust_store_root.is_dir():
        raise FileNotFoundError(f"Missing institutional trust store root at: {trust_store_root}")

    policy_file = trust_store_root / "policy.json"
    if not policy_file.exists():
        raise FileNotFoundError(f"Missing institutional policy file: {policy_file}")

    clock_file = trust_store_root / "host_clock_attestation.json"
    if not clock_file.exists():
        raise FileNotFoundError(f"Missing host clock attestation: {clock_file}")

    # 2. Authorization payload checks
    for p, name in [
        (approval_path, "approval"),
        (instruction_path, "instruction"),
        (time_status_path, "time_status"),
        (budget_path, "budget"),
        (recovery_path, "recovery"),
    ]:
        if not p.exists():
            raise FileNotFoundError(f"Missing required operator artifact: {name} ({p})")

    approval = json.loads(approval_path.read_text(encoding="utf-8"))
    instruction = json.loads(instruction_path.read_text(encoding="utf-8"))
    time_status = json.loads(time_status_path.read_text(encoding="utf-8"))
    budget = json.loads(budget_path.read_text(encoding="utf-8"))
    recovery = json.loads(recovery_path.read_text(encoding="utf-8"))

    print("[PASS] All required authorization JSON files exist and are readable.")
    return {
        "approval": approval,
        "instruction": instruction,
        "time_status": time_status,
        "budget": budget,
        "recovery": recovery,
    }


def execute_campaign(
    *,
    trust_store_root: Path,
    approval_path: Path,
    instruction_path: Path,
    time_status_path: Path,
    budget_path: Path,
    recovery_path: Path,
    output_root: Path,
    execute: bool = False,
):
    artifacts = validate_operator_artifacts(
        trust_store_root=trust_store_root,
        approval_path=approval_path,
        instruction_path=instruction_path,
        time_status_path=time_status_path,
        budget_path=budget_path,
        recovery_path=recovery_path,
    )

    if not execute:
        print("\n[VALIDATION SUCCESSFUL] Preflight passed. Training execution was NOT requested (--execute omitted).")
        print("To launch real-data training, the operator must provide valid signed institutional materials and specify --execute.")
        return

    print("\n[LAUNCHING AUTHENTICATED PRODUCTION CAMPAIGN]")
    from src.research.c1_film_launch_rc3 import launch_driver_rc3

    for item in EXPECTED_RUN_PLAN:
        arm = item["arm"]
        seed = item["seed"]
        print(f"\n>>> Starting Run: Arm={arm}, Seed={seed} ...")
        res = launch_driver_rc3.launch(
            arm=arm,
            seed=seed,
            expected_release_digest=FROZEN_RC3_RELEASE_DIGEST,
            approval=artifacts["approval"],
            instruction=artifacts["instruction"],
            time_status=artifacts["time_status"],
            budget=artifacts["budget"],
            run_plan=EXPECTED_RUN_PLAN,
            recovery=artifacts["recovery"],
            output_root=output_root,
            trust_store_root=trust_store_root,
            resume=True,  # Idempotent resumption
        )
        print(f">>> Completed Run {arm}-seed{seed}: {res}")


def main():
    parser = argparse.ArgumentParser(description="RA-MedFiLM-BARR C1 Campaign Launch Runner")
    parser.add_argument("--trust-store", type=Path, default=Path("C:/ProgramData/InstitutionalC1Trust"))
    parser.add_argument("--approval", type=Path, default=Path("configs/c1_operator/approval.json"))
    parser.add_argument("--instruction", type=Path, default=Path("configs/c1_operator/instruction.json"))
    parser.add_argument("--time-status", type=Path, default=Path("configs/c1_operator/time_status.json"))
    parser.add_argument("--budget", type=Path, default=Path("configs/c1_operator/budget.json"))
    parser.add_argument("--recovery", type=Path, default=Path("configs/c1_operator/recovery.json"))
    parser.add_argument("--output-root", type=Path, default=Path("experiments/c1_film_attribution_v1"))
    parser.add_argument("--execute", action="store_true", help="Explicitly authorize actual training execution")

    args = parser.parse_args()

    try:
        execute_campaign(
            trust_store_root=args.trust_store,
            approval_path=args.approval,
            instruction_path=args.instruction,
            time_status_path=args.time_status,
            budget_path=args.budget,
            recovery_path=args.recovery,
            output_root=args.output_root,
            execute=args.execute,
        )
    except Exception as e:
        print(f"\n[LAUNCH REFUSED / BLOCKED] {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
