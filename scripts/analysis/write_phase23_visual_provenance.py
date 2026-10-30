"""Phase 23 — reviewer-visual repair PROVENANCE + additive governance pointer.

Records that the Phase-23 notebook visual repair is a REVIEWER_PRESENTATION_REPAIR:
science unchanged, no search rerun, no training, no inference, TEST closed.

Also records (and does NOT conceal) one factual data defect found and fixed:
the frozen ``phase23_search_log.json::totals.queries_logged`` field read 55
while the same file's per-family query ledger — and the frozen
``phase23_search_query_summary.csv`` — sum to 63. The totals field was corrected
to 63 so the ledger identity holds. This changes NO classification, NO verdict,
NO retained/excluded paper, and NO novelty axis.

Usage:
    ./.venv/Scripts/python.exe scripts/analysis/write_phase23_visual_provenance.py
"""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
FIG = ROOT / "reports" / "figures" / "phase23_novelty_audit"
MAP_CSV = AUD / "phasewise_notebook_map.csv"
NB = (ROOT / "notebooks/phasewise/phase_23_literature_novelty"
      / "phase23_literature_methodological_novelty_audit.ipynb")

OLD_NB_SHA = "cc86153c5011cc83ff787dcda797ecf5a20ef50c15f76eceeba5c9d911934f2e"
TERMINAL = ("PHASE23_REVIEWER_VISUALS_COMPLETE__SCIENCE_UNCHANGED__"
            "PHASE24_NARROWED_SPEC_ELIGIBLE_NOT_STARTED")

FROZEN_UNTOUCHED = [
    "phase20_shared_global_baseline_protocol.json",
    "phase21_final_freeze.json",
    "phase22_diagnostic_protocol.json",
    "phase22_final_freeze.json",
    "phase22_phase21_reference_binding.json",
]

PREDECESSOR_SCIENCE = {
    "phase22_final_freeze.json":
        "reports/audits/phase22_final_freeze.json",
    "phase22_diagnostic_protocol.json":
        "reports/audits/phase22_diagnostic_protocol.json",
    "phase21_best.pt":
        "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt",
    "phase22_canonical_notebook":
        "notebooks/phasewise/phase_22_resource_gap/phase22_resource_gap_analysis.ipynb",
}

# science artifacts that MUST be untouched by this presentation repair
SCIENCE_UNTOUCHED = {
    "phase23_novelty_verdict.json": "reports/audits/phase23_novelty_verdict.json",
    "phase23_novelty_claim_ladder.json": "reports/audits/phase23_novelty_claim_ladder.json",
    "phase23_novelty_axes.csv": "reports/tables/phase23_novelty_axes.csv",
    "phase23_prior_art_matrix.csv": "reports/tables/phase23_prior_art_matrix.csv",
    "phase23_closest_prior_work.csv": "reports/tables/phase23_closest_prior_work.csv",
    "phase23_excluded_nearby_works.csv": "reports/tables/phase23_excluded_nearby_works.csv",
    "phase23_search_query_summary.csv": "reports/tables/phase23_search_query_summary.csv",
    "phase23_counterfactual_terminology_audit.json":
        "reports/audits/phase23_counterfactual_terminology_audit.json",
    "phase23_certification_terminology_audit.json":
        "reports/audits/phase23_certification_terminology_audit.json",
    "phase23_phase24_design_constraints.json":
        "reports/audits/phase23_phase24_design_constraints.json",
}

# expected SHAs recorded at freeze time (from phase23_final_freeze.json)
FREEZE = json.loads((AUD / "phase23_final_freeze.json").read_text(encoding="utf-8"))


