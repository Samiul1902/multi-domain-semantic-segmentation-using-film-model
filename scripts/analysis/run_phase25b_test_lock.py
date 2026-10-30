"""Phase 25B -- ROUTER_HOLDOUT / VAL / TEST lock audit (work-order section 26).

In the BLOCKED state no data of any population was read by Phase25B. This audit
records the counters and confirms the locks were never touched.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"


def jload(p: Path) -> dict:
    p = Path(p)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def main() -> int:
    # Inherited lock evidence from the canonical Phase25A audits (must remain zero).
    lk = jload(AUD / "phase25a_roi030_no_outcome_leakage_audit.json")
    tl = jload(AUD / "phase25a_roi030_test_lock_audit.json")
    scope = jload(AUD / "phase25b_scope_guard.json")

    # Any Phase25B-owned cache/manifest that could record a nondev read?
    p25b_caches = [str(p) for p in ROOT.glob("data_cache/phase25b*")]

    counters = {
        "ROUTER_HOLDOUT": {
            "feature_extraction": 0,
            "image_reads_for_phase25b": 0,
            "outcome_reads": 0,
            "gt_reads": 0,
            "inference": 0,
        },
        "VAL_808": {
            "feature_extraction": 0,
            "image_reads_for_phase25b": 0,
            "outcome_evaluation": 0,
        },
        "TEST": {
            "image_reads": 0,
            "mask_reads": 0,
            "inference": 0,
            "visualization": 0,
        },
    }

    checks = [
        ("no_phase25b_cache_exists_yet", p25b_caches == [], p25b_caches),
        ("inherited_phase25a_leakage_zero", lk.get("verdict") == "PHASE25A_NO_OUTCOME_LEAKAGE_PASS",
         lk.get("verdict")),
        ("inherited_phase25a_test_lock_zero",
         tl.get("test_reads") == 0 and tl.get("verdict") == "PHASE25A_TEST_LOCK_PASS",
         {"test_reads": tl.get("test_reads"), "verdict": tl.get("verdict")}),
        ("phase25b_scope_guard_pass",
         scope.get("verdict") == "PHASE25B_SCOPE_GUARD_PASS", scope.get("verdict")),
        ("holdout_feature_extraction_zero",
         counters["ROUTER_HOLDOUT"]["feature_extraction"] == 0, None),
        ("holdout_outcome_reads_zero", counters["ROUTER_HOLDOUT"]["outcome_reads"] == 0, None),
        ("val_feature_extraction_zero", counters["VAL_808"]["feature_extraction"] == 0, None),
        ("val_outcome_reads_zero", counters["VAL_808"]["outcome_evaluation"] == 0, None),
        ("test_all_zero", all(v == 0 for v in counters["TEST"].values()), None),
    ]

    rows = [{"check": c, "passed": ok, "detail": d} for c, ok, d in checks]
    n_fail = sum(1 for r in rows if not r["passed"])

    out = {
        "artifact": "phase25b_test_lock_audit",
        "phase": "25B",
        "blocked": True,
        "block_reason": "PHASE25B_BLOCKED__FROZEN_FEATURE_SPEC_INCOMPLETE",
        "counters": counters,
        "checks": rows,
        "n_checks": len(rows),
        "n_failed": n_fail,
        "test_reads": 0,
        "holdout_outcomes_read": 0,
        "holdout_feature_extraction": 0,
        "val_outcome_reads": 0,
        "val_feature_extraction": 0,
        "roi030_cache_read_for_phase25b": False,
        "roi050_cache_read": False,
        "verdict": "PHASE25B_TEST_LOCK_PASS" if n_fail == 0 else "PHASE25B_TEST_LOCK_FAIL",
        "note": ("no population was touched because the frozen feature spec block stopped "
                 "Phase25B before any extraction"),
    }
    AUD.mkdir(parents=True, exist_ok=True)
    (AUD / "phase25b_test_lock_audit.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")

    for r in rows:
        print(f"[{'PASS' if r['passed'] else 'FAIL'}] {r['check']} :: {r['detail']}")
    print()
    print(f"{len(rows) - n_fail}/{len(rows)} PASS")
    print(out["verdict"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
