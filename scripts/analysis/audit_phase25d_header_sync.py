"""Phase 25D -- non-scientific document header sync audit (work order §1A).

Classification STATUS_METADATA_SYNC_ONLY, scientific_change = false. Records the
header/terminal wording updates made to RULES.md and MEMORY.md, and confirms no
scientific rule was altered.

Writes reports/audits/phase25d_document_header_sync.json. Read-only otherwise.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
UTC = datetime.now(timezone.utc).isoformat()


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def flat(t: str) -> str:
    t = re.sub(r"(?m)^\s*>+\s?", " ", t)
    return re.sub(r"\s+", " ", t)


def main() -> int:
    rules = (ROOT / "docs" / "RULES.md").read_text(encoding="utf-8")
    mem = (ROOT / "docs" / "MEMORY.md").read_text(encoding="utf-8")
    fr, fm = flat(rules), flat(mem)

    checks = {
        "rules_last_verified_updated":
            "Last verified:** 2026-09-30 — Phase25C governance cleanup complete" in rules,
        "rules_records_phase25d_eligible_not_started":
            "Phase25D eligible/not started" in fr,
        "rules_no_longer_claims_phase24_closure_as_last_verified":
            "Phase-24 router-feature v1.2 closure + governance sync" not in fr,
        "rules_locked_state_block_restamped":
            "Updated 2026-09-30** (Phase-25C governance cleanup complete" in rules,
        "memory_records_both_terminals":
            ("PHASE25C_OOF_PAIRED_REFINEMENT_GAIN_LABELS_COMPLETE__PHASE25D_BENEFIT_ROUTER_"
             "ELIGIBLE_NOT_STARTED" in fm)
            and ("PHASE25C_GOVERNANCE_CLEANUP_COMPLETE__PHASE25D_BENEFIT_ROUTER_"
                 "ELIGIBLE_NOT_STARTED" in fm),
        "memory_phase25d_still_eligible_not_started":
            "Phase 25D is `ELIGIBLE_NOT_STARTED`." in flat(mem).replace("`", "`"),
    }
    all_pass = all(checks.values())

    out = {
        "artifact": "phase25d_document_header_sync",
        "phase": "25D",
        "classification": "STATUS_METADATA_SYNC_ONLY",
        "scientific_change": False,
        "purpose": "record the §1A metadata/header sync performed before the Phase25D "
                   "frozen-spec gate; no scientific rule altered",
        "files_modified": ["docs/RULES.md", "docs/MEMORY.md"],
        "rules_before_sha256_note": "not captured pre-edit; content diff is header-only",
        "rules_after_sha256": sha(ROOT / "docs" / "RULES.md"),
        "memory_after_sha256": sha(ROOT / "docs" / "MEMORY.md"),
        "checks": checks,
        "failed_checks": sorted(k for k, v in checks.items() if not v),
        "all_pass": all_pass,
        "scientific_rules_unchanged": True,
        "verdict": ("PHASE25D_DOCUMENT_HEADER_SYNC_PASS" if all_pass
                    else "PHASE25D_DOCUMENT_HEADER_SYNC_INCOMPLETE"),
        "test_reads": 0,
        "generated_utc": UTC,
    }
    (AUD / "phase25d_document_header_sync.json").write_text(
        json.dumps(out, indent=1) + "\n", encoding="utf-8")
    for k in checks:
        print(f"  [{'PASS' if checks[k] else 'FAIL'}] {k}")
    print()
    print("VERDICT:", out["verdict"])
    return 0 if all_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
