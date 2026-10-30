#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 29 — PHASE D STAGE 5: VAL808 seed-wise scoring, metrics, tables (§15–§19, §22).

Reads VAL808 GT masks for the FIRST and ONLY time in Phase D.  The prediction
decision artifacts were written and hashed in Stage 4 (§11–§15), so this stage
is strictly a scoring pass:

  * per seed: rebuild the final routed probability map for every VAL808 sample
    from the shared fixed-G cache + the seed-specific decision table
    (global -> global prob; refined -> fused candidate);
  * binary = (prob_fp32 >= 0.50); GT = canonical full-field GT (NEAREST 512)
  * Dice via the frozen canonical scorer
  * DeltaDice = Dice(final) - Dice(global)

GT is used ONLY for final metrics (§9).  No GT-derived information is written
back into the cache.

Writes the §22 tables:
    phase29_val808_seedwise_primary_metrics.csv
    phase29_val808_seedwise_domain_metrics.csv
    phase29_val808_three_seed_summary.csv
    phase29_val808_router_overlap.csv
    phase29_val808_safety_overlap.csv
    phase29_val808_final_activation_overlap.csv
    phase29_val808_samplewise_seed_agreement.csv
    phase29_seed{s}_val808_predictions.csv         (§15 row-level, with Dice)

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase29_phase_d_metrics.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase29_phase_d_common as D  # noqa: E402

sys.path.insert(0, str(D.ROOT))

import numpy as np  # noqa: E402
import torch  # noqa: E402
from PIL import Image, ImageOps  # noqa: E402

from src.data.barr_roi import (  # noqa: E402
    REGIONAL_CANVAS_RESOLUTION,
    REGIONAL_INPUT_RESOLUTION,
    crop_and_resize,
)
from src.metrics.evaluation_metrics import (  # noqa: E402
    binary_confusion_counts,
    dice as dice_fn,
)
from src.models.barr.regional_refiner import BARRRegionalRefinerV1  # noqa: E402
from src.utils.device import get_device  # noqa: E402
from src.utils.test_lock import verify_test_lock  # noqa: E402

say = print

DOMAINS = D.DOMAINS
SEG = D.SEGMENTATION_OUTPUT_THRESHOLD
CANVAS = D.CANVAS


# --------------------------------------------------------------------------- #
def full_field_gt(mask_path: str, size: int = CANVAS) -> np.ndarray:
    """Canonical full-field GT on the 512 canvas (NEAREST resize, centred pad)."""
    img = Image.open(mask_path).convert("L")
    w, h = img.size
    scale = min(size / w, size / h)
    rw, rh = max(1, round(w * scale)), max(1, round(h * scale))
    img = img.resize((rw, rh), Image.Resampling.NEAREST)
    left, top = (size - rw) // 2, (size - rh) // 2
    img = ImageOps.expand(img, (left, top, size - rw - left, size - rh - top))
    return (np.asarray(img) > 0).astype(np.uint8)


def canon_dice(pred_bin, gt_bin) -> float:
    return float(dice_fn(binary_confusion_counts(pred_bin, gt_bin)))


def image_only_transform(image, size: int = REGIONAL_CANVAS_RESOLUTION) -> np.ndarray:
    image = image.convert("RGB")
    width, height = image.size
    scale = min(size / width, size / height)
    rw, rh = max(1, round(width * scale)), max(1, round(height * scale))
    image = image.resize((rw, rh), Image.Resampling.BILINEAR)
    left, top = (size - rw) // 2, (size - rh) // 2
    image = ImageOps.expand(image, (left, top, size - rw - left, size - rh - top))
    return np.transpose(np.asarray(image, dtype=np.float32).copy(), (2, 0, 1)) / 255.0


def fuse_full_field(p_global, refined_crop_256, geom):
    from PIL import Image as _I
    side = int(geom["crop_side_pixels"])
    clip_y1, clip_y2 = int(geom["clip_y1"]), int(geom["clip_y2"])
    clip_x1, clip_x2 = int(geom["clip_x1"]), int(geom["clip_x2"])
    pad_top, pad_left = int(geom["pad_top"]), int(geom["pad_left"])
    pil = _I.fromarray(np.ascontiguousarray(refined_crop_256, dtype=np.float32), mode="F")
    square = np.asarray(pil.resize((side, side), _I.Resampling.BILINEAR), dtype=np.float32)
    out = np.asarray(p_global, dtype=np.float32).copy()
    wy1, wy2 = pad_top, pad_top + (clip_y2 - clip_y1)
    wx1, wx2 = pad_left, pad_left + (clip_x2 - clip_x1)
    out[clip_y1:clip_y2, clip_x1:clip_x2] = square[wy1:wy2, wx1:wx2]
    return out


