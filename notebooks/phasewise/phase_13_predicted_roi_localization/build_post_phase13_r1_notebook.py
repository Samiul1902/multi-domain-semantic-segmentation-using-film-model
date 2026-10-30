"""Build the Post-Phase-13 R1 reviewer notebook (READ-ONLY, no inference)."""
from __future__ import annotations

from pathlib import Path

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

ROOT = Path(r"D:\Softfors\jup")
OUT = (ROOT / "notebooks" / "phasewise" / "phase_13_predicted_roi_localization"
       / "post_phase13_regional_revision_r1_analysis.ipynb")

cells = []
md = lambda t: cells.append(new_markdown_cell(t))       # noqa: E731
code = lambda t: cells.append(new_code_cell(t))         # noqa: E731

md("""# POST-PHASE-13 REGIONAL REVISION R1 — SELECTIVE-ACCEPTANCE POLICY ABLATION (REVIEWER)

**READ-ONLY.** No model inference, no model construction, no CUDA, no proposal regeneration, no oracle
rerun, no TEST access. This notebook only reads the frozen R1 tables and audits.

Run id: `post_phase13_regional_revision_r1_selective_acceptance`

> **Adaptive-development disclosure.** R1 is an **adaptive VAL-development revision** initiated after
> Phase 13 failed the regional-integration gate. The seven-policy family was frozen **before**
> candidate-specific segmentation execution. Candidate **membership is label-blind**. GT is used only for
> **post-freeze evaluation**. R1 findings are **development evidence** and do **not** replace final TEST
> evaluation. TEST remains untouched.""")

code("""import json
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

pd.set_option('display.width', 300)
pd.set_option('display.max_columns', 200)

ROOT = Path(r'D:\\Softfors\\jup')
TABLES = ROOT / 'reports' / 'tables'
AUDITS = ROOT / 'reports' / 'audits'
CONFIGS = ['R1-C0', 'R1-C1', 'R1-C2', 'R1-C3', 'R1-C4', 'R1-C5', 'R1-C6']
MODELS = ['unet', 'attention_unet', 'unetpp', 'deeplabv3plus']


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()


def show(df):
    print(df.to_string(index=False))
    print(f'[rows {len(df)}]')


case = pd.read_csv(TABLES / 'post_phase13_r1_case_model_policy_metrics.csv')
comp = pd.read_csv(TABLES / 'post_phase13_r1_component_model_policy_metrics.csv')
summ = pd.read_csv(TABLES / 'post_phase13_r1_model_policy_summary.csv')
inter = pd.read_csv(TABLES / 'post_phase13_r1_policy_intervention_summary.csv')
cross = pd.read_csv(TABLES / 'post_phase13_r1_cross_architecture_policy_summary.csv')
policy = json.loads((AUDITS / 'post_phase13_regional_revision_r1_policy_frozen.json').read_text('utf-8'))
ctrl = json.loads((AUDITS / 'post_phase13_r1_control_and_duplicate_verification.json').read_text('utf-8'))
ev = json.loads((AUDITS / 'post_phase13_regional_revision_r1_evaluation.json').read_text('utf-8'))
print('loaded frozen R1 artifacts')""")

# 1
md("""## 1. Revision provenance

Phase 13 is **COMPLETE / FROZEN** with regional gate **`REVISE_LOCALIZER`** (regional mechanism **not**
promoted). Revision R0 performed a label-blind failure decomposition and froze a bounded 7-configuration
candidate family. R0-B froze the deterministic execution semantics (acceptance comparator, within-case
order, tie-breaking). R1 is the single authorized bounded policy-ablation round.""")

code("""for k in ('phase13', 'regional_gate', 'revision_r0', 'revision_r1_policy_definition',
          'revision_r1_scientific_execution', 'phase14', 'test'):
    print(f'{k:<38}', policy['continuity'].get(k))
print()
print('R0 failure decomposition :', ev['bindings']['r0_failure_decomposition']['sha'])
print('R1 policy artifact       :', sha256_file(AUDITS / 'post_phase13_regional_revision_r1_policy_frozen.json'))""")

# 2
md("""## 2. R0 hypothesis — `H1_FIRST_SELECTIVE_ACCEPTANCE`

R0 concluded the Phase-13 deployable failure is **dominated by intervention precision / off-target
intervention burden**. The selective-abstention principle was assessed **SUPPORTED** because the frozen
fusion rule already guarantees `PREDICTED == GLOBAL` exactly when nothing is accepted, so maximum proposal
recall is not required.

> **Scope note (additive R0 clarification).** R0's persisted wording was corrected additively: the evidence
> does **not** establish that representation failure is the primary limitation, but it also does **not
> exclude** localizer representation or score calibration as contributors.""")

