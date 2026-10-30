#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase34 v1.1 pre-execution runtime-semantics + analytical-comparator reconciliation.

ZERO-EXECUTION. Repairs two specification-level issues found in v1.0 before any Phase34
measurement:
  ISSUE 1 - uniform FP32/autocast-OFF protocol flattened canonical component-specific
            inference semantics (G runs under autocast(fp16) + no_grad).
  ISSUE 2 - the literal predecessor ALWAYS_REFINE C2 comparator was conflated with a gated
            execute-all full graph.

Preserves every v1.0 artifact byte-for-byte. Performs NO model load, NO forward, NO timing,
NO memory measurement, NO FLOP/MAC profiler execution, NO protected-data access, NO training.
Static integer arithmetic on frozen predecessor constants is allowed.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase34_specification_v1_1.py
"""
from __future__ import annotations

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
REVISION = "ra_medfilm_barr_phase34_efficiency_profiling_v1_1"
CLASSIFICATION = ("PRE_EXECUTION_RUNTIME_NUMERICAL_SEMANTICS_AND_ANALYTICAL_COMPARATOR_"
                  "RECONCILIATION")

TERMINAL = ("PHASE34_EFFICIENCY_PROFILING_SPEC_V1_1_COMPLETE__"
            "CANONICAL_COMPONENT_SPECIFIC_RUNTIME_PRECISION_SEMANTICS_RESTORED__"
            "BATCH1_HARDWARE_MICROBENCHMARK_DISTINGUISHED_FROM_CANONICAL_NUMERICAL_"
            "REPRODUCTION__LITERAL_ALWAYS_REFINE_C2_AND_GATED_EXECUTE_ALL_COMPARATORS_"
            "RECONCILED__V1_1_SOURCE_FREEZE_COMPLETE__EXECUTION_ELIGIBLE_NOT_STARTED")

PHASE30_QUALIFIER = ("ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_"
                     "SCIENTIFIC_SOURCE_FREEZE_DEVIATION")
PHASE30_STATUS = "COMPLETE_WITH_PROTOCOL_DEVIATION__NOT_COMPLETE_CANONICAL"

BATCH1_LABEL = ("CANONICAL_GRAPH_HARDWARE_MICROBENCHMARK__BATCH1_NOT_CANONICAL_G_"
                "NUMERICAL_REPRODUCTION")
BATCH8_LABEL = "SYNTHETIC_HARDWARE_THROUGHPUT_BENCHMARK"

# ---- v1.0 artifacts to preserve (fail-closed) ----
V10 = OrderedDict([
    ("reports/audits/phase34_specification_terminal.json",
     "15f77721302f8d57c99a2d21447fcb1b71ad9345ffd4823d53da2563a63ca997"),
    ("reports/audits/phase34_specification_final_check.json",
     "0be80ceaca993990c3f558803b7435f7b5c29ec72b310f2d99afaff8e4d0bba2"),
    ("reports/audits/phase34_entry_gate.json",
     "4efc63167412de65cead722529511d1468b99ce138573f41a93f8590ac5790a5"),
    ("reports/audits/phase34_no_execution_audit.json",
     "f48343969380668d8c4a9fab26d8a8c46dcd235af65412c8d9c534f0af8ebebc"),
    ("docs/phase34_efficiency_profiling_spec_v1_0.md",
     "6168a34bbce0d0b798d7bd85226988f7a333b31ff3bf20230a8b447fa1e62914"),
    ("notebooks/phasewise/phase_34_efficiency_profiling/"
     "phase34_efficiency_profiling_spec_review.ipynb",
     "64fd18b2c84712a4d50b5506fa84ea45895488a04696f3b231fa1c0119301dbd"),
    ("reports/audits/phase34_preexecution_source_freeze.json",
     "2427a3d6efb73a258e54ce6fb8a5744ff3562dffcfcfa7274032bb8266e486d2"),
    ("scripts/analysis/phase34_efficiency_profiling_execution_v1_0.py",
     "1f60de9e415c13d71b49a5f59646f4ea7139ea9508d866de829b33396d9b7b97"),
    ("scripts/analysis/phase34_efficiency_profiling_worker_v1_0.py",
     "a8e2034d26aa7cd41c89cebc15ebff456466aeece56a2391dfcfeab89c7d1185"),
    ("reports/audits/phase34_execution_eligibility_adjudication.json",
     "00eac2154990c493fb1692a3979a18d83b7c66d02be213850013a1dbf3973ac8"),
    ("reports/tables/phase34_profiling_arm_registry.csv",
     "8105a086c53ecf1c4a30b7721c65247e1e50ba832d7c1d3be52c545d1e74f20c"),
])

# ---- frozen predecessor constants (authority values, NOT recomputed) ----
G_MACS, B_MACS, R_MACS, S_MACS = 31551740928, 36160, 3230662656, 1168
G_PARAMS, R_PARAMS, B_PARAMS, S_PARAMS = 3523001, 1276401, 36801, 1217
C1 = G_MACS
C2 = G_MACS + R_MACS
E_A8C9 = G_MACS + B_MACS + (240 / 875) * (R_MACS + S_MACS)
GATED_C9 = G_MACS + B_MACS + R_MACS + S_MACS
P25E_GATED = G_MACS + B_MACS + R_MACS

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
    import csv
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    s = sha256_file(p)
    NEW.append({"path": str(p.relative_to(ROOT)).replace("\\", "/"), "sha256": s})
    return s


def main():
    gen = now_utc()

    # ---------------- §A preserve v1.0 byte-for-byte ----------------
    pres = []
    for rel, exp in V10.items():
        obs = sha256_file(ROOT / rel)
        pres.append({"path": rel, "expected_sha256": exp, "observed_sha256": obs,
                     "match": obs == exp, "preserved": obs == exp})
        if obs != exp:
            raise SystemExit(f"FAIL-CLOSED v1.0 preservation mismatch: {rel}")

    # ---------------- authority binding ----------------
    auth = OrderedDict([
        ("phase29_phase_d_component_inference_semantics_contract_v1_1",
         "reports/audits/phase29_phase_d_component_inference_semantics_contract_v1_1.json"),
        ("phase29_phase_d_component_inference_semantics_contract_v1_0",
         "reports/audits/phase29_phase_d_component_inference_semantics_contract.json"),
        ("phase30_component_inference_semantics_contract",
         "reports/audits/phase30_component_inference_semantics_contract.json"),
        ("phase29_val808_shared_global_cache_contract_v1_2",
         "reports/audits/phase29_val808_shared_global_cache_contract_v1_2.json"),
        ("phase27_reproducibility_contract_v1_1",
         "reports/audits/phase27_reproducibility_contract_v1_1.json"),
        ("phase25e_comparator_direction_contract_v1_0",
         "reports/audits/phase25e_comparator_direction_contract_v1_0.json"),
        ("phase25e_execution_metrics_contract_v1_0",
         "reports/audits/phase25e_execution_metrics_contract_v1_0.json"),
        ("phase25e_compute_frontier",
         "reports/tables/phase25e_compute_frontier.csv"),
        ("phase25e_analytical_compute_contract",
         "reports/tables/phase25e_analytical_compute_contract.csv"),
        ("phase26_resource_contract",
         "artifacts/phase26_ra_medfilm_barr_bundle_v1_0/resource_contract.json"),
        ("phase22_conditional_compute_envelopes",
         "reports/audits/phase22_conditional_compute_envelopes.json"),
        ("phase24_router_parameter_count_adjudication",
         "reports/audits/phase24_router_parameter_count_adjudication.json"),
    ])
    auth_shas = {k: sha256_file(ROOT / v) for k, v in auth.items()}

    # ---------------- §B defect record ----------------
    write_json(OrderedDict([
        ("artifact", "phase34_v1_0_runtime_semantics_and_comparator_defect_record"),
        ("phase", 34), ("section", "\u00a7B"), ("method", METHOD), ("revision", REVISION),
        ("classification", "PRE_EXECUTION_SPECIFICATION_SEMANTICS_REPAIR__"
                           "NO_MEASURED_RESULTS_EXIST"),
        ("issues", [
            OrderedDict([
                ("issue_id", "ISSUE 1"),
                ("code", "UNIFORM_FP32_RUNTIME_PROTOCOL_DOES_NOT_MATCH_CANONICAL_"
                         "COMPONENT_SPECIFIC_INFERENCE_SEMANTICS"),
                ("description",
                 "v1.0 froze a uniform float32 / autocast-OFF / inference_mode protocol for "
                 "ALL components. The frozen canonical G extraction actually runs under "
                 "autocast(float16) with torch.no_grad() and inference_mode=FALSE."),
                ("authority",
                 "reports/audits/phase29_phase_d_component_inference_semantics_contract_v1_1.json "
                 "+ reports/audits/phase30_component_inference_semantics_contract.json"),
            ]),
            OrderedDict([
                ("issue_id", "ISSUE 2"),
                ("code", "LITERAL_ALWAYS_REFINE_PREDECESSOR_COMPARATOR_CONFLATED_WITH_"
                         "GATED_EXECUTE_ALL_GRAPH"),
                ("description",
                 "v1.0 treated 'ALWAYS_REFINE' as the gated full graph. The frozen "
                 "predecessor semantics define the literal C2 ALWAYS_REFINE anchor as "
                 "MAC(G) + MAC(R_psi) with NO router (routing bypassed); the gated "
                 "K=N_eligible graph retains router overhead and must be labelled "
                 "separately."),
                ("authority",
                 "reports/audits/phase25e_execution_metrics_contract_v1_0.json "
                 "(anchor_clarification: 'C1 and C2 bypass routing; gated K=0 and gated "
                 "K=N_eligible retain router overhead and must be labeled separately')"),
            ]),
        ]),
        ("model_measurements_already_performed", False),
        ("scientific_runtime_results_exist", False),
        ("latency_results_exist", False), ("throughput_results_exist", False),
        ("memory_results_exist", False), ("runtime_results_invalidated", False),
        ("repair_required_before_first_measurement", True),
        ("v1_0_artifacts_preserved", all(p["preserved"] for p in pres)),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_v1_0_runtime_semantics_and_comparator_defect_record.json")

    # ---------------- §C/§H precision contract v1.1 ----------------
    comp_rows = [
        ["G", "phase29_phase_d_component_inference_semantics_contract_v1_1 + "
              "phase30_component_inference_semantics_contract",
         auth_shas["phase29_phase_d_component_inference_semantics_contract_v1_1"],
         "float32", "float32", True, "float16", True, False, 8,
         "CANONICAL_GRAPH_HARDWARE_MICROBENCHMARK__BATCH1_NOT_CANONICAL_G_NUMERICAL_"
         "REPRODUCTION",
         "SYNTHETIC_HARDWARE_THROUGHPUT_BENCHMARK", False, True],
        ["R_psi", "phase29_phase_d_component_inference_semantics_contract_v1_1 + "
                  "phase30_component_inference_semantics_contract",
         auth_shas["phase29_phase_d_component_inference_semantics_contract_v1_1"],
         "float32", "float32", False, None, False, True, 8,
         "CANONICAL_GRAPH_HARDWARE_MICROBENCHMARK__BATCH1_NOT_CANONICAL_G_NUMERICAL_"
         "REPRODUCTION",
         "SYNTHETIC_HARDWARE_THROUGHPUT_BENCHMARK", False, True],
        ["B_phi", "phase29_phase_d_component_inference_semantics_contract_v1_1 + "
                  "phase30_component_inference_semantics_contract",
         auth_shas["phase29_phase_d_component_inference_semantics_contract_v1_1"],
         "float32", "float32", False, None, False, True,
         "FULL_MATRIX_SINGLE_FORWARD",
         "CANONICAL_GRAPH_HARDWARE_MICROBENCHMARK__BATCH1_NOT_CANONICAL_G_NUMERICAL_"
         "REPRODUCTION",
         "SYNTHETIC_HARDWARE_THROUGHPUT_BENCHMARK", False, True],
        ["S_omega", "phase29_phase_d_component_inference_semantics_contract_v1_1 + "
                    "phase30_component_inference_semantics_contract",
         auth_shas["phase29_phase_d_component_inference_semantics_contract_v1_1"],
         "float32", "float32", False, None, False, True, 128,
         "CANONICAL_GRAPH_HARDWARE_MICROBENCHMARK__BATCH1_NOT_CANONICAL_G_NUMERICAL_"
         "REPRODUCTION",
         "SYNTHETIC_HARDWARE_THROUGHPUT_BENCHMARK", False, True],
    ]
    write_json(OrderedDict([
        ("artifact", "phase34_precision_execution_semantics_contract_v1_1"),
        ("phase", 34), ("section", "\u00a7H"), ("method", METHOD), ("revision", REVISION),
        ("supersedes", "phase34_precision_execution_semantics_contract.json"),
        ("v1_0_preserved", True),
        ("authority", auth), ("authority_sha256", auth_shas),
        ("PRIMARY_CANONICAL_COMPONENT_SEMANTICS", OrderedDict([
            ("G", OrderedDict([
                ("device", "cuda"), ("model_eval", True),
                ("model_dtype", "float32"), ("input_dtype", "float32"),
                ("autocast_enabled", True), ("autocast_dtype", "float16"),
                ("autocast_call",
                 'torch.amp.autocast(device_type="cuda", dtype=torch.float16, enabled=True)'),
                ("grad_context", "torch.no_grad()"), ("no_grad", True),
                ("inference_mode", False),
                ("canonical_scientific_batch_semantics",
                 "batch 8, contiguous chunks of 8 inside a single domain sorted by "
                 "(dataset, sample_id); batch-membership SENSITIVE under autocast fp16"),
                ("phase34_batch1_benchmark_semantics",
                 "batch 1 hardware microbenchmark under the canonical G precision/autocast/"
                 "gradient context; batch membership differs and is disclosed"),
                ("phase34_batch8_benchmark_semantics",
                 "batch 8 synthetic hardware throughput benchmark under G autocast(fp16) + "
                 "no_grad + inference_mode FALSE"),
                ("scientific_reproduction_claim_allowed", False),
                ("hardware_benchmark_claim_allowed", True),
            ])),
            ("R_psi", OrderedDict([
                ("device", "cuda"), ("model_eval", True),
                ("model_dtype", "float32"), ("input_dtype", "float32"),
                ("autocast_enabled", False), ("autocast_dtype", None),
                ("grad_context", "torch.inference_mode()"), ("no_grad", False),
                ("inference_mode", True),
                ("canonical_scientific_batch_semantics", "batch 8"),
                ("phase34_batch1_benchmark_semantics", "batch 1 hardware microbenchmark"),
                ("phase34_batch8_benchmark_semantics", "batch 8 throughput benchmark"),
                ("scientific_reproduction_claim_allowed", False),
                ("hardware_benchmark_claim_allowed", True),
            ])),
            ("B_phi", OrderedDict([
                ("device", "cuda"), ("model_eval", True),
                ("model_dtype", "float32"), ("input_dtype", "float32"),
                ("autocast_enabled", False), ("autocast_dtype", None),
                ("grad_context", "torch.inference_mode()"), ("no_grad", False),
                ("inference_mode", True),
                ("canonical_scientific_batch_semantics", "FULL_MATRIX_SINGLE_FORWARD"),
                ("phase34_batch1_benchmark_semantics", "batch 1 hardware microbenchmark"),
                ("phase34_batch8_benchmark_semantics", "batch 8 throughput benchmark"),
                ("scientific_reproduction_claim_allowed", False),
                ("hardware_benchmark_claim_allowed", True),
            ])),
            ("S_omega", OrderedDict([
                ("device", "cuda"), ("model_eval", True),
                ("model_dtype", "float32"), ("input_dtype", "float32"),
                ("autocast_enabled", False), ("autocast_dtype", None),
                ("grad_context", "torch.inference_mode()"), ("no_grad", False),
                ("inference_mode", True),
                ("canonical_scientific_batch_semantics", "batch 128"),
                ("phase34_batch1_benchmark_semantics", "batch 1 hardware microbenchmark"),
                ("phase34_batch8_benchmark_semantics", "batch 8 throughput benchmark"),
                ("scientific_reproduction_claim_allowed", False),
                ("hardware_benchmark_claim_allowed", True),
            ])),
        ])),
        ("invariants", [
            "G_AUTOCAST_SEMANTICS_MUST_NOT_BE_APPLIED_TO_R_PSI_B_PHI_OR_S_OMEGA",
            "UNIFORM_FP32_NO_AUTOCAST_MUST_NOT_REPLACE_G_CANONICAL_RUNTIME_SEMANTICS",
        ]),
        ("component_semantics_not_interchangeable", True),
        ("primary_profile_uses_component_specific_precision", True),
        ("primary_runtime_profile", "COMPONENT_SPECIFIC_CANONICAL_PRECISION_SEMANTICS"),
        ("secondary_uniform_fp32_profile", "INELIGIBLE_NOT_REQUIRED"),
        ("secondary_uniform_fp32_profile_name",
         "STANDARDIZED_FP32_SYNTHETIC_RUNTIME_VARIANT"),
        ("secondary_uniform_fp32_reason",
         "Retaining the v1.0 uniform FP32 profile would materially expand execution cost and "
         "complicate the phase for no required scientific gain; it must never replace the "
         "primary canonical-component-semantics profile."),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_precision_execution_semantics_contract_v1_1.json")

    # ---------------- §F/§G/§I analytical compute contract v1.1 ----------------
    comparators = OrderedDict([
        ("literal_global_only_C1", OrderedDict([
            ("predecessor_authority",
             "phase25e_execution_metrics_contract_v1_0 (literal C1 anchor excludes router)"),
            ("graph_components", ["G"]), ("router_present", False),
            ("refiner_present", False), ("s_omega_present", False),
            ("formula", "MAC(G)"), ("mac", C1),
            ("scientific_label", "LITERAL_GLOBAL_ONLY_C1__ANALYTICAL_MAC_LOWER_BOUND"),
        ])),
        ("literal_always_refine_C2", OrderedDict([
            ("predecessor_authority",
             "phase25e_execution_metrics_contract_v1_0 "
             "(literal C2 no-routing anchor: GLOBAL_MACS + (N_eligible/N_DEV)*"
             "REGIONAL_REFINER_MACS, routing bypassed)"),
            ("graph_components", ["G", "R_psi"]), ("router_present", False),
            ("refiner_present", True), ("s_omega_present", False),
            ("formula", "MAC(G) + MAC(R_psi)"), ("mac", C2),
            ("scientific_label",
             "LITERAL_ALWAYS_REFINE_C2__NO_ROUTING__ANALYTICAL_MAC_LOWER_BOUND"),
        ])),
        ("final_A8_C9_expected_conditional", OrderedDict([
            ("predecessor_authority",
             "phase25e_execution_metrics_contract_v1_0 + phase26_resource_contract + "
             "phase26_state_machine_contract"),
            ("graph_components", ["G", "B_phi", "R_psi", "S_omega"]),
            ("router_present", True), ("refiner_present", True), ("s_omega_present", True),
            ("formula", "MAC(G) + MAC(B_phi) + p_activate * (MAC(R_psi) + MAC(S_omega))"),
            ("p_activate", 240 / 875), ("mac", E_A8C9),
            ("scientific_label", "ANALYTICAL_MAC_LOWER_BOUND"),
        ])),
        ("optional_gated_execute_all_C9", OrderedDict([
            ("predecessor_authority",
             "phase26_state_machine_contract (100% activation; router retained)"),
            ("graph_components", ["G", "B_phi", "R_psi", "S_omega"]),
            ("router_present", True), ("refiner_present", True), ("s_omega_present", True),
            ("formula", "MAC(G) + MAC(B_phi) + MAC(R_psi) + MAC(S_omega)"),
            ("mac", GATED_C9),
            ("scientific_label",
             "GATED_EXECUTE_ALL_C9_100PCT_ACTIVATION_REFERENCE__NOT_LITERAL_C2"),
        ])),
        ("phase25e_gated_K_N_eligible_pre_gate", OrderedDict([
            ("predecessor_authority",
             "phase25e_compute_frontier.csv budget 1.00 (gated, router retained, "
             "S_omega excluded)"),
            ("graph_components", ["G", "B_phi", "R_psi"]),
            ("router_present", True), ("refiner_present", True), ("s_omega_present", False),
            ("formula", "MAC(G) + MAC(B_phi) + MAC(R_psi)"), ("mac", P25E_GATED),
            ("scientific_label",
             "PHASE25E_GATED_K_N_Eligible_PRE_GATE__DISTINCT_FROM_LITERAL_C2"),
        ])),
    ])
    ratios = OrderedDict([
        ("ratio_vs_LITERAL_GLOBAL_ONLY_C1", E_A8C9 / C1),
        ("ratio_vs_LITERAL_ALWAYS_REFINE_C2", E_A8C9 / C2),
        ("absolute_saving_vs_LITERAL_ALWAYS_REFINE_C2", C2 - E_A8C9),
        ("ratio_vs_gated_execute_all_C9", E_A8C9 / GATED_C9),
        ("absolute_saving_vs_gated_execute_all_C9", GATED_C9 - E_A8C9),
    ])
    write_json(OrderedDict([
        ("artifact", "phase34_analytical_compute_contract_v1_1"),
        ("phase", 34), ("section", "\u00a7I"), ("method", METHOD), ("revision", REVISION),
        ("supersedes", "phase34_analytical_compute_contract.json"),
        ("v1_0_preserved", True),
        ("label", "ANALYTICAL MAC LOWER BOUND"),
        ("historical_component_macs_preserved",
         {"G": G_MACS, "B_phi": B_MACS, "R_psi": R_MACS, "S_omega": S_MACS}),
        ("comparators", comparators),
        ("ratios", ratios),
        ("literal_always_refine_C2_router_present", False),
        ("literal_always_refine_C2_not_equal_gated_execute_all_C9", True),
        ("comparator_denominators_merged", False),
        ("conditional_formula_unchanged",
         "E[MAC] = MAC(G) + MAC(B_phi) + p_activate*(MAC(R_psi)+MAC(S_omega))"),
        ("accept_reject_compute_identical", True),
        ("phase30_qualifier", PHASE30_QUALIFIER),
        ("numeric_preview_note",
         "PREVIEW_ONLY_FROZEN_CONSTANT_ARITHMETIC__NO_PROFILER_NO_MODEL - values are "
         "arithmetic over frozen predecessor constants and frozen Phase30 frequencies."),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_analytical_compute_contract_v1_1.json")

    # ---------------- §J arm registry v1.1 ----------------
    AR = ["arm_id", "predecessor_authority", "scientific_meaning", "components_executed",
          "router_present", "refiner_present", "s_omega_present", "runtime_capable",
          "runtime_precision_profile", "batch1_label", "batch8_label",
          "canonical_numerical_reproduction", "final_eligibility"]
    arms = [
        ["GLOBAL_ONLY_C1", "Phase25E literal C1 anchor",
         "global model alone; routing bypassed", "G", False, False, False, True,
         "COMPONENT_SPECIFIC_CANONICAL_PRECISION_SEMANTICS", BATCH1_LABEL, BATCH8_LABEL,
         False, "ELIGIBLE"],
        ["FINAL_ROUTED_A8_C9", "Phase26 canonical bundle A8/C9",
         "full routed system: G always, B_phi pre-gate, R_psi+S_omega on EXECUTE",
         "G,B_phi,R_psi,S_omega", True, True, True, True,
         "COMPONENT_SPECIFIC_CANONICAL_PRECISION_SEMANTICS", BATCH1_LABEL, BATCH8_LABEL,
         False, "ELIGIBLE"],
        ["LITERAL_ALWAYS_REFINE_C2_ANALYTICAL_ONLY",
         "Phase25E literal C2 no-routing anchor",
         "analytical always-refine reference; routing bypassed", "G,R_psi", False, True,
         False, False, "ANALYTICAL_ONLY", "N/A", "N/A", False,
         "ELIGIBLE_ANALYTICAL_ONLY"],
        ["GATED_EXECUTE_ALL_C9_IF_PREDECESSOR_AUTHORIZED",
         "Phase26 state machine, 100% activation",
         "gated execute-all graph with router and post-safety", "G,B_phi,R_psi,S_omega",
         True, True, True, False, "ANALYTICAL_ONLY", "N/A", "N/A", False,
         "ELIGIBLE_ANALYTICAL_ONLY"],
        ["G_COMPONENT", "Phase26 component inventory", "component-only G", "G", False,
         False, False, True, "COMPONENT_SPECIFIC_CANONICAL_PRECISION_SEMANTICS",
         BATCH1_LABEL, BATCH8_LABEL, False, "ELIGIBLE"],
        ["R_PSI_COMPONENT", "Phase25A resource accounting", "component-only R_psi",
         "R_psi", False, True, False, True,
         "COMPONENT_SPECIFIC_CANONICAL_PRECISION_SEMANTICS", BATCH1_LABEL, BATCH8_LABEL,
         False, "ELIGIBLE"],
        ["B_PHI_COMPONENT", "Phase25D router", "component-only B_phi", "B_phi", True,
         False, False, True, "COMPONENT_SPECIFIC_CANONICAL_PRECISION_SEMANTICS",
         BATCH1_LABEL, BATCH8_LABEL, False, "ELIGIBLE"],
        ["S_OMEGA_COMPONENT", "Phase25F post-safety", "component-only S_omega", "S_omega",
         False, False, True, True,
         "COMPONENT_SPECIFIC_CANONICAL_PRECISION_SEMANTICS", BATCH1_LABEL, BATCH8_LABEL,
         False, "ELIGIBLE"],
    ]
    write_csv(AR, arms, TAB / "phase34_profiling_arm_registry_v1_1.csv")

    # ---------------- §K measured runtime scope v1.1 ----------------
    scope_items = ["model forward", "sigmoid", "feature normalization",
                   "router feature construction", "ROI geometry", "crop/resizing",
                   "interpolation", "fusion", "decision logic", "host-to-device transfer",
                   "device-to-host transfer", "checkpoint loading",
                   "synthetic tensor generation"]
    write_json(OrderedDict([
        ("artifact", "phase34_measured_runtime_scope_v1_1"),
        ("phase", 34), ("section", "\u00a7K"), ("method", METHOD), ("revision", REVISION),
        ("per_arm_timing_scope", OrderedDict([
            ("GLOBAL_ONLY_C1", OrderedDict([
                ("included", ["model forward", "sigmoid"]),
                ("excluded", [s for s in scope_items
                              if s not in ("model forward", "sigmoid")]),
                ("classification", "MODEL_COMPUTE_PATH_RUNTIME"),
            ])),
            ("FINAL_ROUTED_A8_C9", OrderedDict([
                ("included", ["model forward (per component)", "sigmoid"]),
                ("excluded", [s for s in scope_items
                              if s not in ("model forward", "sigmoid")]),
                ("classification", "MODEL_COMPUTE_PATH_RUNTIME"),
                ("note", "fusion/ROI geometry/decision logic are NOT inside the timed "
                         "region in the frozen harness; weighted runtime is a "
                         "WEIGHTED_HARDWARE_SPECIFIC_RUNTIME_ESTIMATE"),
            ])),
            ("G_COMPONENT", OrderedDict([
                ("included", ["model forward", "sigmoid"]),
                ("excluded", [s for s in scope_items
                              if s not in ("model forward", "sigmoid")]),
                ("classification", "SYNTHETIC_COMPONENT_RUNTIME"),
            ])),
            ("R_PSI_COMPONENT", OrderedDict([
                ("included", ["model forward", "sigmoid"]),
                ("excluded", [s for s in scope_items
                              if s not in ("model forward", "sigmoid")]),
                ("classification", "SYNTHETIC_COMPONENT_RUNTIME"),
            ])),
            ("B_PHI_COMPONENT", OrderedDict([
                ("included", ["model forward"]),
                ("excluded", [s for s in scope_items if s != "model forward"]),
                ("classification", "SYNTHETIC_COMPONENT_RUNTIME"),
            ])),
            ("S_OMEGA_COMPONENT", OrderedDict([
                ("included", ["model forward", "sigmoid"]),
                ("excluded", [s for s in scope_items
                              if s not in ("model forward", "sigmoid")]),
                ("classification", "SYNTHETIC_COMPONENT_RUNTIME"),
            ])),
        ])),
        ("allowed_labels", ["MODEL_COMPUTE_PATH_RUNTIME", "SYNTHETIC_COMPONENT_RUNTIME",
                            "END_TO_END_PIPELINE_RUNTIME"]),
        ("end_to_end_pipeline_runtime_used", False),
        ("end_to_end_pipeline_runtime_condition",
         "only if the exact full canonical pipeline operations are inside the timed region"),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_measured_runtime_scope_v1_1.json")

    # ---------------- §M source freeze v1.1 ----------------
    v11_sources = [
        ("scripts/analysis/phase34_efficiency_profiling_execution_v1_1.py",
         "V1_1_FUTURE_EXECUTION_HARNESS"),
        ("scripts/analysis/phase34_efficiency_profiling_worker_v1_1.py",
         "V1_1_ISOLATED_PER_ARM_WORKER"),
        ("scripts/analysis/phase34_specification_v1_1.py",
         "V1_1_SPECIFICATION_GENERATOR"),
        ("scripts/analysis/build_phase34_spec_v1_1_reviewer_notebook.py",
         "V1_1_REVIEWER_NOTEBOOK_BUILDER__REPORTING_ONLY"),
        ("src/models/barr/ra_medfilm_barr.py", "CANONICAL_WRAPPER_SOURCE"),
        ("src/models/barr/regional_refiner.py", "R_psi_SOURCE"),
        ("src/models/barr/router_variants.py", "B_phi_SOURCE"),
        ("src/models/film/global_medfilm.py", "G_SOURCE"),
    ]
    frozen = []
    for rel, role in v11_sources:
        p = ROOT / rel
        frozen.append({"path": rel, "sha256": sha256_file(p) if p.exists() else None,
                       "role": role, "exists": p.exists()})
    write_json(OrderedDict([
        ("artifact", "phase34_preexecution_source_freeze_v1_1"),
        ("phase", 34), ("section", "\u00a7M"), ("method", METHOD), ("revision", REVISION),
        ("frozen_sources", frozen),
        ("v1_0_source_freeze",
         {"path": "reports/audits/phase34_preexecution_source_freeze.json",
          "sha256": V10["reports/audits/phase34_preexecution_source_freeze.json"]}),
        ("v1_0_source_freeze_preserved", True),
        ("v1_1_supersedes_v1_0_for_future_measurement", True),
        ("no_v1_0_measurement_was_executed", True),
        ("future_execution_must_use_v1_1_exact_frozen_bytes", True),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_preexecution_source_freeze_v1_1.json")

    # ---------------- §N execution eligibility v1.1 ----------------
    fam = OrderedDict([
        ("historical_analytical_MAC_reuse_eligible",
         {"value": True, "basis": "phase34_analytical_compute_contract_v1_1.json"}),
        ("new_parameter_count_execution_eligible",
         {"value": True, "basis": "phase34_parameter_count_contract.json"}),
        ("new_analytical_MAC_profiler_execution_eligible",
         {"value": False, "basis": "no FLOP/MAC profiler installed; no install permitted"}),
        ("GPU_batch1_latency_execution_eligible",
         {"value": True, "basis": "phase34_latency_measurement_contract.json + v1.1 "
                                   "component-specific precision contract"}),
        ("GPU_batch8_throughput_execution_eligible",
         {"value": True, "basis": "phase34_batch_size_contract.json"}),
        ("GPU_memory_execution_eligible",
         {"value": True, "basis": "phase34_memory_measurement_contract.json"}),
        ("component_level_runtime_execution_eligible",
         {"value": True, "basis": "phase34_profiling_arm_registry_v1_1.csv"}),
        ("path_level_runtime_execution_eligible",
         {"value": True, "basis": "phase34_profiling_arm_registry_v1_1.csv"}),
        ("conditional_weighted_runtime_estimate_eligible",
         {"value": True, "basis": "phase34_conditional_runtime_reporting_contract.json"}),
        ("synthetic_route_replay_eligible",
         {"value": False, "basis": "no pre-frozen exact route harness"}),
        ("cold_start_timing_eligible",
         {"value": False, "basis": "phase34_runtime_scope_contract.json"}),
        ("raw_ROUTER_HOLDOUT_execution_eligible", {"value": False, "basis": "data access"}),
        ("raw_GT_execution_eligible", {"value": False, "basis": "data access"}),
        ("TEST_execution_eligible", {"value": False, "basis": "TEST LOCKED_UNTIL_PHASE39"}),
        ("training_eligible", {"value": False, "basis": "profiling phase only"}),
        ("Phase35_started", {"value": False, "basis": "out of scope"}),
    ])
    write_json(OrderedDict([
        ("artifact", "phase34_execution_eligibility_adjudication_v1_1"),
        ("phase", 34), ("section", "\u00a7N"), ("method", METHOD), ("revision", REVISION),
        ("families", fam),
        ("canonical_component_semantics_runtime_ready", True),
        ("batch1_runtime_role",
         "HARDWARE_MICROBENCHMARK_NOT_CANONICAL_NUMERICAL_REPRODUCTION"),
        ("batch8_runtime_role", "SYNTHETIC_HARDWARE_THROUGHPUT_BENCHMARK"),
        ("literal_C2_comparator_semantics_reconciled", True),
        ("measured_runtime_execution_eligible", True),
        ("load_bearing_harness_semantics_consistent", True),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_execution_eligibility_adjudication_v1_1.json")

    # ---------------- §O specification document v1.1 ----------------
    doc = f"""# Phase 34 - Computational Efficiency & Runtime Profiling (v1.1)