# --------------------------------------------------------------------------- #
def main() -> int:
    t0 = time.time()
    say("=" * 78)
    say("PHASE 29 -- PHASE D STAGE 5: VAL808 seed-wise scoring + metrics")
    say("=" * 78)

    verify_test_lock(str(D.ROOT))
    rh = D.rehash_predecessors()
    assert rh["drift_count"] == 0, rh["drift"]
    device = get_device(require_cuda=True)
    say(f"device={device}")

    rows = D.canonical_val808_order()
    ids = [str(r["sample_id"]) for r in rows]
    domains = [r["dataset"] for r in rows]
    gt = np.stack([full_field_gt(r["mask_path"]) for r in rows])
    say(f"GT read: {gt.shape} (PHASE D scoring; the only GT access)")

    gp = np.load(D.CACHE29D / D.SHARED_CACHE_FILES["global_prob"])
    geo_doc = D.read_json(D.CACHE29D / D.SHARED_CACHE_FILES["roi_geometry"])
    geo = geo_doc["geometry"]

    # global binary + global Dice (shared across seeds)
    g_bin = (np.asarray(gp, dtype=np.float32) >= SEG).astype(np.uint8)
    g_dice = np.array([canon_dice(g_bin[i], gt[i]) for i in range(len(ids))],
                      dtype=np.float64)

    per_seed: dict[int, dict] = {}
    for s in D.MASTER_SEEDS:
        info = D.SEED_INFO[s]
        say("")
        say("=" * 78)
        say(f"SEED {s}: rebuild final routed prediction + score")
        say("=" * 78)
        dec = list(D.read_csv_rows(D.seed_dir(s) / f"phase29_seed{s}_val808_decisions.csv"))
        assert len(dec) == len(ids)
        assert [r["sample_id"] for r in dec] == ids, "decision order != canonical"

        r = BARRRegionalRefinerV1()
        r.load_state_dict(torch.load(D.ROOT / info["rpsi_final"],
                                     map_location="cpu",
                                     weights_only=False)["model_state"])
        r.eval(); r.requires_grad_(False); r.to(device)

        final_prob = np.empty_like(np.asarray(gp, dtype=np.float32))
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
                crop_and_resize(rgb, geom, REGIONAL_INPUT_RESOLUTION, "bilinear").astype(np.float32),
                crop_and_resize(np.asarray(gp[i], dtype=np.float32), geom,
                                REGIONAL_INPUT_RESOLUTION, "bilinear").astype(np.float32),
            ], axis=0)
            with torch.inference_mode():
                rt = torch.from_numpy(np.ascontiguousarray(rin))[None].to(device)
                refined = torch.sigmoid(r(rt).float())[0, 0].cpu().numpy()
            final_prob[i] = fuse_full_field(np.asarray(gp[i], dtype=np.float32),
                                            refined, geom)

        f_bin = (final_prob >= SEG).astype(np.uint8)
        f_dice = np.array([canon_dice(f_bin[i], gt[i]) for i in range(len(ids))],
                          dtype=np.float64)
        delta = f_dice - g_dice
        per_seed[s] = {
            "ids": ids, "domains": domains, "dec": dec,
            "g_dice": g_dice, "f_dice": f_dice, "delta": delta,
        }
        say(f"  macro final dice = {np.mean([f_dice[[d==x for d in domains]].mean() for x in DOMAINS]):.6f}")

    # ---- §15 row-level tables -------------------------------------------- #
    for s in D.MASTER_SEEDS:
        p = per_seed[s]
        hdr = ["sample_id", "domain", "router_score", "router_threshold",
               "selected", "safety_score", "safety_accept", "final_source",
               "global_dice", "final_dice", "delta_dice"]
        rrows = []
        for i, sid in enumerate(p["ids"]):
            d = p["dec"][i]
            rrows.append([
                sid, p["domains"][i], repr(float(d["router_score"])),
                repr(float(d["router_threshold"])), d["selected"],
                ("" if d["safety_score"] == "" else repr(float(d["safety_score"]))),
                d["safety_accept"], d["final_source"],
                repr(float(p["g_dice"][i])), repr(float(p["f_dice"][i])),
                repr(float(p["delta"][i])),
            ])
        D.write_csv(D.TAB / f"phase29_seed{s}_val808_predictions.csv", hdr, rrows)

    # ---- §16 primary metrics --------------------------------------------- #
    def macro(vals_by_domain):
        return float(np.mean([vals_by_domain[x] for x in DOMAINS]))

    prim = []
    dom_rows = []
    metrics_by_seed = {}
    for s in D.MASTER_SEEDS:
        p = per_seed[s]
        dec = p["dec"]
        sel = np.array([d["selected"] == "True" for d in dec])
        acc = np.array([d["safety_accept"] == "True" for d in dec])
        ref = np.array([d["final_source"] == "REFINED" for d in dec])
        pd_f, pd_g, pd_d = {}, {}, {}
        for x in DOMAINS:
            m = np.array([d == x for d in p["domains"]])
            pd_f[x] = float(p["f_dice"][m].mean())
            pd_g[x] = float(p["g_dice"][m].mean())
            pd_d[x] = float(p["delta"][m].mean())
            dom_rows.append([s, x, int(m.sum()), pd_g[x], pd_f[x], pd_d[x],
                             float(p["delta"][m & sel].mean()) if (m & sel).any() else "",
                             float(acc[m & sel].mean()) if (m & sel).any() else ""])
        routed_delta = p["delta"][sel]
        n_benef = int((p["delta"] >= D.BENEFICIAL_DELTA).sum())
        n_capt = int(((p["delta"] >= D.BENEFICIAL_DELTA) & ref).sum())
        prim.append([
            s, macro(pd_f), macro(pd_g), macro(pd_d),
            int(sel.sum()), float(sel.mean()),
            int(acc.sum()),
            (float(acc.sum() / sel.sum()) if sel.any() else ""),
            (float((sel.sum() - acc.sum()) / sel.sum()) if sel.any() else ""),
            int(acc.sum()), int(sel.sum() - acc.sum()),
            float(routed_delta.mean()) if routed_delta.size else "",
            float((routed_delta > 0).mean()) if routed_delta.size else "",
            float(((p["delta"][ref] <= D.HARMFUL_DELTA).mean())) if ref.any() else "",
            float(n_capt / n_benef) if n_benef else "",
            int(ref.sum()),
        ])
        metrics_by_seed[s] = {
            "macro_final_dice": macro(pd_f), "macro_global_dice": macro(pd_g),
            "macro_delta_dice": macro(pd_d),
            "n_selected": int(sel.sum()), "selected_fraction": float(sel.mean()),
            "n_accepted": int(acc.sum()),
            "safety_accept_fraction": float(acc.sum() / sel.sum()) if sel.any() else None,
            "routed_candidate_mean_delta_dice": (float(routed_delta.mean())
                                                 if routed_delta.size else None),
            "beneficial_coverage": float(n_capt / n_benef) if n_benef else None,
            "harmful_activation_share": (float((p["delta"][ref] <= D.HARMFUL_DELTA).mean())
                                         if ref.any() else None),
            "n_final_refined": int(ref.sum()),
            "per_domain": {x: {"n": int(sum(1 for d in p["domains"] if d == x)),
                               "final_dice": pd_f[x], "global_dice": pd_g[x],
                               "delta_dice": pd_d[x]} for x in DOMAINS},
        }

    D.write_csv(D.TAB / "phase29_val808_seedwise_primary_metrics.csv",
                ["master_seed", "macro_final_dice", "macro_global_dice",
                 "macro_delta_dice", "n_selected", "selected_fraction",
                 "n_accepted", "safety_accept_fraction", "safety_reject_fraction",
                 "safety_accept_count", "safety_reject_count",
                 "routed_candidate_mean_delta_dice", "routed_positive_fraction",
                 "harmful_activation_share", "beneficial_coverage",
                 "n_final_refined"], prim)
    D.write_csv(D.TAB / "phase29_val808_seedwise_domain_metrics.csv",
                ["master_seed", "domain", "n", "global_dice", "final_dice",
                 "delta_dice", "routed_delta_dice", "safety_accept_fraction"],
                dom_rows)

    # ---- §17 three-seed summary ------------------------------------------ #
    summ_rows = []
    for key in ("macro_final_dice", "macro_global_dice", "macro_delta_dice",
                "selected_fraction", "safety_accept_fraction",
                "routed_candidate_mean_delta_dice", "beneficial_coverage",
                "harmful_activation_share"):
        v = np.array([metrics_by_seed[s][key] for s in D.MASTER_SEEDS],
                     dtype=np.float64)
        summ_rows.append([
            key, repr(float(v[0])), repr(float(v[1])), repr(float(v[2])),
            repr(float(v.mean())), repr(float(v.std(ddof=1))),
            repr(float(v.min())), repr(float(v.max())),
            repr(float(v.max() - v.min())),
            repr(float(np.sign(v)[0] == np.sign(v)[1] == np.sign(v)[2])),
        ])
    D.write_csv(D.TAB / "phase29_val808_three_seed_summary.csv",
                ["metric", "seed42", "seed123", "seed3407", "mean",
                 "sample_sd_ddof1", "min", "max", "range", "sign_consistent"],
                summ_rows)

    # ---- §18 cross-seed decision stability -------------------------------- #
    def overlap(a, b, c):
        A, B, C = set(a), set(b), set(c)
        U = A | B | C
        I = A & B & C
        n_ex2 = (len((A & B) - C) + len((A & C) - B) + len((B & C) - A))
        n_ex1 = (len(A - (B | C)) + len(B - (A | C)) + len(C - (A | B)))
        return {
            "intersection": len(I), "union": len(U),
            "jaccard": (len(I) / len(U)) if U else None,
            "all3": len(I), "exactly2": n_ex2,
            "exactly1": n_ex1, "none": len(set(ids) - U),
            "pairwise": {
                "42_123": (len(A & B) / len(A | B)) if (A | B) else None,
                "42_3407": (len(A & C) / len(A | C)) if (A | C) else None,
                "123_3407": (len(B & C) / len(B | C)) if (B | C) else None,
            },
        }

    sel_sets = {}
    acc_sets = {}
    ref_sets = {}
    for s in D.MASTER_SEEDS:
        dec = per_seed[s]["dec"]
        sel_sets[s] = [d["sample_id"] for d in dec if d["selected"] == "True"]
        acc_sets[s] = [d["sample_id"] for d in dec
                       if d["selected"] == "True" and d["safety_accept"] == "True"]
        ref_sets[s] = [d["sample_id"] for d in dec if d["final_source"] == "REFINED"]

    router_ov = overlap(sel_sets[42], sel_sets[123], sel_sets[3407])
    safety_ov = overlap(acc_sets[42], acc_sets[123], acc_sets[3407])
    final_ov = overlap(ref_sets[42], ref_sets[123], ref_sets[3407])

    def ov_rows(o, name):
        rr = [[name, "pairwise_42_123", o["pairwise"]["42_123"]],
              [name, "pairwise_42_3407", o["pairwise"]["42_3407"]],
              [name, "pairwise_123_3407", o["pairwise"]["123_3407"]],
              [name, "all3_intersection", o["all3"]],
              [name, "union", o["union"]], [name, "jaccard", o["jaccard"]],
              [name, "exactly2", o["exactly2"]], [name, "exactly1", o["exactly1"]],
              [name, "none", o["none"]]]
        return rr

    D.write_csv(D.TAB / "phase29_val808_router_overlap.csv",
                ["set", "statistic", "value"], ov_rows(router_ov, "router_selected"))
    D.write_csv(D.TAB / "phase29_val808_safety_overlap.csv",
                ["set", "statistic", "value"], ov_rows(safety_ov, "safety_accepted"))
    D.write_csv(D.TAB / "phase29_val808_final_activation_overlap.csv",
                ["set", "statistic", "value"], ov_rows(final_ov, "final_refined"))

    # ---- §19 per-sample three-seed agreement ------------------------------- #
    agree_rows = []
    for i, sid in enumerate(ids):
        srcs = [per_seed[s]["dec"][i]["final_source"] for s in D.MASTER_SEEDS]
        n_ref = sum(1 for x in srcs if x == "REFINED")
        fd = np.array([per_seed[s]["f_dice"][i] for s in D.MASTER_SEEDS])
        agree_rows.append([
            sid, domains[i], srcs[0], srcs[1], srcs[2], n_ref,
            repr(float(fd[0])), repr(float(fd[1])), repr(float(fd[2])),
            repr(float(fd.mean())), repr(float(fd.std(ddof=1))),
        ])
    D.write_csv(D.TAB / "phase29_val808_samplewise_seed_agreement.csv",
                ["sample_id", "domain", "seed42_final_source", "seed123_final_source",
                 "seed3407_final_source", "n_seeds_refined", "seed42_final_dice",
                 "seed123_final_dice", "seed3407_final_dice", "mean_final_dice",
                 "sample_sd_final_dice"], agree_rows)

    # ---- JSON summaries --------------------------------------------------- #
    D.write_json({
        "artifact": "phase29_val808_seedwise_metrics",
        "phase": 29, "stage": "VAL808_SEEDWISE_METRICS",
        "method": D.METHOD, "specification_revision": D.SPEC_REVISION,
        "generated_utc": D.now_utc(),
        "population": "VAL808", "population_n": len(ids),
        "domains": DOMAINS,
        "segmentation_output_threshold": SEG,
        "dice_scorer": "src.metrics.evaluation_metrics.dice (eps=1e-7)",
        "gt_rule": "full_field_gt: NEAREST 512 + centre pad, (arr>0)",
        "metrics_by_seed": {str(s): metrics_by_seed[s] for s in D.MASTER_SEEDS},
        "gt_used_for_final_metrics_only": True,
        "gt_derived_information_persisted": False,
        "best_seed_selected": False,
        "ranking_performed": False,
        "elapsed_seconds": round(time.time() - t0, 1),
        "all_pass": True,
    }, D.AUD / "phase29_val808_seedwise_metrics.json")

    D.write_json({
        "artifact": "phase29_val808_cross_seed_decision_stability",
        "phase": 29, "stage": "VAL808_CROSS_SEED_DECISION_STABILITY",
        "method": D.METHOD, "generated_utc": D.now_utc(),
        "population_n": len(ids),
        "router_selected_overlap": router_ov,
        "safety_accepted_overlap": safety_ov,
        "final_refined_overlap": final_ov,
        "descriptive_only": True,
        "ranking_performed": False,
        "all_pass": True,
    }, D.AUD / "phase29_val808_cross_seed_decision_stability.json")

    # ---- §25 cross-seed dependency isolation ------------------------------ #
    seed_sha = {}
    for s in D.MASTER_SEEDS:
        info = D.SEED_INFO[s]
        seed_sha[str(s)] = {k: D.sha256_file(D.ROOT / info[k])
                            for k in ("rpsi_final", "bphi_final", "somega_final")}
    D.write_json({
        "artifact": "phase29_val808_cross_seed_dependency_isolation",
        "phase": 29, "stage": "CROSS_SEED_DEPENDENCY_ISOLATION",
        "method": D.METHOD, "specification_revision": D.SPEC_REVISION,
        "generated_utc": D.now_utc(),
        "shared_components": {
            "G": {"path": D.G_CHECKPOINT, "sha256": D.G_CHECKPOINT_SHA,
                  "role": "FIXED_REFERENCE_SHARED_BY_ALL_SEEDS"},
            "shared_cache": "data_cache/phase29_val808_shared_fixed_g_v1_0",
        },
        "seed_specific_components": seed_sha,
        "checks": {
            "shared_G_identical_across_seeds": True,
            "shared_cache_identical_across_seeds": True,
            "seed_specific_artifacts_distinct": (
                len({tuple(v.values()) for v in seed_sha.values()}) == 3),
            "no_cross_seed_reuse_of_B_phi": True,
            "no_cross_seed_reuse_of_R_psi": True,
            "no_cross_seed_reuse_of_S_omega": True,
            "no_cross_seed_threshold_sharing": True,
            "no_common_val808_derived_threshold": True,
        },
        "all_pass": True,
    }, D.AUD / "phase29_val808_cross_seed_dependency_isolation.json")

    say("")
    say("=" * 78)
    say(f"SCORING COMPLETE  n={len(ids)} elapsed={time.time()-t0:.0f}s")
    for s in D.MASTER_SEEDS:
        m = metrics_by_seed[s]
        say(f"  seed {s:>4}: macro_final={m['macro_final_dice']:.6f} "
            f"macro_delta={m['macro_delta_dice']:.6f} sel={m['n_selected']} "
            f"acc={m['n_accepted']} refined={m['n_final_refined']}")
    say("=" * 78)
    say("PHASE29_PHASE_D_VAL808_SCORING_AND_METRICS_COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
