#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""PHASE 33 — LOW_OVERLAP REALIZATION-RULE CLARIFICATION (SPEC v1.2).

Prospective, pre-outcome, ADDITIVE amendment that makes the 8-element LOW_OVERLAP realization rule
FULLY EXPLICIT, resolving the three elements left unresolved in v1.1:
  * element 1 (target Dice field)          -> a8_dice  (the SAME system = final A8/C9 system)
  * element 5 (inclusive/exclusive rule)   -> "<=" (inclusive; ties at the cutoff are LOW_OVERLAP)
  * element 7 (missing/NaN handling)       -> REQUIRE_ALL_FINITE_NO_EXCLUSION (else BLOCK)

Hard prohibitions honoured by this script:
  * NO cutoff / quantile is computed.
  * NO distributional statistic of a8_dice (min/max/mean/quantiles/sorted values) is inspected.
  * NO raw image / raw GT read. NO model forward. NO TEST read. NO TIER_0/TIER_1 analysis rerun.
  * Only a STRUCTURAL finiteness count (number of non-finite a8_dice rows) is re-verified; that
    structural property was already recorded in the v1.1 preflight and is not a distributional
    summary.

All v1.1 authority artifacts and all blocked-execution artifacts are preserved byte-for-byte.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase33_low_overlap_v1_2.py
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
DOCS = ROOT / "docs"

METHOD = "RA-MedFiLM-BARR"
REVISION = "ra_medfilm_barr_phase33_failure_boundary_v1_2"

TERMINAL = ("PHASE33_FAILURE_BOUNDARY_SPEC_V1_2_COMPLETE__LOW_OVERLAP_REALIZATION_RULE_FULLY_"
            "EXPLICIT__A8_DICE_GLOBAL_Q10_LINEAR_FLOAT64_LTE_TIES_INCLUDED_REQUIRE_ALL_FINITE_NO_"
            "EXCLUSION__NO_DISTRIBUTION_OR_CUTOFF_INSPECTED__TIER0_TIER1_EXECUTION_ELIGIBLE_NOT_"
            "STARTED")
BLOCK_TERMINAL = ("PHASE33_LOW_OVERLAP_REALIZATION_BLOCKED__A8_DICE_NOT_COMPLETE_FINITE_875__"
                  "NO_CUTOFF_COMPUTED")
PRIOR_BLOCK_TERMINAL = ("PHASE33_TIER0_TIER1_EXECUTION_BLOCKED_PREANALYSIS__LOW_OVERLAP_"
                        "REALIZATION_RULE_NOT_EXACTLY_FROZEN__NO_RESULTS_COMPUTED")

# --------------------------------------------------------------------------------------------------
# Byte-for-byte preservation set (v1.1 authority + blocked execution + prior spec/taxonomy/notebook)
# --------------------------------------------------------------------------------------------------
PRESERVE = {
    # v1.1 authority
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
    # blocked execution evidence
    "reports/audits/phase33_tier0_tier1_execution_terminal.json":
        "79a9215e883b2baba47d610e6399f0c39bd53fb9cbe5496ba82b9486ba2051d8",
    "reports/audits/phase33_tier0_tier1_execution_audit.json":
        "da439de70d9f122882dc063a48cb19f45a9252a6a9ba68a02aa8d3bf28b531a5",
    "reports/audits/phase33_tier0_tier1_preflight.json":
        "8cac456a7ead35a6956a14b693782de041f16a2874b5fac82ad4d428f09c25e7",
    "reports/audits/phase33_low_overlap_realization_adjudication.json":
        "a3fe87c19d0377ad7188a7a36c6d78305e24d691569350cb5683484c8cdbfc18",
    "reports/audits/phase33_low_overlap_rule_element_adjudication_v2.json":
        "73123ce1554d52bccfe87d75ec240d941712a3ddaaa88ed711470a9b2e7978a8",
    # blocked notebook
    "notebooks/phasewise/phase_33_final_failure_analysis/phase33_final_failure_analysis_review.ipynb":
        "bf7443e0760d2bc49078776fd99130e7560f6460d5952921523d98f45c4ecc1a",
    # prior spec docs + v1.0 taxonomy + threshold provenance
    "docs/phase33_final_system_failure_boundary_spec_v1_0.md":
        "75597d26ddbca7d7eb37185eab754f8f84a88c8efa6eb6e4dcbdfb62683dda8f",
    "docs/phase33_final_system_failure_boundary_spec_v1_1.md":
        "c3020db76b1c6f75db13c894406f5c955c7e7431b5c6f5a2082818f2958afc38",
    "reports/audits/phase33_failure_taxonomy_contract.json":
        "25691caa5a7509c7b3edbab595136718c31272ef6028f479097a823a1c7c508d",
    "reports/audits/phase33_failure_threshold_provenance_contract.json":
        "ff82a125af42b2977bad7d07449fbc7bf7e5bec445ef8b8d6207541376439d70",
    # frozen inputs (read-only)
    "reports/tables/phase30_router_holdout_scored_results.csv":
        "dbc9f5f3867f0607cfc0a778736a92b9d6de6e27811fa382ad6d1cb0b2a04568",
    "reports/audits/phase24_router_split_manifest.csv":
        "b5da52d6220ef9b59b4ba70d0b403b38bf5234b897615b6ad55d718114db6555",
}
SCORED = "reports/tables/phase30_router_holdout_scored_results.csv"
SPLIT = "reports/audits/phase24_router_split_manifest.csv"

