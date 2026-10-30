"""Phase 29 -- Three-Seed Deterministic Reproducibility Study: PRE-EXECUTION SPECIFICATION AUDIT.

GOVERNANCE / SPECIFICATION ONLY.
NO training. NO model forward. NO new predictions. NO new targets. NO metrics.
NO ROUTER_HOLDOUT. NO TEST. NO Phase30.

Implements the 40-section work order:
    §0   entry gate
    §1   canonical title / role
    §2   authoritative multi-seed policy recovery
    §3   master seed vs component sub-seeds
    §4   training scope (HARD BLOCKER)
    §5   seed-42 reuse vs retrain
    §6   split / fold stability (HARD BLOCKER)
    §7   holdout protection
    §8   evaluation population (HARD BLOCKER)
    §9   VAL808 status
    §10-§13 component protocols (G / R_psi / B_phi / S_omega)
    §14  dependency consistency
    §15  feature cache question
    §16  paired-gain target question
    §17  post-safety target question
    §18  canonical policy / budget
    §19  final-router threshold across seeds (HARD BLOCKER)
    §20  S_omega threshold
    §21-§25 estimands / question / criteria / preservation / statistics
    §26  deterministic training requirements
    §27  seed-specific artifact roots
    §28  training-run count
    §29-§31 reuse / dependency / evaluation tables
    §32-§34 boundaries
    §35  specification completeness matrix
    §36  hard blockers
    §37  required audits
    §38  no-execution
    §39  success terminal
    §40  blocked terminals

Usage:
    ./.venv/Scripts/python.exe scripts/analysis/phase29_spec_audit.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"


def sha(p: Path):
    p = Path(p)
    if not p.exists():
        return None
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def rel(p: Path) -> str:
    return str(Path(p).relative_to(ROOT)).replace("\\", "/")


def read_json(p: Path):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def write_json(p: Path, obj):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False)
        f.write("\n")


def write_csv(p: Path, header, rows):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        for r in rows:
            w.writerow(r)


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ==========================================================================
# Frozen constants of this specification audit
# ==========================================================================
ENTRY_TERMINAL = ("PHASE28_CANONICAL_CLOSURE_REPAIRED__EXECUTED_FULL_18_RUN_HISTORY_NOTEBOOK"
                  "_FROZEN__SCIENTIFIC_ARTIFACTS_UNCHANGED__PHASE29_ELIGIBLE_NOT_STARTED")
PHASE28_NB_SHA = "ba40b5f22febb2250f14fb6b863ce974a46667b07f3cb3fff46293c67eb486e1"
CANONICAL_BUNDLE_SHA = "f7aebb0f646bcc8de49fa91b70a4c4cc1051c9998ab6b055a8d4d187809cb3d9"
BASE_PHASE28_FREEZE_SHA = "ac4b9f72ce663e57d4f7049a979e3bad8cd3ec460cca494c332e9ebc32bb098a"

SEEDS = [42, 123, 3407]

SUCCESS_TERMINAL = ("PHASE29_REPRODUCIBILITY_SPEC_COMPLETE__THREE_SEEDS_TRAINING_SCOPE_DEPENDENCY_"
                    "CHAIN_AND_EVALUATION_PROTOCOL_FROZEN__PHASE29_EXECUTION_ELIGIBLE_NOT_STARTED")

BLOCKED_TERMINALS = {
    "PREDECESSOR_ARTIFACT_DRIFT": "PHASE29_BLOCKED__PREDECESSOR_ARTIFACT_DRIFT",
    "THREE_SEED_SET_NOT_AUTHORITATIVELY_FROZEN": "PHASE29_BLOCKED__THREE_SEED_SET_NOT_AUTHORITATIVELY_FROZEN",
    "REPRODUCIBILITY_TRAINING_SCOPE_UNRESOLVED": "PHASE29_BLOCKED__REPRODUCIBILITY_TRAINING_SCOPE_UNRESOLVED",
    "MULTISEED_SPLIT_OR_FOLD_RULE_UNRESOLVED": "PHASE29_BLOCKED__MULTISEED_SPLIT_OR_FOLD_RULE_UNRESOLVED",
    "SEED_SPECIFIC_DEPENDENCY_CHAIN_UNRESOLVED": "PHASE29_BLOCKED__SEED_SPECIFIC_DEPENDENCY_CHAIN_UNRESOLVED",
    "MULTISEED_ROUTER_CALIBRATION_RULE_UNRESOLVED": "PHASE29_BLOCKED__MULTISEED_ROUTER_CALIBRATION_RULE_UNRESOLVED",
    "REPRODUCIBILITY_EVALUATION_POPULATION_UNRESOLVED": "PHASE29_BLOCKED__REPRODUCIBILITY_EVALUATION_POPULATION_UNRESOLVED",
    "SEED_SPECIFIC_ROUTER_TARGET_DEPENDENCY_UNRESOLVED": "PHASE29_BLOCKED__SEED_SPECIFIC_ROUTER_TARGET_DEPENDENCY_UNRESOLVED",
    "REPRODUCIBILITY_SPEC_INCOMPLETE": "PHASE29_BLOCKED__REPRODUCIBILITY_SPEC_INCOMPLETE",
}


# ==========================================================================
# §0  Entry gate
# ==========================================================================
def section_0():
    term = read_json(AUD / "phase28_terminal_state_notebook_compliance_repair.json")
    add = read_json(AUD / "phase28_final_freeze_notebook_compliance_addendum.json")
    base_ff = read_json(AUD / "phase28_final_freeze.json")
    idx = read_json(AUD / "phase28_phase_index_additive_update.json")
    nb = ROOT / "notebooks/phasewise/phase_28_model_ablation/phase28_comprehensive_ablation.ipynb"

    checks = {
        "terminal_exact": term.get("terminal") == ENTRY_TERMINAL,
        "phase28_complete_canonical": idx.get("phase28_state") == "COMPLETE_CANONICAL",
        "phase29_eligible_not_started": idx.get("phase29_state") == "ELIGIBLE_NOT_STARTED",
        "phase30_not_started": idx.get("phase30_state") == "NOT_STARTED",
        "notebook_sha_exact": sha(nb) == PHASE28_NB_SHA,
        "router_holdout_reserved": idx.get("router_holdout_state") == "RESERVED_UNOPENED_FOR_PHASE30",
        "test_locked": idx.get("test_state") == "LOCKED_UNTIL_PHASE39",
        "base_final_freeze_unchanged": sha(AUD / "phase28_final_freeze.json") == BASE_PHASE28_FREEZE_SHA,
        "canonical_bundle_unchanged": base_ff.get("canonical_bundle_sha256") == CANONICAL_BUNDLE_SHA,
        "router_holdout_reads_zero": term.get("ROUTER_HOLDOUT_reads") == 0,
        "val808_reads_zero": term.get("VAL808_reads") == 0,
        "test_reads_zero": term.get("TEST_reads") == 0,
        "scientific_artifacts_unchanged": add.get("scientific_artifacts_unchanged") is True,
    }
    failed = [k for k, v in checks.items() if v is not True]
    obj = {
        "artifact": "phase29_spec_entry_gate",
        "phase": 29,
        "classification": "PHASE29_THREE_SEED_REPRODUCIBILITY_PRE_EXECUTION_SPECIFICATION_AUDIT",
        "method": "RA-MedFiLM-BARR",
        "governance_only": True,
        "execution": "NONE",
        "required_terminal": ENTRY_TERMINAL,
        "observed_terminal": term.get("terminal"),
        "phase28": "COMPLETE_CANONICAL",
        "phase29": "ELIGIBLE_NOT_STARTED",
        "phase30": "NOT_STARTED",
        "phase28_notebook_sha256": sha(nb),
        "phase28_notebook_sha256_expected": PHASE28_NB_SHA,
        "router_holdout_state": "RESERVED_UNOPENED_FOR_PHASE30",
        "test_state": "LOCKED_UNTIL_PHASE39",
        "checks": checks,
        "n_checks": len(checks),
        "n_failed": len(failed),
        "failed_checks": failed,
        "gate_pass": len(failed) == 0,
        "predecessor_drift": False,
        "blocked_terminal_if_drift": BLOCKED_TERMINALS["PREDECESSOR_ARTIFACT_DRIFT"],
        "all_pass": len(failed) == 0,
    }
    write_json(AUD / "phase29_spec_entry_gate.json", obj)
    print(f"[§0] entry gate | {'PASS' if obj['gate_pass'] else 'FAIL ' + str(failed)}")
    return obj


# ==========================================================================
# §1  Canonical title / role
# ==========================================================================
def section_1():
    obj = {
        "artifact": "phase29_canonical_title_and_role",
        "phase": 29,
        "classification": "PHASE29_CANONICAL_TITLE_AND_ROLE_BINDING",
        "canonical_title": "Three-Seed Deterministic Reproducibility Study",
        "canonical_notebook_dir": "notebooks/phasewise/phase_29_3seed_reproducibility",
        "canonical_notebook_readme": "notebooks/phasewise/phase_29_3seed_reproducibility/README.md",
        "canonical_notebook_readme_sha256": sha(ROOT / "notebooks/phasewise/phase_29_3seed_reproducibility/README.md"),
        "canonical_phase_id": "phase_29_3seed_reproducibility",
        "stage": "Stage C: Evidence & Rigor",
        "scientific_role": ("measure sensitivity/stability of the frozen RA-MedFiLM-BARR development "
                            "result to prospectively frozen training seeds"),
        "is_not": [
            "model selection", "architecture search", "threshold search", "policy search",
            "ablation expansion", "holdout evaluation", "formal significance testing",
        ],
        "formal_hypothesis_testing_owner": "PHASE31",
        "population": "ROUTER_DEVELOPMENT (DEV)",
        "title_sources": [
            {"path": "configs/research_protocol.json", "sha256": sha(ROOT / "configs/research_protocol.json")},
            {"path": "docs/TASKS.md", "sha256": sha(ROOT / "docs/TASKS.md"),
             "line_ref": "| 29 | Three-Seed Deterministic Reproducibility Study | NOT_STARTED |"},
            {"path": "PROJECT_MASTER_PLAN.md", "sha256": sha(ROOT / "PROJECT_MASTER_PLAN.md"),
             "line_ref": "- **Phase 29:** Three-Seed Deterministic Reproducibility Study (NOT_STARTED)"},
            {"path": "reports/audits/phase26_downstream_phase_boundary_audit.json",
             "sha256": sha(AUD / "phase26_downstream_phase_boundary_audit.json")},
            {"path": "notebooks/phasewise/phase_29_3seed_reproducibility/README.md",
             "sha256": sha(ROOT / "notebooks/phasewise/phase_29_3seed_reproducibility/README.md")},
        ],
        "title_sources_agree": True,
        "all_pass": True,
    }
    write_json(AUD / "phase29_canonical_title_and_role.json", obj)
    print("[§1] title/role bound:", obj["canonical_title"])
    return obj


# ==========================================================================
# §2  Authoritative multi-seed policy
# ==========================================================================
def section_2():
    rp = read_json(ROOT / "configs/research_protocol.json")
    rp_seeds = rp.get("policies", {}).get("multi_seed")
    rp_seed_policy = rp.get("policies", {}).get("seed_policy")
    md_seeds_raw = (ROOT / "reports/audits/research_protocol.md").read_text(encoding="utf-8")
    nb00 = ROOT / ("notebooks/phasewise/phase_00_governance/"
                   "phase00_governance_reproducibility_and_protocol.ipynb")

    sources = [
        {"path": "configs/research_protocol.json", "sha256": sha(ROOT / "configs/research_protocol.json"),
         "binds_seeds": rp_seeds, "role": "AUTHORITATIVE_MACHINE_READABLE", "binding_level": "PRIMARY"},
        {"path": "reports/audits/research_protocol.md", "sha256": sha(ROOT / "reports/audits/research_protocol.md"),
         "binds_seeds": "Seeds: 42, 123, 3407", "role": "AUTHORITATIVE_HUMAN_READABLE", "binding_level": "PRIMARY"},
        {"path": "notebooks/phasewise/phase_00_governance/phase00_governance_reproducibility_and_protocol.ipynb",
         "sha256": sha(nb00),
         "binds_seeds": "Random Seeds | NO | Supervisor Authorization Required | Deterministic multi-seed evaluation",
         "role": "GOVERNANCE_POLICY", "binding_level": "SUPPORTING"},
        {"path": "reports/audits/phase20_shared_global_baseline_protocol.json",
         "sha256": sha(AUD / "phase20_shared_global_baseline_protocol.json"),
         "binds_seeds": {"seed": 42, "second_seed_belongs_to_phase_29": True},
         "role": "PHASE_OWNERSHIP_OF_SECOND_SEED", "binding_level": "SUPPORTING"},
        {"path": "reports/audits/phase21_global_medfilm_architecture_binding.json",
         "sha256": sha(AUD / "phase21_global_medfilm_architecture_binding.json"),
         "binds_seeds": {"seed": 42, "second_seed_belongs_to_later_phase": True,
                         "logical_runs_authorized": 1},
         "role": "PHASE_OWNERSHIP_OF_SECOND_SEED", "binding_level": "SUPPORTING"},
        {"path": "docs/DESIGN.md", "sha256": sha(ROOT / "docs/DESIGN.md"),
         "binds_seeds": "Still NOT performed: Phase 29 three-seed reproducibility",
         "role": "PROJECT_STATE", "binding_level": "SUPPORTING"},
    ]
    seeds_frozen = rp_seeds == SEEDS
    obj = {
        "artifact": "phase29_seed_policy_source_binding",
        "phase": 29,
        "classification": "PHASE29_SEED_POLICY_SOURCE_BINDING",
        "seeds": SEEDS,
        "seeds_frozen": seeds_frozen,
        "seed_set_authoritatively_frozen": seeds_frozen,
        "primary_binding_source": "configs/research_protocol.json",
        "primary_binding_key": "policies.multi_seed",
        "primary_binding_value": rp_seeds,
        "seed_policy_legacy_note": rp_seed_policy,
        "sources_searched": [
            "configs/research_protocol.json", "reports/audits/research_protocol.md",
            "notebooks/phasewise/phase_00_governance/phase00_governance_reproducibility_and_protocol.ipynb",
            "PROJECT_MASTER_PLAN.md", "docs/RULES.md", "docs/DESIGN.md", "docs/PRD.md",
            "docs/TASKS.md", "docs/MEMORY.md", "docs/ARCHITECTURE.md",
            "docs/phase26_training_spec.md", "docs/phase27_preservation_spec.md",
            "docs/phase28_ablation_execution_spec_v1_2.md",
            "reports/audits/phase21_final_freeze.json", "reports/audits/phase21_protocol_binding.json",
            "reports/audits/phase25a_crossfit_protocol.json",
            "reports/audits/phase25d_frozen_training_spec_binding_v1_2_1.json",
            "reports/audits/phase25f_cv_manifest_reuse_contract_v1_0.json",
            "reports/audits/phase26_final_freeze.json", "reports/audits/phase28_final_freeze.json",
            "notebooks/phasewise/phase_29_3seed_reproducibility/README.md",
        ],
        "sources_binding_seed_set": sources,
        "chat_text_used_as_authority": False,
        "missing_canonical_spec_doc": {
            "declared_by_readme": "docs/phase29_repro_spec.md",
            "exists": (ROOT / "docs/phase29_repro_spec.md").exists(),
            "note": ("The Phase29 README declares docs/phase29_repro_spec.md as its canonical "
                     "provenance source; that document does NOT physically exist. The seed set is "
                     "nonetheless authoritatively frozen by configs/research_protocol.json."),
        },
        "blocked_terminal_if_unresolved": BLOCKED_TERMINALS["THREE_SEED_SET_NOT_AUTHORITATIVELY_FROZEN"],
        "all_pass": seeds_frozen,
    }
    write_json(AUD / "phase29_seed_policy_source_binding.json", obj)
    print(f"[§2] seed set {SEEDS} frozen = {seeds_frozen}")
    return obj


# ==========================================================================
# §3  Master seed vs component sub-seeds
# ==========================================================================
def section_3():
    obj = {
        "artifact": "phase29_master_seed_vs_component_subseed_audit",
        "phase": 29,
        "classification": "PHASE29_MASTER_SEED_VS_COMPONENT_SUBSEED_AUDIT",
        "rule": "master seed != every internal seed; each component has an exact frozen derivation",
        "master_seed_role": ("Phase29 master seed selects the TRAINING RANDOMNESS (weight init, "
                             "shuffle order, augmentation RNG) for a replicate. It does NOT "
                             "automatically equal every internal derived seed."),
        "must_not_assume": "master seed == every internal seed",
        "existing_component_seed_derivation": {
            "GlobalMedFiLM_G": {
                "source": "reports/audits/phase20_shared_global_baseline_protocol.json",
                "source_sha256": sha(AUD / "phase20_shared_global_baseline_protocol.json"),
                "training_seed": "MASTER_OR_SEED_DERIVED (Phase21 used literal 42)",
                "canonical_seed42_value": 42,
                "cv_folds": "NONE (single run, TRAIN=5832 / VAL=808 fixed membership)",
                "dataloader": "torch.Generator(make_generator(seed)), seed_worker",
                "note": "G trains on the fixed TRAIN membership; no fold structure.",
            },
            "BARRRegionalRefinerV1_R_psi": {
                "source": "reports/audits/phase25a_crossfit_protocol.json",
                "source_sha256": sha(AUD / "phase25a_crossfit_protocol.json"),
                "crossfit_seed": 42,
                "outer_folds": 3,
                "fold_assignment": ("deterministic group-safe domain-stratified; per domain, whole "
                                    "groups ordered by sha256('42::<group_key>')"),
                "inner_fit_fraction": 0.9,
                "inner_early_stop_fraction": 0.1,
                "inner_split_seeds": "derived from the cross-fit seed 42 (group-safe, domain-stratified)",
                "outer_target_role": "UNTOUCHED; OOF prediction only",
            },
            "BARRBenefitRouterV1_B_phi": {
                "source": "reports/audits/phase25d_data_loader_randomness_contract_v1_2_1.json",
                "source_sha256": sha(AUD / "phase25d_data_loader_randomness_contract_v1_2_1.json"),
                "base_seed": 42,
                "outer_cv": "StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)",
                "outer_fold_seed_derivation": "42000 + outer_cv_fold",
                "inner_split_seeds": "4200 + outer_fold_index",
                "fold_seed_uses": ["model initialization", "task embedding initialization",
                                   "training-shuffle generator"],
                "per_fold_fresh": ["model", "optimizer", "scheduler", "loader RNG"],
                "final_refit_seed": 42,
                "persistence_required": ["Python RNG", "NumPy RNG", "Torch CPU RNG",
                                         "Torch CUDA RNG", "DataLoader generator"],
            },
            "BARRPostSafetyV1_S_omega": {
                "source": "reports/audits/phase25f_cv_manifest_reuse_contract_v1_0.json",
                "source_sha256": sha(AUD / "phase25f_cv_manifest_reuse_contract_v1_0.json"),
                "cv_runs": 5,
                "cv_seeds": "54000-54004",
                "final_refit_seed": 42,
                "fold_reuse": "reuses Phase25D FIT/EARLY_STOP/OUTER_TARGET manifests",
            },
        },
        "seed_derivation_requires_prospective_freeze": True,
        "prospective_derivation_frozen_before_execution_required": True,
        "prospective_derivation_defined": False,
        "prospective_derivation_note": (
            "The Phase29 master-seed -> component sub-seed mapping is NOT yet prospectively defined "
            "for seeds 123 and 3407. Under the work order §3 this must be frozen BEFORE execution. "
            "It is an execution-critical field (see §35 completeness matrix) but the DERIVATION RULE "
            "ITSELF is derivable deterministically from the frozen components above."),
        "all_pass": True,
    }
    write_json(AUD / "phase29_master_seed_vs_component_subseed_audit.json", obj)
    print("[§3] master/sub-seed audit written")
    return obj


# ==========================================================================
# §4  Training scope (HARD BLOCKER)
# ==========================================================================
COMPONENTS = [
    {
        "component": "G", "name": "GlobalMedFiLM",
        "canonical_seed42_checkpoint": "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt",
        "canonical_seed42_sha256": "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7",
        "spec": "Phase21 (inherits Phase20 global protocol)",
        "reused_by_phase28": False,
    },
    {
        "component": "R_psi", "name": "BARRRegionalRefinerV1",
        "canonical_seed42_checkpoint": "checkpoints/phase25a_barr_regional_refiner_v1_1_roi030/final/final.pt",
        "canonical_seed42_sha256": "6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109",
        "spec": "Phase25A ROI-0.30 cross-fit 3-fold + final refit",
        "reused_by_phase28": True,
    },
    {
        "component": "B_phi", "name": "BARRBenefitRouterV1",
        "canonical_seed42_checkpoint": "checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt",
        "canonical_seed42_sha256": "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b",
        "spec": "Phase25D v1.2.1 5-fold OOF + final refit",
        "reused_by_phase28": True,
    },
    {
        "component": "S_omega", "name": "BARRPostSafetyV1",
        "canonical_seed42_checkpoint": "checkpoints/phase25f_barr_post_safety_v1_0_seed42/final/final.pt",
        "canonical_seed42_sha256": "eee9b97b9921e53fc07eac9281dce64ba518c6e1659916b97b0b3bec21ec6d2e",
        "spec": "Phase25F post-safety 5-fold OOF + final refit",
        "reused_by_phase28": False,
    },
]


def section_4():
    # physical presence + SHA of the four canonical checkpoints
    phys = {}
    for c in COMPONENTS:
        p = ROOT / c["canonical_seed42_checkpoint"]
        phys[c["component"]] = {
            "path": c["canonical_seed42_checkpoint"],
            "exists": p.exists(),
            "sha256_on_disk": sha(p),
            "sha256_expected": c["canonical_seed42_sha256"],
            "sha_match": sha(p) == c["canonical_seed42_sha256"],
        }
    all_match = all(v["sha_match"] for v in phys.values())
    obj = {
        "artifact": "phase29_training_scope_audit",
        "phase": 29,
        "classification": "PHASE29_TRAINING_SCOPE_AUDIT",
        "hard_blocker": True,
        "question": "exactly which canonical learned components must Phase29 retrain per seed?",
        "candidate_components": ["G", "R_psi", "B_phi", "S_omega"],
        "phase26_wrapper_fusion_learned_params": 0,
        "canonical_checkpoint_physical_binding": phys,
        "canonical_checkpoints_all_present_and_match": all_match,
        "canonical_component_checkpoints": {
            c["component"]: {
                "checkpoint": c["canonical_seed42_checkpoint"],
                "sha256": c["canonical_seed42_sha256"],
                "spec": c["spec"],
            } for c in COMPONENTS
        },
        "scope_search_sources": [
            {"path": "notebooks/phasewise/phase_29_3seed_reproducibility/README.md",
             "sha256": sha(ROOT / "notebooks/phasewise/phase_29_3seed_reproducibility/README.md"),
             "defines_component_scope": False,
             "declares_spec_doc_that_does_not_exist": "docs/phase29_repro_spec.md"},
            {"path": "configs/research_protocol.json",
             "sha256": sha(ROOT / "configs/research_protocol.json"),
             "defines_component_scope": False, "binds_seeds_only": True},
            {"path": "PROJECT_MASTER_PLAN.md", "sha256": sha(ROOT / "PROJECT_MASTER_PLAN.md"),
             "defines_component_scope": False, "title_and_status_only": True},
            {"path": "docs/TASKS.md", "sha256": sha(ROOT / "docs/TASKS.md"),
             "defines_component_scope": False, "title_and_status_only": True},
            {"path": "docs/DESIGN.md", "sha256": sha(ROOT / "docs/DESIGN.md"),
             "defines_component_scope": False,
             "notes_scope": "records that Phase29 three-seed reproducibility is still NOT performed"},
            {"path": "reports/audits/phase26_downstream_phase_boundary_audit.json",
             "sha256": sha(AUD / "phase26_downstream_phase_boundary_audit.json"),
             "defines_component_scope": False,
             "binds": "title + population ROUTER_DEVELOPMENT + NOT_STARTED"},
            {"path": "reports/audits/phase28_phase29_boundary_audit.json",
             "sha256": sha(AUD / "phase28_phase29_boundary_audit.json"),
             "defines_component_scope": False, "binds": "population DEV"},
        ],
        "scope_physically_defined": False,
        "scope_definition_absent_reason": (
            "No authoritative artifact states which of G / R_psi / B_phi / S_omega Phase29 must "
            "retrain. The Phase29 README points to docs/phase29_repro_spec.md, which does not exist. "
            "The word 'three-seed system' does not automatically imply all four components are retrained."),
        "must_not_assume": "three-seed system == all four components retrained",
        "per_component_status": {
            "G": "UNRESOLVED",
            "R_psi": "UNRESOLVED",
            "B_phi": "UNRESOLVED",
            "S_omega": "UNRESOLVED",
        },
        "allowed_classifications": ["IN_SCOPE_RETRAIN", "REUSE_CANONICAL_FIXED", "NOT_APPLICABLE"],
        "scope_resolved": False,
        "blocked_terminal_if_unresolved": BLOCKED_TERMINALS["REPRODUCIBILITY_TRAINING_SCOPE_UNRESOLVED"],
        "all_pass": False,
    }
    write_json(AUD / "phase29_training_scope_audit.json", obj)
    print(f"[§4] training scope RESOLVED={obj['scope_resolved']} (HARD BLOCKER)")
    return obj


# ==========================================================================
# §5  Seed-42 reuse vs retrain
# ==========================================================================
def section_5():
    rows = []
    checks = {
        "architecture": True, "training_population": True, "split_manifests": True,
        "optimizer_loss_scheduler": True, "augmentation": True,
        "training_selection_rule": True, "numeric_precision": True,
        "phase29_evaluation_rule": None,  # evaluation rule is NOT yet frozen (see §8)
    }
    obj = {
        "artifact": "phase29_seed42_reuse_audit",
        "phase": 29,
        "classification": "PHASE29_SEED42_REUSE_AUDIT",
        "question": "do existing canonical seed-42 artifacts qualify as the seed-42 Phase29 replicate?",
        "reuse_requires_all_exact": [
            "architecture", "training_population", "split_manifests", "optimizer/loss/scheduler",
            "augmentation", "training-selection_rule", "numeric_precision", "Phase29_evaluation_rule",
        ],
        "per_component_protocol_match": {
            "G": {
                "architecture": "MATCH (phase21_global_medfilm_architecture_binding.json)",
                "training_population": "MATCH (TRAIN 5832 fixed)",
                "split_manifests": "MATCH (no folds)",
                "optimizer_loss_scheduler": "MATCH (AdamW/CosineAnnealingLR/bce_dice)",
                "augmentation": "MATCH (SegmentationTransform train=True)",
                "training_selection_rule": "MATCH (early stopping patience 15)",
                "numeric_precision": "MATCH (AMP on CUDA; determinism policy not yet frozen per-seed)",
                "Phase29_evaluation_rule": "UNRESOLVED",
            },
            "R_psi": {
                "architecture": "MATCH (BARRRegionalRefinerV1, 1,276,401 params)",
                "training_population": "MATCH (DEV 4957)",
                "split_manifests": "MATCH (phase25a crossfit 3-fold)",
                "optimizer_loss_scheduler": "MATCH (AdamW/CosineAnnealingLR/0.5 BCE + 0.5 Dice)",
                "augmentation": "MATCH (phase25a_augmentation_binding.json)",
                "training_selection_rule": "MATCH (min EARLY_STOP total loss, patience 15)",
                "numeric_precision": "UNRESOLVED",
                "Phase29_evaluation_rule": "UNRESOLVED",
            },
            "B_phi": {
                "architecture": "MATCH (phase25d, 36,801 params)",
                "training_population": "MATCH (DEV 4957)",
                "split_manifests": "MATCH (phase25d cv5)",
                "optimizer_loss_scheduler": "MATCH (AdamW/ReduceLROnPlateau/Huber delta 0.05)",
                "augmentation": "N/A (tabular features)",
                "training_selection_rule": "MATCH (EARLY_STOP mean Huber, MINIMIZE)",
                "numeric_precision": "UNRESOLVED",
                "Phase29_evaluation_rule": "UNRESOLVED",
            },
            "S_omega": {
                "architecture": "MATCH (phase25f, 1,217 params)",
                "training_population": "MATCH (DEV 4957)",
                "split_manifests": "MATCH (reuses phase25d manifests)",
                "optimizer_loss_scheduler": "MATCH (BCEWithLogitsLoss; phase25f protocol)",
                "augmentation": "N/A (tabular features)",
                "training_selection_rule": "MATCH (phase25f checkpoint rule)",
                "numeric_precision": "UNRESOLVED",
                "Phase29_evaluation_rule": "UNRESOLVED",
            },
        },
        "seed42_role": "UNRESOLVED",
        "seed42_role_allowed_values": ["REUSE_EXISTING_CANONICAL_REPLICATE", "NEW_PHASE29_RETRAIN_REQUIRED"],
        "seed42_role_depends_on": [
            "training_scope (§4) being resolved first",
            "Phase29 evaluation rule (§8) being resolved first",
        ],
        "does_not_silently_mix_incomparable_seed_protocols": True,
        "all_per_component_protocol_match_exact": False,
        "all_pass": False,
    }
    write_json(AUD / "phase29_seed42_reuse_audit.json", obj)
    print(f"[§5] seed42 role = {obj['seed42_role']}")
    return obj


# ==========================================================================
# §6  Split / fold stability (HARD BLOCKER)
# ==========================================================================
def section_6():
    obj = {
        "artifact": "phase29_split_fold_stability_audit",
        "phase": 29,
        "classification": "PHASE29_SPLIT_FOLD_STABILITY_AUDIT",
        "hard_blocker": True,
        "question": "does Phase29 change ONLY optimization randomness, keeping data membership fixed?",
        "preferred_scientific_interpretation": "FIX_DATA_PARTITIONS__CHANGE_TRAINING_RANDOMNESS_ONLY",
        "preferred_interpretation_adopted": False,
        "adoption_requires_authority": True,
        "partitions_requiring_explicit_classification": {
            "TRAIN_VAL_split": {"status": "UNRESOLVED", "authority_found": False},
            "ROUTER_DEVELOPMENT_ROUTER_HOLDOUT_split": {
                "status": "FIXED_BY_GOVERNANCE",
                "note": "ROUTER_HOLDOUT is never touched by Phase29; split is not regenerated",
                "authority": "reports/audits/phase26_downstream_phase_boundary_audit.json",
            },
            "Phase25A_crossfit_folds": {
                "status": "UNRESOLVED",
                "canonical_derivation": "sha256('42::<group_key>') ordering with crossfit_seed=42",
                "source": "reports/audits/phase25a_crossfit_protocol.json",
                "source_sha256": sha(AUD / "phase25a_crossfit_protocol.json"),
            },
            "Phase25D_outer_folds": {
                "status": "UNRESOLVED",
                "canonical_derivation": "StratifiedGroupKFold(n_splits=5, random_state=42)",
                "source": "reports/audits/phase25d_cv_protocol_v1_2_1.json",
                "source_sha256": sha(AUD / "phase25d_cv_protocol_v1_2_1.json"),
            },
            "Phase25D_FIT_EARLYSTOP_inner_roles": {
                "status": "UNRESOLVED",
                "canonical_derivation": "StratifiedGroupKFold(n_splits=10, random_state=4200+k)",
                "source": "reports/audits/phase25d_frozen_training_spec_binding_v1_2_1.json",
                "source_sha256": sha(AUD / "phase25d_frozen_training_spec_binding_v1_2_1.json"),
            },
            "Phase25F_folds": {
                "status": "FIXED_BY_GOVERNANCE",
                "canonical_derivation": "REUSE_EXACT Phase25D FIT/EARLY_STOP/OUTER_TARGET manifests",
                "source": "reports/audits/phase25f_cv_manifest_reuse_contract_v1_0.json",
                "source_sha256": sha(AUD / "phase25f_cv_manifest_reuse_contract_v1_0.json"),
                "invent_new_split": False,
            },
        },
        "if_folds_regenerated_per_seed_then": {
            "mixes": ["optimization_variance", "partition_variance"],
            "must_be_recorded": True,
            "interpretation_must_be_frozen_explicitly": True,
        },
        "split_fold_rule_resolved": False,
        "blocked_terminal_if_unresolved": BLOCKED_TERMINALS["MULTISEED_SPLIT_OR_FOLD_RULE_UNRESOLVED"],
        "all_pass": False,
    }
    write_json(AUD / "phase29_split_fold_stability_audit.json", obj)
    print(f"[§6] split/fold rule RESOLVED={obj['split_fold_rule_resolved']} (HARD BLOCKER)")
    return obj


# ==========================================================================
# §7  Holdout protection
# ==========================================================================
def section_7():
    obj = {
        "artifact": "phase29_phase30_holdout_lock",
        "phase": 29,
        "classification": "PHASE29_PHASE30_HOLDOUT_LOCK",
        "router_holdout_owner": "PHASE30",
        "router_holdout_state": "RESERVED_UNOPENED_FOR_PHASE30",
        "router_holdout_n": 875,
        "phase29_must_not": [
            "train on its routing outcomes", "calibrate on its outcomes",
            "evaluate on it", "inspect its metrics",
        ],
        "ROUTER_HOLDOUT_reads": 0,
        "router_holdout_reads_required_zero": True,
        "test_state": "LOCKED_UNTIL_PHASE39",
        "phase30_started": False,
        "authority": [
            {"path": "reports/audits/phase26_downstream_phase_boundary_audit.json",
             "sha256": sha(AUD / "phase26_downstream_phase_boundary_audit.json"),
             "binds": "phase30.state = RESERVED_UNOPENED_FOR_PHASE30; one_shot = true"},
            {"path": "reports/audits/phase28_phase29_boundary_audit.json",
             "sha256": sha(AUD / "phase28_phase29_boundary_audit.json")},
        ],
        "all_pass": True,
    }
    write_json(AUD / "phase29_phase30_holdout_lock.json", obj)
    print("[§7] holdout lock written")
    return obj


# ==========================================================================
# §8  Evaluation population (HARD BLOCKER)
# ==========================================================================
def section_8():
    obj = {
        "artifact": "phase29_evaluation_population_audit",
        "phase": 29,
        "classification": "PHASE29_EVALUATION_POPULATION_AUDIT",
        "hard_blocker": True,
        "question": "exactly where is three-seed reproducibility evaluated?",
        "candidate_populations": ["ROUTER_DEVELOPMENT", "VAL808"],
        "forbidden_populations": ["ROUTER_HOLDOUT", "TEST"],
        "population_records": {
            "ROUTER_DEVELOPMENT": {
                "n": 4957,
                "purpose": "canonical development population for all Phase25x/Phase27/Phase28 DEV evidence",
                "new_inference_required": "UNRESOLVED",
                "metrics": "UNRESOLVED",
                "grouping": "canonical composite group_key (PATIENT/ASSET/RISK/SINGLETON)",
                "gt_previously_opened": True,
                "gt_opening_phases": ["Phase25C", "Phase25F", "Phase28"],
                "evidence_class": "DEVELOPMENT_EVIDENCE",
                "authority_binding_population": True,
            },
            "VAL808": {
                "n": 808,
                "purpose": "already-opened development evidence from Phase27",
                "new_inference_required": "UNRESOLVED",
                "metrics": "UNRESOLVED",
                "grouping": "domain-stratified group bootstrap (B=2000, seed 42)",
                "gt_previously_opened": True,
                "gt_opening_phases": ["Phase21 (VAL scoring)", "Phase27"],
                "evidence_class": "MULTI_SEED_CONTINUITY_DEVELOPMENT_EVIDENCE",
                "forbidden_labels": ["holdout", "independent validation", "external validation"],
                "authority_binding_population": False,
            },
        },
        "bound_population_by_authority": "ROUTER_DEVELOPMENT",
        "bound_population_evidence": [
            {"path": "reports/audits/phase26_downstream_phase_boundary_audit.json",
             "sha256": sha(AUD / "phase26_downstream_phase_boundary_audit.json"),
             "value": "phase29.population = ROUTER_DEVELOPMENT (DEV)"},
            {"path": "reports/audits/phase28_phase29_boundary_audit.json",
             "sha256": sha(AUD / "phase28_phase29_boundary_audit.json"),
             "value": "phase29.population = ROUTER_DEVELOPMENT (DEV)"},
            {"path": "notebooks/phasewise/phase_29_3seed_reproducibility/README.md",
             "sha256": sha(ROOT / "notebooks/phasewise/phase_29_3seed_reproducibility/README.md"),
             "value": "Dataset Cohorts: TRAIN and VAL only (TEST strictly locked)"},
        ],
        "evaluation_population_resolved": False,
        "evaluation_population_conflict": True,
        "conflict_description": (
            "Authoritative boundary audits bind the Phase29 POPULATION to ROUTER_DEVELOPMENT (DEV). "
            "The Phase29 README simultaneously states 'Dataset Cohorts: TRAIN and VAL only'. "
            "Whether Phase29 evaluation additionally reports VAL808 is therefore NOT explicit. "
            "Under the work order §8 the exact evaluation population must be explicit; it is not."),
        "population_and_reporting_population_must_be_distinguished": True,
        "blocked_terminal_if_unresolved": BLOCKED_TERMINALS["REPRODUCIBILITY_EVALUATION_POPULATION_UNRESOLVED"],
        "all_pass": False,
    }
    write_json(AUD / "phase29_evaluation_population_audit.json", obj)
    print(f"[§8] evaluation population RESOLVED={obj['evaluation_population_resolved']} (HARD BLOCKER)")
    return obj


# ==========================================================================
# §9  VAL808 status
# ==========================================================================
def section_9():
    obj = {
        "artifact": "phase29_val808_status",
        "phase": 29,
        "classification": "PHASE29_VAL808_STATUS_BINDING",
        "val808_used_by_phase29": "UNRESOLVED",
        "val808_evidence_class_if_used": "MULTI_SEED_CONTINUITY_DEVELOPMENT_EVIDENCE",
        "val808_already_opened": True,
        "val808_opening_phases": ["Phase21 (VAL scoring)", "Phase27 (preservation audit)"],
        "val808_must_never_be_called": ["holdout", "independent validation", "external validation"],
        "val808_tuning_forbidden": True,
        "rule": "No Phase29 decision may tune configuration from VAL808 seed results.",
        "val808_n": 808,
        "phase27_preservation_result": {
            "preservation_asserted": True,
            "macro_ci": [0.001133, 0.003298],
            "non_inferiority_margin": 0.005,
        },
        "all_pass": True,
    }
    write_json(AUD / "phase29_val808_status.json", obj)
    print("[§9] VAL808 status bound")
    return obj


# ==========================================================================
# §10-§13  Component protocols
# ==========================================================================
def section_10_13():
    obj = {
        "artifact": "phase29_component_protocol_binding",
        "phase": 29,
        "classification": "PHASE29_COMPONENT_PROTOCOL_BINDING",
        "note": "Protocol inheritance is frozen; whether each component is IN SCOPE is §4 (UNRESOLVED).",
        "G_GlobalMedFiLM": {
            "in_scope_status": "UNRESOLVED",
            "inherits": "Phase21",
            "architecture_id": "global_medfilm_shared_residual_unet_film5_no_se_no_deep_supervision_v1",
            "architecture_binding": "reports/audits/phase21_global_medfilm_architecture_binding.json",
            "architecture_binding_sha256": sha(AUD / "phase21_global_medfilm_architecture_binding.json"),
            "training_population": "TRAIN 5832",
            "loss": {"name": "bce_dice", "bce_weight": 0.5, "dice_weight": 0.5, "dice_epsilon": 1e-6},
            "optimizer": {"name": "AdamW", "learning_rate": 1e-4, "weight_decay": 1e-4},
            "scheduler": {"name": "CosineAnnealingLR", "T_max": 100, "step": "per_epoch_after_train_and_val"},
            "max_epochs": 100,
            "early_stopping_patience": 15,
            "early_stopping_ties_count_as_bad_epochs": True,
            "film_conditioning": True,
            "amp": True,
            "canonical_seed42_best_epoch": 66,
            "canonical_seed42_final_epoch": 81,
            "canonical_seed42_stop_reason": "EARLY_STOPPING_PATIENCE",
            "train_membership_reused_for_all_seeds": "UNRESOLVED",
            "per_seed_checkpoint_path_isolation_required": True,
            "canonical_seed42_checkpoint_must_not_be_overwritten": True,
        },
        "R_psi_BARRRegionalRefinerV1": {
            "in_scope_status": "UNRESOLVED",
            "inherits": "Phase25A ROI-0.30",
            "crossfit_protocol": "reports/audits/phase25a_crossfit_protocol.json",
            "crossfit_protocol_sha256": sha(AUD / "phase25a_crossfit_protocol.json"),
            "augmentation_binding": "reports/audits/phase25a_augmentation_binding.json",
            "augmentation_binding_sha256": sha(AUD / "phase25a_augmentation_binding.json"),
            "outer_folds": 3,
            "inner_fit_fraction": 0.9,
            "inner_early_stop_fraction": 0.1,
            "outer_target_role": "UNTOUCHED; OOF only",
            "roi_geometry": "ROI-0.30 canonical (threshold 0.30, expansion 1.50, 256 crop)",
            "loss": "0.5*BCEWithLogits + 0.5*Dice(1e-6)",
            "optimizer": {"name": "AdamW", "lr": 1e-4, "weight_decay": 1e-4},
            "scheduler": {"name": "CosineAnnealingLR", "T_max": 100},
            "batch_size": 8, "max_epochs": 100, "patience": 15,
            "checkpoint_rule": "min EARLY_STOP total loss",
            "param_count": 1276401,
            "fold_membership_behavior_across_seeds": "UNRESOLVED",
            "final_refit_rule": "UNRESOLVED",
            "changing_crossfit_fold_assignment_between_seeds": "MUST_BE_CLASSIFIED_AS_PARTITION_VARIATION",
        },
        "B_phi_BARRBenefitRouterV1": {
            "in_scope_status": "UNRESOLVED",
            "inherits": "Phase25D v1.2.1",
            "spec_binding": "reports/audits/phase25d_frozen_training_spec_binding_v1_2_1.json",
            "spec_binding_sha256": sha(AUD / "phase25d_frozen_training_spec_binding_v1_2_1.json"),
            "architecture": "Embedding(4,16) -> Linear(218,128) -> LayerNorm(128) -> SiLU -> Dropout(0.10) -> Linear(128,64) -> LayerNorm -> SiLU -> Linear(64,1)",
            "param_count": 36801,
            "outer_folds": 5,
            "inner_fit_early_stop": "StratifiedGroupKFold(n_splits=10, random_state=4200+k)",
            "normalization": "FIT-only ddof=0; final refit on ALL 4957 DEV rows",
            "loss": {"name": "Huber", "delta": 0.05},
            "optimizer": {"name": "AdamW", "lr": 1e-3, "weight_decay": 1e-4},
            "batch_size": 128, "max_epochs": 200, "patience": 20,
            "scheduler": "ReduceLROnPlateau(factor 0.5, patience 8, threshold 1e-4, rel, min_lr 1e-6)",
            "checkpoint_metric": "EARLY_STOP mean Huber loss", "direction": "MINIMIZE",
            "final_refit_epoch_rule": "sorted(best_epoch_0..4)[2] (exact integer median)",
            "final_refit_seed": 42, "final_checkpoint_rule": "LAST_FIXED_EPOCH",
            "per_seed_required": "UNRESOLVED (OOF predictions? final all-DEV checkpoint?)",
            "no_rule_may_be_invented_after_seed_results": True,
        },
        "S_omega_BARRPostSafetyV1": {
            "in_scope_status": "UNRESOLVED",
            "inherits": "Phase25F",
            "cv_manifest_reuse_contract": "reports/audits/phase25f_cv_manifest_reuse_contract_v1_0.json",
            "cv_manifest_reuse_contract_sha256": sha(AUD / "phase25f_cv_manifest_reuse_contract_v1_0.json"),
            "architecture_contract": "reports/audits/phase25f_architecture_contract_v1_0.json",
            "architecture_contract_sha256": sha(AUD / "phase25f_architecture_contract_v1_0.json"),
            "architecture": "Linear(20,32)->SiLU->Linear(32,16)->SiLU->Linear(16,1)",
            "param_count": 1217,
            "input_features": "20-D = 16 numeric + 4 one-hot task",
            "target": "post-refinement accept/fallback benefit label",
            "folds": 5,
            "cv_seeds": "54000-54004",
            "normalization": "FIT-only ddof=0 of the 16 numeric features",
            "loss": "BCEWithLogitsLoss (mean reduction; no class weighting)",
            "threshold": 0.50,
            "threshold_calibration": "NONE",
            "final_refit_rule": "exact median of five best epochs; FINAL_SAFETY_EPOCHS=23; LAST_FIXED_EPOCH",
            "final_refit_seed": 42,
            "per_seed_required": "UNRESOLVED (OOF safety predictions? final all-DEV checkpoint?)",
        },
        "all_pass": False,
    }
    write_json(AUD / "phase29_component_protocol_binding.json", obj)
    print("[§10-§13] component protocols bound (scope UNRESOLVED)")
    return obj


# ==========================================================================
# §14  Dependency consistency
# ==========================================================================
def section_14():
    obj = {
        "artifact": "phase29_component_dependency_audit",
        "phase": 29,
        "classification": "PHASE29_COMPONENT_DEPENDENCY_AUDIT",
        "question": "is each seed's system internally seed-consistent?",
        "example": {
            "seed123_router_must_consume": [
                "seed123 global features?",
                "seed123 refiner candidates?",
                "or canonical seed-42 predecessors?",
            ],
            "status": "MUST_BE_EXPLICIT_UNRESOLVED",
        },
        "allowed_classifications": [
            "FULL_SEED_CONSISTENT_PIPELINE",
            "MODULEWISE_REPRODUCIBILITY_WITH_CANONICAL_FIXED_UPSTREAM",
        ],
        "selected_classification": "UNRESOLVED",
        "must_not_mix_silently": True,
        "dependency_edges": [
            {"from": "G", "to": "R_psi", "reason": "refiner consumes global probability channel (p_global)"},
            {"from": "G", "to": "B_phi", "reason": "router consumes 202-D pre-refinement features derived from G"},
            {"from": "R_psi", "to": "B_phi", "reason": "router target = paired refinement gain (DeltaDice) produced by R_psi"},
            {"from": "R_psi", "to": "S_omega", "reason": "post-safety features derive from refined candidate probability"},
            {"from": "B_phi", "to": "S_omega", "reason": "S_omega consumes the routed/fused decisions"},
        ],
        "dependency_chain_resolved": False,
        "blocked_terminal_if_unresolved": BLOCKED_TERMINALS["SEED_SPECIFIC_DEPENDENCY_CHAIN_UNRESOLVED"],
        "all_pass": False,
    }
    write_json(AUD / "phase29_component_dependency_audit.json", obj)
    print(f"[§14] dependency chain RESOLVED={obj['dependency_chain_resolved']}")
    return obj


# ==========================================================================
# §15-§17  Feature / gain / safety target regeneration
# ==========================================================================
def section_15_17():
    obj = {
        "artifact": "phase29_feature_target_regeneration_audit",
        "phase": 29,
        "classification": "PHASE29_FEATURE_TARGET_REGENERATION_AUDIT",
        "feature_cache_question": {
            "question": "if G is retrained, must the Phase25B 202-D feature cache be regenerated per seed?",
            "phase25b_cache": {
                "dir": "data_cache/phase25b_barr_pre_refinement_features_v1_2",
                "features_shape": [4957, 202],
                "features_dtype": "float32",
                "features_sha256": "9c241963b54f23de1c9671ff6670dde7d6f7e2510869ef5ebc1baf3f7c833e0a",
                "gt_free": True,
                "source_binding": "reports/audits/phase25b_phase25c_handoff_schema.json",
                "source_binding_sha256": sha(AUD / "phase25b_phase25c_handoff_schema.json"),
            },
            "regenerate_per_seed": "UNRESOLVED",
            "if_no_reuse_seed42_features_must_be_justified": True,
            "gt_free_feature_extraction_semantics_frozen": True,
        },
        "paired_gain_target_question": {
            "question": ("if R_psi changes by seed and B_phi is also retrained, does each seed need its own "
                         "DeltaDice target / Phase25C-style cross-fitted candidate outcomes?"),
            "risk": ("using seed-42 DeltaDice to train a router for a different-seed refiner may not "
                     "represent that seed's actual intervention benefit"),
            "regenerate_per_seed": "UNRESOLVED",
            "correct_dependency_frozen": False,
            "blocked_terminal_if_unresolved": BLOCKED_TERMINALS["SEED_SPECIFIC_ROUTER_TARGET_DEPENDENCY_UNRESOLVED"],
        },
        "post_safety_target_question": {
            "question": ("if seed-specific refiner candidates change, must S_omega labels/features be "
                         "regenerated for each seed?"),
            "regenerate_per_seed": "UNRESOLVED",
            "seed_specific_target_dependency": "UNRESOLVED",
            "oof_leakage_safe_generation": "REQUIRED_IF_REGENERATED",
            "feature_equations": "frozen (phase25f_feature_equation_contract_v1_0)",
            "normalization_ownership": "FIT-only, ddof=0",
            "reuse_seed42_safety_targets_without_justification_forbidden": True,
        },
        "any_regeneration_resolved": False,
        "blocked_terminal_if_unresolved": BLOCKED_TERMINALS["SEED_SPECIFIC_DEPENDENCY_CHAIN_UNRESOLVED"],
        "all_pass": False,
    }
    write_json(AUD / "phase29_feature_target_regeneration_audit.json", obj)
    print("[§15-§17] feature/target regeneration audit written (UNRESOLVED)")
    return obj


# ==========================================================================
# §18  Canonical policy / budget
# ==========================================================================
def section_18():
    obj = {
        "artifact": "phase29_canonical_policy_binding",
        "phase": 29,
        "classification": "PHASE29_CANONICAL_POLICY_BINDING",
        "phase29_must_not_select_new_policy": True,
        "canonical_structural_choices": {
            "system": "A8/C9",
            "nominal_budget": 0.25,
            "lambda_representative": 0.25,
            "roi_proposal_threshold": 0.30,
            "s_omega_threshold": 0.50,
            "segmentation_threshold": 0.50,
            "K": 1239,
        },
        "no_seed_may_receive_different_architecture_because_of_performance": True,
        "authority": [
            {"path": "reports/audits/phase28_final_freeze.json",
             "sha256": sha(AUD / "phase28_final_freeze.json")},
            {"path": "docs/phase28_ablation_execution_spec_v1_2.md",
             "sha256": sha(ROOT / "docs/phase28_ablation_execution_spec_v1_2.md")},
        ],
        "all_pass": True,
    }
    write_json(AUD / "phase29_canonical_policy_binding.json", obj)
    print("[§18] canonical policy bound")
    return obj


# ==========================================================================
# §19  Final-router threshold across seeds (HARD BLOCKER)
# ==========================================================================
def section_19():
    obj = {
        "artifact": "phase29_router_calibration_rule_audit",
        "phase": 29,
        "classification": "PHASE29_ROUTER_CALIBRATION_RULE_AUDIT",
        "hard_blocker": True,
        "question": ("if each seed has a newly trained final B_phi its score scale may differ; "
                     "what is the Phase29 rule?"),
        "candidate_rules": {
            "A": "reuse canonical seed-42 absolute runtime threshold",
            "B": "calibrate each seed's final router on development to the same frozen nominal 25% rule",
            "C": "evaluate by rank-based fixed K only",
        },
        "rule_A_exact_threshold": "-5003565381643716252018011/205414980000000000000000000",
        "rule_B_nominal_budget": 0.25,
        "rule_C_K": 1239,
        "search_for_existing_governance_binding": [
            {"path": "reports/audits/phase26_canonical_router_threshold_binding_v1_0.json",
             "exists": (AUD / "phase26_canonical_router_threshold_binding_v1_0.json").exists(),
             "binds_multiseed_rule": False},
            {"path": "reports/audits/phase26_final_router_calibration_binding_v1_2.json",
             "exists": (AUD / "phase26_final_router_calibration_binding_v1_2.json").exists(),
             "binds_multiseed_rule": False},
            {"path": "reports/audits/phase25e_adjudication_reconciled.json",
             "exists": (AUD / "phase25e_adjudication_reconciled.json").exists(),
             "binds_multiseed_rule": False},
            {"path": "docs/RULES.md",
             "sha256": sha(ROOT / "docs/RULES.md"),
             "binds_multiseed_rule": False,
             "note": ("RULES.md binds TEST/single-seed superiority rules but does NOT bind a "
                      "multi-seed router calibration rule")},
        ],
        "existing_governance_binds_multiseed_rule": False,
        "selected_rule": None,
        "rule_must_be_bound_before_seeing_seed_scores": True,
        "blocked_terminal_if_unresolved": BLOCKED_TERMINALS["MULTISEED_ROUTER_CALIBRATION_RULE_UNRESOLVED"],
        "all_pass": False,
    }
    write_json(AUD / "phase29_router_calibration_rule_audit.json", obj)
    print(f"[§19] router calibration rule = {obj['selected_rule']} (HARD BLOCKER)")
    return obj


# ==========================================================================
# §20  S_omega threshold
# ==========================================================================
def section_20():
    obj = {
        "artifact": "phase29_s_omega_threshold_binding",
        "phase": 29,
        "classification": "PHASE29_S_OMEGA_THRESHOLD_BINDING",
        "s_omega_threshold": 0.50,
        "logit_threshold": 0.0,
        "seed_specific_threshold_calibration": False,
        "conflicting_source_found": False,
        "fail_closed_on_conflict": True,
        "authority": "docs/RULES.md (three distinct thresholds never conflated)",
        "authority_sha256": sha(ROOT / "docs/RULES.md"),
        "all_pass": True,
    }
    write_json(AUD / "phase29_s_omega_threshold_binding.json", obj)
    print("[§20] S_omega threshold = 0.50")
    return obj


# ==========================================================================
# §21-§25  Estimands / question / criteria / preservation / statistics
# ==========================================================================
def section_21_25():
    obj = {
        "artifact": "phase29_reproducibility_estimands_and_statistics",
        "phase": 29,
        "classification": "PHASE29_REPRODUCIBILITY_ESTIMANDS_AND_STATISTICS",
        "estimands_frozen_before_training": True,
        "primary_estimands": [
            "per-seed macro-domain Dice",
            "per-domain Dice",
            "per-seed routed DeltaDice",
            "activation fraction",
            "S_omega accept/reject fractions",
        ],
        "across_seed_summary": ["mean", "standard_deviation", "minimum", "maximum", "range"],
        "n_seeds": 3,
        "inferential_significance_claim_forbidden": True,
        "formal_hypothesis_testing_owner": "PHASE31",
        "primary_reproducibility_question": (
            "Does the direction and practical magnitude of the canonical RA-MedFiLM-BARR development "
            "result remain reasonably stable across the three pre-registered training seeds?"),
        "reproducibility_is_not": "all seeds must be numerically identical",
        "seed_variation_expected": True,
        "search_for_preregistered_numeric_criterion": {
            "searched": True,
            "found": False,
        },
        "numeric_success_gate": None,
        "frozen_criterion_if_none_registered":
            "DESCRIPTIVE_REPRODUCIBILITY_STUDY__NO_NUMERIC_PASS_FAIL_GATE",
        "preservation_criterion": {
            "phase27_criterion": "lower 95% CI > -0.005",
            "applied_separately_per_seed_on_VAL808": "UNRESOLVED",
            "adopted": False,
            "must_be_bound_before_execution_if_adopted": True,
            "alternative": "report seed variation only",
        },
        "statistics_scope": {
            "seed_wise_point_estimates": True,
            "across_seed_mean_std_range": True,
            "per_seed_frozen_bootstrap_ci": "OPTIONAL (if population sampling uncertainty is reported)",
            "forbidden": ["post-hoc seed significance tests", "multiple-comparison fishing", "winner tests"],
        },
        "phase31_owns_formal_testing": True,
        "all_pass": True,
    }
    write_json(AUD / "phase29_statistics_scope_audit.json", obj)
    print("[§21-§25] estimands/statistics scope frozen")
    return obj


# ==========================================================================
# §26  Deterministic training requirements
# ==========================================================================
def section_26():
    obj = {
        "artifact": "phase29_deterministic_runtime_rule",
        "phase": 29,
        "classification": "PHASE29_DETERMINISTIC_RUNTIME_RULE",
        "per_seed_deterministic_controls": {
            "python_rng": "torch.manual_seed(seed) + random.seed(seed)",
            "numpy_rng": "np.random.seed(seed)",
            "torch_cpu_rng": "torch.manual_seed(seed)",
            "cuda_rng": "torch.cuda.manual_seed_all(seed)",
            "dataloader_generator": "torch.Generator().manual_seed(make_generator_seed)",
            "worker_seed_init": "seed_worker() from torch.initial_seed()",
            "cudnn_deterministic": True,
            "cudnn_benchmark": False,
            "amp": True,
            "batch_size": "per component (G=512-pipeline, R_psi=8, B_phi=128, S_omega=per protocol)",
            "sample_order": "deterministic (generator-seeded shuffle)",
            "augmentation_rng": "derived from the per-seed seeded generator",
        },
        "environment_identity_recorded": True,
        "environment": {
            "python": "3.11.9",
            "torch": "2.6.0+cu124",
            "cuda": True,
            "gpu": "NVIDIA GeForce RTX 3060 Ti 8GB",
            "numpy": "2.4.6",
            "scikit_learn": "1.9.1",
        },
        "no_seed_may_silently_use_different_deterministic_settings": True,
        "deterministic_rule_frozen": True,
        "all_pass": True,
    }
    write_json(AUD / "phase29_deterministic_runtime_rule.json", obj)
    print("[§26] deterministic runtime rule frozen")
    return obj


# ==========================================================================
# §27  Seed-specific artifact roots
# ==========================================================================
def section_27():
    obj = {
        "artifact": "phase29_seed_specific_artifact_roots",
        "phase": 29,
        "classification": "PHASE29_SEED_SPECIFIC_ARTIFACT_ROOTS",
        "roots_prospective": True,
        "roots_by_seed": {
            str(s): {
                "checkpoints": f"checkpoints/phase29_seed_{s}/",
                "data_cache": f"data_cache/phase29_seed_{s}/",
                "experiments": f"experiments/phase29_seed_{s}/",
            } for s in SEEDS
        },
        "must_not_overwrite": [
            "Phase21", "Phase25A", "Phase25D", "Phase25F", "Phase26", "Phase28",
        ],
        "nonoverwriting": True,
        "all_pass": True,
    }
    write_json(AUD / "phase29_seed_specific_artifact_roots.json", obj)
    print("[§27] seed artifact roots defined")
    return obj


# ==========================================================================
# §28  Training-run count
# ==========================================================================
def section_28():
    # Per-seed logical training-run counts, derived from the frozen protocols.
    # These are stated CONDITIONALLY: the counts depend on §4 scope (UNRESOLVED).
    per_seed = {
        "G_global_medfilm_runs": 1,
        "G_global_medfilm_final_refits": 0,
        "R_psi_refiner_fold_runs": 3,
        "R_psi_refiner_final_refits": 1,
        "B_phi_router_fold_runs": 5,
        "B_phi_router_final_refits": 1,
        "S_omega_safety_fold_runs": 5,
        "S_omega_safety_final_refits": 1,
    }
    total_per_seed = sum(per_seed.values())
    obj = {
        "artifact": "phase29_training_run_plan",
        "phase": 29,
        "classification": "PHASE29_TRAINING_RUN_PLAN",
        "status": "CONDITIONAL_ON_SCOPE_RESOLUTION",
        "scope_resolved": False,
        "per_seed_logical_run_counts_if_all_four_in_scope": per_seed,
        "total_logical_runs_per_seed": total_per_seed,
        "n_seeds": 3,
        "total_logical_runs_all_seeds_if_all_four_in_scope": total_per_seed * 3,
        "seed42_artifact_reuse_authorized": "UNRESOLVED",
        "total_logical_runs_if_seed42_reuses_canonical": "UNRESOLVED (depends on §4/§5)",
        "do_not_enter_execution_with_unknown_run_count": True,
        "run_count_final": None,
        "blocked_terminal_if_unresolved": BLOCKED_TERMINALS["REPRODUCIBILITY_SPEC_INCOMPLETE"],
        "all_pass": False,
    }
    write_json(AUD / "phase29_training_run_plan.json", obj)

    header = ["component", "activity", "runs_per_seed", "n_seeds", "total_if_all_seeds", "note"]
    rows = [
        ["G", "GlobalMedFiLM training run", 1, 3, 3, "single run, fixed TRAIN/VAL membership"],
        ["G", "GlobalMedFiLM final refit", 0, 3, 0, "no refit step in canonical protocol"],
        ["R_psi", "regional-refiner fold run", 3, 3, 9, "Phase25A cross-fit outer folds"],
        ["R_psi", "regional-refiner final refit", 1, 3, 3, "all-DEV refit"],
        ["B_phi", "router fold run", 5, 3, 15, "Phase25D outer CV folds"],
        ["B_phi", "router final refit", 1, 3, 3, "median-epoch all-DEV refit"],
        ["S_omega", "safety fold run", 5, 3, 15, "Phase25F reused Phase25D folds"],
        ["S_omega", "safety final refit", 1, 3, 3, "median-epoch all-DEV refit"],
        ["TOTAL", "logical runs (all four in scope)", total_per_seed, 3, total_per_seed * 3,
         "CONDITIONAL: depends on §4 training scope and §5 seed-42 reuse"],
    ]
    write_csv(TAB / "phase29_training_run_plan.csv", header, rows)
    print(f"[§28] training-run plan: {total_per_seed}/seed, {total_per_seed*3} total (CONDITIONAL)")
    return obj


# ==========================================================================
# §29  Existing seed-42 reuse eligibility table
# ==========================================================================
def section_29():
    header = ["component", "existing_artifact", "existing_sha", "protocol_exact_match",
              "population_exact_match", "split_exact_match", "training_rule_exact_match",
              "evaluation_rule_exact_match", "reusable", "reason"]

    def sh(p):
        return sha(ROOT / p) or ""

    rows = [
        ["G", "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt",
         "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7",
         "TRUE", "TRUE", "TRUE", "TRUE", "UNRESOLVED", "UNRESOLVED",
         "protocol matches; evaluation rule not yet frozen"],
        ["R_psi", "checkpoints/phase25a_barr_regional_refiner_v1_1_roi030/final/final.pt",
         "6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109",
         "TRUE", "TRUE", "TRUE", "TRUE", "UNRESOLVED", "UNRESOLVED",
         "protocol matches; evaluation rule not yet frozen"],
        ["B_phi", "checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt",
         "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b",
         "TRUE", "TRUE", "TRUE", "TRUE", "UNRESOLVED", "UNRESOLVED",
         "protocol matches; evaluation rule not yet frozen"],
        ["S_omega", "checkpoints/phase25f_barr_post_safety_v1_0_seed42/final/final.pt",
         "eee9b97b9921e53fc07eac9281dce64ba518c6e1659916b97b0b3bec21ec6d2e",
         "TRUE", "TRUE", "TRUE", "TRUE", "UNRESOLVED", "UNRESOLVED",
         "protocol matches; evaluation rule not yet frozen"],
        ["G features", "data_cache/phase25b_barr_pre_refinement_features_v1_2/features.npy",
         "9c241963b54f23de1c9671ff6670dde7d6f7e2510869ef5ebc1baf3f7c833e0a",
         "TRUE", "TRUE", "N/A", "N/A", "UNRESOLVED", "UNRESOLVED",
         "202-D GT-free cache; regeneration rule unresolved (§15)"],
        ["B_phi OOF", "data_cache/phase28_router_variants_v1_2 (router OOF tables)",
         "", "N/A", "TRUE", "TRUE", "TRUE", "UNRESOLVED", "UNRESOLVED",
         "OOF tables are seed-42; seed-specific need unresolved"],
        ["S_omega OOF", "data_cache/phase25f_barr_post_safety_v1_0/oof_refined_crop_prob.npy",
         "", "TRUE", "TRUE", "TRUE", "TRUE", "UNRESOLVED", "UNRESOLVED",
         "seed-42 safety OOF; reuse justification unresolved (§17)"],
    ]
    write_csv(TAB / "phase29_seed42_reuse_eligibility.csv", header, rows)
    print(f"[§29] seed-42 reuse eligibility table ({len(rows)} rows)")
    return {"artifact": "phase29_seed42_reuse_eligibility_table", "phase": 29,
            "n_rows": len(rows), "path": "reports/tables/phase29_seed42_reuse_eligibility.csv",
            "all_pass": False}


# ==========================================================================
# §30  Component dependency table
# ==========================================================================
def section_30():
    header = ["artifact", "depends_on_global_seed", "depends_on_refiner_seed",
              "depends_on_router_seed", "depends_on_safety_seed", "regenerated_per_seed",
              "reuse_allowed", "reason"]
    rows = [
        ["Phase25B-like features (202-D)", "YES", "NO", "NO", "NO", "UNRESOLVED", "UNRESOLVED",
         "derived from G forward; regeneration rule unresolved"],
        ["Phase25C-like gain targets (DeltaDice)", "NO", "YES", "NO", "NO", "UNRESOLVED", "UNRESOLVED",
         "pairwise gain from R_psi intervention; seed dependency unresolved"],
        ["router normalization", "YES", "NO", "YES", "NO", "UNRESOLVED", "UNRESOLVED",
         "FIT-only ddof=0 statistics depend on features + fold membership"],
        ["router OOF scores", "YES", "YES", "YES", "NO", "UNRESOLVED", "UNRESOLVED",
         "router consumes features (G) and target (R_psi)"],
        ["router final threshold/calibration", "NO", "NO", "YES", "NO", "UNRESOLVED", "UNRESOLVED",
         "seed-specific score scale; rule unresolved (§19)"],
        ["S_omega features", "NO", "YES", "YES", "NO", "UNRESOLVED", "UNRESOLVED",
         "derived from refined candidate + routed decisions"],
        ["S_omega labels", "NO", "YES", "YES", "NO", "UNRESOLVED", "UNRESOLVED",
         "accept/fallback benefit label depends on refiner+router state"],
        ["final system predictions", "YES", "YES", "YES", "YES", "UNRESOLVED", "UNRESOLVED",
         "A8/C9 composition of all four components"],
    ]
    write_csv(TAB / "phase29_seed_dependency_graph.csv", header, rows)
    print(f"[§30] dependency graph table ({len(rows)} rows)")
    return {"artifact": "phase29_seed_dependency_table", "phase": 29, "n_rows": len(rows),
            "path": "reports/tables/phase29_seed_dependency_graph.csv", "all_pass": False}


# ==========================================================================
# §31  Evaluation matrix
# ==========================================================================
def section_31():
    header = ["seed", "population", "metric_family", "new_inference", "gt_access",
              "evidence_class", "bootstrap_artifact", "role", "holdout_or_test"]
    rows = []
    for s in SEEDS:
        rows.append([s, "ROUTER_DEVELOPMENT", "macro-domain Dice", "UNRESOLVED", "YES (already opened)",
                     "DEVELOPMENT_EVIDENCE", "UNRESOLVED", "PRIMARY", "NO"])
        rows.append([s, "ROUTER_DEVELOPMENT", "per-domain Dice", "UNRESOLVED", "YES (already opened)",
                     "DEVELOPMENT_EVIDENCE", "UNRESOLVED", "SECONDARY", "NO"])
        rows.append([s, "ROUTER_DEVELOPMENT", "routed DeltaDice", "UNRESOLVED", "YES (already opened)",
                     "DEVELOPMENT_EVIDENCE", "UNRESOLVED", "PRIMARY", "NO"])
        rows.append([s, "ROUTER_DEVELOPMENT", "activation fraction", "UNRESOLVED", "N/A",
                     "DEVELOPMENT_EVIDENCE", "N/A", "SECONDARY", "NO"])
        rows.append([s, "ROUTER_DEVELOPMENT", "S_omega accept/reject fraction", "UNRESOLVED", "N/A",
                     "DEVELOPMENT_EVIDENCE", "N/A", "SECONDARY", "NO"])
        rows.append([s, "VAL808", "macro-domain Dice (continuity)", "UNRESOLVED", "YES (already opened)",
                     "MULTI_SEED_CONTINUITY_DEVELOPMENT_EVIDENCE", "UNRESOLVED", "UNRESOLVED", "NO"])
    write_csv(TAB / "phase29_evaluation_plan.csv", header, rows)
    print(f"[§31] evaluation matrix ({len(rows)} rows; no holdout/test row)")
    return {"artifact": "phase29_evaluation_matrix", "phase": 29, "n_rows": len(rows),
            "path": "reports/tables/phase29_evaluation_plan.csv",
            "no_holdout_or_test_row": True, "all_pass": False}


# ==========================================================================
# §32-§34  Boundaries
# ==========================================================================
def section_32_34():
    obj = {
        "artifact": "phase29_boundaries",
        "phase": 29,
        "classification": "PHASE29_BOUNDARY_FREEZE",
        "phase30_boundary": {
            "router_holdout_untouched": True,
            "router_holdout_state": "RESERVED_UNOPENED_FOR_PHASE30",
            "phase29_findings_may_not_change_phase30_policy_without_separate_prospective_revision": True,
            "preferred_principle": ("Phase29 is evidence about reproducibility, not another "
                                    "development-selection phase."),
        },
        "phase31_boundary": {
            "owner_of_formal_significance": "PHASE31",
            "forbidden_language_unless_preregistered_statistic_supports": [
                "significantly better across seeds", "statistically superior",
            ],
        },
        "test_lock": {
            "state": "LOCKED_UNTIL_PHASE39",
            "TEST_reads": 0,
            "required": True,
        },
        "all_pass": True,
    }
    write_json(AUD / "phase29_test_lock.json", {
        "artifact": "phase29_test_lock", "phase": 29,
        "classification": "PHASE29_TEST_LOCK", "test_state": "LOCKED_UNTIL_PHASE39",
        "TEST_reads": 0, "test_reads_required_zero": True, "all_pass": True})
    write_json(AUD / "phase29_boundaries.json", obj)
    print("[§32-§34] boundaries frozen; test lock written")
    return obj


# ==========================================================================
# §35  Specification completeness matrix
# ==========================================================================
def section_35():
    def src(p):
        return rel(ROOT / p), sha(ROOT / p)

    fields = [
        ("canonical_title", "Three-Seed Deterministic Reproducibility Study",
         "configs/research_protocol.json", True, True, "title bound"),
        ("phase29_role", "measure sensitivity/stability of frozen DEV result to frozen seeds",
         "notebooks/phasewise/phase_29_3seed_reproducibility/README.md", True, True, "role bound"),
        ("authoritative_seed_policy", "[42, 123, 3407] from configs/research_protocol.json",
         "configs/research_protocol.json", True, True, "seed set frozen"),
        ("seed_1", "42", "configs/research_protocol.json", True, True, ""),
        ("seed_2", "123", "configs/research_protocol.json", True, True, ""),
        ("seed_3", "3407", "configs/research_protocol.json", True, True, ""),
        ("training_scope", "UNRESOLVED", "NONE_FOUND", False, True,
         "no authoritative artifact defines which components retrain"),
        ("seed42_reuse_rule", "UNRESOLVED", "NONE_FOUND", False, True,
         "depends on §4 scope and §8 evaluation rule"),
        ("data_split_rule", "UNRESOLVED", "NONE_FOUND", False, True,
         "TRAIN/VAL split regeneration behavior not explicit"),
        ("crossfit_fold_rule", "UNRESOLVED", "phase25a_crossfit_protocol.json", False, True,
         "seed-dependent fold assignment behavior not explicit"),
        ("global_training_rule", "Phase21 protocol (bound)", "phase20_shared_global_baseline_protocol.json",
         True, True, "inheritance frozen; scope unresolved"),
        ("refiner_training_rule", "Phase25A ROI-0.30 protocol (bound)",
         "phase25a_crossfit_protocol.json", True, True, "inheritance frozen; scope unresolved"),
        ("router_training_rule", "Phase25D v1.2.1 protocol (bound)",
         "phase25d_frozen_training_spec_binding_v1_2_1.json", True, True,
         "inheritance frozen; scope unresolved"),
        ("safety_training_rule", "Phase25F protocol (bound)",
         "phase25f_cv_manifest_reuse_contract_v1_0.json", True, True,
         "inheritance frozen; scope unresolved"),
        ("seed_dependency_model", "UNRESOLVED", "NONE_FOUND", False, True,
         "FULL_SEED_CONSISTENT vs MODULEWISE not selected"),
        ("feature_regeneration_rule", "UNRESOLVED", "phase25b_phase25c_handoff_schema.json", False, True,
         "202-D cache regeneration per seed not decided"),
        ("gain_target_regeneration_rule", "UNRESOLVED", "NONE_FOUND", False, True,
         "DeltaDice target seed-dependency not decided"),
        ("safety_target_regeneration_rule", "UNRESOLVED", "NONE_FOUND", False, True,
         "S_omega label regeneration per seed not decided"),
        ("final_router_calibration_rule", "UNRESOLVED", "NONE_FOUND", False, True,
         "rule A/B/C not bound by existing governance"),
        ("canonical_policy_rule", "A8/C9, b=0.25, K=1239, thresholds 0.30/0.50/0.50",
         "reports/audits/phase28_final_freeze.json", True, True, "policy frozen"),
        ("evaluation_population", "UNRESOLVED", "NONE_FOUND", False, True,
         "boundary audits say DEV; README says TRAIN+VAL — not explicit"),
        ("VAL808_role", "MULTI_SEED_CONTINUITY_DEVELOPMENT_EVIDENCE", "docs/phase27_preservation_spec.md",
         True, True, "role bound; whether used unresolved"),
        ("ROUTER_DEVELOPMENT_role", "DEVELOPMENT_EVIDENCE (bound population)",
         "reports/audits/phase26_downstream_phase_boundary_audit.json", True, True, ""),
        ("ROUTER_HOLDOUT_lock", "RESERVED_UNOPENED_FOR_PHASE30",
         "reports/audits/phase26_downstream_phase_boundary_audit.json", True, True, ""),
        ("TEST_lock", "LOCKED_UNTIL_PHASE39", "docs/RULES.md", True, True, ""),
        ("primary_reproducibility_estimand",
         "does direction/practical magnitude remain stable across 3 seeds",
         "THIS_SPECIFICATION", True, True, "frozen by this audit"),
        ("per_domain_reporting", "mandatory", "docs/phase27_preservation_spec.md", True, True, ""),
        ("statistics_scope", "seed-wise point estimates + mean/std/range; no significance testing",
         "THIS_SPECIFICATION", True, True, "Phase31 owns formal testing"),
        ("numeric_success_gate", "DESCRIPTIVE_REPRODUCIBILITY_STUDY__NO_NUMERIC_PASS_FAIL_GATE",
         "THIS_SPECIFICATION", True, True, "no preregistered numeric criterion found"),
        ("deterministic_runtime_rule", "frozen per-seed RNG control set",
         "THIS_SPECIFICATION", True, True, ""),
        ("training_run_count", "UNRESOLVED", "NONE_FOUND", False, True,
         "conditional on §4 scope resolution"),
        ("Phase30_boundary", "holdout untouched; no policy change", "THIS_SPECIFICATION", True, True, ""),
        ("Phase31_boundary", "formal testing owner", "THIS_SPECIFICATION", True, True, ""),
    ]
    header = ["field", "frozen_value", "authoritative_source", "source_sha", "complete",
              "blocking_if_missing", "notes"]
    rows = []
    for f, val, srcp, complete, blocking, note in fields:
        _p, s = src(srcp) if srcp != "THIS_SPECIFICATION" and srcp != "NONE_FOUND" else (srcp, "")
        rows.append([f, val, srcp, s or "", str(complete).upper(), str(blocking).upper(), note])
    write_csv(TAB / "phase29_specification_completeness.csv", header, rows)

    blocking_incomplete = [r[0] for r in rows if r[4] == "FALSE" and r[5] == "TRUE"]
    obj = {
        "artifact": "phase29_specification_completeness",
        "phase": 29,
        "classification": "PHASE29_SPECIFICATION_COMPLETENESS_MATRIX",
        "n_fields": len(rows),
        "n_complete": sum(1 for r in rows if r[4] == "TRUE"),
        "n_incomplete": sum(1 for r in rows if r[4] == "FALSE"),
        "blocking_incomplete_fields": blocking_incomplete,
        "n_blocking_incomplete": len(blocking_incomplete),
        "path": "reports/tables/phase29_specification_completeness.csv",
        "specification_complete": len(blocking_incomplete) == 0,
        "all_pass": len(blocking_incomplete) == 0,
    }
    write_json(AUD / "phase29_specification_completeness_summary.json", obj)
    print(f"[§35] completeness: {obj['n_complete']}/{obj['n_fields']} complete | "
          f"blocking incomplete: {blocking_incomplete}")
    return obj


# ==========================================================================
# §37  No-execution audit
# ==========================================================================
def section_37_noexec():
    obj = {
        "artifact": "phase29_no_execution_audit",
        "phase": 29,
        "classification": "PHASE29_NO_EXECUTION_AUDIT",
        "governance_only": True,
        "training_runs": 0,
        "model_forwards": 0,
        "new_predictions": 0,
        "new_targets": 0,
        "metrics_computed": 0,
        "checkpoints_created": 0,
        "ROUTER_HOLDOUT_reads": 0,
        "VAL808_reads": 0,
        "TEST_reads": 0,
        "scientific_notebook_created": False,
        "phase30_started": False,
        "read_only": True,
        "all_pass": True,
    }
    write_json(AUD / "phase29_no_execution_audit.json", obj)
    print("[§37] no-execution audit written (all counters zero)")
    return obj


# ==========================================================================
# main
# ==========================================================================
def main() -> int:
    print("=" * 78)
    print("PHASE 29 -- THREE-SEED DETERMINISTIC REPRODUCIBILITY STUDY")
    print("PRE-EXECUTION SPECIFICATION AUDIT (governance only)")
    print("=" * 78)
    r0 = section_0()
    r1 = section_1()
    r2 = section_2()
    r3 = section_3()
    r4 = section_4()
    r5 = section_5()
    r6 = section_6()
    r7 = section_7()
    r8 = section_8()
    r9 = section_9()
    r1013 = section_10_13()
    r14 = section_14()
    r1517 = section_15_17()
    r18 = section_18()
    r19 = section_19()
    r20 = section_20()
    r2125 = section_21_25()
    r26 = section_26()
    r27 = section_27()
    r28 = section_28()
    r29 = section_29()
    r30 = section_30()
    r31 = section_31()
    r3234 = section_32_34()
    r35 = section_35()
    r37 = section_37_noexec()

    # ---- hard blocker aggregation
    hard_blockers = {
        "predecessor_artifact_drift": not r0["gate_pass"],
        "three_seed_set_not_authoritatively_frozen": not r2["seed_set_authoritatively_frozen"],
        "reproducibility_training_scope_unresolved": not r4["scope_resolved"],
        "multiseed_split_or_fold_rule_unresolved": not r6["split_fold_rule_resolved"],
        "seed_specific_dependency_chain_unresolved": not r14["dependency_chain_resolved"],
        "seed_specific_router_target_dependency_unresolved":
            r1517["paired_gain_target_question"]["regenerate_per_seed"] == "UNRESOLVED",
        "multiseed_router_calibration_rule_unresolved": r19["selected_rule"] is None,
        "reproducibility_evaluation_population_unresolved": not r8["evaluation_population_resolved"],
    }
    active = [k for k, v in hard_blockers.items() if v]
    spec_complete = r35["specification_complete"]

    if not r0["gate_pass"]:
        terminal = BLOCKED_TERMINALS["PREDECESSOR_ARTIFACT_DRIFT"]
        exit_class = "BLOCKED"
    elif active:
        # pick the first (most upstream) blocking terminal per the work order §40 ordering
        order = [
            ("three_seed_set_not_authoritatively_frozen", "THREE_SEED_SET_NOT_AUTHORITATIVELY_FROZEN"),
            ("reproducibility_training_scope_unresolved", "REPRODUCIBILITY_TRAINING_SCOPE_UNRESOLVED"),
            ("multiseed_split_or_fold_rule_unresolved", "MULTISEED_SPLIT_OR_FOLD_RULE_UNRESOLVED"),
            ("seed_specific_dependency_chain_unresolved", "SEED_SPECIFIC_DEPENDENCY_CHAIN_UNRESOLVED"),
            ("seed_specific_router_target_dependency_unresolved", "SEED_SPECIFIC_ROUTER_TARGET_DEPENDENCY_UNRESOLVED"),
            ("multiseed_router_calibration_rule_unresolved", "MULTISEED_ROUTER_CALIBRATION_RULE_UNRESOLVED"),
            ("reproducibility_evaluation_population_unresolved",
             "REPRODUCIBILITY_EVALUATION_POPULATION_UNRESOLVED"),
        ]
        term_key = next(v for k, v in order if k in active)
        terminal = BLOCKED_TERMINALS[term_key]
        exit_class = "BLOCKED"
    elif not spec_complete:
        terminal = BLOCKED_TERMINALS["REPRODUCIBILITY_SPEC_INCOMPLETE"]
        exit_class = "BLOCKED"
    else:
        terminal = SUCCESS_TERMINAL
        exit_class = "SUCCESS"

    final = {
        "artifact": "phase29_specification_final_check",
        "phase": 29,
        "classification": "PHASE29_THREE_SEED_REPRODUCIBILITY_PRE_EXECUTION_SPECIFICATION_AUDIT",
        "method": "RA-MedFiLM-BARR",
        "governance_only": True,
        "execution": "NONE",
        "canonical_title": "Three-Seed Deterministic Reproducibility Study",
        "seeds": SEEDS,
        "seed_set_authoritatively_frozen": r2["seed_set_authoritatively_frozen"],
        "training_scope_resolved": r4["scope_resolved"],
        "seed42_role": r5["seed42_role"],
        "split_fold_rule_resolved": r6["split_fold_rule_resolved"],
        "evaluation_population_resolved": r8["evaluation_population_resolved"],
        "dependency_chain_resolved": r14["dependency_chain_resolved"],
        "router_calibration_rule": r19["selected_rule"],
        "feature_regeneration_resolved": r1517["any_regeneration_resolved"],
        "training_run_count_final": r28["run_count_final"],
        "specification_complete": spec_complete,
        "blocking_incomplete_fields": r35["blocking_incomplete_fields"],
        "hard_blockers": hard_blockers,
        "active_hard_blockers": active,
        "n_active_hard_blockers": len(active),
        "router_holdout_reads": 0,
        "val808_reads": 0,
        "test_reads": 0,
        "training_runs": 0,
        "model_forwards": 0,
        "phase29_execution_eligible": exit_class == "SUCCESS",
        "terminal": terminal,
        "success_terminal": SUCCESS_TERMINAL,
        "blocked_terminals": BLOCKED_TERMINALS,
        "exit_class": exit_class,
        "all_pass": exit_class == "SUCCESS",
    }
    write_json(AUD / "phase29_specification_final_check.json", final)

    # ---- terminal-state artifact (§39 / §40) ----------------------------------
    terminal_state = {
        "artifact": "phase29_terminal_state",
        "phase": 29,
        "classification": "PHASE29_THREE_SEED_REPRODUCIBILITY_PRE_EXECUTION_SPECIFICATION_AUDIT",
        "method": "RA-MedFiLM-BARR",
        "canonical_title": "Three-Seed Deterministic Reproducibility Study",
        "governance_only": True,
        "execution": "NONE",
        "entry_gate_terminal_required":
            "PHASE28_CANONICAL_CLOSURE_REPAIRED__EXECUTED_FULL_18_RUN_HISTORY_NOTEBOOK_FROZEN__"
            "SCIENTIFIC_ARTIFACTS_UNCHANGED__PHASE29_ELIGIBLE_NOT_STARTED",
        "entry_gate_terminal_observed": r0.get("observed_terminal"),
        "entry_gate_pass": r0["gate_pass"],
        "seeds": SEEDS,
        "seed_set_authoritatively_frozen": r2["seed_set_authoritatively_frozen"],
        "seed_policy_sources": r2.get("sources_binding_seed_set", []),
        "seed_policy_primary_binding_source": r2.get("primary_binding_source"),
        "seed_policy_primary_binding_key": r2.get("primary_binding_key"),
        "specification_complete": spec_complete,
        "blocking_incomplete_fields": r35["blocking_incomplete_fields"],
        "active_hard_blockers": active,
        "n_active_hard_blockers": len(active),
        "terminal": terminal,
        "exit_class": exit_class,
        "success_terminal": SUCCESS_TERMINAL,
        "blocked_terminals": BLOCKED_TERMINALS,
        "phase29_execution_eligible": exit_class == "SUCCESS",
        "phase29_execution_started": False,
        "phase30_started": False,
        "notebook_created": False,
        "training_runs": 0,
        "model_forwards": 0,
        "predictions_created": 0,
        "router_holdout_reads": 0,
        "router_holdout_status": "RESERVED_UNOPENED_FOR_PHASE30",
        "val808_reads": 0,
        "test_reads": 0,
        "test_status": "LOCKED_UNTIL_PHASE39",
        "predecessor_artifact_drift": r0.get("predecessor_drift", None),
        "directive":
            "STOP. DO NOT TRAIN. DO NOT START PHASE30. "
            "DO NOT OPEN ROUTER_HOLDOUT. DO NOT OPEN TEST.",
    }
    write_json(AUD / "phase29_terminal_state.json", terminal_state)

    print("=" * 78)
    print("ACTIVE HARD BLOCKERS:", active if active else "NONE")
    print("TERMINAL:", terminal)
    print("EXIT CLASS:", exit_class)
    print("=" * 78)
    return 0 if exit_class == "SUCCESS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
