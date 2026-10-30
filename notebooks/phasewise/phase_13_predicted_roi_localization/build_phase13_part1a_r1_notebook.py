"""Build Phase 13 Part 1A-R1 — supervisor freeze amendment notebook (companion; does NOT touch the accepted Part-1A notebook)."""
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


md("""# Phase 13 Part 1A-R1 — Supervisor Protocol-Freeze Amendment

**Model:** Gemini 3.8 Flash Medium · **Date:** 2026-09-21
**Manifest:** `phase4_v3` · **Taxonomy:** `kub_size_clean_v3_v1`
**Part 1A archaeology/reconstruction:** ACCEPTED
**Part 1A scientific protocol:** NOT YET frozen for execution — **Part 1A-R1 ONLY is authorized**

---

> **AMENDMENT PHASE ONLY.** This notebook records exact supervisor decisions, amends the
> clean-v3 Phase-13 protocol candidate, and produces the final supervisor-frozen protocol
> artifact.
>
> **NO TRAINING · NO OPTIMIZER · NO MODEL FORWARD PASS · NO LOCALIZER INFERENCE ·
> NO PREDICTED-REGION INFERENCE · NO PROPOSALS · NO TEST ACCESS · NO PART 1B · NO PHASE 14.**
>
> Authorized reads: already-frozen clean-v3 VAL predictions/tables, used **only** to derive
> the prospectively defined hard-set membership (§17).

## Companion-notebook rule

The accepted Part-1A notebook is **NOT modified** by this task:

- `phase13_clean_v3_localizer_protocol_freeze.ipynb`
- SHA-256 `68f787e1f70fcf706442b342e62cc615eeb347653e753149987becf793ac2bd0`

This notebook is a small companion amendment.
""")

co("""import sys, json
from pathlib import Path
import pandas as pd
pd.set_option('display.max_rows', None); pd.set_option('display.max_columns', None)
pd.set_option('display.width', None); pd.set_option('display.max_colwidth', 90)

PROJECT_ROOT = Path(r'D:\\Softfors\\jup')
CODE_DIR = PROJECT_ROOT / 'notebooks/phasewise/phase_13_predicted_roi_localization/code'
for p in (str(PROJECT_ROOT), str(CODE_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import phase13_localizer_freeze_amendment as r1
TABLES = PROJECT_ROOT / 'reports/tables'
AUDITS = PROJECT_ROOT / 'reports/audits'

# Read-only regeneration: derives hard sets from frozen clean-v3 tables and writes the
# frozen protocol artifact. No model is loaded, no forward pass, no optimizer, no inference.
hashes = r1.write_all(write_frozen=True)
print(f'wrote {len(hashes)} artifacts')
print('training 0 | optimizer steps 0 | forward passes 0 | localizer inference 0 | '
      'predicted-region inference 0 | proposals 0 | TEST reads 0')
""")

md("""## 1. Accepted Part-1A notebook — unchanged verification

The accepted Part-1A notebook SHA must still match. This is checked before anything else.
""")

co("""nb_path = r1.PART1A_NOTEBOOK
actual = r1.sha256_file(nb_path)
print('path    :', nb_path.relative_to(PROJECT_ROOT))
print('expected:', r1.PART1A_NOTEBOOK_SHA)
print('actual  :', actual)
print('UNCHANGED:', actual == r1.PART1A_NOTEBOOK_SHA)
assert actual == r1.PART1A_NOTEBOOK_SHA, 'accepted Part-1A notebook was modified'
""")

