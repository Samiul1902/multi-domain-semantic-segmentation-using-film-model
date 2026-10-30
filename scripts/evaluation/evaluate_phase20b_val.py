"""Phase-20B — ONE canonical VAL evaluation per model, with persisted predictions.

Generalises ``scripts/evaluation/evaluate_phase20_val.py`` to any Phase-20B model
key. The methodology is IDENTICAL: one full forward pass over the same 808 VAL
samples, the same frozen threshold / resolution / channel policy, the same
metrics, and the same persisted artifact contract.

TEST is never touched.

Persists, per VAL sample, under
``reports/predictions/<experiment_id>/val/<DATASET>/<sample_id>.npz``:
    prob : float16 probability map
    pred : uint8 binary prediction at the frozen threshold
    gt   : uint8 aligned ground truth

Writes (phase20b_ prefixed; Phase-20A artifacts are untouched)
--------------------------------------------------------------
reports/predictions/<experiment_id>/val/...                      (808 NPZ files)
reports/tables/phase20b_<slug>_per_image_val_metrics.csv         (808 rows)
reports/tables/phase20b_<slug>_prediction_manifest.csv
reports/audits/phase20b_<slug>_prediction_manifest.json
reports/audits/phase20b_<slug>_val_evaluation.json

Usage
-----
    ./.venv/Scripts/python.exe scripts/evaluation/evaluate_phase20b_val.py --model-key unet
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
sys.path.insert(0, str(ROOT / "scripts"))

from phase20b_common import (  # noqa: E402
    MANIFEST_DIR,
    ORDER,
    PROTOCOL_PATH,
    ckpt_dir,
    exp_dir,
    experiment_id,
    per_image_csv,
    pred_root,
    prediction_manifest_csv,
    prediction_manifest_json,
    resolve_model_class,
    val_eval_json,
)
from src.data.loaders import create_loader  # noqa: E402
from src.data.multidomain_dataset import MultiDomainDataset, harmonized_collate  # noqa: E402
from src.metrics.evaluation_metrics import (  # noqa: E402
    assd,
    hd95,
    segmentation_metrics,
    surface_dice,
)
from src.utils.device import get_device  # noqa: E402
from src.utils.test_lock import verify_test_lock  # noqa: E402

DATASET_ORDER = ["ISIC", "BUSI", "KVASIR", "KUB"]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evaluate(model_key: str, limit: int | None = None) -> int:
    exp_id = experiment_id(model_key)
    exp = exp_dir(model_key)
    ckpt = ckpt_dir(model_key)
    pred_dir = pred_root(model_key)

    protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
    size = int(protocol["input_resolution"])
    threshold = float(protocol["evaluation_metrics"]["threshold"])
    policy = protocol["input_representation"]["channel_policy"]
    eval_bs = int(protocol["eval_batch_size"])

    verify_test_lock(str(ROOT))
    closure = json.loads((exp / "closure.json").read_text(encoding="utf-8"))
    best_path = ckpt / "best.pt"
    best_sha = sha256_file(best_path)
    if best_sha != closure["best_checkpoint_sha256"]:
        raise RuntimeError(f"[{model_key}] best.pt SHA mismatch: {best_sha} != {closure['best_checkpoint_sha256']}")

    device = get_device(require_cuda=True)
    ck = torch.load(best_path, map_location=device, weights_only=False)
    ModelClass = resolve_model_class(model_key)
    model = ModelClass(in_channels=3, out_channels=1, base_channels=32).to(device)
    model.load_state_dict(ck["model_state"])
    model.eval()
    print(f"[{model_key}] loaded best.pt epoch={ck['epoch']} "
          f"best_macro={ck['best_macro_domain_dice']:.6f} sha={best_sha[:16]}")

    ds_val = MultiDomainDataset(MANIFEST_DIR / "val.csv", "VAL", size=size, train=False,
                                channel_policy=policy)
    assert len(ds_val) == 808, f"VAL population mismatch: {len(ds_val)}"
    loader = create_loader(ds_val, batch_size=eval_bs, shuffle=False, seed=42, num_workers=2,
                           collate_fn=harmonized_collate)

    val_frame = pd.read_csv(MANIFEST_DIR / "val.csv")
    meta = {r["sample_id"]: r for _, r in val_frame.iterrows()}
    gt_sha = {sid: sha256_file(Path(r["mask_path"])) for sid, r in meta.items()}

    rows, manifest_rows = [], []
    pred_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    n_done = 0

    with torch.no_grad():
        for batch in loader:
            images = batch["image"].to(device, non_blocking=True)
            masks = batch["mask"].to(device, non_blocking=True)
            datasets = batch["dataset"]
            sample_ids = batch["sample_id"]
            task_ids = batch["task_id"].tolist()
            with torch.amp.autocast(device_type=device.type, enabled=True):
                logits = model(images)
            probs = torch.sigmoid(logits.float()).cpu().numpy()
            preds = (probs >= threshold).astype(np.uint8)

            for i, sid in enumerate(sample_ids):
                dsname = str(datasets[i])
                prob = probs[i, 0].astype(np.float16)
                pred = preds[i, 0].astype(np.uint8)
                gt = (masks[i, 0].cpu().numpy() > 0)

                out_dir = pred_dir / "val" / dsname
                out_dir.mkdir(parents=True, exist_ok=True)
                npz_path = out_dir / f"{sid}.npz"
                np.savez_compressed(npz_path, prob=prob, pred=pred, gt=gt.astype(np.uint8))

                m = segmentation_metrics(pred, gt)
                h = hd95(pred, gt)
                a = assd(pred, gt)
                sd = surface_dice(pred, gt, tolerance=2.0)
                rows.append({
                    "sample_id": sid, "dataset": dsname, "task_id": int(task_ids[i]),
                    "model_key": model_key,
                    "dice": m["dice"], "iou": m["iou"], "precision": m["precision"],
                    "recall": m["recall"], "specificity": m["specificity"],
                    "balanced_accuracy": m["balanced_accuracy"], "mcc": m["mcc"],
                    "accuracy": m["accuracy"], "cohen_kappa": m["cohen_kappa"],
                    "tp": m["tp"], "tn": m["tn"], "fp": m["fp"], "fn": m["fn"],
                    "hd95": h["hd95"], "hd95_valid": h["valid"],
                    "assd": a["assd"], "assd_valid": a["valid"],
                    "surface_dice": sd["surface_dice"], "surface_dice_valid": sd["valid"],
                    "gt_empty": m["gt_empty"], "pred_empty": m["pred_empty"],
                    "empty_case": m["empty_case"],
                    "gt_foreground_pixels": int(m["foreground_gt"]),
                    "pred_foreground_pixels": int(m["foreground_pred"]),
                    "gt_mask_path": str(meta[sid]["mask_path"]),
                    "gt_sha256": gt_sha[sid],
                })
                manifest_rows.append({
                    "sample_id": sid, "dataset": dsname, "task_id": int(task_ids[i]),
                    "model_key": model_key,
                    "npz_path": str(npz_path.relative_to(ROOT)).replace("\\", "/"),
                    "prob_dtype": "float16", "pred_dtype": "uint8", "gt_dtype": "uint8",
                    "prob_shape": list(prob.shape), "npz_keys": ["prob", "pred", "gt"],
                    "checkpoint_sha256": best_sha, "threshold": threshold,
                    "input_channel_policy": policy, "input_resolution": size,
                    "preprocessing_contract": protocol["preprocessing_contract_id"],
                    "evaluation_contract": protocol["evaluation_contract_id"],
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
    per_image_path = per_image_csv(model_key)
    per_image.to_csv(per_image_path, index=False)

    man = pd.DataFrame(manifest_rows)
    man_csv = prediction_manifest_csv(model_key)
    man.to_csv(man_csv, index=False)

    manifest = {
        "artifact": "phase20b_prediction_manifest",
        "phase": 20, "subphase": "20B", "model_key": model_key,
        "experiment_id": exp_id,
        "scope": "VAL only; TEST never read",
        "n_predictions": len(man),
        "per_domain_counts": {k: int(v) for k, v in man.groupby("dataset").size().items()},
        "storage": {"format": "npz (compressed)", "prob_dtype": "float16", "pred_dtype": "uint8",
                    "prob_semantics": "sigmoid probability of foreground, [0,1]",
                    "pred_semantics": f"binary at threshold {threshold}"},
        "binding": {
            "checkpoint_path": f"checkpoints/{exp_id}/best.pt",
            "checkpoint_sha256": best_sha, "checkpoint_epoch": int(ck["epoch"]),
            "threshold": threshold, "input_channel_policy": policy, "input_resolution": size,
            "preprocessing_contract": protocol["preprocessing_contract_id"],
            "evaluation_contract": protocol["evaluation_contract_id"],
            "manifest_version": protocol["dataset_populations"]["manifest_version"],
        },
        "gt_reference_scheme": "native mask path + sha256 of the native mask file bytes",
        "manifest_csv": str(man_csv.relative_to(ROOT)).replace("\\", "/"),
        "manifest_csv_sha256": sha256_file(man_csv),
        "per_image_table": str(per_image_path.relative_to(ROOT)).replace("\\", "/"),
        "per_image_table_sha256": sha256_file(per_image_path),
        "prediction_root": f"reports/predictions/{exp_id}/val",
        "allows_future_phases_to_avoid_replay": True,
    }
    prediction_manifest_json(model_key).write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    eval_summary = {
        "artifact": "phase20b_val_evaluation",
        "phase": 20, "subphase": "20B", "model_key": model_key,
        "experiment_id": exp_id,
        "canonical_val_inference_runs": 1,
        "val_population": 808,
        "samples_evaluated": int(len(per_image)),
        "domains_evaluated": sorted(per_image["dataset"].unique().tolist()),
        "checkpoint_path": f"checkpoints/{exp_id}/best.pt",
        "checkpoint_sha256": best_sha, "threshold": threshold,
        "per_image_table": str(per_image_path.relative_to(ROOT)).replace("\\", "/"),
        "per_image_table_sha256": sha256_file(per_image_path),
        "prediction_manifest": str(prediction_manifest_json(model_key).relative_to(ROOT)).replace("\\", "/"),
        "prob_maps_persisted": int(len(man)),
        "binary_predictions_persisted": int(len(man)),
        "test_reads": {"test_image_reads": 0, "test_mask_reads": 0,
                       "test_inference": 0, "test_visualization": 0},
        "elapsed_seconds": round(time.time() - t0, 1),
        "partial_mode": bool(limit),
    }
    val_eval_json(model_key).write_text(json.dumps(eval_summary, indent=2), encoding="utf-8")

    print(f"[{model_key}] evaluated {len(per_image)} VAL samples in {time.time()-t0:.0f}s")
    print(f"[{model_key}] per-domain counts: "
          f"{ {k: int(v) for k, v in per_image.groupby('dataset').size().items()} }")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Phase-20B canonical VAL evaluation.")
    ap.add_argument("--model-key", choices=ORDER, required=True)
    ap.add_argument("--allow-partial", action="store_true",
                    help="Diagnostic only: evaluate a subset. NOT used for the canonical run.")
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    return evaluate(args.model_key, limit=args.limit)


if __name__ == "__main__":
    raise SystemExit(main())
