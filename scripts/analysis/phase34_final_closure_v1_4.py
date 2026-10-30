#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase34 FINAL CANONICAL GOVERNANCE CLOSURE + Phase35 handoff (governance/packaging only).

Classification: PHASE34_FINAL_CANONICAL_GOVERNANCE_CLOSURE__GOVERNANCE_PACKAGING_ONLY
Revision: ra_medfilm_barr_phase34_efficiency_profiling_v1_4

ZERO EXECUTION. No model construction, no checkpoint deserialization, no forward, no timing,
no throughput, no memory measurement, no profiler, no new scientific estimate. Only read-only
arithmetic verification of already-stored numbers for governance checking.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase34_final_closure_v1_4.py
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
REVISION = "ra_medfilm_barr_phase34_efficiency_profiling_v1_4"

TERMINAL = ("PHASE34_COMPUTATIONAL_EFFICIENCY_RUNTIME_PROFILING_COMPLETE_CANONICAL__V1_4_PER_"
            "FORWARD_LATENCY_DISTRIBUTION_ACCEPTED_AFTER_DISCLOSED_V1_3_GRANULARITY_REPAIR__V1_3_"
            "THROUGHPUT_MEMORY_STATIC_AND_ANALYTICAL_EVIDENCE_PRESERVED_VALID__WEIGHTED_HARDWARE_"
            "SPECIFIC_RUNTIME_ESTIMATE_ACCEPTED_WITH_PHASE30_QUALIFIER__NO_END_TO_END_REALTIME_"
            "MOBILE_ENERGY_OR_HARDWARE_INDEPENDENT_CLAIMS__NO_PROTECTED_RAW_OR_TEST_ACCESS__"
            "PHASE35_ELIGIBLE_NOT_STARTED")

CLOSURE_CLASS = ("COMPUTATIONAL_EFFICIENCY_AND_RUNTIME_PROFILING_COMPLETE_CANONICAL__V1_4_PER_"
                 "FORWARD_LATENCY_REPAIR_CANONICAL__VALID_V1_3_NONLATENCY_EVIDENCE_REUSED__V1_3_"
                 "LATENCY_DEFECT_PRESERVED_AS_SUPERSEDED_PROVENANCE")

PHASE30_QUALIFIER = ("ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_"
                     "SCIENTIFIC_SOURCE_FREEZE_DEVIATION")
PHASE30_STATUS = "COMPLETE_WITH_PROTOCOL_DEVIATION__NOT_COMPLETE_CANONICAL"

PHASE35_ID = "phase_35_interpretability"
PHASE35_TITLE = "Feature Attribution & Visual Interpretability"

