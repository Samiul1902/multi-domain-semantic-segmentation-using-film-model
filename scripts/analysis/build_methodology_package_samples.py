"""
Build representative real image samples for the RA-MedFiLM-BARR methodology
diagram evidence package.

GOVERNANCE (ZERO-EXECUTION):
  * NO model construction, NO checkpoint load, NO forward, NO CUDA.
  * Panels 01/02/03 copy EXISTING frozen raw VAL808 input + GT files.
  * Panels 04 (p_global) and 07 (final prob) are read from EXISTING frozen
    Phase29/Phase27 VAL808 caches (already-computed outputs).
  * Panel 05 (ROI proposal) is DRAWN as a rectangle over the input using the
    EXISTING frozen Phase29 GT-free ROI geometry (threshold 0.30, margin 0.25).
  * Panel 06 (regional refinement) = NOT_AVAILABLE_WITHOUT_NEW_MODEL_EXECUTION.
  * TEST and ROUTER_HOLDOUT are NOT touched.
"""
import csv, json, os, hashlib
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(r"D:\Softfors\jup")
PKG = ROOT / "reports" / "figures" / "methodology_diagram_package"
SAMPLES = PKG / "representative_samples"

VAL_CSV = ROOT / "manifests" / "phase4_v3" / "val.csv"
GLOBAL_PROB = ROOT / "data_cache" / "phase29_val808_shared_fixed_g_v1_1_canonical" / "val808_global_prob_f16.npy"
ROI_GEOM = ROOT / "data_cache" / "phase29_val808_shared_fixed_g_v1_1_canonical" / "val808_roi_geometry.json"
FINAL_PROB = ROOT / "data_cache" / "phase27_barr_preservation_v1_0" / "phase27_val808_final_prob_f16.npy"

TASK_ID = {"ISIC": 0, "BUSI": 1, "KVASIR": 2, "KUB": 3}
DOMAIN_META = {
    "ISIC":   {"full": "ISIC 2018 (Task 1 skin lesion)", "modality": "dermoscopy (RGB)", "target": "skin lesion"},
    "BUSI":   {"full": "BUSI-WHU Breast Cancer Ultrasound", "modality": "ultrasound (L->RGB)", "target": "breast lesion"},
    "KVASIR": {"full": "Kvasir-SEG", "modality": "endoscopy (RGB)", "target": "colorectal polyp"},
    "KUB":    {"full": "KUB-Stone (X-ray)", "modality": "radiograph (L/RGB)", "target": "kidney/bladder/ureteric stone"},
}

def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()

def load_rows():
    with open(VAL_CSV, encoding="utf-8") as f:
        return list(csv.DictReader(f))

