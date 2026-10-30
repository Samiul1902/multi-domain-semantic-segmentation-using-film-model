"""PHASE-13 PART-1C — frozen best-checkpoint standalone GT-free proposal evaluation.

ONE deterministic full 103-case FULL_FIELD VAL inference pass on frozen best.pt
(epoch 53), at the single frozen proposal configuration 0.10 / 0.20 / 5 / 0.30.

GT never influences proposal generation. GT is used only after proposals exist.

PRIMARY coverage: HISTORICAL_EXECUTING_BBOX_COVERAGE (explicit R2C helper).
SECONDARY: PIXEL_MASK_COMPONENT_COVERAGE (descriptive sensitivity only).

No training. No optimizer. No gradients. No grid. No regional segmentation.
No gate decision. TEST locked.
"""
from __future__ import annotations

import csv
import datetime
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

EXP = "phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_clean_v3"
TABLES = ROOT / "reports" / "tables"
AUDITS = ROOT / "reports" / "audits"
BEST = ROOT / "checkpoints" / EXP / "best.pt"
TOL = 1e-12

EXPECTED = {
    "bbox": {
        "tiny_recall90": 0.6805555555555556,
        "overall_recall90": 0.5986842105263158,
        "mean_roi_area_fraction": 0.004846047236646169,
        "hard_tiny_recovered90": 4,
        "global_empty_images_covered90": 1,
        "multi_component_recall90": 0.5714285714285714,
        "mean_proposals_per_image": 4.796116504854369,
        "overall_recall50": 0.7894736842105263,
        "any_overlap_recall": 0.8486842105263158,
        "mean_coverage": 0.7584022780771768,
    },
    "pixel": {
        "tiny_recall90": 0.6944444444444444,
        "overall_recall90": 0.6644736842105263,
        "hard_tiny_recovered90": 5,
        "global_empty_images_covered90": 1,
        "multi_component_recall90": 0.6224489795918368,
        "overall_recall50": 0.8026315789473685,
        "any_overlap_recall": 0.8486842105263158,
        "mean_coverage": 0.7768993431799454,
    },
    "total_proposals": 494,
}