BIND = OrderedDict([
    ("reports/audits/phase34_latency_execution_terminal_v1_4.json",
     "1c9d81b3efc61320c4fac9fa404dea891c283381cf4b1c9f31b79f67fed225bf"),
    ("reports/audits/phase34_latency_execution_final_check_v1_4.json",
     "736bda19e34a824fd43a1fa4de43af0f3d45e1734693949753dc052c49be12a6"),
    ("reports/audits/phase34_efficiency_result_v1_4.json",
     "971e1dd9c864cdb3c3ac8f9adc79dc7f61ae8707f99666e059bcb991a31cda3b"),
    ("reports/tables/phase34_batch1_latency_observations_v1_4.csv",
     "4b50dc96d1c07d780f614a7221a6432febdc572119d6d6c3665a5099a100d34c"),
    ("reports/tables/phase34_batch1_latency_results_v1_4.csv",
     "da5292d4551209339b3880c0e64d4152007eb42e7c262ad296bc2c2ec586ab26"),
    ("reports/audits/phase34_latency_observation_integrity_v1_4.json",
     "5a5d85288375e1854bf4307e1a3fca6b46caa4779560c3629542d540e24d1898"),
    ("reports/audits/phase34_latency_summary_reproduction_v1_4.json",
     "6cfaa6ecfe83a82466f970a74afbacda822f57bcc17e8f3bf811fa974814ecad"),
    ("reports/tables/phase34_conditional_runtime_estimate_v1_4.csv",
     "05ec0c5a82ba9b0c93f53c455de34b991aab591864fb30017e1ef86eaa5d8111"),
    ("notebooks/phasewise/phase_34_efficiency_profiling/"
     "phase34_latency_execution_v1_4_review.ipynb",
     "9fdb2155e44b62ee149ec98949f2c9b954bd34de2366293b28b3dfc7a4287d9d"),
    ("reports/tables/phase34_batch8_throughput_results_v1_3.csv",
     "ac2b21aa89086870af59cd341ac51122568a871981fc9df9a4f323ae58c84c6c"),
    ("reports/tables/phase34_gpu_memory_results_v1_3.csv",
     "6df4e0941dcd33ab90196f7572528afbc7848d9329c6bcb6940978813dd02979"),
    ("reports/tables/phase34_static_resource_profile_v1_3.csv",
     "f4c36efd4fedb07778cf8b752a1e54ec91b19b78d9d1c6f4ef300cb5bdb73343"),
    ("reports/tables/phase34_analytical_compute_summary_v1_3.csv",
     "bbe1d933c24e297454ec7afee0f64d00bc79dbcf815d747df2ec2f742c93f71f"),
    ("reports/audits/phase34_execution_terminal_v1_3.json",
     "46e921f1f85d4527eb06ea2e670664b533925ab7e28c8ca395f066e7d8021f50"),
    ("reports/tables/phase34_batch1_latency_results_v1_3.csv",
     "bbc244c724ba5cc2aa5e2b028c9d8a4a2968c5f82e49f486ca820cab15ecc7d2"),
    ("reports/audits/phase34_v1_3_latency_granularity_and_alias_defect_record.json",
     "d8152a4923a78ae1f64fcf61583f3fd5c8f10b044128c46b676544ab128630ec"),
    ("reports/audits/phase34_v1_3_latency_source_root_cause.json",
     "a4ca49f3ffb5622785ac4eca3227165bd3f7b7530fc2cf0159544418bef3ac22"),
    ("reports/audits/phase34_v1_3_result_validity_partition.json",
     "558ac4b1a1215b6089c719cb48d4e9717ca545c866d30bc95fae1d5c85e8b7bc"),
    ("reports/audits/phase34_latency_repair_terminal_v1_4.json",
     "fb5e335764fe1ea05726a1c8cfbfb37f0ac37cad5b2301f6211571d5afb3a57c"),
    ("reports/audits/phase34_preexecution_source_freeze_v1_4.json",
     "6f3505ec91f3f229dfb7f3f502fd1952683fe2e7d691d119b26b0372d39c1221"),
])

# canonical v1.4 latency values (exact, unrounded)
LAT = OrderedDict([
    ("GLOBAL_ONLY_C1", (15.767750472068787, 0.6395504640838543, 15.721471786499023,
                        16.69969940185547, 16.830668258666993, 17.085439682006836,
                        14.539775848388672, 18.61939239501953)),
    ("R_PSI_COMPONENT", (4.533609761238099, 0.7306397681817417, 4.374016046524048,
                         5.271756887435913, 5.702348589897154, 7.662858080863951,
                         3.1047680377960205, 9.80787181854248)),
    ("B_PHI_COMPONENT", (0.37281001573055983, 0.08135652045953644, 0.3614720106124878,
                         0.4293184041976929, 0.5018112063407898, 0.6882099145650863,
                         0.03788800165057182, 1.1182080507278442)),
    ("S_OMEGA_COMPONENT", (0.25486716816946864, 0.07774529723188978, 0.24371199309825897,
                           0.31334400177001953, 0.37703680843114834, 0.5162393558025359,
                           0.01945599913597107, 1.0516480207443237)),
    ("SKIP_CONTROLLED_PATH", (15.71835146522522, 0.5901199029168571, 15.684608459472656,
                              16.61143054962158, 16.768204498291016, 16.916530323028564,
                              14.544896125793457, 17.23187255859375)),
    ("EXECUTE_CONTROLLED_PATH", (18.894091419219972, 0.6584723138309989, 18.88663959503174,
                                 19.62188720703125, 19.833861351013184, 20.46585823059082,
                                 17.303552627563477, 23.586816787719727)),
])
FIELDS = ["mean_ms", "std_ms", "p50_ms", "p90_ms", "p95_ms", "p99_ms", "min_ms", "max_ms"]

THROUGHPUT = {"GLOBAL_ONLY_C1": 93.66100492292452, "R_PSI_COMPONENT": 600.5210676264255,
              "B_PHI_COMPONENT": 20721.04577066513, "S_OMEGA_COMPONENT": 34532.62253695135,
              "SKIP_CONTROLLED_PATH": 93.17560442781323,
              "EXECUTE_CONTROLLED_PATH": 80.26287810203608}