def pick_representative(rows):
    """Ordinary (median-index) sample per domain; KUB prefers a neutral Kidney_Stone row."""
    picks = {}
    for dom in ["ISIC", "BUSI", "KVASIR", "KUB"]:
        sub = [r for r in rows if r["dataset"] == dom]
        if dom == "KUB":
            # neutral-ish: prefer a Kidney_Stone row near the middle (documented separately)
            ks = [r for r in sub if r.get("category") == "Kidney_Stone"]
            pool = ks if ks else sub
            picks[dom] = pool[len(pool) // 2]
        else:
            picks[dom] = sub[len(sub) // 2]
    return picks

def to_uint8_arr(x):
    x = np.asarray(x, dtype=np.float32)
    x = np.clip(x, 0.0, 1.0)
    return (x * 255.0 + 0.5).astype(np.uint8)

def main():
    rows = load_rows()
    order = json.load(open(ROOT/"data_cache"/"phase29_val808_shared_fixed_g_v1_1_canonical"/"val808_roi_geometry.json", encoding="utf-8"))["sample_id_order"]
    sid_index = {s: i for i, s in enumerate(order)}

    gp = np.load(GLOBAL_PROB)            # (808,512,512) float16  -- EXISTING frozen cache
    fp = np.load(FINAL_PROB)             # (808,512,512) float16  -- EXISTING frozen cache
    geom = json.load(open(ROI_GEOM, encoding="utf-8"))["geometry"]

    picks = pick_representative(rows)
    summary = {}
    new_inference = False

    for dom, row in picks.items():
        d = SAMPLES / dom
        d.mkdir(parents=True, exist_ok=True)
        sid = row["sample_id"]
        img_p = Path(row["image_path"]); msk_p = Path(row["mask_path"])
        rec = {
            "sample_id": sid,
            "domain": dom,
            "task_id": int(row["task_id"]),
            "category": row.get("category", "NOT_AVAILABLE"),
            "split": row.get("split", "VAL"),
            "source_manifest": "manifests/phase4_v3/val.csv",
            "new_inference_performed": False,
        }

        # 01 input (copy-as-is; convert to png for embedding)
        img = Image.open(img_p).convert("RGB")
        img.save(d / "01_input.png")
        rec["01_input"] = {"availability": "AVAILABLE", "kind": "frozen VAL808 raw input",
                           "original_path": str(img_p), "size": list(img.size)}

        # 02 ground truth
        gt = Image.open(msk_p).convert("L")
        gt.save(d / "02_ground_truth.png")
        rec["02_ground_truth"] = {"availability": "AVAILABLE", "kind": "frozen VAL808 raw GT",
                                  "original_path": str(msk_p), "size": list(gt.size)}

        # 03 overlay (input + GT contour)
        W, H = img.size
        gt_r = gt.resize((W, H), Image.NEAREST)
        ga = np.array(gt_r)
        mask = ga > 0
        ov = np.array(img).copy()
        # outline via simple dilation-difference
        m = mask.astype(np.uint8)
        pad = np.pad(m, 1, mode="edge")
        dil = np.zeros_like(m)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                dil |= pad[1+dy:1+dy+m.shape[0], 1+dx:1+dx+m.shape[1]]
        edge = (dil.astype(bool)) & (~mask)
        ov[edge] = [255, 0, 0]
        Image.fromarray(ov).save(d / "03_input_gt_overlay.png")
        rec["03_input_gt_overlay"] = {"availability": "AVAILABLE",
                                      "kind": "DERIVED (input + GT boundary), no model"}

        # index into frozen array
        idx = sid_index.get(sid)

        # 04 global probability (EXISTING frozen cache)
        if idx is not None:
            pg = gp[idx].astype(np.float32)
            Image.fromarray((np.clip(pg, 0, 1) * 255 + 0.5).astype(np.uint8)).resize((W, H)).save(d / "04_global_probability.png")
            rec["04_global_probability"] = {"availability": "AVAILABLE",
                "kind": "EXISTING frozen Phase29 canonical p_global cache (no new inference)",
                "source": "data_cache/phase29_val808_shared_fixed_g_v1_1_canonical/val808_global_prob_f16.npy",
                "array_index": int(idx)}
            # 07 final segmentation (EXISTING frozen cache)
            pf = fp[idx].astype(np.float32)
            Image.fromarray((np.clip(pf, 0, 1) * 255 + 0.5).astype(np.uint8)).resize((W, H)).save(d / "07_final_segmentation.png")
            rec["07_final_segmentation"] = {"availability": "AVAILABLE",
                "kind": "EXISTING frozen Phase27 final fused probability cache (no new inference)",
                "source": "data_cache/phase27_barr_preservation_v1_0/phase27_val808_final_prob_f16.npy",
                "array_index": int(idx)}
        else:
            rec["04_global_probability"] = {"availability": "NOT_AVAILABLE_WITHOUT_NEW_MODEL_EXECUTION"}
            rec["07_final_segmentation"] = {"availability": "NOT_AVAILABLE_WITHOUT_NEW_MODEL_EXECUTION"}

        # 05 ROI proposal drawn from EXISTING frozen GT-free geometry
        if sid in geom:
            g = geom[sid]
            vis = Image.open(img_p).convert("RGB").resize((W, H))
            dr = ImageDraw.Draw(vis)
            dr.rectangle([g["x1"], g["y1"], g["x2"], g["y2"]], outline=(255, 0, 0), width=max(2, W // 200))
            vis.save(d / "05_roi_proposal.png")
            rec["05_roi_proposal"] = {"availability": "AVAILABLE",
                "kind": "EXISTING frozen GT-free ROI geometry drawn over the input (no new inference)",
                "source": "data_cache/phase29_val808_shared_fixed_g_v1_1_canonical/val808_roi_geometry.json",
                "roi_box": [g["x1"], g["y1"], g["x2"], g["y2"]],
                "roi_proposal_threshold": 0.30, "roi_fractional_margin": 0.25}
        else:
            rec["05_roi_proposal"] = {"availability": "NOT_AVAILABLE_WITHOUT_NEW_MODEL_EXECUTION"}

        # 06 regional refinement (NOT cached as an image -> omit)
        rec["06_regional_refinement"] = {"availability": "NOT_AVAILABLE_WITHOUT_NEW_MODEL_EXECUTION",
            "reason": "No frozen per-sample refined-probability image cache exists; rendering would require a new R_psi forward."}

        rec["why_selected"] = ("Ordinary median-index VAL808 sample for this domain; NOT a best-result/cherry-picked case. "
                               "KUB picks a Kidney_Stone row near the domain median (subgroup is reporting metadata only).")
        rec["input_is"] = "raw VAL808 input image"
        rec["gt_is"] = "raw VAL808 ground-truth mask (binarized for overlay)"
        rec["cache_or_existing_output"] = True
        (d / "sample_metadata.json").write_text(json.dumps(rec, indent=2), encoding="utf-8")
        summary[dom] = rec

    (PKG / "_sample_build_summary.json").write_text(json.dumps(
        {"new_inference_performed": new_inference,
         "domains": {k: {"sample_id": v["sample_id"], "task_id": v["task_id"], "category": v["category"]} for k, v in summary.items()}},
        indent=2), encoding="utf-8")
    print("built samples:", list(summary.keys()))
    for k, v in summary.items():
        print(" ", k, v["sample_id"], "task", v["task_id"], "cat", v["category"])

if __name__ == "__main__":
    main()
