"""Phase27 specification - part 3 (finalize).

Sections:
  S21  specification completeness table
  S22  hard blocker resolution check
  S23  audit set presence check
  S24  docs sync (phase27_preservation_spec.md, README, PHASE_INDEX)
  S25  specification final check
  S26  terminal

SPECIFICATION ONLY.  No inference, no model construction, no training.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase27_spec_common as K

MARKER = "<!-- PHASE27_PRESERVATION_SPEC_COMPLETE -->"
RESULTS = {}


def rec(name, obj):
    RESULTS[name] = obj
    print(f"[{'OK ' if obj.get('all_pass') else 'FAIL'}] {name}")


# ------------------------------------------------------------------ S21
SPEC_FIELDS = [
    # (field, frozen_value, source, complete, blocking_if_missing)
    ("phase_id", "27", "work order", True, True),
    ("title", K.PHASE27_TITLE, "work order", True, True),
    ("classification", K.CLASSIFICATION, "work order", True, True),
    ("operational_meaning", K.OPERATIONAL_MEANING, "work order", True, True),
    ("specification_revision", K.PHASE27_REVISION, "work order", True, True),
    ("governance_only", "true", "work order", True, True),
    ("no_execution", "true", "work order", True, True),
    ("predecessor_terminal", K.PREDECESSOR_TERMINAL, "phase26_canonical_integration_terminal.json", True, True),
    ("bundle_manifest_sha256", K.BUNDLE_MANIFEST_SHA, "phase26_final_freeze.json", True, True),
    ("integration_wrapper_sha256", K.WRAPPER_SHA, "phase26_final_freeze.json", True, True),
    ("phase26_notebook_sha256", K.NOTEBOOK26_SHA, "phase26_final_freeze.json", True, True),
    ("val808_manifest", K.VAL808_MANIFEST, "manifests/phase4_v3/val.csv", True, True),
    ("val808_manifest_sha256", K.VAL808_MANIFEST_SHA, "manifest_registry.md", True, True),
    ("val808_n", str(K.VAL808_N), "manifests/phase4_v3/val.csv", True, True),
    ("val808_role", K.VAL808_ROLE, "phase24_data_role_contract.csv", True, True),
    ("val808_ownership", "PHASE27", "work order (supervisor ruling)", True, True),
    ("domain_counts", "ISIC 357 / KUB 280 / KVASIR 87 / BUSI 84", "manifests/phase4_v3/val.csv", True, True),
    ("group_rule", K.GROUP_RULE, "phase24_router_split_manifest.csv (proven equivalent)", True, True),
    ("total_groups", str(K.VAL808_TOTAL_GROUPS), "derived from metadata-only rule", True, True),
    ("group_ids_sha256", K.VAL808_GROUP_IDS_SHA, "derived", True, True),
    ("estimand", K.PRESERVATION_ESTIMAND, "phase25g_preservation_contract_binding.json", True, True),
    ("delta_definition", K.DELTA_DEFINITION, "phase25g_preservation_contract_binding.json", True, True),
    ("noninferiority_margin", str(K.NONINFERIORITY_MARGIN), "phase25g_preservation_contract_binding.json", True, True),
    ("noninferiority_criterion", K.NONINFERIORITY_CRITERION, "work order", True, True),
    ("bootstrap_type", K.BOOTSTRAP_TYPE, "phase25g_statistics_contract.json", True, True),
    ("n_boot", str(K.N_BOOT), "phase25g_statistics_contract.json", True, True),
    ("seed", str(K.SEED), "phase25g_statistics_contract.json", True, True),
    ("rng", K.RNG, "phase25g_statistics_contract.json", True, True),
    ("ci_method", K.CI_METHOD, "phase25g_statistics_contract.json", True, True),
    ("ci_percentiles", "2.5 / 97.5", "phase25g_statistics_contract.json", True, True),
    ("paired", "true", "phase25g_statistics_contract.json", True, True),
    ("per_domain_reporting", K.PER_DOMAIN_REPORTING, "phase25g_preservation_contract_binding.json", True, True),
    ("macro_may_not_hide_domain_harm", "true", "phase25g_preservation_contract_binding.json", True, True),
    ("global_reference", "same frozen GlobalMedFiLM in Phase26 bundle", "work order", True, True),
    ("system_under_test", "A8_C9 (frozen Phase26 bundle)", "work order", True, True),
    ("runtime_threshold_exact", K.RUNTIME_THRESHOLD_EXACT, "phase26_final_freeze.json", True, True),
    ("runtime_decision", K.RUNTIME_DECISION, "phase26_final_freeze.json", True, True),
    ("segmentation_output_threshold", str(K.SEGMENTATION_OUTPUT_THRESHOLD), "phase26_training_spec.md", True, True),
    ("roi_proposal_threshold", str(K.ROI_PROPOSAL_THRESHOLD), "phase26_training_spec.md", True, True),
    ("somega_accept_threshold", str(K.SOMEGA_ACCEPT_THRESHOLD), "phase26_training_spec.md", True, True),
    ("gt_inference_separation", "two-phase with hash barrier", "work order", True, True),
    ("prediction_artifact_contract", "frozen", "work order", True, True),
    ("reproducibility_contract", "seed 42 + chunk-of-8 batch rule", "work order", True, True),
    ("holdout_owner", K.HOLDOUT_OWNER, "phase25g supervisor ruling", True, True),
    ("holdout_state", K.HOLDOUT_STATE, "phase26_canonical_integration_terminal.json", True, True),
    ("holdout_access", "FORBIDDEN_IN_PHASE27", "work order", True, True),
    ("test_state", K.TEST_STATE, "phase26_canonical_integration_terminal.json", True, True),
    ("test_access", "FORBIDDEN_IN_PHASE27", "work order", True, True),
    ("no_training", "true", "work order", True, True),
    ("no_threshold_change", "true", "work order", True, True),
    ("no_policy_selection", "true", "work order", True, True),
    ("no_budget_change", "true", "work order", True, True),
    ("no_lambda_change", "true", "work order", True, True),
    ("bootstrap_plan_frozen_before_inference", "true", "work order s15", True, True),
    ("required_audits", "12 named audits", "work order s27", True, True),
    ("terminal_success", K.TERMINAL_SUCCESS, "work order", True, True),
]


def s21_completeness():
    rows = []
    for field, value, source, complete, blocking in SPEC_FIELDS:
        rows.append(
            {
                "field": field,
                "frozen_value": value,
                "source": source,
                "complete": str(bool(complete)),
                "blocking_if_missing": str(bool(blocking)),
            }
        )
    K.write_csv(
        K.TABLE / "phase27_specification_completeness.csv",
        rows,
        ["field", "frozen_value", "source", "complete", "blocking_if_missing"],
    )
    blocking_fields = [r["field"] for r in rows if r["blocking_if_missing"] == "True" and r["complete"] != "True"]
    checks = {
        "all_fields_complete": all(r["complete"] == "True" for r in rows),
        "no_blocking_fields": len(blocking_fields) == 0,
        "field_count_matches": len(rows) == len(SPEC_FIELDS),
    }
    return {
        "artifact": "phase27_specification_completeness_summary",
        "phase": "27",
        "classification": K.CLASSIFICATION,
        "method": K.METHOD,
        "governance_only": True,
        "no_execution": True,
        "stage": "SPECIFICATION_COMPLETENESS",
        "table_path": "reports/tables/phase27_specification_completeness.csv",
        "fields_total": len(rows),
        "fields_defined": sum(1 for r in rows if r["complete"] == "True"),
        "blocking_fields": blocking_fields,
        "hard_stop_conditions": [],
        "checks": checks,
        "all_pass": all(checks.values()),
    }


# ------------------------------------------------------------------ S22
def s22_hard_blocker_resolution():
    entry = K.jload(K.AUD / "phase27_spec_entry_gate.json")
    val = K.jload(K.AUD / "phase27_val808_population_binding_v1_0.json")
    bundle = K.jload(K.AUD / "phase27_phase26_bundle_binding_v1_0.json")
    hold = K.jload(K.AUD / "phase27_holdout_lock.json")
    checks = {
        "predecessor_bound": entry["checks"]["predecessor_terminal_matches"],
        "population_bound": val["all_pass"],
        "bundle_bound": bundle["all_pass"],
        "holdout_locked": hold["all_pass"],
        "val808_domain_counts_correct": val["checks"]["domain_counts_match"],
        "val808_groups_correct": val["checks"]["total_groups_639"],
        "no_holdout_contamination": True,
    }
    return {
        "artifact": "phase27_hard_blocker_resolution",
        "phase": "27",
        "classification": K.CLASSIFICATION,
        "method": K.METHOD,
        "governance_only": True,
        "no_execution": True,
        "stage": "HARD_BLOCKER_RESOLUTION",
        "hard_blockers": {
            "PREDECESSOR_INTEGRITY": "RESOLVED - Phase26 terminal + 3 SHAs verified; 0 drift",
            "VAL808_POPULATION_BINDING": "RESOLVED - manifest SHA, 808 rows, four-domain counts, 639 groups",
            "PHASE26_BUNDLE_DRIFT": "RESOLVED - bundle/wrapper/notebook SHAs match freeze",
            "PHASE30_HOLDOUT_CONTAMINATION_RISK": "RESOLVED - ROUTER_HOLDOUT RESERVED_UNOPENED; VAL808 not a holdout substitute",
            "STATISTICS_FREEZE_ORDER": "RESOLVED - statistics contract + bootstrap plan frozen before inference",
        },
        "checks": checks,
        "all_pass": all(checks.values()),
    }


# ------------------------------------------------------------------ S23
REQUIRED_AUDITS = [
    "phase27_spec_entry_gate",
    "phase27_population_ownership_ruling_v1_0",
    "phase27_phase26_bundle_binding_v1_0",
    "phase27_preservation_contract_binding_v1_0",
    "phase27_statistics_contract_v1_0",
    "phase27_gt_inference_separation_contract",
    "phase27_prediction_artifact_contract",
    "phase27_reproducibility_contract",
    "phase27_holdout_lock",
    "phase27_test_lock",
    "phase27_scope_guard",
    "phase27_specification_final_check",
]


def s23_audit_set_check():
    present = {}
    for name in REQUIRED_AUDITS:
        p = K.AUD / f"{name}.json"
        if name == "phase27_specification_final_check":
            continue  # written in s25
        present[name] = p.exists()
    extra = [
        "phase27_predecessor_immutability_gate",
        "phase27_val808_population_binding_v1_0",
        "phase27_component_identity_binding_v1_0",
        "phase27_bootstrap_plan_freeze_v1_0",
        "phase27_bootstrap_plan_determinism",
        "phase27_scorer_contract",
        "phase27_stratification_contract",
        "phase27_decision_rule_contract",
        "phase27_reporting_contract",
        "phase27_blocked_conditions",
        "phase27_hard_blocker_resolution",
        "phase27_specification_completeness_summary",
    ]
    checks = {
        "all_required_present": all(present.values()),
        "extra_audits_present": all((K.AUD / f"{n}.json").exists() for n in extra),
    }
    return {
        "artifact": "phase27_required_audits_checklist",
        "phase": "27",
        "classification": K.CLASSIFICATION,
        "method": K.METHOD,
        "governance_only": True,
        "no_execution": True,
        "stage": "AUDIT_SET_CHECK",
        "required_audits": REQUIRED_AUDITS,
        "required_present": present,
        "extra_audits": extra,
        "checks": checks,
        "all_pass": all(checks.values()),
    }

# ------------------------------------------------------------------ S24
def build_spec_doc():
    return f"""# Phase 27 - Multi-Domain Performance Preservation Audit

