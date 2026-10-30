#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 29 — PHASE D STAGE 1: §0 entry gate + §1 frozen-artifact rehash.

§0  Verify the Phase C terminal and the Phase C final-check contract, the
    pre-VAL808 freeze gate, and the VAL808 shared-cache contract v1.1.
    STOP PHASE29_PHASE_D_BLOCKED__ENTRY_GATE_FAILURE on any failure.

§1  Rehash every frozen Phase C artifact + the canonical components + the
    Phase27 VAL808 global-probability cache + the canonical trainers (§1).
    The ONE declared, user-approved additive entry-point exception in
    scripts/training/train_phase25a_refiner.py must be the ONLY drift.
    Pre-VAL808-read assertion: VAL808 images have NOT been read yet.

Writes NO VAL808 image or mask reads in this stage.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase29_phase_d_entry.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase29_phase_d_common as D  # noqa: E402

say = print
RESULTS: dict[str, bool] = {}
FAIL: list[str] = []


def check(section, name, cond, detail=""):
    ok = bool(cond)
    say(f"  [{'PASS' if ok else 'FAIL'}] {name} {detail}".rstrip())
    RESULTS[f"{section}::{name}"] = ok
    if not ok:
        FAIL.append(f"{section}::{name}")
    return ok


# =========================================================================== #
# §0 ENTRY GATE
# =========================================================================== #
def s0_entry_gate():
    say("")
    say("=" * 78)
    say("PHASE 29 -- PHASE D  §0 ENTRY GATE")
    say("=" * 78)

    fc = D.read_json(D.AUD / "phase29_phase_c_final_check.json")
    fg = D.read_json(D.ROOT / D.PHASE_C_PRE_VAL808_FREEZE_GATE)
    cc = D.read_json(D.ROOT / D.VAL808_CACHE_CONTRACT_V1_1)

    check("S0", "phase_c_final_check_exists", bool(fc), str(bool(fc)))
    check("S0", "phase_c_final_check_all_pass", fc.get("all_pass") is True)
    check("S0", "phase_c_final_check_n_failed_zero", fc.get("n_failed") == 0,
          str(fc.get("n_failed")))
    check("S0", "phase_c_success_terminal",
          fc.get("success_terminal_if_pass") == D.PHASE_C_TERMINAL,
          (fc.get("success_terminal_if_pass") or "")[:60])
    check("S0", "phase_c_new_training_runs_32",
          fc.get("new_training_runs") == 32, str(fc.get("new_training_runs")))
    check("S0", "phase_c_unauthorized_zero",
          fc.get("unauthorized_training_runs") == 0,
          str(fc.get("unauthorized_training_runs")))
    check("S0", "phase_c_val808_reads_zero", fc.get("VAL808_reads") == 0,
          str(fc.get("VAL808_reads")))
    check("S0", "phase_c_router_holdout_reads_zero",
          fc.get("ROUTER_HOLDOUT_reads") == 0, str(fc.get("ROUTER_HOLDOUT_reads")))
    check("S0", "phase_c_test_reads_zero", fc.get("TEST_reads") == 0,
          str(fc.get("TEST_reads")))
    check("S0", "phase_c_best_seed_selected_false",
          fc.get("best_seed_selected") is False)
    check("S0", "phase_c_canonical_bundle_changed_false",
          fc.get("canonical_bundle_changed") is False)
    check("S0", "phase_c_stop_after_pre_val808_freeze_gate",
          fc.get("stop_after") == "PRE_VAL808_FREEZE_GATE",
          str(fc.get("stop_after")))

    check("S0", "pre_val808_freeze_gate_all_pass", fg.get("all_pass") is True)
    check("S0", "pre_val808_freeze_gate_n_failed_zero", fg.get("n_failed") == 0,
          str(fg.get("n_failed")))
    check("S0", "pre_val808_freeze_gate_val808_reads_zero",
          fg.get("VAL808_reads") == 0, str(fg.get("VAL808_reads")))

    check("S0", "val808_contract_v1_1_all_pass", cc.get("all_pass") is True)
    check("S0", "val808_contract_unresolved_placeholders_empty",
          cc.get("unresolved_placeholders") == [],
          str(cc.get("unresolved_placeholders")))
    check("S0", "val808_contract_no_TO_BE_CONFIRMED",
          cc.get("no_TO_BE_CONFIRMED") is True)
    check("S0", "val808_contract_no_IF_REUSABLE", cc.get("no_IF_REUSABLE") is True)
    check("S0", "val808_contract_shared_G_logical_passes_1",
          cc.get("shared_G_logical_passes") == 1,
          str(cc.get("shared_G_logical_passes")))
    check("S0", "val808_contract_shared_G_samples_808",
          cc.get("shared_G_samples") == 808, str(cc.get("shared_G_samples")))
    check("S0", "val808_contract_runs_once_not_per_seed",
          cc.get("runs_once_not_per_seed") is True)
    check("S0", "val808_contract_G_retrained_false",
          cc.get("G_retrained") is False)

    artifact = {
        "artifact": "phase29_phase_d_entry_gate",
        "phase": 29, "stage": "PHASE_D_ENTRY_GATE",
        "method": D.METHOD, "specification_revision": D.SPEC_REVISION,
        "generated_utc": D.now_utc(),
        "predecessor_terminal_expected": D.PHASE_C_TERMINAL,
        "phase_c_final_check": {
            "all_pass": fc.get("all_pass"), "n_checks": fc.get("n_checks"),
            "n_failed": fc.get("n_failed"),
            "new_training_runs": fc.get("new_training_runs"),
            "unauthorized_training_runs": fc.get("unauthorized_training_runs"),
            "VAL808_reads": fc.get("VAL808_reads"),
            "ROUTER_HOLDOUT_reads": fc.get("ROUTER_HOLDOUT_reads"),
            "TEST_reads": fc.get("TEST_reads"),
            "best_seed_selected": fc.get("best_seed_selected"),
            "canonical_bundle_changed": fc.get("canonical_bundle_changed"),
        },
        "pre_val808_freeze_gate": {
            "all_pass": fg.get("all_pass"), "n_checks": fg.get("n_checks"),
            "n_failed": fg.get("n_failed"), "VAL808_reads": fg.get("VAL808_reads"),
        },
        "val808_cache_contract_v1_1": {
            "all_pass": cc.get("all_pass"),
            "unresolved_placeholders": cc.get("unresolved_placeholders"),
            "no_TO_BE_CONFIRMED": cc.get("no_TO_BE_CONFIRMED"),
            "no_IF_REUSABLE": cc.get("no_IF_REUSABLE"),
            "shared_G_logical_passes": cc.get("shared_G_logical_passes"),
            "shared_G_samples": cc.get("shared_G_samples"),
            "runs_once_not_per_seed": cc.get("runs_once_not_per_seed"),
            "G_retrained": cc.get("G_retrained"),
            "decision": cc.get("decision"),
        },
        "checks": {k: v for k, v in RESULTS.items() if k.startswith("S0::")},
        "all_pass": not any(k.startswith("S0::") for k in FAIL),
        "blocked_terminal_if_fail": D.BLOCKED["ENTRY_GATE_FAILURE"],
    }
    D.write_json(artifact, D.AUD / "phase29_phase_d_entry_gate.json")
    return artifact


