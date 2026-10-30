"""Build the Phase25E reviewer notebook WITH the post-closure reconciliation addendum.

Archive-and-rebuild:
  * the pre-reconciliation canonical notebook is copied to
    reports/audits/phase25e_reconciliation_archive/phase25e_resource_gate__pre_reconciliation.ipynb
    (provenance) and its SHA is recorded;
  * the canonical notebook is rebuilt = original cells (unchanged) + an ADDITIVE
    reconciliation addendum that (a) records the multiplicity-provenance finding,
    (b) presents the reconciled PRIMARY adjudication (raw paired p) alongside the
    retained secondary Holm sensitivity, (c) states the preservation scope and the
    corrected model-execution wording, and (d) lists the original statements that
    are SUPERSEDED.

Only frozen tables/audits are read. No model import, no outcome re-derivation.
"""
import hashlib
import json
import shutil
from pathlib import Path

import nbformat
from nbclient import NotebookClient

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_phase25e_notebook as base  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
AUD = ROOT / 'reports/audits'
NB = base.NB
ARCHIVE_DIR = AUD / 'phase25e_reconciliation_archive'
ARCHIVE = ARCHIVE_DIR / 'phase25e_resource_gate__pre_reconciliation.ipynb'
PRE_RECON_SHA = 'e5d8f5657b43a18fd87e50bcf6f4834bcdd94dcbb2def0ef02ce720f0f1d7718'

ADDENDUM_INPUTS = [
    'reports/audits/phase25e_postclosure_reconciliation_entry_gate.json',
    'reports/audits/phase25e_multiplicity_provenance_audit.json',
    'reports/audits/phase25e_adjudication_reconciled.json',
    'reports/audits/phase25e_preservation_scope_clarification.json',
    'reports/audits/phase25e_model_execution_wording_reconciliation.json',
    'reports/tables/phase25e_s1_primary_vs_multiplicity_sensitivity.csv',
]

ADDENDUM = [
    ('markdown', """## 10. Post-closure statistical-adjudication reconciliation (addendum)

**Status**: additive reconciliation of the Phase25E closure. No raw scientific value is
changed — no membership, bootstrap replicate, model weight, prediction or metric is
recomputed. Only the *decision rule* used for the S1/H1 significance call is repaired.

**Finding.** The frozen Phase24 pre-registration declares a paired bootstrap with a
"paired p-value where appropriate" and **no multiplicity correction at all**. The frozen
Phase25E statistics contract (`phase25e_evaluation_statistics_contract_v1_0.json`) states
verbatim:

> `multiplicity`: *primary = raw paired two-sided p; secondary = Holm-Bonferroni within the
> pre-declared C7-vs-comparator family (C1..C6, C10)*

The post-outcome closure adjudication nonetheless used **Holm-Bonferroni as the primary
significance gate**. Holm was therefore never pre-registered as the *primary* rule; promoting
it to primary is an **unauthorized extension** of the frozen protocol. The reconciliation
restores the frozen primary statistic (the raw paired two-sided p) and retains Holm only as a
conservative secondary sensitivity. This follows from protocol provenance, **not** from which
result looks stronger."""),
    ('code', """prov = read_json('reports/audits/phase25e_multiplicity_provenance_audit.json')
print('classification:', prov['classification_code'], '-', prov['classification_label'])
print('frozen multiplicity clause:', prov['frozen_multiplicity_clause'])
print('Phase24 pre-registration artifacts mentioning multiplicity:',
      len(prov['phase24_artifacts_mentioning_multiplicity']))
print('material sensitivity rows (raw p vs Holm):', prov['material_sensitivity_count'])"""),
    ('markdown', """### 10.1 Primary (raw paired p) vs secondary (Holm) adjudication

The table below reports every budget/comparator/metric where the raw paired two-sided p and the
Holm-adjusted p give a different 5% significance call. Exactly two precision rows flip — both at
the 25% budget."""),
    ('code', """rec = read_json('reports/audits/phase25e_adjudication_reconciled.json')
sens = read_csv('reports/tables/phase25e_s1_primary_vs_multiplicity_sensitivity.csv')
table(sens[sens.metric=='precision_at_budget'][['budget','comparator','mean_diff','paired_p_raw',
      'raw_significant_at_0.05','holm_adjusted_p','holm_significant_at_0.05',
      'primary_decision_changed_by_holm']],
      'S1 precision@budget: PRIMARY raw p vs SECONDARY Holm')
table(pd.DataFrame([
    ['primary decision rule', rec['primary_decision_rule']],
    ['secondary decision rule', rec['secondary_decision_rule']],
    ['holm primary role', rec['holm_primary_role']],
    ['holm secondary role', rec['holm_secondary_role']],
    ['S1/H1 (PRIMARY, raw p)', rec['S1_H1_status']],
    ['S1 budget pass (PRIMARY)', json.dumps(rec['S1_budget_pass'])],
    ['S1/H1 (SECONDARY, Holm)', rec['S1_status_under_secondary_holm']],
    ['S1 budget pass (SECONDARY)', json.dumps(rec['S1_budget_pass_under_secondary_holm'])],
    ['closure original S1/H1', rec['closure_original_S1_H1_status']],
    ['closure original budget pass', json.dumps(rec['closure_original_budget_pass'])],
    ['F2 router failure', rec['F2_router_failure']],
], columns=['item','value']), 'Reconciled adjudication: PRIMARY vs SECONDARY')"""),
    ('markdown', """**Repaired result.** Under the frozen PRIMARY statistic (raw paired two-sided p), C7 beats
all four simple GT-free proxies on precision@budget at the **10% and 25%** budgets, and the
advantage is not significant at the 50% budget. The headline criterion S1/H1 remains
**PARTIAL** (two of three informative budgets pass), but the 25% budget now passes, whereas the
original Holm-primary closure recorded it as failing. Under the conservative secondary Holm
sensitivity only the 10% budget passes. F2 (router failure) is not triggered under either rule."""),
    ('markdown', """### 10.2 Preservation scope and corrected model-execution wording

Two wording records are clarified without touching any number: the exact scope of the S2
preservation claim, and the exact model-execution inventory of the evaluation."""),
    ('code', """psc = read_json('reports/audits/phase25e_preservation_scope_clarification.json')
mex = read_json('reports/audits/phase25e_model_execution_wording_reconciliation.json')
print('S2 preservation satisfied:', psc['satisfied'], '| all macro CI lows > -0.005:',
      psc['all_ci_lows_above_minus_0.005'], '| domain collapse:', psc['domain_collapse_triggered'])
print('preservation covers:', psc['what_the_claim_covers'][0])
print('preservation does NOT cover:', psc['what_the_claim_does_NOT_cover'][0])
print('---')
print('router forwards (frozen inventory):', mex['execution_inventory_frozen']['router_forwards'],
      'over', mex['execution_inventory_frozen']['router_forward_scope'])
print('global forwards:', mex['execution_inventory_frozen']['global_model_forwards'],
      '| refiner forwards:', mex['execution_inventory_frozen']['regional_refiner_forwards'],
      '| training runs:', mex['execution_inventory_frozen']['training_runs'])
print('reconciled wording:', mex['reconciled_wording'])"""),
    ('markdown', """### 10.3 Statements in this notebook that are SUPERSEDED

The following statements, carried over unchanged from the pre-reconciliation build, are
superseded by the reconciliation above and must not be quoted as the current Phase25E result:

- Section 7 / Section 9: that the C7 advantage is significant **only at the 10% budget** and
  non-significant at 25%/50% — under the frozen primary statistic it is significant at
  **10% and 25%**, non-significant only at 50%. (The 25%/50% phrasing reflected the
  Holm-as-primary extension.)
- Any phrasing that implies the evaluation loaded or ran no model at all — exactly **one
  outcome-blind forward pass of the frozen final router** over the 4,957 DEV rows was
  executed; no global-model forward, no refiner forward, no training.

The authoritative primary adjudication is `reports/audits/phase25e_adjudication_reconciled.json`;
the original closure adjudication `reports/audits/phase25e_adjudication.json` is retained
unchanged as provenance.

**Reconciliation terminal**:
`PHASE25E_CANONICAL_ADJUDICATION_REPAIRED__PRIMARY_PHASE24_STATISTICS_RESTORED__HOLM_RETAINED_AS_SENSITIVITY__PHASE25F_ELIGIBLE_NOT_STARTED`."""),
]


