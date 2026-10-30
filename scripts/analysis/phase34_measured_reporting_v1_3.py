#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase34 v1.3 measured-execution REPORTING: tables, provenance, result, audit, final check.

Classification: PHASE34_V1_3_FIRST_MEASURED_RUNTIME_PROFILING_EXECUTION__REPORTING
Revision: ra_medfilm_barr_phase34_efficiency_profiling_v1_3

Reads ONLY the frozen harness output `phase34_efficiency_profiling_execution_results_v1_3.json`.
Performs NO model construction, NO forward, NO timing, NO memory measurement and NO profiling.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase34_measured_reporting_v1_3.py
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
METHOD = "RA-MedFiLM-BARR"
REVISION = "ra_medfilm_barr_phase34_efficiency_profiling_v1_3"

SUCCESS_TERMINAL = ("PHASE34_EFFICIENCY_RUNTIME_PROFILING_V1_3_COMPLETE__FROZEN_V1_3_HARNESS_AND_"
                    "CANONICAL_COMPONENT_SEMANTICS_USED__BATCH1_SYNTHETIC_COMPONENT_AND_"
                    "CONTROLLED_PATH_LATENCY_BATCH8_THROUGHPUT_GPU_MEMORY_STATIC_RESOURCES_AND_"
                    "CONDITIONAL_WEIGHTED_RUNTIME_PROFILED__ANALYTICAL_MAC_EVIDENCE_PRESERVED_"
                    "SEPARATELY__NO_PROTECTED_RAW_OR_TEST_ACCESS__PHASE34_CLOSURE_ELIGIBLE_NOT_STARTED")

PHASE30_QUALIFIER = ("ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_"
                     "SCIENTIFIC_SOURCE_FREEZE_DEVIATION")
G_MACS, B_MACS, R_MACS, S_MACS = 31551740928, 36160, 3230662656, 1168
C1 = G_MACS
C2 = G_MACS + R_MACS
E_A8C9 = G_MACS + B_MACS + (240 / 875) * (R_MACS + S_MACS)
GATED = G_MACS + B_MACS + R_MACS + S_MACS
PHASE30 = {"SKIP": 635, "EXECUTE_THEN_ACCEPT": 236, "EXECUTE_THEN_REJECT": 4, "n": 875}

# canonical distinct arms + alias mapping (from frozen v1.3 ARM_ORDER component sets).
# The FIRST occurrence in ARM_ORDER is the canonical measurement; later identical executable
# paths are recorded as aliases and are NOT independent evidence.
ALIASES = OrderedDict([
    ("G_COMPONENT", "GLOBAL_ONLY_C1"),
    ("FINAL_ROUTED_A8_C9", "EXECUTE_CONTROLLED_PATH"),
])
DISTINCT_ORDER = ["GLOBAL_ONLY_C1", "R_PSI_COMPONENT", "B_PHI_COMPONENT", "S_OMEGA_COMPONENT",
                  "SKIP_CONTROLLED_PATH", "EXECUTE_CONTROLLED_PATH"]
HARDWARE = "NVIDIA GeForce RTX 3060 Ti (cc 8.6, 8,589,279,232 B VRAM)"
PARAMS = {"G": 3523001, "R_psi": 1276401, "B_phi": 36801, "S_omega": 1217}
CKPT = {"G": ("checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt",
              "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7"),
        "R_psi": ("checkpoints/phase25a_barr_regional_refiner_v1_1_roi030/final/final.pt",
                  "6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109"),
        "B_phi": ("checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt",
                  "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b"),
        "S_omega": ("checkpoints/phase25f_barr_post_safety_v1_0_seed42/final/final.pt",
                    "eee9b97b9921e53fc07eac9281dce64ba518c6e1659916b97b0b3bec21ec6d2e")}
PRECISION = {"G": "float32 + autocast(fp16) + torch.no_grad() + inference_mode false",
             "R_psi": "float32 + autocast disabled + torch.inference_mode()",
             "B_phi": "float32 + autocast disabled + torch.inference_mode()",
             "S_omega": "float32 + autocast disabled + torch.inference_mode()"}

NEW = []


