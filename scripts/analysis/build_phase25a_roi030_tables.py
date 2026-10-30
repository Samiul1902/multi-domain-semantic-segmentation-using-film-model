"""Phase 25A (CANONICAL RERUN) — assemble the ROI-0.30 canonical report tables.

Writes to reports/tables/ :
    phase25a_roi030_fold0_training_history.csv    (every epoch)
    phase25a_roi030_fold1_training_history.csv
    phase25a_roi030_fold2_training_history.csv
    phase25a_roi030_final_refit_history.csv
    phase25a_roi030_refiner_selected_epochs.csv
    phase25a_roi030_checkpoint_inventory.csv
    phase25a_roi030_table_index.json

(population / action-availability / crop-geometry tables are written by
``build_phase25a_roi030_cache.py``.)

Historical ROI-0.50 equivalents are NOT overwritten.

Usage:
    ./.venv/Scripts/python.exe scripts/analysis/build_phase25a_roi030_tables.py
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(r"D:/Softfors/jup")
TAB = ROOT / "reports" / "tables"
EXP = ROOT / "experiments" / "phase25a_barr_regional_refiner_v1_1_roi030"
CKPT = ROOT / "checkpoints" / "phase25a_barr_regional_refiner_v1_1_roi030"
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
    index = {"artifact": "phase25a_roi030_table_index", "classification": "CANONICAL_PHASE25A",
             "roi_proposal_threshold": 0.30, "segmentation_output_threshold": 0.50,
             "tables": {}, "generated_utc": UTC}

    for run, d in RUNS.items():
        src = EXP / d / "history.csv"
        if not src.exists():
            print(f"FAIL-CLOSED: missing {src}")
            return 2
        hist = pd.read_csv(src)
        if run == "final":
            out_name = "phase25a_roi030_final_refit_history.csv"
        else:
            out_name = f"phase25a_roi030_{run}_training_history.csv"
        out = TAB / out_name
        hist.to_csv(out, index=False)

        rj = jload(EXP / d / "run.json")
        best_dice = None
        if "early_stop_Dice" in hist.columns and rj.get("best_epoch") is not None:
            m = hist[hist["epoch"] == rj["best_epoch"]]
            if len(m):
                best_dice = float(m["early_stop_Dice"].iloc[0])
        summary_rows.append({
            "run": run,
            "outer_fold": rj.get("outer_fold"),
            "classification": rj.get("classification"),
            "roi_proposal_threshold": rj.get("roi_proposal_threshold"),
            "segmentation_output_threshold": rj.get("segmentation_output_threshold"),
            "epochs_completed": rj.get("epochs_completed"),
            "epochs_target": rj.get("epochs_target"),
            "best_epoch": rj.get("best_epoch"),
            "best_early_stop_loss": rj.get("best_early_stop_loss"),
            "best_early_stop_dice": best_dice,
            "final_train_loss": rj.get("final_train_loss"),
            "stop_reason": rj.get("stop_reason"),
            "resume_count": rj.get("resume_count"),
            "n_fit_action_available": rj.get("n_fit_action_available"),
            "n_early_stop_action_available": rj.get("n_early_stop_action_available"),
            "parameter_count": rj.get("parameter_count"),
            "history_sha256": rj.get("history_sha256"),
            "test_reads": rj.get("test_reads"),
        })
        index["tables"][out_name] = {"sha256": sha(out), "rows": int(len(hist)),
                                     "bytes": out.stat().st_size}

    sel = pd.DataFrame(summary_rows)
    sel_path = TAB / "phase25a_roi030_refiner_selected_epochs.csv"
    sel.to_csv(sel_path, index=False)
    index["tables"][sel_path.name] = {"sha256": sha(sel_path), "rows": int(len(sel)),
                                      "bytes": sel_path.stat().st_size}

    # ---- checkpoint inventory --------------------------------------------- #
    inv = []
    for f in sorted(CKPT.rglob("*.pt")):
        inv.append({
            "run": f.parent.name,
            "file": f.name,
            "sha256": sha(f),
            "bytes": f.stat().st_size,
            "classification": "CANONICAL_PHASE25A",
        })
    inv_df = pd.DataFrame(inv)
    inv_path = TAB / "phase25a_roi030_checkpoint_inventory.csv"
    inv_df.to_csv(inv_path, index=False)
    index["tables"][inv_path.name] = {"sha256": sha(inv_path), "rows": int(len(inv_df)),
                                      "bytes": inv_path.stat().st_size}

    (TAB / "phase25a_roi030_table_index.json").write_text(
        json.dumps(index, indent=1) + "\n", encoding="utf-8")

    print(sel[["run", "best_epoch", "best_early_stop_loss", "epochs_completed",
               "stop_reason"]].to_string(index=False))
    print(f"\nwrote {len(index['tables'])} canonical tables + index")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
