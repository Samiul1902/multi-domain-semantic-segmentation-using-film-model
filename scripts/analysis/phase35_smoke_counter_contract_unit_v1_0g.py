#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase35 v1.0g smoke counter-contract unit test (CPU / MODEL-FREE).

Classification: PRE_EXECUTION_SYNTHETIC_SMOKE_COUNTER_CONTRACT_REPAIR__NO_SCIENTIFIC_PROTOCOL_CHANGE

Simulates the ONE primary target-mask creation and the ONE empty-mask observability check against the
v1.0g counter contract, and proves that:
  * the PRIMARY counter reaches 1 and its alias reaches 1,
  * the empty-mask observability counter reaches 1,
  * the empty-mask helper does NOT increment the primary (or alias) counter,
  * repeated / incorrect increments ARE detected.

NO model, NO checkpoint, NO torch, NO data, NO forward, NO autograd. Pure stdlib.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase35_smoke_counter_contract_unit_v1_0g.py
"""
from __future__ import annotations

import hashlib
import json
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
AUD = ROOT / "reports" / "audits"
OUT = AUD / "phase35_smoke_counter_contract_unit_v1_0g.json"
METHOD = "RA-MedFiLM-BARR"
REVISION = "ra_medfilm_barr_phase35_interpretability_v1_0g"

PRIMARY = "primary_synthetic_target_masks"
ALIAS = "synthetic_smoke_target_masks"
EMPTY = "actual_logits_empty_mask_helper_checks"
ADD_FWD = "additional_G_forwards_for_empty_mask"
ADD_BWD = "additional_autograd_calls_for_empty_mask"

EXPECTED = OrderedDict([
    (PRIMARY, 1), (ALIAS, 1), (EMPTY, 1), (ADD_FWD, 0), (ADD_BWD, 0),
])


def make_counters():
    # mirrors the frozen v1.0c store shape for the mask-related keys
    return OrderedDict([(PRIMARY, 0), (ALIAS, 0), (EMPTY, 0), (ADD_FWD, 0), (ADD_BWD, 0)])


def primary_target_mask_event(c):
    """The ONE primary mask event: V0D increments the alias internally; v1.0g adds the primary."""
    c[ALIAS] += 1          # frozen V0D.smoke_synthetic_target_mask_rank2()
    c[PRIMARY] += 1        # v1.0g canonical primary counter
    return c


def empty_mask_observability_event(c):
    """The empty-mask observability event: increments ONLY its own counter."""
    c[EMPTY] += 1
    return c


def matches(c, expected):
    return all(c[k] == v for k, v in expected.items())


def main():
    gen = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    tests = OrderedDict()

    # T1 - single primary-mask event
    c = make_counters()
    primary_target_mask_event(c)
    tests["01_primary_event_primary_count_1"] = (c[PRIMARY] == 1)
    tests["02_primary_event_alias_count_1"] = (c[ALIAS] == 1)
    tests["03_primary_event_empty_count_0"] = (c[EMPTY] == 0)
    tests["04_primary_event_alias_equals_primary"] = (c[ALIAS] == c[PRIMARY])

    # T2 - single empty-mask observability event does not touch the primary counters
    # (the primary-mask event already ran once in T1; the empty event is the SECOND, distinct event)
    empty_mask_observability_event(c)
    tests["05_empty_helper_count_1"] = (c[EMPTY] == 1)
    tests["06_empty_helper_preserves_primary_1"] = (c[PRIMARY] == 1)
    tests["07_empty_helper_preserves_alias_1"] = (c[ALIAS] == 1)
    tests["08_empty_helper_not_counted_as_primary"] = (c[PRIMARY] == 1 and c[EMPTY] == 1)

    # T3 - full frozen expectation set matches
    tests["09_full_expected_match"] = matches(c, EXPECTED)
    tests["10_counts_match_expected_true"] = matches(c, EXPECTED)

    # T4 - additional forward/autograd counters remain 0
    tests["11_additional_forward_0"] = (c[ADD_FWD] == 0)
    tests["12_additional_autograd_0"] = (c[ADD_BWD] == 0)

    # ---- negative controls: the OLD v1.0f defect must be DETECTED ----
    # N1: the historical defect (empty helper increments the alias)
    d = make_counters()
    d[ALIAS] += 1            # primary mask
    d[PRIMARY] += 1
    d[ALIAS] += 1            # v1.0f BUG: empty helper increments the alias again
    tests["13_old_defect_detected_primary_ok"] = (d[PRIMARY] == 1)
    tests["14_old_defect_detected_alias_2"] = (d[ALIAS] == 2)
    tests["15_old_defect_breaks_expected"] = (not matches(d, EXPECTED))

    # N2: empty helper increments the OTHER (primary) counter by mistake
    e = make_counters()
    e[ALIAS] += 1
    e[PRIMARY] += 1
    e[PRIMARY] += 1          # WRONG: another increment of the primary counter
    tests["16_wrong_primary_double_increment_detected"] = (e[PRIMARY] == 2 and not matches(e, EXPECTED))

    # N3: repeated/incorrect increment detection helper
    f = make_counters()
    for _ in range(3):
        primary_target_mask_event(f)
    tests["17_triple_primary_detected"] = (f[PRIMARY] == 3 and not matches(f, EXPECTED))

    # N4: missing empty-mask event
    g = make_counters()
    primary_target_mask_event(g)
    tests["18_missing_empty_event_detected"] = (g[EMPTY] == 0 and not matches(g, EXPECTED))

    # N5: correct run matches
    h = make_counters()
    primary_target_mask_event(h)
    empty_mask_observability_event(h)
    tests["19_correct_run_matches_expected"] = matches(h, EXPECTED)
    tests["20_alias_equals_primary_invariant"] = (h[ALIAS] == h[PRIMARY] == 1)

    n_tests = len(tests)
    n_pass = sum(1 for v in tests.values() if v)
    n_fail = n_tests - n_pass
    failed = [k for k, v in tests.items() if not v]

    obj = OrderedDict([
        ("artifact", "phase35_smoke_counter_contract_unit_v1_0g"),
        ("phase", 35), ("method", METHOD), ("revision", REVISION),
        ("classification", "PRE_EXECUTION_SYNTHETIC_SMOKE_COUNTER_CONTRACT_REPAIR__NO_SCIENTIFIC_PROTOCOL_CHANGE"),
        ("environment", "CPU_MODEL_FREE_STDLIB_ONLY"),
        ("tested_counters", OrderedDict([(PRIMARY, 1), (ALIAS, 1), (EMPTY, 1), (ADD_FWD, 0), (ADD_BWD, 0)])),
        ("tests", tests), ("n_tests", n_tests), ("n_pass", n_pass), ("n_fail", n_fail),
        ("failed", failed), ("all_pass", n_fail == 0),
        ("primary_target_mask_counter", PRIMARY),
        ("primary_target_mask_alias_counter", ALIAS),
        ("empty_mask_observability_counter", EMPTY),
        ("primary_expected", 1), ("alias_expected", 1), ("empty_helper_expected", 1),
        ("model_constructed", False), ("checkpoint_deserialized", False),
        ("forward_executed", False), ("autograd_executed", False),
        ("raw_val_reads", 0), ("real_p_global_reads", 0), ("gt_reads", 0),
        ("router_holdout_reads", 0), ("test_reads", 0), ("training", 0),
        ("generated_utc", gen),
    ])
    OUT.write_text(json.dumps(obj, indent=1) + "\n", encoding="utf-8")

    print("=== PHASE35 v1.0g SMOKE COUNTER-CONTRACT UNIT TEST (model-free) ===")
    print("tests:", n_tests, "| pass:", n_pass, "| fail:", n_fail)
    for k in failed:
        print("  FAILED:", k)
    print("all_pass:", n_fail == 0)
    hsh = hashlib.sha256(OUT.read_bytes()).hexdigest()
    print()
    print(f"{hsh}  reports/audits/{OUT.name}")
    return 0 if n_fail == 0 else 3


if __name__ == "__main__":
    raise SystemExit(main())