# =========================================================================== #
# §1 FROZEN ARTIFACT REHASH
# =========================================================================== #
def s1_frozen_rehash():
    say("")
    say("=" * 78)
    say("PHASE 29 -- PHASE D  §1 FROZEN ARTIFACT REHASH")
    say("=" * 78)

    rh = D.rehash_predecessors()
    drift = sorted(rh["drift"])

    say(f"  predecessor records: {len(rh['predecessors'])}")
    say(f"  canonical components: {len(rh['canonical_components'])}")
    say(f"  phase27 cache artifacts: {len(rh['phase27_cache'])}")
    say(f"  canonical trainers: {len(rh['canonical_trainers'])}")
    say(f"  drift: {drift}")

    for name, rel, exp in D.CANONICAL_COMPONENTS:
        p = D.ROOT / rel
        act = D.sha256_file(p) if p.exists() else None
        check("S1", f"component_{name}", act == exp, (act or "MISSING")[:16])

    for name, rel, exp in D.PHASE27_CACHE_ARTIFACTS:
        p = D.ROOT / rel
        act = D.sha256_file(p) if p.exists() else None
        check("S1", f"phase27_cache_{name}", act == exp, (act or "MISSING")[:16])

    # canonical trainers: exactly the declared exception, no other drift
    check("S1", "trainer_drift_is_only_declared_exception",
          drift == [] or drift == [D.DECLARED_TRAINER_EXCEPTION],
          str(drift))
    tdrift = [t["name"] for t in rh["canonical_trainers"] if not t["unchanged"]]
    check("S1", "trainer_effective_no_unexpected_drift", tdrift == [], str(tdrift))
    entry = [t for t in rh["canonical_trainers"]
             if t["name"] == D.DECLARED_TRAINER_EXCEPTION][0]
    check("S1", "declared_exception_sha_is_approved_current",
          entry["sha256_observed"] == D.DECLARED_TRAINER_EXCEPTION_SHA_CURRENT,
          (entry["sha256_observed"] or "")[:16])

    # pre-VAL808-read assertion: the Phase27 global-prob cache predates Phase D
    gp = D.ROOT / D.PHASE27_GLOBAL_PROB
    check("S1", "phase27_global_prob_present", gp.exists())
    import numpy as np
    if gp.exists():
        arr = np.load(gp, mmap_mode="r")
        check("S1", "phase27_global_prob_shape_808_512_512",
              tuple(arr.shape) == (808, 512, 512), str(tuple(arr.shape)))
        check("S1", "phase27_global_prob_dtype_f16",
              str(arr.dtype) == "float16", str(arr.dtype))

    artifact = {
        "artifact": "phase29_phase_d_predecessor_rehash",
        "phase": 29, "stage": "PHASE_D_FROZEN_ARTIFACT_REHASH",
        "method": D.METHOD, "specification_revision": D.SPEC_REVISION,
        "generated_utc": D.now_utc(),
        "rehash": rh,
        "drift": drift, "drift_count": len(drift),
        "declared_exception": D.DECLARED_TRAINER_EXCEPTION,
        "declared_exception_sha_current": D.DECLARED_TRAINER_EXCEPTION_SHA_CURRENT,
        "declared_exception_repair_class": "ADDITIVE_ONLY_ENTRYPOINT_GENERALIZATION",
        "no_new_exception": (drift == [] or drift == [D.DECLARED_TRAINER_EXCEPTION]),
        "val808_images_read_in_this_stage": 0,
        "checks": {k: v for k, v in RESULTS.items() if k.startswith("S1::")},
        "all_pass": not any(k.startswith("S1::") for k in FAIL),
        "blocked_terminal_if_fail": D.BLOCKED["FROZEN_ARTIFACT_DRIFT"],
    }
    D.write_json(artifact, D.AUD / "phase29_phase_d_predecessor_rehash.json")
    return artifact


def main() -> int:
    say("=" * 78)
    say("PHASE 29 -- PHASE D STAGE 1: entry gate + frozen rehash")
    say("=" * 78)

    g = s0_entry_gate()
    if not g["all_pass"]:
        say("")
        say(f"STOP: {D.BLOCKED['ENTRY_GATE_FAILURE']}")
        return 2
    r = s1_frozen_rehash()
    if not r["all_pass"]:
        say("")
        say(f"STOP: {D.BLOCKED['FROZEN_ARTIFACT_DRIFT']}")
        return 3

    say("")
    say("=" * 78)
    say("PHASE D STAGE 1 GATES (§0-§1): ALL PASS")
    say("=" * 78)
    say("PHASE_D_ENTRY_GATE_AND_FROZEN_REHASH_PASS__VAL808_NOT_YET_READ")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
