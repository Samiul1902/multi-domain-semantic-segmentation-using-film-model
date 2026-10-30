"""Build Phase 13 Part 1A-R2 — checkpoint-selection provenance correction notebook (companion)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(r'D:\Softfors\jup')))
import nbformat as nbf
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell

nb = new_notebook()
nb.metadata['kernelspec'] = {'display_name': 'jup-venv', 'language': 'python', 'name': 'jup-venv'}
nb.metadata['language_info'] = {'name': 'python', 'version': '3.13.12'}


def md(t):
    nb.cells.append(new_markdown_cell(t))


def co(t):
    nb.cells.append(new_code_cell(t))


md("""# Phase 13 Part 1A-R2 — Checkpoint-Selection Provenance Correction

**Model:** Gemini 3.8 Flash Medium · **Date:** 2026-09-21
**Manifest:** `phase4_v3` · **Taxonomy:** `kub_size_clean_v3_v1`
**Part 1A:** COMPLETE · **Part 1A-R1:** EXECUTION PASS · **Part 1A-R2 ONLY is authorized**

---

> **AMENDMENT PHASE ONLY — NO TRAINING / NO INFERENCE.**
>
> **NO TRAINING · NO OPTIMIZER · NO MODEL LOADING · NO FORWARD PASS · NO LOCALIZER
> INFERENCE · NO PROPOSALS · NO PREDICTED-REGION SEGMENTATION · NO 20-CONFIG GRID ·
> NO PART 1B · NO PHASE 14 · NO TEST ACCESS.**

## Why R2 exists

R1 froze an **8-term** checkpoint-selection tuple. Subsequent provenance verification
established that the historical **executing** trainer used a **4-term** tuple
(`scripts/training/train_phase13b_localizer.py` line 164). The clean-v3 primary experiment is
intended to reproduce the executing historical localizer mechanism as closely as scientifically
possible, so **the primary clean-v3 checkpoint-selection tuple is corrected to the executing
historical 4-term tuple**.

R2 supersedes **only** the R1 checkpoint-selection rule. All other R1 decisions remain frozen.

## Companion-notebook rule

Neither of these is modified by this task:

- `phase13_clean_v3_localizer_protocol_freeze.ipynb` — `68f787e1…`
- `phase13_clean_v3_localizer_supervisor_freeze_amendment.ipynb` — `6a08d6bd…`
- `phase13_clean_v3_localizer_protocol_frozen.json` — `999144bb…` (preserved for provenance)
""")

co("""import sys, json
from pathlib import Path
import pandas as pd
pd.set_option('display.max_rows', None); pd.set_option('display.max_columns', None)
pd.set_option('display.width', None); pd.set_option('display.max_colwidth', 100)

