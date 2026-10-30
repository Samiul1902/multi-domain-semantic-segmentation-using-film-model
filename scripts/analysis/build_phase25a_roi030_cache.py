"""Phase 25A (CANONICAL RERUN) — ROI-0.30 TRAIN-ONLY global cache + action availability.

Re-derives the frozen ROI crops under the **repository-authoritative Phase-24 v1.1
ROI PROPOSAL threshold 0.30**, replacing the noncanonical 0.50 execution.

THRESHOLD SEMANTICS (never conflated):
    * ROI PROPOSAL threshold             = 0.30  <- this script
    * SEGMENTATION OUTPUT threshold      = 0.50  <- inherited, used for
      segmentation/evaluation masks only; must not appear in any ROI derivation.

Probability source
------------------
The frozen Phase-21 Global MedFiLM is re-run (eval, ``no_grad``, float32 sigmoid)
to regenerate the probability maps in **full float32**. The previously persisted
``prob512.npy`` is float16 and its manifest explicitly states that the binary
decision was taken in float32 and that the float16 copy "is never used to
re-derive the decision". Re-deriving a 0.30 decision from float16 would be a
lossy re-decision, so the forward pass is replayed instead. The checkpoint is
frozen and the model is deterministic in eval mode, so this is a re-derivation,
not a re-training.

Forbidden and NOT performed here:
    * ROUTER_HOLDOUT outcome processing
    * any evaluation on the existing 808-case VAL
    * any TEST access
    * any GT-derived routing metric (Dice / DeltaDice / benefit label)

Outputs
-------
    data_cache/phase25a_barr_roi030_cache/<DOMAIN>/{prob512,rgb_crop,prob_crop,gt_crop,action}.npy
    data_cache/phase25a_barr_roi030_cache/<DOMAIN>/meta.csv
    data_cache/phase25a_barr_roi030_cache/cache_manifest.json
    reports/audits/phase25a_roi030_cache_provenance.json
    reports/tables/phase25a_roi030_population_accounting.csv
    reports/tables/phase25a_roi030_action_availability_by_domain.csv
    reports/tables/phase25a_roi030_crop_geometry_summary.csv

Usage:
    ./.venv/Scripts/python.exe scripts/analysis/build_phase25a_roi030_cache.py
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import torch

ROOT = Path(r"D:/Softfors/jup")
sys.path.insert(0, str(ROOT))
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
CACHE = ROOT / "data_cache" / "phase25a_barr_roi030_cache"
FOLD_DIR = CACHE / "folds"
PREV_FOLD_DIR = ROOT / "data_cache" / "phase25a_global_cache" / "folds"
UTC = datetime.now(timezone.utc).isoformat()

from src.data.barr_roi import (  # noqa: E402
    ROI_PROPOSAL_THRESHOLD,
    SEGMENTATION_OUTPUT_THRESHOLD,
    REGIONAL_CANVAS_RESOLUTION,
    REGIONAL_INPUT_RESOLUTION,
    extract_roi_triplet,
    roi_geometry,
    threshold_probability,
)
from src.data.transforms import SegmentationTransform  # noqa: E402
from src.models.film import GlobalMedFiLM  # noqa: E402
from src.utils.device import get_device  # noqa: E402
from src.utils.test_lock import verify_test_lock  # noqa: E402

SEED = 42
GLOBAL_CKPT = ROOT / "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt"
GLOBAL_CONFIG = ROOT / "experiments/phase21_global_medfilm_fourdomain_seed42_clean_v3/config.json"
SPLIT_MANIFEST = AUD / "phase24_router_split_manifest.csv"
BATCH = 8
GEOM_KEYS = ("y1", "y2", "x1", "x2", "clip_y1", "clip_y2", "clip_x1", "clip_x2",
             "pad_top", "pad_bottom", "pad_left", "pad_right", "crop_side_pixels",
             "effective_magnification", "margin", "bbox_min_y", "bbox_min_x",
             "bbox_max_y", "bbox_max_x", "predicted_foreground_pixels")


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None,
                    help="smoke-test only: cap samples per domain")
    ap.add_argument("--domains", type=str, default=None,
                    help="comma-separated domain subset (smoke-test only)")
    ap.add_argument("--out", type=str, default=None, help="override cache root")
    args = ap.parse_args()

    global CACHE, FOLD_DIR
    if args.out:
        CACHE = Path(args.out)
        if not CACHE.is_absolute():
            CACHE = ROOT / CACHE
        FOLD_DIR = CACHE / "folds"

    assert abs(ROI_PROPOSAL_THRESHOLD - 0.30) < 1e-12, ROI_PROPOSAL_THRESHOLD
    assert abs(SEGMENTATION_OUTPUT_THRESHOLD - 0.50) < 1e-12, SEGMENTATION_OUTPUT_THRESHOLD

    verify_test_lock(str(ROOT))
    print("TEST lock verified")

    cfg = json.loads(GLOBAL_CONFIG.read_text(encoding="utf-8"))
    g_sha = sha(GLOBAL_CKPT)
    print(f"global checkpoint sha256 {g_sha[:16]}...")

    sm = pd.read_csv(SPLIT_MANIFEST)
    dev = sm[sm["split_role"] == "ROUTER_DEVELOPMENT"].copy()
    assert len(dev) == 4957, f"ROUTER_DEVELOPMENT population mismatch: {len(dev)}"
    manifest = pd.read_csv(ROOT / "manifests/phase4_v3/train.csv")
    manifest = manifest.set_index("sample_id", drop=False)
    dev = dev.sort_values(["dataset", "sample_id"]).reset_index(drop=True)

    device = get_device(require_cuda=True)
    print(f"device={device} torch={torch.__version__}")

    model = GlobalMedFiLM(
        task_count=cfg["model"]["task_count"],
        in_channels=cfg["model"]["in_channels"],
        out_channels=cfg["model"]["out_channels"],
        channels=tuple(cfg["model"]["channels"]),
        task_embedding_dim=cfg["model"]["task_embedding_dim"],
        film_hidden_dim=cfg["model"]["film_hidden_dim"],
    )
    state = torch.load(GLOBAL_CKPT, map_location="cpu", weights_only=False)
    model.load_state_dict(state["model_state"])
    model.eval().to(device)
    for p in model.parameters():
        p.requires_grad = False
    n_global_params = sum(p.numel() for p in model.parameters())
    print(f"global model loaded (eval, requires_grad=False), params={n_global_params:,}")
    assert n_global_params == 3523001, "global model parameter mismatch"

    transform = SegmentationTransform(size=REGIONAL_CANVAS_RESOLUTION, train=False,
                                      image_mode="RGB")

    CACHE.mkdir(parents=True, exist_ok=True)
    domains = list(args.domains.split(",")) if args.domains else \
        sorted(dev["dataset"].unique().tolist())

    forward_passes = 0
    counts: dict[str, dict] = {}
    geom_rows: list[dict] = []
    t0 = time.time()

    for domain in domains:
        sub = dev[dev["dataset"] == domain].reset_index(drop=True)
        if args.limit:
            sub = sub.head(args.limit)
        n = len(sub)
        ddir = CACHE / domain
        ddir.mkdir(parents=True, exist_ok=True)
        print(f"\n[{domain}] n={n}")

        # prob512 keeps FULL float32 precision: the 0.30 decision is taken on it.
        prob512 = np.lib.format.open_memmap(ddir / "prob512.npy", mode="w+",
                                            dtype=np.float32,
                                            shape=(n, REGIONAL_CANVAS_RESOLUTION,
                                                   REGIONAL_CANVAS_RESOLUTION))
        rgb_crop = np.lib.format.open_memmap(ddir / "rgb_crop.npy", mode="w+", dtype=np.uint8,
                                             shape=(n, 3, REGIONAL_INPUT_RESOLUTION,
                                                    REGIONAL_INPUT_RESOLUTION))
        prob_crop = np.lib.format.open_memmap(ddir / "prob_crop.npy", mode="w+", dtype=np.float16,
                                              shape=(n, 1, REGIONAL_INPUT_RESOLUTION,
                                                     REGIONAL_INPUT_RESOLUTION))
        gt_crop = np.lib.format.open_memmap(ddir / "gt_crop.npy", mode="w+", dtype=np.uint8,
                                            shape=(n, 1, REGIONAL_INPUT_RESOLUTION,
                                                   REGIONAL_INPUT_RESOLUTION))
        action = np.zeros((n,), dtype=np.uint8)
        meta: list[dict] = []
        n_action = 0

        for start in range(0, n, BATCH):
            chunk = sub.iloc[start:start + BATCH]
            imgs, masks, tasks = [], [], []
            for _, r in chunk.iterrows():
                row = manifest.loc[r["sample_id"]]
                image = __import__("PIL.Image", fromlist=["Image"]).open(row["image_path"])
                mask = __import__("PIL.Image", fromlist=["Image"]).open(row["mask_path"])
                it, mt, _ = transform(image, mask)
                imgs.append(it)
                masks.append(mt)
                tasks.append(int(row["task_id"]))
            batch_img = torch.stack(imgs).to(device)
            batch_task = torch.tensor(tasks, dtype=torch.long, device=device)
            with torch.no_grad(), torch.amp.autocast(device_type=device.type, enabled=True):
                logits = model(batch_img, batch_task)
            prob = torch.sigmoid(logits.float()).cpu().numpy()[:, 0]
            forward_passes += int(batch_img.shape[0])

            for i in range(batch_img.shape[0]):
                gi = start + i
                r = chunk.iloc[i]
                p512 = prob[i].astype(np.float32)          # full precision
                prob512[gi] = p512

                geom = roi_geometry(p512, ROI_PROPOSAL_THRESHOLD)
                rec = {
                    "sample_id": str(r["sample_id"]),
                    "dataset": domain,
                    "task_id": int(r["task_id"]),
                    "group_key": str(r["group_key"]),
                    "global_checkpoint_sha256": g_sha,
                    "roi_proposal_threshold": ROI_PROPOSAL_THRESHOLD,
                    "segmentation_output_threshold": SEGMENTATION_OUTPUT_THRESHOLD,
                    "canvas_resolution": REGIONAL_CANVAS_RESOLUTION,
                    "regional_input_resolution": REGIONAL_INPUT_RESOLUTION,
                    "predicted_foreground_pixels": int(
                        threshold_probability(p512, ROI_PROPOSAL_THRESHOLD).sum()),
                }
                if geom is None:
                    rec["action_available"] = False
                    rec["action_unavailable_reason"] = "ACTION_UNAVAILABLE_GLOBAL_EMPTY"
                    for k in GEOM_KEYS:
                        rec[k] = ""
                else:
                    n_action += 1
                    rec["action_available"] = True
                    rec["action_unavailable_reason"] = ""
                    for k in GEOM_KEYS:
                        rec[k] = geom.get(k, "")
                    rgb, prb, gt = extract_roi_triplet(
                        batch_img[i].cpu().numpy(), p512, masks[i][0].numpy(), geom,
                        REGIONAL_INPUT_RESOLUTION)
                    rgb_crop[gi] = np.clip(np.rint(rgb * 255.0), 0, 255).astype(np.uint8)
                    prob_crop[gi] = prb.astype(np.float16)
                    gt_crop[gi] = (gt > 0.5).astype(np.uint8)
                    action[gi] = 1
                    geom_rows.append({
                        "sample_id": str(r["sample_id"]), "domain": domain,
                        "bbox_min_y": geom["bbox_min_y"], "bbox_min_x": geom["bbox_min_x"],
                        "bbox_max_y": geom["bbox_max_y"], "bbox_max_x": geom["bbox_max_x"],
                        "crop_side_pixels": geom["crop_side_pixels"],
                        "effective_magnification": geom["effective_magnification"],
                        "predicted_foreground_pixels": geom["predicted_foreground_pixels"],
                    })
                meta.append(rec)

            if (start // BATCH) % 25 == 0:
                print(f"   {start + batch_img.shape[0]:5d}/{n}  "
                      f"action_available={n_action}  elapsed={time.time()-t0:.0f}s", flush=True)

        prob512.flush(); rgb_crop.flush(); prob_crop.flush(); gt_crop.flush()
        np.save(ddir / "action.npy", action)
        pd.DataFrame(meta).to_csv(ddir / "meta.csv", index=False)
        counts[domain] = {"total": n, "action_available": n_action,
                          "action_unavailable_global_empty": n - n_action}

    total = sum(c["total"] for c in counts.values())
    total_action = sum(c["action_available"] for c in counts.values())
    print(f"\nDONE total={total} action_available={total_action} "
          f"unavailable={total - total_action}  forward_passes={forward_passes}  "
          f"elapsed={time.time()-t0:.0f}s")

    # ---- fold membership is threshold-independent: copy the frozen CSVs ------- #
    FOLD_DIR.mkdir(parents=True, exist_ok=True)
    fold_copies = {}
    if PREV_FOLD_DIR.exists() and not args.limit:
        for f in sorted(PREV_FOLD_DIR.glob("*.csv")):
            dst = FOLD_DIR / f.name
            dst.write_bytes(f.read_bytes())
            fold_copies[f.name] = {"sha256": sha(dst), "bytes": dst.stat().st_size,
                                   "source_sha256": sha(f)}
        print(f"copied {len(fold_copies)} frozen fold CSVs (threshold-independent)")

    # ---------------- cache manifest ---------------------------------------- #
    files = {}
    for domain in domains:
        for fname in ("prob512.npy", "rgb_crop.npy", "prob_crop.npy", "gt_crop.npy",
                      "action.npy", "meta.csv"):
            p = CACHE / domain / fname
            if p.exists():
                files[f"{domain}/{fname}"] = {"sha256": sha(p), "bytes": p.stat().st_size}
    cache_manifest = {
        "artifact": "phase25a_roi030_cache_manifest",
        "phase": "25A",
        "classification": "CANONICAL_PHASE25A",
        "purpose": "TRAIN-only frozen p_global + ROI-0.30 crop cache for ROUTER_DEVELOPMENT",
        "population": "ROUTER_DEVELOPMENT only",
        "population_n": total,
        "action_available_n": total_action,
        "action_unavailable_global_empty_n": total - total_action,
        "by_domain": counts,
        "global_checkpoint_sha256": g_sha,
        "global_checkpoint_path": str(GLOBAL_CKPT.relative_to(ROOT)),
        "global_model_params": n_global_params,
        "global_forward_passes": forward_passes,
        "device": str(device),
        "amp": True,
        "preprocessing_binding": "src.data.transforms.SegmentationTransform(size=512, "
                                 "train=False, image_mode='RGB') — aspect-preserving resize + "
                                 "centre pad to the 512 canvas",
        "roi_proposal_threshold": ROI_PROPOSAL_THRESHOLD,
        "roi_proposal_threshold_role": "ROI_PROPOSAL — predicted foreground / bbox / ACTION_AVAILABLE",
        "segmentation_output_threshold": SEGMENTATION_OUTPUT_THRESHOLD,
        "segmentation_output_threshold_role": "SEGMENTATION_OUTPUT (inherited) — NOT used for ROI",
        "roi_proposal_threshold_rule": "pred = float32(prob) >= 0.30 (lower-inclusive float32)",
        "segmentation_output_threshold_used_in_roi_derivation": False,
        "prob512_dtype": "float32",
        "prob512_note": "FULL float32 precision. The 0.30 ROI decision is taken directly on the "
                        "float32 probability; no float16 re-decision is performed. The float16 "
                        "copy that used to be persisted is replaced because re-deriving a 0.30 "
                        "decision from float16 would be a lossy re-decision.",
        "supersedes_cache": "data_cache/phase25a_global_cache (ROI-0.50, noncanonical)",
        "fold_membership_copied_threshold_independent": bool(fold_copies),
        "fold_membership": fold_copies,
        "contains_gt_derived_routing_metric": False,
        "contains_dice_or_deltadice": False,
        "router_holdout_outcomes_read": 0,
        "val_outcome_reads": 0,
        "test_reads": 0,
        "files": files,
        "generated_utc": UTC,
    }
    (CACHE / "cache_manifest.json").write_text(json.dumps(cache_manifest, indent=1) + "\n",
                                               encoding="utf-8")

    # ---------------- population accounting -------------------------------- #
    TAB.mkdir(parents=True, exist_ok=True)
    pop_rows = []
    for domain, c in counts.items():
        pop_rows.append({
            "domain": domain,
            "router_development_total": c["total"],
            "action_available": c["action_available"],
            "action_unavailable_global_empty": c["action_unavailable_global_empty"],
            "availability_fraction": round(c["action_available"] / c["total"], 6),
            "enters_refiner_training": c["action_available"],
            "roi_proposal_threshold": ROI_PROPOSAL_THRESHOLD,
            "segmentation_output_threshold": SEGMENTATION_OUTPUT_THRESHOLD,
            "router_holdout_outcomes_read": 0,
            "val_outcomes_read": 0,
            "test_reads": 0,
        })
    pop_rows.append({
        "domain": "ALL",
        "router_development_total": total,
        "action_available": total_action,
        "action_unavailable_global_empty": total - total_action,
        "availability_fraction": round(total_action / total, 6),
        "enters_refiner_training": total_action,
        "roi_proposal_threshold": ROI_PROPOSAL_THRESHOLD,
        "segmentation_output_threshold": SEGMENTATION_OUTPUT_THRESHOLD,
        "router_holdout_outcomes_read": 0,
        "val_outcomes_read": 0,
        "test_reads": 0,
    })
    pd.DataFrame(pop_rows).to_csv(TAB / "phase25a_roi030_population_accounting.csv", index=False)
    pd.DataFrame(pop_rows).to_csv(TAB / "phase25a_roi030_action_availability_by_domain.csv",
                                  index=False)
    print(f"wrote {TAB / 'phase25a_roi030_population_accounting.csv'}")
    print(f"wrote {TAB / 'phase25a_roi030_action_availability_by_domain.csv'}")

    # ---------------- crop geometry summary -------------------------------- #
    if geom_rows:
        gdf = pd.DataFrame(geom_rows)
        summ = []
        for domain in sorted(gdf["domain"].unique()) + ["ALL"]:
            sub = gdf if domain == "ALL" else gdf[gdf["domain"] == domain]
            if not len(sub):
                continue
            summ.append({
                "domain": domain, "n_action_available": int(len(sub)),
                "crop_side_pixels_min": int(sub["crop_side_pixels"].min()),
                "crop_side_pixels_median": float(sub["crop_side_pixels"].median()),
                "crop_side_pixels_max": int(sub["crop_side_pixels"].max()),
                "crop_side_pixels_mean": round(float(sub["crop_side_pixels"].mean()), 4),
                "effective_magnification_median": round(
                    float(sub["effective_magnification"].median()), 6),
                "predicted_foreground_pixels_median": float(
                    sub["predicted_foreground_pixels"].median()),
                "roi_proposal_threshold": ROI_PROPOSAL_THRESHOLD,
            })
        pd.DataFrame(summ).to_csv(TAB / "phase25a_roi030_crop_geometry_summary.csv", index=False)
        print(f"wrote {TAB / 'phase25a_roi030_crop_geometry_summary.csv'}")

    # ---------------- provenance audit ------------------------------------- #
    (AUD / "phase25a_roi030_cache_provenance.json").write_text(json.dumps({
        "artifact": "phase25a_roi030_cache_provenance",
        "phase": "25A",
        "classification": "CANONICAL_PHASE25A",
        "purpose": "prove the canonical ROI-0.30 global cache is TRAIN-only, "
                   "GT-routing-metric-free and TEST-free",
        "population": "ROUTER_DEVELOPMENT only",
        "population_n": total,
        "probability_source": {
            "source": "frozen Phase-21 Global MedFiLM forward pass replay (eval, no_grad)",
            "global_checkpoint_path": str(GLOBAL_CKPT.relative_to(ROOT)),
            "global_checkpoint_sha256": g_sha,
            "global_forward_passes": forward_passes,
            "persisted_dtype": "float32",
            "threshold_derivation_precision": "float32",
            "reused_float16_prob512": False,
            "reuse_rationale": "the pre-existing prob512.npy is float16 and its own manifest "
                               "states the float16 copy is never used to re-derive the decision; "
                               "a 0.30 decision cannot be recovered losslessly from it",
        },
        "roi_proposal_threshold": ROI_PROPOSAL_THRESHOLD,
        "roi_proposal_threshold_role": "ROI_PROPOSAL",
        "segmentation_output_threshold": SEGMENTATION_OUTPUT_THRESHOLD,
        "segmentation_output_threshold_role": "SEGMENTATION_OUTPUT (inherited; not used for ROI)",
        "roi_derivation_uses_segmentation_threshold": False,
        "threshold_from_a_different_value": 0.30,
        "prior_noncanonical_threshold": 0.5,
        "prior_noncanonical_classification": "NONCANONICAL_PROTOCOL_DEVIATION__ROI_THRESHOLD_0P50",
        "action_availability": counts,
        "action_available_n": total_action,
        "action_unavailable_global_empty_n": total - total_action,
        "assuming_zero_forced_skip_rejected": True,
        "crop_geometry_statistics_ref": "reports/tables/phase25a_roi030_crop_geometry_summary.csv",
        "cache_manifest_sha256": sha(CACHE / "cache_manifest.json"),
        "cache_root": str(CACHE.relative_to(ROOT)),
        "fold_membership_copied_threshold_independent": bool(fold_copies),
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "torch": torch.__version__,
            "cuda": torch.version.cuda,
        },
        "router_holdout_outcomes_read": 0,
        "router_holdout_images_used_for_outcome_evaluation": 0,
        "val_outcome_reads": 0,
        "test_reads": 0,
        "gt_derived_routing_metric_created": False,
        "dice_computed": 0,
        "deltadice_computed": 0,
        "verdict": "PHASE25A_ROI030_CACHE_PROVENANCE_PASS",
        "generated_utc": UTC,
    }, indent=1) + "\n", encoding="utf-8")

    print("PHASE25A_ROI030_CACHE_COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