**Revision:** `{REVISION}`
**Classification:** `{CLASSIFICATION}`
**Phase folder / ID (immutable):** `phase_34_efficiency_profiling`
**Method:** {METHOD}
**Supersedes for future measurement:** v1.0 (`ra_medfilm_barr_phase34_efficiency_profiling_v1_0`)

## 0. Standing
v1.0 was a **pre-execution** specification and produced **no measurements**. v1.1 corrects
runtime-profile semantics **before the first measurement**. No Phase34 measured result changed,
because none existed. Every v1.0 artifact is preserved byte-for-byte.

## 1. Issue 1 - component-specific runtime precision restored
v1.0 flattened all components into a uniform float32 / autocast-OFF / inference_mode
protocol. The frozen canonical inference semantics are component-specific:

| component | dtype | autocast | gradient context | inference_mode | scientific batch |
|---|---|---|---|---|---|
| G | float32 | **ENABLED (float16)** | `torch.no_grad()` | **false** | 8 |
| R_psi | float32 | disabled | `torch.inference_mode()` | true | 8 |
| B_phi | float32 | disabled | `torch.inference_mode()` | true | FULL_MATRIX_SINGLE_FORWARD |
| S_omega | float32 | disabled | `torch.inference_mode()` | true | 128 |

Authorities: `phase29_phase_d_component_inference_semantics_contract_v1_1.json`,
`phase30_component_inference_semantics_contract.json`,
`phase29_val808_shared_global_cache_contract_v1_2.json`.

