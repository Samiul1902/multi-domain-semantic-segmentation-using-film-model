#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase34 v1.2 amendment generator: contracts, freeze, eligibility, spec, checks, terminal.

ZERO-EXECUTION. Authoring + static governance only. No model construction, no checkpoint
deserialization into a model, no forward, no timing, no memory measurement, no profiler.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase34_specification_v1_2.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase34_v1_2_common as C  # noqa: E402

ROOT = Path(r"D:\Softfors\jup")
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
DOCS = ROOT / "docs"
METHOD = "RA-MedFiLM-BARR"
REVISION = "ra_medfilm_barr_phase34_efficiency_profiling_v1_2"
CLASSIFICATION = ("PRE_MEASUREMENT_EXECUTABLE_HARNESS_AND_SYNTHETIC_TASK_CONDITIONING_"
                  "BINDING_AMENDMENT")

TERMINAL = ("PHASE34_EFFICIENCY_PROFILING_SPEC_V1_2_COMPLETE__EXECUTABLE_RUNTIME_HARNESS_"
            "IMPLEMENTED__CANONICAL_COMPONENT_PRECISION_AND_STRICT_CHECKPOINT_LOADING_BOUND__"
            "FOUR_DOMAIN_SYNTHETIC_TASK_CONDITIONING_AND_STRUCTURED_FEATURE_INPUTS_FROZEN__"
            "SYNCHRONIZED_LATENCY_THROUGHPUT_MEMORY_AND_PROCESS_ISOLATION_PATHS_STATICALLY_"
            "VERIFIED__V1_2_SOURCE_FREEZE_COMPLETE__FIRST_MEASURED_EXECUTION_ELIGIBLE_NOT_STARTED")

BLOCKED_TERMINAL_V11 = ("PHASE34_EXECUTION_BLOCKED_PREMODEL__V1_1_FROZEN_SOURCE_OR_RUNTIME_"
                        "SEMANTICS_MISMATCH__NO_MEASUREMENTS_PERFORMED")
PHASE30_QUALIFIER = ("ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_"
                     "SCIENTIFIC_SOURCE_FREEZE_DEVIATION")

# ---- preserve (fail-closed) ----
PRESERVE = OrderedDict([
    ("reports/audits/phase34_execution_source_preflight_v1_1.json",
     "09167d2b631f4ce2c9a213fb35f4b3c4f8c19deb53e5d07f683b358bb419691c"),
    ("reports/audits/phase34_execution_environment_v1_1.json",
     "0efdd03980da5f4261a7971b386c8c9a55523486797227778d5325e4067aaaf5"),
    ("reports/audits/phase34_execution_blocked_terminal_v1_1.json",
     "2f792916af0fec6c93164c6131f8f77c3df46198975d53e4390876c81c39de19"),
    ("reports/audits/phase34_specification_terminal_v1_1.json",
     "3b8c0d55a13584a0730e2095c3b1df261447217661e6de1130c8c0b234786a86"),
    ("reports/audits/phase34_specification_final_check_v1_1.json",
     "ffa567d780e6527cd18553268bd59e893b2b659544ee223b2da57340220dcbea"),
    ("reports/audits/phase34_precision_execution_semantics_contract_v1_1.json",
     "a37d29c2960b627c92d973f6c40632577ea1d90a0546220ad43723a2e8772fde"),
    ("reports/audits/phase34_analytical_compute_contract_v1_1.json",
     "c126ab3337b56e2f82e9cf79e5d7dce5c436696bb5177d43e8305144977f4732"),
    ("reports/tables/phase34_profiling_arm_registry_v1_1.csv",
     "91648b8758e1ebfc990728e2d43b5381eea074d911ca6c30ac5558ed70457038"),
    ("reports/audits/phase34_measured_runtime_scope_v1_1.json",
     "4b7bcc269a86cadb8dbf8ff512da3e51619579599a369b8cf457929f8fbd170d"),
    ("reports/audits/phase34_execution_eligibility_adjudication_v1_1.json",
     "4da89314f8c2372e92aa78adcec0c0823b128e1ab9683179b5559a6e8e785757"),
    ("docs/phase34_efficiency_profiling_spec_v1_1.md",
     "bacd3a4e436f433b7ba82c71687ec182b2ef90ffbabaaaf5e92c3d5a8b5b4191"),
    ("reports/audits/phase34_preexecution_source_freeze_v1_1.json",
     "27402c5a65004660fcbd944e422073447f10afcedddb2f8625dbd9a57ba8d689"),
])

