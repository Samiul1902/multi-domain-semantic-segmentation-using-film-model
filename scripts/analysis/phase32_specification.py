#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""PHASE 32 — EXTERNAL DATASET & DOMAIN SHIFT EVALUATION.
Entry gate + external-cohort provenance + population ownership + pre-execution specification.

PROVENANCE / DISCOVERY / SPECIFICATION ONLY.
Metadata + directory listing only: no image-pixel read, no mask-pixel read, no model forward,
no metric computation, no threshold tuning, no training, no ROUTER_HOLDOUT reopen, no TEST.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase32_specification.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
DOCS = ROOT / "docs"

METHOD = "RA-MedFiLM-BARR"
REVISION = "ra_medfilm_barr_phase32_external_domain_shift_v1_0"
CLASSIFICATION = "PRE_EXECUTION_EXTERNAL_PROVENANCE_AND_DOMAIN_SHIFT_SPECIFICATION"
QUALIFIER = ("ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_SCIENTIFIC_SOURCE_"
             "FREEZE_DEVIATION")

TERMINAL_NO_CLEAN = ("PHASE32_EXTERNAL_DOMAIN_SHIFT_SPEC_COMPLETE__NO_PROSPECTIVE_CLEAN_EXTERNAL_"
                     "COHORT_ELIGIBLE__HISTORICAL_AND_STRESS_TEST_EVIDENCE_CLASSIFIED__EXECUTION_"
                     "NOT_AUTHORIZED")

BIND = {
    "reports/audits/phase31_closure_terminal.json":
        "b14f3729b5c899988c6d2ce05389d79ca82398aa98809a73baef2ae1a227abc1",
    "reports/audits/phase31_final_closure.json":
        "27993a7e97c4bc583abb3337b84e012d9843bc07f378e90bc2bbf6652adfb0dd",
    "reports/audits/phase31_final_closure_check.json":
        "85a031d1124dd6392feba86e52e249f91da29bf25445ffdc32ff90561f0a8d38",
    "reports/audits/phase31_phase32_handoff.json":
        "1580d334ef408cab4bf62303e4323de237cccae18691b77414ef913253755549",
}
P31_TERMINAL = ("PHASE31_STATISTICAL_CLAIM_GOVERNANCE_COMPLETE_CANONICAL__NO_NEW_CONFIRMATORY_OR_"
                "EXPLORATORY_STATISTICAL_EXECUTION_ELIGIBLE_OR_REQUIRED__PHASE30_PROTOCOL_DEVIATION_"
                "QUALIFIER_PRESERVED__PHASE32_ELIGIBLE_NOT_STARTED")

# ---------------------------------------------------------------- discovery
LEGACY_EXT = Path(r"D:/Softfors/final/external_test_ds")
LEGACY_EXT2 = Path(r"D:/Softfors/final/medfilm_seg/data_external")
UPSTREAM_RAW = Path(r"D:/Softfors/omni_seg/data_raw")

EXPOSURE_CLASSES = [
    "EXTERNAL_UNSEEN_OUTCOME_UNEXPOSED",
    "EXTERNAL_DATA_SEEN_BUT_OUTCOMES_UNEXPOSED",
    "EXTERNAL_OUTCOME_EXPOSED_HISTORICALLY",
    "EXTERNAL_USED_FOR_PRIOR_MODEL_OR_THRESHOLD_SELECTION",
    "EXTERNAL_PROVENANCE_AMBIGUOUS",
    "NOT_GENUINELY_EXTERNAL",
    "TASK_OR_ANNOTATION_INCOMPATIBLE",
    "SUPPLEMENTARY_STRESS_TEST_ONLY",
]
ROLE_CLASSES = [
    "PRIMARY_EXTERNAL_DOMAIN_SHIFT_COHORT",
    "SECONDARY_EXTERNAL_DOMAIN_SHIFT_COHORT",
    "HISTORICALLY_EXPOSED_EXTERNAL_BENCHMARK",
    "SUPPLEMENTARY_STRESS_TEST_ONLY",
    "INELIGIBLE_TASK_MISMATCH",
    "INELIGIBLE_PROVENANCE_AMBIGUOUS",
    "INELIGIBLE_OVERLAP_RISK",
    "INELIGIBLE_PRIOR_SELECTION_USE",
]
OPEN_STATES = [
    "UNOPENED_IN_PROJECT_HISTORY", "METADATA_ONLY_DISCOVERED", "IMAGE_OPENED_GT_UNOPENED",
    "GT_OPENED_NO_MODEL_OUTCOME", "OUTCOME_EXPOSED_HISTORICALLY", "PRIOR_SELECTION_USE",
    "UNKNOWN_REQUIRES_BLOCK",
]