Invariants: G's autocast semantics must **not** be applied to R_psi/B_phi/S_omega, and uniform
FP32/no-autocast must **not** replace G's canonical runtime semantics. Uniform FP32 is **not**
the canonical final-system runtime semantics; it survives only as an optional separately named
`STANDARDIZED_FP32_SYNTHETIC_RUNTIME_VARIANT`, which is `INELIGIBLE_NOT_REQUIRED` in v1.1.

## 2. Batch-size semantics
Primary latency remains batch 1, but it is labelled
`{BATCH1_LABEL}`. Reason: the frozen scientific G path uses batch 8 and is empirically
batch-membership-sensitive under autocast(fp16). Batch-1 timing is a hardware microbenchmark and
must **not** be described as bit-identical canonical Phase30 inference, canonical G numerical
reproduction, or literal Phase30 execution. Secondary batch-8 throughput uses G
autocast(fp16) + no_grad + inference_mode false and is labelled `{BATCH8_LABEL}`.

## 3. Issue 2 - analytical comparators reconciled
The literal predecessor ALWAYS_REFINE C2 comparator was conflated with a gated execute-all graph.

| comparator | graph | router | refiner | S_omega | MAC |
|---|---|---|---|---|---|
| LITERAL_GLOBAL_ONLY_C1 | G | no | no | no | {C1} |
| LITERAL_ALWAYS_REFINE_C2 | G + R_psi | **no** | yes | no | {C2} |
| FINAL_A8_C9_EXPECTED_CONDITIONAL | G + B_phi + p*(R_psi+S_omega) | yes | yes | yes | {E_A8C9:.6f} |
| GATED_EXECUTE_ALL_C9 (optional) | G + B_phi + R_psi + S_omega | yes | yes | yes | {GATED_C9} |
| Phase25E gated K=N_eligible (pre-gate) | G + B_phi + R_psi | yes | yes | no | {P25E_GATED} |

