"""Phase 14 clean-v3 — GLOBAL reference generator (§6, ADDITIVE).

Generates Tg_clean_v3 and Dg_clean_v3 ONCE from the frozen clean_v3 GLOBAL UNet++
checkpoint on the exact 103-image FULL_FIELD clean_v3 VAL population. Writes
reports/audits/phase14_clean_v3_global_reference_freeze.json and FROZENS it.

Governance:
- No Oracle/Predicted computation (this is the GLOBAL-ONLY reference step).
- No TEST reads, no external data, no training.
- Tg/Dg are NOT hardcoded; they are measured here and frozen.
- Must NOT be re-run for favorability after this freeze.

Preprocessing / metric semantics are copied VERBATIM from the v2-era
scripts/evaluation/evaluate_phase14_diagnostic.py (preserve metric/fusion semantics).
"""
import hashlib
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image
import torch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(PROJECT_ROOT))

from src.analysis.oracle_roi import extract_gt_components
from src.inference.kub_predict import _preprocess_image, _restore_original_coordinates
from src.models.factory import create_model
from src.models.unet import UNet
from src.utils.checkpointing import load_training_checkpoint
from src.utils.manifest_guard import validate_manifest_version_strict

TABLES = PROJECT_ROOT / "reports" / "tables"
AUDITS = PROJECT_ROOT / "reports" / "audits"
GLOBAL_CKPT = PROJECT_ROOT / "checkpoints" / "phase10_kub_unetpp_seed42_512_clean_v3" / "best.pt"
EXPECTED_GLOBAL_SHA = "ec7eb13f32e43af27eab7fc617bd1a2a8fcce1d6651a1b4a3653f3e4d1283269"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def dice_binary(pred_mask, gt_mask, eps=1e-7):
    p = pred_mask > 0
    g = gt_mask > 0
    tp = float((p & g).sum())
    fp = float((p & ~g).sum())
    fn = float((~p & g).sum())
    return (2.0 * tp + eps) / (2.0 * tp + fp + fn + eps)


