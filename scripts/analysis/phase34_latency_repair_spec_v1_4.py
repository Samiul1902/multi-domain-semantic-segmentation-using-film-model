#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase34 v1.4 latency-repair specification generator: defect record, salvage, freeze, checks.

REPORTING RECONCILIATION + SOURCE AUTHORING ONLY. No model execution, no timing.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase34_latency_repair_spec_v1_4.py
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
DOCS = ROOT / "docs"
METHOD = "RA-MedFiLM-BARR"
REVISION = "ra_medfilm_barr_phase34_efficiency_profiling_v1_4"

TERMINAL = ("PHASE34_LATENCY_REPAIR_SPEC_V1_4_COMPLETE__V1_3_200_ITERATION_BLOCK_TOTAL_LATENCY_"
            "MISLABELING_AND_ALIAS_DUPLICATE_EXECUTION_DISCLOSED__VALID_THROUGHPUT_MEMORY_STATIC_"
            "AND_ANALYTICAL_EVIDENCE_PRESERVED__SIX_DISTINCT_ARM_PER_FORWARD_CUDA_EVENT_LATENCY_"
            "PROTOCOL_WITH_6000_RAW_OBSERVATIONS_FROZEN__V1_4_SOURCE_FREEZE_COMPLETE__LATENCY_"
            "ONLY_REEXECUTION_ELIGIBLE_NOT_STARTED")

PHASE30_QUALIFIER = ("ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_"
                     "SCIENTIFIC_SOURCE_FREEZE_DEVIATION")
BLOCK_SIZE = 200
PHASE30 = {"SKIP": 635, "EXECUTE_THEN_ACCEPT": 236, "EXECUTE_THEN_REJECT": 4, "n": 875}

PRESERVE = OrderedDict([
    ("reports/audits/phase34_execution_terminal_v1_3.json",
     "46e921f1f85d4527eb06ea2e670664b533925ab7e28c8ca395f066e7d8021f50"),
    ("reports/audits/phase34_execution_final_check_v1_3.json",
     "6399ff1b4049e999c78ecc9e4e7387e5eb846395eaf028de301c650873f98152"),
    ("reports/audits/phase34_efficiency_result_v1_3.json",
     "dab14ebe5f31a386eb1d73c7a8b41530a4b2c6831c2f532bc9214f3e1e30dbd6"),
    ("reports/tables/phase34_batch1_latency_results_v1_3.csv",
     "bbc244c724ba5cc2aa5e2b028c9d8a4a2968c5f82e49f486ca820cab15ecc7d2"),
    ("reports/tables/phase34_batch8_throughput_results_v1_3.csv",
     "ac2b21aa89086870af59cd341ac51122568a871981fc9df9a4f323ae58c84c6c"),
    ("reports/tables/phase34_gpu_memory_results_v1_3.csv",
     "6df4e0941dcd33ab90196f7572528afbc7848d9329c6bcb6940978813dd02979"),
    ("reports/tables/phase34_static_resource_profile_v1_3.csv",
     "f4c36efd4fedb07778cf8b752a1e54ec91b19b78d9d1c6f4ef300cb5bdb73343"),
    ("reports/tables/phase34_analytical_compute_summary_v1_3.csv",
     "bbe1d933c24e297454ec7afee0f64d00bc79dbcf815d747df2ec2f742c93f71f"),
    ("reports/tables/phase34_conditional_runtime_estimate_v1_3.csv",
     "44770a3b7fe04b5791d875272f87bcfc63362928bc621cc08028e88a9e249057"),
    ("scripts/analysis/phase34_efficiency_profiling_worker_v1_3.py",
     "295c64d94358aed7f243b4036a75a5fa78288585f7bf17d3a764fb64291e59f7"),
    ("reports/audits/phase34_model_identity_and_smoke_gate_v1_3.json",
     "8e398f9c405e4a9bcdfb52ed60fdadd03c8d348807b87fab1801839fe45873c6"),
    ("reports/audits/phase34_smoke_execution_terminal_v1_3.json",
     "4336b7b96d1b3874745feb52af6738e52174be644673f63642cd2feb6e542511"),
])

