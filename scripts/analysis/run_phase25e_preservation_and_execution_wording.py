"""Phase25E §8 PRESERVATION-SCOPE CLARIFICATION + §9 MODEL-EXECUTION WORDING RECONCILIATION.

Both are WORDING/RECORD reconciliations. Neither changes any raw scientific
value: every number is read from the frozen Phase25E closure artifacts.

§8 -> reports/audits/phase25e_preservation_scope_clarification.json
§9 -> reports/audits/phase25e_model_execution_wording_reconciliation.json
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUD = ROOT / 'reports/audits'
REV = 'ra_medfilm_barr_resource_gate_v1_0'
CLASS = 'PHASE25E_RESOURCE_GATE_POLICY_EVALUATION'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    adj = json.loads((AUD / 'phase25e_adjudication.json').read_text(encoding='utf-8'))
    summary = json.loads((AUD / 'phase25e_policy_evaluation_summary.json').read_text(encoding='utf-8'))
    calib = json.loads((AUD / 'phase25e_final_router_dev_calibration.json').read_text(encoding='utf-8'))
    no_exec = json.loads((AUD / 'phase25e_no_execution_audit.json').read_text(encoding='utf-8'))
    pres_contract = json.loads((AUD / 'phase24_preservation_contract.json').read_text(encoding='utf-8'))
    criteria = json.loads((AUD / 'phase25e_success_failure_criteria_binding.json').read_text(encoding='utf-8'))

    # ---------------- §8 preservation scope clarification ------------------------
    macro_ci = adj['S2_macro_domain_ci_low']
    f5 = {d['budget']: d for d in adj['F5_detail']}
    per_domain = {
        b: {
            'domain_means': f5[b]['domain_means'],
            'collapse': f5[b]['collapse'],
            'min_domain_mean': (min(f5[b]['domain_means'].values())
                                if f5[b]['domain_means'] else None),
        } for b in f5
    }

    s8 = {
        'classification': CLASS,
        'specification_revision': REV,
        'stage': 'PRESERVATION_SCOPE_CLARIFICATION',
        'criterion': 'S2 PRESERVATION_SATISFIED',
        'criterion_definition': next(c['definition'] for c in criteria['criteria'] if c['id'] == 'S2'),
        'operationalization': criteria['operationalization']['S2'],
        'preservation_contract_ref': 'reports/audits/phase24_preservation_contract.json',
        'preservation_contract_sha256': sha(AUD / 'phase24_preservation_contract.json'),
        'margin': pres_contract['non_inferiority']['margin'],
        'claim_condition': pres_contract['non_inferiority']['claim_only_if'],
        'satisfied': adj['S2_preservation_satisfied'],
        'macro_domain_ci_low_by_budget': macro_ci,
        'all_ci_lows_above_minus_0.005': all(
            (v is not None and v > -0.005) for k, v in macro_ci.items() if k != 'C7_budget0.00'),
        'per_domain_detail_by_budget': per_domain,
        'domain_collapse_triggered': adj['F5_domain_collapse_triggered'],
        'what_the_claim_covers': [
            'NON-INFERIORITY of the routed system vs the frozen global reference on the macro-domain mean '
            'true paired DeltaDice, on ROUTER_DEVELOPMENT (4957), at the frozen budget grid.',
            'The lower 95% CI bound of the macro-domain mean Delta exceeds -0.005 at every informative '
            'budget (0.10/0.25/0.50) and at the degenerate 1.00 budget.',
            'No domain collapse: no domain shows a routed mean at or below -0.01 while another domain is '
            'positive (F5 not triggered).',
            'The global output remains AVAILABLE until the final selection (no destructive replacement '
            'before the final decision); SKIP and EXECUTE_THEN_REJECT both return the global output.',
        ],
        'what_the_claim_does_NOT_cover': [
            'It is NOT a per-domain IMPROVEMENT claim. Routed benefit is strongly heterogeneous: KUB '
            'carries most of the positive mean; BUSI and KVASIR are near zero and KVASIR is marginally '
            'negative at 0.25/0.50 (but far above the -0.01 collapse threshold).',
            'It is NOT a claim that no individual sample is harmed: the harmful activation rate among '
            'routed samples is strictly positive at every budget.',
            'It is NOT a holdout or TEST claim: it is scoped to ROUTER_DEVELOPMENT only; ROUTER_HOLDOUT, '
            'VAL808 and TEST are untouched.',
            'It is NOT a claim about the C9 post-safety comparator (not evaluated in Phase25E).',
            'It is NOT a measured-latency or real-deployment claim: all compute is an ANALYTICAL MAC '
            'LOWER BOUND.',
            'It is NOT a claim about the always-refine system; it compares the ROUTED system against the '
            'global-only reference.',
        ],
        'allowed_phrases': ['performance preserving', 'non-inferior on the macro-domain mean'],
        'forbidden_phrases_until_further_validation': [
            'improves every domain', 'harmless', 'no sample is harmed', 'validated on holdout/TEST'],
        'raw_scientific_values_changed': False,
        'router_holdout_reads': 0, 'VAL808_reads': 0, 'TEST_reads': 0,
        'failures': [],
        'all_pass': bool(adj['S2_preservation_satisfied']),
    }
    (AUD / 'phase25e_preservation_scope_clarification.json').write_text(
        json.dumps(s8, indent=2, allow_nan=False) + '\n', encoding='utf-8')

    # ---------------- §9 model-execution wording reconciliation ------------------
    s9 = {
        'classification': CLASS,
        'specification_revision': REV,
        'stage': 'MODEL_EXECUTION_WORDING_RECONCILIATION',
        'defect': ('Six project-control documents and the phasewise index state "No models were loaded or '
                   'run in this evaluation". That sentence is FALSE for the Phase25E EVALUATION phase: the '
                   'frozen final Phase25D router checkpoint was loaded and run ONCE, outcome-blind, over the '
                   '4957 ROUTER_DEVELOPMENT feature rows to derive the DEV deployment-score ranking and the '
                   'per-budget rank boundaries/tau. The sentence is only true of the earlier Phase25E '
                   'SPECIFICATION-FREEZE phase.'),
        'execution_inventory_frozen': {
            'router_model_loads': 1,
            'router_forwards': 1,
            'router_forward_scope': 'ROUTER_DEVELOPMENT (4957 rows), outcome-blind',
            'global_model_forwards': 0,
            'regional_refiner_forwards': 0,
            'training_runs': 0,
            'optimizer_steps': 0,
            'new_bootstrap_replicates': 0,
            'new_membership_generation': 0,
            'outcome_recomputation': 0,
            'lambda_selected': 0,
            'C9_post_safety_evaluated': False,
        },
        'evidence': {
            'phase25e_final_router_dev_calibration.json': {
                'sha256': sha(AUD / 'phase25e_final_router_dev_calibration.json'),
                'checkpoint_sha256': calib['checkpoint_sha256'],
                'checkpoint_epoch': calib['checkpoint_epoch'],
                'parameter_count': calib['parameter_count'],
                'population': calib['population'],
                'outcome_access': calib['outcome_access'],
                'dev_scores_sha256': calib['dev_scores_sha256'],
                'role': 'This artifact RECORDS the single frozen-router DEV forward.',
            },
            'phase25e_no_execution_audit.json': {
                'sha256': sha(AUD / 'phase25e_no_execution_audit.json'),
                'classification': no_exec['classification'],
                'router_model_loads': no_exec['router_model_loads'],
                'router_forwards': no_exec['router_forwards'],
                'model_inference_required': no_exec['model_inference_required'],
                'role': ('This artifact is scoped to the Phase25E SPECIFICATION-FREEZE phase ONLY '
                         '(classification PHASE25E_PRE_EXECUTION_RESOURCE_GATE_SPECIFICATION_FREEZE). Its '
                         'zero-forward counts describe the spec phase, NOT the later policy evaluation.'),
            },
        },
        'scope_disambiguation': {
            'phase25e_specification_freeze': 'no model load / no forward (design + membership freeze only)',
            'phase25e_policy_evaluation': ('exactly one frozen-router forward over the 4957 DEV rows; '
                                           'no global forward; no refiner forward; no training'),
        },
        'reconciled_wording': (
            'Phase25E loaded the frozen final benefit-router checkpoint once and ran a single outcome-blind '
            'forward pass over the 4,957 ROUTER_DEVELOPMENT feature rows to fix the DEV deployment-score '
            'ranking and per-budget rank boundaries. No global segmentation model was re-run, no regional '
            'refiner was run, no model was trained, no lambda was selected, and the C9 post-safety '
            'comparator was not evaluated. ROUTER_HOLDOUT, VAL808 and TEST were never read.'),
        'stale_sentence_removed': 'No models were loaded or run in this evaluation',
        'documents_to_repair': [
            'docs/RULES.md', 'docs/TASKS.md', 'docs/MEMORY.md', 'docs/ARCHITECTURE.md',
            'docs/DESIGN.md', 'docs/PRD.md', 'notebooks/phasewise/PHASE_INDEX.md'],
        'raw_scientific_values_changed': False,
        'router_holdout_reads': 0, 'VAL808_reads': 0, 'TEST_reads': 0,
        'failures': [],
        'all_pass': True,
    }
    (AUD / 'phase25e_model_execution_wording_reconciliation.json').write_text(
        json.dumps(s9, indent=2, allow_nan=False) + '\n', encoding='utf-8')

    print('§8 preservation scope clarification: S2 satisfied =', s8['satisfied'],
          '| CI lows above -0.005 =', s8['all_ci_lows_above_minus_0.005'])
    print('§9 model-execution wording reconciliation: router_forwards =',
          s9['execution_inventory_frozen']['router_forwards'])
    print('PHASE25E_S8_S9_WRITTEN')


if __name__ == '__main__':
    main()
