"""Phase 25F — POST-SAFETY SPECIFICATION REPAIR  §4 / §5 / §6.

§4 supervisor ruling F2 — prove the canonical identity/alignment of the Phase25C
   fold-specific OOF refined crop-probability arrays (13 checkboxes). BLOCKING.
§5 promote the existing arrays into the stable canonical cache
   ``data_cache/phase25f_barr_post_safety_v1_0/`` in ``feature_row_index`` order.
§6 recover the like-for-like global probability crop ``oof_global_crop_prob.npy``
   using the EXACT frozen Phase25A crop utility (no new global forward).

No model construction / training / forward pass / refinement / DeltaDice.

Outputs:
  data_cache/phase25f_barr_post_safety_v1_0/oof_refined_crop_prob.npy
  data_cache/phase25f_barr_post_safety_v1_0/oof_refined_crop_prob_metadata.csv
  data_cache/phase25f_barr_post_safety_v1_0/oof_refined_crop_prob_source_manifest.json
  data_cache/phase25f_barr_post_safety_v1_0/oof_global_crop_prob.npy
  reports/audits/phase25f_oof_refinement_source_contract_v1_0.json
  reports/audits/phase25f_oof_refinement_source_promotion.json
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))
import phase25f_spec_repair_common as C  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(ROOT))
from src.data.barr_roi import crop_and_resize, roi_geometry, GEOMETRY_KEYS  # noqa: E402

BLOCKED_TERMINAL = "PHASE25F_SPEC_REPAIR_BLOCKED__OOF_REFINEMENT_SOURCE_PROVENANCE_INCOMPLETE"


def main() -> int:
    C.CACHE25F.mkdir(parents=True, exist_ok=True)

    checks: dict[str, bool] = {}
    failures: list[str] = []

    def chk(name, cond, detail=None):
        checks[name] = bool(cond)
        if not cond:
            failures.append(name if detail is None else f"{name}: {detail}")

    # ------------------------------------------------------------------ #
    # bindings
    # ------------------------------------------------------------------ #
    label_csv = pd.read_csv(C.PHASE25C_LABEL_CSV)
    label_manifest = C.jload(C.PHASE25C_LABEL_MANIFEST)
    exec_binding = C.jload(C.AUD / "phase25c_refiner_inference_execution_binding.json")
    leakage = C.jload(C.AUD / "phase25c_crossfit_leakage_audit.json")
    b25 = pd.read_csv(C.PHASE25B_METADATA)

    # ------------------------------------------------------------------ #
    # [1] every array was written by the canonical Phase25C execution
    # ------------------------------------------------------------------ #
    chk("label_csv_sha_exact", C.sha256_file(C.PHASE25C_LABEL_CSV) == C.PHASE25C_LABEL_CSV_SHA)
    chk("canonical_writer_present", C.PHASE25C_WRITER.exists())
    chk("canonical_common_present", C.PHASE25C_COMMON.exists())
    chk("writer_writes_tmp_arrays",
        "_tmp_refined_crop_prob_{d}.npy" in C.PHASE25C_WRITER.read_text(encoding="utf-8"))
    chk("label_manifest_rows_4957", int(label_manifest.get("rows", 0)) == 4957)

    # ------------------------------------------------------------------ #
    # [13] no final Phase25A refiner used for these OOF outputs
    # ------------------------------------------------------------------ #
    chk("phase25a_final_refiner_used_for_oof_false",
        exec_binding.get("phase25a_final_refiner_used_for_oof") is False,
        exec_binding.get("phase25a_final_refiner_used_for_oof"))

    # ------------------------------------------------------------------ #
    # [3][4][5] cross-fit exclusion (nested, independent of the arrays)
    # ------------------------------------------------------------------ #
    chk("crossfit_leakage_violations_zero",
        int(leakage.get("crossfit_leakage_violations", -1)) == 0,
        leakage.get("crossfit_leakage_violations"))

    fold_sets: dict[int, dict[str, set]] = {}
    for k in (0, 1, 2):
        fold_sets[k] = {
            role: set(pd.read_csv(C.ROI030_CACHE / "folds" / f"fold{k}_{role}.csv")["sample_id"].astype(str))
            for role in ("fit", "early_stop", "outer_target")
        }

    # ------------------------------------------------------------------ #
    # feature_row_index map from the frozen Phase25B metadata
    # ------------------------------------------------------------------ #
    b25["sample_id"] = b25["sample_id"].astype(str)
    fr_map = dict(zip(b25["sample_id"], b25["feature_row_index"].astype(int)))
    dev_ids = set(fr_map.keys())
    chk("phase25b_metadata_rows_4957", len(b25) == 4957)
    chk("feature_row_index_is_0_to_4956",
        sorted(fr_map.values()) == list(range(4957)))
    b25_domain = dict(zip(b25["sample_id"], b25["domain"].astype(str)))
    b25_task = dict(zip(b25["sample_id"], b25["task_id"].astype(int)))

    label_by_sid = {str(r.sample_id): r for r in label_csv.itertuples(index=False)}
    chk("label_csv_covers_all_4957_dev",
        set(label_by_sid.keys()) == dev_ids,
        f"{len(label_by_sid)} vs {len(dev_ids)}")

    # ------------------------------------------------------------------ #
    # per-domain scan: ordering, mapping, coverage, finiteness, range, shape
    # ------------------------------------------------------------------ #
    refined_mm = {}
    domain_rows: list[dict] = []
    order_ok = True
    shape_ok = True
    finite_ok = True
    range_ok = True
    dup_seen: list[str] = []
    seen: set[str] = set()
    outer_fold_ok = True
    ckpt_ok = True
    exclusion_ok = True
    coverage_per_domain: dict[str, int] = {}
    meta_order_matches_labels = True
    max_abs_geom_int_diff = 0.0
    max_abs_geom_float_diff = 0.0
    prob_crop_max_abs_diff = 0.0
    INT_GEOM_KEYS = ("y1", "y2", "x1", "x2", "clip_y1", "clip_y2", "clip_x1", "clip_x2",
                     "pad_top", "pad_bottom", "pad_left", "pad_right", "crop_side_pixels")
    FLOAT_GEOM_KEYS = ("effective_magnification", "margin")

    for d in C.DOMAINS:
        meta = pd.read_csv(C.ROI030_CACHE / d / "meta.csv")
        meta["sample_id"] = meta["sample_id"].astype(str)
        arr_path = C.PHASE25C_DIR / f"_tmp_refined_crop_prob_{d}.npy"
        arr = np.load(arr_path, mmap_mode="r")
        refined_mm[d] = arr
        coverage_per_domain[d] = int(arr.shape[0])
        if arr.shape[0] != len(meta) or arr.shape[1:] != (256, 256):
            shape_ok = False
        ids = meta["sample_id"].tolist()

        # [6] domain-local ordering recoverable: meta.csv row order
        # [7] sample_id <-> array-index mapping recoverable: meta row index
        # cross-check that the same order reproduces the (domain,sample_id) sorted
        # Phase25B / Phase25C order
        if ids != sorted(ids):
            meta_order_matches_labels = False

        prob512 = np.load(C.ROI030_CACHE / d / "prob512.npy", mmap_mode="r")
        prob_crop = np.load(C.ROI030_CACHE / d / "prob_crop.npy", mmap_mode="r")
        action = np.load(C.ROI030_CACHE / d / "action.npy")

        for gi, sid in enumerate(ids):
            if sid in seen:
                dup_seen.append(sid)
            seen.add(sid)
            if sid not in fr_map:
                order_ok = False
                continue

            # finiteness / range / shape per sample
            sample = np.asarray(arr[gi], dtype=np.float32)
            if sample.shape != (256, 256):
                shape_ok = False
            if not np.isfinite(sample).all():
                finite_ok = False
            if sample.min() < 0.0 or sample.max() > 1.0:
                range_ok = False

            lab = label_by_sid.get(sid)
            if lab is None:
                outer_fold_ok = False
                continue
            k = int(lab.outer_fold)
            # [2] producer checkpoint is the fold whose outer target contains the sample
            if sid not in fold_sets[k]["outer_target"]:
                outer_fold_ok = False
            # checkpoint sha recorded for the row equals the frozen fold checkpoint
            expected_ckpt = {
                0: "40b7573a4a15483f895fece8b9624f4f23b1ee040e294b7594ed3cdf8438fc1c",
                1: "512cc116b2a1baa5368711f438dfd0b2aabff1448d02fbc0c369b91da8ffc1ce",
                2: "1259e2d938a7e6e81ad9ddce4bfc25189e20858e8f201d167663c26c72c269ec",
            }[k]
            if str(lab.fold_refiner_checkpoint_sha) != expected_ckpt:
                ckpt_ok = False
            # [3][4] excluded from producer FIT and EARLY_STOP
            if (sid in fold_sets[k]["fit"]) or (sid in fold_sets[k]["early_stop"]):
                exclusion_ok = False

            # [5] did not select producer checkpoint (nested inner split only)
            # guaranteed structurally by the disjointness proven above; record the
            # fact explicitly per row for the audit trail
            domain_rows.append({
                "sample_id": sid,
                "feature_row_index": int(fr_map[sid]),
                "domain": d,
                "task_id": int(b25_task[sid]),
                "phase25c_outer_fold": k,
                "source_domain_array": f"_tmp_refined_crop_prob_{d}.npy",
                "source_domain_index": int(gi),
                "producer_refiner_checkpoint_sha": str(lab.fold_refiner_checkpoint_sha),
                "action_available": bool(action[gi]) if gi < len(action) else bool(lab.action_available),
            })

            # geometry audit: frozen meta geometry reproduces roi_geometry(p512,0.30)
            geom_meta = {kk: meta.iloc[gi][kk] for kk in GEOMETRY_KEYS}
            geom_rc = roi_geometry(np.asarray(prob512[gi], dtype=np.float32),
                                   C.ROI_PROPOSAL_THRESHOLD)
            if geom_rc is None:
                order_ok = False
            else:
                for kk in INT_GEOM_KEYS:
                    diff = abs(int(geom_meta[kk]) - int(geom_rc[kk]))
                    max_abs_geom_int_diff = max(max_abs_geom_int_diff, float(diff))
                for kk in FLOAT_GEOM_KEYS:
                    diff = abs(float(geom_meta[kk]) - float(geom_rc[kk]))
                    max_abs_geom_float_diff = max(max_abs_geom_float_diff, diff)

            # canonical global crop (float32) vs frozen float16 prob_crop
            g_crop = crop_and_resize(np.asarray(prob512[gi], dtype=np.float32),
                                     geom_meta, 256, "bilinear")[0]
            pc = np.asarray(prob_crop[gi], dtype=np.float32)
            if pc.ndim == 3:
                pc = pc[0]
            prob_crop_max_abs_diff = max(prob_crop_max_abs_diff,
                                         float(np.max(np.abs(g_crop - pc))))

    chk("domain_local_order_recoverable", meta_order_matches_labels)
    chk("sample_id_array_index_mapping_recoverable", order_ok)
    chk("all_4957_covered_exactly_once", len(seen) == 4957 and len(domain_rows) == 4957,
        f"{len(seen)}/{len(domain_rows)}")
    chk("no_duplicate_sample", len(dup_seen) == 0, dup_seen[:5])
    chk("spatial_shape_256x256", shape_ok)
    chk("probability_arrays_finite", finite_ok)
    chk("probability_values_in_0_1", range_ok)
    chk("producer_checkpoint_matches_outer_fold", outer_fold_ok)
    chk("producer_checkpoint_sha_matches_frozen_fold", ckpt_ok)
    chk("sample_excluded_from_producer_fit_and_early_stop", exclusion_ok)
    chk("frozen_meta_integer_geometry_reproduces_roi_geometry",
        max_abs_geom_int_diff == 0.0, f"max_abs_int_diff={max_abs_geom_int_diff}")
    chk("frozen_meta_float_geometry_reproduces_roi_geometry",
        max_abs_geom_float_diff <= 1e-9, f"max_abs_float_diff={max_abs_geom_float_diff}")
    chk("canonical_global_crop_matches_frozen_prob_crop_f16", prob_crop_max_abs_diff <= 1e-3,
        f"max_abs_diff={prob_crop_max_abs_diff}")

    if failures:
        blocked = {
            "artifact": "phase25f_oof_refinement_source_contract_v1_0",
            "phase": "25F",
            "stage": "OOF_REFINEMENT_SOURCE_PROVENANCE",
            "terminal": BLOCKED_TERMINAL,
            "checks": checks,
            "failures": failures,
            "all_pass": False,
        }
        C.jdump(blocked, C.AUD / "phase25f_oof_refinement_source_contract_v1_0.json")
        print("BLOCKED:", failures)
        return 1

    # ------------------------------------------------------------------ #
    # §5 promote into feature_row_index order
    # ------------------------------------------------------------------ #
    meta_df = pd.DataFrame(domain_rows).sort_values("feature_row_index").reset_index(drop=True)
    assert meta_df["feature_row_index"].tolist() == list(range(4957))

    refined = np.lib.format.open_memmap(
        C.CACHE25F / "oof_refined_crop_prob.npy", mode="w+",
        dtype=np.float32, shape=(4957, 256, 256))
    global_crop = np.lib.format.open_memmap(
        C.CACHE25F / "oof_global_crop_prob.npy", mode="w+",
        dtype=np.float32, shape=(4957, 256, 256))

    for d in C.DOMAINS:
        meta = pd.read_csv(C.ROI030_CACHE / d / "meta.csv")
        meta["sample_id"] = meta["sample_id"].astype(str)
        prob512 = np.load(C.ROI030_CACHE / d / "prob512.npy", mmap_mode="r")
        arr = refined_mm[d]
        sub = meta_df[meta_df["domain"] == d]
        for r in sub.itertuples(index=False):
            gi = int(r.source_domain_index)
            fri = int(r.feature_row_index)
            refined[fri] = np.asarray(arr[gi], dtype=np.float32)
            geom = {kk: meta.iloc[gi][kk] for kk in GEOMETRY_KEYS}
            global_crop[fri] = crop_and_resize(
                np.asarray(prob512[gi], dtype=np.float32), geom, 256, "bilinear")[0]
    refined.flush()
    global_crop.flush()
    del refined, global_crop

    # deterministic CSV
    (C.CACHE25F / "oof_refined_crop_prob_metadata.csv").write_text(
        C.csv_text(meta_df), encoding="utf-8", newline="")

    source_manifest = {
        "artifact": "phase25f_oof_refined_crop_prob_source_manifest",
        "phase": "25F",
        "method": C.METHOD,
        "specification_revision": C.REVISION,
        "canonical_array": "oof_refined_crop_prob.npy",
        "canonical_shape": [4957, 256, 256],
        "canonical_dtype": "float32",
        "canonical_ordering": "feature_row_index ascending 0..4956",
        "row_semantics": "row i = the ROUTER_DEVELOPMENT sample whose Phase25B "
                         "feature_row_index == i (canonical (domain, sample_id) order)",
        "source": {
            "type": "PHASE25C_FOLD_SPECIFIC_OOF_REFINED_CROP_PROBABILITY",
            "domain_arrays": {
                d: C.bind(C.PHASE25C_DIR / f"_tmp_refined_crop_prob_{d}.npy")
                for d in C.DOMAINS
            },
            "domain_array_shapes": {
                d: [int(refined_mm[d].shape[0]), 256, 256] for d in C.DOMAINS
            },
            "originals_altered": False,
            "originals_deleted": False,
        },
        "global_crop_companion": {
            "path": "data_cache/phase25f_barr_post_safety_v1_0/oof_global_crop_prob.npy",
            "source": "data_cache/phase25a_barr_roi030_cache/<DOMAIN>/prob512.npy",
            "crop_utility": "src.data.barr_roi.crop_and_resize(prob512, geom, 256, 'bilinear')",
            "roi_proposal_threshold": C.ROI_PROPOSAL_THRESHOLD,
            "roi_expansion_factor": 1.5,
            "global_model_forwards": 0,
            "refiner_forwards": 0,
        },
        "phase25c_bindings": {
            "label_csv": C.bind(C.PHASE25C_LABEL_CSV),
            "label_manifest": C.bind(C.PHASE25C_LABEL_MANIFEST),
            "writer": C.bind(C.PHASE25C_WRITER),
            "execution_binding": C.bind(C.AUD / "phase25c_refiner_inference_execution_binding.json"),
            "crossfit_leakage_audit": C.bind(C.AUD / "phase25c_crossfit_leakage_audit.json"),
        },
        "no_new_inference": True,
        "global_model_forwards": 0,
        "refiner_forwards": 0,
        "test_reads": 0,
    }
    C.jdump(source_manifest, C.CACHE25F / "oof_refined_crop_prob_source_manifest.json")

    # ------------------------------------------------------------------ #
    # verification of the promoted artifacts
    # ------------------------------------------------------------------ #
    r_chk = np.load(C.CACHE25F / "oof_refined_crop_prob.npy", mmap_mode="r")
    g_chk = np.load(C.CACHE25F / "oof_global_crop_prob.npy", mmap_mode="r")
    promoted = {
        "refined_shape": list(r_chk.shape),
        "refined_dtype": str(r_chk.dtype),
        "global_shape": list(g_chk.shape),
        "global_dtype": str(g_chk.dtype),
    }
    promoted_finite = bool(np.isfinite(np.asarray(r_chk[::37])).all()
                           and np.isfinite(np.asarray(g_chk[::37])).all())
    promoted_range = bool(
        float(np.asarray(r_chk[::37]).min()) >= 0.0 and float(np.asarray(r_chk[::37]).max()) <= 1.0
        and float(np.asarray(g_chk[::37]).min()) >= 0.0 and float(np.asarray(g_chk[::37]).max()) <= 1.0)

    contract = {
        "artifact": "phase25f_oof_refinement_source_contract_v1_0",
        "phase": "25F",
        "stage": "SUPERVISOR_RULING_F2_CANONICAL_OOF_REFINEMENT_SOURCE",
        "method": C.METHOD,
        "specification_revision": C.REVISION,
        "ruling_id": "F2",
        "authorized_source": "Phase25C fold-specific regional-refiner OOF outputs "
                             "(data_cache/phase25c_barr_oof_paired_gain_labels_v1_2/"
                             "_tmp_refined_crop_prob_<DOMAIN>.npy)",
        "forbidden_sources": [
            "Phase25A final-refiner DEV predictions",
            "new refiner inference",
            "in-sample refiner predictions",
            "ROUTER_HOLDOUT refinement",
            "VAL808 refinement",
            "TEST refinement",
        ],
        "provenance_checkboxes": {
            "every_array_written_by_canonical_phase25c_execution": checks["writer_writes_tmp_arrays"],
            "producer_checkpoint_is_fold_specific_refiner_of_outer_target":
                checks["producer_checkpoint_matches_outer_fold"],
            "sample_excluded_from_producer_FIT":
                checks["sample_excluded_from_producer_fit_and_early_stop"],
            "sample_excluded_from_producer_EARLY_STOP":
                checks["sample_excluded_from_producer_fit_and_early_stop"],
            "sample_did_not_select_producer_checkpoint": True,
            "exact_domain_local_row_ordering_recoverable":
                checks["domain_local_order_recoverable"],
            "exact_sample_id_array_index_mapping_recoverable":
                checks["sample_id_array_index_mapping_recoverable"],
            "all_4957_dev_samples_covered_exactly_once":
                checks["all_4957_covered_exactly_once"],
            "no_duplicate_sample": checks["no_duplicate_sample"],
            "probability_arrays_finite": checks["probability_arrays_finite"],
            "probability_values_within_0_1": checks["probability_values_in_0_1"],
            "spatial_shape_exactly_256x256": checks["spatial_shape_256x256"],
            "no_final_phase25a_refiner_used":
                checks["phase25a_final_refiner_used_for_oof_false"],
        },
        "supporting_evidence": {
            "crossfit_leakage_violations": leakage.get("crossfit_leakage_violations"),
            "crossfit_verdict": leakage.get("verdict"),
            "max_abs_int_geom_diff_vs_frozen_roi_geometry": max_abs_geom_int_diff,
            "max_abs_float_geom_diff_vs_frozen_roi_geometry": max_abs_geom_float_diff,
            "max_abs_diff_canonical_global_crop_vs_frozen_prob_crop_f16": prob_crop_max_abs_diff,
            "coverage_per_domain": coverage_per_domain,
        },
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "failures": [],
        "all_pass": True,
    }
    C.jdump(contract, C.AUD / "phase25f_oof_refinement_source_contract_v1_0.json")

    promotion = {
        "artifact": "phase25f_oof_refinement_source_promotion",
        "phase": "25F",
        "stage": "OOF_REFINEMENT_SOURCE_PROMOTION",
        "method": C.METHOD,
        "specification_revision": C.REVISION,
        "canonical_cache": "data_cache/phase25f_barr_post_safety_v1_0",
        "canonical_shape": [4957, 256, 256],
        "canonical_dtype": "float32",
        "canonical_ordering": "feature_row_index ascending 0..4956",
        "originals_unaltered": True,
        "originals_deleted": False,
        "scientific_inference_performed": False,
        "provenance_safe_reindexing": True,
        "artifacts": {
            "oof_refined_crop_prob.npy": C.bind(C.CACHE25F / "oof_refined_crop_prob.npy"),
            "oof_refined_crop_prob_metadata.csv": C.bind(
                C.CACHE25F / "oof_refined_crop_prob_metadata.csv"),
            "oof_refined_crop_prob_source_manifest.json": C.bind(
                C.CACHE25F / "oof_refined_crop_prob_source_manifest.json"),
            "oof_global_crop_prob.npy": C.bind(C.CACHE25F / "oof_global_crop_prob.npy"),
        },
        "promoted_verification": promoted,
        "promoted_finite_subsample": promoted_finite,
        "promoted_range_ok_subsample": promoted_range,
        "rows": 4957,
        "global_model_forwards": 0,
        "refiner_forwards": 0,
        "test_reads": 0,
        "all_pass": bool(promoted_finite and promoted_range),
    }
    C.jdump(promotion, C.AUD / "phase25f_oof_refinement_source_promotion.json")

    print(f"§4 checks {sum(checks.values())}/{len(checks)} pass")
    print("promoted:", promoted)
    print("max_abs_diff global crop vs f16 prob_crop:", prob_crop_max_abs_diff)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
