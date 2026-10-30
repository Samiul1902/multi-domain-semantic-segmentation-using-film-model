#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""PHASE 33 — LOW_OVERLAP REALIZATION RULE: REFINED ELEMENT-LEVEL ADJUDICATION (v2).

Re-affirms the fail-closed determination after a full re-read of the Phase33 authority, with a
finer element-level classification (EXPLICIT / DETERMINABLE_BY_TEXT / ABSENT) and an
empirical-materiality check on the missing/NaN element.

No scientific derivation. No raw reads. No model. No TEST.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase33_low_overlap_adjudication_v2.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"

METHOD = "RA-MedFiLM-BARR"
REVISION = "ra_medfilm_barr_phase33_failure_boundary_v1_1"
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
}
SCORED = "reports/tables/phase30_router_holdout_scored_results.csv"
SCORED_SHA = "dbc9f5f3867f0607cfc0a778736a92b9d6de6e27811fa382ad6d1cb0b2a04568"
SPLIT = "reports/audits/phase24_router_split_manifest.csv"
SPLIT_SHA = "b5da52d6220ef9b59b4ba70d0b403b38bf5234b897615b6ad55d718114db6555"

ELEMENTS = [
    {"n": 1, "element": "target Dice field",
     "status": "DETERMINABLE_BY_TEXT_NOT_EXPLICIT",
     "authority_text": "threshold provenance: 'the frozen ROUTER_HOLDOUT per-sample Dice of the "
                       "SAME system'",
     "reading": "the system under analysis is the final A8/C9 system -> a8_dice; global_dice is "
                "the REFERENCE, not 'the system'",
     "residual_ambiguity": "the taxonomy v1.1 LOW_OVERLAP record lists BOTH global_dice and "
                           "a8_dice as required_fields, so no column name is stated outright",
     "explicitly_named": False},
    {"n": 2, "element": "population", "status": "EXPLICIT",
     "authority_text": "ROUTER_HOLDOUT frozen table", "explicitly_named": True},
    {"n": 3, "element": "quantile probability", "status": "EXPLICIT",
     "authority_text": "0.10", "explicitly_named": True},
    {"n": 4, "element": "quantile algorithm/interpolation", "status": "EXPLICIT",
     "authority_text": "np.quantile(values, 0.10, method='linear') on float64", "explicitly_named": True},
    {"n": 5, "element": "inclusive/exclusive comparison rule",
     "status": "DETERMINABLE_BY_TEXT_NOT_EXPLICIT",
     "authority_text": "definition says 'below a prospectively frozen stratum rule'; the threshold "
                       "contract adds 'ties included'",
     "reading": "'below' + 'ties included' -> inclusive comparison (<=) with ties at the cutoff "
                "counted as LOW_OVERLAP",
     "residual_ambiguity": "the operator symbol is never written; 'below' alone would read as '<'",
     "explicitly_named": False},
    {"n": 6, "element": "tie handling", "status": "EXPLICIT",
     "authority_text": "ties included", "explicitly_named": True},
    {"n": 7, "element": "missing/NaN handling", "status": "ABSENT",
     "authority_text": "not stated in the threshold provenance contract, the taxonomy v1.1, the "
                       "quantitative analysis contract, the hard-case selection contract, or the "
                       "v1.1 specification document",
     "reading": None, "residual_ambiguity": "no basis in authority for inference",
     "explicitly_named": False},
    {"n": 8, "element": "global vs domain-specific cutoff", "status": "EXPLICIT",
     "authority_text": "computed on the frozen ROUTER_HOLDOUT per-sample Dice (all 875 rows; not "
                       "per-domain)", "explicitly_named": True},
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
    tmp = str(path) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(json.dumps(obj, indent=1) + "\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def main() -> int:
    print("=" * 78)
    print("PHASE 33 — LOW_OVERLAP RULE REFINED ELEMENT-LEVEL ADJUDICATION (v2)")
    print("=" * 78)

    binds = [{"path": p, "expected_sha256": e, "observed_sha256": sha256_file(ROOT / p),
              "match": sha256_file(ROOT / p) == e} for p, e in AUTH.items()]
    a_ok = all(b["match"] for b in binds)
    inp_ok = (sha256_file(ROOT / SCORED) == SCORED_SHA
              and sha256_file(ROOT / SPLIT) == SPLIT_SHA)

    # empirical materiality of element 7 (structural check only; no distribution inspection)
    rows = list(csv.DictReader((ROOT / SCORED).open(encoding="utf-8")))

    def nf(v):
        try:
            return not math.isfinite(float(v))
        except Exception:
            return True

    nonfinite_a8 = sum(1 for r in rows if nf(r.get("a8_dice", "")))
    nonfinite_global = sum(1 for r in rows if nf(r.get("global_dice", "")))
    empty_a8 = sum(1 for r in rows if not str(r.get("a8_dice", "")).strip())

    blocking = [e for e in ELEMENTS if e["status"] != "EXPLICIT"]
    hard_blocking = [e for e in ELEMENTS if e["status"] == "ABSENT"]
    soft_blocking = [e for e in ELEMENTS if e["status"] == "DETERMINABLE_BY_TEXT_NOT_EXPLICIT"]
    block = len(blocking) > 0
    print(f"§A authority {sum(1 for b in binds if b['match'])}/{len(binds)}; inputs ok={inp_ok}")
    print(f"§E ABSENT={[e['element'] for e in hard_blocking]} "
          f"DETERMINABLE_NOT_EXPLICIT={[e['element'] for e in soft_blocking]}")
    print(f"    non-finite a8_dice rows={nonfinite_a8} (element-7 empirical materiality)")

    write_json({
        "artifact": "phase33_low_overlap_rule_element_adjudication_v2", "phase": 33, "section": "§E",
        "method": METHOD, "revision": REVISION,
        "purpose": "re-affirm the fail-closed LOW_OVERLAP realization determination after a full "
                   "re-read of every Phase33 authority artifact, with a finer element-level "
                   "classification and an empirical-materiality check",
        "authority_bindings": binds, "all_authority_match": a_ok,
        "inputs": {"scored_table": {"path": SCORED, "sha256": sha256_file(ROOT / SCORED),
                                    "expected": SCORED_SHA, "match": sha256_file(ROOT / SCORED) == SCORED_SHA},
                   "split_manifest": {"path": SPLIT, "sha256": sha256_file(ROOT / SPLIT),
                                      "expected": SPLIT_SHA, "match": sha256_file(ROOT / SPLIT) == SPLIT_SHA}},
        "authority_artifacts_re_read": [
            "reports/audits/phase33_failure_threshold_provenance_contract.json",
            "reports/audits/phase33_failure_taxonomy_contract_v1_1.json",
            "reports/audits/phase33_quantitative_analysis_contract.json",
            "reports/audits/phase33_hard_case_selection_contract.json",
            "docs/phase33_final_system_failure_boundary_spec_v1_1.md"],
        "elements": ELEMENTS,
        "element_status_counts": {
            "EXPLICIT": sum(1 for e in ELEMENTS if e["status"] == "EXPLICIT"),
            "DETERMINABLE_BY_TEXT_NOT_EXPLICIT": len(soft_blocking),
            "ABSENT": len(hard_blocking)},
        "explicit_elements": [e["element"] for e in ELEMENTS if e["status"] == "EXPLICIT"],
        "determinable_not_explicit_elements": [e["element"] for e in soft_blocking],
        "absent_elements": [e["element"] for e in hard_blocking],
        "element_7_empirical_materiality": {
            "non_finite_a8_dice_rows": nonfinite_a8,
            "non_finite_global_dice_rows": nonfinite_global,
            "empty_a8_dice_rows": empty_a8,
            "materiality": "IMMATERIAL_FOR_THIS_DATA" if (nonfinite_a8 == 0 and empty_a8 == 0)
                           else "MATERIAL",
            "note": "the authority still does not STATE a missing/NaN policy; empirical absence of "
                    "missing values does not convert an unstated rule into a frozen rule"},
        "dice_distribution_inspected": False,
        "quantile_or_cutoff_computed": False,
        "historical_phase11_precedent_used_as_permission": False,
        "rule_exactly_frozen": not block,
        "blocking_elements": [{"n": e["n"], "element": e["element"], "status": e["status"]}
                              for e in blocking],
        "action": "BLOCK" if block else "PROCEED",
        "blocked_terminal": BLOCKED_TERMINAL if block else None,
        "unblock_amendment_required": {
            "scope": "prospective Phase33 amendment (pre-outcome), additive",
            "must_state": [
                "the exact target Dice column (recommend naming a8_dice explicitly)",
                "the exact cutoff comparison operator (recommend '<=, ties included')",
                "the exact missing/NaN policy (recommend 'no NaN expected; any non-finite value "
                "excluded from the quantile and flagged, never silently dropped')"],
            "then": "re-run the fail-closed preflight and realize the cutoff deterministically"},
        "science_definition_changed": False,
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase33_low_overlap_rule_element_adjudication_v2.json")
    print(f"§E action={('BLOCK' if block else 'PROCEED')}")
    print("")
    print("=" * 78)
    if block:
        print(BLOCKED_TERMINAL)
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
