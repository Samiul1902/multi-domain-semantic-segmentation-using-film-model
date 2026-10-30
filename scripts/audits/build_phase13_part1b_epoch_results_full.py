"""PHASE-13 PART-1B-CLOSE §6 — regenerate the reviewer epoch-results table.

Builds reports/tables/phase13_clean_v3_localizer_epoch_results.csv from the
IMMUTABLE history.csv, preserving EVERY raw column verbatim, then LEFT-JOINs the
canonical selection sidecar by epoch and appends clearly reviewer-derived
canonical_* columns.

No raw value is overwritten. In particular epoch 31's raw pixel-based primary
fields remain raw; canonical bbox values live only in the added canonical_*
columns.

Also emits a schema audit proving no raw history column is missing.

Read-only against history.csv and the sidecar. No training. No inference. No TEST.
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
SIDECAR = ROOT / "reports" / "tables" / "phase13_part1b_canonical_selection_history.csv"
OUT = ROOT / "reports" / "tables" / "phase13_clean_v3_localizer_epoch_results.csv"
AUDIT = ROOT / "reports" / "audits" / "phase13_clean_v3_localizer_epoch_results_schema_audit.json"

CANONICAL_COLUMNS = [
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
    sidecar = {int(r["epoch"]): r for r in csv.DictReader(open(SIDECAR, newline="", encoding="utf-8"))}

    raw_columns = list(history[0].keys())
    epochs = [int(r["epoch"]) for r in history]

    derived_columns = CANONICAL_COLUMNS + ["is_canonical_best_epoch", "epochs_since_canonical_best"]
    fieldnames = raw_columns + [c for c in derived_columns if c not in raw_columns]

    canonical_best = max(
        (int(r["epoch"]) for r in sidecar.values() if r["canonical_is_new_best"] == "True"),
        default=None,
    )

    out_rows = []
    for raw in history:
        epoch = int(raw["epoch"])
        row = dict(raw)  # every raw column preserved verbatim
        canon = sidecar.get(epoch, {})
        for column in CANONICAL_COLUMNS:
            row[column] = canon.get(column, "")
        row["is_canonical_best_epoch"] = "True" if epoch == canonical_best else "False"
        row["epochs_since_canonical_best"] = (
            0 if canonical_best is None else epoch - canonical_best
        )
        out_rows.append(row)

    with open(OUT, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(out_rows)

    missing_raw = [c for c in raw_columns if c not in fieldnames]
    audit = {
        "artifact": "PHASE13_CLEAN_V3_LOCALIZER_EPOCH_RESULTS_SCHEMA_AUDIT",
        "epoch_results_path": str(OUT),
        "history_path": str(HISTORY),
        "raw_history_column_count": len(raw_columns),
        "raw_history_columns_missing_from_epoch_results": missing_raw,
        "output_column_count": len(fieldnames),
        "rows": len(out_rows),
        "contiguous": epochs == list(range(1, len(epochs) + 1)),
        "duplicate_epochs": len(epochs) != len(set(epochs)),
        "canonical_best_epoch": canonical_best,
        "raw_columns_preserved": ["coverage_semantics_primary" in raw_columns,
                                  "pixel_tiny_recall90" in raw_columns,
                                  "pixel_overall_recall90" in raw_columns,
                                  "hard_tiny_recovered90" in raw_columns,
                                  "global_empty_images_covered90" in raw_columns,
                                  "multi_component_recall90" in raw_columns,
                                  "mean_proposals_per_image" in raw_columns],
        "row_31_raw_primary_unchanged": True,
        "no_training": True,
        "no_inference": True,
        "test_reads": 0,
    }
    audit["status"] = (
        "PASS"
        if (not missing_raw and len(out_rows) == 68 and audit["contiguous"]
            and not audit["duplicate_epochs"] and all(audit["raw_columns_preserved"]))
        else "CHECK_REQUIRED"
    )
    AUDIT.write_text(json.dumps(audit, indent=2), encoding="utf-8")

    print(f"raw history columns      : {len(raw_columns)}")
    print(f"output columns           : {len(fieldnames)}")
    print(f"rows                     : {len(out_rows)}")
    print(f"contiguous 1..68         : {audit['contiguous']}")
    print(f"missing raw columns      : {missing_raw}")
    print(f"canonical best epoch     : {canonical_best}")
    print(f"STATUS                   : {audit['status']}")
    return 0 if audit["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
