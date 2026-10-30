"""
Phase 11 Part 1A — Historical protocol reconstruction + CLEAN-v3 failure-definition
support (READ-ONLY).

Part 1A is a PROTOCOL / DEFINITION phase. It does NOT execute the full Phase-11
failure analysis. Forbidden: training, optimizer.step, checkpoint writes, config
changes, threshold tuning, TEST reads, reference-model selection.

All historical facts below are reconstructed from repository artifacts:
  1. scripts/analysis/analyze_phase11_failures.py        (executing analysis code)
  2. reports/audits/phase11_failure_strata_definitions.json (persisted definitions)
  3. reports/audits/phase11_kub_failure_analysis.json    (audit)
  4. notebooks/phasewise/phase_11_failure_analysis/...ipynb (executed historical notebook)
  5. scripts/generate_phase11_failures.py                (hard-case selection code)
  6. src/metrics/object_metrics.py                       (object/connectivity contract)
  7. reports/audits/kub_size_clean_v3_v1_thresholds.json (clean-v3 taxonomy)

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
PHASEWISE = PROJECT_ROOT / 'notebooks' / 'phasewise'

# ---------------------------------------------------------------------------
# Frozen clean-v3 inputs (from Phase 10)
# ---------------------------------------------------------------------------

CLEAN_V3_MODELS = ['unet', 'attention_unet', 'unetpp', 'deeplabv3plus']
MODEL_DISPLAY = {'unet': 'UNet', 'attention_unet': 'Attention U-Net',
                 'unetpp': 'UNet++', 'deeplabv3plus': 'DeepLabV3+'}

CLEAN_V3_METRICS = {
    'unet': {'best_epoch': 44, 'dice': 0.7406133413314819, 'iou': 0.6253822445869446,
             'precision': 0.7707186937332153, 'recall': 0.7839437127113342},
    'attention_unet': {'best_epoch': 54, 'dice': 0.7525129853960107, 'iou': 0.6349387691368995,
                       'precision': 0.7729140812402236, 'recall': 0.7922248481868364},
    'unetpp': {'best_epoch': 70, 'dice': 0.7641595156062713, 'iou': 0.6525442690586191,
               'precision': 0.7996825971468945, 'recall': 0.7912384169561990},
    'deeplabv3plus': {'best_epoch': 52, 'dice': 0.7509140344161673, 'iou': 0.6460492792430865,
                      'precision': 0.7943328495850855, 'recall': 0.7822983241135557},
}

PAIRED_TABLE = TABLES / 'phase10_clean_v3_paired_val_case_metrics.csv'
PHASE10_EPOCH_TABLES = {
    'unet': TABLES / 'phase10_final_epoch_results_unet.csv',
    'attention_unet': TABLES / 'phase10_final_epoch_results_attention_unet.csv',
    'unetpp': TABLES / 'phase10_final_epoch_results_unetpp.csv',
    'deeplabv3plus': TABLES / 'phase10_final_epoch_results_deeplabv3plus.csv',
}
EXPECTED_EPOCH_ROWS = {'unet': 59, 'attention_unet': 69, 'unetpp': 85, 'deeplabv3plus': 67}

# clean-v3 frozen contracts
TAXONOMY_ID = 'kub_size_clean_v3_v1'
TAXONOMY_SHA = '89031c51a35c24f6f939fd6206fde6002a019d4bda24ce8cb21988f04db0f0d6'
TAXONOMY_QUANTILES = {'Q25': 0.0001497998649691358,
                      'Q50': 0.0003401438395182292,
                      'Q75': 0.0008279682677469136}
FOREGROUND_RULE = 'mask > 0'
CONNECTIVITY = 8
MINIMUM_OVERLAP_PIXELS = 1
REGIME_COUNTS = {'FULL_FIELD': 103, 'ROI': 177}
CATEGORY_COUNTS = {'Bladder_Stone': 144, 'Kidney_Stone': 112, 'Ureteric_Stone': 24}


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Historical source inventory (§26)
# ---------------------------------------------------------------------------

HISTORICAL_SOURCES = [
    ('executing analysis code', 1, 'scripts/analysis/analyze_phase11_failures.py',
     'Defines failure labels, decile cutoffs, taxonomy counts, cross-model overlap'),
    ('executing selection code', 1, 'scripts/generate_phase11_failures.py',
     'Defines the 16-case hard-case cohort selection procedure'),
    ('persisted strata definitions', 2, 'reports/audits/phase11_failure_strata_definitions.json',
     'Numeric cutoffs for low_dice/high_hd95/high_fp deciles'),
    ('persisted audit', 2, 'reports/audits/phase11_kub_failure_analysis.json',
     'Primary model, comparator, split, threshold, component-space convention, Phase-12 motivation'),
    ('executed historical notebook', 3, 'notebooks/phasewise/phase_11_failure_analysis/phase11_kub_failure_analysis_and_tiny_stone_errors.ipynb',
     'Rendered historical failure analysis'),
    ('historical README', 4, 'notebooks/phasewise/phase_11_failure_analysis/README.md',
     'Phase scope prose'),
    ('per-image table', 2, 'reports/tables/phase11_kub_failure_analysis_per_image.csv',
     'Case-level metrics + failure labels'),
    ('per-component table', 2, 'reports/tables/phase11_kub_failure_analysis_per_component.csv',
     'Object/component-level detection'),
    ('multicomponent table', 2, 'reports/tables/phase11_kub_multicomponent_failure.csv',
     'Multi-component detection classes'),
    ('size failure summary', 2, 'reports/tables/phase11_kub_size_failure_summary.csv',
     'TINY/SMALL/MEDIUM/LARGE recall (kub_size_v1)'),
    ('cross-model overlap', 2, 'reports/tables/phase11_cross_model_failure_overlap.csv',
     'ALL_FOUR_LOW / ARCHITECTURE_DISAGREEMENT style categories'),
    ('16-case selection', 2, 'reports/tables/phase11_failure_16_selection.csv',
     'Selected qualitative failure cohort'),
    ('qualitative selection json', 2, 'reports/qualitative/phase11_kub_failure_analysis/phase11_unetpp_failure_selection.json',
     'Selector names -> sample_ids for the UNet++ panel'),
    ('object metric contract', 1, 'src/metrics/object_metrics.py',
     '8-connected, overlap-based matching, minimum_overlap_pixels=1'),
    ('project context prose', 5, 'PROJECT_CONTEXT.md',
     'Historical phase narrative incl. Phase-12/13 conclusions'),
]


def build_source_inventory() -> pd.DataFrame:
    rows = []
    for kind, prec, rel, role in HISTORICAL_SOURCES:
        p = PROJECT_ROOT / rel
        rows.append({'source_kind': kind, 'precedence': prec, 'path': rel,
                     'exists': p.exists(),
                     'sha256': sha256_file(p) if p.exists() else 'N/A',
                     'role': role})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Historical failure-definition matrix (§8)
# ---------------------------------------------------------------------------

# concept, historical_definition, unit, metric, threshold, scope, source, status
FAILURE_MATRIX = [
 ('low Dice', 'bottom decile of per-image Dice (low_dice_decile)', 'case', 'dice',
  'dice <= 0.5461063385009766', 'VAL (283, phase4_v2)',
  'reports/audits/phase11_failure_strata_definitions.json', 'VERIFIED'),
 ('low IoU', 'no separate IoU failure stratum defined', 'case', 'iou', 'NOT_FOUND',
  'n/a', 'analyze_phase11_failures.py', 'NOT_FOUND'),
 ('false-negative dominant', 'recall reported per case; no FN-dominant stratum', 'case', 'recall',
  'NOT_FOUND', 'n/a', 'analyze_phase11_failures.py', 'NOT_FOUND'),
 ('false-positive dominant', 'high_fp_decile = fp evaluation components >= cutoff', 'case',
  'fp_eval_components', 'fp_eval_components >= 4.0', 'VAL (283)',
  'reports/audits/phase11_failure_strata_definitions.json', 'VERIFIED'),
 ('empty prediction', 'prediction has zero foreground pixels (empty_prediction)', 'case',
  'empty_prediction', 'prediction foreground == 0', 'VAL (283)',
  'analyze_phase11_failures.py', 'VERIFIED'),
 ('object miss', 'GT component with no overlapping predicted component', 'component',
  'missed_eval_components / detected', 'overlap < 1 px => missed', 'evaluation 512 space',
  'src/metrics/object_metrics.py', 'VERIFIED'),
 ('partial object miss', 'multi-component case: some but not all GT components detected', 'case',
  'detection_class = PARTIAL_DETECTION', '0 < detected < total', 'multi-component subset (50)',
  'reports/tables/phase11_kub_multicomponent_failure.csv', 'VERIFIED'),
 ('under-segmentation', 'no explicit under-segmentation fraction defined', 'case/pixel',
  'n/a', 'NOT_FOUND', 'n/a', 'analyze_phase11_failures.py', 'NOT_FOUND'),
 ('over-segmentation', 'no explicit over-segmentation fraction defined', 'case/pixel',
  'n/a', 'NOT_FOUND', 'n/a', 'analyze_phase11_failures.py', 'NOT_FOUND'),
 ('boundary error', 'HD95 (95th percentile symmetric surface distance) with validity flag',
  'case', 'hd95 / hd95_valid', 'hd95 >= 83.07246563841615 (valid only)',
  'VAL (283; 275 valid / 8 invalid)',
  'reports/audits/phase11_failure_strata_definitions.json', 'VERIFIED'),
 ('tiny-object failure', 'missed TINY component (kub_size_v1 TINY)', 'component',
  'missed_tiny_component', 'component_ratio <= Q25 of kub_size_v1',
  'VALID original-space components', 'analyze_phase11_failures.py', 'VERIFIED'),
 ('small-object failure', 'missed SMALL component (kub_size_v1 SMALL)', 'component',
  'missed_small_component', 'Q25 < ratio <= Q50', 'VALID original-space components',
  'analyze_phase11_failures.py', 'VERIFIED'),
 ('multi-component failure', 'original_component_count > 1; COMPLETE/PARTIAL/COMPLETE_MISS',
  'case', 'detection_class', 'detected == 0 -> COMPLETE_MISS; detected == total -> COMPLETE_DETECTION',
  'multi-component subset (50)', 'reports/tables/phase11_kub_multicomponent_failure.csv',
  'VERIFIED'),
 ('FULL_FIELD failure', 'stratified by FOV == FULL_FIELD', 'case', 'dice/recall by FOV',
  'regime membership', 'FULL_FIELD 106 / ROI_CROP 177',
  'reports/tables/phase11_kub_failure_analysis_per_image.csv', 'VERIFIED'),
 ('ROI failure', 'stratified by FOV == ROI_CROP', 'case', 'dice/recall by FOV',
  'regime membership', 'ROI_CROP 177 / FULL_FIELD 106',
  'reports/tables/phase11_kub_failure_analysis_per_image.csv', 'VERIFIED'),
 ('category-specific failure', 'category (Bladder/Kidney/Ureteric) used as metadata subgroup',
  'case', 'metrics by category', 'subgroup membership (not pixel class)',
  'Bladder 145 / Kidney 114 / Ureteric 24',
  'reports/tables/phase11_kub_failure_analysis_per_image.csv', 'VERIFIED'),
 ('cross-model disagreement', 'failure_category incl. ARCHITECTURE_DISAGREEMENT, *_UNIQUELY_*',
  'case', 'low-performer flags per model',
  'low = each model own bottom Dice decile', 'cross-model VAL',
  'analyze_phase11_failures.py', 'VERIFIED'),
 ('shared hard case', 'ALL_FOUR_LOW = low in all four models (bottom decile each)', 'case',
  'low_* flags', 'all(low_unet, low_attn, low_unetpp, low_deeplab)', 'cross-model VAL',
  'analyze_phase11_failures.py', 'VERIFIED'),
]


def build_failure_matrix() -> pd.DataFrame:
    rows = []
    for concept, defn, unit, metric, thr, scope, src, status in FAILURE_MATRIX:
        p = PROJECT_ROOT / src
        rows.append({'concept': concept, 'historical_definition': defn, 'unit': unit,
                     'metric': metric, 'threshold': thr, 'scope': scope, 'source': src,
                     'source_sha': sha256_file(p) if p.exists() else 'N/A',
                     'status': status})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Clean-v3 failure dimensions (§13 / §26)
# ---------------------------------------------------------------------------

CLEAN_V3_DIMENSIONS = [
 ('regime', 'FULL_FIELD vs ROI acquisition regime', 'case', 'VERIFIED_CONTRACT',
  'FULL_FIELD 103 / ROI 177; NEVER pool without showing both'),
 ('category', 'Kidney/Bladder/Ureteric subgroup metadata', 'case', 'VERIFIED_CONTRACT',
  'metadata only; not a pixel class; Ureteric n=24 do not overinterpret'),
 ('size stratum (FULL_FIELD only)', 'kub_size_clean_v3_v1 TINY/SMALL/MEDIUM/LARGE', 'component',
  'VERIFIED_CONTRACT', 'Q25/Q50/Q75 frozen; ROI = ROI_NOT_PRIMARY_BINNED'),
 ('object detection', 'per-GT-component detected/missed via 8-conn, >=1px overlap', 'component',
  'VERIFIED_CONTRACT', 'original space = identity; evaluation 512 space = predictions/FP'),
 ('multi-component', 'COMPLETE / PARTIAL / COMPLETE_MISS detection classes', 'case',
  'HISTORICAL_VERIFIED_PROPOSED_EXTENSION',
  'historical analysed on original_component_count>1; retain as descriptive subgroup'),
 ('boundary', 'HD95 with validity flag; invalid handled explicitly', 'case',
  'VERIFIED_CONTRACT', 'no silent NaN dropping; report valid counts'),
 ('empty prediction', 'zero-foreground prediction', 'case', 'HISTORICAL_VERIFIED',
  'carry forward from historical definition'),
 ('false-positive burden', 'fp evaluation components count', 'case', 'HISTORICAL_VERIFIED',
  'historical used decile cutoff; clean-v3 cutoff NOT yet frozen'),
 ('low-Dice stratum', 'bottom-decile Dice stratum', 'case', 'HISTORICAL_METHOD_NOT_VALUE',
  'method (own-distribution bottom decile) is historical; the numeric value must be recomputed on clean-v3 and is NOT frozen here'),
 ('shared failure', 'cases difficult across all four clean-v3 baselines', 'case',
  'CANDIDATE_FOR_SUPERVISOR_REVIEW', 'no formula frozen in Part 1A'),
 ('architecture disagreement', 'cases where the four baselines diverge materially', 'case',
  'CANDIDATE_FOR_SUPERVISOR_REVIEW', 'e.g. max-min Dice or SD; no threshold frozen'),
]


def build_dimensions() -> pd.DataFrame:
    return pd.DataFrame(CLEAN_V3_DIMENSIONS,
                        columns=['dimension', 'definition', 'unit', 'status', 'note'])


# ---------------------------------------------------------------------------
# Hard-case selection protocol (§17 / §26)
# ---------------------------------------------------------------------------

HARD_CASE_PROTOCOL = [
 ('cohort_size', '16', 'HISTORICAL_VERIFIED',
  'phase11_failure_16_selection.csv contains 16 cases'),
 ('strata', '4 categories x 4 cases', 'HISTORICAL_VERIFIED',
  'Global-Empty; Missed GT Component; Severe FP; Low Dice Decile'),
 ('stratum_1', 'empty_prediction == True', 'HISTORICAL_VERIFIED', 'take first 4 by sample_id'),
 ('stratum_2', 'missed_eval_components > 0', 'HISTORICAL_VERIFIED',
  'exclude already-selected; first 4 by sample_id'),
 ('stratum_3', 'fp_eval_components >= 4', 'HISTORICAL_AMBIGUOUS',
  'code uses >=4 but inline comment says ">=5"; COMMENT/CODE mismatch recorded'),
 ('stratum_4', 'low_dice_decile == True', 'HISTORICAL_AMBIGUOUS',
  'cohort label says "Low Dice Decile (<0.30)" but actual cutoff is 0.5461 (bottom decile); LABEL mismatch recorded'),
 ('tie_break', 'sort by sample_id (deterministic); low-dice stratum sorts by ascending dice',
  'HISTORICAL_VERIFIED', 'selection is deterministic and prediction-independent in ordering'),
 ('exclusion', 'each stratum excludes samples selected by earlier strata', 'HISTORICAL_VERIFIED',
  'prevents duplicate cases across categories'),
 ('depends_on_prediction_quality', 'YES by construction (failure strata)', 'HISTORICAL_VERIFIED',
  'unlike the Phase-10 gallery, this cohort IS selected by failure status - intentional for failure analysis'),
 ('clean_v3_status', 'NOT YET APPLIED', 'FROZEN_PROPOSAL_ONLY',
  'Part 1A freezes the procedure; no clean-v3 cases are selected in Part 1A'),
]


def build_hard_case_protocol() -> pd.DataFrame:
    return pd.DataFrame(HARD_CASE_PROTOCOL,
                        columns=['item', 'rule', 'status', 'note'])


# ---------------------------------------------------------------------------
# Phase-12 bridge reconstruction (§21 / §26)
# ---------------------------------------------------------------------------

PHASE12_BRIDGE = [
 ('historical_observation',
  'FULL_FIELD, small-object and multi-component failures persisted for the global baseline',
  'reports/audits/phase11_kub_failure_analysis.json:phase12_motivation'),
 ('historical_rationale',
  'Motivates testing whether increased effective local resolution can recover missed targets; explicitly NOT a claim that ROI will solve them',
  'reports/audits/phase11_kub_failure_analysis.json:phase12_motivation'),
 ('tiny_recall_evidence', 'TINY component recall 57/73 = 0.7808 (kub_size_v1, UNet++)',
  'reports/tables/phase11_kub_size_failure_summary.csv'),
 ('multicomponent_evidence', '50 multi-component cases: 36 COMPLETE / 10 PARTIAL / 4 COMPLETE_MISS',
  'reports/tables/phase11_kub_multicomponent_failure.csv'),
 ('primary_model_historical', 'UNet++ (phase10_kub_unetpp_seed42_512)',
  'reports/audits/phase11_kub_failure_analysis.json:primary_model'),
 ('comparator_historical', 'DeepLabV3+',
  'reports/audits/phase11_kub_failure_analysis.json:secondary_comparator'),
 ('clean_v3_reference_model', 'NOT SELECTED',
  'Part 1A must not choose a reference from single-seed VAL (see spec section 22)'),
 ('part_1b_must_test',
  'Whether the same FULL_FIELD / small-object / multi-component failure pattern holds for ALL FOUR clean-v3 baselines, and whether it is shared or architecture-specific',
  'derived'),
]


def build_phase12_bridge() -> pd.DataFrame:
    return pd.DataFrame(PHASE12_BRIDGE, columns=['item', 'value', 'source'])


# ---------------------------------------------------------------------------
# Upstream epoch tables (read-only, §23)
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


def load_paired_table() -> pd.DataFrame:
    return pd.read_csv(PAIRED_TABLE)


def verify_paired_table() -> Dict[str, Any]:
    d = load_paired_table()
    need = [f'{m}_{x}' for m in CLEAN_V3_MODELS for x in ['dice', 'iou', 'precision', 'recall']]
    return {'rows': len(d), 'unique_samples': int(d['sample_id'].nunique()),
            'all_model_columns': all(c in d.columns for c in need),
            'any_nan': bool(d[need].isna().any().any()),
            'category_counts': d['category'].value_counts().to_dict(),
            'acquisition_counts': d['acquisition_type'].value_counts().to_dict()}
