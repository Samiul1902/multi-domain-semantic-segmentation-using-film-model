"""Real-data training/evaluation producers for the five external baselines and the GlobalMedFiLM adapter.

Real execution is gated exactly like the C1 trainer: a caller must pass a grant object exposing
``authorize_baseline(contract)``.  No such grant exists in the repository, so real runs fail closed;
this module never mints one.  The same ``fit_baseline`` engine is exercised by synthetic tests, with
outputs forced outside the real run root and labelled ``synthetic``.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import pickle
import platform
import time
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator, Mapping

import numpy as np
import torch

from src.research.c3_baselines import experiment as C3
from src.research.stage6 import matrix as M
from src.research.stage6.evaluate import evaluate_plain_model

ROOT = M.ROOT
CONTRACT_SCHEMA = "stage6_baseline_real_contract_v1"
REAL_ROOT = M.RUN_ROOT
DOMAIN_ORDER = C3.DOMAIN_ORDER
EVALUATION_CONFIGURATION = {
    "precision": "fp32", "batch_size": 1, "threshold": 0.5, "metric_definition": "stage6 per_image_record",
    "selection_during_training": "AMP batch-8 validation (frozen C1 recipe)",
    "numerical_note": ("Prospective batch-1 fp32 export can differ numerically from batch-8 mixed-precision "
                       "validation and from historical batch-8 AMP caches; the two configurations are never mixed."),
}


class BaselineExecutionError(RuntimeError):
    pass


def c3_key(model_key: str) -> str:
    if model_key not in M.BASELINES:
        raise BaselineExecutionError(f"not an external baseline: {model_key}")
    return model_key.lower()


def make_contract(model_key: str, seed: int, *, device: str = "cuda") -> dict[str, Any]:
    """Hash-bound run contract derived from the frozen C3/C1 configuration (no data access)."""
    config = C3.build_experiment_config(c3_key(model_key), seed)
    spec = C3.ARCHITECTURES[c3_key(model_key)]
    probe = C3.build_model(c3_key(model_key))
    contract = {
        "schema": CONTRACT_SCHEMA, "model_key": model_key, "c3_model_key": c3_key(model_key), "seed": seed,
        "device": device, "training_protocol": copy.deepcopy(M.EXPECTED_TRAINING_PROTOCOL),
        "c3_config": config, "parameters_trainable": C3.parameter_count(probe),
        "architecture_specific_differences": {
            "architecture": spec["architecture"], "detail": spec["historical_architecture_detail"],
            "pretrained_weights": False, "task_id_is_model_input": False,
            "note": "Computational cost differs by architecture; no equalisation of FLOPs or memory is attempted."},
        "evaluation_configuration": EVALUATION_CONFIGURATION,
        "train_workers": 4, "eval_workers": 2,
    }
    contract["contract_sha256"] = hashlib.sha256(json.dumps(contract, sort_keys=True, default=str).encode()).hexdigest()
    return contract


def _authorize(contract: Mapping[str, Any], grant: Any) -> None:
    if grant is None:
        raise BaselineExecutionError("STAGE6_BASELINE_LAUNCH_GRANT_REQUIRED")
    authorize = getattr(grant, "authorize_baseline", None)
    if not callable(authorize):
        raise BaselineExecutionError("STAGE6_BASELINE_LAUNCH_GRANT_INVALID")
    authorize(dict(contract))


# ----------------------------------------------------------------------------- real loaders
def _datasets():
    from src.data.multidomain_dataset import MultiDomainDataset

    train = MultiDomainDataset(C3.MANIFEST_TRAIN, "TRAIN", size=512, train=True, channel_policy="RGB_3CH")
    val = MultiDomainDataset(C3.MANIFEST_VAL, "VAL", size=512, train=False, channel_policy="RGB_3CH")
    if (len(train), len(val)) != (5832, 808):
        raise BaselineExecutionError(f"population mismatch TRAIN/VAL: {len(train)}/{len(val)}")
    return train, val


def build_real_loaders(seed: int, *, train_batch: int = 4, eval_batch: int = 8, train_workers: int = 4,
                       eval_workers: int = 2):
    """Canonical TRAIN5832 domain-balanced loader factory and VAL808 loader (TEST is rejected upstream)."""
    from src.data.domain_balanced_sampler import build_domain_balanced_sampler, derive_epoch_seed
    from src.data.loaders import create_loader
    from src.data.multidomain_dataset import harmonized_collate

    train, val = _datasets()
    domains = train.frame["dataset"].tolist()

    def train_factory(epoch: int):
        return create_loader(train, batch_size=train_batch, shuffle=False, seed=derive_epoch_seed(seed, epoch),
                             num_workers=train_workers, persistent_workers=False, collate_fn=harmonized_collate,
                             sampler=build_domain_balanced_sampler(domains, seed, epoch))

    val_loader = create_loader(val, batch_size=eval_batch, shuffle=False, seed=seed, num_workers=eval_workers,
                               collate_fn=harmonized_collate)
    return train_factory, val_loader


def iter_real_val_samples() -> Iterator[dict[str, Any]]:
    """Batch-1 VAL808 samples in manifest order for the per-image exporter."""
    _, val = _datasets()
    for i in range(len(val)):
        s = val[i]
        yield {"sample_id": s.sample_id, "domain": s.dataset, "task_id": s.task_id,
               "image": s.image[None], "mask": s.mask[0].numpy()}


def check_task_ids(batch: Mapping[str, Any]) -> None:
    for domain, task in zip(batch["dataset"], batch["task_id"].tolist()):
        if M.TASK_IDS.get(domain) != task:
            raise C3.C3ExecutionError("domain/task_id mapping violated")


def loader_forward_backward_check(model_key: str, seed: int = 42, *, samples_per_domain: int = 1,
                                  device: str = "cuda") -> dict[str, Any]:
    """Loader correctness probe: eligible TRAIN rows only, one forward/backward pass, no optimizer step, nothing saved."""
    from src.data.multidomain_dataset import harmonized_collate

    train, _ = _datasets()
    labels = train.frame["dataset"].to_numpy()
    picks = [int(i) for d in DOMAIN_ORDER for i in np.flatnonzero(labels == d)[:samples_per_domain]]
    batch = harmonized_collate([train[i] for i in picks])
    C3._validate_batch(batch, "TRAIN")
    check_task_ids(batch)
    dev = torch.device(device)
    C3._seed_everything(seed)
    model = C3.build_model(c3_key(model_key)).to(dev).train()
    criterion = C3.BCEDiceLoss(0.5, 0.5, 1e-6)
    torch.cuda.reset_peak_memory_stats(dev) if dev.type == "cuda" else None
    with torch.amp.autocast(device_type=dev.type, enabled=dev.type == "cuda"):
        logits = model(batch["image"].to(dev))
        loss = criterion(logits, batch["mask"].to(dev))
    loss.backward()
    finite_grads = all(p.grad is None or bool(torch.isfinite(p.grad).all()) for p in model.parameters())
    return {
        "model_key": model_key, "split": "TRAIN", "n_samples": len(picks),
        "domains": list(batch["dataset"]), "task_ids": batch["task_id"].tolist(),
        "image_shape": list(batch["image"].shape), "mask_shape": list(batch["mask"].shape),
        "mask_unique_values": sorted(float(v) for v in torch.unique(batch["mask"])),
        "logits_shape": list(logits.shape), "loss": float(loss.detach()), "finite_gradients": finite_grads,
        "peak_memory_mib": (torch.cuda.max_memory_allocated(dev) / 2 ** 20) if dev.type == "cuda" else None,
        "protected_splits_accessed": [], "optimizer_step_taken": False, "checkpoint_written": False,
    }


# ----------------------------------------------------------------------------- training engine
def fit_baseline(contract: Mapping[str, Any], train_factory: Callable[[int], Iterable[dict]], val_loader: Iterable[dict],
                 run_dir: Path, *, real: bool, device: str = "cuda", resume: bool = False,
                 max_epochs: int | None = None, base_channels: int = C3.BASE_CHANNELS) -> dict[str, Any]:
    """Train with the frozen recipe, select by equal-domain macro VAL Dice, checkpoint atomically, resume exactly."""
    run_dir = Path(run_dir).resolve()
    inside_real = REAL_ROOT.resolve() in (run_dir, *run_dir.parents)
    if real != inside_real:
        raise BaselineExecutionError("real outputs must live under the real run root and synthetic outputs outside it")
    proto = contract["training_protocol"]
    if proto != M.EXPECTED_TRAINING_PROTOCOL:
        raise BaselineExecutionError("training protocol differs from the frozen recipe")
    if real and max_epochs is not None:
        raise BaselineExecutionError("max_epochs override is permitted only for synthetic tests")
    epochs = int(proto["max_epochs"] if max_epochs is None else max_epochs)
    model_key, seed = contract["model_key"], int(contract["seed"])
    dev = torch.device(device)
    amp = bool(proto["amp"]) and dev.type == "cuda"
    run_dir.mkdir(parents=True, exist_ok=True)
    latest, best, history_path = run_dir / "latest.pt", run_dir / "best.pt", run_dir / "history.jsonl"
    digest = contract["contract_sha256"]

    C3._seed_everything(seed)
    model = C3.build_model(contract["c3_model_key"], base_channels=base_channels).to(dev)
    optimizer = torch.optim.AdamW(model.parameters(), lr=proto["learning_rate"], weight_decay=proto["weight_decay"])
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=proto["T_max"])
    scaler = torch.amp.GradScaler("cuda", enabled=amp)
    criterion = C3.BCEDiceLoss(proto["bce_weight"], proto["dice_weight"], proto["dice_epsilon"])
    history: list[dict[str, Any]] = []
    start, best_macro, best_loss, best_epoch, bad = 1, -math.inf, math.inf, 0, 0
    if latest.exists() and not resume:
        raise BaselineExecutionError("existing run state found; pass resume=True or choose a new directory")
    if resume:
        if not latest.is_file():
            raise BaselineExecutionError("resume requires latest.pt")
        try:
            ck = torch.load(latest, map_location="cpu", weights_only=False)
        except (OSError, EOFError, RuntimeError, pickle.UnpicklingError) as exc:
            raise BaselineExecutionError(f"corrupt latest checkpoint: {exc}") from exc
        if ck.get("contract_sha256") != digest or ck.get("model_key") != model_key or ck.get("seed") != seed \
                or ck.get("real") is not real:
            raise BaselineExecutionError("resume contract/model/seed/evidence-class mismatch")
        model.load_state_dict(ck["model_state"], strict=True)
        optimizer.load_state_dict(ck["optimizer_state"])
        scheduler.load_state_dict(ck["scheduler_state"])
        scaler.load_state_dict(ck["scaler_state"])
        history = ck["history_rows"]
        start = int(ck["epoch"]) + 1
        best_macro, best_loss, best_epoch, bad = ck["best_macro"], ck["best_loss"], ck["best_epoch"], ck["bad_epochs"]

    for epoch in range(start, epochs + 1):
        if bad >= int(proto["early_stop_patience"]):
            break
        from src.data.domain_balanced_sampler import derive_epoch_seed
        C3._seed_everything(derive_epoch_seed(seed, epoch))
        model.train()
        t0, losses = time.perf_counter(), []
        for batch in train_factory(epoch):
            C3._validate_batch(batch, "TRAIN")
            check_task_ids(batch)
            optimizer.zero_grad(set_to_none=True)
            with torch.amp.autocast(device_type=dev.type, enabled=amp):
                loss = criterion(model(batch["image"].to(dev)), batch["mask"].to(dev))
            if not torch.isfinite(loss):
                raise C3.C3ExecutionError("nonfinite training loss")
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            losses.append(float(loss.detach()))
        if not losses:
            raise C3.C3ExecutionError("empty training loader")
        val_loss, per_domain, _ = C3._evaluate(model, val_loader, criterion, dev, proto["threshold"], amp)
        macro = C3.macro_domain_dice({d: per_domain[d]["dice"] for d in DOMAIN_ORDER})
        improved = C3.is_new_best(macro, val_loss, best_macro, best_loss)
        if improved:
            best_macro, best_loss, best_epoch, bad = macro, val_loss, epoch, 0
        else:
            bad += 1
        history.append({"epoch": epoch, "train_loss": float(np.mean(losses)), "val_loss": val_loss,
                        "macro_domain_dice": macro, **{f"val_dice_{d}": per_domain[d]["dice"] for d in DOMAIN_ORDER},
                        **{f"val_iou_{d}": per_domain[d]["iou"] for d in DOMAIN_ORDER},
                        "learning_rate": float(optimizer.param_groups[0]["lr"]), "is_new_best": improved,
                        "seconds_measured": time.perf_counter() - t0})
        history_path.write_text("".join(json.dumps(r, sort_keys=True, allow_nan=False) + "\n" for r in history),
                                encoding="utf-8")
        scheduler.step()
        state = {"schema": "stage6_baseline_checkpoint_v1", "model_key": model_key, "seed": seed, "epoch": epoch,
                 "contract_sha256": digest, "real": real, "model_state": model.state_dict(),
                 "optimizer_state": optimizer.state_dict(), "scheduler_state": scheduler.state_dict(),
                 "scaler_state": scaler.state_dict(), "best_macro": best_macro, "best_loss": best_loss,
                 "best_epoch": best_epoch, "bad_epochs": bad, "history_rows": history}
        C3._atomic_torch_save(latest, state)
        if improved:
            C3._atomic_torch_save(best, state)

    if not best.is_file():
        raise BaselineExecutionError("no best checkpoint produced")
    replay = C3.select_best_epoch(history)
    saved = torch.load(best, map_location="cpu", weights_only=False)
    if saved["epoch"] != replay["selected_epoch"] or saved["contract_sha256"] != digest:
        raise BaselineExecutionError("best checkpoint does not match replayed validation selection")
    manifest = {"schema": "stage6_baseline_run_manifest_v1", "model_key": model_key, "seed": seed, "real": real,
                "contract_sha256": digest, "best_epoch": best_epoch, "completed_epochs": len(history),
                "history_sha256": C3.sha256_file(history_path), "best_checkpoint_sha256": C3.sha256_file(best),
                "latest_checkpoint_sha256": C3.sha256_file(latest), "protected_splits_accessed": []}
    C3._atomic_json(run_dir / "run_manifest.json", manifest)
    return manifest


# ----------------------------------------------------------------------------- result export
def _hardware(device: torch.device) -> dict[str, Any]:
    return {"device": torch.cuda.get_device_name(device) if device.type == "cuda" else "cpu", "torch": torch.__version__,
            "cuda": torch.version.cuda, "platform": platform.platform()}


def export_cell(model: torch.nn.Module, samples: Iterable[Mapping[str, Any]], cell_dir: Path, *, model_key: str, seed: int,
                real: bool, device: str, provenance: Mapping[str, Any], takes_task: bool = False,
                macs_input: tuple[int, int, int, int] = (1, 3, 512, 512)) -> dict[str, Any]:
    """Batch-1 fp32 per-image export through the shared exporter and the strict cell writer."""
    dev = torch.device(device)
    meta: list[Mapping[str, Any]] = []

    def tracked() -> Iterator[Mapping[str, Any]]:
        for s in samples:
            meta.append(s)
            yield s

    macs = None if takes_task else C3.analytical_macs_lower_bound(model.to(dev), macs_input)["macs_lower_bound"]
    records, summary = evaluate_plain_model(model, tracked(), device=device, parameters=C3.parameter_count(model),
                                            macs=macs, takes_task=takes_task)
    for rec, s in zip(records, meta):
        rec["task_id"] = int(s["task_id"])
    prov = {**provenance, "model_key": model_key, "seed": seed, "synthetic": not real, "training_performed": True,
            "evidence_class": M.REAL_EVIDENCE_CLASS if real else M.SYNTHETIC_EVIDENCE_CLASS,
            "protocol_sha256": M.PROTOCOL_SHA256, "protected_splits_accessed": [],
            "evaluation_hardware": _hardware(dev), "evaluation_configuration": EVALUATION_CONFIGURATION,
            "macs_method": "Conv2d+Linear lower bound" if macs is not None else "not measured"}
    return M.write_cell_result(Path(cell_dir), model_key=model_key, seed=seed, records=records, summary=summary, provenance=prov)


def export_trained_baseline(contract: Mapping[str, Any], run_dir: Path, cell_dir: Path, samples: Iterable[Mapping[str, Any]],
                            *, real: bool, device: str, base_channels: int = C3.BASE_CHANNELS) -> dict[str, Any]:
    run_dir = Path(run_dir)
    manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
    best = run_dir / "best.pt"
    if (manifest["contract_sha256"] != contract["contract_sha256"] or manifest["real"] is not real
            or C3.sha256_file(best) != manifest["best_checkpoint_sha256"]):
        raise BaselineExecutionError("run manifest does not match contract/checkpoint")
    ck = torch.load(best, map_location="cpu", weights_only=False)
    model = C3.build_model(contract["c3_model_key"], base_channels=base_channels)
    model.load_state_dict(ck["model_state"], strict=True)
    cfg = contract["c3_config"]
    provenance = {
        "checkpoint_sha256": manifest["best_checkpoint_sha256"], "checkpoint_path": str(best.relative_to(ROOT)) if real else str(best),
        "best_epoch": manifest["best_epoch"], "completed_epochs": manifest["completed_epochs"],
        "history_sha256": manifest["history_sha256"], "contract_sha256": contract["contract_sha256"],
        "training_protocol": contract["training_protocol"], "train_manifest_sha256": cfg["dataset"]["train_manifest_sha256"],
        "val_manifest_sha256": cfg["dataset"]["val_manifest_sha256"], "model_source_sha256": cfg["source"]["model_source_sha256"],
        "architecture_specific_differences": contract["architecture_specific_differences"],
        "seed_independence": "independently trained from random initialisation per seed",
        "historical_results_used": False,
    }
    return export_cell(model, samples, cell_dir, model_key=contract["model_key"], seed=contract["seed"], real=real,
                       device=device, provenance=provenance)


def run_real_baseline(model_key: str, seed: int, *, grant: Any, device: str = "cuda", resume: bool = False) -> dict[str, Any]:
    """Genuine TRAIN5832 training + VAL808 export.  Fails closed without a release grant."""
    if device != "cuda" or not torch.cuda.is_available():
        raise BaselineExecutionError("real baseline training requires CUDA (use the project .venv interpreter)")
    contract = make_contract(model_key, seed, device=device)
    _authorize(contract, grant)
    run_dir = M.cell_dir(REAL_ROOT, model_key, seed) / "training"
    train_factory, val_loader = build_real_loaders(seed, train_workers=contract["train_workers"], eval_workers=contract["eval_workers"])
    fit_baseline(contract, train_factory, val_loader, run_dir, real=True, device=device, resume=resume)
    return export_trained_baseline(contract, run_dir, M.cell_dir(REAL_ROOT, model_key, seed), iter_real_val_samples(),
                                   real=True, device=device)


# ----------------------------------------------------------------------------- GlobalMedFiLM via C1-T
def global_manifest_from_c1(run_dir: Path, seed: int, *, allow_synthetic: bool = False) -> tuple[dict[str, Any], dict[str, Any]]:
    """Read-only translation of a validated C1-T run into the compatibility manifest; never touches C1 code."""
    from src.research.paper_assets.c1_run_export import validate_run

    report = validate_run(run_dir, expected_arm="C1-T", expected_seed=seed, allow_synthetic=allow_synthetic, check_continuity=False)
    state = torch.load(Path(run_dir) / report["checkpoint_file"], map_location="cpu", weights_only=True)
    contract, recipe = state["contract"], state["contract"]["recipe"]
    pops = contract["dataset"]["populations"]
    manifest = {
        "arm": contract["arm"], "model_identity": "GlobalMedFiLM", "seed": contract["seed"],
        "protocol_sha256": contract["protocol_sha256"], "train_n": pops["TRAIN"]["n"], "val_n": pops["VAL"]["n"],
        "resolution": recipe["resolution"], "channel_policy": recipe["channel_policy"],
        "selection_rule": recipe["selection_rule"], "threshold": recipe["threshold"],
        "checkpoint_sha256": report["checkpoint_sha256"], "per_image_export_sha256": report["checkpoint_sha256"],
        "protected_splits_accessed": [], "mode": contract["mode"],
        "training_protocol": {**{k: recipe.get(k) for k in M.EXPECTED_TRAINING_PROTOCOL if k in recipe},
                              "train_batch_size": recipe["train_batch_size"], "loss": recipe["loss"]},
        "val_manifest_sha256": pops["VAL"]["sha256"], "train_manifest_sha256": pops["TRAIN"]["sha256"],
    }
    return manifest, state


def export_global_cell_from_c1(run_dir: Path, seed: int, cell_dir: Path, samples: Iterable[Mapping[str, Any]], *,
                               device: str = "cuda", allow_synthetic: bool = False) -> dict[str, Any]:
    """Populate a GLOBAL_MEDFILM cell only when the C1-T artifact passes every compatibility check."""
    from src.research.c1_film.control import build_matched_arms

    manifest, state = global_manifest_from_c1(run_dir, seed, allow_synthetic=allow_synthetic)
    ok, reasons = M.c1t_can_populate_global(manifest)
    if manifest["mode"] == "SYNTHETIC_ONLY":
        reasons = [*reasons, "C1 run is synthetic"]
    if reasons:
        raise BaselineExecutionError("C1-T not compatible with GLOBAL_MEDFILM cell: " + "; ".join(reasons))
    model, _ = build_matched_arms(seed)
    model.load_state_dict(state["best_model"], strict=True)
    provenance = {
        "checkpoint_sha256": manifest["checkpoint_sha256"], "checkpoint_source": "C1-T selected epoch best_model",
        "best_epoch": state["best_epoch"], "contract_sha256": hashlib.sha256(json.dumps(state["contract"], sort_keys=True).encode()).hexdigest(),
        "training_protocol": {**M.EXPECTED_TRAINING_PROTOCOL, **{k: manifest["training_protocol"][k] for k in manifest["training_protocol"]
                                                                  if k in M.EXPECTED_TRAINING_PROTOCOL}},
        "train_manifest_sha256": manifest["train_manifest_sha256"], "val_manifest_sha256": manifest["val_manifest_sha256"],
        "reused_artifact": "C1-T", "historical_results_used": False,
    }
    return export_cell(model, samples, cell_dir, model_key=M.GLOBAL, seed=seed, real=True, device=device,
                       provenance=provenance, takes_task=True)
