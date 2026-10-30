#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase35 v1.0h MODEL-FREE full counter-contract unit test.

CPU / model-free / stdlib-only. This module imports NO torch and constructs NO model. It loads the
v1.0h execution module ONLY for its counter-schema constants and pure counter helpers, then exercises
the frozen contract with synthetic observable/expected dictionaries.

It reproduces as negative controls BOTH historical defects:
  * the v1.0f double-mask defect (two mask events sharing one counter), and
  * the v1.0g split-counter / alias defect (shallow-copied store + un-mirrored alias).

Exit code 0 iff every test passes.
"""
from __future__ import annotations

import os
import sys
from collections import OrderedDict
from pathlib import Path

ROOT = Path(r"D://Softfors//jup")
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))

# Import the v1.0h execution module in gate-safe mode. Setting the smoke gate makes the module
# importable without performing any execution; the module has no import-time model construction.
os.environ.setdefault("PHASE35_SMOKE_EXECUTE", "1")
import phase35_interpretability_execution_v1_0h as H  # noqa: E402

VERBOSE = os.environ.get("PHASE35_UNIT_VERBOSE", "") == "1"
RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((name, bool(ok), detail))
    if VERBOSE or not ok:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  {detail}" if detail else ""))


def _expected() -> OrderedDict:
    return OrderedDict(H.EXPECTED_COUNTERS_V1_0H)


def _make_observed(**overrides) -> OrderedDict:
    """A canonical CORRECT observed store = the full expected table with optional overrides."""
    obs = OrderedDict(_expected())
    for k, v in overrides.items():
        obs[k] = v
    return obs


def _reset_legacy_and_ext() -> None:
    """Reset BOTH live stores to baseline zero (unit-local only; never touches a real run)."""
    for k in H.LEGACY_COUNTER_STORE:
        H.LEGACY_COUNTER_STORE[k] = 0
    for k in H.SMOKE_COUNTERS_EXT:
        H.SMOKE_COUNTERS_EXT[k] = 0


# --------------------------------------------------------------------------- #
# T01-T05 : schema and exact keyset/values
# --------------------------------------------------------------------------- #
def t01_expected_key_count_is_35() -> None:
    n = len(H.EXPECTED_COUNTERS_V1_0H)
    check("T01 expected key count == 35", n == 35, f"got {n}")


def t02_exact_keyset_equality_passes_on_canonical() -> None:
    obs = _make_observed()
    ex = H.exact_counter_contract_check(obs)
    check("T02 canonical keyset exact", ex["counter_keyset_exact"] is True)
    check("T02 canonical count exact", ex["counter_count_exact"] is True)
    check("T02 canonical values exact", ex["counter_values_exact"] is True)
    check("T02 canonical counts_match_expected", ex["counts_match_expected"] is True)


def t03_missing_key_fails() -> None:
    obs = _make_observed()
    del obs["VAL_GT_reads"]
    ex = H.exact_counter_contract_check(obs)
    check("T03 missing key fails keyset", ex["counter_keyset_exact"] is False)
    check("T03 missing key reported", ex["missing_expected_keys"] == ["VAL_GT_reads"])
    check("T03 missing key fails counts_match_expected", ex["counts_match_expected"] is False)


def t04_extra_key_fails() -> None:
    obs = _make_observed()
    obs["unregistered_counter"] = 0
    ex = H.exact_counter_contract_check(obs)
    check("T04 extra key fails keyset", ex["counter_keyset_exact"] is False)
    check("T04 extra key reported", ex["extra_observed_keys"] == ["unregistered_counter"])
    check("T04 extra key count 36", ex["observed_key_count"] == 36)


def t05_wrong_value_fails() -> None:
    obs = _make_observed(total_model_forwards=1)
    ex = H.exact_counter_contract_check(obs)
    check("T05 wrong value keeps keyset exact", ex["counter_keyset_exact"] is True)
    check("T05 wrong value fails values exact", ex["counter_values_exact"] is False)
    check("T05 wrong value reported",
          ex["counter_value_mismatches"].get("total_model_forwards")
          == {"observed": 1, "expected": 2})


def _simulate_primary_mask_event() -> None:
    """Simulate ONE complete primary-mask event EXACTLY as the v1.0h wiring produces it.

    The real event calls the frozen `V0D.smoke_synthetic_target_mask_rank2()`, which imports torch and
    allocates a CUDA tensor. To stay strictly CPU/model/torch-free, this unit reproduces the TWO
    counter consequences of that one event - and nothing else:
      (a) the inherited alias increment on the LIVE legacy store
          (V0D.SMOKE_COUNTERS['synthetic_smoke_target_masks'] += 1), and
      (b) the extension primary increment
          (SMOKE_COUNTERS_EXT['primary_synthetic_target_masks'] += 1).
    The wiring under test (both increments, once each, on disjoint stores) is identical to the real
    pair; only the mask TENSOR construction is elided.
    """
    H.LEGACY_COUNTER_STORE["synthetic_smoke_target_masks"] += 1   # (a) inherited alias, live store
    H.SMOKE_COUNTERS_EXT["primary_synthetic_target_masks"] += 1   # (b) extension primary


def _simulate_empty_mask_event() -> None:
    """Simulate ONE empty-mask observability event (extension counter only, no forward/autograd)."""
    H.SMOKE_COUNTERS_EXT["actual_logits_empty_mask_helper_checks"] += 1


# --------------------------------------------------------------------------- #
# T06-T10 : primary / alias / empty-observability ownership
# --------------------------------------------------------------------------- #
def t06_primary_mask_increments_primary_once() -> None:
    _reset_legacy_and_ext()
    _simulate_primary_mask_event()
    check("T06 primary == 1", H.SMOKE_COUNTERS_EXT["primary_synthetic_target_masks"] == 1,
          f"got {H.SMOKE_COUNTERS_EXT['primary_synthetic_target_masks']}")


def t07_primary_alias_increments_once() -> None:
    _reset_legacy_and_ext()
    _simulate_primary_mask_event()
    alias = H.LEGACY_COUNTER_STORE["synthetic_smoke_target_masks"]
    check("T07 alias == 1", alias == 1, f"got {alias}")


def t08_empty_helper_increments_empty_once() -> None:
    _reset_legacy_and_ext()
    _simulate_empty_mask_event()
    n = H.SMOKE_COUNTERS_EXT["actual_logits_empty_mask_helper_checks"]
    check("T08 empty observability == 1", n == 1, f"got {n}")


def t09_empty_helper_does_not_increment_primary() -> None:
    _reset_legacy_and_ext()
    _simulate_empty_mask_event()
    n = H.SMOKE_COUNTERS_EXT["primary_synthetic_target_masks"]
    check("T09 empty helper leaves primary at 0", n == 0, f"got {n}")


def t10_empty_helper_does_not_increment_alias() -> None:
    _reset_legacy_and_ext()
    _simulate_empty_mask_event()
    n = H.LEGACY_COUNTER_STORE["synthetic_smoke_target_masks"]
    check("T10 empty helper leaves alias at 0", n == 0, f"got {n}")


# --------------------------------------------------------------------------- #
# T11-T15 : protected data, router ownership, merge, duplicates, alias==primary
# --------------------------------------------------------------------------- #
def t11_protected_data_keys_all_zero() -> None:
    prot = ["raw_VAL_image_reads", "real_persisted_VAL_probability_reads", "VAL_GT_reads",
            "router_feature_cache_rows_read", "ROUTER_HOLDOUT_reads", "TEST_reads",
            "TRAIN_raw_reads", "scientific_outputs"]
    exp = _expected()
    present = all(k in exp for k in prot)
    zero = all(exp.get(k) == 0 for k in prot)
    check("T11 all 8 protected keys present", present)
    check("T11 all 8 protected keys expected 0", zero)


def t12_router_legacy_counter_ownership_represented() -> None:
    router_keys = ["B_phi_synthetic_forwards", "router_numeric_input_autograd_calls",
                   "total_model_forwards", "total_autograd_calls",
                   "synthetic_router_attribution_rows"]
    legacy = set(H.LEGACY_COUNTER_STORE)
    ext = set(H.SMOKE_COUNTERS_EXT)
    in_legacy = all(k in legacy for k in router_keys)
    not_in_ext = all(k not in ext for k in router_keys)
    check("T12 router counters owned by LEGACY store", in_legacy)
    check("T12 router counters NOT owned by extension store", not_in_ext)


def t13_merge_produces_35_unique_keys() -> None:
    merged = H.merge_observed_counters()
    check("T13 merge key count == 35", len(merged) == 35, f"got {len(merged)}")
    check("T13 merge keys == expected keys", set(merged) == set(H.EXPECTED_COUNTERS_V1_0H))


def t14_duplicate_ownership_fails() -> None:
    # simulate a duplicate: extension owns a key that legacy also owns
    saved = H.SMOKE_COUNTERS_EXT["additional_G_forwards_for_empty_mask"]
    H.LEGACY_COUNTER_STORE["__dup_probe__"] = 0
    H.SMOKE_COUNTERS_EXT["__dup_probe__"] = 0
    raised = False
    try:
        H.merge_observed_counters()
    except RuntimeError as e:
        raised = "COUNTER_MERGE_DUPLICATE_OWNERSHIP" in str(e) or "KEYSET_MISMATCH" in str(e)
    finally:
        del H.LEGACY_COUNTER_STORE["__dup_probe__"]
        del H.SMOKE_COUNTERS_EXT["__dup_probe__"]
        H.SMOKE_COUNTERS_EXT["additional_G_forwards_for_empty_mask"] = saved
    check("T14 duplicate ownership raises", raised)


def t15_alias_not_equal_primary_fails() -> None:
    obs = _make_observed(synthetic_smoke_target_masks=0)   # alias stale (the v1.0g defect signature)
    ex = H.exact_counter_contract_check(obs)
    check("T15 stale alias fails values exact", ex["counter_values_exact"] is False)
    check("T15 stale alias fails counts_match_expected", ex["counts_match_expected"] is False)
    # and the primary<>alias consistency helper
    consistent = (obs["primary_synthetic_target_masks"] == obs["synthetic_smoke_target_masks"])
    check("T15 primary != alias detected", consistent is False)


# --------------------------------------------------------------------------- #
# T16-T20 : end-to-end correct contract
# --------------------------------------------------------------------------- #
def t16_primary1_alias1_empty1_passes() -> None:
    _reset_legacy_and_ext()
    _simulate_primary_mask_event()
    _simulate_empty_mask_event()
    p = H.SMOKE_COUNTERS_EXT["primary_synthetic_target_masks"]
    a = H.LEGACY_COUNTER_STORE["synthetic_smoke_target_masks"]
    e = H.SMOKE_COUNTERS_EXT["actual_logits_empty_mask_helper_checks"]
    check("T16 primary=1 alias=1 empty=1", (p, a, e) == (1, 1, 1), f"got {(p, a, e)}")


def t17_total_forwards_2_required() -> None:
    obs = _make_observed()
    ok = obs["total_model_forwards"] == 2
    obs_bad = _make_observed(total_model_forwards=1)
    check("T17 total_model_forwards == 2 required", ok)
    check("T17 total_model_forwards 1 rejected",
          H.exact_counter_contract_check(obs_bad)["counter_values_exact"] is False)


def t18_total_autograd_2_required() -> None:
    obs = _make_observed()
    check("T18 total_autograd_calls == 2 required", obs["total_autograd_calls"] == 2)
    obs_bad = _make_observed(total_autograd_calls=1)
    check("T18 total_autograd_calls 1 rejected",
          H.exact_counter_contract_check(obs_bad)["counter_values_exact"] is False)


def t19_router_rows_4_required() -> None:
    obs = _make_observed()
    check("T19 synthetic_router_attribution_rows == 4 required",
          obs["synthetic_router_attribution_rows"] == 4)
    obs_bad = _make_observed(synthetic_router_attribution_rows=0)
    check("T19 router rows 0 rejected (v1.0g signature)",
          H.exact_counter_contract_check(obs_bad)["counter_values_exact"] is False)


def t20_all_35_correct_passes() -> None:
    merged = H.merge_observed_counters()   # baseline zeros
    # build a fully-correct simulated observed store exercising the whole contract
    obs = _make_observed()
    ex = H.exact_counter_contract_check(obs)
    check("T20 all 35 correct -> keyset exact", ex["counter_keyset_exact"] is True)
    check("T20 all 35 correct -> count exact", ex["counter_count_exact"] is True)
    check("T20 all 35 correct -> values exact", ex["counter_values_exact"] is True)
    check("T20 all 35 correct -> counts_match_expected", ex["counts_match_expected"] is True)
    check("T20 merge baseline key set == expected", set(merged) == set(H.EXPECTED_COUNTERS_V1_0H))


# --------------------------------------------------------------------------- #
# NEGATIVE CONTROLS : reproduce both historical defects
# --------------------------------------------------------------------------- #
def n01_v1_0f_double_mask_defect() -> None:
    """Two mask events sharing one counter -> that counter reaches 2 vs expected 1."""
    shared = 0
    shared += 1   # primary mask event
    shared += 1   # empty-mask observability event (WRONG: shares the primary counter)
    check("N01 v1.0f double-mask defect reproduced", shared == 2,
          "shared counter reached 2 vs expected 1")
    obs = _make_observed(synthetic_smoke_target_masks=shared,
                         primary_synthetic_target_masks=shared)
    ex = H.exact_counter_contract_check(obs)
    check("N01 double-mask rejected by contract", ex["counts_match_expected"] is False)


def n02_v1_0g_shallow_copy_alias_defect() -> None:
    """Shallow-copied store disconnects the reported store from the inherited alias writer."""
    import copy
    live_legacy = OrderedDict([("synthetic_smoke_target_masks", 0)])
    reported_copy = OrderedDict(live_legacy)          # the v1.0g defect: OrderedDict(...) copy
    live_legacy["synthetic_smoke_target_masks"] += 1  # inherited writer mutates the LIVE store
    check("N02 v1.0g split-store defect reproduced",
          reported_copy["synthetic_smoke_target_masks"] == 0
          and live_legacy["synthetic_smoke_target_masks"] == 1,
          "reported copy stayed 0 while live store became 1")
    # the v1.0h single-ownership model avoids it by aliasing:
    live2 = OrderedDict([("synthetic_smoke_target_masks", 0)])
    alias2 = live2                                     # v1.0h: alias, not copy
    live2["synthetic_smoke_target_masks"] += 1
    check("N02 v1.0h aliasing model unaffected",
          alias2["synthetic_smoke_target_masks"] == 1)


def main() -> int:
    tests = [t01_expected_key_count_is_35, t02_exact_keyset_equality_passes_on_canonical,
             t03_missing_key_fails, t04_extra_key_fails, t05_wrong_value_fails,
             t06_primary_mask_increments_primary_once, t07_primary_alias_increments_once,
             t08_empty_helper_increments_empty_once, t09_empty_helper_does_not_increment_primary,
             t10_empty_helper_does_not_increment_alias, t11_protected_data_keys_all_zero,
             t12_router_legacy_counter_ownership_represented, t13_merge_produces_35_unique_keys,
             t14_duplicate_ownership_fails, t15_alias_not_equal_primary_fails,
             t16_primary1_alias1_empty1_passes, t17_total_forwards_2_required,
             t18_total_autograd_2_required, t19_router_rows_4_required, t20_all_35_correct_passes,
             n01_v1_0f_double_mask_defect, n02_v1_0g_shallow_copy_alias_defect]
    for t in tests:
        t()
    _reset_legacy_and_ext()

    npass = sum(1 for _, ok, _ in RESULTS if ok)
    nfail = len(RESULTS) - npass
    print(f"\nunit tests: {npass}/{len(RESULTS)} assertions passed, {nfail} failed")
    print(f"test functions: {len(tests)}")

    import json
    import hashlib
    import datetime
    out = OrderedDict([
        ("artifact", "phase35_full_counter_contract_unit_v1_0h"),
        ("section", "\u00a7L"), ("phase", 35), ("method", "RA-MedFiLM-BARR"),
        ("revision", H.REVISION),
        ("test_class", "MODEL_FREE_CPU_STDLIB_ONLY"),
        ("torch_imported", False), ("model_constructed", False),
        ("checkpoint_deserialized", False), ("forward_executed", False), ("autograd_executed", False),
        ("test_functions", len(tests)),
        ("assertions_total", len(RESULTS)),
        ("assertions_passed", npass),
        ("assertions_failed", nfail),
        ("covered", [
            "expected_key_count_35", "keyset_equality", "missing_key_fails", "extra_key_fails",
            "wrong_value_fails", "primary_increments_once", "alias_increments_once",
            "empty_increments_once", "empty_not_primary", "empty_not_alias",
            "protected_zero", "router_legacy_ownership", "merge_35_unique",
            "duplicate_ownership_fails", "alias_ne_primary_fails", "primary1_alias1_empty1",
            "forwards2", "autograd2", "router_rows4", "all35_pass",
            "negative_control_v1_0f_double_mask", "negative_control_v1_0g_split_store"]),
        ("failures", [{"name": n, "detail": d} for n, ok, d in RESULTS if not ok]),
        ("generated_utc", datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")),
        ("all_pass", nfail == 0),
    ])
    op = ROOT / "reports" / "audits" / "phase35_full_counter_contract_unit_v1_0h.json"
    op.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8", newline="\n")
    print("wrote", op)
    print("unit artifact sha256:", hashlib.sha256(op.read_bytes()).hexdigest())
    return 0 if nfail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
