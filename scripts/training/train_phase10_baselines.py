"""Phase 10 sequential fair KUB baseline training; TRAIN/VAL only."""
import argparse, datetime, json, math, sys, time
from pathlib import Path
import pandas as pd
import torch
import yaml

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from src.data.kub_dataset import KUBDataset
from src.data.loaders import create_loader
from src.data.transforms import SegmentationTransform
from src.losses.segmentation import BCEDiceLoss
from src.models.factory import create_model
from src.training.trainer import Trainer
from src.utils.checkpointing import load_training_checkpoint, save_training_checkpoint
from src.utils.experiment import register_experiment
from src.utils.manifest_guard import verify_manifests
from src.utils.reproducibility import set_seed
from src.utils.test_lock import verify_test_lock


def load_config():
    return yaml.safe_load((ROOT / "configs/kub/phase10_baselines.yaml").read_text(encoding="utf-8"))


def registry_record(spec, config, batch, accumulation, status, start_time, **updates):
    record = {
        "experiment_id": spec["experiment_id"], "phase": 10, "dataset": "KUB", "split_scope": "TRAIN/VAL",
        "model": spec["key"], "architecture": spec["architecture"], "seed": 42, "image_size": 512,
        "batch_size": batch, "effective_batch_size": batch * accumulation, "optimizer": "AdamW",
        "learning_rate": 1e-4, "weight_decay": 1e-4, "scheduler": "CosineAnnealingLR",
        "loss": "0.5_BCE+0.5_Dice", "threshold": 0.5, "manifest_version": "phase4_v2",
        "status": status, "start_time": start_time, "end_time": "",
        "checkpoint_path": str(ROOT / "checkpoints" / spec["experiment_id"] / "best.pt"),
        "best_val_dice": "", "git_commit": "",
        "notes": "Phase 10 fair baseline; random initialization; no pretrained weights",
    }
    record.update(updates); return record


def attempt_batch_policy(spec, device):
    """Use batch 4 unless a genuine CUDA smoke OOM requires the frozen fallback."""
    for batch, accumulation in ((4, 1), (2, 2), (1, 4)):
        model = create_model(spec["key"], in_channels=1, out_channels=1, base_channels=32).to(device).train()
        criterion = BCEDiceLoss(); optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4, weight_decay=1e-4)
        try:
            optimizer.zero_grad(set_to_none=True)
            sample = torch.rand(batch, 1, 512, 512, device=device); target = torch.zeros_like(sample)
            with torch.amp.autocast("cuda", enabled=True): output = model(sample); loss = criterion(output, target)
            if output.shape != target.shape or not torch.isfinite(output).all() or not torch.isfinite(loss):
                raise RuntimeError("Invalid smoke-test shape or numerical output")
            loss.backward(); optimizer.step()
            del model, optimizer, sample, target, output, loss; torch.cuda.empty_cache()
            return batch, accumulation
        except torch.cuda.OutOfMemoryError:
            del model, optimizer; torch.cuda.empty_cache()
            if batch == 1: raise
    raise RuntimeError("Batch policy exhausted")


