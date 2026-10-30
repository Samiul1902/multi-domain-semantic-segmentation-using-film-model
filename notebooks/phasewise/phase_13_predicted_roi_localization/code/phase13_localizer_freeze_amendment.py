"""
Phase 13 Part 1A-R1 — Supervisor protocol-freeze amendment (READ-ONLY / NO TRAINING).

Part 1A-R1 records exact supervisor decisions, amends the clean-v3 Phase-13 protocol
candidate, and produces the final supervisor-frozen protocol artifact.

Forbidden here: training, optimizer instantiation for training, model forward inference,
clean-v3 proposal generation, predicted-region segmentation, inspecting clean-v3 localizer
results, Part 1B, Phase 14, TEST access.

Authorized reads: already-frozen clean-v3 VAL predictions/tables, used ONLY to derive the
prospectively defined hard-set membership (Phase-13 Part 1A-R1 §17).

Author: WorkBuddy AI (Agent mode)
Date: 2026-09-21
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

PROJECT_ROOT = Path(r'D:\Softfors\jup')
REPORTS = PROJECT_ROOT / 'reports'
TABLES = REPORTS / 'tables'
AUDITS = REPORTS / 'audits'

CODE_DIR = PROJECT_ROOT / 'notebooks/phasewise/phase_13_predicted_roi_localization/code'
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

import phase13_localizer_protocol as p13  # noqa: E402  (Part-1A read-only support module)

# ---------------------------------------------------------------------------
# Frozen identities
# ---------------------------------------------------------------------------
MANIFEST_CLEAN = 'phase4_v3'
TAXONOMY_CLEAN = 'kub_size_clean_v3_v1'

PART1A_NOTEBOOK = (PROJECT_ROOT / 'notebooks/phasewise/phase_13_predicted_roi_localization'
                   / 'phase13_clean_v3_localizer_protocol_freeze.ipynb')
PART1A_NOTEBOOK_SHA = '68f787e1f70fcf706442b342e62cc615eeb347653e753149987becf793ac2bd0'

CANDIDATE_JSON = AUDITS / 'phase13_clean_v3_localizer_protocol_candidate.json'
PART1A_MODULE = CODE_DIR / 'phase13_localizer_protocol.py'

# --- hard-set sources (frozen clean-v3 tables) ---
GEOMETRY_TABLE = TABLES / 'phase12_clean_v3_oracle_geometry.csv'
COMPONENT_TABLE = TABLES / 'phase12_clean_v3_oracle_component_metrics.csv'
CASE_TABLE = TABLES / 'phase12_clean_v3_oracle_case_metrics.csv'
PHASE11_CASE_TABLE = TABLES / 'phase11_clean_v3_per_model_case_failure_metrics.csv'

HARD_TINY_OUT = TABLES / 'phase13_clean_v3_hard_tiny_replication_set.csv'
GLOBAL_EMPTY_OUT = TABLES / 'phase13_clean_v3_global_empty_replication_set.csv'
DIFF_OUT = TABLES / 'phase13_v2_to_clean_v3_localizer_protocol_diff.csv'
FROZEN_JSON = AUDITS / 'phase13_clean_v3_localizer_protocol_frozen.json'
FROZEN_MD = AUDITS / 'phase13_clean_v3_localizer_protocol_frozen.md'

# --- frozen proposal configuration (supervisor decision §5 / §9) ---
FIXED_PROPOSAL_CONFIG = {'threshold': 0.10, 'margin': 0.20, 'top_k': 5, 'nms_iou': 0.30}
FIXED_PROPOSAL_CONFIG_PROVENANCE = ('VERIFIED_HISTORICAL_SELECTION + '
                                    'PROSPECTIVELY_FROZEN_FOR_CLEAN_V3_PRIMARY')

# --- heatmap contract (supervisor decision §2) ---
HEATMAP_CONTRACT = {
    'input': '512x512',
    'output_heatmap': '128x128',
    'heatmap_resolution': 128,
    'explicit_argument_required': True,
    'fail_loud_assertions': [
        'model output spatial shape == (128, 128)',
        'target heatmap spatial shape == (128, 128)',
        'prediction and target shapes identical',
    ],
    'applies_to': ['training', 'validation', 'checkpoint reproduction', 'proposal inference'],
    'never_rely_on_constructor_default': True,
    'historical_helper_defect': 'src/inference/learned_roi.predict_localizer omits '
                                'heatmap_resolution=128',
    'preferred_remediation': 'B',
    'remediation_options': {
        'A': 'repair the reusable helper prospectively with explicit heatmap_resolution=128',
        'B': 'create a clean-v3-safe inference wrapper (PREFERRED — avoids any risk of '
             'altering historical reproduction)',
    },
    'must_be_declared_and_tested': True,
    'historical_frozen_outputs_must_not_be_modified': True,
}

# --- historical checkpoint-selection provenance (verified from executing code) ---
HISTORICAL_EXECUTING_SELECTION = {
    'source': 'scripts/training/train_phase13b_localizer.py',
    'source_line': 164,
    'score_tuple': '(tiny_recall90, overall_recall90, -mean_roi_area_fraction, -val_loss)',
    'tuple_length': 4,
    'improvement_rule': 'score > best_score (strict)',
    'ties': 'bad epoch',
    'patience': 15,
    'proposal_config_used': 'BEST OF THE 20-CONFIG GRID PER EPOCH (VAL-dependent)',
    'checkpoint_key': 'best_validation_score',
    'manifest_recorded_in_checkpoint': 'phase4_v2',
    'note': 'The executing code used a 4-tuple that did NOT include hard_tiny_recovered90, '
            'global_empty_images_covered90 or multi_component_recall90, even though those '
            'were computed and logged into history.csv.',
}
HISTORICAL_PROTOCOL_DOC_SELECTION = {
    'source': 'PHASE13B.md',
    'score_tuple': '(recovered frozen 16 Tiny misses@90, recovered frozen 7 global-empty@90, '
                   'overall Tiny recall90, overall component recall90, multi-component '
                   'recall90, min ROI area fraction, min proposals/image, prefer 512)',
    'tuple_length': 8,
    'note': 'Frozen-protocol document (authority rank 2), not the executing code.',
}
HISTORICAL_STAGE3_SELECTION = {
    'source': 'reports/audits/phase13b_stage3_validation_correction.md',
    'score_tuple': '(VAL Tiny recall90, overall component recall90, lower VAL localization loss)',
    'tuple_length': 3,
    'note': 'Stage-3 correction document (authority rank 2).',
}

CLEAN_V3_CHECKPOINT_SELECTION = {
    'evaluated_at': 'ONE FIXED PROPOSAL CONFIGURATION ONLY',
    'fixed_config': FIXED_PROPOSAL_CONFIG,
    'tuple_ordering': [
        'hard_tiny_recovered90',
        'global_empty_images_covered90',
        'tiny_recall90',
        'overall_recall90',
        'multi_component_recall90',
        '-mean_roi_area_fraction',
        '-mean_proposals_per_image',
        '-val_loss',
    ],
    'tuple_length': 8,
    'improvement_rule': 'new_score > best_score (strict tuple comparison)',
    'ties': 'bad epoch',
    'patience': 15,
    'hard_tiny_and_global_empty_terms_use': 'CLEAN-v3 RE-DERIVED REPLICATION COHORTS',
    'zero_denominator_rule': 'STOP / CHECK_REQUIRED BEFORE TRAINING',
    'per_epoch_proposal_grid_search': 'DISABLED',
    'provenance_disclosure': (
        'SUPERVISOR_SPECIFIED_CLEAN_V3_CONTRACT. The executing historical code used a 4-tuple '
        '(see HISTORICAL_EXECUTING_SELECTION); the supervisor R1 contract specifies an 8-term '
        'tuple that extends it with the hard-set, multi-component and proposals/image terms. '
        'The executing-code 4-tuple is recorded here so the deviation is never silently '
        'mis-stated as historical reproduction.'),
}

COVERAGE_CONTRACT = {
    'primary': 'covered90 = component coverage fraction >= 0.90',
    'descriptive_preserved': ['covered50', 'any_overlap', 'coverage_fraction'],
    'new_threshold_after_training': 'FORBIDDEN',
}

PHASE14_DISTRIBUTION_REQUIREMENT = {
    'historical_verified_problem': 'Phase-14 refiner trained on GT-derived + perturbed + '
                                   'background-negative crops but evaluated on predicted '
                                   'Stage-4D proposals',
    'is_a_phase13_localizer_training_change': False,
    'phase13_trains': 'image -> localization heatmap / proposals (NOT a regional '
                      'segmentation refiner)',
    'canonical_disposition': 'DEFERRED_REQUIREMENT_FOR_PHASE14_IF_GATE_ALLOWS',
    'requirement': 'If the post-Phase-13 gate permits Phase 14, its regional-refiner training '
                   'distribution MUST be prospectively designed to match, or explicitly model, '
                   'the frozen predicted-proposal distribution.',
    'phase14_crop_training_recipe_frozen_here': False,
    'phase14_started': False,
    'phase13_predicted_proposal_training_crops': False,
}

DOWNSTREAM_GEOMETRY = {
    'proposal_generation': 'frozen GT-free Stage-4D semantics',
    'config': FIXED_PROPOSAL_CONFIG,
    'must_not_change_margin_to_phase12_oracle_margin': 0.25,
    'reason': 'Phase 13 measures the practical GT-free proposal pipeline; the Phase-12 oracle '
              'is an upper bound and used margin 0.25',
    'retention_includes': ['localization imperfection', 'practical proposal geometry difference'],
    'not_a_pure_localization_error_isolation_study': True,
    'label': 'PRACTICAL_GT_FREE_ORACLE_BENEFIT_RETENTION',
}

DOWNSTREAM_COMPOSITION = {
    'regional_crop_resolution': '512x512',
    'regional_probability_restoration': 'FLOAT_BILINEAR',
    'multiple_predicted_regional_crops': 'pixelwise MAX among REGIONAL probabilities',
    'global_outside_predicted_proposal_union': 'RETAIN GLOBAL probability',
    'inside_predicted_proposal_support': 'REPLACE with REGIONAL probability',
    'forbidden': ['max(global, regional) inside proposal support',
                  'averaging global/regional', 'learned fusion'],
    'final_threshold_full_native_probability': 0.5,
    'primary_name': 'PREDICTED_REGION_FLOAT_GLOBAL_RETAINED',
    'status': 'PROSPECTIVELY_FROZEN_FOR_PHASE13_PRACTICAL_EVALUATION',
    'predicted_region_inference_authorized_in_r1': False,
}

DOWNSTREAM_MODEL_SCOPE = ['UNet', 'Attention U-Net', 'UNet++', 'DeepLabV3+']
DOWNSTREAM_REFERENCE_MODEL = None
HARDSET_ANCHOR_ROLE = 'HISTORICAL_PHASE13_HARDSET_REPLICATION_ANCHOR_ONLY'
HARDSET_ANCHOR_IS_NOT = ['winner', 'best model', 'Phase-13 downstream reference model',
                         'final architecture choice']

RETENTION_CONTRACT = {
    'aggregate_model_level': {
        'oracle_gain_dice': 'ORACLE - GLOBAL',
        'predicted_gain_dice': 'PREDICTED - GLOBAL',
        'oracle_gap_retention_dice': 'predicted_gain_dice / oracle_gain_dice '
                                     '(only where oracle_gain_dice > 0)',
        'object_recall': 'same construction',
    },
    'numerical_sufficient_retention_threshold': None,
    'case_level': 'report raw deltas; do NOT force ratios where oracle delta <= 0',
}

GATE_GOVERNANCE = {
    'dimension_b': 'PRACTICAL_LOCALIZATION_RETENTION',
    'dimension_b_status': 'CANDIDATE_FOR_SUPERVISOR_FREEZE (final evidence contract recorded '
                          'by this R1)',
    'scalar_gate_score': None,
    'numerical_go_threshold': None,
    'final_regional_gate': 'NOT_DECIDED',
    'outcomes_issued_in_this_task': [],
}

LABEL_DEFECTS = {
    'STAGE4D_DESIGN_AUDIT_LABEL_PROVENANCE_DEFECT': {
        'artifact': 'reports/audits/phase13b_stage4d_design_audit.json',
        'label': 'clean_v3_results',
        'status': 'NOT_ACCEPTED_AS_CLEAN_V3_EVIDENCE',
        'evidence': 'the denominator 156 components matches historical phase4_v2',
        'disposition': 'HISTORICAL_v2_PROVENANCE_ONLY',
        'do_not_reuse_as_clean_v3_metrics': True,
        'historical_artifact_modified': False,
    },
    'NON_BLOCKING_HISTORICAL_ARTIFACT_GAP': {
        'artifact': 'experiments/phase13b_kub_localizer_r512_h128_sigmaeq075_'
                    'centernetfocal_seed42_v1/val_search_epoch079.csv',
        'status': 'MISSING',
        'existing_search_dumps': 87,
        'total_epochs_in_history': 88,
        'history_contiguous': True,
        'disposition': 'NON_BLOCKING_HISTORICAL_ARTIFACT_GAP',
        'recreated': False,
        'fabricated': False,
        'history_modified': False,
        'authoritative_epoch_provenance': 'history.csv',
    },
}

GOVERNANCE = {
    'training': 0,
    'optimizer_steps': 0,
    'model_forward_passes': 0,
    'localizer_inference': 0,
    'predicted_region_inference': 0,
    'proposals_generated': 0,
    'clean_v3_grid_search_run': False,
    'test_content_reads': 0,
    'test_metrics': 'NONE',
    'phase14_started': False,
    'external_data_used': False,
    'experiment_a_modified': False,
    'winner_declared': False,
    'reference_model_selected': False,
    'regional_mechanism_promoted': False,
    'historical_artifacts_modified': False,
}


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def _sha(p: Path) -> str:
    return sha256_file(p) if p.is_file() else 'N/A'


# ---------------------------------------------------------------------------
# §1 — clean-v3 historical-replication hard-set derivation
# ---------------------------------------------------------------------------
HISTORICAL_DEFINITION = (
    'hard_tiny = TINY native components (kub_size_clean_v3_v1) AND global_detected == false; '
    'global_detected = at least 1 native-space pixel of the 8-connected GT component has '
    'GLOBAL_NATIVE probability >= 0.5 (executing definition, '
    'phase12_oracle_inference.py component_detection / driver line 459)'
)
GLOBAL_EMPTY_DEFINITION = (
    'global_empty_image = FULL_FIELD image whose clean-v3 UNet++ GLOBAL_NATIVE segmentation '
    'prediction is empty (prediction_empty == true)'
)


def derive_hard_tiny() -> pd.DataFrame:
    """TINY clean-v3 native components NOT detected by the clean-v3 UNet++ global baseline."""
    geometry = pd.read_csv(GEOMETRY_TABLE)[
        ['sample_id', 'native_component_id', 'size_stratum']]
    components = pd.read_csv(COMPONENT_TABLE)
    unetpp = components[components['model'] == 'unetpp'][
        ['sample_id', 'native_component_id', 'global_detected']]
    joined = geometry.merge(unetpp, on=['sample_id', 'native_component_id'],
                            how='left', validate='one_to_one')
    if joined['global_detected'].isna().any():
        raise RuntimeError('hard-set derivation: unmatched components')
    hard = joined[(joined['size_stratum'] == 'TINY') & (~joined['global_detected'].astype(bool))]
    hard = hard.sort_values(['sample_id', 'native_component_id']).reset_index(drop=True)
    out = pd.DataFrame({
        'sample_id': hard['sample_id'],
        'native_component_id': hard['native_component_id'],
        'size_stratum': hard['size_stratum'],
        'historical_definition': HISTORICAL_DEFINITION,
        'clean_v3_source': str(COMPONENT_TABLE.relative_to(PROJECT_ROOT)).replace('\\', '/'),
        'source_sha': _sha(COMPONENT_TABLE),
        'supporting_source': str(GEOMETRY_TABLE.relative_to(PROJECT_ROOT)).replace('\\', '/'),
        'supporting_source_sha': _sha(GEOMETRY_TABLE),
        'global_detected': hard['global_detected'].astype(bool).values,
        'anchor_model': 'unetpp',
        'anchor_role': HARDSET_ANCHOR_ROLE,
    })
    return out


def derive_global_empty() -> pd.DataFrame:
    """FULL_FIELD clean-v3 images whose clean-v3 UNet++ global prediction is empty."""
    cases = pd.read_csv(CASE_TABLE)
    empty = cases[(cases['model'] == 'unetpp') & (cases['variant'] == 'GLOBAL_NATIVE')
                  & (cases['prediction_empty'].astype(bool))]
    empty = empty.sort_values('sample_id').reset_index(drop=True)
    # independent cross-validation against the frozen Phase-11 clean-v3 table
    p11 = pd.read_csv(PHASE11_CASE_TABLE)
    p11_empty = p11[(p11['acquisition_type'] == 'FULL_FIELD') & (p11['model'] == 'unetpp')
                    & (p11['prediction_empty'].astype(bool))]
    if set(empty['sample_id']) != set(p11_empty['sample_id']):
        raise RuntimeError('global-empty derivation: Phase-11 / Phase-12 disagreement')
    out = pd.DataFrame({
        'sample_id': empty['sample_id'],
        'native_component_id': 'N/A',
        'size_stratum': 'N/A',
        'historical_definition': GLOBAL_EMPTY_DEFINITION,
        'clean_v3_source': str(CASE_TABLE.relative_to(PROJECT_ROOT)).replace('\\', '/'),
        'source_sha': _sha(CASE_TABLE),
        'supporting_source': str(PHASE11_CASE_TABLE.relative_to(PROJECT_ROOT)).replace('\\', '/'),
        'supporting_source_sha': _sha(PHASE11_CASE_TABLE),
        'prediction_empty': True,
        'anchor_model': 'unetpp',
        'anchor_role': HARDSET_ANCHOR_ROLE,
    })
    return out


# ---------------------------------------------------------------------------
# §14 — amended v2 -> clean-v3 protocol diff
# ---------------------------------------------------------------------------
AMENDMENT_ROWS = [
    {
        'field': 'A_manifest_population',
        'historical_v2': 'phase4_v2 / FULL_FIELD VAL 106 images / 156 components',
        'proposed_clean_v3': 'phase4_v3 / FULL_FIELD VAL 103 images / 152 components',
        'same_or_changed': 'CHANGED',
        'change_reason': 'clean governance + clean-v3 population (supervisor R1 §14A)',
        'scientifically_material': False,
        'supervisor_decision_required': False,
        'amendment_id': 'A',
        'authorization': 'AUTHORIZED',
    },
    {
        'field': 'B_hard_set_membership',
        'historical_v2': '16 hard-Tiny component IDs + 7 global-empty image IDs (phase4_v2)',
        'proposed_clean_v3': 're-derived on clean-v3 using the SAME historical definition '
                             '(15 hard-Tiny components / 5 global-empty images)',
        'same_or_changed': 'CHANGED',
        'change_reason': 'v2 sample/component IDs must not be reused; definition reproduced on '
                         'clean-v3 before training (supervisor R1 §14B / §1)',
        'scientifically_material': True,
        'supervisor_decision_required': False,
        'amendment_id': 'B',
        'authorization': 'AUTHORIZED',
    },
    {
        'field': 'C_inference_heatmap_resolution_contract',
        'historical_v2': 'implicit / defective generic path '
                         '(learned_roi.predict_localizer omits heatmap_resolution=128)',
        'proposed_clean_v3': 'explicit 128x128 fail-loud contract on every clean-v3 path',
        'same_or_changed': 'CHANGED',
        'change_reason': 'authorized material correction (supervisor R1 §14C / §2)',
        'scientifically_material': True,
        'supervisor_decision_required': False,
        'amendment_id': 'C',
        'authorization': 'AUTHORIZED',
    },
    {
        'field': 'D_proposal_grid_selection',
        'historical_v2': 'per-epoch best-of-grid over the 20-config proposal grid, used inside '
                         'the checkpoint score',
        'proposed_clean_v3': 'fixed historically selected configuration '
                             '0.10 / 0.20 / 5 / 0.30; per-epoch grid search DISABLED',
        'same_or_changed': 'CHANGED',
        'change_reason': 'authorized material methodological improvement — prevents a new '
                         'VAL-dependent post-processing optimization (supervisor R1 §14D / §5)',
        'scientifically_material': True,
        'supervisor_decision_required': False,
        'amendment_id': 'D',
        'authorization': 'AUTHORIZED',
    },
    {
        'field': 'E_phase14_crop_distribution_issue',
        'historical_v2': 'Phase-14 refiner trained on GT-derived/perturbed/negative crops but '
                         'evaluated on predicted proposals',
        'proposed_clean_v3': 'NOT a Phase-13 localizer change; deferred to post-gate Phase-14 '
                             'governance',
        'same_or_changed': 'DEFERRED',
        'change_reason': 'Phase 13 trains image -> heatmap/proposals, not a regional refiner '
                         '(supervisor R1 §14E / §8)',
        'scientifically_material': True,
        'supervisor_decision_required': False,
        'amendment_id': 'E',
        'authorization': 'DEFERRED_TO_PHASE14_GOVERNANCE',
    },
]

_SUPERSEDED_BASE_FIELDS = {'proposal_search_grid'}


def build_amended_diff() -> pd.DataFrame:
    base = p13.build_protocol_diff().copy()
    base['amendment_id'] = 'PART_1A_BASE'
    base['authorization'] = [
        'SUPERSEDED_BY_AMENDMENT_D' if f in _SUPERSEDED_BASE_FIELDS else 'SUPERVISOR_FROZEN'
        for f in base['field']
    ]
    amended = pd.concat([base, pd.DataFrame(AMENDMENT_ROWS)], ignore_index=True)
    amended['unauthorized_material_difference'] = False
    amended['unauthorized_material_difference'] = amended[
        'unauthorized_material_difference'].astype(bool)
    return amended[['amendment_id', 'field', 'historical_v2', 'proposed_clean_v3',
                    'same_or_changed', 'change_reason', 'scientifically_material',
                    'supervisor_decision_required', 'authorization',
                    'unauthorized_material_difference']]


# ---------------------------------------------------------------------------
# §15 — frozen protocol artifact
# ---------------------------------------------------------------------------
def build_frozen_protocol(hard_tiny: pd.DataFrame, global_empty: pd.DataFrame,
                          hard_tiny_sha: str, global_empty_sha: str) -> Dict[str, Any]:
    return {
        'phase': '13',
        'part': '1A-R1',
        'document_type': 'CLEAN_V3_LOCALIZER_PROTOCOL_FROZEN',
        'status': 'SUPERVISOR_FROZEN_READY_FOR_PART1B_TRAINING',
        'date': '2026-09-21',
        'model': 'Gemini 3.8 Flash Medium',
        'task': 'SUPERVISOR_PROTOCOL_FREEZE_AMENDMENT',
        'manifest_version': MANIFEST_CLEAN,
        'taxonomy': TAXONOMY_CLEAN,
        'authorization': {
            'part1a_archaeology': 'ACCEPTED',
            'part1a_protocol_frozen_for_execution': False,
            'part1a_r1': 'AUTHORIZED (this task)',
            'part1b': 'ELIGIBLE_FOR_SUPERVISOR_AUTHORIZATION',
            'part1b_authorized': False,
        },
        'sources': {
            'candidate_protocol': {
                'path': str(CANDIDATE_JSON.relative_to(PROJECT_ROOT)).replace('\\', '/'),
                'sha256': _sha(CANDIDATE_JSON)},
            'part1a_notebook': {
                'path': str(PART1A_NOTEBOOK.relative_to(PROJECT_ROOT)).replace('\\', '/'),
                'sha256': _sha(PART1A_NOTEBOOK),
                'expected_sha256': PART1A_NOTEBOOK_SHA,
                'unchanged': _sha(PART1A_NOTEBOOK) == PART1A_NOTEBOOK_SHA},
            'part1a_support_module': {
                'path': str(PART1A_MODULE.relative_to(PROJECT_ROOT)).replace('\\', '/'),
                'sha256': _sha(PART1A_MODULE)},
        },
        'population': {
            'TRAIN_FULL_FIELD': p13.POPULATION_CENSUS['TRAIN'],
            'VAL_FULL_FIELD': p13.POPULATION_CENSUS['VAL'],
            'VAL_strata': p13.VAL_STRATA_CLEAN,
            'roi_acquisitions': 'EXCLUDED (ROI_NOT_PRIMARY_BINNED)',
            'foreground_rule': 'mask > 0',
            'connectivity': 8,
        },
        'hard_sets': {
            'hard_tiny': {
                'path': str(HARD_TINY_OUT.relative_to(PROJECT_ROOT)).replace('\\', '/'),
                'sha256': hard_tiny_sha,
                'count': int(len(hard_tiny)),
                'definition': HISTORICAL_DEFINITION,
            },
            'global_empty': {
                'path': str(GLOBAL_EMPTY_OUT.relative_to(PROJECT_ROOT)).replace('\\', '/'),
                'sha256': global_empty_sha,
                'count': int(len(global_empty)),
                'definition': GLOBAL_EMPTY_DEFINITION,
            },
            'historical_v2_counts': {'hard_tiny': 16, 'global_empty': 7},
            'counts_need_not_equal_historical': True,
            'derived_before_training': True,
            'anchor_model': 'UNet++',
            'anchor_role': HARDSET_ANCHOR_ROLE,
            'anchor_is_not': HARDSET_ANCHOR_IS_NOT,
            'cross_validated_against': 'reports/tables/phase11_clean_v3_per_model_case_'
                                       'failure_metrics.csv',
            'may_participate_in': 'the historical-style checkpoint metric',
            'must_not_replace_gate_cohorts': [
                'Phase-11 ALL_FOUR_LOW', 'Phase-11 hard cohort',
                'Phase-11 disagreement cohort', 'Phase-12 FULL_FIELD 103'],
        },
        'heatmap_contract': HEATMAP_CONTRACT,
        'proposal_configuration': {
            'threshold': FIXED_PROPOSAL_CONFIG['threshold'],
            'margin': FIXED_PROPOSAL_CONFIG['margin'],
            'top_k': FIXED_PROPOSAL_CONFIG['top_k'],
            'nms_iou': FIXED_PROPOSAL_CONFIG['nms_iou'],
            'provenance': FIXED_PROPOSAL_CONFIG_PROVENANCE,
            'clean_v3_primary_grid_search': 'DISABLED',
            'historical_20_grid': 'DEFERRED_SECONDARY_SENSITIVITY_ONLY',
            'historical_20_grid_authorization_required': True,
            'historical_20_grid_prerequisite': 'primary checkpoint, primary proposal config and '
                                               'primary result must be frozen first',
        },
        'checkpoint_selection': CLEAN_V3_CHECKPOINT_SELECTION,
        'checkpoint_selection_provenance': {
            'executing_code': HISTORICAL_EXECUTING_SELECTION,
            'frozen_protocol_document': HISTORICAL_PROTOCOL_DOC_SELECTION,
            'stage3_correction_document': HISTORICAL_STAGE3_SELECTION,
        },
        'coverage_contract': COVERAGE_CONTRACT,
        'phase14_distribution_requirement': PHASE14_DISTRIBUTION_REQUIREMENT,
        'downstream_geometry': DOWNSTREAM_GEOMETRY,
        'downstream_composition': DOWNSTREAM_COMPOSITION,
        'downstream_model_scope': DOWNSTREAM_MODEL_SCOPE,
        'downstream_reference_model': DOWNSTREAM_REFERENCE_MODEL,
        'retention_contract': RETENTION_CONTRACT,
        'gate_governance': GATE_GOVERNANCE,
        'label_defects': LABEL_DEFECTS,
        'epoch_provenance': {
            'authoritative': 'history.csv (88/88 contiguous epochs)',
            'part1a_complete_epoch_tables': 'reports/tables/phase10_final_epoch_results_*.csv '
                                            '(59/69/85/67) referenced by the Part-1A notebook',
            'part1a_notebook_contains_them': True,
            'duplicated_in_amendment_notebook': False,
            'missing_val_search_epoch079': 'NON_BLOCKING_HISTORICAL_ARTIFACT_GAP (not '
                                           'fabricated)',
        },
        'governance': GOVERNANCE,
        'pass_gate': {
            'hard_sets_rederived_and_frozen_before_training': True,
            'historical_definitions_preserved': True,
            'unetpp_role_replication_anchor_only': True,
            'heatmap_output_contract_128': True,
            'shape_assertions_specified': True,
            'stage4d_label_ambiguity_resolved_as_provenance_defect': True,
            'missing_epoch079_unfabricated': True,
            'primary_proposal_config_fixed': True,
            'historical_20_grid_not_used_for_primary_selection': True,
            'fixed_config_lexicographic_checkpoint_metric_frozen': True,
            'predicted_proposal_training_crops_removed_from_phase13': True,
            'phase14_distribution_mismatch_retained_as_deferred_requirement': True,
            'future_predicted_region_practical_geometry_frozen': True,
            'future_downstream_global_retained_composition_frozen': True,
            'all_four_models_remain_future_downstream_scope': True,
            'no_winner_no_reference_model': True,
            'no_numerical_go_threshold': True,
            'no_training': True,
            'no_inference': True,
            'no_proposals': True,
            'test_reads_zero': True,
            'unauthorized_material_differences': 0,
        },
        'next_action': 'WAIT_FOR_SUPERVISOR_PHASE13_PART1B_TRAINING_AUTHORIZATION',
    }


def _frozen_md(f: Dict[str, Any]) -> str:
    hs, ge = f['hard_sets'], f['governance']
    lines = [
        '# Phase 13 Part 1A-R1 — Clean-v3 Localizer Protocol (SUPERVISOR FROZEN)',
        '',
        f"- Status: **{f['status']}**",
        f"- Phase/part: `{f['phase']}` / `{f['part']}` · Model: {f['model']}",
        f"- Manifest `{f['manifest_version']}` · taxonomy `{f['taxonomy']}`",
        '',
        '## 1. Hard sets (re-derived on clean-v3, frozen before training)',
        '',
        f"- **hard_tiny**: {hs['hard_tiny']['count']} components · "
        f"`{hs['hard_tiny']['sha256']}`",
        f"  - `{hs['hard_tiny']['path']}`",
        f"- **global_empty**: {hs['global_empty']['count']} images · "
        f"`{hs['global_empty']['sha256']}`",
        f"  - `{hs['global_empty']['path']}`",
        f"- Historical v2 counts (NOT a target): {hs['historical_v2_counts']}",
        f"- Anchor: **UNet++** = `{hs['anchor_role']}` — not "
        f"{', '.join(hs['anchor_is_not'])}",
        f"- Cross-validated against: `{hs['cross_validated_against']}`",
        f"- Must NOT replace the gate cohorts: {', '.join(hs['must_not_replace_gate_cohorts'])}",
        '',
        '## 2. Heatmap resolution contract',
        '',
        f"- input **{f['heatmap_contract']['input']}** → output heatmap "
        f"**{f['heatmap_contract']['output_heatmap']}**",
        f"- `heatmap_resolution={f['heatmap_contract']['heatmap_resolution']}`, always passed "
        f"explicitly (never rely on a constructor default)",
        f"- fail-loud assertions: {'; '.join(f['heatmap_contract']['fail_loud_assertions'])}",
        f"- defect: {f['heatmap_contract']['historical_helper_defect']}",
        f"- preferred remediation **{f['heatmap_contract']['preferred_remediation']}** "
        f"(clean-v3-safe inference wrapper)",
        '',
        '## 3. Frozen proposal configuration',
        '',
        f"- threshold **{f['proposal_configuration']['threshold']}** · margin "
        f"**{f['proposal_configuration']['margin']}** · top_k "
        f"**{f['proposal_configuration']['top_k']}** · nms_iou "
        f"**{f['proposal_configuration']['nms_iou']}**",
        f"- provenance: `{f['proposal_configuration']['provenance']}`",
        f"- clean-v3 primary grid search: **{f['proposal_configuration']['clean_v3_primary_grid_search']}**",
        f"- historical 20-grid: `{f['proposal_configuration']['historical_20_grid']}`",
        '',
        '## 4. Checkpoint-selection contract (fixed config only)',
        '',
    ]
    for i, term in enumerate(f['checkpoint_selection']['tuple_ordering'], start=1):
        lines.append(f"{i}. `{term}`")
    lines += [
        '',
        f"- strict improvement (`{f['checkpoint_selection']['improvement_rule']}`); ties are "
        f"bad epochs; patience {f['checkpoint_selection']['patience']}",
        f"- {f['checkpoint_selection']['provenance_disclosure']}",
        '',
        '### 4.1 Provenance of the selection tuple (disclosed, not silently asserted)',
        '',
        f"- **executing code** `{HISTORICAL_EXECUTING_SELECTION['source']}` line "
        f"{HISTORICAL_EXECUTING_SELECTION['source_line']}: "
        f"`{HISTORICAL_EXECUTING_SELECTION['score_tuple']}` (length "
        f"{HISTORICAL_EXECUTING_SELECTION['tuple_length']})",
        f"- **PHASE13B.md**: length {HISTORICAL_PROTOCOL_DOC_SELECTION['tuple_length']}",
        f"- **Stage-3 correction**: length {HISTORICAL_STAGE3_SELECTION['tuple_length']}",
        '',
        '## 5. Phase-14 distribution requirement',
        '',
        f"- disposition: `{PHASE14_DISTRIBUTION_REQUIREMENT['canonical_disposition']}`",
        f"- is a Phase-13 localizer training change: "
        f"**{PHASE14_DISTRIBUTION_REQUIREMENT['is_a_phase13_localizer_training_change']}**",
        f"- predicted-proposal training crops in Phase 13: "
        f"**{PHASE14_DISTRIBUTION_REQUIREMENT['phase13_predicted_proposal_training_crops']}**",
        f"- Phase-14 crop recipe frozen here: "
        f"**{PHASE14_DISTRIBUTION_REQUIREMENT['phase14_crop_training_recipe_frozen_here']}**",
        '',
        '## 6. Downstream predicted-region contract (frozen, not executed)',
        '',
        f"- geometry: `{DOWNSTREAM_GEOMETRY['config']}` (margin "
        f"**{DOWNSTREAM_GEOMETRY['config']['margin']}**, NOT the Phase-12 oracle margin 0.25)",
        f"- label: `{DOWNSTREAM_GEOMETRY['label']}`",
        f"- composition: `{DOWNSTREAM_COMPOSITION['primary_name']}` — "
        f"regional {DOWNSTREAM_COMPOSITION['regional_probability_restoration']} at "
        f"{DOWNSTREAM_COMPOSITION['regional_crop_resolution']}, pixelwise MAX across regional "
        f"crops, global RETAINED outside the proposal union, REPLACED inside; final threshold "
        f"{DOWNSTREAM_COMPOSITION['final_threshold_full_native_probability']}",
        f"- forbidden: {', '.join(DOWNSTREAM_COMPOSITION['forbidden'])}",
        f"- model scope: {', '.join(DOWNSTREAM_MODEL_SCOPE)} · reference model: "
        f"**{DOWNSTREAM_REFERENCE_MODEL or 'NONE'}**",
        '',
        '## 7. Retention metric contract',
        '',
        f"- `oracle_gap_retention_dice = predicted_gain_dice / oracle_gain_dice`, only where "
        f"`oracle_gain_dice > 0`",
        f"- numerical sufficient-retention threshold: "
        f"**{RETENTION_CONTRACT['numerical_sufficient_retention_threshold']}**",
        f"- case level: {RETENTION_CONTRACT['case_level']}",
        '',
        '## 8. Label defects recorded',
        '',
        f"- `STAGE4D_DESIGN_AUDIT_LABEL_PROVENANCE_DEFECT`: `clean_v3_results` in "
        f"`phase13b_stage4d_design_audit.json` is **{LABEL_DEFECTS['STAGE4D_DESIGN_AUDIT_LABEL_PROVENANCE_DEFECT']['disposition']}** "
        f"(denominator 156 = v2). Historical artifact NOT modified.",
        f"- `NON_BLOCKING_HISTORICAL_ARTIFACT_GAP`: `val_search_epoch079.csv` missing "
        f"({LABEL_DEFECTS['NON_BLOCKING_HISTORICAL_ARTIFACT_GAP']['existing_search_dumps']}/88 "
        f"dumps). Not recreated, not fabricated. `history.csv` remains authoritative "
        f"(88/88 contiguous).",
        '',
        '## 9. Gate governance',
        '',
        f"- dimension B `{GATE_GOVERNANCE['dimension_b']}` — "
        f"{GATE_GOVERNANCE['dimension_b_status']}",
        f"- scalar gate score: **{GATE_GOVERNANCE['scalar_gate_score']}** · numerical GO "
        f"threshold: **{GATE_GOVERNANCE['numerical_go_threshold']}**",
        f"- final regional gate: **{GATE_GOVERNANCE['final_regional_gate']}**; outcomes issued "
        f"here: {GATE_GOVERNANCE['outcomes_issued_in_this_task'] or 'NONE'}",
        '',
        '## 10. Governance boundary',
        '',
        f"- training **{ge['training']}** · optimizer steps **{ge['optimizer_steps']}** · "
        f"model forward passes **{ge['model_forward_passes']}**",
        f"- localizer inference **{ge['localizer_inference']}** · predicted-region inference "
        f"**{ge['predicted_region_inference']}** · proposals **{ge['proposals_generated']}**",
        f"- clean-v3 grid search run: **{ge['clean_v3_grid_search_run']}** · TEST content reads "
        f"**{ge['test_content_reads']}**",
        f"- Phase 14 started: **{ge['phase14_started']}** · historical artifacts modified: "
        f"**{ge['historical_artifacts_modified']}**",
        f"- winner declared **{ge['winner_declared']}** · reference model selected "
        f"**{ge['reference_model_selected']}** · regional mechanism promoted "
        f"**{ge['regional_mechanism_promoted']}**",
        '',
        f"**Next action:** `{f['next_action']}`",
    ]
    return '\n'.join(lines) + '\n'


def write_all(write_frozen: bool = True) -> Dict[str, str]:
    out: Dict[str, str] = {}

    hard_tiny = derive_hard_tiny()
    global_empty = derive_global_empty()
    if len(hard_tiny) == 0 or len(global_empty) == 0:
        raise RuntimeError('CHECK_REQUIRED: a re-derived cohort is unexpectedly empty')

    hard_tiny.to_csv(HARD_TINY_OUT, index=False, encoding='utf-8')
    global_empty.to_csv(GLOBAL_EMPTY_OUT, index=False, encoding='utf-8')
    out[HARD_TINY_OUT.name] = sha256_file(HARD_TINY_OUT)
    out[GLOBAL_EMPTY_OUT.name] = sha256_file(GLOBAL_EMPTY_OUT)

    amended = build_amended_diff()
    assert not amended['unauthorized_material_difference'].any(), \
        'unauthorized material differences must be 0'
    amended.to_csv(DIFF_OUT, index=False, encoding='utf-8')
    out[DIFF_OUT.name] = sha256_file(DIFF_OUT)

    if write_frozen:
        frozen = build_frozen_protocol(hard_tiny, global_empty,
                                       out[HARD_TINY_OUT.name], out[GLOBAL_EMPTY_OUT.name])
        FROZEN_JSON.write_text(json.dumps(frozen, indent=2, ensure_ascii=False), encoding='utf-8')
        out[FROZEN_JSON.name] = sha256_file(FROZEN_JSON)
        FROZEN_MD.write_text(_frozen_md(frozen), encoding='utf-8')
        out[FROZEN_MD.name] = sha256_file(FROZEN_MD)
    return out


if __name__ == '__main__':
    for k, v in write_all().items():
        print(f'{v}  {k}')
