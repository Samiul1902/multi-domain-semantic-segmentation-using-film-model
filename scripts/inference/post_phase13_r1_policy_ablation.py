"""POST-PHASE-13 REVISION R1 — bounded selective-acceptance policy ablation.

Compute-efficiency contract: each of the 494 frozen proposals is forwarded ONCE per architecture
(1976 regional crop evaluations total). All seven frozen policies are assembled from the SAME
per-case regional maps.

NO training. NO optimizer. NO localizer inference. NO proposal regeneration. NO oracle rerun.
NO TEST access. NO candidate-family expansion.

Run id: post_phase13_regional_revision_r1_selective_acceptance
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch

PROJECT_ROOT = Path(r"D:\Softfors\jup")
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "notebooks" / "phasewise" / "phase_12_oracle_roi" / "code"))

from scripts.inference.phase13_part1d_predicted_region_inference import (  # noqa: E402
    assert_geometry_invariants,
    parse_proposal_geometry,
    prepare_regional_crop_512,
    proposal_support_mask,
    restore_probability_to_full_native,
)

import phase12_oracle_inference as p12  # noqa: E402

TABLES = PROJECT_ROOT / "reports" / "tables"
AUDITS = PROJECT_ROOT / "reports" / "audits"
RUN_ID = "post_phase13_regional_revision_r1_selective_acceptance"
CACHE = PROJECT_ROOT / "data_cache" / "phase13_part1d_b_predicted_region_clean_v3" / "global_512"
THRESHOLD = 0.5
MODELS = ["unet", "attention_unet", "unetpp", "deeplabv3plus"]
DISPLAY = {"unet": "UNet", "attention_unet": "Attention U-Net",
           "unetpp": "UNet++", "deeplabv3plus": "DeepLabV3+"}
CONFIGS = ["R1-C0", "R1-C1", "R1-C2", "R1-C3", "R1-C4", "R1-C5", "R1-C6"]
DISTINCT = ["R1-C0", "R1-C1", "R1-C2", "R1-C4", "R1-C5", "R1-C6"]  # C3 == C1

BIND = {
    "r1_policy": ("reports/audits/post_phase13_regional_revision_r1_policy_frozen.json",
                  "13d9d95c3bc03776003a3b824eeaf52f2dc8b158ad47e65d238895ce50ba118b"),
    "r0_protocol": ("reports/audits/post_phase13_regional_revision_r0_protocol_frozen.json",
                    "c24ed2cca28740f3d38fdbb9109cae078ef58be571d85b0f421bc47497ea5d6b"),
    "candidate_family": ("reports/tables/post_phase13_regional_revision_r1_candidate_family.csv",
                         "4a6dca9d1333ea7efcb31c6b3b441fa23b12543c62f2992556e5d215712d4c4a"),
    "membership": ("reports/tables/post_phase13_regional_revision_r1_frozen_membership.csv",
                   "c65e3e43038d0ebe7d12c966686e709897a43dd051d9283d099e362ca8e6aa0e"),
    "membership_summary": ("reports/tables/post_phase13_regional_revision_r1_membership_summary.csv",
                           "a4f4ecf4f592405d3e76d06a77c763f70f4ff3380cb23e06d8d3906a8a977594"),
    "phase13_case_model": ("reports/tables/phase13_part1d_predicted_region_case_model_metrics.csv",
                           "53e93982c0235e32568e01fbddbdd858d205077e3e0a50fd69bef992454f2658"),
    "phase13_component_model": ("reports/tables/phase13_part1d_predicted_region_component_model_metrics.csv",
                                "f82e0632898467d32916eb0b71a9fff75818548665477052e2db9b365d313c9d"),
    "part1d_helper": ("scripts/inference/phase13_part1d_predicted_region_inference.py",
                      "8cd7e39814a049a025f706c57ccea0b535a230908a177690d6289318234c6284"),
    "part1c_proposals": ("reports/tables/phase13_part1c_best_checkpoint_proposals.csv",
                         "8c3151a3f1f9a56f0692c6ff2d2171472a777a56e99fa2e474aff8a3478a564a"),
    "part1c_case_proposals": ("reports/tables/phase13_part1c_best_checkpoint_case_proposals.csv",
                              "d25c44ec1361365e261d36458e86e707ad3bcb58cf000763a732605db0f856ed"),
    "part1c_component_coverage": ("reports/tables/phase13_part1c_best_checkpoint_component_coverage.csv",
                                  "2a3623fecbc1fc5dd5a2c2a12fbd6d5e78fe2e123a9c45431ba53ca14e4e4b87"),
    "phase12_case": ("reports/tables/phase12_clean_v3_oracle_case_metrics.csv",
                     "080f158fb8b3e3552ac7854c6d9a116e11564bcefa9efdcdbb3511dba090b436"),
    "global_cache_manifest": ("data_cache/phase13_part1d_b_predicted_region_clean_v3/global_512_manifest.csv",
                              "76e1034d2bc7925260af33826fc19565b2d5ef786c612a7ad71f3bde46fb89a8"),
    "ckpt_unet": ("checkpoints/phase9_kub_unet_baseline_seed42_512_clean_v3/best.pt",
                  "7b955ba86464a2fec2d569ecb6124de1fa9a4e66d0b5d58b267be9a280b4c2c0"),
    "ckpt_attention_unet": ("checkpoints/phase10_kub_attention_unet_seed42_512_clean_v3/best.pt",
                            "a49b19d66e43b57ed082ea6efc0ac10bccf444277abd3540dc68612bf30b88b3"),
    "ckpt_unetpp": ("checkpoints/phase10_kub_unetpp_seed42_512_clean_v3/best.pt",
                    "ec7eb13f32e43af27eab7fc617bd1a2a8fcce1d6651a1b4a3653f3e4d1283269"),
    "ckpt_deeplabv3plus": ("checkpoints/phase10_kub_deeplabv3plus_seed42_512_clean_v3/best.pt",
                           "f519027ba1a3a4d6212d83fecd4379f61f71bc05b0751924b9660da08d597dad"),
}
EXPECT_MEMBERSHIP = {"R1-C0": 494, "R1-C1": 103, "R1-C2": 444, "R1-C3": 103,
                     "R1-C4": 372, "R1-C5": 102, "R1-C6": 337}


def sha(p) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def fast_metrics(gt, pred):
    g = gt.astype(bool); p = pred.astype(bool)
    tp = float((p & g).sum()); fp = float((p & ~g).sum()); fn = float((~p & g).sum()); eps = 1e-7
    return {"dice": (2 * tp + eps) / (2 * tp + fp + fn + eps),
            "iou": (tp + eps) / (tp + fp + fn + eps),
            "precision": (tp + eps) / (tp + fp + eps),
            "recall": (tp + eps) / (tp + fn + eps),
            "tp_pixels": tp, "fp_pixels": fp, "fn_pixels": fn,
            "prediction_empty": bool(p.sum() == 0)}


def load_model_strict(key, device):
    if key == "unet":
        from src.models.unet import UNet as M
    elif key == "attention_unet":
        from src.models.attention_unet import AttentionUNet as M
    elif key == "unetpp":
        from src.models.unetpp import UNetPlusPlus as M
    else:
        from src.models.deeplabv3plus import DeepLabV3Plus as M
    ck = torch.load(PROJECT_ROOT / BIND[f"ckpt_{key}"][0], map_location="cpu", weights_only=False)
    mc = ck["configuration"]["model"]
    model = M(in_channels=mc["input_channels"], out_channels=mc["output_channels"],
              base_channels=mc["base_channels"])
    res = model.load_state_dict(ck["model_state"], strict=True)
    if res.missing_keys or res.unexpected_keys:
        raise RuntimeError(f"{key}: state_dict mismatch {res.missing_keys} {res.unexpected_keys}")
    return model.to(device).eval()


def main() -> dict:
    from src.utils.device import get_device
    from src.metrics.segmentation import hd95
    from PIL import Image

    print("=== provenance gates ===")
    for k, (rel, exp) in BIND.items():
        got = sha(PROJECT_ROOT / rel)
        if got != exp:
            raise RuntimeError(f"BINDING MISMATCH {k}: {got} != {exp}")
    pol = json.loads((AUDITS / "post_phase13_regional_revision_r1_policy_frozen.json").read_text("utf-8"))
    if pol["status"] != "SUPERVISOR_FROZEN_R1_POLICY_READY_FOR_EXECUTION":
        raise RuntimeError("R1 policy status mismatch")
    mem = pd.read_csv(TABLES / "post_phase13_regional_revision_r1_frozen_membership.csv")
    for c, n in EXPECT_MEMBERSHIP.items():
        got = int(mem[(mem.config_id == c) & mem.accepted].shape[0])
        if got != n:
            raise RuntimeError(f"membership total mismatch {c}: {got} != {n}")
    print("all provenance gates PASS")

    accepted = {c: set(map(tuple, mem[(mem.config_id == c) & mem.accepted]
                           [["sample_id", "proposal_rank"]].to_numpy())) for c in CONFIGS}
    if accepted["R1-C1"] != accepted["R1-C3"]:
        raise RuntimeError("C1 membership != C3 membership")

    dev = get_device(require_cuda=True)
    if dev.type != "cuda":
        raise RuntimeError("CPU fallback FORBIDDEN")
    print("device:", dev, torch.cuda.get_device_name(0))

    ff = p12.full_field_frame()
    ff_ids = list(ff["sample_id"])
    gt_by, lab_by, ncomp_by, pre_by = {}, {}, {}, {}
    for _, r in ff.iterrows():
        gt = p12.native_gt(Path(r["mask_path"]))
        lab, n = p12.label(gt > 0, structure=p12.STRUCT8)
        gt_by[r["sample_id"]] = gt; lab_by[r["sample_id"]] = lab
        ncomp_by[r["sample_id"]] = int(n)
        pre_by[r["sample_id"]] = (p12.preprocess_geometry(gt.shape), gt.shape, r["image_path"])
    assert sum(ncomp_by.values()) == 152

    case_tbl = pd.read_csv(TABLES / "phase13_part1c_best_checkpoint_case_proposals.csv")
    prop_geoms = {}
    for r in case_tbl.itertuples():
        shape = (int(r.native_H), int(r.native_W))
        geoms = parse_proposal_geometry({"proposal_crop_geometry": r.proposal_crop_geometry})
        for g in geoms:
            assert_geometry_invariants(g, shape)
        prop_geoms[r.sample_id] = geoms
    assert sum(len(v) for v in prop_geoms.values()) == 494

    # frozen score lookup by (sample_id, proposal_rank)
    prop_tbl = pd.read_csv(TABLES / "phase13_part1c_best_checkpoint_proposals.csv")
    score_of = {(r.sample_id, int(r.proposal_rank)): float(r.proposal_score) for r in prop_tbl.itertuples()}

    # frozen reference tables
    p13 = pd.read_csv(TABLES / "phase13_part1d_predicted_region_case_model_metrics.csv")
    p13_idx = p13.set_index(["model", "sample_id"])
    p13comp = pd.read_csv(TABLES / "phase13_part1d_predicted_region_component_model_metrics.csv")
    p13comp_idx = p13comp.set_index(["model", "sample_id", "native_component_id"])
    p12case = pd.read_csv(TABLES / "phase12_clean_v3_oracle_case_metrics.csv")
    on = p12case[p12case["variant"] == "ORACLE_FLOAT_GLOBAL_RETAINED"].set_index(["model", "sample_id"])
    p1ccomp = pd.read_csv(TABLES / "phase13_part1c_best_checkpoint_component_coverage.csv")
    p1ccomp_idx = p1ccomp.set_index(["sample_id", "native_component_id"])

    rows, comp_rows = [], []
    c0_diffs = {m: {f: 0.0 for f in ("dice", "iou", "precision", "recall")} for m in MODELS}
    c1c3 = {"accepted_ids_equal": True, "fused_probability_equal": True, "binary_prediction_equal": True,
            "metrics_max_abs_diff": 0.0, "component_detection_equal": True}
    crop_counts, hd95_calls, hd95_memo = {}, 0, 0

    for key in MODELS:
        model = load_model_strict(key, dev)
        n_crops = 0
        for sid in ff_ids:
            pre, shape, img_path = pre_by[sid]
            geoms = prop_geoms[sid]
            G = p12.global_native(np.load(CACHE / key / f"{sid}.npy"), pre, shape)
            gray = np.asarray(Image.open(img_path).convert("L"))
            regional = []
            for g in geoms:
                crop = prepare_regional_crop_512(gray, g)
                t = torch.from_numpy(np.ascontiguousarray(crop))[None, None].to(dev)
                with torch.inference_mode():
                    with torch.amp.autocast("cuda", enabled=True):
                        logits = model(t)
                    prob512 = torch.sigmoid(logits).float().squeeze().cpu().numpy().astype(np.float32)
                regional.append(restore_probability_to_full_native(prob512, g, shape))
                n_crops += 1
            del gray

            gt = gt_by[sid]; lab = lab_by[sid]; ncomp = ncomp_by[sid]
            memo = {}
            per = {}
            for cfg in CONFIGS:
                acc = [j for j in range(len(geoms)) if (sid, j + 1) in accepted[cfg]]
                if acc:
                    R = np.maximum.reduce([regional[j] for j in acc])
                    U = proposal_support_mask([geoms[j] for j in acc], shape)
                    P = np.where(U, R, G)
                else:
                    U = np.zeros(shape, dtype=bool)
                    P = G
                pred = P >= THRESHOLD
                m = fast_metrics(gt, pred)
                bk = hashlib.sha256(pred.tobytes()).hexdigest()
                if bk in memo:
                    h = memo[bk]; hd95_memo += 1
                else:
                    hr = hd95(pred, gt.astype(bool)); hd95_calls += 1
                    h = {"hd95": float(hr["hd95"]) if hr["hd95_valid"] else np.nan,
                         "hd95_valid": bool(hr["hd95_valid"]),
                         "hd95_invalid_reason": hr.get("invalid_reason", "")}
                    memo[bk] = h
                per[cfg] = {"m": m, "h": h, "acc": acc, "ufrac": float(U.sum()) / float(shape[0] * shape[1]),
                            "pred": pred, "P": P if cfg in ("R1-C1", "R1-C3") else None}

            ref = p13_idx.loc[(key, sid)]
            for f in ("dice", "iou", "precision", "recall"):
                c0_diffs[key][f] = max(c0_diffs[key][f],
                                       abs(per["R1-C0"]["m"][f] - float(ref[f"predicted_{f}"])))
            a, b = per["R1-C1"], per["R1-C3"]
            if a["acc"] != b["acc"]:
                c1c3["accepted_ids_equal"] = False
            if not np.array_equal(a["P"], b["P"]):
                c1c3["fused_probability_equal"] = False
            if not np.array_equal(a["pred"], b["pred"]):
                c1c3["binary_prediction_equal"] = False
            for f in ("dice", "iou", "precision", "recall", "tp_pixels", "fp_pixels", "fn_pixels"):
                c1c3["metrics_max_abs_diff"] = max(c1c3["metrics_max_abs_diff"],
                                                   abs(a["m"][f] - b["m"][f]))

            # global detection computed from the verified cache (G >= 0.5)
            gpred = G >= THRESHOLD
            gdet = {cid: bool(int((gpred & (lab == cid)).sum()) >= 1) for cid in range(1, ncomp + 1)}
            del gpred

            o = on.loc[(key, sid)]
            for cfg in CONFIGS:
                pc = per[cfg]
                row = {"config_id": cfg, "sample_id": sid, "model": key, "model_display": DISPLAY[key],
                       "accepted_proposal_count": len(pc["acc"]),
                       "accepted_proposal_ranks": ";".join(str(j + 1) for j in pc["acc"]),
                       "accepted_proposal_scores": ";".join(f"{score_of[(sid, j + 1)]:.6f}" for j in pc["acc"]),
                       "accepted_union_area_fraction": pc["ufrac"]}
                for f in ("dice", "iou", "precision", "recall", "tp_pixels", "fp_pixels", "fn_pixels"):
                    row[f"global_{f}"] = float(ref[f"global_{f}"])
                    row[f"oracle_{f}"] = float(o[f])
                    row[f"policy_{f}"] = pc["m"][f]
                row["global_prediction_empty"] = bool(ref["global_prediction_empty"])
                row["oracle_prediction_empty"] = bool(o["prediction_empty"])
                row["policy_prediction_empty"] = pc["m"]["prediction_empty"]
                row["policy_hd95"] = pc["h"]["hd95"]
                row["policy_hd95_valid"] = pc["h"]["hd95_valid"]
                row["policy_hd95_invalid_reason"] = pc["h"]["hd95_invalid_reason"]
                for f in ("dice", "iou", "precision", "recall"):
                    row[f"policy_minus_global_{f}"] = row[f"policy_{f}"] - row[f"global_{f}"]
                    row[f"oracle_minus_global_{f}"] = row[f"oracle_{f}"] - row[f"global_{f}"]
                    row[f"policy_minus_C0_{f}"] = row[f"policy_{f}"] - per["R1-C0"]["m"][f]
                rows.append(row)

            # component rows
            c0det = {cid: bool(int((per["R1-C0"]["pred"] & (lab == cid)).sum()) >= 1)
                     for cid in range(1, ncomp + 1)}
            for cfg in CONFIGS:
                pc = per[cfg]
                r1det = {cid: bool(int((pc["pred"] & (lab == cid)).sum()) >= 1)
                         for cid in range(1, ncomp + 1)}
                for cid in range(1, ncomp + 1):
                    cov = p1ccomp_idx.loc[(sid, cid)]
                    fc = p13comp_idx.loc[(key, sid, cid)]
                    odet = bool(fc["oracle_detected"])
                    cdet = bool(fc["predicted_detected"])
                    comp_rows.append({
                        "config_id": cfg, "model": key, "model_display": DISPLAY[key],
                        "sample_id": sid, "native_component_id": cid,
                        "size_stratum": str(fc["size_stratum"]),
                        "component_pixels": int(fc["component_pixels"]),
                        "hard_tiny": bool(cov["hard_tiny"]),
                        "global_empty_image": bool(cov["global_empty_image"]),
                        "multi_component_image": bool(fc["multi_component_image"]),
                        "part1c_bbox_coverage_fraction": float(cov["bbox_coverage_fraction"]),
                        "part1c_bbox_covered90": bool(cov["bbox_covered90"]),
                        "part1c_bbox_covered50": bool(cov["bbox_covered50"]),
                        "part1c_bbox_any_overlap": bool(cov["bbox_any_overlap"]),
                        "part1c_pixel_coverage_fraction": float(cov["pixel_coverage_fraction"]),
                        "part1c_pixel_covered90": bool(cov["pixel_covered90"]),
                        "part1c_pixel_any_overlap": bool(cov["pixel_any_overlap"]),
                        "global_detected": bool(gdet[cid]),
                        "oracle_detected": odet,
                        "phase13_control_detected": cdet,
                        "r1_policy_detected": bool(r1det[cid]),
                        "GLOBAL_TO_R1_RECOVERY": bool((not gdet[cid]) and r1det[cid]),
                        "GLOBAL_TO_R1_LOSS": bool(gdet[cid] and (not r1det[cid])),
                        "C0_TO_R1_RECOVERY": bool((not c0det[cid]) and r1det[cid]),
                        "C0_TO_R1_LOSS": bool(c0det[cid] and (not r1det[cid])),
                    })
            del regional, per, G
        crop_counts[key] = n_crops
        print(f"  {DISPLAY[key]}: {n_crops} regional crop evaluations", flush=True)
        # incremental persistence so a late failure does not lose completed models
        pd.DataFrame(rows).to_csv(TABLES / "post_phase13_r1_case_model_policy_metrics.csv", index=False)
        pd.DataFrame(comp_rows).to_csv(TABLES / "post_phase13_r1_component_model_policy_metrics.csv", index=False)
        print(f"    incremental rows: case={len(rows)} comp={len(comp_rows)}", flush=True)
        del model
        torch.cuda.empty_cache()

    case_df = pd.DataFrame(rows)
    comp_df = pd.DataFrame(comp_rows)
    case_df.to_csv(TABLES / "post_phase13_r1_case_model_policy_metrics.csv", index=False)
    comp_df.to_csv(TABLES / "post_phase13_r1_component_model_policy_metrics.csv", index=False)

    return {"case_df": case_df, "comp_df": comp_df, "c0_diffs": c0_diffs, "c1c3": c1c3,
            "crop_counts": crop_counts, "hd95_calls": hd95_calls, "hd95_memo": hd95_memo}


if __name__ == "__main__":
    res = main()
    print("\n=== C0 reproduction max abs diffs vs frozen Phase-13 ===")
    for m, d in res["c0_diffs"].items():
        print(f"  {m:<16} " + " ".join(f"{k}={v:.3e}" for k, v in d.items()))
    print("C0 PASS all four (<=1e-6):", all(v["dice"] <= 1e-6 for v in res["c0_diffs"].values()))
    print("C1 vs C3:", res["c1c3"])
    print("crop counts:", res["crop_counts"], "| total:", sum(res["crop_counts"].values()))
    print("hd95 calls:", res["hd95_calls"], "| memo hits:", res["hd95_memo"])
    print("case rows:", len(res["case_df"]), "| comp rows:", len(res["comp_df"]))
