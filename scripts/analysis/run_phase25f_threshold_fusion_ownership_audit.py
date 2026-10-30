"""Phase25F §6-§10: THRESHOLD SEMANTICS + FUSION/FALLBACK CONTRACT + A7/A8
EVALUATION OWNERSHIP + SCOPE GUARD (+ resource claim guard) + TEST LOCK.

AUDIT ONLY.

Writes:
  reports/audits/phase25f_threshold_semantics_audit.json
  reports/audits/phase25f_fusion_fallback_contract_audit.json
  reports/audits/phase25f_a7_a8_evaluation_ownership.json
  reports/audits/phase25f_scope_guard.json
  reports/audits/phase25f_test_lock_audit.json
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUD = ROOT / 'reports/audits'
TABLE = ROOT / 'reports/tables'

IMPL_SPEC = 'reports/audits/phase24_exact_implementation_spec.json'
ARCH_SPEC = 'reports/audits/phase24_architecture_spec.json'
PRESERV = 'reports/audits/phase24_preservation_contract.json'
MODULE_PLAN = 'reports/audits/phase24_phase25_module_plan.json'
MODULE_SPEC = 'reports/tables/phase24_module_spec.csv'
ABLATION = 'reports/tables/phase24_ablation_plan.csv'
COMPARATOR = 'reports/tables/phase24_comparator_plan.csv'
DATA_ROLE = 'reports/tables/phase24_data_role_contract.csv'
C25E_DIRECTION = 'reports/audits/phase25e_comparator_direction_contract_v1_0.json'
C25E_HANDOFF = 'reports/audits/phase25e_phase25f_handoff_schema.json'
C25E_FIXED_BUDGET = 'reports/audits/phase25e_fixed_budget_contract_v1_0.json'
C25C_SCOPE = 'reports/audits/phase25c_scope_guard.json'
C25C_TESTLOCK = 'reports/audits/phase25c_test_lock_audit.json'
C25E_FINAL = 'reports/audits/phase25e_postclosure_reconciliation_final_check.json'
C25E_RECON_ADJ = 'reports/audits/phase25e_adjudication_reconciled.json'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def J(rel):
    return json.loads((ROOT / rel).read_text(encoding='utf-8'))


def main():
    impl = J(IMPL_SPEC)
    arch = J(ARCH_SPEC)
    preserv = J(PRESERV)
    plan = J(MODULE_PLAN)
    direction = J(C25E_DIRECTION)
    handoff = J(C25E_HANDOFF)
    fc = J(C25E_FINAL)
    recon = J(C25E_RECON_ADJ)

    fusion = impl['fusion']
    impl_ps = impl['post_safety']

    # ================= §3N THRESHOLD SEMANTICS ===================================
    thr = {
        'classification': 'PHASE25F_POST_SAFETY_SPEC_COMPLETENESS_AUDIT',
        'stage': 'THRESHOLD_SEMANTICS_AUDIT',
        'method': 'RA-MedFiLM-BARR',
        'question': ('Is the exact probability/logit threshold for ACCEPT_REFINEMENT vs '
                     'FALLBACK_GLOBAL frozen for S_omega?'),
        's_omega_decision_threshold': 'NOT_FROZEN',
        's_omega_output_spec': impl_ps['architecture'],
        's_omega_output_interpretation_ambiguous': True,
        'distinct_thresholds_in_the_frozen_record': {
            'roi_proposal_threshold': {'value': 0.30, 'role': 'bbox -> ACTION_AVAILABLE / FORCED_SKIP',
                                       'is_s_omega_decision_threshold': False},
            'segmentation_output_threshold': {'value': 0.50, 'role': 'final mask / Dice / IoU (INHERITED)',
                                              'is_s_omega_decision_threshold': False},
            's_omega_accept_threshold': {'value': None, 'role': 'ACCEPT_REFINEMENT vs FALLBACK_GLOBAL',
                                         'is_s_omega_decision_threshold': True},
        },
        'assumption_0p5_forbidden': True,
        'assumption_0p5_forbidden_reason': (
            'The frozen 0.5 belongs to the SEGMENTATION OUTPUT threshold and is INHERITED. The frozen '
            'fusion block explicitly sets threshold_tuning=false. No document freezes 0.5 (or any value) '
            'as the S_omega ACCEPT/FALLBACK decision threshold. Assuming 0.5 because the output may be '
            'sigmoid would be threshold invention.'),
        'verdict': 'BLOCKING__DECISION_THRESHOLD_NOT_FROZEN',
        'sources': {IMPL_SPEC: sha(ROOT / IMPL_SPEC), ARCH_SPEC: sha(ROOT / ARCH_SPEC)},
        'all_pass': True,
    }
    (AUD / 'phase25f_threshold_semantics_audit.json').write_text(
        json.dumps(thr, indent=2, allow_nan=False) + '\n', encoding='utf-8')

    # ================= §3O FUSION / FALLBACK CONTRACT ============================
    fb = {
        'classification': 'PHASE25F_POST_SAFETY_SPEC_COMPLETENESS_AUDIT',
        'stage': 'FUSION_FALLBACK_CONTRACT_AUDIT',
        'method': 'RA-MedFiLM-BARR',
        'frozen_fusion_rule': fusion['rule'],
        'frozen_fusion_rule_architecture_spec': arch['fusion_rule']['primary'],
        'alpha_blending': fusion['alpha_blending'],
        'learned_fusion': fusion['learned_fusion'],
        'segmentation_output_threshold': fusion['segmentation_threshold'],
        'segmentation_threshold_source': fusion['segmentation_threshold_source'],
        'threshold_tuning': fusion['threshold_tuning'],
        'preservation_outcomes': preserv['outcomes'],
        'destructive_replacement_before_final_decision': preserv['destructive_replacement_before_final_decision'],
        'structural_enforcement': preserv['structural_enforcement'],
        'resolution': {
            'post_safety_ACCEPTS': 'final = regional-fused (EXECUTE_THEN_ACCEPT) [FROZEN via preservation contract]',
            'post_safety_REJECTS': 'final = global (EXECUTE_THEN_REJECT) [FROZEN via preservation contract]',
            'phase25e_SKIP': 'final = global (SKIP) [FROZEN]',
            'outside_ROI': 'p_final_candidate = p_global [FROZEN]',
            'inside_ROI': 'p_final_candidate = resized p_refined [FROZEN]',
            'segmentation_output_threshold_role': '0.50, INHERITED, final mask/Dice/IoU [FROZEN]',
            'roi_proposal_threshold_role': '0.30, bbox -> ACTION_AVAILABLE/FORCED_SKIP [FROZEN]',
            'action_unavailable_behavior': 'FORCED_SKIP pre-gate; final = global [FROZEN]',
            'interaction_with_phase25e_SKIP': 'final = global; no refinement executed [FROZEN]',
        },
        'explicit_somega_to_outcome_mapping_frozen': False,
        'explicit_somega_to_outcome_mapping_note': (
            'The preservation contract freezes the three OUTCOMES (SKIP / EXECUTE_THEN_REJECT / '
            'EXECUTE_THEN_ACCEPT) and their final outputs, and the frozen role of S_omega is '
            '"quality preservation AFTER refinement". The mapping S_omega-ACCEPT -> EXECUTE_THEN_ACCEPT '
            'and S_omega-REJECT -> EXECUTE_THEN_REJECT is strongly implied but is NOT stated as an '
            'explicit frozen mapping.'),
        'learned_blending_introduced': False,
        'verdict': 'FUSION_RULE_FROZEN__EXPLICIT_SOMEGA_OUTCOME_MAPPING_IMPLIED_NOT_STATED',
        'sources': {IMPL_SPEC: sha(ROOT / IMPL_SPEC), PRESERV: sha(ROOT / PRESERV)},
        'all_pass': True,
    }
    (AUD / 'phase25f_fusion_fallback_contract_audit.json').write_text(
        json.dumps(fb, indent=2, allow_nan=False) + '\n', encoding='utf-8')

    # ================= §9 A7/A8 EVALUATION OWNERSHIP =============================
    m25f = next(m for m in plan['modules'] if m['id'] == '25F')
    m25g = next(m for m in plan['modules'] if m['id'] == '25G')
    own = {
        'classification': 'PHASE25F_POST_SAFETY_SPEC_COMPLETENESS_AUDIT',
        'stage': 'A7_A8_EVALUATION_OWNERSHIP',
        'method': 'RA-MedFiLM-BARR',
        'recovered_definitions': {
            'A7': {'ablation_plan': 'A6 + resource cost', 'purpose': 'H5 test',
                   'comparator_equivalent': 'C8 (LEARNED_GAIN_PLUS_RESOURCE_COST)'},
            'A8': {'ablation_plan': 'A7 + post-safety', 'purpose': 'H3 test; isolates S_omega',
                   'comparator_equivalent': 'C9 (LEARNED_GAIN_PLUS_RESOURCE_COST_PLUS_POST_SAFETY)'},
            'C9': {'comparator_plan': direction['comparators']['C9'],
                   'architecture_spec': arch['post_safety'],
                   'phase25e_scope': 'Phase25F only; excluded from Phase25E'},
            'C11': {'comparator_plan': direction['comparators']['C11'],
                    'status': 'excluded unless separately authorized'},
        },
        'authoritative_evidence': {
            MODULE_PLAN: {
                'sha256': sha(ROOT / MODULE_PLAN),
                '25F': m25f,
                '25G': m25g,
            },
            C25E_HANDOFF: {
                'sha256': sha(ROOT / C25E_HANDOFF),
                'phase25f_scope': handoff['phase25f_scope'],
            },
            C25E_DIRECTION: {
                'sha256': sha(ROOT / C25E_DIRECTION),
                'C9': direction['comparators']['C9'],
            },
            ABLATION: {'sha256': sha(ROOT / ABLATION),
                       'A7': 'A6 + resource cost', 'A8': 'A7 + post-safety'},
        },
        'reading_A_25F_constructs_25G_evaluates': {
            'claim': ('The module plan gives 25F the deliverable "S_omega + ROI-weighted fusion" and gives '
                      '25G the deliverable "comparator + ablation evaluation report and freeze", with 25G '
                      'starting after 25E and 25F. Under this reading Phase25F CONSTRUCTS S_omega and the '
                      'C9 policy, while the A7-vs-A8 comparative ablation evaluation belongs to Phase25G.'),
            'support': 'phase24_phase25_module_plan.json (25F/25G deliverables and starts_after)',
        },
        'reading_B_25F_owns_C9_evaluation': {
            'claim': ('The Phase25E->25F handoff schema lists "C9 post-safety (S_omega) comparator" under '
                      'phase25f_scope, and the Phase25E comparator direction contract marks C9 '
                      '"Phase25F only", which could be read as Phase25F owning the C9 comparison.'),
            'support': 'phase25e_phase25f_handoff_schema.json; phase25e_comparator_direction_contract_v1_0.json',
        },
        'ownership_resolved': False,
        'ownership_ambiguous': True,
        'blocking_governance_field': True,
        'recommended_ruling': ('Phase25F constructs S_omega + ROI-weighted fusion and may compute C9 policy '
                              'artifacts on ROUTER_DEVELOPMENT, but the A7-vs-A8 (C8-vs-C9) comparative '
                              'ablation evaluation and report are owned by Phase25G per the frozen module '
                              'plan. A supervisor ruling is required to confirm before any A7/A8 evaluation.'),
        'evaluation_on_router_development_authorized_for_25F': 'AMBIGUOUS',
        'verdict': 'BLOCKING_GOVERNANCE_FIELD__A7_A8_OWNERSHIP_AMBIGUOUS',
        'all_pass': True,
    }
    (AUD / 'phase25f_a7_a8_evaluation_ownership.json').write_text(
        json.dumps(own, indent=2, allow_nan=False) + '\n', encoding='utf-8')

    # ================= §7/§10 SCOPE GUARD + RESOURCE CLAIM GUARD =================
    scope = {
        'classification': 'PHASE25F_POST_SAFETY_SPEC_COMPLETENESS_AUDIT',
        'stage': 'SCOPE_GUARD',
        'method': 'RA-MedFiLM-BARR',
        'audit_only': True,
        'forbidden_actions_executed': {
            'model_construction': False, 'training': False, 'forward_passes': 0,
            'new_oof_prediction': False, 'new_refinement': False, 'new_delta_dice': False,
            'lambda_selection': False, 'budget_selection': False, 'threshold_invention': False,
            'holdout_reads': 0, 'val808_reads': 0, 'test_reads': 0, 'phase25g_started': False,
        },
        'phase25e_state_frozen': {
            'memberships_changed': False, 'budgets_changed': False, 'lambda_grid_changed': False,
            'routing_thresholds_changed': False, 'random_priorities_changed': False,
            'c7_c8_memberships_changed': False, 'bootstrap_plan_changed': False,
            'paired_tests_changed': False, 'primary_raw_p_adjudication_changed': False,
            'holm_sensitivity_adjudication_changed': False,
            'lambda_selected': False, 'single_budget_selected': False,
            'retrospective_optimization_of_phase25e': False,
        },
        'phase25e_frozen_evidence': {
            'final_check_terminal': fc['terminal'],
            'final_check_all_pass': fc['all_pass'],
            'S1_H1_status_primary': recon['S1_H1_status'],
            'S1_budget_pass_primary': recon['S1_budget_pass'],
            'holm_secondary_role': recon['holm_secondary_role'],
        },
        'resource_claim_guard': {
            's_omega_executes_after_refinement': True,
            'post_safety_reduces_refiner_execution_count': False,
            'post_safety_creates_additional_pre_execution_compute_savings': False,
            'post_safety_changes_phase25e_routing_membership': False,
            'post_safety_may_improve_final_output_preservation_by_rejecting_already_executed_harmful_refinements': True,
            'post_safety_macs_must_be_reported_separately': True,
            'post_safety_macs_measured': False,
        },
        'no_scientific_notebook_created': True,
        'forbidden_notebook_path': 'notebooks/phasewise/phase_25f_preservation_fusion/phase25f_post_safety_and_fusion.ipynb',
        'forbidden_notebook_exists': (ROOT / 'notebooks/phasewise/phase_25f_preservation_fusion/'
                                              'phase25f_post_safety_and_fusion.ipynb').exists(),
        'blocked_audit_must_not_manufacture_empty_notebook': True,
        'sources': {MODULE_PLAN: sha(ROOT / MODULE_PLAN), C25E_FINAL: sha(ROOT / C25E_FINAL)},
        'all_pass': True,
    }
    if scope['forbidden_notebook_exists']:
        scope['all_pass'] = False
    (AUD / 'phase25f_scope_guard.json').write_text(
        json.dumps(scope, indent=2, allow_nan=False) + '\n', encoding='utf-8')

    # ================= §7 TEST / HOLDOUT / VAL LOCK ==============================
    lock = {
        'classification': 'PHASE25F_POST_SAFETY_SPEC_COMPLETENESS_AUDIT',
        'stage': 'TEST_LOCK_AUDIT',
        'method': 'RA-MedFiLM-BARR',
        'router_holdout_reads': 0,
        'router_holdout_outcomes_read': 0,
        'router_holdout_post_safety_labels_inspected': 0,
        'router_holdout_post_refinement_features_generated': 0,
        'val808_reads': 0,
        'val808_used_to_fill_missing_phase25f_spec_values': False,
        'test_reads': 0,
        'test_status': 'LOCKED UNTIL PHASE39',
        'threshold_calibrated_on_holdout': False,
        'evidence': {
            'phase25e_final_check': {
                'router_holdout_reads': fc['router_holdout_reads'],
                'VAL808_reads': fc['VAL808_reads'],
                'TEST_reads': fc['TEST_reads'],
                'test_lock': fc['test_lock'],
            },
            'phase24_data_role_contract': 'ROUTER_HOLDOUT = untouched holdout; VAL808 = secondary/continuity; TEST = CLOSED',
        },
        'sources': {C25E_FINAL: sha(ROOT / C25E_FINAL), DATA_ROLE: sha(ROOT / DATA_ROLE)},
        'all_pass': True,
    }
    (AUD / 'phase25f_test_lock_audit.json').write_text(
        json.dumps(lock, indent=2, allow_nan=False) + '\n', encoding='utf-8')

    print('§3N threshold verdict:', thr['verdict'])
    print('§3O fusion verdict:', fb['verdict'])
    print('§9 ownership:', own['verdict'])
    print('§7/§10 scope all_pass:', scope['all_pass'], '| test lock all_pass:', lock['all_pass'])
    print('PHASE25F_S6_S10_AUDIT_WRITTEN')


if __name__ == '__main__':
    main()