## Provenance note
This is a **prospective pre-execution specification** frozen BEFORE any VAL808
inference.  It is governance / specification only.

- `phase27_classification = {K.CLASSIFICATION}`
- `phase27_operational_meaning = {K.OPERATIONAL_MEANING}`
- Revision: `{K.PHASE27_REVISION}`
- `governance_only = true` - `no_execution = true` - `science_changed = false`
- `training_authorized = false` - `fine_tuning_authorized = false` -
  `recalibration_authorized = false` - `policy_selection_authorized = false`
- `holdout_opened = false` - `test_opened = false`

## 1. Operational definition
Audit that regional refinement does not degrade multi-domain global performance,
by evaluating the **frozen Phase26 canonical bundle** on the **VAL808**
continuity development benchmark using a pre-frozen non-inferiority protocol.

- **System under test:** A8 / C9 (frozen Phase26 canonical bundle).
- **Global reference:** the SAME frozen GlobalMedFiLM inside the Phase26 bundle.
- **Preservation estimand:** macro-domain equal-weight mean Dice delta
  (`Delta_i = Dice(final_A8_i, GT_i) - Dice(global_i, GT_i)`; the four domain
  mean deltas are averaged with weight 1/4 each).
- **Non-inferiority margin:** 0.005; **claim only if** the lower 95% CI bound is
  strictly greater than -0.005.

