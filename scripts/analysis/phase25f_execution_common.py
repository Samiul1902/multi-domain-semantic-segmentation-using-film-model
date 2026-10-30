"""Phase 25F — CANONICAL POST-SAFETY EXECUTION (shared execution module).

Implements the physically frozen v1.0 post-safety specification
(``ra_medfilm_barr_post_safety_v1_0``) as an executable training / inference
stack:

* ``BARRPostSafetyV1`` — Linear(20,32) -> SiLU -> Linear(32,16) -> SiLU -> Linear(16,1)
* FIT-only standardization of the 16 numeric features (ddof = 0, zero-sigma rule)
* ``BCEWithLogitsLoss(reduction="mean")`` + AdamW(1e-3, 1e-4) + ReduceLROnPlateau
* EARLY_STOP-mean-BCE checkpoint selection (MINIMIZE, 1e-12 strict improvement)
* resumable, atomic, RNG-complete logical runs (harness teardown safe)

NO A7/A8 segmentation comparison, NO C8/C9 system-performance comparison, NO
ROUTER_HOLDOUT / VAL808 / TEST access. All artifacts are ROUTER_DEVELOPMENT
(4957) only.
"""
from __future__ import annotations

import csv
import json
import os
import random
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase25f_spec_repair_common as C  # noqa: E402

# --------------------------------------------------------------------------- #
# paths
# --------------------------------------------------------------------------- #
ROOT = C.ROOT
AUD = C.AUD
TAB = C.TAB
CACHE25F = C.CACHE25F

RUN_FAMILY = "phase25f_barr_post_safety_v1_0_seed42"
CKPT_ROOT = ROOT / "checkpoints" / RUN_FAMILY
EXP_ROOT = ROOT / "experiments" / RUN_FAMILY

FEATURES_NPY = CACHE25F / "features.npy"
METADATA_CSV = CACHE25F / "metadata.csv"
FEATURE_SCHEMA_CSV = CACHE25F / "feature_schema.csv"
TARGETS_CSV = CACHE25F / "targets.csv"
OOF_PRED_CSV = CACHE25F / "phase25f_oof_safety_predictions.csv"

# --------------------------------------------------------------------------- #
# frozen contract values
# --------------------------------------------------------------------------- #
FEATURE_DIM = 20
NUMERIC_IDX = list(range(0, 16))
ONEHOT_IDX = list(range(16, 20))
HIDDEN = (32, 16)
EXPECTED_PARAMS = 1217

N_DEV = 4957
POS_EXPECTED = 2775
NEG_EXPECTED = 2182
ZERO_DELTA_EXPECTED = 67

CV_SEEDS = {0: 54000, 1: 54001, 2: 54002, 3: 54003, 4: 54004}
FINAL_SEED = 42

BATCH_SIZE = 128
MAX_EPOCHS = 200
PATIENCE = 20
LR = 1e-3
WEIGHT_DECAY = 1e-4
IMPROVEMENT_EPS = 1e-12

SOMEGA_ACCEPT_PROB_THRESHOLD = 0.50
SOMEGA_ACCEPT_LOGIT_THRESHOLD = 0.0

# --------------------------------------------------------------------------- #
# deterministic io
# --------------------------------------------------------------------------- #
def sha256_file(p: Path) -> str:
    return C.sha256_file(Path(p))


def sha256_bytes(b: bytes) -> str:
    import hashlib
    return hashlib.sha256(b).hexdigest()


def atomic_write(path: Path, data: bytes) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = str(path) + ".tmp"
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, path)


def atomic_torch_save(obj, path: Path) -> None:
    import io
    buf = io.BytesIO()
    torch.save(obj, buf)
    atomic_write(path, buf.getvalue())


def jdump(obj, path: Path) -> None:
    C.jdump(_convert(obj), path)


