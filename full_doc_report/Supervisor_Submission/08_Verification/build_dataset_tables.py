#!/usr/bin/env python
"""Generate the two supervisor dataset tables from canonical frozen evidence.

Read-only with respect to datasets. Writes only:
  05_Datasets/DATASET_RESOURCE_TABLE.csv
  05_Datasets/EXTERNAL_SKIN_EVALUATION_MATRIX.csv

Split counts are computed from manifests/phase4_v3/all_paired.csv (METADATA ONLY;
no image or mask is opened, test.csv is never opened).
"""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "full_doc_report" / "Supervisor_Submission" / "05_Datasets"

RESOURCE_FIELDS = [
    "id", "dataset", "role", "official_url", "doi_or_citation_id", "modality",
    "segmentation_target", "original_release_size", "project_rows_all_paired",
    "train", "val", "test_protected_metadata_only", "quarantined",
    "selected_split_membership", "licence", "licence_authority", "citation",
    "preprocessing_contract", "redistribution_in_zip", "status_note",
]

# Descriptive fields are transcribed from the verified authorities listed in
# DATASET_GUIDE.md; numeric fields are computed from the frozen manifest.
RESOURCE: list[dict] = [
    dict(id="1", dataset="ISIC 2018 Task 1", role="INTERNAL_PRIMARY",
         official_url="https://challenge.isic-archive.com/data/",
         doi_or_citation_id="arXiv:1902.03368; doi:10.1038/sdata.2018.161",
         modality="dermoscopy RGB", segmentation_target="cutaneous lesion boundary",
         original_release_size="2594 official train / 100 official val / 1000 official test",
         licence="CC0 1.0 (Task 1 only)",
         licence_authority="FINAL_DATASET_PERMISSION_AND_EXECUTION_DECISION.md",
         citation="Codella et al. 2019 arXiv:1902.03368; Tschandl et al. 2018 Sci Data 5:180161",
         preprocessing_contract="phase19_preprocessing_contract_v1",
         redistribution_in_zip="METADATA_MANIFESTS_ONLY",
         status_note="Project splits are NOT the official partitions: VAL808 ISIC = 231 official-train + 14 official-val + 112 official-test."),
    dict(id="2", dataset="BUSI-WHU V3", role="INTERNAL_PRIMARY",
         official_url="https://data.mendeley.com/datasets/k6cpmwybk3/3",
         doi_or_citation_id="doi:10.17632/k6cpmwybk3.3",
         modality="B-mode breast ultrasound (greyscale)",
         segmentation_target="breast lesion / tumour contour",
         original_release_size="927 images + 927 masks",
         licence="CC BY 4.0; ethics WDRY2022-K217",
         licence_authority="FINAL_DATASET_PERMISSION_AND_EXECUTION_DECISION.md",
         citation="Al-Dhabyani et al., Data in Brief 28:104863 (2020)",
         preprocessing_contract="phase19_preprocessing_contract_v1",
         redistribution_in_zip="METADATA_MANIFESTS_ONLY",
         status_note="Wuhan University release, NOT the Cairo BUSI set. Patient workbook excluded and never opened."),
    dict(id="3", dataset="Kvasir-SEG", role="INTERNAL_PRIMARY",
         official_url="https://datasets.simula.no/kvasir-seg/",
         doi_or_citation_id="doi:10.1007/978-3-030-37734-2_37",
         modality="colonoscopy endoscopy RGB",
         segmentation_target="colorectal polyp",
         original_release_size="1000 images + 1000 masks",
         licence="Simula custom research/education; commercial use forbidden without written permission (NOT CC)",
         licence_authority="FINAL_DATASET_PERMISSION_AND_EXECUTION_DECISION.md",
         citation="Jha et al., MMM 2020, pp.451-462",
         preprocessing_contract="phase19_preprocessing_contract_v1",
         redistribution_in_zip="METADATA_MANIFESTS_ONLY",
         status_note="Mandatory citation; non-commercial only."),
    dict(id="4", dataset="KUB-StoneX Figshare v1", role="INTERNAL_PRIMARY",
         official_url="https://doi.org/10.6084/m9.figshare.32049369.v1",
         doi_or_citation_id="doi:10.6084/m9.figshare.32049369.v1",
         modality="KUB abdominal radiograph (mixed L/RGB)",
         segmentation_target="urinary calculus / stone instance ROI",
         original_release_size="2570 images / 1703 patients (432 bladder, 573 kidney, 177 ureteric, 1388 normal)",
         licence="CC BY 4.0; IRB REC-FSIT-2025/No: 12732",
         licence_authority="FINAL_DATASET_PERMISSION_AND_EXECUTION_DECISION.md",
         citation="Zerin et al., Figshare v1 (2026-04-30)",
         preprocessing_contract="phase19_preprocessing_contract_v1",
         redistribution_in_zip="METADATA_MANIFESTS_ONLY",
         status_note="Mixed unit of analysis: 1146 full-field + 1670 ROI patches = 2816 active rows; local mirror missing 32 masks."),
    dict(id="5", dataset="CVC-ClinicDB", role="EXTERNAL_EXTERNAL884",
         official_url="https://polyp.grand-challenge.org/CVCClinicDB/",
         doi_or_citation_id="Bernal et al., Comput Med Imaging Graph 43:99-111 (2015)",
         modality="colonoscopy endoscopy RGB", segmentation_target="polyp boundary",
         original_release_size="612 frames + 612 masks",
         licence="CHECK_REQUIRED (no local licence file; redistribution not cleared)",
         licence_authority="ext01_external_dataset_inventory.json",
         citation="Bernal et al. 2015",
         preprocessing_contract="ext02_preprocessing_freeze.json",
         redistribution_in_zip="RESULT_TABLES_AND_AUDITS_ONLY",
         status_note="612 evaluated, 0 excluded; cluster bootstrap n_clusters=29."),
    dict(id="6", dataset="BrEaST-Lesions-USG", role="EXTERNAL_EXTERNAL884",
         official_url="https://www.cancerimagingarchive.net/collection/breast-lesions-usg/",
         doi_or_citation_id="Pawlowska et al., TCIA (2024)",
         modality="breast ultrasound", segmentation_target="breast lesion (tumour mask)",
         original_release_size="256 images; 252 tumour masks",
         licence="CHECK_REQUIRED (redistribution not cleared)",
         licence_authority="ext01_external_dataset_inventory.json",
         citation="Pawlowska et al. 2024 (TCIA)",
         preprocessing_contract="ext02_preprocessing_freeze.json (RGBA->RGB)",
         redistribution_in_zip="RESULT_TABLES_AND_AUDITS_ONLY",
         status_note="4 cases excluded pre-inference for missing tumour mask; patient-level independence NOT verifiable."),
    dict(id="7", dataset="Stones_where_are_you (Roboflow COCO-seg v3)", role="EXTERNAL_EXTERNAL884",
         official_url="https://universe.roboflow.com/xray-abdomen-to-identify-stones/stones_where_are_you",
         doi_or_citation_id="Roboflow Universe dataset page (no DOI)",
         modality="abdominal X-ray", segmentation_target="urinary stone (COCO polygon -> binary)",
         original_release_size="460 images / 456 masks; 384 train + 56 valid + 20 test",
         licence="CC0_PUBLIC_DOMAIN as recorded in ext01 inventory (not independently re-verified)",
         licence_authority="ext01_external_dataset_inventory.json",
         citation="Roboflow Universe contributor page",
         preprocessing_contract="ext02_preprocessing_freeze.json (COCO rasterisation)",
         redistribution_in_zip="RESULT_TABLES_AND_AUDITS_ONLY",
         status_note="Only 20 test images evaluated: 6 stone-positive + 14 stone-free. 14/14 stone-free false-positive in BOTH arms."),
    dict(id="8", dataset="HAM10000 (ISIC-2018 Task 3 training input)", role="AUDITED_NOT_EVALUATED",
         official_url="https://doi.org/10.7910/DVN/DBW86T",
         doi_or_citation_id="doi:10.7910/DVN/DBW86T",
         modality="dermoscopy RGB",
         segmentation_target="NONE in official release (7-class diagnostic labels); local binary masks have NO provenance",
         original_release_size="10015 classification images",
         licence="CC BY-NC 4.0 (attribution ViDIR Group, Medical University of Vienna; non-commercial)",
         licence_authority="local images/LICENSE.txt + images/ATTRIBUTION.txt",
         citation="Tschandl et al., Sci Data 5:180161 (2018); arXiv:1803.10417",
         preprocessing_contract="ext02_preprocessing_freeze.json (NOT APPLIED: no eligible evaluation executed)",
         redistribution_in_zip="METADATA_MANIFEST_COUNTS_AND_AUDIT_ONLY",
         status_note="EXTERNAL_SKIN_DATASET_AVAILABLE__SEGMENTATION_EVALUATION_NOT_ESTABLISHED; excluded from EXTERNAL884; 0 rows analysed."),
]

