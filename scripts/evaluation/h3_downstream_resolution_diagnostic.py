"""Resolution/checkpoint diagnostic for the H3 downstream pipeline.

Purpose (diagnostic only — NOT part of the frozen contrast table):
  (a) Reproduce the frozen PREDICTED arm by running the SAME pipeline with the
      bound Phase-13B localizer constructed at the 512 default (as the frozen
      Phase-14 evaluator does). If this reproduces the frozen PREDICTED metrics,
      the downstream evaluator is validated.
  (b) Run the bound Phase-13B localizer at 128 (training-faithful), to isolate the
      localizer heatmap-decode construction effect from the checkpoint effect.

No training. No tuning. TEST closed.
"""
from __future__ import annotations

import hashlib
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image
import torch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.analysis.oracle_roi import extract_gt_components
from src.data.regional_dataset import crop_and_preprocess
from src.data.transforms import SegmentationTransform
from src.inference.kub_predict import _preprocess_image, _restore_original_coordinates
from src.inference.predicted_roi import generate_predicted_rois
from src.inference.regional_evaluator import aggregate_and_fuse, restore_regional_probability
from src.inference.learned_roi_clean_v3 import build_clean_v3_localizer
from src.metrics.object_metrics import object_metrics
from src.models.factory import create_model
from src.models.unet import UNet
from src.utils.checkpointing import load_training_checkpoint
from src.utils.manifest_guard import validate_manifest_version_strict

H3_CKPT = PROJECT_ROOT / "checkpoints" / "h3_kub_localizer_sigma_adaptive_sizeaware_seed42_clean_v3" / "best.pt"
P13B_CKPT = PROJECT_ROOT / "checkpoints" / "phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_clean_v3" / "best.pt"
REFINER_CKPT = PROJECT_ROOT / "checkpoints" / "phase14_kub_refiner_unet_a3_256_seed42_clean_v3" / "best.pt"
GLOBAL_CKPT = PROJECT_ROOT / "checkpoints" / "phase10_kub_unetpp_seed42_512_clean_v3" / "best.pt"

VAL_SAMPLES = PROJECT_ROOT / "reports" / "tables" / "kub_val_samples_sized_clean_v3.csv"
VAL_COMPONENTS = PROJECT_ROOT / "reports" / "tables" / "kub_val_components_sized_clean_v3.csv"
HARD_TINY_SET = PROJECT_ROOT / "reports" / "tables" / "phase13_clean_v3_hard_tiny_replication_set.csv"
GLOBAL_EMPTY_SET = PROJECT_ROOT / "reports" / "tables" / "phase13_clean_v3_global_empty_replication_set.csv"


def dice_binary(p, g, eps=1e-7):
    p, g = p > 0, g > 0
    tp = float((p & g).sum()); fp = float((p & ~g).sum()); fn = float((~p & g).sum())
    return (2 * tp + eps) / (2 * tp + fp + fn + eps)


