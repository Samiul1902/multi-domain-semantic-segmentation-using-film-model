"""Build the Phase-13 Part-1E-B gate-adjudication review notebook (READ-ONLY, no inference)."""
from __future__ import annotations

from pathlib import Path

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

ROOT = Path(r"D:\Softfors\jup")
OUT = (ROOT / "notebooks" / "phasewise" / "phase_13_predicted_roi_localization"
       / "phase13_regional_integration_gate_review.ipynb")

cells = []
md = lambda t: cells.append(new_markdown_cell(t))          # noqa: E731
code = lambda t: cells.append(new_code_cell(t))            # noqa: E731

# 1
md("""# PHASE-13 — REGIONAL INTEGRATION GATE REVIEW (PART 1E-B)

**READ-ONLY.** No inference, no model construction, no CUDA, no proposal generation, no oracle rerun,
no TEST access. This notebook only reads the frozen gate artifact and its bound evidence.

**Gate id:** `REGIONAL_INTEGRATION_GATE_AFTER_PHASE13`
**Adjudication mode:** `QUALITATIVE_PROSPECTIVE_EVIDENCE_ADJUDICATION`
**Evidence scope:** prospectively frozen evidence only (criteria frozen in Part 1E-A **before** any
Part-1D-B result existed).

> This notebook does not duplicate the hundreds of rows already visible in the Part-1D-B reviewer
> notebook. It presents the *adjudication record*.""")

code("""import json
import hashlib
from pathlib import Path

import pandas as pd

ROOT = Path(r'D:\\Softfors\\jup')
AUDITS = ROOT / 'reports' / 'audits'
TABLES = ROOT / 'reports' / 'tables'


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()


gate = json.loads((AUDITS / 'phase13_regional_integration_gate_after_phase13.json').read_text('utf-8'))
crit = json.loads((AUDITS / 'phase13_regional_integration_gate_criteria_frozen.json').read_text('utf-8'))
ev = json.loads((AUDITS / 'phase13_part1d_b_predicted_region_evaluation.json').read_text('utf-8'))
dim = pd.read_csv(TABLES / 'phase13_regional_integration_gate_after_phase13.csv')
print('loaded frozen gate artifact + bound evidence')""")

# 2
md("""## 1. Prospective criteria identity

The criteria were frozen in Part 1E-A before any Part-1D-B result existed, and were **not edited or
reinterpreted** during adjudication.""")

code("""print('status                          :', crit['status'])
print('part1d_b_results_inspected      :', crit['part1d_b_results_inspected'])
print('numerical_thresholds_introduced :', crit['numerical_thresholds_introduced'])
print('gate mode                       :', crit['gate_mode'])
print('dimensions                      :', list(crit['dimensions']))
print('outcomes                        :', list(crit['outcomes']))
print('criteria SHA-256                :', sha256_file(AUDITS / 'phase13_regional_integration_gate_criteria_frozen.json'))
print('recorded in gate artifact       :', gate['bindings']['prospective_criteria']['sha'])
print('criteria edited by Part 1E-B    :', gate['bindings']['prospective_criteria']['edited'])""")

# 3
md("""## 2. Integrity precondition

A material integrity failure would have forced `CHECK_REQUIRED` with **no** verdict issued.""")

code("""pre = gate['integrity_precondition']
print('integrity precondition result :', pre['result'])
print()
for k, v in pre['checks'].items():
    print(f'  {\"PASS\" if v else \"FAIL\"}  {k}')""")

# 4
md("""## 3. Dimension A — `ORACLE_MECHANISM_VALUE`

Part-1D-B may change A **only** if it reveals a material integrity / reproduction defect in Phase-12.
Poor predicted-localizer performance must **not** be used to invalidate A.""")

code("""A = gate['dimensions']['A']
print('pre-state    :', A['pre_state'])
print('state        :', A['state'])
print('changed      :', 'NO')
print()
print('frozen Phase-12 oracle Dice gains (re-confirmed):')
for k, v in A['oracle_gains'].items():
    if k in ('unet', 'attention_unet', 'unetpp', 'deeplabv3plus'):
        print(f'  {k:<16} {v:+.6f}')
print()
print(A['evidence'])""")

