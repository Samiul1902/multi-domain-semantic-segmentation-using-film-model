"""Phase25E FINAL-ROUTER DEV DEPLOYMENT-SCORE CALIBRATION (outcome-blind).

Loads the frozen final Phase25D checkpoint and runs it on the 4957
ROUTER_DEVELOPMENT feature rows ONLY. Derives the deployment rank order,
per-budget rank boundaries and tau for the frozen C7/C8 policies. NO outcome
column is read; NO ROUTER_HOLDOUT / VAL808 / TEST.

Persists:
  data_cache/phase25e_barr_resource_gate_v1_0/phase25e_final_router_dev_scores.csv
  reports/tables/phase25e_final_router_dev_thresholds.csv
  reports/audits/phase25e_final_router_dev_calibration.json
"""
import csv
import hashlib
import json
import sys
from fractions import Fraction
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn

ROOT = Path(__file__).resolve().parents[2]
AUD = ROOT / 'reports/audits'
TABLE = ROOT / 'reports/tables'
CACHE = ROOT / 'data_cache/phase25e_barr_resource_gate_v1_0'
CKPT = ROOT / 'checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt'
CACHE25B = ROOT / 'data_cache/phase25b_barr_pre_refinement_features_v1_2'
REV = 'ra_medfilm_barr_resource_gate_v1_0'
CLASS = 'PHASE25E_RESOURCE_GATE_POLICY_EVALUATION'
EXPECTED_CKPT_SHA = '8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b'
SCALAR_NORMALIZE_IDX = [192, 193, 194, 195, 196, 197, 200, 201]
BUDGETS = [('0.00', 0), ('0.10', 495), ('0.25', 1239), ('0.50', 2478), ('1.00', 4957)]
LAMBDAS = ['0.00', '0.25', '0.50', '1.00']


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def rational(x):
    return f'{x.numerator}/{x.denominator}'


class BARRBenefitRouterV1(nn.Module):
    def __init__(self):
        super().__init__()
        self.task_embedding = nn.Embedding(4, 16)
        self.net = nn.Sequential(
            nn.Linear(218, 128),
            nn.LayerNorm(128, elementwise_affine=True),
            nn.SiLU(),
            nn.Dropout(0.10),
            nn.Linear(128, 64),
            nn.LayerNorm(64, elementwise_affine=True),
            nn.SiLU(),
            nn.Dropout(0.10),
            nn.Linear(64, 1),
        )

    def forward(self, x_numeric, task_ids):
        emb = self.task_embedding(task_ids)
        x = torch.cat([x_numeric, emb], dim=-1)
        return self.net(x).squeeze(-1)