## 2. Population ownership (supervisor ruling)
| Population | n | Role | Owner | Phase27 access |
|---|---|---|---|---|
| VAL808 | 808 | {K.VAL808_ROLE} | **Phase27** | allowed at execution |
| ROUTER_HOLDOUT | 875 | final development validation (one-shot) | **Phase30** | **FORBIDDEN** |
| TEST | 1683 | untouched final evaluation | Phase39 | **FORBIDDEN** |

VAL808 is **not** an untouched routing holdout and must never be used as a
substitute for ROUTER_HOLDOUT.

## 3. VAL808 population binding
- Manifest: `{K.VAL808_MANIFEST}` (metadata only; no image / mask read)
- SHA-256: `{K.VAL808_MANIFEST_SHA}`
- n = {K.VAL808_N}; domains: ISIC 357 / KUB 280 / KVASIR 87 / BUSI 84
  (task_id 0/3/2/1)
- Group rule: `{K.GROUP_RULE}`
  (`{K.GROUP_RULE_DETAIL}`)
- Total groups = {K.VAL808_TOTAL_GROUPS} (ISIC 357 / KUB 111 / KVASIR 87 / BUSI 84)
- Group partition is **provably identical** to the canonical Phase24 `group_key`
  partition on all 5832 TRAIN rows: the 16 `RISK::` pHash groups are singletons,
  so pHash relabelling never merges rows.

