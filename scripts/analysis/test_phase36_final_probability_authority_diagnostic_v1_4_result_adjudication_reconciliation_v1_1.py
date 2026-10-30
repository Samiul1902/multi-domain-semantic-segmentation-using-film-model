"""Static / non-consuming unit + negative-control validation for the Phase36 v1.4
result-adjudication RECONCILIATION v1.1 (D76 / D77 / D78).

Purely static: re-hashes on-disk evidence and exercises the reconciliation builder's
fail-closed gate via its in-process `evaluate_gate`, WITHOUT executing any model, the
v1.4 diagnostic, or the reconciliation builder's write path.

Proves:
  * frozen v1.0 adjudication unchanged
  * frozen v1.0 builder unchanged
  * all ancestor hashes exact (14/14 family + attempt + prior + targets)
  * D76 corrected field semantics exact (29 / 31, post-snapshot = 029/030)
  * D77 fail-closed gate genuinely prevents write under mismatch
  * D78 source hashes exact + source-semantic extraction succeeds
  * POLICY_B is only asserted if its predicates pass
  * the historical wrong Phase27 score SHA is not introduced
  * no attempt/science markers are touched
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUILDER = (
    ROOT
    / "scripts"
    / "analysis"
    / "build_phase36_final_probability_authority_diagnostic_v1_4_result_adjudication_reconciliation_v1_1.py"
)
OUT_PATH = (
    ROOT
    / "reports"
    / "audits"
    / "phase36_final_probability_authority_diagnostic_v1_4_result_adjudication_reconciliation_v1_1.json"
)

FROZEN_ADJ = (
    "reports/audits/phase36_final_probability_authority_diagnostic_v1_4_result_adjudication_v1_0.json",
    "912cb24e4b27dcc7d66310b36db2154180411ec52d79d19c767aa708220b9b36",
)
FROZEN_BLD = (
    "scripts/analysis/build_phase36_final_probability_authority_diagnostic_v1_4_result_adjudication_v1_0.py",
    "8c95a6f6c3d9f3735169256d9c6f06bd538ed5ebbba8afb8a96ed72b2e81baf7",
)
WRONG_SHA_PREFIX = "08417a17d"
CANONICAL_SCORE_SHA = "702133930ce14ac9513c992833396e3e250d08417b17d1032cbd260a405cfb12"
EXPECTED_CHAIN = "v1_4_29980_2026-10-10T09:56:09Z"

n_pass = 0
n_fail = 0
failures: list[str] = []


def ok(name: str, cond: bool) -> None:
    global n_pass, n_fail
    if cond:
        n_pass += 1
    else:
        n_fail += 1
        failures.append(name)
        print(f"  FAIL {name}")


def sha_file(p: Path) -> str | None:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def load_builder():
    spec = importlib.util.spec_from_file_location("recon_builder", BUILDER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    print("== frozen family ==")
    ok("frozen_adjudication_unchanged", sha_file(ROOT / FROZEN_ADJ[0]) == FROZEN_ADJ[1])
    ok("frozen_builder_unchanged", sha_file(ROOT / FROZEN_BLD[0]) == FROZEN_BLD[1])

    m = load_builder()

    print("== ancestor gate (clean) ==")
    ev = m.evaluate_gate(None)
    ok("clean_gate_pass", ev["gate_pass"] is True)
    ok("family_14_14", ev["n_family_pins_ok"] == 14 and ev["n_family_pins"] == 14)
    for k, v in ev["checks"].items():
        ok(f"check::{k}", bool(v))

    print("== D77 fail-closed: each negated authority must fail the gate ==")
    for key in [
        "frozen_adjudication",
        "frozen_builder",
        "scoring_phaseA",
        "scoring_phaseB",
        "scoring_v1_14",
        "journal_n",
    ]:
        ev2 = m.evaluate_gate({key: "0" * 64})
        ok(f"negctl::{key}_gate_fails", ev2["gate_pass"] is False)
    # The historical wrong prefix must trip the positive guard when it is the prefix
    # the bound score sha actually begins with (simulating a wrong-SHA introduction
    # by making the guard compare against the canonical good constant's leading hex).
    ev3 = m.evaluate_gate({"wrong_sha_prefix": CANONICAL_SCORE_SHA[:9]})
    ok(
        "negctl::historical_wrong_sha_guard_trips",
        ev3["checks"]["historical_wrong_score_sha_not_introduced"] is False,
    )

    print("== D76 corrected semantics ==")
    j = json.loads(OUT_PATH.read_text(encoding="utf-8")) if OUT_PATH.exists() else {}
    ok("d76_reconciled", j.get("D76_status") == "RECONCILED")
    ok("journal_result_snapshot_records_29", j.get("journal_result_snapshot_records") == 29)
    ok("journal_final_on_disk_records_31", j.get("journal_final_on_disk_records") == 31)
    ok("n_post_snapshot_records_2", j.get("n_post_snapshot_records") == 2)
    ok(
        "post_snapshot_records_exact",
        j.get("post_snapshot_records")
        == ["029_101_result_write__BEGIN.json", "030_101_result_write__COMPLETE.json"],
    )
    ok("journal_classification_preserved",
       j.get("journal_29_to_31_classification") == "EXPECTED_POST_RESULT_SNAPSHOT_COMPLETION")
    ok("journal_single_attempt_chain", j.get("journal_single_attempt_chain") is True)
    ok("journal_chain_is_expected", j.get("journal_attempt_chains") == [EXPECTED_CHAIN])

    print("== D77 reconciliation builder is fail-closed ==")
    ok("d77_reconciled", j.get("D77_status") == "RECONCILED")
    ok("original_builder_fail_closed_false", j.get("original_builder_fail_closed") is False)
    ok("new_builder_fail_closed_true", j.get("new_reconciliation_builder_fail_closed") is True)
    ok("fail_closed_gate_all_pass", j.get("fail_closed_gate", {}).get("all_required_checks_pass") is True)

    print("== D78 source binding ==")
    ok("d78_bound", j.get("D78") == "D75_SCORING_SOURCE_PROVENANCE_BOUND")
    ok("phaseA_sha_bound",
       j.get("Phase27_PhaseA_source_sha256")
       == "ac0ffbdadbfe60349061a926f5a664716a3a3690ac3a90c21a35802263975841")
    ok("phaseB_sha_bound",
       j.get("Phase27_PhaseB_source_sha256")
       == "35800e39d9220e638adbb640bd25e18bc14da5298d9bed4a603f2f0dec64cf37")
    ok("v1_14_sha_bound",
       j.get("v1_14_source_sha256")
       == "ac09ff8ded3610244920e66612145b246b33127140d344a9730d454bab27cff5")
    ok("phase27_scored_repr",
       j.get("phase27_historical_scored_representation")
       == "PERSISTED_F16__RECAST_F32__THRESHOLD_0_50")
    ok("v1_14_scored_repr",
       j.get("v1_14_clean_scored_representation") == "LIVE_F32__THRESHOLD_0_50")
    ok("phaseA_not_authoritative",
       j.get("phaseA_binary_pngs_are_not_authoritative_scoring_representation") is True)

    print("== POLICY_B asserted only if predicates pass ==")
    sem = m.derive_scoring_semantics(ev)
    ok("policy_b_asserted", sem["v1_15_repair_policy"] == "POLICY_B")
    ev_bad = json.loads(json.dumps(ev))
    ev_bad["scoring_sources"]["phaseB"]["match"] = False
    sem_bad = m.derive_scoring_semantics(ev_bad)
    ok("policy_b_degrades_on_predicate_failure", sem_bad["v1_15_repair_policy"] == "NOT_ESTABLISHED")
    ok("d78_degrades_on_predicate_failure",
       sem_bad["D78"] == "D75_SCORING_SOURCE_PROVENANCE_NOT_ESTABLISHED")

    print("== guards / prohibitions ==")
    body = OUT_PATH.read_text(encoding="utf-8") if OUT_PATH.exists() else ""
    ok("wrong_sha_not_in_artifact", WRONG_SHA_PREFIX not in body)
    ok("TEST_not_accessed", j.get("TEST_accessed") is False)
    ok("ROUTER_HOLDOUT_not_accessed", j.get("ROUTER_HOLDOUT_accessed") is False)
    ok("v1_15_not_created", j.get("v1_15_created") is False)
    ok("v1_15_not_executed", j.get("v1_15_executed") is False)
    ok("Phase36_not_complete", j.get("Phase36_complete") is False)
    ok("Phase37_not_started", j.get("Phase37") == "NOT_STARTED")
    ok("v1_4_retry_not_permitted", j.get("v1_4_retry_permitted") is False)
    ok(
        "START_unchanged",
        sha_file(ROOT / "reports/audits/phase36_final_probability_authority_diagnostic_start_v1_4.json")
        == "298f56414eaa39281e8dfaf33faa5e1260d6e7708ae5bfe5f850bcf04520caca",
    )
    ok(
        "RESULT_unchanged",
        sha_file(ROOT / "reports/audits/phase36_final_probability_authority_diagnostic_result_v1_4.json")
        == "046a1e3c3053fb00b97895d8d1834d0011f8b190209daa01795e6915b7fd5284",
    )
    ok(
        "FAILURE_absent",
        not (ROOT / "reports/audits/phase36_final_probability_authority_diagnostic_failure_v1_4.json").exists(),
    )

    print(f"\nRESULT: {n_pass} passed, {n_fail} failed")
    if failures:
        print("FAILURES:")
        for f in failures:
            print("  -", f)
        return 1
    print("ALL_VALIDATION_OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
