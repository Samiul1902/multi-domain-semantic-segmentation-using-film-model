"""
Phase-14 resume-equivalence verification (DISK-ONLY).

Compares the preserved uninterrupted valid attempt (attempt 2, epochs 1-12)
against the current run (attempt 4, resumed from epoch 10 via RNG-state restore).

Hard constraints honoured:
  - NO model forward passes
  - NO backward passes
  - NO inference
  - NO TEST reads

Only torch.load / pandas / hashing of already-written artifacts.
"""
import json
import sys
from pathlib import Path

import pandas as pd
import torch

ROOT = Path(r"D:\Softfors\jup")
PRESERVED = ROOT / "checkpoints/_INTERRUPTED_VALID_ATTEMPT_20260924/phase14_kub_refiner_unet_a3_256_seed42_clean_v3"
CURRENT_CKPT = ROOT / "checkpoints/phase14_kub_refiner_unet_a3_256_seed42_clean_v3"
CURRENT_EXP = ROOT / "experiments/phase14_kub_refiner_unet_a3_256_seed42_clean_v3"

METRIC_COLS = [
    "epoch", "train_loss", "val_loss", "val_crop_dice", "learning_rate",
    "is_new_best", "best_epoch_so_far", "bad_epochs",
]

report = {
    "artifact": "PHASE14_RESUME_EQUIVALENCE_VERIFICATION",
    "kind": "DISK_ONLY_VERIFICATION",
    "method_note": "No forward pass, no backward pass, no inference, no TEST read. Only already-written artifacts were loaded and compared.",
    "compared": {},
    "metric_comparison": {},
    "state_comparison": {},
    "first_mismatch": None,
    "classification": None,
}


def fail(msg, where):
    if report["first_mismatch"] is None:
        report["first_mismatch"] = {"where": where, "detail": msg}
    print(f"MISMATCH [{where}]: {msg}")


def _json_default(o):
    """Make numpy scalars/arrays JSON-serialisable."""
    import numpy as _np
    if isinstance(o, _np.integer):
        return int(o)
    if isinstance(o, _np.floating):
        return float(o)
    if isinstance(o, _np.bool_):
        return bool(o)
    if isinstance(o, _np.ndarray):
        return o.tolist()
    if isinstance(o, torch.Tensor):
        return o.tolist()
    return str(o)


def tensors_equal(a, b, path, tol=0.0):
    """Exact (or tolerance) comparison of nested tensor/state structures."""
    ok = True
    if isinstance(a, torch.Tensor) and isinstance(b, torch.Tensor):
        if a.shape != b.shape:
            fail(f"shape {tuple(a.shape)} != {tuple(b.shape)}", path)
            return False
        if a.dtype != b.dtype:
            fail(f"dtype {a.dtype} != {b.dtype}", path)
            return False
        if a.numel() == 0:
            return True
        d = (a.to(torch.float64) - b.to(torch.float64)).abs().max().item()
        if tol == 0.0:
            if not torch.equal(a, b):
                fail(f"values differ, max abs diff = {d}", path)
                return False
        elif d > tol:
            fail(f"max abs diff {d} > tol {tol}", path)
            return False
        return True
    if isinstance(a, dict) and isinstance(b, dict):
        ka, kb = set(a.keys()), set(b.keys())
        if ka != kb:
            fail(f"key sets differ: only_a={sorted(map(str, ka - kb))[:5]} only_b={sorted(map(str, kb - ka))[:5]}", path)
            ok = False
        for k in sorted(ka & kb, key=str):
            if not tensors_equal(a[k], b[k], f"{path}.{k}", tol):
                ok = False
        return ok
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        if len(a) != len(b):
            fail(f"length {len(a)} != {len(b)}", path)
            return False
        for i, (x, y) in enumerate(zip(a, b)):
            if not tensors_equal(x, y, f"{path}[{i}]", tol):
                ok = False
        return ok
    # scalars / other
    try:
        if isinstance(a, float) or isinstance(b, float):
            if abs(float(a) - float(b)) > tol:
                fail(f"{a} != {b}", path)
                return False
        else:
            if a != b:
                fail(f"{a!r} != {b!r}", path)
                return False
    except Exception as e:
        fail(f"uncomparable types {type(a)} vs {type(b)}: {e}", path)
        return False
    return ok


# ------------------------------------------------------------------ metrics
cur_hist = pd.read_csv(CURRENT_EXP / "history.csv")
pre_hist = pd.read_csv(PRESERVED / "history.csv")

print(f"current history epochs : {list(cur_hist['epoch'])}")
print(f"preserved history epochs: {list(pre_hist['epoch'])}")

