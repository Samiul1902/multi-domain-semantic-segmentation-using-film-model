"""Phase 28 -- F1 INTEGRATED SECONDARY post-safety analysis (spec v1.2 §24).

For the EXACT canonical A8 (25% budget) routing membership:
  1. build the F1 fused FULL-FIELD candidate from the F1 OOF refined crop;
  2. recompute ONLY the deterministic 20-D GT-free S_omega feature vector
     (frozen `phase25f_post_safety_features.build_input_vector`);
  3. normalize indices 0..15 with the FROZEN per-fold
     `phase25f_cv_fold{k}_normalization_stats.csv` (FIT-only, ddof=0);
  4. score with the FROZEN Phase25F OOF fold model
     `checkpoints/phase25f_barr_post_safety_v1_0_seed42/cv_fold{k}/best.pt`
     (the fold k of the sample's `router_cv_fold`), no retraining;
  5. apply the frozen ACCEPT_REFINEMENT / FALLBACK_GLOBAL decision at
     SOMEGA_ACCEPT_LOGIT_THRESHOLD = 0.0;
  6. compute the integrated system DeltaDice.

Outputs
-------
reports/audits/phase28_f1_integrated_secondary.json
reports/tables/phase28_f1_integrated_per_sample.csv
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))

import numpy as np  # noqa: E402

AUD = ROOT / "reports" / "audits"
TABLES = ROOT / "reports" / "tables"
F1_CACHE = ROOT / "data_cache" / "phase28_f1_refiner_v1_2"
CACHE25C = ROOT / "data_cache" / "phase25c_barr_oof_paired_gain_labels_v1_2"
CACHE25F = ROOT / "data_cache" / "phase25f_barr_post_safety_v1_0"
ROI_CACHE = ROOT / "data_cache" / "phase25a_barr_roi030_cache"
F_CKPT = ROOT / "checkpoints" / "phase25f_barr_post_safety_v1_0_seed42"

LAM = 0.25
BUD = 0.25
K = 1239
N = 4957
SEG = 0.50
ROI_T = 0.30
CANVAS = 512
SEED = 42
N_BOOT = 2000
ACCEPT_LOGIT_THRESHOLD = 0.0


def wj(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False)
        f.write("\n")


def main() -> int:
    from PIL import Image, ImageOps
    import torch

    from src.data.barr_roi import roi_geometry
    from src.metrics.evaluation_metrics import binary_confusion_counts, dice as dice_fn

    _code = ROOT / "notebooks" / "phasewise" / "phase_25c_paired_gain_labels" / "code"
    sys.path.insert(0, str(_code))
    import phase25c_common as C  # noqa: E402

    import phase25f_execution_common as E  # noqa: E402
    import phase25f_post_safety_features as F  # noqa: E402

    DEV = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # ---- frozen A7/A8 memberships --------------------------------------- #
    c9_all = list(csv.DictReader(
        open(TABLES / "phase25f_c9_decision_manifest.csv", encoding="utf-8")))
    c9 = [r for r in c9_all if r["policy_id"] == f"C8_lambda{LAM:.2f}_budget{BUD:.2f}"]
    A8_mem = {r["sample_id"] for r in c9 if r["somega_decision"] == "ACCEPT_REFINEMENT"}
    A7_mem = {r["sample_id"] for r in c9 if r["c8_decision"] == "EXECUTE"}
    assert len(A7_mem) == K, f"A7 membership {len(A7_mem)} != {K}"
    print(f"A7 EXECUTE membership: {len(A7_mem)} | A8 ACCEPT: {len(A8_mem)}")

    # ---- F1 OOF candidate paths ------------------------------------------ #
    f1_path = {}
    for k in range(3):
        idx = F1_CACHE / f"fold{k}_refined_crop_index.csv"
        for r in csv.DictReader(open(idx, encoding="utf-8")):
            f1_path[r["sample_id"]] = ROOT / r["refined_crop_path"]
    print(f"F1 OOF candidate coverage: {len(f1_path)} / {N}")

    # ---- per-sample metadata: router_cv_fold / task_id / domain ---------- #
    # The A8 membership uses the Phase25C OOF outer fold, which is exactly the
    # sample's `router_cv_fold` in the frozen Phase25D CV5 manifest.
    cv_rows = list(csv.DictReader(
        open(TABLES / "phase25d_cv5_manifest.csv", encoding="utf-8")))
    sid_fold = {r["sample_id"]: int(r["router_cv_fold"]) for r in cv_rows}
    sid_domtask = {r["sample_id"]: (r["dataset"], int(r["task_id"]))
                   for r in cv_rows}

    # ---- Phase25B scalar geometry (indices 200/201) ---------------------- #
    import phase25f_spec_repair_common as SC  # noqa: E402
    b25 = {}
    b25f = np.load(SC.PHASE25B_FEATURES, mmap_mode="r")
    for r in csv.DictReader(open(SC.PHASE25B_METADATA, encoding="utf-8")):
        b25[r["sample_id"]] = int(r["feature_row_index"])

    # ---- frozen per-fold normalization stats ----------------------------- #
    norm_stats = {}
    for k in range(5):
        rows = list(csv.DictReader(open(
            TABLES / f"phase25f_cv_fold{k}_normalization_stats.csv", encoding="utf-8")))
        mu = np.array([float(r["mu"]) for r in rows], dtype=np.float64)
        sigma = np.array([float(r["sigma"]) for r in rows], dtype=np.float64)
        const = np.array([r["is_constant"] == "True" for r in rows], dtype=bool)
        norm_stats[k] = (mu, sigma, const)

    # ---- frozen Phase25F OOF fold models --------------------------------- #
    fold_models = {}
    for k in range(5):
        ck = F_CKPT / f"cv_fold{k}" / "best.pt"
        fold_models[k] = E.load_best_model(ck, DEV)
    print("loaded 5 frozen Phase25F OOF fold models")

    # ---- frozen global probability 256 crops (P_g) ----------------------- #
    # Phase25F P_g == `oof_global_crop_prob.npy` (canonical global probability
    # crop, 256x256). Row order is the Phase25F feature_row_index order.
    pg_all = np.load(CACHE25F / "oof_global_crop_prob.npy", mmap_mode="r")
    meta25f = list(csv.DictReader(
        open(CACHE25F / "oof_refined_crop_prob_metadata.csv", encoding="utf-8")))
    sid_pg_row = {r["sample_id"]: int(r["feature_row_index"]) for r in meta25f}
    assert pg_all.shape[0] == N, pg_all.shape
    print(f"frozen global prob crop cache: {pg_all.shape} {pg_all.dtype}")

    # ---- global prob512 + GT caches -------------------------------------- #
    import pandas as _pd
    man = _pd.read_csv(ROOT / "manifests" / "phase4_v3" / "train.csv").set_index("sample_id", drop=False)

    domain_cache = {}
    for d in ("BUSI", "ISIC", "KUB", "KVASIR"):
        ddir = ROI_CACHE / d
        meta = list(csv.DictReader(open(ddir / "meta.csv", encoding="utf-8")))
        domain_cache[d] = {
            "prob512": np.load(ddir / "prob512.npy", mmap_mode="r"),
            "pos": {m["sample_id"]: i for i, m in enumerate(meta)},
        }

    def full_field_gt(sample_id: str) -> np.ndarray:
        img = Image.open(str(man.loc[sample_id, "mask_path"])).convert("L")
        w, h = img.size
        scale = min(CANVAS / w, CANVAS / h)
        rw, rh = max(1, round(w * scale)), max(1, round(h * scale))
        img = img.resize((rw, rh), Image.Resampling.NEAREST)
        left, top = (CANVAS - rw) // 2, (CANVAS - rh) // 2
        img = ImageOps.expand(img, (left, top, CANVAS - rw - left, CANVAS - rh - top))
        return (np.asarray(img) > 0).astype(np.uint8)

    # ---- stream the A7 membership (pairs of 256-crop -> full field) ------- #
    rows_out = []
    skipped = 0
    for sid in sorted(A7_mem):
        if sid not in f1_path:
            skipped += 1
            continue
        m = None
        dom, task_id = sid_domtask[sid]
        k = sid_fold[sid]
        dc = domain_cache[dom]
        p512 = np.asarray(dc["prob512"][dc["pos"][sid]], dtype=np.float32)
        geom = roi_geometry(p512, ROI_T)
        if geom is None:
            skipped += 1
            continue

        # F1 fused full-field candidate
        f1_crop = np.load(f1_path[sid]).astype(np.float32)
        if f1_crop.ndim == 3:
            f1_crop = f1_crop[0]
        p_f1_full, valid = C.fuse_full_field(p512, f1_crop, geom)

        # frozen P_g: canonical global probability crop (256x256)
        p_g_crop = np.asarray(pg_all[sid_pg_row[sid]], dtype=np.float32)
        if p_g_crop.ndim == 3:
            p_g_crop = p_g_crop[0]

        j = b25[sid]
        roi_area_fraction = float(b25f[j, SC.PHASE25B_IDX_ROI_AREA_FRACTION])
        roi_side = float(b25f[j, SC.PHASE25B_IDX_ROI_SIDE])
        vec_raw = F.build_input_vector(p_g_crop, f1_crop, roi_area_fraction, roi_side, task_id)

        mu, sigma, const = norm_stats[k]
        vec = vec_raw.astype(np.float32).copy()
        sigma_safe = np.where(sigma < 1e-12, 1.0, sigma)
        norm = (vec_raw[:16].astype(np.float64) - mu) / sigma_safe
        norm[const] = 0.0
        vec[:16] = norm.astype(np.float32)

        model = fold_models[k]
        logit = float(E.predict_logits(model, vec[None, :], DEV)[0])
        dec = "ACCEPT_REFINEMENT" if logit >= ACCEPT_LOGIT_THRESHOLD else "FALLBACK_GLOBAL"

        # integrated DeltaDice under the frozen state machine
        gt = full_field_gt(sid)
        m_glob = (p512 >= SEG).astype(np.uint8)
        m_f1 = (p_f1_full >= SEG).astype(np.uint8)
        d_glob = dice_fn(binary_confusion_counts(m_glob, gt))
        d_f1 = dice_fn(binary_confusion_counts(m_f1, gt))
        delta = (d_f1 - d_glob) if dec == "ACCEPT_REFINEMENT" else 0.0

        rows_out.append({
            "sample_id": sid, "domain": dom, "task_id": task_id, "router_cv_fold": k,
            "somega_logit": repr(logit), "somega_decision": dec,
            "global_dice": repr(float(d_glob)),
            "f1_candidate_dice": repr(float(d_f1)),
            "delta_dice_integrated": repr(float(delta)),
        })

    print(f"integrated rows: {len(rows_out)} (skipped {skipped})")

    tp = TABLES / "phase28_f1_integrated_per_sample.csv"
    with open(tp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()))
        w.writeheader()
        w.writerows(rows_out)

    delta = np.array([float(r["delta_dice_integrated"]) for r in rows_out], dtype=np.float64)
    n_acc = sum(1 for r in rows_out if r["somega_decision"] == "ACCEPT_REFINEMENT")
    n_fb = len(rows_out) - n_acc
    mean_delta = float(delta.mean())

    # paired bootstrap on the integrated delta vs the canonical A8 delta
    # Canonical A8 per-sample delta = true DeltaDice on ACCEPT else 0.
    dd_by_sid = {r["sample_id"]: float(r["delta_dice"]) for r in csv.DictReader(
        open(CACHE25F / "targets.csv", encoding="utf-8"))}
    c9_by_sid = {r["sample_id"]: r for r in c9}
    canon_int = np.array([
        dd_by_sid[r["sample_id"]]
        if c9_by_sid[r["sample_id"]].get("somega_decision") == "ACCEPT_REFINEMENT" else 0.0
        for r in rows_out], dtype=np.float64)
    f1_int = np.array([float(r["delta_dice_integrated"]) for r in rows_out], dtype=np.float64)
    diff_f1_canon = f1_int - canon_int
    rng = np.random.RandomState(SEED)
    n = len(rows_out)
    boot = np.empty(N_BOOT, dtype=np.float64)
    for b in range(N_BOOT):
        idx = rng.randint(0, n, n)
        boot[b] = diff_f1_canon[idx].mean()
    ci = [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))]

    out = {
        "artifact": "phase28_f1_integrated_secondary",
        "phase": 28,
        "classification": "F1_INTEGRATED_SECONDARY_ANALYSIS",
        "routing_membership": "EXACT_CANONICAL_A8_25PCT_OOF",
        "post_safety": "recompute 20-D S_omega from F1 candidate; FROZEN Phase25F OOF fold "
                       "model per router_cv_fold; NO retrain",
        "n_A8_membership": len(A8_mem),
        "n_A7_execute": len(A7_mem),
        "n_integrated_rows": len(rows_out),
        "n_skipped": skipped,
        "n_f1_accept": n_acc,
        "n_f1_fallback": n_fb,
        "f1_integrated_mean_delta_dice": mean_delta,
        "f1_integrated_sum_delta_dice": float(delta.sum()),
        "canonical_A8_mean_delta_dice": 0.007515754298,
        "paired_mean_difference_f1_minus_canonical": float(diff_f1_canon.mean()),
        "paired_bootstrap_ci95": ci,
        "bootstrap_replicates": N_BOOT,
        "bootstrap_seed": SEED,
        "accept_logit_threshold": ACCEPT_LOGIT_THRESHOLD,
        "segmentation_threshold": SEG,
        "roi_proposal_threshold": ROI_T,
        "frozen_model_checkpoint": "checkpoints/phase25f_barr_post_safety_v1_0_seed42/cv_fold{k}/best.pt",
        "s_omega_retrained": False,
        "all_pass": len(rows_out) == K,
    }
    wj(AUD / "phase28_f1_integrated_secondary.json", out)

    print(f"F1 integrated mean ΔD: {mean_delta:+.7f} (accept {n_acc} / fallback {n_fb})")
    print(f"paired diff vs canonical A8: {diff_f1_canon.mean():+.7f}  CI95 {ci[0]:+.7f} .. {ci[1]:+.7f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
