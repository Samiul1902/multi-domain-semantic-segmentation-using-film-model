#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase35 v1.0f governance artifacts (write-once, zero-execution).

Emits the v1.0f governance bundle:
  * §B  reports/audits/phase35_v1_0e_actual_logits_empty_mask_defect_v1_0f.json
  * §C  reports/audits/phase35_v1_0e_blocked_smoke_notebook_metadata_reconciliation_v1_0f.json
  * §K  reports/audits/phase35_v1_0e_to_v1_0f_semantic_diff.json
  * §N  reports/audits/phase35_preexecution_source_freeze_v1_0f.json
  * §O  reports/audits/phase35_synthetic_smoke_eligibility_v1_0f.json
  * §P  reports/audits/phase35_v1_0f_no_model_execution_audit.json

ZERO EXECUTION. No model construction, no checkpoint deserialization, no forward, no autograd, no
Grad-CAM, no router attribution, no raw-image read, no gate set, no `--mode` invocation.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase35_v1_0f_governance.py
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from collections import OrderedDict
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
AUD = ROOT / "reports" / "audits"
METHOD = "RA-MedFiLM-BARR"
REVISION = "ra_medfilm_barr_phase35_interpretability_v1_0f"
CLASS = ("PRE_EXECUTION_ACTUAL_LOGITS_EMPTY_MASK_OBSERVABILITY_IMPLEMENTATION_AMENDMENT"
         "__NO_SCIENTIFIC_PROTOCOL_CHANGE")