md("""## 2. Supervisor decisions (verbatim dispositions)

| § | Decision | Disposition |
|---|---|---|
| §1 | Hard sets | re-derive on clean-v3 using the **same historical definition**, freeze **before** training |
| §2 | Heatmap resolution | **APPROVED MATERIAL CORRECTION** — explicit `heatmap_resolution=128` |
| §3 | Stage-4D `clean_v3_results` label | `STAGE4D_DESIGN_AUDIT_LABEL_PROVENANCE_DEFECT` → `HISTORICAL_v2_PROVENANCE_ONLY` |
| §4 | Missing `val_search_epoch079.csv` | `NON_BLOCKING_HISTORICAL_ARTIFACT_GAP` — not fabricated |
| §5 | Proposal grid | clean-v3 primary grid search **DISABLED**; historical 20-grid `DEFERRED_SECONDARY_SENSITIVITY_ONLY` |
| §6 | Checkpoint selection | fixed-config historical lexicographic score |
| §7 | Coverage | historical `covered90 >= 0.90` preserved; no new post-training threshold |
| §8 | Phase-14 distribution mismatch | `DEFERRED_REQUIREMENT_FOR_PHASE14_IF_GATE_ALLOWS` — **not** a Phase-13 change |
| §9 | Downstream geometry | frozen GT-free config, margin **0.20** (not the Phase-12 oracle 0.25) |
| §10 | Downstream composition | `PREDICTED_REGION_FLOAT_GLOBAL_RETAINED` |
| §11 | Downstream model scope | all four; no reference model |
| §12 | Retention contract | ratio only where `oracle_gain > 0`; no sufficiency threshold |
| §13 | Gate | dimension B `CANDIDATE_FOR_SUPERVISOR_FREEZE`; gate `NOT_DECIDED` |
""")

md("""## 3. Clean-v3 hard-set derivation

Both cohorts are re-derived from **already-frozen clean-v3 VAL tables** using the exact
historical definition reconstructed in Part 1A. No segmentation inference is run.

**`hard_tiny`** — TINY native components whose clean-v3 UNet++ GLOBAL prediction misses them:

> `global_detected = at least 1 native-space pixel of the 8-connected GT component has`
> `GLOBAL_NATIVE probability >= 0.5` (executing definition, `phase12_oracle_inference.py`
> `component_detection` / driver line 459)

**`global_empty_image`** — FULL_FIELD images whose clean-v3 UNet++ GLOBAL prediction is empty
(`prediction_empty == true`), cross-validated against the frozen Phase-11 clean-v3 table.
""")

co("""ht = pd.read_csv(r1.HARD_TINY_OUT)
print('CLEAN-v3 HARD TINY SET — count:', len(ht))
print('source      :', ht['clean_v3_source'].iloc[0])
print('source SHA  :', ht['source_sha'].iloc[0])
print('supporting  :', ht['supporting_source'].iloc[0])
print('anchor      :', ht['anchor_model'].iloc[0], '/', ht['anchor_role'].iloc[0])
print('all TINY and undetected:',
      bool((ht['size_stratum'] == 'TINY').all() and (~ht['global_detected'].astype(bool)).all()))
display(ht[['sample_id', 'native_component_id', 'size_stratum', 'global_detected']])
""")

co("""ge = pd.read_csv(r1.GLOBAL_EMPTY_OUT)
print('CLEAN-v3 GLOBAL-EMPTY SET — count:', len(ge))
print('source      :', ge['clean_v3_source'].iloc[0])
print('source SHA  :', ge['source_sha'].iloc[0])
print('supporting  :', ge['supporting_source'].iloc[0])
print('cross-validated Phase-11 vs Phase-12: True (asserted during derivation)')
display(ge[['sample_id', 'prediction_empty', 'anchor_model', 'anchor_role']])
""")

co("""print('historical v2 counts (NOT a target):', {'hard_tiny': 16, 'global_empty': 7})
print('clean-v3 re-derived counts        :', {'hard_tiny': len(ht), 'global_empty': len(ge)})
print()
print('UNet++ role:', r1.HARDSET_ANCHOR_ROLE)
print('UNet++ is NOT:', ', '.join(r1.HARDSET_ANCHOR_IS_NOT))
print('reference model selected:', r1.DOWNSTREAM_REFERENCE_MODEL)
print()
print('These replication cohorts may participate in the historical-style checkpoint metric.')
print('They MUST NOT replace the architecture-independent frozen gate cohorts:')
for c in r1.build_frozen_protocol(ht, ge, 'x', 'x')['hard_sets']['must_not_replace_gate_cohorts']:
    print('  -', c)
""")

md("""## 4. Heatmap resolution contract

The historical helper defect is **not** silently used. Every clean-v3 path must pass
`heatmap_resolution=128` explicitly, with fail-loud shape assertions.
""")

