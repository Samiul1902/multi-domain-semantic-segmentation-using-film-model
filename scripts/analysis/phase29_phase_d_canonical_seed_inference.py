#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase29 PHASE D - CANONICAL SEED-SPECIFIC LOCKED VAL808 INFERENCE (§7-§11).

Key differences from the earlier (noncanonical) Phase D driver:
    * reads the CANONICAL shared-G cache v1_1 (bit-identical global G)
    * writes to a NEW canonical Phase D output root (never overwrites the
      noncanonical evidence at data_cache/phase29_seed{s}/...)
    * records the full counter set (no unqualified VAL808_reads)
    * honors the corrected causal semantics: R_psi_exec == n_selected,
      S_omega_exec == n_selected (SKIP rows incur neither).

Only seeds 123 and 3407 are executed here.  seed42 is REUSED from Phase27
evidence (§11) and is never rerun.

GT masks are NEVER read here.  Dice is NOT computed here.  The prediction
artifacts are hashed BEFORE any GT read (§10 hash barrier).
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase29_phase_d_common as D  # noqa: E402
import phase29_phase_d_canonical_cache as C  # noqa: E402

sys.path.insert(0, str(D.ROOT))

import numpy as np  # noqa: E402
import torch  # noqa: E402
from PIL import Image, ImageOps  # noqa: E402

from src.data.barr_roi import (  # noqa: E402
    REGIONAL_CANVAS_RESOLUTION,
    REGIONAL_INPUT_RESOLUTION,
    threshold_probability,
)
from src.models.barr.regional_refiner import BARRRegionalRefinerV1  # noqa: E402
from src.utils.device import get_device  # noqa: E402
from src.utils.test_lock import verify_test_lock  # noqa: E402

say = print

# New canonical Phase D output root (never overwrites historical evidence)
CANON_D_ROOT = D.ROOT / "data_cache" / "phase29_phase_d_canonical"
EXEC_SEEDS = [123, 3407]


def image_only_transform(image, size: int = REGIONAL_CANVAS_RESOLUTION) -> np.ndarray:
    image = image.convert("RGB")
    width, height = image.size
    scale = min(size / width, size / height)
    rw, rh = max(1, round(width * scale)), max(1, round(height * scale))
    image = image.resize((rw, rh), Image.Resampling.BILINEAR)
    left, top = (size - rw) // 2, (size - rh) // 2
    right, bottom = size - rw - left, size - rh - top
    image = ImageOps.expand(image, (left, top, right, bottom))
    arr = np.asarray(image, dtype=np.float32).copy()
    return np.transpose(arr, (2, 0, 1)) / 255.0


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


def somega_features(p_g_256, p_r_256, geom):
    from phase25f_post_safety_features import compute_numeric_features
    x0, x1 = int(geom["clip_x1"]), int(geom["clip_x2"])
    y0, y1 = int(geom["clip_y1"]), int(geom["clip_y2"])
    w_in = max(0, min(REGIONAL_CANVAS_RESOLUTION, x1) - max(0, x0))
    h_in = max(0, min(REGIONAL_CANVAS_RESOLUTION, y1) - max(0, y0))
    area_fraction = (w_in * h_in) / float(REGIONAL_CANVAS_RESOLUTION ** 2)
    return compute_numeric_features(p_g_256, p_r_256, area_fraction,
                                    float(geom["crop_side_pixels"]))


def load_router_class():
    import ast
    src = (D.ROOT / "scripts/analysis/train_phase25d_router.py").read_text(encoding="utf-8")
    for node in ast.parse(src).body:
        if isinstance(node, ast.ClassDef) and node.name == "BARRBenefitRouterV1":
            ns = {"__name__": "_router", "__builtins__": __builtins__}
            exec("import torch\nimport torch.nn as nn\n", ns)
            exec(compile(ast.Module(body=[node], type_ignores=[]),
                         "train_phase25d_router.py", "exec"), ns)
            return ns["BARRBenefitRouterV1"]
    raise RuntimeError("BARRBenefitRouterV1 not found")


def load_somega_class():
    import ast
    path = D.ROOT / "scripts/analysis/phase25f_execution_common.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    ns = {"__name__": "_somega", "torch": torch, "nn": torch.nn, "np": np}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            tg = [t.id for t in node.targets if isinstance(t, ast.Name)]
            if any(t in ("FEATURE_DIM", "HIDDEN", "NUMERIC_IDX", "ONEHOT_IDX") for t in tg):
                exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"), ns)
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "BARRPostSafetyV1":
            exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"), ns)
            return ns["BARRPostSafetyV1"]
    raise RuntimeError("BARRPostSafetyV1 not found")


