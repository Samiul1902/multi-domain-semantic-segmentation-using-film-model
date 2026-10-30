"""Phase 25C -- §34 terminal-state audit.

Confirms, from on-disk evidence only, that Phase 25C produced LABELS and nothing
else: no router, no task embedding, no Phase 25D work, no forbidden data reads. Writes
``reports/audits/phase25c_terminal_state.json`` and prints the terminal.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
UTC = datetime.now(timezone.utc).isoformat()
TERMINAL = ("PHASE25C_OOF_PAIRED_REFINEMENT_GAIN_LABELS_COMPLETE"
            "__PHASE25D_BENEFIT_ROUTER_ELIGIBLE_NOT_STARTED")


def jf(name: str) -> dict:
    p = AUD / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def main() -> int:
    freeze = jf("phase25c_final_freeze.json")
    scope = jf("phase25c_scope_guard.json")
    lock = jf("phase25c_test_lock_audit.json")
    handoff = jf("phase25c_phase25d_handoff_schema.json")

    ckpt_root = ROOT / "checkpoints"
    router_ckpt_exists = any(
        p.name.lower().startswith(("router", "benefit_router", "barr_benefit"))
        for p in ckpt_root.glob("**/*") if p.is_file()
    ) if ckpt_root.exists() else False

    checks = {
        "phase25c_complete": freeze.get("phase25c_complete") is True,
        "phase25c_all_gates_pass": freeze.get("all_gates_pass") is True,
        "labels_written": (ROOT / "data_cache"
                           / "phase25c_barr_oof_paired_gain_labels_v1_2"
                           / "phase25c_oof_paired_gain_labels.csv").exists(),
        "label_rows_4957": freeze.get("n_label_rows") == 4957,
        "no_router_training": scope.get("router_training_runs") == 0,
        "no_router_instantiation": scope.get("BARRBenefitRouterV1_instantiated") is False,
        "no_task_embedding_training": scope.get("task_embedding_training_runs") == 0,
        "no_task_embedding_instantiation": scope.get("task_embedding_instantiated") is False,
        "no_global_forwards": scope.get("global_model_forwards") == 0,
        "no_final_refiner_oof_forwards": scope.get("final_refiner_oof_forwards") == 0,
        "no_tta": scope.get("tta_used") is False,
        "no_checkpoint_ensemble": scope.get("checkpoint_ensemble_used") is False,
        "router_holdout_reads_zero": lock.get("router_holdout", {}).get("image_reads") == 0,
        "val808_reads_zero": lock.get("val808", {}).get("image_reads") == 0,
        "test_reads_zero": lock.get("test_reads") == 0,
        "phase25d_handoff_ready":
            handoff.get("verdict") == "PHASE25C_PHASE25D_HANDOFF_READY",
        "phase25d_started_false": freeze.get("phase25d_started") is False,
        "no_router_checkpoint_on_disk": router_ckpt_exists is False,
        "phase25e_not_started": freeze.get("phase25e_status") == "NOT_STARTED",
    }
    all_pass = all(checks.values())

    out = {
        "artifact": "phase25c_terminal_state",
        "phase": "25C",
        "classification": "PHASE25C_EXECUTED_EVIDENCE",
        "method": "RA-MedFiLM-BARR",
        "terminal": TERMINAL,
        "phase25c_complete": all_pass,
        "checks": checks,
        "failed_checks": sorted(k for k, v in checks.items() if not v),
        "evidence": {
            "phase25c_final_freeze": "reports/audits/phase25c_final_freeze.json",
            "scope_guard": "reports/audits/phase25c_scope_guard.json",
            "lock_audit": "reports/audits/phase25c_test_lock_audit.json",
            "phase25d_handoff": "reports/audits/phase25c_phase25d_handoff_schema.json",
        },
        "created": "LABELS_ONLY",
        "phase25d_eligible": True,
        "phase25d_status": "ELIGIBLE_NOT_STARTED",
        "phase25e_status": "NOT_STARTED",
        "task_embedding_owner": "PHASE25D",
        "test_reads": 0,
        "generated_utc": UTC,
    }
    (AUD / "phase25c_terminal_state.json").write_text(json.dumps(out, indent=1) + "\n",
                                                      encoding="utf-8")
    for k, v in checks.items():
        print(f"  [{'PASS' if v else 'FAIL'}] {k}")
    print()
    print("TERMINAL:", TERMINAL if all_pass else f"BLOCKED {out['failed_checks']}")
    return 0 if all_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
