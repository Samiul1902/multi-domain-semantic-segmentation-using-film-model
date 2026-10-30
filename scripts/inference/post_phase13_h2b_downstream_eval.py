"""POST-PHASE-13 H2-B-B2 — Downstream regional segmentation evaluation.

Uses the frozen H2B best-checkpoint localizer proposals (488 proposals) against four
frozen segmentation architectures.  Reuses the Phase-13 Part1D-B global cache.

No localizer training, no localizer forward, no proposal regeneration,
no H1 filtering, no threshold search, no TEST.

Run id: post_phase13_h2b_downstream_best_native_policy
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
    THRESHOLD,
    assert_geometry_invariants,
    prepare_regional_crop_512,
    proposal_support_mask,
    restore_probability_to_full_native,
)

import phase12_oracle_inference as p12  # noqa: E402

TABLES = PROJECT_ROOT / "reports" / "tables"
AUDITS = PROJECT_ROOT / "reports" / "audits"
RUN_ID = "post_phase13_h2b_downstream_best_native_policy"
CACHE = PROJECT_ROOT / "data_cache" / "phase13_part1d_b_predicted_region_clean_v3" / "global_512"
DICE_TOL = 1e-12
DISPLAY = {"unet": "UNet", "attention_unet": "Attention U-Net",
           "unetpp": "UNet++", "deeplabv3plus": "DeepLabV3+"}
MODELS = ["unet", "attention_unet", "unetpp", "deeplabv3plus"]

# ---------------------------------------------------------------------------
# Bindings
# ---------------------------------------------------------------------------
BINDINGS = {
    "h2b_protocol": ("reports/audits/post_phase13_h2b_protocol_frozen.json",
                     "22d4e363a9375bc12828c944b1583921efa77d45b6df7d6387738d13d950949e"),
    "h2b_b1_eval": ("reports/audits/post_phase13_h2b_b1_training_evaluation.json",
                    "34a52942ea4ef9da21c4aa450a925c8c59ada771e08f99ab99c3ec669c1e2175"),
    "h2b_best_pt": ("checkpoints/post_phase13_h2b_kub_localizer_r512_h128_sigmaeq075_"
                    "softtargetfocalgamma2_deploymentbalance_seed42_clean_v3/best.pt",
                    "a9147ad7d1835a6e4ef8d66cc04c063db85b2f9a65585a4a34ae2acfef05f028"),
    "h2b_loss_module": ("src/losses/soft_target_focal_bce.py",
                        "40d359e36a5579ea7544a1f0079aa999e024b8b144956493c184388766c27b75"),
    "ckpt_unet": ("checkpoints/phase9_kub_unet_baseline_seed42_512_clean_v3/best.pt",
                  "7b955ba86464a2fec2d569ecb6124de1fa9a4e66d0b5d58b267be9a280b4c2c0"),
    "ckpt_attention_unet": ("checkpoints/phase10_kub_attention_unet_seed42_512_clean_v3/best.pt",
                            "a49b19d66e43b57ed082ea6efc0ac10bccf444277abd3540dc68612bf30b88b3"),
    "ckpt_unetpp": ("checkpoints/phase10_kub_unetpp_seed42_512_clean_v3/best.pt",
                    "ec7eb13f32e43af27eab7fc617bd1a2a8fcce1d6651a1b4a3653f3e4d1283269"),
    "ckpt_deeplabv3plus": ("checkpoints/phase10_kub_deeplabv3plus_seed42_512_clean_v3/best.pt",
                           "f519027ba1a3a4d6212d83fecd4379f61f71bc05b0751924b9660da08d597dad"),
    "global_cache_manifest": ("data_cache/phase13_part1d_b_predicted_region_clean_v3/global_512_manifest.csv",
                              "76e1034d2bc7925260af33826fc19565b2d5ef786c612a7ad71f3bde46fb89a8"),
    "phase12_case": ("reports/tables/phase12_clean_v3_oracle_case_metrics.csv",
                     "080f158fb8b3e3552ac7854c6d9a116e11564bcefa9efdcdbb3511dba090b436"),
    "phase12_component": ("reports/tables/phase12_clean_v3_oracle_component_metrics.csv",
                          "d66933a3c2821d3ab9375eadb5c0540fea145edcf49b648064fe9aa4c460c753"),
    "phase12_geometry": ("reports/tables/phase12_clean_v3_oracle_geometry.csv",
                         "29326d5b9a3bf71add74d8743750511f146d8c4dfbd1dc5b04a5e1b647c37cc0"),
    "phase13_predicted_case": ("reports/tables/phase13_part1d_predicted_region_case_model_metrics.csv",
                               ""),  # SHA computed at runtime
    "phase13_predicted_component": ("reports/tables/phase13_part1d_predicted_region_component_model_metrics.csv",
                                    ""),
    "h2b_case_proposals": ("reports/tables/post_phase13_h2b_best_checkpoint_case_proposals.csv",
                           ""),
    "h2b_proposals": ("reports/tables/post_phase13_h2b_best_checkpoint_proposals.csv",
                      ""),
    "h2b_component": ("reports/tables/post_phase13_h2b_best_checkpoint_component_coverage.csv",
                      ""),
    "part1d_helper": ("scripts/inference/phase13_part1d_predicted_region_inference.py",
                      "8cd7e39814a049a025f706c57ccea0b535a230908a177690d6289318234c6284"),
}


def sha256_file(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def verify_bindings() -> dict:
    out = {}
    for key, (rel_path, expected_sha) in BINDINGS.items():
        p = PROJECT_ROOT / rel_path
        if not p.exists():
            raise RuntimeError(f"BINDING MISSING: {key} -> {p}")
        actual = sha256_file(p)
        if expected_sha and actual != expected_sha:
            raise RuntimeError(
                f"BINDING SHA MISMATCH: {key}\n  expected {expected_sha}\n  actual   {actual}"
            )
        out[key] = {"path": str(p), "sha": actual}
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


def h2b_geom_from_row(row) -> dict:
    """Reconstruct full geometry dict from a frozen proposal table's columns.

    The frozen proposal tables store only clip_* and crop_side_pixels; pads are zero because
    clipping already bounds the crop to the native image.  The full-square coords
    y1/y2/x1/x2 equal the clip coords when padding is absent.
    """
    side = int(row["crop_side_pixels"])
    geom = {
        "y1": int(row["clip_y1"]),
        "y2": int(row["clip_y2"]),
        "x1": int(row["clip_x1"]),
        "x2": int(row["clip_x2"]),
        "clip_y1": int(row["clip_y1"]),
        "clip_y2": int(row["clip_y2"]),
        "clip_x1": int(row["clip_x1"]),
        "clip_x2": int(row["clip_x2"]),
        "pad_top": 0,
        "pad_bottom": 0,
        "pad_left": 0,
        "pad_right": 0,
        "crop_side": side,
        "crop_side_pixels": side,
        "margin": 0.20,
    }
    return geom


def main() -> dict:
    import sys
    from src.utils.device import get_device
    from PIL import Image

    print("=== binding verification ===", flush=True)
    bind = verify_bindings()
    print("all bindings PASS", flush=True)

    dev = get_device(require_cuda=True)
    if dev.type != "cuda":
        raise RuntimeError("CPU fallback FORBIDDEN")
    print("device:", dev, torch.cuda.get_device_name(0), flush=True)

    ff = p12.full_field_frame()
    ff_ids = list(ff["sample_id"])
    assert len(ff_ids) == 103, len(ff_ids)

    # -----------------------------------------------------------------------
    # Load H2B proposal artifacts
    # -----------------------------------------------------------------------
    h2b_case = pd.read_csv(TABLES / "post_phase13_h2b_best_checkpoint_case_proposals.csv")
    h2b_prop = pd.read_csv(TABLES / "post_phase13_h2b_best_checkpoint_proposals.csv")
    h2b_comp = pd.read_csv(TABLES / "post_phase13_h2b_best_checkpoint_component_coverage.csv")

    assert len(h2b_case) == 103, f"H2B case rows {len(h2b_case)} != 103"
    assert len(h2b_prop) == 488, f"H2B proposal rows {len(h2b_prop)} != 488"
    assert len(h2b_comp) == 152, f"H2B component rows {len(h2b_comp)} != 152"

    # Build per-case geometry
    case_geom, prop_geoms, labels_by_case, ncomp_by_case, gt_by_case = {}, {}, {}, {}, {}
    for _, r in ff.iterrows():
        gt = p12.native_gt(Path(r["mask_path"]))
        lab, n = p12.label(gt > 0, structure=p12.STRUCT8)
        gt_by_case[r["sample_id"]] = gt
        labels_by_case[r["sample_id"]] = lab
        ncomp_by_case[r["sample_id"]] = int(n)
        case_geom[r["sample_id"]] = {"pre": p12.preprocess_geometry(gt.shape),
                                     "shape": gt.shape, "image_path": r["image_path"]}
    assert sum(ncomp_by_case.values()) == 152, sum(ncomp_by_case.values())

    proposal_index = []
    for _, r in h2b_prop.iterrows():
        sid = r["sample_id"]
        shape = case_geom[sid]["shape"]
        geom = h2b_geom_from_row(r)
        assert_geometry_invariants(geom, shape)
        if sid not in prop_geoms:
            prop_geoms[sid] = []
        prop_geoms[sid].append(geom)
        proposal_index.append((sid, geom))
    assert len(proposal_index) == 488, len(proposal_index)

    # -----------------------------------------------------------------------
    # Load frozen comparators
    # -----------------------------------------------------------------------
    p12case = pd.read_csv(TABLES / "phase12_clean_v3_oracle_case_metrics.csv")
    gn = p12case[p12case["variant"] == "GLOBAL_NATIVE"].set_index(["model", "sample_id"])
    on = p12case[p12case["variant"] == "ORACLE_FLOAT_GLOBAL_RETAINED"].set_index(["model", "sample_id"])
    assert len(gn) == 412 and len(on) == 412

    p13case = pd.read_csv(TABLES / "phase13_part1d_predicted_region_case_model_metrics.csv")
    # The Phase-13 predicted table stores its metrics with a ``predicted_`` prefix;
    # normalise them to the canonical bare metric names used by the comparator loop.
    _p13_metrics = ["dice", "iou", "precision", "recall", "tp_pixels", "fp_pixels", "fn_pixels",
                    "prediction_empty", "hd95", "hd95_valid", "hd95_invalid_reason",
                    "detected_native_components", "missed_native_components", "object_recall"]
    _missing = [m for m in _p13_metrics if f"predicted_{m}" not in p13case.columns]
    if _missing:
        raise RuntimeError(f"phase13 predicted table missing predicted_ columns: {_missing}")
    p13case = p13case.rename(columns={f"predicted_{m}": m for m in _p13_metrics})
    p13 = p13case.set_index(["model", "sample_id"])
    assert len(p13) == 412
    p13comp = pd.read_csv(TABLES / "phase13_part1d_predicted_region_component_model_metrics.csv")
    p13comp_idx = p13comp.set_index(["model", "sample_id", "native_component_id"])

    # Frozen H2A-B2 downstream comparator (physically present -> include it).
    H2A_CMP_AVAILABLE = True
    h2a_cmp_case = pd.read_csv(TABLES / "post_phase13_h2a_downstream_case_model_metrics.csv")
    h2a_cmp_case_idx = h2a_cmp_case.set_index(["model", "sample_id"])
    assert len(h2a_cmp_case_idx) == 412, len(h2a_cmp_case_idx)
    h2a_cmp_comp = pd.read_csv(TABLES / "post_phase13_h2a_downstream_component_model_metrics.csv")
    h2a_cmp_comp_idx = h2a_cmp_comp.set_index(["model", "sample_id", "native_component_id"])
    assert len(h2a_cmp_comp_idx) == 608, len(h2a_cmp_comp_idx)
    print("H2A downstream comparator: AVAILABLE", flush=True)

    # Fail fast on comparator schema problems BEFORE any GPU compute.
    _REQ_CASE = ["dice", "iou", "precision", "recall", "tp_pixels", "fp_pixels", "fn_pixels",
                 "prediction_empty", "hd95", "hd95_valid", "hd95_invalid_reason",
                 "detected_native_components", "missed_native_components", "object_recall"]
    for _name, _idx in (("p12_global", gn), ("p12_oracle", on), ("phase13", p13)):
        _cols = set(_idx.reset_index().columns)
        _miss = [c for c in _REQ_CASE if c not in _cols]
        if _miss:
            raise RuntimeError(f"comparator {_name} missing case columns: {_miss}")
    _h2a_req = [f"h2a_predicted_{c}" for c in ("dice", "iou", "precision", "recall",
                                               "tp_pixels", "fp_pixels", "fn_pixels",
                                               "prediction_empty")]
    _miss = [c for c in _h2a_req if c not in h2a_cmp_case.columns]
    if _miss:
        raise RuntimeError(f"H2A comparator missing columns: {_miss}")
    if "h2a_predicted_detected" not in h2a_cmp_comp.columns:
        raise RuntimeError("H2A comparator component table missing h2a_predicted_detected")
    print("comparator schema pre-flight: PASS", flush=True)

    p12comp = pd.read_csv(TABLES / "phase12_clean_v3_oracle_component_metrics.csv")
    p12geom = pd.read_csv(TABLES / "phase12_clean_v3_oracle_geometry.csv")
    frozen_comp = p12comp.set_index(["model", "sample_id", "native_component_id"])
    p12geom_idx = p12geom.set_index(["sample_id", "native_component_id"])

    # Aggregate H2B per-case cohort flags from component table
    h2b_case_cohorts = h2b_comp.groupby("sample_id").agg(
        hard_tiny_image=("hard_tiny", "any"),
        global_empty_image=("global_empty_image", "any"),
        number_of_components=("native_component_id", "count")
    )
    h2b_case_cohorts["multi_component_image"] = h2b_case_cohorts["number_of_components"] > 1

    # -----------------------------------------------------------------------
    # Stage G — global cache reuse + reproduction gate
    # -----------------------------------------------------------------------
    global_metrics, gdet = {}, {}
    cache_manifest = pd.read_csv(CACHE.parent / "global_512_manifest.csv")
    assert len(cache_manifest) == 412
    assert set(cache_manifest["model"].unique()) == {"unet", "attention_unet", "unetpp", "deeplabv3plus"}

    for key in MODELS:
        n_done = 0
        for sid in ff_ids:
            cg = case_geom[sid]
            arr = np.load(CACHE / key / f"{sid}.npy")
            G = p12.global_native(arr, cg["pre"], cg["shape"])
            pred = G >= THRESHOLD
            m = full_case_metrics(gt_by_case[sid], pred, labels_by_case[sid], ncomp_by_case[sid])
            global_metrics[(key, sid)] = m
            gdet.update({(key, sid, c): v for c, v in
                         per_component_detected(labels_by_case[sid], ncomp_by_case[sid], pred).items()})
            n_done += 1
        print(f"  Stage G {DISPLAY[key]}: {n_done}/103 (cache reuse)", flush=True)

    # Reproduction gate against frozen Phase-12 GLOBAL_NATIVE
    repro_rows, repro_pass = [], True
    for key in MODELS:
        d = {f: [] for f in ("dice", "iou", "precision", "recall")}
        for sid in ff_ids:
            mine, ref = global_metrics[(key, sid)], gn.loc[(key, sid)]
            for f in d:
                d[f].append(abs(mine[f] - float(ref[f])))
        mx = float(np.max(d["dice"]))
        ok = mx <= 1e-6  # pure cache reuse -> tight tolerance
        repro_pass = repro_pass and ok
        repro_rows.append({
            "model": DISPLAY[key], "model_key": key, "n_cases": len(d["dice"]),
            "max_abs_dice_diff": mx, "mean_abs_dice_diff": float(np.mean(d["dice"])),
            "pass": bool(ok)})
        print(f"  repro {DISPLAY[key]}: max abs Dice diff {mx:.3e} -> {'PASS' if ok else 'FAIL'}", flush=True)

    if not repro_pass:
        raise RuntimeError("GLOBAL CACHE REPRODUCTION FAILED -> CHECK_REQUIRED")

    # -----------------------------------------------------------------------
    # Stage R — H2B predicted-region inference (488 x 4 = 1952 crops)
    # -----------------------------------------------------------------------
    h2b_metrics, h2b_det, crop_counts, union_frac = {}, {}, {}, {}
    for key in MODELS:
        model, _ = load_model_strict(key, dev)
        n_crops = 0
        for i, sid in enumerate(ff_ids):
            if i > 0 and i % 20 == 0:
                print(f"    {key} case {i}/{len(ff_ids)}", flush=True)
            shape = case_geom[sid]["shape"]
            geoms = prop_geoms.get(sid, [])
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
            G = p12.global_native(np.load(CACHE / key / f"{sid}.npy"),
                                  case_geom[sid]["pre"], shape)
            R = np.maximum.reduce(regional) if regional else np.zeros(shape, dtype=np.float32)
            U = proposal_support_mask(geoms, shape)
            P = np.where(U, R, G)
            pred = P >= THRESHOLD
            m = full_case_metrics(gt_by_case[sid], pred, labels_by_case[sid], ncomp_by_case[sid])
            h2b_metrics[(key, sid)] = m
            h2b_det.update({(key, sid, c): v for c, v in
                            per_component_detected(labels_by_case[sid], ncomp_by_case[sid], pred).items()})
            union_frac[(key, sid)] = float(U.sum()) / float(shape[0] * shape[1])
            del regional, R, U, P, G, pred
        crop_counts[key] = n_crops
        print(f"  Stage R {DISPLAY[key]}: {n_crops} crop evaluations", flush=True)
        del model
        torch.cuda.empty_cache()

    assert all(v == sum(len(prop_geoms.get(sid, [])) for sid in ff_ids) for v in crop_counts.values())
    total_crops = sum(crop_counts.values())
    print(f"TOTAL regional crop evaluations: {total_crops} (expected 1952)", flush=True)
    assert total_crops == 1952, f"{total_crops} != 1952"
    assert len(h2b_metrics) == 412, len(h2b_metrics)

    # -----------------------------------------------------------------------
    # Case-Model Table (412 rows)
    # -----------------------------------------------------------------------
    h2b_case_idx = h2b_case.set_index("sample_id")
    h2b_comp_idx = h2b_comp.set_index(["sample_id", "native_component_id"])

    case_rows = []
    for sid in ff_ids:
        cr = h2b_case_idx.loc[sid]
        cc = h2b_case_cohorts.loc[sid]
        for key in MODELS:
            g = global_metrics[(key, sid)]
            o = on.loc[(key, sid)]
            p13m = p13.loc[(key, sid)]
            h = h2b_metrics[(key, sid)]
            row = {
                "sample_id": sid,
                "model": key,
                "model_display": DISPLAY[key],
                "native_height": case_geom[sid]["shape"][0],
                "native_width": case_geom[sid]["shape"][1],
                "native_gt_components": ncomp_by_case[sid],
                "h2b_proposal_count": int(cr["proposal_count"]),
                "h2b_proposal_union_area_fraction": union_frac[(key, sid)],
                "hard_tiny_image": bool(cc["hard_tiny_image"]),
                "global_empty_image": bool(cc["global_empty_image"]),
                "multi_component_image": bool(cc["multi_component_image"]),
            }
            # Add H2B proposal score stats where available
            sid_props = h2b_prop[h2b_prop["sample_id"] == sid]
            if len(sid_props):
                row["h2b_proposal_score_mean"] = float(sid_props["proposal_score"].mean())
                row["h2b_proposal_score_max"] = float(sid_props["proposal_score"].max())
            else:
                row["h2b_proposal_score_mean"] = np.nan
                row["h2b_proposal_score_max"] = np.nan

            for tag, src in (("global", g), ("oracle", o), ("phase13_predicted", p13m), ("h2b_predicted", h)):
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

            # Frozen H2A-B2 downstream comparator
            h2ac = h2a_cmp_case_idx.loc[(key, sid)]
            for f in ("dice", "iou", "precision", "recall"):
                row[f"h2a_predicted_{f}"] = float(h2ac[f"h2a_predicted_{f}"])
            for f in ("tp_pixels", "fp_pixels", "fn_pixels"):
                row[f"h2a_predicted_{f}"] = float(h2ac[f"h2a_predicted_{f}"])
            row["h2a_predicted_prediction_empty"] = bool(h2ac["h2a_predicted_prediction_empty"])

            # Deltas
            for f in ("dice", "iou", "precision", "recall"):
                row[f"h2b_minus_global_{f}"] = row[f"h2b_predicted_{f}"] - row[f"global_{f}"]
                row[f"h2b_minus_phase13_{f}"] = row[f"h2b_predicted_{f}"] - row[f"phase13_predicted_{f}"]
                row[f"h2b_minus_h2a_{f}"] = row[f"h2b_predicted_{f}"] - row[f"h2a_predicted_{f}"]
                row[f"h2b_minus_oracle_{f}"] = row[f"h2b_predicted_{f}"] - row[f"oracle_{f}"]
                row[f"oracle_minus_global_{f}"] = row[f"oracle_{f}"] - row[f"global_{f}"]

            row["case_dice_improved_vs_global"] = bool(row["h2b_predicted_dice"] > row["global_dice"] + DICE_TOL)
            row["case_dice_worsened_vs_global"] = bool(row["h2b_predicted_dice"] < row["global_dice"] - DICE_TOL)
            row["case_dice_unchanged_vs_global"] = bool(abs(row["h2b_predicted_dice"] - row["global_dice"]) <= DICE_TOL)
            row["case_dice_improved_vs_phase13"] = bool(row["h2b_predicted_dice"] > row["phase13_predicted_dice"] + DICE_TOL)
            row["case_dice_worsened_vs_phase13"] = bool(row["h2b_predicted_dice"] < row["phase13_predicted_dice"] - DICE_TOL)
            row["case_dice_unchanged_vs_phase13"] = bool(abs(row["h2b_predicted_dice"] - row["phase13_predicted_dice"]) <= DICE_TOL)
            row["case_dice_improved_vs_h2a"] = bool(row["h2b_predicted_dice"] > row["h2a_predicted_dice"] + DICE_TOL)
            row["case_dice_worsened_vs_h2a"] = bool(row["h2b_predicted_dice"] < row["h2a_predicted_dice"] - DICE_TOL)
            row["case_dice_unchanged_vs_h2a"] = bool(abs(row["h2b_predicted_dice"] - row["h2a_predicted_dice"]) <= DICE_TOL)
            case_rows.append(row)

    case_df = pd.DataFrame(case_rows)
    assert len(case_df) == 412, len(case_df)
    case_df.to_csv(TABLES / "post_phase13_h2b_downstream_case_model_metrics.csv", index=False)

    # -----------------------------------------------------------------------
    # Component-Model Table (608 rows)
    # -----------------------------------------------------------------------
    comp_rows = []
    for sid in ff_ids:
        n = ncomp_by_case[sid]
        for cid in range(1, n + 1):
            geo = p12geom_idx.loc[(sid, cid)]
            hc = h2b_comp_idx.loc[(sid, cid)] if (sid, cid) in h2b_comp_idx.index else None
            for key in MODELS:
                fc = frozen_comp.loc[(key, sid, cid)]
                gd = bool(gdet[(key, sid, cid)])
                od = bool(fc["primary_oracle_detected"])
                p13d = bool(p13comp_idx.loc[(key, sid, cid)]["predicted_detected"])
                hd = bool(h2b_det[(key, sid, cid)])
                h2ad = bool(h2a_cmp_comp_idx.loc[(key, sid, cid)]["h2a_predicted_detected"])
                comp_rows.append({
                    "sample_id": sid,
                    "native_component_id": cid,
                    "model": key,
                    "model_display": DISPLAY[key],
                    "size_stratum": str(geo["size_stratum"]),
                    "component_pixels": int(geo["native_component_pixels"]),
                    "hard_tiny": bool(hc["hard_tiny"]) if hc is not None else False,
                    "global_empty_image": bool(hc["global_empty_image"]) if hc is not None else False,
                    "multi_component_image": bool(n > 1),
                    "h2b_coverage_fraction": float(hc["coverage_fraction"]) if hc is not None else np.nan,
                    "h2b_covered90": bool(hc["covered90"]) if hc is not None else False,
                    "h2b_covered50": bool(hc["covered50"]) if hc is not None else False,
                    "h2b_any_overlap": bool(hc["any_overlap"]) if hc is not None else False,
                    "global_detected": gd,
                    "oracle_detected": od,
                    "phase13_predicted_detected": p13d,
                    "h2b_predicted_detected": hd,
                    "GLOBAL_TO_H2B_RECOVERY": bool((not gd) and hd),
                    "GLOBAL_TO_H2B_LOSS": bool(gd and (not hd)),
                    "PHASE13_TO_H2B_RECOVERY": bool((not p13d) and hd),
                    "PHASE13_TO_H2B_LOSS": bool(p13d and (not hd)),
                    "h2a_predicted_detected": h2ad,
                    "H2A_TO_H2B_RECOVERY": bool((not h2ad) and hd),
                    "H2A_TO_H2B_LOSS": bool(h2ad and (not hd)),
                })

    comp_df = pd.DataFrame(comp_rows)
    assert len(comp_df) == 608, len(comp_df)
    comp_df.to_csv(TABLES / "post_phase13_h2b_downstream_component_model_metrics.csv", index=False)

    # -----------------------------------------------------------------------
    # Model Summary (4 rows)
    # -----------------------------------------------------------------------
    sum_rows = []
    for key in MODELS:
        sub = case_df[case_df["model"] == key]
        comps = comp_df[comp_df["model"] == key]
        D_G = float(sub["global_dice"].mean())
        D_O = float(sub["oracle_dice"].mean())
        D_P13 = float(sub["phase13_predicted_dice"].mean())
        D_H2B = float(sub["h2b_predicted_dice"].mean())
        D_H2A = float(sub["h2a_predicted_dice"].mean())
        sum_rows.append({
            "model": key,
            "model_display": DISPLAY[key],
            "proposal_count": 488,
            "mean_proposals_per_image": float(sub["h2b_proposal_count"].mean()),
            "mean_intervention_union_area": float(sub["h2b_proposal_union_area_fraction"].mean()),
            "global_macro_dice": D_G,
            "phase13_predicted_macro_dice": D_P13,
            "h2b_predicted_macro_dice": D_H2B,
            "oracle_macro_dice": D_O,
            "DELTA_H2B_GLOBAL_DICE": D_H2B - D_G,
            "DELTA_H2B_PHASE13_DICE": D_H2B - D_P13,
            "h2a_predicted_macro_dice": D_H2A,
            "h2a_predicted_macro_iou": float(sub["h2a_predicted_iou"].mean()),
            "h2a_predicted_macro_precision": float(sub["h2a_predicted_precision"].mean()),
            "h2a_predicted_macro_recall": float(sub["h2a_predicted_recall"].mean()),
            "mean_h2a_fp": float(sub["h2a_predicted_fp_pixels"].mean()),
            "mean_h2a_fn": float(sub["h2a_predicted_fn_pixels"].mean()),
            "DELTA_H2B_H2A_DICE": D_H2B - D_H2A,
            "ORACLE_GAIN_FROM_GLOBAL": D_O - D_G,
            "H2B_ORACLE_BENEFIT_RETENTION": retention(D_H2B, D_G, D_O),
            "H2B_ORACLE_GAP": D_H2B - D_O,
            "global_macro_iou": float(sub["global_iou"].mean()),
            "phase13_predicted_macro_iou": float(sub["phase13_predicted_iou"].mean()),
            "h2b_predicted_macro_iou": float(sub["h2b_predicted_iou"].mean()),
            "oracle_macro_iou": float(sub["oracle_iou"].mean()),
            "global_macro_precision": float(sub["global_precision"].mean()),
            "phase13_predicted_macro_precision": float(sub["phase13_predicted_precision"].mean()),
            "h2b_predicted_macro_precision": float(sub["h2b_predicted_precision"].mean()),
            "oracle_macro_precision": float(sub["oracle_precision"].mean()),
            "global_macro_recall": float(sub["global_recall"].mean()),
            "phase13_predicted_macro_recall": float(sub["phase13_predicted_recall"].mean()),
            "h2b_predicted_macro_recall": float(sub["h2b_predicted_recall"].mean()),
            "oracle_macro_recall": float(sub["oracle_recall"].mean()),
            "mean_global_fp": float(sub["global_fp_pixels"].mean()),
            "mean_phase13_fp": float(sub["phase13_predicted_fp_pixels"].mean()),
            "mean_h2b_fp": float(sub["h2b_predicted_fp_pixels"].mean()),
            "mean_oracle_fp": float(sub["oracle_fp_pixels"].mean()),
            "mean_global_fn": float(sub["global_fn_pixels"].mean()),
            "mean_phase13_fn": float(sub["phase13_predicted_fn_pixels"].mean()),
            "mean_h2b_fn": float(sub["h2b_predicted_fn_pixels"].mean()),
            "mean_oracle_fn": float(sub["oracle_fn_pixels"].mean()),
            "fp_delta_vs_global": float((sub["h2b_predicted_fp_pixels"] - sub["global_fp_pixels"]).mean()),
            "fp_delta_vs_phase13": float((sub["h2b_predicted_fp_pixels"] - sub["phase13_predicted_fp_pixels"]).mean()),
            "fn_delta_vs_global": float((sub["h2b_predicted_fn_pixels"] - sub["global_fn_pixels"]).mean()),
            "fn_delta_vs_phase13": float((sub["h2b_predicted_fn_pixels"] - sub["phase13_predicted_fn_pixels"]).mean()),
            "cases_improved_vs_global": int(sub["case_dice_improved_vs_global"].sum()),
            "cases_same_vs_global": int(sub["case_dice_unchanged_vs_global"].sum()),
            "cases_worse_vs_global": int(sub["case_dice_worsened_vs_global"].sum()),
            "cases_improved_vs_phase13": int(sub["case_dice_improved_vs_phase13"].sum()),
            "cases_same_vs_phase13": int(sub["case_dice_unchanged_vs_phase13"].sum()),
            "cases_worse_vs_phase13": int(sub["case_dice_worsened_vs_phase13"].sum()),
            "component_recoveries_vs_global": int(comps["GLOBAL_TO_H2B_RECOVERY"].sum()),
            "component_losses_vs_global": int(comps["GLOBAL_TO_H2B_LOSS"].sum()),
            "component_recoveries_vs_phase13": int(comps["PHASE13_TO_H2B_RECOVERY"].sum()),
            "component_losses_vs_phase13": int(comps["PHASE13_TO_H2B_LOSS"].sum()),
            "component_recoveries_vs_h2a": int(comps["H2A_TO_H2B_RECOVERY"].sum()),
            "component_losses_vs_h2a": int(comps["H2A_TO_H2B_LOSS"].sum()),
            "fp_delta_vs_h2a": float((sub["h2b_predicted_fp_pixels"] - sub["h2a_predicted_fp_pixels"]).mean()),
            "cases_improved_vs_h2a": int(sub["case_dice_improved_vs_h2a"].sum()),
            "cases_same_vs_h2a": int(sub["case_dice_unchanged_vs_h2a"].sum()),
            "cases_worse_vs_h2a": int(sub["case_dice_worsened_vs_h2a"].sum()),
            "empty_recoveries": int((sub["global_prediction_empty"] & ~sub["h2b_predicted_prediction_empty"]).sum()),
            "new_empty_predictions": int((~sub["global_prediction_empty"] & sub["h2b_predicted_prediction_empty"]).sum()),
        })

    summary_df = pd.DataFrame(sum_rows)
    assert len(summary_df) == 4, len(summary_df)
    summary_df.to_csv(TABLES / "post_phase13_h2b_downstream_model_summary.csv", index=False)

    # -----------------------------------------------------------------------
    # Cross-Architecture Summary
    # -----------------------------------------------------------------------
    piv_imp_g = case_df.pivot_table(index="sample_id", columns="model",
                                     values="case_dice_improved_vs_global", aggfunc="first")
    piv_wor_g = case_df.pivot_table(index="sample_id", columns="model",
                                     values="case_dice_worsened_vs_global", aggfunc="first")
    piv_imp_p = case_df.pivot_table(index="sample_id", columns="model",
                                     values="case_dice_improved_vs_phase13", aggfunc="first")
    piv_wor_p = case_df.pivot_table(index="sample_id", columns="model",
                                     values="case_dice_worsened_vs_phase13", aggfunc="first")
    piv_imp_h = case_df.pivot_table(index="sample_id", columns="model",
                                     values="case_dice_improved_vs_h2a", aggfunc="first")
    piv_wor_h = case_df.pivot_table(index="sample_id", columns="model",
                                     values="case_dice_worsened_vs_h2a", aggfunc="first")
    cross = {
        "cases_h2b_improved_vs_global_all4": int((piv_imp_g.sum(axis=1) == 4).sum()),
        "cases_h2b_nonworse_vs_global_all4": int((piv_wor_g.sum(axis=1) == 0).sum()),
        "cases_h2b_worse_vs_global_all4": int((piv_wor_g.sum(axis=1) == 4).sum()),
        "cases_h2b_improved_vs_phase13_all4": int((piv_imp_p.sum(axis=1) == 4).sum()),
        "cases_h2b_worse_vs_phase13_all4": int((piv_wor_p.sum(axis=1) == 4).sum()),
        "components_recovered_vs_global_by_at_least_one": int(comp_df.groupby(["sample_id", "native_component_id"])["GLOBAL_TO_H2B_RECOVERY"].max().sum()),
        "components_recovered_vs_global_by_all4": int((comp_df.groupby(["sample_id", "native_component_id"])["GLOBAL_TO_H2B_RECOVERY"].sum() == 4).sum()),
        "components_lost_vs_global_by_at_least_one": int(comp_df.groupby(["sample_id", "native_component_id"])["GLOBAL_TO_H2B_LOSS"].max().sum()),
        "components_lost_vs_global_by_all4": int((comp_df.groupby(["sample_id", "native_component_id"])["GLOBAL_TO_H2B_LOSS"].sum() == 4).sum()),
        "cases_h2b_improved_vs_h2a_all4": int((piv_imp_h.sum(axis=1) == 4).sum()),
        "cases_h2b_worse_vs_h2a_all4": int((piv_wor_h.sum(axis=1) == 4).sum()),
    }
    pd.DataFrame([cross]).T.rename(columns={0: "value"}).to_csv(
        TABLES / "post_phase13_h2b_downstream_cross_architecture_summary.csv")

    # -----------------------------------------------------------------------
    # Localizer-to-Downstream Link Table
    # -----------------------------------------------------------------------
    # Frozen localizer metrics for all three localizer families.
    h2b_localizer = json.loads(
        (AUDITS / "post_phase13_h2b_best_checkpoint_standalone_evaluation.json").read_text("utf-8"))["metrics"]
    h2a_localizer = json.loads(
        (AUDITS / "post_phase13_h2a_best_checkpoint_standalone_evaluation.json").read_text("utf-8"))["metrics"]

    link_rows = []
    for key in MODELS:
        sub = case_df[case_df["model"] == key]
        comps = comp_df[comp_df["model"] == key]
        link_rows.append({
            "model": key,
            "model_display": DISPLAY[key],
            # --- H2B localizer (frozen B1 best checkpoint) ---
            "h2b_proposal_count": 488,
            "h2b_pixel_any_hit_precision": h2b_localizer["proposal_pixel_any_hit_precision"],
            "h2b_bbox_any_hit_precision": h2b_localizer["proposal_bbox_any_hit_precision"],
            "h2b_tiny90": h2b_localizer["tiny_recall90"],
            "h2b_overall90": h2b_localizer["overall_recall90"],
            "h2b_overall50": h2b_localizer["overall_recall50"],
            "h2b_any_overlap": h2b_localizer["any_overlap_recall"],
            "h2b_mean_coverage": h2b_localizer["mean_coverage"],
            "h2b_mean_union_area": h2b_localizer["mean_proposal_union_area"],
            "h2b_score_max": h2b_localizer["score_max"],
            "h2b_score_iqr": h2b_localizer["score_iqr"],
            "h2b_fraction_at_max": h2b_localizer["fraction_exactly_at_max"],
            "h2b_roc_auc": h2b_localizer["roc_auc_score_to_pixel_any_hit"],
            "h2b_pr_auc": h2b_localizer["pr_auc_score_to_pixel_any_hit"],
            # --- H2A localizer (frozen) ---
            "h2a_proposal_count": 457,
            "h2a_pixel_any_hit_precision": h2a_localizer["proposal_pixel_any_hit_precision"],
            "h2a_bbox_any_hit_precision": h2a_localizer["proposal_bbox_any_hit_precision"],
            "h2a_tiny90": h2a_localizer["tiny_recall90"],
            "h2a_overall90": h2a_localizer["overall_recall90"],
            "h2a_overall50": h2a_localizer["overall_recall50"],
            "h2a_any_overlap": h2a_localizer["any_overlap_recall"],
            "h2a_mean_coverage": h2a_localizer["mean_coverage"],
            "h2a_mean_union_area": h2a_localizer["mean_proposal_union_area"],
            "h2a_score_max": h2a_localizer["score_max"],
            "h2a_score_iqr": h2a_localizer["score_iqr"],
            "h2a_fraction_at_max": h2a_localizer["fraction_exactly_at_max"],
            "h2a_roc_auc": h2a_localizer["roc_auc_score_to_pixel_any_hit"],
            "h2a_pr_auc": h2a_localizer["pr_auc_score_to_pixel_any_hit"],
            # --- Phase13 localizer (historical context) ---
            "phase13_proposal_count": 494,
            "phase13_pixel_any_hit_precision": 0.24696356275303644,
            "phase13_bbox_any_hit_precision": 0.24898785425101214,
            "phase13_tiny90": 0.6805555555555556,
            "phase13_overall90": 0.5986842105263158,
            "phase13_overall50": 0.7894736842105263,
            "phase13_any_overlap": 0.8486842105263158,
            "phase13_mean_coverage": 0.7584022780771768,
            "phase13_mean_union_area": 0.004846047236646118,
            "phase13_score_max": 0.1250653713941574,
            "phase13_score_iqr": 0.0005326690673828125,
            "phase13_fraction_at_max": 0.6821862348178138,
            # --- Downstream (this run) ---
            "h2b_macro_dice": float(sub["h2b_predicted_dice"].mean()),
            "h2b_macro_iou": float(sub["h2b_predicted_iou"].mean()),
            "h2b_macro_precision": float(sub["h2b_predicted_precision"].mean()),
            "h2b_macro_recall": float(sub["h2b_predicted_recall"].mean()),
            "h2b_mean_fp": float(sub["h2b_predicted_fp_pixels"].mean()),
            "h2b_mean_fn": float(sub["h2b_predicted_fn_pixels"].mean()),
            "h2b_component_recoveries_vs_global": int(comps["GLOBAL_TO_H2B_RECOVERY"].sum()),
            "h2b_component_losses_vs_global": int(comps["GLOBAL_TO_H2B_LOSS"].sum()),
            # --- Downstream (frozen comparators) ---
            "h2a_macro_dice": float(sub["h2a_predicted_dice"].mean()),
            "h2a_macro_precision": float(sub["h2a_predicted_precision"].mean()),
            "h2a_macro_recall": float(sub["h2a_predicted_recall"].mean()),
            "h2a_mean_fp": float(sub["h2a_predicted_fp_pixels"].mean()),
            "h2a_mean_fn": float(sub["h2a_predicted_fn_pixels"].mean()),
            "phase13_macro_dice": float(sub["phase13_predicted_dice"].mean()),
            "phase13_macro_precision": float(sub["phase13_predicted_precision"].mean()),
            "phase13_macro_recall": float(sub["phase13_predicted_recall"].mean()),
            "phase13_mean_fp": float(sub["phase13_predicted_fp_pixels"].mean()),
            "phase13_mean_fn": float(sub["phase13_predicted_fn_pixels"].mean()),
        })
    pd.DataFrame(link_rows).to_csv(TABLES / "post_phase13_h2b_localizer_to_downstream_comparison.csv", index=False)

    # -----------------------------------------------------------------------
    # Integrity Audit
    # -----------------------------------------------------------------------
    audit = {
        "artifact": "POST_PHASE13_H2B_B2_DOWNSTREAM_INTEGRITY",
        "run_id": RUN_ID,
        "status": "PASS",
        "h2b_protocol_sha": bind["h2b_protocol"]["sha"],
        "h2b_b1_evaluation_sha": bind["h2b_b1_eval"]["sha"],
        "h2b_best_pt_sha": bind["h2b_best_pt"]["sha"],
        "h2b_loss_module_sha": bind["h2b_loss_module"]["sha"],
        "h2a_downstream_comparator": "AVAILABLE",
        "h2a_comparator_case_sha": sha256_file(TABLES / "post_phase13_h2a_downstream_case_model_metrics.csv"),
        "h2a_comparator_component_sha": sha256_file(TABLES / "post_phase13_h2a_downstream_component_model_metrics.csv"),
        "phase12_oracle_case_sha": sha256_file(TABLES / "phase12_clean_v3_oracle_case_metrics.csv"),
        "phase13_predicted_case_sha": sha256_file(TABLES / "phase13_part1d_predicted_region_case_model_metrics.csv"),
        "proposal_table_shas": {
            "case": sha256_file(TABLES / "post_phase13_h2b_best_checkpoint_case_proposals.csv"),
            "proposals": sha256_file(TABLES / "post_phase13_h2b_best_checkpoint_proposals.csv"),
            "component": sha256_file(TABLES / "post_phase13_h2b_best_checkpoint_component_coverage.csv"),
            "stratified": sha256_file(TABLES / "post_phase13_h2b_best_checkpoint_size_stratified.csv"),
        },
        "proposal_count": 488,
        "part1d_helper_sha": bind["part1d_helper"]["sha"],
        "segmentation_checkpoint_shas": {k: bind[f"ckpt_{k}"]["sha"] for k in MODELS},
        "global_cache_manifest_sha": bind["global_cache_manifest"]["sha"],
        "global_reproduction": "PASS",
        "case_model_rows": len(case_df),
        "component_model_rows": len(comp_df),
        "model_summary_rows": len(summary_df),
        "regional_crop_evaluations": total_crops,
        "localizer_forwards": 0,
        "proposal_regeneration": 0,
        "new_global_forwards": 0,
        "test_reads": 0,
        "external_test_reads": 0,
    }
    (AUDITS / "post_phase13_h2b_b2_downstream_integrity.json").write_text(
        json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Also write .md
    md = ["# POST-PHASE-13 H2-B-B2 — Downstream Integrity Audit", "",
          f"- status: **PASS**", f"- run id: `{RUN_ID}`", "",
          "## Bindings", "",
          f"- H2B protocol: `{bind['h2b_protocol']['sha']}`",
          f"- H2B B1 evaluation: `{bind['h2b_b1_eval']['sha']}`",
          f"- H2B best.pt: `{bind['h2b_best_pt']['sha']}`",
          f"- H2B loss module: `{bind['h2b_loss_module']['sha']}`",
          f"- Part1D helper: `{bind['part1d_helper']['sha']}`",
          f"- Global cache manifest: `{bind['global_cache_manifest']['sha']}`", "",
          "## Segmentation checkpoints", "",
          "| model | SHA-256 |", "|---|---|"]
    for k in MODELS:
        md.append(f"| {DISPLAY[k]} | `{bind[f'ckpt_{k}']['sha']}` |")
    md += ["", "## Results", "",
           f"- regional crop evaluations: **{total_crops}** (expected 1952)",
           f"- case-model rows: **{len(case_df)}** (expected 412)",
           f"- component-model rows: **{len(comp_df)}** (expected 608)",
           f"- model-summary rows: **{len(summary_df)}** (expected 4)",
           f"- localizer forwards: **0**",
           f"- proposal regeneration: **0**",
           f"- new global forwards: **0**", "",
           f"**next_action: WAIT_FOR_SUPERVISOR_H2B_OUTCOME_ADJUDICATION_AUTHORIZATION**", ""]
    (AUDITS / "post_phase13_h2b_b2_downstream_integrity.md").write_text("\n".join(md), encoding="utf-8")

    print("\n=== H2B-B2 COMPLETE ===", flush=True)
    print(f"case-model: {len(case_df)} rows", flush=True)
    print(f"component-model: {len(comp_df)} rows", flush=True)
    print(f"model-summary: {len(summary_df)} rows", flush=True)
    print(f"regional crops: {total_crops}", flush=True)
    return {"status": "PASS", "case_df": case_df, "comp_df": comp_df, "summary_df": summary_df}


if __name__ == "__main__":
    main()