# 5
md("""## 4. Dimension B — `PRACTICAL_LOCALIZATION_RETENTION`

Adjudicated from multiple frozen fields; **no single field alone decides** and **no retention cutoff
was introduced**. Negative retention values are preserved unclipped.""")

code("""B = gate['dimensions']['B']
print('pre-state :', B['pre_state'])
print('state     :', B['state'])
print()
rows = []
for m, b in B['per_model'].items():
    rows.append({'model': m, 'GLOBAL': b['global_dice'], 'ORACLE': b['oracle_dice'],
                 'PREDICTED': b['predicted_dice'], 'DELTA_ORACLE': b['DELTA_ORACLE_DICE'],
                 'DELTA_PRED': b['DELTA_PRED_DICE'], 'RETENTION_DICE': b['RETENTION_DICE'],
                 'ORACLE_GAP': b['ORACLE_GAP_DICE'], 'IoU_ret': b['iou_gain_retention'],
                 'ObjRecall_ret': b['object_recall_gain_retention'],
                 'FNred_ret': b['fn_reduction_retention'],
                 'recovered': b['component_recoveries'], 'lost': b['component_losses'],
                 'empty_rec': b['empty_recoveries'], 'new_empty': b['new_empty_predictions']})
print(pd.DataFrame(rows).to_string(index=False))
print()
print(B['evidence'])""")

# 6
md("""## 5. Dimension C — `GLOBAL_PRESERVATION_FP_COST`

Target recovery is always interpreted **together with** the FP / precision cost. Neither component
recovery nor the FP burden is hidden.""")

code("""C = gate['dimensions']['C']
print('pre-state :', C['pre_state'])
print('state     :', C['state'])
print()
rows = []
for m, c in C['per_model'].items():
    rows.append({'model': m, 'dDice': c['mean_dice_delta'], 'dIoU': c['mean_iou_delta'],
                 'dPrecision': c['mean_precision_delta'], 'dRecall': c['mean_recall_delta'],
                 'meanFPdelta': c['mean_fp_delta'], 'meanFNdelta': c['mean_fn_delta'],
                 'improved': c['cases_improved'], 'unchanged': c['cases_unchanged'],
                 'worsened': c['cases_worsened'], 'maxImp': c['max_case_improvement'],
                 'maxWor': c['max_case_worsening'], 'recovered': c['component_recoveries'],
                 'lost': c['component_losses'], 'empty_rec': c['empty_recoveries']})
print(pd.DataFrame(rows).to_string(index=False))
print()
print(C['evidence'])""")

# 7
md("""## 6. Dimension D — `GENERALITY`

Four frozen architectures; reference model **NONE**; **no winner**; **no ranking**; heterogeneity
reported rather than averaged away.""")

code("""D = gate['dimensions']['D']
print('pre-state :', D['pre_state'])
print('state     :', D['state'])
print()
for k, v in D['cross_architecture'].items():
    print(f'  {k:<45} {v}')
print()
print(D['evidence'])""")

# 8
md("""## 7. Prospective logic applied

The frozen outcome rules, applied mechanically. `GO` requires **A and B and C and D**.
`REVISE_LOCALIZER` requires **A supported AND at least one of** (B weak, C materially problematic,
D too architecture-specific). `NO_GO` requires **A no longer scientifically supportable** — and the
frozen invariant forbids `NO_GO` from a poor GT-free localizer result alone while A remains supported.""")

code("""lg = gate['prospective_logic_applied']
print('GO                 satisfied :', lg['GO']['satisfied'])
print('   blocked by                 :', '; '.join(lg['GO']['blocking']))
print('REVISE_LOCALIZER   satisfied :', lg['REVISE_LOCALIZER']['satisfied'])
print('   triggered by               :', '; '.join(lg['REVISE_LOCALIZER']['triggered_by']))
print('NO_GO              satisfied :', lg['NO_GO']['satisfied'])
print('   blocked by                 :', lg['NO_GO']['blocked_by'])
print()
print('SELECTED VERDICT   :', lg['selected'])""")

# 9
md("""## 8. Final verdict""")

