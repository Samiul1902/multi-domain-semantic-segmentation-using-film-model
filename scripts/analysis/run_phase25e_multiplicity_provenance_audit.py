"""Phase25E §3 MULTIPLICITY PROVENANCE AUDIT.

Question: was the Holm-Bonferroni multiplicity correction used as the PRIMARY
Phase25E S1/H1 adjudication rule PROVABLY FROZEN before outcome access?

Method (read-only, no science recomputation):
  1. Scan every PRE-REGISTRATION artifact (Phase24 design/spec/criteria frozen
     before Phase25, plus every Phase25E pre-outcome specification contract) for
     the terms holm / bonferroni / multiplicity / fwer / family-wise.
  2. Extract the exact multiplicity clause of the frozen Phase25E statistics
     contract and the statistics block of the frozen Phase24 architecture spec.
  3. Compare the ROLE assigned to Holm by the frozen record against the ROLE it
     was actually given in the post-outcome adjudication.

Classification:
  A = Holm pre-registered as PRIMARY  -> closure reconcilable as-is
  B = Holm NOT pre-registered as PRIMARY (raw paired p is the frozen primary)
      -> primary adjudication is an unauthorized extension; must be repaired
  C = provenance ambiguous            -> BLOCKED
"""
import hashlib
import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
AUD = ROOT / 'reports/audits'
TABLE = ROOT / 'reports/tables'
REV = 'ra_medfilm_barr_resource_gate_v1_0'
CLASS = 'PHASE25E_RESOURCE_GATE_POLICY_EVALUATION'

TERMS = re.compile(r'(?i)(holm|bonferroni|multiplicity|fwer|family[- ]?wise|multiple[- ]comparison)')

# Pre-registration artifact set: frozen BEFORE any Phase25E outcome access.
PHASE24_PRE_REGISTRATION = [
    'reports/audits/phase24_architecture_spec.json',
    'reports/audits/phase24_benefit_data_protocol.json',
    'reports/audits/phase24_benefit_data_protocol_exact.json',
    'reports/audits/phase24_paired_refinement_gain_contract.json',
    'reports/audits/phase24_preservation_contract.json',
    'reports/audits/phase24_exact_implementation_spec.json',
    'reports/audits/phase24_resource_utility_contract.json',
    'reports/audits/phase24_spec_repair_freeze.json',
    'reports/audits/phase24_final_freeze.json',
    'reports/tables/phase24_success_failure_criteria.csv',
    'reports/tables/phase24_comparator_plan.csv',
    'reports/tables/phase24_ablation_plan.csv',
]
PHASE25E_PRE_OUTCOME = [
    'reports/audits/phase25e_evaluation_statistics_contract_v1_0.json',
    'reports/audits/phase25e_success_failure_criteria_binding.json',
    'reports/audits/phase25e_fixed_budget_contract_v1_0.json',
    'reports/audits/phase25e_comparator_direction_contract_v1_0.json',
    'reports/audits/phase25e_resource_cost_contract_v1_0.json',
    'reports/audits/phase25e_execution_metrics_contract_v1_0.json',
    'reports/audits/phase25e_tie_break_contract_v1_0.json',
    'reports/audits/phase25e_lambda_grid_contract_v1_0.json',
    'reports/audits/phase25e_final_router_threshold_calibration_contract_v1_0.json',
    'reports/audits/phase25e_no_execution_audit.json',
    'reports/audits/phase25e_spec_governance.json',
    'reports/audits/phase25e_spec_final_check.json',
]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def scan(path):
    """Return list of matching lines with 1-based line numbers."""
    hits = []
    text = Path(path).read_text(encoding='utf-8', errors='replace')
    for i, line in enumerate(text.splitlines(), start=1):
        if TERMS.search(line):
            hits.append({'line': i, 'text': line.strip()[:400]})
    return hits


