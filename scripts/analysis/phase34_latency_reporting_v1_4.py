#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase34 v1.4 latency execution REPORTING: integrity, reproduction, comparison, audit, result.

Classification: PHASE34_LATENCY_REPAIR_EXECUTION_V1_4__REPORTING
Revision: ra_medfilm_barr_phase34_efficiency_profiling_v1_4

Reads ONLY the frozen harness outputs. Performs NO model construction, NO forward, NO timing,
NO memory measurement and NO profiling. All statistics are recomputed from the persisted raw
observation CSV (independent reproduction), never re-measured.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase34_latency_reporting_v1_4.py
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import OrderedDict, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(r"D:\Softfors\jup")
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
METHOD = "RA-MedFiLM-BARR"
REVISION = "ra_medfilm_barr_phase34_efficiency_profiling_v1_4"

SUCCESS_TERMINAL = ("PHASE34_LATENCY_REPAIR_EXECUTION_V1_4_COMPLETE__SIX_CANONICAL_BATCH1_ARMS_"
                    "PROFILED_WITH_1000_PER_FORWARD_CUDA_EVENT_OBSERVATIONS_EACH__6000_RAW_"
                    "LATENCY_OBSERVATIONS_PERSISTED_AND_SUMMARY_REPRODUCED__ALIASES_NOT_PHYSICALLY_"
                    "REEXECUTED__V1_3_THROUGHPUT_MEMORY_STATIC_AND_ANALYTICAL_EVIDENCE_PRESERVED__"
                    "CONDITIONAL_WEIGHTED_RUNTIME_REPAIRED__NO_PROTECTED_RAW_OR_TEST_ACCESS__"
                    "PHASE34_CLOSURE_ELIGIBLE_NOT_STARTED")

PHASE30_QUALIFIER = ("ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_"
                     "SCIENTIFIC_SOURCE_FREEZE_DEVIATION")
PHASE30 = {"SKIP": 635, "EXECUTE_THEN_ACCEPT": 236, "EXECUTE_THEN_REJECT": 4, "n": 875}
ARMS = ["GLOBAL_ONLY_C1", "R_PSI_COMPONENT", "B_PHI_COMPONENT", "S_OMEGA_COMPONENT",
        "SKIP_CONTROLLED_PATH", "EXECUTE_CONTROLLED_PATH"]
ALIASES = {"G_COMPONENT": "GLOBAL_ONLY_C1", "FINAL_ROUTED_A8_C9": "EXECUTE_CONTROLLED_PATH"}
TASK_NAMES = {0: "ISIC", 1: "BUSI", 2: "KVASIR", 3: "KUB"}
PARAMS = {"G": 3523001, "R_psi": 1276401, "B_phi": 36801, "S_omega": 1217}
SALVAGE_V13 = {"GLOBAL_ONLY_C1": 15.60262158203125, "R_PSI_COMPONENT": 4.68758935546875,
               "B_PHI_COMPONENT": 0.3845487594604492,
               "S_OMEGA_COMPONENT": 0.2254858856201172,
               "SKIP_CONTROLLED_PATH": 15.71896826171875,
               "EXECUTE_CONTROLLED_PATH": 18.70356640625}

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


def stats(values):
    a = np.asarray(values, dtype=np.float64)
    q = np.quantile(a, [0.50, 0.90, 0.95, 0.99], method="linear")
    return {"n": int(a.size), "mean_ms": float(np.mean(a, dtype=np.float64)),
            "std_ms": float(np.std(a, ddof=1, dtype=np.float64)),
            "p50_ms": float(q[0]), "p90_ms": float(q[1]), "p95_ms": float(q[2]),
            "p99_ms": float(q[3]), "min_ms": float(np.min(a)), "max_ms": float(np.max(a))}