def train_model(spec, config):
    verify_manifests(); verify_test_lock(ROOT)
    if not torch.cuda.is_available(): raise RuntimeError("CUDA is required for Phase 10")
    set_seed(42, deterministic=True); device = torch.device("cuda")
    exp_dir = ROOT / "experiments" / spec["experiment_id"]
    checkpoint_dir = ROOT / "checkpoints" / spec["experiment_id"]
    exp_dir.mkdir(parents=True, exist_ok=True); checkpoint_dir.mkdir(parents=True, exist_ok=True)
    metadata = json.loads((ROOT / "manifests/manifest_metadata.json").read_text(encoding="utf-8"))
    latest_path = checkpoint_dir / "latest.pt"
    if latest_path.exists():
        probe = torch.load(latest_path, map_location="cpu", weights_only=False)
        batch = int(probe["configuration"]["runtime"]["physical_batch"])
        accumulation = int(probe["configuration"]["runtime"]["gradient_accumulation_steps"])
    else: batch, accumulation = attempt_batch_policy(spec, device)
    runtime_config = json.loads(json.dumps(config))
    runtime_config["runtime"] = {"physical_batch": batch, "gradient_accumulation_steps": accumulation,
                                 "effective_batch": batch * accumulation}
    started_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    record = registry_record(spec, config, batch, accumulation, "RUNNING", started_utc)
    register_experiment(record, ROOT)

    train_ds = KUBDataset(ROOT / "manifests/train.csv", "TRAIN", SegmentationTransform(512, True),
                          ROOT / "reports/tables/kub_train_samples_sized.csv")
    val_ds = KUBDataset(ROOT / "manifests/val.csv", "VAL", SegmentationTransform(512, False),
                        ROOT / "reports/tables/kub_val_samples_sized.csv")
    model = create_model(spec["key"], in_channels=1, out_channels=1, base_channels=32).to(device)
    parameters = sum(p.numel() for p in model.parameters())
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=100)
    trainer = Trainer(model, optimizer, scheduler, BCEDiceLoss(), device, True, accumulation, 0.5, 15)
    history, best_score, best_epoch, start_epoch, generator_state = [], float("-inf"), -1, 1, None

    if latest_path.exists():
        state = load_training_checkpoint(latest_path, model, optimizer, scheduler, trainer.scaler, True, device)
        if state["manifest_version"] != "phase4_v2" or state["manifest_hashes"] != metadata["hashes"]:
            raise RuntimeError("Checkpoint manifest mismatch")
        history, best_score = state["training_history"], float(state["best_validation_score"])
        start_epoch, trainer.global_step = int(state["epoch"]) + 1, int(state["global_step"])
        early = state.get("early_stopping_state") or {}
        trainer.early_stopping.best = float(early.get("best", best_score))
        trainer.early_stopping.bad_epochs = int(early.get("bad_epochs", 0))
        generator_state = (state.get("loader_generator_states") or {}).get("train")
        best_epoch = int(torch.load(checkpoint_dir / "best.pt", map_location="cpu", weights_only=False)["epoch"])
    train_loader = create_loader(train_ds, batch, True, 42, 0, True, generator_state=generator_state)
    val_loader = create_loader(val_ds, batch, False, 42, 0, True)
    log_path = exp_dir / "training.log"; log = log_path.open("a" if start_epoch > 1 else "w", encoding="utf-8")
    log.write(f"{'Resume' if start_epoch > 1 else 'Start'} UTC={started_utc} epoch={start_epoch} batch={batch} accumulation={accumulation}\n"); log.flush()

    for epoch in range(start_epoch, 101):
        torch.cuda.reset_peak_memory_stats(device); epoch_start = time.perf_counter()
        train_info = trainer.train_one_epoch(train_loader); val_info, _ = trainer.validate(val_loader); scheduler.step()
        values = [train_info["loss"], val_info["loss"], val_info["dice"], val_info["iou"], val_info["precision"], val_info["recall"]]
        if not all(math.isfinite(float(value)) for value in values):
            record.update(status="CHECK_REQUIRED", end_time=datetime.datetime.now(datetime.timezone.utc).isoformat(), notes="NaN/Inf encountered; model stopped")
            register_experiment(record, ROOT); log.close(); raise RuntimeError("NaN/Inf encountered")
        row = {"epoch": epoch, "train_loss": train_info["loss"], "val_loss": val_info["loss"],
               "val_dice": val_info["dice"], "val_iou": val_info["iou"], "val_precision": val_info["precision"],
               "val_recall": val_info["recall"], "learning_rate": optimizer.param_groups[0]["lr"],
               "epoch_seconds": time.perf_counter() - epoch_start,
               "peak_gpu_allocated": torch.cuda.max_memory_allocated(device),
               "peak_gpu_reserved": torch.cuda.max_memory_reserved(device)}
        history.append(row); improved = val_info["dice"] > best_score
        if improved: best_score, best_epoch = val_info["dice"], epoch
        stop = trainer.early_stopping.update(val_info["dice"])
        early = {"best": trainer.early_stopping.best, "bad_epochs": trainer.early_stopping.bad_epochs,
                 "patience": 15, "stopped": stop}
        generators = {"train": train_loader.generator.get_state(), "val": val_loader.generator.get_state()}
        common = (model, optimizer, scheduler, trainer.scaler, epoch, trainer.global_step, best_score,
                  runtime_config, 42, history, "phase4_v2", metadata["hashes"], spec["experiment_id"],
                  spec["key"], 512, 0.5)
        save_training_checkpoint(latest_path, *common, early_stopping_state=early, loader_generator_states=generators)
        if improved:
            save_training_checkpoint(checkpoint_dir / "best.pt", *common, early_stopping_state=early, loader_generator_states=generators)
        pd.DataFrame(history).to_csv(exp_dir / "history.csv", index=False)
        line = (f"Epoch {epoch:03d}/100 train_loss={row['train_loss']:.8f} val_loss={row['val_loss']:.8f} "
                f"val_dice={row['val_dice']:.15f} val_iou={row['val_iou']:.15f} "
                f"lr={row['learning_rate']:.10f} seconds={row['epoch_seconds']:.1f} best={improved}\n")
        print(spec["display_name"], line.strip(), flush=True); log.write(line); log.flush()
        if stop:
            log.write(f"Early stopping epoch={epoch} best_epoch={best_epoch} best={best_score:.15f}\n"); break

    log.close(); total_seconds = sum(x["epoch_seconds"] for x in history)
    summary = {"experiment_id": spec["experiment_id"], "status": "TRAINED_PENDING_VAL_FINALIZATION",
               "model": spec["key"], "display_name": spec["display_name"], "architecture": spec["architecture"],
               "parameter_count": parameters, "seed": 42, "epochs_completed": len(history), "best_epoch": best_epoch,
               "best_val_dice_checkpoint_selection": best_score, "physical_batch": batch,
               "gradient_accumulation_steps": accumulation, "effective_batch": batch * accumulation,
               "training_seconds": total_seconds, "mean_epoch_seconds": total_seconds / len(history),
               "peak_gpu_allocated": max(x["peak_gpu_allocated"] for x in history),
               "peak_gpu_reserved": max(x["peak_gpu_reserved"] for x in history),
               "initialization": "random_kaiming_no_pretrained_weights", "pretrained_weights": False,
               "manifest_version": "phase4_v2", "manifest_hashes": metadata["hashes"],
               "best_checkpoint": str(checkpoint_dir / "best.pt"), "latest_checkpoint": str(latest_path),
               "test_accessed": False, "external_accessed": False, "experiment_a_modified": False}
    (exp_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    record.update(status="TRAINED_PENDING_VAL_FINALIZATION", end_time=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  best_val_dice=best_score, notes="Phase 10 training complete; VAL finalization pending")
    register_experiment(record, ROOT)


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--model", choices=["attention_unet", "unetpp", "deeplabv3plus", "all"], default="all")
    args = parser.parse_args(); config = load_config()
    specs = config["models"] if args.model == "all" else [x for x in config["models"] if x["key"] == args.model]
    for spec in specs: train_model(spec, config)


if __name__ == "__main__": main()
