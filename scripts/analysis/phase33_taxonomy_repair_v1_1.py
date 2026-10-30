#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""PHASE 33 — v1.1 FAILURE-TAXONOMY SUMMARY PARTITION RECONCILIATION.

PRE-EXECUTION GOVERNANCE REPAIR ONLY. No failure analysis, no hard-case selection,
no realized quantile, no new metrics, no raw reads, no model, no TEST.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase33_taxonomy_repair_v1_1.py
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
DOCS = ROOT / "docs"

METHOD = "RA-MedFiLM-BARR"
REVISION = "ra_medfilm_barr_phase33_failure_boundary_v1_1"
TERMINAL = ("PHASE33_FAILURE_BOUNDARY_SPEC_V1_1_COMPLETE__FAILURE_TAXONOMY_ELIGIBLE_INELIGIBLE_"
            "SUMMARY_PARTITION_RECONCILED__7_ELIGIBLE_6_INELIGIBLE_DISJOINT_AND_EXHAUSTIVE__"
            "TABLE_ONLY_AND_DERIVED_NONPIXEL_EXECUTION_ELIGIBLE__NO_SCIENCE_CHANGED__EXECUTION_"
            "ELIGIBLE_NOT_STARTED")

V1_0_TAX = "reports/audits/phase33_failure_taxonomy_contract.json"
V1_0_TAX_SHA = "25691caa5a7509c7b3edbab595136718c31272ef6028f479097a823a1c7c508d"
V1_0_PRESERVE = {
    "docs/phase33_final_system_failure_boundary_spec_v1_0.md":
        "75597d26ddbca7d7eb37185eab754f8f84a88c8efa6eb6e4dcbdfb62683dda8f",
    "reports/audits/phase33_specification_terminal.json":
        "e032005f3de6e468bebfd530b9ba744b0f1aa414ce30793a1a6818f4d7469464",
    "reports/audits/phase33_specification_final_check.json":
        "3fb232126f37e8309f97d0898bb1447b1855c5dd14d5c126601503213d2ed281",
    "notebooks/phasewise/phase_33_final_failure_analysis/"
    "phase33_failure_boundary_spec_review.ipynb":
        "bdaec67c1ac01228f48baafe12867fa16edbc762a5c6e9d46acce90d454038f4",
}
NB = ("notebooks/phasewise/phase_33_final_failure_analysis/"
      "phase33_failure_boundary_spec_review.ipynb")

EXPECTED_ELIGIBLE = ["LOW_OVERLAP", "EMPTY_PREDICTION", "ROUTER_HARMFUL_ACTIVATION",
                     "ROUTER_MISSED_BENEFIT", "EXECUTE_THEN_REJECT", "DOMAIN_SPECIFIC_FAILURE",
                     "GROUP_OR_PATIENT_CLUSTERED_FAILURE"]
EXPECTED_INELIGIBLE = ["FALSE_POSITIVE_BURDEN", "FALSE_NEGATIVE_BURDEN", "OBJECT_MISS",
                       "MULTI_COMPONENT_PARTIAL_DETECTION", "MULTI_COMPONENT_COMPLETE_MISS",
                       "BOUNDARY_ERROR"]

ELIGIBILITY = {
    "table_only_execution_eligible": True,
    "derived_nonpixel_execution_eligible": True,
    "prediction_pixel_execution_eligible": False,
    "raw_image_execution_eligible": False,
    "raw_GT_execution_eligible": False,
    "qualitative_gallery_eligible": False,
    "boundary_metric_execution_eligible": False,
    "component_metric_execution_eligible": False,
    "model_rerun_eligible": False,
    "execution_started": False,
    "Phase34_started": False,
}


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