EXTERNAL_EVALUATED = {"5": 612, "6": 252, "7": 20, "8": 0}

MATRIX_FIELDS = [
    "cohort", "modality", "skin_lesion_cohort", "official_url_or_doi",
    "local_images", "local_masks", "matched_mask_coverage_pct",
    "mask_provenance_verified", "n_evaluated_cases", "n_saved_full_predictions",
    "part_of_external884", "dice", "iou", "precision", "recall", "hd95_px",
    "paired_delta", "evaluation_status", "reason_not_reported",
]

MATRIX_ROWS = [
    dict(cohort="ISIC 2018 Task 1 (internal)", modality="dermoscopy",
         skin_lesion_cohort="YES", official_url_or_doi="https://challenge.isic-archive.com/data/",
         local_images="", local_masks="", matched_mask_coverage_pct="",
         mask_provenance_verified="YES", n_evaluated_cases=357,
         n_saved_full_predictions="SAVED_MASKS_AVAILABLE",
         part_of_external884="NO_INTERNAL_VAL808",
         dice="0.898081 (FULL, VAL808 ISIC)", iou="0.831117", precision="0.916000",
         recall="0.906581", hd95_px="25.310635", paired_delta="+0.000892",
         evaluation_status="COMPLETED_INTERNAL_VALIDATION",
         reason_not_reported="Internal domain, not an external skin-lesion benchmark."),
    dict(cohort="HAM10000", modality="dermoscopy",
         skin_lesion_cohort="YES", official_url_or_doi="https://doi.org/10.7910/DVN/DBW86T",
         local_images=10015, local_masks=10015, matched_mask_coverage_pct=100.0,
         mask_provenance_verified="NO", n_evaluated_cases=0,
         n_saved_full_predictions=0, part_of_external884="NO",
         dice="NOT_ESTABLISHED", iou="NOT_ESTABLISHED", precision="NOT_ESTABLISHED",
         recall="NOT_ESTABLISHED", hd95_px="NOT_ESTABLISHED", paired_delta="NOT_ESTABLISHED",
         evaluation_status="EXTERNAL_SKIN_DATASET_AVAILABLE__SEGMENTATION_EVALUATION_NOT_ESTABLISHED",
         reason_not_reported=("Official Task 3 release ships no segmentation masks; 10015 local binary masks have "
                              "undocumented provenance (HAM10000_EXCLUDED__MASK_PROVENANCE_UNVERIFIED). "
                              "No dataset-level ReMedFiLM FULL predictions and no FULL metrics exist. "
                              "The single historical F5 ISIC_0024306 value is GlobalMedFiLM-only, single-case.")),
    dict(cohort="CVC-ClinicDB", modality="colonoscopy endoscopy",
         skin_lesion_cohort="NO", official_url_or_doi="https://polyp.grand-challenge.org/CVCClinicDB/",
         local_images=612, local_masks=612, matched_mask_coverage_pct=100.0,
         mask_provenance_verified="YES", n_evaluated_cases=612,
         n_saved_full_predictions="SAVED_RETROSPECTIVE", part_of_external884="YES",
         dice="0.689747 (FULL) / 0.686568 (G)", iou="0.577924 / 0.574871",
         precision="0.683420 / 0.679505", recall="0.813743 / 0.815625",
         hd95_px="108.493700 / 109.593437", paired_delta="SEE_c1_external_stress_per_case.csv",
         evaluation_status="COMPLETED_EXTERNAL_RETROSPECTIVE",
         reason_not_reported=""),
    dict(cohort="BrEaST-Lesions-USG", modality="breast ultrasound",
         skin_lesion_cohort="NO", official_url_or_doi="https://www.cancerimagingarchive.net/collection/breast-lesions-usg/",
         local_images=256, local_masks=252, matched_mask_coverage_pct=98.4375,
         mask_provenance_verified="YES", n_evaluated_cases=252,
         n_saved_full_predictions="SAVED_RETROSPECTIVE", part_of_external884="YES",
         dice="SEE_c1_external_stress_summary.csv", iou="SEE_c1_external_stress_summary.csv",
         precision="SEE_c1_external_stress_summary.csv", recall="SEE_c1_external_stress_summary.csv",
         hd95_px="SEE_c1_external_stress_summary.csv", paired_delta="SEE_c1_external_stress_per_case.csv",
         evaluation_status="COMPLETED_EXTERNAL_RETROSPECTIVE",
         reason_not_reported="Patient-level independence NOT verifiable."),
    dict(cohort="Stones_where_are_you", modality="abdominal X-ray",
         skin_lesion_cohort="NO",
         official_url_or_doi="https://universe.roboflow.com/xray-abdomen-to-identify-stones/stones_where_are_you",
         local_images=460, local_masks=456, matched_mask_coverage_pct=99.1304,
         mask_provenance_verified="COCO_POLYGON_FROZEN", n_evaluated_cases=20,
         n_saved_full_predictions="SAVED_RETROSPECTIVE", part_of_external884="YES",
         dice="0.273755 stone-positive n=6 (FULL); 0.0 on each of 14 empty-GT stone-free cases; 20-case mean 0.082126",
         iou="0.205312 stone-positive n=6; 20-case mean 0.061594",
         precision="0.251522 stone-positive n=6; 20-case mean 0.075457",
         recall="UNDEFINED for empty-GT cases; n_defined=6 (0.674008 FULL)",
         hd95_px="UNDEFINED for empty-GT cases; n_defined=6 (169.899664 FULL)",
         paired_delta="SEE_c1_external_stress_per_case.csv",
         evaluation_status="COMPLETED_EXTERNAL_RETROSPECTIVE_WITH_NEGATIVE_CONTROL_FAILURE",
         reason_not_reported=("14/14 stone-free scans produce a false-positive mask in BOTH arms "
                              "(empty_prediction_rate=0.0, specificity 0.0). For empty GT, Dice/IoU/"
                              "Precision are defined and equal 0; Recall/HD95/ASSD are undefined and "
                              "reported on n=6 only. The 20-case means mix two denominators.")),
]


