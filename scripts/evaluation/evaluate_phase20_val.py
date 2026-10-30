"""Phase 20 - ONE canonical VAL evaluation of best.pt, with persisted predictions.

Runs exactly one full forward pass over the 808 VAL samples of the four domains.
TEST is never touched.

Persists, per VAL sample, under
``reports/predictions/<experiment_id>/val/<DATASET>/<sample_id>.npz``:

    prob : float16 probability map (H, W) in [0, 1]
    pred : uint8 binary prediction at the frozen threshold

plus a prediction manifest binding every artifact to the checkpoint SHA, the
threshold and the input/preprocessing contract. Persisting predictions is the
explicit lesson from earlier phases, where the absence of saved predictions
forced later safe replays.

Writes
------
reports/predictions/<experiment_id>/val/...            (808 NPZ files)
reports/tables/phase20_per_image_val_metrics.csv       (808 rows)
reports/tables/phase20_prediction_manifest.csv
reports/audits/phase20_prediction_manifest.json
reports/audits/phase20_val_evaluation.json
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

from src.data.loaders import create_loader
from src.data.multidomain_dataset import MultiDomainDataset, harmonized_collate
from src.metrics.evaluation_metrics import assd, hd95, segmentation_metrics, surface_dice
from src.models.unetpp import UNetPlusPlus
from src.utils.device import get_device
from src.utils.test_lock import verify_test_lock

EXPERIMENT_ID = "phase20_shared_unetpp_fourdomain_seed42_clean_v3"
CKPT_DIR = ROOT / "checkpoints" / EXPERIMENT_ID
EXP_DIR = ROOT / "experiments" / EXPERIMENT_ID
PROTOCOL = ROOT / "reports/audits/phase20_shared_global_baseline_protocol.json"
PRED_DIR = ROOT / "reports/predictions" / EXPERIMENT_ID
MANIFEST_DIR = ROOT / "manifests/phase4_v3"
DATASET_ORDER = ["ISIC", "BUSI", "KVASIR", "KUB"]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description="Phase-20 canonical VAL evaluation.")
    ap.add_argument("--allow-partial", action="store_true",
                    help="Diagnostic only: evaluate a subset. NOT used for the canonical run.")
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    size = int(protocol["input_resolution"])
    threshold = float(protocol["evaluation_metrics"]["threshold"])
    policy = protocol["input_representation"]["channel_policy"]
    eval_bs = int(protocol["eval_batch_size"])

    verify_test_lock(str(ROOT))
    closure = json.loads((EXP_DIR / "closure.json").read_text(encoding="utf-8"))
    best_path = CKPT_DIR / "best.pt"
    best_sha = sha256_file(best_path)
    if best_sha != closure["best_checkpoint_sha256"]:
        raise RuntimeError(f"best.pt SHA mismatch: {best_sha} != {closure['best_checkpoint_sha256']}")

    device = get_device(require_cuda=True)
    ck = torch.load(best_path, map_location=device, weights_only=False)
    model = UNetPlusPlus(in_channels=3, out_channels=1, base_channels=32).to(device)
    model.load_state_dict(ck["model_state"])
    model.eval()
    print(f"loaded best.pt epoch={ck['epoch']} best_macro={ck['best_macro_domain_dice']:.6f} sha={best_sha[:16]}")

    ds_val = MultiDomainDataset(MANIFEST_DIR / "val.csv", "VAL", size=size, train=False,
                                channel_policy=policy)
    assert len(ds_val) == 808
    loader = create_loader(ds_val, batch_size=eval_bs, shuffle=False, seed=42, num_workers=2,
                           collate_fn=harmonized_collate)

    val_frame = pd.read_csv(MANIFEST_DIR / "val.csv")
    meta = {r["sample_id"]: r for _, r in val_frame.iterrows()}

    # native GT content hash, computed once per VAL mask (no TEST)
    gt_sha = {sid: sha256_file(Path(r["mask_path"])) for sid, r in meta.items()}

    rows, manifest_rows = [], []
    PRED_DIR.mkdir(parents=True, exist_ok=True)
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
            probs = torch.sigmoid(logits.float()).cpu().numpy()          # (B,1,H,W)
            preds = (probs >= threshold).astype(np.uint8)

            for i, sid in enumerate(sample_ids):
                dsname = str(datasets[i])
                prob = probs[i, 0].astype(np.float16)
                pred = preds[i, 0].astype(np.uint8)
                gt = (masks[i, 0].cpu().numpy() > 0)

                out_dir = PRED_DIR / "val" / dsname
                out_dir.mkdir(parents=True, exist_ok=True)
                npz_path = out_dir / f"{sid}.npz"
                # Self-contained: prob (float16), pred (uint8) and the aligned GT
                # (uint8) so no later phase ever needs to replay preprocessing or
                # re-run inference to recompute a metric.
                np.savez_compressed(npz_path, prob=prob, pred=pred,
                                    gt=gt.astype(np.uint8))

                m = segmentation_metrics(pred, gt)
                h = hd95(pred, gt)
                a = assd(pred, gt)
                sd = surface_dice(pred, gt, tolerance=2.0)
                row = {
                    "sample_id": sid,
                    "dataset": dsname,
                    "task_id": int(task_ids[i]),
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
                }
                rows.append(row)
                manifest_rows.append({
                    "sample_id": sid, "dataset": dsname, "task_id": int(task_ids[i]),
                    "npz_path": str(npz_path.relative_to(ROOT)).replace("\\", "/"),
                    "prob_dtype": "float16", "pred_dtype": "uint8", "gt_dtype": "uint8",
                    "prob_shape": list(prob.shape),
                    "npz_keys": ["prob", "pred", "gt"],
                    "checkpoint_sha256": best_sha,
                    "threshold": threshold,
                    "input_channel_policy": policy,
                    "input_resolution": size,
                    "preprocessing_contract": protocol["preprocessing_contract_id"],
                    "evaluation_contract": protocol["evaluation_contract_id"],
                    "gt_mask_path": str(meta[sid]["mask_path"]),
                    "gt_sha256": gt_sha[sid],
                    "split": "VAL",
                })
                n_done += 1
                if args.limit and n_done >= args.limit:
                    break
            if args.limit and n_done >= args.limit:
                break
            if n_done % 160 < eval_bs:
                print(f"  evaluated {n_done}/808  ({time.time()-t0:.0f}s)")

    per_image = pd.DataFrame(rows)
    per_image_path = ROOT / "reports/tables/phase20_per_image_val_metrics.csv"
    per_image.to_csv(per_image_path, index=False)

    man = pd.DataFrame(manifest_rows)
    man_csv = ROOT / "reports/tables/phase20_prediction_manifest.csv"
    man.to_csv(man_csv, index=False)

    manifest = {
        "artifact": "phase20_prediction_manifest",
        "phase": 20,
        "experiment_id": EXPERIMENT_ID,
        "scope": "VAL only; TEST never read",
        "n_predictions": len(man),
        "per_domain_counts": {k: int(v) for k, v in man.groupby("dataset").size().items()},
        "storage": {"format": "npz (compressed)", "prob_dtype": "float16", "pred_dtype": "uint8",
                    "prob_semantics": "sigmoid probability of foreground, [0,1]",
                    "pred_semantics": f"binary at threshold {threshold}"},
        "binding": {
            "checkpoint_path": f"checkpoints/{EXPERIMENT_ID}/best.pt",
            "checkpoint_sha256": best_sha,
            "checkpoint_epoch": int(ck["epoch"]),
            "threshold": threshold,
            "input_channel_policy": policy,
            "input_resolution": size,
            "preprocessing_contract": protocol["preprocessing_contract_id"],
            "evaluation_contract": protocol["evaluation_contract_id"],
            "manifest_version": protocol["dataset_populations"]["manifest_version"],
        },
        "gt_reference_scheme": "native mask path + sha256 of the native mask file bytes "
                               "(GT identity, not a duplicated copy)",
        "manifest_csv": "reports/tables/phase20_prediction_manifest.csv",
        "manifest_csv_sha256": sha256_file(man_csv),
        "per_image_table": "reports/tables/phase20_per_image_val_metrics.csv",
        "per_image_table_sha256": sha256_file(per_image_path),
        "prediction_root": f"reports/predictions/{EXPERIMENT_ID}/val",
        "allows_future_phases_to_avoid_replay": True,
    }
    (ROOT / "reports/audits/phase20_prediction_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")

    eval_summary = {
        "artifact": "phase20_val_evaluation",
        "phase": 20,
        "experiment_id": EXPERIMENT_ID,
        "canonical_val_inference_runs": 1,
        "val_population": 808,
        "samples_evaluated": int(len(per_image)),
        "domains_evaluated": sorted(per_image["dataset"].unique().tolist()),
        "checkpoint_path": f"checkpoints/{EXPERIMENT_ID}/best.pt",
        "checkpoint_sha256": best_sha,
        "threshold": threshold,
        "per_image_table": "reports/tables/phase20_per_image_val_metrics.csv",
        "per_image_table_sha256": sha256_file(per_image_path),
        "prediction_manifest": "reports/audits/phase20_prediction_manifest.json",
        "prob_maps_persisted": int(len(man)),
        "binary_predictions_persisted": int(len(man)),
        "test_reads": {"test_image_reads": 0, "test_mask_reads": 0,
                       "test_inference": 0, "test_visualization": 0},
        "elapsed_seconds": round(time.time() - t0, 1),
        "partial_mode": bool(args.limit),
    }
    (ROOT / "reports/audits/phase20_val_evaluation.json").write_text(
        json.dumps(eval_summary, indent=2), encoding="utf-8")

    print()
    print(f"evaluated {len(per_image)} VAL samples in {time.time()-t0:.0f}s")
    print("per-domain counts:", eval_summary["domains_evaluated"],
          {k: int(v) for k, v in per_image.groupby("dataset").size().items()})
    print("per-image table:", per_image_path.relative_to(ROOT), sha256_file(per_image_path)[:16])
    print("prediction manifest sha256:",
          sha256_file(ROOT / "reports/audits/phase20_prediction_manifest.json")[:16])
    print("prob maps persisted:", len(man), "| binary predictions persisted:", len(man))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
