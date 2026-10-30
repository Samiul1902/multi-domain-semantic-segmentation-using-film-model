"""Phase 25A (CANONICAL RERUN) — derive FINAL_REFIT_EPOCHS_ROI030.

Reads the three ROI-0.30 folds' own best epochs (e0, e1, e2), computes the integer
median, and PERSISTS the rule BEFORE the final refit starts.

The ROI-0.50 value (27) is explicitly NOT reused.

Writes:
    reports/audits/phase25a_roi030_final_refit_epoch_rule.json

Usage:
    ./.venv/Scripts/python.exe scripts/analysis/build_phase25a_roi030_final_refit_rule.py
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
EXP = ROOT / "experiments" / "phase25a_barr_regional_refiner_v1_1_roi030"
UTC = datetime.now(timezone.utc).isoformat()
ROI050_EPOCHS = 27


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main() -> int:
    best: dict[str, int] = {}
    raw: dict[str, int] = {}
    for f in ("fold0", "fold1", "fold2"):
        rj = EXP / f / "run.json"
        if not rj.exists():
            print(f"FAIL-CLOSED: missing {rj}")
            return 2
        rec = json.loads(rj.read_text(encoding="utf-8"))
        if rec.get("stop_reason") is None:
            print(f"FAIL-CLOSED: {f} not complete (stop_reason is None)")
            return 2
        ep = rec.get("best_epoch")
        if ep is None:
            print(f"FAIL-CLOSED: {f} has no best_epoch")
            return 2
        raw[f] = int(ep)

    e = sorted(raw.values())
    median = int(e[1])          # integer median of three
    median = int(round((e[0] + e[1] + e[2]) / 3)) if (e[0] + e[1] + e[2]) % 3 == 0 else e[1]
    # explicit: integer median of three sorted values is the middle element
    median = int(e[1])

    rule = {
        "artifact": "phase25a_roi030_final_refit_epoch_rule",
        "phase": "25A",
        "classification": "CANONICAL_PHASE25A_AFTER_THRESHOLD_ADJUDICATION",
        "roi_proposal_threshold": 0.30,
        "segmentation_output_threshold": 0.50,
        "rule": "FINAL_REFIT_EPOCHS_ROI030 = integer median of the 3 ROI-0.30 fold best epochs",
        "per_fold_best_epoch": raw,
        "source_best_epochs": e,
        "final_refit_epochs": median,
        "roi050_value": ROI050_EPOCHS,
        "roi050_value_reused": median == ROI050_EPOCHS,
        "roi050_value_reused_note": "false means the ROI-0.30 median genuinely differs from the "
                                    "superseded ROI-0.50 median",
        "persisted_before_final_refit": True,
        "early_stopping_in_final_refit": False,
        "holdout_used": False,
        "val_used": False,
        "test_used": False,
        "fold_run_json_sha256": {f: sha(EXP / f / "run.json") for f in ("fold0", "fold1", "fold2")},
        "generated_utc": UTC,
        "verdict": "PHASE25A_ROI030_FINAL_REFIT_EPOCH_RULE_PERSISTED",
    }
    (AUD / "phase25a_roi030_final_refit_epoch_rule.json").write_text(
        json.dumps(rule, indent=1) + "\n", encoding="utf-8")
    print(f"folds best epochs : {raw}")
    print(f"sorted            : {e}")
    print(f"FINAL_REFIT_EPOCHS_ROI030 = {median}")
    print(f"ROI-0.50 value reused?    : {rule['roi050_value_reused']}")
    print(rule["verdict"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
