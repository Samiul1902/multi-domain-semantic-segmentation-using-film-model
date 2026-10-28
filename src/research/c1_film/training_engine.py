"""C1 matched training loop; data supplied by gated adapter or synthetic fixtures."""
from __future__ import annotations

import copy
import hashlib
import math
import random
import time
from pathlib import Path

import numpy as np
import torch

from scripts.training.phase21_common import per_image_dice_iou_precision_recall
from src.data.domain_balanced_sampler import derive_epoch_seed
from src.losses.segmentation import BCEDiceLoss
from src.training.phase20_selection import DOMAIN_ORDER, is_new_best, select_best_epoch
from .control import build_matched_arms, optimizer_group_spec, parameter_accounting, verify_identity_control
from .integration_contract import digest, validate_contract, validate_synthetic_output
from .recovery_store import EpochStore, RecoveryError, writer_lock


def capture_rng() -> dict:
    n = np.random.get_state()
    return {"python": random.getstate(), "numpy": [n[0], n[1].tolist(), n[2], n[3], n[4]],
            "cpu": torch.get_rng_state(),
            "cuda": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else []}


def restore_rng(state: dict) -> None:
    random.setstate(state["python"])
    n = state["numpy"]
    np.random.set_state((n[0], np.asarray(n[1], dtype=np.uint32), n[2], n[3], n[4]))
    torch.set_rng_state(state["cpu"].cpu())
    if state["cuda"]:
        if len(state["cuda"]) != torch.cuda.device_count():
            raise RecoveryError("C1_CUDA_RNG_TOPOLOGY_CHANGED")
        torch.cuda.set_rng_state_all([x.cpu() for x in state["cuda"]])


def initial_digest(model) -> str:
    h = hashlib.sha256()
    for name, tensor in sorted(model.state_dict().items()):
        h.update(name.encode())
        h.update(tensor.cpu().contiguous().numpy().tobytes())
    return h.hexdigest()