def _convert(o):
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (np.float32, np.float64)):
        return float(o)
    if isinstance(o, (np.int32, np.int64)):
        return int(o)
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, dict):
        return {k: _convert(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_convert(v) for v in o]
    return o


def write_csv(path: Path, header, rows) -> None:
    import io
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(header)
    for r in rows:
        w.writerow(r)
    atomic_write(path, buf.getvalue().encode("utf-8"))


def read_csv_rows(path: Path):
    with open(path, "r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# --------------------------------------------------------------------------- #
# model
# --------------------------------------------------------------------------- #
class BARRPostSafetyV1(nn.Module):
    """Linear(20,32) -> SiLU -> Linear(32,16) -> SiLU -> Linear(16,1).

    Returns one RAW logit (no sigmoid inside the module).
    """

    def __init__(self) -> None:
        super().__init__()
        self.fc1 = nn.Linear(FEATURE_DIM, HIDDEN[0])
        self.fc2 = nn.Linear(HIDDEN[0], HIDDEN[1])
        self.fc3 = nn.Linear(HIDDEN[1], 1)
        self.reset_parameters()

    def reset_parameters(self) -> None:
        # Exactly the standard PyTorch Linear initialization, made explicit.
        for lin in (self.fc1, self.fc2, self.fc3):
            nn.init.kaiming_uniform_(lin.weight, a=np.sqrt(5))
            bound = 1.0 / np.sqrt(lin.in_features)
            nn.init.uniform_(lin.bias, -bound, bound)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = nn.functional.silu(self.fc1(x))
        x = nn.functional.silu(self.fc2(x))
        return self.fc3(x).squeeze(-1)


def count_params(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def build_model(seed: int, device) -> BARRPostSafetyV1:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    model = BARRPostSafetyV1()
    return model.to(device)


# --------------------------------------------------------------------------- #
# normalization (FIT only, ddof = 0, zero-sigma rule)
# --------------------------------------------------------------------------- #
def fit_normalization(fit_features: np.ndarray):
    """Return (mu, sigma, constant_mask) over the 16 numeric columns."""
    num = fit_features[:, NUMERIC_IDX].astype(np.float64)
    mu = num.mean(axis=0)
    sigma = num.std(axis=0, ddof=0)
    const = sigma < 1e-12
    return mu, sigma, const


def apply_normalization(features: np.ndarray, mu, sigma, const) -> np.ndarray:
    out = features.astype(np.float32).copy()
    sigma_safe = np.where(sigma < 1e-12, 1.0, sigma)
    norm = (features[:, NUMERIC_IDX].astype(np.float64) - mu) / sigma_safe
    norm[:, const] = 0.0
    out[:, NUMERIC_IDX] = norm.astype(np.float32)
    # one-hot columns 16..19 stay raw
    return out


# --------------------------------------------------------------------------- #
# data loading
# --------------------------------------------------------------------------- #
def load_features():
    return np.load(FEATURES_NPY).astype(np.float32)


def load_metadata():
    return read_csv_rows(METADATA_CSV)


def load_targets():
    return read_csv_rows(TARGETS_CSV)


def load_fold_members():
    """Return {k: {'fit': [ids], 'early_stop': [ids], 'outer_target': [ids]}}."""
    members = {}
    for k in range(5):
        members[k] = {}
        for split in ("fit", "early_stop", "outer_target"):
            p = TAB / f"phase25d_cv_fold{k}_{split}_ids.csv"
            members[k][split] = [r["sample_id"] for r in read_csv_rows(p)]
    return members


def load_cv_manifest():
    return read_csv_rows(TAB / "phase25d_cv5_manifest.csv")


# --------------------------------------------------------------------------- #
# RNG state capture / restore
# --------------------------------------------------------------------------- #
def capture_rng(gen: torch.Generator) -> dict:
    st = {
        "python": random.getstate(),
        "numpy": np.random.get_state(),
        "torch": torch.get_rng_state(),
        "generator": gen.get_state(),
    }
    if torch.cuda.is_available():
        st["cuda"] = torch.cuda.get_rng_state_all()
    return st


def restore_rng(st: dict, gen: torch.Generator) -> None:
    random.setstate(st["python"])
    np.random.set_state(st["numpy"])
    torch.set_rng_state(st["torch"])
    if torch.cuda.is_available() and "cuda" in st:
        torch.cuda.set_rng_state_all(st["cuda"])
    gen.set_state(st["generator"])


# --------------------------------------------------------------------------- #
# training (resumable, one logical run)
# --------------------------------------------------------------------------- #
def _loader(X: np.ndarray, y: np.ndarray, gen: torch.Generator, shuffle: bool, device):
    ds = TensorDataset(torch.from_numpy(X), torch.from_numpy(y))
    return DataLoader(ds, batch_size=BATCH_SIZE, shuffle=shuffle, generator=gen,
                      num_workers=0, drop_last=False)


def train_logical_run(
    *,
    run_id: str,
    ckpt_dir: Path,
    exp_dir: Path,
    seed: int,
    fit_X: np.ndarray,
    fit_y: np.ndarray,
    es_X: np.ndarray,
    es_y: np.ndarray,
    device,
    max_epochs: int = MAX_EPOCHS,
    patience: int = PATIENCE,
    use_early_stop: bool = True,
    force_epochs: int | None = None,
    verbose: bool = True,
) -> dict:
    """Train one logical run with full RNG-complete resumability.

    Per-epoch order (frozen): train FIT -> evaluate complete EARLY_STOP ->
    mean EARLY_STOP BCE -> checkpoint decision -> atomically persist
    history/checkpoint -> scheduler.step(early_stop_bce) -> patience update.
    """
    ckpt_dir = Path(ckpt_dir)
    exp_dir = Path(exp_dir)
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    exp_dir.mkdir(parents=True, exist_ok=True)

    done_path = exp_dir / "run_complete.json"
    if done_path.exists():
        if verbose:
            print(f"[{run_id}] already complete -> skip")
        return json.loads(done_path.read_text(encoding="utf-8"))

    state_path = ckpt_dir / "state.pt"
    best_path = ckpt_dir / "best.pt"
    hist_path = exp_dir / "history.csv"

    gen = torch.Generator()
    gen.manual_seed(seed)

    if state_path.exists():
        state = torch.load(state_path, map_location="cpu", weights_only=False)
        model = BARRPostSafetyV1().to(device)
        model.load_state_dict(state["model_state"])
        optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
        optimizer.load_state_dict(state["optimizer_state"])
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, mode="min", factor=0.5, patience=8,
            threshold=1e-4, threshold_mode="rel", cooldown=0, min_lr=1e-6, eps=1e-8)
        scheduler.load_state_dict(state["scheduler_state"])
        restore_rng(state["rng"], gen)
        start_epoch = state["epoch"] + 1
        best_loss = state["best_loss"]
        best_epoch = state["best_epoch"]
        bad_epochs = state["bad_epochs"]
        history = state["history"]
        if verbose:
            print(f"[{run_id}] resuming from epoch {start_epoch} (best={best_epoch})")
    else:
        model = build_model(seed, device)
        optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, mode="min", factor=0.5, patience=8,
            threshold=1e-4, threshold_mode="rel", cooldown=0, min_lr=1e-6, eps=1e-8)
        start_epoch = 1
        best_loss = float("inf")
        best_epoch = -1
        bad_epochs = 0
        history = []

    criterion = nn.BCEWithLogitsLoss(reduction="mean")
    limit = force_epochs if force_epochs is not None else max_epochs

    t0 = time.time()
    epoch = start_epoch - 1
    for epoch in range(start_epoch, limit + 1):
        model.train()
        fit_loader = _loader(fit_X, fit_y, gen, shuffle=True, device=device)
        losses = []
        for xb, yb in fit_loader:
            xb, yb = xb.to(device), yb.to(device)
            optimizer.zero_grad(set_to_none=True)
            logit = model(xb)
            loss = criterion(logit, yb)
            loss.backward()
            optimizer.step()
            losses.append(loss.item())
        train_bce = float(np.mean(losses))

        if use_early_stop:
            model.eval()
            es_loader = _loader(es_X, es_y, gen, shuffle=False, device=device)
            es_losses = []
            with torch.inference_mode():
                for xb, yb in es_loader:
                    xb, yb = xb.to(device), yb.to(device)
                    es_losses.append(criterion(model(xb), yb).item())
            monitor = float(np.mean(es_losses))
        else:
            monitor = train_bce  # final refit: sample-weighted TRAIN BCE

        # checkpoint decision (MINIMIZE, strict 1e-12 improvement, tie = earlier)
        is_best = False
        is_tie = False
        if use_early_stop:
            if monitor < best_loss - IMPROVEMENT_EPS:
                best_loss = monitor
                best_epoch = epoch
                bad_epochs = 0
                is_best = True
            else:
                if abs(monitor - best_loss) <= IMPROVEMENT_EPS:
                    is_tie = True
                bad_epochs += 1

        # atomically persist history + state (and best checkpoint)
        entry = {
            "epoch": epoch,
            "train_bce": train_bce,
            "early_stop_bce": monitor if use_early_stop else "",
            "learning_rate": optimizer.param_groups[0]["lr"],
            "is_best": int(is_best),
            "is_tie": int(is_tie),
            "bad_epochs": bad_epochs,
            "elapsed_seconds": round(time.time() - t0, 3),
        }
        history.append(entry)
        write_csv(hist_path, list(entry.keys()), [list(e.values()) for e in history])

        if is_best:
            atomic_torch_save({
                "model_state": model.state_dict(),
                "epoch": epoch,
                "best_epoch": best_epoch,
                "best_monitor": best_loss,
                "seed": seed,
                "run_id": run_id,
            }, best_path)

        atomic_torch_save({
            "model_state": model.state_dict(),
            "optimizer_state": optimizer.state_dict(),
            "scheduler_state": scheduler.state_dict(),
            "epoch": epoch,
            "best_loss": best_loss,
            "best_epoch": best_epoch,
            "bad_epochs": bad_epochs,
            "history": history,
            "rng": capture_rng(gen),
            "seed": seed,
            "run_id": run_id,
        }, state_path)

        scheduler.step(monitor)

        if use_early_stop and bad_epochs >= patience:
            if verbose:
                print(f"[{run_id}] early stop at epoch {epoch}, best={best_epoch}")
            break

    termination = "early_stop" if (use_early_stop and bad_epochs >= patience) else (
        "fixed_epochs" if force_epochs is not None else "max_epochs")
    closure = {
        "run_id": run_id,
        "seed": seed,
        "total_epochs": len(history),
        "last_epoch": history[-1]["epoch"],
        "best_epoch": best_epoch,
        "best_monitor_bce": best_loss if use_early_stop else None,
        "termination": termination,
        "patience": patience if use_early_stop else None,
        "early_stopping": bool(use_early_stop),
        "force_epochs": force_epochs,
        "model_parameter_count": count_params(model),
        "best_checkpoint_sha256": sha256_file(best_path) if best_path.exists() else None,
        "state_checkpoint_sha256": sha256_file(state_path),
        "history_sha256": sha256_file(hist_path),
    }
    jdump(closure, done_path)
    if verbose:
        print(f"[{run_id}] done: {closure['termination']} best_epoch={best_epoch}")
    return closure


# --------------------------------------------------------------------------- #
# inference
# --------------------------------------------------------------------------- #
def predict_logits(model: nn.Module, X: np.ndarray, device) -> np.ndarray:
    model.eval()
    out = []
    with torch.inference_mode():
        for i in range(0, len(X), 512):
            xb = torch.from_numpy(X[i:i + 512]).to(device)
            out.append(model(xb).cpu().numpy())
    return np.concatenate(out).astype(np.float32)


def load_best_model(ckpt_path: Path, device) -> BARRPostSafetyV1:
    ck = torch.load(ckpt_path, map_location=device, weights_only=False)
    m = BARRPostSafetyV1().to(device)
    m.load_state_dict(ck["model_state"])
    m.eval()
    return m


def load_final_model(ckpt_path: Path, device) -> BARRPostSafetyV1:
    ck = torch.load(ckpt_path, map_location=device, weights_only=False)
    m = BARRPostSafetyV1().to(device)
    m.load_state_dict(ck["model_state"])
    m.eval()
    return m


# --------------------------------------------------------------------------- #
# deterministic fusion / fallback (frozen state machine)
# --------------------------------------------------------------------------- #
def fuse_prediction(p_global: np.ndarray, p_refined_resized: np.ndarray,
                    roi_mask: np.ndarray, accept: bool) -> np.ndarray:
    """Frozen ROI-weighted fusion / fallback.

    * ``accept`` False (reject or skip) -> ``p_final = p_global`` everywhere.
    * ``accept`` True -> ``p_final = p_global`` outside the frozen ROI and
      ``p_final = p_refined_resized`` inside it.

    No alpha blending, no learned fusion. Arrays are (H, W) probabilities;
    ``roi_mask`` is a boolean (H, W) mask.
    """
    if not accept:
        return p_global.astype(np.float32, copy=True)
    out = p_global.astype(np.float32, copy=True)
    out[roi_mask] = p_refined_resized.astype(np.float32)[roi_mask]
    return out


def c9_state(c8_decision: str, action_available: bool, p_accept: float) -> dict:
    """Resolve the frozen Phase25F state machine for one sample/policy."""
    if not action_available:
        return {"state": "STATE_A", "refiner_executed": False,
                "somega_executed": False, "final": "GLOBAL",
                "outcome": "FORCED_SKIP"}
    if c8_decision == "SKIP":
        return {"state": "STATE_B", "refiner_executed": False,
                "somega_executed": False, "final": "GLOBAL",
                "outcome": "PRE_GATE_SKIP"}
    accept = p_accept >= SOMEGA_ACCEPT_PROB_THRESHOLD
    return {"state": "STATE_C", "refiner_executed": True,
            "somega_executed": True,
            "final": "REGIONAL_FUSED" if accept else "GLOBAL",
            "outcome": "EXECUTE_THEN_ACCEPT" if accept else "EXECUTE_THEN_REJECT"}