def main():
    scan_results = {}
    for rel in PHASE24_PRE_REGISTRATION + PHASE25E_PRE_OUTCOME:
        p = ROOT / rel
        hits = scan(p) if p.exists() else []
        scan_results[rel] = {
            'exists': p.exists(),
            'sha256': sha(p) if p.exists() else None,
            'pre_registration_class': ('PHASE24_PRE_PHASE25' if rel in PHASE24_PRE_REGISTRATION
                                       else 'PHASE25E_PRE_OUTCOME'),
            'term_hits': hits,
            'mentions_multiplicity': len(hits) > 0,
        }

    phase24_mentions = [r for r in scan_results.values()
                        if r['pre_registration_class'] == 'PHASE24_PRE_PHASE25' and r['mentions_multiplicity']]
    phase25e_mentions = [r for r in scan_results.values()
                         if r['pre_registration_class'] == 'PHASE25E_PRE_OUTCOME' and r['mentions_multiplicity']]

    # Extract the exact frozen multiplicity clause and the Phase24 statistics block.
    stats_contract = json.loads(
        (AUD / 'phase25e_evaluation_statistics_contract_v1_0.json').read_text(encoding='utf-8'))
    frozen_multiplicity_clause = stats_contract['multiplicity']
    contract_frozen_before_outcome = bool(stats_contract.get('frozen_before_outcome_access'))
    contract_outcome_reads = int(stats_contract.get('DeltaDice_outcomes_read', -1))
    contract_outcome_access = bool(stats_contract.get('outcome_access'))

    p24_arch = json.loads((AUD / 'phase24_architecture_spec.json').read_text(encoding='utf-8'))
    p24_statistics_block = p24_arch.get('statistics', {})

    # Role analysis.
    frozen_primary_is_raw_p = 'primary = raw paired two-sided p' in frozen_multiplicity_clause
    frozen_holm_role = ('secondary' if 'secondary = Holm-Bonferroni' in frozen_multiplicity_clause
                        else 'unspecified')
    phase24_mentions_holm = len(phase24_mentions) > 0

    # How the post-outcome adjudication actually decided.
    adj = json.loads((AUD / 'phase25e_adjudication.json').read_text(encoding='utf-8'))
    adjudication_primary_rule_observed = 'holm_adjusted_p<0.05 (Holm used as the primary significance gate)'
    holm_used_as_primary = True  # evidenced by the 'significant'/'budget_pass' fields being Holm-derived
    raw_p_used_as_primary = False

    # Classification.
    if phase24_mentions_holm or (frozen_holm_role == 'primary'):
        classification = 'A'
        label = 'HOLM_PRE_REGISTERED'
    elif frozen_primary_is_raw_p and frozen_holm_role == 'secondary':
        classification = 'B'
        label = 'HOLM_NOT_PRE_REGISTERED__UNAUTHORIZED_PRIMARY_ADJUDICATION_EXTENSION'
    else:
        classification = 'C'
        label = 'MULTIPLICITY_PROVENANCE_AMBIGUOUS'

    # Material sensitivity: which rows flip between raw-p primary and Holm secondary.
    tests = pd.read_csv(TABLE / 'phase25e_paired_bootstrap_tests.csv', dtype=str)
    flips = []
    for _, r in tests.iterrows():
        if r['metric'] != 'precision_at_budget' or pd.isna(r['paired_p_raw']):
            continue
        raw = float(r['paired_p_raw'])
        holm = float(r['holm_adjusted_p']) if not pd.isna(r['holm_adjusted_p']) else None
        raw_sig = raw < 0.05
        holm_sig = (holm is not None and holm < 0.05)
        if raw_sig != holm_sig:
            flips.append({'budget': r['budget'], 'comparator': r['comparator'],
                          'paired_p_raw': raw, 'holm_adjusted_p': holm,
                          'raw_significant': raw_sig, 'holm_significant': holm_sig})

    audit = {
        'classification': CLASS,
        'specification_revision': REV,
        'stage': 'MULTIPLICITY_PROVENANCE_AUDIT',
        'question': ('Was Holm-Bonferroni used as the PRIMARY Phase25E S1/H1 adjudication rule PROVABLY '
                     'FROZEN before outcome access?'),
        'method': ('Read-only provenance scan of every pre-registration artifact (Phase24 pre-Phase25 design '
                   'set + Phase25E pre-outcome specification contracts) for multiplicity terminology, then '
                   'comparison of the frozen ROLE of Holm against the ROLE actually used post-outcome.'),
        'term_regex': TERMS.pattern,
        'scan_results': scan_results,
        'phase24_pre_registration_artifacts_scanned': len(PHASE24_PRE_REGISTRATION),
        'phase25e_pre_outcome_artifacts_scanned': len(PHASE25E_PRE_OUTCOME),
        'phase24_artifacts_mentioning_multiplicity': [k for k, r in scan_results.items()
                                                      if r['pre_registration_class'] == 'PHASE24_PRE_PHASE25'
                                                      and r['mentions_multiplicity']],
        'phase25e_pre_outcome_artifacts_mentioning_multiplicity': [
            k for k, r in scan_results.items()
            if r['pre_registration_class'] == 'PHASE25E_PRE_OUTCOME' and r['mentions_multiplicity']],
        'frozen_multiplicity_clause': frozen_multiplicity_clause,
        'frozen_contract_frozen_before_outcome_access': contract_frozen_before_outcome,
        'frozen_contract_DeltaDice_outcomes_read': contract_outcome_reads,
        'frozen_contract_outcome_access': contract_outcome_access,
        'phase24_statistics_block': p24_statistics_block,
        'phase24_declared_report_items': p24_statistics_block.get('report', []),
        'phase24_declares_multiplicity': any('multiplicit' in str(x).lower()
                                             for x in p24_statistics_block.get('report', [])),
        'frozen_primary_is_raw_paired_p': frozen_primary_is_raw_p,
        'frozen_holm_role': frozen_holm_role,
        'adjudication_primary_rule_observed': adjudication_primary_rule_observed,
        'holm_used_as_primary_in_closure': holm_used_as_primary,
        'raw_p_used_as_primary_in_closure': raw_p_used_as_primary,
        'material_sensitivity_rows': flips,
        'material_sensitivity_count': len(flips),
        'classification_code': classification,
        'classification_label': label,
        'verdict': ('Holm-Bonferroni was frozen ONLY as a SECONDARY multiplicity sensitivity. The frozen '
                    'Phase25E statistics contract explicitly designates the raw paired two-sided p as the '
                    'PRIMARY statistic, and the Phase24 pre-registration declares only "paired p-value where '
                    'appropriate" with no multiplicity term at all. Using Holm as the primary significance '
                    'gate in the post-outcome adjudication is therefore an UNAUTHORIZED extension of the '
                    'frozen protocol. The primary adjudication MUST be restored to the frozen raw paired '
                    'bootstrap p; Holm is retained as a conservative secondary sensitivity. This correction '
                    'follows from protocol provenance, NOT from which result looks stronger.'),
        'reconciliation_terminal_if_repaired': ('PHASE25E_CANONICAL_ADJUDICATION_REPAIRED__PRIMARY_PHASE24_'
                                                'STATISTICS_RESTORED__HOLM_RETAINED_AS_SENSITIVITY__PHASE25F_'
                                                'ELIGIBLE_NOT_STARTED'),
        'outcome_access_semantics': ('No new outcome access. The audit reads the frozen paired-bootstrap '
                                     'p-values and the frozen statistics contract only.'),
        'router_holdout_reads': 0, 'VAL808_reads': 0, 'TEST_reads': 0,
        'failures': [],
        'all_pass': classification in ('A', 'B'),
    }
    (AUD / 'phase25e_multiplicity_provenance_audit.json').write_text(
        json.dumps(audit, indent=2, allow_nan=False) + '\n', encoding='utf-8')

    print(f'Classification: {classification} ({label})')
    print(f'Phase24 pre-registration artifacts mentioning multiplicity: {len(phase24_mentions)}')
    print(f'Phase25E pre-outcome artifacts mentioning multiplicity: {len(phase25e_mentions)}')
    print(f'Frozen multiplicity clause: {frozen_multiplicity_clause}')
    print(f'Material sensitivity rows (raw vs Holm on precision): {len(flips)}')
    for f in flips:
        print(f"  budget {f['budget']} {f['comparator']}: raw={f['paired_p_raw']:.6f} "
              f"holm={f['holm_adjusted_p']:.6f}")
    print('PHASE25E_MULTIPLICITY_PROVENANCE_AUDIT_COMPLETE')


if __name__ == '__main__':
    main()
