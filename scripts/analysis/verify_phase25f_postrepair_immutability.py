"""Phase 25F — independent POST-REPAIR scientific-immutability re-verification.

Belt-and-suspenders check run *after* every compliance-repair write has landed.
Re-reads each canonical scientific artifact from disk and re-hashes it, comparing
against the frozen expected SHAs assembled from the Phase25F bindings. Also pins
the headline artifact SHAs and the notebook / archive / freeze SHAs.

Read-only. No model construction, training, forward/backward, OOF/C9 recompute.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_phase25f_notebook_repair_gates as G  # noqa: E402

ROOT = G.ROOT
AUD = G.AUD
TAB = G.TAB
NB = G.NB
ARCHIVE = G.ARCHIVE

EXPECTED = {
    "notebook_new": "1ba9c08bee97e95926994b11268017e8d6b45150929ebe6edfca4dfe95715c90",
    "notebook_archive_old": "d40120ab35956335e884f2b71398a4a6727e3ca3b50be788fd1d86f33e948908",
    "final_checkpoint": "eee9b97b9921e53fc07eac9281dce64ba518c6e1659916b97b0b3bec21ec6d2e",
    "oof_predictions": "a9f63edd6d58a9a1d78a052a3e4539c6e0dd4d68bfb1c09c4c36789c441ebdee",
    "c9_manifest": "cde91c474bf19bb36368357ce4b38dd1cc7dad1b37d900fcec7cde6b9e72dbd1",
    "final_freeze": "383280b9bbd015b8f85b962a453d7a14b40dea424b55b2fe3189d6bac127bb1c",
}

HEADLINE_PATHS = {
    "notebook_new": NB,
    "notebook_archive_old": ARCHIVE,
    "final_checkpoint": ROOT / "checkpoints/phase25f_barr_post_safety_v1_0_seed42/final/final.pt",
    "oof_predictions": ROOT / "data_cache/phase25f_barr_post_safety_v1_0/phase25f_oof_safety_predictions.csv",
    "c9_manifest": TAB / "phase25f_c9_decision_manifest.csv",
    "final_freeze": AUD / "phase25f_final_freeze.json",
}


def main() -> int:
    report = {
        "artifact": "phase25f_postrepair_immutability_reverification",
        "phase": "25F",
        "classification": "NOTEBOOK_AND_EVIDENCE_PRESENTATION_REPAIR_ONLY",
    }

    # 1) headline artifact SHA pins
    headline = {}
    for key, path in HEADLINE_PATHS.items():
        actual = G.sha(path)
        headline[key] = {
            "path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "expected": EXPECTED[key],
            "actual": actual,
            "match": actual == EXPECTED[key],
        }
    report["headline"] = headline

    # 2) full bound-artifact map re-hash
    exp = G.scientific_artifact_map()
    missing, drift = [], []
    for rel, (_src, expected) in sorted(exp.items()):
        p = ROOT / rel
        if not p.exists():
            missing.append(rel)
            continue
        actual = G.sha(p)
        if actual != expected:
            drift.append({"path": rel, "expected": expected, "actual": actual})
    report["bound_artifact_count"] = len(exp)
    report["missing_artifacts"] = missing
    report["drift"] = drift

    # 3) freeze / compliance cross-checks
    addendum = json.loads((AUD / "phase25f_final_freeze_notebook_compliance_addendum.json").read_text())
    compliance = json.loads((AUD / "phase25f_postrepair_final_compliance_check.json").read_text())
    terminal = json.loads((AUD / "phase25f_notebook_compliance_repair_terminal.json").read_text())
    fz = json.loads((AUD / "phase25f_final_freeze.json").read_text())

    checks = {
        "headline_all_match": all(v["match"] for v in headline.values()),
        "zero_bound_artifact_drift": len(drift) == 0,
        "no_missing_artifacts": len(missing) == 0,
        "final_freeze_sha_unchanged": G.sha(AUD / "phase25f_final_freeze.json") == EXPECTED["final_freeze"],
        "addendum_base_freeze_sha_matches": addendum["base_final_freeze_sha256"] == EXPECTED["final_freeze"],
        "addendum_new_nb_sha_matches": addendum["new_notebook_sha"] == EXPECTED["notebook_new"],
        "addendum_science_changed_false": addendum["science_changed"] is False,
        "compliance_all_pass": compliance.get("all_pass") is True,
        "terminal_exact": terminal["terminal"] == G.TERMINAL_OK,
        "final_freeze_terminal_unchanged": fz.get("terminal") == G.EXPECTED_TERMINAL,
        "phase25f_status_complete_canonical": fz.get("phase25f_status") == "COMPLETE_CANONICAL",
        "phase25g_status_eligible_not_started": fz.get("phase25g_status") == "ELIGIBLE_NOT_STARTED",
        "phase25g_not_started": fz.get("phase25g_started") is False,
        "router_holdout_reads_zero": compliance.get("router_holdout_reads") == 0,
        "val808_reads_zero": compliance.get("VAL808_reads") == 0,
        "test_reads_zero": compliance.get("TEST_reads") == 0,
    }
    report["checks"] = checks
    report["all_pass"] = all(checks.values())

    out = AUD / "phase25f_postrepair_immutability_reverification.json"
    out.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")

    print(json.dumps(report["checks"], indent=1))
    print(f"\nbound_artifact_count = {report['bound_artifact_count']}")
    print(f"drift               = {len(drift)}")
    print(f"missing             = {len(missing)}")
    for k, v in headline.items():
        flag = "OK " if v["match"] else "FAIL"
        print(f"  [{flag}] {k:22s} {v['actual']}")
    print(f"\nALL_PASS = {report['all_pass']}")
    print(f"written -> {out.relative_to(ROOT)}")
    return 0 if report["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