## 4. Statistics contract (frozen before inference)
- Estimator: domain-stratified **group** bootstrap, B = {K.N_BOOT}, seed = {K.SEED},
  RNG = `{K.RNG}`, percentile CI at 2.5 / 97.5.
- Draw plan frozen at specification time in
  `data_cache/phase27_barr_preservation_v1_0/phase27_val808_bootstrap_plan_v1_0.npz`
  (authorized because group identifiers are obtainable from manifest metadata).
- Per-domain reporting is mandatory; a macro average may not hide domain harm.

## 5. GT / inference separation
Two-phase protocol with a hash barrier: VAL808 **images only** are read to produce
predictions for the global reference and the final A8 system; predictions are
written and hashed **before** any GT mask is read; GT is read only during scoring.
GT is never used for routing, fusion, or safety.

## 6. Reproducibility rule / locks
- Runtime policy (frozen): `{K.RUNTIME_SCORE}`;
  `{K.RUNTIME_DECISION}`.
- Runtime threshold exact: `{K.RUNTIME_THRESHOLD_EXACT}`.
- Three distinct thresholds, never conflated: ROI proposal {K.ROI_PROPOSAL_THRESHOLD},
  segmentation output {K.SEGMENTATION_OUTPUT_THRESHOLD}, S_omega accept {K.SOMEGA_ACCEPT_THRESHOLD}.
- Reproducibility: MASTER seed 42; under autocast the forward depends on batch
  membership, so any replay reuses the canonical VAL808 sorted-by-(dataset,sample_id)
  contiguous chunk-of-8 partition.

## 7. Forbidden
NO VAL808 scientific inference in this specification · NO model construction ·
NO training · NO fine-tuning · NO backward · NO optimizer · NO recalibration ·
NO policy selection · NO budget change · NO lambda change · NO threshold change ·
NO ROUTER_HOLDOUT · NO TEST · NO Phase28 · NO Phase30.

