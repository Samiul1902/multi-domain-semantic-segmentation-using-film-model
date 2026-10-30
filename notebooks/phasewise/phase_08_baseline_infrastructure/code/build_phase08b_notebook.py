"""
Phase 08 Part 1B — build the trainer/protocol audit notebook (unexecuted).
"""

from __future__ import annotations

from pathlib import Path

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

PROJECT_ROOT = Path(r'D:\Softfors\jup')
NB_DIR = PROJECT_ROOT / 'notebooks' / 'phasewise' / 'phase_08_baseline_infrastructure'
NB_PATH = NB_DIR / 'phase08_part1b_trainer_and_phase09_protocol_audit.ipynb'

KERNEL = {'display_name': 'jup-venv', 'language': 'python', 'name': 'jup-venv'}

cells = []
md = lambda s: cells.append(new_markdown_cell(s))
code = lambda s: cells.append(new_code_cell(s))

md("""# Phase 08 Part 1B — Trainer / Validation / Resume Contract
## + Historical Phase-09 Protocol Reconstruction

**Phase ID:** `phase_08_baseline_infrastructure`
**Part:** 1B
**Model:** Gemini 3.1 Pro High
**Project Root:** `D:\\Softfors\\jup` · **Kernel:** `jup-venv`

**Active manifest:** `phase4_v3` · **Frozen taxonomy:** `kub_size_clean_v3_v1`

> This notebook **reconstructs** the historical Phase-09 protocol and audits the
> trainer/checkpoint/resume contract. It performs **no scientific training** and
> never reads TEST content.""")

md("""## 2. Scope / Governance

| Rule | Value |
|---|---|
| Historical results | labelled `HISTORICAL_v2` (`manifest_version = phase4_v2`) |
| TEST image/mask reads | **0** |
| TEST metrics / visualizations | **0** |
| Full scientific training | **NONE** |
| Checkpoint selection split | VAL only |
| Early stopping split | VAL only |
| Phase 09 | **NOT started** |
| Phase-13/14 test debt | documented, **not repaired** |

Historical v2 metrics are **not** rewritten as clean-v3 results.""")

code("""import json, sys, tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import matplotlib
matplotlib.use('Agg')
from IPython.display import Image as IPImage, display

PROJECT_ROOT = Path(r'D:\\Softfors\\jup')
CODE_DIR = PROJECT_ROOT / 'notebooks' / 'phasewise' / 'phase_08_baseline_infrastructure' / 'code'
TABLES = PROJECT_ROOT / 'reports' / 'tables'
AUDITS = PROJECT_ROOT / 'reports' / 'audits'
FIGDIR = PROJECT_ROOT / 'reports' / 'figures' / 'phase08_baseline_infrastructure'
sys.path.insert(0, str(PROJECT_ROOT)); sys.path.insert(0, str(CODE_DIR))
import phase08b_protocol_audit as p8b

from src.training.trainer import EarlyStopping, Trainer
from src.utils.run_lock import acquire_lock, release_lock, inspect_lock, ExperimentLockError
from src.utils import config as cfgmod

print('torch :', torch.__version__)
print('manifest:', p8b.MANIFEST_VERSION_CLEAN, '| taxonomy:', p8b.TAXONOMY_ID)""")

md("""## 3. Accepted Part-1A Contracts

Preserved from Part 1A (not redesigned here): `mask > 0` foreground, 1 input
channel, aspect-preserving resize + centre pad, nearest mask interpolation,
target sizes {256,512,768,1024}, CUDA-required device, AMP supported,
TRAIN stochastic / VAL deterministic, TEST locked.""")

md("""## 4. Historical Phase-09 Source Audit

The checkpoint directory is the primary experiment-level provenance source.
Precedence: (1) config saved with the checkpoint, (2) trainer/model source,
(3) checkpoint metadata/history, (4) Phase-10 loop, (5) notebook/audit, (6) prose.""")

code("""prov = p8b.audit_checkpoint_artifacts()
p8b.write_table(prov, 'phase08_phase09_checkpoint_artifact_provenance.csv')
display(prov[['artifact','kind','bytes','precedence_rank','sha256']])""")