code("""print('hypothesis                       :', policy['hypothesis'])
print('changed axis                     : proposal acceptance / abstention ONLY')
print('localizer checkpoint             :', policy['frozen_unchanged']['localizer_checkpoint'])
print('proposal geometry                :', policy['frozen_unchanged']['proposal_geometry'])
print('margin / NMS                     :', policy['frozen_unchanged']['margin'], '/', policy['frozen_unchanged']['nms_iou'])
print('fusion                           :', policy['frozen_unchanged']['fusion'])
print('segmentation threshold           :', policy['frozen_unchanged']['segmentation_threshold'])""")

# 3
md("""## 3. Frozen R1 policy family

Seven configurations; **6 distinct memberships** because R1-C1 and R1-C3 coincide (see section 4).""")

code("""print('status:', policy['status'])
print()
show(inter[['config_id', 'accepted_proposals', 'rejected_proposals', 'cases_zero_accepted',
            'mean_accepted_proposals', 'median_accepted_proposals']])
print()
print('acceptance operator :', policy['execution_semantics']['acceptance_operator']['comparator'],
      policy['execution_semantics']['acceptance_operator']['expression'])
print('within-case order   :', policy['execution_semantics']['within_case_order']['sort_key'],
      policy['execution_semantics']['within_case_order']['direction'])
print('tie handling        :', policy['execution_semantics']['tie_handling']['policy'])
print('zero acceptance     :', policy['execution_semantics']['zero_acceptance']['final_prediction'])""")

# 4
md("""## 4. Membership identities and disclosed redundancy

`proposal_rank` is used **only** as the already-frozen deterministic ordering — **not** as confidence
superiority within ties, because 68.2% of proposals are tied at the marginal maximum.""")

code("""for k, v in policy['membership_hashes'].items():
    print(f'{k}  {v}')
print()
d = policy['disclosed_family_redundancy']
print('distinct memberships :', d['distinct_memberships'], 'of', d['configs_in_family'])
print('identical groups     :', d['identical_membership_groups'])
print('family changed       :', d['family_changed'])
print()
print('tie audit:')
for k, v in policy['tie_audit'].items():
    print(f'  {k}: {v}')""")

# 5
md("""## 5. Compute / provenance integrity

Each of the 494 frozen proposals was forwarded **once** per architecture (1976 regional crop evaluations).
All seven policies were assembled from the **same** per-case regional maps. The verified Part-1D-B global
cache was reused, so **no** new global model pass was run.""")

code("""print('regional crop evaluations :', ev['counters']['regional_crop_evaluations'], '(expected 1976)')
print('global model forwards     :', ev['counters']['global_model_forwards'])
print('training / optimizer      :', ev['counters']['training'], '/', ev['counters']['optimizer'])
print('localizer forwards        :', ev['counters']['localizer_forwards'])
print('proposal generation       :', ev['counters']['proposal_generation'])
print('oracle reruns             :', ev['counters']['oracle_reruns'])
print('candidate-family expansion:', ev['counters']['candidate_family_expansion'])
print('TEST reads                :', ev['counters']['test_reads'], '| external:', ev['counters']['external_test_reads'])
print()
print('global cache reused       :', ev['global_cache']['reused'])
print('cache items verified      :', ev['global_cache']['items_verified'])
print('cache manifest sha        :', ev['global_cache']['manifest_sha'])""")

# 6
md("""## 6. Control reproduction — R1-C0 must reproduce frozen Phase-13

R1-C0 is exactly the frozen Phase-13 policy, so it must reproduce `PREDICTED_REGION_FLOAT_GLOBAL_RETAINED`.
Primary integrity criterion: **max abs per-case Dice difference <= 1e-6** for every model.""")

code("""print('C0 reproduction result :', ctrl['control_reproduction']['result'])
print()
for m, v in ctrl['control_reproduction']['per_model'].items():
    print(f'  {m:<16} max abs Dice {v[\"max_abs_dice_diff\"]:.3e}  '
          f'IoU {v[\"max_abs_iou_diff\"]:.3e}  precision {v[\"max_abs_precision_diff\"]:.3e}  '
          f'recall {v[\"max_abs_recall_diff\"]:.3e}')
print()
print('descriptive (no new threshold):', ctrl['control_reproduction']['secondary_note'])""")

# 7
md("""## 7. C1 / C3 duplicate verification

R1-C1 and R1-C3 have identical frozen membership, so their downstream outputs must be identical **by
construction**. They must **not** be treated as independent evidence.""")

code("""d = ctrl['c1_c3_duplicate']
for k, v in d.items():
    print(f'  {k}: {v}')""")

# 8
md("""## 8. Intervention selectivity""")

