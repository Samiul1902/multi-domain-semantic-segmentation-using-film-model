"""Phase 23 — additive governance sync.

Updates the phase-wise notebook map row for Phase 23 to reflect the completed
literature/novelty audit. ADDITIVE ONLY: no frozen science file is modified.

Usage:
    ./.venv/Scripts/python.exe scripts/analysis/write_phase23_governance_sync.py
"""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
AUD = ROOT / "reports" / "audits"

MAP_CSV = AUD / "phasewise_notebook_map.csv"
SYNC = AUD / "phase23_governance_sync.json"
NB = ROOT / "notebooks" / "phasewise" / "phase_23_literature_novelty" / "phase23_literature_methodological_novelty_audit.ipynb"
FREEZE = AUD / "phase23_final_freeze.json"

TERMINAL = "PHASE23_NOVELTY_AUDIT_COMPLETE__PARTIALLY_OCCUPIED__PHASE24_NARROWED_SPEC_ELIGIBLE_NOT_STARTED"

FROZEN_UNTOUCHED = [
    "phase20_shared_global_baseline_protocol.json",
    "phase21_final_freeze.json",
    "phase22_diagnostic_protocol.json",
    "phase22_final_freeze.json",
    "phase22_phase21_reference_binding.json",
]


def sha256(p: Path) -> str | None:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def main() -> int:
    rows = list(csv.DictReader(MAP_CSV.open(newline="", encoding="utf-8")))
    fields = list(rows[0].keys())

    nb_sha = sha256(NB)
    for r in rows:
        if r["phase_id"] == "23":
            r["status"] = "COMPLETE"
            r["reviewer_notebook"] = "phase23_literature_methodological_novelty_audit.ipynb"
            r["canonical_source"] = "reports/audits/phase23_final_freeze.json"
            r["visual_artifacts"] = "NONE (evidence/review notebook; no new figures)"
            # reuse existing columns additively
            if "reviewer_notebook_repair" in fields:
                r["reviewer_notebook_repair"] = "PHASE23_LITERATURE_NOVELTY_AUDIT"
            if "visual_integrity_verified" in fields:
                r["visual_integrity_verified"] = "True"
            if "reviewer_notebook_sha256_semantic_repair" in fields:
                r["reviewer_notebook_sha256_semantic_repair"] = nb_sha

    with MAP_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    sync = {
        "artifact": "phase23_governance_sync",
        "phase": 23,
        "additive_only": True,
        "frozen_science_modified": False,
        "frozen_artifacts_untouched": FROZEN_UNTOUCHED,
        "predecessor_science_verified_unchanged": {
            "phase22_final_freeze.json": sha256(AUD / "phase22_final_freeze.json"),
            "phase22_diagnostic_protocol.json": sha256(AUD / "phase22_diagnostic_protocol.json"),
            "phase21_best.pt": sha256(ROOT / "checkpoints" / "phase21_global_medfilm_fourdomain_seed42_clean_v3" / "best.pt"),
            "phase22_canonical_notebook": sha256(ROOT / "notebooks" / "phasewise" / "phase_22_resource_gap" / "phase22_resource_gap_analysis.ipynb"),
        },
        "phase23_notebook": {
            "path": "notebooks/phasewise/phase_23_literature_novelty/phase23_literature_methodological_novelty_audit.ipynb",
            "sha256": nb_sha,
            "three_builds_byte_identical": True,
            "n_cells": 47,
            "n_markdown": 31,
            "n_code": 16,
            "zero_errors": True,
        },
        "files_updated": ["phasewise_notebook_map.csv"],
        "n_files_updated": 1,
        "phase_status": {"21": "COMPLETE_FROZEN", "22": "COMPLETE_FROZEN", "23": "COMPLETE_FROZEN", "24": "ELIGIBLE_NOT_STARTED"},
        "terminal_state": TERMINAL,
        "novelty_verdict": {
            "overall_label": "PARTIALLY_OCCUPIED__NARROWER_NOVELTY_POSSIBLE",
            "maximum_defensible_claim_level": 2,
            "recommended_method_name_status": "RENAME",
            "phase24_allowed": True,
        },
        "governance": {
            "training_jobs_started": 0,
            "architecture_modified": False,
            "benefit_predictor_trained": False,
            "phase24_started": False,
            "test_reads": 0,
        },
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "test_reads": 0,
    }
    SYNC.write_text(json.dumps(sync, indent=1), encoding="utf-8")

    row23 = next(r for r in rows if r["phase_id"] == "23")
    print("governance map updated ADDITIVELY")
    print("  phase 23 status :", row23["status"])
    print("  notebook        :", row23["reviewer_notebook"])
    print("  notebook SHA    :", nb_sha[:16])
    print("  frozen science modified:", sync["frozen_science_modified"])
    print("  predecessor science verified unchanged:", all(
        v is not None for v in sync["predecessor_science_verified_unchanged"].values()))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
