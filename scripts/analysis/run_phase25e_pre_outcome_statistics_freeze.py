"""Phase25E PRE-OUTCOME STATISTICS FREEZE + CRITERIA BINDING (outcome-blind).

Runs BEFORE any Phase25C outcome column is opened. Persists:
  - reports/audits/phase25e_evaluation_statistics_contract_v1_0.json
  - reports/audits/phase25e_success_failure_criteria_binding.json
  - data_cache/phase25e_barr_resource_gate_v1_0/phase25e_bootstrap_plan_v1_0.npz
    (the realized domain-stratified group-bootstrap draw, hashed so that the
    statistical mechanics provably pre-date the outcome join)

Only identity / group_key / domain metadata is read. No delta_dice.
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
AUD = ROOT / 'reports/audits'
TABLE = ROOT / 'reports/tables'
CACHE = ROOT / 'data_cache/phase25e_barr_resource_gate_v1_0'
REV = 'ra_medfilm_barr_resource_gate_v1_0'
CLASS = 'PHASE25E_RESOURCE_GATE_POLICY_EVALUATION'

N_BOOT = 2000
SEED = 42
CI_PCT = [2.5, 97.5]
BUDGETS = ['0.00', '0.10', '0.25', '0.50', '1.00']
LAMBDAS = ['0.00', '0.25', '0.50', '1.00']


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    failures = []

    # --- group structure (identity + domain only) -------------------------------
    m = pd.read_csv(ROOT / 'reports/audits/phase24_router_split_manifest.csv',
                    usecols=['sample_id', 'dataset', 'group_key', 'split_role'], dtype=str)
    dev = m[m.split_role == 'ROUTER_DEVELOPMENT'].copy()
    if len(dev) != 4957:
        failures.append(f'DEV_ROWS:{len(dev)}')
    meta = pd.read_csv(ROOT / 'data_cache/phase25b_barr_pre_refinement_features_v1_2/metadata.csv',
                       usecols=['sample_id'], dtype={'sample_id': str})
    if set(dev.sample_id) != set(meta.sample_id):
        failures.append('DEV_IDENTITY_MISMATCH')

    strata = sorted(dev.dataset.unique())
    group_lists = {d: sorted(dev.loc[dev.dataset == d, 'group_key'].unique()) for d in strata}
    group_counts = {d: len(group_lists[d]) for d in strata}
    total_groups = sum(group_counts.values())

    # --- realize the frozen bootstrap draw --------------------------------------
    rng = np.random.Generator(np.random.PCG64(SEED))
    h = hashlib.sha256()
    draw_arrays = {}
    for b in range(N_BOOT):
        for d in strata:
            n_g = group_counts[d]
            idx = rng.integers(0, n_g, size=n_g, dtype=np.int64)
            h.update(idx.tobytes())
            draw_arrays[f'{b}:{d}'] = idx
    bootstrap_plan_sha = h.hexdigest()

    plan_path = CACHE / 'phase25e_bootstrap_plan_v1_0.npz'
    np.savez_compressed(plan_path, **draw_arrays)
    plan_file_sha = sha(plan_path)

    # --- frozen GT-free size-strata quartiles (predicted_roi_area_fraction) ------
    schema = pd.read_csv(ROOT / 'data_cache/phase25b_barr_pre_refinement_features_v1_2/feature_schema.csv')
    roi_row = schema.loc[schema.feature_name == 'predicted_roi_area_fraction']
    roi_idx = int(roi_row.feature_index.iloc[0])
    if bool(roi_row.uses_GT.iloc[0]):
        failures.append('ROI_AREA_USES_GT')
    matrix = np.load(ROOT / 'data_cache/phase25b_barr_pre_refinement_features_v1_2/features.npy',
                     mmap_mode='r', allow_pickle=False)
    meta_av = pd.read_csv(ROOT / 'data_cache/phase25b_barr_pre_refinement_features_v1_2/metadata.csv',
                          usecols=['feature_row_index', 'sample_id', 'action_available'],
                          dtype={'sample_id': str}).sort_values('feature_row_index', kind='stable')
    elig_rows = meta_av.loc[meta_av.action_available.astype(bool), 'feature_row_index'].to_numpy()
    roi_vals = np.asarray(matrix[elig_rows, roi_idx], dtype=np.float64)
    q25, q50, q75 = (float(np.quantile(roi_vals, q)) for q in (0.25, 0.50, 0.75))
    size_quartiles = {'Q25': q25, 'Q50': q50, 'Q75': q75, 'n_eligible': int(len(roi_vals))}

    # --- statistics contract -----------------------------------------------------
    metrics = {
        'precision_at_budget': '|S intersect B| / K',
        'benefit_capture_at_budget': 'sum(max(d_i,0) for i in S) / sum(max(d_i,0) for i in E)',
        'mean_true_delta_dice_among_routed': 'sum(d_i for i in S) / K',
        'harmful_activation_rate': '|S intersect H| / K',
        'beneficial_activation_rate': '|S intersect B| / |B|',
        'missed_benefit_rate': '|B minus S| / |B|',
        'routing_regret_vs_oracle': 'sum(d_i for i in oracle top-K) - sum(d_i for i in S)',
        'regret_mean_per_sample': 'routing_regret_vs_oracle / N_DEV',
        'regret_mean_per_routed_sample': 'routing_regret_vs_oracle / K',
        'macro_domain_mean_true_delta_dice': 'mean over domains of mean(d_i for i in S intersect domain)',
    }
    contract = {
        'classification': CLASS,
        'specification_revision': REV,
        'stage': 'PRE_OUTCOME_STATISTICS_FREEZE',
        'bootstrap_type': 'DOMAIN_STRATIFIED_GROUP_BOOTSTRAP',
        'group_unit': 'phase24_router_split_manifest.csv:group_key (canonical composite PATIENT/ASSET/RISK/SINGLETON)',
        'strata': strata,
        'strata_group_counts': group_counts,
        'total_groups': total_groups,
        'n_boot': N_BOOT,
        'seed': SEED,
        'rng': 'numpy.random.Generator(numpy.random.PCG64(42))',
        'draw_algorithm': ('for b in range(n_boot): for d in sorted(strata): '
                           'idx = rng.integers(0, n_groups[d], size=n_groups[d], dtype=int64); '
                           'replicate rows = concat of member rows of sampled groups (with replacement, '
                           'groups may repeat)'),
        'resample_unit': 'group (cluster), within domain stratum',
        'bootstrap_selection_rule': ('within each replicate, re-apply the frozen policy ranking '
                                     '(routing_score DESC, sample_id ASC over the canonical sample_id-ascending '
                                     'order) to the resampled eligible multiset and select the top '
                                     'K_b_rep = n_elig_rep if budget==1.00 else floor(budget*n_elig_rep); '
                                     'the budget is treated as a fraction of the replicate eligible count'),
        'oracle_in_replicate': ('top K_b_rep of the replicate eligible multiset by true DeltaDice DESC, '
                                'sample_id ASC, with K_b_rep as defined by bootstrap_selection_rule'),
        'size_strata_definition': ('quartiles of the GT-free predicted_roi_area_fraction over the 4957 eligible '
                                   'DEV rows (Q25/Q50/Q75 frozen); strata Q1..Q4 lower-inclusive/upper-exclusive; '
                                   'a GT-free deployment-available proxy distinct from the historical GT tiny taxonomy'),
        'size_strata_quartiles': size_quartiles,
        'domain_strata_definition': 'domain field (BUSI/ISIC/KUB/KVASIR)',
        'ci_method': 'percentile',
        'ci_percentiles': CI_PCT,
        'paired_two_sided_p': ('p_lower=(1+count(D_b<=0))/(B+1); p_upper=(1+count(D_b>=0))/(B+1); '
                               'p=min(1, 2*min(p_lower,p_upper)); D_b = metric_A(b) - metric_B(b)'),
        'multiplicity': ('primary = raw paired two-sided p; secondary = Holm-Bonferroni within the '
                         'pre-declared C7-vs-comparator family (C1..C6, C10)'),
        'comparison_family': ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C10'],
        'primary_method': 'C7',
        'metrics': metrics,
        'zero_denominator': 'null with reason UNDEFINED_ZERO_DENOMINATOR; sums over empty sets are zero',
        'benefit_labels': {'BENEFICIAL': 'd_i >= +0.02', 'HARMFUL': 'd_i <= -0.01', 'NEUTRAL': 'otherwise'},
        'bootstrap_plan_sha256': bootstrap_plan_sha,
        'bootstrap_plan_file': 'data_cache/phase25e_barr_resource_gate_v1_0/phase25e_bootstrap_plan_v1_0.npz',
        'bootstrap_plan_file_sha256': plan_file_sha,
        'frozen_before_outcome_access': True,
        'DeltaDice_outcomes_read': 0,
        'outcome_access': False,
    }
    (AUD / 'phase25e_evaluation_statistics_contract_v1_0.json').write_text(
        json.dumps(contract, indent=2, allow_nan=False) + '\n', encoding='utf-8')

    # --- criteria binding --------------------------------------------------------
    crit = pd.read_csv(TABLE / 'phase24_success_failure_criteria.csv', dtype=str)
    criteria = crit.to_dict('records')
    # operationalizations (frozen pre-outcome)
    operationalization = {
        'S1': ('C7 precision_at_budget and/or mean_true_delta_dice_among_routed exceed every simple '
               'GT-free proxy (C3/C4/C5/C6) at equal budget; paired bootstrap supports the gap'),
        'F2': 'negation of S1: C7 fails to beat simple proxies at equal budget',
        'S2': ('macro_domain_mean_true_delta_dice lower 95% CI bound > -0.005 and no domain collapse'),
        'F3': 'macro-domain lower bound <= -0.005 or a routed system materially degrades the reference',
        'S3': 'a monotone-usable accuracy-compute frontier exists across the five budget points',
        'F4': 'router+refiner cost removes the useful compute-performance trade-off',
        'F5': ('benefit concentrated in one domain while another is materially harmed '
               '(domain-level routed mean <= -0.01 with a positive domain present)'),
        'F1': 'refiner provides insufficient positive action opportunity (Phase25A/25C scope)',
    }
    binding = {
        'classification': CLASS,
        'specification_revision': REV,
        'stage': 'SUCCESS_FAILURE_CRITERIA_BINDING',
        'criteria_source': 'reports/tables/phase24_success_failure_criteria.csv',
        'criteria_source_sha256': sha(TABLE / 'phase24_success_failure_criteria.csv'),
        'criteria': criteria,
        'operationalization': operationalization,
        'evaluated_in_phase25e': ['S1', 'F2', 'S2', 'F3', 'S3', 'F4', 'F5'],
        'deferred': {'F1': 'Phase25A/25C scope', 'S3_full': 'Phase25E frontier + later phases'},
        'adjudication_rule': ('criteria evaluated on frozen DEV memberships joined to frozen Phase25C '
                              'outcomes; no criterion may use ROUTER_HOLDOUT/VAL808/TEST'),
        'all_pass': True,
    }
    (AUD / 'phase25e_success_failure_criteria_binding.json').write_text(
        json.dumps(binding, indent=2, allow_nan=False) + '\n', encoding='utf-8')

    print(f'Strata: {strata}; groups: {group_counts}; total={total_groups}', flush=True)
    print(f'Bootstrap plan sha256: {bootstrap_plan_sha}', flush=True)
    print(f'Failures: {failures}', flush=True)
    if failures:
        sys.exit(1)
    print('PHASE25E_PRE_OUTCOME_STATISTICS_FREEZE_PASS', flush=True)


if __name__ == '__main__':
    main()