code("""show(inter[['config_id', 'accepted_proposals', 'cases_zero_accepted',
            'accepted_union_area_mean', 'gt_hit_accepted_proposals', 'gt_miss_accepted_proposals',
            'accepted_gt_miss_fraction', 'gt_hit_retention_relative_to_C0',
            'gt_miss_rejected_fraction_of_all_misses']])
print()
print('GT fields are POST-FREEZE DESCRIPTIVE EVALUATION ONLY. Membership is label-blind.')""")

# 9
md("""## 9. Global preservation""")

code("""show(summ[['config_id', 'model_display', 'policy_macro_precision', 'global_macro_precision',
            'mean_fp_delta_vs_global', 'mean_fn_delta_vs_global', 'cases_improved', 'cases_same',
            'cases_worse']])""")

# 10
md("""## 10. Dice / IoU outcomes""")

code("""show(summ[['config_id', 'model_display', 'global_macro_dice', 'oracle_macro_dice',
            'policy_macro_dice', 'DELTA_POLICY_GLOBAL_DICE', 'RETENTION_DICE', 'ORACLE_GAP_DICE',
            'global_macro_iou', 'policy_macro_iou']])""")

# 11
md("""## 11. Precision / recall / FP / FN outcomes""")

code("""show(summ[['config_id', 'model_display', 'policy_macro_precision', 'policy_macro_recall',
            'mean_global_fp', 'mean_policy_fp', 'mean_global_fn', 'mean_policy_fn']])""")

# 12
md("""## 12. Component recovery / loss

Component definition unchanged: foreground `mask > 0`, 8-connectivity, detected iff >= 1 native predicted
pixel overlaps the component.""")

code("""show(summ[['config_id', 'model_display', 'component_recoveries_vs_global',
            'component_losses_vs_global']])""")

# 13
md("""## 13. Empty recovery / new empties""")

code("""show(summ[['config_id', 'model_display', 'empty_recoveries', 'new_empty_predictions']])""")

# 14
md("""## 14. Oracle-benefit retention

`RETENTION_DICE = (D_policy - D_global) / (D_oracle - D_global)` where the denominator is positive; never
clipped. `N/A` on an invalid denominator — never a fabricated zero.""")

code("""show(summ[['config_id', 'model_display', 'DELTA_POLICY_GLOBAL_DICE', 'RETENTION_DICE', 'ORACLE_GAP_DICE']])
print()
print('N/A count (invalid denominator):', int(summ['RETENTION_DICE'].isna().sum()))""")

# 15
md("""## 15. Size-stratified behaviour

Predeclared strata only: TINY / SMALL / MEDIUM / LARGE.""")

code("""rows = []
for cfg in CONFIGS:
    for st in ('TINY', 'SMALL', 'MEDIUM', 'LARGE'):
        s = comp[(comp.config_id == cfg) & (comp.size_stratum == st) & (comp.model == 'unet')]
        rows.append({'config_id': cfg, 'size_stratum': st, 'n': len(s),
                     'global_detected': int(s['global_detected'].sum()),
                     'policy_detected': int(s['r1_policy_detected'].sum()),
                     'recovered': int(s['GLOBAL_TO_R1_RECOVERY'].sum()),
                     'lost': int(s['GLOBAL_TO_R1_LOSS'].sum())})
show(pd.DataFrame(rows))""")

# 16
md("""## 16. Predeclared difficult cohorts""")

code("""rows = []
for cfg in CONFIGS:
    for name, col in (('hard_tiny', 'hard_tiny'), ('global_empty', 'global_empty_image'),
                      ('multi_component', 'multi_component_image')):
        s = comp[(comp.config_id == cfg) & (comp[col]) & (comp.model == 'unet')]
        rows.append({'config_id': cfg, 'cohort': name, 'n': len(s),
                     'global_detected': int(s['global_detected'].sum()),
                     'policy_detected': int(s['r1_policy_detected'].sum()),
                     'recovered': int(s['GLOBAL_TO_R1_RECOVERY'].sum()),
                     'lost': int(s['GLOBAL_TO_R1_LOSS'].sum())})
show(pd.DataFrame(rows))""")

# 17
md("""## 17. Cross-architecture behaviour

No architecture ranking, no winner.""")

code("""show(cross)""")

# 18
md("""## 18. Trade-off summary (descriptive only)

Reported as descriptive trade-offs. **No best policy, no winner, no optimal threshold** is declared here —
the supervisor adjudicates H1 after reviewing the frozen R1 evidence.""")

code("""show(summ[['config_id', 'model_display', 'mean_accepted_proposals_per_image',
            'mean_fp_delta_vs_global', 'DELTA_POLICY_GLOBAL_DICE',
            'component_recoveries_vs_global', 'component_losses_vs_global']])""")