def build_inputs():
    inputs = base.build_inputs()
    for rel in ADDENDUM_INPUTS:
        p = ROOT / rel
        assert p.exists(), rel
        inputs[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return inputs


def normalize(nb):
    nb = base.normalize(nb)
    # Canonicalize stdout: nbclient may split one print into several 'stream'
    # outputs depending on flush timing. Merge adjacent same-name streams and
    # coerce the payload to a single string so the bytes are deterministic.
    for cell in nb.cells:
        merged = []
        for out in cell.get('outputs', []):
            if (merged and out.get('output_type') == 'stream'
                    and merged[-1].get('output_type') == 'stream'
                    and merged[-1].get('name') == out.get('name')):
                prev = merged[-1]
                pt = prev.get('text', '')
                pt = ''.join(pt) if isinstance(pt, list) else pt
                at = out.get('text', '')
                at = ''.join(at) if isinstance(at, list) else at
                prev['text'] = pt + at
            else:
                if out.get('output_type') == 'stream' and isinstance(out.get('text'), list):
                    out['text'] = ''.join(out['text'])
                merged.append(out)
        if 'outputs' in cell:
            cell['outputs'] = merged
    return nb


def build():
    # 1. archive the pre-reconciliation notebook (provenance) - first build only
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    if not ARCHIVE.exists():
        pre_sha = hashlib.sha256(NB.read_bytes()).hexdigest()
        assert pre_sha == PRE_RECON_SHA, f'unexpected pre-reconciliation notebook sha {pre_sha}'
        shutil.copy2(NB, ARCHIVE)
    assert hashlib.sha256(ARCHIVE.read_bytes()).hexdigest() == PRE_RECON_SHA

    # 2. rebuild = original cells + additive addendum
    inputs = build_inputs()
    cells = list(base.CELLS) + list(ADDENDUM)
    nb = nbformat.v4.new_notebook()
    nb.metadata = {'kernelspec': {'display_name': 'jup-venv', 'language': 'python', 'name': 'jup-venv'},
                   'language_info': {'name': 'python'}}
    for i, (kind, src) in enumerate(cells):
        if kind == 'markdown':
            cell = nbformat.v4.new_markdown_cell(src)
        else:
            code = (base.SETUP.replace('__INPUTS__', json.dumps(inputs, indent=0, sort_keys=True))
                    if src == 'setup' else src)
            cell = nbformat.v4.new_code_cell(code)
        cell['id'] = f'p25e-cell-{i:02d}'
        nb.cells.append(cell)
    client = NotebookClient(nb, kernel_name='jup-venv', timeout=900, allow_errors=False)
    client.execute()
    normalize(nb)
    NB.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(nb, NB)
    return hashlib.sha256(NB.read_bytes()).hexdigest()


if __name__ == '__main__':
    print('pre-reconciliation notebook sha256:', PRE_RECON_SHA)
    print('archived to:', ARCHIVE.relative_to(ROOT).as_posix())
    print('rebuilt notebook sha256:', build())
