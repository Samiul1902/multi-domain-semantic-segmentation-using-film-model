"""
Phase 12 Part 1A — Historical oracle-protocol reconstruction + CLEAN-v3 prospective
protocol-freeze candidate support (READ-ONLY).

Part 1A is a PROTOCOL / DEFINITION phase. It does NOT run the clean-v3 oracle experiment.

Forbidden here: oracle inference, training, checkpoint/history/config/manifest changes,
TEST access, Phase 13, Phases 14-18, RA-MedFiLM implementation, winner or single-reference
architecture selection.

Historical facts are reconstructed from repository artifacts using the source-precedence
ladder:
  1. executing source code      -> src/analysis/oracle_roi.py,
                                   scripts/analysis/execute_phase12_oracle.py
  2. persisted audit/table      -> reports/audits/phase12_oracle_roi_upper_bound.json,
                                   reports/tables/phase12_oracle_*.csv
  3. executed historical notebook -> notebooks/phasewise/phase_12_oracle_roi/...
  4. frozen report/README       -> notebooks/phasewise/phase_12_oracle_roi/README.md
  5. prose/comment

Author: Gemini 3.1 Pro High
Date: 2026-09-21
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

PROJECT_ROOT = Path(r'D:\Softfors\jup')
REPORTS = PROJECT_ROOT / 'reports'
TABLES = REPORTS / 'tables'
AUDITS = REPORTS / 'audits'

# Historical (v2) artifacts
H_NOTEBOOK = PROJECT_ROOT / 'notebooks/phasewise/phase_12_oracle_roi/phase12_oracle_roi_upper_bound_analysis.ipynb'
H_README = PROJECT_ROOT / 'notebooks/phasewise/phase_12_oracle_roi/README.md'
H_MODULE = PROJECT_ROOT / 'src/analysis/oracle_roi.py'
H_EXEC = PROJECT_ROOT / 'scripts/analysis/execute_phase12_oracle.py'
H_AUDIT = AUDITS / 'phase12_oracle_roi_upper_bound.json'
H_SUMMARY = TABLES / 'phase12_oracle_roi_summary.csv'
H_GEOMETRY = TABLES / 'phase12_oracle_crop_geometry.csv'
H_PER_IMAGE = TABLES / 'phase12_oracle_roi_per_image.csv'
H_PER_COMPONENT = TABLES / 'phase12_oracle_roi_per_component.csv'
H_SIZE_RECOVERY = TABLES / 'phase12_oracle_roi_size_recovery.csv'
H_MULTI = TABLES / 'phase12_oracle_roi_multicomponent.csv'
H_PANEL_SEL = PROJECT_ROOT / 'reports/qualitative/phase12_oracle_roi/phase12_oracle_panel_selection.json'
H_CACHE_PROV = PROJECT_ROOT / 'data_cache/phase12_oracle_roi/provenance.json'

# Clean-v3 frozen inputs
CLEAN_V3_MODELS = ['unet', 'attention_unet', 'unetpp', 'deeplabv3plus']
MODEL_DISPLAY = {'unet': 'UNet', 'attention_unet': 'Attention U-Net',
                 'unetpp': 'UNet++', 'deeplabv3plus': 'DeepLabV3+'}

# Phase-11 frozen bridge values (clean-v3)
PHASE11_ALL_FOUR_LOW = 12
PHASE11_HARD_COHORT = 16
PHASE11_TOP_DISAGREEMENT = 4
PHASE11_REGIME = {'FULL_FIELD': 103, 'ROI': 177}
PHASE11_FULLFIELD_MEAN_DICE = {'UNet': 0.596460, 'Attention U-Net': 0.631730,
                               'UNet++': 0.645474, 'DeepLabV3+': 0.559086}
PHASE11_ROI_MEAN_DICE = {'UNet': 0.824499, 'Attention U-Net': 0.822799,
                         'UNet++': 0.833225, 'DeepLabV3+': 0.862543}
PHASE11_MULTICOMPONENT_CASES = 49
PHASE11_EMPTY = {'UNet': 8, 'Attention U-Net': 3, 'UNet++': 6, 'DeepLabV3+': 11}
PHASE11_OBJECT_RECALL = {'UNet': 0.896341, 'Attention U-Net': 0.923780,
                         'UNet++': 0.914634, 'DeepLabV3+': 0.881098}

TAXONOMY_CLEAN = 'kub_size_clean_v3_v1'
TAXONOMY_HIST = 'kub_size_v1'
MANIFEST_CLEAN = 'phase4_v3'
MANIFEST_HIST = 'phase4_v2'

# Frozen clean-v3 upstream epoch tables (read-only appendix)
PHASE10_EPOCH_TABLES = {
    'unet': TABLES / 'phase10_final_epoch_results_unet.csv',
    'attention_unet': TABLES / 'phase10_final_epoch_results_attention_unet.csv',
    'unetpp': TABLES / 'phase10_final_epoch_results_unetpp.csv',
    'deeplabv3plus': TABLES / 'phase10_final_epoch_results_deeplabv3plus.csv',
}
EXPECTED_EPOCH_ROWS = {'unet': 59, 'attention_unet': 69, 'unetpp': 85, 'deeplabv3plus': 67}


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()


def load_historical_audit() -> Dict[str, Any]:
    return json.loads(H_AUDIT.read_text(encoding='utf-8'))


# ---------------------------------------------------------------------------
# §7 Historical source inventory
# ---------------------------------------------------------------------------

HISTORICAL_SOURCES = [
    ('src/analysis/oracle_roi.py', 'executing_source', 1,
     'Authoritative oracle geometry: extract_gt_components, compute_square_crop, '
     'crop_and_preprocess, restore_crop_probability, fuse_probability_maps, run_oracle_roi_image'),
    ('scripts/analysis/execute_phase12_oracle.py', 'executing_driver', 1,
     'Driver: margins (10,25,50), checkpoint, per-image/per-component/geometry tables'),
    ('reports/audits/phase12_oracle_roi_upper_bound.json', 'persisted_audit', 2,
     'Model, checkpoint SHA, population, oracle definition, metrics, Phase-13 gate'),
    ('reports/tables/phase12_oracle_roi_summary.csv', 'persisted_table', 2,
     'Global vs Oracle 10/25/50 macro metrics and size recalls'),
    ('reports/tables/phase12_oracle_crop_geometry.csv', 'persisted_table', 2,
     'Per-component crop side / magnification per margin'),
    ('reports/tables/phase12_oracle_roi_per_image.csv', 'persisted_table', 2,
     'Per-image global + oracle metrics'),
    ('reports/tables/phase12_oracle_roi_per_component.csv', 'persisted_table', 2,
     'Per-component detection under global vs oracle'),
    ('reports/tables/phase12_oracle_roi_size_recovery.csv', 'persisted_table', 2,
     'Size-stratified recovery'),
    ('reports/tables/phase12_oracle_roi_multicomponent.csv', 'persisted_table', 2,
     'Multi-component oracle behaviour'),
    ('notebooks/phasewise/phase_12_oracle_roi/phase12_oracle_roi_upper_bound_analysis.ipynb',
     'executed_notebook', 3, 'Rendered historical analysis'),
    ('notebooks/phasewise/phase_12_oracle_roi/README.md', 'frozen_readme', 4,
     'Phase-12 prose summary'),
    ('reports/qualitative/phase12_oracle_roi/phase12_oracle_panel_selection.json',
     'qualitative_selection', 2, 'Deterministic qualitative panel selection'),
    ('data_cache/phase12_oracle_roi/provenance.json', 'cache_provenance', 2,
     'Cached oracle probability/mask provenance'),
    ('reports/tables/phase11_clean_v3_phase12_bridge_evidence.csv', 'clean_v3_bridge', 2,
     'Phase-11 -> Phase-12 bridge evidence (clean-v3)'),
]


def build_source_inventory() -> pd.DataFrame:
    rows = []
    for rel, kind, rank, notes in HISTORICAL_SOURCES:
        p = PROJECT_ROOT / rel
        rows.append({'source_path': rel, 'source_type': kind,
                     'sha256': sha256_file(p) if p.exists() else 'N/A',
                     'historical_phase': 12, 'relevance': notes,
                     'authority_rank': rank,
                     'notes': 'present' if p.exists() else 'MISSING'})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# §8 Historical oracle protocol matrix (concepts A..AD from §6)
# ---------------------------------------------------------------------------

# (concept, historical_value, unit, scope, source, status, notes)
PROTOCOL_MATRIX = [
 ('A_model_scope', 'UNet++ only', 'model', 'historical Phase 12',
  'reports/audits/phase12_oracle_roi_upper_bound.json', 'VERIFIED',
  'single architecture; clean-v3 must use ALL FOUR'),
 ('B_checkpoint', 'checkpoints/phase10_kub_unetpp_seed42_512/best.pt',
  'path', 'historical', 'reports/audits/phase12_oracle_roi_upper_bound.json', 'VERIFIED',
  'checkpoint_sha256 4bffcf926227fb11029ead6bcd8e7dd8ed246e0f1678e3efb2ce4297439a3f2d'),
 ('C_manifest_split', 'phase4_v2 · VAL_ONLY', 'manifest', 'historical',
  'reports/audits/phase12_oracle_roi_upper_bound.json', 'VERIFIED',
  'clean-v3 must use phase4_v3'),
 ('D_full_field_only', 'yes (FOV == FULL_FIELD)', 'bool', 'historical',
  'reports/audits/phase12_oracle_roi_upper_bound.json', 'VERIFIED',
  'population 106 images, 156 components'),
 ('E_roi_cases_included', 'no', 'bool', 'historical',
  'reports/audits/phase12_oracle_roi_upper_bound.json', 'VERIFIED',
  'ROI acquisition cases were NOT part of the oracle study'),
 ('F_oracle_unit', 'PER_COMPONENT_BBOX (component-wise)', 'unit', 'historical',
  'src/analysis/oracle_roi.py', 'VERIFIED',
  'one square crop per original-space GT component; never a case/union bbox'),
 ('G_connectivity', '8', 'int', 'original native GT',
  'src/analysis/oracle_roi.py', 'VERIFIED',
  'label(gt, structure=np.ones((3,3)))'),
 ('H_bbox_space', 'ORIGINAL_NATIVE', 'space', 'historical',
  'src/analysis/oracle_roi.py', 'VERIFIED',
  'bbox from native pixel extents; ratio = pixels/(H*W)'),
 ('I_crop_margin_rule', 'fraction of bbox dimension: round(margin * bbox_dim)',
  'fraction', 'historical', 'src/analysis/oracle_roi.py', 'VERIFIED',
  'margins {0.10, 0.25, 0.50}; primary 0.25; applied per axis (m_y, m_x)'),
 ('J_crop_shape', 'SQUARE (side = max(expanded_h, expanded_w), centred)', 'shape',
  'historical', 'src/analysis/oracle_roi.py', 'VERIFIED',
  'aspect ratio is NOT preserved; square is forced around the expanded bbox centre'),
 ('K_min_crop_size', 'none enforced', 'px', 'historical',
  'src/analysis/oracle_roi.py', 'VERIFIED',
  'side derives from bbox+margin; no explicit minimum'),
 ('L_boundary_handling', 'clip to image then zero-pad to side', 'rule', 'historical',
  'src/analysis/oracle_roi.py', 'VERIFIED',
  'clip_{y1,y2,x1,x2} + pad_{top,bottom,left,right} with constant 0'),
 ('M_crop_resolution', '512 x 512', 'px', 'historical',
  'reports/audits/phase12_oracle_roi_upper_bound.json', 'VERIFIED',
  'model_input_shape [1,1,512,512]'),
 ('N_image_interpolation', 'BILINEAR', 'interp', 'historical',
  'src/analysis/oracle_roi.py', 'VERIFIED',
  'crop resize to 512 bilinear; probability restore resize bilinear'),
 ('O_mask_interpolation', 'N/A (GT mask never resized for oracle crops)', 'interp',
  'historical', 'src/analysis/oracle_roi.py', 'VERIFIED',
  'GT evaluated in native space; no mask interpolation in the oracle path'),
 ('P_same_global_model', 'yes (the frozen global UNet++ is reused on crops)', 'bool',
  'historical', 'src/analysis/oracle_roi.py', 'VERIFIED',
  'model(crop_tensor) with the same checkpoint'),
 ('Q_separate_refiner_model', 'no', 'bool', 'historical',
  'src/analysis/oracle_roi.py', 'VERIFIED', 'no regional/refiner model involved'),
 ('R_context_retained', 'yes (margin of surrounding context)', 'bool', 'historical',
  'src/analysis/oracle_roi.py', 'VERIFIED',
  'crop includes a margin beyond the bbox; not a tight crop'),
 ('S_prediction_threshold', '0.5 (applied AFTER fusion)', 'float', 'historical',
  'src/analysis/oracle_roi.py', 'VERIFIED',
  'mask_combined = (prob_combined >= 0.5)'),
 ('T_mapping_back', 'restore prob to (side,side) bilinear, strip pad, place at clip coords '
  'into a zero-initialised full-size array', 'rule', 'historical',
  'src/analysis/oracle_roi.py', 'VERIFIED',
  'restore_crop_probability; note uint8 quantisation before resize (see ambiguity)'),
 ('U_multiple_merge', 'pixelwise MAX of restored component probabilities', 'rule',
  'historical', 'src/analysis/oracle_roi.py', 'VERIFIED',
  'fuse_probability_maps via np.maximum.reduce'),
 ('V_global_outside_crop', 'NOT retained — outside-crop region is 0', 'rule', 'historical',
  'src/analysis/oracle_roi.py', 'VERIFIED',
  'prob_full initialised to zeros; only crop regions are filled'),
 ('W_fusion', 'pixelwise max of restored component probabilities, then threshold',
  'rule', 'historical', 'src/analysis/oracle_roi.py', 'VERIFIED',
  'no overwrite/union/logit fusion'),
 ('X_metrics', 'macro/micro dice, iou, precision, recall; hd95; empty rate; size-stratified '
  'object recall', 'metric', 'historical',
  'reports/tables/phase12_oracle_roi_summary.csv', 'VERIFIED',
  'mask_metrics + hd95 from src/metrics'),
 ('Y_object_recall', 'fraction of original GT components with >=1 overlapping predicted pixel',
  'metric', 'historical', 'scripts/analysis/execute_phase12_oracle.py', 'VERIFIED',
  'detected = bool((mask_combined & (labels==c)).sum())'),
 ('Z_size_taxonomy', 'kub_size_v1 (HISTORICAL)', 'taxonomy', 'historical',
  'reports/tables/phase12_oracle_crop_geometry.csv', 'VERIFIED',
  'clean-v3 must use kub_size_clean_v3_v1'),
 ('AA_hard_case_subgroups', 'size strata TINY/SMALL/MEDIUM/LARGE; multi-component',
  'subgroup', 'historical', 'reports/tables/phase12_oracle_roi_size_recovery.csv', 'VERIFIED',
  'no Phase-11 shared-failure cohort was used historically'),
 ('AB_success_criteria', 'no numeric gate threshold frozen; Phase-13 gate = YES',
  'rule', 'historical', 'reports/audits/phase12_oracle_roi_upper_bound.json', 'VERIFIED',
  'primary margin 0.25 predeclared; gate decided descriptively'),
 ('AC_parameters_predeclared', 'primary margin 0.25 predeclared; margins {0.10,0.25,0.50} '
  'explored', 'bool', 'historical',
  'reports/audits/phase12_oracle_roi_upper_bound.json', 'VERIFIED',
  'no evidence of post-hoc crop tuning beyond the predeclared margin set'),
 ('AD_phase12_to_phase13_rationale',
  'Meaningful FULL_FIELD Dice and TINY-component recovery demonstrates exploitable '
  'localization/resolution headroom; no claim that predicted ROI will reproduce the Oracle gain',
  'rationale', 'historical', 'reports/audits/phase12_oracle_roi_upper_bound.json', 'VERIFIED',
  'gate outcome YES'),
 ('AE_prob_restore_quantisation',
  'restore_crop_probability converts prob to uint8 ((p*255).astype(uint8)) before bilinear '
  'resize', 'rule', 'historical', 'src/analysis/oracle_roi.py', 'AMBIGUOUS',
  'precision loss not mentioned in the audit; clean-v3 should decide explicitly (float restore)'),
 ('AF_fp_comparability',
  'Oracle-constrained FP is artificially advantaged and not fairly comparable to deployable '
  'global inference', 'caveat', 'historical',
  'reports/audits/phase12_oracle_roi_upper_bound.json', 'VERIFIED',
  'recorded fp_caveat'),
 ('AG_readme_prose_conflict',
  'README prose claims "+16.2% Dice and 100% tiny recall"', 'prose', 'historical',
  'notebooks/phasewise/phase_12_oracle_roi/README.md', 'CONFLICT',
  'audit gives macro Dice 0.652776 -> 0.775736 (+12.30 pp) and Tiny_Recall 0.986301 (not 1.0)'),
]


def build_protocol_matrix() -> pd.DataFrame:
    rows = []
    for concept, value, unit, scope, src, status, notes in PROTOCOL_MATRIX:
        p = PROJECT_ROOT / src
        rows.append({'concept': concept, 'historical_value': value, 'unit': unit,
                     'scope': scope, 'source': src,
                     'source_sha': sha256_file(p) if p.exists() else 'N/A',
                     'status': status, 'notes': notes})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# §15/§16 clean-v3 candidate protocol + diff
# ---------------------------------------------------------------------------

# (field, historical_v2, proposed_clean_v3, change_reason, material, supervisor_required)
CANDIDATE = [
 ('oracle_unit', 'PER_COMPONENT_BBOX', 'PER_COMPONENT_BBOX', 'historical design is scientifically valid', False, False),
 ('connectivity', '8', '8', 'unchanged', False, False),
 ('bbox_space', 'ORIGINAL_NATIVE', 'ORIGINAL_NATIVE', 'unchanged', False, False),
 ('crop_margin_rule', 'round(margin * bbox_dim); primary 0.25',
  'round(margin * bbox_dim); primary 0.25 (predeclared)',
  'unchanged; keep predeclared primary margin', False, False),
 ('square_or_aspect_rule', 'SQUARE (side = max(exp_h, exp_w))',
  'SQUARE (side = max(exp_h, exp_w))', 'unchanged', False, False),
 ('min_crop_size', 'none enforced', 'none enforced', 'unchanged', False, False),
 ('boundary_handling', 'clip to image + zero-pad to side',
  'clip to image + zero-pad to side', 'unchanged', False, False),
 ('regional_input_resolution', '512', '512', 'unchanged', False, False),
 ('image_interpolation', 'BILINEAR', 'BILINEAR', 'unchanged', False, False),
 ('mask_interpolation', 'N/A (native GT evaluation)', 'N/A (native GT evaluation)',
  'unchanged', False, False),
 ('mapping_back_rule', 'restore prob to (side,side) bilinear; strip pad; place at clip coords',
  'restore prob to (side,side) bilinear in FLOAT (no uint8 quantisation); strip pad; place at clip coords',
  'removes an undocumented precision loss; improves reproducibility', True, True),
 ('multi_component_rule', 'one square crop per native GT component',
  'one square crop per native GT component', 'unchanged', False, False),
 ('multiple_crop_fusion_rule', 'pixelwise MAX of restored component probabilities',
  'pixelwise MAX of restored component probabilities', 'unchanged', False, False),
 ('global_outside_crop_rule', 'zeros outside crop (global prediction NOT retained)',
  'PROPOSE: retain global prediction outside crop (regional-only inside), reported BOTH ways',
  'historical zeros outside crop makes oracle mask crop-only; clean-v3 should separate the '
  'regional effect from the global baseline it is compared against', True, True),
 ('prediction_threshold', '0.5', '0.5', 'unchanged', False, False),
 ('model_scope', 'UNet++ only', 'ALL FOUR clean-v3 baselines', 'SR-1 requires architecture-general test', True, True),
 ('manifest_version', 'phase4_v2', 'phase4_v3', 'clean governance', False, False),
 ('taxonomy', 'kub_size_v1', 'kub_size_clean_v3_v1', 'clean governance', False, False),
 ('primary_population', 'FULL_FIELD 106 (v2)', 'FULL_FIELD 103 (clean-v3)',
  'clean-v3 population', False, False),
 ('roi_acquisition_cases', 'excluded', 'excluded (observational context only)', 'unchanged', False, False),
]


def build_candidate_protocol() -> pd.DataFrame:
    return pd.DataFrame(CANDIDATE, columns=[
        'field', 'historical_v2', 'proposed_clean_v3', 'change_reason',
        'scientifically_material', 'supervisor_decision_required'])


def build_protocol_diff() -> pd.DataFrame:
    d = build_candidate_protocol().copy()
    d['same_or_changed'] = ['SAME' if h == p else 'CHANGED'
                            for h, p in zip(d['historical_v2'], d['proposed_clean_v3'])]
    return d[['field', 'historical_v2', 'proposed_clean_v3', 'same_or_changed',
              'change_reason', 'scientifically_material', 'supervisor_decision_required']]


# ---------------------------------------------------------------------------
# §23 Component correspondence spec
# ---------------------------------------------------------------------------

CORRESPONDENCE = [
 ('native_component_identity', '8-connected label() on binarized native GT (mask > 0)',
  'deterministic', 'kub_size_clean_v3_v1'),
 ('native_component_ratio', 'component_pixels / (native_H * native_W)', 'deterministic', 'FULL_FIELD scope'),
 ('size_stratum', 'TINY <= Q25 < SMALL <= Q50 < MEDIUM <= Q75 < LARGE (lower-inclusive)',
  'deterministic', 'kub_size_clean_v3_v1 quantiles'),
 ('native_bbox', 'min_y/max_y/min_x/max_x from native component pixels', 'deterministic', 'inclusive extents'),
 ('crop_geometry', 'compute_square_crop(bbox, native_shape, margin) -> clip + pad + side',
  'deterministic', 'reuse historical geometry'),
 ('crop_to_native_map', 'invert clip/pad then side->native scaling implied by restore step',
  'deterministic', 'explicit, not case-complete inference'),
 ('component_detection', '>= 1 predicted foreground pixel overlapping the mapped GT component',
  'deterministic', 'unless historical contract proves otherwise (it does not)'),
 ('stratum_recall', 'detected components / total components within stratum', 'deterministic',
  'REPLACES the Phase-11 case-attributed approximation'),
 ('roi_handling', 'ROI_NOT_PRIMARY_BINNED (never size-binned)', 'rule', 'taxonomy scope'),
]


def build_correspondence_spec() -> pd.DataFrame:
    return pd.DataFrame(CORRESPONDENCE, columns=['item', 'specification', 'kind', 'notes'])


# ---------------------------------------------------------------------------
# §18 Prospective metric contract
# ---------------------------------------------------------------------------

METRIC_CONTRACT = [
 ('case_dice', 'per-case Dice (macro mean over cases)', 'case', 'primary effect'),
 ('case_iou', 'per-case IoU (macro mean)', 'case', 'primary effect'),
 ('case_precision', 'per-case precision (macro mean)', 'case', 'descriptive'),
 ('case_recall', 'per-case recall (macro mean)', 'case', 'descriptive'),
 ('object_recall', 'detected native GT components / total', 'component', '>=1 px overlap, 8-conn'),
 ('size_stratum_recall', 'TINY/SMALL/MEDIUM/LARGE component recall', 'component',
  'explicit component correspondence (not case-complete inference)'),
 ('empty_prediction', 'prediction has zero foreground pixels', 'case', 'recovery of Phase-11 empties'),
 ('empty_prediction_recovered', 'global empty AND oracle non-empty', 'case', 'derived'),
 ('missed_components', 'native GT components with no overlapping prediction', 'component', 'derived'),
 ('multicomponent_outcome', 'COMPLETE_DETECTION / PARTIAL_DETECTION / COMPLETE_MISS', 'case',
  'native multi-component membership'),
 ('hd95', 'HD95 with explicit hd95_valid flag', 'case', 'invalid flagged, never dropped'),
 ('fp_component_burden', 'FP predicted components (evaluation space)', 'component',
  'NOTE: oracle-constrained FP is artificially advantaged (historical caveat)'),
 ('tp_fp_fn', 'pixel TP/FP/FN', 'pixel', 'descriptive extension'),
 ('delta_dice', 'oracle_dice - global_dice (paired, same case, same architecture)', 'case',
  'PRIMARY ORACLE EFFECT'),
 ('delta_iou', 'oracle_iou - global_iou (paired)', 'case', 'derived'),
 ('delta_object_recall', 'oracle_object_recall - global_object_recall (paired)', 'component', 'derived'),
 ('delta_missed_components', 'global_missed - oracle_missed (paired)', 'component', 'derived'),
]


def build_metric_contract() -> pd.DataFrame:
    return pd.DataFrame(METRIC_CONTRACT, columns=['metric', 'definition', 'unit', 'role'])


# ---------------------------------------------------------------------------
# §24 Future visualization protocol
# ---------------------------------------------------------------------------

VIZ_PROTOCOL = [
 ('A', 'Per-model paired GLOBAL vs ORACLE Dice', 'grouped bar / paired line', 'FULL_FIELD 103'),
 ('B', 'delta Dice by model', 'bar with per-case distribution', 'paired within case+architecture'),
 ('C', 'object recall GLOBAL vs ORACLE', 'grouped bar', 'component space'),
 ('D', 'FULL_FIELD size-stratified component recovery', 'grouped bar TINY/SMALL/MEDIUM/LARGE',
  'explicit correspondence'),
 ('E', 'multi-component recovery', 'stacked bar COMPLETE/PARTIAL/MISS', '49 native cases'),
 ('F', 'empty-prediction recovery', 'bar recovered/not-recovered', 'Phase-11 empties 8/3/6/11'),
 ('G', 'Phase-11 ALL_FOUR_LOW recovery', 'bar', '12 frozen cases'),
 ('H', 'hard-case visual panels', 'multipage panel', 'Phase-11 frozen 16-case cohort'),
 ('I', 'cases where oracle worsens predictions', 'bar/table of negative delta', 'descriptive'),
 ('J', 'cross-model oracle-effect consistency', 'bar of per-model delta + spread',
  'number_of_models_improved, median/range'),
]


def build_viz_protocol() -> pd.DataFrame:
    return pd.DataFrame(VIZ_PROTOCOL, columns=['id', 'visualization', 'form', 'basis'])


# ---------------------------------------------------------------------------
# §26/§27 Regional integration gate candidate
# ---------------------------------------------------------------------------

GATE_DIMENSIONS = [
 ('A', 'ORACLE_MECHANISM_VALUE',
  'Does GT-derived higher-effective-resolution regional processing provide useful recovery '
  'over global inference?',
  'delta_dice, delta_object_recall, size-stratum recall on FULL_FIELD 103',
  'CANDIDATE_FOR_SUPERVISOR_FREEZE',
  'Candidate: positive median paired delta_dice across all four models. Threshold NOT frozen.'),
 ('B', 'PRACTICAL_LOCALIZATION_RETENTION',
  'In Phase 13, how much oracle benefit is retained using GT-free localization?',
  'Phase-13 oracle-vs-predicted-region retention ratio',
  'CANDIDATE_FOR_SUPERVISOR_FREEZE',
  'Candidate: retention clearly above zero; exact fraction NOT frozen.'),
 ('C', 'GLOBAL_PRESERVATION_FP_COST',
  'Does regional processing recover targets without unacceptable FP/global degradation?',
  'delta precision, FP component burden, cases where oracle worsens',
  'CANDIDATE_FOR_SUPERVISOR_FREEZE',
  'Candidate: no material global degradation; oracle-FP caveat acknowledged.'),
 ('D', 'GENERALITY',
  'Is the effect seen across enough architectures/case types to justify a reusable mechanism?',
  'number_of_models_improved, all_four_improved, range_of_delta_dice',
  'CANDIDATE_FOR_SUPERVISOR_FREEZE',
  'Candidate: benefit not confined to a single architecture. Threshold NOT frozen.'),
]


def build_gate_candidate() -> pd.DataFrame:
    return pd.DataFrame(GATE_DIMENSIONS,
                        columns=['dimension_id', 'dimension', 'question', 'evidence_fields',
                                 'criterion_status', 'candidate_criterion'])


# ---------------------------------------------------------------------------
# §21 Phase-11 frozen cohort bridge plan
# ---------------------------------------------------------------------------

COHORT_BRIDGE = [
 ('ALL_FOUR_LOW', 12, 'reports/tables/phase11_clean_v3_paired_case_failure_summary.csv',
  'Report oracle vs global delta_dice for these 12 cases; how many are recovered/unchanged/worsened'),
 ('PHASE11_HARD_COHORT', 16, 'reports/tables/phase11_clean_v3_hard_case_selection.csv',
  'Report oracle effect per stratum (A_EMPTY/B_MISSED/C_HIGH_FP/D_LOW_DICE)'),
 ('TOP_DISAGREEMENT', 4, 'reports/tables/phase11_clean_v3_top_disagreement_cases.csv',
  'Report whether oracle reduces cross-model disagreement on these cases'),
 ('FULL_FIELD_REGIME', 103, 'reports/tables/phase11_clean_v3_failure_by_acquisition.csv',
  'Primary oracle population; report regime-separated results'),
 ('MULTICOMPONENT', 49, 'reports/tables/phase11_clean_v3_multicomponent_analysis.csv',
  'Report oracle multi-component outcome transitions'),
]


def build_cohort_bridge() -> pd.DataFrame:
    rows = []
    for name, n, src, plan in COHORT_BRIDGE:
        p = PROJECT_ROOT / src
        rows.append({'cohort': name, 'n': n, 'source': src,
                     'source_sha': sha256_file(p) if p.exists() else 'N/A',
                     'prospective_plan': plan,
                     'reselect_after_results': False})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Upstream epoch tables (read-only appendix, §31)
# ---------------------------------------------------------------------------

def load_upstream_epoch_table(key: str) -> pd.DataFrame:
    return pd.read_csv(PHASE10_EPOCH_TABLES[key])


def verify_upstream_epoch_tables() -> pd.DataFrame:
    rows = []
    for k in CLEAN_V3_MODELS:
        d = load_upstream_epoch_table(k)
        eps = d['epoch'].astype(int).tolist()
        exp = EXPECTED_EPOCH_ROWS[k]
        expected = list(range(1, exp + 1))
        rows.append({'model': MODEL_DISPLAY[k], 'rows': len(d), 'expected_rows': exp,
                     'row_count_matches': len(d) == exp,
                     'first_epoch': min(eps), 'last_epoch': max(eps),
                     'missing_epochs': str(sorted(set(expected) - set(eps))),
                     'duplicate_epochs': str(sorted({e for e in eps if eps.count(e) > 1})),
                     'contiguous': eps == expected,
                     'sha256': sha256_file(PHASE10_EPOCH_TABLES[k])})
    return pd.DataFrame(rows)