# 19
md("""## 19. Limitations / adaptive-development disclosure

- **Adaptive VAL-development revision.** R1 was initiated *after* Phase 13 failed the gate. The 7-policy
  family was frozen **before** candidate-specific segmentation execution, and membership is **label-blind**;
  GT is used only for post-freeze evaluation.
- **R1-C1 and R1-C3 are the same policy** and must not be counted as two independent tests.
- The proposal score is **near-degenerate** (68.2% of proposals tied at the maximum), so the acceptance
  floor has limited resolution; `proposal_rank` is a **deterministic order only**, not a confidence ordering.
- Single seed per architecture; no paired significance testing was performed and none is claimed.
- ORACLE values are the **frozen Phase-12 authoritative table** (no oracle rerun).
- HD95 invalid entries are explicitly labelled rather than fabricated.
- **VAL remains development data.** R1 findings do **not** replace final TEST evaluation; TEST is untouched
  until Phase 39. No external-test tuning, no hidden candidate search.
- Component definition, fusion rule, margin, NMS, checkpoints and segmentation threshold were **never**
  changed in R1.""")

# 20
md("""## 20. Explicit stop boundary""")

code("""print('R1 execution        :', ev['final_r1_execution_status'])
print('H1 verdict          :', ev['h1_verdict'])
print('H2                  :', ev['counters'].get('h2_execution', 'NOT_STARTED'))
print('Phase14             :', policy['continuity']['phase14'])
print('TEST                :', policy['continuity']['test'])
print()
print('Not decided here: H1 viable / H1 failed / advance to H2 / promote regional mechanism.')
print('Those are separate supervisor steps.')""")

# 21
md("""## 21. Artifact SHA registry""")

code("""reg = {
    'R0 failure decomposition': AUDITS / 'post_phase13_regional_revision_r0_failure_decomposition.json',
    'R0 protocol frozen': AUDITS / 'post_phase13_regional_revision_r0_protocol_frozen.json',
    'R0 interpretation clarification': AUDITS / 'post_phase13_r0_interpretation_clarification.json',
    'R1 policy frozen': AUDITS / 'post_phase13_regional_revision_r1_policy_frozen.json',
    'R1 control + duplicate verification': AUDITS / 'post_phase13_r1_control_and_duplicate_verification.json',
    'R1 evaluation': AUDITS / 'post_phase13_regional_revision_r1_evaluation.json',
    'candidate family': TABLES / 'post_phase13_regional_revision_r1_candidate_family.csv',
    'frozen membership': TABLES / 'post_phase13_regional_revision_r1_frozen_membership.csv',
    'membership summary': TABLES / 'post_phase13_regional_revision_r1_membership_summary.csv',
    'case-model-policy metrics': TABLES / 'post_phase13_r1_case_model_policy_metrics.csv',
    'component-model-policy metrics': TABLES / 'post_phase13_r1_component_model_policy_metrics.csv',
    'model-policy summary': TABLES / 'post_phase13_r1_model_policy_summary.csv',
    'policy intervention summary': TABLES / 'post_phase13_r1_policy_intervention_summary.csv',
    'cross-architecture summary': TABLES / 'post_phase13_r1_cross_architecture_policy_summary.csv',
}
for k, p in reg.items():
    print(f'{sha256_file(p)}  {k}')""")

# appendix
md("""## Appendix — complete-table validation

The full 2884-row and 4256-row tables are **not** dumped here. They are validated by row count,
uniqueness and SHA, and remain the machine-readable authority.""")

code("""print('case-model-policy rows      :', len(case), '(expected 2884)')
print('unique config/sample/model  :', case[['config_id', 'sample_id', 'model']].drop_duplicates().shape[0])
print('component-model-policy rows :', len(comp), '(expected 4256)')
print('unique config/comp/model    :', comp[['config_id', 'sample_id', 'native_component_id', 'model']].drop_duplicates().shape[0])
print('model-policy summary rows   :', len(summ), '(expected 28)')
print('policy intervention rows    :', len(inter), '(expected 7)')
print('cross-architecture rows     :', len(cross), '(expected 7)')
print()
print('case-model-policy SHA       :', sha256_file(TABLES / 'post_phase13_r1_case_model_policy_metrics.csv'))
print('component-model-policy SHA  :', sha256_file(TABLES / 'post_phase13_r1_component_model_policy_metrics.csv'))
print()
print('READ-ONLY notebook: no inference, no model construction, no CUDA, no TEST access.')""")

nb = new_notebook(cells=cells)
nb.metadata = {"kernelspec": {"display_name": "jup-venv", "language": "python", "name": "jup-venv"},
               "language_info": {"name": "python"}}
OUT.parent.mkdir(parents=True, exist_ok=True)
nbformat.write(nb, str(OUT))
print("wrote", OUT)
print("cells", len(nb.cells), "code", len([c for c in nb.cells if c.cell_type == "code"]))