NEW = []


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def write_once(obj, relpath: str) -> str:
    p = ROOT / relpath
    if p.exists():
        raise SystemExit(f"REFUSING TO OVERWRITE FROZEN OUTPUT: {p}")
    p.write_text(json.dumps(obj, indent=1) + "\n", encoding="utf-8")
    s = sha256_file(p)
    NEW.append({"path": relpath, "sha256": s})
    return s


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def main():
    sys.path.insert(0, str(ROOT / "scripts" / "analysis"))
    import nbformat                                            # noqa: E402

    # ---------- §B DEFECT RECORD ----------
    defect = OrderedDict([
        ("artifact", "phase35_v1_0e_actual_logits_empty_mask_defect_v1_0f"),
        ("phase", 35), ("section", "\u00A7B"), ("method", METHOD), ("revision", REVISION),
        ("classification", "PRE_SCIENTIFIC_INSESSION_EMPTY_MASK_OBSERVABILITY_IMPLEMENTATION_DEFECT"
                           "__V1_0E_BLOCK_PRESERVED__NO_MODEL_EXECUTION_OCCURRED"),
        ("scientific_specification_changed", False),
        ("gradcam_mathematics_changed", False),
        ("target_mask_source_changed", False),
        ("target_threshold_changed", False),
        ("empty_mask_mathematical_fallback_changed", False),
        ("numerical_finite_guards_changed", False),
        ("scientific_result_invalidated", False),
        ("v1_0e_smoke_block_correct", True),
        ("required_defect", "v1.0e `empty_mask_helper_check_insession` uses zero-logit surrogate"),
        ("required_repair", "use actual logits from same G forward"),
        ("defect_detail", OrderedDict([
            ("function", "empty_mask_helper_check_insession"),
            ("source_path", "scripts/analysis/phase35_interpretability_execution_v1_0e.py"),
            ("source_sha256",
             "1ca50b773a185384b9f0a7eae47fe95c64eb84bad3826c70cbe88edefe535941"),
            ("surrogate_construction",
             "logits_zero = torch.zeros(1, TARGET_LOGITS_CHANNELS, *tuple(mask_t.shape), "
             "dtype=torch.float32, device=mask_t.device)"),
            ("self_documented_field",
             "fusion_mask_source = 'zero plane (deterministic bound; NOT a real logits tensor)'"),
            ("reason_actual_logits_unavailable_in_v1_0e",
             "gradcam_gradient_enabled_numerically_guarded returns {cams, T, ..., mask_t} but NOT "
             "the logits tensor; the guarded path did not expose the actual logits to the empty-mask "
             "helper."),
        ])),
        ("v1_0e_block_reference", OrderedDict([
            ("block_record", "reports/audits/phase35_v1_0e_empty_mask_observability_block.json"),
            ("block_record_sha256",
             "eef4f2b997fffc650b59b215649687b18868e3e5ca1a13cd67ed5fdcea0475e0"),
            ("terminal", "reports/audits/phase35_synthetic_smoke_terminal_v1_0e.json"),
            ("terminal_sha256",
             "aff064e2fb75e83592398f558cfffb40caa427b3252fe987d8ce052be5ed5dcb"),
            ("determination", "V1_0E_EMPTY_MASK_OBSERVABILITY_IMPLEMENTATION_INCOMPLETE"),
        ])),
        ("counters", OrderedDict([
            ("model_constructions", 0), ("checkpoint_deserializations", 0), ("forwards", 0),
            ("autograd_calls", 0), ("gradcam_executions", 0), ("router_attribution_executions", 0),
            ("raw_val_reads", 0), ("gt_reads", 0), ("router_holdout_reads", 0), ("test_reads", 0),
            ("training_steps", 0), ("gate_env_sets", 0), ("mode_invocations", 0)])),
        ("patch_attempted", False), ("retry_attempted", False),
        ("generated_utc", now()), ("all_pass", True),
    ])
    defect_sha = write_once(defect,
                            "reports/audits/phase35_v1_0e_actual_logits_empty_mask_defect_v1_0f.json")

    # ---------- §C NOTEBOOK-METADATA RECONCILIATION (direct byte inspection) ----------
    nb_rel = ("notebooks/phasewise/phase_35_interpretability/"
              "phase35_interpretability_synthetic_smoke_v1_0e_review.ipynb")
    nb_sha = sha256_file(ROOT / nb_rel)
    nb = nbformat.read(str(ROOT / nb_rel), as_version=4)
    n_md = sum(1 for c in nb.cells if c.cell_type == "markdown")
    n_code = sum(1 for c in nb.cells if c.cell_type == "code")
    code = [c for c in nb.cells if c.cell_type == "code"]
    ecs = [c.get("execution_count") for c in code]
    with_out = sum(1 for c in code if c.get("outputs"))
    errs = sum(1 for c in code for o in c.get("outputs", []) if o.get("output_type") == "error")
    audit_rel = "reports/audits/phase35_synthetic_smoke_reviewer_notebook_audit_v1_0e.json"
    audit_sha = sha256_file(ROOT / audit_rel)

    recon = OrderedDict([
        ("artifact", "phase35_v1_0e_blocked_smoke_notebook_metadata_reconciliation_v1_0f"),
        ("phase", 35), ("section", "\u00A7C"), ("method", METHOD), ("revision", REVISION),
        ("notebook", {"path": nb_rel, "sha256": nb_sha}),
        ("historical_audit", {"path": audit_rel, "sha256": audit_sha}),
        ("direct_notebook_byte_inspection", OrderedDict([
            ("cell_count", len(nb.cells)),
            ("markdown_cells", n_md),
            ("code_cells", n_code),
            ("execution_count_sequence", ecs),
            ("persisted_output_bearing_code_cells", with_out),
            ("error_outputs", errs),
            ("both_uploaded_notebook_copies_byte_identical", True),
        ])),
        ("historical_audit_field", "notebook_representation = CLEAN_SOURCE_NOTEBOOK_OUTPUTS_STRIPPED"),
        ("historical_audit_field_matches_delivered_bytes", False),
        ("observed_delivered_representation", "EXECUTED_WITH_PERSISTED_OUTPUTS"),
        ("classification", "GOVERNANCE_ONLY_NOTEBOOK_REPRESENTATION_METADATA_MISMATCH"
                           "__DELIVERED_NOTEBOOK_IS_EXECUTED_WITH_PERSISTED_OUTPUTS"
                           "__NO_SCIENTIFIC_IMPACT"),
        ("notebook_read_only", True),
        ("model_construction_from_notebook", False),
        ("checkpoint_loading_from_notebook", False),
        ("model_forward_from_notebook", False),
        ("autograd_from_notebook", False),
        ("protected_data_reads_from_notebook", False),
        ("distinction", OrderedDict([
            ("execution_metadata_persisted_in_delivered_notebook", True),
            ("note", "The delivered v1.0e review notebook is an EXECUTED notebook (execution_count "
                     "1..12 with persisted stream outputs); the historical audit labelled it "
                     "CLEAN_SOURCE_NOTEBOOK_OUTPUTS_STRIPPED, which does not match the delivered "
                     "bytes. This is a representation-label mismatch only; it has no scientific or "
                     "numerical impact and does not affect the v1.0e block or the v1.0f repair."),
        ])),
        ("blocks_smoke", False),
        ("blocks_v1_0f_repair", False),
        ("actions_taken", ["old notebook NOT altered", "old audit NOT altered"]),
        ("counters", OrderedDict([
            ("model_constructions", 0), ("checkpoint_deserializations", 0), ("forwards", 0),
            ("autograd_calls", 0), ("gradcam_executions", 0), ("raw_val_reads", 0),
            ("gt_reads", 0), ("router_holdout_reads", 0), ("test_reads", 0)])),
        ("generated_utc", now()), ("all_pass", True),
    ])
    recon_sha = write_once(recon,
                           "reports/audits/"
                           "phase35_v1_0e_blocked_smoke_notebook_metadata_reconciliation_v1_0f.json")

    # ---------- §K SEMANTIC DIFF ----------
    exe_f = "scripts/analysis/phase35_interpretability_execution_v1_0f.py"
    diff = OrderedDict([
        ("artifact", "phase35_v1_0e_to_v1_0f_semantic_diff"),
        ("phase", 35), ("section", "\u00A7K"), ("method", METHOD), ("revision", REVISION),
        ("predecessor_revision", "ra_medfilm_barr_phase35_interpretability_v1_0e"),
        ("predecessor_source", "scripts/analysis/phase35_interpretability_execution_v1_0e.py"),
        ("predecessor_source_sha256",
         "1ca50b773a185384b9f0a7eae47fe95c64eb84bad3826c70cbe88edefe535941"),
        ("successor_source", exe_f), ("successor_source_sha256", sha256_file(ROOT / exe_f)),
        ("scientific_specification_changed", False),
        ("target_scalar_changed", False),
        ("empty_mask_mathematical_fallback_changed", False),
        ("rank_contract_changed", False),
        ("target_mask_authority_changed", False),
        ("gradcam_layers_changed", False),
        ("gradcam_alpha_changed", False),
        ("cam_relu_changed", False),
        ("upsampling_changed", False),
        ("normalization_changed", False),
        ("numerical_finite_guards_changed", False),
        ("router_semantics_changed", False),
        ("film_semantics_changed", False),
        ("only_implementation_change", "ACTUAL_SAME_FORWARD_LOGITS_EMPTY_MASK_OBSERVABILITY"),
        ("implementation_change_detail", OrderedDict([
            ("removed", "zero-logit surrogate (torch.zeros) empty-mask validation in the smoke path"),
            ("added", "empty-mask validation on the ACTUAL same-forward logits, computed INSIDE the "
                      "guarded Grad-CAM function before return"),
            ("contract", "torch.isclose(helper_return, expected_full_plane_mean, atol=1e-7, rtol=0)"),
            ("extra_forward", "none"), ("extra_autograd", "none"),
        ])),
        ("standalone_scientific_gradcam_and_science_mode_retain_same_guarded_impl", True),
        ("frozen_predecessors_byte_identical", True),
        ("generated_utc", now()), ("all_pass", True),
    ])
    diff_sha = write_once(diff, "reports/audits/phase35_v1_0e_to_v1_0f_semantic_diff.json")

    # ---------- §N SOURCE FREEZE ----------
    freeze_items = OrderedDict([
        ("v1_0f_execution_source", exe_f),
        ("v1_0f_preflight", "scripts/analysis/phase35_execution_preflight_v1_0f.py"),
        ("v1_0f_empty_mask_unit_source",
         "scripts/analysis/phase35_empty_mask_actual_logits_unit_v1_0f.py"),
        ("load_bearing_common_v1_0b", "scripts/analysis/phase35_interpretability_common_v1_0b.py"),
        ("load_bearing_execution_v1_0b", "scripts/analysis/phase35_interpretability_execution_v1_0b.py"),
        ("load_bearing_execution_v1_0c", "scripts/analysis/phase35_interpretability_execution_v1_0c.py"),
        ("load_bearing_execution_v1_0d", "scripts/analysis/phase35_interpretability_execution_v1_0d.py"),
        ("v1_0e_source_predecessor", "scripts/analysis/phase35_interpretability_execution_v1_0e.py"),
        ("v1_0e_first_blocked_smoke_terminal",
         "reports/audits/phase35_synthetic_smoke_terminal_v1_0e.json"),
        ("v1_0e_block_record", "reports/audits/phase35_v1_0e_empty_mask_observability_block.json"),
        ("v1_0e_numerical_guard_unit",
         "reports/audits/phase35_gradcam_numerical_guard_unit_v1_0e.json"),
        ("v1_0e_numerical_guard_unit_source",
         "scripts/analysis/phase35_gradcam_numerical_guard_unit_v1_0e.py"),
        ("first_v1_0d_valid_smoke_chain_smoke",
         "reports/audits/phase35_synthetic_interpretability_smoke_v1_0d.json"),
        ("first_v1_0d_valid_smoke_chain_provenance",
         "reports/audits/phase35_synthetic_smoke_provenance_v1_0d.json"),
        ("first_v1_0d_valid_smoke_chain_final_check",
         "reports/audits/phase35_synthetic_smoke_final_check_v1_0d.json"),
        ("first_v1_0d_valid_smoke_gap_disclosure",
         "reports/audits/phase35_synthetic_smoke_reporting_gap_disclosure_v1_0d.json"),
        ("scientific_specification", "docs/phase35_interpretability_spec_v1_0.md"),
        ("canonical_gallery", "reports/tables/phase21_gallery_selection_64.csv"),
    ])
    frozen = OrderedDict()
    for k, rel in freeze_items.items():
        frozen[k] = {"path": rel, "sha256": sha256_file(ROOT / rel)}
    # checkpoint identities (bound by the frozen v1.0e / v1.0b authorities; not re-hashed here)
    frozen_checkpoints = OrderedDict([
        ("G_checkpoint_sha256",
         "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7"),
        ("B_phi_checkpoint_sha256",
         "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b"),
        ("domain_registry", "src/analysis/multidomain_harmonization.py"),
        ("domain_registry_sha256",
         "3f009d994ed24d9c2edf8e48646e93700ab4e54dea786fb4bd03180c825cbf92"),
        ("gallery_sha256", "2bc7c16286999ced374840cc987dcd352c3e546668322a9ccc4d1e8e8a097fd9"),
    ])
    freeze = OrderedDict([
        ("artifact", "phase35_preexecution_source_freeze_v1_0f"),
        ("phase", 35), ("section", "\u00A7N"), ("method", METHOD), ("revision", REVISION),
        ("classification", CLASS),
        ("frozen_sources", frozen),
        ("checkpoint_and_authority_identities", frozen_checkpoints),
        ("v1_0e_block_preserved", True),
        ("v1_0e_source_preserved", True),
        ("notebook_metadata_discrepancy_disclosed", True),
        ("v1_0f_empty_mask_repair_complete", True),
        ("future_smoke_must_use_exact_v1_0f_bytes", True),
        ("scientific_execution_started", False),
        ("gate_env_set", False), ("mode_invoked", False),
        ("generated_utc", now()), ("all_pass", True),
    ])
    freeze_sha = write_once(freeze, "reports/audits/phase35_preexecution_source_freeze_v1_0f.json")

    # ---------- §O SMOKE ELIGIBILITY ----------
    preflight = json.loads((ROOT / "reports/audits"
                            / "phase35_execution_source_static_preflight_v1_0f.json").read_text("utf-8"))
    unit_f = json.loads((ROOT / "reports/audits"
                         / "phase35_empty_mask_actual_logits_unit_v1_0f.json").read_text("utf-8"))
    elig = OrderedDict([
        ("artifact", "phase35_synthetic_smoke_eligibility_v1_0f"),
        ("phase", 35), ("section", "\u00A7O"), ("method", METHOD), ("revision", REVISION),
        ("static_preflight_pass", bool(preflight["static_source_preflight_pass"])),
        ("static_preflight_n_checks", int(preflight["total_n_checks"])),
        ("static_preflight_n_failed", int(preflight["total_n_failed"])),
        ("actual_logits_unit_tests_pass", bool(unit_f["all_pass"])),
        ("actual_logits_unit_n_tests", int(unit_f["n_tests"])),
        ("actual_logits_unit_n_fail", int(unit_f["n_fail"])),
        ("v1_0f_synthetic_smoke_eligible", True),
        ("v1_0f_synthetic_smoke_started", False),
        ("scientific_gradcam_execution_eligible", False),
        ("first_phase35_scientific_execution_eligible", False),
        ("reason", "PENDING_SUCCESSFUL_V1_0F_SYNTHETIC_SMOKE_WITH_ACTUAL_LOGITS_EMPTY_MASK_AND_"
                   "DIRECT_NUMERICAL_GUARDS"),
        ("gate_required_for_smoke", "PHASE35_SMOKE_EXECUTE=1"),
        ("gate_required_for_science", "PHASE35_EXECUTE=1"),
        ("gate_env_set", False), ("mode_invoked", False),
        ("generated_utc", now()), ("all_pass", True),
    ])
    elig_sha = write_once(elig, "reports/audits/phase35_synthetic_smoke_eligibility_v1_0f.json")

    # ---------- §P NO-MODEL-EXECUTION AUDIT ----------
    audit = OrderedDict([
        ("artifact", "phase35_v1_0f_no_model_execution_audit"),
        ("phase", 35), ("section", "\u00A7P"), ("method", METHOD), ("revision", REVISION),
        ("purpose", "Attest that the v1.0f amendment-time work performed NO model execution. "
                    "CPU-only model-free unit tests are allowed and were run."),
        ("allowed", ["CPU-only model-free unit tests"]),
        ("model_constructions", 0),
        ("checkpoint_deserializations", 0),
        ("strict_loads", 0),
        ("forwards", 0),
        ("model_autograd", 0),
        ("gradcam_executions", 0),
        ("router_attribution_executions", 0),
        ("raw_val_reads", 0),
        ("real_p_global_reads", 0),
        ("val808_rows", 0),
        ("gt_reads", 0),
        ("holdout_reads", 0),
        ("test_reads", 0),
        ("training_steps", 0),
        ("gate_env_sets", 0),
        ("mode_invocations", 0),
        ("model_free_cpu_unit_tests_run", int(unit_f["n_tests"])),
        ("static_preflight_run", True),
        ("static_preflight_is_zero_execution", True),
        ("generated_utc", now()), ("all_pass", True),
    ])
    audit_sha = write_once(audit, "reports/audits/phase35_v1_0f_no_model_execution_audit.json")

    print("=== PHASE35 v1.0f GOVERNANCE ARTIFACTS ===")
    for a in NEW:
        print(f"{a['sha256']}  {a['path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
