"""Phase26 pre-execution training-specification audit - PART 1 (§0-§8).

Governance only.  Produces:
  phase26_spec_entry_gate.json
  phase26_authoritative_source_binding.json
  phase26_operational_definition_audit.json
  phase26_module_trainability_contract.csv
  phase26_module_trainability_audit.json
  phase26_gradient_graph_audit.json
  phase26_data_population_contract.json
  phase26_integrated_architecture_binding.json
  phase26_policy_requirement_audit.json
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import phase26_common as C  # noqa: E402

OUT = []


def say(msg):
    print(msg, flush=True)
    OUT.append(msg)


# =============================================================== §0-§2 entry gate
def section_entry_gate():
    say("=" * 78)
    say("§0-§2  ENTRY GATE + AUTHORITATIVE SOURCE BINDING")
    say("=" * 78)

    term = C.jload(C.ROOT / "reports/audits/phase25g_terminal.json")
    pred_terminal = term.get("terminal")
    pred_ok = pred_terminal == C.PREDECESSOR_TERMINAL

    nb = C.ROOT / "notebooks/phasewise/phase_25g_controlled_validation/phase25g_integrated_controlled_evaluation.ipynb"
    nb_sha = C.sha256_file(nb)
    nb_ok = nb_sha == C.PHASE25G_NOTEBOOK_SHA

    # predecessor immutability (before)
    bindings = {rel: C.bind(rel, sha) for rel, sha in C.PREDECESSOR_BINDINGS.items()}
    all_match = all(b["matches_expected"] for b in bindings.values())

    gate = {
        "artifact": "phase26_spec_entry_gate",
        "phase": "26",
        "classification": C.CLASSIFICATION,
        "method": C.METHOD_NAME,
        "governance_only": True,
        "no_execution": True,
        "predecessor_phase": "25G",
        "predecessor_terminal_expected": C.PREDECESSOR_TERMINAL,
        "predecessor_terminal_actual": pred_terminal,
        "predecessor_terminal_ok": pred_ok,
        "phase25g_notebook_sha_expected": C.PHASE25G_NOTEBOOK_SHA,
        "phase25g_notebook_sha_actual": nb_sha,
        "phase25g_notebook_sha_ok": nb_ok,
        "predecessor_binding_count": len(bindings),
        "predecessor_all_match": all_match,
        "phase25g_status": term.get("phase25g_status"),
        "phase25_status": term.get("phase25_status"),
        "phase26_status": term.get("phase26_status"),
        "holdout_owner": term.get("holdout_owner"),
        "holdout_state": term.get("holdout_state"),
        "holdout_reads": 0,
        "val808_reads": 0,
        "test_reads": 0,
        "all_pass": bool(pred_ok and nb_ok and all_match),
    }
    C.write_json(C.AUD / "phase26_spec_entry_gate.json", gate)

    say(f"  predecessor terminal ok : {pred_ok}")
    say(f"  Phase25G notebook SHA ok: {nb_ok}  ({nb_sha[:16]}...)")
    say(f"  predecessor bindings    : {len(bindings)} bound, all_match={all_match}")
    say(f"  entry gate all_pass     : {gate['all_pass']}")
    return gate, bindings


def section_source_binding(bindings):
    say("")
    say("-" * 78)
    say("§2  AUTHORITATIVE SOURCE BINDING (definition sources)")
    say("-" * 78)
    defs = {rel: C.bind(rel) for rel in C.DEFINITION_SOURCES}
    declared = C.bind(C.DECLARED_PHASE26_SPEC)

    for rel, b in defs.items():
        say(f"  [{'OK ' if b['exists'] else 'MISS'}] {rel}")
    say(f"  [{'OK ' if declared['exists'] else 'MISS'}] {C.DECLARED_PHASE26_SPEC}"
        f"   <-- declared canonical provenance source (Phase26 README)")

    obj = {
        "artifact": "phase26_authoritative_source_binding",
        "phase": "26",
        "classification": C.CLASSIFICATION,
        "method": C.METHOD_NAME,
        "governance_only": True,
        "purpose": ("SHA-bind every repository source that could operationally define "
                    "'Full four-domain RA-MedFiLM-BARR training' BEFORE reasoning about it. "
                    "No inference from synonyms."),
        "definition_sources": defs,
        "definition_sources_n": len(defs),
        "declared_phase26_canonical_provenance_source": {
            **declared,
            "declared_by": "notebooks/phasewise/phase_26_full_four_domain_training/README.md",
            "note": ("The Phase26 README names docs/phase26_training_spec.md as the "
                     "Canonical Provenance Source, but that file DOES NOT EXIST."),
        },
        "predecessor_bindings": bindings,
        "test_reads": 0,
        "val808_reads": 0,
        "holdout_reads": 0,
        "all_pass": True,
    }
    C.write_json(C.AUD / "phase26_authoritative_source_binding.json", obj)
    return obj


# =============================================================== §1 operational definition
def section_operational_definition():
    say("")
    say("-" * 78)
    say("§1  OPERATIONAL DEFINITION OF 'Full four-domain RA-MedFiLM-BARR training'")
    say("-" * 78)

    readme = (C.NB26 / "README.md").read_text(encoding="utf-8")

    interpretations = [
        {
            "id": "A",
            "label": "JOINT_OPTIMIZATION",
            "definition": ("End-to-end joint optimization of all four domains in one "
                           "training run (a single objective back-propagating through "
                           "G, R_psi, B_phi and possibly S_omega)."),
            "authoritative_source_found": False,
            "evidence": ("No repository source states Phase26 jointly optimizes the "
                         "modules. PROJECT_MASTER_PLAN.md lists only the title "
                         "'Full Four-Domain Joint Architecture Training' with status "
                         "NOT_STARTED; no objective, gradient graph or optimizer is named."),
            "resolved": False,
        },
        {
            "id": "B",
            "label": "STAGED_FINE_TUNING",
            "definition": ("Sequential / staged fine-tuning of the assembled pipeline "
                           "(e.g. freeze G, fine-tune R_psi, then B_phi)."),
            "authoritative_source_found": False,
            "evidence": ("No source defines a staged fine-tuning schedule for Phase26."),
            "resolved": False,
        },
        {
            "id": "C",
            "label": "FINAL_REFITTING",
            "definition": ("Final refitting of already-specified components on the full "
                           "development population, using the frozen Phase24 refit rules."),
            "authoritative_source_found": False,
            "evidence": ("phase24_exact_implementation_spec.json#final_refiner names "
                         "R_psi_final.sole_regional_refiner_for = ['ROUTER_HOLDOUT "
                         "integrated evaluation','later continuity VAL evaluation',"
                         "'future Phase 26+ development unless explicitly superseded'] - "
                         "this permits reuse but does NOT state that Phase26 IS final "
                         "refitting, and defines no Phase26 objective."),
            "resolved": False,
            "partial_hint": True,
        },
        {
            "id": "D",
            "label": "ASSEMBLY_OF_TRAINED_COMPONENTS",
            "definition": ("Assembly / integration of the already-trained and frozen "
                           "components (G, R_psi, B_phi, S_omega) with no new training."),
            "authoritative_source_found": False,
            "evidence": ("All four components exist and are frozen (Phase21/25A/25D/25F), "
                         "and the Phase25G integrated evaluation already assembled them "
                         "at the artifact level. No source states Phase26 is assembly-only "
                         "or that assembly is complete."),
            "resolved": False,
            "partial_hint": True,
        },
        {
            "id": "E",
            "label": "OTHER",
            "definition": "Any other operational meaning not covered by A-D.",
            "authoritative_source_found": False,
            "evidence": "No other authoritative definition exists.",
            "resolved": False,
        },
    ]

    obj = {
        "artifact": "phase26_operational_definition_audit",
        "phase": "26",
        "classification": C.CLASSIFICATION,
        "method": C.METHOD_NAME,
        "governance_only": True,
        "question": ("What does the roadmap phrase 'Full four-domain RA-MedFiLM-BARR "
                     "training' actually mean operationally?"),
        "rule": ("Do NOT infer. Only an authoritative existing source or an explicit "
                 "later supervisor ruling may choose among the interpretations."),
        "readme_core_question_verbatim": (
            "Phase 26 executes joint multi-task training across all 4 domains on TRAIN."
        ),
        "readme_declared_provenance_source": C.DECLARED_PHASE26_SPEC,
        "readme_declared_provenance_source_exists": False,
        "readme_declared_provenance_note": (
            "The README's own Core Question sentence is an unratified stub, not an "
            "authoritative frozen specification; and its declared canonical provenance "
            "source docs/phase26_training_spec.md does not exist."
        ),
        "interpretations": interpretations,
        "n_interpretations": len(interpretations),
        "n_resolved": sum(1 for i in interpretations if i["resolved"]),
        "operational_definition_explicit": False,
        "operational_definition_verdict": "OPERATIONAL_DEFINITION_NOT_EXPLICIT",
        "blocking": True,
        "supervisor_ruling_present": False,
        "all_pass": False,
    }
    C.write_json(C.AUD / "phase26_operational_definition_audit.json", obj)

    say(f"  interpretations tested: {obj['n_interpretations']}  (A-E)")
    say(f"  resolved by authoritative source: {obj['n_resolved']}")
    say(f"  verdict: {obj['operational_definition_verdict']}  (blocking={obj['blocking']})")
    return obj


# =============================================================== §3 trainability
def section_trainability():
    say("")
    say("-" * 78)
    say("§3  MODULE TRAINABILITY CONTRACT")
    say("-" * 78)

    rows = [
        {"module_id": "G", "module_name": "GlobalMedFiLM",
         "phase_origin": "Phase21", "trained_in_phase": "Phase21",
         "frozen_artifact": "Phase21 global checkpoint (frozen baseline)",
         "param_count": "", "phase26_trainability_defined": False,
         "phase26_trainability_value": "",
         "evidence_source": "docs/ARCHITECTURE.md; PROJECT_MASTER_PLAN.md §7",
         "status": "UNDEFINED_IN_PHASE26_SPEC"},
        {"module_id": "R_psi", "module_name": "BARRRegionalRefinerV1",
         "phase_origin": "Phase25A (ROI-0.30 canonical)", "trained_in_phase": "Phase25A",
         "frozen_artifact": "checkpoints/phase25a_barr_regional_refiner_v1_1_roi030",
         "param_count": 1276401, "phase26_trainability_defined": False,
         "phase26_trainability_value": "",
         "evidence_source": "phase24_exact_implementation_spec.json#refiner; Phase25A",
         "status": "UNDEFINED_IN_PHASE26_SPEC"},
        {"module_id": "B_phi", "module_name": "BARRBenefitRouterV1",
         "phase_origin": "Phase25D", "trained_in_phase": "Phase25D",
         "frozen_artifact": "Phase25D router final checkpoint (8a412b2f...)",
         "param_count": 36801, "phase26_trainability_defined": False,
         "phase26_trainability_value": "",
         "evidence_source": "phase25d_frozen_training_spec_binding_v1_2_1.json",
         "status": "UNDEFINED_IN_PHASE26_SPEC"},
        {"module_id": "S_omega", "module_name": "BARRPostSafetyV1",
         "phase_origin": "Phase25F", "trained_in_phase": "Phase25F",
         "frozen_artifact": "checkpoints/phase25f_barr_post_safety_v1_0_seed42/final/final.pt",
         "param_count": 1217, "phase26_trainability_defined": False,
         "phase26_trainability_value": "",
         "evidence_source": "phase25f_final_freeze.json",
         "status": "UNDEFINED_IN_PHASE26_SPEC"},
        {"module_id": "FUSION", "module_name": "mask fusion rule",
         "phase_origin": "Phase24 spec / Phase25A", "trained_in_phase": "n/a (no params)",
         "frozen_artifact": "fusion rule (outside ROI: p_global; inside ROI: p_refined)",
         "param_count": 0, "phase26_trainability_defined": False,
         "phase26_trainability_value": "",
         "evidence_source": "phase24_exact_implementation_spec.json#fusion",
         "status": "UNDEFINED_IN_PHASE26_SPEC"},
    ]
    fields = ["module_id", "module_name", "phase_origin", "trained_in_phase",
              "frozen_artifact", "param_count", "phase26_trainability_defined",
              "phase26_trainability_value", "evidence_source", "status"]
    C.write_csv(C.TABLE / "phase26_module_trainability_contract.csv", rows, fields)

    obj = {
        "artifact": "phase26_module_trainability_audit",
        "phase": "26",
        "classification": C.CLASSIFICATION,
        "method": C.METHOD_NAME,
        "governance_only": True,
        "modules": [r["module_id"] for r in rows],
        "n_modules": len(rows),
        "n_trainability_defined": sum(1 for r in rows if r["phase26_trainability_defined"]),
        "modules_trained_and_frozen": ["G", "R_psi", "B_phi", "S_omega"],
        "trainable_parameter_set_defined": False,
        "frozen_parameter_set_defined": False,
        "module_init_source_defined": False,
        "note": ("Every module is trained and frozen from a prior phase.  No authoritative "
                 "source states which parameters (if any) remain trainable in Phase26, nor "
                 "whether Phase26 constructs a new model at all."),
        "verdict": "MODULE_TRAINABILITY_NOT_DEFINED_FOR_PHASE26",
        "blocking": True,
        "all_pass": False,
    }
    C.write_json(C.AUD / "phase26_module_trainability_audit.json", obj)
    say(f"  modules: {obj['modules']}")
    say(f"  trainability defined for Phase26: {obj['n_trainability_defined']}/{obj['n_modules']}")
    say(f"  verdict: {obj['verdict']}")
    return obj


# =============================================================== §4 gradient graph
def section_gradient_graph():
    say("")
    say("-" * 78)
    say("§4  GRADIENT GRAPH AUDIT")
    say("-" * 78)
    obj = {
        "artifact": "phase26_gradient_graph_audit",
        "phase": "26",
        "classification": C.CLASSIFICATION,
        "method": C.METHOD_NAME,
        "governance_only": True,
        "gradient_flow_topology_defined": False,
        "gradient_stop_points_defined": False,
        "shared_trunk_gradient_path_defined": False,
        "aux_head_gradient_path_defined": False,
        "single_difference_identity_available": False,
        "note": ("The Phase24 specification fixes the FORWARD architecture of each "
                 "component but no authoritative source defines a Phase26 gradient graph "
                 "(which tensors receive gradient, where detach/stop-gradient applies, or "
                 "how the four components are composed into one differentiable graph)."),
        "verdict": "GRADIENT_GRAPH_NOT_FROZEN",
        "blocking": True,
        "all_pass": False,
    }
    C.write_json(C.AUD / "phase26_gradient_graph_audit.json", obj)
    say(f"  verdict: {obj['verdict']}  (blocking={obj['blocking']})")
    return obj


# =============================================================== §5 data population
def section_data_population():
    say("")
    say("-" * 78)
    say("§5  DATA POPULATION CONTRACT")
    say("-" * 78)
    proto = C.jload(C.ROOT / "reports/audits/phase24_benefit_data_protocol_exact.json")
    obj = {
        "artifact": "phase26_data_population_contract",
        "phase": "26",
        "classification": C.CLASSIFICATION,
        "method": C.METHOD_NAME,
        "governance_only": True,
        "phase26_training_population_defined": False,
        "candidate_populations": {
            "ORIGINAL_TRAIN": {
                "n": C.N_TRAIN_TOTAL,
                "composition": "ROUTER_DEVELOPMENT (4957) + ROUTER_HOLDOUT (875)",
                "authorized_for_phase26_training": False,
                "reason": ("Using all 5832 would train on the 875 ROUTER_HOLDOUT samples "
                           "that are RESERVED_UNOPENED_FOR_PHASE30, contaminating the "
                           "Phase30 one-shot development validation."),
                "contamination_risk": True,
            },
            "ROUTER_DEVELOPMENT": {
                "n": C.N_ROUTER_DEVELOPMENT,
                "role": "DEV population; already used for OOF label creation in Phase25C",
                "authorized_for_phase26_training": None,
                "reason": "No authoritative source authorizes or forbids Phase26 training on DEV.",
            },
            "ROUTER_HOLDOUT": {
                "n": C.N_ROUTER_HOLDOUT,
                "role": "one-shot holdout",
                "state": "RESERVED_UNOPENED_FOR_PHASE30",
                "owner": "Phase30",
                "authorized_for_phase26_training": False,
            },
            "VAL808": {
                "n": C.N_VAL,
                "role": "continuity / secondary benchmark",
                "state": "UNOPENED",
                "authorized_for_phase26_training": False,
            },
            "TEST": {
                "n": C.N_TEST,
                "role": "untouched final test cohort",
                "state": "LOCKED_UNTIL_PHASE39",
                "authorized_for_phase26_training": False,
            },
        },
        "frozen_split_provenance": {
            "split_manifest": "reports/audits/phase24_router_split_manifest.csv",
            "split_manifest_sha256": proto.get("manifest_sha256"),
            "development_n": proto.get("development_n"),
            "holdout_n": proto.get("holdout_n"),
            "total_n": proto.get("total_n"),
        },
        "per_domain_sampling_policy_defined": False,
        "epoch_definition_defined": False,
        "holdout_exclusion_rule_defined": False,
        "phase30_holdout_contamination_risk": True,
        "verdict": "PHASE26_TRAINING_POPULATION_NOT_DEFINED",
        "blocking": True,
        "all_pass": False,
    }
    C.write_json(C.AUD / "phase26_data_population_contract.json", obj)
    say(f"  ORIGINAL_TRAIN n={C.N_TRAIN_TOTAL} = DEV {C.N_ROUTER_DEVELOPMENT} + "
        f"HOLDOUT {C.N_ROUTER_HOLDOUT}")
    say(f"  training population defined for Phase26: {obj['phase26_training_population_defined']}")
    say(f"  contamination risk (train on 5832): {obj['phase30_holdout_contamination_risk']}")
    return obj


# =============================================================== §6 architecture binding
def section_architecture_binding():
    say("")
    say("-" * 78)
    say("§6  INTEGRATED ARCHITECTURE BINDING")
    say("-" * 78)
    spec = C.jload(C.ROOT / "reports/audits/phase24_exact_implementation_spec.json")
    obj = {
        "artifact": "phase26_integrated_architecture_binding",
        "phase": "26",
        "classification": C.CLASSIFICATION,
        "method": C.METHOD_NAME,
        "governance_only": True,
        "architecture_id": spec.get("architecture_id"),
        "architecture_spec_source": "reports/audits/phase24_exact_implementation_spec.json",
        "components": {
            "G": {"role": "global segmentation (MedFiLM)", "defined": True, "origin": "Phase21"},
            "R_psi": {"role": "regional refiner", "defined": True,
                      "origin": "Phase25A", "params": spec["refiner"]["expected_parameter_count_closed_form"]},
            "B_phi": {"role": "benefit router", "defined": True,
                      "origin": "Phase25D", "params": spec["router"]["expected_parameter_count_closed_form"]},
            "S_omega": {"role": "post-safety selector", "defined": True, "origin": "Phase25F"},
            "FUSION": {"role": "mask fusion", "defined": True,
                       "rule": spec["fusion"]["rule"],
                       "segmentation_threshold": spec["fusion"]["segmentation_threshold"]},
        },
        "forward_architecture_fully_frozen": True,
        "integrated_forward_composition_defined": True,
        "phase26_training_architecture_defined": False,
        "note": ("The forward composition of the four frozen components is fully specified "
                 "and was already exercised at the artifact level in Phase25G.  However, "
                 "no authoritative source defines a Phase26 TRAINING architecture (whether "
                 "any component is re-instantiated, shared, or jointly trained)."),
        "verdict": "FORWARD_ARCHITECTURE_FROZEN__TRAINING_ARCHITECTURE_UNDEFINED",
        "blocking": True,
        "all_pass": False,
    }
    C.write_json(C.AUD / "phase26_integrated_architecture_binding.json", obj)
    say(f"  architecture_id: {obj['architecture_id']}")
    say(f"  forward architecture frozen: {obj['forward_architecture_fully_frozen']}")
    say(f"  Phase26 training architecture defined: {obj['phase26_training_architecture_defined']}")
    return obj


# =============================================================== §7 policy requirement
def section_policy_requirement():
    say("")
    say("-" * 78)
    say("§7  POLICY REQUIREMENT AUDIT")
    say("-" * 78)
    nps = C.jload(C.ROOT / "reports/audits/phase25g_no_policy_selection.json")
    obj = {
        "artifact": "phase26_policy_requirement_audit",
        "phase": "26",
        "classification": C.CLASSIFICATION,
        "method": C.METHOD_NAME,
        "governance_only": True,
        "phase25g_no_policy_selection": nps,
        "policy_choices_deferred_to": nps.get("policy_choices_deferred_to"),
        "deferral_requires": "a separate prospective ruling",
        "prospective_policy_selection_rule_present": False,
        "supervisor_ruling_for_phase26_policy_present": False,
        "lambda_selected": False,
        "budget_selected": False,
        "policy_selected": False,
        "note": ("Phase25G deliberately selected no policy and deferred the choice to "
                 "Phase26 '(requires a separate prospective ruling)'.  No such prospective "
                 "ruling exists in the repository.  Phase26 therefore has no prospective "
                 "rule by which a lambda/budget policy could be selected, and the audit "
                 "must NOT invent one."),
        "verdict": "NO_PROSPECTIVE_POLICY_SELECTION_RULE",
        "blocking": True,
        "all_pass": False,
    }
    C.write_json(C.AUD / "phase26_policy_requirement_audit.json", obj)
    say(f"  deferred_to: {obj['policy_choices_deferred_to']}")
    say(f"  prospective rule present: {obj['prospective_policy_selection_rule_present']}")
    say(f"  verdict: {obj['verdict']}")
    return obj


def main():
    gate, bindings = section_entry_gate()
    section_source_binding(bindings)
    od = section_operational_definition()
    tr = section_trainability()
    gg = section_gradient_graph()
    dp = section_data_population()
    ab = section_architecture_binding()
    pr = section_policy_requirement()

    say("")
    say("=" * 78)
    say("PART 1 SUMMARY")
    say("=" * 78)
    say(f"  entry_gate.all_pass                 : {gate['all_pass']}")
    say(f"  operational_definition_explicit     : {od['operational_definition_explicit']}")
    say(f"  module_trainability_defined         : {tr['n_trainability_defined']}/{tr['n_modules']}")
    say(f"  gradient_graph_defined              : {gg['gradient_flow_topology_defined']}")
    say(f"  training_population_defined         : {dp['phase26_training_population_defined']}")
    say(f"  phase26_training_architecture_def   : {ab['phase26_training_architecture_defined']}")
    say(f"  prospective_policy_rule_present     : {pr['prospective_policy_selection_rule_present']}")
    say(f"  blocking conditions (part 1)        : "
        f"{sum(1 for x in (od,tr,gg,dp,ab,pr) if x['blocking'])}")


if __name__ == "__main__":
    main()