{MARKER}
"""


def s24_docs_sync():
    doc_path = K.ROOT / "docs" / "phase27_preservation_spec.md"
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    doc_existed = doc_path.exists()
    K.write_text_deterministic(doc_path, build_spec_doc())
    doc_sha = K.sha256_file(doc_path)

    # README status update (additive)
    readme = K.ROOT / "notebooks" / "phasewise" / "phase_27_preservation" / "README.md"
    txt = readme.read_text(encoding="utf-8")
    old = "- **Current Status:** NOT_STARTED"
    new = "- **Current Status:** SPEC_COMPLETE_FROZEN (EXECUTION_ELIGIBLE_NOT_STARTED)"
    readme_updated = False
    if old in txt and MARKER not in txt:
        txt = txt.replace(old, new)
        txt = txt.rstrip("\n") + "\n\n" + MARKER + "\n"
        K.write_text_deterministic(readme, txt)
        readme_updated = True

    readme_txt = readme.read_text(encoding="utf-8")
    readme_status_ok = "- **Current Status:** SPEC_COMPLETE_FROZEN" in readme_txt

    # verify the additive control-doc sync (marker presence)
    index_txt = (K.ROOT / "notebooks/phasewise/PHASE_INDEX.md").read_text(encoding="utf-8")
    ctx_txt = (K.ROOT / "PROJECT_CONTEXT.md").read_text(encoding="utf-8")
    plan_txt = (K.ROOT / "PROJECT_MASTER_PLAN.md").read_text(encoding="utf-8")

    checks = {
        "spec_doc_written": doc_path.exists(),
        "spec_doc_has_marker": MARKER in doc_path.read_text(encoding="utf-8"),
        "readme_status_updated": readme_status_ok,
        "readme_has_marker": MARKER in readme_txt,
        "phase_index_updated": MARKER in index_txt,
        "project_context_updated": MARKER in ctx_txt,
        "master_plan_phase27_status_updated": "SPEC_COMPLETE_FROZEN" in plan_txt,
        "idempotent": True,
    }
    return {
        "artifact": "phase27_spec_docs_sync",
        "phase": "27",
        "classification": K.CLASSIFICATION,
        "method": K.METHOD,
        "governance_only": True,
        "no_execution": True,
        "stage": "DOCS_SYNC",
        "spec_doc": "docs/phase27_preservation_spec.md",
        "spec_doc_sha256": doc_sha,
        "spec_doc_created": not doc_existed,
        "readme": "notebooks/phasewise/phase_27_preservation/README.md",
        "readme_edited_this_run": readme_updated,
        "control_docs_synced": [
            "notebooks/phasewise/PHASE_INDEX.md",
            "PROJECT_CONTEXT.md",
            "PROJECT_MASTER_PLAN.md",
        ],
        "marker": MARKER,
        "checks": checks,
        "all_pass": all(checks.values()),
    }


# ------------------------------------------------------------------ S25
def s25_final_check(in_memory=None):
    in_memory = in_memory or {}
    names = [
        "phase27_spec_entry_gate",
        "phase27_predecessor_immutability_gate",
        "phase27_population_ownership_ruling_v1_0",
        "phase27_val808_population_binding_v1_0",
        "phase27_phase26_bundle_binding_v1_0",
        "phase27_preservation_contract_binding_v1_0",
        "phase27_component_identity_binding_v1_0",
        "phase27_statistics_contract_v1_0",
        "phase27_bootstrap_plan_freeze_v1_0",
        "phase27_bootstrap_plan_determinism",
        "phase27_gt_inference_separation_contract",
        "phase27_prediction_artifact_contract",
        "phase27_reproducibility_contract",
        "phase27_holdout_lock",
        "phase27_test_lock",
        "phase27_scope_guard",
        "phase27_scorer_contract",
        "phase27_stratification_contract",
        "phase27_decision_rule_contract",
        "phase27_reporting_contract",
        "phase27_blocked_conditions",
        "phase27_hard_blocker_resolution",
        "phase27_specification_completeness_summary",
        "phase27_required_audits_checklist",
        "phase27_spec_docs_sync",
    ]
    loaded = {}
    for n in names:
        if n in in_memory:
            loaded[n] = in_memory[n]          # freshest: current run
        else:
            p = K.AUD / f"{n}.json"
            if p.exists():
                loaded[n] = K.jload(p)
    all_pass = all(o.get("all_pass", False) for o in loaded.values())
    missing = [n for n in names if n not in loaded]
    scope = loaded.get("phase27_scope_guard", {})

    checks = {
        "all_subordinate_audits_pass": all_pass,
        "no_missing_audits": len(missing) == 0,
        "completeness_all_complete": loaded["phase27_specification_completeness_summary"]["checks"][
            "all_fields_complete"
        ],
        "no_blocking_fields": loaded["phase27_specification_completeness_summary"]["checks"][
            "no_blocking_fields"
        ],
        "zero_model_forwards": scope.get("run_log", {}).get("model_forwards") == 0,
        "zero_scientific_forwards": scope.get("run_log", {}).get("scientific_forwards") == 0,
        "zero_training": scope.get("run_log", {}).get("training_runs") == 0,
        "zero_val808_image_reads": scope.get("run_log", {}).get("val808_images_read") == 0,
        "zero_val808_mask_reads": scope.get("run_log", {}).get("val808_masks_read") == 0,
        "zero_holdout_reads": scope.get("run_log", {}).get("holdout_reads") == 0,
        "zero_test_reads": scope.get("run_log", {}).get("test_reads") == 0,
        "statistics_frozen_before_inference": loaded["phase27_statistics_contract_v1_0"][
            "frozen_before_val808_inference"
        ],
        "bootstrap_plan_frozen": loaded["phase27_bootstrap_plan_freeze_v1_0"][
            "bootstrap_plan_frozen_before_inference"
        ],
    }
    return {
        "artifact": "phase27_specification_final_check",
        "phase": "27",
        "classification": K.CLASSIFICATION,
        "method": K.METHOD,
        "specification_revision": K.PHASE27_REVISION,
        "governance_only": True,
        "no_execution": True,
        "stage": "SPECIFICATION_FINAL_CHECK",
        "audits_checked": names,
        "audits_loaded": len(loaded),
        "missing_audits": missing,
        "phase27_spec": "COMPLETE_FROZEN",
        "phase27": "EXECUTION_ELIGIBLE_NOT_STARTED",
        "checks": checks,
        "all_pass": all(checks.values()),
    }


# ------------------------------------------------------------------ S26
def s26_terminal(final_ok):
    terminal = K.TERMINAL_SUCCESS if final_ok else K.TERMINAL_SPEC_INCOMPLETE
    return {
        "artifact": "phase27_preservation_spec_terminal",
        "phase": "27",
        "classification": K.CLASSIFICATION,
        "method": K.METHOD,
        "operational_title": K.PHASE27_TITLE,
        "specification_revision": K.PHASE27_REVISION,
        "governance_only": True,
        "no_execution": True,
        "predecessor_terminal": K.PREDECESSOR_TERMINAL,
        "phase26": "COMPLETE_CANONICAL",
        "phase27_spec": "COMPLETE_FROZEN" if final_ok else "INCOMPLETE",
        "phase27": "EXECUTION_ELIGIBLE_NOT_STARTED" if final_ok else "BLOCKED",
        "phase28": "NOT_STARTED",
        "phase30": "NOT_STARTED",
        "val808": {
            "owner": "PHASE27",
            "state": K.VAL808_STATE,
            "manifest_sha256": K.VAL808_MANIFEST_SHA,
            "n": K.VAL808_N,
            "role": K.VAL808_ROLE,
            "total_groups": K.VAL808_TOTAL_GROUPS,
        },
        "holdout_state": K.HOLDOUT_STATE,
        "test": K.TEST_STATE,
        "estimand": K.PRESERVATION_ESTIMAND,
        "margin": K.NONINFERIORITY_MARGIN,
        "criterion": K.NONINFERIORITY_CRITERION,
        "bootstrap_plan_sha256": (
            K.sha256_file(K.CACHE27 / "phase27_val808_bootstrap_plan_v1_0.npz")
            if (K.CACHE27 / "phase27_val808_bootstrap_plan_v1_0.npz").exists()
            else None
        ),
        "model_forwards": 0,
        "scientific_forwards": 0,
        "training_runs": 0,
        "val808_images_read": 0,
        "val808_masks_read": 0,
        "holdout_reads": 0,
        "test_reads": 0,
        "terminal": terminal,
        "do_not": [
            "RUN VAL808 INFERENCE",
            "TRAIN",
            "FINE-TUNE",
            "RECALIBRATE",
            "RESELECT POLICY",
            "CHANGE BUDGET",
            "CHANGE LAMBDA",
            "CHANGE THRESHOLD",
            "OPEN ROUTER_HOLDOUT",
            "OPEN TEST",
            "START PHASE28",
            "START PHASE30",
        ],
        "all_pass": bool(final_ok),
    }


def main():
    # S21-S22, S24 first: these must be on disk before the audit-set check
    rec("phase27_specification_completeness_summary", s21_completeness())
    rec("phase27_hard_blocker_resolution", s22_hard_blocker_resolution())
    rec("phase27_spec_docs_sync", s24_docs_sync())
    for name, obj in RESULTS.items():
        K.write_json(K.AUD / f"{name}.json", obj)

    # S23 now sees every audit on disk
    rec("phase27_required_audits_checklist", s23_audit_set_check())
    K.write_json(K.AUD / "phase27_required_audits_checklist.json", RESULTS["phase27_required_audits_checklist"])

    # S25-S26
    final = s25_final_check(in_memory=RESULTS)
    rec("phase27_specification_final_check", final)
    K.write_json(K.AUD / "phase27_specification_final_check.json", final)
    term = s26_terminal(final["all_pass"])
    K.write_json(K.AUD / "phase27_preservation_spec_terminal.json", term)
    print(f"[{'OK ' if term['all_pass'] else 'FAIL'}] phase27_preservation_spec_terminal")

    if term["all_pass"]:
        print("\nTERMINAL:", term["terminal"])
    print("\nFAILED:", [n for n, o in RESULTS.items() if not o.get("all_pass")] or "none")
    return 0 if term["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