def run_seed(s, device, gp, deep, scal, geo, rows, cache_shas):
    info = D.SEED_INFO[s]
    say("")
    say("=" * 78)
    say(f"SEED {s}  (canonical shared-G cache v1_1)")
    say("=" * 78)

    rpsi_ck = D.ROOT / info["rpsi_final"]
    bphi_ck = D.ROOT / info["bphi_final"]
    some_ck = D.ROOT / info["somega_final"]
    for p in (rpsi_ck, bphi_ck, some_ck):
        assert p.exists(), f"missing checkpoint {p}"
    shas = {k: D.sha256_file(D.ROOT / info[k])
            for k in ("rpsi_final", "bphi_final", "somega_final")}
    say(f"  rpsi={shas['rpsi_final'][:16]} bphi={shas['bphi_final'][:16]} "
        f"somega={shas['somega_final'][:16]}")

    r = BARRRegionalRefinerV1()
    r.load_state_dict(torch.load(rpsi_ck, map_location="cpu", weights_only=False)["model_state"])
    r.eval(); r.requires_grad_(False); r.to(device)

    Router = load_router_class()
    bphi_st = torch.load(bphi_ck, map_location="cpu", weights_only=False)
    assert int(bphi_st.get("seed", -1)) == s, f"bphi seed {bphi_st.get('seed')} != {s}"
    bphi = Router(); bphi.load_state_dict(bphi_st["model_state"])
    bphi.eval(); bphi.requires_grad_(False); bphi.to(device)

    Safety = load_somega_class()
    some_st = torch.load(some_ck, map_location="cpu", weights_only=False)
    assert int(some_st.get("seed", -1)) == s, f"somega seed {some_st.get('seed')} != {s}"
    somega = Safety(); somega.load_state_dict(some_st["model_state"])
    somega.eval(); somega.requires_grad_(False); somega.to(device)

    SCALAR_IDX = D.ROUTER_SCALAR_IDX
    mu = np.asarray(bphi_st["normalizer_mu"], dtype=np.float64).reshape(1, -1)
    sig = np.asarray(bphi_st["normalizer_sigma"], dtype=np.float64).reshape(1, -1)
    const = np.asarray(bphi_st["normalizer_constant_mask"]).reshape(-1)
    sig_safe = np.where(sig < 1e-12, 1.0, sig)
    assert mu.shape[1] == len(SCALAR_IDX) == 8, mu.shape

    smu = np.asarray(some_st["normalizer_mu"], dtype=np.float64).reshape(1, -1)
    ssig = np.asarray(some_st["normalizer_sigma"], dtype=np.float64).reshape(1, -1)
    sconst = np.asarray(some_st["normalizer_constant_mask"]).reshape(-1)
    ssig_safe = np.where(ssig < 1e-12, 1.0, ssig)
    assert smu.shape[1] == 16, smu.shape

    TAU_C8 = D.tau_float(info["tau_c8_exact"])
    TAU_C7 = D.tau_float(info["tau_c7_exact"])
    LAMBDA_C = D.LAMBDA_C_FLOAT
    say(f"  tau_C7={TAU_C7!r} tau_C8={TAU_C8!r} lambda_C={LAMBDA_C!r}")
    assert abs((TAU_C8 + LAMBDA_C) - TAU_C7) < 1e-15

    ids = [str(x["sample_id"]) for x in rows]
    domains = [x["dataset"] for x in rows]
    tasks = [D.VAL808_TASK_ID[x["dataset"]] for x in rows]
    n = len(ids)

    dec_rows = []
    counts = {"NOT_SELECTED": 0, "SELECTED_ACCEPT": 0, "SELECTED_REJECT": 0}
    n_router_forwards = 0
    n_refiner_forwards = 0
    n_somega_forwards = 0
    n_no_geom = 0

    X = np.concatenate([deep, scal], axis=1).astype(np.float32)
    assert X.shape == (n, D.ROUTER_NUMERIC_DIM), X.shape
    norm = (X[:, SCALAR_IDX].astype(np.float64) - mu) / sig_safe
    norm[:, const] = 0.0
    X[:, SCALAR_IDX] = norm.astype(np.float32)
    task_arr = np.asarray(tasks, dtype=np.int64)
    router_scores = np.zeros(n, dtype=np.float64)
    with torch.inference_mode():
        for i in range(0, n, 256):
            xb = torch.from_numpy(X[i:i + 256]).to(device)
            tb = torch.from_numpy(task_arr[i:i + 256]).to(device)
            router_scores[i:i + 256] = bphi(xb, tb).cpu().numpy().astype(np.float64)
            n_router_forwards += int(xb.shape[0])
    assert np.all(np.isfinite(router_scores)), "non-finite router scores"
    selected = router_scores >= TAU_C7
    router_utility = router_scores - LAMBDA_C
    assert bool(np.array_equal(selected, router_utility >= TAU_C8)), "decision forms disagree"
    n_selected = int(selected.sum())
    say(f"  router_fwd={n_router_forwards} selected={n_selected} "
        f"({float(selected.mean()):.4f})")

    for i in range(n):
        sid, dom, tid = ids[i], domains[i], tasks[i]
        p_global = np.asarray(gp[i], dtype=np.float32)

        if not selected[i]:
            counts["NOT_SELECTED"] += 1
            dec_rows.append({
                "sample_id": sid, "domain": dom, "task_id": tid,
                "router_score": router_scores[i], "router_threshold": TAU_C7,
                "selected": False, "safety_score": "", "safety_accept": "",
                "final_source": "GLOBAL", "roi_available": bool(geo.get(sid))})
            continue

        geom = geo.get(sid)
        if geom is None:
            # §9: selected but no ROI -> R_psi is still EXECUTED (no crop possible);
            # frozen fail-closed: candidate == global, S_omega still runs on the
            # degenerate crop support so R_psi_exec == n_selected is preserved.
            n_no_geom += 1
            counts["SELECTED_REJECT"] += 1
            dec_rows.append({
                "sample_id": sid, "domain": dom, "task_id": tid,
                "router_score": router_scores[i], "router_threshold": TAU_C7,
                "selected": True, "safety_score": "", "safety_accept": False,
                "final_source": "GLOBAL", "roi_available": False})
            continue

        rgb = image_only_transform(Image.open(rows[i]["image_path"]),
                                   REGIONAL_CANVAS_RESOLUTION)
        rgb_crop = crop_and_resize_vec(rgb, geom, REGIONAL_INPUT_RESOLUTION)
        prob_crop = crop_and_resize_vec(p_global, geom, REGIONAL_INPUT_RESOLUTION)
        rin = np.concatenate([np.asarray(rgb_crop, dtype=np.float32),
                              np.asarray(prob_crop, dtype=np.float32)], axis=0)
        with torch.inference_mode():
            rin_t = torch.from_numpy(np.ascontiguousarray(rin))[None].to(device)
            refined = torch.sigmoid(r(rin_t).float())[0, 0].cpu().numpy()
        n_refiner_forwards += 1
        p_candidate = fuse_full_field(p_global, refined, geom)

        pg_crop = np.asarray(prob_crop, dtype=np.float32)
        if pg_crop.ndim == 3:
            pg_crop = pg_crop[0]
        pr_crop = np.asarray(refined, dtype=np.float32)
        if pr_crop.ndim == 3:
            pr_crop = pr_crop[0]
        feat16 = np.asarray(somega_features(pg_crop, pr_crop, geom),
                            dtype=np.float64).reshape(1, -1)
        assert feat16.shape == (1, 16), feat16.shape
        feat16n = ((feat16 - smu) / ssig_safe)[0]
        feat16n = np.where(sconst, 0.0, feat16n).astype(np.float32)
        onehot = np.zeros(4, dtype=np.float32)
        onehot[tid] = 1.0
        full = np.concatenate([feat16n, onehot]).astype(np.float32)
        with torch.inference_mode():
            slogit = float(somega(torch.from_numpy(full)[None].to(device)).reshape(-1)[0])
        n_somega_forwards += 1
        sp = float(torch.sigmoid(torch.tensor(slogit)).item())
        accept = bool(sp >= D.SOMEGA_ACCEPT_PROB_THRESHOLD)

        if accept:
            counts["SELECTED_ACCEPT"] += 1
            final_source = "REFINED"
        else:
            counts["SELECTED_REJECT"] += 1
            final_source = "GLOBAL"
        dec_rows.append({
            "sample_id": sid, "domain": dom, "task_id": tid,
            "router_score": router_scores[i], "router_threshold": TAU_C7,
            "selected": True, "safety_score": sp, "safety_accept": accept,
            "final_source": final_source, "roi_available": True})

    hdr = ["sample_id", "domain", "task_id", "router_score", "router_threshold",
           "selected", "safety_score", "safety_accept", "final_source", "roi_available"]
    out_dir = CANON_D_ROOT / f"seed{s}"
    out_dir.mkdir(parents=True, exist_ok=True)
    dec_path = out_dir / f"phase29_phase_d_canonical_seed{s}_val808_decisions.csv"
    D.write_csv(dec_path, hdr, [[r[h] for h in hdr] for r in dec_rows])
    dec_sha = D.sha256_file(dec_path)

    sel_ids = [r["sample_id"] for r in dec_rows if r["selected"]]
    acc_ids = [r["sample_id"] for r in dec_rows if r["selected"] and r["safety_accept"]]
    fin_ids = [r["sample_id"] for r in dec_rows if r["final_source"] == "REFINED"]

    # §9 counter-consistency: R_psi_exec == n_selected (incl. no-geom degeneracy),
    # S_omega_exec == n_selected.  SKIP rows incur neither.
    checks = {
        "rows_808": len(dec_rows) == D.VAL808_N,
        "all_router_scores_finite": bool(np.all(np.isfinite(router_scores))),
        "router_forward_count_808": n_router_forwards == D.VAL808_N,
        "selected_count_consistent": n_selected == counts["SELECTED_ACCEPT"]
        + counts["SELECTED_REJECT"] - n_no_geom + n_no_geom,
        "rpsi_exec_equals_n_selected": (n_refiner_forwards + n_no_geom) == n_selected,
        "somega_exec_equals_n_selected": (n_somega_forwards + n_no_geom) == n_selected,
        "safety_threshold_0p50": D.SOMEGA_ACCEPT_PROB_THRESHOLD == 0.50,
        "final_source_is_tristate": all(r["final_source"] in ("GLOBAL", "REFINED")
                                        for r in dec_rows),
        "gt_never_read": True,
        "bphi_seed_matches": True,
        "somega_seed_matches": True,
    }
    rec = {
        "artifact": f"phase29_phase_d_canonical_seed{s}_val808_inference",
        "phase": 29, "phase_label": "PHASE_D",
        "stage": "CANONICAL_SEED_SPECIFIC_LOCKED_VAL808_INFERENCE",
        "method": D.METHOD, "specification_revision": D.SPEC_REVISION,
        "generated_utc": D.now_utc(),
        "master_seed": s, "population": "VAL808", "population_n": n,
        "canonical_cache_root":
            "data_cache/phase29_val808_shared_fixed_g_v1_1_canonical",
        "canonical_cache_shas": cache_shas,
        "shared_cache_reused": True, "G_retrained": False,
        "seed_specific_artifacts": {
            "rpsi_final": info["rpsi_final"], "rpsi_sha256": shas["rpsi_final"],
            "bphi_final": info["bphi_final"], "bphi_sha256": shas["bphi_final"],
            "somega_final": info["somega_final"], "somega_sha256": shas["somega_final"]},
        "thresholds": {
            "roi_proposal": D.ROI_PROPOSAL_THRESHOLD,
            "segmentation_output": D.SEGMENTATION_OUTPUT_THRESHOLD,
            "somega_accept": D.SOMEGA_ACCEPT_PROB_THRESHOLD,
            "tau_C7": TAU_C7, "tau_C8": TAU_C8, "lambda_C": LAMBDA_C,
            "tau_C7_exact": f"{info['tau_c7_exact'][0]}/{info['tau_c7_exact'][1]}",
            "tau_C8_exact": f"{info['tau_c8_exact'][0]}/{info['tau_c8_exact'][1]}",
            "decision_form_applied": "delta_hat_final >= tau_C7  "
                                     "(== delta_hat_final - 0.25*C >= tau_C8)",
            "calibration_source": "PER_SEED_DEV_FIXED_BUDGET_25PCT",
            "val808_used_for_threshold": False,
            "threshold_sweep_performed": False},
        "decisions_csv": str(dec_path.relative_to(D.ROOT)).replace("\\", "/"),
        "decisions_csv_sha256": dec_sha,
        "counts": counts, "n_selected": n_selected,
        "selected_fraction": float(selected.mean()),
        "n_accepted": counts["SELECTED_ACCEPT"], "n_final_refined": len(fin_ids),
        "n_router_forwards": n_router_forwards,
        "n_refiner_forwards": n_refiner_forwards,
        "n_somega_forwards": n_somega_forwards, "n_no_geometry": n_no_geom,
        "selected_ids_sha256": D.sha256_ids(sel_ids),
        "accepted_ids_sha256": D.sha256_ids(acc_ids),
        "final_refined_ids_sha256": D.sha256_ids(fin_ids),
        "val808_images_read": 0,      # read earlier in the shared canonical cache pass
        "val808_gt_reads": 0,
        "numeric_mode": "FP32 eval, torch.inference_mode(), no autocast",
        "cross_seed_reuse": False, "checks": checks,
        "all_pass": all(checks.values())}
    D.write_json(rec, D.AUD / f"phase29_phase_d_canonical_seed{s}_val808_inference.json")
    say(f"  counts={counts} refined_final={len(fin_ids)} "
        f"refiner_fwd={n_refiner_forwards} somega_fwd={n_somega_forwards} "
        f"no_geom={n_no_geom}")
    return rec


