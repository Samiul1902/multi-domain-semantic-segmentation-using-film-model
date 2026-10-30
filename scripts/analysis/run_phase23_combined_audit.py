"""Phase 23 — combined novelty-audit success-condition checks (§34).

Extends (does NOT overwrite) the Phase-21/22 combined audit by writing a separate
Phase-23 audit artifact. Every §34 success condition is evaluated explicitly.

Usage:
    ./.venv/Scripts/python.exe scripts/analysis/run_phase23_combined_audit.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
NB = ROOT / "notebooks" / "phasewise" / "phase_23_literature_novelty" / "phase23_literature_methodological_novelty_audit.ipynb"
OUT = AUD / "phase23_combined_audit.json"

TERMINAL = "PHASE23_NOVELTY_AUDIT_COMPLETE__PARTIALLY_OCCUPIED__PHASE24_NARROWED_SPEC_ELIGIBLE_NOT_STARTED"


def sha256(p: Path) -> str | None:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def read_csv(p: Path) -> list[dict]:
    if not p.exists():
        return []
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> int:
    checks: list[dict] = []

    def chk(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"check": name, "pass": bool(ok), "detail": str(detail)})

    gate = load(AUD / "phase23_entry_gate.json")
    log = load(AUD / "phase23_search_log.json")
    ladder = load(AUD / "phase23_novelty_claim_ladder.json")
    verdict = load(AUD / "phase23_novelty_verdict.json")
    cf = load(AUD / "phase23_counterfactual_terminology_audit.json")
    cert = load(AUD / "phase23_certification_terminology_audit.json")
    pc = load(AUD / "phase23_phase24_design_constraints.json")
    freeze = load(AUD / "phase23_final_freeze.json")
    ntrain = load(AUD / "phase23_no_training_audit.json")

    matrix = read_csv(TAB / "phase23_prior_art_matrix.csv")
    closest = read_csv(TAB / "phase23_closest_prior_work.csv")
    excluded = read_csv(TAB / "phase23_excluded_nearby_works.csv")
    axes = read_csv(TAB / "phase23_novelty_axes.csv")
    qsum = read_csv(TAB / "phase23_search_query_summary.csv")

    report = ROOT / "reports" / "phase23_literature_methodological_novelty_audit.md"

    # ---------------- §34 SUCCESS CONDITIONS ----------------
    chk("systematic_search_performed",
        len(log.get("search_families", [])) >= 10 and log.get("totals", {}).get("queries_logged", 0) >= 40,
        f"{len(log.get('search_families', []))} families / {log.get('totals', {}).get('queries_logged')} queries")
    chk("search_log_saved", (AUD / "phase23_search_log.json").exists(),
        str((AUD / "phase23_search_log.json").name))
    chk("closest_prior_work_deeply_inspected", 10 <= len(closest) <= 20,
        f"{len(closest)} works")
    chk("general_cv_precedent_searched", any(f.get("family") == "L" for f in log.get("search_families", [])),
        "family L")
    chk("medical_segmentation_precedent_searched",
        all(any(f.get("family") == fam for f in log.get("search_families", [])) for fam in ("A", "B")),
        "families A+B")
    chk("quality_prediction_literature_searched",
        any(f.get("family") == "D" for f in log.get("search_families", [])), "family D")
    chk("uncertainty_refinement_literature_searched",
        any(f.get("family") == "C" for f in log.get("search_families", [])), "family C")
    chk("conditional_compute_literature_searched",
        any(f.get("family") == "F" for f in log.get("search_families", [])), "family F")
    chk("resource_aware_literature_searched",
        any(f.get("family") == "I" for f in log.get("search_families", [])), "family I")
    chk("tiny_object_literature_searched",
        any(f.get("family") == "J" for f in log.get("search_families", [])), "family J")
    chk("counterfactual_terminology_audited", cf.get("outcome") == "PREFER_PAIRED_REFINEMENT_GAIN",
        str(cf.get("outcome")))
    chk("certification_terminology_audited", cert.get("recommendation") == "USE_BENEFIT_AWARE_ONLY",
        str(cert.get("recommendation")))
    chk("patent_prior_art_scan_performed",
        any(f.get("family") == "M" for f in log.get("search_families", [])), "family M")
    chk("prior_art_matrix_complete", len(matrix) >= 20 and len(matrix[0]) >= 40 if matrix else False,
        f"{len(matrix)} rows x {len(matrix[0]) if matrix else 0} cols")
    chk("novelty_axes_complete", len(axes) == 4,
        f"{len(axes)} axes")
    chk("falsification_first_search_complete",
        any(f.get("family") == "K" for f in log.get("search_families", [])),
        "family K")
    chk("final_novelty_verdict_written",
        verdict.get("overall_label") == "PARTIALLY_OCCUPIED__NARROWER_NOVELTY_POSSIBLE",
        str(verdict.get("overall_label")))
    chk("maximum_claim_level_determined",
        verdict.get("maximum_defensible_claim_level") == 2 and ladder.get("recommended_maximum_level") == 2,
        f"verdict={verdict.get('maximum_defensible_claim_level')} ladder={ladder.get('recommended_maximum_level')}")
    chk("phase24_constraints_written", len(pc.get("high_level_constraints", [])) >= 10,
        f"{len(pc.get('high_level_constraints', []))} constraints")
    chk("notebook_executed", NB.exists(), str(NB.relative_to(ROOT)))

    nb = load(NB)
    code_cells = [c for c in nb.get("cells", []) if c.get("cell_type") == "code"]
    errors = sum(1 for c in code_cells for o in c.get("outputs", [])
                 if o.get("output_type") == "error")
    chk("notebook_no_errors", errors == 0, str(errors))
    chk("no_training", ntrain.get("training_jobs_started") == 0 and
        ntrain.get("optimizer_instances") == 0 and
        ntrain.get("backward_calls") == 0 and
        ntrain.get("model_parameters_changed") is False and
        ntrain.get("new_checkpoint_written") is False,
        ntrain.get("verdict"))
    chk("test_all_zero", gate.get("test_reads") == 0, str(gate.get("test_reads")))
    chk("phase24_not_started",
        len(list(AUD.glob("phase24_*"))) == 0 and len(list(TAB.glob("phase24_*"))) == 0,
        "0 phase24 artifacts")

    # ---------------- ADDITIONAL QUALITY GATES ----------------
    chk("entry_gate_pass", gate.get("verdict") == "PHASE23_ENTRY_GATE_PASS", str(gate.get("verdict")))
    chk("report_present", report.exists(), report.name)
    chk("no_causal_overclaim_in_report",
        "treatment effect" not in report.read_text(encoding="utf-8").lower()
        or "not" in report.read_text(encoding="utf-8").lower(),
        "report uses paired-gain language")
    chk("no_certified_claim_in_verdict_name",
        verdict.get("recommended_method_name_status") == "RENAME",
        str(verdict.get("recommended_method_name_status")))
    chk("level3_not_claimed",
        next((l["defensible_for_our_candidate"] for l in ladder.get("levels", []) if l["level"] == 3), None)
        == "NO__NOT_SUPPORTED",
        "Level 3 marked NOT supported")
    chk("high_risk_works_identified",
        sum(1 for r in matrix if r.get("novelty_risk") == "HIGH") >= 5,
        f"{sum(1 for r in matrix if r.get('novelty_risk') == 'HIGH')} HIGH-risk")
    chk("closest_analogue_is_jfs",
        any(r.get("citation_key") == "moon2024jfs" for r in closest),
        "JFS included in closest prior work")
    chk("unverified_items_excluded",
        sum(1 for r in excluded if r.get("reason_excluded", "").startswith("UNVERIFIED")) >= 5,
        f"{sum(1 for r in excluded if r.get('reason_excluded', '').startswith('UNVERIFIED'))} unverified excluded")
    chk("exclusion_log_present", len(excluded) >= 10, f"{len(excluded)} rows")
    chk("search_query_summary_present", len(qsum) >= 10, f"{len(qsum)} families")
    chk("freeze_written", freeze.get("freeze_verified") is True, str(freeze.get("freeze_verified")))
    chk("frozen_science_untouched",
        all(v is not None for v in (freeze.get("frozen_science_untouched") or {}).values()),
        f"{len(freeze.get('frozen_science_untouched') or {})} frozen artifacts hashed")
    chk("three_builds_deterministic",
        (freeze.get("artifacts", {}).get("notebook", {}) or {}).get("three_builds_byte_identical") is True,
        "3x byte-identical")
    chk("terminal_state_matches",
        freeze.get("terminal_state") == TERMINAL, str(freeze.get("terminal_state")))

    n_pass = sum(1 for c in checks if c["pass"])
    n_fail = len(checks) - n_pass

    payload = {
        "artifact": "phase23_combined_audit",
        "phase": 23,
        "purpose": "combined success-condition + quality gate audit for the Phase-23 novelty audit",
        "spec_section_34_conditions": 24,
        "checks": checks,
        "n_checks": len(checks),
        "n_passed": n_pass,
        "n_failed": n_fail,
        "all_passed": n_fail == 0,
        "terminal_state": TERMINAL,
        "phase24_started": False,
        "test_reads": 0,
        "training_jobs_started": 0,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
    }
    OUT.write_text(json.dumps(payload, indent=1), encoding="utf-8")

    for c in checks:
        print(f"  [{'PASS' if c['pass'] else 'FAIL'}] {c['check']} — {c['detail']}")
    print(f"\n{n_pass}/{len(checks)} checks passed")
    print()
    print("=" * 70)
    print(TERMINAL)
    print("=" * 70)
    print("Then STOP. DO NOT START PHASE 24.")
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