def split_counts() -> dict[str, dict[str, int]]:
    """Counts from all_paired.csv split-assignment metadata. No pixels, no test.csv."""
    counts: dict[str, Counter] = {}
    with (ROOT / "manifests" / "phase4_v3" / "all_paired.csv").open(
            "r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            counts.setdefault(row["dataset"], Counter())[row["split"]] += 1
    return {k: dict(v) for k, v in counts.items()}


def main() -> int:
    counts = split_counts()
    dataset_key = {"1": "ISIC", "2": "BUSI", "3": "KVASIR", "4": "KUB"}
    rows = []
    for item in RESOURCE:
        row = {k: "" for k in RESOURCE_FIELDS}
        row.update(item)
        key = dataset_key.get(item["id"])
        if key:
            c = counts[key]
            row["train"] = c.get("TRAIN", 0)
            row["val"] = c.get("VAL", 0)
            row["test_protected_metadata_only"] = c.get("TEST", 0)
            row["quarantined"] = c.get("QUARANTINED", 0)
            row["project_rows_all_paired"] = sum(c.values())
            row["selected_split_membership"] = (
                f"TRAIN {row['train']} / VAL808 {row['val']} / TEST1683(PROTECTED) "
                f"{row['test_protected_metadata_only']} / QUARANTINED {row['quarantined']}"
            )
        else:
            n_eval = EXTERNAL_EVALUATED[item["id"]]
            row["project_rows_all_paired"] = "N/A_EXTERNAL"
            row["selected_split_membership"] = (
                f"EXTERNAL884 evaluated n={n_eval}" if n_eval else "0 evaluated (excluded)")
        rows.append(row)

    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "DATASET_RESOURCE_TABLE.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=RESOURCE_FIELDS)
        w.writeheader()
        w.writerows(rows)
    with (OUT / "EXTERNAL_SKIN_EVALUATION_MATRIX.csv").open(
            "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=MATRIX_FIELDS)
        w.writeheader()
        w.writerows(MATRIX_ROWS)
    print(f"DATASET_RESOURCE_TABLE.csv: {len(rows)} rows")
    print(f"EXTERNAL_SKIN_EVALUATION_MATRIX.csv: {len(MATRIX_ROWS)} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