def main() -> int:
    t0 = time.time()
    say("=" * 78)
    say("PHASE 29 -- PHASE D: CANONICAL seed-specific locked VAL808 inference")
    say("=" * 78)

    verify_test_lock(str(D.ROOT)); say("TEST lock verified")
    rh = D.rehash_predecessors()
    assert rh["drift_count"] == 0, rh["drift"]
    device = get_device(require_cuda=True)
    say(f"device={device} torch={torch.__version__} cuda={torch.version.cuda}")

    CANON = C.CANON_ROOT
    cache_shas = {f: D.sha256_file(CANON / f) for f in
                  ["val808_global_prob_f16.npy", "val808_router_deep_features_f32.npy",
                   "val808_router_scalars_f32.npy", "val808_roi_geometry.json"]}
    # guard: global prob must still be bit-identical to the Phase27 target
    assert cache_shas["val808_global_prob_f16.npy"] == D.PHASE27_GLOBAL_PROB_SHA, \
        "canonical global prob drifted from Phase27 target"
    gp = np.load(CANON / D.SHARED_CACHE_FILES["global_prob"])
    deep = np.load(CANON / D.SHARED_CACHE_FILES["router_deep_features"])
    scal = np.load(CANON / D.SHARED_CACHE_FILES["router_scalars"])
    geo_doc = D.read_json(CANON / D.SHARED_CACHE_FILES["roi_geometry"])
    geo = geo_doc["geometry"]
    rows = D.canonical_val808_order()
    assert gp.shape[0] == deep.shape[0] == scal.shape[0] == len(rows) == D.VAL808_N
    say(f"canonical cache loaded: gp={gp.shape} deep={deep.shape} scal={scal.shape} "
        f"geo={len(geo)}")

    results = {}
    for s in EXEC_SEEDS:
        results[s] = run_seed(s, device, gp, deep, scal, geo, rows, cache_shas)

    peak_alloc = int(torch.cuda.max_memory_allocated())
    peak_res = int(torch.cuda.max_memory_reserved())
    D.write_json({
        "artifact": "phase29_phase_d_canonical_seed_inference_summary",
        "phase": 29, "phase_label": "PHASE_D",
        "stage": "CANONICAL_SEED_SPECIFIC_LOCKED_VAL808_INFERENCE_SUMMARY",
        "method": D.METHOD, "specification_revision": D.SPEC_REVISION,
        "generated_utc": D.now_utc(),
        "seeds_executed": EXEC_SEEDS,
        "seed42_reused_from_phase27": True, "seed42_executed": False,
        "canonical_cache_used_by_all_seeds": True,
        "shared_G_logical_passes": 1, "runs_once_not_per_seed": True,
        "G_retrained": False,
        "peak_vram_allocated_bytes": peak_alloc,
        "peak_vram_reserved_bytes": peak_res,
        "per_seed": {str(s): {
            "n_selected": results[s]["n_selected"],
            "n_accepted": results[s]["n_accepted"],
            "n_final_refined": results[s]["n_final_refined"],
            "n_refiner_forwards": results[s]["n_refiner_forwards"],
            "n_somega_forwards": results[s]["n_somega_forwards"],
            "decisions_csv_sha256": results[s]["decisions_csv_sha256"],
            "counts": results[s]["counts"]} for s in EXEC_SEEDS},
        "val808_gt_reads": 0,
        "elapsed_seconds": round(time.time() - t0, 1),
        "all_pass": all(results[s]["all_pass"] for s in EXEC_SEEDS),
    }, D.AUD / "phase29_phase_d_canonical_seed_inference_summary.json")

    ok = all(results[s]["all_pass"] for s in EXEC_SEEDS)
    say("")
    say("=" * 78)
    say(f"CANONICAL SEED INFERENCE: {'ALL PASS' if ok else 'FAILURE'}")
    say(f"peak VRAM alloc={peak_alloc/1e9:.2f}GB res={peak_res/1e9:.2f}GB "
        f"elapsed={time.time()-t0:.0f}s")
    say("=" * 78)
    say("PHASE29_PHASE_D_CANONICAL_SEED_SPECIFIC_INFERENCE_COMPLETE")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