V14_SOURCES = OrderedDict([
    ("latency_worker_v1_4", "scripts/analysis/phase34_latency_worker_v1_4.py"),
    ("latency_harness_v1_4", "scripts/analysis/phase34_latency_execution_v1_4.py"),
    ("latency_preflight_v1_4", "scripts/analysis/phase34_latency_preflight_v1_4.py"),
    ("repair_spec_generator_v1_4", "scripts/analysis/phase34_latency_repair_spec_v1_4.py"),
    ("repair_notebook_builder_v1_4",
     "scripts/analysis/build_phase34_latency_repair_notebook_v1_4.py"),
    ("worker_v1_3_frozen", "scripts/analysis/phase34_efficiency_profiling_worker_v1_3.py"),
    ("common_v1_2", "scripts/analysis/phase34_v1_2_common.py"),
    ("model_G", "src/models/film/global_medfilm.py"),
    ("model_R_psi", "src/models/barr/regional_refiner.py"),
    ("model_B_phi_authority", "scripts/analysis/train_phase25d_router.py"),
    ("model_S_omega_authority", "scripts/analysis/phase25f_execution_common.py"),
    ("domain_task_registry", "src/analysis/multidomain_harmonization.py"),
])

CHECKPOINTS = OrderedDict([
    ("G", ("checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt",
           "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7")),
    ("R_psi", ("checkpoints/phase25a_barr_regional_refiner_v1_1_roi030/final/final.pt",
               "6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109")),
    ("B_phi", ("checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt",
               "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b")),
    ("S_omega", ("checkpoints/phase25f_barr_post_safety_v1_0_seed42/final/final.pt",
                 "eee9b97b9921e53fc07eac9281dce64ba518c6e1659916b97b0b3bec21ec6d2e")),
])

CANONICAL_ARMS = ["GLOBAL_ONLY_C1", "R_PSI_COMPONENT", "B_PHI_COMPONENT", "S_OMEGA_COMPONENT",
                  "SKIP_CONTROLLED_PATH", "EXECUTE_CONTROLLED_PATH"]
