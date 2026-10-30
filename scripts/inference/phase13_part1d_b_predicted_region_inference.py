"""PHASE-13 PART-1D-B — four-model predicted-region segmentation inference.

Stage G : GLOBAL_NATIVE reproduction for all four frozen architectures (one deterministic
          103-case pass each) + FLOAT32 512-space global probability cache.
Gate    : per-case native Dice reproduction vs the frozen Phase-12 GLOBAL_NATIVE rows,
          tolerance 1e-4. STOP -> CHECK_REQUIRED on failure (regional inference not run).
Stage R : PREDICTED_REGION_FLOAT_GLOBAL_RETAINED inference over the 494 frozen GT-free
          Part-1C proposals per architecture, using the R1 square/padding crop-restore helpers.

NOT performed: training, optimizer creation, localizer inference, proposal regeneration,
proposal tuning, config grid, oracle rerun, gate verdict, TEST access.

Run id: phase13_part1d_b_predicted_region_clean_v3
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
    EXPECTED_CASE_MODEL_ROWS,
    EXPECTED_COMPONENT_MODEL_ROWS,
    MODELS,
    THRESHOLD,
    assert_geometry_invariants,
    parse_proposal_geometry,
    prepare_regional_crop_512,
    proposal_support_mask,
    restore_probability_to_full_native,
)

import phase12_oracle_inference as p12  # noqa: E402  (read-only authoritative reference)

TABLES = PROJECT_ROOT / "reports" / "tables"
AUDITS = PROJECT_ROOT / "reports" / "audits"
RUN_ID = "phase13_part1d_b_predicted_region_clean_v3"
CACHE = PROJECT_ROOT / "data_cache" / RUN_ID / "global_512"
GALLERY_DIR = PROJECT_ROOT / "data_cache" / RUN_ID / "gallery"
REPRO_TOL = 1e-4
DICE_TOL = 1e-12
DISPLAY = {"unet": "UNet", "attention_unet": "Attention U-Net",
           "unetpp": "UNet++", "deeplabv3plus": "DeepLabV3+"}

BINDINGS = {
    "r1_protocol": ("reports/audits/phase13_part1d_predicted_region_protocol_frozen_r1.json",
                    "9089b948ef7563252963bf68d0e0b57a9e891c5e913f54a315bce94c98207eb8"),
    "gate_criteria": ("reports/audits/phase13_regional_integration_gate_criteria_frozen.json",
                      "342a8bcac2c87bf0b85f7bbd963179e74f029825c0434cf527fbd939d2d13c21"),
    "part1d_helper": ("scripts/inference/phase13_part1d_predicted_region_inference.py",
                      "8cd7e39814a049a025f706c57ccea0b535a230908a177690d6289318234c6284"),
    "ckpt_unet": ("checkpoints/phase9_kub_unet_baseline_seed42_512_clean_v3/best.pt",
                  "7b955ba86464a2fec2d569ecb6124de1fa9a4e66d0b5d58b267be9a280b4c2c0"),
    "ckpt_attention_unet": ("checkpoints/phase10_kub_attention_unet_seed42_512_clean_v3/best.pt",
                            "a49b19d66e43b57ed082ea6efc0ac10bccf444277abd3540dc68612bf30b88b3"),
    "ckpt_unetpp": ("checkpoints/phase10_kub_unetpp_seed42_512_clean_v3/best.pt",
                    "ec7eb13f32e43af27eab7fc617bd1a2a8fcce1d6651a1b4a3653f3e4d1283269"),
    "ckpt_deeplabv3plus": ("checkpoints/phase10_kub_deeplabv3plus_seed42_512_clean_v3/best.pt",
                           "f519027ba1a3a4d6212d83fecd4379f61f71bc05b0751924b9660da08d597dad"),
    "phase12_case": ("reports/tables/phase12_clean_v3_oracle_case_metrics.csv",
                     "080f158fb8b3e3552ac7854c6d9a116e11564bcefa9efdcdbb3511dba090b436"),
    "phase12_component": ("reports/tables/phase12_clean_v3_oracle_component_metrics.csv",
                          "d66933a3c2821d3ab9375eadb5c0540fea145edcf49b648064fe9aa4c460c753"),
    "phase12_geometry": ("reports/tables/phase12_clean_v3_oracle_geometry.csv",
                         "29326d5b9a3bf71add74d8743750511f146d8c4dfbd1dc5b04a5e1b647c37cc0"),
    "part1c_case": ("reports/tables/phase13_part1c_best_checkpoint_case_proposals.csv",
                    "d25c44ec1361365e261d36458e86e707ad3bcb58cf000763a732605db0f856ed"),
    "part1c_proposals": ("reports/tables/phase13_part1c_best_checkpoint_proposals.csv",
                         "8c3151a3f1f9a56f0692c6ff2d2171472a777a56e99fa2e474aff8a3478a564a"),
    "part1c_component": ("reports/tables/phase13_part1c_best_checkpoint_component_coverage.csv",
                         "2a3623fecbc1fc5dd5a2c2a12fbd6d5e78fe2e123a9c45431ba53ca14e4e4b87"),
    "part1c_stratified": ("reports/tables/phase13_part1c_size_stratified_coverage.csv",
                          "147d3947d53fce5102ad290d8caa5f19ccb3eebcc61f75634fcb261780c792f9"),
    "gallery": ("reports/tables/phase13_part1c_gallery_selection.csv",
                "1fcbc0ae93e1b63ef3b7c3f045af740e9c353cb7635fd5c98e61d31e177d49d3"),
}


def sha256_file(p) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def verify_bindings() -> dict:
    out, bad = {}, []
    for k, (rel, exp) in BINDINGS.items():
        got = sha256_file(PROJECT_ROOT / rel)
        out[k] = {"path": rel, "sha": got, "expected": exp, "match": got == exp}
        if got != exp:
            bad.append(k)
    r1 = json.loads((AUDITS / "phase13_part1d_predicted_region_protocol_frozen_r1.json").read_text("utf-8"))
    if r1["status"] != "SUPERVISOR_FROZEN_PART1D_R1_READY_FOR_INFERENCE":
        bad.append("r1_status")
    gc = json.loads((AUDITS / "phase13_regional_integration_gate_criteria_frozen.json").read_text("utf-8"))
    for f, v in (("part1d_b_results_inspected", "NO"), ("numerical_thresholds_introduced", 0),
                 ("gate_state", "NOT_DECIDED")):
        if gc[f] != v:
            bad.append(f"gate_{f}")
    if bad:
        raise RuntimeError(f"BINDING VERIFICATION FAILED -> CHECK_REQUIRED: {bad}")
    return out


def load_model_strict(key: str, device):
    if key == "unet":
        from src.models.unet import UNet as M
    elif key == "attention_unet":
        from src.models.attention_unet import AttentionUNet as M
    elif key == "unetpp":
        from src.models.unetpp import UNetPlusPlus as M
    else:
        from src.models.deeplabv3plus import DeepLabV3Plus as M
    ckpt = PROJECT_ROOT / BINDINGS[f"ckpt_{key}"][0]
    ck = torch.load(ckpt, map_location="cpu", weights_only=False)
    mc = ck["configuration"]["model"]
    model = M(in_channels=mc["input_channels"], out_channels=mc["output_channels"],
              base_channels=mc["base_channels"])
    res = model.load_state_dict(ck["model_state"], strict=True)
    missing, unexpected = list(res.missing_keys), list(res.unexpected_keys)
    if missing or unexpected:
        raise RuntimeError(f"{key}: state_dict mismatch missing={missing} unexpected={unexpected}")
    return model.to(device).eval(), {"missing": missing, "unexpected": unexpected}


def per_component_detected(lab, n, pred_bool) -> dict:
    return {cid: bool(int((pred_bool & (lab == cid)).sum()) >= 1) for cid in range(1, n + 1)}


def full_case_metrics(gt, pred, lab, n):
    """Phase-12 native_metrics + component fields, under the Phase-12 key names."""
    m = p12.native_metrics(gt, pred)
    det, missed = p12.component_detection(gt, pred, lab, n)
    m["detected_native_components"] = int(det)
    m["missed_native_components"] = int(missed)
    m["object_recall"] = float(det / n) if n else np.nan
    return m


def retention(pred_v, glob_v, orac_v):
    den = orac_v - glob_v
    if den > 0:
        return (pred_v - glob_v) / den
    return None


def main() -> dict:
    from src.utils.device import get_device
    from PIL import Image

    print("=== binding verification ===")
    bind = verify_bindings()
    print("all bindings PASS")

    dev = get_device(require_cuda=True)
    if dev.type != "cuda":
        raise RuntimeError("CPU fallback FORBIDDEN")
    print("device:", dev, torch.cuda.get_device_name(0))

    ff = p12.full_field_frame()
    ff_ids = list(ff["sample_id"])
    assert len(ff_ids) == 103, len(ff_ids)

    case_tbl = pd.read_csv(TABLES / "phase13_part1c_best_checkpoint_case_proposals.csv")
    case_geom, labels_by_case, ncomp_by_case, gt_by_case = {}, {}, {}, {}
    for _, r in ff.iterrows():
        gt = p12.native_gt(Path(r["mask_path"]))
        lab, n = p12.label(gt > 0, structure=p12.STRUCT8)
        gt_by_case[r["sample_id"]] = gt
        labels_by_case[r["sample_id"]] = lab
        ncomp_by_case[r["sample_id"]] = int(n)
        case_geom[r["sample_id"]] = {"pre": p12.preprocess_geometry(gt.shape),
                                     "shape": gt.shape, "image_path": r["image_path"]}
    assert sum(ncomp_by_case.values()) == 152, sum(ncomp_by_case.values())

    proposal_index, prop_geoms = [], {}
    for r in case_tbl.itertuples():
        sid = r.sample_id
        shape = (int(r.native_H), int(r.native_W))
        geoms = parse_proposal_geometry({"proposal_crop_geometry": r.proposal_crop_geometry})
        for g in geoms:
            assert_geometry_invariants(g, shape)
        prop_geoms[sid] = geoms
        for j, g in enumerate(geoms):
            proposal_index.append((sid, j, g))
    assert len(proposal_index) == 494, len(proposal_index)

    gallery = pd.read_csv(TABLES / "phase13_part1c_gallery_selection.csv")
    gallery_ids = list(gallery["sample_id"])
    assert len(gallery_ids) == 16, len(gallery_ids)
    GALLERY_DIR.mkdir(parents=True, exist_ok=True)

    # ================= STAGE G =================
    global_metrics, gdet = {}, {}
    cache_manifest, load_report = [], {}
    CACHE.mkdir(parents=True, exist_ok=True)
    loader, ds = p12.make_loader()

    for key in MODELS:
        model, rep = load_model_strict(key, dev)
        load_report[key] = rep
        (CACHE / key).mkdir(parents=True, exist_ok=True)
        ck_sha = bind[f"ckpt_{key}"]["sha"]
        n_done = 0
        for batch in loader:
            imgs = batch["image"].to(dev)
            with torch.inference_mode():
                with torch.amp.autocast("cuda", enabled=(dev.type == "cuda")):
                    out = model(imgs)
                probs = torch.sigmoid(out).float().cpu().numpy()[:, 0]
            for b in range(probs.shape[0]):
                sid = batch["sample_id"][b]
                if sid not in case_geom:
                    continue
                arr = np.ascontiguousarray(probs[b], dtype=np.float32)
                fp = CACHE / key / f"{sid}.npy"
                np.save(fp, arr)
                cache_manifest.append({"model": key, "sample_id": sid, "checkpoint_sha": ck_sha,
                                       "shape": f"{arr.shape[0]}x{arr.shape[1]}", "dtype": str(arr.dtype),
                                       "file_sha": sha256_file(fp)})
                cg = case_geom[sid]
                G = p12.global_native(arr, cg["pre"], cg["shape"])
                pred = G >= THRESHOLD
                m = full_case_metrics(gt_by_case[sid], pred, labels_by_case[sid], ncomp_by_case[sid])
                global_metrics[(key, sid)] = m
                gdet.update({(key, sid, c): v for c, v in
                             per_component_detected(labels_by_case[sid], ncomp_by_case[sid], pred).items()})
                n_done += 1
        print(f"  Stage G {DISPLAY[key]}: {n_done}/103")
        del model
        torch.cuda.empty_cache()
    assert len(global_metrics) == 412, len(global_metrics)
    pd.DataFrame(cache_manifest).to_csv(CACHE.parent / "global_512_manifest.csv", index=False)

    # ================= REPRODUCTION GATE =================
    p12case = pd.read_csv(TABLES / "phase12_clean_v3_oracle_case_metrics.csv")
    gn = p12case[p12case["variant"] == "GLOBAL_NATIVE"].set_index(["model", "sample_id"])
    on = p12case[p12case["variant"] == "ORACLE_FLOAT_GLOBAL_RETAINED"].set_index(["model", "sample_id"])
    assert len(gn) == 412 and len(on) == 412, (len(gn), len(on))
    repro_rows, repro_pass = [], True
    for key in MODELS:
        d = {f: [] for f in ("dice", "iou", "precision", "recall")}
        for sid in ff_ids:
            mine, ref = global_metrics[(key, sid)], gn.loc[(key, sid)]
            for f in d:
                d[f].append(abs(mine[f] - float(ref[f])))
        mx = float(np.max(d["dice"]))
        ok = mx <= REPRO_TOL
        repro_pass = repro_pass and ok
        repro_rows.append({
            "model": DISPLAY[key], "model_key": key, "n_cases": len(d["dice"]),
            "rows_matched": f"{len(d['dice'])}/103",
            "max_abs_dice_diff": mx, "mean_abs_dice_diff": float(np.mean(d["dice"])),
            "mean_dice_new": float(np.mean([global_metrics[(key, s)]["dice"] for s in ff_ids])),
            "mean_dice_phase12": float(np.mean([float(gn.loc[(key, s)]["dice"]) for s in ff_ids])),
            "mean_abs_iou_diff": float(np.mean(d["iou"])), "max_abs_iou_diff": float(np.max(d["iou"])),
            "mean_abs_precision_diff": float(np.mean(d["precision"])),
            "max_abs_precision_diff": float(np.max(d["precision"])),
            "mean_abs_recall_diff": float(np.mean(d["recall"])),
            "max_abs_recall_diff": float(np.max(d["recall"])),
            "checkpoint_sha": bind[f"ckpt_{key}"]["sha"], "pass": bool(ok)})
        print(f"  repro {DISPLAY[key]}: max abs Dice diff {mx:.3e} -> {'PASS' if ok else 'FAIL'}")
    repro_df = pd.DataFrame(repro_rows)
    repro_df.to_csv(TABLES / "phase13_part1d_b_global_reproduction_gate.csv", index=False)

    if not repro_pass:
        (AUDITS / "phase13_part1d_b_global_reproduction.json").write_text(json.dumps({
            "artifact": "PHASE13_PART1D_B_GLOBAL_REPRODUCTION", "status": "CHECK_REQUIRED",
            "reason": "GLOBAL_REPRODUCTION_FAILED", "tolerance": REPRO_TOL,
            "models": repro_rows, "regional_inference_started": "NO"}, indent=2) + "\n", "utf-8")
        raise RuntimeError("GLOBAL REPRODUCTION GATE FAILED -> CHECK_REQUIRED; regional NOT started")

    # ================= STAGE R =================
    pred_metrics, pdet, crop_counts, union_frac = {}, {}, {}, {}
    for key in MODELS:
        model, _ = load_model_strict(key, dev)
        n_crops = 0
        for sid in ff_ids:
            shape = case_geom[sid]["shape"]
            geoms = prop_geoms[sid]
            gray = np.asarray(Image.open(case_geom[sid]["image_path"]).convert("L"))
            regional = []
            for g in geoms:
                crop = prepare_regional_crop_512(gray, g)
                t = torch.from_numpy(np.ascontiguousarray(crop))[None, None].to(dev)
                with torch.inference_mode():
                    with torch.amp.autocast("cuda", enabled=(dev.type == "cuda")):
                        logits = model(t)
                    prob512 = torch.sigmoid(logits).float().squeeze().cpu().numpy().astype(np.float32)
                regional.append(restore_probability_to_full_native(prob512, g, shape))
                n_crops += 1
            del gray
            G = p12.global_native(np.load(CACHE / key / f"{sid}.npy"), case_geom[sid]["pre"], shape)
            R = np.maximum.reduce(regional) if regional else np.zeros(shape, dtype=np.float32)
            U = proposal_support_mask(geoms, shape)
            P = np.where(U, R, G)
            pred = P >= THRESHOLD
            m = full_case_metrics(gt_by_case[sid], pred, labels_by_case[sid], ncomp_by_case[sid])
            pred_metrics[(key, sid)] = m
            pdet.update({(key, sid, c): v for c, v in
                         per_component_detected(labels_by_case[sid], ncomp_by_case[sid], pred).items()})
            union_frac[(key, sid)] = float(U.sum()) / float(shape[0] * shape[1])
            if sid in gallery_ids:
                gdir = GALLERY_DIR / sid
                gdir.mkdir(parents=True, exist_ok=True)
                np.save(gdir / f"{key}_predicted_binary.npy", pred.astype(np.uint8))
                np.save(gdir / f"{key}_global_prob.npy", G.astype(np.float32))
            del regional, R, U, P, G, pred
        crop_counts[key] = n_crops
        print(f"  Stage R {DISPLAY[key]}: {n_crops} crop evaluations")
        del model
        torch.cuda.empty_cache()

    assert all(v == 494 for v in crop_counts.values()), crop_counts
    assert len(pred_metrics) == 412, len(pred_metrics)

    # persist per-case inference results so tables/audits can be rebuilt WITHOUT re-inference
    import pickle
    RESULTS_PKL = CACHE.parent / "case_inference_results.pkl"
    with open(RESULTS_PKL, "wb") as f:
        pickle.dump({"global": global_metrics, "predicted": pred_metrics,
                     "gdet": gdet, "pdet": pdet, "union_frac": union_frac,
                     "crop_counts": crop_counts, "load_report": load_report,
                     "repro_rows": repro_rows, "bind": bind}, f)
    print("  persisted case inference results ->", RESULTS_PKL)

    # gallery static context (GT + proposals) — no extra inference
    for sid in gallery_ids:
        gdir = GALLERY_DIR / sid
        np.save(gdir / "gt_binary.npy", (gt_by_case[sid] > 0).astype(np.uint8))
        np.save(gdir / "proposal_support.npy", proposal_support_mask(prop_geoms[sid], gt_by_case[sid].shape).astype(np.uint8))

    # ================= CASE-MODEL TABLE =================
    p1c_comp = pd.read_csv(TABLES / "phase13_part1c_best_checkpoint_component_coverage.csv")
    p12comp = pd.read_csv(TABLES / "phase12_clean_v3_oracle_component_metrics.csv")
    p12geom = pd.read_csv(TABLES / "phase12_clean_v3_oracle_geometry.csv")
    case_lookup = case_tbl.set_index("sample_id")

    case_rows = []
    for sid in ff_ids:
        cr = case_lookup.loc[sid]
        for key in MODELS:
            g, o, p = global_metrics[(key, sid)], on.loc[(key, sid)], pred_metrics[(key, sid)]
            row = {
                "sample_id": sid, "model": key, "model_display": DISPLAY[key],
                "native_height": case_geom[sid]["shape"][0], "native_width": case_geom[sid]["shape"][1],
                "native_gt_components": ncomp_by_case[sid],
                "proposal_count": int(cr["proposal_count"]),
                "proposal_union_area_fraction": union_frac[(key, sid)],
                "part1c_bbox_any_component_covered90": bool(cr["bbox_any_component_covered90"]),
                "part1c_bbox_all_components_covered90": bool(cr["bbox_all_components_covered90"]),
                "part1c_pixel_any_component_covered90": bool(cr["pixel_any_component_covered90"]),
                "part1c_pixel_all_components_covered90": bool(cr["pixel_all_components_covered90"]),
                "part1c_bbox_mean_component_coverage": float(cr["bbox_mean_component_coverage"]),
                "part1c_pixel_mean_component_coverage": float(cr["pixel_mean_component_coverage"]),
                "part1c_contains_TINY": bool(cr["contains_TINY"]),
                "part1c_contains_SMALL": bool(cr["contains_SMALL"]),
                "part1c_contains_MEDIUM": bool(cr["contains_MEDIUM"]),
                "part1c_contains_LARGE": bool(cr["contains_LARGE"]),
                "hard_tiny_image": bool(cr["hard_tiny_image"]),
                "global_empty_image": bool(cr["global_empty_image"]),
                "multi_component_image": bool(int(cr["native_component_count"]) > 1),
            }
            for tag, src in (("global", g), ("oracle", o), ("predicted", p)):
                for f in ("dice", "iou", "precision", "recall"):
                    row[f"{tag}_{f}"] = float(src[f])
                for f in ("tp_pixels", "fp_pixels", "fn_pixels"):
                    row[f"{tag}_{f}"] = float(src[f])
                row[f"{tag}_prediction_empty"] = bool(src["prediction_empty"])
                row[f"{tag}_hd95"] = float(src["hd95"]) if pd.notna(src["hd95"]) else np.nan
                row[f"{tag}_hd95_valid"] = bool(src["hd95_valid"])
                row[f"{tag}_hd95_invalid_reason"] = str(src["hd95_invalid_reason"]) if src["hd95_invalid_reason"] else ""
                row[f"{tag}_detected_native_components"] = int(src["detected_native_components"])
                row[f"{tag}_missed_native_components"] = int(src["missed_native_components"])
                row[f"{tag}_object_recall"] = float(src["object_recall"])
            for f in ("dice", "iou", "precision", "recall"):
                row[f"predicted_minus_global_{f}"] = row[f"predicted_{f}"] - row[f"global_{f}"]
                row[f"oracle_minus_global_{f}"] = row[f"oracle_{f}"] - row[f"global_{f}"]
                row[f"predicted_minus_oracle_{f}"] = row[f"predicted_{f}"] - row[f"oracle_{f}"]
            row["case_dice_improved"] = bool(row["predicted_dice"] > row["global_dice"] + DICE_TOL)
            row["case_dice_worsened"] = bool(row["predicted_dice"] < row["global_dice"] - DICE_TOL)
            row["case_dice_unchanged"] = bool(abs(row["predicted_dice"] - row["global_dice"]) <= DICE_TOL)
            case_rows.append(row)
    case_df = pd.DataFrame(case_rows)
    assert len(case_df) == EXPECTED_CASE_MODEL_ROWS, len(case_df)
    case_df.to_csv(TABLES / "phase13_part1d_predicted_region_case_model_metrics.csv", index=False)

    # ================= COMPONENT-MODEL TABLE =================
    frozen_comp = p12comp.set_index(["model", "sample_id", "native_component_id"])
    p1c_comp_idx = p1c_comp.set_index(["sample_id", "native_component_id"])
    p12geom_idx = p12geom.set_index(["sample_id", "native_component_id"])
    comp_rows = []
    for sid in ff_ids:
        n = ncomp_by_case[sid]
        for cid in range(1, n + 1):
            cov = p1c_comp_idx.loc[(sid, cid)]
            geo = p12geom_idx.loc[(sid, cid)]
            for key in MODELS:
                fc = frozen_comp.loc[(key, sid, cid)]
                gd = bool(gdet[(key, sid, cid)])
                od = bool(fc["primary_oracle_detected"])
                pd_ = bool(pdet[(key, sid, cid)])
                gd12 = bool(fc["global_detected"])
                comp_rows.append({
                    "sample_id": sid, "native_component_id": cid, "model": key,
                    "model_display": DISPLAY[key],
                    "size_stratum": str(geo["size_stratum"]),
                    "component_pixels": int(geo["native_component_pixels"]),
                    "hard_tiny": bool(cov["hard_tiny"]),
                    "global_empty_image": bool(cov["global_empty_image"]),
                    "multi_component_image": bool(n > 1),
                    "part1c_bbox_coverage_fraction": float(cov["bbox_coverage_fraction"]),
                    "part1c_bbox_covered90": bool(cov["bbox_covered90"]),
                    "part1c_bbox_covered50": bool(cov["bbox_covered50"]),
                    "part1c_bbox_any_overlap": bool(cov["bbox_any_overlap"]),
                    "part1c_pixel_coverage_fraction": float(cov["pixel_coverage_fraction"]),
                    "part1c_pixel_covered90": bool(cov["pixel_covered90"]),
                    "part1c_pixel_covered50": bool(cov["pixel_covered50"]),
                    "part1c_pixel_any_overlap": bool(cov["pixel_any_overlap"]),
                    "global_detected": gd,
                    "global_detected_phase12": gd12,
                    "global_detection_matches_phase12": bool(gd == gd12),
                    "oracle_detected": od,
                    "predicted_detected": pd_,
                    "GLOBAL_TO_PREDICTED_RECOVERY": bool((not gd) and pd_),
                    "GLOBAL_TO_PREDICTED_LOSS": bool(gd and (not pd_)),
                    "GLOBAL_TO_ORACLE_RECOVERY": bool((not gd12) and od),
                    "GLOBAL_TO_ORACLE_LOSS": bool(gd12 and (not od)),
                })
    comp_df = pd.DataFrame(comp_rows)
    assert len(comp_df) == EXPECTED_COMPONENT_MODEL_ROWS, len(comp_df)
    comp_df.to_csv(TABLES / "phase13_part1d_predicted_region_component_model_metrics.csv", index=False)

    # ================= MODEL SUMMARY =================
    r1_gains = json.loads((AUDITS / "phase13_part1d_predicted_region_protocol_frozen_r1.json")
                          .read_text("utf-8"))["phase12_oracle_dice_gains"]
    sum_rows = []
    for key in MODELS:
        sub = case_df[case_df["model"] == key]
        comps = comp_df[comp_df["model"] == key]
        D_G = float(sub["global_dice"].mean())
        D_O = float(sub["oracle_dice"].mean())
        D_P = float(sub["predicted_dice"].mean())
        # ORACLE-SOURCE GUARD: the frozen Phase-12 oracle gain must be reproduced from the
        # authoritative ORACLE_FLOAT_GLOBAL_RETAINED rows. Catches any variant-lookup error.
        exp_gain = float(r1_gains[key])
        got_gain = D_O - D_G
        if abs(got_gain - exp_gain) > 1e-4:
            raise RuntimeError(
                f"ORACLE SOURCE GUARD FAILED for {key}: D_O-D_G={got_gain:.9f} "
                f"but frozen Phase-12 oracle gain is {exp_gain:.9f} -> CHECK_REQUIRED")
        IoU_G = float(sub["global_iou"].mean()); IoU_O = float(sub["oracle_iou"].mean())
        IoU_P = float(sub["predicted_iou"].mean())
        Obj_G = float(sub["global_object_recall"].mean())
        Obj_O = float(sub["oracle_object_recall"].mean())
        Obj_P = float(sub["predicted_object_recall"].mean())
        FN_G = float(sub["global_fn_pixels"].mean()); FN_O = float(sub["oracle_fn_pixels"].mean())
        FN_P = float(sub["predicted_fn_pixels"].mean())
        sum_rows.append({
            "model": key, "model_display": DISPLAY[key],
            "global_macro_dice": D_G, "global_macro_iou": IoU_G,
            "global_macro_precision": float(sub["global_precision"].mean()),
            "global_macro_recall": float(sub["global_recall"].mean()),
            "oracle_macro_dice": D_O, "oracle_macro_iou": IoU_O,
            "oracle_macro_precision": float(sub["oracle_precision"].mean()),
            "oracle_macro_recall": float(sub["oracle_recall"].mean()),
            "predicted_macro_dice": D_P, "predicted_macro_iou": IoU_P,
            "predicted_macro_precision": float(sub["predicted_precision"].mean()),
            "predicted_macro_recall": float(sub["predicted_recall"].mean()),
            "DELTA_ORACLE_DICE": D_O - D_G,
            "DELTA_PRED_DICE": D_P - D_G,
            "RETENTION_DICE": retention(D_P, D_G, D_O),
            "ORACLE_GAP_DICE": D_P - D_O,
            "iou_gain_retention": retention(IoU_P, IoU_G, IoU_O),
            "global_object_recall": Obj_G, "oracle_object_recall": Obj_O,
            "predicted_object_recall": Obj_P,
            "object_recall_gain_retention": retention(Obj_P, Obj_G, Obj_O),
            "mean_global_fn_pixels": FN_G, "mean_oracle_fn_pixels": FN_O, "mean_predicted_fn_pixels": FN_P,
            "fn_reduction_retention": retention(-FN_P, -FN_G, -FN_O),
            "mean_fp_delta": float((sub["predicted_fp_pixels"] - sub["global_fp_pixels"]).mean()),
            "mean_fn_delta": float((sub["predicted_fn_pixels"] - sub["global_fn_pixels"]).mean()),
            "cases_dice_improved": int(sub["case_dice_improved"].sum()),
            "cases_dice_unchanged": int(sub["case_dice_unchanged"].sum()),
            "cases_dice_worsened": int(sub["case_dice_worsened"].sum()),
            "max_dice_improvement": float((sub["predicted_dice"] - sub["global_dice"]).max()),
            "max_dice_worsening": float((sub["predicted_dice"] - sub["global_dice"]).min()),
            "component_recoveries": int(comps["GLOBAL_TO_PREDICTED_RECOVERY"].sum()),
            "component_losses": int(comps["GLOBAL_TO_PREDICTED_LOSS"].sum()),
            "empty_recoveries": int((sub["global_prediction_empty"] & ~sub["predicted_prediction_empty"]).sum()),
            "new_empty_predictions": int((~sub["global_prediction_empty"] & sub["predicted_prediction_empty"]).sum()),
        })
    summary_df = pd.DataFrame(sum_rows)
    assert len(summary_df) == 4, len(summary_df)
    summary_df.to_csv(TABLES / "phase13_part1d_predicted_region_model_summary.csv", index=False)

    # ================= CROSS-ARCHITECTURE =================
    piv_imp = case_df.pivot_table(index="sample_id", columns="model", values="case_dice_improved", aggfunc="first")
    piv_wor = case_df.pivot_table(index="sample_id", columns="model", values="case_dice_worsened", aggfunc="first")
    cross = {
        "cases_improved_all_four": int((piv_imp.sum(axis=1) == 4).sum()),
        "cases_nonworse_all_four": int((piv_wor.sum(axis=1) == 0).sum()),
        "cases_worse_all_four": int((piv_wor.sum(axis=1) == 4).sum()),
        "components_recovered_by_at_least_one": int(comp_df.groupby(["sample_id", "native_component_id"])["GLOBAL_TO_PREDICTED_RECOVERY"].max().sum()),
        "components_recovered_by_all_four": int((comp_df.groupby(["sample_id", "native_component_id"])["GLOBAL_TO_PREDICTED_RECOVERY"].sum() == 4).sum()),
        "components_lost_by_at_least_one": int(comp_df.groupby(["sample_id", "native_component_id"])["GLOBAL_TO_PREDICTED_LOSS"].max().sum()),
        "components_lost_by_all_four": int((comp_df.groupby(["sample_id", "native_component_id"])["GLOBAL_TO_PREDICTED_LOSS"].sum() == 4).sum()),
    }
    pd.DataFrame([cross]).T.rename(columns={0: "value"}).to_csv(
        TABLES / "phase13_part1d_cross_architecture_summary.csv")

    # ================= SIZE / COHORT SUMMARIES =================
    cohort_rows = []
    for dim, vals in (("size_stratum", ["TINY", "SMALL", "MEDIUM", "LARGE"]),
                      ("hard_tiny", [True]), ("global_empty_image", [True]), ("multi_component_image", [True])):
        for v in vals:
            sub = comp_df[comp_df[dim] == v]
            if not len(sub):
                continue
            for key in MODELS:
                s = sub[sub["model"] == key]
                cohort_rows.append({
                    "cohort_dimension": dim, "cohort_value": str(v), "model": key,
                    "model_display": DISPLAY[key], "n_components": len(s),
                    "global_detected": int(s["global_detected"].sum()),
                    "oracle_detected": int(s["oracle_detected"].sum()),
                    "predicted_detected": int(s["predicted_detected"].sum()),
                    "GLOBAL_TO_PREDICTED_RECOVERIES": int(s["GLOBAL_TO_PREDICTED_RECOVERY"].sum()),
                    "GLOBAL_TO_PREDICTED_LOSSES": int(s["GLOBAL_TO_PREDICTED_LOSS"].sum()),
                    "part1c_bbox_covered90": int(s["part1c_bbox_covered90"].sum()),
                    "part1c_pixel_covered90": int(s["part1c_pixel_covered90"].sum()),
                })
    pd.DataFrame(cohort_rows).to_csv(TABLES / "phase13_part1d_predicted_region_cohort_summary.csv", index=False)

    # ================= LOCALIZATION -> SEGMENTATION LINK =================
    link_rows = []
    for field in ("part1c_bbox_covered90", "part1c_bbox_covered50", "part1c_bbox_any_overlap",
                  "part1c_pixel_covered90", "part1c_pixel_covered50", "part1c_pixel_any_overlap"):
        for key in MODELS:
            s = comp_df[comp_df["model"] == key]
            for val in (True, False):
                ss = s[s[field] == val]
                if not len(ss):
                    continue
                link_rows.append({
                    "field": field, "value": bool(val), "model": key, "model_display": DISPLAY[key],
                    "n_components": len(ss),
                    "recovered": int(ss["GLOBAL_TO_PREDICTED_RECOVERY"].sum()),
                    "recovery_rate": float(ss["GLOBAL_TO_PREDICTED_RECOVERY"].mean()),
                    "lost": int(ss["GLOBAL_TO_PREDICTED_LOSS"].sum()),
                    "lost_rate": float(ss["GLOBAL_TO_PREDICTED_LOSS"].mean()),
                })
    pd.DataFrame(link_rows).to_csv(TABLES / "phase13_part1d_localization_segmentation_linkage.csv", index=False)

    return {"bind": bind, "repro": repro_rows, "crop_counts": crop_counts,
            "load_report": load_report, "summary": sum_rows, "cross": cross,
            "case_df": case_df, "comp_df": comp_df}


if __name__ == "__main__":
    res = main()
    print("\n=== DONE ===")
    for r in res["summary"]:
        print(f"{r['model_display']:<16} D_G={r['global_macro_dice']:.6f} "
              f"D_O={r['oracle_macro_dice']:.6f} D_P={r['predicted_macro_dice']:.6f} "
              f"RET={r['RETENTION_DICE']}")
    print("cross:", res["cross"])