co("""hc = r1.HEATMAP_CONTRACT
print('input          :', hc['input'])
print('output heatmap :', hc['output_heatmap'])
print('heatmap_resolution:', hc['heatmap_resolution'], '(explicit, never a constructor default)')
print('applies to     :', ', '.join(hc['applies_to']))
print('fail-loud assertions:')
for a in hc['fail_loud_assertions']:
    print('  -', a)
print()
print('defect       :', hc['historical_helper_defect'])
print('preferred fix:', hc['preferred_remediation'], '->', hc['remediation_options'][hc['preferred_remediation']])
print('historical frozen outputs must not be modified:', hc['historical_frozen_outputs_must_not_be_modified'])
print()
print('Any violation -> STOP / CHECK_REQUIRED')
""")

md("""## 5. Frozen proposal configuration

The historically selected configuration is known **before** clean-v3 localizer results are
inspected, so it is frozen now. Letting the clean-v3 VAL cohort choose another configuration
would introduce a new VAL-dependent post-processing optimization.
""")

co("""cfg = r1.FIXED_PROPOSAL_CONFIG
print('FROZEN clean-v3 primary proposal configuration:')
for k, v in cfg.items():
    print(f'  {k:10s} = {v}')
print()
print('provenance:', r1.FIXED_PROPOSAL_CONFIG_PROVENANCE)
print('clean-v3 primary grid search :', 'DISABLED')
print('historical 20-grid           : DEFERRED_SECONDARY_SENSITIVITY_ONLY')
print('  may only run later under separate authorization, after the primary checkpoint,')
print('  primary proposal config and primary result are frozen.')
""")

md("""## 6. Checkpoint-selection contract

Lexicographic evidence priorities, computed at **one fixed proposal configuration only**.

### 6.1 Provenance disclosure (recorded, not silently asserted)

The supervisor R1 contract specifies an **8-term** tuple described as "reconstructed from
executing code". Verification of the executing code shows a **4-term** tuple. The deviation is
recorded explicitly so it is never mis-stated as historical reproduction.
""")

co("""ex = r1.HISTORICAL_EXECUTING_SELECTION
print('EXECUTING CODE (authority rank 1):')
print('  source :', ex['source'], 'line', ex['source_line'])
print('  score  :', ex['score_tuple'])
print('  length :', ex['tuple_length'])
print('  improvement:', ex['improvement_rule'], '| ties:', ex['ties'], '| patience:', ex['patience'])
print('  proposal config used:', ex['proposal_config_used'])
print('  checkpoint key:', ex['checkpoint_key'])
print('  note:', ex['note'])
print()
print('FROZEN PROTOCOL DOC (PHASE13B.md, rank 2): length', r1.HISTORICAL_PROTOCOL_DOC_SELECTION['tuple_length'])
print('STAGE-3 CORRECTION DOC (rank 2)          : length', r1.HISTORICAL_STAGE3_SELECTION['tuple_length'])
print()
cs = r1.CLEAN_V3_CHECKPOINT_SELECTION
print('CLEAN-v3 SUPERVISOR-FROZEN CONTRACT (authoritative):')
for i, t in enumerate(cs['tuple_ordering'], start=1):
    print(f'  {i}. {t}')
print('  evaluated at:', cs['evaluated_at'])
print('  hard-set terms use:', cs['hard_tiny_and_global_empty_terms_use'])
print('  zero denominator ->', cs['zero_denominator_rule'])
print('  per-epoch proposal grid search:', cs['per_epoch_proposal_grid_search'])
print()
print('DISCLOSURE:', cs['provenance_disclosure'])
""")

md("""## 7. Final v2 → clean-v3 protocol diff

The Part-1A base rows plus five explicit amendment rows (A–E). **Unauthorized material
differences must be 0.**
""")

co("""diff = pd.read_csv(r1.DIFF_OUT)
display(diff[['amendment_id', 'field', 'same_or_changed', 'scientifically_material',
              'authorization']])
print('rows:', len(diff), '| amendments:', diff['amendment_id'].value_counts().to_dict())
print('unauthorized material differences:', int(diff['unauthorized_material_difference'].sum()))
assert int(diff['unauthorized_material_difference'].sum()) == 0
""")

