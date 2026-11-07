# Generate evidence CSV tables for V4:
# 1. EXTERNAL_EVALUATION_EVIDENCE.csv
# 2. PROGRESSION_AND_PROPAGATION_EVIDENCE.csv

import pandas as pd
import numpy as np

# 1. EXTERNAL_EVALUATION_EVIDENCE.csv
ext_data = [
    {
        'cohort_name': 'CVC-ClinicDB',
        'task_analogue': 'KVASIR (Colonoscopy Polyp)',
        'sample_count': 612,
        'global_dice': 0.686568,
        'barr_full_dice': 0.689747,
        'paired_delta_pp': 0.317952,
        'global_iou': 0.574871,
        'barr_iou': 0.577924,
        'hd95_global_px': 109.593,
        'hd95_barr_px': 107.842,
        'routed_count': 142,
        'adopted_count': 112,
        'rejected_count': 30,
        'improved_count': 81,
        'worsened_count': 31,
        'harm_rate_of_adopted': 0.276786,
        'evidence_status': 'RETROSPECTIVE_HISTORICAL_EXPLORATORY',
        'source_artifact': 'reports/tables/c1_external_stress_summary.csv'
    },
    {
        'cohort_name': 'BrEaST-Lesions-USG',
        'task_analogue': 'BUSI (Breast Ultrasound)',
        'sample_count': 252,
        'global_dice': 0.707822,
        'barr_full_dice': 0.708098,
        'paired_delta_pp': 0.027631,
        'global_iou': 0.590559,
        'barr_iou': 0.590864,
        'hd95_global_px': 87.168,
        'hd95_barr_px': 87.054,
        'routed_count': 38,
        'adopted_count': 24,
        'rejected_count': 14,
        'improved_count': 14,
        'worsened_count': 3,
        'harm_rate_of_adopted': 0.125000,
        'evidence_status': 'RETROSPECTIVE_HISTORICAL_EXPLORATORY',
        'source_artifact': 'reports/tables/c1_external_stress_summary.csv'
    },
    {
        'cohort_name': 'Stones_where_are_you (Overall)',
        'task_analogue': 'KUB (Abdominal Radiography)',
        'sample_count': 20,
        'global_dice': 0.080840,
        'barr_full_dice': 0.082126,
        'paired_delta_pp': 0.128592,
        'global_iou': 0.060916,
        'barr_iou': 0.061594,
        'hd95_global_px': 166.904,
        'hd95_barr_px': 169.900,
        'routed_count': 4,
        'adopted_count': 3,
        'rejected_count': 1,
        'improved_count': 1,
        'worsened_count': 0,
        'harm_rate_of_adopted': 0.000000,
        'evidence_status': 'RETROSPECTIVE_HISTORICAL_EXPLORATORY',
        'source_artifact': 'reports/tables/c1_external_stress_summary.csv'
    },
    {
        'cohort_name': 'Stones_where_are_you (Stone-Free Negative)',
        'task_analogue': 'KUB (Negative Control)',
        'sample_count': 14,
        'global_dice': 0.000000,
        'barr_full_dice': 0.000000,
        'paired_delta_pp': 0.000000,
        'global_iou': 0.000000,
        'barr_iou': 0.000000,
        'hd95_global_px': np.nan,
        'hd95_barr_px': np.nan,
        'routed_count': 3,
        'adopted_count': 2,
        'rejected_count': 1,
        'improved_count': 0,
        'worsened_count': 0,
        'harm_rate_of_adopted': 0.000000,
        'evidence_status': 'MATERIAL_FAILURE__14_OF_14_FALSE_POSITIVE',
        'source_artifact': 'reports/tables/c1_external_stress_stones_subgroups.csv'
    },
    {
        'cohort_name': 'Stones_where_are_you (Stone-Positive)',
        'task_analogue': 'KUB (Positive Control)',
        'sample_count': 6,
        'global_dice': 0.269468,
        'barr_full_dice': 0.273755,
        'paired_delta_pp': 0.428641,
        'global_iou': 0.203052,
        'barr_iou': 0.205312,
        'hd95_global_px': 166.904,
        'hd95_barr_px': 169.900,
        'routed_count': 1,
        'adopted_count': 1,
        'rejected_count': 0,
        'improved_count': 1,
        'worsened_count': 0,
        'harm_rate_of_adopted': 0.000000,
        'evidence_status': 'RETROSPECTIVE_HISTORICAL_EXPLORATORY',
        'source_artifact': 'reports/tables/c1_external_stress_stones_subgroups.csv'
    }
]

