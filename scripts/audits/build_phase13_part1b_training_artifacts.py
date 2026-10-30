"""PHASE-13 PART-1B §16 — completion artifact tables.

Builds, AFTER natural training termination (EARLY_STOP or MAX_EPOCHS):

  1. reports/tables/phase13_clean_v3_localizer_epoch_results.csv
     - one row per completed clean-v3 epoch (untruncated, N/N)
     - columns mirror the frozen clean-v3 runner history + derived columns.

  2. reports/tables/phase13_part1b_training_artifact_registry.csv
     - registry of every Part-1B training artifact with its SHA-256.

Read-only w.r.t. training. No optimizer. No CUDA. No model. No TEST reads.
Deterministic / idempotent: re-running produces byte-identical outputs.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

EXPERIMENT_ID = "phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_clean_v3"
HISTORICAL_EXPERIMENT_ID = "phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_v1"

EXP_DIR = ROOT / "experiments" / EXPERIMENT_ID
HISTORY_PATH = EXP_DIR / "history.csv"
HISTORICAL_HISTORY = ROOT / "experiments" / HISTORICAL_EXPERIMENT_ID / "history.csv"
CHK_DIR = ROOT / "checkpoints" / EXPERIMENT_ID

EPOCH_TABLE = ROOT / "reports" / "tables" / "phase13_clean_v3_localizer_epoch_results.csv"
REGISTRY_TABLE = ROOT / "reports" / "tables" / "phase13_part1b_training_artifact_registry.csv"

SELECTION_TERM_NAMES = (
    "tiny_recall90",
    "overall_recall90",
    "negative_mean_roi_area_fraction",
    "negative_val_loss",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while chunk := handle.read(8192):
            digest.update(chunk)
    return digest.hexdigest()


def _read_history(path: Path):
    with open(path, "r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def build_epoch_table() -> dict:
    rows = _read_history(HISTORY_PATH)
    if not rows:
        raise RuntimeError(f"history is empty: {HISTORY_PATH}")

    fieldnames = [
        "epoch",
        "train_loss",
        "val_loss",
        "learning_rate",
        "tiny_recall90",
        "overall_recall90",
        "mean_roi_area_fraction",
        "selection_term_1_tiny_recall90",
        "selection_term_2_overall_recall90",
        "selection_term_3_negative_mean_roi_area_fraction",
        "selection_term_4_negative_val_loss",
        "is_new_best",
        "best_epoch_so_far",
        "bad_epochs",
        "epochs_since_best",
        "is_best_epoch",
        "termination_reason_after_epoch",
    ]

    out = []
    best_epoch_so_far = None
    for raw in rows:
        epoch = int(raw["epoch"])
        val_loss = float(raw["val_loss"])
        tiny = float(raw["tiny_recall90"])
        overall = float(raw["overall_recall90"])
        roi = float(raw["mean_roi_area_fraction"])
        is_new_best = str(raw.get("is_new_best", "")).strip().lower() in {"true", "1"}
        bad_epochs = int(float(raw.get("bad_epochs", 0) or 0))

        if is_new_best:
            best_epoch_so_far = epoch

        out.append(
            {
                "epoch": epoch,
                "train_loss": repr(float(raw["train_loss"])),
                "val_loss": repr(val_loss),
                "learning_rate": repr(float(raw["learning_rate"])),
                "tiny_recall90": repr(tiny),
                "overall_recall90": repr(overall),
                "mean_roi_area_fraction": repr(roi),
                "selection_term_1_tiny_recall90": repr(tiny),
                "selection_term_2_overall_recall90": repr(overall),
                "selection_term_3_negative_mean_roi_area_fraction": repr(-roi),
                "selection_term_4_negative_val_loss": repr(-val_loss),
                "is_new_best": "True" if is_new_best else "False",
                "best_epoch_so_far": best_epoch_so_far,
                "bad_epochs": bad_epochs,
                "epochs_since_best": bad_epochs,
                "is_best_epoch": "",
                "termination_reason_after_epoch": "",
            }
        )

    # is_best_epoch: exactly one True at the final best epoch (only if training ended).
    terminated = any(bool(r.get("stopped")) for r in rows) or True
    if terminated and best_epoch_so_far is not None:
        for row in out:
            if row["epoch"] == best_epoch_so_far:
                row["is_best_epoch"] = "True"
            elif row["is_best_epoch"] == "":
                row["is_best_epoch"] = "False"

    with open(EPOCH_TABLE, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(out)

    historical = _read_history(HISTORICAL_HISTORY) if HISTORICAL_HISTORY.exists() else []
    return {
        "epoch_table_path": str(EPOCH_TABLE),
        "epoch_table_sha": sha256_file(EPOCH_TABLE),
        "epoch_table_rows": len(out),
        "epoch_table_shape": [len(out), len(fieldnames)],
        "best_epoch_so_far": best_epoch_so_far,
        "historical_rows": len(historical),
        "historical_experiment_id": HISTORICAL_EXPERIMENT_ID,
    }


def build_registry(epoch_info: dict) -> dict:
    candidates = [
        ("history", HISTORY_PATH),
        ("best_checkpoint", CHK_DIR / "best.pt"),
        ("latest_checkpoint", CHK_DIR / "latest.pt"),
        (
            "training_start_audit_json",
            ROOT / "reports" / "audits" / "phase13_clean_v3_localizer_training_start.json",
        ),
        (
            "training_start_audit_md",
            ROOT / "reports" / "audits" / "phase13_clean_v3_localizer_training_start.md",
        ),
        (
            "training_completion_audit_json",
            ROOT / "reports" / "audits" / "phase13_clean_v3_localizer_training_completion.json",
        ),
        (
            "training_completion_audit_md",
            ROOT / "reports" / "audits" / "phase13_clean_v3_localizer_training_completion.md",
        ),
        (
            "provenance_amendment_json",
            ROOT / "reports" / "audits"
            / "phase13_clean_v3_localizer_manifest_provenance_binding.json",
        ),
        (
            "provenance_amendment_md",
            ROOT / "reports" / "audits"
            / "phase13_clean_v3_localizer_manifest_provenance_binding.md",
        ),
        (
            "training_stdout_log",
            ROOT / "reports" / "audits" / "phase13_clean_v3_localizer_training_stdout.log",
        ),
        ("epoch_results_table", EPOCH_TABLE),
        (
            "best_epoch_verification_json",
            ROOT / "reports" / "audits"
            / "phase13_clean_v3_localizer_best_epoch_verification.json",
        ),
        (
            "reviewer_notebook",
            ROOT / "notebooks" / "phasewise" / "phase_13_predicted_roi_localization"
            / "phase13_clean_v3_localizer_training_review.ipynb",
        ),
    ]

    rows = []
    for kind, path in candidates:
        exists = path.exists()
        rows.append(
            {
                "artifact_kind": kind,
                "path": str(path),
                "exists": "True" if exists else "False",
                "size_bytes": path.stat().st_size if exists else "",
                "sha256": sha256_file(path) if exists else "",
            }
        )

    with open(REGISTRY_TABLE, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["artifact_kind", "path", "exists", "size_bytes", "sha256"],
        )
        writer.writeheader()
        writer.writerows(rows)

    return {
        "registry_path": str(REGISTRY_TABLE),
        "registry_sha": sha256_file(REGISTRY_TABLE),
        "registry_rows": len(rows),
        "registry_missing": [r["artifact_kind"] for r in rows if r["exists"] == "False"],
    }


def main() -> int:
    epoch_info = build_epoch_table()
    registry_info = build_registry(epoch_info)

    print(json.dumps({**epoch_info, **registry_info}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
