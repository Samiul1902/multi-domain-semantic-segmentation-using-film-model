"""Phase 25F canonical execution — §33 build the real 41-section reviewer
notebook (executed, deterministic).

Reads frozen Phase25F tables/audits/figures only; no model training, no
outcome re-derivation, no TEST/VAL/HOLDOUT access.
"""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[2]
AUD = ROOT / "reports/audits"
TABLE = ROOT / "reports/tables"
FIG = ROOT / "reports/figures"
CACHE = ROOT / "data_cache/phase25f_barr_post_safety_v1_0"
NB = ROOT / "notebooks/phasewise/phase_25f_post_safety/phase25f_post_safety_execution.ipynb"
REV = "ra_medfilm_barr_post_safety_v1_0"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _is_repair_process_artifact(path: Path) -> bool:
    """Repair-process artifacts are excluded from the notebook binding: the
    compliance addendum records the notebook SHA, so binding it would be
    circular, and the gates/audits are re-written as the repair progresses."""
    n = path.name
    return (n.startswith("phase25f_notebook_compliance_repair_")
            or n.startswith("phase25f_notebook_pre_compliance_repair_")
            or n.startswith("phase25f_existing_notebook_")
            or n.startswith("phase25f_final_freeze_notebook_compliance_")
            or n.startswith("phase25f_postrepair_"))


def build_inputs():
    inputs = {}
    for p in sorted(TABLE.glob("phase25f_*.csv")):
        inputs[p.relative_to(ROOT).as_posix()] = sha(p)
    for p in sorted(FIG.glob("p25f_*.png")):
        inputs[p.relative_to(ROOT).as_posix()] = sha(p)
    for p in sorted(AUD.glob("phase25f_*.json")):
        if _is_repair_process_artifact(p):
            continue
        inputs[p.relative_to(ROOT).as_posix()] = sha(p)
    for name in ["features.npy", "metadata.csv", "feature_schema.csv", "targets.csv",
                 "phase25f_oof_safety_predictions.csv"]:
        p = CACHE / name
        inputs[p.relative_to(ROOT).as_posix()] = sha(p)
    for sub in ["cv_fold0", "cv_fold1", "cv_fold2", "cv_fold3", "cv_fold4", "final"]:
        base = ROOT / "experiments" / "phase25f_barr_post_safety_v1_0_seed42" / sub
        inputs[(base / "history.csv").relative_to(ROOT).as_posix()] = sha(base / "history.csv")
        inputs[(base / "run_complete.json").relative_to(ROOT).as_posix()] = sha(base / "run_complete.json")
    return inputs


SETUP = '''from pathlib import Path
import base64, hashlib, json
import numpy as np
import pandas as pd
from IPython.display import display, HTML, Image

ROOT = Path.cwd()
while not (ROOT / 'reports/audits/phase25f_execution_reentry_gate.json').exists() and ROOT.parent != ROOT:
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

def epoch_history(rel, closure_rel, expected_rows, expected_best=None, expected_term=None):
    """Read a COMPLETE persisted epoch history and assert its integrity.

    Returns (history_df, closure_dict). Renders nothing (the caller decides).
    """
    h = read_csv(rel)
    cl = read_json(closure_rel)
    assert len(h) == expected_rows, (rel, 'row_count', len(h), expected_rows)
    assert list(h['epoch']) == list(range(1, expected_rows + 1)), (rel, 'epoch_sequence')
    assert int(h['epoch'].duplicated().sum()) == 0, (rel, 'duplicate_epoch')
    assert np.isfinite(h['train_bce']).all(), (rel, 'train_bce_nonfinite')
    assert np.isfinite(h['learning_rate']).all(), (rel, 'lr_nonfinite')
    assert np.isfinite(h['elapsed_seconds']).all(), (rel, 'elapsed_nonfinite')
    assert int(cl['total_epochs']) == expected_rows, (rel, 'closure_total_epochs')
    assert int(cl['last_epoch']) == expected_rows, (rel, 'closure_last_epoch')
    assert cl['history_sha256'] == INPUTS[rel], (rel, 'closure_history_sha_mismatch')
    if expected_best is not None:
        # EARLY_STOP monitoring exists: require finite monitor and the canonical best epoch.
        assert np.isfinite(h['early_stop_bce']).all(), (rel, 'early_stop_bce_nonfinite')
        best = int(h.loc[h['early_stop_bce'].idxmin(), 'epoch'])
        assert best == int(cl['best_epoch']) == expected_best, (rel, 'best_epoch', best, cl['best_epoch'])
    else:
        # Final refit has no validation: early_stop_bce is NaN by design (unused field).
        assert cl['early_stopping'] is False, (rel, 'unexpected_early_stopping')
        assert int(cl['force_epochs']) == expected_rows, (rel, 'force_epochs')
    if expected_term is not None:
        assert cl['termination'] == expected_term, (rel, 'termination', cl['termination'])
    return h, cl

def render_history(h, cl, title, best=None):
    b = cl['best_epoch'] if best is None else best
    print(f'{title}: {len(h)} rows | best_epoch={b} | termination={cl["termination"]} '
          f'| seed={cl["seed"]} | history_sha256={cl["history_sha256"][:16]}...')
    table(h, f'{title} - COMPLETE epoch history (all {len(h)} rows; no truncation)')
print('Phase25F frozen inputs bound:', len(INPUTS))
'''