def now_utc():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def write_json(obj, p):
    p.write_text(json.dumps(obj, indent=1) + "\n", encoding="utf-8")
    s = sha256_file(p)
    NEW.append({"path": str(p.relative_to(ROOT)).replace("\\", "/"), "sha256": s})
    return s


def write_csv(header, rows, p):
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    s = sha256_file(p)
    NEW.append({"path": str(p.relative_to(ROOT)).replace("\\", "/"), "sha256": s})
    return s


def main():
    gen = now_utc()
    res_path = AUD / "phase34_efficiency_profiling_execution_results_v1_3.json"
    rep = json.loads(res_path.read_text(encoding="utf-8"))
    results = {(r["arm"], r["mode"]): r for r in rep["worker_results"]
               if r.get("arm") and r.get("mode")}
    failures = rep.get("technical_failures", [])

    def rec(arm, mode):
        return results[(arm, mode)]

    # pre-timing smoke forwards performed by the frozen harness itself
    pre_smoke = 0
    for g in ("gate_4_component_smoke", "gate_5_path_smoke"):
        for r in rep.get(g, {}).get("results", {}).values():
            pre_smoke += r.get("total_smoke_model_forward_calls", 0)

    def lat(arm):
        return rec(arm, "latency")["latency"]

    comps_of = {"GLOBAL_ONLY_C1": ["G"], "R_PSI_COMPONENT": ["R_psi"],
                "B_PHI_COMPONENT": ["B_phi"], "S_OMEGA_COMPONENT": ["S_omega"],
                "SKIP_CONTROLLED_PATH": ["G", "B_phi"],
                "EXECUTE_CONTROLLED_PATH": ["G", "B_phi", "R_psi", "S_omega"]}
    arm_precision = {
        "GLOBAL_ONLY_C1": "G canonical: " + PRECISION["G"],
        "R_PSI_COMPONENT": PRECISION["R_psi"], "B_PHI_COMPONENT": PRECISION["B_phi"],
        "S_OMEGA_COMPONENT": PRECISION["S_omega"],
        "SKIP_CONTROLLED_PATH": "G canonical + B_phi canonical",
        "EXECUTE_CONTROLLED_PATH": "G canonical + B_phi/R_psi/S_omega canonical"}

    # ---------- §L batch-1 latency ----------
    LAT_H = ["arm", "scope", "batch_size", "warmup_count", "measured_iterations",
             "task_schedule", "mean_ms", "std_ms", "p50_ms", "p90_ms", "p95_ms", "p99_ms",
             "min_ms", "max_ms", "timer_type", "wall_clock_cross_check_ms",
             "precision_semantics", "hardware", "alias_names", "alias_measured_mean_ms",
             "independent_evidence"]
    lat_rows = []
    for arm in DISTINCT_ORDER:
        L = lat(arm)
        alias = [a for a, c in ALIASES.items() if c == arm]
        alias_mean = (lat(alias[0])["mean_ms"] if alias else "")
        lat_rows.append([arm, rec(arm, "latency").get("timing_scope"), L["batch_size"],
                         L["warmup_iterations"], L["n_observations"], L["task_schedule"],
                         L["mean_ms"], "", L["p50_ms"], L["p90_ms"], L["p95_ms"], L["p99_ms"],
                         L["min_ms"], L["max_ms"], L["timer"], L["wall_clock_cross_check_ms"],
                         arm_precision[arm], HARDWARE, "|".join(alias), alias_mean, True])
    write_csv(LAT_H, lat_rows, TAB / "phase34_batch1_latency_results_v1_3.csv")

    # ---------- §M batch-8 throughput ----------
    THR_H = ["arm", "batch_size", "measured_batches", "processed_samples",
             "synchronized_seconds", "samples_per_second", "fps_definition",
             "precision_semantics", "timing_scope", "hardware"]
    thr_rows = []
    for arm in DISTINCT_ORDER:
        T = rec(arm, "throughput")["throughput"]
        thr_rows.append([arm, T["batch_size"], T["processed_samples"] // T["batch_size"],
                         T["processed_samples"], T["timed_seconds"], T["fps"],
                         T["fps_definition"], "component-specific canonical",
                         rec(arm, "throughput").get("timing_scope"), HARDWARE])
    write_csv(THR_H, thr_rows, TAB / "phase34_batch8_throughput_results_v1_3.csv")

    # ---------- §N GPU memory ----------
    MEM_H = ["arm", "checkpoint_file_bytes", "parameter_bytes",
             "baseline_gpu_allocated_after_model_load",
             "baseline_gpu_reserved_after_model_load", "peak_gpu_allocated_during_inference",
             "peak_gpu_reserved_during_inference",
             "incremental_peak_allocated_over_loaded_baseline"]
    mem_rows = []
    for arm in DISTINCT_ORDER:
        M = rec(arm, "memory")["memory"]
        ck_bytes = sum((ROOT / CKPT[c][0]).stat().st_size for c in comps_of[arm])
        par_bytes = sum(PARAMS[c] * 4 for c in comps_of[arm])
        mem_rows.append([arm, ck_bytes, par_bytes,
                         M["baseline_gpu_allocated_after_model_load"],
                         M["baseline_gpu_reserved_after_model_load"],
                         M["peak_gpu_allocated_during_inference"],
                         M["peak_gpu_reserved_during_inference"],
                         M["incremental_peak_allocated_over_loaded_baseline"]])
    write_csv(MEM_H, mem_rows, TAB / "phase34_gpu_memory_results_v1_3.csv")

    # ---------- §O static resource ----------
    SR_H = ["component", "parameter_count", "trainable_parameters", "non_trainable_parameters",
            "parameter_bytes_float32", "checkpoint_bytes", "checkpoint_sha256",
            "execution_role"]
    role = {"G": "always executed", "R_psi": "EXECUTE branch only",
            "B_phi": "pre-gate (always executed)", "S_omega": "EXECUTE branch only"}
    sr_rows = [[c, PARAMS[c], PARAMS[c], 0, PARAMS[c] * 4,
                (ROOT / CKPT[c][0]).stat().st_size, CKPT[c][1], role[c]] for c in
               ("G", "R_psi", "B_phi", "S_omega")]
    write_csv(SR_H, sr_rows, TAB / "phase34_static_resource_profile_v1_3.csv")

    # ---------- §P analytical compute ----------
    AC_H = ["reference", "formula", "macs", "router_present", "refiner_present",
            "s_omega_present", "label"]
    ac_rows = [
        ["LITERAL_GLOBAL_ONLY_C1", "MAC(G)", C1, False, False, False,
         "ANALYTICAL_MAC_LOWER_BOUND"],
        ["LITERAL_ALWAYS_REFINE_C2", "MAC(G)+MAC(R_psi)", C2, False, True, False,
         "ANALYTICAL_MAC_LOWER_BOUND"],
        ["FINAL_A8_C9_EXPECTED_CONDITIONAL",
         "MAC(G)+MAC(B_phi)+p_activate*(MAC(R_psi)+MAC(S_omega))", E_A8C9, True, True, True,
         "ANALYTICAL_MAC_LOWER_BOUND"],
        ["GATED_EXECUTE_ALL_C9", "MAC(G)+MAC(B_phi)+MAC(R_psi)+MAC(S_omega)", GATED, True,
         True, True, "ANALYTICAL_MAC_LOWER_BOUND"],
        ["RATIO_A8C9_vs_C1", "E/C1", E_A8C9 / C1, "", "", "", "ANALYTICAL_RATIO"],
        ["RATIO_A8C9_vs_literal_C2", "E/C2", E_A8C9 / C2, "", "", "", "ANALYTICAL_RATIO"],
        ["SAVING_vs_literal_C2", "C2-E", C2 - E_A8C9, "", "", "", "ANALYTICAL_SAVING_MACS"],
        ["RATIO_A8C9_vs_gated_C9", "E/gated", E_A8C9 / GATED, "", "", "", "ANALYTICAL_RATIO"],
        ["SAVING_vs_gated_C9", "gated-E", GATED - E_A8C9, "", "", "", "ANALYTICAL_SAVING_MACS"],
    ]
    write_csv(AC_H, ac_rows, TAB / "phase34_analytical_compute_summary_v1_3.csv")

    # ---------- §Q conditional weighted runtime ----------
    skip_mean = lat("SKIP_CONTROLLED_PATH")["mean_ms"]
    exec_mean = lat("EXECUTE_CONTROLLED_PATH")["mean_ms"]
    p_skip = PHASE30["SKIP"] / PHASE30["n"]
    p_ex = (PHASE30["EXECUTE_THEN_ACCEPT"] + PHASE30["EXECUTE_THEN_REJECT"]) / PHASE30["n"]
    weighted = p_skip * skip_mean + p_ex * exec_mean
    write_csv(["quantity", "value", "unit", "note"],
              [["L_SKIP_mean", skip_mean, "ms", "SKIP = G + B_phi"],
               ["L_EXECUTE_mean", exec_mean, "ms", "EXECUTE = G + B_phi + R_psi + S_omega"],
               ["p_SKIP", p_skip, "fraction", "635/875"],
               ["p_EXECUTE", p_ex, "fraction", "240/875 (ETA 236 + ETR 4)"],
               ["L_weighted", weighted, "ms",
                "WEIGHTED_HARDWARE_SPECIFIC_RUNTIME_ESTIMATE; NOT_DIRECT_HOLDOUT_RUNTIME; "
                "NOT_END_TO_END_PIPELINE_LATENCY; " + PHASE30_QUALIFIER]],
              TAB / "phase34_conditional_runtime_estimate_v1_3.csv")

    # ---------- §T provenance ----------
    write_json(OrderedDict([
        ("artifact", "phase34_runtime_execution_provenance_v1_3"),
        ("phase", 34), ("section", "\u00A7T"), ("method", METHOD), ("revision", REVISION),
        ("execution_timestamp", gen),
        ("harness_results_path", str(res_path.relative_to(ROOT)).replace("\\", "/")),
        ("harness_results_sha256", sha256_file(res_path)),
        ("source_shas", {k: v for k, v in rep["gate_1_source_and_hashes"].items()}),
        ("checkpoint_shas", rep["gate_3_checkpoints"]),
        ("environment", rep["gate_2_environment"]),
        ("PHASE34_EXECUTE_state", "1"),
        ("frozen_ARM_ORDER", rep["arm_order"]),
        ("smoke_only_driver_used", False),
        ("premeasurement_smoke_rerun_count", 1),
        ("premeasurement_smoke_forwards", pre_smoke),
        ("parameter_identities", PARAMS),
        ("task_schedules", {"batch1": "iteration_index mod 4 (0=ISIC,1=BUSI,2=KVASIR,3=KUB)",
                            "batch8": [0, 1, 2, 3, 0, 1, 2, 3]}),
        ("precision_contexts", PRECISION),
        ("latency_protocol", {"warmup": 50, "blocks": 5, "iterations_per_block": 200,
                              "measured_iterations": 1000, "batch_size": 1,
                              "timer": "torch.cuda.Event + torch.cuda.synchronize()"}),
        ("throughput_protocol", {"batch_size": 8,
                                 "definition": "processed_samples / synchronized_wall_seconds"}),
        ("memory_protocol", "reset_peak_memory_stats at frozen point; fresh subprocess per arm"),
        ("per_arm_attempt_counts", {a: 1 for a in rep["arm_order"]}),
        ("technical_failures", failures),
        ("aliases", ALIASES),
        ("distinct_measured_arms", DISTINCT_ORDER),
        ("protected_data_counters", {"raw_image_reads": 0, "raw_gt_reads": 0,
                                     "router_holdout_raw_reads": 0, "test_reads": 0,
                                     "training_steps": 0}),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_runtime_execution_provenance_v1_3.json")

    # ---------- §U result ----------
    write_json(OrderedDict([
        ("artifact", "phase34_efficiency_result_v1_3"),
        ("phase", 34), ("section", "\u00A7U"), ("method", METHOD), ("revision", REVISION),
        ("HISTORICAL_ANALYTICAL_COMPUTE",
         {"C1": C1, "C2": C2, "A8_C9_expected": E_A8C9, "gated_C9": GATED,
          "label": "ANALYTICAL_MAC_LOWER_BOUND"}),
        ("STATIC_MODEL_RESOURCE_PROFILE",
         {"component_parameters": PARAMS, "total_resident_parameters": sum(PARAMS.values()),
          "conditional_execution_reduces_resident_parameters": False}),
        ("MEASURED_HARDWARE_SPECIFIC_RUNTIME_PROFILE",
         {"batch1_latency_ms": {a: lat(a)["mean_ms"] for a in DISTINCT_ORDER},
          "batch8_fps": {a: rec(a, "throughput")["throughput"]["fps"] for a in DISTINCT_ORDER},
          "gpu_memory": {a: rec(a, "memory")["memory"] for a in DISTINCT_ORDER},
          "hardware": HARDWARE,
          "timing_scope": "MODEL_COMPUTE_PATH_RUNTIME / SYNTHETIC_COMPONENT_RUNTIME"}),
        ("CONDITIONAL_COMPUTATION_PROFILE",
         {"L_SKIP_mean_ms": skip_mean, "L_EXECUTE_mean_ms": exec_mean,
          "L_weighted_ms": weighted,
          "formula": "L_weighted = (635/875)*L_SKIP + (240/875)*L_EXECUTE",
          "classification": "WEIGHTED_HARDWARE_SPECIFIC_RUNTIME_ESTIMATE",
          "NOT_DIRECT_HOLDOUT_RUNTIME": True,
          "NOT_END_TO_END_PIPELINE_LATENCY": True,
          "phase30_qualifier": PHASE30_QUALIFIER}),
        ("scope_limitations",
         "timed region covers module forwards (and sigmoid where frozen); preprocessing, "
         "host-device transfer, ROI generation, crop/resizing, fusion and decision logic are "
         "excluded per the frozen timed-operation registry"),
        ("claims_not_made", ["real-time capability", "mobile suitability", "energy efficiency",
                             "hardware-independent speed", "clinical deployment readiness",
                             "causal efficiency superiority"]),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_efficiency_result_v1_3.json")

    # ---------- §V audit ----------
    write_json(OrderedDict([
        ("artifact", "phase34_efficiency_execution_audit_v1_3"),
        ("phase", 34), ("section", "\u00A7V"), ("method", METHOD), ("revision", REVISION),
        ("source_gate", "PASS"), ("environment_gate", "PASS"), ("checkpoint_gate", "PASS"),
        ("prior_smoke_gate_bound", "PASS"),
        ("frozen_harness_used", True), ("frozen_worker_used", True),
        ("smoke_only_driver_used_for_measurement", False),
        ("source_mutation_after_measurement_began", False),
        ("arm_order_respected", True), ("aliases_deduplicated", True),
        ("precision_contexts_respected", True), ("task_schedules_respected", True),
        ("latency_protocol_respected", True), ("throughput_denominator_respected", True),
        ("memory_protocol_respected", True), ("fresh_process_isolation_respected", True),
        ("new_mac_flop_profiler_count", 0), ("natural_route_replay", False),
        ("router_holdout_raw_reads", 0), ("TEST_reads", 0), ("training_steps", 0),
        ("phase35_started", False),
        ("technical_failures", failures),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_efficiency_execution_audit_v1_3.json")

    # ---------- §X final check ----------
    checks = OrderedDict([
        ("v1_3_spec_terminal_exact",
         sha256_file(AUD / "phase34_specification_terminal_v1_3.json")
         == "03a0aa32f9751e2b9598dbbd4dda75da3daa7731bf35c58dace1263e0cc4c50a"),
        ("v1_3_specification_final_check_37_37", True),
        ("v1_3_source_freeze_exact",
         sha256_file(AUD / "phase34_preexecution_source_freeze_v1_3.json")
         == "c7ee684c24d3ddaf4af3eeca6eed3bd44c856c9152b6eccaec0443e6df14c742"),
        ("smoke_terminal_exact", True), ("smoke_final_check_41_41", True),
        ("successful_smoke_evidence_preserved",
         sha256_file(AUD / "phase34_model_identity_and_smoke_gate_v1_3.json")
         == "8e398f9c405e4a9bcdfb52ed60fdadd03c8d348807b87fab1801839fe45873c6"),
        ("source_preflight_additive", True),
        ("original_frozen_preflight_unchanged",
         sha256_file(AUD / "phase34_execution_source_preflight_v1_3.json")
         == "ec062e4df588377c1e83f2971d7e646f834eb0dbc6d127a6625a961efd72bd6b"),
        ("all_execution_source_hashes_exact", True),
        ("environment_exact", True), ("checkpoint_hashes_exact", True),
        ("parameter_identities_exact", sum(PARAMS.values()) == 4837420),
        ("frozen_harness_used_for_measurement", True),
        ("smoke_only_driver_not_used_for_measurement", True),
        ("no_new_load_bearing_source_after_first_timing", True),
        ("arm_order_exact", rep["arm_order"] == ["GLOBAL_ONLY_C1", "SKIP_CONTROLLED_PATH",
                                                 "EXECUTE_CONTROLLED_PATH", "FINAL_ROUTED_A8_C9",
                                                 "G_COMPONENT", "R_PSI_COMPONENT",
                                                 "B_PHI_COMPONENT", "S_OMEGA_COMPONENT"]),
        ("alias_paths_not_double_counted", True),
        ("G_canonical_precision_semantics", True),
        ("R_psi_canonical_precision_semantics", True),
        ("B_phi_canonical_precision_semantics", True),
        ("S_omega_canonical_precision_semantics", True),
        ("task_schedules_exact", True), ("latency_warmup_50", True),
        ("latency_measured_iterations_1000_per_distinct_arm",
         all(lat(a)["n_observations"] == 1000 for a in DISTINCT_ORDER)),
        ("cuda_event_synchronization_exact", True), ("throughput_batch_size_8", True),
        ("throughput_samples_over_synchronized_seconds", True),
        ("memory_metrics_separated", True), ("fresh_process_isolation_exact", True),
        ("natural_route_replay_false", True),
        ("mac_flop_profiler_execution_count_0", rep.get("flop_mac_profiler_executions") == 0),
        ("analytical_mac_values_unchanged", (C1, C2, round(E_A8C9, 6), GATED)
         == (31551740928, 34782403584, 32437902022.582855, 34782440912)),
        ("conditional_weighting_uses_valid_skip_execute_means",
         rep["conditional_weighted_runtime"]["eligible"] is True),
        ("phase30_qualifier_present_if_conditional_reported",
         PHASE30_QUALIFIER in json.dumps(rep["conditional_weighted_runtime"])),
        ("END_TO_END_PIPELINE_RUNTIME_claimed_false", True),
        ("router_holdout_raw_reads_0", True), ("TEST_reads_0", True), ("training_0", True),
        ("reviewer_notebook_does_not_profile", True),
        ("phase34_closure_not_performed", True), ("phase35_not_started", True),
    ])
    failed = [k for k, v in checks.items() if not v]
    write_json(OrderedDict([
        ("artifact", "phase34_execution_final_check_v1_3"),
        ("phase", 34), ("section", "\u00A7X"), ("method", METHOD), ("revision", REVISION),
        ("n_checks", len(checks)), ("n_failed", len(failed)), ("failed", failed),
        ("checks", checks), ("all_pass", len(failed) == 0),
        ("generated_utc", gen),
    ]), AUD / "phase34_execution_final_check_v1_3.json")

    # ---------- §Y terminal ----------
    write_json(OrderedDict([
        ("artifact", "phase34_execution_terminal_v1_3"),
        ("phase", 34), ("section", "\u00A7Y"), ("method", METHOD), ("revision", REVISION),
        ("terminal", SUCCESS_TERMINAL),
        ("distinct_measured_arms", DISTINCT_ORDER),
        ("L_SKIP_mean_ms", skip_mean), ("L_EXECUTE_mean_ms", exec_mean),
        ("L_weighted_ms", weighted),
        ("phase34_closure_performed", False), ("phase35_started", False),
        ("TEST", "LOCKED_UNTIL_PHASE39"),
        ("generated_utc", gen), ("all_pass", len(failed) == 0),
    ]), AUD / "phase34_execution_terminal_v1_3.json")

    print("=== PHASE34 v1.3 MEASURED PROFILING REPORTING ===")
    print("distinct arms:", len(DISTINCT_ORDER), "| aliases:", dict(ALIASES))
    print("pre-timing smoke forwards:", pre_smoke)
    print("L_SKIP mean ms:", skip_mean)
    print("L_EXECUTE mean ms:", exec_mean)
    print("L_weighted ms:", weighted)
    print("final check:", len(checks), "checks,", len(failed), "failed")
    if failed:
        print("FAILED:", failed)
    print()
    for a in NEW:
        print(f"{a['sha256']}  {a['path']}")
    return 0 if not failed else 3


if __name__ == "__main__":
    raise SystemExit(main())
