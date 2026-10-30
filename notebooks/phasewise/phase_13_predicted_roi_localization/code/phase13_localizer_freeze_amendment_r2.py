"""
Phase 13 Part 1A-R2 — Checkpoint-selection provenance correction (READ-ONLY / NO TRAINING).

Part 1A-R2 records ONE material supervisor correction: the primary clean-v3 checkpoint-selection
tuple is the EXECUTING HISTORICAL 4-term tuple, not the R1 8-term supervisor extension. Every
other R1 decision remains frozen.

Forbidden here: training, optimizer instantiation for training, model forward inference,
proposal generation, clean-v3 localizer evaluation, predicted-region segmentation, the
20-config grid, Part 1B, Phase 14, TEST access.

The R1 frozen artifact is preserved untouched and is superseded for execution purposes only.

Author: WorkBuddy AI (Agent mode)
Date: 2026-09-21
"""
from __future__ import annotations

import copy
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
for p in (str(PROJECT_ROOT), str(CODE_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import phase13_localizer_freeze_amendment as r1  # noqa: E402  (R1 read-only support module)

# ---------------------------------------------------------------------------
# Frozen identities
# ---------------------------------------------------------------------------
PART1A_NOTEBOOK = (PROJECT_ROOT / 'notebooks/phasewise/phase_13_predicted_roi_localization'
                   / 'phase13_clean_v3_localizer_protocol_freeze.ipynb')
PART1A_NOTEBOOK_SHA = '68f787e1f70fcf706442b342e62cc615eeb347653e753149987becf793ac2bd0'
R1_NOTEBOOK = (PROJECT_ROOT / 'notebooks/phasewise/phase_13_predicted_roi_localization'
               / 'phase13_clean_v3_localizer_supervisor_freeze_amendment.ipynb')
R1_NOTEBOOK_SHA = '6a08d6bd43e173f4b8b646d130fdabca0e95f3466b5caf0a91323cc52d34a622'
R1_FROZEN_JSON = AUDITS / 'phase13_clean_v3_localizer_protocol_frozen.json'
R1_FROZEN_JSON_SHA = '999144bbad4af4e1d2dc006279aef1a5fb93f450006ae2c5db159c791c913703'
R1_FROZEN_MD = AUDITS / 'phase13_clean_v3_localizer_protocol_frozen.md'

R2_FROZEN_JSON = AUDITS / 'phase13_clean_v3_localizer_protocol_frozen_r2.json'
R2_FROZEN_MD = AUDITS / 'phase13_clean_v3_localizer_protocol_frozen_r2.md'
R2_DIFF = TABLES / 'phase13_r1_to_r2_protocol_diff.csv'

R1_STATUS_FOR_EXECUTION = 'SUPERSEDED_BY_SUPERVISOR_R2_CHECKPOINT_SELECTION_CORRECTION'
R2_STATUS = 'SUPERVISOR_FROZEN_R2_READY_FOR_PART1B_TRAINING'

EXECUTING_TRAINER = 'scripts/training/train_phase13b_localizer.py'
EXECUTING_TRAINER_LINE = 164

# --- §2 final primary checkpoint-selection contract (executing historical tuple) ---
PRIMARY_CHECKPOINT_TUPLE = ['tiny_recall90', 'overall_recall90',
                            '-mean_roi_area_fraction', '-val_loss']
PRIMARY_CHECKPOINT_TUPLE_LABEL = 'EXECUTING_HISTORICAL_4TERM_FIXED_CONFIG_SELECTION'
PRIMARY_CHECKPOINT_SELECTION = {
    'label': PRIMARY_CHECKPOINT_TUPLE_LABEL,
    'role': 'PRIMARY',
    'tuple': PRIMARY_CHECKPOINT_TUPLE,
    'tuple_length': len(PRIMARY_CHECKPOINT_TUPLE),
    'provenance': 'HISTORICAL EXECUTING CODE',
    'provenance_source': EXECUTING_TRAINER,
    'provenance_line': EXECUTING_TRAINER_LINE,
    'comparison': 'STRICT_LEXICOGRAPHIC_GREATER_THAN',
    'improvement_rule': 'new_score > best_score (strict tuple comparison)',
    'ties': 'BAD_EPOCH',
    'patience': 15,
    'checkpoint_save': {
        'best_pt': 'only on strict tuple improvement',
        'latest_pt': 'every completed epoch, per the reconstructed trainer ordering',
    },
    'checkpoint_metadata_must_store': ['the COMPLETE tuple', 'the tuple term names'],
    'evaluated_at': 'ONE FIXED PROPOSAL CONFIGURATION ONLY (0.10 / 0.20 / 5 / 0.30)',
    'zero_denominator_rule': 'STOP / CHECK_REQUIRED BEFORE TRAINING',
    'per_epoch_proposal_grid_search': 'DISABLED',
}

# --- §4 diagnostics: computed/logged, but excluded from primary selection ---
DIAGNOSTIC_METRICS = {
    'hard_tiny_recovered90': 'SECONDARY_DIAGNOSTIC_NOT_SELECTION_TERM',
    'global_empty_images_covered90': 'SECONDARY_DIAGNOSTIC_NOT_SELECTION_TERM',
    'multi_component_recall90': 'SECONDARY_DIAGNOSTIC_NOT_SELECTION_TERM',
    'mean_proposals_per_image': 'SECONDARY_DIAGNOSTIC_NOT_SELECTION_TERM',
}
DIAGNOSTIC_METRICS_NOTE = (
    'These remain valuable and SHOULD be computed/logged per epoch when physically available. '
    'They MUST NOT participate in primary checkpoint selection. mean_proposals_per_image '
    'appeared in the R1 8-term extension but not in the executing 4-term tuple; it is preserved '
    'as a diagnostic only.')

# --- §5 hard sets: frozen, now secondary diagnostic cohorts ---
HARD_SET_ROLE_R2 = 'PRE_FROZEN_SECONDARY_DIAGNOSTIC_COHORT'
HARD_SET_USEFUL_FOR = ['localization analysis', 'difficult-case analysis', 'historical comparison']

# --- §6 recorded rationale ---
R2_RATIONALE = {
    'A': 'Checkpoint selection is a material scientific parameter.',
    'B': 'The executing historical trainer is higher-authority evidence than prose documentation.',
    'C': 'Using the executing 4-term tuple minimizes unnecessary v2->v3 protocol drift.',
    'D': 'The R1 8-term extension would make primary checkpoint selection depend partly on hard '
         'cohorts derived using the UNet++ historical-replication anchor.',
    'E': 'UNet++ is NOT a Phase-13 reference model.',
    'F': 'Keeping those fields as diagnostics preserves their analytical value without allowing '
         'them to bias primary checkpoint selection.',
}

# --- §15 additive R1 -> R2 diff ---
R1_TO_R2_ROWS = [
    ('checkpoint_selection_tuple',
     '8-term supervisor extension: (hard_tiny_recovered90, global_empty_images_covered90, '
     'tiny_recall90, overall_recall90, multi_component_recall90, -mean_roi_area_fraction, '
     '-mean_proposals_per_image, -val_loss)',
     '4-term executing historical tuple: (tiny_recall90, overall_recall90, '
     '-mean_roi_area_fraction, -val_loss)',
     'CHANGED', True, True, 'M1',
     'EXECUTING_CODE_PRECEDENCE_AND_MINIMIZE_PROTOCOL_DRIFT'),
    ('hard_set_selection_role',
     'checkpoint-selection terms',
     'SECONDARY_DIAGNOSTIC_NOT_SELECTION_TERM (pre-frozen secondary diagnostic cohorts)',
     'CHANGED', False, True, 'M1',
     'CONSEQUENCE_OF_THE_SINGLE_AUTHORIZED_MATERIAL_CHANGE (checkpoint_selection_tuple)'),
    ('proposal_configuration', '0.10 / 0.20 / 5 / 0.30', '0.10 / 0.20 / 5 / 0.30',
     'SAME', False, False, '', 'UNCHANGED_FROM_R1'),
    ('primary_grid_search', 'DISABLED', 'DISABLED', 'SAME', False, False, '',
     'UNCHANGED_FROM_R1'),
    ('historical_20_grid', 'DEFERRED_SECONDARY_SENSITIVITY_ONLY',
     'DEFERRED_SECONDARY_SENSITIVITY_ONLY', 'SAME', False, False, '', 'UNCHANGED_FROM_R1'),
    ('heatmap_resolution_contract', '512x512 -> 128x128, heatmap_resolution=128 explicit, '
     'fail-loud shape assertions',
     '512x512 -> 128x128, heatmap_resolution=128 explicit, fail-loud shape assertions',
     'SAME', False, False, '', 'UNCHANGED_FROM_R1'),
    ('architecture', 'KUBLocalizer compact 3-stage U-Net, base_channels 16',
     'KUBLocalizer compact 3-stage U-Net, base_channels 16', 'SAME', False, False, '',
     'UNCHANGED_FROM_R1'),
    ('target_generation', 'Gaussian, pixelwise MAX, nearest integer pixel forced to 1.0, '
     'sigma 0.75 in 128-space',
     'Gaussian, pixelwise MAX, nearest integer pixel forced to 1.0, sigma 0.75 in 128-space',
     'SAME', False, False, '', 'UNCHANGED_FROM_R1'),
    ('loss', '0.75 CenterNet focal (alpha 0.25, gamma 2.0) + 0.25 soft Dice',
     '0.75 CenterNet focal (alpha 0.25, gamma 2.0) + 0.25 soft Dice',
     'SAME', False, False, '', 'UNCHANGED_FROM_R1'),
    ('optimizer', 'AdamW lr 1e-4, weight_decay 1e-4', 'AdamW lr 1e-4, weight_decay 1e-4',
     'SAME', False, False, '', 'UNCHANGED_FROM_R1'),
    ('scheduler', 'CosineAnnealingLR, T_max 100', 'CosineAnnealingLR, T_max 100',
     'SAME', False, False, '', 'UNCHANGED_FROM_R1'),
    ('seed', '42', '42', 'SAME', False, False, '', 'UNCHANGED_FROM_R1'),
    ('population', 'phase4_v3 FULL_FIELD TRAIN 770/1161, VAL 103/152, ROI excluded',
     'phase4_v3 FULL_FIELD TRAIN 770/1161, VAL 103/152, ROI excluded',
     'SAME', False, False, '', 'UNCHANGED_FROM_R1'),
    ('epochs_patience_augmentation', 'max_epochs 100, patience 15, AMP, TRAIN augmentation '
     'unchanged',
     'max_epochs 100, patience 15, AMP, TRAIN augmentation unchanged',
     'SAME', False, False, '', 'UNCHANGED_FROM_R1'),
    ('downstream_composition', 'PREDICTED_REGION_FLOAT_GLOBAL_RETAINED, margin 0.20, '
     '512 crop, FLOAT_BILINEAR, pixelwise MAX, global retained outside, threshold 0.5',
     'PREDICTED_REGION_FLOAT_GLOBAL_RETAINED, margin 0.20, 512 crop, FLOAT_BILINEAR, '
     'pixelwise MAX, global retained outside, threshold 0.5',
     'SAME', False, False, '', 'UNCHANGED_FROM_R1'),
    ('downstream_model_scope', 'UNet, Attention U-Net, UNet++, DeepLabV3+; no reference model',
     'UNet, Attention U-Net, UNet++, DeepLabV3+; no reference model',
     'SAME', False, False, '', 'UNCHANGED_FROM_R1'),
    ('retention_metric', 'PRACTICAL_GT_FREE_ORACLE_BENEFIT_RETENTION; ratio only where '
     'oracle_gain > 0; no sufficiency threshold',
     'PRACTICAL_GT_FREE_ORACLE_BENEFIT_RETENTION; ratio only where oracle_gain > 0; '
     'no sufficiency threshold', 'SAME', False, False, '', 'UNCHANGED_FROM_R1'),
    ('gate_governance', 'dimension B candidate; no scalar score; no GO threshold; NOT_DECIDED',
     'dimension B candidate; no scalar score; no GO threshold; NOT_DECIDED',
     'SAME', False, False, '', 'UNCHANGED_FROM_R1'),
    ('test_lock', 'TEST locked; content reads 0', 'TEST locked; content reads 0',
     'SAME', False, False, '', 'UNCHANGED_FROM_R1'),
]

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
    'r1_artifacts_modified': False,
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
# §15 additive diff table
# ---------------------------------------------------------------------------
def build_r1_to_r2_diff() -> pd.DataFrame:
    rows = []
    for field, r1v, r2v, change, material, authorized, group, reason in R1_TO_R2_ROWS:
        rows.append({
            'field': field, 'r1_value': r1v, 'r2_value': r2v, 'change': change,
            'scientifically_material': bool(material), 'authorized': bool(authorized),
            'material_change_group': group, 'reason': reason,
            'unauthorized_material_difference': False,
        })
    return pd.DataFrame(rows)


def diff_counts(df: pd.DataFrame) -> Dict[str, int]:
    changed = df['change'] == 'CHANGED'
    material = changed & df['scientifically_material']
    return {
        'r1_to_r2_material_differences': int(material.sum()),
        'authorized_material_differences': int((material & df['authorized']).sum()),
        'unauthorized_material_differences': int(df['unauthorized_material_difference'].sum()),
        'changed_fields': int(changed.sum()),
        'unchanged_fields': int((df['change'] == 'SAME').sum()),
    }


# ---------------------------------------------------------------------------
# §13 R2 canonical frozen protocol
# ---------------------------------------------------------------------------
# Top-level keys that R2 is allowed to differ from R1 on. Anything else differing is a bug.
EXPECTED_CHANGED_KEYS = {
    'part', 'document_type', 'status', 'task', 'authorization', 'checkpoint_selection',
    'checkpoint_selection_r1', 'checkpoint_selection_provenance', 'hard_sets',
    'diagnostic_metrics', 'r1_supersession', 'r2_rationale', 'sources', 'governance',
    'pass_gate', 'diff_from_r1', 'next_action',
}


def build_r2_protocol() -> Dict[str, Any]:
    r1_frozen = json.loads(R1_FROZEN_JSON.read_text(encoding='utf-8'))
    r2 = copy.deepcopy(r1_frozen)

    r2['part'] = '1A-R2'
    r2['document_type'] = 'CLEAN_V3_LOCALIZER_PROTOCOL_FROZEN_R2'
    r2['status'] = R2_STATUS
    r2['task'] = 'CHECKPOINT_SELECTION_PROVENANCE_CORRECTION'

    auth = dict(r1_frozen['authorization'])
    auth['part1a'] = 'COMPLETE'
    auth['part1a_r1'] = 'EXECUTION PASS'
    auth['part1a_r2'] = 'AUTHORIZED (this task)'
    auth['part1b'] = 'ELIGIBLE_FOR_SUPERVISOR_AUTHORIZATION'
    auth['part1b_authorized'] = False
    r2['authorization'] = auth

    # R1 selection retained as provenance only
    r2['checkpoint_selection_r1'] = {
        'role': 'SUPERSEDED_FOR_PRIMARY_CHECKPOINT_SELECTION',
        'preserved_as': 'PROVENANCE',
        'tuple': r1_frozen['checkpoint_selection']['tuple_ordering'],
        'tuple_length': r1_frozen['checkpoint_selection']['tuple_length'],
        'note': 'The R1 8-term supervisor extension is superseded for primary checkpoint '
                'selection by the R2 executing historical 4-term tuple. It remains recorded '
                'here and in the preserved R1 artifact.',
    }
    r2['checkpoint_selection'] = PRIMARY_CHECKPOINT_SELECTION

    prov = dict(r1_frozen['checkpoint_selection_provenance'])
    prov['r2_resolution'] = (
        'R2 corrects the primary selection rule to the executing 4-term tuple. '
        'HISTORICAL_EXECUTING_SELECTION is now the PRIMARY rule; '
        'HISTORICAL_PROTOCOL_DOC_SELECTION (8-term) and HISTORICAL_STAGE3_SELECTION (3-term) '
        'remain recorded as non-executing documentation.')
    r2['checkpoint_selection_provenance'] = prov

    hard_sets = copy.deepcopy(r1_frozen['hard_sets'])
    hard_sets['role'] = HARD_SET_ROLE_R2
    hard_sets['useful_for'] = HARD_SET_USEFUL_FOR
    hard_sets['participates_in_primary_checkpoint_selection'] = False
    hard_sets['anchor_role'] = 'HISTORICAL_PHASE13_HARDSET_REPLICATION_ANCHOR_ONLY'
    r2['hard_sets'] = hard_sets

    r2['diagnostic_metrics'] = {
        'labels': DIAGNOSTIC_METRICS,
        'note': DIAGNOSTIC_METRICS_NOTE,
        'participate_in_primary_checkpoint_selection': False,
    }

    r2['r1_supersession'] = {
        'r1_artifact': str(R1_FROZEN_JSON.relative_to(PROJECT_ROOT)).replace('\\', '/'),
        'r1_artifact_sha256': _sha(R1_FROZEN_JSON),
        'r1_artifact_sha256_expected': R1_FROZEN_JSON_SHA,
        'r1_artifact_unchanged': _sha(R1_FROZEN_JSON) == R1_FROZEN_JSON_SHA,
        'r1_md_artifact': str(R1_FROZEN_MD.relative_to(PROJECT_ROOT)).replace('\\', '/'),
        'r1_status_for_execution': R1_STATUS_FOR_EXECUTION,
        'r1_artifact_modified': False,
        'scope_of_supersession': 'ONLY the R1 8-term checkpoint-selection rule; all other R1 '
                                 'decisions remain frozen',
        'future_part1b_must_use': str(R2_FROZEN_JSON.relative_to(PROJECT_ROOT)).replace('\\', '/'),
    }
    r2['r2_rationale'] = R2_RATIONALE

    sources = copy.deepcopy(r1_frozen['sources'])
    sources['part1a_notebook']['sha256'] = _sha(PART1A_NOTEBOOK)
    sources['part1a_notebook']['unchanged'] = _sha(PART1A_NOTEBOOK) == PART1A_NOTEBOOK_SHA
    sources['r1_amendment_notebook'] = {
        'path': str(R1_NOTEBOOK.relative_to(PROJECT_ROOT)).replace('\\', '/'),
        'sha256': _sha(R1_NOTEBOOK),
        'expected_sha256': R1_NOTEBOOK_SHA,
        'unchanged': _sha(R1_NOTEBOOK) == R1_NOTEBOOK_SHA,
    }
    sources['r1_frozen_protocol'] = {
        'path': str(R1_FROZEN_JSON.relative_to(PROJECT_ROOT)).replace('\\', '/'),
        'sha256': _sha(R1_FROZEN_JSON),
        'expected_sha256': R1_FROZEN_JSON_SHA,
        'unchanged': _sha(R1_FROZEN_JSON) == R1_FROZEN_JSON_SHA,
    }
    sources['executing_trainer'] = {
        'path': EXECUTING_TRAINER,
        'line': EXECUTING_TRAINER_LINE,
        'sha256': _sha(PROJECT_ROOT / EXECUTING_TRAINER),
    }
    r2['sources'] = sources

    r2['governance'] = GOVERNANCE

    r2['pass_gate'] = {
        'r1_provenance_preserved': True,
        'r2_uses_executing_historical_4term_tuple': True,
        'fixed_proposal_config_retained': True,
        'primary_grid_search_remains_disabled': True,
        'hard_sets_retained_but_removed_from_checkpoint_selection': True,
        'hard_set_diagnostic_role_clearly_labelled': True,
        'unetpp_remains_replication_anchor_only': True,
        'heatmap_512_to_128_contract_unchanged': True,
        'scientific_core_otherwise_unchanged': True,
        'downstream_predicted_region_contract_unchanged': True,
        'no_training': True,
        'no_inference': True,
        'test_reads_zero': True,
        'part1b_not_authorized': True,
        'unauthorized_material_differences': 0,
    }

    diff = build_r1_to_r2_diff()
    counts = diff_counts(diff)
    r2['diff_from_r1'] = {
        'table': str(R2_DIFF.relative_to(PROJECT_ROOT)).replace('\\', '/'),
        'table_sha256': _sha(R2_DIFF),
        **counts,
    }
    r2['next_action'] = 'WAIT_FOR_SUPERVISOR_PHASE13_PART1B_TRAINING_AUTHORIZATION'
    return r2


def verify_only_expected_keys_changed(r2: Dict[str, Any]) -> List[str]:
    r1_frozen = json.loads(R1_FROZEN_JSON.read_text(encoding='utf-8'))
    changed = {k for k in set(r1_frozen) | set(r2) if r1_frozen.get(k) != r2.get(k)}
    unexpected = sorted(changed - EXPECTED_CHANGED_KEYS)
    return unexpected


# ---------------------------------------------------------------------------
# R2 markdown
# ---------------------------------------------------------------------------
def _r2_md(f: Dict[str, Any]) -> str:
    cs = f['checkpoint_selection']
    hs, ge = f['hard_sets'], f['governance']
    lines = [
        '# Phase 13 Part 1A-R2 — Clean-v3 Localizer Protocol (SUPERVISOR FROZEN R2)',
        '',
        f"- Status: **{f['status']}**",
        f"- Phase/part: `{f['phase']}` / `{f['part']}` · Model: {f['model']}",
        f"- Manifest `{f['manifest_version']}` · taxonomy `{f['taxonomy']}`",
        '',
        '## 1. Primary checkpoint-selection contract (CORRECTED)',
        '',
        f"- label: **`{cs['label']}`** · role: **{cs['role']}**",
        f"- provenance: **{cs['provenance']}** "
        f"(`{cs['provenance_source']}` line {cs['provenance_line']})",
        '',
        '```',
        '(',
    ]
    for t in cs['tuple']:
        lines.append(f'    {t},')
    lines += [
        ')',
        '```',
        '',
        f"- length **{cs['tuple_length']}** · comparison **{cs['comparison']}** · ties "
        f"**{cs['ties']}** · patience **{cs['patience']}**",
        f"- `best.pt`: {cs['checkpoint_save']['best_pt']}",
        f"- `latest.pt`: {cs['checkpoint_save']['latest_pt']}",
        f"- checkpoint metadata must store: {', '.join(cs['checkpoint_metadata_must_store'])}",
        f"- evaluated at: {cs['evaluated_at']}",
        '',
        '### 1.1 R1 tuple retained as provenance only',
        '',
        f"- R1 8-term tuple status: **{f['checkpoint_selection_r1']['role']}** "
        f"({f['checkpoint_selection_r1']['preserved_as']})",
        '',
        '## 2. Fixed proposal configuration (UNCHANGED from R1)',
        '',
        f"- threshold **{f['proposal_configuration']['threshold']}** · margin "
        f"**{f['proposal_configuration']['margin']}** · top_k "
        f"**{f['proposal_configuration']['top_k']}** · nms_iou "
        f"**{f['proposal_configuration']['nms_iou']}**",
        f"- clean-v3 primary grid search: **{f['proposal_configuration']['clean_v3_primary_grid_search']}**",
        f"- historical 20-grid: `{f['proposal_configuration']['historical_20_grid']}`",
        '',
        '## 3. Diagnostic metrics (computed, NOT selection terms)',
        '',
    ]
    for k, v in f['diagnostic_metrics']['labels'].items():
        lines.append(f"- `{k}`: **{v}**")
    lines += ['', f['diagnostic_metrics']['note'], '',
              '## 4. Hard sets (frozen; now secondary diagnostic cohorts)', '',
              f"- hard_tiny: **{hs['hard_tiny']['count']}** · `{hs['hard_tiny']['sha256']}`",
              f"- global_empty: **{hs['global_empty']['count']}** · "
              f"`{hs['global_empty']['sha256']}`",
              f"- role: **{hs['role']}** · participates in primary selection: "
              f"**{hs['participates_in_primary_checkpoint_selection']}**",
              f"- anchor: **UNet++** = `{hs['anchor_role']}`",
              f"- useful for: {', '.join(hs['useful_for'])}",
              f"- must NOT replace the gate cohorts: "
              f"{', '.join(hs['must_not_replace_gate_cohorts'])}",
              '',
              '## 5. Heatmap contract (UNCHANGED from R1)', '',
              f"- input **{f['heatmap_contract']['input']}** → output heatmap "
              f"**{f['heatmap_contract']['output_heatmap']}**",
              f"- `heatmap_resolution={f['heatmap_contract']['heatmap_resolution']}`, always "
              f"explicit; fail-loud shape assertions required",
              f"- preferred remediation **{f['heatmap_contract']['preferred_remediation']}** "
              f"(clean-v3-safe wrapper); historical generic helper NOT altered",
              '',
              '## 6. R1 supersession relationship', '',
              f"- R1 artifact: `{f['r1_supersession']['r1_artifact']}` "
              f"`{f['r1_supersession']['r1_artifact_sha256']}`",
              f"- R1 status for execution: **{f['r1_supersession']['r1_status_for_execution']}**",
              f"- R1 artifact modified: **{f['r1_supersession']['r1_artifact_modified']}** "
              f"(preserved for provenance)",
              f"- scope: {f['r1_supersession']['scope_of_supersession']}",
              f"- future Part 1B must use: `{f['r1_supersession']['future_part1b_must_use']}`",
              '',
              '## 7. Recorded rationale', '']
    for k, v in f['r2_rationale'].items():
        lines.append(f"{k}. {v}")
    lines += [
        '',
        '## 8. R1 → R2 diff',
        '',
        f"- table: `{f['diff_from_r1']['table']}` `{f['diff_from_r1']['table_sha256']}`",
        f"- material differences **{f['diff_from_r1']['r1_to_r2_material_differences']}** · "
        f"authorized **{f['diff_from_r1']['authorized_material_differences']}** · "
        f"unauthorized **{f['diff_from_r1']['unauthorized_material_differences']}**",
        f"- changed fields **{f['diff_from_r1']['changed_fields']}** · unchanged fields "
        f"**{f['diff_from_r1']['unchanged_fields']}**",
        '',
        '## 9. Downstream contract (UNCHANGED from R1)',
        '',
        f"- primary: `{f['downstream_composition']['primary_name']}` · geometry margin "
        f"**{f['downstream_geometry']['config']['margin']}** (oracle comparator 0.25)",
        f"- label: `{f['downstream_geometry']['label']}`",
        f"- model scope: {', '.join(f['downstream_model_scope'])} · reference model: **NONE**",
        f"- retention: `oracle_gap_retention_dice = predicted_gain_dice / oracle_gain_dice`, "
        f"only where `oracle_gain_dice > 0`; no sufficiency threshold",
        f"- gate: **{f['gate_governance']['final_regional_gate']}**; no GO / REVISE_LOCALIZER / "
        f"NO_GO issued",
        '',
        '## 10. Governance boundary',
        '',
        f"- training **{ge['training']}** · optimizer steps **{ge['optimizer_steps']}** · "
        f"forward passes **{ge['model_forward_passes']}**",
        f"- localizer inference **{ge['localizer_inference']}** · predicted-region inference "
        f"**{ge['predicted_region_inference']}** · proposals **{ge['proposals_generated']}**",
        f"- TEST content reads **{ge['test_content_reads']}** · Phase 14 started "
        f"**{ge['phase14_started']}** · R1 artifacts modified "
        f"**{ge['r1_artifacts_modified']}** · historical artifacts modified "
        f"**{ge['historical_artifacts_modified']}**",
        '',
        f"**Next action:** `{f['next_action']}`",
    ]
    return '\n'.join(lines) + '\n'


def write_all(write_frozen: bool = True) -> Dict[str, str]:
    out: Dict[str, str] = {}

    diff = build_r1_to_r2_diff()
    counts = diff_counts(diff)
    if counts['unauthorized_material_differences'] != 0:
        raise RuntimeError('CHECK_REQUIRED: unauthorized material differences present')
    if counts['r1_to_r2_material_differences'] != 1:
        raise RuntimeError('CHECK_REQUIRED: expected exactly one material difference')
    diff.to_csv(R2_DIFF, index=False, encoding='utf-8')
    out[R2_DIFF.name] = sha256_file(R2_DIFF)

    if write_frozen:
        r2 = build_r2_protocol()
        unexpected = verify_only_expected_keys_changed(r2)
        if unexpected:
            raise RuntimeError(f'CHECK_REQUIRED: unexpected protocol drift in keys {unexpected}')
        R2_FROZEN_JSON.write_text(json.dumps(r2, indent=2, ensure_ascii=False), encoding='utf-8')
        out[R2_FROZEN_JSON.name] = sha256_file(R2_FROZEN_JSON)
        R2_FROZEN_MD.write_text(_r2_md(r2), encoding='utf-8')
        out[R2_FROZEN_MD.name] = sha256_file(R2_FROZEN_MD)
    return out


if __name__ == '__main__':
    for k, v in write_all().items():
        print(f'{v}  {k}')