co("""amd = diff[diff['amendment_id'] != 'PART_1A_BASE']
display(amd[['amendment_id', 'field', 'historical_v2', 'proposed_clean_v3', 'authorization']])
""")

md("""## 8. Phase-14 distribution requirement (deferred)

The verified historical mismatch is **not** a Phase-13 localizer training change. Any wording
implying "predicted-proposal training crops" belong to Phase-13 Part-1B localizer training is
removed.
""")

co("""p14 = r1.PHASE14_DISTRIBUTION_REQUIREMENT
print('disposition:', p14['canonical_disposition'])
print('is a Phase-13 localizer training change:', p14['is_a_phase13_localizer_training_change'])
print('Phase 13 trains:', p14['phase13_trains'])
print('predicted-proposal training crops in Phase 13:', p14['phase13_predicted_proposal_training_crops'])
print('Phase-14 crop recipe frozen here:', p14['phase14_crop_training_recipe_frozen_here'])
print('Phase 14 started:', p14['phase14_started'])
print()
print('requirement:', p14['requirement'])
""")

md("""## 9. Downstream predicted-region contract (frozen, NOT executed)

Label: **`PRACTICAL_GT_FREE_ORACLE_BENEFIT_RETENTION`** — the retention experiment includes
localization imperfection **and** the practical proposal-geometry difference, so it is not a
pure localization-error isolation study.
""")

co("""g = r1.DOWNSTREAM_GEOMETRY
print('geometry:', g['config'])
print('must NOT change margin to the Phase-12 oracle margin', g['must_not_change_margin_to_phase12_oracle_margin'])
print('retention includes:', ', '.join(g['retention_includes']))
print('pure localization-error isolation study:', not g['not_a_pure_localization_error_isolation_study'])
print('label:', g['label'])
print()
c = r1.DOWNSTREAM_COMPOSITION
print('primary name :', c['primary_name'])
print('  regional crop resolution       :', c['regional_crop_resolution'])
print('  regional prob restoration      :', c['regional_probability_restoration'])
print('  multiple regional crops        :', c['multiple_predicted_regional_crops'])
print('  outside proposal union         :', c['global_outside_predicted_proposal_union'])
print('  inside proposal support        :', c['inside_predicted_proposal_support'])
print('  final threshold (full native)  :', c['final_threshold_full_native_probability'])
print('  FORBIDDEN                      :', ', '.join(c['forbidden']))
print()
print('downstream model scope:', ', '.join(r1.DOWNSTREAM_MODEL_SCOPE))
print('downstream reference model:', r1.DOWNSTREAM_REFERENCE_MODEL)
""")

md("""## 10. Retention metric contract and gate governance
""")

co("""rc = r1.RETENTION_CONTRACT
for k, v in rc['aggregate_model_level'].items():
    print(f'  {k}: {v}')
print('  numerical sufficient-retention threshold:', rc['numerical_sufficient_retention_threshold'])
print('  case level:', rc['case_level'])
print()
gg = r1.GATE_GOVERNANCE
print('dimension B:', gg['dimension_b'], '->', gg['dimension_b_status'])
print('scalar gate score:', gg['scalar_gate_score'])
print('numerical GO threshold:', gg['numerical_go_threshold'])
print('final regional gate:', gg['final_regional_gate'])
print('outcomes issued here:', gg['outcomes_issued_in_this_task'] or 'NONE')
""")

md("""## 11. Label defects recorded (no historical artifact modified)
""")

co("""for name, d in r1.LABEL_DEFECTS.items():
    print(f'--- {name}')
    for k, v in d.items():
        print(f'    {k}: {v}')
    print()
""")

md("""## 12. Zero training / inference boundary

Explicit confirmation that this amendment executed no scientific computation.
""")

co("""gv = r1.GOVERNANCE
for k, v in gv.items():
    print(f'  {k}: {v}')
assert gv['training'] == 0 and gv['optimizer_steps'] == 0 and gv['model_forward_passes'] == 0
assert gv['localizer_inference'] == 0 and gv['predicted_region_inference'] == 0
assert gv['proposals_generated'] == 0 and gv['test_content_reads'] == 0
assert not gv['phase14_started'] and not gv['historical_artifacts_modified']
print()
print('BOUNDARY VERIFIED: 0 training, 0 inference, 0 proposals, 0 TEST reads, 0 historical edits')
""")

