"""Phase 20B - SHARED FOUR-DOMAIN CONVENTIONAL BASELINE BENCHMARK (generic trainer).

Completes the Phase-20 conventional baseline benchmark. Phase 20A already trained
and closed the frozen UNet++ baseline; Phase 20B trains the REMAINING conventional
architectures under the *identical* Phase-20 protocol so the five models are
directly comparable.

    Phase 20A (done) : UNet++                    -> phase20_shared_unetpp_fourdomain_seed42_clean_v3
    Phase 20B (here) : U-Net
                       Attention U-Net
                       DeepLabV3+
                       Transformer/MiT-style U-Net

Scientific contract
-------------------
Every scientific field is read from the FROZEN Phase-20 protocol
(``reports/audits/phase20_shared_global_baseline_protocol.json``) and is IDENTICAL
for every model:

    RGB_3CH | 512 px | bce_dice 0.5/0.5 eps 1e-6 | AdamW 1e-4 / 1e-4
    CosineAnnealingLR(T_max=100) stepped per epoch after train+val | batch 4
    eval batch 8 | num_workers 4 | AMP | seed 42 | max_epochs 100 | patience 15
    sampling phase20_domain_balanced_uniform_v1 | threshold 0.5
    checkpoint selection phase20_macro_domain_mean_dice_v1 (tie-break lower val loss)

NO per-model recipe change, NO per-model threshold tuning, NO architecture search.
The ONLY per-model differences are (a) the model constructor and (b) the
experiment/output identity. That is what makes the five-way comparison valid.

Governance
----------
NO FiLM. NO task conditioning as model input. NO regional module, localizer,
proposal, ROI or dataset-specific head. ONE shared parameter set across
ISIC / BUSI / KVASIR / KUB. ``task_id`` is sampling/bookkeeping only and is NEVER
passed to the model forward pass. TEST is never read (``verify_test_lock``).

Fail-closed
-----------
Training refuses to start unless, for the requested model:
  * the architecture binding artifact exists and its recorded model-source SHA256
    still matches the file on disk, and
  * the pre-execution check artifact exists with ``all_checks_passed == true``, and
  * the frozen Phase-20 protocol SHA256 still matches.

Execution mechanism (no scientific effect)
------------------------------------------
* ``--resume`` continues the SAME logical run from ``latest.pt``; it never starts a
  second independent run. ``resume_count`` in the closure records how many times.
* Resume is bit-exact BY CONSTRUCTION: data order and every stochastic augmentation
  for epoch k derive from ``derive_epoch_seed(SEED, k)``, so epoch k is a pure
  function of (SEED, k) and is independent of how many epochs ran before it.
  Workers are re-created each epoch (``persistent_workers=False``).
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
from src.models.attention_unet import AttentionUNet
from src.models.deeplabv3plus import DeepLabV3Plus
from src.models.unet import UNet
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
PHASE = 20
SUBPHASE = "20B"
MANIFEST_VERSION = "phase4_v3"
MANIFEST_DIR = ROOT / "manifests/phase4_v3"

PROTOCOL_PATH = ROOT / "reports/audits/phase20_shared_global_baseline_protocol.json"
PROTOCOL_SHA256 = "b74f1f9f429adbce374f0306180943b9f373f872e1e69e115b7d17e81414283c"
BINDING_DIR = ROOT / "reports/audits"

# The ONLY per-model variation permitted in Phase 20B.
MODEL_REGISTRY = {
    "unet": {
        "display_name": "U-Net",
        "class_name": "UNet",
        "class": UNet,
        "module": "src.models.unet",
        "source_file": "src/models/unet.py",
        "architecture": "unet_4_stage_plain_skip_base32",
        "binding_slug": "unet",
        "experiment_id": "phase20b_shared_unet_fourdomain_seed42_clean_v3",
    },
    "attention_unet": {
        "display_name": "Attention U-Net",
        "class_name": "AttentionUNet",
        "class": AttentionUNet,
        "module": "src.models.attention_unet",
        "source_file": "src/models/attention_unet.py",
        "architecture": "attention_unet_4_stage_additive_skip_gates_base32",
        "binding_slug": "attention_unet",
        "experiment_id": "phase20b_shared_attention_unet_fourdomain_seed42_clean_v3",
    },
    "deeplabv3plus": {
        "display_name": "DeepLabV3+",
        "class_name": "DeepLabV3Plus",
        "class": DeepLabV3Plus,
        "module": "src.models.deeplabv3plus",
        "source_file": "src/models/deeplabv3plus.py",
        "architecture": "deeplabv3plus_resnet50_os16_random_init_no_pretrained_aspp_rates_6_12_18",
        "binding_slug": "deeplabv3plus",
        "experiment_id": "phase20b_shared_deeplabv3plus_fourdomain_seed42_clean_v3",
    },
    "transformer_mit_unet": {
        "display_name": "Transformer/MiT-style U-Net",
        "class_name": "TransformerMiTUNet",
        "class": None,  # resolved lazily; only present if the local module exists
        "module": "src.models.transformer_mit_unet",
        "source_file": "src/models/transformer_mit_unet.py",
        "architecture": "transformer_mit_style_unet_local_random_init",
        "binding_slug": "transformer_mit_unet",
        "experiment_id": "phase20b_shared_transformer_mit_unet_fourdomain_seed42_clean_v3",
    },
}

FORBIDDEN_MODULE_TOKENS = ("film", "localizer", "proposal", "roi", "regional",
                           "domain_embedding", "task_embedding", "routing")

ORDER = ["unet", "attention_unet", "deeplabv3plus", "transformer_mit_unet"]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_config(model_key: str) -> dict:
    """Scientific config: IDENTICAL to Phase 20A apart from model identity."""
    spec = MODEL_REGISTRY[model_key]
    return {
        "experiment_id": spec["experiment_id"],
        "phase": PHASE,
        "subphase": SUBPHASE,
        "parent_phase20a_experiment": "phase20_shared_unetpp_fourdomain_seed42_clean_v3",
        "manifest_version": MANIFEST_VERSION,
        "dataset": "MULTI_DOMAIN_ISIC_BUSI_KVASIR_KUB",
        "architecture": spec["architecture"],
        "model": {"name": spec["class_name"], "in_channels": 3, "out_channels": 1,
                  "base_channels": 32},
        "input_channel_policy": "RGB_3CH",
        "input_resolution": 512,
        "loss": {"name": "bce_dice", "bce_weight": 0.5, "dice_weight": 0.5,
                 "dice_epsilon": 1e-6},
        "optimizer": {"name": "AdamW", "learning_rate": 1e-4, "weight_decay": 1e-4},
        "scheduler": {"name": "CosineAnnealingLR", "T_max": 100,
                      "step": "per_epoch_after_train_and_val"},
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
                       "task_id_as_model_input": False, "film": False,
                       "regional_module": False, "localizer": False, "roi_proposal": False},
        "taxonomy_id": None,
    }


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


# --------------------------------------------------------------------------- #
def resolve_model_class(model_key: str):
    spec = MODEL_REGISTRY[model_key]
    if spec["class"] is not None:
        return spec["class"]
    import importlib
    try:
        mod = importlib.import_module(spec["module"])
    except ModuleNotFoundError as exc:
        raise SystemExit(
            f"FAIL CLOSED: model '{model_key}' requires {spec['module']} which does not exist "
            f"({exc}). Do NOT substitute a different architecture."
        )
    return getattr(mod, spec["class_name"])


def fail_closed(model_key: str, reason: str) -> None:
    print(f"FAIL CLOSED [{model_key}]: {reason}", flush=True)
    raise SystemExit(2)


def verify_binding(model_key: str) -> dict:
    """Refuse to train unless the binding + pre-execution check are current."""
    spec = MODEL_REGISTRY[model_key]
    binding_path = BINDING_DIR / f"phase20b_{spec['binding_slug']}_architecture_binding.json"
    check_path = BINDING_DIR / f"phase20b_{spec['binding_slug']}_pre_execution_check.json"

    if not binding_path.exists():
        fail_closed(model_key, f"architecture binding missing: {binding_path.name}")
    binding = json.loads(binding_path.read_text(encoding="utf-8"))
    src = ROOT / binding["repository_implementation"]
    if not src.exists():
        fail_closed(model_key, f"model source missing: {binding['repository_implementation']}")
    observed = sha256_file(src)
    if observed != binding["model_source_sha256"]:
        fail_closed(model_key,
                    f"model source drifted: {binding['repository_implementation']} "
                    f"bound={binding['model_source_sha256'][:16]} observed={observed[:16]}")

    if not check_path.exists():
        fail_closed(model_key, f"pre-execution check missing: {check_path.name}")
    check = json.loads(check_path.read_text(encoding="utf-8"))
    if not check.get("all_checks_passed"):
        fail_closed(model_key,
                    f"pre-execution check NOT passed: failed={check.get('failed_checks')}")

    if sha256_file(PROTOCOL_PATH) != PROTOCOL_SHA256:
        fail_closed(model_key, "frozen Phase-20 protocol SHA256 changed")

    return {"binding_path": str(binding_path.relative_to(ROOT)).replace("\\", "/"),
            "binding_sha256": sha256_file(binding_path),
            "pre_execution_check_path": str(check_path.relative_to(ROOT)).replace("\\", "/"),
            "pre_execution_check_sha256": sha256_file(check_path),
            "model_source_sha256": observed,
            "protocol_sha256": PROTOCOL_SHA256}


# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description="Phase-20B shared four-domain conventional baseline trainer.")
    ap.add_argument("--model-key", required=True, choices=ORDER,
                    help="Which conventional architecture to train (Phase-20 protocol, unchanged).")
    ap.add_argument("--resume", action="store_true",
                    help="Resume the SAME logical run from latest.pt (bit-exact by construction).")
    ap.add_argument("--recover-stale-lock", action="store_true")
    ap.add_argument("--max-epochs", type=int, default=None,
                    help="Operational override for the run loop bound; scientific config unchanged.")
    args = ap.parse_args()

    model_key = args.model_key
    spec = MODEL_REGISTRY[model_key]
    CONFIG = build_config(model_key)
    EXPERIMENT_ID = CONFIG["experiment_id"]

    CKPT_DIR = ROOT / "checkpoints" / EXPERIMENT_ID
    EXP_DIR = ROOT / "experiments" / EXPERIMENT_ID
    HISTORY_PATH = EXP_DIR / "history.csv"

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

    # --- governance preflight (FAIL CLOSED) ----------------------------------
    log(f"PHASE 20B model_key={model_key} display={spec['display_name']}")
    binding_info = verify_binding(model_key)
    log(f"architecture binding verified: {binding_info['binding_path']} "
        f"sha={binding_info['binding_sha256'][:16]} model_src_sha={binding_info['model_source_sha256'][:16]}")
    log(f"pre-execution check verified: {binding_info['pre_execution_check_path']} "
        f"sha={binding_info['pre_execution_check_sha256'][:16]}")

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
    log(f"sampling policy={BALANCED_SAMPLING_POLICY_ID} "
        f"expected={expected_domain_proportions(ds_train.frame['dataset'].tolist())}")

    ModelClass = resolve_model_class(model_key)
    model = ModelClass(in_channels=CONFIG["model"]["in_channels"],
                       out_channels=CONFIG["model"]["out_channels"],
                       base_channels=CONFIG["model"]["base_channels"]).to(device)
    n_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    log(f"model={spec['class_name']} params={n_params:,} "
        f"(one shared parameter set across all four domains)")
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
        "artifact": "phase20b_training_closure",
        "phase": PHASE,
        "subphase": SUBPHASE,
        "model_key": model_key,
        "model_display_name": spec["display_name"],
        "experiment_id": EXPERIMENT_ID,
        "manifest_version": MANIFEST_VERSION,
        "architecture": spec["architecture"],
        "model_class": spec["class_name"],
        "model_source_file": spec["source_file"],
        "model_source_sha256": binding_info["model_source_sha256"],
        "architecture_binding_path": binding_info["binding_path"],
        "architecture_binding_sha256": binding_info["binding_sha256"],
        "pre_execution_check_path": binding_info["pre_execution_check_path"],
        "pre_execution_check_sha256": binding_info["pre_execution_check_sha256"],
        "protocol_sha256": binding_info["protocol_sha256"],
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
        "trainer_path": "scripts/training/train_phase20b_shared_baseline.py",
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
    log(f"TRAINING COMPLETE model={spec['display_name']} best_epoch={best_epoch} "
        f"best_macro={best_macro:.6f} final_epoch={final_epoch} stop_reason={stop_reason}")
    release_lock(EXP_DIR)
    run_log.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