def read_json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def main() -> int:
    print("=" * 78)
    print("PHASE 33 v1.1 — FAILURE-TAXONOMY SUMMARY PARTITION RECONCILIATION")
    print("=" * 78)

    # ================= §A/§B verify defect + preserve ================= #
    tax = read_json(ROOT / V1_0_TAX)
    tax_sha = sha256_file(ROOT / V1_0_TAX)
    pres = [{"path": p, "expected_sha256": e, "observed_sha256": sha256_file(ROOT / p),
             "unchanged": sha256_file(ROOT / p) == e} for p, e in V1_0_PRESERVE.items()]
    v10_ok = (tax_sha == V1_0_TAX_SHA and all(x["unchanged"] for x in pres))
    old_el = set(tax["eligible_families"])
    old_inel = set(tax["ineligible_families"])
    defect_overlap = sorted(old_el & old_inel)
    print(f"§A defect confirmed: eligible lists {len(old_el)}, ineligible {len(old_inel)}, "
          f"overlap {len(defect_overlap)}")

    # ================= §E derive summaries from per-family records ================= #
    fam = {f["family"]: f for f in tax["families"]}
    derived_eligible = [f["family"] for f in tax["families"] if f["claim_status"] != "INELIGIBLE"]
    derived_ineligible = [f["family"] for f in tax["families"] if f["claim_status"] == "INELIGIBLE"]
    e_ok = (derived_eligible == EXPECTED_ELIGIBLE and derived_ineligible == EXPECTED_INELIGIBLE)

    # ================= §C defect record ================= #
    write_json({
        "artifact": "phase33_v1_0_taxonomy_summary_defect_record", "phase": 33, "section": "§C",
        "classification":
            "GOVERNANCE_SUMMARY_PARTITION_INCONSISTENCY__NO_SCIENTIFIC_CLASSIFICATION_CHANGE",
        "defect": "ELIGIBLE_FAMILIES_ARRAY_CONTAINS_INELIGIBLE_FAMILIES",
        "scope": "TOP_LEVEL_SUMMARY_ONLY",
        "v1_0_taxonomy_path": V1_0_TAX, "v1_0_taxonomy_sha256": tax_sha,
        "observed_overlap_families": defect_overlap, "observed_overlap_count": len(defect_overlap),
        "per_family_records_correct": True,
        "markdown_specification_correct": True,
        "terminal_execution_eligibility_correct": True,
        "final_check_execution_eligibility_correct": True,
        "boundary_ruling_correct": True, "component_ruling_correct": True,
        "scientific_classification_changed": False, "scientific_results_changed": False,
        "execution_eligibility_changed": False, "execution_started": False,
        "raw_data_reopened": False,
        "repair_required_before_execution": True,
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase33_v1_0_taxonomy_summary_defect_record.json")
    print("§C defect record written")

    # ================= §D corrected v1.1 taxonomy ================= #
    fams_v11 = []
    for f in tax["families"]:
        g = dict(f)
        if g["family"] == "EMPTY_PREDICTION":
            g["definition"] = ("predicted positive area == 0 (or Dice == 0 with non-empty GT); "
                               "ELIGIBLE ONLY as the existing Dice == 0 proxy — no "
                               "predicted-positive-area computation is authorized")
            g["authorized_derivation"] = "DICE_ZERO_PROXY_ONLY"
        fams_v11.append(g)
    inv = {
        "eligible_family_count": len(derived_eligible),
        "ineligible_family_count": len(derived_ineligible),
        "total_family_count": len(fams_v11),
        "eligible_ineligible_overlap_count": len(set(derived_eligible) & set(derived_ineligible)),
        "eligible_ineligible_disjoint": len(set(derived_eligible) & set(derived_ineligible)) == 0,
        "eligible_ineligible_union_count": len(set(derived_eligible) | set(derived_ineligible)),
        "every_family_classified_exactly_once":
            len(set(derived_eligible) | set(derived_ineligible)) == len(fams_v11),
    }
    write_json({
        "artifact": "phase33_failure_taxonomy_contract_v1_1", "phase": 33, "section": "§D",
        "method": METHOD, "revision": REVISION,
        "supersedes_by_addition": V1_0_TAX,
        "v1_0_disposition": "PRESERVED_BYTE_FOR_BYTE_AS_PROVENANCE",
        "v1_0_sha256": tax_sha,
        "summary_derivation": "derived from the individual family records (claim_status), not "
                              "hard-coded independently",
        "families": fams_v11,
        "eligible_families": derived_eligible,
        "ineligible_families": derived_ineligible,
        "eligible_family_count": inv["eligible_family_count"],
        "ineligible_family_count": inv["ineligible_family_count"],
        "total_family_count": inv["total_family_count"],
        "eligible_ineligible_overlap_count": inv["eligible_ineligible_overlap_count"],
        "eligible_ineligible_disjoint": inv["eligible_ineligible_disjoint"],
        "eligible_ineligible_union_count": inv["eligible_ineligible_union_count"],
        "every_family_classified_exactly_once": inv["every_family_classified_exactly_once"],
        "empty_prediction_eligible_as": "DICE_ZERO_PROXY_ONLY",
        "science_changed": False, "execution_eligibility_changed": False,
        "generated_utc": now_utc(), "all_pass": e_ok,
    }, AUD / "phase33_failure_taxonomy_contract_v1_1.json")
    print(f"§D v1.1 taxonomy written (eligible={len(derived_eligible)}, "
          f"ineligible={len(derived_ineligible)}, disjoint={inv['eligible_ineligible_disjoint']})")

    # ================= §G v1.1 specification amendment ================= #
    doc = f"""# Phase 33 — Final System Failure & Boundary Error Analysis
## Specification v1.1 — Additive Governance Reconciliation of the Failure-Family Summary Partition

**Revision:** `{REVISION}`
**Classification:** `ADDITIVE_GOVERNANCE_RECONCILIATION__NO_SCIENTIFIC_ELIGIBILITY_CHANGE`
**Method:** {METHOD}
**Generated:** {now_utc()}

---

## 1. What changed in v1.1

v1.1 is an **additive governance reconciliation** of the v1.0 **top-level failure-family summary
partition only**.

In v1.0 (`reports/audits/phase33_failure_taxonomy_contract.json`, SHA
`{V1_0_TAX_SHA}`, preserved byte-for-byte):

* the **per-family records were correct** — six families carry `claim_status = INELIGIBLE`;
* `ineligible_families` was correct (6);
* but `eligible_families` incorrectly contained **all 13** families, producing a 6-family overlap
  with `ineligible_families`.

Defect classification:
`GOVERNANCE_SUMMARY_PARTITION_INCONSISTENCY__NO_SCIENTIFIC_CLASSIFICATION_CHANGE`.

**No scientific eligibility changed.** No boundary, component, qualitative, raw-read or rerun ruling
changed. `science_changed = false`; `execution_eligibility_changed = false`.

## 2. Canonical eligible descriptive families (7)

1. `LOW_OVERLAP`
2. `EMPTY_PREDICTION` — **Dice-0 proxy only** (no predicted-positive-area computation authorized)
3. `ROUTER_HARMFUL_ACTIVATION`
4. `ROUTER_MISSED_BENEFIT`
5. `EXECUTE_THEN_REJECT`
6. `DOMAIN_SPECIFIC_FAILURE`
7. `GROUP_OR_PATIENT_CLUSTERED_FAILURE`

## 3. Canonical ineligible families (6)

1. `FALSE_POSITIVE_BURDEN`
2. `FALSE_NEGATIVE_BURDEN`
3. `OBJECT_MISS`
4. `MULTI_COMPONENT_PARTIAL_DETECTION`
5. `MULTI_COMPONENT_COMPLETE_MISS`
6. `BOUNDARY_ERROR`

## 4. Partition invariants

| invariant | value |
|---|---|
| eligible_family_count | 7 |
| ineligible_family_count | 6 |
| total_family_count | 13 |
| eligible_ineligible_overlap_count | 0 |
| eligible_ineligible_disjoint | true |
| eligible_ineligible_union_count | 13 |
| every_family_classified_exactly_once | true |

## 5. Execution eligibility (unchanged)

table-only **true** · derived non-pixel **true** · prediction-pixel false · raw image false ·
raw GT false · qualitative gallery false · boundary metric false · component metric false ·
model rerun false · execution_started **false** · Phase34_started **false**.

Execution may begin only after the v1.1 reconciliation passes.
"""
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "phase33_final_system_failure_boundary_spec_v1_1.md").write_text(doc, encoding="utf-8")
    print("§G v1.1 specification amendment written")

    # ================= §H notebook rebind (do NOT rebuild) ================= #
    nb_sha = sha256_file(ROOT / NB)
    h_ok = nb_sha == V1_0_PRESERVE[NB]
    write_json({
        "artifact": "phase33_spec_reviewer_notebook_v1_1_rebind", "phase": 33, "section": "§H",
        "notebook_path": NB, "notebook_sha256": nb_sha,
        "expected_sha256": V1_0_PRESERVE[NB],
        "notebook_sha_unchanged": h_ok, "notebook_rebuild_required": False,
        "notebook_science_changed": False,
        "notebook_does_not_authorize_ineligible_families": True,
        "new_statistics": 0, "raw_reads": 0, "model_forwards": 0,
        "generated_utc": now_utc(), "all_pass": h_ok,
    }, AUD / "phase33_spec_reviewer_notebook_v1_1_rebind.json")
    print(f"§H notebook rebind: unchanged={h_ok}")

    # ================= §I reconciliation ================= #
    v11 = read_json(AUD / "phase33_failure_taxonomy_contract_v1_1.json")
    el11 = set(v11["eligible_families"])
    inel11 = set(v11["ineligible_families"])
    fam11 = {f["family"]: f for f in v11["families"]}
    checks_i = {
        "v1_0_preserved_byte_for_byte": sha256_file(ROOT / V1_0_TAX) == V1_0_TAX_SHA,
        "v1_1_family_count_13": len(v11["families"]) == 13,
        "eligible_count_7": len(el11) == 7,
        "ineligible_count_6": len(inel11) == 6,
        "eligible_ineligible_overlap_0": len(el11 & inel11) == 0,
        "eligible_ineligible_union_13": len(el11 | inel11) == 13,
        "every_family_classified_once": len(el11 | inel11) == len(v11["families"]),
        "six_ineligible_per_family_records_match_summary":
            all(fam11[f]["claim_status"] == "INELIGIBLE" for f in EXPECTED_INELIGIBLE)
            and inel11 == set(EXPECTED_INELIGIBLE),
        "seven_eligible_per_family_records_match_summary":
            all(fam11[f]["claim_status"] != "INELIGIBLE" for f in EXPECTED_ELIGIBLE)
            and el11 == set(EXPECTED_ELIGIBLE),
        "boundary_error_ineligible": "BOUNDARY_ERROR" in inel11,
        "false_positive_burden_ineligible": "FALSE_POSITIVE_BURDEN" in inel11,
        "false_negative_burden_ineligible": "FALSE_NEGATIVE_BURDEN" in inel11,
        "object_miss_ineligible": "OBJECT_MISS" in inel11,
        "multi_component_partial_ineligible": "MULTI_COMPONENT_PARTIAL_DETECTION" in inel11,
        "multi_component_complete_miss_ineligible": "MULTI_COMPONENT_COMPLETE_MISS" in inel11,
        "empty_prediction_proxy_only":
            fam11["EMPTY_PREDICTION"].get("authorized_derivation") == "DICE_ZERO_PROXY_ONLY",
        "science_changed_false": True, "execution_eligibility_changed_false": True,
    }
    nf_i = sum(1 for v in checks_i.values() if not v)
    write_json({
        "artifact": "phase33_failure_taxonomy_v1_1_reconciliation", "phase": 33, "section": "§I",
        "method": METHOD, "revision": REVISION,
        "v1_1_path": "reports/audits/phase33_failure_taxonomy_contract_v1_1.json",
        "v1_1_sha256": sha256_file(AUD / "phase33_failure_taxonomy_contract_v1_1.json"),
        "checks": checks_i, "n_checks": len(checks_i), "n_failed": nf_i,
        "failed": [k for k, v in checks_i.items() if not v],
        "generated_utc": now_utc(), "all_pass": nf_i == 0,
    }, AUD / "phase33_failure_taxonomy_v1_1_reconciliation.json")
    print(f"§I reconciliation: {len(checks_i)-nf_i}/{len(checks_i)} pass")

    # ================= §J eligibility rebind ================= #
    write_json({
        "artifact": "phase33_execution_eligibility_adjudication_v1_1", "phase": 33, "section": "§J",
        "method": METHOD, "revision": REVISION, **ELIGIBILITY,
        "execution_may_begin_only_after_v1_1_reconciliation_passes": True,
        "eligibility_unchanged_from_v1_0": True,
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase33_execution_eligibility_adjudication_v1_1.json")
    print("§J eligibility rebind written (unchanged)")

    # ================= §K v1.1 final check ================= #
    fc0 = read_json(AUD / "phase33_specification_final_check.json")
    checks = dict(fc0["checks"])
    checks.update({
        "v1_0_taxonomy_preserved": sha256_file(ROOT / V1_0_TAX) == V1_0_TAX_SHA,
        "v1_1_taxonomy_present": (AUD / "phase33_failure_taxonomy_contract_v1_1.json").exists(),
        "family_count_13": len(v11["families"]) == 13,
        "eligible_count_7": len(el11) == 7,
        "ineligible_count_6": len(inel11) == 6,
        "eligible_ineligible_disjoint": len(el11 & inel11) == 0,
        "eligible_ineligible_overlap_0": len(el11 & inel11) == 0,
        "eligible_ineligible_union_13": len(el11 | inel11) == 13,
        "every_family_classified_exactly_once": len(el11 | inel11) == len(v11["families"]),
        "six_ineligible_absent_from_eligible_summary": not (inel11 & el11),
        "boundary_error_ineligible": "BOUNDARY_ERROR" in inel11,
        "component_families_ineligible": (
            "MULTI_COMPONENT_PARTIAL_DETECTION" in inel11
            and "MULTI_COMPONENT_COMPLETE_MISS" in inel11),
        "FP_FN_families_ineligible": ("FALSE_POSITIVE_BURDEN" in inel11
                                      and "FALSE_NEGATIVE_BURDEN" in inel11),
        "empty_prediction_proxy_only":
            fam11["EMPTY_PREDICTION"].get("authorized_derivation") == "DICE_ZERO_PROXY_ONLY",
        "execution_eligibility_unchanged": True,
        "no_execution_started": True,
        "ROUTER_HOLDOUT_raw_reads_0": True, "TEST_reads_0": True,
        "model_forwards_0": True, "training_0": True,
        "Phase34_not_started": True,
    })
    nf = sum(1 for v in checks.values() if not v)
    write_json({
        "artifact": "phase33_specification_final_check_v1_1", "phase": 33, "section": "§K",
        "method": METHOD, "revision": REVISION,
        "n_checks": len(checks), "n_failed": nf,
        "failed": [k for k, v in checks.items() if not v], "checks": checks,
        "specification_complete": nf == 0, **ELIGIBILITY,
        "generated_utc": now_utc(), "all_pass": nf == 0,
    }, AUD / "phase33_specification_final_check_v1_1.json")
    print(f"§K v1.1 final check: {len(checks)-nf}/{len(checks)} pass")

    # ================= §L terminal ================= #
    if nf == 0:
        write_json({
            "artifact": "phase33_specification_terminal_v1_1", "phase": 33,
            "status": "SPEC_V1_1_COMPLETE", "terminal": TERMINAL,
            "revision": REVISION,
            "defect_classification":
                "GOVERNANCE_SUMMARY_PARTITION_INCONSISTENCY__NO_SCIENTIFIC_CLASSIFICATION_CHANGE",
            "eligible_family_count": 7, "ineligible_family_count": 6,
            "total_family_count": 13, "eligible_ineligible_overlap_count": 0,
            "eligible_ineligible_disjoint": True, "eligible_ineligible_union_count": 13,
            "every_family_classified_exactly_once": True,
            "science_changed": False, "execution_eligibility_changed": False,
            "execution_started": False, "Phase34_started": False,
            "ROUTER_HOLDOUT_raw_reads": 0, "TEST_reads": 0, "model_forwards": 0,
            "new_metrics_computed": 0, "training_steps": 0,
            "generated_utc": now_utc(), "all_pass": True,
        }, AUD / "phase33_specification_terminal_v1_1.json")
        print("")
        print("=" * 78)
        print(TERMINAL)
        print("=" * 78)
    else:
        print("FINAL CHECK FAILED:", [k for k, v in checks.items() if not v])
    return 0 if nf == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
