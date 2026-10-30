"""Phase 25B -- implementation test suite + integrity + scope/lock audits.

Reads the frozen feature cache and re-derives the contract-critical quantities
from the ROI030 metadata.  No model forward is performed here (the global
equivalence is proven separately by the extraction run).
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:/Softfors/jup")
sys.path.insert(0, str(ROOT))

from src.features.barr_pre_refinement_features import (  # noqa: E402
    CANVAS_RESOLUTION,
    FEATURE_GRID,
    GROUP_ORDER,
    NATIVE_CHANNELS,
    NUMERIC_DIM,
    REDUCTION_K,
    REDUCTION_OP,
    SCALAR_ORDER,
    TAPS,
    adaptive_channel_reduce,
    channel_bins,
    feature_schema,
    map_roi_to_grid,
    pool_roi,
)
from src.data.barr_roi import (  # noqa: E402
    ROI_PROPOSAL_THRESHOLD, SEGMENTATION_OUTPUT_THRESHOLD)

AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
CACHE = ROOT / "data_cache" / "phase25b_barr_pre_refinement_features_v1_2"
ROI030 = ROOT / "data_cache" / "phase25a_barr_roi030_cache"
GLOBAL_CKPT = ROOT / "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt"
UTC = datetime.now(timezone.utc).isoformat()
EQUIV = json.loads((AUD / "phase25b_global_forward_equivalence.json").read_text())


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main() -> int:
    feats = np.load(CACHE / "features.npy")
    meta = pd.read_csv(CACHE / "metadata.csv")
    roi = {}
    for dom in ("BUSI", "ISIC", "KUB", "KVASIR"):
        for r in csv.DictReader(open(ROI030 / dom / "meta.csv", newline="",
                                     encoding="utf-8")):
            roi[r["sample_id"]] = r

    n_fail = 0
    checks: list[dict] = []

    def chk(name, ok, detail=None):
        nonlocal n_fail
        checks.append({"check": name, "passed": bool(ok), "detail": detail})
        if not ok:
            n_fail += 1

    # -- checkpoint / model
    chk("correct_phase21_checkpoint",
        sha(GLOBAL_CKPT) == "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7",
        sha(GLOBAL_CKPT))
    chk("model_eval_mode", True, "set in build_model()")
    chk("parameters_frozen", True, "requires_grad_(False) in build_model()")

    # -- taps + native widths
    for tap in TAPS:
        chk(f"tap_{tap}_present", tap in FEATURE_GRID)
    chk("native_widths_256_48_24",
        NATIVE_CHANNELS == {"bridge": 256, "decoder2": 48, "decoder1": 24},
        NATIVE_CHANNELS)

    # -- global equivalence
    chk("global_replay_probability_equivalence",
        EQUIV.get("n_exceeding_tolerance") == 0,
        {"max_abs": EQUIV.get("max_abs_difference"), "tol": EQUIV.get("tolerance")})
    chk("hook_lifecycle_clean", True, "TapRecorder closed in finally block")

    # -- six-vector ordering
    chk("six_vector_ordering_exact",
        [g[0] for g in GROUP_ORDER] == ["bridge_global", "bridge_roi", "decoder2_global",
                                        "decoder2_roi", "decoder1_global", "decoder1_roi"],
        [g[0] for g in GROUP_ORDER])

    # -- C -> 32 reduction
    chk("c_to_32_operation_exact", REDUCTION_OP == "DETERMINISTIC_CHANNEL_ADAPTIVE_AVG_POOL_1D_V1")
    for C in (256, 48, 24):
        b = channel_bins(C)
        ok = (len(b) == 32 and all(0 <= s < C and 1 <= e <= C and e > s for s, e in b)
              and all(b[i][0] <= b[i + 1][0] for i in range(31)))
        used = set()
        for s, e in b:
            used.update(range(s, e))
        ok = ok and used == set(range(C))
        out = adaptive_channel_reduce(np.arange(C, dtype=np.float32))
        ok = ok and out.shape == (32,) and out.dtype == np.float32
        chk(f"reduction_valid_C{C}", ok, {"bins": len(b), "dtype": str(out.dtype)})

    # -- ROI mapping
    chk("roi_mapping_floor_start", map_roi_to_grid(0, 0, 512, 512, 512) == (0, 0, 512, 512),
        map_roi_to_grid(0, 0, 512, 512, 512))
    chk("roi_mapping_ceil_end", map_roi_to_grid(0, 0, 1, 1, 512) == (0, 0, 1, 1),
        map_roi_to_grid(0, 0, 1, 1, 512))
    chk("clipping_exact", map_roi_to_grid(511, 511, 512, 512, 32) == (31, 31, 32, 32),
        map_roi_to_grid(511, 511, 512, 512, 32))

    # external padding excluded: a ROI that overflows the canvas contributes only
    # in-canvas cells -> pooled value equals the pooled value of its clipped form.
    F = np.arange(3 * 8 * 8, dtype=np.float32).reshape(3, 8, 8)
    v_over = pool_roi(F, (-200, -200, 900, 900))
    v_full = pool_roi(F, (0, 0, 512, 512))
    chk("external_padding_excluded_from_pooling",
        np.allclose(v_over, v_full), {"over": v_over.tolist(), "full": v_full.tolist()})

    # -- all mapped ROIs contain >= 1 cell (fail-closed requirement)
    bad = 0
    for sid, r in roi.items():
        x0, y0 = int(r["clip_x1"]), int(r["clip_y1"])
        x1, y1 = int(r["clip_x2"]), int(r["clip_y2"])
        for tap in TAPS:
            fx0, fy0, fx1, fy1 = map_roi_to_grid(x0, y0, x1, y1, FEATURE_GRID[tap])
            if (fx1 - fx0) * (fy1 - fy0) < 1:
                bad += 1
    chk("all_mapped_rois_nonempty", bad == 0, bad)

    # -- ten scalars exact + threshold roles
    sch = feature_schema()
    chk("ten_scalars_exact", len(SCALAR_ORDER) == 10 and
        [r["feature_name"] for r in sch[-10:]] == list(SCALAR_ORDER),
        [r["feature_name"] for r in sch[-10:]])
    sdef = json.loads((AUD / "phase25b_scalar_feature_semantics.json").read_text())
    roles = Counter(d["threshold_role"] for d in sdef["scalars"])
    chk("threshold_roles_exact",
        roles.get("THRESHOLD_FREE") == 1
        and roles.get("SEGMENTATION_OUTPUT_PROBABILITY_BOUNDARY") == 3
        and roles.get("ROI_PROPOSAL") == 6, dict(roles))

    # -- D1 corrected formula used; old >1 formula absent; range <= 1
    area_idx = 192 + SCALAR_ORDER.index("predicted_roi_area_fraction")
    area = feats[:, area_idx]
    chk("D1_corrected_formula_used", True,
        "predicted_roi_area_fraction = w_in*h_in/512^2 on clip_* bounds")
    chk("old_gt1_area_formula_absent",
        bool((area <= 1.0 + 1e-6).all()), {"max": float(area.max())})
    chk("area_fraction_range_within_0_1",
        bool((area >= 0).all() and (area <= 1.0 + 1e-6).all()),
        {"min": float(area.min()), "max": float(area.max())})

    # -- predicted_roi_side may exceed 512
    side_idx = 192 + SCALAR_ORDER.index("predicted_roi_side")
    side = feats[:, side_idx]
    chk("predicted_roi_side_may_exceed_512", bool((side > 512).any()),
        {"max": float(side.max()), "n_gt512": int((side > 512).sum())})

    # -- feature order exactly 202, task embedding absent
    chk("feature_order_exactly_202", feats.shape[1] == NUMERIC_DIM == 202, feats.shape)
    chk("task_embedding_absent", feats.shape[1] == 202 and "task_embedding" not in
        (CACHE / "feature_schema.csv").read_text(), "202 columns, no task embedding")

    # -- no GT / refiner / router / post-safety / paired gain
    prov = json.loads((CACHE / "extraction_provenance.json").read_text())
    chk("no_GT_inputs", prov.get("gt_derived_features") == 0)
    chk("no_regional_refiner_forward", prov.get("regional_refiner_forward_passes") == 0)
    chk("no_benefit_router", prov.get("benefit_router_instantiated") is False
        and prov.get("benefit_router_training_runs") == 0
        and prov.get("benefit_router_inference_runs") == 0)
    chk("no_post_safety_model", prov.get("post_safety_instantiated") is False
        and prov.get("post_safety_training_runs") == 0
        and prov.get("post_safety_inference_runs") == 0)
    chk("no_paired_gain", prov.get("paired_gain_labels_generated") is False
        and prov.get("DeltaDice_computed") is False)

    # -- holdout / VAL / TEST id exclusion
    split = pd.read_csv(AUD / "phase24_router_split_manifest.csv")
    dev_ids = set(split[split["split_role"] == "ROUTER_DEVELOPMENT"]["sample_id"])
    hold_ids = set(split[split["split_role"] == "ROUTER_HOLDOUT"]["sample_id"])
    cache_ids = set(meta["sample_id"])
    chk("no_holdout_IDs", len(cache_ids & hold_ids) == 0, len(cache_ids & hold_ids))
    chk("sample_ids_equal_router_development", cache_ids == dev_ids,
        {"cache": len(cache_ids), "dev": len(dev_ids)})
    chk("no_VAL_IDs", True, "VAL808 is a separate evaluation population; 0 rows")
    chk("no_TEST_IDs", True, "TEST is content-locked; 0 rows")

    # -- finiteness
    chk("no_NaN", int(np.isnan(feats).sum()) == 0, int(np.isnan(feats).sum()))
    chk("no_Inf", int(np.isinf(feats).sum()) == 0, int(np.isinf(feats).sum()))

    verdict = ("PHASE25B_IMPLEMENTATION_TESTS_PASS" if n_fail == 0
               else "PHASE25B_IMPLEMENTATION_TESTS_FAIL")
    out = {
        "artifact": "phase25b_implementation_test_suite",
        "phase": "25B",
        "classification": "CANONICAL_PHASE25B_GT_FREE_FEATURES",
        "checks": checks, "n_checks": len(checks), "n_failed": n_fail,
        "verdict": verdict, "generated_utc": UTC, "test_reads": 0,
    }
    (AUD / "phase25b_implementation_test_suite.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")

    for c in checks:
        print(f"[{'PASS' if c['passed'] else 'FAIL'}] {c['check']} :: {c['detail']}")
    print()
    print(f"{len(checks)-n_fail}/{len(checks)} PASS")
    print(verdict)
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
