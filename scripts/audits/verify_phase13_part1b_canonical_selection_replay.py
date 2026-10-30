"""PHASE-13 PART-1B §19 — independent canonical checkpoint-selection replay.

Independently replays the ENTIRE canonical selection sidecar
(reports/tables/phase13_part1b_canonical_selection_history.csv) using ONLY the
historical bbox primary coverage semantics, and confirms that the recorded
best epoch / best tuple / bad_epochs / early stopping all reproduce exactly.

Pixel metrics remain descriptive sensitivity only and are not consulted.

Read-only. No training. No model. No CUDA. No TEST.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

EXP = "phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_clean_v3"
CANON = ROOT / "reports" / "tables" / "phase13_part1b_canonical_selection_history.csv"
COMPLETION = ROOT / "reports" / "audits" / "phase13_clean_v3_localizer_training_completion.json"
OUT = ROOT / "reports" / "audits" / "phase13_part1b_canonical_selection_replay_verification.json"

PATIENCE = 15


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while chunk := handle.read(8192):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    rows = list(csv.DictReader(open(CANON, newline="", encoding="utf-8")))
    epochs = [int(r["epoch"]) for r in rows]

    mismatches = []
    best_score = None
    best_epoch = None
    bad = 0
    for row in rows:
        epoch = int(row["epoch"])
        score = (
            float(row["canonical_tiny_recall90"]),
            float(row["canonical_overall_recall90"]),
            -float(row["canonical_mean_roi_area_fraction"]),
            -float(row["canonical_val_loss"]),
        )
        if best_score is None or score > best_score:
            is_new_best = True
            best_score = score
            best_epoch = epoch
            bad = 0
        else:
            is_new_best = False
            bad += 1
        rec_new = row["canonical_is_new_best"] == "True"
        if rec_new != is_new_best:
            mismatches.append(f"is_new_best@epoch{epoch}: recorded={rec_new} replayed={is_new_best}")
        if int(row["canonical_best_epoch_so_far"]) != best_epoch:
            mismatches.append(
                f"best_epoch_so_far@epoch{epoch}: recorded="
                f"{row['canonical_best_epoch_so_far']} replayed={best_epoch}"
            )
        if int(row["canonical_bad_epochs"]) != bad:
            mismatches.append(
                f"bad_epochs@epoch{epoch}: recorded={row['canonical_bad_epochs']} replayed={bad}"
            )

    completion = json.loads(COMPLETION.read_text(encoding="utf-8"))
    early_stop_expected = int(completion["best_epoch"]) + PATIENCE

    payload = {
        "artifact": "PHASE13_PART1B_CANONICAL_SELECTION_REPLAY_VERIFICATION",
        "document_type": "INDEPENDENT_REPLAY_FROM_CANONICAL_SIDECAR",
        "experiment_id": EXP,
        "sidecar_path": str(CANON),
        "sidecar_sha": sha256_file(CANON),
        "rows": len(rows),
        "contiguous_1_to_N": epochs == list(range(1, len(epochs) + 1)),
        "primary_coverage_semantics": "HISTORICAL_EXECUTING_BBOX_COVERAGE",
        "pixel_metrics_consulted": False,
        "replayed_best_epoch": best_epoch,
        "replayed_best_tuple": list(best_score) if best_score else None,
        "replayed_final_bad_epochs": bad,
        "recorded_completion_best_epoch": int(completion["best_epoch"]),
        "recorded_completion_final_epoch": int(completion["final_epoch"]),
        "recorded_completion_termination": completion["termination_reason"],
        "recorded_completion_best_tuple": completion["best_selection_tuple"],
        "best_epoch_reproduced": best_epoch == int(completion["best_epoch"]),
        "best_tuple_reproduced": (
            best_score is not None
            and all(
                abs(a - b) <= 1e-12
                for a, b in zip(best_score, completion["best_selection_tuple"])
            )
        ),
        "early_stop_arithmetic_reproduced": (
            len(epochs) == early_stop_expected
            and completion["termination_reason"] == "EARLY_STOPPING_PATIENCE"
        ),
        "expected_early_stop_epoch": early_stop_expected,
        "mismatches": mismatches,
        "no_training": True,
        "no_model": True,
        "no_cuda": True,
        "test_reads": 0,
    }
    payload["status"] = (
        "PASS"
        if (
            payload["contiguous_1_to_N"]
            and not mismatches
            and payload["best_epoch_reproduced"]
            and payload["best_tuple_reproduced"]
            and payload["early_stop_arithmetic_reproduced"]
        )
        else "CHECK_REQUIRED"
    )
    OUT.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    print(f"sidecar rows              : {len(rows)}")
    print(f"replayed best epoch       : {best_epoch}")
    print(f"replayed best tuple       : {best_score}")
    print(f"replayed final bad_epochs : {bad}")
    print(f"completion best epoch     : {completion['best_epoch']}")
    print(f"mismatches                : {len(mismatches)}")
    for item in mismatches[:8]:
        print("   -", item)
    print(f"STATUS                    : {payload['status']}")
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