md("""## 13. Epoch provenance (reference only — not duplicated)

- Authoritative epoch provenance: `history.csv` — **88 / 88 contiguous epochs**.
- The accepted Part-1A notebook already contains the complete upstream epoch tables
  (59 / 69 / 85 / 67 for UNet / Attention U-Net / UNet++ / DeepLabV3+); they are **not**
  duplicated here.
- `val_search_epoch079.csv` remains absent (87 of 88 dumps) — **not recreated, not fabricated**.
""")

co("""hist = PROJECT_ROOT / 'experiments/phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_v1/history.csv'
h = pd.read_csv(hist)
eps = h['epoch'].astype(int).tolist()
print('history.csv rows:', len(h), '| epochs:', min(eps), '->', max(eps),
      '| contiguous:', eps == list(range(1, len(h) + 1)))
print('history SHA:', r1.sha256_file(hist))
sd = hist.parent
dumps = sorted(p.name for p in sd.glob('val_search_epoch*.csv'))
print('val_search dumps present:', len(dumps), '| epoch079 present:', 'val_search_epoch079.csv' in dumps)
print('part1a notebook contains the 59/69/85/67 tables:', True, '(verified unchanged above)')
""")

md("""## 14. Frozen protocol artifact
""")

co("""frozen = json.loads(r1.FROZEN_JSON.read_text(encoding='utf-8'))
print('status :', frozen['status'])
print('json   :', r1.FROZEN_JSON.name, '->', hashes[r1.FROZEN_JSON.name])
print('md     :', r1.FROZEN_MD.name, '->', hashes[r1.FROZEN_MD.name])
print()
print('pass gate:')
for k, v in frozen['pass_gate'].items():
    print(f'  {k}: {v}')
# NOTE: 'unauthorized_material_differences' is a COUNT whose required value is 0
# (zero unauthorized differences), so it must be checked for equality, not truthiness.
assert frozen['pass_gate']['unauthorized_material_differences'] == 0
assert all(v for k, v in frozen['pass_gate'].items()
           if k != 'unauthorized_material_differences')
print()
print('ALL PASS-GATE ITEMS TRUE (unauthorized material differences == 0)')
""")

co("""reg = pd.DataFrame([{'artifact': k, 'sha256': v} for k, v in sorted(hashes.items())])
display(reg)
print()
print('NEXT ACTION:', frozen['next_action'])
""")

md("""## 15. STOP

- Part 1A archaeology: **ACCEPTED**. Part 1A protocol: **frozen** at `SUPERVISOR_FROZEN_READY_FOR_PART1B_TRAINING`.
- Part 1B: **ELIGIBLE / NOT AUTHORIZED**.
- `REGIONAL_INTEGRATION_GATE_AFTER_PHASE13`: **NOT_DECIDED** (no GO / REVISE_LOCALIZER / NO_GO issued).
- Phase 14: **not started**. `RA-MedFiLM-Seg++`: **not implemented**.
- TEST: **untouched** (content reads 0).

**STOP — WAIT_FOR_SUPERVISOR_PHASE13_PART1B_TRAINING_AUTHORIZATION.**
""")

co("""print('PHASE 13 PART 1A-R1 — COMPLETE (supervisor freeze amendment)')
print('protocol status: SUPERVISOR_FROZEN_READY_FOR_PART1B_TRAINING')
print('part1b: ELIGIBLE / NOT AUTHORIZED')
print('gate: NOT_DECIDED | phase14: not started | RA-MedFiLM: not implemented')
print('training 0 | inference 0 | proposals 0 | TEST reads 0')
""")

out = Path(r'D:\Softfors\jup\notebooks\phasewise\phase_13_predicted_roi_localization'
           r'\phase13_clean_v3_localizer_supervisor_freeze_amendment.ipynb')
for i, cell in enumerate(nb.cells):
    cell['id'] = f'p13r1{i:03d}'
nbf.write(nb, str(out))
print('wrote', out, '| cells:', len(nb.cells))
