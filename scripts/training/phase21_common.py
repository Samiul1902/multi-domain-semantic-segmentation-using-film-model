"""Phase 21 — shared configuration + deterministic VAL pass for the Global MedFiLM run.

The scientific values here are INHERITED from the frozen Phase-20 protocol
(``reports/audits/phase20_shared_global_baseline_protocol.json``, SHA
``b74f1f9f...``). The ONLY intentional differences are architectural: the model
is the task-conditioned Global MedFiLM (one shared network + FiLM) instead of
the plain UNet++, and ``task_id`` is therefore an allowed CONDITIONING input.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import torch

from src.data.multidomain_dataset import DATASET_ORDER

ROOT = Path(__file__).resolve().parent.parent.parent

EXPERIMENT_ID = "phase21_global_medfilm_fourdomain_seed42_clean_v3"
PHASE = 21
MANIFEST_VERSION = "phase4_v3"
MANIFEST_DIR = ROOT / "manifests/phase4_v3"

PROTOCOL_SHA256 = "b74f1f9f429adbce374f0306180943b9f373f872e1e69e115b7d17e81414283c"
PROTOCOL_PATH = "reports/audits/phase20_shared_global_baseline_protocol.json"

ARCHITECTURE_ID = "global_medfilm_shared_residual_unet_film5_no_se_no_deep_supervision_v1"

CONFIG = {
    "experiment_id": EXPERIMENT_ID,
    "phase": PHASE,
    "manifest_version": MANIFEST_VERSION,
    "dataset": "MULTI_DOMAIN_ISIC_BUSI_KVASIR_KUB",
    "architecture": ARCHITECTURE_ID,
    "model": {
        "name": "GlobalMedFiLM",
        "task_count": 4,
        "in_channels": 3,
        "out_channels": 1,
        "channels": [24, 48, 96, 192, 256],
        "task_embedding_dim": 32,
        "film_hidden_dim": 64,
        "film_sites": ["bridge", "decoder4", "decoder3", "decoder2", "decoder1"],
        "film_equation": "F_hat = (1 + gamma(t)) * F + beta(t); gamma=tanh(gamma_raw), beta=tanh(beta_raw)",
        "film_output_projection": "zero_initialised__identity_at_init",
        "heads": "ONE shared 1x1 foreground head (no dataset-specific head)",
    },
    "input_channel_policy": "RGB_3CH",
    "input_resolution": 512,
    "loss": {"name": "bce_dice", "bce_weight": 0.5, "dice_weight": 0.5, "dice_epsilon": 1e-6},
    "optimizer": {"name": "AdamW", "learning_rate": 1e-4, "weight_decay": 1e-4},
    "scheduler": {"name": "CosineAnnealingLR", "T_max": 100,
                  "step": "per_epoch_after_train_and_val"},
    "training": {
        "batch_size": 4, "eval_batch_size": 8, "num_workers": 4,
        "persistent_workers": False, "max_epochs": 100, "early_stopping_patience": 15,
        "amp": True, "seed": 42, "gradient_accumulation_steps": 1,
        "effective_batch_size": 4, "threshold": 0.5,
        "sampling_policy": "phase20_domain_balanced_uniform_v1",
        "checkpoint_metric": "phase20_macro_domain_mean_dice_v1",
        "checkpoint_metric_description": "macro-domain mean VAL Dice "
                                          "(unweighted mean of the four per-domain per-image macro Dice)",
        "tie_break": "lower validation loss",
    },
    "augmentation_policy": "src.data.transforms.SegmentationTransform(train=True): horizontal mirror p=0.5, "
                           "rotation +/-5 deg, brightness +/-0.10, contrast +/-0.10; mask NEAREST; VAL disabled",
    "governance": {"allow_test": False, "allow_external": False,
                   "task_id_as_model_input": "CONDITIONING_ALLOWED",
                   "task_id_forbidden_channels": ["mask_path", "foreground", "patient", "case",
                                                  "gt_derived", "kub_category", "object_size_bin",
                                                  "roi_coords"],
                   "film": True, "regional_module": False, "localizer": False,
                   "roi_proposal": False, "benefit_router": False, "test_evaluation": False},
    "taxonomy_id": "kub_size_clean_v3_v1",
}

CKPT_DIR = ROOT / "checkpoints" / EXPERIMENT_ID
EXP_DIR = ROOT / "experiments" / EXPERIMENT_ID
HISTORY_PATH = EXP_DIR / "history.csv"
HISTORY_JSON_PATH = EXP_DIR / "history.json"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# --------------------------------------------------------------------------- #
def per_image_dice_iou_precision_recall(logits: torch.Tensor, masks: torch.Tensor,
                                        threshold: float, eps: float = 1e-7):
    """Per-image binary metrics, one image at a time (identical to Phase 20)."""
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
    """Deterministic VAL pass. task_id is passed ONLY as the FiLM conditioning signal."""
    model.eval()
    losses = []
    acc = {d: {k: [] for k in ("dice", "iou", "precision", "recall")} for d in DATASET_ORDER}
    for batch in loader:
        images = batch["image"].to(device, non_blocking=True)
        masks = batch["mask"].to(device, non_blocking=True)
        task_ids = batch["task_id"].to(device, non_blocking=True)
        datasets = batch["dataset"]
        with torch.amp.autocast(device_type=device.type, enabled=amp):
            logits = model(images, task_ids)
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