df_ext = pd.DataFrame(ext_data)
df_ext.to_csv('full_doc_report/EXTERNAL_EVALUATION_EVIDENCE.csv', index=False)
df_ext.to_csv('full_doc_report/tables/external_evaluation_evidence.csv', index=False)
print('Saved EXTERNAL_EVALUATION_EVIDENCE.csv')

# 2. PROGRESSION_AND_PROPAGATION_EVIDENCE.csv
prog_data = [
    {
        'stage_sequence': 'Stage 0 -> Stage 1',
        'stage_name': 'GlobalMedFiLM Backbone (G)',
        'population': 'VAL808',
        'input_n': 808,
        'active_components': 'G (Task-conditioned FiLM)',
        'mean_dice': 0.835079,
        'routed_fraction': 0.0,
        'accepted_fraction': 0.0,
        'net_delta_pp': 0.0,
        'harm_rate': 0.0,
        'gmacs_lower_bound': 31.5517,
        'notes': 'Frozen baseline across all 4 domains'
    },
    {
        'stage_sequence': 'Stage 1 -> Stage 2',
        'stage_name': 'Candidate Regional Refiner (R_psi, Unrouted)',
        'population': 'ROUTER_DEVELOPMENT4957',
        'input_n': 4957,
        'active_components': 'G + R_psi (Arm A1, Always Refine)',
        'mean_dice': np.nan,
        'routed_fraction': 1.0,
        'accepted_fraction': 1.0,
        'net_delta_pp': 0.1658,
        'harm_rate': 0.426669,
        'gmacs_lower_bound': 34.7824,
        'notes': 'Unconditional refinement causes 42.7% harm rate'
    },
    {
        'stage_sequence': 'Stage 2 -> Stage 3',
        'stage_name': 'Benefit Router (B_phi, Learned Benefit Selection)',
        'population': 'ROUTER_DEVELOPMENT4957',
        'input_n': 4957,
        'active_components': 'G + R_psi + B_phi (Arm A7, Budget 0.25)',
        'mean_dice': np.nan,
        'routed_fraction': 0.24995,
        'accepted_fraction': 0.24995,
        'net_delta_pp': 0.7247,
        'harm_rate': 0.332526,
        'gmacs_lower_bound': 32.4379,
        'notes': 'Learned benefit routing cuts harm rate to 33.3%'
    },
    {
        'stage_sequence': 'Stage 3 -> Stage 4',
        'stage_name': 'Post-Safety Gate (S_omega, Final BARR)',
        'population': 'ROUTER_DEVELOPMENT4957',
        'input_n': 4957,
        'active_components': 'G + R_psi + B_phi + S_omega (Arm A8)',
        'mean_dice': np.nan,
        'routed_fraction': 0.24995,
        'accepted_fraction': 0.243091,
        'net_delta_pp': 0.7516,
        'harm_rate': 0.323651,
        'gmacs_lower_bound': 32.4379,
        'notes': '34 unsafe proposals rejected, lifting routed delta to +0.75 pp'
    },
    {
        'stage_sequence': 'Stage 4 (Validated)',
        'stage_name': 'FULL RA-MedFiLM-BARR Final Pipeline',
        'population': 'VAL808',
        'input_n': 808,
        'active_components': 'Full 4-component bundle (G + R + B + S)',
        'mean_dice': 0.837862,
        'routed_fraction': 0.2265,
        'accepted_fraction': 0.2042,
        'net_delta_pp': 0.2783,
        'harm_rate': 0.1878,
        'gmacs_lower_bound': 32.4379,
        'notes': 'Canonical frozen validation outcome (+0.28 pp overall gain)'
    },
    {
        'stage_sequence': 'Scientific Audit Gate',
        'stage_name': 'Incremental Dataset Progression',
        'population': 'N/A',
        'input_n': 0,
        'active_components': 'INCREMENTAL_DATASET_PROGRESSION_NOT_EXECUTED',
        'mean_dice': np.nan,
        'routed_fraction': np.nan,
        'accepted_fraction': np.nan,
        'net_delta_pp': np.nan,
        'harm_rate': np.nan,
        'gmacs_lower_bound': np.nan,
        'notes': 'Audit confirms no genuine multi-seed incremental domain training study exists in repository'
    }
]

df_prog = pd.DataFrame(prog_data)
df_prog.to_csv('full_doc_report/PROGRESSION_AND_PROPAGATION_EVIDENCE.csv', index=False)
df_prog.to_csv('full_doc_report/tables/progression_and_propagation_evidence.csv', index=False)
print('Saved PROGRESSION_AND_PROPAGATION_EVIDENCE.csv')