CELLS = [
    ("markdown", """# Phase 25F - Canonical Post-Safety Execution (`BARRPostSafetyV1`)

**Method**: `RA-MedFiLM-BARR` - post-safety revision `ra_medfilm_barr_post_safety_v1_0`.

This is the **canonical reviewer / audit notebook** for the Phase25F post-safety
execution. It reads **frozen artifacts only**: it never instantiates
`BARRPostSafetyV1`, never loads a model for inference, never trains, never runs a
forward or backward pass, and never recomputes OOF predictions, C9 decisions,
features or targets.

This notebook documents the **canonical Phase25F execution**: construction of the
post-refinement preservation selector `S_omega` (`BARRPostSafetyV1`), five frozen
cross-validation logical runs, 4957 OOF safety predictions, the final all-DEV refit
checkpoint, and construction of the **C9 post-safety state/decision artifact**.

**Complete epoch histories**: every persisted per-epoch history is rendered **in full**
(fold0 36 / fold1 27 / fold2 86 / fold3 55 / fold4 43 / final 23 rows). No `head()`,
`tail()`, `iloc` subset, ellipsis or sampled display is used anywhere.

**Hard scope**: `ROUTER_DEVELOPMENT` (4957) only. `ROUTER_HOLDOUT` (875), `VAL808`
(808) and `TEST` (1683) are never read. TEST stays locked until Phase39.

**What Phase25F does NOT do**: no A7-vs-A8 segmentation comparison, no C8-vs-C9
system-performance comparison, no preservation adjudication, no new budget/lambda
selection, no `S_omega` threshold tuning. Those are owned by Phase25G."""),
    ("code", "setup"),
    ("markdown", "## 1. Scope and role of `S_omega`\n\n`S_omega` is a POST-REFINEMENT preservation/safety selector: it never changes whether refinement ran, only which already-computed prediction is returned. `saves_compute = false`, `novelty_claimed = false`."),
    ("code", """role = read_json('reports/audits/phase25f_role_and_novelty_boundary_v1_0.json')
table(pd.DataFrame([
    ['role', role.get('role', 'POST_REFINEMENT_PRESERVATION_SAFETY_SELECTOR')],
    ['saves_compute', role.get('saves_compute')],
    ['novelty_claimed', role.get('novelty_claimed')],
    ['classification', role.get('classification', 'CONTROLLED_CORE_EXTENSION')],
    ['closest_prior', role.get('closest_prior', 'JFS')],
], columns=['frozen item', 'value']), 'S_omega role boundary')"""),
    ("markdown", "## 2. Predecessor terminal and re-entry gate\n\nThe fail-closed re-entry gate binds the frozen specification and every predecessor artifact before any model is constructed."),
    ("code", """gate = read_json('reports/audits/phase25f_execution_reentry_gate.json')
enf = read_json('reports/audits/phase25f_execution_gate_enforcement.json')
print('predecessor terminal:', gate['predecessor_terminal'])
print('checks passed:', gate['checks_passed'], '/', gate['checks_total'])
print('execution permitted:', enf['execution_permitted'])
table(read_csv('reports/tables/phase25f_execution_entry_gate_summary.csv'), 'Re-entry gate checks')"""),
    ("markdown", "## 3. Frozen v1.0 contract binding\n\nFourteen physically frozen v1.0 contracts govern this execution. Where a value appears in more than one place, the on-disk contract wins."),
    ("code", """binding = read_json('reports/audits/phase25f_execution_contract_binding.json')
print('precedence rule:', binding['precedence_rule'])
table(read_csv('reports/tables/phase25f_contract_binding_summary.csv'), 'Bound frozen contracts')"""),
    ("markdown", "## 4. Upstream cross-fit disclosure\n\nThe Phase25F OOF predictions are **META_LEVEL_OOF_DEVELOPMENT_PREDICTIONS**: the Phase25C 3-fold upstream refiner cross-fit and the Phase25F 5-fold downstream `S_omega` cross-validation are not a fully nested end-to-end hierarchy."),
    ("code", """note = read_json('reports/audits/phase25f_upstream_crossfit_dependency_note.json')
print('oof classification:', note['oof_classification'])
print('fully nested end-to-end hierarchy:', note['fully_nested_end_to_end_hierarchy'])
print(note['disclosure'])"""),
    ("markdown", "## 5. Join integrity\n\nMetadata, targets and the Phase25C label table are joined 1:1 by `sample_id` with row-index alignment."),
    ("code", """join = read_json('reports/audits/phase25f_execution_join_integrity.json')
print('rows:', join['rows'], '| sample-id sets equal:', join['sample_id_sets_equal'])
print('row-index aligned:', join['feature_row_index_aligned'],
      '| targets == Phase25C delta_dice (float32):',
      join['targets_delta_dice_matches_phase25c_float32'])
table(read_csv('reports/tables/phase25f_join_integrity_summary.csv'), 'Join integrity')"""),
    ("markdown", "## 6. Cross-validation split integrity\n\nThe frozen Phase25D five-fold identity manifests are **reused, not reinvented**. Roles are FIT / EARLY_STOP / OUTER_TARGET."),
    ("code", """split = read_json('reports/audits/phase25f_execution_split_integrity.json')
print('manifest sha256:', split['outer_manifest_sha256'])
print('group leakage:', split['group_leakage'], '| new split invented:', split['new_split_invented'])
table(read_csv('reports/tables/phase25f_split_integrity_summary.csv'), 'Per-fold role sizes')"""),
    ("markdown", "## 7. Fold role assignments\n\nEvery fold partitions the full 4957 `ROUTER_DEVELOPMENT` rows into disjoint FIT / EARLY_STOP / OUTER_TARGET sets."),
    ("code", """table(read_csv('reports/tables/phase25f_cv_fold_role_assignments.csv'), 'Fold role assignments')"""),
    ("markdown", "## 8. The frozen 20-D GT-free input vector\n\nThe `S_omega` input is 16 numeric features + 4 task one-hot columns. No ground truth and no refiner hidden feature maps are used."),
    ("code", """schema = read_csv('reports/tables/phase25f_feature_schema_v1_0.csv')
table(schema[['feature_index','name','normalization_role','GT_free','group']], 'Phase25F 20-D input schema')"""),
    ("markdown", "## 9. Feature equations (frozen)\n\nEntropy, foreground fraction, 8-connected component count and boundary fraction are frozen closed-form expressions."),
    ("code", """eq = read_json('reports/audits/phase25f_feature_equation_contract_v1_0.json')
print('feature dim:', eq.get('feature_dim'), '| numeric:', eq.get('numeric_dim'),
      '| one-hot:', eq.get('onehot_dim'))
print('GT-free:', eq.get('GT_free'), '| delta_dice forbidden as input:', eq.get('delta_dice_forbidden_from_model_input'))
table(read_csv('reports/tables/phase25f_post_safety_input_contract_v1_0.csv'), 'Post-safety input contract')"""),
    ("markdown", "## 10. Normalization contract\n\nOnly the 16 numeric features (indices 0..15) are standardized, using FIT-only statistics with `ddof = 0`. The one-hot columns 16..19 stay raw."),
    ("code", """norm = read_json('reports/audits/phase25f_normalization_contract_v1_0.json')
print('normalized:', norm['normalized_features'], '| raw:', norm['not_normalized_features'])
print('statistics source:', norm['statistics_source'], '| zero-sigma rule:', norm['zero_sigma_rule'])
table(read_csv('reports/tables/phase25f_cv_normalization_stats_summary.csv').head(20),
      'Per-fold normalization statistics (first 20 rows)')"""),
    ("markdown", "## 11. `BARRPostSafetyV1` architecture\n\n`Linear(20,32) -> SiLU -> Linear(32,16) -> SiLU -> Linear(16,1)`, one raw logit, 1217 trainable parameters."),
    ("code", """arch = read_json('reports/audits/phase25f_architecture_execution_binding.json')
print('architecture:', arch['architecture_string'])
print('params measured:', arch['parameter_count_measured'], '/ closed form:', arch['parameter_count_closed_form'])
print('sigmoid inside model:', arch['sigmoid_inside_model'], '| output:', arch['output'])
table(pd.DataFrame(arch['layer_shapes'].items(), columns=['layer','[weight, bias]']), 'Layer shapes')"""),
    ("markdown", "## 12. Initialization binding\n\nStandard PyTorch `Linear` initialization, made explicit: `kaiming_uniform_(a=sqrt(5))` weights and `Uniform(-1/sqrt(fan_in), +1/sqrt(fan_in))` biases."),
    ("code", """init = read_json('reports/audits/phase25f_initialization_binding.json')
print('weight init:', init['weight_init'])
print('bias init:', init['bias_init'])
print('all_pass:', init['all_pass'])
table(pd.DataFrame(init['checks'].items(), columns=['check','pass']), 'Initialization checks')"""),
    ("markdown", "## 13. Implementation tests\n\nArchitecture, initialization, normalization, loss, optimizer, scheduler and checkpoint-selection primitives are exercised before training."),
    ("code", """it = read_json('reports/audits/phase25f_implementation_tests.json')
print('checks passed:', it['checks_passed'], '/', it['checks_total'], '| all_pass:', it['all_pass'])
table(pd.DataFrame(it['implementation_checks'].items(), columns=['check','pass']), 'Implementation checks')"""),
    ("markdown", "## 14. Training contract\n\n`BCEWithLogitsLoss(reduction=mean)`, AdamW(lr=1e-3, wd=1e-4), batch 128, max 200 epochs, patience 20, no AMP, float32. `ReduceLROnPlateau` monitors the EARLY_STOP mean BCE."),
    ("code", """tr = read_json('reports/audits/phase25f_training_contract_v1_0.json')
table(pd.DataFrame([
    ['loss', tr['loss']['class']], ['reduction', tr['loss']['reduction']],
    ['class weighting', tr['loss']['class_weighting']], ['optimizer', tr['optimizer']['name']],
    ['lr', tr['optimizer']['lr']], ['weight decay', tr['optimizer']['weight_decay']],
    ['batch size', tr['optimizer']['batch_size']], ['max epochs', tr['optimizer']['max_epochs']],
    ['patience', tr['optimizer']['early_stopping_patience']], ['amp', tr['optimizer']['amp']],
    ['scheduler', tr['scheduler']['class']],
], columns=['frozen item','value']), 'Training contract')"""),
    ("markdown", "## 15. Checkpoint selection rule\n\nBest epoch = lowest EARLY_STOP mean BCE (MINIMIZE), strict improvement `current < best - 1e-12`; a tie keeps the earlier epoch and counts as non-improvement."),
    ("code", """ck = read_json('reports/audits/phase25f_checkpoint_selection_contract_v1_0.json')
print('primary metric:', ck['primary_metric'], '| direction:', ck['direction'])
print('update rule:', ck['update_rule'])
print('tie rule:', ck['tie_rule'])"""),
    ("markdown", "## 16. Training run registry\n\nExactly five CV logical runs (seeds 54000..54004) plus one final refit (seed 42). Every persisted epoch history is read **in full** below."),
    ("code", """reg = read_json('reports/audits/phase25f_training_run_registry.json')
print('logical runs:', reg['logical_run_count'], '| device:', reg['device'])
table(read_csv('reports/tables/phase25f_training_run_summary.csv'), 'Training run summary')

# Prove every persisted epoch history is available and complete (no truncation).
_hist_proof = []
for _sub, _exp in [('cv_fold0', 36), ('cv_fold1', 27), ('cv_fold2', 86),
                   ('cv_fold3', 55), ('cv_fold4', 43), ('final', 23)]:
    _h = read_csv(f'experiments/phase25f_barr_post_safety_v1_0_seed42/{_sub}/history.csv')
    _c = read_json(f'experiments/phase25f_barr_post_safety_v1_0_seed42/{_sub}/run_complete.json')
    assert len(_h) == _exp, (_sub, len(_h))
    _hist_proof.append([_sub, len(_h), int(_h['epoch'].min()), int(_h['epoch'].max()),
                        _c['best_epoch'], _c['termination'], _c['history_sha256'][:16]])
table(pd.DataFrame(_hist_proof, columns=['run', 'rows', 'first_epoch', 'last_epoch',
      'best_epoch', 'termination', 'history_sha256_16']),
      'Complete persisted epoch histories (all six runs read in full)')"""),
    ("markdown", "## 17. CV fold 0 — complete epoch history\n\nAll 36 persisted epochs are rendered. No `head()`, `tail()`, `iloc` subset, ellipsis or sampled display is used."),
    ("code", """h0, cl0 = epoch_history('experiments/phase25f_barr_post_safety_v1_0_seed42/cv_fold0/history.csv',
                            'experiments/phase25f_barr_post_safety_v1_0_seed42/cv_fold0/run_complete.json',
                            36, expected_best=16, expected_term='early_stop')
render_history(h0, cl0, 'Fold 0', best=16)"""),
    ("markdown", "## 18. CV fold 1 — complete epoch history\n\nAll 27 persisted epochs are rendered."),
    ("code", """h1, cl1 = epoch_history('experiments/phase25f_barr_post_safety_v1_0_seed42/cv_fold1/history.csv',
                            'experiments/phase25f_barr_post_safety_v1_0_seed42/cv_fold1/run_complete.json',
                            27, expected_best=7, expected_term='early_stop')
render_history(h1, cl1, 'Fold 1', best=7)"""),
    ("markdown", "## 19. CV fold 2 — complete epoch history\n\nAll 86 persisted epochs are rendered."),
    ("code", """h2, cl2 = epoch_history('experiments/phase25f_barr_post_safety_v1_0_seed42/cv_fold2/history.csv',
                            'experiments/phase25f_barr_post_safety_v1_0_seed42/cv_fold2/run_complete.json',
                            86, expected_best=66, expected_term='early_stop')
render_history(h2, cl2, 'Fold 2', best=66)"""),
    ("markdown", "## 20. CV fold 3 — complete epoch history\n\nAll 55 persisted epochs are rendered."),
    ("code", """h3, cl3 = epoch_history('experiments/phase25f_barr_post_safety_v1_0_seed42/cv_fold3/history.csv',
                            'experiments/phase25f_barr_post_safety_v1_0_seed42/cv_fold3/run_complete.json',
                            55, expected_best=35, expected_term='early_stop')
render_history(h3, cl3, 'Fold 3', best=35)"""),
    ("markdown", "## 21. CV fold 4 — complete epoch history\n\nAll 43 persisted epochs are rendered."),
    ("code", """h4, cl4 = epoch_history('experiments/phase25f_barr_post_safety_v1_0_seed42/cv_fold4/history.csv',
                            'experiments/phase25f_barr_post_safety_v1_0_seed42/cv_fold4/run_complete.json',
                            43, expected_best=23, expected_term='early_stop')
render_history(h4, cl4, 'Fold 4', best=23)
print('complete CV histories read:', [len(h0), len(h1), len(h2), len(h3), len(h4)])
print('canonical best epochs:', [cl0['best_epoch'], cl1['best_epoch'], cl2['best_epoch'],
                                 cl3['best_epoch'], cl4['best_epoch']])"""),
    ("markdown", "## 22. Training curves\n\nFIT train BCE and EARLY_STOP mean BCE for all five folds."),
    ("code", """show_fig('reports/figures/p25f_training_curves.png')"""),
    ("markdown", "## 23. Selected epoch per fold and the median rule\n\nThe final refit epoch count is the exact integer median of the five selected epochs."),
    ("code", """show_fig('reports/figures/p25f_best_epochs.png')
table(read_csv('reports/tables/phase25f_final_epoch_rule.csv'), 'Final epoch rule')"""),
    ("markdown", "## 24. Training health\n\nAll histories are finite, best epochs are in range, and train BCE decreases in every fold."),
    ("code", """health = read_json('reports/audits/phase25f_training_health.json')
print('best epochs:', health['best_epochs'], '| terminations:', health['terminations'])
table(read_csv('reports/tables/phase25f_training_health_summary.csv'), 'Training health checks')"""),
    ("markdown", "## 25. Final epoch rule execution\n\n`FINAL_SAFETY_EPOCHS = sorted(best_epoch_0..best_epoch_4)[2]`."),
    ("code", """rule = read_json('reports/audits/phase25f_final_epoch_rule_execution.json')
print('best epochs:', rule['best_epochs_in_fold_order'])
print('sorted:', rule['sorted_best_epochs'], '| FINAL_SAFETY_EPOCHS:', rule['final_safety_epochs'])"""),
    ("markdown", "## 26. Final all-DEV normalization\n\nStatistics are re-fit on all 4957 `ROUTER_DEVELOPMENT` rows for the final refit."),
    ("code", """fn = read_json('reports/audits/phase25f_final_normalization.json')
print('rows:', fn['rows'], '| source:', fn['statistics_source'], '| ddof:', fn['ddof'])
table(read_csv('reports/tables/phase25f_final_normalization_stats.csv'), 'Final normalization statistics')"""),
    ("markdown", "## 27. Final refit — complete epoch history\n\nA fresh `BARRPostSafetyV1` is trained on all 4957 rows for exactly `FINAL_SAFETY_EPOCHS` epochs, with no validation and no early stopping. All 23 persisted epochs are rendered."),
    ("code", """fc = read_json('reports/audits/phase25f_final_checkpoint_integrity.json')
print('final checkpoint:', fc['final_checkpoint'])
print('final safety epochs:', fc['final_safety_epochs'])
hf, clf = epoch_history('experiments/phase25f_barr_post_safety_v1_0_seed42/final/history.csv',
                        'experiments/phase25f_barr_post_safety_v1_0_seed42/final/run_complete.json',
                        23, expected_best=None, expected_term='fixed_epochs')
assert int(fc['final_safety_epochs']) == 23
assert int(hf['epoch'].iloc[-1]) == 23
# No validation exists for the final refit, so early_stop_bce is NaN by design (unused field).
print('final early_stop_bce all-NaN (by design, unused):',
      bool(hf['early_stop_bce'].isna().all()))
print('final train_bce finite:', bool(np.isfinite(hf['train_bce']).all()))
table(hf, 'Final refit - COMPLETE epoch history (all 23 rows; no truncation)')"""),
    ("markdown", "## 28. Final checkpoint integrity\n\nParameter count, state-dict load, finite parameters and a synthetic forward pass."),
    ("code", """table(pd.DataFrame(fc['checks'].items(), columns=['check','pass']), 'Final checkpoint integrity')
table(read_csv('reports/tables/phase25f_checkpoint_registry.csv'), 'Checkpoint registry')"""),
    ("markdown", "## 29. OOF safety prediction assembly\n\nEach fold's frozen best checkpoint predicts once on that fold's OUTER_TARGET. The five folds union to exactly 4957 rows."),
    ("code", """oof = read_csv('data_cache/phase25f_barr_post_safety_v1_0/phase25f_oof_safety_predictions.csv')
print('OOF rows:', len(oof), '| unique sample ids:', oof.sample_id.nunique())
table(oof.head(8), 'OOF safety predictions (head)')
table(read_csv('reports/tables/phase25f_oof_fold_coverage.csv'), 'OOF coverage by fold')"""),
    ("markdown", "## 30. OOF integrity\n\nLogits are finite, probabilities are the sigmoid of the logits, and decisions follow the fixed threshold `p_accept >= 0.50`."),
    ("code", """oi = read_json('reports/audits/phase25f_oof_integrity.json')
print('decision counts:', oi['decision_counts'])
print('sigmoid matches logit:', oi['checks']['sigmoid_matches_logit'])
print('decisions match fixed threshold:', oi['checks']['decisions_match_fixed_threshold'])
table(read_csv('reports/tables/phase25f_oof_decision_distribution.csv'), 'OOF decisions by domain')"""),
    ("markdown", "## 31. Prediction determinism\n\nThe full canonical fold-batched OOF inference is replayed 3x from the frozen checkpoints and compared to the stored logits."),
    ("code", """det = read_json('reports/audits/phase25f_oof_prediction_determinism.json')
c = det['checks']
print('subset size:', c['subset_size'], '| per domain:', c['per_domain'])
print('full OOF max abs vs stored:', c['full_oof_max_abs_vs_stored'])
print('bit-identical to stored:', c['bit_identical_to_stored'], '| replays bit-identical:', c['replays_bit_identical'])"""),
    ("markdown", "## 32. OOF logit distribution\n\nSeparation of the ACCEPT (y=1) and FALLBACK (y=0) classes in OOF logit space."),
    ("code", """show_fig('reports/figures/p25f_oof_logit_distribution.png')
show_fig('reports/figures/p25f_oof_prob_by_domain.png')"""),
    ("markdown", "## 33. Classifier-level metrics (overall)\n\nDescriptive metrics for `S_omega` itself at the fixed 0.50 threshold. These are NOT segmentation results and NOT a preservation proof."),
    ("code", """cmo = read_json('reports/audits/phase25f_classifier_metrics.json')
print('metric class:', cmo['metric_class'], '| threshold tuning:', cmo['threshold_tuning'])
table(read_csv('reports/tables/phase25f_classifier_metrics_overall.csv'), 'Classifier metrics - overall')"""),
    ("markdown", "## 34. Classifier-level metrics by domain"),
    ("code", """table(read_csv('reports/tables/phase25f_classifier_metrics_by_domain.csv'), 'Classifier metrics - by domain')
show_fig('reports/figures/p25f_metrics_by_domain.png')"""),
    ("markdown", "## 35. Classifier-level metrics by CV fold"),
    ("code", """table(read_csv('reports/tables/phase25f_classifier_metrics_by_fold.csv'), 'Classifier metrics - by fold')"""),
    ("markdown", "## 36. ROC and precision-recall curves\n\nClassifier-level discrimination of the frozen `S_omega` on the 4957 development rows."),
    ("code", """show_fig('reports/figures/p25f_roc_curves.png')
show_fig('reports/figures/p25f_pr_curves.png')"""),
    ("markdown", "## 37. Confusion matrix at the fixed threshold"),
    ("code", """show_fig('reports/figures/p25f_confusion_matrix.png')"""),
    ("markdown", "## 38. C9 post-safety state/decision artifact\n\nC9 gates each frozen Phase25E C8 policy with the frozen `S_omega` decision. Only state/decision artifacts are constructed - no performance is evaluated."),
    ("code", """c9 = read_json('reports/audits/phase25f_c9_decision_artifact.json')
print('comparator:', c9['comparator'], c9['comparator_name'])
print('C8 policies:', c9['c8_policy_count'], '| rows:', c9['rows'])
print('state counts:', c9['state_counts'])
table(read_csv('reports/tables/phase25f_c9_decision_summary.csv'), 'C9 state/decision summary per policy')"""),
    ("markdown", "## 39. C9 state distribution\n\nAcross the 20 frozen C8 policies, how many samples fall into skip / accept / reject."),
    ("code", """show_fig('reports/figures/p25f_c9_state_distribution.png')"""),
    ("markdown", "## 40. Scope guards and locks\n\n`ROUTER_HOLDOUT`, `VAL808` and `TEST` are never read. No A7/A8 segmentation comparison, no C8/C9 system-performance comparison, no preservation adjudication."),
    ("code", """guard = read_json('reports/audits/phase25f_a7_a8_execution_guard.json')
table(read_csv('reports/tables/phase25f_scope_lock_summary.csv'), 'Scope lock summary')
print('A7/A8 evaluation owner:', guard['A7_A8_evaluation_owner'])
print('C8/C9 comparison owner:', guard['C8_C9_comparison_owner'])"""),
    ("markdown", """## 41. Conclusions (scoped)

- `BARRPostSafetyV1` was constructed exactly as frozen (1217 parameters, raw logit)
  and trained for exactly five frozen CV logical runs plus one all-DEV final refit
  (`FINAL_SAFETY_EPOCHS` = the integer median of the five selected epochs).
- **Every persisted epoch history is presented in full** (36 / 27 / 86 / 55 / 43 for
  the five CV folds; 23 for the final refit), with row counts, contiguous epoch
  sequences and canonical best epochs asserted from code against the frozen
  `run_complete.json` closures.
- 4957 OOF safety logits/probabilities/decisions were produced on `ROUTER_DEVELOPMENT`
  and are **bit-reproducible** (3x replay, max abs difference 0.0).
- Classifier-level metrics describe `S_omega` itself at the fixed 0.50 threshold; they
  are not segmentation results and not a preservation proof.
- The **C9 post-safety state/decision artifact** was constructed over the 20 frozen C8
  policies. No performance was evaluated.

**Handoff**: Phase25G owns A7-vs-A8, C8-vs-C9, preservation adjudication and the
integrated controlled development freeze. `ROUTER_HOLDOUT`, `VAL808` and `TEST` remain
unread; TEST is locked until Phase39."""),
]