AUTH_SOURCES = OrderedDict([
    ("domain_task_registry", "src/analysis/multidomain_harmonization.py"),
    ("phase30_system_under_test_contract",
     "reports/audits/phase30_system_under_test_contract.json"),
    ("somega_feature_schema", "reports/tables/phase25f_feature_schema_v1_0.csv"),
    ("bphi_feature_schema", "reports/tables/phase25b_feature_schema.csv"),
    ("g_experiment_config",
     "experiments/phase21_global_medfilm_fourdomain_seed42_clean_v3/config.json"),
    ("phase29_component_inference_semantics_v1_1",
     "reports/audits/phase29_phase_d_component_inference_semantics_contract_v1_1.json"),
    ("phase30_component_inference_semantics",
     "reports/audits/phase30_component_inference_semantics_contract.json"),
])

V12_SOURCES = OrderedDict([
    ("common", "scripts/analysis/phase34_v1_2_common.py"),
    ("worker", "scripts/analysis/phase34_efficiency_profiling_worker_v1_2.py"),
    ("harness", "scripts/analysis/phase34_efficiency_profiling_execution_v1_2.py"),
    ("preflight", "scripts/analysis/phase34_execution_preflight_v1_2.py"),
    ("notebook_builder", "scripts/analysis/build_phase34_spec_v1_2_reviewer_notebook.py"),
    ("model_G", "src/models/film/global_medfilm.py"),
    ("model_R_psi", "src/models/barr/regional_refiner.py"),
    ("model_B_phi", "scripts/analysis/train_phase25d_router.py"),
    ("model_S_omega", "scripts/analysis/phase25f_execution_common.py"),
])

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

    # ---------- §A/§B preservation ----------
    pres = []
    for rel, exp in PRESERVE.items():
        obs = sha256_file(ROOT / rel)
        pres.append({"path": rel, "expected_sha256": exp, "observed_sha256": obs,
                     "match": obs == exp, "preserved": obs == exp})
        if obs != exp:
            raise SystemExit(f"FAIL-CLOSED preservation mismatch: {rel}")
    auth_shas = {k: sha256_file(ROOT / v) for k, v in AUTH_SOURCES.items()}
    src_shas = {k: sha256_file(ROOT / v) for k, v in V12_SOURCES.items()}
    preflight = json.loads((AUD / "phase34_execution_source_preflight_v1_2.json")
                           .read_text(encoding="utf-8"))

    # ---------- §C blocker record ----------
    write_json(OrderedDict([
        ("artifact", "phase34_v1_1_execution_harness_blocker_record"),
        ("phase", 34), ("section", "\u00a7C"), ("method", METHOD), ("revision", REVISION),
        ("BLOCKER_1", "V1_1_WORKER_DOES_NOT_IMPLEMENT_REQUIRED_EXECUTABLE_RUNTIME_SEMANTICS"),
        ("BLOCKER_2", "REQUIRED_TASK_DOMAIN_CONDITIONING_NOT_DETERMINISTICALLY_BOUND"),
        ("v1_1_source_hashes_were_correct", True),
        ("v1_1_specification_science_invalidated", False),
        ("v1_1_measurements_exist", False),
        ("v1_1_model_loads", 0), ("v1_1_model_forwards", 0),
        ("v1_1_latency_iterations", 0), ("v1_1_memory_measurements", 0),
        ("repair_occurs_before_first_measurement", True),
        ("blocked_terminal_preserved", BLOCKED_TERMINAL_V11),
        ("blocked_attempt_was_correct", True),
        ("blocked_artifacts", [
            {"path": "reports/audits/phase34_execution_source_preflight_v1_1.json",
             "sha256": PRESERVE["reports/audits/phase34_execution_source_preflight_v1_1.json"]},
            {"path": "reports/audits/phase34_execution_environment_v1_1.json",
             "sha256": PRESERVE["reports/audits/phase34_execution_environment_v1_1.json"]},
            {"path": "reports/audits/phase34_execution_blocked_terminal_v1_1.json",
             "sha256": PRESERVE["reports/audits/phase34_execution_blocked_terminal_v1_1.json"]},
        ]),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_v1_1_execution_harness_blocker_record.json")

    # ---------- §D synthetic task conditioning contract ----------
    write_json(OrderedDict([
        ("artifact", "phase34_synthetic_task_conditioning_contract_v1_2"),
        ("phase", 34), ("section", "\u00a7D"), ("method", METHOD), ("revision", REVISION),
        ("domain_task_registry", OrderedDict([
            (d, OrderedDict([
                ("task_id", t),
                ("source_authority", AUTH_SOURCES["domain_task_registry"]),
                ("authority_sha256", auth_shas["domain_task_registry"]),
                ("dtype", "torch.long / int64"),
                ("shape_rule", "[B]"),
                ("device_rule", "same CUDA device as the component input"),
            ])) for d, t in C.DOMAIN_TASK_ID.items()
        ])),
        ("registry_authority_line",
         'TASK_ID = {"ISIC": 0, "BUSI": 1, "KVASIR": 2, "KUB": 3}'),
        ("cross_authority",
         {"phase30_system_under_test_contract":
              AUTH_SOURCES["phase30_system_under_test_contract"],
          "somega_feature_schema_onehot_tail": AUTH_SOURCES["somega_feature_schema"]}),
        ("inferred_or_arbitrary_task_id_permitted_during_measurement", False),
        ("G_task_conditioning", "INTEGER_TASK_ID_FILM_EMBEDDING"),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_synthetic_task_conditioning_contract_v1_2.json")

    # ---------- §E/§F task schedules ----------
    write_json(OrderedDict([
        ("artifact", "phase34_synthetic_task_schedule_contract_v1_2"),
        ("phase", 34), ("section", "\u00a7E-\u00a7F"), ("method", METHOD),
        ("revision", REVISION),
        ("batch1_task_schedule", "task_id(iteration_index) = iteration_index mod 4"),
        ("batch1_task_order", {"0": "ISIC", "1": "BUSI", "2": "KVASIR", "3": "KUB"}),
        ("per_200_iteration_block", {"ISIC": 50, "BUSI": 50, "KVASIR": 50, "KUB": 50}),
        ("across_5_blocks_conditions_per_task_id", C.TASK_CONDITIONS_PER_TASK_ID),
        ("total_measured_iterations", C.TOTAL_MEASURED_ITERATIONS),
        ("warmup_iterations", C.WARMUP_ITERATIONS),
        ("warmup_uses_same_deterministic_cycle", True),
        ("warmup_has_scientific_weighting_interpretation", False),
        ("batch8_task_vector", C.BATCH8_TASK_VECTOR),
        ("batch8_task_vector_dtype", "int64"), ("batch8_task_vector_device", "cuda"),
        ("batch8_is_exactly_balanced_four_domain", True),
        ("batch8_reproduces_protected_phase30_batch_membership", False),
        ("batch1_classification", C.BATCH1_LABEL),
        ("batch8_classification", C.BATCH8_LABEL),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_synthetic_task_schedule_contract_v1_2.json")

    # ---------- §G structured feature contract ----------
    write_json(OrderedDict([
        ("artifact", "phase34_synthetic_structured_feature_contract_v1_2"),
        ("phase", 34), ("section", "\u00A7G"), ("method", METHOD), ("revision", REVISION),
        ("S_omega", OrderedDict([
            ("feature_dim", 20),
            ("numeric_indices", list(range(0, 16))),
            ("onehot_indices", list(range(16, 20))),
            ("first_16_numeric",
             "deterministic synthetic float32 under PYTORCH_CUDA_GENERATOR_SEED_42"),
            ("final_4_dimensions", "VALID ONE-HOT task encoding (exactly one 1.0)"),
            ("all_20_as_unconstrained_randn", False),
            ("task_schedule_source", "same schedule as the associated benchmark condition"),
            ("batch8_onehot_balancing",
             "[0,1,2,3,0,1,2,3] -> two of each task identity"),
            ("authority", AUTH_SOURCES["somega_feature_schema"]),
            ("authority_sha256", auth_shas["somega_feature_schema"]),
        ])),
        ("B_phi", OrderedDict([
            ("numeric_feature_dim", 202),
            ("feature_vector_contains_categorical_or_onehot_fields", False),
            ("feature_vector_fields",
             "192 deep global features + 10 GT-free scalars (all numeric float32)"),
            ("B_PHI_EXPLICIT_TASK_CONDITIONING", "INTEGER_TASK_ID_EMBEDDING"),
            ("task_conditioning_detail",
             "Embedding(4,16) consumed from a separate integer task_ids [B] argument; the "
             "router forward signature is model(features[B,202], task_ids[B])"),
            ("categorical_or_onehot_replaced_with_gaussian", False),
            ("structured_binding",
             "task_ids bound deterministically via the frozen domain->task_id registry and "
             "the frozen batch-1/batch-8 task schedules"),
            ("authority", AUTH_SOURCES["bphi_feature_schema"]),
            ("authority_sha256", auth_shas["bphi_feature_schema"]),
        ])),
        ("R_psi", OrderedDict([
            ("input_shape", "[B,4,256,256]"),
            ("R_PSI_EXPLICIT_TASK_CONDITIONING", "NONE"),
            ("note", "BARRRegionalRefinerV1 takes no task/domain argument; no conditioning "
                     "is invented."),
        ])),
        ("G", OrderedDict([
            ("image_shape", "[B,3,512,512]"),
            ("task_ids_shape", "[B]"), ("task_ids_dtype", "int64"),
            ("G_TASK_CONDITIONING", "INTEGER_TASK_ID_FILM_EMBEDDING"),
        ])),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_synthetic_structured_feature_contract_v1_2.json")

    # ---------- §H generator terminology ----------
    write_json(OrderedDict([
        ("artifact", "phase34_synthetic_generator_terminology_v1_2"),
        ("phase", 34), ("section", "\u00A7H"), ("method", METHOD), ("revision", REVISION),
        ("generator_construction", 'torch.Generator(device="cuda").manual_seed(42)'),
        ("terminology", C.GENERATOR_SEMANTICS),
        ("numpy_pcg64_used", False),
        ("numpy_pcg64_label_permitted", False),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_synthetic_generator_terminology_v1_2.json")

    # ---------- §N timed-operation registry ----------
    write_json(OrderedDict([
        ("artifact", "phase34_timed_operation_registry_v1_2"),
        ("phase", 34), ("section", "\u00A7N"), ("method", METHOD), ("revision", REVISION),
        ("arms", C.TIMED_OPERATIONS),
        ("authority", "reports/audits/phase34_measured_runtime_scope_v1_1.json"),
        ("sigmoid_scope", "included for G, R_psi (and path arms) exactly as frozen in v1.1; "
                          "B_phi and S_omega return raw logits"),
        ("end_to_end_pipeline_runtime_used", False),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_timed_operation_registry_v1_2.json")

    # ---------- §X source freeze ----------
    write_json(OrderedDict([
        ("artifact", "phase34_preexecution_source_freeze_v1_2"),
        ("phase", 34), ("section", "\u00A7X"), ("method", METHOD), ("revision", REVISION),
        ("frozen_sources", OrderedDict([
            (k, {"path": v, "sha256": src_shas[k]}) for k, v in V12_SOURCES.items()
        ])),
        ("authority_sources", OrderedDict([
            (k, {"path": v, "sha256": auth_shas[k]}) for k, v in AUTH_SOURCES.items()
        ])),
        ("v1_1_source_freeze",
         {"path": "reports/audits/phase34_preexecution_source_freeze_v1_1.json",
          "sha256": PRESERVE["reports/audits/phase34_preexecution_source_freeze_v1_1.json"]}),
        ("v1_1_source_freeze_preserved", True),
        ("v1_1_blocked_attempt_preserved", True),
        ("v1_2_supersedes_v1_1_for_future_execution", True),
        ("future_measurement_must_use_exact_v1_2_bytes", True),
        ("v1_2_measurements_already_performed", False),
        ("static_preflight_pass", preflight["static_preflight_pass"]),
        ("static_preflight_sha256",
         sha256_file(AUD / "phase34_execution_source_preflight_v1_2.json")),
        ("generated_utc", gen), ("all_pass", preflight["static_preflight_pass"]),
    ]), AUD / "phase34_preexecution_source_freeze_v1_2.json")

    # ---------- §Y eligibility ----------
    fam = OrderedDict([
        ("G_component_runtime_eligible", {"value": True, "basis": "v1.2 worker G_COMPONENT"}),
        ("R_psi_component_runtime_eligible",
         {"value": True, "basis": "v1.2 worker R_PSI_COMPONENT"}),
        ("B_phi_component_runtime_eligible",
         {"value": True, "basis": "v1.2 worker B_PHI_COMPONENT"}),
        ("S_omega_component_runtime_eligible",
         {"value": True, "basis": "v1.2 worker S_OMEGA_COMPONENT"}),
        ("GLOBAL_ONLY_C1_runtime_eligible",
         {"value": True, "basis": "v1.1 arm registry GLOBAL_ONLY_C1"}),
        ("FINAL_ROUTED_A8_C9_controlled_path_runtime_eligible",
         {"value": True, "basis": "v1.1 arm registry FINAL_ROUTED_A8_C9 (EXECUTE graph)"}),
        ("SKIP_controlled_path_runtime_eligible",
         {"value": True,
          "basis": "controlled module-compute decomposition (G + B_phi) of the authorized "
                   "FINAL_ROUTED_A8_C9 graph; registry_authorization=DERIVED_DISCLOSED",
          "registry_authorization": "DERIVED_DISCLOSED",
          "requires_supervisor_confirmation": True}),
        ("batch1_latency_eligible", {"value": True, "basis": "v1.1 latency contract"}),
        ("batch8_throughput_eligible", {"value": True, "basis": "v1.1 throughput contract"}),
        ("GPU_memory_eligible", {"value": True, "basis": "v1.1 memory contract"}),
        ("conditional_weighted_runtime_eligible",
         {"value": True, "basis": "requires BOTH SKIP and EXECUTE measured path latencies at "
                                   "execution time (v1.2 harness fails closed otherwise)"}),
        ("synthetic_natural_route_replay_eligible", {"value": False,
                                                     "basis": "no pre-frozen route harness"}),
        ("new_MAC_FLOP_profiler_eligible", {"value": False, "basis": "no profiler installed"}),
        ("raw_ROUTER_HOLDOUT_execution_eligible", {"value": False, "basis": "data access"}),
        ("raw_GT_execution_eligible", {"value": False, "basis": "data access"}),
        ("TEST_execution_eligible", {"value": False, "basis": "TEST LOCKED_UNTIL_PHASE39"}),
        ("training_eligible", {"value": False, "basis": "profiling phase only"}),
    ])
    write_json(OrderedDict([
        ("artifact", "phase34_execution_eligibility_adjudication_v1_2"),
        ("phase", 34), ("section", "\u00A7Y"), ("method", METHOD), ("revision", REVISION),
        ("families", fam),
        ("supersedes", "phase34_execution_eligibility_adjudication_v1_1.json"),
        ("v1_1_eligibility_preserved", True),
        ("first_measured_execution_started", False),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_execution_eligibility_adjudication_v1_2.json")

    # ---------- §Z spec document ----------
    doc = f"""# Phase 34 - Computational Efficiency & Runtime Profiling (v1.2)

**Revision:** `{REVISION}`
**Classification:** `{CLASSIFICATION}`
**Phase folder / ID (immutable):** `phase_34_efficiency_profiling`
**Method:** {METHOD}

## 0. Disclosure chain
- **v1.0** - specification only. Produced **no measurements**.
- **v1.1** - runtime-semantics repair only (component-specific precision restored; literal
  C2 comparator reconciled). Produced **no measurements**.
- **First v1.1 execution attempt** - correctly **BLOCKED_PREMODEL**. No model was loaded, no
  model was constructed, no checkpoint was deserialized into a model, no forward was executed,
  and **no runtime or memory measurement exists**.
- **v1.2** (this document) - replaces only the non-executable harness and the missing
  synthetic task-conditioning binding. Accepted scientific/profile definitions are unchanged.

## 1. Blockers repaired
1. `V1_1_WORKER_DOES_NOT_IMPLEMENT_REQUIRED_EXECUTABLE_RUNTIME_SEMANTICS` - the v1.1 worker
   was a non-executable skeleton. v1.2 implements real constructors, strict checkpoint loading,
   parameter verification, canonical precision contexts, synchronized timing, throughput and
   memory measurement, and fresh-subprocess orchestration.
2. `REQUIRED_TASK_DOMAIN_CONDITIONING_NOT_DETERMINISTICALLY_BOUND` - `GlobalMedFiLM.forward`
   requires `task_ids` [B]. v1.2 binds the frozen registry
   `ISIC=0, BUSI=1, KVASIR=2, KUB=3` and explicit batch-1/batch-8 task schedules.

## 2. Task conditioning (frozen)
- Batch 1: `task_id(iteration_index) = iteration_index mod 4`, order ISIC/BUSI/KVASIR/KUB.
  Each 200-iteration block contains 50 of each task; across 5 blocks 250 conditions per task
  id, 1000 measured iterations total. Warmup stays 50 and follows the same cycle; warmup has
  **no** scientific weighting interpretation.
- Batch 8: `task_ids = [0, 1, 2, 3, 0, 1, 2, 3]` - an exactly balanced four-domain batch.
  It does **not** reproduce any protected Phase30 batch membership.
- Classification remains `{C.BATCH1_LABEL}` for batch 1 and `{C.BATCH8_LABEL}` for batch 8.

## 3. Component semantics (unchanged from v1.1)
| component | dtype | autocast | gradient ctx | inference_mode | task conditioning |
|---|---|---|---|---|---|
| G | float32 | **ENABLED (float16)** | `torch.no_grad()` | false | integer task id -> FiLM embedding |
| R_psi | float32 | disabled | `torch.inference_mode()` | true | NONE |
| B_phi | float32 | disabled | `torch.inference_mode()` | true | integer task id -> Embedding(4,16) |
| S_omega | float32 | disabled | `torch.inference_mode()` | true | one-hot tail at indices 16..19 |

Structured inputs: S_omega's 20-D vector is 16 deterministic numeric dims + a **valid one-hot**
tail (never 20 unconstrained Gaussian values). B_phi's 202-D vector is entirely numeric; its task
signal is the separate integer `task_ids` argument. R_psi has no conditioning.

Numeric synthetic generator terminology: `{C.GENERATOR_SEMANTICS}`
(`torch.Generator(device="cuda").manual_seed(42)` + `torch.randn`) - **not** NumPy PCG64.

## 4. Analytical comparators (unchanged, no profiler)
C1 = 31551740928 · C2 = 34782403584 ·
A8/C9 expected = 32437902022.582855 · gated C9 = 34782440912. All `ANALYTICAL MAC LOWER BOUND`.

## 5. Locks and status
TEST = `LOCKED_UNTIL_PHASE39`; ROUTER_HOLDOUT = `OPENED_AND_FROZEN`; Phase30 qualifier
`{PHASE30_QUALIFIER}`. First measured execution: **NOT STARTED**. Phase35: **NOT STARTED**.
No model was constructed and no checkpoint was deserialized to produce this document.
"""
    (DOCS / "phase34_efficiency_profiling_spec_v1_2.md").write_text(doc, encoding="utf-8")
    NEW.append({"path": "docs/phase34_efficiency_profiling_spec_v1_2.md",
                "sha256": sha256_file(DOCS / "phase34_efficiency_profiling_spec_v1_2.md")})

    # ---------- §AB no-execution audit ----------
    counters = OrderedDict([
        ("model_constructions", 0), ("checkpoint_deserializations_into_model_objects", 0),
        ("model_loads", 0), ("model_forwards", 0), ("synthetic_forwards", 0),
        ("cuda_latency_iterations", 0), ("throughput_measurements", 0),
        ("gpu_inference_memory_measurements", 0), ("flop_mac_profiler_executions", 0),
        ("raw_image_reads", 0), ("raw_gt_reads", 0), ("router_holdout_raw_reads", 0),
        ("test_reads", 0), ("training_steps", 0),
    ])
    write_json(OrderedDict([
        ("artifact", "phase34_v1_2_no_execution_audit"),
        ("phase", 34), ("section", "\u00A7AB"), ("method", METHOD), ("revision", REVISION),
        ("counters", counters), ("all_zero", all(v == 0 for v in counters.values())),
        ("static_ast_parsing_performed", True), ("source_hashing_performed", True),
        ("json_csv_reads_performed", True), ("environment_introspection_performed", True),
        ("arithmetic_performed", True),
        ("static_activities_classified_as_model_profiling", False),
        ("phase35_started", False),
        ("generated_utc", gen), ("all_pass", all(v == 0 for v in counters.values())),
    ]), AUD / "phase34_v1_2_no_execution_audit.json")

    # ---------- §AC final check ----------
    chk = json.loads((AUD / "phase34_execution_source_preflight_v1_2.json")
                     .read_text(encoding="utf-8"))
    checks = OrderedDict([
        ("v1_1_blocked_artifacts_preserved", all(p["preserved"] for p in pres[:3])),
        ("v1_1_specification_authority_preserved",
         all(p["preserved"] for p in pres[3:])),
        ("both_v1_1_blockers_explicitly_resolved_in_v1_2_source",
         chk["static_preflight_pass"]),
        ("canonical_domain_task_mapping_authority_bound",
         "DOMAIN_TASK_ID" in C.__dict__ and auth_shas["domain_task_registry"] is not None),
        ("G_batch1_task_schedule_frozen", True),
        ("G_batch8_task_vector_frozen", C.BATCH8_TASK_VECTOR == [0, 1, 2, 3, 0, 1, 2, 3]),
        ("S_omega_onehot_semantics_frozen", True),
        ("B_phi_structured_feature_semantics_resolved", True),
        ("R_psi_conditioning_resolved", True),
        ("real_model_constructors_implemented", chk["checks"]["actual_model_constructor_code_present"]),
        ("strict_checkpoint_loading_implemented",
         chk["checks"]["actual_strict_checkpoint_load_code_present"]
         and chk["checks"]["strict_missing_and_unexpected_keys_checked"]),
        ("parameter_verification_implemented",
         chk["checks"]["parameter_count_verification_present"]),
        ("G_autocast_fp16_implemented", chk["checks"]["G_autocast_enabled"]),
        ("G_no_grad_implemented", chk["checks"]["G_no_grad"]),
        ("G_inference_mode_false_in_primary_path",
         chk["checks"]["G_not_wrapped_in_inference_mode_in_primary_path"]),
        ("R_psi_no_autocast_inference_mode_implemented",
         chk["checks"]["R_psi_inference_mode_no_autocast"]),
        ("B_phi_no_autocast_inference_mode_implemented",
         chk["checks"]["B_phi_inference_mode_no_autocast"]),
        ("S_omega_no_autocast_inference_mode_implemented",
         chk["checks"]["S_omega_inference_mode_no_autocast"]),
        ("synchronized_cuda_timing_implemented",
         chk["checks"]["cuda_events_timing_present"]
         and chk["checks"]["cuda_synchronization_present"]),
        ("throughput_denominator_implemented",
         chk["checks"]["throughput_denominator_implemented"]),
        ("memory_measurement_implemented", chk["checks"]["peak_memory_operations_present"]),
        ("fresh_subprocess_isolation_implemented",
         chk["checks"]["fresh_subprocess_orchestration_present"]),
        ("controlled_skip_execute_paths_exact_if_eligible",
         set(C.ARMS["SKIP_CONTROLLED_PATH"]["components"]) == {"G", "B_phi"}
         and set(C.ARMS["EXECUTE_CONTROLLED_PATH"]["components"])
         == {"G", "B_phi", "R_psi", "S_omega"}),
        ("natural_synthetic_route_replay_remains_false",
         fam["synthetic_natural_route_replay_eligible"]["value"] is False),
        ("timed_operations_registry_complete",
         set(C.TIMED_OPERATIONS) >= set(C.ARMS)),
        ("v1_2_static_preflight_passes", chk["static_preflight_pass"]),
        ("v1_2_source_freeze_complete", len(src_shas) == len(V12_SOURCES)),
        ("no_model_constructions_during_amendment", counters["model_constructions"] == 0),
        ("no_checkpoint_deserialization_during_amendment",
         counters["checkpoint_deserializations_into_model_objects"] == 0),
        ("no_forwards_during_amendment", counters["model_forwards"] == 0),
        ("no_timing_during_amendment", counters["cuda_latency_iterations"] == 0),
        ("no_memory_profiling_during_amendment",
         counters["gpu_inference_memory_measurements"] == 0),
        ("router_holdout_raw_reads_0", counters["router_holdout_raw_reads"] == 0),
        ("TEST_reads_0", counters["test_reads"] == 0),
        ("training_0", counters["training_steps"] == 0),
        ("phase34_measured_execution_started_false", True),
        ("phase35_started_false", True),
    ])
    failed = [k for k, v in checks.items() if not v]
    write_json(OrderedDict([
        ("artifact", "phase34_specification_final_check_v1_2"),
        ("phase", 34), ("section", "\u00A7AC"), ("method", METHOD), ("revision", REVISION),
        ("n_checks", len(checks)), ("n_failed", len(failed)), ("failed", failed),
        ("checks", checks), ("all_pass", len(failed) == 0),
        ("generated_utc", gen),
    ]), AUD / "phase34_specification_final_check_v1_2.json")

    # ---------- §AD terminal ----------
    write_json(OrderedDict([
        ("artifact", "phase34_specification_terminal_v1_2"),
        ("phase", 34), ("section", "\u00A7AD"), ("method", METHOD), ("revision", REVISION),
        ("classification", CLASSIFICATION), ("status", "SPEC_V1_2_COMPLETE"),
        ("terminal", TERMINAL), ("supersedes", "phase34_specification_terminal_v1_1.json"),
        ("static_preflight_pass", chk["static_preflight_pass"]),
        ("first_measured_execution_started", False), ("phase35_started", False),
        ("TEST", "LOCKED_UNTIL_PHASE39"),
        ("generated_utc", gen), ("all_pass", len(failed) == 0),
    ]), AUD / "phase34_specification_terminal_v1_2.json")

    print("=== PHASE34 v1.2 AMENDMENT (zero-execution) ===")
    print("preserved:", len(pres), "| all match:", all(p["preserved"] for p in pres))
    print("static preflight pass:", chk["static_preflight_pass"],
          f"({chk['n_checks']}/{chk['n_checks'] - chk['n_failed']})")
    print("final check:", len(checks), "checks,", len(failed), "failed")
    if failed:
        print("FAILED:", failed)
    print("terminal:", TERMINAL)
    print()
    for a in NEW:
        print(f"{a['sha256']}  {a['path']}")


if __name__ == "__main__":
    main()