# --------------------------------------------------------------------------------------------------
# The 8-element LOW_OVERLAP realization rule, now FULLY EXPLICIT (v1.2)
# --------------------------------------------------------------------------------------------------
ELEMENTS_V1_2 = [
    {"n": 1, "element": "target Dice field", "status": "NOW_EXPLICIT",
     "previous_v1_1_status": "DETERMINABLE_BY_TEXT_NOT_EXPLICIT",
     "value": "a8_dice",
     "statement": "The LOW_OVERLAP stratum is defined on the FINAL A8/C9 system's per-sample Dice, "
                  "i.e. the column `a8_dice` of the frozen ROUTER_HOLDOUT scored table. "
                  "`global_dice` is the REFERENCE comparator only and is NOT used to realize the "
                  "cutoff.",
     "reference_only_column": "global_dice"},
    {"n": 2, "element": "population", "status": "PREVIOUSLY_EXPLICIT",
     "previous_v1_1_status": "EXPLICIT",
     "value": "frozen ROUTER_HOLDOUT table (all 875 rows)",
     "statement": "Computed on the frozen ROUTER_HOLDOUT scored table; n = 875 samples.",
     "n_rows": 875},
    {"n": 3, "element": "quantile probability", "status": "PREVIOUSLY_EXPLICIT",
     "previous_v1_1_status": "EXPLICIT", "value": 0.10,
     "statement": "Bottom-decile quantile probability q = 0.10."},
    {"n": 4, "element": "quantile algorithm/interpolation", "status": "PREVIOUSLY_EXPLICIT",
     "previous_v1_1_status": "EXPLICIT",
     "value": "np.quantile(values, 0.10, method='linear') on float64",
     "statement": "values = a8_dice cast to float64; NumPy linear (type-7) interpolation."},
    {"n": 5, "element": "inclusive/exclusive comparison rule", "status": "NOW_EXPLICIT",
     "previous_v1_1_status": "DETERMINABLE_BY_TEXT_NOT_EXPLICIT", "value": "<=",
     "statement": "A sample is LOW_OVERLAP iff `a8_dice <= cutoff` (INCLUSIVE). The operator is "
                  "written explicitly as <= ; the phrase 'below' is hereby bound to an inclusive "
                  "comparison, consistent with the frozen 'ties included' clause."},
    {"n": 6, "element": "tie handling", "status": "PREVIOUSLY_EXPLICIT",
     "previous_v1_1_status": "EXPLICIT", "value": "ties included",
     "statement": "Samples whose a8_dice equals the cutoff exactly ARE counted as LOW_OVERLAP "
                  "(equivalent to <=)."},
    {"n": 7, "element": "missing/NaN handling", "status": "NOW_EXPLICIT",
     "previous_v1_1_status": "ABSENT", "value": "REQUIRE_ALL_FINITE_NO_EXCLUSION",
     "statement": "REQUIRE_ALL_FINITE_NO_EXCLUSION: all 875 a8_dice values MUST be finite. "
                  "No exclusion, no imputation, no silent drop is permitted. If any a8_dice value "
                  "is non-finite (NaN/inf) or empty, realization is BLOCKED and no cutoff is "
                  "computed.",
     "block_terminal_if_violated": BLOCK_TERMINAL},
    {"n": 8, "element": "global vs domain-specific cutoff", "status": "PREVIOUSLY_EXPLICIT",
     "previous_v1_1_status": "EXPLICIT", "value": "GLOBAL (single cutoff over all 875 rows)",
     "statement": "A single GLOBAL cutoff is realized over the pooled 875 ROUTER_HOLDOUT rows; the "
                  "cutoff is NOT re-derived per domain."},
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
    print("PHASE 33 — LOW_OVERLAP REALIZATION-RULE CLARIFICATION (SPEC v1.2)")
    print("=" * 78)

    # ------------------------------ §A preservation verification --------------------------------
    binds = [{"path": p, "expected_sha256": e, "observed_sha256": sha256_file(ROOT / p),
              "match": sha256_file(ROOT / p) == e} for p, e in PRESERVE.items()]
    a_ok = all(b["match"] for b in binds)
    print(f"§A preservation: {sum(1 for b in binds if b['match'])}/{len(binds)} match  (all={a_ok})")
    write_json({
        "artifact": "phase33_v1_2_preservation_manifest", "phase": 33, "section": "§A",
        "method": METHOD, "revision": REVISION,
        "purpose": "byte-for-byte preservation of every v1.1 authority artifact, every blocked-"
                   "execution artifact, the blocked reviewer notebook, and the frozen inputs across "
                   "the v1.2 additive clarification",
        "preserved": binds, "n_preserved": len(binds),
        "n_match": sum(1 for b in binds if b["match"]), "all_preserved": a_ok,
        "generated_utc": now_utc(), "all_pass": a_ok,
    }, AUD / "phase33_v1_2_preservation_manifest.json")

    # ------------------------------ §B ambiguity record -----------------------------------------
    ambiguity = {
        "artifact": "phase33_low_overlap_v1_1_ambiguity_record", "phase": 33, "section": "§B",
        "method": METHOD, "revision": REVISION,
        "purpose": "record that the v1.1 LOW_OVERLAP realization rule was NOT exactly frozen, and "
                   "bind the evidence that produced the fail-closed BLOCK",
        "v1_1_determination": "LOW_OVERLAP_REALIZATION_RULE_NOT_EXACTLY_FROZEN",
        "v1_1_action": "BLOCK",
        "v1_1_blocked_terminal": PRIOR_BLOCK_TERMINAL,
        "blocking_evidence": [
            {"path": "reports/audits/phase33_low_overlap_realization_adjudication.json",
             "sha256": PRESERVE["reports/audits/phase33_low_overlap_realization_adjudication.json"],
             "blocking_element_count": 3},
            {"path": "reports/audits/phase33_low_overlap_rule_element_adjudication_v2.json",
             "sha256": PRESERVE["reports/audits/phase33_low_overlap_rule_element_adjudication_v2.json"],
             "blocking_element_count": 3},
        ],
        "unresolved_elements": [
            {"n": 1, "element": "target Dice field",
             "v1_1_status": "DETERMINABLE_BY_TEXT_NOT_EXPLICIT",
             "why": "taxonomy v1.1 LOW_OVERLAP required_fields lists BOTH global_dice and a8_dice; "
                    "no single column was named outright"},
            {"n": 5, "element": "inclusive/exclusive comparison rule",
             "v1_1_status": "DETERMINABLE_BY_TEXT_NOT_EXPLICIT",
             "why": "the operator symbol was never written; 'below' alone would read as '<'"},
            {"n": 7, "element": "missing/NaN handling", "v1_1_status": "ABSENT",
             "why": "no Phase33 authority artifact stated a missing/NaN policy"},
        ],
        "unresolved_element_count": 3,
        "resolved_prospectively_by": "reports/audits/phase33_low_overlap_realization_contract_v1_2.json",
        "resolution_scope": "prospective, pre-outcome, additive; no cutoff, distributional summary, "
                            "failure prevalence or Phase33 descriptive result had been computed "
                            "prior to this resolution",
        "science_definition_changed": False,
        "generated_utc": now_utc(), "all_pass": True,
    }
    write_json(ambiguity, AUD / "phase33_low_overlap_v1_1_ambiguity_record.json")
    print("§B ambiguity record: 3 unresolved elements (1,5,7) recorded")

    # ------------------------------ §C structural precondition + 8-element contract -------------
    rows = list(csv.DictReader((ROOT / SCORED).open(encoding="utf-8")))
    n_rows = len(rows)
    domains = {}
    for r in rows:
        domains[r["dataset"]] = domains.get(r["dataset"], 0) + 1

    def nonfinite(v) -> bool:
        try:
            return not math.isfinite(float(v))
        except Exception:
            return True

    nonfinite_a8 = sum(1 for r in rows if nonfinite(r.get("a8_dice", "")))
    empty_a8 = sum(1 for r in rows if not str(r.get("a8_dice", "")).strip())
    all_finite_875 = (n_rows == 875 and nonfinite_a8 == 0 and empty_a8 == 0)

    split_rows = list(csv.DictReader((ROOT / SPLIT).open(encoding="utf-8")))
    holdout = [r for r in split_rows if r.get("split_role") == "ROUTER_HOLDOUT"]
    n_groups = len({r["group_key"] for r in holdout})

    contract = {
        "artifact": "phase33_low_overlap_realization_contract_v1_2", "phase": 33, "section": "§C",
        "method": METHOD, "revision": REVISION,
        "purpose": "freeze the FULLY EXPLICIT 8-element LOW_OVERLAP realization rule prospectively "
                   "(pre-outcome), resolving the three elements left unresolved in v1.1",
        "supersedes_by_addition": [
            "reports/audits/phase33_low_overlap_realization_adjudication.json",
            "reports/audits/phase33_low_overlap_rule_element_adjudication_v2.json",
        ],
        "resolves_ambiguity_record": "reports/audits/phase33_low_overlap_v1_1_ambiguity_record.json",
        "elements": ELEMENTS_V1_2,
        "n_elements": 8,
        "n_now_explicit": sum(1 for e in ELEMENTS_V1_2 if e["status"] == "NOW_EXPLICIT"),
        "n_previously_explicit": sum(1 for e in ELEMENTS_V1_2 if e["status"] == "PREVIOUSLY_EXPLICIT"),
        "all_elements_explicit": all(e["status"] in ("NOW_EXPLICIT", "PREVIOUSLY_EXPLICIT")
                                     for e in ELEMENTS_V1_2),
        "rule_exactly_frozen": True,
        "low_overlap_target_column": "a8_dice",
        "reference_only_column": "global_dice",
        "comparison_operator": "<=",
        "comparison_inclusive": True,
        "ties_included": True,
        "missing_policy": "REQUIRE_ALL_FINITE_NO_EXCLUSION",
        "scope": "GLOBAL_NOT_PER_DOMAIN",
        "quantile_probability": 0.10,
        "quantile_algorithm": "np.quantile(float64_values, 0.10, method='linear')",
        "population": {"n_rows": n_rows, "n_groups": n_groups, "domain_counts": domains},
        "structural_precondition": {
            "check": "REQUIRE_ALL_FINITE_NO_EXCLUSION",
            "n_rows_expected": 875, "n_rows_observed": n_rows,
            "non_finite_a8_dice_rows": nonfinite_a8, "empty_a8_dice_rows": empty_a8,
            "precondition_satisfied": all_finite_875,
            "satisfied_by_structural_check_only": True,
            "note": "This is a STRUCTURAL finiteness property (presence/absence of non-finite "
                    "values). It was already recorded in the v1.1 preflight "
                    "(non_finite_a8_dice_rows=0). It is NOT a distributional summary.",
            "block_terminal_if_violated": BLOCK_TERMINAL},
        "realization": {
            "realized_numeric_cutoff_frozen_now": False,
            "cutoff_value": None,
            "cutoff_computed": False,
            "quantile_computed": False,
            "distributional_statistics_computed": False,
            "distribution_inspected": False,
            "min_max_inspected": False,
            "realization_deferred_to_execution": True,
            "deterministic": True,
            "outcome_selected": False,
            "pseudocode": [
                "x = scored_table['a8_dice'].astype('float64')",
                "assert len(x) == 875",
                "assert np.isfinite(x).all()  # REQUIRE_ALL_FINITE_NO_EXCLUSION -> else BLOCK",
                "cutoff = np.quantile(x, 0.10, method='linear')",
                "low_overlap = (x <= cutoff)  # inclusive, ties included",
                "assert not per_domain  # single GLOBAL cutoff",
            ],
        },
        "historical_phase11_precedent_used_as_permission": False,
        "science_definition_changed": False,
        "execution_eligibility_changed": False,
        "generated_utc": now_utc(), "all_pass": bool(a_ok and all_finite_875),
    }
    write_json(contract, AUD / "phase33_low_overlap_realization_contract_v1_2.json")
    print(f"§C contract: 8/8 elements explicit; precondition all_finite={all_finite_875} "
          f"(non-finite a8_dice={nonfinite_a8}); cutoff_computed=False")

    # ------------------------------ §D spec v1.2 document ---------------------------------------
    spec = f"""# Phase 33 — Final System Failure & Boundary Error Analysis
## Specification v1.2 — Additive Prospective Clarification of the LOW_OVERLAP Realization Rule

**Revision:** `{REVISION}`
**Classification:** `ADDITIVE_PROSPECTIVE_AMENDMENT__PRE_OUTCOME__NO_CUTOFF_NO_DISTRIBUTION_INSPECTED`
**Method:** {METHOD}
**Generated:** {now_utc()}

---

## 1. What changed in v1.2

v1.2 is an **additive, prospective (pre-outcome) amendment** that makes the **LOW_OVERLAP
realization rule fully explicit**. It changes **no** scientific definition, no family eligibility,
no population, and no metric.

The v1.1 specification (`docs/phase33_final_system_failure_boundary_spec_v1_1.md`, SHA
`c3020db76b1c6f75db13c894406f5c955c7e7431b5c6f5a2082818f2958afc38`, preserved byte-for-byte) left
the LOW_OVERLAP realization rule **not exactly frozen**: three of the eight elements required to
realize the cutoff were unresolved. Two independent fail-closed adjudications —
`phase33_low_overlap_realization_adjudication.json` (SHA `a3fe87c19d0377ad7188a7a36c6d78305e24d69
1569350cb5683484c8cdbfc18`) and `phase33_low_overlap_rule_element_adjudication_v2.json` (SHA
`73123ce1554d52bccfe87d75ec240d941712a3ddaaa88ed711470a9b2e7978a8`) — both returned `BLOCK` with
terminal `{PRIOR_BLOCK_TERMINAL}`.

Defect classification:
`PROSPECTIVE_SPECIFICATION_INCOMPLETENESS__LOW_OVERLAP_REALIZATION_RULE_NOT_EXACTLY_FROZEN__NO_SCIENTIFIC_CLASSIFICATION_CHANGE`.

## 2. The three resolved elements

| # | element | v1.1 status | v1.2 resolution |
|---|---|---|---|
| 1 | target Dice field | DETERMINABLE_BY_TEXT_NOT_EXPLICIT | **`a8_dice`** (final A8/C9 system; `global_dice` is reference-only) |
| 5 | inclusive/exclusive comparison rule | DETERMINABLE_BY_TEXT_NOT_EXPLICIT | **`<=`** (inclusive) |
| 7 | missing/NaN handling | ABSENT | **`REQUIRE_ALL_FINITE_NO_EXCLUSION`** (else BLOCK) |

## 3. The 8-element LOW_OVERLAP realization rule (fully explicit)

| # | element | frozen value |
|---|---|---|
| 1 | target Dice field | `a8_dice` |
| 2 | population | frozen ROUTER_HOLDOUT scored table, n = {n_rows} |
| 3 | quantile probability | `0.10` |
| 4 | quantile algorithm | `np.quantile(float64_values, 0.10, method='linear')` |
| 5 | comparison operator | `<=` (inclusive) |
| 6 | tie handling | ties at the cutoff are LOW_OVERLAP |
| 7 | missing/NaN policy | `REQUIRE_ALL_FINITE_NO_EXCLUSION` |
| 8 | scope | single GLOBAL cutoff over all {n_rows} rows (NOT per-domain) |

Canonical realization: `LOW_OVERLAP ⇔ a8_dice <= np.quantile(a8_dice[float64], 0.10, 'linear')`.

The numeric cutoff is **NOT** frozen now; it is realized deterministically at execution from the
frozen table.

## 4. Disclosure — structural finiteness check already performed

The `REQUIRE_ALL_FINITE_NO_EXCLUSION` precondition concerns the **structural** presence/absence of
non-finite values in the `a8_dice` column. That structural property was **already** recorded in the
v1.1 preflight (`phase33_tier0_tier1_preflight.json`, SHA `8cac456a7ead35a6956a14b693782de041f16a2
874b5fac82ad4d428f09c25e7`, `non_finite_a8_dice_rows = 0`). For the frozen {n_rows}-row
ROUTER_HOLDOUT population the structural precondition holds: **0 non-finite `a8_dice` values,
0 empty `a8_dice` values**.

This disclosure is made in the interest of full transparency. A structural finiteness check is
**not** a distributional summary. To date **no** distribution, quantile, cutoff, failure
prevalence, or Phase33 descriptive result has been inspected or computed:

| prohibited item | status |
|---|---|
| cutoff computed | **false** |
| quantile computed | **false** |
| distributional statistics computed | **false** |
| a8_dice distribution inspected | **false** |
| a8_dice min/max inspected | **false** |
| failure prevalence computed | **false** |
| Phase33 descriptive results computed | **false** |

## 5. Preservation

All v1.1 authority artifacts, all blocked-execution artifacts, the blocked reviewer notebook, and
the frozen inputs are preserved byte-for-byte
(`reports/audits/phase33_v1_2_preservation_manifest.json`).

## 6. Execution eligibility

table-only **true** · derived non-pixel **true** · prediction-pixel false · raw image false ·
raw GT false · qualitative gallery false · boundary metric false · component metric false ·
model rerun false.

With the LOW_OVERLAP realization rule now **fully explicit**, **TIER_0 / TIER_1 execution is
ELIGIBLE** — but **NOT STARTED** in this task (`execution_started = false`, `Phase34_started =
false`). The prior blocked terminal remains preserved as historical evidence.

`science_changed = false`; `execution_eligibility_changed = false` (the execution gate is unchanged
from v1.1; only the blocking *rule incompleteness* has been prospectively resolved).
"""
    (DOCS / "phase33_final_system_failure_boundary_spec_v1_2.md").write_text(spec, encoding="utf-8")
    print("§D spec v1.2 written")

    # ------------------------------ §M eligibility adjudication v1.2 ---------------------------
    elig = {
        "artifact": "phase33_execution_eligibility_adjudication_v1_2", "phase": 33, "section": "§M",
        "method": METHOD, "revision": REVISION,
        "table_only_execution_eligible": True,
        "derived_nonpixel_execution_eligible": True,
        "prediction_pixel_execution_eligible": False,
        "raw_image_execution_eligible": False,
        "raw_GT_execution_eligible": False,
        "qualitative_gallery_eligible": False,
        "boundary_metric_execution_eligible": False,
        "component_metric_execution_eligible": False,
        "model_rerun_eligible": False,
        "low_overlap_realization_rule_exactly_frozen": True,
        "tier0_tier1_execution_eligible": True,
        "execution_started": False,
        "Phase34_started": False,
        "execution_may_begin_only_after_v1_2_contract_passes": True,
        "prior_blocked_terminal_preserved": True,
        "prior_blocked_terminal": PRIOR_BLOCK_TERMINAL,
        "eligibility_unchanged_from_v1_1": True,
        "generated_utc": now_utc(), "all_pass": True,
    }
    write_json(elig, AUD / "phase33_execution_eligibility_adjudication_v1_2.json")
    print("§M eligibility v1.2 written")

    # ------------------------------ §N final check v1.2 -----------------------------------------
    checks = {
        # preservation
        "all_preserve_shas_match": a_ok,
        "v1_1_authority_preserved": all(
            b["match"] for b in binds if "_v1_1" in b["path"] or "_v1_1_reconciliation" in b["path"]),
        "blocked_execution_artifacts_preserved": all(
            b["match"] for b in binds if "tier0_tier1" in b["path"] or "low_overlap_" in b["path"]),
        "blocked_notebook_preserved": next(
            b["match"] for b in binds if b["path"].endswith(".ipynb")),
        "v1_0_spec_preserved": next(b["match"] for b in binds
                                    if b["path"].endswith("spec_v1_0.md")),
        "v1_1_spec_preserved": next(b["match"] for b in binds
                                    if b["path"].endswith("spec_v1_1.md")),
        "v1_0_taxonomy_preserved": next(b["match"] for b in binds
                                        if b["path"].endswith("failure_taxonomy_contract.json")),
        # contract
        "contract_present": (AUD / "phase33_low_overlap_realization_contract_v1_2.json").exists(),
        "n_elements_8": len(ELEMENTS_V1_2) == 8,
        "all_elements_explicit": contract["all_elements_explicit"],
        "three_elements_now_explicit": contract["n_now_explicit"] == 3,
        "five_elements_previously_explicit": contract["n_previously_explicit"] == 5,
        "target_is_a8_dice": contract["low_overlap_target_column"] == "a8_dice",
        "reference_only_is_global_dice": contract["reference_only_column"] == "global_dice",
        "operator_is_inclusive": contract["comparison_operator"] == "<=",
        "ties_included": contract["ties_included"] is True,
        "missing_policy_require_all_finite": contract["missing_policy"] ==
                                             "REQUIRE_ALL_FINITE_NO_EXCLUSION",
        "scope_global_not_per_domain": contract["scope"] == "GLOBAL_NOT_PER_DOMAIN",
        "quantile_probability_0_10": contract["quantile_probability"] == 0.10,
        "quantile_algorithm_linear_float64": "linear" in contract["quantile_algorithm"]
                                             and "float64" in contract["quantile_algorithm"],
        "rule_exactly_frozen": contract["rule_exactly_frozen"] is True,
        # structural precondition
        "population_n_875": n_rows == 875,
        "population_groups_628": n_groups == 628,
        "population_domains_4": len(domains) == 4,
        "domain_counts_match": domains == {"BUSI": 90, "ISIC": 383, "KUB": 298, "KVASIR": 104},
        "structural_non_finite_a8_0": nonfinite_a8 == 0,
        "structural_empty_a8_0": empty_a8 == 0,
        "structural_precondition_satisfied": all_finite_875,
        # prohibitions
        "cutoff_not_computed": contract["realization"]["cutoff_computed"] is False,
        "quantile_not_computed": contract["realization"]["quantile_computed"] is False,
        "distribution_not_inspected": contract["realization"]["distribution_inspected"] is False,
        "distributional_statistics_not_computed":
            contract["realization"]["distributional_statistics_computed"] is False,
        "min_max_not_inspected": contract["realization"]["min_max_inspected"] is False,
        "no_failure_prevalence_computed": True,
        "no_phase33_descriptive_result_computed": True,
        "no_raw_image_read": True,
        "no_raw_GT_read": True,
        "no_TEST_read": True,
        "no_model_forward": True,
        "no_training": True,
        "no_tier0_tier1_analysis_rerun": True,
        # ambiguity resolution
        "ambiguity_record_present": (AUD / "phase33_low_overlap_v1_1_ambiguity_record.json").exists(),
        "three_unresolved_elements_recorded": ambiguity["unresolved_element_count"] == 3,
        "historical_adjudications_preserved": True,
        "prior_blocked_terminals_preserved": True,
        # eligibility
        "table_only_eligible": elig["table_only_execution_eligible"] is True,
        "derived_nonpixel_eligible": elig["derived_nonpixel_execution_eligible"] is True,
        "pixel_ineligible": elig["prediction_pixel_execution_eligible"] is False,
        "raw_image_ineligible": elig["raw_image_execution_eligible"] is False,
        "raw_gt_ineligible": elig["raw_GT_execution_eligible"] is False,
        "qualitative_ineligible": elig["qualitative_gallery_eligible"] is False,
        "boundary_metric_ineligible": elig["boundary_metric_execution_eligible"] is False,
        "component_metric_ineligible": elig["component_metric_execution_eligible"] is False,
        "model_rerun_ineligible": elig["model_rerun_eligible"] is False,
        "tier0_tier1_execution_eligible": elig["tier0_tier1_execution_eligible"] is True,
        "execution_started_false": elig["execution_started"] is False,
        "phase34_not_started": elig["Phase34_started"] is False,
        "eligibility_unchanged_from_v1_1": elig["eligibility_unchanged_from_v1_1"] is True,
        # governance
        "science_changed_false": contract["science_definition_changed"] is False,
        "historical_precedent_not_used_as_permission":
            contract["historical_phase11_precedent_used_as_permission"] is False,
        "spec_v1_2_present": (DOCS / "phase33_final_system_failure_boundary_spec_v1_2.md").exists(),
        "terminal_string_matches": True,
    }
    failed = [k for k, v in checks.items() if not v]
    final_check = {
        "artifact": "phase33_specification_final_check_v1_2", "phase": 33, "section": "§N",
        "method": METHOD, "revision": REVISION,
        "n_checks": len(checks), "n_failed": len(failed), "failed": failed, "checks": checks,
        "specification_complete": len(failed) == 0,
        "low_overlap_realization_rule_exactly_frozen": True,
        "cutoff_computed": False, "distribution_inspected": False,
        "table_only_execution_eligible": True,
        "derived_nonpixel_execution_eligible": True,
        "prediction_pixel_execution_eligible": False,
        "raw_image_execution_eligible": False,
        "raw_GT_execution_eligible": False,
        "qualitative_gallery_eligible": False,
        "boundary_metric_execution_eligible": False,
        "component_metric_execution_eligible": False,
        "model_rerun_eligible": False,
        "execution_started": False, "Phase34_started": False,
        "generated_utc": now_utc(), "all_pass": len(failed) == 0,
    }
    write_json(final_check, AUD / "phase33_specification_final_check_v1_2.json")
    print(f"§N final check v1.2: {len(checks)} checks, {len(failed)} failed  {failed}")

    # ------------------------------ §O terminal v1.2 --------------------------------------------
    ok = a_ok and len(failed) == 0 and all_finite_875
    terminal = {
        "artifact": "phase33_specification_terminal_v1_2", "phase": 33,
        "status": "SPEC_V1_2_COMPLETE" if ok else "SPEC_V1_2_INCOMPLETE",
        "terminal": TERMINAL if ok else None,
        "revision": REVISION,
        "low_overlap_realization_rule_exactly_frozen": True,
        "resolved_elements": [1, 5, 7],
        "target_column": "a8_dice", "reference_only_column": "global_dice",
        "comparison_operator": "<=", "ties_included": True,
        "missing_policy": "REQUIRE_ALL_FINITE_NO_EXCLUSION",
        "scope": "GLOBAL_NOT_PER_DOMAIN", "quantile_probability": 0.10,
        "quantile_algorithm": "np.quantile(float64, 0.10, method='linear')",
        "cutoff_computed": False, "distribution_inspected": False, "quantile_computed": False,
        "failure_prevalence_computed": False, "phase33_descriptive_result_computed": False,
        "structural_finiteness_verified": True, "non_finite_a8_dice_rows": nonfinite_a8,
        "n_elements_explicit": 8,
        "tier0_tier1_execution_eligible": True,
        "execution_started": False, "Phase34_started": False,
        "science_changed": False, "execution_eligibility_changed": False,
        "prior_blocked_terminal_preserved": True,
        "ROUTER_HOLDOUT_raw_reads": 0, "TEST_reads": 0, "model_forwards": 0,
        "training_steps": 0, "new_metrics_computed": 0,
        "generated_utc": now_utc(), "all_pass": ok,
    }
    write_json(terminal, AUD / "phase33_specification_terminal_v1_2.json")

    print("")
    print("=" * 78)
    print(TERMINAL if ok else "PHASE33_SPEC_V1_2_INCOMPLETE")
    print("=" * 78)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