def _load_runner():
    spec = importlib.util.spec_from_file_location(
        "p13c", ROOT / "scripts" / "training" / "train_phase13_clean_v3_localizer.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    import torch
    import yaml
    from PIL import Image
    from torch.utils.data import DataLoader

    from src.data.kub_localizer_dataset import KUBLocalizerDataset
    from src.data.transforms import SegmentationTransform
    from src.inference.clean_v3_components import (
        assert_component_contract,
        build_clean_v3_val_components,
    )
    from src.inference.clean_v3_coverage import (
        evaluate_historical_bbox_coverage,
        evaluate_pixel_mask_coverage,
    )
    from src.inference.predicted_roi import generate_predicted_rois, union_roi_area_fraction
    from src.models.factory import create_model
    from src.utils.checkpointing import load_training_checkpoint
    from src.utils.device import get_device
    from src.utils.manifest_guard import get_manifest_path, validate_manifest_version_strict
    from src.utils.reproducibility import make_generator, seed_worker, set_seed
    from src.utils.run_lock import acquire_lock, release_lock
    from src.utils.test_lock import verify_test_lock

    runner = _load_runner()
    verify_test_lock(ROOT)
    validate_manifest_version_strict(runner.MANIFEST_VERSION)
    cfg = yaml.safe_load(runner.CONFIG_PATH.read_text(encoding="utf-8"))
    seed = int(cfg["training"]["seed"])
    set_seed(seed, deterministic=True)
    device = get_device(require_cuda=True)

    exp_dir = ROOT / "experiments" / EXP
    acquire_lock(exp_dir, EXP, recover_stale=True)
    try:
        val_ids = set(pd.read_csv(get_manifest_path(runner.MANIFEST_VERSION, "val"))["sample_id"].astype(str))
        val_frame = pd.read_csv(ROOT / cfg["data"]["sample_table_val"])
        val_frame = val_frame[
            val_frame["view_type"].eq("FULL_FIELD") & val_frame["sample_id"].astype(str).isin(val_ids)
        ].reset_index(drop=True)
        assert len(val_frame) == 103, f"VAL cases {len(val_frame)} != 103"

        geo = pd.read_csv(runner.VAL_COMPONENT_TABLE)
        comp_frame = geo[geo["sample_id"].astype(str).isin(val_ids)].reset_index(drop=True)
        hard_keys, empty_ids = runner._load_hard_sets()
        grouped = build_clean_v3_val_components(
            comp_frame, val_frame, hard_tiny_keys=hard_keys, global_empty_ids=empty_ids
        )
        contract = assert_component_contract(
            grouped, hard_tiny_keys=hard_keys, global_empty_ids=empty_ids
        )
        print("contract:", contract)

        sigma = float(cfg["target"]["sigma"])
        val_ds = KUBLocalizerDataset(val_frame, "VAL", runner.INPUT_RESOLUTION, sigma,
                                     heatmap_resolution=runner.HEATMAP_RESOLUTION)
        loader = DataLoader(val_ds, batch_size=int(cfg["training"]["batch_size"]), shuffle=False,
                            num_workers=0, pin_memory=True,
                            generator=make_generator(seed), worker_init_fn=seed_worker)
        model = create_model("kub_localizer", in_channels=1, out_channels=1, base_channels=16,
                             heatmap_resolution=runner.HEATMAP_RESOLUTION).to(device)
        state = load_training_checkpoint(BEST, model, restore_rng=False, map_location=device)
        model_keys = set(model.state_dict().keys())
        ckpt_keys = set(state["model_state"].keys())
        missing = model_keys - ckpt_keys
        unexpected = ckpt_keys - model_keys
        assert not missing and not unexpected, f"missing={missing} unexpected={unexpected}"
        assert int(state["epoch"]) == 53, f"best epoch {state['epoch']} != 53"
        print("checkpoint epoch 53 loaded; missing=0 unexpected=0")

        model.eval()
        transform = SegmentationTransform(runner.INPUT_RESOLUTION, False)
        case_rows, prop_rows, comp_rows = [], [], []
        with torch.inference_mode():
            for batch in loader:
                images = batch["image"].to(device)
                with torch.amp.autocast("cuda"):
                    logits = model(images)
                probs = torch.sigmoid(logits.float()).cpu().numpy()
                for i, sid in enumerate(batch["sample_id"]):
                    sid = str(sid)
                    shape = (int(batch["original_height"][i]), int(batch["original_width"][i]))
                    pm = probs[i, 0]
                    runner._assert_native_geometry(pm)
                    with Image.open(Path(str(batch["image_path"][i]))) as h:
                        native = h.convert("L")
                    _im, _mk, meta = transform(native, Image.new("L", native.size))
                    proposals = runner._generate_proposals_fixed_config(
                        pm, meta, shape, generate_predicted_rois=generate_predicted_rois)
                    comps = grouped[sid]
                    uf, mx = (union_roi_area_fraction(proposals, shape) if proposals else (0.0, 0.0))
                    bbox_cov = evaluate_historical_bbox_coverage(proposals, comps)
                    pix_cov = evaluate_pixel_mask_coverage(proposals, comps)

                    gt_masks = [c["mask"] for c in comps]
                    gt_boxes = [(c["min_y"], c["min_x"], c["max_y"], c["max_x"]) for c in comps]
                    for p in proposals:
                        g = p["crop_geometry"]
                        cy1, cy2, cx1, cx2 = g["clip_y1"], g["clip_y2"], g["clip_x1"], g["clip_x2"]
                        bbox_hits = sum(1 for (y1, x1, y2, x2) in gt_boxes
                                        if not (cy2 <= y1 or y2 + 1 <= cy1 or cx2 <= x1 or x2 + 1 <= cx1))
                        pix_hits = sum(1 for m in gt_masks if m[cy1:cy2, cx1:cx2].sum() > 0)
                        prop_rows.append({
                            "sample_id": sid, "proposal_rank": int(p["rank"]),
                            "proposal_score": float(p["score"]),
                            "clip_y1": cy1, "clip_y2": cy2, "clip_x1": cx1, "clip_x2": cx2,
                            "native_proposal_area": int((cy2 - cy1) * (cx2 - cx1)),
                            "native_image_area": int(shape[0] * shape[1]),
                            "proposal_area_fraction": float(((cy2 - cy1) * (cx2 - cx1)) / (shape[0] * shape[1])),
                            "overlaps_any_gt_bbox": bool(bbox_hits > 0),
                            "overlaps_any_gt_pixel": bool(pix_hits > 0),
                            "number_gt_components_with_any_bbox_overlap": int(bbox_hits),
                            "number_gt_components_with_any_pixel_overlap": int(pix_hits),
                        })

                    for b, px, c in zip(bbox_cov, pix_cov, comps):
                        comp_rows.append({
                            "sample_id": sid, "native_component_id": int(c["component_id"]),
                            "size_stratum": c["size_stratum"], "hard_tiny": bool(c["hard_tiny"]),
                            "global_empty_image": bool(c["global_empty_image"]),
                            "component_pixels": int(c["mask"].sum()),
                            "native_H": c["native_H"], "native_W": c["native_W"],
                            "component_ratio": float(c["mask"].sum()) / (c["native_H"] * c["native_W"]),
                            "bbox_min_y": c["min_y"], "bbox_max_y": c["max_y"],
                            "bbox_min_x": c["min_x"], "bbox_max_x": c["max_x"],
                            "bbox_coverage_fraction": float(b["coverage_fraction"]),
                            "bbox_covered90": bool(b["covered90"]),
                            "bbox_covered50": bool(b["covered50"]),
                            "bbox_any_overlap": bool(b["any_overlap"]),
                            "pixel_coverage_fraction": float(px["coverage_fraction"]),
                            "pixel_covered90": bool(px["covered90"]),
                            "pixel_covered50": bool(px["covered50"]),
                            "pixel_any_overlap": bool(px["any_overlap"]),
                            "bbox_minus_pixel_coverage": float(b["coverage_fraction"]) - float(px["coverage_fraction"]),
                        })

                    strata = {c["size_stratum"] for c in comps}
                    case_rows.append({
                        "sample_id": sid, "native_H": shape[0], "native_W": shape[1],
                        "native_component_count": len(comps),
                        "contains_TINY": "TINY" in strata, "contains_SMALL": "SMALL" in strata,
                        "contains_MEDIUM": "MEDIUM" in strata, "contains_LARGE": "LARGE" in strata,
                        "hard_tiny_image": any(c["hard_tiny"] for c in comps),
                        "global_empty_image": sid in empty_ids,
                        "proposal_count": len(proposals),
                        "proposal_scores": json.dumps([float(p["score"]) for p in proposals]),
                        "proposal_native_boxes": json.dumps([list(p["proposal_bbox"]) for p in proposals]),
                        "proposal_crop_geometry": json.dumps([p["crop_geometry"] for p in proposals], default=str),
                        "proposal_union_area_fraction": float(uf),
                        "max_proposal_area_fraction": float(mx),
                        "bbox_any_component_covered90": any(b["covered90"] for b in bbox_cov),
                        "bbox_all_components_covered90": all(b["covered90"] for b in bbox_cov),
                        "pixel_any_component_covered90": any(p["covered90"] for p in pix_cov),
                        "pixel_all_components_covered90": all(p["covered90"] for p in pix_cov),
                        "bbox_mean_component_coverage": float(np.mean([b["coverage_fraction"] for b in bbox_cov])),
                        "pixel_mean_component_coverage": float(np.mean([p["coverage_fraction"] for p in pix_cov])),
                    })
    finally:
        release_lock(exp_dir, force=True)

    pd.DataFrame(case_rows).to_csv(TABLES / "phase13_part1c_best_checkpoint_case_proposals.csv", index=False)
    pd.DataFrame(prop_rows).to_csv(TABLES / "phase13_part1c_best_checkpoint_proposals.csv", index=False)
    pd.DataFrame(comp_rows).to_csv(TABLES / "phase13_part1c_best_checkpoint_component_coverage.csv", index=False)

    cr = pd.DataFrame(comp_rows)
    print()
    print("cases:", len(case_rows), "| proposals:", len(prop_rows), "| components:", len(comp_rows))
    print("bbox tiny:", cr[cr.size_stratum == "TINY"]["bbox_covered90"].sum(), "/", (cr.size_stratum == "TINY").sum())
    print("bbox overall:", cr["bbox_covered90"].sum(), "/", len(cr))
    print("pixel overall:", cr["pixel_covered90"].sum(), "/", len(cr))
    print("mean proposals/image:", float(np.mean([r["proposal_count"] for r in case_rows])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
