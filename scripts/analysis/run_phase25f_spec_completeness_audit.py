"""Phase25F §2-§5: ROLE / NOVELTY BOUNDARY + EXECUTION-CRITICAL SPEC AUDIT +
TRAINING-DATA SOURCE AUDIT + LEAKAGE CONTRACT + COMPLETENESS TABLE.

AUDIT ONLY. Reads frozen artifacts; constructs nothing; trains nothing.

Writes:
  reports/audits/phase25f_role_and_novelty_boundary.json
  reports/audits/phase25f_post_safety_spec_binding.json
  reports/audits/phase25f_training_data_source_audit.json
  reports/audits/phase25f_leakage_safety_audit.json
  reports/tables/phase25f_specification_completeness.csv
  reports/tables/phase25f_training_data_leakage_contract.csv
  reports/tables/phase25f_post_safety_input_contract.csv
"""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUD = ROOT / 'reports/audits'
TABLE = ROOT / 'reports/tables'

ARCH_SPEC = 'reports/audits/phase24_architecture_spec.json'
IMPL_SPEC = 'reports/audits/phase24_exact_implementation_spec.json'
PRESERV = 'reports/audits/phase24_preservation_contract.json'
MODULE_PLAN = 'reports/audits/phase24_phase25_module_plan.json'
NOVELTY = 'reports/audits/phase24_novelty_boundary.json'
ABLATION = 'reports/tables/phase24_ablation_plan.csv'
COMPARATOR = 'reports/tables/phase24_comparator_plan.csv'
MODULE_SPEC = 'reports/tables/phase24_module_spec.csv'
DATA_ROLE = 'reports/tables/phase24_data_role_contract.csv'
CROSSFIT_LEAK = 'reports/audits/phase25c_crossfit_leakage_audit.json'
C25C_INFER = 'reports/audits/phase25c_refiner_inference_execution_binding.json'
C25C_CACHE = 'reports/audits/phase25c_global_cache_binding.json'
C25C_FULLFIELD = 'reports/audits/phase25c_fullfield_reconstruction_audit.json'
C25C_HANDOFF = 'reports/audits/phase25c_phase25d_handoff_schema.json'
C25E_DIRECTION = 'reports/audits/phase25e_comparator_direction_contract_v1_0.json'
C25E_HANDOFF = 'reports/audits/phase25e_phase25f_handoff_schema.json'
LABEL_MANIFEST = 'data_cache/phase25c_barr_oof_paired_gain_labels_v1_2/label_manifest.json'
P25B_GROUPS = 'data_cache/phase25b_barr_pre_refinement_features_v1_2/feature_group_offsets.json'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def J(rel):
    return json.loads((ROOT / rel).read_text(encoding='utf-8'))