class Trainer:
    def __init__(self, contract: dict, *, grant=None):
        validate_contract(contract)
        if contract["mode"] != "SYNTHETIC_ONLY":
            # The preparation gate (assert_launch_allowed) remains frozen and can
            # never return. Real execution requires a LaunchGrant minted by the
            # additive launch release after the full authorization chain passes.
            from .readiness import ReadinessError
            if grant is None:
                raise ReadinessError("C1_LAUNCH_GRANT_REQUIRED")
            authorize = getattr(grant, "authorize_trainer", None)
            if not callable(authorize):
                raise ReadinessError("C1_LAUNCH_GRANT_INVALID")
            authorize(contract)
        self.contract = copy.deepcopy(contract)
        self.identity = digest(contract)
        self.device = torch.device(contract["device"])
        self.recipe = contract["recipe"]
        seed = contract["seed"]
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        if self.device.type == "cuda":
            torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
        t, c = build_matched_arms(seed)
        self.model = (t if contract["arm"] == "C1-T" else c).to(self.device)
        self.initial_sha256 = initial_digest(self.model)
        self.counts = parameter_accounting(self.model)
        self.optimizer = torch.optim.AdamW(optimizer_group_spec(self.model))
        self.scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            self.optimizer, T_max=self.recipe["T_max"])
        self.amp = self.recipe["amp"] and self.device.type == "cuda"
        self.scaler = torch.amp.GradScaler("cuda", enabled=self.amp)
        self.criterion = BCEDiceLoss(self.recipe["bce_weight"], self.recipe["dice_weight"],
                                    self.recipe["dice_epsilon"])
        self.history = []
        self.best_macro, self.best_loss = -math.inf, math.inf
        self.best_epoch, self.bad_epochs = 0, 0
        self.best_model, self.best_records = None, []
        self.loader_states = {}
        self.active_seconds = 0.0

    def check_batch(self, batch: dict, split: str) -> None:
        from .readiness import TASK_IDS
        if (not batch["split"] or any(s != split for s in batch["split"]) or
                len(batch["dataset"]) != len(batch["task_id"]) or
                len(batch["sample_id"]) != len(batch["dataset"]) or
                len(batch["image"]) != len(batch["dataset"]) or
                len(batch["split"]) != len(batch["dataset"])):
            raise RecoveryError("C1_BATCH_SPLIT_OR_LENGTH_MISMATCH")
        for domain, task in zip(batch["dataset"], batch["task_id"].tolist()):
            if domain not in TASK_IDS or TASK_IDS[domain] != task:
                raise RecoveryError("C1_BATCH_DOMAIN_TASK_MISMATCH")
        side = 32 if self.contract["mode"] == "SYNTHETIC_ONLY" else self.recipe["resolution"]
        if tuple(batch["image"].shape[1:]) != (3, side, side):
            raise RecoveryError("C1_INPUT_SHAPE_DRIFT")
        if tuple(batch["mask"].shape) != (len(batch["image"]), 1, side, side):
            raise RecoveryError("C1_TARGET_SHAPE_DRIFT")
        if (not torch.isfinite(batch["image"]).all() or not torch.isfinite(batch["mask"]).all()
                or not ((batch["mask"] == 0) | (batch["mask"] == 1)).all()):
            raise RecoveryError("C1_NONFINITE_OR_NONBINARY_INPUT")

    @staticmethod
    def remember_loader(loader) -> dict:
        return {"loader": loader.generator.get_state() if loader.generator is not None else None,
                "sampler": loader.sampler.generator.get_state()
                if getattr(loader.sampler, "generator", None) is not None else None}

    def train_epoch(self, loader) -> float:
        self.model.train()
        losses = []
        for batch in loader:
            self.check_batch(batch, "TRAIN")
            self.optimizer.zero_grad(set_to_none=True)
            with torch.amp.autocast(device_type=self.device.type, enabled=self.amp):
                logits = self.model(batch["image"].to(self.device), batch["task_id"].to(self.device))
                loss = self.criterion(logits, batch["mask"].to(self.device))
            if not torch.isfinite(loss):
                raise RecoveryError("C1_NONFINITE_LOSS")
            self.scaler.scale(loss).backward()
            self.scaler.unscale_(self.optimizer)
            if any(p.grad is not None and not torch.isfinite(p.grad).all()
                   for p in self.model.parameters()):
                raise RecoveryError("C1_NONFINITE_GRADIENT")
            self.scaler.step(self.optimizer)
            self.scaler.update()
            losses.append(float(loss.detach()))
        if not losses:
            raise RecoveryError("C1_EMPTY_TRAIN_LOADER")
        self.loader_states["train"] = self.remember_loader(loader)
        return float(np.mean(losses))

    @torch.no_grad()
    def evaluate(self, loader):
        self.model.eval()
        losses, records = [], []
        for batch in loader:
            self.check_batch(batch, "VAL")
            with torch.amp.autocast(device_type=self.device.type, enabled=self.amp):
                logits = self.model(batch["image"].to(self.device), batch["task_id"].to(self.device))
                loss = self.criterion(logits, batch["mask"].to(self.device))
            if not torch.isfinite(loss):
                raise RecoveryError("C1_NONFINITE_VALIDATION")
            losses.append(float(loss))
            metrics = per_image_dice_iou_precision_recall(
                logits, batch["mask"].to(self.device), self.recipe["threshold"])
            for i, sid in enumerate(batch["sample_id"]):
                records.append({"sample_id": sid, "domain": batch["dataset"][i],
                                **{k: float(v[i]) for k, v in metrics.items()}})
        if not losses or len({r["sample_id"] for r in records}) != len(records):
            raise RecoveryError("C1_EMPTY_OR_DUPLICATE_VALIDATION")
        by_domain = {d: float(np.mean([r["dice"] for r in records if r["domain"] == d]))
                     for d in DOMAIN_ORDER}
        if not all(math.isfinite(v) for v in by_domain.values()):
            raise RecoveryError("C1_MISSING_DOMAIN")
        self.loader_states["val"] = self.remember_loader(loader)
        return float(np.mean(losses)), by_domain, records

    def state(self) -> dict:
        return {"schema": 1, "identity": self.identity, "contract": self.contract,
                "epoch": len(self.history), "model": self.model.state_dict(),
                "optimizer": self.optimizer.state_dict(), "scheduler": self.scheduler.state_dict(),
                "scaler": self.scaler.state_dict(), "rng": capture_rng(),
                "loader_states": self.loader_states, "history": self.history,
                "best_macro": self.best_macro, "best_loss": self.best_loss,
                "best_epoch": self.best_epoch, "bad_epochs": self.bad_epochs,
                "best_model": self.best_model, "best_records": self.best_records,
                "initial_sha256": self.initial_sha256, "counts": self.counts,
                "active_seconds": self.active_seconds}

    def restore(self, state: dict) -> None:
        if (state["contract"] != self.contract or state["identity"] != self.identity or
                state["initial_sha256"] != self.initial_sha256 or state["counts"] != self.counts or
                state["epoch"] != len(state["history"])):
            raise RecoveryError("C1_RECOVERY_CONTRACT_MISMATCH")
        history = state["history"]
        if [r["epoch"] for r in history] != list(range(1, len(history) + 1)):
            raise RecoveryError("C1_HISTORY_DISCONTIGUOUS")
        for row in history:
            if (not all(math.isfinite(row[f"val_dice_{d}"]) for d in DOMAIN_ORDER) or
                    not math.isfinite(row["val_loss"]) or
                    row["macro_domain_dice"] != sum(row[f"val_dice_{d}"] for d in DOMAIN_ORDER) / 4):
                raise RecoveryError("C1_HISTORY_METRIC_TRACE_MISMATCH")
        replay = select_best_epoch(history)
        if any(row["improved"] != trace["improved"]
               for row, trace in zip(history, replay["trace"])):
            raise RecoveryError("C1_SELECTION_TRACE_MISMATCH")
        if (replay["selected_epoch"] != state["best_epoch"] or
                replay["selected_macro_domain_dice"] != state["best_macro"] or
                replay["selected_val_loss"] != state["best_loss"] or
                len(history) - state["best_epoch"] != state["bad_epochs"]):
            raise RecoveryError("C1_SELECTION_REPLAY_MISMATCH")
        self.model.load_state_dict(state["model"], strict=True)
        self.optimizer.load_state_dict(state["optimizer"])
        self.scheduler.load_state_dict(state["scheduler"])
        self.scaler.load_state_dict(state["scaler"])
        if self.contract["arm"] == "C1-C":
            verify_identity_control(self.model)
        self.history = history
        for name in ("best_macro", "best_loss", "best_epoch", "bad_epochs", "best_model",
                     "best_records", "loader_states", "active_seconds"):
            setattr(self, name, state[name])
        restore_rng(state["rng"])

    def run(self, root: Path, loader_factory, *, resume=False, recover_writer=False,
            fault=None, until_epoch=None) -> dict:
        """Replay interrupted epochs; never reinterpret an existing run as fresh."""
        validate_contract(self.contract)
        root = (validate_synthetic_output(root) if self.contract["mode"] == "SYNTHETIC_ONLY"
                else Path(root))
        with writer_lock(root, recover=recover_writer):
            store = EpochStore(root)
            if resume:
                self.restore(store.load(self.identity))
            elif ((root / "lifecycle.json").exists() or (root / "latest.json").exists()
                  or list(root.glob("epoch-*.pt"))):
                raise RecoveryError("C1_EXISTING_ATTEMPT_REQUIRES_RESUME")
            store.lifecycle("RUNNING", self.identity)
            full_limit = self.contract["fixture"]["epochs"] if self.contract["fixture"] else self.recipe["max_epochs"]
            limit = min(full_limit, until_epoch) if until_epoch is not None else full_limit
            for epoch in range(len(self.history) + 1, limit + 1):
                if self.bad_epochs >= self.recipe["early_stop_patience"]:
                    break
                if self.active_seconds >= 96 * 3600:
                    raise RecoveryError("C1_ACTIVE_TIME_LIMIT")
                start = time.perf_counter()
                ep_seed = derive_epoch_seed(self.contract["seed"], epoch)
                torch.manual_seed(ep_seed)
                random.seed(ep_seed)
                np.random.seed(ep_seed)
                train_loader, val_loader = loader_factory(self.contract["seed"], epoch)
                train_loss = self.train_epoch(train_loader)
                val_loss, by_domain, records = self.evaluate(val_loader)
                self.scheduler.step()
                macro = float(sum(by_domain.values()) / 4)
                improved = is_new_best(macro, val_loss, self.best_macro, self.best_loss)
                if improved:
                    self.best_macro, self.best_loss = macro, val_loss
                    self.best_epoch, self.bad_epochs = epoch, 0
                    self.best_model = {n: p.detach().cpu().clone() for n, p in self.model.state_dict().items()}
                    self.best_records = records
                else:
                    self.bad_epochs += 1
                self.active_seconds += time.perf_counter() - start
                self.history.append({"epoch": epoch, "train_loss": train_loss, "val_loss": val_loss,
                                     "macro_domain_dice": macro, "improved": improved,
                                     "learning_rate": self.optimizer.param_groups[0]["lr"],
                                     **{f"val_dice_{d}": v for d, v in by_domain.items()}})
                if self.contract["arm"] == "C1-C":
                    verify_identity_control(self.model)
                store.commit(self.state(), fault=fault)
            complete = len(self.history) >= full_limit or self.bad_epochs >= self.recipe["early_stop_patience"]
            store.lifecycle("COMPLETE" if complete else "PAUSED", self.identity)
            return {"complete": complete, "epochs": len(self.history),
                    "counts": self.counts, "identity": self.identity}
