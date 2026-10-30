"""PHASE-13 PART-1B §8/§9 — canonical selection-history reconstruction.

Rebuilds the authoritative checkpoint-selection sequence for the whole
experiment under R2C HISTORICAL_EXECUTING_BBOX_COVERAGE.

Rows 1-30 need no inference: proposals were zero, so the primary coverage terms
were identically zero under either semantics (ZERO_PROPOSAL_INVARIANT).

Row 31 uses the R2C canonical bbox re-evaluation.

Performs a strict lexicographic > replay and reports whether epoch 31 remains the
canonical best.

Writes reports/tables/phase13_part1b_canonical_selection_history.csv
No training. No model. No CUDA. No TEST.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

EXP = "phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_clean_v3"
HISTORY = ROOT / "experiments" / EXP / "history.csv"
E31 = ROOT / "reports" / "audits" / "phase13_part1b_epoch31_canonical_bbox_evaluation.json"
OUT = ROOT / "reports" / "tables" / "phase13_part1b_canonical_selection_history.csv"
OUT_JSON = ROOT / "reports" / "audits" / "phase13_part1b_canonical_selection_reconstruction.json"

FIELDS = [
    "epoch",
    "canonical_tiny_recall90",
    "canonical_overall_recall90",
    "canonical_mean_roi_area_fraction",
    "canonical_val_loss",
    "canonical_selection_tuple",
    "canonical_is_new_best",
    "canonical_best_epoch_so_far",
    "canonical_bad_epochs",
    "source_metric_semantics",
    "raw_history_status",
]


def main() -> int:
    history = list(csv.DictReader(open(HISTORY, newline="", encoding="utf-8")))
    e31 = json.loads(E31.read_text(encoding="utf-8"))
    bbox = e31["bbox_primary"]
    e31_val_loss = float(e31["val_loss"])

    rows = []
    best_score = None
    best_epoch = None
    bad = 0
    for raw in history:
        epoch = int(raw["epoch"])
        val_loss = float(raw["val_loss"])
        if epoch <= 30:
            tiny = 0.0
            overall = 0.0
            roi = 0.0
            semantics = "ZERO_PROPOSAL_INVARIANT"
            raw_status = "PRIMARY_VALID_ZERO_PROPOSAL_INVARIANT"
        elif epoch == 31:
            tiny = float(bbox["tiny_recall90"])
            overall = float(bbox["overall_recall90"])
            roi = float(bbox["mean_roi_area_fraction"])
            val_loss = e31_val_loss
            semantics = "R2C_HISTORICAL_BBOX_REEVALUATION"
            raw_status = "R2B_PIXEL_SEMANTICS_PROVISIONAL"
        else:
            # Rows >= 32 were produced by the R2C runner, whose unsuffixed
            # primary fields ARE historical bbox coverage.
            produced = str(raw.get("coverage_semantics_primary", "")).strip()
            if produced != "HISTORICAL_EXECUTING_BBOX_COVERAGE":
                raise ValueError(
                    f"epoch {epoch} row does not declare "
                    f"HISTORICAL_EXECUTING_BBOX_COVERAGE (got {produced!r}). STOP."
                )
            tiny = float(raw["tiny_recall90"])
            overall = float(raw["overall_recall90"])
            roi = float(raw["mean_roi_area_fraction"])
            semantics = "R2C_HISTORICAL_BBOX_COVERAGE"
            raw_status = "R2C_CANONICAL_PRIMARY"

        score = (tiny, overall, -roi, -val_loss)
        if best_score is None or score > best_score:
            is_new_best = True
            best_score = score
            best_epoch = epoch
            bad = 0
        else:
            is_new_best = False
            bad += 1

        rows.append(
            {
                "epoch": epoch,
                "canonical_tiny_recall90": repr(tiny),
                "canonical_overall_recall90": repr(overall),
                "canonical_mean_roi_area_fraction": repr(roi),
                "canonical_val_loss": repr(val_loss),
                "canonical_selection_tuple": json.dumps(list(score)),
                "canonical_is_new_best": "True" if is_new_best else "False",
                "canonical_best_epoch_so_far": best_epoch,
                "canonical_bad_epochs": bad,
                "source_metric_semantics": semantics,
                "raw_history_status": raw_status,
            }
        )

    with open(OUT, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    # ---- §9 critical branch ------------------------------------------------
    best_through_30 = None
    for row in rows:
        if row["epoch"] == 30:
            best_through_30 = int(row["canonical_best_epoch_so_far"])
    e31_row = next(r for r in rows if r["epoch"] == 31)
    final_row = rows[-1]
    e31_is_best = int(e31_row["canonical_best_epoch_so_far"]) == 31
    final_best = int(final_row["canonical_best_epoch_so_far"])

    payload = {
        "artifact": "PHASE13_PART1B_CANONICAL_SELECTION_RECONSTRUCTION",
        "experiment_id": EXP,
        "rows": len(rows),
        "table_path": str(OUT),
        "primary_coverage_semantics": "HISTORICAL_EXECUTING_BBOX_COVERAGE",
        "prior_canonical_best_epoch_through_30": best_through_30,
        "epoch31_canonical_tuple": json.loads(e31_row["canonical_selection_tuple"]),
        "epoch31_still_canonical_best": e31_is_best,
        "canonical_best_epoch_through_31": int(e31_row["canonical_best_epoch_so_far"]),
        "canonical_bad_epochs_after_31": int(e31_row["canonical_bad_epochs"]),
        "final_canonical_epoch": int(final_row["epoch"]),
        "final_canonical_best_epoch": final_best,
        "final_canonical_bad_epochs": int(final_row["canonical_bad_epochs"]),
        "final_canonical_best_tuple": json.loads(
            next(r for r in rows if r["epoch"] == final_best)["canonical_selection_tuple"]
        ),
        "raw_history_modified": False,
        "test_reads": 0,
    }
    payload["status"] = "PASS" if e31_is_best else "CHECK_REQUIRED"
    payload["branch"] = (
        "CONTINUE_TO_ARCHIVE_AND_REBIND" if e31_is_best else "PRIOR_CANONICAL_BEST_WEIGHTS_UNAVAILABLE"
    )
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"rows                              : {len(rows)}")
    print(f"prior canonical best through 30   : {best_through_30}")
    print(f"epoch31 canonical tuple           : {payload['epoch31_canonical_tuple']}")
    print(f"epoch31 still canonical best      : {e31_is_best}")
    print(f"canonical best through 31         : {payload['canonical_best_epoch_through_31']}")
    print(f"canonical bad_epochs after 31     : {payload['canonical_bad_epochs_after_31']}")
    print(f"FINAL canonical epoch             : {payload['final_canonical_epoch']}")
    print(f"FINAL canonical best epoch        : {final_best}")
    print(f"FINAL canonical bad_epochs        : {payload['final_canonical_bad_epochs']}")
    print(f"FINAL canonical best tuple        : {payload['final_canonical_best_tuple']}")
    print(f"BRANCH                            : {payload['branch']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