code("""print('FINAL GATE VERDICT :', gate['final_gate_verdict'])
print()
print('Dimension table (one row per frozen dimension):')
print(dim[['dimension_id', 'dimension_name', 'adjudicated_state',
           'supports_go', 'supports_revise', 'supports_no_go', 'integrity_issue']].to_string(index=False))
print()
print('Reasoning:')
print(gate['verdict_reasoning'])
print()
print('Verdict discipline:')
for k, v in gate['verdict_discipline'].items():
    print(f'  {k} : {v}')""")

# 10
md("""## 9. Localization / FP context and claim limitations

The frozen Part-1C proposal context and the Part-1D-B gallery fusion verification are **descriptive
context only**. The gate decision does not require a sole-cause diagnosis.""")

code("""ctx = gate['localization_fp_context']
print('proposals total                :', ctx['frozen_proposals_total'])
print('overlap >=1 GT pixel           :', ctx['proposals_overlapping_at_least_one_gt_pixel'])
print('overlap no GT pixel            :', ctx['proposals_overlapping_no_gt_pixel'])
print('off-target fraction            :', ctx['off_target_fraction'])
print('gallery pairs checked          :', ctx['gallery_fusion_verification']['case_model_pairs_checked'])
print('outside support P == G exactly :', ctx['gallery_fusion_verification']['outside_support_P_equals_G_exactly'])
print()
print('allowed  :', ctx['allowed_interpretation'])
print('FORBIDDEN:', ctx['forbidden_interpretation'])
print('sole-cause diagnosis required for the gate :', ctx['sole_cause_diagnosis_required_for_gate'])
print()
print('Claim limits:')
for k, v in gate['claim_limits'].items():
    print(f'  {k} : {v}')
print()
print('Phase-13 closure:')
for k, v in gate['phase13_closure'].items():
    print(f'  {k} : {v}')""")

# 11
md("""## 10. Artifact SHA registry""")

code("""reg = {
    'gate artifact': AUDITS / 'phase13_regional_integration_gate_after_phase13.json',
    'gate markdown': AUDITS / 'phase13_regional_integration_gate_after_phase13.md',
    'dimension table': TABLES / 'phase13_regional_integration_gate_after_phase13.csv',
    'prospective criteria': AUDITS / 'phase13_regional_integration_gate_criteria_frozen.json',
    'Part-1D R1 protocol': AUDITS / 'phase13_part1d_predicted_region_protocol_frozen_r1.json',
    'Part-1D-B evaluation': AUDITS / 'phase13_part1d_b_predicted_region_evaluation.json',
    'Part-1D-B reproduction': AUDITS / 'phase13_part1d_b_global_reproduction.json',
    'Phase-12 oracle case metrics': TABLES / 'phase12_clean_v3_oracle_case_metrics.csv',
    'Phase-12 oracle component metrics': TABLES / 'phase12_clean_v3_oracle_component_metrics.csv',
    'Phase-12 oracle geometry': TABLES / 'phase12_clean_v3_oracle_geometry.csv',
    'Part-1C proposals': TABLES / 'phase13_part1c_best_checkpoint_proposals.csv',
    'Part-1C case proposals': TABLES / 'phase13_part1c_best_checkpoint_case_proposals.csv',
    'Part-1D-B model summary': TABLES / 'phase13_part1d_predicted_region_model_summary.csv',
    'Part-1D-B case-model': TABLES / 'phase13_part1d_predicted_region_case_model_metrics.csv',
    'Part-1D-B component-model': TABLES / 'phase13_part1d_predicted_region_component_model_metrics.csv',
}
for k, p in reg.items():
    print(f'{sha256_file(p)}  {k}')
print()
print('READ-ONLY: no inference, no model construction, no CUDA, no oracle rerun, no TEST access.')
print('counters:', gate['counters'])""")

nb = new_notebook(cells=cells)
nb.metadata = {"kernelspec": {"display_name": "jup-venv", "language": "python", "name": "jup-venv"},
               "language_info": {"name": "python"}}
OUT.parent.mkdir(parents=True, exist_ok=True)
nbformat.write(nb, str(OUT))
print("wrote", OUT)
print("cells", len(nb.cells), "code", len([c for c in nb.cells if c.cell_type == "code"]))
