"""Phase 21 — ONE canonical VAL evaluation of the Global MedFiLM reference.

Exactly ONE forward pass over the frozen 808-sample VAL population with
``best.pt``, the frozen threshold / resolution / channel policy, the correct
task ID, and NO test-time augmentation, NO threshold tuning, NO morphology.

Persists, per VAL sample, under
``reports/predictions/<experiment_id>/val/<DATASET>/<sample_id>.npz``:
    prob : float16 foreground probability map
    pred : uint8 binary prediction at the frozen threshold
    gt   : uint8 aligned ground truth

Writes
------
reports/predictions/<experiment_id>/val/...                 (808 NPZ files)
reports/tables/phase21_per_image_val_metrics.csv            (808 rows)
reports/tables/phase21_prediction_manifest.csv
reports/audits/phase21_prediction_manifest.json
reports/audits/phase21_val_evaluation.json

TEST is never touched.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from scripts.training.phase21_common import (
    CKPT_DIR,
    CONFIG,
    EXPERIMENT_ID,
    EXP_DIR,
    MANIFEST_DIR,
    MANIFEST_VERSION,
    PROTOCOL_PATH,
    PROTOCOL_SHA256,
    sha256_file,
)
from src.data.loaders import create_loader
from src.data.multidomain_dataset import DATASET_ORDER, MultiDomainDataset, harmonized_collate
from src.metrics.evaluation_metrics import (
    assd,
    average_precision,
    brier_score,
    expected_calibration_error,
    hd95,
    maximum_calibration_error,
    roc_auc,
    segmentation_metrics,
    surface_dice,
)
from src.models.film import GlobalMedFiLM
from src.utils.device import get_device
from src.utils.test_lock import verify_test_lock

PRED_ROOT = ROOT / "reports" / "predictions" / EXPERIMENT_ID
PER_IMAGE_CSV = ROOT / "reports" / "tables" / "phase21_per_image_val_metrics.csv"
MANIFEST_CSV = ROOT / "reports" / "tables" / "phase21_prediction_manifest.csv"
MANIFEST_JSON = ROOT / "reports" / "audits" / "phase21_prediction_manifest.json"
VAL_EVAL_JSON = ROOT / "reports" / "audits" / "phase21_val_evaluation.json"


def evaluate(limit: int | None = None) -> int:
    proto = json.loads((ROOT / PROTOCOL_PATH).read_text(encoding="utf-8"))
    proto_sha = sha256_file(ROOT / PROTOCOL_PATH)
    assert proto_sha == PROTOCOL_SHA256, "frozen protocol SHA drift"

    size = int(proto["input_resolution"])
    threshold = float(proto["evaluation_metrics"]["threshold"])
    policy = proto["input_representation"]["channel_policy"]
    eval_bs = int(proto["eval_batch_size"])

    verify_test_lock(str(ROOT))
    closure = json.loads((EXP_DIR / "phase21_training_closure.json").read_text(encoding="utf-8"))
    best_path = CKPT_DIR / "best.pt"
    best_sha = sha256_file(best_path)
    if best_sha != closure["best_checkpoint_sha256"]:
        raise RuntimeError(f"best.pt SHA mismatch: {best_sha} != {closure['best_checkpoint_sha256']}")
    if closure.get("stop_reason") not in ("EARLY_STOPPING_PATIENCE", "MAX_EPOCHS"):
        raise RuntimeError(f"training not naturally terminated: {closure.get('stop_reason')}")

    device = get_device(require_cuda=True)
    ck = torch.load(best_path, map_location=device, weights_only=False)
    model = GlobalMedFiLM(
        task_count=CONFIG["model"]["task_count"],
        in_channels=CONFIG["model"]["in_channels"],
        out_channels=CONFIG["model"]["out_channels"],
        channels=tuple(CONFIG["model"]["channels"]),
        task_embedding_dim=CONFIG["model"]["task_embedding_dim"],
        film_hidden_dim=CONFIG["model"]["film_hidden_dim"],
    ).to(device)
    model.load_state_dict(ck["model_state"])
    model.eval()
    print(f"loaded best.pt epoch={ck['epoch']} best_macro={ck['best_macro_domain_dice']:.6f} "
          f"sha={best_sha[:16]}")

    ds_val = MultiDomainDataset(MANIFEST_DIR / "val.csv", "VAL", size=size, train=False,
                                channel_policy=policy)
    assert len(ds_val) == 808, f"VAL population mismatch: {len(ds_val)}"
    loader = create_loader(ds_val, batch_size=eval_bs, shuffle=False, seed=42, num_workers=2,
                           collate_fn=harmonized_collate)

    val_frame = pd.read_csv(MANIFEST_DIR / "val.csv")
    meta = {r["sample_id"]: r for _, r in val_frame.iterrows()}
    gt_sha = {sid: sha256_file(Path(r["mask_path"])) for sid, r in meta.items()}

    rows, manifest_rows = [], []
    PRED_ROOT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    n_done = 0

    with torch.no_grad():
        for batch in loader:
            images = batch["image"].to(device, non_blocking=True)
            masks = batch["mask"].to(device, non_blocking=True)
            task_ids_t = batch["task_id"].to(device, non_blocking=True)
            datasets = batch["dataset"]
            sample_ids = batch["sample_id"]
            task_ids = batch["task_id"].tolist()
            with torch.amp.autocast(device_type=device.type, enabled=True):
                logits = model(images, task_ids_t)
            probs = torch.sigmoid(logits.float()).cpu().numpy()
            preds = (probs >= threshold).astype(np.uint8)

            for i, sid in enumerate(sample_ids):
                dsname = str(datasets[i])
                prob = probs[i, 0].astype(np.float16)
                pred = preds[i, 0].astype(np.uint8)
                gt = (masks[i, 0].cpu().numpy() > 0)

                out_dir = PRED_ROOT / "val" / dsname
                out_dir.mkdir(parents=True, exist_ok=True)
                npz_path = out_dir / f"{sid}.npz"
                np.savez_compressed(npz_path, prob=prob, pred=pred, gt=gt.astype(np.uint8))

                m = segmentation_metrics(pred, gt)
                h = hd95(pred, gt)
                a = assd(pred, gt)
                sd = surface_dice(pred, gt, tolerance=2.0)

                # Probability-based metrics are defined only when both classes exist.
                pf = prob.astype(np.float32).ravel()
                gt_flat = gt.ravel().astype(np.uint8)
                has_both = bool(gt_flat.min() == 0 and gt_flat.max() == 1)
                if has_both:
                    ra = float(roc_auc(gt_flat, pf))
                    ap = float(average_precision(gt_flat, pf))
                    br = float(brier_score(gt_flat, pf))
                    ece = float(expected_calibration_error(gt_flat, pf, n_bins=15))
                    mce = float(maximum_calibration_error(gt_flat, pf, n_bins=15))
                else:
                    ra = ap = br = ece = mce = float("nan")

                rows.append({
                    "sample_id": sid, "dataset": dsname, "task_id": int(task_ids[i]),
                    "model_key": "global_medfilm",
                    "dice": m["dice"], "iou": m["iou"], "precision": m["precision"],
                    "recall": m["recall"], "specificity": m["specificity"],
                    "balanced_accuracy": m["balanced_accuracy"], "mcc": m["mcc"],
                    "accuracy": m["accuracy"], "cohen_kappa": m["cohen_kappa"],
                    "tp": m["tp"], "tn": m["tn"], "fp": m["fp"], "fn": m["fn"],
                    "hd95": h["hd95"], "hd95_valid": h["valid"],
                    "assd": a["assd"], "assd_valid": a["valid"],
                    "surface_dice": sd["surface_dice"], "surface_dice_valid": sd["valid"],
                    "roc_auc": ra, "pr_auc": ap, "brier": br, "ece": ece, "mce": mce,
                    "prob_metrics_valid": has_both,
                    "gt_empty": m["gt_empty"], "pred_empty": m["pred_empty"],
                    "empty_case": m["empty_case"],
                    "gt_foreground_pixels": int(m["foreground_gt"]),
                    "pred_foreground_pixels": int(m["foreground_pred"]),
                    "gt_mask_path": str(meta[sid]["mask_path"]),
                    "gt_sha256": gt_sha[sid],
                })
                manifest_rows.append({
                    "sample_id": sid, "dataset": dsname, "task_id": int(task_ids[i]),
                    "model_key": "global_medfilm",
                    "npz_path": str(npz_path.relative_to(ROOT)).replace("\\", "/"),
                    "prob_dtype": "float16", "pred_dtype": "uint8", "gt_dtype": "uint8",
                    "prob_shape": list(prob.shape), "npz_keys": ["prob", "pred", "gt"],
                    "checkpoint_sha256": best_sha, "threshold": threshold,
                    "input_channel_policy": policy, "input_resolution": size,
                    "preprocessing_contract": proto["preprocessing_contract_id"],
                    "evaluation_contract": proto["evaluation_contract_id"],
                    "gt_mask_path": str(meta[sid]["mask_path"]), "gt_sha256": gt_sha[sid],
                    "split": "VAL",
                })
                n_done += 1
                if limit and n_done >= limit:
                    break
            if limit and n_done >= limit:
                break
            if n_done % 160 < eval_bs:
                print(f"  evaluated {n_done}/808  ({time.time()-t0:.0f}s)")

    per_image = pd.DataFrame(rows)
    PER_IMAGE_CSV.parent.mkdir(parents=True, exist_ok=True)
    per_image.to_csv(PER_IMAGE_CSV, index=False)

    man = pd.DataFrame(manifest_rows)
    man.to_csv(MANIFEST_CSV, index=False)

    manifest = {
        "artifact": "phase21_prediction_manifest",
        "phase": 21,
        "experiment_id": EXPERIMENT_ID,
        "scope": "VAL only; TEST never read",
        "samples_expected": 808,
        "samples_evaluated": int(len(man)),
        "canonical_val_inference_runs": 1,
        "n_predictions": int(len(man)),
        "per_domain_counts": {k: int(v) for k, v in man.groupby("dataset").size().items()},
        "storage": {"format": "npz (compressed)", "prob_dtype": "float16", "pred_dtype": "uint8",
                    "prob_semantics": "sigmoid probability of foreground, [0,1]",
                    "pred_semantics": f"binary at threshold {threshold}"},
        "binding": {
            "checkpoint_path": f"checkpoints/{EXPERIMENT_ID}/best.pt",
            "checkpoint_sha256": best_sha, "checkpoint_epoch": int(ck["epoch"]),
            "threshold": threshold, "input_channel_policy": policy, "input_resolution": size,
            "preprocessing_contract": proto["preprocessing_contract_id"],
            "evaluation_contract": proto["evaluation_contract_id"],
            "manifest_version": MANIFEST_VERSION,
            "frozen_protocol_sha256": proto_sha,
            "task_id_role": "FiLM conditioning only",
        },
        "gt_reference_scheme": "native mask path + sha256 of the native mask file bytes",
        "manifest_csv": str(MANIFEST_CSV.relative_to(ROOT)).replace("\\", "/"),
        "manifest_csv_sha256": sha256_file(MANIFEST_CSV),
        "per_image_table": str(PER_IMAGE_CSV.relative_to(ROOT)).replace("\\", "/"),
        "per_image_table_sha256": sha256_file(PER_IMAGE_CSV),
        "prediction_root": f"reports/predictions/{EXPERIMENT_ID}/val",
        "allows_future_phases_to_avoid_replay": True,
        "test_reads": {"test_image_reads": 0, "test_mask_reads": 0,
                       "test_inference": 0, "test_visualization": 0},
    }
    MANIFEST_JSON.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_JSON.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    val_summary = {
        "artifact": "phase21_val_evaluation",
        "phase": 21,
        "experiment_id": EXPERIMENT_ID,
        "canonical_val_inference_runs": 1,
        "val_population": 808,
        "samples_expected": 808,
        "samples_evaluated": int(len(per_image)),
        "domains_evaluated": sorted(per_image["dataset"].unique().tolist()),
        "checkpoint_path": f"checkpoints/{EXPERIMENT_ID}/best.pt",
        "checkpoint_sha256": best_sha, "threshold": threshold,
        "no_tta": True, "no_threshold_tuning": True, "no_morphology": True,
        "per_image_table": str(PER_IMAGE_CSV.relative_to(ROOT)).replace("\\", "/"),
        "per_image_table_sha256": sha256_file(PER_IMAGE_CSV),
        "prediction_manifest": str(MANIFEST_JSON.relative_to(ROOT)).replace("\\", "/"),
        "prob_maps_persisted": int(len(man)),
        "binary_predictions_persisted": int(len(man)),
        "test_reads": {"test_image_reads": 0, "test_mask_reads": 0,
                       "test_inference": 0, "test_visualization": 0},
        "elapsed_seconds": round(time.time() - t0, 1),
        "partial_mode": bool(limit),
    }
    VAL_EVAL_JSON.write_text(json.dumps(val_summary, indent=2), encoding="utf-8")

    print(f"evaluated {len(per_image)} VAL samples in {time.time()-t0:.0f}s")
    print(f"per-domain counts: "
          f"{ {k: int(v) for k, v in per_image.groupby('dataset').size().items()} }")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Phase-21 canonical VAL evaluation.")
    ap.add_argument("--limit", type=int, default=None,
                    help="Diagnostic only; NOT used for the canonical run.")
    args = ap.parse_args()
    return evaluate(limit=args.limit)


if __name__ == "__main__":
    raise SystemExit(main())
