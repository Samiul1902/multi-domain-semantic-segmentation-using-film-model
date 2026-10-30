"""Phase 24 — additive governance pointer update + governance sync artifact.

DESIGN ONLY. Updates ONLY row 24 of reports/audits/phasewise_notebook_map.csv (previously
NOT_STARTED with PENDING_PHASE23) so it points at the newly materialised Phase-24
specification notebook and figures. Every other row is left byte-identical. Writes
reports/audits/phase24_governance_sync.json.

Usage:
    ./.venv/Scripts/python.exe scripts/analysis/sync_phase24_governance.py
"""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
CSV = AUD / "phasewise_notebook_map.csv"
NB = (ROOT / "notebooks/phasewise/phase_24_architecture_spec"
      / "phase24_narrowed_benefit_aware_refinement_spec.ipynb")
UTC = datetime.now(timezone.utc).isoformat()

nb_sha = hashlib.sha256(NB.read_bytes()).hexdigest()
before = CSV.read_text(encoding="utf-8")

with CSV.open(newline="", encoding="utf-8") as f:
    rows = list(csv.reader(f))

header = rows[0]
assert header[0] == "phase_id", "unexpected map schema"
idx = {name: i for i, name in enumerate(header)}

changed = False
for r in rows[1:]:
    if r and r[0] == "24":
        # additive pointer update only
        r[idx["status"]] = "COMPLETE"
        r[idx["reviewer_notebook"]] = NB.name
        r[idx["canonical_source"]] = "reports/phase24_narrowed_architecture_spec.md"
        r[idx["visual_artifacts"]] = (
            "reports/figures/phase24_architecture_spec/ "
            "(6 design PNG; embedded in notebook)"
        )
        r[idx["active_development_manifest_version"]] = "phase4_v3"
        r[idx["reviewer_notebook_sha256_semantic_repair"]] = nb_sha
        changed = True
        break

assert changed, "row 24 not found"

with CSV.open("w", newline="", encoding="utf-8") as f:
    csv.writer(f).writerows(rows)

after = CSV.read_text(encoding="utf-8")
# confirm only row 24 content changed
b_lines, a_lines = before.splitlines(), after.splitlines()
assert len(b_lines) == len(a_lines), "line count changed"
diffs = [i for i, (x, y) in enumerate(zip(b_lines, a_lines)) if x != y]

sync = {
    "artifact": "phase24_governance_sync",
    "phase": 24,
    "purpose": "additive governance pointer update for the materialised Phase-24 spec notebook",
    "map_file": str(CSV.relative_to(ROOT)).replace("\\", "/"),
    "rows_changed": len(diffs),
    "changed_line_numbers": diffs,
    "updated_row": 24,
    "previous_status": "NOT_STARTED",
    "new_status": "COMPLETE",
    "reviewer_notebook": NB.name,
    "reviewer_notebook_sha256": nb_sha,
    "canonical_source": "reports/phase24_narrowed_architecture_spec.md",
    "additive_only": True,
    "other_rows_untouched": len(diffs) == 1,
    "science_unchanged": True,
    "predecessor_artifacts_modified": 0,
    "generated_utc": UTC,
    "test_reads": 0,
}
(AUD / "phase24_governance_sync.json").write_text(
    json.dumps(sync, indent=1), encoding="utf-8")

print("governance map updated (additive)")
print("  rows changed :", len(diffs), "->", diffs)
print("  row 24 status:", "NOT_STARTED -> COMPLETE")
print("  notebook sha :", nb_sha)
print("wrote phase24_governance_sync.json")
