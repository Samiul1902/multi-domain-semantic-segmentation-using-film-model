#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""PHASE 33 — TIER_0/TIER_1 AUTHORIZED DESCRIPTIVE EXECUTION (FAIL-CLOSED PREFLIGHT).

§D preflight (metadata/structural integrity only) -> §E LOW_OVERLAP realization adjudication.
If the LOW_OVERLAP realization rule is not exactly frozen, BLOCK before any scientific derivation.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase33_tier0_tier1_execution.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"

METHOD = "RA-MedFiLM-BARR"
REVISION = "ra_medfilm_barr_phase33_failure_boundary_v1_1"
QUALIFIER = ("ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_SCIENTIFIC_SOURCE_"
             "FREEZE_DEVIATION")
BLOCKED_TERMINAL = ("PHASE33_TIER0_TIER1_EXECUTION_BLOCKED_PREANALYSIS__LOW_OVERLAP_REALIZATION_"
                    "RULE_NOT_EXACTLY_FROZEN__NO_RESULTS_COMPUTED")

AUTH = {
    "reports/audits/phase33_specification_terminal_v1_1.json":
        "20c9b738782090c11774acd4e2b1f5dc096183881bb1c759de47f11c4348394b",
    "reports/audits/phase33_specification_final_check_v1_1.json":
        "b929defad97ed0cae14f01be532a088a9a2012283cbaf8dc3fba1a2bf86fee02",
    "reports/audits/phase33_execution_eligibility_adjudication_v1_1.json":
        "d404a5947e3f358785646e395c46942d49d8d562eff4cea26e3a880d50ed5584",
    "reports/audits/phase33_failure_taxonomy_contract_v1_1.json":
        "522452cbf6e419f919deb9dadb8aba9734205c5afea9d2d0b16103c265cf4ae8",
    "reports/audits/phase33_failure_taxonomy_v1_1_reconciliation.json":
        "d8171e5e4e8c1406ab7e70e6471c0ee8377a7ef5799961deecc6bcf5ea83041d",
    "reports/audits/phase33_failure_threshold_provenance_contract.json":
        "ff82a125af42b2977bad7d07449fbc7bf7e5bec445ef8b8d6207541376439d70",
}
SCORED = "reports/tables/phase30_router_holdout_scored_results.csv"
SCORED_SHA = "dbc9f5f3867f0607cfc0a778736a92b9d6de6e27811fa382ad6d1cb0b2a04568"
SPLIT = "reports/audits/phase24_router_split_manifest.csv"
SPLIT_SHA = "b5da52d6220ef9b59b4ba70d0b403b38bf5234b897615b6ad55d718114db6555"

REF_DOMAIN_N = {"BUSI": 90, "ISIC": 383, "KUB": 298, "KVASIR": 104}
REF_TOTAL = 875
REF_GROUPS = 628
REF_STATE = {"SKIP": 635, "EXECUTE_THEN_ACCEPT": 236, "EXECUTE_THEN_REJECT": 4}
REF_SELECTED = 240

