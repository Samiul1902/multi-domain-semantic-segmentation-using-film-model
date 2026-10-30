#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase29 PHASE D - PREDICTION HASH BARRIER (§10) + GT SCORING (§12-§13).

Two strictly ordered stages:

  STAGE A (image-only, NO GT):
      Rebuild, for each executed seed (123, 3407) and for the reused seed42
      evidence, the FULL final routed probability map for all 808 VAL808 rows
      from the canonical shared-G cache + the seed decision table.
      Write the per-seed final-probability .npy + the decision/derived artifacts,
      then hash ALL of them -> emit PREDICTION_HASH_BARRIER_PASS.
      VAL808 GT MUST NOT be read in this stage.

  STAGE B (GT scoring, ONLY after the barrier):
      Read VAL808 GT masks for the first (and only) time, compute Dice and
      DeltaDice, bootstrap the macro-domain equal-weight estimand with the
      frozen Phase27 machinery, and write the §13 per-seed continuity metrics.

seed42: §11 reuse-only.  Its canonical final probability is reconstructed from
the FROZEN Phase27 artifacts (phase27_val808_final_prob_f16.npy) - the model is
NOT rerun.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase29_phase_d_hash_barrier_and_scoring.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase29_phase_d_common as D  # noqa: E402
import phase29_phase_d_canonical_cache as C  # noqa: E402
import phase27_exec_common as E27  # noqa: E402