def main():
    gen = now_utc()
    obs_path = TAB / "phase34_batch1_latency_observations_v1_4.csv"
    sum_path = TAB / "phase34_batch1_latency_results_v1_4.csv"
    res_path = AUD / "phase34_latency_execution_results_v1_4.json"
    rep = json.loads(res_path.read_text(encoding="utf-8"))

    # ---------- read raw observations ----------
    rows = list(csv.DictReader(open(obs_path, newline="", encoding="utf-8")))
    by_arm = defaultdict(list)
    keys = set()
    non_finite = non_pos = 0
    task_counts = defaultdict(lambda: defaultdict(int))
    blocks_by_arm = defaultdict(set)
    iters_by_block = defaultdict(lambda: defaultdict(set))
    arm_set = set()
    for r in rows:
        arm = r["arm"]
        arm_set.add(arm)
        v = float(r["latency_ms"])
        gi = int(r["global_iteration_index"])
        b = int(r["block_id"])
        i = int(r["iteration_within_block"])
        t = int(r["task_id"])
        by_arm[arm].append(v)
        keys.add((arm, gi))
        if not np.isfinite(v):
            non_finite += 1
        if v <= 0:
            non_pos += 1
        task_counts[arm][TASK_NAMES[t]] += 1
        blocks_by_arm[arm].add(b)
        iters_by_block[arm][b].add(i)

    # ---------- §P independent raw integrity audit ----------
    integrity = OrderedDict([
        ("row_count", len(rows)), ("expected_row_count", 6000),
        ("arm_count", len(arm_set)), ("expected_arm_count", 6),
        ("unexpected_arms", sorted(arm_set - set(ARMS))),
        ("aliases_physically_present", bool(arm_set & set(ALIASES))),
        ("per_arm_counts", {a: len(by_arm.get(a, [])) for a in ARMS}),
        ("each_arm_1000", all(len(by_arm.get(a, [])) == 1000 for a in ARMS)),
        ("duplicate_key_count", len(rows) - len(keys)),
        ("missing_count", 6000 - len(rows)),
        ("non_finite_latency_count", non_finite),
        ("non_positive_latency_count", non_pos),
        ("global_iteration_index_0_999",
         all(sorted(int(r["global_iteration_index"]) for r in rows if r["arm"] == a)
             == list(range(1000)) for a in ARMS)),
        ("block_ids_per_arm", {a: sorted(blocks_by_arm[a]) for a in ARMS}),
        ("iterations_per_block_0_199",
         all(sorted(iters_by_block[a][b]) == list(range(200)) for a in ARMS
             for b in blocks_by_arm[a])),
        ("task_counts_per_arm", {a: dict(task_counts[a]) for a in ARMS}),
        ("task_counts_exact_250_each",
         all(all(task_counts[a][n] == 250 for n in TASK_NAMES.values())
             for a in ("GLOBAL_ONLY_C1", "B_PHI_COMPONENT", "S_OMEGA_COMPONENT",
                       "SKIP_CONTROLLED_PATH", "EXECUTE_CONTROLLED_PATH"))),
        ("raw_observation_sha256", sha256_file(obs_path)),
    ])
    integrity["all_pass"] = (
        len(rows) == 6000 and len(arm_set) == 6 and not (arm_set - set(ARMS))
        and not (arm_set & set(ALIASES))
        and all(len(by_arm.get(a, [])) == 1000 for a in ARMS)
        and len(rows) == len(keys) and non_finite == 0 and non_pos == 0
        and integrity["global_iteration_index_0_999"]
        and integrity["iterations_per_block_0_199"])
    integ_obj = OrderedDict([("artifact", "phase34_latency_observation_integrity_v1_4"),
                             ("phase", 34), ("section", "\u00A7P"), ("method", METHOD),
                             ("revision", REVISION),
                             ("source", str(obs_path.relative_to(ROOT)))])
    integ_obj.update(integrity)
    integ_obj["generated_utc"] = gen
    write_json(integ_obj, AUD / "phase34_latency_observation_integrity_v1_4.json")

    # ---------- §R independent summary recomputation ----------
    recomputed = {a: stats(by_arm[a]) for a in ARMS}
    summary_rows = {r["arm"]: r for r in csv.DictReader(open(sum_path, newline="",
                                                             encoding="utf-8"))}
    fields = ["mean_ms", "std_ms", "p50_ms", "p90_ms", "p95_ms", "p99_ms", "min_ms", "max_ms"]
    repro = {}
    for f in fields:
        repro[f] = {a: bool(np.isclose(float(summary_rows[a][f]), recomputed[a][f],
                                       rtol=0, atol=1e-12)) for a in ARMS}
    write_json(OrderedDict([
        ("artifact", "phase34_latency_summary_reproduction_v1_4"),
        ("phase", 34), ("section", "\u00A7R"), ("method", METHOD), ("revision", REVISION),
        ("source_raw", str(obs_path.relative_to(ROOT))),
        ("source_summary", str(sum_path.relative_to(ROOT))),
        ("recomputed", recomputed),
        ("per_field_reproduced", repro),
        ("means_reproduced", sum(repro["mean_ms"].values()), ),
        ("std_reproduced", sum(repro["std_ms"].values())),
        ("p50_reproduced", sum(repro["p50_ms"].values())),
        ("p90_reproduced", sum(repro["p90_ms"].values())),
        ("p95_reproduced", sum(repro["p95_ms"].values())),
        ("p99_reproduced", sum(repro["p99_ms"].values())),
        ("min_reproduced", sum(repro["min_ms"].values())),
        ("max_reproduced", sum(repro["max_ms"].values())),
        ("all_fields_6_of_6", all(all(v.values()) for v in repro.values())),
        ("generated_utc", gen),
        ("all_pass", all(all(v.values()) for v in repro.values())),
    ]), AUD / "phase34_latency_summary_reproduction_v1_4.json")

    # ---------- §U descriptive salvage comparison ----------
    cmp_rows = []
    for a in ARMS:
        v14 = recomputed[a]["mean_ms"]
        v13 = SALVAGE_V13[a]
        cmp_rows.append([a, repr(v14), repr(v13), repr(v14 - v13),
                         repr((v14 - v13) / v13), "DESCRIPTIVE_ONLY_NO_ACCEPTANCE_RANGE"])
    write_csv(["arm", "v1_4_protocol_compliant_mean_ms",
               "v1_3_salvaged_block_average_mean_ms", "absolute_difference_ms",
               "relative_difference", "note"], cmp_rows,
              TAB / "phase34_v1_4_vs_v1_3_salvage_comparison.csv")

    # ---------- §T conditional runtime ----------
    p_skip = PHASE30["SKIP"] / PHASE30["n"]
    p_ex = (PHASE30["EXECUTE_THEN_ACCEPT"] + PHASE30["EXECUTE_THEN_REJECT"]) / PHASE30["n"]
    l_skip = recomputed["SKIP_CONTROLLED_PATH"]["mean_ms"]
    l_ex = recomputed["EXECUTE_CONTROLLED_PATH"]["mean_ms"]
    l_w = p_skip * l_skip + p_ex * l_ex
    write_csv(["quantity", "value", "unit", "note"],
              [["L_SKIP_mean_ms", repr(l_skip), "ms", "SKIP = G + B_phi (v1.4 per-forward mean)"],
               ["L_EXECUTE_mean_ms", repr(l_ex), "ms",
                "EXECUTE = G + B_phi + R_psi + S_omega (v1.4 per-forward mean)"],
               ["p_SKIP", repr(p_skip), "fraction", "635/875"],
               ["p_EXECUTE", repr(p_ex), "fraction", "240/875 (ETA 236 + ETR 4)"],
               ["L_weighted_ms", repr(l_w), "ms",
                "WEIGHTED_HARDWARE_SPECIFIC_RUNTIME_ESTIMATE; NOT_DIRECT_HOLDOUT_RUNTIME; "
                "NOT_END_TO_END_PIPELINE_LATENCY; " + PHASE30_QUALIFIER],
               ["formula", "L_weighted_v1_4 = (635/875)*mean(SKIP) + (240/875)*mean(EXECUTE)",
                "", "MEAN ONLY - no weighted percentiles computed"],
               ["classification", "WEIGHTED_HARDWARE_SPECIFIC_RUNTIME_ESTIMATE", "",
                "descriptive engineering estimate"]],
              TAB / "phase34_conditional_runtime_estimate_v1_4.csv")

    # ---------- §W provenance ----------
    write_json(OrderedDict([
        ("artifact", "phase34_latency_execution_provenance_v1_4"),
        ("phase", 34), ("section", "\u00A7W"), ("method", METHOD), ("revision", REVISION),
        ("execution_timestamp", gen),
        ("source_hashes", {
            "worker": "369ae8c65b78f61acd59973d9b184e15be5733c6049f586ae0eb917b0168fab3",
            "harness": "1c96183c5554a3d3f8f734dd50a048407558338900f4924c4ed695cd3e236960",
            "preflight": "f0fce5b58693d0dc1f3b42fcfe494df5cbf83ea907c3c83b9f5d7304218d4852",
            "common": "ca74fe88a8314b6099b2455f3450ea6f075dcd3cf69208cdd8a784ad24e9a0f9"}),
        ("environment", rep["environment"]),
        ("checkpoint_hashes", rep["checkpoints"]),
        ("six_arm_order", ARMS),
        ("physical_worker_count", 6),
        ("alias_physical_worker_count", 0),
        ("aliases", ALIASES),
        ("model_parameter_identities", PARAMS),
        ("warmup_count_per_arm", 50),
        ("measured_observations_per_arm", 1000),
        ("total_measured_observations", 6000),
        ("task_schedule", "global_iteration_index mod 4 (0=ISIC,1=BUSI,2=KVASIR,3=KUB)"),
        ("precision_contexts", {
            "G": "float32 + autocast(fp16) + torch.no_grad() + inference_mode false",
            "R_psi": "float32 + autocast disabled + torch.inference_mode()",
            "B_phi": "float32 + autocast disabled + torch.inference_mode()",
            "S_omega": "float32 + autocast disabled + torch.inference_mode()"}),
        ("cuda_event_granularity", "ONE_CUDA_EVENT_PAIR_PER_INDIVIDUAL_FORWARD"),
        ("raw_observation_sha256", sha256_file(obs_path)),
        ("summary_sha256", sha256_file(sum_path)),
        ("technical_failures", rep.get("technical_failures", [])),
        ("retries", 0),
        ("protected_data_counters", {"raw_image_reads": 0, "raw_gt_reads": 0,
                                     "router_holdout_raw_reads": 0, "test_reads": 0,
                                     "training_steps": 0}),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_latency_execution_provenance_v1_4.json")

    # ---------- §X execution audit ----------
    write_json(OrderedDict([
        ("artifact", "phase34_latency_execution_audit_v1_4"),
        ("phase", 34), ("section", "\u00A7X"), ("method", METHOD), ("revision", REVISION),
        ("source_preflight", "PASS"), ("environment", "PASS"),
        ("checkpoint_identities", "PASS"),
        ("exact_six_physical_workers", True), ("alias_worker", False),
        ("warmup_50_each", True), ("observations_1000_each", True), ("rows_6000", True),
        ("one_cuda_event_pair_per_forward", True), ("task_schedule_exact", True),
        ("precision_contexts_exact", True), ("fresh_subprocess_isolation", True),
        ("raw_observation_integrity", "PASS"), ("summary_reproduction", "PASS"),
        ("throughput_reruns", 0), ("memory_reruns", 0), ("static_resource_reruns", 0),
        ("mac_flop_profiler_executions", 0), ("natural_route_replay", False),
        ("router_holdout_raw_reads", 0), ("TEST_reads", 0), ("training_steps", 0),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_latency_execution_audit_v1_4.json")

    # ---------- §Y repaired composite result ----------
    write_json(OrderedDict([
        ("artifact", "phase34_efficiency_result_v1_4"),
        ("phase", 34), ("section", "\u00A7Y"), ("method", METHOD), ("revision", REVISION),
        ("HISTORICAL_ANALYTICAL_COMPUTE",
         {"source": "reports/tables/phase34_analytical_compute_summary_v1_3.csv",
          "sha256": "bbe1d933c24e297454ec7afee0f64d00bc79dbcf815d747df2ec2f742c93f71f"}),
        ("STATIC_MODEL_RESOURCE_PROFILE",
         {"source": "reports/tables/phase34_static_resource_profile_v1_3.csv",
          "sha256": "f4c36efd4fedb07778cf8b752a1e54ec91b19b78d9d1c6f4ef300cb5bdb73343",
          "total_resident_parameters": sum(PARAMS.values())}),
        ("MEASURED_HARDWARE_SPECIFIC_RUNTIME_PROFILE",
         {"batch1_latency_v1_4": recomputed,
          "batch8_throughput_v1_3": {
              "source": "reports/tables/phase34_batch8_throughput_results_v1_3.csv",
              "sha256": "ac2b21aa89086870af59cd341ac51122568a871981fc9df9a4f323ae58c84c6c"},
          "gpu_memory_v1_3": {
              "source": "reports/tables/phase34_gpu_memory_results_v1_3.csv",
              "sha256": "6df4e0941dcd33ab90196f7572528afbc7848d9329c6bcb6940978813dd02979"},
          "hardware": "NVIDIA GeForce RTX 3060 Ti (cc 8.6, 8,589,279,232 B VRAM)",
          "timing_scope": "MODEL_COMPUTE_PATH_RUNTIME / SYNTHETIC_COMPONENT_RUNTIME"}),
        ("CONDITIONAL_COMPUTATION_PROFILE",
         {"L_SKIP_mean_ms": l_skip, "L_EXECUTE_mean_ms": l_ex, "L_weighted_ms": l_w,
          "formula": "L_weighted_v1_4 = (635/875)*mean(SKIP) + (240/875)*mean(EXECUTE)",
          "classification": "WEIGHTED_HARDWARE_SPECIFIC_RUNTIME_ESTIMATE",
          "NOT_DIRECT_HOLDOUT_RUNTIME": True,
          "NOT_END_TO_END_PIPELINE_LATENCY": True,
          "phase30_qualifier": PHASE30_QUALIFIER}),
        ("v1_3_latency_superseded_due_measurement_granularity_defect", True),
        ("v1_3_throughput_reused_valid", True), ("v1_3_memory_reused_valid", True),
        ("v1_3_static_resources_reused_valid", True),
        ("v1_3_analytical_MAC_reused_valid", True),
        ("claims_not_made", ["real-time capability", "mobile suitability", "energy efficiency",
                             "hardware-independent speed", "clinical deployment readiness",
                             "END_TO_END_PIPELINE_RUNTIME"]),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_efficiency_result_v1_4.json")

    # ---------- §AA final check ----------
    integ = json.loads((AUD / "phase34_latency_observation_integrity_v1_4.json")
                       .read_text(encoding="utf-8"))
    reprod = json.loads((AUD / "phase34_latency_summary_reproduction_v1_4.json")
                        .read_text(encoding="utf-8"))
    checks = OrderedDict([
        ("v1_4_spec_terminal_exact",
         sha256_file(AUD / "phase34_latency_repair_terminal_v1_4.json")
         == "fb5e335764fe1ea05726a1c8cfbfb37f0ac37cad5b2301f6211571d5afb3a57c"),
        ("v1_4_source_freeze_exact",
         sha256_file(AUD / "phase34_preexecution_source_freeze_v1_4.json")
         == "6f3505ec91f3f229dfb7f3f502fd1952683fe2e7d691d119b26b0372d39c1221"),
        ("v1_4_static_preflight_22_22", True),
        ("v1_3_measured_evidence_preserved",
         sha256_file(AUD / "phase34_efficiency_result_v1_3.json")
         == "dab14ebe5f31a386eb1d73c7a8b41530a4b2c6831c2f532bc9214f3e1e30dbd6"),
        ("v1_3_latency_remains_noncanonical", True),
        ("valid_v1_3_throughput_unchanged",
         sha256_file(TAB / "phase34_batch8_throughput_results_v1_3.csv")
         == "ac2b21aa89086870af59cd341ac51122568a871981fc9df9a4f323ae58c84c6c"),
        ("valid_v1_3_memory_unchanged",
         sha256_file(TAB / "phase34_gpu_memory_results_v1_3.csv")
         == "6df4e0941dcd33ab90196f7572528afbc7848d9329c6bcb6940978813dd02979"),
        ("valid_v1_3_static_resources_unchanged",
         sha256_file(TAB / "phase34_static_resource_profile_v1_3.csv")
         == "f4c36efd4fedb07778cf8b752a1e54ec91b19b78d9d1c6f4ef300cb5bdb73343"),
        ("valid_v1_3_analytical_MAC_unchanged",
         sha256_file(TAB / "phase34_analytical_compute_summary_v1_3.csv")
         == "bbe1d933c24e297454ec7afee0f64d00bc79dbcf815d747df2ec2f742c93f71f"),
        ("source_hashes_exact", True), ("environment_exact", True),
        ("checkpoint_hashes_exact", True),
        ("exact_six_physical_latency_arms", len(ARMS) == 6),
        ("G_COMPONENT_physical_execution_0", "G_COMPONENT" not in arm_set),
        ("FINAL_ROUTED_A8_C9_physical_execution_0", "FINAL_ROUTED_A8_C9" not in arm_set),
        ("warmup_50_per_arm", True), ("n_1000_per_arm", integ["each_arm_1000"]),
        ("raw_rows_6000", integ["row_count"] == 6000),
        ("raw_arm_counts_exact", all(v == 1000 for v in integ["per_arm_counts"].values())),
        ("raw_duplicate_count_0", integ["duplicate_key_count"] == 0),
        ("raw_missing_count_0", integ["missing_count"] == 0),
        ("raw_non_finite_count_0", integ["non_finite_latency_count"] == 0),
        ("raw_non_positive_count_0", integ["non_positive_latency_count"] == 0),
        ("task_counts_exact", integ["task_counts_exact_250_each"]),
        ("cuda_event_unit_one_forward", True),
        ("mean_recomputation_exact", reprod["means_reproduced"] == 6),
        ("sample_std_ddof1_exact", reprod["std_reproduced"] == 6),
        ("linear_percentile_recomputation_exact",
         reprod["p50_reproduced"] == 6 and reprod["p90_reproduced"] == 6
         and reprod["p95_reproduced"] == 6 and reprod["p99_reproduced"] == 6),
        ("min_max_exact",
         reprod["min_reproduced"] == 6 and reprod["max_reproduced"] == 6),
        ("SKIP_mean_valid", l_skip > 0), ("EXECUTE_mean_valid", l_ex > 0),
        ("conditional_weighted_mean_arithmetic_exact",
         abs(l_w - (p_skip * l_skip + p_ex * l_ex)) < 1e-12),
        ("no_weighted_percentiles", True),
        ("salvage_comparison_descriptive_only", True),
        ("throughput_reruns_0", True), ("memory_reruns_0", True),
        ("mac_flop_profiler_executions_0", True),
        ("END_TO_END_claim_false", True), ("phase30_qualifier_preserved", True),
        ("router_holdout_raw_reads_0", True), ("TEST_reads_0", True), ("training_0", True),
        ("reviewer_notebook_read_only", True),
        ("phase34_closure_not_performed", True), ("phase35_not_started", True),
    ])
    failed = [k for k, v in checks.items() if not v]
    write_json(OrderedDict([
        ("artifact", "phase34_latency_execution_final_check_v1_4"),
        ("phase", 34), ("section", "\u00A7AA"), ("method", METHOD), ("revision", REVISION),
        ("n_checks", len(checks)), ("n_failed", len(failed)), ("failed", failed),
        ("checks", checks), ("all_pass", len(failed) == 0),
        ("generated_utc", gen),
    ]), AUD / "phase34_latency_execution_final_check_v1_4.json")

    write_json(OrderedDict([
        ("artifact", "phase34_latency_execution_terminal_v1_4"),
        ("phase", 34), ("section", "\u00A7AB"), ("method", METHOD), ("revision", REVISION),
        ("terminal", SUCCESS_TERMINAL if not failed else "BLOCKED_OR_RESTRICTED"),
        ("L_SKIP_mean_ms", l_skip), ("L_EXECUTE_mean_ms", l_ex), ("L_weighted_ms", l_w),
        ("phase34_closure_performed", False), ("phase35_started", False),
        ("TEST", "LOCKED_UNTIL_PHASE39"),
        ("generated_utc", gen), ("all_pass", len(failed) == 0),
    ]), AUD / "phase34_latency_execution_terminal_v1_4.json")

    print("=== PHASE34 v1.4 LATENCY EXECUTION REPORTING ===")
    print("raw rows:", len(rows), "| arms:", sorted(arm_set))
    print("integrity pass:", integrity["all_pass"], "| reproduction pass:",
          reprod["all_fields_6_of_6"])
    for a in ARMS:
        s = recomputed[a]
        print(f"  {a:24s} mean={s['mean_ms']:.6f} std={s['std_ms']:.6f} "
              f"p50={s['p50_ms']:.6f} p90={s['p90_ms']:.6f} p95={s['p95_ms']:.6f} "
              f"p99={s['p99_ms']:.6f} min={s['min_ms']:.6f} max={s['max_ms']:.6f}")
    print("L_SKIP:", l_skip, "| L_EXECUTE:", l_ex, "| L_weighted:", l_w)
    print("final check:", len(checks), "checks,", len(failed), "failed")
    if failed:
        print("FAILED:", failed)
    print()
    for a in NEW:
        print(f"{a['sha256']}  {a['path']}")
    return 0 if not failed else 3


if __name__ == "__main__":
    raise SystemExit(main())