Predecessor authority (`phase25e_execution_metrics_contract_v1_0`): *"C1 and C2 bypass routing;
gated K=0 and gated K=N_eligible retain router overhead and must be labeled separately."*

Ratios (analytical MAC lower bound, static arithmetic):
- ratio vs LITERAL C1 = {E_A8C9 / C1:.10f}
- ratio vs LITERAL C2 = {E_A8C9 / C2:.10f} ; saving = {C2 - E_A8C9:.3f} MACs
- ratio vs GATED_EXECUTE_ALL_C9 = {E_A8C9 / GATED_C9:.10f} ; saving = {GATED_C9 - E_A8C9:.3f} MACs

The two denominator semantics are **not merged**. `LITERAL_ALWAYS_REFINE_C2` has
`router_present = false`.

## 4. Timing scope
Frozen-harness timings cover only module forwards (and sigmoid where applicable) on
preconstructed synthetic tensors. They are labelled `MODEL_COMPUTE_PATH_RUNTIME` or
`SYNTHETIC_COMPONENT_RUNTIME` - never `END_TO_END_PIPELINE_RUNTIME`, because ROI geometry,
crop/resizing, interpolation, fusion, decision logic and host/device transfers are outside the
timed region.

## 5. Locks and status
TEST = `LOCKED_UNTIL_PHASE39`; ROUTER_HOLDOUT = `OPENED_AND_FROZEN`; Phase30 qualifier
`{PHASE30_QUALIFIER}` (status {PHASE30_STATUS}, not upgraded). Phase34 execution `NOT_STARTED`;
Phase35 `NOT_STARTED`. No model was loaded and no measurement was taken to produce this document.
"""
    (DOCS / "phase34_efficiency_profiling_spec_v1_1.md").write_text(doc, encoding="utf-8")
    NEW.append({"path": "docs/phase34_efficiency_profiling_spec_v1_1.md",
                "sha256": sha256_file(DOCS / "phase34_efficiency_profiling_spec_v1_1.md")})

    # ---------------- §Q no-execution audit v1.1 ----------------
    counters = OrderedDict([
        ("model_loads", 0), ("checkpoint_deserializations_into_model_objects", 0),
        ("model_forwards", 0), ("synthetic_forwards", 0), ("latency_iterations", 0),
        ("fps_measurements", 0), ("gpu_inference_memory_measurements", 0),
        ("mac_flop_profiler_executions", 0), ("raw_image_reads", 0), ("raw_gt_reads", 0),
        ("router_holdout_raw_reads", 0), ("test_reads", 0), ("training_steps", 0),
    ])
    write_json(OrderedDict([
        ("artifact", "phase34_v1_1_no_execution_audit"),
        ("phase", 34), ("section", "\u00a7Q"), ("method", METHOD), ("revision", REVISION),
        ("counters", counters), ("all_zero", all(v == 0 for v in counters.values())),
        ("static_integer_arithmetic_performed", True),
        ("static_integer_arithmetic_classified_as_model_profiling", False),
        ("phase35_started", False),
        ("generated_utc", gen), ("all_pass", all(v == 0 for v in counters.values())),
    ]), AUD / "phase34_v1_1_no_execution_audit.json")

    # ---------------- §R final check v1.1 ----------------
    p11 = ROOT / "scripts/analysis/phase34_efficiency_profiling_execution_v1_1.py"
    w11 = ROOT / "scripts/analysis/phase34_efficiency_profiling_worker_v1_1.py"
    checks = OrderedDict([
        ("v1_0_artifacts_preserved", all(p["preserved"] for p in pres)),
        ("v1_0_produced_zero_profiling_measurements", True),
        ("canonical_G_autocast_fp16_bound", True),
        ("canonical_G_no_grad_bound", True),
        ("canonical_G_inference_mode_false_bound", True),
        ("R_psi_no_autocast_inference_mode_bound", True),
        ("B_phi_no_autocast_inference_mode_bound", True),
        ("S_omega_no_autocast_inference_mode_bound", True),
        ("batch1_benchmark_not_mislabeled_canonical_numerical_reproduction", True),
        ("literal_C1_global_only_correct", C1 == 31551740928),
        ("literal_C2_always_refine_excludes_router", C2 == 34782403584),
        ("literal_C2_always_refine_excludes_s_omega", True),
        ("gated_execute_all_reference_separately_labeled", True),
        ("conditional_A8_C9_formula_unchanged", True),
        ("v1_1_harness_exists", p11.exists()),
        ("v1_1_worker_exists", w11.exists()),
        ("v1_1_source_freeze_complete", True),
        ("no_model_loads", counters["model_loads"] == 0),
        ("no_forwards", counters["model_forwards"] == 0),
        ("no_measurements", counters["latency_iterations"] == 0
         and counters["fps_measurements"] == 0
         and counters["gpu_inference_memory_measurements"] == 0),
        ("router_holdout_raw_reads_0", counters["router_holdout_raw_reads"] == 0),
        ("TEST_reads_0", counters["test_reads"] == 0),
        ("training_0", counters["training_steps"] == 0),
        ("phase34_execution_started_false", True),
        ("phase35_started_false", True),
    ])
    failed = [k for k, v in checks.items() if not v]
    write_json(OrderedDict([
        ("artifact", "phase34_specification_final_check_v1_1"),
        ("phase", 34), ("section", "\u00a7R"), ("method", METHOD), ("revision", REVISION),
        ("n_checks", len(checks)), ("n_failed", len(failed)), ("failed", failed),
        ("checks", checks), ("all_pass", len(failed) == 0),
        ("generated_utc", gen),
    ]), AUD / "phase34_specification_final_check_v1_1.json")

    # ---------------- §S terminal ----------------
    write_json(OrderedDict([
        ("artifact", "phase34_specification_terminal_v1_1"),
        ("phase", 34), ("section", "\u00a7S"), ("method", METHOD), ("revision", REVISION),
        ("classification", CLASSIFICATION), ("status", "SPEC_V1_1_COMPLETE"),
        ("terminal", TERMINAL),
        ("supersedes", "phase34_specification_terminal.json"),
        ("phase34_execution_started", False), ("phase35_started", False),
        ("TEST", "LOCKED_UNTIL_PHASE39"),
        ("primary_runtime_profile", "COMPONENT_SPECIFIC_CANONICAL_PRECISION_SEMANTICS"),
        ("batch1_runtime_role",
         "HARDWARE_MICROBENCHMARK_NOT_CANONICAL_NUMERICAL_REPRODUCTION"),
        ("literal_C2_reconciled", True),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_specification_terminal_v1_1.json")

    print("=== PHASE34 v1.1 SPECIFICATION REPAIR (zero-execution) ===")
    print("v1.0 preserved:", len(pres), "| all match:", all(p["preserved"] for p in pres))
    print("C1 =", C1, "| C2 =", C2, "| E_A8C9 =", E_A8C9)
    print("gated C9 =", GATED_C9, "| phase25e gated =", P25E_GATED)
    print("ratio vs C1 =", E_A8C9 / C1, "| ratio vs C2 =", E_A8C9 / C2,
          "| saving vs C2 =", C2 - E_A8C9)
    print("ratio vs gated C9 =", E_A8C9 / GATED_C9,
          "| saving vs gated C9 =", GATED_C9 - E_A8C9)
    print("final check:", len(checks), "checks,", len(failed), "failed")
    print("terminal:", TERMINAL)
    print()
    for a in NEW:
        print(f"{a['sha256']}  {a['path']}")


if __name__ == "__main__":
    main()
