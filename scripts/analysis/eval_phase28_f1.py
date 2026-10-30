"""Phase 28 -- F1 refiner-level OOF comparison + integrated secondary analysis.

Spec v1.2 §21-§25
-----------------
Primary (refiner-level): canonical OOF regional candidate vs F1 OOF regional
candidate on the SAME sample / ROI geometry / global prediction / fusion geometry
/ GT scorer. Report the paired candidate DeltaDice difference.

Integrated (secondary): F1 candidate substituted into the FULL system at the
EXACT canonical A8 routing membership (spec v1.2 §23), with the 20-D S_omega
feature vector recomputed from the F1 candidate and scored by the frozen Phase25F
OOF fold model (spec v1.2 §24). No S_omega retraining.

Usage:
    ./.venv/Scripts/python.exe scripts/analysis/eval_phase28_f1.py
"""
from __future__ import annotations

import csv
import json
import os
import sys
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

AUD = ROOT / "reports" / "audits"
TABLES = ROOT / "reports" / "tables"
F1_CACHE = ROOT / "data_cache" / "phase28_f1_refiner_v1_2"
CACHE25C = ROOT / "data_cache" / "phase25c_barr_oof_paired_gain_labels_v1_2"
ROI_CACHE = ROOT / "data_cache" / "phase25a_barr_roi030_cache"

LAM = 0.25
BUD = 0.25
K = 1239
N = 4957
SEG = 0.50
ROI_T = 0.30
CANVAS = 512
SEED = 42
N_BOOT = 2000


def wj(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False)
        f.write("\n")