def main():
    failures = []
    ckpt_sha = sha(CKPT)
    if ckpt_sha != EXPECTED_CKPT_SHA:
        failures.append(f'CKPT_SHA:{ckpt_sha}')
        print(failures, flush=True)
        sys.exit(1)

    ck = torch.load(CKPT, map_location='cpu', weights_only=False)
    model = BARRBenefitRouterV1()
    model.load_state_dict(ck['model_state'])
    model.eval()
    n_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    if n_params != 36801:
        failures.append(f'PARAM_COUNT:{n_params}')

    # DEV identity + conditioning from an outcome-blind source
    meta = pd.read_csv(CACHE25B / 'metadata.csv',
                       usecols=['feature_row_index', 'sample_id', 'task_id', 'domain', 'action_available'],
                       dtype={'sample_id': str})
    meta = meta.sort_values('feature_row_index', kind='stable').reset_index(drop=True)
    if len(meta) != 4957 or meta.feature_row_index.tolist() != list(range(4957)):
        failures.append('META_ORDER')
    ids = meta.sample_id.tolist()
    task_ids = meta.task_id.to_numpy(np.int64)
    eligible = meta.action_available.to_numpy().astype(bool)
    if int(eligible.sum()) != 4957:
        failures.append(f'ELIGIBLE:{int(eligible.sum())}')

    features = np.load(CACHE25B / 'features.npy').astype(np.float32)
    if features.shape != (4957, 202):
        failures.append(f'FEATURE_SHAPE:{features.shape}')

    # Normalization from the frozen checkpoint, cross-checked vs the CSV
    mu = np.asarray(ck['normalizer_mu'], dtype=np.float64).reshape(-1)
    sigma = np.asarray(ck['normalizer_sigma'], dtype=np.float64).reshape(-1)
    const_mask = np.asarray(ck['normalizer_constant_mask'], dtype=bool).reshape(-1)
    norm_csv = pd.read_csv(TABLE / 'phase25d_final_normalization_stats.csv')
    # CSV stores truncated decimals (~9 sig figs) of the float32 checkpoint stats.
    for i, idx in enumerate(SCALAR_NORMALIZE_IDX):
        row = norm_csv.loc[norm_csv.scalar_index == idx].iloc[0]
        if not (np.isclose(float(row.mu), mu[i], rtol=1e-6, atol=1e-9)
                and np.isclose(float(row.sigma), sigma[i], rtol=1e-6, atol=1e-9)):
            failures.append(f'NORM_STATS_MISMATCH:{idx}')

    sigma_safe = np.where(sigma < 1e-12, 1.0, sigma)
    x = features.copy()
    norm = (features[:, SCALAR_NORMALIZE_IDX].astype(np.float64) - mu) / sigma_safe
    norm[:, const_mask] = 0.0
    x[:, SCALAR_NORMALIZE_IDX] = norm.astype(np.float32)

    with torch.no_grad():
        out = model(torch.from_numpy(np.array(x, copy=True)),
                    torch.from_numpy(np.array(task_ids, copy=True))).numpy().astype(np.float64)
    if not np.isfinite(out).all():
        failures.append('NONFINITE_OUTPUT')

    scores = {sid: Fraction(str(float(v))) for sid, v in zip(ids, out)}
    order = sorted([i for i in range(len(ids)) if eligible[i]],
                   key=lambda i: (-scores[ids[i]], ids[i]))

    # persist raw DEV scores
    score_path = CACHE / 'phase25e_final_router_dev_scores.csv'
    with score_path.open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerow(['sample_id', 'feature_row_index', 'domain', 'task_id',
                    'delta_hat_final_dev', 'delta_hat_final_dev_exact'])
        for i, sid in enumerate(ids):
            w.writerow([sid, i, meta.domain.iloc[i], int(task_ids[i]),
                        format(float(out[i]), '.17g'), rational(scores[sid])])

    # per-budget rank boundaries + tau (C7 deployment; C8 identical under constant cost)
    rows = []
    selected_sets = {}
    for b, k in BUDGETS:
        sel = set(order[:k])
        selected_sets[b] = sel
        if k == 0:
            low = high = tau = ''
            tied = False
            policy = 'EXECUTE_NONE'
        elif k == len(order):
            low = high = tau = ''
            tied = False
            policy = 'EXECUTE_ALL_ELIGIBLE'
        else:
            high = scores[ids[order[k - 1]]]
            low = scores[ids[order[k]]]
            tied = high == low
            tau = '' if tied else (high + low) / 2
            policy = 'EXACT_BUDGET_REQUIRES_DETERMINISTIC_TIE_BREAK' if tied else 'SCALAR_TAU_EQUIVALENT'
        rows.append({
            'policy_id': f'C7_final_dev_budget{b}', 'comparator': 'C7', 'budget': b, 'K_b': k,
            'selected_count': len(sel),
            'tau_low': rational(low) if low != '' else '',
            'tau_high': rational(high) if high != '' else '',
            'tau': rational(tau) if tau != '' else '',
            'boundary_tied': tied,
            'sample_id_cutoff_rank_K': ids[order[k - 1]] if k >= 1 else '',
            'sample_id_cutoff_rank_K1': ids[order[k]] if k < len(order) else '',
            'threshold_policy': policy,
        })
    thr_path = TABLE / 'phase25e_final_router_dev_thresholds.csv'
    with thr_path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n')
        w.writeheader()
        w.writerows(rows)

    audit = {
        'classification': CLASS,
        'specification_revision': REV,
        'stage': 'FINAL_ROUTER_DEV_CALIBRATION',
        'checkpoint_sha256': ckpt_sha,
        'checkpoint_epoch': int(ck['epoch']),
        'parameter_count': n_params,
        'population': 'ROUTER_DEVELOPMENT only (4957)',
        'normalization_source': 'frozen final checkpoint (cross-checked vs phase25d_final_normalization_stats.csv)',
        'dev_scores_sha256': sha(score_path),
        'dev_thresholds_sha256': sha(thr_path),
        'thresholds': rows,
        'c8_equals_c7_under_constant_cost': True,
        'lambda_grid': LAMBDAS,
        'outcome_access': False,
        'DeltaDice_outcomes_read': 0,
        'router_holdout_reads': 0,
        'VAL808_reads': 0,
        'TEST_reads': 0,
        'checks': {
            'checkpoint_sha_exact': ckpt_sha == EXPECTED_CKPT_SHA,
            'param_count_36801': n_params == 36801,
            'finite_scores': bool(np.isfinite(out).all()),
            'all_eligible': int(eligible.sum()) == 4957,
            'norm_stats_consistent': not any('NORM_STATS_MISMATCH' in x for x in failures),
        },
        'failures': failures,
        'all_pass': not failures,
    }
    (AUD / 'phase25e_final_router_dev_calibration.json').write_text(
        json.dumps(audit, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    print(f'DEV scores: {len(ids)}; thresholds: {len(rows)}', flush=True)
    print(f'Failures: {failures}', flush=True)
    if failures:
        sys.exit(1)
    print('PHASE25E_FINAL_ROUTER_DEV_CALIBRATION_PASS', flush=True)


if __name__ == '__main__':
    main()
