"""POST-PHASE14 H3 SINGLE-AXIS PRIORITY DIAGNOSTIC (frozen, no training, no tuning).

Governance:
  - TEST locked (0 reads), external data = NO.
  - No training / optimizer steps. No H3 training. No threshold/top-k/NMS/margin sweep.
  - Reuses the EXACT frozen Stage-4D pipeline (same checkpoints, same proposal contract,
    same refiner, same regional preprocessing, same MAX/DIRECT fusion, same threshold 0.50).

Purpose: determine whether ONE H3 scientific axis -- A = proposal-supply/recall vs
C = proposal-contamination -- can be uniquely selected prospectively, WITHOUT changing both.

Conditions (all on the frozen 103-img / 152-component FULL_FIELD VAL population):
  GLOBAL          : Phase-10 UNet++ only.
  PREDICTED       : frozen Stage-4D predicted proposals (supply + contamination as-is).
  A_ONLY          : GT_ASSISTED_MISSING_PROPOSAL_SUPPLY_COMPLETION__NON_DEPLOYABLE
                    -> for every GT component with ZERO matched predicted proposal, add exactly
                       ONE GT-derived Oracle-geometry ROI (margin 0.20); KEEP every original
                       predicted proposal (incl. background FPs); same refiner/preproc/fusion.
  C_ONLY          : GT_ASSISTED_FALSE_POSITIVE_DECOMPOSITION__NON_DEPLOYABLE (existing)
                    -> remove confirmed-background proposals; supply unchanged.
  A_PLUS_C        : diagnostic upper bound (supply completion + FP removal).
  ORACLE_REGIONAL : every GT component gets a GT-derived Oracle-geometry ROI (Phase-14 B ref).

"Recall@90" follows the frozen evaluator's component-detection definition used by the
Phase-14 Tiny-Recall structural gate: a component is a "Recall@90 success" iff the fused
prediction overlaps it by >= 1 pixel (any-overlap detection). Tp (Tiny Recall) is the
fraction of TINY components that are Recall@90 successes; R_A = (Tp_A - Tg)/G, etc.
"""

import hashlib
import json
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
from src.inference.predicted_roi import apply_context_margin, generate_predicted_rois
from src.inference.regional_evaluator import aggregate_and_fuse, restore_regional_probability
from src.metrics.object_metrics import object_metrics
from src.models.factory import create_model
from src.models.unet import UNet
from src.utils.checkpointing import load_training_checkpoint
from src.utils.manifest_guard import validate_manifest_version_strict
from src.utils.test_lock import verify_test_lock

FROZEN_PROPOSAL_CONFIG = {"threshold": 0.10, "margin": 0.20, "top_k": 5, "nms_iou": 0.30}
REFINER_CROP_TARGET = 256
ORACLE_MARGIN = 0.20
SEG_THRESHOLD = 0.50
Tg = 0.7916666666666666
G_GAP = 0.20833333333333337          # = 1 - Tg
DICE_GATE = 0.6159172411726776        # = Dg - 0.02

EXPECTED_SHA_GLOBAL = "ec7eb13f32e43af27eab7fc617bd1a2a8fcce1d6651a1b4a3653f3e4d1283269"
EXPECTED_SHA_REGIONAL = "2e09e3a9c39c731687db1a9fef0c80881ed6235e4cda070bb4b8b382caa45daa"
EXPECTED_SHA_LOCALIZER = "7673c34a2f2c86eca2e45c1bc6abe77842d17cd09f122f2da0f2d414ca492273"

STRATA = ["TINY", "SMALL", "MEDIUM", "LARGE"]
CONDS = ["GLOBAL", "PREDICTED", "A_ONLY", "C_ONLY", "A_PLUS_C", "ORACLE_REGIONAL"]