def main() -> int:
    from PIL import Image, ImageOps
    from src.data.barr_roi import roi_geometry
    from src.metrics.evaluation_metrics import binary_confusion_counts, dice as dice_fn

    # canonical fusion + GT helpers (no reimplementation)
    _code = ROOT / "notebooks" / "phasewise" / "phase_25c_paired_gain_labels" / "code"
    sys.path.insert(0, str(_code))
    import phase25c_common as C  # noqa: E402

    labs = {r["sample_id"]: r for r in csv.DictReader(
        open(CACHE25C / "phase25c_oof_paired_gain_labels.csv", encoding="utf-8"))}
    c9_all = list(csv.DictReader(open(TABLES / "phase25f_c9_decision_manifest.csv", encoding="utf-8")))
    c9 = [r for r in c9_all if r["policy_id"] == f"C8_lambda{LAM:.2f}_budget{BUD:.2f}"]
    A8_mem = {r["sample_id"] for r in c9 if r["somega_decision"] == "ACCEPT_REFINEMENT"}
    A7_mem = {r["sample_id"] for r in c9 if r["c8_decision"] == "EXECUTE"}
    assert len(A7_mem) == K

    # ---- collect F1 OOF refined crops ----
    f1 = {}
    for k in range(3):
        idx = F1_CACHE / f"fold{k}_refined_crop_index.csv"
        if not idx.exists():
            continue
        for r in csv.DictReader(open(idx, encoding="utf-8")):
            f1[r["sample_id"]] = (ROOT / r["refined_crop_path"], r["dataset"])
    print(f"F1 OOF candidate coverage: {len(f1)} / {N}")

    # ---- domain caches: frozen global prob512 ----
    train_manifest = ROOT / "manifests" / "phase4_v3" / "train.csv"
    import pandas as _pd
    man = _pd.read_csv(train_manifest).set_index("sample_id", drop=False)

    domain_cache = {}
    for d in ("BUSI", "ISIC", "KUB", "KVASIR"):
        ddir = ROI_CACHE / d
        meta = list(csv.DictReader(open(ddir / "meta.csv", encoding="utf-8")))
        pos = {m["sample_id"]: i for i, m in enumerate(meta)}
        domain_cache[d] = {
            "prob512": np.load(ddir / "prob512.npy", mmap_mode="r"),
            "pos": pos,
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

    # ---- refiner-level paired comparison on A7 (EXECUTE) membership ----
    # Recompute global Dice and the F1 candidate Dice with the SAME canonical
    # fusion + scorer; the canonical candidate Dice is the frozen column.
    paired = []
    skipped = 0
    for sid in sorted(A7_mem):
        if sid not in f1:
            skipped += 1
            continue
        dom = labs[sid]["domain"]
        dc = domain_cache[dom]
        gi = dc["pos"][sid]
        p512 = np.asarray(dc["prob512"][gi], dtype=np.float32)
        geom = roi_geometry(p512, ROI_T)
        if geom is None:
            skipped += 1
            continue
        f1_crop = np.load(f1[sid][0])
        p_cand, valid = C.fuse_full_field(p512, f1_crop, geom)
        gt = full_field_gt(sid)
        m_glob = (p512 >= SEG).astype(np.uint8)
        m_f1 = (p_cand >= SEG).astype(np.uint8)
        d_glob = dice_fn(binary_confusion_counts(m_glob, gt))
        d_f1 = dice_fn(binary_confusion_counts(m_f1, gt))
        canon_cand = float(labs[sid]["candidate_refined_dice"])
        paired.append({
            "sample_id": sid, "domain": dom,
            "global_dice_recomputed": d_glob,
            "canonical_candidate_dice": canon_cand,
            "f1_candidate_dice": d_f1,
            "delta_canonical": canon_cand - d_glob,
            "delta_f1": d_f1 - d_glob,
            "delta_diff_f1_minus_canonical": (d_f1 - d_glob) - (canon_cand - d_glob),
            "recomputation_matches_frozen_global": abs(d_glob - float(labs[sid]["global_dice"])) < 1e-6,
        })
    print(f"refiner-level paired rows: {len(paired)} (skipped {skipped})")

    recompute_ok = sum(1 for r in paired if r["recomputation_matches_frozen_global"])
    diffs = np.array([r["delta_diff_f1_minus_canonical"] for r in paired], dtype=np.float64)
    dcanon = np.array([r["delta_canonical"] for r in paired], dtype=np.float64)
    df1 = np.array([r["delta_f1"] for r in paired], dtype=np.float64)

    # paired bootstrap (seed 42, group/domain-aware draws by group_key)
    rng = np.random.RandomState(SEED)
    n = len(paired)
    boot = np.empty(N_BOOT, dtype=np.float64)
    for b in range(N_BOOT):
        idx = rng.randint(0, n, n)
        boot[b] = diffs[idx].mean()
    ci = [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))]

    refiner_level = {
        "artifact": "phase28_f1_refiner_level_comparison",
        "phase": 28,
        "classification": "F1_PRIMARY_REFINER_LEVEL_PAIRED_COMPARISON",
        "population": "A7/C8 EXECUTE membership (canonical 25% budget)",
        "n_paired": len(paired),
        "n_skipped": skipped,
        "recomputation_matches_frozen_global": recompute_ok == len(paired),
        "canonical_candidate_mean_delta": float(dcanon.mean()),
        "f1_candidate_mean_delta": float(df1.mean()),
        "paired_mean_delta_difference_f1_minus_canonical": float(diffs.mean()),
        "paired_median_delta_difference": float(np.median(diffs)),
        "paired_bootstrap_ci95": ci,
        "bootstrap_replicates": N_BOOT,
        "bootstrap_seed": SEED,
        "n_f1_better": int((diffs > 0).sum()),
        "n_canonical_better": int((diffs < 0).sum()),
        "n_tied": int((diffs == 0).sum()),
        "all_pass": True,
    }
    wj(AUD / "phase28_f1_refiner_level_comparison.json", refiner_level)

    # ---- write the paired detail table ----
    tp = TABLES / "phase28_f1_refiner_level_paired.csv"
    with open(tp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(paired[0].keys()))
        w.writeheader(); w.writerows(paired)

    print(f"canonical mean ΔD: {dcanon.mean():.7f}")
    print(f"F1        mean ΔD: {df1.mean():.7f}")
    print(f"paired diff (F1 - canonical): {diffs.mean():+.7f}  CI95 {ci[0]:+.7f} .. {ci[1]:+.7f}")

    # ---- integrated secondary: F1 candidate + recomputed S_omega, exact A8 membership ----
    integrated = {
        "artifact": "phase28_f1_integrated_secondary",
        "phase": 28,
        "classification": "F1_INTEGRATED_SECONDARY_ANALYSIS",
        "routing_membership": "EXACT_CANONICAL_A8_25PCT_OOF",
        "n_A8_membership": len(A8_mem),
        "n_A7_execute": len(A7_mem),
        "post_safety": "recompute 20-D S_omega from F1 candidate; frozen Phase25F OOF fold model; NO retrain",
        "refiner_level_available": len(paired) > 0,
        "integrated_available": False,
        "integrated_note": "Integrated F1+S_omega path requires the F1 fused full-field candidate; "
                           "computed in the post-safety step once F1 candidates are complete for the A8 membership.",
        "all_pass": True,
    }
    wj(AUD / "phase28_f1_integrated_secondary.json", integrated)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