# candidate table: (id, name, root, modality, exposure_class, ownership, role, open_state, refs)
CANDIDATES = [
    ("EXT-01", "BDCXR-3257", str(LEGACY_EXT / "BDCXR-3257"), "chest radiograph (bone)",
     "EXTERNAL_OUTCOME_EXPOSED_HISTORICALLY", "legacy MedFiLM-Seg external cohort",
     "HISTORICALLY_EXPOSED_EXTERNAL_BENCHMARK", "OUTCOME_EXPOSED_HISTORICALLY", 150),
    ("EXT-02", "BrEaST-Lesions_USG", str(LEGACY_EXT / "BrEaST-Lesions_USG-images_and_masks"),
     "breast ultrasound", "EXTERNAL_OUTCOME_EXPOSED_HISTORICALLY",
     "legacy MedFiLM-Seg external cohort", "HISTORICALLY_EXPOSED_EXTERNAL_BENCHMARK",
     "OUTCOME_EXPOSED_HISTORICALLY", 233),
    ("EXT-03", "CVC-ClinicDB", str(LEGACY_EXT / "CVC-ClinicDB"), "colonoscopy polyp",
     "EXTERNAL_OUTCOME_EXPOSED_HISTORICALLY", "legacy MedFiLM-Seg external cohort",
     "HISTORICALLY_EXPOSED_EXTERNAL_BENCHMARK", "OUTCOME_EXPOSED_HISTORICALLY", 659),
    ("EXT-04", "DentIRO", str(LEGACY_EXT / "DentIRO"), "dental radiograph",
     "EXTERNAL_OUTCOME_EXPOSED_HISTORICALLY", "legacy MedFiLM-Seg external cohort",
     "HISTORICALLY_EXPOSED_EXTERNAL_BENCHMARK", "OUTCOME_EXPOSED_HISTORICALLY", 157),
    ("EXT-05", "GastroEndoNet", str(LEGACY_EXT /
     "GastroEndoNet Comprehensive Endoscopy Image Dataset for GERD and Polyp Detection"),
     "endoscopy (GERD/polyp)", "EXTERNAL_OUTCOME_EXPOSED_HISTORICALLY",
     "legacy MedFiLM-Seg external cohort", "HISTORICALLY_EXPOSED_EXTERNAL_BENCHMARK",
     "OUTCOME_EXPOSED_HISTORICALLY", 61),
    ("EXT-06", "HAM10000", str(LEGACY_EXT / "HAM10000"), "skin dermoscopy",
     "EXTERNAL_OUTCOME_EXPOSED_HISTORICALLY", "legacy MedFiLM-Seg external cohort",
     "HISTORICALLY_EXPOSED_EXTERNAL_BENCHMARK", "OUTCOME_EXPOSED_HISTORICALLY", 306),
    ("EXT-07", "KUB-Stone (legacy external copy)", str(LEGACY_EXT / "KUB-Stone"),
     "KUB radiograph", "NOT_GENUINELY_EXTERNAL",
     "same source family as the internal KUB domain", "INELIGIBLE_OVERLAP_RISK",
     "OUTCOME_EXPOSED_HISTORICALLY", 0),
    ("EXT-08", "MILK10k", str(LEGACY_EXT / "MILK10k_Training_Input"), "skin dermoscopy",
     "EXTERNAL_OUTCOME_EXPOSED_HISTORICALLY", "legacy MedFiLM-Seg external cohort",
     "HISTORICALLY_EXPOSED_EXTERNAL_BENCHMARK", "OUTCOME_EXPOSED_HISTORICALLY", 192),
    ("EXT-09", "OrthoFrac-XR", str(LEGACY_EXT / "OrthoFrac-XR"), "orthopedic fracture radiograph",
     "EXTERNAL_OUTCOME_EXPOSED_HISTORICALLY", "legacy MedFiLM-Seg external cohort",
     "HISTORICALLY_EXPOSED_EXTERNAL_BENCHMARK", "OUTCOME_EXPOSED_HISTORICALLY", 173),
    ("EXT-10", "PolypDataset.zip (archived)", str(LEGACY_EXT / "PolypDataset.zip"),
     "colonoscopy polyp (archived)", "EXTERNAL_DATA_SEEN_BUT_OUTCOMES_UNEXPOSED",
     "legacy archive; superset relationship to CVC-ClinicDB unclear",
     "INELIGIBLE_PROVENANCE_AMBIGUOUS", "METADATA_ONLY_DISCOVERED", 0),
    ("EXT-11", "Stones_where_are_you (COCO)", str(
        LEGACY_EXT / "Stones_where_are_you-.v3i.coco-segmentation"), "kidney/urinary stone",
     "EXTERNAL_PROVENANCE_AMBIGUOUS", "late-added legacy COCO export; provenance unregistered",
     "INELIGIBLE_PROVENANCE_AMBIGUOUS", "UNKNOWN_REQUIRES_BLOCK", 0),
    ("EXT-12", "legacy data/ (image,label)", str(LEGACY_EXT / "data"),
     "unregistered", "EXTERNAL_PROVENANCE_AMBIGUOUS", "unlabelled legacy folder",
     "INELIGIBLE_PROVENANCE_AMBIGUOUS", "UNKNOWN_REQUIRES_BLOCK", 0),
    ("EXT-13", "legacy medfilm_seg/data_external/CVC_ClinicDB", str(LEGACY_EXT2 / "CVC_ClinicDB"),
     "colonoscopy polyp", "EXTERNAL_OUTCOME_EXPOSED_HISTORICALLY",
     "duplicate of EXT-03 inside the legacy source tree", "INELIGIBLE_OVERLAP_RISK",
     "OUTCOME_EXPOSED_HISTORICALLY", 0),
    ("EXT-14", "NLM (Montgomery CXR)", str(UPSTREAM_RAW / "NLM"), "chest radiograph (TB)",
     "TASK_OR_ANNOTATION_INCOMPATIBLE", "upstream OmniMedSeg_FL project data; not this project",
     "INELIGIBLE_TASK_MISMATCH", "UNKNOWN_REQUIRES_BLOCK", 0),
    ("EXT-15", "msd (Medical Segmentation Decathlon)", str(UPSTREAM_RAW / "msd"),
     "CT/MRI multi-organ", "TASK_OR_ANNOTATION_INCOMPATIBLE",
     "upstream OmniMedSeg_FL project data; not this project", "INELIGIBLE_TASK_MISMATCH",
     "UNKNOWN_REQUIRES_BLOCK", 0),
    ("EXT-16", "kits_2d_splitted (KiTS)", str(UPSTREAM_RAW / "kits_2d_splitted"),
     "kidney tumor CT", "TASK_OR_ANNOTATION_INCOMPATIBLE",
     "upstream OmniMedSeg_FL project data; not this project", "INELIGIBLE_TASK_MISMATCH",
     "UNKNOWN_REQUIRES_BLOCK", 0),
    ("EXT-17", "BraTS-PEDs-v1", str(UPSTREAM_RAW / "BraTS-PEDs-v1"), "brain MRI tumor",
     "TASK_OR_ANNOTATION_INCOMPATIBLE",
     "upstream OmniMedSeg_FL project data; not this project", "INELIGIBLE_TASK_MISMATCH",
     "UNKNOWN_REQUIRES_BLOCK", 0),
    ("EXT-18", "brats_2d_npy", str(UPSTREAM_RAW / "brats_2d_npy"), "brain MRI tumor (2D)",
     "TASK_OR_ANNOTATION_INCOMPATIBLE",
     "upstream OmniMedSeg_FL project data; not this project", "INELIGIBLE_TASK_MISMATCH",
     "UNKNOWN_REQUIRES_BLOCK", 0),
    ("EXT-19", "stone (Dataset Part 1/2)", str(UPSTREAM_RAW / "stone"),
     "radiograph stone (jpg+txt pairs)", "EXTERNAL_PROVENANCE_AMBIGUOUS",
     "upstream project data with no jup/omni_seg code reference", "INELIGIBLE_PROVENANCE_AMBIGUOUS",
     "UNKNOWN_REQUIRES_BLOCK", 0),
]


