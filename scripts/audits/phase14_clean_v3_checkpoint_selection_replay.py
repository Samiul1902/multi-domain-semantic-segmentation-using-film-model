"""
Phase-14 clean-v3 checkpoint-selection replay (DISK-ONLY).

Verifies that the frozen checkpoint rule was honoured:
  rule      : best_val_crop_dice  (max over val_crop_dice)
  artifacts : best.pt / latest.pt / history.csv / closure.json

No forward passes, no backward passes, no inference, no TEST reads.
"""
import json
from pathlib import Path

import pandas as pd
import torch

ROOT = Path(r"D:\Softfors\jup")
EXP = ROOT / "experiments/phase14_kub_refiner_unet_a3_256_seed42_clean_v3"
CKPT = ROOT / "checkpoints/phase14_kub_refiner_unet_a3_256_seed42_clean_v3"

hist = pd.read_csv(EXP / "history.csv")
closure = json.loads((EXP / "closure.json").read_text(encoding="utf-8"))
best = torch.load(CKPT / "best.pt", map_location="cpu", weights_only=False)
latest = torch.load(CKPT / "latest.pt", map_location="cpu", weights_only=False)

argmax_epoch = int(hist.loc[hist["val_crop_dice"].idxmax(), "epoch"])
argmax_dice = float(hist["val_crop_dice"].max())
last_epoch = int(hist["epoch"].max())

report = {
    "artifact": "PHASE14_CLEAN_V3_CHECKPOINT_SELECTION_REPLAY",
    "kind": "DISK_ONLY_REPLAY",
    "method_note": "No forward pass, no backward pass, no inference, no TEST read.",
    "frozen_rule": {
        "checkpoint_metric": "val_crop_dice",
        "mode": "max",
        "checkpoint_rule": "best_val_crop_dice",
        "early_stopping": {"patience": 15, "metric": "val_crop_dice", "mode": "max"},
    },
    "history": {
        "epochs_recorded": last_epoch,
        "rows": int(len(hist)),
        "argmax_epoch": argmax_epoch,
        "argmax_val_crop_dice": argmax_dice,
    },
    "artifacts": {
        "best_pt_epoch": int(best["epoch"]),
        "best_pt_best_val_crop_dice": float(best["best_val_crop_dice"]),
        "best_pt_best_epoch_field": int(best.get("best_epoch", -1)),
        "best_pt_bad_epochs": int(best.get("bad_epochs", -1)),
        "latest_pt_epoch": int(latest["epoch"]),
        "latest_pt_best_val_crop_dice": float(latest["best_val_crop_dice"]),
        "latest_pt_best_epoch_field": int(latest.get("best_epoch", -1)),
        "latest_pt_bad_epochs": int(latest.get("bad_epochs", -1)),
    },
    "closure": {
        "best_epoch": closure["best_epoch"],
        "best_val_crop_dice": closure["best_val_crop_dice"],
        "total_epochs": closure["total_epochs"],
        "stop_reason": closure["stop_reason"],
        "crop_margin": closure["crop_margin"],
        "crop_margin_role": closure["crop_margin_role"],
        "predicted_proposal_margin": closure["predicted_proposal_margin"],
        "best_checkpoint_sha256": closure["best_checkpoint_sha256"],
        "latest_checkpoint_sha256": closure["latest_checkpoint_sha256"],
        "history_sha256": closure["history_sha256"],
    },
    "checks": {},
}

checks = report["checks"]
checks["best_pt_epoch_equals_history_argmax"] = int(best["epoch"]) == argmax_epoch
checks["best_pt_dice_equals_history_argmax"] = abs(float(best["best_val_crop_dice"]) - argmax_dice) < 1e-12
checks["closure_best_epoch_equals_argmax"] = int(closure["best_epoch"]) == argmax_epoch
checks["closure_best_dice_equals_argmax"] = abs(float(closure["best_val_crop_dice"]) - argmax_dice) < 1e-12
checks["latest_pt_epoch_is_final_epoch"] = int(latest["epoch"]) == last_epoch
checks["closure_total_epochs_is_final_epoch"] = int(closure["total_epochs"]) == last_epoch
checks["latest_pt_carries_best_dice"] = abs(float(latest["best_val_crop_dice"]) - argmax_dice) < 1e-12
checks["best_epoch_field_consistent"] = int(best.get("best_epoch", -1)) == argmax_epoch
checks["stop_reason_is_early_stopping"] = closure["stop_reason"] == "EARLY_STOPPING_PATIENCE_15"
checks["early_stopping_arithmetic"] = (last_epoch - argmax_epoch) == 15
checks["crop_margin_is_role_resolved_025"] = abs(float(closure["crop_margin"]) - 0.25) < 1e-12
checks["predicted_proposal_margin_is_020"] = abs(float(closure["predicted_proposal_margin"]) - 0.20) < 1e-12
checks["history_rows_equal_epochs"] = int(len(hist)) == last_epoch

all_ok = all(bool(v) for v in checks.values())
report["verdict"] = "REPLAY_PASS__FROZEN_RULE_HONOURED" if all_ok else "REPLAY_FAIL"
report["failed_checks"] = [k for k, v in checks.items() if not v]

print(json.dumps({k: report[k] for k in ("history", "artifacts", "checks", "verdict", "failed_checks")}, indent=2))

out = ROOT / "reports/audits/phase14_clean_v3_checkpoint_selection_replay.json"
out.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("written:", out)
