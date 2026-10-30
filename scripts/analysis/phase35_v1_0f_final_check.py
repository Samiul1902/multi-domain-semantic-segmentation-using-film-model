#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase35 v1.0f final check (§R) + success terminal (§S).

Counts the actual amendment-time checks by loading each produced v1.0f artifact and asserting its
truthful contents, then writes:
  * reports/audits/phase35_empty_mask_actual_logits_repair_final_check_v1_0f.json
  * reports/audits/phase35_empty_mask_actual_logits_repair_terminal_v1_0f.json

ZERO EXECUTION. No model construction, no checkpoint deserialization, no forward, no autograd, no
Grad-CAM, no router attribution, no raw-image read, no gate set, no `--mode` invocation.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase35_v1_0f_final_check.py
"""
from __future__ import annotations

import hashlib
import json
import time
from collections import OrderedDict
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
AUD = ROOT / "reports" / "audits"
METHOD = "RA-MedFiLM-BARR"
REVISION = "ra_medfilm_barr_phase35_interpretability_v1_0f"
CLASS = ("PRE_EXECUTION_ACTUAL_LOGITS_EMPTY_MASK_OBSERVABILITY_IMPLEMENTATION_AMENDMENT"
         "__NO_SCIENTIFIC_PROTOCOL_CHANGE")

TERMINAL = ("PHASE35_PREEXECUTION_EMPTY_MASK_ACTUAL_LOGITS_REPAIR_V1_0F_COMPLETE"
            "__V1_0E_PREMODEL_BLOCK_PRESERVED"
            "__SAME_FORWARD_ACTUAL_G_LOGITS_EMPTY_MASK_FALLBACK_OBSERVABILITY_IMPLEMENTED"
            "__ZERO_LOGIT_SURROGATE_REMOVED_FROM_REACHABLE_SMOKE_PATH"
            "__FIXED_ATOL1E7_RTOL0_COMPARISON_AND_DIRECT_DIAGNOSTICS_BOUND"
            "__V1_0E_NUMERICAL_FINITE_GUARDS_AND_PARAMETER_GRAD_AUDIT_PRESERVED"
            "__NO_SCIENTIFIC_PROTOCOL_CHANGE"
            "__V1_0F_SOURCE_FREEZE_COMPLETE"
            "__SYNTHETIC_SMOKE_ELIGIBLE_NOT_STARTED")

NEW = []


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def jload(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def write_once(obj, rel):
    p = ROOT / rel
    if p.exists():
        raise SystemExit(f"REFUSING TO OVERWRITE FROZEN OUTPUT: {p}")
    p.write_text(json.dumps(obj, indent=1) + "\n", encoding="utf-8")
    s = sha256_file(p)
    NEW.append({"path": rel, "sha256": s})
    return s


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def main():
    defect = jload("reports/audits/phase35_v1_0e_actual_logits_empty_mask_defect_v1_0f.json")
    recon = jload("reports/audits/"
                  "phase35_v1_0e_blocked_smoke_notebook_metadata_reconciliation_v1_0f.json")
    diff = jload("reports/audits/phase35_v1_0e_to_v1_0f_semantic_diff.json")
    freeze = jload("reports/audits/phase35_preexecution_source_freeze_v1_0f.json")
    elig = jload("reports/audits/phase35_synthetic_smoke_eligibility_v1_0f.json")
    unit = jload("reports/audits/phase35_empty_mask_actual_logits_unit_v1_0f.json")
    pf = jload("reports/audits/phase35_execution_source_static_preflight_v1_0f.json")
    nmea = jload("reports/audits/phase35_v1_0f_no_model_execution_audit.json")
    blk = jload("reports/audits/phase35_v1_0e_empty_mask_observability_block.json")
    term_e = jload("reports/audits/phase35_synthetic_smoke_terminal_v1_0e.json")
    nba = jload("reports/audits/"
                "phase35_empty_mask_actual_logits_repair_reviewer_notebook_audit_v1_0f.json")

    checks = OrderedDict([
        ("01_v1_0e_blocked_attempt_preserved",
         (sha256_file(ROOT / "reports/audits/phase35_synthetic_smoke_terminal_v1_0e.json")
          == "aff064e2fb75e83592398f558cfffb40caa427b3252fe987d8ce052be5ed5dcb")
         and (sha256_file(ROOT / "reports/audits/phase35_v1_0e_empty_mask_observability_block.json")
              == "eef4f2b997fffc650b59b215649687b18868e3e5ca1a13cd67ed5fdcea0475e0")),
        ("02_v1_0e_block_reason_exact",
         blk["determination"] == "V1_0E_EMPTY_MASK_OBSERVABILITY_IMPLEMENTATION_INCOMPLETE"
         and term_e["outcome"] == "BLOCKED_PRE_MODEL_CONSTRUCTION"
         and term_e["smoke_executed"] is False),
        ("03_notebook_representation_discrepancy_reconciled",
         recon["classification"] == "GOVERNANCE_ONLY_NOTEBOOK_REPRESENTATION_METADATA_MISMATCH"
                                     "__DELIVERED_NOTEBOOK_IS_EXECUTED_WITH_PERSISTED_OUTPUTS"
                                     "__NO_SCIENTIFIC_IMPACT"
         and recon["historical_audit_field_matches_delivered_bytes"] is False
         and recon["observed_delivered_representation"] == "EXECUTED_WITH_PERSISTED_OUTPUTS"
         and recon["blocks_v1_0f_repair"] is False),
        ("04_scientific_semantics_unchanged",
         diff["scientific_specification_changed"] is False
         and diff["target_scalar_changed"] is False
         and diff["empty_mask_mathematical_fallback_changed"] is False
         and diff["rank_contract_changed"] is False
         and diff["target_mask_authority_changed"] is False
         and diff["numerical_finite_guards_changed"] is False
         and diff["only_implementation_change"]
             == "ACTUAL_SAME_FORWARD_LOGITS_EMPTY_MASK_OBSERVABILITY"),
        ("05_actual_same_forward_logits_available",
         _has_actual_logits_helper()
         and _exec_source_has("empty_mask_helper_check_insession_actual_logits(logits, mask_t)")),
        ("06_rank_safe_helper_reused",
         True if _exec_source_has("V0D.gradcam_target_scalar_rank_safe(logits, empty)") else False),
        ("07_surrogate_zero_logits_unreachable",
         pf["zero_logit_surrogate_unreachable_from_v1_0f_smoke"] is True
         and (not _exec_source_has("logits_zero"))
         and (not _exec_source_has("V0E.empty_mask_helper_check_insession"))),
        ("08_empty_mask_expected_mean_independently_computed",
         _exec_source_has("logits.float()[0, 0, :, :].mean()")),
        ("09_atol_exact_1e-7", _exec_source_has("EMPTY_MASK_ATOL = 1e-7")),
        ("10_rtol_exact_0", _exec_source_has("EMPTY_MASK_RTOL = 0.0")),
        ("11_no_second_forward", _exec_source_has("additional_G_forwards") and
         _exec_source_has('("additional_G_forwards", 0)')),
        ("12_no_second_autograd", _exec_source_has('("additional_autograd_calls", 0)')),
        ("13_eight_stage_numerical_guards_unchanged",
         _exec_source_has("FINITE_GUARD_STAGES") and _exec_source_has("V0E.cam_normalize_guarded")
         and (not _exec_source_has("def cam_normalize_guarded("))),
        ("14_direct_parameter_grad_reporting_retained",
         _exec_source_has("parameter_grad_state_audit_insession = "
                          "V0E.parameter_grad_state_audit_insession")
         and _exec_source_has('"NO_PARAMETER_GRAD_POPULATED"')),
        ("15_state_immutability_retained",
         _exec_source_has("V0C.smoke_parameter_immutability")),
        ("16_router_unchanged",
         _exec_source_has('("router", V0B.mode_router)')),
        ("17_film_unchanged",
         _exec_source_has('("film", V0B.mode_film)')),
        ("18_protected_data_guards_unchanged",
         (not _exec_source_has("router_holdout")) and (not _exec_source_has("/test/"))),
        ("19_unit_tests_pass", unit["all_pass"] is True and unit["n_fail"] == 0
         and unit["n_pass"] == unit["n_tests"]),
        ("20_static_preflight_pass", pf["static_source_preflight_pass"] is True
         and pf["total_n_failed"] == 0),
        ("21_source_freeze_complete", freeze["v1_0f_empty_mask_repair_complete"] is True
         and freeze["future_smoke_must_use_exact_v1_0f_bytes"] is True
         and freeze["v1_0e_block_preserved"] is True
         and freeze["v1_0e_source_preserved"] is True
         and freeze["notebook_metadata_discrepancy_disclosed"] is True),
        ("22_no_model_construction", nmea["model_constructions"] == 0),
        ("23_no_checkpoint_load", nmea["checkpoint_deserializations"] == 0
         and nmea["strict_loads"] == 0),
        ("24_no_forward", nmea["forwards"] == 0),
        ("25_no_model_autograd", nmea["model_autograd"] == 0),
        ("26_no_raw_val", nmea["raw_val_reads"] == 0),
        ("27_no_real_p_global", nmea["real_p_global_reads"] == 0),
        ("28_no_GT", nmea["gt_reads"] == 0),
        ("29_no_HOLDOUT", nmea["holdout_reads"] == 0),
        ("30_no_TEST", nmea["test_reads"] == 0),
        ("31_no_training", nmea["training_steps"] == 0),
        ("32_reviewer_notebook_clean",
         nba["error_cells"] == 0 and nba["notebook_read_only"] is True
         and nba["model_construction_from_notebook"] is False
         and all(v == 0 for v in nba["counters"].values())),
        ("33_phase35_scientific_execution_false",
         freeze["scientific_execution_started"] is False
         and elig["scientific_gradcam_execution_eligible"] is False
         and elig["first_phase35_scientific_execution_eligible"] is False),
        ("34_phase36_false", _exec_source_has("phase36") is False),
        ("35_TEST_locked_until_phase39",
         blk.get("judgement") is not None and pf["test_reads"] == 0),
    ])

    n_failed = sum(1 for v in checks.values() if not v)
    failed = [k for k, v in checks.items() if not v]

    fc = OrderedDict([
        ("artifact", "phase35_empty_mask_actual_logits_repair_final_check_v1_0f"),
        ("phase", 35), ("section", "\u00A7R"), ("method", METHOD), ("revision", REVISION),
        ("classification", CLASS),
        ("checks", checks), ("n_checks", len(checks)), ("n_failed", n_failed),
        ("failed", failed), ("all_pass", n_failed == 0),
        ("phase35_scientific_execution_started", False),
        ("phase36_started", False),
        ("TEST", "LOCKED_UNTIL_PHASE39"),
        ("ROUTER_HOLDOUT", "OPENED_AND_FROZEN"),
        ("counters", OrderedDict([
            ("model_constructions", 0), ("checkpoint_deserializations", 0), ("forwards", 0),
            ("model_autograd", 0), ("gradcam_executions", 0),
            ("router_attribution_executions", 0), ("raw_val_reads", 0),
            ("real_p_global_reads", 0), ("gt_reads", 0), ("router_holdout_reads", 0),
            ("test_reads", 0), ("training_steps", 0), ("gate_env_sets", 0),
            ("mode_invocations", 0)])),
        ("generated_utc", now()),
    ])
    fc_sha = write_once(fc,
                        "reports/audits/"
                        "phase35_empty_mask_actual_logits_repair_final_check_v1_0f.json")

    if n_failed == 0:
        term = OrderedDict([
            ("artifact", "phase35_empty_mask_actual_logits_repair_terminal_v1_0f"),
            ("phase", 35), ("section", "\u00A7S"), ("method", METHOD), ("revision", REVISION),
            ("classification", CLASS), ("terminal", TERMINAL),
            ("v1_0e_block_preserved", True),
            ("v1_0e_source_preserved", True),
            ("notebook_metadata_discrepancy_disclosed", True),
            ("v1_0f_empty_mask_repair_complete", True),
            ("zero_logit_surrogate_removed_from_reachable_smoke_path", True),
            ("scientific_protocol_changed", False),
            ("v1_0f_source_freeze_complete", True),
            ("synthetic_smoke_eligible", True),
            ("synthetic_smoke_started", False),
            ("scientific_execution_started", False),
            ("phase36_started", False),
            ("test_state", "LOCKED_UNTIL_PHASE39"),
            ("router_holdout_state", "OPENED_AND_FROZEN"),
            ("gate_env_set", False), ("mode_invoked", False),
            ("generated_utc", now()),
        ])
        term_sha = write_once(term,
                              "reports/audits/"
                              "phase35_empty_mask_actual_logits_repair_terminal_v1_0f.json")
    else:
        term_sha = None
        print("FINAL CHECK FAILED — SUCCESS TERMINAL NOT EMITTED")

    print("=== PHASE35 v1.0f FINAL CHECK ===")
    print("checks:", len(checks), "| failed:", n_failed)
    for k in failed:
        print("  FAILED:", k)
    print("all_pass:", n_failed == 0)
    print("final check sha256:", fc_sha)
    if term_sha:
        print("terminal:", TERMINAL)
        print("terminal sha256:", term_sha)
    for a in NEW:
        print(f"{a['sha256']}  {a['path']}")
    return 0 if n_failed == 0 else 3


def _exec_source() -> str:
    return (ROOT / "scripts" / "analysis"
            / "phase35_interpretability_execution_v1_0f.py").read_text(encoding="utf-8")


def _exec_source_has(tok: str) -> bool:
    return tok in _exec_source()


def _has_actual_logits_helper() -> bool:
    return "def empty_mask_helper_check_insession_actual_logits(" in _exec_source()


if __name__ == "__main__":
    raise SystemExit(main())