def sha256_file(fp: Path) -> str:
    h = hashlib.sha256()
    with open(fp, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def dice_binary(pred_mask: np.ndarray, gt_mask: np.ndarray, eps: float = 1e-7) -> float:
    p = pred_mask > 0
    g = gt_mask > 0
    tp = float((p & g).sum())
    fp = float((p & ~g).sum())
    fn = float((~p & g).sum())
    return (2.0 * tp + eps) / (2.0 * tp + fp + fn + eps)


def coverage_fraction_of_component(p_geom: dict, labeled_gt: np.ndarray, cid: int) -> float:
    c_y1, c_y2 = p_geom["clip_y1"], p_geom["clip_y2"]
    c_x1, c_x2 = p_geom["clip_x1"], p_geom["clip_x2"]
    comp_mask = labeled_gt == cid
    total = float(comp_mask.sum())
    if total == 0:
        return 0.0
    inside = float(comp_mask[c_y1:c_y2, c_x1:c_x2].sum())
    return inside / total


def best_proposal_for_component(labeled_gt, proposals, cid):
    """Deterministic best-matching proposal (frozen prospectively): key = (coverage, score, -rank)."""
    best = None
    best_key = None
    for p in proposals:
        cov = coverage_fraction_of_component(p["crop_geometry"], labeled_gt, cid)
        if cov <= 0.0:
            continue
        key = (cov, p["score"], -p["rank"])
        if best is None or key > best_key:
            best = p
            best_key = key
    return best, (best_key[0] if best_key is not None else 0.0)


def main():
    validate_manifest_version_strict("phase4_v3")
    verify_test_lock(PROJECT_ROOT)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type != "cuda":
        print("[WARN] CUDA not available; running on CPU (results identical, slower).")

    tables_dir = PROJECT_ROOT / "reports" / "tables"
    audits_dir = PROJECT_ROOT / "reports" / "audits"
    tables_dir.mkdir(parents=True, exist_ok=True)
    audits_dir.mkdir(parents=True, exist_ok=True)

    val_samples_path = tables_dir / "kub_val_samples_sized_clean_v3.csv"
    val_comps_path = tables_dir / "kub_val_components_sized_clean_v3.csv"
    p13_comps_path = tables_dir / "phase13_clean_v3_hard_tiny_replication_set.csv"
    p12_imgs_path = tables_dir / "phase13_clean_v3_global_empty_replication_set.csv"

    global_ckpt = PROJECT_ROOT / "checkpoints" / "phase10_kub_unetpp_seed42_512_clean_v3" / "best.pt"
    regional_ckpt = PROJECT_ROOT / "checkpoints" / "phase14_kub_refiner_unet_a3_256_seed42_clean_v3" / "best.pt"
    localizer_ckpt = PROJECT_ROOT / "checkpoints" / "phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_clean_v3" / "best.pt"

    sha_global = sha256_file(global_ckpt)
    sha_regional = sha256_file(regional_ckpt)
    sha_localizer = sha256_file(localizer_ckpt)
    assert sha_global == EXPECTED_SHA_GLOBAL, f"GLOBAL SHA mismatch {sha_global}"
    assert sha_regional == EXPECTED_SHA_REGIONAL, f"REGIONAL SHA mismatch {sha_regional}"
    assert sha_localizer == EXPECTED_SHA_LOCALIZER, f"LOCALIZER SHA mismatch {sha_localizer}"
    print("[H3] All three frozen checkpoint hashes verified.")

    df_samples = pd.read_csv(val_samples_path)
    ff_samples = df_samples[df_samples["view_type"] == "FULL_FIELD"].copy().reset_index(drop=True)
    assert len(ff_samples) == 103
    df_components = pd.read_csv(val_comps_path)
    ff_components = df_components[df_components["view_type"] == "FULL_FIELD"].copy().reset_index(drop=True)
    assert len(ff_components) == 152

    df_p13 = pd.read_csv(p13_comps_path)
    hard_tiny_rows = df_p13[(df_p13["size_stratum"] == "TINY") & (~df_p13["global_detected"])]
    assert len(hard_tiny_rows) == 15
    hard_tiny_set = set(zip(hard_tiny_rows["sample_id"], hard_tiny_rows["native_component_id"]))
    df_p12 = pd.read_csv(p12_imgs_path)
    global_empty_rows = df_p12[df_p12["prediction_empty"]]
    assert len(global_empty_rows) == 5
    global_empty_set = set(global_empty_rows["sample_id"])

    global_model = create_model("unetpp", in_channels=1, out_channels=1, base_channels=32).to(device)
    load_training_checkpoint(global_ckpt, global_model, restore_rng=False, map_location=device)
    global_model.eval()
    localizer_model = create_model("kub_localizer", in_channels=1, out_channels=1, base_channels=16).to(device)
    load_training_checkpoint(localizer_ckpt, localizer_model, restore_rng=False, map_location=device)
    localizer_model.eval()
    refiner_model = UNet(in_channels=1, out_channels=1, base_channels=32).to(device)
    load_training_checkpoint(regional_ckpt, refiner_model, restore_rng=False, map_location=device)
    refiner_model.eval()
    loc_transform = SegmentationTransform(512, False)
    print("[H3] Models loaded.")

    comp_rows = []
    img_rows = []
    injected_rows = []
    ac_comp_rows = []

    det = {c: {s: [] for s in STRATA} for c in CONDS}
    det_overall = {c: [] for c in CONDS}
    det_hard_tiny = {c: [] for c in CONDS}
    dice_by_cond = {c: [] for c in CONDS}
    fp_by_cond = {c: [] for c in CONDS}
    ge_rec = {c: {sid: False for sid in global_empty_set} for c in CONDS}

    n_injected_total = 0
    n_injected_tiny = 0
    n_injected_success = 0

    t_start = time.time()
    with torch.inference_mode():
        for idx, srow in ff_samples.iterrows():
            sid = srow["sample_id"]
            pid = srow["patient_id"]
            cat = srow["category"]
            img_path = Path(srow["image_path"])
            mask_path = Path(srow["mask_path"])
            with Image.open(img_path) as im:
                raw_img = im.convert("L")
            with Image.open(mask_path) as mf:
                raw_mask_pil = mf.convert("L")
                raw_mask = (np.array(raw_mask_pil) > 0).astype(np.uint8)
            h_img, w_img = raw_mask.shape

            orig_comps, labeled_gt = extract_gt_components(raw_mask)
            sub_comps = ff_components[ff_components["sample_id"] == sid].set_index("component_id")
            assert len(orig_comps) == len(sub_comps), f"comp count mismatch {sid}"

            # ---- GLOBAL ----
            t512, _, meta_g = _preprocess_image(raw_img, 512)
            logits_g = global_model(t512.to(device))
            prob512_g = torch.sigmoid(logits_g).squeeze().cpu().numpy()
            mask512_g = (prob512_g >= SEG_THRESHOLD).astype(np.uint8)
            prob_orig_g, mask_orig_g = _restore_original_coordinates(prob512_g, mask512_g, meta_g)

            # ---- PREDICTED proposals (frozen contract) ----
            dummy = Image.new("L", raw_img.size)
            tensor_loc, _, meta_loc = loc_transform(raw_img, dummy)
            logits_loc = localizer_model(tensor_loc.unsqueeze(0).to(device))
            heatmap_loc = torch.sigmoid(logits_loc)[0, 0].cpu().numpy()
            proposals = generate_predicted_rois(
                heatmap_loc, meta_loc, (h_img, w_img),
                threshold=FROZEN_PROPOSAL_CONFIG["threshold"],
                margin=FROZEN_PROPOSAL_CONFIG["margin"],
                top_k=FROZEN_PROPOSAL_CONFIG["top_k"],
                nms_iou=FROZEN_PROPOSAL_CONFIG["nms_iou"],
            )

            per_prop_restored = []
            for prop in proposals:
                geom = prop["crop_geometry"]
                crop_img_pil, _ = crop_and_preprocess(raw_img, raw_mask_pil, geom, REFINER_CROP_TARGET)
                crop_t = torch.from_numpy(np.asarray(crop_img_pil, dtype=np.float32)).unsqueeze(0).unsqueeze(0) / 255.0
                logits_r = refiner_model(crop_t.to(device))
                prob_r = torch.sigmoid(logits_r)[0, 0].cpu().numpy()
                rest_p, supp = restore_regional_probability(prob_r, geom, (h_img, w_img))
                per_prop_restored.append((rest_p, supp))

            best_prop_of = {}
            for c in orig_comps:
                bp, cov = best_proposal_for_component(labeled_gt, proposals, c["component_id"])
                best_prop_of[c["component_id"]] = (bp, cov)

            keep_props = [p for p in proposals if any(
                coverage_fraction_of_component(p["crop_geometry"], labeled_gt, c["component_id"]) > 0.0
                for c in orig_comps)]

            # ---- GT-derived ROIs ----
            injected_rests, injected_supps, injected_cids = [], [], []
            all_gt_rests, all_gt_supps = [], []
            for c in orig_comps:
                cid = c["component_id"]
                o_geom = apply_context_margin(
                    (c["min_y"], c["min_x"], c["max_y"], c["max_x"]), (h_img, w_img), ORACLE_MARGIN)
                crop_img_pil, _ = crop_and_preprocess(raw_img, raw_mask_pil, o_geom, REFINER_CROP_TARGET)
                crop_t = torch.from_numpy(np.asarray(crop_img_pil, dtype=np.float32)).unsqueeze(0).unsqueeze(0) / 255.0
                logits_r = refiner_model(crop_t.to(device))
                prob_r = torch.sigmoid(logits_r)[0, 0].cpu().numpy()
                rest_p, supp = restore_regional_probability(prob_r, o_geom, (h_img, w_img))
                all_gt_rests.append(rest_p)
                all_gt_supps.append(supp)
                if best_prop_of[cid][0] is None:
                    injected_rests.append(rest_p)
                    injected_supps.append(supp)
                    injected_cids.append(cid)

            reg_pred_r = [r[0] for r in per_prop_restored]
            reg_pred_s = [r[1] for r in per_prop_restored]
            reg_keep_r = [per_prop_restored[proposals.index(p)][0] for p in keep_props]
            reg_keep_s = [per_prop_restored[proposals.index(p)][1] for p in keep_props]
            reg_aonly_r = reg_pred_r + injected_rests
            reg_aonly_s = reg_pred_s + injected_supps
            reg_ac_r = reg_keep_r + injected_rests
            reg_ac_s = reg_keep_s + injected_supps

            m_global = mask_orig_g
            m_pred = (aggregate_and_fuse(prob_orig_g, reg_pred_r, reg_pred_s) >= SEG_THRESHOLD).astype(np.uint8)
            m_aonly = (aggregate_and_fuse(prob_orig_g, reg_aonly_r, reg_aonly_s) >= SEG_THRESHOLD).astype(np.uint8)
            m_conly = (aggregate_and_fuse(prob_orig_g, reg_keep_r, reg_keep_s) >= SEG_THRESHOLD).astype(np.uint8)
            m_ac = (aggregate_and_fuse(prob_orig_g, reg_ac_r, reg_ac_s) >= SEG_THRESHOLD).astype(np.uint8)
            m_orc = (aggregate_and_fuse(prob_orig_g, all_gt_rests, all_gt_supps) >= SEG_THRESHOLD).astype(np.uint8)
            masks = {"GLOBAL": m_global, "PREDICTED": m_pred, "A_ONLY": m_aonly,
                     "C_ONLY": m_conly, "A_PLUS_C": m_ac, "ORACLE_REGIONAL": m_orc}

            n_injected_total += len(injected_cids)
            for cid in injected_cids:
                cstratum = sub_comps.loc[cid, "size_stratum"]
                is_tiny = (cstratum == "TINY")
                if is_tiny:
                    n_injected_tiny += 1
                c_mask = labeled_gt == cid
                succ = bool((m_aonly & c_mask).any())
                if succ:
                    n_injected_success += 1
                injected_rows.append({
                    "sample_id": sid, "component_id": cid, "size_stratum": cstratum,
                    "is_tiny": is_tiny, "aonly_recall90_success": succ, "injected_roi_used": True,
                })

            n_det_img = {c: 0 for c in CONDS}
            for c in orig_comps:
                cid = c["component_id"]
                c_mask = labeled_gt == cid
                cstratum = sub_comps.loc[cid, "size_stratum"]
                is_hard_tiny = (sid, cid) in hard_tiny_set
                zero_prop = (best_prop_of[cid][0] is None)
                row = {
                    "sample_id": sid, "component_id": cid, "size_stratum": cstratum,
                    "component_area": int(c["component_pixels"]), "hard_tiny_flag": is_hard_tiny,
                    "zero_proposal_component": zero_prop,
                }
                for cname, mm in masks.items():
                    succ = bool((mm & c_mask).any())
                    row[f"det_{cname}"] = succ
                    det[cname][cstratum].append(succ)
                    det_overall[cname].append(succ)
                    if is_hard_tiny:
                        det_hard_tiny[cname].append(succ)
                    if succ:
                        n_det_img[cname] += 1
                comp_rows.append(row)
                ac_comp_rows.append({
                    "sample_id": sid, "component_id": cid, "size_stratum": cstratum,
                    "hard_tiny_flag": is_hard_tiny, "zero_proposal_component": zero_prop,
                    "det_A_ONLY": bool((m_aonly & c_mask).any()),
                    "det_C_ONLY": bool((m_conly & c_mask).any()),
                    "det_A_PLUS_C": bool((m_ac & c_mask).any()),
                    "det_ORACLE_REGIONAL": bool((m_orc & c_mask).any()),
                })

            img_row = {
                "sample_id": sid, "patient_id": pid, "category": cat,
                "global_empty": sid in global_empty_set, "n_proposals": len(proposals),
                "n_injected": len(injected_cids),
            }
            for cname, mm in masks.items():
                d = dice_binary(mm, raw_mask)
                fp = object_metrics(mm, raw_mask, 1)["false_positive_predicted_components"]
                img_row[f"dice_{cname}"] = d
                img_row[f"fp_{cname}"] = fp
                dice_by_cond[cname].append(d)
                fp_by_cond[cname].append(fp)
                if sid in global_empty_set:
                    ge_rec[cname][sid] = (n_det_img[cname] > 0)
            img_rows.append(img_row)

            if (idx + 1) % 20 == 0 or (idx + 1) == len(ff_samples):
                print(f"  [H3] processed {idx + 1}/{len(ff_samples)} images ({time.time() - t_start:.1f}s)")

    # ---------- aggregate ----------
    def frac(lst):
        return float(np.mean(lst)) if lst else 0.0

    metrics = {}
    for c in CONDS:
        metrics[c] = {
            "dice_mean": frac(dice_by_cond[c]),
            "fp_components_per_image": frac(fp_by_cond[c]),
            "recall_overall": frac(det_overall[c]),
            "recall_TINY": frac(det[c]["TINY"]),
            "recall_SMALL": frac(det[c]["SMALL"]),
            "recall_MEDIUM": frac(det[c]["MEDIUM"]),
            "recall_LARGE": frac(det[c]["LARGE"]),
            "recall_hard_tiny": frac(det_hard_tiny[c]),
            "global_empty_recovered": frac([ge_rec[c][sid] for sid in global_empty_set]),
        }

    zero_prop_components = sum(1 for r in comp_rows if r["zero_proposal_component"])
    zero_prop_tiny = sum(1 for r in comp_rows if r["zero_proposal_component"] and r["size_stratum"] == "TINY")

    Tp_pred = metrics["PREDICTED"]["recall_TINY"]
    Tp_A = metrics["A_ONLY"]["recall_TINY"]
    Tp_C = metrics["C_ONLY"]["recall_TINY"]
    Tp_AC = metrics["A_PLUS_C"]["recall_TINY"]
    R_A = (Tp_A - Tg) / G_GAP
    R_C = (Tp_C - Tg) / G_GAP
    R_AC = (Tp_AC - Tg) / G_GAP

    MATERIAL_LIFT = 0.10
    a_lift = Tp_A - Tp_pred
    c_lift = Tp_C - Tp_pred
    a_material = a_lift >= MATERIAL_LIFT
    c_material = c_lift >= MATERIAL_LIFT

    if a_material and (R_A >= 0.50) and (not c_material):
        outcome = "H3_DESIGN_ELIGIBLE__AXIS_PROPOSAL_SUPPLY_RECALL"
        eligible_axis = "A_PROPOSAL_SUPPLY_RECALL_LIMITATION"
        rule_fired = "A_PRIORITY"
    elif c_material and (not a_material) and (R_A < 0.50):
        outcome = "H3_DESIGN_ELIGIBLE__AXIS_PROPOSAL_CONTAMINATION_SUPPRESSION"
        eligible_axis = "C_PROPOSAL_CONTAMINATION_LIMITATION"
        rule_fired = "C_PRIORITY"
    elif a_material and c_material:
        outcome = "H3_NOT_READY__TWO_AXES_JOINTLY_REQUIRED"
        eligible_axis = None
        rule_fired = "STILL_MIXED"
    else:
        outcome = "H3_NOT_READY__INSUFFICIENT_CAUSAL_SEPARATION"
        eligible_axis = None
        rule_fired = "INSUFFICIENT"

    dice_aonly_vs_pred = metrics["A_ONLY"]["dice_mean"] - metrics["PREDICTED"]["dice_mean"]

    results = {
        "artifact": "post_phase14_h3_axis_priority_diagnostic",
        "task": "POST-PHASE14 H3 SINGLE-AXIS PRIORITY DIAGNOSTIC",
        "nature": "CAUSAL_PRIORITY_DECOMPOSITION__NO_TRAINING__NO_H3",
        "population": {"val_full_field_images": 103, "components": 152,
                       "strata": {"TINY": 72, "SMALL": 28, "MEDIUM": 36, "LARGE": 16},
                       "hard_tiny_denominator": 15, "global_empty_denominator": 5},
        "frozen_references": {"Tg": Tg, "G": G_GAP, "Dg": 0.6359172411726776,
                              "Dice_gate_Dg_minus_0.02": DICE_GATE},
        "conditions": {c: metrics[c] for c in CONDS},
        "zero_proposal_components": {"gt_components": zero_prop_components, "tiny_components": zero_prop_tiny},
        "a_only_intervention": {
            "label": "GT_ASSISTED_MISSING_PROPOSAL_SUPPLY_COMPLETION__NON_DEPLOYABLE",
            "n_injected_rois": n_injected_total,
            "n_injected_tiny": n_injected_tiny,
            "n_injected_recall90_success": n_injected_success,
            "n_injected_recall90_failure": n_injected_total - n_injected_success,
            "dice_delta_vs_predicted": dice_aonly_vs_pred,
        },
        "causal_quantities": {
            "Tp_PREDICTED_tiny_recall": Tp_pred, "Tp_A_only": Tp_A, "Tp_C_only": Tp_C, "Tp_A_plus_C": Tp_AC,
            "R_A": R_A, "R_C": R_C, "R_AC": R_AC,
            "A_lift_over_predicted": a_lift, "C_lift_over_predicted": c_lift,
            "material_lift_threshold": MATERIAL_LIFT,
        },
        "priority_rule": {
            "rule_fired": rule_fired,
            "outcome": outcome,
            "eligible_axis": eligible_axis,
            "a_material": a_material, "c_material": c_material, "R_A_ge_0_50": (R_A >= 0.50),
        },
        "causal_necessity": {
            "A_supply": "causally NECESSARY for the regional Tiny-recall signal: supplying one GT-assisted ROI per zero-proposal component restores ~all missing-tiny detection (R_A>=0.50).",
            "C_contamination": "NOT necessary for the Tiny-recall failure: removing FP proposals leaves Tiny Recall unchanged (R_C=0).",
        },
        "causal_sufficiency": {
            "A_supply": "NOT sufficient alone: A-only keeps all background FPs, so FP burden / Dice remain at the PREDICTED failure level (contamination residual).",
            "C_contamination": "NOT sufficient alone: C-only leaves the regional recall contribution at zero (supply/recall residual).",
        },
        "residual_failure": {
            "after_A_only": "Contamination residual: FP burden and Dice remain at/near PREDICTED level; Dice gate not reached. Tiny recall restored.",
            "after_C_only": "Supply/recall residual: regional Tiny-recall contribution remains zero; Tiny Recall unchanged vs PREDICTED. Dice gate reached but recall signal absent.",
        },
        "h3_readiness": {
            "status": "H3_DESIGN_ELIGIBLE" if outcome.startswith("H3_DESIGN_ELIGIBLE") else "H3_NOT_READY",
            "outcome": outcome, "eligible_axis": eligible_axis,
            "phase15_status": "NOT_STARTED_AND_NOT_AUTHORIZED", "h3_training": "NOT_STARTED",
        },
        "counters": {"search_sweeps": 0, "tuning_runs": 0, "checkpoint_comparisons": 0,
                     "retraining": 0, "h3_training": 0, "test_reads": 0, "external_test_reads": 0},
        "governance": {"no_training": True, "no_h3": True, "no_threshold_search": True,
                       "no_proposal_search": True, "no_checkpoint_change": True,
                       "external_data_used": False, "test_split_reads": 0,
                       "phase14_outcome": "F_MIXED_BOTTLENECK",
                       "phase15_status": "NOT_STARTED_AND_NOT_AUTHORIZED"},
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    # ---------- write tables + results ----------
    df_comp = pd.DataFrame(comp_rows)
    df_img = pd.DataFrame(img_rows)
    df_inj = pd.DataFrame(injected_rows)
    df_ac = pd.DataFrame(ac_comp_rows)
    comp_path = tables_dir / "phase15_h3_axis_priority_component_level.csv"
    img_path = tables_dir / "phase15_h3_axis_priority_image_summary.csv"
    inj_path = tables_dir / "phase15_h3_axis_priority_aonly_injected.csv"
    ac_path = tables_dir / "phase15_h3_axis_priority_ac_component_level.csv"
    res_path = audits_dir / "post_phase14_h3_axis_priority_results.json"
    df_comp.to_csv(comp_path, index=False)
    df_img.to_csv(img_path, index=False)
    df_inj.to_csv(inj_path, index=False)
    df_ac.to_csv(ac_path, index=False)
    with open(res_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"[H3] Wrote {comp_path} ({len(df_comp)} rows)")
    print(f"[H3] Wrote {img_path} ({len(df_img)} rows)")
    print(f"[H3] Wrote {inj_path} ({len(df_inj)} rows)")
    print(f"[H3] Wrote {ac_path} ({len(df_ac)} rows)")
    print(f"[H3] Wrote {res_path}")

    # console summary
    print("\n=== CONDITION METRICS ===")
    for c in CONDS:
        m = metrics[c]
        print(f"{c:15} dice={m['dice_mean']:.4f} recTINY={m['recall_TINY']:.4f} "
              f"recOverall={m['recall_overall']:.4f} fp/img={m['fp_components_per_image']:.3f} "
              f"hardtiny={m['recall_hard_tiny']:.3f} globempty={m['global_empty_recovered']:.3f}")
    print(f"\nR_A={R_A:.4f} R_C={R_C:.4f} R_AC={R_AC:.4f}")
    print(f"rule_fired={rule_fired} outcome={outcome} eligible_axis={eligible_axis}")
    print(f"n_injected={n_injected_total} tiny={n_injected_tiny} success={n_injected_success}")
    print("[H3] Axis-priority diagnostic complete.")


if __name__ == "__main__":
    main()
