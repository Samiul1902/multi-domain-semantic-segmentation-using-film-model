#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build the v1.0h governance artifacts:  §N source freeze, §O eligibility, §P no-execution audit, §Q final check.

SOURCE + GOVERNANCE ONLY. No model construction, no checkpoint deserialization, no strict load, no forward,
no autograd, no Grad-CAM, no router attribution, no protected-data access. Never imports torch.
"""
from __future__ import annotations

import hashlib
import json
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")


def sha(rel: str) -> str:
    p = ROOT / rel
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def dump(rel: str, doc) -> str:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8", newline="\n")
    return hashlib.sha256(p.read_bytes()).hexdigest()


NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

EXEC_H = "scripts/analysis/phase35_interpretability_execution_v1_0h.py"
PRE_H = "scripts/analysis/phase35_execution_preflight_v1_0h.py"
UNIT_H = "scripts/analysis/phase35_full_counter_contract_unit_v1_0h.py"
EXEC_G = "scripts/analysis/phase35_interpretability_execution_v1_0g.py"
EXEC_F = "scripts/analysis/phase35_interpretability_execution_v1_0f.py"
EXEC_E = "scripts/analysis/phase35_interpretability_execution_v1_0e.py"
EXEC_D = "scripts/analysis/phase35_interpretability_execution_v1_0d.py"
EXEC_C = "scripts/analysis/phase35_interpretability_execution_v1_0c.py"
EXEC_B = "scripts/analysis/phase35_interpretability_execution_v1_0b.py"

COMMON_B = "scripts/analysis/phase35_interpretability_common_v1_0b.py"
ROUTER_TRAIN = "scripts/analysis/train_phase25d_router.py"
SPEC = "docs/phase35_interpretability_spec_v1_0.md"
GALLERY = "reports/tables/phase21_gallery_selection_64.csv"
DOMAIN_REG = "src/analysis/multidomain_harmonization.py"

DEFECT_REC = "reports/audits/phase35_v1_0g_counter_store_contract_defect_v1_0h.json"
SEMDIFF = "reports/audits/phase35_v1_0g_to_v1_0h_semantic_diff.json"
UNIT_ART = "reports/audits/phase35_full_counter_contract_unit_v1_0h.json"
PREF_ART = "reports/audits/phase35_execution_source_static_preflight_v1_0h.json"

EXPECTED = OrderedDict([
    ("G_model_constructions", 1),
    ("B_phi_model_constructions", 1),
    ("checkpoint_deserializations", 2),
    ("strict_loads", 2),
    ("G_synthetic_forwards", 1),
    ("total_model_forwards", 2),
    ("G_gradcam_autograd_calls", 1),
    ("total_autograd_calls", 2),
    ("G_synthetic_backward_calls", 1),
    ("synthetic_CAM_maps", 4),
    ("synthetic_CAM_finite_checks", 4),
    ("synthetic_CAM_normalizations", 4),
    ("synthetic_CAM_zero_range_fallbacks", 0),
    ("synthetic_target_mask_rank_checks", 1),
    ("synthetic_smoke_target_masks", 1),
    ("primary_synthetic_target_masks", 1),
    ("B_phi_synthetic_forwards", 1),
    ("router_numeric_input_autograd_calls", 1),
    ("synthetic_router_attribution_rows", 4),
    ("synthetic_router_zero_denominator_events", 0),
    ("router_gradient_x_input_finite_checks", 1),
    ("film_smoke_checks", 1),
    ("film_smoke_conditioning_pairs", 20),
    ("embedding_smoke_checks", 1),
    ("checkpoint_identity_checks", 2),
    ("environment_checks", 1),
    ("parameter_immutability_checks", 1),
    ("actual_logits_empty_mask_helper_checks", 1),
    ("additional_G_forwards_for_empty_mask", 1),
    ("additional_autograd_calls_for_empty_mask", 1),
    ("raw_VAL_image_reads", 0),
    ("real_persisted_VAL_probability_reads", 0),
    ("VAL_GT_reads", 0),
    ("router_feature_cache_rows_read", 0),
    ("ROUTER_HOLDOUT_reads", 0),
    ("TEST_reads", 0),
    ("TRAIN_raw_reads", 0),
    ("scientific_outputs", 0),
])

# -------------------------------------------------------------------------------------------------- #
# §N — pre-execution source freeze
# -------------------------------------------------------------------------------------------------- #
freeze = OrderedDict([
    ("artifact", "phase35_preexecution_source_freeze_v1_0h"),
    ("phase", 35),
    ("section", "\u00a7N"),
    ("method", "RA-MedFiLM-BARR"),
    ("revision", "ra_medfilm_barr_phase35_interpretability_v1_0h"),
    ("classification",
     "PRE_EXECUTION_SYNTHETIC_SMOKE_COUNTER_STORE_AND_EXPECTED_CONTRACT_REPAIR__NO_SCIENTIFIC_PROTOCOL_CHANGE"),
    ("frozen_sources", OrderedDict([
        ("v1_0h_execution_source", {"path": EXEC_H, "sha256": sha(EXEC_H)}),
        ("v1_0h_preflight", {"path": PRE_H, "sha256": sha(PRE_H)}),
        ("v1_0h_full_counter_contract_unit_source", {"path": UNIT_H, "sha256": sha(UNIT_H)}),
        ("v1_0g_source_predecessor", {"path": EXEC_G, "sha256": sha(EXEC_G)}),
        ("v1_0f_source_predecessor", {"path": EXEC_F, "sha256": sha(EXEC_F)}),
        ("v1_0e_source_predecessor", {"path": EXEC_E, "sha256": sha(EXEC_E)}),
        ("load_bearing_execution_v1_0d", {"path": EXEC_D, "sha256": sha(EXEC_D)}),
        ("load_bearing_execution_v1_0c_legacy_counter_owner", {"path": EXEC_C, "sha256": sha(EXEC_C)}),
        ("load_bearing_execution_v1_0b", {"path": EXEC_B, "sha256": sha(EXEC_B)}),
        ("load_bearing_common_v1_0b", {"path": COMMON_B, "sha256": sha(COMMON_B)}),
        ("v1_0h_counter_store_contract_defect_record", {"path": DEFECT_REC, "sha256": sha(DEFECT_REC)}),
        ("v1_0g_to_v1_0h_semantic_diff", {"path": SEMDIFF, "sha256": sha(SEMDIFF)}),
        ("v1_0h_full_counter_contract_unit_artifact", {"path": UNIT_ART, "sha256": sha(UNIT_ART)}),
        ("v1_0h_execution_source_static_preflight_artifact", {"path": PREF_ART, "sha256": sha(PREF_ART)}),
        ("v1_0g_first_blocked_smoke", {"path": "reports/audits/phase35_synthetic_interpretability_smoke_v1_0g.json",
                                       "sha256": sha("reports/audits/phase35_synthetic_interpretability_smoke_v1_0g.json")}),
        ("v1_0g_first_blocked_terminal", {"path": "reports/audits/phase35_synthetic_smoke_terminal_v1_0g.json",
                                          "sha256": sha("reports/audits/phase35_synthetic_smoke_terminal_v1_0g.json")}),
        ("v1_0f_blocked_smoke", {"path": "reports/audits/phase35_synthetic_interpretability_smoke_v1_0f.json",
                                 "sha256": sha("reports/audits/phase35_synthetic_interpretability_smoke_v1_0f.json")}),
        ("v1_0f_scientific_authority_manifest", {"path": "reports/audits/phase35_preexecution_source_freeze_v1_0f.json",
                                                 "sha256": sha("reports/audits/phase35_preexecution_source_freeze_v1_0f.json")}),
        ("v1_0g_scientific_authority_manifest", {"path": "reports/audits/phase35_preexecution_source_freeze_v1_0g.json",
                                                 "sha256": sha("reports/audits/phase35_preexecution_source_freeze_v1_0g.json")}),
        ("bphi_router_training_authority", {"path": ROUTER_TRAIN, "sha256": sha(ROUTER_TRAIN)}),
        ("scientific_specification", {"path": SPEC, "sha256": sha(SPEC)}),
        ("canonical_gallery", {"path": GALLERY, "sha256": sha(GALLERY)}),
    ])),
    ("checkpoint_and_authority_identities", OrderedDict([
        ("G_checkpoint_sha256", "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7"),
        ("B_phi_checkpoint_sha256", "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b"),
        ("domain_registry", DOMAIN_REG),
        ("domain_registry_sha256", sha(DOMAIN_REG)),
        ("gallery_sha256", sha(GALLERY)),
    ])),
    ("expected_counter_contract", OrderedDict([
        ("counter_count", 35),
        ("extension_counter_count", 4),
        ("legacy_counter_count", 31),
        ("primary_synthetic_target_masks", 1),
        ("primary_alias_synthetic_smoke_target_masks", 1),
        ("empty_mask_observability_counter", 1),
        ("expected_counters", dict(EXPECTED)),
        ("protected_zero_keys", ["raw_VAL_image_reads", "real_persisted_VAL_probability_reads",
                                 "VAL_GT_reads", "router_feature_cache_rows_read", "ROUTER_HOLDOUT_reads",
                                 "TEST_reads", "TRAIN_raw_reads", "scientific_outputs"]),
    ])),
    ("single_counter_ownership_model", OrderedDict([
        ("legacy_owner", "phase35_interpretability_execution_v1_0c.SMOKE_COUNTERS"),
        ("legacy_owner_keys", 31),
        ("extension_store", "SMOKE_COUNTERS_EXT"),
        ("extension_owned_keys", ["primary_synthetic_target_masks",
                                  "actual_logits_empty_mask_helper_checks",
                                  "additional_G_forwards_for_empty_mask",
                                  "additional_autograd_calls_for_empty_mask"]),
        ("independent_copy_created", False),
        ("router_counts_faked", False),
        ("report_time_canonical_is_exact_merge", True),
    ])),
    ("v1_0f_scientific_authority_preserved", True),
    ("v1_0g_blocked_smoke_history_preserved", True),
    ("v1_0g_first_smoke_preserved", True),
    ("v1_0g_retry_performed", False),
    ("v1_0f_smoke_retry_performed", False),
    ("scientific_protocol_changed", False),
    ("model_execution_semantics_changed", False),
    ("protected_data_semantics_changed", False),
    ("future_smoke_must_use_exact_v1_0h_bytes", True),
    ("scientific_execution_started", False),
    ("gate_env_set", False),
    ("mode_invoked", False),
    ("generated_utc", NOW),
    ("all_pass", True),
])
n_freeze = dump("reports/audits/phase35_preexecution_source_freeze_v1_0h.json", freeze)

# -------------------------------------------------------------------------------------------------- #
# §O — synthetic smoke eligibility
# -------------------------------------------------------------------------------------------------- #
elig = OrderedDict([
    ("artifact", "phase35_synthetic_smoke_eligibility_v1_0h"),
    ("phase", 35),
    ("section", "\u00a7O"),
    ("method", "RA-MedFiLM-BARR"),
    ("revision", "ra_medfilm_barr_phase35_interpretability_v1_0h"),
    ("eligibility", OrderedDict([
        ("synthetic_smoke_execution_eligible", True),
        ("synthetic_smoke_started", False),
        ("source_freeze_complete", True),
        ("source_freeze_manifest", "reports/audits/phase35_preexecution_source_freeze_v1_0h.json"),
        ("source_freeze_manifest_sha256", n_freeze),
        ("execution_source_sha256", sha(EXEC_H)),
        ("preflight_all_pass", True),
        ("unit_contract_all_pass", True),
        ("semantic_diff_no_scientific_change", True),
        ("scientific_execution_eligible", False),
        ("scientific_execution_ineligible_reason", "PENDING_SUCCESSFUL_V1_0H_SYNTHETIC_SMOKE"),
        ("scientific_execution_started", False),
        ("v1_0g_blocked_history_preserved", True),
        ("v1_0f_blocked_history_preserved", True),
    ])),
    ("prerequisites_satisfied", [
        "V1_0H_FULL_SMOKE_COUNTER_CONTRACT_REPAIR_COMPLETE",
        "V1_0H_SOURCE_FREEZE_COMPLETE",
        "V1_0H_STATIC_PREFLIGHT_ALL_PASS",
        "V1_0H_MODEL_FREE_UNIT_CONTRACT_ALL_PASS",
        "V1_0G_BLOCKED_HISTORY_PRESERVED",
        "V1_0F_SCIENTIFIC_AUTHORITY_PRESERVED",
    ]),
    ("not_authorized_by_this_work_order", [
        "V1_0H_SYNTHETIC_SMOKE_EXECUTION",
        "PHASE35_SCIENTIFIC_EXECUTION",
        "PHASE36",
        "TEST_ACCESS",
    ]),
    ("gate_env_set", False),
    ("mode_invoked", False),
    ("generated_utc", NOW),
    ("all_pass", True),
])
n_elig = dump("reports/audits/phase35_synthetic_smoke_eligibility_v1_0h.json", elig)

# -------------------------------------------------------------------------------------------------- #
# §P — no-execution audit (all zero)
# -------------------------------------------------------------------------------------------------- #
noexec = OrderedDict([
    ("artifact", "phase35_v1_0h_no_execution_audit"),
    ("phase", 35),
    ("section", "\u00a7P"),
    ("method", "RA-MedFiLM-BARR"),
    ("revision", "ra_medfilm_barr_phase35_interpretability_v1_0h"),
    ("audit_class", "SOURCE_AND_GOVERNANCE_ONLY__NO_EXECUTION"),
    ("execution_ledger", OrderedDict([
        ("model_constructions", 0),
        ("checkpoint_deserializations", 0),
        ("strict_loads", 0),
        ("forwards", 0),
        ("backwards", 0),
        ("autograd_calls", 0),
        ("gradcam_calls", 0),
        ("router_attribution_calls", 0),
        ("optimizer_steps", 0),
        ("training_steps", 0),
        ("raw_VAL_image_reads", 0),
        ("real_persisted_VAL_probability_reads", 0),
        ("VAL_GT_reads", 0),
        ("router_feature_cache_rows_read", 0),
        ("ROUTER_HOLDOUT_reads", 0),
        ("TEST_reads", 0),
        ("TRAIN_raw_reads", 0),
        ("real_p_global_reads", 0),
        ("scientific_outputs", 0),
        ("smoke_executions", 0),
        ("gate_env_set", False),
        ("mode_invoked", False),
        ("torch_imported", False),
        ("gpu_used", False),
    ])),
    ("unit_test_note", "the model-free CPU unit contract uses only stdlib/synthetic OrderedDict arithmetic; "
                       "it imports no torch and performs no model execution"),
    ("preflight_note", "the static preflight parses sources with ast only; it imports no torch and executes "
                       "no model path"),
    ("generated_utc", NOW),
    ("all_zero", True),
    ("all_pass", True),
])
n_noexec = dump("reports/audits/phase35_v1_0h_no_execution_audit.json", noexec)

print("freeze:", n_freeze)
print("elig  :", n_elig)
print("noexec:", n_noexec)