PROJECT_ROOT = Path(r'D:\\Softfors\\jup')
CODE_DIR = PROJECT_ROOT / 'notebooks/phasewise/phase_13_predicted_roi_localization/code'
for p in (str(PROJECT_ROOT), str(CODE_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import phase13_localizer_freeze_amendment_r2 as r2mod
TABLES = PROJECT_ROOT / 'reports/tables'
AUDITS = PROJECT_ROOT / 'reports/audits'

# Read-only regeneration. No model is loaded, no forward pass, no optimizer, no inference.
hashes = r2mod.write_all(write_frozen=True)
print(f'wrote {len(hashes)} artifacts')
print('training 0 | optimizer steps 0 | forward passes 0 | localizer inference 0 | '
      'proposals 0 | predicted-region inference 0 | grid search: not run | TEST reads 0')
""")

md("""## 1. Provenance comparison — four competing accounts of the selection rule

The project's source-precedence ladder ranks **executing source (rank 1)** above
**frozen protocol document (rank 2)** above **prose**. Four accounts exist historically.
""")

co("""import importlib
r1mod = importlib.import_module('phase13_localizer_freeze_amendment')

executing = r1mod.HISTORICAL_EXECUTING_SELECTION
protocol_doc = r1mod.HISTORICAL_PROTOCOL_DOC_SELECTION
stage3 = r1mod.HISTORICAL_STAGE3_SELECTION

rows = [
    {'account': 'EXECUTING CODE', 'authority_rank': 1, 'source': executing['source'],
     'line': executing['source_line'], 'length': executing['tuple_length'],
     'tuple': executing['score_tuple'], 'r2_role': 'PRIMARY (adopted)'},
    {'account': 'PHASE13B.md', 'authority_rank': 2, 'source': protocol_doc['source'],
     'line': '-', 'length': protocol_doc['tuple_length'],
     'tuple': protocol_doc['score_tuple'], 'r2_role': 'documentation only'},
    {'account': 'Stage-3 correction', 'authority_rank': 2, 'source': stage3['source'],
     'line': '-', 'length': stage3['tuple_length'],
     'tuple': stage3['score_tuple'], 'r2_role': 'documentation only'},
    {'account': 'R1 supervisor extension', 'authority_rank': 'n/a (supervisor decision)',
     'source': 'phase13_clean_v3_localizer_protocol_frozen.json', 'line': '-',
     'length': 8, 'tuple': '8-term lexicographic extension',
     'r2_role': 'SUPERSEDED_FOR_PRIMARY_CHECKPOINT_SELECTION (preserved as provenance)'},
]
display(pd.DataFrame(rows))
""")

md("""## 2. Executing 4-term source evidence

Read directly from the frozen historical trainer (plain file read — the file is **not**
imported, executed, or modified).
""")

co("""trainer = PROJECT_ROOT / r2mod.EXECUTING_TRAINER
print('file :', trainer.relative_to(PROJECT_ROOT))
print('SHA  :', r2mod.sha256_file(trainer))
print('line :', r2mod.EXECUTING_TRAINER_LINE)
print()
lines = trainer.read_text(encoding='utf-8').splitlines()
lo, hi = r2mod.EXECUTING_TRAINER_LINE - 4, r2mod.EXECUTING_TRAINER_LINE + 6
for i in range(lo, hi + 1):
    marker = '>>' if i == r2mod.EXECUTING_TRAINER_LINE else '  '
    print(f'{marker} {i:4d} | {lines[i-1]}')
""")

co("""print('EXECUTING TUPLE (verbatim from the marked line):')
print('   (tiny_recall90, overall_recall90, -mean_roi_area_fraction, -val_loss)')
print('   length = 4')
print()
print('Same block confirms:')
print('  - improvement rule : score > best_score   (strict lexicographic)')
print('  - ties             : bad epoch')
print('  - patience         : 15')
print('  - best.pt          : saved only on improvement')
print('  - checkpoint key   : best_validation_score')
print('  - manifest recorded: phase4_v2')
print('  - proposal config  : best-of-the-20-config-grid PER EPOCH (the VAL-dependent')
print('                       behaviour that R1 correctly removed)')
""")

md("""## 3. R1 8-term vs R2 4-term

**Only** the checkpoint-selection rule changes. The hard-set / diagnostic fields move from
*selection terms* to *diagnostics* — a direct consequence of that single change.
""")

co("""R1_TUPLE = ['hard_tiny_recovered90', 'global_empty_images_covered90', 'tiny_recall90',
            'overall_recall90', 'multi_component_recall90', '-mean_roi_area_fraction',
            '-mean_proposals_per_image', '-val_loss']
R2_TUPLE = r2mod.PRIMARY_CHECKPOINT_TUPLE

print('R1 (8-term, SUPERSEDED for primary selection):')
for i, t in enumerate(R1_TUPLE, 1):
    tag = '' if t in R2_TUPLE else '   <-- no longer a selection term'
    print(f'  {i}. {t}{tag}')
print()
print('R2 (4-term, PRIMARY — executing historical):')
for i, t in enumerate(R2_TUPLE, 1):
    print(f'  {i}. {t}')
print()
print('label:', r2mod.PRIMARY_CHECKPOINT_TUPLE_LABEL)
print('provenance:', r2mod.PRIMARY_CHECKPOINT_SELECTION['provenance'])
print()
print('Removed from selection, retained as diagnostics:')
for k, v in r2mod.DIAGNOSTIC_METRICS.items():
    print(f'  {k}: {v}')
""")

md("""## 4. Recorded rationale (supervisor §6)
""")

co("""for k, v in r2mod.R2_RATIONALE.items():
    print(f'{k}. {v}')
""")

md("""## 5. R1 → R2 additive diff

A new additive table — history is **not** rewritten. The R1 table
(`phase13_v2_to_clean_v3_localizer_protocol_diff.csv`) is untouched.
""")

co("""diff = pd.read_csv(r2mod.R2_DIFF)
counts = r2mod.diff_counts(diff)
display(diff[['field', 'change', 'scientifically_material', 'authorized',
              'material_change_group']])
print('counts:', counts)
assert counts['unauthorized_material_differences'] == 0
assert counts['r1_to_r2_material_differences'] == 1
assert counts['authorized_material_differences'] == 1
print()
print('Exactly ONE material difference (checkpoint_selection_tuple), authorized, 0 unauthorized.')
""")

co("""changed = diff[diff['change'] == 'CHANGED']
display(changed[['field', 'r1_value', 'r2_value', 'reason']])
""")

md("""## 6. Confirmation that all other protocol fields are unchanged

Programmatic key-level comparison of the R1 frozen JSON against the regenerated R2 protocol:
only an explicitly allow-listed set of keys may differ. Any other drift raises.
""")

co("""r2 = r2mod.build_r2_protocol()
unexpected = r2mod.verify_only_expected_keys_changed(r2)
print('unexpected protocol drift:', unexpected or 'NONE')
assert not unexpected, unexpected
print()
r1_frozen = json.loads(r2mod.R1_FROZEN_JSON.read_text(encoding='utf-8'))
same_keys = sorted(k for k in r1_frozen if r1_frozen.get(k) == r2.get(k))
print(f'identical top-level keys: {len(same_keys)}')
print('  ', ', '.join(same_keys))
print()
print('intentionally changed keys:')
print('  ', ', '.join(sorted(r2mod.EXPECTED_CHANGED_KEYS)))
""")

co("""print('UNCHANGED scientific core (spot check against R1):')
for key in ['population', 'heatmap_contract', 'proposal_configuration', 'coverage_contract',
            'downstream_composition', 'downstream_geometry', 'downstream_model_scope',
            'downstream_reference_model', 'retention_contract', 'gate_governance',
            'phase14_distribution_requirement', 'label_defects', 'epoch_provenance']:
    same = r1_frozen.get(key) == r2.get(key)
    print(f'  {key:38s} identical={same}')
    assert same, key
print()
print('ALL LISTED CORE FIELDS IDENTICAL TO R1')
""")

md("""## 7. Final R2 protocol display
""")

co("""cs = r2['checkpoint_selection']
print('STATUS:', r2['status'])
print('PART  :', r2['part'], '| DOC:', r2['document_type'])
print()
print('PRIMARY CHECKPOINT SELECTION:')
print('  label      :', cs['label'])
print('  provenance :', cs['provenance'], f"({cs['provenance_source']}:{cs['provenance_line']})")
print('  tuple      :', tuple(cs['tuple']))
print('  length     :', cs['tuple_length'])
print('  comparison :', cs['comparison'])
print('  ties       :', cs['ties'], '| patience:', cs['patience'])
print('  evaluated at:', cs['evaluated_at'])
print()
print('FIXED PROPOSAL CONFIG:', r2['proposal_configuration']['threshold'],
      r2['proposal_configuration']['margin'], r2['proposal_configuration']['top_k'],
      r2['proposal_configuration']['nms_iou'])
print('PRIMARY GRID SEARCH :', r2['proposal_configuration']['clean_v3_primary_grid_search'])
print('HISTORICAL 20-GRID  :', r2['proposal_configuration']['historical_20_grid'])
print()
print('HARD SETS: hard_tiny', r2['hard_sets']['hard_tiny']['count'],
      '| global_empty', r2['hard_sets']['global_empty']['count'],
      '| role', r2['hard_sets']['role'])
print('HEATMAP   :', r2['heatmap_contract']['input'], '->', r2['heatmap_contract']['output_heatmap'])
print('DOWNSTREAM:', r2['downstream_composition']['primary_name'],
      '| margin', r2['downstream_geometry']['config']['margin'])
print('RETENTION :', r2['downstream_geometry']['label'])
print('GATE      :', r2['gate_governance']['final_regional_gate'])
""")

co("""print('R1 SUPERSESSION:')
for k, v in r2['r1_supersession'].items():
    print(f'  {k}: {v}')
""")

md("""## 8. Immutability verification (§17)
""")

co("""checks = [
    ('Part-1A notebook', r2mod.PART1A_NOTEBOOK, r2mod.PART1A_NOTEBOOK_SHA),
    ('R1 amendment notebook', r2mod.R1_NOTEBOOK, r2mod.R1_NOTEBOOK_SHA),
    ('R1 frozen JSON', r2mod.R1_FROZEN_JSON, r2mod.R1_FROZEN_JSON_SHA),
    ('hard-Tiny table', r2mod.TABLES / 'phase13_clean_v3_hard_tiny_replication_set.csv',
     '2f9828d77c008e7c90cd69e82d0af3568902ca9d508fdfcb9d8ccf8abd569538'),
    ('global-empty table', r2mod.TABLES / 'phase13_clean_v3_global_empty_replication_set.csv',
     'a0b332cad6bca4466ccc528cbe18cc527ef6503603ab69c55b9d699d7979f0ea'),
    ('historical history.csv', PROJECT_ROOT / 'experiments/phase13b_kub_localizer_r512_h128_'
     'sigmaeq075_centernetfocal_seed42_v1/history.csv',
     'dcdb4369d0c3a087fd0bd2611db0aac3ff0afd48db8c1f9a9bb5e79b834fdb76'),
    ('historical best.pt', PROJECT_ROOT / 'checkpoints/phase13b_kub_localizer_r512_h128_'
     'sigmaeq075_centernetfocal_seed42_v1/best.pt',
     'ece906df6c73f2e93c3f873661490bf3cb1a6b82be2d2d93b58c25bc967cbace'),
    ('historical latest.pt', PROJECT_ROOT / 'checkpoints/phase13b_kub_localizer_r512_h128_'
     'sigmaeq075_centernetfocal_seed42_v1/latest.pt',
     'a1461df2e8d6784984337c79b87c65833c39fed16382579088d97d7c60ba78f4'),
    ('historical Stage-4D notebook', PROJECT_ROOT / 'notebooks/phasewise/'
     'phase_13_predicted_roi_localization/phase13_stage4d_localizer_final_visual_analysis.ipynb',
     '561fd5d63d7fa0ea7de9155b055ce08035928d065054bb94b8a707ce83b969d0'),
]
rows = []
for name, path, expected in checks:
    actual = r2mod.sha256_file(path)
    rows.append({'artifact': name, 'expected': expected[:16] + '...',
                 'actual': actual[:16] + '...', 'unchanged': actual == expected})
    assert actual == expected, name
display(pd.DataFrame(rows))
print('ALL IMMUTABILITY CHECKS PASS')
""")

md("""## 9. Zero-training / zero-inference boundary
""")

co("""for k, v in r2['governance'].items():
    print(f'  {k}: {v}')
g = r2['governance']
assert g['training'] == 0 and g['optimizer_steps'] == 0 and g['model_forward_passes'] == 0
assert g['localizer_inference'] == 0 and g['predicted_region_inference'] == 0
assert g['proposals_generated'] == 0 and g['test_content_reads'] == 0
assert not g['phase14_started'] and not g['historical_artifacts_modified']
assert not g['r1_artifacts_modified'] and not g['clean_v3_grid_search_run']
print()
print('BOUNDARY VERIFIED: no model was loaded, no forward pass, no optimizer,')
print('no inference, no proposals, no grid search, 0 TEST reads, 0 historical/R1 edits.')
""")

md("""## 10. Pass gate and artifact registry
""")

co("""pg = r2['pass_gate']
for k, v in pg.items():
    print(f'  {k}: {v}')
assert pg['unauthorized_material_differences'] == 0
assert all(v for k, v in pg.items() if k != 'unauthorized_material_differences')
print()
print('ALL PASS-GATE ITEMS TRUE (unauthorized material differences == 0)')
""")

co("""reg = pd.DataFrame([{'artifact': k, 'sha256': v} for k, v in sorted(hashes.items())])
display(reg)
print()
print('FUTURE PART 1B MUST USE:', r2['r1_supersession']['future_part1b_must_use'])
print('NEXT ACTION:', r2['next_action'])
""")

md("""## 11. STOP

- Part 1A / 1A-R1 / 1A-R2: **COMPLETE**. Current executable protocol:
  **`SUPERVISOR_FROZEN_R2_READY_FOR_PART1B_TRAINING`**.
- Primary checkpoint selection: **4-term executing historical tuple** at the fixed proposal
  configuration. R1 8-term tuple: **SUPERSEDED_FOR_PRIMARY_CHECKPOINT_SELECTION** (provenance
  preserved).
- Hard-set / global-empty metrics: **`SECONDARY_DIAGNOSTIC_NOT_SELECTION_TERM`**.
- Part 1B: **ELIGIBLE / NOT AUTHORIZED**.
- `REGIONAL_INTEGRATION_GATE_AFTER_PHASE13`: **NOT_DECIDED** (no GO / REVISE_LOCALIZER / NO_GO).
- Phase 14: **not started**. `RA-MedFiLM-Seg++`: **not implemented**. TEST: **untouched**.

**STOP — WAIT_FOR_SUPERVISOR_PHASE13_PART1B_TRAINING_AUTHORIZATION.**
""")

co("""print('PHASE 13 PART 1A-R2 — COMPLETE (checkpoint-selection provenance correction)')
print('protocol status: SUPERVISOR_FROZEN_R2_READY_FOR_PART1B_TRAINING')
print('primary tuple: 4-term executing historical, at fixed config 0.10/0.20/5/0.30')
print('part1b: ELIGIBLE / NOT AUTHORIZED | gate: NOT_DECIDED | phase14: not started')
print('training 0 | inference 0 | proposals 0 | TEST reads 0')
""")

out = Path(r'D:\Softfors\jup\notebooks\phasewise\phase_13_predicted_roi_localization'
           r'\phase13_clean_v3_localizer_checkpoint_selection_r2.ipynb')
for i, cell in enumerate(nb.cells):
    cell['id'] = f'p13r2{i:03d}'
nbf.write(nb, str(out))
print('wrote', out, '| cells:', len(nb.cells))