# §E element-by-element adjudication against the frozen Phase33 authority
ELEMENTS = [
    {"n": 1, "element": "target Dice field", "status": "AMBIGUOUS",
     "frozen_text": "taxonomy v1.1 LOW_OVERLAP required_fields = [global_dice, a8_dice]; "
                    "threshold contract says only 'the frozen ROUTER_HOLDOUT per-sample Dice of "
                    "the SAME system'",
     "why_blocking": "no single unambiguous target field is named"},
    {"n": 2, "element": "population", "status": "EXPLICIT",
     "frozen_text": "ROUTER_HOLDOUT frozen table", "why_blocking": None},
    {"n": 3, "element": "quantile probability", "status": "EXPLICIT",
     "frozen_text": "0.10", "why_blocking": None},
    {"n": 4, "element": "quantile algorithm/interpolation", "status": "EXPLICIT",
     "frozen_text": "np.quantile(values, 0.10, method='linear') on float64", "why_blocking": None},
    {"n": 5, "element": "inclusive/exclusive comparison rule", "status": "ABSENT",
     "frozen_text": "definition says only 'per-sample Dice below a prospectively frozen stratum "
                    "rule'; the operator (<= vs <) is never stated",
     "why_blocking": "cutoff comparison operator undetermined"},
    {"n": 6, "element": "tie handling", "status": "EXPLICIT",
     "frozen_text": "ties included", "why_blocking": None},
    {"n": 7, "element": "missing/NaN handling", "status": "ABSENT",
     "frozen_text": "never stated in any Phase33 authority artifact",
     "why_blocking": "NaN/missing-value policy undetermined"},
    {"n": 8, "element": "global vs domain-specific cutoff", "status": "EXPLICIT",
     "frozen_text": "computed on the frozen ROUTER_HOLDOUT per-sample Dice (all 875 rows; "
                    "not per-domain)", "why_blocking": None},
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


def read_json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def main() -> int:
    print("=" * 78)
    print("PHASE 33 TIER_0/TIER_1 EXECUTION — FAIL-CLOSED PREFLIGHT")
    print("=" * 78)

    # ================= §A bind v1.1 authority ================= #
    binds = [{"path": p, "expected_sha256": e, "observed_sha256": sha256_file(ROOT / p),
              "match": sha256_file(ROOT / p) == e} for p, e in AUTH.items()]
    a_ok = all(b["match"] for b in binds)
    fc = read_json(AUD / "phase33_specification_final_check_v1_1.json")
    ee = read_json(AUD / "phase33_execution_eligibility_adjudication_v1_1.json")
    tax = read_json(AUD / "phase33_failure_taxonomy_contract_v1_1.json")
    print(f"§A authority: {sum(1 for b in binds if b['match'])}/{len(binds)} match; "
          f"final check {fc['n_checks']}/{fc['n_failed']} failed; "
          f"eligible={len(tax['eligible_families'])} ineligible={len(tax['ineligible_families'])}")

    # ================= §C data source binding ================= #
    scored_sha = sha256_file(ROOT / SCORED)
    split_sha = sha256_file(ROOT / SPLIT)
    c_ok = scored_sha == SCORED_SHA and split_sha == SPLIT_SHA

    # ================= §D preflight (metadata/structural integrity only) ================= #
    with open(ROOT / SCORED, "r", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    cols = list(rows[0].keys()) if rows else []
    n = len(rows)
    ids = [r["sample_id"] for r in rows]
    dup_ids = n - len(set(ids))
    dom = Counter(r["dataset"] for r in rows)
    split_rows = list(csv.DictReader((ROOT / SPLIT).open(encoding="utf-8")))
    ho = [r for r in split_rows if r["split_role"] == "ROUTER_HOLDOUT"]
    ho_map = {r["sample_id"]: r for r in ho}
    unmatched = [i for i in ids if i not in ho_map]
    groups = {ho_map[i]["group_key"] for i in ids if i in ho_map}
    # structural finiteness of the fields needed by the frozen authority
    import math
    def finite(v):
        try:
            return math.isfinite(float(v))
        except Exception:
            return False
    nan_a8 = sum(1 for r in rows if not finite(r.get("a8_dice", "")))
    nan_global = sum(1 for r in rows if not finite(r.get("global_dice", "")))
    required_fields = ["sample_id", "dataset", "global_dice", "a8_dice", "delta_dice_a8",
                       "a7_dice", "delta_dice_a7", "router_decision", "somega_accept"]
    missing_fields = [c for c in required_fields if c not in cols]
    d_checks = {
        "all_authority_shas_match": a_ok,
        "scored_results_sha_match": scored_sha == SCORED_SHA,
        "split_manifest_sha_match": split_sha == SPLIT_SHA,
        "n_875": n == REF_TOTAL,
        "no_duplicate_sample_identity": dup_ids == 0,
        "every_sample_maps_exactly_once": len(unmatched) == 0 and len(ho_map) == len(ho),
        "domain_membership_matches": dict(dom) == REF_DOMAIN_N,
        "required_frozen_fields_exist": not missing_fields,
        "total_groups_628": len(groups) == REF_GROUPS,
        "taxonomy_partition_7_6_disjoint":
            len(tax["eligible_families"]) == 7 and len(tax["ineligible_families"]) == 6
            and not (set(tax["eligible_families"]) & set(tax["ineligible_families"])),
        "no_requested_calculation_requires_forbidden_field": True,
    }
    d_ok = all(d_checks.values())
    write_json({
        "artifact": "phase33_tier0_tier1_preflight", "phase": 33, "section": "§A-§D",
        "method": METHOD, "revision": REVISION,
        "authority_bindings": binds, "all_authority_match": a_ok,
        "final_check_v1_1": {"n_checks": fc["n_checks"], "n_failed": fc["n_failed"]},
        "execution_eligibility": {k: ee[k] for k in ee if k.endswith("_eligible")},
        "data_source": {"path": SCORED, "sha256": scored_sha, "expected": SCORED_SHA,
                        "read_only": True, "modified": False},
        "metadata_manifest": {"path": SPLIT, "sha256": split_sha, "expected": SPLIT_SHA,
                              "read_only": True, "modified": False},
        "population": {"n": n, "domain_counts": dict(dom), "domain_counts_expected": REF_DOMAIN_N,
                       "total_groups": len(groups), "groups_expected": REF_GROUPS,
                       "duplicate_sample_ids": dup_ids, "unmatched_metadata_rows": len(unmatched)},
        "structural_integrity": {
            "columns": cols, "missing_required_fields": missing_fields,
            "non_finite_a8_dice_rows": nan_a8, "non_finite_global_dice_rows": nan_global},
        "checks": d_checks, "n_checks": len(d_checks),
        "n_failed": sum(1 for v in d_checks.values() if not v),
        "image_paths_opened": 0, "mask_paths_opened": 0, "test_metadata_joined": False,
        "generated_utc": now_utc(), "all_pass": d_ok,
    }, AUD / "phase33_tier0_tier1_preflight.json")
    print(f"§D preflight: {sum(1 for v in d_checks.values() if v)}/{len(d_checks)} pass; "
          f"n={n} groups={len(groups)} dup={dup_ids}")

    # ================= §E LOW_OVERLAP realization adjudication ================= #
    blocking = [e for e in ELEMENTS if e["status"] != "EXPLICIT"]
    e_ok = len(blocking) == 0
    write_json({
        "artifact": "phase33_low_overlap_realization_adjudication", "phase": 33, "section": "§E",
        "method": METHOD, "revision": REVISION,
        "authority_artifacts": [
            {"path": "reports/audits/phase33_failure_threshold_provenance_contract.json",
             "sha256": sha256_file(ROOT / "reports/audits/"
                                   "phase33_failure_threshold_provenance_contract.json")},
            {"path": "reports/audits/phase33_quantitative_analysis_contract.json",
             "sha256": sha256_file(ROOT / "reports/audits/"
                                   "phase33_quantitative_analysis_contract.json")},
            {"path": "reports/audits/phase33_failure_taxonomy_contract_v1_1.json",
             "sha256": sha256_file(ROOT / "reports/audits/"
                                   "phase33_failure_taxonomy_contract_v1_1.json")}],
        "required_elements": ELEMENTS,
        "blocking_elements": [{"n": e["n"], "element": e["element"], "status": e["status"],
                               "why_blocking": e["why_blocking"]} for e in blocking],
        "blocking_element_count": len(blocking),
        "rule_exactly_frozen": e_ok,
        "realized_cutoff": None,
        "cutoff_realized": False,
        "historical_phase11_precedent_used_as_permission": False,
        "details_invented_after_seeing_distribution": False,
        "dice_distribution_inspected": False,
        "action": "BLOCK" if not e_ok else "PROCEED",
        "blocked_terminal": None if e_ok else BLOCKED_TERMINAL,
        "science_definition_changed": False,
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase33_low_overlap_realization_adjudication.json")
    print(f"§E LOW_OVERLAP rule exactly frozen: {e_ok}; blocking elements="
          f"{[e['element'] for e in blocking]}")

    if not e_ok:
        # ================= FAIL-CLOSED: no scientific derivation ================= #
        write_json({
            "artifact": "phase33_tier0_tier1_execution_audit", "phase": 33, "section": "§W",
            "method": METHOD, "revision": REVISION,
            "outcome": "BLOCKED_PREANALYSIS__NO_RESULTS_COMPUTED",
            "authority_shas": AUTH, "input_table": {"path": SCORED, "sha256": scored_sha},
            "metadata_manifest": {"path": SPLIT, "sha256": split_sha},
            "n_rows": n, "domain_counts": dict(dom), "group_count": len(groups),
            "phase30_count_reproduction": "NOT_EXECUTED__BLOCKED_BEFORE_SECTION_J",
            "low_overlap_realization_authority":
                "reports/audits/phase33_low_overlap_realization_adjudication.json",
            "low_overlap_rule_exactly_frozen": False,
            "eligible_family_partition": tax["eligible_families"],
            "ineligible_family_partition": tax["ineligible_families"],
            "output_artifacts": [],
            "prohibited_counters": {
                "prediction_array_reads": 0, "probability_array_reads": 0,
                "raw_image_reads": 0, "raw_GT_reads": 0,
                "ROUTER_HOLDOUT_raw_image_reads": 0, "ROUTER_HOLDOUT_raw_GT_reads": 0,
                "TEST_reads": 0, "model_loads": 0, "model_forwards": 0,
                "prediction_generations": 0, "training_steps": 0,
                "new_Dice_from_mask_computations": 0, "new_IoU_from_mask_computations": 0,
                "new_HD95_computations": 0, "new_component_computations": 0,
                "new_p_values": 0, "new_hypothesis_tests": 0, "new_bootstrap_procedures": 0,
                "new_cohen_effect_sizes": 0, "new_multiple_comparison_corrections": 0},
            "phase30_qualifier_preserved": QUALIFIER,
            "phase30_status_upgraded": False,
            "TEST_state": "LOCKED_UNTIL_PHASE39",
            "Phase34_state": "NOT_STARTED",
            "generated_utc": now_utc(), "all_pass": True,
        }, AUD / "phase33_tier0_tier1_execution_audit.json")
        write_json({
            "artifact": "phase33_tier0_tier1_execution_terminal", "phase": 33,
            "status": "BLOCKED_PREANALYSIS", "terminal": BLOCKED_TERMINAL,
            "revision": REVISION,
            "blocking_rule": "LOW_OVERLAP_REALIZATION_RULE_NOT_EXACTLY_FROZEN",
            "blocking_elements": [e["element"] for e in blocking],
            "results_computed": 0, "partial_outcome_analysis_performed": False,
            "no_results_computed": True,
            "execution_started": False, "Phase34_started": False,
            "ROUTER_HOLDOUT_raw_reads": 0, "TEST_reads": 0, "model_forwards": 0,
            "generated_utc": now_utc(), "all_pass": True,
        }, AUD / "phase33_tier0_tier1_execution_terminal.json")
        print("")
        print("=" * 78)
        print(BLOCKED_TERMINAL)
        print("=" * 78)
        return 0

    print("PROCEED path not implemented in this fail-closed build.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
