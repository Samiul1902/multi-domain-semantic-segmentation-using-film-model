#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Phase 29 — PHASE C  STAGE 1: §0 entry gate + §1 predecessor rehash.

Creates:
    reports/audits/phase29_phase_c_entry_gate.json
    reports/audits/phase29_phase_c_predecessor_rehash.json

Exits non-zero (and writes the blocked terminal) on any failure.

NO training, NO forward pass, NO locked-population access.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase29_phase_c_common as C  # noqa: E402


def main() -> int:
    print("=" * 78)
    print("PHASE 29 -- PHASE C  STAGE 1: entry gate + predecessor rehash")
    print("=" * 78)

    # ---------------- §0 entry gate ------------------------------------- #
    pb_final = C.read_json(C.AUD / "phase29_phase_b_final_check.json")
    pb_term = C.read_json(C.AUD / "phase29_phase_b_terminal.json")
    pa_term = C.read_json(C.AUD / "phase29_phase_a_terminal.json")
    spec_term = C.read_json(C.AUD / "phase29_spec_v1_1_terminal.json")

    checks = {}
    checks["phase_b_terminal_exact"] = (
        str(pb_term.get("terminal", "")) == C.PHASE_B_TERMINAL)
    checks["phase_b_final_check_all_pass"] = bool(pb_final.get("all_pass"))
    for k in ("historical_trainer_sources_unchanged",
              "phase29_wrappers_additive_only",
              "rpsi_seed42_config_parity",
              "bphi_seed42_config_parity",
              "somega_seed42_config_parity",
              "seed_bound_before_rng",
              "fixed_partition_full_identity"):
        checks[f"phase_b_{k}"] = bool(pb_final.get(k))
    checks["phase_b_new_run_configs_32"] = int(pb_final.get("new_run_configs", 0)) == 32
    checks["phase_b_unique_output_roots_32"] = int(
        pb_final.get("unique_output_roots", 0)) == 32
    checks["phase_b_output_collisions_0"] = int(
        pb_final.get("output_collisions", -1)) == 0
    # pre-Phase-C counters must all be zero
    for k in ("training_runs", "model_forwards", "val808_reads",
              "router_holdout_reads", "test_reads"):
        checks[f"precondition_{k}_zero"] = int(pb_final.get(k, -1)) == 0
    checks["phase_a_terminal_exact"] = (
        str(pa_term.get("terminal", "")) == C.PHASE_A_TERMINAL)

    all_pass = all(checks.values())
    gate = {
        "artifact": "phase29_phase_c_entry_gate",
        "phase": 29,
        "stage": "PHASE_C_ENTRY_GATE",
        "method": C.METHOD,
        "specification_revision": C.SPEC_REVISION,
        "generated_utc": C.now_utc(),
        "required_terminal": C.PHASE_B_TERMINAL,
        "observed_terminal": pb_term.get("terminal"),
        "checks": checks,
        "n_checks": len(checks),
        "n_failed": sum(1 for v in checks.values() if not v),
        "failed": [k for k, v in checks.items() if not v],
        "blocked_terminal_if_fail": C.BLOCKED["ENTRY_GATE_FAILURE"],
        "all_pass": all_pass,
    }
    C.write_json(gate, C.AUD / "phase29_phase_c_entry_gate.json")
    print(f"[§0] entry gate: {len(checks)-gate['n_failed']}/{len(checks)} "
          f"PASS" if all_pass else "[§0] entry gate: FAIL")

    # ---------------- §1 predecessor rehash ----------------------------- #
    rh = C.rehash_predecessors()
    rehash = {
        "artifact": "phase29_phase_c_predecessor_rehash",
        "phase": 29,
        "stage": "PRE_TRAINING_PREDECESSOR_REHASH",
        "method": C.METHOD,
        "specification_revision": C.SPEC_REVISION,
        "generated_utc": C.now_utc(),
        "predecessors": rh["predecessors"],
        "canonical_trainers": rh["canonical_trainers"],
        "predecessor_drift": rh["drift_count"],
        "drift_names": rh["drift"],
        "blocked_terminal_if_drift": C.BLOCKED["PREDECESSOR_ARTIFACT_DRIFT"],
        "all_pass": rh["drift_count"] == 0,
    }
    C.write_json(rehash, C.AUD / "phase29_phase_c_predecessor_rehash.json")
    print(f"[§1] predecessor rehash: {len(rh['predecessors'])} artifacts, "
          f"{len(rh['canonical_trainers'])} trainers, drift={rh['drift_count']}")

    if not all_pass:
        C.write_json({
            "artifact": "phase29_phase_c_terminal_state",
            "terminal": C.BLOCKED["ENTRY_GATE_FAILURE"],
            "exit_class": "BLOCKED", "generated_utc": C.now_utc(),
            "failed_checks": gate["failed"],
        }, C.AUD / "phase29_phase_c_terminal_state.json")
        print("TERMINAL:", C.BLOCKED["ENTRY_GATE_FAILURE"])
        return 2
    if rh["drift_count"] != 0:
        C.write_json({
            "artifact": "phase29_phase_c_terminal_state",
            "terminal": C.BLOCKED["PREDECESSOR_ARTIFACT_DRIFT"],
            "exit_class": "BLOCKED", "generated_utc": C.now_utc(),
            "drift_names": rh["drift"],
        }, C.AUD / "phase29_phase_c_terminal_state.json")
        print("TERMINAL:", C.BLOCKED["PREDECESSOR_ARTIFACT_DRIFT"])
        return 2

    print("STAGE 1 OK -> entry gate PASS, predecessor drift 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
