"""Phase 25A — FINAL REFIT EPOCH RULE (persisted BEFORE the final refit).

Reads the three fold run records and computes

    FINAL_REFIT_EPOCHS = integer median of the three best epochs

This artifact MUST exist before ``train_phase25a_refiner.py --final`` runs, so the
final refit epoch count can never be chosen from observed performance.

Writes:
    reports/audits/phase25a_final_refit_epoch_rule.json
    reports/tables/phase25a_refiner_selected_epochs.csv

Usage:
    ./.venv/Scripts/python.exe scripts/analysis/build_phase25a_final_refit_rule.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
EXP_ROOT = ROOT / "experiments" / "phase25a_barr_regional_refiner_v1_1"
CKPT_ROOT = ROOT / "checkpoints" / "phase25a_barr_regional_refiner_v1_1"
UTC = datetime.now(timezone.utc).isoformat()


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main() -> int:
    runs = {}
    for k in range(3):
        run_json = EXP_ROOT / f"fold{k}" / "run.json"
        if not run_json.exists():
            print(f"FAIL: missing {run_json}; train all three folds first")
            return 2
        runs[f"fold{k}"] = json.loads(run_json.read_text(encoding="utf-8"))

    best_epochs = {r: int(v["best_epoch"]) for r, v in runs.items()}
    values = sorted(best_epochs.values())
    median_epoch = int(values[len(values) // 2])       # integer median of three

    rows = []
    for r, v in runs.items():
        rows.append({
            "run": r,
            "outer_fold": v.get("outer_fold"),
            "best_epoch": int(v["best_epoch"]),
            "best_early_stop_loss": v.get("best_early_stop_loss"),
            "epochs_completed": v.get("epochs_completed"),
            "stop_reason": v.get("stop_reason"),
            "resume_count": v.get("resume_count"),
            "checkpoint_best_sha256": (v.get("checkpoint_sha256") or {}).get("best.pt"),
            "selection_rule": "minimum EARLY_STOP total loss",
        })
    pd.DataFrame(rows).to_csv(TAB / "phase25a_refiner_selected_epochs.csv", index=False)

    out = {
        "artifact": "phase25a_final_refit_epoch_rule",
        "phase": "25A",
        "purpose": "persist the median-of-folds refit epoch rule BEFORE the final refit so the "
                   "final epoch count cannot be selected from observed performance",
        "rule": "FINAL_REFIT_EPOCHS = integer median of the three fold best epochs",
        "fold_best_epochs": best_epochs,
        "sorted_best_epochs": values,
        "median_index_used": len(values) // 2,
        "final_refit_epochs": median_epoch,
        "median_derivation": f"sorted {values} -> middle element {median_epoch}",
        "no_early_stopping_in_final_refit": True,
        "final_refit_population": "ALL action-available ROUTER_DEVELOPMENT samples",
        "final_refit_uses_holdout": False,
        "final_refit_uses_val": False,
        "final_refit_uses_test": False,
        "persisted_before_final_refit": True,
        "fold_run_sha256": {r: sha(EXP_ROOT / r / "run.json") for r in runs},
        "verdict": "PHASE25A_FINAL_REFIT_EPOCH_RULE_FROZEN",
        "generated_utc": UTC,
        "test_reads": 0,
    }
    (AUD / "phase25a_final_refit_epoch_rule.json").write_text(
        json.dumps(out, indent=1) + "\n", encoding="utf-8")

    print("=" * 78)
    print("PHASE 25A — FINAL REFIT EPOCH RULE")
    print("=" * 78)
    for r, v in best_epochs.items():
        print(f"  {r}: best_epoch = {v}")
    print(f"  sorted          : {values}")
    print(f"  FINAL_REFIT_EPOCHS = {median_epoch}  ({out['median_derivation']})")
    print(f"wrote {AUD / 'phase25a_final_refit_epoch_rule.json'}")
    print(f"wrote {TAB / 'phase25a_refiner_selected_epochs.csv'}")
    print("PHASE25A_FINAL_REFIT_EPOCH_RULE_FROZEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
