#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 — D29 V1.10 FROZEN VALIDATOR SOURCE AVAILABILITY / PROVENANCE RECORD.

HONEST RECORD.  The work order that commissioned v1.11 asserted that the frozen
v1.10 unit source was MISSING from the workspace.  An independent inspection at
the time of this record shows the OPPOSITE: the exact source named by the order
is PRESENT on disk and its SHA-256 EQUALS the exact frozen value the order cites
AND the value bound by the v1.10 preexecution freeze.

Consequently this record does NOT claim the artifact is missing.  It records the
truthful availability state, flags the premise discrepancy, and confirms that
v1.10 is NOT reconstructed or rewritten.

NO torch.  NO model.  NO protected read.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

UNIT_V1_10 = ROOT / "scripts/analysis/phase36_robustness_unit_v1_10.py"
FREEZE_V1_10 = ROOT / "reports/audits/phase36_preexecution_source_freeze_v1_10.json"

# The exact SHA the v1.10 freeze bound AND the work order cites.
BOUND_UNIT_V1_10_SHA = "9b880c92469e7daca8f6563e64bf2e2e712d4eb8ac304298fbb52f89ab87c329"


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main() -> int:
    present = UNIT_V1_10.exists()
    observed = sha(UNIT_V1_10) if present else None
    bound = None
    freeze_says = None
    if FREEZE_V1_10.exists():
        fr = json.loads(FREEZE_V1_10.read_text(encoding="utf-8"))
        fs = fr.get("frozen_sources", {})
        freeze_says = fs.get("scripts/analysis/phase36_robustness_unit_v1_10.py")
    bound = freeze_says or BOUND_UNIT_V1_10_SHA

    sha_matches_bound = bool(present and observed == bound)
    sha_matches_order = bool(present and observed == BOUND_UNIT_V1_10_SHA)

    # Long-ish read only to confirm it parses as a real suite (no execution).
    parses = False
    n_checks = 0
    n_lines = 0
    if present:
        import ast
        src = UNIT_V1_10.read_text(encoding="utf-8")
        n_lines = len(src.splitlines())
        try:
            tree = ast.parse(src)
            parses = True
            n_checks = sum(
                1 for n in ast.walk(tree)
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                and n.func.id == "check")
        except SyntaxError:
            parses = False

    if present and sha_matches_bound:
        availability = "PRESENT_SHA_VERIFIED_MATCHES_FREEZE"
        defect_applicable = False
        honest_note = ("The v1.10 frozen validator source IS PRESENT and byte-matches "
                       "its own freeze binding.  D29 'missing' is NOT applicable to "
                       "this workspace state; recording the true availability instead "
                       "of fabricating a missing-artifact defect.")
    elif not present:
        availability = "MISSING"
        defect_applicable = True
        honest_note = ("The v1.10 frozen validator source is absent; the work-order "
                       "premise is TRUE for this workspace state.")
    else:
        availability = "PRESENT_BUT_SHA_MISMATCH"
        defect_applicable = True
        honest_note = ("The named path exists but its bytes do NOT match the frozen "
                       "v1.10 binding; the frozen source is effectively unavailable "
                       "under its original identity.")

    record = {
        "artifact": "phase36_v1_10_frozen_validator_availability_provenance",
        "phase": 36,
        "method": "RA-MedFiLM-BARR",
        "revision": "ra_medfilm_barr_phase36_robustness_v1_11",
        "type": "HISTORICAL_AVAILABILITY_PROVENANCE_RECORD",
        "defect_id": "D29_V1_10_FROZEN_VALIDATOR_SOURCE_MISSING",
        "defect_applicable_to_this_workspace": bool(defect_applicable),
        "work_order_premise": "v1.10 unit source MISSING from workspace",
        "independent_inspection_result": availability,
        "historical_v1_10_freeze_existed": bool(FREEZE_V1_10.exists()),
        "freeze_bound_unit_sha256": bound,
        "work_order_cited_unit_sha256": BOUND_UNIT_V1_10_SHA,
        "unit_source_path": "scripts/analysis/phase36_robustness_unit_v1_10.py",
        "unit_source_present_on_disk": bool(present),
        "unit_source_observed_sha256": observed,
        "unit_source_sha_matches_freeze_binding": bool(sha_matches_bound),
        "unit_source_sha_matches_work_order_value": bool(sha_matches_order),
        "unit_source_parses": bool(parses),
        "unit_source_lines": n_lines,
        "unit_source_check_calls": n_checks,
        "reconstructed_or_rewritten_by_v1_11": False,
        "v1_10_smoke_executed": False,
        "v1_10_science_executed": False,
        "v1_10_scientific_evidence": "NONE",
        "honest_note": honest_note,
        "premise_discrepancy_flagged": bool(present and sha_matches_bound),
        "governing_rule": ("A frozen contract whose wording is not unambiguous -> STOP "
                           "and record the ambiguity; never invent a rule, never "
                           "'repair' a non-defect.  Recording a false 'missing' defect "
                           "would itself be a provenance violation."),
        "action_taken": "Recorded truthful availability; did NOT recreate/rewrite v1.10; "
                        "proceeded to build an INDEPENDENT v1.11 validation suite.",
        "protected_population_read": False,
        "torch_imported": "torch" in sys.modules,
    }
    out = ROOT / "reports/audits/phase36_v1_10_frozen_validator_availability_provenance.json"
    out.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "availability": availability,
        "defect_applicable": defect_applicable,
        "present": present,
        "sha_matches_bound": sha_matches_bound,
        "lines": n_lines, "checks": n_checks,
    }, indent=1))
    raise SystemExit(0)


if __name__ == "__main__":
    raise SystemExit(main())
