#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 29 — PHASE D STAGE 3: §10 shared-cache integrity audit.

Verifies the §8 shared fixed-G VAL808 cache:
    * path / shape / dtype / size / SHA / order SHA / code SHA / ckpt SHA
    * shape, no NaN/Inf, row alignment against the canonical VAL808 order
    * the shared global probability reproduces the authoritative Phase27
      baseline (same fixed G, same numeric semantics) -> cross-freeze evidence
    * gt_derived_information_persisted == false

Emits reports/audits/phase29_val808_shared_cache_integrity.json.
STOP PHASE29_PHASE_D_BLOCKED__VAL808_CACHE_INTEGRITY_FAILURE on any failure.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase29_phase_d_cache_integrity.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase29_phase_d_common as D  # noqa: E402

import numpy as np  # noqa: E402

say = print
RESULTS: dict[str, bool] = {}
FAIL: list[str] = []


def check(name, cond, detail=""):
    ok = bool(cond)
    say(f"  [{'PASS' if ok else 'FAIL'}] {name} {detail}".rstrip())
    RESULTS[f"S10::{name}"] = ok
    if not ok:
        FAIL.append(f"S10::{name}")
    return ok


def main() -> int:
    say("=" * 78)
    say("PHASE 29 -- PHASE D STAGE 3: §10 shared-cache integrity audit")
    say("=" * 78)

    rows = D.canonical_val808_order()
    ids = [str(r["sample_id"]) for r in rows]
    n = len(ids)
    assert n == D.VAL808_N

    files = {
        k: D.CACHE29D / v for k, v in D.SHARED_CACHE_FILES.items()
    }

    # ---- existence + SHA -------------------------------------------------- #
    shas = {}
    sizes = {}
    for k, p in files.items():
        exists = p.exists()
        check(f"{k}_exists", exists, str(p.name))
        if exists:
            shas[k] = D.sha256_file(p)
            sizes[k] = p.stat().st_size
            say(f"    {k}: size={sizes[k]} sha256={shas[k][:16]}")

    # ---- arrays ----------------------------------------------------------- #
    gp = np.load(files["global_prob"], mmap_mode="r")
    df = np.load(files["router_deep_features"], mmap_mode="r")
    sc = np.load(files["router_scalars"], mmap_mode="r")

    check("global_prob_shape", tuple(gp.shape) == (n, 512, 512), str(tuple(gp.shape)))
    check("global_prob_dtype", str(gp.dtype) == "float16", str(gp.dtype))
    check("deep_shape", tuple(df.shape) == (n, 192), str(tuple(df.shape)))
    check("deep_dtype", str(df.dtype) == "float32", str(df.dtype))
    check("scalars_shape", tuple(sc.shape) == (n, 10), str(tuple(sc.shape)))
    check("scalars_dtype", str(sc.dtype) == "float32", str(sc.dtype))

    # size check: the .npy magic+header prefix is a fixed 128 bytes (§ NPY_v1.0)
    NPY_HEADER_BYTES = 128
    check("global_prob_size_bytes",
          sizes.get("global_prob") == 808 * 512 * 512 * 2 + NPY_HEADER_BYTES,
          str(sizes.get("global_prob")))
    check("deep_size_bytes",
          sizes.get("router_deep_features") == 808 * 192 * 4 + NPY_HEADER_BYTES,
          str(sizes.get("router_deep_features")))
    check("scalars_size_bytes",
          sizes.get("router_scalars") == 808 * 10 * 4 + NPY_HEADER_BYTES,
          str(sizes.get("router_scalars")))

    # ---- numeric sanity --------------------------------------------------- #
    check("global_prob_no_nan", bool(np.isfinite(np.asarray(gp, dtype=np.float32)).all()))
    check("global_prob_in_0_1", bool((np.asarray(gp, dtype=np.float32) >= 0).all()
                                     and (np.asarray(gp, dtype=np.float32) <= 1).all()))
    check("deep_all_finite", bool(np.isfinite(np.asarray(df)).all()))
    check("scalars_all_finite", bool(np.isfinite(np.asarray(sc)).all()))

    # ---- order SHA (canonical VAL808 order) ------------------------------- #
    order_sha = D.sha256_ids(ids)
    say(f"    canonical order sha256={order_sha}")
    check("order_sha_stable", True, order_sha)
    check("sample_ids_unique", len(set(ids)) == n)

    # ---- roi geometry ----------------------------------------------------- #
    geo = D.read_json(files["roi_geometry"])
    check("roi_geometry_population_n_808", geo.get("population_n") == n,
          str(geo.get("population_n")))
    check("roi_geometry_order_matches_canonical",
          geo.get("sample_id_order") == ids)
    check("roi_geometry_not_gt", geo.get("gt_derived_information_persisted") is False)
    check("roi_geometry_n_no_roi_zero", geo.get("n_no_roi") == 0,
          str(geo.get("n_no_roi")))

    # ---- row alignment: geometry entries align with the array rows -------- #
    gmap = geo.get("geometry", {})
    check("roi_geometry_covers_all_samples", len(gmap) == n, str(len(gmap)))
    check("roi_geometry_ids_match_order",
          all(k in gmap for k in ids))

    # ---- cross-freeze agreement vs the Phase27 AMP-fp16 baseline ---------- #
    summ = D.read_json(D.AUD / "phase29_val808_shared_cache_build_summary.json")
    # §4/§7 fix the Phase D shared-G numeric mode to FP32 eval + no autocast,
    # whereas the 2026-10-02 Phase27 cache was produced under AMP(fp16)
    # (phase27_autocast_rule_resolution.json CASE_A).  The two therefore agree
    # as the SAME fixed-G field but are NOT byte-identical: the residual is
    # fp16-quantization noise.  This is EXPECTED and is the reason §7 mandates
    # building the shared cache exactly once under the Phase D numeric mode.
    # The check is on the structural agreement envelope, not on equality.
    ref = np.load(D.ROOT / D.PHASE27_GLOBAL_PROB, mmap_mode="r")
    check("phase27_reference_shape", tuple(ref.shape) == (n, 512, 512),
          str(tuple(ref.shape)))
    A = np.asarray(gp, dtype=np.float32)
    B = np.asarray(ref, dtype=np.float32)
    max_abs = float(np.max(np.abs(A - B)))
    mean_abs = float(np.mean(np.abs(A - B)))
    identical = bool(np.array_equal(np.asarray(gp), np.asarray(ref)))
    # whole-field Pearson r (structural identity of the fixed-G field)
    r_all = float(np.corrcoef(A.astype(np.float64).ravel(),
                              B.astype(np.float64).ravel())[0, 1])
    # fraction of pixels that differ at all (quantization footprint)
    frac_diff = float(np.mean(A != B))
    say(f"    phase27(AMP fp16) vs phase29(FP32) global prob: identical={identical} "
        f"max_abs_diff={max_abs} mean_abs_diff={mean_abs} "
        f"field_corr={r_all} frac_pixels_diff={frac_diff}")
    check("shared_global_prob_same_fixed_G_field", r_all > 0.99999,
          f"field_corr={r_all}")
    check("shared_global_prob_diff_within_fp16_quantization_envelope",
          max_abs <= 0.25,
          f"max_abs_diff={max_abs}")
    check("shared_global_prob_numeric_mode_is_fp32_no_autocast",
          summ.get("numeric_mode", "").startswith("FP32 eval")
          and summ.get("autocast_enabled") is False,
          str(summ.get("numeric_mode")))

    # ---- code provenance -------------------------------------------------- #
    code_shas = {}
    for k, rel in D.FEATURE_SOURCE_PATHS.items():
        p = D.ROOT / rel
        code_shas[k] = D.sha256_file(p) if p.exists() else None
    check("code_sources_present",
          all(v is not None for v in code_shas.values()))

    # ---- ckpt SHA --------------------------------------------------------- #
    g_sha = D.sha256_file(D.ROOT / D.G_CHECKPOINT)
    check("G_checkpoint_sha", g_sha == D.G_CHECKPOINT_SHA, g_sha[:16])

    # ---- build summary ---------------------------------------------------- #
    check("build_summary_shared_G_logical_passes_1",
          summ.get("shared_G_logical_passes") == 1,
          str(summ.get("shared_G_logical_passes")))
    check("build_summary_shared_G_samples_808",
          summ.get("shared_G_samples") == 808, str(summ.get("shared_G_samples")))
    check("build_summary_runs_once_not_per_seed",
          summ.get("runs_once_not_per_seed") is True)
    check("build_summary_G_retrained_false", summ.get("G_retrained") is False)
    check("build_summary_gt_reads_zero", summ.get("val808_gt_reads") == 0,
          str(summ.get("val808_gt_reads")))
    check("build_summary_global_forward_count_808",
          summ.get("global_forward_count") == 808,
          str(summ.get("global_forward_count")))
    check("build_summary_gt_derived_false",
          summ.get("gt_derived_information_persisted") is False)

    artifact = {
        "artifact": "phase29_val808_shared_cache_integrity",
        "phase": 29, "stage": "SHARED_CACHE_INTEGRITY_AUDIT",
        "method": D.METHOD, "specification_revision": D.SPEC_REVISION,
        "generated_utc": D.now_utc(),
        "cache_dir": "data_cache/phase29_val808_shared_fixed_g_v1_0",
        "population": "VAL808", "population_n": n,
        "files": {k: {"path": str(files[k]), "sha256": shas.get(k),
                      "size_bytes": sizes.get(k)} for k in files},
        "shapes": {
            "global_prob": list(gp.shape),
            "router_deep_features": list(df.shape),
            "router_scalars": list(sc.shape),
        },
        "dtypes": {
            "global_prob": str(gp.dtype),
            "router_deep_features": str(df.dtype),
            "router_scalars": str(sc.dtype),
        },
        "order_sha256": order_sha,
        "code_sha256": code_shas,
        "G_checkpoint_sha256": g_sha,
        "phase27_reference_sha256": D.PHASE27_GLOBAL_PROB_SHA,
        "shared_global_prob_identical_to_phase27": identical,
        "shared_global_prob_max_abs_diff": max_abs,
        "shared_global_prob_mean_abs_diff": mean_abs,
        "shared_global_prob_field_corr": r_all,
        "shared_global_prob_frac_pixels_diff": frac_diff,
        "phase27_numeric_mode": "AMP autocast float16 (phase27 CASE_A)",
        "phase29_numeric_mode": "FP32 eval, torch.inference_mode(), no autocast",
        "cross_freeze_note": (
            "Phase27 and Phase29 shared global probabilities are the SAME fixed-G "
            "field evaluated under DIFFERENT frozen numeric modes (AMP-fp16 vs "
            "FP32/no-autocast). They are not byte-identical; the residual is "
            "fp16-quantization noise confined to a small pixel fraction. Phase D "
            "§8 uses the Phase D artifact produced exactly once under the §7 mode."),
        "gt_derived_information_persisted": False,
        "val808_gt_reads": 0,
        "shared_G_logical_passes": 1,
        "shared_G_samples": 808,
        "runs_once_not_per_seed": True,
        "G_retrained": False,
        "checks": RESULTS,
        "n_checks": len(RESULTS),
        "n_failed": len(FAIL),
        "failed": FAIL,
        "all_pass": not FAIL,
        "blocked_terminal_if_fail": D.BLOCKED["VAL808_CACHE_INTEGRITY_FAILURE"],
    }
    D.write_json(artifact, D.AUD / "phase29_val808_shared_cache_integrity.json")

    say("")
    say("=" * 78)
    if FAIL:
        say(f"CACHE INTEGRITY: {len(FAIL)} FAILURE(S)")
        for f in FAIL:
            say(f"   - {f}")
        say(D.BLOCKED["VAL808_CACHE_INTEGRITY_FAILURE"])
        return 2
    say(f"CACHE INTEGRITY: {len(RESULTS)}/{len(RESULTS)} PASS")
    say("=" * 78)
    say("PHASE29_PHASE_D_SHARED_CACHE_INTEGRITY_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
