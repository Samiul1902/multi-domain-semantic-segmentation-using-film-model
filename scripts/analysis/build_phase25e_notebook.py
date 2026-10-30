"""Build the canonical Phase25E reviewer notebook (executed, deterministic).

Reads frozen Phase25E tables/audits only; no model imports, no outcome re-derivation.
"""
import base64
import hashlib
import io
import json
import re
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[2]
AUD = ROOT / 'reports/audits'
TABLE = ROOT / 'reports/tables'
FIG = ROOT / 'reports/figures'
NB = ROOT / 'notebooks/phasewise/phase_25e_resource_gate/phase25e_resource_gate.ipynb'
REV = 'ra_medfilm_barr_resource_gate_v1_0'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build_inputs():
    inputs = {}
    for p in sorted(TABLE.glob('phase25e_*.csv')):
        inputs[p.relative_to(ROOT).as_posix()] = sha(p)
    for p in sorted(FIG.glob('p25e_*.png')):
        inputs[p.relative_to(ROOT).as_posix()] = sha(p)
    for name in ['phase25e_policy_eval_entry_gate', 'phase25e_membership_immutability_audit',
                 'phase25e_evaluation_statistics_contract_v1_0', 'phase25e_success_failure_criteria_binding',
                 'phase25e_final_router_dev_calibration', 'phase25e_pre_outcome_freeze',
                 'phase25e_policy_evaluation_summary', 'phase25e_adjudication',
                 'phase25e_resource_cost_contract_v1_0', 'phase25e_fixed_budget_contract_v1_0',
                 'phase25e_lambda_grid_contract_v1_0', 'phase25e_tie_break_contract_v1_0',
                 'phase25e_comparator_direction_contract_v1_0', 'phase25e_execution_metrics_contract_v1_0',
                 'phase25e_cost_variability_and_policy_redundancy_audit']:
        p = AUD / (name + '.json')
        inputs[p.relative_to(ROOT).as_posix()] = sha(p)
    return inputs


SETUP = '''from pathlib import Path
import base64, hashlib, io, json
import numpy as np
import pandas as pd
from IPython.display import display, HTML, Image

ROOT = Path.cwd()
while not (ROOT / 'reports/audits/phase25e_adjudication.json').exists() and ROOT.parent != ROOT:
    ROOT = ROOT.parent
INPUTS = __INPUTS__
for relative, expected in INPUTS.items():
    actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    assert actual == expected, relative

def read_csv(rel):
    assert rel in INPUTS
    return pd.read_csv(ROOT / rel, dtype={'budget': str, 'lambda': str})
def read_json(rel):
    assert rel in INPUTS
    return json.loads((ROOT / rel).read_text())
def table(df, name):
    display(HTML('<h3>' + name + '</h3>' + df.to_html(index=False, max_rows=None, max_cols=None)))
def show_fig(rel):
    assert rel in INPUTS
    display(Image(data=base64.b64decode(base64.b64encode((ROOT / rel).read_bytes())), format='png'))
print('Phase25E frozen inputs bound:', len(INPUTS))
'''

