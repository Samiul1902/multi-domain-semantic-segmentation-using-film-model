"""Phase 20B - read-only progress + ETA reporter for the four-model sequence.

Reports, for each of the four conventional models, how many epochs are done, the
current best macro-domain VAL Dice, and a projected completion window for the
whole sequence.

This script is STRICTLY READ-ONLY: it parses ``history.csv`` /
``closure.json`` and never touches checkpoints, locks, the protocol JSON, or the
architecture bindings. It is a reporting aid, not part of the frozen pipeline.

Empirical basis for the projection
----------------------------------
``unet`` (the only completed 20B model) ran 89 epochs (best_epoch 74, then
patience 15) at a mean of ~451 s/epoch. ``attention_unet`` is tracking the same
per-epoch cost (~446 s mean). The projection therefore models a realistic model
as peaking somewhere in epochs 60-80 and terminating at ``best + patience``,
giving a final epoch of roughly 75-95.

Usage:
    python scripts/training/phase20b_progress_eta.py
"""
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

ORDER = ["unet", "attention_unet", "deeplabv3plus", "transformer_mit_unet"]
EXP_DIR = {k: ROOT / "experiments" / f"phase20b_shared_{k}_fourdomain_seed42_clean_v3" for k in ORDER}

HIST_EPOCH_COL = 0
HIST_MACRO_COL = 3
HIST_BEST_EPOCH_COL = 22
HIST_SECONDS_COL = 24

NATURAL_STOP_REASONS = {"EARLY_STOPPING_PATIENCE", "MAX_EPOCHS"}
MAX_EPOCHS = 100
PATIENCE = 15


def read_history(model: str) -> list[dict]:
    path = EXP_DIR[model] / "history.csv"
    if not path.exists():
        return []
    out = []
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.reader(fh):
            if row and row[0].strip().isdigit():
                out.append(row)
    return out


def read_closure(model: str) -> dict | None:
    path = EXP_DIR[model] / "closure.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def model_state(model: str) -> dict:
    closure = read_closure(model)
    if closure and closure.get("stop_reason") in NATURAL_STOP_REASONS:
        return {
            "model": model,
            "status": "COMPLETE",
            "epochs": closure.get("total_completed_epochs"),
            "best_epoch": closure.get("best_epoch"),
            "best_macro": closure.get("best_macro_domain_dice"),
            "stop_reason": closure.get("stop_reason"),
            "mean_s": None,
        }
    hist = read_history(model)
    if not hist:
        return {"model": model, "status": "NOT_STARTED", "epochs": 0,
                "best_epoch": None, "best_macro": None, "stop_reason": None, "mean_s": None}
    secs = [float(r[HIST_SECONDS_COL]) for r in hist if len(r) > HIST_SECONDS_COL]
    best_epoch = int(float(hist[-1][HIST_BEST_EPOCH_COL])) if len(hist[-1]) > HIST_BEST_EPOCH_COL else None
    best_macro = max(float(r[HIST_MACRO_COL]) for r in hist)
    return {
        "model": model,
        "status": "IN_PROGRESS",
        "epochs": len(hist),
        "best_epoch": best_epoch,
        "best_macro": best_macro,
        "stop_reason": None,
        "mean_s": (sum(secs) / len(secs)) if secs else None,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rate", type=float, default=None,
                    help="Override s/epoch. Default: mean over all observed epochs.")
    ap.add_argument("--peak-lo", type=int, default=60,
                    help="Lower bound of the assumed best-epoch window.")
    ap.add_argument("--peak-hi", type=int, default=80,
                    help="Upper bound of the assumed best-epoch window.")
    args = ap.parse_args()

    states = [model_state(m) for m in ORDER]

    all_secs = []
    for m in ORDER:
        hist = read_history(m)
        all_secs += [float(r[HIST_SECONDS_COL]) for r in hist if len(r) > HIST_SECONDS_COL]
    rate = args.rate or (sum(all_secs) / len(all_secs) if all_secs else 460.0)

    now = datetime.now()
    print(f"NOW: {now:%a %Y-%m-%d %H:%M}   rate={rate:.0f} s/epoch")
    print("-" * 78)
    total_lo = total_hi = 0.0
    for s in states:
        if s["status"] == "COMPLETE":
            print(f"{s['model']:<20} COMPLETE  {s['epochs']:>3} ep  "
                  f"best_ep={s['best_epoch']}  macro={s['best_macro']:.6f}  {s['stop_reason']}")
            continue
        if s["status"] == "NOT_STARTED":
            lo, hi = args.peak_lo + PATIENCE, min(MAX_EPOCHS, args.peak_hi + PATIENCE)
            rem_lo, rem_hi = lo, hi
            print(f"{s['model']:<20} NOT_STARTED  -> projected final {lo}-{hi} ep  "
                  f"({rem_lo * rate / 3600:.1f}-{rem_hi * rate / 3600:.1f} h)")
        else:
            lo = max(args.peak_lo, s["epochs"]) + PATIENCE
            hi = min(MAX_EPOCHS, args.peak_hi + PATIENCE)
            rem_lo, rem_hi = max(0, lo - s["epochs"]), max(0, hi - s["epochs"])
            best_ep = s["best_epoch"] if s["best_epoch"] is not None else "?"
            print(f"{s['model']:<20} IN_PROGRESS {s['epochs']:>3} ep  best_ep={best_ep}  "
                  f"macro={s['best_macro']:.6f}  -> remaining {rem_lo * rate / 3600:.1f}-"
                  f"{rem_hi * rate / 3600:.1f} h")
        total_lo += rem_lo * rate
        total_hi += rem_hi * rate

    print("-" * 78)
    if total_lo == 0 and total_hi == 0:
        print("SEQUENCE COMPLETE - all four models naturally terminated.")
        return 0
    lo_dt = now + timedelta(seconds=total_lo)
    hi_dt = now + timedelta(seconds=total_hi)
    print(f"Projected remaining : {total_lo / 3600:.1f} - {total_hi / 3600:.1f} h")
    print(f"Projected completion: {lo_dt:%a %Y-%m-%d %H:%M}  ..  {hi_dt:%a %Y-%m-%d %H:%M}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