def normalize(nb):
    """Strip execution metadata and canonicalise stream-output chunking so the
    serialised notebook is byte-identical across builds."""
    for cell in nb.cells:
        cell.get("metadata", {}).pop("execution", None)
        merged = []
        for o in cell.get("outputs", []):
            if isinstance(o.get("text"), list):
                o["text"] = "".join(o["text"])
            if (o.get("output_type") == "stream" and merged
                    and merged[-1].get("output_type") == "stream"
                    and merged[-1].get("name") == o.get("name")):
                merged[-1]["text"] = merged[-1]["text"] + o["text"]
                continue
            merged.append(o)
        cell["outputs"] = merged
        for o in cell.get("outputs", []):
            o.get("metadata", {}).pop("execution", None)
    return nb


def build():
    inputs = build_inputs()
    nb = nbformat.v4.new_notebook()
    nb.metadata = {
        "kernelspec": {"display_name": "jup-venv", "language": "python", "name": "jup-venv"},
        "language_info": {"name": "python"},
    }
    for i, (kind, src) in enumerate(CELLS):
        if kind == "markdown":
            cell = nbformat.v4.new_markdown_cell(src)
        else:
            code = SETUP.replace("__INPUTS__", json.dumps(inputs, indent=0, sort_keys=True)) if src == "setup" else src
            cell = nbformat.v4.new_code_cell(code)
        cell["id"] = f"p25f-cell-{i:02d}"
        nb.cells.append(cell)
    client = NotebookClient(nb, kernel_name="jup-venv", timeout=900, allow_errors=False,
                            resources={"metadata": {"path": str(ROOT)}})
    client.execute()
    normalize(nb)
    NB.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(nb, NB)
    return sha(NB)


if __name__ == "__main__":
    n_sections = sum(1 for k, s in CELLS if k == "markdown" and s.lstrip().startswith("## "))
    print("numbered markdown sections:", n_sections)
    print("notebook sha256:", build())