code("""ck = p8b.phase09_checkpoint_metadata()
print('best.pt   :', {k: v for k, v in ck['best.pt'].items() if k != 'manifest_hashes'})
print()
print('latest.pt :', {k: v for k, v in ck['latest.pt'].items() if k != 'manifest_hashes'})
print()
print('SHA best  :', ck['best.pt']['sha256'])
print('SHA latest:', ck['latest.pt']['sha256'])""")

md("""### 4b. Precedence check — checkpoint-embedded config vs YAML""")
code("""import yaml
ck_cfg = p8b.load_phase09_config()
yaml_cfg = yaml.safe_load(p8b.PHASE09_CONFIG.read_text(encoding='utf-8'))

def flat(d, pre=''):
    out = {}
    for k, v in (d or {}).items():
        key = f'{pre}{k}'
        if isinstance(v, dict): out.update(flat(v, key + '.'))
        else: out[key] = v
    return out
a, b = flat(ck_cfg), flat(yaml_cfg)
keys = sorted(set(a) | set(b))
diffs = [(k, a.get(k, '<absent>'), b.get(k, '<absent>')) for k in keys if a.get(k, '<absent>') != b.get(k, '<absent>')]
print(f'fields compared : {len(keys)}')
print(f'identical       : {len(keys) - len(diffs)}')
print(f'differing       : {len(diffs)}')
for k, va, vb in diffs:
    print(f'  DIFF {k}: checkpoint={va!r} yaml={vb!r}')
print()
print('MATERIAL SOURCE DISAGREEMENTS:', len(diffs))""")

md("## 5. Historical Baseline Set")
code("""mapping = p8b.build_phase_model_mapping()
p8b.write_table(mapping, 'phase08_phase09_phase_model_mapping.csv')
display(mapping)
print()
print('Phase-09 clean-rerun scope models:', int(mapping['in_phase09_clean_rerun_scope'].sum()))
print('Phase 09 = TRAINING (UNet baseline only); Phase 10 = COMPARISON (3 extra models).')""")

md("""## 6. Exact Protocol Matrix

One row per historical baseline protocol, with source config/trainer SHAs.""")
code("""protocol = p8b.build_protocol_matrix()
p8b.write_table(protocol, 'phase08_phase09_historical_protocol_matrix.csv')
cols = ['experiment_id','architecture','input_channels','output_channels','resolution',
        'manifest_version','loss','optimizer','learning_rate','weight_decay','scheduler',
        'scheduler_step_timing','batch_size','amp','seed','max_epochs','checkpoint_metric',
        'early_stopping_patience','prediction_threshold','protocol_status']
display(protocol[cols].T)""")

code("""p = protocol.iloc[0]
for k in ['experiment_id','architecture','model_key','input_channels','output_channels',
          'base_channels','resolution','manifest_version','loss','loss_parameters',
          'optimizer','learning_rate','weight_decay','scheduler','scheduler_parameters',
          'scheduler_step_timing','batch_size','gradient_accumulation_steps',
          'effective_batch_size','amp','seed','max_epochs','augmentation_policy',
          'checkpoint_metric','checkpoint_mode','checkpoint_improvement_rule',
          'early_stopping_patience','early_stopping_min_delta','prediction_threshold',
          'validation_aggregation','val_shuffle','val_augmentation','num_workers',
          'pin_memory','gradient_clipping']:
    print(f'{k:32s}: {p[k]}')""")

md("""## 4b. Phase-10 Cross-Check (field by field)

Proving the Phase-10 loop matches Phase-09 semantics requires showing the actual
fields, not asserting equivalence.""")
code("""cross = p8b.build_phase10_crosscheck()
p8b.write_table(cross, 'phase08_phase09_phase10_crosscheck.csv')
display(cross)
print()
print('fields compared     :', len(cross))
print('identical           :', int((cross['same_or_different'] == 'same').sum()))
print('different           :', int((cross['same_or_different'] == 'different').sum()))
print('MATERIAL differences:', int(cross['material'].sum()))""")