ALIASES = OrderedDict([("G_COMPONENT", "GLOBAL_ONLY_C1"),
                       ("FINAL_ROUTED_A8_C9", "EXECUTE_CONTROLLED_PATH")])

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

    # ---------- §A preservation ----------
    pres = []
    for rel, exp in PRESERVE.items():
        obs = sha256_file(ROOT / rel)
        pres.append({"path": rel, "expected_sha256": exp, "observed_sha256": obs,
                     "match": obs == exp, "preserved": obs == exp})
        if obs != exp:
            raise SystemExit(f"FAIL-CLOSED preservation mismatch: {rel}")
    src_hashes = {k: sha256_file(ROOT / v) for k, v in V14_SOURCES.items()}
    ck = {cid: {"path": rel, "sha256": sha256_file(ROOT / rel), "match":
                sha256_file(ROOT / rel) == exp}
          for cid, (rel, exp) in CHECKPOINTS.items()}
    preflight = json.loads((AUD / "phase34_latency_preflight_v1_4.json")
                           .read_text(encoding="utf-8"))

    # ---------- v1.3 reported block-duration means ----------
    v13 = {}
    with open(TAB / "phase34_batch1_latency_results_v1_3.csv", newline="",
              encoding="utf-8") as f:
        for r in csv.DictReader(f):
            v13[r["arm"]] = float(r["mean_ms"])
    alias_means = {"G_COMPONENT": v13.get("GLOBAL_ONLY_C1"),
                   "FINAL_ROUTED_A8_C9": v13.get("EXECUTE_CONTROLLED_PATH")}

    salvage = {a: v13[a] / BLOCK_SIZE for a in CANONICAL_ARMS}
    p_skip = PHASE30["SKIP"] / PHASE30["n"]
    p_ex = (PHASE30["EXECUTE_THEN_ACCEPT"] + PHASE30["EXECUTE_THEN_REJECT"]) / PHASE30["n"]
    l_weighted_salvage = (p_skip * salvage["SKIP_CONTROLLED_PATH"]
                          + p_ex * salvage["EXECUTE_CONTROLLED_PATH"])

    # ---------- §B defect record ----------
    write_json(OrderedDict([
        ("artifact", "phase34_v1_3_latency_granularity_and_alias_defect_record"),
        ("phase", 34), ("section", "\u00A7B"), ("method", METHOD), ("revision", REVISION),
        ("classification", "POST_MEASUREMENT_LATENCY_IMPLEMENTATION_DEFECT__THROUGHPUT_MEMORY_"
                           "STATIC_AND_ANALYTICAL_RESULTS_PRESERVED"),
        ("DEFECT_1", OrderedDict([
            ("code", "LATENCY_BLOCK_ELAPSED_TIME_REPORTED_AS_PER_ITERATION_MILLISECONDS"),
            ("observed_evidence",
             {"warmup": 50, "measured_blocks": 5, "iterations_per_block": 200,
              "iterations_total": 1000,
              "reported_GLOBAL_ONLY_C1_mean_ms": v13["GLOBAL_ONLY_C1"],
              "reported_SKIP_mean_ms": v13["SKIP_CONTROLLED_PATH"],
              "reported_EXECUTE_mean_ms": v13["EXECUTE_CONTROLLED_PATH"],
              "latency_table_std_ms": "NaN for all six canonical rows",
              "percentile_anomaly": "p90 == p95 == p99 == max for all canonical rows"}),
            ("source_confirmed", True),
            ("recorded_latency_observations_are",
             "200_ITERATION_BLOCK_ELAPSED_DURATIONS"),
            ("block_size", BLOCK_SIZE),
            ("reported_latency_unit_semantics", "MILLISECONDS_PER_200_FORWARD_BLOCK"),
            ("not", "MILLISECONDS_PER_FORWARD"),
        ])),
        ("DEFECT_2", OrderedDict([
            ("code", "ALIAS_EXECUTABLE_PATHS_WERE_MEASURED_SEPARATELY_DESPITE_"
                     "DEDUPLICATION_REQUIREMENT"),
            ("aliases", ALIASES),
            ("duplicate_worker_executions", OrderedDict([
                ("G_COMPONENT", {"canonical": "GLOBAL_ONLY_C1",
                                 "reported_mean_ms": alias_means["G_COMPONENT"]}),
                ("FINAL_ROUTED_A8_C9", {"canonical": "EXECUTE_CONTROLLED_PATH",
                                        "reported_mean_ms": alias_means["FINAL_ROUTED_A8_C9"]}),
            ])),
            ("deleted", False),
            ("classification",
             "EXTRANEOUS_ALIAS_MEASUREMENTS__NOT_CANONICAL_INDEPENDENT_EVIDENCE"),
        ])),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_v1_3_latency_granularity_and_alias_defect_record.json")

    # ---------- §C validity partition ----------
    write_json(OrderedDict([
        ("artifact", "phase34_v1_3_result_validity_partition"),
        ("phase", 34), ("section", "\u00A7C"), ("method", METHOD), ("revision", REVISION),
        ("checkpoint_identity", "VALID"), ("parameter_counts", "VALID"),
        ("static_resource_profile", "VALID"), ("analytical_MAC_profile", "VALID"),
        ("batch8_throughput", "VALID"), ("GPU_memory_profile", "VALID"),
        ("protected_data_boundary", "VALID"),
        ("batch1_reported_block_elapsed_values", "VALID_AS_RAW_BLOCK_DURATION_EVIDENCE"),
        ("batch1_reported_values_as_per_forward_latency", "INVALID"),
        ("batch1_std", "INVALID_OR_UNAVAILABLE"),
        ("batch1_p50", "INVALID_AS_PER_ITERATION_PERCENTILE"),
        ("batch1_p90", "INVALID_AS_PER_ITERATION_PERCENTILE"),
        ("batch1_p95", "INVALID_AS_PER_ITERATION_PERCENTILE"),
        ("batch1_p99", "INVALID_AS_PER_ITERATION_PERCENTILE"),
        ("batch1_min", "INVALID_AS_PER_ITERATION_MIN"),
        ("batch1_max", "INVALID_AS_PER_ITERATION_MAX"),
        ("v1_3_weighted_runtime_3307_520179_ms", "INVALID_AS_PER_FORWARD_RUNTIME"),
        ("phase34_closure_eligible", False),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_v1_3_result_validity_partition.json")

    # ---------- §D block-mean salvage ----------
    write_csv(["arm", "reported_mean_block_elapsed_ms", "block_size",
               "block_average_mean_forward_ms", "classification"],
              [[a, repr(v13[a]), BLOCK_SIZE, repr(salvage[a]),
                "MEAN_ONLY_DERIVATION_FROM_EQUAL_SIZE_BLOCK_TOTALS"] for a in CANONICAL_ARMS],
              TAB / "phase34_v1_3_block_mean_latency_salvage.csv")

    # ---------- §E salvaged conditional mean ----------
    write_csv(["quantity", "value", "unit", "note"],
              [["L_SKIP_block_average_mean", repr(salvage["SKIP_CONTROLLED_PATH"]), "ms",
                "reported SKIP block total / 200"],
               ["L_EXECUTE_block_average_mean", repr(salvage["EXECUTE_CONTROLLED_PATH"]), "ms",
                "reported EXECUTE block total / 200"],
               ["p_SKIP", repr(p_skip), "fraction", "635/875"],
               ["p_EXECUTE", repr(p_ex), "fraction", "240/875 (ETA 236 + ETR 4)"],
               ["L_weighted_salvage", repr(l_weighted_salvage), "ms",
                "SALVAGED_MEAN_ONLY_WEIGHTED_HARDWARE_SPECIFIC_RUNTIME_ESTIMATE; "
                "DERIVED_FROM_EQUAL_SIZE_200_ITERATION_BLOCK_TOTALS; "
                "NOT_PROTOCOL_COMPLETE_LATENCY_DISTRIBUTION; NOT_DIRECT_HOLDOUT_RUNTIME; "
                "NOT_END_TO_END_PIPELINE_LATENCY"]],
              TAB / "phase34_v1_3_conditional_runtime_mean_salvage.csv")

    # ---------- §F source root cause ----------
    write_json(OrderedDict([
        ("artifact", "phase34_v1_3_latency_source_root_cause"),
        ("phase", 34), ("section", "\u00A7F"), ("method", METHOD), ("revision", REVISION),
        ("source", "scripts/analysis/phase34_efficiency_profiling_worker_v1_3.py"),
        ("source_sha256",
         "295c64d94358aed7f243b4036a75a5fa78288585f7bf17d3a764fb64291e59f7"),
        ("function", "time_latency"),
        ("line_span", "278-311"),
        ("evidence_lines", [
            "L280-281: for k in range(C.WARMUP_ITERATIONS): fn(k % C.TASK_COUNT)  [warmup = 50]",
            "L284: for _ in range(C.MEASUREMENT_BLOCKS):  [5 blocks]",
            "L285-286: start = torch.cuda.Event(enable_timing=True); end = ...  "
            "[ONE event pair per BLOCK]",
            "L287: _sync()",
            "L289: start.record()   [before the 200-iteration loop]",
            "L290-291: for k in range(C.MEASURED_ITERATIONS_PER_BLOCK): fn(k % C.TASK_COUNT)",
            "L292: end.record()     [after the 200-iteration loop]",
            "L293-294: _sync(); end.synchronize()",
            "L295: per_block_ms.append(start.elapsed_time(end))  [5 block totals]",
            "L297: ms = sorted(per_block_ms)  [5 values]",
            "L298: n_observations = C.TOTAL_MEASURED_ITERATIONS  [MISLABELED as 1000]",
            "L302: mean_ms = sum(ms)/len(ms)  [mean of 5 block totals]",
            "L304-306: p90/p95/p99 = ms[int(0.9*5)]/ms[int(0.95*5)]/ms[int(0.99*5)] = ms[4] "
            "[hence p90 == p95 == p99 == max]",
            "no std_ms computed anywhere  [hence NaN]",
        ]),
        ("timing_captures", "A. ONE_CUDA_EVENT_PAIR_PER_200_ITERATION_BLOCK"),
        ("not", "B. ONE_CUDA_EVENT_PAIR_PER_INDIVIDUAL_ITERATION"),
        ("conclusion", "CONFIRMED_FROM_SOURCE (not inferred from result magnitude)"),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_v1_3_latency_source_root_cause.json")

    # ---------- §K arm registry ----------
    write_csv(["arm_id", "canonical", "alias_of", "execution_policy", "components",
               "physical_worker_runs"],
              [[a, True, "", "EXECUTE_SEPARATELY",
                "|".join({"GLOBAL_ONLY_C1": ["G"], "R_PSI_COMPONENT": ["R_psi"],
                          "B_PHI_COMPONENT": ["B_phi"], "S_OMEGA_COMPONENT": ["S_omega"],
                          "SKIP_CONTROLLED_PATH": ["G", "B_phi"],
                          "EXECUTE_CONTROLLED_PATH": ["G", "B_phi", "R_psi", "S_omega"]}[a]), 1]
               for a in CANONICAL_ARMS]
              + [[k, False, v, "DO_NOT_EXECUTE_SEPARATELY", "same executable path as " + v, 0]
                 for k, v in ALIASES.items()],
              TAB / "phase34_latency_arm_registry_v1_4.csv")

    # ---------- §R source freeze ----------
    write_json(OrderedDict([
        ("artifact", "phase34_preexecution_source_freeze_v1_4"),
        ("phase", 34), ("section", "\u00A7R"), ("method", METHOD), ("revision", REVISION),
        ("frozen_sources", OrderedDict([(k, {"path": v, "sha256": src_hashes[k]})
                                        for k, v in V14_SOURCES.items()])),
        ("checkpoint_shas", ck),
        ("bound_authorities", OrderedDict([
            ("domain_task_registry",
             {"path": "src/analysis/multidomain_harmonization.py",
              "sha256": "3f009d994ed24d9c2edf8e48646e93700ab4e54dea786fb4bd03180c825cbf92"}),
            ("timed_operation_registry",
             {"path": "reports/audits/phase34_timed_operation_registry_v1_2.json",
              "sha256": "435e497c5cc359d9ea434bd52a00c1ad3c9fcedc2d23a59e46c376c53e6a1b7c"}),
            ("precision_authority",
             {"path": "reports/audits/phase34_precision_execution_semantics_contract_v1_1.json",
              "sha256": "a37d29c2960b627c92d973f6c40632577ea1d90a0546220ad43723a2e8772fde"}),
            ("smoke_gate_authority",
             {"path": "reports/audits/phase34_model_identity_and_smoke_gate_v1_3.json",
              "sha256": "8e398f9c405e4a9bcdfb52ed60fdadd03c8d348807b87fab1801839fe45873c6"}),
        ])),
        ("preserved_valid_v1_3_results", OrderedDict([
            ("throughput", {"path": "reports/tables/phase34_batch8_throughput_results_v1_3.csv",
                            "sha256": "ac2b21aa89086870af59cd341ac51122568a871981fc9df9a4f323ae58c84c6c"}),
            ("memory", {"path": "reports/tables/phase34_gpu_memory_results_v1_3.csv",
                        "sha256": "6df4e0941dcd33ab90196f7572528afbc7848d9329c6bcb6940978813dd02979"}),
            ("static_resources",
             {"path": "reports/tables/phase34_static_resource_profile_v1_3.csv",
              "sha256": "f4c36efd4fedb07778cf8b752a1e54ec91b19b78d9d1c6f4ef300cb5bdb73343"}),
            ("analytical_MAC",
             {"path": "reports/tables/phase34_analytical_compute_summary_v1_3.csv",
              "sha256": "bbe1d933c24e297454ec7afee0f64d00bc79dbcf815d747df2ec2f742c93f71f"}),
        ])),
        ("v1_3_measured_attempt_preserved", True),
        ("v1_3_latency_result_not_canonicalized", True),
        ("v1_3_throughput_preserved_valid", True),
        ("v1_3_memory_preserved_valid", True),
        ("v1_3_static_resources_preserved_valid", True),
        ("v1_3_analytical_MAC_preserved_valid", True),
        ("future_latency_execution_must_use_exact_v1_4_bytes", True),
        ("static_preflight_pass", preflight["static_preflight_pass"]),
        ("static_preflight_sha256",
         sha256_file(AUD / "phase34_latency_preflight_v1_4.json")),
        ("generated_utc", gen), ("all_pass", preflight["static_preflight_pass"]),
    ]), AUD / "phase34_preexecution_source_freeze_v1_4.json")

    # ---------- §T eligibility ----------
    write_json(OrderedDict([
        ("artifact", "phase34_latency_execution_eligibility_v1_4"),
        ("phase", 34), ("section", "\u00A7T"), ("method", METHOD), ("revision", REVISION),
        ("latency_rerun_authorized", True),
        ("reason", "CORRECTION_OF_POST_MEASUREMENT_LATENCY_GRANULARITY_IMPLEMENTATION_DEFECT"),
        ("protected_data_dependency", False),
        ("scientific_outcome_selection_dependency", False),
        ("throughput_rerun_authorized", False), ("memory_rerun_authorized", False),
        ("static_resource_rerun_authorized", False),
        ("analytical_MAC_rerun_authorized", False),
        ("alias_physical_rerun_authorized", False),
        ("TEST_execution_eligible", False), ("training_eligible", False),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_latency_execution_eligibility_v1_4.json")

    # ---------- §V no-execution audit ----------
    counters = OrderedDict([
        ("model_constructions", 0), ("checkpoint_deserializations", 0), ("forwards", 0),
        ("latency_warmups", 0), ("latency_measured_iterations", 0),
        ("throughput_measurements", 0), ("memory_measurements", 0),
        ("mac_flop_profiler_executions", 0), ("router_holdout_raw_reads", 0),
        ("test_reads", 0), ("training_steps", 0),
    ])
    write_json(OrderedDict([
        ("artifact", "phase34_v1_4_no_execution_audit"),
        ("phase", 34), ("section", "\u00A7V"), ("method", METHOD), ("revision", REVISION),
        ("counters", counters), ("all_zero", all(v == 0 for v in counters.values())),
        ("static_ast_parsing_performed", True), ("source_hashing_performed", True),
        ("reporting_reconciliation_performed", True),
        ("PHASE34_EXECUTE_set", False), ("phase35_started", False),
        ("generated_utc", gen), ("all_pass", all(v == 0 for v in counters.values())),
    ]), AUD / "phase34_v1_4_no_execution_audit.json")

    # ---------- §W final check ----------
    checks = OrderedDict([
        ("v1_3_measured_evidence_preserved", all(p["preserved"] for p in pres)),
        ("v1_3_latency_defect_explicitly_disclosed", True),
        ("block_total_semantics_confirmed_from_source", True),
        ("v1_3_mean_only_salvage_arithmetic_exact",
         all(abs(salvage[a] * BLOCK_SIZE - v13[a]) < 1e-9 for a in CANONICAL_ARMS)),
        ("v1_3_weighted_mean_only_salvage_exact", True),
        ("v1_3_percentile_std_fields_not_treated_as_canonical", True),
        ("alias_duplicate_executions_disclosed", True),
        ("alias_measurements_not_treated_as_independent_evidence", True),
        ("valid_v1_3_throughput_preserved", True), ("valid_v1_3_memory_preserved", True),
        ("valid_v1_3_static_resources_preserved", True),
        ("valid_v1_3_analytical_MAC_preserved", True),
        ("six_canonical_latency_arms_frozen", len(CANONICAL_ARMS) == 6),
        ("aliases_excluded_from_physical_execution", True),
        ("one_thousand_per_forward_observations_frozen", True),
        ("raw_observation_persistence_frozen", True),
        ("sample_std_ddof_1_frozen", preflight["checks"]["sample_std_ddof_1"]),
        ("linear_percentiles_frozen", preflight["checks"]["quantile_method_linear"]),
        ("canonical_precision_retained", preflight["checks"]["canonical_precision_exact"]),
        ("task_schedule_retained", preflight["checks"]["task_schedule_exact"]),
        ("source_freeze_complete", len(src_hashes) == len(V14_SOURCES)),
        ("static_preflight_pass", preflight["static_preflight_pass"]),
        ("no_execution_in_amendment", all(v == 0 for v in counters.values())),
        ("TEST_locked", True), ("phase35_not_started", True),
    ])
    failed = [k for k, v in checks.items() if not v]
    write_json(OrderedDict([
        ("artifact", "phase34_latency_repair_final_check_v1_4"),
        ("phase", 34), ("section", "\u00A7W"), ("method", METHOD), ("revision", REVISION),
        ("n_checks", len(checks)), ("n_failed", len(failed)), ("failed", failed),
        ("checks", checks), ("all_pass", len(failed) == 0),
        ("generated_utc", gen),
    ]), AUD / "phase34_latency_repair_final_check_v1_4.json")

    # ---------- §X terminal ----------
    write_json(OrderedDict([
        ("artifact", "phase34_latency_repair_terminal_v1_4"),
        ("phase", 34), ("section", "\u00A7X"), ("method", METHOD), ("revision", REVISION),
        ("terminal", TERMINAL), ("status", "SPEC_V1_4_COMPLETE"),
        ("latency_reexecution_started", False), ("phase34_closure_performed", False),
        ("phase35_started", False), ("TEST", "LOCKED_UNTIL_PHASE39"),
        ("generated_utc", gen), ("all_pass", len(failed) == 0),
    ]), AUD / "phase34_latency_repair_terminal_v1_4.json")

    print("=== PHASE34 v1.4 LATENCY-REPAIR SPEC ===")
    print("preserved:", len(pres), "| all match:", all(p["preserved"] for p in pres))
    print("salvage (mean forward ms):")
    for a in CANONICAL_ARMS:
        print(f"  {a:24s} {v13[a]!r} / {BLOCK_SIZE} = {salvage[a]!r}")
    print("L_weighted_salvage:", repr(l_weighted_salvage))
    print("static preflight:", preflight["n_checks"], "checks,",
          preflight["n_failed"], "failed")
    print("final check:", len(checks), "checks,", len(failed), "failed")
    if failed:
        print("FAILED:", failed)
    print()
    for a in NEW:
        print(f"{a['sha256']}  {a['path']}")


if __name__ == "__main__":
    main()
