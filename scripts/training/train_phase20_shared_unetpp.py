"""Phase 20 - SHARED FOUR-DOMAIN GLOBAL BASELINE (single frozen UNet++).

Experiment: phase20_shared_unetpp_fourdomain_seed42_clean_v3

NO FiLM. NO task conditioning as model input. NO regional mechanism, no
localizer, no proposal, no ROI, no dataset-specific head. ONE shared parameter
set across ISIC / BUSI / KVASIR / KUB.

Protocol: reports/audits/phase20_shared_global_baseline_protocol.json
Architecture freeze: reports/audits/phase20_baseline_architecture_freeze.json

Execution-mechanism notes (no scientific effect)
------------------------------------------------
* ``--resume`` continues the SAME logical run from ``latest.pt``. It never starts
  a second independent run.
* Resume is bit-exact BY CONSTRUCTION: the data order and every stochastic
  augmentation for epoch k derive from ``derive_epoch_seed(SEED, k)``, so epoch k
  is a pure function of (SEED, k) and does not depend on how many epochs ran
  before it. Workers are re-created each epoch (persistent_workers=False) so no
  worker RNG state leaks across epochs.
* ``history.csv`` is flushed after EVERY epoch and checkpoints are written every
  epoch, so an externally terminated process still leaves a complete record.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.data.domain_balanced_sampler import (
    BALANCED_SAMPLING_POLICY_ID,
    build_domain_balanced_sampler,
    derive_epoch_seed,
    expected_domain_proportions,
)
from src.data.loaders import create_loader
from src.data.multidomain_dataset import DATASET_ORDER, MultiDomainDataset, harmonized_collate
from src.losses.segmentation import BCEDiceLoss
from src.models.unetpp import UNetPlusPlus
from src.training.phase20_selection import (
    SELECTION_RULE_ID,
    DOMAIN_ORDER as SEL_DOMAIN_ORDER,
    is_new_best,
    macro_domain_dice,
)
from src.utils.device import get_device
from src.utils.run_lock import acquire_lock, release_lock
from src.utils.test_lock import verify_test_lock

# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "phase20_shared_unetpp_fourdomain_seed42_clean_v3"
PHASE = 20
MANIFEST_VERSION = "phase4_v3"
MANIFEST_DIR = ROOT / "manifests/phase4_v3"

CONFIG = {
    "experiment_id": EXPERIMENT_ID,
    "phase": PHASE,
    "manifest_version": MANIFEST_VERSION,
    "dataset": "MULTI_DOMAIN_ISIC_BUSI_KVASIR_KUB",
    "architecture": "unetpp_nested_4_level_no_deep_supervision_base32",
    "model": {"name": "UNetPlusPlus", "in_channels": 3, "out_channels": 1, "base_channels": 32},
    "input_channel_policy": "RGB_3CH",
    "input_resolution": 512,
    "loss": {"name": "bce_dice", "bce_weight": 0.5, "dice_weight": 0.5, "dice_epsilon": 1e-6},
    "optimizer": {"name": "AdamW", "learning_rate": 1e-4, "weight_decay": 1e-4},
    "scheduler": {"name": "CosineAnnealingLR", "T_max": 100, "step": "per_epoch_after_train_and_val"},
    "training": {
        "batch_size": 4, "eval_batch_size": 8, "num_workers": 4,
        "persistent_workers": False, "max_epochs": 100, "early_stopping_patience": 15,
        "amp": True, "seed": 42, "gradient_accumulation_steps": 1,
        "effective_batch_size": 4, "threshold": 0.5,
        "sampling_policy": BALANCED_SAMPLING_POLICY_ID,
        "checkpoint_metric": SELECTION_RULE_ID,
        "checkpoint_metric_description": "macro-domain mean VAL Dice "
                                          "(unweighted mean of the four per-domain per-image macro Dice)",
        "tie_break": "lower validation loss",
    },
    "augmentation_policy": "src.data.transforms.SegmentationTransform(train=True): horizontal mirror p=0.5, "
                           "rotation +/-5 deg, brightness +/-0.10, contrast +/-0.10; mask NEAREST; VAL disabled",
    "governance": {"allow_test": False, "allow_external": False,
                   "task_id_as_model_input": False, "film": False, "regional_module": False,
                   "localizer": False, "roi_proposal": False},
    "taxonomy_id": None,
}

CKPT_DIR = ROOT / "checkpoints" / EXPERIMENT_ID
EXP_DIR = ROOT / "experiments" / EXPERIMENT_ID
HISTORY_PATH = EXP_DIR / "history.csv"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# --------------------------------------------------------------------------- #
def per_image_dice_iou_precision_recall(logits: torch.Tensor, masks: torch.Tensor,
                                        threshold: float, eps: float = 1e-7):
    """Per-image binary metrics, computed one image at a time. Returns dict of tensors."""
    preds = torch.sigmoid(logits).ge(threshold)
    tgts = masks.bool()
    dims = tuple(range(1, tgts.ndim))
    tp = (preds & tgts).sum(dims).float()
    fp = (preds & ~tgts).sum(dims).float()
    fn = (~preds & tgts).sum(dims).float()
    return {
        "dice": (2 * tp + eps) / (2 * tp + fp + fn + eps),
        "iou": (tp + eps) / (tp + fp + fn + eps),
        "precision": (tp + eps) / (tp + fp + eps),
        "recall": (tp + eps) / (tp + fn + eps),
    }


@torch.no_grad()
def validate(model, loader, criterion, device, threshold, amp):
    """Deterministic VAL pass; returns overall loss plus per-domain macro metrics."""
    model.eval()
    losses = []
    acc = {d: {k: [] for k in ("dice", "iou", "precision", "recall")} for d in DATASET_ORDER}
    for batch in loader:
        images = batch["image"].to(device, non_blocking=True)
        masks = batch["mask"].to(device, non_blocking=True)
        datasets = batch["dataset"]
        # GOVERNANCE: only the image reaches the model. task_id is never an input.
        with torch.amp.autocast(device_type=device.type, enabled=amp):
            logits = model(images)
            loss = criterion(logits, masks)
        losses.append(float(loss.item()))
        m = per_image_dice_iou_precision_recall(logits, masks, threshold)
        for key, tensor in m.items():
            values = tensor.detach().cpu().numpy()
            for i, ds in enumerate(datasets):
                acc[str(ds)][key].append(float(values[i]))
    out = {d: {k: float(np.mean(v)) if v else float("nan") for k, v in acc[d].items()}
           for d in DATASET_ORDER}
    return float(np.mean(losses)), out


def main() -> int:
    ap = argparse.ArgumentParser(description="Phase-20 shared four-domain UNet++ baseline.")
    ap.add_argument("--resume", action="store_true",
                    help="Resume the SAME logical run from latest.pt (bit-exact by construction).")
    ap.add_argument("--recover-stale-lock", action="store_true")
    ap.add_argument("--max-epochs", type=int, default=None,
                    help="Operational override for the run loop bound; scientific config unchanged.")
    args = ap.parse_args()

    CKPT_DIR.mkdir(parents=True, exist_ok=True)
    EXP_DIR.mkdir(parents=True, exist_ok=True)
    (ROOT / "logs").mkdir(parents=True, exist_ok=True)

    run_log_path = ROOT / "logs" / f"{EXPERIMENT_ID}.run.log"
    run_log = open(run_log_path, "a", encoding="utf-8", buffering=1)
    run_start = time.time()

    def log(msg: str) -> None:
        line = f"[{time.strftime('%Y-%m-%dT%H:%M:%S')}] +{time.time()-run_start:9.1f}s {msg}"
        print(line, flush=True)
        run_log.write(line + "\n")
        run_log.flush()

    # --- governance preflight ------------------------------------------------
    verify_test_lock(str(ROOT))
    log("TEST lock verified (manifests/test.csv sha256 matches the frozen lock)")
    lock = acquire_lock(EXP_DIR, EXPERIMENT_ID, recover_stale=args.recover_stale_lock)
    log(f"run lock acquired pid={lock['pid']} host={lock['host']}")

    seed = int(CONFIG["training"]["seed"])
    torch.manual_seed(seed)
    np.random.seed(seed)
    random.seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

    device = get_device(require_cuda=True)
    log(f"device={device} torch={torch.__version__} cudnn_deterministic=True")

    ds_train = MultiDomainDataset(MANIFEST_DIR / "train.csv", "TRAIN", size=CONFIG["input_resolution"],
                                  train=True, channel_policy=CONFIG["input_channel_policy"])
    ds_val = MultiDomainDataset(MANIFEST_DIR / "val.csv", "VAL", size=CONFIG["input_resolution"],
                                train=False, channel_policy=CONFIG["input_channel_policy"])
    assert len(ds_train) == 5832 and len(ds_val) == 808, "population mismatch"
    log(f"TRAIN={len(ds_train)} VAL={len(ds_val)} train_domains={ds_train.class_distribution()}")
    log(f"sampling policy={BALANCED_SAMPLING_POLICY_ID} expected={expected_domain_proportions(ds_train.frame['dataset'].tolist())}")

    model = UNetPlusPlus(in_channels=CONFIG["model"]["in_channels"],
                         out_channels=CONFIG["model"]["out_channels"],
                         base_channels=CONFIG["model"]["base_channels"]).to(device)
    n_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    log(f"model=UNetPlusPlus params={n_params:,} (one shared parameter set across all four domains)")
    assert not any("film" in n.lower() for n, _ in model.named_modules()), "FiLM module detected"
    assert not any(k in n.lower() for n in dict(model.named_modules())
                   for k in ("localizer", "proposal", "roi", "regional")), "forbidden module detected"

    criterion = BCEDiceLoss(CONFIG["loss"]["bce_weight"], CONFIG["loss"]["dice_weight"],
                            CONFIG["loss"]["dice_epsilon"])
    optimizer = torch.optim.AdamW(model.parameters(), lr=CONFIG["optimizer"]["learning_rate"],
                                  weight_decay=CONFIG["optimizer"]["weight_decay"])
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=CONFIG["scheduler"]["T_max"])
    amp = bool(CONFIG["training"]["amp"]) and device.type == "cuda"
    scaler = torch.amp.GradScaler("cuda", enabled=amp)
    threshold = float(CONFIG["training"]["threshold"])
    patience = int(CONFIG["training"]["early_stopping_patience"])

    best_macro, best_epoch, best_val_loss, bad_epochs = float("-inf"), 0, float("inf"), 0
    history: list = []
    start_epoch = 1
    resume_source = None
    resume_events: list = []

    if args.resume and (CKPT_DIR / "latest.pt").exists():
        ck = torch.load(CKPT_DIR / "latest.pt", map_location=device, weights_only=False)
        model.load_state_dict(ck["model_state"])
        optimizer.load_state_dict(ck["optimizer_state"])
        scheduler.load_state_dict(ck["scheduler_state"])
        if ck.get("grad_scaler_state"):
            scaler.load_state_dict(ck["grad_scaler_state"])
        best_macro = float(ck["best_macro_domain_dice"])
        best_epoch = int(ck["best_epoch"])
        best_val_loss = float(ck["best_val_loss"])
        bad_epochs = int(ck["bad_epochs"])
        start_epoch = int(ck["epoch"]) + 1
        resume_source = str(CKPT_DIR / "latest.pt")
        if HISTORY_PATH.exists():
            history = pd.read_csv(HISTORY_PATH).to_dict("records")
        resume_events = ck.get("resume_events", []) + [{"at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                                                        "resumed_from_epoch": int(ck["epoch"])}]
        log(f"RESUME from {resume_source} at epoch {ck['epoch']} -> next {start_epoch} "
            f"best_macro={best_macro:.6f} best_epoch={best_epoch} bad={bad_epochs} "
            f"history_rows={len(history)}")
        log("resume is bit-exact by construction (per-epoch deterministic seeding)")
    elif args.resume:
        log("RESUME requested but no latest.pt found; starting from epoch 1")

    max_epochs = int(args.max_epochs or CONFIG["training"]["max_epochs"])
    log(f"RUN START experiment={EXPERIMENT_ID} seed={seed} start_epoch={start_epoch} "
        f"max_epochs={max_epochs} patience={patience}")

    for epoch in range(start_epoch, max_epochs + 1):
        t0 = time.perf_counter()
        ep_seed = derive_epoch_seed(seed, epoch)
        torch.manual_seed(ep_seed)
        np.random.seed(ep_seed)
        random.seed(ep_seed)

        sampler = build_domain_balanced_sampler(ds_train.frame["dataset"].tolist(), seed, epoch)
        loader_train = create_loader(ds_train, batch_size=CONFIG["training"]["batch_size"],
                                     shuffle=False, seed=ep_seed,
                                     num_workers=CONFIG["training"]["num_workers"],
                                     persistent_workers=CONFIG["training"]["persistent_workers"],
                                     collate_fn=harmonized_collate, sampler=sampler)
        loader_val = create_loader(ds_val, batch_size=CONFIG["training"]["eval_batch_size"],
                                   shuffle=False, seed=seed, num_workers=2,
                                   collate_fn=harmonized_collate)

        model.train()
        optimizer.zero_grad(set_to_none=True)
        train_losses = []
        for batch in loader_train:
            images = batch["image"].to(device, non_blocking=True)
            masks = batch["mask"].to(device, non_blocking=True)
            with torch.amp.autocast(device_type=device.type, enabled=amp):
                logits = model(images)
                loss = criterion(logits, masks)
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            optimizer.zero_grad(set_to_none=True)
            train_losses.append(float(loss.item()))
        train_loss = float(np.mean(train_losses))

        val_loss, per_domain = validate(model, loader_val, criterion, device, threshold, amp)
        scheduler.step()
        elapsed = time.perf_counter() - t0

        macro = macro_domain_dice({d: per_domain[d]["dice"] for d in SEL_DOMAIN_ORDER})
        new_best = is_new_best(macro, val_loss, best_macro, best_val_loss)
        if new_best:
            best_macro, best_epoch, best_val_loss, bad_epochs = macro, epoch, val_loss, 0
        else:
            bad_epochs += 1

        row = {
            "epoch": epoch,
            "train_loss": train_loss,
            "val_loss": val_loss,
            "macro_domain_dice": macro,
            **{f"val_dice_{d}": per_domain[d]["dice"] for d in DATASET_ORDER},
            **{f"val_iou_{d}": per_domain[d]["iou"] for d in DATASET_ORDER},
            **{f"val_precision_{d}": per_domain[d]["precision"] for d in DATASET_ORDER},
            **{f"val_recall_{d}": per_domain[d]["recall"] for d in DATASET_ORDER},
            "learning_rate": optimizer.param_groups[0]["lr"],
            "is_new_best": bool(new_best),
            "best_epoch_so_far": best_epoch,
            "bad_epochs": bad_epochs,
            "epoch_seconds": elapsed,
            "cumulative_seconds": time.time() - run_start,
        }
        history.append(row)
        pd.DataFrame(history).to_csv(HISTORY_PATH, index=False)

        ckpt = {
            "model_state": model.state_dict(),
            "optimizer_state": optimizer.state_dict(),
            "scheduler_state": scheduler.state_dict(),
            "grad_scaler_state": scaler.state_dict(),
            "epoch": epoch,
            "best_macro_domain_dice": best_macro,
            "best_epoch": best_epoch,
            "best_val_loss": best_val_loss,
            "bad_epochs": bad_epochs,
            "configuration": CONFIG,
            "seed": seed,
            "experiment_id": EXPERIMENT_ID,
            "resume_events": resume_events,
            "history_rows": len(history),
        }
        torch.save(ckpt, CKPT_DIR / "latest.pt")
        if new_best:
            torch.save(ckpt, CKPT_DIR / "best.pt")

        log(f"EPOCH {epoch:03d} train_loss={train_loss:.4f} val_loss={val_loss:.4f} "
            f"macro={macro:.6f} ISIC={per_domain['ISIC']['dice']:.4f} BUSI={per_domain['BUSI']['dice']:.4f} "
            f"KVASIR={per_domain['KVASIR']['dice']:.4f} KUB={per_domain['KUB']['dice']:.4f} "
            f"lr={optimizer.param_groups[0]['lr']:.3e} best_ep={best_epoch} bad={bad_epochs} "
            f"new_best={new_best} {elapsed:.1f}s")

        if bad_epochs >= patience:
            log(f"EARLY STOPPING at epoch {epoch} (patience={patience})")
            break

    final_epoch = int(history[-1]["epoch"])
    stop_reason = "EARLY_STOPPING_PATIENCE" if bad_epochs >= patience else "MAX_EPOCHS"
    closure = {
        "artifact": "phase20_training_closure",
        "experiment_id": EXPERIMENT_ID,
        "phase": PHASE,
        "manifest_version": MANIFEST_VERSION,
        "selection_rule_id": SELECTION_RULE_ID,
        "best_epoch": best_epoch,
        "best_macro_domain_dice": best_macro,
        "best_val_loss": best_val_loss,
        "per_domain_dice_at_best": {d: float(history[best_epoch - 1][f"val_dice_{d}"])
                                    for d in DATASET_ORDER},
        "final_epoch": final_epoch,
        "total_completed_epochs": final_epoch,
        "stop_reason": stop_reason,
        "early_stopping_patience": patience,
        "history_path": str(HISTORY_PATH.relative_to(ROOT)).replace("\\", "/"),
        "history_sha256": sha256_file(HISTORY_PATH),
        "best_checkpoint_sha256": sha256_file(CKPT_DIR / "best.pt"),
        "latest_checkpoint_sha256": sha256_file(CKPT_DIR / "latest.pt"),
        "trainer_path": "scripts/training/train_phase20_shared_unetpp.py",
        "trainer_sha256": sha256_file(Path(__file__).resolve()),
        "resume_events": resume_events,
        "resume_count": len(resume_events),
        "independent_duplicate_runs": 0,
        "test_reads": {"test_image_reads": 0, "test_mask_reads": 0,
                       "test_inference": 0, "test_visualization": 0},
        "training_performed": True,
        "model_params": n_params,
        "total_elapsed_seconds": time.time() - run_start,
        "configuration": CONFIG,
    }
    (EXP_DIR / "closure.json").write_text(json.dumps(closure, indent=2), encoding="utf-8")
    (EXP_DIR / "config.json").write_text(json.dumps(CONFIG, indent=2), encoding="utf-8")
    log(f"TRAINING COMPLETE best_epoch={best_epoch} best_macro={best_macro:.6f} "
        f"final_epoch={final_epoch} stop_reason={stop_reason}")
    release_lock(EXP_DIR)
    run_log.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