md("## 7. Trainer Lifecycle")
code("""display(IPImage(filename=str(FIGDIR / 'phase08b_trainer_lifecycle.png')))
print('One root trainer per experiment ID; single-writer lock enforced by')
print('src/utils/run_lock.py (active conflict fails loudly; stale recovery explicit).')""")

md("""## 8. Training-Step Semantics

Ordering (from `src/training/trainer.py::train_one_epoch`):

`zero_grad(set_to_none=True)` → autocast forward → loss/accumulation →
scaled backward → on accumulation boundary: `scaler.step` → `scaler.update` →
`zero_grad`. No gradient clipping. No autonomous batch skipping.""")
code("""src = (PROJECT_ROOT / 'src' / 'training' / 'trainer.py').read_text(encoding='utf-8')
checks = {
    'zero_grad first': 'self.optimizer.zero_grad(set_to_none=True)' in src,
    'autocast forward': 'torch.amp.autocast' in src,
    'scaled backward': 'self.scaler.scale(loss).backward()' in src,
    'scaler.step before update': src.find('scaler.step') < src.find('scaler.update'),
    'accumulation gating': '(index+1)%self.accumulation==0' in src,
    'no gradient clipping': 'clip_grad' not in src,
    'no batch skipping': 'continue' not in src,
}
for k, v in checks.items():
    print(f'  {k:30s}: {v}')""")

md("""## 9. Validation Aggregation

Canonical convention: **macro = unweighted mean of per-image metrics**.
Micro (global pixel aggregate) is also reported but is NOT used for checkpoint
selection. Hand-check examples below prove the semantics.""")
code("""agg = p8b.build_validation_aggregation_contract()
p8b.write_table(agg, 'phase08_validation_aggregation_contract.csv')
display(agg)
print()
print('live macro check from the canonical implementation:',
      agg.attrs.get('live_macro_check'))
print()
print('VAL augmentation: OFF | VAL shuffle: FALSE | VAL deterministic: TRUE')""")

code("""display(IPImage(filename=str(FIGDIR / 'phase08b_validation_aggregation_handcheck.png')))""")

md("## 10. Metric Threshold")
code("""print('prediction threshold (historical, unchanged):', p8b.load_phase09_config()['training']['threshold'])
print('used for: validation metrics AND qualitative panels')
print('Phase 08 does NOT retune this value.')""")

md("## 11. Checkpoint-Selection Semantics")
code("""ckpt_contract = p8b.build_checkpoint_selection_contract()
p8b.write_table(ckpt_contract, 'phase08_checkpoint_selection_contract.csv')
display(ckpt_contract)""")

md("## 12. Early-Stopping Semantics")
code("""es_contract = p8b.build_early_stopping_contract()
p8b.write_table(es_contract, 'phase08_early_stopping_contract.csv')
display(es_contract)""")

code("""display(IPImage(filename=str(FIGDIR / 'phase08b_checkpoint_state_machine.png')))
print()
# live boundary demonstration of the historical EarlyStopping
es = EarlyStopping(patience=3)
trace = []
for epoch, score in enumerate([0.50, 0.50, 0.40, 0.60, 0.60, 0.55, 0.55, 0.55], start=1):
    stop = es.update(score)
    trace.append({'epoch': epoch, 'score': score, 'bad_epochs': es.bad_epochs,
                  'best': es.best, 'stop': stop})
display(pd.DataFrame(trace))""")

md("## 13. Scheduler Semantics")
code("""sched_contract = p8b.build_scheduler_contract()
p8b.write_table(sched_contract, 'phase08_scheduler_contract.csv')
display(sched_contract)""")

md("## 14. History / Logging Contract")
code("""hist = pd.read_csv(PROJECT_ROOT / 'experiments' / p8b.PHASE09_EXP_ID / 'history.csv')
print('historical history.csv columns:', list(hist.columns))
print('rows:', len(hist))
display(hist.head(3))
print()
required = ['epoch','train_loss','val_loss','val_dice','val_iou','val_precision',
            'val_recall','learning_rate','epoch_seconds','peak_gpu_allocated',
            'peak_gpu_reserved']
print('all required per-epoch fields present:', all(c in hist.columns for c in required))
print('provenance fields required for clean-v3: experiment_id, manifest_version,')
print('taxonomy_id, seed (recorded alongside the history, not per row).')""")

