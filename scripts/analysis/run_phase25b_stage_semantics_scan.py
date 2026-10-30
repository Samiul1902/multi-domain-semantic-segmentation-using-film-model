"""Phase 25B handoff-semantics repair -- repository stale-stage-label scan
(work-order section 6).

Searches CURRENT, non-historical project-control / Phase25B artifacts for stale
Phase25C stage labels, classifies each hit as:
    CURRENT_CANONICAL   -- mutable, must be corrected
    HISTORICAL_PROVENANCE -- frozen/immutable record, must NOT be rewritten
    UNRELATED           -- a false positive (list of prohibitions, etc.)

Requires current_canonical_stale_stage_labels == 0.

Writes reports/audits/phase25b_stage_semantics_repository_scan.json
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
UTC = datetime.now(timezone.utc).isoformat()

# Patterns that indicate the stale "Phase25C == router training / task embedding" semantics.
# NOTE: the repaired artifacts deliberately carry fields like
# ``phase25c_trains_router: false`` / ``phase25c_trains_task_embedding`` used as ASSERTIONS
# that 25C does NOT train; those are not stale labels (see NEGATION_OK below).
PATTERNS = [
    r"Phase\s*25C\s*\(router training\)",
    r"Phase\s*25C\s*\(benefit[-\s]router training\)",
    r"phase_25c_router_training",
    r"Phase\s*25C\s*MUST\s+append",
    r"Phase\s*25C\s+must\s+append",
    r"Phase25C\s+must\s+append",
    r"25C\s+router",
    r"Phase\s*25C\s*.*benefit\s*router\s*training",
    r"next authorized action is \*\*Phase 25C\*\* \(benefit-router training\)",
]
COMPILED = [re.compile(p, re.I) for p in PATTERNS]

# A line that merely ASSERTS the corrected semantics (25C does not train) is not stale.
NEGATION_OK = re.compile(
    r"(phase25c_trains_router|phase25c_trains_task_embedding)\s*[\"']?\s*:?\s*"
    r"(false|False|is\s+False)|"
    r"(does\s+NOT\s+train|does\s+not\s+train|NOT\s+train|not\s+train|"
    r"MUST\s+NOT\s+assume|retired_phase_keys)", re.I)

# Frozen / immutable records: hit here => HISTORICAL_PROVENANCE (do not rewrite).
FROZEN_MARKERS = (
    "phase24_v1_1_", "phase24_v1_2", "_provenance", "blocked_attempt",
    "memor_archive", "memory_archive", "_historical", "superseded",
    "phase25a_dedicated_regional_refiner.ipynb",   # frozen canonical predecessor (SHA bound)
    "phase24_narrowed_benefit_aware_refinement_spec__v1_1",
)

# Files that are ACTIVE Phase25B project control / artifacts (must be clean).
CURRENT_PATHS = [
    "reports/audits/phase25b_phase25c_handoff_schema.json",
    "reports/audits/phase25b_final_freeze.json",
    "reports/audits/phase25b_project_status_sync.json",
    "reports/audits/phase25b_stage_semantics_repair_no_execution.json",
    "reports/audits/phase25b_stage_semantics_repair_final_check.json",
    "docs/MEMORY.md",
    "docs/TASKS.md",
    "notebooks/phasewise/PHASE_INDEX.md",
    "notebooks/phasewise/phase_25b_gt_free_features/phase25b_gt_free_pre_refinement_features.ipynb",
    "scripts/notebooks/build_phase25b_notebook.py",
    "scripts/analysis/build_phase25b_binding_audits.py",
    "scripts/analysis/run_phase25b_final_freeze.py",
    "scripts/analysis/run_project_sync_phase24_v1_2_closure.py",
]

SCAN_GLOBS = [
    "reports/audits/phase25*.json", "reports/tables/phase25*.csv",
    "docs/*.md", "notebooks/phasewise/**/*.ipynb", "notebooks/phasewise/*.md",
    "scripts/**/*.py", "*.md", "PROJECT_MASTER_PLAN.md",
]


def classify(rel: str) -> str:
    s = rel.replace("\\", "/")
    if any(m in s.lower() for m in FROZEN_MARKERS):
        return "HISTORICAL_PROVENANCE"
    if s in CURRENT_PATHS:
        return "CURRENT_CANONICAL"
    return "OTHER"


def main() -> int:
    hits = []
    seen = set()
    for g in SCAN_GLOBS:
        for p in ROOT.glob(g):
            rel = str(p.relative_to(ROOT)).replace("\\", "/")
            if rel in seen:
                continue
            seen.add(rel)
            if ".venv" in rel or "/.git/" in rel or rel.startswith(".workbuddy-ai"):
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for ln_no, line in enumerate(text.splitlines(), 1):
                for cp in COMPILED:
                    m = cp.search(line)
                    if m:
                        cls = classify(rel)
                        # A "not for Phase25C, not for router labels" prohibition list is
                        # UNRELATED: it does not assert a stage assignment.
                        if re.search(r"not\s+for\s+Phase\s*25C", line, re.I) \
                                and not re.search(r"Phase\s*25C\s*\(", line, re.I):
                            cls = "UNRELATED"
                        # The repaired artifacts deliberately assert 25C does NOT train
                        # the router / task embedding; those lines are the CORRECTED
                        # semantics, not stale labels.
                        if NEGATION_OK.search(line):
                            cls = "HANDOFF_SEMANTICS_CORRECTED"
                        hits.append({
                            "path": rel, "line": ln_no,
                            "pattern": cp.pattern,
                            "text": line.strip()[:200],
                            "classification": cls,
                        })
                        break

    # a hit is "stale-current" only if it still asserts router/task-embedding ownership
    # by Phase25C in a CURRENT_CANONICAL file.  The prohibition-list false positives and
    # the frozen records never count.
    current_stale = [h for h in hits if h["classification"] == "CURRENT_CANONICAL"]
    hist = [h for h in hits if h["classification"] == "HISTORICAL_PROVENANCE"]
    unrelated = [h for h in hits if h["classification"] == "UNRELATED"]

    out = {
        "artifact": "phase25b_stage_semantics_repository_scan",
        "phase": "25B",
        "repair": "POST_PHASE25B_HANDOFF_SEMANTICS_REPAIR",
        "patterns": PATTERNS,
        "files_scanned": len(seen),
        "n_hits": len(hits),
        "hits": hits,
        "n_current_canonical": len(current_stale),
        "n_historical_provenance": len(hist),
        "n_unrelated": len(unrelated),
        "current_canonical_hits": current_stale,
        "historical_provenance_hits": [
            {"path": h["path"], "line": h["line"], "text": h["text"]} for h in hist],
        "unrelated_hits": [
            {"path": h["path"], "line": h["line"], "text": h["text"]} for h in unrelated],
        "current_canonical_stale_stage_labels": len(current_stale),
        "note": ("frozen canonical predecessors (e.g. the Phase25A notebook, whose SHA is bound "
                 "by gates) are classified HISTORICAL_PROVENANCE and are NOT rewritten; a "
                 "prohibition list such as 'not for Phase25C, not for router labels' is "
                 "UNRELATED because it asserts no stage assignment"),
        "verdict": ("PHASE25B_STAGE_SEMANTICS_SCAN_CLEAN" if not current_stale
                    else "PHASE25B_STAGE_SEMANTICS_SCAN_DIRTY"),
        "generated_utc": UTC,
        "test_reads": 0,
    }
    (AUD / "phase25b_stage_semantics_repository_scan.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")

    print(f"files scanned : {out['files_scanned']}")
    print(f"hits          : {out['n_hits']}")
    print(f"  CURRENT_CANONICAL  : {out['n_current_canonical']}")
    print(f"  HISTORICAL_PROV    : {out['n_historical_provenance']}")
    print(f"  UNRELATED          : {out['n_unrelated']}")
    for h in current_stale:
        print(f"  [STALE] {h['path']}:{h['line']} :: {h['text'][:110]}")
    print(out["verdict"])
    return 0 if not current_stale else 2


if __name__ == "__main__":
    sys.exit(main())
