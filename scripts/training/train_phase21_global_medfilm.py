"""Phase 21 — GLOBAL MedFiLM four-domain training (ONE logical run, seed 42).

Experiment: phase21_global_medfilm_fourdomain_seed42_clean_v3

Task-conditioned GLOBAL reference: ONE shared network, task embedding + FiLM
(5 sites), ONE shared foreground head. task_id is the ONLY task signal.

NO regional refinement, NO benefit routing, NO ROI proposal, NO localizer, NO
compression, NO architecture search, NO TEST evaluation.

Scientific values are INHERITED from the frozen Phase-20 protocol
(reports/audits/phase20_shared_global_baseline_protocol.json, SHA b74f1f9f...).
See reports/audits/phase21_protocol_binding.json (unintentional_differences=[]).

Execution-mechanism notes (no scientific effect)
------------------------------------------------
* ``--resume`` continues the SAME logical run from ``latest.pt``. It never starts
  a second independent run.
* Resume is bit-exact BY CONSTRUCTION: the data order and every stochastic
  augmentation for epoch k derive from ``derive_epoch_seed(SEED, k)``.
* ``history.csv`` is flushed after EVERY epoch and checkpoints are written every
  epoch, so an externally terminated process still leaves a complete record.
"""
from __future__ import annotations

import argparse
import json
import platform
import random
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from scripts.training.phase21_common import (
    ARCHITECTURE_ID,
    CKPT_DIR,
    CONFIG,
    EXPERIMENT_ID,
    EXP_DIR,
    HISTORY_JSON_PATH,
    HISTORY_PATH,
    MANIFEST_DIR,
    MANIFEST_VERSION,
    PHASE,
    PROTOCOL_PATH,
    PROTOCOL_SHA256,
    per_image_dice_iou_precision_recall,
    sha256_file,
    validate,
)
from src.data.domain_balanced_sampler import (
    BALANCED_SAMPLING_POLICY_ID,
    build_domain_balanced_sampler,
    derive_epoch_seed,
    expected_domain_proportions,
)
from src.data.loaders import create_loader
from src.data.multidomain_dataset import DATASET_ORDER, MultiDomainDataset, harmonized_collate
from src.losses.segmentation import BCEDiceLoss
from src.models.film import GlobalMedFiLM
from src.training.phase20_selection import (
    SELECTION_RULE_ID,
    DOMAIN_ORDER as SEL_DOMAIN_ORDER,
    is_new_best,
    macro_domain_dice,
)
from src.utils.device import get_device
from src.utils.run_lock import acquire_lock, release_lock
from src.utils.test_lock import verify_test_lock

AUDIT_DIR = ROOT / "reports" / "audits"