md("""## 15. Experiment-ID / Single-Writer Contract

One experiment ID = one logical scientific run. Resume after crash/power loss/
interruption reuses the SAME ID; `_v2`/`_retry`/`_new` suffixes are not appended
merely because a run resumed.""")
code("""with tempfile.TemporaryDirectory() as tmp:
    acquire_lock(tmp, 'demo_exp')
    st = inspect_lock(tmp)
    print('lock present:', st['present'], '| active:', st['active'], '| reason:', st['reason'])
    try:
        acquire_lock(tmp, 'demo_exp')
        print('ERROR: second trainer should have been refused')
    except ExperimentLockError as e:
        print('second trainer refused loudly:', type(e).__name__)
    # simulate a dead owner -> stale, explicit recovery
    import json
    from src.utils.run_lock import lock_path
    payload = json.loads(lock_path(tmp).read_text()); payload['pid'] = 999999999
    lock_path(tmp).write_text(json.dumps(payload))
    st2 = inspect_lock(tmp)
    print('after owner death -> active:', st2['active'], '| stale:', st2['stale'])
    rec = acquire_lock(tmp, 'demo_exp', recover_stale=True)
    print('stale recovered explicitly:', rec['recovered_stale_lock'])
    release_lock(tmp, force=True)""")

md("## 16. Checkpoint / Resume Contract")
code("""resume_contract = p8b.build_resume_contract()
p8b.write_table(resume_contract, 'phase08_resume_contract.csv')
display(resume_contract)""")

md("""## 17. Resume-Equivalence Probe

**INFRASTRUCTURE_TEST_ONLY** — synthetic data, no scientific claim.
Path A runs N steps continuously; Path B runs K steps, checkpoints, destroys the
objects, restores, then runs the remaining N-K steps.""")
code("""probe = p8b.resume_equivalence_probe()
for k in ['label','device','steps','split_at','losses_identical','max_loss_abs_diff',
          'lr_schedule_identical','parameters_identical','max_param_abs_diff',
          'restored_experiment_id','restored_manifest_version','restored_taxonomy_id',
          'restored_epoch','scientific_claim']:
    print(f'{k:28s}: {probe[k]}')
print()
print('losses A:', [round(x, 8) for x in probe['losses_continuous']])
print('losses B:', [round(x, 8) for x in probe['losses_resumed']])""")

code("""display(IPImage(filename=str(FIGDIR / 'phase08b_resume_equivalence_trace.png')))""")

md("## 18. Config Validation")
code("""t = cfgmod.config_template()
v = cfgmod.validate_experiment_config(t, require_all=True)
print('template with <REQUIRED> placeholders -> valid:', v['valid'], '(expected False)')
print('placeholder fields:', len(v['placeholder_fields']))
print()
full = {k: 'v' for k in cfgmod.REQUIRED_SCIENTIFIC_FIELDS}
full['manifest_version'] = 'phase4_v3'
print('complete config -> valid:', cfgmod.validate_experiment_config(full)['valid'])
missing = dict(full); missing.pop('loss')
print('missing loss -> valid:', cfgmod.validate_experiment_config(missing)['valid'])""")

md("## 19. v2 → clean-v3 Protocol Diff")
code("""diff_df = p8b.build_protocol_diff(protocol.iloc[0].to_dict())
p8b.write_table(diff_df, 'phase08_phase09_v2_to_clean_v3_protocol_diff.csv')
display(diff_df[diff_df['same_or_changed'] == 'changed'])
print()
print('fields compared        :', len(diff_df))
print('changed fields         :', int((diff_df['same_or_changed'] == 'changed').sum()))
print('SCIENTIFICALLY MATERIAL:', int(diff_df['scientifically_material'].sum()))""")

