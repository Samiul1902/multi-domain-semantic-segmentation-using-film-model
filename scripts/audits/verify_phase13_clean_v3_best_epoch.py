"""PHASE-13 PART-1B §19 — independent canonical best-epoch verification.

Emits the registry-expected artifact
``reports/audits/phase13_clean_v3_localizer_best_epoch_verification.json``.

R2C: the AUTHORITATIVE replay source is the canonical selection sidecar
``reports/tables/phase13_part1b_canonical_selection_history.csv``, replayed using
ONLY the historical bbox primary coverage semantics.

Rationale: row 31 of the immutable ``history.csv`` carries LEGACY primary fields
that were produced under R2B pixel-mask coverage. The raw-history replay is
therefore reported only as a cross-check, never as the authoritative result.

Verifies:
  * canonical sidecar replay: is_new_best / best_epoch_so_far / bad_epochs
  * best epoch == best.pt epoch == completion-audit best epoch
  * best tuple reproduction
  * early-stop arithmetic (best_epoch + patience == final epoch)
  * contiguity and finite values

Read-only. No training. No optimizer. No inference. No CUDA. No TEST reads.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

EXPERIMENT_ID = "phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_clean_v3"
EXP_DIR = ROOT / "experiments" / EXPERIMENT_ID
CHK_DIR = ROOT / "checkpoints" / EXPERIMENT_ID
HISTORY_PATH = EXP_DIR / "history.csv"
CANON_PATH = ROOT / "reports" / "tables" / "phase13_part1b_canonical_selection_history.csv"
COMPLETION_PATH = ROOT / "reports" / "audits" / "phase13_clean_v3_localizer_training_completion.json"
OUT_JSON = ROOT / "reports" / "audits" / "phase13_clean_v3_localizer_best_epoch_verification.json"

PATIENCE = 15
TOL = 1e-12
PRIMARY_SEMANTICS = "HISTORICAL_EXECUTING_BBOX_COVERAGE"


def sha256_file(path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while chunk := handle.read(8192):
            digest.update(chunk)
    return digest.hexdigest()


def _replay(rows, key):
    """Strict lexicographic > replay over a sequence of scored rows."""
    best_score = best_epoch = None
    bad = 0
    out = []
    for row in rows:
        epoch = int(row["epoch"])
        score = (
            float(row[key["tiny"]]),
            float(row[key["overall"]]),
            -float(row[key["roi"]]),
            -float(row[key["val_loss"]]),
        )
        if best_score is None or score > best_score:
            is_new_best, best_score, best_epoch, bad = True, score, epoch, 0
        else:
            is_new_best, bad = False, bad + 1
        out.append(
            {
                "epoch": epoch,
                "score": score,
                "is_new_best": is_new_best,
                "best_epoch_so_far": best_epoch,
                "bad_epochs": bad,
            }
        )
    return out, best_score, best_epoch, bad


def main() -> int:
    import torch

    canon = list(csv.DictReader(open(CANON_PATH, newline="", encoding="utf-8")))
    history = pd.read_csv(HISTORY_PATH)
    completion = json.loads(COMPLETION_PATH.read_text(encoding="utf-8"))

    # ---- authoritative: canonical sidecar replay (bbox primary only) -------
    canon_rows, canon_best_score, canon_best_epoch, canon_bad = _replay(
        canon,
        {"tiny": "canonical_tiny_recall90", "overall": "canonical_overall_recall90",
         "roi": "canonical_mean_roi_area_fraction", "val_loss": "canonical_val_loss"},
    )
    mismatches = []
    for recorded, replayed in zip(canon, canon_rows):
        epoch = int(recorded["epoch"])
        if (recorded["canonical_is_new_best"] == "True") != replayed["is_new_best"]:
            mismatches.append(f"canonical_is_new_best@epoch{epoch}")
        if int(recorded["canonical_best_epoch_so_far"]) != replayed["best_epoch_so_far"]:
            mismatches.append(f"canonical_best_epoch_so_far@epoch{epoch}")
        if int(recorded["canonical_bad_epochs"]) != replayed["bad_epochs"]:
            mismatches.append(f"canonical_bad_epochs@epoch{epoch}")

    # ---- cross-check only: raw-history replay (mixed semantics at row 31) --
    raw = history.to_dict(orient="records")
    raw_rows, raw_best_score, raw_best_epoch, raw_bad = _replay(
        raw,
        {"tiny": "tiny_recall90", "overall": "overall_recall90",
         "roi": "mean_roi_area_fraction", "val_loss": "val_loss"},
    )

    epochs = [int(r["epoch"]) for r in canon]
    contiguous = epochs == list(range(1, len(epochs) + 1))
    non_finite = []
    for column in ("canonical_tiny_recall90", "canonical_overall_recall90",
                   "canonical_mean_roi_area_fraction", "canonical_val_loss"):
        series = pd.to_numeric(pd.Series([r[column] for r in canon]), errors="coerce")
        if series.isna().any():
            non_finite.append(column)

    ckpt = torch.load(CHK_DIR / "best.pt", map_location="cpu", weights_only=False)
    checkpoint_epoch = int(ckpt["epoch"])
    latest = torch.load(CHK_DIR / "latest.pt", map_location="cpu", weights_only=False)
    latest_epoch = int(latest["epoch"])

    payload = {
        "artifact": "PHASE13_CLEAN_V3_LOCALIZER_BEST_EPOCH_VERIFICATION",
        "document_type": "INDEPENDENT_BEST_EPOCH_REPLAY",
        "experiment_id": EXPERIMENT_ID,
        "primary_coverage_semantics": PRIMARY_SEMANTICS,
        "pixel_metrics_consulted": False,
        "authoritative_replay_source": str(CANON_PATH),
        "canonical_sidecar_sha": sha256_file(CANON_PATH),
        "history_path": str(HISTORY_PATH),
        "history_sha": sha256_file(HISTORY_PATH),
        "history_rows": len(history),
        "history_contiguous": contiguous,
        "canonical_rows": len(canon),
        "nan_inf_events": non_finite,
        "selection_terms": ["tiny_recall90", "overall_recall90",
                            "-mean_roi_area_fraction", "-val_loss"],
        "replayed_best_epoch": canon_best_epoch,
        "replayed_best_score": list(canon_best_score) if canon_best_score else None,
        "replayed_final_bad_epochs": canon_bad,
        "recorded_best_epoch": int(completion["best_epoch"]),
        "checkpoint_best_epoch": checkpoint_epoch,
        "latest_epoch": latest_epoch,
        "completion_best_tuple": completion["best_selection_tuple"],
        "completion_termination": completion["termination_reason"],
        "best_epoch_reproduced": canon_best_epoch == int(completion["best_epoch"]),
        "checkpoint_epoch_matches_best": checkpoint_epoch == canon_best_epoch,
        "best_tuple_reproduced": all(
            abs(a - b) <= TOL for a, b in zip(canon_best_score, completion["best_selection_tuple"])
        ),
        "final_bad_epochs_equals_patience": canon_bad == PATIENCE,
        "early_stop_epoch_reproduced": (
            len(epochs) == int(completion["best_epoch"]) + PATIENCE
            and completion["termination_reason"] == "EARLY_STOPPING_PATIENCE"
        ),
        "cross_check_raw_history": {
            "note": "reported for transparency only; row 31 legacy primaries are "
                    "pixel-based, so this replay is NOT authoritative",
            "raw_replayed_best_epoch": raw_best_epoch,
            "raw_replayed_best_score": list(raw_best_score) if raw_best_score else None,
            "raw_final_bad_epochs": raw_bad,
            "agrees_with_canonical_best_epoch": raw_best_epoch == canon_best_epoch,
        },
        "mismatches": mismatches,
        "no_training": True,
        "no_optimizer": True,
        "no_cuda": True,
        "test_reads": 0,
    }
    payload["status"] = (
        "PASS"
        if (
            contiguous
            and not non_finite
            and not mismatches
            and payload["best_epoch_reproduced"]
            and payload["checkpoint_epoch_matches_best"]
            and payload["best_tuple_reproduced"]
            and payload["final_bad_epochs_equals_patience"]
            and payload["early_stop_epoch_reproduced"]
        )
        else "CHECK_REQUIRED"
    )
    OUT_JSON.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    print(f"canonical rows        : {len(canon)}")
    print(f"replayed best epoch   : {canon_best_epoch}")
    print(f"checkpoint best epoch : {checkpoint_epoch}")
    print(f"completion best epoch : {completion['best_epoch']}")
    print(f"replayed best tuple   : {canon_best_score}")
    print(f"final bad_epochs      : {canon_bad}")
    print(f"raw cross-check epoch : {raw_best_epoch}")
    print(f"mismatches            : {len(mismatches)}")
    print(f"STATUS                : {payload['status']}")
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