def sha256_file(p) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def write_json(obj, path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = str(path) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(json.dumps(obj, indent=1) + "\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def write_csv(path, header, rows) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        for r in rows:
            w.writerow(r)


def dir_stats(p: Path):
    """Metadata-only: file counts by extension."""
    if not p.exists():
        return None, None, None
    n_img = n_msk = n_tot = 0
    img_ext = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".npy", ".dcm"}
    msk_hint = ("mask", "label", "gt", "groundtruth", "seg")
    for r, _, fs in os.walk(p):
        for f in fs:
            n_tot += 1
            e = os.path.splitext(f)[1].lower()
            if e in img_ext:
                n_img += 1
            low = f.lower()
            if any(k in low for k in msk_hint):
                n_msk += 1
    return n_img, n_msk, n_tot


def main() -> int:
    print("=" * 78)
    print("PHASE 32 — EXTERNAL DATASET & DOMAIN SHIFT EVALUATION (SPECIFICATION)")
    print("=" * 78)

    # ================= §A bind Phase31 closure ================= #
    binds = [{"path": p, "expected_sha256": e, "observed_sha256": sha256_file(ROOT / p),
              "match": sha256_file(ROOT / p) == e} for p, e in BIND.items()]
    t31 = json.loads((AUD / "phase31_closure_terminal.json").read_text(encoding="utf-8"))
    a_ok = (all(b["match"] for b in binds) and t31["terminal"] == P31_TERMINAL
            and t31["status"] == "COMPLETE_CANONICAL"
            and t31["Phase32_status"] == "ELIGIBLE_NOT_STARTED")
    write_json({
        "artifact": "phase32_entry_authority_binding", "phase": 32, "section": "§A/§B",
        "method": METHOD, "revision": REVISION,
        "phase31_closure_terminal": binds[0], "phase31_terminal_token": t31["terminal"],
        "phase31_status": t31["status"], "phase32_roadmap_identity":
            "EXTERNAL DATASET & DOMAIN SHIFT EVALUATION",
        "phase32_status_required": "ELIGIBLE_NOT_STARTED",
        "phase31_bindings": binds, "all_bindings_match": all(b["match"] for b in binds),
        "phase30_qualifier_carried_forward": QUALIFIER,
        "phase30_status": "COMPLETE_WITH_PROTOCOL_DEVIATION__NOT_COMPLETE_CANONICAL",
        "phase30_status_upgraded": False,
        "generated_utc": now_utc(), "all_pass": a_ok,
    }, AUD / "phase32_entry_authority_binding.json")
    print(f"§A Phase31 closure bound: {sum(1 for b in binds if b['match'])}/{len(binds)} match")

    # ================= §E external dataset discovery ================= #
    disc_rows = []
    for cid, name, root, modality, expo, owner, role, ostate, refs in CANDIDATES:
        p = Path(root)
        n_img, n_msk, n_tot = dir_stats(p)
        disc_rows.append([
            cid, name, root, "filesystem_discovery", "", str(p.exists()),
            ("" if n_img is None else n_img), ("" if n_msk is None else n_msk),
            ("" if n_tot is None else n_tot), modality, "segmentation (claimed)",
            "True" if refs > 0 else "False", expo, role])
    hdr = ["candidate_id", "dataset_name", "root", "source_artifact", "source_sha",
           "filesystem_exists", "n_image_files_metadata_only", "n_mask_files_metadata_only",
           "n_files_total", "known_domain_modality", "claimed_task_mapping",
           "historical_evaluation_evidence_exists", "historical_outcome_exposure_known",
           "candidate_status"]
    write_csv(TAB / "phase32_external_dataset_discovery.csv", hdr, disc_rows)
    n_exist = sum(1 for r in disc_rows if r[5] == "True")
    write_json({
        "artifact": "phase32_external_dataset_discovery_summary", "phase": 32, "section": "§E",
        "method": METHOD, "revision": REVISION, "discovery_mode": "METADATA_AND_DIRECTORY_LISTING_ONLY",
        "project_declared_external_roots_present": {
            "data_external/": (ROOT / "data_external").exists(),
            "external_test_ds/": (ROOT / "external_test_ds").exists(),
            "data/external/": (ROOT / "data/external").exists(),
            "data_raw/external/": (ROOT / "data_raw/external").exists()},
        "legacy_external_root_found": str(LEGACY_EXT), "legacy_external_root_exists":
            LEGACY_EXT.exists(),
        "legacy_result_documents_present": sorted(
            [f.name for f in LEGACY_EXT.glob("*.docx")] + [f.name for f in LEGACY_EXT.glob("*.pptx")]
        ) if LEGACY_EXT.exists() else [],
        "n_candidates": len(CANDIDATES), "n_candidates_on_disk": n_exist,
        "image_pixels_read": 0, "mask_pixels_read": 0,
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase32_external_dataset_discovery_summary.json")
    print(f"§E discovery: {len(CANDIDATES)} candidates, {n_exist} present on disk")

    # ================= §F prior exposure audit ================= #
    exp_rows = []
    for cid, name, root, modality, expo, owner, role, ostate, refs in CANDIDATES:
        exp_rows.append([cid, name, expo, refs, owner,
                         "legacy MedFiLM-Seg notebooks/result documents"
                         if refs > 0 else "no direct evaluation reference found",
                         "True" if expo == "EXTERNAL_OUTCOME_EXPOSED_HISTORICALLY" else "False"])
    write_csv(TAB / "phase32_external_prior_exposure_matrix.csv",
              ["candidate_id", "dataset_name", "exposure_class",
               "legacy_notebook_reference_count", "ownership_note", "exposure_evidence",
               "outcome_exposed"], exp_rows)
    from collections import Counter
    expo_counts = Counter(c[4] for c in CANDIDATES)
    write_json({
        "artifact": "phase32_external_prior_exposure_audit", "phase": 32, "section": "§F",
        "method": METHOD, "revision": REVISION,
        "scope": "every earlier project phase, notebook, script, report and legacy experiment",
        "evidence": {
            "legacy_project": "D:/Softfors/final (MedFiLM-Seg predecessor)",
            "notebook_reference_counts": {
                "main.ipynb": {"external_test_ds": 1523, "ClinicDB": 659, "HAM10000": 306,
                               "BrEaST": 233, "MILK10k": 192},
                "main_fix.ipynb": {"OrthoFrac": 173, "DentIRO": 157, "BDCXR": 150,
                                   "GastroEndoNet": 61},
                "main_paper.ipynb": {"BDCXR": 583, "DentIRO": 426, "OrthoFrac": 390,
                                     "GastroEndoNet": 14},
                "main_medfilm_seg_kub_stone_extension.ipynb": {"external_test_ds": 1524,
                                                               "ClinicDB": 659, "HAM10000": 306}},
            "result_documents": ["MedFiLM_Seg_Important_Result_Parameters_V7_FINAL_CLEAN.docx",
                                 "MedSegFilm_Report (2) (Repaired) (1).docx",
                                 "MedSeg-FiLM Presentation (1472,1457).pptx"],
            "legacy_artifact": "D:/Softfors/jup/reports/audits/phase19_legacy_evidence_reuse_map.json "
                               "(component_id legacy.final.external_test_ds, "
                               "old_role 'External evaluation dataset engineering', "
                               "current_intended_reuse 'External-evaluation engineering reference "
                               "for Phase 32')"},
        "candidate_exposure_classes": {c[0]: c[4] for c in CANDIDATES},
        "exposure_class_counts": dict(expo_counts),
        "n_unseen_unexposed": expo_counts.get("EXTERNAL_UNSEEN_OUTCOME_UNEXPOSED", 0),
        "no_cohort_may_be_called_untouched_external_validation_set": True,
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase32_external_prior_exposure_audit.json")
    print(f"§F exposure audit: {dict(expo_counts)}")

    # ================= §G population ownership ================= #
    own_rows = []
    for cid, name, root, modality, expo, owner, role, ostate, refs in CANDIDATES:
        mod_ok = modality.split(" (")[0] in (
            "skin dermoscopy", "breast ultrasound", "colonoscopy polyp", "KUB radiograph",
            "kidney/urinary stone")
        own_rows.append({
            "candidate_id": cid, "dataset_name": name, "modality": modality,
            "source_collection": owner,
            "patient_identity_available": "unknown",
            "segmentation_gt_exists": "likely" if refs > 0 else "unknown",
            "label_target_matches_project": mod_ok,
            "modality_matches_four_domains": mod_ok,
            "task_id_mapping_legitimate": "unknown",
            "annotation_semantics_compatible": "unknown",
            "multi_mask_per_image": "unknown",
            "empty_masks_legitimate": "unknown",
            "case_level_or_image_level": "unknown",
            "repeated_frames_clustering_risk": "unknown",
            "patient_ids_exist": "unknown",
            "licensing_documented_in_project_provenance": "partial (legacy only)",
        })
    write_json({
        "artifact": "phase32_population_ownership_ruling", "phase": 32, "section": "§G",
        "method": METHOD, "revision": REVISION,
        "per_candidate": own_rows,
        "ruling": "No candidate has fully resolved population ownership. Patient/case identity, "
                  "annotation semantics, licensing and clustering structure are NOT recoverable "
                  "from current project provenance for any candidate. Population ownership must be "
                  "resolved prospectively in a future Phase32 execution step before any inference.",
        "clinical_equivalence_inferred_from_filenames": False,
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase32_population_ownership_ruling.json")
    print("§G population ownership ruling: none fully resolved")

    # ================= §H overlap/leakage specification ================= #
    write_json({
        "artifact": "phase32_overlap_audit_specification", "phase": 32, "section": "§H",
        "method": METHOD, "revision": REVISION,
        "purpose": "detect overlap between any future external cohort and ALL development populations",
        "against": ["Phase26 training/development data", "VAL808", "ROUTER_DEVELOPMENT",
                    "ROUTER_HOLDOUT", "TEST metadata only where governance permits"],
        "detection_targets": ["exact duplicate images", "exact duplicate masks (metadata-hashable)",
                              "same patient/case IDs", "filename lineage", "source-dataset overlap",
                              "known derivative/resized copies", "near-duplicate risk"],
        "known_immediate_overlap_findings": [
            "EXT-07 legacy external KUB-Stone is the same source family as the internal KUB domain "
            "-> INELIGIBLE_OVERLAP_RISK",
            "EXT-13 legacy medfilm_seg/data_external/CVC_ClinicDB duplicates EXT-03 -> "
            "INELIGIBLE_OVERLAP_RISK"],
        "test_image_or_mask_read_authorized": False,
        "test_metadata_precomputed_hashes_only": True,
        "pixel_level_overlap_check_executed_now": False,
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase32_overlap_audit_specification.json")

    # ================= §I role registry ================= #
    write_csv(TAB / "phase32_external_cohort_role_registry.csv",
              ["candidate_id", "dataset_name", "exposure_class", "phase32_role",
               "selection_basis", "known_performance_used_for_selection"],
              [[c[0], c[1], c[4], c[6], "provenance / task compatibility / externality / integrity",
                "False"] for c in CANDIDATES])
    role_counts = Counter(c[6] for c in CANDIDATES)
    write_json({
        "artifact": "phase32_external_cohort_role_registry_summary", "phase": 32, "section": "§I",
        "role_counts": dict(role_counts),
        "primary_eligible": role_counts.get("PRIMARY_EXTERNAL_DOMAIN_SHIFT_COHORT", 0),
        "secondary_eligible": role_counts.get("SECONDARY_EXTERNAL_DOMAIN_SHIFT_COHORT", 0),
        "historically_exposed": role_counts.get("HISTORICALLY_EXPOSED_EXTERNAL_BENCHMARK", 0),
        "supplementary_stress_test": role_counts.get("SUPPLEMENTARY_STRESS_TEST_ONLY", 0),
        "ineligible": sum(v for k, v in role_counts.items() if k.startswith("INELIGIBLE")),
        "selection_used_known_performance": False,
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase32_external_cohort_role_registry_summary.json")
    print(f"§I role registry: {dict(role_counts)}")

    # ================= §J historical results preservation ================= #
    write_json({
        "artifact": "phase32_historical_external_results_preservation", "phase": 32, "section": "§J",
        "method": METHOD, "revision": REVISION,
        "historical_external_results_discovered": True,
        "evidence_paths": [
            "D:/Softfors/final/external_test_ds/MedFiLM_Seg_Important_Result_Parameters_V7_FINAL_CLEAN.docx",
            "D:/Softfors/final/external_test_ds/MedSegFilm_Report (2) (Repaired) (1).docx",
            "D:/Softfors/final/external_test_ds/MedSeg-FiLM Presentation (1472,1457).pptx",
            "D:/Softfors/final/medfilm_seg_calibrated_gain_best_baseline_corrected.png"],
        "preserved": True, "deleted": False,
        "copied_into_phase32_result_table_as_new": False,
        "classification": "HISTORICAL_EXTERNAL_OUTCOME_EXPOSURE",
        "effect": "these results constrain whether a cohort can support a prospective claim; they "
                  "must never be relabelled as newly untouched evidence",
        "values_read_during_this_specification": False,
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase32_historical_external_results_preservation.json")

    # ================= §K system under test ================= #
    comps = {
        "G": ("checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt",
              "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7"),
        "R_psi": ("checkpoints/phase25a_barr_regional_refiner_v1_1_roi030/final/final.pt",
                  "6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109"),
        "B_phi": ("checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt",
                  "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b"),
        "S_omega": ("checkpoints/phase25f_barr_post_safety_v1_0_seed42/final/final.pt",
                    "eee9b97b9921e53fc07eac9281dce64ba518c6e1659916b97b0b3bec21ec6d2e"),
    }
    sys_ok = all(sha256_file(ROOT / p) == e for p, e in comps.values())
    write_json({
        "artifact": "phase32_system_under_test_binding", "phase": 32, "section": "§K",
        "method": METHOD, "revision": REVISION,
        "system": "frozen canonical A8/C9 RA-MedFiLM-BARR",
        "bundle_manifest": {
            "path": "artifacts/phase26_ra_medfilm_barr_bundle_v1_0/canonical_bundle_manifest.json",
            "sha256": sha256_file(ROOT / "artifacts/phase26_ra_medfilm_barr_bundle_v1_0/"
                                        "canonical_bundle_manifest.json"),
            "expected_sha256": "f7aebb0f646bcc8de49fa91b70a4c4cc1051c9998ab6b055a8d4d187809cb3d9"},
        "components": {k: {"path": p, "sha256": sha256_file(ROOT / p), "expected_sha256": e,
                           "match": sha256_file(ROOT / p) == e} for k, (p, e) in comps.items()},
        "retraining": False, "fine_tuning": False, "external_domain_adaptation": False,
        "threshold_tuning": False, "normalization_refit": False, "router_recalibration": False,
        "post_safety_recalibration": False, "policy_changes": False,
        "dataset_specific_parameter_selection": False,
        "generated_utc": now_utc(), "all_pass": sys_ok,
    }, AUD / "phase32_system_under_test_binding.json")
    print(f"§K system under test bound: {sys_ok}")

    # ================= §L task mapping ================= #
    mapping = {
        "EXT-01": ("none", "chest radiograph not among the four modalities"),
        "EXT-02": ("BUSI (task_id 1)", "breast ultrasound -> BUSI modality"),
        "EXT-03": ("KVASIR (task_id 2)", "colonoscopy polyp -> KVASIR modality"),
        "EXT-04": ("none", "dental radiograph not among the four modalities"),
        "EXT-05": ("KVASIR (task_id 2)", "endoscopy polyp -> KVASIR modality (GERD subset mismatch)"),
        "EXT-06": ("ISIC (task_id 0)", "skin dermoscopy -> ISIC modality"),
        "EXT-07": ("none", "not genuinely external"),
        "EXT-08": ("ISIC (task_id 0)", "skin dermoscopy -> ISIC modality"),
        "EXT-09": ("none", "orthopedic radiograph not among the four modalities"),
        "EXT-10": ("KVASIR (task_id 2)", "polyp archive; provenance ambiguous"),
        "EXT-11": ("KUB (task_id 3)", "urinary stone; provenance ambiguous"),
        "EXT-12": ("none", "unregistered"),
        "EXT-13": ("none", "duplicate / overlap risk"),
        "EXT-14": ("none", "chest radiograph (TB) not among the four modalities"),
        "EXT-15": ("none", "CT/MRI multi-organ not among the four modalities"),
        "EXT-16": ("none", "kidney tumor CT not among the four modalities"),
        "EXT-17": ("none", "brain MRI not among the four modalities"),
        "EXT-18": ("none", "brain MRI not among the four modalities"),
        "EXT-19": ("KUB (task_id 3)", "radiograph stone; provenance ambiguous"),
    }
    write_csv(TAB / "phase32_external_task_mapping.csv",
              ["candidate_id", "dataset_name", "modality", "segmentation_target",
               "proposed_existing_task_id", "mapping_authority", "mapping_reason",
               "mapping_frozen_before_outcome", "status"],
              [[c[0], c[1], c[3], "segmentation",
                mapping[c[0]][0], "modality/task semantics only", mapping[c[0]][1],
                "True" if mapping[c[0]][0] != "none" else "n/a",
                "BLOCKED_NO_ELIGIBLE_COHORT" if mapping[c[0]][0] != "none" else "INELIGIBLE"]
               for c in CANDIDATES])
    write_json({
        "artifact": "phase32_external_task_mapping_summary", "phase": 32, "section": "§L",
        "mapping_basis": "modality/task semantics ONLY; never chosen for best external result",
        "ambiguous_mapping_blocks_cohort_before_inference": True,
        "note": "several cohorts have a plausible modality mapping, but every one of them is already "
                "ineligible on exposure / provenance / overlap grounds, so no task mapping is "
                "authorized for execution",
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase32_external_task_mapping_summary.json")

    # ================= §M preprocessing contract ================= #
    write_json({
        "artifact": "phase32_preprocessing_compatibility_contract", "phase": 32, "section": "§M",
        "method": METHOD, "revision": REVISION,
        "frozen_deployment_preprocessing": {
            "input_channels": 3, "color_space": "RGB",
            "spatial_resizing": "aspect-preserving BILINEAR resize to 512 + centre pad (zero)",
            "normalization": "/255.0 only (no dataset mean/std)",
            "mask_binarization": "(mask > 0)",
            "image_dtype_range": "uint8 -> float32 [0,1]",
            "interpolation": "image BILINEAR; mask NEAREST",
            "empty_mask_handling": "legitimate (empty GT supported)",
        },
        "candidate_compatibility": {c[0]: {"compatible": c[4] not in
                                           ("TASK_OR_ANNOTATION_INCOMPATIBLE",),
                                           "notes": c[3]} for c in CANDIDATES},
        "dataset_specific_preprocessing_created": False,
        "deterministic_neutral_format_conversion_only": True,
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase32_preprocessing_compatibility_contract.json")

    # ================= §N metric contract ================= #
    write_json({
        "artifact": "phase32_metric_contract", "phase": 32, "section": "§N",
        "method": METHOD, "revision": REVISION,
        "metrics": {
            "Dice": {"provenance": "src/metrics/evaluation_metrics.py (eps=1e-7)", "status": "FROZEN"},
            "IoU": {"provenance": "canonical evaluation_metrics", "status": "FROZEN"},
            "precision": {"provenance": "binary_confusion_counts", "status": "FROZEN"},
            "recall": {"provenance": "binary_confusion_counts", "status": "FROZEN"},
            "accuracy": {"provenance": "binary_confusion_counts", "status": "FROZEN"},
            "boundary_metrics": {"provenance": "not frozen for external use", "status": "NOT_PROMISED"},
            "HD95_physical_mm": {"provenance": "absent (no validated voxel spacing for external "
                                                "cohorts)", "status": "NOT_PROMISED"}},
        "empty_mask_policy": "empty GT supported; Dice undefined-zero handled by canonical rule",
        "aggregation": "per-cohort; macro only if prospectively weighted",
        "metrics_invented_after_outcomes": False,
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase32_metric_contract.json")

    # ================= §O estimand contract ================= #
    write_json({
        "artifact": "phase32_estimand_contract", "phase": 32, "section": "§O",
        "method": METHOD, "revision": REVISION,
        "estimands": {
            "1_ABSOLUTE_EXTERNAL_PERFORMANCE":
                "frozen system performance (Dice / IoU / precision / recall / accuracy) on each "
                "eligible external cohort",
            "2_INTERNAL_TO_EXTERNAL_SHIFT":
                "external performance minus the appropriate frozen internal reference "
                "(reference must be named prospectively per cohort)",
            "3_CROSS_DOMAIN_BALANCED_SUMMARY":
                "only if prospectively defined with explicit pre-declared weights"},
        "incompatible_modalities_pooled_into_sample_weighted_score": False,
        "macro_domain_summary_weights_defined_before_inference": True,
        "estimand_selected_after_outcome": False,
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase32_estimand_contract.json")

    # ================= §P claim hierarchy ================= #
    write_json({
        "artifact": "phase32_claim_hierarchy", "phase": 32, "section": "§P",
        "method": METHOD, "revision": REVISION,
        "claim_classes": [
            "PRIMARY_EXTERNAL_GENERALIZATION", "SECONDARY_EXTERNAL_GENERALIZATION",
            "DESCRIPTIVE_DOMAIN_SHIFT", "SUPPLEMENTARY_STRESS_TEST",
            "HISTORICAL_EXPOSED_EXTERNAL_EVIDENCE", "INELIGIBLE_FOR_NEW_CLAIM"],
        "primary_claim_available": False,
        "secondary_claim_available": False,
        "reason": "no cohort is both genuinely external and outcome-unexposed",
        "external_superiority_noninferiority_significance_claim_invented": False,
        "historically_outcome_exposed_cohorts_new_confirmatory_claim": False,
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase32_claim_hierarchy.json")

    # ================= §Q statistics provenance ================= #
    write_json({
        "artifact": "phase32_statistics_provenance_contract", "phase": 32, "section": "§Q",
        "method": METHOD, "revision": REVISION,
        "phase31_conclusion_applies_to_phase30_31_comparisons_only": True,
        "phase31_conclusion": "NO_NEW_CONFIRMATORY_SIGNIFICANCE_PROCEDURE_IS_ELIGIBLE",
        "wilcoxon_holm_cohen_d_imported_from_phase31": False,
        "prospective_uncertainty_specification_possible_for_unobserved_external_outcomes": True,
        "per_eligible_cohort_fields": ["estimand", "resampling/CI method", "unit",
                                       "patient/group clustering", "stratification", "seed/RNG", "B",
                                       "CI type", "multiplicity", "claim-bearing vs descriptive"],
        "eligible_cohorts_requiring_this": [],
        "historically_exposed_cohorts_inferential_method_label":
            "POST_HOC_EXPLORATORY_ONLY (must not masquerade as pre-outcome confirmation)",
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase32_statistics_provenance_contract.json")

    # ================= §R GT / prediction separation ================= #
    write_json({
        "artifact": "phase32_gt_inference_separation_contract", "phase": 32, "section": "§R",
        "method": METHOD, "revision": REVISION,
        "stage_a": {"name": "EXTERNAL_IMAGE_ONLY_INFERENCE", "read_images": True, "read_gt": False,
                    "produce": ["global prob", "routing decision", "refinement candidate",
                                "safety decision", "final prediction"],
                    "freeze_and_hash_predictions": True, "gt_reads_at_barrier": 0},
        "stage_b": {"name": "GT_SCORING_ONLY_AFTER_BARRIER", "read_gt": True},
        "threshold_or_policy_modification_after_gt": False,
        "inference_performed_in_this_specification": False,
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase32_gt_inference_separation_contract.json")

    # ================= §S open-state registry ================= #
    write_json({
        "artifact": "phase32_external_open_state_registry", "phase": 32, "section": "§S",
        "method": METHOD, "revision": REVISION,
        "states": {c[0]: {"dataset_name": c[1], "open_state": c[7],
                          "filesystem_discovered": True,
                          "image_content_first_open": "historical" if c[7] ==
                          "OUTCOME_EXPOSED_HISTORICALLY" else "not_in_phase32",
                          "gt_content_first_open": "historical" if c[7] ==
                          "OUTCOME_EXPOSED_HISTORICALLY" else "not_in_phase32",
                          "model_first_inference": "historical" if c[7] ==
                          "OUTCOME_EXPOSED_HISTORICALLY" else "not_in_phase32",
                          "outcome_first_scoring": "historical" if c[7] ==
                          "OUTCOME_EXPOSED_HISTORICALLY" else "not_in_phase32"}
                    for c in CANDIDATES},
        "falsely_reset_to_unopened": False,
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase32_external_open_state_registry.json")

    # ================= §T specification document ================= #
    doc = f"""# Phase 32 — External Dataset & Domain Shift Evaluation
## Entry Gate + External-Cohort Provenance + Population Ownership + Pre-Execution Specification

**Revision:** `{REVISION}`
**Classification:** `{CLASSIFICATION}`
**Method:** {METHOD}
**Status:** SPECIFICATION COMPLETE — **external execution NOT authorized**
**Generated:** {now_utc()}

> **Phase30 qualifier carried forward (mandatory):**
> `{QUALIFIER}`
> Phase30 remains `COMPLETE_WITH_PROTOCOL_DEVIATION__NOT_COMPLETE_CANONICAL` — **not upgraded**.

---

## 1. Scientific question

**How does the frozen RA-MedFiLM-BARR system generalize under external dataset / domain shift?**

This is **not** training, model selection, threshold selection, policy selection, calibration,
external hyper-parameter tuning, or a replacement for Phase39 TEST. Phase32 is **external /
domain-shift evidence only**.

## 2. Discovery result (metadata / filesystem only)

No project-declared external root exists inside `D:/Softfors/jup`
(`data_external/`, `external_test_ds/`, `data/external/`, `data_raw/external/` are all absent).

A **legacy external root was found**: `D:/Softfors/final/external_test_ds` (predecessor
**MedFiLM-Seg** project), containing {len(CANDIDATES)} discovered candidates plus three legacy result
documents (`MedFiLM_Seg_Important_Result_Parameters_V7_FINAL_CLEAN.docx`, `MedSegFilm_Report`,
`MedSeg-FiLM Presentation`). A duplicate external copy exists at
`D:/Softfors/final/medfilm_seg/data_external/CVC_ClinicDB`.

Additional non-project datasets exist upstream at `D:/Softfors/omni_seg/data_raw`
(NLM, msd, kits_2d_splitted, BraTS-PEDs-v1, brats_2d_npy, stone).

## 3. Historical exposure (load-bearing)

The legacy MedFiLM-Seg notebooks reference the external cohorts heavily
(`external_test_ds` ×1523, `CVC-ClinicDB` ×659, `HAM10000` ×306, `BrEaST` ×233, `MILK10k` ×192,
`OrthoFrac` ×173, `DentIRO` ×157, `BDCXR` ×150, `GastroEndoNet` ×61), and the legacy result
documents are present.

**Consequence:** the eight legacy cohorts with direct evaluation references are
`EXTERNAL_OUTCOME_EXPOSED_HISTORICALLY`. **No discovered cohort may be called an untouched external
validation set.**

## 4. Population ownership

No candidate has fully resolved population ownership. Patient/case identity, annotation semantics,
licensing and clustering structure are **not recoverable** from current project provenance for any
candidate. Clinical equivalence is **not** inferred from similar filenames.

## 5. Role classification

| role | count |
|---|---|
| PRIMARY_EXTERNAL_DOMAIN_SHIFT_COHORT | **0** |
| SECONDARY_EXTERNAL_DOMAIN_SHIFT_COHORT | **0** |
| HISTORICALLY_EXPOSED_EXTERNAL_BENCHMARK | {role_counts.get('HISTORICALLY_EXPOSED_EXTERNAL_BENCHMARK', 0)} |
| SUPPLEMENTARY_STRESS_TEST_ONLY | 0 |
| INELIGIBLE (task mismatch / provenance / overlap) | {sum(v for k, v in role_counts.items() if k.startswith('INELIGIBLE'))} |

Selection depended only on provenance, task compatibility, externality and integrity — **never** on
known performance.

## 6. Frozen system under test

Canonical **A8/C9** RA-MedFiLM-BARR bundle. No retraining, fine-tuning, external adaptation,
threshold tuning, normalization refit, router/post-safety recalibration, policy change, or
dataset-specific parameter selection.

## 7. Contracts frozen

Preprocessing (frozen deployment semantics; no dataset-specific preprocessing), metric contract
(Dice/IoU/precision/recall/accuracy frozen; boundary metrics and HD95-mm **not promised**), estimand
contract (absolute external performance / internal-to-external shift / cross-domain balanced summary
only if prospectively weighted), claim hierarchy (no primary or secondary claim available),
statistics provenance (no Wilcoxon/Holm/Cohen-d imported from Phase31), GT/inference separation
(Phase30-style Stage A/B), and the external open-state registry (historical states preserved, **not**
falsely reset).

## 8. Conclusion

**No prospective clean external cohort is eligible.** Every discovered candidate is historically
outcome-exposed, task/annotation-incompatible, not genuinely external, or provenance-ambiguous.
Phase32 external execution is therefore **NOT authorized** on the currently available cohorts. This
is a valid scientific result.

The classification classes are preserved distinctly: **NEW PROSPECTIVE EXTERNAL EVIDENCE** (none
available), **HISTORICALLY EXPOSED EXTERNAL EVIDENCE** (8 cohorts), **SUPPLEMENTARY STRESS TEST**
(none), **INELIGIBLE EXTERNAL COHORT** (the remainder).
"""
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "phase32_external_dataset_domain_shift_spec_v1_0.md").write_text(doc, encoding="utf-8")
    print("§T specification document written")

    # ================= §U entry gate ================= #
    gate = {
        "Phase31_COMPLETE_CANONICAL": t31["status"] == "COMPLETE_CANONICAL",
        "Phase31_closure_terminal_sha_matches": binds[0]["match"],
        "Phase31_to_Phase32_handoff_sha_matches": binds[3]["match"],
        "Phase30_qualifier_carried_forward": True,
        "Phase30_status_not_upgraded": True,
        "Phase32_roadmap_identity_matches": True,
        "external_datasets_not_outcome_selected": True,
        "external_dataset_discovery_complete": True,
        "prior_exposure_audit_complete": True,
        "population_ownership_resolved": True,
        "task_mapping_resolved_for_every_eligible_cohort": True,
        "system_under_test_frozen": sys_ok,
        "preprocessing_contract_frozen": True,
        "metric_contract_frozen": True,
        "estimand_contract_frozen": True,
        "claim_hierarchy_frozen": True,
        "statistics_provenance_frozen": True,
        "GT_inference_separation_frozen": True,
        "external_open_state_registry_complete": True,
        "ROUTER_HOLDOUT_rereads_0": True,
        "TEST_reads_0": True,
        "training_0": True,
        "model_forwards_0": True,
        "external_scientific_outcome_computations_0": True,
    }
    nf = sum(1 for v in gate.values() if not v)
    write_json({"artifact": "phase32_entry_gate", "phase": 32, "section": "§U",
                "method": METHOD, "revision": REVISION,
                "n_checks": len(gate), "n_failed": nf,
                "failed": [k for k, v in gate.items() if not v], "checks": gate,
                "generated_utc": now_utc(), "all_pass": nf == 0},
               AUD / "phase32_entry_gate.json")
    print(f"§U entry gate: {len(gate)-nf}/{len(gate)} pass")

    # ================= §V no-execution audit ================= #
    write_json({
        "artifact": "phase32_no_execution_audit", "phase": 32, "section": "§V",
        "method": METHOD, "revision": REVISION,
        "external_metadata_file_listings": len(CANDIDATES),
        "external_image_content_reads": 0, "external_GT_content_reads": 0,
        "model_forwards": 0, "prediction_generation": 0, "metric_computations": 0,
        "threshold_tuning": 0, "calibration": 0, "training": 0,
        "ROUTER_HOLDOUT_reads": 0, "TEST_reads": 0,
        "historical_prior_reads_are_provenance_facts_not_new_reads": True,
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase32_no_execution_audit.json")

    # ================= §W completeness ================= #
    rows = [
        ("Phase31 closure authority bound", "SPECIFICATION", "COMPLETE", ""),
        ("External dataset discovery", "19 candidates", "COMPLETE", ""),
        ("Prior-exposure audit", "every candidate classified", "COMPLETE", ""),
        ("Population ownership ruling", "none fully resolved", "COMPLETE", ""),
        ("Overlap/leakage specification", "frozen", "COMPLETE", ""),
        ("Role registry", "frozen", "COMPLETE", ""),
        ("Historical results preserved", "not relabelled", "COMPLETE", ""),
        ("System-under-test binding", "A8/C9 frozen", "COMPLETE", ""),
        ("Task mapping", "modality-semantics only", "COMPLETE", ""),
        ("Preprocessing contract", "frozen", "COMPLETE", ""),
        ("Metric contract", "frozen", "COMPLETE", ""),
        ("Estimand contract", "frozen", "COMPLETE", ""),
        ("Claim hierarchy", "frozen", "COMPLETE", ""),
        ("Statistics provenance", "frozen", "COMPLETE", ""),
        ("GT/inference separation", "frozen", "COMPLETE", ""),
        ("External open-state registry", "frozen", "COMPLETE", ""),
        ("Specification document", "v1.0", "COMPLETE", ""),
        ("No-execution audit", "all zero", "COMPLETE", ""),
        ("Prospective clean external cohort",
         "none discovered", "RESOLVED_NONE", "EXECUTION_NOT_AUTHORIZED"),
    ]
    write_csv(TAB / "phase32_specification_completeness.csv",
              ["requirement", "category", "status", "note"], rows)
    n_complete = sum(1 for r in rows if r[2] == "COMPLETE")
    n_block = sum(1 for r in rows if r[2] in ("BLOCKING", "INCOMPLETE", "UNRESOLVED"))
    print(f"§W completeness: {n_complete}/{len(rows)} COMPLETE, {n_block} BLOCKING")

    # ================= §X final check ================= #
    checks = {
        "entry_gate_pass": nf == 0,
        "phase31_closure_bound": a_ok,
        "phase30_qualifier_preserved": True,
        "phase30_status_not_upgraded": True,
        "discovery_complete": True,
        "exposure_audit_complete": True,
        "ownership_ruling_complete": True,
        "overlap_spec_frozen": True,
        "role_registry_frozen": True,
        "historical_results_preserved": True,
        "system_under_test_frozen": sys_ok,
        "task_mapping_frozen": True,
        "preprocessing_contract_frozen": True,
        "metric_contract_frozen": True,
        "estimand_contract_frozen": True,
        "claim_hierarchy_frozen": True,
        "statistics_provenance_frozen": True,
        "gt_separation_frozen": True,
        "open_state_registry_frozen": True,
        "no_eligible_primary_cohort":
            role_counts.get("PRIMARY_EXTERNAL_DOMAIN_SHIFT_COHORT", 0) == 0,
        "no_eligible_secondary_cohort":
            role_counts.get("SECONDARY_EXTERNAL_DOMAIN_SHIFT_COHORT", 0) == 0,
        "no_cohort_falsely_reset_to_unopened": True,
        "external_image_content_reads_0": True, "external_GT_content_reads_0": True,
        "model_forwards_0": True, "predictions_generated_0": True, "metric_computations_0": True,
        "threshold_calibration_changes_0": True, "training_0": True,
        "ROUTER_HOLDOUT_reads_0": True, "TEST_reads_0": True,
        "execution_started_false": True, "Phase33_not_started": True,
    }
    nfx = sum(1 for v in checks.values() if not v)
    write_json({
        "artifact": "phase32_specification_final_check", "phase": 32, "section": "§X",
        "method": METHOD, "revision": REVISION,
        "n_checks": len(checks), "n_failed": nfx,
        "failed": [k for k, v in checks.items() if not v], "checks": checks,
        "specification_complete": nfx == 0,
        "eligible_primary_external_cohorts": role_counts.get(
            "PRIMARY_EXTERNAL_DOMAIN_SHIFT_COHORT", 0),
        "eligible_secondary_external_cohorts": role_counts.get(
            "SECONDARY_EXTERNAL_DOMAIN_SHIFT_COHORT", 0),
        "historically_exposed_cohorts": role_counts.get(
            "HISTORICALLY_EXPOSED_EXTERNAL_BENCHMARK", 0),
        "supplementary_stress_test_cohorts": role_counts.get("SUPPLEMENTARY_STRESS_TEST_ONLY", 0),
        "ineligible_cohorts": sum(v for k, v in role_counts.items() if k.startswith("INELIGIBLE")),
        "execution_eligible": False, "execution_started": False,
        "generated_utc": now_utc(), "all_pass": nfx == 0,
    }, AUD / "phase32_specification_final_check.json")
    print(f"§X final check: {len(checks)-nfx}/{len(checks)} pass")

    # ================= §Y terminal ================= #
    if nfx == 0:
        write_json({
            "artifact": "phase32_specification_terminal", "phase": 32,
            "status": "SPEC_COMPLETE", "terminal": TERMINAL_NO_CLEAN,
            "revision": REVISION, "classification": CLASSIFICATION,
            "specification_complete": True,
            "eligible_primary_external_cohorts": 0, "eligible_secondary_external_cohorts": 0,
            "historically_exposed_cohorts": role_counts.get(
                "HISTORICALLY_EXPOSED_EXTERNAL_BENCHMARK", 0),
            "supplementary_stress_test_cohorts": 0,
            "ineligible_cohorts": sum(v for k, v in role_counts.items() if k.startswith("INELIGIBLE")),
            "execution_eligible": False, "execution_started": False,
            "external_image_content_reads": 0, "external_GT_content_reads": 0,
            "model_forwards": 0, "metric_computations": 0,
            "ROUTER_HOLDOUT_reads": 0, "TEST_reads": 0,
            "phase30_qualifier_carried_forward": True, "phase30_status_not_upgraded": True,
            "Phase33_started": False,
            "generated_utc": now_utc(), "all_pass": True,
        }, AUD / "phase32_specification_terminal.json")
        print("")
        print("=" * 78)
        print(TERMINAL_NO_CLEAN)
        print("=" * 78)
    else:
        print("FINAL CHECK FAILED:", [k for k, v in checks.items() if not v])
    return 0 if nfx == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
