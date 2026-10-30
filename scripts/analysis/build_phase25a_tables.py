"""Phase 25A — assemble the required report tables from the training run artefacts.

Writes to reports/tables/ :
    phase25a_training_epochs_fold0.csv   (every epoch)
    phase25a_training_epochs_fold1.csv
    phase25a_training_epochs_fold2.csv
    phase25a_training_epochs_final.csv
    phase25a_run_summary.csv
    phase25a_table_index.json

Usage:
    ./.venv/Scripts/python.exe scripts/analysis/build_phase25a_tables.py
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(r"D:/Softfors/jup")
TAB = ROOT / "reports" / "tables"
EXP = ROOT / "experiments" / "phase25a_barr_regional_refiner_v1_1"
UTC = datetime.now(timezone.utc).isoformat()

RUNS = {"fold0": "fold0", "fold1": "fold1", "fold2": "fold2", "final": "final_refit"}


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def jload(p: Path) -> dict:
    p = Path(p)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def main() -> int:
    TAB.mkdir(parents=True, exist_ok=True)
    summary_rows = []
    for run, d in RUNS.items():
        src = EXP / d / "history.csv"
        if not src.exists():
            print(f"FAIL-CLOSED: missing {src}")
            return 2
        hist = pd.read_csv(src)
        out = TAB / f"phase25a_training_epochs_{run}.csv"
        hist.to_csv(out, index=False)
        rj = jload(EXP / d / "run.json")
        es_best = rj.get("best_early_stop_loss")
        best_dice = None
        if "early_stop_Dice" in hist.columns and rj.get("best_epoch") is not None:
            m = hist[hist["epoch"] == rj["best_epoch"]]
            if len(m):
                best_dice = float(m["early_stop_Dice"].iloc[0])
        summary_rows.append({
            "run": run,
            "outer_fold": rj.get("outer_fold"),
            "n_fit_action_available": rj.get("n_fit_action_available"),
            "n_early_stop_action_available": rj.get("n_early_stop_action_available"),
            "epochs_completed": rj.get("epochs_completed"),
            "epochs_target": rj.get("epochs_target"),
            "best_epoch": rj.get("best_epoch"),
            "best_early_stop_loss": es_best,
            "early_stop_dice_at_best": best_dice,
            "final_train_loss": rj.get("final_train_loss"),
            "stop_reason": rj.get("stop_reason"),
            "resume_count": rj.get("resume_count"),
            "checkpoint_events": rj.get("checkpoint_events"),
            "parameter_count": rj.get("parameter_count"),
            "history_sha256": rj.get("history_sha256"),
        })
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(TAB / "phase25a_run_summary.csv", index=False)

    required = [
        "phase25a_population_accounting.csv",
        "phase25a_action_availability_by_domain.csv",
        "phase25a_crossfit_fold_manifest_summary.csv",
        "phase25a_resource_accounting.csv",
        "phase25a_refiner_selected_epochs.csv",
        "phase25a_training_epochs_fold0.csv",
        "phase25a_training_epochs_fold1.csv",
        "phase25a_training_epochs_fold2.csv",
        "phase25a_training_epochs_final.csv",
        "phase25a_run_summary.csv",
    ]
    entries, missing = [], []
    for n in required:
        p = TAB / n
        if p.exists():
            entries.append({"table": n, "bytes": p.stat().st_size, "sha256": sha(p)})
        else:
            missing.append(n)
    index = {
        "artifact": "phase25a_table_index",
        "phase": "25A",
        "required": required,
        "n_required": len(required),
        "n_present": len(entries),
        "missing": missing,
        "tables": entries,
        "generated_utc": UTC,
        "test_reads": 0,
    }
    (TAB / "phase25a_table_index.json").write_text(json.dumps(index, indent=1) + "\n",
                                                   encoding="utf-8")
    for e in entries:
        print(f"  {e['table']:48s} {e['bytes']:>9,} B")
    print(f"\n{len(entries)}/{len(required)} required tables present")
    if missing:
        print("MISSING:", missing)
        return 2
    print("PHASE25A_TABLES_COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