def main():
    validate_manifest_version_strict("phase4_v3")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type != "cuda":
        raise RuntimeError("CUDA is required for the Phase-14 clean-v3 reference generation.")

    # ---- Population (frozen clean_v3 executable tables) ----
    df_samples = pd.read_csv(TABLES / "kub_val_samples_sized_clean_v3.csv")
    df_components = pd.read_csv(TABLES / "kub_val_components_sized_clean_v3.csv")
    ff_samples = df_samples[df_samples["view_type"] == "FULL_FIELD"].copy().reset_index(drop=True)
    ff_components = df_components[df_components["view_type"] == "FULL_FIELD"].copy().reset_index(drop=True)
    assert len(ff_samples) == 103, f"expected 103, got {len(ff_samples)}"
    assert len(ff_components) == 152, f"expected 152, got {len(ff_components)}"

    # ---- Verify checkpoint SHA before inference ----
    sha_global = sha256_file(GLOBAL_CKPT)
    assert sha_global == EXPECTED_GLOBAL_SHA, f"GLOBAL SHA mismatch: {sha_global}"

    # ---- Load GLOBAL model ----
    global_model = create_model("unetpp", in_channels=1, out_channels=1, base_channels=32).to(device)
    load_training_checkpoint(GLOBAL_CKPT, global_model, restore_rng=False, map_location=device)
    global_model.eval()

    n_images = len(ff_samples)
    image_dices = []
    tiny_success = []
    tiny_total = 0
    forward_count = 0
    t_start = time.time()

    with torch.inference_mode():
        for idx, srow in ff_samples.iterrows():
            sid = srow["sample_id"]
            img_path = Path(srow["image_path"])
            mask_path = Path(srow["mask_path"])
            with Image.open(img_path) as im:
                raw_img = im.convert("L")
            with Image.open(mask_path) as mf:
                raw_mask = (np.array(mf.convert("L")) > 0).astype(np.uint8)
            h_img, w_img = raw_mask.shape

            orig_comps, labeled_gt = extract_gt_components(raw_mask)
            sub_comps = ff_components[ff_components["sample_id"] == sid].set_index("component_id")
            assert len(orig_comps) == len(sub_comps), f"component mismatch {sid}"

            t512, _, meta_g = _preprocess_image(raw_img, 512)
            logits_g = global_model(t512.to(device))
            prob512_g = torch.sigmoid(logits_g).squeeze().cpu().numpy()
            mask512_g = (prob512_g >= 0.50).astype(np.uint8)
            prob_orig_g, mask_orig_g = _restore_original_coordinates(prob512_g, mask512_g, meta_g)
            forward_count += 1

            image_dices.append(dice_binary(mask_orig_g, raw_mask))

            for c in orig_comps:
                cid = c["component_id"]
                c_mask = labeled_gt == cid
                c_pixels = int(c["component_pixels"])
                c_stratum = sub_comps.loc[cid, "size_stratum"]
                ov_g = int((mask_orig_g & c_mask).sum())
                det_g = ov_g >= 1
                if c_stratum == "TINY":
                    tiny_success.append(1 if det_g else 0)
                    tiny_total += 1

            if (idx + 1) % 20 == 0 or (idx + 1) == n_images:
                print(f"  reference GLOBAL: {idx + 1}/{n_images}")

    Dg = float(np.mean(image_dices))
    Tg = float(np.mean(tiny_success)) if tiny_total > 0 else 0.0
    elapsed = time.time() - t_start

    # ---- Evaluator SHA (this generator + the forthcoming main evaluator) ----
    gen_sha = sha256_file(Path(__file__))
    main_eval_path = PROJECT_ROOT / "scripts" / "evaluation" / "evaluate_phase14_clean_v3_diagnostic.py"
    main_eval_sha = sha256_file(main_eval_path) if main_eval_path.exists() else None

    # key dependencies that define metric/fusion semantics
    deps = {
        "src/analysis/oracle_roi.py": sha256_file(PROJECT_ROOT / "src" / "analysis" / "oracle_roi.py"),
        "src/inference/kub_predict.py": sha256_file(PROJECT_ROOT / "src" / "inference" / "kub_predict.py"),
        "src/models/unet.py": sha256_file(PROJECT_ROOT / "src" / "models" / "unet.py"),
        "src/models/factory.py": sha256_file(PROJECT_ROOT / "src" / "models" / "factory.py"),
        "src/utils/checkpointing.py": sha256_file(PROJECT_ROOT / "src" / "utils" / "checkpointing.py"),
        "reports/tables/kub_val_samples_sized_clean_v3.csv": sha256_file(TABLES / "kub_val_samples_sized_clean_v3.csv"),
        "reports/tables/kub_val_components_sized_clean_v3.csv": sha256_file(TABLES / "kub_val_components_sized_clean_v3.csv"),
    }

    ref = {
        "artifact": "phase14_clean_v3_global_reference_freeze",
        "status": "FROZEN",
        "generation_timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "references": {
            "Tg_clean_v3": Tg,
            "Dg_clean_v3": Dg,
        },
        "derivation": {
            "checkpoint": "checkpoints/phase10_kub_unetpp_seed42_512_clean_v3/best.pt",
            "checkpoint_sha256": sha_global,
            "population": "103 FULL_FIELD KUB VAL images (phase4_v3) via reports/tables/kub_val_samples_sized_clean_v3.csv",
            "Tg_definition": "GLOBAL_ONLY Tiny Recall@90 = mean over TINY components of (global mask >=1px overlap) — identical semantics to v2-era evaluate_phase14_diagnostic.py",
            "Dg_definition": "GLOBAL_ONLY mean Dice over the 103-image FULL_FIELD VAL population",
            "preprocessing": "resize 512, sigmoid, threshold 0.50, restore to native coordinates (verbatim v2)",
            "NOT_used": "val_macro_dice = 0.7641601653354622 (all-view-types macro; not the FULL_FIELD mean-dice reference)",
        },
        "population_counts": {
            "val_samples": n_images,
            "authoritative_components": len(ff_components),
            "tiny_components": tiny_total,
        },
        "forward_count": forward_count,
        "elapsed_seconds": round(elapsed, 2),
        "evaluator_sha256": {
            "reference_generator": gen_sha,
            "main_evaluator": main_eval_sha,
        },
        "dependency_sha256": deps,
        "governance_locks": {
            "test_split_reads": 0,
            "external_test_reads": 0,
            "external_data_used": False,
            "training_executed": False,
        },
        "governance_note": (
            "Generated ONCE and FROZEN. Tg/Dg are population-dependent clean_v3 GLOBAL references. "
            "No favorability-driven rerun permitted. The §8 three-contrast diagnostic MUST read these "
            "frozen values; it must not recompute or overwrite them (a deterministic verification "
            "recompute inside the main evaluator is allowed but must agree within 1e-6)."
        ),
    }

    out = AUDITS / "phase14_clean_v3_global_reference_freeze.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(ref, f, indent=2)

    print("=" * 60)
    print("PHASE 14 clean-v3 GLOBAL REFERENCE GENERATION (§6)")
    print("=" * 60)
    print(f"Dg_clean_v3 (FULL_FIELD mean Dice): {Dg:.6f}")
    print(f"Tg_clean_v3 (Tiny Recall@90):       {Tg:.6f}")
    print(f"forward_count: {forward_count} | elapsed: {elapsed:.1f}s")
    print(f"Wrote FROZEN reference: {out}")
    print("=" * 60)


if __name__ == "__main__":
    main()