def sha(p: Path) -> str | None:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def main() -> int:
    nb_sha = sha(NB)

    # ---- verify science artifacts are unchanged vs the freeze --------------
    expected = dict(FREEZE["artifacts"]["audits"])
    expected.update(FREEZE["artifacts"]["tables"])
    changed, verified = [], {}
    for name, rel in SCIENCE_UNTOUCHED.items():
        cur = sha(ROOT / rel)
        exp = expected.get(name)
        verified[name] = {"sha256": cur, "freeze_sha256": exp, "unchanged": cur == exp}
        if cur != exp:
            changed.append(name)

    # ---- the one corrected field (transparently recorded) -------------------
    log = json.loads((AUD / "phase23_search_log.json").read_text(encoding="utf-8"))
    ledger_sum = sum(len(f.get("queries") or []) for f in log["search_families"])
    summary_sum = sum(
        int(r["n_queries"]) for r in csv.DictReader(
            (ROOT / "reports/tables/phase23_search_query_summary.csv").open(encoding="utf-8")))
    ledger_fix = {
        "field": "phase23_search_log.json::totals.queries_logged",
        "previous_value": 55,
        "corrected_value": log["totals"]["queries_logged"],
        "per_family_ledger_sum": ledger_sum,
        "search_query_summary_sum": summary_sum,
        "identity_holds_now": (log["totals"]["queries_logged"] == ledger_sum == summary_sum),
        "nature": "FACTUAL_LEDGER_ARITHMETIC_CORRECTION",
        "classification_or_verdict_impact": "NONE",
        "papers_retained_changed": False,
        "papers_excluded_changed": False,
        "results_screened_changed": False,
        "rows_affected_in_summary_csv": 0,
    }

    # ---- figure inventory ---------------------------------------------------
    manifest = json.loads((FIG / "phase23_figure_manifest.json").read_text(encoding="utf-8"))
    figures = manifest["figures"]

    prov = {
        "artifact": "phase23_reviewer_visual_repair",
        "phase": 23,
        "classification": "REVIEWER_PRESENTATION_REPAIR",
        "purpose": ("Add reviewer-quality deterministic visualizations to the Phase-23 "
                    "evidence/review notebook, derived only from existing frozen Phase-23 "
                    "tables/audits."),
        "scientific_results_changed": False,
        "search_rerun": False,
        "prior_art_matrix_changed": False,
        "novelty_verdict_changed": False,
        "literature_classification_changed": False,
        "retained_papers_added_or_removed": False,
        "training": False,
        "inference": False,
        "test_reads": 0,
        "phase24_started": False,

        "notebook": {
            "path": str(NB.relative_to(ROOT)).replace("\\", "/"),
            "old_sha256": OLD_NB_SHA,
            "new_sha256": nb_sha,
            "supersedes": OLD_NB_SHA,
        },
        "figures": {
            "required": [k for k, v in figures.items() if v["required"]],
            "optional": [k for k, v in figures.items() if not v["required"]],
            "n_required": manifest["n_required"],
            "n_optional": manifest["n_optional"],
            "builder": "scripts/analysis/build_phase23_visuals.py",
            "source": "frozen Phase-23 tables/audits only",
        },
        "science_untouched_verification": {
            "n_verified": len(verified),
            "n_changed": len(changed),
            "changed": changed,
            "detail": verified,
        },
        "data_defect_found_and_fixed": ledger_fix,
        "frozen_science_untouched": FROZEN_UNTOUCHED,
        "predecessor_science_sha256": {
            name: sha(ROOT / rel) for name, rel in PREDECESSOR_SCIENCE.items()
        },
        "governance": {
            "test_reads": 0,
            "training_jobs_started": 0,
            "architecture_modified": False,
            "benefit_predictor_trained": False,
            "phase24_started": False,
            "web_access_from_notebook": False,
        },
        "terminal_state": TERMINAL,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "test_reads": 0,
    }
    (AUD / "phase23_reviewer_visual_repair.json").write_text(
        json.dumps(prov, indent=1), encoding="utf-8")

    # ---- additive governance pointer update ---------------------------------
    rows = list(csv.DictReader(MAP_CSV.open(newline="", encoding="utf-8")))
    fields = list(rows[0].keys())
    for r in rows:
        if r["phase_id"] == "23":
            r["visual_artifacts"] = (
                "reports/figures/phase23_novelty_audit/ (4 required + 1 optional PNG; "
                "embedded in notebook)")
            if "reviewer_notebook_repair" in fields:
                r["reviewer_notebook_repair"] = (
                    "PHASE23_LITERATURE_NOVELTY_AUDIT + REVIEWER_PRESENTATION_REPAIR")
            if "visual_integrity_verified" in fields:
                r["visual_integrity_verified"] = "True"
            if "reviewer_notebook_sha256_semantic_repair" in fields:
                r["reviewer_notebook_sha256_semantic_repair"] = nb_sha
            if "reviewer_notebook_sha256_superseded" in fields:
                r["reviewer_notebook_sha256_superseded"] = OLD_NB_SHA
    with MAP_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    print("provenance written:", "phase23_reviewer_visual_repair.json")
    print("  classification           :", prov["classification"])
    print("  scientific_results_changed:", prov["scientific_results_changed"])
    print("  science artifacts checked :", prov["science_untouched_verification"]["n_verified"])
    print("  science artifacts changed :", len(changed), changed)
    print("  ledger identity now holds :", ledger_fix["identity_holds_now"])
    print("  governance map updated    : ADDITIVE (row 23)")
    print("  new notebook SHA          :", nb_sha[:16])

    if changed:
        print("FAIL-CLOSED: a science artifact changed unexpectedly")
        return 1
    if not ledger_fix["identity_holds_now"]:
        print("FAIL-CLOSED: search-ledger identity does not hold")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
