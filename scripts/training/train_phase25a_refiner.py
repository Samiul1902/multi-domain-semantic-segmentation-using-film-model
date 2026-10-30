"""Phase 25A — train ONE regional-refiner run (a fold, or the final refit).

Frozen protocol (Phase-24 v1.1 ``refiner`` block, Phase-25A sections 14-21):

    loss      : 0.5 * BCEWithLogits + 0.5 * soft Dice
    optimizer : AdamW, lr 1e-4, weight_decay 1e-4
    scheduler : cosine annealing, T_max = 100
    max epochs: 100
    patience  : 15
    batch     : 8
    seed      : 42
    AMP       : enabled on CUDA
    selection : minimum EARLY_STOP total loss (Dice is a secondary diagnostic)

Exactly one logical run per invocation. ``--resume`` continues the SAME logical
run from ``latest.pt`` and degrades gracefully to epoch 0 when none exists.

Writes (per run):
    checkpoints/phase25a_barr_regional_refiner_v1_1/<run>/{best.pt,latest.pt,final.pt}
    experiments/phase25a_barr_regional_refiner_v1_1/<run>/{config.json,history.csv,run.json}
    logs/phase25a_<run>.run.log

Usage:
    ./.venv/Scripts/python.exe -u scripts/training/train_phase25a_refiner.py --fold 0 --resume
    ./.venv/Scripts/python.exe -u scripts/training/train_phase25a_refiner.py --final --resume
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import random
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader

ROOT = Path(r"D:/Softfors/jup")
sys.path.insert(0, str(ROOT))

from src.data.barr_refiner_dataset import (  # noqa: E402
    BARRRefinerCropDataset,
    barr_refiner_collate,
    DEFAULT_CACHE_ROOT,
)
from src.data.barr_roi import (  # noqa: E402
    ROI_PROPOSAL_THRESHOLD,
    SEGMENTATION_OUTPUT_THRESHOLD,
)
from src.models.barr import (  # noqa: E402
    BARRRegionalRefinerV1,
    BARR_REFINER_ARCHITECTURE_ID,
    BARR_REFINER_EXPECTED_PARAMETERS,
    count_parameters,
)
from src.utils.device import get_device  # noqa: E402
from src.utils.test_lock import verify_test_lock  # noqa: E402

AUD = ROOT / "reports" / "audits"
# CANONICAL roots: the ROI-0.30 cache and its own checkpoint/experiment trees.
# The ROI-0.50 artifacts stay untouched under phase25a_barr_regional_refiner_v1_1.
CACHE = Path(DEFAULT_CACHE_ROOT)
CKPT_ROOT = ROOT / "checkpoints" / "phase25a_barr_regional_refiner_v1_1_roi030"
EXP_ROOT = ROOT / "experiments" / "phase25a_barr_regional_refiner_v1_1_roi030"

METHOD = "RA-MedFiLM-BARR"
ARCH_REVISION = "ra_medfilm_barr_narrowed_v1_1"
MODULE = "regional_refiner"
SEED = 42
BATCH = 8
LR = 1e-4
WEIGHT_DECAY = 1e-4
MAX_EPOCHS = 100
PATIENCE = 15
T_MAX = 100

# --------------------------------------------------------------------------- #
# Atomic write helpers.
#
# The execution harness tears down the whole process tree without warning. A
# checkpoint or CSV being written at that instant is left TRUNCATED or zero-filled
# on Windows, which destroys the newest (and most valuable) artefact. Writing to a
# temporary file and then os.replace()-ing it makes every destination path either
# the previous COMPLETE file or the new COMPLETE file — never a partial one.
# This is an execution-mechanism change only: no forward pass, loss term,
# optimiser behaviour or data transformation is altered.
# --------------------------------------------------------------------------- #
def _atomic_write_bytes(data: bytes, path: Path) -> None:
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "wb") as fh:
        fh.write(data)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def _atomic_torch_save(obj, path: Path) -> None:
    tmp = path.with_name(path.name + ".tmp")
    torch.save(obj, tmp)
    os.replace(tmp, path)


def _atomic_write_text(text: str, path: Path) -> None:
    _atomic_write_bytes(text.encode("utf-8"), path)


def _as_cpu_byte_tensor(t):
    """Coerce a saved RNG state to a CPU uint8 ByteTensor.

    Checkpoints are loaded with map_location='cpu', but a checkpoint saved from a
    CUDA run may still hold CUDA ByteTensors for the CUDA RNG state.
    torch.set_rng_state requires a CPU ByteTensor.
    """
    if isinstance(t, torch.Tensor):
        return t.detach().to(device="cpu", dtype=torch.uint8).contiguous()
    return torch.tensor(list(t), dtype=torch.uint8)


def restore_rng_state(rs) -> None:
    """Restore every RNG source that influences the training stream.

    Without this a resumed run is NOT bit-exact: DataLoader(shuffle=True) draws a
    fresh permutation seed from the global torch RNG on every __iter__.
    """
    if not rs:
        return
    if rs.get("python") is not None:
        random.setstate(rs["python"])
    if rs.get("numpy") is not None:
        np.random.set_state(rs["numpy"])
    if rs.get("torch_cpu") is not None:
        torch.set_rng_state(_as_cpu_byte_tensor(rs["torch_cpu"]))
    cuda_states = rs.get("torch_cuda")
    if cuda_states is not None and torch.cuda.is_available():
        coerced = [_as_cpu_byte_tensor(s) for s in cuda_states]
        if len(coerced) == torch.cuda.device_count():
            torch.cuda.set_rng_state_all(coerced)
AMP_ENABLED = True
SELECTION_RULE = "minimum EARLY_STOP total loss"

BIND_PATHS = {
    "phase24_exact_spec": AUD / "phase24_exact_implementation_spec.json",
    "roi_threshold_adjudication": AUD / "phase24_phase25_roi_threshold_adjudication.json",
    "roi050_supersession": AUD / "phase25a_roi050_supersession.json",
    "global_checkpoint": ROOT / "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt",
    "augmentation_binding": AUD / "phase25a_augmentation_binding.json",
    "roi_transform_audit": AUD / "phase25a_roi_transform_audit.json",
    "crossfit_protocol": AUD / "phase25a_crossfit_protocol.json",
    "model_source": ROOT / "src" / "models" / "barr" / "regional_refiner.py",
    "dataset_source": ROOT / "src" / "data" / "barr_refiner_dataset.py",
    "roi_source": ROOT / "src" / "data" / "barr_roi.py",
}


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def build_loader(manifest_csv: Path, train: bool, seed: int, epoch: int,
                 shuffle: bool) -> tuple[BARRRefinerCropDataset, DataLoader]:
    ds = BARRRefinerCropDataset(manifest_csv, cache_root=CACHE, train=train,
                                base_seed=seed, epoch=epoch)
    gen = torch.Generator()
    gen.manual_seed(seed + epoch)
    loader = DataLoader(ds, batch_size=BATCH, shuffle=shuffle, num_workers=0,
                        pin_memory=True, drop_last=False, generator=gen,
                        collate_fn=barr_refiner_collate)
    return ds, loader


def dice_score_from_logits(logits: torch.Tensor, targets: torch.Tensor,
                           threshold: float = 0.5, eps: float = 1e-6) -> float:
    pred = torch.sigmoid(logits).ge(threshold)
    tgt = targets.bool()
    dims = tuple(range(1, tgt.ndim))
    tp = (pred & tgt).sum(dims).float()
    fp = (pred & ~tgt).sum(dims).float()
    fn = (~pred & tgt).sum(dims).float()
    return float(((2 * tp + eps) / (2 * tp + fp + fn + eps)).mean().item())


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fold", type=int, choices=[0, 1, 2], default=None)
    ap.add_argument("--final", action="store_true")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--max-epochs", type=int, default=None,
                    help="operational bound only; the scientific protocol is unchanged")
    # ---- canonical ROI-threshold rerun plumbing --------------------------- #
    # The default values keep this script pointing at the CANONICAL ROI-0.30
    # artifacts. The earlier ROI-0.50 run remains reachable only by passing the
    # superseded roots explicitly (provenance/debugging), never by default.
    ap.add_argument("--cache-root", type=str, default=None,
                    help="crop cache root; default = canonical ROI-0.30 cache")
    ap.add_argument("--ckpt-root", type=str, default=None,
                    help="checkpoint root; default = canonical ROI-0.30 root")
    ap.add_argument("--exp-root", type=str, default=None,
                    help="experiment root; default = canonical ROI-0.30 root")
    ap.add_argument("--refit-rule", type=str, default=None,
                    help="path to the final-refit epoch rule JSON; default = ROI-0.30 rule")
    ap.add_argument("--run-tag", type=str, default="phase25a",
                    help="log-file tag; default 'phase25a' (canonical)")
    args = ap.parse_args(argv)
    if (args.fold is None) == (not args.final):
        raise SystemExit("pass exactly one of --fold {0,1,2} or --final")

    global CACHE, CKPT_ROOT, EXP_ROOT
    if args.cache_root:
        CACHE = Path(args.cache_root)
    if args.ckpt_root:
        CKPT_ROOT = Path(args.ckpt_root)
    if args.exp_root:
        EXP_ROOT = Path(args.exp_root)
    refit_rule_path = (Path(args.refit_rule) if args.refit_rule
                       else AUD / "phase25a_roi030_final_refit_epoch_rule.json")

    run = f"fold{args.fold}" if args.fold is not None else "final"
    ckpt_dir = CKPT_ROOT / run
    exp_dir = EXP_ROOT / ("final_refit" if args.final else run)
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    exp_dir.mkdir(parents=True, exist_ok=True)
    (ROOT / "logs").mkdir(parents=True, exist_ok=True)
    log_path = ROOT / "logs" / f"{args.run_tag}_{run}.run.log"
    logf = open(log_path, "a", encoding="utf-8", buffering=1)
    t_start = time.time()

    def log(msg: str) -> None:
        line = f"[{time.strftime('%Y-%m-%dT%H:%M:%S')}] +{time.time()-t_start:8.1f}s {msg}"
        print(line, flush=True)
        logf.write(line + "\n")
        logf.flush()

    verify_test_lock(str(ROOT))
    log(f"TEST lock verified; run={run}")
    log(f"cache_root={CACHE.relative_to(ROOT) if CACHE.is_relative_to(ROOT) else CACHE}")
    log(f"ckpt_root={CKPT_ROOT.relative_to(ROOT) if CKPT_ROOT.is_relative_to(ROOT) else CKPT_ROOT}")
    log(f"exp_root={EXP_ROOT.relative_to(ROOT) if EXP_ROOT.is_relative_to(ROOT) else EXP_ROOT}")

    # ---- idempotency guard (chained relaunch safety) ----------------------- #
    # A run that already reached a terminal state must NOT be resumed: resuming a
    # fold that stopped early would otherwise train extra epochs past its stop and
    # silently alter the frozen result. --resume on a completed run is a no-op.
    existing_run = exp_dir / "run.json"
    if args.resume and existing_run.exists():
        try:
            prev = json.loads(existing_run.read_text(encoding="utf-8"))
        except Exception:
            prev = {}
        if prev.get("stop_reason"):
            log(f"ALREADY COMPLETE run={run} stop_reason={prev['stop_reason']} "
                f"epochs={prev.get('epochs_completed')} — no-op (nothing modified)")
            print(f"PHASE25A_RUN_COMPLETE {run}")
            return 0

    # ---- frozen protocol -------------------------------------------------- #
    for name, p in BIND_PATHS.items():
        if not p.exists():
            log(f"FAIL-CLOSED: missing binding artifact {name}: {p}")
            return 2
    bind = {k: {"path": str(v.relative_to(ROOT)), "sha256": sha(v)}
            for k, v in BIND_PATHS.items()}
    crossfit = json.loads(BIND_PATHS["crossfit_protocol"].read_text(encoding="utf-8"))

    if args.final:
        rule_path = refit_rule_path
        if not rule_path.exists():
            log(f"FAIL-CLOSED: final refit requires {rule_path.name}")
            return 2
        rule = json.loads(rule_path.read_text(encoding="utf-8"))
        epochs_target = int(rule["final_refit_epochs"])
        log(f"final-refit rule {rule_path.name} sha256={sha(rule_path)[:16]}... "
            f"classification={rule.get('classification', 'n/a')}")
        manifest_csv = None
        fit_manifest_sha = None
        es_manifest_sha = None
        outer_fold = None
        early_stopping = False
        log(f"FINAL refit: exactly {epochs_target} epochs (median rule), no early stopping")
    else:
        k = args.fold
        manifest_csv = CACHE / "folds" / f"fold{k}_fit.csv"
        es_csv = CACHE / "folds" / f"fold{k}_early_stop.csv"
        fit_manifest_sha = sha(manifest_csv)
        es_manifest_sha = sha(es_csv)
        outer_fold = k
        epochs_target = MAX_EPOCHS
        early_stopping = True

    seed = SEED
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    device = get_device(require_cuda=True)
    amp = AMP_ENABLED and device.type == "cuda"
    log(f"device={device} amp={amp} torch={torch.__version__}")

    # ---- data ------------------------------------------------------------- #
    if args.final:
        all_dev = pd.concat([
            pd.read_csv(CACHE / "folds" / f"fold{k}_outer_target.csv") for k in range(3)
        ] + [pd.read_csv(CACHE / "folds" / f"fold{k}_fit.csv") for k in range(3)]
            + [pd.read_csv(CACHE / "folds" / f"fold{k}_early_stop.csv") for k in range(3)]
        ).drop_duplicates(subset=["sample_id"])
        manifest_csv = CACHE / "folds" / "final_all_development.csv"
        all_dev[["sample_id", "dataset", "task_id", "group_key"]].to_csv(manifest_csv, index=False)
        fit_manifest_sha = sha(manifest_csv)
        log(f"final refit population manifest: {len(all_dev)} ROUTER_DEVELOPMENT rows")

    ds_train, train_loader = build_loader(manifest_csv, True, seed, 0, shuffle=True)
    ds_es, es_loader = (build_loader(CACHE / "folds" / f"fold{args.fold}_early_stop.csv",
                                     False, seed, 0, shuffle=False)
                        if early_stopping else (None, None))
    log(f"FIT action-available n={len(ds_train)}  domains={ds_train.class_distribution()}")
    if ds_es is not None:
        log(f"EARLY_STOP action-available n={len(ds_es)}  domains={ds_es.class_distribution()}")
    if len(ds_train) == 0:
        log("FAIL-CLOSED: empty FIT population")
        return 2

    # ---- model / optimiser ------------------------------------------------ #
    model = BARRRegionalRefinerV1().to(device)
    n_params = count_parameters(model)
    if n_params != BARR_REFINER_EXPECTED_PARAMETERS:
        log(f"FAIL-CLOSED: parameter mismatch {n_params} != {BARR_REFINER_EXPECTED_PARAMETERS}")
        return 2
    log(f"model=BARRRegionalRefinerV1 params={n_params:,} (frozen)")

    bce = torch.nn.BCEWithLogitsLoss()
    dice_loss_fn = __import__("src.losses.segmentation", fromlist=["DiceLoss"]).DiceLoss(1e-6)
    optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=T_MAX)
    scaler = torch.amp.GradScaler("cuda", enabled=amp)

    history_path = exp_dir / "history.csv"
    history: list[dict] = []
    start_epoch = 0
    best_loss = float("inf")
    best_epoch = -1
    bad_epochs = 0
    resume_count = 0
    stop_reason = ""
    checkpoint_events = 0

    latest = ckpt_dir / "latest.pt"

    def _try_load(path: Path):
        """Load a checkpoint, returning None if it is absent or unreadable.

        A harness teardown can leave a half-written file; that must degrade to
        'no checkpoint' rather than abort the run.
        """
        if not path.exists():
            return None
        try:
            return torch.load(path, map_location="cpu", weights_only=False)
        except Exception as exc:
            log(f"WARNING: unreadable checkpoint {path.name} ({type(exc).__name__}: {exc})")
            return None

    if args.resume:
        state = _try_load(latest)
        source = "latest.pt"
        if state is None and (ckpt_dir / "best.pt").exists():
            # last resort: the best checkpoint. Its history covers 0..best_epoch, so
            # resuming from it re-runs the epochs after best_epoch, which is safe.
            state = _try_load(ckpt_dir / "best.pt")
            source = "best.pt"
        if state is not None:
            if "random_state" not in state or state["random_state"] is None:
                log("FAIL-CLOSED: checkpoint lacks RNG state — refusing to resume "
                    "(a non-bit-exact resume would silently diverge)")
                return 2
            model.load_state_dict(state["model_state"])
            optimizer.load_state_dict(state["optimizer_state"])
            if state.get("scheduler_state") is not None:
                scheduler.load_state_dict(state["scheduler_state"])
            if state.get("grad_scaler_state") is not None:
                scaler.load_state_dict(state["grad_scaler_state"])
            # RNG MUST be restored or the resumed stream diverges (shuffle seeds).
            restore_rng_state(state.get("random_state"))
            start_epoch = int(state["epoch"]) + 1
            best_loss = float(state["best_loss"])
            best_epoch = int(state["best_epoch"])
            bad_epochs = int(state.get("bad_epochs", 0))
            resume_count = int(state.get("resume_count", 0)) + 1
            history = list(state.get("history", []))
            checkpoint_events = int(state.get("checkpoint_events", 0))
            log(f"RESUMED from {source} at epoch {start_epoch} (best_epoch={best_epoch} "
                f"best_es_loss={best_loss:.6f} history_rows={len(history)} "
                f"resume_count={resume_count})")
        else:
            log("no readable checkpoint found — starting from epoch 0 "
                "(graceful degradation)")
            history = []
    else:
        history = []

    config = {
        "experiment_id": f"phase25a_barr_regional_refiner_v1_1_{run}",
        "phase": "25A",
        "method": METHOD,
        "architecture_revision": ARCH_REVISION,
        "module": MODULE,
        "run": run,
        "outer_fold": outer_fold,
        "seed": SEED,
        "loss": {"name": "bce_dice", "bce_weight": 0.5, "dice_weight": 0.5, "dice_epsilon": 1e-6},
        "optimizer": {"name": "AdamW", "lr": LR, "weight_decay": WEIGHT_DECAY},
        "scheduler": {"name": "CosineAnnealingLR", "T_max": T_MAX},
        "batch_size": BATCH,
        "max_epochs": MAX_EPOCHS,
        "early_stopping_patience": PATIENCE,
        "amp": amp,
        "checkpoint_selection": SELECTION_RULE,
        "checkpoint_selection_secondary": "EARLY_STOP Dice (diagnostic only)",
        "epochs_target": epochs_target,
        "early_stopping": early_stopping,
        "fit_manifest": str(manifest_csv.relative_to(ROOT)),
        "fit_manifest_sha256": fit_manifest_sha,
        "early_stop_manifest_sha256": es_manifest_sha,
        "bindings": bind,
        "test_reads": 0,
    }
    _atomic_write_text(json.dumps(config, indent=1) + "\n", exp_dir / "config.json")

    def save_ckpt(path: Path, epoch: int, is_best: bool) -> None:
        _atomic_torch_save({
            "phase": "25A",
            "method": METHOD,
            "architecture_revision": ARCH_REVISION,
            "module": MODULE,
            "seed": SEED,
            "epoch": epoch,
            "outer_fold": outer_fold,
            "run": run,
            "model_state": model.state_dict(),
            "optimizer_state": optimizer.state_dict(),
            "scheduler_state": scheduler.state_dict(),
            "grad_scaler_state": scaler.state_dict(),
            "best_loss": best_loss,
            "best_epoch": best_epoch,
            "bad_epochs": bad_epochs,
            "resume_count": resume_count,
            "checkpoint_events": checkpoint_events,
            "history": history,
            "selection_rule": SELECTION_RULE,
            "is_best": is_best,
            "parameter_count": n_params,
            "architecture_id": BARR_REFINER_ARCHITECTURE_ID,
            "bindings": bind,
            "random_state": {
                "python": random.getstate(),
                "numpy": np.random.get_state(),
                "torch_cpu": torch.get_rng_state(),
                "torch_cuda": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None,
            },
            "pytorch_version": torch.__version__,
        }, path)

    # ---- training loop ---------------------------------------------------- #
    log(f"training loop: epochs {start_epoch}..{epochs_target - 1} "
        f"({epochs_target} target), steps/epoch={len(train_loader)}")
    for epoch in range(start_epoch, epochs_target):
        t_ep = time.time()
        ds_train.set_epoch(epoch)
        model.train()
        run_loss = run_bce = run_dice = 0.0
        n_seen = 0
        nonfinite_grads = 0
        for batch in train_loader:
            inputs = batch["input"].to(device, non_blocking=True)
            targets = batch["target"].to(device, non_blocking=True)
            optimizer.zero_grad(set_to_none=True)
            with torch.amp.autocast(device_type=device.type, enabled=amp):
                logits = model(inputs)
                b = bce(logits.float(), targets)
                d = dice_loss_fn(logits.float(), targets)
                loss = 0.5 * b + 0.5 * d
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            gn = torch.nn.utils.clip_grad_norm_(model.parameters(), float("inf"))
            if not torch.isfinite(gn):
                nonfinite_grads += 1
            scaler.step(optimizer)
            scaler.update()
            bs = inputs.shape[0]
            run_loss += float(loss.item()) * bs
            run_bce += float(b.item()) * bs
            run_dice += float(d.item()) * bs
            n_seen += bs
        train_loss = run_loss / max(n_seen, 1)
        train_bce = run_bce / max(n_seen, 1)
        train_dice_loss = run_dice / max(n_seen, 1)
        lr_now = float(optimizer.param_groups[0]["lr"])
        scheduler.step()

        es_loss = float("nan")
        es_dice = float("nan")
        is_best = False
        if early_stopping:
            model.eval()
            tot = 0.0
            n_es = 0
            dice_accum = []
            with torch.no_grad():
                for batch in es_loader:
                    inputs = batch["input"].to(device, non_blocking=True)
                    targets = batch["target"].to(device, non_blocking=True)
                    with torch.amp.autocast(device_type=device.type, enabled=amp):
                        logits = model(inputs)
                        l = 0.5 * bce(logits.float(), targets) + 0.5 * dice_loss_fn(
                            logits.float(), targets)
                    tot += float(l.item()) * inputs.shape[0]
                    n_es += inputs.shape[0]
                    dice_accum.append(dice_score_from_logits(logits.float(), targets))
            es_loss = tot / max(n_es, 1)
            es_dice = float(np.mean(dice_accum)) if dice_accum else float("nan")
            if es_loss < best_loss - 1e-12:
                best_loss = es_loss
                best_epoch = epoch
                bad_epochs = 0
                is_best = True
                checkpoint_events += 1
            else:
                bad_epochs += 1

        row = {
            "run": run,
            "epoch": epoch,
            "train_loss": train_loss,
            "train_BCE": train_bce,
            "train_Dice_loss": train_dice_loss,
            "early_stop_loss": es_loss,
            "early_stop_Dice": es_dice,
            "learning_rate": lr_now,
            "elapsed_seconds": round(time.time() - t_ep, 3),
            "amp": bool(amp),
            "checkpoint_event": bool(is_best),
            "best_epoch_so_far": best_epoch,
            "best_early_stop_loss_so_far": best_loss if early_stopping else "",
            "nonfinite_gradient_batches": nonfinite_grads,
            "resume_count": resume_count,
        }
        # ORDER MATTERS: the history row is appended and persisted BEFORE the
        # checkpoint is written. A checkpoint therefore always carries a history
        # covering epochs 0..epoch, so resuming yields contiguous epoch numbering
        # with no gap. (The reverse order leaves a one-epoch hole on resume.)
        history.append(row)
        _atomic_write_text(pd.DataFrame(history).to_csv(index=False), history_path)

        if is_best:
            save_ckpt(ckpt_dir / "best.pt", epoch, True)
        save_ckpt(latest, epoch, is_best)
        log(f"epoch {epoch:3d} train={train_loss:.5f} bce={train_bce:.5f} "
            f"diceL={train_dice_loss:.5f} es={es_loss:.5f} esDice={es_dice:.4f} "
            f"lr={lr_now:.3e} best={is_best} bad={bad_epochs}")

        if early_stopping and bad_epochs >= PATIENCE:
            stop_reason = f"early_stopping_patience_{PATIENCE}"
            log(f"early stopping at epoch {epoch} (best epoch {best_epoch}, "
                f"best EARLY_STOP loss {best_loss:.6f})")
            break
    else:
        stop_reason = "max_epochs_reached"

    if args.final:
        final_path = ckpt_dir / "final.pt"
        save_ckpt(final_path, epochs_target - 1, False)
        log(f"final checkpoint written: {final_path.relative_to(ROOT)}")

    _atomic_write_text(pd.DataFrame(history).to_csv(index=False), history_path)
    ckpt_shas = {p.name: sha(p) for p in sorted(ckpt_dir.glob("*.pt"))}
    run_record = {
        "run": run,
        "outer_fold": outer_fold,
        "classification": "CANONICAL_PHASE25A" if "roi030" in str(CACHE) else
                          "NONCANONICAL_PROTOCOL_DEVIATION__ROI_THRESHOLD_0P50",
        "cache_root": str(CACHE.relative_to(ROOT)) if CACHE.is_relative_to(ROOT) else str(CACHE),
        "roi_proposal_threshold": float(ROI_PROPOSAL_THRESHOLD),
        "segmentation_output_threshold": float(SEGMENTATION_OUTPUT_THRESHOLD),
        "n_fit_action_available": int(len(ds_train)),
        "n_early_stop_action_available": int(len(ds_es)) if ds_es is not None else 0,
        "epochs_completed": len(history),
        "epochs_target": epochs_target,
        "best_epoch": best_epoch,
        "best_early_stop_loss": best_loss if early_stopping else None,
        "final_train_loss": history[-1]["train_loss"] if history else None,
        "stop_reason": stop_reason,
        "resume_count": resume_count,
        "checkpoint_events": checkpoint_events,
        "checkpoint_sha256": ckpt_shas,
        "history_sha256": sha(history_path),
        "parameter_count": n_params,
        "bindings": bind,
        "seed": SEED,
        "test_reads": 0,
    }
    _atomic_write_text(json.dumps(run_record, indent=1) + "\n", exp_dir / "run.json")
    log(f"DONE run={run} epochs={len(history)} best_epoch={best_epoch} "
        f"best_es_loss={best_loss if early_stopping else float('nan'):.6f} "
        f"stop={stop_reason} checkpoints={list(ckpt_shas)}")
    print(f"PHASE25A_RUN_COMPLETE {run}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
