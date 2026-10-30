"""Phase-20 cross-domain TRAIN<->VAL duplicate / near-duplicate audit.

Resolves the single residual issue Phase 19 explicitly left open:

    "Cross-domain near-duplicate detection across the newly combined four-domain
     development pool is not yet established."

Method
------
* EXACT content identity  : sha256 of the raw image file bytes.
* PERCEPTUAL near-duplicate: the ALREADY-APPROVED repository method, reused
  verbatim from ``scripts/audit/run_phash_fast.py``:
      32x32 grayscale (BOX resample) -> 2-D DCT (ortho, both axes)
      -> top-left 8x8 low-frequency block -> median threshold -> 64-bit hash
  Candidate threshold: Hamming distance <= 6 (the frozen diagnostic threshold).

Scope
-----
TRAIN and VAL image content ONLY. ``manifests/phase4_v3/{train,val}.csv`` is
read directly; ``manifests/all_paired.csv`` is deliberately NOT used because it
contains TEST rows. Zero TEST images are opened.

Frozen blocking rule (declared BEFORE the audit is interpreted)
--------------------------------------------------------------
BLOCK Phase-20 training if ANY TRAIN<->VAL pair satisfies either:
  (a) identical content sha256, or
  (b) pHash Hamming distance == 0  (perceptually identical).
REPORT (non-blocking) all pairs with 1 <= Hamming <= 6, flagging cross-dataset
pairs at Hamming <= 2 as HIGH_ATTENTION. Within-TRAIN and within-VAL duplicates
are reported descriptively; splits are NOT modified.

Writes
------
reports/audits/phase20_cross_domain_duplicate_audit.json
reports/tables/phase20_cross_domain_duplicate_candidates.csv
reports/audits/phase20_phash_cache.npz  (TRAIN+VAL only)
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image
from scipy.fftpack import dct

ROOT = Path(__file__).resolve().parent.parent.parent
AUDIT_DIR = ROOT / "reports/audits"
TABLE_DIR = ROOT / "reports/tables"
MANIFEST_DIR = ROOT / "manifests/phase4_v3"

CACHE = AUDIT_DIR / "phase20_phash_cache.npz"
HASH_CACHE = AUDIT_DIR / "phase20_content_sha_cache.json"
HASH_CACHE_VERSION = "phase20_trainval_content_sha_v1"

HAMMING_CANDIDATE = 6      # frozen diagnostic threshold (legacy convention)
HAMMING_HIGH_ATTENTION = 2  # cross-dataset pairs at/below this need attention
DATASET_ORDER = ["ISIC", "BUSI", "KVASIR", "KUB"]


def sha256_file(path: str, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            block = fh.read(chunk)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def phash64(path: str) -> np.ndarray:
    """Approved repository 64-bit DCT perceptual hash (verbatim method)."""
    try:
        with Image.open(path) as img:
            img = img.convert("L").resize((32, 32), Image.Resampling.BOX)
            pixels = np.asarray(img, dtype=np.float32)
            low = dct(dct(pixels, axis=0, norm="ortho"), axis=1, norm="ortho")[:8, :8]
            return (low > np.median(low)).flatten()
    except Exception:
        return np.zeros(64, dtype=bool)


def classify(dist: int, same_path: bool) -> str:
    if dist == 0:
        return "EXACT_DUPLICATE" if same_path else "PERCEPTUALLY_IDENTICAL"
    if dist <= 2:
        return "LIKELY_NEAR_DUPLICATE"
    if dist <= 4:
        return "POSSIBLE_NEAR_DUPLICATE"
    return "SIMILAR_BUT_DISTINCT"


def hamming_matrix(packed_a: np.ndarray, packed_b: np.ndarray) -> np.ndarray:
    """Pairwise Hamming distance between two uint64 hash vectors."""
    xor = packed_a[:, None] ^ packed_b[None, :]
    return np.bitwise_count(xor).astype(np.int16)


def main() -> int:
    t_start = time.time()
    tr = pd.read_csv(MANIFEST_DIR / "train.csv")
    va = pd.read_csv(MANIFEST_DIR / "val.csv")
    df = pd.concat([tr, va], ignore_index=True)
    df["split"] = df["split"].astype(str).str.upper()
    assert set(df["split"]) <= {"TRAIN", "VAL"}, "TEST rows must never enter this audit"
    print(f"TRAIN={len(tr)} VAL={len(va)} total={len(df)} (TEST excluded by construction)")

    # ---- content sha256 (cached) ----------------------------------------
    if HASH_CACHE.exists():
        cache = json.loads(HASH_CACHE.read_text(encoding="utf-8"))
        if cache.get("version") == HASH_CACHE_VERSION:
            content_sha = cache["sha"]
            print(f"loaded content-sha cache ({len(content_sha)} entries)")
        else:
            cache = None
    else:
        cache = None
    if cache is None:
        t0 = time.time()
        content_sha = {}
        for i, p in enumerate(df["image_path"]):
            content_sha[p] = sha256_file(p)
            if (i + 1) % 1000 == 0:
                print(f"  sha256 {i+1}/{len(df)}  ({time.time()-t0:.0f}s)")
        HASH_CACHE.write_text(json.dumps({"version": HASH_CACHE_VERSION, "sha": content_sha},
                                         indent=1), encoding="utf-8")
        print(f"content sha256 computed in {time.time()-t0:.1f}s")

    # ---- pHash (cached) --------------------------------------------------
    if CACHE.exists():
        hashes = np.load(CACHE)["hashes"]
        assert hashes.shape == (len(df), 64), "phash cache shape mismatch"
        print("loaded pHash cache")
    else:
        t0 = time.time()
        hashes = np.array([phash64(p) for p in df["image_path"]], dtype=bool)
        np.savez_compressed(CACHE, hashes=hashes)
        print(f"pHash computed in {time.time()-t0:.1f}s")

    packed = np.packbits(hashes, axis=1).view(np.uint64).flatten()
    tr_idx = np.flatnonzero(df["split"].values == "TRAIN")
    va_idx = np.flatnonzero(df["split"].values == "VAL")

    # ---- TRAIN <-> VAL pairwise -----------------------------------------
    t0 = time.time()
    dist = hamming_matrix(packed[tr_idx], packed[va_idx])
    print(f"TRAIN x VAL Hamming matrix {dist.shape} in {time.time()-t0:.1f}s")

    # exact-identity pre-check (fast, independent of pHash)
    sha_tr = np.array([content_sha[p] for p in df["image_path"].values[tr_idx]])
    sha_va = np.array([content_sha[p] for p in df["image_path"].values[va_idx]])
    exact_same = sha_tr[:, None] == sha_va[None, :]
    n_exact_same = int(exact_same.sum())

    ds_tr = df["dataset"].values[tr_idx]
    ds_va = df["dataset"].values[va_idx]
    pid_tr = df["patient_id"].values[tr_idx]
    pid_va = df["patient_id"].values[va_idx]
    sid_tr = df["sample_id"].values[tr_idx]
    sid_va = df["sample_id"].values[va_idx]
    path_tr = df["image_path"].values[tr_idx]
    path_va = df["image_path"].values[va_idx]

    # candidate mask = hamming<=6 OR exact content identity
    cand = (dist <= HAMMING_CANDIDATE) | exact_same
    ai, bi = np.nonzero(cand)
    print(f"TRAIN<->VAL candidate pairs (hamming<={HAMMING_CANDIDATE} or exact sha): {len(ai)}")

    records = []
    for a, b in zip(ai, bi):
        d = int(dist[a, b])
        same_sha = bool(exact_same[a, b])
        records.append({
            "sample_id_train": sid_tr[a],
            "sample_id_val": sid_va[b],
            "dataset_train": ds_tr[a],
            "dataset_val": ds_va[b],
            "pair_kind": "WITHIN_DATASET" if ds_tr[a] == ds_va[b] else "CROSS_DATASET",
            "patient_id_train": pid_tr[a],
            "patient_id_val": pid_va[b],
            "same_patient_id": bool(str(pid_tr[a]) == str(pid_va[b])),
            "hamming_distance": d,
            "exact_content_sha_match": same_sha,
            "phash_train": "".join(hashes[tr_idx[a]].astype(int).astype(str)),
            "phash_val": "".join(hashes[va_idx[b]].astype(int).astype(str)),
            "image_path_train": path_tr[a],
            "image_path_val": path_va[b],
            "classification": classify(d, bool(path_tr[a] == path_va[b])),
            "high_attention": bool(d <= HAMMING_HIGH_ATTENTION
                                   and ds_tr[a] != ds_va[b]),
        })
    cand_df = pd.DataFrame(records)
    if len(cand_df):
        cand_df = cand_df.sort_values(["hamming_distance", "dataset_train", "dataset_val"],
                                      kind="mergesort").reset_index(drop=True)
    cand_df.to_csv(TABLE_DIR / "phase20_cross_domain_duplicate_candidates.csv", index=False)

    # ---- blocking determination -----------------------------------------
    blocking_pairs = cand_df[(cand_df["hamming_distance"] == 0)
                             | (cand_df["exact_content_sha_match"])] if len(cand_df) else pd.DataFrame()
    n_blocking = int(len(blocking_pairs))

    # ---- stratified reporting -------------------------------------------
    pairs = {}
    for da in DATASET_ORDER:
        for db in DATASET_ORDER:
            if da > db:
                continue
            if da == db:
                m = (ds_tr == da)[:, None] & (ds_va == db)[None, :]
            else:
                m = ((ds_tr == da)[:, None] & (ds_va == db)[None, :]) | \
                    ((ds_tr == db)[:, None] & (ds_va == da)[None, :])
            dd = dist[m]
            pairs[f"{da}<->{db}"] = {
                "kind": "WITHIN_DATASET" if da == db else "CROSS_DATASET",
                "n_pairs_compared": int(m.sum()),
                "n_hamming_0": int((dd == 0).sum()),
                "n_hamming_1_2": int(((dd >= 1) & (dd <= 2)).sum()),
                "n_hamming_3_4": int(((dd >= 3) & (dd <= 4)).sum()),
                "n_hamming_5_6": int(((dd >= 5) & (dd <= 6)).sum()),
                "min_hamming": int(dd.min()) if dd.size else None,
            }

    # within-TRAIN and within-VAL descriptive
    def within(split_idx, name):
        p = packed[split_idx]
        d = hamming_matrix(p, p)
        iu = np.triu_indices(d.shape[0], k=1)
        dd = d[iu]
        return {
            "split": name,
            "n_images": int(len(split_idx)),
            "n_pairs_compared": int(dd.size),
            "n_hamming_0": int((dd == 0).sum()),
            "n_hamming_1_2": int(((dd >= 1) & (dd <= 2)).sum()),
            "n_hamming_3_4": int(((dd >= 3) & (dd <= 4)).sum()),
            "n_hamming_5_6": int(((dd >= 5) & (dd <= 6)).sum()),
        }

    payload = {
        "artifact": "phase20_cross_domain_duplicate_audit",
        "phase": "20",
        "resolves_phase19_residual_issue": True,
        "phase19_residual_statement": (
            "Cross-domain near-duplicate detection across the newly combined "
            "four-domain development pool is not yet established."),
        "scope": "TRAIN and VAL image content only",
        "test_reads": {"test_image_reads": 0, "test_mask_reads": 0},
        "method": {
            "exact": "sha256 of raw image file bytes",
            "perceptual": {
                "implementation_source": "scripts/audit/run_phash_fast.py (approved repository method)",
                "algorithm": "32x32 L (BOX) -> 2-D DCT ortho -> top-left 8x8 -> median threshold -> 64-bit",
                "candidate_threshold_hamming": HAMMING_CANDIDATE,
                "high_attention_threshold_hamming": HAMMING_HIGH_ATTENTION,
                "classification_bands": {
                    "0_same_path": "EXACT_DUPLICATE",
                    "0_diff_path": "PERCEPTUALLY_IDENTICAL",
                    "1_2": "LIKELY_NEAR_DUPLICATE",
                    "3_4": "POSSIBLE_NEAR_DUPLICATE",
                    "5_6": "SIMILAR_BUT_DISTINCT",
                },
            },
        },
        "blocking_rule_declared_before_interpretation": {
            "block_if": ["identical content sha256 across TRAIN<->VAL",
                         "pHash Hamming distance == 0 across TRAIN<->VAL"],
            "report_only": "1 <= Hamming <= 6",
            "splits_modified": False,
            "manifest_modified": False,
        },
        "populations": {"TRAIN": int(len(tr)), "VAL": int(len(va)), "compared_pairs": int(len(tr) * len(va))},
        "train_val_pairwise": pairs,
        "within_split": [within(tr_idx, "TRAIN"), within(va_idx, "VAL")],
        "n_candidate_pairs": int(len(cand_df)),
        "n_exact_content_sha_matches_train_val": n_exact_same,
        "n_blocking_pairs": n_blocking,
        "blocking_pair_examples": (blocking_pairs.head(20).to_dict("records")
                                   if n_blocking else []),
        "candidates_high_attention": int(cand_df["high_attention"].sum()) if len(cand_df) else 0,
        "cross_dataset_candidate_counts": {
            k: v["n_hamming_0"] + v["n_hamming_1_2"] + v["n_hamming_3_4"] + v["n_hamming_5_6"]
            for k, v in pairs.items() if v["kind"] == "CROSS_DATASET"},
        "verdict": "PHASE20_DUPLICATE_AUDIT_PASS__NO_TRAIN_VAL_LEAKAGE" if n_blocking == 0
                   else "PHASE20_DUPLICATE_AUDIT_FAIL__TRAIN_VAL_LEAKAGE_DETECTED",
        "training_may_start": n_blocking == 0,
        "fail_closed": True,
        "candidates_table": "reports/tables/phase20_cross_domain_duplicate_candidates.csv",
        "elapsed_seconds": round(time.time() - t_start, 1),
    }
    (AUDIT_DIR / "phase20_cross_domain_duplicate_audit.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8")

    print()
    print("=== CROSS-DATASET TRAIN<->VAL (Hamming bands) ===")
    for k, v in pairs.items():
        print(f"  {k:<16} {v['kind']:<15} pairs={v['n_pairs_compared']:>8} "
              f"d0={v['n_hamming_0']:>4} d1-2={v['n_hamming_1_2']:>4} "
              f"d3-4={v['n_hamming_3_4']:>4} d5-6={v['n_hamming_5_6']:>4} min={v['min_hamming']}")
    print()
    print("blocking pairs:", n_blocking, "| exact sha matches:", n_exact_same,
          "| candidates:", len(cand_df))
    print("VERDICT:", payload["verdict"])
    print("training_may_start:", payload["training_may_start"])
    return 0 if n_blocking == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