sys.path.insert(0, str(D.ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import torch  # noqa: E402
from PIL import Image, ImageOps  # noqa: E402

from src.data.barr_roi import (  # noqa: E402
    REGIONAL_CANVAS_RESOLUTION,
    REGIONAL_INPUT_RESOLUTION,
)
from src.metrics.evaluation_metrics import (  # noqa: E402
    binary_confusion_counts,
    dice as dice_fn,
)
from src.models.barr.regional_refiner import BARRRegionalRefinerV1  # noqa: E402
from src.utils.device import get_device  # noqa: E402
from src.utils.test_lock import verify_test_lock  # noqa: E402

say = print

CANON = C.CANON_ROOT
CANON_D_ROOT = D.ROOT / "data_cache" / "phase29_phase_d_canonical"
EXEC_SEEDS = [123, 3407]
SEG = D.SEGMENTATION_OUTPUT_THRESHOLD
CANVAS = D.CANVAS
DOMAINS = D.DOMAINS

PHASE27_FINAL_PROB = D.ROOT / D.PHASE27_FINAL_PROB
PHASE27_FINAL_PROB_SHA = D.PHASE27_FINAL_PROB_SHA


# ------------------------------------------------------------------ helpers ---
def full_field_gt(mask_path, size=CANVAS):
    img = Image.open(mask_path).convert("L")
    w, h = img.size
    scale = min(size / w, size / h)
    rw, rh = max(1, round(w * scale)), max(1, round(h * scale))
    img = img.resize((rw, rh), Image.Resampling.NEAREST)
    left, top = (size - rw) // 2, (size - rh) // 2
    img = ImageOps.expand(img, (left, top, size - rw - left, size - rh - top))
    return (np.asarray(img) > 0).astype(np.uint8)


def canon_dice(pred_bin, gt_bin):
    return float(dice_fn(binary_confusion_counts(pred_bin, gt_bin)))


def image_only_transform(image, size=REGIONAL_CANVAS_RESOLUTION):
    image = image.convert("RGB")
    width, height = image.size
    scale = min(size / width, size / height)
    rw, rh = max(1, round(width * scale)), max(1, round(height * scale))
    image = image.resize((rw, rh), Image.Resampling.BILINEAR)
    left, top = (size - rw) // 2, (size - rh) // 2
    image = ImageOps.expand(image, (left, top, size - rw - left, size - rh - top))
    return np.transpose(np.asarray(image, dtype=np.float32).copy(), (2, 0, 1)) / 255.0


def crop_and_resize_vec(arr, geom, out_size):
    from PIL import Image as _I
    cy1, cy2 = int(geom["clip_y1"]), int(geom["clip_y2"])
    cx1, cx2 = int(geom["clip_x1"]), int(geom["clip_x2"])
    window = np.asarray(arr)[..., cy1:cy2, cx1:cx2]
    pads = [(0, 0)] * (window.ndim - 2) + [
        (int(geom["pad_top"]), int(geom["pad_bottom"])),
        (int(geom["pad_left"]), int(geom["pad_right"]))]
    window = np.pad(window, pads, mode="constant", constant_values=0)
    if window.ndim == 2:
        window = window[None, ...]
    channels = []
    for ch in window:
        pil = _I.fromarray(np.ascontiguousarray(ch, dtype=np.float32), mode="F")
        channels.append(np.asarray(pil.resize((out_size, out_size),
                                              _I.Resampling.BILINEAR), dtype=np.float32))
    return np.stack(channels, axis=0)


def fuse_full_field(p_global, refined_crop_256, geom):
    from PIL import Image as _I
    side = int(geom["crop_side_pixels"])
    clip_y1, clip_y2 = int(geom["clip_y1"]), int(geom["clip_y2"])
    clip_x1, clip_x2 = int(geom["clip_x1"]), int(geom["clip_x2"])
    pad_top, pad_left = int(geom["pad_top"]), int(geom["pad_left"])
    pil = _I.fromarray(np.ascontiguousarray(refined_crop_256, dtype=np.float32), mode="F")
    square = np.asarray(pil.resize((side, side), _I.Resampling.BILINEAR), dtype=np.float32)
    out = np.asarray(p_global, dtype=np.float32).copy()
    out[clip_y1:clip_y2, clip_x1:clip_x2] = square[pad_top:pad_top + (clip_y2 - clip_y1),
                                                   pad_left:pad_left + (clip_x2 - clip_x1)]
    return out


def rebuild_final_prob(s, device, gp, geo, rows, dec, info):
    """Rebuild the FULL final routed float32 prob map (NO GT)."""
    ids = [str(r["sample_id"]) for r in rows]
    r = BARRRegionalRefinerV1()
    r.load_state_dict(torch.load(D.ROOT / info["rpsi_final"], map_location="cpu",
                                 weights_only=False)["model_state"])
    r.eval(); r.requires_grad_(False); r.to(device)
    final_prob = np.empty_like(np.asarray(gp, dtype=np.float32))
    n_refiner = 0
    for i in range(len(ids)):
        sid = ids[i]
        sel = dec[i]["selected"] == "True"
        src = dec[i]["final_source"]
        if (not sel) or src != "REFINED":
            final_prob[i] = np.asarray(gp[i], dtype=np.float32)
            continue
        geom = geo.get(sid)
        assert geom is not None, sid
        rgb = image_only_transform(Image.open(rows[i]["image_path"]))
        rin = np.concatenate([
            crop_and_resize_vec(rgb, geom, REGIONAL_INPUT_RESOLUTION).astype(np.float32),
            crop_and_resize_vec(np.asarray(gp[i], dtype=np.float32), geom,
                                REGIONAL_INPUT_RESOLUTION).astype(np.float32)], axis=0)
        with torch.inference_mode():
            rt = torch.from_numpy(np.ascontiguousarray(rin))[None].to(device)
            refined = torch.sigmoid(r(rt).float())[0, 0].cpu().numpy()
        n_refiner += 1
        final_prob[i] = fuse_full_field(np.asarray(gp[i], dtype=np.float32), refined, geom)
    return final_prob, n_refiner


# ------------------------------------------------------------------ bootstrap --
def domain_stratified_group_bootstrap(delta, domains, groups, seed=42, B=2000):
    """Frozen Phase27 machinery: macro-domain equal-weight, domain-stratified
    group bootstrap, PCG64(seed), percentile 2.5/97.5."""
    rng = np.random.Generator(np.random.PCG64(seed))
    delta = np.asarray(delta, dtype=np.float64)
    dom_arr = np.asarray(domains)
    grp_arr = np.asarray(groups)
    # per-domain group -> row index lists
    per_dom = {}
    for x in DOMAINS:
        dm = dom_arr == x
        gd = {}
        for gi, g in enumerate(grp_arr[dm]):
            gd.setdefault(g, []).append(np.where(dm)[0][gi])
        per_dom[x] = {g: np.asarray(v) for g, v in gd.items()}
    boot = np.empty(B, dtype=np.float64)
    for b in range(B):
        dom_means = []
        for x in DOMAINS:
            gd = per_dom[x]
            keys = list(gd.keys())
            idx = rng.integers(0, len(keys), size=len(keys))
            rows_idx = np.concatenate([gd[keys[k]] for k in idx])
            dom_means.append(delta[rows_idx].mean())
        boot[b] = np.mean(dom_means)
    return {
        "point": float(np.mean([delta[dom_arr == x].mean() for x in DOMAINS])),
        "ci_low": float(np.percentile(boot, 2.5)),
        "ci_high": float(np.percentile(boot, 97.5)),
        "n_boot": B, "seed": seed, "method": "DOMAIN_STRATIFIED_GROUP_BOOTSTRAP",
        "rng": "numpy.random.Generator(numpy.random.PCG64(42))",
        "percentiles": [2.5, 97.5],
    }


# ------------------------------------------------------------------ main ------
def main() -> int:
    t0 = time.time()
    verify_test_lock(str(D.ROOT)); say("TEST lock verified")
    device = get_device(require_cuda=True)
    say(f"device={device} torch={torch.__version__} cuda={torch.version.cuda}")

    rows = D.canonical_val808_order()
    ids = [str(r["sample_id"]) for r in rows]
    domains = [r["dataset"] for r in rows]
    groups = [(("PATIENT::" + r["patient_id"]) if r["dataset"] == "KUB"
               else ("SINGLETON::" + r["dataset"] + "::" + str(r["sample_id"])))
              for r in rows]
    assert len(groups) == 808
    assert len(set(groups)) == D.VAL808_TOTAL_GROUPS, len(set(groups))

    gp = np.load(CANON / D.SHARED_CACHE_FILES["global_prob"])
    geo = D.read_json(CANON / D.SHARED_CACHE_FILES["roi_geometry"])["geometry"]

    # ================= STAGE A: image-only, NO GT read ==================== #
    say("")
    say("=" * 78)
    say("STAGE A: prediction rebuild + hash barrier (NO GT READ)")
    say("=" * 78)
    stage_a_shas = {}
    per_seed_a = {}

    for s in EXEC_SEEDS:
        info = D.SEED_INFO[s]
        dec = list(D.read_csv_rows(
            CANON_D_ROOT / f"seed{s}" /
            f"phase29_phase_d_canonical_seed{s}_val808_decisions.csv"))
        assert [r["sample_id"] for r in dec] == ids, "decision order != canonical"
        fp, n_ref = rebuild_final_prob(s, device, gp, geo, rows, dec, info)
        outdir = CANON_D_ROOT / f"seed{s}"
        outdir.mkdir(parents=True, exist_ok=True)
        fp16 = fp.astype(np.float16)
        fp_path = outdir / f"phase29_phase_d_canonical_seed{s}_val808_final_prob_f16.npy"
        np.save(fp_path, fp16)
        per_seed_a[s] = {"final_prob_f16_sha256": D.sha256_file(fp_path),
                         "n_refiner_forwards": n_ref,
                         "final_prob_shape": list(fp16.shape)}
        # hash the decision table too
        stage_a_shas[f"seed{s}_decisions"] = D.sha256_file(
            outdir / f"phase29_phase_d_canonical_seed{s}_val808_decisions.csv")
        stage_a_shas[f"seed{s}_final_prob_f16"] = per_seed_a[s]["final_prob_f16_sha256"]
        say(f"  seed{s}: final_prob={fp16.shape} refiner_fwd={n_ref} "
            f"sha={per_seed_a[s]['final_prob_f16_sha256'][:16]}")

    # seed42 reuse-only: canonical final prob is the FROZEN Phase27 artifact
    assert D.sha256_file(PHASE27_FINAL_PROB) == PHASE27_FINAL_PROB_SHA, \
        "Phase27 final prob drifted"
    stage_a_shas["seed42_final_prob_f16_REUSED_phase27"] = PHASE27_FINAL_PROB_SHA
    # seed42 decision evidence = Phase27 predictions CSV (frozen)
    p27_pred = D.ROOT / D.PHASE27_CACHE_ARTIFACTS[3][1]
    stage_a_shas["seed42_predictions_REUSED_phase27"] = D.sha256_file(p27_pred)
    per_seed_a[42] = {"final_prob_f16_sha256": PHASE27_FINAL_PROB_SHA,
                      "reused_from": "phase27_barr_preservation_v1_0",
                      "rerun": False}
    say(f"  seed42: REUSED phase27 final prob sha={PHASE27_FINAL_PROB_SHA[:16]} (NOT rerun)")

    barrier = {
        "artifact": "phase29_phase_d_prediction_hash_barrier",
        "phase": 29, "phase_label": "PHASE_D", "section": "§10",
        "stage": "PREDICTION_HASH_BARRIER",
        "prediction_hashes": stage_a_shas,
        "all_predictions_hashed_before_gt": True,
        "gt_reads_at_hash_time": 0,
        "val808_gt_reads_stage_a": 0,
        "val808_images_read_stage_a": 0,   # images read earlier in cache build
        "barrier_token": "PREDICTION_HASH_BARRIER_PASS",
        "seed42_reuse_only": True, "seed42_rerun": False,
        "generated_utc": D.now_utc(), "all_pass": True,
    }
    D.write_json(barrier, D.AUD / "phase29_phase_d_prediction_hash_barrier.json")
    say("")
    say(">>> PREDICTION_HASH_BARRIER_PASS")

    # ================= STAGE B: GT scoring (only after barrier) =========== #
    say("")
    say("=" * 78)
    say("STAGE B: VAL808 GT scoring (FIRST and ONLY GT read)")
    say("=" * 78)
    gt = np.stack([full_field_gt(r["mask_path"]) for r in rows])
    say(f"  GT read: {gt.shape} val808_gt_reads={len(ids)}")

    # ---- shared global dice (identical to Phase27 global) ---------------- #
    g_bin = (np.asarray(gp, dtype=np.float32) >= SEG).astype(np.uint8)
    g_dice = np.array([canon_dice(g_bin[i], gt[i]) for i in range(len(ids))],
                      dtype=np.float64)

    final_probs = {}
    decs = {}
    for s in EXEC_SEEDS:
        final_probs[s] = np.load(
            CANON_D_ROOT / f"seed{s}" /
            f"phase29_phase_d_canonical_seed{s}_val808_final_prob_f16.npy"
        ).astype(np.float32)
        decs[s] = list(D.read_csv_rows(
            CANON_D_ROOT / f"seed{s}" /
            f"phase29_phase_d_canonical_seed{s}_val808_decisions.csv"))
    # seed42: frozen Phase27 final prob (f16) + frozen decisions
    final_probs[42] = np.load(PHASE27_FINAL_PROB).astype(np.float32)
    p27 = pd.read_csv(p27_pred)
    p27["sample_id"] = p27["sample_id"].astype(str)
    p27 = p27.set_index("sample_id").loc[ids].reset_index()
    decs[42] = []
    for _, rr in p27.iterrows():
        sel = rr["router_decision"] == "EXECUTE"
        src = ("REFINED" if str(rr["state_machine_branch"]) == "EXECUTE_THEN_ACCEPT"
               else "GLOBAL")
        decs[42].append({
            "sample_id": str(rr["sample_id"]), "domain": rr["dataset"],
            "selected": "True" if sel else "False",
            "safety_accept": ("True" if str(rr["state_machine_branch"])
                              == "EXECUTE_THEN_ACCEPT" else "False"),
            "safety_score": ("" if rr["somega_accept"] == "" else
                             repr(float(rr["somega_accept"]))),
            "final_source": src,
            "router_score": ("" if rr["router_utility"] == "" else
                             repr(float(rr["router_utility"]) + D.LAMBDA_C_FLOAT))})

    metrics_by_seed = {}
    per_seed = {}
    for s in D.MASTER_SEEDS:
        fp = final_probs[s]
        f_bin = (fp >= SEG).astype(np.uint8)
        f_dice = np.array([canon_dice(f_bin[i], gt[i]) for i in range(len(ids))],
                          dtype=np.float64)
        delta = f_dice - g_dice
        boot = domain_stratified_group_bootstrap(delta, domains, groups)
        boot_noninferior = bool(boot["ci_low"] > -E27.NONINFERIORITY_MARGIN)
        dec = decs[s]
        sel = np.array([d["selected"] == "True" for d in dec])
        acc = np.array([d["safety_accept"] == "True" for d in dec])
        ref = np.array([d["final_source"] == "REFINED" for d in dec])
        per_dom = {}
        for x in DOMAINS:
            m = np.array([d == x for d in domains])
            per_dom[x] = {
                "n": int(m.sum()),
                "global_dice": float(g_dice[m].mean()),
                "final_dice": float(f_dice[m].mean()),
                "delta_dice": float(delta[m].mean())}
        metrics_by_seed[s] = {
            "macro_final_dice": float(np.mean([per_dom[x]["final_dice"] for x in DOMAINS])),
            "macro_global_dice": float(np.mean([per_dom[x]["global_dice"] for x in DOMAINS])),
            "macro_delta_dice": float(np.mean([per_dom[x]["delta_dice"] for x in DOMAINS])),
            "bootstrap": boot,
            "noninferiority_margin": E27.NONINFERIORITY_MARGIN,
            "noninferiority_ci_low_gt_minus_margin": boot_noninferior,
            "n_selected": int(sel.sum()), "selected_fraction": float(sel.mean()),
            "n_accepted": int(acc.sum()),
            "safety_accept_fraction": (float(acc.sum() / sel.sum()) if sel.any() else None),
            "n_final_refined": int(ref.sum()),
            "per_domain": per_dom}
        per_seed[s] = {"delta": delta, "g_dice": g_dice, "f_dice": f_dice, "dec": dec}
        say(f"  seed {s:>4}: macro_final={metrics_by_seed[s]['macro_final_dice']:.6f} "
            f"macro_delta={metrics_by_seed[s]['macro_delta_dice']:.6f} "
            f"CI=[{boot['ci_low']:.6f},{boot['ci_high']:.6f}] "
            f"sel={int(sel.sum())} acc={int(acc.sum())} refined={int(ref.sum())}")

    # ---- §13 per-seed continuity metrics artifact ------------------------ #
    D.write_json({
        "artifact": "phase29_phase_d_val808_per_seed_continuity",
        "phase": 29, "phase_label": "PHASE_D", "section": "§13",
        "population": "VAL808", "population_n": len(ids),
        "domains": DOMAINS, "macro_domain_equal_weight": True,
        "segmentation_output_threshold": SEG,
        "dice_scorer": "src.metrics.evaluation_metrics.dice",
        "gt_rule": "full_field_gt NEAREST 512 + centre pad, (arr>0)",
        "bootstrap": {"type": "DOMAIN_STRATIFIED_GROUP_BOOTSTRAP", "B": E27.N_BOOT,
                      "seed": 42, "rng": "PCG64(42)", "percentiles": [2.5, 97.5]},
        "metrics_by_seed": {str(s): metrics_by_seed[s] for s in D.MASTER_SEEDS},
        "numeric_reproducibility_pass_fail_gate": "NONE",
        "NO_NUMERIC_REPRODUCIBILITY_PASS_FAIL_GATE": True,
        "gt_used_for_final_metrics_only": True,
        "gt_derived_information_persisted": False,
        "best_seed_selected": False, "ranking_performed": False,
        "generated_utc": D.now_utc(), "all_pass": True,
    }, D.AUD / "phase29_phase_d_val808_per_seed_continuity.json")

    # ---- row-level prediction tables (with Dice) ------------------------- #
    for s in D.MASTER_SEEDS:
        p = per_seed[s]
        hdr = ["sample_id", "domain", "router_score", "router_threshold",
               "selected", "safety_score", "safety_accept", "final_source",
               "global_dice", "final_dice", "delta_dice"]
        rrows = []
        for i, sid in enumerate(ids):
            d = p["dec"][i]
            rrows.append([
                sid, domains[i], d.get("router_score", ""), "",
                d["selected"],
                ("" if d["safety_score"] == "" else repr(float(d["safety_score"]))),
                d["safety_accept"], d["final_source"],
                repr(float(p["g_dice"][i])), repr(float(p["f_dice"][i])),
                repr(float(p["delta"][i]))])
        D.write_csv(D.TAB / f"phase29_phase_d_canonical_seed{s}_val808_predictions.csv",
                    hdr, rrows)

    np.savez_compressed(
        CANON_D_ROOT / "phase29_phase_d_three_seed_val808_delta_dice.npz",
        sample_ids=np.array(ids),
        domains=np.array(domains),
        global_dice=g_dice,
        seed42_final_dice=per_seed[42]["f_dice"],
        seed123_final_dice=per_seed[123]["f_dice"],
        seed3407_final_dice=per_seed[3407]["f_dice"])

    say("")
    say("=" * 78)
    say(f"STAGE B COMPLETE elapsed={time.time()-t0:.0f}s")
    say("=" * 78)
    say("PHASE29_PHASE_D_HASH_BARRIER_AND_GT_SCORING_COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