common = sorted(set(cur_hist["epoch"]) & set(pre_hist["epoch"]))
report["metric_comparison"]["common_epochs"] = common

metric_ok = True
per_epoch = {}
for ep in common:
    rc = cur_hist[cur_hist["epoch"] == ep].iloc[0]
    rp = pre_hist[pre_hist["epoch"] == ep].iloc[0]
    row = {}
    for col in METRIC_COLS:
        if col not in cur_hist.columns or col not in pre_hist.columns:
            continue
        vc, vp = rc[col], rp[col]
        if isinstance(vc, float) or isinstance(vp, float):
            same = (float(vc) == float(vp))
        else:
            same = (vc == vp)
        row[col] = {"current": (float(vc) if isinstance(vc, float) else vc),
                    "preserved": (float(vp) if isinstance(vp, float) else vp),
                    "equal": bool(same)}
        if not same:
            metric_ok = False
            fail(f"epoch {ep} {col}: current={vc!r} preserved={vp!r}", f"history.epoch{ep}.{col}")
    per_epoch[ep] = row
report["metric_comparison"]["per_epoch"] = per_epoch
report["metric_comparison"]["all_common_epochs_equal"] = metric_ok

# explicitly surface epochs 11 and 12 (the requested focus)
for ep in (11, 12):
    if ep in per_epoch:
        row = per_epoch[ep]
        print(f"epoch {ep}: train_loss={row['train_loss']['current']} val_loss={row['val_loss']['current']} "
              f"val_crop_dice={row['val_crop_dice']['current']} lr={row['learning_rate']['current']} "
              f"best_epoch={row['best_epoch_so_far']['current']} bad={row['bad_epochs']['current']} "
              f"-> {'MATCH' if all(v['equal'] for v in row.values()) else 'MISMATCH'}")

# ------------------------------------------------------------------ state (epoch 9 best.pt, shared epoch)
pre_best = torch.load(PRESERVED / "best.pt", map_location="cpu", weights_only=False)
cur_best = torch.load(CURRENT_CKPT / "best.pt", map_location="cpu", weights_only=False)

report["state_comparison"]["preserved_best_epoch"] = int(pre_best["epoch"])
report["state_comparison"]["current_best_epoch"] = int(cur_best["epoch"])
report["state_comparison"]["shared_epoch"] = int(cur_best["epoch"]) == int(pre_best["epoch"])
report["state_comparison"]["preserved_best_has_rng_state"] = "rng_state" in pre_best
report["state_comparison"]["current_best_has_rng_state"] = "rng_state" in cur_best

state_ok = True
if int(cur_best["epoch"]) == int(pre_best["epoch"]):
    for key in ("model_state", "optimizer_state", "scheduler_state", "grad_scaler_state"):
        a, b = pre_best.get(key), cur_best.get(key)
        if a is None or b is None:
            report["state_comparison"][key] = {"compared": False, "reason": "missing in one side"}
            continue
        ok = tensors_equal(a, b, key)
        report["state_comparison"][key] = {"compared": True, "equal": bool(ok)}
        if not ok:
            state_ok = False
        print(f"  {key}: {'IDENTICAL' if ok else 'DIFFERS'}")
    # scalar metadata that is scientifically meaningful
    for key in ("best_val_crop_dice", "best_epoch", "bad_epochs", "seed", "experiment_id"):
        if key in pre_best and key in cur_best:
            same = pre_best[key] == cur_best[key]
            report["state_comparison"][f"meta_{key}"] = {"preserved": pre_best[key], "current": cur_best[key], "equal": bool(same)}
            if not same:
                state_ok = False
                fail(f"{key}: {pre_best[key]!r} != {cur_best[key]!r}", f"best.{key}")
else:
    report["state_comparison"]["note"] = "best.pt epochs differ; state comparison not applicable"
    state_ok = None

# ------------------------------------------------------------------ verdict
if report["first_mismatch"] is None and metric_ok and state_ok is True:
    report["classification"] = "BIT_EXACT_CONFIRMED"
elif report["first_mismatch"] is None and metric_ok and state_ok is None:
    report["classification"] = "METRIC_EXACT__STATE_NOT_COMPARABLE"
else:
    report["classification"] = "MISMATCH_DETECTED__STOP"

print()
print("first_mismatch:", report["first_mismatch"])
print("classification:", report["classification"])

out = ROOT / "reports/audits/phase14_resume_equivalence_verification.json"
out.write_text(json.dumps(report, indent=2, default=_json_default), encoding="utf-8")
print("written:", out)