CELLS = [
    ('markdown', """# Phase 25E - Canonical Resource-Gate Policy Evaluation

**Method**: `RA-MedFiLM-BARR` - resource-gate revision `ra_medfilm_barr_resource_gate_v1_0`.

This notebook evaluates the **45 frozen prospective policies** (comparators C3-C8 across the
five fixed budgets and the four lambda values) on the 4957 `ROUTER_DEVELOPMENT` rows, after
joining the frozen OOF memberships to the frozen Phase25C paired-gain outcomes.

**Hard scope**: `ROUTER_DEVELOPMENT` only. `ROUTER_HOLDOUT` (875), `VAL808` and `TEST` are
never read. The oracle (C10) is a **nondeployable development upper bound**. TEST is locked
until Phase39. No lambda is selected; the resource gate is not calibrated for deployment here
beyond the frozen DEV-score thresholds.

Ordering guarantee: memberships, statistics and final-router DEV thresholds were frozen
**before** any outcome column was opened (`phase25e_pre_outcome_freeze.json`)."""),
    ('code', 'setup'),
    ('markdown', "## 1. Frozen contract binding\n\nCost, budget, lambda, tie-break and comparator rules are read from the frozen specification."),
    ('code', """cost = read_json('reports/audits/phase25e_resource_cost_contract_v1_0.json')
budget = read_json('reports/audits/phase25e_fixed_budget_contract_v1_0.json')
lam = read_json('reports/audits/phase25e_lambda_grid_contract_v1_0.json')
tie = read_json('reports/audits/phase25e_tie_break_contract_v1_0.json')
comp = read_json('reports/audits/phase25e_comparator_direction_contract_v1_0.json')
table(pd.DataFrame([
    ['global MACs', cost['global_macs']],
    ['regional-refiner MACs', cost['regional_refiner_macs']],
    ['router MACs (excluded from C_i)', cost['router_macs']],
    ['cost exact ratio', cost['cost_exact_ratio']],
    ['cost decimal', cost['cost_decimal']],
    ['budgets', ','.join(budget['budgets'])],
    ['lambda grid', ','.join(lam['lambda_grid'])],
    ['tie rule', tie['rank_rule']],
], columns=['frozen item', 'value']), 'Frozen resource-gate contract')
table(pd.read_csv(ROOT / 'reports/tables/phase25e_fixed_budget_cardinalities.csv'), 'Fixed-budget cardinalities')"""),
    ('markdown', "## 2. Membership immutability\n\nThe 45 prospective membership tables were frozen before outcome access and are re-hashed here."),
    ('code', """manifest = read_csv('reports/tables/phase25e_policy_membership_manifest.csv')
imm = read_json('reports/audits/phase25e_membership_immutability_audit.json')
table(manifest[['policy_id','comparator','lambda','budget','N_eligible','K_b','selected_count','threshold_policy']],
      'Frozen policy membership manifest (45 policies)')
print('all membership SHAs exact:', imm['checks']['all_45_shas_exact'])
print('C8 redundant with C7:', imm['checks']['c8_redundant_with_c7'])"""),
    ('markdown', "## 3. Policy evaluation metrics\n\nPoint metrics for every frozen policy on the full DEV population."),
    ('code', """met = read_csv('reports/tables/phase25e_policy_evaluation_metrics.csv')
key = ['C1','C2','C3','C4','C5','C6','C7','C10']
sub = met[met.comparator.isin(key)][['comparator','budget','K','precision_at_budget',
      'mean_true_delta_dice_among_routed','benefit_capture_at_budget','harmful_activation_rate',
      'routing_regret_vs_oracle','average_total_analytical_macs']]
table(sub, 'Equal-budget policy metrics (C7/C8 identical under constant action cost)')
show_fig('reports/figures/p25e_precision_vs_budget.png')
show_fig('reports/figures/p25e_mean_delta_vs_budget.png')"""),
    ('markdown', "## 4. Oracle upper bound and compute frontier\n\nC10 is the nondeployable true-DeltaDice top-K upper bound."),
    ('code', """table(read_csv('reports/tables/phase25e_oracle_upper_bound.csv')[['policy_id','budget','K',
      'precision_at_budget','mean_true_delta_dice_among_routed','benefit_capture_at_budget']],
      'Oracle (C10) upper bound - NONDEPLOYABLE')
show_fig('reports/figures/p25e_compute_frontier.png')
show_fig('reports/figures/p25e_regret_vs_budget.png')"""),
    ('markdown', "## 5. C7/C8 structural redundancy\n\nBecause the incremental action cost is constant across eligible rows, `lambda` cannot change the fixed-budget ranking."),
    ('code', """red = read_csv('reports/tables/phase25e_c7_c8_redundancy.csv')
table(red, 'C7/C8 membership and metric equivalence')
print('all C7/C8 memberships equal:', bool(red.same_membership.all()))
show_fig('reports/figures/p25e_c7_c8_redundancy.png')"""),
    ('markdown', "## 6. Domain and size-stratum reporting"),
    ('code', """dom = read_csv('reports/tables/phase25e_domain_reporting.csv')
table(dom[(dom.comparator=='C7')][['budget','domain','n_routed','mean_true_delta_dice',
      'precision_at_budget','harmful_activation_rate']], 'C7 routed metrics by domain')
show_fig('reports/figures/p25e_domain_breakdown.png')
size = read_csv('reports/tables/phase25e_size_strata_reporting.csv')
table(size[(size.comparator=='C7')][['budget','size_stratum','n_routed','mean_true_delta_dice',
      'precision_at_budget']], 'C7 routed metrics by GT-free ROI-size stratum')
show_fig('reports/figures/p25e_size_strata.png')"""),
    ('markdown', "## 7. Domain-stratified group bootstrap\n\n2000 replicates, seed 42, percentile 95% CI, paired two-sided p (Holm-adjusted within the C7-vs-comparator family)."),
    ('code', """stats = read_json('reports/audits/phase25e_evaluation_statistics_contract_v1_0.json')
print('bootstrap:', stats['bootstrap_type'], '| n_boot', stats['n_boot'], '| seed', stats['seed'])
print('plan sha256:', stats['bootstrap_plan_sha256'])
boot = read_csv('reports/tables/phase25e_bootstrap_ci.csv')
sel = boot[boot.policy_id.str.match(r'C[3-7]_budget')][['policy_id','precision_at_budget_mean',
      'precision_at_budget_ci_low','precision_at_budget_ci_high','mean_true_delta_dice_among_routed_mean',
      'mean_true_delta_dice_among_routed_ci_low','mean_true_delta_dice_among_routed_ci_high']]
table(sel, 'Bootstrap CIs for deployable comparators')
paired = read_csv('reports/tables/phase25e_paired_bootstrap_tests.csv')
table(paired[(paired.metric=='precision_at_budget')][['budget','comparator','mean_diff','paired_p_raw','holm_adjusted_p','n_pairs']],
      'Paired tests: C7 vs comparators (precision@budget)')
show_fig('reports/figures/p25e_bootstrap_ci_precision.png')"""),
    ('markdown', "## 8. Adjudication against the frozen Phase24 criteria"),
    ('code', """adj = read_json('reports/audits/phase25e_adjudication.json')
table(pd.DataFrame([
    ['S1 H1 status', adj['S1_H1_status']],
    ['S1 per-budget pass', json.dumps(adj['S1_budget_pass'])],
    ['F2 router failure', adj['F2_router_failure']],
    ['S2 preservation satisfied', adj['S2_preservation_satisfied']],
    ['F3 preservation failure', adj['F3_preservation_failure']],
    ['S3 frontier measured', adj['S3_frontier_measured']],
    ['F4 resource failure', adj['F4_resource_failure']],
    ['F5 domain collapse', adj['F5_domain_collapse_triggered']],
], columns=['criterion','outcome']), 'Phase24 criteria adjudication')
table(pd.DataFrame(adj['S1_detail']), 'S1 detail: C7 vs simple GT-free proxies (Holm-adjusted)')
summary = read_json('reports/audits/phase25e_policy_evaluation_summary.json')
print('policies:', summary['policy_count'], '| bootstrap replicates:', summary['bootstrap_replicates'])
print('holdout reads:', summary['router_holdout_reads'], '| VAL808:', summary['VAL808_reads'], '| TEST:', summary['TEST_reads'])"""),
    ('markdown', """## 9. Conclusions (scoped)

- The learned paired-gain router (C7) **significantly beats every simple GT-free proxy on
  precision@budget at the tight budget (10%)**, with the advantage shrinking to statistical
  non-significance at 25% and 50% (entropy and margin proxies are competitive there).
- Preservation holds: the macro-domain mean routed gain lower 95% CI bound stays above
  -0.005 at every budget, and no domain collapse is observed.
- A usable accuracy-compute frontier exists across the five budget points (S3).
- `C8` is structurally redundant with `C7` under the constant incremental action cost.

**Scope guard**: `ROUTER_HOLDOUT`, `VAL808` and `TEST` were never read. The oracle is a
nondeployable development upper bound. H1 wording is therefore scoped to the integrated
GT-free paired-gain router at tight budgets (Level-2 novelty)."""),
]


def normalize(nb):
    for cell in nb.cells:
        if 'metadata' in cell and 'execution' in cell['metadata']:
            del cell['metadata']['execution']
        for out in cell.get('outputs', []):
            out.get('metadata', {}).pop('execution', None)
    return nb


def build():
    inputs = build_inputs()
    nb = nbformat.v4.new_notebook()
    nb.metadata = {'kernelspec': {'display_name': 'jup-venv', 'language': 'python', 'name': 'jup-venv'},
                   'language_info': {'name': 'python'}}
    for i, (kind, src) in enumerate(CELLS):
        if kind == 'markdown':
            cell = nbformat.v4.new_markdown_cell(src)
        else:
            code = SETUP.replace('__INPUTS__', json.dumps(inputs, indent=0, sort_keys=True)) if src == 'setup' else src
            cell = nbformat.v4.new_code_cell(code)
        cell['id'] = f'p25e-cell-{i:02d}'
        nb.cells.append(cell)
    client = NotebookClient(nb, kernel_name='jup-venv', timeout=600, allow_errors=False)
    client.execute()
    normalize(nb)
    NB.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(nb, NB)
    return sha(NB)


if __name__ == '__main__':
    print('notebook sha256:', build())
