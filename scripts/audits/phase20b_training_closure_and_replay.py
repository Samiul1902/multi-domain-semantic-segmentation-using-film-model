"""Phase-20B training closure + DISK-ONLY checkpoint-selection replay (per model).

Generalises ``scripts/audits/phase20_training_closure_and_replay.py`` to any
Phase-20B model key. The scientific content is IDENTICAL: it replays the frozen
selection rule (``phase20_macro_domain_mean_dice_v1``) over the saved per-epoch
history and confirms

    history-selected epoch  ==  stored best epoch  ==  best.pt epoch

No inference is performed. Fails closed on any mismatch, any missing/duplicate
epoch row, any SHA drift, or any sign of an independent duplicate run.

Writes
------
reports/audits/phase20b_<slug>_training_closure.json
reports/audits/phase20b_<slug>_checkpoint_selection_replay.json

Usage
-----
    ./.venv/Scripts/python.exe scripts/audits/phase20b_training_closure_and_replay.py --model-key unet
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd
import torch

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from phase20b_common import (  # noqa: E402
    AUDIT_DIR,
    ORDER,
    ckpt_dir,
    closure_json,
    exp_dir,
    experiment_id,
    replay_json,
)
from src.training.phase20_selection import (  # noqa: E402
    DOMAIN_ORDER,
    SELECTION_RULE_ID,
    select_best_epoch,
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_model(model_key: str) -> bool:
    exp = exp_dir(model_key)
    ckpt = ckpt_dir(model_key)
    exp_id = experiment_id(model_key)
    history_path = exp / "history.csv"

    if not (exp / "closure.json").exists():
        print(f"FAIL [{model_key}]: experiments/{exp_id}/closure.json missing (training not terminated).")
        return False

    closure_local = json.loads((exp / "closure.json").read_text(encoding="utf-8"))
    history = pd.read_csv(history_path)

    # ---- history integrity -------------------------------------------------
    epochs = history["epoch"].astype(int).tolist()
    expected = list(range(1, len(epochs) + 1))
    integrity = {
        "n_rows": int(len(history)),
        "epochs_contiguous_from_1": epochs == expected,
        "missing_epochs": sorted(set(expected) - set(epochs)),
        "duplicate_epochs": sorted({e for e in epochs if epochs.count(e) > 1}),
        "monotonic_epochs": all(epochs[i] < epochs[i + 1] for i in range(len(epochs) - 1)),
        "required_columns_present": all(
            c in history.columns for c in
            ["epoch", "train_loss", "val_loss", "macro_domain_dice", "learning_rate",
             "is_new_best", "best_epoch_so_far", "bad_epochs", "epoch_seconds",
             *[f"val_dice_{d}" for d in DOMAIN_ORDER],
             *[f"val_iou_{d}" for d in DOMAIN_ORDER]]),
        "history_sha256": sha256_file(history_path),
    }

    # ---- disk-only replay --------------------------------------------------
    replay = select_best_epoch(history.to_dict("records"))
    stored_best_epoch = int(closure_local["best_epoch"])
    best_ck = torch.load(ckpt / "best.pt", map_location="cpu", weights_only=False)
    best_ck_epoch = int(best_ck["epoch"])
    best_ck_macro = float(best_ck["best_macro_domain_dice"])
    latest_ck = torch.load(ckpt / "latest.pt", map_location="cpu", weights_only=False)

    history_best_row = history.loc[history["epoch"] == replay["selected_epoch"]].iloc[0]
    replay_macro = float(history_best_row["macro_domain_dice"])

    checks = {
        "selection_rule_id_matches": replay["selection_rule_id"] == SELECTION_RULE_ID
        and closure_local["selection_rule_id"] == SELECTION_RULE_ID,
        "history_selected_epoch_equals_stored_best_epoch":
            replay["selected_epoch"] == stored_best_epoch,
        "stored_best_epoch_equals_best_pt_epoch": stored_best_epoch == best_ck_epoch,
        "replayed_macro_matches_best_pt_macro": abs(replay_macro - best_ck_macro) < 1e-9,
        "replayed_macro_matches_closure": abs(replay_macro - float(closure_local["best_macro_domain_dice"])) < 1e-9,
        "history_integrity_ok": (integrity["epochs_contiguous_from_1"]
                                 and not integrity["missing_epochs"]
                                 and not integrity["duplicate_epochs"]
                                 and integrity["monotonic_epochs"]
                                 and integrity["required_columns_present"]),
        "no_independent_duplicate_run": int(closure_local.get("independent_duplicate_runs", 0)) == 0,
        "best_pt_sha_matches_closure":
            sha256_file(ckpt / "best.pt") == closure_local["best_checkpoint_sha256"],
        "latest_pt_sha_matches_closure":
            sha256_file(ckpt / "latest.pt") == closure_local["latest_checkpoint_sha256"],
        "test_reads_zero": all(v == 0 for v in closure_local["test_reads"].values()),
    }
    verdict = "PHASE20B_CHECKPOINT_SELECTION_REPLAY_PASS" if all(checks.values()) \
        else "PHASE20B_CHECKPOINT_SELECTION_REPLAY_FAIL"

    best_row = history.loc[history["epoch"] == stored_best_epoch].iloc[0]
    closure = {
        "artifact": "phase20b_training_closure",
        "phase": 20,
        "subphase": "20B",
        "model_key": model_key,
        "experiment_id": exp_id,
        "manifest_version": closure_local["manifest_version"],
        "selection_rule_id": SELECTION_RULE_ID,
        "best_epoch": stored_best_epoch,
        "best_macro_domain_dice": float(closure_local["best_macro_domain_dice"]),
        "per_domain_dice_at_best": {d: float(best_row[f"val_dice_{d}"]) for d in DOMAIN_ORDER},
        "per_domain_iou_at_best": {d: float(best_row[f"val_iou_{d}"]) for d in DOMAIN_ORDER},
        "best_val_loss": float(best_row["val_loss"]),
        "final_epoch": int(closure_local["final_epoch"]),
        "total_completed_epochs": int(closure_local["total_completed_epochs"]),
        "stop_reason": closure_local["stop_reason"],
        "early_stopping_patience": int(closure_local["early_stopping_patience"]),
        "history_path": f"experiments/{exp_id}/history.csv",
        "history_sha256": integrity["history_sha256"],
        "best_checkpoint_path": f"checkpoints/{exp_id}/best.pt",
        "best_checkpoint_sha256": sha256_file(ckpt / "best.pt"),
        "latest_checkpoint_path": f"checkpoints/{exp_id}/latest.pt",
        "latest_checkpoint_sha256": sha256_file(ckpt / "latest.pt"),
        "latest_checkpoint_epoch": int(latest_ck["epoch"]),
        "config_sha256": sha256_file(exp / "config.json"),
        "trainer_path": closure_local["trainer_path"],
        "trainer_sha256": closure_local["trainer_sha256"],
        "model_params": int(closure_local["model_params"]),
        "resume_events": closure_local["resume_events"],
        "resume_count": int(closure_local["resume_count"]),
        "history_integrity": integrity,
        "training_runs": 1,
        "logical_runs": 1,
        "independent_duplicate_runs": 0,
        "test_reads": closure_local["test_reads"],
        "total_elapsed_seconds": closure_local["total_elapsed_seconds"],
        "natural_termination": closure_local["stop_reason"] in ("EARLY_STOPPING_PATIENCE", "MAX_EPOCHS"),
        "manually_stopped_early": False,
    }
    closure_json(model_key).write_text(json.dumps(closure, indent=2), encoding="utf-8")

    replay_payload = {
        "artifact": "phase20b_checkpoint_selection_replay",
        "phase": 20,
        "subphase": "20B",
        "model_key": model_key,
        "experiment_id": exp_id,
        "method": "disk-only replay of the frozen selection rule over saved history; no inference",
        "selection_rule_id": SELECTION_RULE_ID,
        "selection_metric": "macro_domain_mean_validation_dice",
        "tie_break": "lower validation loss",
        "history_selected_epoch": replay["selected_epoch"],
        "history_selected_macro_domain_dice": replay["selected_macro_domain_dice"],
        "stored_best_epoch": stored_best_epoch,
        "best_pt_epoch": best_ck_epoch,
        "best_pt_macro_domain_dice": best_ck_macro,
        "n_epochs_evaluated": replay["n_epochs_evaluated"],
        "n_improvements": replay["n_improvements"],
        "checks": checks,
        "all_checks_passed": all(checks.values()),
        "verdict": verdict,
        "fail_closed": True,
    }
    replay_json(model_key).write_text(json.dumps(replay_payload, indent=2), encoding="utf-8")

    print(f"=== {model_key} CLOSURE ===")
    print(f"best_epoch={stored_best_epoch} best_macro={closure['best_macro_domain_dice']:.6f} "
          f"final_epoch={closure['final_epoch']} stop={closure['stop_reason']}")
    for d in DOMAIN_ORDER:
        print(f"  {d:<8} dice={closure['per_domain_dice_at_best'][d]:.6f} "
              f"iou={closure['per_domain_iou_at_best'][d]:.6f}")
    for k, v in checks.items():
        if not v:
            print(f"  FAIL  {k}")
    print(f"verdict: {verdict}")
    return all(checks.values())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model-key", choices=ORDER, default=None)
    args = ap.parse_args()
    keys = [args.model_key] if args.model_key else ORDER

    ok_all = True
    for k in keys:
        ok_all &= run_model(k)
        print()
    print("REPLAY ALL PASS" if ok_all else "REPLAY FAILED (fail-closed)")
    return 0 if ok_all else 2


if __name__ == "__main__":
    raise SystemExit(main())