def main() -> int:
    ap = argparse.ArgumentParser(description="Phase-21 Global MedFiLM four-domain run.")
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

    # --- governance preflight ------------------------------------------------ #
    verify_test_lock(str(ROOT))
    log("TEST lock verified (manifests/test.csv sha256 matches the frozen lock)")
    lock = acquire_lock(EXP_DIR, EXPERIMENT_ID, recover_stale=args.recover_stale_lock)
    log(f"run lock acquired pid={lock['pid']} host={lock['host']}")

    proto_sha = sha256_file(ROOT / PROTOCOL_PATH)
    if proto_sha != PROTOCOL_SHA256:
        log(f"FAIL-CLOSED: frozen protocol SHA drift {proto_sha} != {PROTOCOL_SHA256}")
        release_lock(EXP_DIR)
        return 2
    log(f"frozen Phase-20 protocol SHA verified {proto_sha[:16]}...")

    for name in ("phase21_protocol_binding.json", "phase21_global_medfilm_architecture_binding.json",
                 "phase21_pre_execution_check.json"):
        p = AUDIT_DIR / name
        if not p.exists():
            log(f"FAIL-CLOSED: required audit artifact missing: {name}")
            release_lock(EXP_DIR)
            return 2
    binding = json.loads((AUDIT_DIR / "phase21_global_medfilm_architecture_binding.json")
                         .read_text(encoding="utf-8"))
    if binding.get("verdict") != "PHASE21_ARCHITECTURE_FROZEN":
        log("FAIL-CLOSED: architecture is not frozen")
        release_lock(EXP_DIR)
        return 2
    pec = json.loads((AUDIT_DIR / "phase21_pre_execution_check.json").read_text(encoding="utf-8"))
    if not pec.get("training_may_start"):
        log("FAIL-CLOSED: pre-execution check did not authorize training")
        release_lock(EXP_DIR)
        return 2
    log("governance preflight OK (protocol binding + architecture freeze + pre-execution check)")

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

    ds_train = MultiDomainDataset(MANIFEST_DIR / "train.csv", "TRAIN",
                                  size=CONFIG["input_resolution"], train=True,
                                  channel_policy=CONFIG["input_channel_policy"])
    ds_val = MultiDomainDataset(MANIFEST_DIR / "val.csv", "VAL",
                                size=CONFIG["input_resolution"], train=False,
                                channel_policy=CONFIG["input_channel_policy"])
    assert len(ds_train) == 5832 and len(ds_val) == 808, "population mismatch"
    log(f"TRAIN={len(ds_train)} VAL={len(ds_val)} train_domains={ds_train.class_distribution()}")
    log(f"sampling policy={BALANCED_SAMPLING_POLICY_ID} "
        f"expected={expected_domain_proportions(ds_train.frame['dataset'].tolist())}")

    model = GlobalMedFiLM(
        task_count=CONFIG["model"]["task_count"],
        in_channels=CONFIG["model"]["in_channels"],
        out_channels=CONFIG["model"]["out_channels"],
        channels=tuple(CONFIG["model"]["channels"]),
        task_embedding_dim=CONFIG["model"]["task_embedding_dim"],
        film_hidden_dim=CONFIG["model"]["film_hidden_dim"],
    ).to(device)
    n_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    log(f"model=GlobalMedFiLM params={n_params:,} "
        f"(ONE shared parameter set; task conditioning via FiLM only)")
    assert model.medfilm_components_present is True, "FiLM components missing"
    assert not any(k in n.lower() for n, _ in model.named_modules()
                   for k in ("localizer", "proposal", "roi", "regional", "refiner", "router")), \
        "forbidden module detected"

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

    # ---- run manifest (written once, before the loop) --------------------- #
    env = {
        "python": sys.version,
        "platform": platform.platform(),
        "torch": torch.__version__,
        "cuda": torch.version.cuda,
        "cudnn": torch.backends.cudnn.version(),
        "device": str(device),
        "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "gpu_total_memory_bytes": (torch.cuda.get_device_properties(0).total_memory
                                   if torch.cuda.is_available() else None),
        "numpy": np.__version__,
        "pandas": pd.__version__,
    }
    code_shas = {
        "scripts/training/train_phase21_global_medfilm.py": sha256_file(Path(__file__).resolve()),
        "scripts/training/phase21_common.py": sha256_file(ROOT / "scripts/training/phase21_common.py"),
        "src/models/film/global_medfilm.py": sha256_file(ROOT / "src/models/film/global_medfilm.py"),
        "src/models/film/__init__.py": sha256_file(ROOT / "src/models/film/__init__.py"),
        "src/models/factory.py": sha256_file(ROOT / "src/models/factory.py"),
    }
    run_manifest = {
        "artifact": "phase21_run_manifest",
        "experiment_id": EXPERIMENT_ID,
        "phase": PHASE,
        "architecture_id": ARCHITECTURE_ID,
        "manifest_version": MANIFEST_VERSION,
        "dataset_populations": {
            "TRAIN": ds_train.class_distribution(),
            "VAL": ds_val.class_distribution(),
            "TRAIN_total": len(ds_train),
            "VAL_total": len(ds_val),
            "task_ids": {"ISIC": 0, "BUSI": 1, "KVASIR": 2, "KUB": 3},
        },
        "frozen_protocol": {"path": PROTOCOL_PATH, "sha256": proto_sha},
        "binding_artifacts": {
            "protocol_binding": "reports/audits/phase21_protocol_binding.json",
            "protocol_binding_sha256": sha256_file(AUDIT_DIR / "phase21_protocol_binding.json"),
            "architecture_binding": "reports/audits/phase21_global_medfilm_architecture_binding.json",
            "architecture_binding_sha256": sha256_file(
                AUDIT_DIR / "phase21_global_medfilm_architecture_binding.json"),
            "entry_gate": "reports/audits/phase21_entry_gate.json",
            "entry_gate_sha256": sha256_file(AUDIT_DIR / "phase21_entry_gate.json"),
            "pre_execution_check": "reports/audits/phase21_pre_execution_check.json",
            "pre_execution_check_sha256": sha256_file(AUDIT_DIR / "phase21_pre_execution_check.json"),
        },
        "code_shas": code_shas,
        "environment": env,
        "configuration": CONFIG,
        "model_params": n_params,
        "run_started_utc": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
        "test_reads": 0,
    }
    (EXP_DIR / "run_manifest.json").write_text(json.dumps(run_manifest, indent=2), encoding="utf-8")
    (EXP_DIR / "config.json").write_text(json.dumps(CONFIG, indent=2), encoding="utf-8")

    best_macro, best_epoch, best_val_loss, bad_epochs = float("-inf"), 0, float("inf"), 0
    history: list = []
    start_epoch = 1
    resume_source = None
    resume_events: list = []
    prior_cumulative = 0.0

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
        prior_cumulative = float(history[-1]["cumulative_seconds"]) if history else 0.0
        resume_events = ck.get("resume_events", []) + [
            {"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "resumed_from_epoch": int(ck["epoch"])}]
        log(f"RESUME from {resume_source} at epoch {ck['epoch']} -> next {start_epoch} "
            f"best_macro={best_macro:.6f} best_epoch={best_epoch} bad={bad_epochs} "
            f"history_rows={len(history)}")
    elif args.resume:
        log("RESUME requested but no latest.pt found; starting from epoch 1")

    max_epochs = int(args.max_epochs or CONFIG["training"]["max_epochs"])
    log(f"RUN START experiment={EXPERIMENT_ID} seed={seed} start_epoch={start_epoch} "
        f"max_epochs={max_epochs} patience={patience}")

    stop_reason = None
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
            task_ids = batch["task_id"].to(device, non_blocking=True)
            with torch.amp.autocast(device_type=device.type, enabled=amp):
                logits = model(images, task_ids)
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
            "best_so_far": best_macro,
            "bad_epochs": bad_epochs,
            "epoch_seconds": elapsed,
            "cumulative_seconds": prior_cumulative + time.time() - run_start,
        }
        history.append(row)
        pd.DataFrame(history).to_csv(HISTORY_PATH, index=False)
        HISTORY_JSON_PATH.write_text(json.dumps(history, indent=2), encoding="utf-8")

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
        torch.save(ckpt, CKPT_DIR / "last.pt")
        if new_best:
            torch.save(ckpt, CKPT_DIR / "best.pt")

        (EXP_DIR / "training_state.json").write_text(json.dumps({
            "artifact": "phase21_training_state",
            "experiment_id": EXPERIMENT_ID,
            "epoch": epoch,
            "best_epoch": best_epoch,
            "best_macro_domain_dice": best_macro,
            "best_val_loss": best_val_loss,
            "bad_epochs": bad_epochs,
            "early_stopping_patience": patience,
            "history_rows": len(history),
            "resume_count": len(resume_events),
            "cumulative_seconds": prior_cumulative + time.time() - run_start,
            "stop_reason": None,
            "updated_utc": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
        }, indent=2), encoding="utf-8")

        log(f"EPOCH {epoch:03d} train_loss={train_loss:.4f} val_loss={val_loss:.4f} "
            f"macro={macro:.6f} ISIC={per_domain['ISIC']['dice']:.4f} BUSI={per_domain['BUSI']['dice']:.4f} "
            f"KVASIR={per_domain['KVASIR']['dice']:.4f} KUB={per_domain['KUB']['dice']:.4f} "
            f"lr={optimizer.param_groups[0]['lr']:.3e} best_ep={best_epoch} bad={bad_epochs} "
            f"new_best={new_best} {elapsed:.1f}s")

        if bad_epochs >= patience:
            stop_reason = "EARLY_STOPPING_PATIENCE"
            log(f"EARLY STOPPING at epoch {epoch} (patience={patience})")
            break

    final_epoch = int(history[-1]["epoch"])
    stop_reason = stop_reason or "MAX_EPOCHS"
    total_elapsed = prior_cumulative + time.time() - run_start

    # ---- checkpoint-selection replay from DISK (frozen rule) --------------- #
    replay = select_best_from_disk(HISTORY_PATH)
    replay_ok = (replay["best_epoch"] == best_epoch
                 and abs(replay["best_macro_domain_dice"] - best_macro) < 1e-12)
    (EXP_DIR / "phase21_checkpoint_selection_replay.json").write_text(json.dumps({
        "artifact": "phase21_checkpoint_selection_replay",
        "experiment_id": EXPERIMENT_ID,
        "selection_rule_id": SELECTION_RULE_ID,
        "source": "experiments/%s/history.csv (disk only, no model re-evaluation)" % EXPERIMENT_ID,
        "history_sha256": sha256_file(HISTORY_PATH),
        "replayed_best_epoch": replay["best_epoch"],
        "replayed_best_macro_domain_dice": replay["best_macro_domain_dice"],
        "training_best_epoch": best_epoch,
        "training_best_macro_domain_dice": best_macro,
        "replay_matches_training": bool(replay_ok),
        "verdict": "PHASE21_CHECKPOINT_SELECTION_REPLAY_PASS" if replay_ok
                   else "PHASE21_CHECKPOINT_SELECTION_REPLAY_FAIL",
        "test_reads": 0,
    }, indent=2), encoding="utf-8")
    log(f"checkpoint-selection replay best_epoch={replay['best_epoch']} "
        f"macro={replay['best_macro_domain_dice']:.6f} matches={replay_ok}")

    closure = {
        "artifact": "phase21_training_closure",
        "experiment_id": EXPERIMENT_ID,
        "phase": PHASE,
        "manifest_version": MANIFEST_VERSION,
        "architecture_id": ARCHITECTURE_ID,
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
        "history_path": f"experiments/{EXPERIMENT_ID}/history.csv",
        "history_sha256": sha256_file(HISTORY_PATH),
        "best_checkpoint_sha256": sha256_file(CKPT_DIR / "best.pt"),
        "last_checkpoint_sha256": sha256_file(CKPT_DIR / "last.pt"),
        "trainer_path": "scripts/training/train_phase21_global_medfilm.py",
        "trainer_sha256": sha256_file(Path(__file__).resolve()),
        "model_file_sha256": sha256_file(ROOT / "src/models/film/global_medfilm.py"),
        "frozen_protocol_sha256": proto_sha,
        "resume_events": resume_events,
        "resume_count": len(resume_events),
        "independent_duplicate_runs": 0,
        "test_reads": {"test_image_reads": 0, "test_mask_reads": 0,
                       "test_inference": 0, "test_visualization": 0},
        "training_performed": True,
        "model_params": n_params,
        "total_elapsed_seconds": total_elapsed,
        "checkpoint_selection_replay_verdict": (
            "PHASE21_CHECKPOINT_SELECTION_REPLAY_PASS" if replay_ok
            else "PHASE21_CHECKPOINT_SELECTION_REPLAY_FAIL"),
        "configuration": CONFIG,
    }
    (EXP_DIR / "closure.json").write_text(json.dumps(closure, indent=2), encoding="utf-8")
    (EXP_DIR / "phase21_training_closure.json").write_text(json.dumps(closure, indent=2),
                                                           encoding="utf-8")
    (EXP_DIR / "training_state.json").write_text(json.dumps({
        "artifact": "phase21_training_state",
        "experiment_id": EXPERIMENT_ID,
        "epoch": final_epoch,
        "best_epoch": best_epoch,
        "best_macro_domain_dice": best_macro,
        "best_val_loss": best_val_loss,
        "bad_epochs": bad_epochs,
        "early_stopping_patience": patience,
        "history_rows": len(history),
        "resume_count": len(resume_events),
        "cumulative_seconds": total_elapsed,
        "stop_reason": stop_reason,
        "updated_utc": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
    }, indent=2), encoding="utf-8")

    log(f"TRAINING COMPLETE best_epoch={best_epoch} best_macro={best_macro:.6f} "
        f"final_epoch={final_epoch} stop_reason={stop_reason}")
    release_lock(EXP_DIR)
    run_log.close()
    return 0


def select_best_from_disk(history_path: Path) -> dict:
    """Disk-only replay of the frozen selection rule (no model, no inference)."""
    from src.training.phase20_selection import select_best_epoch
    df = pd.read_csv(history_path)
    result = select_best_epoch(df.to_dict("records"))
    return {"best_epoch": int(result["selected_epoch"]),
            "best_macro_domain_dice": float(result["selected_macro_domain_dice"]),
            "n_epochs_evaluated": int(result["n_epochs_evaluated"]),
            "n_improvements": int(result["n_improvements"])}


if __name__ == "__main__":
    raise SystemExit(main())