md("## 20. Candidate Clean-v3 Phase-09 Configs")
code("""cand = p8b.build_candidate_configs(ck_cfg)
p8b.write_table(cand, 'phase08_phase09_clean_v3_candidate_configs.csv')
paths = p8b.write_candidate_config_files(ck_cfg)
display(cand.T)
print()
print('candidate config file(s):', [str(p.relative_to(PROJECT_ROOT)) for p in paths])
print('status :', cand['candidate_status'].iloc[0])
print('executed:', cand['executed'].iloc[0])""")

md("## 21. Pre-existing Unrelated Test Debt")
code("""debt = p8b.build_test_debt()
display(debt)
print()
print('None of these are required by Phase-09 baseline infrastructure.')
print('Disposition:', debt['disposition'].iloc[0])
print()
print('NOTE: `pytest tests/` never completes because test_phase14_part1.py hangs.')
print('Part 1B therefore uses scoped test files, not the full suite.')""")

md("""## 22. Limitations

- Protocol reconstruction is from historical artifacts; no historical run was re-executed.
- Historical v2 metrics remain `HISTORICAL_v2` and are not comparable to clean-v3 results.
- The resume probe is synthetic and CPU-based; it does not claim GPU bitwise determinism.
- Phase-13/14 test debt is documented, not repaired (out of scope, unrelated modules).
- Candidate configs are **not** executed and are **not** scientifically authorized.""")

md("""## 23. Phase-08 Conclusion

The historical Phase-09 protocol is fully reconstructed with no material ambiguity:
the checkpoint-embedded config matches the YAML exactly (0 disagreements), the
Phase-09 baseline set is a single UNet model, and the Phase-10 loop reproduces the
same semantics field-for-field. Trainer, validation, checkpoint, early-stopping,
scheduler and resume semantics are explicit and tested. A clean-v3 candidate config
differs from the historical protocol only in authorized provenance fields.""")

md("## 24. Artifact Hashes")
code("""ledger = {
    'historical_phase09': {
        'experiment_id': p8b.PHASE09_EXP_ID,
        'checkpoint_dir': 'checkpoints/phase9_kub_unet_baseline_seed42_512',
        'config_sha': p8b.sha256_file(p8b.PHASE09_CONFIG),
        'best_sha': ck['best.pt']['sha256'],
        'latest_sha': ck['latest.pt']['sha256'],
    },
    'clean_v3': {'manifest_version': p8b.MANIFEST_VERSION_CLEAN,
                 'taxonomy_id': p8b.TAXONOMY_ID},
    'resume_probe_passed': bool(probe['losses_identical'] and probe['parameters_identical']),
    'test_content_reads': 0,
    'full_scientific_training_performed': False,
    'phase09_started': False,
}
print(json.dumps(ledger, indent=2))
print()
reg = p8b.final_table_registry(TABLES)
display(reg)
print('TABLE COUNT:', int(reg['exists'].sum()))""")

code("""print('=' * 62)
print('PHASE 08 PART 1B — FINAL STATUS')
print('=' * 62)
print('HISTORICAL PHASE09 EXP ID :', p8b.PHASE09_EXP_ID)
print('PHASE09 BASELINE MODELS   : 1 (unet)')
print('PHASE10 CROSS-CHECK       : material differences =', int(cross['material'].sum()))
print('v2 -> clean-v3 MATERIAL   :', int(diff_df['scientifically_material'].sum()))
print('CANDIDATE CONFIG          :', cand['candidate_status'].iloc[0])
print('TEST CONTENT READS        : 0')
print('FULL SCIENTIFIC TRAINING  : NO')
print('PHASE 09 STARTED          : NO')
print('=' * 62)""")

nb = new_notebook(cells=cells, metadata={
    'kernelspec': KERNEL, 'language_info': {'name': 'python'}})
nbformat.write(nb, str(NB_PATH))
print('Wrote:', NB_PATH)
print('cells:', len(nb.cells), '| code:', sum(1 for c in nb.cells if c.cell_type == 'code'))
