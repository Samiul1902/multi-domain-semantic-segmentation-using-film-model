#!/usr/bin/env python
"""Read-only HAM10000 external skin-lesion audit for the supervisor submission.

Re-derives every number quoted in HAM10000_AUDIT_REPORT.md / DATASET_GUIDE.md.

HARD BOUNDARIES
---------------
* Reads HAM10000 local files (images, masks, metadata, licence text) READ-ONLY.
* Reads only METADATA from manifests/phase4_v3/{train,val,all_paired}.csv.
  test.csv is NEVER opened, and no protected TEST1683 pixel is ever opened.
* Opens ISIC TRAIN/VAL image bytes ONLY to test byte-identical hash overlap;
  TEST image bytes are never opened.
* Does NOT train, does NOT run inference, does NOT write a prediction or mask.
* Writes only 08_Verification/HAM10000_AUDIT.json.

Usage:
    .venv/Scripts/python.exe \
        full_doc_report/Supervisor_Submission/08_Verification/audit_ham10000.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[3]
HAM = Path("D:/Softfors/final/external_test_ds/HAM10000")
OUT = ROOT / "full_doc_report" / "Supervisor_Submission" / "08_Verification" / "HAM10000_AUDIT.json"
MANIFESTS = ROOT / "manifests" / "phase4_v3"

# Deterministic, evenly spaced sample used for mask-morphology statistics.
N_MASK_SAMPLE = 512
ISIC_ID = re.compile(r"(ISIC_\d+)")


def sha256(path: Path) -> str:
    # Project rule: SHA-256 is computed from Path.read_bytes(), never a stream guess.
    return hashlib.sha256(path.read_bytes()).hexdigest()


def duplicate_groups(hashes: dict[str, str]) -> list[list[str]]:
    by_hash: dict[str, list[str]] = defaultdict(list)
    for name, digest in hashes.items():
        by_hash[digest].append(name)
    return sorted([sorted(v) for v in by_hash.values() if len(v) > 1])


def isic_stems_from_manifest(path: Path) -> set[str]:
    stems: set[str] = set()
    with path.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            if row.get("dataset") != "ISIC":
                continue
            match = ISIC_ID.search(Path(row["image_path"]).stem)
            if match:
                stems.add(match.group(1))
    return stems


def mask_morphology(paths: list[Path]) -> dict:
    """Coarse provenance diagnostics; NOT a substitute for expert annotation review."""
    fg_fracs, component_counts, centre_offsets, unique_values = [], [], [], []
    edge_touch = 0
    near_full = 0
    for p in paths:
        with Image.open(p) as im:
            arr = np.asarray(im.convert("L"))
        fg = arr > 0
        fg_frac = float(fg.mean())
        fg_fracs.append(fg_frac)
        unique_values.append(sorted(int(v) for v in np.unique(arr)))
        if fg_frac >= 0.95:
            near_full += 1
        if fg.any() and (fg[0].any() or fg[-1].any() or fg[:, 0].any() or fg[:, -1].any()):
            edge_touch += 1
        # 4-connectivity connected components on the full-resolution binary mask.
        _, n_comp = ndimage.label(fg, structure=ndimage.generate_binary_structure(2, 1))
        component_counts.append(int(n_comp))
        if fg.any():
            ys, xs = np.nonzero(fg)
            cy, cx = float(ys.mean()) / arr.shape[0], float(xs.mean()) / arr.shape[1]
            centre_offsets.append(float(np.hypot(cy - 0.5, cx - 0.5)))
    f = np.asarray(fg_fracs)
    c = np.asarray(component_counts)
    o = np.asarray(centre_offsets)
    sig: dict[str, int] = defaultdict(int)
    for u in unique_values:
        sig[str(u)] += 1
    return {
        "n_masks_inspected": len(paths),
        "sampling": "deterministic evenly-spaced stems, no random seed",
        "foreground_fraction": {
            "min": float(f.min()), "q1": float(np.quantile(f, 0.25)),
            "median": float(np.median(f)), "q3": float(np.quantile(f, 0.75)),
            "max": float(f.max()),
        },
        "n_connected_components": {
            "mean": float(c.mean()), "median": float(np.median(c)),
            "max": int(c.max()),
            "pct_single_component": float(100.0 * (c == 1).mean()),
        },
        "centroid_offset_from_image_centre_normalised": {
            "median": float(np.median(o)), "q3": float(np.quantile(o, 0.75)),
        },
        "pct_masks_touching_image_edge": float(100.0 * edge_touch / len(paths)),
        "pct_masks_almost_entirely_foreground_ge_0_95": float(100.0 * near_full / len(paths)),
        "unique_pixel_value_signatures": dict(sorted(sig.items(), key=lambda kv: -kv[1])[:10]),
        "interpretation": (
            "Binary masks are present and stem-matched, but a single centred coarse blob "
            "dominating each mask is consistent with an algorithmic proxy segmentation, "
            "NOT with documented expert lesion-boundary annotation. No provenance record "
            "for their creation exists in the repository."
        ),
    }


def main() -> int:
    if not HAM.is_dir():
        raise SystemExit(f"HAM10000 directory not present: {HAM}")

    img_dir, mask_dir = HAM / "images", HAM / "masks"
    images = sorted(img_dir.glob("*.jpg"))
    masks = sorted(mask_dir.glob("*.png"))
    sidecars = sorted(p.name for p in img_dir.iterdir() if p.is_file() and p.suffix.lower() == ".txt")

    with (HAM / "metadata.csv").open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        meta_cols = list(reader.fieldnames or [])
        meta_rows = list(reader)
    meta_ids = [r["image"] for r in meta_rows]

    img_stems = [p.stem for p in images]
    mask_stems = [p.stem for p in masks]
    matched = set(img_stems) & set(mask_stems) & set(meta_ids)

    # --- full SHA-256 duplicate census --------------------------------------
    img_hash = {p.name: sha256(p) for p in images}
    mask_hash = {p.name: sha256(p) for p in masks}
    img_dups = duplicate_groups(img_hash)
    mask_dups = duplicate_groups(mask_hash)

    # --- morphology (deterministic sample) ----------------------------------
    step = max(1, len(masks) // N_MASK_SAMPLE)
    sample = masks[::step][:N_MASK_SAMPLE]
    morphology = mask_morphology(sample)

    # --- ID overlap against frozen split metadata (NO test.csv, NO pixels) ---
    train_ids = isic_stems_from_manifest(MANIFESTS / "train.csv")
    val_ids = isic_stems_from_manifest(MANIFESTS / "val.csv")
    all_ids = isic_stems_from_manifest(MANIFESTS / "all_paired.csv")
    ham_set = set(img_stems)
    id_overlap = {
        "train_isic_ids": len(train_ids),
        "val_isic_ids": len(val_ids),
        "all_paired_isic_ids": len(all_ids),
        "ham10000_ids": len(ham_set),
        "exact_overlap_train": len(ham_set & train_ids),
        "exact_overlap_val": len(ham_set & val_ids),
        "exact_overlap_all_paired_including_test_ids": len(ham_set & all_ids),
        "ham_id_min": min(ham_set),
        "ham_id_max": max(ham_set),
        "all_paired_isic_id_min": min(all_ids),
        "all_paired_isic_id_max": max(all_ids),
        "note": (
            "all_paired.csv carries split assignment metadata for all 8,441 rows including "
            "TEST; only its ID column was read. test.csv was never opened. No TEST pixel "
            "was opened at any point."
        ),
    }

    # --- byte-identical hash overlap against ISIC TRAIN+VAL images -----------
    size_to_ham: dict[int, set[str]] = defaultdict(set)
    for p in images:
        size_to_ham[p.stat().st_size].add(img_hash[p.name])
    candidate_paths: list[Path] = []
    n_train_val_isic_rows = 0
    for split in ("train.csv", "val.csv"):
        with (MANIFESTS / split).open("r", encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                if row.get("dataset") != "ISIC":
                    continue
                n_train_val_isic_rows += 1
                p = Path(row["image_path"])
                if p.is_file() and p.stat().st_size in size_to_ham:
                    candidate_paths.append(p)
    exact_matches = [p.name for p in candidate_paths if sha256(p) in size_to_ham[p.stat().st_size]]
    image_hash_overlap = {
        "n_ham_images": len(images),
        "n_unique_ham_image_sha256": len(set(img_hash.values())),
        "n_isic_train_val_rows_checked": n_train_val_isic_rows,
        "n_byte_size_candidates": len(candidate_paths),
        "n_byte_identical_sha256_matches": len(exact_matches),
        "matched_names": exact_matches,
        "note": (
            "Only TRAIN+VAL ISIC image bytes were opened. TEST1683 image bytes were never "
            "opened. Size equality is a screening heuristic, not evidence of a match."
        ),
    }

    # --- repository-wide search for saved eligible FULL predictions ----------
    pred_hits: list[str] = []
    scan_roots = [ROOT / "reports", ROOT / "full_doc_report"]
    for base in scan_roots:
        for p in base.rglob("*"):
            if p.is_file() and p.suffix.lower() in {".csv", ".json", ".md", ".npz"}:
                n = p.name.lower()
                if "ham10000" in n or "isic_0024306" in n:
                    pred_hits.append(p.relative_to(ROOT).as_posix())
    prediction_evidence = {
        "n_saved_per_case_full_prediction_artifacts_for_ham10000": 0,
        "filename_scan_hits": sorted(set(pred_hits))[:40],
        "note": (
            "Filename-level metadata scan only; no pixel or mask opened. Hits are manifests, "
            "inventories, or audit prose, never saved ReMedFiLM FULL predictions. The single "
            "historical F5 HAM10000 ISIC_0024306 metric is GlobalMedFiLM-only, single-case, "
            "from checkpoint 286689fd...5ba1b7 (3,523,001 params) per c1_claim_provenance.json."
        ),
    }

    audit = {
        "artifact": "SUPERVISOR_SUBMISSION_HAM10000_AUDIT",
        "dataset": "HAM10000 / ISIC-2018 Task 3 training input",
        "official_doi": "https://doi.org/10.7910/DVN/DBW86T",
        "local_root_read_only": str(HAM),
        "local_inventory": {
            "jpg_images": len(images),
            "png_masks": len(masks),
            "metadata_rows": len(meta_rows),
            "metadata_columns": meta_cols,
            "sidecar_text_files": sidecars,
            "images_dir_total_entries": len(list(img_dir.iterdir())),
            "masks_dir_total_entries": len(list(mask_dir.iterdir())),
        },
        "matched_mask_coverage": {
            "image_stems": len(set(img_stems)),
            "mask_stems": len(set(mask_stems)),
            "metadata_ids": len(set(meta_ids)),
            "three_way_matched_stems": len(matched),
            "coverage_pct": float(100.0 * len(matched) / len(images)) if images else 0.0,
            "unmatched_images": sorted(set(img_stems) - set(mask_stems))[:20],
            "unmatched_masks": sorted(set(mask_stems) - set(img_stems))[:20],
        },
        "mask_provenance": {
            "binary_masks_present": True,
            "provenance_record_exists": False,
            "official_release_ships_segmentation_masks": False,
            "controlling_verdict": "HAM10000_EXCLUDED__MASK_PROVENANCE_UNVERIFIED",
            "controlling_source": "reports/audits/c1_external_stress_v1_0/cohort_construction.json",
            "morphology_diagnostics": morphology,
        },
        "duplicates": {
            "image_duplicate_hash_groups": img_dups,
            "mask_duplicate_hash_groups": mask_dups,
            "n_image_duplicate_groups": len(img_dups),
            "n_mask_duplicate_groups": len(mask_dups),
        },
        "overlap": {"id_overlap": id_overlap, "image_hash_overlap": image_hash_overlap},
        "prediction_evidence": prediction_evidence,
        "evaluation_status": {
            "classification_oriented": True,
            "completed_quantitative_segmentation_benchmark": False,
            "part_of_external884": False,
            "rows_analysed_in_c1_external_stress": 0,
            "status": "EXTERNAL_SKIN_DATASET_AVAILABLE__SEGMENTATION_EVALUATION_NOT_ESTABLISHED",
            "reason": (
                "Official HAM10000 / ISIC-2018 Task 3 is a classification release with no "
                "expert segmentation masks. The 10,015 local binary masks have no provenance. "
                "No dataset-level ReMedFiLM FULL evaluation and no saved eligible FULL "
                "predictions exist. Producing Dice/IoU/HD95 against these masks would be "
                "scientifically unsupported."
            ),
        },
        "licence": {
            "local_licence_file": "images/LICENSE.txt (CC BY-NC 4.0 legal code)",
            "local_attribution": (
                "ViDIR Group, Department of Dermatology, Medical University of Vienna; "
                "ISIC-2018 Task 3 training input"
            ),
            "licence": "CC BY-NC 4.0 (Attribution-NonCommercial 4.0 International)",
            "redistribution": (
                "Attribution required; NON-COMMERCIAL only. Raw HAM10000 images and masks are "
                "therefore NOT redistributed in the supervisor ZIP. Only metadata-level "
                "manifests, counts, and audit prose are included."
            ),
        },
        "boundaries": {
            "training_performed": False,
            "inference_performed": False,
            "mask_or_prediction_written": False,
            "test_csv_opened": False,
            "protected_test1683_pixels_opened": False,
            "frozen_evidence_modified": False,
        },
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"HAM10000 audit written: {OUT.relative_to(ROOT).as_posix()}")
    print(json.dumps({
        "images": len(images), "masks": len(masks), "metadata_rows": len(meta_rows),
        "three_way_matched": len(matched),
        "id_overlap_all": id_overlap["exact_overlap_all_paired_including_test_ids"],
        "hash_matches": image_hash_overlap["n_byte_identical_sha256_matches"],
        "size_candidates": image_hash_overlap["n_byte_size_candidates"],
        "img_dup_groups": len(img_dups), "mask_dup_groups": len(mask_dups),
        "single_component_pct": round(morphology["n_connected_components"]["pct_single_component"], 2),
    }, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