def main():
    arch = J(ARCH_SPEC)
    impl = J(IMPL_SPEC)
    preserv = J(PRESERV)
    module_plan = J(MODULE_PLAN)
    novelty = J(NOVELTY)
    crossfit = J(CROSSFIT_LEAK)
    infer = J(C25C_INFER)
    cache = J(C25C_CACHE)
    fullfield = J(C25C_FULLFIELD)
    c25c_handoff = J(C25C_HANDOFF)
    direction = J(C25E_DIRECTION)
    handoff = J(C25E_HANDOFF)
    label_manifest = J(LABEL_MANIFEST)
    p25b_groups = J(P25B_GROUPS)

    arch_ps = arch['post_safety']
    impl_ps = impl['post_safety']
    fusion = impl['fusion']
    arch_fusion = arch['fusion_rule']

    # ================= §2 ROLE / NOVELTY BOUNDARY ================================
    module_25f = next(m for m in module_plan['modules'] if m['id'] == '25F')
    module_25g = next(m for m in module_plan['modules'] if m['id'] == '25G')
    module_25e = next(m for m in module_plan['modules'] if m['id'] == '25E')

    role = {
        'classification': 'PHASE25F_POST_SAFETY_SPEC_COMPLETENESS_AUDIT',
        'stage': 'ROLE_AND_NOVELTY_BOUNDARY',
        'method': 'RA-MedFiLM-BARR',
        'frozen_role': 'POST-REFINEMENT preservation / safety selector (S_omega) + ROI-weighted fusion',
        'is_pre_execution_compute_saving_router': False,
        'executes_after_regional_refinement': True,
        'post_safety_saves_compute': impl_ps['saves_compute'],
        'post_safety_saves_compute_expected': False,
        'pre_execution_compute_saving_claim_for_Somega': False,
        'is_source_of_phase25e_conditional_compute_savings': False,
        'phase25e_compute_savings_source': ('Phase25E conditional-compute savings come from the PRE-execution '
                                            'resource gate (C7/C8), never from S_omega.'),
        'frozen_statements': {
            'phase24_architecture_spec.post_safety.role': arch_ps['role'],
            'phase24_architecture_spec.post_safety.saves_compute': arch_ps['saves_compute'],
            'phase24_architecture_spec.post_safety.importance': arch_ps['importance'],
            'phase24_exact_implementation_spec.post_safety.primary_evaluation_excludes_it':
                impl_ps['primary_evaluation_excludes_it'],
            'phase24_exact_implementation_spec.post_safety.primary_evaluation': impl_ps['primary_evaluation'],
            'phase24_exact_implementation_spec.post_safety.included_in': impl_ps['included_in'],
        },
        'post_safety_novelty_claimed': arch_ps['novelty_claimed'],
        'post_safety_novelty_claimed_required': False,
        'jfs_adjacent_component': True,
        'jfs_boundary_statement': arch_ps['importance'],
        'novelty_bearing_component': novelty['novelty_bearing_component'],
        'non_novel_preserved_components_includes_Somega': any('S_omega' in s for s in
                                                              novelty['non_novel_preserved_components']),
        'mandatory_controlled_comparison': {
            'A7': 'pre-execution router / resource gate WITHOUT post-safety',
            'A8': 'the matched routed policy PLUS post-safety / fallback',
            'frozen_A7_definition': 'A6 + resource cost',
            'frozen_A8_definition': 'A7 + post-safety',
            'frozen_A8_purpose': 'H3 test; isolates S_omega',
            'comparator_equivalent': {'A7': 'C8', 'A8': 'C9'},
            'comparator_plan_C8': 'LEARNED_GAIN_PLUS_RESOURCE_COST (tests H5)',
            'comparator_plan_C9': 'LEARNED_GAIN_PLUS_RESOURCE_COST_PLUS_POST_SAFETY (tests H3)',
        },
        'module_plan_25F': module_25f,
        'module_plan_25G': module_25g,
        'module_plan_25E': module_25e,
        'authoritative_sources': {
            ARCH_SPEC: sha(ROOT / ARCH_SPEC), IMPL_SPEC: sha(ROOT / IMPL_SPEC),
            NOVELTY: sha(ROOT / NOVELTY), MODULE_PLAN: sha(ROOT / MODULE_PLAN),
            ABLATION: sha(ROOT / ABLATION), COMPARATOR: sha(ROOT / COMPARATOR),
        },
        'required_flags': {
            'post_safety_novelty_claimed': False,
            'JFS_adjacent_component': True,
            'pre_execution_compute_saving_claim_for_Somega': False,
        },
        'failures': [],
        'all_pass': (arch_ps['novelty_claimed'] is False
                     and arch_ps['saves_compute'] is False
                     and impl_ps['saves_compute'] is False),
    }
    if not role['all_pass']:
        role['failures'].append('ROLE_FLAG_MISMATCH')
    (AUD / 'phase25f_role_and_novelty_boundary.json').write_text(
        json.dumps(role, indent=2, allow_nan=False) + '\n', encoding='utf-8')

    # ================= §3 POST-SAFETY SPEC BINDING ===============================
    binding = {
        'classification': 'PHASE25F_POST_SAFETY_SPEC_COMPLETENESS_AUDIT',
        'stage': 'POST_SAFETY_SPEC_BINDING',
        'method': 'RA-MedFiLM-BARR',
        'symbol': 'S_omega',
        'class_name_frozen': impl_ps['name'],
        'verbatim_frozen_post_safety_block_exact_impl': impl_ps,
        'verbatim_frozen_post_safety_block_architecture_spec': arch_ps,
        'verbatim_frozen_fusion_block': fusion,
        'verbatim_frozen_fusion_rule_architecture_spec': arch_fusion,
        'verbatim_frozen_preservation_contract': preserv,
        'sources': {IMPL_SPEC: sha(ROOT / IMPL_SPEC), ARCH_SPEC: sha(ROOT / ARCH_SPEC),
                    PRESERV: sha(ROOT / PRESERV)},
        'field_status': {},   # filled below
        'all_pass': True,
    }

    # ================= §5 SPECIFICATION COMPLETENESS =============================
    # field, frozen_value, source, complete, blocking_if_missing, notes
    NA = 'NOT_FROZEN'
    rows = []

    def add(field, value, source, complete, blocking, notes):
        rows.append({
            'field': field,
            'frozen_value': value,
            'authoritative_source': source,
            'source_sha': (sha(ROOT / source) if (ROOT / source).exists() else ''),
            'complete': bool(complete),
            'blocking_if_missing': bool(blocking),
            'notes': notes,
        })

    # A. model / architecture
    add('architecture', impl_ps['architecture'], IMPL_SPEC, False, True,
        'Frozen as "input -> 32 -> 16 -> 1 (sigmoid/logit)": hidden widths 32/16 and a single '
        'scalar output are given, but the INPUT dimensionality is not frozen, so the layer shapes '
        'are not determined. Output activation is written "sigmoid/logit" - explicitly ambiguous.')
    add('input_vector', NA, IMPL_SPEC, False, True,
        'Only "feature_family_examples" (7 example families) are listed. No exact input vector.')
    add('feature_order', NA, IMPL_SPEC, False, True, 'No ordering of input features is frozen.')
    add('feature_equations', NA, IMPL_SPEC, False, True,
        'No formula for any post-refinement feature (e.g. "foreground-area change", '
        '"component-count change", "boundary-size change") is frozen.')
    add('activation_functions', NA, IMPL_SPEC, False, True,
        'Hidden activation is not stated (router/refiner use SiLU, but that is NOT frozen for S_omega).')
    add('normalization_layers', NA, IMPL_SPEC, False, True, 'No LayerNorm/BatchNorm/None is frozen for S_omega.')
    add('dropout', NA, IMPL_SPEC, False, True, 'No dropout probability is frozen for S_omega.')
    add('output_dimension', '1 (single scalar)', IMPL_SPEC, False, True,
        'Output dimension 1 is implied by "-> 1", but the output interpretation (sigmoid probability '
        'vs raw logit) is ambiguous ("sigmoid/logit").')
    add('output_interpretation', 'sigmoid/logit (AMBIGUOUS)', IMPL_SPEC, False, True,
        'The frozen text writes "sigmoid/logit"; it does not resolve which.')
    add('parameter_count_convention', NA, IMPL_SPEC, False, False,
        'No closed-form parameter target or ceiling is frozen for S_omega (module_spec.csv gives 0 '
        'parameters for S, which is a rule-based placeholder, not a learned-model target).')
    add('initialization', NA, IMPL_SPEC, False, True, 'No initialization scheme frozen.')
    add('seed', NA, IMPL_SPEC, False, True, 'No seed frozen for S_omega training.')

    # B. post-refinement input contract
    add('inference_GT_free', impl_ps['gt_at_inference'] is False, IMPL_SPEC, True, True,
        'Frozen: gt_at_inference = false. Requirement satisfied.')
    add('input_tensor_source', 'already-computed post-refinement quantities only', IMPL_SPEC, False, True,
        'The source is bounded to "already-computed post-refinement quantities only" and '
        'second_image_encoder=false, but the exact tensors are not named.')
    add('input_dtype', NA, IMPL_SPEC, False, True, 'No dtype frozen.')
    add('input_units', NA, IMPL_SPEC, False, True, 'No units frozen.')
    add('input_normalization', NA, IMPL_SPEC, False, True,
        'No standardization / normalization rule frozen for S_omega inputs.')
    add('input_requires_p_global', 'implied by feature_family_examples', IMPL_SPEC, False, True,
        'p_global is implied (probability summary difference) but not explicitly frozen as an input.')
    add('input_requires_p_refined', 'implied by feature_family_examples', IMPL_SPEC, False, True,
        'p_refined is implied but not explicitly frozen as an input.')
    add('input_requires_ROI_geometry', 'listed in feature_family_examples', IMPL_SPEC, False, True,
        'ROI geometry is listed as an example family, not frozen as a required input.')
    add('input_uses_task_id', 'listed in feature_family_examples', IMPL_SPEC, False, True,
        'task_id is listed as an example family, not frozen as a required input.')
    add('input_uses_benefit_router_output', NA, IMPL_SPEC, False, True,
        'Whether B_phi output enters S_omega is NOT frozen.')
    add('input_uses_refined_feature_map', NA, IMPL_SPEC, False, True,
        'Whether refined feature maps (beyond probability summaries) enter S_omega is NOT frozen.')

    # C. training target
    add('training_target', impl_ps['target'], IMPL_SPEC, True, True,
        'Frozen: "ACCEPT iff DeltaDice > 0". Binary target, ACCEPT=1 iff DeltaDice strictly positive.')
    add('zero_gain_label_rule', 'ACCEPT = 0 (DeltaDice == 0 is NOT > 0)', IMPL_SPEC, True, False,
        'Strictly derivable from "iff DeltaDice > 0": DeltaDice == 0 -> ACCEPT = 0 (fallback). '
        'The frozen text states ">" not ">=", so no convention is invented.')
    add('target_dtype', NA, IMPL_SPEC, False, False, 'Target dtype (bool/int64/float32) not frozen.')
    add('target_class_names', NA, IMPL_SPEC, False, False,
        'Class names (e.g. ACCEPT/FALLBACK) not frozen. Do NOT substitute the Phase25C '
        'BENEFICIAL/HARMFUL/NEUTRAL categories, which are NOT equivalent to DeltaDice > 0.')
    add('target_source', impl_ps['target_source'], IMPL_SPEC, True, True,
        'Frozen: OOF refinement predictions from ROUTER_DEVELOPMENT only.')
    add('target_not_phase25c_categories', True, IMPL_SPEC, True, False,
        'The Phase25C categories (BENEFICIAL >= +0.02 / HARMFUL <= -0.01 / NEUTRAL) are NOT frozen '
        'as the S_omega target and must not be substituted.')

    # D. loss
    add('loss', impl_ps['loss'], IMPL_SPEC, False, True,
        'Frozen as the NAME "binary cross entropy" only. No reduction, no class weighting, no '
        'pos_weight, no label smoothing, and no BCEWithLogits-vs-BCE choice is frozen.')
    add('loss_class_weighting', NA, IMPL_SPEC, False, True, 'No class weighting frozen.')
    add('loss_pos_weight', NA, IMPL_SPEC, False, True, 'No pos_weight frozen.')
    add('loss_label_smoothing', NA, IMPL_SPEC, False, True, 'No label smoothing frozen.')
    add('loss_reduction', NA, IMPL_SPEC, False, True, 'No reduction frozen.')

    # E. optimizer
    add('optimizer', NA, IMPL_SPEC, False, True, 'No optimizer class frozen for S_omega.')
    add('lr', NA, IMPL_SPEC, False, True, 'No learning rate frozen for S_omega.')
    add('weight_decay', NA, IMPL_SPEC, False, True, 'No weight decay frozen for S_omega.')
    add('batch_size', NA, IMPL_SPEC, False, True, 'No batch size frozen for S_omega.')

    # F. training length / early stopping
    add('max_epochs', NA, IMPL_SPEC, False, True, 'No max_epochs frozen for S_omega.')
    add('patience', NA, IMPL_SPEC, False, True, 'No early-stopping patience frozen for S_omega.')

    # G. checkpoint selection
    add('checkpoint_metric', NA, IMPL_SPEC, False, True, 'No checkpoint-selection metric frozen for S_omega.')
    add('checkpoint_direction', NA, IMPL_SPEC, False, True, 'No MINIMIZE/MAXIMIZE frozen for S_omega.')
    add('tie_rule', NA, IMPL_SPEC, False, True, 'No checkpoint tie rule frozen for S_omega.')

    # H. scheduler
    add('scheduler', NA, IMPL_SPEC, False, True, 'No scheduler frozen for S_omega.')
    add('scheduler_monitor', NA, IMPL_SPEC, False, True, 'No scheduler monitor frozen for S_omega.')
    add('scheduler_order', NA, IMPL_SPEC, False, True,
        'No ordering relative to checkpoint decision / patience frozen for S_omega.')

    # I. data partition / leakage
    add('OOF_refinement_source', impl_ps['target_source'], IMPL_SPEC, True, True,
        'Frozen: OOF refinement predictions from ROUTER_DEVELOPMENT only. Phase25C cross-fit is clean '
        '(0 violations; fold-specific checkpoints; Phase25A final refiner NOT used for OOF).')
    add('somega_training_example_construction', NA, IMPL_SPEC, False, True,
        'The exact construction of S_omega training examples (which OOF candidate refinement maps are '
        'used, and how they are paired with their global counterparts) is NOT frozen.')

    # J. availability of required post-refinement features
    add('post_refinement_feature_availability', 'PARTIAL__UNBOUND', IMPL_SPEC, False, True,
        'No frozen post-refinement GT-free feature table exists. On disk there are only '
        'data_cache/phase25c_barr_oof_paired_gain_labels_v1_2/_tmp_refined_crop_prob_<DOMAIN>.npy '
        '(temporary-named, referenced by NO audit/contract) and the bound p_global 512 cache '
        '(data_cache/phase25a_barr_roi030_cache). Without frozen feature formulas the required '
        'S_omega inputs cannot be reproduced without inventing them.')

    # K. CV / split
    add('CV_fold_count', NA, IMPL_SPEC, False, True, 'No S_omega CV fold count frozen.')
    add('CV_algorithm', NA, IMPL_SPEC, False, True, 'No S_omega CV fold-assignment algorithm frozen.')
    add('grouping', NA, IMPL_SPEC, False, True, 'No S_omega grouping variable frozen.')
    add('stratification', NA, IMPL_SPEC, False, True, 'No S_omega stratification variable frozen.')
    add('CV_seed', NA, IMPL_SPEC, False, True, 'No S_omega CV seed frozen.')
    add('inner_split', NA, IMPL_SPEC, False, True, 'No S_omega inner early-stop split rule frozen.')

    # L. normalization
    add('normalization', NA, IMPL_SPEC, False, True,
        'No per-feature normalization rule frozen for S_omega (the Phase25D router normalization is '
        'frozen for the ROUTER only and must not be borrowed unless explicitly frozen for Phase25F).')

    # M. final refit
    add('final_refit', NA, IMPL_SPEC, False, True, 'No S_omega final-refit rule frozen.')
    add('final_epoch_rule', NA, IMPL_SPEC, False, True, 'No S_omega final-refit epoch rule frozen.')
    add('final_seed', NA, IMPL_SPEC, False, True, 'No S_omega final-refit seed frozen.')
    add('final_scheduler', NA, IMPL_SPEC, False, True, 'No S_omega final-refit scheduler behavior frozen.')

    # N. decision threshold
    add('decision_threshold', NA, IMPL_SPEC, False, True,
        'BLOCKING. No probability/logit threshold for ACCEPT_REFINEMENT vs FALLBACK_GLOBAL is frozen. '
        'The 0.5 in the frozen fusion block is the SEGMENTATION OUTPUT threshold (INHERITED), NOT the '
        'S_omega decision threshold. 0.5 must not be assumed.')

    # O. fusion / fallback
    add('fusion_rule', fusion['rule'], IMPL_SPEC, True, True,
        'Frozen: outside frozen ROI -> p_final_candidate = p_global; inside frozen ROI -> resized p_refined.')
    add('fusion_alpha_blending', fusion['alpha_blending'], IMPL_SPEC, True, False, 'Frozen: alpha_blending = false.')
    add('fusion_learned', fusion['learned_fusion'], IMPL_SPEC, True, False, 'Frozen: learned_fusion = false.')
    add('fallback_rule', 'SKIP -> final = global; EXECUTE_THEN_REJECT -> final = global; '
                         'EXECUTE_THEN_ACCEPT -> final = regional-fused', PRESERV, True, True,
        'Frozen in the preservation contract. NOTE: the explicit binding of the S_omega ACCEPT/REJECT '
        'decision onto EXECUTE_THEN_ACCEPT / EXECUTE_THEN_REJECT is implied by the contract but is not '
        'stated as an explicit S_omega-to-outcome mapping.')
    add('ROI_threshold_role', '0.30 (ROI PROPOSAL threshold; bbox -> ACTION_AVAILABLE/FORCED_SKIP)', IMPL_SPEC, True, False,
        'Frozen. Distinct from the segmentation output threshold.')
    add('segmentation_threshold_role', '0.50 (segmentation OUTPUT threshold; final mask/Dice/IoU; INHERITED)',
        IMPL_SPEC, True, False, 'Frozen. Not the S_omega decision threshold.')
    add('action_unavailable_behavior', 'FORCED_SKIP pre-gate; final = global', IMPL_SPEC, True, False,
        'Frozen in the action_availability block.')
    add('interaction_with_phase25e_SKIP', NA, IMPL_SPEC, False, True,
        'The exact interaction of S_omega with a Phase25E SKIP (no refinement executed) is not frozen '
        'beyond the preservation contract (SKIP -> final = global).')

    # Policy fields
    add('A7_A8_evaluation_contract', 'AMBIGUOUS_OWNERSHIP', MODULE_PLAN, False, True,
        'See phase25f_a7_a8_evaluation_ownership.json. The module plan assigns "comparator + ablation '
        'evaluation report and freeze" to 25G, while the Phase25E->25F handoff lists "C9 post-safety '
        '(S_omega) comparator" under Phase25F scope. Marked BLOCKING.')
    add('holdout_policy', 'ROUTER_HOLDOUT forbidden for fitting/threshold/calibration; integrated '
                          'evaluation only', DATA_ROLE, True, False, 'Frozen.')
    add('VAL808_policy', 'SECONDARY / CONTINUITY DEVELOPMENT BENCHMARK; not used to fill spec values',
        DATA_ROLE, True, False, 'Frozen.')
    add('TEST_policy', 'CLOSED until Phase39; 0 reads', DATA_ROLE, True, False, 'Frozen.')

    with (TABLE / 'phase25f_specification_completeness.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['field', 'frozen_value', 'authoritative_source', 'source_sha',
                                          'complete', 'blocking_if_missing', 'notes'])
        w.writeheader()
        for r in rows:
            w.writerow(r)

    incomplete = [r for r in rows if not r['complete']]
    blocking = [r for r in rows if (not r['complete']) and r['blocking_if_missing']]
    binding['field_status'] = {
        'total_fields': len(rows),
        'complete_fields': len(rows) - len(incomplete),
        'incomplete_fields': len(incomplete),
        'blocking_fields': len(blocking),
        'blocking_field_names': [r['field'] for r in blocking],
        'incomplete_field_names': [r['field'] for r in incomplete],
    }
    binding['all_pass'] = True  # binding itself succeeded; completeness verdict is separate
    (AUD / 'phase25f_post_safety_spec_binding.json').write_text(
        json.dumps(binding, indent=2, allow_nan=False) + '\n', encoding='utf-8')

    # ================= §3 input contract table ===================================
    input_rows = []
    for fam in impl_ps['feature_family_examples']:
        input_rows.append({
            'feature_family_example': fam,
            'exact_name_frozen': False,
            'formula_frozen': False,
            'dtype_frozen': False,
            'ordering_frozen': False,
            'normalization_frozen': False,
            'source_tensor_available_on_disk': 'PARTIAL (p_global 512 cache bound; refined crop probs exist '
                                               'only as unbound _tmp files)',
            'source_tensor_bound_by_contract': False,
            'gt_free_at_inference': True,
            'authoritative_source': IMPL_SPEC,
            'verdict': 'BLOCKING__FEATURE_NOT_FROZEN',
        })
    input_rows.append({
        'feature_family_example': 'second_image_encoder',
        'exact_name_frozen': True, 'formula_frozen': True, 'dtype_frozen': False,
        'ordering_frozen': True, 'normalization_frozen': False,
        'source_tensor_available_on_disk': 'N/A',
        'source_tensor_bound_by_contract': True,
        'gt_free_at_inference': True,
        'authoritative_source': IMPL_SPEC,
        'verdict': 'FROZEN_FALSE__NO_SECOND_ENCODER',
    })
    with (TABLE / 'phase25f_post_safety_input_contract.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(input_rows[0].keys()))
        w.writeheader()
        w.writerows(input_rows)

    # ================= §3I/§3J training-data source audit ========================
    src_audit = {
        'classification': 'PHASE25F_POST_SAFETY_SPEC_COMPLETENESS_AUDIT',
        'stage': 'TRAINING_DATA_SOURCE_AUDIT',
        'method': 'RA-MedFiLM-BARR',
        'frozen_target_source': impl_ps['target_source'],
        'phase25c_provides': c25c_handoff['phase25c_provides'],
        'phase25b_provides': c25c_handoff['phase25b_provides'],
        'label_manifest': label_manifest,
        'phase25b_feature_groups': p25b_groups,
        'p_global_cache_binding': cache,
        'refiner_inference_binding': infer,
        'fullfield_reconstruction': fullfield,
        'crossfit_leakage_audit': crossfit,
        'post_refinement_gt_free_feature_table_exists': False,
        'post_refinement_scalar_table_search': 'reports/tables/ contains no post-refinement / refined-feature table',
        'on_disk_post_refinement_arrays': {
            'path_pattern': 'data_cache/phase25c_barr_oof_paired_gain_labels_v1_2/_tmp_refined_crop_prob_<DOMAIN>.npy',
            'referenced_by_any_audit_or_contract': False,
            'bound_by_sha': False,
            'naming': 'temporary (_tmp_ prefix)',
        },
        'delta_dice_csv_alone_sufficient': False,
        'delta_dice_csv_alone_sufficient_reason':
            'A DeltaDice CSV is not sufficient: S_omega requires post-refinement GT-free INPUT features '
            'that were never persisted as a frozen feature table. The label CSV additionally contains '
            'GT-derived columns (global_dice, candidate_refined_dice) that are FORBIDDEN as inputs.',
        'sources': {IMPL_SPEC: sha(ROOT / IMPL_SPEC), C25C_HANDOFF: sha(ROOT / C25C_HANDOFF),
                    LABEL_MANIFEST: sha(ROOT / LABEL_MANIFEST), C25C_CACHE: sha(ROOT / C25C_CACHE)},
        'all_pass': True,
    }
    (AUD / 'phase25f_training_data_source_audit.json').write_text(
        json.dumps(src_audit, indent=2, allow_nan=False) + '\n', encoding='utf-8')

    # ================= §4 leakage-safety matrix ==================================
    def row(source_name, pop, contains_gt, gt_role, at_infer, pre_post, producer, producer_fold,
            excl_fit, excl_es, excl_ckpt, allowed_input, allowed_target, auth, verdict):
        return {
            'source_name': source_name, 'sample_population': pop, 'contains_GT': contains_gt,
            'GT_role': gt_role, 'available_at_inference': at_infer,
            'generated_pre_or_post_refinement': pre_post, 'producer_model': producer,
            'producer_fold': producer_fold, 'sample_excluded_from_producer_fit': excl_fit,
            'sample_excluded_from_producer_early_stop': excl_es,
            'sample_excluded_from_producer_checkpoint_selection': excl_ckpt,
            'allowed_for_Somega_input': allowed_input, 'allowed_for_Somega_target': allowed_target,
            'authoritative_source': auth, 'verdict': verdict,
        }

    leak_rows = [
        row('phase25c_oof_paired_gain_labels.delta_dice', 'ROUTER_DEVELOPMENT (4957)', 'YES',
            'GT-DERIVED SCALAR (Dice_cand - Dice_global); used as TARGET only', 'NO (not an input)',
            'POST_REFINEMENT', 'fold-specific BARRRegionalRefinerV1 (3 outer folds)', 'outer_fold column',
            'YES', 'YES', 'YES', 'FORBIDDEN', 'ALLOWED (ACCEPT iff DeltaDice > 0)',
            'data_cache/.../phase25c_oof_paired_gain_labels.csv',
            'TARGET_OK__INPUT_FORBIDDEN'),
        row('phase25c_oof_paired_gain_labels.global_dice', 'ROUTER_DEVELOPMENT (4957)', 'YES',
            'GT-DERIVED METRIC', 'NO', 'POST_REFINEMENT', 'n/a (metric)', 'n/a', 'n/a', 'n/a', 'n/a',
            'FORBIDDEN', 'FORBIDDEN', 'data_cache/.../phase25c_oof_paired_gain_labels.csv',
            'FORBIDDEN__GT_DERIVED'),
        row('phase25c_oof_paired_gain_labels.candidate_refined_dice', 'ROUTER_DEVELOPMENT (4957)', 'YES',
            'GT-DERIVED METRIC', 'NO', 'POST_REFINEMENT', 'n/a (metric)', 'n/a', 'n/a', 'n/a', 'n/a',
            'FORBIDDEN', 'FORBIDDEN', 'data_cache/.../phase25c_oof_paired_gain_labels.csv',
            'FORBIDDEN__GT_DERIVED'),
        row('phase25c_oof_paired_gain_labels.gain_category', 'ROUTER_DEVELOPMENT (4957)', 'YES',
            'GT-DERIVED CATEGORY (BENEFICIAL/HARMFUL/NEUTRAL)', 'NO', 'POST_REFINEMENT', 'n/a', 'n/a',
            'n/a', 'n/a', 'n/a', 'FORBIDDEN', 'FORBIDDEN (not the frozen target)', 
            'data_cache/.../phase25c_oof_paired_gain_labels.csv', 'FORBIDDEN__NOT_THE_FROZEN_TARGET'),
        row('phase25c_oof_refined_crop_prob_<DOMAIN>.npy', 'ROUTER_DEVELOPMENT action-available', 'NO',
            'NONE (model output probability)', 'YES', 'POST_REFINEMENT',
            'fold-specific BARRRegionalRefinerV1', 'outer_fold (fold-specific checkpoint)',
            'YES', 'YES', 'YES', 'UNDEFINED__INPUT_CONTRACT_NOT_FROZEN', 'FORBIDDEN',
            'data_cache/phase25c_barr_oof_paired_gain_labels_v1_2/_tmp_refined_crop_prob_*.npy',
            'UNBOUND__NOT_A_FROZEN_ARTIFACT'),
        row('phase25a_roi030_cache.prob512 (p_global)', 'ROUTER_DEVELOPMENT (4957)', 'NO',
            'NONE (frozen global model output)', 'YES', 'PRE_REFINEMENT',
            'frozen Phase21 global MedFiLM (SHA 286689fd...)', 'n/a (frozen global model)', 'n/a', 'n/a', 'n/a',
            'UNDEFINED__INPUT_CONTRACT_NOT_FROZEN', 'FORBIDDEN',
            'reports/audits/phase25c_global_cache_binding.json', 'BOUND__INPUT_ROLE_NOT_FROZEN'),
        row('phase25b_barr_pre_refinement_features_v1_2 (202-D)', 'ROUTER_DEVELOPMENT (4957)', 'NO',
            'NONE (GT-free pre-refinement features)', 'YES', 'PRE_REFINEMENT',
            'frozen Phase21 global MedFiLM + ROI rule', 'n/a', 'n/a', 'n/a', 'n/a',
            'NO (frozen spec says S_omega inputs are POST-refinement only)', 'FORBIDDEN',
            'data_cache/phase25b_barr_pre_refinement_features_v1_2/cache_manifest.json',
            'PRE_REFINEMENT__NOT_THE_FROZEN_SOMEGA_FAMILY'),
        row('candidate_mask_sha256', 'ROUTER_DEVELOPMENT (4957)', 'NO',
            'NONE (integrity digest)', 'YES', 'POST_REFINEMENT', 'n/a', 'n/a', 'n/a', 'n/a', 'n/a',
            'NO (not a feature)', 'FORBIDDEN', 'data_cache/.../phase25c_oof_paired_gain_labels.csv',
            'DIGEST_ONLY'),
        row('predicted_roi_area_fraction', 'ROUTER_DEVELOPMENT (4957)', 'NO',
            'NONE (GT-free ROI geometry)', 'YES', 'PRE_REFINEMENT', 'frozen Phase21 global MedFiLM + ROI rule',
            'n/a', 'n/a', 'n/a', 'n/a', 'UNDEFINED__INPUT_CONTRACT_NOT_FROZEN', 'FORBIDDEN',
            'data_cache/phase25b_barr_pre_refinement_features_v1_2/feature_group_offsets.json',
            'AVAILABLE__ROLE_NOT_FROZEN'),
    ]
    with (TABLE / 'phase25f_training_data_leakage_contract.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(leak_rows[0].keys()))
        w.writeheader()
        w.writerows(leak_rows)

    leak_audit = {
        'classification': 'PHASE25F_POST_SAFETY_SPEC_COMPLETENESS_AUDIT',
        'stage': 'LEAKAGE_SAFETY_AUDIT',
        'method': 'RA-MedFiLM-BARR',
        'requirement': ('For every development sample used to train/evaluate S_omega, the regional-refiner '
                        'output used as an input MUST come from a refiner that did not fit / early-stop / '
                        'select its checkpoint on that sample outer fold.'),
        'phase25c_crossfit_leakage_violations': crossfit['crossfit_leakage_violations'],
        'phase25c_crossfit_verdict': crossfit['verdict'],
        'phase25a_final_refiner_used_for_oof': infer['phase25a_final_refiner_used_for_oof'],
        'fold_specific_checkpoints_only': True,
        'oof_target_fold_never_used_for_checkpoint_selection': True,
        'leakage_safe_source_exists': True,
        'leakage_safe_source': ('Phase25C OOF fold-specific refined crop probability outputs on '
                                'ROUTER_DEVELOPMENT (cross-fit leakage-clean).'),
        'leakage_safe_source_is_frozen_bound_artifact': False,
        'unbound_source_problem': ('The OOF refined crop probability arrays exist only as '
                                   '"_tmp_refined_crop_prob_<DOMAIN>.npy" files that NO audit or contract '
                                   'references or hashes. They are not a frozen, reproducible artifact.'),
        'ambiguity_count': 0,
        'blocking_rows': [r['source_name'] for r in leak_rows
                          if 'UNDEFINED__INPUT_CONTRACT_NOT_FROZEN' in r['allowed_for_Somega_input']
                          or 'UNBOUND' in r['verdict']],
        'sources': {CROSSFIT_LEAK: sha(ROOT / CROSSFIT_LEAK), C25C_INFER: sha(ROOT / C25C_INFER),
                    C25C_HANDOFF: sha(ROOT / C25C_HANDOFF), LABEL_MANIFEST: sha(ROOT / LABEL_MANIFEST)},
        'verdict': 'LEAKAGE_SAFE_SOURCE_EXISTS_BUT_INPUT_CONTRACT_AND_ARTIFACT_BINDING_MISSING',
        'all_pass': True,
    }
    (AUD / 'phase25f_leakage_safety_audit.json').write_text(
        json.dumps(leak_audit, indent=2, allow_nan=False) + '\n', encoding='utf-8')

    print(f'§2 role: all_pass={role["all_pass"]} (saves_compute={impl_ps["saves_compute"]}, '
          f'novelty_claimed={arch_ps["novelty_claimed"]})')
    print(f'§5 completeness: {len(rows)} fields, {len(incomplete)} incomplete, {len(blocking)} blocking')
    print('  blocking:', [r['field'] for r in blocking])
    print(f'§4 leakage rows: {len(leak_rows)}; verdict={leak_audit["verdict"]}')
    print('PHASE25F_S2_S5_AUDIT_WRITTEN')


if __name__ == '__main__':
    main()