def run_arm(localizer_ckpt, heatmap_resolution, device, ff_samples, ff_components,
            hard_tiny_set, global_empty_set, global_model, refiner_model, tag):
    print(f"\n===== ARM {tag}: localizer={localizer_ckpt.name} hres={heatmap_resolution} =====")
    if heatmap_resolution == 128:
        localizer = build_clean_v3_localizer(device=device)
        load_training_checkpoint(localizer_ckpt, localizer, restore_rng=False, map_location=device)
    else:
        localizer = create_model("kub_localizer", in_channels=1, out_channels=1,
                                 base_channels=16, heatmap_resolution=heatmap_resolution).to(device)
        load_training_checkpoint(localizer_ckpt, localizer, restore_rng=False, map_location=device)
    localizer.eval()
    loc_transform = SegmentationTransform(512, False)

    recs = []
    with torch.inference_mode():
        for idx, srow in ff_samples.iterrows():
            sid = srow["sample_id"]
            img_path = Path(srow["image_path"]); mask_path = Path(srow["mask_path"])
            with Image.open(img_path) as im:
                raw_img = im.convert("L")
            with Image.open(mask_path) as mf:
                raw_mask_pil = mf.convert("L")
                raw_mask = (np.array(raw_mask_pil) > 0).astype(np.uint8)
            h_img, w_img = raw_mask.shape
            orig_comps, labeled_gt = extract_gt_components(raw_mask)
            sub = ff_components[ff_components["sample_id"] == sid].set_index("component_id")

            t512, _, meta_g = _preprocess_image(raw_img, 512)
            prob512 = torch.sigmoid(global_model(t512.to(device))).squeeze().cpu().numpy()
            prob_orig_g, _ = _restore_original_coordinates(prob512, (prob512 >= 0.5).astype(np.uint8), meta_g)

            dummy = Image.new("L", raw_img.size)
            tensor_loc, _, meta_loc = loc_transform(raw_img, dummy)
            logits = localizer(tensor_loc.unsqueeze(0).to(device))
            heatmap = torch.sigmoid(logits)[0, 0].float().cpu().numpy()
            proposals = generate_predicted_rois(heatmap, meta_loc, (h_img, w_img), 0.10, 0.20, 5, 0.30)

            reg_probs, reg_supps = [], []
            for prop in proposals:
                geom = prop["crop_geometry"]
                crop_img_pil, _ = crop_and_preprocess(raw_img, raw_mask_pil, geom, 256)
                crop_t = torch.from_numpy(np.asarray(crop_img_pil, dtype=np.float32)).unsqueeze(0).unsqueeze(0) / 255.0
                prob_r = torch.sigmoid(refiner_model(crop_t.to(device)))[0, 0].cpu().numpy()
                rest_p, supp = restore_regional_probability(prob_r, geom, (h_img, w_img))
                reg_probs.append(rest_p); reg_supps.append(supp)

            prob_fused = aggregate_and_fuse(prob_orig_g, reg_probs, reg_supps)
            mask_fused = (prob_fused >= 0.5).astype(np.uint8)
            d = dice_binary(mask_fused, raw_mask)

            for c in orig_comps:
                cid = c["component_id"]
                ov = int((mask_fused & (labeled_gt == cid)).sum())
                recs.append({
                    "sample_id": sid, "component_id": cid,
                    "size": sub.loc[cid, "size_stratum"],
                    "rec90": (ov / int(c["component_pixels"])) >= 0.90,
                    "hard": (sid, cid) in hard_tiny_set,
                    "dice": d,
                    "n_prop": len(proposals),
                })
            if (idx + 1) % 40 == 0:
                print(f"  {idx + 1}/{len(ff_samples)}")
    df = pd.DataFrame(recs)
    per_img = df.drop_duplicates("sample_id")
    out = {
        "tag": tag, "mean_dice": float(per_img["dice"].mean()),
        "tiny": float(df[df["size"] == "TINY"]["rec90"].mean()),
        "small": float(df[df["size"] == "SMALL"]["rec90"].mean()),
        "medium": float(df[df["size"] == "MEDIUM"]["rec90"].mean()),
        "large": float(df[df["size"] == "LARGE"]["rec90"].mean()),
        "overall": float(df["rec90"].mean()),
        "hard_tiny": int(df[df["hard"]]["rec90"].sum()),
        "mean_props": float(per_img["n_prop"].mean()),
    }
    print(f"  RESULT {tag}: dice={out['mean_dice']:.6f} tiny={out['tiny']:.6f} small={out['small']:.6f} "
          f"med={out['medium']:.6f} large={out['large']:.6f} overall={out['overall']:.6f} "
          f"hard={out['hard_tiny']}/15 props={out['mean_props']:.4f}")
    return out


def main():
    validate_manifest_version_strict("phase4_v3")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type != "cuda":
        raise RuntimeError("CUDA required")

    df_samples = pd.read_csv(VAL_SAMPLES)
    ff_samples = df_samples[df_samples["view_type"] == "FULL_FIELD"].reset_index(drop=True)
    df_comp = pd.read_csv(VAL_COMPONENTS)
    ff_comp = df_comp[df_comp["view_type"] == "FULL_FIELD"].reset_index(drop=True)
    df_ht = pd.read_csv(HARD_TINY_SET)
    ht = set(zip(df_ht[(df_ht["size_stratum"] == "TINY") & (~df_ht["global_detected"])]["sample_id"],
                 df_ht[(df_ht["size_stratum"] == "TINY") & (~df_ht["global_detected"])]["native_component_id"]))
    df_ge = pd.read_csv(GLOBAL_EMPTY_SET)
    ge = set(df_ge[df_ge["prediction_empty"]]["sample_id"])

    global_model = create_model("unetpp", in_channels=1, out_channels=1, base_channels=32).to(device)
    load_training_checkpoint(GLOBAL_CKPT, global_model, restore_rng=False, map_location=device)
    global_model.eval()
    refiner = UNet(in_channels=1, out_channels=1, base_channels=32).to(device)
    load_training_checkpoint(REFINER_CKPT, refiner, restore_rng=False, map_location=device)
    refiner.eval()

    results = {}
    results["P13B_512"] = run_arm(P13B_CKPT, 512, device, ff_samples, ff_comp, ht, ge, global_model, refiner, "P13B_512")
    results["P13B_128"] = run_arm(P13B_CKPT, 128, device, ff_samples, ff_comp, ht, ge, global_model, refiner, "P13B_128")
    results["H3_128"] = run_arm(H3_CKPT, 128, device, ff_samples, ff_comp, ht, ge, global_model, refiner, "H3_128")
    results["H3_512"] = run_arm(H3_CKPT, 512, device, ff_samples, ff_comp, ht, ge, global_model, refiner, "H3_512")

    import json
    out = PROJECT_ROOT / "reports" / "audits" / "h3_downstream_resolution_diagnostic.json"
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nSaved diagnostic: {out}")
    print("\nFrozen PREDICTED reference: dice=0.418531 tiny=0.791667 small=0.892857 med=1.0 large=0.9375 overall=0.875")


if __name__ == "__main__":
    main()