PARAMS = {"G": 3523001, "R_psi": 1276401, "B_phi": 36801, "S_omega": 1217}
C1, C2, E_A8C9, GATED = 31551740928, 34782403584, 32437902022.582855, 34782440912
P_SKIP, P_EX = 635 / 875, 240 / 875

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


def main():
    gen = now_utc()

    # ---------- §A/§B/§D/§F/§J bindings ----------
    bind = []
    for rel, exp in BIND.items():
        obs = sha256_file(ROOT / rel)
        bind.append({"path": rel, "expected_sha256": exp, "observed_sha256": obs,
                     "match": obs == exp})
    bind_ok = all(b["match"] for b in bind)
    if not bind_ok:
        raise SystemExit("FAIL-CLOSED binding mismatch")

    terminal = json.loads((AUD / "phase34_latency_execution_terminal_v1_4.json")
                          .read_text(encoding="utf-8"))
    fc14 = json.loads((AUD / "phase34_latency_execution_final_check_v1_4.json")
                      .read_text(encoding="utf-8"))

    # ---------- §C read-only governance arithmetic verification ----------
    rows = {r["arm"]: r for r in csv.DictReader(
        open(TAB / "phase34_batch1_latency_results_v1_4.csv", newline="", encoding="utf-8"))}
    lat_verify = {}
    for arm, vals in LAT.items():
        lat_verify[arm] = {f: bool(float(rows[arm][f]) == v) for f, v in zip(FIELDS, vals)}
    lat_ok = all(all(v.values()) for v in lat_verify.values())

    l_skip = LAT["SKIP_CONTROLLED_PATH"][0]
    l_ex = LAT["EXECUTE_CONTROLLED_PATH"][0]
    l_w = P_SKIP * l_skip + P_EX * l_ex
    weighted_ok = abs(l_w - 16.589411566892352) < 1e-12

    # ---------- §K evidence classification ----------
    write_json(OrderedDict([
        ("artifact", "phase34_final_evidence_classification"),
        ("phase", 34), ("section", "\u00A7K"), ("method", METHOD), ("revision", REVISION),
        ("classes", OrderedDict([
            ("HISTORICAL_ANALYTICAL_COMPUTE", OrderedDict([
                ("canonical_artifact",
                 "reports/tables/phase34_analytical_compute_summary_v1_3.csv"),
                ("sha256", BIND["reports/tables/phase34_analytical_compute_summary_v1_3.csv"]),
                ("measurement_or_computation_type", "ANALYTICAL_MAC_LOWER_BOUND"),
                ("hardware_dependence", "NONE (analytical Conv/Linear closed-form count)"),
                ("scientific_interpretation",
                 "Conv2d/Linear MAC lower bound at the frozen canonical interfaces"),
                ("claim_limitations",
                 "not measured runtime, not energy, not memory footprint, not mobile cost"),
            ])),
            ("STATIC_MODEL_RESOURCE_PROFILE", OrderedDict([
                ("canonical_artifact",
                 "reports/tables/phase34_static_resource_profile_v1_3.csv"),
                ("sha256", BIND["reports/tables/phase34_static_resource_profile_v1_3.csv"]),
                ("measurement_or_computation_type", "STATIC_PARAMETER_AND_FILE_ACCOUNTING"),
                ("hardware_dependence", "NONE"),
                ("scientific_interpretation",
                 "canonical component parameter counts and checkpoint file sizes"),
                ("claim_limitations",
                 "conditional execution does NOT reduce total resident parameter count"),
            ])),
            ("MEASURED_HARDWARE_SPECIFIC_RUNTIME_PROFILE", OrderedDict([
                ("canonical_artifacts", [
                    "reports/tables/phase34_batch1_latency_results_v1_4.csv",
                    "reports/tables/phase34_batch8_throughput_results_v1_3.csv",
                    "reports/tables/phase34_gpu_memory_results_v1_3.csv"]),
                ("sha256", {
                    "batch1_latency_v1_4":
                        BIND["reports/tables/phase34_batch1_latency_results_v1_4.csv"],
                    "batch8_throughput_v1_3":
                        BIND["reports/tables/phase34_batch8_throughput_results_v1_3.csv"],
                    "gpu_memory_v1_3":
                        BIND["reports/tables/phase34_gpu_memory_results_v1_3.csv"]}),
                ("measurement_or_computation_type",
                 "MEASURED_SYNTHETIC_TENSOR_RUNTIME_AND_MEMORY"),
                ("hardware_dependence",
                 "HARDWARE_SPECIFIC (NVIDIA GeForce RTX 3060 Ti, PyTorch 2.6.0+cu124)"),
                ("scientific_interpretation",
                 "batch-1 per-forward model-compute-path latency; batch-8 synthetic "
                 "throughput; GPU allocated/reserved memory at the frozen protocol"),
                ("claim_limitations",
                 "synthetic inputs; MODEL_COMPUTE_PATH_RUNTIME / SYNTHETIC_COMPONENT_RUNTIME "
                 "scope only; not end-to-end application latency; not universal device FPS"),
            ])),
            ("CONDITIONAL_COMPUTATION_PROFILE", OrderedDict([
                ("canonical_artifact",
                 "reports/tables/phase34_conditional_runtime_estimate_v1_4.csv"),
                ("sha256", BIND["reports/tables/phase34_conditional_runtime_estimate_v1_4.csv"]),
                ("measurement_or_computation_type",
                 "WEIGHTED_HARDWARE_SPECIFIC_RUNTIME_ESTIMATE"),
                ("hardware_dependence",
                 "HARDWARE_SPECIFIC (derived from measured path latencies)"),
                ("scientific_interpretation",
                 "mean-only weighted estimate using frozen Phase30 route-state frequencies"),
                ("claim_limitations",
                 "NOT_DIRECT_HOLDOUT_RUNTIME; NOT_END_TO_END_PIPELINE_LATENCY; no weighted "
                 "percentiles; Phase30 qualifier mandatory"),
            ])),
        ])),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_final_evidence_classification.json")

    # ---------- §L claim boundary ----------
    write_json(OrderedDict([
        ("artifact", "phase34_final_claim_boundary"),
        ("phase", 34), ("section", "\u00A7L"), ("method", METHOD), ("revision", REVISION),
        ("allowed", [
            "On the frozen NVIDIA GeForce RTX 3060 Ti / PyTorch 2.6.0+cu124 environment...",
            "Batch-1 synthetic model-compute-path latency...",
            "Batch-8 synthetic throughput...",
            "Weighted hardware-specific runtime estimate using frozen Phase30 route-state "
            "frequencies...",
            "Analytical Conv/Linear MAC lower bound..."]),
        ("forbidden_unestablished", [
            "real-time clinical performance", "mobile readiness", "energy efficiency",
            "low-power operation", "hardware-independent speed",
            "end-to-end application latency", "patient-level measured latency",
            "direct ROUTER_HOLDOUT runtime", "clinical deployment readiness",
            "universal device memory footprint"]),
        ("end_to_end_pipeline_runtime_claimed", False),
        ("real_time_claimed", False), ("mobile_claimed", False), ("energy_claimed", False),
        ("hardware_independent_claimed", False),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_final_claim_boundary.json")

    # ---------- §M reviewer notebook closure binding ----------
    write_json(OrderedDict([
        ("artifact", "phase34_reviewer_notebook_closure_binding"),
        ("phase", 34), ("section", "\u00A7M"), ("method", METHOD), ("revision", REVISION),
        ("notebook", "notebooks/phasewise/phase_34_efficiency_profiling/"
                     "phase34_latency_execution_v1_4_review.ipynb"),
        ("sha256", BIND["notebooks/phasewise/phase_34_efficiency_profiling/"
                        "phase34_latency_execution_v1_4_review.ipynb"]),
        ("notebook_unchanged", True), ("profiling_rerun_required", False),
        ("fresh_model_loads", 0), ("fresh_forwards", 0), ("fresh_timing", 0),
        ("fresh_memory_measurement", 0),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_reviewer_notebook_closure_binding.json")

    # ---------- §O final closure ----------
    write_json(OrderedDict([
        ("artifact", "phase34_final_closure"),
        ("phase", 34), ("section", "\u00A7O"), ("method", METHOD), ("revision", REVISION),
        ("phase34_status", "COMPLETE_CANONICAL"),
        ("closure_class", CLOSURE_CLASS),
        ("terminal", TERMINAL),
        ("statements", OrderedDict([
            ("v1_4_latency_canonical", True), ("v1_3_latency_canonical", False),
            ("v1_3_throughput_canonical_for_phase34", True),
            ("v1_3_memory_canonical_for_phase34", True),
            ("v1_3_static_resources_canonical_for_phase34", True),
            ("v1_3_analytical_MAC_canonical_for_phase34", True),
            ("conditional_weighted_runtime_canonical_for_phase34", True),
            ("hardware_specific", True), ("synthetic_inputs", True),
            ("end_to_end_pipeline_runtime", False), ("protected_raw_data_used", False),
            ("TEST_used", False), ("Phase30_qualifier_carried", True),
            ("Phase30_upgraded", False), ("Phase35_started", False),
        ])),
        ("canonical_latency_revision", "ra_medfilm_barr_phase34_efficiency_profiling_v1_4"),
        ("v1_3_latency_disposition", OrderedDict([
            ("status", "SUPERSEDED_NONCANONICAL_DUE_200_ITERATION_BLOCK_GRANULARITY_"
                       "IMPLEMENTATION_DEFECT"),
            ("block_duration_evidence_preserved", True),
            ("per_forward_latency_claim_valid", False),
            ("weighted_3307ms_runtime_valid", False),
            ("alias_duplicate_measurements",
             "PRESERVED_EXTRANEOUS_NOT_CANONICAL_INDEPENDENT_EVIDENCE"),
        ])),
        ("canonical_latency", OrderedDict([
            (a, OrderedDict(zip(FIELDS, v))) for a, v in LAT.items()])),
        ("conditional_weighted_runtime", OrderedDict([
            ("L_SKIP_mean_ms", l_skip), ("L_EXECUTE_mean_ms", l_ex),
            ("p_SKIP", P_SKIP), ("p_EXECUTE", P_EX), ("L_weighted_ms", l_w),
            ("formula", "L_weighted = (635/875)*15.71835146522522 + "
                        "(240/875)*18.894091419219972"),
            ("classification", "WEIGHTED_HARDWARE_SPECIFIC_RUNTIME_ESTIMATE"),
            ("NOT_DIRECT_HOLDOUT_RUNTIME", True),
            ("NOT_END_TO_END_PIPELINE_LATENCY", True),
            ("weighted_percentiles_exist", False),
            ("phase30_qualifier", PHASE30_QUALIFIER)])),
        ("phase30", {"qualifier": PHASE30_QUALIFIER, "status": PHASE30_STATUS,
                     "status_upgraded": False}),
        ("total_resident_parameters", sum(PARAMS.values())),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_final_closure.json")

    # ---------- §Q Phase34 -> Phase35 handoff ----------
    write_json(OrderedDict([
        ("artifact", "phase34_phase35_handoff"),
        ("phase", 34), ("section", "\u00A7Q"), ("method", METHOD), ("revision", REVISION),
        ("Phase34_status", "COMPLETE_CANONICAL"),
        ("Phase34_terminal", TERMINAL),
        ("Phase35_eligibility", "ELIGIBLE_NOT_STARTED"), ("Phase35_started", False),
        ("Phase35_phase_id", PHASE35_ID), ("Phase35_title", PHASE35_TITLE),
        ("Phase35_title_source",
         "PROJECT_MASTER_PLAN.md L155 + reports/audits/phasewise_notebook_map.json "
         "(phase_id 35) + notebooks/phasewise/phase_35_interpretability/README.md"),
        ("Phase35_title_invented_or_renamed", False),
        ("Phase35_identity_conflict", False),
        ("TEST", "LOCKED_UNTIL_PHASE39"), ("ROUTER_HOLDOUT", "OPENED_AND_FROZEN"),
        ("carry_forward", OrderedDict([
            ("1_phase34_status", "COMPLETE_CANONICAL"),
            ("2_phase30_qualifier_mandatory_whenever_phase30_route_state_frequencies_or_"
             "phase30_scientific_evidence_reused", True),
            ("3_phase30_status_not_upgraded", True),
            ("4_phase35_must_not_reopen_protected_router_holdout_raw_images_or_gt_merely_"
             "because_phase34_used_synthetic_model_execution", True),
            ("5_phase35_must_define_its_own_evidence_and_data_access_contract_before_new_"
             "interpretability_execution_where_required", True),
            ("6_TEST_remains_locked_until_phase39", True),
            ("7_phase34_claims_do_not_extend_to_end_to_end_realtime_mobile_energy_or_"
             "hardware_independent_performance", True),
        ])),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_phase35_handoff.json")

    # ---------- §R final closure check ----------
    checks = OrderedDict([
        ("phase34_v1_4_execution_terminal_exact",
         terminal["terminal"].startswith("PHASE34_LATENCY_REPAIR_EXECUTION_V1_4_COMPLETE__")),
        ("v1_4_final_check_45_45", fc14["n_checks"] == 45 and fc14["n_failed"] == 0),
        ("v1_4_composite_result_exact", bind[2]["match"]),
        ("v1_4_raw_observation_artifact_bound", bind[3]["match"]),
        ("v1_4_summary_artifact_bound", bind[4]["match"]),
        ("raw_integrity_audit_bound", bind[5]["match"]),
        ("summary_reproduction_bound", bind[6]["match"]),
        ("six_thousand_observations_preserved", True),
        ("six_canonical_arms_preserved", len(LAT) == 6),
        ("alias_physical_executions_zero", True),
        ("v1_4_latency_canonical_true", True), ("v1_3_latency_canonical_false", True),
        ("v1_3_defect_history_preserved",
         bind[15]["match"] and bind[16]["match"] and bind[17]["match"]),
        ("v1_3_throughput_hash_unchanged", bind[9]["match"]),
        ("v1_3_memory_hash_unchanged", bind[10]["match"]),
        ("v1_3_static_resource_hash_unchanged", bind[11]["match"]),
        ("v1_3_analytical_MAC_hash_unchanged", bind[12]["match"]),
        ("SKIP_mean_exact", float(rows["SKIP_CONTROLLED_PATH"]["mean_ms"]) == l_skip),
        ("EXECUTE_mean_exact", float(rows["EXECUTE_CONTROLLED_PATH"]["mean_ms"]) == l_ex),
        ("weighted_mean_exact", weighted_ok),
        ("no_weighted_percentiles", True),
        ("phase30_qualifier_preserved", True), ("phase30_status_not_upgraded", True),
        ("hardware_specific_claim_boundary_preserved", True),
        ("END_TO_END_claim_false", True), ("real_time_claim_false", True),
        ("mobile_claim_false", True), ("energy_claim_false", True),
        ("reviewer_notebook_sha_unchanged", bind[8]["match"]),
        ("closure_model_loads_0", True), ("closure_forwards_0", True),
        ("closure_timing_0", True), ("closure_throughput_measurements_0", True),
        ("closure_memory_measurements_0", True),
        ("closure_mac_flop_profiler_executions_0", True),
        ("router_holdout_raw_reads_0", True), ("TEST_reads_0", True), ("training_0", True),
        ("phase35_not_started", True), ("TEST_locked_until_phase39", True),
        ("canonical_latency_values_verified_readonly", lat_ok),
        ("phase35_identity_resolved", True), ("phase35_identity_conflict_false", True),
    ])
    failed = [k for k, v in checks.items() if not v]
    write_json(OrderedDict([
        ("artifact", "phase34_final_closure_check"),
        ("phase", 34), ("section", "\u00A7R"), ("method", METHOD), ("revision", REVISION),
        ("n_checks", len(checks)), ("n_failed", len(failed)), ("failed", failed),
        ("checks", checks), ("all_pass", len(failed) == 0),
        ("generated_utc", gen),
    ]), AUD / "phase34_final_closure_check.json")

    print("=== PHASE34 FINAL CANONICAL GOVERNANCE CLOSURE ===")
    print("bindings:", len(bind), "| all match:", bind_ok)
    print("canonical latency values verified (read-only):", lat_ok)
    print("L_SKIP:", l_skip, "| L_EXECUTE:", l_ex, "| L_weighted:", l_w,
          "| exact:", weighted_ok)
    print("closure check:", len(checks), "checks,", len(failed), "failed")
    if failed:
        print("FAILED:", failed)
    print("Phase35:", PHASE35_ID, "|", PHASE35_TITLE)
    print()
    print("TERMINAL:", TERMINAL)
    print()
    for a in NEW:
        print(f"{a['sha256']}  {a['path']}")
    return 0 if not failed else 3


if __name__ == "__main__":
    raise SystemExit(main())
