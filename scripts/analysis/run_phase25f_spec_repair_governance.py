"""Phase 25F — POST-SAFETY SPECIFICATION REPAIR  §1 / §2 / §3.

§1 classification + specification revision + predecessor-preservation record.
§2 carry the frozen S_omega role / novelty boundary forward unchanged.
§3 supervisor ruling F1 — Phase25F / Phase25G ownership resolution.

No model construction / training / forward pass / refinement / DeltaDice.

Outputs:
  reports/audits/phase25f_spec_repair_governance.json
  reports/audits/phase25f_a7_a8_ownership_ruling_v1_0.json
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))
import phase25f_spec_repair_common as C  # noqa: E402


def main() -> int:
    arch_spec = C.jload(C.AUD / "phase24_architecture_spec.json")
    exact = C.jload(C.AUD / "phase24_exact_implementation_spec.json")
    pres = C.jload(C.AUD / "phase24_preservation_contract.json")
    module_plan = C.jload(C.AUD / "phase24_phase25_module_plan.json")
    handoff = C.jload(C.AUD / "phase25e_phase25f_handoff_schema.json")
    comparator = C.jload(C.AUD / "phase25e_comparator_direction_contract_v1_0.json")
    entry = C.jload(C.AUD / "phase25f_spec_repair_entry_gate.json")

    ps_arch = arch_spec.get("post_safety", {})
    ps_exact = exact.get("post_safety", {})

    # ---------------- §1 governance ---------------------------------------- #
    gov = {
        "artifact": "phase25f_spec_repair_governance",
        "phase": "25F",
        "stage": "SPEC_REPAIR_GOVERNANCE",
        "method": C.METHOD,
        "classification": C.CLASSIFICATION,
        "specification_revision": C.REVISION,
        "supersedes_only_incompleteness": True,
        "science_results_changed": False,
        "architecture_executed": False,
        "Phase25A_changed": False,
        "Phase25B_changed": False,
        "Phase25C_changed": False,
        "Phase25D_changed": False,
        "Phase25E_changed": False,
        "blocked_attempt_provenance": {
            "status": "BLOCKED_ATTEMPT_PROVENANCE",
            "terminal": C.PHASE25F_BLOCKED_TERMINAL,
            "blocking_field_count": C.EXPECTED_BLOCKING_FIELD_COUNT,
            "hard_stop_triggered_count": C.EXPECTED_HARD_STOP_COUNT,
            "overwritten": False,
            "deleted": False,
            "artifact_count": entry.get("blocked_attempt_artifact_count"),
            "artifact_sha256": entry.get("blocked_attempt_artifacts"),
            "note": "The first blocked Phase25F attempt is preserved verbatim as provenance; "
                    "its audits are neither overwritten nor deleted.",
        },
        "predecessor_bindings": {
            "phase24_architecture_spec": C.bind(C.AUD / "phase24_architecture_spec.json"),
            "phase24_exact_implementation_spec": C.bind(C.AUD / "phase24_exact_implementation_spec.json"),
            "phase24_preservation_contract": C.bind(C.AUD / "phase24_preservation_contract.json"),
            "phase24_phase25_module_plan": C.bind(C.AUD / "phase24_phase25_module_plan.json"),
            "phase25e_phase25f_handoff_schema": C.bind(C.AUD / "phase25e_phase25f_handoff_schema.json"),
            "phase25e_comparator_direction_contract_v1_0": C.bind(
                C.AUD / "phase25e_comparator_direction_contract_v1_0.json"),
        },
        "no_execution_invariants": entry.get("no_execution_invariants"),
        "entry_gate_all_pass": entry.get("all_pass"),
    }
    C.jdump(gov, C.AUD / "phase25f_spec_repair_governance.json")

    # ---------------- §2 role / novelty boundary (unchanged) ---------------- #
    role = {
        "artifact": "phase25f_role_and_novelty_boundary_v1_0",
        "phase": "25F",
        "stage": "ROLE_NOVELTY_BOUNDARY_CARRIED_FORWARD",
        "method": C.METHOD,
        "specification_revision": C.REVISION,
        "symbol": "S_omega",
        "class_name": "BARRPostSafetyV1",
        "role": "POST-REFINEMENT preservation / safety selector",
        "classification": "CONTROLLED_CORE_EXTENSION",
        "deployment_inputs_gt_free": True,
        "post_safety_saves_compute": False,
        "novelty_claimed": False,
        "jfs_adjacency": True,
        "changed_by_this_repair": False,
        "verbatim_source_architecture_spec": ps_arch,
        "verbatim_source_exact_impl": ps_exact,
        "mandatory_conceptual_comparison": {
            "A7": "pre-execution router/resource gate WITHOUT post-safety",
            "A8": "matched routed policy PLUS post-safety/fallback",
        },
        "must_never_be_described_as": [
            "the compute-saving mechanism",
            "the novelty-bearing component",
            "a causal estimator",
            "a certified safety mechanism",
        ],
        "phase25e_remains_owner_of": "conditional execution savings",
        "forbidden_tokens_guard": {
            "forbidden": ["counterfactual", "certified", "causal", "guaranteed"],
            "applied_to": "all Phase25F repair artifacts and future Phase25F documents",
        },
        "preservation_contract_bound": {
            "outcomes": pres.get("outcomes"),
            "margin": (pres.get("non_inferiority") or {}).get("margin"),
            "destructive_replacement_before_final_decision":
                pres.get("destructive_replacement_before_final_decision"),
        },
        "all_pass": True,
    }
    C.jdump(role, C.AUD / "phase25f_role_and_novelty_boundary_v1_0.json")

    # ---------------- §3 A7/A8 ownership ruling ----------------------------- #
    ruling = {
        "artifact": "phase25f_a7_a8_ownership_ruling_v1_0",
        "phase": "25F",
        "stage": "SUPERVISOR_RULING_F1_PHASE25F_PHASE25G_OWNERSHIP",
        "method": C.METHOD,
        "specification_revision": C.REVISION,
        "ruling_id": "F1",
        "resolves": "documented A7/A8 evaluation-ownership ambiguity",
        "phase25f_owns": [
            "leakage-safe S_omega feature construction",
            "S_omega cross-validated training",
            "OOF S_omega probabilities / decisions",
            "final S_omega refit",
            "final S_omega checkpoint",
            "deterministic fusion/fallback implementation",
            "construction of the C9 decision artifact on ROUTER_DEVELOPMENT",
            "classifier-level descriptive metrics for S_omega itself",
        ],
        "phase25f_does_not_own": [
            "A7-vs-A8 integrated segmentation-performance comparison",
            "C8-vs-C9 system-performance comparison",
            "post-safety preservation adjudication",
            "final comparator ranking",
            "integrated ablation reporting",
        ],
        "phase25g_owns": [
            "A7 vs A8",
            "C8 vs C9",
            "integrated preservation evaluation",
            "comparator + ablation report",
            "controlled development freeze",
        ],
        "phase25f_may_construct_C9_artifacts": True,
        "phase25f_may_evaluate_A7_vs_A8_system_performance": False,
        "hierarchy_basis": "Phase24 module-plan hierarchy",
        "module_plan_binding": {
            m.get("id"): {"name": m.get("name"), "deliverable": m.get("deliverable"),
                          "starts_after": m.get("starts_after")}
            for m in (module_plan.get("modules") or []) if m.get("id") in ("25F", "25G")
        },
        "handoff_schema_scope": handoff.get("phase25f_scope"),
        "comparator_direction_contract": {
            "C9": (comparator.get("comparators") or {}).get("C9"),
        },
        "a7_a8_evaluation_performed": False,
        "c8_c9_comparison_performed": False,
        "all_pass": True,
    }
    C.jdump(ruling, C.AUD / "phase25f_a7_a8_ownership_ruling_v1_0.json")

    print("governance + role + ownership ruling written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
